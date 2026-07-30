import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

#.env読み取り
load_dotenv()

#Claude API Key取得
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

#FastAPI実例
app = FastAPI()

#say_hellow実例
@app.get("/")
def say_hellow():
    return {"message":"hellow world"}

#health_check実例
@app.get("/health")
def health_check():
    return {"message":200}

#os_test実例
@app.get("/os_test")
def os_test():
    key = CLAUDE_API_KEY[:5]
    return {"message":key}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    
##---

##from fastapi import FastAPI
##from fastapi_app.mcp.server import mcp
##from fastapi_app.routers import health

##mcp_app = mcp.http_app()

##app = FastAPI(lifespan=mcp_app.lifespan)
##app.mount("/mcp", mcp_app)
##app.include_router(health.router)
