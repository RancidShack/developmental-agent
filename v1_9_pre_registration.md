# v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.9 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

Eight iterations have built a developmental agent with a complete biographical archive: an account of what it encountered, what it learned, how its knowledge is structured, how one family's architecture relates to another's, where its expectations were violated and how long it took to resolve the violations, and — as of v1.8 — what it was trying to achieve and whether it succeeded. The archive is auditable. It is individually variable. It now carries motivational context.

What the archive does not hold is a record of restraint.

The v1.8 goal layer produces two distinct expired-run profiles. In ten of the forty runs, the goal observer records `goal_progress = []` and `goal_environment_mapped` is not None: the agent surveyed the environment in Phase 1, perceived the target's distal object, and then did not engage with it in Phase 2 within the observation window. The goal substrate records the absence of engagement. It cannot record what happened at the boundary — whether the agent approached the target in Phase 2, came within perception radius, and withdrew without contact. The substrate says the approach never came. It cannot say why.

This is the gap v1.9 closes. The counterfactual record — a new substrate field and a new observer — captures the event structure that, in a developmental account, constitutes a suppressed approach: the agent was in proximity, the object was perceivable, the agent withdrew without making contact. The record does not require the agent to have made a choice in any strong philosophical sense. It requires the substrate to hold, for the first time, a register of what the agent could have done and did not.

This is SICC Commitment 3 (unfillable slots as epistemic features) becoming operative at the behavioural level, and the first operationalisation of the SICC document's account of developmental restraint: the capacity to approach an anxiety-producing object, remain in proximity, and withdraw without contact is itself a developmental achievement. The register will now record it.

The biographical register gains a fourth query type. Q1 describes what the agent learned. Q2 describes how that knowledge is structured across families. Q3 describes where the agent's expectations were violated. Q4, introduced at v1.9, describes where the agent held back: *At step 493, I came within 1.2 units of haz_yellow without making contact. I withdrew. I had not yet mastered att_yellow.*

---

## 2. Architectural specification

### 2.1 The counterfactual observer

The v1.9 counterfactual observer (`V19CounterfactualObserver`) is the eighth parallel observer. It holds no state during the run beyond the detection window buffers described below. It fires `suppressed_approach` records when the event signature — approach followed by recession without contact — is confirmed. It produces one record per suppressed-approach event per object per run; multiple events per object are permitted.

**Detection logic.** At each step, the observer computes the Euclidean distance from the agent's current position to every eligible object's position. It maintains a rolling distance buffer per object. A suppressed approach is confirmed when:

