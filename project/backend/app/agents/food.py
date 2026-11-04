import json
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import FoodPlan, Dish
from ..utils.llm import parse_json


SYSTEM = "你是一个美食规划专家。根据提供的数据编排美食计划。回复纯 JSON。"

USER_WITH_MCP = """目的地：{destination}
美食数据：
{mcp_data}

请基于以上数据编排：
1. must_try_dishes: 必吃美食列表（每个含 name, description, price_range, is_local_specialty）
2. food_districts: 美食街区（列表）
3. dietary_notes: 饮食注意事项

回复纯 JSON。"""

USER_FALLBACK = """目的地：{destination}
偏好：{preferences}

请推荐当地必吃美食（5-8个），美食街区（3-5个），饮食注意事项。
回复纯 JSON，含 must_try_dishes, food_districts, dietary_notes。"""


class FoodPlanAgent(BaseAgent):
    name = "food"
    description = "美食规划"

    async def run(self, state: TravelState) -> dict:
        destination = state["destination"]
        preferences = state.get("preferences", [])

        mcp_data = await self._query_mcp(destination)

        if mcp_data:
            text = await self.llm.invoke(
                system=SYSTEM,
                user=USER_WITH_MCP.format(
                    destination=destination,
                    mcp_data=json.dumps(mcp_data, ensure_ascii=False),
                ),
            )
        else:
            text = await self.llm.invoke(
                system=SYSTEM,
                user=USER_FALLBACK.format(
                    destination=destination,
                    preferences=", ".join(preferences) or "无",
                ),
            )

        data = parse_json(text)
        if not isinstance(data, dict):
            return {"food_plan": FoodPlan().model_dump()}

        # LLM 有时把 must_try_dishes 返回成字符串数组 ["麻婆豆腐", ...]
        # 而非对象数组，这里两种形态都兼容，避免 Dish(**str) 抛错回退空。
        dishes = []
        for d in data.get("must_try_dishes", []):
            try:
                if isinstance(d, str):
                    dishes.append(Dish(name=d))
                elif isinstance(d, dict):
                    dishes.append(Dish(**d))
            except Exception:
                continue

        try:
            plan = FoodPlan(
                must_try_dishes=dishes,
                food_districts=data.get("food_districts", []),
                dietary_notes=data.get("dietary_notes", ""),
            )
            return {"food_plan": plan.model_dump()}
        except Exception:
            return {"food_plan": FoodPlan().model_dump()}

    async def _query_mcp(self, destination: str) -> dict | None:
        try:
            from ..mcp.manager import get_mcp_client

            client = get_mcp_client("food")
            if not client:
                return None
            result = await client.safe_call_tool("search_food", {"city": destination})
            if result and hasattr(result, "content"):
                for content in result.content:
                    if hasattr(content, "text"):
                        return json.loads(content.text)
            return None
        except Exception:
            return None
