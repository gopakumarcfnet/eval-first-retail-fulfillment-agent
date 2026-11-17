
import json

from dotenv import load_dotenv
from langsmith import traceable
from langsmith.run_helpers import tracing_context
from langchain_core.tracers.langchain import wait_for_all_tracers

from src.agent import build_graph

load_dotenv()

# Compile the actual LangGraph workflow
graph = build_graph()


@traceable(name="Retail Fulfillment - UAE Pickup", run_type="chain")
def run_pickup(request):
    state = graph.invoke(
        {"request": request},
        config={"run_name": "Global Pickup Validation"},
    )
    return state["result"]


request = {
    "country": "AE",
    "city": "Dubai",
    "district": "Downtown",
    "store_id": "UAE-DXB-01",
    "order_status": "READY_FOR_PICKUP",
    "postal_code": None,
}

with tracing_context(enabled=True):
    result = run_pickup(request)
    print(json.dumps(result, indent=2))

wait_for_all_tracers()
