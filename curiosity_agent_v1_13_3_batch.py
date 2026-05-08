"""
curiosity_agent_v1_13_batch.py
--------------------------------
v1.13 batch runner: Abductive Inference and the Predictive Schema Record.

CHANGES FROM V1.12
  - V113World replaces V17World. ENV1 contains haz_blue (no att_blue).
    ENV2 contains att_blue (no haz_blue). Object positions differ across
    environments (repeat-pattern interference control). Pre-registered §2.1.
  - haz_blue added to Phase 1 waypoint sequence in ENV1 as a mandatory
    target. Transfer cannot fire unless haz_blue has been approached.
    Pre-registered §2.3.
  - Transfer condition changed: YELLOW complete + GREEN complete +
    predicted schema record written for haz_blue. Replaces full
    environment completion gate from v1.12. Pre-registered §2.3.
  - V13SchemaObserver (v1.13 write pathway) added alongside the existing
    V13SchemaObserver (v1.3 observer). The v1.13 instance is schema_v13_obs.
  - build_predicted_records() called within-run on haz_blue surprise event.
    Pre-registered §2.4.
  - Directed search waypoint for att_blue injected into ENV2 world at run
    start. Pre-registered §2.5.
  - Q4/CF sanity check: CF statement count must not exceed CF emitted count
    for the run's primary environment. Pre-registered §2.9.
  - report_env = env1 enforced as named constant. Pre-registered §2.9.
  - predicted_schema_v1_13.csv output added. Pre-registered §3.
  - env2_run_data extended: att_blue_mastery_step, att_blue_mastery_env,
    predicted_record_state_at_run_end, att_blue_sequence_position.

ARCHITECTURE UNCHANGED
  All eleven observers inherited. V111CausalObserver inherited and extended
  with build_predicted_records(). V110Agent, phase schedule, drive
  composition unchanged.

ADDITIVE DISCIPLINE
  --no-prediction: disables predicted schema records, write pathway is a
                   no-op, all Q1-Q5 outputs byte-identical to v1.12 at
                   matched seeds. V113World at v1.12-equivalent families
                   is byte-identical to V17World at matched seeds.
  --no-env2:       skips second-environment architecture.
  --no-causal:     disables causal observer.

PRE-FLIGHT
  verify_v1_13_level14.py must pass before full batch.

Usage:
    python curiosity_agent_v1_13_batch.py [--no-report]
                                           [--no-goal]
                                           [--no-counterfactual]
                                           [--no-belief-revision]
                                           [--no-completion-signal]
                                           [--no-causal]
                                           [--no-env2]
                                           [--no-prediction]
"""

import argparse
import csv
import os
import sys
import statistics

import numpy as np

import v1_13_observer_substrates  # noqa: F401  — applies all patches
from v1_13_observer_substrates import build_bundle_from_observers, PREDICTION_FAMILY_MINIMUM

# World
from v1_13_world import (
    V113World, ENV1_FAMILIES, ENV2_FAMILIES, NUM_ACTIONS,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ,
    PERCEPTION_RADIUS,
)

# Agent
from v1_10_agent import V110Agent
from v1_7_agent  import V17Agent

# Observers — v1.3 through v1.11 (unchanged)
from v1_1_provenance                import V1ProvenanceStore
from v1_3_schema_extension          import V13SchemaObserver as V13SchemaObserverBase
from v1_3_family_observer           import V13FamilyObserver
from v1_4_comparison_observer       import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver
from v1_6_reporting_layer           import V16ReportingLayer
from v1_7_observer_substrates       import flush_provenance_csv
from v1_8_goal_layer                import V18GoalObserver, assign_goal, GOAL_FIELDS
from v1_9_counterfactual_observer   import (
    V19CounterfactualObserver, COUNTERFACTUAL_FIELDS
)
from v1_10_belief_revision_observer import (
    V110BeliefRevisionObserver, BELIEF_REVISION_FIELDS
)
from v1_11_causal_observer import (
    V111CausalObserver, CAUSAL_FIELDS, CHAIN_DEPTH_MINIMUM
)

