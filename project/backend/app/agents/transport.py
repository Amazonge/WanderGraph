import json
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import TransportPlan, TransportOption


SYSTEM = "你是一个交通出行规划专家。回复纯 JSON。"

USER = """目的地：{destination}

请给出：
1. arrival_options: 到达方式（飞机/高铁/自驾），每个含 mode, duration, price_range, tips
2. local_transport: 市内交通建议（列表，每个含 mode 和 description）
3. transport_cards: 可用的交通卡/APP（列表）

回复纯 JSON。"""


class TransportPlanAgent(BaseAgent):
    name = "transport"
    description = "交通规划"

    async def run(self, state: TravelState) -> dict:
        destination = state["destination"]

        text = await self.llm.invoke(
            system=SYSTEM,
            user=USER.format(destination=destination),
        )

        try:
            raw = text.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:-1])
            data = json.loads(raw)
            plan = TransportPlan(
                arrival_options=[TransportOption(**o) for o in data.get("arrival_options", [])],
                local_transport=data.get("local_transport", []),
                transport_cards=data.get("transport_cards", []),
            )
            return {"transport_plan": plan.model_dump()}
        except Exception:
            return {"transport_plan": TransportPlan().model_dump()}
