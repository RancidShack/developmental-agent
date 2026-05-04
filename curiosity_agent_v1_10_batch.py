"""
curiosity_agent_v1_10_batch.py
--------------------------------
v1.10 batch runner.

NEW AT V1.10
  - V110Agent: subclass of V17Agent with end_state_draw_reward().
    The Montessori wait-by-the-door completion signal: a soft draw
    (END_STATE_DRAW=+0.20) toward the END_STATE cell activates once
    activation_step fires (all attractors mastered + all hazards
    banked). 13/40 v1.9 runs banked the end state opportunistically;
    the draw is designed to raise this substantially.

  - V110BeliefRevisionObserver: ninth parallel observer. Fires
    revised_expectation records after each resolved_surprise event.
    Maintains per-object preference bias (POSITIVE_APPROACH_BIAS=+0.15,
    BIAS_DURATION=10,000, BIAS_DECAY=5,000). Q3 gains belief-revision
    statements as final entries.

  - Temporal exclusion window (K_EXCLUSION=500): applied to
    V19CounterfactualObserver at record-emission stage. Reduces CF
    record count from ~1,800/run (v1.9) to ~50–200/run.

  - environment_complete provenance record: fired when agent banks
    end state. Substrate record for v1.11 next-environment trigger.

  - belief_revision_v1_10.csv, preference_bias_log_v1_10.csv,
    end_state_draw_log_v1_10.csv: new output files.

ADDITIVE DISCIPLINE
  --no-belief-revision: disables BR observer; Q3 identical to v1.9.
  --no-completion-signal: instantiates V17Agent; draw absent.
  Both flags together + --no-counterfactual → byte-identical to v1.8.

PRE-FLIGHT
  Run Level-11 re-run then Level-12: verify_v1_10_level12.py

Usage:
    python curiosity_agent_v1_10_batch.py [--no-report]
                                           [--no-goal]
                                           [--no-counterfactual]
                                           [--no-belief-revision]
                                           [--no-completion-signal]
"""

import argparse
import csv
import os
import sys
import statistics

import numpy as np

import v1_10_observer_substrates  # noqa: F401
from v1_10_observer_substrates import build_bundle_from_observers

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_10_agent  import V110Agent
from v1_7_agent   import V17Agent

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

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_CSV             = "run_data_v1_9.csv"
RUN_DATA_CSV         = "run_data_v1_10.csv"
PROVENANCE_CSV       = "provenance_v1_10.csv"
GOAL_CSV             = "goal_v1_10.csv"
COUNTERFACTUAL_CSV   = "counterfactual_v1_10.csv"
BELIEF_REVISION_CSV  = "belief_revision_v1_10.csv"
REPORT_CSV           = "report_v1_10.csv"
REPORT_SUMMARY_CSV   = "report_summary_v1_10.csv"
END_STATE_DRAW_CSV   = "end_state_draw_log_v1_10.csv"

BATCH_STEPS   = 320_000
HAZARD_COSTS  = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST = 10
ARCH          = "v1_10"

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
    # v1.10 new
    "end_state_draw_active",
    "end_state_banked_step",
    "steps_draw_to_bank",
    "revised_expectation_count",
]

REPORT_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "query_type", "statement_text",
    "source_type", "source_key", "source_resolves",
]

SUMMARY_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "total_statements", "statements_q1", "statements_q2",
    "statements_q3", "statements_q4",
    "hallucination_count",
    "q1_formation_depth", "q3_surprise_cells", "q3_resolution_stated",
    "report_complete",
    "statements_with_relevance_markers",
    "goal_statement_present", "goal_resolution_stated",
    "q4_statement_count",
    "suppressed_approach_count", "goal_relevant_suppressed_count",
    # v1.10
    "br_statement_count", "revised_expectation_count",
    "mean_approach_delta", "bias_effective",
    "cf_records_raw", "cf_records_emitted", "cf_exclusion_rate",
    "end_state_draw_active", "end_state_banked_step",
]

