from fastapi import APIRouter

#router設定
#check if the router is healthy
router = APIRouter()

@router.get("/router_health")
def health_check():
    return {"status": "200"}
