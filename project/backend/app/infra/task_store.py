"""
TaskStore — 用 Redis Hash 存储任务状态

为什么用 Hash 而不是 String(JSON)？
- Hash 支持部分读写：只更新 status 不需要读写整个 result blob
- HSET/HGET 是 O(1) 操作
- 每个字段可以独立设置 TTL（虽然我们这里对整个 key 设 TTL）

Redis 数据结构：
  Key:    wandergraph:task:{task_id}
  Type:   Hash
  Fields: status | query | result | created_at | updated_at
  TTL:    3600s（1小时后自动清理）
"""
import json
from datetime import datetime
import redis.asyncio as aioredis


class TaskStore:
    def __init__(self, redis_client: aioredis.Redis, prefix: str = "wandergraph"):
        self.redis = redis_client
        self.prefix = prefix
        self.ttl = 3600  # 1 小时过期

    def _key(self, task_id: str) -> str:
        return f"{self.prefix}:task:{task_id}"

    async def create(self, task_id: str, query: str) -> None:
        """创建任务 — HSET + EXPIRE"""
        key = self._key(task_id)
        now = datetime.now().isoformat()
        await self.redis.hset(key, mapping={
            "status": "pending",
            "query": query,
            "result": "",
            "created_at": now,
            "updated_at": now,
        })
        await self.redis.expire(key, self.ttl)    # 1 小时后自动删除

    async def get(self, task_id: str) -> dict | None:
        """读取任务 — HGETALL"""
        data = await self.redis.hgetall(self._key(task_id))
        if not data:
            return None
        # 解析 result 字段（JSON 字符串 → dict）
        if data.get("result"):
            try:
                data["result"] = json.loads(data["result"])
            except json.JSONDecodeError:
                data["result"] = {}
        else:
            data["result"] = {}
        return data

    async def update_status(self, task_id: str, status: str) -> None:
        """更新状态 — HSET（只改 status 字段）"""
        await self.redis.hset(self._key(task_id), mapping={
            "status": status,
            "updated_at": datetime.now().isoformat(),
        })

    async def save_result(self, task_id: str, result: dict) -> None:
        """保存结果 — HSET（只改 result 和 status 字段）"""
        await self.redis.hset(self._key(task_id), mapping={
            "status": "completed",
            "result": json.dumps(result, ensure_ascii=False),
            "updated_at": datetime.now().isoformat(),
        })

    async def save_error(self, task_id: str, error: str) -> None:
        """保存错误 — HSET"""
        await self.redis.hset(self._key(task_id), mapping={
            "status": "failed",
            "result": json.dumps({"error": error}, ensure_ascii=False),
            "updated_at": datetime.now().isoformat(),
        })

    async def exists(self, task_id: str) -> bool:
        """检查任务是否存在 — EXISTS"""
        return bool(await self.redis.exists(self._key(task_id)))
