import os
from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from ..core.security import StaticTokenVerifier
from ..services.mail import read_latest_mail

load_dotenv()

PUBLIC_HOST = os.getenv("PUBLIC_HOST")

mail_mcp = MCPServer(
    "Mail",
    token_verifier=StaticTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(f"https://{PUBLIC_HOST}"),
        resource_server_url=AnyHttpUrl(f"https://{PUBLIC_HOST}/mcp/mail/"),
        required_scopes=["mcp:read"],
    ),
)


@mail_mcp.tool()
def read_mail(limit: int = 5) -> str:
    """Read the latest emails from the inbox.

    Args:
        limit: Maximum number of emails to return
    """
    emails = read_latest_mail(limit)
    if not emails:
        return "No emails found."
    lines = [f"From: {e['from']} | Subject: {e['subject']} | Date: {e['date']}" for e in emails]
    return "\n".join(lines)