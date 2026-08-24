import os
import json
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException


#Mail設定取得
load_dotenv()
MAIL_IMAP_HOST = os.getenv("MAIL_IMAP_HOST")
MAIL_IMAP_PORT = int(os.getenv("MAIL_IMAP_PORT", 993))
MAIL_USER = os.getenv("MAIL_USER_YU")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD_YU")

#router設定
router = APIRouter()

#decode header
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

#mail_read実例
@router.get("/mail_read")
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
