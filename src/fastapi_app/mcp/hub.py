import os
from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from ..core.security import StaticTokenVerifier

load_dotenv()

PUBLIC_HOST = os.getenv("PUBLIC_HOST")

hub_mcp = MCPServer(
    "hub_mcp",
    token_verifier=StaticTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(f"https://{PUBLIC_HOST}"),
        resource_server_url=AnyHttpUrl(f"https://{PUBLIC_HOST}/mcp/hub/"),
        required_scopes=["mcp:read"],
    ),
)

