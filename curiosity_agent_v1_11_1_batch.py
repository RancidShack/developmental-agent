"""
curiosity_agent_v1_11_batch.py
--------------------------------
v1.11 batch runner.

NEW AT V1.11
  - V111CausalObserver: tenth parallel observer. Runs post-simulation
    on the assembled SubstrateBundle. Constructs auditable causal chains
    for each resolved_surprise event. Adds Q5 (why_this_arc) statements
    to the biographical register. causal_v1_11.csv output.

  - Next-environment architecture: when environment_complete fires in
    bundle.provenance, the batch runner instantiates a second V17World
    (seed_env2 = seed + 10000). The agent's Q-table and provenance
    substrate carry over. Observer substrates reset for Environment 2.
    env2_run_data_v1_11.csv output.

ADDITIVE DISCIPLINE
  --no-causal:  disables causal observer; Q5 absent; all Q1–Q4 outputs
                byte-identical to v1.10 at matched seeds.
  --no-env2:    skips second-environment architecture regardless of
                environment_complete status.

CONDITIONALITY (pre-registered §2.4)
  Next-environment architecture runs only if at least 30% of pre-flight
  runs (3/10) produce environment_complete records. The batch runner
  checks this automatically after pre-flight; if threshold is not met,
  --no-env2 is implied and a warning is printed.

SEED SOURCE
  run_data_v1_10_1.csv (primary). Falls back to run_data_v1_9.csv if
  v1.10.1 data keys differ.

PRE-FLIGHT
  Run Level-12 re-run (--no-causal) then Level-13: verify_v1_11_level13.py

Usage:
    python curiosity_agent_v1_11_batch.py [--no-report]
                                           [--no-goal]
                                           [--no-counterfactual]
                                           [--no-belief-revision]
                                           [--no-completion-signal]
                                           [--no-causal]
                                           [--no-env2]
"""

import argparse
import csv
import os
import sys
import statistics

import numpy as np

import v1_11_observer_substrates  # noqa: F401
from v1_11_observer_substrates import build_bundle_from_observers

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_10_agent import V110Agent
from v1_7_agent  import V17Agent

from v1_1_provenance                import V1ProvenanceStore
from v1_3_schema_extension          import V13SchemaObserver
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

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_CSV_PRIMARY   = "run_data_v1_10_1.csv"
SEED_CSV_FALLBACK  = "run_data_v1_9.csv"
RUN_DATA_CSV       = "run_data_v1_11.csv"
PROVENANCE_CSV     = "provenance_v1_11.csv"
GOAL_CSV           = "goal_v1_11.csv"
COUNTERFACTUAL_CSV = "counterfactual_v1_11.csv"
BELIEF_REVISION_CSV = "belief_revision_v1_11.csv"
CAUSAL_CSV         = "causal_v1_11.csv"
REPORT_CSV         = "report_v1_11.csv"
REPORT_SUMMARY_CSV = "report_summary_v1_11.csv"
END_STATE_DRAW_CSV = "end_state_draw_log_v1_11.csv"
ENV2_RUN_DATA_CSV  = "env2_run_data_v1_11.csv"

BATCH_STEPS    = 320_000
HAZARD_COSTS   = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST  = 10
ARCH           = "v1_11"
ENV2_SEED_OFFSET = 10_000   # pre-registered; seed_env2 = seed_env1 + 10000

# ---------------------------------------------------------------------------
# Field definitions
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
    # v1.11 new
    "causal_chain_count",
    "mean_chain_depth",
    "complete_chain_count",
    "q5_statement_count",
    "env2_ran",
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
    "env2_end_state_banked_step",
    "env2_yellow_surprise_step",
    "env2_yellow_resolution_window",
    "env2_q5_chain_count",
    "env2_q5_mean_chain_depth",
]


# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

def load_seeds(path):
    seeds = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if int(row["num_steps"]) == BATCH_STEPS:
                    key = (float(row["hazard_cost"]), int(row["run_idx"]))
                    seeds[key] = int(row["seed"])
            except (ValueError, KeyError):
                continue
    return seeds


