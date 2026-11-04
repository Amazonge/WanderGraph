import json
from datetime import date
from .base import BaseAgent
from ..graph.state import TravelState
from ..models.travel import ValidationResult, ValidationIssue


SYSTEM = "你是一个行程校验专家。检查行程中的逻辑错误。回复纯 JSON 数组。"


class ValidationAgent(BaseAgent):
    name = "validator"
    description = "行程校验与修正"

    async def run(self, state: TravelState) -> dict:
        itinerary = state.get("itinerary", [])
        issues = []

        issues.extend(self._check_dates(state, itinerary))
        issues.extend(self._check_completeness(state, itinerary))
        issues.extend(self._check_budget(state))

        semantic_issues = await self._llm_check(state, itinerary)
        issues.extend(semantic_issues)

        corrected = self._auto_correct_day_indices(itinerary)

        result = ValidationResult(
            passed=len([i for i in issues if i.severity == "high"]) == 0,
            issues=issues,
            corrected_count=len([i for i in issues if i.corrected]),
        )

        return {
            "itinerary": corrected,
            "validation_result": result.model_dump(),
        }

    def _check_dates(self, state, itinerary) -> list[ValidationIssue]:
        issues = []
        dates = state.get("travel_dates", {})
        if not dates:
            return issues
        try:
            s = date.fromisoformat(dates["start"])
            e = date.fromisoformat(dates["end"])
            expected_days = (e - s).days + 1
            if len(itinerary) != expected_days:
                issues.append(
                    ValidationIssue(
                        type="date_mismatch",
                        message=f"行程 {len(itinerary)} 天，但日期跨度 {expected_days} 天",
                        severity="high",
                    )
                )
        except Exception:
            pass
        return issues

    def _check_completeness(self, state, itinerary) -> list[ValidationIssue]:
        issues = []
        if not itinerary:
            issues.append(
                ValidationIssue(type="empty_itinerary", message="行程为空", severity="high")
            )
        for day in itinerary:
            if not day.get("activities"):
                issues.append(
                    ValidationIssue(
                        type="empty_day",
                        message=f"Day {day.get('day', '?')} 没有活动安排",
                        severity="medium",
                    )
                )
        return issues

    def _check_budget(self, state) -> list[ValidationIssue]:
        issues = []
        budget = state.get("budget")
        estimate = state.get("budget_estimate", {})
        if budget and estimate.get("total", 0) > budget * 1.2:
            issues.append(
                ValidationIssue(
                    type="budget_exceeded",
                    message=f"预估费用超预算",
                    severity="medium",
                )
            )
        return issues

    async def _llm_check(self, state, itinerary) -> list[ValidationIssue]:
        if not itinerary:
            return []
        user = f"""请检查以下行程是否有逻辑问题：
{json.dumps(itinerary[:3], ensure_ascii=False, indent=2)}

检查：时间是否连续、餐饮是否合理、地理位置是否合理。
如有问题，回复 JSON 数组（每个含 type, message, severity）。无问题回复空数组。"""
        try:
            text = await self.llm.invoke(system=SYSTEM, user=user)
            raw = text.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:-1])
            items = json.loads(raw)
            return [ValidationIssue(**i) for i in items]
        except Exception:
            return []

    def _auto_correct_day_indices(self, itinerary) -> list[dict]:
        corrected = []
        for i, day in enumerate(itinerary):
            d = dict(day)
            d["day"] = i + 1
            corrected.append(d)
        return corrected
