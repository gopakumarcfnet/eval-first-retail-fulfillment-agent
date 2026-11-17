
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.agent import build_graph

load_dotenv()

model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

cases = [
    json.loads(line)
    for line in Path("data/golden_cases.jsonl")
    .read_text(encoding="utf-8").splitlines()
    if line.strip()
]

case = next(c for c in cases if c["id"] == "BASE-002")
result = build_graph().invoke(
    {"request": case["input"]}
)["result"]

if result["decision"] != case["expected"]["decision"]:
    raise RuntimeError("Golden decision mismatch")

facts = {
    "decision": result["decision"],
    "pickup_promised": result["pickup_promised"],
    "reason": result.get("reason"),
    "order_status": case["input"].get("order_status"),
}

response = client.models.generate_content(
    model=model,
    contents=json.dumps(facts),
    config=types.GenerateContentConfig(
        system_instruction=(
            "Write one short customer-facing explanation "
            "of the supplied verified pickup decision. "
            "Only use facts explicitly provided. "
            "The decision is authoritative. "
            "Never claim the order is processing, packed, "
            "shipped, or undergoing preparation unless "
            "that exact status is explicitly provided. "
            "Never promise emails, SMS, notifications, "
            "follow-ups, or future contact. "
            "Never invent pickup times or store details. "
            "If the decision is NOT_READY, state only "
            "that pickup is not available yet. "
            "Do not add operational commitments."
        ),
        temperature=0,
        max_output_tokens=120,
    ),
)

explanation = (response.text or "").strip()

if not explanation:
    raise RuntimeError("Gemini returned an empty explanation")

print("CASE:", case["id"])
print("DECISION:", result["decision"])
print("REVISED EXPLANATION:", explanation)

Path("results/gemini_remediated_BASE-002.json").write_text(
    json.dumps({
        "case_id": case["id"],
        "model": model,
        "facts": facts,
        "explanation": explanation,
    }, indent=2),
    encoding="utf-8",
)

print("Saved remediation evidence.")
