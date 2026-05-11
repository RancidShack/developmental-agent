"""
curiosity_agent_v1_1_batch.py
-----------------------------
v1.1 provenance-phase batch runner. Inherits the v0.14 architecture
unchanged; runs both the v1.0 recorder (for snapshot continuity with
the v1.0 audit) and the v1.1 provenance store (for the new formation
records). Outputs three CSVs:

  run_data_v1_1.csv          per-run metrics: all v1.0 fields retained
                              plus per-run provenance aggregates
  snapshots_v1_1.csv          v1.1 provenance snapshots
  provenance_v1_1.csv         per-flag formation records

Plus, when v1.0 instrumentation is enabled, a v1.0 snapshot file
(snapshots_v1_0_under_v1_1.csv by default) using the v1.0 schema.

The architecture imported from curiosity_agent_v0_14 is unchanged.
v1.1 contributes record-writing only; no agent or world modification.

Flag combinations:
  --no-instrument --no-provenance: bit-for-bit identical to v0.14
                                    baseline. Used by the v0.14
                                    pre-flight verification.
  --no-provenance only:             matches v1.0 baseline at matched
                                    seeds. The permanent regression
                                    test required by v1.1 pre-reg §6.
  (defaults):                       full v1.1 production run.

Seeds: matched to v1.0 batch via run_data_v1_0.csv.

Run from Terminal with:
    python3 curiosity_agent_v1_1_batch.py
"""

import argparse
import csv
import os
import time
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

from v1_0_recorder import V1Recorder
from v1_1_provenance import V1ProvenanceStore


CELL_TYPE_CONSTANTS = {
    "FRAME": FRAME,
    "NEUTRAL": NEUTRAL,
    "HAZARD": HAZARD,
    "ATTRACTOR": ATTRACTOR,
    "END_STATE": END_STATE,
    "KNOWLEDGE": KNOWLEDGE,
}


class V11World(StructuredGridWorld):
    """v1.1 world. Identical to v1.0/v0.14 except for the cost
    parameter. permutation_offset fixed at 0 to match the v0.14
    baseline batch."""

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
        self.agent_pos = target
        return self.observe(), target, True, 0.0


