"""
curiosity_agent_v0_5_4.py
-------------------------
v0.5.3 plus intention-action gap detection.

Version 0.5.4 — changes from v0.5.3:
  * INTENTION-ACTION GAP DETECTION. At the end of the countdown, the
    agent computes how well its actual behaviour matched its stated
    policy.
      - If the chosen policy was COMPLETION: the gap is 1 minus the
        fraction of remaining uncovered cells that were actually reached
        during countdown. Perfect alignment = covered all that remained;
        total misalignment = covered none.
      - If the chosen policy was PREFERENCE: the gap is 1 minus the
        fraction of countdown steps spent in cells that were in the
        agent's top preferences at countdown-start. Perfect alignment =
        every countdown step in preferred cells; total misalignment =
        none of them.
    The gap is recorded; no behavioural response is produced.
  * GAP NAMING. The narrative now includes explicit first-person
    recognition of the gap (or the absence of one).
  * NOTABLY ABSENT: any mechanism that uses the gap to change
    behaviour. The agent sees the gap. It does not act on it. This is
    deliberate. v0.6 will address what, if anything, the agent should
    do with this knowledge.

The purpose of this version is to establish that the gap exists as a
detectable, describable property of the agent's life, before deciding
how to respond to it.

Run from Terminal with:
    python3 curiosity_agent_v0_5_4.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque, Counter

# --------------------------------------------------------------------------
# 1. THE WORLD
# --------------------------------------------------------------------------

GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]
COUNTDOWN_FRACTION = 0.15

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
# 2. THE AGENT
# --------------------------------------------------------------------------

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

        # Countdown state
        self.countdown_policy = None
        self.countdown_decision_reason = None
        # --- NEW IN v0.5.4 ---
        self.top_preferred_at_countdown = []    # captured at countdown start
        self.uncovered_at_countdown = set()     # captured at countdown start
        self.countdown_cells_visited = Counter()

        self.self_log = []

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
        # Track countdown-phase visits for later gap analysis
        if self.steps_taken >= self.countdown_start:
            self.countdown_cells_visited[cell] += 1

    def update_values(self, state, action, next_state, intrinsic):
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def enter_countdown(self):
        uncovered_count = len(self.scope) - len(self.covered)
        self.uncovered_at_countdown = {
            c for c in self.scope if c not in self.covered
        }

        prefs = sorted(self.cell_preference.items(),
                       key=lambda kv: -kv[1])
        # Top preferred cells at countdown start — used for both policy
        # choice and later gap analysis
        self.top_preferred_at_countdown = [c for c, _ in prefs[:10]]
        pref_values = [v for _, v in prefs] if prefs else [0.0]
        top_pref = pref_values[0] if pref_values else 0.0
        mean_pref = np.mean(pref_values) if pref_values else 1e-6
        pref_clarity = top_pref / (mean_pref + 1e-6)

        if uncovered_count <= 10:
            self.countdown_policy = "preference"
            self.countdown_decision_reason = (
                f"Few cells remained uncovered ({uncovered_count}); "
                f"I chose to spend my remaining time on what drew me."
            )
        elif uncovered_count >= 25:
            self.countdown_policy = "completion"
            self.countdown_decision_reason = (
                f"Many cells were still uncovered ({uncovered_count}); "
                f"I chose to continue the survey I had begun."
            )
        else:
            if pref_clarity >= 3.0:
                self.countdown_policy = "preference"
                self.countdown_decision_reason = (
                    f"{uncovered_count} cells remained uncovered, but my preferences "
                    f"had become clear enough (ratio {pref_clarity:.1f}) "
                    f"that I chose to return to what drew me."
                )
            else:
                self.countdown_policy = "completion"
                self.countdown_decision_reason = (
                    f"{uncovered_count} cells remained uncovered and my preferences "
                    f"were not clear enough (ratio {pref_clarity:.1f}) "
                    f"to choose them over the survey."
                )

        if self.countdown_policy == "preference":
            self.preference_weight = 2.0
            self.ambient_base_weight = 0.0
            self.discovery_weight = 0.0
        else:
            self.preference_weight = 0.0
            self.ambient_base_weight = 0.02
            self.discovery_weight = 8.0

    def measure_intention_action_gap(self):
        """
        Compute how well the agent's actual countdown behaviour matched
        its stated policy. Returns a dict containing the gap value (0 =
        perfect alignment, 1 = total misalignment) along with the raw
        numbers used to compute it.
        """
        if self.countdown_policy == "completion":
            # Alignment = fraction of uncovered-at-countdown cells that
            # were actually reached
            reached_in_countdown = self.uncovered_at_countdown & self.covered
            target_size = len(self.uncovered_at_countdown)
            if target_size == 0:
                # No cells were uncovered at countdown start — policy was
                # effectively moot
                return {
                    "gap": 0.0,
                    "target_size": 0,
                    "achieved": 0,
                    "note": "No uncovered cells remained at countdown start.",
                }
            reached = len(reached_in_countdown)
            alignment = reached / target_size
            return {
                "gap": 1.0 - alignment,
                "target_size": target_size,
                "achieved": reached,
                "note": f"Policy was to complete survey; reached "
                        f"{reached}/{target_size} of remaining cells.",
            }
        else:  # preference
            top_pref_set = set(self.top_preferred_at_countdown[:5])
            total_countdown_visits = sum(self.countdown_cells_visited.values())
            if total_countdown_visits == 0:
                return {
                    "gap": 0.0,
                    "target_size": 0,
                    "achieved": 0,
                    "note": "No countdown visits recorded.",
                }
            visits_in_preferred = sum(
                n for cell, n in self.countdown_cells_visited.items()
                if cell in top_pref_set
            )
            alignment = visits_in_preferred / total_countdown_visits
            return {
                "gap": 1.0 - alignment,
                "target_size": total_countdown_visits,
                "achieved": visits_in_preferred,
                "note": f"Policy was to return to preferred regions; "
                        f"{visits_in_preferred}/{total_countdown_visits} "
                        f"({100*alignment:.0f}%) of countdown steps were in my "
                        f"top-5 preferred cells.",
            }

    def record_step(self, step, state, action, next_state,
                    r_novelty, r_progress, r_coverage, r_preference,
                    error):
        drives = {"novelty": r_novelty, "progress": r_progress,
                  "coverage": r_coverage, "preference": r_preference}
        dominant = max(drives, key=drives.get) if max(drives.values()) > 0 else "none"
        self.self_log.append({
            "step": step,
            "phase": "countdown" if step >= self.countdown_start else "main",
            "cell": (next_state[0], next_state[1]),
            "is_feature": next_state[2],
            "action": action,
            "r_novelty": r_novelty,
            "r_progress": r_progress,
            "r_coverage": r_coverage,
            "r_preference": r_preference,
            "dominant_drive": dominant,
            "error": error,
        })


# --------------------------------------------------------------------------
# 3. GAP NARRATIVE
# --------------------------------------------------------------------------

def name_the_gap(policy, gap_info):
    """
    Produce a first-person description of the intention-action gap, or
    its absence. Scale of language matches the size of the gap.
    """
    gap = gap_info["gap"]
    if gap_info["target_size"] == 0:
        return ("My policy was moot — there was nothing left to do under it. "
                "I cannot tell from this life whether I would have followed it.")

    if policy == "completion":
        if gap <= 0.15:
            return (f"I stated I would complete the survey, and I largely did. "
                    f"{gap_info['note']} "
                    f"My intention and my action were close to aligned.")
        elif gap <= 0.5:
            return (f"I stated I would complete the survey, but I managed only part of it. "
                    f"{gap_info['note']} "
                    f"There is a gap between what I said I would do and what I did, "
                    f"though not a total one.")
        else:
            return (f"I stated I would complete the survey. I did not. "
                    f"{gap_info['note']} "
                    f"My action did not follow from my stated intention. "
                    f"I cannot, from what I have recorded of myself, explain "
                    f"why this was so.")
    else:  # preference
        if gap <= 0.15:
            return (f"I stated I would spend my remaining time in the regions I had "
                    f"come to prefer, and I did. "
                    f"{gap_info['note']} "
                    f"My intention and my action were closely aligned.")
        elif gap <= 0.5:
            return (f"I stated I would spend my remaining time in preferred regions, "
                    f"and partially I did. "
                    f"{gap_info['note']} "
                    f"A portion of my countdown was spent elsewhere — "
                    f"I cannot say from what I have recorded why.")
        else:
            return (f"I stated I would spend my remaining time on what drew me. "
                    f"I did not. "
                    f"{gap_info['note']} "
                    f"Whatever my body did during the countdown was not what I said "
                    f"I would do. I cannot, from what I have recorded of myself, "
                    f"explain this gap.")


# --------------------------------------------------------------------------
# 4. RUN
# --------------------------------------------------------------------------

def run():
    world = GridWorld()
    agent = DevelopmentalAgent(world.scope_cells, NUM_STEPS)

    heatmap_all = np.zeros((GRID_SIZE, GRID_SIZE))
    heatmap_countdown = np.zeros((GRID_SIZE, GRID_SIZE))
    novelty_trace = []
    progress_trace = []
    coverage_reward_trace = []
    preference_reward_trace = []
    coverage_pct_trace = []
    mastered_count_trace = []
    ambient_weight_trace = []

    state = world.observe()
    coverage_complete_step = None
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
        agent.record_step(step, state, action, next_state,
                          r_novelty, r_progress, r_coverage, r_preference, error)

        x, y, _ = next_state
        heatmap_all[y, x] += 1
        if step >= agent.countdown_start:
            heatmap_countdown[y, x] += 1

        novelty_trace.append(r_novelty)
        progress_trace.append(r_progress)
        coverage_reward_trace.append(r_coverage)
        preference_reward_trace.append(r_preference)
        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))
        mastered_count_trace.append(sum(
            1 for errs in agent.fast_errors.values()
            if len(errs) >= 5 and np.mean(errs) < 0.15
        ))
        ambient_weight_trace.append(agent.ambient_weight_now())

        if coverage_complete_step is None and len(agent.covered) == len(agent.scope):
            coverage_complete_step = step

        state = next_state

    # Gap measurement
    gap_info = agent.measure_intention_action_gap()
    gap_narrative = name_the_gap(agent.countdown_policy, gap_info)

    # Plots
    def running_mean(x, window=150):
        if len(x) < window: return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window

    fig, axes = plt.subplots(3, 2, figsize=(13, 13))

    ax = axes[0, 0]
    im = ax.imshow(heatmap_all, cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title("Full-life heatmap\n(red stars = feature cells)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[0, 1]
    im = ax.imshow(heatmap_countdown, cmap="plasma", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="white", markersize=14)
    ax.set_title(f"Countdown-only heatmap\n(last {int(100*COUNTDOWN_FRACTION)}% of life)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1, 0]
    ax.plot(coverage_pct_trace, linewidth=1.5, color="teal")
    ax.axvline(agent.countdown_start, color="orange", linestyle="--", linewidth=1.0,
               label=f"countdown @ {agent.countdown_start}")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8,
                   label=f"coverage complete @ {coverage_complete_step}")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage over time")
    ax.set_xlabel("Step"); ax.set_ylabel("% of scope visited")
    ax.set_ylim(0, 105)

    ax = axes[1, 1]
    ax.plot(ambient_weight_trace, linewidth=1.2, color="darkblue", label="ambient weight")
    ax.axvline(agent.countdown_start, color="orange", linestyle="--", linewidth=1.0)
    ax.set_title("Ambient coverage weight over time")
    ax.set_xlabel("Step"); ax.set_ylabel("ambient weight per cell")
    ax.legend(fontsize=8)

    ax = axes[2, 0]
    ax.plot(progress_trace, linewidth=0.4, alpha=0.35, color="green", label="raw")
    ax.plot(running_mean(progress_trace), linewidth=1.5, color="darkgreen", label="mean")
    ax.axvline(agent.countdown_start, color="orange", linestyle="--", linewidth=1.0)
    ax.set_title("Learning progress over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Progress signal")
    ax.legend(loc="upper right", fontsize=8)

    ax = axes[2, 1]
    ax.plot(mastered_count_trace, linewidth=1.5, color="sienna")
    ax.axvline(agent.countdown_start, color="orange", linestyle="--", linewidth=1.0)
    ax.set_title("Mastery accumulation")
    ax.set_xlabel("Step"); ax.set_ylabel("# pairs mastered")

    plt.tight_layout()
    plt.savefig("run_output_v0_5_4.png", dpi=120)

    # Report
    lines = []
    lines.append("=" * 65)
    lines.append("STRUCTURED CHARACTERISATION (v0.5.4)")
    lines.append("=" * 65)
    lines.append(f"Life length              : {NUM_STEPS} steps")
    lines.append(f"Countdown began at       : step {agent.countdown_start}")
    lines.append(f"Coverage at countdown    : {coverage_at_countdown_start}/100")
    lines.append(f"Coverage at end          : {len(agent.covered)}/100")
    lines.append("")
    lines.append(f"Countdown policy chosen  : {agent.countdown_policy.upper()}")
    lines.append(f"Reason                   : {agent.countdown_decision_reason}")
    lines.append("")
    lines.append("--- INTENTION-ACTION GAP ---")
    lines.append(f"Gap value                : {gap_info['gap']:.2f}  "
                 f"(0 = perfect alignment, 1 = total misalignment)")
    lines.append(f"Measurement              : {gap_info['note']}")
    lines.append("")
    lines.append("Top preferred cells at countdown start:")
    for cell in agent.top_preferred_at_countdown[:5]:
        marker = " (feature)" if cell in FEATURE_CELLS else ""
        lines.append(f"  {cell}: pref = {agent.cell_preference[cell]:.2f}{marker}")
    lines.append("")
    lines.append("Top 5 most-visited cells during countdown:")
    top_countdown = agent.countdown_cells_visited.most_common(5)
    pref_set = set(agent.top_preferred_at_countdown[:5])
    for cell, n in top_countdown:
        marker = " (feature)" if cell in FEATURE_CELLS else ""
        in_prefs = " [preferred]" if cell in pref_set else ""
        was_uncovered = " [was uncovered at countdown]" if cell in agent.uncovered_at_countdown else ""
        lines.append(f"  {cell}: {n} visits{marker}{in_prefs}{was_uncovered}")
    lines.append("")
    lines.append("=" * 65)
    lines.append("NARRATIVE")
    lines.append("=" * 65)
    lines.append("")
    lines.append(agent.countdown_decision_reason)
    lines.append("")
    lines.append(gap_narrative)

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open("self_report_v0_5_4.txt", "w") as f:
        f.write(report_str)
    print("\nReport saved to self_report_v0_5_4.txt")
    print("Plots saved to run_output_v0_5_4.png")
    plt.show()


if __name__ == "__main__":
    run()
