import math
from typing import Dict, Any, List
from hypothesis import given, settings, strategies as st, HealthCheck
from rtm_ethics_module import RtmEthicsModule
from rtm_ethics_schema import DecisionAudit, AbortPayload

def _new_eng() -> RtmEthicsModule:
    return RtmEthicsModule()

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

HARM_T = RtmEthicsModule.SHUTOFF_HARM_THRESHOLD
FEAS_MIN = RtmEthicsModule.FEASIBILITY_MIN
NEC_LOW = RtmEthicsModule.NECESSITY_LOW
NEC_HIGH = RtmEthicsModule.NECESSITY_HIGH
HARM_LOW = RtmEthicsModule.HARM_LOW
COLL_MIN = RtmEthicsModule.COLLATERAL_MIN

scores_strat = st.fixed_dictionaries({
    "H": st.floats(min_value=0, max_value=1),
    "C": st.floats(min_value=0, max_value=1),
    "N": st.floats(min_value=0, max_value=1),
    "M": st.floats(min_value=0, max_value=1),
    "B": st.floats(min_value=0, max_value=1),
    "F": st.floats(min_value=0, max_value=1),
})

bounds = {"time": "t", "budget": "b", "authority": "a", "risk_tolerance": "r"}

@given(scores=scores_strat, e=st.floats(min_value=0, max_value=1))
@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.filter_too_much])
def test_cost_monotone_in_h(scores: Dict[str, float], e: float):
    eng = _new_eng()
    c0 = eng._cost(scores, e)
    s1 = dict(scores); s1["H"] = clamp01(scores["H"] + 0.1)
    c1 = eng._cost(s1, e)
    assert c1 >= c0
    if s1["H"] > scores["H"]:
        assert c1 > c0

@given(scores=scores_strat, e=st.floats(min_value=0, max_value=1))
@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.filter_too_much])
def test_cost_monotone_decreasing_in_b(scores: Dict[str, float], e: float):
    eng = _new_eng()
    c0 = eng._cost(scores, e)
    s1 = dict(scores); s1["B"] = clamp01(scores["B"] + 0.1)
    c1 = eng._cost(s1, e)
    assert c1 <= c0
    if s1["B"] > scores["B"]:
        assert c1 < c0

@given(scores=scores_strat, e=st.floats(min_value=0, max_value=1))
@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.filter_too_much])
def test_cost_monotone_decreasing_in_m(scores, e):
    eng = _new_eng()
    c0 = eng._cost(scores, e)
    s1 = dict(scores); s1["M"] = clamp01(scores["M"] + 0.1)
    c1 = eng._cost(s1, e)
    assert c1 <= c0
    if s1["M"] > scores["M"]:
        assert c1 < c0

@given(scores=scores_strat, e=st.floats(min_value=0, max_value=1))
@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.filter_too_much])
def test_cost_monotone_in_future_risk(scores, e):
    eng = _new_eng()
    c0 = eng._cost(scores, e)
    e2 = clamp01(e + 0.1)
    c1 = eng._cost(scores, e2)
    assert c1 >= c0
    if e2 > e:
        assert c1 > c0

@given(
    lowH_scores=scores_strat.map(lambda s: {**s, "H": max(min(HARM_T - 0.1, 1.0), 0.0), "F": max(s["F"], FEAS_MIN)}),
    highH_scores=scores_strat.map(lambda s: {**s, "H": min(max(HARM_T + 0.1, 0.0), 1.0), "F": max(s["F"], FEAS_MIN)})
)
@settings(deadline=None, max_examples=120, suppress_health_check=[HealthCheck.filter_too_much])
def test_high_harm_action_not_selected_when_alternatives_remain(lowH_scores, highH_scores):
    eng = _new_eng()
    actions = [
        {"action_name": "LowH", "scores": lowH_scores, "future_risk_e": 0.2, "mitigations": []},
        {"action_name": "HighH", "scores": highH_scores, "future_risk_e": 0.2, "mitigations": []},
    ]
    out = eng.evaluate_actions(candidate_actions=actions, bounds=bounds, alternatives_exhausted=False, trajectory_e_before=0.3)
    if not (isinstance(out, dict) and out.get("ACTION_ABORTED")):
        assert out["selected_action"] != "HighH"

@given(
    infeasible_scores=scores_strat.map(lambda s: {**s, "F": max(FEAS_MIN - 0.1, 0.0)}),
    ok_scores=scores_strat.map(lambda s: {**s, "F": min(FEAS_MIN + 0.1, 1.0), "H": max(HARM_LOW - 0.1, 0.0)})
)
@settings(deadline=None, max_examples=120, suppress_health_check=[HealthCheck.filter_too_much])
def test_infeasible_option_is_never_selected(infeasible_scores, ok_scores):
    eng = _new_eng()
    actions = [
        {"action_name": "Infeasible", "scores": infeasible_scores, "future_risk_e": 0.3, "mitigations": []},
        {"action_name": "FeasibleOK", "scores": ok_scores, "future_risk_e": 0.3, "mitigations": []},
    ]
    out = eng.evaluate_actions(candidate_actions=actions, bounds=bounds, alternatives_exhausted=True, trajectory_e_before=0.4)
    if not (isinstance(out, dict) and out.get("ACTION_ABORTED")):
        assert out["selected_action"] != "Infeasible"

