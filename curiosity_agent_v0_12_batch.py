"""
curiosity_agent_v0_12_batch.py
------------------------------
Batch runner for v0.12 against the v0.11.2 baseline (matched-seed
comparison, no v0.11.2 re-run).

Implements the experimental matrix specified in v0.12-preregistration.md:
  - 1 architecture: v0.12 (signature-matching first-entry flagging
    on cell-type signature, inheriting v0.11.2 otherwise)
  - 6 cost levels: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
  - 3 run lengths: 20,000, 80,000, 160,000 steps
  - 10 runs per cell

Total: 1 x 6 x 3 x 10 = 180 runs.

Matched seeds against v0.11.2: run i at cost c at run length L uses
seed = hash(("v0_11_2", c, L, i)) % (2**31), matching the seed-
generation formula in curiosity_agent_v0_11_2_batch.py. This is
deliberate: the v0.12 pre-registration commits to matched-seed
comparison against the existing v0.11.2 batch, so seeds must match
the v0.11.2 ones exactly. v0.12 is run with arch="v0_12" in the
metrics but with seeds generated as if arch="v0_11_2".

The existing run_data_v0_11_2.csv (from the v0.11.2 batch) is loaded
for comparison and is not re-run. The v0.10 batch results are
referenced via run_data_v0_11_2.csv since that batch contained both
v0.10 and v0.11.2 architectures.

CLI args allow restricting to a subset:
  --steps 20000           Run only one run length (omit for all three)
  --cost 1.0              Run only one cost level (omit for all six)
  --runs 5                Override runs per cell (default 10)
  --baseline path.csv     Path to v0.11.2 baseline CSV
                          (default: run_data_v0_11_2.csv)

Run from Terminal with:
    python3 curiosity_agent_v0_12_batch.py
"""

import argparse
import csv
import os
import time
from collections import defaultdict, Counter
import numpy as np

# Import constants and helpers from v0.12. The agent class in v0.12 is
# DevelopmentalAgent; the world is StructuredGridWorld inherited from
# the v0.10 line. The v0.12 agent uses module-level HAZARD_COST in
# update_threat_layer for the cost_paid_on_signature_matched_hazards
# metric, but the world's step function is what actually returns the
# cost on each step. The world is parameterised below.
from curiosity_agent_v0_12 import (
    GRID_SIZE, PHASE_3_START_FRACTION, Q_VALUE_RESET_MULTIPLIER,
    FEATURE_DRIVE_WEIGHT, FRAME, NEUTRAL, HAZARD, ATTRACTOR,
    AVERSION_PENALTY, ATTRACTION_BONUS, FLAG_THRESHOLD,
    MASTERY_THRESHOLD, MASTERY_BONUS,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, START_CELL,
    StructuredGridWorld, plan_phase_1_path, path_to_actions,
    DevelopmentalAgent as V012Agent,
)


# --------------------------------------------------------------------------
# WORLD VARIANT WITH PARAMETERISED HAZARD COST
# --------------------------------------------------------------------------

class V012World(StructuredGridWorld):
    """v0.12 world: identical to v0.11.2 / v0.10 world. Hazards always
    passable at parameterised cost. The signature-matching mechanism
    operates inside the agent's update_threat_layer, not the world."""

    def __init__(self, hazard_cost, size=GRID_SIZE):
        super().__init__(size=size)
        self.hazard_cost = hazard_cost

    def step(self, action):
        x, y = self.agent_pos
        if action == 0:
            target = (x, y - 1)
        elif action == 1:
            target = (x, y + 1)
        elif action == 2:
            target = (x - 1, y)
        elif action == 3:
            target = (x + 1, y)
        else:
            target = self.agent_pos

        if not (0 <= target[0] < self.size and 0 <= target[1] < self.size):
            target_type = FRAME
        else:
            target_type = self.cell_type[target]

        if target_type == FRAME:
            return self.observe(), target, False, 0.0
        if target_type == HAZARD:
            self.agent_pos = target
            return self.observe(), target, True, self.hazard_cost
        self.agent_pos = target
        return self.observe(), target, True, 0.0


# --------------------------------------------------------------------------
# RUN ONE AGENT
# --------------------------------------------------------------------------

