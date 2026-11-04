"""
Redis 异步连接池 — 全局单例

设计要点：
- redis.asyncio.Redis 内置连接池，不需要额外的 ConnectionPool
- decode_responses=True：所有返回都是 str 而不是 bytes
- hiredis：C 语言实现的 Redis 协议解析器，比纯 Python 快 10x
- 懒初始化：第一次调用 get_redis() 时才创建连接
"""
import redis.asyncio as aioredis
from ..config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 客户端单例（懒初始化）"""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,        # 返回 str 而不是 bytes
        )
        # 验证连接
        await _redis.ping()
        print(f"[Redis] 已连接: {settings.REDIS_URL}")
    return _redis


async def close_redis():
    """关闭连接池（FastAPI shutdown 时调用）"""
    global _redis
    if _redis:
        await _redis.aclose()    # 关闭连接池中的所有连接
        _redis = None
        print("[Redis] 已断开")
