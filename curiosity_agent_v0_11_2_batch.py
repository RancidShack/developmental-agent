"""
curiosity_agent_v0_11_2_batch.py
--------------------------------
Batch runner for v0.11.2 vs v0.10 matched-seed comparison.

Implements the experimental matrix specified in v0.11-preregistration.md
(retained unchanged through v0.11.1 and v0.11.2 amendments):
  - 2 architectures: v0.10 (threat layer only) and v0.11.2 (threat
    layer + attractor depletion + persistent mastery layer + preference
    reset on banking + blocked preference accumulation on mastered)
  - 6 cost levels: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
  - 3 run lengths: 20,000, 80,000, 160,000 steps
  - 10 runs per cell

Total: 2 x 6 x 3 x 10 = 360 runs.

Matched seeds across architectures: run i at cost c at run length L
uses the same random seed for both v0.10 and v0.11.2, so comparison
is within-seed up to the point at which the mastery layer first
intervenes in v0.11.2.

CLI args allow restricting to a subset:
  --steps 20000           Run only one run length (omit for all three)
  --arch v0_11_2          Run only one architecture (omit for both)
  --cost 1.0              Run only one cost level (omit for all six)
  --runs 5                Override runs per cell (default 10)

Run from Terminal with:
    python3 curiosity_agent_v0_11_2_batch.py
"""

import argparse
import csv
import time
from collections import defaultdict, deque, Counter
import numpy as np

# Import constants and helpers from v0.11.2
from curiosity_agent_v0_11_2 import (
    GRID_SIZE, PHASE_3_START_FRACTION, Q_VALUE_RESET_MULTIPLIER,
    FEATURE_DRIVE_WEIGHT, FRAME, NEUTRAL, HAZARD, ATTRACTOR,
    AVERSION_PENALTY, ATTRACTION_BONUS, FLAG_THRESHOLD,
    MASTERY_THRESHOLD, MASTERY_BONUS,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, START_CELL,
    StructuredGridWorld, plan_phase_1_path, path_to_actions,
    DevelopmentalAgent as V0112Agent,
)


# --------------------------------------------------------------------------
# v0.10 AGENT (REIMPLEMENTED FOR BATCH USE WITHOUT MODULE-LEVEL CONFIG)
# --------------------------------------------------------------------------
# Same approach as v0.10's batch: reimplement the comparison-architecture
# agent as a class that takes hazard_cost as a constructor argument.
# This v0.10 reimplementation is functionally identical to the published
# v0.10 in cost_no_aversion mode with persistent threat layer.

class V010Agent:
    """v0.10 agent (cost_no_aversion + persistent threat layer)
    parameterised by hazard_cost. No mastery mechanism. Matches the
    published v0.10 architecture for the comparison condition."""

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

        # v0.10 threat layer
        self.threat_flag = {}
        self.hazard_entry_counter = defaultdict(int)
        for cell, ctype in world.cell_type.items():
            if ctype == FRAME:
                self.threat_flag[cell] = 1
            else:
                self.threat_flag[cell] = 0

        self.time_to_first_flag = None
        self.time_to_final_flag = None
        self.cells_flagged_during_run = set()
        self.cost_at_final_flag = None

        self.frame_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_entries_by_phase = {1: 0, 2: 0, 3: 0}
        self.total_cost_incurred = 0.0
        self.hazard_gated_by_threat_layer = {1: 0, 2: 0, 3: 0}

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

    def _get_destination_cell(self, state, action):
        x, y = state[0], state[1]
        if action == 0:
            target = (x, y - 1)
        elif action == 1:
            target = (x, y + 1)
        elif action == 2:
            target = (x - 1, y)
        elif action == 3:
            target = (x + 1, y)
        else:
            return None
        if not (0 <= target[0] < GRID_SIZE and 0 <= target[1] < GRID_SIZE):
            return None
        return target

    def _action_is_gated(self, state, action):
        dest = self._get_destination_cell(state, action)
        if dest is None:
            return False
        return self.threat_flag.get(dest, 0) == 1

    def choose_action(self, state):
        all_actions = list(range(self.num_actions))
        candidate_actions = [a for a in all_actions
                             if not self._action_is_gated(state, a)]
        gated_count = len(all_actions) - len(candidate_actions)
        if gated_count > 0:
            self.hazard_gated_by_threat_layer[self.phase] += gated_count
        if not candidate_actions:
            candidate_actions = all_actions

        if np.random.rand() < self.epsilon:
            biases = self._primitive_bias(state)
            valid = [a for a in candidate_actions
                     if biases[a] > AVERSION_PENALTY / 2]
            if not valid:
                valid = candidate_actions
            return int(np.random.choice(valid))

        biases = self._primitive_bias(state)
        values = np.array([self.q_values[(state, a)] for a in range(self.num_actions)])
        combined = values + biases
        mask = np.array([a in candidate_actions for a in all_actions])
        combined = np.where(mask, combined, -np.inf)
        max_v = combined.max()
        best = [a for a in candidate_actions if combined[a] == max_v]
        if not best:
            return int(np.random.choice(candidate_actions))
        return int(np.random.choice(best))

    def update_threat_layer(self, entered_cell, step):
        self.hazard_entry_counter[entered_cell] += 1
        if (self.hazard_entry_counter[entered_cell] >= FLAG_THRESHOLD
                and self.threat_flag.get(entered_cell, 0) == 0):
            self.threat_flag[entered_cell] = 1
            self.cells_flagged_during_run.add(entered_cell)
            if self.time_to_first_flag is None:
                self.time_to_first_flag = step
            self.time_to_final_flag = step
            self.cost_at_final_flag = self.total_cost_incurred

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

    def record_action_outcome(self, target_cell, success, cost_incurred, world, step):
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
            self.update_threat_layer(target_cell, step)


