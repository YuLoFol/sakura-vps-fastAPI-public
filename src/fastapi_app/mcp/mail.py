from .hub import hub_mcp
from ..services.mail import read_latest_mail


@hub_mcp.tool()
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