
import json
from pathlib import Path

from evaluate_gemini_release import evaluate

original = json.loads(
    Path("results/three_scenarios.json")
    .read_text(encoding="utf-8")
)

remediated = json.loads(
    Path("results/gemini_remediated_BASE-002.json")
    .read_text(encoding="utf-8")
)

# Replace only the failed explanation.
revised = [row.copy() for row in original]

for row in revised:
    if row["case_id"] == "BASE-002":
        row["explanation"] = remediated["explanation"]

outcomes = evaluate(revised)

print("\nPOST-REMEDIATION EVALUATION")

for row in outcomes:
    status = "PASS" if row["passed"] else "FAIL"
    print(
        f"{row['case_id']} | {status} | {row['reason']}"
    )

passed = sum(row["passed"] for row in outcomes)
release_passed = passed == len(outcomes)

print(f"\nPassed: {passed}/{len(outcomes)}")
print("RELEASE:", "PASS" if release_passed else "BLOCK")

Path("results/gemini_remediation_evaluation.json").write_text(
    json.dumps(outcomes, indent=2),
    encoding="utf-8",
)

if not release_passed:
    raise SystemExit(1)
