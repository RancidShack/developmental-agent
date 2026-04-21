"""
curiosity_agent_v0_4_3.py
-------------------------
Phase-structured developmental agent — corrected architecture.

Branches from v0.4.2 after the v0.4.2 failure. The failure revealed
that structure implemented by drive *suppression* (Phase 1 with only
coverage active) produces an agent that cannot find uncovered cells
because it has no directional signal — coverage ambient pressure is
undirected, and novelty was silenced.

v0.4.3 corrects the phase structure to be CUMULATIVE rather than
swapping:

PHASE 1 — ACQUISITION
    Coverage + Novelty active.
    Coverage provides the task (find the uncovered cells).
    Novelty provides the compass (go where you have been rarely).
    Progress and preference silent.
    Phase ends when every scope cell has been visited at least once.

PHASE 2 — INTEGRATION
    Coverage silent (its job is done).
    Novelty remains active.
    Progress joins — the agent begins to track where it is learning.
    Preference silent.
    Duration: runs until step PHASE_3_START_TARGET or end of life.

PHASE 3 — AUTONOMY
    Coverage silent.
    Novelty active.
    Progress active.
    Preference joins — the agent can be pulled by the regions it has
    come to find rewarding.

MEMORY ACROSS PHASES:
  - Forward model, error windows, visit counts, preferences: all carry
    over in full.
  - Q-values: partially reset (× 0.3) at each phase boundary.

Run from Terminal with:
    python3 curiosity_agent_v0_4_3.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque, Counter

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]
PHASE_3_START_FRACTION = 0.6
Q_VALUE_RESET_MULTIPLIER = 0.3


# --------------------------------------------------------------------------
# WORLD
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


# --------------------------------------------------------------------------
# AGENT
# --------------------------------------------------------------------------

class PhasedAgent:
    def __init__(self, scope_cells, total_steps, num_actions=4):
        self.scope = set(scope_cells)
        self.total_steps = total_steps
        self.steps_taken = 0
        self.covered = set()
        self.num_actions = num_actions

        # Memory carried across phases
        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.fast_errors = defaultdict(lambda: deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: deque(maxlen=30))
        self.cell_preference = defaultdict(float)
        self.q_values = defaultdict(float)

        # Phase tracking
        self.phase = 1
        self.phase_1_end_step = None
        self.phase_2_end_step = None
        self.phase_3_start_target = int(total_steps * PHASE_3_START_FRACTION)

        self.learning_rate = 0.1
        self.epsilon = 0.1

        self._apply_phase_weights()

    def _apply_phase_weights(self):
        """Cumulative drive activation across phases."""
        if self.phase == 1:
            # Coverage + Novelty. Novelty is the compass during acquisition.
            self.coverage_discovery_weight = 6.0
            self.coverage_ambient_weight = 0.005
            self.novelty_weight = 0.3
            self.progress_weight = 0.0
            self.preference_weight = 0.0
        elif self.phase == 2:
            # Novelty + Progress. Coverage silent — its job is done.
            self.coverage_discovery_weight = 0.0
            self.coverage_ambient_weight = 0.0
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.0
        elif self.phase == 3:
            # Novelty + Progress + Preference.
            self.coverage_discovery_weight = 0.0
            self.coverage_ambient_weight = 0.0
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.8

    def _transition_phase(self, new_phase):
        for key in list(self.q_values.keys()):
            self.q_values[key] *= Q_VALUE_RESET_MULTIPLIER
        self.phase = new_phase
        self._apply_phase_weights()

    def check_phase_transition(self):
        if self.phase == 1:
            if len(self.covered) == len(self.scope):
                self.phase_1_end_step = self.steps_taken
                self._transition_phase(2)
                return True
        elif self.phase == 2:
            if self.steps_taken >= self.phase_3_start_target:
                self.phase_2_end_step = self.steps_taken
                self._transition_phase(3)
                return True
        return False

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
        discovery = self.coverage_discovery_weight if (
            cell in self.scope and cell not in self.covered
        ) else 0.0
        uncovered_count = len(self.scope) - len(self.covered)
        ambient = self.coverage_ambient_weight * uncovered_count
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
        return self.progress_weight * max(0.0, progress)

    def update_model(self, state, action, next_state, error, r_progress):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)
        self.cell_preference[cell] += r_progress

    def update_values(self, state, action, next_state, intrinsic):
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error


# --------------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------------

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
    mastered_count_trace = []
    phase_trace = []

    state = world.observe()

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        agent.check_phase_transition()

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

        x, y, _ = next_state
        heatmap_by_phase[agent.phase][y, x] += 1

        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))
        progress_trace.append(r_progress)
        novelty_trace.append(r_novelty)
        preference_trace.append(r_preference)
        mastered_count_trace.append(sum(
            1 for errs in agent.fast_errors.values()
            if len(errs) >= 5 and np.mean(errs) < 0.15
        ))
        phase_trace.append(agent.phase)

        state = next_state

    # --- ANALYSIS ---
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

    p1_duration = agent.phase_1_end_step if agent.phase_1_end_step else NUM_STEPS
    p1_final_coverage = len(agent.covered) if not agent.phase_1_end_step else len(agent.scope)

    p3_visits = heatmap_by_phase[3]
    p3_total_visits = int(p3_visits.sum())
    if p3_total_visits > 0:
        p3_top_cell_visits = p3_visits.max()
        p3_uniform_expected = p3_total_visits / (GRID_SIZE * GRID_SIZE)
        p3_concentration = p3_top_cell_visits / p3_uniform_expected
    else:
        p3_concentration = 0.0

    # --- PLOTS ---
    fig, axes = plt.subplots(3, 2, figsize=(13, 13))

    ax = axes[0, 0]
    im = ax.imshow(heatmap_by_phase[1], cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title(f"Phase 1 (Acquisition) heatmap\n"
                 f"{p1_duration} steps, coverage {p1_final_coverage}/100")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[0, 1]
    im = ax.imshow(heatmap_by_phase[2], cmap="plasma", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="white", markersize=14)
    title2 = "Phase 2 (Integration) heatmap"
    if agent.phase_1_end_step is not None:
        p2_end = agent.phase_2_end_step if agent.phase_2_end_step else NUM_STEPS
        title2 += f"\nsteps {agent.phase_1_end_step}–{p2_end}"
    else:
        title2 += "\n(Phase 2 not entered)"
    ax.set_title(title2)
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1, 0]
    im = ax.imshow(heatmap_by_phase[3], cmap="magma", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="white", markersize=14)
    title3 = "Phase 3 (Autonomy) heatmap"
    if agent.phase_2_end_step is not None:
        title3 += f"\nsteps {agent.phase_2_end_step}–{NUM_STEPS}"
    else:
        title3 += "\n(Phase 3 not entered)"
    ax.set_title(title3)
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1, 1]
    ax.plot(coverage_pct_trace, linewidth=1.5, color="teal")
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--",
                   label=f"Phase 1 end @ {agent.phase_1_end_step}")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--",
                   label=f"Phase 2 end @ {agent.phase_2_end_step}")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage over time")
    ax.set_xlabel("Step"); ax.set_ylabel("% visited")
    ax.set_ylim(0, 105)

    ax = axes[2, 0]
    def running_mean(x, window=150):
        if len(x) < window: return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window
    ax.plot(running_mean(progress_trace), linewidth=1.2, color="darkgreen", label="progress")
    ax.plot(running_mean(novelty_trace), linewidth=1.2, color="navy", label="novelty")
    ax.plot(running_mean(preference_trace), linewidth=1.2, color="crimson", label="preference")
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
    plt.savefig("run_output_v0_4_3.png", dpi=120)

    # --- REPORT ---
    lines = []
    lines.append("=" * 68)
    lines.append("STRUCTURED CHARACTERISATION (v0.4.3 — phase-structured, cumulative)")
    lines.append("=" * 68)
    lines.append(f"Life length              : {NUM_STEPS} steps")
    lines.append("")
    lines.append("Phase 1 (Acquisition — coverage + novelty):")
    if agent.phase_1_end_step:
        lines.append(f"  Completed at step      : {agent.phase_1_end_step}")
        lines.append(f"  Feature visit ratio    : {feature_ratio(heatmap_by_phase[1]):.2f}x chance")
        lines.append(f"  Attention CV           : {attention_cv(heatmap_by_phase[1]):.2f}")
    else:
        lines.append(f"  Not completed          : reached {len(agent.covered)}/100 in {NUM_STEPS} steps")
        lines.append(f"  Feature visit ratio    : {feature_ratio(heatmap_by_phase[1]):.2f}x chance")
    lines.append("")
    if agent.phase_1_end_step:
        p2_end = agent.phase_2_end_step if agent.phase_2_end_step else NUM_STEPS
        p2_duration = p2_end - agent.phase_1_end_step
        lines.append("Phase 2 (Integration — novelty + progress):")
        lines.append(f"  Duration               : {p2_duration} steps")
        lines.append(f"  Feature visit ratio    : {feature_ratio(heatmap_by_phase[2]):.2f}x chance")
        lines.append(f"  Attention CV           : {attention_cv(heatmap_by_phase[2]):.2f}")
        lines.append("")
    if agent.phase_2_end_step:
        p3_duration = NUM_STEPS - agent.phase_2_end_step
        lines.append("Phase 3 (Autonomy — novelty + progress + preference):")
        lines.append(f"  Duration               : {p3_duration} steps")
        lines.append(f"  Feature visit ratio    : {feature_ratio(heatmap_by_phase[3]):.2f}x chance")
        lines.append(f"  Attention CV           : {attention_cv(heatmap_by_phase[3]):.2f}")
        lines.append(f"  Attention concentration: {p3_concentration:.1f}x uniform")
        lines.append("")
    lines.append(f"Total pairs mastered       : {mastered_count_trace[-1]}")
    lines.append("")
    lines.append("Top 5 preferred cells at end of life:")
    for cell, pref in top_preferred:
        marker = " (feature)" if cell in FEATURE_CELLS else ""
        lines.append(f"  {cell}: preference = {pref:.2f}{marker}")
    lines.append("")
    lines.append("=" * 68)
    lines.append("NARRATIVE")
    lines.append("=" * 68)
    lines.append("")
    if agent.phase_1_end_step:
        lines.append(f"My first {agent.phase_1_end_step} steps were given to acquisition. "
                     f"I was pulled by two things together — the presence of uncovered cells "
                     f"and the pull of cells I had seen only rarely. Novelty was my compass; "
                     f"coverage was my task. I completed the survey.")
        lines.append("")
        lines.append(f"I then entered integration. Coverage went silent — its work was done. "
                     f"Novelty remained with me, and learning progress joined. I revisited the "
                     f"territory I had surveyed, now attending to what I was learning.")
        lines.append("")
        if agent.phase_2_end_step:
            lines.append(f"At step {agent.phase_2_end_step} I entered autonomy. Preference was "
                         f"permitted to pull me toward what I had come to find rewarding. "
                         f"Whatever I spent my final time on reflects what I had become, "
                         f"not what I was told.")
        else:
            lines.append(f"I did not reach autonomy within my life. The integration phase ran "
                         f"until the end.")
    else:
        lines.append(f"My life ended before I had completed acquisition. I reached "
                     f"{len(agent.covered)} of the 100 cells. The phases that would have "
                     f"followed were not entered.")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open("self_report_v0_4_3.txt", "w") as f:
        f.write(report_str)
    print("\nReport saved to self_report_v0_4_3.txt")
    print("Plots saved to run_output_v0_4_3.png")
    plt.show()


if __name__ == "__main__":
    run()
