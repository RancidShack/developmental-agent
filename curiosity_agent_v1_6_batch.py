"""
curiosity_agent_v1_6_batch.py
------------------------------
v1.6 batch runner.

No new agent simulations are run. The v1.6 batch reads from the
stored v1.5 observer output files, reconstructs a SubstrateBundle
for each of the 60 complete runs at 320,000 steps, instantiates
V16ReportingLayer, runs all three query types, and writes:

  report_v1_6.csv
    One row per ReportStatement per run.
    Fields: run_idx, seed, hazard_cost, num_steps, query_type,
            statement_text, source_type, source_key, source_resolves.

  report_summary_v1_6.csv
    One row per run.
    Fields: run_idx, seed, hazard_cost, num_steps,
            total_statements, statements_q1, statements_q2,
            statements_q3, hallucination_count,
            q1_formation_depth, q3_surprise_cells,
            q3_resolution_stated, report_complete.

Pre-flight verifications (Levels 7 and 8) must pass before this
batch is run. This script does not re-run those verifications; they
are run separately via verify_v1_6_substrate.py and
verify_v1_6_no_hallucinations.py.

Usage:
    python curiosity_agent_v1_6_batch.py

All paths are relative to the current directory.
"""

import csv
import os
import sys

import v1_6_observer_substrates  # noqa: F401 — registers get_substrate()
from v1_6_substrate_bundle import build_bundle_from_csvs
from v1_6_reporting_layer import V16ReportingLayer

# ---------------------------------------------------------------------------
# Input / output paths
# ---------------------------------------------------------------------------

RUN_DATA_CSV          = "run_data_v1_5.csv"
PROVENANCE_CSV        = "provenance_v1_5.csv"
SCHEMA_CSV            = "schema_v1_5.csv"
FAMILY_CSV            = "family_v1_5.csv"
COMPARISON_CSV        = "comparison_v1_5.csv"
PREDICTION_ERROR_CSV  = "prediction_error_v1_5.csv"

REPORT_CSV            = "report_v1_6.csv"
REPORT_SUMMARY_CSV    = "report_summary_v1_6.csv"

BATCH_STEPS           = 320000

# ---------------------------------------------------------------------------
# Output field lists
# ---------------------------------------------------------------------------

REPORT_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "query_type", "statement_text",
    "source_type", "source_key", "source_resolves",
]

SUMMARY_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "total_statements",
    "statements_q1", "statements_q2", "statements_q3",
    "hallucination_count",
    "q1_formation_depth",
    "q3_surprise_cells",
    "q3_resolution_stated",
    "report_complete",
]


# ---------------------------------------------------------------------------
# Biographical individuation distance
# ---------------------------------------------------------------------------

def _edit_distance_normalised(seq_a, seq_b):
    """Normalised edit distance between two sequences of strings.

    Uses Levenshtein distance. Returns a float in [0, 1].
    Returns 0.0 if both sequences are empty.
    """
    if not seq_a and not seq_b:
        return 0.0
    n, m = len(seq_a), len(seq_b)
    # Standard DP edit distance
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
# Load 320k run identifiers
# ---------------------------------------------------------------------------

def load_320k_runs(path):
    """Return list of (run_idx, seed, hazard_cost) for all 320k runs,
    sorted by (hazard_cost, run_idx)."""
    runs = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if int(row["num_steps"]) == BATCH_STEPS:
                    runs.append((
                        int(row["run_idx"]),
                        int(row["seed"]),
                        float(row["hazard_cost"]),
                    ))
            except (ValueError, KeyError):
                continue
    return sorted(runs, key=lambda r: (r[2], r[0]))


# ---------------------------------------------------------------------------
# Process one run
# ---------------------------------------------------------------------------

def process_run(run_idx, seed, hazard_cost):
    """Build SubstrateBundle, run reporting layer, return statements."""
    bundle = build_bundle_from_csvs(
        run_idx=run_idx,
        num_steps=BATCH_STEPS,
        seed=seed,
        provenance_csv=PROVENANCE_CSV,
        schema_csv=SCHEMA_CSV,
        family_csv=FAMILY_CSV,
        comparison_csv=COMPARISON_CSV,
        prediction_error_csv=PREDICTION_ERROR_CSV,
        run_data_csv=RUN_DATA_CSV,
    )
    layer = V16ReportingLayer(bundle)
    return layer.generate_report(), bundle


# ---------------------------------------------------------------------------
# Compute summary for one run
# ---------------------------------------------------------------------------

