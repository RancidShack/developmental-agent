"""
curiosity_agent_v1_7_batch.py
------------------------------
v1.7 batch runner.

Runs agent simulations in V17World (3D continuous-space substrate) with
the full six-observer cognitive stack. Writes the standard six observer
output CSVs plus the reporting layer outputs.

ARCHITECTURE
  - V17Agent in V17World replaces V15Agent in V13World.
  - The six observers (provenance, schema, family, comparison,
    prediction-error, reporting) are instantiated identically to v1.5/v1.6
    except that V15PredictionErrorObserver is patched by
    v1_7_observer_substrates to use object_id keys.
  - The reporting layer (V16ReportingLayer) is instantiated with a
    SubstrateBundle built from v1.7 observer outputs. It is not modified.
  - Seeds are drawn from run_data_v1_5.csv at num_steps=320000, preserving
    the seed chain.

PRE-FLIGHT
  Run Levels 1-9 before this batch. This script does not run them.
  Level 1-6: verify_v1_7_levels_1_6.py
  Level 7: verify_v1_7_substrate.py
  Level 8: verify_v1_7_single_run.py
  Level 9: verify_v1_7_level9.py

Usage:
    python curiosity_agent_v1_7_batch.py [--no-report]
"""

import argparse
import csv
import os
import sys

import numpy as np

# Substrate patch must be imported before any observer is instantiated
import v1_7_observer_substrates  # noqa: F401
from v1_7_observer_substrates import flush_provenance_csv

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_7_agent import V17Agent

from v1_1_provenance import V1ProvenanceStore
from v1_3_schema_extension import V13SchemaObserver
from v1_3_family_observer import V13FamilyObserver
from v1_4_comparison_observer import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver

from v1_6_substrate_bundle import build_bundle_from_observers, SubstrateBundle
from v1_6_reporting_layer import V16ReportingLayer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_CSV               = "run_data_v1_5.csv"

RUN_DATA_CSV           = "run_data_v1_7.csv"
PROVENANCE_CSV         = "provenance_v1_7.csv"
SCHEMA_CSV             = "schema_v1_7.csv"
FAMILY_CSV             = "family_v1_7.csv"
COMPARISON_CSV         = "comparison_v1_7.csv"
PREDICTION_ERROR_CSV   = "prediction_error_v1_7.csv"
REPORT_CSV             = "report_v1_7.csv"
REPORT_SUMMARY_CSV     = "report_summary_v1_7.csv"

BATCH_STEPS  = 320000
HAZARD_COSTS = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST = 15

ARCH = "v1_7"

# ---------------------------------------------------------------------------
# Run data fields
# ---------------------------------------------------------------------------

RUN_DATA_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "phase_1_end_step", "phase_2_end_step",
    "time_to_first_flag", "time_to_second_flag", "time_to_final_flag",
    "total_cost_incurred",
    "time_to_first_mastery", "time_to_final_mastery",
    "mastery_order_sequence",
    "activation_step", "end_state_found_step", "end_state_banked",
    "time_to_first_transition", "time_to_final_transition",
    "transition_order_sequence",
    "knowledge_banked_sequence",
    # v1.5 prediction-error summary fields
    "yellow_pre_transition_entries",
    "green_pre_transition_entries",
    "unaffiliated_pre_transition_entries",
    "yellow_resolution_window",
    "green_resolution_window",
    "total_prediction_error_events",
    "prediction_error_complete",
]

REPORT_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "query_type", "statement_text",
    "source_type", "source_key", "source_resolves",
]

SUMMARY_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "total_statements", "statements_q1", "statements_q2", "statements_q3",
    "hallucination_count",
    "q1_formation_depth", "q3_surprise_cells", "q3_resolution_stated",
    "report_complete",
]

# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

