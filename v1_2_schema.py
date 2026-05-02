"""
v1_2_schema.py
--------------
v1.2 schema phase — parallel observer module.

Implements SICC Commitment 1 (schema as embodied a priori): the agent
acquires an explicit representation of the categorical structure of its
environment — cell types as kinds, actions as available verbs, phases
as developmental periods, flag types as formation categories — held as
an inspectable structure from construction time.

The schema is given, not learned. It does not drive the agent's
action-selection pipeline, drive composition, model updates, or any
other behavioural pathway. The agent can call query_schema() to examine
the schema; calling it produces no side effects and alters no state.

Implementation pattern: parallel observer, identical to v1_1_provenance.py.
The v0.14 agent and world are unmodified. The agent subclass V12Agent
adds _build_schema() and query_schema() at construction time without
touching any inherited method. The schema observer V12SchemaObserver
reads the agent's schema at on_run_end() and writes it to schema_v1_2.csv.
With the observer either disabled or absent, the batch produces v1.1-
baseline-identical output at matched seeds (permanent regression test).

Schema structure
----------------
Four sub-schemas, each a dict keyed by category name:

  cell_type_schema  — FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE,
                      KNOWLEDGE with architectural property fields.
  action_schema     — UP, DOWN, LEFT, RIGHT with (dx, dy) offset pairs.
  phase_schema      — PHASE_1, PHASE_2, PHASE_3 with drive compositions
                      and transition conditions.
  flag_type_schema  — THREAT, MASTERY, KNOWLEDGE_BANKING, END_STATE
                      with formation conditions and confirming/
                      disconfirming operationalisations.

Public interface
----------------
V12Agent.query_schema(domain, key=None)
    domain: 'cell_types' | 'actions' | 'phases' | 'flag_types'
    key:    optional string to retrieve a single entry; if None, the
            full sub-schema dict is returned.
    Returns a copy of the requested schema structure (no aliasing).

V12SchemaObserver(agent, world, run_metadata, cell_type_constants)
    Parallel observer. Call on_run_end(step) once at end of each run.
    Call write_schema_csv(path, append=True) to persist.
    Call reset() between runs.

CSV outputs
-----------
schema_v1_2.csv  — one row per run, schema field values.
"""

import copy
import csv

from curiosity_agent_v0_14 import (
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE,
    FLAG_THRESHOLD, MASTERY_THRESHOLD, KNOWLEDGE_THRESHOLD,
    FEATURE_DRIVE_WEIGHT, ATTRACTION_BONUS,
    DevelopmentalAgent as V014Agent,
)


# ---------------------------------------------------------------------------
# Schema field names for the output CSV (one row per run).
# The schema content is largely identical across all runs at matched
# parameters; the run_id fields allow cross-run verification (Category β)
# and per-run consistency checks (Category δ3).
# ---------------------------------------------------------------------------

