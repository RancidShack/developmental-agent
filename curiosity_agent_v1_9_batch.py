"""
curiosity_agent_v1_9_batch.py
------------------------------
v1.9 batch runner.

Runs agent simulations in V17World with the full eight-observer
cognitive stack (seven inherited from v1.8 plus the new counterfactual
layer). Writes all v1.8 output CSVs, the new counterfactual CSV, and
updated reporting layer outputs including Q4 statements.

NEW AT V1.9
  - V19CounterfactualObserver: eighth parallel observer. Detects
    suppressed-approach events (approach-then-recession without contact)
    for HAZARD objects and goal-relevant DIST_OBJ targets.
  - Q4 (where_held_back): new query type in the biographical register.
    One statement per confirmed suppressed-approach event.
  - counterfactual_v1_9.csv: per-event suppressed-approach records.
  - report_summary_v1_9.csv gains Q4 count fields.

INHERITED UNCHANGED FROM V1.8
  - V18GoalObserver, goal assignment schedule (run_idx % 3),
    budget fraction 0.5, paired goal-free runs for Category γ.
  - All v1.7 and v1.8 substrate patches.
  - Seeds drawn from run_data_v1_8.csv.

ADDITIVE DISCIPLINE
  With --no-counterfactual, output is byte-identical to v1.8.2 at
  matched seeds on all v1.8 metrics. Verified at Level 11 C7 before
  full batch.

PRE-FLIGHT
  Run Level 10 re-run then Level 11: verify_v1_9_level11.py

Usage:
    python curiosity_agent_v1_9_batch.py [--no-report]
                                          [--no-goal]
                                          [--no-counterfactual]
"""

import argparse
import csv
import os
import sys
import statistics

import numpy as np

# Substrate patches: v1.9 imports v1.8, which imports v1.7.
import v1_9_observer_substrates  # noqa: F401
from v1_9_observer_substrates import build_bundle_from_observers

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_7_agent import V17Agent

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

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_CSV             = "run_data_v1_8.csv"

RUN_DATA_CSV         = "run_data_v1_9.csv"
PROVENANCE_CSV       = "provenance_v1_9.csv"
GOAL_CSV             = "goal_v1_9.csv"
COUNTERFACTUAL_CSV   = "counterfactual_v1_9.csv"
REPORT_CSV           = "report_v1_9.csv"
REPORT_SUMMARY_CSV   = "report_summary_v1_9.csv"

BATCH_STEPS   = 320_000
HAZARD_COSTS  = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST = 10

ARCH = "v1_9"

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
    "transition_order_sequence",
    "knowledge_banked_sequence",
    # v1.5 prediction-error summary fields (inherited)
    "yellow_pre_transition_entries",
    "green_pre_transition_entries",
    "unaffiliated_pre_transition_entries",
    "yellow_resolution_window",
    "green_resolution_window",
    "total_prediction_error_events",
    "prediction_error_complete",
    # v1.8 goal summary fields (inherited)
    "goal_type", "goal_target_id", "goal_step_budget",
    "goal_resolved", "goal_resolution_step", "goal_budget_remaining",
    "goal_expired", "goal_last_progress_step", "goal_resolution_window",
    "goal_progress_event_count",
    # v1.9 counterfactual summary fields
    "suppressed_approach_count",
    "goal_relevant_suppressed_count",
    "suppressed_approach_objects",
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
    # v1.8 goal fields (inherited)
    "statements_with_relevance_markers",
    "goal_statement_present",
    "goal_resolution_stated",
    # v1.9 counterfactual fields
    "q4_statement_count",
    "suppressed_approach_count",
    "goal_relevant_suppressed_count",
]

# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

