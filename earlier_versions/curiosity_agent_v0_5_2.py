"""
curiosity_agent_v0_5_2.py
-------------------------
Refinement of v0.5.1. Fixes the coverage-drive architectural flaw
revealed by the v0.5.1 batch runs.

Version 0.5.2 — changes from v0.5.1:
  * COVERAGE DRIVE REDESIGNED. The flaw in v0.5.1 was that coverage
    paid out only in the single step an uncovered cell was entered —
    one payout per cell, then silence. Other drives pay out
    continuously, so coverage was structurally outcompeted regardless
    of weight. In v0.5.2 the coverage reward has two components:
      - DISCOVERY (retained): a bonus in the step a new cell is entered.
        Same as v0.5.1, weight 6.0.
      - AMBIENT (new): a small constant added at every step, proportional
        to the number of scope cells still uncovered. This is the
        agent's sense of "unfinished business" — present whenever
        obligation remains, silent when discharged.
  * BATCH NOTE: this version should be run through the v0.5.2_batch
    wrapper (to be built next if results look good) to see whether
    the architectural tendency has meaningfully changed.

Run from Terminal with:
    python3 curiosity_agent_v0_5_2.py
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
        self.discovery_weight = 6.0        # one-off: bonus for entering new cell
        self.ambient_weight_per_cell = 0.05  # ambient: per-uncovered-cell pressure
        self.epsilon = 0.1

        self.self_log = []

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
        Two components:
          - DISCOVERY: large one-off reward for entering a cell in scope
            that has not yet been covered.
          - AMBIENT: small continuous pressure proportional to how much
            of the scope remains uncovered. Present at EVERY step while
            any cells are uncovered. Silent once all are covered.
        """
        cell = (state[0], state[1])
        # Discovery component
        discovery = self.discovery_weight if (cell in self.scope and cell not in self.covered) else 0.0
        # Ambient component
        uncovered_count = len(self.scope) - len(self.covered)
        ambient = self.ambient_weight_per_cell * uncovered_count
        return discovery + ambient

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

    def update_model(self, state, action, next_state, error):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)

    def update_values(self, state, action, next_state, intrinsic):
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def record_step(self, step, state, action, next_state,
                    r_novelty, r_progress, r_coverage,
                    error, is_new_coverage, is_mastered):
        drives = {"novelty": r_novelty, "progress": r_progress, "coverage": r_coverage}
        dominant = max(drives, key=drives.get) if max(drives.values()) > 0 else "none"
        self.self_log.append({
            "step": step,
            "cell": (next_state[0], next_state[1]),
            "is_feature": next_state[2],
            "action": action,
            "r_novelty": r_novelty,
            "r_progress": r_progress,
            "r_coverage": r_coverage,
            "dominant_drive": dominant,
            "error": error,
            "is_new_coverage": is_new_coverage,
            "is_mastered_pair": is_mastered,
        })


# --------------------------------------------------------------------------
# 3. INTERPRETATION LAYER (identical to v0.5.1)
# --------------------------------------------------------------------------

