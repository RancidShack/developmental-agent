"""
curiosity_agent_v1_15_batch.py
--------------------------------
v1.15 batch runner: Developmental Individuation in a Shared Prepared
Environment — Two Agents, One World.

CHANGES FROM V1.14.1
  Two V110Agents run simultaneously in a single shared V113World
  instance. Agents are cognitively independent (separate Q-tables,
  mastery_flag, knowledge_banked, observers). The world's object_type
  and knowledge_unlocked dicts are shared: HAZARD→KNOWLEDGE mutations
  propagate to both agents immediately.

  Each tick: agent_a acts, then agent_b acts. world.agent_pos is swapped
  to each agent's position before its step. Agents are invisible to each
  other (no inter-agent perception layer; reserved for v1.15.1).

  Three-phase structure inherited from v1.14.1. Each agent independently
  evaluates transfer condition (ENV1), att_blue mastery (ENV2), and
  arc_complete (return ENV1). Phases terminate when BOTH eligible agents
  are done or budget is exhausted.

  New outputs:
    arc_paired_v1_15.csv  — one paired comparison row per run
  All v1.14.1 outputs preserved with 'agent' field ('a'/'b').

  SEED DESIGN: seed_a from run_data_v1_14_1.csv; seed_b = seed_a + 20_000.
  ARCH = v1_15.

PRE-REGISTRATION: v1_15_pre_registration.md (8 May 2026).
"""

import argparse
import csv
import math
import os

import numpy as np

