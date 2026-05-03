"""
v1_2_schema.py
--------------
v1.2 schema observer. Reconstructed for v1.7 from the v1.3 schema
extension's interface requirements and the v1.2 paper's Table 1
cell-type property matrix.

Provides:
    V12Agent          — subclasses V014Agent, adds query_schema callable
    V12SchemaObserver — parallel observer; builds schema at init,
                        populates self._row at on_run_end
    SCHEMA_FIELDS     — ordered field list for schema CSV

The schema describes the architecture's structure: cell types, action
vocabulary, phase schedule, flag types. It is a property of the
architecture (fixed at run start), not of the run.

V12Agent adds query_schema(section) to the agent namespace. V13Agent
subclasses this and extends the cell_type_schema with COLOUR_CELL.

SCHEMA STRUCTURE (v1.2 paper §2.2)
  cell_types: {name: {code, passable, cost_on_entry,
                       feature_reward_eligible, attraction_bias_eligible,
                       gating_eligible, transformation_eligible}}
  actions:    {name: {code, description}}
  phases:     {name: {code, description, novelty_weight, progress_weight,
                       preference_weight, feature_weight}}
  flag_types: {name: {formation_condition, formation_threshold,
                       confirming_operationalisation,
                       disconfirming_semantics, applicable_cell_types}}

CELL TYPE PROPERTIES (Table 1 from v1.2 paper)
                        passable  cost  feat  attr  gate  transf
  FRAME                 False     N/A   False False False False
  NEUTRAL               True      0     False False False False
  HAZARD                True      >0    False False True  True
  ATTRACTOR             True      0     True  True  False False
  END_STATE             True      0     True  True  True  False
  KNOWLEDGE             True      0     True  True  False False
"""

import csv

from curiosity_agent_v0_14 import (
    DevelopmentalAgent as V014Agent,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE,
    PHASE_3_START_FRACTION, FEATURE_DRIVE_WEIGHT,
    FLAG_THRESHOLD, MASTERY_THRESHOLD, KNOWLEDGE_THRESHOLD,
)

# ---------------------------------------------------------------------------
# SCHEMA_FIELDS
# ---------------------------------------------------------------------------

# Run identification fields
_ID_FIELDS = ["arch", "hazard_cost", "num_steps", "run_idx", "seed"]

# Cell type fields: six properties × six types
_CELL_TYPES = ["FRAME", "NEUTRAL", "HAZARD", "ATTRACTOR", "END_STATE", "KNOWLEDGE"]
_CT_PROPS   = [
    "passable", "cost_on_entry",
    "feature_reward_eligible", "attraction_bias_eligible",
    "gating_eligible", "transformation_eligible",
]
_CT_FIELDS = [
    f"ct_{ct}_{prop}"
    for ct in _CELL_TYPES
    for prop in _CT_PROPS
]

# Action vocabulary fields (4 actions)
_ACTION_NAMES = ["UP", "DOWN", "LEFT", "RIGHT"]
_ACTION_PROPS = ["code", "description"]
_ACTION_FIELDS = [
    f"action_{act}_{prop}"
    for act in _ACTION_NAMES
    for prop in _ACTION_PROPS
]

# Phase schedule fields (3 phases)
_PHASE_NAMES = ["PHASE_1", "PHASE_2", "PHASE_3"]
_PHASE_PROPS = [
    "code", "description",
    "novelty_weight", "progress_weight",
    "preference_weight", "feature_weight",
]
_PHASE_FIELDS = [
    f"phase_{ph}_{prop}"
    for ph in _PHASE_NAMES
    for prop in _PHASE_PROPS
]

# Flag type fields (4 flag types)
_FLAG_TYPES = ["THREAT", "MASTERY", "KNOWLEDGE_BANKING", "END_STATE"]
_FLAG_PROPS = [
    "formation_condition", "formation_threshold",
    "confirming_operationalisation", "disconfirming_semantics",
    "applicable_cell_types",
]
_FLAG_FIELDS = [
    f"flag_{ft}_{prop}"
    for ft in _FLAG_TYPES
    for prop in _FLAG_PROPS
]

# Summary fields
_SUMMARY_FIELDS = ["schema_cell_types_count", "schema_complete"]

SCHEMA_FIELDS = (
    _ID_FIELDS
    + _CT_FIELDS
    + _ACTION_FIELDS
    + _PHASE_FIELDS
    + _FLAG_FIELDS
    + _SUMMARY_FIELDS
)


# ---------------------------------------------------------------------------
# Schema content (architecture-level constants)
# ---------------------------------------------------------------------------