def interpret_self(agent, coverage_complete_step):
    log = agent.self_log
    n_steps = len(log)
    cells_seen = len(set(r["cell"] for r in log))
    features = {}
    fired_claims = []
    evidence_log = []

    drive_counts = Counter(r["dominant_drive"] for r in log)
    total = sum(drive_counts.values())
    drive_shares = {k: v / total for k, v in drive_counts.items()}
    features["drive_shares"] = drive_shares
    ranked = sorted(drive_shares.items(), key=lambda kv: -kv[1])
    top_drive, top_share = ranked[0]
    runner_up_share = ranked[1][1] if len(ranked) > 1 else 0
    drive_gap = top_share - runner_up_share
    features["top_drive"] = top_drive

    drive_description = {
        "progress": "the pull of getting better at things I was beginning to understand",
        "coverage": "the pull of reaching and completing the territory I was responsible for",
        "novelty": "the pull of cells I had seen only rarely",
    }

    if drive_gap >= 0.20:
        strength = "strongly"; fire = True
    elif drive_gap >= 0.10:
        strength = "moderately"; fire = True
    elif drive_gap >= 0.05:
        strength = "slightly"; fire = True
    else:
        strength = None; fire = False

    if fire:
        fired_claims.append(
            f"I appear to have been {strength} drawn to {drive_description[top_drive]} "
            f"(dominant in {100*top_share:.0f}% of my choices, against "
            f"{100*runner_up_share:.0f}% for the runner-up)."
        )
        evidence_log.append(f"Drive tendency: FIRED ({strength}) — gap {100*drive_gap:.1f}pp")
    else:
        evidence_log.append(f"Drive tendency: silent — gap only {100*drive_gap:.1f}pp")

    runs = []
    current_cell = log[0]["cell"]
    run_len = 1
    for r in log[1:]:
        if r["cell"] == current_cell:
            run_len += 1
        else:
            runs.append(run_len); current_cell = r["cell"]; run_len = 1
    runs.append(run_len)
    mean_persistence = np.mean(runs)
    features["mean_persistence"] = mean_persistence
    features["max_persistence"] = max(runs)
    if mean_persistence >= 1.5:
        fired_claims.append(
            f"I tended to linger — mean persistence {mean_persistence:.2f} steps per cell, "
            f"above the ~1.0 random-movement baseline."
        )
        evidence_log.append(f"Persistence: FIRED (lingering) — mean {mean_persistence:.2f}")
    elif mean_persistence <= 1.02:
        fired_claims.append(
            f"I almost never lingered — mean persistence {mean_persistence:.2f}, at baseline."
        )
        evidence_log.append(f"Persistence: FIRED (no lingering) — mean {mean_persistence:.2f}")
    else:
        evidence_log.append(f"Persistence: silent — mean {mean_persistence:.2f} is unremarkable")

    cell_visit_counts = Counter(r["cell"] for r in log)
    visits = np.array(list(cell_visit_counts.values()))
    expected_per_cell = n_steps / cells_seen
    cv = np.std(visits) / np.mean(visits)
    features["attention_cv"] = cv
    features["max_over_uniform"] = max(visits) / expected_per_cell
    if cv >= 0.6:
        fired_claims.append(
            f"My attention was very unevenly distributed — some cells received "
            f"{features['max_over_uniform']:.1f}x as many visits as the average."
        )
        evidence_log.append(f"Attention: FIRED (uneven) — CV {cv:.2f}")
    elif cv <= 0.3:
        fired_claims.append(
            f"My attention was distributed fairly evenly across the cells I visited "
            f"(coefficient of variation {cv:.2f})."
        )
        evidence_log.append(f"Attention: FIRED (even) — CV {cv:.2f}")
    else:
        evidence_log.append(f"Attention: silent — CV {cv:.2f} is moderate")

    feature_visits = sum(r["is_feature"] for r in log)
    feature_visit_share = feature_visits / n_steps
    feature_cells_in_scope = sum(1 for c in agent.scope if c in FEATURE_CELLS)
    expected_feature_share = feature_cells_in_scope / len(agent.scope)
    feature_ratio = feature_visit_share / expected_feature_share if expected_feature_share > 0 else 0
    features["feature_ratio"] = feature_ratio
    if feature_ratio >= 1.4:
        fired_claims.append(
            f"Cells with distinct observations drew me disproportionately "
            f"({feature_ratio:.2f}x chance)."
        )
        evidence_log.append(f"Feature affinity: FIRED (drawn) — ratio {feature_ratio:.2f}")
    elif feature_ratio <= 0.7:
        fired_claims.append(
            f"I appear to have under-visited cells with distinct observations "
            f"({feature_ratio:.2f}x chance)."
        )
        evidence_log.append(f"Feature affinity: FIRED (avoidance) — ratio {feature_ratio:.2f}")
    else:
        evidence_log.append(f"Feature affinity: silent — ratio {feature_ratio:.2f} is near chance")

    return features, fired_claims, evidence_log


# --------------------------------------------------------------------------
# 4. RUN
# --------------------------------------------------------------------------

