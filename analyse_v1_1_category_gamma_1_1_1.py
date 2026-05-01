"""
analyse_v1_1_category_gamma.py
------------------------------
v1.1 Category γ analysis. Implements the pairwise structural-distance
metric committed in the v1.1.1 amendment (Baker, 2026s):

  d(i, j) = 0.25 * d_order
          + 0.25 * d_content
          + 0.25 * d_xref
          + 0.25 * d_conf

where:
  d_order   normalised Kendall tau distance over flag identifiers
            shared between agents i and j (formation order).
  d_content Jaccard distance between the flag identifier sets
            (which flags formed at all).
  d_xref    Jaccard distance between cross-reference pairs
            (threat-flag-to-knowledge-banking-flag linkage structure).
  d_conf    normalised L1 distance between per-flag-type
            confirmation-density vectors.

Each component lies in [0, 1]; the composite distance lies in [0, 1].

The script reads:
  provenance_v1_1.csv   per-flag formation records
  run_data_v1_1.csv     per-run aggregates (used for confirmation
                        density normalisation and run metadata)

Outputs:
  category_gamma_distances.csv      per-pair distance matrix in long
                                     form: (i, j, d_order, d_content,
                                     d_xref, d_conf, d_composite)
  category_gamma_summary.csv        per-(cost, run length) cell
                                     statistics: mean, std, min, max
                                     of d_within_cell, plus the
                                     d_across_cells aggregate
  category_gamma_verdict.txt        human-readable verdict against
                                     the v1.1.1 amendment §5 criteria

The script is fully deterministic given the input CSVs. No random
seeds, no model fits, no hyperparameter tuning.

Usage:
    python3 analyse_v1_1_category_gamma.py
    python3 analyse_v1_1_category_gamma.py --provenance provenance_v1_1.csv \\
        --runs run_data_v1_1.csv --out-dir .
"""

import argparse
import csv
import os
from collections import defaultdict
from itertools import combinations


EPSILON = 1e-6  # for d_conf division-by-zero protection
WITHIN_CELL_FLOOR = 0.05  # v1.1.1 amendment §5 first criterion
STD_FLOOR = 0.02  # v1.1.1 amendment §5 second criterion
STD_FLOOR_MIN_CELLS = 4  # v1.1.1 amendment §5 second criterion

FLAG_TYPES = [
    "threat", "mastery", "knowledge_banking",
    "end_state_activation", "end_state_banking",
]


def _run_key(row):
    """Canonical run identifier used as the agent id throughout."""
    return (float(row["hazard_cost"]),
            int(row["num_steps"]),
            int(row["run_idx"]))


def _to_int_or_none(v):
    if v is None or v == "" or v == "None":
        return None
    return int(v)


def load_records(provenance_path):
    """Load provenance records grouped by run.

    Returns: dict mapping run_key -> list of record dicts.
    """
    by_run = defaultdict(list)
    with open(provenance_path) as f:
        for r in csv.DictReader(f):
            try:
                key = _run_key(r)
            except (ValueError, KeyError):
                continue
            by_run[key].append(r)
    return dict(by_run)


def load_runs(runs_path):
    """Load per-run aggregates indexed by run key."""
    by_key = {}
    with open(runs_path) as f:
        for r in csv.DictReader(f):
            try:
                key = _run_key(r)
            except (ValueError, KeyError):
                continue
            by_key[key] = r
    return by_key


# ----------------------------------------------------------------
# Per-agent feature extraction
# ----------------------------------------------------------------

def agent_flag_set(records):
    """Set of flag identifiers formed by this agent."""
    return frozenset(r["flag_id"] for r in records)


def agent_flag_order(records):
    """Ordered list of flag identifiers in formation order, with ties
    broken by flag_id alphabetically (matching the v1.1 batch's
    ordering in summary_metrics)."""
    sorted_recs = sorted(
        records,
        key=lambda r: (int(r["flag_set_step"]), r["flag_id"])
    )
    return [r["flag_id"] for r in sorted_recs]


