"""
verify_v1_8_level10.py
-----------------------
v1.8 Level-10 pre-flight verification: goal layer correctness.

V18GoalObserver, instantiated with a deterministic goal assignment,
must satisfy six correctness criteria on 10 runs at cost=1.0,
num_steps=80,000 before the full v1.8 batch runs.

The 80,000-step run length gives a step_budget of 40,000 steps — enough
for locate_family resolution to be reachable while ensuring that some
runs expire, producing a non-degenerate verification population that
exercises both branches of the terminal logic.

Exit 0: all six criteria hold across all 10 runs. Goal layer is correct.
        Category α pre-condition satisfied at Level 10 scale.
        Proceed to full v1.8 batch.

Exit 1: at least one criterion failed. Prints the specific failure type
        and run_idx. Correct and re-run Level 10 before proceeding.

SIX CRITERIA (per pre-registration §3)
  1. goal_set_present       — goal_set record exists in every run
  2. exactly_one_terminal   — exactly one of goal_resolved / goal_expired
                               is non-None per run (not both; not neither)
  3. resolved_within_budget — if resolved: resolved_at_step <= step_budget
  4. expired_at_budget      — if expired: expired_at_step == step_budget
  5. goal_source_resolves   — all statements with source_type=="goal"
                               have source_resolves=True
  6. zero_hallucinations    — total hallucination_count == 0 across all
                               statements in the run

LEVEL 9 RE-RUN
Before running Level 10, this script first runs a Level 9 regression
check (goal observer disabled) to confirm that the v1.8 substrate stack
produces output consistent with v1.7 at the same seeds. Level 9 re-run
is not byte-for-byte comparison (different arch tag, different num_steps
from the v1.7 Level 9 run); it checks Category α (zero hallucinations)
only.

Seeds: first 10 from run_data_v1_7.csv at cost=1.0, num_steps=80000.
If fewer than 10 seeds exist at num_steps=80000, falls back to
num_steps=320000 seeds (same agent, shorter run).

Usage:
    python verify_v1_8_level10.py [--skip-level9-rerun]
"""

import argparse
import csv
import os
import sys
import traceback

import numpy as np

# v1.8 substrate patches must be imported before any observer is instantiated
import v1_8_observer_substrates  # noqa: F401
from v1_8_observer_substrates import build_bundle_from_observers

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_7_agent import V17Agent

from v1_1_provenance import V1ProvenanceStore
from v1_3_schema_extension import V13SchemaObserver
from v1_3_family_observer import V13FamilyObserver
from v1_4_comparison_observer import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver
from v1_6_reporting_layer import V16ReportingLayer
from v1_7_observer_substrates import flush_provenance_csv

from v1_8_goal_layer import V18GoalObserver, assign_goal

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED_CSV           = "run_data_v1_7.csv"
VERIFICATION_COST  = 1.0
VERIFICATION_STEPS = 80000
VERIFICATION_N     = 10
ARCH               = "v1_8"

# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

def load_seeds(path, cost, steps, n):
    """Load first n seeds at (cost, steps) from run_data CSV.

    Falls back to any available steps value if exact match not found.
    """
    seeds = []
    fallback = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                row_cost  = float(row["hazard_cost"])
                row_steps = int(row["num_steps"])
                row_seed  = int(row["seed"])
                row_idx   = int(row["run_idx"])
            except (ValueError, KeyError):
                continue
            if abs(row_cost - cost) < 1e-6:
                if row_steps == steps:
                    seeds.append((row_idx, row_seed))
                else:
                    fallback.append((row_idx, row_seed, row_steps))

    seeds.sort(key=lambda x: x[0])
    if len(seeds) >= n:
        return [(idx, seed) for idx, seed in seeds[:n]]

    # Fallback: use seeds from a different step count (same cost)
    fallback.sort(key=lambda x: (x[0],))
    fallback_pairs = [(idx, seed) for idx, seed, _ in fallback]
    # Deduplicate by run_idx
    seen = set()
    deduped = []
    for idx, seed in fallback_pairs:
        if idx not in seen:
            seen.add(idx)
            deduped.append((idx, seed))
    return deduped[:n]


# ---------------------------------------------------------------------------
# Single run (shared by Level 9 re-run and Level 10)
# ---------------------------------------------------------------------------

