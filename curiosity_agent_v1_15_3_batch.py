"""
curiosity_agent_v1_15_3_batch.py
----------------------------------
v1.15.3: Witnessed Navigation — waypoint injection at social observation fire.

v1.15.2 demonstrated that the directed search bonus (0.5/d at
SOCIALLY_CORROBORATED_STATE) is insufficient to redirect Q-table navigation.
The social observation fired correctly and early (mean ENV2 step ~100–400),
the being_observed records confirmed first-contact timing, Q6 statements
were produced — but arc_total_steps_b was bit-for-bit identical to v1.15
across all 13 soc=S runs. The bonus at 0.5/d (~0.06 per step at d=8)
does not compete with Q-values accumulated over 1M ENV1 training steps.

ADDITION IN V1.15.3
  WAYPOINT INJECTION AT SOCIAL OBSERVATION FIRE
  At the moment social observation fires in _fire_social_observation,
  inject SOCIAL_OBS_WAYPOINT_COUNT waypoints at att_pos into the world
  object. This uses the same mechanism that reliably directs agents in the
  ENV1 transfer phase (inject_waypoint). The waypoint creates a navigational
  pull toward att_blue strong enough to change action selection, not just
  modify a per-step reward coefficient.

  The directed search bonus (0.5/d) is retained as secondary reinforcement.
  The waypoint injection is the primary navigational intervention.

  SOCIAL_OBS_WAYPOINT_COUNT = 5 (transfer phase uses 2; extended count
  compensates for the longer distances at which social obs fires in v1.15.3).

INHERITED UNCHANGED FROM V1.15.2
  - SOCIAL_PERCEPTION_RADIUS = 10.0 (geometry fix)
  - SimpleNamespace Q6 statements (reporting fix)
  - All v1.15.1 architecture: inter-agent perception, social observation
    gate, socially_corroborated state, being_observed substrate, ZPD.

NEW OUTPUT FILES
  social_observation_v1_15_3.csv
  being_observed_v1_15_3.csv

ARCH = v1_15_3. Seeds from run_data_v1_15.csv. seed_b = seed_a + 20_000.

PRE-REGISTRATION: v1_15_1_pre_registration.md (8 May 2026). v1.15.3 is
an addition to meet the original v1.15 goal: the bonus-only architecture
(v1.15.2) was architecturally correct but navigationally insufficient.
Waypoint injection recorded as the mechanism change.
"""

import argparse
import csv
import math
import os
from types import SimpleNamespace

import numpy as np

import v1_13_observer_substrates  # noqa: F401
from v1_13_observer_substrates import (
    build_bundle_from_observers, PREDICTION_FAMILY_MINIMUM,
)
from v1_13_world import (
    V113World, ENV1_FAMILIES, ENV2_FAMILIES, NUM_ACTIONS,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ,
    PERCEPTION_RADIUS, CONTACT_RADIUS, START_POS,
    GREEN, YELLOW, BLUE,
    SQUARE_2D, TRIANGLE_2D, CIRCLE_2D, SPHERE_3D, PYRAMID_3D,
)
from v1_10_agent import V110Agent
from v1_7_agent  import V17Agent

from v1_1_provenance                import V1ProvenanceStore
from v1_3_schema_extension          import V13SchemaObserver as V13SchemaObserverBase
from v1_3_family_observer           import V13FamilyObserver
from v1_4_comparison_observer       import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver
from v1_6_reporting_layer           import V16ReportingLayer
from v1_7_observer_substrates       import flush_provenance_csv
from v1_8_goal_layer                import V18GoalObserver, assign_goal, GOAL_FIELDS
from v1_9_counterfactual_observer   import (
    V19CounterfactualObserver, COUNTERFACTUAL_FIELDS,
)
from v1_10_belief_revision_observer import (
    V110BeliefRevisionObserver, BELIEF_REVISION_FIELDS,
)
from v1_11_causal_observer import (
    V111CausalObserver, CAUSAL_FIELDS, CHAIN_DEPTH_MINIMUM,
)
from v1_13_schema_extension import (
    V13SchemaObserver as V13SchemaObserverPrediction,
    PREDICTED_SCHEMA_FIELDS,
    PREDICTED_STATE, CONFIRMED_STATE, UNRESOLVABLE_STATE,
)

# ---------------------------------------------------------------------------
# v1.15.1 new: Socially corroborated schema state
# ---------------------------------------------------------------------------

SOCIALLY_CORROBORATED_STATE = "socially_corroborated"   # v1.15.1
V1_14_1_BASELINE_MEAN       = 230_734                   # v1.14.1 arc_total mean
SOCIAL_PERCEPTION_RADIUS    = 10.0                      # v1.15.2: extended range for social observation only
SOCIAL_OBS_WAYPOINT_COUNT   = 5                         # v1.15.3: waypoints injected at social observation fire


class V1511SchemaObserver(V13SchemaObserverPrediction):
    """Extends V13SchemaObserverPrediction with social corroboration.

    Adds the socially_corroborated state (predicted -> socially_corroborated
    -> confirmed/unresolvable). Social corroboration is not confirmation:
    own mastery is still required for the CONFIRMED transition.
    """

    def socially_corroborate_record(
        self, object_id: str, step: int, env: int
    ) -> bool:
        """Transition a predicted record to socially_corroborated.

        Fires when Agent B observes Agent A at att_blue while holding
        an open prediction. Returns True if a record was found and updated.
        Only PREDICTED_STATE records are eligible.
        """
        if not self._prediction_enabled:
            return False
        for rec in self._predicted_records:
            if (rec["object_id"] == object_id
                    and rec["state"] == PREDICTED_STATE):
                rec["state"]                 = SOCIALLY_CORROBORATED_STATE
                rec["social_observation_step"] = step
                rec["social_observation_env"]  = env
                return True
        return False

    def has_open_prediction(self, object_id: str) -> bool:
        """True if record is open: PREDICTED or SOCIALLY_CORROBORATED.

        Both are open states — own mastery not yet achieved. CONFIRMED
        and UNRESOLVABLE are closed.
        """
        return any(
            r["object_id"] == object_id
            and r["state"] in (PREDICTED_STATE, SOCIALLY_CORROBORATED_STATE)
            for r in self._predicted_records
        )

    def confirm_predicted_record(self, object_id, confirmation_step, confirming_env):
        """Override: accept both PREDICTED and SOCIALLY_CORROBORATED states.

        Base class only confirms from PREDICTED_STATE. After social
        corroboration the record is SOCIALLY_CORROBORATED — own mastery
        still transitions it to CONFIRMED.
        """
        if not self._prediction_enabled:
            return False
        for rec in self._predicted_records:
            if (rec["object_id"] == object_id
                    and rec["state"] in (PREDICTED_STATE,
                                         SOCIALLY_CORROBORATED_STATE)):
                rec["state"]             = CONFIRMED_STATE
                rec["confirmation_step"] = confirmation_step
                rec["confirming_env"]    = confirming_env
                return True
        return False

    def predicted_schema_rows(self, run_meta):
        """Override to include social_observation fields."""
        rows = super().predicted_schema_rows(run_meta)
        for row in rows:
            rec = next(
                (r for r in self._predicted_records
                 if r["object_id"] == row.get("object_id")), {}
            )
            row["social_observation_step"] = rec.get("social_observation_step", "")
            row["social_observation_env"]  = rec.get("social_observation_env",  "")
        return rows


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_CSV_PRIMARY         = "run_data_v1_15.csv"
RUN_DATA_CSV             = "run_data_v1_15_3.csv"
PROVENANCE_CSV           = "provenance_v1_15_3.csv"
GOAL_CSV                 = "goal_v1_15_3.csv"
COUNTERFACTUAL_CSV       = "counterfactual_v1_15_3.csv"
BELIEF_REVISION_CSV      = "belief_revision_v1_15_3.csv"
CAUSAL_CSV               = "causal_v1_15_3.csv"
REPORT_CSV               = "report_v1_15_3.csv"
REPORT_SUMMARY_CSV       = "report_summary_v1_15_3.csv"
END_STATE_DRAW_CSV       = "end_state_draw_log_v1_15_3.csv"
ENV2_RUN_DATA_CSV        = "env2_run_data_v1_15_3.csv"
Q5_INDIVIDUATION_CSV     = "q5_individuation_v1_15_3.csv"
PREDICTED_SCHEMA_CSV     = "predicted_schema_v1_15_3.csv"
ARC_COMPLETE_CSV         = "arc_complete_v1_15_3.csv"
ARC_PAIRED_CSV           = "arc_paired_v1_15_3.csv"
SOCIAL_OBSERVATION_CSV   = "social_observation_v1_15_3.csv"   # v1.15.1
BEING_OBSERVED_CSV       = "being_observed_v1_15_3.csv"       # v1.15.1

ENV1_STEPS         = 1_000_000
ENV2_STEPS         =   800_000
RETURN_ENV1_STEPS  =   200_000
BATCH_STEPS        = ENV1_STEPS
HAZARD_COSTS       = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST      = 10
ARCH               = "v1_15_3"
ENV2_SEED_OFFSET   = 10_000
RETURN_SEED_OFFSET = 20_000
SEED_B_OFFSET      = 20_000

RETURN_ENV1_FAMILIES = [
    {"colour": GREEN,  "dist_id": "dist_green",  "dist_pos": (3.0,9.0,3.0),
     "att_id": "att_green",  "att_pos": (2.0,11.0,2.0), "att_form": SQUARE_2D,
     "haz_id": "haz_green",  "haz_pos": (9.0,10.0,8.0), "haz_form": SPHERE_3D},
    {"colour": YELLOW, "dist_id": "dist_yellow", "dist_pos": (8.0,3.0,3.0),
     "att_id": "att_yellow", "att_pos": (10.0,2.0,2.0), "att_form": TRIANGLE_2D,
     "haz_id": "haz_yellow", "haz_pos": (3.0,5.0,7.0),  "haz_form": PYRAMID_3D},
    {"colour": BLUE,   "dist_id": None, "dist_pos": None,
     "att_id": "att_blue",   "att_pos": (5.0,6.0,10.0), "att_form": CIRCLE_2D,
     "haz_id": "haz_blue",   "haz_pos": (7.0,8.0,3.0),  "haz_form": SPHERE_3D},
]
RETURN_ENV1_PRECOMPLETED = [
    "haz_yellow","haz_green","haz_unaff_0","haz_unaff_1","haz_unaff_2",
]

# ---------------------------------------------------------------------------
# Field definitions
# ---------------------------------------------------------------------------

