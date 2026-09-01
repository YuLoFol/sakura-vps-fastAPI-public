import os
import datetime as dt
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATASOURCE_ID_CASHFLOW = os.getenv("NOTION_DATASOURCE_ID_CASHFLOW")


def get_properties() -> dict:
    """取得 Notion data source 的欄位結構"""
    notion_url = f"https://api.notion.com/v1/data_sources/{NOTION_DATASOURCE_ID_CASHFLOW}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2026-03-11",
    }
    response = requests.get(notion_url, headers=headers)
    response.raise_for_status()
    return response.json()


def search_recent(days: int = 365) -> dict:
    """取得最近 N 天的 Notion 資料（原本寫死 365 天，這裡改成參數，預設維持 365 保持原行為）"""
    three_days_before = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    notion_url = f"https://api.notion.com/v1/data_sources/{NOTION_DATASOURCE_ID_CASHFLOW}/query"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2026-03-11",
    }
    payload = {
        "filter": {
            "property": "日期",
            "date": {"on_or_after": three_days_before},
        }
    }

    response = requests.post(notion_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()