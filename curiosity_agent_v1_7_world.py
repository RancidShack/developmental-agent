"""
curiosity_agent_v1_7_world.py
------------------------------
v1.7 world: 3D continuous-space substrate transposition.

Replaces the 20x20 tabular grid (V13World) with a bounded 3D
continuous-space environment. The agent has a real-valued (x, y, z)
position and navigates by choosing from a discrete action set that
applies velocity vectors. Objects exist at fixed real-valued
coordinates and persist after transformation.

THEORETICAL GROUNDING (pre-registration §1)
The Montessori prepared environment principle requires a substrate in
which object contact has the quality of an encounter rather than a
cell-entry event. Object-relations theory holds that the self emerges
through internalisations of repeated object encounters: the object is
first perceived at a distance, then approached, then contacted, then
internalised — held as a known entity after transformation. V17World
gives spatial form to this sequence. Objects can be perceived before
contact (approach phase), contacted to produce mastery or cost events
(contact phase), and retained as known entities after transformation
(persistence after internalisation).

SUBSTRATE INTERFACE CONTRACT
V17World exposes the same interface attributes the cognitive layer
reads from V13World:

    world.agent_pos          -> current agent position (x, y, z) floats
    world.object_type        -> dict: object_id -> object type constant
    world.cell_type          -> dict: object_id -> type constant
                                (alias of object_type; satisfies
                                 pre_transition_hazard_entries detection
                                 in V15PredictionErrorObserver)
    world.attractor_cells    -> set of object_ids for ATTRACTOR objects
    world.hazard_cells       -> set of object_ids for HAZARD/KNOWLEDGE
    world.scope_cells        -> set of all object_ids in play
    world.end_state_cell     -> object_id of the END_STATE object
    world.hazard_cost        -> scalar cost paid on costly-object contact
    world.hazard_competency_thresholds -> dict: object_id -> int threshold
    world.family_precondition_attractor -> dict: hazard_id -> attractor_id

    world.perceive_within_radius(pos, r) -> list of (object_type, object_id)
    world.step(action) -> (obs, object_id_or_None, moved, cost)
    world.observe()    -> state tuple

KEY DESIGN DECISIONS

1. Object identity by string ID, not coordinates.
   Object IDs are stable strings (e.g. "att_green", "haz_green",
   "dist_green", "att_yellow", "haz_yellow", "dist_yellow",
   "att_free_0" ... "att_free_3", "haz_unaff_0" ... "haz_unaff_2",
   "end_state", "threshold_object").
   The cognitive layer's flag IDs will use these string IDs rather
   than grid coordinates. This is the substrate-interface migration
   of the mastery:(4,15) / mastery:(16,3) format.

2. cell_type dict keyed by object_id.
   The prediction-error observer reads world.cell_type to detect
   HAZARD→KNOWLEDGE transitions. V17World provides this dict keyed
   by object_id. The observer's _prev_cell_type cache, transition
   detection, and _tracked_cells set all operate on object_ids.

3. Actions: 26 directions + stay.
   The 3D action space has 26 unit-direction vectors (all combinations
   of {-1, 0, 1}^3 minus (0,0,0)) plus a stay action (index 26).
   The agent's num_actions = 27. Each move applies a step of size
   STEP_SIZE in the chosen direction, bounded to the world volume.

4. Approach phase: perceive_within_radius.
   The agent can perceive objects within PERCEPTION_RADIUS without
   contacting them. Contact fires on distance < CONTACT_RADIUS.
   perceive_adjacent() is provided as an alias that calls
   perceive_within_radius(agent_pos, PERCEPTION_RADIUS) for
   compatibility with any cognitive-layer code that calls it, but
   the canonical method is perceive_within_radius.

5. Objects persist after transformation.
   When a HAZARD object is banked as KNOWLEDGE, its object_id and
   real-valued position are retained. The spatial location remains
   meaningful. The object's type in object_type changes from HAZARD
   to KNOWLEDGE; its coordinates are unchanged.

6. Phase 1 path planning.
   The grid's boustrophedon Phase 1 path is replaced by a space-
   filling waypoint sequence that visits all object positions plus
   a grid of waypoints at WAYPOINT_SPACING intervals. The agent
   follows this sequence in Phase 1 by choosing actions that move
   toward the current waypoint, advancing to the next on arrival.

FAMILY STRUCTURE (preserved from v1.3)
GREEN family:
    Distal object (DIST_OBJ):  id="dist_green",  pos=(3.0, 9.0, 3.0),
                                colour=GREEN, form=FLAT
    Acquirable (ATTRACTOR):    id="att_green",   pos=(2.0, 11.0, 2.0),
                                colour=GREEN, form=SQUARE_2D
    Bankable (HAZARD):         id="haz_green",   pos=(9.0, 10.0, 8.0),
                                colour=GREEN, form=SPHERE_3D

YELLOW family:
    Distal object (DIST_OBJ):  id="dist_yellow", pos=(8.0, 3.0, 3.0),
                                colour=YELLOW, form=FLAT
    Acquirable (ATTRACTOR):    id="att_yellow",  pos=(10.0, 2.0, 2.0),
                                colour=YELLOW, form=TRIANGLE_2D
    Bankable (HAZARD):         id="haz_yellow",  pos=(3.0, 5.0, 7.0),
                                colour=YELLOW, form=PYRAMID_3D

Unaffiliated attractors (4):
    att_free_0 .. att_free_3 — positions chosen to spread across volume

Unaffiliated hazards (3):
    haz_unaff_0 .. haz_unaff_2 — positions chosen to spread across volume

End-state object:
    Sampled from unaffiliated attractor positions at run init (seeded).

PRESERVED COMPETENCY GATE (v1.3.2 rule)
The GREEN bankable object (haz_green) cannot transition to KNOWLEDGE
until the GREEN acquirable object (att_green) is mastered (mastery_flag
for att_green is 1). Equivalently for YELLOW. Unaffiliated hazards use
the global competency threshold gate.

family_precondition_attractor = {
    "haz_green":  "att_green",
    "haz_yellow": "att_yellow",
}
"""

