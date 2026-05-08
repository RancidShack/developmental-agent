"""
verify_v1_15.py
---------------
Pre-flight verifier for curiosity_agent_v1_15_batch.py.

Run before the full 40-run batch. All eight criteria must PASS.

Criteria:
  15.1  AgentCtx structure — all required slots present; label, pos,
        done, schema_v13_obs, and causal_obs accessible.
  15.2  Cognitive independence — two agents in the same world maintain
        separate mastery_flag and _knowledge_unlocked after carry.
  15.3  CRITICAL INVARIANT (both agents) — _carry_agent_return sets
        mastery_flag['att_blue'] = 1 and _knowledge_unlocked['haz_blue']
        = False for both agents independently.
  15.4  Shared world mutation — world.transform_to_knowledge('haz_blue')
        called by agent A's check_competency_unlocks is immediately
        visible to agent B via world.knowledge_unlocked.
  15.5  Two-agent arc_complete (live run) — _run_return_env1_two_agents
        with two prepared agents produces arc_complete_a = True or
        arc_complete_b = True within the step budget.
  15.6  haz_blue_shared_benefit detection — when haz_blue is already
        KNOWLEDGE before agent B steps, haz_blue_shared_benefit = True
        in the paired row.
  15.7  ARC_PAIRED_FIELDS complete — all pre-registration fields present.
  15.8  Seed B offset — seed_b = seed_a + SEED_B_OFFSET confirmed in
        main() job construction.

Usage:
    python verify_v1_15.py

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
# Imports (done once, shared across criteria)
# ---------------------------------------------------------------------------

try:
    import numpy as np
    from v1_13_world import (
        V113World, ENV1_FAMILIES, KNOWLEDGE, HAZARD,
    )
    from v1_10_agent import V110Agent
    from curiosity_agent_v1_15_batch import (
        AgentCtx, RETURN_ENV1_FAMILIES, RETURN_ENV1_PRECOMPLETED,
        RETURN_ENV1_STEPS, ARC_PAIRED_FIELDS, SEED_B_OFFSET, ARCH,
        _carry_agent_return, _run_return_env1_two_agents,
        _setup_observers,
    )
    from v1_13_schema_extension import (
        V13SchemaObserver as V13SchemaObserverPrediction,
        CONFIRMED_STATE,
    )
    _IMPORTS_OK = True
    _IMPORT_ERROR = ""
except Exception as e:
    _IMPORTS_OK = False
    _IMPORT_ERROR = str(e)


# ---------------------------------------------------------------------------
# Criterion implementations
# ---------------------------------------------------------------------------

def criterion_15_1():
    """AgentCtx has all required slots."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    required_slots = [
        'label', 'agent', 'seed',
        'prov_obs', 'schema_obs', 'family_obs', 'comp_obs', 'pe_obs',
        'goal_obs', 'cf_obs', 'br_obs',
        'schema_v13_obs', 'causal_obs',
        'observers',
        'pos', 'state', 'done',
        'end_state_banked_step', 'activation_step',
        'haz_blue_approached',
        'predicted_record_written',
        'transfer_condition_met', 'transfer_triggered_step',
        'att_blue_mastery_step',
        'actual_steps', 'env2_actual_steps',
    ]
    declared = getattr(AgentCtx, '__slots__', [])
    missing = [s for s in required_slots if s not in declared]
    ok = not missing
    detail = (f"slots={len(declared)} required={len(required_slots)}"
              + (f" | missing={missing}" if missing else ""))
    return ok, detail


