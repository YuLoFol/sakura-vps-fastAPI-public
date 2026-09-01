import imaplib
from fastapi import APIRouter, HTTPException
from ..services.mail import read_latest_mail

router = APIRouter()


@router.get("/mail_read")
def mail_read(limit: int = 5):
    """最新N通メールを読み取り(デフォルト5通)"""
    try:
        results = read_latest_mail(limit)
        return {"count": len(results), "mails": results}
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=401, detail=f"IMAP 認証失敗: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"読み込みエラー: {str(e)}")