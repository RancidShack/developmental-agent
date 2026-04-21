"""
curiosity_agent.py
------------------
A curiosity-driven reinforcement learning agent in a grid world.

The agent receives NO external reward for completing tasks.
Its only drives are:
  - Novelty       : visiting states it hasn't seen (or seen rarely)
  - Uncertainty   : resolving things it doesn't yet understand
  - Prediction    : being surprised by its environment triggers exploration

You will see the agent move from random flailing, to pattern-seeking,
to something that looks like deliberate exploration, and finally to
boredom as its world becomes fully known.

Run from Terminal with:
    python3 curiosity_agent.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# --------------------------------------------------------------------------
# 1. THE WORLD
# --------------------------------------------------------------------------
# A 10x10 grid. Most cells are ordinary floor. A few cells are "features" —
# they feel different to the agent, producing a distinct observation when
# visited. Features are what the agent becomes curious about.
# --------------------------------------------------------------------------

GRID_SIZE = 10
NUM_STEPS = 5000          # total steps the agent will take
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]

class GridWorld:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.agent_pos = (0, 0)
        self.features = set(FEATURE_CELLS)

    def observe(self):
        """What the agent perceives: its position + whether current cell is special."""
        x, y = self.agent_pos
        is_feature = 1 if self.agent_pos in self.features else 0
        return (x, y, is_feature)

    def step(self, action):
        """Actions: 0=up, 1=down, 2=left, 3=right. Walls block movement."""
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
# The agent maintains three internal systems:
#
#   (a) Visit counts — for novelty. Cells seen often become less rewarding.
#   (b) A forward model — a simple table that predicts the next state given
#       the current state and chosen action. Prediction errors drive curiosity.
#   (c) An action-value table — updated using INTRINSIC reward only.
#
# There is NO external reward anywhere in this code. The agent is learning
# purely because being surprised feels important to it.
# --------------------------------------------------------------------------

class CuriosityAgent:
    def __init__(self, num_actions=4):
        self.num_actions = num_actions
        self.visit_counts = defaultdict(int)
        # Forward model: (state, action) -> predicted next state (as dict of counts)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        # Q-values: (state, action) -> value
        self.q_values = defaultdict(float)
        # Hyperparameters
        self.learning_rate = 0.1
        self.novelty_weight = 1.0
        self.surprise_weight = 1.0
        self.epsilon = 0.1   # a little randomness keeps exploration alive

    def choose_action(self, state):
        """Pick the action with highest expected intrinsic reward (with some noise)."""
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.num_actions)
        values = [self.q_values[(state, a)] for a in range(self.num_actions)]
        max_v = max(values)
        # break ties randomly so the agent doesn't get stuck in a corner
        best = [a for a, v in enumerate(values) if v == max_v]
        return np.random.choice(best)

    def novelty_reward(self, state):
        """Inverse square root of visit count — classic count-based novelty."""
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def surprise_reward(self, state, action, next_state):
        """How wrong was the forward model? High error = high surprise = reward."""
        predictions = self.forward_model[(state, action)]
        total = sum(predictions.values())
        if total == 0:
            return self.surprise_weight  # fully surprising — never seen this pair
        predicted_prob = predictions[next_state] / total
        # surprise is inversely proportional to predicted probability
        return self.surprise_weight * (1.0 - predicted_prob)

    def update(self, state, action, next_state):
        """Update visit counts, forward model, and Q-values."""
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        r_novel = self.novelty_reward(next_state)
        r_surprise = self.surprise_reward(state, action, next_state)
        intrinsic = r_novel + r_surprise
        # Q-learning update using intrinsic reward only
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error
        return intrinsic, r_novel, r_surprise


# --------------------------------------------------------------------------
# 3. THE RUN
# --------------------------------------------------------------------------

def run():
    world = GridWorld()
    agent = CuriosityAgent()

    # Logging
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
        intrinsic, r_n, r_s = agent.update(state, action, next_state)

        # record position for heatmap
        x, y, _ = next_state
        heatmap[y, x] += 1

        novelty_trace.append(r_n)
        surprise_trace.append(r_s)
        total_reward_trace.append(intrinsic)
        action_window.append(action)

        # rolling entropy of recent actions (behavioural predictability)
        if len(action_window) > 200:
            action_window.pop(0)
        counts = np.bincount(action_window, minlength=4) / len(action_window)
        ent = -np.sum(counts * np.log(counts + 1e-9))
        entropy_trace.append(ent)

        # event markers
        if step == 500: event_log.append((step, "Early exploration phase"))
        if step == 2000: event_log.append((step, "Features should now be familiar"))
        if step == 4000: event_log.append((step, "World largely known — boredom onset"))

        state = next_state

    # ----------------------------------------------------------------------
    # 4. THE READOUT
    # ----------------------------------------------------------------------

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Exploration heatmap
    ax = axes[0, 0]
    im = ax.imshow(heatmap, cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title("Exploration heatmap\n(red stars = feature cells)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Novelty reward over time
    ax = axes[0, 1]
    ax.plot(novelty_trace, linewidth=0.6)
    ax.set_title("Novelty reward over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Novelty signal")

    # Surprise/prediction error over time
    ax = axes[1, 0]
    ax.plot(surprise_trace, linewidth=0.6, color="darkorange")
    ax.set_title("Prediction error (surprise) over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Surprise signal")

    # Behavioural entropy
    ax = axes[1, 1]
    ax.plot(entropy_trace, linewidth=0.8, color="purple")
    ax.set_title("Behavioural entropy\n(higher = more varied actions)")
    ax.set_xlabel("Step"); ax.set_ylabel("Entropy (nats)")

    plt.tight_layout()
    plt.savefig("run_output.png", dpi=120)
    print("\nRun complete. Plots saved to run_output.png")

    # Summary
    print("\n--- Summary ---")
    print(f"Total steps           : {NUM_STEPS}")
    print(f"Unique states visited : {len(agent.visit_counts)}")
    print(f"Mean novelty (first 500) : {np.mean(novelty_trace[:500]):.3f}")
    print(f"Mean novelty (last 500)  : {np.mean(novelty_trace[-500:]):.3f}")
    print(f"Mean surprise (first 500): {np.mean(surprise_trace[:500]):.3f}")
    print(f"Mean surprise (last 500) : {np.mean(surprise_trace[-500:]):.3f}")
    print("\nEvent log:")
    for s, msg in event_log:
        print(f"  step {s:>5} — {msg}")

    plt.show()


if __name__ == "__main__":
    run()
