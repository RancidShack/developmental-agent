"""
curiosity_agent_v1_14_batch.py
--------------------------------
v1.14 batch runner: The Reparative Return and the First Complete
Cross-Environment Causal Chain.

CHANGES FROM V1.13.8
  - RETURN_ENV1_FAMILIES added: full BLUE family (att_blue + haz_blue).
    att_blue at ENV2 position (5,6,10). haz_blue at ENV1 position (7,8,3).
    No unreachable hazards. Pre-registered §2.2.
  - Return ENV1 phase added after ENV2 confirmation. Gate:
    predicted_record_state == 'confirmed'. Pre-registered §2.1.
  - carry_agent for return ENV1 preserves mastery_flag['att_blue'] = 1.
    CRITICAL INVARIANT: V110Agent.check_competency_unlocks fires on
    first contact → family_precondition_attractor['haz_blue'] = 'att_blue'
    → mastery_flag['att_blue'] == 1 → transform_to_knowledge('haz_blue').
    Pre-registered §2.4.
  - ENV2 early exit changed: att_blue_mastery_step (prediction confirmed)
    replaces end_state_banked_step. The completion signal for ENV2 is
    prediction confirmation; end_state banking was 0/32 in v1.13.8.
    Pre-registered §2.9 (arc_complete ≠ environment_complete).
  - arc_complete_v1_14.csv added. Pre-registered §2.6.
  - arc_complete, arc_timeout, ineligible_reason, return_step,
    transformation_step, arc_total_steps added to run_data. §2.6.
  - ARCH = v1_14. Seed source = run_data_v1_13_8.csv.

ADDITIVE DISCIPLINE
  --no-return:  skips return ENV1; v1.13.8-equivalent output for
                comparison baseline.
  All v1.13.8 flags (--no-prediction, --no-env2, etc.) inherited.

PRE-REGISTRATION: v1_14_pre_registration.md (8 May 2026).
"""

import argparse
import csv
import os

import numpy as np

import v1_13_observer_substrates  # noqa: F401
from v1_13_observer_substrates import (
    build_bundle_from_observers, PREDICTION_FAMILY_MINIMUM,
)

from v1_13_world import (
    V113World, ENV1_FAMILIES, ENV2_FAMILIES, NUM_ACTIONS,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ,
    PERCEPTION_RADIUS,
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

SEED_CSV_PRIMARY     = "run_data_v1_13_8.csv"
RUN_DATA_CSV         = "run_data_v1_14.csv"
PROVENANCE_CSV       = "provenance_v1_14.csv"
GOAL_CSV             = "goal_v1_14.csv"
COUNTERFACTUAL_CSV   = "counterfactual_v1_14.csv"
BELIEF_REVISION_CSV  = "belief_revision_v1_14.csv"
CAUSAL_CSV           = "causal_v1_14.csv"
REPORT_CSV           = "report_v1_14.csv"
REPORT_SUMMARY_CSV   = "report_summary_v1_14.csv"
END_STATE_DRAW_CSV   = "end_state_draw_log_v1_14.csv"
ENV2_RUN_DATA_CSV    = "env2_run_data_v1_14.csv"
Q5_INDIVIDUATION_CSV = "q5_individuation_v1_14.csv"
PREDICTED_SCHEMA_CSV = "predicted_schema_v1_14.csv"
ARC_COMPLETE_CSV     = "arc_complete_v1_14.csv"        # v1.14 new

ENV1_STEPS        = 1_000_000
ENV2_STEPS        =   800_000
RETURN_ENV1_STEPS =   200_000    # generous; transform fires on first contact
BATCH_STEPS       = ENV1_STEPS
HAZARD_COSTS      = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST     = 10
ARCH              = "v1_14"
ENV2_SEED_OFFSET  = 10_000
RETURN_SEED_OFFSET = 20_000

# ---------------------------------------------------------------------------
# Return ENV1 families (v1.14 new)
# Full BLUE family: att_blue at ENV2 position, haz_blue at ENV1 position.
# No unreachable_hazards — haz_blue is completable because att_blue mastery
# is carried from ENV2 (mastery_flag['att_blue'] = 1).
# ---------------------------------------------------------------------------

RETURN_ENV1_FAMILIES = [
    {
        "colour":   GREEN,
        "dist_id":  "dist_green",
        "dist_pos": (3.0, 9.0, 3.0),    # same as ENV1
        "att_id":   "att_green",
        "att_pos":  (2.0, 11.0, 2.0),   # same as ENV1
        "att_form": SQUARE_2D,
        "haz_id":   "haz_green",
        "haz_pos":  (9.0, 10.0, 8.0),   # same as ENV1
        "haz_form": SPHERE_3D,
    },
    {
        "colour":   YELLOW,
        "dist_id":  "dist_yellow",
        "dist_pos": (8.0, 3.0, 3.0),    # same as ENV1
        "att_id":   "att_yellow",
        "att_pos":  (10.0, 2.0, 2.0),   # same as ENV1
        "att_form": TRIANGLE_2D,
        "haz_id":   "haz_yellow",
        "haz_pos":  (3.0, 5.0, 7.0),    # same as ENV1
        "haz_form": PYRAMID_3D,
    },
    {
        "colour":   BLUE,
        "dist_id":  None,
        "dist_pos": None,
        "att_id":   "att_blue",
        "att_pos":  (5.0, 6.0, 10.0),   # same as ENV2 att_blue
        "att_form": CIRCLE_2D,
        "haz_id":   "haz_blue",          # PRESENT AND REACHABLE
        "haz_pos":  (7.0, 8.0, 3.0),    # same as ENV1 haz_blue
        "haz_form": SPHERE_3D,
    },
]

# Hazards completed in original ENV1 — pre-transitioned in return ENV1.
RETURN_ENV1_PRECOMPLETED = [
    "haz_yellow", "haz_green",
    "haz_unaff_0", "haz_unaff_1", "haz_unaff_2",
]

# ---------------------------------------------------------------------------
# Field definitions (v1.13.8 preserved; v1.14 appended)
# ---------------------------------------------------------------------------

RUN_DATA_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
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
    "env2_ran",
    "haz_blue_approached",
    "predicted_record_written",
    "transfer_triggered_step",
    "env1_mastery_order_sequence",
    "env1_end_state_banked_step",
    # v1.14 new
    "return_env1_ran",
    "arc_complete",
    "arc_timeout",
    "ineligible_reason",
    "return_step",
    "transformation_step",
    "arc_total_steps",
]

ARC_COMPLETE_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost",
    "arc_complete", "arc_timeout", "ineligible_reason",
    "env1_surprise_step",
    "prediction_step",
    "transfer_triggered_step",
    "confirmation_step",
    "return_step",
    "transformation_step",
    "arc_total_steps",
    "arc_env_span",
    "causal_chain_depth",
    "causal_chain_complete",
]

REPORT_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "query_type", "statement_text",
    "source_type", "source_key", "source_resolves",
]

