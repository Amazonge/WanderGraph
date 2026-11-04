from fastapi import APIRouter, Request
from ...config import settings

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    result = {
        "status": "ok",
        "version": "0.2.0",
        "llm_provider": settings.LLM_PROVIDER,
        "redis": "disabled (memory mode)",
    }

    # Redis 健康检查（内存模式下 task_store 为 None，跳过）
    task_store = getattr(request.app.state, "task_store", None)
    if task_store is not None:
        try:
            await task_store.redis.ping()
            result["redis"] = "ok"
        except Exception as e:
            result["redis"] = f"error: {e}"
            result["status"] = "degraded"
    elif not settings.USE_REDIS:
        result["status"] = "ok (memory mode)"

    return result