SCHEMA_FIELDS = [
    # Run identification
    "arch", "hazard_cost", "num_steps", "run_idx", "seed",

    # Cell-type schema: one column per (cell_type, property) pair.
    # 6 types × 6 properties = 36 columns.
    "ct_FRAME_passable",
    "ct_FRAME_cost_on_entry",
    "ct_FRAME_feature_reward_eligible",
    "ct_FRAME_attraction_bias_eligible",
    "ct_FRAME_gating_eligible",
    "ct_FRAME_transformation_eligible",

    "ct_NEUTRAL_passable",
    "ct_NEUTRAL_cost_on_entry",
    "ct_NEUTRAL_feature_reward_eligible",
    "ct_NEUTRAL_attraction_bias_eligible",
    "ct_NEUTRAL_gating_eligible",
    "ct_NEUTRAL_transformation_eligible",

    "ct_HAZARD_passable",
    "ct_HAZARD_cost_on_entry",
    "ct_HAZARD_feature_reward_eligible",
    "ct_HAZARD_attraction_bias_eligible",
    "ct_HAZARD_gating_eligible",
    "ct_HAZARD_transformation_eligible",

    "ct_ATTRACTOR_passable",
    "ct_ATTRACTOR_cost_on_entry",
    "ct_ATTRACTOR_feature_reward_eligible",
    "ct_ATTRACTOR_attraction_bias_eligible",
    "ct_ATTRACTOR_gating_eligible",
    "ct_ATTRACTOR_transformation_eligible",

    "ct_END_STATE_passable",
    "ct_END_STATE_cost_on_entry",
    "ct_END_STATE_feature_reward_eligible",
    "ct_END_STATE_attraction_bias_eligible",
    "ct_END_STATE_gating_eligible",
    "ct_END_STATE_transformation_eligible",

    "ct_KNOWLEDGE_passable",
    "ct_KNOWLEDGE_cost_on_entry",
    "ct_KNOWLEDGE_feature_reward_eligible",
    "ct_KNOWLEDGE_attraction_bias_eligible",
    "ct_KNOWLEDGE_gating_eligible",
    "ct_KNOWLEDGE_transformation_eligible",

    # Action schema: 4 actions × 2 offset fields = 8 columns.
    "act_UP_dx", "act_UP_dy",
    "act_DOWN_dx", "act_DOWN_dy",
    "act_LEFT_dx", "act_LEFT_dy",
    "act_RIGHT_dx", "act_RIGHT_dy",

    # Phase schema: 3 phases × 4 fields = 12 columns.
    # drive_composition and transition_condition are pipe-delimited strings.
    "ph_PHASE_1_drive_composition",
    "ph_PHASE_1_transition_condition",
    "ph_PHASE_1_phase_number",
    "ph_PHASE_1_drive_weights",

    "ph_PHASE_2_drive_composition",
    "ph_PHASE_2_transition_condition",
    "ph_PHASE_2_phase_number",
    "ph_PHASE_2_drive_weights",

    "ph_PHASE_3_drive_composition",
    "ph_PHASE_3_transition_condition",
    "ph_PHASE_3_phase_number",
    "ph_PHASE_3_drive_weights",

    # Flag-type schema: 4 types × 5 fields = 20 columns.
    "ft_THREAT_formation_condition",
    "ft_THREAT_formation_threshold",
    "ft_THREAT_confirming_operationalisation",
    "ft_THREAT_disconfirming_semantics",
    "ft_THREAT_cell_types_applicable",

    "ft_MASTERY_formation_condition",
    "ft_MASTERY_formation_threshold",
    "ft_MASTERY_confirming_operationalisation",
    "ft_MASTERY_disconfirming_semantics",
    "ft_MASTERY_cell_types_applicable",

    "ft_KNOWLEDGE_BANKING_formation_condition",
    "ft_KNOWLEDGE_BANKING_formation_threshold",
    "ft_KNOWLEDGE_BANKING_confirming_operationalisation",
    "ft_KNOWLEDGE_BANKING_disconfirming_semantics",
    "ft_KNOWLEDGE_BANKING_cell_types_applicable",

    "ft_END_STATE_formation_condition",
    "ft_END_STATE_formation_threshold",
    "ft_END_STATE_confirming_operationalisation",
    "ft_END_STATE_disconfirming_semantics",
    "ft_END_STATE_cell_types_applicable",

    # Schema completeness summary (Category β).
    "schema_cell_types_count",
    "schema_actions_count",
    "schema_phases_count",
    "schema_flag_types_count",
    "schema_complete",
]


# ---------------------------------------------------------------------------
# V12Agent: V014Agent subclass with schema.
# Adds _build_schema() at __init__ time and query_schema() as a read-only
# interface. No inherited method is overridden.
# ---------------------------------------------------------------------------

