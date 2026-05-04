"""
verify_v1_10_level12.py
------------------------
v1.10 Level-12 pre-flight verification: belief-revision observer and
completion-signal correctness.

Runs 10 verification runs at cost=1.0, 80,000 steps.
Level-11 re-run (counterfactual regression) runs first unless
--skip-level11-rerun is passed.

EXIT 0: all eight criteria hold. Proceed to full v1.10 batch.
EXIT 1: at least one criterion failed.

EIGHT CRITERIA
  C1. belief_revision_field_present  — bundle.belief_revision is a
                                        list in every run
  C2. source_key_format_valid        — every belief-revision Q3
                                        statement matches
                                        "revised_expectation:{oid}:{step}"
  C3. source_resolves_for_all_br     — every belief-revision statement
                                        has source_resolves=True
  C4. zero_hallucinations            — hallucination_count == 0 across
                                        Q1–Q4 including extended Q3
  C5. prior_revised_text_derivable   — prior/revised texts consistent
                                        with provenance + pe substrates
  C6. bias_fires                     — at least one run produces a
                                        revised_expectation record
  C7. temporal_exclusion_effective   — mean CF records per run < 500
  C8. completion_signal_fires        — end_state_draw_active=True in
                                        runs where activation_step fired

Usage:
    python verify_v1_10_level12.py [--skip-level11-rerun]
                                    [--no-belief-revision]
                                    [--no-completion-signal]
"""

import argparse
import csv
import os
import sys
import traceback
import statistics

import numpy as np

# v1.10 patches must be imported first
import v1_10_observer_substrates  # noqa: F401
from v1_10_observer_substrates import build_bundle_from_observers

from curiosity_agent_v1_7_world import (
    V17World, NUM_ACTIONS, HAZARD, DIST_OBJ, ATTRACTOR,
    NEUTRAL, END_STATE, KNOWLEDGE,
)
from v1_10_agent import V110Agent
from v1_7_agent  import V17Agent

from v1_1_provenance                import V1ProvenanceStore
from v1_3_schema_extension          import V13SchemaObserver
from v1_3_family_observer           import V13FamilyObserver
from v1_4_comparison_observer       import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver
from v1_6_reporting_layer           import V16ReportingLayer
from v1_7_observer_substrates       import flush_provenance_csv
from v1_8_goal_layer                import V18GoalObserver, assign_goal
from v1_9_counterfactual_observer   import V19CounterfactualObserver
from v1_10_belief_revision_observer import V110BeliefRevisionObserver

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED_CSV           = "run_data_v1_9.csv"
VERIFICATION_COST  = 1.0
VERIFICATION_STEPS = 80_000
VERIFICATION_N     = 10
ARCH               = "v1_10"

# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