def agent_xref_pairs(records):
    """Set of cross-reference items.

    Each item is one of:
      ("paired", threat_flag_id, knowledge_banking_flag_id)
        for threat flags whose derived_knowledge_flag_id is non-null
        and resolves to a knowledge-banking record in this run.
      ("pending", threat_flag_id, expected_kb_id)
        for threat flags with transformed_at_step set but
        derived_knowledge_flag_id either null or unresolved.

    The pending sentinel ensures pending and resolved cross-references
    are distinguished in the structural-distance computation.
    """
    items = set()
    knowledge_record_ids = {
        r["flag_id"] for r in records
        if r["flag_type"] == "knowledge_banking"
    }
    for r in records:
        if r["flag_type"] != "threat":
            continue
        transformed = r.get("transformed_at_step", "")
        if not transformed or transformed == "None":
            continue
        forward = r.get("derived_knowledge_flag_id", "")
        if forward and forward != "None" and forward in knowledge_record_ids:
            items.add(("paired", r["flag_id"], forward))
        else:
            # Pending: cell transformed but knowledge-banking flag did
            # not yet form by end-of-run (or forward reference missing
            # for some other reason; both surface as the pending case).
            items.add(("pending", r["flag_id"], forward or ""))
    return items


def agent_confirmation_density_vector(records, num_steps):
    """Per-flag-type confirmation density vector.

    For each flag type, computes the mean of (confirming_observations
    per flag) / (post-formation window length per flag), where the
    post-formation window length is num_steps - flag_set_step.

    Returns a tuple of length 5 in FLAG_TYPES order. Flag types with
    no formed flags get a zero entry (treated as zero density rather
    than as missing, per v1.1.1 amendment §2.4).
    """
    densities = [0.0] * len(FLAG_TYPES)
    for ti, ft in enumerate(FLAG_TYPES):
        per_flag_densities = []
        for r in records:
            if r["flag_type"] != ft:
                continue
            set_step = int(r["flag_set_step"])
            window = max(num_steps - set_step, 1)
            conf = int(r["confirming_observations"])
            per_flag_densities.append(conf / window)
        if per_flag_densities:
            densities[ti] = sum(per_flag_densities) / len(per_flag_densities)
    return tuple(densities)


# ----------------------------------------------------------------
# Distance components
# ----------------------------------------------------------------

def d_order(order_i, order_j, set_i, set_j):
    """Normalised Kendall tau distance over the symmetric set."""
    shared = set_i & set_j
    if len(shared) < 2:
        return 0.0
    # Build position maps restricted to the shared set
    pos_i = {fid: idx for idx, fid in enumerate(order_i) if fid in shared}
    pos_j = {fid: idx for idx, fid in enumerate(order_j) if fid in shared}
    # Count discordant pairs
    shared_list = sorted(shared)
    discordant = 0
    total = 0
    for a, b in combinations(shared_list, 2):
        # In agent i: does a precede b?
        i_a_before_b = pos_i[a] < pos_i[b]
        # In agent j: does a precede b?
        j_a_before_b = pos_j[a] < pos_j[b]
        if i_a_before_b != j_a_before_b:
            discordant += 1
        total += 1
    if total == 0:
        return 0.0
    return discordant / total


def d_content(set_i, set_j):
    """Jaccard distance between flag identifier sets."""
    union = set_i | set_j
    if not union:
        return 0.0
    return 1.0 - len(set_i & set_j) / len(union)


def d_xref(xref_i, xref_j):
    """Jaccard distance between cross-reference items."""
    union = xref_i | xref_j
    if not union:
        return 0.0
    return 1.0 - len(xref_i & xref_j) / len(union)


def d_conf(vec_i, vec_j):
    """Normalised L1 distance between confirmation density vectors."""
    n = len(vec_i)
    if n == 0:
        return 0.0
    total = 0.0
    for a, b in zip(vec_i, vec_j):
        denom = max(a + b, EPSILON)
        total += abs(a - b) / denom
    return total / n


def composite_distance(d_o, d_c, d_x, d_f):
    """Equal-weighted composite distance per v1.1.1 amendment §2.5."""
    return 0.25 * d_o + 0.25 * d_c + 0.25 * d_x + 0.25 * d_f


# ----------------------------------------------------------------
# Per-agent feature precomputation
# ----------------------------------------------------------------

def precompute_agent_features(records_by_run, runs_by_key):
    """For each agent, compute the four features the distance metric
    operates on. Returns dict: run_key -> dict with keys 'set',
    'order', 'xref', 'conf'."""
    features = {}
    for key, records in records_by_run.items():
        run_meta = runs_by_key.get(key)
        if run_meta is None:
            continue
        num_steps = int(run_meta["num_steps"])
        features[key] = {
            "set": agent_flag_set(records),
            "order": agent_flag_order(records),
            "xref": agent_xref_pairs(records),
            "conf": agent_confirmation_density_vector(records, num_steps),
        }
    # Agents with no records still need a feature entry (empty)
    for key in runs_by_key:
        if key not in features:
            features[key] = {
                "set": frozenset(),
                "order": [],
                "xref": set(),
                "conf": tuple(0.0 for _ in FLAG_TYPES),
            }
    return features