def run_one(hazard_cost, num_steps, seed, run_idx,
             instrument=True, record_provenance=True):
    """Execute one v1.1 run.

    instrument=True instantiates the v1.0 recorder.
    record_provenance=True instantiates the v1.1 provenance store.
    Both False: bit-for-bit identical to v0.14 baseline.
    instrument=True, record_provenance=False: identical to v1.0 at
        matched seeds (permanent regression test).
    Both True: full v1.1 production run.
    """
    np.random.seed(seed)

    world = V11World(hazard_cost)
    agent = V014Agent(world, num_steps)

    recorder = None
    if instrument:
        recorder = V1Recorder(
            agent=agent,
            world=world,
            run_metadata={
                "arch": "v1_1",
                "hazard_cost": hazard_cost,
                "num_steps": num_steps,
                "run_idx": run_idx,
                "seed": seed,
            },
            cell_type_constants=CELL_TYPE_CONSTANTS,
        )

    provenance = None
    if record_provenance:
        provenance = V1ProvenanceStore(
            agent=agent,
            world=world,
            run_metadata={
                "arch": "v1_1",
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

        if recorder is not None:
            recorder.on_pre_action(step)
        if provenance is not None:
            provenance.on_pre_action(step)

        if agent.phase == 1:
            action = agent.get_prescribed_action()
            if action is None:
                action = 0
        else:
            action = agent.choose_action(state)

        next_state, target_cell, success, cost_incurred = world.step(action)
        agent.record_action_outcome(target_cell, success, cost_incurred,
                                    world, step)

        if recorder is not None:
            recorder.on_post_event(step)
        if provenance is not None:
            provenance.on_post_event(step)

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

    if recorder is not None:
        recorder.on_run_end(num_steps - 1)
    if provenance is not None:
        provenance.on_run_end(num_steps - 1)

    metrics = {
        "arch": "v1_1",
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

    metrics["snapshot_count"] = (recorder.snapshot_count()
                                  if recorder is not None
                                  else 0)

    if provenance is not None:
        prov_summary = provenance.summary_metrics()
        metrics.update(prov_summary)
    else:
        for t in ["threat", "mastery", "knowledge_banking",
                  "end_state_activation", "end_state_banking"]:
            metrics[f"prov_{t}_count"] = 0
            metrics[f"prov_{t}_mean_set_step"] = None
            metrics[f"prov_{t}_mean_confirming"] = None
            metrics[f"prov_{t}_mean_disconfirming"] = None
        metrics["prov_crossref_complete"] = 0
        metrics["prov_crossref_pending"] = 0
        metrics["prov_formation_narrative"] = ""
        metrics["prov_total_records"] = 0

    return metrics, recorder, provenance


def load_baseline(path):
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
    ap.add_argument("--out", type=str, default="run_data_v1_1.csv")
    ap.add_argument("--snapshots-out", type=str,
                    default="snapshots_v1_1.csv")
    ap.add_argument("--provenance-out", type=str,
                    default="provenance_v1_1.csv")
    ap.add_argument("--v10-snapshots-out", type=str,
                    default="snapshots_v1_0_under_v1_1.csv")
    ap.add_argument("--baseline", type=str, default="run_data_v1_0.csv")
    ap.add_argument("--no-instrument", action="store_true",
                    help=("Disable v1.0 instrumentation. With "
                          "--no-instrument AND --no-provenance, output "
                          "is bit-for-bit identical to v0.14 baseline."))
    ap.add_argument("--no-provenance", action="store_true",
                    help=("Disable v1.1 provenance recording. With v1.0 "
                          "instrumentation active and provenance disabled, "
                          "this is the permanent regression test against "
                          "v1.0 baseline."))
    args = ap.parse_args()

    instrument = not args.no_instrument
    record_provenance = not args.no_provenance

    baseline = load_baseline(args.baseline)
    baseline_seeds = {}
    for r in baseline:
        if r["arch"] not in ("v1_0", "v0_14", "v0_14_repl"):
            continue
        try:
            key = (r["hazard_cost"], r["num_steps"], int(r["run_idx"]))
            seed = int(r["seed"])
            existing = baseline_seeds.get(key)
            priority = {"v1_0": 0, "v0_14": 1, "v0_14_repl": 2}
            if existing is None:
                baseline_seeds[key] = (seed, r["arch"])
            else:
                _, existing_arch = existing
                if priority.get(r["arch"], 99) < priority.get(existing_arch, 99):
                    baseline_seeds[key] = (seed, r["arch"])
        except (ValueError, KeyError):
            continue

    jobs = []
    for steps in args.steps:
        for cost in args.cost:
            for run_idx in range(args.runs):
                key = (cost, steps, run_idx)
                if key not in baseline_seeds:
                    continue
                seed, _ = baseline_seeds[key]
                jobs.append((cost, steps, run_idx, seed))

    print(f"v1.1 PROVENANCE-PHASE BATCH")
    print(f"  Architecture: v0.14 (unchanged)")
    print(f"  v1.0 instrumentation: {'ENABLED' if instrument else 'DISABLED'}")
    print(f"  v1.1 provenance:      {'ENABLED' if record_provenance else 'DISABLED'}")
    print(f"  Total runs: {len(jobs)}")
    print(f"  Per-run output:    {args.out}")
    if instrument:
        print(f"  v1.0 snapshots:    {args.v10_snapshots_out}")
    if record_provenance:
        print(f"  v1.1 snapshots:    {args.snapshots_out}")
        print(f"  Provenance output: {args.provenance_out}")
    print()

    if instrument:
        from v1_0_recorder import SNAPSHOT_FIELDS as V10_SNAPSHOT_FIELDS
        with open(args.v10_snapshots_out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=V10_SNAPSHOT_FIELDS)
            writer.writeheader()

    if record_provenance:
        from v1_1_provenance import SNAPSHOT_FIELDS as V11_SNAPSHOT_FIELDS
        from v1_1_provenance import PROVENANCE_FIELDS
        with open(args.snapshots_out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=V11_SNAPSHOT_FIELDS)
            writer.writeheader()
        with open(args.provenance_out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=PROVENANCE_FIELDS)
            writer.writeheader()

    results = []
    total_v10_snapshots = 0
    total_v11_snapshots = 0
    total_records = 0
    t_start = time.time()
    for i, (cost, steps, run_idx, seed) in enumerate(jobs):
        t0 = time.time()
        metrics, recorder, provenance = run_one(
            cost, steps, seed, run_idx,
            instrument=instrument,
            record_provenance=record_provenance,
        )
        results.append(metrics)
        if recorder is not None:
            recorder.write_csv(args.v10_snapshots_out, append=True)
            total_v10_snapshots += recorder.snapshot_count()
            recorder.reset()
        if provenance is not None:
            provenance.write_snapshots_csv(args.snapshots_out, append=True)
            provenance.write_provenance_csv(args.provenance_out, append=True)
            total_v11_snapshots += provenance.snapshot_count()
            total_records += provenance.record_count()
            provenance.reset()
        elapsed_run = time.time() - t0
        elapsed_total = time.time() - t_start
        completed = i + 1
        eta = (elapsed_total / completed) * (len(jobs) - completed)
        print(f"[{completed:>3}/{len(jobs)}] cost={cost} steps={steps} "
              f"run={run_idx}: mast={metrics['attractors_mastered']} "
              f"trans={metrics['hazards_transitioned']} "
              f"banked={metrics['hazards_banked_as_knowledge']} "
              f"act={metrics['activation_step']} "
              f"recs={metrics.get('prov_total_records', 0)} "
              f"({elapsed_run:.1f}s, ETA {eta/60:.1f}m)")

    print(f"\nv1.1 batch complete in {(time.time()-t_start)/60:.1f} minutes.")
    if instrument:
        print(f"Total v1.0 snapshots: {total_v10_snapshots}")
    if record_provenance:
        print(f"Total v1.1 snapshots: {total_v11_snapshots}")
        print(f"Total v1.1 records:   {total_records}")

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
        "prov_threat_count", "prov_threat_mean_set_step",
        "prov_threat_mean_confirming", "prov_threat_mean_disconfirming",
        "prov_mastery_count", "prov_mastery_mean_set_step",
        "prov_mastery_mean_confirming", "prov_mastery_mean_disconfirming",
        "prov_knowledge_banking_count", "prov_knowledge_banking_mean_set_step",
        "prov_knowledge_banking_mean_confirming",
        "prov_knowledge_banking_mean_disconfirming",
        "prov_end_state_activation_count",
        "prov_end_state_activation_mean_set_step",
        "prov_end_state_activation_mean_confirming",
        "prov_end_state_activation_mean_disconfirming",
        "prov_end_state_banking_count",
        "prov_end_state_banking_mean_set_step",
        "prov_end_state_banking_mean_confirming",
        "prov_end_state_banking_mean_disconfirming",
        "prov_crossref_complete", "prov_crossref_pending",
        "prov_formation_narrative", "prov_total_records",
    ]

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"Per-run data written to {args.out}")
    if instrument:
        print(f"v1.0 snapshot data written to {args.v10_snapshots_out}")
    if record_provenance:
        print(f"v1.1 snapshot data written to {args.snapshots_out}")
        print(f"v1.1 provenance records written to {args.provenance_out}")


if __name__ == "__main__":
    main()
