"""
curiosity_agent_v0_13_batch.py
------------------------------
Batch runner for v0.13 against the v0.12 baseline (matched-seed
comparison, no v0.12 re-run).

Implements the experimental matrix specified in v0.13-preregistration.md:
  - 1 architecture: v0.13 (end-state target activation via random-
    location cell on the all-attractors-mastered signal, inheriting
    v0.12 otherwise)
  - 6 cost levels: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
  - 3 run lengths: 20,000, 80,000, 160,000 steps
  - 10 runs per cell

Total: 1 x 6 x 3 x 10 = 180 runs.

Matched seeds against v0.12: run i at cost c at run length L uses
the seed recorded for the same cell in run_data_v0_12.csv. The v0.12
batch's seeds are themselves drawn from the v0.11.2 batch CSV via
the same matched-seed mechanism. The seed chain therefore links
v0.10 / v0.11.2 / v0.12 / v0.13 at every (cost, run_length, run_idx)
cell: same seed, same agent RNG state at construction, comparable
trajectories up to the divergence each architecture introduces.

The existing run_data_v0_12.csv (from the v0.12 batch) is loaded
for comparison and is not re-run. The baseline file is required;
the batch refuses to execute without it.

CLI args allow restricting to a subset:
  --steps 20000           Run only one run length (omit for all three)
  --cost 1.0              Run only one cost level (omit for all six)
  --runs 5                Override runs per cell (default 10)
  --baseline path.csv     Path to v0.12 baseline CSV
                          (default: run_data_v0_12.csv)

Pre-registered Category A Check 4: byte-identical pre-activation
behaviour against v0.12 at matched seeds. The meta-report verifies
this directly by comparing v0.13 pre-activation metrics against
v0.12's recorded values at the same (cost, run_length, run_idx)
triple. The metrics audited are those determined by pre-activation
dynamics alone: hazards_flagged, time_to_first_flag,
time_to_second_flag, time_to_final_flag, first_entry_conversions,
attractors_mastered, time_to_first_mastery, time_to_final_mastery,
mastery_sequence, first_banked, total_cost (up to activation).

Run from Terminal with:
    python3 curiosity_agent_v0_13_batch.py
"""

import argparse
import csv
import os
import time
from collections import defaultdict, Counter
import numpy as np

# Import constants and helpers from v0.13. The agent class in v0.13
# is DevelopmentalAgent; the world is StructuredGridWorld with the
# end-state cell sampling and activate_end_state method added.
from curiosity_agent_v0_13 import (
    GRID_SIZE, PHASE_3_START_FRACTION, Q_VALUE_RESET_MULTIPLIER,
    FEATURE_DRIVE_WEIGHT, FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE,
    AVERSION_PENALTY, ATTRACTION_BONUS, FLAG_THRESHOLD,
    MASTERY_THRESHOLD, MASTERY_BONUS,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, START_CELL,
    StructuredGridWorld, plan_phase_1_path, path_to_actions,
    DevelopmentalAgent as V013Agent,
)


# --------------------------------------------------------------------------
# WORLD VARIANT WITH PARAMETERISED HAZARD COST
# --------------------------------------------------------------------------

class V013World(StructuredGridWorld):
    """v0.13 world: inherits StructuredGridWorld from curiosity_agent_v0_13,
    which provides end-state cell sampling at __init__ and the
    activate_end_state method. Hazards always passable at parameterised
    cost; END_STATE cells (post-activation) passable at zero cost
    parallel to ATTRACTOR / NEUTRAL."""

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
        # NEUTRAL, ATTRACTOR, END_STATE: passable at zero cost
        self.agent_pos = target
        return self.observe(), target, True, 0.0


# --------------------------------------------------------------------------
# RUN ONE AGENT
# --------------------------------------------------------------------------