def _run_one_verify(run_idx, seed, num_steps, with_goal):
    """Execute one verification run. Returns (statements, goal_sub, step_budget)."""
    np.random.seed(seed)

    world = V17World(hazard_cost=VERIFICATION_COST, seed=seed)
    agent = V17Agent(world, total_steps=num_steps, num_actions=NUM_ACTIONS)

    meta = {
        "arch":        ARCH,
        "hazard_cost": VERIFICATION_COST,
        "num_steps":   num_steps,
        "run_idx":     run_idx,
        "seed":        seed,
    }

    from curiosity_agent_v1_7_world import (
        FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ
    )
    ctc = {
        "FRAME": FRAME, "NEUTRAL": NEUTRAL, "HAZARD": HAZARD,
        "ATTRACTOR": ATTRACTOR, "END_STATE": END_STATE,
        "KNOWLEDGE": KNOWLEDGE, "DIST_OBJ": DIST_OBJ,
    }

    prov_obs      = V1ProvenanceStore(agent, world, meta, ctc)
    schema_obs    = V13SchemaObserver(agent, world, meta)
    family_obs    = V13FamilyObserver(agent, world, meta, provenance_store=prov_obs)
    comp_obs      = V14ComparisonObserver(family_obs, meta)
    pe_obs        = V15PredictionErrorObserver(agent, world, meta)

    goal_obs = None
    step_budget = 0
    if with_goal:
        goal_type, target_id, step_budget = assign_goal(run_idx, num_steps)
        goal_obs = V18GoalObserver(
            agent, world, meta, goal_type, target_id, step_budget
        )

    observers = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs]
    if goal_obs is not None:
        observers.append(goal_obs)

    # Run loop
    state = world.observe()
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
        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)
        state = obs_next

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
    )
    layer      = V16ReportingLayer(bundle)
    statements = layer.generate_report()
    goal_sub   = bundle.goal   # None if goal observer not active

    return statements, goal_sub, step_budget


# ---------------------------------------------------------------------------
# Level 9 re-run
# ---------------------------------------------------------------------------

def run_level9_rerun(seeds, num_steps):
    """Category α regression check: zero hallucinations, goal observer OFF.

    Not a byte-identical check — confirms the v1.8 substrate stack does
    not introduce hallucinations when the goal layer is absent.
    """
    print("Level-9 Re-Run: Category α regression (goal observer DISABLED)")
    print(f"  {len(seeds)} runs at cost={VERIFICATION_COST}, steps={num_steps}")
    print()

    total_halluc = 0

    for run_idx, seed in seeds:
        try:
            statements, _, _ = _run_one_verify(
                run_idx, seed, num_steps, with_goal=False
            )
        except Exception as e:
            print(f"  Run {run_idx:3d}: ERROR — {e}")
            traceback.print_exc()
            total_halluc += 1
            continue

        halluc = sum(1 for s in statements if not s.source_resolves)
        total_halluc += halluc
        status = "PASS" if halluc == 0 else f"FAIL({halluc})"
        print(
            f"  Run {run_idx:3d} | seed={seed:12d} | "
            f"stmts={len(statements):3d} | {status}"
        )

    print()
    if total_halluc == 0:
        print("Level-9 Re-Run: PASSED — zero hallucinations. v1.8 stack is clean.")
        return True
    else:
        print(f"Level-9 Re-Run: FAILED — {total_halluc} hallucination(s).")
        print("  The v1.8 substrate stack introduced a hallucination before the")
        print("  goal layer was added. Diagnose v1_8_observer_substrates.py.")
        return False


# ---------------------------------------------------------------------------
# Level 10 criteria check
# ---------------------------------------------------------------------------

def check_criteria(run_idx, statements, goal_sub, step_budget):
    """Apply six Level-10 criteria. Returns list of failure strings."""
    failures = []

    # Criterion 1: goal_set present
    if goal_sub is None or goal_sub.get("goal_set") is None:
        failures.append("C1 goal_set_present: FAIL — goal_set is None")

    # Criterion 2: exactly one terminal record
    resolved = (goal_sub is not None and goal_sub.get("goal_resolved") is not None)
    expired  = (goal_sub is not None and goal_sub.get("goal_expired")  is not None)
    if resolved and expired:
        failures.append("C2 exactly_one_terminal: FAIL — both resolved AND expired")
    elif not resolved and not expired:
        failures.append("C2 exactly_one_terminal: FAIL — neither resolved NOR expired")

    # Criterion 3: if resolved, resolved_at_step <= step_budget
    if resolved:
        at_step = goal_sub["goal_resolved"].get("resolved_at_step")
        if at_step is None or at_step > step_budget:
            failures.append(
                f"C3 resolved_within_budget: FAIL — "
                f"resolved_at_step={at_step}, budget={step_budget}"
            )

    # Criterion 4: if expired, expired_at_step == step_budget
    if expired:
        at_step = goal_sub["goal_expired"].get("expired_at_step")
        if at_step != step_budget:
            failures.append(
                f"C4 expired_at_budget: FAIL — "
                f"expired_at_step={at_step}, budget={step_budget}"
            )

    # Criterion 5: all goal-sourced statements resolve
    goal_stmts = [s for s in statements if s.source_type == "goal"]
    bad_goal   = [s for s in goal_stmts if not s.source_resolves]
    if bad_goal:
        failures.append(
            f"C5 goal_source_resolves: FAIL — "
            f"{len(bad_goal)} unresolvable goal statement(s): "
            + ", ".join(f"source_key={s.source_key}" for s in bad_goal)
        )

    # Criterion 6: zero total hallucinations
    halluc = sum(1 for s in statements if not s.source_resolves)
    if halluc > 0:
        failures.append(
            f"C6 zero_hallucinations: FAIL — {halluc} hallucination(s)"
        )

    return failures