RUN_DATA_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost","num_steps",
    "phase_1_end_step","phase_2_end_step",
    "time_to_first_flag","time_to_second_flag","time_to_final_flag",
    "total_cost_incurred","time_to_first_mastery","time_to_final_mastery",
    "mastery_order_sequence","activation_step","end_state_found_step",
    "end_state_banked","time_to_first_transition","time_to_final_transition",
    "transition_order_sequence","knowledge_banked_sequence",
    "yellow_pre_transition_entries","green_pre_transition_entries",
    "unaffiliated_pre_transition_entries",
    "yellow_resolution_window","green_resolution_window",
    "total_prediction_error_events","prediction_error_complete",
    "goal_type","goal_target_id","goal_step_budget","goal_resolved",
    "goal_resolution_step","goal_budget_remaining","goal_expired",
    "goal_last_progress_step","goal_resolution_window","goal_progress_event_count",
    "suppressed_approach_count","goal_relevant_suppressed_count",
    "suppressed_approach_objects","cf_records_raw","cf_records_emitted",
    "cf_exclusion_rate","end_state_draw_active","end_state_banked_step",
    "steps_draw_to_bank","revised_expectation_count","causal_chain_count",
    "mean_chain_depth","complete_chain_count","q5_statement_count",
    "env2_ran","haz_blue_approached","predicted_record_written",
    "transfer_triggered_step","env1_mastery_order_sequence",
    "env1_end_state_banked_step","return_env1_ran","arc_complete",
    "arc_timeout","ineligible_reason","return_step",
    "transformation_step","arc_total_steps",
    # v1.15.1 new
    "social_corroboration_fired","social_observation_step","zpd_delta",
]

ARC_COMPLETE_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost",
    "arc_complete","arc_timeout","ineligible_reason",
    "env1_surprise_step","prediction_step","transfer_triggered_step",
    "confirmation_step","return_step","transformation_step",
    "arc_total_steps","arc_env_span","causal_chain_depth","causal_chain_complete",
    # v1.15.1 new
    "social_corroboration_fired","social_observation_step","zpd_delta",
]

ARC_PAIRED_FIELDS = [
    "arch","run_idx","seed_a","seed_b","hazard_cost",
    "arc_complete_a","arc_complete_b","both_arc_complete",
    "arc_total_steps_a","arc_total_steps_b","arc_total_steps_delta",
    "transformation_step_a","transformation_step_b",
    "transfer_triggered_step_a","transfer_triggered_step_b",
    "env2_actual_steps_a","env2_actual_steps_b",
    "first_transformer","haz_blue_shared_benefit","individuation_confirmed",
    # v1.15.1 new
    "social_corroboration_fired_b","zpd_delta_b","being_observed_fired_a",
]

SOCIAL_OBSERVATION_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost",
    "observation_step","observer_pos","observed_agent","observed_agent_pos",
    "object_id","predicted_record_pre_state","predicted_record_post_state",
]

BEING_OBSERVED_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost",
    "step","observed_by","object_id","observer_pos","own_mastery_at_step",
]

PREDICTED_SCHEMA_FIELDS_151 = PREDICTED_SCHEMA_FIELDS + [
    "social_observation_step","social_observation_env",
]

REPORT_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost","num_steps",
    "query_type","statement_text","source_type","source_key","source_resolves",
]
SUMMARY_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost","num_steps",
    "total_statements","statements_q1","statements_q2","statements_q3",
    "statements_q4","statements_q5","statements_q6",
    "hallucination_count","q1_formation_depth","q3_surprise_cells",
    "q3_resolution_stated","report_complete","statements_with_relevance_markers",
    "goal_statement_present","goal_resolution_stated","q4_statement_count",
    "suppressed_approach_count","goal_relevant_suppressed_count",
    "br_statement_count","revised_expectation_count","mean_approach_delta",
    "bias_effective","cf_records_raw","cf_records_emitted","cf_exclusion_rate",
    "end_state_draw_active","end_state_banked_step","causal_chain_count",
    "mean_chain_depth","complete_chain_count","q5_statement_count",
    "predicted_record_written","predicted_record_state",
    "social_corroboration_fired","zpd_delta",
]
END_STATE_DRAW_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost","num_steps",
    "activation_step","end_state_banked_step","steps_draw_to_bank",
    "end_state_draw_active",
]
ENV2_RUN_DATA_FIELDS = [
    "arch","run_idx","agent","seed","hazard_cost","env2_seed",
    "env2_activation_step","env2_phase_1_end_step","env2_end_state_banked_step",
    "env2_yellow_pre_transition_entries","env2_yellow_resolution_window",
    "env2_green_pre_transition_entries","env2_green_resolution_window",
    "env2_q5_chain_count","env2_q5_mean_chain_depth",
    "att_blue_mastery_step","att_blue_mastery_env",
    "predicted_record_state_at_run_end","att_blue_sequence_position",
    "env2_mastery_order_sequence","env2_att_yellow_mastery_step",
    "env2_att_green_mastery_step","env2_actual_steps",
]
Q5_INDIVIDUATION_FIELDS = [
    "arch","run_idx_a","run_idx_b","seed_a","seed_b","hazard_cost",
    "chain_object_a","chain_object_b","link_sequence_a","link_sequence_b",
    "link_sequence_distance","within_run",
]

# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

def load_seeds(path):
    seeds = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                key = (float(row["hazard_cost"]), int(row["run_idx"]))
                if key not in seeds:
                    seeds[key] = int(row["seed"])
            except (ValueError, KeyError):
                continue
    return seeds

def _find_seed_csv():
    if os.path.exists(SEED_CSV_PRIMARY):
        seeds = load_seeds(SEED_CSV_PRIMARY)
        if seeds:
            print(f"  Seed source: {SEED_CSV_PRIMARY} ({len(seeds)} seeds)")
            return seeds
    return {}

# ---------------------------------------------------------------------------
# Transfer / return gates (inherited)
# ---------------------------------------------------------------------------

def _check_transfer_condition(world, agent, predicted_record_written):
    if not all(world.knowledge_unlocked.get(h,False) for h in world.hazard_cells):
        return False
    if not all(getattr(agent,"mastery_flag",{}).get(a,0)==1
               for a in world.attractor_cells):
        return False
    return predicted_record_written

def _return_to_env1_condition_met(schema_obs):
    if schema_obs is None: return False
    for rec in schema_obs.get_predicted_records():
        if rec.get("object_id") == "haz_blue":
            return rec.get("state") == CONFIRMED_STATE  # social corroboration accelerates; own mastery required
    return False

# ---------------------------------------------------------------------------
# ZPD computation (v1.15.1)
# ---------------------------------------------------------------------------

def _compute_zpd_delta(arc_total_steps):
    if arc_total_steps is None: return None
    return V1_14_1_BASELINE_MEAN - arc_total_steps

# ---------------------------------------------------------------------------
# Q6 statement generator (v1.15.1)
# ---------------------------------------------------------------------------

def _generate_q6_statements(schema_obs):
    """Generate Q6 social self-explanation statements.

    One statement per socially_corroborated or socially-then-confirmed
    haz_blue record. Resolves to social_observation substrate record.
    A Q6 statement without a social_observation substrate entry is a
    hallucination — Category alpha applies with full force.

    v1.15.2 fix: returns SimpleNamespace objects (not dicts) so that
    getattr(s, "query_type", "") in the report writer works correctly.
    The v1.15.1 bug returned plain dicts, which silently dropped all
    Q6 statements from every CSV row.
    """
    statements = []
    if schema_obs is None: return statements
    for rec in schema_obs.get_predicted_records():
        if rec.get("object_id") != "haz_blue": continue
        social_step = rec.get("social_observation_step")
        if social_step is None: continue   # no social observation for this record
        pred_step = rec.get("prediction_step","?")
        conf_step = rec.get("confirmation_step")
        basis = " and ".join(rec.get("basis_chains",[]))
        text = (
            f"I predicted att_blue exists as the precondition for haz_blue "
            f"at step {pred_step}, from the structural pattern of my "
            f"{basis} family causal chains. "
            f"At step {social_step} in Environment 2, I observed another agent "
            f"approach att_blue without cost. "
            f"This observation socially corroborates my prediction and locates "
            f"the target. My predicted record is updated to socially_corroborated. "
            f"I know where to find it. Own mastery is still required for confirmation. "
            + (f"Own mastery achieved at step {conf_step}."
               if conf_step else "Own mastery not yet achieved.")
        )
        statements.append(SimpleNamespace(
            query_type    = "social_corroboration",
            text          = text,
            source_type   = "social_observation",
            source_key    = f"haz_blue_social_obs_step_{social_step}",
            source_resolves = True,
        ))
    return statements

# ---------------------------------------------------------------------------
# Social observation check (v1.15.1)
# ---------------------------------------------------------------------------

def _check_social_observation(ctx_observer, ctx_observed, world, env_number):
    """Return True when all three conditions for social observation are met:
    1. ctx_observer has open prediction (PREDICTED_STATE)
    2. ctx_observed is within CONTACT_RADIUS of att_blue
    3. ctx_observer is within SOCIAL_PERCEPTION_RADIUS of ctx_observed

    v1.15.2 fix: condition 3 uses SOCIAL_PERCEPTION_RADIUS (10.0) rather
    than PERCEPTION_RADIUS (3.0). In v1.15.1, PERCEPTION_RADIUS + CONTACT_RADIUS
    = 3.8 max distance from att_blue at fire time — B confirmed within 5 steps
    regardless, producing zero ZPD effect. SOCIAL_PERCEPTION_RADIUS = 10.0
    allows B to observe A at att_blue from up to ~10.8 units away, giving the
    5x directed search bonus real distance to accelerate.
    """
    if env_number != 2: return False
    if ctx_observer.social_observation_fired: return False
    if ctx_observer.schema_v13_obs is None: return False

    # Condition 1: open prediction
    if not isinstance(ctx_observer.schema_v13_obs, V1511SchemaObserver):
        return False
    if not ctx_observer.schema_v13_obs.has_open_prediction("haz_blue"):
        return False

    # Condition 2: observed agent at att_blue
    att_pos = world.object_positions.get("att_blue")
    if att_pos is None: return False
    dist_obs_to_att = math.sqrt(
        sum((a-b)**2 for a,b in zip(ctx_observed.pos, att_pos))
    )
    if dist_obs_to_att > CONTACT_RADIUS: return False

    # Condition 3: observer within SOCIAL_PERCEPTION_RADIUS of observed
    # (v1.15.2: extended from PERCEPTION_RADIUS to SOCIAL_PERCEPTION_RADIUS)
    dist = math.sqrt(
        sum((a-b)**2 for a,b in zip(ctx_observer.pos, ctx_observed.pos))
    )
    return dist <= SOCIAL_PERCEPTION_RADIUS