def load_seeds(path):
    """Load seeds from run_data_v1_8.csv at num_steps=320000."""
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
            with_goal=True, with_counterfactual=True):
    """Execute one complete run.

    Returns (run_row, statements, summary, prov_obs, goal_obs, cf_obs).
    goal_obs and cf_obs are None when their respective flags are False.
    """
    np.random.seed(seed)

    world = V17World(hazard_cost=hazard_cost, seed=seed)
    agent = V17Agent(world, total_steps=BATCH_STEPS, num_actions=NUM_ACTIONS)

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

    observers = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs]
    if goal_obs is not None:
        observers.append(goal_obs)
    if cf_obs is not None:
        observers.append(cf_obs)

    # Run loop — identical to v1.8 (counterfactual observer is additive)
    state = world.observe()
    for step in range(BATCH_STEPS):
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
        agent.update_values(state, action, obs_next, intrinsic)
        agent.update_model(state, action, obs_next)

        state = obs_next

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

    cf_summary_fields = {}
    if cf_obs is not None:
        cf_records = cf_obs.get_substrate()
        gr_count   = sum(1 for r in cf_records if r.get("goal_relevant"))
        obj_list   = ",".join(
            sorted({r["object_id"] for r in cf_records})
        )
        cf_summary_fields = {
            "suppressed_approach_count":      len(cf_records),
            "goal_relevant_suppressed_count": gr_count,
            "suppressed_approach_objects":    obj_list,
        }

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
        "activation_step":           agent.activation_step,
        "end_state_found_step":      agent.end_state_found_step,
        "end_state_banked":          agent.end_state_banked,
        "time_to_first_transition":  agent.time_to_first_transition,
        "time_to_final_transition":  agent.time_to_final_transition,
        "transition_order_sequence": str(agent.transition_order_sequence),
        "knowledge_banked_sequence": str(agent.knowledge_banked_sequence),
        **pe_summary,
        **goal_summary_fields,
        **cf_summary_fields,
    }

    # Build SubstrateBundle and reporting layer
    statements = []
    summary    = {}
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
        )
        layer      = V16ReportingLayer(bundle)
        statements = layer.generate_report()
        summary    = _compute_summary(
            run_idx, seed, hazard_cost, statements, goal_obs, cf_obs
        )

    return run_row, statements, summary, prov_obs, goal_obs, cf_obs


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def _compute_summary(run_idx, seed, hazard_cost, statements,
                     goal_obs=None, cf_obs=None):
    stmts_q1 = [s for s in statements if s.query_type == "what_learned"]
    stmts_q2 = [s for s in statements if s.query_type == "how_related"]
    stmts_q3 = [s for s in statements if s.query_type == "where_surprised"]
    stmts_q4 = [s for s in statements if s.query_type == "where_held_back"]
    hallucinations = sum(1 for s in statements if not s.source_resolves)

    q1_prov_keys = {
        s.source_key for s in stmts_q1 if s.source_type == "provenance"
    }

    q3_cells    = set()
    q3_resolved = 0
    for s in stmts_q3:
        if s.source_type == "prediction_error" and s.source_resolves:
            q3_cells.add(s.source_key)
            if "resolution window" in s.text.lower():
                q3_resolved += 1

    # v1.8 goal fields (inherited)
    relevance_count = sum(1 for s in stmts_q1 if s.source_type == "goal")
    goal_stmt       = next(
        (s for s in stmts_q3 if s.source_type == "goal"), None
    )

    # v1.9 counterfactual fields
    cf_records  = cf_obs.get_substrate() if cf_obs is not None else []
    gr_count    = sum(1 for r in cf_records if r.get("goal_relevant"))

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
        "hallucination_count": hallucinations,
        "q1_formation_depth":  len(q1_prov_keys),
        "q3_surprise_cells":   len(q3_cells),
        "q3_resolution_stated": q3_resolved,
        "report_complete": (
            len(stmts_q1) > 0
            and len(stmts_q2) > 0
            and len(stmts_q3) > 0
            and hallucinations == 0
            # Q4 may be empty — that is valid per pre-reg §6.2
        ),
        # v1.8 goal fields
        "statements_with_relevance_markers": relevance_count,
        "goal_statement_present":  goal_stmt is not None,
        "goal_resolution_stated":  (
            goal_stmt is not None
            and goal_stmt.source_key == "goal_resolved"
        ),
        # v1.9 counterfactual fields
        "q4_statement_count":             len(stmts_q4),
        "suppressed_approach_count":      len(cf_records),
        "goal_relevant_suppressed_count": gr_count,
    }


# ---------------------------------------------------------------------------
# Edit distance for Category γ (inherited from v1.8)
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
            if seq_a[i - 1] == seq_b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[m] / max(n, m)


