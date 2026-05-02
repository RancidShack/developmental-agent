"""
verify_v1_3_no_family.py
-------------------------
v1.3.2 pre-flight verification (amended per v1.3.2 amendment).

Level 4 is now an internal consistency check rather than byte-identical
comparison, because V13Agent overrides check_competency_unlocks and
v1.3.2 behaviour is not byte-identical to v1.2 at matched seeds.

Checks:
  (a) Observer fields (provenance counts, schema counts excluding
      cell_types_count/schema_complete) match v1.2 baseline.
  (b) No family hazard cell transitions before its precondition
      attractor is mastered (checked in production batch mode).

Exit 0 = pass. Exit 1 = Category alpha failure.
"""

import csv
import os
import sys

from curiosity_agent_v1_3_batch import run_one

BASELINE_PATH      = "run_data_v1_2.csv"
VERIFICATION_COST  = 1.0
VERIFICATION_STEPS = 20000
VERIFICATION_RUNS  = 10

# Observer fields stable across v1.2 -> v1.3.2 (not affected by gating change)
V1_2_OBSERVER_FIELDS = [
    "hazard_cost", "num_steps", "seed", "run_idx",
    "phase_1_end", "phase_2_end",
    "frame_attempts_p1", "frame_attempts_p2", "frame_attempts_p3",
    "prov_threat_count", "prov_mastery_count",
    "prov_knowledge_banking_count",
    "prov_end_state_activation_count", "prov_end_state_banking_count",
    "prov_crossref_complete", "prov_crossref_pending",
    "prov_total_records",
    "schema_actions_count",
    "schema_phases_count",
    "schema_flag_types_count",
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

    print("v1.3.2 Level-4 Pre-Flight Verification")
    print(f"  V13Agent overrides check_competency_unlocks.")
    print(f"  Level 4 verifies observer consistency, not byte-identity.")
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

        metrics, _, _, _, _ = run_one(
            hazard_cost=VERIFICATION_COST,
            num_steps=VERIFICATION_STEPS,
            seed=seed,
            run_idx=run_idx,
            instrument=True,
            record_provenance=True,
            record_schema=True,
            record_family=False,
            use_v13_world=False,
        )

        run_failures = []
        for field in V1_2_OBSERVER_FIELDS:
            v13_val = normalise(metrics.get(field))
            v12_val = normalise(baseline.get(field))
            if v13_val != v12_val:
                run_failures.append(
                    f"  {field}: v1.3.2={v13_val!r}  v1.2={v12_val!r}"
                )

        status = "PASS" if not run_failures else "FAIL"
        print(f"  Run {run_idx}: seed={seed}  {status}")
        if run_failures:
            for msg in run_failures:
                print(msg)
            failures.extend(run_failures)

    print()
    if not failures:
        print("Level-4 verification PASSED — 10/10 runs clean.")
        print("Category α pre-condition satisfied.")
        sys.exit(0)
    else:
        print(f"Level-4 verification FAILED — {len(failures)} mismatch(es).")
        print("Category α failure: diagnose before running v1.3.2 batch.")
        sys.exit(1)


if __name__ == "__main__":
    main()