def compute_summary(run_idx, seed, hazard_cost, statements):
    stmts_q1 = [s for s in statements if s.query_type == "what_learned"]
    stmts_q2 = [s for s in statements if s.query_type == "how_related"]
    stmts_q3 = [s for s in statements if s.query_type == "where_surprised"]

    hallucinations = sum(1 for s in statements if not s.source_resolves)

    # q1_formation_depth: distinct provenance source_keys in Query 1
    q1_prov_keys = {
        s.source_key for s in stmts_q1
        if s.source_type == "provenance"
    }
    q1_formation_depth = len(q1_prov_keys)

    # q3_surprise_cells: cells that produced at least one PE statement
    # (i.e. statements with source_type = prediction_error)
    q3_cells = set()
    q3_resolved = 0
    for s in stmts_q3:
        if s.source_type == "prediction_error" and s.source_resolves:
            q3_cells.add(s.source_key)
            if "resolution window" in s.text.lower():
                q3_resolved += 1

    report_complete = (
        len(stmts_q1) > 0
        and len(stmts_q2) > 0
        and len(stmts_q3) > 0
        and hallucinations == 0
    )

    return {
        "arch":               "v1_6",
        "run_idx":            run_idx,
        "seed":               seed,
        "hazard_cost":        hazard_cost,
        "num_steps":          BATCH_STEPS,
        "total_statements":   len(statements),
        "statements_q1":      len(stmts_q1),
        "statements_q2":      len(stmts_q2),
        "statements_q3":      len(stmts_q3),
        "hallucination_count": hallucinations,
        "q1_formation_depth": q1_formation_depth,
        "q3_surprise_cells":  len(q3_cells),
        "q3_resolution_stated": q3_resolved,
        "report_complete":    report_complete,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Check input files
    for path in (
        RUN_DATA_CSV, PROVENANCE_CSV, SCHEMA_CSV,
        FAMILY_CSV, COMPARISON_CSV, PREDICTION_ERROR_CSV,
    ):
        if not os.path.exists(path):
            print(f"ERROR: required input file not found: {path}")
            print("Ensure v1.5 output files are in the current directory.")
            sys.exit(1)

    runs = load_320k_runs(RUN_DATA_CSV)
    if not runs:
        print(f"ERROR: no {BATCH_STEPS}-step runs found in {RUN_DATA_CSV}.")
        sys.exit(1)

    print(f"v1.6 Report Batch")
    print(f"  Reading {len(runs)} complete runs at {BATCH_STEPS:,} steps.")
    print(f"  No new agent simulations — reading from v1.5 substrate.")
    print(f"  Output: {REPORT_CSV}, {REPORT_SUMMARY_CSV}")
    print()

    total_hallucinations = 0
    total_statements     = 0
    incomplete_runs      = []

    # Accumulate statement sequences for Category γ individuation measure
    q1_sequences = {}  # run_idx -> list of source_keys

    with (
        open(REPORT_CSV, "w", newline="")    as rep_f,
        open(REPORT_SUMMARY_CSV, "w", newline="") as sum_f,
    ):
        rep_writer = csv.DictWriter(rep_f,    fieldnames=REPORT_FIELDS)
        sum_writer = csv.DictWriter(sum_f,    fieldnames=SUMMARY_FIELDS)
        rep_writer.writeheader()
        sum_writer.writeheader()

        for run_idx, seed, hazard_cost in runs:
            try:
                statements, bundle = process_run(run_idx, seed, hazard_cost)
            except Exception as e:
                print(f"  Run {run_idx} (seed={seed}): ERROR — {e}")
                incomplete_runs.append(run_idx)
                continue

            # Write per-statement rows
            for stmt in statements:
                rep_writer.writerow({
                    "arch":            "v1_6",
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

            # Write summary row
            summary = compute_summary(run_idx, seed, hazard_cost, statements)
            sum_writer.writerow(summary)

            # Track for batch totals
            run_halluc = summary["hallucination_count"]
            total_hallucinations += run_halluc
            total_statements     += summary["total_statements"]
            if not summary["report_complete"]:
                incomplete_runs.append(run_idx)

            # Accumulate Q1 key sequence for Category γ
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

    # --- Category γ: biographical individuation ---
    print()
    print("Category γ: biographical individuation")
    run_ids = sorted(q1_sequences.keys())
    n = len(run_ids)
    if n >= 2:
        distances = []
        for i in range(n):
            for j in range(i + 1, n):
                d = _edit_distance_normalised(
                    q1_sequences[run_ids[i]],
                    q1_sequences[run_ids[j]],
                )
                distances.append(d)
        min_d   = min(distances)
        max_d   = max(distances)
        mean_d  = sum(distances) / len(distances)
        floor   = 0.05
        passed  = min_d >= floor
        print(f"  Pairwise Q1 distances: n={len(distances)}")
        print(f"  min={min_d:.4f}  mean={mean_d:.4f}  max={max_d:.4f}")
        print(f"  Substantive-differentiation floor: {floor}")
        print(f"  Category γ: {'PASS' if passed else 'FAIL'}")
    else:
        print("  Insufficient runs for pairwise comparison.")

    # --- Batch summary ---
    print()
    print("=" * 60)
    print(f"Batch complete.")
    print(f"  Runs processed:     {len(runs) - len(incomplete_runs)} / "
          f"{len(runs)}")
    print(f"  Total statements:   {total_statements}")
    print(f"  Total hallucinations: {total_hallucinations}")
    if incomplete_runs:
        print(f"  Incomplete runs:    {incomplete_runs}")

    alpha_pass = total_hallucinations == 0
    beta_pass  = len(incomplete_runs) == 0

    print()
    print(f"  Category α (zero hallucinations): "
          f"{'PASS' if alpha_pass else 'FAIL'}")
    print(f"  Category β (query coverage):      "
          f"{'PASS' if beta_pass else 'FAIL'}")
    print()
    print(f"  Report files written:")
    print(f"    {REPORT_CSV}")
    print(f"    {REPORT_SUMMARY_CSV}")

    if not alpha_pass or not beta_pass:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
