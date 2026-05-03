"""
verify_v1_7_level9.py
----------------------
v1.7 Level-9 pre-flight verification: SubstrateBundle portability.

V16ReportingLayer, instantiated with a SubstrateBundle populated from
V17World observers, must produce reports that pass Category α (zero
hallucinations) on 10 runs before the full v1.7 batch.

This is the substrate-agnosticism commitment operationalised at minimum
scale (pre-registration §2.4).

Exit 0: all 10 runs pass Category α. The reporting layer carried forward
        unchanged. Proceed to full v1.7 batch.

Exit 1: at least one run failed Category α. A hallucination was found —
        a ReportStatement whose source_key does not resolve in the
        new-substrate SubstrateBundle. Prints the specific source_type
        and source_key of the failing statement to guide diagnosis.
        Correct and re-run Level 9 before proceeding.

WHAT LEVEL 9 CONFIRMS
If Level 9 exits 0:
  - V16ReportingLayer imported no grid-specific constant that would
    break on object_id keys.
  - SubstrateBundle.resolve() works correctly with object_id-keyed
    provenance records and object_id-based encounter records.
  - The flag_id format migration (mastery:att_green vs mastery:(4,15))
    is complete at the substrate interface.
  - SICC Commitment 10 is operative at the reporting layer.

If Level 9 exits 1:
  - The specific source_type of the failing statement identifies the
    component that retained a grid-specific assumption.
  - Diagnose that component before amending.

Seeds: first 10 from run_data_v1_5.csv at cost=1.0, num_steps=320000.
"""

import csv
import os
import sys

import numpy as np

import v1_7_observer_substrates  # noqa: F401

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_7_agent import V17Agent

from v1_1_provenance import V1ProvenanceStore
from v1_3_schema_extension import V13SchemaObserver
from v1_3_family_observer import V13FamilyObserver
from v1_4_comparison_observer import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver

from v1_6_substrate_bundle import build_bundle_from_observers
from v1_6_reporting_layer import V16ReportingLayer

SEED_CSV      = "run_data_v1_5.csv"
VERIFICATION_COST  = 1.0
VERIFICATION_STEPS = 20000
VERIFICATION_N     = 10
ARCH = "v1_7"


def load_seeds(path, cost, steps, n):
    seeds = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if (float(row["hazard_cost"]) == cost
                        and int(row["num_steps"]) == steps):
                    seeds.append((int(row["run_idx"]), int(row["seed"])))
            except (ValueError, KeyError):
                continue
    seeds.sort(key=lambda x: x[0])
    return seeds[:n]


def run_one_verify(run_idx, seed, hazard_cost):
    np.random.seed(seed)
    world = V17World(hazard_cost=hazard_cost, seed=seed)
    agent = V17Agent(world, total_steps=VERIFICATION_STEPS, num_actions=NUM_ACTIONS)

    meta = {
        "arch": ARCH, "hazard_cost": hazard_cost,
        "num_steps": VERIFICATION_STEPS, "run_idx": run_idx, "seed": seed,
    }

    from curiosity_agent_v1_7_world import (
        FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ
    )
    ctc = {"FRAME":FRAME,"NEUTRAL":NEUTRAL,"HAZARD":HAZARD,
            "ATTRACTOR":ATTRACTOR,"END_STATE":END_STATE,
            "KNOWLEDGE":KNOWLEDGE,"DIST_OBJ":DIST_OBJ}
    prov_obs   = V1ProvenanceStore(agent, world, meta, ctc)
    schema_obs = V13SchemaObserver(agent, world, meta)
    family_obs = V13FamilyObserver(agent, world, meta, provenance_store=prov_obs)
    comp_obs   = V14ComparisonObserver(family_obs, meta)
    pe_obs     = V15PredictionErrorObserver(agent, world, meta)
    observers  = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs]

    state = world.observe()
    for step in range(VERIFICATION_STEPS):
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
        obs.on_run_end(VERIFICATION_STEPS)

    bundle = build_bundle_from_observers(
        provenance_obs=prov_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comparison_obs=comp_obs,
        prediction_error_obs=pe_obs,
        run_meta=meta,
    )
    layer = V16ReportingLayer(bundle)
    statements = layer.generate_report()
    return statements, bundle


def main():
    if not os.path.exists(SEED_CSV):
        print(f"FAIL: seed file not found: {SEED_CSV}")
        sys.exit(1)

    seeds = load_seeds(SEED_CSV, VERIFICATION_COST, VERIFICATION_STEPS, VERIFICATION_N)
    if len(seeds) < VERIFICATION_N:
        print(f"FAIL: only {len(seeds)} seeds found; need {VERIFICATION_N}.")
        sys.exit(1)

    print("v1.7 Level-9 Pre-Flight: SubstrateBundle Portability")
    print(f"  V16ReportingLayer on V17World SubstrateBundle")
    print(f"  {VERIFICATION_N} runs at cost={VERIFICATION_COST}")
    print(f"  Category α criterion: zero hallucinations across all {VERIFICATION_N} runs")
    print()

    total_hallucinations = 0
    all_failures = []

    for run_idx, seed in seeds:
        try:
            statements, bundle = run_one_verify(run_idx, seed, VERIFICATION_COST)
        except Exception as e:
            import traceback
            print(f"  Run {run_idx}: ERROR — {e}")
            traceback.print_exc()
            all_failures.append((run_idx, "exception", str(e), ""))
            total_hallucinations += 1
            continue

        hallucinations = [s for s in statements if not s.source_resolves]
        total_hallucinations += len(hallucinations)

        status = "PASS" if not hallucinations else f"FAIL({len(hallucinations)})"
        print(
            f"  Run {run_idx:3d} | seed={seed:12d} | "
            f"stmts={len(statements):3d} | {status}"
        )

        for s in hallucinations:
            all_failures.append((run_idx, s.query_type, s.source_type, s.source_key))
            print(f"    HALLUCINATION: query={s.query_type} "
                  f"source_type={s.source_type} source_key={s.source_key}")
            print(f"    text: {s.text[:120]}")

    print()

    if total_hallucinations == 0:
        print("Level-9 PASSED — zero hallucinations across all "
              f"{VERIFICATION_N} runs.")
        print("Category α pre-condition satisfied at Level-9 scale.")
        print("Substrate-agnosticism commitment confirmed at the reporting layer.")
        print("Proceed to full v1.7 batch.")
        sys.exit(0)
    else:
        print(f"Level-9 FAILED — {total_hallucinations} hallucination(s) found.")
        print()
        print("Diagnostic: failing statements by source_type:")
        from collections import Counter
        type_counts = Counter(f[2] for f in all_failures)
        for source_type, count in type_counts.most_common():
            print(f"  {source_type}: {count} failure(s)")
        print()
        print("Interpretation:")
        print("  provenance failure -> flag_id format not fully migrated to object_ids")
        print("  family failure     -> family field key uses coord rather than object_id")
        print("  schema failure     -> schema field missing for new object type")
        print("  prediction_error   -> encounter index out of range or missing")
        print("  comparison failure -> comparison field absent or key mismatch")
        print()
        print("Correct the identified substrate-interface component.")
        print("Re-run Level 9 before proceeding to full batch.")
        sys.exit(1)


if __name__ == "__main__":
    main()
