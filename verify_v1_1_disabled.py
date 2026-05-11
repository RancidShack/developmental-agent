"""
verify_v1_1_disabled.py
-----------------------
v1.1 pre-flight verification, level 1: byte-identical preservation
against v0.14 baseline with both v1.0 instrumentation AND v1.1
provenance disabled.

This is the strongest preservation test: with all instrumentation
suppressed, the v1.1 batch runner must produce v0.14-identical
output at matched seeds. The agent and world are unmodified; this
verification confirms that the parallel observer modules genuinely
do not interfere with the agent's RNG state, computation, or output
when not instantiated.

Required artefact: run_data_v0_14.csv (v0.14 baseline).

Usage:
    python3 verify_v1_1_disabled.py
    python3 verify_v1_1_disabled.py --cost 1.0 --steps 20000 --runs 10
"""

import argparse
import csv
import os
import sys

from curiosity_agent_v1_1_batch import run_one


# v0.14 baseline metric fields. Provenance fields are not present in
# v0.14 baseline and so are excluded from this comparison.
V014_BASELINE_FIELDS = [
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
]


def _normalise(v):
    """Coerce CSV-read values to a canonical form for comparison."""
    if v is None or v == "":
        return ""
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=str, default="run_data_v0_14.csv",
                    help="v0.14 baseline CSV to compare against.")
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
            if r.get("arch") not in ("v0_14", "v0_14_repl"):
                continue
            try:
                key = (float(r["hazard_cost"]),
                       int(r["num_steps"]),
                       int(r["run_idx"]))
                baseline[key] = r
            except (ValueError, KeyError):
                continue

    print("v1.1 PRE-FLIGHT VERIFICATION (level 1)")
    print("  Comparison: v1.1 with --no-instrument --no-provenance "
          "vs v0.14 baseline")
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
                    instrument=False,
                    record_provenance=False,
                )
                total += 1
                run_failures = []
                for field in V014_BASELINE_FIELDS:
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
    print(f"Verification: {matches} of {total} runs match v0.14 baseline.")
    if failures:
        print(f"FAIL: {len(failures)} runs diverge from baseline.")
        sys.exit(1)
    print("PASS: v1.1 with all instrumentation disabled is "
          "byte-identical to v0.14.")
    sys.exit(0)


if __name__ == "__main__":
    main()
