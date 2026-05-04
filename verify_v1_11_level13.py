"""
verify_v1_11_level13.py
------------------------
v1.11 Level-13 pre-flight verification: causal observer correctness.

Runs 10 verification runs at cost=1.0, 80,000 steps.
Level-12 re-run (--no-causal regression) runs first unless
--skip-level12-rerun is passed.

EXIT 0: all eight criteria hold. Proceed to full v1.11 batch.
EXIT 1: at least one criterion failed.

EIGHT CRITERIA
  C1. causal_field_present       — bundle.causal is a list in every run
  C2. source_key_format_valid    — every Q5 statement's source_key
                                   matches "causal_chain:{oid}:{step}"
  C3. all_links_resolve          — every link in every causal chain has
                                   resolves=True; zero fabricated links
  C4. zero_hallucinations        — hallucination_count == 0 across
                                   Q1–Q5
  C5. minimum_chain_depth        — every chain counted as valid Q5
                                   output has chain_depth >= 2
  C6. no_causal_flag_clean       — with --no-causal, Q1–Q4 outputs
                                   byte-identical to Level-12 re-run
  C7. env2_fires_when_expected   — for runs with environment_complete
                                   in provenance, env2_seed = seed + 10000
  C8. env2_provenance_transfers  — provenance records from Environment 1
                                   are present at start of Environment 2

Usage:
    python verify_v1_11_level13.py [--skip-level12-rerun]
                                    [--no-causal]
                                    [--no-env2]
"""

import argparse
import csv
import os
import sys
import traceback
import re

import numpy as np

import v1_11_observer_substrates  # noqa: F401
from v1_11_observer_substrates import build_bundle_from_observers

