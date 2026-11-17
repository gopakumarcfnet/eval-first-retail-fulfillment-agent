
import json
import unittest
from pathlib import Path

from src.agent import build_graph

graph = build_graph()

cases = [
    json.loads(line)
    for line in Path("data/golden_cases.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]


class TestReleaseGate(unittest.TestCase):

    def test_golden_decisions(self):
        for case in cases:
            with self.subTest(case_id=case["id"]):
                actual = graph.invoke(
                    {"request": case["input"]}
                )["result"]

                self.assertEqual(
                    actual["decision"],
                    case["expected"]["decision"]
                )

    def test_no_unsafe_pickup_promises(self):
        for case in cases:
            with self.subTest(case_id=case["id"]):
                actual = graph.invoke(
                    {"request": case["input"]}
                )["result"]

                if actual["pickup_promised"]:
                    self.assertEqual(
                        actual["decision"], "ELIGIBLE"
                    )
                    self.assertEqual(
                        case["input"]["order_status"],
                        "READY_FOR_PICKUP"
                    )
                    self.assertIsNotNone(
                        actual["coordinates"]
                    )


if __name__ == "__main__":
    unittest.main()
