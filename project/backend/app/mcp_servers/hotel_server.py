"""模拟酒店 MCP 服务（开发阶段用）"""

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn
import json

server = Server("hotel-mcp")

# 酒店数据模板
MOCK_HOTEL = {
    "北京市": {
        "hotels": [
            {
                "name": "北京饭店",
                "star_rating": 5,
                "price_range": "¥800-1500/晚",
                "location_description": "位于北京市中心，靠近天安门广场",
                "highlights": ["豪华装修", "地理位置优越", "服务优质"],
                "suitable_for": ["商务旅行", "观光旅游"],
                "booking_tips": "建议提前预订，旺季价格较高"
            },
            {
                "name": "北京国际酒店",
                "star_rating": 4,
                "price_range": "¥500-800/晚",
                "location_description": "位于朝阳区，交通便利",
                "highlights": ["设施齐全", "性价比高", "靠近地铁站"],
                "suitable_for": ["家庭旅行", "商务出差"],
                "booking_tips": "地铁10号线直达，适合预算有限的旅客"
            },
            {
                "name": "北京青年旅舍",
                "star_rating": 2,
                "price_range": "¥150-300/晚",
                "location_description": "位于海淀区，靠近大学城",
                "highlights": ["价格实惠", "青年氛围", "交通便利"],
                "suitable_for": ["背包客", "学生"],
                "booking_tips": "需要提前确认床位，旺季可能满房"
            }
        ]
    },
    "上海市": {
        "hotels": [
            {
                "name": "上海外滩华尔道夫酒店",
                "star_rating": 5,
                "price_range": "¥1200-2000/晚",
                "location_description": "位于外滩，黄浦江畔",
                "highlights": ["江景房", "豪华设施", "地理位置绝佳"],
                "suitable_for": ["高端商务", "蜜月旅行"],
                "booking_tips": "提前3个月预订，价格较高"
            },
            {
                "name": "上海静安寺酒店",
                "star_rating": 4,
                "price_range": "¥600-1000/晚",
                "location_description": "位于静安区，靠近静安寺",
                "highlights": ["安静舒适", "商务设施完善", "交通便利"],
                "suitable_for": ["商务会议", "休闲旅游"],
                "booking_tips": "靠近2号线静安寺站，出行方便"
            },
            {
                "name": "上海青年旅舍",
                "star_rating": 2,
                "price_range": "¥180-350/晚",
                "location_description": "位于浦东新区，靠近陆家嘴",
                "highlights": ["价格便宜", "青年氛围", "地理位置好"],
                "suitable_for": ["背包客", "学生"],
                "booking_tips": "靠近地铁2号线，出行方便"
            }
        ]
    },
    "广州市": {
        "hotels": [
            {
                "name": "广州白天鹅宾馆",
                "star_rating": 5,
                "price_range": "¥900-1600/晚",
                "location_description": "位于沙面岛，珠江边",
                "highlights": ["历史悠久的五星级酒店", "江景房", "环境优美"],
                "suitable_for": ["商务会议", "休闲度假"],
                "booking_tips": "需要提前预订，周末价格较高"
            },
            {
                "name": "广州花园酒店",
                "star_rating": 4,
                "price_range": "¥600-900/晚",
                "location_description": "位于越秀区，市中心位置",
                "highlights": ["交通便利", "设施齐全", "服务好"],
                "suitable_for": ["商务出差", "旅游观光"],
                "booking_tips": "地铁1号线公园前站附近，出行方便"
            },
            {
                "name": "广州青年旅舍",
                "star_rating": 2,
                "price_range": "¥150-300/晚",
                "location_description": "位于天河区，体育中心附近",
                "highlights": ["价格实惠", "青年氛围", "交通便利"],
                "suitable_for": ["背包客", "学生"],
                "booking_tips": "靠近地铁1号线体育中心站"
            }
        ]
    },
    "深圳市": {
        "hotels": [
            {
                "name": "深圳君悦酒店",
                "star_rating": 5,
                "price_range": "¥1000-1800/晚",
                "location_description": "位于福田区，市民中心附近",
                "highlights": ["豪华设施", "地理位置优越", "服务优质"],
                "suitable_for": ["商务会议", "高端旅游"],
                "booking_tips": "提前预订，价格较高"
            },
            {
                "name": "深圳京基100酒店",
                "star_rating": 4,
                "price_range": "¥700-1200/晚",
                "location_description": "位于罗湖区，京基100大厦内",
                "highlights": ["高空景观", "设施齐全", "交通便利"],
                "suitable_for": ["商务出差", "观光旅游"],
                "booking_tips": "地铁1号线老街站附近，出行方便"
            },
            {
                "name": "深圳青年旅舍",
                "star_rating": 2,
                "price_range": "¥160-320/晚",
                "location_description": "位于南山区，科技园附近",
                "highlights": ["价格实惠", "青年氛围", "交通便利"],
                "suitable_for": ["背包客", "学生"],
                "booking_tips": "靠近地铁1号线科技园站"
            }
        ]
    }
}

@server.list_tools()
async def list_tools():
    from mcp.types import Tool

    return [
        Tool(
            name="search_hotel",
            description="搜索指定城市的酒店信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "目标城市"
                    },
                    "budget": {
                        "type": "string",
                        "description": "预算范围（可选）"
                    }
                },
                "required": ["destination"]
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_hotel":
        destination = arguments.get("destination", "")
        budget = arguments.get("budget", "")

        # 获取对应城市的酒店数据
        data = MOCK_HOTEL.get(
            destination,
            {
                "hotels": [
                    {
                        "name": "当地酒店",
                        "star_rating": 3,
                        "price_range": "¥300-600/晚",
                        "location_description": "请自行探索",
                        "highlights": ["待探索", "待发现"],
                        "suitable_for": ["各类旅客"],
                        "booking_tips": "建议提前预订"
                    }
                ]
            },
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
    uvicorn.run(app, host="0.0.0.0", port=8003)