import math
import numpy as np
from collections import defaultdict

# ---------------------------------------------------------------------------
# Object type constants — same integer values as v0.14 cell types so that
# any code comparing against FRAME, NEUTRAL, HAZARD, etc. works unchanged.
# ---------------------------------------------------------------------------
FRAME     = 0   # out-of-bounds / boundary sentinel
NEUTRAL   = 1   # open space / passable waypoint
HAZARD    = 2   # costly object (pre-transformation)
ATTRACTOR = 3   # acquirable object
END_STATE = 4   # threshold object
KNOWLEDGE = 5   # post-transformation object (was HAZARD)
DIST_OBJ  = 6   # distal perceivable object (was COLOUR_CELL)

# ---------------------------------------------------------------------------
# Family vocabulary (preserved from v1.3)
# ---------------------------------------------------------------------------
GREEN  = "GREEN"
YELLOW = "YELLOW"

FLAT         = "FLAT"
SQUARE_2D    = "SQUARE_2D"
TRIANGLE_2D  = "TRIANGLE_2D"
SPHERE_3D    = "SPHERE_3D"
PYRAMID_3D   = "PYRAMID_3D"

# ---------------------------------------------------------------------------
# World geometry
# ---------------------------------------------------------------------------
WORLD_SIZE       = 12.0   # cubic volume [0, WORLD_SIZE]^3
STEP_SIZE        = 1.0    # distance per action
PERCEPTION_RADIUS = 3.0   # objects within this radius are perceivable
CONTACT_RADIUS    = 0.8   # objects within this radius are contacted
WAYPOINT_SPACING  = 2.5   # grid spacing for Phase 1 waypoints
START_POS         = (1.0, 1.0, 1.0)

# Number of discrete actions: 26 directions + 1 stay
NUM_ACTIONS = 27

