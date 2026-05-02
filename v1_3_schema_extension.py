"""
v1_3_schema_extension.py
-------------------------
v1.3 schema extension. Subclasses V12Agent and V12SchemaObserver to add
COLOUR_CELL as the seventh cell type in the architecture's schema.

The v1.2 schema observer hardcodes six cell types in both _build_schema()
and EXPECTED_CELL_TYPES. v1.3 introduces COLOUR_CELL = 6, which the v1.2
schema observer does not know about. This module provides thin subclasses
that extend the schema without modifying v1_2_schema.py.

V13Agent
--------
Subclasses V12Agent. Overrides _build_schema() to call the parent
implementation and then add COLOUR_CELL to the cell_type_schema. No
other method is overridden. Behaviour is identical to V12Agent.

V13SchemaObserver
-----------------
Subclasses V12SchemaObserver. Extends EXPECTED_CELL_TYPES to include
COLOUR_CELL, extends SCHEMA_FIELDS to include the seven COLOUR_CELL
property columns, and overrides on_run_end() to serialise COLOUR_CELL
alongside the six inherited types.

COLOUR_CELL properties (pre-registration §2.2):
    passable:                  True
    cost_on_entry:             None
    feature_reward_eligible:   False
    attraction_bias_eligible:  False
    gating_eligible:           False
    transformation_eligible:   False

schema_cell_types_count will be 7 in all runs where V13Agent is used.
schema_complete will be True when all seven types are present and correct.
"""

import copy

from v1_2_schema import V12Agent, V12SchemaObserver, SCHEMA_FIELDS


# ---------------------------------------------------------------------------
# Extended SCHEMA_FIELDS — adds COLOUR_CELL columns after KNOWLEDGE columns.
# ---------------------------------------------------------------------------

# Find insertion point: after the last KNOWLEDGE field, before action fields.
_KNOWLEDGE_LAST = "ct_KNOWLEDGE_transformation_eligible"
_INSERT_AFTER    = SCHEMA_FIELDS.index(_KNOWLEDGE_LAST)

COLOUR_CELL_SCHEMA_FIELDS = [
    "ct_COLOUR_CELL_passable",
    "ct_COLOUR_CELL_cost_on_entry",
    "ct_COLOUR_CELL_feature_reward_eligible",
    "ct_COLOUR_CELL_attraction_bias_eligible",
    "ct_COLOUR_CELL_gating_eligible",
    "ct_COLOUR_CELL_transformation_eligible",
]

# Build extended field list: insert COLOUR_CELL columns immediately after
# KNOWLEDGE columns, preserving all other field positions.
SCHEMA_FIELDS_V13 = (
    SCHEMA_FIELDS[: _INSERT_AFTER + 1]
    + COLOUR_CELL_SCHEMA_FIELDS
    + SCHEMA_FIELDS[_INSERT_AFTER + 1 :]
)


# ---------------------------------------------------------------------------
# V13Agent
# ---------------------------------------------------------------------------

class V13Agent(V12Agent):
    """v1.3 agent. Extends V12Agent schema with COLOUR_CELL entry.

    No behavioural method is overridden. The only change is the addition
    of COLOUR_CELL to the cell_type_schema returned by _build_schema().
    """

    def _build_schema(self, world):
        schema = super()._build_schema(world)
        schema["cell_types"]["COLOUR_CELL"] = {
            "code": 6,
            "passable": True,
            "cost_on_entry": None,
            "feature_reward_eligible": False,
            "attraction_bias_eligible": False,
            "gating_eligible": False,
            "transformation_eligible": False,
        }
        return schema


# ---------------------------------------------------------------------------
# V13SchemaObserver
# ---------------------------------------------------------------------------

class V13SchemaObserver(V12SchemaObserver):
    """v1.3 schema observer. Extends V12SchemaObserver with COLOUR_CELL.

    Overrides:
        EXPECTED_CELL_TYPES — adds "COLOUR_CELL"
        on_run_end()        — serialises COLOUR_CELL columns and writes
                              arch as "v1_3"

    All other methods (summary_metrics, write_schema_csv, reset) are
    inherited unchanged. write_schema_csv uses SCHEMA_FIELDS_V13 rather
    than SCHEMA_FIELDS.
    """

    EXPECTED_CELL_TYPES = {
        "FRAME", "NEUTRAL", "HAZARD", "ATTRACTOR",
        "END_STATE", "KNOWLEDGE", "COLOUR_CELL",
    }

    def on_run_end(self, step):
        """Serialise the v1.3 agent's schema including COLOUR_CELL."""
        # Call parent to build the base row (six cell types, all other
        # sections). Parent writes arch as "v1_2"; we update it below.
        super().on_run_end(step)

        if self._row is None:
            return

        # Update arch tag.
        self._row["arch"] = self._meta.get("arch", "v1_3")

        # Serialise COLOUR_CELL.
        schema   = self._agent.query_schema
        ct_schema = schema("cell_types")
        entry    = ct_schema.get("COLOUR_CELL", {})
        prefix   = "ct_COLOUR_CELL_"

        self._row[prefix + "passable"]                = entry.get("passable")
        self._row[prefix + "cost_on_entry"]           = entry.get("cost_on_entry")
        self._row[prefix + "feature_reward_eligible"] = entry.get(
            "feature_reward_eligible"
        )
        self._row[prefix + "attraction_bias_eligible"] = entry.get(
            "attraction_bias_eligible"
        )
        self._row[prefix + "gating_eligible"]         = entry.get("gating_eligible")
        self._row[prefix + "transformation_eligible"] = entry.get(
            "transformation_eligible"
        )

        # Recompute schema_cell_types_count and schema_complete with
        # the extended expected set.
        actual_ct  = set(ct_schema.keys())
        act_schema = schema("actions")
        ph_schema  = schema("phases")
        ft_schema  = schema("flag_types")

        self._row["schema_cell_types_count"] = len(actual_ct)

        complete = (
            actual_ct  == self.EXPECTED_CELL_TYPES
            and set(act_schema.keys()) == self.EXPECTED_ACTIONS
            and set(ph_schema.keys())  == self.EXPECTED_PHASES
            and set(ft_schema.keys())  == self.EXPECTED_FLAG_TYPES
        )
        self._row["schema_complete"] = complete

    def write_schema_csv(self, path, append=False):
        """Write schema row using extended v1.3 field list."""
        if self._row is None:
            return
        import csv as _csv

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
            writer = _csv.DictWriter(f, fieldnames=SCHEMA_FIELDS_V13)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {k: self._row.get(k, "") for k in SCHEMA_FIELDS_V13}
            )
