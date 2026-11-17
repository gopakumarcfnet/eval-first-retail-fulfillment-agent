
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from src.agent import build_graph

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY missing from .env")

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

# Load one existing golden case.
cases = [
    json.loads(line)
    for line in Path("data/golden_cases.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
]

case = next(c for c in cases if c["id"] == "BASE-001")

# Existing deterministic LangGraph decision.
graph = build_graph()
result = graph.invoke(
    {"request": case["input"]}
)["result"]

expected = case["expected"]["decision"]

if result["decision"] != expected:
    raise RuntimeError(
        "Golden decision mismatch. LLM call blocked."
    )

print("\nCASE:", case["id"])
print("DECISION:", result["decision"])
print("PICKUP PROMISED:", result["pickup_promised"])

# Only send synthetic, decision-relevant facts.
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

client = OpenAI(max_retries=0, timeout=30.0)

response = client.responses.create(
    model=MODEL,
    instructions=(
        "You explain simulated retail pickup decisions "
        "to customers in plain English. "
        "The supplied decision is authoritative. "
        "Never change the decision. "
        "Never invent pickup times, store hours, "
        "reservations, order details, or guarantees. "
        "If pickup_promised is false, never say "
        "the order is ready to collect. "
        "Missing UAE postal codes alone do not "
        "invalidate a pickup address in this simulation. "
        "Write 1 or 2 short sentences. "
        "Do not include a greeting."
    ),
    input=(
        "Explain this verified pickup result:\n"
        + json.dumps(facts)
    ),
    max_output_tokens=160,
    store=False,
)

explanation = response.output_text.strip()

if not explanation:
    raise RuntimeError("Model returned no explanation")

print("\nAI EXPLANATION:")
print(explanation)

print("\nMODEL:", MODEL)
if response.usage:
    print("INPUT TOKENS:", response.usage.input_tokens)
    print("OUTPUT TOKENS:", response.usage.output_tokens)

# Preserve evidence for evaluation without another API call.
output = {
    "case_id": case["id"],
    "model": MODEL,
    "facts": facts,
    "explanation": explanation,
    "input_tokens": (
        response.usage.input_tokens if response.usage else None
    ),
    "output_tokens": (
        response.usage.output_tokens if response.usage else None
    ),
}

Path("results").mkdir(exist_ok=True)

Path("results/llm_explanation_BASE-001.json").write_text(
    json.dumps(output, indent=2),
    encoding="utf-8",
)

print("\nSaved: results/llm_explanation_BASE-001.json")