def _build_cell_type_schema():
    return {
        "FRAME": {
            "code": FRAME,
            "passable": False,
            "cost_on_entry": None,
            "feature_reward_eligible": False,
            "attraction_bias_eligible": False,
            "gating_eligible": False,
            "transformation_eligible": False,
        },
        "NEUTRAL": {
            "code": NEUTRAL,
            "passable": True,
            "cost_on_entry": 0,
            "feature_reward_eligible": False,
            "attraction_bias_eligible": False,
            "gating_eligible": False,
            "transformation_eligible": False,
        },
        "HAZARD": {
            "code": HAZARD,
            "passable": True,
            "cost_on_entry": ">0",
            "feature_reward_eligible": False,
            "attraction_bias_eligible": False,
            "gating_eligible": True,
            "transformation_eligible": True,
        },
        "ATTRACTOR": {
            "code": ATTRACTOR,
            "passable": True,
            "cost_on_entry": 0,
            "feature_reward_eligible": True,
            "attraction_bias_eligible": True,
            "gating_eligible": False,
            "transformation_eligible": False,
        },
        "END_STATE": {
            "code": END_STATE,
            "passable": True,
            "cost_on_entry": 0,
            "feature_reward_eligible": True,
            "attraction_bias_eligible": True,
            "gating_eligible": True,
            "transformation_eligible": False,
        },
        "KNOWLEDGE": {
            "code": KNOWLEDGE,
            "passable": True,
            "cost_on_entry": 0,
            "feature_reward_eligible": True,
            "attraction_bias_eligible": True,
            "gating_eligible": False,
            "transformation_eligible": False,
        },
    }


def _build_action_schema():
    return {
        "UP":    {"code": 0, "description": "move up (y-1)"},
        "DOWN":  {"code": 1, "description": "move down (y+1)"},
        "LEFT":  {"code": 2, "description": "move left (x-1)"},
        "RIGHT": {"code": 3, "description": "move right (x+1)"},
    }


def _build_phase_schema():
    p3_start = PHASE_3_START_FRACTION
    return {
        "PHASE_1": {
            "code": 1,
            "description": "Prescribed boustrophedon path exploration",
            "novelty_weight":    0.0,
            "progress_weight":   0.0,
            "preference_weight": 0.0,
            "feature_weight":    0.0,
        },
        "PHASE_2": {
            "code": 2,
            "description": "Curiosity-driven exploration",
            "novelty_weight":    0.3,
            "progress_weight":   1.2,
            "preference_weight": 0.0,
            "feature_weight":    FEATURE_DRIVE_WEIGHT,
        },
        "PHASE_3": {
            "code": 3,
            "description": f"Preference-driven exploitation (from step {p3_start:.0%})",
            "novelty_weight":    0.3,
            "progress_weight":   0.3,
            "preference_weight": 0.5,
            "feature_weight":    FEATURE_DRIVE_WEIGHT,
        },
    }


def _build_flag_type_schema():
    return {
        "THREAT": {
            "formation_condition": (
                f"Three entries to a HAZARD cell (FLAG_THRESHOLD={FLAG_THRESHOLD}) "
                f"or first-entry signature match"
            ),
            "formation_threshold": FLAG_THRESHOLD,
            "confirming_operationalisation": (
                "Subsequent entries to the flagged cell without cost reduction"
            ),
            "disconfirming_semantics": (
                "Cell type transitions from HAZARD to KNOWLEDGE "
                "(v0.14 competency-gated transformation)"
            ),
            "applicable_cell_types": "HAZARD",
        },
        "MASTERY": {
            "formation_condition": (
                f"Three visits to an ATTRACTOR cell "
                f"(MASTERY_THRESHOLD={MASTERY_THRESHOLD})"
            ),
            "formation_threshold": MASTERY_THRESHOLD,
            "confirming_operationalisation": "Mastery flag set; feature reward depletes",
            "disconfirming_semantics": "None (mastery flag is permanent)",
            "applicable_cell_types": "ATTRACTOR",
        },
        "KNOWLEDGE_BANKING": {
            "formation_condition": (
                f"Three post-transition entries to a KNOWLEDGE cell "
                f"(KNOWLEDGE_THRESHOLD={KNOWLEDGE_THRESHOLD})"
            ),
            "formation_threshold": KNOWLEDGE_THRESHOLD,
            "confirming_operationalisation": (
                "Banking step reached; threat flag clears; preference resets"
            ),
            "disconfirming_semantics": "None (banking is permanent)",
            "applicable_cell_types": "KNOWLEDGE",
        },
        "END_STATE": {
            "formation_condition": (
                "All attractors mastered AND all hazards banked as knowledge "
                "(v0.14 amended trigger)"
            ),
            "formation_threshold": 1,
            "confirming_operationalisation": "First post-activation entry banks end-state",
            "disconfirming_semantics": "None (end-state activation is permanent)",
            "applicable_cell_types": "END_STATE",
        },
    }


# ---------------------------------------------------------------------------
# V12Agent
# ---------------------------------------------------------------------------

