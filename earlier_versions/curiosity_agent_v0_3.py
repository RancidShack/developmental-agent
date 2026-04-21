"""
curiosity_agent_v0_3.py
-----------------------
A curiosity-driven RL agent in a grid world, with LEARNING PROGRESS
(competence gain) as the primary intrinsic reward — not raw prediction
error.

Version 0.3 — changes from v0.2:
  * CORE SHIFT: "surprise" is replaced with "learning progress".
    Instead of rewarding the agent for being wrong, we reward the agent
    for GETTING LESS WRONG. This maps more closely onto how humans
    behave around material they are mastering — engaged while progress
    is happening, disengaged once it plateaus, indifferent to both
    fully-known and unlearnable states.
  * Each (state, action) pair keeps TWO moving averages of its
    prediction error: a short fast window and a longer slow window.
    Learning progress = slow_error - fast_error (clipped at 0).
    Positive when the agent is improving; zero when mastered; zero
    when noise (unlearnable).
  * Novelty is retained but deliberately downweighted so that progress
    has room to drive behaviour.
  * Summary adds a "mastered states" count — pairs whose fast error
    has dropped below a threshold.

Run from Terminal with:
    python3 curiosity_agent_v0_3.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque

# --------------------------------------------------------------------------
# 1. THE WORLD
# --------------------------------------------------------------------------

GRID_SIZE = 10
NUM_STEPS = 8000       # slightly longer run — mastery takes time to reveal
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]

class GridWorld:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.agent_pos = (0, 0)
        self.features = set(FEATURE_CELLS)

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

class LearningProgressAgent:
    def __init__(self, num_actions=4):
        self.num_actions = num_actions
        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.q_values = defaultdict(float)

        # Two moving averages of prediction error, per (state, action).
        # deque with fixed maxlen gives a rolling window automatically.
        self.fast_errors = defaultdict(lambda: deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: deque(maxlen=30))

        # Hyperparameters
        self.learning_rate = 0.1
        self.novelty_weight = 0.3      # deliberately smaller than v0.2
        self.progress_weight = 1.5     # the dominant drive now
        self.epsilon = 0.1

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

    def prediction_error(self, state, action, next_state):
        """
        The PRIOR error the forward model would have made. Used both to
        compute learning progress AND to update the error-tracking windows.
        """
        predictions = self.forward_model[(state, action)]
        total = sum(predictions.values())
        pseudo_vocab = 5
        smoothed_prob = (predictions[next_state] + 1) / (total + pseudo_vocab)
        return 1.0 - smoothed_prob

    def learning_progress(self, state, action):
        """
        Difference between slow-window error and fast-window error.
        Positive when the agent has recently been getting better at
        predicting transitions from this (state, action). Zero when
        mastered or when noise.
        """
        fast = self.fast_errors[(state, action)]
        slow = self.slow_errors[(state, action)]
        # Need enough samples in both windows to be meaningful
        if len(fast) < 3 or len(slow) < 10:
            return 0.0
        fast_mean = np.mean(fast)
        slow_mean = np.mean(slow)
        progress = slow_mean - fast_mean
        # Clip at zero — we don't punish the agent for noise/regression
        return self.progress_weight * max(0.0, progress)

    def update_model(self, state, action, next_state, error):
        """Update visit counts, forward model, AND the error windows."""
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)

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
    agent = LearningProgressAgent()

    heatmap = np.zeros((GRID_SIZE, GRID_SIZE))
    novelty_trace = []
    progress_trace = []
    raw_error_trace = []
    action_window = []
    entropy_trace = []
    event_log = []

    state = world.observe()

    for step in range(NUM_STEPS):
        action = agent.choose_action(state)
        next_state = world.step(action)

        # 1. Compute PRIOR prediction error (for learning-progress tracking)
        error = agent.prediction_error(state, action, next_state)
        # 2. Compute learning progress from PRIOR error windows
        r_progress = agent.learning_progress(state, action)
        # 3. Compute novelty from PRIOR visit counts
        r_novelty = agent.novelty_reward(next_state)
        # 4. Combine
        intrinsic = r_novelty + r_progress
        # 5. NOW update model, visit counts, and error windows
        agent.update_model(state, action, next_state, error)
        # 6. Update Q-values
        agent.update_values(state, action, next_state, intrinsic)

        x, y, _ = next_state
        heatmap[y, x] += 1

        novelty_trace.append(r_novelty)
        progress_trace.append(r_progress)
        raw_error_trace.append(error)
        action_window.append(action)

        if len(action_window) > 200:
            action_window.pop(0)
        counts = np.bincount(action_window, minlength=4) / len(action_window)
        ent = -np.sum(counts * np.log(counts + 1e-9))
        entropy_trace.append(ent)

        if step == 1000: event_log.append((step, "Early mastery phase"))
        if step == 3000: event_log.append((step, "First regions should be plateauing"))
        if step == 6000: event_log.append((step, "Agent should be relocating"))

        state = next_state

    # ----------------------------------------------------------------------
    # 4. THE READOUT
    # ----------------------------------------------------------------------

    def running_mean(x, window=150):
        if len(x) < window: return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Exploration heatmap
    ax = axes[0, 0]
    im = ax.imshow(heatmap, cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title("Exploration heatmap\n(red stars = feature cells)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Novelty
    ax = axes[0, 1]
    ax.plot(novelty_trace, linewidth=0.4, alpha=0.4, label="raw")
    ax.plot(running_mean(novelty_trace), linewidth=1.5, color="navy", label="rolling mean")
    ax.set_title("Novelty reward over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Novelty signal")
    ax.legend(loc="upper right", fontsize=8)

    # Learning progress (the new core signal)
    ax = axes[1, 0]
    ax.plot(progress_trace, linewidth=0.4, alpha=0.4, color="green", label="raw")
    ax.plot(running_mean(progress_trace), linewidth=1.5, color="darkgreen", label="rolling mean")
    ax.set_title("Learning progress (competence gain) over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Progress signal")
    ax.legend(loc="upper right", fontsize=8)

    # Entropy
    ax = axes[1, 1]
    ax.plot(entropy_trace, linewidth=0.8, color="purple")
    ax.set_title("Behavioural entropy\n(higher = more varied actions)")
    ax.set_xlabel("Step"); ax.set_ylabel("Entropy (nats)")

    plt.tight_layout()
    plt.savefig("run_output_v0_3.png", dpi=120)
    print("\nRun complete. Plots saved to run_output_v0_3.png")

    # Summary
    print("\n--- Summary (v0.3) ---")
    print(f"Total steps           : {NUM_STEPS}")
    print(f"Unique states visited : {len(agent.visit_counts)}")
    print(f"Mean novelty  (first 500) : {np.mean(novelty_trace[:500]):.3f}")
    print(f"Mean novelty  (last 500)  : {np.mean(novelty_trace[-500:]):.3f}")
    print(f"Mean progress (first 500) : {np.mean(progress_trace[:500]):.3f}")
    print(f"Mean progress (mid  500)  : {np.mean(progress_trace[3000:3500]):.3f}")
    print(f"Mean progress (last 500)  : {np.mean(progress_trace[-500:]):.3f}")
    print(f"Mean raw error (first 500): {np.mean(raw_error_trace[:500]):.3f}")
    print(f"Mean raw error (last 500) : {np.mean(raw_error_trace[-500:]):.3f}")

    # Count "mastered" (state, action) pairs: fast error < threshold
    mastered = 0
    total_tracked = 0
    for key in agent.fast_errors:
        if len(agent.fast_errors[key]) >= 5:
            total_tracked += 1
            if np.mean(agent.fast_errors[key]) < 0.15:
                mastered += 1
    print(f"\nMastery state:")
    print(f"  (state, action) pairs tracked : {total_tracked}")
    print(f"  of which mastered (error<0.15): {mastered}")
    if total_tracked > 0:
        print(f"  mastery ratio                 : {100*mastered/total_tracked:.1f}%")

    total_n = sum(novelty_trace)
    total_p = sum(progress_trace)
    total = total_n + total_p
    if total > 0:
        print(f"\nDrive breakdown (share of total intrinsic reward):")
        print(f"  Novelty         : {100*total_n/total:5.1f}%")
        print(f"  Learning progress: {100*total_p/total:5.1f}%")

    print("\nEvent log:")
    for s, msg in event_log:
        print(f"  step {s:>5} — {msg}")

    plt.show()


if __name__ == "__main__":
    run()
