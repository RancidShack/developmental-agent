"""
curiosity_agent_v0_6_batch.py
-----------------------------
Batch runner for the v0.6 agent with scheduled reflection.

Purpose: determine whether the strengthen/abandon/persist pattern
observed in single runs is a stable architectural phenomenon or varies
meaningfully across runs. Specifically we want to know:
  - How often does strengthening alone close the gap (no abandonment)?
  - How often does the agent proceed all the way to abandonment?
  - Does the abandon->completion transition produce more coverage gain
    than no-abandon runs?
  - What fraction of runs have clean persistence (no strengthening
    needed at all)?

The answers will tell us whether each reflection mechanism is doing
real architectural work or is cosmetic.

Run from Terminal with:
    python3 curiosity_agent_v0_6_batch.py
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
REFLECTION_OFFSETS = [500, 1000]
REFLECTION_GAP_THRESHOLD = 0.5


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
        self.reflection_steps = [self.countdown_start + o for o in REFLECTION_OFFSETS]
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
        self.original_policy = None
        self.top_preferred_at_countdown = []
        self.uncovered_at_countdown = set()
        self.countdown_cells_visited = Counter()
        self.cells_since_last_reflection = Counter()
        self.covered_since_last_reflection = set()
        self.reflection_events = []

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
            if self.steps_taken >= self.countdown_start:
                self.covered_since_last_reflection.add(cell)
        self.cell_preference[cell] += r_progress
        if self.steps_taken >= self.countdown_start:
            self.countdown_cells_visited[cell] += 1
            self.cells_since_last_reflection[cell] += 1

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

        self.original_policy = self.countdown_policy
        self._apply_policy_weights()

    def _apply_policy_weights(self):
        if self.countdown_policy == "preference":
            self.preference_weight = 2.0
            self.ambient_base_weight = 0.0
            self.discovery_weight = 0.0
        else:
            self.preference_weight = 0.0
            self.ambient_base_weight = 0.02
            self.discovery_weight = 8.0

    def measure_partial_gap(self):
        if self.countdown_policy == "completion":
            newly_covered = self.covered_since_last_reflection & self.uncovered_at_countdown
            still_uncovered_at_start_of_window = self.uncovered_at_countdown - (self.covered - self.covered_since_last_reflection)
            if not still_uncovered_at_start_of_window:
                return 0.0, 0, 0
            reached = len(newly_covered)
            expected = min(3, len(still_uncovered_at_start_of_window))
            alignment = min(1.0, reached / expected) if expected > 0 else 1.0
            return 1.0 - alignment, reached, expected
        else:
            top_pref_set = set(self.top_preferred_at_countdown[:5])
            window_visits = sum(self.cells_since_last_reflection.values())
            if window_visits == 0:
                return 0.0, 0, 0
            visits_in_preferred = sum(
                n for cell, n in self.cells_since_last_reflection.items()
                if cell in top_pref_set
            )
            alignment = visits_in_preferred / window_visits
            return 1.0 - alignment, visits_in_preferred, window_visits

    def reflect(self, reflection_index):
        gap, achieved, target = self.measure_partial_gap()
        event = {
            "step": self.steps_taken,
            "reflection_index": reflection_index,
            "policy_before": self.countdown_policy,
            "gap": gap,
            "achieved": achieved,
            "target": target,
        }

        if gap <= REFLECTION_GAP_THRESHOLD:
            event["response"] = "persist"
        else:
            prior_strengthen = any(e.get("response") == "strengthen"
                                   for e in self.reflection_events)
            if not prior_strengthen:
                event["response"] = "strengthen"
                if self.countdown_policy == "preference":
                    self.preference_weight = 4.0
                else:
                    self.ambient_base_weight = 0.04
                    self.discovery_weight = 16.0
            else:
                new_policy = "completion" if self.countdown_policy == "preference" else "preference"
                event["response"] = "abandon"
                self.countdown_policy = new_policy
                self._apply_policy_weights()

        self.cells_since_last_reflection = Counter()
        self.covered_since_last_reflection = set()
        self.reflection_events.append(event)
        return event

    def final_gap_measurement(self):
        if self.countdown_policy == "completion":
            reached_in_countdown = self.uncovered_at_countdown & self.covered
            target_size = len(self.uncovered_at_countdown)
            if target_size == 0:
                return {"gap": 0.0, "target_size": 0, "achieved": 0}
            reached = len(reached_in_countdown)
            return {"gap": 1.0 - (reached / target_size),
                    "target_size": target_size, "achieved": reached}
        else:
            top_pref_set = set(self.top_preferred_at_countdown[:5])
            total = sum(self.countdown_cells_visited.values())
            if total == 0:
                return {"gap": 0.0, "target_size": 0, "achieved": 0}
            in_pref = sum(n for cell, n in self.countdown_cells_visited.items()
                          if cell in top_pref_set)
            return {"gap": 1.0 - (in_pref / total),
                    "target_size": total, "achieved": in_pref}


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
        if step in agent.reflection_steps:
            agent.reflect(len(agent.reflection_events) + 1)

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

    final_gap = agent.final_gap_measurement()
    responses = [e["response"] for e in agent.reflection_events]

    # Classify the trajectory of responses
    if responses == ["persist", "persist"]:
        trajectory = "clean_persistence"
    elif "abandon" in responses:
        trajectory = "abandoned"
    elif responses == ["strengthen", "persist"]:
        trajectory = "strengthen_then_persist"
    elif responses == ["persist", "strengthen"]:
        trajectory = "late_strengthen"
    else:
        trajectory = "other"

    return {
        "original_policy": agent.original_policy,
        "final_policy": agent.countdown_policy,
        "coverage_at_countdown": coverage_at_countdown_start,
        "coverage_at_end": len(agent.covered),
        "coverage_gain": len(agent.covered) - coverage_at_countdown_start,
        "final_gap": final_gap["gap"],
        "reflection_responses": responses,
        "reflection_gaps": [e["gap"] for e in agent.reflection_events],
        "trajectory": trajectory,
        "abandoned": "abandon" in responses,
    }


def aggregate_and_report(results):
    n = len(results)
    out = []
    out.append("=" * 78)
    out.append(f"META-REPORT: REFLECTION OUTCOMES ACROSS {n} LIVES (v0.6 agent)")
    out.append("=" * 78)
    out.append("")

    out.append("PER-RUN RESULTS")
    out.append("-" * 78)
    out.append(f"{'run':>3} | {'orig':>10} | {'final':>10} | {'cov@cd':>6} | "
               f"{'cov@end':>7} | {'gain':>4} | {'r1':>10} | {'r2':>10} | {'gap':>5}")
    out.append("-" * 78)
    for i, r in enumerate(results, 1):
        r1 = r["reflection_responses"][0] if len(r["reflection_responses"]) >= 1 else "-"
        r2 = r["reflection_responses"][1] if len(r["reflection_responses"]) >= 2 else "-"
        out.append(
            f"{i:>3} | {r['original_policy']:>10} | {r['final_policy']:>10} | "
            f"{r['coverage_at_countdown']:>6d} | {r['coverage_at_end']:>7d} | "
            f"{r['coverage_gain']:>4d} | {r1:>10} | {r2:>10} | {r['final_gap']:.2f}"
        )

    # Trajectory distribution
    out.append("")
    out.append("TRAJECTORY DISTRIBUTION")
    out.append("-" * 78)
    traj_counts = Counter(r["trajectory"] for r in results)
    for traj, count in traj_counts.most_common():
        out.append(f"  {traj:30s}: {count}/{n} runs ({100*count/n:.0f}%)")

    # Abandonment rate
    abandoned = sum(1 for r in results if r["abandoned"])
    out.append("")
    out.append(f"Abandonment rate              : {abandoned}/{n} runs ({100*abandoned/n:.0f}%)")

    # Coverage gain comparison
    out.append("")
    out.append("COVERAGE GAIN DURING COUNTDOWN")
    out.append("-" * 78)
    all_gains = [r["coverage_gain"] for r in results]
    out.append(f"  Mean coverage gain            : {np.mean(all_gains):.2f} cells")
    out.append(f"  Std of coverage gain          : {np.std(all_gains):.2f}")

    abandoned_gains = [r["coverage_gain"] for r in results if r["abandoned"]]
    not_abandoned_gains = [r["coverage_gain"] for r in results if not r["abandoned"]]
    if abandoned_gains:
        out.append(f"  Mean gain (abandoned runs)    : {np.mean(abandoned_gains):.2f} cells "
                   f"(n={len(abandoned_gains)})")
    if not_abandoned_gains:
        out.append(f"  Mean gain (not abandoned)     : {np.mean(not_abandoned_gains):.2f} cells "
                   f"(n={len(not_abandoned_gains)})")

    # Did strengthening ever close the gap?
    out.append("")
    out.append("STRENGTHENING EFFICACY")
    out.append("-" * 78)
    strengthen_then_no_abandon = sum(
        1 for r in results
        if "strengthen" in r["reflection_responses"] and not r["abandoned"]
    )
    strengthen_then_abandon = sum(
        1 for r in results
        if "strengthen" in r["reflection_responses"] and r["abandoned"]
    )
    out.append(f"  Strengthened and then did NOT abandon : {strengthen_then_no_abandon}/{n}")
    out.append(f"  Strengthened and THEN abandoned       : {strengthen_then_abandon}/{n}")

    # Interpretation
    out.append("")
    out.append("=" * 78)
    out.append("INTERPRETATION")
    out.append("=" * 78)
    out.append("")

    if abandoned / n >= 0.7:
        out.append("ABANDONMENT is the dominant architectural trajectory. In most runs the")
        out.append("agent recognises mid-countdown that its stated policy is not being")
        out.append("enacted, attempts to strengthen, finds the strengthening insufficient,")
        out.append("and switches to the policy that matches its actual behaviour.")
        out.append("")
        out.append("This is a stable behavioural signature: the strengthen response is")
        out.append("architecturally insufficient, and abandon is the only response that")
        out.append("meaningfully changes trajectory.")
    elif abandoned / n <= 0.3:
        out.append("ABANDONMENT is RARE. Most runs either persist cleanly or resolve")
        out.append("with strengthening alone. This would suggest the architecture is")
        out.append("more flexible than the v0.5.4 batch suggested.")
    else:
        out.append("Abandonment rate is INTERMEDIATE. Some runs resolve with strengthening,")
        out.append("some abandon. The conditions that distinguish these trajectories are")
        out.append("worth further analysis.")

    if strengthen_then_no_abandon == 0 and strengthen_then_abandon >= 0.5 * n:
        out.append("")
        out.append("STRENGTHENING IS FUNCTIONALLY INERT. Every run that attempted")
        out.append("strengthening went on to abandon. Doubling the drive weight is not")
        out.append("enough to overcome Q-value inertia in the remaining countdown time.")
        out.append("")
        out.append("For a future version, the strengthen response should either be")
        out.append("redesigned (perhaps with partial Q-value reset) or removed.")

    if np.mean(all_gains) < 2.0:
        out.append("")
        out.append("COVERAGE GAIN during the countdown is consistently small, regardless of")
        out.append("trajectory. Even abandoned-to-completion runs do not produce meaningful")
        out.append("coverage expansion in the remaining 500 steps. This reinforces the")
        out.append("underlying finding: late-stage policy changes have limited behavioural")
        out.append("reach in this architecture.")

    return "\n".join(out)


def main():
    print(f"Running {NUM_RUNS} independent lives of the v0.6 agent...")
    print(f"Each run = {NUM_STEPS} steps with 2 scheduled reflections.")
    print()
    all_results = []
    start = time.time()

    for i in range(NUM_RUNS):
        r = single_run()
        all_results.append(r)
        r1 = r["reflection_responses"][0] if len(r["reflection_responses"]) >= 1 else "-"
        r2 = r["reflection_responses"][1] if len(r["reflection_responses"]) >= 2 else "-"
        print(f"  Run {i+1:2d}/{NUM_RUNS}: orig={r['original_policy']:>10} final={r['final_policy']:>10} "
              f"cov {r['coverage_at_countdown']:>3d}->{r['coverage_at_end']:>3d} (+{r['coverage_gain']:>2d}) "
              f"reflections: [{r1}, {r2}]  gap={r['final_gap']:.2f}")

    total_time = time.time() - start
    print(f"\nAll runs complete in {total_time:.1f} seconds.")

    report = aggregate_and_report(all_results)
    print()
    print(report)

    with open("meta_report_v0_6.txt", "w") as f:
        f.write(report)
    print(f"\nMeta-report saved to meta_report_v0_6.txt")


if __name__ == "__main__":
    main()
