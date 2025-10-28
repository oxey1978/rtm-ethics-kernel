# RTM Ethics Kernel — Overview

A **stand-alone** ethics & guidelines decision kernel (separate from RTM).  
It produces deterministic choices with **audit logs** and is verified by **property-based tests**.

## What it is
- Core decision engine with:
  - `_cost(s, e)` scoring (H, C, N, M, B, F + future risk `e`)
  - hard **shutoffs** (high harm, infeasible, unmitigated collateral when alternatives exist)
  - a **policy gate** (require high necessity *or* low harm)
  - automatic **Defer / gather info** option (exactly once)
- Typed schemas (`DecisionAudit`, `AbortPayload`, `WhyNot`) using Pydantic v2.
- Tests use Hypothesis to prove monotonicity & safety invariants.

## Quickstart
```bash
pip install -r requirements.txt
pytest -q
