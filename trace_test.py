from dotenv import load_dotenv
from langsmith import traceable
from langsmith.run_helpers import tracing_context

load_dotenv()

@traceable(name="Retail Pickup Validation", run_type="chain")
def validate_pickup():
    return {
        "country": "AE",
        "store_id": "UAE-DXB-01",
        "decision": "ELIGIBLE",
        "pickup_promised": True
    }

with tracing_context(enabled=True):
    result = validate_pickup()
    print(result)
