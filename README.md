# RTM Ethics Kernel

A deterministic, auditable decision kernel that applies property-based proofs to validate ethical invariants.

---

## Overview
This kernel enforces clear safety and moral rules:
- High-harm or infeasible actions are automatically shut off.
- Betterment and moral alignment always reduce overall cost.
- Each decision produces a structured audit (JSON-schema-validated).

---

## Quickstart
```bash
pip install -r requirements.txt
pytest
```

---

## Minimal use
```python
from rtm_ethics_module import RtmEthicsModule

eng = RtmEthicsModule()
audit = eng.evaluate_actions(
  candidate_actions=[
    {"action_name":"A1","scores":{"H":0.2,"C":0.1,"N":0.9,"M":0.6,"B":0.7,"F":0.9},"future_risk_e":0.2,"mitigations":["guard"]},
    {"action_name":"A2","scores":{"H":0.6,"C":0.4,"N":0.4,"M":0.2,"B":0.3,"F":0.8},"future_risk_e":0.3,"mitigations":[]},
  ],
  bounds={"time":"now","budget":"low","authority":"med","risk_tolerance":"med"},
  alternatives_exhausted=False, trajectory_e_before=0.3
)
print(audit)
```

---

## Docs
- [Overview](docs/00-Overview.md)  
- [Architecture](docs/01-Architecture.md)  
- [Invariants](docs/02-Invariants.md)  
- [Sessions Index](docs/03-Sessions-Index.md)
