"""模拟美食 MCP 服务（开发阶段用）"""

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn

server = Server("food-mcp")

MOCK_FOOD = {
    "成都市": {
        "dishes": [
            {
                "name": "火锅",
                "description": "成都灵魂美食，牛油锅底，麻辣鲜香",
                "price_range": "80-150元/人",
                "is_local_specialty": True,
            },
            {
                "name": "串串香",
                "description": "竹签穿食材，自选自烫",
                "price_range": "30-60元/人",
                "is_local_specialty": True,
            },
            {
                "name": "担担面",
                "description": "经典川味面食，麻辣咸香",
                "price_range": "10-20元",
                "is_local_specialty": True,
            },
            {
                "name": "麻婆豆腐",
                "description": "陈麻婆始创，麻辣烫嫩",
                "price_range": "20-35元",
                "is_local_specialty": True,
            },
            {
                "name": "龙抄手",
                "description": "皮薄馅嫩，红油飘香",
                "price_range": "15-30元",
                "is_local_specialty": True,
            },
        ],
        "districts": ["春熙路", "宽窄巷子", "建设路小吃街", "玉林路"],
    },
    "北京市": {
        "dishes": [
            {
                "name": "北京烤鸭",
                "description": "皮脆肉嫩，国宴名菜",
                "price_range": "100-200元/人",
                "is_local_specialty": True,
            },
            {
                "name": "炸酱面",
                "description": "老北京传统面食",
                "price_range": "15-30元",
                "is_local_specialty": True,
            },
        ],
        "districts": ["簋街", "王府井", "南锣鼓巷"],
    },
}


@server.list_tools()
async def list_tools():
    from mcp.types import Tool

    return [
        Tool(
            name="search_food",
            description="搜索城市美食",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    import json

    if name == "search_food":
        city = arguments.get("city", "")
        data = MOCK_FOOD.get(
            city,
            {
                "dishes": [
                    {
                        "name": "当地特色",
                        "description": "请自行探索",
                        "price_range": "未知",
                        "is_local_specialty": False,
                    }
                ],
                "districts": [],
            },
        )
        from mcp.types import TextContent

        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]


sse_transport = SseServerTransport("/sse")

app = Starlette(
    routes=[
        Route("/sse", sse_transport.handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse_transport.handle_message),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
