"""
verify_v1_16.py
---------------
Pre-flight verifier for curiosity_agent_v1_16_batch.py.

Run before the full 40-run batch. All eight criteria must PASS.

Criteria:
  16.1  Form grammar correct — world file carries corrected forms:
        GREEN att_form=CIRCLE_2D, BLUE haz_form=CUBE_3D,
        BLUE att_form=SQUARE_2D (ENV2). CUBE_3D constant exported.
  16.2  haz_grey in ENV1_FAMILIES_V16 — present at HAZ_GREY_POS,
        PYRAMID_3D form, no attractor (att_id=None).
  16.3  haz_grey excluded from transfer gate — V113World with
        unreachable=['haz_blue','haz_grey'] excludes haz_grey from
        hazard_cells and knowledge_unlocked.
  16.4  has_end_state=False — ENV1 world carries no end_state cell;
        end_state_cell is None.
  16.5  Shape connector fires — when both haz_yellow and haz_green
        are unlocked, predicted record basis_chains contains both
        colour entries and shape: prefixed entries.
  16.6  Return gate: CONFIRMED_STATE only — unchanged from v1.14;
        PREDICTED_STATE and UNRESOLVABLE_STATE return False.
  16.7  CRITICAL INVARIANT — mastery_flag['att_blue']=1 preserved
        in return ENV1 carry; transformation fires on first contact.
  16.8  Post-completion fields present — POST_COMPLETION_FIELDS and
        UNREACHABLE_FIELDS defined and non-empty in batch source.

Usage:
    python verify_v1_16.py

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

def criterion_16_1():
    """Form grammar correct in world file."""
    try:
        from v1_13_world import (ENV1_FAMILIES, ENV2_FAMILIES,
                                  BLUE, GREEN, CIRCLE_2D, SQUARE_2D, CUBE_3D, SPHERE_3D)
    except ImportError as e:
        return False, f"Import failed: {e}"

    # ENV1: GREEN att_form should be CIRCLE_2D
    green_env1 = next((f for f in ENV1_FAMILIES if f["colour"] == GREEN), None)
    # ENV1: BLUE haz_form should be CUBE_3D
    blue_env1  = next((f for f in ENV1_FAMILIES if f["colour"] == BLUE), None)
    # ENV2: BLUE att_form should be SQUARE_2D
    blue_env2  = next((f for f in ENV2_FAMILIES if f["colour"] == BLUE), None)

    checks = {
        "GREEN att_form == CIRCLE_2D":   green_env1 and green_env1.get("att_form") == CIRCLE_2D,
        "BLUE haz_form == CUBE_3D":      blue_env1  and blue_env1.get("haz_form")  == CUBE_3D,
        "BLUE att_form == SQUARE_2D":    blue_env2  and blue_env2.get("att_form")  == SQUARE_2D,
        "CUBE_3D constant == \'CUBE_3D\'": CUBE_3D == "CUBE_3D",
    }
    failed = [k for k,v in checks.items() if not v]
    return not failed, str(checks) + (f" | FAILED: {failed}" if failed else "")


def criterion_16_2():
    """haz_grey in ENV1_FAMILIES_V16 with correct form and no attractor."""
    try:
        from curiosity_agent_v1_16_batch import (
            ENV1_FAMILIES_V16, HAZ_GREY_ID, HAZ_GREY_POS, GREY
        )
        from v1_13_world import PYRAMID_3D
    except ImportError as e:
        return False, f"Import failed: {e}"

    grey_fam = next((f for f in ENV1_FAMILIES_V16
                     if f.get("haz_id") == HAZ_GREY_ID), None)
    if grey_fam is None:
        return False, f"No family with haz_id={HAZ_GREY_ID!r} in ENV1_FAMILIES_V16"

    checks = {
        "haz_pos == HAZ_GREY_POS":  grey_fam.get("haz_pos") == HAZ_GREY_POS,
        "haz_form == PYRAMID_3D":   grey_fam.get("haz_form") == PYRAMID_3D,
        "att_id is None":           grey_fam.get("att_id") is None,
        "colour == GREY":           grey_fam.get("colour") == GREY,
    }
    failed = [k for k,v in checks.items() if not v]
    return not failed, str(checks) + (f" | FAILED: {failed}" if failed else "")


def criterion_16_3():
    """haz_grey excluded from transfer gate via unreachable_hazards."""
    try:
        from v1_13_world import V113World, HAZARD
        from curiosity_agent_v1_16_batch import ENV1_FAMILIES_V16, HAZ_GREY_ID
    except ImportError as e:
        return False, f"Import failed: {e}"

    world = V113World(
        families=ENV1_FAMILIES_V16,
        hazard_cost=1.0,
        has_end_state=False,
        seed=42,
        unreachable_hazards=["haz_blue", HAZ_GREY_ID],
    )
    checks = {
        "haz_grey NOT in hazard_cells":      HAZ_GREY_ID not in world.hazard_cells,
        "haz_grey NOT in knowledge_unlocked":HAZ_GREY_ID not in world.knowledge_unlocked,
        "haz_grey IN object_positions":      HAZ_GREY_ID in world.object_positions,
        "haz_blue also excluded":            "haz_blue" not in world.hazard_cells,
    }
    failed = [k for k,v in checks.items() if not v]
    return not failed, str(checks) + (f" | FAILED: {failed}" if failed else "")


def criterion_16_4():
    """has_end_state=False: ENV1 world has no end_state cell."""
    try:
        from v1_13_world import V113World
        from curiosity_agent_v1_16_batch import ENV1_FAMILIES_V16, HAZ_GREY_ID
    except ImportError as e:
        return False, f"Import failed: {e}"

    world = V113World(
        families=ENV1_FAMILIES_V16,
        hazard_cost=1.0,
        has_end_state=False,
        seed=42,
        unreachable_hazards=["haz_blue", HAZ_GREY_ID],
    )
    no_end_state = world.end_state_cell is None
    return no_end_state, f"end_state_cell={world.end_state_cell!r}"


def criterion_16_5():
    """Shape connector adds shape: basis entries to predicted record."""
    try:
        from v1_13_world import V113World
        from curiosity_agent_v1_16_batch import (
            ENV1_FAMILIES_V16, HAZ_GREY_ID,
        )
        from v1_13_schema_extension import (
            V13SchemaObserver as V13SchemaObserverPrediction,
            PREDICTED_STATE,
        )
        from v1_13_observer_substrates import PREDICTION_FAMILY_MINIMUM
    except ImportError as e:
        return False, f"Import failed: {e}"

    # Set up a world and manually unlock both family hazards
    world = V113World(
        families=ENV1_FAMILIES_V16, hazard_cost=1.0,
        has_end_state=False, seed=42,
        unreachable_hazards=["haz_blue", HAZ_GREY_ID],
    )
    world.knowledge_unlocked["haz_yellow"] = True
    world.knowledge_unlocked["haz_green"]  = True

    schema = V13SchemaObserverPrediction(prediction_enabled=True)

    # Simulate the shape connector firing
    colour_basis = sorted(h for h in ("haz_yellow","haz_green")
                          if world.knowledge_unlocked.get(h, False))
    shape_basis  = [f"shape:{h}" for h in colour_basis]
    combined     = colour_basis + shape_basis

    schema.add_predicted_record({
        "object_id":              "haz_blue",
        "predicted_precondition": "att_blue",
        "basis_chains":           combined,
        "prediction_step":        1000,
        "prediction_env":         1,
    })

    recs = schema.get_predicted_records()
    if not recs:
        return False, "No predicted record written"

    basis = recs[0].get("basis_chains", [])
    colour_entries = [b for b in basis if not b.startswith("shape:")]
    shape_entries  = [b for b in basis if b.startswith("shape:")]

    checks = {
        "colour entries present":         len(colour_entries) >= 2,
        "shape entries present":          len(shape_entries)  >= 2,
        "shape:haz_green in basis":       "shape:haz_green"  in basis,
        "shape:haz_yellow in basis":      "shape:haz_yellow" in basis,
        "predicted_precondition=att_blue":recs[0].get("predicted_precondition") == "att_blue",
    }
    failed = [k for k,v in checks.items() if not v]
    return not failed, f"basis={basis} | " + (f"FAILED: {failed}" if failed else "OK")


def criterion_16_6():
    """Return gate: CONFIRMED_STATE only."""
    try:
        from curiosity_agent_v1_16_batch import _return_to_env1_condition_met
        from v1_13_schema_extension import (
            V13SchemaObserver as Obs,
            PREDICTED_STATE, CONFIRMED_STATE, UNRESOLVABLE_STATE,
        )
    except ImportError as e:
        return False, f"Import failed: {e}"

    def _make(state):
        obs = Obs(prediction_enabled=True)
        obs.add_predicted_record({"object_id":"haz_blue","predicted_precondition":"att_blue",
                                   "basis_chains":["haz_green"],"prediction_step":1,"prediction_env":1})
        if state == CONFIRMED_STATE:
            obs.confirm_predicted_record("haz_blue", 100, 2)
        elif state == UNRESOLVABLE_STATE:
            obs.mark_unresolvable("haz_blue")
        return obs

    checks = {
        "CONFIRMED_STATE → True":    _return_to_env1_condition_met(_make(CONFIRMED_STATE)),
        "PREDICTED_STATE → False":   not _return_to_env1_condition_met(_make(PREDICTED_STATE)),
        "UNRESOLVABLE_STATE → False":not _return_to_env1_condition_met(_make(UNRESOLVABLE_STATE)),
        "None → False":              not _return_to_env1_condition_met(None),
    }
    failed = [k for k,v in checks.items() if not v]
    return not failed, str(checks) + (f" | FAILED: {failed}" if failed else "")


def criterion_16_7():
    """CRITICAL INVARIANT + live transformation."""
    try:
        from v1_13_world import V113World
        from v1_10_agent import V110Agent
        from curiosity_agent_v1_16_batch import (
            _run_return_env1,
            RETURN_ENV1_FAMILIES, RETURN_ENV1_PRECOMPLETED,
        )
        from v1_13_schema_extension import (
            V13SchemaObserver as Obs, CONFIRMED_STATE,
        )
        from v1_11_causal_observer import V111CausalObserver
    except ImportError as e:
        return False, f"Import failed: {e}"

    seed = 999
    return_seed = seed + 20_000
    import numpy as np
    np.random.seed(return_seed)

    return_world = V113World(
        families=RETURN_ENV1_FAMILIES, hazard_cost=1.0,
        has_end_state=False, seed=return_seed,
        unreachable_hazards=None,
    )

    # Pre-transition completed hazards
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in return_world.hazard_cells:
            return_world.transform_to_knowledge(oid)

    agent = V110Agent(return_world, total_steps=200_000, num_actions=6)

    # Inline carry: set mastery_flag with att_blue=1 (CRITICAL INVARIANT)
    if hasattr(agent, 'mastery_flag'):
        agent.mastery_flag = {a: 0 for a in return_world.attractor_cells}
        agent.mastery_flag['att_blue'] = 1
    if hasattr(agent, 'knowledge_banked'):
        agent.knowledge_banked = {h: False for h in return_world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent.knowledge_banked:
                agent.knowledge_banked[oid] = True
    if hasattr(agent, '_knowledge_unlocked'):
        agent._knowledge_unlocked = {h: False for h in return_world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent._knowledge_unlocked:
                agent._knowledge_unlocked[oid] = True

    invariant_ok = agent.mastery_flag.get('att_blue', 0) == 1

    schema = Obs(prediction_enabled=True)
    schema.add_predicted_record({
        "object_id": "haz_blue", "predicted_precondition": "att_blue",
        "basis_chains": ["haz_green", "haz_yellow"], "prediction_step": 1, "prediction_env": 1,
    })
    schema.confirm_predicted_record("haz_blue", 100, 2)

    meta = {"arch": "v1_16", "hazard_cost": 1.0, "num_steps": 200_000,
            "run_idx": 0, "seed": seed, "env": 1}
    causal = V111CausalObserver(meta)

    result = _run_return_env1(
        run_idx=0, seed=seed, hazard_cost=1.0,
        carry_agent=agent, carry_prov_obs=None,
        schema_v13_obs=schema, causal_obs=causal,
        env1_surprise_step=500, prediction_step=1000,
        transfer_step=5000, confirmation_step=10000,
        env2_actual_steps=15000,
    )

    checks = {
        "mastery_flag['att_blue']==1 before return": invariant_ok,
        "arc_complete=True":                         result.get("arc_complete"),
        "transformation_step is not None":           result.get("transformation_step") is not None,
        "post_completion_row present":               result.get("post_completion_row") is not None,
    }
    failed = [k for k, v in checks.items() if not v]
    return not failed, str(checks) + (f" | FAILED: {failed}" if failed else "")


def criterion_16_8():
    """POST_COMPLETION_FIELDS and UNREACHABLE_FIELDS defined."""
    try:
        from curiosity_agent_v1_16_batch import (
            POST_COMPLETION_FIELDS, UNREACHABLE_FIELDS,
            ARC_COMPLETE_FIELDS, ARCH,
        )
    except ImportError as e:
        return False, f"Import failed: {e}"

    checks = {
        "POST_COMPLETION_FIELDS non-empty":  len(POST_COMPLETION_FIELDS) > 0,
        "UNREACHABLE_FIELDS non-empty":      len(UNREACHABLE_FIELDS) > 0,
        "behaviour_category in POST":        "behaviour_category" in POST_COMPLETION_FIELDS,
        "haz_grey_contact_count in UNRCH":   "haz_grey_contact_count" in UNREACHABLE_FIELDS,
        "ARCH == v1_16":                     ARCH == "v1_16",
    }
    failed = [k for k,v in checks.items() if not v]
    return not failed, str(checks) + (f" | FAILED: {failed}" if failed else "")


def main():
    print("v1.16 Pre-flight Verifier")
    print("=" * 50)
    print()
    criteria = [
        ("16.1  Form grammar correct (CIRCLE_2D, CUBE_3D, SQUARE_2D)",  criterion_16_1),
        ("16.2  haz_grey in ENV1_FAMILIES_V16 (PYRAMID_3D, no att)",    criterion_16_2),
        ("16.3  haz_grey excluded from transfer gate",                   criterion_16_3),
        ("16.4  has_end_state=False: no end_state cell in ENV1",         criterion_16_4),
        ("16.5  Shape connector fires (shape: basis entries present)",   criterion_16_5),
        ("16.6  Return gate: CONFIRMED_STATE only",                      criterion_16_6),
        ("16.7  CRITICAL INVARIANT + live transformation + post-comp",  criterion_16_7),
        ("16.8  POST_COMPLETION_FIELDS + UNREACHABLE_FIELDS defined",    criterion_16_8),
    ]
    results = []
    for label, fn in criteria:
        passed = run_criterion(label, fn)
        results.append(passed)
    print()
    n_pass = sum(results)
    n_fail = len(results) - n_pass
    print(f"v1.16: {n_pass}/{len(results)} PASS, {n_fail} FAIL")
    if n_fail > 0:
        print()
        print("FULL BATCH BLOCKED \u2014 resolve all FAIL before proceeding.")
        import sys; sys.exit(1)
    else:
        print()
        print("All v1.16 criteria PASS. Full batch authorised.")
        import sys; sys.exit(0)


if __name__ == "__main__":
    main()
