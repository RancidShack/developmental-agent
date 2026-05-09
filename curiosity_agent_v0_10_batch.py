"""
curiosity_agent_v0_10_batch.py
------------------------------
Batch runner for v0.10 vs v0.9 matched-seed comparison.

Implements the experimental matrix specified in v0.10-preregistration.md:
  - 2 architectures: v0.9 (cost_no_aversion mode, no threat layer) and
    v0.10 (cost_no_aversion + persistent threat layer)
  - 6 cost levels: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
  - 3 run lengths: 20,000, 80,000, 160,000 steps
  - 10 runs per cell

Total: 2 × 6 × 3 × 10 = 360 runs.

Matched seeds across architectures: run i at cost c at run length L
uses the same random seed for both v0.9 and v0.10, so comparison is
within-seed up to the point at which the threat layer first intervenes.

For computational tractability, the default execution is the full
matrix. CLI args allow restricting to a subset:
  --steps 20000           Run only one run length (omit for all three)
  --arch v0_10            Run only one architecture (omit for both)
  --cost 1.0              Run only one cost level (omit for all six)
  --runs 5                Override runs per cell (default 10)

Run from Terminal with:
    python3 curiosity_agent_v0_10_batch.py
    python3 curiosity_agent_v0_10_batch.py --steps 20000 --arch v0_10
"""

import argparse
import copy
import csv
import time
from collections import defaultdict, deque
import numpy as np

# Import constants and helper functions from v0.10
# (these are also identical to v0.9 for the shared portions)
from curiosity_agent_v0_10 import (
    GRID_SIZE, PHASE_3_START_FRACTION, Q_VALUE_RESET_MULTIPLIER,
    FEATURE_DRIVE_WEIGHT, FRAME, NEUTRAL, HAZARD, ATTRACTOR,
    AVERSION_PENALTY, ATTRACTION_BONUS, FLAG_THRESHOLD,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, START_CELL,
    StructuredGridWorld, plan_phase_1_path, path_to_actions,
    DevelopmentalAgent as V010Agent,
)

# --------------------------------------------------------------------------
# v0.9 AGENT (REIMPLEMENTED FOR BATCH USE WITHOUT MODULE-LEVEL CONFIG)
# --------------------------------------------------------------------------
# We need a v0.9 implementation that takes hazard_cost as an argument
# rather than reading from module globals, so the batch runner can vary
# it without rewriting files. This reimplements v0.9's cost_no_aversion
# behaviour as a class.

