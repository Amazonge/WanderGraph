import pytest
from app.models.travel import (
    Location,
    DateRange,
    Attraction,
    DailyWeather,
    WeatherInfo,
    HotelRecommendation,
    Dish,
    Meal,
    FoodPlan,
    TransportOption,
    TransportPlan,
    BudgetEstimate,
    Activity,
    DayPlan,
    ValidationResult,
)


def test_location():
    loc = Location(lat=30.57, lng=104.07)
    assert loc.to_amap() == (104.07, 30.57)


def test_date_range_valid():
    dr = DateRange(start="2026-06-01", end="2026-06-03")
    assert dr.days == 3


def test_date_range_invalid():
    with pytest.raises(ValueError):
        DateRange(start="2026-06-03", end="2026-06-01")


def test_attraction_defaults():
    a = Attraction(name="武侯祠")
    assert a.estimated_duration_hours == 2
    assert a.tips == []
    assert a.ticket_price is None


def test_budget_auto_calc():
    b = BudgetEstimate(hotel=600, food=450, transport=200, tickets=150)
    assert b.total == 1400


def test_daily_weather_temp_fix():
    w = DailyWeather(date="2026-06-01", temp_high=15, temp_low=25, condition="多云")
    assert w.temp_high == 25
    assert w.temp_low == 15


def test_meal_type_valid():
    m = Meal(type="lunch", restaurant="test")
    assert m.type == "lunch"


def test_meal_type_invalid():
    with pytest.raises(Exception):
        Meal(type="brunch")


def test_food_plan_defaults():
    fp = FoodPlan()
    assert fp.must_try_dishes == []
    assert fp.food_districts == []


def test_day_plan():
    dp = DayPlan(
        day=1,
        date="2026-06-01",
        theme="市区探索",
        activities=[
            Activity(name="武侯祠", time="09:00-11:00", description="三国文化"),
            Activity(name="锦里", time="11:00-12:00", description="古街漫步"),
        ],
        meals=[Meal(type="lunch", restaurant="陈麻婆豆腐", dishes=["麻婆豆腐"], estimated_cost=50)],
    )
    assert len(dp.activities) == 2
    assert dp.meals[0].type == "lunch"


def test_validation_result():
    r = ValidationResult(passed=False, issues=[])
    assert r.passed is False
    assert r.corrected_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