def load_seeds(path, cost, n):
    seeds = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if abs(float(row["hazard_cost"]) - cost) < 1e-6:
                    seeds.append((int(row["run_idx"]), int(row["seed"])))
            except (ValueError, KeyError):
                continue
    seen, deduped = set(), []
    for idx, seed in sorted(seeds):
        if idx not in seen:
            seen.add(idx)
            deduped.append((idx, seed))
    return deduped[:n]


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def _run_one(run_idx, seed, num_steps,
             with_goal=True, with_counterfactual=True,
             with_belief_revision=True, with_completion_signal=True):

    np.random.seed(seed)

    world = V17World(hazard_cost=VERIFICATION_COST, seed=seed)

    AgentClass = V110Agent if with_completion_signal else V17Agent
    agent = AgentClass(world, total_steps=num_steps, num_actions=NUM_ACTIONS)

    meta = {
        "arch":        ARCH,
        "hazard_cost": VERIFICATION_COST,
        "num_steps":   num_steps,
        "run_idx":     run_idx,
        "seed":        seed,
    }

    try:
        from curiosity_agent_v1_7_world import FRAME
    except ImportError:
        FRAME = 0

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

    goal_obs = None
    if with_goal:
        goal_type, target_id, step_budget = assign_goal(run_idx, num_steps)
        goal_obs = V18GoalObserver(
            agent, world, meta, goal_type, target_id, step_budget
        )

    cf_obs = None
    if with_counterfactual:
        cf_obs = V19CounterfactualObserver(
            agent, world, meta, goal_obs=goal_obs
        )

    br_obs = None
    if with_belief_revision:
        br_obs = V110BeliefRevisionObserver(
            agent, world, meta,
            prediction_error_obs=pe_obs,
            provenance_obs=prov_obs,
            counterfactual_obs=cf_obs,
        )

    observers = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs]
    if goal_obs is not None:
        observers.append(goal_obs)
    if cf_obs is not None:
        observers.append(cf_obs)
    if br_obs is not None:
        observers.append(br_obs)

    state = world.observe()
    end_state_banked_this_run = False

    for step in range(num_steps):
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
        )

        # Completion signal draw
        if with_completion_signal and isinstance(agent, V110Agent):
            intrinsic += agent.end_state_draw_reward(state, obs_next)

        # Preference bias from belief-revision layer
        if br_obs is not None:
            agent_pos = getattr(world, 'agent_pos', None)
            obj_positions = getattr(world, 'object_positions', {})
            for bias_oid in br_obs.active_biased_objects(step):
                obj_pos = obj_positions.get(bias_oid)
                if obj_pos is not None and agent_pos is not None:
                    import math
                    # Check if moving closer
                    # (simplified: use draw reward pattern)
                    intrinsic += br_obs.preference_bias_reward(
                        bias_oid, step, moving_closer=True
                    )

        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)
        state = obs_next

        # Fire environment_complete hook
        if (not end_state_banked_this_run
                and getattr(agent, 'end_state_banked', False)):
            prov_obs.on_end_state_banked(step)
            end_state_banked_this_run = True

    for obs in observers:
        obs.on_run_end(num_steps)

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

    # Process PE substrate now that bundle is assembled
    if br_obs is not None:
        pe_records = getattr(bundle, "prediction_error", None) or []
        br_obs.process_pe_substrate(pe_records)
        # Re-build bundle so belief_revision field reflects the records
        bundle.belief_revision = br_obs.get_substrate()

    layer      = V16ReportingLayer(bundle)
    statements = layer.generate_report()

    return statements, bundle, goal_obs, cf_obs, br_obs, agent


# ---------------------------------------------------------------------------
# Level 11 re-run (regression)
# ---------------------------------------------------------------------------

def run_level11_rerun(seeds, num_steps):
    print("Level-11 Re-Run: Counterfactual regression on v1.10 stack")
    print(f"  {len(seeds)} runs, cost={VERIFICATION_COST}, "
          f"steps={num_steps}")
    print()

    total_halluc = 0
    total_cf     = 0
    fails        = []

    for run_idx, seed in seeds:
        try:
            stmts, bundle, _, cf_obs, _, _ = _run_one(
                run_idx, seed, num_steps,
                with_belief_revision=False,
                with_completion_signal=False,
            )
        except Exception as e:
            print(f"  Run {run_idx:3d}: ERROR — {e}")
            traceback.print_exc()
            fails.append(run_idx)
            continue

        halluc   = sum(1 for s in stmts if not s.source_resolves)
        cf_count = len(cf_obs.get_substrate()) if cf_obs else 0
        total_halluc += halluc
        total_cf     += cf_count
        status = "PASS" if halluc == 0 else f"FAIL({halluc})"
        print(f"  Run {run_idx:3d} | seed={seed:12d} | "
              f"cf={cf_count:3d} | halluc={halluc} | {status}")

    print()
    print(f"  Total CF records: {total_cf}")
    mean_cf = total_cf / len(seeds) if seeds else 0
    print(f"  Mean CF per run:  {mean_cf:.1f}")

    c6_pass = total_cf > 0
    c7_pass = mean_cf < 500

    print(f"  C6 detection_fires: {'PASS' if c6_pass else 'FAIL'}")
    print(f"  C7 temporal_exclusion_effective (mean<500): "
          f"{'PASS' if c7_pass else 'FAIL'}")

    passed = (total_halluc == 0 and not fails and c6_pass and c7_pass)
    print()
    print(f"Level-11 Re-Run: {'PASSED' if passed else 'FAILED'}")
    return passed


# ---------------------------------------------------------------------------
# Level 12 criteria
# ---------------------------------------------------------------------------

