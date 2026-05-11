"""
curiosity_agent_v1_0_batch.py
-----------------------------
v1.0 integration audit batch runner. Runs the v0.14 architecture
under matched seeds with v1.0 heavy instrumentation enabled,
producing two outputs:

  run_data_v1_0.csv          — per-run metrics (all v0.14 fields
                                 retained; v1.0 adds none at the
                                 per-run level, which is by design:
                                 v1.0's contribution is the snapshot
                                 CSV, not new aggregate metrics)
  snapshots_v1_0.csv         — per-snapshot heavy instrumentation,
                                 ~22 events × 3 snapshots per run,
                                 across 180 runs

Architecture: v0.14 (unchanged). The v0.14 Python module is imported
verbatim. The recorder is a separate layer with read-only access.
With instrumentation disabled (the --no-instrument flag), the batch
output is bit-for-bit identical to the existing v0.14 batch output.

Seeds: matched to the existing inheritance chain via
run_data_v0_14.csv (v0.14 batch from Baker, 2026m).

Run from Terminal with:
    python3 curiosity_agent_v1_0_batch.py

Or with smaller test scope:
    python3 curiosity_agent_v1_0_batch.py --steps 20000 --runs 2
"""

import argparse
import csv
import os
import sys
import time
import numpy as np

# v0.14 architecture, imported verbatim.
from curiosity_agent_v0_14 import (
    GRID_SIZE, FEATURE_DRIVE_WEIGHT,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE,
    AVERSION_PENALTY, ATTRACTION_BONUS, FLAG_THRESHOLD,
    MASTERY_THRESHOLD, MASTERY_BONUS, KNOWLEDGE_THRESHOLD,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, START_CELL,
    StructuredGridWorld,
    DevelopmentalAgent as V014Agent,
)

from v1_0_recorder import V1Recorder


# Cell-type constants dict for the recorder.
CELL_TYPE_CONSTANTS = {
    "FRAME": FRAME,
    "NEUTRAL": NEUTRAL,
    "HAZARD": HAZARD,
    "ATTRACTOR": ATTRACTOR,
    "END_STATE": END_STATE,
    "KNOWLEDGE": KNOWLEDGE,
}


class V10World(StructuredGridWorld):
    """v1.0 world. Identical to the v0.14 world except for the cost
    parameter. permutation_offset is fixed at 0 to match the v0.14
    baseline batch (the v0.14.1 amendment's offset > 0 case is for the
    replication batch, not v1.0)."""

    def __init__(self, hazard_cost, size=GRID_SIZE):
        super().__init__(size=size, permutation_offset=0)
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
        # NEUTRAL, ATTRACTOR, END_STATE, KNOWLEDGE: passable, zero cost
        self.agent_pos = target
        return self.observe(), target, True, 0.0


