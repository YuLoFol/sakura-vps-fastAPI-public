"""
FileMaker Cloud Data API 連携レイヤー

処理フロー：
1. Cognito SRP ログイン (claris_auth.py) で Claris ID Token (= IdToken) を取得
2. IdToken を使って FileMaker Data API の session token に交換する
   -> POST /fmi/data/vLatest/databases/{db}/sessions
   -> Header: Authorization: FMID <IdToken>   （"FMID " であって "Bearer " ではない点に注意）
3. 取得した fm session token を、以降すべての CRUD 呼び出しで使用する
   -> Header: Authorization: Bearer <fm_session_token>

2つの token はそれぞれ有効期限が異なる：
- Claris ID Token (IdToken)：1時間で失効。失効後は Cognito フローを再実行する必要がある
  （元の /fm_cognito_refresh に相当。REFRESH_TOKEN を使って新しい IdToken に更新する）
- FM Data API session token：15分間アクセスがないと失効する。失効後は IdToken を使って
  Data API の sessions に再ログインする必要がある

ここではシンプルな process 内キャッシュ（threading.Lock で保護）を使い、
リクエストのたびに Cognito + Data API ログインをやり直さないようにしている。
本番環境でマルチワーカー／複数台構成の場合は、Redis 等の共有ストレージに
キャッシュを置き換えることを推奨する。そうしないと各 process がそれぞれ
独自の token を保持してしまい、FileMaker Server 側に不要な session が
大量に発生してしまう。
"""

import os
import threading
import time
import requests
from dotenv import load_dotenv
from typing import Any, Optional
from .claris_auth import get_fresh_id_token, start_srp_login

load_dotenv()

FM_HOST = os.getenv("FM_HOST")  # 例: xxxx.account.filemaker-cloud.com
FM_DATABASE = os.getenv("FM_DATABASE")  # 操作対象のデフォルトファイル名
DATA_API_VERSION = os.getenv("FM_DATA_API_VERSION", "vLatest")

_BASE_URL = f"https://{FM_HOST}/fmi/data/{DATA_API_VERSION}/databases"


class FileMakerAuthError(Exception):
    """FM Data API 関連の認証エラー（Cognito 層、Data API session 層どちらの失敗でもこれを送出する）"""


class _TokenCache:
    """process 内で共有する token キャッシュ。thread-safe。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._id_token: Optional[str] = None
        self._id_token_expires_at: float = 0.0
        self._fm_token: Optional[str] = None
        self._fm_token_expires_at: float = 0.0

    # ---------- Claris ID (Cognito) 層 ----------
    def get_id_token(self, force_refresh: bool = False) -> str:
        with self._lock:
            now = time.time()
            if not force_refresh and self._id_token and now < self._id_token_expires_at:
                return self._id_token

            # まず refresh token を使って新しい IdToken に交換する（SRP より速く、MFA も発生しない）
            try:
                id_token = get_fresh_id_token()
            except Exception:
                # refresh token が無効な場合は SRP フル認証にフォールバックする
                # 注意：MFA が有効なアカウントの場合、ここで MFA 要求の例外が
                # 発生する可能性がある。/fm_cognito と同様のチャレンジ対応が
                # 必要になるが、ここでは一旦例外をそのまま外に投げる。
                result = start_srp_login()
                id_token = result["AuthenticationResult"]["IdToken"]

            self._id_token = id_token
            # Claris ID Token の有効期限は1時間。5分のバッファを持たせて早めに更新する
            self._id_token_expires_at = now + 55 * 60
            return id_token

    # ---------- FM Data API session 層 ----------
    def get_fm_token(self, database: str, force_refresh: bool = False) -> str:
        with self._lock:
            now = time.time()
            if not force_refresh and self._fm_token and now < self._fm_token_expires_at:
                return self._fm_token

        id_token = self.get_id_token()
        resp = requests.post(
            f"{_BASE_URL}/{database}/sessions",
            headers={
                "Authorization": f"FMID {id_token}",
                "Content-Type": "application/json",
            },
            json={},
            timeout=15,
        )

        if resp.status_code == 401:
            # IdToken がちょうど失効していた可能性があるため、Cognito 層を強制更新して再試行する
            id_token = self.get_id_token(force_refresh=True)
            resp = requests.post(
                f"{_BASE_URL}/{database}/sessions",
                headers={
                    "Authorization": f"FMID {id_token}",
                    "Content-Type": "application/json",
                },
                json={},
                timeout=15,
            )

        if resp.status_code >= 400:
            raise FileMakerAuthError(
                f"Data API session login failed ({resp.status_code}): {resp.text}"
            )

        token = resp.json()["response"]["token"]
        with self._lock:
            self._fm_token = token
            # Data API session は15分無操作で失効するため、バッファを持たせる
            self._fm_token_expires_at = time.time() + 13 * 60
        return token

    def invalidate_fm_token(self) -> None:
        with self._lock:
            self._fm_token = None
            self._fm_token_expires_at = 0.0


_cache = _TokenCache()


def _request(
    method: str,
    path: str,
    database: Optional[str] = None,
    **kwargs: Any,
) -> dict:
    """
    Data API へのリクエストを行う共通の入り口。
    401（fm session 失効）が返ってきた場合は、Data API に強制的に再ログインして
    新しい token を取得し、もう一度だけリトライする。
    """
    database = database or FM_DATABASE
    if not database:
        raise ValueError("database を指定してください（または環境変数 FM_DATABASE を設定してください）")

    token = _cache.get_fm_token(database)
    url = f"{_BASE_URL}/{database}{path}"
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers.setdefault("Content-Type", "application/json")

    resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)

    if resp.status_code == 401:
        _cache.invalidate_fm_token()
        token = _cache.get_fm_token(database, force_refresh=True)
        headers["Authorization"] = f"Bearer {token}"
        resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)

    if resp.status_code >= 400:
        raise FileMakerAuthError(f"Data API 呼び出しに失敗しました ({resp.status_code}): {resp.text}")

    return resp.json() if resp.content else {}
