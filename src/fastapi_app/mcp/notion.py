import os
from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from ..core.security import StaticTokenVerifier
from ..services.notion import get_properties, search_recent

load_dotenv()

PUBLIC_HOST = os.getenv("PUBLIC_HOST")

notion_mcp = MCPServer(
    "Notion",
    token_verifier=StaticTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(f"https://{PUBLIC_HOST}"),
        resource_server_url=AnyHttpUrl(f"https://{PUBLIC_HOST}/mcp/notion/"),
        required_scopes=["mcp:read"],
    ),
)


@notion_mcp.tool()
def search_notion(days: int = 365) -> str:
    """Search recent entries in the Notion cashflow database.

    Args:
        days: How many days back to search
    """
    data = search_recent(days=days)
    results = data.get("results", [])
    if not results:
        return "No matching pages found."
    return f"Found {len(results)} matching entries in the last {days} days."


@notion_mcp.tool()
def get_notion_schema() -> str:
    """Get the property/schema structure of the Notion cashflow database."""
    data = get_properties()
    props = data.get("properties", {})
    if not props:
        return "No properties found."
    return "Properties: " + ", ".join(props.keys())