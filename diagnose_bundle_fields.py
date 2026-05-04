"""
diagnose_bundle_fields.py
--------------------------
v1.11 pre-implementation diagnostic.

Confirms the exact field names, record types, and sample record
structures for all five SubstrateBundle fields that V111CausalObserver
will read from:

  bundle.provenance        — formation records (ProvenanceRecord dataclass)
  bundle.prediction_error  — PE encounter records (list of dicts)
  bundle.counterfactual    — suppressed-approach records (list of dicts)
  bundle.goal              — goal records (dict with nested lists)
  bundle.belief_revision   — revised_expectation records (list of dicts)

MOTIVATION
v1.10 consumed all three amendments on interface mismatches in a single
function (on_end_state_banked): self._agent vs self.agent, self.flags
vs self.records, dict vs ProvenanceRecord dataclass. This diagnostic
runs before any V111CausalObserver code is written and confirms the
exact interface the causal observer will depend on.

Usage:
    python diagnose_bundle_fields.py

Runs one verification run at cost=1.0, 80,000 steps and prints the
full field inventory for each substrate field.

EXIT 0: diagnostic complete; field inventory printed.
EXIT 1: import error or run failure.
"""

import sys
import traceback
import pprint
import numpy as np

# v1.10 patches applied first
try:
    import v1_10_observer_substrates  # noqa: F401
    from v1_10_observer_substrates import build_bundle_from_observers
except ImportError as e:
    print(f"ERROR: could not import v1_10_observer_substrates: {e}")
    sys.exit(1)

try:
    from curiosity_agent_v1_7_world import (
        V17World, NUM_ACTIONS,
        FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ
    )
    from v1_10_agent                    import V110Agent
    from v1_1_provenance                import V1ProvenanceStore
    from v1_3_schema_extension          import V13SchemaObserver
    from v1_3_family_observer           import V13FamilyObserver
    from v1_4_comparison_observer       import V14ComparisonObserver
    from v1_5_prediction_error_observer import V15PredictionErrorObserver
    from v1_6_reporting_layer           import V16ReportingLayer
    from v1_8_goal_layer                import V18GoalObserver, assign_goal
    from v1_9_counterfactual_observer   import V19CounterfactualObserver
    from v1_10_belief_revision_observer import V110BeliefRevisionObserver
