"""
curiosity_agent_v0_4_4_batch.py
-------------------------------
Batch runner for the v0.4.4 phase-structured agent with prescribed
Phase 1 traversal.

Naming convention: agent code is identical to v0.4.4, only the harness
differs. The _batch suffix preserves traceability.

Purpose: determine whether the focused Phase 3 behaviour observed in
the single v0.4.4 run — concentration index >20x, preferences
clustered around feature cells — is reproducible across runs or a
fortunate stochastic artefact.

Specifically we want to answer:
  - Is Phase 3 concentration consistently high (>20x uniform)?
  - Do preferences reliably cluster near feature cells?
  - Does Phase 2 feature visit ratio predict Phase 3 preferences?
  - How stable is mastery count across runs?

Run from Terminal with:
    python3 curiosity_agent_v0_4_4_batch.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
from collections import defaultdict, deque, Counter
import time

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

NUM_RUNS = 10
GRID_SIZE = 10
NUM_STEPS = 10000
FEATURE_CELLS = [(2, 3), (7, 8), (4, 6), (8, 1), (1, 7)]
PHASE_3_START_FRACTION = 0.6
Q_VALUE_RESET_MULTIPLIER = 0.3


# --------------------------------------------------------------------------
# WORLD
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


# --------------------------------------------------------------------------
# BOUSTROPHEDON TRAVERSAL
# --------------------------------------------------------------------------

def boustrophedon_path(size):
    path = []
    for y in range(size):
        if y % 2 == 0:
            for x in range(size):
                path.append((x, y))
        else:
            for x in range(size - 1, -1, -1):
                path.append((x, y))
    return path


def action_to_move(from_cell, to_cell):
    fx, fy = from_cell
    tx, ty = to_cell
    dx = tx - fx
    dy = ty - fy
    if dy == -1: return 0
    if dy == 1:  return 1
    if dx == -1: return 2
    if dx == 1:  return 3
    return 0  # fallback


# --------------------------------------------------------------------------
# AGENT (identical to v0.4.4)
# --------------------------------------------------------------------------

class PhasedAgent:
    def __init__(self, scope_cells, total_steps, num_actions=4):
        self.scope = set(scope_cells)
        self.total_steps = total_steps
        self.steps_taken = 0
        self.covered = set()
        self.num_actions = num_actions
        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.fast_errors = defaultdict(lambda: deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: deque(maxlen=30))
        self.cell_preference = defaultdict(float)
        self.q_values = defaultdict(float)
        self.phase = 1
        self.phase_1_end_step = None
        self.phase_2_end_step = None
        self.phase_3_start_target = int(total_steps * PHASE_3_START_FRACTION)
        self.prescribed_path = boustrophedon_path(GRID_SIZE)
        self.path_index = 0
        self.learning_rate = 0.1
        self.epsilon = 0.1
        self._apply_phase_weights()

    def _apply_phase_weights(self):
        if self.phase == 1:
            self.novelty_weight = 0.0
            self.progress_weight = 0.0
            self.preference_weight = 0.0
        elif self.phase == 2:
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.0
        elif self.phase == 3:
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.8

    def _transition_phase(self, new_phase):
        for key in list(self.q_values.keys()):
            self.q_values[key] *= Q_VALUE_RESET_MULTIPLIER
        self.phase = new_phase
        self._apply_phase_weights()

    def check_phase_transition(self):
        if self.phase == 1:
            if self.path_index >= len(self.prescribed_path):
                self.phase_1_end_step = self.steps_taken
                self._transition_phase(2)
                return True
        elif self.phase == 2:
            if self.steps_taken >= self.phase_3_start_target:
                self.phase_2_end_step = self.steps_taken
                self._transition_phase(3)
                return True
        return False

    def get_prescribed_action(self, current_cell):
        if self.path_index == 0:
            self.path_index = 1
        if self.path_index >= len(self.prescribed_path):
            return None
        next_cell = self.prescribed_path[self.path_index]
        action = action_to_move(current_cell, next_cell)
        self.path_index += 1
        return action

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
        return self.progress_weight * max(0.0, progress)

    def update_model(self, state, action, next_state, error, r_progress):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)
        self.cell_preference[cell] += r_progress

    def update_values(self, state, action, next_state, intrinsic):
        if self.phase == 1:
            return
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error


# --------------------------------------------------------------------------
# SINGLE RUN
# --------------------------------------------------------------------------

def single_run():
    np.random.seed(None)
    world = GridWorld()
    agent = PhasedAgent(world.scope_cells, NUM_STEPS)
    heatmap_by_phase = {1: np.zeros((GRID_SIZE, GRID_SIZE)),
                        2: np.zeros((GRID_SIZE, GRID_SIZE)),
                        3: np.zeros((GRID_SIZE, GRID_SIZE))}
    state = world.observe()

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        agent.check_phase_transition()

        if agent.phase == 1:
            current_cell = (state[0], state[1])
            action = agent.get_prescribed_action(current_cell)
            if action is None:
                action = 0
        else:
            action = agent.choose_action(state)

        next_state = world.step(action)
        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        intrinsic = r_novelty + r_progress + r_preference
        agent.update_model(state, action, next_state, error, r_progress)
        agent.update_values(state, action, next_state, intrinsic)

        x, y, _ = next_state
        heatmap_by_phase[agent.phase][y, x] += 1
        state = next_state

    # Analysis
    def feature_ratio(heatmap):
        total = heatmap.sum()
        if total == 0: return 0.0
        feature_visits = sum(heatmap[fy, fx] for fx, fy in FEATURE_CELLS)
        expected_share = len(FEATURE_CELLS) / (GRID_SIZE * GRID_SIZE)
        actual_share = feature_visits / total
        return actual_share / expected_share if expected_share > 0 else 0.0

    def attention_cv(heatmap):
        visits = heatmap[heatmap > 0]
        if len(visits) < 2: return 0.0
        return visits.std() / visits.mean()

    p3_visits = heatmap_by_phase[3]
    p3_total = int(p3_visits.sum())
    if p3_total > 0:
        p3_concentration = p3_visits.max() / (p3_total / (GRID_SIZE * GRID_SIZE))
    else:
        p3_concentration = 0.0

    # Top preferred cells — are they near features?
    top_preferred = sorted(agent.cell_preference.items(),
                           key=lambda kv: -kv[1])[:5]
    top_pref_cells = [c for c, _ in top_preferred]
    # Count how many top-5 preferred cells are a feature cell or adjacent to one
    def near_feature(cell):
        for fx, fy in FEATURE_CELLS:
            if abs(cell[0] - fx) + abs(cell[1] - fy) <= 1:
                return True
        return False

    top_pref_on_feature = sum(1 for c in top_pref_cells if c in FEATURE_CELLS)
    top_pref_near_feature = sum(1 for c in top_pref_cells if near_feature(c))

    mastered = sum(
        1 for errs in agent.fast_errors.values()
        if len(errs) >= 5 and np.mean(errs) < 0.15
    )

    return {
        "phase_1_end": agent.phase_1_end_step,
        "phase_2_end": agent.phase_2_end_step,
        "p1_feature_ratio": feature_ratio(heatmap_by_phase[1]),
        "p2_feature_ratio": feature_ratio(heatmap_by_phase[2]),
        "p3_feature_ratio": feature_ratio(heatmap_by_phase[3]),
        "p2_cv": attention_cv(heatmap_by_phase[2]),
        "p3_cv": attention_cv(heatmap_by_phase[3]),
        "p3_concentration": p3_concentration,
        "mastered_count": mastered,
        "top_pref_cells": top_pref_cells,
        "top_pref_on_feature": top_pref_on_feature,
        "top_pref_near_feature": top_pref_near_feature,
    }


# --------------------------------------------------------------------------
# META-REPORT
# --------------------------------------------------------------------------

def aggregate_and_report(all_results):
    n = len(all_results)
    out = []
    out.append("=" * 78)
    out.append(f"META-REPORT: PHASE-STRUCTURED AGENT ACROSS {n} LIVES (v0.4.4)")
    out.append("=" * 78)
    out.append("")

    # Per-run table
    out.append("PER-RUN RESULTS")
    out.append("-" * 78)
    out.append(f"{'run':>3} | {'P3 conc':>7} | {'P3 feat':>7} | {'P2 feat':>7} | "
               f"{'P3 CV':>5} | {'mast':>5} | {'pref near feat':>14}")
    out.append("-" * 78)
    for i, r in enumerate(all_results, 1):
        out.append(
            f"{i:>3} | {r['p3_concentration']:>7.1f} | "
            f"{r['p3_feature_ratio']:>7.2f} | "
            f"{r['p2_feature_ratio']:>7.2f} | "
            f"{r['p3_cv']:>5.2f} | "
            f"{r['mastered_count']:>5d} | "
            f"{r['top_pref_near_feature']:>3d}/5"
        )

    # Aggregates
    def m_s(values):
        return np.mean(values), np.std(values)

    out.append("")
    out.append("CENTRAL TENDENCIES (mean +/- std)")
    out.append("-" * 78)
    p3_conc = [r["p3_concentration"] for r in all_results]
    p3_feat = [r["p3_feature_ratio"] for r in all_results]
    p2_feat = [r["p2_feature_ratio"] for r in all_results]
    p3_cv = [r["p3_cv"] for r in all_results]
    mastery = [r["mastered_count"] for r in all_results]
    pref_near = [r["top_pref_near_feature"] for r in all_results]

    m, s = m_s(p3_conc)
    out.append(f"  Phase 3 concentration   : {m:6.2f} +/- {s:5.2f}  "
               f"(min {min(p3_conc):.1f}, max {max(p3_conc):.1f})")
    m, s = m_s(p3_feat)
    out.append(f"  Phase 3 feature ratio   : {m:6.2f} +/- {s:5.2f}  "
               f"(min {min(p3_feat):.2f}, max {max(p3_feat):.2f})")
    m, s = m_s(p2_feat)
    out.append(f"  Phase 2 feature ratio   : {m:6.2f} +/- {s:5.2f}")
    m, s = m_s(p3_cv)
    out.append(f"  Phase 3 attention CV    : {m:6.2f} +/- {s:5.2f}")
    m, s = m_s(mastery)
    out.append(f"  Pairs mastered          : {m:6.1f} +/- {s:5.1f}  "
               f"(min {min(mastery)}, max {max(mastery)})")
    m, s = m_s(pref_near)
    out.append(f"  Top-5 prefs near feature: {m:6.2f} +/- {s:5.2f} (out of 5)")

    # Feature preference hit rate
    out.append("")
    out.append("PREFERENCE / FEATURE ALIGNMENT")
    out.append("-" * 78)
    any_on_feature = sum(1 for r in all_results if r["top_pref_on_feature"] > 0)
    majority_near_feature = sum(1 for r in all_results if r["top_pref_near_feature"] >= 3)
    out.append(f"  Runs where a feature cell was in top-5 prefs : {any_on_feature}/{n}")
    out.append(f"  Runs where 3+ of top-5 prefs are near feature: {majority_near_feature}/{n}")

    # Concentration stability
    high_conc = sum(1 for c in p3_conc if c >= 20.0)
    moderate_conc = sum(1 for c in p3_conc if 10.0 <= c < 20.0)
    low_conc = sum(1 for c in p3_conc if c < 10.0)
    out.append("")
    out.append("PHASE 3 CONCENTRATION DISTRIBUTION")
    out.append("-" * 78)
    out.append(f"  High (>= 20x uniform)     : {high_conc}/{n}")
    out.append(f"  Moderate (10-20x)         : {moderate_conc}/{n}")
    out.append(f"  Low (< 10x)               : {low_conc}/{n}")

    # Interpretation
    out.append("")
    out.append("=" * 78)
    out.append("INTERPRETATION")
    out.append("=" * 78)
    out.append("")

    mean_conc = np.mean(p3_conc)
    mean_p3_feat = np.mean(p3_feat)
    mean_near = np.mean(pref_near)

    if mean_conc >= 15 and high_conc >= 0.6 * n:
        out.append("FOCUSED AUTONOMY is reproducible under this architecture. Across most")
        out.append("runs, the agent in Phase 3 concentrated its attention on a small number")
        out.append("of cells — well above the threshold that distinguishes focused behaviour")
        out.append("from broadly distributed activity.")
    elif mean_conc >= 8:
        out.append("Focused autonomy appears in most runs but with meaningful variability.")
        out.append("Some lives produce strong concentration, others more diffuse attention.")
    else:
        out.append("Concentration in Phase 3 is LOW across runs. The architecture does not")
        out.append("reliably produce focused autonomous behaviour even with a structured")
        out.append("Phase 1.")

    if mean_p3_feat >= 3.0:
        out.append("")
        out.append("FEATURE AFFINITY IS ARCHITECTURAL. The agent in Phase 3 visits cells with")
        out.append("distinct observations far more often than chance would predict. Its")
        out.append("preferences are NOT arbitrary accidents of trajectory — they are grounded")
        out.append("in cells that genuinely offered something to learn.")
    elif mean_p3_feat >= 1.5:
        out.append("")
        out.append("Feature affinity is present but moderate. The agent's preferences lean")
        out.append("toward feature cells but do not overwhelmingly concentrate on them.")
    else:
        out.append("")
        out.append("Feature affinity is near chance. The architecture does not reliably pull")
        out.append("the agent toward cells with distinct observations.")

    if mean_near >= 3.0:
        out.append("")
        out.append("The agent's strongest preferences consistently cluster in the neighbourhood")
        out.append("of feature cells. This is the clearest signature that structured acquisition")
        out.append("enables meaningful downstream preference formation.")

    return "\n".join(out)


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main():
    print(f"Running {NUM_RUNS} independent lives of the v0.4.4 agent...")
    print(f"Each run = {NUM_STEPS} steps with prescribed Phase 1 traversal.")
    print()
    all_results = []
    start = time.time()

    for i in range(NUM_RUNS):
        r = single_run()
        all_results.append(r)
        print(f"  Run {i+1:2d}/{NUM_RUNS}: P3 conc={r['p3_concentration']:5.1f}x  "
              f"P3 feat ratio={r['p3_feature_ratio']:4.2f}  "
              f"P3 CV={r['p3_cv']:.2f}  "
              f"mastery={r['mastered_count']:3d}  "
              f"prefs near feature={r['top_pref_near_feature']}/5")

    total_time = time.time() - start
    print(f"\nAll runs complete in {total_time:.1f} seconds.")

    report = aggregate_and_report(all_results)
    print()
    print(report)

    with open("meta_report_v0_4_4.txt", "w") as f:
        f.write(report)
    print(f"\nMeta-report saved to meta_report_v0_4_4.txt")


if __name__ == "__main__":
    main()
