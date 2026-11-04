from typing import Any
from contextlib import AsyncExitStack


class MCPClient:
    """MCP SSE 客户端 - 懒连接 + 失败降级"""

    def __init__(self, server_url: str, name: str = "mcp"):
        self.server_url = server_url
        self.name = name
        self._session = None
        self._exit_stack: AsyncExitStack | None = None
        self._connected = False

    async def connect(self):
        if self._connected and self._session:
            return self._session
        try:
            from mcp import ClientSession
            from mcp.client.sse import sse_client

            self._exit_stack = AsyncExitStack()
            read, write = await self._exit_stack.enter_async_context(
                sse_client(self.server_url)
            )
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self._session.initialize()
            self._connected = True
            print(f"[MCP:{self.name}] 已连接")
            return self._session
        except Exception as e:
            print(f"[MCP:{self.name}] 连接失败: {e}")
            self._connected = False
            raise

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]):
        session = await self.connect()
        return await session.call_tool(tool_name, arguments)

    async def safe_call_tool(self, tool_name: str, arguments: dict):
        try:
            return await self.call_tool(tool_name, arguments)
        except Exception as e:
            print(f"[MCP:{self.name}] 调用失败: {e}")
            return None

    async def close(self):
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._connected = False
