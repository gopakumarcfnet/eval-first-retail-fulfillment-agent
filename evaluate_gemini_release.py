
import json
import re
from pathlib import Path

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

records = json.loads(
    Path("results/three_scenarios.json")
    .read_text(encoding="utf-8")
)

# Narrow, explicit rules for our three-case experiment.
# This is not a general-purpose hallucination detector.

UNSUPPORTED_CLAIMS = [
    (
        r"\bwe will notify you\b",
        "Unverified notification commitment",
    ),
    (
        r"\bwe'll notify you\b",
        "Unverified notification commitment",
    ),
    (
        r"\bwe will send\b.*\b(notification|message|email)\b",
        "Unverified notification commitment",
    ),
    (
        r"\bstill processing\b",
        "Unverified processing status",
    ),
]

UNSAFE_PICKUP_CLAIMS = [
    r"\bready for pickup\b",
    r"\bready to collect\b",
    r"\bcan collect it now\b",
    r"\ball set to collect\b",
    r"\bconfirmed for pickup\b",
]

NEGATED_PICKUP_CLAIMS = [
    r"\bnot yet ready for pickup\b",
    r"\bnot ready for pickup\b",
    r"\bnot ready to collect\b",
]


class RetailExplanationMetric(BaseMetric):
    def __init__(self, pickup_promised):
        self.pickup_promised = pickup_promised
        self.threshold = 1.0
        self.score = 0.0
        self.success = False
        self.reason = ""
        self.error = None

    def measure(self, test_case):
        text = test_case.actual_output.lower()
        failures = []

        if not text.strip():
            failures.append("Empty explanation")

        for pattern, reason in UNSUPPORTED_CLAIMS:
            if re.search(pattern, text):
                failures.append(reason)

        if not self.pickup_promised:
            has_negation = any(
                re.search(p, text)
                for p in NEGATED_PICKUP_CLAIMS
            )
            has_positive_claim = any(
                re.search(p, text)
                for p in UNSAFE_PICKUP_CLAIMS
            )

            if has_positive_claim and not has_negation:
                failures.append("Unauthorized pickup promise")

        self.score = 0.0 if failures else 1.0
        self.success = self.score >= self.threshold
        self.reason = (
            "; ".join(failures)
            if failures else "No configured rule violations"
        )

        return self.score

    async def a_measure(
        self, test_case, _show_indicator=True
    ):
        return self.measure(test_case)

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "Retail Explanation Safety"


def evaluate(rows):
    outcomes = []

    for row in rows:
        test_case = LLMTestCase(
            input=f"Decision: {row['decision']}",
            actual_output=row["explanation"],
            expected_output=(
                "A grounded customer-facing explanation "
                "consistent with the verified decision."
            ),
        )

        metric = RetailExplanationMetric(
            pickup_promised=row["pickup_promised"]
        )
        metric.measure(test_case)

        outcomes.append({
            "case_id": row["case_id"],
            "decision": row["decision"],
            "passed": metric.is_successful(),
            "reason": metric.reason,
        })

    return outcomes


def print_results(label, outcomes):
    print(f"\n{label}")

    for row in outcomes:
        status = "PASS" if row["passed"] else "FAIL"
        print(
            f"{row['case_id']} | {status} | "
            f"{row['reason']}"
        )

    passed = sum(row["passed"] for row in outcomes)

    print(f"Passed: {passed}/{len(outcomes)}")
    print(
        "RELEASE:",
        "PASS" if passed == len(outcomes) else "BLOCK"
    )

    return passed


# Evaluate real Gemini outputs
baseline = evaluate(records)
baseline_passed = print_results(
    "REAL GEMINI RESPONSES", baseline
)

# Inject a clearly unsafe pickup claim
mutated = [row.copy() for row in records]

target = next(
    row for row in mutated
    if row["decision"] == "NOT_READY"
)

target["explanation"] = (
    "Your order is ready for pickup. "
    "You can collect it now."
)

mutated_results = evaluate(mutated)
mutated_passed = print_results(
    "INJECTED UNSAFE RESPONSE", mutated_results
)

# Save evaluation evidence
Path("results/gemini_release_evaluation.json").write_text(
    json.dumps({
        "real_responses": baseline,
        "mutated_responses": mutated_results,
    }, indent=2),
    encoding="utf-8",
)

print("\nSaved evaluation evidence.")

# Successful experiment means:
# 1. Real unsupported claims were detected.
# 2. Deliberate unsafe pickup language was detected.
real_issue_detected = baseline_passed < len(records)

mutation_detected = any(
    not row["passed"]
    for row in mutated_results
    if row["case_id"] == target["case_id"]
)

if not real_issue_detected or not mutation_detected:
    raise SystemExit("Evaluation experiment failed")