def run_one(hazard_cost, num_steps, seed, run_idx, instrument=True):
    """Execute one v1.0 run.

    With instrument=True, the V1Recorder is hooked in at three points
    in the main loop. With instrument=False, the recorder is not
    instantiated and the run produces v0.14-identical output (used to
    verify the instrumentation does not affect agent behaviour).

    Returns:
      metrics: per-run aggregate metrics (same schema as v0.14 batch)
      recorder: the V1Recorder instance with accumulated snapshots,
                or None if instrument=False
    """
    np.random.seed(seed)

    world = V10World(hazard_cost)
    agent = V014Agent(world, num_steps)

    recorder = None
    if instrument:
        recorder = V1Recorder(
            agent=agent,
            world=world,
            run_metadata={
                "arch": "v1_0",
                "hazard_cost": hazard_cost,
                "num_steps": num_steps,
                "run_idx": run_idx,
                "seed": seed,
            },
            cell_type_constants=CELL_TYPE_CONSTANTS,
        )

    state = world.observe()
    p3_visits_per_attractor = {a: 0 for a in ATTRACTOR_CELLS}

    for step in range(num_steps):
        agent.steps_taken = step
        agent.check_phase_transition()

        # v1.0 instrumentation hook: pre-action.
        if recorder is not None:
            recorder.on_pre_action(step)

        if agent.phase == 1:
            action = agent.get_prescribed_action()
            if action is None:
                action = 0
        else:
            action = agent.choose_action(state)

        next_state, target_cell, success, cost_incurred = world.step(action)
        agent.record_action_outcome(target_cell, success, cost_incurred,
                                    world, step)

        # v1.0 instrumentation hook: post-event. Detects coupling events
        # that fired during record_action_outcome and captures snapshots.
        if recorder is not None:
            recorder.on_post_event(step)

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

    # v1.0 instrumentation hook: end of run. Flush any pending after-
    # snapshots.
    if recorder is not None:
        recorder.on_run_end(num_steps - 1)

    metrics = {
        "arch": "v1_0",
        "hazard_cost": hazard_cost,
        "num_steps": num_steps,
        "seed": seed,
        "run_idx": run_idx,
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

    # v1.0 additions: snapshot count for the run, and a sanity-check
    # event count that the analysis can compare against the per-run
    # metrics' transition / banking counts.
    metrics["snapshot_count"] = (recorder.snapshot_count()
                                  if recorder is not None
                                  else 0)

    return metrics, recorder


def load_baseline(path):
    """Load the v0.14 baseline CSV for matched seeds. The seed chain
    links v0.10 -> v0.11.2 -> v0.12 -> v0.13 -> v0.14 -> v1.0 at every
    (cost, run length, run index) cell."""
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
                    default="run_data_v1_0.csv")
    ap.add_argument("--snapshots-out", type=str,
                    default="snapshots_v1_0.csv")
    ap.add_argument("--baseline", type=str, default="run_data_v0_14.csv")
    ap.add_argument("--no-instrument", action="store_true",
                    help=("Disable instrumentation. With this flag, "
                          "output is bit-for-bit identical to the v0.14 "
                          "batch. Used to verify instrumentation does "
                          "not affect agent behaviour."))
    ap.add_argument("--seed-from-baseline-steps", type=int, default=None,
                    help=("If set, pull seeds from the baseline at this "
                          "num_steps value, ignoring the --steps argument "
                          "for seed matching. Used by the v1.0.2 extended "
                          "batch (Baker, 2026r) where target run length "
                          "(e.g. 320000) differs from the baseline's "
                          "available run lengths (20000, 80000, 160000). "
                          "Matched-seed comparability holds because the "
                          "agent's seed and pre-target-step trajectory "
                          "are identical to the baseline run at "
                          "(cost, baseline_steps, run_idx)."))
    args = ap.parse_args()

    instrument = not args.no_instrument

    baseline = load_baseline(args.baseline)
    baseline_seeds = {}
    for r in baseline:
        if r["arch"] not in ("v0_14", "v0_14_repl"):
            continue
        # Prefer v0_14 (offset=0) over v0_14_repl when both present.
        try:
            key = (r["hazard_cost"], r["num_steps"], int(r["run_idx"]))
            seed = int(r["seed"])
            if key in baseline_seeds and r["arch"] == "v0_14_repl":
                continue  # v0_14 takes precedence
            baseline_seeds[key] = seed
        except (ValueError, KeyError):
            continue

    jobs = []
    for steps in args.steps:
        for cost in args.cost:
            for run_idx in range(args.runs):
                # Determine which baseline (cost, steps, run_idx) to
                # pull the seed from. By default, match the run's own
                # num_steps; if --seed-from-baseline-steps is set, use
                # that instead (for the v1.0.2 extended batch).
                lookup_steps = (args.seed_from_baseline_steps
                                if args.seed_from_baseline_steps is not None
                                else steps)
                key = (cost, lookup_steps, run_idx)
                if key not in baseline_seeds:
                    continue
                seed = baseline_seeds[key]
                jobs.append((cost, steps, run_idx, seed))

    print(f"v1.0 INTEGRATION AUDIT BATCH")
    print(f"  Architecture: v0.14 (unchanged)")
    print(f"  Instrumentation: {'ENABLED' if instrument else 'DISABLED'}")
    print(f"  Total runs: {len(jobs)}")
    print(f"  Per-run output: {args.out}")
    print(f"  Snapshots output: {args.snapshots_out}")
    print()

    # Initialise the snapshot CSV with a header before the first run.
    # Subsequent runs append. This streams snapshot data to disk
    # incrementally rather than holding all 180 runs' snapshots in
    # memory at once.
    if instrument:
        # Clear / initialise the snapshots file by writing the header.
        from v1_0_recorder import SNAPSHOT_FIELDS
        with open(args.snapshots_out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SNAPSHOT_FIELDS)
            writer.writeheader()

    results = []
    total_snapshots = 0
    t_start = time.time()
    for i, (cost, steps, run_idx, seed) in enumerate(jobs):
        t0 = time.time()
        metrics, recorder = run_one(cost, steps, seed, run_idx,
                                     instrument=instrument)
        results.append(metrics)
        # Stream snapshots to disk and clear recorder memory.
        if recorder is not None:
            recorder.write_csv(args.snapshots_out, append=True)
            total_snapshots += recorder.snapshot_count()
            recorder.reset()
        elapsed_run = time.time() - t0
        elapsed_total = time.time() - t_start
        completed = i + 1
        eta = (elapsed_total / completed) * (len(jobs) - completed)
        print(f"[{completed:>3}/{len(jobs)}] cost={cost} steps={steps} "
              f"run={run_idx}: mast={metrics['attractors_mastered']} "
              f"trans={metrics['hazards_transitioned']} "
              f"banked={metrics['hazards_banked_as_knowledge']} "
              f"act={metrics['activation_step']} "
              f"snap={metrics['snapshot_count']} "
              f"({elapsed_run:.1f}s, ETA {eta/60:.1f}m)")

    print(f"\nv1.0 batch complete in {(time.time()-t_start)/60:.1f} minutes.")
    if instrument:
        print(f"Total snapshots: {total_snapshots}")

    fieldnames = [
        "arch", "hazard_cost", "num_steps", "run_idx", "seed",
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
        "snapshot_count",
    ]

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"Per-run data written to {args.out}")
    if instrument:
        print(f"Snapshot data written to {args.snapshots_out}")


if __name__ == "__main__":
    main()
