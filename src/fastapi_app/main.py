from fastapi import FastAPI
from fastapi_app.mcp.server import mcp
from fastapi_app.routers import health

mcp_app = mcp.http_app()

app = FastAPI(lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)
app.include_router(health.router)