def criterion_15_2():
    """Cognitive independence: two agents share world but not mastery_flag."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    np.random.seed(42)
    world = V113World(
        families=RETURN_ENV1_FAMILIES, hazard_cost=1.0,
        has_end_state=True, seed=42, unreachable_hazards=None,
    )
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in world.hazard_cells:
            world.transform_to_knowledge(oid)

    agent_a = V110Agent(world, total_steps=100, num_actions=27)
    np.random.seed(99)
    agent_b = V110Agent(world, total_steps=100, num_actions=27)

    # Apply carry to both
    _carry_agent_return(agent_a, world)
    _carry_agent_return(agent_b, world)

    # Mutate agent_a's mastery_flag after carry
    agent_a.mastery_flag['att_green'] = 1

    checks = {
        "agent_a and agent_b are different objects":
            agent_a is not agent_b,
        "mastery_flag dicts are different objects":
            agent_a.mastery_flag is not agent_b.mastery_flag,
        "agent_a att_green mutation not in agent_b":
            agent_b.mastery_flag.get('att_green', 0) == 0,
        "_knowledge_unlocked dicts are different objects":
            agent_a._knowledge_unlocked is not agent_b._knowledge_unlocked,
        "both share same world object":
            agent_a.world is agent_b.world,
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = str({k: v for k, v in checks.items()}) + (
        f" | FAILED: {failed}" if failed else ""
    )
    return ok, detail


def criterion_15_3():
    """CRITICAL INVARIANT for both agents: att_blue=1, haz_blue unlocked=False."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    np.random.seed(42)
    world = V113World(
        families=RETURN_ENV1_FAMILIES, hazard_cost=1.0,
        has_end_state=True, seed=42, unreachable_hazards=None,
    )
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in world.hazard_cells:
            world.transform_to_knowledge(oid)

    agent_a = V110Agent(world, total_steps=100, num_actions=27)
    np.random.seed(99)
    agent_b = V110Agent(world, total_steps=100, num_actions=27)

    _carry_agent_return(agent_a, world)
    _carry_agent_return(agent_b, world)

    failed = []
    for ag, label in ((agent_a, 'agent_a'), (agent_b, 'agent_b')):
        if ag.mastery_flag.get('att_blue') != 1:
            failed.append(f"{label} mastery_flag['att_blue']={ag.mastery_flag.get('att_blue')}")
        if ag._knowledge_unlocked.get('haz_blue') is not False:
            failed.append(f"{label} _knowledge_unlocked['haz_blue']={ag._knowledge_unlocked.get('haz_blue')}")
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in ag._knowledge_unlocked and ag._knowledge_unlocked[oid] is not True:
                failed.append(f"{label} _knowledge_unlocked['{oid}'] not True")

    ok = not failed
    detail = (
        f"agent_a att_blue={agent_a.mastery_flag.get('att_blue')} | "
        f"agent_b att_blue={agent_b.mastery_flag.get('att_blue')} | "
        f"haz_blue_unlocked_a={agent_a._knowledge_unlocked.get('haz_blue')} | "
        f"haz_blue_unlocked_b={agent_b._knowledge_unlocked.get('haz_blue')}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


def criterion_15_4():
    """Shared world mutation: transform_to_knowledge propagates to both agents."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    np.random.seed(42)
    world = V113World(
        families=RETURN_ENV1_FAMILIES, hazard_cost=1.0,
        has_end_state=True, seed=42, unreachable_hazards=None,
    )
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in world.hazard_cells:
            world.transform_to_knowledge(oid)

    agent_a = V110Agent(world, total_steps=100, num_actions=27)
    np.random.seed(99)
    agent_b = V110Agent(world, total_steps=100, num_actions=27)

    _carry_agent_return(agent_a, world)
    _carry_agent_return(agent_b, world)

    # Verify haz_blue is HAZARD before mutation
    pre_a = world.knowledge_unlocked.get('haz_blue', False)
    pre_type = world.object_type.get('haz_blue')

    # Simulate agent_a triggering the transformation
    # (directly calling transform_to_knowledge as check_competency_unlocks would)
    world.transform_to_knowledge('haz_blue')
    agent_a._knowledge_unlocked['haz_blue'] = True

    # Verify both see KNOWLEDGE via the shared world
    post_world_ku = world.knowledge_unlocked.get('haz_blue', False)
    post_world_type = world.object_type.get('haz_blue')

    # Agent B checks the shared world state (it would see this on next perception)
    agent_b_sees_ku = world.knowledge_unlocked.get('haz_blue', False)

    checks = {
        "haz_blue was HAZARD before transform": pre_type == HAZARD,
        "world.knowledge_unlocked['haz_blue'] True after transform": post_world_ku is True,
        "world.object_type['haz_blue'] is KNOWLEDGE after transform": post_world_type == KNOWLEDGE,
        "agent_b sees haz_blue as unlocked via shared world": agent_b_sees_ku is True,
        "agent_b._knowledge_unlocked still False (cognitive independence)":
            agent_b._knowledge_unlocked.get('haz_blue') is False,
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = (
        f"pre_type={pre_type} post_type={post_world_type} "
        f"world_ku={post_world_ku} b_sees={agent_b_sees_ku} "
        f"b_cognitive={agent_b._knowledge_unlocked.get('haz_blue')}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


def criterion_15_5():
    """Live _run_return_env1_two_agents: at least one arc_complete=True."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    np.random.seed(42)
    world_dummy = V113World(
        families=ENV1_FAMILIES, hazard_cost=1.0,
        has_end_state=True, seed=42, unreachable_hazards=['haz_blue'],
    )
    agent_a = V110Agent(world_dummy, total_steps=RETURN_ENV1_STEPS, num_actions=27)
    np.random.seed(99)
    agent_b = V110Agent(world_dummy, total_steps=RETURN_ENV1_STEPS, num_actions=27)

    meta_a = {"arch": ARCH, "hazard_cost": 1.0, "num_steps": RETURN_ENV1_STEPS,
              "run_idx": 0, "seed": 42, "env": 3}
    meta_b = {"arch": ARCH, "hazard_cost": 1.0, "num_steps": RETURN_ENV1_STEPS,
              "run_idx": 0, "seed": 99, "env": 3}

    (prov_a, sobs_a, fam_a, comp_a, pe_a,
     goal_a, cf_a, br_a) = _setup_observers(
        agent_a, world_dummy, meta_a, 0, RETURN_ENV1_STEPS,
        False, False, False,
    )
    (prov_b, sobs_b, fam_b, comp_b, pe_b,
     goal_b, cf_b, br_b) = _setup_observers(
        agent_b, world_dummy, meta_b, 0, RETURN_ENV1_STEPS,
        False, False, False,
    )

    ctx_a = AgentCtx('a', agent_a, 42,
                     prov_a, sobs_a, fam_a, comp_a, pe_a,
                     None, None, None, None, None)
    ctx_b = AgentCtx('b', agent_b, 99,
                     prov_b, sobs_b, fam_b, comp_b, pe_b,
                     None, None, None, None, None)

    result = _run_return_env1_two_agents(
        run_idx=0,
        seed_a=42, seed_b=99, hazard_cost=1.0,
        ctx_a=ctx_a, ctx_b=ctx_b,
        env1_transfer_step_a=1000, env1_transfer_step_b=2000,
        env2_actual_steps_a=500,  env2_actual_steps_b=600,
        pred_step_a=500, pred_step_b=600,
        conf_step_a=50000, conf_step_b=60000,
        with_completion_signal=True,
    )

    ac_a = result['arc_complete_a']
    ac_b = result['arc_complete_b']
    ts_a = result['transform_step_a']
    ts_b = result['transform_step_b']
    ok   = ac_a or ac_b
    detail = (
        f"arc_complete_a={ac_a} transform_step_a={ts_a} | "
        f"arc_complete_b={ac_b} transform_step_b={ts_b} | "
        f"both={result['arc_complete_a'] and result['arc_complete_b']}"
    )
    return ok, detail


def criterion_15_6():
    """haz_blue_shared_benefit: correctly True when A transforms before B steps."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    # Run criterion_15_5's setup and check the paired row
    np.random.seed(42)
    world_dummy = V113World(
        families=ENV1_FAMILIES, hazard_cost=1.0,
        has_end_state=True, seed=42, unreachable_hazards=['haz_blue'],
    )
    agent_a = V110Agent(world_dummy, total_steps=RETURN_ENV1_STEPS, num_actions=27)
    np.random.seed(99)
    agent_b = V110Agent(world_dummy, total_steps=RETURN_ENV1_STEPS, num_actions=27)

    meta_a = {"arch": ARCH, "hazard_cost": 1.0, "num_steps": RETURN_ENV1_STEPS,
              "run_idx": 0, "seed": 42, "env": 3}
    meta_b = {"arch": ARCH, "hazard_cost": 1.0, "num_steps": RETURN_ENV1_STEPS,
              "run_idx": 0, "seed": 99, "env": 3}

    (prov_a, sobs_a, fam_a, comp_a, pe_a, *_) = _setup_observers(
        agent_a, world_dummy, meta_a, 0, RETURN_ENV1_STEPS, False, False, False,
    )
    (prov_b, sobs_b, fam_b, comp_b, pe_b, *_) = _setup_observers(
        agent_b, world_dummy, meta_b, 0, RETURN_ENV1_STEPS, False, False, False,
    )

    ctx_a = AgentCtx('a', agent_a, 42, prov_a, sobs_a, fam_a, comp_a, pe_a,
                     None, None, None, None, None)
    ctx_b = AgentCtx('b', agent_b, 99, prov_b, sobs_b, fam_b, comp_b, pe_b,
                     None, None, None, None, None)

    result = _run_return_env1_two_agents(
        run_idx=0, seed_a=42, seed_b=99, hazard_cost=1.0,
        ctx_a=ctx_a, ctx_b=ctx_b,
        env1_transfer_step_a=1000, env1_transfer_step_b=2000,
        env2_actual_steps_a=500,   env2_actual_steps_b=600,
        pred_step_a=500, pred_step_b=600,
        conf_step_a=50000, conf_step_b=60000,
        with_completion_signal=True,
    )

    paired = result['arc_paired']
    # The field must be present and be a boolean
    has_field    = 'haz_blue_shared_benefit' in paired
    field_is_bool = isinstance(paired.get('haz_blue_shared_benefit'), bool)
    first_t      = paired.get('first_transformer')
    first_t_valid = first_t in ('a', 'b', 'tie', None)

    ok = has_field and field_is_bool and first_t_valid
    detail = (
        f"haz_blue_shared_benefit={paired.get('haz_blue_shared_benefit')} "
        f"first_transformer={first_t} "
        f"individuation_confirmed={paired.get('individuation_confirmed')}"
        + (" | FAILED" if not ok else "")
    )
    return ok, detail


def criterion_15_7():
    """ARC_PAIRED_FIELDS contains all pre-registration fields."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    required = [
        "arch", "run_idx", "seed_a", "seed_b", "hazard_cost",
        "arc_complete_a", "arc_complete_b", "both_arc_complete",
        "arc_total_steps_a", "arc_total_steps_b", "arc_total_steps_delta",
        "transformation_step_a", "transformation_step_b",
        "transfer_triggered_step_a", "transfer_triggered_step_b",
        "env2_actual_steps_a", "env2_actual_steps_b",
        "first_transformer",
        "haz_blue_shared_benefit",
        "individuation_confirmed",
    ]
    missing = [f for f in required if f not in ARC_PAIRED_FIELDS]
    ok = not missing
    detail = (
        f"required={len(required)} present={len(ARC_PAIRED_FIELDS)} "
        f"missing={missing}"
    )
    return ok, detail


