"""
verify_v1_6_no_hallucinations.py
----------------------------------
v1.6 Level-8 pre-flight verification.

Before the full 60-run report batch, a single run is processed and
every ReportStatement checked for source_resolves = True. The
internal-consistency characterisation (Category α) requires that
hallucination_count = 0 across all statements. This verification
tests that condition at minimum scale before committing to the full
batch.

The run selected is: cost=1.0, steps=320000, run_idx=0.
Seeds loaded from run_data_v1_5.csv.

Exit 0 = pass (all statements resolve; Category α pre-condition met).
Exit 1 = failure (hallucination found; diagnose before batch).
"""

import csv
import os
import sys

import v1_6_observer_substrates  # noqa: F401 — registers get_substrate()
from v1_6_substrate_bundle import build_bundle_from_csvs
from v1_6_reporting_layer import V16ReportingLayer

RUN_DATA_CSV          = "run_data_v1_5.csv"
PROVENANCE_CSV        = "provenance_v1_5.csv"
SCHEMA_CSV            = "schema_v1_5.csv"
FAMILY_CSV            = "family_v1_5.csv"
COMPARISON_CSV        = "comparison_v1_5.csv"
PREDICTION_ERROR_CSV  = "prediction_error_v1_5.csv"

VERIFICATION_COST     = 1.0
VERIFICATION_STEPS    = 320000
VERIFICATION_RUN_IDX  = 0


def load_seed(path, cost, steps, run_idx):
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if (float(row["hazard_cost"]) == cost
                        and int(row["num_steps"]) == steps
                        and int(row["run_idx"]) == run_idx):
                    return int(row["seed"])
            except (ValueError, KeyError):
                continue
    return None


def main():
    for path in (
        RUN_DATA_CSV, PROVENANCE_CSV, SCHEMA_CSV,
        FAMILY_CSV, COMPARISON_CSV, PREDICTION_ERROR_CSV,
    ):
        if not os.path.exists(path):
            print(f"FAIL: required file not found: {path}")
            sys.exit(1)

    print("v1.6 Level-8 Pre-Flight Verification")
    print("  All ReportStatements must have source_resolves = True.")
    print(f"  Run: cost={VERIFICATION_COST}  steps={VERIFICATION_STEPS}"
          f"  run_idx={VERIFICATION_RUN_IDX}")
    print()

    seed = load_seed(
        RUN_DATA_CSV,
        VERIFICATION_COST,
        VERIFICATION_STEPS,
        VERIFICATION_RUN_IDX,
    )
    if seed is None:
        print(
            f"FAIL: seed not found for cost={VERIFICATION_COST}, "
            f"steps={VERIFICATION_STEPS}, run_idx={VERIFICATION_RUN_IDX}."
        )
        sys.exit(1)

    print(f"  Seed: {seed}")

    bundle = build_bundle_from_csvs(
        run_idx=VERIFICATION_RUN_IDX,
        num_steps=VERIFICATION_STEPS,
        seed=seed,
        provenance_csv=PROVENANCE_CSV,
        schema_csv=SCHEMA_CSV,
        family_csv=FAMILY_CSV,
        comparison_csv=COMPARISON_CSV,
        prediction_error_csv=PREDICTION_ERROR_CSV,
        run_data_csv=RUN_DATA_CSV,
    )

    layer = V16ReportingLayer(bundle)
    statements = layer.generate_report()

    total    = len(statements)
    resolved = sum(1 for s in statements if s.source_resolves)
    hallucinations = [s for s in statements if not s.source_resolves]

    print(f"  Total statements:  {total}")
    print(f"  Resolved:          {resolved}")
    print(f"  Hallucinations:    {len(hallucinations)}")
    print()

    # Print per-query summary
    for qt in ("what_learned", "how_related", "where_surprised"):
        qt_stmts = [s for s in statements if s.query_type == qt]
        print(f"  {qt}: {len(qt_stmts)} statement(s)")

    print()

    if hallucinations:
        print("Level-8 verification FAILED — hallucinations found:")
        for s in hallucinations:
            print(f"  [{s.query_type}] source={s.source_type}:"
                  f"{s.source_key}")
            print(f"    text: {s.text[:120]}")
        print()
        print("Category α failure: diagnose before running v1.6 batch.")
        sys.exit(1)
    else:
        print("Level-8 verification PASSED — 0 hallucinations.")
        print("Category α pre-condition satisfied at single-run scale.")
        print("Proceed to full v1.6 60-run report batch.")
        sys.exit(0)


if __name__ == "__main__":
    main()