def _find_seed_csv():
    for path in (SEED_CSV_PRIMARY, SEED_CSV_FALLBACK):
        if os.path.exists(path):
            seeds = load_seeds(path)
            if seeds:
                print(f"  Seed source: {path} ({len(seeds)} seeds)")
                return seeds
    return {}


# ---------------------------------------------------------------------------
# Single environment run
# ---------------------------------------------------------------------------

def _run_environment(
    run_idx, seed, hazard_cost, num_steps,
    with_goal=True, with_counterfactual=True,
    with_belief_revision=True, with_completion_signal=True,
    env_number=1,
    carry_agent=None,
    carry_prov_obs=None,
):
    """Run one environment. Returns run artefacts.

    Parameters
    ----------
    carry_agent : V110Agent or None
        If not None, reuse this agent's Q-table for Environment 2.
    carry_prov_obs : V1ProvenanceStore or None
        If not None, reuse this provenance store for Environment 2.
        The existing records carry over; new records accumulate.
    """
    np.random.seed(seed)

    world = V17World(hazard_cost=hazard_cost, seed=seed)
    AgentClass = V110Agent if with_completion_signal else V17Agent

    if carry_agent is not None:
        # Reuse agent; update world reference
        agent = carry_agent
        agent.world = world
        # Reset end_state_banked for new environment
        if hasattr(agent, 'end_state_banked'):
            agent.end_state_banked = False
        if hasattr(agent, 'activation_step'):
            agent.activation_step = None
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

    from curiosity_agent_v1_7_world import (
        FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ
    )
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

    schema_obs = V13SchemaObserver(agent, world, meta)
    family_obs = V13FamilyObserver(agent, world, meta,
                                   provenance_store=prov_obs)
    comp_obs   = V14ComparisonObserver(family_obs, meta)
    pe_obs     = V15PredictionErrorObserver(agent, world, meta)

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

    br_obs = None
    if with_belief_revision:
        br_obs = V110BeliefRevisionObserver(
            agent, world, meta,
            prediction_error_obs=pe_obs,
            provenance_obs=prov_obs,
            counterfactual_obs=cf_obs,
        )

    observers = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs]
    if goal_obs is not None:
        observers.append(goal_obs)
    if cf_obs is not None:
        observers.append(cf_obs)
    if br_obs is not None:
        observers.append(br_obs)

    state = world.observe()
    end_state_banked_step = None

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
            agent_pos     = getattr(world, 'agent_pos', None)
            obj_positions = getattr(world, 'object_positions', {})
            for bias_oid in br_obs.active_biased_objects(step):
                obj_pos = obj_positions.get(bias_oid)
                if obj_pos is not None and agent_pos is not None:
                    import math
                    intrinsic += br_obs.preference_bias_reward(
                        bias_oid, step, moving_closer=True
                    )

        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)
        state = obs_next

        if (end_state_banked_step is None
                and getattr(agent, 'end_state_banked', False)):
            prov_obs.on_end_state_banked(step)
            end_state_banked_step = step

    for obs in observers:
        obs.on_run_end(num_steps)

    # Write phase boundary into meta so V111CausalObserver._check_phase1
    # can read it. phase_1_end_step is set on the agent during simulation.
    meta['phase_1_end_step'] = getattr(agent, 'phase_1_end_step', None)
    meta['phase_2_end_step'] = getattr(agent, 'phase_2_end_step', None)

    return dict(
        agent=agent,
        prov_obs=prov_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comp_obs=comp_obs,
        pe_obs=pe_obs,
        goal_obs=goal_obs,
        cf_obs=cf_obs,
        br_obs=br_obs,
        end_state_banked_step=end_state_banked_step,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Full run (one or two environments)
# ---------------------------------------------------------------------------

def run_one(run_idx, seed, hazard_cost,
            report=True,
            with_goal=True, with_counterfactual=True,
            with_belief_revision=True, with_completion_signal=True,
            with_causal=True, with_env2=True):

    # ---- Environment 1 ----
    env1 = _run_environment(
        run_idx=run_idx, seed=seed,
        hazard_cost=hazard_cost, num_steps=BATCH_STEPS,
        with_goal=with_goal,
        with_counterfactual=with_counterfactual,
        with_belief_revision=with_belief_revision,
        with_completion_signal=with_completion_signal,
        env_number=1,
    )

    agent    = env1['agent']
    prov_obs = env1['prov_obs']

    # Check if environment_complete fired
    env1_complete = (env1['end_state_banked_step'] is not None)

    # ---- Environment 2 (conditional) ----
    env2 = None
    env2_seed = None
    if with_env2 and env1_complete:
        env2_seed = seed + ENV2_SEED_OFFSET
        env2 = _run_environment(
            run_idx=run_idx, seed=env2_seed,
            hazard_cost=hazard_cost, num_steps=BATCH_STEPS,
            with_goal=with_goal,
            with_counterfactual=with_counterfactual,
            with_belief_revision=with_belief_revision,
            with_completion_signal=with_completion_signal,
            env_number=2,
            carry_agent=agent,
            carry_prov_obs=prov_obs,
        )

    # ---- Bundle assembly (on completed env, or env2 if ran) ----
    active_env  = env2 if env2 is not None else env1
    active_meta = active_env['meta']

    causal_obs = None
    if with_causal:
        causal_obs = V111CausalObserver(active_meta)

    statements, summary = [], {}
    causal_records = []
    env2_row = None

    if report:
        bundle = build_bundle_from_observers(
            provenance_obs       = active_env['prov_obs'],
            schema_obs           = active_env['schema_obs'],
            family_obs           = active_env['family_obs'],
            comparison_obs       = active_env['comp_obs'],
            prediction_error_obs = active_env['pe_obs'],
            run_meta             = active_meta,
            goal_obs             = active_env['goal_obs'],
            counterfactual_obs   = active_env['cf_obs'],
            belief_revision_obs  = active_env['br_obs'],
            causal_obs           = None,   # populated below
        )

        br_obs = active_env['br_obs']
        if br_obs is not None:
            pe_records = getattr(bundle, 'prediction_error', None) or []
            br_obs.process_pe_substrate(pe_records)
            bundle.belief_revision = br_obs.get_substrate()

        # Build causal chains now that bundle is complete
        if causal_obs is not None:
            causal_obs.build_causal_chains(bundle)
            bundle.causal = causal_obs.get_substrate()

        layer      = V16ReportingLayer(bundle)
        statements = layer.generate_report()
        causal_records = causal_obs.get_substrate() if causal_obs else []

        # Env2 row
        if env2 is not None:
            env2_row = _build_env2_row(
                run_idx, seed, hazard_cost, env2_seed,
                env2, causal_records
            )

        summary = _compute_summary(
            run_idx, seed, hazard_cost, statements,
            active_env['goal_obs'],
            active_env['cf_obs'],
            active_env['br_obs'],
            causal_records,
            active_env['end_state_banked_step'],
            env2 is not None,
        )

    # Build run_row from env1 (env1 is the primary development record)
    run_row = _build_run_row(
        run_idx, seed, hazard_cost, env1, causal_records,
        env2 is not None
    )

    return (run_row, statements, summary,
            env1['prov_obs'], env1['goal_obs'],
            env1['cf_obs'], env1['br_obs'],
            env1['end_state_banked_step'],
            causal_obs, env2_row)


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
            "goal_type":               g["goal_type"],
            "goal_target_id":          g["target_id"],
            "goal_step_budget":        g["step_budget"],
            "goal_resolved":           g["resolved"],
            "goal_resolution_step":    g["resolution_step"],
            "goal_budget_remaining":   g["budget_remaining"],
            "goal_expired":            g["expired"],
            "goal_last_progress_step": g["last_progress_step"],
            "goal_resolution_window":  g["goal_resolution_window"],
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
    deltas      = [r.get("approach_delta", 0) for r in br_records]

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
        "arch":                ARCH,
        "run_idx":             run_idx,
        "seed":                seed,
        "hazard_cost":         hazard_cost,
        "num_steps":           BATCH_STEPS,
        "phase_1_end_step":    agent.phase_1_end_step,
        "phase_2_end_step":    agent.phase_2_end_step,
        "time_to_first_flag":  agent.time_to_first_flag,
        "time_to_second_flag": agent.time_to_second_flag,
        "time_to_final_flag":  agent.time_to_final_flag,
        "total_cost_incurred": agent.total_cost_incurred,
        "time_to_first_mastery": agent.time_to_first_mastery,
        "time_to_final_mastery": agent.time_to_final_mastery,
        "mastery_order_sequence": str(agent.mastery_order_sequence),
        "activation_step":     activation_step,
        "end_state_found_step": agent.end_state_found_step,
        "end_state_banked":    agent.end_state_banked,
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
        "mean_chain_depth":               (
            round(sum(depths) / len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count":           complete_count,
        "q5_statement_count":             0,   # filled after report
        "env2_ran":                       env2_ran,
    }


def _build_env2_row(run_idx, seed, hazard_cost, env2_seed,
                    env2, causal_records):
    agent    = env2['agent']
    pe_obs   = env2['pe_obs']
    es_step  = env2['end_state_banked_step']

    pe_summary = pe_obs.summary_metrics()
    activation_step = getattr(agent, 'activation_step', None)

    # Yellow resolution window in env2
    yel_win = pe_summary.get("yellow_resolution_window")

    # Q5 chains from env2 causal records (env field = 2)
    env2_chains = [r for r in causal_records
                   if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    depths = [r["chain_depth"] for r in env2_chains]

    return {
        "arch":                    ARCH,
        "run_idx":                 run_idx,
        "seed":                    seed,
        "hazard_cost":             hazard_cost,
        "env2_seed":               env2_seed,
        "env2_activation_step":    activation_step,
        "env2_end_state_banked_step": es_step,
        "env2_yellow_surprise_step": pe_summary.get("yellow_pre_transition_entries"),
        "env2_yellow_resolution_window": yel_win,
        "env2_q5_chain_count":         len(env2_chains),
        "env2_q5_mean_chain_depth":    (
            round(sum(depths) / len(depths), 2) if depths else 0.0
        ),
    }


def _compute_summary(run_idx, seed, hazard_cost, statements,
                     goal_obs, cf_obs, br_obs, causal_records,
                     es_banked_step, env2_ran):
    stmts_q1 = [s for s in statements if s.query_type == "what_learned"]
    stmts_q2 = [s for s in statements if s.query_type == "how_related"]
    stmts_q3 = [s for s in statements if s.query_type == "where_surprised"]
    stmts_q4 = [s for s in statements if s.query_type == "where_held_back"]
    stmts_q5 = [s for s in statements if s.query_type == "why_this_arc"]
    br_stmts = [s for s in stmts_q3 if s.source_type == "belief_revision"]
    halluc   = sum(1 for s in statements if not s.source_resolves)

    q1_prov_keys = {
        s.source_key for s in stmts_q1 if s.source_type == "provenance"
    }
    q3_cells, q3_resolved = set(), 0
    for s in stmts_q3:
        if s.source_type == "prediction_error" and s.source_resolves:
            q3_cells.add(s.source_key)
            if "resolution window" in s.text.lower():
                q3_resolved += 1

    cf_records = cf_obs.get_substrate() if cf_obs else []
    cf_raw     = cf_obs.raw_records_count() if cf_obs else 0
    cf_emitted = len(cf_records)
    cf_excl    = (1.0 - cf_emitted / cf_raw) if cf_raw > 0 else 0.0
    gr_count   = sum(1 for r in cf_records if r.get("goal_relevant"))
    br_records = br_obs.get_substrate() if br_obs else []
    deltas     = [r.get("approach_delta", 0) for r in br_records]
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    bias_eff   = any(d > 0 for d in deltas)

    valid_chains   = [r for r in causal_records
                      if r.get("chain_depth", 0) >= CHAIN_DEPTH_MINIMUM]
    depths         = [r["chain_depth"] for r in valid_chains]
    complete_count = sum(1 for r in valid_chains if r.get("chain_complete"))

    relevance_count = sum(1 for s in stmts_q1 if s.source_type == "goal")
    goal_stmt = next(
        (s for s in stmts_q3 if s.source_type == "goal"), None
    )
    draw_active = es_banked_step is not None

    return {
        "arch":                ARCH,
        "run_idx":             run_idx,
        "seed":                seed,
        "hazard_cost":         hazard_cost,
        "num_steps":           BATCH_STEPS,
        "total_statements":    len(statements),
        "statements_q1":       len(stmts_q1),
        "statements_q2":       len(stmts_q2),
        "statements_q3":       len(stmts_q3),
        "statements_q4":       len(stmts_q4),
        "statements_q5":       len(stmts_q5),
        "hallucination_count": halluc,
        "q1_formation_depth":  len(q1_prov_keys),
        "q3_surprise_cells":   len(q3_cells),
        "q3_resolution_stated": q3_resolved,
        "report_complete": (
            len(stmts_q1) > 0
            and len(stmts_q2) > 0
            and len(stmts_q3) > 0
            and halluc == 0
        ),
        "statements_with_relevance_markers": relevance_count,
        "goal_statement_present":  goal_stmt is not None,
        "goal_resolution_stated":  (
            goal_stmt is not None
            and goal_stmt.source_key == "goal_resolved"
        ),
        "q4_statement_count":             len(stmts_q4),
        "suppressed_approach_count":      cf_emitted,
        "goal_relevant_suppressed_count": gr_count,
        "br_statement_count":             len(br_stmts),
        "revised_expectation_count":      len(br_records),
        "mean_approach_delta":            round(mean_delta, 3),
        "bias_effective":                 bias_eff,
        "cf_records_raw":                 cf_raw,
        "cf_records_emitted":             cf_emitted,
        "cf_exclusion_rate":              round(cf_excl, 4),
        "end_state_draw_active":          draw_active,
        "end_state_banked_step":          es_banked_step,
        "causal_chain_count":             len(valid_chains),
        "mean_chain_depth":               (
            round(sum(depths) / len(depths), 2) if depths else 0.0
        ),
        "complete_chain_count":           complete_count,
        "q5_statement_count":             len(stmts_q5),
    }


# ---------------------------------------------------------------------------
# Edit distance for Category γ
# ---------------------------------------------------------------------------

def _edit_distance_normalised(seq_a, seq_b):
    if not seq_a and not seq_b:
        return 0.0
    n, m = len(seq_a), len(seq_b)
    dp   = list(range(m + 1))
    for i in range(1, n + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, m + 1):
            temp  = dp[j]
            dp[j] = prev if seq_a[i-1] == seq_b[j-1] else 1 + min(prev, dp[j], dp[j-1])
            prev  = temp
    return dp[m] / max(n, m)


def _pairwise_distances(sequences):
    run_ids   = sorted(sequences.keys())
    distances = []
    for i in range(len(run_ids)):
        for j in range(i + 1, len(run_ids)):
            distances.append(_edit_distance_normalised(
                sequences[run_ids[i]], sequences[run_ids[j]]
            ))
    return distances


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
    args = parser.parse_args()

    report              = not args.no_report
    with_goal           = not args.no_goal
    with_counterfactual = not args.no_counterfactual
    with_br             = not args.no_belief_revision
    with_cs             = not args.no_completion_signal
    with_causal         = not args.no_causal
    with_env2           = not args.no_env2

    seeds = _find_seed_csv()
    if not seeds:
        print("ERROR: no seed file found or no matching seeds.")
        sys.exit(1)

    jobs = []
    for cost in HAZARD_COSTS:
        for run_idx in range(RUNS_PER_COST):
            seed = seeds.get((cost, run_idx))
            if seed is None:
                print(f"WARNING: no seed for cost={cost} "
                      f"run_idx={run_idx}; skipping.")
                continue
            jobs.append((run_idx, seed, cost))

    print("v1.11 Batch — Causal Self-Explanation "
          "and the Next-Environment Architecture")
    print(f"  Causal observer:    {'enabled' if with_causal else 'DISABLED'}")
    print(f"  Next-environment:   {'enabled' if with_env2 else 'DISABLED'}")
    print(f"  Goal layer:         {'enabled' if with_goal else 'DISABLED'}")
    print(f"  Counterfactual:     {'enabled' if with_counterfactual else 'DISABLED'}")
    print(f"  Belief revision:    {'enabled' if with_br else 'DISABLED'}")
    print(f"  Completion signal:  {'enabled' if with_cs else 'DISABLED'}")
    print(f"  Reporting:          {'enabled' if report else 'disabled'}")
    print(f"  Total runs:         {len(jobs)}")
    print()

    total_hallucinations = 0
    total_statements     = 0
    total_cf_emitted     = 0
    total_br_records     = 0
    total_causal_chains  = 0
    end_state_banked_runs = 0
    env2_runs            = 0
    incomplete_runs      = []

    q1_sequences_goal = {}
    q1_sequences_free = {}
    goal_rows         = []

    csv_files = {
        "rd":   open(RUN_DATA_CSV,        "w", newline=""),
        "goal": open(GOAL_CSV,            "w", newline=""),
        "cf":   open(COUNTERFACTUAL_CSV,  "w", newline=""),
        "br":   open(BELIEF_REVISION_CSV, "w", newline=""),
        "caus": open(CAUSAL_CSV,          "w", newline=""),
        "rep":  open(REPORT_CSV,          "w", newline=""),
        "sum":  open(REPORT_SUMMARY_CSV,  "w", newline=""),
        "es":   open(END_STATE_DRAW_CSV,  "w", newline=""),
        "env2": open(ENV2_RUN_DATA_CSV,   "w", newline=""),
    }

    writers = {
        "rd":   csv.DictWriter(csv_files["rd"],   fieldnames=RUN_DATA_FIELDS),
        "goal": csv.DictWriter(csv_files["goal"], fieldnames=GOAL_FIELDS),
        "cf":   csv.DictWriter(csv_files["cf"],   fieldnames=COUNTERFACTUAL_FIELDS),
        "br":   csv.DictWriter(csv_files["br"],   fieldnames=BELIEF_REVISION_FIELDS),
        "caus": csv.DictWriter(csv_files["caus"], fieldnames=CAUSAL_FIELDS),
        "rep":  csv.DictWriter(csv_files["rep"],  fieldnames=REPORT_FIELDS),
        "sum":  csv.DictWriter(csv_files["sum"],  fieldnames=SUMMARY_FIELDS),
        "es":   csv.DictWriter(csv_files["es"],   fieldnames=END_STATE_DRAW_FIELDS),
        "env2": csv.DictWriter(csv_files["env2"], fieldnames=ENV2_RUN_DATA_FIELDS),
    }

    try:
        for w in writers.values():
            w.writeheader()

        for job_num, (run_idx, seed, hazard_cost) in enumerate(jobs):
            is_first = (job_num == 0)

            try:
                result = run_one(
                    run_idx=run_idx, seed=seed, hazard_cost=hazard_cost,
                    report=report,
                    with_goal=with_goal,
                    with_counterfactual=with_counterfactual,
                    with_belief_revision=with_br,
                    with_completion_signal=with_cs,
                    with_causal=with_causal,
                    with_env2=with_env2,
                )
            except Exception as e:
                import traceback as tb
                print(f"  Run {run_idx} cost={hazard_cost}: ERROR — {e}")
                tb.print_exc()
                continue

            (run_row, statements, summary, prov_obs, goal_obs,
             cf_obs, br_obs, es_banked_step, causal_obs, env2_row) = result

            # Update q5 count in run_row
            if report:
                q5_count = summary.get("q5_statement_count", 0)
                run_row["q5_statement_count"] = q5_count

            writers["rd"].writerow(
                {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
            )
            flush_provenance_csv(prov_obs, PROVENANCE_CSV, first_run=is_first)

            if with_goal and goal_obs is not None:
                goal_row = goal_obs.goal_row()
                writers["goal"].writerow(
                    {k: goal_row.get(k, "") for k in GOAL_FIELDS}
                )
                goal_rows.append(goal_row)

            if with_counterfactual and cf_obs is not None:
                for cf_row in cf_obs.counterfactual_rows():
                    writers["cf"].writerow(
                        {k: cf_row.get(k, "") for k in COUNTERFACTUAL_FIELDS}
                    )
                total_cf_emitted += len(cf_obs.get_substrate())

            if with_br and br_obs is not None:
                for br_row in br_obs.belief_revision_rows():
                    writers["br"].writerow(
                        {k: br_row.get(k, "") for k in BELIEF_REVISION_FIELDS}
                    )
                total_br_records += len(br_obs.get_substrate())

            if with_causal and causal_obs is not None:
                for caus_row in causal_obs.causal_rows():
                    writers["caus"].writerow(
                        {k: caus_row.get(k, "") for k in CAUSAL_FIELDS}
                    )
                total_causal_chains += len(causal_obs.valid_chains())

            activation_step = run_row.get("activation_step")
            writers["es"].writerow({
                "arch":                  ARCH,
                "run_idx":               run_idx,
                "seed":                  seed,
                "hazard_cost":           hazard_cost,
                "num_steps":             BATCH_STEPS,
                "activation_step":       activation_step,
                "end_state_banked_step": es_banked_step,
                "steps_draw_to_bank":    run_row.get("steps_draw_to_bank"),
                "end_state_draw_active": run_row.get("end_state_draw_active"),
            })

            if es_banked_step is not None:
                end_state_banked_runs += 1

            if env2_row is not None:
                writers["env2"].writerow(
                    {k: env2_row.get(k, "") for k in ENV2_RUN_DATA_FIELDS}
                )
                env2_runs += 1

            if report:
                for stmt in statements:
                    writers["rep"].writerow({
                        "arch":            ARCH,
                        "run_idx":         run_idx,
                        "seed":            seed,
                        "hazard_cost":     hazard_cost,
                        "num_steps":       BATCH_STEPS,
                        "query_type":      stmt.query_type,
                        "statement_text":  stmt.text,
                        "source_type":     stmt.source_type,
                        "source_key":      stmt.source_key,
                        "source_resolves": stmt.source_resolves,
                    })
                writers["sum"].writerow(
                    {k: summary.get(k, "") for k in SUMMARY_FIELDS}
                )

                run_halluc = summary["hallucination_count"]
                total_hallucinations += run_halluc
                total_statements     += summary["total_statements"]

                if not summary["report_complete"]:
                    incomplete_runs.append((run_idx, hazard_cost))

                q1_keys_goal = [
                    s.source_key for s in statements
                    if s.query_type == "what_learned"
                    and s.source_type in ("provenance", "goal")
                ]
                q1_sequences_goal[run_idx] = q1_keys_goal

                status = (
                    "PASS" if run_halluc == 0 else f"FAIL({run_halluc})"
                )
                goal_outcome = ""
                if with_goal and goal_obs is not None:
                    gs = goal_obs.get_substrate()["goal_summary"]
                    goal_outcome = (
                        f"goal={'resolved' if gs['resolved'] else 'expired'} | "
                    )
                es_flag  = f"es={'banked' if es_banked_step else 'pending'} | "
                env2_flag = f"env2={'ran' if env2_row else '-'} | "
                causal_n = run_row.get("causal_chain_count", 0)
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"stmts={summary['total_statements']:3d} | "
                    f"q5={summary.get('q5_statement_count',0):2d} | "
                    f"chains={causal_n:2d} | "
                    f"{goal_outcome}{es_flag}{env2_flag}"
                    f"halluc={status}"
                )

                # Paired goal-free run for Category γ
                if with_goal:
                    try:
                        free_result = run_one(
                            run_idx, seed, hazard_cost,
                            report=True, with_goal=False,
                            with_counterfactual=False,
                            with_belief_revision=False,
                            with_completion_signal=False,
                            with_causal=False, with_env2=False,
                        )
                        q1_sequences_free[run_idx] = [
                            s.source_key for s in free_result[1]
                            if s.query_type == "what_learned"
                            and s.source_type == "provenance"
                        ]
                    except Exception as e:
                        import traceback as tb
                        print(f"    [paired run {run_idx}: ERROR — {e}]")
                        tb.print_exc()

    finally:
        for f in csv_files.values():
            f.close()

    # -----------------------------------------------------------------------
    # Category γ
    # -----------------------------------------------------------------------
    if report and len(q1_sequences_goal) >= 2:
        print()
        print("Category γ: biographical individuation")
        goal_distances = _pairwise_distances(q1_sequences_goal)
        min_g  = min(goal_distances)
        mean_g = sum(goal_distances) / len(goal_distances)
        floor  = 0.05
        c1_pass = min_g >= floor
        print(f"  Q1 goal-directed: n={len(goal_distances)} "
              f"min={min_g:.4f} mean={mean_g:.4f}")
        print(f"  Component 1 (min >= {floor}): "
              f"{'PASS' if c1_pass else 'FAIL'}")
        if len(q1_sequences_free) >= 2:
            free_distances = _pairwise_distances(q1_sequences_free)
            mean_f = sum(free_distances) / len(free_distances)
            direction = "higher" if mean_g > mean_f else "lower"
            print(f"  Goal-free mean={mean_f:.4f} — "
                  f"goal-directed is {direction}")

    # -----------------------------------------------------------------------
    # Category θ: completion signal persistence
    # -----------------------------------------------------------------------
    if with_cs:
        print()
        print("Category θ: completion signal persistence")
        rate = end_state_banked_runs / len(jobs) if jobs else 0
        v110_baseline = 14 / 40
        c1_pass = rate >= v110_baseline
        print(f"  End state banked: {end_state_banked_runs}/{len(jobs)} "
              f"({rate:.0%})")
        print(f"  v1.10 baseline (≥35%): {'PASS' if c1_pass else 'FAIL'}")

    # -----------------------------------------------------------------------
    # Category Σ: causal self-explanation
    # -----------------------------------------------------------------------
    if with_causal and report:
        print()
        print("Category Σ: causal self-explanation")
        print(f"  Total valid chains (depth≥{CHAIN_DEPTH_MINIMUM}): "
              f"{total_causal_chains}")
        print(f"  Q5 statements: counted in individual runs above")

    # -----------------------------------------------------------------------
    # Category Λ: developmental transfer
    # -----------------------------------------------------------------------
    if with_env2:
        print()
        print("Category Λ: developmental transfer")
        print(f"  Runs with Environment 2: {env2_runs}/{len(jobs)}")
        if env2_runs < 8:
            print(f"  NOTE: n={env2_runs} < 8 — Category Λ underpowered; "
                  f"reserved for v1.12")
        else:
            print(f"  n={env2_runs} — Category Λ evaluable; "
                  f"see env2_run_data_v1_11.csv for transfer analysis")

    # -----------------------------------------------------------------------
    # Batch summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 65)
    print("Batch complete.")
    print(f"  Runs processed: "
          f"{len(jobs) - len(incomplete_runs)} / {len(jobs)}")

    if report:
        print(f"  Total statements:     {total_statements}")
        print(f"  Total hallucinations: {total_hallucinations}")
        print(f"  Total CF emitted:     {total_cf_emitted}")
        print(f"  Total BR records:     {total_br_records}")
        print(f"  Total causal chains:  {total_causal_chains}")
        alpha_pass = total_hallucinations == 0
        beta_pass  = not incomplete_runs
        print(f"  Category α: {'PASS' if alpha_pass else 'FAIL'}")
        print(f"  Category β: {'PASS' if beta_pass else 'FAIL'}")

    if with_goal and goal_rows:
        n_resolved = sum(
            1 for r in goal_rows
            if str(r.get("goal_resolved", "")).lower() == "true"
        )
        print(f"  Goal resolved: {n_resolved}/{len(goal_rows)}")

    if incomplete_runs:
        print(f"  Incomplete runs: {incomplete_runs}")


if __name__ == "__main__":
    main()