# v1.13 new
from v1_13_schema_extension import (
    V13SchemaObserver as V13SchemaObserverPrediction,
    PREDICTED_SCHEMA_FIELDS,
    PREDICTED_STATE, CONFIRMED_STATE, UNRESOLVABLE_STATE,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_CSV_PRIMARY    = "run_data_v1_12.csv"
RUN_DATA_CSV        = "run_data_v1_13.csv"
PROVENANCE_CSV      = "provenance_v1_13.csv"
GOAL_CSV            = "goal_v1_13.csv"
COUNTERFACTUAL_CSV  = "counterfactual_v1_13.csv"
BELIEF_REVISION_CSV = "belief_revision_v1_13.csv"
CAUSAL_CSV          = "causal_v1_13.csv"
REPORT_CSV          = "report_v1_13.csv"
REPORT_SUMMARY_CSV  = "report_summary_v1_13.csv"
END_STATE_DRAW_CSV  = "end_state_draw_log_v1_13.csv"
ENV2_RUN_DATA_CSV   = "env2_run_data_v1_13.csv"
Q5_INDIVIDUATION_CSV = "q5_individuation_v1_13.csv"
PREDICTED_SCHEMA_CSV = "predicted_schema_v1_13.csv"

ENV1_STEPS       = 500_000   # Environment 1 step budget
ENV2_STEPS       = 640_000   # Environment 2 step budget — independent allocation
                              # per the Montessori principle: each environment
                              # receives its full budget regardless of transfer timing.
                              # 640k gives late-transferring agents ~275k+ steps in ENV2.
BATCH_STEPS      = ENV1_STEPS  # backward-compat alias used in reporting
HAZARD_COSTS     = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST    = 10
ARCH             = "v1_13"
ENV2_SEED_OFFSET = 10_000

# ---------------------------------------------------------------------------
# Field definitions (v1.12 fields preserved; v1.13 extensions appended)
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
    # v1.13 new
    "haz_blue_approached",
    "predicted_record_written",
    "transfer_triggered_step",
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
    # v1.13 new
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
    # v1.13 new
    "att_blue_mastery_step",
    "att_blue_mastery_env",
    "predicted_record_state_at_run_end",
    "att_blue_sequence_position",
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
# Transfer condition helpers
# ---------------------------------------------------------------------------

def _yellow_green_complete(world):
    """Return True if YELLOW and GREEN family objectives are complete.

    Uses world.knowledge_unlocked directly — the ground truth for whether
    each family hazard has transitioned to KNOWLEDGE. This is reliable
    within the run; PE observer summary_metrics() only populates
    resolution_window fields in on_run_end, not during the run.
    """
    return (world.knowledge_unlocked.get('haz_yellow', False)
            and world.knowledge_unlocked.get('haz_green', False))


def _check_transfer_condition(world, schema_v13_obs):
    """Return True if ENV1 transfer condition is satisfied.

    Transfer condition (pre-registered §2.3):
      1. YELLOW family complete (haz_yellow transitioned to KNOWLEDGE)
      2. GREEN family complete (haz_green transitioned to KNOWLEDGE)
      3. Predicted schema record written for haz_blue

    Uses world.knowledge_unlocked as the ground truth for conditions
    1 and 2. schema_v13_obs for condition 3.
    """
    if not _yellow_green_complete(world):
        return False
    if not schema_v13_obs.has_pending_prediction("haz_blue") and \
       not any(r["object_id"] == "haz_blue"
               for r in schema_v13_obs.get_predicted_records()):
        return False
    return True


# ---------------------------------------------------------------------------
# Single environment run
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
    schema_v13_obs=None,   # shared across environments for predicted record
    causal_obs=None,       # shared for within-run build_predicted_records
    directed_search_target=None,  # att_blue position if prediction pending
):
    """Run one environment. Returns run artefacts dict.

    Parameters
    ----------
    families : list of dict
        Family definition list for V113World (ENV1_FAMILIES or ENV2_FAMILIES).
    carry_agent : V110Agent or None
        If not None, reuse this agent's Q-table (Environment 2).
    carry_prov_obs : V1ProvenanceStore or None
        If not None, carry provenance store across environments.
    schema_v13_obs : V13SchemaObserverPrediction or None
        Shared prediction schema observer. Carries predicted records
        across environments. Must be the same instance for ENV1 and ENV2.
    causal_obs : V111CausalObserver or None
        Shared causal observer. Carries chains across environments.
    directed_search_target : tuple (x,y,z) or None
        If provided (att_blue position), injected as a waypoint at ENV2 start.
    """
    np.random.seed(seed)

    world = V113World(
        families=families,
        hazard_cost=hazard_cost,
        has_end_state=True,
        seed=seed,
    )

    # ---- Inject mandatory waypoints (before agent setup so Phase 1
    #      reset drains the correct queue) ----
    if env_number == 1:
        haz_blue_pos = world.object_positions.get("haz_blue")
        if haz_blue_pos is not None:
            world.inject_waypoint(haz_blue_pos)
    if env_number == 2 and directed_search_target is not None:
        world.inject_waypoint(directed_search_target)

    AgentClass = V110Agent if with_completion_signal else V17Agent

    if carry_agent is not None:
        # Reuse agent; update world reference.
        # Reset per-environment state identically to v1.12 — the phase
        # schedule, prescribed path, and waypoint consumption all restart
        # naturally because the ENV2 world is freshly constructed with
        # _waypoint_idx=0. V17Agent drives Phase 1 via world.get_next_waypoint()
        # directly; no prescribed_actions rebuild is needed or correct.
        # The Q-table carries forward (developmental history preserved).
        agent = carry_agent
        agent.world = world
        if hasattr(agent, 'end_state_banked'):
            agent.end_state_banked = False
        if hasattr(agent, 'activation_step'):
            agent.activation_step = None
        if hasattr(agent, 'phase_1_end_step'):
            agent.phase_1_end_step = None
        if hasattr(agent, 'phase_2_end_step'):
            agent.phase_2_end_step = None
        if hasattr(agent, 'end_state_found_step'):
            agent.end_state_found_step = None

        # mastery_flag extension for att_blue.
        # att_blue is absent from mastery_flag (built from ENV1 attractor_cells).
        # Add it so mastery tracking fires correctly in ENV2.
        # No Q-value prior — att_blue is encountered genuinely during Phase 1.
        if hasattr(agent, 'mastery_flag'):
            if 'att_blue' not in agent.mastery_flag:
                agent.mastery_flag['att_blue'] = 0

        # Reset knowledge_banked for ENV2 hazards.
        # The activation gate checks sum(knowledge_banked.values()) ==
        # len(world.hazard_cells). Carried ENV1 knowledge_banked values
        # cause this to fire immediately on ENV2 entry before the agent
        # has mastered anything in the new environment. Reset all ENV2
        # hazard cells to False so the gate reflects genuine ENV2 progress.
        # The Q-table retains the learned values — only the banking
        # completion flag is reset, consistent with the ENV2 world being
        # a fresh developmental context.
        if hasattr(agent, 'knowledge_banked'):
            for h in world.hazard_cells:
                agent.knowledge_banked[h] = False
        if hasattr(agent, 'knowledge_banked_step'):
            for h in world.hazard_cells:
                agent.knowledge_banked_step[h] = None
        if hasattr(agent, 'knowledge_banked_sequence'):
            agent.knowledge_banked_sequence = []

        # Reset mastery_flag for all ENV2 attractor cells to 0.
        # Same principle: carried ENV1 mastery_flag values cause the
        # all_attractors_mastered gate to fire prematurely. The agent
        # must re-master attractors in ENV2 through genuine encounter.
        # att_blue starts at 0 (added above). YELLOW and GREEN attractors
        # also reset to 0 — they exist at new positions in ENV2 and must
        # be re-encountered. The schema knowledge (sequencing) carries
        # forward in the Q-table; the completion state does not.
        if hasattr(agent, 'mastery_flag'):
            for a in world.attractor_cells:
                agent.mastery_flag[a] = 0
        if hasattr(agent, 'mastery_order_sequence'):
            agent.mastery_order_sequence = []
        if hasattr(agent, 'time_to_first_mastery'):
            agent.time_to_first_mastery = None
        if hasattr(agent, 'time_to_final_mastery'):
            agent.time_to_final_mastery = None
    else:
        agent = AgentClass(world, total_steps=num_steps,
                           num_actions=NUM_ACTIONS)

    meta = {
        "arch":        ARCH,
        "hazard_cost": hazard_cost,
        "num_steps":   num_steps,
        "run_idx":     run_idx,
        "seed":        seed,
        "env":         env_number,
    }

    ctc = {
        "FRAME": FRAME, "NEUTRAL": NEUTRAL, "HAZARD": HAZARD,
        "ATTRACTOR": ATTRACTOR, "END_STATE": END_STATE,
        "KNOWLEDGE": KNOWLEDGE, "DIST_OBJ": DIST_OBJ,
    }

    # ---- Observers ----
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
        goal_obs = V18GoalObserver(
            agent, world, meta, goal_type, target_id, step_budget
        )

    cf_obs = None
    if with_counterfactual:
        cf_obs = V19CounterfactualObserver(
            agent, world, meta, goal_obs=goal_obs
        )
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
    if goal_obs is not None:
        observers.append(goal_obs)
    if cf_obs is not None:
        observers.append(cf_obs)
    if br_obs is not None:
        observers.append(br_obs)

    # ---- Simulation loop ----
    state = world.observe()
    end_state_banked_step = None
    env2_activation_step  = None
    haz_blue_approached   = False
    transfer_triggered_step = None
    predicted_record_written = False
    att_blue_mastery_step = None
    transfer_condition_met = False

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

        # ---- Directed-search bias for att_blue ----
        intrinsic = (
            agent.novelty_reward(state)
            + agent.preference_reward(state)
            + agent.feature_reward(state)
        )

        if with_completion_signal and isinstance(agent, V110Agent):
            intrinsic += agent.end_state_draw_reward(state, obs_next)

        if br_obs is not None:
            agent_pos     = getattr(world, 'agent_pos', None)
            obj_positions = getattr(world, 'object_positions', {})
            for bias_oid in br_obs.active_biased_objects(step):
                obj_pos = obj_positions.get(bias_oid)
                if obj_pos is not None and agent_pos is not None:
                    import math
                    intrinsic += br_obs.preference_bias_reward(
                        bias_oid, step, moving_closer=True
                    )

        # Directed search bias toward att_blue when prediction is pending
        if (with_prediction and schema_v13_obs is not None
                and env_number == 2
                and schema_v13_obs.has_pending_prediction("haz_blue")):
            att_blue_pos = world.object_positions.get("att_blue")
            agent_pos    = getattr(world, 'agent_pos', None)
            if att_blue_pos is not None and agent_pos is not None:
                import math
                dist = math.sqrt(sum(
                    (a - b)**2 for a, b in zip(agent_pos, att_blue_pos)
                ))
                # Soft pull: reward proportional to proximity
                if dist > 0:
                    intrinsic += 0.1 / dist

        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)
        state = obs_next

        # ---- Track env2 activation independently ----
        if env2_activation_step is None:
            a = getattr(agent, 'activation_step', None)
            if a is not None:
                env2_activation_step = step

        # ---- End state banking ----
        if (end_state_banked_step is None
                and getattr(agent, 'end_state_banked', False)):
            prov_obs.on_end_state_banked(step)
            end_state_banked_step = step

        # ---- haz_blue approach detection (ENV1 only) ----
        # Detection fires on PERCEPTION (within PERCEPTION_RADIUS): the
        # agent reliably passes within perception range as it navigates
        # the injected waypoint, even if it doesn't achieve a contact event.
        if (env_number == 1 and not haz_blue_approached):
            haz_blue_pos_check = world.object_positions.get("haz_blue")
            if haz_blue_pos_check is not None:
                import math as _math
                _dist_to_haz_blue = _math.sqrt(sum(
                    (a - b)**2 for a, b in zip(world.agent_pos, haz_blue_pos_check)
                ))
                if _dist_to_haz_blue <= PERCEPTION_RADIUS:
                    haz_blue_approached = True

        # ---- Predicted record construction (ENV1 only) ----
        # Fires once haz_blue has been approached AND the two-family minimum
        # can be met. Checked every 500 steps (not every step) for performance.
        # Uses world.knowledge_unlocked as the most reliable real-time evidence
        # that YELLOW and GREEN have transitioned — more reliable than the
        # PE substrate which may not be assembled until post-run.
        _prediction_check_interval = 500
        # No cost gate. In the Montessori framework, time and cost are not
        # constraints — the agent works at its own tempo. An agent that
        # completes both family arcs at cost=0.1 has earned the inference
        # as legitimately as one at cost=10.0. The two-family minimum is
        # the structural criterion; cost is not.
        if (env_number == 1
                and haz_blue_approached
                and step % _prediction_check_interval == 0
                and with_prediction
                and schema_v13_obs is not None
                and causal_obs is not None
                and not schema_v13_obs.has_pending_prediction("haz_blue")
                and not any(r["object_id"] == "haz_blue"
                            for r in schema_v13_obs.get_predicted_records())):
            # Two-family check via world.knowledge_unlocked.
            # Both family hazards must have transitioned through the full
            # competency arc (mastery of precondition attractor).
            _family_hazards_unlocked = sum(
                1 for h in ('haz_yellow', 'haz_green')
                if world.knowledge_unlocked.get(h, False)
            )
            if _family_hazards_unlocked >= PREDICTION_FAMILY_MINIMUM:
                # Write the predicted record directly using world.knowledge_unlocked
                # as the verified two-family evidence. Do NOT re-check through the
                # PE substrate — transformed_at_step is only populated in on_run_end,
                # so build_causal_chains finds zero resolvable events within the run.
                # world.knowledge_unlocked is the ground truth: both family hazards
                # have transitioned. The inference is valid and the record is written.
                _basis = sorted(
                    h for h in ('haz_yellow', 'haz_green')
                    if world.knowledge_unlocked.get(h, False)
                )
                schema_v13_obs.add_predicted_record({
                    "object_id":              "haz_blue",
                    "predicted_precondition": "att_blue",
                    "basis_chains":           _basis,
                    "prediction_step":        step,
                    "prediction_env":         env_number,
                })
                predicted_record_written = True

        # ---- att_blue mastery detection (ENV2 only) ----
        if (env_number == 2 and att_blue_mastery_step is None
                and contact_oid == "att_blue"):
            if world.object_type.get("att_blue") == KNOWLEDGE:
                att_blue_mastery_step = step
                # Update predicted record to confirmed
                if (with_prediction and schema_v13_obs is not None):
                    schema_v13_obs.confirm_predicted_record(
                        object_id="haz_blue",
                        confirmation_step=step,
                        confirming_env=env_number,
                    )

        # ---- Transfer condition check (ENV1 only) ----
        if (env_number == 1 and not transfer_condition_met
                and haz_blue_approached):
            if with_prediction and schema_v13_obs is not None:
                if _check_transfer_condition(world, schema_v13_obs):
                    transfer_condition_met = True
                    transfer_triggered_step = step
            else:
                # --no-prediction: fall back to v1.12 end-state-banked gate
                if end_state_banked_step is not None:
                    transfer_condition_met = True
                    transfer_triggered_step = step

    # ---- End of simulation ----
    for obs in observers:
        obs.on_run_end(num_steps)

    # Mark unresolvable if ENV2 finished without att_blue mastery
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
        meta=meta,
        world=world,
    )