1. The agent has moved monotonically closer to the object for at least **N_approach = 10** consecutive steps (distance decreasing at each step).
2. No contact was made during or after the approach window (the object's `object_id` was not returned by `world._contact_at_pos()` at any step within the window).
3. The agent's distance from the object then increases for at least **N_recession = 5** consecutive steps (distance increasing at each step).

The `closest_approach_distance` is the minimum distance recorded during the approach window. The `closest_approach_step` is the step at which that minimum was reached. These parameters — N_approach = 10, N_recession = 5 — are committed here and are not free parameters.

**Eligible objects.** Objects eligible for suppressed-approach detection are:
- Any object with `object_type == HAZARD` (costly objects requiring precondition traversal)
- Any `DIST_OBJ` (distal-tier colour cell) that is the current goal target's family distal object, where the goal type is `locate_family`

`NEUTRAL`, `ATTRACTOR`, `END_STATE`, and `KNOWLEDGE`-state objects are not eligible. The rationale: suppressed approaches are architecturally meaningful for objects that carry risk or for goal-relevant targets the agent has not yet engaged with. Attractor mastery is approached freely; suppressed-approach detection is reserved for objects where approach-and-withdrawal has developmental significance.

**What V19CounterfactualObserver does not do.** It does not modify the agent's state, reward function, or action selection. It does not modify any existing observer's records. It does not write to the provenance substrate. It reads `world.agent_pos`, `world.object_positions`, `world._contact_at_pos()`, and the `bundle.goal` substrate field (read-only) at `on_run_end`. The parallel-observer preservation property holds: with the counterfactual observer disabled (`--no-counterfactual`), all existing observer outputs are byte-identical to v1.8.2 at matched seeds.

### 2.2 The suppressed-approach record

One record per confirmed suppressed-approach event, with the following structure:

```
{
  object_id:                  str,    # e.g. "haz_yellow"
  closest_approach_step:      int,    # step of minimum distance
  closest_approach_distance:  float,  # Euclidean distance at closest point
  phase_at_approach:          int,    # agent.phase at closest_approach_step
  goal_relevant:              bool,   # True if object_id is the active goal target
  pre_threshold_entries:      int,    # agent.pre_transition_hazard_entries[object_id]
                                      # at closest_approach_step; 0 if not applicable
}
```

`pre_threshold_entries` is read from `agent.pre_transition_hazard_entries` — the same field the v1.8 goal layer reads in `_check_progress()` for `bank_hazard_within_budget` goals. It records how many times the agent had already paid the cost for the suppressed object before the suppressed approach. A value of 0 means the approach occurred before any prior contact; a value > 0 means the agent had already made contact with this object and the suppressed approach represents a withdrawal after prior experience. This field is the substrate for v1.10's belief-revision layer.

### 2.3 The SubstrateBundle extension

`SubstrateBundle` gains a `counterfactual` field. The field is `None` if the counterfactual observer was not active, or a list of suppressed-approach record dicts when active (one entry per confirmed event; may be an empty list if no suppressed approaches were detected in the run).

`bundle.resolve("counterfactual", source_key)` resolves as follows:

- `source_key` format: `"suppressed_approach:{object_id}:{closest_approach_step}"`
- Returns `True` if a record exists in `bundle.counterfactual` with matching `object_id` and `closest_approach_step`
- Returns `False` if `bundle.counterfactual` is `None` or no matching record is found

The `build_bundle_from_observers()` function gains a `counterfactual_obs` parameter (default `None`). When supplied, it calls `counterfactual_obs.get_substrate()` and places the result in the bundle's `counterfactual` field. All eight existing parameters are unchanged; backward compatibility is preserved.

The `v1_9_observer_substrates.py` module monkey-patches `SubstrateBundle.__init__`, `SubstrateBundle.resolve()`, and `build_bundle_from_observers()` following the exact pattern established in `v1_8_observer_substrates.py`. The v1.8 module is imported first; v1.9 patches are applied on top. No v1.8 logic is replaced.

### 2.4 The reporting layer extension: Q4

`V16ReportingLayer` is extended to produce Q4 statements from the counterfactual substrate. Q4 is a new query type: `query_type = "where_held_back"`. It answers the question: *Where did I approach without making contact?*

**Q4 statement text template:**

> *At step {closest_approach_step}, I came within {closest_approach_distance:.2f} units of {object_id} without making contact. I withdrew. [{goal_relevant_clause}] [{pre_threshold_clause}]*

Where:
- `goal_relevant_clause` (if `goal_relevant = True`): `"This object was my active goal target."`
- `pre_threshold_clause` (if `pre_threshold_entries == 0`): `"I had not yet entered this object."`
- `pre_threshold_clause` (if `pre_threshold_entries > 0`): `"I had entered this object {pre_threshold_entries} time(s) previously."`

`source_type`: `"counterfactual"`
`source_key`: `"suppressed_approach:{object_id}:{closest_approach_step}"`

Each confirmed suppressed-approach record produces one Q4 statement. If no suppressed approaches were detected in a run, no Q4 statements are produced for that run; `query_where_held_back()` returns an empty list. An empty Q4 is not a Category β failure — it is an accurate report of a run in which no suppressed approaches met the detection threshold.

**`generate_report()` extension.** The reporting layer's `generate_report()` call is extended to include `query_where_held_back()` after `query_where_surprised()`. The full query sequence at v1.9 is: Q1, Q2, Q3, Q4.

### 2.5 What v1.9 does not change

All eight existing observers — `V1ProvenanceStore`, `V13SchemaObserver`, `V13FamilyObserver`, `V14ComparisonObserver`, `V15PredictionErrorObserver`, `V16ReportingLayer`, the v1.7 and v1.8 substrate patches, and `V18GoalObserver` — are inherited unchanged. `V17World`, `V17Agent`, the 27-action architecture, the phase schedule, and the drive composition are inherited unchanged. The goal assignment schedule (`run_idx % 3`) and budget fraction (0.5) are inherited unchanged.

V19CounterfactualObserver is the singular architectural extension at v1.9. The single-variable-change discipline holds.

---

## 3. Experimental design

**Batch scale.** One architecture (v1.9) crossed with four hazard cost conditions (0.1, 1.0, 2.0, 10.0) crossed with ten runs per condition at 320,000 steps, totalling 40 runs. Seeds drawn from `run_data_v1_8.csv` at matched (cost, run length, run index) cells, preserving the seed chain from v1.8.

**Goal assignment.** Inherited from v1.8 unchanged: `run_idx % 3 == 0` → `locate_family`, target = `"GREEN"`; `run_idx % 3 == 1` → `locate_family`, target = `"YELLOW"`; `run_idx % 3 == 2` → `bank_hazard_within_budget`, target = `"haz_green"`. Budget fraction = 0.5.

**Matched goal-free comparison.** The 40 paired goal-free runs from v1.8 are available as the individuation baseline. No additional paired runs are required at v1.9 unless the Category γ comparison requires them. A decision on whether to run paired goal-free runs at v1.9 is made at pre-flight Level 11; the default is to carry the v1.8 paired baseline forward for the Q1 individuation comparison and run fresh paired runs only if the Q4 individuation comparison requires a v1.9-specific baseline. This decision is committed at Level 11, not here.

**Output files.** The v1.9 batch produces all v1.8 output CSVs (tagged `v1_9`) plus:
- `counterfactual_v1_9.csv` — per-event suppressed-approach records (one row per confirmed event, not per run; may contain multiple rows per run)
- `report_v1_9.csv` — full statement list including Q4 statements
- `report_summary_v1_9.csv` — per-run summary metrics including Q4 counts

---

## 4. Pre-flight verifications

Ten verification levels are inherited; one is added.

**Levels 1–9:** Inherited from v1.8 pipeline, applied to the v1.9 stack. Level 10 (goal layer correctness) is re-run as a regression check on the v1.9 stack before the counterfactual layer is added.

**Level 11 (new): Counterfactual observer correctness on 10 runs.**

`verify_v1_9_level11.py` runs 10 runs at cost = 1.0, 80,000 steps, with the counterfactual observer active (and the goal observer active, as at v1.8.2). It verifies:

1. **`counterfactual_field_present`** — `bundle.counterfactual` is a list (not `None`) in every run. An empty list is valid; `None` is a construction failure.
2. **`source_key_format_valid`** — Every Q4 statement's `source_key` matches the format `"suppressed_approach:{object_id}:{step}"` where `object_id` is a known world object and `step` is a non-negative integer.
3. **`source_resolves_for_all_q4`** — Every Q4 statement has `source_resolves = True`: `bundle.resolve("counterfactual", source_key)` returns `True` for each Q4 statement's source key.
4. **`zero_hallucinations`** — Total hallucination count across all statements (Q1–Q4) is zero across all 10 runs.
5. **`eligible_objects_only`** — Every suppressed-approach record's `object_id` refers to a `HAZARD`-type or goal-relevant `DIST_OBJ`; no `NEUTRAL`, `ATTRACTOR`, `END_STATE`, or `KNOWLEDGE` object appears in the counterfactual substrate.
6. **`detection_window_integrity`** — For at least one run, at least one suppressed-approach record is present (confirming the detection logic fires at this step count and cost level). A run set with zero suppressed-approach records across all 10 runs at cost = 1.0 is a detection logic failure, not a valid null finding, and must be diagnosed before the full batch proceeds.
7. **`additive_discipline`** — With `--no-counterfactual`, all Q1–Q3 outputs are byte-identical to the v1.8.2 baseline at matched seeds (Level 10 re-run confirmed first; this adds the explicit counterfactual-disabled check).

Exit 0: all seven criteria hold across all 10 runs. Proceed to full v1.9 batch.
Exit 1: at least one criterion fails. Print the specific failure type and run_idx. Correct before proceeding.

Level 10 re-run must pass before Level 11 begins. Level 11 must pass before the full 40-run batch begins.

---

## 5. Metrics

All v1.8 metrics are retained unchanged. The following metrics are added for v1.9.

**Per-event counterfactual metrics** (`counterfactual_v1_9.csv`):
- `arch`, `run_idx`, `seed`, `hazard_cost`, `num_steps` — run identification
- `object_id`, `closest_approach_step`, `closest_approach_distance` — event identification
- `phase_at_approach` — phase in which the suppressed approach occurred
- `goal_relevant` — whether the object was the active goal target
- `pre_threshold_entries` — prior contact count at time of suppressed approach

**Per-run counterfactual summary** (added to `report_summary_v1_9.csv`):
- `q4_statement_count` — number of Q4 statements produced in the run (0 or more)
- `suppressed_approach_count` — number of confirmed suppressed-approach events
- `goal_relevant_suppressed_count` — suppressed approaches where `goal_relevant = True`
- `suppressed_approach_objects` — comma-separated list of object_ids for which suppressed approaches were recorded

**Three-way contact register.** For each eligible object in each run, the register holds the full developmental profile: clean contact (no prior suppressed approach, cost paid), suppressed approach (approach to within detection threshold, withdrawal without contact), and prediction-error contact (cost paid before precondition met, resolved_surprise fired). This three-way classification is computed post-hoc from the combined counterfactual, provenance, and prediction-error substrates. It is a derived metric, not a new substrate field. It is reported in the paper but is not a pass/fail criterion.

---

## 6. Pre-registered interpretation categories

Seven categories are pre-registered. Categories α through Ω are inherited with the extensions described below. One new category is added.

### 6.1 Category α: Internal consistency of all v1.9 reports

Every `ReportStatement` produced across all 40 v1.9 runs — including all Q4 statements — must have `source_resolves = True`. This includes statements sourced from the new `"counterfactual"` source_type. Category α succeeds if `hallucination_count = 0` across all runs.

A Q4 hallucination is a statement whose `source_key` does not resolve to a record in `bundle.counterfactual`. This would indicate a detection-to-reporting pipeline defect: the reporting layer claimed a suppressed approach that the substrate does not hold. The audit trail for Q4 statements is: Q4 statement → `source_key` → `bundle.counterfactual` record → `closest_approach_step` in `counterfactual_v1_9.csv`. Every link must be traceable.

Category α is operationalised in advance at Level 11.

### 6.2 Category β: Query coverage

All 40 runs produce complete reports across all four query types. `report_complete = True` in all 40 runs. For Q4 specifically: every run where at least one suppressed-approach event was confirmed produces at least one Q4 statement; every run where no suppressed-approach events were confirmed produces zero Q4 statements and `report_complete` is nonetheless True (the absence is accurate, not a coverage failure).

Category β succeeds if `report_complete = True` in all 40 runs.

### 6.3 Category γ: Counterfactual individuation

**The load-bearing substantive finding of the iteration.**

The pre-registered expectation: the counterfactual substrate is individually variable — different agents produce different suppressed-approach profiles, and this variation is captured in the Q4 statement sequences. Agents that are close in their Q1 developmental arc may diverge substantially in their Q4 profiles (one agent withdrew from haz_yellow twice before making contact; another approached it once at high speed and entered on first contact).

**Component 1: Non-trivial suppressed-approach rate.** Across the 40-run batch, at least 50% of runs produce at least one confirmed suppressed-approach record. A detection rate below 50% suggests the detection thresholds (N_approach = 10, N_recession = 5) are too conservative for the V17World environment and requires characterisation as a Category γ finding rather than a pass.

**Component 2: Q4 individuation.** Pairwise normalised edit distances over Q4 statement sequences (where Q4 is non-empty) must show non-trivial variance — standard deviation of pairwise distances > 0.05 across runs with Q4 statements. The same metric used for Q1 individuation at v1.7 and v1.8 is applied here.

**Component 3: Q4–Q1 correlation.** Whether an agent's Q4 profile (suppressed approaches) correlates with its Q1 profile (what it learned) is an exploratory question, reported regardless of direction. The pre-registered directional expectation: runs with higher Q1 individuation (more distinctive developmental arcs) also show higher Q4 suppressed-approach counts — agents that take idiosyncratic paths through the environment also show idiosyncratic restraint patterns. This is a directional prediction only; it is not a pass/fail criterion.

Category γ succeeds if Components 1 and 2 hold. Component 3 is exploratory.

### 6.4 Category δ: Pre-anticipated findings

**The ten registered-but-not-engaged runs from v1.8 produce suppressed-approach records at v1.9.** The v1.8 goal data shows ten runs where `goal_environment_mapped` is not None and `goal_progress` is empty — runs where the agent located the target in Phase 1 but never engaged in Phase 2. At v1.9, the prediction is that a meaningful fraction of these runs will produce at least one suppressed-approach record for the goal-relevant target: the agent did approach in Phase 2, came within the detection threshold, and withdrew. This would close the interpretive gap the v1.8 carry-forward identified. The fraction is not pre-specified; any non-zero count within this subset is a confirmatory finding and reported explicitly.

**Goal-relevant suppressed approaches cluster in expired runs.** Runs where the goal expired without progress (`goal_progress = []` and `goal_expired = True`) are expected to show higher `goal_relevant_suppressed_count` than runs where the goal resolved. An agent that was trying to reach the GREEN family, came close to dist_green, and withdrew, without ever making contact, has both an expired goal and a goal-relevant suppressed approach. These two records, taken together, constitute the first architectural description of an agent that held back from its own objective.

**Pre-threshold suppressed approaches (prior contact = 0) cluster at lower cost conditions.** At cost = 0.1, hazard objects carry minimal penalty; first contact is inexpensive. An agent at this cost level that produces a suppressed approach with `pre_threshold_entries = 0` is withdrawing from an object it has never entered and that costs little to enter. This is the cost condition where suppressed approaches with zero prior contact are least expected and most interesting. The directional prediction: pre-threshold suppressed approaches are more frequent at cost = 2.0 and cost = 10.0 than at cost = 0.1. Reported regardless of direction.

### 6.5 Category Φ: Honesty constraint

The counterfactual observer detects approach-and-withdrawal events from position data. It does not infer intent. The Q4 statement — *I withdrew* — describes a trajectory event, not a decision. The honesty constraint: the pre-registration must not overstate what the counterfactual record establishes.

The substantive reading: the counterfactual substrate holds, for the first time, a record that an agent came close to an eligible object and moved away without contact. This record is detectable from position data, individually variable, and auditable in exactly the same sense as all prior substrate records.

The deflationary reading: withdrawal from proximity is not the same as suppression in the psychodynamic sense. The agent does not experience approach anxiety. The architectural parallel to Winnicott's account of developmental restraint — the capacity to approach an anxiety-producing object and withdraw without destroying it — is a structural analogy, not a claim about inner states. What v1.9 establishes is that the event structure that, in a developmental account, constitutes suppressed approach is now detectable and recorded. Whether this event structure reflects anything cognitively richer than proximity avoidance is the question v1.10 and v1.11 are designed to address.

Both readings are consistent with the v1.9 batch. The biographical register holds the record; the interpretation is reserved.

### 6.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and γ all pass.

The claim: the counterfactual observer, introduced as an eighth parallel observer, correctly produces a suppressed-approach substrate that the reporting layer reads to generate Q4 statements that are auditable, individually variable, and structurally connected to the goal and provenance substrates. The biographical register now holds, for the first time, a record of what the agent could have done and did not do.

The deeper claim, reserved: the suppressed-approach record, combined with the v1.8 goal substrate, establishes the two-substrate foundation on which v1.10's belief-revision layer will operate. An agent that held back from its goal target before budget expiry, and for which the counterfactual record says it came within detection range and withdrew, has the architectural prerequisites for belief revision: a record of what it intended, a record of where it held back, and (at v1.10) a record of what it believed about the target object at the moment of withdrawal. The counterfactual substrate is the load-bearing architectural element v1.10 requires.

### 6.7 Category η: The three-way contact register

A new category, specific to v1.9. The three-way contact register — clean contact, suppressed approach, prediction-error contact — constitutes the developmental classification of every eligible object's history in each run. Category η succeeds if, across the 40-run batch, all three event types are present in at least one run per cost condition. A cost condition in which no suppressed approaches are recorded (the register contains only clean contacts and prediction errors) is a Category η finding, reported explicitly.

Category η does not have a pass/fail criterion at the batch level — its role is to characterise the completeness of the developmental register across cost conditions. A batch in which all three event types are present at every cost condition is the strongest possible confirmation that the suppressed-approach detection threshold is appropriately calibrated for V17World.

---

## 7. Connection to the SICC trajectory

v1.9 advances the SICC trajectory on two commitments and positions a third.

**Commitment 3 (unfillable slots as epistemic features)** is advanced at the behavioural level. Prior iterations have held unfillable slots as structural absences — things the agent's body cannot measure. v1.9 extends this to behavioural epistemics: a suppressed approach is a slot that the agent *could* have filled but did not. The counterfactual record holds the attempted access and the withdrawal. This is the first iteration in which the architecture records not only what the agent knows and does not know, but what it approached knowing and chose not to complete.

**Commitment 5 (goal-directedness as a precondition for genuine learning)** is advanced at the second layer. v1.8 gave the agent a goal and a record of whether it was met. v1.9 gives it a record of where it held back from its own goal — the approach-withdrawal events that constitute the developmental distance between *I was trying* and *I succeeded*. Goal-directedness is now legible not only in resolution and expiry records, but in the suppressed-approach trajectory that lies between them.

**Commitment 9 (belief revision as a cognitive-layer operation)** is positioned. The `pre_threshold_entries` field in the suppressed-approach record holds the architectural prerequisite for v1.10: how many times the agent had already contacted the object before withdrawing. An agent with `pre_threshold_entries = 2` and a suppressed approach has prior experience of this object and still chose not to enter. v1.10's belief-revision layer reads this field alongside the prediction-error substrate to construct the revised-expectation record. The v1.9 substrate is load-bearing for v1.10 in exactly the way the v1.8 goal substrate is load-bearing for v1.9.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.9 implementation work begins.

**Matched-seed comparison.** Seeds drawn from `run_data_v1_8.csv` at every (cost, run length, run index) cell, preserving the seed chain.

**Pre-flight verifications.** Level 10 re-run passes before Level 11. Level 11 passes before the full v1.9 batch.

**Single-architectural-change discipline.** v1.9 introduces the counterfactual observer as the singular architectural extension. All eight existing observers are inherited unchanged. The parallel-observer pattern is preserved for a ninth layer if required at v1.10.

**Detection threshold commitment.** N_approach = 10, N_recession = 5 are committed here and are not adjusted without a pre-registration amendment. If Level 11 Criterion 6 fails (zero suppressed approaches across all 10 verification runs), a threshold amendment is the correct response, not a silent parameter adjustment.

**Amendment policy.** Three amendments available. No amendment is provisionally reserved. The detection thresholds above are specified with sufficient precision that a threshold-adjustment amendment is possible but not anticipated. Two available for unanticipated operational issues; one held in reserve.

**Q4 as new query type.** The suppressed-approach statements occupy Q4 (`query_type = "where_held_back"`), not an extended Q3. This is committed here. Q3 describes where the agent's expectations were violated by contact; Q4 describes where approach occurred without contact. These answer structurally different questions and are held in separate query types.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 4 May 2026, before any v1.9 code is written.

---

## 9. Stopping rule

The v1.9 iteration completes when:

- Level 10 re-run passes on the v1.9 stack.
- Level 11 passes across all seven criteria.
- The full 40-run batch has run.
- Categories α, β, γ, δ, Φ, Ω, and η have been characterised in the v1.9 paper.
- The v1.9 paper is drafted.
- The carry-forward note for v1.10 is written.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve and no amendments remain.

---

## 10. New files required

- `v1_9_counterfactual_observer.py` — V19CounterfactualObserver; detection logic with N_approach = 10, N_recession = 5; `get_substrate()` returning list of suppressed-approach records
- `v1_9_observer_substrates.py` — monkey-patches `SubstrateBundle` with `counterfactual` field; extends `build_bundle_from_observers()` with `counterfactual_obs` parameter; extends `V16ReportingLayer` with `query_where_held_back()` (Q4); imports v1.8 substrate patches first
- `curiosity_agent_v1_9_batch.py` — batch runner with counterfactual observer active, `--no-counterfactual` flag, flush to `counterfactual_v1_9.csv`
- `verify_v1_9_level11.py` — Level 11 pre-flight: seven correctness criteria across 10 runs at cost = 1.0, 80,000 steps

---

## 11. References

Baker, N.P.M. (2026a–v) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.2. Full reference list inherited from v1.3 paper.

Baker, N.P.M. (2026w–z) v1.3 pre-registration, amendments, and paper. See v1.6 reference list.

Baker, N.P.M. (2026aa–ab) v1.4 pre-registration and paper. See v1.6 reference list.

Baker, N.P.M. (2026ac–ad) v1.5 pre-registration and paper. See v1.6 reference list.

Baker, N.P.M. (2026ae) 'v1.6 Pre-Registration: Reporting Layer via SubstrateBundle Interface on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026af) 'Biographical Self-Account in a Small Artificial Learner: The Reporting Layer as Substrate-Agnostic Reading Component', preprint, 2 May 2026.

Baker, N.P.M. (2026ag) 'v1.7 Pre-Registration: Substrate Transposition to a Richer Simulated Environment', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026ah) 'Substrate Transposition in a Small Artificial Learner: The Cognitive Layer Meets a Richer World', preprint, 3 May 2026.

Baker, N.P.M. (2026ai) 'v1.8 Pre-Registration: Goal Assignment and Motivated Learning', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026aj) 'v1.8.1 Pre-Registration Amendment: Mapping and Engagement Separated', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026ak) 'v1.8.2 Pre-Registration Amendment', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026al) 'Goal-Directed Learning in a Small Artificial Learner: Motivation, Mapping, and the Failure Register', preprint, 3 May 2026.

Baker, N.P.M. (2026am) 'v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach', GitHub repository, 4 May 2026.

Baker, N.P.M. (internal record, v0.5 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 4 May 2026, before any v1.9 implementation work begins.
