from .base import BaseAgent
from ..graph.state import TravelState


SYSTEM = "你是一个旅行摘要撰写专家。用简洁优美的语言总结旅行计划。"

USER = """请根据以下信息撰写一段旅行摘要（200-300字）：

目的地：{destination}
日期：{start} 至 {end}
人数：{count} 人
预算：{budget}

行程概要：
{itinerary_summary}

预算总计：{budget_total}

请用第二人称（"你"）来写，语气轻松愉快。"""


class SummaryAgent(BaseAgent):
    name = "summary"
    description = "生成旅行摘要"

    async def run(self, state: TravelState) -> dict:
        destination = state["destination"]
        dates = state.get("travel_dates", {})
        itinerary = state.get("itinerary", [])
        budget_est = state.get("budget_estimate", {})

        summary_lines = []
        for day in itinerary[:5]:
            theme = day.get("theme", "")
            acts = [a.get("name", "") for a in day.get("activities", [])]
            summary_lines.append(f"Day {day.get('day', '?')}: {theme} - {', '.join(acts[:3])}")

        text = await self.llm.invoke(
            system=SYSTEM,
            user=USER.format(
                destination=destination,
                start=dates.get("start", ""),
                end=dates.get("end", ""),
                count=state.get("traveler_count", 1),
                budget=f"¥{state.get('budget', '不限')}" if state.get("budget") else "不限",
                itinerary_summary="\n".join(summary_lines) or "暂无详细行程",
                budget_total=f"¥{budget_est.get('total', 0)}",
            ),
        )

        return {"summary": text.strip(), "progress": 1.0}
