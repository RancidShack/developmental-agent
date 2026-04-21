"""
curiosity_agent_v0_4.py
-----------------------
A curiosity-driven agent in a bounded, time-limited world.

Version 0.4 — changes from v0.3:
  * SCOPE SHOWN. At initialisation the agent receives a map: the set of
    cells it is responsible for. It does not know what is IN the cells,
    only which cells exist and are in-scope.
  * TIME GIVEN. The agent is told its total step budget at the start.
    As time runs down, a subtle temporal weighting nudges attention
    toward unmastered-but-progressing regions. No panic, no frenzy —
    just a gentle urgency.
  * COVERAGE DRIVE. A new intrinsic drive rewards visiting any cell in
    the map that has not yet been visited at least once. Strong while
    uncovered cells remain; switches off when all cells have been touched.
  * METRICS CHANGED. We now track:
      - Coverage over time (% of map visited at least once)
      - Focus index (post-coverage concentration in top cells)
      - Mastery accumulation curve
    so we can read the survey-then-focus behaviour directly.

This is an intermediate step toward a learner-centred architecture.
It is NOT that architecture. See notes in the accompanying conversation
for why genuine understanding-driven behaviour requires further changes.

Run from Terminal with:
    python3 curiosity_agent_v0_4.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque

# --------------------------------------------------------------------------
# 1. THE WORLD
# --------------------------------------------------------------------------

GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]

class GridWorld:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.agent_pos = (0, 0)
        self.features = set(FEATURE_CELLS)
        # The full set of in-scope cells. In this simple world, every cell
        # is in-scope. In richer worlds we could carve out sub-regions.
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
# 2. THE AGENT
# --------------------------------------------------------------------------

class DevelopmentalAgent:
    def __init__(self, scope_cells, total_steps, num_actions=4):
        # Scope and time — given at the start
        self.scope = set(scope_cells)
        self.total_steps = total_steps
        self.steps_taken = 0

        # Coverage tracking: which scope cells have been visited at least once
        self.covered = set()

        self.num_actions = num_actions
        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.q_values = defaultdict(float)
        self.fast_errors = defaultdict(lambda: deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: deque(maxlen=30))

        # Hyperparameters
        self.learning_rate = 0.1
        self.novelty_weight = 0.25
        self.progress_weight = 1.2
        self.coverage_weight = 2.0      # loud early, but turns OFF when done
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
        """
        Strong bonus for reaching a cell in the scope that has not yet
        been covered. Turns off permanently once all scope cells are
        covered.
        """
        # Extract the (x, y) from the state tuple (state is (x, y, is_feature))
        cell = (state[0], state[1])
        if cell in self.scope and cell not in self.covered:
            return self.coverage_weight
        return 0.0

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
        # Temporal weighting: a gentle late-run boost on progress-rich regions.
        # Early in the run, this multiplier is near 1.0. As time runs down,
        # it climbs modestly, nudging attention toward regions where the
        # agent is still making gains.
        time_gone = 1.0 - self.time_fraction_remaining()
        temporal_mult = 1.0 + 0.5 * time_gone  # up to 1.5x by the end
        return self.progress_weight * max(0.0, progress) * temporal_mult

    def update_model(self, state, action, next_state, error):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        # Record coverage
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)

    def update_values(self, state, action, next_state, intrinsic):
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error


# --------------------------------------------------------------------------
# 3. THE RUN
# --------------------------------------------------------------------------

def run():
    world = GridWorld()
    agent = DevelopmentalAgent(world.scope_cells, NUM_STEPS)

    heatmap = np.zeros((GRID_SIZE, GRID_SIZE))
    novelty_trace = []
    progress_trace = []
    coverage_reward_trace = []
    coverage_pct_trace = []
    mastery_ratio_trace = []
    action_window = []
    entropy_trace = []
    event_log = []

    state = world.observe()
    coverage_complete_step = None

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        action = agent.choose_action(state)
        next_state = world.step(action)

        # Compute all intrinsic drives against PRIOR state of knowledge
        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_coverage = agent.coverage_reward(next_state)
        intrinsic = r_novelty + r_progress + r_coverage

        # Update knowledge
        agent.update_model(state, action, next_state, error)
        agent.update_values(state, action, next_state, intrinsic)

        x, y, _ = next_state
        heatmap[y, x] += 1

        novelty_trace.append(r_novelty)
        progress_trace.append(r_progress)
        coverage_reward_trace.append(r_coverage)
        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))

        # Mastery ratio at this step (fraction of tracked pairs with low recent error)
        tracked = 0
        mastered = 0
        for key, errs in agent.fast_errors.items():
            if len(errs) >= 5:
                tracked += 1
                if np.mean(errs) < 0.15:
                    mastered += 1
        mastery_ratio_trace.append(100 * mastered / tracked if tracked > 0 else 0)

        action_window.append(action)
        if len(action_window) > 200:
            action_window.pop(0)
        counts = np.bincount(action_window, minlength=4) / len(action_window)
        ent = -np.sum(counts * np.log(counts + 1e-9))
        entropy_trace.append(ent)

        # Event markers
        if coverage_complete_step is None and len(agent.covered) == len(agent.scope):
            coverage_complete_step = step
            event_log.append((step, "COVERAGE COMPLETE — survey phase ends"))

        state = next_state

    # ----------------------------------------------------------------------
    # 4. THE READOUT
    # ----------------------------------------------------------------------

    def running_mean(x, window=150):
        if len(x) < window: return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window

    fig, axes = plt.subplots(3, 2, figsize=(13, 13))

    # Exploration heatmap
    ax = axes[0, 0]
    im = ax.imshow(heatmap, cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title("Exploration heatmap\n(red stars = feature cells)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Coverage over time — the key new plot
    ax = axes[0, 1]
    ax.plot(coverage_pct_trace, linewidth=1.5, color="teal")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8,
                   label=f"coverage complete @ step {coverage_complete_step}")
        ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage of scope over time")
    ax.set_xlabel("Step"); ax.set_ylabel("% of scope visited")
    ax.set_ylim(0, 105)

    # Learning progress
    ax = axes[1, 0]
    ax.plot(progress_trace, linewidth=0.4, alpha=0.35, color="green", label="raw")
    ax.plot(running_mean(progress_trace), linewidth=1.5, color="darkgreen", label="rolling mean")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8)
    ax.set_title("Learning progress over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Progress signal")
    ax.legend(loc="upper right", fontsize=8)

    # Mastery accumulation
    ax = axes[1, 1]
    ax.plot(mastery_ratio_trace, linewidth=1.2, color="sienna")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8)
    ax.set_title("Mastery accumulation over time")
    ax.set_xlabel("Step"); ax.set_ylabel("% tracked pairs mastered")
    ax.set_ylim(0, 105)

    # Novelty
    ax = axes[2, 0]
    ax.plot(novelty_trace, linewidth=0.4, alpha=0.35, label="raw")
    ax.plot(running_mean(novelty_trace), linewidth=1.5, color="navy", label="rolling mean")
    ax.set_title("Novelty reward over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Novelty signal")
    ax.legend(loc="upper right", fontsize=8)

    # Entropy
    ax = axes[2, 1]
    ax.plot(entropy_trace, linewidth=0.8, color="purple")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8)
    ax.set_title("Behavioural entropy")
    ax.set_xlabel("Step"); ax.set_ylabel("Entropy (nats)")

    plt.tight_layout()
    plt.savefig("run_output_v0_4.png", dpi=120)
    print("\nRun complete. Plots saved to run_output_v0_4.png")

    # Summary
    print("\n--- Summary (v0.4) ---")
    print(f"Total steps               : {NUM_STEPS}")
    print(f"Scope size                : {len(agent.scope)} cells")
    print(f"Covered at end            : {len(agent.covered)} / {len(agent.scope)}  "
          f"({100*len(agent.covered)/len(agent.scope):.1f}%)")
    if coverage_complete_step is not None:
        print(f"Coverage completed at step: {coverage_complete_step} "
              f"({100*coverage_complete_step/NUM_STEPS:.1f}% of life)")
    else:
        print(f"Coverage completed at step: NOT COMPLETED within budget")

    # Focus index: in the post-coverage phase, what fraction of steps
    # were spent in the top-5 most-visited cells?
    if coverage_complete_step is not None:
        post = heatmap.copy()
        # We don't have per-step position lists, but we can approximate:
        # of total visits AFTER coverage, what fraction went to the top 5 cells?
        # We'll compute this from the full heatmap as a reasonable proxy.
        flat = sorted(heatmap.flatten(), reverse=True)
        top5 = sum(flat[:5])
        total = sum(flat)
        print(f"Focus index (top-5 share) : {100*top5/total:.1f}% of total visits")

    print(f"\nFinal mastery ratio        : {mastery_ratio_trace[-1]:.1f}%")
    print(f"Mastery @ coverage-complete: "
          f"{mastery_ratio_trace[coverage_complete_step]:.1f}%"
          if coverage_complete_step is not None
          else "Mastery @ coverage-complete: n/a")

    total_n = sum(novelty_trace)
    total_p = sum(progress_trace)
    total_c = sum(coverage_reward_trace)
    total = total_n + total_p + total_c
    if total > 0:
        print(f"\nDrive breakdown (share of total intrinsic reward):")
        print(f"  Coverage        : {100*total_c/total:5.1f}%")
        print(f"  Novelty         : {100*total_n/total:5.1f}%")
        print(f"  Learning progress: {100*total_p/total:5.1f}%")

    print("\nEvent log:")
    for s, msg in event_log:
        print(f"  step {s:>5} — {msg}")

    plt.show()


if __name__ == "__main__":
    run()
