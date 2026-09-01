import os
from dotenv import load_dotenv
from mcp.server.auth.provider import AccessToken, TokenVerifier

load_dotenv()

MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
if not MCP_AUTH_TOKEN:
    raise RuntimeError("MCP_AUTH_TOKEN is not set in .env")

KNOWN_TOKENS = {
    MCP_AUTH_TOKEN: AccessToken(
        token=MCP_AUTH_TOKEN,
        client_id="my-vps",
        scopes=["mcp:read","router:read"]
    ),
}

class StaticTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        return KNOWN_TOKENS.get(token)
