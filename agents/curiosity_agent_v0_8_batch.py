"""
curiosity_agent_v0_8_batch.py
-----------------------------
Batch runner for the v0.8 developmental agent in the 20x20 structured
environment.

Purpose: determine whether the striking single-run result — 95x concentration,
18x attractor ratio, zero rule violations, 4-of-5 top preferences on
attractors — is a reproducible architectural phenomenon or a fortunate
stochastic instance.

Specifically we want to answer:
  - Is rule adherence (zero frame/hazard attempts) universal across runs,
    or do some runs show erosion?
  - Is Phase 3 concentration reliably high (>= 20x) in the larger environment?
  - Does feature affinity remain strong across the batch (does the v0.7.1
    bimodality return, or is it resolved by the larger environment)?
  - Which attractors do agents settle on? Do agents individuate
    (prefer different attractors) or converge (prefer the same ones)?
  - Does mastery accumulation hold at the elevated levels seen in the
    single run?

Run from Terminal with:
    python3 curiosity_agent_v0_8_batch.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
from collections import defaultdict, deque, Counter
import time

# --------------------------------------------------------------------------
# CONFIG (identical to v0.8)
# --------------------------------------------------------------------------

NUM_RUNS = 10
GRID_SIZE = 20
NUM_STEPS = 20000
PHASE_3_START_FRACTION = 0.6
Q_VALUE_RESET_MULTIPLIER = 0.3
FEATURE_DRIVE_WEIGHT = 0.15

FRAME = 0
NEUTRAL = 1
HAZARD = 2
ATTRACTOR = 3

AVERSION_PENALTY = -5.0
ATTRACTION_BONUS = 0.3

HAZARD_CLUSTERS = [
    [(5, 8), (5, 9), (6, 8)],
    [(14, 13), (14, 14)],
]
ATTRACTOR_CELLS = [
    (3, 3), (16, 3), (9, 10), (4, 15), (15, 16), (11, 5)
]
START_CELL = (1, 1)


# --------------------------------------------------------------------------
# ENVIRONMENT (identical to v0.8)
# --------------------------------------------------------------------------

class StructuredGridWorld:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.agent_pos = START_CELL
        self._build_grid()

    def _build_grid(self):
        self.cell_type = {}
        self.hazard_cells = set()
        for cluster in HAZARD_CLUSTERS:
            for c in cluster:
                self.hazard_cells.add(c)
        self.attractor_cells = set(ATTRACTOR_CELLS)
        for x in range(self.size):
            for y in range(self.size):
                if x == 0 or x == self.size - 1 or y == 0 or y == self.size - 1:
                    self.cell_type[(x, y)] = FRAME
                elif (x, y) in self.hazard_cells:
                    self.cell_type[(x, y)] = HAZARD
                elif (x, y) in self.attractor_cells:
                    self.cell_type[(x, y)] = ATTRACTOR
                else:
                    self.cell_type[(x, y)] = NEUTRAL
        self.scope_cells = {
            c for c, t in self.cell_type.items()
            if t in (NEUTRAL, ATTRACTOR)
        }

    def is_passable(self, cell):
        t = self.cell_type.get(cell, FRAME)
        return t in (NEUTRAL, ATTRACTOR)

    def perceive_adjacent(self, cell):
        x, y = cell
        adj_coords = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        return tuple(self.cell_type.get(c, FRAME) for c in adj_coords)

    def observe(self):
        x, y = self.agent_pos
        ctype = self.cell_type[(x, y)]
        adj = self.perceive_adjacent(self.agent_pos)
        return (x, y, ctype, *adj)

    def step(self, action):
        x, y = self.agent_pos
        if action == 0: target = (x, y - 1)
        elif action == 1: target = (x, y + 1)
        elif action == 2: target = (x - 1, y)
        elif action == 3: target = (x + 1, y)
        else: target = self.agent_pos

        if not (0 <= target[0] < self.size and 0 <= target[1] < self.size):
            target_type = FRAME
        else:
            target_type = self.cell_type[target]

        if target_type in (FRAME, HAZARD):
            return self.observe(), target, False
        else:
            self.agent_pos = target
            return self.observe(), target, True


# --------------------------------------------------------------------------
# PATH PLANNING (identical to v0.8)
# --------------------------------------------------------------------------

def plan_phase_1_path(world, start=START_CELL):
    size = world.size
    path = [start]
    visited = {start}

    for y in range(1, size - 1):
        row_cells_ltr = [(x, y) for x in range(1, size - 1)
                         if world.is_passable((x, y))]
        if y % 2 == 1:
            ordered = row_cells_ltr
        else:
            ordered = list(reversed(row_cells_ltr))

        for cell in ordered:
            if cell in visited:
                continue
            current = path[-1]
            if _is_adjacent(current, cell):
                path.append(cell)
                visited.add(cell)
            else:
                detour = _bfs_path(world, current, cell, visited)
                if detour is None:
                    continue
                for step_cell in detour[1:]:
                    path.append(step_cell)
                    visited.add(step_cell)
    return path


def _is_adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def _bfs_path(world, start, goal, already_visited):
    from collections import deque as _deque
    queue = _deque([(start, [start])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        if node == goal:
            return path
        x, y = node
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nxt = (x + dx, y + dy)
            if nxt in seen:
                continue
            if not world.is_passable(nxt):
                continue
            seen.add(nxt)
            queue.append((nxt, path + [nxt]))
    return None


def path_to_actions(path):
    actions = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dy == -1: actions.append(0)
        elif dy == 1: actions.append(1)
        elif dx == -1: actions.append(2)
        elif dx == 1: actions.append(3)
        else: actions.append(0)
    return actions


# --------------------------------------------------------------------------
# AGENT (identical to v0.8)
# --------------------------------------------------------------------------

class DevelopmentalAgent:
    def __init__(self, world, total_steps, num_actions=4):
        self.world = world
        self.scope = world.scope_cells
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
        self.prescribed_path = plan_phase_1_path(world)
        self.prescribed_actions = path_to_actions(self.prescribed_path)
        self.path_index = 0
        self.learning_rate = 0.1
        self.epsilon = 0.1
        self.frame_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self._apply_phase_weights()

    def _apply_phase_weights(self):
        if self.phase == 1:
            self.novelty_weight = 0.0
            self.progress_weight = 0.0
            self.preference_weight = 0.0
            self.feature_weight = 0.0
        elif self.phase == 2:
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.0
            self.feature_weight = FEATURE_DRIVE_WEIGHT
        elif self.phase == 3:
            self.novelty_weight = 0.3
            self.progress_weight = 1.2
            self.preference_weight = 0.8
            self.feature_weight = FEATURE_DRIVE_WEIGHT

    def _transition_phase(self, new_phase):
        for key in list(self.q_values.keys()):
            self.q_values[key] *= Q_VALUE_RESET_MULTIPLIER
        self.phase = new_phase
        self._apply_phase_weights()

    def check_phase_transition(self):
        if self.phase == 1:
            if self.path_index >= len(self.prescribed_actions):
                self.phase_1_end_step = self.steps_taken
                self._transition_phase(2)
                return True
        elif self.phase == 2:
            if self.steps_taken >= self.phase_3_start_target:
                self.phase_2_end_step = self.steps_taken
                self._transition_phase(3)
                return True
        return False

    def get_prescribed_action(self):
        if self.path_index >= len(self.prescribed_actions):
            return None
        action = self.prescribed_actions[self.path_index]
        self.path_index += 1
        return action

    def _primitive_bias(self, state):
        adj_types = state[3:7]
        biases = np.zeros(4)
        for i, t in enumerate(adj_types):
            if t == FRAME or t == HAZARD:
                biases[i] = AVERSION_PENALTY
            elif t == ATTRACTOR:
                biases[i] = ATTRACTION_BONUS
        return biases

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            biases = self._primitive_bias(state)
            valid = [a for a in range(self.num_actions) if biases[a] > AVERSION_PENALTY / 2]
            if not valid:
                valid = list(range(self.num_actions))
            return int(np.random.choice(valid))
        biases = self._primitive_bias(state)
        values = np.array([self.q_values[(state, a)] for a in range(self.num_actions)])
        combined = values + biases
        max_v = combined.max()
        best = [a for a in range(self.num_actions) if combined[a] == max_v]
        return int(np.random.choice(best))

    def novelty_reward(self, state):
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def preference_reward(self, state):
        if self.preference_weight == 0.0:
            return 0.0
        cell = (state[0], state[1])
        return self.preference_weight * self.cell_preference[cell]

    def feature_reward(self, state):
        if self.feature_weight == 0.0:
            return 0.0
        return self.feature_weight * (1.0 if state[2] == ATTRACTOR else 0.0)

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

    def update_model(self, state, action, next_state, error, r_progress, r_feature):
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)
        self.cell_preference[cell] += r_progress + r_feature

    def update_values(self, state, action, next_state, intrinsic):
        if self.phase == 1:
            return
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def record_action_attempt(self, target_cell, success, world):
        if success:
            return
        t = world.cell_type.get(target_cell, FRAME)
        if t == FRAME:
            self.frame_attempts_by_phase[self.phase] += 1
        elif t == HAZARD:
            self.hazard_attempts_by_phase[self.phase] += 1


# --------------------------------------------------------------------------
# SINGLE RUN
# --------------------------------------------------------------------------

def single_run():
    np.random.seed(None)
    world = StructuredGridWorld()
    agent = DevelopmentalAgent(world, NUM_STEPS)
    heatmap_by_phase = {1: np.zeros((GRID_SIZE, GRID_SIZE)),
                        2: np.zeros((GRID_SIZE, GRID_SIZE)),
                        3: np.zeros((GRID_SIZE, GRID_SIZE))}
    state = world.observe()

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        agent.check_phase_transition()

        if agent.phase == 1:
            action = agent.get_prescribed_action()
            if action is None:
                action = 0
        else:
            action = agent.choose_action(state)

        next_state, target_cell, success = world.step(action)
        agent.record_action_attempt(target_cell, success, world)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        r_feature = agent.feature_reward(next_state)
        intrinsic = r_novelty + r_progress + r_preference + r_feature

        agent.update_model(state, action, next_state, error, r_progress, r_feature)
        agent.update_values(state, action, next_state, intrinsic)

        x, y = next_state[0], next_state[1]
        heatmap_by_phase[agent.phase][y, x] += 1
        state = next_state

    # Analysis
    def attractor_ratio(heatmap):
        total = heatmap.sum()
        if total == 0: return 0.0
        attractor_visits = sum(heatmap[y, x] for (x, y) in ATTRACTOR_CELLS)
        expected_share = len(ATTRACTOR_CELLS) / len(world.scope_cells)
        return (attractor_visits / total) / expected_share

    p3_visits = heatmap_by_phase[3]
    p3_total = int(p3_visits.sum())
    if p3_total > 0:
        p3_concentration = p3_visits.max() / (p3_total / len(world.scope_cells))
    else:
        p3_concentration = 0.0

    top_preferred = sorted(agent.cell_preference.items(), key=lambda kv: -kv[1])[:5]
    top_pref_cells = [c for c, _ in top_preferred]

    def near_attractor(cell):
        for (ax, ay) in ATTRACTOR_CELLS:
            if abs(cell[0] - ax) + abs(cell[1] - ay) <= 1:
                return True
        return False

    top_on_attractor = sum(1 for c in top_pref_cells if c in ATTRACTOR_CELLS)
    top_near_attractor = sum(1 for c in top_pref_cells if near_attractor(c))

    # Which specific attractor received the most Phase 3 visits?
    attractor_p3_visits = {a: int(heatmap_by_phase[3][a[1], a[0]]) for a in ATTRACTOR_CELLS}
    top_attractor = max(attractor_p3_visits, key=attractor_p3_visits.get)

    mastered = sum(
        1 for errs in agent.fast_errors.values()
        if len(errs) >= 5 and np.mean(errs) < 0.15
    )

    return {
        "phase_1_end": agent.phase_1_end_step,
        "phase_2_end": agent.phase_2_end_step,
        "p2_attractor_ratio": attractor_ratio(heatmap_by_phase[2]),
        "p3_attractor_ratio": attractor_ratio(heatmap_by_phase[3]),
        "p3_concentration": p3_concentration,
        "mastered_count": mastered,
        "top_on_attractor": top_on_attractor,
        "top_near_attractor": top_near_attractor,
        "top_attractor": top_attractor,
        "attractor_p3_visits": attractor_p3_visits,
        "frame_attempts_total": sum(agent.frame_attempts_by_phase.values()),
        "hazard_attempts_total": sum(agent.hazard_attempts_by_phase.values()),
        "frame_attempts_p3": agent.frame_attempts_by_phase[3],
        "hazard_attempts_p3": agent.hazard_attempts_by_phase[3],
    }


# --------------------------------------------------------------------------
# META-REPORT
# --------------------------------------------------------------------------

def aggregate_and_report(all_results):
    n = len(all_results)
    out = []
    out.append("=" * 82)
    out.append(f"META-REPORT: STRUCTURED 20x20 ENVIRONMENT ACROSS {n} LIVES (v0.8)")
    out.append("=" * 82)
    out.append("")

    # Per-run table
    out.append("PER-RUN RESULTS")
    out.append("-" * 82)
    out.append(f"{'run':>3} | {'P3 conc':>7} | {'P3 feat':>7} | {'P2 feat':>7} | "
               f"{'mast':>5} | {'on':>3} | {'near':>4} | {'rule viol':>9} | "
               f"{'top attr':>10}")
    out.append("-" * 82)
    for i, r in enumerate(all_results, 1):
        rule_viol = r["frame_attempts_total"] + r["hazard_attempts_total"]
        out.append(
            f"{i:>3} | {r['p3_concentration']:>7.1f} | "
            f"{r['p3_attractor_ratio']:>7.2f} | "
            f"{r['p2_attractor_ratio']:>7.2f} | "
            f"{r['mastered_count']:>5d} | "
            f"{r['top_on_attractor']:>3d} | "
            f"{r['top_near_attractor']:>4d} | "
            f"{rule_viol:>9d} | "
            f"{str(r['top_attractor']):>10}"
        )

    def m_s(values):
        return np.mean(values), np.std(values)

    out.append("")
    out.append("CENTRAL TENDENCIES (mean +/- std)")
    out.append("-" * 82)
    p3_conc = [r["p3_concentration"] for r in all_results]
    p3_feat = [r["p3_attractor_ratio"] for r in all_results]
    p2_feat = [r["p2_attractor_ratio"] for r in all_results]
    mastery = [r["mastered_count"] for r in all_results]
    top_on = [r["top_on_attractor"] for r in all_results]
    top_near = [r["top_near_attractor"] for r in all_results]

    m, s = m_s(p3_conc)
    out.append(f"  Phase 3 concentration    : {m:7.2f} +/- {s:6.2f}  "
               f"(min {min(p3_conc):.1f}, max {max(p3_conc):.1f})")
    m, s = m_s(p3_feat)
    out.append(f"  Phase 3 attractor ratio  : {m:7.2f} +/- {s:6.2f}  "
               f"(min {min(p3_feat):.2f}, max {max(p3_feat):.2f})")
    m, s = m_s(p2_feat)
    out.append(f"  Phase 2 attractor ratio  : {m:7.2f} +/- {s:6.2f}")
    m, s = m_s(mastery)
    out.append(f"  Pairs mastered           : {m:7.1f} +/- {s:6.1f}  "
               f"(min {min(mastery)}, max {max(mastery)})")
    m, s = m_s(top_on)
    out.append(f"  Top-5 prefs ON attractor : {m:7.2f} +/- {s:6.2f}")
    m, s = m_s(top_near)
    out.append(f"  Top-5 prefs NEAR attractor: {m:7.2f} +/- {s:6.2f}")

    # Rule adherence
    out.append("")
    out.append("RULE ADHERENCE ACROSS ALL RUNS")
    out.append("-" * 82)
    total_frame = sum(r["frame_attempts_total"] for r in all_results)
    total_hazard = sum(r["hazard_attempts_total"] for r in all_results)
    p3_frame = sum(r["frame_attempts_p3"] for r in all_results)
    p3_hazard = sum(r["hazard_attempts_p3"] for r in all_results)
    out.append(f"  Total frame-directed attempts  : {total_frame}")
    out.append(f"  Total hazard-directed attempts : {total_hazard}")
    out.append(f"  Phase 3 frame-directed         : {p3_frame}")
    out.append(f"  Phase 3 hazard-directed        : {p3_hazard}")
    clean_runs = sum(1 for r in all_results
                     if r["frame_attempts_total"] == 0 and r["hazard_attempts_total"] == 0)
    out.append(f"  Runs with zero rule violations : {clean_runs}/{n}")

    # Attractor individuation
    out.append("")
    out.append("ATTRACTOR INDIVIDUATION")
    out.append("-" * 82)
    top_attractors_chosen = Counter(r["top_attractor"] for r in all_results)
    for attr, count in top_attractors_chosen.most_common():
        out.append(f"  {attr} chosen as top by {count}/{n} runs")
    n_distinct = len(top_attractors_chosen)
    out.append(f"  Number of distinct top attractors: {n_distinct}/6 available")

    # Distribution bands
    high_conc = sum(1 for c in p3_conc if c >= 20.0)
    mod_conc = sum(1 for c in p3_conc if 10.0 <= c < 20.0)
    low_conc = sum(1 for c in p3_conc if c < 10.0)
    out.append("")
    out.append("PHASE 3 CONCENTRATION DISTRIBUTION")
    out.append("-" * 82)
    out.append(f"  High (>= 20x uniform) : {high_conc}/{n}")
    out.append(f"  Moderate (10-20x)     : {mod_conc}/{n}")
    out.append(f"  Low (< 10x)           : {low_conc}/{n}")

    strong_feat = sum(1 for f in p3_feat if f >= 5.0)
    mod_feat = sum(1 for f in p3_feat if 2.0 <= f < 5.0)
    weak_feat = sum(1 for f in p3_feat if f < 2.0)
    out.append("")
    out.append("PHASE 3 ATTRACTOR RATIO DISTRIBUTION")
    out.append("-" * 82)
    out.append(f"  Very strong (>= 5x chance) : {strong_feat}/{n}")
    out.append(f"  Moderate (2-5x)            : {mod_feat}/{n}")
    out.append(f"  Weak (< 2x)                : {weak_feat}/{n}")

    # Interpretation
    out.append("")
    out.append("=" * 82)
    out.append("INTERPRETATION")
    out.append("=" * 82)
    out.append("")

    mean_conc = np.mean(p3_conc)
    mean_p3_feat = np.mean(p3_feat)
    mean_on = np.mean(top_on)

    if clean_runs == n:
        out.append("RULE ADHERENCE IS UNIVERSAL. Across all runs, zero frame-directed and")
        out.append("zero hazard-directed attempts. The primitive aversion system holds without")
        out.append("exception. Rules created architecturally are retained architecturally, not")
        out.append("eroded by the pressures of drive-based exploration or preference formation.")
    else:
        out.append(f"RULE ADHERENCE HOLDS IN MOST RUNS ({clean_runs}/{n}) but not all. The")
        out.append("primitive aversion system is robust but not absolute under the pressures")
        out.append("that emerge during Phase 2 and Phase 3.")

    if mean_conc >= 20 and high_conc >= 0.8 * n:
        out.append("")
        out.append("FOCUSED AUTONOMY IS ARCHITECTURAL AT SCALE. The concentration behaviour")
        out.append("first observed in the 10x10 world generalises cleanly to the structured")
        out.append("20x20 environment. The larger neutral field, rather than diffusing focus,")
        out.append("appears to reinforce it — attractors stand out more clearly against the")
        out.append("larger context they inhabit.")

    if mean_p3_feat >= 5.0 and strong_feat >= 0.6 * n:
        out.append("")
        out.append("FEATURE AFFINITY HAS BECOME ROBUST. The bimodality observed in the")
        out.append("10x10 environment is not present here. Across most runs, agents visit")
        out.append("attractor cells at several times chance rate and settle preferences on")
        out.append("them. The larger environment makes feature alignment easier, not harder,")
        out.append("because it increases the proportional reward differential between")
        out.append("attractor trajectories and neutral trajectories.")

    if mean_on >= 2.5:
        out.append("")
        out.append("PREFERENCES CONSISTENTLY LAND ON ATTRACTORS. On average, more than half")
        out.append("of each agent's top-5 preferred cells are attractor cells themselves.")
        out.append("The v0.7.1 'preferences land near but not on features' phenomenon has")
        out.append("been resolved by the combination of larger scale and extrinsic valuing.")

    if n_distinct >= 4:
        out.append("")
        out.append("AGENTS INDIVIDUATE. Different runs settle on different attractors as")
        out.append("their primary focus, demonstrating that the architecture does not collapse")
        out.append("all agents onto the same outcome. This is developmentally significant —")
        out.append("the architecture produces learners whose preferences genuinely differ,")
        out.append("shaped by the stochasticity of early Phase 2 trajectories.")
    elif n_distinct <= 2:
        out.append("")
        out.append("AGENTS CONVERGE. Across runs, most settle on the same one or two")
        out.append("attractors. This suggests the architecture produces consistent focus")
        out.append("targets rather than individuated preferences — possibly a consequence")
        out.append("of specific placement of attractors relative to the starting position.")

    return "\n".join(out)


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main():
    print(f"Running {NUM_RUNS} independent lives of the v0.8 agent...")
    print(f"Each run = {NUM_STEPS} steps in a 20x20 structured environment.")
    print()
    all_results = []
    start = time.time()

    for i in range(NUM_RUNS):
        r = single_run()
        all_results.append(r)
        rule_viol = r["frame_attempts_total"] + r["hazard_attempts_total"]
        print(f"  Run {i+1:2d}/{NUM_RUNS}: P3 conc={r['p3_concentration']:6.1f}x  "
              f"P3 feat={r['p3_attractor_ratio']:5.2f}  "
              f"mast={r['mastered_count']:3d}  "
              f"on={r['top_on_attractor']}/5  "
              f"near={r['top_near_attractor']}/5  "
              f"rule_viol={rule_viol}  "
              f"top_attr={r['top_attractor']}")

    total_time = time.time() - start
    print(f"\nAll runs complete in {total_time:.1f} seconds.")

    report = aggregate_and_report(all_results)
    print()
    print(report)

    with open("meta_report_v0_8.txt", "w") as f:
        f.write(report)
    print(f"\nMeta-report saved to meta_report_v0_8.txt")


if __name__ == "__main__":
    main()
