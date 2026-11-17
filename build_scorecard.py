
import csv
import json
from pathlib import Path

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

# Verified results from our experiments.
experiments = [
    {
        "experiment": "Golden decision accuracy",
        "passed": 30,
        "total": 30,
        "release": "PASS",
    },
    {
        "experiment": "Defective postal-code policy",
        "passed": 18,
        "total": 30,
        "release": "BLOCK",
    },
    {
        "experiment": "DeepEval decision correctness",
        "passed": 30,
        "total": 30,
        "release": "PASS",
    },
    {
        "experiment": "Original Gemini explanations",
        "passed": 2,
        "total": 3,
        "release": "BLOCK",
    },
    {
        "experiment": "Injected unsafe explanation",
        "passed": 2,
        "total": 3,
        "release": "BLOCK",
    },
    {
        "experiment": "Remediated Gemini explanations",
        "passed": 3,
        "total": 3,
        "release": "PASS",
    },
]

for row in experiments:
    row["pass_rate"] = round(
        100 * row["passed"] / row["total"], 1
    )

csv_path = results_dir / "evaluation_scorecard.csv"
json_path = results_dir / "evaluation_scorecard.json"

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(experiments[0].keys()),
    )
    writer.writeheader()
    writer.writerows(experiments)

json_path.write_text(
    json.dumps(experiments, indent=2),
    encoding="utf-8",
)

print("\nEVALUATION SCORECARD")
print("-" * 65)

for row in experiments:
    print(
        f"{row['experiment']:<37}"
        f"{row['passed']}/{row['total']}  "
        f"{row['pass_rate']:>5.1f}%  "
        f"{row['release']}"
    )

print("\nSaved:", csv_path)
print("Saved:", json_path)
