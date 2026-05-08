"""
v1_13_world.py
--------------
V113World: parameterised world constructor for v1.13 and the
developmental arc through v1.16.

ARCHITECTURE PRINCIPLE
V17World is frozen as the regression baseline. V113World replaces it
as the active world class from v1.13 onwards. Its constructor accepts
a family definition list, environment-specific object layout, an
end_state presence flag, and an optional unreachable_hazards list.
This accommodates:

    v1.13  — BLUE family added; haz_blue in ENV1, att_blue in ENV2;
              object positions differ across environments
    v1.14  — six colour families; 2D/3D object classes; multiple
              environments; return-to-environment architecture
    v1.15  — two-agent shared environment
    v1.16  — no end_state; one unreachable hazard; shape as second
              connector axis

REGRESSION CONTRACT
V113World instantiated with the v1.12-equivalent family definition
and has_end_state=True produces byte-identical object populations
to V17World at matched seeds (same positions, same types, same
family_precondition_attractor, same competency thresholds).
Verified by Level-14 pre-flight criterion.

FAMILY DEFINITION FORMAT
Each family is a dict:

    {
        "colour":      str,           # e.g. "BLUE"
        "dist_id":     str | None,    # distractor object id, or None
        "dist_pos":    (x, y, z) | None,
        "att_id":      str,           # attractor object id
        "att_pos":     (x, y, z),
        "att_form":    str,           # e.g. CIRCLE_2D
        "haz_id":      str | None,    # hazard object id, or None
                                      # None when hazard is in another env
        "haz_pos":     (x, y, z) | None,
        "haz_form":    str | None,
    }

haz_id=None: the family hazard exists in another environment. No
HAZARD object for this family is placed in this world instance.
att_id is always present; the attractor is the directed search target.

INTERFACE CONTRACT (identical to V17World)
    world.agent_pos
    world.object_type
    world.cell_type
    world.attractor_cells
    world.hazard_cells
    world.scope_cells
    world.end_state_cell          (None if has_end_state=False)
    world.hazard_cost
    world.hazard_competency_thresholds
    world.family_precondition_attractor
    world.object_colour           (property)
    world.object_form             (property)
    world.perceive_within_radius(pos, r)
    world.perceive_adjacent(pos)
    world.step(action)
    world.observe()
    world.transform_to_knowledge(object_id)
    world.activate_end_state()
    world.get_next_waypoint()
    world.is_passable_for_path_planning(pos)

PREDICTED RECORD WAYPOINT INJECTION
    world.inject_waypoint(pos)    — insert a position at the front of
                                    the remaining waypoint queue. Used
                                    by the batch runner to add haz_blue
                                    as a mandatory Phase 1 target before
                                    transfer, and att_blue as the directed
                                    search target in Environment 2.
"""

import math
import numpy as np
from collections import defaultdict
from curiosity_agent_v1_7_world import V17World as _V17WorldBase

# ---------------------------------------------------------------------------
# Re-export object type constants (identical values to V17World)
# ---------------------------------------------------------------------------
FRAME     = 0
NEUTRAL   = 1
HAZARD    = 2
ATTRACTOR = 3
END_STATE = 4
KNOWLEDGE = 5
DIST_OBJ  = 6

# ---------------------------------------------------------------------------
# Form vocabulary (extended for BLUE family and future families)
# ---------------------------------------------------------------------------
FLAT         = "FLAT"
SQUARE_2D    = "SQUARE_2D"
TRIANGLE_2D  = "TRIANGLE_2D"
CIRCLE_2D    = "CIRCLE_2D"     # att_blue form
SPHERE_3D    = "SPHERE_3D"     # haz_blue form
PYRAMID_3D   = "PYRAMID_3D"
CUBE_3D      = "CUBE_3D"       # reserved for future families

# ---------------------------------------------------------------------------
# Colour vocabulary
# ---------------------------------------------------------------------------
GREEN  = "GREEN"
YELLOW = "YELLOW"
BLUE   = "BLUE"
# Reserved for v1.14+:
RED    = "RED"
ORANGE = "ORANGE"
PURPLE = "PURPLE"

