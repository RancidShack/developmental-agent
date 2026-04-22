"""
curiosity_agent_v0_9.py
-----------------------
Developmental agent in a 20x20 structured environment — v0.9 extension
of v0.8 testing whether hazard avoidance in v0.8 is sustained by
pre-wired aversion bias alone, and/or learnable from experienced cost
without the pre-wired bias.

This is a minimal extension of v0.8. Only the hazard handler and its
supporting plumbing change. All other code paths — environment layout,
drives, phase structure, Phase 1 path planner, analysis pipeline — are
identical to v0.8.

See v0.9-preregistration-amended.md for the full experimental design.

HAZARD_MODE CONFIG FLAG
  "impassable"             - v0.8 behaviour. Wall + HAZARD aversion +
                             HAZARD epsilon filter. Control for Design A.
  "impassable_no_aversion" - Wall, no HAZARD aversion, no HAZARD filter.
                             Control for Design C.
  "cost"                   - No wall, HAZARD aversion retained, filter
                             retained. Experimental condition for Design A.
  "cost_no_aversion"       - No wall, no HAZARD aversion, no HAZARD filter.
                             Experimental condition for Design C.

FRAME cells are unaffected by HAZARD_MODE. Frames are ontological
boundaries (edge of the world), not normative rules. They remain
impassable and their aversion bias is retained in every mode.

COST MECHANISM (used in "cost" and "cost_no_aversion" modes)
  When the agent enters a hazard cell, HAZARD_COST is subtracted from
  the intrinsic reward for that step. The cost affects only the reward
  signal at that step; it does not modify cell_preference directly, and
  does not persist as a separate penalty state. This is the more
  conservative single-variable implementation discussed prior to coding.

Run from Terminal with:
    python3 curiosity_agent_v0_9.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

GRID_SIZE = 20
NUM_STEPS = 20000
PHASE_3_START_FRACTION = 0.6
Q_VALUE_RESET_MULTIPLIER = 0.3
FEATURE_DRIVE_WEIGHT = 0.15

# Cell type constants
FRAME = 0
NEUTRAL = 1
HAZARD = 2
ATTRACTOR = 3

# Primitive structures
AVERSION_PENALTY = -5.0      # applied to FRAME always; to HAZARD in
                             # "impassable" and "cost" modes only
ATTRACTION_BONUS = 0.3

# v0.9 additions
HAZARD_MODE = "cost"         # one of: "impassable", "impassable_no_aversion",
                             # "cost", "cost_no_aversion"
HAZARD_COST = 1.0            # scalar subtracted from intrinsic reward on
                             # hazard entry; only applies in cost modes

# Environment content: placed deterministically so batch runs are comparable
HAZARD_CLUSTERS = [
    [(5, 8), (5, 9), (6, 8)],
    [(14, 13), (14, 14)],
]
ATTRACTOR_CELLS = [
    (3, 3), (16, 3), (9, 10), (4, 15), (15, 16), (11, 5)
]
START_CELL = (1, 1)


# Valid hazard modes — used for config validation
VALID_HAZARD_MODES = {
    "impassable",
    "impassable_no_aversion",
    "cost",
    "cost_no_aversion",
}


def _validate_config():
    if HAZARD_MODE not in VALID_HAZARD_MODES:
        raise ValueError(
            f"HAZARD_MODE must be one of {VALID_HAZARD_MODES}, got {HAZARD_MODE!r}"
        )
    if HAZARD_COST < 0:
        raise ValueError(f"HAZARD_COST must be non-negative, got {HAZARD_COST}")


def _hazard_is_impassable():
    return HAZARD_MODE in ("impassable", "impassable_no_aversion")


def _hazard_has_aversion():
    return HAZARD_MODE in ("impassable", "cost")


# --------------------------------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------------------------------

class StructuredGridWorld:
    """A 20x20 grid with frame, neutral, hazard, and attractor cells.

    The agent starts at START_CELL. It can move one cell at a time in
    four cardinal directions.

    FRAME cells are always impassable (ontological boundary).
    HAZARD cells are impassable or cost-bearing depending on HAZARD_MODE.
    """

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
        # Scope: cells the agent can legitimately occupy during a run.
        # For Phase 1 path planning we treat only NEUTRAL and ATTRACTOR
        # as passable, so Phase 1 continues to route around hazards
        # regardless of hazard_mode — the prescribed path never
        # deliberately walks through a hazard. The cost only applies
        # if the agent chooses to enter a hazard in Phase 2/3.
        self.scope_cells = {
            c for c, t in self.cell_type.items()
            if t in (NEUTRAL, ATTRACTOR)
        }

    def is_passable_for_path_planning(self, cell):
        """Used only by plan_phase_1_path. Hazards are never in Phase 1
        paths; this is independent of HAZARD_MODE by design."""
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
        """Attempt a move.

        Returns (observation, attempted_cell, success, cost_incurred).

        cost_incurred is 0.0 except when the agent enters a HAZARD cell
        under a cost-based mode, in which case it is HAZARD_COST.

        FRAME cells are always blocked (agent stays put, success=False,
        cost=0.0).

        HAZARD cells are blocked when _hazard_is_impassable() is True
        (success=False, cost=0.0). Otherwise the agent enters and
        cost_incurred = HAZARD_COST.

        NEUTRAL and ATTRACTOR cells are always entered (success=True,
        cost=0.0).

        action: 0=up, 1=down, 2=left, 3=right
        """
        x, y = self.agent_pos
        if action == 0:
            target = (x, y - 1)
        elif action == 1:
            target = (x, y + 1)
        elif action == 2:
            target = (x - 1, y)
        elif action == 3:
            target = (x + 1, y)
        else:
            target = self.agent_pos

        # Bounds check — out-of-grid treated as FRAME
        if not (0 <= target[0] < self.size and 0 <= target[1] < self.size):
            target_type = FRAME
        else:
            target_type = self.cell_type[target]

        if target_type == FRAME:
            # Always blocked, always free. Ontological boundary.
            return self.observe(), target, False, 0.0

        if target_type == HAZARD:
            if _hazard_is_impassable():
                # Blocked, no cost (v0.8 behaviour or Design C control).
                return self.observe(), target, False, 0.0
            else:
                # Passable at cost (Design A or Design C experimental).
                self.agent_pos = target
                return self.observe(), target, True, HAZARD_COST

        # NEUTRAL or ATTRACTOR
        self.agent_pos = target
        return self.observe(), target, True, 0.0


# --------------------------------------------------------------------------
# PATH PLANNING FOR PHASE 1 (identical to v0.8)
# --------------------------------------------------------------------------

def plan_phase_1_path(world, start=START_CELL):
    """Generate a traversal of all passable interior cells.

    Phase 1 never deliberately routes through a hazard regardless of
    HAZARD_MODE. The prescribed path treats only NEUTRAL and ATTRACTOR
    cells as passable. This means the Phase 1 behaviour is identical
    across all four modes — any divergence in later phases is
    attributable to the hazard_mode manipulation, not to Phase 1.
    """
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
    """Shortest path from start to goal through passable cells."""
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
    """Convert a cell-path into a sequence of actions."""
    actions = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dy == -1:
            actions.append(0)
        elif dy == 1:
            actions.append(1)
        elif dx == -1:
            actions.append(2)
        elif dx == 1:
            actions.append(3)
        else:
            actions.append(0)
    return actions


# --------------------------------------------------------------------------
# AGENT
# --------------------------------------------------------------------------

class DevelopmentalAgent:
    """Extends v0.8's DevelopmentalAgent with hazard_mode-aware action
    selection and hazard-entry tracking.

    Changes from v0.8:
      - _primitive_bias(): HAZARD aversion applied only when
        _hazard_has_aversion() is True. FRAME aversion always applied.
      - choose_action() epsilon branch: HAZARD-directed actions filtered
        out only when _hazard_has_aversion() is True. FRAME-directed
        actions always filtered.
      - New tracking: hazard_entries_by_phase counts actual entries into
        hazard cells (distinct from hazard_attempts_by_phase, which
        counts blocked attempts as in v0.8).
    """

    def __init__(self, world, total_steps, num_actions=4):
        self.world = world
        self.scope = world.scope_cells
        self.total_steps = total_steps
        self.steps_taken = 0
        self.covered = set()
        self.num_actions = num_actions

        # Memory structures
        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.fast_errors = defaultdict(lambda: deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: deque(maxlen=30))
        self.cell_preference = defaultdict(float)
        self.q_values = defaultdict(float)

        # Phase tracking
        self.phase = 1
        self.phase_1_end_step = None
        self.phase_2_end_step = None
        self.phase_3_start_target = int(total_steps * PHASE_3_START_FRACTION)

        # Phase 1 prescribed path
        self.prescribed_path = plan_phase_1_path(world)
        self.prescribed_actions = path_to_actions(self.prescribed_path)
        self.path_index = 0

        # Learning parameters
        self.learning_rate = 0.1
        self.epsilon = 0.1

        # Rule-adherence tracking (v0.8-style: blocked attempts)
        self.frame_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_attempts_by_phase = {1: 0, 2: 0, 3: 0}

        # v0.9 addition: actual hazard entries (only possible in cost modes)
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
        """Compute Q-value biases from primitive aversion/attraction.

        FRAME always receives AVERSION_PENALTY (ontological boundary).
        HAZARD receives AVERSION_PENALTY only when _hazard_has_aversion()
        returns True — i.e. in "impassable" and "cost" modes. In
        "impassable_no_aversion" and "cost_no_aversion" modes, HAZARD
        cells receive no pre-wired bias; the agent must learn their
        valence from experience (or, in the impassable_no_aversion
        control, encounter the wall repeatedly without bias).

        ATTRACTOR always receives ATTRACTION_BONUS.
        """
        adj_types = state[3:7]
        biases = np.zeros(4)
        hazard_has_aversion = _hazard_has_aversion()
        for i, t in enumerate(adj_types):
            if t == FRAME:
                biases[i] = AVERSION_PENALTY
            elif t == HAZARD and hazard_has_aversion:
                biases[i] = AVERSION_PENALTY
            elif t == ATTRACTOR:
                biases[i] = ATTRACTION_BONUS
        return biases

    def choose_action(self, state):
        """Drive-based action selection, used in Phase 2 and 3.

        Combines learned Q-values with primitive biases. Epsilon-greedy
        exploration.

        The epsilon branch filters out actions with strongly negative
        bias — this means FRAME-directed actions are always filtered,
        and HAZARD-directed actions are filtered only when
        _hazard_has_aversion() is True. In no-aversion modes, the
        agent's random exploration can select hazard-directed actions.
        """
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
        """Update forward model, error windows, visit counts, preferences.

        Preferences accumulate progress + feature reward (unchanged from
        v0.7.1 and v0.8). The hazard cost does NOT feed into
        cell_preference directly — it affects only the intrinsic reward
        at the entry step. This preserves v0.8's representational
        structure; the only new mechanism is the scalar cost subtraction.
        """
        self.visit_counts[next_state] += 1
        self.forward_model[(state, action)][next_state] += 1
        self.fast_errors[(state, action)].append(error)
        self.slow_errors[(state, action)].append(error)
        cell = (next_state[0], next_state[1])
        if cell in self.scope:
            self.covered.add(cell)
        self.cell_preference[cell] += r_progress + r_feature

    def update_values(self, state, action, next_state, intrinsic):
        """Q-learning update. intrinsic has already had any hazard cost
        subtracted in the main loop before this function is called."""
        if self.phase == 1:
            return
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def record_action_outcome(self, target_cell, success, cost_incurred, world):
        """Track what happened with the attempted action.

        Three possible outcomes:
          - Blocked by FRAME: increment frame_attempts_by_phase.
          - Blocked by HAZARD: increment hazard_attempts_by_phase
            (only possible in impassable modes).
          - Entered a HAZARD with cost: increment hazard_entries_by_phase
            and accumulate cost (only possible in cost modes).
        """
        if not success:
            t = world.cell_type.get(target_cell, FRAME)
            if t == FRAME:
                self.frame_attempts_by_phase[self.phase] += 1
            elif t == HAZARD:
                self.hazard_attempts_by_phase[self.phase] += 1
            return
        # Successful move — check if we entered a hazard at cost
        if cost_incurred > 0:
            self.hazard_entries_by_phase[self.phase] += 1
            self.total_cost_incurred += cost_incurred


# --------------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------------

def run():
    _validate_config()

    world = StructuredGridWorld()
    agent = DevelopmentalAgent(world, NUM_STEPS)

    # Report config
    print(f"v0.9 single run")
    print(f"  HAZARD_MODE     : {HAZARD_MODE}")
    print(f"  HAZARD_COST     : {HAZARD_COST}")
    print(f"  Hazard impass.  : {_hazard_is_impassable()}")
    print(f"  Hazard aversion : {_hazard_has_aversion()}")
    print(f"  Environment     : {GRID_SIZE}x{GRID_SIZE}")
    print(f"  Passable scope  : {len(world.scope_cells)}")
    print(f"  Phase 1 path    : {len(agent.prescribed_actions)} steps")
    print()

    heatmap_by_phase = {1: np.zeros((GRID_SIZE, GRID_SIZE)),
                        2: np.zeros((GRID_SIZE, GRID_SIZE)),
                        3: np.zeros((GRID_SIZE, GRID_SIZE))}
    coverage_pct_trace = []
    progress_trace = []
    novelty_trace = []
    preference_trace = []
    feature_trace = []
    cost_trace = []  # v0.9 addition: per-step cost incurred
    mastered_count_trace = []

    state = world.observe()
    covered_at_phase_1_end = 0

    for step in range(NUM_STEPS):
        agent.steps_taken = step
        transitioned = agent.check_phase_transition()
        if transitioned and agent.phase == 2 and covered_at_phase_1_end == 0:
            covered_at_phase_1_end = len(agent.covered)

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

        coverage_pct_trace.append(100 * len(agent.covered) / len(agent.scope))
        progress_trace.append(r_progress)
        novelty_trace.append(r_novelty)
        preference_trace.append(r_preference)
        feature_trace.append(r_feature)
        cost_trace.append(cost_incurred)
        mastered_count_trace.append(sum(
            1 for errs in agent.fast_errors.values()
            if len(errs) >= 5 and np.mean(errs) < 0.15
        ))
        state = next_state

    # --- ANALYSIS ---
    top_preferred = sorted(agent.cell_preference.items(),
                           key=lambda kv: -kv[1])[:5]

    def attractor_ratio(heatmap):
        total = heatmap.sum()
        if total == 0:
            return 0.0
        attractor_visits = sum(heatmap[y, x] for (x, y) in ATTRACTOR_CELLS)
        expected_share = len(ATTRACTOR_CELLS) / len(world.scope_cells)
        actual_share = attractor_visits / total
        return actual_share / expected_share if expected_share > 0 else 0.0

    def attention_cv(heatmap):
        visits = heatmap[heatmap > 0]
        if len(visits) < 2:
            return 0.0
        return visits.std() / visits.mean()

    p3_visits = heatmap_by_phase[3]
    p3_total = int(p3_visits.sum())
    if p3_total > 0:
        p3_concentration = p3_visits.max() / (p3_total / len(world.scope_cells))
    else:
        p3_concentration = 0.0

    # --- REPORT ---
    lines = []
    lines.append("=" * 72)
    lines.append(f"v0.9 CHARACTERISATION  —  hazard_mode = {HAZARD_MODE}")
    lines.append(f"                          hazard_cost = {HAZARD_COST}")
    lines.append("=" * 72)
    lines.append(f"Life length              : {NUM_STEPS} steps")
    lines.append(f"Environment size         : {GRID_SIZE}x{GRID_SIZE}")
    lines.append(f"Passable scope           : {len(world.scope_cells)}")
    lines.append(f"Hazard cells             : {len(world.hazard_cells)}")
    lines.append(f"Attractor cells          : {len(world.attractor_cells)}")
    lines.append("")
    lines.append("Phase 1 (Prescribed traversal):")
    lines.append(f"  Completed at step      : {agent.phase_1_end_step}")
    lines.append(f"  Cells covered          : {covered_at_phase_1_end}/{len(world.scope_cells)}")
    lines.append(f"  Path length            : {len(agent.prescribed_actions)} actions")
    lines.append("")
    if agent.phase_2_end_step:
        p2_duration = agent.phase_2_end_step - agent.phase_1_end_step
        lines.append(f"Phase 2 (Integration): {p2_duration} steps")
        lines.append(f"  Attractor visit ratio  : {attractor_ratio(heatmap_by_phase[2]):.2f}x chance")
        lines.append(f"  Attention CV           : {attention_cv(heatmap_by_phase[2]):.2f}")
        lines.append("")
    if agent.phase_2_end_step:
        p3_duration = NUM_STEPS - agent.phase_2_end_step
        lines.append(f"Phase 3 (Autonomy): {p3_duration} steps")
        lines.append(f"  Attractor visit ratio  : {attractor_ratio(heatmap_by_phase[3]):.2f}x chance")
        lines.append(f"  Attention CV           : {attention_cv(heatmap_by_phase[3]):.2f}")
        lines.append(f"  Attention concentration: {p3_concentration:.1f}x uniform")
        lines.append("")
    lines.append("RULE ADHERENCE:")
    lines.append(f"  Frame-directed blocked attempts  — P1: {agent.frame_attempts_by_phase[1]:4d}  "
                 f"P2: {agent.frame_attempts_by_phase[2]:4d}  "
                 f"P3: {agent.frame_attempts_by_phase[3]:4d}")
    lines.append(f"  Hazard-directed blocked attempts — P1: {agent.hazard_attempts_by_phase[1]:4d}  "
                 f"P2: {agent.hazard_attempts_by_phase[2]:4d}  "
                 f"P3: {agent.hazard_attempts_by_phase[3]:4d}")
    lines.append(f"  Actual hazard entries            — P1: {agent.hazard_entries_by_phase[1]:4d}  "
                 f"P2: {agent.hazard_entries_by_phase[2]:4d}  "
                 f"P3: {agent.hazard_entries_by_phase[3]:4d}")
    lines.append(f"  Total cost incurred              : {agent.total_cost_incurred:.2f}")
    lines.append("")
    lines.append(f"Total pairs mastered       : {mastered_count_trace[-1]}")
    lines.append("")
    lines.append("Top 5 preferred cells at end of life:")
    for cell, pref in top_preferred:
        ctype = world.cell_type.get(cell, FRAME)
        marker = ""
        if ctype == ATTRACTOR:
            marker = " (ATTRACTOR)"
        elif ctype == HAZARD:
            marker = " (HAZARD)"
        elif any(abs(cell[0] - ax) + abs(cell[1] - ay) <= 1
                 for (ax, ay) in ATTRACTOR_CELLS):
            marker = " (near attractor)"
        lines.append(f"  {cell}: preference = {pref:.2f}{marker}")

    report_str = "\n".join(lines)
    print("\n" + report_str)

    report_filename = f"self_report_v0_9_{HAZARD_MODE}_c{HAZARD_COST}.txt"
    with open(report_filename, "w") as f:
        f.write(report_str)
    print(f"\nReport saved to {report_filename}")

    # --- PLOTS ---
    # Matches v0.8's six-panel layout with two changes for v0.9:
    #   1. Hazard cells are drawn as large red squares on all heatmaps
    #      so actual entries are visible against the visit counts.
    #   2. The drive-signal plot overlays a cost trace, so any cost
    #      accrued during Phase 2/3 is visible on the same axes as
    #      the intrinsic drives it competes with.
    fig, axes = plt.subplots(3, 2, figsize=(14, 14))

    def draw_heatmap(ax, heatmap, title, cmap):
        im = ax.imshow(heatmap, cmap=cmap, origin="upper")
        for (x, y), t in world.cell_type.items():
            if t == FRAME:
                ax.plot(x, y, marker="s", color="saddlebrown", markersize=3)
            elif t == HAZARD:
                ax.plot(x, y, marker="s", color="red", markersize=6)
            elif t == ATTRACTOR:
                ax.plot(x, y, marker="*", color="lime", markersize=12,
                        markeredgecolor="black", markeredgewidth=0.5)
        ax.set_title(title)
        plt.colorbar(im, ax=ax, fraction=0.046)
        ax.set_xlim(-0.5, GRID_SIZE - 0.5)
        ax.set_ylim(GRID_SIZE - 0.5, -0.5)

    draw_heatmap(axes[0, 0], heatmap_by_phase[1],
                 f"Phase 1 (Prescribed)\nended step {agent.phase_1_end_step}",
                 "viridis")
    p2_steps = (agent.phase_2_end_step - agent.phase_1_end_step
                if agent.phase_2_end_step else 0)
    draw_heatmap(axes[0, 1], heatmap_by_phase[2],
                 f"Phase 2 (Integration)\n{p2_steps} steps", "plasma")
    p3_steps = (NUM_STEPS - agent.phase_2_end_step
                if agent.phase_2_end_step else 0)
    draw_heatmap(axes[1, 0], heatmap_by_phase[3],
                 f"Phase 3 (Autonomy)\n{p3_steps} steps", "magma")

    ax = axes[1, 1]
    ax.plot(coverage_pct_trace, linewidth=1.5, color="teal")
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--",
                   label=f"P1 end @ {agent.phase_1_end_step}")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--",
                   label=f"P2 end @ {agent.phase_2_end_step}")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage over time (% of passable scope)")
    ax.set_xlabel("Step")
    ax.set_ylabel("% visited")
    ax.set_ylim(0, 105)

    def running_mean(x, window=200):
        if len(x) < window:
            return np.array(x)
        c = np.cumsum(np.insert(x, 0, 0))
        return (c[window:] - c[:-window]) / window

    ax = axes[2, 0]
    ax.plot(running_mean(progress_trace), linewidth=1.0,
            color="darkgreen", label="progress")
    ax.plot(running_mean(novelty_trace), linewidth=1.0,
            color="navy", label="novelty")
    ax.plot(running_mean(preference_trace), linewidth=1.0,
            color="crimson", label="preference")
    ax.plot(running_mean(feature_trace), linewidth=1.0,
            color="goldenrod", label="feature")
    # v0.9 addition: cost trace overlaid on the same axes as the drives.
    # Plotted as negative values so visual direction reflects that cost
    # subtracts from the intrinsic reward.
    neg_cost_trace = [-c for c in cost_trace]
    ax.plot(running_mean(neg_cost_trace), linewidth=1.0,
            color="black", label="cost (neg)")
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--")
    ax.set_title("Drive signals over time (rolling mean)")
    ax.set_xlabel("Step")
    ax.set_ylabel("signal")
    ax.legend(fontsize=8)

    ax = axes[2, 1]
    ax.plot(mastered_count_trace, linewidth=1.5, color="sienna")
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--")
    ax.set_title("Mastery accumulation")
    ax.set_xlabel("Step")
    ax.set_ylabel("# pairs mastered")

    # Figure-level title includes the mode and cost for immediate
    # visual identification when multiple outputs are in the same folder.
    fig.suptitle(
        f"v0.9  —  hazard_mode = {HAZARD_MODE}   hazard_cost = {HAZARD_COST}",
        fontsize=13, y=0.995
    )
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    plot_filename = f"run_output_v0_9_{HAZARD_MODE}_c{HAZARD_COST}.png"
    plt.savefig(plot_filename, dpi=110)
    print(f"Plots saved to {plot_filename}")
    plt.show()

    return agent, world, heatmap_by_phase


if __name__ == "__main__":
    run()