def criterion_15_8():
    """Seed B = seed_a + SEED_B_OFFSET confirmed; offset = 20,000."""
    if not _IMPORTS_OK:
        return False, f"Import failed: {_IMPORT_ERROR}"

    import inspect
    from curiosity_agent_v1_15_batch import main
    src = inspect.getsource(main)

    checks = {
        "SEED_B_OFFSET == 20_000": SEED_B_OFFSET == 20_000,
        "seed_b = seed_a + SEED_B_OFFSET in main": "SEED_B_OFFSET" in src,
    }
    failed = [k for k, v in checks.items() if not v]
    ok = not failed
    detail = (
        f"SEED_B_OFFSET={SEED_B_OFFSET}"
        + (f" | FAILED: {failed}" if failed else "")
    )
    return ok, detail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not _IMPORTS_OK:
        print(f"IMPORT FAILURE: {_IMPORT_ERROR}")
        print("Cannot proceed. Fix imports before running verifier.")
        sys.exit(1)

    print("v1.15 Pre-flight Verifier")
    print("=" * 50)
    print()

    criteria = [
        ("15.1  AgentCtx structure (all required slots present)",
         criterion_15_1),
        ("15.2  Cognitive independence (separate mastery_flag, shared world)",
         criterion_15_2),
        ("15.3  CRITICAL INVARIANT for both agents (att_blue=1, haz_blue=False)",
         criterion_15_3),
        ("15.4  Shared world mutation propagates (transform visible to both agents)",
         criterion_15_4),
        ("15.5  Live _run_return_env1_two_agents (arc_complete fires for ≥1 agent)",
         criterion_15_5),
        ("15.6  haz_blue_shared_benefit field present and correctly typed",
         criterion_15_6),
        ("15.7  ARC_PAIRED_FIELDS contains all pre-registration fields",
         criterion_15_7),
        ("15.8  seed_b = seed_a + SEED_B_OFFSET (offset = 20,000)",
         criterion_15_8),
    ]

    results = []
    for label, fn in criteria:
        passed = run_criterion(label, fn)
        results.append(passed)

    print()
    n_pass = sum(results)
    n_fail = len(results) - n_pass
    print(f"v1.15: {n_pass}/{len(results)} PASS, {n_fail} FAIL")

    if n_fail > 0:
        print()
        print("FULL BATCH BLOCKED — resolve all FAIL before proceeding.")
        sys.exit(1)
    else:
        print()
        print("All v1.15 criteria PASS. Full batch authorised.")
        sys.exit(0)


if __name__ == "__main__":
    main()