# ---------------------------------------------------------------------------
# World geometry (inherited from V17World; not parameterised)
# ---------------------------------------------------------------------------
WORLD_SIZE        = 12.0
STEP_SIZE         = 1.0
PERCEPTION_RADIUS = 3.0
CONTACT_RADIUS    = 0.8
WAYPOINT_SPACING  = 2.5
START_POS         = (1.0, 1.0, 1.0)
NUM_ACTIONS       = 27

# Pre-computed direction vectors (identical to V17World)
_DIRECTION_VECTORS = []
for _dz in (-1, 0, 1):
    for _dy in (-1, 0, 1):
        for _dx in (-1, 0, 1):
            if _dx == 0 and _dy == 0 and _dz == 0:
                continue
            _DIRECTION_VECTORS.append((_dx, _dy, _dz))

# ---------------------------------------------------------------------------
# V1.13 Environment definitions
# ---------------------------------------------------------------------------

# Environment 1: GREEN + YELLOW families (complete) + haz_blue (BLUE hazard
# only — att_blue is absent; agent will encounter haz_blue, pay cost, and
# transfer to Environment 2 carrying the predicted schema record).
# Positions are the V17World originals for GREEN and YELLOW to satisfy the
# regression contract. haz_blue placed at a distinct position.

ENV1_FAMILIES = [
    {
        "colour":   GREEN,
        "dist_id":  "dist_green",
        "dist_pos": (3.0, 9.0, 3.0),
        "att_id":   "att_green",
        "att_pos":  (2.0, 11.0, 2.0),
        "att_form": SQUARE_2D,
        "haz_id":   "haz_green",
        "haz_pos":  (9.0, 10.0, 8.0),
        "haz_form": SPHERE_3D,
    },
    {
        "colour":   YELLOW,
        "dist_id":  "dist_yellow",
        "dist_pos": (8.0, 3.0, 3.0),
        "att_id":   "att_yellow",
        "att_pos":  (10.0, 2.0, 2.0),
        "att_form": TRIANGLE_2D,
        "haz_id":   "haz_yellow",
        "haz_pos":  (3.0, 5.0, 7.0),
        "haz_form": PYRAMID_3D,
    },
    {
        "colour":   BLUE,
        "dist_id":  None,              # no distractor for BLUE at v1.13
        "dist_pos": None,
        "att_id":   None,              # att_blue is absent from ENV1
        "att_pos":  None,
        "att_form": None,
        "haz_id":   "haz_blue",
        "haz_pos":  (7.0, 8.0, 3.0),  # distinct from GREEN/YELLOW objects
        "haz_form": SPHERE_3D,
    },
]

# Environment 2: GREEN + YELLOW (new positions — repeat-pattern interference
# control) + att_blue (BLUE attractor only — haz_blue is in ENV1).
# Positions are deliberately different from ENV1 to ensure any behavioural
# regularity survives the position change (schema-level, not spatial memory).

ENV2_FAMILIES = [
    {
        "colour":   GREEN,
        "dist_id":  "dist_green",
        "dist_pos": (9.0, 3.0, 9.0),   # ENV2 position — differs from ENV1
        "att_id":   "att_green",
        "att_pos":  (10.0, 2.0, 10.0), # ENV2 position
        "att_form": SQUARE_2D,
        "haz_id":   "haz_green",
        "haz_pos":  (2.0, 9.0, 4.0),   # ENV2 position
        "haz_form": SPHERE_3D,
    },
    {
        "colour":   YELLOW,
        "dist_id":  "dist_yellow",
        "dist_pos": (3.0, 10.0, 9.0),  # ENV2 position
        "att_id":   "att_yellow",
        "att_pos":  (2.0, 11.0, 8.0),  # ENV2 position
        "att_form": TRIANGLE_2D,
        "haz_id":   "haz_yellow",
        "haz_pos":  (9.0, 4.0, 5.0),   # ENV2 position
        "haz_form": PYRAMID_3D,
    },
    {
        "colour":   BLUE,
        "dist_id":  None,
        "dist_pos": None,
        "att_id":   "att_blue",
        "att_pos":  (5.0, 6.0, 10.0),  # att_blue: directed search target
        "att_form": CIRCLE_2D,
        "haz_id":   None,              # haz_blue is in ENV1
        "haz_pos":  None,
        "haz_form": None,
    },
]

