from fastmcp import FastMCP

mcp = FastMCP("ihoka-fastapi")

@mcp.tool()
def health_check() -> str:
    """Check if the FastAPI server is healthy"""
    return "ok"
