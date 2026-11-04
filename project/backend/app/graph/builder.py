import asyncio
import json
from datetime import datetime
from langgraph.graph import StateGraph, START, END

from .state import TravelState
from ..agents.coordinator import CoordinatorAgent
from ..agents.destination import DestinationParserAgent
from ..agents.attraction import AttractionSearchAgent
from ..agents.weather import WeatherQueryAgent
from ..agents.hotel import HotelRecommendAgent
from ..agents.food import FoodPlanAgent
from ..agents.transport import TransportPlanAgent
from ..agents.budget import BudgetEstimateAgent
from ..agents.image import ImageSearchAgent
from ..agents.compiler import ItineraryCompilerAgent
from ..agents.validator import ValidationAgent
from ..agents.summary import SummaryAgent


class EventEmittingAgent:
    """带事件推送的 Agent 包装器

    支持两种事件通道：
    - asyncio.Queue（旧版，内存，单进程）
    - EventPublisher（新版，Redis Pub/Sub，多进程）
    """

    def __init__(self, agent, queue: asyncio.Queue | None = None,
                 publisher=None, task_id: str = ""):
        self.agent = agent
        self.queue = queue
        self.publisher = publisher     # EventPublisher 实例
        self.task_id = task_id
        self.name = agent.name

    async def _emit(self, event: dict):
        """发送事件到所有通道"""
        event_json = json.dumps(event, ensure_ascii=False)
        if self.queue:
            await self.queue.put(event_json)
        if self.publisher:
            await self.publisher.publish(self.task_id, event)

    async def __call__(self, state: TravelState) -> dict:
        await self._emit({
            "type": "node_start",
            "node": self.agent.name,
            "timestamp": datetime.now().isoformat(),
            "details": f"开始执行 {self.agent.description}"
        })

        update = await self.agent(state)

        # 获取节点执行状态
        node_status = update.get("node_status", {}).get(self.agent.name, "completed")

        # 添加详细的执行信息
        details = f"完成执行 {self.agent.description}"
        if node_status == "failed":
            error_info = update.get("errors", [])
            if error_info and isinstance(error_info, list) and len(error_info) > 0:
                details = f"执行失败: {error_info[0].get('message', '未知错误')}"
            else:
                details = "执行失败，未知原因"

        await self._emit({
            "type": "node_complete",
            "node": self.agent.name,
            "status": node_status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })

        return update


def build_travel_graph(
    queue: asyncio.Queue | None = None,
    publisher=None,
    task_id: str = "",
) -> StateGraph:
    """构建完整的旅行规划 DAG

    Args:
        queue: asyncio.Queue（旧版兼容）
        publisher: EventPublisher（Redis Pub/Sub）
        task_id: 任务 ID（Pub/Sub 需要）
    """

    def wrap(agent):
        if queue or publisher:
            return EventEmittingAgent(
                agent, queue=queue, publisher=publisher, task_id=task_id
            )
        return agent

    graph = StateGraph(TravelState)

    graph.add_node("coordinator", wrap(CoordinatorAgent()))
    graph.add_node("destination_parser", wrap(DestinationParserAgent()))
    graph.add_node("attraction", wrap(AttractionSearchAgent()))
    graph.add_node("weather", wrap(WeatherQueryAgent()))
    graph.add_node("hotel", wrap(HotelRecommendAgent()))
    graph.add_node("food", wrap(FoodPlanAgent()))
    graph.add_node("transport", wrap(TransportPlanAgent()))
    graph.add_node("budget", wrap(BudgetEstimateAgent()))
    graph.add_node("image", wrap(ImageSearchAgent()))
    graph.add_node("compiler", wrap(ItineraryCompilerAgent()))
    graph.add_node("validator", wrap(ValidationAgent()))
    graph.add_node("summary", wrap(SummaryAgent()))

    # fan-in 汇聚节点
    graph.add_node("sync_tier2", lambda s: {})
    graph.add_node("sync_tier3", lambda s: {})

    # 边定义
    graph.add_edge(START, "coordinator")
    graph.add_edge("coordinator", "destination_parser")

    # destination -> 并行扇出
    graph.add_conditional_edges(
        "destination_parser",
        lambda s: ["attraction", "weather", "hotel"],
        ["attraction", "weather", "hotel"],
    )

    graph.add_edge("attraction", "sync_tier2")
    graph.add_edge("weather", "sync_tier2")
    graph.add_edge("hotel", "sync_tier2")

    graph.add_conditional_edges(
        "sync_tier2",
        lambda s: ["food", "transport"],
        ["food", "transport"],
    )

    graph.add_edge("food", "sync_tier3")
    graph.add_edge("transport", "sync_tier3")

    graph.add_edge("sync_tier3", "budget")
    graph.add_edge("budget", "image")
    graph.add_edge("image", "compiler")
    graph.add_edge("compiler", "validator")
    graph.add_edge("validator", "summary")
    graph.add_edge("summary", END)

    return graph.compile()
