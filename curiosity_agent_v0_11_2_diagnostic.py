"""
curiosity_agent_v0_11_2_diagnostic.py
-------------------------------------
Diagnostic version of v0.11.2. The architecture is unchanged from
v0.11.2; only the reporting is extended to dump additional information
that distinguishes between three hypotheses for the post-mastery
fixation behaviour observed in v0.11.2's probe.

The hypotheses being distinguished:
  H1: Fixation is driven by preference accumulation on cells adjacent
      to mastered attractors. Approach paths accumulate preference
      during Phase 2; in Phase 3 those preferences pull the agent
      back into the neighbourhood, where it visits the mastered cell
      as collateral.
  H2: Fixation is driven by Q-values around mastered cells. The
      MASTERY_BONUS deposited at banking propagates through TD
      learning into nearby state-action pairs; those Q-values persist
      into Phase 3 and reinforce the path toward the mastered cell.
  H3: Some combination of H1 and H2, or a mechanism not yet identified.

Diagnostic outputs added:
  - Preference values for ALL cells within Manhattan distance 2 of
    each mastered attractor.
  - Q-values for ALL state-action pairs leading INTO each mastered
    attractor (i.e. actions that target the mastered cell from
    adjacent positions).
  - Phase 3 trajectory analysis: which cells were visited most often
    in Phase 3 within Manhattan distance 2 of mastered attractors.
  - Time-of-visit distribution: when in Phase 3 did the agent visit
    mastered cells (early, mid, late, throughout).

The architecture is identical to v0.11.2. Reporting is extended.

Run from Terminal with:
    python3 curiosity_agent_v0_11_2_diagnostic.py
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
AVERSION_PENALTY = -5.0
ATTRACTION_BONUS = 0.3

# Inherited from v0.10
HAZARD_COST = 1.0
FLAG_THRESHOLD = 3           # hazards: entries before flag set

# v0.11 additions
MASTERY_THRESHOLD = 3        # attractor visits before mastery (banking)
MASTERY_BONUS = 1.0          # one-time bonus at banking (replaces
                             # feature reward on that entry)

# Environment content: identical to v0.8/v0.9/v0.10
HAZARD_CLUSTERS = [
    [(5, 8), (5, 9), (6, 8)],
    [(14, 13), (14, 14)],
]
ATTRACTOR_CELLS = [
    (3, 3), (16, 3), (9, 10), (4, 15), (15, 16), (11, 5)
]
START_CELL = (1, 1)


def _validate_config():
    if HAZARD_COST < 0:
        raise ValueError(f"HAZARD_COST must be non-negative, got {HAZARD_COST}")
    if FLAG_THRESHOLD < 1:
        raise ValueError(f"FLAG_THRESHOLD must be >= 1, got {FLAG_THRESHOLD}")
    if MASTERY_THRESHOLD < 1:
        raise ValueError(f"MASTERY_THRESHOLD must be >= 1, got {MASTERY_THRESHOLD}")
    if MASTERY_BONUS < 0:
        raise ValueError(f"MASTERY_BONUS must be non-negative, got {MASTERY_BONUS}")


# --------------------------------------------------------------------------
# ENVIRONMENT (identical to v0.10)
# --------------------------------------------------------------------------

class StructuredGridWorld:
    """20x20 grid with frame, neutral, hazard, and attractor cells.
    Identical to v0.10. Hazards always passable at cost; the threat
    layer in the agent (inherited from v0.10) handles experience-driven
    avoidance. Attractors handled by the agent's new mastery mechanism."""

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

    def is_passable_for_path_planning(self, cell):
        t = self.cell_type.get(cell, FRAME)
        return t in (NEUTRAL, ATTRACTOR)

    def perceive_adjacent(self, cell):
        x, y = cell
        adj_coords = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        return tuple(self.cell_type.get(c, FRAME) for c in adj_coords)

    def perceive_adjacent_with_coords(self, cell):
        """Return adjacent (cell_type, coordinates) pairs. Used by the
        v0.11 primitive bias so it can check the mastery flag for
        adjacent attractor cells."""
        x, y = cell
        adj_coords = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        return [(self.cell_type.get(c, FRAME), c) for c in adj_coords]

    def observe(self):
        x, y = self.agent_pos
        ctype = self.cell_type[(x, y)]
        adj = self.perceive_adjacent(self.agent_pos)
        return (x, y, ctype, *adj)

    def step(self, action):
        """Identical to v0.10: hazards passable at cost, attractors and
        neutrals passable freely, frame impassable. The mastery
        mechanism operates on the reward stream in the agent's update,
        not on the world's transitions."""
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

        if not (0 <= target[0] < self.size and 0 <= target[1] < self.size):
            target_type = FRAME
        else:
            target_type = self.cell_type[target]

        if target_type == FRAME:
            return self.observe(), target, False, 0.0
        if target_type == HAZARD:
            self.agent_pos = target
            return self.observe(), target, True, HAZARD_COST
        self.agent_pos = target
        return self.observe(), target, True, 0.0