# Pre-computed direction vectors for actions 0..25; action 26 = stay
_DIRECTION_VECTORS = []
for dz in (-1, 0, 1):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0 and dz == 0:
                continue
            _DIRECTION_VECTORS.append((dx, dy, dz))
# _DIRECTION_VECTORS has exactly 26 entries; action 26 appended below
# (stay is handled in step() by index check, not stored here)

# ---------------------------------------------------------------------------
# Object layout
# ---------------------------------------------------------------------------

# Family objects: fixed positions chosen to spread meaningfully across
# the volume, analogous to fixed grid coordinates in V13World.
OBJECT_POSITIONS = {
    # GREEN family
    "dist_green":  (3.0,  9.0,  3.0),
    "att_green":   (2.0,  11.0, 2.0),
    "haz_green":   (9.0,  10.0, 8.0),
    # YELLOW family
    "dist_yellow": (8.0,  3.0,  3.0),
    "att_yellow":  (10.0, 2.0,  2.0),
    "haz_yellow":  (3.0,  5.0,  7.0),
    # Unaffiliated attractors (6 total, matching v0.14's 6 ATTRACTOR_CELLS)
    "att_free_0":  (5.0,  2.0,  5.0),
    "att_free_1":  (9.0,  5.0,  2.0),
    "att_free_2":  (6.0,  8.0,  1.0),
    "att_free_3":  (11.0, 9.0,  5.0),
    # Unaffiliated hazards (3 total, matching v0.14's 3 unaffiliated hazards)
    "haz_unaff_0": (5.0,  6.0,  9.0),
    "haz_unaff_1": (6.0,  5.0,  10.0),
    "haz_unaff_2": (10.0, 7.0,  4.0),
}

OBJECT_BASE_TYPE = {
    "dist_green":  DIST_OBJ,
    "dist_yellow": DIST_OBJ,
    "att_green":   ATTRACTOR,
    "att_yellow":  ATTRACTOR,
    "att_free_0":  ATTRACTOR,
    "att_free_1":  ATTRACTOR,
    "att_free_2":  ATTRACTOR,
    "att_free_3":  ATTRACTOR,
    "haz_green":   HAZARD,
    "haz_yellow":  HAZARD,
    "haz_unaff_0": HAZARD,
    "haz_unaff_1": HAZARD,
    "haz_unaff_2": HAZARD,
    # end_state: sampled at run init; added dynamically
}

OBJECT_COLOUR = {
    "dist_green":  GREEN,
    "att_green":   GREEN,
    "haz_green":   GREEN,
    "dist_yellow": YELLOW,
    "att_yellow":  YELLOW,
    "haz_yellow":  YELLOW,
}

OBJECT_FORM = {
    "dist_green":  FLAT,
    "att_green":   SQUARE_2D,
    "haz_green":   SPHERE_3D,
    "dist_yellow": FLAT,
    "att_yellow":  TRIANGLE_2D,
    "haz_yellow":  PYRAMID_3D,
}

# Family precondition: hazard_id -> precondition_attractor_id
# (v1.3.2 rule preserved at cognitive level)
FAMILY_PRECONDITION = {
    "haz_green":  "att_green",
    "haz_yellow": "att_yellow",
}

# Unaffiliated hazard ids
UNAFFILIATED_HAZARD_IDS = frozenset(["haz_unaff_0", "haz_unaff_1", "haz_unaff_2"])

# End-state candidates: any attractor can become the end-state object
END_STATE_CANDIDATES = [
    "att_free_0", "att_free_1", "att_free_2", "att_free_3"
]

# ---------------------------------------------------------------------------
# Phase 1 waypoint generation
# ---------------------------------------------------------------------------

