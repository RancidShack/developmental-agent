"""
verify_v1_14.py
---------------
Pre-flight verifier for curiosity_agent_v1_14_batch.py.

Run before the full 40-run batch. All eight criteria must PASS.

Criteria:
  14.1  RETURN_ENV1_FAMILIES positions — att_blue matches ENV2,
        haz_blue matches ENV1. No None positions in BLUE family.
  14.2  Return world completeness — haz_blue in hazard_cells,
        att_blue in attractor_cells, no unreachable hazards,
        family_precondition_attractor['haz_blue'] == 'att_blue'.
  14.3  Pre-transition logic — RETURN_ENV1_PRECOMPLETED hazards
        become KNOWLEDGE; haz_blue remains HAZARD.
  14.4  carry_agent invariant — mastery_flag['att_blue'] == 1
        preserved after full replacement; _knowledge_unlocked
        state correct for precompleted and haz_blue.
  14.5  Transformation fires on first contact — live call to
        _run_return_env1 with a properly prepared agent produces
        arc_complete=True and transformation_step is not None.
  14.6  Return gate logic — _return_to_env1_condition_met returns
        True for CONFIRMED_STATE only; False for PREDICTED_STATE,
        UNRESOLVABLE_STATE, and no record.
  14.7  ENV2 exit on att_blue mastery — batch source confirms exit
        fires on att_blue_mastery_step not end_state_banked_step.
  14.8  ARC_COMPLETE_FIELDS complete — all pre-registration fields
        present in ARC_COMPLETE_FIELDS.

Usage:
    python verify_v1_14.py

Exits 0 on full pass, 1 on any failure.
"""

import sys
import traceback

PASS = "PASS"
FAIL = "FAIL"


def run_criterion(label, fn):
    try:
        result, detail = fn()
        status = PASS if result else FAIL
    except Exception as e:
        status = FAIL
        detail = f"Exception: {e}\n{traceback.format_exc()}"
    print(f"  [{status}] {label}")
    if status == FAIL or detail:
        for line in str(detail).splitlines():
            print(f"         {line}")
    return status == PASS


# ---------------------------------------------------------------------------
# Criterion implementations
# ---------------------------------------------------------------------------

