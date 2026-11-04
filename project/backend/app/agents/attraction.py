import json
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import Attraction
from ..utils.algorithms import ContentRecommender


SYSTEM = "你是一个旅行景点推荐专家。根据目的地和偏好推荐景点。回复纯 JSON 数组。"

USER = """目的地：{destination}
偏好：{preferences}

请推荐 5-8 个热门景点，每个景点包含：
- name: 景点名
- description: 一句话简介
- category: 类别（自然/历史/文化/主题公园/博物馆）
- estimated_duration_hours: 游玩时长（小时）
- ticket_price: 门票价格（免费则为0）
- best_time_to_visit: 最佳游览时间
- tips: 游玩建议（2-3条）
- location: {{"lat": 纬度, "lng": 经度}}（如知道的话）

回复纯 JSON 数组。"""


async def _query_ticket_mcp(destination: str) -> dict[str, float] | None:
    """查询门票 MCP 服务，返回 {景点名: 票价} 映射。

    用于覆盖 LLM 估算的票价，提供更真实的门票数据。
    MCP 客户端 safe_call_tool 返回 CallToolResult（.content 列表），
    失败返回 None。
    """
    from ..mcp.manager import get_mcp_client

    client = get_mcp_client("ticket")
    if not client:
        return None

    result = await client.safe_call_tool("search_ticket", {"city": destination})
    if not result or not getattr(result, "content", None):
        return None

    try:
        for content in result.content:
            text = getattr(content, "text", None)
            if not text:
                continue
            data = json.loads(text)
            if isinstance(data, dict):
                payload = data.get("tickets", data)
                if isinstance(payload, list):
                    return {t.get("name", ""): t.get("price", 0) for t in payload}
                if isinstance(payload, dict):
                    return {k: float(v) for k, v in payload.items() if v is not None}
    except (json.JSONDecodeError, AttributeError, ValueError, TypeError):
        return None
    return None


def _build_text(attraction: dict) -> str:
    """把景点的 category / description / tips 拼成 TF-IDF 文本"""
    parts = [attraction.get("category", ""), attraction.get("description", "")]
    parts.extend(attraction.get("tips", []) or [])
    return " ".join(str(p) for p in parts if p)


class AttractionSearchAgent(BaseAgent):
    name = "attraction"
    description = "搜索目的地景点（TF-IDF 偏好排序 + 门票 MCP）"

    async def run(self, state: TravelState) -> dict:
        destination = state["destination"]
        preferences = state.get("preferences", [])

        text = await self.llm.invoke(
            system=SYSTEM,
            user=USER.format(
                destination=destination,
                preferences=", ".join(preferences) or "无特殊偏好",
            ),
        )

        try:
            raw = text.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:-1])
            items = json.loads(raw)
            attractions = [Attraction(**item).model_dump() for item in items]
        except Exception as e:
            return {"attractions": [], "errors": [{"node": self.name, "error": f"解析失败: {e}"}]}

        if not attractions:
            return {"attractions": []}

        # === 1. 门票 MCP 覆盖真实票价 ===
        ticket_map = await _query_ticket_mcp(destination)
        if ticket_map:
            for a in attractions:
                price = ticket_map.get(a.get("name"))
                if price is not None and price > 0:
                    a["ticket_price"] = float(price)

        # === 2. TF-IDF 内容推荐：按用户偏好重排景点 ===
        # 算法含金量点：ContentRecommender（纯 Python TF-IDF + 余弦相似度）
        # 把每个景点的 category+description+tips 向量化，与用户偏好向量计算
        # 余弦相似度，按相关度排序——让"偏好"真正影响景点顺序，而非依赖 LLM。
        meta = None
        if preferences:
            for a in attractions:
                a["_text"] = _build_text(a)
            recommender = ContentRecommender()
            recommender.fit(attractions, text_key="_text")
            query = " ".join(preferences)
            ranked = recommender.recommend(query, top_k=len(attractions))
            # recommend 返回的是按相似度降序的景点；补回任何没被命中的尾部
            ranked_names = {r.get("name") for r in ranked}
            tail = [a for a in attractions if a.get("name") not in ranked_names]
            attractions = ranked + tail
            for a in attractions:
                a.pop("_text", None)
            meta = {
                "algorithm": "TF-IDF + cosine similarity",
                "preference_query": query,
                "ranked_by_preference": True,
            }

        result = {"attractions": attractions}
        if meta:
            result["recommendation_meta"] = meta
        return result
