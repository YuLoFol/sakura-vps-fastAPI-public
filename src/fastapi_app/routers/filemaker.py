from fastapi import APIRouter, HTTPException
from ..services.filemaker_data_api import FileMakerAuthError
from ..services.filemaker import list_layouts

#router設定
router = APIRouter(prefix="/fm_data")

@router.get("/layouts")
def fm_list_layouts(database: str | None = None):
    try:
        return list_layouts(database)
    except FileMakerAuthError as e:
        raise HTTPException(status_code=502, detail=str(e))
