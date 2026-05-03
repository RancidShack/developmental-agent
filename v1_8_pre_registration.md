# v1.8 Pre-Registration: Goal Assignment and Motivated Learning

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 3 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.8 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

Seven iterations have built a developmental agent that encounters objects, forms relationships with them, survives costs, builds knowledge, traverses family structures, compares those structures across families, detects its own prediction errors, and generates an auditable biographical account of all of it. The account is traceable — every statement resolves to a substrate record. The account is individually variable — 40 distinct developmental arcs produce 40 distinct autobiographies, minimum pairwise edit distance 0.366 in V17World. The account is substrate-agnostic at the reporting layer — V16ReportingLayer required zero modifications to carry forward from the tabular grid to a bounded 3D continuous-space environment.

What the account does not contain is motivation.

The agent learns, in the sense that it acquires knowledge. But it does not want anything. It does not succeed at a task and know it has succeeded. It does not fail at a task and know it has failed. Its Q3 statements describe prediction errors — *I encountered haz_yellow at step 493, before the precondition was met; the resolution window was 7,336 steps* — but these are records of what happened, not records of what the agent was trying to achieve. The agent has a sophisticated developmental archive. It does not yet have an archive of attempted goals.

v1.8 introduces that archive. A goal layer — the eighth cognitive component — assigns the agent an explicit objective, tracks progress, and records resolution or expiry. The goal layer is additive: a seventh observer in the parallel stack. It does not modify the agent, world, or any existing observer. The biographical register gains motivational context at Q1 and a failure register at Q3 — the first time the agent's report describes not just what surprised it, but what it was trying to do and whether it succeeded.

This is SICC Commitment 5 (goal-directedness as a precondition for genuine learning) advanced at the first layer. The agent does not yet choose its goals, revise them, or understand why it failed. Those capabilities are the arc from v1.9 to v1.11. v1.8 establishes the substrate on which that arc will build: a record that distinguishes incompletion from failure, and that holds the gap between last progress and budget expiry as an architectural object.

---

## 2. Architectural specification

### 2.1 The goal layer

The goal layer is implemented as a seventh parallel observer. It holds a goal specification — a structured record comprising target type, success criterion, and step budget — and tracks progress against that target across the run. It fires four record types.

**Goal specification fields:**
- `goal_type` — one of `locate_family`, `achieve_end_state`, `bank_hazard_within_budget`
- `target_id` — the object_id or family colour targeted (e.g. `"GREEN"`, `"end_state_0"`, `"haz_yellow"`)
- `step_budget` — the maximum number of steps within which the goal must be resolved
- `set_at_step` — always 0 (goal is assigned at the start of the run)

**Goal record types:**

`goal_set` — emitted at step 0. Records goal_type, target_id, step_budget, set_at_step. One record per run.

`goal_progress` — emitted when the agent comes within measurable distance of the target. Definition by goal_type:
- `locate_family`: emitted when the agent's first distal-tier object of the target family is perceived (distance below perception radius). Progress field: `progress_type = "first_perception"`, `progress_step = step`.
- `achieve_end_state`: emitted when all family traversal sequences are complete and the end-state is activated. Progress field: `progress_type = "end_state_activated"`, `progress_step = step`.
- `bank_hazard_within_budget`: emitted when the target hazard object is first perceived. Progress field: `progress_type = "hazard_first_perceived"`, `progress_step = step`.

Multiple `goal_progress` records are possible per run where the goal type permits partial milestones. At most one `goal_resolved` record is possible per run.

`goal_resolved` — emitted if and only if the success criterion is met within the step budget. Success criteria:
- `locate_family`: the agent has contacted all three objects in the target family (distal, acquirable, and costly tier) before step budget expires.
- `achieve_end_state`: end-state activation recorded before step budget expires.
- `bank_hazard_within_budget`: the target hazard object has been transformed to KNOWLEDGE state before step budget expires.

Fields: `resolved_at_step`, `steps_used`, `budget_remaining`.