SUMMARY_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "total_statements", "statements_q1", "statements_q2",
    "statements_q3", "statements_q4", "statements_q5",
    "hallucination_count",
    "q1_formation_depth", "q3_surprise_cells", "q3_resolution_stated",
    "report_complete",
    "statements_with_relevance_markers",
    "goal_statement_present", "goal_resolution_stated",
    "q4_statement_count",
    "suppressed_approach_count", "goal_relevant_suppressed_count",
    "br_statement_count", "revised_expectation_count",
    "mean_approach_delta", "bias_effective",
    "cf_records_raw", "cf_records_emitted", "cf_exclusion_rate",
    "end_state_draw_active", "end_state_banked_step",
    "causal_chain_count", "mean_chain_depth", "complete_chain_count",
    "q5_statement_count",
    "predicted_record_written",
    "predicted_record_state",
]

END_STATE_DRAW_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "activation_step", "end_state_banked_step",
    "steps_draw_to_bank", "end_state_draw_active",
]

ENV2_RUN_DATA_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost",
    "env2_seed",
    "env2_activation_step",
    "env2_phase_1_end_step",
    "env2_end_state_banked_step",
    "env2_yellow_pre_transition_entries",
    "env2_yellow_resolution_window",
    "env2_green_pre_transition_entries",
    "env2_green_resolution_window",
    "env2_q5_chain_count",
    "env2_q5_mean_chain_depth",
    "att_blue_mastery_step",
    "att_blue_mastery_env",
    "predicted_record_state_at_run_end",
    "att_blue_sequence_position",
    "env2_mastery_order_sequence",
    "env2_att_yellow_mastery_step",
    "env2_att_green_mastery_step",
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
# Transfer condition helpers (unchanged from v1.13.8)
# ---------------------------------------------------------------------------

def _check_transfer_condition(world, agent, predicted_record_written):
    """ENV1 → ENV2 gate: all completable hazards + all attractors + prediction."""
    if not all(world.knowledge_unlocked.get(h, False)
               for h in world.hazard_cells):
        return False
    mastery_flag = getattr(agent, 'mastery_flag', {})
    if not all(mastery_flag.get(a, 0) == 1
               for a in world.attractor_cells):
        return False
    if not predicted_record_written:
        return False
    return True


# ---------------------------------------------------------------------------
# Return-to-ENV1 gate (v1.14 new)
# ---------------------------------------------------------------------------

def _return_to_env1_condition_met(schema_v13_obs):
    """ENV2 → Return ENV1 gate: predicted_record_state == 'confirmed'.

    Distinct from environment_complete (end_state banked) and from
    transfer_condition (ENV1→ENV2 gate). The agent returns to finish
    what it started because it has earned the competency, not because
    the environment is exhausted.
    """
    if schema_v13_obs is None:
        return False
    for rec in schema_v13_obs.get_predicted_records():
        if rec.get("object_id") == "haz_blue":
            return rec.get("state") == CONFIRMED_STATE
    return False


# ---------------------------------------------------------------------------
# Single environment run (ENV1 and ENV2)
# ---------------------------------------------------------------------------

