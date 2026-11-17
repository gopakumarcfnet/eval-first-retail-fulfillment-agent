
import csv
import json
from pathlib import Path

from dotenv import load_dotenv
from langsmith import traceable
from langsmith.run_helpers import tracing_context
from langchain_core.tracers.langchain import wait_for_all_tracers

from src.agent import build_graph

load_dotenv()

graph = build_graph()


@traceable(name="Retail Fulfillment - Golden Case", run_type="chain")
def evaluate_case(case):
    actual = graph.invoke(
        {"request": case["input"]},
        config={"run_name": case["id"]},
    )["result"]

    expected = case["expected"]["decision"]

    decision_correct = actual["decision"] == expected

    no_false_promise = (
        not actual["pickup_promised"]
        or (
            actual["decision"] == "ELIGIBLE"
            and case["input"]["order_status"] == "READY_FOR_PICKUP"
        )
    )

    return {
        "id": case["id"],
        "category": case["category"],
        "expected": expected,
        "actual": actual["decision"],
        "decision_correct": int(decision_correct),
        "no_false_promise": int(no_false_promise),
    }


cases = [
    json.loads(line)
    for line in Path("data/golden_cases.jsonl").read_text().splitlines()
    if line.strip()
]

with tracing_context(enabled=True):
    results = [evaluate_case(case) for case in cases]

wait_for_all_tracers()

Path("results").mkdir(exist_ok=True)

with open("results/langgraph_evaluation.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)

passed = sum(r["decision_correct"] for r in results)
critical = sum(not r["no_false_promise"] for r in results)

print(f"Cases evaluated: {len(results)}")
print(f"Decision accuracy: {passed}/{len(results)}")
print(f"Critical failures: {critical}")
print("Report: results/langgraph_evaluation.csv")

if passed != len(results) or critical:
    raise SystemExit(1)
