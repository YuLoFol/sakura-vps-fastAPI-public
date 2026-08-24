import os
import json
import imaplib
import email
import datetime as dt
import uvicorn
import requests
import boto3
from email.header import decode_header
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pycognito.aws_srp import AWSSRP
from pycognito import Cognito
from pycognito.exceptions import SMSMFAChallengeException

#.env読み取り
load_dotenv()

#Claude API Key取得
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

#Mail設定取得
MAIL_IMAP_HOST = os.getenv("MAIL_IMAP_HOST")
MAIL_IMAP_PORT = int(os.getenv("MAIL_IMAP_PORT", 993))
MAIL_USER = os.getenv("MAIL_USER_YU")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD_YU")

#Notopn設定取得
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATASOURCE_ID_CASHFLOW = os.getenv("NOTION_DATASOURCE_ID_CASHFLOW")

#Clairs設定取得
CLARIS_USERNAME = os.getenv("CLARIS_USERNAME")
CLARIS_PASSWORD = os.getenv("CLARIS_PASSWORD")
CLARIS_REGION = os.getenv("CLARIS_REGION")
CLARIS_USER_POOL_ID = os.getenv("CLARIS_USER_POOL_ID")
CLARIS_CLIENT_ID = os.getenv("CLARIS_CLIENT_ID")
CLARIS_REFRESH_TOKEN = os.getenv("CLARIS_REFRESH_TOKEN")

#FastAPI実例
app = FastAPI()

def decode_mime_header(raw_header):
    """處理郵件標題可能包含的編碼（例如日文郵件常見）"""
    if raw_header is None:
        return ""
    decoded_parts = decode_header(raw_header)
    result = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="ignore")
        else:
            result += part
    return result


#say_hellow実例
@app.get("/")
def say_hellow():
    return {"message":"hellow world"}

#health_check実例
@app.get("/health")
def health_check():
    return {"message":200}

#mail_read実例
@app.get("/mail_read")
def mail_read(limit: int = 5):
    """讀取最新的 N 封郵件（預設 5 封）"""
    try:
        imap = imaplib.IMAP4_SSL(MAIL_IMAP_HOST, MAIL_IMAP_PORT)
        imap.login(MAIL_USER, MAIL_PASSWORD)
        imap.select("INBOX")

        status, messages = imap.search(None, "ALL")
        mail_ids = messages[0].split()

        latest_ids = mail_ids[-limit:] if len(mail_ids) > limit else mail_ids

        results = []
        for mail_id in reversed(latest_ids):
            status, msg_data = imap.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = decode_mime_header(msg.get("Subject"))
            from_ = decode_mime_header(msg.get("From"))
            date_ = msg.get("Date")

            results.append({
                "id": mail_id.decode(),
                "subject": subject,
                "from": from_,
                "date": date_,
            })

        imap.logout()
        #return {"count": len(results), "mails": json.dumps(results, indent=4, ensure_ascii=False)}
        return status, msg_data

    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=401, detail=f"IMAP 認證或連線失敗: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取郵件時發生錯誤: {str(e)}")

#notion_read実例
@app.get("/notion_properities")
def notion_get_properities():
    notion_url = f"https://api.notion.com/v1/data_sources/{NOTION_DATASOURCE_ID_CASHFLOW}"
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2026-03-11"
    }

    try:
        response = requests.get(notion_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get Error when getting properities")

@app.get("/notion_search")
def notion_search():
    """最新のNotionデータ3日分を取得する"""
    today = dt.datetime.now().strftime("%Y-%m-%d")
    three_days_before = ((dt.datetime.now()) - (dt.timedelta(days=365))).strftime("%Y-%m-%d")
    notion_url = f"https://api.notion.com/v1/data_sources/{NOTION_DATASOURCE_ID_CASHFLOW}/query"
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2026-03-11"
    }
    payload = {
        "filter":{
            "property": "日期",
            "date": {"on_or_after": f"{three_days_before}"}
        }
    }
    
    try:
        response = requests.post(notion_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get Error when reading notion: {str(e)}")

@app.get("/fm_cognito")
def fm_cognito(mfa_code: str = None, session: str = None):
    client = boto3.client("cognito-idp", region_name=f"{CLARIS_REGION}")

    if mfa_code and session:
        try:
            response = client.respond_to_auth_challenge(
                ClientId=CLARIS_CLIENT_ID,
                ChallengeName="SMS_MFA",
                Session=session,
                ChallengeResponses={
                    "SMS_MFA_CODE": mfa_code,
                    "USERNAME": CLARIS_USERNAME
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"MFA vertification failed {str(e)}"
            )
        if "AuthenticationResult" not in response:
            raise HTTPException(
                status_code=401,
                detail=f"Unexpected response, no AuthenticationResult: {response}"
            )

        return response["AuthenticationResult"]

    aws = AWSSRP(
        username=f"{CLARIS_USERNAME}",
        password=f"{CLARIS_PASSWORD}",
        pool_id=f"{CLARIS_USER_POOL_ID}",
        client_id=f"{CLARIS_CLIENT_ID}",
        client=client
    )
    try:
        cognito_tokens = aws.authenticate_user()
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


@app.get("/fm_cognito_refresh")
def fm_cognito_refresh():
    client = boto3.client("cognito-idp", region_name=f"{CLARIS_REGION}")

    if not CLARIS_REFRESH_TOKEN:
        raise HTTPException(
            status_code=400, 
            detail="CLARIS_REFRESH_TOKEN 未設定"
        )

    try:
        response = client.initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={
                "REFRESH_TOKEN": CLARIS_REFRESH_TOKEN,
            },
            ClientId=CLARIS_CLIENT_ID,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Refresh token 已失效或錯誤: {str(e)}")

    return response["AuthenticationResult"]


def get_fresh_id_token():
    client = boto3.client("cognito-idp", region_name=CLARIS_REGION)
    response = client.initiate_auth(
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={
            "REFRESH_TOKEN": CLARIS_REFRESH_TOKEN
        },
        ClientId=CLARIS_CLIENT_ID,
    )
    return response["AuthenticationResult"]["IdToken"]


@app.get("/fm_data_api_test")
def fm_data_api_test(host: str, database: str):
    id_token = get_fresh_id_token()
    headers = {"Authorization": f"FMID {id_token}"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

#---

##from fastapi import FastAPI
##from fastapi_app.mcp.server import mcp
##from fastapi_app.routers import health

##mcp_app = mcp.http_app()

##app = FastAPI(lifespan=mcp_app.lifespan)
##app.mount("/mcp", mcp_app)
##app.include_router(health.router)
