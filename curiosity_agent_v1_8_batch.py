"""
curiosity_agent_v1_8_batch.py
------------------------------
v1.8 batch runner.

Runs agent simulations in V17World with the full seven-observer cognitive
stack (six inherited from v1.7 plus the new goal layer). Writes the
standard six observer output CSVs, goal-layer output, and reporting
layer outputs.

NEW AT V1.8
  - V18GoalObserver: seventh parallel observer. Assigns a deterministic
    goal to each run; records goal_set, goal_progress, goal_resolved /
    goal_expired. Populated into SubstrateBundle.goal field.
  - V16ReportingLayer.query_what_learned() gains relevance markers on
    goal-relevant provenance records (source_type="goal").
  - V16ReportingLayer.query_where_surprised() gains a goal outcome
    statement as the final Q3 statement.
  - goal_v1_8.csv: per-run goal records.
  - Paired goal-free runs at matched seeds for Category γ comparison.

GOAL ASSIGNMENT SCHEDULE (deterministic, per pre-registration §2.5)
  run_idx % 3 == 0  =>  locate_family,            target="GREEN"
  run_idx % 3 == 1  =>  locate_family,            target="YELLOW"
  run_idx % 3 == 2  =>  bank_hazard_within_budget, target="haz_green"
  step_budget = int(BATCH_STEPS * 0.5) = 160,000 steps

ADDITIVE DISCIPLINE
  With goal observer disabled (--no-goal flag), output is byte-identical
  to v1.7 at matched seeds on all v1.7 metrics. Verified at Level-9
  re-run before Level-10.

PRE-FLIGHT
  Run Levels 1-9 before this batch, then Level 10.
  Level 9 re-run + Level 10: verify_v1_8_level10.py

Usage:
    python curiosity_agent_v1_8_batch.py [--no-report] [--no-goal]
"""

import argparse
import csv
import os
import sys
import statistics

import numpy as np

# Substrate patches must be imported before any observer is instantiated.
# v1_8_observer_substrates imports v1_7_observer_substrates internally.
import v1_8_observer_substrates  # noqa: F401
from v1_8_observer_substrates import build_bundle_from_observers

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_7_agent import V17Agent

from v1_1_provenance import V1ProvenanceStore
from v1_3_schema_extension import V13SchemaObserver
from v1_3_family_observer import V13FamilyObserver
from v1_4_comparison_observer import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver
from v1_6_reporting_layer import V16ReportingLayer
from v1_7_observer_substrates import flush_provenance_csv

from v1_8_goal_layer import V18GoalObserver, assign_goal, GOAL_FIELDS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_CSV             = "run_data_v1_7.csv"

RUN_DATA_CSV         = "run_data_v1_8.csv"
PROVENANCE_CSV       = "provenance_v1_8.csv"
SCHEMA_CSV           = "schema_v1_8.csv"
FAMILY_CSV           = "family_v1_8.csv"
COMPARISON_CSV       = "comparison_v1_8.csv"
PREDICTION_ERROR_CSV = "prediction_error_v1_8.csv"
GOAL_CSV             = "goal_v1_8.csv"
REPORT_CSV           = "report_v1_8.csv"
REPORT_SUMMARY_CSV   = "report_summary_v1_8.csv"

BATCH_STEPS   = 320000
HAZARD_COSTS  = [0.1, 1.0, 2.0, 10.0]
RUNS_PER_COST = 10

ARCH = "v1_8"

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
    # v1.8 goal summary fields
    "goal_type", "goal_target_id", "goal_step_budget",
    "goal_resolved", "goal_resolution_step", "goal_budget_remaining",
    "goal_expired", "goal_last_progress_step", "goal_resolution_window",
    "goal_progress_event_count",
]

REPORT_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "query_type", "statement_text",
    "source_type", "source_key", "source_resolves",
]

SUMMARY_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "total_statements", "statements_q1", "statements_q2", "statements_q3",
    "hallucination_count",
    "q1_formation_depth", "q3_surprise_cells", "q3_resolution_stated",
    "report_complete",
    # v1.8 goal summary fields
    "statements_with_relevance_markers",
    "goal_statement_present",
    "goal_resolution_stated",
]