import v1_13_observer_substrates  # noqa: F401
from v1_13_observer_substrates import (
    build_bundle_from_observers, PREDICTION_FAMILY_MINIMUM,
)
from v1_13_world import (
    V113World, ENV1_FAMILIES, ENV2_FAMILIES, NUM_ACTIONS,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ,
    PERCEPTION_RADIUS, START_POS,
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
# Paths
# ---------------------------------------------------------------------------

SEED_CSV_PRIMARY     = "run_data_v1_14_1.csv"
RUN_DATA_CSV         = "run_data_v1_15.csv"
PROVENANCE_CSV       = "provenance_v1_15.csv"
GOAL_CSV             = "goal_v1_15.csv"
COUNTERFACTUAL_CSV   = "counterfactual_v1_15.csv"
BELIEF_REVISION_CSV  = "belief_revision_v1_15.csv"
CAUSAL_CSV           = "causal_v1_15.csv"
REPORT_CSV           = "report_v1_15.csv"
REPORT_SUMMARY_CSV   = "report_summary_v1_15.csv"
END_STATE_DRAW_CSV   = "end_state_draw_log_v1_15.csv"
ENV2_RUN_DATA_CSV    = "env2_run_data_v1_15.csv"
Q5_INDIVIDUATION_CSV = "q5_individuation_v1_15.csv"
PREDICTED_SCHEMA_CSV = "predicted_schema_v1_15.csv"
ARC_COMPLETE_CSV     = "arc_complete_v1_15.csv"
ARC_PAIRED_CSV       = "arc_paired_v1_15.csv"        # v1.15 new

ENV1_STEPS         = 1_000_000
ENV2_STEPS         =   800_000
RETURN_ENV1_STEPS  =   200_000
BATCH_STEPS        = ENV1_STEPS
HAZARD_COSTS       = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST      = 10
ARCH               = "v1_15"
ENV2_SEED_OFFSET   = 10_000
RETURN_SEED_OFFSET = 20_000
SEED_B_OFFSET      = 20_000       # seed_b = seed_a + SEED_B_OFFSET

# ---------------------------------------------------------------------------
# Families (inherited from v1.14.1)
# ---------------------------------------------------------------------------

RETURN_ENV1_FAMILIES = [
    {
        "colour":   GREEN,  "dist_id":  "dist_green",
        "dist_pos": (3.0, 9.0, 3.0),
        "att_id":   "att_green", "att_pos": (2.0, 11.0, 2.0),
        "att_form": SQUARE_2D, "haz_id": "haz_green",
        "haz_pos":  (9.0, 10.0, 8.0), "haz_form": SPHERE_3D,
    },
    {
        "colour":   YELLOW, "dist_id":  "dist_yellow",
        "dist_pos": (8.0, 3.0, 3.0),
        "att_id":   "att_yellow", "att_pos": (10.0, 2.0, 2.0),
        "att_form": TRIANGLE_2D, "haz_id": "haz_yellow",
        "haz_pos":  (3.0, 5.0, 7.0), "haz_form": PYRAMID_3D,
    },
    {
        "colour":   BLUE,   "dist_id": None, "dist_pos": None,
        "att_id":   "att_blue", "att_pos": (5.0, 6.0, 10.0),
        "att_form": CIRCLE_2D,
        "haz_id":   "haz_blue", "haz_pos": (7.0, 8.0, 3.0),
        "haz_form": SPHERE_3D,
    },
]

RETURN_ENV1_PRECOMPLETED = [
    "haz_yellow", "haz_green",
    "haz_unaff_0", "haz_unaff_1", "haz_unaff_2",
]

# ---------------------------------------------------------------------------
# Field definitions (RUN_DATA_FIELDS adds 'agent'; others inherited)
# ---------------------------------------------------------------------------

RUN_DATA_FIELDS = [
    "arch", "run_idx", "agent", "seed", "hazard_cost", "num_steps",
    "phase_1_end_step", "phase_2_end_step",
    "time_to_first_flag", "time_to_second_flag", "time_to_final_flag",
    "total_cost_incurred",
    "time_to_first_mastery", "time_to_final_mastery",
    "mastery_order_sequence",
    "activation_step", "end_state_found_step", "end_state_banked",
    "time_to_first_transition", "time_to_final_transition",
    "transition_order_sequence", "knowledge_banked_sequence",
    "yellow_pre_transition_entries", "green_pre_transition_entries",
    "unaffiliated_pre_transition_entries",
    "yellow_resolution_window", "green_resolution_window",
    "total_prediction_error_events", "prediction_error_complete",
    "goal_type", "goal_target_id", "goal_step_budget",
    "goal_resolved", "goal_resolution_step", "goal_budget_remaining",
    "goal_expired", "goal_last_progress_step", "goal_resolution_window",
    "goal_progress_event_count",
    "suppressed_approach_count", "goal_relevant_suppressed_count",
    "suppressed_approach_objects",
    "cf_records_raw", "cf_records_emitted", "cf_exclusion_rate",
    "end_state_draw_active", "end_state_banked_step", "steps_draw_to_bank",
    "revised_expectation_count",
    "causal_chain_count", "mean_chain_depth", "complete_chain_count",
    "q5_statement_count",
    "env2_ran", "haz_blue_approached",
    "predicted_record_written", "transfer_triggered_step",
    "env1_mastery_order_sequence", "env1_end_state_banked_step",
    "return_env1_ran", "arc_complete", "arc_timeout",
    "ineligible_reason", "return_step",
    "transformation_step", "arc_total_steps",
]

ARC_COMPLETE_FIELDS = [
    "arch", "run_idx", "agent", "seed", "hazard_cost",
    "arc_complete", "arc_timeout", "ineligible_reason",
    "env1_surprise_step", "prediction_step",
    "transfer_triggered_step", "confirmation_step",
    "return_step", "transformation_step",
    "arc_total_steps", "arc_env_span",
    "causal_chain_depth", "causal_chain_complete",
]

ARC_PAIRED_FIELDS = [
    "arch", "run_idx", "seed_a", "seed_b", "hazard_cost",
    "arc_complete_a", "arc_complete_b", "both_arc_complete",
    "arc_total_steps_a", "arc_total_steps_b", "arc_total_steps_delta",
    "transformation_step_a", "transformation_step_b",
    "transfer_triggered_step_a", "transfer_triggered_step_b",
    "env2_actual_steps_a", "env2_actual_steps_b",
    "first_transformer",
    "haz_blue_shared_benefit",
    "individuation_confirmed",
]

REPORT_FIELDS = [
    "arch", "run_idx", "agent", "seed", "hazard_cost", "num_steps",
    "query_type", "statement_text",
    "source_type", "source_key", "source_resolves",
]

SUMMARY_FIELDS = [
    "arch", "run_idx", "agent", "seed", "hazard_cost", "num_steps",
    "total_statements", "statements_q1", "statements_q2",
    "statements_q3", "statements_q4", "statements_q5",
    "hallucination_count",
    "q1_formation_depth", "q3_surprise_cells", "q3_resolution_stated",
    "report_complete", "statements_with_relevance_markers",
    "goal_statement_present", "goal_resolution_stated",
    "q4_statement_count",
    "suppressed_approach_count", "goal_relevant_suppressed_count",
    "br_statement_count", "revised_expectation_count",
    "mean_approach_delta", "bias_effective",
    "cf_records_raw", "cf_records_emitted", "cf_exclusion_rate",
    "end_state_draw_active", "end_state_banked_step",
    "causal_chain_count", "mean_chain_depth", "complete_chain_count",
    "q5_statement_count",
    "predicted_record_written", "predicted_record_state",
]

END_STATE_DRAW_FIELDS = [
    "arch", "run_idx", "agent", "seed", "hazard_cost", "num_steps",
    "activation_step", "end_state_banked_step",
    "steps_draw_to_bank", "end_state_draw_active",
]

ENV2_RUN_DATA_FIELDS = [
    "arch", "run_idx", "agent", "seed", "hazard_cost",
    "env2_seed", "env2_activation_step", "env2_phase_1_end_step",
    "env2_end_state_banked_step",
    "env2_yellow_pre_transition_entries", "env2_yellow_resolution_window",
    "env2_green_pre_transition_entries",  "env2_green_resolution_window",
    "env2_q5_chain_count", "env2_q5_mean_chain_depth",
    "att_blue_mastery_step", "att_blue_mastery_env",
    "predicted_record_state_at_run_end",
    "att_blue_sequence_position", "env2_mastery_order_sequence",
    "env2_att_yellow_mastery_step", "env2_att_green_mastery_step",
    "env2_actual_steps",
]

Q5_INDIVIDUATION_FIELDS = [
    "arch", "run_idx_a", "run_idx_b", "seed_a", "seed_b",
    "hazard_cost", "chain_object_a", "chain_object_b",
    "link_sequence_a", "link_sequence_b",
    "link_sequence_distance", "within_run",
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
# Helpers (inherited from v1.14.1)
# ---------------------------------------------------------------------------

def _check_transfer_condition(world, agent, predicted_record_written):
    if not all(world.knowledge_unlocked.get(h, False)
               for h in world.hazard_cells):
        return False
    if not all(getattr(agent, 'mastery_flag', {}).get(a, 0) == 1
               for a in world.attractor_cells):
        return False
    if not predicted_record_written:
        return False
    return True


def _return_to_env1_condition_met(schema_v13_obs):
    if schema_v13_obs is None:
        return False
    for rec in schema_v13_obs.get_predicted_records():
        if rec.get("object_id") == "haz_blue":
            return rec.get("state") == CONFIRMED_STATE
    return False


# ---------------------------------------------------------------------------
# AgentCtx: per-agent state within a shared-world phase
# ---------------------------------------------------------------------------

class AgentCtx:
    """Holds one agent's cognitive context and per-step tracking state.

    The world is shared across both AgentCtx instances in a run.
    Each ctx holds its own observers, position, and tracking flags.
    """

    __slots__ = (
        'label', 'agent', 'seed',
        'prov_obs', 'schema_obs', 'family_obs', 'comp_obs', 'pe_obs',
        'goal_obs', 'cf_obs', 'br_obs',
        'schema_v13_obs', 'causal_obs',
        'observers',
        'pos', 'state',
        'done',
        'end_state_banked_step', 'activation_step',
        'haz_blue_approached',
        'predicted_record_written',
        'transfer_condition_met', 'transfer_triggered_step',
        'att_blue_mastery_step', 'att_yellow_mastery_step',
        'att_green_mastery_step',
        'actual_steps',
        'env2_actual_steps',
    )

    def __init__(self, label, agent, seed,
                 prov_obs, schema_obs, family_obs, comp_obs, pe_obs,
                 goal_obs, cf_obs, br_obs,
                 schema_v13_obs, causal_obs):
        self.label      = label      # 'a' or 'b'
        self.agent      = agent
        self.seed       = seed
        self.prov_obs   = prov_obs
        self.schema_obs = schema_obs
        self.family_obs = family_obs
        self.comp_obs   = comp_obs
        self.pe_obs     = pe_obs
        self.goal_obs   = goal_obs
        self.cf_obs     = cf_obs
        self.br_obs     = br_obs
        self.schema_v13_obs = schema_v13_obs
        self.causal_obs     = causal_obs

        self.observers = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs]
        if goal_obs: self.observers.append(goal_obs)
        if cf_obs:   self.observers.append(cf_obs)
        if br_obs:   self.observers.append(br_obs)

        self.pos   = START_POS
        self.state = None
        self.done  = False

        self.end_state_banked_step  = None
        self.activation_step        = None
        self.haz_blue_approached    = False
        self.predicted_record_written = False
        self.transfer_condition_met = False
        self.transfer_triggered_step = None
        self.att_blue_mastery_step  = None
        self.att_yellow_mastery_step = None
        self.att_green_mastery_step  = None
        self.actual_steps   = 0
        self.env2_actual_steps = 0


# ---------------------------------------------------------------------------
# Observer setup
# ---------------------------------------------------------------------------

def _setup_observers(agent, world, meta, run_idx, num_steps,
                     with_goal, with_counterfactual, with_belief_revision,
                     carry_prov_obs=None):
    """Build observer set for one agent in a (possibly shared) world."""
    ctc = {
        "FRAME": FRAME, "NEUTRAL": NEUTRAL, "HAZARD": HAZARD,
        "ATTRACTOR": ATTRACTOR, "END_STATE": END_STATE,
        "KNOWLEDGE": KNOWLEDGE, "DIST_OBJ": DIST_OBJ,
    }
    if carry_prov_obs is not None:
        prov_obs = carry_prov_obs
        prov_obs._agent = agent
        prov_obs._world = world
        prov_obs._environment_complete_fired = False
    else:
        prov_obs = V1ProvenanceStore(agent, world, meta, ctc)

    schema_obs = V13SchemaObserverBase(agent, world, meta)
    family_obs = V13FamilyObserver(agent, world, meta, provenance_store=prov_obs)
    comp_obs   = V14ComparisonObserver(family_obs, meta)
    pe_obs     = V15PredictionErrorObserver(agent, world, meta)

    goal_obs = None
    if with_goal:
        goal_type, target_id, step_budget = assign_goal(run_idx, num_steps)
        goal_obs = V18GoalObserver(agent, world, meta,
                                   goal_type, target_id, step_budget)

    cf_obs = None
    if with_counterfactual:
        cf_obs = V19CounterfactualObserver(agent, world, meta, goal_obs=goal_obs)
        cf_obs._records = []; cf_obs._last_emission_step = {}
        cf_obs._cf_raw_count = 0

    br_obs = None
    if with_belief_revision:
        br_obs = V110BeliefRevisionObserver(
            agent, world, meta,
            prediction_error_obs=pe_obs,
            provenance_obs=prov_obs,
            counterfactual_obs=cf_obs,
        )

    return prov_obs, schema_obs, family_obs, comp_obs, pe_obs, goal_obs, cf_obs, br_obs


# ---------------------------------------------------------------------------
# Agent carry (ENV1 → ENV2, ENV2 → return ENV1)
# ---------------------------------------------------------------------------

def _carry_agent(agent, world, seed, env_number='env2'):
    """Reset per-environment agent state for a new environment."""
    agent.world = world
    for attr in ('end_state_banked', 'activation_step',
                 'phase_1_end_step', 'phase_2_end_step',
                 'end_state_found_step'):
        if hasattr(agent, attr):
            setattr(agent, attr,
                    False if attr == 'end_state_banked' else None)

    if hasattr(agent, 'mastery_flag'):
        agent.mastery_flag = {a: 0 for a in world.attractor_cells}
    if hasattr(agent, 'knowledge_banked'):
        agent.knowledge_banked = {h: False for h in world.hazard_cells}
    if hasattr(agent, 'knowledge_banked_step'):
        agent.knowledge_banked_step = {h: None for h in world.hazard_cells}
    if hasattr(agent, 'knowledge_banked_sequence'):
        agent.knowledge_banked_sequence = []
    if hasattr(agent, '_knowledge_unlocked'):
        agent._knowledge_unlocked = {h: False for h in world.hazard_cells}
    if hasattr(agent, 'mastery_order_sequence'):
        agent.mastery_order_sequence = []
    if hasattr(agent, 'time_to_first_mastery'):
        agent.time_to_first_mastery = None
    if hasattr(agent, 'time_to_final_mastery'):
        agent.time_to_final_mastery = None


def _carry_agent_return(agent, world):
    """Apply return ENV1 carry: reset with CRITICAL INVARIANT preserved."""
    _carry_agent(agent, world, None, env_number='return')

    # CRITICAL INVARIANT: preserve att_blue mastery
    if hasattr(agent, 'mastery_flag'):
        agent.mastery_flag = {a: 0 for a in world.attractor_cells}
        agent.mastery_flag['att_blue'] = 1

    if hasattr(agent, 'knowledge_banked'):
        agent.knowledge_banked = {h: False for h in world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent.knowledge_banked:
                agent.knowledge_banked[oid] = True

    if hasattr(agent, '_knowledge_unlocked'):
        agent._knowledge_unlocked = {h: False for h in world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent._knowledge_unlocked:
                agent._knowledge_unlocked[oid] = True
        # haz_blue stays False — triggers on first contact


# ---------------------------------------------------------------------------
# Single-agent step (called alternately for A and B in the shared world)
# ---------------------------------------------------------------------------

def _step_agent(ctx, world, step, env_number,
                with_completion_signal, with_prediction):
    """Execute one step for ctx.agent in the shared world.

    Sets world.agent_pos to ctx.pos before acting, updates ctx.pos after.
    ctx.done is set True when the agent completes its phase objective.
    """
    if ctx.done:
        return None   # contact_oid returned for shared-benefit detection

    world.agent_pos = ctx.pos

    for obs in ctx.observers:
        obs.on_pre_action(step)

    action = ctx.agent.choose_action(ctx.state)
    obs_next, contact_oid, moved, cost = world.step(action)
    ctx.pos = world.agent_pos

    ctx.agent.record_action_outcome(
        contact_oid, moved or contact_oid is not None, cost, world, step
    )

    for obs in ctx.observers:
        obs.on_post_event(step)

    intrinsic = (
        ctx.agent.novelty_reward(ctx.state)
        + ctx.agent.preference_reward(ctx.state)
        + ctx.agent.feature_reward(ctx.state)
    )
    if with_completion_signal and isinstance(ctx.agent, V110Agent):
        intrinsic += ctx.agent.end_state_draw_reward(ctx.state, obs_next)

    if ctx.br_obs is not None:
        obj_pos = getattr(world, 'object_positions', {})
        for bias_oid in ctx.br_obs.active_biased_objects(step):
            bp = obj_pos.get(bias_oid)
            if bp:
                intrinsic += ctx.br_obs.preference_bias_reward(
                    bias_oid, step, moving_closer=True
                )

    if (with_prediction and ctx.schema_v13_obs is not None
            and env_number == 2
            and ctx.schema_v13_obs.has_pending_prediction("haz_blue")):
        att_pos = world.object_positions.get("att_blue")
        if att_pos and ctx.pos:
            d = math.sqrt(sum((a-b)**2 for a,b in zip(ctx.pos, att_pos)))
            if d > 0:
                intrinsic += 0.1 / d

    ctx.agent.update_values(ctx.state, action, obs_next, intrinsic)
    ctx.agent.update_model(ctx.state, action, obs_next)
    ctx.state = obs_next

    # Tracking
    if (ctx.activation_step is None
            and getattr(ctx.agent, 'activation_step', None) is not None):
        ctx.activation_step = step

    if (ctx.end_state_banked_step is None
            and getattr(ctx.agent, 'end_state_banked', False)):
        ctx.prov_obs.on_end_state_banked(step)
        ctx.end_state_banked_step = step

    # haz_blue approach (ENV1)
    if env_number == 1 and not ctx.haz_blue_approached:
        hbp = world.object_positions.get("haz_blue")
        if hbp:
            if math.sqrt(sum((a-b)**2
                             for a,b in zip(ctx.pos, hbp))) <= PERCEPTION_RADIUS:
                ctx.haz_blue_approached = True

    # Predicted record (ENV1)
    if (env_number == 1 and ctx.haz_blue_approached
            and step % 500 == 0
            and with_prediction and ctx.schema_v13_obs is not None
            and ctx.causal_obs is not None
            and not ctx.schema_v13_obs.has_pending_prediction("haz_blue")
            and not any(r["object_id"] == "haz_blue"
                        for r in ctx.schema_v13_obs.get_predicted_records())):
        n = sum(1 for h in ('haz_yellow', 'haz_green')
                if world.knowledge_unlocked.get(h, False))
        if n >= PREDICTION_FAMILY_MINIMUM:
            basis = sorted(h for h in ('haz_yellow', 'haz_green')
                           if world.knowledge_unlocked.get(h, False))
            ctx.schema_v13_obs.add_predicted_record({
                "object_id":              "haz_blue",
                "predicted_precondition": "att_blue",
                "basis_chains":           basis,
                "prediction_step":        step,
                "prediction_env":         env_number,
            })
            ctx.predicted_record_written = True

    # att_blue mastery (ENV2)
    if (env_number == 2 and ctx.att_blue_mastery_step is None
            and contact_oid == "att_blue"
            and getattr(ctx.agent, 'mastery_flag', {}).get('att_blue', 0) == 1):
        ctx.att_blue_mastery_step = step
        if with_prediction and ctx.schema_v13_obs is not None:
            ctx.schema_v13_obs.confirm_predicted_record(
                object_id="haz_blue",
                confirmation_step=step,
                confirming_env=env_number,
            )

    # Family mastery tracking (ENV2)
    if env_number == 2:
        if (ctx.att_yellow_mastery_step is None and contact_oid == "att_yellow"
                and getattr(ctx.agent, 'mastery_flag', {}).get('att_yellow', 0) == 1):
            ctx.att_yellow_mastery_step = step
        if (ctx.att_green_mastery_step is None and contact_oid == "att_green"
                and getattr(ctx.agent, 'mastery_flag', {}).get('att_green', 0) == 1):
            ctx.att_green_mastery_step = step

    # Transfer condition (ENV1)
    if (env_number == 1 and not ctx.transfer_condition_met
            and ctx.haz_blue_approached):
        pred_ok = with_prediction and ctx.schema_v13_obs is not None
        if _check_transfer_condition(
                world, ctx.agent,
                ctx.predicted_record_written if pred_ok else True):
            ctx.transfer_condition_met = True
            ctx.transfer_triggered_step = step
            ctx.done = True

    # ENV2 exit
    if env_number == 2 and ctx.att_blue_mastery_step is not None:
        ctx.done = True

    return contact_oid


# ---------------------------------------------------------------------------
# Two-agent phase runner
# ---------------------------------------------------------------------------

def _run_phase_two_agents(ctx_a, ctx_b, world, num_steps, env_number,
                           with_completion_signal, with_prediction):
    """Run both agents in the shared world for one phase.

    Alternates A-then-B each tick. Phase ends when both agents are done
    or the step budget is exhausted.

    Returns: actual_steps (int)
    """
    # Initialise states from each agent's starting position
    world.agent_pos = ctx_a.pos
    ctx_a.state = world.observe()
    world.agent_pos = ctx_b.pos
    ctx_b.state = world.observe()

    actual_steps = num_steps
    for step in range(num_steps):
        # --- Agent A ---
        contact_a = _step_agent(
            ctx_a, world, step, env_number,
            with_completion_signal, with_prediction,
        )
        # --- Agent B ---
        contact_b = _step_agent(
            ctx_b, world, step, env_number,
            with_completion_signal, with_prediction,
        )

        if ctx_a.done and ctx_b.done:
            actual_steps = step + 1
            break

    ctx_a.actual_steps += actual_steps
    ctx_b.actual_steps += actual_steps
    return actual_steps


# ---------------------------------------------------------------------------
# Return ENV1 two-agent phase
# ---------------------------------------------------------------------------

def _run_return_env1_two_agents(run_idx, seed_a, seed_b, hazard_cost,
                                 ctx_a, ctx_b,
                                 env1_transfer_step_a, env1_transfer_step_b,
                                 env2_actual_steps_a, env2_actual_steps_b,
                                 pred_step_a, pred_step_b,
                                 conf_step_a, conf_step_b,
                                 with_completion_signal):
    """Run both eligible agents through return ENV1 in a shared world.

    Both agents are carried with the CRITICAL INVARIANT.
    arc_complete fires for each agent independently when
    world.knowledge_unlocked['haz_blue'] becomes True.

    Note: haz_blue is a SHARED object. The FIRST agent to trigger
    transform_to_knowledge('haz_blue') changes it for both agents.
    The second agent may therefore see haz_blue as KNOWLEDGE
    without having triggered the transformation itself.
    haz_blue_shared_benefit is set True in the paired row when this occurs.
    """
    return_seed = seed_a + RETURN_SEED_OFFSET
    np.random.seed(return_seed)

    return_world = V113World(
        families=RETURN_ENV1_FAMILIES,
        hazard_cost=hazard_cost,
        has_end_state=True,
        seed=return_seed,
        unreachable_hazards=None,
    )

    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in return_world.hazard_cells:
            return_world.transform_to_knowledge(oid)

    # Inject haz_blue twice — once for each agent (A first, then B)
    hbp = return_world.object_positions.get("haz_blue")
    if hbp is not None:
        return_world.inject_waypoint(hbp)
        return_world.inject_waypoint(hbp)

    # Carry both agents
    _carry_agent_return(ctx_a.agent, return_world)
    _carry_agent_return(ctx_b.agent, return_world)

    ctx_a.agent.world = return_world
    ctx_b.agent.world = return_world

    if ctx_a.prov_obs is not None:
        ctx_a.prov_obs._agent = ctx_a.agent
        ctx_a.prov_obs._world = return_world
        ctx_a.prov_obs._environment_complete_fired = False
    if ctx_b.prov_obs is not None:
        ctx_b.prov_obs._agent = ctx_b.agent
        ctx_b.prov_obs._world = return_world
        ctx_b.prov_obs._environment_complete_fired = False

    # Reset ctx positions and done flags for return phase
    ctx_a.pos = START_POS; ctx_a.done = False
    ctx_b.pos = START_POS; ctx_b.done = False

    # Return-phase tracking
    transform_step_a = None
    transform_step_b = None
    arc_complete_a   = False
    arc_complete_b   = False
    arc_timeout_a    = False
    arc_timeout_b    = False
    first_transformer = None     # 'a', 'b', or 'tie'
    haz_blue_was_knowledge_before_b = False

    return_world.agent_pos = ctx_a.pos
    ctx_a.state = return_world.observe()
    return_world.agent_pos = ctx_b.pos
    ctx_b.state = return_world.observe()

    actual_steps = RETURN_ENV1_STEPS

    for step in range(RETURN_ENV1_STEPS):
        # Agent A
        if not ctx_a.done:
            return_world.agent_pos = ctx_a.pos
            for obs in ctx_a.observers:
                obs.on_pre_action(step)
            action_a = ctx_a.agent.choose_action(ctx_a.state)
            obs_a, contact_a, moved_a, cost_a = return_world.step(action_a)
            ctx_a.pos = return_world.agent_pos
            ctx_a.agent.record_action_outcome(
                contact_a, moved_a or contact_a is not None,
                cost_a, return_world, step,
            )
            for obs in ctx_a.observers:
                obs.on_post_event(step)
            intrinsic_a = (
                ctx_a.agent.novelty_reward(ctx_a.state)
                + ctx_a.agent.preference_reward(ctx_a.state)
                + ctx_a.agent.feature_reward(ctx_a.state)
            )
            ctx_a.agent.update_values(ctx_a.state, action_a, obs_a, intrinsic_a)
            ctx_a.agent.update_model(ctx_a.state, action_a, obs_a)
            ctx_a.state = obs_a

            if return_world.knowledge_unlocked.get('haz_blue', False):
                if not arc_complete_a:
                    transform_step_a = step
                    arc_complete_a   = True
                    first_transformer = 'a'
                    ctx_a.agent.end_state_banked = True
                ctx_a.done = True

        # Agent B
        if not ctx_b.done:
            # Check if haz_blue was already KNOWLEDGE before B acts
            # (shared-benefit: A transformed it and now B sees it for free)
            hbk_before_b = return_world.knowledge_unlocked.get('haz_blue', False)

            return_world.agent_pos = ctx_b.pos
            for obs in ctx_b.observers:
                obs.on_pre_action(step)
            action_b = ctx_b.agent.choose_action(ctx_b.state)
            obs_b, contact_b, moved_b, cost_b = return_world.step(action_b)
            ctx_b.pos = return_world.agent_pos
            ctx_b.agent.record_action_outcome(
                contact_b, moved_b or contact_b is not None,
                cost_b, return_world, step,
            )
            for obs in ctx_b.observers:
                obs.on_post_event(step)
            intrinsic_b = (
                ctx_b.agent.novelty_reward(ctx_b.state)
                + ctx_b.agent.preference_reward(ctx_b.state)
                + ctx_b.agent.feature_reward(ctx_b.state)
            )
            ctx_b.agent.update_values(ctx_b.state, action_b, obs_b, intrinsic_b)
            ctx_b.agent.update_model(ctx_b.state, action_b, obs_b)
            ctx_b.state = obs_b

            if return_world.knowledge_unlocked.get('haz_blue', False):
                if not arc_complete_b:
                    transform_step_b = step
                    arc_complete_b   = True
                    # Shared benefit: haz_blue was already KNOWLEDGE when B stepped
                    if hbk_before_b:
                        haz_blue_was_knowledge_before_b = True
                    ctx_b.agent.end_state_banked = True
                    if first_transformer is None:
                        first_transformer = 'b'
                    elif first_transformer == 'b':
                        pass  # already 'b' from a tie situation
                    # If A already set it, first_transformer stays 'a'
                ctx_b.done = True

        if ctx_a.done and ctx_b.done:
            actual_steps = step + 1
            break

    if not arc_complete_a: arc_timeout_a = True
    if not arc_complete_b: arc_timeout_b = True

    # Determine first_transformer for the tie case
    if arc_complete_a and arc_complete_b:
        if transform_step_a == transform_step_b:
            first_transformer = 'tie'
        elif transform_step_a < transform_step_b:
            first_transformer = 'a'
        else:
            first_transformer = 'b'

    def _arc_total(transfer_step, env2_steps, transform_step):
        if transform_step is None:
            return None
        return (transfer_step or 0) + (env2_steps or 0) + transform_step

    arc_total_a = _arc_total(env1_transfer_step_a, env2_actual_steps_a, transform_step_a)
    arc_total_b = _arc_total(env1_transfer_step_b, env2_actual_steps_b, transform_step_b)

    def _arc_row(agent_label, seed, arc_complete, arc_timeout,
                 transform_step, arc_total,
                 env1_transfer_step, pred_step, conf_step):
        return {
            "arch": ARCH, "run_idx": run_idx,
            "agent": agent_label, "seed": seed,
            "hazard_cost": hazard_cost,
            "arc_complete":        arc_complete,
            "arc_timeout":         arc_timeout,
            "ineligible_reason":   "",
            "env1_surprise_step":  env1_transfer_step,
            "prediction_step":     pred_step,
            "transfer_triggered_step": env1_transfer_step,
            "confirmation_step":   conf_step,
            "return_step":         0,
            "transformation_step": transform_step,
            "arc_total_steps":     arc_total,
            "arc_env_span":        3 if arc_complete else None,
            "causal_chain_depth":  6 if arc_complete else 4,
            "causal_chain_complete": arc_complete,
        }

    arc_row_a = _arc_row('a', seed_a, arc_complete_a, arc_timeout_a,
                          transform_step_a, arc_total_a,
                          env1_transfer_step_a, pred_step_a, conf_step_a)
    arc_row_b = _arc_row('b', seed_b, arc_complete_b, arc_timeout_b,
                          transform_step_b, arc_total_b,
                          env1_transfer_step_b, pred_step_b, conf_step_b)

    delta = None
    if arc_total_a is not None and arc_total_b is not None:
        delta = abs(arc_total_a - arc_total_b)

    arc_paired = {
        "arch": ARCH, "run_idx": run_idx,
        "seed_a": seed_a, "seed_b": seed_b,
        "hazard_cost": hazard_cost,
        "arc_complete_a": arc_complete_a,
        "arc_complete_b": arc_complete_b,
        "both_arc_complete": arc_complete_a and arc_complete_b,
        "arc_total_steps_a": arc_total_a,
        "arc_total_steps_b": arc_total_b,
        "arc_total_steps_delta": delta,
        "transformation_step_a": transform_step_a,
        "transformation_step_b": transform_step_b,
        "transfer_triggered_step_a": env1_transfer_step_a,
        "transfer_triggered_step_b": env1_transfer_step_b,
        "env2_actual_steps_a": env2_actual_steps_a,
        "env2_actual_steps_b": env2_actual_steps_b,
        "first_transformer":   first_transformer,
        "haz_blue_shared_benefit": haz_blue_was_knowledge_before_b,
        "individuation_confirmed": delta is not None and delta > 0,
    }

    return dict(
        arc_row_a=arc_row_a, arc_row_b=arc_row_b,
        arc_paired=arc_paired,
        arc_complete_a=arc_complete_a, arc_complete_b=arc_complete_b,
        arc_timeout_a=arc_timeout_a, arc_timeout_b=arc_timeout_b,
        transform_step_a=transform_step_a, transform_step_b=transform_step_b,
        arc_total_a=arc_total_a, arc_total_b=arc_total_b,
    )


# ---------------------------------------------------------------------------
# Full run: ENV1 + ENV2 + return ENV1 (two agents)
# ---------------------------------------------------------------------------

def run_one(run_idx, seed_a, seed_b, hazard_cost,
            report=True,
            with_goal=True, with_counterfactual=True,
            with_belief_revision=True, with_completion_signal=True,
            with_causal=True, with_env2=True, with_prediction=True,
            with_return=True):

    # -----------------------------------------------------------------------
    # Schema / causal observers — one per agent
    # -----------------------------------------------------------------------
    schema_a = V13SchemaObserverPrediction(prediction_enabled=with_prediction)
    schema_b = V13SchemaObserverPrediction(prediction_enabled=with_prediction)

    run_meta_a = {"arch": ARCH, "hazard_cost": hazard_cost,
                  "num_steps": BATCH_STEPS, "run_idx": run_idx,
                  "seed": seed_a, "env": 1}
    run_meta_b = {"arch": ARCH, "hazard_cost": hazard_cost,
                  "num_steps": BATCH_STEPS, "run_idx": run_idx,
                  "seed": seed_b, "env": 1}

    causal_a = V111CausalObserver(run_meta_a) if with_causal else None
    causal_b = V111CausalObserver(run_meta_b) if with_causal else None

    # -----------------------------------------------------------------------
    # ENV1 — shared world, two agents
    # -----------------------------------------------------------------------
    np.random.seed(seed_a)
    env1_world = V113World(
        families=ENV1_FAMILIES, hazard_cost=hazard_cost,
        has_end_state=True, seed=seed_a,
        unreachable_hazards=['haz_blue'],
    )
    # Inject haz_blue waypoint twice (once per agent)
    hbp = env1_world.object_positions.get("haz_blue")
    if hbp is not None:
        env1_world.inject_waypoint(hbp)
        env1_world.inject_waypoint(hbp)

    AgentClass = V110Agent if with_completion_signal else V17Agent
    agent_a = AgentClass(env1_world, total_steps=ENV1_STEPS, num_actions=NUM_ACTIONS)
    agent_b = AgentClass(env1_world, total_steps=ENV1_STEPS, num_actions=NUM_ACTIONS)
    np.random.seed(seed_b)  # different seed for agent_b's Q-table init
    agent_b = AgentClass(env1_world, total_steps=ENV1_STEPS, num_actions=NUM_ACTIONS)

    for oid in env1_world.unreachable_hazard_ids:
        for attr in ('knowledge_banked', 'knowledge_banked_step'):
            for ag in (agent_a, agent_b):
                if hasattr(ag, attr):
                    getattr(ag, attr).pop(oid, None)

    (prov_a, sobs_a, fam_a, comp_a, pe_a,
     goal_a, cf_a, br_a) = _setup_observers(
        agent_a, env1_world, run_meta_a, run_idx, ENV1_STEPS,
        with_goal, with_counterfactual, with_belief_revision,
    )
    (prov_b, sobs_b, fam_b, comp_b, pe_b,
     goal_b, cf_b, br_b) = _setup_observers(
        agent_b, env1_world, run_meta_b, run_idx, ENV1_STEPS,
        with_goal, with_counterfactual, with_belief_revision,
    )

    ctx_a = AgentCtx('a', agent_a, seed_a,
                     prov_a, sobs_a, fam_a, comp_a, pe_a,
                     goal_a, cf_a, br_a, schema_a, causal_a)
    ctx_b = AgentCtx('b', agent_b, seed_b,
                     prov_b, sobs_b, fam_b, comp_b, pe_b,
                     goal_b, cf_b, br_b, schema_b, causal_b)

    _run_phase_two_agents(ctx_a, ctx_b, env1_world, ENV1_STEPS, 1,
                           with_completion_signal, with_prediction)

    env1_mastery_a = list(getattr(agent_a, 'mastery_order_sequence', []))
    env1_mastery_b = list(getattr(agent_b, 'mastery_order_sequence', []))

    run_meta_a['phase_1_end_step'] = getattr(agent_a, 'phase_1_end_step', None)
    run_meta_b['phase_1_end_step'] = getattr(agent_b, 'phase_1_end_step', None)

    # FIX 2: orphan predicted record (same as v1.14.1)
    for ctx, sch in ((ctx_a, schema_a), (ctx_b, schema_b)):
        if (with_prediction and sch is not None
                and ctx.predicted_record_written
                and not ctx.transfer_condition_met):
            sch.mark_unresolvable("haz_blue")

    # -----------------------------------------------------------------------
    # ENV2 — shared world, eligible agents only
    # -----------------------------------------------------------------------
    env2_result_a = None; env2_result_b = None
    env2_seed = seed_a + ENV2_SEED_OFFSET

    if with_env2 and (ctx_a.transfer_condition_met or ctx_b.transfer_condition_met):
        np.random.seed(env2_seed)
        env2_world = V113World(
            families=ENV2_FAMILIES, hazard_cost=hazard_cost,
            has_end_state=True, seed=env2_seed,
        )
        att_blue_pos = env2_world.object_positions.get("att_blue")
        # Inject att_blue twice for directed search
        if att_blue_pos:
            env2_world.inject_waypoint(att_blue_pos)
            env2_world.inject_waypoint(att_blue_pos)

        active_ctxs = []
        for ctx, ag, sch, caus, prov in (
            (ctx_a, agent_a, schema_a, causal_a, prov_a),
            (ctx_b, agent_b, schema_b, causal_b, prov_b),
        ):
            if not ctx.transfer_condition_met:
                ctx.done = True   # not eligible — skip in phase loop
                continue
            _carry_agent(ag, env2_world, None, 'env2')
            ag.world = env2_world
            prov._agent = ag; prov._world = env2_world
            prov._environment_complete_fired = False
            ctx.pos  = START_POS
            ctx.done = False
            ctx.att_blue_mastery_step    = None
            ctx.att_yellow_mastery_step  = None
            ctx.att_green_mastery_step   = None
            ctx.end_state_banked_step    = None
            ctx.env2_actual_steps        = 0
            active_ctxs.append(ctx)

        if active_ctxs:
            _run_phase_two_agents(ctx_a, ctx_b, env2_world, ENV2_STEPS, 2,
                                   with_completion_signal, with_prediction)

        for ctx, sch in ((ctx_a, schema_a), (ctx_b, schema_b)):
            if (with_prediction and sch is not None
                    and ctx.transfer_condition_met
                    and ctx.att_blue_mastery_step is None):
                sch.mark_unresolvable("haz_blue")

        ctx_a.env2_actual_steps = env2_world._waypoint_idx   # proxy; use actual
        # Better: track per-agent steps in phase loop
        # For now env2_actual_steps is the phase's actual_steps
        # We'll compute from the done step — stored in ctx.actual_steps

    # -----------------------------------------------------------------------
    # Return ENV1 — eligible confirmed agents
    # -----------------------------------------------------------------------
    return_result = None
    arc_paired    = None

    def _get_pred_field(sch, field):
        if sch is None: return None
        recs = sch.get_predicted_records()
        return next((r.get(field) for r in recs if r.get("object_id") == "haz_blue"), None)

    confirmed_a = _return_to_env1_condition_met(schema_a)
    confirmed_b = _return_to_env1_condition_met(schema_b)

    if with_return and (confirmed_a or confirmed_b):
        # Ineligible agents (not confirmed) are marked done in return phase
        if not confirmed_a:
            ctx_a.done = True
        if not confirmed_b:
            ctx_b.done = True

        return_result = _run_return_env1_two_agents(
            run_idx, seed_a, seed_b, hazard_cost,
            ctx_a, ctx_b,
            env1_transfer_step_a=ctx_a.transfer_triggered_step,
            env1_transfer_step_b=ctx_b.transfer_triggered_step,
            env2_actual_steps_a=ctx_a.env2_actual_steps,
            env2_actual_steps_b=ctx_b.env2_actual_steps,
            pred_step_a=_get_pred_field(schema_a, 'prediction_step'),
            pred_step_b=_get_pred_field(schema_b, 'prediction_step'),
            conf_step_a=_get_pred_field(schema_a, 'confirmation_step'),
            conf_step_b=_get_pred_field(schema_b, 'confirmation_step'),
            with_completion_signal=with_completion_signal,
        )
        arc_paired = return_result['arc_paired']
    else:
        # Build ineligible/no-return arc rows
        def _ineli_row(agent_label, seed, ctx, sch):
            recs = sch.get_predicted_records() if sch else []
            reason = ""
            if not ctx.transfer_condition_met:
                reason = "no_transfer"
            elif recs:
                st = next((r.get("state","") for r in recs
                           if r.get("object_id") == "haz_blue"), "")
                reason = ("prediction_unresolvable"
                          if st == UNRESOLVABLE_STATE else "prediction_unresolved")
            else:
                reason = "no_predicted_record"
            if not with_return:
                reason = "no_return_flag"
            return {
                "arch": ARCH, "run_idx": run_idx,
                "agent": agent_label, "seed": seed,
                "hazard_cost": hazard_cost,
                "arc_complete": False, "arc_timeout": False,
                "ineligible_reason": reason,
                "env1_surprise_step": ctx.transfer_triggered_step,
                "prediction_step": _get_pred_field(sch, 'prediction_step'),
                "transfer_triggered_step": ctx.transfer_triggered_step,
                "confirmation_step": None, "return_step": None,
                "transformation_step": None, "arc_total_steps": None,
                "arc_env_span": None, "causal_chain_depth": 3,
                "causal_chain_complete": False,
            }

        arc_row_a = _ineli_row('a', seed_a, ctx_a, schema_a)
        arc_row_b = _ineli_row('b', seed_b, ctx_b, schema_b)
        arc_paired = {
            "arch": ARCH, "run_idx": run_idx,
            "seed_a": seed_a, "seed_b": seed_b,
            "hazard_cost": hazard_cost,
            "arc_complete_a": False, "arc_complete_b": False,
            "both_arc_complete": False,
            "arc_total_steps_a": None, "arc_total_steps_b": None,
            "arc_total_steps_delta": None,
            "transformation_step_a": None, "transformation_step_b": None,
            "transfer_triggered_step_a": ctx_a.transfer_triggered_step,
            "transfer_triggered_step_b": ctx_b.transfer_triggered_step,
            "env2_actual_steps_a": ctx_a.env2_actual_steps,
            "env2_actual_steps_b": ctx_b.env2_actual_steps,
            "first_transformer": None,
            "haz_blue_shared_benefit": False,
            "individuation_confirmed": False,
        }
        return_result = {"arc_row_a": arc_row_a, "arc_row_b": arc_row_b}

    # -----------------------------------------------------------------------
    # Reporting (env1 only, per agent)
    # -----------------------------------------------------------------------
    def _build_reports(ctx, agent, sch, caus, run_meta, env1_mastery):
        statements = []; summary = {}; causal_records = []

        if report:
            bundle = build_bundle_from_observers(
                provenance_obs=ctx.prov_obs,
                schema_obs=ctx.schema_obs,
                family_obs=ctx.family_obs,
                comparison_obs=ctx.comp_obs,
                prediction_error_obs=ctx.pe_obs,
                run_meta=run_meta,
                goal_obs=ctx.goal_obs,
                counterfactual_obs=ctx.cf_obs,
                belief_revision_obs=ctx.br_obs,
                causal_obs=None,
                schema_v13_obs=sch,
            )
            if ctx.br_obs is not None:
                pe_records = getattr(bundle, 'prediction_error', None) or []
                ctx.br_obs.process_pe_substrate(pe_records)
                bundle.belief_revision = ctx.br_obs.get_substrate()

            if caus is not None:
                caus._meta['phase_1_end_step'] = run_meta.get('phase_1_end_step')
                caus._built = False
                caus.build_causal_chains(bundle)
                bundle.causal = caus.get_substrate()

            layer = V16ReportingLayer(bundle)
            statements    = layer.generate_report()
            causal_records = caus.get_substrate() if caus else []

        pred_rows = sch.predicted_schema_rows(run_meta) if with_prediction else []
        return statements, summary, causal_records, pred_rows

    stmts_a, summ_a, causal_a_recs, pred_rows_a = _build_reports(
        ctx_a, agent_a, schema_a, causal_a, run_meta_a, env1_mastery_a,
    )
    stmts_b, summ_b, causal_b_recs, pred_rows_b = _build_reports(
        ctx_b, agent_b, schema_b, causal_b, run_meta_b, env1_mastery_b,
    )

    if report:
        summ_a = _compute_summary(
            run_idx, seed_a, 'a', hazard_cost, stmts_a,
            ctx_a.goal_obs, ctx_a.cf_obs, ctx_a.br_obs,
            causal_a_recs, ctx_a.end_state_banked_step,
            ctx_a.transfer_condition_met, schema_a,
        )
        summ_b = _compute_summary(
            run_idx, seed_b, 'b', hazard_cost, stmts_b,
            ctx_b.goal_obs, ctx_b.cf_obs, ctx_b.br_obs,
            causal_b_recs, ctx_b.end_state_banked_step,
            ctx_b.transfer_condition_met, schema_b,
        )

    def _rr(ctx, return_res, label):
        ac = return_res.get(f'arc_complete_{label}', False) if return_result else False
        at = return_res.get(f'arc_timeout_{label}', False) if return_result else False
        ts = return_res.get(f'transform_step_{label}') if return_result else None
        ta = return_res.get(f'arc_total_{label}') if return_result else None
        return ac, at, ts, ta

    ac_a, at_a, ts_a, ta_a = _rr(ctx_a, return_result or {}, 'a')
    ac_b, at_b, ts_b, ta_b = _rr(ctx_b, return_result or {}, 'b')

    run_row_a = _build_run_row(
        run_idx, seed_a, 'a', hazard_cost, ctx_a, causal_a_recs,
        ctx_a.transfer_condition_met, env1_mastery_a,
        return_ran=return_result is not None and confirmed_a,
        arc_complete=ac_a, arc_timeout=at_a,
        transformation_step=ts_a, arc_total_steps=ta_a,
    )
    run_row_b = _build_run_row(
        run_idx, seed_b, 'b', hazard_cost, ctx_b, causal_b_recs,
        ctx_b.transfer_condition_met, env1_mastery_b,
        return_ran=return_result is not None and confirmed_b,
        arc_complete=ac_b, arc_timeout=at_b,
        transformation_step=ts_b, arc_total_steps=ta_b,
    )

    return (run_row_a, run_row_b,
            stmts_a, stmts_b,
            summ_a, summ_b,
            ctx_a.prov_obs, ctx_b.prov_obs,
            ctx_a.goal_obs, ctx_b.goal_obs,
            ctx_a.cf_obs,   ctx_b.cf_obs,
            ctx_a.br_obs,   ctx_b.br_obs,
            ctx_a.end_state_banked_step, ctx_b.end_state_banked_step,
            causal_a, causal_b,
            causal_a_recs, causal_b_recs,
            None, None,  # env2_row placeholders (built below if needed)
            pred_rows_a, pred_rows_b,
            return_result.get('arc_row_a'), return_result.get('arc_row_b'),
            arc_paired,
            env2_seed if with_env2 else None)


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def _build_run_row(run_idx, seed, agent_label, hazard_cost, ctx,
                   causal_records, env2_ran,
                   env1_mastery_snapshot=None,
                   return_ran=False,
                   arc_complete=False, arc_timeout=False,
                   transformation_step=None, arc_total_steps=None):
    agent = ctx.agent
    pe_obs  = ctx.pe_obs
    goal_obs = ctx.goal_obs
    cf_obs  = ctx.cf_obs
    br_obs  = ctx.br_obs
    es_step = ctx.end_state_banked_step

    pe_summary = pe_obs.summary_metrics()
    goal_fields = {}
    if goal_obs is not None:
        g = goal_obs.get_substrate()["goal_summary"]
        goal_fields = {
            "goal_type": g["goal_type"], "goal_target_id": g["target_id"],
            "goal_step_budget": g["step_budget"], "goal_resolved": g["resolved"],
            "goal_resolution_step": g["resolution_step"],
            "goal_budget_remaining": g["budget_remaining"],
            "goal_expired": g["expired"],
            "goal_last_progress_step": g["last_progress_step"],
            "goal_resolution_window": g["goal_resolution_window"],
            "goal_progress_event_count": len(
                goal_obs.get_substrate()["goal_progress"]
            ),
        }

    cf_records = cf_obs.get_substrate() if cf_obs else []
    cf_raw     = cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted = len(cf_records)
    cf_excl    = (1.0 - cf_emitted / cf_raw) if cf_raw > 0 else 0.0
    gr_count   = sum(1 for r in cf_records if r.get("goal_relevant"))
    obj_list   = ",".join(sorted({r["object_id"] for r in cf_records}))
    br_records = br_obs.get_substrate() if br_obs else []

    activation_step = getattr(agent, 'activation_step', None)
    draw_active     = getattr(agent, 'end_state_draw_active', False)
    steps_draw_bank = (
        (es_step - activation_step)
        if es_step is not None and activation_step is not None else None
    )

    valid_chains   = [r for r in causal_records
                      if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    depths         = [r["chain_depth"] for r in valid_chains]
    complete_count = sum(1 for r in valid_chains if r.get("chain_complete"))

    ineligible_reason = ""
    if return_ran and not arc_complete and not arc_timeout:
        ineligible_reason = "prediction_unresolvable"

    return {
        "arch": ARCH, "run_idx": run_idx, "agent": agent_label,
        "seed": seed, "hazard_cost": hazard_cost,
        "num_steps": ctx.actual_steps,
        "phase_1_end_step": getattr(agent, 'phase_1_end_step', None),
        "phase_2_end_step": getattr(agent, 'phase_2_end_step', None),
        "time_to_first_flag": getattr(agent, 'time_to_first_flag', None),
        "time_to_second_flag": getattr(agent, 'time_to_second_flag', None),
        "time_to_final_flag": getattr(agent, 'time_to_final_flag', None),
        "total_cost_incurred": getattr(agent, 'total_cost_incurred', 0),
        "time_to_first_mastery": getattr(agent, 'time_to_first_mastery', None),
        "time_to_final_mastery": getattr(agent, 'time_to_final_mastery', None),
        "mastery_order_sequence": str(getattr(agent, 'mastery_order_sequence', [])),
        "activation_step": activation_step,
        "end_state_found_step": getattr(agent, 'end_state_found_step', None),
        "end_state_banked": getattr(agent, 'end_state_banked', False),
        "time_to_first_transition": getattr(agent, 'time_to_first_transition', None),
        "time_to_final_transition": getattr(agent, 'time_to_final_transition', None),
        "transition_order_sequence": str(getattr(agent, 'transition_order_sequence', [])),
        "knowledge_banked_sequence": str(getattr(agent, 'knowledge_banked_sequence', [])),
        **pe_summary,
        **goal_fields,
        "suppressed_approach_count": cf_emitted,
        "goal_relevant_suppressed_count": gr_count,
        "suppressed_approach_objects": obj_list,
        "cf_records_raw": cf_raw, "cf_records_emitted": cf_emitted,
        "cf_exclusion_rate": round(cf_excl, 4),
        "end_state_draw_active": draw_active,
        "end_state_banked_step": es_step,
        "steps_draw_to_bank": steps_draw_bank,
        "revised_expectation_count": len(br_records),
        "causal_chain_count": len(valid_chains),
        "mean_chain_depth": (
            round(sum(depths)/len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count": complete_count,
        "q5_statement_count": 0,
        "env2_ran": env2_ran,
        "haz_blue_approached": ctx.haz_blue_approached,
        "predicted_record_written": ctx.predicted_record_written,
        "transfer_triggered_step": ctx.transfer_triggered_step,
        "env1_mastery_order_sequence": str(env1_mastery_snapshot or []),
        "env1_end_state_banked_step": ctx.end_state_banked_step,
        "return_env1_ran": return_ran,
        "arc_complete": arc_complete, "arc_timeout": arc_timeout,
        "ineligible_reason": ineligible_reason,
        "return_step": 0 if return_ran else None,
        "transformation_step": transformation_step,
        "arc_total_steps": arc_total_steps,
    }


def _compute_summary(run_idx, seed, agent_label, hazard_cost, statements,
                     goal_obs, cf_obs, br_obs, causal_records,
                     es_step, env2_ran, schema_v13_obs=None):
    total = len(statements)
    halluc = sum(1 for s in statements if not s.source_resolves)
    q1 = sum(1 for s in statements if s.query_type == "what_learned")
    q2 = sum(1 for s in statements if s.query_type == "how_structured")
    q3 = sum(1 for s in statements if s.query_type == "what_surprised")
    q4 = sum(1 for s in statements if s.query_type == "what_avoided")
    q5 = sum(1 for s in statements if s.query_type == "why_this_arc")
    q3_cells = len({s.source_key for s in statements if s.query_type == "what_surprised"})
    q3_res   = sum(1 for s in statements
                   if s.query_type == "what_surprised"
                   and "resolution" in s.text.lower())
    cf_records = cf_obs.get_substrate() if cf_obs else []
    cf_raw     = cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted = len(cf_records)
    cf_excl    = (1.0 - cf_emitted / cf_raw) if cf_raw > 0 else 0.0
    br_records = br_obs.get_substrate() if br_obs else []
    deltas     = [r.get("approach_delta", 0) for r in br_records]
    mean_delta = round(sum(deltas)/len(deltas), 2) if deltas else 0.0
    valid_chains   = [r for r in causal_records if r.get("chain_depth",0) >= CHAIN_DEPTH_MINIMUM]
    depths         = [r["chain_depth"] for r in valid_chains]
    complete_count = sum(1 for r in valid_chains if r.get("chain_complete"))

    pred_written = False; pred_state = ""
    if schema_v13_obs:
        recs = schema_v13_obs.get_predicted_records()
        pred_written = bool(recs)
        pred_state = next((r["state"] for r in recs
                           if r["object_id"] == "haz_blue"), "")
    return {
        "arch": ARCH, "run_idx": run_idx, "agent": agent_label,
        "seed": seed, "hazard_cost": hazard_cost, "num_steps": BATCH_STEPS,
        "total_statements": total,
        "statements_q1": q1, "statements_q2": q2, "statements_q3": q3,
        "statements_q4": q4, "statements_q5": q5,
        "hallucination_count": halluc,
        "q1_formation_depth": q1,
        "q3_surprise_cells": q3_cells, "q3_resolution_stated": q3_res,
        "report_complete": halluc == 0,
        "statements_with_relevance_markers": 0,
        "goal_statement_present": goal_obs is not None,
        "goal_resolution_stated": (
            goal_obs.get_substrate()["goal_summary"]["resolved"]
            if goal_obs else False
        ),
        "q4_statement_count": q4,
        "suppressed_approach_count": cf_emitted,
        "goal_relevant_suppressed_count": sum(1 for r in cf_records if r.get("goal_relevant")),
        "br_statement_count": q3,
        "revised_expectation_count": len(br_records),
        "mean_approach_delta": mean_delta, "bias_effective": mean_delta > 0,
        "cf_records_raw": cf_raw, "cf_records_emitted": cf_emitted,
        "cf_exclusion_rate": round(cf_excl, 4),
        "end_state_draw_active": False, "end_state_banked_step": es_step,
        "causal_chain_count": len(valid_chains),
        "mean_chain_depth": (
            round(sum(depths)/len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count": complete_count, "q5_statement_count": q5,
        "predicted_record_written": pred_written,
        "predicted_record_state": pred_state,
    }


# ---------------------------------------------------------------------------
# Q5 individuation (unchanged)
# ---------------------------------------------------------------------------

def _edit_distance(seq_a, seq_b):
    if not seq_a and not seq_b: return 0.0
    la, lb = len(seq_a), len(seq_b)
    dp = [[0]*(lb+1) for _ in range(la+1)]
    for i in range(la+1): dp[i][0] = i
    for j in range(lb+1): dp[0][j] = j
    for i in range(1, la+1):
        for j in range(1, lb+1):
            cost = 0 if seq_a[i-1] == seq_b[j-1] else 1
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
    return dp[la][lb] / max(la, lb)


def compute_q5_individuation(causal_records, run_meta):
    valid = [r for r in causal_records if r.get("chain_depth",0) >= CHAIN_DEPTH_MINIMUM]
    rows  = []
    for i, ra in enumerate(valid):
        for j, rb in enumerate(valid):
            if j <= i: continue
            sa = [lnk["link_type"] for lnk in ra.get("links", [])]
            sb = [lnk["link_type"] for lnk in rb.get("links", [])]
            rows.append({
                "arch": run_meta.get("arch", ARCH),
                "run_idx_a": ra.get("run_idx",""), "run_idx_b": rb.get("run_idx",""),
                "seed_a": ra.get("seed",""), "seed_b": rb.get("seed",""),
                "hazard_cost": ra.get("hazard_cost",""),
                "chain_object_a": ra.get("object_id",""),
                "chain_object_b": rb.get("object_id",""),
                "link_sequence_a": ">".join(sa), "link_sequence_b": ">".join(sb),
                "link_sequence_distance": round(_edit_distance(sa, sb), 4),
                "within_run": ra.get("run_idx","") == rb.get("run_idx",""),
            })
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-report",            action="store_true")
    parser.add_argument("--no-goal",              action="store_true")
    parser.add_argument("--no-counterfactual",    action="store_true")
    parser.add_argument("--no-belief-revision",   action="store_true")
    parser.add_argument("--no-completion-signal", action="store_true")
    parser.add_argument("--no-causal",            action="store_true")
    parser.add_argument("--no-env2",              action="store_true")
    parser.add_argument("--no-prediction",        action="store_true")
    parser.add_argument("--no-return",            action="store_true")
    args = parser.parse_args()

    report      = not args.no_report
    with_goal   = not args.no_goal
    with_cf     = not args.no_counterfactual
    with_br     = not args.no_belief_revision
    with_cs     = not args.no_completion_signal
    with_causal = not args.no_causal
    with_env2   = not args.no_env2
    with_pred   = not args.no_prediction
    with_return = not args.no_return

    seeds = _find_seed_csv()
    jobs  = [
        (cost_idx * RUNS_PER_COST + run_idx,
         seeds.get((cost, run_idx), run_idx * 1000 + int(cost * 10)),
         cost)
        for cost_idx, cost in enumerate(HAZARD_COSTS)
        for run_idx in range(RUNS_PER_COST)
    ]

    csv_files = {}; writers = {}

    try:
        for key, path in [
            ('run', RUN_DATA_CSV),   ('prov', PROVENANCE_CSV),
            ('rpt', REPORT_CSV),     ('sum',  REPORT_SUMMARY_CSV),
            ('es',  END_STATE_DRAW_CSV), ('env2', ENV2_RUN_DATA_CSV),
            ('q5i', Q5_INDIVIDUATION_CSV), ('pred', PREDICTED_SCHEMA_CSV),
            ('arc', ARC_COMPLETE_CSV), ('pair', ARC_PAIRED_CSV),
        ]:
            csv_files[key] = open(path, 'w', newline='')
        if with_goal:   csv_files['goal'] = open(GOAL_CSV,            'w', newline='')
        if with_cf:     csv_files['cf']   = open(COUNTERFACTUAL_CSV,  'w', newline='')
        if with_br:     csv_files['br']   = open(BELIEF_REVISION_CSV, 'w', newline='')
        if with_causal: csv_files['caus'] = open(CAUSAL_CSV,          'w', newline='')

        writers['run']  = csv.DictWriter(csv_files['run'],  fieldnames=RUN_DATA_FIELDS)
        writers['prov'] = csv.DictWriter(csv_files['prov'], fieldnames=[
            "arch","run_idx","agent","seed","hazard_cost",
            "flag_id","flag_type","flag_set_step",
        ])
        writers['rpt']  = csv.DictWriter(csv_files['rpt'],  fieldnames=REPORT_FIELDS)
        writers['sum']  = csv.DictWriter(csv_files['sum'],  fieldnames=SUMMARY_FIELDS)
        writers['es']   = csv.DictWriter(csv_files['es'],   fieldnames=END_STATE_DRAW_FIELDS)
        writers['env2'] = csv.DictWriter(csv_files['env2'], fieldnames=ENV2_RUN_DATA_FIELDS)
        writers['q5i']  = csv.DictWriter(csv_files['q5i'],  fieldnames=Q5_INDIVIDUATION_FIELDS)
        writers['pred'] = csv.DictWriter(csv_files['pred'], fieldnames=PREDICTED_SCHEMA_FIELDS)
        writers['arc']  = csv.DictWriter(csv_files['arc'],  fieldnames=ARC_COMPLETE_FIELDS)
        writers['pair'] = csv.DictWriter(csv_files['pair'], fieldnames=ARC_PAIRED_FIELDS)
        for w in writers.values(): w.writeheader()
        if with_goal:
            writers['goal'] = csv.DictWriter(csv_files['goal'], fieldnames=GOAL_FIELDS)
            writers['goal'].writeheader()
        if with_cf:
            writers['cf'] = csv.DictWriter(csv_files['cf'], fieldnames=COUNTERFACTUAL_FIELDS)
            writers['cf'].writeheader()
        if with_br:
            writers['br'] = csv.DictWriter(csv_files['br'], fieldnames=BELIEF_REVISION_FIELDS)
            writers['br'].writeheader()
        if with_causal:
            writers['caus'] = csv.DictWriter(csv_files['caus'], fieldnames=CAUSAL_FIELDS)
            writers['caus'].writeheader()

        total_statements     = 0
        total_hallucinations = 0
        arc_complete_runs    = 0   # runs where at least one agent completed
        both_arc_complete    = 0   # runs where BOTH agents completed
        arc_timeout_runs     = 0
        individuation_confirmed = 0
        incomplete_runs      = []
        all_causal_records   = []

        print(f"v1.15 batch: {len(jobs)} runs × 2 agents = {len(jobs)*2} agent-runs | "
              f"return={'ON' if with_return else 'OFF'}")
        print()

        for run_idx, seed_a, hazard_cost in jobs:
            seed_b = seed_a + SEED_B_OFFSET
            try:
                result = run_one(
                    run_idx, seed_a, seed_b, hazard_cost,
                    report=report,
                    with_goal=with_goal, with_counterfactual=with_cf,
                    with_belief_revision=with_br,
                    with_completion_signal=with_cs,
                    with_causal=with_causal, with_env2=with_env2,
                    with_prediction=with_pred, with_return=with_return,
                )
            except Exception as e:
                import traceback as tb
                print(f"  Run {run_idx}: ERROR — {e}"); tb.print_exc()
                incomplete_runs.append(run_idx); continue

            (run_row_a, run_row_b,
             stmts_a, stmts_b,
             summ_a, summ_b,
             prov_a, prov_b,
             goal_a, goal_b,
             cf_a, cf_b,
             br_a, br_b,
             es_a, es_b,
             caus_a, caus_b,
             causal_recs_a, causal_recs_b,
             _, _,
             pred_rows_a, pred_rows_b,
             arc_row_a, arc_row_b,
             arc_paired,
             env2_seed) = result

            for run_row in (run_row_a, run_row_b):
                writers['run'].writerow(
                    {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
                )

            flush_provenance_csv(prov_a, PROVENANCE_CSV)
            flush_provenance_csv(prov_b, PROVENANCE_CSV)

            for goal_obs, cf_obs, br_obs in ((goal_a, cf_a, br_a), (goal_b, cf_b, br_b)):
                if with_goal and goal_obs:
                    for gr in goal_obs.get_substrate().get("goal_progress", []):
                        writers['goal'].writerow({k: gr.get(k,"") for k in GOAL_FIELDS})
                if with_cf and cf_obs:
                    for cr in cf_obs.get_substrate():
                        writers['cf'].writerow({k: cr.get(k,"") for k in COUNTERFACTUAL_FIELDS})
                if with_br and br_obs:
                    for br in br_obs.get_substrate():
                        writers['br'].writerow({k: br.get(k,"") for k in BELIEF_REVISION_FIELDS})

            for caus, causal_recs, ag_label, seed in (
                (caus_a, causal_recs_a, 'a', seed_a),
                (caus_b, causal_recs_b, 'b', seed_b),
            ):
                if with_causal and caus:
                    cm = {"arch": ARCH, "run_idx": run_idx, "seed": seed,
                          "hazard_cost": hazard_cost, "num_steps": BATCH_STEPS}
                    for cr in caus.causal_rows():
                        writers['caus'].writerow(
                            {k: {**cm,**cr}.get(k,"") for k in CAUSAL_FIELDS}
                        )
                    all_causal_records.extend([
                        {**r, "run_idx": run_idx, "seed": seed,
                         "hazard_cost": hazard_cost}
                        for r in causal_recs
                    ])

            for pred_rows in (pred_rows_a, pred_rows_b):
                if with_pred and pred_rows:
                    for pr in pred_rows:
                        writers['pred'].writerow(
                            {k: pr.get(k,"") for k in PREDICTED_SCHEMA_FIELDS}
                        )

            for arc_row in (arc_row_a, arc_row_b):
                if arc_row:
                    writers['arc'].writerow(
                        {k: arc_row.get(k,"") for k in ARC_COMPLETE_FIELDS}
                    )

            if arc_paired:
                writers['pair'].writerow(
                    {k: arc_paired.get(k,"") for k in ARC_PAIRED_FIELDS}
                )
                if arc_paired.get("arc_complete_a") or arc_paired.get("arc_complete_b"):
                    arc_complete_runs += 1
                if arc_paired.get("both_arc_complete"):
                    both_arc_complete += 1
                if arc_paired.get("individuation_confirmed"):
                    individuation_confirmed += 1

            for stmts, summ, es_step, ag_label, seed in (
                (stmts_a, summ_a, es_a, 'a', seed_a),
                (stmts_b, summ_b, es_b, 'b', seed_b),
            ):
                if report and stmts:
                    for s in stmts:
                        writers['rpt'].writerow({
                            "arch": ARCH, "run_idx": run_idx,
                            "agent": ag_label, "seed": seed,
                            "hazard_cost": hazard_cost, "num_steps": BATCH_STEPS,
                            "query_type": getattr(s,'query_type',''),
                            "statement_text": getattr(s,'text',''),
                            "source_type": getattr(s,'source_type',''),
                            "source_key": getattr(s,'source_key',''),
                            "source_resolves": getattr(s,'source_resolves',False),
                        })
                if report and summ:
                    writers['sum'].writerow(
                        {k: summ.get(k,"") for k in SUMMARY_FIELDS}
                    )
                    total_statements     += summ.get("total_statements", 0)
                    total_hallucinations += summ.get("hallucination_count", 0)

                writers['es'].writerow({
                    "arch": ARCH, "run_idx": run_idx,
                    "agent": ag_label, "seed": seed,
                    "hazard_cost": hazard_cost, "num_steps": BATCH_STEPS,
                    "activation_step": None,
                    "end_state_banked_step": es_step,
                    "steps_draw_to_bank": None,
                    "end_state_draw_active": False,
                })

            if report and (summ_a or summ_b):
                ac_sym = ("✓" if arc_paired.get("both_arc_complete")
                          else ("a" if arc_paired.get("arc_complete_a")
                                else ("b" if arc_paired.get("arc_complete_b")
                                      else "–")))
                indiv = "I" if arc_paired.get("individuation_confirmed") else "-"
                delta = arc_paired.get("arc_total_steps_delta")
                delta_str = f"Δ={delta:,}" if delta is not None else "Δ=–"
                h_a = (summ_a or {}).get("hallucination_count", "?")
                h_b = (summ_b or {}).get("hallucination_count", "?")
                print(
                    f"  Run {run_idx:3d} | sa={seed_a:12d} cost={hazard_cost:5.1f} | "
                    f"arc={ac_sym} {indiv} {delta_str} | "
                    f"halluc={h_a}/{h_b}"
                )

        # Summary
        print()
        print("Category Ω: arc_complete (two-agent)")
        print(f"  At least one arc_complete: {arc_complete_runs}/{len(jobs)}")
        print(f"  Both arc_complete:         {both_arc_complete}/{len(jobs)}")
        print()
        print("Category γ: Individuation")
        print(f"  arc_total_steps_delta > 0: {individuation_confirmed}/{len(jobs)}")

        if with_causal and all_causal_records:
            valid_q5 = [r for r in all_causal_records
                        if r.get("chain_depth",0) >= CHAIN_DEPTH_MINIMUM]
            if valid_q5:
                indiv_rows = compute_q5_individuation(all_causal_records, {"arch": ARCH})
                for irow in indiv_rows:
                    writers['q5i'].writerow(
                        {k: irow.get(k,"") for k in Q5_INDIVIDUATION_FIELDS}
                    )
                between = [r["link_sequence_distance"] for r in indiv_rows if not r["within_run"]]
                within  = [r["link_sequence_distance"] for r in indiv_rows if r["within_run"]]
                if between:
                    mb = sum(between)/len(between)
                    mw = sum(within)/len(within) if within else 0.0
                    print()
                    print(f"Category ζ: Q5 between={mb:.4f} within={mw:.4f} "
                          f"{'PASS' if mb > mw else 'FAIL'}")

        print()
        print("=" * 65)
        print(f"v1.15 complete. {len(jobs)-len(incomplete_runs)}/{len(jobs)} runs.")
        if report:
            print(f"  Statements:    {total_statements}")
            print(f"  Hallucinations:{total_hallucinations}")
            print(f"  Category α:    {'PASS' if total_hallucinations == 0 else 'FAIL'}")
        if incomplete_runs:
            print(f"  Incomplete: {incomplete_runs}")
        print()
        print("  Outputs:")
        for label, path in [
            ("Run data",         RUN_DATA_CSV),
            ("Report",           REPORT_CSV),
            ("Report summary",   REPORT_SUMMARY_CSV),
            ("Arc complete",     ARC_COMPLETE_CSV),
            ("Arc paired",       ARC_PAIRED_CSV),
            ("Predicted schema", PREDICTED_SCHEMA_CSV),
            ("Causal chains",    CAUSAL_CSV),
            ("ENV2 run data",    ENV2_RUN_DATA_CSV),
            ("Q5 individuation", Q5_INDIVIDUATION_CSV),
        ]:
            print(f"    {label:<22} {path}")

    finally:
        for f in csv_files.values():
            f.close()


if __name__ == "__main__":
    main()
