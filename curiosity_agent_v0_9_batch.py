"""
curiosity_agent_v0_9_batch.py
-----------------------------
Batch runner for the v0.9 developmental agent in the 20x20 structured
environment, covering Designs A and C as specified in
v0.9-preregistration-amended.md.

Purpose: move from the four v0.9 single-run probes (all showing full
survival in Design A at cost = 0.1, 1.0, 5.0, 10.0; and a learning
signature in Design C at cost = 1.0) to a distributional characterisation
across 140 runs. Per the pre-registration:

  DESIGN A — does pre-wired aversion bias sustain hazard avoidance when
             the architectural wall is removed?
    hazard_mode = "cost" across six cost levels, 10 runs each (60 runs)
    plus 10 control runs with hazard_mode = "impassable"       (10 runs)
    Total Design A:                                              70 runs

  DESIGN C — can hazard avoidance be learned from experienced cost alone,
             without pre-wired aversion?
    hazard_mode = "cost_no_aversion" across six cost levels,
        10 runs each                                             (60 runs)
    plus 10 control runs with hazard_mode = "impassable_no_aversion"
                                                                (10 runs)
    Total Design C:                                              70 runs

  Grand total: 140 runs.

Cost levels are log-spaced: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0.

Per-run metrics captured (in addition to v0.8's set):
  - hazard_entries_p2:   actual entries during Phase 2
  - hazard_entries_p3:   actual entries during Phase 3
  - total_cost:          sum of cost incurred across the run
  - rule_violated_total: 1 if total hazard entries >= 3, else 0
                         (pre-registered threshold-crossing metric)
  - rule_violated_p3:    1 if Phase 3 entries >= 3, else 0
                         (Design C interpretation metric — see amended
                          pre-registration commentary)

Meta-report grouped by hazard_mode and cost level. Threshold-crossing
reported per mode per cost level. Cross-design comparison at equivalent
cost levels reported as a separate section.

Run from Terminal with:
    python3 curiosity_agent_v0_9_batch.py

Expected duration: several hours on an M4 MacBook. 140 runs at 20,000
steps each.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
from collections import defaultdict, deque, Counter
import time

# --------------------------------------------------------------------------
# CONFIG (matches v0.9 single-run exactly)
# --------------------------------------------------------------------------

NUM_RUNS_PER_CELL = 10      # runs per (mode, cost) cell
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

# Cost levels from pre-registration (log-spaced)
COST_LEVELS = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

# Modes to run. Order matters: Design A first, then Design C (per
# implementation sequence specified in pre-registration amendment).
EXPERIMENTAL_MODES = [
    ("cost", "Design A experimental: no wall, aversion retained"),
    ("cost_no_aversion", "Design C experimental: no wall, no aversion"),
]
CONTROL_MODES = [
    ("impassable", "Design A control: v0.8 behaviour"),
    ("impassable_no_aversion", "Design C control: wall, no aversion"),
]

HAZARD_CLUSTERS = [
    [(5, 8), (5, 9), (6, 8)],
    [(14, 13), (14, 14)],
]
ATTRACTOR_CELLS = [
    (3, 3), (16, 3), (9, 10), (4, 15), (15, 16), (11, 5)
]
START_CELL = (1, 1)

# Threshold-crossing definition (pre-registered)
RULE_VIOLATED_THRESHOLD = 3  # >= this many entries counts as rule violated


def _hazard_is_impassable(mode):
    return mode in ("impassable", "impassable_no_aversion")


def _hazard_has_aversion(mode):
    return mode in ("impassable", "cost")


# --------------------------------------------------------------------------
# ENVIRONMENT (identical to v0.9 single-run, parameterised by mode)
# --------------------------------------------------------------------------

class StructuredGridWorld:
    def __init__(self, hazard_mode, hazard_cost, size=GRID_SIZE):
        self.size = size
        self.hazard_mode = hazard_mode
        self.hazard_cost = hazard_cost
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

    def is_passable_for_path_planning(self, cell):
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
        """Returns (observation, attempted_cell, success, cost_incurred).
        Matches v0.9 single-run semantics exactly.
        """
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

        if target_type == FRAME:
            return self.observe(), target, False, 0.0

        if target_type == HAZARD:
            if _hazard_is_impassable(self.hazard_mode):
                return self.observe(), target, False, 0.0
            else:
                self.agent_pos = target
                return self.observe(), target, True, self.hazard_cost

        self.agent_pos = target
        return self.observe(), target, True, 0.0


# --------------------------------------------------------------------------
# PATH PLANNING FOR PHASE 1 (identical to v0.8/v0.9 single-run)
# --------------------------------------------------------------------------

def plan_phase_1_path(world, start=START_CELL):
    size = world.size
    path = [start]
    visited = {start}

    for y in range(1, size - 1):
        row_cells_ltr = [(x, y) for x in range(1, size - 1)
                         if world.is_passable_for_path_planning((x, y))]
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
            if not world.is_passable_for_path_planning(nxt):
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
# AGENT (identical to v0.9 single-run, parameterised by mode)
# --------------------------------------------------------------------------

class DevelopmentalAgent:
    def __init__(self, world, total_steps, hazard_mode, num_actions=4):
        self.world = world
        self.hazard_mode = hazard_mode
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
        self.hazard_entries_by_phase = {1: 0, 2: 0, 3: 0}
        self.total_cost_incurred = 0.0

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
        hazard_has_aversion = _hazard_has_aversion(self.hazard_mode)
        for i, t in enumerate(adj_types):
            if t == FRAME:
                biases[i] = AVERSION_PENALTY
            elif t == HAZARD and hazard_has_aversion:
                biases[i] = AVERSION_PENALTY
            elif t == ATTRACTOR:
                biases[i] = ATTRACTION_BONUS
        return biases

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            biases = self._primitive_bias(state)
            valid = [a for a in range(self.num_actions)
                     if biases[a] > AVERSION_PENALTY / 2]
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

    def record_action_outcome(self, target_cell, success, cost_incurred, world):
        if not success:
            t = world.cell_type.get(target_cell, FRAME)
            if t == FRAME:
                self.frame_attempts_by_phase[self.phase] += 1
            elif t == HAZARD:
                self.hazard_attempts_by_phase[self.phase] += 1
            return
        if cost_incurred > 0:
            self.hazard_entries_by_phase[self.phase] += 1
            self.total_cost_incurred += cost_incurred


# --------------------------------------------------------------------------
# SINGLE RUN (batch-internal, no plotting, returns dict of metrics)
# --------------------------------------------------------------------------

def single_run(hazard_mode, hazard_cost):
    np.random.seed(None)
    world = StructuredGridWorld(hazard_mode=hazard_mode, hazard_cost=hazard_cost)
    agent = DevelopmentalAgent(world, NUM_STEPS, hazard_mode=hazard_mode)
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

        next_state, target_cell, success, cost_incurred = world.step(action)
        agent.record_action_outcome(target_cell, success, cost_incurred, world)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        r_feature = agent.feature_reward(next_state)
        intrinsic = r_novelty + r_progress + r_preference + r_feature - cost_incurred

        agent.update_model(state, action, next_state, error, r_progress, r_feature)
        agent.update_values(state, action, next_state, intrinsic)

        x, y = next_state[0], next_state[1]
        heatmap_by_phase[agent.phase][y, x] += 1
        state = next_state

    # --- analysis ---
    def attractor_ratio(heatmap):
        total = heatmap.sum()
        if total == 0:
            return 0.0
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

    # Top attractor by Phase 3 visits (same definition as v0.8 batch)
    attractor_p3_visits = {a: int(heatmap_by_phase[3][a[1], a[0]]) for a in ATTRACTOR_CELLS}
    top_attractor = max(attractor_p3_visits, key=attractor_p3_visits.get)

    mastered = sum(
        1 for errs in agent.fast_errors.values()
        if len(errs) >= 5 and np.mean(errs) < 0.15
    )

    entries_p1 = agent.hazard_entries_by_phase[1]
    entries_p2 = agent.hazard_entries_by_phase[2]
    entries_p3 = agent.hazard_entries_by_phase[3]
    entries_total = entries_p1 + entries_p2 + entries_p3

    return {
        "hazard_mode": hazard_mode,
        "hazard_cost": hazard_cost,
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

        # v0.8-style rule adherence (blocked attempts)
        "frame_attempts_total": sum(agent.frame_attempts_by_phase.values()),
        "hazard_attempts_total": sum(agent.hazard_attempts_by_phase.values()),
        "frame_attempts_p3": agent.frame_attempts_by_phase[3],
        "hazard_attempts_p3": agent.hazard_attempts_by_phase[3],

        # v0.9-specific: actual entries under cost modes
        "hazard_entries_p1": entries_p1,
        "hazard_entries_p2": entries_p2,
        "hazard_entries_p3": entries_p3,
        "hazard_entries_total": entries_total,
        "total_cost_incurred": agent.total_cost_incurred,

        # Threshold-crossing metrics
        "rule_violated_total": 1 if entries_total >= RULE_VIOLATED_THRESHOLD else 0,
        "rule_violated_p3": 1 if entries_p3 >= RULE_VIOLATED_THRESHOLD else 0,
    }


# --------------------------------------------------------------------------
# META-REPORT
# --------------------------------------------------------------------------

def aggregate_and_report(all_results):
    """Produce the v0.9 meta-report.

    Structure:
      1. Per-run table, grouped by (mode, cost)
      2. Central tendencies by (mode, cost)
      3. Rule adherence summary by mode
      4. Threshold analysis (both metrics)
      5. Attractor individuation (by mode, to compare against v0.8)
      6. Concentration / feature-ratio distributions
      7. Cross-design comparison (A vs C at equivalent cost levels)
      8. Interpretation
    """
    out = []
    n_total = len(all_results)

    # Group results by (mode, cost)
    groups = defaultdict(list)
    for r in all_results:
        key = (r["hazard_mode"], r["hazard_cost"])
        groups[key].append(r)

    out.append("=" * 94)
    out.append(f"META-REPORT: v0.9 COST-BASED HAZARDS — {n_total} RUNS ACROSS {len(groups)} CONDITIONS")
    out.append("=" * 94)
    out.append("")
    out.append("Cost levels: " + ", ".join(str(c) for c in COST_LEVELS))
    out.append(f"Runs per condition: {NUM_RUNS_PER_CELL}")
    out.append(f"Life length per run: {NUM_STEPS} steps")
    out.append(f"Threshold-crossing defined as: hazard entries >= {RULE_VIOLATED_THRESHOLD}")
    out.append("")

    # --- 1. Per-run table ---
    out.append("PER-RUN RESULTS (grouped by mode and cost)")
    out.append("-" * 94)
    out.append(
        f"{'mode':>22} | {'cost':>5} | {'run':>3} | "
        f"{'P3conc':>6} | {'P3feat':>6} | {'mast':>4} | "
        f"{'on':>2} | {'ent P2':>6} | {'ent P3':>6} | {'cost':>6} | {'viol':>4}"
    )
    out.append("-" * 94)

    def sort_key(kv):
        mode, cost = kv
        mode_order = {
            "impassable": 0,
            "cost": 1,
            "impassable_no_aversion": 2,
            "cost_no_aversion": 3,
        }
        return (mode_order.get(mode, 99), cost)

    for (mode, cost) in sorted(groups.keys(), key=sort_key):
        group_runs = groups[(mode, cost)]
        for i, r in enumerate(group_runs, 1):
            viol_mark = "YES" if r["rule_violated_total"] else "no"
            out.append(
                f"{mode:>22} | {cost:>5.1f} | {i:>3} | "
                f"{r['p3_concentration']:>6.1f} | "
                f"{r['p3_attractor_ratio']:>6.2f} | "
                f"{r['mastered_count']:>4d} | "
                f"{r['top_on_attractor']:>2d} | "
                f"{r['hazard_entries_p2']:>6d} | "
                f"{r['hazard_entries_p3']:>6d} | "
                f"{r['total_cost_incurred']:>6.1f} | "
                f"{viol_mark:>4}"
            )
        out.append("-" * 94)

    # --- 2. Central tendencies by (mode, cost) ---
    def m_s(values):
        if not values:
            return 0.0, 0.0
        return float(np.mean(values)), float(np.std(values))

    out.append("")
    out.append("CENTRAL TENDENCIES BY CONDITION (mean +/- std)")
    out.append("-" * 94)
    out.append(
        f"{'mode':>22} | {'cost':>5} | "
        f"{'P3conc':>13} | {'P3feat':>13} | {'mast':>11} | "
        f"{'entries':>11} | {'cost':>11}"
    )
    out.append("-" * 94)
    for (mode, cost) in sorted(groups.keys(), key=sort_key):
        runs = groups[(mode, cost)]
        mc, sc = m_s([r["p3_concentration"] for r in runs])
        mf, sf = m_s([r["p3_attractor_ratio"] for r in runs])
        mm, sm = m_s([r["mastered_count"] for r in runs])
        me, se = m_s([r["hazard_entries_total"] for r in runs])
        mcost, scost = m_s([r["total_cost_incurred"] for r in runs])
        out.append(
            f"{mode:>22} | {cost:>5.1f} | "
            f"{mc:>6.1f}+/-{sc:>4.1f} | "
            f"{mf:>6.2f}+/-{sf:>4.2f} | "
            f"{mm:>5.1f}+/-{sm:>4.1f} | "
            f"{me:>5.1f}+/-{se:>4.1f} | "
            f"{mcost:>5.1f}+/-{scost:>4.1f}"
        )

    # --- 3. Rule adherence summary by mode ---
    out.append("")
    out.append("RULE ADHERENCE BY MODE")
    out.append("-" * 94)
    for mode_name, _desc in EXPERIMENTAL_MODES + CONTROL_MODES:
        mode_runs = [r for r in all_results if r["hazard_mode"] == mode_name]
        if not mode_runs:
            continue
        total_entries = sum(r["hazard_entries_total"] for r in mode_runs)
        total_attempts = sum(r["hazard_attempts_total"] for r in mode_runs)
        clean_runs = sum(1 for r in mode_runs
                         if r["hazard_entries_total"] == 0
                         and r["hazard_attempts_total"] == 0)
        violated_total = sum(r["rule_violated_total"] for r in mode_runs)
        violated_p3 = sum(r["rule_violated_p3"] for r in mode_runs)
        out.append(f"  {mode_name}:")
        out.append(f"    Runs                              : {len(mode_runs)}")
        out.append(f"    Total hazard entries (all runs)   : {total_entries}")
        out.append(f"    Total hazard blocked attempts     : {total_attempts}")
        out.append(f"    Runs with zero entries & attempts : {clean_runs}/{len(mode_runs)}")
        out.append(f"    Runs with rule_violated_total=YES : {violated_total}/{len(mode_runs)}")
        out.append(f"    Runs with rule_violated_p3=YES    : {violated_p3}/{len(mode_runs)}")
        out.append("")

    # --- 4. Threshold analysis ---
    out.append("THRESHOLD ANALYSIS BY COST LEVEL")
    out.append("-" * 94)
    out.append("A cost level is 'threshold crossed' when a majority of runs at that level")
    out.append(f"have >= {RULE_VIOLATED_THRESHOLD} hazard entries (pre-registered definition).")
    out.append("")
    out.append("Pre-registered metric (total entries):")
    out.append(f"{'mode':>22} | " + " | ".join(f"c={c:>4}" for c in COST_LEVELS))
    out.append("-" * 94)
    for mode in ["cost", "cost_no_aversion"]:
        row = [f"{mode:>22}"]
        for c in COST_LEVELS:
            runs = groups.get((mode, c), [])
            if not runs:
                row.append("  n/a  ")
                continue
            violated = sum(r["rule_violated_total"] for r in runs)
            n = len(runs)
            crossed = "X" if violated > n / 2 else "-"
            row.append(f" {violated:>2}/{n:<2}{crossed}")
        out.append(" | ".join(row))
    out.append("")
    out.append("Design-C-relevant metric (Phase 3 entries only):")
    out.append(f"{'mode':>22} | " + " | ".join(f"c={c:>4}" for c in COST_LEVELS))
    out.append("-" * 94)
    for mode in ["cost", "cost_no_aversion"]:
        row = [f"{mode:>22}"]
        for c in COST_LEVELS:
            runs = groups.get((mode, c), [])
            if not runs:
                row.append("  n/a  ")
                continue
            violated = sum(r["rule_violated_p3"] for r in runs)
            n = len(runs)
            crossed = "X" if violated > n / 2 else "-"
            row.append(f" {violated:>2}/{n:<2}{crossed}")
        out.append(" | ".join(row))
    out.append("")

    # --- 5. Attractor individuation by mode ---
    out.append("ATTRACTOR INDIVIDUATION BY MODE")
    out.append("-" * 94)
    for mode_name, _desc in EXPERIMENTAL_MODES + CONTROL_MODES:
        mode_runs = [r for r in all_results if r["hazard_mode"] == mode_name]
        if not mode_runs:
            continue
        counts = Counter(r["top_attractor"] for r in mode_runs)
        n_distinct = len(counts)
        out.append(f"  {mode_name} ({len(mode_runs)} runs):")
        for attr, count in counts.most_common():
            out.append(f"    {attr} chosen as top by {count}/{len(mode_runs)}")
        out.append(f"    Distinct top attractors: {n_distinct}/6 available")
        out.append("")

    # --- 6. Concentration and feature-ratio distributions ---
    out.append("PHASE 3 CONCENTRATION DISTRIBUTION BY MODE")
    out.append("-" * 94)
    for mode_name, _desc in EXPERIMENTAL_MODES + CONTROL_MODES:
        mode_runs = [r for r in all_results if r["hazard_mode"] == mode_name]
        if not mode_runs:
            continue
        conc_values = [r["p3_concentration"] for r in mode_runs]
        high = sum(1 for c in conc_values if c >= 20)
        mod = sum(1 for c in conc_values if 10 <= c < 20)
        low = sum(1 for c in conc_values if c < 10)
        out.append(f"  {mode_name}: "
                   f"high(>=20x)={high}/{len(mode_runs)}, "
                   f"mod(10-20x)={mod}/{len(mode_runs)}, "
                   f"low(<10x)={low}/{len(mode_runs)}")

    out.append("")
    out.append("PHASE 3 ATTRACTOR RATIO DISTRIBUTION BY MODE")
    out.append("-" * 94)
    for mode_name, _desc in EXPERIMENTAL_MODES + CONTROL_MODES:
        mode_runs = [r for r in all_results if r["hazard_mode"] == mode_name]
        if not mode_runs:
            continue
        feat_values = [r["p3_attractor_ratio"] for r in mode_runs]
        strong = sum(1 for f in feat_values if f >= 5)
        mod = sum(1 for f in feat_values if 2 <= f < 5)
        weak = sum(1 for f in feat_values if f < 2)
        out.append(f"  {mode_name}: "
                   f"strong(>=5x)={strong}/{len(mode_runs)}, "
                   f"mod(2-5x)={mod}/{len(mode_runs)}, "
                   f"weak(<2x)={weak}/{len(mode_runs)}")

    # --- 7. Cross-design comparison ---
    out.append("")
    out.append("CROSS-DESIGN COMPARISON: DESIGN A vs DESIGN C AT EQUIVALENT COST LEVELS")
    out.append("-" * 94)
    out.append(
        f"{'cost':>5} | {'A entries mean':>14} | {'C entries mean':>14} | "
        f"{'A viol/10':>10} | {'C viol/10':>10}"
    )
    out.append("-" * 94)
    for c in COST_LEVELS:
        a_runs = groups.get(("cost", c), [])
        c_runs = groups.get(("cost_no_aversion", c), [])
        if not a_runs or not c_runs:
            continue
        a_entries = np.mean([r["hazard_entries_total"] for r in a_runs])
        c_entries = np.mean([r["hazard_entries_total"] for r in c_runs])
        a_viol = sum(r["rule_violated_total"] for r in a_runs)
        c_viol = sum(r["rule_violated_total"] for r in c_runs)
        out.append(
            f"{c:>5.1f} | {a_entries:>14.1f} | {c_entries:>14.1f} | "
            f"{a_viol:>6}/{len(a_runs):<3} | {c_viol:>6}/{len(c_runs):<3}"
        )

    # --- 8. Interpretation (brief; detailed analysis for paper) ---
    out.append("")
    out.append("=" * 94)
    out.append("INTERPRETATION (summary only — detailed analysis reserved for preprint)")
    out.append("=" * 94)
    out.append("")

    # Design A finding
    cost_runs_all = [r for r in all_results if r["hazard_mode"] == "cost"]
    if cost_runs_all:
        cost_entries_any = sum(1 for r in cost_runs_all if r["hazard_entries_total"] > 0)
        if cost_entries_any == 0:
            out.append("DESIGN A: FULL SURVIVAL. No hazard entries at any cost level. Pre-wired")
            out.append("aversion bias is sufficient to sustain hazard avoidance when the")
            out.append("architectural wall is removed. v0.8's zero-violation result is reproduced")
            out.append("by the bias alone, across the full pre-registered cost range.")
        else:
            out.append(f"DESIGN A: {cost_entries_any}/{len(cost_runs_all)} runs show some hazard entries.")
            out.append("See threshold analysis table above for cost-level breakdown.")
    out.append("")

    # Design C finding
    cnr_runs_all = [r for r in all_results if r["hazard_mode"] == "cost_no_aversion"]
    if cnr_runs_all:
        # Count P3-clean runs (learning succeeded) vs P3-violated (no learning)
        cnr_p3_clean = sum(1 for r in cnr_runs_all if r["hazard_entries_p3"] == 0)
        cnr_p3_violated = len(cnr_runs_all) - cnr_p3_clean
        out.append(f"DESIGN C: {cnr_p3_clean}/{len(cnr_runs_all)} runs show zero Phase 3 entries,")
        out.append(f"          {cnr_p3_violated}/{len(cnr_runs_all)} runs show some Phase 3 entries.")
        out.append("See threshold analysis tables above for cost-level breakdown by both metrics.")

    return "\n".join(out)


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main(num_steps=None, design_c_only=False):
    """Run the v0.9 batch.

    Parameters
    ----------
    num_steps : int, optional
        Life length per run. Defaults to NUM_STEPS (20000).
    design_c_only : bool
        If True, skip Design A runs (the "cost" experimental condition
        and the "impassable" control). Used for the extended-run-length
        follow-up experiment pre-registered in
        v0.9-preregistration-amendment-2.md, where Design A's full-survival
        result at 20,000 steps makes extended-length Design A runs
        uninformative.
    """
    # Allow override of module-level NUM_STEPS (used inside single_run)
    if num_steps is not None:
        global NUM_STEPS
        NUM_STEPS = num_steps

    run_specs = []

    if not design_c_only:
        # Design A
        for c in COST_LEVELS:
            for _ in range(NUM_RUNS_PER_CELL):
                run_specs.append(("cost", c))
        for _ in range(NUM_RUNS_PER_CELL):
            run_specs.append(("impassable", 0.0))  # cost placeholder; unused

    # Design C (always included)
    for c in COST_LEVELS:
        for _ in range(NUM_RUNS_PER_CELL):
            run_specs.append(("cost_no_aversion", c))
    for _ in range(NUM_RUNS_PER_CELL):
        run_specs.append(("impassable_no_aversion", 0.0))

    total_runs = len(run_specs)

    # Output filenames include run length and design subset so different
    # batches don't overwrite each other. Default 20000-step full batch
    # preserves the original filenames for continuity with the committed
    # meta_report_v0_9.txt and run_data_v0_9.csv.
    if num_steps is None and not design_c_only:
        report_filename = "meta_report_v0_9.txt"
        csv_filename = "run_data_v0_9.csv"
    else:
        subset_tag = "_Conly" if design_c_only else "_full"
        steps_tag = f"_s{NUM_STEPS}"
        report_filename = f"meta_report_v0_9{subset_tag}{steps_tag}.txt"
        csv_filename = f"run_data_v0_9{subset_tag}{steps_tag}.csv"

    print(f"v0.9 BATCH")
    print(f"  Total runs: {total_runs}")
    print(f"  Life length per run: {NUM_STEPS} steps")
    print(f"  Cost levels: {COST_LEVELS}")
    print(f"  Runs per condition: {NUM_RUNS_PER_CELL}")
    print(f"  Design subset: {'Design C only' if design_c_only else 'Full (A + C)'}")
    print(f"  Output files: {report_filename}, {csv_filename}")
    print()

    all_results = []
    batch_start = time.time()

    for i, (mode, cost) in enumerate(run_specs, 1):
        run_start = time.time()
        r = single_run(hazard_mode=mode, hazard_cost=cost)
        all_results.append(r)
        run_duration = time.time() - run_start
        elapsed = time.time() - batch_start
        eta = (elapsed / i) * (total_runs - i)

        viol = "VIOL" if r["rule_violated_total"] else "ok"
        print(
            f"  Run {i:>3}/{total_runs}: "
            f"mode={mode:>22} c={cost:>4.1f}  "
            f"P3conc={r['p3_concentration']:>6.1f} "
            f"entries P2={r['hazard_entries_p2']:>3} P3={r['hazard_entries_p3']:>3} "
            f"cost={r['total_cost_incurred']:>5.1f} "
            f"{viol:>4}  "
            f"[{run_duration:>4.1f}s, ETA {eta/60:>5.1f}m]"
        )

    total_duration = time.time() - batch_start
    print(f"\nAll {total_runs} runs complete in {total_duration/60:.1f} minutes.")

    report = aggregate_and_report(all_results)
    print()
    print(report)

    with open(report_filename, "w") as f:
        f.write(report)
    print(f"\nMeta-report saved to {report_filename}")

    import csv
    csv_keys = [
        "hazard_mode", "hazard_cost",
        "p3_concentration", "p3_attractor_ratio", "p2_attractor_ratio",
        "mastered_count", "top_on_attractor", "top_near_attractor",
        "top_attractor",
        "hazard_entries_p1", "hazard_entries_p2", "hazard_entries_p3",
        "hazard_entries_total", "total_cost_incurred",
        "rule_violated_total", "rule_violated_p3",
        "frame_attempts_total", "hazard_attempts_total",
    ]
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_keys)
        writer.writeheader()
        for r in all_results:
            row = {k: r.get(k, "") for k in csv_keys}
            writer.writerow(row)
    print(f"Per-run data saved to {csv_filename}")

    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="v0.9 batch runner. Default: 140 runs at 20000 steps."
    )
    parser.add_argument(
        "--steps", type=int, default=None,
        help="Life length per run. Default: 20000 (from module config)."
    )
    parser.add_argument(
        "--design-c-only", action="store_true",
        help="Skip Design A runs. Used for extended-run-length follow-up."
    )
    args = parser.parse_args()
    main(num_steps=args.steps, design_c_only=args.design_c_only)
