import os
import uvicorn
from fastapi import FastAPI, HTTPException

from .routers import router_health, my_notion, my_mail, my_claris

#FastAPI実例
app = FastAPI()

app.include_router(router_health.router)
app.include_router(my_notion.router)
app.include_router(my_mail.router)
app.include_router(my_claris.router)


#health_check実例
@app.get("/health")
def health_check():
    return {"message": 200}


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