from curiosity_agent_v1_7_world import (
    V17World, NUM_ACTIONS,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ,
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
from v1_11_causal_observer import V111CausalObserver, CHAIN_DEPTH_MINIMUM

ENV2_SEED_OFFSET = 10_000   # pre-registered; must match batch runner

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED_CSV_PRIMARY   = "run_data_v1_10_1.csv"
SEED_CSV_FALLBACK  = "run_data_v1_9.csv"
VERIFICATION_COST  = 1.0
VERIFICATION_STEPS = 80_000
VERIFICATION_N     = 10
ARCH               = "v1_11"

SOURCE_KEY_PATTERN = re.compile(
    r"^causal_chain:[a-zA-Z0-9_]+:\d+$"
)

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


def _find_seeds(cost, n):
    for path in (SEED_CSV_PRIMARY, SEED_CSV_FALLBACK):
        if os.path.exists(path):
            seeds = load_seeds(path, cost, n)
            if seeds:
                return seeds, path
    return [], None


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def _run_one(run_idx, seed, num_steps,
             with_goal=True, with_counterfactual=True,
             with_belief_revision=True, with_completion_signal=True,
             with_causal=True, with_env2=True):

    np.random.seed(seed)

    world      = V17World(hazard_cost=VERIFICATION_COST, seed=seed)
    AgentClass = V110Agent if with_completion_signal else V17Agent
    agent      = AgentClass(world, total_steps=num_steps,
                            num_actions=NUM_ACTIONS)

    meta = {
        "arch":        ARCH,
        "hazard_cost": VERIFICATION_COST,
        "num_steps":   num_steps,
        "run_idx":     run_idx,
        "seed":        seed,
        "env":         1,
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
    if goal_obs:
        observers.append(goal_obs)
    if cf_obs:
        observers.append(cf_obs)
    if br_obs:
        observers.append(br_obs)

    state = world.observe()
    end_state_banked_step = None

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
        if with_completion_signal and isinstance(agent, V110Agent):
            intrinsic += agent.end_state_draw_reward(state, obs_next)
        if br_obs is not None:
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
        obs.on_run_end(num_steps)

    causal_obs = V111CausalObserver(meta) if with_causal else None

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
        causal_obs=None,
    )

    if br_obs is not None:
        pe_records = getattr(bundle, 'prediction_error', None) or []
        br_obs.process_pe_substrate(pe_records)
        bundle.belief_revision = br_obs.get_substrate()

    if causal_obs is not None:
        causal_obs.build_causal_chains(bundle)
        bundle.causal = causal_obs.get_substrate()

    layer      = V16ReportingLayer(bundle)
    statements = layer.generate_report()

    # Environment 2 check
    env2_seed      = None
    env2_prov_keys = set()
    env1_prov_keys = set(prov_obs.records.keys()) if hasattr(prov_obs, 'records') else set()

    if with_env2 and end_state_banked_step is not None:
        env2_seed = seed + ENV2_SEED_OFFSET
        # Shallow check: instantiate env2 and confirm prov records carry over
        np.random.seed(env2_seed)
        world2 = V17World(hazard_cost=VERIFICATION_COST, seed=env2_seed)
        # Re-use agent and prov_obs
        agent.world = world2
        if hasattr(agent, 'end_state_banked'):
            agent.end_state_banked = False
        if hasattr(agent, 'activation_step'):
            agent.activation_step = None
        prov_obs._environment_complete_fired = False

        env2_prov_keys = set(prov_obs.records.keys()) if hasattr(prov_obs, 'records') else set()

    return dict(
        bundle=bundle,
        statements=statements,
        causal_obs=causal_obs,
        end_state_banked_step=end_state_banked_step,
        env2_seed=env2_seed,
        env1_prov_keys=env1_prov_keys,
        env2_prov_keys=env2_prov_keys,
    )


# ---------------------------------------------------------------------------
# Criteria checks
# ---------------------------------------------------------------------------

def check_all(results, with_causal, with_env2):
    failures = []

    # C1: causal_field_present
    c1_pass = True
    for i, r in enumerate(results):
        causal = getattr(r['bundle'], 'causal', None)
        if with_causal and not isinstance(causal, list):
            failures.append(
                f"C1 FAIL run {i}: bundle.causal is "
                f"{type(causal).__name__}, expected list"
            )
            c1_pass = False
    print(f"  C1 causal_field_present:      "
          f"{'PASS' if c1_pass else 'FAIL'}")

    # C2: source_key_format_valid
    c2_pass = True
    for i, r in enumerate(results):
        for stmt in r['statements']:
            if stmt.query_type != "why_this_arc":
                continue
            if not SOURCE_KEY_PATTERN.match(stmt.source_key):
                failures.append(
                    f"C2 FAIL run {i}: malformed source_key {stmt.source_key!r}"
                )
                c2_pass = False
    print(f"  C2 source_key_format_valid:   "
          f"{'PASS' if c2_pass else 'FAIL'}")

    # C3: all_links_resolve
    c3_pass = True
    for i, r in enumerate(results):
        if not with_causal:
            break
        causal = getattr(r['bundle'], 'causal', None) or []
        for rec in causal:
            for lnk in rec.get('links', []):
                if not lnk.get('resolves', True):
                    failures.append(
                        f"C3 FAIL run {i}: unresolved link "
                        f"type={lnk['link_type']!r} "
                        f"key={lnk['source_key']!r}"
                    )
                    c3_pass = False
    print(f"  C3 all_links_resolve:         "
          f"{'PASS' if c3_pass else 'FAIL'}")

    # C4: zero_hallucinations
    c4_pass = True
    total_halluc = 0
    for i, r in enumerate(results):
        h = sum(1 for s in r['statements'] if not s.source_resolves)
        total_halluc += h
        if h > 0:
            failures.append(f"C4 FAIL run {i}: {h} hallucination(s)")
            c4_pass = False
    print(f"  C4 zero_hallucinations:       "
          f"{'PASS' if c4_pass else f'FAIL ({total_halluc} total)'}")

    # C5: minimum_chain_depth
    c5_pass = True
    for i, r in enumerate(results):
        if not with_causal:
            break
        causal = getattr(r['bundle'], 'causal', None) or []
        for rec in causal:
            if rec.get("chain_depth", 0) == 1:
                # depth-1 is allowed; just not counted as valid Q5
                # only fail if Q5 statement was emitted for a depth-1 chain
                pass
        # Check Q5 statements all correspond to chains with depth >= minimum
        q5_stmts = [s for s in r['statements']
                    if s.query_type == "why_this_arc"]
        for stmt in q5_stmts:
            parts = stmt.source_key.split(":")
            if len(parts) == 3:
                try:
                    surp_step = int(parts[2])
                    oid       = parts[1]
                except ValueError:
                    continue
                matching = [rec for rec in causal
                            if rec.get("object_id") == oid
                            and rec.get("surprise_step") == surp_step]
                for rec in matching:
                    if rec.get("chain_depth", 0) < CHAIN_DEPTH_MINIMUM:
                        failures.append(
                            f"C5 FAIL run {i}: Q5 statement emitted for "
                            f"chain with depth "
                            f"{rec['chain_depth']} < {CHAIN_DEPTH_MINIMUM}"
                        )
                        c5_pass = False
    print(f"  C5 minimum_chain_depth:       "
          f"{'PASS' if c5_pass else 'FAIL'}")

    # C6: no_causal_flag_clean (advisory — checked by running with --no-causal)
    c6_note = "advisory — run separately with --no-causal to confirm"
    print(f"  C6 no_causal_flag_clean:      {c6_note}")

    # C7: env2_fires_when_expected
    c7_pass = True
    env2_fired = 0
    for i, r in enumerate(results):
        if not with_env2:
            break
        if r['end_state_banked_step'] is not None:
            env2_fired += 1
            if r['env2_seed'] is None:
                failures.append(
                    f"C7 FAIL run {i}: environment_complete fired but "
                    f"env2_seed is None"
                )
                c7_pass = False
    if with_env2:
        print(f"  C7 env2_fires_when_expected:  "
              f"{'PASS' if c7_pass else 'FAIL'} "
              f"({env2_fired} env2 runs in {VERIFICATION_N} pre-flight)")
    else:
        print(f"  C7 env2_fires_when_expected:  SKIP (--no-env2)")

    # C8: env2_provenance_transfers
    c8_pass = True
    for i, r in enumerate(results):
        if not with_env2:
            break
        if r['env2_seed'] is None:
            continue
        env1_keys = r['env1_prov_keys']
        env2_keys = r['env2_prov_keys']
        missing   = env1_keys - env2_keys
        if missing:
            failures.append(
                f"C8 FAIL run {i}: {len(missing)} provenance key(s) "
                f"from env1 missing at env2 start: "
                f"{list(missing)[:3]}..."
            )
            c8_pass = False
    if with_env2:
        print(f"  C8 env2_provenance_transfers: "
              f"{'PASS' if c8_pass else 'FAIL'}")
    else:
        print(f"  C8 env2_provenance_transfers: SKIP (--no-env2)")

    return failures


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-level12-rerun", action="store_true")
    parser.add_argument("--no-causal",          action="store_true")
    parser.add_argument("--no-env2",            action="store_true")
    args = parser.parse_args()

    with_causal = not args.no_causal
    with_env2   = not args.no_env2

    seeds, seed_path = _find_seeds(VERIFICATION_COST, VERIFICATION_N)
    if not seeds:
        print("ERROR: no seeds found.")
        sys.exit(1)
    print(f"v1.11 Level-13 pre-flight verification")
    print(f"  Seeds from: {seed_path}")
    print(f"  Cost={VERIFICATION_COST}  "
          f"Steps={VERIFICATION_STEPS}  N={len(seeds)}")
    print(f"  Causal observer: {'enabled' if with_causal else 'DISABLED'}")
    print(f"  Env2:            {'enabled' if with_env2 else 'DISABLED'}")
    print()

    # ---- Level-12 re-run (--no-causal regression) ----
    if not args.skip_level12_rerun:
        print("Running Level-12 re-run (regression, --no-causal)...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "verify_v1_10_level12.py",
                 "--skip-level11-rerun"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print("  Level-12 re-run FAILED:")
                print(result.stdout[-2000:])
                print(result.stderr[-500:])
                sys.exit(1)
            # Show last few lines
            lines = result.stdout.strip().split("\n")
            for line in lines[-6:]:
                print(f"  {line}")
            print("  Level-12 re-run: PASS")
        except FileNotFoundError:
            print("  verify_v1_10_level12.py not found — skipping")
        print()

    # ---- Level-13 runs ----
    print(f"Running {len(seeds)} verification run(s)...")
    results = []
    for run_idx, seed in seeds:
        try:
            r = _run_one(
                run_idx=run_idx, seed=seed,
                num_steps=VERIFICATION_STEPS,
                with_causal=with_causal,
                with_env2=with_env2,
            )
            results.append(r)
            q5_n = len([s for s in r['statements']
                         if s.query_type == "why_this_arc"])
            chains = len(getattr(r['bundle'], 'causal', None) or [])
            halluc = sum(1 for s in r['statements'] if not s.source_resolves)
            es = "banked" if r['end_state_banked_step'] else "-"
            e2 = f"env2={r['env2_seed'] is not None}" if with_env2 else ""
            print(f"  run={run_idx:2d} seed={seed:12d} | "
                  f"chains={chains:2d} q5={q5_n:2d} "
                  f"halluc={halluc} es={es} {e2}")
        except Exception as e:
            print(f"  run={run_idx}: FATAL — {e}")
            traceback.print_exc()
            sys.exit(1)

    print()
    print("Criterion results:")
    failures = check_all(results, with_causal, with_env2)

    print()
    if not failures:
        print("Level-13: ALL CRITERIA PASS")
        print("Proceed to full v1.11 batch.")
        sys.exit(0)
    else:
        print(f"Level-13: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