END_STATE_DRAW_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "activation_step", "end_state_banked_step",
    "steps_draw_to_bank", "end_state_draw_active",
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


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def run_one(run_idx, seed, hazard_cost, report=True,
            with_goal=True, with_counterfactual=True,
            with_belief_revision=True, with_completion_signal=True):

    np.random.seed(seed)

    world = V17World(hazard_cost=hazard_cost, seed=seed)
    AgentClass = V110Agent if with_completion_signal else V17Agent
    agent = AgentClass(world, total_steps=BATCH_STEPS,
                       num_actions=NUM_ACTIONS)

    meta = {
        "arch":        ARCH,
        "hazard_cost": hazard_cost,
        "num_steps":   BATCH_STEPS,
        "run_idx":     run_idx,
        "seed":        seed,
    }

    from curiosity_agent_v1_7_world import (
        FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, DIST_OBJ
    )
    ctc = {
        "FRAME": FRAME, "NEUTRAL": NEUTRAL, "HAZARD": HAZARD,
        "ATTRACTOR": ATTRACTOR, "END_STATE": END_STATE,
        "KNOWLEDGE": KNOWLEDGE, "DIST_OBJ": DIST_OBJ,
    }

    prov_obs   = V1ProvenanceStore(agent, world, meta, ctc)
    schema_obs = V13SchemaObserver(agent, world, meta)
    family_obs = V13FamilyObserver(agent, world, meta,
                                   provenance_store=prov_obs)
    comp_obs   = V14ComparisonObserver(family_obs, meta)
    pe_obs     = V15PredictionErrorObserver(agent, world, meta)

    goal_obs = None
    if with_goal:
        goal_type, target_id, step_budget = assign_goal(run_idx, BATCH_STEPS)
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

    for step in range(BATCH_STEPS):
        for obs in observers:
            obs.on_pre_action(step)

        action   = agent.choose_action(state)
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

        # Completion signal draw
        if with_completion_signal and isinstance(agent, V110Agent):
            intrinsic += agent.end_state_draw_reward(state, obs_next)

        # Preference bias
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

        # Fire environment_complete hook
        if (end_state_banked_step is None
                and getattr(agent, 'end_state_banked', False)):
            prov_obs.on_end_state_banked(step)
            end_state_banked_step = step

    for obs in observers:
        obs.on_run_end(BATCH_STEPS)

    # Assemble run_row
    pe_summary = pe_obs.summary_metrics()

    goal_summary_fields = {}
    if goal_obs is not None:
        g = goal_obs.get_substrate()["goal_summary"]
        goal_summary_fields = {
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
    mean_delta  = sum(deltas) / len(deltas) if deltas else 0.0
    bias_eff    = any(d > 0 for d in deltas)

    activation_step  = getattr(agent, 'activation_step', None)
    draw_active      = getattr(agent, 'end_state_draw_active', False)
    steps_draw_bank  = (
        (end_state_banked_step - activation_step)
        if (end_state_banked_step is not None
            and activation_step is not None)
        else None
    )

    run_row = {
        "arch":                      ARCH,
        "run_idx":                   run_idx,
        "seed":                      seed,
        "hazard_cost":               hazard_cost,
        "num_steps":                 BATCH_STEPS,
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
        **goal_summary_fields,
        "suppressed_approach_count":      cf_emitted,
        "goal_relevant_suppressed_count": gr_count,
        "suppressed_approach_objects":    obj_list,
        "cf_records_raw":                 cf_raw,
        "cf_records_emitted":             cf_emitted,
        "cf_exclusion_rate":              round(cf_excl, 4),
        "end_state_draw_active":          draw_active,
        "end_state_banked_step":          end_state_banked_step,
        "steps_draw_to_bank":             steps_draw_bank,
        "revised_expectation_count":      len(br_records),
    }

    statements, summary = [], {}
    if report:
        bundle = build_bundle_from_observers(
            provenance_obs=prov_obs,
            schema_obs=schema_obs,
            family_obs=family_obs,
            comparison_obs=comp_obs,
            prediction_error_obs=pe_obs,
            run_meta=meta,
            goal_obs=goal_obs,
            counterfactual_obs=cf_obs,
            belief_revision_obs=br_obs,
        )
        layer      = V16ReportingLayer(bundle)
        statements = layer.generate_report()
        summary    = _compute_summary(
            run_idx, seed, hazard_cost, statements,
            goal_obs, cf_obs, br_obs,
            draw_active, end_state_banked_step,
            cf_raw, cf_emitted, cf_excl, mean_delta, bias_eff,
        )

    return (run_row, statements, summary, prov_obs, goal_obs,
            cf_obs, br_obs, end_state_banked_step)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _compute_summary(run_idx, seed, hazard_cost, statements,
                     goal_obs, cf_obs, br_obs,
                     draw_active, end_state_banked_step,
                     cf_raw, cf_emitted, cf_excl,
                     mean_delta, bias_eff):
    stmts_q1 = [s for s in statements if s.query_type == "what_learned"]
    stmts_q2 = [s for s in statements if s.query_type == "how_related"]
    stmts_q3 = [s for s in statements if s.query_type == "where_surprised"]
    stmts_q4 = [s for s in statements if s.query_type == "where_held_back"]
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

    relevance_count = sum(1 for s in stmts_q1 if s.source_type == "goal")
    goal_stmt = next(
        (s for s in stmts_q3 if s.source_type == "goal"), None
    )

    cf_records = cf_obs.get_substrate() if cf_obs else []
    gr_count   = sum(1 for r in cf_records if r.get("goal_relevant"))
    br_records = br_obs.get_substrate() if br_obs else []

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
        "end_state_banked_step":          end_state_banked_step,
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
            temp = dp[j]
            dp[j] = prev if seq_a[i-1]==seq_b[j-1] else 1+min(prev,dp[j],dp[j-1])
            prev = temp
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
    args = parser.parse_args()

    report              = not args.no_report
    with_goal           = not args.no_goal
    with_counterfactual = not args.no_counterfactual
    with_br             = not args.no_belief_revision
    with_cs             = not args.no_completion_signal

    if not os.path.exists(SEED_CSV):
        print(f"ERROR: seed file not found: {SEED_CSV}")
        sys.exit(1)

    seeds = load_seeds(SEED_CSV)
    if not seeds:
        print(f"ERROR: no {BATCH_STEPS}-step seeds found.")
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

    print("v1.10 Batch — Belief Revision with Consequences "
          "and the Completion Signal")
    print(f"  Agent:              "
          f"{'V110Agent (with draw)' if with_cs else 'V17Agent'}")
    print(f"  Goal layer:         {'enabled' if with_goal else 'DISABLED'}")
    print(f"  Counterfactual:     "
          f"{'enabled (K_excl=500)' if with_counterfactual else 'DISABLED'}")
    print(f"  Belief revision:    {'enabled' if with_br else 'DISABLED'}")
    print(f"  Completion signal:  "
          f"{'enabled (draw=+0.20)' if with_cs else 'DISABLED'}")
    print(f"  Reporting:          {'enabled' if report else 'disabled'}")
    print(f"  Total runs:         {len(jobs)}")
    print()

    total_hallucinations = 0
    total_statements     = 0
    total_cf_emitted     = 0
    total_br_records     = 0
    end_state_banked_runs = 0
    incomplete_runs      = []

    q1_sequences_goal = {}
    q1_sequences_free = {}
    goal_rows         = []

    with (
        open(RUN_DATA_CSV,        "w", newline="") as rd_f,
        open(GOAL_CSV,            "w", newline="") as goal_f,
        open(COUNTERFACTUAL_CSV,  "w", newline="") as cf_f,
        open(BELIEF_REVISION_CSV, "w", newline="") as br_f,
        open(REPORT_CSV,          "w", newline="") as rep_f,
        open(REPORT_SUMMARY_CSV,  "w", newline="") as sum_f,
        open(END_STATE_DRAW_CSV,  "w", newline="") as es_f,
    ):
        rd_writer   = csv.DictWriter(rd_f,   fieldnames=RUN_DATA_FIELDS)
        goal_writer = csv.DictWriter(goal_f, fieldnames=GOAL_FIELDS)
        cf_writer   = csv.DictWriter(cf_f,   fieldnames=COUNTERFACTUAL_FIELDS)
        br_writer   = csv.DictWriter(br_f,   fieldnames=BELIEF_REVISION_FIELDS)
        rep_writer  = csv.DictWriter(rep_f,  fieldnames=REPORT_FIELDS)
        sum_writer  = csv.DictWriter(sum_f,  fieldnames=SUMMARY_FIELDS)
        es_writer   = csv.DictWriter(es_f,   fieldnames=END_STATE_DRAW_FIELDS)

        for w in [rd_writer, goal_writer, cf_writer, br_writer,
                  rep_writer, sum_writer, es_writer]:
            w.writeheader()

        for job_idx, (run_idx, seed, hazard_cost) in enumerate(jobs):
            is_first = (job_idx == 0)

            try:
                (run_row, statements, summary, prov_obs, goal_obs,
                 cf_obs, br_obs, es_banked_step) = run_one(
                    run_idx, seed, hazard_cost,
                    report=report,
                    with_goal=with_goal,
                    with_counterfactual=with_counterfactual,
                    with_belief_revision=with_br,
                    with_completion_signal=with_cs,
                )
            except Exception as e:
                import traceback as tb
                print(f"  Run {run_idx} cost={hazard_cost}: ERROR — {e}")
                tb.print_exc()
                incomplete_runs.append((run_idx, hazard_cost))
                continue

            rd_writer.writerow(
                {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
            )
            flush_provenance_csv(prov_obs, PROVENANCE_CSV,
                                 first_run=is_first)

            if with_goal and goal_obs is not None:
                goal_row = goal_obs.goal_row()
                goal_writer.writerow(
                    {k: goal_row.get(k, "") for k in GOAL_FIELDS}
                )
                goal_rows.append(goal_row)

            if with_counterfactual and cf_obs is not None:
                for cf_row in cf_obs.counterfactual_rows():
                    cf_writer.writerow(
                        {k: cf_row.get(k, "") for k in COUNTERFACTUAL_FIELDS}
                    )
                total_cf_emitted += len(cf_obs.get_substrate())

            if with_br and br_obs is not None:
                for br_row in br_obs.belief_revision_rows():
                    br_writer.writerow(
                        {k: br_row.get(k, "") for k in BELIEF_REVISION_FIELDS}
                    )
                total_br_records += len(br_obs.get_substrate())

            # End-state draw log
            act_step = run_row.get("activation_step")
            es_writer.writerow({
                "arch":                ARCH,
                "run_idx":             run_idx,
                "seed":                seed,
                "hazard_cost":         hazard_cost,
                "num_steps":           BATCH_STEPS,
                "activation_step":     act_step,
                "end_state_banked_step": es_banked_step,
                "steps_draw_to_bank":  run_row.get("steps_draw_to_bank"),
                "end_state_draw_active": run_row.get("end_state_draw_active"),
            })

            if es_banked_step is not None:
                end_state_banked_runs += 1

            if report:
                for stmt in statements:
                    rep_writer.writerow({
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
                sum_writer.writerow(
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
                        f"goal={'resolved' if gs['resolved'] else 'expired'}"
                        f" | "
                    )
                es_flag = (
                    f"es={'banked' if es_banked_step else 'pending'} | "
                )
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"stmts={summary['total_statements']:3d} | "
                    f"br={summary['revised_expectation_count']:2d} | "
                    f"cf={summary['suppressed_approach_count']:3d} | "
                    f"{goal_outcome}{es_flag}"
                    f"halluc={status}"
                )

            # Paired goal-free run
            if report and with_goal:
                try:
                    (_, stmts_free, _, _, _, _, _, _) = run_one(
                        run_idx, seed, hazard_cost,
                        report=True, with_goal=False,
                        with_counterfactual=False,
                        with_belief_revision=False,
                        with_completion_signal=False,
                    )
                    q1_sequences_free[run_idx] = [
                        s.source_key for s in stmts_free
                        if s.query_type == "what_learned"
                        and s.source_type == "provenance"
                    ]
                except Exception as e:
                    import traceback as tb
                    print(f"    [paired run {run_idx}: ERROR — {e}]")
                    tb.print_exc()

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
                  f"goal-directed is {direction} "
                  f"({'as pre-registered' if mean_g > mean_f else 'REVERSED'})")

    # -----------------------------------------------------------------------
    # Category θ: completion signal
    # -----------------------------------------------------------------------
    if with_cs:
        print()
        print("Category θ: completion signal effectiveness")
        rate = end_state_banked_runs / len(jobs) if jobs else 0
        c1_pass = rate >= 0.5
        print(f"  End state banked: {end_state_banked_runs}/{len(jobs)} "
              f"({rate:.0%})")
        print(f"  Component 1 (≥50%): {'PASS' if c1_pass else 'FAIL'}")
        print(f"  v1.9 baseline: 13/40 (32.5%)")
        if rate > 0.325:
            print(f"  Direction: above v1.9 baseline ✓")
        else:
            print(f"  Direction: at or below v1.9 baseline — report as finding")

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
