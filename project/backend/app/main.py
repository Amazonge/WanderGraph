from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import health, plan
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期 — Redis 可选，无 Redis 自动用内存模式

    Redis 模式只使用：
    - TaskStore（Hash）：任务状态持久化
    - EventPublisher（Pub/Sub）：SSE 事件推送
    任务执行由 plan.py 直接 asyncio.create_task 拉起，结果写回 Hash。
    """

    # 尝试连接 Redis
    if settings.USE_REDIS:
        try:
            from .infra.redis_client import get_redis
            from .infra.task_store import TaskStore
            from .infra.event_bus import EventPublisher

            redis = await get_redis()
            prefix = settings.REDIS_KEY_PREFIX

            app.state.task_store = TaskStore(redis, prefix)
            app.state.event_publisher = EventPublisher(redis, prefix)

            print("[Redis] 已连接，使用 Redis 模式")
        except Exception as e:
            print(f"[Redis] 连接失败: {e}，降级到内存模式")
            app.state.task_store = None
            app.state.event_publisher = None
    else:
        app.state.task_store = None
        app.state.event_publisher = None
        print("[Redis] 未启用，使用内存模式")

    yield

    # 关闭 MCP 客户端连接
    try:
        from .mcp.manager import close_all_clients
        await close_all_clients()
    except Exception:
        pass

    if settings.USE_REDIS:
        try:
            from .infra.redis_client import close_redis
            await close_redis()
        except Exception:
            pass


app = FastAPI(title="WanderGraph", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(plan.router, prefix="/api")