# ----------------------------------------------------------------
# Main analysis
# ----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provenance", default="provenance_v1_1.csv")
    ap.add_argument("--runs", default="run_data_v1_1.csv")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    if not os.path.exists(args.provenance):
        raise SystemExit(f"FAIL: {args.provenance} not found.")
    if not os.path.exists(args.runs):
        raise SystemExit(f"FAIL: {args.runs} not found.")

    records_by_run = load_records(args.provenance)
    runs_by_key = load_runs(args.runs)

    print(f"Loaded {len(records_by_run)} runs with provenance records "
          f"out of {len(runs_by_key)} total runs.")
    if len(runs_by_key) != 180:
        print(f"  WARNING: expected 180 runs, found {len(runs_by_key)}.")

    features = precompute_agent_features(records_by_run, runs_by_key)
    agent_keys = sorted(features.keys())
    n_agents = len(agent_keys)
    n_pairs = n_agents * (n_agents - 1) // 2
    print(f"Computing pairwise distances for {n_agents} agents "
          f"({n_pairs} pairs)...")

    # Compute all pairwise distances. Streamed to disk to avoid
    # holding the full distance matrix in memory.
    distances_path = os.path.join(args.out_dir, "category_gamma_distances.csv")
    distance_records = []
    with open(distances_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "i_cost", "i_steps", "i_run_idx",
            "j_cost", "j_steps", "j_run_idx",
            "d_order", "d_content", "d_xref", "d_conf",
            "d_composite",
            "same_cell",
        ])
        for ki, kj in combinations(agent_keys, 2):
            fi = features[ki]
            fj = features[kj]
            do = d_order(fi["order"], fj["order"], fi["set"], fj["set"])
            dc = d_content(fi["set"], fj["set"])
            dx = d_xref(fi["xref"], fj["xref"])
            df = d_conf(fi["conf"], fj["conf"])
            comp = composite_distance(do, dc, dx, df)
            same_cell = (ki[0] == kj[0] and ki[1] == kj[1])
            writer.writerow([
                ki[0], ki[1], ki[2],
                kj[0], kj[1], kj[2],
                f"{do:.6f}", f"{dc:.6f}", f"{dx:.6f}", f"{df:.6f}",
                f"{comp:.6f}",
                "1" if same_cell else "0",
            ])
            distance_records.append({
                "ki": ki, "kj": kj, "same_cell": same_cell,
                "d_composite": comp,
            })

    print(f"Per-pair distances written to {distances_path}")

    # Aggregate to per-cell statistics
    by_cell_distances = defaultdict(list)  # (cost, steps) -> list of d_composite within
    across_cell_distances = []

    for rec in distance_records:
        if rec["same_cell"]:
            cell = (rec["ki"][0], rec["ki"][1])
            by_cell_distances[cell].append(rec["d_composite"])
        else:
            across_cell_distances.append(rec["d_composite"])

    summary_path = os.path.join(args.out_dir, "category_gamma_summary.csv")
    summary_rows = []
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "cost", "num_steps", "n_pairs",
            "mean", "std", "min", "max",
        ])
        for cell in sorted(by_cell_distances.keys()):
            ds = by_cell_distances[cell]
            n = len(ds)
            mean = sum(ds) / n if n else 0.0
            if n > 1:
                var = sum((d - mean) ** 2 for d in ds) / (n - 1)
                std = var ** 0.5
            else:
                std = 0.0
            mn = min(ds) if ds else 0.0
            mx = max(ds) if ds else 0.0
            writer.writerow([
                cell[0], cell[1], n,
                f"{mean:.6f}", f"{std:.6f}",
                f"{mn:.6f}", f"{mx:.6f}",
            ])
            summary_rows.append({
                "cost": cell[0], "num_steps": cell[1], "n_pairs": n,
                "mean": mean, "std": std, "min": mn, "max": mx,
            })

    print(f"Per-cell summary written to {summary_path}")

    # d_across_cells aggregate
    n_across = len(across_cell_distances)
    d_across_mean = (sum(across_cell_distances) / n_across
                     if n_across else 0.0)
    if n_across > 1:
        var = sum((d - d_across_mean) ** 2 for d in across_cell_distances) / (n_across - 1)
        d_across_std = var ** 0.5
    else:
        d_across_std = 0.0

    # Verdict against v1.1.1 amendment §5
    verdict_lines = []
    verdict_lines.append("v1.1 CATEGORY γ VERDICT")
    verdict_lines.append("=" * 70)
    verdict_lines.append("")
    verdict_lines.append(f"Pairwise distances computed: {len(distance_records)}")
    verdict_lines.append(f"  within-cell pairs:   {sum(len(ds) for ds in by_cell_distances.values())}")
    verdict_lines.append(f"  across-cell pairs:   {n_across}")
    verdict_lines.append("")
    verdict_lines.append(f"d_across_cells: mean={d_across_mean:.4f} std={d_across_std:.4f}")
    verdict_lines.append("")
    verdict_lines.append("Per-cell within-cell statistics:")
    verdict_lines.append(f"  {'cost':>6} {'steps':>8} {'n':>4} {'mean':>8} {'std':>8} {'min':>8} {'max':>8}")
    for row in summary_rows:
        verdict_lines.append(
            f"  {row['cost']:>6} {row['num_steps']:>8} {row['n_pairs']:>4} "
            f"{row['mean']:>8.4f} {row['std']:>8.4f} "
            f"{row['min']:>8.4f} {row['max']:>8.4f}"
        )
    verdict_lines.append("")
    verdict_lines.append("v1.1.1 amendment §5 criteria:")
    verdict_lines.append("")

    # First criterion: d_within_cell >= 0.05 AND d_across_cells > d_within_cell
    cells_meeting_floor = [r for r in summary_rows if r["mean"] >= WITHIN_CELL_FLOOR]
    cells_with_across_dominance = [
        r for r in summary_rows if d_across_mean > r["mean"]
    ]
    cells_passing_first = [
        r for r in summary_rows
        if r["mean"] >= WITHIN_CELL_FLOOR and d_across_mean > r["mean"]
    ]
    verdict_lines.append(
        f"  Criterion 1 (d_within_cell >= {WITHIN_CELL_FLOOR} AND "
        f"d_across_cells > d_within_cell):"
    )
    verdict_lines.append(
        f"    cells passing:                  "
        f"{len(cells_passing_first)} / {len(summary_rows)}"
    )
    verdict_lines.append(
        f"    cells meeting floor:            "
        f"{len(cells_meeting_floor)} / {len(summary_rows)}"
    )
    verdict_lines.append(
        f"    cells with d_across > d_within: "
        f"{len(cells_with_across_dominance)} / {len(summary_rows)}"
    )

    # Second criterion: std >= 0.02 in at least 4 cells
    cells_passing_std = [r for r in summary_rows if r["std"] >= STD_FLOOR]
    verdict_lines.append("")
    verdict_lines.append(
        f"  Criterion 2 (std >= {STD_FLOOR} in at least "
        f"{STD_FLOOR_MIN_CELLS} cells):"
    )
    verdict_lines.append(
        f"    cells with std >= {STD_FLOOR}:       "
        f"{len(cells_passing_std)} / {len(summary_rows)}"
    )
    crit2_pass = len(cells_passing_std) >= STD_FLOOR_MIN_CELLS
    verdict_lines.append(
        f"    Criterion 2 verdict:            "
        f"{'PASS' if crit2_pass else 'FAIL'}"
    )

    verdict_lines.append("")
    crit1_pass = len(cells_passing_first) == len(summary_rows)
    if crit1_pass and crit2_pass:
        overall = "PASS"
    elif crit1_pass or crit2_pass:
        overall = "PARTIAL PASS"
    else:
        overall = "FAIL"
    verdict_lines.append(f"OVERALL CATEGORY γ VERDICT: {overall}")
    verdict_lines.append("")
    if overall != "PASS":
        verdict_lines.append(
            "Per v1.1 pre-registration §5.3 and v1.1.1 amendment §6: "
            "negative findings are honestly reported. The v1.1 paper's "
            "Category γ section reads against the actual distribution "
            "rather than against threshold-pass framing."
        )
        verdict_lines.append("")

    verdict_text = "\n".join(verdict_lines)
    verdict_path = os.path.join(args.out_dir, "category_gamma_verdict.txt")
    with open(verdict_path, "w") as f:
        f.write(verdict_text + "\n")
    print(f"Verdict written to {verdict_path}")
    print()
    print(verdict_text)


if __name__ == "__main__":
    main()
