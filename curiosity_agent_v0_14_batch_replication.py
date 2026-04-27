"""
curiosity_agent_v0_14_batch_replication.py
-------------------------------------------
Targeted replication batch for v0.14 per the v0.14.1 amendment.

The replication uses the same architecture (v0.14), the same matched
seeds (loaded from run_data_v0_13.csv), and the same experimental
matrix (180 runs across 6 costs and 3 run lengths) as the original
v0.14 batch. The only difference is that the hazard-competency-
threshold assignment uses a permutation_offset > 0, advancing the
global RNG stream by N draws before the permutation sample, then
restoring the original state. This produces a different permutation
draw while preserving the matched-seed comparison guarantee against
v0.13 (Check 4a still passes 180/180 by construction).

The replication addresses one specific question raised by the per-cell
analysis of the original v0.14 batch: does the (cell=(5,9),
threshold=1) mean Δ(attractors_mastered) = +0.649 spike persist under
a different permutation draw, or is it a sampling artefact of one
particular ordering?

Output: run_data_v0_14_replication.csv
The original batch's CSV (run_data_v0_14.csv) is the pre-registered
data of record and is not overwritten or modified.

Run from Terminal with:
    python3 curiosity_agent_v0_14_batch_replication.py

Or with a different offset:
    python3 curiosity_agent_v0_14_batch_replication.py --offset 7
"""

import argparse
import csv
import os
import time
from collections import defaultdict
import numpy as np

from curiosity_agent_v0_14 import (
    GRID_SIZE, FEATURE_DRIVE_WEIGHT,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE,
    AVERSION_PENALTY, ATTRACTION_BONUS, FLAG_THRESHOLD,
    MASTERY_THRESHOLD, MASTERY_BONUS, KNOWLEDGE_THRESHOLD,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, START_CELL,
    StructuredGridWorld,
    DevelopmentalAgent as V014Agent,
)

# Reuse the World variant and run_one logic from the main batch runner.
# The only difference is that we construct the world with a non-zero
# permutation_offset.

class V014ReplicationWorld(StructuredGridWorld):
    """v0.14 world for the replication batch. Identical to V014World
    in the main batch runner except for the permutation_offset
    parameter, which is non-zero in the replication."""

    def __init__(self, hazard_cost, permutation_offset, size=GRID_SIZE):
        super().__init__(size=size, permutation_offset=permutation_offset)
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
        # NEUTRAL, ATTRACTOR, END_STATE, KNOWLEDGE: passable at zero cost
        self.agent_pos = target
        return self.observe(), target, True, 0.0


def run_one(hazard_cost, num_steps, seed, permutation_offset):
    """Execute one v0.14 replication run."""
    np.random.seed(seed)

    world = V014ReplicationWorld(hazard_cost, permutation_offset)
    agent = V014Agent(world, num_steps)

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

    metrics = {
        "arch": "v0_14_repl",
        "hazard_cost": hazard_cost,
        "num_steps": num_steps,
        "seed": seed,
        "permutation_offset": permutation_offset,
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
        "hazards_flagged": len(agent.cells_flagged_during_run),
        "time_to_first_flag": agent.time_to_first_flag,
        "time_to_second_flag": agent.time_to_second_flag,
        "time_to_final_flag": agent.time_to_final_flag,
        "first_entry_conversions": agent.first_entry_flag_conversions,
        "cost_on_sig_matched": agent.cost_paid_on_signature_matched_hazards,
        "actions_gated_p2": agent.hazard_gated_by_threat_layer[2],
        "actions_gated_p3": agent.hazard_gated_by_threat_layer[3],
        "attractors_mastered": len(agent.mastery_order_sequence),
        "time_to_first_mastery": agent.time_to_first_mastery,
        "time_to_final_mastery": agent.time_to_final_mastery,
        "first_banked": (str(agent.mastery_order_sequence[0])
                         if agent.mastery_order_sequence else None),
        "mastery_sequence": "|".join(
            str(c) for c in agent.mastery_order_sequence
        ),
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
        "hazards_transitioned": len(agent.transition_order_sequence),
        "hazards_banked_as_knowledge": len(agent.knowledge_banked_sequence),
        "time_to_first_transition": agent.time_to_first_transition,
        "time_to_final_transition": agent.time_to_final_transition,
        "transition_order_sequence": "|".join(
            str(c) for c in agent.transition_order_sequence
        ),
        "knowledge_banked_sequence": "|".join(
            str(c) for c in agent.knowledge_banked_sequence
        ),
    }

    sorted_hazards = sorted(world.hazard_cells)
    metrics["hazard_thresholds"] = "|".join(
        f"{c}:{world.hazard_competency_thresholds[c]}"
        for c in sorted_hazards
    )
    metrics["competency_unlock_steps"] = "|".join(
        f"{c}:{agent.competency_unlock_step.get(c)}"
        for c in sorted_hazards
    )
    metrics["knowledge_banked_steps"] = "|".join(
        f"{c}:{agent.knowledge_banked_step.get(c)}"
        for c in sorted_hazards
    )
    metrics["knowledge_entries_per_cell"] = "|".join(
        f"{c}:{agent.knowledge_entry_counter.get(c, 0)}"
        for c in sorted_hazards
    )
    metrics["pre_transition_entries_per_cell"] = "|".join(
        f"{c}:{agent.pre_transition_hazard_entries.get(c, 0)}"
        for c in sorted_hazards
    )

    post_mastery_visits = 0
    for ma in agent.mastery_order_sequence:
        total_visits = agent.attractor_visit_counter.get(ma, 0)
        post_mastery_visits += max(0, total_visits - MASTERY_THRESHOLD)
    metrics["post_mastery_visits_total"] = post_mastery_visits

    metrics["p3_visits_to_mastered"] = sum(
        v for cell, v in p3_visits_per_attractor.items()
        if agent.mastery_flag.get(cell, 0) == 1
    )
    metrics["p3_visits_to_unmastered"] = sum(
        v for cell, v in p3_visits_per_attractor.items()
        if agent.mastery_flag.get(cell, 0) == 0
    )

    attractor_prefs = {a: agent.cell_preference[a] for a in ATTRACTOR_CELLS}
    top_attractor = max(attractor_prefs, key=attractor_prefs.get)
    metrics["top_attractor"] = str(top_attractor)
    metrics["top_attractor_pref"] = attractor_prefs[top_attractor]

    metrics["phase_3_clean"] = (agent.hazard_entries_by_phase[3] < 3)
    total_entries = (agent.hazard_entries_by_phase[1]
                     + agent.hazard_entries_by_phase[2]
                     + agent.hazard_entries_by_phase[3])
    metrics["full_run_clean"] = (total_entries < 3)

    return metrics


