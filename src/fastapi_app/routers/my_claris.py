from fastapi import APIRouter, HTTPException
from ..services.claris_auth import start_srp_login, respond_mfa, get_fresh_id_token

#router設定
router = APIRouter()

@router.get("/fm_cognito")
def fm_cognito(mfa_code: str = None, session: str = None):
    if mfa_code and session:
        try:
            response = respond_mfa(mfa_code, session)
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

    try:
        cognito_tokens = start_srp_login()
        return cognito_tokens["AuthenticationResult"]

    except Exception as e:
        if len(e.args) >= 2 and isinstance(e.args[1], dict) and e.args[1].get("ChallengeName") == "SMS_MFA":
            challenge_data = e.args[1]
            return {
                "status": "mfa_required",
                "message": "mfa_codeとsessionを使い、続けて実行してください",
                "session": challenge_data["Session"],
                "code_destination": challenge_data["ChallengeParameters"].get("CODE_DELIVERY_DESTINATION")
            }

        raise HTTPException(
            status_code=401,
            detail=f"Cognito authentication failed: {str(e)}"
        )


@router.get("/fm_cognito_refresh")
def fm_cognito_refresh():
    try:
        id_token = get_fresh_id_token()
        return {"IdToken": id_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Refresh token 已失效或錯誤: {str(e)}")
        