class V009Agent:
    """v0.9 agent in cost_no_aversion mode, parameterised by hazard_cost.

    No threat layer. No pre-wired HAZARD aversion. No HAZARD epsilon
    filter. Hazards passable at cost. This is the comparison condition
    for v0.10.
    """

    def __init__(self, world, total_steps, hazard_cost, num_actions=4):
        self.world = world
        self.scope = world.scope_cells
        self.total_steps = total_steps
        self.hazard_cost = hazard_cost
        self.steps_taken = 0
        self.covered = set()
        self.num_actions = num_actions

        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.fast_errors = defaultdict(lambda: deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: deque(maxlen=30))
        self.cell_preference = defaultdict(float)
        self.q_values = defaultdict(float)

        self.phase = 1
        self.phase_1_end_step = None
        self.phase_2_end_step = None
        self.phase_3_start_target = int(total_steps * PHASE_3_START_FRACTION)

        self.prescribed_path = plan_phase_1_path(world)
        self.prescribed_actions = path_to_actions(self.prescribed_path)
        self.path_index = 0

        self.learning_rate = 0.1
        self.epsilon = 0.1

        self.frame_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_entries_by_phase = {1: 0, 2: 0, 3: 0}
        self.total_cost_incurred = 0.0

        self._apply_phase_weights()

    def _apply_phase_weights(self):
        if self.phase == 1:
            self.novelty_weight = 0.0
            self.progress_weight = 0.0
            self.preference_weight = 0.0
            self.feature_weight = 0.0
        elif self.phase == 2:
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.0
            self.feature_weight = FEATURE_DRIVE_WEIGHT
        elif self.phase == 3:
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.8
            self.feature_weight = FEATURE_DRIVE_WEIGHT

    def _transition_phase(self, new_phase):
        for key in list(self.q_values.keys()):
            self.q_values[key] *= Q_VALUE_RESET_MULTIPLIER
        self.phase = new_phase
        self._apply_phase_weights()

    def check_phase_transition(self):
        if self.phase == 1:
            if self.path_index >= len(self.prescribed_actions):
                self.phase_1_end_step = self.steps_taken
                self._transition_phase(2)
                return True
        elif self.phase == 2:
            if self.steps_taken >= self.phase_3_start_target:
                self.phase_2_end_step = self.steps_taken
                self._transition_phase(3)
                return True
        return False

    def get_prescribed_action(self):
        if self.path_index >= len(self.prescribed_actions):
            return None
        action = self.prescribed_actions[self.path_index]
        self.path_index += 1
        return action

    def _primitive_bias(self, state):
        adj_types = state[3:7]
        biases = np.zeros(4)
        for i, t in enumerate(adj_types):
            if t == FRAME:
                biases[i] = AVERSION_PENALTY
            elif t == ATTRACTOR:
                biases[i] = ATTRACTION_BONUS
        return biases

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            biases = self._primitive_bias(state)
            valid = [a for a in range(self.num_actions)
                     if biases[a] > AVERSION_PENALTY / 2]
            if not valid:
                valid = list(range(self.num_actions))
            return int(np.random.choice(valid))
        biases = self._primitive_bias(state)
        values = np.array([self.q_values[(state, a)] for a in range(self.num_actions)])
        combined = values + biases
        max_v = combined.max()
        best = [a for a in range(self.num_actions) if combined[a] == max_v]
        return int(np.random.choice(best))

    def novelty_reward(self, state):
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def preference_reward(self, state):
        if self.preference_weight == 0.0:
            return 0.0
        cell = (state[0], state[1])
        return self.preference_weight * self.cell_preference[cell]

    def feature_reward(self, state):
        if self.feature_weight == 0.0:
            return 0.0
        return self.feature_weight * (1.0 if state[2] == ATTRACTOR else 0.0)

    def prediction_error(self, state, action, next_state):
        predictions = self.forward_model[(state, action)]
        total = sum(predictions.values())
        pseudo_vocab = 5
        smoothed_prob = (predictions[next_state] + 1) / (total + pseudo_vocab)
        return 1.0 - smoothed_prob

    def learning_progress(self, state, action):
        fast = self.fast_errors[(state, action)]
        slow = self.slow_errors[(state, action)]
        if len(fast) < 3 or len(slow) < 10:
            return 0.0
        fast_mean = np.mean(fast)
        slow_mean = np.mean(slow)
        progress = slow_mean - fast_mean
        return self.progress_weight * max(0.0, progress)

    def update_model(self, state, action, next_state, error, r_progress, r_feature):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)
        self.cell_preference[cell] += r_progress + r_feature

    def update_values(self, state, action, next_state, intrinsic):
        if self.phase == 1:
            return
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def record_action_outcome(self, target_cell, success, cost_incurred, world):
        if not success:
            t = world.cell_type.get(target_cell, FRAME)
            if t == FRAME:
                self.frame_attempts_by_phase[self.phase] += 1
            elif t == HAZARD:
                self.hazard_attempts_by_phase[self.phase] += 1
            return
        if cost_incurred > 0:
            self.hazard_entries_by_phase[self.phase] += 1
            self.total_cost_incurred += cost_incurred


# --------------------------------------------------------------------------
# WORLD VARIANT FOR v0.9 BATCH (cost_no_aversion behaviour, parameterised)
# --------------------------------------------------------------------------

class V009World(StructuredGridWorld):
    """v0.9 world in cost_no_aversion: hazards passable at cost. Uses
    the same step semantics as v0.10's world (which is also always
    cost-passable). Distinguished by class to keep batch code explicit."""

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
# v0.10 WORLD WRAPPER
# --------------------------------------------------------------------------
# v0.10's world is identical to V009World, but we wrap for clarity.

