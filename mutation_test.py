
import json
from pathlib import Path
from collections import Counter

import src.agent as agent

DATASET = Path("data/golden_cases.jsonl")

cases = [
    json.loads(line)
    for line in DATASET.read_text(encoding="utf-8").splitlines()
    if line.strip()
]


def evaluate(graph):
    results = []

    for case in cases:
        actual = graph.invoke(
            {"request": case["input"]}
        )["result"]

        expected = case["expected"]["decision"]
        correct = actual["decision"] == expected

        results.append({
            "id": case["id"],
            "country": case["input"]["country"],
            "expected": expected,
            "actual": actual["decision"],
            "correct": correct,
            "pickup_promised": actual["pickup_promised"],
        })

    return results


def report(name, results):
    passed = sum(r["correct"] for r in results)
    failures = [r for r in results if not r["correct"]]

    print(f"\n{name}")
    print(f"Accuracy: {passed}/{len(results)}")
    print(f"Failed cases: {len(failures)}")
    print("Failures by country:",
          dict(Counter(r["country"] for r in failures)))

    for row in failures:
        print(
            f"  {row['id']}: "
            f"expected={row['expected']} "
            f"actual={row['actual']}"
        )

    return passed, failures


# 1. Evaluate the original implementation
baseline_graph = agent.build_graph()
baseline = evaluate(baseline_graph)
baseline_passed, _ = report("BASELINE", baseline)

# 2. Simulate an actual business-rule defect
original_policy = agent.POSTAL_POLICY.copy()

try:
    agent.POSTAL_POLICY["AE"] = "required"
    agent.POSTAL_POLICY["TR"] = "required"

    defective_graph = agent.build_graph()
    defective = evaluate(defective_graph)

finally:
    # Restore the original rules, even on an error
    agent.POSTAL_POLICY.clear()
    agent.POSTAL_POLICY.update(original_policy)

defective_passed, failures = report(
    "DEFECTIVE IMPLEMENTATION", defective
)

# 3. Release gate
baseline_ok = baseline_passed == len(cases)
mutation_detected = defective_passed < baseline_passed

print("\nRELEASE GATE")
print("Baseline:", "PASS" if baseline_ok else "FAIL")
print(
    "Defective version:",
    "BLOCKED" if defective_passed < len(cases) else "NOT BLOCKED"
)
print(
    "Mutation detected:",
    "YES" if mutation_detected else "NO"
)

if not baseline_ok or not mutation_detected:
    raise SystemExit(1)
