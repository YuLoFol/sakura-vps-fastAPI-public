import os
import boto3
from dotenv import load_dotenv
from pycognito.aws_srp import AWSSRP

#Claris設定取得
load_dotenv()
CLARIS_USERNAME = os.getenv("CLARIS_USERNAME")
CLARIS_PASSWORD = os.getenv("CLARIS_PASSWORD")
CLARIS_REGION = os.getenv("CLARIS_REGION")
CLARIS_USER_POOL_ID = os.getenv("CLARIS_USER_POOL_ID")
CLARIS_CLIENT_ID = os.getenv("CLARIS_CLIENT_ID")
CLARIS_REFRESH_TOKEN = os.getenv("CLARIS_REFRESH_TOKEN")


def get_cognito_client():
    return boto3.client("cognito-idp", region_name=CLARIS_REGION)


def start_srp_login():
    """SRP パスワード認証。成功の場合は tokens； MFAの場合はチャレンジ付きの例外"""
    client = get_cognito_client()
    aws = AWSSRP(
        username=CLARIS_USERNAME,
        password=CLARIS_PASSWORD,
        pool_id=CLARIS_USER_POOL_ID,
        client_id=CLARIS_CLIENT_ID,
        client=client,
    )
    return aws.authenticate_user()  # 成功すると dict；MFA の場合はチャレンジ


def respond_mfa(mfa_code: str, session: str):
    """SMS_MFA"""
    client = get_cognito_client()
    response = client.respond_to_auth_challenge(
        ClientId=CLARIS_CLIENT_ID,
        ChallengeName="SMS_MFA",
        Session=session,
        ChallengeResponses={
            "SMS_MFA_CODE": mfa_code,
            "USERNAME": CLARIS_USERNAME,
        },
    )
    return response


def get_fresh_id_token() -> str:
    """RefreshTokenお使い、IdTokenを取得"""
    client = get_cognito_client()
    response = client.initiate_auth(
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={"REFRESH_TOKEN": CLARIS_REFRESH_TOKEN},
        ClientId=CLARIS_CLIENT_ID,
    )
    return response["AuthenticationResult"]["IdToken"]