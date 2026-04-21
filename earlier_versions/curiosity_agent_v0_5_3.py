"""
curiosity_agent_v0_5_3.py
-------------------------
Time-structured developmental agent with a countdown window and
heuristic phase commitment.

Version 0.5.3 — changes from v0.5.2:
  * TIME-DECAYING COVERAGE. The ambient coverage pressure now decays
    linearly from full strength at step 0 to zero at the midpoint of
    the run. The agent is shaped by time, not by remaining work.
  * REGION PREFERENCE TRACKING. Throughout its life, the agent
    accumulates a per-cell preference signal based on cumulative
    learning progress in that cell. By late in the run it has an
    implicit ranking of "which regions rewarded me most".
  * COUNTDOWN WINDOW. In the final 15% of the run, the agent enters
    a countdown phase. At the start of this phase, it evaluates its
    situation and commits to one of two policies for the remainder:
      - COMPLETION policy: weight coverage drive high, chase remaining
        uncovered cells.
      - PREFERENCE policy: weight preference signal high, return to
        the regions it found most rewarding.
    The commitment is binary and sticky for the countdown — one
    decision, held to the end of the run.
  * CHOICE HEURISTIC. The agent's countdown decision follows a simple
    rule: if outstanding coverage is small and preference is strong,
    choose preference. If outstanding coverage is large, choose
    completion. The logic is deliberately heuristic; deliberative
    self-evaluation is held for v0.6.
  * VISIBLE CHOICE. The self-report explicitly records what the agent
    chose during countdown, why, and what happened.

This is a staged step toward learner-centred architecture. v0.5.3
introduces choice as a behavioural phase. v0.6 will make the choice
informed by reasoning about expected reward.

Run from Terminal with:
    python3 curiosity_agent_v0_5_3.py
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

# Countdown configuration
COUNTDOWN_FRACTION = 0.15  # last 15% of life is countdown window

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

        # Hyperparameters
        self.learning_rate = 0.1
        self.novelty_weight = 0.25
        self.progress_weight = 1.2
        self.discovery_weight = 6.0
        self.ambient_base_weight = 0.005  # ambient at step 0 (decays to 0)
        self.preference_weight = 0.0      # zero during survey; set during countdown
        self.epsilon = 0.1

        # Preference tracking: cumulative learning progress per cell
        self.cell_preference = defaultdict(float)

        # Countdown state
        self.countdown_policy = None   # "completion" or "preference", set at countdown start
        self.countdown_decision_reason = None

        self.self_log = []

    def time_fraction_remaining(self):
        return max(0.0, 1.0 - (self.steps_taken / self.total_steps))

    def ambient_weight_now(self):
        """
        Ambient coverage pressure decays linearly from full strength at
        step 0 to zero at the midpoint of the run. After the midpoint,
        ambient is zero.
        """
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
        """
        Reward for being in a cell with high accumulated preference.
        This is silent during survey and only activates during the
        countdown window under the 'preference' policy.
        """
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
        # Accumulate preference = sum of learning progress accrued in this cell
        self.cell_preference[cell] += r_progress

    def update_values(self, state, action, next_state, intrinsic):
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def enter_countdown(self):
        """
        Called once, at the first step of the countdown window.
        The agent evaluates its situation and commits to a policy
        for the remainder of the run.
        """
        uncovered_count = len(self.scope) - len(self.covered)
        # Sort cells by preference
        prefs = sorted(self.cell_preference.values(), reverse=True)
        top_pref = prefs[0] if prefs else 0.0
        # Ratio of top preference to the mean is a measure of how "clear" the
        # agent's preferences are. A strong clear preference has high ratio.
        mean_pref = np.mean(prefs) if prefs else 1e-6
        pref_clarity = top_pref / (mean_pref + 1e-6)

        # Heuristic choice:
        #   Small outstanding coverage (<=10) -> preference
        #   Large outstanding coverage (>=25) -> completion
        #   In between -> decided by preference clarity
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
            # Middle range — let preference clarity decide
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

        # Apply the policy by adjusting drive weights
        if self.countdown_policy == "preference":
            # Preference dominant, coverage silent
            self.preference_weight = 2.0
            self.ambient_base_weight = 0.0
            self.discovery_weight = 0.0
            # Keep novelty and progress at normal levels
        else:  # completion
            # Coverage dominant, preference silent
            self.preference_weight = 0.0
            self.ambient_base_weight = 0.02  # reactivated strongly
            self.discovery_weight = 8.0      # strong discovery payout
            # Ensure ambient decay is reset — during countdown ambient is
            # constant rather than decaying
            # (We achieve this by overriding ambient_weight_now below)
            self._countdown_ambient_override = True

    def ambient_weight_now(self):
        """
        Overridden for countdown: if in completion policy, ambient is
        constant at ambient_base_weight; otherwise linear decay to midpoint.
        """
        if self.countdown_policy == "completion":
            return self.ambient_base_weight
        t = self.steps_taken / self.total_steps
        if t >= 0.5:
            return 0.0
        return self.ambient_base_weight * (1.0 - 2.0 * t)

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
# 3. INTERPRETATION LAYER
# --------------------------------------------------------------------------

def interpret_self(agent, coverage_complete_step):
    log = agent.self_log
    n_steps = len(log)

    # Main-phase (pre-countdown) analysis
    main_log = [r for r in log if r["phase"] == "main"]
    countdown_log = [r for r in log if r["phase"] == "countdown"]

    # Overall drive shares
    drive_counts = Counter(r["dominant_drive"] for r in log)
    total = sum(drive_counts.values())
    drive_shares = {k: v / total for k, v in drive_counts.items()}
    for k in ["novelty", "progress", "coverage", "preference"]:
        drive_shares.setdefault(k, 0.0)

    # Main-phase drive shares
    main_drive_counts = Counter(r["dominant_drive"] for r in main_log)
    main_total = sum(main_drive_counts.values())
    main_drive_shares = {k: v / main_total for k, v in main_drive_counts.items()}
    for k in ["novelty", "progress", "coverage"]:
        main_drive_shares.setdefault(k, 0.0)

    # Countdown phase analysis
    countdown_drive_counts = Counter(r["dominant_drive"] for r in countdown_log)
    cd_total = sum(countdown_drive_counts.values())
    countdown_drive_shares = {k: v / cd_total for k, v in countdown_drive_counts.items()}
    for k in ["novelty", "progress", "coverage", "preference"]:
        countdown_drive_shares.setdefault(k, 0.0)

    # Top preferred cells (by accumulated preference at end of main phase)
    top_preferred = sorted(agent.cell_preference.items(),
                           key=lambda kv: -kv[1])[:5]

    # Countdown behaviour: did the agent's cell distribution during countdown
    # match its commitment?
    countdown_cells = Counter(r["cell"] for r in countdown_log)
    countdown_top_cells = countdown_cells.most_common(5)

    return {
        "drive_shares": drive_shares,
        "main_drive_shares": main_drive_shares,
        "countdown_drive_shares": countdown_drive_shares,
        "top_preferred": top_preferred,
        "countdown_top_cells": countdown_top_cells,
        "coverage_at_countdown_start": None,  # filled in from run data
    }


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

        # Enter countdown once we cross the boundary
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

    results = interpret_self(agent, coverage_complete_step)
    results["coverage_at_countdown_start"] = coverage_at_countdown_start

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
    plt.savefig("run_output_v0_5_3.png", dpi=120)

    # ---------------- REPORT ----------------
    lines = []
    lines.append("=" * 65)
    lines.append("STRUCTURED CHARACTERISATION (v0.5.3)")
    lines.append("=" * 65)
    lines.append(f"Life length              : {NUM_STEPS} steps")
    lines.append(f"Countdown began at       : step {agent.countdown_start}")
    lines.append(f"Coverage at countdown    : {coverage_at_countdown_start}/100")
    lines.append(f"Coverage at end          : {len(agent.covered)}/100")
    if coverage_complete_step is not None:
        lines.append(f"Coverage completed at    : step {coverage_complete_step}")
    else:
        lines.append(f"Coverage completed at    : NOT COMPLETED")
    lines.append("")
    lines.append(f"Countdown policy chosen  : {agent.countdown_policy.upper()}")
    lines.append(f"Reason                   : {agent.countdown_decision_reason}")
    lines.append("")
    lines.append("Overall drive profile (all steps):")
    for k, v in sorted(results["drive_shares"].items(), key=lambda kv: -kv[1]):
        if v > 0:
            lines.append(f"  {k:12s}: {100*v:5.1f}%")
    lines.append("")
    lines.append("Main-phase drive profile (before countdown):")
    for k, v in sorted(results["main_drive_shares"].items(), key=lambda kv: -kv[1]):
        if v > 0:
            lines.append(f"  {k:12s}: {100*v:5.1f}%")
    lines.append("")
    lines.append("Countdown-phase drive profile:")
    for k, v in sorted(results["countdown_drive_shares"].items(), key=lambda kv: -kv[1]):
        if v > 0:
            lines.append(f"  {k:12s}: {100*v:5.1f}%")
    lines.append("")
    lines.append("Top 5 preferred cells (by accumulated learning progress):")
    for cell, pref in results["top_preferred"]:
        marker = " (feature)" if cell in FEATURE_CELLS else ""
        lines.append(f"  {cell}: pref = {pref:.2f}{marker}")
    lines.append("")
    lines.append("Top 5 most-visited cells during countdown:")
    for cell, n in results["countdown_top_cells"]:
        marker = " (feature)" if cell in FEATURE_CELLS else ""
        in_top_prefs = any(c == cell for c, _ in results["top_preferred"])
        pref_marker = " [preferred region]" if in_top_prefs else ""
        lines.append(f"  {cell}: {n} visits{marker}{pref_marker}")
    lines.append("")
    lines.append("=" * 65)
    lines.append("NARRATIVE")
    lines.append("=" * 65)
    lines.append("")
    lines.append(agent.countdown_decision_reason)
    lines.append("")
    if agent.countdown_policy == "preference":
        pref_cells_visited_in_countdown = sum(
            n for cell, n in results["countdown_top_cells"]
            if any(c == cell for c, _ in results["top_preferred"])
        )
        cd_total = sum(n for _, n in results["countdown_top_cells"]) or 1
        frac = pref_cells_visited_in_countdown / cd_total
        lines.append(f"During the countdown, {100*frac:.0f}% of my movements within "
                     f"my top-5 visited cells were to regions I had found rewarding "
                     f"during my main life.")
    else:
        cells_newly_covered = len(agent.covered) - coverage_at_countdown_start
        lines.append(f"During the countdown, I reached {cells_newly_covered} additional "
                     f"cells that I had not previously visited.")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open("self_report_v0_5_3.txt", "w") as f:
        f.write(report_str)
    print("\nReport saved to self_report_v0_5_3.txt")
    print("Plots saved to run_output_v0_5_3.png")
    plt.show()


if __name__ == "__main__":
    run()
