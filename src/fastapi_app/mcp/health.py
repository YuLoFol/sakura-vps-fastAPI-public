from mcp.server import MCPServer

health_mcp = MCPServer("Health")


@health_mcp.tool()
def health_check() -> str:
    """Check if the FastAPI server is healthy."""
    return "ok"