def _run_environment(
    run_idx, seed, hazard_cost, num_steps,
    families,
    with_goal=True, with_counterfactual=True,
    with_belief_revision=True, with_completion_signal=True,
    with_prediction=True,
    env_number=1,
    carry_agent=None,
    carry_prov_obs=None,
    schema_v13_obs=None,
    causal_obs=None,
    directed_search_target=None,
):
    np.random.seed(seed)

    unreachable = ['haz_blue'] if env_number == 1 else None
    world = V113World(
        families=families,
        hazard_cost=hazard_cost,
        has_end_state=True,
        seed=seed,
        unreachable_hazards=unreachable,
    )

    if env_number == 1:
        hbp = world.object_positions.get("haz_blue")
        if hbp is not None:
            world.inject_waypoint(hbp)
    if env_number == 2 and directed_search_target is not None:
        world.inject_waypoint(directed_search_target)

    AgentClass = V110Agent if with_completion_signal else V17Agent

    if carry_agent is not None:
        agent = carry_agent
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
    else:
        agent = AgentClass(world, total_steps=num_steps,
                           num_actions=NUM_ACTIONS)
        if world.unreachable_hazard_ids:
            for oid in world.unreachable_hazard_ids:
                if hasattr(agent, 'knowledge_banked'):
                    agent.knowledge_banked.pop(oid, None)
                if hasattr(agent, 'knowledge_banked_step'):
                    agent.knowledge_banked_step.pop(oid, None)

    meta = {
        "arch": ARCH, "hazard_cost": hazard_cost,
        "num_steps": num_steps, "run_idx": run_idx,
        "seed": seed, "env": env_number,
    }
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

    schema_obs_base = V13SchemaObserverBase(agent, world, meta)
    family_obs      = V13FamilyObserver(agent, world, meta,
                                        provenance_store=prov_obs)
    comp_obs        = V14ComparisonObserver(family_obs, meta)
    pe_obs          = V15PredictionErrorObserver(agent, world, meta)

    goal_obs = None
    if with_goal:
        goal_type, target_id, step_budget = assign_goal(run_idx, num_steps)
        goal_obs = V18GoalObserver(agent, world, meta,
                                   goal_type, target_id, step_budget)

    cf_obs = None
    if with_counterfactual:
        cf_obs = V19CounterfactualObserver(agent, world, meta, goal_obs=goal_obs)
        cf_obs._records            = []
        cf_obs._last_emission_step = {}
        cf_obs._cf_raw_count       = 0

    br_obs = None
    if with_belief_revision:
        br_obs = V110BeliefRevisionObserver(
            agent, world, meta,
            prediction_error_obs=pe_obs,
            provenance_obs=prov_obs,
            counterfactual_obs=cf_obs,
        )

    observers = [prov_obs, schema_obs_base, family_obs, comp_obs, pe_obs]
    if goal_obs: observers.append(goal_obs)
    if cf_obs:   observers.append(cf_obs)
    if br_obs:   observers.append(br_obs)

    state = world.observe()
    end_state_banked_step    = None
    env2_activation_step     = None
    haz_blue_approached      = False
    transfer_triggered_step  = None
    predicted_record_written = False
    att_blue_mastery_step    = None
    att_yellow_mastery_step  = None
    att_green_mastery_step   = None
    transfer_condition_met   = False
    actual_steps             = num_steps

    for step in range(num_steps):
        for obs in observers:
            obs.on_pre_action(step)

        action = agent.choose_action(state)
        obs_next, contact_oid, moved, cost = world.step(action)
        agent.record_action_outcome(
            contact_oid, moved or contact_oid is not None, cost, world, step
        )

        for obs in observers:
            obs.on_post_event(step)

        intrinsic = (
            agent.novelty_reward(state)
            + agent.preference_reward(state)
            + agent.feature_reward(state)
        )
        if with_completion_signal and isinstance(agent, V110Agent):
            intrinsic += agent.end_state_draw_reward(state, obs_next)

        if br_obs is not None:
            agent_pos = getattr(world, 'agent_pos', None)
            obj_pos   = getattr(world, 'object_positions', {})
            for bias_oid in br_obs.active_biased_objects(step):
                if obj_pos.get(bias_oid) and agent_pos:
                    intrinsic += br_obs.preference_bias_reward(
                        bias_oid, step, moving_closer=True
                    )

        # Directed search bias toward att_blue in ENV2
        if (with_prediction and schema_v13_obs is not None
                and env_number == 2
                and schema_v13_obs.has_pending_prediction("haz_blue")):
            import math
            att_pos   = world.object_positions.get("att_blue")
            agent_pos = getattr(world, 'agent_pos', None)
            if att_pos and agent_pos:
                d = math.sqrt(sum((a-b)**2 for a,b in zip(agent_pos, att_pos)))
                if d > 0:
                    intrinsic += 0.1 / d

        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)
        state = obs_next

        if (env2_activation_step is None
                and getattr(agent, 'activation_step', None) is not None):
            env2_activation_step = step

        if (end_state_banked_step is None
                and getattr(agent, 'end_state_banked', False)):
            prov_obs.on_end_state_banked(step)
            end_state_banked_step = step

        # haz_blue approach detection (ENV1 only)
        if env_number == 1 and not haz_blue_approached:
            hbp = world.object_positions.get("haz_blue")
            if hbp is not None:
                import math as _m
                if _m.sqrt(sum((a-b)**2
                               for a,b in zip(world.agent_pos, hbp))) <= PERCEPTION_RADIUS:
                    haz_blue_approached = True

        # Predicted record construction (ENV1 only)
        if (env_number == 1 and haz_blue_approached
                and step % 500 == 0
                and with_prediction and schema_v13_obs is not None
                and causal_obs is not None
                and not schema_v13_obs.has_pending_prediction("haz_blue")
                and not any(r["object_id"] == "haz_blue"
                            for r in schema_v13_obs.get_predicted_records())):
            n = sum(1 for h in ('haz_yellow', 'haz_green')
                    if world.knowledge_unlocked.get(h, False))
            if n >= PREDICTION_FAMILY_MINIMUM:
                basis = sorted(h for h in ('haz_yellow', 'haz_green')
                               if world.knowledge_unlocked.get(h, False))
                schema_v13_obs.add_predicted_record({
                    "object_id":              "haz_blue",
                    "predicted_precondition": "att_blue",
                    "basis_chains":           basis,
                    "prediction_step":        step,
                    "prediction_env":         env_number,
                })
                predicted_record_written = True

        # att_blue mastery detection (ENV2 only)
        if (env_number == 2 and att_blue_mastery_step is None
                and contact_oid == "att_blue"
                and getattr(agent, 'mastery_flag', {}).get('att_blue', 0) == 1):
            att_blue_mastery_step = step
            if with_prediction and schema_v13_obs is not None:
                schema_v13_obs.confirm_predicted_record(
                    object_id="haz_blue",
                    confirmation_step=step,
                    confirming_env=env_number,
                )

        # Family attractor mastery tracking (ENV2)
        if env_number == 2:
            if (att_yellow_mastery_step is None and contact_oid == "att_yellow"
                    and getattr(agent, 'mastery_flag', {}).get('att_yellow', 0) == 1):
                att_yellow_mastery_step = step
            if (att_green_mastery_step is None and contact_oid == "att_green"
                    and getattr(agent, 'mastery_flag', {}).get('att_green', 0) == 1):
                att_green_mastery_step = step

        # Transfer condition (ENV1)
        if (env_number == 1 and not transfer_condition_met
                and haz_blue_approached):
            pred_ok = with_prediction and schema_v13_obs is not None
            if _check_transfer_condition(
                    world, agent,
                    predicted_record_written if pred_ok else True):
                transfer_condition_met  = True
                transfer_triggered_step = step

        # Early termination
        # ENV1: on transfer condition met
        # ENV2 (v1.14): on att_blue mastery — prediction confirmed.
        #   end_state_banked was 0/32 in v1.13.8; it is not the ENV2 signal.
        if env_number == 1 and transfer_condition_met:
            actual_steps = step + 1; break
        if env_number == 2 and att_blue_mastery_step is not None:
            actual_steps = step + 1; break

    for obs in observers:
        obs.on_run_end(actual_steps)

    if (env_number == 2 and with_prediction and schema_v13_obs is not None
            and att_blue_mastery_step is None):
        schema_v13_obs.mark_unresolvable("haz_blue")

    meta['phase_1_end_step'] = getattr(agent, 'phase_1_end_step', None)
    meta['phase_2_end_step'] = getattr(agent, 'phase_2_end_step', None)

    return dict(
        agent=agent,
        prov_obs=prov_obs,
        schema_obs=schema_obs_base,
        family_obs=family_obs,
        comp_obs=comp_obs,
        pe_obs=pe_obs,
        goal_obs=goal_obs,
        cf_obs=cf_obs,
        br_obs=br_obs,
        end_state_banked_step=end_state_banked_step,
        env2_activation_step=env2_activation_step,
        haz_blue_approached=haz_blue_approached,
        predicted_record_written=predicted_record_written,
        transfer_condition_met=transfer_condition_met,
        transfer_triggered_step=transfer_triggered_step,
        att_blue_mastery_step=att_blue_mastery_step,
        att_yellow_mastery_step=att_yellow_mastery_step,
        att_green_mastery_step=att_green_mastery_step,
        actual_steps=actual_steps,
        meta=meta,
        world=world,
    )


# ---------------------------------------------------------------------------
# Return ENV1 phase (v1.14 new)
# ---------------------------------------------------------------------------

