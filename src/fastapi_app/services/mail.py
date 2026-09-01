import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

#mail設定取得
MAIL_IMAP_HOST = os.getenv("MAIL_IMAP_HOST")
MAIL_IMAP_PORT = int(os.getenv("MAIL_IMAP_PORT", 993))
MAIL_USER = os.getenv("MAIL_USER_YU")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD_YU")


def _decode_mime_header(raw_header) -> str:
    """ヘッダー処理"""
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


def read_latest_mail(limit: int = 5) -> list[dict]:
    """最新のメール(N通)を読み取り(デフォルト5通)、return list[dict]"""
    imap = imaplib.IMAP4_SSL(MAIL_IMAP_HOST, MAIL_IMAP_PORT)
    try:
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

            subject = _decode_mime_header(msg.get("Subject"))
            from_ = _decode_mime_header(msg.get("From"))
            date_ = msg.get("Date")

            results.append({
                "id": mail_id.decode(),
                "subject": subject,
                "from": from_,
                "date": date_,
            })

        return results
    finally:
        imap.logout()