@given(
    bad_scores=scores_strat.map(lambda s: {**s, "C": min(max(COLL_MIN + 0.1, 0.0), 1.0), "N": max(NEC_LOW - 0.1, 0.0),
                                          "H": max(min(HARM_T - 0.1, 1.0), 0.0), "F": min(max(FEAS_MIN + 0.1, 0.0), 1.0)}),
    good_scores=scores_strat.map(lambda s: {**s, "C": max(COLL_MIN - 0.05, 0.0), "N": min(NEC_HIGH + 0.1, 1.0),
                                            "H": max(HARM_LOW - 0.1, 0.0), "F": min(max(FEAS_MIN + 0.1, 0.0), 1.0)})
)
@settings(deadline=None, max_examples=120, suppress_health_check=[HealthCheck.filter_too_much])
def test_unmitigated_collateral_is_shutoff(bad_scores, good_scores):
    eng = _new_eng()
    actions = [
        {"action_name": "BadUnmitigated", "scores": bad_scores, "future_risk_e": 0.3, "mitigations": []},
        {"action_name": "GoodAlternative", "scores": good_scores, "future_risk_e": 0.3, "mitigations": []},
    ]
    out = eng.evaluate_actions(candidate_actions=actions, bounds=bounds, alternatives_exhausted=False, trajectory_e_before=0.4)
    if not (isinstance(out, dict) and out.get("ACTION_ABORTED")):
        assert out["selected_action"] != "BadUnmitigated"

@given(
    base_scores=scores_strat.map(lambda s: {**s, "C": 0.4, "N": min(NEC_HIGH + 0.1, 1.0), "H": 0.15, "F": 0.9})
)
@settings(deadline=None, max_examples=120, suppress_health_check=[HealthCheck.filter_too_much])
def test_mitigations_allow_selection_when_policy_ok(base_scores):
    eng = _new_eng()
    actions = [
        {"action_name": "WithMitigation", "scores": base_scores, "future_risk_e": 0.3, "mitigations": ["traffic marshal"]},
        {"action_name": "Alt", "scores": {**base_scores, "B": clamp01(base_scores["B"] * 0.8)}, "future_risk_e": 0.3, "mitigations": []},
    ]
    out = eng.evaluate_actions(candidate_actions=actions, bounds={"time":"now","budget":"none","authority":"low","risk_tolerance":"med"},
                               alternatives_exhausted=True, trajectory_e_before=0.5)
    if not (isinstance(out, dict) and out.get("ACTION_ABORTED")):
        if out["selected_action"] != "WithMitigation":
            reasons = {r["action"]: r["reason"] for r in out["why_not_others"]}
            if "WithMitigation" in reasons:
                assert "Collateral" not in str(reasons["WithMitigation"])

@given(actions_data=st.lists(st.fixed_dictionaries({
        "action_name": st.text(min_size=1, max_size=12),
        "scores": scores_strat,
        "future_risk_e": st.floats(min_value=0, max_value=1),
        "mitigations": st.lists(st.text(), max_size=2)
    }), min_size=2, max_size=5))
@settings(deadline=None, max_examples=120, suppress_health_check=[HealthCheck.filter_too_much])
def test_selected_action_always_passes_policy_gate(actions_data: List[Dict[str, Any]]):
    eng = _new_eng()
    actions = list(actions_data) + [{
        "action_name":"AuditPass",
        "scores":{"H":0.1,"C":0.0,"N":1.0,"M":1.0,"B":1.0,"F":1.0},
        "future_risk_e":0.0,"mitigations":[]}]
    out = eng.evaluate_actions(candidate_actions=actions, bounds={"time":"t","budget":"b","authority":"a","risk_tolerance":"r"},
                               alternatives_exhausted=True, trajectory_e_before=0.5)
    if not (isinstance(out, dict) and out.get("ACTION_ABORTED")):
        sel = out["scores"]
        assert (sel.get("N",0.0) >= NEC_HIGH) or (sel.get("H",0.0) < HARM_LOW)

def test_defer_action_is_inserted_and_not_duplicated():
    eng = _new_eng()
    actions_no_defer = [{"action_name":"Action1","scores":{"H":0.5,"C":0.5,"N":0.5,"M":0.5,"B":0.5,"F":0.5},
                         "future_risk_e":0.5,"mitigations":["test"]}]
    result_no_defer = eng._ensure_defer(actions_no_defer)
    assert sum(1 for a in result_no_defer if "Defer" in a["action_name"]) == 1
    assert len(result_no_defer) == 2

    actions_with_defer = actions_no_defer + [{"action_name":"Defer / gather info",
        "scores":{"H":0.0,"C":0.0,"N":0.0,"M":0.5,"B":0.1,"F":1.0},"future_risk_e":0.2,
        "mitigations":["Request critical facts"]}]
    result_with_defer = eng._ensure_defer(actions_with_defer)
    assert sum(1 for a in result_with_defer if "Defer" in a["action_name"]) == 1
    assert len(result_with_defer) == 2

def test_decision_audit_conforms_to_schema():
    eng = _new_eng()
    out = eng.evaluate_actions(
        candidate_actions=[
            {"action_name":"A1","scores":{"H":0.2,"C":0.0,"N":0.8,"M":0.8,"B":0.6,"F":1.0},"future_risk_e":0.3,"mitigations":[]},
            {"action_name":"A2","scores":{"H":0.9,"C":0.1,"N":0.1,"M":0.1,"B":0.1,"F":0.4},"future_risk_e":0.8,"mitigations":[]},
        ],
        bounds={"time":"now","budget":"none","authority":"low","risk_tolerance":"med"},
        alternatives_exhausted=False, trajectory_e_before=0.5)
    if isinstance(out, dict) and out.get("ACTION_ABORTED"):
        AbortPayload.model_validate(out)
    else:
        DecisionAudit.model_validate(out)