def load_baseline(path):
    """Load v0.13 baseline CSV for matched seeds."""
    if not os.path.exists(path):
        raise RuntimeError(
            f"Baseline {path} not found; cannot proceed without seeds."
        )
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                r["hazard_cost"] = float(r["hazard_cost"])
                r["num_steps"] = int(r["num_steps"])
            except (ValueError, KeyError):
                continue
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, nargs="+",
                    default=[20000, 80000, 160000])
    ap.add_argument("--cost", type=float, nargs="+",
                    default=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--out", type=str,
                    default="run_data_v0_14_replication.csv")
    ap.add_argument("--baseline", type=str, default="run_data_v0_13.csv")
    ap.add_argument("--offset", type=int, default=1,
                    help=("Permutation offset (advances RNG by N draws "
                          "before the permutation sample). Must be > 0 "
                          "for the replication; default 1."))
    args = ap.parse_args()

    if args.offset == 0:
        raise ValueError(
            "permutation_offset must be > 0 for the replication batch. "
            "Use the main batch runner for offset = 0."
        )

    baseline = load_baseline(args.baseline)
    baseline_seeds = {}
    for r in baseline:
        if r["arch"] != "v0_13":
            continue
        try:
            key = (r["hazard_cost"], r["num_steps"], int(r["run_idx"]))
            baseline_seeds[key] = int(r["seed"])
        except (ValueError, KeyError):
            continue

    jobs = []
    for steps in args.steps:
        for cost in args.cost:
            for run_idx in range(args.runs):
                key = (cost, steps, run_idx)
                if key not in baseline_seeds:
                    continue
                seed = baseline_seeds[key]
                jobs.append((cost, steps, run_idx, seed))

    print(f"v0.14 REPLICATION batch (v0.14.1 amendment)")
    print(f"  Permutation offset: {args.offset}")
    print(f"  Total runs: {len(jobs)}")
    print(f"  Output: {args.out}")
    print()

    results = []
    t_start = time.time()
    for i, (cost, steps, run_idx, seed) in enumerate(jobs):
        t0 = time.time()
        metrics = run_one(cost, steps, seed, args.offset)
        metrics["run_idx"] = run_idx
        results.append(metrics)
        elapsed_run = time.time() - t0
        elapsed_total = time.time() - t_start
        completed = i + 1
        eta = (elapsed_total / completed) * (len(jobs) - completed)
        print(f"[{completed:>3}/{len(jobs)}] cost={cost} steps={steps} "
              f"run={run_idx}: mast={metrics['attractors_mastered']} "
              f"trans={metrics['hazards_transitioned']} "
              f"banked={metrics['hazards_banked_as_knowledge']} "
              f"act={metrics['activation_step']} "
              f"({elapsed_run:.1f}s, ETA {eta/60:.1f}m)")

    print(f"\nReplication batch complete in "
          f"{(time.time()-t_start)/60:.1f} minutes.")

    fieldnames = [
        "arch", "hazard_cost", "num_steps", "run_idx", "seed",
        "permutation_offset",
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

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"Replication data written to {args.out}")


if __name__ == "__main__":
    main()
