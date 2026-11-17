
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.agent import build_graph

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY missing from .env")

# Load one golden case
cases = [
    json.loads(line)
    for line in Path("data/golden_cases.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
]

case = next(c for c in cases if c["id"] == "BASE-001")

# Execute existing LangGraph decision engine
graph = build_graph()
result = graph.invoke(
    {"request": case["input"]}
)["result"]

expected = case["expected"]["decision"]

if result["decision"] != expected:
    raise RuntimeError(
        "Golden decision mismatch. Gemini call blocked."
    )

facts = {
    "country": case["input"].get("country"),
    "city": case["input"].get("city"),
    "order_status": case["input"].get("order_status"),
    "postal_code_present": bool(
        case["input"].get("postal_code")
    ),
    "decision": result["decision"],
    "pickup_promised": result["pickup_promised"],
    "reason": result.get("reason"),
}

print("CASE:", case["id"])
print("DECISION:", result["decision"])
print("PICKUP PROMISED:", result["pickup_promised"])

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model=model,
    contents=(
        "Explain the following verified pickup decision "
        "to a customer in one or two short sentences.\n"
        + json.dumps(facts)
    ),
    config=types.GenerateContentConfig(
        system_instruction=(
            "You explain simulated retail pickup decisions. "
            "The supplied decision is authoritative. "
            "Never change the decision. "
            "Never invent store hours, pickup times, "
            "order details, or guarantees. "
            "If pickup_promised is false, do not tell "
            "the customer the order is ready. "
            "A missing UAE postal code alone does not "
            "invalidate pickup in this simulation."
        ),
        temperature=0,
        max_output_tokens=160,
    ),
)

explanation = (response.text or "").strip()

if not explanation:
    raise RuntimeError("Gemini returned an empty explanation")

print("\nGEMINI EXPLANATION:")
print(explanation)
print("\nMODEL:", model)

usage = response.usage_metadata

output = {
    "case_id": case["id"],
    "model": model,
    "facts": facts,
    "explanation": explanation,
    "input_tokens": (
        usage.prompt_token_count if usage else None
    ),
    "output_tokens": (
        usage.candidates_token_count if usage else None
    ),
}

Path("results").mkdir(exist_ok=True)

Path("results/gemini_explanation_BASE-001.json").write_text(
    json.dumps(output, indent=2),
    encoding="utf-8",
)

print("\nSaved: results/gemini_explanation_BASE-001.json")
