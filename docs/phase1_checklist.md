# Phase 1 guided checklist

- [ ] Read README and review synthetic policy in `src/agent.py`.
- [ ] Inspect `data/golden_cases.jsonl` and explain expected decisions for UAE, Turkey, and US cases.
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python -m evals.run_evals` and inspect `results/baseline.csv`.
- [ ] Run `python -m src.run` and inspect output JSON.
- [ ] Optional: install requirements, configure LangSmith using environment variables, run `python -m src.run --graph`, verify a trace appears in LangSmith.
- [ ] Add at least five new edge cases without editing business rules; verify tests pass.
- [ ] Deliberately break a policy rule, run evals, capture the failure, then revert the change.

## Evidence to capture for portfolio
1. Baseline summary and number of test cases.
2. One failed-regression screenshot and explanation.
3. A LangSmith trace screenshot, only after successful setup.
4. A short release note: which failures would block release and why.
