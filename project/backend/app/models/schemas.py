from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    query: str = Field(min_length=5, max_length=500)


class PlanResponse(BaseModel):
    task_id: str
    status: str


class PlanResultResponse(BaseModel):
    task_id: str
    status: str
    destination: str | None = None
    travel_dates: dict | None = None
    itinerary: list[dict] = []
    summary: str | None = None
    full_result: dict | None = None
