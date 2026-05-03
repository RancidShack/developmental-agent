"""
v1_7_agent.py
-------------
V17Agent: the v1.7 agent for the 3D continuous-space substrate.

ARCHITECTURE PRINCIPLE
All cognitive-layer logic is inherited unchanged from V15Agent through
the full inheritance chain. The substrate-interface methods — action
selection, primitive bias, destination calculation, Phase 1 path
following, observation indexing — are overridden for the 3D continuous
world. Everything the cognitive layer does with what the agent
encounters (threat layer, mastery layer, knowledge layer, competency
unlocks, end-state activation) is inherited without modification.

WHAT CHANGES (substrate interface)
  - num_actions = 27 (26 directions + stay)
  - Phase 1 path follows 3D waypoints via action selection, not a
    prescribed grid sequence
  - _get_destination_cell → returns None for stay actions; estimates
    destination for 3D moves (used only by _action_is_gated)
  - _primitive_bias → operates on perceived objects within radius rather
    than 4 adjacent grid cells
  - visit_counts keyed by rounded position bucket rather than (x,y) cell
  - record_action_outcome called with the contacted object_id
    (string, e.g. "haz_green") rather than a grid coordinate tuple

WHAT STAYS UNCHANGED (cognitive layer)
  - update_threat_layer(object_id, step)
  - update_mastery_layer(object_id, step)
  - update_knowledge_layer(object_id, step)
  - check_competency_unlocks(step) — iterates world.hazard_cells by
    object_id; calls world.transform_to_knowledge(object_id)
  - All mastery_flag, threat_flag, knowledge_banked dicts — keyed by
    object_id (str) instead of (x,y) tuple; same dict structure
  - The end-state activation check — reads len(world.attractor_cells)
    and len(world.hazard_cells); both are sets of object_ids

FLAG ID FORMAT MIGRATION
In V13World, flag IDs embedded grid coordinates: "mastery:(4, 15)".
In V17World, flag IDs embed object_ids: "mastery:att_green".
This migration is entirely at the substrate interface (the provenance
observer constructs flag IDs from cell/object identity). No cognitive-
layer provenance logic changes; only the key format changes.

The V15PredictionErrorObserver detects transitions by watching
world.cell_type[object_id]. V17World.cell_type is an alias of
world.object_type, keyed by object_id. The observer's _prev_cell_type
cache, _tracked_cells set, and transition detection loop all work
unchanged because they iterate over dict keys — which are now
object_id strings rather than coordinate tuples. The only observer
code that embeds specific cell identities is the UNAFFILIATED_HAZARD_CELLS
frozenset, which must be updated to use object_ids (see
v1_7_observer_substrates.py).

Inheritance chain:
  V17Agent → V15Agent → V14Agent → V13Agent → V12Agent → V014Agent
"""

import math
import numpy as np
from collections import defaultdict

from v1_5_agent import V15Agent
from curiosity_agent_v1_7_world import (
    V17World,
    NUM_ACTIONS, STEP_SIZE, CONTACT_RADIUS, PERCEPTION_RADIUS,
    ATTRACTOR, END_STATE, KNOWLEDGE, HAZARD, FRAME, NEUTRAL, DIST_OBJ,
    _dist3, _DIRECTION_VECTORS,
)
from curiosity_agent_v0_14 import ATTRACTION_BONUS, AVERSION_PENALTY

# Import constants from base agent for cognitive-layer methods
from curiosity_agent_v0_14 import (
    FEATURE_DRIVE_WEIGHT, PHASE_3_START_FRACTION,
    FLAG_THRESHOLD, MASTERY_THRESHOLD, KNOWLEDGE_THRESHOLD,
    MASTERY_BONUS,
)

# ---------------------------------------------------------------------------
# V17Agent
# ---------------------------------------------------------------------------


