"""
curiosity_agent_v0_14_batch.py
------------------------------
Batch runner for v0.14 against the v0.13 baseline (matched-seed
comparison, no v0.13 re-run).

Implements the experimental matrix specified in v0.14-prereg.md:
  - 1 architecture: v0.14 (competency-gated content transformation
    of hazard cells into knowledge cells, with amended end-state
    activation trigger; inheriting v0.13 otherwise)
  - 6 cost levels: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
  - 3 run lengths: 20,000, 80,000, 160,000 steps
  - 10 runs per cell

Total: 1 x 6 x 3 x 10 = 180 runs.

Matched seeds against v0.13: run i at cost c at run length L uses
the seed recorded for the same cell in run_data_v0_13.csv. The
v0.13 batch's seeds were themselves drawn from the v0.12 batch CSV
via the same matched-seed mechanism. The seed chain therefore
links v0.10 / v0.11.2 / v0.12 / v0.13 / v0.14 at every (cost,
run_length, run_idx) cell: same seed, same agent RNG state at
construction, comparable trajectories up to the divergence each
architecture introduces.

The existing run_data_v0_13.csv is loaded for comparison and is
not re-run. The baseline file is required; the batch refuses to
execute without it.

Pre-registered Category A Check 4a (per v0.14 pre-reg Section 6,
calibrated under the v0.13.1-amendment lesson on temporal-scope
restriction): byte-identical pre-first-transition behaviour
against v0.13 at matched seeds. 'Pre-first-transition' is
operationalised as 'behaviour up to first attractor banking',
because the cell with assigned threshold 1 transitions at the
step the first attractor is banked. Audit fields are those whose
values are determined by behaviour through first attractor
banking.

Pre-registered Category A Check 4b (cross-layer effects): three
hypotheses pre-registered in Section 5.3 of v0.14-prereg.md.
Audit reports characteristically (per-run divergence counts and
directional analysis) rather than testing thresholds.

Run from Terminal with:
    python3 curiosity_agent_v0_14_batch.py
"""

import argparse
import csv
import os
import time
from collections import defaultdict, Counter
import numpy as np

from curiosity_agent_v0_14 import (
    GRID_SIZE, PHASE_3_START_FRACTION, Q_VALUE_RESET_MULTIPLIER,
    FEATURE_DRIVE_WEIGHT,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE,
    AVERSION_PENALTY, ATTRACTION_BONUS, FLAG_THRESHOLD,
    MASTERY_THRESHOLD, MASTERY_BONUS, KNOWLEDGE_THRESHOLD,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, START_CELL,
    StructuredGridWorld, plan_phase_1_path, path_to_actions,
    DevelopmentalAgent as V014Agent,
)


# --------------------------------------------------------------------------
# WORLD VARIANT WITH PARAMETERISED HAZARD COST
# --------------------------------------------------------------------------

class V014World(StructuredGridWorld):
    """v0.14 world: inherits StructuredGridWorld from
    curiosity_agent_v0_14, which provides hazard competency-threshold
    assignment and end-state cell sampling at __init__, plus
    transition_hazard_to_knowledge and activate_end_state methods.
    Hazards always passable at parameterised cost; KNOWLEDGE cells
    (post-transition) passable at zero cost parallel to ATTRACTOR /
    NEUTRAL / END_STATE."""

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
        # NEUTRAL, ATTRACTOR, END_STATE, KNOWLEDGE: passable at zero cost
        self.agent_pos = target
        return self.observe(), target, True, 0.0


# --------------------------------------------------------------------------
# RUN ONE AGENT
# --------------------------------------------------------------------------