class V12Agent(V014Agent):
    """v1.2 agent. Extends V014Agent with schema construction.

    Adds query_schema(section) callable. No computational behaviour is
    modified. The schema is built at construction time from the world's
    structural properties and the architecture's constants.
    """

    def __init__(self, world, total_steps, num_actions=4):
        super().__init__(world, total_steps, num_actions=num_actions)
        self._schema = self._build_schema(world)

    def _build_schema(self, world):
        return {
            "cell_types":  _build_cell_type_schema(),
            "actions":     _build_action_schema(),
            "phases":      _build_phase_schema(),
            "flag_types":  _build_flag_type_schema(),
        }

    def query_schema(self, section):
        """Return a schema section dict.

        section: one of "cell_types", "actions", "phases", "flag_types"
        Returns a copy to prevent mutation.
        """
        import copy
        return copy.deepcopy(self._schema.get(section, {}))


# ---------------------------------------------------------------------------
# V12SchemaObserver
# ---------------------------------------------------------------------------

class V12SchemaObserver:
    """v1.2 parallel schema observer.

    Constructs the schema at __init__ time and populates self._row at
    on_run_end. The three hook methods (on_pre_action, on_post_event,
    on_run_end) follow the parallel-observer pattern.

    Attributes
    ----------
    _row : dict | None
        Flat dict of schema fields for this run. None until on_run_end.
    _meta : dict
        Run identification dict (arch, hazard_cost, num_steps, run_idx, seed).
    """

    EXPECTED_CELL_TYPES = {
        "FRAME", "NEUTRAL", "HAZARD", "ATTRACTOR", "END_STATE", "KNOWLEDGE",
    }
    EXPECTED_ACTIONS    = {"UP", "DOWN", "LEFT", "RIGHT"}
    EXPECTED_PHASES     = {"PHASE_1", "PHASE_2", "PHASE_3"}
    EXPECTED_FLAG_TYPES = {"THREAT", "MASTERY", "KNOWLEDGE_BANKING", "END_STATE"}

    def __init__(self, agent, world, run_metadata):
        self._agent = agent
        self._world = world
        self._meta  = run_metadata
        self._row   = None

    def on_pre_action(self, step):
        pass

    def on_post_event(self, step):
        pass

    def on_run_end(self, step):
        """Build the schema row from the agent's query_schema callable."""
        if not hasattr(self._agent, 'query_schema') or self._agent.query_schema is None:
            self._row = None
            return

        schema    = self._agent.query_schema
        ct_schema  = schema("cell_types")
        act_schema = schema("actions")
        ph_schema  = schema("phases")
        ft_schema  = schema("flag_types")

        row = {}

        # Run identification
        for f in _ID_FIELDS:
            row[f] = self._meta.get(f, "")

        # Cell types
        for ct_name in _CELL_TYPES:
            entry  = ct_schema.get(ct_name, {})
            prefix = f"ct_{ct_name}_"
            for prop in _CT_PROPS:
                row[prefix + prop] = entry.get(prop)

        # Actions
        for act_name in _ACTION_NAMES:
            entry  = act_schema.get(act_name, {})
            prefix = f"action_{act_name}_"
            for prop in _ACTION_PROPS:
                row[prefix + prop] = entry.get(prop)

        # Phases
        for ph_name in _PHASE_NAMES:
            entry  = ph_schema.get(ph_name, {})
            prefix = f"phase_{ph_name}_"
            for prop in _PHASE_PROPS:
                row[prefix + prop] = entry.get(prop)

        # Flag types
        for ft_name in _FLAG_TYPES:
            entry  = ft_schema.get(ft_name, {})
            prefix = f"flag_{ft_name}_"
            for prop in _FLAG_PROPS:
                row[prefix + prop] = entry.get(prop)

        # Summary
        actual_ct = set(ct_schema.keys())
        complete  = (
            actual_ct     == self.EXPECTED_CELL_TYPES
            and set(act_schema.keys()) == self.EXPECTED_ACTIONS
            and set(ph_schema.keys())  == self.EXPECTED_PHASES
            and set(ft_schema.keys())  == self.EXPECTED_FLAG_TYPES
        )
        row["schema_cell_types_count"] = len(actual_ct)
        row["schema_complete"]         = complete
        row["arch"]                    = self._meta.get("arch", "v1_2")

        self._row = row

    def summary_metrics(self):
        """Return summary fields for inclusion in run_data CSV."""
        if self._row is None:
            return {"schema_complete": False}
        return {
            "schema_cell_types_count": self._row.get("schema_cell_types_count"),
            "schema_complete":         self._row.get("schema_complete"),
        }

    def get_substrate(self):
        """Return schema row as flat dict, or None (v1.6 interface)."""
        if self._row is None:
            return None
        return dict(self._row)

    def write_schema_csv(self, path, append=False):
        """Write schema row to CSV."""
        if self._row is None:
            return

        def _file_has_rows(p):
            try:
                with open(p) as f:
                    lines = [l for l in f if l.strip()]
                return len(lines) > 1
            except FileNotFoundError:
                return False

        mode = "a" if append else "w"
        write_header = (not append) or (not _file_has_rows(path))
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMA_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow({k: self._row.get(k, "") for k in SCHEMA_FIELDS})

    def reset(self):
        self._row = None
