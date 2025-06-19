from typing import Any, Dict, List, Union
import os
from datetime import datetime, timedelta

class ConditionEvaluator:
    def __init__(self, state: Dict[str, Any], steps_status: Dict[str, str], outputs: Dict[str, Dict[str, Any]]):
        self.state = state
        self.steps_status = steps_status
        self.outputs = outputs

    def evaluate(self, condition: Union[Dict, List, bool]) -> bool:
        if isinstance(condition, bool):
            return condition
        if isinstance(condition, list):
            return all(self.evaluate(cond) for cond in condition)
        if not isinstance(condition, dict):
            return False

        if "all" in condition:
            return all(self.evaluate(c) for c in condition["all"])
        if "any" in condition:
            return any(self.evaluate(c) for c in condition["any"])
        if "not" in condition:
            return not self.evaluate(condition["not"])

        if "parameter" in condition:
            param = condition["parameter"]
            operator = condition.get("operator")
            value = condition.get("value")
            actual = self.state.get(param)
            return self._compare(actual, operator, value)

        if "step_completed" in condition:
            step = condition["step_completed"]
            return self.steps_status.get(step) == "completed"

        if "file_exists" in condition:
            return os.path.exists(condition["file_exists"])

        if "output_available" in condition:
            step_output = condition["output_available"]
            step_id, _, output_key = step_output.partition(".")
            return self.outputs.get(step_id, {}).get(output_key) is not None

        if "external_check" in condition:
            # Placeholder: Should integrate real service logic
            return False

        if "time_elapsed" in condition:
            # Placeholder logic
            ref_time = self.state.get("step_start_times", {}).get(condition["time_elapsed"]["after_step"])
            if ref_time:
                delta = timedelta(minutes=condition["time_elapsed"]["minutes"])
                return datetime.utcnow() >= datetime.fromisoformat(ref_time) + delta
            return False

        return False

    def _compare(self, actual, operator: str, expected) -> bool:
        if operator == "==":
            return actual == expected
        if operator == "!=":
            return actual != expected
        if operator == ">":
            return actual > expected
        if operator == "<":
            return actual < expected
        if operator == ">=":
            return actual >= expected
        if operator == "<=":
            return actual <= expected
        if operator == "in":
            return actual in expected
        if operator == "not in":
            return actual not in expected
        return False