"""
curiosity_agent_v0_5_1_batch.py
-------------------------------
Batch runner for the v0.5.1 developmental agent. Runs the agent N times
independently and produces a meta-report aggregating the self-portraits
across all runs.

Naming convention: this file ends in _batch rather than being given a
new version number, because the AGENT CODE is unchanged from v0.5.1.
Only the harness around it differs. Future batch wrappers should follow
the same pattern (e.g. curiosity_agent_v0_6_batch.py).

Purpose: distinguish architectural tendencies (claims that fire across
most runs) from stochastic accidents (claims that fire only sometimes).
This gives us a stable characterisation of what kind of agent this
architecture *tends* to produce — material we can use as the input to
v0.6, where the self-representation becomes operational.

Run from Terminal with:
    python3 curiosity_agent_v0_5_1_batch.py

Default is 10 runs. Adjust NUM_RUNS below to taste.
Plots are NOT shown; each run's data is collected silently and the
combined meta-report is printed at the end and saved to file.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend; suppresses plot windows
import matplotlib.pyplot as plt
from collections import defaultdict, deque, Counter
import time

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

NUM_RUNS = 10
GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]

# --------------------------------------------------------------------------
# WORLD AND AGENT (identical to v0.5.1)
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
        self.coverage_weight = 6.0
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
# INTERPRETATION (identical to v0.5.1, returns features and claims)
# --------------------------------------------------------------------------

def interpret_self(agent, coverage_complete_step):
    log = agent.self_log
    n_steps = len(log)
    cells_seen = len(set(r["cell"] for r in log))
    features = {}
    fired_claims = {}

    drive_counts = Counter(r["dominant_drive"] for r in log)
    total = sum(drive_counts.values())
    drive_shares = {k: v / total for k, v in drive_counts.items()}
    features["drive_shares"] = drive_shares
    ranked = sorted(drive_shares.items(), key=lambda kv: -kv[1])
    top_drive, top_share = ranked[0]
    runner_up_share = ranked[1][1] if len(ranked) > 1 else 0
    drive_gap = top_share - runner_up_share
    features["top_drive"] = top_drive
    features["drive_gap"] = drive_gap

    if drive_gap >= 0.20:
        fired_claims["drive_strong"] = (top_drive, top_share, runner_up_share)
    elif drive_gap >= 0.10:
        fired_claims["drive_moderate"] = (top_drive, top_share, runner_up_share)
    elif drive_gap >= 0.05:
        fired_claims["drive_slight"] = (top_drive, top_share, runner_up_share)

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
    mean_persistence = np.mean(runs)
    features["mean_persistence"] = mean_persistence
    if mean_persistence >= 1.5:
        fired_claims["persistence_lingering"] = mean_persistence
    elif mean_persistence <= 1.02:
        fired_claims["persistence_none"] = mean_persistence

    cell_visit_counts = Counter(r["cell"] for r in log)
    visits = np.array(list(cell_visit_counts.values()))
    expected_per_cell = n_steps / cells_seen
    cv = np.std(visits) / np.mean(visits)
    features["attention_cv"] = cv
    features["max_over_uniform"] = max(visits) / expected_per_cell
    if cv >= 0.6:
        fired_claims["attention_uneven"] = (cv, features["max_over_uniform"])
    elif cv <= 0.3:
        fired_claims["attention_even"] = cv

    feature_visits = sum(r["is_feature"] for r in log)
    feature_visit_share = feature_visits / n_steps
    feature_cells_in_scope = sum(1 for c in agent.scope if c in FEATURE_CELLS)
    expected_feature_share = feature_cells_in_scope / len(agent.scope)
    feature_ratio = feature_visit_share / expected_feature_share if expected_feature_share > 0 else 0
    features["feature_ratio"] = feature_ratio
    if feature_ratio >= 1.4:
        fired_claims["feature_drawn"] = feature_ratio
    elif feature_ratio <= 0.7:
        fired_claims["feature_avoidance"] = feature_ratio

    features["coverage_complete_step"] = coverage_complete_step
    features["cells_covered"] = len(agent.covered)
    features["mastered_count"] = sum(
        1 for errs in agent.fast_errors.values()
        if len(errs) >= 5 and np.mean(errs) < 0.15
    )

    return features, fired_claims


# --------------------------------------------------------------------------
# SINGLE RUN
# --------------------------------------------------------------------------

def single_run(run_idx):
    np.random.seed(None)
    world = GridWorld()
    agent = DevelopmentalAgent(world.scope_cells, NUM_STEPS)
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

        if coverage_complete_step is None and len(agent.covered) == len(agent.scope):
            coverage_complete_step = step
        state = next_state

    features, fired_claims = interpret_self(agent, coverage_complete_step)
    return features, fired_claims


# --------------------------------------------------------------------------
# META-REPORT
# --------------------------------------------------------------------------

drive_description = {
    "progress": "the pull of getting better at what I am beginning to understand",
    "coverage": "the pull of reaching cells I have not yet visited",
    "novelty": "the pull of cells I have seen only rarely",
}


def aggregate_and_report(all_features, all_fired):
    n = len(all_features)
    out = []
    out.append("=" * 65)
    out.append(f"META-REPORT: AGGREGATE OF {n} INDEPENDENT LIVES (v0.5.1 agent)")
    out.append("=" * 65)
    out.append("")
    out.append("CENTRAL TENDENCIES (mean +/- std)")
    out.append("-" * 65)

    def m_s(values):
        return np.mean(values), np.std(values)

    coverage_vals = [f["cells_covered"] for f in all_features]
    mastered_vals = [f["mastered_count"] for f in all_features]
    cv_vals = [f["attention_cv"] for f in all_features]
    feat_vals = [f["feature_ratio"] for f in all_features]
    persist_vals = [f["mean_persistence"] for f in all_features]

    m, s = m_s(coverage_vals)
    out.append(f"  Cells covered           : {m:5.1f} +/- {s:4.1f}  "
               f"(min {min(coverage_vals)}, max {max(coverage_vals)})")
    m, s = m_s(mastered_vals)
    out.append(f"  Pairs mastered          : {m:5.1f} +/- {s:4.1f}  "
               f"(min {min(mastered_vals)}, max {max(mastered_vals)})")
    m, s = m_s(cv_vals)
    out.append(f"  Attention CV            : {m:5.2f} +/- {s:4.2f}  "
               f"(min {min(cv_vals):.2f}, max {max(cv_vals):.2f})")
    m, s = m_s(feat_vals)
    out.append(f"  Feature visit ratio     : {m:5.2f} +/- {s:4.2f}  "
               f"(min {min(feat_vals):.2f}, max {max(feat_vals):.2f})")
    m, s = m_s(persist_vals)
    out.append(f"  Mean persistence        : {m:5.2f} +/- {s:4.2f}  "
               f"(min {min(persist_vals):.2f}, max {max(persist_vals):.2f})")

    completed = sum(1 for f in all_features if f["coverage_complete_step"] is not None)
    out.append(f"  Coverage completed in   : {completed}/{n} runs")

    out.append("")
    out.append("DRIVE DOMINANCE (which drive was top, across runs)")
    out.append("-" * 65)
    top_drive_counts = Counter(f["top_drive"] for f in all_features)
    for drive, count in top_drive_counts.most_common():
        out.append(f"  {drive:10s}: top in {count}/{n} runs ({100*count/n:.0f}%)")

    out.append("")
    out.append("AVERAGE DRIVE SHARES (% of steps each drive dominated)")
    out.append("-" * 65)
    for drive in ["novelty", "progress", "coverage"]:
        shares = [f["drive_shares"].get(drive, 0) for f in all_features]
        m, s = m_s(shares)
        out.append(f"  {drive:10s}: {100*m:5.1f}% +/- {100*s:4.1f}%")

    out.append("")
    out.append("CLAIM STABILITY (how often each claim fired)")
    out.append("-" * 65)
    claim_counts = Counter()
    for fired in all_fired:
        for claim_name in fired:
            claim_counts[claim_name] += 1
    claim_descriptions = {
        "drive_strong": "drive tendency: STRONGLY drawn to one drive",
        "drive_moderate": "drive tendency: MODERATELY drawn to one drive",
        "drive_slight": "drive tendency: SLIGHTLY drawn to one drive",
        "persistence_lingering": "persistence: lingering above baseline",
        "persistence_none": "persistence: at random-movement baseline",
        "attention_uneven": "attention distribution: uneven (corner-camping)",
        "attention_even": "attention distribution: even",
        "feature_drawn": "feature affinity: drawn to feature cells",
        "feature_avoidance": "feature affinity: avoiding feature cells",
    }
    for claim_name, desc in claim_descriptions.items():
        c = claim_counts.get(claim_name, 0)
        if c > 0:
            stability = "STABLE" if c >= 0.7*n else "MIXED" if c >= 0.3*n else "RARE"
            out.append(f"  [{stability:6s}] {c}/{n} runs : {desc}")

    out.append("")
    out.append("=" * 65)
    out.append("CONSENSUS SELF-PORTRAIT")
    out.append("(claims that fired in 70%+ of lives — the architectural tendencies)")
    out.append("=" * 65)
    out.append("")
    consensus = [name for name, c in claim_counts.items() if c >= 0.7 * n]

    if not consensus:
        out.append("Across these lives, no single self-claim was stable enough to be")
        out.append("considered a real architectural tendency. The agent's self-portrait")
        out.append("varies meaningfully from run to run.")
    else:
        if any(c.startswith("drive_") for c in consensus):
            top_drives_seen = [f["top_drive"] for f in all_features]
            most_common_top = Counter(top_drives_seen).most_common(1)[0][0]
            count_top = Counter(top_drives_seen)[most_common_top]
            out.append(f"In most of my lives ({count_top}/{n}), I was drawn most strongly to")
            out.append(f"{drive_description[most_common_top]}.")
            out.append("")
        if "attention_uneven" in consensus:
            out.append("My attention is consistently unevenly distributed across the")
            out.append("territory I am responsible for; I tend to over-visit a few cells")
            out.append("at the expense of others.")
            out.append("")
        if "attention_even" in consensus:
            out.append("My attention tends to spread fairly evenly across the territory")
            out.append("I am responsible for; I do not strongly favour particular regions.")
            out.append("")
        if "feature_avoidance" in consensus:
            out.append("I appear to systematically under-visit cells with distinct")
            out.append("observations — a tendency that holds across most of my lives.")
            out.append("")
        if "feature_drawn" in consensus:
            out.append("I appear to be reliably drawn to cells with distinct observations,")
            out.append("visiting them more than chance across most of my lives.")
            out.append("")
        if "persistence_none" in consensus:
            out.append("I almost never linger in cells; my movement is restless across")
            out.append("nearly all of my lives.")
            out.append("")
        if "persistence_lingering" in consensus:
            out.append("I tend to linger in cells; this pattern holds across most of my")
            out.append("lives.")
            out.append("")

    out.append("=" * 65)
    return "\n".join(out)


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main():
    print(f"Running {NUM_RUNS} independent lives of the v0.5.1 agent...")
    print(f"Each run = {NUM_STEPS} steps. This will take a few minutes.")
    print()
    all_features = []
    all_fired = []
    start = time.time()

    for i in range(NUM_RUNS):
        run_start = time.time()
        features, fired = single_run(i)
        all_features.append(features)
        all_fired.append(fired)
        elapsed = time.time() - run_start
        print(f"  Run {i+1:2d}/{NUM_RUNS} done — "
              f"covered {features['cells_covered']:3d}/100, "
              f"top drive {features['top_drive']:10s} ({100*features['drive_shares'][features['top_drive']]:.0f}%), "
              f"feature ratio {features['feature_ratio']:.2f}, "
              f"({elapsed:.1f}s)")

    total_time = time.time() - start
    print(f"\nAll runs complete in {total_time:.1f} seconds.")

    report = aggregate_and_report(all_features, all_fired)
    print()
    print(report)

    with open("meta_report_v0_5_1.txt", "w") as f:
        f.write(report)
    print(f"\nMeta-report saved to meta_report_v0_5_1.txt")


if __name__ == "__main__":
    main()
