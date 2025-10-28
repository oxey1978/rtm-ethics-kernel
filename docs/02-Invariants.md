# Invariants (what the tests prove)

These are the rules that must *always* hold true for the Ethics Kernel to behave correctly.  
Each rule is verified by property-based tests using Hypothesis.

---

## 1. Monotonicity (Cost function rules)

- If **H** (Harm) increases → **Cost increases**  
- If **B** (Betterment) increases → **Cost decreases**  
- If **M** (Moral alignment / Mitigation)** increases → **Cost decreases**  
- If **Future risk (E)** increases → **Cost increases**

---

## 2. Shutoffs (Hard stops)

These actions are *never* allowed:
- **Infeasible** actions where `F < FEASIBILITY_MIN`
- **High harm** actions (`H > SHUTOFF_HARM_THRESHOLD`) when safer alternatives exist
- **Unmitigated collateral** when necessity is low and alternatives exist

---

## 3. Policy Gate (Soft rule)

Any selected action must satisfy:

```
N ≥ NECESSITY_HIGH  OR  H < HARM_LOW
```

If neither is true, the action fails the policy gate and cannot be selected.

---

## 4. Defer Option

The system automatically adds exactly **one**  
“Defer / gather info” action if it isn’t already present.  
It’s never duplicated.

---

All of these rules are enforced and validated by  
`tests/test_rtm_ethics_properties.py`.