def run():
    world = GridWorld()
    agent = DevelopmentalAgent(world.scope_cells, NUM_STEPS)

    heatmap = np.zeros((GRID_SIZE, GRID_SIZE))
    novelty_trace = []
    progress_trace = []
    coverage_reward_trace = []
    coverage_pct_trace = []
    mastered_count_trace = []

    state = world.observe()
    coverage_complete_step = None

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        action = agent.choose_action(state)
        next_state = world.step(action)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_coverage = agent.coverage_reward(next_state)
        intrinsic = r_novelty + r_progress + r_coverage

        cell = (next_state[0], next_state[1])
        is_new_coverage = (cell in agent.scope) and (cell not in agent.covered)
        pair = (state, action)
        is_mastered = (len(agent.fast_errors[pair]) >= 5 and
                       np.mean(agent.fast_errors[pair]) < 0.15)

        agent.update_model(state, action, next_state, error)
        agent.update_values(state, action, next_state, intrinsic)

        agent.record_step(step, state, action, next_state,
                          r_novelty, r_progress, r_coverage,
                          error, is_new_coverage, is_mastered)

        x, y, _ = next_state
        heatmap[y, x] += 1
        novelty_trace.append(r_novelty)
        progress_trace.append(r_progress)
        coverage_reward_trace.append(r_coverage)
        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))
        mastered_count_trace.append(sum(
            1 for errs in agent.fast_errors.values()
            if len(errs) >= 5 and np.mean(errs) < 0.15
        ))

        if coverage_complete_step is None and len(agent.covered) == len(agent.scope):
            coverage_complete_step = step

        state = next_state

    features, claims, evidence_log = interpret_self(agent, coverage_complete_step)

    def running_mean(x, window=150):
        if len(x) < window: return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    ax = axes[0, 0]
    im = ax.imshow(heatmap, cmap="viridis", origin="upper")
    for (fx, fy) in FEATURE_CELLS:
        ax.plot(fx, fy, marker="*", color="red", markersize=14)
    ax.set_title("Exploration heatmap\n(red stars = feature cells)")
    plt.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[0, 1]
    ax.plot(coverage_pct_trace, linewidth=1.5, color="teal")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8,
                   label=f"coverage complete @ {coverage_complete_step}")
        ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage of scope over time")
    ax.set_xlabel("Step"); ax.set_ylabel("% of scope visited")
    ax.set_ylim(0, 105)

    ax = axes[1, 0]
    ax.plot(progress_trace, linewidth=0.4, alpha=0.35, color="green", label="raw")
    ax.plot(running_mean(progress_trace), linewidth=1.5, color="darkgreen", label="rolling mean")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8)
    ax.set_title("Learning progress over time")
    ax.set_xlabel("Step"); ax.set_ylabel("Progress signal")
    ax.legend(loc="upper right", fontsize=8)

    ax = axes[1, 1]
    ax.plot(mastered_count_trace, linewidth=1.5, color="sienna")
    if coverage_complete_step is not None:
        ax.axvline(coverage_complete_step, color="red", linestyle="--", linewidth=0.8)
    ax.set_title("Mastery accumulation (count)")
    ax.set_xlabel("Step"); ax.set_ylabel("# pairs mastered")

    plt.tight_layout()
    plt.savefig("run_output_v0_5_2.png", dpi=120)

    # Report
    lines = []
    lines.append("=" * 60)
    lines.append("STRUCTURED CHARACTERISATION (v0.5.2)")
    lines.append("=" * 60)
    lines.append(f"Scope covered          : {len(agent.covered)} / {len(agent.scope)}")
    if coverage_complete_step is not None:
        lines.append(f"Coverage completed at  : step {coverage_complete_step}")
    else:
        lines.append(f"Coverage completed at  : NOT COMPLETED")
    lines.append("")
    lines.append("Drive profile:")
    for k, v in sorted(features["drive_shares"].items(), key=lambda kv: -kv[1]):
        lines.append(f"  {k:10s}: {100*v:5.1f}%")
    lines.append("")
    lines.append(f"Mean persistence  : {features['mean_persistence']:.2f}")
    lines.append(f"Attention CV      : {features['attention_cv']:.2f}")
    lines.append(f"Feature visit ratio: {features['feature_ratio']:.2f}x chance")
    lines.append("")
    lines.append("EVIDENCE LOG:")
    for e in evidence_log:
        lines.append(f"  • {e}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("NARRATIVE CHARACTERISATION")
    lines.append("=" * 60)
    lines.append("")
    if not claims:
        lines.append("I find I have little to say about myself with confidence.")
    else:
        for c in claims:
            lines.append(c); lines.append("")

    report_str = "\n".join(lines)
    print("\n" + report_str)
    with open("self_report_v0_5_2.txt", "w") as f:
        f.write(report_str)
    print("\nReport saved to self_report_v0_5_2.txt")
    print("Plots saved to run_output_v0_5_2.png")
    plt.show()


if __name__ == "__main__":
    run()
