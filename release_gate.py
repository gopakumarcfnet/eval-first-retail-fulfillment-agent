import os
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

checks = [
    {
        "name": "Golden decision and pickup safety",
        "command": [
            sys.executable,
            "-m",
            "unittest",
            "test_release_gate",
            "-v",
        ],
    },
    {
        "name": "DeepEval decision correctness",
        "command": [
            sys.executable,
            "deepeval_test.py",
        ],
    },
    {
        "name": "Gemini remediation verification",
        "command": [
            sys.executable,
            "verify_remediation.py",
        ],
    },
]

outcomes = []

for check in checks:
    print(f"\nRUNNING: {check['name']}", flush=True)

    process = subprocess.run(
    check["command"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    env={
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "TERM": "dumb",
    },
)

    passed = process.returncode == 0

    print(process.stdout)
    if process.stderr:
        print(process.stderr)

    outcomes.append({
        "check": check["name"],
        "status": "PASS" if passed else "FAIL",
        "exit_code": process.returncode,
    })

report = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "checks": outcomes,
    "release_decision": (
        "PASS"
        if all(c["status"] == "PASS" for c in outcomes)
        else "BLOCK"
    ),
}

report_path = RESULTS / "release_gate_report.json"
report_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)

print("\n" + "=" * 45)
print("AUTOMATED RELEASE GATE")
print("=" * 45)

for outcome in outcomes:
    print(f"{outcome['check']}: {outcome['status']}")

print("\nFINAL RELEASE DECISION:", report["release_decision"])
print("Report saved:", report_path)

if report["release_decision"] != "PASS":
    raise SystemExit(1)
