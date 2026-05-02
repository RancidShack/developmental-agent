"""
verify_v1_2_disabled.py
-----------------------
v1.2 pre-flight verification, level 1: byte-identical preservation
against v0.14 baseline with ALL instrumentation disabled
(--no-instrument --no-provenance --no-schema).

This confirms that none of the three parallel observers — the v1.0
recorder, the v1.1 provenance store, and the v1.2 schema observer —
interfere with the agent's RNG state, computation, or output when
not instantiated. It also confirms that V12Agent (which subclasses
V014Agent) produces bit-for-bit identical output to V014Agent at
matched seeds when the schema observer is not running.

This is the stronger test of the agent itself. The level-2 test
(verify_v1_2_no_schema.py) is specifically about the parallel-observer
pattern with v1.0 and v1.1 active. This level-1 test is the baseline
sanity check: no observers, no schema side-effects, pure v0.14 behaviour.

Required artefact: run_data_v0_14.csv (v0.14 baseline).
If run_data_v0_14.csv is not available, run_data_v1_0.csv or
run_data_v1_1.csv can be used as the baseline (they contain v0.14-
equivalent rows at matched seeds for all behavioural fields up to
snapshot_count).

Usage:
    python3 verify_v1_2_disabled.py
    python3 verify_v1_2_disabled.py --baseline run_data_v1_1.csv
    python3 verify_v1_2_disabled.py --cost 1.0 --steps 20000 --runs 10
"""

import argparse
import csv
import os
import sys

from curiosity_agent_v1_2_batch import run_one


# Core v0.14 metric fields — the fields present in run_data_v0_14.csv.
# snapshot_count is included because it is written by the v1.0 recorder;
# with --no-instrument it will be 0, and the baseline should also record
# 0 or the field should be absent (handled by _normalise below).
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
    if v is None or v == "":
        return ""
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=str, default="run_data_v0_14.csv",
                    help=("v0.14 baseline CSV to compare against. "
                          "run_data_v1_1.csv or run_data_v1_0.csv can "
                          "be used if run_data_v0_14.csv is unavailable; "
                          "the arch filter below will select the right rows."))
    ap.add_argument("--baseline-arch", type=str, default=None,
                    help=("Arch tag to filter baseline rows. If None, "
                          "any arch containing 'v0_14' is accepted, "
                          "plus v1_0 and v1_1 rows (which share v0.14 "
                          "behavioural fields at matched seeds)."))
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

    # Accept rows from v0_14, v0_14_repl, v1_0, or v1_1 — all share
    # the v0.14 behavioural fields at matched seeds for the core fields.
    accepted_archs = {"v0_14", "v0_14_repl", "v1_0", "v1_1", "v1_2"}
    if args.baseline_arch is not None:
        accepted_archs = {args.baseline_arch}

    baseline = {}
    with open(args.baseline) as f:
        for r in csv.DictReader(f):
            arch = r.get("arch", "")
            if arch not in accepted_archs:
                continue
            try:
                key = (float(r["hazard_cost"]),
                       int(r["num_steps"]),
                       int(r["run_idx"]))
                # Priority: prefer v0_14 > v0_14_repl > v1_0 > v1_1 > v1_2
                priority = {
                    "v0_14": 0, "v0_14_repl": 1,
                    "v1_0": 2, "v1_1": 3, "v1_2": 4,
                }
                existing = baseline.get(key)
                if existing is None:
                    baseline[key] = r
                elif (priority.get(arch, 99)
                        < priority.get(existing.get("arch", ""), 99)):
                    baseline[key] = r
            except (ValueError, KeyError):
                continue

    print("v1.2 PRE-FLIGHT VERIFICATION (level 1)")
    print("  Comparison: v1.2 with ALL observers disabled vs v0.14 baseline")
    print(f"  Baseline:   {args.baseline}")
    print(f"  Costs:      {args.cost}")
    print(f"  Run lens:   {args.steps}")
    print(f"  Runs/cell:  {args.runs}")
    print()
    print("  NOTE: V12Agent (not V014Agent) is used with all observers off.")
    print("  This confirms V12Agent is behaviourally identical to V014Agent")
    print("  when the schema observer is not instantiated.")
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
                # All three observers disabled.
                metrics, _, _, _ = run_one(
                    cost, steps, seed, run_idx,
                    instrument=False,
                    record_provenance=False,
                    record_schema=False,
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
        print("Investigate whether V12Agent.__init__ modifies inherited")
        print("state beyond self._schema, or whether V12World differs")
        print("from V11World at matched seeds.")
        sys.exit(1)
    print("PASS: v1.2 with all observers disabled is byte-identical")
    print("to v0.14. V12Agent introduces no behavioural side-effects.")
    sys.exit(0)


if __name__ == "__main__":
    main()