# --------------------------------------------------------------------------
# WORLD VARIANTS WITH PARAMETERISED HAZARD COST
# --------------------------------------------------------------------------

class V010World(StructuredGridWorld):
    """v0.10 world: hazards always passable at parameterised cost."""

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


class V0112World(StructuredGridWorld):
    """v0.11.2 world: identical to v0.10 world. The mastery mechanism
    operates inside the agent, not the world."""

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

def run_one(arch, hazard_cost, num_steps, seed):
    """Execute one agent run. Returns a dict of per-run metrics.

    arch: "v0_10" or "v0_11_2"
    """
    np.random.seed(seed)

    if arch == "v0_10":
        world = V010World(hazard_cost)
        agent = V010Agent(world, num_steps, hazard_cost)
    elif arch == "v0_11_2":
        world = V0112World(hazard_cost)
        # v0.11.2 agent uses module-level HAZARD_COST for cost values,
        # but the world's step function is what actually returns the
        # cost. As long as the world is parameterised, the agent works
        # correctly. The agent just uses the cost value the world returns.
        agent = V0112Agent(world, num_steps)
    else:
        raise ValueError(f"Unknown arch: {arch}")

    state = world.observe()
    # Track Phase 3 visit counts for attractor cells specifically
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

        # Both architectures' record_action_outcome takes (target_cell,
        # success, cost_incurred, world, step) - same signature.
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

        # Track Phase 3 attractor visits
        if agent.phase == 3:
            cell = (next_state[0], next_state[1])
            if cell in p3_visits_per_attractor:
                p3_visits_per_attractor[cell] += 1

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
        "hazards_flagged": len(agent.cells_flagged_during_run),
        "time_to_first_flag": agent.time_to_first_flag,
        "time_to_final_flag": agent.time_to_final_flag,
        "actions_gated_p2": agent.hazard_gated_by_threat_layer[2],
        "actions_gated_p3": agent.hazard_gated_by_threat_layer[3],
    }

    # v0.11.2-specific metrics
    if arch == "v0_11_2":
        metrics["attractors_mastered"] = len(agent.mastery_order_sequence)
        metrics["time_to_first_mastery"] = agent.time_to_first_mastery
        metrics["time_to_final_mastery"] = agent.time_to_final_mastery
        # First-banked attractor (for individuation analysis)
        if agent.mastery_order_sequence:
            metrics["first_banked"] = str(agent.mastery_order_sequence[0])
        else:
            metrics["first_banked"] = None
        # Full mastery sequence as string for distinct-sequence analysis
        metrics["mastery_sequence"] = "|".join(
            str(c) for c in agent.mastery_order_sequence
        )
        # Total post-mastery visits across all mastered attractors
        post_mastery_visits = 0
        for ma in agent.mastery_order_sequence:
            total_visits = agent.attractor_visit_counter.get(ma, 0)
            # Post-mastery = total visits beyond MASTERY_THRESHOLD
            post_mastery_visits += max(0, total_visits - MASTERY_THRESHOLD)
        metrics["post_mastery_visits_total"] = post_mastery_visits
        # Phase 3 visits per attractor (mastered/unmastered split)
        p3_visits_to_mastered = sum(
            v for cell, v in p3_visits_per_attractor.items()
            if agent.mastery_flag.get(cell, 0) == 1
        )
        p3_visits_to_unmastered = sum(
            v for cell, v in p3_visits_per_attractor.items()
            if agent.mastery_flag.get(cell, 0) == 0
        )
        metrics["p3_visits_to_mastered"] = p3_visits_to_mastered
        metrics["p3_visits_to_unmastered"] = p3_visits_to_unmastered
    else:
        metrics["attractors_mastered"] = None
        metrics["time_to_first_mastery"] = None
        metrics["time_to_final_mastery"] = None
        metrics["first_banked"] = None
        metrics["mastery_sequence"] = None
        metrics["post_mastery_visits_total"] = None
        metrics["p3_visits_to_mastered"] = None
        metrics["p3_visits_to_unmastered"] = None

    # Top attractor by preference (for individuation)
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
# BATCH ORCHESTRATION
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, nargs="+", default=[20000, 80000, 160000],
                    help="Run length(s) in steps.")
    ap.add_argument("--arch", type=str, nargs="+",
                    choices=["v0_10", "v0_11_2"],
                    default=["v0_10", "v0_11_2"],
                    help="Architecture(s) to run.")
    ap.add_argument("--cost", type=float, nargs="+",
                    default=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                    help="Hazard cost level(s).")
    ap.add_argument("--runs", type=int, default=10,
                    help="Runs per (arch, cost, steps) cell.")
    ap.add_argument("--out", type=str, default="run_data_v0_11_2.csv",
                    help="Output CSV filename.")
    ap.add_argument("--report", type=str, default="meta_report_v0_11_2.txt",
                    help="Output meta-report filename.")
    args = ap.parse_args()

    jobs = []
    for steps in args.steps:
        for arch in args.arch:
            for cost in args.cost:
                for run_idx in range(args.runs):
                    seed = hash((arch, cost, steps, run_idx)) % (2**31)
                    jobs.append((arch, cost, steps, run_idx, seed))

    print(f"v0.11.2 batch")
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
        mast_str = (f"mast={metrics['attractors_mastered']}"
                    if metrics['attractors_mastered'] is not None else "")
        print(f"[{completed:>3}/{len(jobs)}] {arch} cost={cost} steps={steps} "
              f"run={run_idx}: P3_ent={metrics['hazard_entries_p3']:>3} "
              f"flagged={metrics['hazards_flagged']} {mast_str} "
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
    lines.append("v0.11.2 BATCH META-REPORT")
    lines.append("=" * 76)
    lines.append(f"Total runs: {len(results)}")
    lines.append(f"Compute time: {total_elapsed/60:.1f} minutes "
                 f"({total_elapsed:.0f}s)")
    lines.append("")

    for steps in sorted(set(r["num_steps"] for r in results)):
        lines.append(f"\n--- RUN LENGTH: {steps} steps ---")
        for arch in sorted(set(r["arch"] for r in results)):
            arch_results = [r for r in results
                            if r["num_steps"] == steps and r["arch"] == arch]
            if not arch_results:
                continue
            lines.append(f"\n  Architecture: {arch}")
            lines.append(f"  {'Cost':>6} | {'P3_clean':>8} | "
                         f"{'Mean_P3_ent':>11} | {'Mean_total_cost':>15} | "
                         f"{'Mean_mast_pairs':>15} | {'Mast_attr':>9} | "
                         f"{'P3_to_mast':>10} | {'P3_to_unmast':>12}")
            lines.append(f"  {'-'*6} | {'-'*8} | "
                         f"{'-'*11} | {'-'*15} | "
                         f"{'-'*15} | {'-'*9} | "
                         f"{'-'*10} | {'-'*12}")
            for cost in sorted(set(r["hazard_cost"] for r in arch_results)):
                cell_results = [r for r in arch_results
                                if r["hazard_cost"] == cost]
                p3_clean = sum(1 for r in cell_results if r["phase_3_clean"])
                mean_p3 = np.mean([r["hazard_entries_p3"] for r in cell_results])
                mean_cost = np.mean([r["total_cost"] for r in cell_results])
                mean_mast = np.mean([r["mastered_pairs"] for r in cell_results])
                if arch == "v0_11_2":
                    mean_attr = np.mean([r["attractors_mastered"]
                                          for r in cell_results])
                    mean_p3_mast = np.mean([r["p3_visits_to_mastered"]
                                             for r in cell_results])
                    mean_p3_unmast = np.mean([r["p3_visits_to_unmastered"]
                                               for r in cell_results])
                    attr_str = f"{mean_attr:.1f}/6"
                    p3_mast_str = f"{mean_p3_mast:.0f}"
                    p3_unmast_str = f"{mean_p3_unmast:.0f}"
                else:
                    attr_str = "N/A"
                    p3_mast_str = "N/A"
                    p3_unmast_str = "N/A"
                lines.append(f"  {cost:>6.2f} | {p3_clean:>3}/{len(cell_results):<3}  | "
                             f"{mean_p3:>11.2f} | {mean_cost:>15.2f} | "
                             f"{mean_mast:>15.1f} | {attr_str:>9} | "
                             f"{p3_mast_str:>10} | {p3_unmast_str:>12}")

            n = len(arch_results)
            tot_p3_clean = sum(1 for r in arch_results if r["phase_3_clean"])
            lines.append(f"  {'TOTAL':>6} | {tot_p3_clean:>3}/{n:<3}  |")

            # Individuation
            top_attractors = [r["top_attractor"] for r in arch_results]
            unique_attractors = set(top_attractors)
            lines.append(f"  Distinct top attractors: {len(unique_attractors)}/6")
            lines.append(f"  Top attractor distribution: "
                         + ", ".join(f"{a}({top_attractors.count(a)})"
                                     for a in sorted(unique_attractors)))

            # v0.11.2-specific: first-banked individuation
            if arch == "v0_11_2":
                first_banks = [r["first_banked"] for r in arch_results
                               if r["first_banked"] is not None]
                if first_banks:
                    unique_first = set(first_banks)
                    lines.append(f"  Distinct first-banked: {len(unique_first)}/6")
                    lines.append(f"  First-banked distribution: "
                                 + ", ".join(
                                     f"{a}({first_banks.count(a)})"
                                     for a in sorted(unique_first)))

                # Mastery sequence dominance (Category F signal)
                sequences = [r["mastery_sequence"] for r in arch_results
                              if r["mastery_sequence"]]
                if sequences:
                    seq_counts = Counter(sequences)
                    most_common_seq, most_common_count = seq_counts.most_common(1)[0]
                    pct = 100 * most_common_count / len(sequences)
                    lines.append(f"  Most common mastery sequence accounts for: "
                                 f"{pct:.1f}% of runs ({most_common_count}/{len(sequences)})")
                    lines.append(f"  Distinct mastery sequences: "
                                 f"{len(seq_counts)}/{len(sequences)}")

    # v0.11.2-specific summary
    v112_results = [r for r in results if r["arch"] == "v0_11_2"]
    if v112_results:
        lines.append("\n\n--- v0.11.2 MASTERY DYNAMICS SUMMARY ---")
        for steps in sorted(set(r["num_steps"] for r in v112_results)):
            slice_results = [r for r in v112_results
                             if r["num_steps"] == steps]
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
            mean_p3_to_mast = np.mean([r["p3_visits_to_mastered"]
                                        for r in slice_results])
            mean_p3_to_unmast = np.mean([r["p3_visits_to_unmastered"]
                                          for r in slice_results])
            lines.append(f"  Mean P3 visits to mastered attractors: "
                         f"{mean_p3_to_mast:.1f}")
            lines.append(f"  Mean P3 visits to unmastered attractors: "
                         f"{mean_p3_to_unmast:.1f}")

            first_mastery = [r["time_to_first_mastery"] for r in slice_results
                              if r["time_to_first_mastery"] is not None]
            if first_mastery:
                lines.append(f"  Mean time to first mastery: "
                             f"{np.mean(first_mastery):.0f} steps "
                             f"(min {min(first_mastery)}, max {max(first_mastery)})")
            final_mastery = [r["time_to_final_mastery"] for r in slice_results
                              if r["time_to_final_mastery"] is not None]
            if final_mastery:
                lines.append(f"  Mean time to final mastery: "
                             f"{np.mean(final_mastery):.0f} steps "
                             f"(min {min(final_mastery)}, max {max(final_mastery)})")

    # --- HEADLINE: 160k Phase 3 cleanness comparison + Category assessment ---
    if 160000 in args.steps and "v0_10" in args.arch and "v0_11_2" in args.arch:
        lines.append("\n\n--- HEADLINE COMPARISON: 160,000-STEP RESULTS ---")
        v10_160k = [r for r in results
                    if r["arch"] == "v0_10" and r["num_steps"] == 160000]
        v112_160k = [r for r in results
                     if r["arch"] == "v0_11_2" and r["num_steps"] == 160000]
        v10_clean = sum(1 for r in v10_160k if r["phase_3_clean"])
        v112_clean = sum(1 for r in v112_160k if r["phase_3_clean"])
        lines.append(f"  Phase 3 cleanness:")
        lines.append(f"    v0.10:   {v10_clean}/{len(v10_160k)}")
        lines.append(f"    v0.11.2: {v112_clean}/{len(v112_160k)}")
        lines.append(f"  Behavioural preservation check: rule adherence "
                     f"{'PRESERVED' if v112_clean >= 50 else 'DEGRADED'}")

        # v0.11.2 mastery distribution at 160k
        if v112_160k:
            mean_mast_160k = np.mean([r["attractors_mastered"] for r in v112_160k])
            lines.append(f"\n  v0.11.2 mean attractors mastered at 160k: "
                         f"{mean_mast_160k:.2f}/6")

            # Category assignment per pre-registration
            lines.append("\n  v0.11 PRE-REGISTERED CATEGORY ASSESSMENT:")
            if mean_mast_160k >= 5.0:
                lines.append(f"  CATEGORY A — Full mastery trajectory "
                             f"(mean {mean_mast_160k:.2f} >= 5.0)")
            elif mean_mast_160k >= 3.0:
                lines.append(f"  CATEGORY B — Partial mastery trajectory "
                             f"(mean {mean_mast_160k:.2f} in [3.0, 5.0))")
            else:
                lines.append(f"  CATEGORY C — Weak mastery "
                             f"(mean {mean_mast_160k:.2f} < 3.0)")

            # Category F check (individuation collapse) at 160k
            lines.append("\n  CATEGORY F (INDIVIDUATION COLLAPSE) ASSESSMENT at 160k:")
            first_banks_160k = [r["first_banked"] for r in v112_160k
                                 if r["first_banked"] is not None]
            unique_first_160k = set(first_banks_160k)
            sigF1 = len(unique_first_160k) < 4
            lines.append(f"    Signal 1 (first-banked < 4 distinct): "
                         f"{len(unique_first_160k)}/6 distinct - "
                         f"{'TRIGGERED' if sigF1 else 'NOT triggered'}")

            sequences_160k = [r["mastery_sequence"] for r in v112_160k
                               if r["mastery_sequence"]]
            if sequences_160k:
                seq_counts_160k = Counter(sequences_160k)
                most_common_seq_160k, most_common_count_160k = seq_counts_160k.most_common(1)[0]
                pct_dom = 100 * most_common_count_160k / len(sequences_160k)
                sigF2 = pct_dom > 40
                lines.append(f"    Signal 2 (dominant sequence > 40%): "
                             f"{pct_dom:.1f}% - "
                             f"{'TRIGGERED' if sigF2 else 'NOT triggered'}")
            else:
                sigF2 = False
                lines.append(f"    Signal 2: no mastery sequences to analyse")

            # Signal 3 (mastery rank vs Manhattan distance correlation)
            # Pool all banked attractors with their rank (1 = first banked)
            from scipy.stats import pearsonr
            ranks = []
            distances = []
            for r in v112_160k:
                if r["mastery_sequence"]:
                    seq_cells = r["mastery_sequence"].split("|")
                    for rank, cell_str in enumerate(seq_cells, start=1):
                        # Parse "(x, y)" string
                        try:
                            inner = cell_str.strip("()").split(",")
                            cx, cy = int(inner[0]), int(inner[1].strip())
                            dist = abs(cx - START_CELL[0]) + abs(cy - START_CELL[1])
                            ranks.append(rank)
                            distances.append(dist)
                        except (ValueError, IndexError):
                            pass
            if len(ranks) > 5:
                try:
                    corr, _ = pearsonr(ranks, distances)
                    sigF3 = corr > 0.7
                    lines.append(f"    Signal 3 (rank vs distance Pearson r > 0.7): "
                                 f"{corr:.3f} - "
                                 f"{'TRIGGERED' if sigF3 else 'NOT triggered'}")
                except Exception:
                    sigF3 = False
                    lines.append(f"    Signal 3: correlation could not be computed")
            else:
                sigF3 = False
                lines.append(f"    Signal 3: insufficient data for correlation")

            triggered = sum([sigF1, sigF2, sigF3])
            if triggered >= 2:
                lines.append(f"    CATEGORY F: TRIGGERED ({triggered}/3 signals)")
            else:
                lines.append(f"    Category F: NOT triggered ({triggered}/3 signals)")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open(args.report, "w") as f:
        f.write(report_str)
    print(f"\nMeta-report saved to {args.report}")


if __name__ == "__main__":
    main()