class V12Agent(V014Agent):
    """v0.14 agent with explicit schema (SICC Commitment 1).

    The schema is built at construction time from the architecture's
    own constants and the world's specifications. It does not drive
    any behavioural pathway; query_schema() is read-only and side-
    effect-free.
    """

    def __init__(self, world, num_steps):
        super().__init__(world, num_steps)
        self._schema = self._build_schema(world)

    def _build_schema(self, world):
        """Construct the four sub-schemas from architectural constants."""

        # ---------------------------------------------------------------
        # Cell-type schema.
        # Properties derived from the v0.14 / v0.13 / v0.10 specs:
        #   passable              — FRAME is the only impassable type.
        #   cost_on_entry         — HAZARD only (pre-transformation),
        #                           value is the world's hazard_cost.
        #   feature_reward_elig.  — ATTRACTOR, END_STATE (pre-banking),
        #                           KNOWLEDGE (post-transition, pre-banking).
        #   attraction_bias_elig. — ATTRACTOR, END_STATE (pre-banking).
        #   gating_eligible       — HAZARD only (hard-gate on flagged cells).
        #   transformation_elig.  — HAZARD only (v0.14 competency-gated).
        # ---------------------------------------------------------------
        hazard_cost = getattr(world, "hazard_cost", None)

        cell_type_schema = {
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
                "cost_on_entry": None,
                "feature_reward_eligible": False,
                "attraction_bias_eligible": False,
                "gating_eligible": False,
                "transformation_eligible": False,
            },
            "HAZARD": {
                "code": HAZARD,
                "passable": True,
                "cost_on_entry": hazard_cost,
                "feature_reward_eligible": False,
                "attraction_bias_eligible": False,
                "gating_eligible": True,
                "transformation_eligible": True,
            },
            "ATTRACTOR": {
                "code": ATTRACTOR,
                "passable": True,
                "cost_on_entry": None,
                "feature_reward_eligible": True,
                "attraction_bias_eligible": True,
                "gating_eligible": False,
                "transformation_eligible": False,
            },
            "END_STATE": {
                "code": END_STATE,
                "passable": True,
                "cost_on_entry": None,
                "feature_reward_eligible": True,
                "attraction_bias_eligible": True,
                "gating_eligible": False,
                "transformation_eligible": False,
            },
            "KNOWLEDGE": {
                "code": KNOWLEDGE,
                "passable": True,
                "cost_on_entry": None,
                "feature_reward_eligible": True,
                "attraction_bias_eligible": False,
                "gating_eligible": False,
                "transformation_eligible": False,
            },
        }

        # ---------------------------------------------------------------
        # Action schema.
        # Action codes 0–3 as defined in v1.1/v0.14 batch runner world.step:
        #   0 = UP    (y decreases: dy = -1)
        #   1 = DOWN  (y increases: dy = +1)
        #   2 = LEFT  (x decreases: dx = -1)
        #   3 = RIGHT (x increases: dx = +1)
        # ---------------------------------------------------------------
        action_schema = {
            "UP":    {"code": 0, "dx": 0,  "dy": -1},
            "DOWN":  {"code": 1, "dx": 0,  "dy": +1},
            "LEFT":  {"code": 2, "dx": -1, "dy":  0},
            "RIGHT": {"code": 3, "dx": +1, "dy":  0},
        }

        # ---------------------------------------------------------------
        # Phase schema.
        # Drive compositions and transition conditions from the v0.14
        # three-phase developmental schedule.
        # Phase 1: prescribed acquisition — boustrophedon path completion.
        # Phase 2: drive-based integration — transitions at 60% of run.
        # Phase 3: preference-weighted autonomy — runs to end.
        # Drive weights are stored as a dict; None for inactive drives.
        # ---------------------------------------------------------------
        phase_schema = {
            "PHASE_1": {
                "phase_number": 1,
                "drive_composition": ["prescribed_path"],
                "transition_condition": "boustrophedon_path_completion",
                "drive_weights": {
                    "prescribed_path": 1.0,
                    "novelty": None,
                    "learning_progress": None,
                    "preference": None,
                    "feature": None,
                },
            },
            "PHASE_2": {
                "phase_number": 2,
                "drive_composition": [
                    "novelty",
                    "learning_progress",
                    "feature",
                ],
                "transition_condition": "proportional_run_length_0.6",
                "drive_weights": {
                    "prescribed_path": None,
                    "novelty": 1.0,
                    "learning_progress": 1.0,
                    "preference": None,
                    "feature": FEATURE_DRIVE_WEIGHT,
                },
            },
            "PHASE_3": {
                "phase_number": 3,
                "drive_composition": [
                    "novelty",
                    "learning_progress",
                    "preference",
                    "feature",
                ],
                "transition_condition": "run_end",
                "drive_weights": {
                    "prescribed_path": None,
                    "novelty": 1.0,
                    "learning_progress": 1.0,
                    "preference": 1.0,
                    "feature": FEATURE_DRIVE_WEIGHT,
                },
            },
        }

        # ---------------------------------------------------------------
        # Flag-type schema.
        # Formation conditions and confirming/disconfirming semantics
        # from the v1.1 pre-registration §2.2 and §2.3 specifications.
        # ---------------------------------------------------------------
        flag_type_schema = {
            "THREAT": {
                "formation_condition": (
                    "hazard_cell_entered FLAG_THRESHOLD times (v0.10 rule) "
                    "OR first_entry_signature_match on same-category cell "
                    "(v0.12 rule)"
                ),
                "formation_threshold": FLAG_THRESHOLD,
                "confirming_operationalisation": (
                    "signature_match_at_adjacent_same_category_cell | "
                    "forced_entry_to_flagged_cell | "
                    "phase_boundary_persistence_as_hazard"
                ),
                "disconfirming_semantics": (
                    "v0.14_competency_gated_transformation: cell transitions "
                    "from HAZARD to KNOWLEDGE; exactly one disconfirming "
                    "observation recorded per transformation event"
                ),
                "cell_types_applicable": ["HAZARD"],
            },
            "MASTERY": {
                "formation_condition": (
                    f"attractor_cell_entered {MASTERY_THRESHOLD} times "
                    "(v0.11.2 rule)"
                ),
                "formation_threshold": MASTERY_THRESHOLD,
                "confirming_operationalisation": (
                    "post_banking_visit_to_mastered_attractor_cell"
                ),
                "disconfirming_semantics": (
                    "none_under_present_architecture: mastery_flags_do_not_"
                    "retract; slot_exists_for_future_iterations"
                ),
                "cell_types_applicable": ["ATTRACTOR"],
            },
            "KNOWLEDGE_BANKING": {
                "formation_condition": (
                    f"knowledge_cell_entered {KNOWLEDGE_THRESHOLD} times "
                    "post_v0.14_transformation (v0.14 rule)"
                ),
                "formation_threshold": KNOWLEDGE_THRESHOLD,
                "confirming_operationalisation": (
                    "post_banking_visit_to_banked_knowledge_cell"
                ),
                "disconfirming_semantics": (
                    "none_under_present_architecture: knowledge_banking_flags"
                    "_do_not_retract; slot_exists_for_future_iterations"
                ),
                "cell_types_applicable": ["KNOWLEDGE"],
            },
            "END_STATE": {
                "formation_condition": (
                    "all_attractors_mastered_AND_all_hazards_banked_as_"
                    "knowledge trigger fires (v0.14_amended activation); "
                    "banking on first_post_activation_entry to end_state_cell"
                ),
                "formation_threshold": 1,
                "confirming_operationalisation": (
                    "activation: post_activation_steps_where_all_attractors_"
                    "mastered_AND_all_hazards_banked_as_knowledge_holds | "
                    "banking: post_banking_visit_to_end_state_cell"
                ),
                "disconfirming_semantics": (
                    "none_under_present_architecture: end_state_flags_do_not_"
                    "retract; slot_exists_for_future_iterations"
                ),
                "cell_types_applicable": ["END_STATE"],
            },
        }

        return {
            "cell_types": cell_type_schema,
            "actions": action_schema,
            "phases": phase_schema,
            "flag_types": flag_type_schema,
        }

    def query_schema(self, domain, key=None):
        """Return schema content for a named domain.

        domain : 'cell_types' | 'actions' | 'phases' | 'flag_types'
        key    : optional string; if provided, returns only that entry.

        Returns a deep copy so callers cannot mutate the schema.
        Raises KeyError if the domain or key does not exist.
        """
        if domain not in self._schema:
            raise KeyError(
                f"Unknown schema domain {domain!r}. "
                f"Valid domains: {list(self._schema)}"
            )
        sub = self._schema[domain]
        if key is not None:
            if key not in sub:
                raise KeyError(
                    f"Key {key!r} not found in schema domain {domain!r}. "
                    f"Available keys: {list(sub)}"
                )
            return copy.deepcopy(sub[key])
        return copy.deepcopy(sub)


