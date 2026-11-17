# Eval-First Global Retail Pickup & Address Validation (Phase 1)

**Independent synthetic retail simulation. Not affiliated with Apple.** No internal data, business rules, or real store coordinates are used; locations are illustrative synthetic fixtures.

## Why this exists
Demonstrate testable country-specific address handling, store lookup, pickup readiness, regression gates and (optionally) LangGraph execution / LangSmith tracing.

## Architecture
`Request → Address validation → Location resolution → Pickup eligibility → Decision`.
The decision functions are deterministic. LangGraph orchestrates the same functions when installed.

## Quick start (Python 3.10+)
From the repository root:

```bash
python -m unittest discover -s tests -v
python -m evals.run_evals
python -m src.run
```

These three commands require only Python's standard library. `results/baseline.csv` is generated locally.

## Optional LangGraph and LangSmith

```bash
python -m pip install -r requirements.txt
# Configure LANGSMITH_API_KEY, LANGSMITH_TRACING=true, LANGSMITH_PROJECT
python -m src.run --graph
```

LangSmith traces require a configured account, key and network access. No traces are claimed until verified in your own LangSmith project.

## Dataset
`data/golden_cases.jsonl` includes 30 synthetic scenarios spanning 3 countries and 6 stores. Each case has `id`, `category`, `input`, `expected.decision`. The fixture policy intentionally makes US postal codes required and AE/TR optional; this is a **fictional test policy**, not legal or authoritative country guidance.

## Evaluation
`evals/run_evals.py` measures decision accuracy, false pickup promises, coordinate integrity, and output schema. This Phase 1 harness is deterministic. **DeepEval LLM-as-judge and conversational evaluations are planned for Phase 2**, not yet implemented. The dependency is listed for later work.

## Portfolio honesty
Baseline metrics must be computed by running the included commands. Do not represent synthetic scores as production results. The first baseline may be perfect because the fixtures mirror the policy; Phase 2 should include held-out adversarial cases and injected failures.

## Roadmap
1. Phase 1: policy fixtures, 30 golden cases, deterministic evaluation and optional LangGraph tracing.
2. Phase 2: natural-language interpretation, response generation, DeepEval GEval rubric, judge calibration.
3. Phase 3: multi-turn simulation, held-out regression suites, prompt/model comparisons, release gate and failure reports.
