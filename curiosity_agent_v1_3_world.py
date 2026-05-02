"""
curiosity_agent_v1_3_world.py
------------------------------
v1.3 world extension. Adds COLOUR_CELL = 6 as the seventh cell type,
two family property dimensions (colour and form), and a V13World class
that extends the v0.14 StructuredGridWorld with family-attributed cells
and colour-cell placement.

The v0.14 agent (V014Agent) is used unchanged. No agent method is
modified. All behaviour is identical to v1.2 when the family properties
are ignored by the agent, which they are — the agent's drives, action
selection, and value functions operate on cell_type alone, and
COLOUR_CELL = 6 is perceived as a new passable cell type through the
existing perceive_adjacent machinery.

Family specification (pre-registration §2.1):
  GREEN family:
    Perceivable tier:  COLOUR_CELL at (7, 13), colour=GREEN, form=FLAT
    Acquirable tier:   ATTRACTOR at (4, 15),   colour=GREEN, form=SQUARE_2D
    Bankable tier:     HAZARD at (14, 14),      colour=GREEN, form=SPHERE_3D

  YELLOW family:
    Perceivable tier:  COLOUR_CELL at (13, 6),  colour=YELLOW, form=FLAT
    Acquirable tier:   ATTRACTOR at (16, 3),    colour=YELLOW, form=TRIANGLE_2D
    Bankable tier:     HAZARD at (5, 8),         colour=YELLOW, form=PYRAMID_3D

Unaffiliated cells carry colour=None, form=None.

COLOUR_CELL properties (pre-registration §2.2):
  - Passable: True
  - Feature-reward-bearing: False
  - Attraction-bias-bearing: False
  - Gating-eligible: False
  - Transformation-eligible: False
  - Perceivable from adjacent cells: True (via standard perceive_adjacent,
    which returns cell_type; colour and form readable via
    world.cell_colour and world.cell_form dicts)

Preservation guarantee: with --no-family suppressing the V13FamilyObserver,
and with V13World used instead of V12World, the agent's behaviour diverges
from v1.2 at matched seeds only in runs where COLOUR_CELL or family-
attributed cells affect trajectory through the novelty drive. This is
expected divergence (pre-registration §3). The level-4 regression test
(verify_v1_3_no_family.py) uses V12World, not V13World, to verify
byte-identical preservation in the --no-family configuration.
"""

from curiosity_agent_v0_14 import (
    GRID_SIZE, FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE,
    ATTRACTOR_CELLS, HAZARD_CLUSTERS,
    StructuredGridWorld,
)

# -------------------------------------------------------------------------
# New cell type constant
# -------------------------------------------------------------------------
COLOUR_CELL = 6   # seventh cell type; passable, perceivable, no reward

# -------------------------------------------------------------------------
# Family colour and form vocabularies
# -------------------------------------------------------------------------
# Colour values
GREEN  = "GREEN"
YELLOW = "YELLOW"

# Form values — tier descriptors
FLAT         = "FLAT"           # perceivable tier
SQUARE_2D    = "SQUARE_2D"      # acquirable tier, green family
TRIANGLE_2D  = "TRIANGLE_2D"    # acquirable tier, yellow family
SPHERE_3D    = "SPHERE_3D"      # bankable tier, green family
PYRAMID_3D   = "PYRAMID_3D"     # bankable tier, yellow family

# -------------------------------------------------------------------------
# Family layout — fixed coordinates (pre-registration §2.1 and §2.3)
# -------------------------------------------------------------------------
COLOUR_CELL_COORDS = {
    GREEN:  (7, 13),
    YELLOW: (13, 6),
}

FAMILY_ATTRACTOR_COORDS = {
    GREEN:  (4, 15),   # square 2D; member of ATTRACTOR_CELLS
    YELLOW: (16, 3),   # triangle 2D; member of ATTRACTOR_CELLS
}

FAMILY_HAZARD_COORDS = {
    GREEN:  (14, 14),  # sphere 3D; member of HAZARD_CLUSTERS cluster 2
    YELLOW: (5, 8),    # pyramid 3D; member of HAZARD_CLUSTERS cluster 1
}

# Convenience: full family membership by coord
FAMILY_COLOUR_BY_COORD = {}
FAMILY_FORM_BY_COORD   = {}

