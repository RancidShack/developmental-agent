"""
curiosity_agent_v0_14.py
------------------------
Developmental agent in a 20x20 structured environment — v0.14
extension of v0.13 with competency-gated content transformation
of hazard cells into knowledge cells.

VERSION:        v0.14 architecture, file incorporates v0.14.1 amendment
AMENDMENT:      v0.14.1 (27 April 2026) — adds permutation_offset
                parameter to StructuredGridWorld for the targeted
                replication batch. Default offset=0 reproduces the
                original v0.14 batch's threshold assignment bit-for-bit.
                Architecture unchanged at the research-question level.
                See v0.14.1-amendment.md for full scope.
SEARCH KEY:     v0.14.1

The v0.13 batch demonstrated that the architecture's existing
locating machinery (novelty drive, learning-progress drive,
primitive attraction bias, preference accumulation) handles
late-appearing feature-reward sources at random locations through
inherited Phase 3 dynamics. By the close of v0.13 the threat-and-
mastery programme as originally scoped is complete on its own
terms: persistent threat representation, persistent mastery,
category-level signature-matching, and late-target activation
are all in place.

v0.14 closes the gap between the existing architecture and the
competency-gated content reframing settled in the v0.12 design
conversation. Hazard cells are reframed as content gated behind
competency thresholds. The transformation from HAZARD to
KNOWLEDGE is the architecture's representation of the developmental
shift from "I cannot enter this cell" to "I can now learn from
this cell."

The architectural change has four contained elements:

(1) Each of the five hazard cells is assigned a sequential
competency threshold from {1, 2, 3, 4, 5} at run start. The
assignment is randomised per run via global RNG state save-and-
restore (parallel to v0.13's end-state cell sampling), preserving
byte-identical pre-first-transition behaviour against v0.13.

(2) After every step, the agent compares its current competency
(sum of mastery flags — the inherited mastery dict, no new state
representation) against each hazard cell's threshold. When a
threshold is first reached, the corresponding cell transitions
HAZARD -> KNOWLEDGE.

(3) The threat layer's hard-gate action selection acquires a
competency-bounded exception. The hard-gate continues to exclude
actions targeting cells where threat_flag = 1 AND cell_type =
HAZARD, but does not exclude actions targeting cells where
threat_flag = 1 AND cell_type = KNOWLEDGE. The threat flag itself
persists across the cell-type transition until the cell is banked
as knowledge.

(4) Post-transition KNOWLEDGE cells carry FEATURE_DRIVE_WEIGHT
and ATTRACTION_BONUS parallel to attractor and end-state cells,
pre-banking. They bank after three post-transition entries (the
mastery-equivalent operation, parallel to attractor cells'
MASTERY_THRESHOLD = 3). At banking the four mastery interventions
apply: feature reward depletes, attraction bias clears, preference
resets, accumulation blocks. The threat flag clears at banking.

(5) The v0.13 end-state activation trigger is amended. The original
trigger fired on `all_attractors_mastered`; v0.14 amends to
`all_attractors_mastered AND all_hazards_banked_as_knowledge`. The
v0.13 end-state cell sampling and post-activation behaviour are
preserved unchanged.

The Category F honesty constraint from the v0.14 pre-registration:
v0.14 contributes the competency-threshold mechanism (Sections
2.2, 2.3 of the pre-reg), the cell-type transition rule with
action-selection exception (Section 2.4), and the amended end-
state trigger (Section 2.7). v0.14 does NOT contribute the
locating machinery (inherited from v0.13's Phase 3 dynamics) or
the state-checking machinery (the mastery flag dict, inherited
from v0.11.2 — used here as the competency variable directly).

See v0.14-prereg.md for full reasoning, including the temporal-
scope-restricted Check 4a audit logic (per the v0.13.1 lesson).

All other architectural elements from v0.13 (which inherits v0.12,
v0.11.2, v0.11.1, v0.11, v0.10) are retained unchanged.

Run from Terminal with:
    python3 curiosity_agent_v0_14.py
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

GRID_SIZE = 20
NUM_STEPS = 160000
PHASE_3_START_FRACTION = 0.6
Q_VALUE_RESET_MULTIPLIER = 0.3
FEATURE_DRIVE_WEIGHT = 0.15

# Cell type constants
FRAME = 0
NEUTRAL = 1
HAZARD = 2
ATTRACTOR = 3
END_STATE = 4                    # v0.13: end-state target cell
KNOWLEDGE = 5                    # v0.14: post-competency-unlock cell type,
                                 # transitioned from HAZARD when the agent's
                                 # competency reaches the cell's threshold

# Primitive structures
AVERSION_PENALTY = -5.0
ATTRACTION_BONUS = 0.3

# Inherited from v0.10
HAZARD_COST = 1.0
FLAG_THRESHOLD = 3           # hazards: entries before flag set

# v0.11 additions
MASTERY_THRESHOLD = 3        # attractor visits before mastery (banking)
MASTERY_BONUS = 1.0          # one-time bonus at banking

# v0.14 additions
KNOWLEDGE_THRESHOLD = 3      # post-transition entries before knowledge
                             # banking. Three-entry banking parallels
                             # attractor mastery (the mastery-equivalent
                             # operation), distinct from v0.13's one-entry
                             # end-state banking (the location-finding
                             # operation).

# Environment content: identical to v0.8/v0.9/v0.10/v0.13
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
    if KNOWLEDGE_THRESHOLD < 1:
        raise ValueError(f"KNOWLEDGE_THRESHOLD must be >= 1, got {KNOWLEDGE_THRESHOLD}")


# --------------------------------------------------------------------------
# ENVIRONMENT (extends v0.13)
# --------------------------------------------------------------------------

class StructuredGridWorld:
    """20x20 grid with frame, neutral, hazard, attractor, end-state, and
    (v0.14) knowledge cells. Hazards always passable at scalar cost; the
    threat layer in the agent (inherited from v0.10) handles experience-
    driven avoidance, with the v0.14 competency-bounded exception
    permitting entry to KNOWLEDGE-typed cells whose threat_flag persists
    from the pre-transition period.

    v0.14 additions to world construction:
      - hazard_competency_thresholds: dict mapping each hazard cell
        coordinate to its assigned threshold from {1, 2, 3, 4, 5},
        sampled at run start by permutation under global RNG state
        save-and-restore (parallel to end-state cell sampling).
      - knowledge_unlocked: dict tracking whether each hazard cell has
        had its HAZARD -> KNOWLEDGE transition applied. Initialised
        False; set True via transition_hazard_to_knowledge().
    """

    def __init__(self, size=GRID_SIZE, permutation_offset=0):
        self.size = size
        self.agent_pos = START_CELL
        self.permutation_offset = permutation_offset
        self._build_grid()
        # v0.14: competency-threshold assignment to hazard cells. Performed
        # before end-state cell sampling so the per-run draw sequence is
        # competency-thresholds first, end-state cell second. Both use
        # global RNG state save-and-restore.
        self._assign_hazard_competency_thresholds()
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

    def _assign_hazard_competency_thresholds(self):
        """v0.14: sample a permutation of {1, 2, 3, 4, 5} and assign
        the elements to the five hazard cells in sorted-coordinate order.

        Implementation note: the sampling saves and restores the global
        numpy RNG state around its draw, parallel to _sample_end_state_cell
        in v0.13. This preserves the main stream for the agent's
        choose_action calls, which means v0.14's pre-first-transition
        behaviour is byte-identical to v0.13's at matched seeds (v0.14
        pre-reg Check 4a, scoped to the period before the first
        cell-type transition fires).

        The assignment is deterministic with respect to the run's seed
        (because the saved state is exactly what np.random.seed(seed)
        produced) but the draw does not advance the global stream. The
        assignment order — which threshold to which cell — varies across
        runs because the saved RNG state at this point in __init__
        differs across runs (set by the batch runner before world
        construction).

        v0.14.1 amendment: the permutation_offset parameter (default 0)
        permits a targeted replication batch to draw a different
        permutation while preserving the matched-seed comparison
        guarantee. When non-zero, the offset advances the RNG stream
        by `permutation_offset` draws before the permutation sample;
        the saved state (without offset) is then restored, so the
        agent's first action-selection RNG state is unchanged. The
        first-batch behaviour is recovered exactly when offset = 0.
        """
        sorted_hazards = sorted(self.hazard_cells)
        if len(sorted_hazards) != 5:
            raise ValueError(
                f"v0.14 assumes exactly 5 hazard cells; "
                f"found {len(sorted_hazards)}."
            )
        rng_state = np.random.get_state()
        # v0.14.1 amendment: advance the stream by permutation_offset
        # draws before the permutation sample, to produce a different
        # permutation under replication while preserving the saved
        # state for restore.
        for _ in range(self.permutation_offset):
            np.random.rand()
        permutation = np.random.permutation(5)
        np.random.set_state(rng_state)
        self.hazard_competency_thresholds = {
            sorted_hazards[i]: int(permutation[i]) + 1  # convert 0..4 -> 1..5
            for i in range(5)
        }
        # Track which hazard cells have had their HAZARD -> KNOWLEDGE
        # transition applied. Initialised False; set True by
        # transition_hazard_to_knowledge().
        self.knowledge_unlocked = {h: False for h in sorted_hazards}

    def _sample_end_state_cell(self):
        """v0.13: sample one neutral cell coordinate at random from the
        passable non-attractor scope, designate it the end-state cell
        location. Preserved unchanged in v0.14. The end-state activation
        trigger is amended (see DevelopmentalAgent.record_action_outcome),
        but the cell sampling and post-activation behaviour are
        unchanged.

        Implementation note (inherited from v0.13): the sampling saves
        and restores the global numpy RNG state around its draw. Under
        v0.14, _assign_hazard_competency_thresholds also performs a
        save-and-restore draw immediately before this method, so the
        global RNG state at the start of this method is what the seed
        produced and the agent's subsequent action selection RNG state
        is preserved. Pre-first-transition behaviour matches v0.13
        byte-for-byte.
        """
        candidates = sorted([
            c for c, t in self.cell_type.items() if t == NEUTRAL
        ])
        rng_state = np.random.get_state()
        idx = np.random.randint(0, len(candidates))
        np.random.set_state(rng_state)
        self.end_state_cell = candidates[idx]
        self.end_state_activated = False

    def transition_hazard_to_knowledge(self, cell):
        """v0.14: called by the agent when its competency first reaches
        the cell's assigned threshold. Mutates the cell's type from
        HAZARD to KNOWLEDGE. The cell's perceptual properties change
        immediately; from the next action selection onward, the agent
        perceives the cell as KNOWLEDGE. The threat flag in the agent
        persists across the transition (cleared only at knowledge
        banking).

        Idempotent: if called more than once for the same cell, only
        the first call has effect. The agent's main loop should call
        this once at the unlock step and not again."""
        if self.knowledge_unlocked.get(cell, False):
            return
        if cell not in self.hazard_cells:
            raise ValueError(
                f"transition_hazard_to_knowledge called on non-hazard "
                f"cell {cell}"
            )
        self.cell_type[cell] = KNOWLEDGE
        self.knowledge_unlocked[cell] = True

    def activate_end_state(self):
        """v0.13: called by the agent when the amended end-state
        activation signal first fires. Mutates the end-state cell's type
        from NEUTRAL to END_STATE. v0.14: the activation trigger is
        amended (see DevelopmentalAgent.record_action_outcome), but
        this method's behaviour is unchanged.

        Idempotent: if called more than once, only the first call has
        effect."""
        if self.end_state_activated:
            return
        self.cell_type[self.end_state_cell] = END_STATE
        self.end_state_activated = True

    def is_passable_for_path_planning(self, cell):
        t = self.cell_type.get(cell, FRAME)
        # v0.14: KNOWLEDGE cells are passable for path planning. They
        # cannot exist during Phase 1 (transitions cannot fire until at
        # least one attractor is mastered, and mastery cannot occur in
        # Phase 1 because feature_weight is zero), so this branch is
        # reached only via mid-run cell-type transition. Treat KNOWLEDGE
        # as passable parallel to ATTRACTOR / END_STATE.
        return t in (NEUTRAL, ATTRACTOR, END_STATE, KNOWLEDGE)

    def perceive_adjacent(self, cell):
        x, y = cell
        adj_coords = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        return tuple(self.cell_type.get(c, FRAME) for c in adj_coords)

    def perceive_adjacent_with_coords(self, cell):
        """Return adjacent (cell_type, coordinates) pairs."""
        x, y = cell
        adj_coords = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        return [(self.cell_type.get(c, FRAME), c) for c in adj_coords]

    def observe(self):
        x, y = self.agent_pos
        ctype = self.cell_type[(x, y)]
        adj = self.perceive_adjacent(self.agent_pos)
        return (x, y, ctype, *adj)

    def step(self, action):
        """v0.14 modification: HAZARD entries return cost as before;
        KNOWLEDGE entries return zero cost (the cell is no longer hazard-
        typed). NEUTRAL, ATTRACTOR, END_STATE remain passable at zero
        cost. FRAME impassable.

        The cost stream is therefore: pre-transition entries to a hazard
        cell pay HAZARD_COST; post-transition entries to the same cell
        (now KNOWLEDGE) pay zero. The threat flag persists across the
        transition, so the action-selection hard-gate continues to
        exclude the cell unless the v0.14 competency-bounded exception
        applies (cell type is now KNOWLEDGE)."""
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
        # NEUTRAL, ATTRACTOR, END_STATE, KNOWLEDGE: passable at zero cost
        self.agent_pos = target
        return self.observe(), target, True, 0.0


# --------------------------------------------------------------------------
# PATH PLANNING (identical to v0.8/v0.9/v0.10/v0.13)
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
    """v0.14 extension of v0.13. Adds competency-gated content
    transformation: hazard cells transition to knowledge cells when the
    agent's competency (sum of mastery flags) reaches the cell's
    assigned threshold. The action-selection hard-gate acquires a
    competency-bounded exception permitting entry to KNOWLEDGE-typed
    cells whose threat_flag persists from the pre-transition period.

    Inherits from v0.13 (which inherits v0.12, v0.11.2, v0.11.1, v0.11,
    v0.10):
      - threat_flag, hazard_entry_counter, FLAG_THRESHOLD = 3
      - Three-entry conversion + v0.12 signature-matching first-entry
      - Hard-gate action selection (v0.14 modification: now consults
        cell_type to apply the competency-bounded exception)
      - attractor_visit_counter, mastery_flag, MASTERY_THRESHOLD = 3,
        MASTERY_BONUS = 1.0
      - Modified feature_reward, _primitive_bias, update_model
        (v0.14 extends each to handle KNOWLEDGE cells)
      - End-state cell sampling, activation, banking, four mastery
        interventions on banking (v0.14 amends activation trigger)

    v0.14 additions:
      - knowledge_entry_counter: per-cell counter for post-transition
        KNOWLEDGE entries. Banks at KNOWLEDGE_THRESHOLD = 3.
      - knowledge_banked: per-cell flag, set true at banking, parallel
        to mastery_flag for attractors.
      - competency_unlock_step: per-cell step at which the cell-type
        transition fired.
      - knowledge_banked_step: per-cell step at which the cell was
        banked as knowledge.
      - pre_transition_hazard_entries: per-cell counter for entries to
        the cell during the HAZARD-typed period. Recorded for analysis
        of how pre-transition exposure relates to post-transition
        engagement.
      - Amended end-state activation trigger:
        all_attractors_mastered AND all_hazards_banked_as_knowledge.
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
        self.first_entry_flag_conversions = 0
        self.time_to_second_flag = None
        self.cost_paid_on_signature_matched_hazards = 0.0

        # v0.11 additions: mastery layer
        self.attractor_visit_counter = defaultdict(int)
        self.mastery_flag = {}
        for cell in world.attractor_cells:
            self.mastery_flag[cell] = 0
        self.time_to_first_mastery = None
        self.time_to_final_mastery = None
        self.mastery_order_sequence = []

        # v0.13 end-state target activation (inherited; trigger amended
        # in record_action_outcome below).
        self.activation_step = None
        self.end_state_cell = world.end_state_cell
        self.end_state_found_step = None
        self.end_state_visits = 0
        self.end_state_banked = False

        # v0.14 additions: competency-gated content transformation.
        # Per-cell counters and flags for the five hazard cells. The
        # cell-type transition is recorded at the unlock step; the
        # banking event is recorded at the third post-transition entry.
        self.knowledge_entry_counter = defaultdict(int)
        self.knowledge_banked = {h: False for h in world.hazard_cells}
        self.competency_unlock_step = {h: None for h in world.hazard_cells}
        self.knowledge_banked_step = {h: None for h in world.hazard_cells}
        self.pre_transition_hazard_entries = defaultdict(int)
        # Mirror the world's threshold assignment for ease of metric
        # access; the world's record is canonical.
        self.hazard_competency_thresholds = dict(
            world.hazard_competency_thresholds
        )
        # Aggregate timing metrics for the v0.14 transition layer.
        self.time_to_first_transition = None
        self.time_to_final_transition = None
        # Order in which cells transitioned (parallel to mastery_order_sequence)
        self.transition_order_sequence = []
        # Order in which cells were banked as knowledge
        self.knowledge_banked_sequence = []

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
        """v0.11/v0.13/v0.14 modifications:
          - ATTRACTOR adjacent: ATTRACTION_BONUS only when unmastered
          - END_STATE adjacent: ATTRACTION_BONUS only when unbanked
          - KNOWLEDGE adjacent (v0.14): ATTRACTION_BONUS only when unbanked
          - HAZARD adjacent: no pre-wired bias
          - FRAME adjacent: AVERSION_PENALTY (unchanged)
        """
        x, y = state[0], state[1]
        adj_coords = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        adj_types = state[3:7]
        biases = np.zeros(4)
        for i, (t, coord) in enumerate(zip(adj_types, adj_coords)):
            if t == FRAME:
                biases[i] = AVERSION_PENALTY
            elif t == ATTRACTOR:
                if self.mastery_flag.get(coord, 0) == 0:
                    biases[i] = ATTRACTION_BONUS
            elif t == END_STATE:
                if not self.end_state_banked:
                    biases[i] = ATTRACTION_BONUS
            elif t == KNOWLEDGE:
                # v0.14: apply bonus only to unbanked knowledge cells.
                if not self.knowledge_banked.get(coord, False):
                    biases[i] = ATTRACTION_BONUS
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
        """v0.14 modification: the hard-gate excludes actions targeting
        cells where threat_flag = 1 AND cell_type = HAZARD. Cells where
        threat_flag = 1 AND cell_type = KNOWLEDGE (the post-transition
        state, with persisting threat flag) are NOT gated — the agent
        can act on them.

        Pre-first-transition behaviour matches v0.13: while all hazard
        cells remain HAZARD-typed, the cell-type check evaluates true
        and the gate behaves as in v0.13 (which gates all flagged
        cells). The byte-identical preservation property of v0.14
        Check 4a relies on this reduction.
        """
        dest = self._get_destination_cell(state, action)
        if dest is None:
            return False
        if self.threat_flag.get(dest, 0) != 1:
            return False
        # v0.14: competency-bounded exception. If the cell has
        # transitioned to KNOWLEDGE, the gate does not apply despite
        # the persisting threat flag.
        dest_type = self.world.cell_type.get(dest, FRAME)
        if dest_type == KNOWLEDGE:
            return False
        return True

    def choose_action(self, state):
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
        """v0.12 inherited unchanged.

        Note: this method is called only on entries where cost is
        incurred (cost_incurred > 0). Post-transition entries to a
        knowledge cell return zero cost from world.step() because the
        cell type is KNOWLEDGE rather than HAZARD; therefore this
        method is not called on knowledge-cell entries, and the
        signature-matching logic continues to operate only on genuine
        hazard entries. The threat flag for a transitioned cell
        persists from the pre-transition period unchanged."""
        any_other_flagged = any(
            self.threat_flag.get(h, 0) == 1
            for h in self.world.hazard_cells
            if h != entered_cell
        )

        if any_other_flagged and self.threat_flag.get(entered_cell, 0) == 0:
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
            return

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
        """v0.11 inherited unchanged."""
        self.attractor_visit_counter[entered_cell] += 1
        if (self.attractor_visit_counter[entered_cell] >= MASTERY_THRESHOLD
                and self.mastery_flag.get(entered_cell, 0) == 0):
            self.mastery_flag[entered_cell] = 1
            self.mastery_order_sequence.append(entered_cell)
            if self.time_to_first_mastery is None:
                self.time_to_first_mastery = step
            self.time_to_final_mastery = step

    def update_knowledge_layer(self, entered_cell, step):
        """v0.14: called on every KNOWLEDGE-typed entry. Increments the
        post-transition entry counter. On the third visit
        (KNOWLEDGE_THRESHOLD), banks the cell: sets knowledge_banked
        true, applies the four mastery interventions (depleted feature
        reward and cleared attraction bias are handled in feature_reward
        and _primitive_bias respectively, by querying knowledge_banked;
        preference reset is performed here; preference accumulation
        block is enforced in update_model).

        Additionally clears the threat flag at banking, on the
        architectural reasoning that the developmental cycle from
        hazard through knowledge to banked-knowledge represents
        complete engagement with the cell.
        """
        self.knowledge_entry_counter[entered_cell] += 1
        if (self.knowledge_entry_counter[entered_cell] >= KNOWLEDGE_THRESHOLD
                and not self.knowledge_banked.get(entered_cell, False)):
            self.knowledge_banked[entered_cell] = True
            self.knowledge_banked_step[entered_cell] = step
            self.knowledge_banked_sequence.append(entered_cell)
            # Reset cell preference at banking, parallel to attractor
            # mastery's v0.11.1 reset. Subsequent accumulation is
            # blocked by update_model's check.
            self.cell_preference[entered_cell] = 0.0
            # Clear the threat flag at banking (v0.14 banking rule:
            # threat representation is no longer the operative state
            # post-engagement).
            self.threat_flag[entered_cell] = 0

    def check_competency_unlocks(self, step):
        """v0.14: after every step, check whether the agent's competency
        (sum of mastery flags) has reached any unfired hazard cell's
        threshold. Trigger transitions in sorted-coordinate order for
        any cells whose threshold has been met but whose transition
        has not yet fired.

        Called from record_action_outcome after the v0.13 activation
        check. The check fires multiple transitions in the same step
        if competency has jumped past multiple thresholds (which can
        happen at the moment of any attractor banking if multiple
        cells share an upper-bound threshold — under the v0.14
        permutation assignment of {1, 2, 3, 4, 5}, no two cells share
        a threshold, so at most one cell can transition per step).
        """
        current_competency = sum(self.mastery_flag.values())
        for cell in sorted(self.world.hazard_cells):
            if self.world.knowledge_unlocked.get(cell, False):
                continue
            threshold = self.hazard_competency_thresholds.get(cell)
            if threshold is None:
                continue
            if current_competency >= threshold:
                # Trigger the transition.
                self.world.transition_hazard_to_knowledge(cell)
                self.competency_unlock_step[cell] = step
                self.transition_order_sequence.append(cell)
                if self.time_to_first_transition is None:
                    self.time_to_first_transition = step
                self.time_to_final_transition = step

    def novelty_reward(self, state):
        count = self.visit_counts[state]
        return self.novelty_weight / np.sqrt(count + 1)

    def preference_reward(self, state):
        if self.preference_weight == 0.0:
            return 0.0
        cell = (state[0], state[1])
        return self.preference_weight * self.cell_preference[cell]

    def feature_reward(self, state):
        """v0.11/v0.13/v0.14: returns:
          - ATTRACTOR (mastery): MASTERY_BONUS on Nth visit, FEATURE on
            visits 1..N-1, 0 after mastery
          - END_STATE: FEATURE pre-banking, 0 post-banking
          - KNOWLEDGE (v0.14): FEATURE pre-banking, 0 post-banking
            (parallel to END_STATE; one-entry banking does not apply
            because v0.14 banks at three entries — but the per-visit
            payout is FEATURE pre-banking, regardless of which visit
            within the unbanked window)

        v0.14 omits a bonus on the banking entry for knowledge cells.
        The architectural reasoning: the bonus on attractor banking is
        v0.11's developmental marker for completed mastery; the absence
        of an analogous bonus on knowledge banking reflects that the
        knowledge-cell engagement is the agent's act of learning from
        a previously-inaccessible cell rather than a developmental
        marker the architecture rewards directly.
        """
        if self.feature_weight == 0.0:
            return 0.0
        ctype = state[2]
        if ctype == END_STATE:
            if self.end_state_banked:
                return 0.0
            return self.feature_weight
        if ctype == KNOWLEDGE:
            cell = (state[0], state[1])
            if self.knowledge_banked.get(cell, False):
                return 0.0
            return self.feature_weight
        if ctype != ATTRACTOR:
            return 0.0
        cell = (state[0], state[1])
        counter = self.attractor_visit_counter[cell]
        if counter == MASTERY_THRESHOLD:
            return MASTERY_BONUS
        elif counter > MASTERY_THRESHOLD:
            return 0.0
        else:
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
        # v0.11.2 / v0.13 / v0.14: block preference accumulation on
        # mastered attractors, banked end-state cell, and banked
        # knowledge cells.
        is_blocked = (
            self.mastery_flag.get(cell, 0) == 1
            or (cell == self.end_state_cell and self.end_state_banked)
            or self.knowledge_banked.get(cell, False)
        )
        if not is_blocked:
            self.cell_preference[cell] += r_progress + r_feature
        # v0.11.1 banking-step reset (retained for clarity, redundant
        # given the block above)
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
        """v0.14 extension of v0.13's record_action_outcome.

        On successful entry:
          - HAZARD-typed cell at the moment of entry: update threat layer
            (cost_incurred > 0); also increment pre_transition_hazard_entries.
          - ATTRACTOR: update mastery layer.
          - END_STATE: bank on first post-activation entry (v0.13).
          - KNOWLEDGE (v0.14): update knowledge layer (post-transition
            entry tracking, banking at KNOWLEDGE_THRESHOLD).

        After any successful entry:
          - v0.14: check competency-unlock thresholds against current
            mastery count. Triggers HAZARD -> KNOWLEDGE transitions for
            any cells whose threshold has been reached.
          - v0.13/v0.14: check the amended end-state activation signal
            (all_attractors_mastered AND all_hazards_banked_as_knowledge).
            Triggers the world's end-state cell-type transition on
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
        # The cell type at the time of entry determines which layer
        # handles the outcome. Note: cost_incurred > 0 iff target_cell
        # was HAZARD-typed at world.step() time, because the world's
        # cost branch is keyed on cell_type. Knowledge-cell entries
        # therefore have cost_incurred == 0.
        target_type_at_entry = world.cell_type.get(target_cell, FRAME)
        if cost_incurred > 0:
            # Hazard entry (cell was HAZARD-typed).
            self.hazard_entries_by_phase[self.phase] += 1
            self.total_cost_incurred += cost_incurred
            self.update_threat_layer(target_cell, step)
            # v0.14: track per-cell pre-transition entries.
            if target_cell in world.hazard_cells:
                self.pre_transition_hazard_entries[target_cell] += 1
        if target_type_at_entry == ATTRACTOR:
            self.update_mastery_layer(target_cell, step)
        # v0.13: end-state entry post-activation.
        if (target_type_at_entry == END_STATE
                and self.activation_step is not None):
            self.end_state_visits += 1
            if not self.end_state_banked:
                self.end_state_found_step = step
                self.end_state_banked = True
                self.cell_preference[self.end_state_cell] = 0.0
        # v0.14: knowledge-cell entry post-transition.
        if target_type_at_entry == KNOWLEDGE:
            self.update_knowledge_layer(target_cell, step)

        # v0.14: check competency-unlock thresholds. Performed after
        # update_mastery_layer so that an attractor banked at this
        # step is reflected in current_competency. Performed before
        # the end-state activation check so that a transition fired
        # at this step is reflected in the all_hazards_banked
        # condition (although banking requires three post-transition
        # entries, so a transition at this step cannot trigger
        # end-state activation at this step).
        self.check_competency_unlocks(step)

        # v0.13/v0.14: amended end-state activation signal.
        # v0.14 amendment: requires both all_attractors_mastered AND
        # all_hazards_banked_as_knowledge. The amended trigger is a
        # strict extension of v0.13's trigger.
        if self.activation_step is None:
            all_attractors_mastered = (
                sum(self.mastery_flag.values())
                == len(world.attractor_cells)
            )
            all_hazards_banked = (
                sum(1 for v in self.knowledge_banked.values() if v)
                == len(world.hazard_cells)
            )
            if all_attractors_mastered and all_hazards_banked:
                self.activation_step = step
                world.activate_end_state()


# --------------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------------

def run():
    _validate_config()

    world = StructuredGridWorld()
    agent = DevelopmentalAgent(world, NUM_STEPS)

    print(f"v0.14 single run")
    print(f"  HAZARD_COST          : {HAZARD_COST}")
    print(f"  FLAG_THRESHOLD       : {FLAG_THRESHOLD}")
    print(f"  MASTERY_THRESHOLD    : {MASTERY_THRESHOLD}")
    print(f"  MASTERY_BONUS        : {MASTERY_BONUS}")
    print(f"  KNOWLEDGE_THRESHOLD  : {KNOWLEDGE_THRESHOLD}")
    print(f"  Environment          : {GRID_SIZE}x{GRID_SIZE}")
    print(f"  Passable scope       : {len(world.scope_cells)}")
    print(f"  Attractors           : {len(world.attractor_cells)}")
    print(f"  Hazards              : {len(world.hazard_cells)}")
    print(f"  End-state cell       : {world.end_state_cell}")
    print(f"  Hazard thresholds    :")
    for cell, thresh in sorted(world.hazard_competency_thresholds.items()):
        print(f"    {cell}: {thresh}")
    print(f"  Phase 1 path         : {len(agent.prescribed_actions)} steps")
    print()

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
        agent.record_action_outcome(target_cell, success, cost_incurred, world, step)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        r_feature = agent.feature_reward(next_state)
        intrinsic = r_novelty + r_progress + r_preference + r_feature - cost_incurred

        agent.update_model(state, action, next_state, error, r_progress, r_feature)
        agent.update_values(state, action, next_state, intrinsic)

        state = next_state

    # --- REPORT ---
    print("=" * 72)
    print("v0.14 CHARACTERISATION")
    print("=" * 72)
    print(f"Life length              : {NUM_STEPS} steps")
    print(f"Phase 1 ended at step    : {agent.phase_1_end_step}")
    print(f"Phase 2 ended at step    : {agent.phase_2_end_step}")
    print()
    print("MASTERY LAYER (v0.11):")
    print(f"  Attractors mastered    : "
          f"{len(agent.mastery_order_sequence)}/{len(world.attractor_cells)}")
    print(f"  Time to first mastery  : {agent.time_to_first_mastery}")
    print(f"  Time to final mastery  : {agent.time_to_final_mastery}")
    print()
    print("THREAT LAYER (v0.10/v0.12):")
    print(f"  Hazards flagged        : "
          f"{len(agent.cells_flagged_during_run)}/{len(world.hazard_cells)}")
    print(f"  Time to first flag     : {agent.time_to_first_flag}")
    print(f"  Time to final flag     : {agent.time_to_final_flag}")
    print(f"  First-entry conversions: {agent.first_entry_flag_conversions}")
    print()
    print("KNOWLEDGE LAYER (v0.14):")
    print(f"  Hazards transitioned   : "
          f"{len(agent.transition_order_sequence)}/{len(world.hazard_cells)}")
    print(f"  Hazards banked as kn.  : "
          f"{len(agent.knowledge_banked_sequence)}/{len(world.hazard_cells)}")
    print(f"  Time to 1st transition : {agent.time_to_first_transition}")
    print(f"  Time to final transition: {agent.time_to_final_transition}")
    print(f"  Per-cell timing:")
    for cell in sorted(world.hazard_cells):
        thresh = agent.hazard_competency_thresholds[cell]
        unlock = agent.competency_unlock_step.get(cell)
        banked = agent.knowledge_banked_step.get(cell)
        kn_entries = agent.knowledge_entry_counter.get(cell, 0)
        pre_entries = agent.pre_transition_hazard_entries.get(cell, 0)
        print(f"    {cell} thr={thresh} "
              f"unlock={unlock} banked={banked} "
              f"pre_entries={pre_entries} kn_entries={kn_entries}")
    print()
    print("END-STATE LAYER (v0.13, v0.14-amended trigger):")
    print(f"  End-state cell location: {world.end_state_cell}")
    print(f"  Activation step        : {agent.activation_step}")
    print(f"  End-state found step   : {agent.end_state_found_step}")
    print(f"  End-state banked       : {agent.end_state_banked}")


if __name__ == "__main__":
    run()