# --------------------------------------------------------------------------
# PATH PLANNING (identical to v0.8/v0.9/v0.10)
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
    """v0.11.2 amendment to v0.11.1. Adds one architectural change
    relative to v0.11.1: preference accumulation in update_model is
    blocked entirely on mastered cells. The v0.11.1 reset at banking
    is retained for architectural clarity but is now redundant.

    Inherits from v0.11/v0.11.1:
      - attractor_visit_counter: per-cell int counter for ATTRACTOR entries
      - mastery_flag: per-cell binary flag (ATTRACTORs only)
      - Modified feature_reward: returns full FEATURE_DRIVE_WEIGHT for
        visits 1 to N-1, MASTERY_BONUS on visit N (banking), 0 after.
      - Modified _primitive_bias: ATTRACTION_BONUS cleared for banked
        attractors so the agent's exploration extends outward.
      - update_model resets cell_preference at the banking step (v0.11.1)

    v0.11.2 additions:
      - update_model blocks cell_preference accumulation entirely on
        mastered cells. Combined with the v0.11/v0.11.1 changes, a
        mastered cell produces no signal pulling the agent back via
        any of the four mechanisms (feature reward, attraction bias,
        preference at banking, preference accumulation post-banking).
    """

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

        # v0.10 threat layer (inherited unchanged)
        self.threat_flag = {}
        self.hazard_entry_counter = defaultdict(int)
        for cell, ctype in world.cell_type.items():
            if ctype == FRAME:
                self.threat_flag[cell] = 1
            else:
                self.threat_flag[cell] = 0

        self.time_to_first_flag = None
        self.time_to_final_flag = None
        self.cells_flagged_during_run = set()
        self.cost_at_final_flag = None

        # v0.11 additions: mastery layer
        self.attractor_visit_counter = defaultdict(int)
        self.mastery_flag = {}
        for cell, ctype in world.cell_type.items():
            if ctype == ATTRACTOR:
                self.mastery_flag[cell] = 0
        self.time_to_first_mastery = None
        self.time_to_final_mastery = None
        self.mastery_order_sequence = []  # ordered list of banked cells

        # Rule-adherence tracking
        self.frame_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_entries_by_phase = {1: 0, 2: 0, 3: 0}
        self.total_cost_incurred = 0.0
        self.hazard_gated_by_threat_layer = {1: 0, 2: 0, 3: 0}

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
        """v0.11 modification: ATTRACTION_BONUS only applies to
        *unmastered* attractors. Banked attractors produce no pre-wired
        bias, so the agent's exploration is not pulled back to cells
        that no longer offer developmental reward.

        To check mastery status we need the coordinates of adjacent
        cells, not just their types. We compute these from the agent's
        current position (state[0], state[1]).
        """
        x, y = state[0], state[1]
        adj_coords = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        adj_types = state[3:7]
        biases = np.zeros(4)
        for i, (t, coord) in enumerate(zip(adj_types, adj_coords)):
            if t == FRAME:
                biases[i] = AVERSION_PENALTY
            elif t == ATTRACTOR:
                # v0.11: apply bonus only to unmastered attractors
                if self.mastery_flag.get(coord, 0) == 0:
                    biases[i] = ATTRACTION_BONUS
                # else: no bias for banked attractors
            # HAZARD: no pre-wired bias
        return biases

    def _get_destination_cell(self, state, action):
        x, y = state[0], state[1]
        if action == 0:
            target = (x, y - 1)
        elif action == 1:
            target = (x, y + 1)
        elif action == 2:
            target = (x - 1, y)
        elif action == 3:
            target = (x + 1, y)
        else:
            return None
        if not (0 <= target[0] < GRID_SIZE and 0 <= target[1] < GRID_SIZE):
            return None
        return target

    def _action_is_gated(self, state, action):
        dest = self._get_destination_cell(state, action)
        if dest is None:
            return False
        return self.threat_flag.get(dest, 0) == 1

    def choose_action(self, state):
        """Drive-based action selection with v0.10 threat-layer hard gate
        and v0.11-modified primitive bias.
        """
        all_actions = list(range(self.num_actions))
        candidate_actions = [a for a in all_actions
                             if not self._action_is_gated(state, a)]
        gated_count = len(all_actions) - len(candidate_actions)
        if gated_count > 0:
            self.hazard_gated_by_threat_layer[self.phase] += gated_count
        if not candidate_actions:
            candidate_actions = all_actions

        if np.random.rand() < self.epsilon:
            biases = self._primitive_bias(state)
            valid = [a for a in candidate_actions
                     if biases[a] > AVERSION_PENALTY / 2]
            if not valid:
                valid = candidate_actions
            return int(np.random.choice(valid))

        biases = self._primitive_bias(state)
        values = np.array([self.q_values[(state, a)] for a in range(self.num_actions)])
        combined = values + biases
        mask = np.array([a in candidate_actions for a in all_actions])
        combined = np.where(mask, combined, -np.inf)
        max_v = combined.max()
        best = [a for a in candidate_actions if combined[a] == max_v]
        if not best:
            return int(np.random.choice(candidate_actions))
        return int(np.random.choice(best))

    def update_threat_layer(self, entered_cell, step):
        """Called after a successful hazard entry. Unchanged from v0.10."""
        self.hazard_entry_counter[entered_cell] += 1
        if (self.hazard_entry_counter[entered_cell] >= FLAG_THRESHOLD
                and self.threat_flag.get(entered_cell, 0) == 0):
            self.threat_flag[entered_cell] = 1
            self.cells_flagged_during_run.add(entered_cell)
            if self.time_to_first_flag is None:
                self.time_to_first_flag = step
            self.time_to_final_flag = step
            self.cost_at_final_flag = self.total_cost_incurred

    def update_mastery_layer(self, entered_cell, step):
        """v0.11: called on every ATTRACTOR entry. Increments the visit
        counter. On the Nth visit (MASTERY_THRESHOLD), sets the mastery
        flag and records timing metrics. Does NOT return the reward
        signal itself — that is handled in feature_reward() which
        queries the counter state."""
        self.attractor_visit_counter[entered_cell] += 1
        if (self.attractor_visit_counter[entered_cell] >= MASTERY_THRESHOLD
                and self.mastery_flag.get(entered_cell, 0) == 0):
            self.mastery_flag[entered_cell] = 1
            self.mastery_order_sequence.append(entered_cell)
            if self.time_to_first_mastery is None:
                self.time_to_first_mastery = step
            self.time_to_final_mastery = step

    def novelty_reward(self, state):
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def preference_reward(self, state):
        if self.preference_weight == 0.0:
            return 0.0
        cell = (state[0], state[1])
        return self.preference_weight * self.cell_preference[cell]

    def feature_reward(self, state):
        """v0.11 modification: returns:
          - MASTERY_BONUS on the Nth visit (the banking visit)
          - FEATURE_DRIVE_WEIGHT for visits 1 to N-1 (unchanged from v0.10)
          - 0 for visits after mastery (depleted)

        This function is called AFTER update_mastery_layer has
        incremented the counter for this visit. So if the counter is
        exactly at MASTERY_THRESHOLD, this is the banking visit and we
        return the bonus. If it's greater, the attractor is already
        mastered (depleted).
        """
        if self.feature_weight == 0.0:
            return 0.0
        if state[2] != ATTRACTOR:
            return 0.0
        cell = (state[0], state[1])
        counter = self.attractor_visit_counter[cell]
        # counter has already been incremented to this visit's value
        if counter == MASTERY_THRESHOLD:
            # Banking visit: deliver the bonus
            return MASTERY_BONUS
        elif counter > MASTERY_THRESHOLD:
            # Depleted
            return 0.0
        else:
            # Pre-mastery visit (counter 1 to N-1)
            return self.feature_weight

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
        # v0.11.2: block preference accumulation on mastered cells.
        # Mastered cells should produce no signal pulling the agent back;
        # blocking accumulation here prevents the post-mastery
        # learning-progress reward from compounding into a fixation
        # signal across many visits.
        if self.mastery_flag.get(cell, 0) == 0:
            self.cell_preference[cell] += r_progress + r_feature
        # v0.11.1: if this cell was just mastered (banking step), reset
        # its preference to zero. Now redundant given v0.11.2's blocking
        # (the v0.11.2 conditional above prevents accumulation on
        # mastered cells, and at the banking step the flag has just been
        # set so the conditional already blocks the increment), but
        # retained for clarity of architectural intent and as a safeguard
        # against any future code path that might bypass the accumulation
        # block.
        if (self.mastery_flag.get(cell, 0) == 1
                and self.attractor_visit_counter.get(cell, 0) == MASTERY_THRESHOLD):
            self.cell_preference[cell] = 0.0

    def update_values(self, state, action, next_state, intrinsic):
        if self.phase == 1:
            return
        future = max(self.q_values[(next_state, a)] for a in range(self.num_actions))
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error

    def record_action_outcome(self, target_cell, success, cost_incurred, world, step):
        """Track outcome. On successful entry:
          - HAZARD: update threat layer (inherited from v0.10)
          - ATTRACTOR: update mastery layer (new in v0.11)
        """
        if not success:
            t = world.cell_type.get(target_cell, FRAME)
            if t == FRAME:
                self.frame_attempts_by_phase[self.phase] += 1
            elif t == HAZARD:
                self.hazard_attempts_by_phase[self.phase] += 1
            return
        # Successful move
        if cost_incurred > 0:
            # Hazard entry
            self.hazard_entries_by_phase[self.phase] += 1
            self.total_cost_incurred += cost_incurred
            self.update_threat_layer(target_cell, step)
        # Check if this was an attractor entry
        if world.cell_type.get(target_cell, FRAME) == ATTRACTOR:
            self.update_mastery_layer(target_cell, step)