except ImportError as e:
    print(f"ERROR: import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

DIAG_SEED  = 42
DIAG_COST  = 1.0
DIAG_STEPS = 80_000
DIAG_RUN   = 0


def _section(title):
    print()
    print("=" * 65)
    print(f"  {title}")
    print("=" * 65)


def _subsection(title):
    print()
    print(f"  --- {title} ---")


def run_diagnostic():
    np.random.seed(DIAG_SEED)

    world = V17World(hazard_cost=DIAG_COST, seed=DIAG_SEED)
    agent = V110Agent(world, total_steps=DIAG_STEPS, num_actions=NUM_ACTIONS)

    meta = {
        "arch":        "v1_11_diag",
        "hazard_cost": DIAG_COST,
        "num_steps":   DIAG_STEPS,
        "run_idx":     DIAG_RUN,
        "seed":        DIAG_SEED,
    }

    ctc = {
        "FRAME": FRAME, "NEUTRAL": NEUTRAL, "HAZARD": HAZARD,
        "ATTRACTOR": ATTRACTOR, "END_STATE": END_STATE,
        "KNOWLEDGE": KNOWLEDGE, "DIST_OBJ": DIST_OBJ,
    }

    prov_obs   = V1ProvenanceStore(agent, world, meta, ctc)
    schema_obs = V13SchemaObserver(agent, world, meta)
    family_obs = V13FamilyObserver(agent, world, meta,
                                   provenance_store=prov_obs)
    comp_obs   = V14ComparisonObserver(family_obs, meta)
    pe_obs     = V15PredictionErrorObserver(agent, world, meta)

    goal_type, target_id, step_budget = assign_goal(DIAG_RUN, DIAG_STEPS)
    goal_obs = V18GoalObserver(
        agent, world, meta, goal_type, target_id, step_budget
    )
    cf_obs = V19CounterfactualObserver(agent, world, meta, goal_obs=goal_obs)
    br_obs = V110BeliefRevisionObserver(
        agent, world, meta,
        prediction_error_obs=pe_obs,
        provenance_obs=prov_obs,
        counterfactual_obs=cf_obs,
    )

    observers = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs,
                 goal_obs, cf_obs, br_obs]

    state = world.observe()
    end_state_banked_step = None

    for step in range(DIAG_STEPS):
        for obs in observers:
            obs.on_pre_action(step)

        action = agent.choose_action(state)
        obs_next, contact_oid, moved, cost = world.step(action)
        agent.record_action_outcome(
            contact_oid, moved or contact_oid is not None, cost, world, step
        )

        for obs in observers:
            obs.on_post_event(step)

        intrinsic = (
            agent.novelty_reward(state)
            + agent.preference_reward(state)
            + agent.feature_reward(state)
            + agent.end_state_draw_reward(state, obs_next)
        )

        agent_pos     = getattr(world, 'agent_pos', None)
        obj_positions = getattr(world, 'object_positions', {})
        for bias_oid in br_obs.active_biased_objects(step):
            obj_pos = obj_positions.get(bias_oid)
            if obj_pos is not None and agent_pos is not None:
                intrinsic += br_obs.preference_bias_reward(
                    bias_oid, step, moving_closer=True
                )

        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)
        state = obs_next

        if (end_state_banked_step is None
                and getattr(agent, 'end_state_banked', False)):
            prov_obs.on_end_state_banked(step)
            end_state_banked_step = step

    for obs in observers:
        obs.on_run_end(DIAG_STEPS)

    bundle = build_bundle_from_observers(
        provenance_obs=prov_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comparison_obs=comp_obs,
        prediction_error_obs=pe_obs,
        run_meta=meta,
        goal_obs=goal_obs,
        counterfactual_obs=cf_obs,
        belief_revision_obs=br_obs,
    )

    pe_records = getattr(bundle, 'prediction_error', None) or []
    br_obs.process_pe_substrate(pe_records)
    bundle.belief_revision = br_obs.get_substrate()

    # -----------------------------------------------------------------------
    # FIELD INVENTORY
    # -----------------------------------------------------------------------

    _section("DIAGNOSTIC: SubstrateBundle field inventory for V111CausalObserver")
    print(f"  Seed={DIAG_SEED}  cost={DIAG_COST}  steps={DIAG_STEPS}")

    # -------------------------------------------------------------------
    # 1. bundle.provenance
    # -------------------------------------------------------------------
    _section("1. bundle.provenance")

    prov = getattr(bundle, 'provenance', None)
    print(f"  type(bundle.provenance): {type(prov)}")

    if prov is None:
        print("  WARNING: bundle.provenance is None")
    elif isinstance(prov, dict):
        print(f"  len(bundle.provenance): {len(prov)}")
        _subsection("Key types")
        key_types = set(type(k).__name__ for k in prov.keys())
        print(f"  Key types: {key_types}")
        _subsection("Sample keys (first 5)")
        for k in list(prov.keys())[:5]:
            print(f"    {k!r}")
        _subsection("Sample record (first entry)")
        for k, v in list(prov.items())[:1]:
            print(f"  Key: {k!r}")
            print(f"  Value type: {type(v).__name__}")
            if hasattr(v, '__dataclass_fields__'):
                print(f"  Dataclass fields: {list(v.__dataclass_fields__.keys())}")
                for field_name in v.__dataclass_fields__:
                    print(f"    .{field_name} = {getattr(v, field_name)!r}")
            elif isinstance(v, dict):
                print(f"  Dict keys: {list(v.keys())}")
                for dk, dv in v.items():
                    print(f"    [{dk!r}] = {dv!r}")
            else:
                print(f"  Value: {v!r}")
    else:
        print(f"  Unexpected type: {type(prov)}")

    # environment_complete record specifically
    _subsection("environment_complete record (if present)")
    ec_key = "environment_complete:end_state"
    if isinstance(prov, dict):
        ec_rec = prov.get(ec_key)
        if ec_rec is not None:
            print(f"  FOUND: {ec_key!r}")
            if hasattr(ec_rec, '__dataclass_fields__'):
                for fn in ec_rec.__dataclass_fields__:
                    print(f"    .{fn} = {getattr(ec_rec, fn)!r}")
        else:
            print(f"  Not present (end_state not banked in this run, or key differs)")
            print(f"  Keys containing 'environment': "
                  f"{[k for k in prov.keys() if 'environment' in str(k)]}")

    # ProvenanceStore direct attributes
    _subsection("V1ProvenanceStore direct attributes")
    print(f"  type(prov_obs): {type(prov_obs).__name__}")
    print(f"  hasattr(prov_obs, 'agent'): {hasattr(prov_obs, 'agent')}")
    print(f"  hasattr(prov_obs, '_agent'): {hasattr(prov_obs, '_agent')}")
    print(f"  hasattr(prov_obs, 'records'): {hasattr(prov_obs, 'records')}")
    print(f"  hasattr(prov_obs, 'flags'): {hasattr(prov_obs, 'flags')}")
    if hasattr(prov_obs, 'records'):
        print(f"  type(prov_obs.records): {type(prov_obs.records).__name__}")
        print(f"  len(prov_obs.records): {len(prov_obs.records)}")

    # -------------------------------------------------------------------
    # 2. bundle.prediction_error
    # -------------------------------------------------------------------
    _section("2. bundle.prediction_error")

    pe = getattr(bundle, 'prediction_error', None)
    print(f"  type(bundle.prediction_error): {type(pe)}")

    if pe is None:
        print("  WARNING: bundle.prediction_error is None")
    elif isinstance(pe, list):
        print(f"  len(bundle.prediction_error): {len(pe)}")
        if pe:
            _subsection("First PE record — all fields")
            rec = pe[0]
            print(f"  type: {type(rec).__name__}")
            if isinstance(rec, dict):
                for k, v in rec.items():
                    print(f"    [{k!r}] = {v!r}")
            elif hasattr(rec, '__dataclass_fields__'):
                for fn in rec.__dataclass_fields__:
                    print(f"    .{fn} = {getattr(rec, fn)!r}")

            _subsection("PE records with precondition_met=False (pre-transition)")
            pre_trans = [r for r in pe
                         if isinstance(r, dict) and not r.get('precondition_met', True)]
            print(f"  Count: {len(pre_trans)}")
            if pre_trans:
                r = pre_trans[0]
                print("  First pre-transition record:")
                for k, v in r.items():
                    print(f"    [{k!r}] = {v!r}")

            _subsection("PE records with transformed_at_step not None (resolved)")
            resolved = [r for r in pe
                        if isinstance(r, dict)
                        and r.get('transformed_at_step') is not None
                        and not r.get('precondition_met', True)]
            print(f"  Resolved surprises: {len(resolved)}")
            if resolved:
                r = resolved[0]
                print("  First resolved surprise:")
                for k, v in r.items():
                    print(f"    [{k!r}] = {v!r}")
        else:
            print("  Empty list (no PE events in this run)")
    else:
        print(f"  Unexpected type: {type(pe)}")

    # -------------------------------------------------------------------
    # 3. bundle.counterfactual
    # -------------------------------------------------------------------
    _section("3. bundle.counterfactual")

    cf = getattr(bundle, 'counterfactual', None)
    print(f"  type(bundle.counterfactual): {type(cf)}")

    if cf is None:
        print("  WARNING: bundle.counterfactual is None")
    elif isinstance(cf, list):
        print(f"  len(bundle.counterfactual): {len(cf)}")
        if cf:
            _subsection("First CF record — all fields")
            rec = cf[0]
            if isinstance(rec, dict):
                for k, v in rec.items():
                    print(f"    [{k!r}] = {v!r}")
        else:
            print("  Empty list")
    else:
        print(f"  Unexpected type: {type(cf)}")

    # -------------------------------------------------------------------
    # 4. bundle.goal
    # -------------------------------------------------------------------
    _section("4. bundle.goal")

    goal_sub = getattr(bundle, 'goal', None)
    print(f"  type(bundle.goal): {type(goal_sub)}")

    if goal_sub is None:
        print("  WARNING: bundle.goal is None")
    elif isinstance(goal_sub, dict):
        print(f"  Top-level keys: {list(goal_sub.keys())}")
        for top_k, top_v in goal_sub.items():
            print(f"  [{top_k!r}]: type={type(top_v).__name__}", end="")
            if isinstance(top_v, list):
                print(f", len={len(top_v)}")
                if top_v:
                    first = top_v[0]
                    if isinstance(first, dict):
                        print(f"    First item keys: {list(first.keys())}")
            elif isinstance(top_v, dict):
                print(f", keys={list(top_v.keys())}")
            else:
                print(f", value={top_v!r}")
    else:
        print(f"  Unexpected type: {type(goal_sub)}")

    # -------------------------------------------------------------------
    # 5. bundle.belief_revision
    # -------------------------------------------------------------------
    _section("5. bundle.belief_revision")

    br = getattr(bundle, 'belief_revision', None)
    print(f"  type(bundle.belief_revision): {type(br)}")

    if br is None:
        print("  WARNING: bundle.belief_revision is None")
    elif isinstance(br, list):
        print(f"  len(bundle.belief_revision): {len(br)}")
        if br:
            _subsection("First BR record — all fields")
            rec = br[0]
            if isinstance(rec, dict):
                for k, v in rec.items():
                    print(f"    [{k!r}] = {v!r}")
        else:
            print("  Empty list (no resolved surprises in this run)")
    else:
        print(f"  Unexpected type: {type(br)}")

    # -------------------------------------------------------------------
    # 6. bundle.schema
    # -------------------------------------------------------------------
    _section("6. bundle.schema (for precondition lookup)")

    schema = getattr(bundle, 'schema', None)
    print(f"  type(bundle.schema): {type(schema)}")

    if schema is None:
        print("  WARNING: bundle.schema is None")
    elif isinstance(schema, dict):
        print(f"  Top-level keys: {list(schema.keys())}")
        _subsection("Family precondition structure (if present)")
        # Look for family or precondition keys
        for k in schema.keys():
            if 'family' in str(k).lower() or 'precond' in str(k).lower():
                print(f"  [{k!r}]: {schema[k]!r}")
        _subsection("Full schema (truncated to 20 keys)")
        for k, v in list(schema.items())[:20]:
            print(f"  [{k!r}]: {v!r}")
    else:
        print(f"  Unexpected type: {type(schema)}")

    # -------------------------------------------------------------------
    # 7. bundle.resolve() interface
    # -------------------------------------------------------------------
    _section("7. bundle.resolve() interface check")

    source_types = [
        "provenance", "prediction_error", "counterfactual",
        "goal", "belief_revision", "schema", "family",
    ]
    for st in source_types:
        try:
            result = bundle.resolve(st, "test_key_that_does_not_exist")
            print(f"  resolve({st!r}, ...) → {result!r}")
        except Exception as e:
            print(f"  resolve({st!r}, ...) → ERROR: {e}")

    # -------------------------------------------------------------------
    # 8. Summary
    # -------------------------------------------------------------------
    _section("SUMMARY: fields V111CausalObserver will read")

    fields_ok = True

    checks = [
        ("bundle.provenance",        prov,      "dict"),
        ("bundle.prediction_error",  pe,        "list"),
        ("bundle.counterfactual",    cf,        "list"),
        ("bundle.goal",              goal_sub,  "dict"),
        ("bundle.belief_revision",   br,        "list"),
        ("bundle.schema",            schema,    "dict"),
    ]

    for name, value, expected_type in checks:
        actual_type = type(value).__name__ if value is not None else "None"
        ok = (value is not None) and (actual_type == expected_type)
        status = "OK " if ok else "WARN"
        if not ok:
            fields_ok = False
        print(f"  [{status}] {name}: {actual_type} "
              f"(expected {expected_type})")

    print()
    if fields_ok:
        print("  All fields present and typed as expected.")
        print("  Safe to write V111CausalObserver.")
    else:
        print("  WARNING: one or more fields missing or mistyped.")
        print("  Resolve before writing V111CausalObserver.")

    return 0 if fields_ok else 1


if __name__ == "__main__":
    try:
        sys.exit(run_diagnostic())
    except Exception as e:
        print(f"\nFATAL: {e}")
        traceback.print_exc()
        sys.exit(1)
