from fastapi import APIRouter, HTTPException
from ..services.notion import get_properties, search_recent

#router設定
router = APIRouter()

@router.get("/notion_properities")
def notion_get_properities():
    try:
        return get_properties()
    except Exception:
        raise HTTPException(status_code=500, detail="get Error when getting properities")


@router.get("/notion_search")
def notion_search():
    """最新のNotionデータを取得する"""
    try:
        return search_recent(days=365)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get Error when reading notion: {str(e)}")