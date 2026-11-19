import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def get_mcp_client(emp_id: str | None = None) -> MultiServerMCPClient:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set in backend/.env")

    if emp_id:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}options=-c%20app.emp_id%3D{emp_id}"

    return MultiServerMCPClient(
        {
            "postgres": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres", db_url],
                "transport": "stdio",
            }
        }
    )


async def load_postgres_tools(emp_id: str | None = None):
    client = get_mcp_client(emp_id)
    return await client.get_tools()