def load_seeds(path):
    """Load seeds from run_data_v1_5.csv at num_steps=320000."""
    seeds = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if int(row["num_steps"]) == BATCH_STEPS:
                    key = (float(row["hazard_cost"]), int(row["run_idx"]))
                    seeds[key] = int(row["seed"])
            except (ValueError, KeyError):
                continue
    return seeds


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def run_one(run_idx, seed, hazard_cost, report=True):
    """Execute one complete run and return (run_row, statements, summary)."""
    np.random.seed(seed)

    world = V17World(hazard_cost=hazard_cost, seed=seed)
    agent = V17Agent(world, total_steps=BATCH_STEPS, num_actions=NUM_ACTIONS)

    meta = {
        "arch":        ARCH,
        "hazard_cost": hazard_cost,
        "num_steps":   BATCH_STEPS,
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
    comparison_obs = V14ComparisonObserver(family_obs, meta)
    pe_obs        = V15PredictionErrorObserver(agent, world, meta)

    observers = [prov_obs, schema_obs, family_obs, comparison_obs, pe_obs]

    # Run loop
    state = world.observe()
    for step in range(BATCH_STEPS):
        for obs in observers:
            obs.on_pre_action(step)

        action = agent.choose_action(state)
        obs_next, contact_oid, moved, cost = world.step(action)

        agent.record_action_outcome(contact_oid, moved or contact_oid is not None, cost, world, step)

        for obs in observers:
            obs.on_post_event(step)

        # Q-value update
        intrinsic = (
            agent.novelty_reward(state)
            + agent.preference_reward(state)
            + agent.feature_reward(state)
        )
        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)

        state = obs_next

    # Run end
    for obs in observers:
        obs.on_run_end(BATCH_STEPS)

    # Assemble run row
    pe_summary = pe_obs.summary_metrics()
    run_row = {
        "arch":                    ARCH,
        "run_idx":                 run_idx,
        "seed":                    seed,
        "hazard_cost":             hazard_cost,
        "num_steps":               BATCH_STEPS,
        "phase_1_end_step":        agent.phase_1_end_step,
        "phase_2_end_step":        agent.phase_2_end_step,
        "time_to_first_flag":      agent.time_to_first_flag,
        "time_to_second_flag":     agent.time_to_second_flag,
        "time_to_final_flag":      agent.time_to_final_flag,
        "total_cost_incurred":     agent.total_cost_incurred,
        "time_to_first_mastery":   agent.time_to_first_mastery,
        "time_to_final_mastery":   agent.time_to_final_mastery,
        "mastery_order_sequence":  str(agent.mastery_order_sequence),
        "activation_step":         agent.activation_step,
        "end_state_found_step":    agent.end_state_found_step,
        "end_state_banked":        agent.end_state_banked,
        "time_to_first_transition": agent.time_to_first_transition,
        "time_to_final_transition": agent.time_to_final_transition,
        "transition_order_sequence": str(agent.transition_order_sequence),
        "knowledge_banked_sequence": str(agent.knowledge_banked_sequence),
        **pe_summary,
    }

    # Build SubstrateBundle and reporting layer
    statements = []
    summary = {}
    if report:
        bundle = build_bundle_from_observers(
            provenance_obs=prov_obs,
            schema_obs=schema_obs,
            family_obs=family_obs,
            comparison_obs=comparison_obs,
            prediction_error_obs=pe_obs,
            run_meta=meta,
        )
        layer = V16ReportingLayer(bundle)
        statements = layer.generate_report()
        summary = _compute_summary(run_idx, seed, hazard_cost, statements)

    return run_row, statements, summary, prov_obs


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def _compute_summary(run_idx, seed, hazard_cost, statements):
    stmts_q1 = [s for s in statements if s.query_type == "what_learned"]
    stmts_q2 = [s for s in statements if s.query_type == "how_related"]
    stmts_q3 = [s for s in statements if s.query_type == "where_surprised"]
    hallucinations = sum(1 for s in statements if not s.source_resolves)

    q1_prov_keys = {
        s.source_key for s in stmts_q1 if s.source_type == "provenance"
    }
    q3_cells = set()
    q3_resolved = 0
    for s in stmts_q3:
        if s.source_type == "prediction_error" and s.source_resolves:
            q3_cells.add(s.source_key)
            if "resolution window" in s.text.lower():
                q3_resolved += 1

    return {
        "arch":                ARCH,
        "run_idx":             run_idx,
        "seed":                seed,
        "hazard_cost":         hazard_cost,
        "num_steps":           BATCH_STEPS,
        "total_statements":    len(statements),
        "statements_q1":       len(stmts_q1),
        "statements_q2":       len(stmts_q2),
        "statements_q3":       len(stmts_q3),
        "hallucination_count": hallucinations,
        "q1_formation_depth":  len(q1_prov_keys),
        "q3_surprise_cells":   len(q3_cells),
        "q3_resolution_stated": q3_resolved,
        "report_complete": (
            len(stmts_q1) > 0
            and len(stmts_q2) > 0
            and len(stmts_q3) > 0
            and hallucinations == 0
        ),
    }


# ---------------------------------------------------------------------------
# Category γ
# ---------------------------------------------------------------------------