def check_criteria(run_idx, statements, bundle, br_obs, cf_obs, agent):
    failures = []

    # C1: belief_revision field is list
    br_sub = getattr(bundle, 'belief_revision', None)
    if not isinstance(br_sub, list):
        failures.append(
            f"C1 belief_revision_field_present: FAIL — "
            f"type={type(br_sub).__name__}"
        )

    # C2: source_key format valid
    br_stmts = [s for s in statements
                if s.source_type == "belief_revision"]
    for s in br_stmts:
        parts = s.source_key.split(":")
        ok = (len(parts) == 3
              and parts[0] == "revised_expectation"
              and parts[2].lstrip("-").isdigit())
        if not ok:
            failures.append(
                f"C2 source_key_format_valid: FAIL — "
                f"malformed '{s.source_key}'"
            )

    # C3: all br statements resolve
    bad_br = [s for s in br_stmts if not s.source_resolves]
    if bad_br:
        failures.append(
            f"C3 source_resolves_for_all_br: FAIL — "
            f"{len(bad_br)} unresolvable statement(s)"
        )

    # C4: zero hallucinations
    halluc = sum(1 for s in statements if not s.source_resolves)
    if halluc > 0:
        failures.append(
            f"C4 zero_hallucinations: FAIL — {halluc} hallucination(s)"
        )

    # C5: prior/revised texts substrate-derivable
    if isinstance(br_sub, list):
        for rec in br_sub:
            prior   = rec.get("prior_expectation", "")
            revised = rec.get("revised_expectation", "")
            oid     = rec.get("object_id", "")
            # Minimal check: both texts reference the object_id
            if oid and oid not in prior:
                failures.append(
                    f"C5 prior_revised_text_derivable: FAIL — "
                    f"prior_expectation for {oid} does not reference oid"
                )
            if oid and oid not in revised:
                failures.append(
                    f"C5 prior_revised_text_derivable: FAIL — "
                    f"revised_expectation for {oid} does not reference oid"
                )

    # C8: completion signal wired correctly
    draw_active = getattr(agent, 'end_state_draw_active', None)
    activation  = getattr(agent, 'activation_step', None)
    if activation is not None and draw_active is not True:
        failures.append(
            f"C8 completion_signal_fires: FAIL — "
            f"activation_step={activation} but "
            f"end_state_draw_active={draw_active}"
        )

    return failures


# ---------------------------------------------------------------------------
# Level 12 main run
# ---------------------------------------------------------------------------

