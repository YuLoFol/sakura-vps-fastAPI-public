from .hub import hub_mcp


@hub_mcp.tool()
def health_check() -> str:
    """Check if the MCP hub is healthy."""
    return "ok"