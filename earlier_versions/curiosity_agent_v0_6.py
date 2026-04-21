"""
curiosity_agent_v0_6.py
-----------------------
v0.5.4 plus scheduled mid-countdown reflection and rule-based response.

Version 0.6 — changes from v0.5.4:
  * SCHEDULED REFLECTION. The countdown is divided into three 500-step
    windows. At the end of each window (steps countdown_start+500 and
    countdown_start+1000), the agent performs a reflection: it measures
    the gap between its stated policy and its actual behaviour so far,
    and applies a rule-based response.
  * RESPONSE OPTIONS. If the partial gap exceeds threshold, the agent
    chooses one of:
      - STRENGTHEN: increase the pull toward its stated policy
      - ABANDON: switch to the policy that matches its actual behaviour
      - PERSIST: continue without adjustment (only if gap is below threshold)
    The choice is rule-based in v0.6 — it is NOT deliberative reasoning
    by the agent. The agent is applying decision rules we have specified;
    it is not reasoning about itself in any meaningful sense.
  * REFLECTION LOG. Every reflection event is logged and appears in the
    final narrative as a distinct event with its reason.

FRAMING NOTE (important):
  This architecture produces behaviour whose SHAPE resembles human
  metacognition. It does NOT produce metacognition. The agent's
  "reflections" are scheduled function calls. Its "choices" are
  rule-based selections from a predefined set. The first-person
  language in the narrative is a READABILITY convention, not a claim
  about the agent's inner life. The purpose of v0.6 is to explore
  what computational conditions produce reflection-shaped behaviour,
  not to simulate reflection itself.

Run from Terminal with:
    python3 curiosity_agent_v0_6.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque, Counter

# --------------------------------------------------------------------------
# 1. WORLD
# --------------------------------------------------------------------------

GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]
COUNTDOWN_FRACTION = 0.15

# Reflection schedule — these are offsets from countdown_start
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


# --------------------------------------------------------------------------
# 2. AGENT
# --------------------------------------------------------------------------

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

        # Countdown state
        self.countdown_policy = None
        self.original_policy = None  # preserved even if abandoned
        self.countdown_decision_reason = None
        self.top_preferred_at_countdown = []
        self.uncovered_at_countdown = set()
        self.countdown_cells_visited = Counter()
        # Running window for reflection: cells visited since the last reflection
        self.cells_since_last_reflection = Counter()
        self.covered_since_last_reflection = set()
        # Reflection log
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
            reason = (f"Few cells remained uncovered ({uncovered_count}); "
                      f"I chose to spend my remaining time on what drew me.")
        elif uncovered_count >= 25:
            self.countdown_policy = "completion"
            reason = (f"Many cells were still uncovered ({uncovered_count}); "
                      f"I chose to continue the survey I had begun.")
        else:
            if pref_clarity >= 3.0:
                self.countdown_policy = "preference"
                reason = (f"{uncovered_count} cells remained uncovered, but my preferences "
                          f"had become clear enough (ratio {pref_clarity:.1f}) "
                          f"that I chose to return to what drew me.")
            else:
                self.countdown_policy = "completion"
                reason = (f"{uncovered_count} cells remained uncovered and my preferences "
                          f"were not clear enough (ratio {pref_clarity:.1f}) "
                          f"to choose them over the survey.")

        self.original_policy = self.countdown_policy
        self.countdown_decision_reason = reason
        self._apply_policy_weights()

    def _apply_policy_weights(self):
        """Set drive weights according to current policy."""
        if self.countdown_policy == "preference":
            self.preference_weight = 2.0
            self.ambient_base_weight = 0.0
            self.discovery_weight = 0.0
        else:  # completion
            self.preference_weight = 0.0
            self.ambient_base_weight = 0.02
            self.discovery_weight = 8.0

    def measure_partial_gap(self):
        """
        Compute the gap since the LAST reflection (or countdown start),
        not over the whole countdown. This is the signal the agent uses
        to decide its reflection response.
        """
        if self.countdown_policy == "completion":
            newly_covered = self.covered_since_last_reflection & self.uncovered_at_countdown
            target_size = len(self.uncovered_at_countdown - (self.covered - self.covered_since_last_reflection))
            # Simplified: what fraction of still-uncovered cells did we reach in this window?
            still_uncovered_at_start_of_window = self.uncovered_at_countdown - (self.covered - self.covered_since_last_reflection)
            if not still_uncovered_at_start_of_window:
                return 0.0, 0, 0  # Nothing left to cover — perfect alignment
            reached = len(newly_covered)
            # Use window length as denominator for target reachability
            # Rough heuristic: we expect to cover perhaps 2-3 cells in a 500-step window
            expected = min(3, len(still_uncovered_at_start_of_window))
            alignment = min(1.0, reached / expected) if expected > 0 else 1.0
            return 1.0 - alignment, reached, expected
        else:  # preference
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
        """
        Scheduled reflection. Measures partial gap and applies a
        rule-based response. Returns a dict describing what happened.
        """
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
            # Alignment is acceptable — persist without change
            event["response"] = "persist"
            event["reason"] = (f"Gap of {gap:.2f} was below threshold "
                               f"({REFLECTION_GAP_THRESHOLD}); my action was close enough to "
                               f"my stated intention.")
        else:
            # Gap is too large — choose between strengthen and abandon
            # Rule: on the FIRST reflection that exceeds threshold, strengthen.
            # On SUBSEQUENT reflections that still exceed threshold, abandon.
            prior_strengthen = any(e.get("response") == "strengthen"
                                   for e in self.reflection_events)
            if not prior_strengthen:
                # First excess — strengthen the intention
                event["response"] = "strengthen"
                event["reason"] = (f"Gap of {gap:.2f} exceeded threshold. "
                                   f"I strengthened my stated intention.")
                if self.countdown_policy == "preference":
                    self.preference_weight = 4.0  # doubled
                else:
                    self.ambient_base_weight = 0.04  # doubled
                    self.discovery_weight = 16.0     # doubled
            else:
                # Strengthening didn't work — abandon and realign
                new_policy = "completion" if self.countdown_policy == "preference" else "preference"
                event["response"] = "abandon"
                event["reason"] = (f"Gap of {gap:.2f} still exceeded threshold after "
                                   f"strengthening. I abandoned my stated policy "
                                   f"({self.countdown_policy}) and aligned with what my "
                                   f"actions were producing ({new_policy}).")
                self.countdown_policy = new_policy
                self._apply_policy_weights()

        # Reset the window
        self.cells_since_last_reflection = Counter()
        self.covered_since_last_reflection = set()

        self.reflection_events.append(event)
        return event

    def final_gap_measurement(self):
        """Full-countdown gap, as in v0.5.4, using the FINAL policy."""
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
            total = sum(self.countdown_cells_visited.values())
            if total == 0:
                return {"gap": 0.0, "target_size": 0, "achieved": 0}
            in_pref = sum(n for cell, n in self.countdown_cells_visited.items()
                          if cell in top_pref_set)
            return {"gap": 1.0 - (in_pref / total), "target_size": total, "achieved": in_pref}


# --------------------------------------------------------------------------
# 3. RUN
# --------------------------------------------------------------------------

def run():
    world = GridWorld()
    agent = DevelopmentalAgent(world.scope_cells, NUM_STEPS)

    heatmap_all = np.zeros((GRID_SIZE, GRID_SIZE))
    heatmap_countdown = np.zeros((GRID_SIZE, GRID_SIZE))
    coverage_pct_trace = []
    progress_trace = []
    preference_weight_trace = []
    ambient_weight_trace = []

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

        x, y, _ = next_state
        heatmap_all[y, x] += 1
        if step >= agent.countdown_start:
            heatmap_countdown[y, x] += 1

        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))
        progress_trace.append(r_progress)
        preference_weight_trace.append(agent.preference_weight)
        ambient_weight_trace.append(agent.ambient_weight_now())

        state = next_state

    final_gap = agent.final_gap_measurement()

    # ---------------- PLOTS ----------------
    def running_mean(x, window=150):
        if len(x) < window: return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window

    fig, axes = plt.subplots(3, 2, figsize=(13, 13))

    ax = axes[0, 0]
    im = ax.imshow(heatmap_all, cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title("Full-life heatmap")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[0, 1]
    im = ax.imshow(heatmap_countdown, cmap="plasma", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="white", markersize=14)
    ax.set_title(f"Countdown-only heatmap (last {int(100*COUNTDOWN_FRACTION)}%)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1, 0]
    ax.plot(coverage_pct_trace, linewidth=1.5, color="teal")
    ax.axvline(agent.countdown_start, color="orange", linestyle="--", linewidth=1.0,
               label="countdown")
    for i, rs in enumerate(agent.reflection_steps):
        ax.axvline(rs, color="purple", linestyle=":", linewidth=0.9,
                   label=f"reflection {i+1}" if i == 0 else None)
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage over time")
    ax.set_xlabel("Step"); ax.set_ylabel("% visited")
    ax.set_ylim(0, 105)

    ax = axes[1, 1]
    ax.plot(preference_weight_trace, linewidth=1.2, color="darkgreen", label="preference weight")
    ax.plot(ambient_weight_trace, linewidth=1.2, color="darkblue", label="ambient weight")
    ax.axvline(agent.countdown_start, color="orange", linestyle="--", linewidth=1.0)
    for rs in agent.reflection_steps:
        ax.axvline(rs, color="purple", linestyle=":", linewidth=0.9)
    ax.set_title("Drive weights over time\n(shifts show reflection responses)")
    ax.set_xlabel("Step"); ax.set_ylabel("weight")
    ax.legend(fontsize=8)

    ax = axes[2, 0]
    ax.plot(progress_trace, linewidth=0.4, alpha=0.35, color="green")
    ax.plot(running_mean(progress_trace), linewidth=1.5, color="darkgreen")
    ax.axvline(agent.countdown_start, color="orange", linestyle="--", linewidth=1.0)
    for rs in agent.reflection_steps:
        ax.axvline(rs, color="purple", linestyle=":", linewidth=0.9)
    ax.set_title("Learning progress")
    ax.set_xlabel("Step"); ax.set_ylabel("progress")

    ax = axes[2, 1]
    # Blank — used for reflection annotation summary
    ax.axis("off")
    annotation = ["Reflection events:", ""]
    for e in agent.reflection_events:
        annotation.append(f"Step {e['step']}: {e['response'].upper()}")
        annotation.append(f"  gap={e['gap']:.2f}, policy_before={e['policy_before']}")
        annotation.append("")
    ax.text(0.02, 0.98, "\n".join(annotation), transform=ax.transAxes,
            fontsize=9, verticalalignment="top", family="monospace")

    plt.tight_layout()
    plt.savefig("run_output_v0_6.png", dpi=120)

    # ---------------- REPORT ----------------
    lines = []
    lines.append("=" * 68)
    lines.append("STRUCTURED CHARACTERISATION (v0.6)")
    lines.append("=" * 68)
    lines.append(f"Life length              : {NUM_STEPS} steps")
    lines.append(f"Countdown began at       : step {agent.countdown_start}")
    lines.append(f"Coverage at countdown    : {coverage_at_countdown_start}/100")
    lines.append(f"Coverage at end          : {len(agent.covered)}/100")
    lines.append("")
    lines.append(f"Original policy          : {agent.original_policy.upper()}")
    lines.append(f"Final policy             : {agent.countdown_policy.upper()}")
    lines.append(f"Original reason          : {agent.countdown_decision_reason}")
    lines.append("")
    lines.append("--- REFLECTION EVENTS ---")
    for i, e in enumerate(agent.reflection_events, 1):
        lines.append(f"Reflection {i} at step {e['step']}:")
        lines.append(f"  Response: {e['response'].upper()}")
        lines.append(f"  Gap at reflection: {e['gap']:.2f}")
        lines.append(f"  Reason: {e['reason']}")
        lines.append("")
    lines.append("--- FINAL GAP (full countdown, final policy) ---")
    lines.append(f"Gap: {final_gap['gap']:.2f}")
    lines.append("")
    lines.append("=" * 68)
    lines.append("NARRATIVE")
    lines.append("=" * 68)
    lines.append("")
    lines.append(f"At the start of my countdown, {agent.countdown_decision_reason.lower()}")
    lines.append("")
    for i, e in enumerate(agent.reflection_events, 1):
        lines.append(f"At my {['first', 'second'][i-1]} reflection, {e['reason'].lower()}")
        lines.append("")
    if agent.countdown_policy != agent.original_policy:
        lines.append(f"I ended my life having abandoned my original intention. "
                     f"What I did reflected my actual behaviour, not my stated purpose.")
    else:
        if final_gap["gap"] <= 0.3:
            lines.append(f"I held to my original intention and largely enacted it "
                         f"(final gap {final_gap['gap']:.2f}).")
        else:
            lines.append(f"I held to my original intention, but a gap remained between "
                         f"what I said I would do and what I did "
                         f"(final gap {final_gap['gap']:.2f}). "
                         f"My strengthening of intention was insufficient.")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open("self_report_v0_6.txt", "w") as f:
        f.write(report_str)
    print("\nReport saved to self_report_v0_6.txt")
    print("Plots saved to run_output_v0_6.png")
    plt.show()


if __name__ == "__main__":
    run()
