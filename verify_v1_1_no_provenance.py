"""
verify_v1_1_no_provenance.py
----------------------------
v1.1 pre-flight verification, level 2: byte-identical preservation
against v1.0 baseline with v1.0 instrumentation ENABLED but v1.1
provenance DISABLED.

This is the permanent regression test required by v1.1 pre-registration
§6. It catches future drift if subsequent iterations (v1.2 and beyond)
accidentally couple the v1.0 instrumentation to v1.1 provenance state,
or if the v1.1 provenance store somehow modifies agent behaviour
through some side effect not visible at the v0.14-vs-v1.1-disabled
level.

The level-1 verification (verify_v1_1_disabled.py) is a stronger test
of the agent itself. The level-2 verification is specifically about
the parallel-observer pattern: does running v1.0 instrumentation under
the v1.1 batch runner produce the same output as running v1.0
instrumentation under the v1.0 batch runner? It must.

Required artefact: run_data_v1_0.csv (v1.0 baseline).

Usage:
    python3 verify_v1_1_no_provenance.py
    python3 verify_v1_1_no_provenance.py --cost 1.0 --steps 20000 --runs 10
"""

import argparse
import csv
import os
import sys

from curiosity_agent_v1_1_batch import run_one


# v1.0 metric fields that should match v1.0 baseline. The v1.0 baseline
# CSV adds snapshot_count to the v0.14 fields; we include it here so
# this regression test is genuinely v1.0-vs-v1.0.
V10_BASELINE_FIELDS = [
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
]


def _normalise(v):
    if v is None or v == "":
        return ""
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=str, default="run_data_v1_0.csv",
                    help="v1.0 baseline CSV to compare against.")
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
            if r.get("arch") != "v1_0":
                continue
            try:
                key = (float(r["hazard_cost"]),
                       int(r["num_steps"]),
                       int(r["run_idx"]))
                baseline[key] = r
            except (ValueError, KeyError):
                continue

    print("v1.1 PRE-FLIGHT VERIFICATION (level 2, permanent regression)")
    print("  Comparison: v1.1 with --no-provenance vs v1.0 baseline")
    print(f"  Baseline:   {args.baseline}")
    print(f"  Costs:      {args.cost}")
    print(f"  Run lens:   {args.steps}")
    print(f"  Runs/cell:  {args.runs}")
    print()

    total = 0
    matches = 0
    failures = []

    for cost in args.cost:
        for steps in args.steps:
            for run_idx in range(args.runs):
                key = (cost, steps, run_idx)
                if key not in baseline:
                    continue
                seed = int(baseline[key]["seed"])
                metrics, _, _ = run_one(
                    cost, steps, seed, run_idx,
                    instrument=True,
                    record_provenance=False,
                )
                total += 1
                run_failures = []
                for field in V10_BASELINE_FIELDS:
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
    print(f"Verification: {matches} of {total} runs match v1.0 baseline.")
    if failures:
        print(f"FAIL: {len(failures)} runs diverge from baseline.")
        print("This is a regression: v1.1 provenance disabled has "
              "produced different output than v1.0.")
        sys.exit(1)
    print("PASS: v1.1 with provenance disabled is byte-identical "
          "to v1.0.")
    sys.exit(0)


if __name__ == "__main__":
    main()
