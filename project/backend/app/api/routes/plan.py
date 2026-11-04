"""
plan.py — 旅行规划 API（双模式：Redis / 内存）

有 Redis → Redis Hash 存状态 + Pub/Sub 推事件，任务直接 asyncio.create_task 执行
无 Redis → 内存 dict + asyncio.Queue
"""
import asyncio
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ...models.schemas import PlanRequest, PlanResponse, PlanResultResponse
from ...graph.builder import build_travel_graph

router = APIRouter()

# 内存模式降级存储
_tasks: dict[str, dict] = {}
_queues: dict[str, asyncio.Queue] = {}


def _use_redis(request: Request) -> bool:
    return request.app.state.task_store is not None


@router.post("/plan", response_model=PlanResponse)
async def create_plan(req: PlanRequest, request: Request):
    task_id = str(uuid.uuid4())

    if _use_redis(request):
        task_store = request.app.state.task_store
        event_publisher = request.app.state.event_publisher
        await task_store.create(task_id, req.query)
        asyncio.create_task(_run_plan_redis(task_id, req.query, task_store, event_publisher))
    else:
        _tasks[task_id] = {"status": "pending", "query": req.query, "result": None}
        _queues[task_id] = asyncio.Queue()
        asyncio.create_task(_run_plan_memory(task_id, req.query, _queues[task_id]))

    return PlanResponse(task_id=task_id, status="pending")


@router.get("/plan/{task_id}/stream")
async def stream_plan(task_id: str, request: Request):
    if _use_redis(request):
        task_store = request.app.state.task_store
        task = await task_store.get(task_id)
        if not task:
            raise HTTPException(404, "任务不存在")
        if task["status"] in ("completed", "failed"):
            async def _done():
                yield f'data: {{"type":"{task["status"]}"}}\n\n'
            return StreamingResponse(_done(), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache"})

        from ...infra.redis_client import get_redis
        from ...infra.event_bus import EventSubscriber
        redis = await get_redis()
        subscriber = EventSubscriber(redis, request.app.state.event_publisher.prefix)

        async def _sse():
            try:
                async for event in subscriber.subscribe(task_id):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event.get("type") in ("complete", "error"):
                        break
            finally:
                await subscriber.close()

        return StreamingResponse(_sse(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})
    else:
        if task_id not in _queues:
            raise HTTPException(404, "任务不存在")

        queue = _queues[task_id]

        async def _sse():
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
                parsed = json.loads(data)
                if parsed.get("type") in ("complete", "error"):
                    break

        return StreamingResponse(_sse(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})


@router.get("/plan/{task_id}", response_model=PlanResultResponse)
async def get_plan(task_id: str, request: Request):
    if _use_redis(request):
        task = await request.app.state.task_store.get(task_id)
    else:
        task = _tasks.get(task_id)

    if not task:
        raise HTTPException(404, "任务不存在")

    result = task.get("result", {}) or {}
    return PlanResultResponse(
        task_id=task_id,
        status=task["status"],
        destination=result.get("destination"),
        travel_dates=result.get("travel_dates"),
        itinerary=result.get("itinerary", []),
        summary=result.get("summary"),
        full_result=result if task["status"] == "completed" else None,
    )


async def _run_plan_redis(task_id: str, query: str, task_store, event_publisher):
    """Redis 模式执行：结果存 Redis Hash，进度走 Pub/Sub

    替代旧的 Stream Consumer：不再走消息队列 + 分布式锁，
    直接在请求进程内 asyncio.create_task 执行 LangGraph DAG，
    把 node 事件和最终结果通过 Pub/Sub 推给 SSE 端点。
    """
    await task_store.update_status(task_id, "running")
    try:
        graph = build_travel_graph(publisher=event_publisher, task_id=task_id)
        result = await graph.ainvoke({
            "user_query": query,
            "errors": [],
            "node_status": {},
            "progress": 0.0,
        })
        await task_store.save_result(task_id, result)
        await event_publisher.publish_complete(task_id, {
            "destination": result.get("destination"),
            "travel_dates": result.get("travel_dates"),
            "summary": result.get("summary"),
        })
    except Exception as e:
        await task_store.save_error(task_id, str(e))
        await event_publisher.publish_error(task_id, str(e))


async def _run_plan_memory(task_id: str, query: str, queue: asyncio.Queue):
    """内存模式执行（无 Redis）"""
    _tasks[task_id]["status"] = "running"
    try:
        graph = build_travel_graph(queue=queue)
        result = await graph.ainvoke({
            "user_query": query,
            "errors": [],
            "node_status": {},
            "progress": 0.0,
        })
        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["result"] = result
        await queue.put(json.dumps({
            "type": "complete",
            "result": {
                "destination": result.get("destination"),
                "travel_dates": result.get("travel_dates"),
                "summary": result.get("summary"),
            }
        }, ensure_ascii=False))
    except Exception as e:
        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["result"] = {"error": str(e)}
        await queue.put(json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False))