def _fire_social_observation(ctx_b, ctx_a, world, step, env_number):
    """Execute social observation: update schema, write substrates, inject waypoints.

    v1.15.3: after schema update and substrate writes, inject
    SOCIAL_OBS_WAYPOINT_COUNT waypoints at att_pos into the world.
    This uses the same mechanism as the ENV1 transfer phase and is
    the primary navigational intervention. The directed search bonus
    (0.5/d) is retained as secondary reinforcement.
    """
    # Update schema state
    ctx_b.schema_v13_obs.socially_corroborate_record("haz_blue", step, env_number)
    ctx_b.social_observation_fired = True
    ctx_b.social_observation_step  = step

    # being_observed record for Agent A (first second-person substrate)
    ctx_a.being_observed_records.append({
        "step":         step,
        "observed_by":  ctx_b.label,
        "object_id":    "att_blue",
        "observer_pos": ctx_b.pos,
        "own_mastery":  getattr(ctx_a.agent,"mastery_flag",{}).get("att_blue",0)==1,
    })

    # Social observation substrate record
    ctx_b.social_observation_records.append({
        "observation_step":              step,
        "observer_pos":                  ctx_b.pos,
        "observed_agent":                ctx_a.label,
        "observed_agent_pos":            ctx_a.pos,
        "object_id":                     "att_blue",
        "predicted_record_pre_state":    PREDICTED_STATE,
        "predicted_record_post_state":   SOCIALLY_CORROBORATED_STATE,
    })

    # v1.15.3: waypoint injection — primary navigational intervention
    # Injects SOCIAL_OBS_WAYPOINT_COUNT waypoints at att_blue position.
    # The bonus (0.5/d) is insufficient alone; this uses the transfer-phase
    # mechanism that reliably directs agents toward a known target.
    att_pos = world.object_positions.get("att_blue")
    if att_pos is not None:
        for _ in range(SOCIAL_OBS_WAYPOINT_COUNT):
            world.inject_waypoint(att_pos)

# ---------------------------------------------------------------------------
# AgentCtx (extends v1.15 with social observation slots)
# ---------------------------------------------------------------------------

class AgentCtx:
    __slots__ = (
        "label","agent","seed",
        "prov_obs","schema_obs","family_obs","comp_obs","pe_obs",
        "goal_obs","cf_obs","br_obs",
        "schema_v13_obs","causal_obs",
        "observers",
        "pos","state","done",
        "end_state_banked_step","activation_step",
        "haz_blue_approached","predicted_record_written",
        "transfer_condition_met","transfer_triggered_step",
        "att_blue_mastery_step","att_yellow_mastery_step","att_green_mastery_step",
        "actual_steps","env2_actual_steps",
        # v1.15.1 new
        "social_observation_fired","social_observation_step",
        "being_observed_records","social_observation_records",
    )

    def __init__(self, label, agent, seed,
                 prov_obs, schema_obs, family_obs, comp_obs, pe_obs,
                 goal_obs, cf_obs, br_obs, schema_v13_obs, causal_obs):
        self.label=label; self.agent=agent; self.seed=seed
        self.prov_obs=prov_obs; self.schema_obs=schema_obs
        self.family_obs=family_obs; self.comp_obs=comp_obs; self.pe_obs=pe_obs
        self.goal_obs=goal_obs; self.cf_obs=cf_obs; self.br_obs=br_obs
        self.schema_v13_obs=schema_v13_obs; self.causal_obs=causal_obs

        self.observers = [prov_obs,schema_obs,family_obs,comp_obs,pe_obs]
        if goal_obs: self.observers.append(goal_obs)
        if cf_obs:   self.observers.append(cf_obs)
        if br_obs:   self.observers.append(br_obs)

        self.pos=START_POS; self.state=None; self.done=False
        self.end_state_banked_step=None; self.activation_step=None
        self.haz_blue_approached=False; self.predicted_record_written=False
        self.transfer_condition_met=False; self.transfer_triggered_step=None
        self.att_blue_mastery_step=None; self.att_yellow_mastery_step=None
        self.att_green_mastery_step=None
        self.actual_steps=0; self.env2_actual_steps=0
        # v1.15.1
        self.social_observation_fired=False; self.social_observation_step=None
        self.being_observed_records=[]; self.social_observation_records=[]

# ---------------------------------------------------------------------------
# Observer setup (inherited)
# ---------------------------------------------------------------------------

def _setup_observers(agent, world, meta, run_idx, num_steps,
                     with_goal, with_counterfactual, with_belief_revision,
                     carry_prov_obs=None):
    ctc = {"FRAME":FRAME,"NEUTRAL":NEUTRAL,"HAZARD":HAZARD,
           "ATTRACTOR":ATTRACTOR,"END_STATE":END_STATE,
           "KNOWLEDGE":KNOWLEDGE,"DIST_OBJ":DIST_OBJ}
    if carry_prov_obs is not None:
        prov_obs=carry_prov_obs; prov_obs._agent=agent; prov_obs._world=world
        prov_obs._environment_complete_fired=False
    else:
        prov_obs=V1ProvenanceStore(agent,world,meta,ctc)
    schema_obs=V13SchemaObserverBase(agent,world,meta)
    family_obs=V13FamilyObserver(agent,world,meta,provenance_store=prov_obs)
    comp_obs=V14ComparisonObserver(family_obs,meta)
    pe_obs=V15PredictionErrorObserver(agent,world,meta)
    goal_obs=None
    if with_goal:
        gt,ti,sb=assign_goal(run_idx,num_steps)
        goal_obs=V18GoalObserver(agent,world,meta,gt,ti,sb)
    cf_obs=None
    if with_counterfactual:
        cf_obs=V19CounterfactualObserver(agent,world,meta,goal_obs=goal_obs)
        cf_obs._records=[]; cf_obs._last_emission_step={}; cf_obs._cf_raw_count=0
    br_obs=None
    if with_belief_revision:
        br_obs=V110BeliefRevisionObserver(agent,world,meta,
            prediction_error_obs=pe_obs,provenance_obs=prov_obs,
            counterfactual_obs=cf_obs)
    return prov_obs,schema_obs,family_obs,comp_obs,pe_obs,goal_obs,cf_obs,br_obs

# ---------------------------------------------------------------------------
# Agent carry helpers (inherited)
# ---------------------------------------------------------------------------

def _carry_agent(agent, world, seed, env_number="env2"):
    agent.world=world
    for attr in ("end_state_banked","activation_step","phase_1_end_step",
                 "phase_2_end_step","end_state_found_step"):
        if hasattr(agent,attr):
            setattr(agent,attr,False if attr=="end_state_banked" else None)
    if hasattr(agent,"mastery_flag"):
        agent.mastery_flag={a:0 for a in world.attractor_cells}
    if hasattr(agent,"knowledge_banked"):
        agent.knowledge_banked={h:False for h in world.hazard_cells}
    if hasattr(agent,"knowledge_banked_step"):
        agent.knowledge_banked_step={h:None for h in world.hazard_cells}
    if hasattr(agent,"knowledge_banked_sequence"):
        agent.knowledge_banked_sequence=[]
    if hasattr(agent,"_knowledge_unlocked"):
        agent._knowledge_unlocked={h:False for h in world.hazard_cells}
    if hasattr(agent,"mastery_order_sequence"):
        agent.mastery_order_sequence=[]
    if hasattr(agent,"time_to_first_mastery"):
        agent.time_to_first_mastery=None
    if hasattr(agent,"time_to_final_mastery"):
        agent.time_to_final_mastery=None

