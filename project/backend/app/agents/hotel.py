import json
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import HotelRecommendation


SYSTEM = "你是一个酒店推荐专家。推荐适合的住宿。回复纯 JSON 数组。"

USER = """目的地：{destination}
预算：{budget}
人数：{count} 人

请推荐 3-5 家酒店，每个包含：
- name: 酒店名
- star_rating: 星级（1-5）
- price_range: 价格区间（如"¥200-400/晚"）
- location_description: 位置描述
- highlights: 特色亮点（列表）
- suitable_for: 适合人群（列表）
- booking_tips: 预订建议

回复纯 JSON 数组。"""


async def _query_hotel_mcp(destination: str, budget) -> list[dict] | None:
    """查询酒店 MCP 服务获取真实酒店数据

    MCP 客户端 safe_call_tool 返回 CallToolResult（含 .content 列表），
    每个 content 是 TextContent（含 .text 字段）。失败返回 None。
    """
    from ..mcp.manager import get_mcp_client

    client = get_mcp_client("hotel")
    if not client:
        return None

    result = await client.safe_call_tool("search_hotel", {
        "destination": destination,
        "budget": budget,
    })

    if not result or not getattr(result, "content", None):
        return None

    try:
        for content in result.content:
            text = getattr(content, "text", None)
            if text:
                data = json.loads(text)
                # MCP 返回 {"hotels": [...]} 结构
                if isinstance(data, dict):
                    return data.get("hotels", [])
                if isinstance(data, list):
                    return data
    except (json.JSONDecodeError, AttributeError):
        return None

    return None


class HotelRecommendAgent(BaseAgent):
    name = "hotel"
    description = "推荐住宿酒店"

    async def run(self, state: TravelState) -> dict:
        destination = state["destination"]
        budget = state.get("budget")
        count = state.get("traveler_count", 1)

        # 1. 优先 MCP 服务（有真实数据时直接用，跳过 LLM）
        mcp_hotels = await _query_hotel_mcp(destination, budget)
        if mcp_hotels:
            hotels = [HotelRecommendation(**h).model_dump() for h in mcp_hotels]
            return {"hotel_recommendations": hotels}

        # 2. MCP 失败或无数据 → 回退到 LLM 生成
        text = await self.llm.invoke(
            system=SYSTEM,
            user=USER.format(
                destination=destination,
                budget=f"¥{budget}" if budget else "不限",
                count=count,
            ),
        )

        try:
            raw = text.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:-1])
            items = json.loads(raw)
            hotels = [HotelRecommendation(**i).model_dump() for i in items]
        except Exception:
            hotels = []

        return {"hotel_recommendations": hotels}