def _build_phase1_waypoints():
    """Build a space-filling waypoint sequence for Phase 1 exploration.

    Generates a 3D boustrophedon-style traversal of the world volume
    at WAYPOINT_SPACING intervals, then appends all object positions
    not already covered. Returns ordered list of (x, y, z) floats.
    """
    waypoints = []
    spacing = WAYPOINT_SPACING
    coords = []
    z = 1.0
    while z <= WORLD_SIZE - 1.0:
        y = 1.0
        while y <= WORLD_SIZE - 1.0:
            x = 1.0
            while x <= WORLD_SIZE - 1.0:
                coords.append((x, y, z))
                x += spacing
            y += spacing
        z += spacing

    # Boustrophedon ordering: reverse alternating rows
    # (simple: keep as-is; sufficient for coverage)
    waypoints = list(coords)

    # Append object positions not already close to a waypoint
    for pos in OBJECT_POSITIONS.values():
        if all(_dist3(pos, w) > spacing * 0.5 for w in waypoints):
            waypoints.append(pos)

    return waypoints


def _dist3(a, b):
    return math.sqrt(
        (a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2
    )


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# V17World
# ---------------------------------------------------------------------------

class V17World:
    """v1.7 world: 3D continuous-space substrate.

    Exposes the same interface contract as V13World so that the cognitive
    layer (provenance, schema, family, comparison, prediction-error
    observers) and the agent (V15Agent via V14Agent→V13Agent→V014Agent)
    operate unchanged at the cognitive level.

    The substrate-interface migration from coord-keys to object_id-keys
    is the primary substrate-interface work at v1.7. Cognitive-layer code
    that was reading world.cell_type[(x,y)] now reads world.cell_type[oid].
    Code that used mastery:(4, 15) flag IDs now uses mastery:att_green etc.
    These are substrate-interface changes; no cognitive-layer logic changes.
    """

    def __init__(self, hazard_cost, size=WORLD_SIZE, seed=None):
        self.hazard_cost = hazard_cost
        self.size        = size
        self._rng        = np.random.default_rng(seed)

        # Agent position
        self.agent_pos = START_POS

        # Object layout
        self.object_positions = dict(OBJECT_POSITIONS)
        self.object_type      = {oid: t for oid, t in OBJECT_BASE_TYPE.items()}

        # Assign end-state object (seeded, parallel to v0.14 sampling)
        self._sample_end_state()

        # Assign hazard competency thresholds (seeded, parallel to v0.14)
        self._assign_hazard_competency_thresholds()

        # Family precondition mapping (cognitive-layer contract)
        self.family_precondition_attractor = dict(FAMILY_PRECONDITION)

        # cell_type: alias of object_type for observer compatibility
        # (V15PredictionErrorObserver reads world.cell_type[cell])
        self.cell_type = self.object_type

        # Convenience sets (cognitive-layer contract)
        self.attractor_cells = {
            oid for oid, t in self.object_type.items() if t == ATTRACTOR
        }
        self.hazard_cells = {
            oid for oid, t in self.object_type.items()
            if t in (HAZARD, KNOWLEDGE)
        }
        self.scope_cells = set(self.object_type.keys())

        # Phase 1 waypoints
        self._waypoints = _build_phase1_waypoints()
        self._waypoint_idx = 0

        # Per-object visit tracking (used by cognitive layer for
        # visit_counts equivalent — keyed by object_id)
        # The agent's visit_counts dict is keyed by "position" in the
        # grid world; in V17World, contact events serve as visits.
        self._contact_counts = defaultdict(int)

    # ------------------------------------------------------------------
    # Seeded initialisation
    # ------------------------------------------------------------------

    def _sample_end_state(self):
        """Sample end-state object from candidates (seeded).

        Parallel to v0.14's _sample_end_state_cell. The sampled object
        changes type from ATTRACTOR to END_STATE.
        """
        candidates = list(END_STATE_CANDIDATES)
        idx = int(self._rng.integers(0, len(candidates)))
        self.end_state_cell = candidates[idx]
        self.object_type[self.end_state_cell] = END_STATE
        # Update attractor set (end_state_cell is no longer ATTRACTOR)
        # Done after __init__ completes; self.attractor_cells rebuilt below.

    def _assign_hazard_competency_thresholds(self):
        """Assign competency thresholds to unaffiliated hazards (seeded).

        Unaffiliated hazards get thresholds from {1, 2, 3} (3 cells,
        matching v0.14's 5 hazards → 5 thresholds but scaled to 3).
        Family hazards (haz_green, haz_yellow) use family-specific
        gating (family_precondition_attractor) rather than thresholds.
        """
        unaff = sorted(UNAFFILIATED_HAZARD_IDS)
        # Draw a random permutation of thresholds [1, 2, 3]
        thresholds = list(range(1, len(unaff) + 1))
        perm = self._rng.permutation(len(thresholds))
        self.hazard_competency_thresholds = {}
        for i, oid in enumerate(unaff):
            self.hazard_competency_thresholds[oid] = int(thresholds[perm[i]])
        # Family hazards: threshold slot preserved but not consulted for
        # family-specific gating (mirror of v1.3.2 behaviour).
        self.hazard_competency_thresholds["haz_green"]  = 99
        self.hazard_competency_thresholds["haz_yellow"] = 99

    # ------------------------------------------------------------------
    # Perception
    # ------------------------------------------------------------------

    def perceive_within_radius(self, pos, radius):
        """Return list of (object_type, object_id) within radius of pos.

        Objects within CONTACT_RADIUS are also included. DIST_OBJ
        objects are perceivable at full PERCEPTION_RADIUS; all objects
        are perceivable within CONTACT_RADIUS.
        """
        results = []
        for oid, opos in self.object_positions.items():
            d = _dist3(pos, opos)
            if d <= radius:
                results.append((self.object_type[oid], oid))
        return results

    def perceive_adjacent(self, pos_or_cell):
        """Compatibility alias for V013Agent's perceive_adjacent call.

        The base agent calls world.perceive_adjacent(self.agent_pos)
        from observe(). In V17World, this returns the types of all
        objects within PERCEPTION_RADIUS as a tuple.

        The return value is a tuple of object types (integers) for
        compatibility with the observation format; object_ids are not
        included here (the agent's observation format uses ints).
        The full (type, id) pairs are available via
        perceive_within_radius().
        """
        if isinstance(pos_or_cell, tuple) and len(pos_or_cell) == 3:
            pos = pos_or_cell
        else:
            pos = self.agent_pos
        nearby = self.perceive_within_radius(pos, PERCEPTION_RADIUS)
        # Return as fixed-length tuple of 26 slots (matching num_actions-1)
        # padded with NEUTRAL. The agent uses this for action bias; the
        # exact length matters less than the content.
        types = tuple(t for t, _ in nearby)
        # Pad to 26 entries with NEUTRAL for interface compatibility
        padded = (types + (NEUTRAL,) * 26)[:26]
        return padded

    def observe(self):
        """Return state observation tuple.

        Format: (x, y, z, object_type_at_contact, *perceived_types)
        where object_type_at_contact is the type of any object within
        CONTACT_RADIUS (or NEUTRAL if none), and perceived_types is
        the tuple from perceive_adjacent.

        This extends the grid observe() signature (x, y, ctype, *adj)
        to 3D continuous space: (x, y, z, contact_type, *perceived).
        The agent's state indexing uses [0],[1] for position — in the
        grid world these were (row, col); here they are (x, y) with z
        available at [2]. The agent's _get_destination_cell uses
        state[0] and state[1] which still function as position
        coordinates.
        """
        x, y, z = self.agent_pos
        contact_type = NEUTRAL
        for oid, opos in self.object_positions.items():
            if _dist3(self.agent_pos, opos) <= CONTACT_RADIUS:
                contact_type = self.object_type[oid]
                break
        adj = self.perceive_adjacent(self.agent_pos)
        return (x, y, z, contact_type, *adj)

    # ------------------------------------------------------------------
    # Step function
    # ------------------------------------------------------------------

    def step(self, action):
        """Apply action and return (obs, contact_id, moved, cost).

        action: integer in [0, 26].
          0..25: move in corresponding direction vector at STEP_SIZE.
          26:    stay in place.

        Returns:
          obs:        observation tuple from observe()
          contact_id: object_id of any object within CONTACT_RADIUS
                      after the move, or None if no contact.
          moved:      True if agent position changed.
          cost:       float cost incurred (hazard_cost if HAZARD contact,
                      else 0.0).
        """
        if action == 26:
            # Stay
            return self.observe(), self._contact_at_pos(self.agent_pos), False, 0.0

        if 0 <= action < 26:
            dx, dy, dz = _DIRECTION_VECTORS[action]
        else:
            dx, dy, dz = 0, 0, 0

        x, y, z = self.agent_pos
        nx = _clamp(x + dx * STEP_SIZE, 0.0, self.size)
        ny = _clamp(y + dy * STEP_SIZE, 0.0, self.size)
        nz = _clamp(z + dz * STEP_SIZE, 0.0, self.size)

        moved = (nx, ny, nz) != (x, y, z)
        self.agent_pos = (nx, ny, nz)

        contact_id = self._contact_at_pos(self.agent_pos)
        if contact_id is not None:
            self._contact_counts[contact_id] += 1

        cost = 0.0
        if contact_id is not None:
            obj_type = self.object_type[contact_id]
            if obj_type == HAZARD:
                cost = self.hazard_cost

        return self.observe(), contact_id, moved, cost

    def _contact_at_pos(self, pos):
        """Return object_id of first object within CONTACT_RADIUS, or None."""
        for oid, opos in self.object_positions.items():
            if _dist3(pos, opos) <= CONTACT_RADIUS:
                return oid
        return None

    # ------------------------------------------------------------------
    # Transformation: HAZARD → KNOWLEDGE
    # ------------------------------------------------------------------

    def transform_to_knowledge(self, object_id):
        """Transform a HAZARD object to KNOWLEDGE in place.

        Called by the agent's check_competency_unlocks equivalent.
        The object_id and position are preserved. Only the type changes.
        This is the spatial internalisation event: the object persists
        at its coordinates in a transformed state.
        """
        if self.object_type.get(object_id) == HAZARD:
            self.object_type[object_id] = KNOWLEDGE
            # hazard_cells set stays the same (haz IDs remain in it
            # post-transformation, as in V13World where hazard_cells
            # was not pruned on transition).

    # ------------------------------------------------------------------
    # End-state activation (parallel to v0.14)
    # ------------------------------------------------------------------

    def activate_end_state(self):
        """Mark the end-state object as END_STATE type (if not already).

        In V13World, the end_state_cell was sampled at init and placed
        as END_STATE. Here it is placed at init already. This method
        exists for interface compatibility with any code that calls
        world.activate_end_state() or checks world.end_state_cell.
        """
        self.object_type[self.end_state_cell] = END_STATE

    # ------------------------------------------------------------------
    # Phase 1 waypoint interface (used by V17Agent path planning)
    # ------------------------------------------------------------------

    def get_next_waypoint(self):
        """Return the next Phase 1 waypoint and advance the index.

        Returns None when all waypoints have been visited.
        """
        if self._waypoint_idx >= len(self._waypoints):
            return None
        wp = self._waypoints[self._waypoint_idx]
        self._waypoint_idx += 1
        return wp

    def is_passable_for_path_planning(self, pos):
        """All positions within the world volume are passable.

        HAZARD objects impose cost but are passable (as in V13World).
        """
        x, y, z = pos
        return 0.0 <= x <= self.size and 0.0 <= y <= self.size and 0.0 <= z <= self.size

    # ------------------------------------------------------------------
    # Family property accessors
    # ------------------------------------------------------------------

    @property
    def object_colour(self):
        return OBJECT_COLOUR

    @property
    def object_form(self):
        return OBJECT_FORM
