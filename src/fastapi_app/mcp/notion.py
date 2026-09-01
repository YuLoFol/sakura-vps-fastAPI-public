from mcp.server import MCPServer
from ..services.notion import get_properties, search_recent

notion_mcp = MCPServer("Notion")


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