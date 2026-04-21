"""
curiosity_agent_v0_7_1.py
-------------------------
v0.7 with preferences that track extrinsic feature reward directly,
not only learning progress.

Version 0.7.1 — single change from v0.7:
  * The cell_preference signal now accumulates BOTH the learning-progress
    reward AND the feature reward whenever the agent enters a cell.
  * Previously, preferences were built purely from progress, which
    caused preference mass to land in approach paths and high-progress
    cells rather than on feature cells themselves.
  * With this change, feature cells accumulate preference twice — once
    from any progress that accrues, once from the constant feature
    reward — so preference landscapes should now include features as
    local maxima, not saddles between them.

All other mechanisms identical to v0.7.

Run from Terminal with:
    python3 curiosity_agent_v0_7_1.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque, Counter

GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]
PHASE_3_START_FRACTION = 0.6
Q_VALUE_RESET_MULTIPLIER = 0.3
FEATURE_DRIVE_WEIGHT = 0.15


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


def boustrophedon_path(size):
    path = []
    for y in range(size):
        if y % 2 == 0:
            for x in range(size):
                path.append((x, y))
        else:
            for x in range(size - 1, -1, -1):
                path.append((x, y))
    return path


def action_to_move(from_cell, to_cell):
    fx, fy = from_cell
    tx, ty = to_cell
    dx = tx - fx
    dy = ty - fy
    if dy == -1: return 0
    if dy == 1:  return 1
    if dx == -1: return 2
    if dx == 1:  return 3
    return 0


class PhasedAgent:
    def __init__(self, scope_cells, total_steps, num_actions=4):
        self.scope = set(scope_cells)
        self.total_steps = total_steps
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
        self.prescribed_path = boustrophedon_path(GRID_SIZE)
        self.path_index = 0
        self.learning_rate = 0.1
        self.epsilon = 0.1
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
            if self.path_index >= len(self.prescribed_path):
                self.phase_1_end_step = self.steps_taken
                self._transition_phase(2)
                return True
        elif self.phase == 2:
            if self.steps_taken >= self.phase_3_start_target:
                self.phase_2_end_step = self.steps_taken
                self._transition_phase(3)
                return True
        return False

    def get_prescribed_action(self, current_cell):
        if self.path_index == 0:
            self.path_index = 1
        if self.path_index >= len(self.prescribed_path):
            return None
        next_cell = self.prescribed_path[self.path_index]
        action = action_to_move(current_cell, next_cell)
        self.path_index += 1
        return action

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

    def preference_reward(self, state):
        if self.preference_weight == 0.0:
            return 0.0
        cell = (state[0], state[1])
        return self.preference_weight * self.cell_preference[cell]

    def feature_reward(self, state):
        if self.feature_weight == 0.0:
            return 0.0
        is_feature = state[2]
        return self.feature_weight * is_feature

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
        """
        CHANGE FROM v0.7: preferences now accumulate BOTH progress and
        feature reward. Feature cells build preference mass directly
        when visited, not only through whatever progress happens to accrue.
        """
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)
        # THE KEY CHANGE: preferences += progress + feature reward
        self.cell_preference[cell] += r_progress + r_feature

    def update_values(self, state, action, next_state, intrinsic):
        if self.phase == 1:
            return
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error


def run():
    world = GridWorld()
    agent = PhasedAgent(world.scope_cells, NUM_STEPS)
    heatmap_by_phase = {1: np.zeros((GRID_SIZE, GRID_SIZE)),
                        2: np.zeros((GRID_SIZE, GRID_SIZE)),
                        3: np.zeros((GRID_SIZE, GRID_SIZE))}
    coverage_pct_trace = []
    progress_trace = []
    novelty_trace = []
    preference_trace = []
    feature_trace = []
    mastered_count_trace = []

    state = world.observe()

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        agent.check_phase_transition()

        if agent.phase == 1:
            current_cell = (state[0], state[1])
            action = agent.get_prescribed_action(current_cell)
            if action is None:
                action = 0
        else:
            action = agent.choose_action(state)

        next_state = world.step(action)
        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        r_feature = agent.feature_reward(next_state)
        intrinsic = r_novelty + r_progress + r_preference + r_feature

        agent.update_model(state, action, next_state, error, r_progress, r_feature)
        agent.update_values(state, action, next_state, intrinsic)

        x, y, _ = next_state
        heatmap_by_phase[agent.phase][y, x] += 1

        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))
        progress_trace.append(r_progress)
        novelty_trace.append(r_novelty)
        preference_trace.append(r_preference)
        feature_trace.append(r_feature)
        mastered_count_trace.append(sum(
            1 for errs in agent.fast_errors.values()
            if len(errs) >= 5 and np.mean(errs) < 0.15
        ))
        state = next_state

    top_preferred = sorted(agent.cell_preference.items(),
                           key=lambda kv: -kv[1])[:5]

    def feature_ratio(heatmap):
        total = heatmap.sum()
        if total == 0: return 0.0
        feature_visits = sum(heatmap[fy, fx] for fx, fy in FEATURE_CELLS)
        expected_share = len(FEATURE_CELLS) / (GRID_SIZE * GRID_SIZE)
        actual_share = feature_visits / total
        return actual_share / expected_share if expected_share > 0 else 0.0

    def attention_cv(heatmap):
        visits = heatmap[heatmap > 0]
        if len(visits) < 2: return 0.0
        return visits.std() / visits.mean()

    p3_visits = heatmap_by_phase[3]
    p3_total = int(p3_visits.sum())
    if p3_total > 0:
        p3_concentration = p3_visits.max() / (p3_total / (GRID_SIZE * GRID_SIZE))
    else:
        p3_concentration = 0.0

    fig, axes = plt.subplots(3, 2, figsize=(13, 13))

    ax = axes[0, 0]
    im = ax.imshow(heatmap_by_phase[1], cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title(f"Phase 1 (Prescribed)\nended at step {agent.phase_1_end_step}")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[0, 1]
    im = ax.imshow(heatmap_by_phase[2], cmap="plasma", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="white", markersize=14)
    ax.set_title("Phase 2 (Integration + feature drive)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1, 0]
    im = ax.imshow(heatmap_by_phase[3], cmap="magma", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="white", markersize=14)
    ax.set_title("Phase 3 (Autonomy + feature-valued preferences)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1, 1]
    ax.plot(coverage_pct_trace, linewidth=1.5, color="teal")
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--",
                   label=f"P1 end @ {agent.phase_1_end_step}")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--",
                   label=f"P2 end @ {agent.phase_2_end_step}")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage over time")
    ax.set_xlabel("Step"); ax.set_ylabel("% visited")
    ax.set_ylim(0, 105)

    ax = axes[2, 0]
    def running_mean(x, window=150):
        if len(x) < window: return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window
    ax.plot(running_mean(progress_trace), linewidth=1.0, color="darkgreen", label="progress")
    ax.plot(running_mean(novelty_trace), linewidth=1.0, color="navy", label="novelty")
    ax.plot(running_mean(preference_trace), linewidth=1.0, color="crimson", label="preference")
    ax.plot(running_mean(feature_trace), linewidth=1.0, color="goldenrod", label="feature")
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--")
    ax.set_title("Drive signals over time (rolling mean)")
    ax.set_xlabel("Step"); ax.set_ylabel("signal")
    ax.legend(fontsize=8)

    ax = axes[2, 1]
    ax.plot(mastered_count_trace, linewidth=1.5, color="sienna")
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--")
    ax.set_title("Mastery accumulation")
    ax.set_xlabel("Step"); ax.set_ylabel("# pairs mastered")

    plt.tight_layout()
    plt.savefig("run_output_v0_7_1.png", dpi=120)

    lines = []
    lines.append("=" * 68)
    lines.append("STRUCTURED CHARACTERISATION (v0.7.1 — feature-valued preferences)")
    lines.append("=" * 68)
    lines.append(f"Life length              : {NUM_STEPS} steps")
    lines.append(f"Feature drive weight     : {FEATURE_DRIVE_WEIGHT}")
    lines.append("Preferences accumulate   : progress + feature reward")
    lines.append("")
    if agent.phase_1_end_step:
        lines.append(f"Phase 1 ended at step {agent.phase_1_end_step}")
    if agent.phase_2_end_step:
        lines.append(f"Phase 2 duration: {agent.phase_2_end_step - agent.phase_1_end_step} steps")
        lines.append(f"  Feature visit ratio    : {feature_ratio(heatmap_by_phase[2]):.2f}x")
        lines.append(f"Phase 3 duration: {NUM_STEPS - agent.phase_2_end_step} steps")
        lines.append(f"  Feature visit ratio    : {feature_ratio(heatmap_by_phase[3]):.2f}x")
        lines.append(f"  Attention concentration: {p3_concentration:.1f}x uniform")
    lines.append("")
    lines.append(f"Total pairs mastered       : {mastered_count_trace[-1]}")
    lines.append("")
    lines.append("Top 5 preferred cells at end of life:")
    for cell, pref in top_preferred:
        marker = " (feature)" if cell in FEATURE_CELLS else ""
        lines.append(f"  {cell}: preference = {pref:.2f}{marker}")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open("self_report_v0_7_1.txt", "w") as f:
        f.write(report_str)
    print("\nReport saved to self_report_v0_7_1.txt")
    print("Plots saved to run_output_v0_7_1.png")
    plt.show()


if __name__ == "__main__":
    run()