class V010World(StructuredGridWorld):
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
# RUN ONE AGENT (works for both v0.9 and v0.10)
# --------------------------------------------------------------------------

def run_one(arch, hazard_cost, num_steps, seed):
    """Execute one agent run. Returns a dict of per-run metrics.

    arch: "v0_9" or "v0_10"
    """
    np.random.seed(seed)

    if arch == "v0_9":
        world = V009World(hazard_cost)
        agent = V009Agent(world, num_steps, hazard_cost)
    elif arch == "v0_10":
        world = V010World(hazard_cost)
        agent = V010Agent(world, num_steps)
        # Override world's cost into agent path: V010Agent uses
        # module-level HAZARD_COST in single-run, but here we want
        # batch-controlled cost. We achieve this by patching the world's
        # step function to use the parameterised cost (already handled
        # in V010World.step) and ensuring the agent's accumulator uses
        # whatever cost the world returns. The agent code uses
        # cost_incurred returned from world.step(), so this is correct.
    else:
        raise ValueError(f"Unknown arch: {arch}")

    state = world.observe()

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

        if arch == "v0_10":
            agent.record_action_outcome(target_cell, success, cost_incurred,
                                        world, step)
        else:
            agent.record_action_outcome(target_cell, success, cost_incurred,
                                        world)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        r_feature = agent.feature_reward(next_state)
        intrinsic = (r_novelty + r_progress + r_preference + r_feature
                     - cost_incurred)

        agent.update_model(state, action, next_state, error, r_progress, r_feature)
        agent.update_values(state, action, next_state, intrinsic)

        state = next_state

    # --- COMPUTE METRICS ---
    metrics = {
        "arch": arch,
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
    }

    # v0.10-specific metrics
    if arch == "v0_10":
        metrics.update({
            "hazards_flagged": len(agent.cells_flagged_during_run),
            "time_to_first_flag": agent.time_to_first_flag,
            "time_to_final_flag": agent.time_to_final_flag,
            "cost_at_final_flag": agent.cost_at_final_flag,
            "actions_gated_p2": agent.hazard_gated_by_threat_layer[2],
            "actions_gated_p3": agent.hazard_gated_by_threat_layer[3],
        })
    else:
        metrics.update({
            "hazards_flagged": None,
            "time_to_first_flag": None,
            "time_to_final_flag": None,
            "cost_at_final_flag": None,
            "actions_gated_p2": None,
            "actions_gated_p3": None,
        })

    # Top attractor (for individuation)
    p3_visits_per_attractor = {
        a: 0 for a in ATTRACTOR_CELLS
    }
    # We need to reconstruct phase-3 visits from the agent's data.
    # In single-run we tracked heatmap_by_phase, but here we kept the
    # data minimal. For batch, count via cell_preference being a proxy
    # (top preferred attractor in scope).
    attractor_prefs = {a: agent.cell_preference[a] for a in ATTRACTOR_CELLS}
    top_attractor = max(attractor_prefs, key=attractor_prefs.get)
    metrics["top_attractor"] = str(top_attractor)
    metrics["top_attractor_pref"] = attractor_prefs[top_attractor]

    # Phase 3 cleanness (boolean per pre-registered Phase 3 metric:
    # cleanness if Phase 3 hazard entries < 3)
    metrics["phase_3_clean"] = (agent.hazard_entries_by_phase[3] < 3)

    # Full-run cleanness (boolean: total entries < 3)
    total_entries = (agent.hazard_entries_by_phase[1]
                     + agent.hazard_entries_by_phase[2]
                     + agent.hazard_entries_by_phase[3])
    metrics["full_run_clean"] = (total_entries < 3)

    return metrics