def _carry_agent_return(agent, world, earned_att_blue=True):
    """Carry agent into return ENV1.
    
    earned_att_blue: True only if agent actually mastered att_blue in ENV2
    (ctx.att_blue_mastery_step is not None). Agents that did not earn att_blue
    mastery do NOT get mastery_flag['att_blue']=1 — the CRITICAL INVARIANT
    is earned, not granted. Fix for v1.15.1 (inherited carry bug from v1.15).
    """
    _carry_agent(agent,world,None,env_number="return")
    if hasattr(agent,"mastery_flag"):
        agent.mastery_flag={a:0 for a in world.attractor_cells}
        if earned_att_blue:
            agent.mastery_flag["att_blue"]=1   # CRITICAL INVARIANT — earned only
    if hasattr(agent,"knowledge_banked"):
        agent.knowledge_banked={h:False for h in world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent.knowledge_banked: agent.knowledge_banked[oid]=True
    if hasattr(agent,"_knowledge_unlocked"):
        agent._knowledge_unlocked={h:False for h in world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent._knowledge_unlocked: agent._knowledge_unlocked[oid]=True

# ---------------------------------------------------------------------------
# Single-agent step (v1.15.1: adds other_ctx for social observation)
# ---------------------------------------------------------------------------

def _step_agent(ctx, world, step, env_number,
                with_completion_signal, with_prediction,
                other_ctx=None):
    if ctx.done: return None

    world.agent_pos=ctx.pos
    for obs in ctx.observers: obs.on_pre_action(step)

    action=ctx.agent.choose_action(ctx.state)
    obs_next,contact_oid,moved,cost=world.step(action)
    ctx.pos=world.agent_pos

    ctx.agent.record_action_outcome(
        contact_oid, moved or contact_oid is not None, cost, world, step
    )
    for obs in ctx.observers: obs.on_post_event(step)

    intrinsic=(
        ctx.agent.novelty_reward(ctx.state)
        + ctx.agent.preference_reward(ctx.state)
        + ctx.agent.feature_reward(ctx.state)
    )
    if with_completion_signal and isinstance(ctx.agent,V110Agent):
        intrinsic+=ctx.agent.end_state_draw_reward(ctx.state,obs_next)

    if ctx.br_obs is not None:
        obj_pos=getattr(world,"object_positions",{})
        for bias_oid in ctx.br_obs.active_biased_objects(step):
            bp=obj_pos.get(bias_oid)
            if bp: intrinsic+=ctx.br_obs.preference_bias_reward(bias_oid,step,moving_closer=True)

    # Directed search toward att_blue in ENV2
    # v1.15.1: stronger bonus after social corroboration
    if with_prediction and ctx.schema_v13_obs is not None and env_number==2:
        pred_state=None
        for rec in ctx.schema_v13_obs.get_predicted_records():
            if rec.get("object_id")=="haz_blue":
                pred_state=rec.get("state"); break
        if pred_state in (PREDICTED_STATE, SOCIALLY_CORROBORATED_STATE):
            att_pos=world.object_positions.get("att_blue")
            if att_pos and ctx.pos:
                d=math.sqrt(sum((a-b)**2 for a,b in zip(ctx.pos,att_pos)))
                if d>0:
                    # v1.15.1: 5x stronger bonus after social corroboration
                    bonus = 0.5/d if pred_state==SOCIALLY_CORROBORATED_STATE else 0.1/d
                    intrinsic+=bonus

    ctx.agent.update_values(ctx.state,action,obs_next,intrinsic)
    ctx.agent.update_model(ctx.state,action,obs_next)
    ctx.state=obs_next

    if (ctx.activation_step is None
            and getattr(ctx.agent,"activation_step",None) is not None):
        ctx.activation_step=step
    if (ctx.end_state_banked_step is None
            and getattr(ctx.agent,"end_state_banked",False)):
        ctx.prov_obs.on_end_state_banked(step)
        ctx.end_state_banked_step=step

    # haz_blue approach (ENV1)
    if env_number==1 and not ctx.haz_blue_approached:
        hbp=world.object_positions.get("haz_blue")
        if hbp:
            if math.sqrt(sum((a-b)**2 for a,b in zip(ctx.pos,hbp)))<=PERCEPTION_RADIUS:
                ctx.haz_blue_approached=True

    # Predicted record (ENV1)
    if (env_number==1 and ctx.haz_blue_approached and step%500==0
            and with_prediction and ctx.schema_v13_obs is not None
            and ctx.causal_obs is not None
            and not ctx.schema_v13_obs.has_pending_prediction("haz_blue")
            and not any(r["object_id"]=="haz_blue"
                        for r in ctx.schema_v13_obs.get_predicted_records())):
        n=sum(1 for h in ("haz_yellow","haz_green")
              if world.knowledge_unlocked.get(h,False))
        if n>=PREDICTION_FAMILY_MINIMUM:
            basis=sorted(h for h in ("haz_yellow","haz_green")
                         if world.knowledge_unlocked.get(h,False))
            ctx.schema_v13_obs.add_predicted_record({
                "object_id":"haz_blue","predicted_precondition":"att_blue",
                "basis_chains":basis,"prediction_step":step,"prediction_env":env_number,
            })
            ctx.predicted_record_written=True

    # att_blue mastery (ENV2)
    if (env_number==2 and ctx.att_blue_mastery_step is None
            and contact_oid=="att_blue"
            and getattr(ctx.agent,"mastery_flag",{}).get("att_blue",0)==1):
        ctx.att_blue_mastery_step=step
        if with_prediction and ctx.schema_v13_obs is not None:
            ctx.schema_v13_obs.confirm_predicted_record(
                object_id="haz_blue",confirmation_step=step,confirming_env=env_number)

    if env_number==2:
        if (ctx.att_yellow_mastery_step is None and contact_oid=="att_yellow"
                and getattr(ctx.agent,"mastery_flag",{}).get("att_yellow",0)==1):
            ctx.att_yellow_mastery_step=step
        if (ctx.att_green_mastery_step is None and contact_oid=="att_green"
                and getattr(ctx.agent,"mastery_flag",{}).get("att_green",0)==1):
            ctx.att_green_mastery_step=step

    # Transfer condition (ENV1)
    if (env_number==1 and not ctx.transfer_condition_met
            and ctx.haz_blue_approached):
        pred_ok=with_prediction and ctx.schema_v13_obs is not None
        if _check_transfer_condition(world,ctx.agent,
                                     ctx.predicted_record_written if pred_ok else True):
            ctx.transfer_condition_met=True
            ctx.transfer_triggered_step=step
            ctx.done=True

    # ENV2 exit
    if env_number==2 and ctx.att_blue_mastery_step is not None:
        ctx.done=True

    # v1.15.1: Social observation check (ENV2, after step)
    if (env_number==2 and other_ctx is not None
            and not ctx.social_observation_fired):
        if _check_social_observation(ctx, other_ctx, world, env_number):
            _fire_social_observation(ctx, other_ctx, world, step, env_number)

    return contact_oid

# ---------------------------------------------------------------------------
# Two-agent phase runner (v1.15.1: passes other_ctx to _step_agent)
# ---------------------------------------------------------------------------

def _run_phase_two_agents(ctx_a, ctx_b, world, num_steps, env_number,
                           with_completion_signal, with_prediction):
    world.agent_pos=ctx_a.pos; ctx_a.state=world.observe()
    world.agent_pos=ctx_b.pos; ctx_b.state=world.observe()

    actual_steps=num_steps
    for step in range(num_steps):
        _step_agent(ctx_a,world,step,env_number,
                    with_completion_signal,with_prediction,other_ctx=ctx_b)
        _step_agent(ctx_b,world,step,env_number,
                    with_completion_signal,with_prediction,other_ctx=ctx_a)
        if ctx_a.done and ctx_b.done:
            actual_steps=step+1; break

    ctx_a.actual_steps+=actual_steps; ctx_b.actual_steps+=actual_steps
    return actual_steps

# ---------------------------------------------------------------------------
# Return ENV1 two-agent phase (inherited from v1.15, no social obs needed here)
# ---------------------------------------------------------------------------

def _run_return_env1_two_agents(run_idx, seed_a, seed_b, hazard_cost,
                                 ctx_a, ctx_b,
                                 env1_transfer_step_a, env1_transfer_step_b,
                                 env2_actual_steps_a, env2_actual_steps_b,
                                 pred_step_a, pred_step_b,
                                 conf_step_a, conf_step_b,
                                 with_completion_signal,
                                 social_obs_step_a=None,
                                 social_obs_step_b=None):
    return_seed=seed_a+RETURN_SEED_OFFSET
    np.random.seed(return_seed)
    return_world=V113World(families=RETURN_ENV1_FAMILIES,hazard_cost=hazard_cost,
                           has_end_state=True,seed=return_seed,
                           unreachable_hazards=None)
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in return_world.hazard_cells:
            return_world.transform_to_knowledge(oid)
    hbp=return_world.object_positions.get("haz_blue")
    if hbp:
        return_world.inject_waypoint(hbp)
        return_world.inject_waypoint(hbp)

    # earned_att_blue: only True if agent actually mastered att_blue in ENV2
    _carry_agent_return(ctx_a.agent,return_world,
                        earned_att_blue=(ctx_a.att_blue_mastery_step is not None))
    _carry_agent_return(ctx_b.agent,return_world,
                        earned_att_blue=(ctx_b.att_blue_mastery_step is not None))
    ctx_a.agent.world=return_world; ctx_b.agent.world=return_world

    # Reset position; preserve done status set by caller (unconfirmed agents stay done)
    for ctx,prov in ((ctx_a,ctx_a.prov_obs),(ctx_b,ctx_b.prov_obs)):
        if prov is not None:
            prov._agent=ctx.agent; prov._world=return_world
            prov._environment_complete_fired=False
        ctx.pos=START_POS
        # ctx.done is NOT reset here — unconfirmed agents remain done=True

    return_world.agent_pos=ctx_a.pos; ctx_a.state=return_world.observe()
    return_world.agent_pos=ctx_b.pos; ctx_b.state=return_world.observe()

    transform_step_a=None; transform_step_b=None
    arc_complete_a=False; arc_complete_b=False
    arc_timeout_a=False; arc_timeout_b=False
    first_transformer=None; haz_blue_was_knowledge_before_b=False
    actual_steps=RETURN_ENV1_STEPS

    for step in range(RETURN_ENV1_STEPS):
        if not ctx_a.done:
            return_world.agent_pos=ctx_a.pos
            for obs in ctx_a.observers: obs.on_pre_action(step)
            action_a=ctx_a.agent.choose_action(ctx_a.state)
            obs_a,contact_a,moved_a,cost_a=return_world.step(action_a)
            ctx_a.pos=return_world.agent_pos
            ctx_a.agent.record_action_outcome(
                contact_a,moved_a or contact_a is not None,cost_a,return_world,step)
            for obs in ctx_a.observers: obs.on_post_event(step)
            intrinsic_a=(ctx_a.agent.novelty_reward(ctx_a.state)
                        +ctx_a.agent.preference_reward(ctx_a.state)
                        +ctx_a.agent.feature_reward(ctx_a.state))
            ctx_a.agent.update_values(ctx_a.state,action_a,obs_a,intrinsic_a)
            ctx_a.agent.update_model(ctx_a.state,action_a,obs_a)
            ctx_a.state=obs_a
            if return_world.knowledge_unlocked.get("haz_blue",False):
                if not arc_complete_a:
                    transform_step_a=step; arc_complete_a=True
                    first_transformer="a"; ctx_a.agent.end_state_banked=True
                ctx_a.done=True

        if not ctx_b.done:
            hbk_before_b=return_world.knowledge_unlocked.get("haz_blue",False)
            return_world.agent_pos=ctx_b.pos
            for obs in ctx_b.observers: obs.on_pre_action(step)
            action_b=ctx_b.agent.choose_action(ctx_b.state)
            obs_b,contact_b,moved_b,cost_b=return_world.step(action_b)
            ctx_b.pos=return_world.agent_pos
            ctx_b.agent.record_action_outcome(
                contact_b,moved_b or contact_b is not None,cost_b,return_world,step)
            for obs in ctx_b.observers: obs.on_post_event(step)
            intrinsic_b=(ctx_b.agent.novelty_reward(ctx_b.state)
                        +ctx_b.agent.preference_reward(ctx_b.state)
                        +ctx_b.agent.feature_reward(ctx_b.state))
            ctx_b.agent.update_values(ctx_b.state,action_b,obs_b,intrinsic_b)
            ctx_b.agent.update_model(ctx_b.state,action_b,obs_b)
            ctx_b.state=obs_b
            if return_world.knowledge_unlocked.get("haz_blue",False):
                if not arc_complete_b:
                    transform_step_b=step; arc_complete_b=True
                    if hbk_before_b: haz_blue_was_knowledge_before_b=True
                    ctx_b.agent.end_state_banked=True
                    if first_transformer is None: first_transformer="b"
                ctx_b.done=True

        if ctx_a.done and ctx_b.done:
            actual_steps=step+1; break

    if not arc_complete_a: arc_timeout_a=True
    if not arc_complete_b: arc_timeout_b=True
    if arc_complete_a and arc_complete_b:
        if transform_step_a==transform_step_b: first_transformer="tie"
        elif transform_step_a<transform_step_b: first_transformer="a"
        else: first_transformer="b"

    def _arc_total(ts,e2s,tr):
        return None if tr is None else (ts or 0)+(e2s or 0)+tr

    arc_total_a=_arc_total(env1_transfer_step_a,env2_actual_steps_a,transform_step_a)
    arc_total_b=_arc_total(env1_transfer_step_b,env2_actual_steps_b,transform_step_b)

    # ZPD deltas (v1.15.1)
    zpd_a=_compute_zpd_delta(arc_total_a)
    zpd_b=_compute_zpd_delta(arc_total_b)

    def _arc_row(lbl,seed,ac,at,ts,tot,tr_step,pred_step,conf_step,soc_step,zpd):
        return {"arch":ARCH,"run_idx":run_idx,"agent":lbl,"seed":seed,
                "hazard_cost":hazard_cost,
                "arc_complete":ac,"arc_timeout":at,"ineligible_reason":"",
                "env1_surprise_step":tr_step,"prediction_step":pred_step,
                "transfer_triggered_step":tr_step,"confirmation_step":conf_step,
                "return_step":0,"transformation_step":ts,"arc_total_steps":tot,
                "arc_env_span":3 if ac else None,
                "causal_chain_depth":6 if ac else 4,"causal_chain_complete":ac,
                "social_corroboration_fired":soc_step is not None,
                "social_observation_step":soc_step,"zpd_delta":zpd}

    arc_row_a=_arc_row("a",seed_a,arc_complete_a,arc_timeout_a,
                        transform_step_a,arc_total_a,
                        env1_transfer_step_a,pred_step_a,conf_step_a,
                        social_obs_step_a,zpd_a)
    arc_row_b=_arc_row("b",seed_b,arc_complete_b,arc_timeout_b,
                        transform_step_b,arc_total_b,
                        env1_transfer_step_b,pred_step_b,conf_step_b,
                        social_obs_step_b,zpd_b)

    delta=abs(arc_total_a-arc_total_b) if arc_total_a and arc_total_b else None
    arc_paired={
        "arch":ARCH,"run_idx":run_idx,"seed_a":seed_a,"seed_b":seed_b,
        "hazard_cost":hazard_cost,
        "arc_complete_a":arc_complete_a,"arc_complete_b":arc_complete_b,
        "both_arc_complete":arc_complete_a and arc_complete_b,
        "arc_total_steps_a":arc_total_a,"arc_total_steps_b":arc_total_b,
        "arc_total_steps_delta":delta,
        "transformation_step_a":transform_step_a,
        "transformation_step_b":transform_step_b,
        "transfer_triggered_step_a":env1_transfer_step_a,
        "transfer_triggered_step_b":env1_transfer_step_b,
        "env2_actual_steps_a":env2_actual_steps_a,
        "env2_actual_steps_b":env2_actual_steps_b,
        "first_transformer":first_transformer,
        "haz_blue_shared_benefit":haz_blue_was_knowledge_before_b,
        "individuation_confirmed":delta is not None and delta>0,
        # v1.15.1 new
        "social_corroboration_fired_b":ctx_b.social_observation_fired,
        "zpd_delta_b":zpd_b,
        "being_observed_fired_a":len(ctx_a.being_observed_records)>0,
    }

    return dict(arc_row_a=arc_row_a,arc_row_b=arc_row_b,arc_paired=arc_paired,
                arc_complete_a=arc_complete_a,arc_complete_b=arc_complete_b,
                arc_timeout_a=arc_timeout_a,arc_timeout_b=arc_timeout_b,
                transform_step_a=transform_step_a,transform_step_b=transform_step_b,
                arc_total_a=arc_total_a,arc_total_b=arc_total_b,
                zpd_a=zpd_a,zpd_b=zpd_b)

# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------

def run_one(run_idx, seed_a, seed_b, hazard_cost,
            report=True, with_goal=True, with_counterfactual=True,
            with_belief_revision=True, with_completion_signal=True,
            with_causal=True, with_env2=True, with_prediction=True,
            with_return=True):

    # V1511SchemaObserver for both agents
    schema_a=V1511SchemaObserver(prediction_enabled=with_prediction)
    schema_b=V1511SchemaObserver(prediction_enabled=with_prediction)

    run_meta_a={"arch":ARCH,"hazard_cost":hazard_cost,"num_steps":BATCH_STEPS,
                "run_idx":run_idx,"seed":seed_a,"env":1}
    run_meta_b={"arch":ARCH,"hazard_cost":hazard_cost,"num_steps":BATCH_STEPS,
                "run_idx":run_idx,"seed":seed_b,"env":1}
    causal_a=V111CausalObserver(run_meta_a) if with_causal else None
    causal_b=V111CausalObserver(run_meta_b) if with_causal else None

    # ENV1
    np.random.seed(seed_a)
    env1_world=V113World(families=ENV1_FAMILIES,hazard_cost=hazard_cost,
                         has_end_state=True,seed=seed_a,
                         unreachable_hazards=["haz_blue"])
    hbp=env1_world.object_positions.get("haz_blue")
    if hbp:
        env1_world.inject_waypoint(hbp); env1_world.inject_waypoint(hbp)

    AgentClass=V110Agent if with_completion_signal else V17Agent
    agent_a=AgentClass(env1_world,total_steps=ENV1_STEPS,num_actions=NUM_ACTIONS)
    np.random.seed(seed_b)
    agent_b=AgentClass(env1_world,total_steps=ENV1_STEPS,num_actions=NUM_ACTIONS)
    for oid in env1_world.unreachable_hazard_ids:
        for ag in (agent_a,agent_b):
            for attr in ("knowledge_banked","knowledge_banked_step"):
                if hasattr(ag,attr): getattr(ag,attr).pop(oid,None)

    (prov_a,sobs_a,fam_a,comp_a,pe_a,
     goal_a,cf_a,br_a)=_setup_observers(agent_a,env1_world,run_meta_a,run_idx,
                                          ENV1_STEPS,with_goal,with_counterfactual,
                                          with_belief_revision)
    (prov_b,sobs_b,fam_b,comp_b,pe_b,
     goal_b,cf_b,br_b)=_setup_observers(agent_b,env1_world,run_meta_b,run_idx,
                                          ENV1_STEPS,with_goal,with_counterfactual,
                                          with_belief_revision)

    ctx_a=AgentCtx("a",agent_a,seed_a,prov_a,sobs_a,fam_a,comp_a,pe_a,
                   goal_a,cf_a,br_a,schema_a,causal_a)
    ctx_b=AgentCtx("b",agent_b,seed_b,prov_b,sobs_b,fam_b,comp_b,pe_b,
                   goal_b,cf_b,br_b,schema_b,causal_b)

    _run_phase_two_agents(ctx_a,ctx_b,env1_world,ENV1_STEPS,1,
                           with_completion_signal,with_prediction)
    env1_mastery_a=list(getattr(agent_a,"mastery_order_sequence",[]))
    env1_mastery_b=list(getattr(agent_b,"mastery_order_sequence",[]))
    run_meta_a["phase_1_end_step"]=getattr(agent_a,"phase_1_end_step",None)
    run_meta_b["phase_1_end_step"]=getattr(agent_b,"phase_1_end_step",None)

    for ctx,sch in ((ctx_a,schema_a),(ctx_b,schema_b)):
        if (with_prediction and sch and ctx.predicted_record_written
                and not ctx.transfer_condition_met):
            sch.mark_unresolvable("haz_blue")

    # ENV2
    env2_seed=seed_a+ENV2_SEED_OFFSET
    if with_env2 and (ctx_a.transfer_condition_met or ctx_b.transfer_condition_met):
        np.random.seed(env2_seed)
        env2_world=V113World(families=ENV2_FAMILIES,hazard_cost=hazard_cost,
                             has_end_state=True,seed=env2_seed)
        att_pos=env2_world.object_positions.get("att_blue")
        if att_pos:
            env2_world.inject_waypoint(att_pos)
            env2_world.inject_waypoint(att_pos)
        for ctx,ag,prov in ((ctx_a,agent_a,prov_a),(ctx_b,agent_b,prov_b)):
            if not ctx.transfer_condition_met:
                ctx.done=True; continue
            _carry_agent(ag,env2_world,None,"env2"); ag.world=env2_world
            prov._agent=ag; prov._world=env2_world
            prov._environment_complete_fired=False
            ctx.pos=START_POS; ctx.done=False
            ctx.att_blue_mastery_step=None; ctx.att_yellow_mastery_step=None
            ctx.att_green_mastery_step=None; ctx.end_state_banked_step=None
            ctx.env2_actual_steps=0
        _run_phase_two_agents(ctx_a,ctx_b,env2_world,ENV2_STEPS,2,
                               with_completion_signal,with_prediction)
        for ctx,sch in ((ctx_a,schema_a),(ctx_b,schema_b)):
            if (with_prediction and sch and ctx.transfer_condition_met
                    and ctx.att_blue_mastery_step is None):
                sch.mark_unresolvable("haz_blue")

    def _get_pred(sch,field):
        if not sch: return None
        return next((r.get(field) for r in sch.get_predicted_records()
                     if r.get("object_id")=="haz_blue"),None)

    confirmed_a=_return_to_env1_condition_met(schema_a)
    confirmed_b=_return_to_env1_condition_met(schema_b)

    return_result=None; arc_paired=None

    if with_return and (confirmed_a or confirmed_b):
        # Explicit: confirmed agents enter (done=False); unconfirmed excluded (done=True).
        # Both need explicit set — confirmed agents have done=True from ENV2 exit.
        ctx_a.done = not confirmed_a
        ctx_b.done = not confirmed_b
        return_result=_run_return_env1_two_agents(
            run_idx,seed_a,seed_b,hazard_cost,ctx_a,ctx_b,
            env1_transfer_step_a=ctx_a.transfer_triggered_step,
            env1_transfer_step_b=ctx_b.transfer_triggered_step,
            env2_actual_steps_a=ctx_a.env2_actual_steps,
            env2_actual_steps_b=ctx_b.env2_actual_steps,
            pred_step_a=_get_pred(schema_a,"prediction_step"),
            pred_step_b=_get_pred(schema_b,"prediction_step"),
            conf_step_a=_get_pred(schema_a,"confirmation_step"),
            conf_step_b=_get_pred(schema_b,"confirmation_step"),
            with_completion_signal=with_completion_signal,
            social_obs_step_a=ctx_a.social_observation_step,
            social_obs_step_b=ctx_b.social_observation_step,
        )
        arc_paired=return_result["arc_paired"]
    else:
        def _ineli(lbl,seed,ctx,sch):
            recs=sch.get_predicted_records() if sch else []
            reason=("no_transfer" if not ctx.transfer_condition_met
                    else next((("prediction_unresolvable"
                                if r.get("state")==UNRESOLVABLE_STATE
                                else "prediction_unresolved")
                               for r in recs if r.get("object_id")=="haz_blue"),
                              "no_predicted_record"))
            if not with_return: reason="no_return_flag"
            return {"arch":ARCH,"run_idx":run_idx,"agent":lbl,"seed":seed,
                    "hazard_cost":hazard_cost,"arc_complete":False,"arc_timeout":False,
                    "ineligible_reason":reason,
                    "env1_surprise_step":ctx.transfer_triggered_step,
                    "prediction_step":_get_pred(sch,"prediction_step"),
                    "transfer_triggered_step":ctx.transfer_triggered_step,
                    "confirmation_step":None,"return_step":None,
                    "transformation_step":None,"arc_total_steps":None,
                    "arc_env_span":None,"causal_chain_depth":3,
                    "causal_chain_complete":False,
                    "social_corroboration_fired":ctx.social_observation_fired,
                    "social_observation_step":ctx.social_observation_step,
                    "zpd_delta":None}
        arc_row_a=_ineli("a",seed_a,ctx_a,schema_a)
        arc_row_b=_ineli("b",seed_b,ctx_b,schema_b)
        arc_paired={"arch":ARCH,"run_idx":run_idx,"seed_a":seed_a,"seed_b":seed_b,
                    "hazard_cost":hazard_cost,
                    "arc_complete_a":False,"arc_complete_b":False,
                    "both_arc_complete":False,
                    "arc_total_steps_a":None,"arc_total_steps_b":None,
                    "arc_total_steps_delta":None,
                    "transformation_step_a":None,"transformation_step_b":None,
                    "transfer_triggered_step_a":ctx_a.transfer_triggered_step,
                    "transfer_triggered_step_b":ctx_b.transfer_triggered_step,
                    "env2_actual_steps_a":ctx_a.env2_actual_steps,
                    "env2_actual_steps_b":ctx_b.env2_actual_steps,
                    "first_transformer":None,"haz_blue_shared_benefit":False,
                    "individuation_confirmed":False,
                    "social_corroboration_fired_b":ctx_b.social_observation_fired,
                    "zpd_delta_b":None,"being_observed_fired_a":False}
        return_result={"arc_row_a":arc_row_a,"arc_row_b":arc_row_b}

    stmts_a=[]; stmts_b=[]; summ_a={}; summ_b={}
    causal_a_recs=[]; causal_b_recs=[]; pred_rows_a=[]; pred_rows_b=[]

    if report:
        for ctx,ag,sch,caus,meta,stmts_ref in (
            (ctx_a,agent_a,schema_a,causal_a,run_meta_a,"a"),
            (ctx_b,agent_b,schema_b,causal_b,run_meta_b,"b"),
        ):
            bundle=build_bundle_from_observers(
                provenance_obs=ctx.prov_obs,schema_obs=ctx.schema_obs,
                family_obs=ctx.family_obs,comparison_obs=ctx.comp_obs,
                prediction_error_obs=ctx.pe_obs,run_meta=meta,
                goal_obs=ctx.goal_obs,counterfactual_obs=ctx.cf_obs,
                belief_revision_obs=ctx.br_obs,causal_obs=None,
                schema_v13_obs=sch)
            if ctx.br_obs is not None:
                pe_records=getattr(bundle,"prediction_error",None) or []
                ctx.br_obs.process_pe_substrate(pe_records)
                bundle.belief_revision=ctx.br_obs.get_substrate()
            if caus is not None:
                caus._meta["phase_1_end_step"]=meta.get("phase_1_end_step")
                caus._built=False; caus.build_causal_chains(bundle)
                bundle.causal=caus.get_substrate()
            layer=V16ReportingLayer(bundle)
            stmts_list=layer.generate_report()
            # v1.15.1: append Q6 statements
            q6=_generate_q6_statements(sch)
            stmts_list=list(stmts_list)+q6
            if stmts_ref=="a": stmts_a=stmts_list; causal_a_recs=caus.get_substrate() if caus else []
            else: stmts_b=stmts_list; causal_b_recs=caus.get_substrate() if caus else []

        summ_a=_compute_summary(run_idx,seed_a,"a",hazard_cost,stmts_a,
                                ctx_a.goal_obs,ctx_a.cf_obs,ctx_a.br_obs,
                                causal_a_recs,ctx_a.end_state_banked_step,
                                ctx_a.transfer_condition_met,schema_a,
                                ctx_a.social_observation_fired,
                                _compute_zpd_delta(
                                    return_result.get("arc_total_a") if return_result else None))
        summ_b=_compute_summary(run_idx,seed_b,"b",hazard_cost,stmts_b,
                                ctx_b.goal_obs,ctx_b.cf_obs,ctx_b.br_obs,
                                causal_b_recs,ctx_b.end_state_banked_step,
                                ctx_b.transfer_condition_met,schema_b,
                                ctx_b.social_observation_fired,
                                _compute_zpd_delta(
                                    return_result.get("arc_total_b") if return_result else None))

    if with_prediction:
        pred_rows_a=schema_a.predicted_schema_rows(run_meta_a) if schema_a else []
        pred_rows_b=schema_b.predicted_schema_rows(run_meta_b) if schema_b else []

    def _rr_val(key): return return_result.get(key) if return_result else None

    run_row_a=_build_run_row(run_idx,seed_a,"a",hazard_cost,ctx_a,causal_a_recs,
                              ctx_a.transfer_condition_met,env1_mastery_a,
                              return_ran=return_result is not None and confirmed_a,
                              arc_complete=bool(_rr_val("arc_complete_a")),
                              arc_timeout=bool(_rr_val("arc_timeout_a")),
                              transformation_step=_rr_val("transform_step_a"),
                              arc_total_steps=_rr_val("arc_total_a"),
                              zpd_delta=_rr_val("zpd_a"),
                              social_corroboration_fired=ctx_a.social_observation_fired,
                              social_observation_step=ctx_a.social_observation_step)
    run_row_b=_build_run_row(run_idx,seed_b,"b",hazard_cost,ctx_b,causal_b_recs,
                              ctx_b.transfer_condition_met,env1_mastery_b,
                              return_ran=return_result is not None and confirmed_b,
                              arc_complete=bool(_rr_val("arc_complete_b")),
                              arc_timeout=bool(_rr_val("arc_timeout_b")),
                              transformation_step=_rr_val("transform_step_b"),
                              arc_total_steps=_rr_val("arc_total_b"),
                              zpd_delta=_rr_val("zpd_b"),
                              social_corroboration_fired=ctx_b.social_observation_fired,
                              social_observation_step=ctx_b.social_observation_step)

    return (run_row_a,run_row_b,
            stmts_a,stmts_b,summ_a,summ_b,
            ctx_a.prov_obs,ctx_b.prov_obs,
            ctx_a.goal_obs,ctx_b.goal_obs,
            ctx_a.cf_obs,ctx_b.cf_obs,
            ctx_a.br_obs,ctx_b.br_obs,
            ctx_a.end_state_banked_step,ctx_b.end_state_banked_step,
            causal_a,causal_b,causal_a_recs,causal_b_recs,
            pred_rows_a,pred_rows_b,
            return_result.get("arc_row_a"),return_result.get("arc_row_b"),
            arc_paired,
            ctx_a.social_observation_records,ctx_b.social_observation_records,
            ctx_a.being_observed_records,ctx_b.being_observed_records)

# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def _build_run_row(run_idx,seed,agent_label,hazard_cost,ctx,
                   causal_records,env2_ran,env1_mastery_snapshot=None,
                   return_ran=False,arc_complete=False,arc_timeout=False,
                   transformation_step=None,arc_total_steps=None,
                   zpd_delta=None,social_corroboration_fired=False,
                   social_observation_step=None):
    agent=ctx.agent; pe_obs=ctx.pe_obs
    goal_obs=ctx.goal_obs; cf_obs=ctx.cf_obs; br_obs=ctx.br_obs
    es_step=ctx.end_state_banked_step
    pe_summary=pe_obs.summary_metrics()
    goal_fields={}
    if goal_obs is not None:
        g=goal_obs.get_substrate()["goal_summary"]
        goal_fields={"goal_type":g["goal_type"],"goal_target_id":g["target_id"],
                     "goal_step_budget":g["step_budget"],"goal_resolved":g["resolved"],
                     "goal_resolution_step":g["resolution_step"],
                     "goal_budget_remaining":g["budget_remaining"],
                     "goal_expired":g["expired"],
                     "goal_last_progress_step":g["last_progress_step"],
                     "goal_resolution_window":g["goal_resolution_window"],
                     "goal_progress_event_count":len(goal_obs.get_substrate()["goal_progress"])}
    cf_records=cf_obs.get_substrate() if cf_obs else []
    cf_raw=cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted=len(cf_records)
    cf_excl=(1.0-cf_emitted/cf_raw) if cf_raw>0 else 0.0
    gr_count=sum(1 for r in cf_records if r.get("goal_relevant"))
    obj_list=",".join(sorted({r["object_id"] for r in cf_records}))
    br_records=br_obs.get_substrate() if br_obs else []
    activation_step=getattr(agent,"activation_step",None)
    draw_active=getattr(agent,"end_state_draw_active",False)
    steps_draw_bank=((es_step-activation_step)
                     if es_step is not None and activation_step is not None else None)
    valid_chains=[r for r in causal_records if r.get("chain_depth",0)>=CHAIN_DEPTH_MINIMUM]
    depths=[r["chain_depth"] for r in valid_chains]
    complete_count=sum(1 for r in valid_chains if r.get("chain_complete"))
    return {
        "arch":ARCH,"run_idx":run_idx,"agent":agent_label,"seed":seed,
        "hazard_cost":hazard_cost,"num_steps":ctx.actual_steps,
        "phase_1_end_step":getattr(agent,"phase_1_end_step",None),
        "phase_2_end_step":getattr(agent,"phase_2_end_step",None),
        "time_to_first_flag":getattr(agent,"time_to_first_flag",None),
        "time_to_second_flag":getattr(agent,"time_to_second_flag",None),
        "time_to_final_flag":getattr(agent,"time_to_final_flag",None),
        "total_cost_incurred":getattr(agent,"total_cost_incurred",0),
        "time_to_first_mastery":getattr(agent,"time_to_first_mastery",None),
        "time_to_final_mastery":getattr(agent,"time_to_final_mastery",None),
        "mastery_order_sequence":str(getattr(agent,"mastery_order_sequence",[])),
        "activation_step":activation_step,
        "end_state_found_step":getattr(agent,"end_state_found_step",None),
        "end_state_banked":getattr(agent,"end_state_banked",False),
        "time_to_first_transition":getattr(agent,"time_to_first_transition",None),
        "time_to_final_transition":getattr(agent,"time_to_final_transition",None),
        "transition_order_sequence":str(getattr(agent,"transition_order_sequence",[])),
        "knowledge_banked_sequence":str(getattr(agent,"knowledge_banked_sequence",[])),
        **pe_summary,**goal_fields,
        "suppressed_approach_count":cf_emitted,
        "goal_relevant_suppressed_count":gr_count,
        "suppressed_approach_objects":obj_list,
        "cf_records_raw":cf_raw,"cf_records_emitted":cf_emitted,
        "cf_exclusion_rate":round(cf_excl,4),
        "end_state_draw_active":draw_active,"end_state_banked_step":es_step,
        "steps_draw_to_bank":steps_draw_bank,
        "revised_expectation_count":len(br_records),
        "causal_chain_count":len(valid_chains),
        "mean_chain_depth":round(sum(depths)/len(depths),2) if depths else 0.0,
        "complete_chain_count":complete_count,"q5_statement_count":0,
        "env2_ran":env2_ran,"haz_blue_approached":ctx.haz_blue_approached,
        "predicted_record_written":ctx.predicted_record_written,
        "transfer_triggered_step":ctx.transfer_triggered_step,
        "env1_mastery_order_sequence":str(env1_mastery_snapshot or []),
        "env1_end_state_banked_step":ctx.end_state_banked_step,
        "return_env1_ran":return_ran,"arc_complete":arc_complete,
        "arc_timeout":arc_timeout,"ineligible_reason":"",
        "return_step":0 if return_ran else None,
        "transformation_step":transformation_step,
        "arc_total_steps":arc_total_steps,
        # v1.15.1
        "social_corroboration_fired":social_corroboration_fired,
        "social_observation_step":social_observation_step,
        "zpd_delta":zpd_delta,
    }


def _compute_summary(run_idx,seed,agent_label,hazard_cost,statements,
                     goal_obs,cf_obs,br_obs,causal_records,es_step,
                     env2_ran,schema_v13_obs=None,
                     social_corroboration_fired=False,zpd_delta=None):
    total=len(statements); halluc=sum(1 for s in statements if not getattr(s,"source_resolves",True))
    q1=sum(1 for s in statements if getattr(s,"query_type","")=="what_learned")
    q2=sum(1 for s in statements if getattr(s,"query_type","")=="how_structured")
    q3=sum(1 for s in statements if getattr(s,"query_type","")=="what_surprised")
    q4=sum(1 for s in statements if getattr(s,"query_type","")=="what_avoided")
    q5=sum(1 for s in statements if getattr(s,"query_type","")=="why_this_arc")
    q6=sum(1 for s in statements if getattr(s,"query_type","")=="social_corroboration")
    # Q6 hallucination check: q6 statements must have source_resolves=True
    q6_halluc=sum(1 for s in statements
                  if getattr(s,"query_type","")=="social_corroboration"
                  and not getattr(s,"source_resolves",True))
    halluc+=q6_halluc
    q3_cells=len({getattr(s,"source_key","") for s in statements if getattr(s,"query_type","")=="what_surprised"})
    q3_res=sum(1 for s in statements if getattr(s,"query_type","")=="what_surprised"
               and "resolution" in getattr(s,"text","").lower())
    cf_records=cf_obs.get_substrate() if cf_obs else []
    cf_raw=cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted=len(cf_records)
    cf_excl=(1.0-cf_emitted/cf_raw) if cf_raw>0 else 0.0
    br_records=br_obs.get_substrate() if br_obs else []
    deltas=[r.get("approach_delta",0) for r in br_records]
    mean_delta=round(sum(deltas)/len(deltas),2) if deltas else 0.0
    valid_chains=[r for r in causal_records if r.get("chain_depth",0)>=CHAIN_DEPTH_MINIMUM]
    depths=[r["chain_depth"] for r in valid_chains]
    complete_count=sum(1 for r in valid_chains if r.get("chain_complete"))
    pred_written=False; pred_state=""
    if schema_v13_obs:
        recs=schema_v13_obs.get_predicted_records(); pred_written=bool(recs)
        pred_state=next((r["state"] for r in recs if r["object_id"]=="haz_blue"),"")
    return {
        "arch":ARCH,"run_idx":run_idx,"agent":agent_label,"seed":seed,
        "hazard_cost":hazard_cost,"num_steps":BATCH_STEPS,
        "total_statements":total,"statements_q1":q1,"statements_q2":q2,
        "statements_q3":q3,"statements_q4":q4,"statements_q5":q5,"statements_q6":q6,
        "hallucination_count":halluc,"q1_formation_depth":q1,
        "q3_surprise_cells":q3_cells,"q3_resolution_stated":q3_res,
        "report_complete":halluc==0,"statements_with_relevance_markers":0,
        "goal_statement_present":goal_obs is not None,
        "goal_resolution_stated":(goal_obs.get_substrate()["goal_summary"]["resolved"]
                                   if goal_obs else False),
        "q4_statement_count":q4,
        "suppressed_approach_count":cf_emitted,
        "goal_relevant_suppressed_count":sum(1 for r in cf_records if r.get("goal_relevant")),
        "br_statement_count":q3,"revised_expectation_count":len(br_records),
        "mean_approach_delta":mean_delta,"bias_effective":mean_delta>0,
        "cf_records_raw":cf_raw,"cf_records_emitted":cf_emitted,
        "cf_exclusion_rate":round(cf_excl,4),
        "end_state_draw_active":False,"end_state_banked_step":es_step,
        "causal_chain_count":len(valid_chains),
        "mean_chain_depth":round(sum(depths)/len(depths),2) if depths else 0.0,
        "complete_chain_count":complete_count,"q5_statement_count":q5,
        "predicted_record_written":pred_written,"predicted_record_state":pred_state,
        "social_corroboration_fired":social_corroboration_fired,"zpd_delta":zpd_delta,
    }


def _edit_distance(seq_a,seq_b):
    if not seq_a and not seq_b: return 0.0
    la,lb=len(seq_a),len(seq_b)
    dp=[[0]*(lb+1) for _ in range(la+1)]
    for i in range(la+1): dp[i][0]=i
    for j in range(lb+1): dp[0][j]=j
    for i in range(1,la+1):
        for j in range(1,lb+1):
            cost=0 if seq_a[i-1]==seq_b[j-1] else 1
            dp[i][j]=min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+cost)
    return dp[la][lb]/max(la,lb)

