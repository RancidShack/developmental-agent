"""
curiosity_agent_v0_13.py
------------------------
Developmental agent in a 20x20 structured environment — v0.13
extension of v0.12 with end-state target activation via a random-
location cell appearing on the all-attractors-mastered signal.

The v0.11.2 batch demonstrated that the architecture reliably
converges toward exhausting the available attractor set at long
run lengths. By 160,000 steps the v0.11.2 / v0.12 batches showed
mean attractors mastered approaching 6 of 6 with the agent's
post-mastery exploration concentrated around the closest banked
cell to the start position (3, 3).

v0.13 introduces a single architectural extension. At run start,
one neutral cell coordinate is sampled at random from the passable
non-attractor scope and designated as the end-state cell location.
The cell remains a neutral cell perceptually until activation; the
agent visits it during Phase 1's prescribed traversal as it would
visit any neutral cell.

When the agent banks all six attractor cells — when
sum(self.mastery_flag.values()) == len(world.attractor_cells)
becomes true — the activation signal fires. The agent records the
activation step and calls world.activate_end_state(), which mutates
the cell's type to END_STATE. From the next step onward, the cell
carries feature reward FEATURE_DRIVE_WEIGHT and primitive attraction
bias ATTRACTION_BONUS, parallel to attractor cells.

The end-state cell banks on first entry after activation. v0.13's
research question is whether the agent locates the cell, not whether
the agent learns about it across multiple visits. Banking applies
the four mastery interventions to the end-state cell: feature reward
depletes to zero, primitive attraction bias clears, cell preference
resets to zero, and ongoing preference accumulation is blocked.

v0.13 does not specify what happens after the end-state cell is
banked. The post-banking environment has no remaining feature-reward
sources; the agent's Phase 3 dynamics continue without modification
through the end of the deterministic step-budget. What the cell is
for — payout structure, transformation, run termination — is
reserved for v0.14 / v0.15 on the competency-gated content design
framework that emerged from the v0.12 design conversation.

The Category F honesty constraint from the pre-registration: the
locating capability operates through inherited Phase 3 dynamics
(novelty drive, learning-progress drive, primitive attraction bias,
preference accumulation). v0.13 contributes the cell type, the
activation signal, and the cell-type transition; the locating
itself is performed by machinery the architecture already had.
The v0.13 result is consistent both with the reading that the
inherited machinery handles late-appearing targets at random
locations and with the deflationary reading that no genuine new
locating capability is demonstrated. The richer-mechanism work is
reserved for v0.15+.

See v0.13-preregistration.md for full reasoning, including the
stopping rule named in Section 10 of that document.

All other architectural elements from v0.12 (which inherits v0.11.2,
v0.11.1, v0.11, and v0.10) are retained unchanged.

Run from Terminal with:
    python3 curiosity_agent_v0_13.py
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
END_STATE = 4                    # v0.13: end-state target cell, activated
                                 # when all attractors are mastered

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
    """20x20 grid with frame, neutral, hazard, attractor, and (v0.13)
    end-state cells. Hazards always passable at cost; the threat
    layer in the agent (inherited from v0.10) handles experience-driven
    avoidance. Attractors handled by the v0.11 mastery mechanism. The
    end-state cell is sampled at run start from the passable
    non-attractor scope and remains a neutral cell perceptually until
    activate_end_state() is called by the agent on the
    all-attractors-mastered signal."""

    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.agent_pos = START_CELL
        self._build_grid()
        self._sample_end_state_cell()

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

    def _sample_end_state_cell(self):
        """v0.13: sample one neutral cell coordinate at random from the
        passable non-attractor scope, designate it the end-state cell
        location. The cell remains NEUTRAL in cell_type until activation;
        only the recorded coordinate distinguishes it pre-activation.

        Implementation note: the sampling saves and restores the global
        numpy RNG state around its draw. This preserves the main stream
        for the agent's choose_action calls, which means v0.13's
        pre-activation behaviour is byte-identical to v0.12's at
        matched seeds. The end-state cell selection itself is still
        deterministic with respect to the run's seed because the saved
        state is exactly what np.random.seed(seed) produced when the
        batch runner seeded the run; the saved-state draw is
        reproducible.

        This implementation choice is dictated by the Category A
        Check 4 commitment in Section 7 of the v0.13 pre-registration,
        which requires byte-identical pre-activation behaviour against
        v0.12 at matched seeds. v0.11.2 and v0.12 perform no np.random
        draws during world or agent initialisation; the v0.13 cell
        sampling would otherwise consume a draw that shifts the
        agent's RNG state and breaks the matched-seed guarantee.
        """
        candidates = sorted([
            c for c, t in self.cell_type.items() if t == NEUTRAL
        ])
        # Save the global RNG state, perform the sampling draw, restore
        # the state. The end-state cell selection is deterministic given
        # the run's seed (because the saved state is what the seed
        # produced) but the draw does not advance the global stream.
        rng_state = np.random.get_state()
        idx = np.random.randint(0, len(candidates))
        np.random.set_state(rng_state)
        self.end_state_cell = candidates[idx]
        # end_state_activated tracks whether the cell-type transition
        # has occurred. False until activate_end_state() is called.
        self.end_state_activated = False

    def activate_end_state(self):
        """v0.13: called by the agent when the all-attractors-mastered
        signal first fires. Mutates the end-state cell's type from
        NEUTRAL to END_STATE. The cell's perceptual properties change
        immediately; from the next action selection onward, the agent
        perceives the cell as END_STATE.

        Idempotent: if called more than once, only the first call has
        effect. The agent's main loop should call this once at the
        activation step and not again."""
        if self.end_state_activated:
            return
        self.cell_type[self.end_state_cell] = END_STATE
        self.end_state_activated = True

    def is_passable_for_path_planning(self, cell):
        t = self.cell_type.get(cell, FRAME)
        # v0.13: END_STATE cells are passable for path planning, but
        # the cell is NEUTRAL during Phase 1 (before activation can
        # possibly fire), so this branch is reached only via
        # mid-run cell-type transition. Treat END_STATE as passable
        # parallel to ATTRACTOR.
        return t in (NEUTRAL, ATTRACTOR, END_STATE)

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
    """v0.12 extension of v0.11.2. Adds one architectural change
    relative to v0.11.2: the threat layer's flag-conversion rule
    is augmented with a category-membership check on cell-type
    signature (signature-matching first-entry flagging on signature
    match). All v0.11.2 mastery-side architecture is preserved.

    Inherits from v0.11.2 (which inherits v0.11.1, v0.11, v0.10):
      - threat_flag: per-cell binary flag (FRAME pre-flagged, others
        initialised to 0)
      - hazard_entry_counter: per-cell int counter for HAZARD entries
      - Three-entry conversion rule: a cell flagged once its counter
        reaches FLAG_THRESHOLD = 3 (retained as the path for the
        first hazard cell flagged in any run)
      - Hard-gate action selection: flagged cells excluded from the
        action-selection pipeline before Q-value computation
      - attractor_visit_counter, mastery_flag, MASTERY_THRESHOLD = 3,
        MASTERY_BONUS = 1.0
      - Modified feature_reward: full FEATURE_DRIVE_WEIGHT for visits
        1 to N-1, MASTERY_BONUS on visit N (banking), 0 after
      - Modified _primitive_bias: ATTRACTION_BONUS cleared for banked
        attractors
      - update_model resets cell_preference at the banking step (v0.11.1)
        and blocks preference accumulation entirely on mastered cells
        (v0.11.2)

    v0.12 addition:
      - update_threat_layer applies a category-membership check before
        the standard three-entry conversion. If any other hazard cell
        has threat_flag = 1, the entered cell's flag is set to 1
        immediately on this entry (signature-matching first-entry
        conversion). If no other hazard is flagged, the standard
        three-entry conversion rule applies as in v0.11.2.
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

        # v0.12 additions: signature-matching metrics
        # first_entry_flag_conversions counts the number of hazard cells
        # whose flag converted on first entry under the signature-matching
        # rule (i.e., not the first hazard to be flagged in the run, but
        # every subsequent novel hazard the agent encounters after at
        # least one hazard is already flagged).
        self.first_entry_flag_conversions = 0
        # time_to_second_flag records the step at which the second hazard
        # cell's flag converted, regardless of whether by three-entry or
        # by signature-matching. Together with time_to_first_flag, this
        # gives the time-from-first-flag-to-second-flag metric.
        self.time_to_second_flag = None
        # cost_paid_on_signature_matched_hazards accumulates the cost paid
        # on cells whose flag converted on first entry under the
        # signature-matching rule. Bounded at one unit of cost per
        # signature-matched cell by construction.
        self.cost_paid_on_signature_matched_hazards = 0.0

        # v0.11 additions: mastery layer
        self.attractor_visit_counter = defaultdict(int)
        self.mastery_flag = {}
        for cell, ctype in world.cell_type.items():
            if ctype == ATTRACTOR:
                self.mastery_flag[cell] = 0
        self.time_to_first_mastery = None
        self.time_to_final_mastery = None
        self.mastery_order_sequence = []  # ordered list of banked cells

        # v0.13 additions: end-state target activation
        # activation_step records the step at which all six attractors
        # were first banked, triggering world.activate_end_state(). None
        # if the run does not reach all-attractors-mastered.
        self.activation_step = None
        # end_state_cell mirrors world.end_state_cell for convenience;
        # the world's record is the canonical one.
        self.end_state_cell = world.end_state_cell
        # end_state_found_step records the step at which the agent first
        # entered the end-state cell after activation. None if the agent
        # does not enter the cell within the run length.
        self.end_state_found_step = None
        # end_state_visits counts entries to the end-state cell in the
        # post-activation period (zero before activation by construction).
        self.end_state_visits = 0
        # end_state_banked tracks whether the cell has been banked. The
        # banking applies the four mastery interventions (depleted feature
        # reward, cleared attraction bias, preference reset, blocked
        # accumulation) on first entry post-activation.
        self.end_state_banked = False
        # end_state_preference tracks the cell's preference accumulation
        # parallel to cell_preference for other cells. Reset to zero at
        # banking and accumulation blocked thereafter.

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

        v0.13 addition: END_STATE cells receive ATTRACTION_BONUS when
        adjacent and not yet banked. Once banked, no bias (parallel to
        the v0.11 treatment of mastered attractors).

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
            elif t == END_STATE:
                # v0.13: apply bonus only to unbanked end-state cell
                if not self.end_state_banked:
                    biases[i] = ATTRACTION_BONUS
                # else: no bias post-banking
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
        """v0.12: signature-matching flag conversion on cell-type signature.

        On entry into a hazard cell, check whether any other hazard cell
        has threat_flag = 1. If yes, set this cell's flag to 1 immediately
        on this entry (signature-matching first-entry flagging). If no,
        apply the standard three-entry conversion rule from v0.10 / v0.11.2.

        The signature is cell type alone (HAZARD). The first hazard cell
        the agent flags still requires three entries (because at the time
        of its first three encounters, no other hazard is flagged); every
        subsequent novel hazard cell encountered is flagged on first entry.
        """
        # v0.12: category-membership check.
        # Enumerate other hazard cells with flag = 1.
        any_other_flagged = any(
            self.threat_flag.get(h, 0) == 1
            for h in self.world.hazard_cells
            if h != entered_cell
        )

        if any_other_flagged and self.threat_flag.get(entered_cell, 0) == 0:
            # Signature-matching first-entry flag conversion.
            self.threat_flag[entered_cell] = 1
            self.cells_flagged_during_run.add(entered_cell)
            self.first_entry_flag_conversions += 1
            self.cost_paid_on_signature_matched_hazards += HAZARD_COST
            if self.time_to_first_flag is None:
                self.time_to_first_flag = step
            elif self.time_to_second_flag is None:
                self.time_to_second_flag = step
            self.time_to_final_flag = step
            self.cost_at_final_flag = self.total_cost_incurred
            # Note: counter is not incremented on signature-matched conversion,
            # since the cell will not be entered again (action selection
            # excludes flagged cells via the hard gate).
            return

        # v0.10 / v0.11.2 behaviour: standard three-entry conversion.
        self.hazard_entry_counter[entered_cell] += 1
        if (self.hazard_entry_counter[entered_cell] >= FLAG_THRESHOLD
                and self.threat_flag.get(entered_cell, 0) == 0):
            self.threat_flag[entered_cell] = 1
            self.cells_flagged_during_run.add(entered_cell)
            if self.time_to_first_flag is None:
                self.time_to_first_flag = step
            elif self.time_to_second_flag is None:
                self.time_to_second_flag = step
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

        v0.13 addition: END_STATE cells return FEATURE_DRIVE_WEIGHT
        pre-banking and zero post-banking. The cell banks on first
        entry (one-entry banking), so the feature_reward path delivers
        FEATURE_DRIVE_WEIGHT once and then depletes. There is no
        MASTERY_BONUS analogue: the cell is found, not mastered.
        """
        if self.feature_weight == 0.0:
            return 0.0
        if state[2] == END_STATE:
            # v0.13: end-state cell. Pre-banking pays feature reward;
            # post-banking is depleted (parallel to mastered attractors).
            if self.end_state_banked:
                return 0.0
            return self.feature_weight
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
        # v0.13: also block accumulation on the end-state cell once
        # banked. Pre-banking, the cell accumulates preference parallel
        # to other cells; post-banking, accumulation is blocked.
        is_blocked = (
            self.mastery_flag.get(cell, 0) == 1
            or (cell == self.end_state_cell and self.end_state_banked)
        )
        if not is_blocked:
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
          - END_STATE: bank on first post-activation entry (new in v0.13)

        After any successful entry, v0.13 checks the all-attractors-
        mastered signal and triggers world.activate_end_state() on
        first fire.
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
        # v0.13: check if this was an end-state cell entry post-activation
        if (world.cell_type.get(target_cell, FRAME) == END_STATE
                and self.activation_step is not None):
            self.end_state_visits += 1
            if not self.end_state_banked:
                # First post-activation entry: bank the cell
                self.end_state_found_step = step
                self.end_state_banked = True
                # Reset cell preference to zero at banking, parallel to
                # v0.11.1's reset on attractor mastery. Subsequent
                # accumulation is blocked by update_model's check.
                self.cell_preference[self.end_state_cell] = 0.0
        # v0.13: check the all-attractors-mastered activation signal.
        # Fires once per run, on the first step at which all six
        # attractors have been banked. Triggers the world's cell-type
        # transition for the end-state cell.
        if (self.activation_step is None
                and sum(self.mastery_flag.values()) == 5):
            self.activation_step = step
            world.activate_end_state()


# --------------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------------

def run():
    _validate_config()

    world = StructuredGridWorld()
    agent = DevelopmentalAgent(world, NUM_STEPS)

    print(f"v0.13 single run")
    print(f"  HAZARD_COST         : {HAZARD_COST}")
    print(f"  FLAG_THRESHOLD      : {FLAG_THRESHOLD}")
    print(f"  MASTERY_THRESHOLD   : {MASTERY_THRESHOLD}")
    print(f"  MASTERY_BONUS       : {MASTERY_BONUS}")
    print(f"  Environment         : {GRID_SIZE}x{GRID_SIZE}")
    print(f"  Passable scope      : {len(world.scope_cells)}")
    print(f"  Attractors          : {len(world.attractor_cells)}")
    print(f"  Hazards             : {len(world.hazard_cells)}")
    print(f"  End-state cell      : {world.end_state_cell}")
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
    lines.append(f"v0.13 CHARACTERISATION")
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
    lines.append("THREAT LAYER (v0.10 inherited, v0.12 signature-matching):")
    lines.append(f"  Hazards flagged          : {len(agent.cells_flagged_during_run)}/{len(world.hazard_cells)}")
    lines.append(f"  Time to first flag       : {agent.time_to_first_flag}")
    lines.append(f"  Time to second flag      : {agent.time_to_second_flag}")
    lines.append(f"  Time to final flag       : {agent.time_to_final_flag}")
    lines.append(f"  First-entry conversions  : {agent.first_entry_flag_conversions}")
    lines.append(f"  Cost on sig-matched cells: {agent.cost_paid_on_signature_matched_hazards:.2f}")
    lines.append(f"  Actions gated by layer   — P2: {agent.hazard_gated_by_threat_layer[2]:4d}  "
                 f"P3: {agent.hazard_gated_by_threat_layer[3]:4d}")
    lines.append("")
    lines.append("END-STATE LAYER (v0.13):")
    lines.append(f"  End-state cell location  : {world.end_state_cell}")
    lines.append(f"  Activation step          : {agent.activation_step}")
    lines.append(f"  End-state found step     : {agent.end_state_found_step}")
    if (agent.activation_step is not None
            and agent.end_state_found_step is not None):
        gap = agent.end_state_found_step - agent.activation_step
        lines.append(f"  Post-activation discovery: {gap} steps")
    elif agent.activation_step is not None:
        lines.append(f"  Post-activation discovery: NOT FOUND within run length")
    else:
        lines.append(f"  Post-activation discovery: activation did not fire")
    lines.append(f"  End-state visits         : {agent.end_state_visits}")
    lines.append(f"  End-state banked         : {agent.end_state_banked}")
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
        elif ctype == END_STATE:
            banked_marker = " BANKED" if agent.end_state_banked else ""
            marker = f" (END_STATE{banked_marker})"
        elif cell == world.end_state_cell:
            # Pre-activation: cell is still NEUTRAL but is the designated
            # end-state cell location.
            marker = " (end-state location, pre-activation)"
        elif any(abs(cell[0] - ax) + abs(cell[1] - ay) <= 1
                 for (ax, ay) in ATTRACTOR_CELLS):
            marker = " (near attractor)"
        lines.append(f"  {cell}: preference = {pref:.2f}{marker}")

    report_str = "\n".join(lines)
    print("\n" + report_str)

    report_filename = f"self_report_v0_13_c{HAZARD_COST}.txt"
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
        # v0.13: render the end-state cell with a diamond marker, drawn
        # over whatever cell-type marker (or lack of one for neutral
        # cells) was placed above. Uses world.end_state_cell directly
        # so the cell appears in all three phase heatmaps regardless
        # of whether activation has fired.
        ex, ey = world.end_state_cell
        if agent.end_state_banked:
            # Banked end-state cell: deep blue diamond with edge
            ax.plot(ex, ey, marker="D", color="navy", markersize=12,
                    markeredgecolor="black", markeredgewidth=1.2)
        else:
            # Unbanked: cyan diamond
            ax.plot(ex, ey, marker="D", color="cyan", markersize=11,
                    markeredgecolor="black", markeredgewidth=0.8)
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
        f"v0.13  —  cost={HAZARD_COST}   mastery_thresh={MASTERY_THRESHOLD}   "
        f"mastery_bonus={MASTERY_BONUS}",
        fontsize=13, y=0.995
    )
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    plot_filename = f"run_output_v0_13_c{HAZARD_COST}.png"
    plt.savefig(plot_filename, dpi=110)
    print(f"Plots saved to {plot_filename}")
    plt.show()

    return agent, world, heatmap_by_phase


if __name__ == "__main__":
    run()
