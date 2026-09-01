import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
if not MCP_AUTH_TOKEN:
    raise RuntimeError("MCP_AUTH_TOKEN is not set in .env")

async def verify_mcp_token(authorization: str = Header(None)):
    expected = f"Bearer {MCP_AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