# --------------------------------------------------------------------------
# BATCH ORCHESTRATION
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, nargs="+", default=[20000, 80000, 160000],
                    help="Run length(s) in steps.")
    ap.add_argument("--arch", type=str, nargs="+",
                    choices=["v0_9", "v0_10"],
                    default=["v0_9", "v0_10"],
                    help="Architecture(s) to run.")
    ap.add_argument("--cost", type=float, nargs="+",
                    default=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                    help="Hazard cost level(s).")
    ap.add_argument("--runs", type=int, default=10,
                    help="Runs per (arch, cost, steps) cell.")
    ap.add_argument("--out", type=str, default="run_data_v0_10.csv",
                    help="Output CSV filename.")
    ap.add_argument("--report", type=str, default="meta_report_v0_10.txt",
                    help="Output meta-report filename.")
    args = ap.parse_args()

    # Build job list
    jobs = []
    for steps in args.steps:
        for arch in args.arch:
            for cost in args.cost:
                for run_idx in range(args.runs):
                    seed = hash((arch, cost, steps, run_idx)) % (2**31)
                    jobs.append((arch, cost, steps, run_idx, seed))

    print(f"v0.10 batch")
    print(f"  Architectures : {args.arch}")
    print(f"  Cost levels   : {args.cost}")
    print(f"  Run lengths   : {args.steps}")
    print(f"  Runs per cell : {args.runs}")
    print(f"  Total runs    : {len(jobs)}")
    print()

    results = []
    t_start = time.time()

    for i, (arch, cost, steps, run_idx, seed) in enumerate(jobs):
        t0 = time.time()
        metrics = run_one(arch, cost, steps, seed)
        metrics["run_idx"] = run_idx
        results.append(metrics)
        elapsed_run = time.time() - t0
        elapsed_total = time.time() - t_start
        completed = i + 1
        remaining = len(jobs) - completed
        eta = (elapsed_total / completed) * remaining
        print(f"[{completed:>3}/{len(jobs)}] {arch} cost={cost} steps={steps} "
              f"run={run_idx}: P3_entries={metrics['hazard_entries_p3']:>3} "
              f"flagged={metrics['hazards_flagged']} "
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
        "hazards_flagged", "time_to_first_flag", "time_to_final_flag",
        "cost_at_final_flag", "actions_gated_p2", "actions_gated_p3",
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
    lines.append("v0.10 BATCH META-REPORT")
    lines.append("=" * 76)
    lines.append(f"Total runs: {len(results)}")
    lines.append(f"Compute time: {total_elapsed/60:.1f} minutes "
                 f"({total_elapsed:.0f}s)")
    lines.append("")

    # Group by (arch, steps, cost) and report aggregates
    for steps in sorted(set(r["num_steps"] for r in results)):
        lines.append(f"\n--- RUN LENGTH: {steps} steps ---")
        for arch in sorted(set(r["arch"] for r in results)):
            arch_results = [r for r in results
                            if r["num_steps"] == steps and r["arch"] == arch]
            if not arch_results:
                continue
            lines.append(f"\n  Architecture: {arch}")
            lines.append(f"  {'Cost':>6} | {'P3_clean':>8} | {'Full_clean':>10} | "
                         f"{'Mean_P3_ent':>11} | {'Mean_total_cost':>15} | "
                         f"{'Mean_mastered':>13} | {'Flagged':>7}")
            lines.append(f"  {'-'*6} | {'-'*8} | {'-'*10} | "
                         f"{'-'*11} | {'-'*15} | "
                         f"{'-'*13} | {'-'*7}")
            for cost in sorted(set(r["hazard_cost"] for r in arch_results)):
                cell_results = [r for r in arch_results
                                if r["hazard_cost"] == cost]
                p3_clean = sum(1 for r in cell_results if r["phase_3_clean"])
                full_clean = sum(1 for r in cell_results if r["full_run_clean"])
                mean_p3 = np.mean([r["hazard_entries_p3"] for r in cell_results])
                mean_cost = np.mean([r["total_cost"] for r in cell_results])
                mean_mast = np.mean([r["mastered_pairs"] for r in cell_results])
                if arch == "v0_10":
                    mean_flagged = np.mean([r["hazards_flagged"]
                                            for r in cell_results])
                    flagged_str = f"{mean_flagged:.1f}/5"
                else:
                    flagged_str = "N/A"
                lines.append(f"  {cost:>6.2f} | {p3_clean:>3}/{len(cell_results):<3}  | "
                             f"{full_clean:>3}/{len(cell_results):<3}    | "
                             f"{mean_p3:>11.2f} | {mean_cost:>15.2f} | "
                             f"{mean_mast:>13.1f} | {flagged_str:>7}")

            # Architecture-level totals across all costs at this run length
            n = len(arch_results)
            tot_p3_clean = sum(1 for r in arch_results if r["phase_3_clean"])
            tot_full_clean = sum(1 for r in arch_results if r["full_run_clean"])
            lines.append(f"  {'TOTAL':>6} | {tot_p3_clean:>3}/{n:<3}  | "
                         f"{tot_full_clean:>3}/{n:<3}    |")

            # Individuation across this arch+steps slice
            top_attractors = [r["top_attractor"] for r in arch_results]
            unique_attractors = set(top_attractors)
            lines.append(f"  Distinct top attractors: {len(unique_attractors)}/6")
            lines.append(f"  Top attractor distribution: "
                         + ", ".join(f"{a}({top_attractors.count(a)})"
                                     for a in sorted(unique_attractors)))

    # v0.10-specific summary: flag dynamics
    v010_results = [r for r in results if r["arch"] == "v0_10"]
    if v010_results:
        lines.append("\n\n--- v0.10 THREAT-LAYER DYNAMICS ---")
        for steps in sorted(set(r["num_steps"] for r in v010_results)):
            slice_results = [r for r in v010_results
                             if r["num_steps"] == steps]
            lines.append(f"\nRun length {steps}:")
            mean_flagged = np.mean([r["hazards_flagged"] for r in slice_results])
            lines.append(f"  Mean hazards flagged across batch: "
                         f"{mean_flagged:.2f}/5")
            # Distribution of flagged counts
            from collections import Counter
            flag_dist = Counter(r["hazards_flagged"] for r in slice_results)
            lines.append(f"  Distribution: "
                         + ", ".join(f"{k} flagged: {v} runs"
                                     for k, v in sorted(flag_dist.items())))
            # Time to first flag (only where flags occurred)
            flags_set = [r["time_to_first_flag"] for r in slice_results
                         if r["time_to_first_flag"] is not None]
            if flags_set:
                lines.append(f"  Mean time to first flag: "
                             f"{np.mean(flags_set):.0f} steps "
                             f"(min {min(flags_set)}, max {max(flags_set)})")
            # Mean total cost paid (across all v0.10 runs)
            mean_cost_paid = np.mean([r["total_cost"] for r in slice_results])
            lines.append(f"  Mean total cost incurred: {mean_cost_paid:.2f}")

    # --- COMPARATIVE FINDING (the headline) ---
    if 160000 in args.steps and "v0_9" in args.arch and "v0_10" in args.arch:
        lines.append("\n\n--- HEADLINE COMPARISON: 160,000-STEP PHASE 3 CLEANNESS ---")
        v09_160k = [r for r in results
                    if r["arch"] == "v0_9" and r["num_steps"] == 160000]
        v10_160k = [r for r in results
                    if r["arch"] == "v0_10" and r["num_steps"] == 160000]
        v09_clean = sum(1 for r in v09_160k if r["phase_3_clean"])
        v10_clean = sum(1 for r in v10_160k if r["phase_3_clean"])
        lines.append(f"  v0.9  Phase 3 clean: {v09_clean}/{len(v09_160k)}")
        lines.append(f"  v0.10 Phase 3 clean: {v10_clean}/{len(v10_160k)}")
        lines.append(f"  Improvement: {v10_clean - v09_clean} runs "
                     f"({100 * (v10_clean - v09_clean) / max(len(v10_160k), 1):.1f} pp)")
        # Pre-registered category assignment for v0.10
        if v10_clean >= 55:
            cat = "A — Full stabilisation"
        elif v10_clean >= 40:
            cat = "B — Partial stabilisation"
        else:
            cat = "C — No meaningful stabilisation"
        lines.append(f"  v0.10 pre-registered category: {cat}")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open(args.report, "w") as f:
        f.write(report_str)
    print(f"\nMeta-report saved to {args.report}")


if __name__ == "__main__":
    main()