def run_one(hazard_cost, num_steps, seed):
    """Execute one v0.14 agent run. Returns a dict of per-run metrics."""
    np.random.seed(seed)

    world = V014World(hazard_cost)
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

    # --- COMPUTE METRICS ---
    metrics = {
        "arch": "v0_14",
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
        # Threat-layer metrics
        "hazards_flagged": len(agent.cells_flagged_during_run),
        "time_to_first_flag": agent.time_to_first_flag,
        "time_to_second_flag": agent.time_to_second_flag,
        "time_to_final_flag": agent.time_to_final_flag,
        "first_entry_conversions": agent.first_entry_flag_conversions,
        "cost_on_sig_matched": agent.cost_paid_on_signature_matched_hazards,
        "actions_gated_p2": agent.hazard_gated_by_threat_layer[2],
        "actions_gated_p3": agent.hazard_gated_by_threat_layer[3],
        # Mastery-layer metrics
        "attractors_mastered": len(agent.mastery_order_sequence),
        "time_to_first_mastery": agent.time_to_first_mastery,
        "time_to_final_mastery": agent.time_to_final_mastery,
        "first_banked": (str(agent.mastery_order_sequence[0])
                         if agent.mastery_order_sequence else None),
        "mastery_sequence": "|".join(
            str(c) for c in agent.mastery_order_sequence
        ),
        # End-state-layer metrics (v0.13, v0.14-amended trigger)
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
        # Knowledge-layer metrics (v0.14 additions)
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

    # Per-cell threshold and timing — serialised compactly for the CSV.
    # Each hazard cell gets entries for: assigned threshold, unlock step,
    # banked step, knowledge entries (post-transition), pre-transition
    # hazard entries.
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

    # Top attractor by preference
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
# BASELINE LOADING (v0.13 CSV)
# --------------------------------------------------------------------------

def load_baseline(path):
    """Load existing v0.13 batch CSV. Returns list of dicts with typed
    fields. Used for matched-seed comparison and the Check 4a / 4b
    audits; baseline runs are not re-executed."""
    if not os.path.exists(path):
        print(f"  [baseline] File {path} not found — comparisons will be skipped.")
        return []
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
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
    ap.add_argument("--out", type=str, default="run_data_v0_14.csv",
                    help="Output CSV filename.")
    ap.add_argument("--report", type=str, default="meta_report_v0_14.txt",
                    help="Output meta-report filename.")
    ap.add_argument("--baseline", type=str, default="run_data_v0_13.csv",
                    help="Path to v0.13 batch CSV for comparison.")
    args = ap.parse_args()

    # --- LOAD BASELINE FIRST (needed for matched seeds) ---
    baseline = load_baseline(args.baseline)
    print()

    # --- BUILD JOB LIST WITH MATCHED SEEDS ---
    if not baseline:
        raise RuntimeError(
            f"Baseline CSV {args.baseline} is required for matched-seed "
            "comparison but was not loaded. Cannot proceed without "
            "baseline seeds."
        )

    baseline_seeds = {}
    for r in baseline:
        if r["arch"] != "v0_13":
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

    print(f"v0.14 batch")
    print(f"  Architecture  : v0.14 (competency-gated content transformation)")
    print(f"  Cost levels   : {args.cost}")
    print(f"  Run lengths   : {args.steps}")
    print(f"  Runs per cell : {args.runs}")
    print(f"  Total runs    : {len(jobs)}")
    print(f"  Seeds matched : loaded from {args.baseline} (v0.13 batch)")
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
        print(f"[{completed:>3}/{len(jobs)}] v0_14 cost={cost} steps={steps} "
              f"run={run_idx}: P3_ent={metrics['hazard_entries_p3']:>3} "
              f"flagged={metrics['hazards_flagged']} "
              f"mast={metrics['attractors_mastered']} "
              f"trans={metrics['hazards_transitioned']} "
              f"banked={metrics['hazards_banked_as_knowledge']} "
              f"act={metrics['activation_step']} "
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
    print(f"Per-run data written to {args.out}")

    # --- META-REPORT ---
    write_meta_report(args.report, results, baseline, args)


def write_meta_report(report_path, results, baseline, args):
    """Generate the v0.14 meta-report. Includes:
      - Per-(cost, run_length) summary statistics
      - Knowledge-layer aggregate findings (transition rates, banking
        rates, post-transition delay distributions)
      - End-state activation findings under the v0.14-amended trigger
      - Check 4a: byte-identical preservation against v0.13 in the
        pre-first-transition window (operationalised as 'behaviour
        through first attractor banking')
      - Check 4b: three pre-registered cross-layer effect audits
    """
    lines = []
    lines.append("=" * 72)
    lines.append("v0.14 META-REPORT")
    lines.append(
        "Competency-gated content transformation of hazard cells "
        "into knowledge cells"
    )
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Total runs: {len(results)}")
    lines.append(f"Cost levels: {sorted(set(r['hazard_cost'] for r in results))}")
    lines.append(f"Run lengths: {sorted(set(r['num_steps'] for r in results))}")
    lines.append("")

    # --- KNOWLEDGE LAYER AGGREGATE FINDINGS ---
    lines.append("=" * 72)
    lines.append("KNOWLEDGE LAYER (v0.14)")
    lines.append("=" * 72)
    for run_length in sorted(set(r["num_steps"] for r in results)):
        subset = [r for r in results if r["num_steps"] == run_length]
        n_total = len(subset)
        # Aggregate transitions and banking
        transitions = [r["hazards_transitioned"] for r in subset]
        bankings = [r["hazards_banked_as_knowledge"] for r in subset]
        full_transitions = sum(1 for t in transitions if t == 5)
        full_bankings = sum(1 for b in bankings if b == 5)
        lines.append(f"\nRun length: {run_length}")
        lines.append(f"  Runs                          : {n_total}")
        lines.append(f"  Mean hazards transitioned     : "
                     f"{np.mean(transitions):.2f} of 5")
        lines.append(f"  Mean hazards banked as kn.    : "
                     f"{np.mean(bankings):.2f} of 5")
        lines.append(f"  Runs with all 5 transitioned  : "
                     f"{full_transitions}/{n_total}")
        lines.append(f"  Runs with all 5 banked        : "
                     f"{full_bankings}/{n_total}")
        # End-state activation rate (v0.14-amended trigger)
        activated = sum(1 for r in subset
                        if r["activation_step"] is not None)
        found = sum(1 for r in subset
                    if r["end_state_found_step"] is not None)
        lines.append(f"  End-state activated (v0.14)   : "
                     f"{activated}/{n_total}")
        lines.append(f"  End-state found post-activation: "
                     f"{found}/{n_total}")
        if activated > 0:
            cond_disc = 100 * found / activated
            lines.append(f"  Conditional discovery rate    : "
                         f"{cond_disc:.1f}%")
        # Post-transition delay distribution (mean across all
        # transitioned cells in this subset that were entered at least
        # once post-transition).
        delays = []
        for r in subset:
            unlock_str = r.get("competency_unlock_steps", "")
            kn_entries_str = r.get("knowledge_entries_per_cell", "")
            # We don't have per-cell first-entry steps in the CSV;
            # the delay distribution will be reported in the standalone
            # analysis utility. For now, report the count of cells
            # with at least one post-transition entry.
        # First-entry-after-transition rate among transitioned cells
        cells_first_entered = 0
        cells_transitioned_total = 0
        for r in subset:
            kn_entries_str = r.get("knowledge_entries_per_cell", "")
            unlock_str = r.get("competency_unlock_steps", "")
            # Parse the per-cell strings: format "(x,y):value|..."
            entries_by_cell = _parse_cell_dict(kn_entries_str)
            unlocks_by_cell = _parse_cell_dict(unlock_str)
            for cell, unlock_val in unlocks_by_cell.items():
                if unlock_val in (None, "None", ""):
                    continue
                cells_transitioned_total += 1
                kn_count = entries_by_cell.get(cell, 0)
                try:
                    if int(kn_count) >= 1:
                        cells_first_entered += 1
                except (ValueError, TypeError):
                    pass
        if cells_transitioned_total > 0:
            pct = 100 * cells_first_entered / cells_transitioned_total
            lines.append(f"  Post-transition first-entry rate (per cell):")
            lines.append(f"    {cells_first_entered}/{cells_transitioned_total} "
                         f"({pct:.1f}%)")

    # --- CHECK 4a: BYTE-IDENTICAL PRESERVATION ---
    # Operationalised as 'behaviour up to first attractor banking
    # matches v0.13'. The audit fields are those whose values are
    # determined by behaviour through first attractor banking.
    # Specifically: phase_1_end, phase_2_end, frame_attempts_p1,
    # hazard_entries_p1 (always pre-first-banking because phase 1
    # uses prescribed actions), and time_to_first_mastery.
    #
    # Fields like phase_2_end and frame_attempts_p2 / p3 cover
    # post-first-banking periods and are not part of Check 4a.
    # These are characterised under Check 4b instead.
    lines.append("\n\n--- v0.14 CHECK 4a: PRE-FIRST-TRANSITION PRESERVATION ---")
    lines.append("(Behaviour up to first attractor banking matches v0.13)")

    if not baseline:
        lines.append("  Baseline not loaded; audit skipped.")
    else:
        v13_lookup = {}
        for r in baseline:
            if r["arch"] != "v0_13":
                continue
            try:
                key = (r["hazard_cost"], r["num_steps"], int(r["run_idx"]))
                v13_lookup[key] = r
            except (ValueError, KeyError):
                continue

        # Audit fields restricted to the pre-first-transition window.
        # In v0.14, the threshold-1 cell transitions at the step the
        # first attractor is mastered. Fields determined by behaviour
        # through that point:
        #   - phase_1_end (Phase 1 ends before any mastery; deterministic
        #     via the prescribed path)
        #   - frame_attempts_p1 (Phase 1 only)
        #   - hazard_entries_p1 (Phase 1 only)
        #   - time_to_first_mastery (the moment first attractor is
        #     banked, equivalent to first transition)
        #   - first_banked (which attractor reached mastery first)
        # Note: hazards_flagged through first mastery is harder to
        # extract from aggregate CSV fields, so we rely on
        # time_to_first_flag with the caveat that it may exceed
        # time_to_first_mastery in some runs. We include it but
        # interpret divergence carefully.
        audit_fields = [
            "phase_1_end",
            "frame_attempts_p1",
            "hazard_entries_p1",
            "time_to_first_mastery",
            "first_banked",
        ]

        n_audited = 0
        n_matching = 0
        mismatches_by_field = defaultdict(int)
        examples = []
        for r14 in results:
            key = (r14["hazard_cost"], r14["num_steps"], r14["run_idx"])
            if key not in v13_lookup:
                continue
            r13 = v13_lookup[key]
            n_audited += 1
            run_matches = True
            run_mismatches = []
            for field in audit_fields:
                v14_val = r14.get(field)
                v13_val = r13.get(field)
                v14_str = "" if v14_val is None else str(v14_val)
                v13_str = "" if v13_val in (None, "None") else str(v13_val)
                if v14_str != v13_str:
                    run_matches = False
                    run_mismatches.append((field, v14_str, v13_str))
                    mismatches_by_field[field] += 1
            if run_matches:
                n_matching += 1
            elif len(examples) < 3:
                examples.append((key, run_mismatches))

        if n_audited > 0:
            pct = 100 * n_matching / n_audited
        else:
            pct = 0.0
        check_4a_pass = (n_audited > 0 and n_matching == n_audited)
        lines.append(f"  Runs audited: {n_audited}")
        lines.append(f"  Byte-identical to v0.13 baseline (pre-first-transition fields):")
        lines.append(f"    {n_matching}/{n_audited} ({pct:.1f}%)")

        if mismatches_by_field:
            lines.append(f"  Field mismatch counts:")
            for field, count in sorted(mismatches_by_field.items(),
                                       key=lambda x: -x[1]):
                lines.append(f"    {field}: {count} mismatches")
            lines.append(f"  First {len(examples)} mismatch examples:")
            for key, mismatches in examples:
                lines.append(f"    {key}:")
                for field, v14_str, v13_str in mismatches[:3]:
                    lines.append(f"      {field}: v14={v14_str} v13={v13_str}")

        if check_4a_pass:
            lines.append(f"  CHECK 4a PASS: byte-identical preservation holds")
            lines.append(f"  across all {n_audited} matched-seed runs in the")
            lines.append(f"  pre-first-transition window.")
        elif n_audited == 0:
            lines.append(f"  CHECK 4a INCONCLUSIVE: no matched runs in batch")
        else:
            lines.append(f"  CHECK 4a FAIL: pre-first-transition divergence detected.")
            lines.append(f"  This is a Category E (developmental degradation) signal")
            lines.append(f"  per Section 6.5 of v0.14-prereg.md.")

    # --- CHECK 4b: CROSS-LAYER EFFECT AUDITS ---
    # Three hypotheses pre-registered in Section 5.3 of v0.14-prereg.md:
    #   H1: competency-unlock affects threat-side encounter
    #   H2: knowledge-cell engagement affects subsequent attractor mastery
    #   H3: end-state activation timing affects full-run cleanness
    # Each audit measures per-run divergence on the relevant fields
    # against v0.13 at matched seeds.
    lines.append("\n\n--- v0.14 CHECK 4b: CROSS-LAYER EFFECT AUDITS ---")
    lines.append("(Three pre-registered hypotheses; characterisation only)")

    if not baseline:
        lines.append("  Baseline not loaded; audits skipped.")
    else:
        v13_lookup = {
            (r["hazard_cost"], r["num_steps"], int(r["run_idx"])): r
            for r in baseline if r["arch"] == "v0_13"
        }

        # H1: Competency-unlock affects threat-side encounter.
        # Restricted to runs where at least one transition fired.
        lines.append("\n  Hypothesis 1: competency-unlock affects threat-side encounter")
        lines.append("  Fields audited: hazards_flagged, time_to_final_flag")
        h1_audited = 0
        h1_diverge = {"hazards_flagged": 0, "time_to_final_flag": 0}
        h1_direction_higher_v14 = {"hazards_flagged": 0, "time_to_final_flag": 0}
        h1_direction_higher_v13 = {"hazards_flagged": 0, "time_to_final_flag": 0}
        for r14 in results:
            if r14.get("hazards_transitioned", 0) == 0:
                continue
            key = (r14["hazard_cost"], r14["num_steps"], r14["run_idx"])
            if key not in v13_lookup:
                continue
            r13 = v13_lookup[key]
            h1_audited += 1
            for field in ["hazards_flagged", "time_to_final_flag"]:
                v14_val = r14.get(field)
                v13_val = r13.get(field)
                v14_str = "" if v14_val is None else str(v14_val)
                v13_str = "" if v13_val in (None, "None") else str(v13_val)
                if v14_str != v13_str:
                    h1_diverge[field] += 1
                    try:
                        v14_int = float(v14_val) if v14_val not in (None, "") else None
                        v13_int = float(v13_val) if v13_val not in (None, "None", "") else None
                        if v14_int is not None and v13_int is not None:
                            if v14_int > v13_int:
                                h1_direction_higher_v14[field] += 1
                            elif v13_int > v14_int:
                                h1_direction_higher_v13[field] += 1
                    except (ValueError, TypeError):
                        pass
        lines.append(f"    Activated runs audited: {h1_audited}")
        for field in ["hazards_flagged", "time_to_final_flag"]:
            if h1_audited > 0:
                pct = 100 * h1_diverge[field] / h1_audited
                lines.append(f"    {field}: divergent in {h1_diverge[field]}/{h1_audited} "
                             f"({pct:.1f}%); v14 higher in {h1_direction_higher_v14[field]}, "
                             f"v13 higher in {h1_direction_higher_v13[field]}")

        # H2: Knowledge-cell engagement affects subsequent attractor mastery.
        # Audited on time_to_final_mastery (and time_to_first_mastery as
        # a baseline that should not diverge given Check 4a).
        lines.append("\n  Hypothesis 2: knowledge-cell engagement affects subsequent mastery")
        lines.append("  Fields audited: time_to_final_mastery, attractors_mastered")
        h2_audited = 0
        h2_diverge = {"time_to_final_mastery": 0, "attractors_mastered": 0}
        h2_direction_higher_v14 = {"time_to_final_mastery": 0, "attractors_mastered": 0}
        h2_direction_higher_v13 = {"time_to_final_mastery": 0, "attractors_mastered": 0}
        for r14 in results:
            if r14.get("hazards_transitioned", 0) == 0:
                continue
            key = (r14["hazard_cost"], r14["num_steps"], r14["run_idx"])
            if key not in v13_lookup:
                continue
            r13 = v13_lookup[key]
            h2_audited += 1
            for field in ["time_to_final_mastery", "attractors_mastered"]:
                v14_val = r14.get(field)
                v13_val = r13.get(field)
                v14_str = "" if v14_val is None else str(v14_val)
                v13_str = "" if v13_val in (None, "None") else str(v13_val)
                if v14_str != v13_str:
                    h2_diverge[field] += 1
                    try:
                        v14_int = float(v14_val) if v14_val not in (None, "") else None
                        v13_int = float(v13_val) if v13_val not in (None, "None", "") else None
                        if v14_int is not None and v13_int is not None:
                            if v14_int > v13_int:
                                h2_direction_higher_v14[field] += 1
                            elif v13_int > v14_int:
                                h2_direction_higher_v13[field] += 1
                    except (ValueError, TypeError):
                        pass
        lines.append(f"    Activated runs audited: {h2_audited}")
        for field in ["time_to_final_mastery", "attractors_mastered"]:
            if h2_audited > 0:
                pct = 100 * h2_diverge[field] / h2_audited
                lines.append(f"    {field}: divergent in {h2_diverge[field]}/{h2_audited} "
                             f"({pct:.1f}%); v14 higher in {h2_direction_higher_v14[field]}, "
                             f"v13 higher in {h2_direction_higher_v13[field]}")

        # H3: End-state activation timing affects full-run cleanness.
        # Restricted to runs where end-state activation fires under both
        # architectures.
        lines.append("\n  Hypothesis 3: end-state activation timing affects full-run cleanness")
        lines.append("  Fields audited: activation_step, end_state_found_step, hazard_entries_p3")
        h3_audited = 0
        h3_diverge = {"activation_step": 0, "end_state_found_step": 0, "hazard_entries_p3": 0}
        for r14 in results:
            if r14.get("activation_step") is None:
                continue
            key = (r14["hazard_cost"], r14["num_steps"], r14["run_idx"])
            if key not in v13_lookup:
                continue
            r13 = v13_lookup[key]
            v13_act = r13.get("activation_step")
            if v13_act in (None, "None", ""):
                continue
            h3_audited += 1
            for field in ["activation_step", "end_state_found_step", "hazard_entries_p3"]:
                v14_val = r14.get(field)
                v13_val = r13.get(field)
                v14_str = "" if v14_val is None else str(v14_val)
                v13_str = "" if v13_val in (None, "None") else str(v13_val)
                if v14_str != v13_str:
                    h3_diverge[field] += 1
        lines.append(f"    Both-activated runs audited: {h3_audited}")
        for field in ["activation_step", "end_state_found_step", "hazard_entries_p3"]:
            if h3_audited > 0:
                pct = 100 * h3_diverge[field] / h3_audited
                lines.append(f"    {field}: divergent in {h3_diverge[field]}/{h3_audited} "
                             f"({pct:.1f}%)")

    lines.append("")
    lines.append("=" * 72)
    lines.append("End of v0.14 meta-report")
    lines.append("=" * 72)

    report_str = "\n".join(lines)
    with open(report_path, "w") as f:
        f.write(report_str)
    print(f"\nMeta-report written to {report_path}")
    print()
    print(report_str)


def _parse_cell_dict(s):
    """Parse a 'cell:value|cell:value|...' string into a dict.
    Used for the per-cell threshold and timing fields in the CSV."""
    result = {}
    if not s:
        return result
    parts = s.split("|")
    for part in parts:
        # Split on the LAST colon to handle the (x, y):value format
        # where the cell coordinate itself contains a colon-free comma.
        if ":" not in part:
            continue
        last_colon = part.rfind(":")
        cell_str = part[:last_colon]
        value_str = part[last_colon + 1:]
        result[cell_str] = value_str
    return result


if __name__ == "__main__":
    main()
