from datetime import date, timedelta
from .base import BaseAgent
from ..graph.state import TravelState


SYSTEM_PROMPT = """你是一个旅行信息解析专家。
从用户的自然语言输入中提取结构化旅行信息。
今天是 {today}，用于解析相对日期（如"下周"、"后天"）。
请严格按照 JSON 格式回复，不要多余文字。"""

USER_PROMPT = """用户输入：{query}

请提取：
1. destination: 目的地城市名（不要加"市"后缀，如"成都"）
2. start_date: 出发日期 YYYY-MM-DD
3. end_date: 返回日期 YYYY-MM-DD
4. traveler_count: 出行人数（未提及则为 1）
5. budget: 预算金额人民币（未提及则为 null）
6. preferences: 偏好标签列表（如["美食","历史","自然"]，未提及则为空列表）

回复纯 JSON。"""


class DestinationParserAgent(BaseAgent):
    name = "destination_parser"
    description = "解析用户的自然语言旅行需求"

    async def run(self, state: TravelState) -> dict:
        query = state["user_query"]
        today = date.today().isoformat()

        result = await self.llm.invoke_json(
            system=SYSTEM_PROMPT.format(today=today),
            user=USER_PROMPT.format(query=query),
        )

        destination = self._normalize_destination(result.get("destination", ""))
        traveler_count = max(1, min(20, result.get("traveler_count", 1)))
        budget = result.get("budget")
        if budget is not None:
            budget = abs(float(budget))

        start_date = result.get("start_date", "")
        end_date = result.get("end_date", "")
        if not start_date or not end_date:
            s = date.today() + timedelta(days=7)
            e = s + timedelta(days=2)
            start_date, end_date = s.isoformat(), e.isoformat()
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        return {
            "destination": destination,
            "travel_dates": {"start": start_date, "end": end_date},
            "traveler_count": traveler_count,
            "budget": budget,
            "preferences": result.get("preferences", []),
            "progress": 0.1,
        }

    def _normalize_destination(self, name: str) -> str:
        name = name.strip()
        for suffix in ["市", "省", "区", "县"]:
            if name.endswith(suffix):
                name = name[:-1]
        return name + "市" if name else "未知"