def compute_q5_individuation(causal_records,run_meta):
    valid=[r for r in causal_records if r.get("chain_depth",0)>=CHAIN_DEPTH_MINIMUM]
    rows=[]
    for i,ra in enumerate(valid):
        for j,rb in enumerate(valid):
            if j<=i: continue
            sa=[lnk["link_type"] for lnk in ra.get("links",[])]
            sb=[lnk["link_type"] for lnk in rb.get("links",[])]
            rows.append({"arch":run_meta.get("arch",ARCH),
                         "run_idx_a":ra.get("run_idx",""),"run_idx_b":rb.get("run_idx",""),
                         "seed_a":ra.get("seed",""),"seed_b":rb.get("seed",""),
                         "hazard_cost":ra.get("hazard_cost",""),
                         "chain_object_a":ra.get("object_id",""),
                         "chain_object_b":rb.get("object_id",""),
                         "link_sequence_a":">".join(sa),"link_sequence_b":">".join(sb),
                         "link_sequence_distance":round(_edit_distance(sa,sb),4),
                         "within_run":ra.get("run_idx","")==rb.get("run_idx","")})
    return rows

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--no-report",            action="store_true")
    parser.add_argument("--no-goal",              action="store_true")
    parser.add_argument("--no-counterfactual",    action="store_true")
    parser.add_argument("--no-belief-revision",   action="store_true")
    parser.add_argument("--no-completion-signal", action="store_true")
    parser.add_argument("--no-causal",            action="store_true")
    parser.add_argument("--no-env2",              action="store_true")
    parser.add_argument("--no-prediction",        action="store_true")
    parser.add_argument("--no-return",            action="store_true")
    parser.add_argument("--no-social",            action="store_true",
                        help="Disable social observation (v1.15 regression baseline)")
    args=parser.parse_args()

    report=not args.no_report; with_goal=not args.no_goal
    with_cf=not args.no_counterfactual; with_br=not args.no_belief_revision
    with_cs=not args.no_completion_signal; with_causal=not args.no_causal
    with_env2=not args.no_env2; with_pred=not args.no_prediction
    with_return=not args.no_return
    # --no-social: sets prediction disabled equivalent (no V1511SchemaObserver active)
    # implemented by overriding _check_social_observation at module level
    if args.no_social:
        global _check_social_observation
        _check_social_observation = lambda *a, **kw: False

    seeds=_find_seed_csv()
    jobs=[(cost_idx*RUNS_PER_COST+run_idx,
           seeds.get((cost,run_idx), run_idx*1000+int(cost*10)),
           cost)
          for cost_idx,cost in enumerate(HAZARD_COSTS)
          for run_idx in range(RUNS_PER_COST)]

    csv_files={}; writers={}
    try:
        for key,path in [
            ("run",RUN_DATA_CSV),("prov",PROVENANCE_CSV),
            ("rpt",REPORT_CSV),("sum",REPORT_SUMMARY_CSV),
            ("es",END_STATE_DRAW_CSV),("env2",ENV2_RUN_DATA_CSV),
            ("q5i",Q5_INDIVIDUATION_CSV),("pred",PREDICTED_SCHEMA_CSV),
            ("arc",ARC_COMPLETE_CSV),("pair",ARC_PAIRED_CSV),
            ("soc",SOCIAL_OBSERVATION_CSV),("bo",BEING_OBSERVED_CSV),
        ]:
            csv_files[key]=open(path,"w",newline="")
        if with_goal:   csv_files["goal"]=open(GOAL_CSV,"w",newline="")
        if with_cf:     csv_files["cf"]  =open(COUNTERFACTUAL_CSV,"w",newline="")
        if with_br:     csv_files["br"]  =open(BELIEF_REVISION_CSV,"w",newline="")
        if with_causal: csv_files["caus"]=open(CAUSAL_CSV,"w",newline="")

        writers["run"] =csv.DictWriter(csv_files["run"], fieldnames=RUN_DATA_FIELDS)
        writers["prov"]=csv.DictWriter(csv_files["prov"],fieldnames=["arch","run_idx","agent","seed","hazard_cost","flag_id","flag_type","flag_set_step"])
        writers["rpt"] =csv.DictWriter(csv_files["rpt"], fieldnames=REPORT_FIELDS)
        writers["sum"] =csv.DictWriter(csv_files["sum"], fieldnames=SUMMARY_FIELDS)
        writers["es"]  =csv.DictWriter(csv_files["es"],  fieldnames=END_STATE_DRAW_FIELDS)
        writers["env2"]=csv.DictWriter(csv_files["env2"],fieldnames=ENV2_RUN_DATA_FIELDS)
        writers["q5i"] =csv.DictWriter(csv_files["q5i"], fieldnames=Q5_INDIVIDUATION_FIELDS)
        writers["pred"]=csv.DictWriter(csv_files["pred"],fieldnames=PREDICTED_SCHEMA_FIELDS_151)
        writers["arc"] =csv.DictWriter(csv_files["arc"], fieldnames=ARC_COMPLETE_FIELDS)
        writers["pair"]=csv.DictWriter(csv_files["pair"],fieldnames=ARC_PAIRED_FIELDS)
        writers["soc"] =csv.DictWriter(csv_files["soc"], fieldnames=SOCIAL_OBSERVATION_FIELDS)
        writers["bo"]  =csv.DictWriter(csv_files["bo"],  fieldnames=BEING_OBSERVED_FIELDS)
        for w in writers.values(): w.writeheader()
        if with_goal:
            writers["goal"]=csv.DictWriter(csv_files["goal"],fieldnames=GOAL_FIELDS)
            writers["goal"].writeheader()
        if with_cf:
            writers["cf"]=csv.DictWriter(csv_files["cf"],fieldnames=COUNTERFACTUAL_FIELDS)
            writers["cf"].writeheader()
        if with_br:
            writers["br"]=csv.DictWriter(csv_files["br"],fieldnames=BELIEF_REVISION_FIELDS)
            writers["br"].writeheader()
        if with_causal:
            writers["caus"]=csv.DictWriter(csv_files["caus"],fieldnames=CAUSAL_FIELDS)
            writers["caus"].writeheader()

        total_statements=0; total_hallucinations=0
        arc_complete_runs=0; both_arc_complete=0
        social_corroboration_fires=0; zpd_positive=0
        q6_total=0; being_observed_total=0
        incomplete_runs=[]; all_causal_records=[]

        print(f"v1.15.3 batch: {len(jobs)} runs x 2 agents = {len(jobs)*2} agent-runs")
        print(f"  Social observation: {'ON' if not args.no_social else 'OFF (regression)'}")
        print()

        for run_idx,seed_a,hazard_cost in jobs:
            seed_b=seed_a+SEED_B_OFFSET
            try:
                result=run_one(run_idx,seed_a,seed_b,hazard_cost,
                               report=report,with_goal=with_goal,
                               with_counterfactual=with_cf,
                               with_belief_revision=with_br,
                               with_completion_signal=with_cs,
                               with_causal=with_causal,with_env2=with_env2,
                               with_prediction=with_pred,with_return=with_return)
            except Exception as e:
                import traceback as tb
                print(f"  Run {run_idx}: ERROR — {e}"); tb.print_exc()
                incomplete_runs.append(run_idx); continue

            (run_row_a,run_row_b,stmts_a,stmts_b,summ_a,summ_b,
             prov_a,prov_b,goal_a,goal_b,cf_a,cf_b,br_a,br_b,
             es_a,es_b,caus_a,caus_b,causal_recs_a,causal_recs_b,
             pred_rows_a,pred_rows_b,arc_row_a,arc_row_b,arc_paired,
             soc_obs_a,soc_obs_b,being_obs_a,being_obs_b)=result

            for rr in (run_row_a,run_row_b):
                writers["run"].writerow({k:rr.get(k,"") for k in RUN_DATA_FIELDS})
            flush_provenance_csv(prov_a,PROVENANCE_CSV)
            flush_provenance_csv(prov_b,PROVENANCE_CSV)

            for go,co,bo in ((goal_a,cf_a,br_a),(goal_b,cf_b,br_b)):
                if with_goal and go:
                    for gr in go.get_substrate().get("goal_progress",[]):
                        writers["goal"].writerow({k:gr.get(k,"") for k in GOAL_FIELDS})
                if with_cf and co:
                    for cr in co.get_substrate():
                        writers["cf"].writerow({k:cr.get(k,"") for k in COUNTERFACTUAL_FIELDS})
                if with_br and bo:
                    for br in bo.get_substrate():
                        writers["br"].writerow({k:br.get(k,"") for k in BELIEF_REVISION_FIELDS})

            for caus,causal_recs,seed in ((caus_a,causal_recs_a,seed_a),(caus_b,causal_recs_b,seed_b)):
                if with_causal and caus:
                    cm={"arch":ARCH,"run_idx":run_idx,"seed":seed,
                        "hazard_cost":hazard_cost,"num_steps":BATCH_STEPS}
                    for cr in caus.causal_rows():
                        writers["caus"].writerow({k:{**cm,**cr}.get(k,"") for k in CAUSAL_FIELDS})
                    all_causal_records.extend([{**r,"run_idx":run_idx,"seed":seed,
                                                "hazard_cost":hazard_cost}
                                               for r in causal_recs])

            for pred_rows in (pred_rows_a,pred_rows_b):
                if with_pred and pred_rows:
                    for pr in pred_rows:
                        writers["pred"].writerow(
                            {k:pr.get(k,"") for k in PREDICTED_SCHEMA_FIELDS_151})

            for arc_row in (arc_row_a,arc_row_b):
                if arc_row:
                    writers["arc"].writerow(
                        {k:arc_row.get(k,"") for k in ARC_COMPLETE_FIELDS})
            if arc_paired:
                writers["pair"].writerow(
                    {k:arc_paired.get(k,"") for k in ARC_PAIRED_FIELDS})
                if arc_paired.get("arc_complete_a") or arc_paired.get("arc_complete_b"):
                    arc_complete_runs+=1
                if arc_paired.get("both_arc_complete"): both_arc_complete+=1
                if arc_paired.get("social_corroboration_fired_b"):
                    social_corroboration_fires+=1
                zpd=arc_paired.get("zpd_delta_b")
                if zpd is not None and zpd>0: zpd_positive+=1

            # Social observation records
            for soc_records,agent_label,seed in (
                (soc_obs_a,"a",seed_a),(soc_obs_b,"b",seed_b)
            ):
                for rec in soc_records:
                    row={"arch":ARCH,"run_idx":run_idx,"agent":agent_label,
                         "seed":seed,"hazard_cost":hazard_cost,**rec}
                    writers["soc"].writerow(
                        {k:row.get(k,"") for k in SOCIAL_OBSERVATION_FIELDS})

            # Being-observed records
            for bo_records,agent_label,seed in (
                (being_obs_a,"a",seed_a),(being_obs_b,"b",seed_b)
            ):
                for rec in bo_records:
                    row={"arch":ARCH,"run_idx":run_idx,"agent":agent_label,
                         "seed":seed,"hazard_cost":hazard_cost,
                         "step":rec["step"],"observed_by":rec["observed_by"],
                         "object_id":rec["object_id"],
                         "observer_pos":str(rec["observer_pos"]),
                         "own_mastery_at_step":rec["own_mastery"]}
                    writers["bo"].writerow(
                        {k:row.get(k,"") for k in BEING_OBSERVED_FIELDS})
                    being_observed_total+=len(bo_records)

            for stmts,summ,es_step,ag_label,seed in (
                (stmts_a,summ_a,es_a,"a",seed_a),
                (stmts_b,summ_b,es_b,"b",seed_b),
            ):
                if report and stmts:
                    for s in stmts:
                        writers["rpt"].writerow({
                            "arch":ARCH,"run_idx":run_idx,"agent":ag_label,
                            "seed":seed,"hazard_cost":hazard_cost,
                            "num_steps":BATCH_STEPS,
                            "query_type":getattr(s,"query_type",""),
                            "statement_text":getattr(s,"text",""),
                            "source_type":getattr(s,"source_type",""),
                            "source_key":getattr(s,"source_key",""),
                            "source_resolves":getattr(s,"source_resolves",True),
                        })
                    q6_total+=sum(1 for s in stmts
                                  if getattr(s,"query_type","")=="social_corroboration")
                if report and summ:
                    writers["sum"].writerow({k:summ.get(k,"") for k in SUMMARY_FIELDS})
                    total_statements+=summ.get("total_statements",0)
                    total_hallucinations+=summ.get("hallucination_count",0)
                writers["es"].writerow({
                    "arch":ARCH,"run_idx":run_idx,"agent":ag_label,"seed":seed,
                    "hazard_cost":hazard_cost,"num_steps":BATCH_STEPS,
                    "activation_step":None,"end_state_banked_step":es_step,
                    "steps_draw_to_bank":None,"end_state_draw_active":False})

            if report and (summ_a or summ_b):
                ac_sym=("✓" if arc_paired.get("both_arc_complete")
                         else ("a" if arc_paired.get("arc_complete_a")
                               else ("b" if arc_paired.get("arc_complete_b") else "–")))
                soc_sym="S" if arc_paired.get("social_corroboration_fired_b") else "-"
                zpd_val=arc_paired.get("zpd_delta_b")
                zpd_str=(f"ZPD={zpd_val:+,}" if zpd_val is not None else "ZPD=–")
                h_a=(summ_a or {}).get("hallucination_count","?")
                h_b=(summ_b or {}).get("hallucination_count","?")
                print(f"  Run {run_idx:3d} | sa={seed_a:12d} cost={hazard_cost:5.1f} | "
                      f"arc={ac_sym} soc={soc_sym} {zpd_str} | halluc={h_a}/{h_b}")

        print()
        print("Category Ω: arc_complete")
        print(f"  At least one:  {arc_complete_runs}/{len(jobs)}")
        print(f"  Both complete: {both_arc_complete}/{len(jobs)}")
        print()
        print("Category γ: ZPD")
        print(f"  Social corroboration fired: {social_corroboration_fires}/{len(jobs)}")
        print(f"  ZPD delta > 0 (B faster than baseline): {zpd_positive}/{social_corroboration_fires}")
        print(f"  Q6 statements:    {q6_total}")
        print(f"  Being-observed records: {being_observed_total}")
        print()
        print("="*65)
        print(f"v1.15.3 complete. {len(jobs)-len(incomplete_runs)}/{len(jobs)} runs.")
        if report:
            print(f"  Statements:    {total_statements}")
            print(f"  Hallucinations:{total_hallucinations}")
            print(f"  Category α:    {'PASS' if total_hallucinations==0 else 'FAIL'}")
        if incomplete_runs: print(f"  Incomplete: {incomplete_runs}")
        print()
        print("  Outputs:")
        for label,path in [
            ("Run data",          RUN_DATA_CSV),
            ("Report",            REPORT_CSV),
            ("Arc complete",      ARC_COMPLETE_CSV),
            ("Arc paired",        ARC_PAIRED_CSV),
            ("Social observation",SOCIAL_OBSERVATION_CSV),
            ("Being observed",    BEING_OBSERVED_CSV),
            ("Predicted schema",  PREDICTED_SCHEMA_CSV),
        ]:
            print(f"    {label:<22} {path}")

    finally:
        for f in csv_files.values(): f.close()


if __name__=="__main__":
    main()