# ---------------------------------------------------------------------------
# V12SchemaObserver: parallel observer that serialises the agent's schema.
# ---------------------------------------------------------------------------

class V12SchemaObserver:
    """Parallel observer — writes the agent's schema to schema_v1_2.csv.

    Called by the batch runner at on_run_end() once per run. Does not
    modify the agent or the world. Does not call on_pre_action() or
    on_post_event(); those hooks are included for interface compatibility
    with the v1.0 and v1.1 observer pattern but are no-ops here.

    The schema content should be identical across all 180 runs at
    matched parameters (Category δ3). Any deviation from uniformity
    is logged as a category-δ3 anomaly in the per-run row's
    schema_complete field.
    """

    EXPECTED_CELL_TYPES = {
        "FRAME", "NEUTRAL", "HAZARD", "ATTRACTOR", "END_STATE", "KNOWLEDGE",
    }
    EXPECTED_ACTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}
    EXPECTED_PHASES = {"PHASE_1", "PHASE_2", "PHASE_3"}
    EXPECTED_FLAG_TYPES = {
        "THREAT", "MASTERY", "KNOWLEDGE_BANKING", "END_STATE",
    }

    def __init__(self, agent, world, run_metadata, cell_type_constants=None):
        self._agent = agent
        self._world = world
        self._meta = dict(run_metadata)
        self._row = None

    # ------------------------------------------------------------------
    # Hook interface (on_pre_action and on_post_event are no-ops here;
    # the schema does not change during a run).
    # ------------------------------------------------------------------

    def on_pre_action(self, step):
        pass

    def on_post_event(self, step):
        pass

    def on_run_end(self, step):
        """Serialise the agent's schema to a flat row dict."""
        schema = self._agent.query_schema
        row = {
            "arch": "v1_2",
            "hazard_cost": self._meta.get("hazard_cost"),
            "num_steps": self._meta.get("num_steps"),
            "run_idx": self._meta.get("run_idx"),
            "seed": self._meta.get("seed"),
        }

        # ----------------------------------------------------------------
        # Cell-type schema serialisation.
        # ----------------------------------------------------------------
        ct_schema = schema("cell_types")
        for ct_name in [
            "FRAME", "NEUTRAL", "HAZARD", "ATTRACTOR", "END_STATE", "KNOWLEDGE"
        ]:
            entry = ct_schema.get(ct_name, {})
            prefix = f"ct_{ct_name}_"
            row[prefix + "passable"] = entry.get("passable")
            row[prefix + "cost_on_entry"] = entry.get("cost_on_entry")
            row[prefix + "feature_reward_eligible"] = entry.get(
                "feature_reward_eligible"
            )
            row[prefix + "attraction_bias_eligible"] = entry.get(
                "attraction_bias_eligible"
            )
            row[prefix + "gating_eligible"] = entry.get("gating_eligible")
            row[prefix + "transformation_eligible"] = entry.get(
                "transformation_eligible"
            )

        # ----------------------------------------------------------------
        # Action schema serialisation.
        # ----------------------------------------------------------------
        act_schema = schema("actions")
        for act_name in ["UP", "DOWN", "LEFT", "RIGHT"]:
            entry = act_schema.get(act_name, {})
            prefix = f"act_{act_name}_"
            row[prefix + "dx"] = entry.get("dx")
            row[prefix + "dy"] = entry.get("dy")

        # ----------------------------------------------------------------
        # Phase schema serialisation.
        # ----------------------------------------------------------------
        ph_schema = schema("phases")
        for ph_name in ["PHASE_1", "PHASE_2", "PHASE_3"]:
            entry = ph_schema.get(ph_name, {})
            prefix = f"ph_{ph_name}_"
            row[prefix + "drive_composition"] = "|".join(
                entry.get("drive_composition", [])
            )
            row[prefix + "transition_condition"] = entry.get(
                "transition_condition", ""
            )
            row[prefix + "phase_number"] = entry.get("phase_number")
            # Serialise drive_weights dict as "drive:weight|..." string.
            dw = entry.get("drive_weights", {})
            row[prefix + "drive_weights"] = "|".join(
                f"{k}:{v}" for k, v in sorted(dw.items())
            )

        # ----------------------------------------------------------------
        # Flag-type schema serialisation.
        # ----------------------------------------------------------------
        ft_schema = schema("flag_types")
        for ft_name in [
            "THREAT", "MASTERY", "KNOWLEDGE_BANKING", "END_STATE"
        ]:
            entry = ft_schema.get(ft_name, {})
            prefix = f"ft_{ft_name}_"
            row[prefix + "formation_condition"] = entry.get(
                "formation_condition", ""
            )
            row[prefix + "formation_threshold"] = entry.get(
                "formation_threshold"
            )
            row[prefix + "confirming_operationalisation"] = entry.get(
                "confirming_operationalisation", ""
            )
            row[prefix + "disconfirming_semantics"] = entry.get(
                "disconfirming_semantics", ""
            )
            row[prefix + "cell_types_applicable"] = "|".join(
                entry.get("cell_types_applicable", [])
            )

        # ----------------------------------------------------------------
        # Schema completeness summary (Category β).
        # ----------------------------------------------------------------
        actual_ct = set(ct_schema.keys())
        actual_act = set(act_schema.keys())
        actual_ph = set(ph_schema.keys())
        actual_ft = set(ft_schema.keys())

        row["schema_cell_types_count"] = len(actual_ct)
        row["schema_actions_count"] = len(actual_act)
        row["schema_phases_count"] = len(actual_ph)
        row["schema_flag_types_count"] = len(actual_ft)

        complete = (
            actual_ct == self.EXPECTED_CELL_TYPES
            and actual_act == self.EXPECTED_ACTIONS
            and actual_ph == self.EXPECTED_PHASES
            and actual_ft == self.EXPECTED_FLAG_TYPES
        )
        row["schema_complete"] = complete

        self._row = row

    # ------------------------------------------------------------------
    # CSV output.
    # ------------------------------------------------------------------

    def write_schema_csv(self, path, append=False):
        """Write this run's schema row to path."""
        if self._row is None:
            return
        mode = "a" if append else "w"
        write_header = (not append) or (not _file_has_rows(path))
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMA_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {k: self._row.get(k, "") for k in SCHEMA_FIELDS}
            )

    def summary_metrics(self):
        """Return per-run schema summary fields for the metrics CSV."""
        if self._row is None:
            return {
                "schema_cell_types_count": 0,
                "schema_actions_count": 0,
                "schema_phases_count": 0,
                "schema_flag_types_count": 0,
                "schema_complete": False,
            }
        return {
            "schema_cell_types_count": self._row.get(
                "schema_cell_types_count", 0
            ),
            "schema_actions_count": self._row.get("schema_actions_count", 0),
            "schema_phases_count": self._row.get("schema_phases_count", 0),
            "schema_flag_types_count": self._row.get(
                "schema_flag_types_count", 0
            ),
            "schema_complete": self._row.get("schema_complete", False),
        }

    def reset(self):
        self._row = None

    def record_count(self):
        return 1 if self._row is not None else 0


# ---------------------------------------------------------------------------
# Helper.
# ---------------------------------------------------------------------------

def _file_has_rows(path):
    try:
        with open(path) as f:
            lines = [l for l in f if l.strip()]
        return len(lines) > 1
    except FileNotFoundError:
        return False
