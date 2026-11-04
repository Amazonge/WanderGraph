import json
from datetime import date
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import WeatherInfo, DailyWeather


SYSTEM = "你是一个天气预报助手。根据目的地和日期范围给出天气预报。回复纯 JSON。"

USER = """目的地：{destination}
日期范围：{start} 到 {end}（共 {days} 天）

请给出：
1. forecast: 每天的天气预报，含 date(YYYY-MM-DD), temp_high, temp_low, condition(晴/多云/雨/阴等), humidity
2. summary: 天气总评（一句话）
3. packing_tips: 穿衣/行李建议（2-3条）

回复纯 JSON。"""


class WeatherQueryAgent(BaseAgent):
    name = "weather"
    description = "查询目的地天气"

    async def run(self, state: TravelState) -> dict:
        destination = state["destination"]
        dates = state["travel_dates"]
        days = (date.fromisoformat(dates["end"]) - date.fromisoformat(dates["start"])).days + 1

        text = await self.llm.invoke(
            system=SYSTEM,
            user=USER.format(
                destination=destination,
                start=dates["start"],
                end=dates["end"],
                days=days,
            ),
        )

        try:
            raw = text.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:-1])
            data = json.loads(raw)
            info = WeatherInfo(
                destination=destination,
                forecast=[DailyWeather(**d) for d in data.get("forecast", [])],
                summary=data.get("summary", ""),
                packing_tips=data.get("packing_tips", []),
            )
            return {"weather_info": info.model_dump()}
        except Exception as e:
            return {
                "weather_info": {"destination": destination, "summary": "暂无天气数据"},
                "errors": [{"node": self.name, "error": str(e)}],
            }