def _run_return_env1(run_idx, seed, hazard_cost,
                     carry_agent, carry_prov_obs,
                     schema_v13_obs, causal_obs,
                     env1_surprise_step, prediction_step,
                     transfer_step, confirmation_step):
    """Return ENV1 with full BLUE family.

    CRITICAL INVARIANT: mastery_flag['att_blue'] = 1 preserved.

    On first contact with any object, V110Agent.check_competency_unlocks
    fires. For haz_blue:
      - world.family_precondition_attractor['haz_blue'] = 'att_blue'
      - mastery_flag.get('att_blue', 0) == 1  ← preserved
      → world.transform_to_knowledge('haz_blue') fires.

    arc_complete detected when world.knowledge_unlocked['haz_blue'] = True.
    Exits immediately. No rumination.
    agent.end_state_banked = True at arc_complete (arc_complete IS the
    end_state signal for return ENV1, per pre-registration §7.1).
    """
    return_seed = seed + RETURN_SEED_OFFSET
    np.random.seed(return_seed)

    return_world = V113World(
        families=RETURN_ENV1_FAMILIES,
        hazard_cost=hazard_cost,
        has_end_state=True,
        seed=return_seed,
        unreachable_hazards=None,    # haz_blue NOT unreachable
    )

    # Pre-transition already-completed hazards → KNOWLEDGE.
    # The agent spent ENV1 completing these. Re-encountering them as
    # KNOWLEDGE is structurally correct and consistent with carried state.
    for oid in RETURN_ENV1_PRECOMPLETED:
        if oid in return_world.hazard_cells:
            return_world.transform_to_knowledge(oid)

    # haz_blue injected as first waypoint — directed return target.
    hbp = return_world.object_positions.get("haz_blue")
    if hbp is not None:
        return_world.inject_waypoint(hbp)

    # Carry agent into return ENV1.
    agent = carry_agent
    agent.world = return_world

    for attr in ('end_state_banked', 'activation_step',
                 'phase_1_end_step', 'phase_2_end_step',
                 'end_state_found_step'):
        if hasattr(agent, attr):
            setattr(agent, attr,
                    False if attr == 'end_state_banked' else None)

    # mastery_flag: FULL REPLACEMENT with att_blue = 1 preserved.
    # This is the CRITICAL INVARIANT. Any prior mastery is reset.
    # att_blue is the single exception: it was earned in ENV2.
    if hasattr(agent, 'mastery_flag'):
        agent.mastery_flag = {a: 0 for a in return_world.attractor_cells}
        agent.mastery_flag['att_blue'] = 1       # ← CRITICAL INVARIANT

    # knowledge_banked: propagate ENV1 completions.
    if hasattr(agent, 'knowledge_banked'):
        agent.knowledge_banked = {h: False for h in return_world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent.knowledge_banked:
                agent.knowledge_banked[oid] = True
        # haz_blue stays False — it is the return target.

    if hasattr(agent, 'knowledge_banked_step'):
        agent.knowledge_banked_step = {h: None for h in return_world.hazard_cells}
    if hasattr(agent, 'knowledge_banked_sequence'):
        agent.knowledge_banked_sequence = []

    # _knowledge_unlocked: pre-mark completed hazards so
    # check_competency_unlocks skips them and fires only for haz_blue.
    if hasattr(agent, '_knowledge_unlocked'):
        agent._knowledge_unlocked = {h: False for h in return_world.hazard_cells}
        for oid in RETURN_ENV1_PRECOMPLETED:
            if oid in agent._knowledge_unlocked:
                agent._knowledge_unlocked[oid] = True
        # haz_blue: False — triggers transformation on first contact.

    if hasattr(agent, 'mastery_order_sequence'):
        agent.mastery_order_sequence = []
    if hasattr(agent, 'time_to_first_mastery'):
        agent.time_to_first_mastery = None
    if hasattr(agent, 'time_to_final_mastery'):
        agent.time_to_final_mastery = None

    if carry_prov_obs is not None:
        carry_prov_obs._agent  = agent
        carry_prov_obs._world  = return_world
        carry_prov_obs._environment_complete_fired = False

    # Step loop — immediate exit on arc_complete.
    state               = return_world.observe()
    transformation_step = None
    arc_complete        = False
    arc_timeout         = False
    actual_steps        = RETURN_ENV1_STEPS

    for step in range(RETURN_ENV1_STEPS):
        action = agent.choose_action(state)
        obs_next, contact_oid, moved, cost = return_world.step(action)
        agent.record_action_outcome(
            contact_oid, moved or contact_oid is not None,
            cost, return_world, step
        )
        intrinsic = (
            agent.novelty_reward(state)
            + agent.preference_reward(state)
            + agent.feature_reward(state)
        )
        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)
        state = obs_next

        # arc_complete: haz_blue → KNOWLEDGE via precondition gate.
        # V110Agent.check_competency_unlocks fires on any contact event.
        # mastery_flag['att_blue'] = 1 (carried) satisfies the gate.
        # world.transform_to_knowledge('haz_blue') is called.
        # world.knowledge_unlocked['haz_blue'] becomes True here.
        if return_world.knowledge_unlocked.get('haz_blue', False):
            transformation_step = step
            arc_complete        = True
            actual_steps        = step + 1
            agent.end_state_banked = True    # arc_complete IS end_state signal
            break

    if not arc_complete:
        arc_timeout = True

    arc_total_steps = None
    if arc_complete and env1_surprise_step is not None:
        arc_total_steps = transformation_step - env1_surprise_step

    arc_complete_row = {
        "arch":                    ARCH,
        "run_idx":                 run_idx,
        "seed":                    seed,
        "hazard_cost":             hazard_cost,
        "arc_complete":            arc_complete,
        "arc_timeout":             arc_timeout,
        "ineligible_reason":       "",
        "env1_surprise_step":      env1_surprise_step,
        "prediction_step":         prediction_step,
        "transfer_triggered_step": transfer_step,
        "confirmation_step":       confirmation_step,
        "return_step":             0,
        "transformation_step":     transformation_step,
        "arc_total_steps":         arc_total_steps,
        "arc_env_span":            3 if arc_complete else None,
        "causal_chain_depth":      6 if arc_complete else 4,
        "causal_chain_complete":   arc_complete,
    }

    return dict(
        arc_complete=arc_complete,
        arc_timeout=arc_timeout,
        transformation_step=transformation_step,
        arc_total_steps=arc_total_steps,
        actual_steps=actual_steps,
        arc_complete_row=arc_complete_row,
    )


# ---------------------------------------------------------------------------
# Full run (ENV1 + conditional ENV2 + conditional return ENV1)
# ---------------------------------------------------------------------------