# ---------------------------------------------------------------------------
# Level 10 main run
# ---------------------------------------------------------------------------

def run_level10(seeds, num_steps):
    """Run 10 verification runs with goal observer enabled."""
    print("Level-10: Goal Layer Correctness")
    print(f"  {len(seeds)} runs at cost={VERIFICATION_COST}, steps={num_steps}")
    print(f"  step_budget per run = {int(num_steps * 0.5)}")
    print(
        "  Criteria: goal_set_present | exactly_one_terminal | "
        "resolved_within_budget | expired_at_budget | "
        "goal_source_resolves | zero_hallucinations"
    )
    print()

    total_failures    = []
    resolved_count    = 0
    expired_count     = 0
    goal_stmt_count   = 0
    total_halluc      = 0

    for run_idx, seed in seeds:
        try:
            statements, goal_sub, step_budget = _run_one_verify(
                run_idx, seed, num_steps, with_goal=True
            )
        except Exception as e:
            print(f"  Run {run_idx:3d}: ERROR — {e}")
            traceback.print_exc()
            total_failures.append((run_idx, f"exception: {e}"))
            continue

        failures = check_criteria(run_idx, statements, goal_sub, step_budget)

        # Tallies
        if goal_sub is not None:
            if goal_sub.get("goal_resolved") is not None:
                resolved_count += 1
            if goal_sub.get("goal_expired") is not None:
                expired_count += 1
        goal_stmts  = [s for s in statements if s.source_type == "goal"]
        goal_stmt_count += len(goal_stmts)
        total_halluc += sum(1 for s in statements if not s.source_resolves)

        # Per-run output
        if not failures:
            resolved = (goal_sub is not None
                        and goal_sub.get("goal_resolved") is not None)
            outcome  = "resolved" if resolved else "expired"
            summary  = goal_sub.get("goal_summary", {}) if goal_sub else {}
            print(
                f"  Run {run_idx:3d} | seed={seed:12d} | "
                f"stmts={len(statements):3d} | "
                f"goal_stmts={len(goal_stmts)} | "
                f"{outcome} | "
                f"type={summary.get('goal_type','?')} "
                f"target={summary.get('target_id','?')} | "
                f"PASS"
            )
        else:
            print(f"  Run {run_idx:3d}: FAIL")
            for f in failures:
                print(f"    {f}")
                total_failures.append((run_idx, f))

    print()
    print(f"  Resolved runs:    {resolved_count} / {len(seeds)}")
    print(f"  Expired runs:     {expired_count} / {len(seeds)}")
    print(f"  Goal statements:  {goal_stmt_count}")
    print(f"  Hallucinations:   {total_halluc}")
    print()

    if not total_failures:
        print("Level-10 PASSED — all six criteria hold across all "
              f"{len(seeds)} runs.")
        print("Goal layer correctness confirmed.")
        print("Category α pre-condition satisfied at Level-10 scale.")
        print("Proceed to full v1.8 batch.")
        return True
    else:
        print(f"Level-10 FAILED — {len(total_failures)} criterion failure(s).")
        print()
        print("Failure summary:")
        from collections import Counter
        criterion_counts = Counter(f.split(":")[0] for _, f in total_failures
                                   if not f.startswith("exception"))
        for criterion, count in criterion_counts.most_common():
            print(f"  {criterion}: {count} failure(s)")
        print()
        print("Diagnose the identified component before proceeding.")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-level9-rerun", action="store_true",
        help="Skip Level-9 regression check and run Level-10 directly"
    )
    args = parser.parse_args()

    if not os.path.exists(SEED_CSV):
        print(f"FAIL: seed file not found: {SEED_CSV}")
        sys.exit(1)

    seeds = load_seeds(SEED_CSV, VERIFICATION_COST, VERIFICATION_STEPS, VERIFICATION_N)
    if len(seeds) < VERIFICATION_N:
        print(
            f"WARNING: only {len(seeds)} seeds available "
            f"(need {VERIFICATION_N}). Proceeding with {len(seeds)}."
        )
    if not seeds:
        print("FAIL: no seeds found.")
        sys.exit(1)

    print("=" * 65)
    print("v1.8 Pre-Flight Verification")
    print(f"  Seed source:  {SEED_CSV}")
    print(f"  Cost:         {VERIFICATION_COST}")
    print(f"  Steps:        {VERIFICATION_STEPS}")
    print(f"  Budget:       {int(VERIFICATION_STEPS * 0.5)}")
    print(f"  Runs:         {len(seeds)}")
    print("=" * 65)
    print()

    # Level 9 re-run
    if not args.skip_level9_rerun:
        l9_pass = run_level9_rerun(seeds, VERIFICATION_STEPS)
        print()
        if not l9_pass:
            print("Level-9 re-run FAILED. Fix the v1.8 substrate stack before")
            print("running Level-10.")
            sys.exit(1)
        print("=" * 65)
        print()

    # Level 10
    l10_pass = run_level10(seeds, VERIFICATION_STEPS)
    print()

    sys.exit(0 if l10_pass else 1)


if __name__ == "__main__":
    main()