`goal_expired` — emitted if and only if the step budget is reached without a `goal_resolved` record. Fields: `expired_at_step` (= step_budget), `last_progress_step` (the step of the most recent `goal_progress` record, or None if no progress was made), `goal_resolution_window` (the gap between last_progress_step and expired_at_step if last_progress_step is not None; None otherwise). The `goal_resolution_window` is the direct structural parallel to the prediction-error resolution window: the developmental distance between the closest approach to success and the moment the budget expired.

Exactly one of `goal_resolved` or `goal_expired` is emitted per run. Both cannot be emitted.

### 2.2 The SubstrateBundle extension

`SubstrateBundle` gains a `goal` field. The field is `None` if the goal observer was not active, or a dict with the following structure when active:

```
goal:
  {
    "goal_set":      dict of goal_set record fields,
    "goal_progress": list of goal_progress record dicts (may be empty),
    "goal_resolved": dict of goal_resolved record fields, or None,
    "goal_expired":  dict of goal_expired record fields, or None,
    "goal_summary":  {
        "goal_type":         str,
        "target_id":         str,
        "step_budget":       int,
        "resolved":          bool,
        "resolution_step":   int or None,
        "expired":           bool,
        "last_progress_step": int or None,
        "goal_resolution_window": int or None,
    }
  }
```

`bundle.resolve("goal", source_key)` returns True if `source_key` is one of `"goal_set"`, `"goal_progress"`, `"goal_resolved"`, `"goal_expired"`, `"goal_summary"` and the corresponding field is non-None (or non-empty list for `goal_progress`).

The `build_bundle_from_observers()` function gains a `goal_obs` parameter (default None). When supplied, it calls `goal_obs.get_substrate()` and places the result in the bundle's `goal` field. The existing six parameters are unchanged; backward compatibility is preserved.

### 2.3 The reporting layer extension: Q1 motivational context

`V16ReportingLayer` is extended to read from the `goal` substrate field where present. Two changes are made to existing query types. No new query type is introduced at v1.8 (that addition is reserved for v1.9 when the counterfactual record becomes available).

**Q1 (what_learned) extension.** Where a `goal_set` record is present in the goal substrate, each Q1 statement that describes a provenance event relevant to the goal target gains a relevance marker appended to its text. The relevance criterion:
- For `locate_family` goals: any mastery or knowledge_banking event whose flag_id refers to an object in the target family (identified by object_id prefix, e.g. `"att_green"` or `"haz_green"` for a GREEN family goal) is marked relevant.
- For `bank_hazard_within_budget` goals: the knowledge_banking event for the specific target_id is marked relevant.
- For `achieve_end_state` goals: the end_state_activation event is marked relevant.

The relevance marker text: *(relevant to active goal: {goal_type} — {target_id})*

Statements for events not relevant to the active goal are unchanged in text.

Relevance markers are sourced from the `goal` substrate field. The source_type for statements containing a relevance marker is `"goal"`; the source_key is `"goal_set"`. This is a new source_type added at v1.8. `bundle.resolve("goal", "goal_set")` must return True for these statements to pass Category α.

**Q3 (where_surprised) extension.** Where a `goal_expired` record is present in the goal substrate, a final Q3 statement is appended after all prediction-error statements. The statement text:

> *My goal (goal_type: {goal_type}, target: {target_id}) expired at step {expired_at_step} without resolution. My closest approach was at step {last_progress_step}, leaving a goal-resolution window of {goal_resolution_window} steps.* [if last_progress_step is not None]

or:

> *My goal (goal_type: {goal_type}, target: {target_id}) expired at step {expired_at_step} without resolution. No progress was recorded.* [if last_progress_step is None]

The source_type for this statement is `"goal"`; the source_key is `"goal_expired"`. `bundle.resolve("goal", "goal_expired")` must return True.

Where a `goal_resolved` record is present, a final Q3 statement is appended:

> *My goal (goal_type: {goal_type}, target: {target_id}) resolved at step {resolved_at_step}, with {budget_remaining} steps remaining in the budget.*

Source_type `"goal"`, source_key `"goal_resolved"`.

### 2.4 What v1.8 does not change

All seven existing observers — `V1ProvenanceStore`, `V13SchemaObserver`, `V13FamilyObserver`, `V14ComparisonObserver`, `V15PredictionErrorObserver`, plus the v1.7 substrate patches in `v1_7_observer_substrates.py` — are inherited unchanged. V17World, V17Agent, and the 27-action architecture are inherited unchanged. The phase schedule and drive composition are inherited unchanged.

The goal layer observes the agent's state after each step. It does not modify the agent's state, reward computation, value function, or action selection. It does not modify any existing observer's records. The parallel-observer preservation property holds: with the goal layer disabled, the v1.8 batch runner produces output identical to the v1.7 baseline at matched seeds on all v1.7 metrics.

### 2.5 Experimental design

**Goal assignment logic.** Goal type and target are assigned at the start of each run according to the following fixed schedule. One goal is assigned per run; the assignment is deterministic given run_idx:

- `run_idx % 3 == 0`: `locate_family`, target = `"GREEN"`, budget = `num_steps // 2`
- `run_idx % 3 == 1`: `locate_family`, target = `"YELLOW"`, budget = `num_steps // 2`
- `run_idx % 3 == 2`: `bank_hazard_within_budget`, target = `"haz_green"`, budget = `num_steps // 2`

The step budget is set to half the run length (160,000 steps for a 320,000-step run). This is chosen to ensure that the goal-expired case occurs in a meaningful fraction of runs — the v1.7 batch showed that family traversal completion at 320,000 steps is not universal — while leaving sufficient budget for resolution to be possible. The specific budget fraction (0.5) is committed here; it is not a free parameter.

**Batch scale.** One architecture (v1.8) crossed with four hazard cost conditions (0.1, 1.0, 2.0, 10.0) crossed with ten runs per condition at 320,000 steps, totalling 40 runs. Seeds drawn from `run_data_v1_7.csv` at matched (cost, run length, run index) cells, preserving the seed chain from v1.7.

**Matched-seed goal-free comparison.** For each of the 40 v1.8 runs, a paired goal-free run (goal observer disabled) is executed at the same seed to provide the matched baseline for the Category γ individuation comparison. The 40 paired runs are not reported as standalone results; they serve only as the comparison substrate for Category γ.

**Output files.** The v1.8 batch produces the standard six observer output CSVs inherited from v1.7 (`run_data_v1_8.csv`, `provenance_v1_8.csv`, `schema_v1_8.csv`, `family_v1_8.csv`, `comparison_v1_8.csv`, `prediction_error_v1_8.csv`) plus goal-layer outputs (`goal_v1_8.csv`) and reporting layer outputs (`report_v1_8.csv`, `report_summary_v1_8.csv`).

---

## 3. Pre-flight verifications

Nine verification levels are inherited; one is added.

**Levels 1–8:** Inherited from v1.7 pipeline, applied to the v1.8 stack. Level 9 (V16ReportingLayer + SubstrateBundle portability on V17World) is re-run on the v1.8 stack before the goal layer is added to confirm no regression.

**Level 10 (new): Goal layer correctness on 10 runs.**

`verify_v1_8_level10.py` runs 10 runs at cost = 1.0, 320,000 steps, with the goal layer active, and verifies:

1. A `goal_set` record is present in each run's goal substrate.
2. Exactly one of `goal_resolved` or `goal_expired` is present in each run's goal substrate (not both; not neither).
3. If `goal_resolved`, the `resolved_at_step` is within the step budget.
4. If `goal_expired`, the `expired_at_step` equals the step budget.
5. All Q1 and Q3 statements sourced from `"goal"` have `source_resolves = True` (the goal substrate contains the claimed source_key).
6. Total hallucination count across all 10 runs is zero.

