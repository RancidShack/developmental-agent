"""
verify_v1_6_substrate.py
-------------------------
v1.6 Level-7 pre-flight verification.

The SubstrateBundle reconstructed from v1.5 CSVs must match
summary_metrics() from the original v1.5 observer outputs at matched
seeds on all fields present in both. This confirms that the
get_substrate() -> SubstrateBundle -> build_bundle_from_csvs pipeline
preserves the substrate without loss or distortion.

This script verifies 10 runs at cost=1.0, steps=20000, using seeds from
run_data_v1_5.csv. For each run it:

  1. Runs the agent via curiosity_agent_v1_5_batch.run_one() to obtain
     live observer instances.
  2. Builds a SubstrateBundle from live observers via
     build_bundle_from_observers().
  3. Builds a SubstrateBundle from CSVs via build_bundle_from_csvs().
  4. Compares the two bundles on all fields present in summary_metrics()
     for each observer.

A mismatch on any field is a Category α failure for v1.6 and must be
diagnosed before the full 60-run report batch runs.

Exit 0 = pass (10/10 runs, all fields match on both bundle sources).
Exit 1 = failure (mismatch found; diagnose before proceeding).
"""

import csv
import os
import sys

# v1.6 substrate imports
import v1_6_observer_substrates  # noqa: F401 — registers get_substrate()
from v1_6_substrate_bundle import (
    build_bundle_from_observers,
    build_bundle_from_csvs,
)

# v1.5 batch runner
from curiosity_agent_v1_5_batch import run_one

RUN_DATA_CSV          = "run_data_v1_5.csv"
PROVENANCE_CSV        = "provenance_v1_5.csv"
SCHEMA_CSV            = "schema_v1_5.csv"
FAMILY_CSV            = "family_v1_5.csv"
COMPARISON_CSV        = "comparison_v1_5.csv"
PREDICTION_ERROR_CSV  = "prediction_error_v1_5.csv"

VERIFICATION_COST     = 1.0
VERIFICATION_STEPS    = 20000
VERIFICATION_RUNS     = 10


def load_seeds(path, cost, steps, n_runs):
    seeds = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                rc   = float(row["hazard_cost"])
                rs   = int(row["num_steps"])
                ridx = int(row["run_idx"])
            except (ValueError, KeyError):
                continue
            if rc == cost and rs == steps and ridx < n_runs:
                seeds[ridx] = int(row["seed"])
    return seeds


def normalise(val):
    if val is None:
        return ""
    return str(val).strip()


def compare_provenance(live_bundle, csv_bundle, run_idx):
    """Compare provenance substrates field by field."""
    failures = []

    live_keys = set(live_bundle.provenance.keys())
    csv_keys  = set(csv_bundle.provenance.keys())

    if live_keys != csv_keys:
        failures.append(
            f"  provenance keys differ: "
            f"live={sorted(live_keys)} csv={sorted(csv_keys)}"
        )
        return failures

    for flag_id in sorted(live_keys):
        lr = live_bundle.provenance[flag_id]
        cr = csv_bundle.provenance[flag_id]

        for attr in (
            "flag_type", "flag_coord_str", "flag_id",
            "flag_set_step", "confirming_observations",
            "disconfirming_observations",
            "last_confirmation_step", "last_observation_step",
            "transformed_at_step",
            "derived_knowledge_flag_id",
            "derived_from_threat_flag_id",
        ):
            lv = normalise(getattr(lr, attr, None))
            cv = normalise(getattr(cr, attr, None))
            if lv != cv:
                failures.append(
                    f"  provenance[{flag_id}].{attr}: "
                    f"live={lv!r} csv={cv!r}"
                )

    return failures


def compare_flat(name, live_sub, csv_sub, run_idx, skip_keys=None):
    """Compare two flat dicts (schema, family, comparison)."""
    failures = []
    skip = set(skip_keys or [])

    if live_sub is None and csv_sub is None:
        return failures
    if live_sub is None or csv_sub is None:
        failures.append(
            f"  {name}: one is None — live={live_sub is None} "
            f"csv={csv_sub is None}"
        )
        return failures

    all_keys = set(live_sub.keys()) | set(csv_sub.keys())
    for k in sorted(all_keys):
        if k in skip:
            continue
        lv = normalise(live_sub.get(k))
        cv = normalise(csv_sub.get(k))
        if lv != cv:
            failures.append(
                f"  {name}[{k!r}]: live={lv!r} csv={cv!r}"
            )
    return failures


