"""
verify_v1_2_no_schema.py
------------------------
v1.2 pre-flight verification, level 2 (permanent regression test):
byte-identical preservation against v1.1 baseline with v1.0
instrumentation ENABLED, v1.1 provenance ENABLED, and v1.2 schema
DISABLED.

This is the permanent regression test required by v1.2 pre-registration
§4 and §9. It catches future drift if subsequent iterations (v1.3 and
beyond) accidentally couple the v1.0 instrumentation or v1.1 provenance
store to v1.2 schema state, or if V12Agent's __init__ side-effects the
inherited v0.14 behaviour through some path not visible at the
V014Agent level.

The level-1 verification (verify_v1_2_disabled.py) tests that all
three observers together produce bit-for-bit v0.14 output when
disabled. This level-2 test is specifically about the parallel-observer
pattern for v1.2: does running v1.0 + v1.1 observers under the v1.2
batch runner (which uses V12Agent rather than V014Agent) produce the
same output as the v1.1 baseline? It must.

The key question this test answers: does V12Agent's _build_schema()
call at __init__ time affect any inherited behavioural state? It must
not. If this test passes, V12Agent is behaviourally identical to
V014Agent at matched seeds.

Required artefact: run_data_v1_1.csv (v1.1 baseline).

Usage:
    python3 verify_v1_2_no_schema.py
    python3 verify_v1_2_no_schema.py --cost 1.0 --steps 20000 --runs 10
"""

import argparse
import csv
import os
import sys

from curiosity_agent_v1_2_batch import run_one


# v1.1 metric fields that should match v1.1 baseline exactly.
# These are all fields present in run_data_v1_1.csv, including
# the v1.1 provenance aggregate fields. The v1.2 schema summary
# fields (schema_*) are excluded from this comparison by definition —
# they are the new fields v1.2 introduces and have no v1.1 baseline
# counterpart.
V11_BASELINE_FIELDS = [
    "phase_1_end", "phase_2_end",
    "frame_attempts_p1", "frame_attempts_p2", "frame_attempts_p3",
    "hazard_entries_p1", "hazard_entries_p2", "hazard_entries_p3",
    "total_cost", "mastered_pairs", "top_attractor", "top_attractor_pref",
    "phase_3_clean", "full_run_clean",
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
    "prov_threat_count", "prov_threat_mean_set_step",
    "prov_threat_mean_confirming", "prov_threat_mean_disconfirming",
    "prov_mastery_count", "prov_mastery_mean_set_step",
    "prov_mastery_mean_confirming", "prov_mastery_mean_disconfirming",
    "prov_knowledge_banking_count", "prov_knowledge_banking_mean_set_step",
    "prov_knowledge_banking_mean_confirming",
    "prov_knowledge_banking_mean_disconfirming",
    "prov_end_state_activation_count",
    "prov_end_state_activation_mean_set_step",
    "prov_end_state_activation_mean_confirming",
    "prov_end_state_activation_mean_disconfirming",
    "prov_end_state_banking_count",
    "prov_end_state_banking_mean_set_step",
    "prov_end_state_banking_mean_confirming",
    "prov_end_state_banking_mean_disconfirming",
    "prov_crossref_complete", "prov_crossref_pending",
    "prov_formation_narrative", "prov_total_records",
]


def _normalise(v):
    if v is None or v == "":
        return ""
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=str, default="run_data_v1_1.csv",
                    help="v1.1 baseline CSV to compare against.")
    ap.add_argument("--cost", type=float, nargs="+",
                    default=[1.0],
                    help="Cost levels to verify (default: 1.0 only).")
    ap.add_argument("--steps", type=int, nargs="+",
                    default=[20000],
                    help="Run lengths to verify (default: 20000 only).")
    ap.add_argument("--runs", type=int, default=10,
                    help="Runs per cost-by-steps cell (default: 10).")
    args = ap.parse_args()

    if not os.path.exists(args.baseline):
        print(f"FAIL: baseline {args.baseline} not found.")
        sys.exit(2)

    baseline = {}
    with open(args.baseline) as f:
        for r in csv.DictReader(f):
            if r.get("arch") != "v1_1":
                continue
            try:
                key = (float(r["hazard_cost"]),
                       int(r["num_steps"]),
                       int(r["run_idx"]))
                baseline[key] = r
            except (ValueError, KeyError):
                continue

    print("v1.2 PRE-FLIGHT VERIFICATION (level 2, permanent regression)")
    print("  Comparison: v1.2 with --no-schema vs v1.1 baseline")
    print(f"  Baseline:   {args.baseline}")
    print(f"  Costs:      {args.cost}")
    print(f"  Run lens:   {args.steps}")
    print(f"  Runs/cell:  {args.runs}")
    print()
    print("  NOTE: V12Agent (not V014Agent) is used. This test confirms")
    print("  that V12Agent._build_schema() does not affect any inherited")
    print("  behavioural state. If this passes, the schema is a true")
    print("  additive structure with no behavioural side-effects.")
    print()

    total = 0
    matches = 0
    failures = []

    for cost in args.cost:
        for steps in args.steps:
            for run_idx in range(args.runs):
                key = (cost, steps, run_idx)
                if key not in baseline:
                    print(f"  SKIP: key {key} not in baseline")
                    continue
                seed = int(baseline[key]["seed"])
                # run_one with record_schema=False; V12Agent is still used
                # (instrument=True, record_provenance=True, record_schema=False).
                metrics, _, _, _ = run_one(
                    cost, steps, seed, run_idx,
                    instrument=True,
                    record_provenance=True,
                    record_schema=False,
                )
                total += 1
                run_failures = []
                for field in V11_BASELINE_FIELDS:
                    expected = _normalise(baseline[key].get(field, ""))
                    actual = _normalise(metrics.get(field, ""))
                    if expected != actual:
                        run_failures.append(
                            f"  {field}: expected={expected!r} "
                            f"actual={actual!r}"
                        )
                if run_failures:
                    failures.append((key, run_failures))
                    print(f"[{total}] cost={cost} steps={steps} "
                          f"run={run_idx} seed={seed}: FAIL")
                    for line in run_failures:
                        print(line)
                else:
                    matches += 1
                    print(f"[{total}] cost={cost} steps={steps} "
                          f"run={run_idx} seed={seed}: OK")

    print()
    print(f"Verification: {matches} of {total} runs match v1.1 baseline.")
    if failures:
        print(f"FAIL: {len(failures)} runs diverge from baseline.")
        print("This is a regression: V12Agent with schema disabled has")
        print("produced different output from v1.1. Investigate whether")
        print("_build_schema() modifies inherited agent state, or whether")
        print("V12World differs from V11World at matched seeds.")
        sys.exit(1)
    print("PASS: v1.2 with schema disabled is byte-identical to v1.1.")
    print("V12Agent._build_schema() does not affect inherited behaviour.")
    sys.exit(0)


if __name__ == "__main__":
    main()
