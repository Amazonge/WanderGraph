from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..graph.state import TravelState


class BaseAgent(ABC):
    """Agent 基类"""

    name: str = ""
    description: str = ""

    def __init__(self):
        from ..utils.llm import get_llm

        self.llm = get_llm()

    @abstractmethod
    async def run(self, state: "TravelState") -> dict:
        ...

    async def __call__(self, state: "TravelState") -> dict:
        start = datetime.now()
        print(f"[{self.name}] 开始执行")

        try:
            update = await self.run(state)
            elapsed = (datetime.now() - start).total_seconds()
            if "node_status" not in update:
                update["node_status"] = {}
            update["node_status"][self.name] = "completed"
            print(f"[{self.name}] 完成 ({elapsed:.1f}s)")
            return update
        except Exception as e:
            elapsed = (datetime.now() - start).total_seconds()
            print(f"[{self.name}] 失败 ({elapsed:.1f}s): {e}")
            return self._fallback(state, str(e))

    def _fallback(self, state: "TravelState", error: str) -> dict:
        return {
            "errors": [{"node": self.name, "error": error, "timestamp": datetime.now().isoformat()}],
            "node_status": {**state.get("node_status", {}), self.name: "failed"},
        }