def compare_prediction_error(live_bundle, csv_bundle, run_idx):
    """Compare prediction_error encounter lists."""
    failures = []
    ll = live_bundle.prediction_error
    cl = csv_bundle.prediction_error

    if len(ll) != len(cl):
        failures.append(
            f"  prediction_error length: live={len(ll)} csv={len(cl)}"
        )
        return failures

    for i, (le, ce) in enumerate(zip(ll, cl)):
        for k in sorted(set(le.keys()) | set(ce.keys())):
            lv = normalise(le.get(k))
            cv = normalise(ce.get(k))
            if lv != cv:
                failures.append(
                    f"  prediction_error[{i}][{k!r}]: "
                    f"live={lv!r} csv={cv!r}"
                )

    return failures


def main():
    for path in (
        RUN_DATA_CSV, PROVENANCE_CSV, SCHEMA_CSV,
        FAMILY_CSV, COMPARISON_CSV, PREDICTION_ERROR_CSV,
    ):
        if not os.path.exists(path):
            print(f"FAIL: required file not found: {path}")
            sys.exit(1)

    print("v1.6 Level-7 Pre-Flight Verification")
    print("  SubstrateBundle from live observers must match")
    print("  SubstrateBundle from CSVs at matched seeds.")
    print(f"  Cost: {VERIFICATION_COST}  Steps: {VERIFICATION_STEPS}"
          f"  Runs: {VERIFICATION_RUNS}")
    print()

    seeds = load_seeds(
        RUN_DATA_CSV, VERIFICATION_COST,
        VERIFICATION_STEPS, VERIFICATION_RUNS,
    )
    if len(seeds) < VERIFICATION_RUNS:
        print(f"FAIL: only {len(seeds)} seeds found in {RUN_DATA_CSV}.")
        sys.exit(1)

    all_failures = []

    for run_idx in range(VERIFICATION_RUNS):
        seed = seeds[run_idx]

        # --- Run agent to get live observers ---
        (metrics, recorder, provenance, schema_obs,
         family_obs, comparison_obs, prediction_error_obs) = run_one(
            hazard_cost=VERIFICATION_COST,
            num_steps=VERIFICATION_STEPS,
            seed=seed,
            run_idx=run_idx,
            instrument=True,
            record_provenance=True,
            record_schema=True,
            record_family=True,
            record_comparison=True,
            record_prediction_error=True,
            use_v13_world=True,
        )

        run_meta = {
            "arch":        "v1_5",
            "hazard_cost": VERIFICATION_COST,
            "num_steps":   VERIFICATION_STEPS,
            "run_idx":     run_idx,
            "seed":        seed,
        }

        live_bundle = build_bundle_from_observers(
            provenance_obs=provenance,
            schema_obs=schema_obs,
            family_obs=family_obs,
            comparison_obs=comparison_obs,
            prediction_error_obs=prediction_error_obs,
            run_meta=run_meta,
        )

        csv_bundle = build_bundle_from_csvs(
            run_idx=run_idx,
            num_steps=VERIFICATION_STEPS,
            seed=seed,
            provenance_csv=PROVENANCE_CSV,
            schema_csv=SCHEMA_CSV,
            family_csv=FAMILY_CSV,
            comparison_csv=COMPARISON_CSV,
            prediction_error_csv=PREDICTION_ERROR_CSV,
            run_data_csv=RUN_DATA_CSV,
        )

        run_failures = []
        run_failures += compare_provenance(live_bundle, csv_bundle, run_idx)
        run_failures += compare_flat(
            "schema", live_bundle.schema, csv_bundle.schema,
            run_idx,
            skip_keys=["arch"],   # arch tag may differ v1_5 vs literal
        )
        run_failures += compare_flat(
            "family", live_bundle.family, csv_bundle.family, run_idx,
        )
        run_failures += compare_flat(
            "comparison", live_bundle.comparison, csv_bundle.comparison,
            run_idx,
        )
        run_failures += compare_prediction_error(
            live_bundle, csv_bundle, run_idx,
        )

        status = "PASS" if not run_failures else "FAIL"
        print(f"  Run {run_idx}: seed={seed}  {status}")
        if run_failures:
            for msg in run_failures:
                print(msg)
        all_failures.extend(run_failures)

    print()
    if not all_failures:
        print("Level-7 verification PASSED — 10/10 runs match on all "
              "substrate fields.")
        print("SubstrateBundle reconstruction pipeline is lossless.")
        print("Proceed to Level-8 verification.")
        sys.exit(0)
    else:
        print(f"Level-7 verification FAILED — {len(all_failures)} "
              f"mismatch(es).")
        print("Diagnose before running the v1.6 report batch.")
        sys.exit(1)


if __name__ == "__main__":
    main()
