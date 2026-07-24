import os
import asyncio

from dotenv import load_dotenv, main
from langchain_mcp_adapters.client import MultiServerMCPClient

#load_dotenv()
load_dotenv(override=True)

client = MultiServerMCPClient(
    {
        "discord": {
            "transport": "stdio",
            "command": "uv",
            "args": [
                "--directory",
                r"F:\mcp_project\discord-issue-log\mcp-discord",
                "run",
                "mcp-discord"
            ],
            "env": {
                "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN", "")
            }
        }
    }
)


# tools discovery
# async def main():

#     tools = await client.get_tools()

#     print("\nAvailable MCP Tools:\n")

#     for tool in tools:
#         print(tool.name)

async def main():
    tools = await client.get_tools()

    search_tool = next(
        tool
        for tool in tools
        if tool.name == "read_messages"
    )

    channel_id = os.getenv("DISCORD_CHANNEL_ID", "1520050450999672873")

    result = await search_tool.ainvoke(
        {
            "channel_id": channel_id,
            "limit": 5
        }
    )

    print(result)


# search_tool = None

# async def initialize_mcp():

#     global search_tool


#     if search_tool is not None:
#         return

#     tools = await client.get_tools()

#     print("\nAvailable MCP Tools:\n")

#     for tool in tools:
#         print(tool.name)

#     search_tool = next(
#         tool
#         for tool in tools
#         if tool.name == "read_messages"
#     )


if __name__ == "__main__":
    asyncio.run(main())
