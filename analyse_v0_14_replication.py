"""
analyse_v0_14_replication.py
-----------------------------
Comparative analysis of the v0.14 original and replication batches.

Loads run_data_v0_14.csv (original, permutation_offset = 0) and
run_data_v0_14_replication.csv (replication, permutation_offset > 0)
plus run_data_v0_13.csv as the matched-seed baseline. Produces a
side-by-side report addressing the v0.14.1 amendment's targeted
question: does the (cell=(5,9), threshold=1) mean Δ(attractors_
mastered) = +0.649 spike persist under a different permutation
draw?

Output: replication_analysis_v0_14.txt

Run from Terminal with:
    python3 analyse_v0_14_replication.py
"""

import csv
import os
import sys
from collections import defaultdict
import numpy as np


def load(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def parse_thresholds(s):
    result = {}
    for part in (s or "").split("|"):
        if ":" not in part:
            continue
        last_colon = part.rfind(":")
        cell_str = part[:last_colon]
        value_str = part[last_colon + 1:]
        try:
            result[cell_str] = int(value_str)
        except ValueError:
            pass
    return result


def get_int(r, key):
    v = r.get(key)
    if v in (None, "", "None"):
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def per_cell_threshold_analysis(batch, v13_idx):
    """For each (cell, threshold) condition, compute mean Δ(am) v vs v13."""
    table = defaultdict(list)
    for r in batch:
        key = (r["hazard_cost"], r["num_steps"], r["run_idx"])
        r13 = v13_idx.get(key)
        if not r13:
            continue
        am14 = get_int(r, "attractors_mastered")
        am13 = get_int(r13, "attractors_mastered")
        if am14 is None or am13 is None:
            continue
        delta = am14 - am13
        thr = parse_thresholds(r.get("hazard_thresholds", ""))
        for cell, t in thr.items():
            table[(cell, t)].append(delta)
    return table


def aggregate_findings(batch, v13_idx, label):
    lines = []
    lines.append(f"\n--- {label} ---")
    # Headline aggregate findings
    total_runs = len(batch)
    by_length = defaultdict(list)
    for r in batch:
        by_length[r["num_steps"]].append(r)
    for nl in sorted(by_length.keys()):
        subset = by_length[nl]
        n = len(subset)
        activated = sum(
            1 for r in subset
            if r["activation_step"] not in ("", "None", None)
        )
        found = sum(
            1 for r in subset
            if r["end_state_found_step"] not in ("", "None", None)
        )
        all5_trans = sum(
            1 for r in subset
            if get_int(r, "hazards_transitioned") == 5
        )
        all5_banked = sum(
            1 for r in subset
            if get_int(r, "hazards_banked_as_knowledge") == 5
        )
        cond_disc = (100 * found / activated) if activated else 0.0
        lines.append(
            f"  {nl:>6} steps: act={activated}/{n}, found={found}/{n}, "
            f"cond.disc={cond_disc:.1f}%, "
            f"trans=5/5 in {all5_trans}/{n}, banked=5/5 in {all5_banked}/{n}"
        )

    # H2 aggregate
    am_higher = am_lower = am_eq = 0
    for r in batch:
        key = (r["hazard_cost"], r["num_steps"], r["run_idx"])
        r13 = v13_idx.get(key)
        if not r13:
            continue
        am = get_int(r, "attractors_mastered")
        am13 = get_int(r13, "attractors_mastered")
        if am is None or am13 is None:
            continue
        if am > am13:
            am_higher += 1
        elif am < am13:
            am_lower += 1
        else:
            am_eq += 1
    lines.append(
        f"  H2: attractors_mastered batch_higher={am_higher}, "
        f"v13_higher={am_lower}, equal={am_eq}"
    )

    # Activation rate inversion
    batch_act_v13_not = sum(
        1 for r in batch
        if r["activation_step"] not in ("", "None", None)
        and v13_idx.get((r["hazard_cost"], r["num_steps"], r["run_idx"]),
                        {}).get("activation_step") in ("", "None", None)
    )
    v13_act_batch_not = sum(
        1 for r in batch
        if r["activation_step"] in ("", "None", None)
        and v13_idx.get((r["hazard_cost"], r["num_steps"], r["run_idx"]),
                        {}).get("activation_step") not in ("", "None", None)
    )
    lines.append(
        f"  Activation: batch>v13={batch_act_v13_not}, "
        f"v13>batch={v13_act_batch_not}"
    )
    return lines


def main():
    orig_path = "run_data_v0_14.csv"
    repl_path = "run_data_v0_14_replication.csv"
    base_path = "run_data_v0_13.csv"

    orig = load(orig_path)
    repl = load(repl_path)
    v13 = load(base_path)
    v13_idx = {
        (r["hazard_cost"], r["num_steps"], r["run_idx"]): r
        for r in v13 if r["arch"] == "v0_13"
    }

    if not orig:
        print(f"ERROR: {orig_path} not found")
        sys.exit(1)
    if not repl:
        print(f"ERROR: {repl_path} not found "
              "(run curiosity_agent_v0_14_batch_replication.py first)")
        sys.exit(1)
    if not v13_idx:
        print(f"ERROR: {base_path} not found or no v0_13 rows")
        sys.exit(1)

    lines = []
    lines.append("=" * 72)
    lines.append("v0.14 REPLICATION ANALYSIS")
    lines.append("Original batch + Replication batch + v0.13 baseline")
    lines.append("=" * 72)
    lines.append(f"Original:    {len(orig)} runs")
    lines.append(f"Replication: {len(repl)} runs")
    lines.append(f"v0.13 base:  {len(v13_idx)} runs")
    lines.append("")

    # Aggregate findings comparison
    lines.append("=" * 72)
    lines.append("HEADLINE FINDINGS COMPARISON")
    lines.append("=" * 72)
    lines.extend(aggregate_findings(orig, v13_idx, "ORIGINAL BATCH"))
    lines.extend(aggregate_findings(repl, v13_idx, "REPLICATION BATCH"))

    # Per-cell, per-threshold analysis
    orig_table = per_cell_threshold_analysis(orig, v13_idx)
    repl_table = per_cell_threshold_analysis(repl, v13_idx)

    cells_sorted = sorted(set(c for (c, _) in orig_table.keys()))

    lines.append("\n")
    lines.append("=" * 72)
    lines.append("PER-CELL, PER-THRESHOLD ANALYSIS: mean Δ(attractors_mastered)")
    lines.append("=" * 72)
    lines.append(f"{'Cell':<12} {'Thr':<5} "
                 f"{'Original mean Δ (n)':<25} "
                 f"{'Replication mean Δ (n)':<25} "
                 f"{'persists?':<12}")
    lines.append("-" * 80)
    for cell in cells_sorted:
        for thr in range(1, 6):
            o = orig_table.get((cell, thr), [])
            r = repl_table.get((cell, thr), [])
            o_mean = np.mean(o) if o else float('nan')
            r_mean = np.mean(r) if r else float('nan')
            # "Persists" verdict: same sign as original AND magnitude
            # at least 0.5x of original
            if not o or not r:
                persists_str = "N/A"
            elif abs(o_mean) < 0.1 and abs(r_mean) < 0.1:
                persists_str = "weak both"
            elif np.sign(o_mean) != np.sign(r_mean):
                persists_str = "REVERSED"
            elif abs(r_mean) >= 0.5 * abs(o_mean):
                persists_str = "yes"
            else:
                persists_str = "weakened"
            lines.append(
                f"{cell:<12} {thr:<5} "
                f"{o_mean:+.3f} (n={len(o):>3})           "
                f"{r_mean:+.3f} (n={len(r):>3})           "
                f"{persists_str:<12}"
            )
        lines.append("")

    # Targeted finding: (5,9), threshold 1
    lines.append("=" * 72)
    lines.append("TARGETED FINDING: (5,9) + threshold 1")
    lines.append("=" * 72)
    o59_1 = orig_table.get(("(5, 9)", 1), [])
    r59_1 = repl_table.get(("(5, 9)", 1), [])
    if o59_1:
        lines.append(f"  Original:    n={len(o59_1)}, "
                     f"mean Δ = {np.mean(o59_1):+.3f}, "
                     f"v14_higher={sum(1 for d in o59_1 if d > 0)}, "
                     f"v13_higher={sum(1 for d in o59_1 if d < 0)}, "
                     f"eq={sum(1 for d in o59_1 if d == 0)}")
    if r59_1:
        lines.append(f"  Replication: n={len(r59_1)}, "
                     f"mean Δ = {np.mean(r59_1):+.3f}, "
                     f"repl_higher={sum(1 for d in r59_1 if d > 0)}, "
                     f"v13_higher={sum(1 for d in r59_1 if d < 0)}, "
                     f"eq={sum(1 for d in r59_1 if d == 0)}")
    if o59_1 and r59_1:
        if (np.mean(r59_1) >= 0.4 and np.mean(o59_1) >= 0.4):
            verdict = ("PERSISTS — the (5,9)+threshold-1 spike replicates. "
                       "Structural reading of obstacle-removal at the "
                       "bottleneck cell + earliest threshold gains support.")
        elif np.mean(r59_1) < 0.2 and np.mean(o59_1) >= 0.4:
            verdict = ("DOES NOT PERSIST — the original spike was "
                       "permutation-draw noise. Per-cell mechanism "
                       "story is more complex than obstacle-removal alone.")
        elif np.sign(np.mean(o59_1)) != np.sign(np.mean(r59_1)):
            verdict = ("REVERSED — the per-cell pattern is unstable across "
                       "permutation draws. Aggregate findings hold; "
                       "per-cell mechanism is not robust.")
        else:
            verdict = ("PARTIAL — the replication shows attenuated effect "
                       "in the same direction. Some structural signal "
                       "but mechanism is more nuanced than first-batch "
                       "magnitude implied.")
        lines.append("")
        lines.append(f"  Verdict: {verdict}")

    report = "\n".join(lines)
    out_path = "replication_analysis_v0_14.txt"
    with open(out_path, "w") as f:
        f.write(report)
    print(report)
    print(f"\nReport written to {out_path}")


if __name__ == "__main__":
    main()
