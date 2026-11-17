
import json
from pathlib import Path

from deepeval import assert_test
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from src.agent import build_graph


class PickupDecisionMetric(BaseMetric):
    def __init__(self):
        self.threshold = 1.0
        self.score = 0.0
        self.reason = ""
        self.success = False
        self.error = None
        self.strict_mode = True

    def measure(self, test_case):
        actual = json.loads(test_case.actual_output)
        expected = json.loads(test_case.expected_output)

        correct = (
            actual["decision"] == expected["decision"]
        )

        self.score = 1.0 if correct else 0.0
        self.success = correct
        self.reason = (
            "Pickup decision matches expected result"
            if correct else
            f"Expected {expected['decision']}, "
            f"received {actual['decision']}"
        )

        return self.score

    async def a_measure(self, test_case, _show_indicator=True):
        return self.measure(test_case)

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "Pickup Decision Correctness"


graph = build_graph()

cases = [
    json.loads(line)
    for line in Path("data/golden_cases.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
]

for case in cases:
    actual = graph.invoke(
        {"request": case["input"]}
    )["result"]

    test_case = LLMTestCase(
        input=json.dumps(case["input"]),
        actual_output=json.dumps(actual),
        expected_output=json.dumps(case["expected"]),
    )

    assert_test(
        test_case,
        [PickupDecisionMetric()]
    )

print(f"DeepEval passed: {len(cases)}/{len(cases)} cases")