for _colour, _coord in COLOUR_CELL_COORDS.items():
    FAMILY_COLOUR_BY_COORD[_coord] = _colour
    FAMILY_FORM_BY_COORD[_coord]   = FLAT

FAMILY_COLOUR_BY_COORD[(4, 15)]  = GREEN
FAMILY_FORM_BY_COORD[(4, 15)]    = SQUARE_2D
FAMILY_COLOUR_BY_COORD[(16, 3)]  = YELLOW
FAMILY_FORM_BY_COORD[(16, 3)]    = TRIANGLE_2D
FAMILY_COLOUR_BY_COORD[(14, 14)] = GREEN
FAMILY_FORM_BY_COORD[(14, 14)]   = SPHERE_3D
FAMILY_COLOUR_BY_COORD[(5, 8)]   = YELLOW
FAMILY_FORM_BY_COORD[(5, 8)]     = PYRAMID_3D

# Cross-family lookup: given a bankable coord, which acquirable coord
# is its family precondition?
FAMILY_PRECONDITION = {
    (14, 14): (4, 15),   # green sphere ← green square
    (5, 8):   (16, 3),   # yellow pyramid ← yellow triangle
}


# -------------------------------------------------------------------------
# V13World
# -------------------------------------------------------------------------
class V13World(StructuredGridWorld):
    """v1.3 world.

    Extends v0.14's StructuredGridWorld with:
      - COLOUR_CELL type at two fixed coordinates.
      - cell_colour and cell_form dicts holding family properties for
        all cells (None for unaffiliated cells).

    The agent's perceive_adjacent returns COLOUR_CELL (= 6) for adjacent
    colour cells, which the agent's novelty drive treats as an unvisited
    cell type on first encounter, driving Phase 2 exploration toward it.
    No feature reward, no attraction bias; the novelty signal is the
    only pull.

    The step function handles COLOUR_CELL as passable at zero cost,
    identical to NEUTRAL, ATTRACTOR, and END_STATE.
    """

    def __init__(self, hazard_cost, size=GRID_SIZE):
        super().__init__(size=size, permutation_offset=0)
        self.hazard_cost = hazard_cost
        self._place_colour_cells()
        self._assign_family_properties()

    def _place_colour_cells(self):
        """Place COLOUR_CELL types at the two fixed coordinates.

        Both coordinates are passable neutral cells in the v0.14
        environment (confirmed against the 20x20 grid layout).
        Asserts they were NEUTRAL before placement.
        """
        for colour, coord in COLOUR_CELL_COORDS.items():
            existing = self.cell_type.get(coord, FRAME)
            assert existing == NEUTRAL, (
                f"Colour cell coordinate {coord} ({colour}) is not NEUTRAL "
                f"in v0.14 world — found type {existing}. "
                f"Pre-registration §2.3 requires passable neutral coordinates."
            )
            self.cell_type[coord] = COLOUR_CELL

    def _assign_family_properties(self):
        """Populate cell_colour and cell_form dicts for all cells.

        All cells receive an entry; unaffiliated cells carry None.
        Family-attributed cells carry their colour and form values.

        Also populates family_precondition_attractor: for each family
        hazard cell, the coord of the attractor that must be mastered
        before that hazard can transition to KNOWLEDGE (v1.3.2 rule).
        Unaffiliated hazard cells are not in this dict; they use the
        global competency gate unchanged.
        """
        all_cells = list(self.cell_type.keys())
        self.cell_colour = {c: None for c in all_cells}
        self.cell_form   = {c: None for c in all_cells}
        for coord, colour in FAMILY_COLOUR_BY_COORD.items():
            if coord in self.cell_colour:
                self.cell_colour[coord] = colour
                self.cell_form[coord]   = FAMILY_FORM_BY_COORD[coord]

        # Family-specific competency gate (v1.3.2 amendment).
        # Maps each family hazard coord to its precondition attractor coord.
        # The global threshold slot is preserved in hazard_competency_thresholds
        # but is not consulted for these cells during check_competency_unlocks.
        self.family_precondition_attractor = dict(FAMILY_PRECONDITION)

    def step(self, action):
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
            return self.observe(), target, True, self.hazard_cost
        # NEUTRAL, ATTRACTOR, END_STATE, KNOWLEDGE, COLOUR_CELL:
        # all passable at zero cost.
        self.agent_pos = target
        return self.observe(), target, True, 0.0