class V17Agent(V15Agent):
    """v1.7 agent. Substrate-interface methods overridden for 3D world.

    All cognitive-layer methods — threat layer, mastery layer, knowledge
    layer, competency unlocks, Q-value updates, feature reward — are
    inherited unchanged from V015Agent through V15Agent.
    """

    def __init__(self, world: V17World, total_steps: int, num_actions: int = NUM_ACTIONS):
        # --- Cognitive-layer init (from V014Agent.__init__) ---
        # We cannot call super().__init__() directly because it runs
        # V013Agent init code that assumes a grid world (prescribed path
        # from plan_phase_1_path, 4 actions, grid-sized scope). We
        # replicate the cognitive-layer state initialisation here and
        # replace the substrate-specific parts.

        self.world = world
        self.scope = world.scope_cells  # set of object_ids
        self.total_steps = total_steps
        self.steps_taken = 0
        self.covered = set()
        self.num_actions = num_actions

        self.visit_counts = defaultdict(int)
        self.forward_model = defaultdict(lambda: defaultdict(int))
        self.fast_errors = defaultdict(lambda: __import__('collections').deque(maxlen=5))
        self.slow_errors = defaultdict(lambda: __import__('collections').deque(maxlen=30))
        self.cell_preference = defaultdict(float)
        self.q_values = defaultdict(float)

        self.phase = 1
        self.phase_1_end_step = None
        self.phase_2_end_step = None
        self.phase_3_start_target = int(total_steps * PHASE_3_START_FRACTION)

        # 3D Phase 1: waypoint-following instead of grid boustrophedon
        self._waypoints = list(world._waypoints)
        self._waypoint_idx = 0
        self._current_waypoint = (
            self._waypoints[0] if self._waypoints else None
        )
        self._waypoint_arrival_threshold = CONTACT_RADIUS * 1.5

        self.learning_rate = 0.1
        self.epsilon = 0.1

        # ----------------------------------------------------------------
        # Threat layer (V010Agent, keyed by object_id)
        # ----------------------------------------------------------------
        self.threat_flag = {}
        self.hazard_entry_counter = defaultdict(int)
        # FRAME sentinel: no frame objects in V17World, but gate logic
        # checks threat_flag.get(dest, 0); default 0 is fine.
        for oid in world.scope_cells:
            self.threat_flag[oid] = 0

        self.time_to_first_flag = None
        self.time_to_final_flag = None
        self.cells_flagged_during_run = set()
        self.cost_at_final_flag = None

        # V012 signature-matching metrics
        self.first_entry_flag_conversions = 0
        self.time_to_second_flag = None
        self.cost_paid_on_signature_matched_hazards = 0.0

        # ----------------------------------------------------------------
        # Mastery layer (V011Agent, keyed by object_id)
        # ----------------------------------------------------------------
        self.attractor_visit_counter = defaultdict(int)
        self.mastery_flag = {}
        for oid in world.attractor_cells:
            self.mastery_flag[oid] = 0
        self.time_to_first_mastery = None
        self.time_to_final_mastery = None
        self.mastery_order_sequence = []

        # ----------------------------------------------------------------
        # End-state (V013Agent)
        # ----------------------------------------------------------------
        self.activation_step = None
        self.end_state_cell = world.end_state_cell
        self.end_state_found_step = None
        self.end_state_visits = 0
        self.end_state_banked = False

        # ----------------------------------------------------------------
        # Knowledge layer (V014Agent, keyed by object_id)
        # ----------------------------------------------------------------
        self.knowledge_entry_counter = defaultdict(int)
        self.knowledge_banked = {h: False for h in world.hazard_cells}
        self.competency_unlock_step = {h: None for h in world.hazard_cells}
        self.knowledge_banked_step = {h: None for h in world.hazard_cells}
        self.pre_transition_hazard_entries = defaultdict(int)
        self.hazard_competency_thresholds = dict(world.hazard_competency_thresholds)
        self.time_to_first_transition = None
        self.time_to_final_transition = None
        self.transition_order_sequence = []
        self.knowledge_banked_sequence = []

        # Track world knowledge_unlocked state for competency check
        # (in V13World this was world.knowledge_unlocked; here we track
        # it directly on the agent since V17World.transform_to_knowledge
        # updates world.object_type which we read directly)
        self._knowledge_unlocked = {h: False for h in world.hazard_cells}

        # ----------------------------------------------------------------
        # Rule-adherence tracking
        # ----------------------------------------------------------------
        self.frame_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_attempts_by_phase = {1: 0, 2: 0, 3: 0}
        self.hazard_entries_by_phase = {1: 0, 2: 0, 3: 0}
        self.total_cost_incurred = 0.0
        self.hazard_gated_by_threat_layer = {1: 0, 2: 0, 3: 0}

        # ----------------------------------------------------------------
        # V013/V014 schema (carried via V12Agent; no-op in V17Agent
        # since V13SchemaObserver reads from world attributes not agent)
        # ----------------------------------------------------------------
        # The V12Agent sets self.schema in its __init__. We set it to
        # None here; V13SchemaObserver builds the schema from the world
        # directly, not from agent.schema. This is safe.
        # Build schema for V13SchemaObserver (query_schema interface)
        from v1_2_schema import _build_cell_type_schema, _build_action_schema, _build_phase_schema, _build_flag_type_schema
        self._schema = {
            'cell_types':  _build_cell_type_schema(),
            'actions':     _build_action_schema(),
            'phases':      _build_phase_schema(),
            'flag_types':  _build_flag_type_schema(),
        }
        # Add DIST_OBJ to schema cell types
        from curiosity_agent_v1_7_world import DIST_OBJ
        self._schema['cell_types']['DIST_OBJ'] = {
            'code': DIST_OBJ, 'passable': True, 'cost_on_entry': None,
            'feature_reward_eligible': False, 'attraction_bias_eligible': False,
            'gating_eligible': False, 'transformation_eligible': False,
        }
        self.schema = None  # legacy attribute name

        self._apply_phase_weights()

    # ------------------------------------------------------------------
    # Phase weight application (inherited logic, called from __init__)
    # ------------------------------------------------------------------

    def query_schema(self, section):
        """Return schema section (V12Agent interface, required by V13SchemaObserver)."""
        import copy
        return copy.deepcopy(self._schema.get(section, {}))

    def _apply_phase_weights(self):
        if self.phase == 1:
            self.novelty_weight    = 0.0
            self.progress_weight   = 0.0
            self.preference_weight = 0.0
            self.feature_weight    = 0.0
        elif self.phase == 2:
            self.novelty_weight    = 0.3
            self.progress_weight   = 1.2
            self.preference_weight = 0.0
            self.feature_weight    = FEATURE_DRIVE_WEIGHT
        elif self.phase == 3:
            self.novelty_weight    = 0.3
            self.progress_weight   = 0.3
            self.preference_weight = 0.5
            self.feature_weight    = FEATURE_DRIVE_WEIGHT

    def _transition_phase(self, new_phase):
        self.phase = new_phase
        self._apply_phase_weights()
        if new_phase == 2:
            # Reset Q-values partially on phase transition (inherited)
            for k in list(self.q_values.keys()):
                self.q_values[k] *= 0.3

    # ------------------------------------------------------------------
    # Phase management (3D version)
    # ------------------------------------------------------------------

    def check_phase_transition(self):
        if self.phase == 1:
            # Phase 1 ends when all waypoints visited
            if self._waypoint_idx >= len(self._waypoints):
                self.phase_1_end_step = self.steps_taken
                self._transition_phase(2)
                return True
        elif self.phase == 2:
            if self.steps_taken >= self.phase_3_start_target:
                self.phase_2_end_step = self.steps_taken
                self._transition_phase(3)
                return True
        return False

    # ------------------------------------------------------------------
    # Phase 1 waypoint following
    # ------------------------------------------------------------------

    def get_prescribed_action(self):
        """Return action that moves toward current waypoint.

        Replaces grid boustrophedon path following. Returns None when
        all waypoints have been visited (triggers Phase 2 transition).
        """
        if self._waypoint_idx >= len(self._waypoints):
            return None

        target = self._waypoints[self._waypoint_idx]
        pos = self.world.agent_pos

        # Advance waypoint if agent is close enough
        if _dist3(pos, target) < self._waypoint_arrival_threshold:
            self._waypoint_idx += 1
            if self._waypoint_idx >= len(self._waypoints):
                return None
            target = self._waypoints[self._waypoint_idx]

        # Choose action whose direction vector best approximates
        # the vector from pos to target
        tx, ty, tz = target
        px, py, pz = pos
        dx, dy, dz = tx - px, ty - py, tz - pz
        norm = math.sqrt(dx*dx + dy*dy + dz*dz) + 1e-8
        dx, dy, dz = dx/norm, dy/norm, dz/norm

        best_action = 0
        best_dot = -2.0
        for i, (vx, vy, vz) in enumerate(_DIRECTION_VECTORS):
            dot = dx*vx + dy*vy + dz*vz
            if dot > best_dot:
                best_dot = dot
                best_action = i
        return best_action

    # ------------------------------------------------------------------
    # Substrate-interface: action gating (3D)
    # ------------------------------------------------------------------

    def _get_destination_cell(self, state, action):
        """Estimate destination object_id for action from state.

        In V17World, actions move the agent by STEP_SIZE in a direction
        vector. This method is called only by _action_is_gated to check
        whether the destination is a threat-flagged HAZARD object. We
        estimate the post-move position and return the object_id of any
        HAZARD object within CONTACT_RADIUS of that position, or None.
        """
        if action == 26:
            return None  # stay action: no destination
        if not (0 <= action < 26):
            return None
        dx, dy, dz = _DIRECTION_VECTORS[action]
        x, y, z = state[0], state[1], state[2] if len(state) > 2 else 0.0
        from curiosity_agent_v1_7_world import _clamp, WORLD_SIZE
        nx = _clamp(x + dx * STEP_SIZE, 0.0, WORLD_SIZE)
        ny = _clamp(y + dy * STEP_SIZE, 0.0, WORLD_SIZE)
        nz = _clamp(z + dz * STEP_SIZE, 0.0, WORLD_SIZE)
        # Check if any hazard object is within contact radius of destination
        for oid, opos in self.world.object_positions.items():
            if self.world.object_type.get(oid) == HAZARD:
                if _dist3((nx, ny, nz), opos) <= CONTACT_RADIUS:
                    return oid
        return None

    def _action_is_gated(self, state, action):
        """Gate actions that would contact a threat-flagged HAZARD object.

        Parallel to V014Agent._action_is_gated but using object_ids.
        An action is gated if the estimated destination is a HAZARD-typed
        object with threat_flag == 1. Post-transformation (KNOWLEDGE-typed)
        objects with persisting threat_flag are not gated.
        """
        dest_oid = self._get_destination_cell(state, action)
        if dest_oid is None:
            return False
        if self.threat_flag.get(dest_oid, 0) != 1:
            return False
        dest_type = self.world.object_type.get(dest_oid, NEUTRAL)
        if dest_type == KNOWLEDGE:
            return False
        return True

    # ------------------------------------------------------------------
    # Substrate-interface: primitive bias (3D)
    # ------------------------------------------------------------------

    def _primitive_bias(self, state):
        """Compute action biases from objects perceived within radius.

        Replaces the 4-neighbour grid bias with a radial perception bias.
        For each action direction, computes a bias based on objects that
        would be contacted if the agent moved in that direction. This is
        a forward-looking bias: does this action bring the agent closer
        to a rewarding object or away from a costly one?

        Returns numpy array of shape (num_actions,).
        """
        biases = np.zeros(self.num_actions)
        pos = self.world.agent_pos
        from curiosity_agent_v1_7_world import _clamp, WORLD_SIZE

        for action in range(self.num_actions):
            if action == 26:
                # Stay: no positional change; use current contact as bias
                contact_oid = self.world._contact_at_pos(pos)
                if contact_oid is not None:
                    t = self.world.object_type.get(contact_oid, NEUTRAL)
                    biases[action] = self._object_bias_value(contact_oid, t)
                continue

            dx, dy, dz = _DIRECTION_VECTORS[action]
            nx = _clamp(pos[0] + dx * STEP_SIZE, 0.0, WORLD_SIZE)
            ny = _clamp(pos[1] + dy * STEP_SIZE, 0.0, WORLD_SIZE)
            nz = _clamp(pos[2] + dz * STEP_SIZE, 0.0, WORLD_SIZE)

            # Check objects near the destination position
            dest_pos = (nx, ny, nz)
            max_bias = 0.0
            for oid, opos in self.world.object_positions.items():
                d = _dist3(dest_pos, opos)
                if d <= PERCEPTION_RADIUS:
                    t = self.world.object_type.get(oid, NEUTRAL)
                    b = self._object_bias_value(oid, t)
                    # Weight bias by proximity (closer = stronger pull)
                    weight = 1.0 - (d / PERCEPTION_RADIUS)
                    b_weighted = b * (0.5 + 0.5 * weight)
                    if abs(b_weighted) > abs(max_bias):
                        max_bias = b_weighted
            biases[action] = max_bias

        return biases

    def _object_bias_value(self, oid, obj_type):
        """Return primitive bias value for a single object."""
        if obj_type == ATTRACTOR:
            if self.mastery_flag.get(oid, 0) == 0:
                return ATTRACTION_BONUS
        elif obj_type == END_STATE:
            if not self.end_state_banked:
                return ATTRACTION_BONUS
        elif obj_type == KNOWLEDGE:
            if not self.knowledge_banked.get(oid, False):
                return ATTRACTION_BONUS
        elif obj_type == DIST_OBJ:
            # Distal objects attract mildly (novelty-like)
            return ATTRACTION_BONUS * 0.5
        # HAZARD and NEUTRAL: no pre-wired bias (consistent with V014Agent)
        return 0.0

    # ------------------------------------------------------------------
    # Substrate-interface: visit counts (3D)
    # ------------------------------------------------------------------

    def _position_bucket(self, pos):
        """Return a discretised position key for visit counting.

        Rounds position to the nearest 0.5 unit. This gives a visit
        count that is more granular than object-contact-only but
        coarser than exact float equality.
        """
        x, y, z = pos
        return (round(x * 2) / 2, round(y * 2) / 2, round(z * 2) / 2)

    # ------------------------------------------------------------------
    # Action selection (3D)
    # ------------------------------------------------------------------

    def choose_action(self, state):
        """Select action for current state.

        Phase 1: follow waypoints via get_prescribed_action().
        Phases 2-3: epsilon-greedy with primitive bias + Q-values,
        subject to threat-gate filter.
        """
        if self.phase == 1:
            prescribed = self.get_prescribed_action()
            if prescribed is not None:
                return prescribed
            # Waypoints exhausted: trigger phase transition
            self.check_phase_transition()

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
        values = np.array(
            [self.q_values[(state, a)] for a in range(self.num_actions)]
        )
        combined = values + biases
        mask = np.array([a in candidate_actions for a in all_actions])
        combined = np.where(mask, combined, -np.inf)
        max_v = combined.max()
        best = [a for a in candidate_actions if combined[a] == max_v]
        if not best:
            return int(np.random.choice(candidate_actions))
        return int(np.random.choice(best))

    # ------------------------------------------------------------------
    # Cognitive-layer override: check_competency_unlocks (3D world)
    # ------------------------------------------------------------------

    def check_competency_unlocks(self, step):
        """Check competency thresholds and trigger HAZARD→KNOWLEDGE.

        Parallel to V014Agent.check_competency_unlocks but uses
        world.transform_to_knowledge(object_id) rather than
        world.transition_hazard_to_knowledge(cell). The cognitive-layer
        logic — compare sum(mastery_flag) against per-object thresholds,
        fire at most once per step per object — is identical.

        Family hazards (haz_green, haz_yellow) use family-specific gating:
        precondition_met = mastery_flag[precondition_attractor] == 1.
        Unaffiliated hazards use global threshold.
        """
        current_competency = sum(self.mastery_flag.values())

        for oid in sorted(self.world.hazard_cells):
            # Skip already-transformed objects
            if self._knowledge_unlocked.get(oid, False):
                continue
            if self.world.object_type.get(oid) == KNOWLEDGE:
                self._knowledge_unlocked[oid] = True
                continue

            # Determine precondition
            precondition_attractor = self.world.family_precondition_attractor.get(oid)
            if precondition_attractor is not None:
                # Family cell: use mastery_flag of precondition attractor
                if self.mastery_flag.get(precondition_attractor, 0) != 1:
                    continue
                precondition_met = True
            else:
                # Unaffiliated: use global threshold
                threshold = self.hazard_competency_thresholds.get(oid)
                if threshold is None:
                    continue
                if current_competency < threshold:
                    continue
                precondition_met = True

            if precondition_met:
                self.world.transform_to_knowledge(oid)
                self._knowledge_unlocked[oid] = True
                self.competency_unlock_step[oid] = step
                self.transition_order_sequence.append(oid)
                if self.time_to_first_transition is None:
                    self.time_to_first_transition = step
                self.time_to_final_transition = step

    # ------------------------------------------------------------------
    # Cognitive-layer override: record_action_outcome (3D bridge)
    # ------------------------------------------------------------------

    def record_action_outcome(self, contact_oid, success, cost_incurred, world, step):
        """Bridge V17World contact events to the cognitive-layer outcome record.

        contact_oid: the object_id contacted at this step, or None.
        success: True if agent moved (or stayed and contacted an object).
        cost_incurred: float cost paid (hazard_cost or 0.0).
        world: V17World instance.
        step: current step number.

        The cognitive-layer logic is the same as V014Agent but uses
        object_id keys throughout.
        """
        if contact_oid is None:
            # No contact — track visit count for current position
            bucket = self._position_bucket(world.agent_pos)
            self.visit_counts[bucket] += 1
            self.steps_taken += 1
            self.check_phase_transition()
            return

        # Contact event
        target_type_at_entry = world.object_type.get(contact_oid, NEUTRAL)

        if cost_incurred > 0:
            self.hazard_entries_by_phase[self.phase] += 1
            self.total_cost_incurred += cost_incurred
            self.update_threat_layer(contact_oid, step)
            if contact_oid in world.hazard_cells:
                self.pre_transition_hazard_entries[contact_oid] += 1

        if target_type_at_entry == ATTRACTOR:
            self.update_mastery_layer(contact_oid, step)

        if (target_type_at_entry == END_STATE
                and self.activation_step is not None):
            self.end_state_visits += 1
            if not self.end_state_banked:
                self.end_state_found_step = step
                self.end_state_banked = True
                self.cell_preference[self.end_state_cell] = 0.0

        if target_type_at_entry == KNOWLEDGE:
            self.update_knowledge_layer(contact_oid, step)

        # Visit count for position bucket
        bucket = self._position_bucket(world.agent_pos)
        self.visit_counts[bucket] += 1

        self.check_competency_unlocks(step)

        # End-state activation check
        if self.activation_step is None:
            all_attractors_mastered = (
                sum(self.mastery_flag.values()) == len(world.attractor_cells)
            )
            all_hazards_banked = (
                sum(1 for v in self.knowledge_banked.values() if v)
                == len(world.hazard_cells)
            )
            if all_attractors_mastered and all_hazards_banked:
                self.activation_step = step
                world.activate_end_state()

        self.steps_taken += 1
        self.check_phase_transition()

    # ------------------------------------------------------------------
    # Reward computation (3D — uses contact_oid as state proxy)
    # ------------------------------------------------------------------

    def novelty_reward(self, state):
        bucket = self._position_bucket(self.world.agent_pos)
        count = self.visit_counts[bucket]
        return self.novelty_weight / (count**0.5 + 1)

    def feature_reward(self, state):
        """Feature reward based on contact type at current position."""
        if self.feature_weight == 0.0:
            return 0.0
        contact_oid = self.world._contact_at_pos(self.world.agent_pos)
        if contact_oid is None:
            return 0.0
        obj_type = self.world.object_type.get(contact_oid, NEUTRAL)
        if obj_type == END_STATE:
            return 0.0 if self.end_state_banked else self.feature_weight
        if obj_type == KNOWLEDGE:
            if self.knowledge_banked.get(contact_oid, False):
                return 0.0
            return self.feature_weight
        if obj_type == ATTRACTOR:
            if self.mastery_flag.get(contact_oid, 0) == 1:
                # Banking step bonus (parallel to V011Agent MASTERY_BONUS)
                visits = self.attractor_visit_counter.get(contact_oid, 0)
                if visits == MASTERY_THRESHOLD:
                    return MASTERY_BONUS
                return 0.0
            return self.feature_weight
        return 0.0

    def preference_reward(self, state):
        if self.preference_weight == 0.0:
            return 0.0
        contact_oid = self.world._contact_at_pos(self.world.agent_pos)
        if contact_oid is None:
            return 0.0
        return self.preference_weight * self.cell_preference[contact_oid]

    def update_model(self, state, action, next_state):
        """Update forward model and cell preference.

        In 3D, 'cell' is the contacted object_id. If no contact, updates
        position bucket only.
        """
        contact_oid = self.world._contact_at_pos(self.world.agent_pos)
        key = contact_oid if contact_oid is not None else self._position_bucket(self.world.agent_pos)

        self.forward_model[state][action] += 1
        r_progress = (
            self.progress_weight * (
                self.fast_errors[key] and sum(self.fast_errors[key]) / len(self.fast_errors[key])
                or 0.0
            ) if self.progress_weight > 0.0 else 0.0
        )
        r_feature = self.feature_reward(state)

        if contact_oid is not None:
            # Don't accumulate preference on banked objects
            already_banked = (
                (self.world.object_type.get(contact_oid) == KNOWLEDGE
                 and self.knowledge_banked.get(contact_oid, False))
                or (contact_oid == self.end_state_cell and self.end_state_banked)
                or self.mastery_flag.get(contact_oid, 0) == 1
            )
            if not already_banked:
                self.cell_preference[contact_oid] += r_progress + r_feature

    def update_values(self, state, action, next_state, intrinsic):
        if self.phase == 1:
            return
        future = max(
            self.q_values[(next_state, a)] for a in range(self.num_actions)
        )
        td_target = intrinsic + 0.9 * future
        td_error = td_target - self.q_values[(state, action)]
        self.q_values[(state, action)] += self.learning_rate * td_error