# ---------------------------------------------------------------------------
# Seed loading
# ---------------------------------------------------------------------------

def load_seeds(path):
    """Load seeds from run_data_v1_7.csv at num_steps=320000."""
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

def run_one(run_idx, seed, hazard_cost, report=True, with_goal=True):
    """Execute one complete run.

    Returns (run_row, statements, summary, prov_obs, goal_obs).
    goal_obs is None when with_goal=False.
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

    prov_obs      = V1ProvenanceStore(agent, world, meta, ctc)
    schema_obs    = V13SchemaObserver(agent, world, meta)
    family_obs    = V13FamilyObserver(agent, world, meta, provenance_store=prov_obs)
    comp_obs      = V14ComparisonObserver(family_obs, meta)
    pe_obs        = V15PredictionErrorObserver(agent, world, meta)

    goal_obs = None
    if with_goal:
        goal_type, target_id, step_budget = assign_goal(run_idx, BATCH_STEPS)
        goal_obs = V18GoalObserver(
            agent, world, meta, goal_type, target_id, step_budget
        )

    observers = [prov_obs, schema_obs, family_obs, comp_obs, pe_obs]
    if goal_obs is not None:
        observers.append(goal_obs)

    # Run loop — identical to v1.7 (goal observer is purely additive)
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

    # Assemble run row
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
        )
        layer      = V16ReportingLayer(bundle)
        statements = layer.generate_report()
        summary    = _compute_summary(
            run_idx, seed, hazard_cost, statements, goal_obs
        )

    return run_row, statements, summary, prov_obs, goal_obs


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def _compute_summary(run_idx, seed, hazard_cost, statements, goal_obs=None):
    stmts_q1 = [s for s in statements if s.query_type == "what_learned"]
    stmts_q2 = [s for s in statements if s.query_type == "how_related"]
    stmts_q3 = [s for s in statements if s.query_type == "where_surprised"]
    hallucinations = sum(1 for s in statements if not s.source_resolves)

    # Q1 formation depth: distinct provenance source keys
    q1_prov_keys = {
        s.source_key for s in stmts_q1 if s.source_type == "provenance"
    }

    # Q3 surprise cells and resolution count
    q3_cells    = set()
    q3_resolved = 0
    for s in stmts_q3:
        if s.source_type == "prediction_error" and s.source_resolves:
            q3_cells.add(s.source_key)
            if "resolution window" in s.text.lower():
                q3_resolved += 1

    # v1.8 goal fields
    relevance_count = sum(
        1 for s in stmts_q1 if s.source_type == "goal"
    )
    goal_stmt = next(
        (s for s in stmts_q3 if s.source_type == "goal"),
        None
    )

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
        "hallucination_count": hallucinations,
        "q1_formation_depth":  len(q1_prov_keys),
        "q3_surprise_cells":   len(q3_cells),
        "q3_resolution_stated": q3_resolved,
        "report_complete": (
            len(stmts_q1) > 0
            and len(stmts_q2) > 0
            and len(stmts_q3) > 0
            and hallucinations == 0
        ),
        # v1.8 goal fields
        "statements_with_relevance_markers": relevance_count,
        "goal_statement_present":  goal_stmt is not None,
        "goal_resolution_stated":  (
            goal_stmt is not None
            and goal_stmt.source_key == "goal_resolved"
        ),
    }


# ---------------------------------------------------------------------------
# Edit distance for Category γ
# ---------------------------------------------------------------------------

def _edit_distance_normalised(seq_a, seq_b):
    if not seq_a and not seq_b:
        return 0.0
    n, m = len(seq_a), len(seq_b)
    dp = list(range(m + 1))
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
    """Compute pairwise normalised edit distances over a dict of sequences."""
    run_ids = sorted(sequences.keys())
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
        help="Disable goal observer (produces v1.7-equivalent output)"
    )
    args = parser.parse_args()
    report    = not args.no_report
    with_goal = not args.no_goal

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
                print(f"WARNING: no seed for cost={cost} run_idx={run_idx}; skipping.")
                continue
            jobs.append((run_idx, seed, cost))

    print(f"v1.8 Batch — Goal Assignment and Motivated Learning")
    print(f"  Substrate:     V17World (3D continuous-space, inherited)")
    print(f"  Agent:         V17Agent (inherited cognitive stack)")
    print(f"  Goal layer:    {'enabled' if with_goal else 'DISABLED'}")
    print(f"  Reporting:     {'enabled' if report else 'disabled'}")
    print(f"  Total runs:    {len(jobs)}")
    if with_goal:
        print(f"  Step budget:   {int(BATCH_STEPS * 0.5):,} steps "
              f"({BATCH_STEPS // 2} = 50% of {BATCH_STEPS:,})")
        print(f"  Paired goal-free runs: {len(jobs)} (for Category γ)")
    print()

    total_hallucinations = 0
    total_statements     = 0
    incomplete_runs      = []

    # Q1 sequences for Category γ
    q1_sequences_goal = {}   # goal-directed runs
    q1_sequences_free = {}   # matched goal-free runs

    # Goal rows for Category ζ
    goal_rows = []

    # Track first job for CSV header logic
    first_job = jobs[0] if jobs else None

    with (
        open(RUN_DATA_CSV,         "w", newline="") as rd_f,
        open(GOAL_CSV,             "w", newline="") as goal_f,
        open(REPORT_CSV,           "w", newline="") as rep_f,
        open(REPORT_SUMMARY_CSV,   "w", newline="") as sum_f,
    ):
        rd_writer   = csv.DictWriter(rd_f,   fieldnames=RUN_DATA_FIELDS)
        goal_writer = csv.DictWriter(goal_f, fieldnames=GOAL_FIELDS)
        rep_writer  = csv.DictWriter(rep_f,  fieldnames=REPORT_FIELDS)
        sum_writer  = csv.DictWriter(sum_f,  fieldnames=SUMMARY_FIELDS)

        rd_writer.writeheader()
        goal_writer.writeheader()
        rep_writer.writeheader()
        sum_writer.writeheader()

        for job_idx, (run_idx, seed, hazard_cost) in enumerate(jobs):
            is_first = (job_idx == 0)

            # --- Goal-directed run ---
            try:
                run_row, statements, summary, prov_obs, goal_obs = run_one(
                    run_idx, seed, hazard_cost,
                    report=report, with_goal=with_goal
                )
            except Exception as e:
                import traceback as tb
                print(f"  Run {run_idx} cost={hazard_cost}: ERROR — {e}")
                tb.print_exc()
                incomplete_runs.append((run_idx, hazard_cost))
                continue

            # Write run data
            rd_writer.writerow(
                {k: run_row.get(k, "") for k in RUN_DATA_FIELDS}
            )

            # Write provenance (Amendment 1 fix, inherited from v1.7)
            flush_provenance_csv(
                prov_obs, PROVENANCE_CSV, first_run=is_first
            )

            # Write goal row
            if with_goal and goal_obs is not None:
                goal_row = goal_obs.goal_row()
                goal_writer.writerow(
                    {k: goal_row.get(k, "") for k in GOAL_FIELDS}
                )
                goal_rows.append(goal_row)

            # Write report
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
                sum_writer.writerow(summary)

                run_halluc        = summary["hallucination_count"]
                total_hallucinations += run_halluc
                total_statements     += summary["total_statements"]
                if not summary["report_complete"]:
                    incomplete_runs.append((run_idx, hazard_cost))

                # Q1 sequence for Category γ (goal-directed)
                q1_keys_goal = [
                    s.source_key for s in statements
                    if s.query_type == "what_learned"
                    and s.source_type in ("provenance", "goal")
                ]
                q1_sequences_goal[run_idx] = q1_keys_goal

                status = "PASS" if run_halluc == 0 else f"FAIL({run_halluc})"
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
                    f"{goal_outcome}"
                    f"halluc={status}"
                )
            else:
                print(
                    f"  Run {run_idx:3d} | seed={seed:12d} | "
                    f"cost={hazard_cost:5.1f} | "
                    f"mastery={run_row.get('time_to_final_mastery', 'None')}"
                )

            # --- Paired goal-free run (for Category γ comparison) ---
            if report and with_goal:
                try:
                    _, stmts_free, _, _, _ = run_one(
                        run_idx, seed, hazard_cost,
                        report=True, with_goal=False
                    )
                    q1_keys_free = [
                        s.source_key for s in stmts_free
                        if s.query_type == "what_learned"
                        and s.source_type == "provenance"
                    ]
                    q1_sequences_free[run_idx] = q1_keys_free
                except Exception as e:
                    import traceback as tb
                    print(f"    [paired goal-free run {run_idx}: ERROR — {e}]")
                    tb.print_exc()

    # ---------------------------------------------------------------------------
    # Category γ: biographical individuation
    # ---------------------------------------------------------------------------
    if report and len(q1_sequences_goal) >= 2:
        print()
        print("Category γ: biographical individuation")

        # Component 1: goal-directed individuation floor
        goal_distances = _pairwise_distances(q1_sequences_goal)
        min_g  = min(goal_distances)
        max_g  = max(goal_distances)
        mean_g = sum(goal_distances) / len(goal_distances)
        floor  = 0.05
        c1_pass = min_g >= floor

        print(f"  Goal-directed Q1 distances: n={len(goal_distances)}")
        print(f"  min={min_g:.4f}  mean={mean_g:.4f}  max={max_g:.4f}")
        print(f"  Component 1 (min >= {floor}): {'PASS' if c1_pass else 'FAIL'}")

        # Component 2: goal-directed vs goal-free mean comparison
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

        print(f"  Category γ: {'PASS' if c1_pass else 'FAIL'}")

    # ---------------------------------------------------------------------------
    # Category ζ: goal-resolution window distribution
    # ---------------------------------------------------------------------------
    if with_goal and goal_rows:
        print()
        print("Category ζ: goal-resolution window distribution")

        expired_rows = [
            r for r in goal_rows
            if r.get("goal_expired") is True
            or str(r.get("goal_expired")).lower() == "true"
        ]
        windows = [
            r["goal_resolution_window"] for r in expired_rows
            if r.get("goal_resolution_window") is not None
        ]

        print(f"  Expired runs: {len(expired_rows)} / {len(goal_rows)}")
        print(f"  Expired with progress (window defined): {len(windows)}")

        if len(windows) >= 2:
            mean_rw = statistics.mean(windows)
            std_rw  = statistics.stdev(windows)
            min_rw  = min(windows)
            max_rw  = max(windows)
            c1_pass = std_rw > 0
            print(f"  Window stats: min={min_rw}  mean={mean_rw:.1f}  "
                  f"max={max_rw}  std={std_rw:.1f}")
            print(f"  Component 1 (std > 0): {'PASS' if c1_pass else 'FAIL'}")

            # Component 2: cost-sensitivity (exploratory)
            print("  Component 2 (cost-sensitivity, exploratory):")
            by_cost = {}
            for r in expired_rows:
                if r.get("goal_resolution_window") is not None:
                    c = float(r.get("hazard_cost", 0))
                    by_cost.setdefault(c, []).append(r["goal_resolution_window"])
            for c in sorted(by_cost):
                ws = by_cost[c]
                m  = statistics.mean(ws)
                print(f"    cost={c}: n={len(ws)}, mean_window={m:.1f}")
        elif len(windows) == 1:
            print(f"  Window = {windows[0]} steps (single run; variance not computable)")
            print("  Component 1: INDETERMINATE (only one expired run with progress)")
        else:
            print("  No expired runs with progress — Category ζ Component 1: INDETERMINATE")

    # ---------------------------------------------------------------------------
    # Batch summary
    # ---------------------------------------------------------------------------
    print()
    print("=" * 65)
    print("Batch complete.")
    print(f"  Runs processed: {len(jobs) - len(incomplete_runs)} / {len(jobs)}")

    if report:
        print(f"  Total statements:     {total_statements}")
        print(f"  Total hallucinations: {total_hallucinations}")
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
