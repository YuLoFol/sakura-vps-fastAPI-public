import os
import datetime as dt
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

load_dotenv()

#Notopn設定取得
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATASOURCE_ID_CASHFLOW = os.getenv("NOTION_DATASOURCE_ID_CASHFLOW")

router = APIRouter()


@router.get("/notion_properities")
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


@router.get("/notion_search")
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
        "filter": {
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