import uuid
from .base import BaseAgent
from ..graph.state import TravelState


class CoordinatorAgent(BaseAgent):
    name = "coordinator"
    description = "任务初始化"

    async def run(self, state: TravelState) -> dict:
        return {
            "task_id": str(uuid.uuid4()),
            "progress": 0.05,
        }
