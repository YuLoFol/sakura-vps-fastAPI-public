from fastapi import APIRouter

router = APIRouter()

@router.get("/router_health")
def health_check():
    return {"status": "200"}