def run_one(run_idx, seed, hazard_cost,
            report=True,
            with_goal=True, with_counterfactual=True,
            with_belief_revision=True, with_completion_signal=True,
            with_causal=True, with_env2=True, with_prediction=True,
            with_return=True):

    schema_v13_obs = V13SchemaObserverPrediction(
        prediction_enabled=with_prediction
    )
    run_meta_shared = {
        "arch": ARCH, "hazard_cost": hazard_cost,
        "num_steps": BATCH_STEPS, "run_idx": run_idx,
        "seed": seed, "env": 1,
    }
    causal_obs = V111CausalObserver(run_meta_shared) if with_causal else None

    # ---- Environment 1 ----
    env1 = _run_environment(
        run_idx=run_idx, seed=seed,
        hazard_cost=hazard_cost, num_steps=ENV1_STEPS,
        families=ENV1_FAMILIES,
        with_goal=with_goal, with_counterfactual=with_counterfactual,
        with_belief_revision=with_belief_revision,
        with_completion_signal=with_completion_signal,
        with_prediction=with_prediction,
        env_number=1,
        schema_v13_obs=schema_v13_obs, causal_obs=causal_obs,
    )

    agent    = env1['agent']
    prov_obs = env1['prov_obs']
    env1_mastery_snapshot = list(getattr(agent, 'mastery_order_sequence', []))
    env1_transfer = env1['transfer_condition_met']

    # ---- Environment 2 (conditional) ----
    env2 = None; env2_seed = None

    if with_env2 and env1_transfer:
        env2_seed = seed + ENV2_SEED_OFFSET
        _tw       = V113World(families=ENV2_FAMILIES, hazard_cost=hazard_cost,
                              has_end_state=True, seed=env2_seed)
        att_blue_pos = _tw.object_positions.get("att_blue")

        env2 = _run_environment(
            run_idx=run_idx, seed=env2_seed,
            hazard_cost=hazard_cost, num_steps=ENV2_STEPS,
            families=ENV2_FAMILIES,
            with_goal=with_goal, with_counterfactual=with_counterfactual,
            with_belief_revision=with_belief_revision,
            with_completion_signal=with_completion_signal,
            with_prediction=with_prediction,
            env_number=2,
            carry_agent=agent, carry_prov_obs=prov_obs,
            schema_v13_obs=schema_v13_obs, causal_obs=causal_obs,
            directed_search_target=att_blue_pos,
        )

    # ---- Return ENV1 (v1.14 new, conditional on confirmation) ----
    return_result     = None
    arc_complete_row  = None
    ineligible_reason = ""

    if with_return and env2 is not None:
        if _return_to_env1_condition_met(schema_v13_obs):
            pred_recs = schema_v13_obs.get_predicted_records()
            pred_step = next((r.get("prediction_step")
                              for r in pred_recs
                              if r.get("object_id") == "haz_blue"), None)
            conf_step = next((r.get("confirmation_step")
                              for r in pred_recs
                              if r.get("object_id") == "haz_blue"), None)
            return_result = _run_return_env1(
                run_idx=run_idx, seed=seed, hazard_cost=hazard_cost,
                carry_agent=agent, carry_prov_obs=prov_obs,
                schema_v13_obs=schema_v13_obs, causal_obs=causal_obs,
                env1_surprise_step=env1.get('transfer_triggered_step'),
                prediction_step=pred_step,
                transfer_step=env1['transfer_triggered_step'],
                confirmation_step=conf_step,
            )
            arc_complete_row = return_result['arc_complete_row']
        else:
            # Ineligible: determine reason
            pred_recs = schema_v13_obs.get_predicted_records() if schema_v13_obs else []
            if not pred_recs:
                ineligible_reason = "no_predicted_record"
            else:
                state_val = next(
                    (r.get("state", "") for r in pred_recs
                     if r.get("object_id") == "haz_blue"), ""
                )
                ineligible_reason = (
                    "prediction_unresolvable" if state_val == UNRESOLVABLE_STATE
                    else "prediction_unresolved"
                )
            arc_complete_row = {
                "arch": ARCH, "run_idx": run_idx, "seed": seed,
                "hazard_cost": hazard_cost,
                "arc_complete": False, "arc_timeout": False,
                "ineligible_reason": ineligible_reason,
                "env1_surprise_step": env1.get('transfer_triggered_step'),
                "prediction_step": None,
                "transfer_triggered_step": env1['transfer_triggered_step'],
                "confirmation_step": None, "return_step": None,
                "transformation_step": None, "arc_total_steps": None,
                "arc_env_span": None, "causal_chain_depth": 3,
                "causal_chain_complete": False,
            }
    elif not with_return:
        arc_complete_row = {
            "arch": ARCH, "run_idx": run_idx, "seed": seed,
            "hazard_cost": hazard_cost,
            "arc_complete": False, "arc_timeout": False,
            "ineligible_reason": "no_return_flag",
            "env1_surprise_step": None, "prediction_step": None,
            "transfer_triggered_step": env1['transfer_triggered_step'],
            "confirmation_step": None, "return_step": None,
            "transformation_step": None, "arc_total_steps": None,
            "arc_env_span": None, "causal_chain_depth": 0,
            "causal_chain_complete": False,
        }

    # ---- report_env = env1 (enforced constant) ----
    report_env  = env1
    active_meta = env1['meta']

    statements = []; summary = {}
    causal_records = []; env2_row = None; predicted_rows = []

    if report:
        bundle = build_bundle_from_observers(
            provenance_obs       = report_env['prov_obs'],
            schema_obs           = report_env['schema_obs'],
            family_obs           = report_env['family_obs'],
            comparison_obs       = report_env['comp_obs'],
            prediction_error_obs = report_env['pe_obs'],
            run_meta             = active_meta,
            goal_obs             = report_env['goal_obs'],
            counterfactual_obs   = report_env['cf_obs'],
            belief_revision_obs  = report_env['br_obs'],
            causal_obs           = None,
            schema_v13_obs       = schema_v13_obs,
        )
        if report_env['br_obs'] is not None:
            pe_records = getattr(bundle, 'prediction_error', None) or []
            report_env['br_obs'].process_pe_substrate(pe_records)
            bundle.belief_revision = report_env['br_obs'].get_substrate()

        if causal_obs is not None:
            causal_obs._meta['phase_1_end_step'] = active_meta.get('phase_1_end_step')
            causal_obs._meta['phase_2_end_step'] = active_meta.get('phase_2_end_step')
            causal_obs._built = False
            causal_obs.build_causal_chains(bundle)
            bundle.causal = causal_obs.get_substrate()

        layer      = V16ReportingLayer(bundle)
        statements = layer.generate_report()
        causal_records = causal_obs.get_substrate() if causal_obs else []

        q4_count   = sum(1 for s in statements
                         if getattr(s, 'query_type', '') == 'what_avoided')
        cf_emitted = len(report_env['cf_obs'].get_substrate()
                         if report_env['cf_obs'] else [])
        if q4_count > cf_emitted:
            print(f"  [SANITY FAIL] Run {run_idx}: "
                  f"Q4 ({q4_count}) > CF emitted ({cf_emitted})")

        if env2 is not None:
            env2_row = _build_env2_row(run_idx, seed, hazard_cost, env2_seed,
                                       env2, causal_records, schema_v13_obs)
        summary = _compute_summary(
            run_idx, seed, hazard_cost, statements,
            report_env['goal_obs'], report_env['cf_obs'],
            report_env['br_obs'], causal_records,
            report_env['end_state_banked_step'],
            env2 is not None, schema_v13_obs,
        )

    if with_prediction:
        predicted_rows = schema_v13_obs.predicted_schema_rows(active_meta)

    run_row = _build_run_row(
        run_idx, seed, hazard_cost, env1, causal_records,
        env2 is not None,
        env1_mastery_snapshot=env1_mastery_snapshot,
        return_result=return_result,
        ineligible_reason=ineligible_reason,
    )

    return (run_row, statements, summary,
            env1['prov_obs'], env1['goal_obs'],
            env1['cf_obs'], env1['br_obs'],
            env1['end_state_banked_step'],
            causal_obs, env2_row, predicted_rows,
            arc_complete_row)


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def _build_run_row(run_idx, seed, hazard_cost, env1,
                   causal_records, env2_ran,
                   env1_mastery_snapshot=None,
                   return_result=None,
                   ineligible_reason=""):
    agent    = env1['agent']
    pe_obs   = env1['pe_obs']
    goal_obs = env1['goal_obs']
    cf_obs   = env1['cf_obs']
    br_obs   = env1['br_obs']
    es_step  = env1['end_state_banked_step']

    pe_summary  = pe_obs.summary_metrics()
    goal_fields = {}
    if goal_obs is not None:
        g = goal_obs.get_substrate()["goal_summary"]
        goal_fields = {
            "goal_type":                 g["goal_type"],
            "goal_target_id":            g["target_id"],
            "goal_step_budget":          g["step_budget"],
            "goal_resolved":             g["resolved"],
            "goal_resolution_step":      g["resolution_step"],
            "goal_budget_remaining":     g["budget_remaining"],
            "goal_expired":              g["expired"],
            "goal_last_progress_step":   g["last_progress_step"],
            "goal_resolution_window":    g["goal_resolution_window"],
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

    activation_step  = getattr(agent, 'activation_step', None)
    draw_active      = getattr(agent, 'end_state_draw_active', False)
    steps_draw_bank  = (
        (es_step - activation_step)
        if es_step is not None and activation_step is not None else None
    )

    valid_chains   = [r for r in causal_records
                      if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    depths         = [r["chain_depth"] for r in valid_chains]
    complete_count = sum(1 for r in valid_chains if r.get("chain_complete"))

    arc_complete        = False
    arc_timeout         = False
    transformation_step = None
    arc_total_steps     = None
    return_env1_ran     = return_result is not None
    if return_result:
        arc_complete        = return_result['arc_complete']
        arc_timeout         = return_result['arc_timeout']
        transformation_step = return_result['transformation_step']
        arc_total_steps     = return_result['arc_total_steps']

    return {
        "arch": ARCH, "run_idx": run_idx, "seed": seed,
        "hazard_cost": hazard_cost,
        "num_steps": env1.get('actual_steps', BATCH_STEPS),
        "phase_1_end_step":          agent.phase_1_end_step,
        "phase_2_end_step":          agent.phase_2_end_step,
        "time_to_first_flag":        agent.time_to_first_flag,
        "time_to_second_flag":       agent.time_to_second_flag,
        "time_to_final_flag":        agent.time_to_final_flag,
        "total_cost_incurred":       agent.total_cost_incurred,
        "time_to_first_mastery":     agent.time_to_first_mastery,
        "time_to_final_mastery":     agent.time_to_final_mastery,
        "mastery_order_sequence":    str(agent.mastery_order_sequence),
        "activation_step":           activation_step,
        "end_state_found_step":      agent.end_state_found_step,
        "end_state_banked":          agent.end_state_banked,
        "time_to_first_transition":  agent.time_to_first_transition,
        "time_to_final_transition":  agent.time_to_final_transition,
        "transition_order_sequence": str(agent.transition_order_sequence),
        "knowledge_banked_sequence": str(agent.knowledge_banked_sequence),
        **pe_summary,
        **goal_fields,
        "suppressed_approach_count":      cf_emitted,
        "goal_relevant_suppressed_count": gr_count,
        "suppressed_approach_objects":    obj_list,
        "cf_records_raw":    cf_raw,
        "cf_records_emitted": cf_emitted,
        "cf_exclusion_rate": round(cf_excl, 4),
        "end_state_draw_active":    draw_active,
        "end_state_banked_step":    es_step,
        "steps_draw_to_bank":       steps_draw_bank,
        "revised_expectation_count": len(br_records),
        "causal_chain_count": len(valid_chains),
        "mean_chain_depth": (
            round(sum(depths) / len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count": complete_count,
        "q5_statement_count": 0,
        "env2_ran": env2_ran,
        "haz_blue_approached":      env1['haz_blue_approached'],
        "predicted_record_written": env1['predicted_record_written'],
        "transfer_triggered_step":  env1['transfer_triggered_step'],
        "env1_mastery_order_sequence": str(env1_mastery_snapshot or []),
        "env1_end_state_banked_step":  env1['end_state_banked_step'],
        # v1.14 new
        "return_env1_ran":     return_env1_ran,
        "arc_complete":        arc_complete,
        "arc_timeout":         arc_timeout,
        "ineligible_reason":   ineligible_reason,
        "return_step":         0 if return_env1_ran else None,
        "transformation_step": transformation_step,
        "arc_total_steps":     arc_total_steps,
    }


def _build_env2_row(run_idx, seed, hazard_cost, env2_seed,
                    env2, causal_records, schema_v13_obs):
    agent   = env2['agent']
    pe_obs  = env2['pe_obs']
    es_step = env2['end_state_banked_step']
    pe_sum  = pe_obs.summary_metrics()

    env2_chains = [r for r in causal_records
                   if r.get("env") == 2
                   and r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    e2_depths   = [r["chain_depth"] for r in env2_chains]

    pred_records = schema_v13_obs.get_predicted_records() if schema_v13_obs else []
    pred_state   = next(
        (r["state"] for r in pred_records if r["object_id"] == "haz_blue"), ""
    )

    att_blue_step    = env2.get('att_blue_mastery_step')
    att_blue_seq_pos = None
    if att_blue_step is not None:
        seq = getattr(agent, 'mastery_order_sequence', [])
        if 'att_blue' in seq:
            att_blue_seq_pos = seq.index('att_blue')

    return {
        "arch": ARCH, "run_idx": run_idx, "seed": seed,
        "hazard_cost": hazard_cost, "env2_seed": env2_seed,
        "env2_activation_step":   env2.get('env2_activation_step'),
        "env2_phase_1_end_step":  getattr(agent, 'phase_1_end_step', None),
        "env2_end_state_banked_step": es_step,
        "env2_yellow_pre_transition_entries":
            pe_sum.get("yellow_pre_transition_entries"),
        "env2_yellow_resolution_window":
            pe_sum.get("yellow_resolution_window"),
        "env2_green_pre_transition_entries":
            pe_sum.get("green_pre_transition_entries"),
        "env2_green_resolution_window":
            pe_sum.get("green_resolution_window"),
        "env2_q5_chain_count": len(env2_chains),
        "env2_q5_mean_chain_depth": (
            round(sum(e2_depths) / len(e2_depths), 2) if e2_depths else 0.0
        ),
        "att_blue_mastery_step":  att_blue_step,
        "att_blue_mastery_env":   2 if att_blue_step is not None else None,
        "predicted_record_state_at_run_end": pred_state,
        "att_blue_sequence_position": att_blue_seq_pos,
        "env2_mastery_order_sequence":
            str(getattr(agent, 'mastery_order_sequence', [])),
        "env2_att_yellow_mastery_step": env2.get('att_yellow_mastery_step'),
        "env2_att_green_mastery_step":  env2.get('att_green_mastery_step'),
        "env2_actual_steps": env2.get('actual_steps'),
    }


def _compute_summary(run_idx, seed, hazard_cost, statements,
                     goal_obs, cf_obs, br_obs, causal_records,
                     es_step, env2_ran, schema_v13_obs=None):
    total  = len(statements)
    halluc = sum(1 for s in statements if not s.source_resolves)
    q1 = sum(1 for s in statements if s.query_type == "what_learned")
    q2 = sum(1 for s in statements if s.query_type == "how_structured")
    q3 = sum(1 for s in statements if s.query_type == "what_surprised")
    q4 = sum(1 for s in statements if s.query_type == "what_avoided")
    q5 = sum(1 for s in statements if s.query_type == "why_this_arc")
    q3_cells = len({s.source_key for s in statements
                    if s.query_type == "what_surprised"})
    q3_res   = sum(1 for s in statements
                   if s.query_type == "what_surprised"
                   and "resolution" in s.text.lower())
    goal_pres = goal_obs is not None
    goal_res  = (goal_obs.get_substrate()["goal_summary"]["resolved"]
                 if goal_obs else False)
    cf_records = cf_obs.get_substrate() if cf_obs else []
    cf_raw     = cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted = len(cf_records)
    cf_excl    = (1.0 - cf_emitted / cf_raw) if cf_raw > 0 else 0.0
    br_records = br_obs.get_substrate() if br_obs else []
    deltas     = [r.get("approach_delta", 0) for r in br_records]
    mean_delta = round(sum(deltas) / len(deltas), 2) if deltas else 0.0

    valid_chains   = [r for r in causal_records
                      if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    depths         = [r["chain_depth"] for r in valid_chains]
    complete_count = sum(1 for r in valid_chains if r.get("chain_complete"))

    pred_written = False; pred_state = ""
    if schema_v13_obs:
        recs = schema_v13_obs.get_predicted_records()
        pred_written = bool(recs)
        pred_state = next(
            (r["state"] for r in recs if r["object_id"] == "haz_blue"), ""
        )

    return {
        "arch": ARCH, "run_idx": run_idx, "seed": seed,
        "hazard_cost": hazard_cost, "num_steps": BATCH_STEPS,
        "total_statements": total,
        "statements_q1": q1, "statements_q2": q2,
        "statements_q3": q3, "statements_q4": q4, "statements_q5": q5,
        "hallucination_count": halluc,
        "q1_formation_depth": q1,
        "q3_surprise_cells": q3_cells, "q3_resolution_stated": q3_res,
        "report_complete": halluc == 0,
        "statements_with_relevance_markers": 0,
        "goal_statement_present": goal_pres, "goal_resolution_stated": goal_res,
        "q4_statement_count": q4,
        "suppressed_approach_count": cf_emitted,
        "goal_relevant_suppressed_count": sum(
            1 for r in cf_records if r.get("goal_relevant")
        ),
        "br_statement_count": q3,
        "revised_expectation_count": len(br_records),
        "mean_approach_delta": mean_delta, "bias_effective": mean_delta > 0,
        "cf_records_raw": cf_raw, "cf_records_emitted": cf_emitted,
        "cf_exclusion_rate": round(cf_excl, 4),
        "end_state_draw_active": False, "end_state_banked_step": es_step,
        "causal_chain_count": len(valid_chains),
        "mean_chain_depth": (
            round(sum(depths) / len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count": complete_count, "q5_statement_count": q5,
        "predicted_record_written": pred_written,
        "predicted_record_state": pred_state,
    }


# ---------------------------------------------------------------------------
# Q5 individuation (unchanged from v1.13.8)
# ---------------------------------------------------------------------------

def _edit_distance(seq_a, seq_b):
    if not seq_a and not seq_b:
        return 0.0
    la, lb = len(seq_a), len(seq_b)
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1): dp[i][0] = i
    for j in range(lb + 1): dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if seq_a[i-1] == seq_b[j-1] else 1
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
    return dp[la][lb] / max(la, lb)


def compute_q5_individuation(causal_records, run_meta):
    valid = [r for r in causal_records
             if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    rows  = []
    for i, ra in enumerate(valid):
        for j, rb in enumerate(valid):
            if j <= i: continue
            sa = [lnk["link_type"] for lnk in ra.get("links", [])]
            sb = [lnk["link_type"] for lnk in rb.get("links", [])]
            rows.append({
                "arch": run_meta.get("arch", ARCH),
                "run_idx_a": ra.get("run_idx", ""),
                "run_idx_b": rb.get("run_idx", ""),
                "seed_a": ra.get("seed", ""),
                "seed_b": rb.get("seed", ""),
                "hazard_cost": ra.get("hazard_cost", ""),
                "chain_object_a": ra.get("object_id", ""),
                "chain_object_b": rb.get("object_id", ""),
                "link_sequence_a": ">".join(sa),
                "link_sequence_b": ">".join(sb),
                "link_sequence_distance": round(_edit_distance(sa, sb), 4),
                "within_run": ra.get("run_idx", "") == rb.get("run_idx", ""),
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
    parser.add_argument("--no-return",            action="store_true",
                        help="Skip return ENV1 (v1.13.8 regression baseline)")
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
            ('arc', ARC_COMPLETE_CSV),
        ]:
            csv_files[key] = open(path, 'w', newline='')
        if with_goal:   csv_files['goal'] = open(GOAL_CSV,            'w', newline='')
        if with_cf:     csv_files['cf']   = open(COUNTERFACTUAL_CSV,  'w', newline='')
        if with_br:     csv_files['br']   = open(BELIEF_REVISION_CSV, 'w', newline='')
        if with_causal: csv_files['caus'] = open(CAUSAL_CSV,          'w', newline='')

        writers['run']  = csv.DictWriter(csv_files['run'],  fieldnames=RUN_DATA_FIELDS)
        writers['prov'] = csv.DictWriter(csv_files['prov'], fieldnames=[
            "arch", "run_idx", "seed", "hazard_cost",
            "flag_id", "flag_type", "flag_set_step",
        ])
        writers['rpt']  = csv.DictWriter(csv_files['rpt'],  fieldnames=REPORT_FIELDS)
        writers['sum']  = csv.DictWriter(csv_files['sum'],  fieldnames=SUMMARY_FIELDS)
        writers['es']   = csv.DictWriter(csv_files['es'],   fieldnames=END_STATE_DRAW_FIELDS)
        writers['env2'] = csv.DictWriter(csv_files['env2'], fieldnames=ENV2_RUN_DATA_FIELDS)
        writers['q5i']  = csv.DictWriter(csv_files['q5i'],  fieldnames=Q5_INDIVIDUATION_FIELDS)
        writers['pred'] = csv.DictWriter(csv_files['pred'], fieldnames=PREDICTED_SCHEMA_FIELDS)
        writers['arc']  = csv.DictWriter(csv_files['arc'],  fieldnames=ARC_COMPLETE_FIELDS)
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
        total_causal_chains  = 0
        env2_runs            = 0
        arc_complete_runs    = 0
        arc_timeout_runs     = 0
        predicted_fires      = 0
        predicted_confirmed  = 0
        incomplete_runs      = []
        all_causal_records   = []

        print(f"v1.14 batch: {len(jobs)} runs | "
              f"prediction={'ON' if with_pred else 'OFF'} | "
              f"env2={'ON' if with_env2 else 'OFF'} | "
              f"return={'ON' if with_return else 'OFF (regression)'}")
        print()

        for run_idx, seed, hazard_cost in jobs:
            try:
                result = run_one(
                    run_idx, seed, hazard_cost,
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

            (run_row, statements, summary,
             prov_obs, goal_obs, cf_obs, br_obs,
             es_step, causal_obs, env2_row, pred_rows,
             arc_complete_row) = result

            writers['run'].writerow(
                {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
            )
            flush_provenance_csv(prov_obs, PROVENANCE_CSV)

            if with_goal and goal_obs:
                for gr in goal_obs.get_substrate().get("goal_progress", []):
                    writers['goal'].writerow(
                        {k: gr.get(k, "") for k in GOAL_FIELDS}
                    )
            if with_cf and cf_obs:
                for cr in cf_obs.get_substrate():
                    writers['cf'].writerow(
                        {k: cr.get(k, "") for k in COUNTERFACTUAL_FIELDS}
                    )
            if with_br and br_obs:
                for br in br_obs.get_substrate():
                    writers['br'].writerow(
                        {k: br.get(k, "") for k in BELIEF_REVISION_FIELDS}
                    )

            if with_causal and causal_obs:
                cm = {"arch": ARCH, "run_idx": run_idx, "seed": seed,
                      "hazard_cost": hazard_cost, "num_steps": BATCH_STEPS}
                for cr in causal_obs.causal_rows():
                    row = {**cm, **cr}
                    writers['caus'].writerow(
                        {k: row.get(k, "") for k in CAUSAL_FIELDS}
                    )
                all_causal_records.extend([
                    {**r, "run_idx": run_idx, "seed": seed,
                     "hazard_cost": hazard_cost}
                    for r in causal_obs.get_substrate()
                ])
                total_causal_chains += sum(
                    1 for r in causal_obs.get_substrate()
                    if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM
                )

            if with_pred and pred_rows:
                for pr in pred_rows:
                    writers['pred'].writerow(
                        {k: pr.get(k, "") for k in PREDICTED_SCHEMA_FIELDS}
                    )
                predicted_fires += len(pred_rows)
                predicted_confirmed += sum(
                    1 for pr in pred_rows
                    if pr.get("state") == CONFIRMED_STATE
                )

            if arc_complete_row is not None:
                writers['arc'].writerow(
                    {k: arc_complete_row.get(k, "")
                     for k in ARC_COMPLETE_FIELDS}
                )
                if arc_complete_row.get("arc_complete"):
                    arc_complete_runs += 1
                elif arc_complete_row.get("arc_timeout"):
                    arc_timeout_runs += 1

            if report and statements:
                for s in statements:
                    writers['rpt'].writerow({
                        "arch": ARCH, "run_idx": run_idx,
                        "seed": seed, "hazard_cost": hazard_cost,
                        "num_steps": BATCH_STEPS,
                        "query_type":     getattr(s, 'query_type', ''),
                        "statement_text": getattr(s, 'text', ''),
                        "source_type":    getattr(s, 'source_type', ''),
                        "source_key":     getattr(s, 'source_key', ''),
                        "source_resolves": getattr(s, 'source_resolves', False),
                    })
                run_row["q5_statement_count"] = summary.get("q5_statement_count", 0)

            if report and summary:
                writers['sum'].writerow(
                    {k: summary.get(k, "") for k in SUMMARY_FIELDS}
                )
                total_statements     += summary.get("total_statements", 0)
                total_hallucinations += summary.get("hallucination_count", 0)

            if env2_row is not None:
                writers['env2'].writerow(
                    {k: env2_row.get(k, "") for k in ENV2_RUN_DATA_FIELDS}
                )
                env2_runs += 1

            writers['es'].writerow({
                "arch": ARCH, "run_idx": run_idx,
                "seed": seed, "hazard_cost": hazard_cost,
                "num_steps": BATCH_STEPS,
                "activation_step":       run_row.get("activation_step"),
                "end_state_banked_step": es_step,
                "steps_draw_to_bank":    run_row.get("steps_draw_to_bank"),
                "end_state_draw_active": run_row.get("end_state_draw_active"),
            })

            if report and summary:
                status   = "PASS" if summary["hallucination_count"] == 0 else "FAIL"
                pred_st  = summary.get("predicted_record_state", "-")
                arc_sym  = ("✓" if run_row.get("arc_complete")
                            else ("T" if run_row.get("arc_timeout")
                                  else ("–" if run_row.get("ineligible_reason")
                                        else "?")))
                goal_out = ""
                if with_goal and goal_obs:
                    gs = goal_obs.get_substrate()["goal_summary"]
                    goal_out = f"goal={'R' if gs['resolved'] else 'X'} | "
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"stmts={summary['total_statements']:3d} | "
                    f"chains={run_row.get('causal_chain_count', 0):2d} | "
                    f"{goal_out}"
                    f"env2={'Y' if env2_row else 'N'} | "
                    f"pred={pred_st} | arc={arc_sym} | halluc={status}"
                )

        # -------------------------------------------------------------------
        # Batch summaries
        # -------------------------------------------------------------------
        print()
        print("Category Ω: Cross-environment causal arc (v1.14)")
        print(f"  arc_complete: {arc_complete_runs}/{len(jobs)}")
        print(f"  arc_timeout:  {arc_timeout_runs}/{len(jobs)}")
        if arc_complete_runs + arc_timeout_runs > 0:
            rate = arc_complete_runs / (arc_complete_runs + arc_timeout_runs)
            print(f"  Rate (eligible): {rate:.0%}")
        print(f"  Upper bound from v1.13.8: 29 eligible")

        if with_pred and report:
            print()
            print("Category π: Predictive schema")
            print(f"  Written: {predicted_fires}  Confirmed: {predicted_confirmed}")
            if predicted_fires:
                print(f"  Rate: {predicted_confirmed/predicted_fires:.0%}")

        if with_env2:
            print()
            print(f"Category Λ: ENV2 ran {env2_runs}/{len(jobs)}")

        if with_causal and report and all_causal_records:
            valid_q5 = [r for r in all_causal_records
                        if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
            if valid_q5:
                indiv_rows = compute_q5_individuation(
                    all_causal_records, {"arch": ARCH}
                )
                for irow in indiv_rows:
                    writers['q5i'].writerow(
                        {k: irow.get(k, "") for k in Q5_INDIVIDUATION_FIELDS}
                    )
                between = [r["link_sequence_distance"]
                           for r in indiv_rows if not r["within_run"]]
                within  = [r["link_sequence_distance"]
                           for r in indiv_rows if r["within_run"]]
                if between:
                    mb = sum(between)/len(between)
                    mw = sum(within)/len(within) if within else 0.0
                    print()
                    print(f"Category ζ: Q5 individuation — "
                          f"between={mb:.4f} within={mw:.4f} "
                          f"{'PASS' if mb > mw else 'FAIL'}")

        print()
        print("=" * 65)
        print(f"v1.14 complete. "
              f"{len(jobs) - len(incomplete_runs)}/{len(jobs)} runs.")
        if report:
            print(f"  Statements:    {total_statements}")
            print(f"  Hallucinations:{total_hallucinations}")
            print(f"  Causal chains: {total_causal_chains}")
            print(f"  arc_complete:  {arc_complete_runs}/{len(jobs)}")
            print(f"  Category α:    "
                  f"{'PASS' if total_hallucinations == 0 else 'FAIL'}")
        if incomplete_runs:
            print(f"  Incomplete: {incomplete_runs}")

        print()
        print("  Outputs:")
        for label, path in [
            ("Run data",          RUN_DATA_CSV),
            ("Report",            REPORT_CSV),
            ("Report summary",    REPORT_SUMMARY_CSV),
            ("Provenance",        PROVENANCE_CSV),
            ("Causal chains",     CAUSAL_CSV),
            ("Predicted schema",  PREDICTED_SCHEMA_CSV),
            ("Arc complete",      ARC_COMPLETE_CSV),
            ("ENV2 run data",     ENV2_RUN_DATA_CSV),
            ("Q5 individuation",  Q5_INDIVIDUATION_CSV),
        ]:
            print(f"    {label:<22} {path}")

    finally:
        for f in csv_files.values():
            f.close()


if __name__ == "__main__":
    main()