def run_one(hazard_cost, num_steps, seed):
    """Execute one v0.13 agent run. Returns a dict of per-run metrics."""
    np.random.seed(seed)

    world = V013World(hazard_cost)
    agent = V013Agent(world, num_steps)

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
    # Inherits all v0.10 / v0.11.2 / v0.12 metrics; adds five v0.13-specific
    # ones. Pre-activation metrics are byte-identical to v0.12 at matched
    # seeds by construction (see Section 7 Category A Check 4 of the v0.13
    # pre-registration); the audit verifies this in the meta-report.
    metrics = {
        "arch": "v0_13",
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
        # End-state layer metrics (v0.13 additions)
        "end_state_cell": str(world.end_state_cell),
        "activation_step": agent.activation_step,
        "end_state_found_step": agent.end_state_found_step,
        "end_state_visits": agent.end_state_visits,
        "end_state_banked": agent.end_state_banked,
        "post_activation_window": (num_steps - agent.activation_step
                                   if agent.activation_step is not None
                                   else None),
        "discovery_time": (agent.end_state_found_step - agent.activation_step
                           if (agent.activation_step is not None
                               and agent.end_state_found_step is not None)
                           else None),
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
    ap.add_argument("--out", type=str, default="run_data_v0_13.csv",
                    help="Output CSV filename.")
    ap.add_argument("--report", type=str, default="meta_report_v0_13.txt",
                    help="Output meta-report filename.")
    ap.add_argument("--baseline", type=str, default="run_data_v0_12.csv",
                    help="Path to v0.12 batch CSV for comparison.")
    args = ap.parse_args()

    # --- LOAD BASELINE FIRST (needed for matched seeds) ---
    baseline = load_baseline(args.baseline)
    print()

    # --- BUILD JOB LIST WITH MATCHED SEEDS ---
    # Critical: seeds must match the seeds used by the v0.12 batch.
    # Python's hash() of strings is randomised per interpreter session
    # (PYTHONHASHSEED defaults to random), so the same hash(...) formula
    # cannot reproduce the v0.12 seeds. Instead, the seeds are loaded
    # directly from the v0.12 CSV. This is the only way to guarantee
    # matched-seed comparison and is the methodologically correct
    # approach: the baseline's seeds are recorded data, not regenerable
    # parameters.
    if not baseline:
        raise RuntimeError(
            f"Baseline CSV {args.baseline} is required for matched-seed "
            "comparison but was not loaded. Cannot proceed without "
            "baseline seeds."
        )

    # Index baseline seeds by (cost, steps, run_idx). v0.12 batch CSV
    # contains only v0_12 architecture rows.
    baseline_seeds = {}
    for r in baseline:
        if r["arch"] != "v0_12":
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

    print(f"v0.13 batch")
    print(f"  Architecture  : v0.13 (end-state target activation)")
    print(f"  Cost levels   : {args.cost}")
    print(f"  Run lengths   : {args.steps}")
    print(f"  Runs per cell : {args.runs}")
    print(f"  Total runs    : {len(jobs)}")
    print(f"  Seeds matched : loaded from {args.baseline} (v0.12 batch)")
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
        print(f"[{completed:>3}/{len(jobs)}] v0_13 cost={cost} steps={steps} "
              f"run={run_idx}: P3_ent={metrics['hazard_entries_p3']:>3} "
              f"flagged={metrics['hazards_flagged']} "
              f"mast={metrics['attractors_mastered']} "
              f"act={metrics['activation_step']} "
              f"found={metrics['end_state_found_step']} "
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
        # v0.13 additions
        "end_state_cell", "activation_step", "end_state_found_step",
        "end_state_visits", "end_state_banked",
        "post_activation_window", "discovery_time",
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
    lines.append("v0.13 BATCH META-REPORT")
    lines.append("=" * 76)
    lines.append(f"Total runs (v0.13): {len(results)}")
    lines.append(f"Compute time: {total_elapsed/60:.1f} minutes "
                 f"({total_elapsed:.0f}s)")
    if baseline:
        lines.append(f"Baseline (v0.12): {len(baseline)} runs loaded "
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

    # --- v0.12 SIGNATURE-MATCHING PRESERVATION (inherited by v0.13) ---
    lines.append("\n\n--- v0.12 SIGNATURE-MATCHING PRESERVATION ---")
    lines.append("(v0.13 inherits v0.12's threat layer unchanged. The strict")
    lines.append(" invariant first_entry == n_flagged - 1 should hold.)")
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

    # --- v0.13 END-STATE FINDINGS (HEADLINE) ---
    lines.append("\n\n--- v0.13 END-STATE FINDINGS ---")
    for steps in sorted(set(r["num_steps"] for r in results)):
        slice_results = [r for r in results if r["num_steps"] == steps]
        lines.append(f"\nRun length {steps}:")

        # Activation rate: fraction of runs that reach all-attractors-mastered
        n_activated = sum(1 for r in slice_results
                          if r["activation_step"] is not None)
        lines.append(f"  Activation rate: {n_activated}/{len(slice_results)} "
                     f"({100*n_activated/len(slice_results):.1f}%)")

        # Discovery rate (headline): fraction of runs where the agent
        # entered the end-state cell at least once after activation
        n_discovered = sum(1 for r in slice_results
                           if r["end_state_found_step"] is not None)
        lines.append(f"  Discovery rate:  {n_discovered}/{len(slice_results)} "
                     f"({100*n_discovered/len(slice_results):.1f}%)")

        # Discovery rate among activated runs (the conditional rate that
        # tells us whether the locating mechanism works when it gets the
        # chance to operate)
        if n_activated > 0:
            cond_pct = 100 * n_discovered / n_activated
            lines.append(f"  Conditional discovery rate (given activation): "
                         f"{n_discovered}/{n_activated} ({cond_pct:.1f}%)")

        # Activation step distribution
        act_steps = [r["activation_step"] for r in slice_results
                     if r["activation_step"] is not None]
        if act_steps:
            lines.append(f"  Activation step: mean {np.mean(act_steps):.0f} "
                         f"(min {min(act_steps)}, max {max(act_steps)}, "
                         f"n={len(act_steps)})")

        # Post-activation window distribution
        windows = [r["post_activation_window"] for r in slice_results
                   if r["post_activation_window"] is not None]
        if windows:
            lines.append(f"  Post-activation window: mean {np.mean(windows):.0f} "
                         f"(min {min(windows)}, max {max(windows)})")

        # Discovery time distribution (post-activation discovery time)
        disc_times = [r["discovery_time"] for r in slice_results
                      if r["discovery_time"] is not None]
        if disc_times:
            lines.append(f"  Discovery time: mean {np.mean(disc_times):.0f} "
                         f"(min {min(disc_times)}, max {max(disc_times)}, "
                         f"n={len(disc_times)})")

    # --- v0.13 PRE-ACTIVATION AUDIT (Check 4a + 4b per v0.13.1 amendment) ---
    # Section 7 Category A Check 4 of the v0.13 pre-registration commits
    # to byte-identical pre-activation behaviour against v0.12 at matched
    # seeds. The v0.13.1 amendment splits this into two sub-checks:
    #
    # Check 4a — pre-activation byte-identical, restricted to non-activated
    # runs. For runs where activation_step is None, the architectural
    # extension v0.13 introduces had no behavioural effect, so full-run
    # metrics equal pre-activation metrics by definition. The byte-
    # identical comparison applies cleanly in this population.
    #
    # Check 4b — post-activation cross-layer effect, characterised. For
    # activated runs, divergence from v0.12 in post-activation Phase 2 /
    # Phase 3 dynamics is expected by design (the activated end-state cell
    # is a new feature-reward source whose attentional pull legitimately
    # alters subsequent trajectory). The audit operationalisation here is
    # characterisation rather than byte-identical comparison.
    lines.append("\n\n--- v0.13 CHECK 4a: PRE-ACTIVATION PRESERVATION ---")
    lines.append("(Restricted to non-activated runs per v0.13.1 amendment)")
    if not baseline:
        lines.append("  Baseline not loaded; audit skipped.")
        check_4a_pass = None
        n_4a_audited = 0
        n_4a_matching = 0
    else:
        # Build v0.12 baseline lookup
        v12_lookup = {}
        for r in baseline:
            if r["arch"] != "v0_12":
                continue
            try:
                key = (r["hazard_cost"], r["num_steps"], int(r["run_idx"]))
                v12_lookup[key] = r
            except (ValueError, KeyError):
                continue

        audit_fields = [
            "phase_1_end", "phase_2_end",
            "frame_attempts_p1", "frame_attempts_p2", "frame_attempts_p3",
            "hazard_entries_p1", "hazard_entries_p2",
            "hazards_flagged",
            "time_to_first_flag", "time_to_second_flag", "time_to_final_flag",
            "first_entry_conversions",
            "attractors_mastered",
            "time_to_first_mastery", "time_to_final_mastery",
            "first_banked", "mastery_sequence",
        ]

        # Check 4a: byte-identical comparison restricted to non-activated runs
        n_4a_audited = 0
        n_4a_matching = 0
        mismatches_4a_by_field = defaultdict(int)
        examples_4a = []
        for r13 in results:
            if r13.get("activation_step") is not None:
                continue  # activated runs handled in Check 4b
            key = (r13["hazard_cost"], r13["num_steps"], r13["run_idx"])
            if key not in v12_lookup:
                continue
            r12 = v12_lookup[key]
            n_4a_audited += 1
            run_matches = True
            run_mismatches = []
            for field in audit_fields:
                v13_val = r13.get(field)
                v12_val = r12.get(field)
                v13_str = "" if v13_val is None else str(v13_val)
                v12_str = "" if v12_val in (None, "None") else str(v12_val)
                if v13_str != v12_str:
                    run_matches = False
                    run_mismatches.append((field, v13_str, v12_str))
                    mismatches_4a_by_field[field] += 1
            if run_matches:
                n_4a_matching += 1
            elif len(examples_4a) < 3:
                examples_4a.append((key, run_mismatches))

        if n_4a_audited > 0:
            pct_4a = 100 * n_4a_matching / n_4a_audited
        else:
            pct_4a = 0.0
        check_4a_pass = (n_4a_audited > 0
                         and n_4a_matching == n_4a_audited)
        lines.append(f"  Non-activated runs audited: {n_4a_audited}")
        lines.append(f"  Byte-identical to v0.12 baseline: "
                     f"{n_4a_matching}/{n_4a_audited} ({pct_4a:.1f}%)")

        if mismatches_4a_by_field:
            lines.append(f"  Field mismatch counts:")
            for field, count in sorted(mismatches_4a_by_field.items(),
                                       key=lambda x: -x[1]):
                lines.append(f"    {field}: {count} mismatches")
            lines.append(f"  First {len(examples_4a)} mismatch examples:")
            for key, mismatches in examples_4a:
                lines.append(f"    {key}:")
                for field, v13_str, v12_str in mismatches[:3]:
                    lines.append(f"      {field}: v13={v13_str} v12={v12_str}")
                if len(mismatches) > 3:
                    lines.append(f"      ... ({len(mismatches)-3} more)")

        if check_4a_pass:
            lines.append(f"  CHECK 4a PASS: byte-identical preservation holds")
            lines.append(f"  across all {n_4a_audited} non-activated matched-seed runs.")
        elif n_4a_audited == 0:
            lines.append(f"  CHECK 4a INCONCLUSIVE: no non-activated runs in batch")
            lines.append(f"  (all runs activated; preservation cannot be tested)")
        else:
            lines.append(f"  CHECK 4a FAIL: pre-activation divergence detected.")
            lines.append(f"  This is a Category E (developmental degradation) signal")
            lines.append(f"  per the v0.13.1-amended Section 7 of the pre-registration.")

    # --- Check 4b: post-activation cross-layer effect characterisation ---
    lines.append("\n\n--- v0.13 CHECK 4b: POST-ACTIVATION CROSS-LAYER EFFECT ---")
    lines.append("(Characterisation of activated runs per v0.13.1 amendment)")
    if not baseline:
        lines.append("  Baseline not loaded; characterisation skipped.")
    else:
        # Iterate over activated runs only
        n_4b_audited = 0
        n_4b_divergent = 0
        threat_only_count = 0
        mastery_only_count = 0
        both_count = 0
        threat_fields = {"hazards_flagged", "hazard_entries_p1",
                         "hazard_entries_p2", "time_to_first_flag",
                         "time_to_second_flag", "time_to_final_flag",
                         "first_entry_conversions"}
        mastery_fields = {"attractors_mastered", "time_to_first_mastery",
                          "time_to_final_mastery", "first_banked",
                          "mastery_sequence"}
        mismatches_4b_by_field = defaultdict(int)
        # Direction analysis: count runs where v13 records a higher value
        # than v12 on each directional field, and vice versa.
        v13_higher = defaultdict(int)
        v12_higher = defaultdict(int)
        directional_fields = ["hazards_flagged", "hazard_entries_p2",
                              "first_entry_conversions"]

        for r13 in results:
            if r13.get("activation_step") is None:
                continue  # non-activated runs handled in Check 4a
            key = (r13["hazard_cost"], r13["num_steps"], r13["run_idx"])
            if key not in v12_lookup:
                continue
            r12 = v12_lookup[key]
            n_4b_audited += 1
            run_diverged = False
            diverged_fields = set()
            for field in audit_fields:
                v13_val = r13.get(field)
                v12_val = r12.get(field)
                v13_str = "" if v13_val is None else str(v13_val)
                v12_str = "" if v12_val in (None, "None") else str(v12_val)
                if v13_str != v12_str:
                    run_diverged = True
                    diverged_fields.add(field)
                    mismatches_4b_by_field[field] += 1
            if run_diverged:
                n_4b_divergent += 1
                t_div = bool(diverged_fields & threat_fields)
                m_div = bool(diverged_fields & mastery_fields)
                if t_div and m_div:
                    both_count += 1
                elif t_div:
                    threat_only_count += 1
                elif m_div:
                    mastery_only_count += 1

            # Direction analysis on directional fields
            for field in directional_fields:
                if field not in diverged_fields:
                    continue
                try:
                    v13_v = int(r13.get(field) or 0)
                    v12_v = int(r12.get(field) or 0) if r12.get(field) not in (None, "", "None") else 0
                    if v13_v > v12_v:
                        v13_higher[field] += 1
                    elif v12_v > v13_v:
                        v12_higher[field] += 1
                except (ValueError, TypeError):
                    pass

        if n_4b_audited > 0:
            pct_4b_div = 100 * n_4b_divergent / n_4b_audited
        else:
            pct_4b_div = 0.0
        lines.append(f"  Activated runs audited: {n_4b_audited}")
        lines.append(f"  Divergent from v0.12 baseline: "
                     f"{n_4b_divergent}/{n_4b_audited} ({pct_4b_div:.1f}%)")
        lines.append(f"  Divergence category breakdown:")
        lines.append(f"    Threat-layer fields only:  {threat_only_count} runs")
        lines.append(f"    Mastery-layer fields only: {mastery_only_count} runs")
        lines.append(f"    Both threat and mastery:   {both_count} runs")

        if mismatches_4b_by_field:
            lines.append(f"  Field-level divergence (top fields):")
            for field, count in sorted(mismatches_4b_by_field.items(),
                                       key=lambda x: -x[1])[:6]:
                lines.append(f"    {field}: {count} runs")

        # Direction analysis output
        if v13_higher or v12_higher:
            lines.append(f"  Direction of divergence (which architecture records higher):")
            for field in directional_fields:
                if field in v13_higher or field in v12_higher:
                    h13 = v13_higher.get(field, 0)
                    h12 = v12_higher.get(field, 0)
                    lines.append(f"    {field}: v0.13 higher in {h13}, "
                                 f"v0.12 higher in {h12}")

        # Interpretation note
        lines.append("")
        lines.append("  Note: divergence in the activated-runs population is")
        lines.append("  expected by design. The activated end-state cell is a new")
        lines.append("  feature-reward source whose attentional pull legitimately")
        lines.append("  alters the agent's subsequent trajectory. Mastery-only")
        lines.append("  divergence in this population would indicate Category E")
        lines.append("  (developmental degradation); threat-only divergence is the")
        lines.append("  cross-layer effect the v0.13.1 amendment commits to")
        lines.append("  reporting as a substantive empirical finding.")
        if mastery_only_count == 0 and both_count == 0:
            lines.append("  Mastery dynamics are byte-identical to v0.12 in all")
            lines.append(f"  {n_4b_audited} activated runs. Category E NOT triggered.")
        else:
            lines.append(f"  WARNING: {mastery_only_count + both_count} activated runs")
            lines.append(f"  show mastery-layer divergence; investigate before paper.")

    # --- v0.13 PRE-REGISTERED CATEGORY ASSESSMENT ---
    lines.append("\n\n--- v0.13 PRE-REGISTERED CATEGORY ASSESSMENT ---")

    # Per-run-length Category A discovery-rate thresholds, calibrated to
    # the post-activation window distributions in the v0.12 batch (see
    # Section 7 of the v0.13 pre-registration).
    cat_a_thresholds = {20000: 30, 80000: 50, 160000: 55}

    cat_a_checks = {}
    for steps in sorted(set(r["num_steps"] for r in results)):
        slice_results = [r for r in results if r["num_steps"] == steps]
        n_discovered = sum(1 for r in slice_results
                           if r["end_state_found_step"] is not None)
        threshold = cat_a_thresholds.get(steps)
        if threshold is not None:
            check_passes = (n_discovered >= threshold)
            cat_a_checks[steps] = check_passes
            lines.append(f"  Check (discovery rate >= {threshold}/60 at {steps} steps): "
                         f"{n_discovered}/{len(slice_results)} - "
                         f"{'PASS' if check_passes else 'FAIL'}")

    # Behavioural preservation check (Check 4a per v0.13.1 amendment):
    # references check_4a_pass computed in the audit block above. The
    # amended Check 4 is restricted to non-activated runs, where pre-
    # activation behaviour equals full-run behaviour and the byte-
    # identical comparison applies cleanly.
    if check_4a_pass is None:
        # No non-activated runs in batch (or baseline not loaded)
        preservation_pass = None
        lines.append(f"  Check 4a (byte-identical, non-activated runs only): "
                     f"INCONCLUSIVE")
        lines.append(f"    {n_4a_audited if 'n_4a_audited' in dir() else 0} "
                     f"non-activated runs in batch.")
    else:
        preservation_pass = check_4a_pass
        lines.append(f"  Check 4a (byte-identical, non-activated runs only): "
                     f"{n_4a_matching}/{n_4a_audited} - "
                     f"{'PASS' if preservation_pass else 'FAIL'}")

    # Final Category A assessment.
    all_discovery_checks_pass = all(cat_a_checks.values()) if cat_a_checks else False
    lines.append("")
    if (all_discovery_checks_pass and preservation_pass is True):
        lines.append("  CATEGORY A — successful late-target location with full preservation.")
        lines.append("    All four pre-registered checks pass.")
    else:
        lines.append("  CATEGORY A NOT MET")
        if not all_discovery_checks_pass:
            failing = [s for s, ok in cat_a_checks.items() if not ok]
            unset = [s for s in [20000, 80000, 160000] if s not in cat_a_checks]
            if failing:
                lines.append(f"    Failed: discovery rate at run length(s) {failing}")
            if unset:
                lines.append(f"    Unset (data not in batch): run length(s) {unset}")
        if preservation_pass is False:
            lines.append(f"    Failed: pre-activation behaviour diverges from v0.12")
            lines.append(f"    (this is also a Category E signal)")

    # Category F (honesty constraint).
    lines.append("")
    lines.append("  CATEGORY F (HONESTY CONSTRAINT) — applies regardless of")
    lines.append("  the operational result. The locating capability operates")
    lines.append("  through inherited v0.11.2 / v0.12 Phase 3 dynamics:")
    lines.append("  novelty drive, learning-progress drive, primitive attraction")
    lines.append("  bias, preference accumulation. v0.13 contributes the cell")
    lines.append("  type, the activation signal, and the cell-type transition;")
    lines.append("  the locating itself is performed by machinery the architecture")
    lines.append("  already had. Richer-mechanism work is reserved for v0.15+.")

    # Category D (over-activation) check.
    lines.append("")
    lines.append("  CATEGORY D (OVER-ACTIVATION) checks:")
    # Sub-condition 1: activation fires before all six attractors banked.
    # Detectable by comparing activation_step against the time at which
    # attractors_mastered reaches 6.
    cat_d_early = 0
    for r in results:
        if (r["activation_step"] is not None
                and r["attractors_mastered"] != 6
                and r["attractors_mastered"] != "6"):
            cat_d_early += 1
    lines.append(f"    Sub-condition 1 (activation fires before 6/6 mastered): "
                 f"{cat_d_early}/{len(results)} runs")

    # Sub-condition 2: end_state_found_step earlier than activation_step.
    cat_d_premature = 0
    for r in results:
        if (r["end_state_found_step"] is not None
                and r["activation_step"] is not None
                and int(r["end_state_found_step"]) < int(r["activation_step"])):
            cat_d_premature += 1
    lines.append(f"    Sub-condition 2 (end-state found before activation): "
                 f"{cat_d_premature}/{len(results)} runs")

    cat_d_triggered = (cat_d_early > 0 or cat_d_premature > 0)
    lines.append(f"  Category D: "
                 f"{'TRIGGERED' if cat_d_triggered else 'NOT triggered'}")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open(args.report, "w") as f:
        f.write(report_str)
    print(f"\nMeta-report saved to {args.report}")


if __name__ == "__main__":
    main()
