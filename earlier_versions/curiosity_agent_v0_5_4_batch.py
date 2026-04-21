"""
curiosity_agent_v0_5_4_batch.py
-------------------------------
Batch runner for the v0.5.4 developmental agent with gap detection.

Naming convention: the agent code is identical to v0.5.4, only the
harness differs, hence the _batch suffix rather than a new version number.

Purpose: determine whether the intention-action gap observed in single
runs is an architectural constant or a stochastic property that varies.
If the gap is large across most runs, v0.6 must address it structurally.
If the gap is sometimes small, we want to know under what conditions.

Run from Terminal with:
    python3 curiosity_agent_v0_5_4_batch.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
from collections import defaultdict, deque, Counter
import time

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

NUM_RUNS = 10
GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]
COUNTDOWN_FRACTION = 0.15

# --------------------------------------------------------------------------
# WORLD AND AGENT (identical to v0.5.4)
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
    def __init__(self, scope_cells, total_steps, num_actions=4):
        self.scope = set(scope_cells)
        self.total_steps = total_steps
        self.countdown_start = int(total_steps * (1.0 - COUNTDOWN_FRACTION))
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
        self.ambient_base_weight = 0.005
        self.preference_weight = 0.0
        self.epsilon = 0.1
        self.cell_preference = defaultdict(float)
        self.countdown_policy = None
        self.countdown_decision_reason = None
        self.top_preferred_at_countdown = []
        self.uncovered_at_countdown = set()
        self.countdown_cells_visited = Counter()

    def time_fraction_remaining(self):
        return max(0.0, 1.0 - (self.steps_taken / self.total_steps))

    def ambient_weight_now(self):
        if self.countdown_policy == "completion":
            return self.ambient_base_weight
        t = self.steps_taken / self.total_steps
        if t >= 0.5:
            return 0.0
        return self.ambient_base_weight * (1.0 - 2.0 * t)

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
        ambient = self.ambient_weight_now() * uncovered_count
        return discovery + ambient

    def preference_reward(self, state):
        if self.preference_weight == 0.0:
            return 0.0
        cell = (state[0], state[1])
        return self.preference_weight * self.cell_preference[cell]

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

    def update_model(self, state, action, next_state, error, r_progress):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)
        self.cell_preference[cell] += r_progress
        if self.steps_taken >= self.countdown_start:
            self.countdown_cells_visited[cell] += 1

    def update_values(self, state, action, next_state, intrinsic):
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def enter_countdown(self):
        uncovered_count = len(self.scope) - len(self.covered)
        self.uncovered_at_countdown = {c for c in self.scope if c not in self.covered}
        prefs = sorted(self.cell_preference.items(), key=lambda kv: -kv[1])
        self.top_preferred_at_countdown = [c for c, _ in prefs[:10]]
        pref_values = [v for _, v in prefs] if prefs else [0.0]
        top_pref = pref_values[0] if pref_values else 0.0
        mean_pref = np.mean(pref_values) if pref_values else 1e-6
        pref_clarity = top_pref / (mean_pref + 1e-6)

        if uncovered_count <= 10:
            self.countdown_policy = "preference"
        elif uncovered_count >= 25:
            self.countdown_policy = "completion"
        else:
            if pref_clarity >= 3.0:
                self.countdown_policy = "preference"
            else:
                self.countdown_policy = "completion"

        if self.countdown_policy == "preference":
            self.preference_weight = 2.0
            self.ambient_base_weight = 0.0
            self.discovery_weight = 0.0
        else:
            self.preference_weight = 0.0
            self.ambient_base_weight = 0.02
            self.discovery_weight = 8.0

    def measure_intention_action_gap(self):
        if self.countdown_policy == "completion":
            reached_in_countdown = self.uncovered_at_countdown & self.covered
            target_size = len(self.uncovered_at_countdown)
            if target_size == 0:
                return {"gap": 0.0, "target_size": 0, "achieved": 0}
            reached = len(reached_in_countdown)
            return {
                "gap": 1.0 - (reached / target_size),
                "target_size": target_size,
                "achieved": reached,
            }
        else:
            top_pref_set = set(self.top_preferred_at_countdown[:5])
            total_countdown_visits = sum(self.countdown_cells_visited.values())
            if total_countdown_visits == 0:
                return {"gap": 0.0, "target_size": 0, "achieved": 0}
            visits_in_preferred = sum(
                n for cell, n in self.countdown_cells_visited.items()
                if cell in top_pref_set
            )
            return {
                "gap": 1.0 - (visits_in_preferred / total_countdown_visits),
                "target_size": total_countdown_visits,
                "achieved": visits_in_preferred,
            }


# --------------------------------------------------------------------------
# SINGLE RUN
# --------------------------------------------------------------------------

def single_run():
    np.random.seed(None)
    world = GridWorld()
    agent = DevelopmentalAgent(world.scope_cells, NUM_STEPS)
    state = world.observe()
    coverage_at_countdown_start = None

    for step in range(NUM_STEPS):
        agent.steps_taken = step

        if step == agent.countdown_start and agent.countdown_policy is None:
            coverage_at_countdown_start = len(agent.covered)
            agent.enter_countdown()

        action = agent.choose_action(state)
        next_state = world.step(action)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_coverage = agent.coverage_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        intrinsic = r_novelty + r_progress + r_coverage + r_preference

        agent.update_model(state, action, next_state, error, r_progress)
        agent.update_values(state, action, next_state, intrinsic)
        state = next_state

    gap_info = agent.measure_intention_action_gap()
    return {
        "policy": agent.countdown_policy,
        "coverage_at_countdown": coverage_at_countdown_start,
        "coverage_at_end": len(agent.covered),
        "gap": gap_info["gap"],
        "target_size": gap_info["target_size"],
        "achieved": gap_info["achieved"],
    }


# --------------------------------------------------------------------------
# AGGREGATE REPORT
# --------------------------------------------------------------------------

def aggregate_and_report(results):
    n = len(results)
    out = []
    out.append("=" * 72)
    out.append(f"META-REPORT: INTENTION-ACTION GAP ACROSS {n} LIVES (v0.5.4 agent)")
    out.append("=" * 72)
    out.append("")

    # Per-run table
    out.append("PER-RUN RESULTS")
    out.append("-" * 72)
    out.append(f"{'run':>4} | {'policy':>10} | {'cov@cd':>6} | {'cov@end':>7} | "
               f"{'target':>6} | {'achieved':>8} | {'gap':>5}")
    out.append("-" * 72)
    for i, r in enumerate(results, 1):
        out.append(
            f"{i:>4} | {r['policy']:>10} | {r['coverage_at_countdown']:>6d} | "
            f"{r['coverage_at_end']:>7d} | {r['target_size']:>6d} | "
            f"{r['achieved']:>8d} | {r['gap']:.2f}"
        )

    # Policy split
    out.append("")
    out.append("POLICY DISTRIBUTION")
    out.append("-" * 72)
    policy_counts = Counter(r["policy"] for r in results)
    for policy, count in policy_counts.most_common():
        out.append(f"  {policy:>10}: {count}/{n} runs ({100*count/n:.0f}%)")

    # Gap statistics overall
    out.append("")
    out.append("GAP STATISTICS")
    out.append("-" * 72)
    gaps = [r["gap"] for r in results]
    out.append(f"  Mean gap                : {np.mean(gaps):.2f}")
    out.append(f"  Std of gap              : {np.std(gaps):.2f}")
    out.append(f"  Min gap                 : {min(gaps):.2f}")
    out.append(f"  Max gap                 : {max(gaps):.2f}")

    # Gap bands
    small = sum(1 for g in gaps if g <= 0.15)
    moderate = sum(1 for g in gaps if 0.15 < g <= 0.5)
    large = sum(1 for g in gaps if g > 0.5)
    out.append("")
    out.append(f"  Runs with small gap (<= 0.15)     : {small}/{n}")
    out.append(f"  Runs with moderate gap (0.15-0.5) : {moderate}/{n}")
    out.append(f"  Runs with large gap (> 0.5)       : {large}/{n}")

    # Gap by policy
    out.append("")
    out.append("GAP BY POLICY")
    out.append("-" * 72)
    for policy in ["completion", "preference"]:
        policy_results = [r for r in results if r["policy"] == policy]
        if policy_results:
            policy_gaps = [r["gap"] for r in policy_results]
            out.append(f"  {policy:>10}: n={len(policy_results):>2}, "
                       f"mean gap = {np.mean(policy_gaps):.2f}, "
                       f"std = {np.std(policy_gaps):.2f}")

    # Honest interpretation
    out.append("")
    out.append("=" * 72)
    out.append("INTERPRETATION")
    out.append("=" * 72)
    out.append("")
    mean_gap = np.mean(gaps)
    if mean_gap >= 0.5 and large >= 0.7 * n:
        out.append("The intention-action gap is ARCHITECTURAL. Across most runs the agent")
        out.append("fails to enact the policy it chose during the countdown. This is not a")
        out.append("stochastic property; it is a property of how the architecture integrates")
        out.append("stated intention with accumulated Q-values and visit counts.")
        out.append("")
        out.append("v0.6 must address this gap structurally if the agent is to grow through")
        out.append("self-observation. A dispositional self-model alone is insufficient.")
    elif mean_gap >= 0.3:
        out.append("The intention-action gap is SUBSTANTIAL across runs but not uniform.")
        out.append("Some runs show tighter alignment than others. The gap is a real and")
        out.append("meaningful phenomenon of this architecture, though not an absolute one.")
    elif small >= 0.7 * n:
        out.append("The intention-action gap is SMALL in most runs. The agent largely")
        out.append("succeeds in enacting its chosen countdown policy. If a gap appears")
        out.append("here and there, it is stochastic rather than structural.")
    else:
        out.append("The gap is VARIABLE — sometimes small, sometimes large — with no")
        out.append("clear dominant pattern across runs. Further analysis would be needed")
        out.append("to determine the conditions under which the gap grows or shrinks.")

    return "\n".join(out)


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main():
    print(f"Running {NUM_RUNS} independent lives of the v0.5.4 agent...")
    print(f"Each run = {NUM_STEPS} steps.")
    print()
    all_results = []
    start = time.time()

    for i in range(NUM_RUNS):
        r = single_run()
        all_results.append(r)
        print(f"  Run {i+1:2d}/{NUM_RUNS}: policy={r['policy']:>10}  "
              f"cov@cd={r['coverage_at_countdown']:>3d}  "
              f"cov@end={r['coverage_at_end']:>3d}  "
              f"target={r['target_size']:>4d}  "
              f"achieved={r['achieved']:>4d}  "
              f"gap={r['gap']:.2f}")

    total_time = time.time() - start
    print(f"\nAll runs complete in {total_time:.1f} seconds.")

    report = aggregate_and_report(all_results)
    print()
    print(report)

    with open("meta_report_v0_5_4.txt", "w") as f:
        f.write(report)
    print(f"\nMeta-report saved to meta_report_v0_5_4.txt")


if __name__ == "__main__":
    main()
