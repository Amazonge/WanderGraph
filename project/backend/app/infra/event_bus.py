"""
EventBus — 用 Redis Pub/Sub 实现 SSE 事件推送

为什么用 Pub/Sub 而不是 Redis Streams？
- Pub/Sub 是推送模型：subscriber 立即收到消息，延迟最低
- Streams 是拉取模型：需要 XREAD 轮询，有额外延迟
- SSE 需要实时性，所以选 Pub/Sub
- 代价：Pub/Sub 是 fire-and-forget，消息不持久化
  → 但最终结果存在 Redis Hash 中，SSE 只传进度事件，丢了也没关系

Redis 数据结构：
  Channel: wandergraph:events:{task_id}
  消息格式: JSON 字符串 {"type": "node_start", "node": "attraction", ...}
"""
import json
from datetime import datetime
from typing import AsyncIterator
import redis.asyncio as aioredis


class EventPublisher:
    """事件发布者 — Agent 执行时调用"""

    def __init__(self, redis_client: aioredis.Redis, prefix: str = "wandergraph"):
        self.redis = redis_client
        self.prefix = prefix

    def _channel(self, task_id: str) -> str:
        return f"{self.prefix}:events:{task_id}"

    async def publish(self, task_id: str, event: dict) -> int:
        """发布事件 — PUBLISH channel message
        返回接收该消息的订阅者数量
        """
        return await self.redis.publish(
            self._channel(task_id),
            json.dumps(event, ensure_ascii=False),
        )

    async def publish_node_start(self, task_id: str, node: str) -> None:
        await self.publish(task_id, {
            "type": "node_start",
            "node": node,
            "timestamp": datetime.now().isoformat(),
        })

    async def publish_node_complete(self, task_id: str, node: str, status: str = "completed") -> None:
        await self.publish(task_id, {
            "type": "node_complete",
            "node": node,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        })

    async def publish_complete(self, task_id: str, result: dict) -> None:
        await self.publish(task_id, {
            "type": "complete",
            "result": result,
        })

    async def publish_error(self, task_id: str, message: str) -> None:
        await self.publish(task_id, {
            "type": "error",
            "message": message,
        })


class EventSubscriber:
    """事件订阅者 — SSE 端点调用"""

    def __init__(self, redis_client: aioredis.Redis, prefix: str = "wandergraph"):
        self.redis = redis_client
        self.prefix = prefix
        self._pubsub: aioredis.client.PubSub | None = None

    async def subscribe(self, task_id: str) -> AsyncIterator[dict]:
        """订阅任务事件 — SUBSCRIBE channel
        生成器：yield 每个事件 dict，收到 complete/error 后自动停止
        """
        channel = f"{self.prefix}:events:{task_id}"
        self._pubsub = self.redis.pubsub()
        await self._pubsub.subscribe(channel)

        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                yield data
                # 收到终止事件后停止
                if data.get("type") in ("complete", "error"):
                    break
        finally:
            await self._pubsub.unsubscribe(channel)
            await self._pubsub.close()

    async def close(self):
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