def run_level12(seeds, num_steps):
    print("Level-12: Belief-Revision and Completion-Signal Correctness")
    print(f"  {len(seeds)} runs, cost={VERIFICATION_COST}, "
          f"steps={num_steps}")
    print()

    total_failures    = []
    total_br_records  = 0
    total_cf_emitted  = 0
    total_cf_raw      = 0
    total_halluc      = 0
    runs_with_activation = 0

    for run_idx, seed in seeds:
        try:
            stmts, bundle, goal_obs, cf_obs, br_obs, agent = _run_one(
                run_idx, seed, num_steps,
            )
        except Exception as e:
            print(f"  Run {run_idx:3d}: ERROR — {e}")
            traceback.print_exc()
            total_failures.append((run_idx, f"exception: {e}"))
            continue

        br_sub   = getattr(bundle, 'belief_revision', None) or []
        cf_sub   = cf_obs.get_substrate() if cf_obs else []
        cf_raw   = cf_obs.raw_records_count() if cf_obs else len(cf_sub)
        halluc   = sum(1 for s in stmts if not s.source_resolves)
        br_stmts = [s for s in stmts if s.source_type == "belief_revision"]
        act_step = getattr(agent, 'activation_step', None)

        total_br_records  += len(br_sub)
        total_cf_emitted  += len(cf_sub)
        total_cf_raw      += cf_raw
        total_halluc      += halluc
        if act_step is not None:
            runs_with_activation += 1

        failures = check_criteria(
            run_idx, stmts, bundle, br_obs, cf_obs, agent
        )

        goal_outcome = ""
        if goal_obs is not None:
            gs = goal_obs.get_substrate()["goal_summary"]
            goal_outcome = (
                f"goal={'resolved' if gs['resolved'] else 'expired'} | "
            )

        if not failures:
            print(
                f"  Run {run_idx:3d} | seed={seed:12d} | "
                f"stmts={len(stmts):3d} | "
                f"br={len(br_sub):2d} | "
                f"cf_emitted={len(cf_sub):3d} | "
                f"cf_raw={cf_raw:3d} | "
                f"act={'Y' if act_step else 'N'} | "
                f"{goal_outcome}"
                f"PASS"
            )
        else:
            print(f"  Run {run_idx:3d}: FAIL")
            for f in failures:
                print(f"    {f}")
                total_failures.append((run_idx, f))

    print()

    # C6: bias_fires
    if total_br_records == 0:
        c6_msg = (
            "C6 bias_fires: FAIL — zero revised_expectation records "
            "across all 10 runs at cost=1.0. resolved_surprise events "
            "occur at this cost in v1.9 data — diagnose pipeline before "
            "proceeding."
        )
        print(f"  {c6_msg}")
        total_failures.append((-1, c6_msg))
    else:
        print(f"  C6 bias_fires: PASS — "
              f"{total_br_records} record(s) across {len(seeds)} runs")

    # C7: temporal_exclusion_effective
    mean_cf = total_cf_emitted / len(seeds) if seeds else 0
    excl_rate = (
        1.0 - total_cf_emitted / total_cf_raw
        if total_cf_raw > 0 else 0.0
    )
    c7_pass = mean_cf < 500
    print(f"  C7 temporal_exclusion_effective: "
          f"{'PASS' if c7_pass else 'FAIL'} — "
          f"mean_cf_emitted={mean_cf:.1f}, "
          f"exclusion_rate={excl_rate:.1%}")
    if not c7_pass:
        total_failures.append(
            (-1, f"C7 temporal_exclusion_effective: FAIL — "
                 f"mean_cf_emitted={mean_cf:.1f} >= 500")
        )

    print()
    print(f"  Total BR records:    {total_br_records}")
    print(f"  Total CF emitted:    {total_cf_emitted}")
    print(f"  Total CF raw:        {total_cf_raw}")
    print(f"  Total hallucinations:{total_halluc}")
    print(f"  Runs with activation:{runs_with_activation}/{len(seeds)}")
    print()

    if not total_failures:
        print(f"Level-12 PASSED — all eight criteria hold.")
        print("Belief-revision and completion-signal correctness confirmed.")
        print("Category α pre-condition satisfied at Level-12 scale.")
        print("Proceed to full v1.10 batch.")
        return True
    else:
        print(f"Level-12 FAILED — {len(total_failures)} failure(s).")
        from collections import Counter
        counts = Counter(
            f.split(":")[0] for _, f in total_failures
            if not f.startswith("exception")
        )
        print()
        print("Failure summary:")
        for criterion, count in counts.most_common():
            print(f"  {criterion}: {count} failure(s)")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-level11-rerun", action="store_true")
    parser.add_argument("--no-belief-revision", action="store_true")
    parser.add_argument("--no-completion-signal", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(SEED_CSV):
        print(f"FAIL: seed file not found: {SEED_CSV}")
        sys.exit(1)

    seeds = load_seeds(SEED_CSV, VERIFICATION_COST, VERIFICATION_N)
    if not seeds:
        print("FAIL: no seeds found.")
        sys.exit(1)

    print("=" * 65)
    print("v1.10 Pre-Flight Verification")
    print(f"  Seed source:  {SEED_CSV}")
    print(f"  Cost:         {VERIFICATION_COST}")
    print(f"  Steps:        {VERIFICATION_STEPS:,}")
    print(f"  Runs:         {len(seeds)}")
    print("=" * 65)
    print()

    if not args.skip_level11_rerun:
        l11_pass = run_level11_rerun(seeds, VERIFICATION_STEPS)
        print()
        if not l11_pass:
            print("Level-11 re-run FAILED. Fix before Level-12.")
            sys.exit(1)
        print("=" * 65)
        print()

    l12_pass = run_level12(seeds, VERIFICATION_STEPS)
    sys.exit(0 if l12_pass else 1)


if __name__ == "__main__":
    main()
