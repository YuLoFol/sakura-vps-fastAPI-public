import os
import uvicorn
from dotenv import load_dotenv

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from fastapi import FastAPI, HTTPException
from mcp.server.transport_security import TransportSecuritySettings

#import Routers
from .routers import health as r_health
from .routers import notion as r_notion
from .routers import mail as r_mail
from .routers import claris as r_claris
from .routers import filemaker as r_filemaker

#import MCPs
from .mcp import health as m_health
from .mcp import notion as m_notion
from .mcp import mail as m_mail

load_dotenv()

PUBLIC_HOST=os.getenv("PUBLIC_HOST")

# Transport security：MCPの公開ドメイン許可リスト
security = TransportSecuritySettings(
    allowed_hosts=[PUBLIC_HOST, f"{PUBLIC_HOST}:*"],
    allowed_origins=[f"https://{PUBLIC_HOST}"],
)

# Lifespan：3つの MCP server の session manager を同時に起動 
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(m_health.health_mcp.session_manager.run())
        await stack.enter_async_context(m_mail.mail_mcp.session_manager.run())
        await stack.enter_async_context(m_notion.notion_mcp.session_manager.run())
        yield


# FastAPI実例
app = FastAPI(lifespan=lifespan)

# health_check実例
@app.get("/health")
def health_check():
    return {"message": 200}

# 通常の HTTP routers（REST API）
app.include_router(r_health.router)
app.include_router(r_notion.router)
app.include_router(r_mail.router)
app.include_router(r_claris.router)
app.include_router(r_filemaker.router)

#  MCP servers 
# streamable_http_path="/" の指定によって、
# endpoint root example: https://my.domain/mcp/health/
# transport_security=security の指定によって、
# DNS rebindingを防ぐ（default: 127.0.0.1 -> 設定せずにMCPを公開すると、エラーが発生する）
app.mount(
    "/mcp/health",
    m_health.health_mcp.streamable_http_app(
        streamable_http_path="/", transport_security=security
    ),
)
app.mount(
    "/mcp/mail",
    m_mail.mail_mcp.streamable_http_app(
        streamable_http_path="/", transport_security=security
    ),
)
app.mount(
    "/mcp/notion",
    m_notion.notion_mcp.streamable_http_app(
        streamable_http_path="/", transport_security=security
    ),
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    