def _edit_distance_normalised(seq_a, seq_b):
    if not seq_a and not seq_b:
        return 0.0
    n, m = len(seq_a), len(seq_b)
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, m + 1):
            temp = dp[j]
            if seq_a[i - 1] == seq_b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[m] / max(n, m)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-report", action="store_true",
                        help="Skip reporting layer (run simulations only)")
    args = parser.parse_args()
    report = not args.no_report

    if not os.path.exists(SEED_CSV):
        print(f"ERROR: seed file not found: {SEED_CSV}")
        sys.exit(1)

    seeds = load_seeds(SEED_CSV)
    if not seeds:
        print(f"ERROR: no 320k seeds found in {SEED_CSV}.")
        sys.exit(1)

    # Build job list
    jobs = []
    for cost in HAZARD_COSTS:
        for run_idx in range(RUNS_PER_COST):
            seed = seeds.get((cost, run_idx))
            if seed is None:
                print(f"WARNING: no seed for cost={cost} run_idx={run_idx}; skipping.")
                continue
            jobs.append((run_idx, seed, cost))

    print(f"v1.7 Batch — 3D continuous-space substrate")
    print(f"  Substrate:    V17World (continuous 3D)")
    print(f"  Agent:        V17Agent (inherited cognitive stack)")
    print(f"  Reporting:    {'enabled' if report else 'disabled'}")
    print(f"  Total runs:   {len(jobs)}")
    print()

    total_hallucinations = 0
    total_statements     = 0
    incomplete_runs      = []
    q1_sequences         = {}

    with (
        open(RUN_DATA_CSV,   "w", newline="") as rd_f,
        open(PROVENANCE_CSV, "w", newline="") as pv_f,
        open(REPORT_CSV,     "w", newline="") as rep_f,
        open(REPORT_SUMMARY_CSV, "w", newline="") as sum_f,
    ):
        rd_writer  = csv.DictWriter(rd_f,  fieldnames=RUN_DATA_FIELDS)
        rep_writer = csv.DictWriter(rep_f, fieldnames=REPORT_FIELDS)
        sum_writer = csv.DictWriter(sum_f, fieldnames=SUMMARY_FIELDS)
        rd_writer.writeheader()
        rep_writer.writeheader()
        sum_writer.writeheader()

        for run_idx, seed, hazard_cost in jobs:
            try:
                run_row, statements, summary, prov_obs = run_one(
                    run_idx, seed, hazard_cost, report=report
                )
            except Exception as e:
                import traceback
                print(f"  Run {run_idx} cost={hazard_cost}: ERROR — {e}")
                traceback.print_exc()
                incomplete_runs.append((run_idx, hazard_cost))
                continue

            rd_writer.writerow(
                {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
            )
            # Amendment 1 Fix 3: flush provenance records to CSV
            flush_provenance_csv(
                prov_obs, PROVENANCE_CSV,
                first_run=(run_idx == jobs[0][0] and hazard_cost == jobs[0][2])
            )

            if report:
                for stmt in statements:
                    rep_writer.writerow({
                        "arch":            ARCH,
                        "run_idx":         run_idx,
                        "seed":            seed,
                        "hazard_cost":     hazard_cost,
                        "num_steps":       BATCH_STEPS,
                        "query_type":      stmt.query_type,
                        "statement_text":  stmt.text,
                        "source_type":     stmt.source_type,
                        "source_key":      stmt.source_key,
                        "source_resolves": stmt.source_resolves,
                    })
                sum_writer.writerow(summary)

                run_halluc = summary["hallucination_count"]
                total_hallucinations += run_halluc
                total_statements     += summary["total_statements"]
                if not summary["report_complete"]:
                    incomplete_runs.append((run_idx, hazard_cost))

                q1_keys = [
                    s.source_key for s in statements
                    if s.query_type == "what_learned"
                    and s.source_type == "provenance"
                ]
                q1_sequences[run_idx] = q1_keys

                status = "PASS" if run_halluc == 0 else f"FAIL({run_halluc})"
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"stmts={summary['total_statements']:3d} | "
                    f"halluc={status}"
                )
            else:
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"mastery={run_row.get('time_to_final_mastery', 'None')}"
                )

    # --- Category γ ---
    if report and len(q1_sequences) >= 2:
        print()
        print("Category γ: biographical individuation")
        run_ids = sorted(q1_sequences.keys())
        distances = []
        for i in range(len(run_ids)):
            for j in range(i + 1, len(run_ids)):
                d = _edit_distance_normalised(
                    q1_sequences[run_ids[i]],
                    q1_sequences[run_ids[j]],
                )
                distances.append(d)
        min_d  = min(distances)
        max_d  = max(distances)
        mean_d = sum(distances) / len(distances)
        floor  = 0.05
        passed = min_d >= floor
        print(f"  Pairwise Q1 distances: n={len(distances)}")
        print(f"  min={min_d:.4f}  mean={mean_d:.4f}  max={max_d:.4f}")
        print(f"  Category γ floor: {floor}")
        print(f"  Category γ: {'PASS' if passed else 'FAIL'}")

    # --- Batch summary ---
    print()
    print("=" * 60)
    print(f"Batch complete.")
    print(f"  Runs processed: {len(jobs) - len(incomplete_runs)} / {len(jobs)}")
    if report:
        print(f"  Total statements:     {total_statements}")
        print(f"  Total hallucinations: {total_hallucinations}")
        alpha_pass = total_hallucinations == 0
        beta_pass  = len(incomplete_runs) == 0
        print(f"  Category α: {'PASS' if alpha_pass else 'FAIL'}")
        print(f"  Category β: {'PASS' if beta_pass else 'FAIL'}")

    if incomplete_runs:
        print(f"  Incomplete runs: {incomplete_runs}")


if __name__ == "__main__":
    main()
