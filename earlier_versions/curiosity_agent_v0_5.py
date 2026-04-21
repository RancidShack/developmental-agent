"""
curiosity_agent_v0_5.py
-----------------------
A developmental curiosity agent that keeps a self-log and produces
a self-characterisation at the end of its life.

Version 0.5 — changes from v0.4.1:
  * SELF-LOG. At every step the agent records a compact psychological
    record: which drive dominated the choice, the prediction error, the
    observed learning progress, whether the move entered a new scope
    cell, whether the move achieved mastery on that (state, action) pair.
  * INTERPRETATION LAYER. At end of run the agent computes features
    from the log — drive tendency, region affinity (post-coverage),
    persistence profile, abandonment pattern, mastery preference — and
    turns them into first-person descriptive claims about itself.
  * REPORT. The agent produces both a structured characterisation
    (machine-style) and a narrative paragraph (first-person, tentative
    voice). Both draw from the same underlying features. The narrative
    does not invent — every claim traces back to a computed number.

IMPORTANT DESIGN NOTE:
  The self-representation in v0.5 is OBSERVATIONAL ONLY. It is
  computed from the agent's log but has NO effect on the agent's
  choices during the run. Behaviour in v0.5 is identical to v0.4.1;
  the only difference is that the agent's life is being recorded
  and interpreted. Self-representation becomes operational in v0.6.

Run from Terminal with:
    python3 curiosity_agent_v0_5.py
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

        # Hyperparameters — held constant from v0.4.1
        self.learning_rate = 0.1
        self.novelty_weight = 0.25
        self.progress_weight = 1.2
        self.coverage_weight = 6.0
        self.epsilon = 0.1

        # --- SELF-LOG ---
        # One compact record per step. Kept as a list of dicts rather than
        # separate traces so the interpretation layer can query richly.
        self.self_log = []

    def time_fraction_remaining(self):
        return max(0.0, 1.0 - (self.steps_taken / self.total_steps))

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.num_actions), "exploration"
        values = [self.q_values[(state, a)] for a in range(self.num_actions)]
        max_v = max(values)
        best = [a for a, v in enumerate(values) if v == max_v]
        return np.random.choice(best), "exploitation"

    def novelty_reward(self, state):
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def coverage_reward(self, state):
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
        """Write one compact record to the self-log."""
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
# 3. THE INTERPRETATION LAYER
# --------------------------------------------------------------------------

def interpret_self(agent, coverage_complete_step):
    """
    Compute features from the self-log and return both a structured
    characterisation and a first-person narrative.

    Every claim traces back to a computed number. Claims are marked
    with a confidence level based on the strength of the evidence.
    """
    log = agent.self_log
    n_steps = len(log)

    features = {}

    # --- Drive tendency: which drive dominated most often? ---
    drive_counts = Counter(r["dominant_drive"] for r in log)
    total = sum(drive_counts.values())
    drive_shares = {k: v / total for k, v in drive_counts.items()}
    features["drive_shares"] = drive_shares
    # Find the strongest drive, and by how much it beats the runner-up
    ranked = sorted(drive_shares.items(), key=lambda kv: -kv[1])
    top_drive = ranked[0][0]
    top_share = ranked[0][1]
    runner_up_share = ranked[1][1] if len(ranked) > 1 else 0
    drive_gap = top_share - runner_up_share
    features["top_drive"] = top_drive
    features["drive_gap"] = drive_gap

    # --- Region affinity (post-coverage only) ---
    # After obligation is discharged, where did the agent CHOOSE to spend time?
    if coverage_complete_step is not None and coverage_complete_step < n_steps - 200:
        post = log[coverage_complete_step:]
        cell_counts = Counter(r["cell"] for r in post)
        most_visited_post = cell_counts.most_common(3)
        post_total = sum(cell_counts.values())
        top_cell, top_n = most_visited_post[0]
        top_cell_share = top_n / post_total
        expected_share = 1 / len(agent.scope)
        features["post_coverage_available"] = True
        features["top_cell_post"] = top_cell
        features["top_cell_share"] = top_cell_share
        features["top_cell_vs_uniform"] = top_cell_share / expected_share
        features["top_3_cells_post"] = most_visited_post
        features["top_cell_is_feature"] = top_cell in FEATURE_CELLS
    else:
        features["post_coverage_available"] = False

    # --- Persistence profile: mean consecutive steps in same cell ---
    runs = []
    current_cell = log[0]["cell"]
    run_len = 1
    for r in log[1:]:
        if r["cell"] == current_cell:
            run_len += 1
        else:
            runs.append(run_len)
            current_cell = r["cell"]
            run_len = 1
    runs.append(run_len)
    features["mean_persistence"] = np.mean(runs)
    features["max_persistence"] = max(runs)

    # --- Abandonment pattern ---
    cell_visit_counts = Counter(r["cell"] for r in log)
    visited_once = sum(1 for v in cell_visit_counts.values() if v == 1)
    revisited = sum(1 for v in cell_visit_counts.values() if v > 5)
    features["visited_once"] = visited_once
    features["revisited_often"] = revisited
    features["total_cells_seen"] = len(cell_visit_counts)

    # --- Mastery preference ---
    # Did the agent linger on cells where progress was steady, or sporadic?
    # Cells where at least 30% of visits had dominant_drive == "progress"
    progress_driven_cells = 0
    total_with_data = 0
    cell_logs = defaultdict(list)
    for r in log:
        cell_logs[r["cell"]].append(r)
    for cell, rs in cell_logs.items():
        if len(rs) >= 10:
            total_with_data += 1
            progress_share = sum(1 for r in rs if r["dominant_drive"] == "progress") / len(rs)
            if progress_share >= 0.3:
                progress_driven_cells += 1
    features["progress_driven_cell_share"] = (
        progress_driven_cells / total_with_data if total_with_data > 0 else 0
    )

    # --- Feature-cell affinity ---
    feature_visits = sum(r["is_feature"] for r in log)
    feature_visit_share = feature_visits / n_steps
    feature_cells_in_scope = sum(1 for c in agent.scope if c in FEATURE_CELLS)
    expected_feature_share = feature_cells_in_scope / len(agent.scope)
    features["feature_visit_ratio"] = feature_visit_share / expected_feature_share if expected_feature_share > 0 else 0

    # ----------------------------------------------------------------------
    # CONVERT FEATURES TO CLAIMS
    # ----------------------------------------------------------------------

    claims = []

    # Drive tendency claim — strength depends on the gap
    if drive_gap > 0.20:
        strength = "strongly"
    elif drive_gap > 0.08:
        strength = "moderately"
    elif drive_gap > 0.03:
        strength = "slightly"
    else:
        strength = None

    drive_description = {
        "progress": "the pull of getting better at things I was beginning to understand",
        "coverage": "the pull of reaching cells I had not yet visited",
        "novelty": "the pull of cells I had seen only rarely",
        "none": "none of my drives clearly"
    }

    if strength:
        claims.append(
            (f"I appear to have been {strength} drawn to "
             f"{drive_description[top_drive]} "
             f"(dominant in {100*top_share:.0f}% of my choices, "
             f"against {100*runner_up_share:.0f}% for the runner-up).",
             "drive_tendency", drive_gap)
        )
    else:
        claims.append(
            ("My drives appear to have been roughly balanced throughout my life; "
             "no single pull was clearly dominant.",
             "drive_tendency", 0.0)
        )

    # Region affinity
    if features["post_coverage_available"]:
        ratio = features["top_cell_vs_uniform"]
        cell = features["top_cell_post"]
        if ratio > 3:
            claims.append(
                (f"After I had covered the map, I returned repeatedly to cell {cell} — "
                 f"visiting it {ratio:.1f} times more often than a uniform pattern would produce. "
                 f"{'This was a feature cell.' if features['top_cell_is_feature'] else 'This was not a feature cell.'}",
                 "region_affinity", ratio)
            )
        elif ratio > 1.5:
            claims.append(
                (f"After coverage was complete, I showed a mild preference for cell {cell}, "
                 f"visiting it {ratio:.1f} times more often than uniform attention would predict.",
                 "region_affinity", ratio)
            )
        else:
            claims.append(
                ("After coverage, my attention was distributed fairly evenly across the map; "
                 "I did not appear to develop a strong preference for any particular region.",
                 "region_affinity", ratio)
            )

    # Persistence
    mp = features["mean_persistence"]
    if mp > 2.5:
        claims.append(
            (f"I tended to linger — on average I spent {mp:.1f} consecutive steps in a cell "
             "before moving on.",
             "persistence", mp)
        )
    elif mp < 1.3:
        claims.append(
            (f"I tended to move quickly — on average I stayed only {mp:.2f} steps in a cell "
             "before leaving.",
             "persistence", mp)
        )
    else:
        claims.append(
            (f"My persistence was moderate — an average of {mp:.2f} consecutive steps per cell.",
             "persistence", mp)
        )

    # Abandonment
    once = features["visited_once"]
    revisited = features["revisited_often"]
    if once > revisited * 2:
        claims.append(
            (f"I left {once} cells after a single visit and returned often to only {revisited} — "
             "I appear to have been more of a scanner than a returner.",
             "abandonment", once / max(revisited, 1))
        )
    elif revisited > once * 2:
        claims.append(
            (f"I returned often to {revisited} cells and only briefly visited {once} — "
             "I appear to have been more of a returner than a scanner.",
             "abandonment", revisited / max(once, 1))
        )
    else:
        claims.append(
            (f"I balanced scanning and returning — {once} cells visited briefly, "
             f"{revisited} cells revisited often.",
             "abandonment", 1.0)
        )

    # Feature affinity
    fr = features["feature_visit_ratio"]
    if fr > 1.3:
        claims.append(
            (f"Cells that produced distinct observations drew me disproportionately — "
             f"I spent {fr:.1f} times more time in them than chance would predict.",
             "feature_affinity", fr)
        )
    elif fr < 0.7:
        claims.append(
            (f"I appear to have been somewhat indifferent to cells with distinct observations; "
             f"I visited them {fr:.1f} times less than chance would predict.",
             "feature_affinity", fr)
        )

    return features, claims


def format_structured_report(features, agent, coverage_complete_step):
    """Machine-style structured characterisation."""
    lines = []
    lines.append("=" * 60)
    lines.append("STRUCTURED CHARACTERISATION")
    lines.append("=" * 60)
    lines.append(f"Life length            : {agent.steps_taken + 1} steps")
    lines.append(f"Scope covered          : {len(agent.covered)} / {len(agent.scope)}")
    if coverage_complete_step is not None:
        lines.append(f"Coverage completed at  : step {coverage_complete_step}")
    else:
        lines.append(f"Coverage completed at  : NOT COMPLETED")
    lines.append(f"Cells seen in total    : {features['total_cells_seen']}")
    lines.append("")
    lines.append("Drive profile:")
    for k, v in sorted(features["drive_shares"].items(), key=lambda kv: -kv[1]):
        lines.append(f"  {k:10s}: {100*v:5.1f}% of steps")
    lines.append("")
    lines.append(f"Mean persistence per cell : {features['mean_persistence']:.2f} steps")
    lines.append(f"Max persistence run       : {features['max_persistence']} steps")
    lines.append(f"Cells visited only once   : {features['visited_once']}")
    lines.append(f"Cells visited often (>5)  : {features['revisited_often']}")
    lines.append(f"Feature cell attraction   : {features['feature_visit_ratio']:.2f} x chance")
    if features["post_coverage_available"]:
        lines.append("")
        lines.append("After coverage, top 3 cells:")
        for cell, n in features["top_3_cells_post"]:
            marker = " (feature)" if cell in FEATURE_CELLS else ""
            lines.append(f"  {cell}: {n} visits{marker}")
    return "\n".join(lines)


def format_narrative_report(claims):
    """First-person, tentative, grounded narrative."""
    lines = []
    lines.append("=" * 60)
    lines.append("NARRATIVE CHARACTERISATION")
    lines.append("(the agent, describing itself from its log)")
    lines.append("=" * 60)
    lines.append("")
    for claim, _, _ in claims:
        lines.append(claim)
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 4. THE RUN
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
    action_window = []
    entropy_trace = []

    state = world.observe()
    coverage_complete_step = None

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        action, _ = agent.choose_action(state)
        next_state = world.step(action)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_coverage = agent.coverage_reward(next_state)
        intrinsic = r_novelty + r_progress + r_coverage

        # Determine new-coverage and mastery flags BEFORE update
        cell = (next_state[0], next_state[1])
        is_new_coverage = (cell in agent.scope) and (cell not in agent.covered)
        pair = (state, action)
        is_mastered = (len(agent.fast_errors[pair]) >= 5 and
                       np.mean(agent.fast_errors[pair]) < 0.15)

        agent.update_model(state, action, next_state, error)
        agent.update_values(state, action, next_state, intrinsic)

        # Record in self-log
        agent.record_step(step, state, action, next_state,
                          r_novelty, r_progress, r_coverage,
                          error, is_new_coverage, is_mastered)

        x, y, _ = next_state
        heatmap[y, x] += 1

        novelty_trace.append(r_novelty)
        progress_trace.append(r_progress)
        coverage_reward_trace.append(r_coverage)
        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))

        # Mastery count
        mastered = sum(1 for errs in agent.fast_errors.values()
                       if len(errs) >= 5 and np.mean(errs) < 0.15)
        mastered_count_trace.append(mastered)

        action_window.append(action)
        if len(action_window) > 200:
            action_window.pop(0)
        counts = np.bincount(action_window, minlength=4) / len(action_window)
        ent = -np.sum(counts * np.log(counts + 1e-9))
        entropy_trace.append(ent)

        if coverage_complete_step is None and len(agent.covered) == len(agent.scope):
            coverage_complete_step = step

        state = next_state

    # ----------------------------------------------------------------------
    # 5. INTERPRETATION
    # ----------------------------------------------------------------------

    features, claims = interpret_self(agent, coverage_complete_step)

    # ----------------------------------------------------------------------
    # 6. PLOTS
    # ----------------------------------------------------------------------

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
    plt.savefig("run_output_v0_5.png", dpi=120)

    # ----------------------------------------------------------------------
    # 7. THE REPORTS
    # ----------------------------------------------------------------------

    print("\n")
    print(format_structured_report(features, agent, coverage_complete_step))
    print("\n")
    print(format_narrative_report(claims))

    # Save reports to file as well
    with open("self_report_v0_5.txt", "w") as f:
        f.write(format_structured_report(features, agent, coverage_complete_step))
        f.write("\n\n")
        f.write(format_narrative_report(claims))

    print("\nReports also saved to self_report_v0_5.txt")
    print("Plots saved to run_output_v0_5.png")

    plt.show()


if __name__ == "__main__":
    run()