def run_one(hazard_cost, num_steps, seed):
    """Execute one v0.12 agent run. Returns a dict of per-run metrics."""
    np.random.seed(seed)

    world = V012World(hazard_cost)
    agent = V012Agent(world, num_steps)

    state = world.observe()
    p3_visits_per_attractor = {a: 0 for a in ATTRACTOR_CELLS}

    for step in range(num_steps):
        agent.steps_taken = step
        agent.check_phase_transition()

        if agent.phase == 1:
            action = agent.get_prescribed_action()
            if action is None:
                action = 0
        else:
            action = agent.choose_action(state)

        next_state, target_cell, success, cost_incurred = world.step(action)

        agent.record_action_outcome(target_cell, success, cost_incurred,
                                    world, step)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        r_feature = agent.feature_reward(next_state)
        intrinsic = (r_novelty + r_progress + r_preference + r_feature
                     - cost_incurred)

        agent.update_model(state, action, next_state, error, r_progress, r_feature)
        agent.update_values(state, action, next_state, intrinsic)

        if agent.phase == 3:
            cell = (next_state[0], next_state[1])
            if cell in p3_visits_per_attractor:
                p3_visits_per_attractor[cell] += 1

        state = next_state

    # --- COMPUTE METRICS ---
    # Inherits all v0.11.2 metrics; adds the three v0.12-specific ones.
    metrics = {
        "arch": "v0_12",
        "hazard_cost": hazard_cost,
        "num_steps": num_steps,
        "seed": seed,
        "phase_1_end": agent.phase_1_end_step,
        "phase_2_end": agent.phase_2_end_step,
        "frame_attempts_p1": agent.frame_attempts_by_phase[1],
        "frame_attempts_p2": agent.frame_attempts_by_phase[2],
        "frame_attempts_p3": agent.frame_attempts_by_phase[3],
        "hazard_entries_p1": agent.hazard_entries_by_phase[1],
        "hazard_entries_p2": agent.hazard_entries_by_phase[2],
        "hazard_entries_p3": agent.hazard_entries_by_phase[3],
        "total_cost": agent.total_cost_incurred,
        "mastered_pairs": sum(
            1 for errs in agent.fast_errors.values()
            if len(errs) >= 5 and np.mean(errs) < 0.15
        ),
        # Threat-layer metrics (v0.10 inherited + v0.12 additions)
        "hazards_flagged": len(agent.cells_flagged_during_run),
        "time_to_first_flag": agent.time_to_first_flag,
        "time_to_second_flag": agent.time_to_second_flag,
        "time_to_final_flag": agent.time_to_final_flag,
        "first_entry_conversions": agent.first_entry_flag_conversions,
        "cost_on_sig_matched": agent.cost_paid_on_signature_matched_hazards,
        "actions_gated_p2": agent.hazard_gated_by_threat_layer[2],
        "actions_gated_p3": agent.hazard_gated_by_threat_layer[3],
        # Mastery-layer metrics (v0.11.2 inherited)
        "attractors_mastered": len(agent.mastery_order_sequence),
        "time_to_first_mastery": agent.time_to_first_mastery,
        "time_to_final_mastery": agent.time_to_final_mastery,
        "first_banked": (str(agent.mastery_order_sequence[0])
                         if agent.mastery_order_sequence else None),
        "mastery_sequence": "|".join(
            str(c) for c in agent.mastery_order_sequence
        ),
    }

    # Post-mastery visits across all mastered attractors
    post_mastery_visits = 0
    for ma in agent.mastery_order_sequence:
        total_visits = agent.attractor_visit_counter.get(ma, 0)
        post_mastery_visits += max(0, total_visits - MASTERY_THRESHOLD)
    metrics["post_mastery_visits_total"] = post_mastery_visits

    # Phase 3 visits per attractor (mastered/unmastered split)
    metrics["p3_visits_to_mastered"] = sum(
        v for cell, v in p3_visits_per_attractor.items()
        if agent.mastery_flag.get(cell, 0) == 1
    )
    metrics["p3_visits_to_unmastered"] = sum(
        v for cell, v in p3_visits_per_attractor.items()
        if agent.mastery_flag.get(cell, 0) == 0
    )

    # Top attractor by preference (for individuation analysis)
    attractor_prefs = {a: agent.cell_preference[a] for a in ATTRACTOR_CELLS}
    top_attractor = max(attractor_prefs, key=attractor_prefs.get)
    metrics["top_attractor"] = str(top_attractor)
    metrics["top_attractor_pref"] = attractor_prefs[top_attractor]

    # Phase 3 cleanness
    metrics["phase_3_clean"] = (agent.hazard_entries_by_phase[3] < 3)
    total_entries = (agent.hazard_entries_by_phase[1]
                     + agent.hazard_entries_by_phase[2]
                     + agent.hazard_entries_by_phase[3])
    metrics["full_run_clean"] = (total_entries < 3)

    return metrics


# --------------------------------------------------------------------------
# BASELINE LOADING (v0.11.2 CSV)
# --------------------------------------------------------------------------

