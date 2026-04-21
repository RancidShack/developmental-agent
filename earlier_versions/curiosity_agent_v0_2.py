"""
curiosity_agent_v0_2.py
-----------------------
A curiosity-driven reinforcement learning agent in a grid world.

Version 0.2 — changes from v0.1:
  * FIX: surprise is now calculated against the model's PRIOR prediction,
         before the model is updated with the new transition. In v0.1 the
         model was updated first, which always produced zero surprise.
  * IMPROVEMENT: surprise is computed using an additively smoothed
         probability, so "never seen this (state, action) pair" gives a
         maximal surprise signal rather than a silent full reward.
  * IMPROVEMENT: summary now reports a breakdown of novelty vs surprise
         contribution so you can see which drive is doing the work.
  * IMPROVEMENT: plots are laid out a little more informatively and
         include a running-mean overlay so trends are visible under noise.

The agent receives NO external reward.
Its only drives are:
  - Novelty       : visiting states it hasn't seen (or seen rarely)
  - Surprise      : its forward model was wrong about what would happen

Run from Terminal with:
    python3 curiosity_agent_v0_2.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# --------------------------------------------------------------------------
# 1. THE WORLD
# --------------------------------------------------------------------------

GRID_SIZE = 10
NUM_STEPS = 5000
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

class CuriosityAgent:
    def __init__(self, num_actions=4):
        self.num_actions = num_actions
        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.q_values = defaultdict(float)
        self.learning_rate = 0.1
        self.novelty_weight = 1.0
        self.surprise_weight = 1.0
        self.epsilon = 0.1

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.num_actions)
        values = [self.q_values[(state, a)] for a in range(self.num_actions)]
        max_v = max(values)
        best = [a for a, v in enumerate(values) if v == max_v]
        return np.random.choice(best)

    def novelty_reward(self, state):
        """Count-based novelty: cells seen often become less rewarding."""
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def surprise_reward(self, state, action, next_state):
        """
        Surprise = how wrong the PRIOR forward model was.

        Uses additive (Laplace) smoothing so that a never-seen pair gives a
        high but not infinite signal, and rare-but-seen outcomes still
        produce graded surprise.

        IMPORTANT: this must be called BEFORE update_model(), which is now
        a separate step.
        """
        predictions = self.forward_model[(state, action)]
        total = sum(predictions.values())
        # additive smoothing: pretend we've seen each possible outcome once
        # "possible outcomes" in practice is roughly small; we use 1 as the
        # pseudocount and a nominal vocabulary size for the denominator
        pseudo_vocab = 5
        smoothed_prob = (predictions[next_state] + 1) / (total + pseudo_vocab)
        return self.surprise_weight * (1.0 - smoothed_prob)

    def update_model(self, state, action, next_state):
        """Record the observed transition AFTER surprise has been measured."""
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1

    def update_values(self, state, action, next_state, intrinsic):
        """Q-learning update using intrinsic reward only."""
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error


# --------------------------------------------------------------------------
# 3. THE RUN
# --------------------------------------------------------------------------

def run():
    world = GridWorld()
    agent = CuriosityAgent()

    heatmap = np.zeros((GRID_SIZE, GRID_SIZE))
    novelty_trace = []
    surprise_trace = []
    total_reward_trace = []
    action_window = []
    entropy_trace = []
    event_log = []

    state = world.observe()

    for step in range(NUM_STEPS):
        action = agent.choose_action(state)
        next_state = world.step(action)

        # --- CORRECT ORDER ---------------------------------------------
        # 1. Measure surprise using the PRIOR model
        r_s = agent.surprise_reward(state, action, next_state)
        # 2. Compute novelty using PRIOR visit counts
        r_n = agent.novelty_reward(next_state)
        # 3. Combine into intrinsic reward
        intrinsic = r_n + r_s
        # 4. NOW update the model and visit counts
        agent.update_model(state, action, next_state)
        # 5. Update Q-values
        agent.update_values(state, action, next_state, intrinsic)
        # ----------------------------------------------------------------

        x, y, _ = next_state
        heatmap[y, x] += 1

        novelty_trace.append(r_n)
        surprise_trace.append(r_s)
        total_reward_trace.append(intrinsic)
        action_window.append(action)

        if len(action_window) > 200:
            action_window.pop(0)
        counts = np.bincount(action_window, minlength=4) / len(action_window)
        ent = -np.sum(counts * np.log(counts + 1e-9))
        entropy_trace.append(ent)

        if step == 500: event_log.append((step, "Early exploration phase"))
        if step == 2000: event_log.append((step, "Features should now be familiar"))
        if step == 4000: event_log.append((step, "World largely known — boredom onset"))

        state = next_state

    # ----------------------------------------------------------------------
    # 4. THE READOUT
    # ----------------------------------------------------------------------

    def running_mean(x, window=100):
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

    # Surprise
    ax = axes[1, 0]
    ax.plot(surprise_trace, linewidth=0.4, alpha=0.4, color="orange", label="raw")
    ax.plot(running_mean(surprise_trace), linewidth=1.5, color="darkred", label="rolling mean")
    ax.set_title("Prediction error (surprise) over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Surprise signal")
    ax.legend(loc="upper right", fontsize=8)

    # Entropy
    ax = axes[1, 1]
    ax.plot(entropy_trace, linewidth=0.8, color="purple")
    ax.set_title("Behavioural entropy\n(higher = more varied actions)")
    ax.set_xlabel("Step"); ax.set_ylabel("Entropy (nats)")

    plt.tight_layout()
    plt.savefig("run_output_v0_2.png", dpi=120)
    print("\nRun complete. Plots saved to run_output_v0_2.png")

    # Summary
    print("\n--- Summary (v0.2) ---")
    print(f"Total steps           : {NUM_STEPS}")
    print(f"Unique states visited : {len(agent.visit_counts)}")
    print(f"Mean novelty  (first 500) : {np.mean(novelty_trace[:500]):.3f}")
    print(f"Mean novelty  (last 500)  : {np.mean(novelty_trace[-500:]):.3f}")
    print(f"Mean surprise (first 500) : {np.mean(surprise_trace[:500]):.3f}")
    print(f"Mean surprise (last 500)  : {np.mean(surprise_trace[-500:]):.3f}")
    total_n = sum(novelty_trace)
    total_s = sum(surprise_trace)
    total = total_n + total_s
    print(f"\nDrive breakdown (share of total intrinsic reward):")
    print(f"  Novelty  : {100*total_n/total:5.1f}%")
    print(f"  Surprise : {100*total_s/total:5.1f}%")
    print("\nEvent log:")
    for s, msg in event_log:
        print(f"  step {s:>5} — {msg}")

    plt.show()


if __name__ == "__main__":
    run()