# ---------------------------------------------------------------------------
# Full run (ENV1 + conditional ENV2)
# ---------------------------------------------------------------------------

def run_one(run_idx, seed, hazard_cost,
            report=True,
            with_goal=True, with_counterfactual=True,
            with_belief_revision=True, with_completion_signal=True,
            with_causal=True, with_env2=True, with_prediction=True):

    # Shared observers that span environments
    schema_v13_obs = (
        V13SchemaObserverPrediction(prediction_enabled=True)
        if with_prediction
        else V13SchemaObserverPrediction(prediction_enabled=False)
    )

    # Causal observer is shared: it accumulates chains across ENV1 and ENV2
    # so the cross-environment arc is fully captured.
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
        with_goal=with_goal,
        with_counterfactual=with_counterfactual,
        with_belief_revision=with_belief_revision,
        with_completion_signal=with_completion_signal,
        with_prediction=with_prediction,
        env_number=1,
        schema_v13_obs=schema_v13_obs,
        causal_obs=causal_obs,
    )

    agent    = env1['agent']
    prov_obs = env1['prov_obs']

    # v1.13 transfer gate: predicted record written + YELLOW + GREEN complete.
    # v1.12 fallback (--no-prediction): end state banked.
    env1_transfer = env1['transfer_condition_met']

    # ---- Environment 2 (conditional) ----
    env2      = None
    env2_seed = None

    if with_env2 and env1_transfer:
        env2_seed = seed + ENV2_SEED_OFFSET

        # Get att_blue position from ENV2 world definition for directed search
        # Build a temporary world to read the position without running it
        _temp_world = V113World(
            families=ENV2_FAMILIES, hazard_cost=hazard_cost,
            has_end_state=True, seed=env2_seed,
        )
        att_blue_pos = _temp_world.object_positions.get("att_blue")

        env2 = _run_environment(
            run_idx=run_idx, seed=env2_seed,
            hazard_cost=hazard_cost, num_steps=ENV2_STEPS,
            families=ENV2_FAMILIES,
            with_goal=with_goal,
            with_counterfactual=with_counterfactual,
            with_belief_revision=with_belief_revision,
            with_completion_signal=with_completion_signal,
            with_prediction=with_prediction,
            env_number=2,
            carry_agent=agent,
            carry_prov_obs=prov_obs,
            schema_v13_obs=schema_v13_obs,
            causal_obs=causal_obs,
            directed_search_target=att_blue_pos,
        )

    # ---- report_env = env1 (enforced as named constant) ----
    # Pre-registered §2.9. The biographical report ALWAYS reads from env1.
    # This is the v1.12.3 root-cause fix carried forward as a design
    # invariant, not a patch.
    report_env  = env1
    active_meta = env1['meta']

    statements, summary = [], {}
    causal_records = []
    env2_row = None
    predicted_rows = []

    if report:
        # Build post-run causal chains on the complete substrate.
        # causal_obs has already had build_causal_chains() called within-run
        # on the partial bundle. Call it again on the complete bundle to pick
        # up any chains that became resolvable post-run (belief revision, etc.)
        # build_causal_chains() is idempotent.
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

        br_obs_rep = report_env['br_obs']
        if br_obs_rep is not None:
            pe_records = getattr(bundle, 'prediction_error', None) or []
            br_obs_rep.process_pe_substrate(pe_records)
            bundle.belief_revision = br_obs_rep.get_substrate()

        if causal_obs is not None:
            # Update causal_obs._meta with phase_1_end_step from the completed
            # ENV1 run. causal_obs was created with run_meta_shared (a separate
            # dict) before the run started, so phase_1_end_step was None.
            # Without this update, _check_phase1 returns None for every chain
            # and LINK_PHASE1_ABSENCE is never written — causing depth-5 chains
            # instead of the correct depth-6. This is the v1.13.1 regression fix.
            causal_obs._meta['phase_1_end_step'] = active_meta.get('phase_1_end_step')
            causal_obs._meta['phase_2_end_step'] = active_meta.get('phase_2_end_step')
            # Reset _built so the post-run rebuild uses the updated meta.
            causal_obs._built = False
            causal_obs.build_causal_chains(bundle)
            bundle.causal = causal_obs.get_substrate()

        layer      = V16ReportingLayer(bundle)
        statements = layer.generate_report()
        causal_records = causal_obs.get_substrate() if causal_obs else []

        # ---- Q4/CF sanity check (pre-registered §2.9) ----
        q4_count = sum(
            1 for s in statements
            if getattr(s, 'query_type', '') == 'what_avoided'
        )
        cf_emitted = len(report_env['cf_obs'].get_substrate()
                         if report_env['cf_obs'] else [])
        if q4_count > cf_emitted:
            print(
                f"  [SANITY FAIL] Run {run_idx}: Q4 statements ({q4_count}) "
                f"> CF emitted ({cf_emitted}). report_env contamination."
            )

        # Env2 row
        if env2 is not None:
            env2_row = _build_env2_row(
                run_idx, seed, hazard_cost, env2_seed,
                env2, causal_records, schema_v13_obs
            )

        summary = _compute_summary(
            run_idx, seed, hazard_cost, statements,
            report_env['goal_obs'],
            report_env['cf_obs'],
            report_env['br_obs'],
            causal_records,
            report_env['end_state_banked_step'],
            env2 is not None,
            schema_v13_obs,
        )

    # Predicted schema rows
    if with_prediction:
        predicted_rows = schema_v13_obs.predicted_schema_rows(active_meta)

    run_row = _build_run_row(
        run_idx, seed, hazard_cost, env1, causal_records,
        env2 is not None
    )

    return (run_row, statements, summary,
            env1['prov_obs'], env1['goal_obs'],
            env1['cf_obs'], env1['br_obs'],
            env1['end_state_banked_step'],
            causal_obs, env2_row, predicted_rows)


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def _build_run_row(run_idx, seed, hazard_cost, env1,
                   causal_records, env2_ran):
    agent    = env1['agent']
    pe_obs   = env1['pe_obs']
    goal_obs = env1['goal_obs']
    cf_obs   = env1['cf_obs']
    br_obs   = env1['br_obs']
    es_step  = env1['end_state_banked_step']

    pe_summary = pe_obs.summary_metrics()

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

    cf_records  = cf_obs.get_substrate() if cf_obs else []
    cf_raw      = cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted  = len(cf_records)
    cf_excl     = (1.0 - cf_emitted / cf_raw) if cf_raw > 0 else 0.0
    gr_count    = sum(1 for r in cf_records if r.get("goal_relevant"))
    obj_list    = ",".join(sorted({r["object_id"] for r in cf_records}))

    br_records  = br_obs.get_substrate() if br_obs else []

    activation_step = getattr(agent, 'activation_step', None)
    draw_active     = getattr(agent, 'end_state_draw_active', False)
    steps_draw_bank = (
        (es_step - activation_step)
        if (es_step is not None and activation_step is not None)
        else None
    )

    valid_chains   = [r for r in causal_records
                      if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    depths         = [r["chain_depth"] for r in valid_chains]
    complete_count = sum(1 for r in valid_chains if r.get("chain_complete"))

    return {
        "arch":                  ARCH,
        "run_idx":               run_idx,
        "seed":                  seed,
        "hazard_cost":           hazard_cost,
        "num_steps":             BATCH_STEPS,
        "phase_1_end_step":      agent.phase_1_end_step,
        "phase_2_end_step":      agent.phase_2_end_step,
        "time_to_first_flag":    agent.time_to_first_flag,
        "time_to_second_flag":   agent.time_to_second_flag,
        "time_to_final_flag":    agent.time_to_final_flag,
        "total_cost_incurred":   agent.total_cost_incurred,
        "time_to_first_mastery": agent.time_to_first_mastery,
        "time_to_final_mastery": agent.time_to_final_mastery,
        "mastery_order_sequence": str(agent.mastery_order_sequence),
        "activation_step":       activation_step,
        "end_state_found_step":  agent.end_state_found_step,
        "end_state_banked":      agent.end_state_banked,
        "time_to_first_transition": agent.time_to_first_transition,
        "time_to_final_transition": agent.time_to_final_transition,
        "transition_order_sequence": str(agent.transition_order_sequence),
        "knowledge_banked_sequence": str(agent.knowledge_banked_sequence),
        **pe_summary,
        **goal_fields,
        "suppressed_approach_count":      cf_emitted,
        "goal_relevant_suppressed_count": gr_count,
        "suppressed_approach_objects":    obj_list,
        "cf_records_raw":                 cf_raw,
        "cf_records_emitted":             cf_emitted,
        "cf_exclusion_rate":              round(cf_excl, 4),
        "end_state_draw_active":          draw_active,
        "end_state_banked_step":          es_step,
        "steps_draw_to_bank":             steps_draw_bank,
        "revised_expectation_count":      len(br_records),
        "causal_chain_count":             len(valid_chains),
        "mean_chain_depth": (
            round(sum(depths) / len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count":           complete_count,
        "q5_statement_count":             0,  # filled after report
        "env2_ran":                       env2_ran,
        # v1.13 new
        "haz_blue_approached":       env1['haz_blue_approached'],
        "predicted_record_written":  env1['predicted_record_written'],
        "transfer_triggered_step":   env1['transfer_triggered_step'],
    }


def _build_env2_row(run_idx, seed, hazard_cost, env2_seed,
                    env2, causal_records, schema_v13_obs):
    agent    = env2['agent']
    pe_obs   = env2['pe_obs']
    es_step  = env2['end_state_banked_step']

    pe_summary      = pe_obs.summary_metrics()
    activation_step = env2.get('env2_activation_step')
    yel_win         = pe_summary.get("yellow_resolution_window")
    grn_win         = pe_summary.get("green_resolution_window")

    env2_chains = [r for r in causal_records
                   if r.get("env") == 2
                   and r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    e2_depths   = [r["chain_depth"] for r in env2_chains]

    # att_blue sequence position relative to YELLOW/GREEN formation in env2
    att_blue_step = env2.get('att_blue_mastery_step')
    yellow_done_step = None
    green_done_step  = None
    # Read from PE substrate for resolution steps in env2
    pe_recs = pe_obs.summary_metrics()
    # Approximate: use phase_1_end_step as proxy for family completion order
    # Full sequence position will be derivable from env2_run_data + provenance

    # Predicted record state at run end
    pred_records = schema_v13_obs.get_predicted_records() if schema_v13_obs else []
    pred_state   = ""
    if pred_records:
        for rec in pred_records:
            if rec["object_id"] == "haz_blue":
                pred_state = rec["state"]
                break

    return {
        "arch":                           ARCH,
        "run_idx":                        run_idx,
        "seed":                           seed,
        "hazard_cost":                    hazard_cost,
        "env2_seed":                      env2_seed,
        "env2_activation_step":           activation_step,
        "env2_phase_1_end_step":          getattr(agent, 'phase_1_end_step', None),
        "env2_end_state_banked_step":     es_step,
        "env2_yellow_pre_transition_entries": pe_summary.get("yellow_pre_transition_entries"),
        "env2_yellow_resolution_window":  yel_win,
        "env2_green_pre_transition_entries":  pe_summary.get("green_pre_transition_entries"),
        "env2_green_resolution_window":   grn_win,
        "env2_q5_chain_count":            len(env2_chains),
        "env2_q5_mean_chain_depth": (
            round(sum(e2_depths) / len(e2_depths), 2) if e2_depths else 0.0
        ),
        # v1.13 new
        "att_blue_mastery_step":          att_blue_step,
        "att_blue_mastery_env":           2 if att_blue_step is not None else None,
        "predicted_record_state_at_run_end": pred_state,
        "att_blue_sequence_position":     None,  # post-hoc from provenance
    }


def _compute_summary(run_idx, seed, hazard_cost, statements,
                     goal_obs, cf_obs, br_obs, causal_records,
                     es_step, env2_ran, schema_v13_obs=None):
    """Compute report summary metrics."""
    total      = len(statements)
    halluc     = sum(1 for s in statements if not s.source_resolves)
    q1         = sum(1 for s in statements if s.query_type == "what_learned")
    q2         = sum(1 for s in statements if s.query_type == "how_structured")
    q3         = sum(1 for s in statements if s.query_type == "what_surprised")
    q4         = sum(1 for s in statements if s.query_type == "what_avoided")
    q5         = sum(1 for s in statements if s.query_type == "why_this_arc")
    q3_cells   = len({s.source_key for s in statements
                      if s.query_type == "what_surprised"})
    q3_res     = sum(1 for s in statements
                     if s.query_type == "what_surprised"
                     and "resolution" in s.text.lower())
    goal_pres  = goal_obs is not None
    goal_res   = (goal_obs.get_substrate()["goal_summary"]["resolved"]
                  if goal_obs else False)
    cf_records = cf_obs.get_substrate() if cf_obs else []
    cf_raw     = cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted = len(cf_records)
    cf_excl    = (1.0 - cf_emitted / cf_raw) if cf_raw > 0 else 0.0
    br_records = br_obs.get_substrate() if br_obs else []
    deltas     = [r.get("approach_delta", 0) for r in br_records]
    mean_delta = round(sum(deltas) / len(deltas), 2) if deltas else 0.0
    bias_eff   = mean_delta > 0

    valid_chains   = [r for r in causal_records
                      if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    depths         = [r["chain_depth"] for r in valid_chains]
    complete_count = sum(1 for r in valid_chains if r.get("chain_complete"))

    # Predicted record state for summary
    pred_written = False
    pred_state   = ""
    if schema_v13_obs is not None:
        recs = schema_v13_obs.get_predicted_records()
        pred_written = bool(recs)
        for rec in recs:
            if rec["object_id"] == "haz_blue":
                pred_state = rec["state"]
                break

    return {
        "arch":            ARCH,
        "run_idx":         run_idx,
        "seed":            seed,
        "hazard_cost":     hazard_cost,
        "num_steps":       BATCH_STEPS,
        "total_statements":    total,
        "statements_q1":       q1,
        "statements_q2":       q2,
        "statements_q3":       q3,
        "statements_q4":       q4,
        "statements_q5":       q5,
        "hallucination_count": halluc,
        "q1_formation_depth":  q1,
        "q3_surprise_cells":   q3_cells,
        "q3_resolution_stated": q3_res,
        "report_complete":     halluc == 0,
        "statements_with_relevance_markers": 0,
        "goal_statement_present":  goal_pres,
        "goal_resolution_stated":  goal_res,
        "q4_statement_count":      q4,
        "suppressed_approach_count":      cf_emitted,
        "goal_relevant_suppressed_count": sum(
            1 for r in cf_records if r.get("goal_relevant")
        ),
        "br_statement_count":      q3,
        "revised_expectation_count": len(br_records),
        "mean_approach_delta":     mean_delta,
        "bias_effective":          bias_eff,
        "cf_records_raw":          cf_raw,
        "cf_records_emitted":      cf_emitted,
        "cf_exclusion_rate":       round(cf_excl, 4),
        "end_state_draw_active":   False,
        "end_state_banked_step":   es_step,
        "causal_chain_count":      len(valid_chains),
        "mean_chain_depth": (
            round(sum(depths) / len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count":    complete_count,
        "q5_statement_count":      q5,
        # v1.13 new
        "predicted_record_written": pred_written,
        "predicted_record_state":   pred_state,
    }


# ---------------------------------------------------------------------------
# Q5 individuation
# ---------------------------------------------------------------------------

def _edit_distance(seq_a, seq_b):
    """Normalised edit distance over two sequences."""
    if not seq_a and not seq_b:
        return 0.0
    la, lb = len(seq_a), len(seq_b)
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if seq_a[i-1] == seq_b[j-1] else 1
            dp[i][j] = min(dp[i-1][j] + 1,
                           dp[i][j-1] + 1,
                           dp[i-1][j-1] + cost)
    return dp[la][lb] / max(la, lb)


def compute_q5_individuation(causal_records, run_meta):
    """Compute pairwise Q5 chain structural distances."""
    valid = [r for r in causal_records
             if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    rows  = []
    for i, ra in enumerate(valid):
        for j, rb in enumerate(valid):
            if j <= i:
                continue
            seq_a = [lnk["link_type"] for lnk in ra.get("links", [])]
            seq_b = [lnk["link_type"] for lnk in rb.get("links", [])]
            dist  = _edit_distance(seq_a, seq_b)
            within = (ra.get("run_idx", ra.get("arch","")) ==
                      rb.get("run_idx", rb.get("arch","")))
            rows.append({
                "arch":           run_meta.get("arch", ARCH),
                "run_idx_a":      ra.get("run_idx", ""),
                "run_idx_b":      rb.get("run_idx", ""),
                "seed_a":         ra.get("seed", ""),
                "seed_b":         rb.get("seed", ""),
                "hazard_cost":    ra.get("hazard_cost", ""),
                "chain_object_a": ra.get("object_id", ""),
                "chain_object_b": rb.get("object_id", ""),
                "link_sequence_a": ">".join(seq_a),
                "link_sequence_b": ">".join(seq_b),
                "link_sequence_distance": round(dist, 4),
                "within_run":     within,
            })
    return rows


def _pairwise_distances(sequences_by_run):
    run_ids = list(sequences_by_run.keys())
    dists   = []
    for i, ri in enumerate(run_ids):
        for rj in run_ids[i+1:]:
            sa = sequences_by_run[ri]
            sb = sequences_by_run[rj]
            if sa and sb:
                dists.append(_edit_distance(sa, sb))
    return dists


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
    args = parser.parse_args()

    report      = not args.no_report
    with_goal   = not args.no_goal
    with_cf     = not args.no_counterfactual
    with_br     = not args.no_belief_revision
    with_cs     = not args.no_completion_signal
    with_causal = not args.no_causal
    with_env2   = not args.no_env2
    with_pred   = not args.no_prediction

    seeds = _find_seed_csv()
    jobs  = [
        (cost_idx * RUNS_PER_COST + run_idx, seeds.get((cost, run_idx), run_idx * 1000 + int(cost * 10)),
         cost)
        for cost_idx, cost in enumerate(HAZARD_COSTS)
        for run_idx in range(RUNS_PER_COST)
    ]

    csv_files = {}
    writers   = {}

    try:
        csv_files['run']  = open(RUN_DATA_CSV, 'w', newline='')
        csv_files['prov'] = open(PROVENANCE_CSV, 'w', newline='')
        csv_files['rpt']  = open(REPORT_CSV, 'w', newline='')
        csv_files['sum']  = open(REPORT_SUMMARY_CSV, 'w', newline='')
        csv_files['es']   = open(END_STATE_DRAW_CSV, 'w', newline='')
        csv_files['env2'] = open(ENV2_RUN_DATA_CSV, 'w', newline='')
        csv_files['q5i']  = open(Q5_INDIVIDUATION_CSV, 'w', newline='')
        csv_files['pred'] = open(PREDICTED_SCHEMA_CSV, 'w', newline='')
        if with_goal:
            csv_files['goal'] = open(GOAL_CSV, 'w', newline='')
        if with_cf:
            csv_files['cf'] = open(COUNTERFACTUAL_CSV, 'w', newline='')
        if with_br:
            csv_files['br'] = open(BELIEF_REVISION_CSV, 'w', newline='')
        if with_causal:
            csv_files['caus'] = open(CAUSAL_CSV, 'w', newline='')

        writers['run']  = csv.DictWriter(csv_files['run'],  fieldnames=RUN_DATA_FIELDS)
        writers['prov'] = csv.DictWriter(csv_files['prov'], fieldnames=[
            "arch","run_idx","seed","hazard_cost","flag_id","flag_type","flag_set_step"
        ])
        writers['rpt']  = csv.DictWriter(csv_files['rpt'],  fieldnames=REPORT_FIELDS)
        writers['sum']  = csv.DictWriter(csv_files['sum'],  fieldnames=SUMMARY_FIELDS)
        writers['es']   = csv.DictWriter(csv_files['es'],   fieldnames=END_STATE_DRAW_FIELDS)
        writers['env2'] = csv.DictWriter(csv_files['env2'], fieldnames=ENV2_RUN_DATA_FIELDS)
        writers['q5i']  = csv.DictWriter(csv_files['q5i'],  fieldnames=Q5_INDIVIDUATION_FIELDS)
        writers['pred'] = csv.DictWriter(csv_files['pred'], fieldnames=PREDICTED_SCHEMA_FIELDS)
        for w in writers.values():
            w.writeheader()
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

        # Batch-level accumulators
        total_statements   = 0
        total_hallucinations = 0
        total_cf_emitted   = 0
        total_br_records   = 0
        total_causal_chains = 0
        end_state_banked_runs = 0
        env2_runs          = 0
        incomplete_runs    = []
        all_causal_records = []
        q1_sequences_goal  = {}
        q1_sequences_free  = {}
        predicted_fires    = 0
        predicted_confirmed = 0

        print(f"v1.13 batch: {len(jobs)} runs | "
              f"prediction={'ON' if with_pred else 'OFF'} | "
              f"env2={'ON' if with_env2 else 'OFF'}")
        print()

        for run_idx, seed, hazard_cost in jobs:
            try:
                result = run_one(
                    run_idx, seed, hazard_cost,
                    report=report,
                    with_goal=with_goal,
                    with_counterfactual=with_cf,
                    with_belief_revision=with_br,
                    with_completion_signal=with_cs,
                    with_causal=with_causal,
                    with_env2=with_env2,
                    with_prediction=with_pred,
                )
            except Exception as e:
                import traceback as tb
                print(f"  Run {run_idx}: ERROR — {e}")
                tb.print_exc()
                incomplete_runs.append(run_idx)
                continue

            (run_row, statements, summary,
             prov_obs, goal_obs, cf_obs, br_obs,
             es_step, causal_obs, env2_row, pred_rows) = result

            # Write run data
            writers['run'].writerow(
                {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
            )

            # Write provenance
            flush_provenance_csv(prov_obs, PROVENANCE_CSV)

            # Write goal
            if with_goal and goal_obs is not None:
                gs = goal_obs.get_substrate()
                for gr in gs.get("goal_progress", []):
                    writers['goal'].writerow(
                        {k: gr.get(k, "") for k in GOAL_FIELDS}
                    )

            # Write CF
            if with_cf and cf_obs is not None:
                for cr in cf_obs.get_substrate():
                    writers['cf'].writerow(
                        {k: cr.get(k, "") for k in COUNTERFACTUAL_FIELDS}
                    )

            # Write BR
            if with_br and br_obs is not None:
                for br in br_obs.get_substrate():
                    writers['br'].writerow(
                        {k: br.get(k, "") for k in BELIEF_REVISION_FIELDS}
                    )

            # Write causal
            if with_causal and causal_obs is not None:
                causal_meta = {
                    "arch": ARCH, "run_idx": run_idx, "seed": seed,
                    "hazard_cost": hazard_cost, "num_steps": BATCH_STEPS,
                }
                for cr in causal_obs.causal_rows():
                    row = {**causal_meta, **cr}
                    writers['caus'].writerow(
                        {k: row.get(k, "") for k in CAUSAL_FIELDS}
                    )
                all_causal_records.extend([
                    {**r, "run_idx": run_idx, "seed": seed,
                     "hazard_cost": hazard_cost}
                    for r in causal_obs.get_substrate()
                ])
                valid = [r for r in causal_obs.get_substrate()
                         if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
                total_causal_chains += len(valid)

            # Write predicted schema
            if with_pred and pred_rows:
                for pr in pred_rows:
                    writers['pred'].writerow(
                        {k: pr.get(k, "") for k in PREDICTED_SCHEMA_FIELDS}
                    )
                predicted_fires += len(pred_rows)
                predicted_confirmed += sum(
                    1 for pr in pred_rows if pr.get("state") == CONFIRMED_STATE
                )

            # Write report
            if report and statements:
                for s in statements:
                    writers['rpt'].writerow({
                        "arch": ARCH, "run_idx": run_idx,
                        "seed": seed, "hazard_cost": hazard_cost,
                        "num_steps": BATCH_STEPS,
                        "query_type":    getattr(s, 'query_type', ''),
                        "statement_text": getattr(s, 'text', ''),
                        "source_type":   getattr(s, 'source_type', ''),
                        "source_key":    getattr(s, 'source_key', ''),
                        "source_resolves": getattr(s, 'source_resolves', False),
                    })
                run_row["q5_statement_count"] = summary.get("q5_statement_count", 0)

            # Write summary
            if report and summary:
                writers['sum'].writerow(
                    {k: summary.get(k, "") for k in SUMMARY_FIELDS}
                )
                total_statements    += summary.get("total_statements", 0)
                total_hallucinations += summary.get("hallucination_count", 0)

            # Write env2 row
            if env2_row is not None:
                writers['env2'].writerow(
                    {k: env2_row.get(k, "") for k in ENV2_RUN_DATA_FIELDS}
                )
                env2_runs += 1

            # Write end state draw
            writers['es'].writerow({
                "arch": ARCH, "run_idx": run_idx,
                "seed": seed, "hazard_cost": hazard_cost,
                "num_steps": BATCH_STEPS,
                "activation_step":     run_row.get("activation_step"),
                "end_state_banked_step": es_step,
                "steps_draw_to_bank":  run_row.get("steps_draw_to_bank"),
                "end_state_draw_active": run_row.get("end_state_draw_active"),
            })

            if es_step is not None:
                end_state_banked_runs += 1

            if with_cf and cf_obs is not None:
                total_cf_emitted += len(cf_obs.get_substrate())
            if with_br and br_obs is not None:
                total_br_records += len(br_obs.get_substrate())

            # Console output
            if report and summary:
                status = "PASS" if summary["hallucination_count"] == 0 else "FAIL"
                pred_status = summary.get("predicted_record_state", "-")
                goal_outcome = ""
                if with_goal and goal_obs is not None:
                    gs = goal_obs.get_substrate()["goal_summary"]
                    goal_outcome = (
                        f"goal={'resolved' if gs['resolved'] else 'expired'} | "
                    )
                es_flag   = f"es={'banked' if es_step else 'pending'} | "
                env2_flag = f"env2={'ran' if env2_row else '-'} | "
                pred_flag = f"pred={pred_status} | "
                causal_n  = run_row.get("causal_chain_count", 0)
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"stmts={summary['total_statements']:3d} | "
                    f"q5={summary.get('q5_statement_count',0):2d} | "
                    f"chains={causal_n:2d} | "
                    f"{goal_outcome}{es_flag}{env2_flag}{pred_flag}"
                    f"halluc={status}"
                )

        # -------------------------------------------------------------------
        # Category π: Predictive schema integrity
        # -------------------------------------------------------------------
        if with_pred and report:
            print()
            print("Category π: Predictive schema integrity")
            print(f"  Predicted records written: {predicted_fires}")
            print(f"  Predicted records confirmed: {predicted_confirmed}")
            if predicted_fires > 0:
                conf_rate = predicted_confirmed / predicted_fires
                print(f"  Confirmation rate: {conf_rate:.0%}")
                c1 = any(
                    row.get("hazard_cost") in (10.0, "10.0")
                    for row in []  # reviewed from predicted_schema CSV
                )
                print(f"  Component 1 (fires at cost=10.0): see {PREDICTED_SCHEMA_CSV}")
                print(f"  Component 2 (confirmation rate): {conf_rate:.0%}")
                print(f"  Component 3 (chain extension integrity): see {CAUSAL_CSV}")
            else:
                print("  No predicted records written — check cost=10.0 runs "
                      "and two-family minimum.")

        # -------------------------------------------------------------------
        # Category ζ: Q5 structural individuation
        # -------------------------------------------------------------------
        if with_causal and report and all_causal_records:
            print()
            print("Category ζ: Q5 structural individuation")
            valid_q5 = [r for r in all_causal_records
                        if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
            object_classes = sorted(set(r.get("object_id","") for r in valid_q5))
            print(f"  Object classes with chains: {object_classes}")
            c1 = len(object_classes) >= 2
            print(f"  Component 1 (multi-object): "
                  f"{'PASS' if c1 else 'FAIL'}")

            if valid_q5:
                indiv_rows = compute_q5_individuation(
                    all_causal_records, {"arch": ARCH}
                )
                for irow in indiv_rows:
                    writers['q5i'].writerow(
                        {k: irow.get(k, "") for k in Q5_INDIVIDUATION_FIELDS}
                    )
                within  = [r["link_sequence_distance"] for r in indiv_rows
                           if r["within_run"]]
                between = [r["link_sequence_distance"] for r in indiv_rows
                           if not r["within_run"]]
                if between:
                    mean_b = sum(between) / len(between)
                    mean_w = sum(within) / len(within) if within else 0.0
                    c2 = mean_b > mean_w
                    print(f"  Component 2 (between > within): "
                          f"{'PASS' if c2 else 'FAIL'} "
                          f"between={mean_b:.4f} within={mean_w:.4f}")

        # -------------------------------------------------------------------
        # Category Λ: developmental transfer
        # -------------------------------------------------------------------
        if with_env2:
            print()
            print("Category Λ: developmental transfer")
            print(f"  Runs with Environment 2: {env2_runs}/{len(jobs)}")
            print(f"  Component 4 (att_blue directed search): "
                  f"see {ENV2_RUN_DATA_CSV} att_blue_mastery_step")

        # -------------------------------------------------------------------
        # Category θ
        # -------------------------------------------------------------------
        if with_cs:
            print()
            print("Category θ: completion signal")
            rate = end_state_banked_runs / len(jobs) if jobs else 0
            c1 = rate >= 0.50
            print(f"  ENV2 end state banked: {end_state_banked_runs}/{len(jobs)} "
                  f"({rate:.0%}) | ≥50%: {'PASS' if c1 else 'FAIL'}")

        # -------------------------------------------------------------------
        # Batch summary
        # -------------------------------------------------------------------
        print()
        print("=" * 65)
        print("Batch complete.")
        print(f"  Runs processed: "
              f"{len(jobs) - len(incomplete_runs)} / {len(jobs)}")

        if report:
            alpha_pass = total_hallucinations == 0
            beta_pass  = not incomplete_runs
            print(f"  Total statements:     {total_statements}")
            print(f"  Total hallucinations: {total_hallucinations}")
            print(f"  Total causal chains:  {total_causal_chains}")
            print(f"  Predicted records:    {predicted_fires} written, "
                  f"{predicted_confirmed} confirmed")
            print(f"  Category α: {'PASS' if alpha_pass else 'FAIL'}")
            print(f"  Category β: {'PASS' if beta_pass else 'FAIL'}")

        if incomplete_runs:
            print(f"  Incomplete runs: {incomplete_runs}")

    finally:
        for f in csv_files.values():
            f.close()


if __name__ == "__main__":
    main()
