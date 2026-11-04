"""诊断 compiler/food agent 的 LLM 原始输出与解析异常。
把原始文本与异常写到文件，避免 Windows GBK 控制台打印报错。"""
import asyncio
import json
import os
import sys

# 统一用 utf-8，避免 GBK 控制台崩
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.utils.llm import get_llm
from app.utils.algorithms import optimize_daily_route
from app.agents import compiler as C
from app.agents import food as F

TMP = "C:/Users/29558/AppData/Local/Temp"


def _dump(d, i=2):
    return json.dumps(d, ensure_ascii=False, indent=i)


def write(name, text):
    with open(f"{TMP}/{name}", "w", encoding="utf-8") as f:
        f.write(text)


state = {
    "destination": "成都市",
    "travel_dates": {"start": "2026-07-22", "end": "2026-07-23"},
    "traveler_count": 1,
    "preferences": ["历史", "美食"],
    "attractions": [
        {
            "name": "武侯祠", "category": "历史",
            "location": {"lat": 30.646, "lng": 104.053},
            "ticket_price": 50, "description": "三国历史遗迹", "tips": [],
        }
    ],
    "weather_info": {"summary": "晴"},
    "hotel_recommendations": [{"name": "酒店A", "price_range": "¥300/晚"}],
    "food_plan": {"must_try_dishes": [{"name": "火锅", "price_range": "100元"}]},
    "budget_estimate": {"total": 4500},
}


async def diag_compiler():
    optimized = optimize_daily_route(state["attractions"])
    order_desc = "\n".join(
        f"  {i+1}. {s.get('name', '?')}" for i, s in enumerate(optimized[:10])
    )
    llm = get_llm()
    text = await llm.invoke(
        system=C.SYSTEM.format(optimized_order=order_desc),
        user=C.USER.format(
            destination="成都市", start="2026-07-22", end="2026-07-23",
            days=2, count=1, preferences="历史,美食",
            attractions=_dump([s for s in optimized[:10]]),
            weather=_dump(state["weather_info"]),
            hotels=_dump(state["hotel_recommendations"][:3]),
            food=_dump(state["food_plan"]),
            budget=_dump(state["budget_estimate"]),
        ),
    )
    write("compiler_raw.txt", text)

    raw = text.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    try:
        items = json.loads(raw)
        if isinstance(items, dict) and "days" in items:
            items = items["days"]
        write("compiler_items.json", json.dumps(items, ensure_ascii=False, indent=2))
        from app.models.travel import DayPlan
        try:
            dp = [DayPlan(**item).model_dump() for item in items]
            write("compiler_ok.txt", f"OK len={len(dp)}")
        except Exception as e:
            write(
                "compiler_dayplan_err.txt",
                repr(e) + "\n\nFIRST_ITEM=" +
                (json.dumps(items[0], ensure_ascii=False, indent=2) if items else "empty"),
            )
    except Exception as e:
        write("compiler_json_err.txt", repr(e) + "\n\nRAW_HEAD=" + raw[:800])


async def diag_food():
    llm = get_llm()
    text = await llm.invoke(
        system=F.SYSTEM,
        user=F.USER.format(
            destination="成都市", count=1, preferences="历史,美食",
            budget=_dump(state["budget_estimate"]),
        ),
    )
    write("food_raw.txt", text)

    raw = text.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    try:
        items = json.loads(raw)
        if isinstance(items, dict) and "dishes" in items:
            items = items["dishes"]
        write("food_items.json", json.dumps(items, ensure_ascii=False, indent=2))
        from app.models.travel import Dish
        try:
            dp = [Dish(**item).model_dump() for item in items]
            write("food_ok.txt", f"OK len={len(dp)}")
        except Exception as e:
            write(
                "food_dish_err.txt",
                repr(e) + "\n\nFIRST_ITEM=" +
                (json.dumps(items[0], ensure_ascii=False, indent=2) if items else "empty"),
            )
    except Exception as e:
        write("food_json_err.txt", repr(e) + "\n\nRAW_HEAD=" + raw[:800])


async def main():
    await diag_compiler()
    await diag_food()


if __name__ == "__main__":
    asyncio.run(main())
    print("done")
