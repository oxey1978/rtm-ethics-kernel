# Architecture

This kernel is a **stand-alone ethics & guidelines decision engine**. It takes a list of candidate actions, scores them, applies shutoffs and policy gates, then selects the best viable option and returns an **audit** explaining why.

---

## Files & roles

- **`rtm_ethics_module.py`**  
  The engine. Core pieces:
  - `_cost(scores, e)` — turns a score dict `{H,C,N,M,B,F}` plus future risk `e` into a single number.  
    Lower cost = better.
  - `_ensure_defer(actions)` — guarantees there is exactly one “Defer / gather info” option.
  - `_violates_shutoffs(scores, mitigations, alts_exhausted)` — hard stops:
    - Infeasible (`F` below minimum)
    - High harm (when alternatives still exist)
    - Unmitigated collateral (when alternatives exist and necessity is low)
  - `_policy_gate_ok(scores)` — soft gate: allow if **N ≥ NECESSITY_HIGH** OR **H < HARM_LOW**.
  - `evaluate_actions(...)` — main entrypoint. Applies shutoffs & policy gates, then picks the lowest cost viable action and records **why others lost**.

- **`rtm_ethics_schema.py`**  
  Typed Pydantic models:
  - `DecisionAudit` (normal success payload)
  - `AbortPayload` (all options were shut off)
  - `WhyNot` (per-option reason when not selected)

- **`tests/test_rtm_ethics_properties.py`**  
  Property-based tests (Hypothesis) that prove invariants:
  - Harm ↑ or future risk ↑ ⇒ **cost must increase**
  - Betterment ↑ or mitigation ↑ ⇒ **cost must decrease**
  - Infeasible options are **never** selected
  - High harm not selected if alternatives remain
  - Unmitigated collateral blocked when policy says so
  - If selected, the action **passes policy gate**

- **`requirements.txt`** / **`pyproject.toml`**  
  Python dependencies and package metadata.

- **`.github/workflows/ci.yml`**  
  GitHub Actions: installs deps and runs tests on each push.

- **`docs/`**  
  Human-readable documentation (this page and others).

---

## Data model (scores)

Each candidate action supplies a `scores` dict:

```text
H = Harm (0–1, higher is worse)
C = Collateral (0–1)
N = Necessity (0–1)
M = Mitigation effectiveness (0–1)
B = Betterment / benefit (0–1)
F = Feasibility (0–1)
e = Future risk (trajectory risk, 0–1) passed to the cost function
```

The engine uses class constants (tunable):

```text
SHUTOFF_HARM_THRESHOLD
FEASIBILITY_MIN
NECESSITY_LOW
NECESSITY_HIGH
HARM_LOW
COLLATERAL_MIN
```

---

## Decision flow

1. **Ensure Defer:** add exactly one `"Defer / gather info"` option if missing.  
2. **Apply shutoffs:** drop actions that violate hard rules.  
3. **Policy gate:** prefer options that satisfy `(N ≥ HIGH) OR (H < LOW)`.  
4. **Cost & select:** among allowed pool, compute `_cost()` and pick the **lowest**.  
5. **Audit:** return `DecisionAudit` with `selected_action`, `scores`, `future_risk_e`,
   `mitigations`, and `why_not_others` (each losing action + reason).

---

## Example call

```python
from rtm_ethics_module import RtmEthicsModule

eng = RtmEthicsModule()
audit = eng.evaluate_actions(
    candidate_actions=[
        {"action_name":"A1","scores":{"H":0.2,"C":0.1,"N":0.9,"M":0.6,"B":0.7,"F":0.9},
         "future_risk_e":0.2,"mitigations":["guard"]},
        {"action_name":"A2","scores":{"H":0.6,"C":0.4,"N":0.4,"M":0.2,"B":0.3,"F":0.8},
         "future_risk_e":0.3,"mitigations":[]},
    ],
    bounds={"time":"now","budget":"low","authority":"med","risk_tolerance":"med"},
    alternatives_exhausted=False, trajectory_e_before=0.3
)
print(audit)
```

Outputs either:
- `DecisionAudit` (normal selection + reasons), or
- `AbortPayload` (`{"ACTION_ABORTED": true, "reason": "..."}`) if everything was shut off.

---

## Cost function (intuitive view)

```text
cost = (1.5*H + 0.6*C + 0.8*e)     # risks increase cost
       - (1.0*B + 0.9*M)           # benefits & mitigations reduce cost
       + 0.2*(1-F) + 0.1*(1-N)     # slight penalties for low feasibility/necessity
```

You can tune these weights later; property tests make sure the core **directions** still hold.
Step 3 — add docs/02-Invariants.md
Same drill:

Add file → name it docs/02-Invariants.md.

Paste the text below.

Commit.

markdown
Copy code
# Invariants (what the tests prove)

These properties must always hold:

## Monotonicity (cost function)
- If **H** increases (all else equal) → **cost increases**.
- If **B** increases → **cost decreases**.
- If **M** increases → **cost decreases**.
- If **future risk `e`** increases → **cost increases**.

## Shutoffs (hard stops)
- **Infeasible** actions (`F < FEASIBILITY_MIN`) are never selected.
- **High harm** (`H > SHUTOFF_HARM_THRESHOLD`) is not selected when alternatives remain.
- **Unmitigated collateral** is blocked when alternatives remain and necessity is low.

## Policy gate
- Any selected action satisfies: `N ≥ NECESSITY_HIGH` **or** `H < HARM_LOW`.

## Defer option
- A single `"Defer / gather info"` action is auto-inserted if missing (and never duplicated).

All of the above are enforced by property-based tests in `tests/test_rtm_ethics_properties.py`.
