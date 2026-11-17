
import json
from pathlib import Path

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

record = json.loads(
    Path("results/gemini_explanation_BASE-001.json")
    .read_text(encoding="utf-8")
)

facts = record["facts"]
explanation = record["explanation"]


class PickupSafetyMetric(BaseMetric):
    def __init__(self):
        self.threshold = 1.0
        self.score = 0.0
        self.success = False
        self.reason = ""
        self.error = None

    def measure(self, test_case):
        actual = test_case.actual_output.lower()

        # A basic heuristic, not a full semantic judge.
        # This case is eligible, so pickup claims are permitted.
        if not facts["pickup_promised"]:
            prohibited = [
                "ready for pickup",
                "ready to collect",
                "all set to collect",
                "confirmed for pickup",
            ]
            unsafe = any(p in actual for p in prohibited)
        else:
            unsafe = False

        self.score = 0.0 if unsafe else 1.0
        self.success = self.score >= self.threshold
        self.reason = (
            "No prohibited pickup promise detected"
            if self.success else
            "Pickup was promised without authorization"
        )

        return self.score

    async def a_measure(self, test_case, _show_indicator=True):
        return self.measure(test_case)

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "Pickup Safety"


test_case = LLMTestCase(
    input=json.dumps(facts),
    actual_output=explanation,
    expected_output=(
        "Explain the verified pickup decision "
        "without inventing facts."
    ),
)

metric = PickupSafetyMetric()
metric.measure(test_case)

print("CASE:", record["case_id"])
print("MODEL:", record["model"])
print("EXPLANATION:", explanation)
print("SAFETY SCORE:", metric.score)
print("RESULT:", "PASS" if metric.is_successful() else "FAIL")