def load_baseline(path):
    """Load existing v0.11.2 batch CSV. Returns list of dicts with
    typed fields. Used for comparison in the meta-report; baseline
    runs are not re-executed."""
    if not os.path.exists(path):
        print(f"  [baseline] File {path} not found — comparisons will be skipped.")
        return []
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Type-cast the fields the report needs
            try:
                r["hazard_cost"] = float(r["hazard_cost"])
                r["num_steps"] = int(r["num_steps"])
                r["hazard_entries_p3"] = int(r["hazard_entries_p3"])
                r["phase_3_clean"] = (r["phase_3_clean"] in ("True", "true", "1"))
                r["total_cost"] = float(r["total_cost"])
                r["hazards_flagged"] = int(r["hazards_flagged"])
                if r.get("attractors_mastered", "") not in ("", "None", None):
                    r["attractors_mastered"] = int(r["attractors_mastered"])
                else:
                    r["attractors_mastered"] = None
            except (ValueError, KeyError):
                continue
            rows.append(r)
    print(f"  [baseline] Loaded {len(rows)} rows from {path}")
    return rows


# --------------------------------------------------------------------------
# BATCH ORCHESTRATION
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, nargs="+",
                    default=[20000, 80000, 160000],
                    help="Run length(s) in steps.")
    ap.add_argument("--cost", type=float, nargs="+",
                    default=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                    help="Hazard cost level(s).")
    ap.add_argument("--runs", type=int, default=10,
                    help="Runs per (cost, steps) cell.")
    ap.add_argument("--out", type=str, default="run_data_v0_12.csv",
                    help="Output CSV filename.")
    ap.add_argument("--report", type=str, default="meta_report_v0_12.txt",
                    help="Output meta-report filename.")
    ap.add_argument("--baseline", type=str, default="run_data_v0_11_2.csv",
                    help="Path to v0.11.2 batch CSV for comparison.")
    args = ap.parse_args()

    # --- LOAD BASELINE FIRST (needed for matched seeds) ---
    baseline = load_baseline(args.baseline)
    print()

    # --- BUILD JOB LIST WITH MATCHED SEEDS ---
    # Critical: seeds must match the seeds used by the v0.11.2 batch.
    # Python's hash() of strings is randomised per interpreter session
    # (PYTHONHASHSEED defaults to random), so the same hash(...) formula
    # cannot reproduce the v0.11.2 seeds. Instead, the seeds are loaded
    # directly from the v0.11.2 CSV. This is the only way to guarantee
    # matched-seed comparison and is the methodologically correct
    # approach: the baseline's seeds are recorded data, not regenerable
    # parameters.
    if not baseline:
        raise RuntimeError(
            f"Baseline CSV {args.baseline} is required for matched-seed "
            "comparison but was not loaded. Cannot proceed without "
            "baseline seeds."
        )

    # Index baseline seeds by (arch, cost, steps, run_idx)
    baseline_seeds = {}
    for r in baseline:
        if r["arch"] != "v0_11_2":
            continue
        key = (r["hazard_cost"], r["num_steps"], int(r["run_idx"]))
        try:
            baseline_seeds[key] = int(r["seed"])
        except (ValueError, KeyError):
            continue

    jobs = []
    missing_seeds = []
    for steps in args.steps:
        for cost in args.cost:
            for run_idx in range(args.runs):
                key = (cost, steps, run_idx)
                if key not in baseline_seeds:
                    missing_seeds.append(key)
                    continue
                seed = baseline_seeds[key]
                jobs.append((cost, steps, run_idx, seed))

    if missing_seeds:
        print(f"  WARNING: {len(missing_seeds)} (cost, steps, run_idx) "
              f"cells not found in baseline CSV — skipping those.")
        if len(missing_seeds) <= 5:
            for k in missing_seeds:
                print(f"    missing: {k}")

    print(f"v0.12 batch")
    print(f"  Architecture  : v0.12 (signature-matching threat layer)")
    print(f"  Cost levels   : {args.cost}")
    print(f"  Run lengths   : {args.steps}")
    print(f"  Runs per cell : {args.runs}")
    print(f"  Total runs    : {len(jobs)}")
    print(f"  Seeds matched : loaded from {args.baseline} (v0.11.2 batch)")
    print()

    # --- RUN ---
    results = []
    t_start = time.time()

    for i, (cost, steps, run_idx, seed) in enumerate(jobs):
        t0 = time.time()
        metrics = run_one(cost, steps, seed)
        metrics["run_idx"] = run_idx
        results.append(metrics)
        elapsed_run = time.time() - t0
        elapsed_total = time.time() - t_start
        completed = i + 1
        remaining = len(jobs) - completed
        eta = (elapsed_total / completed) * remaining
        print(f"[{completed:>3}/{len(jobs)}] v0_12 cost={cost} steps={steps} "
              f"run={run_idx}: P3_ent={metrics['hazard_entries_p3']:>3} "
              f"flagged={metrics['hazards_flagged']} "
              f"first_entry={metrics['first_entry_conversions']} "
              f"mast={metrics['attractors_mastered']} "
              f"({elapsed_run:.1f}s, ETA {eta/60:.1f}m)")

    total_elapsed = time.time() - t_start
    print(f"\nBatch complete in {total_elapsed/60:.1f} minutes "
          f"({total_elapsed:.0f}s).")

    # --- WRITE PER-RUN CSV ---
    fieldnames = [
        "arch", "hazard_cost", "num_steps", "run_idx", "seed",
        "phase_1_end", "phase_2_end",
        "frame_attempts_p1", "frame_attempts_p2", "frame_attempts_p3",
        "hazard_entries_p1", "hazard_entries_p2", "hazard_entries_p3",
        "total_cost", "mastered_pairs", "top_attractor", "top_attractor_pref",
        "phase_3_clean", "full_run_clean",
        "hazards_flagged",
        "time_to_first_flag", "time_to_second_flag", "time_to_final_flag",
        "first_entry_conversions", "cost_on_sig_matched",
        "actions_gated_p2", "actions_gated_p3",
        "attractors_mastered", "time_to_first_mastery",
        "time_to_final_mastery", "first_banked", "mastery_sequence",
        "post_mastery_visits_total",
        "p3_visits_to_mastered", "p3_visits_to_unmastered",
    ]
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"Per-run data saved to {args.out}")

    # --- META-REPORT ---
    lines = []
    lines.append("=" * 76)
    lines.append("v0.12 BATCH META-REPORT")
    lines.append("=" * 76)
    lines.append(f"Total runs (v0.12): {len(results)}")
    lines.append(f"Compute time: {total_elapsed/60:.1f} minutes "
                 f"({total_elapsed:.0f}s)")
    if baseline:
        lines.append(f"Baseline (v0.11.2): {len(baseline)} runs loaded "
                     f"from {args.baseline}")
    lines.append("")

    # --- PER-RUN-LENGTH SUMMARY ---
    for steps in sorted(set(r["num_steps"] for r in results)):
        lines.append(f"\n--- RUN LENGTH: {steps} steps ---")
        v12_slice = [r for r in results if r["num_steps"] == steps]

        # v0.12 architecture summary table
        lines.append(f"\n  Architecture: v0.12")
        lines.append(f"  {'Cost':>6} | {'P3_clean':>8} | "
                     f"{'Mean_P3_ent':>11} | {'Mean_total_cost':>15} | "
                     f"{'Mean_mast_pairs':>15} | {'Mast_attr':>9} | "
                     f"{'P3_to_mast':>10} | {'P3_to_unmast':>12} | "
                     f"{'1st_entry':>9} | {'Sig_cost':>9}")
        lines.append(f"  {'-'*6} | {'-'*8} | "
                     f"{'-'*11} | {'-'*15} | "
                     f"{'-'*15} | {'-'*9} | "
                     f"{'-'*10} | {'-'*12} | "
                     f"{'-'*9} | {'-'*9}")
        for cost in sorted(set(r["hazard_cost"] for r in v12_slice)):
            cell = [r for r in v12_slice if r["hazard_cost"] == cost]
            p3_clean = sum(1 for r in cell if r["phase_3_clean"])
            mean_p3 = np.mean([r["hazard_entries_p3"] for r in cell])
            mean_cost = np.mean([r["total_cost"] for r in cell])
            mean_mast_pairs = np.mean([r["mastered_pairs"] for r in cell])
            mean_attr = np.mean([r["attractors_mastered"] for r in cell])
            mean_p3_mast = np.mean([r["p3_visits_to_mastered"] for r in cell])
            mean_p3_unmast = np.mean([r["p3_visits_to_unmastered"] for r in cell])
            mean_first = np.mean([r["first_entry_conversions"] for r in cell])
            mean_sig_cost = np.mean([r["cost_on_sig_matched"] for r in cell])
            lines.append(f"  {cost:>6.2f} | {p3_clean:>3}/{len(cell):<3}  | "
                         f"{mean_p3:>11.2f} | {mean_cost:>15.2f} | "
                         f"{mean_mast_pairs:>15.1f} | {mean_attr:>5.1f}/6  | "
                         f"{mean_p3_mast:>10.0f} | {mean_p3_unmast:>12.0f} | "
                         f"{mean_first:>9.2f} | {mean_sig_cost:>9.2f}")

        n = len(v12_slice)
        tot_clean = sum(1 for r in v12_slice if r["phase_3_clean"])
        lines.append(f"  {'TOTAL':>6} | {tot_clean:>3}/{n:<3}  |")

        # Individuation
        top_attractors = [r["top_attractor"] for r in v12_slice]
        unique_attractors = set(top_attractors)
        lines.append(f"  Distinct top attractors: "
                     f"{len(unique_attractors)}/6")
        lines.append(f"  Top attractor distribution: "
                     + ", ".join(f"{a}({top_attractors.count(a)})"
                                 for a in sorted(unique_attractors)))

        first_banks = [r["first_banked"] for r in v12_slice
                       if r["first_banked"] is not None]
        if first_banks:
            unique_first = set(first_banks)
            lines.append(f"  Distinct first-banked: "
                         f"{len(unique_first)}/6")
            lines.append(f"  First-banked distribution: "
                         + ", ".join(f"{a}({first_banks.count(a)})"
                                     for a in sorted(unique_first)))

        sequences = [r["mastery_sequence"] for r in v12_slice
                     if r["mastery_sequence"]]
        if sequences:
            seq_counts = Counter(sequences)
            most_common_seq, most_common_count = seq_counts.most_common(1)[0]
            pct = 100 * most_common_count / len(sequences)
            lines.append(f"  Most common mastery sequence accounts for: "
                         f"{pct:.1f}% of runs ({most_common_count}/"
                         f"{len(sequences)})")
            lines.append(f"  Distinct mastery sequences: "
                         f"{len(seq_counts)}/{len(sequences)}")

        # --- BASELINE COMPARISON: v0.11.2 at this run length ---
        if baseline:
            v112_slice = [r for r in baseline
                          if r["num_steps"] == steps and r["arch"] == "v0_11_2"]
            v10_slice = [r for r in baseline
                         if r["num_steps"] == steps and r["arch"] == "v0_10"]
            if v112_slice:
                lines.append(f"\n  Comparison: v0.11.2 baseline at {steps} steps")
                lines.append(f"  {'Cost':>6} | {'v112_clean':>10} | "
                             f"{'v12_clean':>9} | {'v112_cost':>9} | "
                             f"{'v12_cost':>9} | {'cost_ratio':>10}")
                lines.append(f"  {'-'*6} | {'-'*10} | "
                             f"{'-'*9} | {'-'*9} | "
                             f"{'-'*9} | {'-'*10}")
                for cost in sorted(set(r["hazard_cost"]
                                       for r in v12_slice)):
                    v112_cell = [r for r in v112_slice
                                 if r["hazard_cost"] == cost]
                    v12_cell = [r for r in v12_slice
                                if r["hazard_cost"] == cost]
                    v112_clean = sum(1 for r in v112_cell
                                     if r["phase_3_clean"])
                    v12_clean = sum(1 for r in v12_cell
                                    if r["phase_3_clean"])
                    v112_cost_mean = (np.mean([r["total_cost"]
                                               for r in v112_cell])
                                      if v112_cell else 0.0)
                    v12_cost_mean = np.mean([r["total_cost"]
                                             for r in v12_cell])
                    ratio = (v12_cost_mean / v112_cost_mean
                             if v112_cost_mean > 0 else 0.0)
                    lines.append(f"  {cost:>6.2f} | "
                                 f"{v112_clean:>3}/{len(v112_cell):<3}    | "
                                 f"{v12_clean:>3}/{len(v12_cell):<3}   | "
                                 f"{v112_cost_mean:>9.2f} | "
                                 f"{v12_cost_mean:>9.2f} | "
                                 f"{ratio:>9.2f}x")

    # --- v0.12-SPECIFIC: SIGNATURE-MATCHING DYNAMICS ---
    lines.append("\n\n--- v0.12 SIGNATURE-MATCHING DYNAMICS SUMMARY ---")
    for steps in sorted(set(r["num_steps"] for r in results)):
        slice_results = [r for r in results if r["num_steps"] == steps]
        lines.append(f"\nRun length {steps}:")

        n_flagged_total = sum(r["hazards_flagged"] for r in slice_results)
        n_first_entry_total = sum(r["first_entry_conversions"]
                                  for r in slice_results)
        lines.append(f"  Total hazards flagged across batch: "
                     f"{n_flagged_total}")
        lines.append(f"  Total first-entry conversions:      "
                     f"{n_first_entry_total}")

        # Pre-registered prediction: first_entry == max(0, n_flagged - 1)
        # for every run in which any hazard is flagged
        runs_with_flag = [r for r in slice_results if r["hazards_flagged"] >= 1]
        prediction_holds = sum(
            1 for r in runs_with_flag
            if r["first_entry_conversions"] == max(0, r["hazards_flagged"] - 1)
        )
        if runs_with_flag:
            pct_holds = 100 * prediction_holds / len(runs_with_flag)
            lines.append(f"  Strict invariant (first_entry == n_flagged - 1) holds: "
                         f"{prediction_holds}/{len(runs_with_flag)} "
                         f"({pct_holds:.1f}%) of flagged runs")

        # Time-to-second-flag distribution
        ttsf = [r["time_to_second_flag"] for r in slice_results
                if r["time_to_second_flag"] is not None
                and r["time_to_second_flag"] != ""]
        ttsf = [int(t) for t in ttsf]
        if ttsf:
            lines.append(f"  Mean time to second flag: {np.mean(ttsf):.0f} "
                         f"steps (min {min(ttsf)}, max {max(ttsf)}, "
                         f"n={len(ttsf)})")

        # Time from first to second flag (the v0.12 mechanistic signature)
        gaps = []
        for r in slice_results:
            t1 = r["time_to_first_flag"]
            t2 = r["time_to_second_flag"]
            if t1 is not None and t2 is not None and t1 != "" and t2 != "":
                gaps.append(int(t2) - int(t1))
        if gaps:
            lines.append(f"  Mean gap (first to second flag): "
                         f"{np.mean(gaps):.0f} steps (min {min(gaps)}, "
                         f"max {max(gaps)}, n={len(gaps)})")

        # Cost on signature-matched cells
        sig_costs = [r["cost_on_sig_matched"] for r in slice_results]
        lines.append(f"  Mean cost on signature-matched cells: "
                     f"{np.mean(sig_costs):.2f}")

    # --- v0.11.2 INHERITANCE: MASTERY DYNAMICS PRESERVED ---
    lines.append("\n\n--- v0.11.2 MASTERY INHERITANCE PRESERVED ---")
    for steps in sorted(set(r["num_steps"] for r in results)):
        slice_results = [r for r in results if r["num_steps"] == steps]
        lines.append(f"\nRun length {steps}:")
        mean_attr = np.mean([r["attractors_mastered"] for r in slice_results])
        lines.append(f"  Mean attractors mastered: {mean_attr:.2f}/6")
        attr_dist = Counter(r["attractors_mastered"] for r in slice_results)
        lines.append(f"  Distribution: "
                     + ", ".join(f"{k} mastered: {v} runs"
                                 for k, v in sorted(attr_dist.items())))
        mean_post_mast = np.mean([r["post_mastery_visits_total"]
                                  for r in slice_results])
        lines.append(f"  Mean post-mastery visits (sum across mastered): "
                     f"{mean_post_mast:.0f}")
        mean_p3_mast = np.mean([r["p3_visits_to_mastered"]
                                for r in slice_results])
        mean_p3_unmast = np.mean([r["p3_visits_to_unmastered"]
                                  for r in slice_results])
        lines.append(f"  Mean P3 visits to mastered attractors: "
                     f"{mean_p3_mast:.1f}")
        lines.append(f"  Mean P3 visits to unmastered attractors: "
                     f"{mean_p3_unmast:.1f}")

    # --- HEADLINE: v0.10 OUTLIER ELIMINATION + CATEGORY ASSESSMENT ---
    if 20000 in args.steps:
        lines.append("\n\n--- HEADLINE: v0.10 OUTLIER ELIMINATION (cost 5.0, 20k steps) ---")
        outlier_cell = [r for r in results
                        if r["num_steps"] == 20000 and r["hazard_cost"] == 5.0]
        if outlier_cell:
            outlier_clean = sum(1 for r in outlier_cell if r["phase_3_clean"])
            lines.append(f"  v0.12 Phase 3 cleanness at cost 5.0, 20k: "
                         f"{outlier_clean}/{len(outlier_cell)}")
            if baseline:
                v112_outlier = [r for r in baseline
                                if r["num_steps"] == 20000
                                and r["hazard_cost"] == 5.0
                                and r["arch"] == "v0_11_2"]
                v10_outlier = [r for r in baseline
                               if r["num_steps"] == 20000
                               and r["hazard_cost"] == 5.0
                               and r["arch"] == "v0_10"]
                if v112_outlier:
                    v112_clean = sum(1 for r in v112_outlier
                                     if r["phase_3_clean"])
                    lines.append(f"  v0.11.2 baseline (same condition):     "
                                 f"{v112_clean}/{len(v112_outlier)}")
                if v10_outlier:
                    v10_clean = sum(1 for r in v10_outlier
                                    if r["phase_3_clean"])
                    lines.append(f"  v0.10 baseline (same condition):       "
                                 f"{v10_clean}/{len(v10_outlier)}")

    # Pre-registered Category assessment
    if 160000 in args.steps:
        lines.append("\n\n--- v0.12 PRE-REGISTERED CATEGORY ASSESSMENT ---")

        # Category A requires three things:
        # 1. Phase 3 cleanness >= 9/10 at cost 5.0, 20k
        # 2. Phase 3 cleanness >= 55/60 at 160k across all costs
        # 3. Mean attractors mastered >= 5.5/6 at 160k AND individuation
        #    Category F not triggered (signal threshold from v0.11.2)

        cat_a_check_1 = None
        cat_a_check_2 = None
        cat_a_check_3 = None

        if 20000 in args.steps:
            outlier_cell = [r for r in results
                            if r["num_steps"] == 20000
                            and r["hazard_cost"] == 5.0]
            if outlier_cell:
                outlier_clean = sum(1 for r in outlier_cell
                                    if r["phase_3_clean"])
                cat_a_check_1 = (outlier_clean >= 9)
                lines.append(f"  Check 1 (cost 5.0 @ 20k >= 9/10): "
                             f"{outlier_clean}/{len(outlier_cell)} - "
                             f"{'PASS' if cat_a_check_1 else 'FAIL'}")

        v12_160k = [r for r in results if r["num_steps"] == 160000]
        if v12_160k:
            v12_160k_clean = sum(1 for r in v12_160k if r["phase_3_clean"])
            cat_a_check_2 = (v12_160k_clean >= 55)
            lines.append(f"  Check 2 (160k all costs >= 55/60): "
                         f"{v12_160k_clean}/{len(v12_160k)} - "
                         f"{'PASS' if cat_a_check_2 else 'FAIL'}")

            # Mastery preservation
            mean_mast_160k = np.mean([r["attractors_mastered"]
                                      for r in v12_160k])
            mast_pass = (mean_mast_160k >= 5.5)
            lines.append(f"  Check 3a (mean attractors mastered >= 5.5/6 at 160k): "
                         f"{mean_mast_160k:.2f}/6 - "
                         f"{'PASS' if mast_pass else 'FAIL'}")

            # Individuation Category F (3-signal v0.11.2 framework)
            first_banks_160k = [r["first_banked"] for r in v12_160k
                                if r["first_banked"] is not None]
            unique_first_160k = set(first_banks_160k)
            sigF1 = len(unique_first_160k) < 4
            lines.append(f"    Indiv signal 1 (first-banked < 4 distinct): "
                         f"{len(unique_first_160k)}/6 distinct - "
                         f"{'TRIGGERED' if sigF1 else 'NOT triggered'}")

            sequences_160k = [r["mastery_sequence"] for r in v12_160k
                              if r["mastery_sequence"]]
            if sequences_160k:
                seq_counts_160k = Counter(sequences_160k)
                _, most_common_count_160k = seq_counts_160k.most_common(1)[0]
                pct_dom = 100 * most_common_count_160k / len(sequences_160k)
                sigF2 = pct_dom > 40
                lines.append(f"    Indiv signal 2 (dominant sequence > 40%): "
                             f"{pct_dom:.1f}% - "
                             f"{'TRIGGERED' if sigF2 else 'NOT triggered'}")
            else:
                sigF2 = False

            # Signal 3: rank vs Manhattan distance
            try:
                from scipy.stats import pearsonr
                ranks, distances = [], []
                for r in v12_160k:
                    if r["mastery_sequence"]:
                        seq_cells = r["mastery_sequence"].split("|")
                        for rank, cell_str in enumerate(seq_cells, start=1):
                            try:
                                inner = cell_str.strip("()").split(",")
                                cx, cy = int(inner[0]), int(inner[1].strip())
                                dist = (abs(cx - START_CELL[0])
                                        + abs(cy - START_CELL[1]))
                                ranks.append(rank)
                                distances.append(dist)
                            except (ValueError, IndexError):
                                pass
                if len(ranks) > 5:
                    corr, _ = pearsonr(ranks, distances)
                    sigF3 = corr > 0.7
                    lines.append(f"    Indiv signal 3 (rank vs distance r > 0.7): "
                                 f"{corr:.3f} - "
                                 f"{'TRIGGERED' if sigF3 else 'NOT triggered'}")
                else:
                    sigF3 = False
            except ImportError:
                sigF3 = False
                lines.append(f"    Indiv signal 3: scipy not available, skipped")

            indiv_triggered = sum([sigF1, sigF2, sigF3])
            indiv_ok = indiv_triggered < 2
            lines.append(f"  Check 3b (individuation Category F NOT triggered): "
                         f"{indiv_triggered}/3 signals - "
                         f"{'PASS' if indiv_ok else 'FAIL'}")

            # bool(...) cast: mast_pass and indiv_ok both derive from
            # numpy.bool_ values via np.mean comparisons. Explicit cast
            # to Python bool prevents identity-check bugs downstream.
            cat_a_check_3 = bool(mast_pass and indiv_ok)

        # Final Category A assessment.
        # Truthiness checks rather than `is True`: cat_a_check_3 derives
        # from numpy.bool_ values (mast_pass via np.mean comparison),
        # which are not Python's True singleton. `is True` returns False
        # for np.True_ and breaks the AND. Truthiness handles both
        # Python bools and numpy bools cleanly, and treats None (the
        # unset-because-block-skipped case) as falsy.
        lines.append("")
        if cat_a_check_1 and cat_a_check_2 and cat_a_check_3:
            lines.append("  CATEGORY A — full elimination of outlier with full preservation")
            lines.append("    All three pre-registered checks pass.")
        else:
            checks_failed = []
            if cat_a_check_1 is not None and not cat_a_check_1:
                checks_failed.append("outlier elimination")
            if cat_a_check_2 is not None and not cat_a_check_2:
                checks_failed.append("160k cleanness")
            if cat_a_check_3 is not None and not cat_a_check_3:
                checks_failed.append("v0.11.2 preservation")
            checks_unset = []
            if cat_a_check_1 is None:
                checks_unset.append("outlier elimination (20k not run)")
            if cat_a_check_2 is None:
                checks_unset.append("160k cleanness (160k not run)")
            if cat_a_check_3 is None:
                checks_unset.append("v0.11.2 preservation (160k not run)")
            lines.append("  CATEGORY A NOT MET")
            if checks_failed:
                lines.append(f"    Failed: {', '.join(checks_failed)}")
            if checks_unset:
                lines.append(f"    Unset (data not in batch): {', '.join(checks_unset)}")
            lines.append("    Categories B-F to be assessed against the per-")
            lines.append("    cost detail above; see v0.12-preregistration.md")
            lines.append("    Section 7 for thresholds.")

        # Category F honesty constraint (cell-type signature)
        lines.append("")
        lines.append("  CATEGORY F (HONESTY CONSTRAINT) — applies whenever the")
        lines.append("  outlier is eliminated regardless of operational success.")
        lines.append("  The v0.12 architectural claim is bounded by the cell-")
        lines.append("  type-only signature choice. v0.14+ work with richer")
        lines.append("  signatures (adjacency, environmental markers) is the")
        lines.append("  necessary follow-on to distinguish 'category-level")
        lines.append("  generalisation works' from 'existing type representation")
        lines.append("  was sufficient once unlocked'.")

        # Category D check (over-flagging)
        lines.append("")
        lines.append("  CATEGORY D (OVER-FLAGGING) check at 160k:")
        # Sub-condition: any non-hazard cell flagged. v0.12 cannot flag
        # non-hazards by construction (the category-membership check is
        # gated on the cell being a hazard via the call site in
        # record_action_outcome). We report the structural guarantee.
        lines.append("    Sub-condition 1 (non-hazard cells flagged): "
                     "structurally impossible by call site - NOT triggered")
        # Sub-condition: all hazards flagged within first 1000 steps of P2
        all_hazards_count = 5  # static
        early_p2_count = 0
        for r in v12_160k:
            p1_end = r["phase_1_end"]
            t_final = r["time_to_final_flag"]
            if (p1_end is not None and t_final is not None
                    and t_final != "" and t_final != "None"
                    and r["hazards_flagged"] == all_hazards_count
                    and int(t_final) - int(p1_end) < 1000):
                early_p2_count += 1
        lines.append(f"    Sub-condition 2 (all hazards flagged in first 1000 P2 "
                     f"steps): {early_p2_count}/{len(v12_160k)} runs")
        # Sub-condition: first_entry > n_flagged - 1 (flag on cell never entered)
        invariant_breaches = 0
        for r in v12_160k:
            if r["first_entry_conversions"] > max(0, r["hazards_flagged"] - 1):
                invariant_breaches += 1
        lines.append(f"    Sub-condition 3 (flags on cells never entered): "
                     f"{invariant_breaches}/{len(v12_160k)} invariant breaches")
        cat_d = (early_p2_count > 0 or invariant_breaches > 0)
        lines.append(f"  Category D: "
                     f"{'TRIGGERED' if cat_d else 'NOT triggered'}")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open(args.report, "w") as f:
        f.write(report_str)
    print(f"\nMeta-report saved to {args.report}")


if __name__ == "__main__":
    main()
