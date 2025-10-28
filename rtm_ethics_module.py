from typing import List, Dict, Any

class RtmEthicsModule:
    SHUTOFF_HARM_THRESHOLD = 0.7
    FEASIBILITY_MIN = 0.5
    NECESSITY_LOW = 0.3
    NECESSITY_HIGH = 0.8
    HARM_LOW = 0.2
    COLLATERAL_MIN = 0.35

    def _cost(self, s: Dict[str, float], e: float) -> float:
        H, C, N, M, B, F = (s.get(k, 0.0) for k in "HCNMBF")
        return (1.5*H + 0.6*C + 0.8*e) - (1.0*B + 0.9*M) + 0.2*(1.0-F) + 0.1*(1.0-N)

    def _ensure_defer(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not any("Defer" in a["action_name"] for a in actions):
            actions = actions + [{
                "action_name": "Defer / gather info",
                "scores": {"H":0.0,"C":0.0,"N":0.0,"M":0.5,"B":0.1,"F":1.0},
                "future_risk_e": 0.2,
                "mitigations": ["Request critical facts"],
            }]
        seen = False
        out = []
        for a in actions:
            if "Defer" in a["action_name"]:
                if seen:
                    continue
                seen = True
            out.append(a)
        return out

    def _violates_shutoffs(self, s: Dict[str, float], mitigations: List[str], alts_exhausted: bool) -> str:
        if s.get("F", 0.0) < self.FEASIBILITY_MIN:
            return "Infeasible"
        if not alts_exhausted and s.get("H", 0.0) > self.SHUTOFF_HARM_THRESHOLD:
            return "HighHarm"
        if (not alts_exhausted and s.get("C", 0.0) > self.COLLATERAL_MIN
            and s.get("N", 0.0) < self.NECESSITY_LOW and len(mitigations) == 0):
            return "Collateral"
        return ""

    def _policy_gate_ok(self, s: Dict[str, float]) -> bool:
        return (s.get("N", 0.0) >= self.NECESSITY_HIGH) or (s.get("H", 0.0) < self.HARM_LOW)

    def evaluate_actions(self, candidate_actions: List[Dict[str, Any]],
                         bounds: Dict[str, Any],
                         alternatives_exhausted: bool,
                         trajectory_e_before: float) -> Dict[str, Any]:
        actions = self._ensure_defer(candidate_actions)
        why, viable = [], []

        for a in actions:
            r = self._violates_shutoffs(a["scores"], a.get("mitigations", []), alternatives_exhausted)
            if r: why.append({"action": a["action_name"], "reason": r})
            else: viable.append(a)

        if not viable:
            return {"ACTION_ABORTED": True, "reason": "All options shut off",
                    "top_safer_options": [], "missing_facts_suggestion": []}

        e = trajectory_e_before
        policy_ok = [a for a in viable if self._policy_gate_ok(a["scores"])]
        pool = policy_ok if policy_ok else viable

        best = min(pool, key=lambda a: self._cost(a["scores"], a.get("future_risk_e", e)))
        for a in pool:
            if a is best:
                continue
            why.append({"action": a["action_name"], "reason": "HigherCost"})

        return {
            "selected_action": best["action_name"],
            "scores": best["scores"],
            "future_risk_e": best.get("future_risk_e", e),
            "mitigations": best.get("mitigations", []),
            "why_not_others": why
        }