# --------------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------------

def run():
    _validate_config()

    world = StructuredGridWorld()
    agent = DevelopmentalAgent(world, NUM_STEPS)

    print(f"v0.11.2 single run")
    print(f"  HAZARD_COST         : {HAZARD_COST}")
    print(f"  FLAG_THRESHOLD      : {FLAG_THRESHOLD}")
    print(f"  MASTERY_THRESHOLD   : {MASTERY_THRESHOLD}")
    print(f"  MASTERY_BONUS       : {MASTERY_BONUS}")
    print(f"  Environment         : {GRID_SIZE}x{GRID_SIZE}")
    print(f"  Passable scope      : {len(world.scope_cells)}")
    print(f"  Attractors          : {len(world.attractor_cells)}")
    print(f"  Hazards             : {len(world.hazard_cells)}")
    print(f"  Phase 1 path        : {len(agent.prescribed_actions)} steps")
    print()

    heatmap_by_phase = {1: np.zeros((GRID_SIZE, GRID_SIZE)),
                        2: np.zeros((GRID_SIZE, GRID_SIZE)),
                        3: np.zeros((GRID_SIZE, GRID_SIZE))}
    coverage_pct_trace = []
    progress_trace = []
    novelty_trace = []
    preference_trace = []
    feature_trace = []
    cost_trace = []
    mastered_count_trace = []
    flagged_count_trace = []
    mastery_count_trace = []  # v0.11: cumulative attractors mastered

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
        agent.record_action_outcome(target_cell, success, cost_incurred, world, step)

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
        flagged_count_trace.append(len(agent.cells_flagged_during_run))
        mastery_count_trace.append(len(agent.mastery_order_sequence))
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

    # v0.11 measure: Phase 3 visits to mastered vs unmastered attractors
    p3_visits_mastered = sum(
        p3_visits[y, x] for (x, y) in ATTRACTOR_CELLS
        if agent.mastery_flag.get((x, y), 0) == 1
    )
    p3_visits_unmastered = sum(
        p3_visits[y, x] for (x, y) in ATTRACTOR_CELLS
        if agent.mastery_flag.get((x, y), 0) == 0
    )

    # --- REPORT ---
    lines = []
    lines.append("=" * 72)
    lines.append(f"v0.11.2 CHARACTERISATION")
    lines.append(f"                  hazard_cost         = {HAZARD_COST}")
    lines.append(f"                  flag_threshold      = {FLAG_THRESHOLD}")
    lines.append(f"                  mastery_threshold   = {MASTERY_THRESHOLD}")
    lines.append(f"                  mastery_bonus       = {MASTERY_BONUS}")
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
        lines.append(f"  P3 visits to mastered  : {int(p3_visits_mastered)}")
        lines.append(f"  P3 visits to unmastered: {int(p3_visits_unmastered)}")
        lines.append("")
    lines.append("MASTERY LAYER (v0.11):")
    lines.append(f"  Attractors mastered      : {len(agent.mastery_order_sequence)}/{len(world.attractor_cells)}")
    lines.append(f"  Time to first mastery    : {agent.time_to_first_mastery}")
    lines.append(f"  Time to final mastery    : {agent.time_to_final_mastery}")
    lines.append(f"  Mastery order sequence   :")
    for i, cell in enumerate(agent.mastery_order_sequence, 1):
        lines.append(f"    {i}. {cell}")
    lines.append("  Per-attractor visit counts:")
    for ac in sorted(world.attractor_cells):
        cnt = agent.attractor_visit_counter.get(ac, 0)
        mastered_marker = " [MASTERED]" if agent.mastery_flag.get(ac, 0) == 1 else ""
        lines.append(f"    {ac}: {cnt}{mastered_marker}")
    lines.append("")
    lines.append("THREAT LAYER (v0.10, inherited):")
    lines.append(f"  Hazards flagged          : {len(agent.cells_flagged_during_run)}/{len(world.hazard_cells)}")
    lines.append(f"  Time to first flag       : {agent.time_to_first_flag}")
    lines.append(f"  Time to final flag       : {agent.time_to_final_flag}")
    lines.append(f"  Actions gated by layer   — P2: {agent.hazard_gated_by_threat_layer[2]:4d}  "
                 f"P3: {agent.hazard_gated_by_threat_layer[3]:4d}")
    lines.append("")
    lines.append("RULE ADHERENCE:")
    lines.append(f"  Frame-directed blocked attempts  — P1: {agent.frame_attempts_by_phase[1]:4d}  "
                 f"P2: {agent.frame_attempts_by_phase[2]:4d}  "
                 f"P3: {agent.frame_attempts_by_phase[3]:4d}")
    lines.append(f"  Actual hazard entries            — P1: {agent.hazard_entries_by_phase[1]:4d}  "
                 f"P2: {agent.hazard_entries_by_phase[2]:4d}  "
                 f"P3: {agent.hazard_entries_by_phase[3]:4d}")
    lines.append(f"  Total cost incurred              : {agent.total_cost_incurred:.2f}")
    lines.append("")
    lines.append(f"Total state-action pairs mastered  : {mastered_count_trace[-1]}")
    lines.append("")
    lines.append("Top 5 preferred cells at end of life:")
    for cell, pref in top_preferred:
        ctype = world.cell_type.get(cell, FRAME)
        marker = ""
        if ctype == ATTRACTOR:
            mastered_marker = " MASTERED" if agent.mastery_flag.get(cell, 0) == 1 else ""
            marker = f" (ATTRACTOR{mastered_marker})"
        elif ctype == HAZARD:
            marker = " (HAZARD)"
        elif any(abs(cell[0] - ax) + abs(cell[1] - ay) <= 1
                 for (ax, ay) in ATTRACTOR_CELLS):
            marker = " (near attractor)"
        lines.append(f"  {cell}: preference = {pref:.2f}{marker}")

    # =====================================================================
    # DIAGNOSTIC DUMP: distinguishing H1, H2, H3 for fixation mechanism
    # =====================================================================
    lines.append("")
    lines.append("=" * 72)
    lines.append("DIAGNOSTIC DUMP — POST-MASTERY FIXATION MECHANISM")
    lines.append("=" * 72)
    lines.append("")

    # Get list of mastered attractors for analysis
    mastered_attractors = [a for a in ATTRACTOR_CELLS
                            if agent.mastery_flag.get(a, 0) == 1]
    lines.append(f"Mastered attractors at end of run: {len(mastered_attractors)}/6")
    for a in mastered_attractors:
        visits = agent.attractor_visit_counter.get(a, 0)
        p3_visits_here = int(p3_visits[a[1], a[0]])
        lines.append(f"  {a}: total visits = {visits}, P3 visits = {p3_visits_here}")
    lines.append("")

    # --- H1 EVIDENCE: preference values in neighbourhood of mastered cells ---
    lines.append("--- H1: Preference accumulation on neighbour cells ---")
    lines.append("(Preference values for cells within Manhattan distance 2 of each")
    lines.append(" mastered attractor. If neighbour preferences are substantial,")
    lines.append(" they could pull the agent back via Phase 3 preference-weighting.)")
    lines.append("")
    for ma in mastered_attractors:
        mx, my = ma
        lines.append(f"Neighbourhood of mastered attractor {ma}:")
        # Distance 1 (4 cells)
        d1_cells = [(mx, my-1), (mx, my+1), (mx-1, my), (mx+1, my)]
        # Distance 2 (8 cells: 4 corners + 4 two-steps)
        d2_cells = [(mx-1, my-1), (mx-1, my+1), (mx+1, my-1), (mx+1, my+1),
                    (mx, my-2), (mx, my+2), (mx-2, my), (mx+2, my)]
        for cell in d1_cells:
            if 0 <= cell[0] < GRID_SIZE and 0 <= cell[1] < GRID_SIZE:
                pref = agent.cell_preference.get(cell, 0.0)
                ctype = world.cell_type.get(cell, FRAME)
                ctype_name = {FRAME: "FRAME", NEUTRAL: "NEUT", HAZARD: "HAZ",
                              ATTRACTOR: "ATTR"}[ctype]
                lines.append(f"    {cell} (d=1, {ctype_name}): preference = {pref:.2f}")
        for cell in d2_cells:
            if 0 <= cell[0] < GRID_SIZE and 0 <= cell[1] < GRID_SIZE:
                pref = agent.cell_preference.get(cell, 0.0)
                ctype = world.cell_type.get(cell, FRAME)
                ctype_name = {FRAME: "FRAME", NEUTRAL: "NEUT", HAZARD: "HAZ",
                              ATTRACTOR: "ATTR"}[ctype]
                lines.append(f"    {cell} (d=2, {ctype_name}): preference = {pref:.2f}")
        lines.append("")

    # Summary statistic for H1
    if mastered_attractors:
        all_neighbour_prefs = []
        for ma in mastered_attractors:
            mx, my = ma
            d1d2 = [(mx, my-1), (mx, my+1), (mx-1, my), (mx+1, my),
                    (mx-1, my-1), (mx-1, my+1), (mx+1, my-1), (mx+1, my+1),
                    (mx, my-2), (mx, my+2), (mx-2, my), (mx+2, my)]
            for cell in d1d2:
                if 0 <= cell[0] < GRID_SIZE and 0 <= cell[1] < GRID_SIZE:
                    if world.cell_type.get(cell, FRAME) == NEUTRAL:
                        all_neighbour_prefs.append(agent.cell_preference.get(cell, 0.0))
        if all_neighbour_prefs:
            mean_neighbour_pref = np.mean(all_neighbour_prefs)
            max_neighbour_pref = max(all_neighbour_prefs)
            lines.append(f"H1 SUMMARY:")
            lines.append(f"  Mean preference on NEUTRAL cells within d=2 of mastered: {mean_neighbour_pref:.2f}")
            lines.append(f"  Max preference on NEUTRAL cells within d=2 of mastered:  {max_neighbour_pref:.2f}")

            # Compare to baseline: mean preference on NEUTRAL cells NOT near any mastered attractor
            far_prefs = []
            for cell, ctype in world.cell_type.items():
                if ctype != NEUTRAL:
                    continue
                # Not within d=2 of any mastered attractor
                near_any = any(
                    abs(cell[0] - ma[0]) + abs(cell[1] - ma[1]) <= 2
                    for ma in mastered_attractors
                )
                if not near_any:
                    far_prefs.append(agent.cell_preference.get(cell, 0.0))
            if far_prefs:
                mean_far = np.mean(far_prefs)
                lines.append(f"  Mean preference on NEUTRAL cells far (>d=2) from mastered: {mean_far:.2f}")
                lines.append(f"  Ratio near/far: {mean_neighbour_pref / max(mean_far, 0.01):.2f}x")
    lines.append("")

    # --- H2 EVIDENCE: Q-values for actions targeting mastered cells ---
    lines.append("--- H2: Q-values for actions LEADING INTO mastered attractors ---")
    lines.append("(Q-values for state-action pairs where the action targets a")
    lines.append(" mastered attractor cell. If these are substantial and positive,")
    lines.append(" they reinforce the path toward the mastered cell despite the")
    lines.append(" cell itself producing no signal.)")
    lines.append("")
    # For each mastered attractor, find all (state, action) pairs where the action
    # would target the mastered cell from an adjacent state.
    for ma in mastered_attractors:
        mx, my = ma
        lines.append(f"Q-values for actions targeting {ma}:")
        # Adjacent positions and the action that moves toward the attractor
        approaches = [
            ((mx, my+1), 0),  # from below, action 0 = up (y-1)
            ((mx, my-1), 1),  # from above, action 1 = down (y+1)
            ((mx+1, my), 2),  # from right, action 2 = left (x-1)
            ((mx-1, my), 3),  # from left, action 3 = right (x+1)
        ]
        approach_qs = []
        for (approach_pos, approach_action) in approaches:
            ax, ay = approach_pos
            if not (0 <= ax < GRID_SIZE and 0 <= ay < GRID_SIZE):
                continue
            ctype = world.cell_type.get(approach_pos, FRAME)
            if ctype == FRAME:
                continue
            # Find Q-values across all observed states at this position
            # (states differ by adjacent cell types, so multiple states per position)
            qs_at_position = []
            for (state, action), q in agent.q_values.items():
                if state[0] == ax and state[1] == ay and action == approach_action:
                    qs_at_position.append(q)
            if qs_at_position:
                max_q = max(qs_at_position)
                mean_q = np.mean(qs_at_position)
                approach_qs.extend(qs_at_position)
                ctype_name = {FRAME: "FRAME", NEUTRAL: "NEUT", HAZARD: "HAZ",
                              ATTRACTOR: "ATTR"}[ctype]
                lines.append(f"    From {approach_pos} ({ctype_name}, action {approach_action}): "
                             f"max Q = {max_q:.3f}, mean Q = {mean_q:.3f}, "
                             f"n_states = {len(qs_at_position)}")
        lines.append("")

    # H2 summary
    lines.append("H2 SUMMARY:")
    all_into_master_qs = []
    for ma in mastered_attractors:
        mx, my = ma
        approaches = [
            ((mx, my+1), 0), ((mx, my-1), 1),
            ((mx+1, my), 2), ((mx-1, my), 3),
        ]
        for (approach_pos, approach_action) in approaches:
            ax, ay = approach_pos
            if not (0 <= ax < GRID_SIZE and 0 <= ay < GRID_SIZE):
                continue
            ctype = world.cell_type.get(approach_pos, FRAME)
            if ctype == FRAME:
                continue
            for (state, action), q in agent.q_values.items():
                if state[0] == ax and state[1] == ay and action == approach_action:
                    all_into_master_qs.append(q)

    # Compare against Q-values for arbitrary other actions
    other_qs = []
    mastered_positions = set(mastered_attractors)
    for (state, action), q in agent.q_values.items():
        # Skip if this action targets a mastered attractor
        sx, sy = state[0], state[1]
        if action == 0:
            target = (sx, sy - 1)
        elif action == 1:
            target = (sx, sy + 1)
        elif action == 2:
            target = (sx - 1, sy)
        elif action == 3:
            target = (sx + 1, sy)
        if target in mastered_positions:
            continue
        other_qs.append(q)

    if all_into_master_qs:
        lines.append(f"  Mean Q-value for actions targeting mastered attractors: "
                     f"{np.mean(all_into_master_qs):.3f}")
        lines.append(f"  Max Q-value for actions targeting mastered attractors: "
                     f"{max(all_into_master_qs):.3f}")
    if other_qs:
        lines.append(f"  Mean Q-value for other actions: {np.mean(other_qs):.3f}")
        lines.append(f"  Max Q-value for other actions: {max(other_qs):.3f}")
    if all_into_master_qs and other_qs:
        ratio = np.mean(all_into_master_qs) / max(abs(np.mean(other_qs)), 0.001)
        lines.append(f"  Ratio (into-mastered / other) means: {ratio:.2f}x")
    lines.append("")

    # --- INTERPRETATION GUIDE ---
    lines.append("--- INTERPRETATION GUIDE ---")
    lines.append("If H1 SUMMARY shows neighbour pref much higher than far pref,")
    lines.append("  then preference accumulation on neighbour cells is driving")
    lines.append("  fixation (preferences pull agent into neighbourhood).")
    lines.append("If H2 SUMMARY shows into-mastered Q-values much higher than")
    lines.append("  other Q-values, then Q-value learning is reinforcing paths")
    lines.append("  toward mastered cells (Q-values pull agent directly to cell).")
    lines.append("If both, both mechanisms are active. If neither is strongly")
    lines.append("  elevated, the mechanism is something else not yet identified.")
    lines.append("")

    report_str = "\n".join(lines)
    print("\n" + report_str)

    report_filename = f"self_report_v0_11_2_diagnostic_c{HAZARD_COST}.txt"
    with open(report_filename, "w") as f:
        f.write(report_str)
    print(f"\nReport saved to {report_filename}")

    # --- PLOTS ---
    fig, axes = plt.subplots(3, 2, figsize=(14, 14))

    def draw_heatmap(ax, heatmap, title, cmap):
        im = ax.imshow(heatmap, cmap=cmap, origin="upper")
        for (x, y), t in world.cell_type.items():
            if t == FRAME:
                ax.plot(x, y, marker="s", color="saddlebrown", markersize=3)
            elif t == HAZARD:
                if agent.threat_flag.get((x, y), 0) == 1:
                    ax.plot(x, y, marker="s", color="darkred", markersize=7,
                            markeredgecolor="black", markeredgewidth=0.8)
                else:
                    ax.plot(x, y, marker="s", color="red", markersize=6)
            elif t == ATTRACTOR:
                if agent.mastery_flag.get((x, y), 0) == 1:
                    # v0.11: mastered attractors drawn differently
                    ax.plot(x, y, marker="*", color="gold", markersize=14,
                            markeredgecolor="black", markeredgewidth=1.2)
                else:
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
    if agent.time_to_first_mastery is not None:
        ax.axvline(agent.time_to_first_mastery, color="goldenrod",
                   linestyle=":", label=f"1st mastery @ {agent.time_to_first_mastery}")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Coverage over time")
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
    ax.plot(mastered_count_trace, linewidth=1.5, color="sienna",
            label="SA pairs mastered")
    ax2 = ax.twinx()
    ax2.plot(mastery_count_trace, linewidth=1.5, color="goldenrod",
             linestyle="--", label="attractors mastered")
    ax2.plot(flagged_count_trace, linewidth=1.0, color="darkred",
             linestyle=":", label="hazards flagged")
    ax2.set_ylabel("# categorical flags", color="goldenrod")
    ax2.set_ylim(0, max(len(world.attractor_cells), len(world.hazard_cells)) + 1)
    if agent.phase_1_end_step:
        ax.axvline(agent.phase_1_end_step, color="orange", linestyle="--")
    if agent.phase_2_end_step:
        ax.axvline(agent.phase_2_end_step, color="purple", linestyle="--")
    ax.set_title("Mastery, threat-layer, and S-A pair accumulation")
    ax.set_xlabel("Step")
    ax.set_ylabel("# SA pairs mastered", color="sienna")
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper left")

    fig.suptitle(
        f"v0.11.2  —  cost={HAZARD_COST}   mastery_thresh={MASTERY_THRESHOLD}   "
        f"mastery_bonus={MASTERY_BONUS}",
        fontsize=13, y=0.995
    )
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    plot_filename = f"run_output_v0_11_2_diagnostic_c{HAZARD_COST}.png"
    plt.savefig(plot_filename, dpi=110)
    print(f"Plots saved to {plot_filename}")
    plt.show()

    return agent, world, heatmap_by_phase


if __name__ == "__main__":
    run()
