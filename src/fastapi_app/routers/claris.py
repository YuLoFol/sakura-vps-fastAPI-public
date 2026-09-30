import os
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from pycognito.exceptions import SMSMFAChallengeException

from ..services.claris_auth import start_srp_login, respond_mfa, get_fresh_id_token

# API Key 認証（リクエストヘッダー X-API-Key）
api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(api_key: str = Depends(api_key_header)):
    expected = os.getenv("INTERNAL_API_KEY")
    if not expected:
        # 設定漏れのときは全て拒否する（キー無しで通ってしまうのを防ぐ）
        raise HTTPException(status_code=500, detail="INTERNAL_API_KEY が設定されていません")
    if not secrets.compare_digest(api_key.encode(), expected.encode()):
        raise HTTPException(status_code=403, detail="Invalid API key")


#router設定（このrouterの全エンドポイントに API Key 認証をかける）
router = APIRouter(dependencies=[Depends(verify_api_key)])


class MfaRequest(BaseModel):
    mfa_code: str = Field(pattern=r"^\d{6}$")
    session: str


@router.post("/fm_cognito/login")
def fm_cognito_login():
    #成功の場合、start_srp_login()のレスポンス（respond_to_auth_challenge のレスポンス dict）をそのまま返す。
    try:
        cognito_tokens = start_srp_login()
        return cognito_tokens["AuthenticationResult"]

    #SMSMFAの場合
    except SMSMFAChallengeException as e:
        challenge_data = e.get_tokens()
        return {
            "status": "mfa_required",
            "message": "mfa_codeとsessionを使い、/fm_cognito/mfa を3分以内に実行してください",
            "session": challenge_data["Session"],
            "code_destination": challenge_data.get("ChallengeParameters", {}).get("CODE_DELIVERY_DESTINATION"),
        }

    #それ以外の例外の場合
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Cognito authentication failed: {str(e)}"
        )


@router.post("/fm_cognito/mfa")
def fm_cognito_mfa(body: MfaRequest):
    try:
        response = respond_mfa(body.mfa_code, body.session)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"MFA verification failed: {str(e)}"
        )
    if "AuthenticationResult" not in response:
        raise HTTPException(
            status_code=401,
            detail=f"Unexpected response, no AuthenticationResult: {response}"
        )
    return response["AuthenticationResult"]


@router.get("/fm_cognito_refresh")
def fm_cognito_refresh():
    try:
        id_token = get_fresh_id_token()
        return {"IdToken": id_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Refresh token 失効: {str(e)}")