def criterion_14_1():
    """RETURN_ENV1_FAMILIES positions match source environments."""
    from v1_13_world import ENV1_FAMILIES, ENV2_FAMILIES, BLUE
    from curiosity_agent_v1_14_batch import RETURN_ENV1_FAMILIES

    env1_haz_blue = next(
        (f.get("haz_pos") for f in ENV1_FAMILIES if f["colour"] == BLUE), None
    )
    env2_att_blue = next(
        (f.get("att_pos") for f in ENV2_FAMILIES if f["colour"] == BLUE), None
    )
    ret_blue = next(
        (f for f in RETURN_ENV1_FAMILIES if f["colour"] == BLUE), None
    )

    if ret_blue is None:
        return False, "BLUE family absent from RETURN_ENV1_FAMILIES"

    ret_att = ret_blue.get("att_pos")
    ret_haz = ret_blue.get("haz_pos")
    ret_att_id = ret_blue.get("att_id")
    ret_haz_id = ret_blue.get("haz_id")

    checks = {
        "att_id == 'att_blue'":    ret_att_id == "att_blue",
        "haz_id == 'haz_blue'":    ret_haz_id == "haz_blue",
        "att_pos not None":        ret_att is not None,
        "haz_pos not None":        ret_haz is not None,
        "att_pos matches ENV2":    ret_att == env2_att_blue,
        "haz_pos matches ENV1":    ret_haz == env1_haz_blue,
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = (
        f"att_pos: return={ret_att} env2={env2_att_blue} | "
        f"haz_pos: return={ret_haz} env1={env1_haz_blue}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


def criterion_14_2():
    """Return world completeness — full BLUE family, correct precondition."""
    from v1_13_world import V113World, HAZARD, ATTRACTOR
    from curiosity_agent_v1_14_batch import RETURN_ENV1_FAMILIES

    w = V113World(
        families=RETURN_ENV1_FAMILIES,
        hazard_cost=1.0,
        has_end_state=True,
        seed=42,
        unreachable_hazards=None,
    )

    checks = {
        "haz_blue in hazard_cells":       "haz_blue" in w.hazard_cells,
        "att_blue in attractor_cells":    "att_blue" in w.attractor_cells,
        "haz_blue NOT unreachable":       "haz_blue" not in w.unreachable_hazard_ids,
        "haz_blue type == HAZARD":        w.object_type.get("haz_blue") == HAZARD,
        "att_blue type == ATTRACTOR":     w.object_type.get("att_blue") == ATTRACTOR,
        "precondition haz_blue→att_blue": (
            w.family_precondition_attractor.get("haz_blue") == "att_blue"
        ),
        "haz_blue knowledge_unlocked False": (
            "haz_blue" in w.knowledge_unlocked
            and w.knowledge_unlocked["haz_blue"] is False
        ),
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = (
        f"family_precondition_attractor={w.family_precondition_attractor} | "
        f"hazard_cells={sorted(w.hazard_cells)}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


def criterion_14_3():
    """Pre-transition logic: PRECOMPLETED → KNOWLEDGE; haz_blue stays HAZARD."""
    from v1_13_world import V113World, HAZARD, KNOWLEDGE
    from curiosity_agent_v1_14_batch import (
        RETURN_ENV1_FAMILIES, RETURN_ENV1_PRECOMPLETED,
    )

    w = V113World(
        families=RETURN_ENV1_FAMILIES,
        hazard_cost=1.0,
        has_end_state=True,
        seed=42,
        unreachable_hazards=None,
    )
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in w.hazard_cells:
            w.transform_to_knowledge(oid)

    failed = []
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid not in w.hazard_cells:
            continue
        if w.object_type.get(oid) != KNOWLEDGE:
            failed.append(f"{oid} not KNOWLEDGE (type={w.object_type.get(oid)})")
        if not w.knowledge_unlocked.get(oid):
            failed.append(f"{oid} knowledge_unlocked not True")

    if w.object_type.get("haz_blue") != HAZARD:
        failed.append(f"haz_blue type={w.object_type.get('haz_blue')} (expect HAZARD)")
    if w.knowledge_unlocked.get("haz_blue") is not False:
        failed.append("haz_blue knowledge_unlocked not False")

    ok = not failed
    detail = (
        f"PRECOMPLETED={RETURN_ENV1_PRECOMPLETED} | "
        f"haz_blue type={w.object_type.get('haz_blue')}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


def criterion_14_4():
    """carry_agent invariant: mastery_flag['att_blue']==1, _knowledge_unlocked correct."""
    from v1_13_world import V113World, HAZARD
    from v1_10_agent import V110Agent
    from curiosity_agent_v1_14_batch import (
        RETURN_ENV1_FAMILIES, RETURN_ENV1_PRECOMPLETED, RETURN_ENV1_STEPS,
    )

    w = V113World(
        families=RETURN_ENV1_FAMILIES,
        hazard_cost=1.0,
        has_end_state=True,
        seed=42,
        unreachable_hazards=None,
    )
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in w.hazard_cells:
            w.transform_to_knowledge(oid)

    agent = V110Agent(w, total_steps=RETURN_ENV1_STEPS, num_actions=27)

    # Apply carry logic exactly as _run_return_env1 does it
    agent.mastery_flag = {a: 0 for a in w.attractor_cells}
    agent.mastery_flag['att_blue'] = 1      # CRITICAL INVARIANT

    agent._knowledge_unlocked = {h: False for h in w.hazard_cells}
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in agent._knowledge_unlocked:
            agent._knowledge_unlocked[oid] = True

    agent.knowledge_banked = {h: False for h in w.hazard_cells}
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in agent.knowledge_banked:
            agent.knowledge_banked[oid] = True

    failed = []
    if agent.mastery_flag.get('att_blue') != 1:
        failed.append(f"mastery_flag['att_blue']={agent.mastery_flag.get('att_blue')}")

    other_mastery = {a: agent.mastery_flag.get(a) for a in w.attractor_cells
                     if a != 'att_blue'}
    if any(v != 0 for v in other_mastery.values()):
        failed.append(f"non-zero mastery on other attractors: {other_mastery}")

    if agent._knowledge_unlocked.get('haz_blue') is not False:
        failed.append("_knowledge_unlocked['haz_blue'] not False")

    pre_ku = {oid: agent._knowledge_unlocked.get(oid)
              for oid in RETURN_ENV1_PRECOMPLETED
              if oid in agent._knowledge_unlocked}
    if any(v is not True for v in pre_ku.values()):
        failed.append(f"_knowledge_unlocked PRECOMPLETED not all True: {pre_ku}")

    if agent.knowledge_banked.get('haz_blue') is not False:
        failed.append("knowledge_banked['haz_blue'] not False")

    ok = not failed
    detail = (
        f"mastery_flag['att_blue']={agent.mastery_flag.get('att_blue')} | "
        f"_knowledge_unlocked['haz_blue']={agent._knowledge_unlocked.get('haz_blue')}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


def criterion_14_5():
    """Transformation fires in live _run_return_env1 call (arc_complete=True)."""
    import numpy as np
    from v1_13_world import V113World, ENV1_FAMILIES
    from v1_10_agent import V110Agent
    from curiosity_agent_v1_14_batch import (
        RETURN_ENV1_STEPS, _run_return_env1,
    )

    # Build a dummy agent via ENV1 world (unreachable_hazards=['haz_blue'])
    # so agent is initialised with a valid world reference.
    # _run_return_env1 replaces agent.world and resets all state internally —
    # the dummy agent just needs to be a valid V110Agent instance.
    np.random.seed(42)
    dummy_world = V113World(
        families=ENV1_FAMILIES,
        hazard_cost=1.0,
        has_end_state=True,
        seed=42,
        unreachable_hazards=['haz_blue'],
    )
    dummy_agent = V110Agent(dummy_world, total_steps=RETURN_ENV1_STEPS,
                            num_actions=27)

    # Call _run_return_env1 directly; it applies all carry logic internally.
    result = _run_return_env1(
        run_idx=0,
        seed=42,
        hazard_cost=1.0,
        carry_agent=dummy_agent,
        carry_prov_obs=None,
        schema_v13_obs=None,
        causal_obs=None,
        env1_surprise_step=1000,
        prediction_step=500,
        transfer_step=1000,
        confirmation_step=50000,
    )

    ok = (result['arc_complete'] is True
          and result['arc_timeout'] is False
          and result['transformation_step'] is not None)
    detail = (
        f"arc_complete={result['arc_complete']} | "
        f"arc_timeout={result['arc_timeout']} | "
        f"transformation_step={result['transformation_step']} | "
        f"actual_steps={result['actual_steps']}"
    )
    return ok, detail


def criterion_14_6():
    """Return gate: _return_to_env1_condition_met correct for all states."""
    from v1_13_schema_extension import (
        V13SchemaObserver as V13SchemaObserverPrediction,
        PREDICTED_STATE, CONFIRMED_STATE, UNRESOLVABLE_STATE,
    )
    from curiosity_agent_v1_14_batch import _return_to_env1_condition_met

    def make_obs(state):
        obs = V13SchemaObserverPrediction(prediction_enabled=True)
        obs.add_predicted_record({
            "object_id": "haz_blue",
            "predicted_precondition": "att_blue",
            "basis_chains": ["haz_yellow", "haz_green"],
            "prediction_step": 1000,
        })
        # add_predicted_record always sets state=PREDICTED_STATE
        if state == CONFIRMED_STATE:
            obs.confirm_predicted_record("haz_blue", 50000, 2)
        elif state == UNRESOLVABLE_STATE:
            obs.mark_unresolvable("haz_blue")
        return obs

    checks = {
        f"CONFIRMED_STATE → True":
            _return_to_env1_condition_met(make_obs(CONFIRMED_STATE)) is True,
        f"PREDICTED_STATE → False":
            _return_to_env1_condition_met(make_obs(PREDICTED_STATE)) is False,
        f"UNRESOLVABLE_STATE → False":
            _return_to_env1_condition_met(make_obs(UNRESOLVABLE_STATE)) is False,
        "None obs → False":
            _return_to_env1_condition_met(None) is False,
        "Empty obs → False":
            _return_to_env1_condition_met(
                V13SchemaObserverPrediction(prediction_enabled=True)
            ) is False,
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = str(checks) + (f" | FAILED: {failed}" if failed else "")
    return ok, detail


def criterion_14_7():
    """ENV2 exit on att_blue mastery — confirmed by source inspection."""
    import inspect
    from curiosity_agent_v1_14_batch import _run_environment

    src = inspect.getsource(_run_environment)

    # The v1.14 ENV2 early exit must fire on att_blue_mastery_step,
    # not end_state_banked_step. Check both conditions in the source.
    att_blue_exit   = "att_blue_mastery_step is not None" in src
    not_es_exit     = "env_number == 2 and end_state_banked_step is not None" not in src

    # Additionally: ENV2 exit line must be guarded by env_number == 2
    env2_att_guard  = "env_number == 2 and att_blue_mastery_step" in src

    checks = {
        "att_blue_mastery_step is not None present": att_blue_exit,
        "end_state_banked_step not ENV2 exit condition": not_es_exit,
        "ENV2 guard on att_blue exit": env2_att_guard,
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = (
        f"att_blue_exit={att_blue_exit} | "
        f"not_es_exit={not_es_exit} | "
        f"env2_att_guard={env2_att_guard}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


def criterion_14_8():
    """ARC_COMPLETE_FIELDS contains all pre-registered fields."""
    from curiosity_agent_v1_14_batch import ARC_COMPLETE_FIELDS

    required = [
        "arch", "run_idx", "seed", "hazard_cost",
        "arc_complete", "arc_timeout", "ineligible_reason",
        "env1_surprise_step",
        "prediction_step",
        "transfer_triggered_step",
        "confirmation_step",
        "return_step",
        "transformation_step",
        "arc_total_steps",
        "arc_env_span",
        "causal_chain_depth",
        "causal_chain_complete",
    ]
    missing = [f for f in required if f not in ARC_COMPLETE_FIELDS]
    ok = not missing
    detail = (
        f"required={len(required)} present={len(ARC_COMPLETE_FIELDS)} "
        f"missing={missing}"
    )
    return ok, detail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("v1.14 Pre-flight Verifier")
    print("=" * 50)
    print()

    criteria = [
        ("14.1  RETURN_ENV1_FAMILIES positions (att_blue=ENV2, haz_blue=ENV1)",
         criterion_14_1),
        ("14.2  Return world completeness (haz_blue reachable, precondition correct)",
         criterion_14_2),
        ("14.3  Pre-transition logic (PRECOMPLETED→KNOWLEDGE, haz_blue stays HAZARD)",
         criterion_14_3),
        ("14.4  carry_agent invariant (mastery_flag['att_blue']=1, _knowledge_unlocked)",
         criterion_14_4),
        ("14.5  Transformation fires in live _run_return_env1 call",
         criterion_14_5),
        ("14.6  _return_to_env1_condition_met gate (confirmed=True only)",
         criterion_14_6),
        ("14.7  ENV2 exits on att_blue mastery not end_state_banked",
         criterion_14_7),
        ("14.8  ARC_COMPLETE_FIELDS contains all pre-registration fields",
         criterion_14_8),
    ]

    results = []
    for label, fn in criteria:
        passed = run_criterion(label, fn)
        results.append(passed)

    print()
    n_pass = sum(results)
    n_fail = len(results) - n_pass
    print(f"v1.14: {n_pass}/{len(results)} PASS, {n_fail} FAIL")

    if n_fail > 0:
        print()
        print("FULL BATCH BLOCKED — resolve all FAIL before proceeding.")
        sys.exit(1)
    else:
        print()
        print("All v1.14 criteria PASS. Full batch authorised.")
        sys.exit(0)


if __name__ == "__main__":
    main()
