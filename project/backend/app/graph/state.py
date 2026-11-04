from typing import TypedDict, Annotated
from operator import add


def merge_dict(left: dict, right: dict) -> dict:
    """字典合并 reducer——供并行节点并发写 node_status 用。

    LangGraph 默认通道是 last_value（只允许每步一个写入者）。
    并行扇出的多个节点（attraction/weather/hotel）会各自返回
    {"node_status": {自己名字: "completed"}}，同一 step 并发写入会让
    last_value 通道抛 InvalidUpdateError。加 reducer 后改为合并写入。
    """
    merged = dict(left or {})
    merged.update(right or {})
    return merged


def last_value(left, right):
    """取后者——给 progress 这类可能在并行 step 被多节点写入的标量兜底。"""
    return right if right is not None else left


class TravelState(TypedDict, total=False):
    # --- 输入 ---
    user_query: str
    task_id: str

    # --- 目的地解析 ---
    destination: str
    travel_dates: dict
    traveler_count: int
    budget: float | None
    preferences: list[str]

    # --- 各 Agent 输出 ---
    attractions: list[dict]
    recommendation_meta: dict
    weather_info: dict
    hotel_recommendations: list[dict]
    food_plan: dict
    transport_plan: dict
    budget_estimate: dict
    image_urls: list[str]

    # --- 最终输出 ---
    itinerary: list[dict]
    validation_result: dict
    summary: str

    # --- 元数据（需 reducer，因并行节点并发写入）---
    errors: Annotated[list[dict], add]
    node_status: Annotated[dict, merge_dict]
    progress: Annotated[float, last_value]
