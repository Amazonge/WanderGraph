import re
from datetime import date
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import BudgetEstimate
from ..utils.algorithms import allocate_budget, optimize_budget_knapsack


def _extract_number(price_str: str) -> float:
    nums = re.findall(r"\d+", str(price_str))
    if not nums:
        return 0
    return float(nums[-1])


class BudgetEstimateAgent(BaseAgent):
    name = "budget"
    description = "预算估算（启发式分配 + 背包优化）"

    async def run(self, state: TravelState) -> dict:
        dates = state.get("travel_dates", {})
        days = 1
        if dates:
            try:
                s = date.fromisoformat(dates["start"])
                e = date.fromisoformat(dates["end"])
                days = (e - s).days + 1
            except Exception:
                pass

        count = state.get("traveler_count", 1)
        total_budget = state.get("budget")

        # === 1. 基础费用估算 ===
        hotel_cost = 0
        for h in state.get("hotel_recommendations", []):
            hotel_cost += _extract_number(h.get("price_range", "")) * days

        food_cost = 0
        for d in state.get("food_plan", {}).get("must_try_dishes", []):
            food_cost += _extract_number(d.get("price_range", ""))
        food_cost = max(food_cost, days * 100)

        ticket_cost = 0
        for a in state.get("attractions", []):
            price = a.get("ticket_price")
            if price:
                ticket_cost += price

        transport_cost = days * 50

        # === 2. 启发式预算分配（有总预算时）===
        allocation = None
        if total_budget:
            allocation = allocate_budget(total_budget, days, count, "moderate")

        # === 3. 背包优化：在预算约束下选择最优体验组合 ===
        knapsack_result = None
        if total_budget:
            optional_items = []
            for a in state.get("attractions", []):
                price = a.get("ticket_price", 0) or 0
                if price > 0:
                    optional_items.append({
                        "name": a.get("name", ""),
                        "cost": price,
                        "value": min(10, max(1, (a.get("rating", 5) or 5) * 2)),
                    })
            for d in state.get("food_plan", {}).get("must_try_dishes", []):
                cost = _extract_number(d.get("price_range", ""))
                if cost > 0:
                    optional_items.append({
                        "name": d.get("name", ""),
                        "cost": cost,
                        "value": 8 if d.get("is_local_specialty") else 5,
                    })
            if optional_items:
                remaining = total_budget - hotel_cost - transport_cost
                if remaining > 0:
                    knapsack_result = optimize_budget_knapsack(optional_items, remaining)

        # === 4. 组装结果 ===
        final_hotel = allocation["hotel"] if allocation else hotel_cost
        final_food = allocation["food"] if allocation else food_cost
        final_transport = allocation["transport"] if allocation else transport_cost
        final_tickets = allocation["tickets"] if allocation else ticket_cost

        estimate = BudgetEstimate(
            hotel=final_hotel,
            food=final_food,
            transport=final_transport,
            tickets=final_tickets,
        )
        result = estimate.model_dump()
        result["per_person"] = result["total"] / max(count, 1)

        if allocation:
            result["allocation_strategy"] = allocation
        if knapsack_result:
            result["optimized_experiences"] = [
                {"name": i["name"], "cost": i["cost"], "value": i["value"]}
                for i in knapsack_result
            ]
            result["optimized_total_value"] = sum(i["value"] for i in knapsack_result)

        return {"budget_estimate": result}