Exit 0: all six conditions hold across all 10 runs. Proceed to full v1.8 batch.
Exit 1: at least one condition fails. Print the specific failure type and run_idx. Correct before proceeding.

Level 10 must pass before the full 40-run batch begins. It is the operationalisation of the goal layer's correctness and the Category α pre-condition at Level 10 scale.

---

## 4. Metrics

All v1.7 metrics are retained unchanged. The following metrics are added for v1.8.

**Per-run goal metrics** (in `goal_v1_8.csv`):
- `goal_type`, `target_id`, `step_budget`, `set_at_step`
- `goal_resolved` (bool), `resolution_step` (int or None), `budget_remaining` (int or None)
- `goal_expired` (bool), `last_progress_step` (int or None), `goal_resolution_window` (int or None)
- `progress_event_count` — number of `goal_progress` records emitted in the run

**Per-run reporting metrics** (additions to `report_summary_v1_8.csv`):
- `statements_with_relevance_markers` — count of Q1 statements containing a relevance marker
- `goal_statement_present` — bool: a goal-sourced Q3 statement was emitted
- `goal_resolution_stated` — bool: the goal Q3 statement described resolution (True) or expiry (False)

**Biographical individuation** (extended):
- Pairwise normalised edit distances over Q1 statement sequences, as in v1.7
- Computed separately for goal-directed runs and matched goal-free runs at identical seeds
- The comparison between goal-directed and goal-free individuation distances is the Category γ substrate

---

## 5. Pre-registered interpretation categories

Seven categories are pre-registered. Categories α through Ω are inherited with extensions; one new category is added.

### 5.1 Category α: Internal consistency of all v1.8 reports

Every `ReportStatement` produced across all 40 v1.8 runs must have `source_resolves = True`. This includes statements sourced from the new `"goal"` source_type. Category α succeeds if `hallucination_count = 0` across all runs. A failure identifies either a goal substrate construction defect or a reporting layer extension defect, classified by source_type.

Category α is operationalised in advance at Level 10.

### 5.2 Category β: Query coverage

All 40 runs produce complete reports across all three query types, with goal-sourced statements present where the goal substrate is populated. `report_complete = True` in all 40 runs.

Category β succeeds if `report_complete = True` in all 40 runs and `goal_statement_present = True` in all 40 runs.

### 5.3 Category γ: Goal-directed individuation

**The load-bearing substantive finding of the iteration.**

The pre-registered expectation: pairwise biographical individuation distances in goal-directed runs are higher than in matched goal-free runs at identical seeds. Goals increase developmental divergence — an agent trying to locate the GREEN family follows a different arc from one following curiosity alone, and the arc is distinct in ways that the biographical register captures.

