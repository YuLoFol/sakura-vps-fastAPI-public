import os
import threading
import time

import boto3
from dotenv import load_dotenv, find_dotenv, set_key, dotenv_values
from pycognito.aws_srp import AWSSRP

# Claris設定取得
# load_dotenv と set_key が同じ .env を指すように、パスを一度だけ決めておく
ENV_PATH = find_dotenv()
load_dotenv(ENV_PATH)
CLARIS_USERNAME = os.getenv("CLARIS_USERNAME")
CLARIS_PASSWORD = os.getenv("CLARIS_PASSWORD")
CLARIS_REGION = os.getenv("CLARIS_REGION")
CLARIS_USER_POOL_ID = os.getenv("CLARIS_USER_POOL_ID")
CLARIS_CLIENT_ID = os.getenv("CLARIS_CLIENT_ID")
# CLARIS_REFRESH_TOKEN は起動時に固定せず、load_refresh_token() で毎回 .env から読む

# IdToken キャッシュ（期限の5分前に更新する）
_REFRESH_MARGIN_SEC = 300
_token_lock = threading.Lock()
_token_cache = {"id_token": None, "expires_at": 0.0}


# boto3 client は thread-safe なので一つを使い回す。
# ただし boto3.client() の呼び出し自体を複数スレッドで同時に行うのは危険なため、
# import 時（シングルスレッド）に専用の Session から一度だけ作成する。
# Claris の Cognito は us-west-2 固定なので、未設定時のデフォルトにしておく。
_cognito_client = boto3.session.Session().client(
    "cognito-idp", region_name=CLARIS_REGION or "us-west-2"
)


def get_cognito_client():
    return _cognito_client


# ---------- RefreshToken の保存・読み込み ----------

def load_refresh_token() -> str | None:
    """.env から最新の RefreshToken を読む（os.environ は更新されないため直接ファイルを読む）"""
    if not ENV_PATH:
        return None
    return dotenv_values(ENV_PATH).get("CLARIS_REFRESH_TOKEN") or None


def save_refresh_token(refresh_token: str) -> None:
    """RefreshToken と取得日時を .env に書き込む"""
    if not ENV_PATH:
        raise RuntimeError(".env ファイルが見つかりません")
    set_key(ENV_PATH, "CLARIS_REFRESH_TOKEN", refresh_token)
    set_key(ENV_PATH, "CLARIS_REFRESH_TOKEN_OBTAINED_AT", str(int(time.time())))


def _handle_auth_result(auth_result: dict) -> None:
    """ログイン成功時：RefreshToken を保存し、新しい IdToken でキャッシュを上書きする"""
    if "RefreshToken" in auth_result:
        save_refresh_token(auth_result["RefreshToken"])
    with _token_lock:
        _token_cache["id_token"] = auth_result["IdToken"]
        _token_cache["expires_at"] = time.time() + auth_result["ExpiresIn"]


# ---------- 認証 ----------

def start_srp_login():
    """SRP パスワード認証。

    成功の場合(戻り値):
        respond_to_auth_challenge のレスポンス dict をそのまま返す。
        Response Structure: ["AuthenticationResult"]["AccessToken"|"ExpiresIn"|"TokenType"|"IdToken"|"ExpiresIn"|"RefreshToken"]
        根拠: pycognito aws_srp.py の authenticate_user()（公式ドキュメントに記載なし）
            https://github.com/NabuCasa/pycognito/blob/master/pycognito/aws_srp.py
        構造: respond_to_auth_challenge の Response Syntax / Response Structure
            https://docs.aws.amazon.com/boto3/latest/reference/services/cognito-idp/client/respond_to_auth_challenge.html

    MFAの場合(例外):
        Cognito が ChallengeName="SMS_MFA" を返すと、pycognito が
        SMSMFAChallengeException を送出する（戻り値は返らない）。
        e.get_tokens() で {"ChallengeName", "Session", "ChallengeParameters"} を取得。
        ChallengeParameters["CODE_DELIVERY_DESTINATION"] はコードの送信先。
        根拠: pycognito README「Respond to SMS MFA challenge」
            https://github.com/NabuCasa/pycognito#respond-to-sms-mfa-challenge
            Cognito 開発者ガイド「SMS and email message MFA」
            https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa-sms-email-message.html
    """
    aws = AWSSRP(
        username=CLARIS_USERNAME,
        password=CLARIS_PASSWORD,
        pool_id=CLARIS_USER_POOL_ID,
        client_id=CLARIS_CLIENT_ID,
        client=get_cognito_client(),
    )
    tokens = aws.authenticate_user()  # MFA が必要な場合はここで例外が発生する
    _handle_auth_result(tokens["AuthenticationResult"]) #IdToken キャッシュを上書きする
    return tokens


def respond_mfa(mfa_code: str, session: str):
    """SMS_MFA"""
    response = get_cognito_client().respond_to_auth_challenge(
        ClientId=CLARIS_CLIENT_ID,
        ChallengeName="SMS_MFA",
        Session=session,
        ChallengeResponses={
            "SMS_MFA_CODE": mfa_code,
            "USERNAME": CLARIS_USERNAME,
        },
    )
    if "AuthenticationResult" in response:
        _handle_auth_result(response["AuthenticationResult"])
    return response


def _is_cache_valid() -> bool:
    return bool(_token_cache["id_token"]) and time.time() < _token_cache["expires_at"] - _REFRESH_MARGIN_SEC


def get_fresh_id_token() -> str:
    """RefreshToken を使い、IdToken を取得（有効期限内はキャッシュを返す）"""
    if _is_cache_valid():
        return _token_cache["id_token"]

    with _token_lock:
        # ロック待ちの間に他のスレッドが更新済みかもしれないので、もう一度確認する
        if _is_cache_valid():
            return _token_cache["id_token"]

        refresh_token = load_refresh_token()
        if not refresh_token:
            raise RuntimeError("RefreshToken がありません。/fm_cognito/login からログインしてください")

        response = get_cognito_client().initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
            ClientId=CLARIS_CLIENT_ID,
        )
        result = response["AuthenticationResult"]
        _token_cache["id_token"] = result["IdToken"]
        _token_cache["expires_at"] = time.time() + result["ExpiresIn"]
        return _token_cache["id_token"]