"""模拟门票 MCP 服务（开发阶段用，port 8002）

提供景点门票价格数据，供 AttractionSearchAgent 覆盖 LLM 估算的票价。
与 food_server.py / hotel_server.py 结构一致，走 MCP SSE 协议。
"""

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import json
import uvicorn

server = Server("ticket-mcp")

# 票价数据（单位：元）。key 与 destination_parser 输出一致（带"市"）
MOCK_TICKET = {
    "成都市": {
        "tickets": [
            {"name": "武侯祠", "price": 50},
            {"name": "锦里", "price": 0},
            {"name": "大熊猫繁育研究基地", "price": 55},
            {"name": "都江堰", "price": 80},
            {"name": "青城山", "price": 80},
            {"name": "杜甫草堂", "price": 50},
            {"name": "宽窄巷子", "price": 0},
        ]
    },
    "北京市": {
        "tickets": [
            {"name": "故宫", "price": 60},
            {"name": "天坛", "price": 15},
            {"name": "颐和园", "price": 30},
            {"name": "八达岭长城", "price": 40},
            {"name": "国家博物馆", "price": 0},
        ]
    },
    "西安市": {
        "tickets": [
            {"name": "兵马俑", "price": 120},
            {"name": "华清宫", "price": 120},
            {"name": "大雁塔", "price": 30},
            {"name": "城墙", "price": 54},
        ]
    },
    "杭州市": {
        "tickets": [
            {"name": "西湖", "price": 0},
            {"name": "灵隐寺", "price": 30},
            {"name": "千岛湖", "price": 130},
        ]
    },
}


@server.list_tools()
async def list_tools():
    from mcp.types import Tool

    return [
        Tool(
            name="search_ticket",
            description="查询指定城市的景点门票价格",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "目标城市"}},
                "required": ["city"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_ticket":
        city = arguments.get("city", "")
        data = MOCK_TICKET.get(
            city,
            {"tickets": []},  # 未知城市返回空列表 → 调用方降级到 LLM 票价
        )
        from mcp.types import TextContent

        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]

    return []


sse_transport = SseServerTransport("/sse")

app = Starlette(
    routes=[
        Route("/sse", sse_transport.handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse_transport.handle_message),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