# Unaffiliated objects: identical across both environments for v1.13.
# Positions inherited from V17World for regression contract.
UNAFFILIATED_POSITIONS = {
    "att_free_0": (5.0,  2.0, 5.0),
    "att_free_1": (9.0,  5.0, 2.0),
    "att_free_2": (6.0,  8.0, 1.0),
    "att_free_3": (11.0, 9.0, 5.0),
    "haz_unaff_0": (5.0,  6.0, 9.0),
    "haz_unaff_1": (6.0,  5.0, 10.0),
    "haz_unaff_2": (10.0, 7.0, 4.0),
}

UNAFFILIATED_BASE_TYPES = {
    "att_free_0":  ATTRACTOR,
    "att_free_1":  ATTRACTOR,
    "att_free_2":  ATTRACTOR,
    "att_free_3":  ATTRACTOR,
    "haz_unaff_0": HAZARD,
    "haz_unaff_1": HAZARD,
    "haz_unaff_2": HAZARD,
}

END_STATE_CANDIDATES = ["att_free_0", "att_free_1", "att_free_2", "att_free_3"]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _dist3(a, b):
    return math.sqrt(
        (a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2
    )

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

def _build_waypoints_from_positions(object_positions, size=WORLD_SIZE):
    """Build a space-filling waypoint sequence from instance object positions.

    Mirrors V17World._build_phase1_waypoints() but operates on the
    instance's object_positions dict rather than the module-level constant.
    Required because V113World's object layout is determined at instantiation,
    not at module load.
    """
    spacing = WAYPOINT_SPACING
    coords = []
    z = 1.0
    while z <= size - 1.0:
        y = 1.0
        while y <= size - 1.0:
            x = 1.0
            while x <= size - 1.0:
                coords.append((x, y, z))
                x += spacing
            y += spacing
        z += spacing

    waypoints = list(coords)

    for pos in object_positions.values():
        if all(_dist3(pos, w) > spacing * 0.5 for w in waypoints):
            waypoints.append(pos)

    return waypoints


# ---------------------------------------------------------------------------
# V113World
# ---------------------------------------------------------------------------

class V113World(_V17WorldBase):
    """Parameterised world constructor for v1.13 and the arc to v1.16.

    Parameters
    ----------
    families : list of dict
        Family definition list (see module docstring for format).
    hazard_cost : float
        Cost paid on HAZARD contact.
    has_end_state : bool
        If True, an end_state object is sampled from unaffiliated
        attractor candidates (seeded). If False, no end_state object
        is placed — v1.16 condition.
    unreachable_hazards : list of str, optional
        Object IDs of hazards that are structurally inaccessible (v1.16).
        These are placed in the world but flagged as unreachable in a
        separate attribute. The cognitive layer reads
        world.unreachable_hazard_ids to identify them.
    size : float
        World volume edge length.
    seed : int or None
        RNG seed for end_state sampling and competency threshold
        assignment.

    Notes
    -----
    The predicted-record waypoint injection method (inject_waypoint) is
    provided for the batch runner to add mandatory Phase 1 targets
    (haz_blue in ENV1, att_blue in ENV2) without modifying the world's
    internal waypoint list at construction time.
    """

    def __init__(
        self,
        families,
        hazard_cost,
        has_end_state   = True,
        unreachable_hazards = None,
        size            = WORLD_SIZE,
        seed            = None,
    ):
        self.hazard_cost = hazard_cost
        self.size        = size
        self._rng        = np.random.default_rng(seed)
        self.has_end_state = has_end_state
        self.unreachable_hazard_ids = frozenset(unreachable_hazards or [])

        # ------------------------------------------------------------------
        # Build object layout from family definitions
        # ------------------------------------------------------------------
        self.object_positions = {}
        self._object_colour   = {}
        self._object_form     = {}
        object_base_type      = {}
        self.family_precondition_attractor = {}
        unaffiliated_hazard_ids = set()

        for fam in families:
            colour = fam["colour"]

            # Distractor
            if fam.get("dist_id") and fam.get("dist_pos"):
                oid = fam["dist_id"]
                self.object_positions[oid] = fam["dist_pos"]
                object_base_type[oid]      = DIST_OBJ
                self._object_colour[oid]   = colour
                self._object_form[oid]     = FLAT

            # Attractor
            if fam.get("att_id") and fam.get("att_pos"):
                oid = fam["att_id"]
                self.object_positions[oid] = fam["att_pos"]
                object_base_type[oid]      = ATTRACTOR
                self._object_colour[oid]   = colour
                self._object_form[oid]     = fam["att_form"]

            # Hazard
            if fam.get("haz_id") and fam.get("haz_pos"):
                oid = fam["haz_id"]
                self.object_positions[oid] = fam["haz_pos"]
                object_base_type[oid]      = HAZARD
                self._object_colour[oid]   = colour
                self._object_form[oid]     = fam["haz_form"]

                # Family precondition: only when both att and haz present
                if fam.get("att_id"):
                    self.family_precondition_attractor[oid] = fam["att_id"]

        # Unaffiliated objects
        for oid, pos in UNAFFILIATED_POSITIONS.items():
            self.object_positions[oid] = pos
            object_base_type[oid]      = UNAFFILIATED_BASE_TYPES[oid]
            if UNAFFILIATED_BASE_TYPES[oid] == HAZARD:
                unaffiliated_hazard_ids.add(oid)

        self._unaffiliated_hazard_ids = frozenset(unaffiliated_hazard_ids)

        # ------------------------------------------------------------------
        # Agent position
        # ------------------------------------------------------------------
        self.agent_pos = START_POS

        # ------------------------------------------------------------------
        # Object type dict (live; mutated by transform_to_knowledge)
        # ------------------------------------------------------------------
        self.object_type = dict(object_base_type)

        # ------------------------------------------------------------------
        # End state
        # ------------------------------------------------------------------
        self.end_state_cell = None
        if self.has_end_state:
            self._sample_end_state()

        # ------------------------------------------------------------------
        # Hazard competency thresholds
        # ------------------------------------------------------------------
        self._assign_hazard_competency_thresholds()

        # ------------------------------------------------------------------
        # cell_type alias (observer compatibility)
        # ------------------------------------------------------------------
        self.cell_type = self.object_type

        # ------------------------------------------------------------------
        # Convenience sets
        # ------------------------------------------------------------------
        self.attractor_cells = {
            oid for oid, t in self.object_type.items() if t == ATTRACTOR
        }
        # v1.13.5: unreachable hazards (e.g. haz_blue in ENV1) are excluded
        # from hazard_cells. They exist in the world and can be encountered,
        # but cannot be banked — their precondition attractor is absent.
        # Including them makes all_hazards_banked permanently False, blocking
        # the end_state gate. Excluding them restores v1.12-equivalent
        # gate behaviour: complete all bankable hazards, end_state fires.
        self.hazard_cells = {
            oid for oid, t in self.object_type.items()
            if t in (HAZARD, KNOWLEDGE)
            and oid not in self.unreachable_hazard_ids
        }
        self.scope_cells = set(self.object_type.keys())

        # ------------------------------------------------------------------
        # Phase 1 waypoints (built from instance positions)
        # ------------------------------------------------------------------
        self._waypoints    = _build_waypoints_from_positions(
            self.object_positions, self.size
        )
        self._waypoint_idx = 0

        # Per-object contact tracking
        self._contact_counts = defaultdict(int)

        # knowledge_unlocked: tracks whether each hazard has been
        # transitioned to KNOWLEDGE. Keyed by object_id (strings).
        # Required by agent's check_competency_unlocks() contract.
        # v1.13.7: exclude unreachable hazards from knowledge_unlocked.
        # The V110Agent's activation gate checks knowledge_unlocked to determine
        # all_hazards_banked. haz_blue (HAZARD type in object_type) was being
        # included here despite being excluded from hazard_cells, producing a
        # 6-key dict against a 5-entry completion count — permanently False.
        # Excluding unreachable_hazard_ids from knowledge_unlocked aligns the
        # gate with the Montessori completion principle: unreachable hazards are
        # structural facts, not completion requirements.
        self.knowledge_unlocked = {
            oid: False
            for oid, t in self.object_type.items()
            if t in (HAZARD, KNOWLEDGE)
            and oid not in self.unreachable_hazard_ids
        }

    # ------------------------------------------------------------------
    # Seeded initialisation
    # ------------------------------------------------------------------

    def _sample_end_state(self):
        """Sample end-state object from unaffiliated attractor candidates."""
        candidates = [
            oid for oid in END_STATE_CANDIDATES
            if oid in self.object_type
        ]
        if not candidates:
            raise ValueError(
                "V113World: has_end_state=True but no END_STATE_CANDIDATES "
                "found in object layout."
            )
        idx = int(self._rng.integers(0, len(candidates)))
        self.end_state_cell = candidates[idx]
        self.object_type[self.end_state_cell] = END_STATE

    def _assign_hazard_competency_thresholds(self):
        """Assign competency thresholds to unaffiliated hazards (seeded).

        Family hazards use family_precondition_attractor gating.
        Unreachable hazards receive threshold 99 (never met by threshold).
        """
        unaff = sorted(self._unaffiliated_hazard_ids)
        thresholds = list(range(1, len(unaff) + 1))
        if thresholds:
            perm = self._rng.permutation(len(thresholds))
        else:
            perm = []
        self.hazard_competency_thresholds = {}
        for i, oid in enumerate(unaff):
            self.hazard_competency_thresholds[oid] = int(thresholds[perm[i]])

        # Family hazards: threshold slot preserved but not consulted
        for fam_haz in self.family_precondition_attractor:
            self.hazard_competency_thresholds[fam_haz] = 99

        # Unreachable hazards
        for oid in self.unreachable_hazard_ids:
            self.hazard_competency_thresholds[oid] = 99

    # ------------------------------------------------------------------
    # Waypoint injection (predicted-record directed search)
    # ------------------------------------------------------------------

    def inject_waypoint(self, pos):
        """Insert a position at the front of the remaining waypoint queue.

        Used by the batch runner to:
          ENV1: inject haz_blue position as a mandatory Phase 1 target,
                ensuring the agent approaches haz_blue before transfer.
          ENV2: inject att_blue position as the directed search target
                after the predicted schema record is written.

        The injection inserts ahead of the current waypoint index so that
        the injected position is visited before any remaining scheduled
        waypoints.
        """
        self._waypoints.insert(self._waypoint_idx, pos)

    # ------------------------------------------------------------------
    # Perception
    # ------------------------------------------------------------------

    def perceive_within_radius(self, pos, radius):
        """Return list of (object_type, object_id) within radius of pos."""
        results = []
        for oid, opos in self.object_positions.items():
            if _dist3(pos, opos) <= radius:
                results.append((self.object_type[oid], oid))
        return results

    def perceive_adjacent(self, pos_or_cell):
        """Compatibility alias (identical to V17World)."""
        if isinstance(pos_or_cell, tuple) and len(pos_or_cell) == 3:
            pos = pos_or_cell
        else:
            pos = self.agent_pos
        nearby = self.perceive_within_radius(pos, PERCEPTION_RADIUS)
        types  = tuple(t for t, _ in nearby)
        padded = (types + (NEUTRAL,) * 26)[:26]
        return padded

    def perceive_adjacent_with_coords(self, pos_or_cell):
        """Return (object_type, object_id) pairs for objects within
        PERCEPTION_RADIUS of pos.

        Satisfies the V13FamilyObserver.on_pre_action() contract that
        expects (cell_type, coord) pairs — in the v1.7+ substrate,
        object_id serves as the 'coord' key. This is the substrate-
        interface migration from coordinate-keyed to object_id-keyed
        access established at v1.7.

        Identical to perceive_within_radius() in return format; provided
        as a named alias so that any observer or substrate patch that
        calls world.perceive_adjacent_with_coords() works without
        modification.
        """
        if isinstance(pos_or_cell, tuple) and len(pos_or_cell) == 3:
            pos = pos_or_cell
        else:
            pos = self.agent_pos
        return self.perceive_within_radius(pos, PERCEPTION_RADIUS)

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------

    def observe(self):
        """Return state observation tuple (identical format to V17World)."""
        x, y, z      = self.agent_pos
        contact_type = NEUTRAL
        for oid, opos in self.object_positions.items():
            if _dist3(self.agent_pos, opos) <= CONTACT_RADIUS:
                contact_type = self.object_type[oid]
                break
        adj = self.perceive_adjacent(self.agent_pos)
        return (x, y, z, contact_type, *adj)

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self, action):
        """Apply action and return (obs, contact_id, moved, cost)."""
        if action == 26:
            return (
                self.observe(),
                self._contact_at_pos(self.agent_pos),
                False,
                0.0,
            )

        if 0 <= action < 26:
            dx, dy, dz = _DIRECTION_VECTORS[action]
        else:
            dx, dy, dz = 0, 0, 0

        x, y, z = self.agent_pos
        nx = _clamp(x + dx * STEP_SIZE, 0.0, self.size)
        ny = _clamp(y + dy * STEP_SIZE, 0.0, self.size)
        nz = _clamp(z + dz * STEP_SIZE, 0.0, self.size)

        moved          = (nx, ny, nz) != (x, y, z)
        self.agent_pos = (nx, ny, nz)

        contact_id = self._contact_at_pos(self.agent_pos)
        if contact_id is not None:
            self._contact_counts[contact_id] += 1

        cost = 0.0
        if contact_id is not None and self.object_type[contact_id] == HAZARD:
            cost = self.hazard_cost

        return self.observe(), contact_id, moved, cost

    def _contact_at_pos(self, pos):
        """Return object_id of first object within CONTACT_RADIUS, or None."""
        for oid, opos in self.object_positions.items():
            if _dist3(pos, opos) <= CONTACT_RADIUS:
                return oid
        return None

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def transform_to_knowledge(self, object_id):
        """Transform a HAZARD object to KNOWLEDGE in place.
        Internal alias; agent-facing contract uses transition_hazard_to_knowledge().
        """
        if self.object_type.get(object_id) == HAZARD:
            self.object_type[object_id] = KNOWLEDGE
            self.knowledge_unlocked[object_id] = True

    def transition_hazard_to_knowledge(self, cell):
        """Agent-facing contract method (v0.14 / v1.3 interface).

        Called by the agent check_competency_unlocks() when competency
        threshold is met. Idempotent: repeated calls after the first
        have no effect.
        """
        if self.knowledge_unlocked.get(cell, False):
            return
        if cell not in self.hazard_cells:
            return
        self.object_type[cell]        = KNOWLEDGE
        self.knowledge_unlocked[cell] = True

    # ------------------------------------------------------------------
    # End-state activation
    # ------------------------------------------------------------------

    def activate_end_state(self):
        """Mark end_state_cell as END_STATE type (interface compatibility)."""
        if self.end_state_cell is not None:
            self.object_type[self.end_state_cell] = END_STATE

    # ------------------------------------------------------------------
    # Phase 1 waypoint interface
    # ------------------------------------------------------------------

    def get_next_waypoint(self):
        """Return next Phase 1 waypoint and advance index. None when done."""
        if self._waypoint_idx >= len(self._waypoints):
            return None
        wp = self._waypoints[self._waypoint_idx]
        self._waypoint_idx += 1
        return wp

    def is_passable_for_path_planning(self, pos):
        """All positions within the world volume are passable."""
        x, y, z = pos
        return (
            0.0 <= x <= self.size
            and 0.0 <= y <= self.size
            and 0.0 <= z <= self.size
        )

    # ------------------------------------------------------------------
    # Family property accessors (instance-level, not module-level)
    # ------------------------------------------------------------------

    @property
    def object_colour(self):
        return dict(self._object_colour)

    @property
    def object_form(self):
        return dict(self._object_form)