**Component 1: Goal-directed individuation floor.** Minimum pairwise normalised edit distance over Q1 sequences in the 40 goal-directed runs must exceed 0.05 (the programme's consistent floor, exceeded by a factor of 7.3 in v1.7).

**Component 2: Goal-directed versus goal-free comparison.** Mean pairwise individuation distance in the goal-directed runs must be higher than mean pairwise individuation distance in the matched goal-free runs. This is the directional claim: the goal layer, by shaping developmental trajectory through motivational context, increases biographical divergence.

Category γ succeeds if Component 1 holds and the Component 2 direction is confirmed. If Component 2 shows a lower mean in goal-directed runs, this is reported as a Category γ failure with the direction of the finding stated explicitly — it would be a genuine result (goals, at this budget fraction, make developmental arcs more similar rather than more distinct) and must be reported as such rather than treated as an anomaly.

### 5.4 Category δ: Pre-anticipated findings

**Goal expiry occurs in a non-trivial fraction of runs.** Given that v1.7 showed 35% end-state completion at 320,000 steps and the budget is set at half the run length (160,000 steps), goal expiry is expected in a meaningful fraction of runs at lower cost conditions (where the agent explores less efficiently) and at higher cost conditions (where hazard avoidance delays traversal). The pre-registered expectation: at least one `goal_expired` record per cost condition across the 40-run batch.

**Relevance markers appear in Q1 statements.** Where the goal target is in a family for which the agent produces mastery and knowledge-banking provenance records within the run, those records should receive relevance markers. The pre-registered expectation: the mean `statements_with_relevance_markers` per run is non-zero across all runs — every run with a goal that the agent makes some progress toward should produce at least one marked statement.

**The goal layer is additive.** With the goal observer disabled, v1.8 output is identical to v1.7 at matched seeds. This is confirmed at Level 9 re-run and is committed as a structural invariant, not an open empirical question.

### 5.5 Category Φ: Honesty constraint

The goal layer's additive character must be demonstrated, not assumed. Any finding that the goal layer modified existing observer outputs — even in a way that improved performance — is reported as a Category Φ finding: the layer was not purely additive and its effect on the prior substrate must be characterised.

The Q1 relevance markers are sourced from the goal substrate, not from the provenance substrate. If a reporting layer defect caused relevance markers to appear in statements whose source_type was incorrectly set to `"provenance"` rather than `"goal"`, that defect is a Category Φ finding: the goal layer contaminated the provenance reporting channel.

### 5.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and γ all pass.

The claim: the goal layer, introduced as a seventh parallel observer, correctly produces a motivational substrate that the reporting layer reads without modification to its existing logic. The biographical register now contains the first records of what the agent was trying to achieve and whether it succeeded. The developmental arc has acquired direction.

The deeper claim, reserved: whether goal-directedness changes what the agent learns — not how it describes what it learned, but the learning itself — is a question v1.10 (belief revision) and v1.11 (causal self-explanation) are designed to answer. v1.8 establishes that the record of intention and outcome is architecturally present. Whether the agent can eventually use that record to understand its own trajectory is the arc from here to v1.11.

### 5.7 Category ζ: Goal-resolution window as a new developmental measure

The `goal_resolution_window` — the gap between last progress event and budget expiry — is a new quantitative measure with no prior-iteration equivalent. It is the direct structural parallel to the prediction-error resolution window from v1.5: the developmental distance between the closest approach to success and the moment the budget expired.

**Component 1: Non-degenerate distribution.** Across runs where `goal_expired = True` and `last_progress_step is not None`, the distribution of `goal_resolution_window` values must show non-trivial variance (standard deviation > 0 across the expired runs). A degenerate distribution — all windows the same length — would indicate that the goal progress events are fired too late in the run to produce meaningful variance.

**Component 2: Cost-sensitivity.** The mean `goal_resolution_window` should vary across cost conditions. The directional prediction (consistent with v1.5): at cost = 2.0, the mean window is the shortest (agents at this cost level are most efficient at close-range traversal); at cost = 10.0, the mean window is the longest (high-cost avoidance delays progress events).

Category ζ succeeds if Component 1 holds. Component 2 is exploratory — a directional prediction, not a pass/fail criterion, reported regardless of direction.

---

## 6. Connection to the SICC trajectory

v1.8 advances the SICC trajectory on one commitment and positions two further commitments.

**Commitment 5 (goal-directedness as a precondition for genuine learning)** is advanced at the first layer. The goal layer introduces the architecture's first record of what the agent was trying to achieve. The agent now has goals, progress events, and resolution or expiry records. It does not yet choose its goals (that remains reserved), but it has the substrate on which chosen goals would be recorded. The developmental arc has acquired direction.

**Commitment 7 (prediction-surprise as learning signal)** is advanced indirectly. The goal-resolution window — the gap between last progress and budget expiry — is a new instance of the resolution-window concept introduced by the prediction-error observer at v1.5. The architecture now holds two parallel resolution-window structures: one measuring the distance between first hazard awareness and readiness-to-transform; one measuring the distance between closest goal approach and budget expiry. Whether these two window types are correlated — whether agents that resolve prediction errors quickly also resolve goals efficiently — is an exploratory question v1.8 can begin to address.

**Commitment 8 (self-knowledge as derivative of object-knowledge)** is advanced. The relevance markers in Q1 connect the agent's developmental history (what it learned, when, with what confirmation) to its motivational context (what it was trying to achieve). The self-account now includes a layer of purpose: the agent's record of which encounters were relevant to its goal. This is the first moment in the programme where the biographical register describes not only what happened but what it was for.

The commitments not yet advanced by v1.8 — counterfactual record (Commitment 3), belief revision (Commitment 9), causal self-explanation — remain reserved for v1.9 through v1.11.

---

## 7. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.8 implementation work begins.

**Matched-seed comparison.** Seeds drawn from `run_data_v1_7.csv` at every (cost, run length, run index) cell. Paired goal-free runs use the same seeds with the goal observer disabled.

**Pre-flight verifications.** All ten levels pass before the full v1.8 batch runs. Level 9 re-run (regression check) before Level 10. Level 10 before full batch.

**Single-architectural-change discipline.** v1.8 introduces the goal layer as the singular architectural extension. The parallel-observer pattern is preserved for a seventh layer. No agent behaviour is modified. No existing observer is modified. The goal layer is purely additive.

**Amendment policy.** Three amendments available. No amendment is provisionally reserved; the goal layer specification above is sufficiently precise that a metric-specification amendment is not anticipated. Two available for unanticipated operational issues; one held in reserve.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 3 May 2026, before any v1.8 code is written.

---

## 8. Stopping rule

The v1.8 iteration completes when:

- All ten pre-flight verifications pass.
- The full 40-run batch has run (plus 40 paired goal-free runs for Category γ comparison).
- Categories α, β, γ, δ, Φ, Ω, and ζ have been characterised in the v1.8 paper.
- The v1.8 paper is drafted.
- The carry-forward note for v1.9 is written.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve and no amendments remain.

---

## 9. New files required

- `v1_8_goal_layer.py` — goal specification, progress tracking, `goal_set` / `goal_progress` / `goal_resolved` / `goal_expired` record types; `get_substrate()` implementation returning the goal substrate dict
- `v1_8_observer_substrates.py` — extends `build_bundle_from_observers()` with `goal_obs` parameter; adds `bundle.resolve("goal", ...)` logic; extends `SubstrateBundle` with `goal` field; extends `V16ReportingLayer` with Q1 relevance markers and Q3 goal statement
- `curiosity_agent_v1_8_batch.py` — batch runner with deterministic goal assignment logic, paired goal-free runs, and goal substrate flush to `goal_v1_8.csv`
- `verify_v1_8_level10.py` — Level 10 pre-flight: six correctness criteria across 10 runs before full batch

---

## 10. References

Baker, N.P.M. (2026a–v) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.2. Full reference list inherited from v1.3 paper.

Baker, N.P.M. (2026w–z) v1.3 pre-registration, amendments, and paper. See v1.6 reference list.

Baker, N.P.M. (2026aa–ab) v1.4 pre-registration and paper. See v1.6 reference list.

Baker, N.P.M. (2026ac–ad) v1.5 pre-registration and paper. See v1.6 reference list.

Baker, N.P.M. (2026ae) 'v1.6 Pre-Registration: Reporting Layer via SubstrateBundle Interface on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026af) 'Biographical Self-Account in a Small Artificial Learner: The Reporting Layer as Substrate-Agnostic Reading Component', preprint, 2 May 2026.

Baker, N.P.M. (2026ag) 'v1.7 Pre-Registration: Substrate Transposition to a Richer Simulated Environment', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026ah) 'Substrate Transposition in a Small Artificial Learner: The Cognitive Layer Meets a Richer World', preprint, 3 May 2026.

Baker, N.P.M. (2026ai) 'v1.8 Pre-Registration: Goal Assignment and Motivated Learning', GitHub repository, 3 May 2026.

Baker, N.P.M. (internal record, v0.5 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 3 May 2026, before any v1.8 implementation work begins.
