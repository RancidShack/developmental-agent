"""
curiosity_agent_v0_5_2_sweep.py
-------------------------------
Calibration sweep over the ambient coverage weight in v0.5.2.

Purpose: after v0.5.2 overshot (coverage drive at 93% of total), we need
to find the right ambient weight empirically rather than by guess. This
sweep runs the agent multiple times at each of several ambient weights
and reports the drive breakdown and coverage completion for each.

Sweep values: 0.002, 0.005, 0.010, 0.020
Runs per value: 3 (to average out stochastic variation without costing much time)

Everything else is held constant:
  - discovery_weight = 6.0 (unchanged from v0.5.2)
  - novelty_weight   = 0.25
  - progress_weight  = 1.2

Run from Terminal with:
    python3 curiosity_agent_v0_5_2_sweep.py

Output: a comparison table printed to Terminal and saved to
calibration_sweep_v0_5_2.txt
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
from collections import defaultdict, deque, Counter
import time

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

SWEEP_WEIGHTS = [0.002, 0.005, 0.010, 0.020]
RUNS_PER_WEIGHT = 3
NUM_STEPS = 10000
GRID_SIZE = 10
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]

# --------------------------------------------------------------------------
# WORLD AND AGENT (v0.5.2 architecture)
# --------------------------------------------------------------------------

class GridWorld:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.agent_pos = (0, 0)
        self.features = set(FEATURE_CELLS)
        self.scope_cells = {(x, y) for x in range(size) for y in range(size)}

    def observe(self):
        x, y = self.agent_pos
        is_feature = 1 if self.agent_pos in self.features else 0
        return (x, y, is_feature)

    def step(self, action):
        x, y = self.agent_pos
        if action == 0 and y > 0: y -= 1
        elif action == 1 and y < self.size - 1: y += 1
        elif action == 2 and x > 0: x -= 1
        elif action == 3 and x < self.size - 1: x += 1
        self.agent_pos = (x, y)
        return self.observe()


class DevelopmentalAgent:
    def __init__(self, scope_cells, total_steps, ambient_weight, num_actions=4):
        self.scope = set(scope_cells)
        self.total_steps = total_steps
        self.steps_taken = 0
        self.covered = set()
        self.num_actions = num_actions
        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.q_values = defaultdict(float)
        self.fast_errors = defaultdict(lambda: deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: deque(maxlen=30))
        self.learning_rate = 0.1
        self.novelty_weight = 0.25
        self.progress_weight = 1.2
        self.discovery_weight = 6.0
        self.ambient_weight_per_cell = ambient_weight  # the variable
        self.epsilon = 0.1

    def time_fraction_remaining(self):
        return max(0.0, 1.0 - (self.steps_taken / self.total_steps))

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.num_actions)
        values = [self.q_values[(state, a)] for a in range(self.num_actions)]
        max_v = max(values)
        best = [a for a, v in enumerate(values) if v == max_v]
        return np.random.choice(best)

    def novelty_reward(self, state):
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def coverage_reward(self, state):
        cell = (state[0], state[1])
        discovery = self.discovery_weight if (cell in self.scope and cell not in self.covered) else 0.0
        uncovered_count = len(self.scope) - len(self.covered)
        ambient = self.ambient_weight_per_cell * uncovered_count
        return discovery + ambient

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
        time_gone = 1.0 - self.time_fraction_remaining()
        temporal_mult = 1.0 + 0.5 * time_gone
        return self.progress_weight * max(0.0, progress) * temporal_mult

    def update_model(self, state, action, next_state, error):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)

    def update_values(self, state, action, next_state, intrinsic):
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error


# --------------------------------------------------------------------------
# SINGLE RUN — returns key metrics
# --------------------------------------------------------------------------

def single_run(ambient_weight):
    np.random.seed(None)
    world = GridWorld()
    agent = DevelopmentalAgent(world.scope_cells, NUM_STEPS, ambient_weight)
    state = world.observe()
    coverage_complete_step = None
    drive_dominance_counts = Counter()

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        action = agent.choose_action(state)
        next_state = world.step(action)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_coverage = agent.coverage_reward(next_state)
        intrinsic = r_novelty + r_progress + r_coverage

        # record dominant drive for this step
        drives = {"novelty": r_novelty, "progress": r_progress, "coverage": r_coverage}
        dominant = max(drives, key=drives.get) if max(drives.values()) > 0 else "none"
        drive_dominance_counts[dominant] += 1

        agent.update_model(state, action, next_state, error)
        agent.update_values(state, action, next_state, intrinsic)

        if coverage_complete_step is None and len(agent.covered) == len(agent.scope):
            coverage_complete_step = step
        state = next_state

    total = sum(drive_dominance_counts.values())
    drive_shares = {k: v / total for k, v in drive_dominance_counts.items()}
    # ensure all three keys are present
    for k in ["novelty", "progress", "coverage"]:
        drive_shares.setdefault(k, 0.0)

    mastered = sum(
        1 for errs in agent.fast_errors.values()
        if len(errs) >= 5 and np.mean(errs) < 0.15
    )

    return {
        "ambient_weight": ambient_weight,
        "cells_covered": len(agent.covered),
        "coverage_complete_step": coverage_complete_step,
        "drive_shares": drive_shares,
        "mastered_count": mastered,
    }


# --------------------------------------------------------------------------
# SWEEP
# --------------------------------------------------------------------------

def main():
    print(f"Calibration sweep over ambient coverage weight.")
    print(f"Weights tested: {SWEEP_WEIGHTS}")
    print(f"Runs per weight: {RUNS_PER_WEIGHT}")
    print(f"Each run = {NUM_STEPS} steps")
    print()

    all_results = {w: [] for w in SWEEP_WEIGHTS}
    start = time.time()

    for weight in SWEEP_WEIGHTS:
        for r in range(RUNS_PER_WEIGHT):
            result = single_run(weight)
            all_results[weight].append(result)
            completed = "YES" if result["coverage_complete_step"] is not None else "NO "
            print(f"  weight {weight:5.3f} run {r+1}/{RUNS_PER_WEIGHT}: "
                  f"covered {result['cells_covered']:3d}/100  "
                  f"complete {completed}  "
                  f"drive shares cov/nov/prog = "
                  f"{100*result['drive_shares']['coverage']:4.1f}% / "
                  f"{100*result['drive_shares']['novelty']:4.1f}% / "
                  f"{100*result['drive_shares']['progress']:4.1f}%  "
                  f"mastered {result['mastered_count']:3d}")

    total_time = time.time() - start
    print(f"\nSweep complete in {total_time:.1f} seconds.")

    # Aggregate and report
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("CALIBRATION SWEEP RESULTS (v0.5.2 ambient coverage weight)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'weight':>7} | {'cov %':>6} | {'complete':>8} | "
                 f"{'cov drv%':>8} | {'nov drv%':>8} | {'prog drv%':>9} | {'mastery':>7}")
    lines.append("-" * 80)

    for weight in SWEEP_WEIGHTS:
        results = all_results[weight]
        mean_coverage = np.mean([r["cells_covered"] for r in results])
        completed_frac = sum(1 for r in results if r["coverage_complete_step"] is not None) / len(results)
        mean_cov_drv = np.mean([r["drive_shares"]["coverage"] for r in results])
        mean_nov_drv = np.mean([r["drive_shares"]["novelty"] for r in results])
        mean_prog_drv = np.mean([r["drive_shares"]["progress"] for r in results])
        mean_mastered = np.mean([r["mastered_count"] for r in results])

        lines.append(
            f"{weight:>7.3f} | "
            f"{mean_coverage:>5.1f}  | "
            f"{completed_frac:>7.0%}  | "
            f"{100*mean_cov_drv:>7.1f}  | "
            f"{100*mean_nov_drv:>7.1f}  | "
            f"{100*mean_prog_drv:>8.1f}  | "
            f"{mean_mastered:>6.1f}"
        )

    lines.append("")
    lines.append("INTERPRETATION GUIDE:")
    lines.append("  The goal is ~33/33/33 across the three drives, with coverage")
    lines.append("  reliably completing. Watch for the lightest weight that")
    lines.append("  still produces high coverage completion.")
    lines.append("")

    report = "\n".join(lines)
    print(report)
    with open("calibration_sweep_v0_5_2.txt", "w") as f:
        f.write(report)
    print(f"\nResults saved to calibration_sweep_v0_5_2.txt")


if __name__ == "__main__":
    main()
