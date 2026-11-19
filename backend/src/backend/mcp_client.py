import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def get_mcp_client() -> MultiServerMCPClient:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set in backend/.env")

    return MultiServerMCPClient(
        {
            "postgres": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres", db_url],
                "transport": "stdio",
            }
        }
    )


async def load_postgres_tools():
    client = get_mcp_client()
    return await client.get_tools()