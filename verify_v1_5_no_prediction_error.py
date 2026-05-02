"""
verify_v1_5_no_prediction_error.py
------------------------------------
v1.5 level-6 pre-flight verification.

With --no-prediction-error only, the v1.5 batch runner produces output
byte-identical to the v1.4 baseline at matched seeds on all v1.4 metrics.
This is the permanent level-6 regression test added to the pipeline by v1.5.

The prediction-error observer is the only addition in v1.5. All other
observers (v1.0 recorder, v1.1 provenance, v1.2/v1.3 schema, v1.3 family,
v1.4 comparison), the V15Agent (behaviourally identical to V14Agent),
V13World, and the entire run loop are inherited unchanged. If the v1.5
batch runner produces different v1.4 metrics from the v1.4 baseline when
--no-prediction-error is set, that is a Category α failure and must be
diagnosed before the full v1.5 batch runs.

This script verifies 10 runs at cost=1.0, steps=20000, using seeds from
run_data_v1_4.csv. It compares all v1.4 fields present in both the v1.5
output and the v1.4 baseline.

Exit 0 = pass (all 10 runs match on all v1.4 fields).
Exit 1 = Category α failure (mismatch found; diagnose before proceeding).
"""

import csv
import os
import sys

from curiosity_agent_v1_5_batch import run_one

BASELINE_PATH      = "run_data_v1_4.csv"
VERIFICATION_COST  = 1.0
VERIFICATION_STEPS = 20000
VERIFICATION_RUNS  = 10

# v1.4 fields to verify — all fields present in run_data_v1_4.csv that
# must be byte-identical in v1.5 with --no-prediction-error.
# Excludes "arch" (legitimately changes from v1_4 to v1_5).
V1_4_VERIFY_FIELDS = [
    "hazard_cost", "num_steps", "seed", "run_idx",
    "phase_1_end", "phase_2_end",
    "frame_attempts_p1", "frame_attempts_p2", "frame_attempts_p3",
    "hazard_entries_p1", "hazard_entries_p2", "hazard_entries_p3",
    "total_cost", "mastered_pairs",
    "hazards_flagged", "time_to_first_flag", "time_to_second_flag",
    "time_to_final_flag", "first_entry_conversions", "cost_on_sig_matched",
    "actions_gated_p2", "actions_gated_p3",
    "attractors_mastered", "time_to_first_mastery", "time_to_final_mastery",
    "first_banked", "mastery_sequence",
    "post_mastery_visits_total",
    "p3_visits_to_mastered", "p3_visits_to_unmastered",
    "end_state_cell", "activation_step", "end_state_found_step",
    "end_state_visits", "end_state_banked",
    "post_activation_window", "discovery_time",
    "hazards_transitioned", "hazards_banked_as_knowledge",
    "time_to_first_transition", "time_to_final_transition",
    "transition_order_sequence", "knowledge_banked_sequence",
    "hazard_thresholds", "competency_unlock_steps",
    "knowledge_banked_steps", "knowledge_entries_per_cell",
    "pre_transition_entries_per_cell",
    "snapshot_count",
    # v1.1 provenance fields
    "prov_threat_count", "prov_mastery_count",
    "prov_knowledge_banking_count",
    "prov_end_state_activation_count", "prov_end_state_banking_count",
    "prov_crossref_complete", "prov_crossref_pending",
    "prov_total_records",
    # v1.2 schema fields
    "schema_cell_types_count",
    "schema_actions_count",
    "schema_phases_count",
    "schema_flag_types_count",
    "schema_complete",
    # v1.3 family summary fields
    "green_cell_registered", "green_cell_first_perception_step",
    "yellow_cell_registered", "yellow_cell_first_perception_step",
    "green_attractor_mastered", "green_attractor_mastery_step",
    "yellow_attractor_mastered", "yellow_attractor_mastery_step",
    "green_knowledge_banked", "green_knowledge_banked_step",
    "yellow_knowledge_banked", "yellow_knowledge_banked_step",
    "green_crossref_complete", "yellow_crossref_complete",
    "family_traversal_narrative",
    # v1.4 comparison summary fields
    "tier_structure_similarity",
    "form_progression_parallelism",
    "traversal_sequence_distance",
    "green_traversal_complete",
    "yellow_traversal_complete",
    "both_complete",
    "green_first",
    "traversal_interleaving",
    "cross_family_comparison_complete",
]


def load_baseline_rows(path, cost, steps, n_runs):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                rc   = float(r["hazard_cost"])
                rs   = int(r["num_steps"])
                ridx = int(r["run_idx"])
            except (ValueError, KeyError):
                continue
            if rc == cost and rs == steps and ridx < n_runs:
                rows[ridx] = r
    return rows


def normalise(val):
    if val is None:
        return ""
    return str(val).strip()


def main():
    if not os.path.exists(BASELINE_PATH):
        print(f"FAIL: baseline {BASELINE_PATH} not found.")
        sys.exit(1)

    print("v1.5 Level-6 Pre-Flight Verification")
    print(f"  --no-prediction-error: v1.5 output must match v1.4 baseline")
    print(f"  on all v1.4 metrics at matched seeds.")
    print(f"  Baseline: {BASELINE_PATH}  Cost: {VERIFICATION_COST}"
          f"  Steps: {VERIFICATION_STEPS}  Runs: {VERIFICATION_RUNS}")
    print()

    baseline_rows = load_baseline_rows(
        BASELINE_PATH, VERIFICATION_COST, VERIFICATION_STEPS, VERIFICATION_RUNS
    )
    if len(baseline_rows) < VERIFICATION_RUNS:
        print(f"FAIL: only {len(baseline_rows)} baseline rows found.")
        sys.exit(1)

    failures = []

    for run_idx in range(VERIFICATION_RUNS):
        baseline = baseline_rows[run_idx]
        seed     = int(baseline["seed"])

        (metrics, _, _, _, _, _, _) = run_one(
            hazard_cost=VERIFICATION_COST,
            num_steps=VERIFICATION_STEPS,
            seed=seed,
            run_idx=run_idx,
            instrument=True,
            record_provenance=True,
            record_schema=True,
            record_family=True,
            record_comparison=True,
            record_prediction_error=False,   # level-6: prediction-error disabled
            use_v13_world=True,
        )

        run_failures = []
        for field in V1_4_VERIFY_FIELDS:
            v15_val = normalise(metrics.get(field))
            v14_val = normalise(baseline.get(field))
            if v15_val != v14_val:
                run_failures.append(
                    f"  {field}: v1.5={v15_val!r}  v1.4={v14_val!r}"
                )

        status = "PASS" if not run_failures else "FAIL"
        print(f"  Run {run_idx}: seed={seed}  {status}")
        if run_failures:
            for msg in run_failures:
                print(msg)
            failures.extend(run_failures)

    print()
    if not failures:
        print("Level-6 verification PASSED — 10/10 runs match v1.4 baseline.")
        print("Category α pre-condition satisfied.")
        print("Proceed to full v1.5 batch.")
        sys.exit(0)
    else:
        print(f"Level-6 verification FAILED — {len(failures)} mismatch(es).")
        print("Category α failure: diagnose before running v1.5 batch.")
        sys.exit(1)


if __name__ == "__main__":
    main()
