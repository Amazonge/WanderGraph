from .client import MCPClient
from ..config import settings

_clients: dict[str, MCPClient] = {}


def get_mcp_client(service: str) -> MCPClient | None:
    """获取（懒创建）MCP 客户端单例。配置中无对应 URL 则返回 None。"""
    if service in _clients:
        return _clients[service]
    url_map = {
        "food": settings.FOOD_MCP_URL,
        "hotel": settings.HOTEL_MCP_URL,
        "ticket": settings.TICKET_MCP_URL,
    }
    url = url_map.get(service)
    if not url:
        return None
    client = MCPClient(url, name=service)
    _clients[service] = client
    return client


async def close_all_clients() -> None:
    """关闭所有 MCP 客户端连接（FastAPI shutdown 时调用）"""
    for client in _clients.values():
        try:
            await client.close()
        except Exception:
            pass
    _clients.clear()