def _pairwise_distances(sequences):
    run_ids   = sorted(sequences.keys())
    distances = []
    for i in range(len(run_ids)):
        for j in range(i + 1, len(run_ids)):
            d = _edit_distance_normalised(
                sequences[run_ids[i]], sequences[run_ids[j]]
            )
            distances.append(d)
    return distances


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-report", action="store_true",
        help="Skip reporting layer (run simulations only)"
    )
    parser.add_argument(
        "--no-goal", action="store_true",
        help="Disable goal observer"
    )
    parser.add_argument(
        "--no-counterfactual", action="store_true",
        help="Disable counterfactual observer (produces v1.8-equivalent output)"
    )
    args = parser.parse_args()
    report              = not args.no_report
    with_goal           = not args.no_goal
    with_counterfactual = not args.no_counterfactual

    if not os.path.exists(SEED_CSV):
        print(f"ERROR: seed file not found: {SEED_CSV}")
        sys.exit(1)

    seeds = load_seeds(SEED_CSV)
    if not seeds:
        print(f"ERROR: no {BATCH_STEPS}-step seeds found in {SEED_CSV}.")
        sys.exit(1)

    # Build job list
    jobs = []
    for cost in HAZARD_COSTS:
        for run_idx in range(RUNS_PER_COST):
            seed = seeds.get((cost, run_idx))
            if seed is None:
                print(f"WARNING: no seed for cost={cost} "
                      f"run_idx={run_idx}; skipping.")
                continue
            jobs.append((run_idx, seed, cost))

    print("v1.9 Batch — Counterfactual Record and Suppressed Approach")
    print(f"  Substrate:            V17World (3D continuous-space, inherited)")
    print(f"  Agent:                V17Agent (inherited cognitive stack)")
    print(f"  Goal layer:           {'enabled' if with_goal else 'DISABLED'}")
    print(f"  Counterfactual layer: "
          f"{'enabled' if with_counterfactual else 'DISABLED'}")
    print(f"  Reporting:            {'enabled' if report else 'disabled'}")
    print(f"  Total runs:           {len(jobs)}")
    if with_goal:
        print(f"  Step budget:          "
              f"{int(BATCH_STEPS * 0.5):,} steps (50% of {BATCH_STEPS:,})")
    if with_counterfactual:
        print(f"  Detection thresholds: "
              f"N_approach=10, N_recession=5 (pre-registered)")
    print()

    total_hallucinations     = 0
    total_statements         = 0
    total_cf_records         = 0
    incomplete_runs          = []

    q1_sequences_goal = {}
    q1_sequences_free = {}
    q4_sequences_goal = {}   # for Category γ Q4 individuation

    goal_rows = []
    cf_rows   = []   # all per-event counterfactual records

    with (
        open(RUN_DATA_CSV,       "w", newline="") as rd_f,
        open(GOAL_CSV,           "w", newline="") as goal_f,
        open(COUNTERFACTUAL_CSV, "w", newline="") as cf_f,
        open(REPORT_CSV,         "w", newline="") as rep_f,
        open(REPORT_SUMMARY_CSV, "w", newline="") as sum_f,
    ):
        rd_writer   = csv.DictWriter(rd_f,   fieldnames=RUN_DATA_FIELDS)
        goal_writer = csv.DictWriter(goal_f, fieldnames=GOAL_FIELDS)
        cf_writer   = csv.DictWriter(cf_f,   fieldnames=COUNTERFACTUAL_FIELDS)
        rep_writer  = csv.DictWriter(rep_f,  fieldnames=REPORT_FIELDS)
        sum_writer  = csv.DictWriter(sum_f,  fieldnames=SUMMARY_FIELDS)

        rd_writer.writeheader()
        goal_writer.writeheader()
        cf_writer.writeheader()
        rep_writer.writeheader()
        sum_writer.writeheader()

        for job_idx, (run_idx, seed, hazard_cost) in enumerate(jobs):
            is_first = (job_idx == 0)

            try:
                (run_row, statements, summary,
                 prov_obs, goal_obs, cf_obs) = run_one(
                    run_idx, seed, hazard_cost,
                    report=report,
                    with_goal=with_goal,
                    with_counterfactual=with_counterfactual,
                )
            except Exception as e:
                import traceback as tb
                print(f"  Run {run_idx} cost={hazard_cost}: ERROR — {e}")
                tb.print_exc()
                incomplete_runs.append((run_idx, hazard_cost))
                continue

            # --- Write run data ---
            rd_writer.writerow(
                {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
            )

            # --- Write provenance ---
            flush_provenance_csv(prov_obs, PROVENANCE_CSV,
                                 first_run=is_first)

            # --- Write goal row ---
            if with_goal and goal_obs is not None:
                goal_row = goal_obs.goal_row()
                goal_writer.writerow(
                    {k: goal_row.get(k, "") for k in GOAL_FIELDS}
                )
                goal_rows.append(goal_row)

            # --- Write counterfactual rows ---
            if with_counterfactual and cf_obs is not None:
                for cf_row in cf_obs.counterfactual_rows():
                    cf_writer.writerow(
                        {k: cf_row.get(k, "") for k in COUNTERFACTUAL_FIELDS}
                    )
                    cf_rows.append(cf_row)
                total_cf_records += len(cf_obs.get_substrate())

            # --- Write report ---
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

                # Q1 sequences for Category γ
                q1_keys_goal = [
                    s.source_key for s in statements
                    if s.query_type == "what_learned"
                    and s.source_type in ("provenance", "goal")
                ]
                q1_sequences_goal[run_idx] = q1_keys_goal

                # Q4 sequences for Category γ Component 2
                q4_keys = [
                    s.source_key for s in statements
                    if s.query_type == "where_held_back"
                ]
                q4_sequences_goal[run_idx] = q4_keys

                status = "PASS" if run_halluc == 0 else f"FAIL({run_halluc})"
                cf_count = (
                    len(cf_obs.get_substrate())
                    if with_counterfactual and cf_obs is not None else 0
                )
                goal_outcome = ""
                if with_goal and goal_obs is not None:
                    gs = goal_obs.get_substrate()["goal_summary"]
                    goal_outcome = (
                        f"goal={'resolved' if gs['resolved'] else 'expired'} | "
                    )
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"stmts={summary['total_statements']:3d} | "
                    f"q4={summary['statements_q4']:2d} | "
                    f"cf={cf_count:2d} | "
                    f"{goal_outcome}"
                    f"halluc={status}"
                )
            else:
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"mastery={run_row.get('time_to_final_mastery', 'None')}"
                )

            # --- Paired goal-free run (Category γ Q1 comparison) ---
            if report and with_goal:
                try:
                    (_, stmts_free, _, _, _, _) = run_one(
                        run_idx, seed, hazard_cost,
                        report=True, with_goal=False,
                        with_counterfactual=False,
                    )
                    q1_keys_free = [
                        s.source_key for s in stmts_free
                        if s.query_type == "what_learned"
                        and s.source_type == "provenance"
                    ]
                    q1_sequences_free[run_idx] = q1_keys_free
                except Exception as e:
                    import traceback as tb
                    print(f"    [paired goal-free run {run_idx}: "
                          f"ERROR — {e}]")
                    tb.print_exc()

    # -----------------------------------------------------------------------
    # Category γ: biographical individuation
    # -----------------------------------------------------------------------
    if report and len(q1_sequences_goal) >= 2:
        print()
        print("Category γ: biographical individuation")

        goal_distances = _pairwise_distances(q1_sequences_goal)
        min_g  = min(goal_distances)
        max_g  = max(goal_distances)
        mean_g = sum(goal_distances) / len(goal_distances)
        floor  = 0.05
        c1_pass = min_g >= floor

        print(f"  Goal-directed Q1 distances: n={len(goal_distances)}")
        print(f"  min={min_g:.4f}  mean={mean_g:.4f}  max={max_g:.4f}")
        print(f"  Component 1 (min >= {floor}): "
              f"{'PASS' if c1_pass else 'FAIL'}")

        if len(q1_sequences_free) >= 2:
            free_distances = _pairwise_distances(q1_sequences_free)
            mean_f = sum(free_distances) / len(free_distances)
            print(f"  Goal-free Q1 distances:    n={len(free_distances)}")
            print(f"  mean={mean_f:.4f}")
            direction = "higher" if mean_g > mean_f else "lower"
            print(
                f"  Component 2: goal-directed mean ({mean_g:.4f}) is "
                f"{direction} than goal-free mean ({mean_f:.4f}) — "
                f"{'as pre-registered' if mean_g > mean_f else 'REVERSED (report as finding)'}"
            )

        # Q4 individuation (Component 2 of Category γ per pre-reg §6.3)
        q4_nonempty = {
            k: v for k, v in q4_sequences_goal.items() if v
        }
        if len(q4_nonempty) >= 2:
            q4_distances = _pairwise_distances(q4_nonempty)
            std_q4 = statistics.stdev(q4_distances) if len(q4_distances) >= 2 else 0.0
            mean_q4 = sum(q4_distances) / len(q4_distances)
            c2_pass = std_q4 > 0.05
            print()
            print(f"  Q4 individuation (runs with Q4): n={len(q4_nonempty)}")
            print(f"  mean={mean_q4:.4f}  std={std_q4:.4f}")
            print(f"  Component 2 (std > 0.05): "
                  f"{'PASS' if c2_pass else 'FAIL'}")
        else:
            print(f"  Q4 individuation: only {len(q4_nonempty)} run(s) "
                  f"with non-empty Q4 — Component 2 INDETERMINATE")

        print(f"  Category γ: {'PASS' if c1_pass else 'FAIL'}")

    # -----------------------------------------------------------------------
    # Category η: three-way contact register
    # -----------------------------------------------------------------------
    if report and with_counterfactual:
        print()
        print("Category η: three-way contact register")
        print("  (clean contact | suppressed approach | "
              "prediction-error contact)")

        # Group by cost condition
        runs_by_cost: dict = {}
        for job in jobs:
            c = job[2]
            runs_by_cost.setdefault(c, []).append(job[0])

        for cost in sorted(runs_by_cost.keys()):
            cf_for_cost = [
                r for r in cf_rows
                if abs(float(r.get("hazard_cost", 0)) - cost) < 1e-6
            ]
            n_suppressed = len(cf_for_cost)
            print(f"  cost={cost:5.1f}: "
                  f"suppressed_approach_records={n_suppressed}")

        # Overall
        has_suppressed = total_cf_records > 0
        rate = (
            sum(1 for r in (
                [summary.get("suppressed_approach_count", 0)
                 for summary in []]   # populated below if needed
            ) if r > 0)
        )
        print(f"  Total suppressed-approach records: {total_cf_records}")

        # Detection rate across runs
        runs_with_cf = sum(
            1 for row in cf_rows
            # count distinct run_idx values
        )
        run_idxs_with_cf = len({r.get("run_idx") for r in cf_rows})
        print(f"  Runs with ≥1 suppressed approach: "
              f"{run_idxs_with_cf} / {len(jobs)}")
        c1_rate = run_idxs_with_cf / len(jobs) if jobs else 0
        c1_pass = c1_rate >= 0.5
        print(f"  Component 1 (≥50% runs): "
              f"{'PASS' if c1_pass else 'FAIL — report as Category η finding'}"
              f" ({c1_rate:.0%})")

    # -----------------------------------------------------------------------
    # Batch summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 65)
    print("Batch complete.")
    print(f"  Runs processed: "
          f"{len(jobs) - len(incomplete_runs)} / {len(jobs)}")

    if report:
        print(f"  Total statements:          {total_statements}")
        print(f"  Total hallucinations:      {total_hallucinations}")
        print(f"  Total CF records:          {total_cf_records}")
        alpha_pass = total_hallucinations == 0
        beta_pass  = not incomplete_runs
        print(f"  Category α: {'PASS' if alpha_pass else 'FAIL'}")
        print(f"  Category β: {'PASS' if beta_pass else 'FAIL'}")

    if with_goal and goal_rows:
        n_resolved = sum(
            1 for r in goal_rows
            if r.get("goal_resolved") is True
            or str(r.get("goal_resolved")).lower() == "true"
        )
        n_expired = len(goal_rows) - n_resolved
        print(f"  Goal resolved: {n_resolved} / {len(goal_rows)}")
        print(f"  Goal expired:  {n_expired} / {len(goal_rows)}")

    if incomplete_runs:
        print(f"  Incomplete runs: {incomplete_runs}")


if __name__ == "__main__":
    main()
