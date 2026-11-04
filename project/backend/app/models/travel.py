import json
import re

from pydantic import BaseModel, Field, field_validator, model_validator


def _coerce_number(v, target=float):
    """LLM 常把数值字段返回成带单位的字符串（'50元' / '72%' / '30°C' / '¥300'），
    提取首个数字（含小数）后转 int/float，避免类型校验失败导致整条记录被丢弃。"""
    if v is None:
        return v
    if isinstance(v, (int, float)):
        return target(v)
    if isinstance(v, str):
        m = re.search(r"-?\d+(?:\.\d+)?", v)
        if m:
            return target(float(m.group()))
    return v


# ============ 基础类型 ============


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)

    def to_amap(self) -> tuple[float, float]:
        return (self.lng, self.lat)


class DateRange(BaseModel):
    start: str
    end: str

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end < self.start:
            raise ValueError("结束日期不能早于开始日期")
        return self

    @property
    def days(self) -> int:
        from datetime import date

        s = date.fromisoformat(self.start)
        e = date.fromisoformat(self.end)
        return (e - s).days + 1


# ============ 景点 ============


class Attraction(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    category: str = ""
    rating: float | None = Field(None, ge=0, le=5)
    estimated_duration_hours: float = Field(default=2, ge=0.5, le=24)
    ticket_price: float | None = Field(None, ge=0)
    location: Location | None = None
    best_time_to_visit: str = ""
    tips: list[str] = []

    @field_validator("rating", "estimated_duration_hours", "ticket_price", mode="before")
    @classmethod
    def _coerce_float(cls, v):
        return _coerce_number(v, float)


# ============ 天气 ============


class DailyWeather(BaseModel):
    date: str
    temp_high: int
    temp_low: int
    condition: str
    humidity: int = Field(default=50, ge=0, le=100)

    @field_validator("temp_high", "temp_low", "humidity", mode="before")
    @classmethod
    def _coerce_int(cls, v):
        return _coerce_number(v, int)

    @model_validator(mode="after")
    def fix_temp(self):
        if self.temp_high < self.temp_low:
            self.temp_high, self.temp_low = self.temp_low, self.temp_high
        return self


class WeatherInfo(BaseModel):
    destination: str = ""
    forecast: list[DailyWeather] = []
    summary: str = ""
    packing_tips: list[str] = []


# ============ 酒店 ============


class HotelRecommendation(BaseModel):
    name: str
    star_rating: int | None = Field(None, ge=1, le=5)
    price_range: str = ""
    location_description: str = ""
    highlights: list[str] = []
    suitable_for: list[str] = []
    booking_tips: str = ""


# ============ 美食 ============


class Dish(BaseModel):
    name: str
    description: str = ""
    recommended_restaurant: str | None = None
    price_range: str = ""
    is_local_specialty: bool = False


class Meal(BaseModel):
    type: str = Field(pattern=r"^(breakfast|lunch|dinner)$")
    time: str = ""
    restaurant: str = ""
    dishes: list[str] = []
    estimated_cost: float = Field(default=0, ge=0)

    @field_validator("estimated_cost", mode="before")
    @classmethod
    def _coerce_float(cls, v):
        return _coerce_number(v, float)


class FoodPlan(BaseModel):
    must_try_dishes: list[Dish] = []
    food_districts: list[str] = []
    dietary_notes: str = ""


# ============ 交通 ============


class TransportOption(BaseModel):
    mode: str
    duration: str = ""
    price_range: str = ""
    tips: str = ""


class TransportPlan(BaseModel):
    arrival_options: list[TransportOption] = []
    local_transport: list[dict] = []
    transport_cards: list[str] = []


# ============ 预算 ============


class BudgetEstimate(BaseModel):
    hotel: float = Field(default=0, ge=0)
    food: float = Field(default=0, ge=0)
    transport: float = Field(default=0, ge=0)
    tickets: float = Field(default=0, ge=0)
    total: float = Field(default=0, ge=0)
    per_person: float = Field(default=0, ge=0)

    @field_validator("hotel", "food", "transport", "tickets", "total", "per_person", mode="before")
    @classmethod
    def _coerce_float(cls, v):
        return _coerce_number(v, float)

    @model_validator(mode="after")
    def calc(self):
        self.total = self.hotel + self.food + self.transport + self.tickets
        return self


# ============ 行程 ============


class Activity(BaseModel):
    time: str = ""
    name: str
    description: str = ""
    duration_hours: float = Field(default=1, ge=0.25, le=24)
    ticket_price: float | None = Field(None, ge=0)
    location: Location | None = None
    transport_to_next: str | None = None

    @field_validator("duration_hours", "ticket_price", mode="before")
    @classmethod
    def _coerce_float(cls, v):
        return _coerce_number(v, float)


class DayPlan(BaseModel):
    day: int = Field(ge=1)
    date: str = ""
    theme: str = ""
    weather_note: str = ""
    activities: list[Activity] = []
    meals: list[Meal] = []
    accommodation: str = ""
    daily_budget_estimate: float = Field(default=0, ge=0)
    tips: list[str] = []

    @field_validator("daily_budget_estimate", mode="before")
    @classmethod
    def _coerce_float(cls, v):
        return _coerce_number(v, float)

    @field_validator("accommodation", mode="before")
    @classmethod
    def _flatten_accommodation(cls, v):
        """LLM 常把 accommodation 返回成对象 {name, price_range}，
        而 schema 声明为 str。这里把 dict 展平成字符串，避免校验失败
        导致整日行程被丢弃（见 ISSUES #14）。"""
        if isinstance(v, dict):
            name = v.get("name") or v.get("hotel") or ""
            price = v.get("price_range") or ""
            if name or price:
                return f"{name} {price}".strip()
            return json.dumps(v, ensure_ascii=False)
        return v


# ============ 校验结果 ============


class ValidationIssue(BaseModel):
    type: str
    message: str
    severity: str = "medium"
    corrected: bool = False


class ValidationResult(BaseModel):
    passed: bool = True
    issues: list[ValidationIssue] = []
    corrected_count: int = 0
