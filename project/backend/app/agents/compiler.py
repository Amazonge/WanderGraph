import json
from datetime import date
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import DayPlan
from ..utils.algorithms import optimize_daily_route, total_distance
from ..utils.llm import parse_json


SYSTEM = """你是一个专业的旅行规划师。根据所有提供的信息编排逐日行程。

以下景点已按地理位置最优顺序排列（路线优化结果），请严格按照此顺序编排每天的活动：
{optimized_order}

请确保行程合理：按给定的景点顺序安排活动、根据天气调整室内/室外、合理分配时间。
回复纯 JSON 数组。"""

USER = """请为以下旅行编排详细行程：

目的地：{destination}
日期：{start} 至 {end}（共 {days} 天）
人数：{count} 人
偏好：{preferences}

景点（已按最优路线排序）：
{attractions}

天气预报：
{weather}

酒店推荐：
{hotels}

美食推荐：
{food}

预算参考：
{budget}

请编排 {days} 天的逐日行程。每天包含：
- day: 天数
- date: 日期
- theme: 当天主题
- weather_note: 天气提醒
- activities: 活动列表（每个含 time, name, description, duration_hours, ticket_price, transport_to_next）
- meals: 餐饮（含 type[breakfast/lunch/dinner], time, restaurant, dishes, estimated_cost）
- accommodation: 住宿
- daily_budget_estimate: 当日预算
- tips: 当日建议

回复纯 JSON 数组，每个元素是一天的行程。"""


class ItineraryCompilerAgent(BaseAgent):
    name = "compiler"
    description = "行程编排（含路线优化）"

    async def run(self, state: TravelState) -> dict:
        dates = state["travel_dates"]
        days = (date.fromisoformat(dates["end"]) - date.fromisoformat(dates["start"])).days + 1
        attractions = state.get("attractions", [])

        # === 路线优化：贪心 + 2-opt ===
        optimized = optimize_daily_route(attractions)
        dist_before = total_distance(attractions)
        dist_after = total_distance(optimized)
        reduction = ((dist_before - dist_after) / dist_before * 100) if dist_before > 0 else 0

        # 构建优化后的景点顺序描述（None 安全：列表元素或字段可能为 null）
        order_desc = "\n".join(
            f"  {i+1}. {(s or {}).get('name', '?')} ({(s or {}).get('category', '')})"
            for i, s in enumerate(optimized[:10])
        )

        def _dump(data, indent=2):
            return json.dumps(data, ensure_ascii=False, indent=indent)

        text = await self.llm.invoke(
            system=SYSTEM.format(optimized_order=order_desc),
            user=USER.format(
                destination=state["destination"],
                start=dates["start"],
                end=dates["end"],
                days=days,
                count=state.get("traveler_count", 1),
                preferences=", ".join(state.get("preferences", [])) or "无",
                attractions=_dump([s for s in optimized[:10]]),
                weather=_dump(state.get("weather_info", {})),
                hotels=_dump(state.get("hotel_recommendations", [])[:3]),
                food=_dump(state.get("food_plan", {})),
                budget=_dump(state.get("budget_estimate", {})),
            ),
        )

        # 容错解析：parse_json 自动去 markdown 围栏 + 用 raw_decode 忽略
        # LLM 在合法 JSON 后多吐的尾部垃圾（如多余的 `}}`）。
        items = parse_json(text)
        if isinstance(items, dict) and "days" in items:
            items = items["days"]
        if not isinstance(items, list):
            items = []
        itinerary = []
        for item in items:
            try:
                itinerary.append(DayPlan(**item).model_dump())
            except Exception:
                # 单日解析失败不丢掉整份行程，跳过坏的那天
                continue

        # LLM 经常不严格遵守请求天数（用户要 2 天却生成 3 天）。
        # 按实际请求天数截断，保证 itinerary 与 travel_dates 一致。
        if days > 0 and len(itinerary) > days:
            itinerary = itinerary[:days]

        return {
            "itinerary": itinerary,
            "route_optimization": {
                "original_distance_km": round(dist_before, 2),
                "optimized_distance_km": round(dist_after, 2),
                "reduction_percent": round(reduction, 1),
                "optimized_order": [(s or {}).get("name", "") for s in optimized],
            },
        }
