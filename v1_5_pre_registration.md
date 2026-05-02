# v1.5 Pre-Registration: Prediction-Error Elevation via Per-Encounter Observer on Existing Architecture

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.5 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

The v1.4 iteration introduced a fifth parallel observer that reads the completed family traversal records at run end and computes structural comparison measures between the two families. One field in the v1.4 per-run data became significant not for what it measured but for what it left unnamed: `pre_transition_entries_per_cell`. This field records how many times an agent entered a family hazard cell before the precondition attractor was mastered. Across 240 runs, the yellow pyramid at (5,8) records a mean of 1.400 pre-transition entries per run (max 3); the green sphere at (14,14) records a mean of 0.171 (max 3). At 320k steps, where both families complete in all 60 runs, 36 of 60 agents show a yellow pre-transition count greater than zero — meaning the agent approached the yellow pyramid, paid the hazard cost, and did not receive the HAZARD-to-KNOWLEDGE transformation. The architecture recorded the cost. It did not record that the outcome was unexpected.

This is the gap v1.5 addresses. The agent approached a cell it could not yet unlock, paid a cost for an outcome it did not receive, and later — when the precondition was met — returned and the transformation fired. The gap between first approach and eventual transformation is a resolution window: a measure of developmental distance between the agent's first encounter with a structural rule and the moment it had the resources to satisfy it. The architecture currently holds the cost side of this sequence. It does not hold the surprise side, the resolution side, or the window between them.

The v1.5 iteration introduces **prediction-error elevation** as the singular architectural extension. A sixth parallel observer records each encounter with a family hazard cell — and with the three unaffiliated hazard cells — as a typed event: resolved surprise, unresolved approach, or clean first entry. The resolution window — the step-gap between first pre-transition approach and eventual HAZARD-to-KNOWLEDGE transformation — is the primary quantitative finding of the iteration.

This is the SICC document's Commitment 7 becoming operative: prediction-surprise as a learning signal, elevated to first-class status as a per-encounter record held alongside the provenance, schema, family, and comparison records. It is not a modification of the agent's reward function. It is a record of structural mismatch between what the agent's action produced and what the architecture's structural rule would have produced if the precondition had been met. The prediction-error record is the raw material from which self-knowledge — Commitment 8 — is eventually constructed.

---

## 2. Architectural specification

The v1.5 architecture inherits v1.4 unchanged except for the addition of the prediction-error observer module. The single-variable-change discipline holds: v1.5 introduces prediction-error elevation as the singular architectural extension.

### 2.1 The prediction-error observer

The v1.5 prediction-error observer (`V15PredictionErrorObserver`) is a sixth parallel observer implementing the same three-hook interface as the existing five. Unlike the v1.4 comparison observer — which holds no live state and operates entirely at run end — the prediction-error observer must hold live state during the run in order to detect pre-transition approach events as they occur.

**Live state held during the run:**

- Per hazard cell: a list of approach events before the precondition attractor is mastered. Each approach event records the step at which the entry occurred and the cost paid.
- Per hazard cell: whether the precondition was met at the time of each approach (assessed against the family-specific competency gate for family cells; against the global competency threshold for unaffiliated cells).
- The step at which the HAZARD-to-KNOWLEDGE transformation fires for each cell (populated during the run as transitions are observed).

**on_pre_action(step):** No action required. The prediction-error observer does not modify agent behaviour or selection.

**on_post_event(step):** The observer reads the world state after each action. If the agent has entered a hazard cell, the observer records whether the precondition was met at the time of entry, the cost paid, and whether the transformation fired on this step. This is the core per-encounter record.

**on_run_end(step):** The observer classifies all recorded approach events into the three encounter types, computes per-run summary fields, and populates the output records.

### 2.2 Encounter types

The prediction-error observer distinguishes three mutually exclusive encounter types per hazard cell per approach event:

**Resolved surprise.** The agent entered a family hazard cell before the precondition attractor was mastered, paid the cost, and did not receive the transformation at the time of entry. Subsequently, the precondition was met and the transformation fired within the run. The approach event is a resolved surprise; the resolution window is `transformation_step − approach_step`.

**Unresolved approach.** The agent entered a family hazard cell before the precondition attractor was mastered, paid the cost, and the transformation did not fire within the run. The approach is recorded with `transformed_at_step = None` and `resolution_window = None`.

**Clean first entry.** The agent entered a family hazard cell after the precondition attractor was mastered. The first approach produces the transformation. No prediction error is recorded for this event.

A single hazard cell within a run may produce multiple pre-transition approach events before the precondition is met; each is recorded as a separate encounter. Only the first approach event for a given cell within a run contributes to the `yellow_resolution_window` and `green_resolution_window` summary fields. The full encounter list is preserved in the per-encounter output file.

### 2.3 Per-encounter record fields

One row is written to `prediction_error_v1_5.csv` per approach event per hazard cell per run, for all five hazard cells (two family cells and three unaffiliated cells):

- `arch`, `hazard_cost`, `num_steps`, `run_idx`, `seed` — run identification
- `step` — the step at which the approach occurred
- `cell` — the cell coordinate
- `family` — `GREEN` or `YELLOW` for family cells; `None` for unaffiliated cells
- `precondition_met` — `True` if the precondition attractor was mastered before this approach; `False` if not
- `cost_paid` — the hazard cost incurred at this step
- `transformed_at_step` — the step at which the HAZARD-to-KNOWLEDGE transformation subsequently fired (`None` if not within the run)
- `resolution_window` — `transformed_at_step − step` (`None` if `transformed_at_step` is `None`)
- `encounter_type` — one of `resolved_surprise`, `unresolved_approach`, `clean_first_entry`

### 2.4 Per-run summary fields

The following fields are added to `run_data_v1_5.csv` alongside all v1.4 fields:

- `yellow_pre_transition_entries` — count of pre-transition approach events for the yellow pyramid at (5,8) within the run (i.e. approaches before yellow attractor mastery). Corresponds to the `pre_transition_entries_per_cell` entry for (5,8) in v1.4; reproduced here for direct comparability.
- `green_pre_transition_entries` — corresponding count for the green sphere at (14,14).
- `unaffiliated_pre_transition_entries` — total count across the three unaffiliated hazard cells ((5,9), (6,8), (14,13)).
- `yellow_resolution_window` — steps between the first yellow pre-transition approach and the yellow transformation (`None` if no pre-transition approach occurred, or if the transformation did not fire within the run).
- `green_resolution_window` — corresponding field for the green sphere.
- `total_prediction_error_events` — total count of pre-transition approach events across all five hazard cells within the run.
- `prediction_error_complete` — `True` if at least one per-encounter record exists for the run.

### 2.5 What the prediction-error observer does not change

The prediction-error observer does not modify the agent's value function, Q-values, or intrinsic reward calculation. The agent's action-selection, drive composition, competency-gating rule, and phase schedule are inherited from V14Agent unchanged. The observer reads world and agent state from existing fields; it does not write to the agent's state or modify any observer already in the stack.

**The parallel-observer preservation property extends to a sixth layer.** With `--no-prediction-error`, the v1.5 batch runner produces output byte-identical to the v1.4 baseline at matched seeds on all v1.4 metrics. The prediction-error observer is the only addition.

### 2.6 The parallel-observer stack extended to six layers

Six parallel observers run alongside the agent: the v1.0 recorder, the v1.1 provenance store, the v1.2/v1.3 schema observer, the v1.3 family observer, the v1.4 comparison observer, and the v1.5 prediction-error observer. The prediction-error observer reads from agent state and world state directly during the run; it does not modify or read from any other observer's internal state during the run. At `on_run_end`, it reads the family observer's summary metrics solely to cross-check family attractor mastery steps against its own live-state records, as a consistency verification.

---

## 3. Experimental matrix and matched-seed comparison

The experimental matrix matches v1.4: one architecture (v1.5) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with four run lengths (20,000, 80,000, 160,000, 320,000 steps) crossed with ten runs per cell, totalling 240 runs. Seeds loaded from `run_data_v1_4.csv`.

With `--no-prediction-error`, the v1.5 batch runner produces output byte-identical to the v1.4 baseline at matched seeds on all v1.4 metrics. Category α is operationalised as the level-6 `--no-prediction-error` regression test.

---

## 4. Pre-flight verifications

Six verification levels are required before the v1.5 batch runs:

**Levels 1–5:** Inherited from the v1.4 pipeline unchanged. Level 5 remains the permanent `--no-comparison` regression test against the v1.3.2 baseline.

**Level 6 (v1.4 baseline, prediction-error observer disabled).** With `--no-prediction-error` only, output matches the v1.4 baseline byte-for-byte on all v1.4 metrics. 10 runs at cost 1.0, 20,000 steps, using seeds from `run_data_v1_4.csv`. This is the permanent level-6 regression test added to the pipeline by v1.5.

All six verifications are pre-conditions for the v1.5 batch.

---

## 5. Metrics

All v1.4 metrics are retained unchanged. The following metrics are added for v1.5:

**Per-encounter prediction-error records.** Written to `prediction_error_v1_5.csv`: one row per approach event per hazard cell per run, with fields as specified in Section 2.3.

**Per-run prediction-error summary fields.** Added to `run_data_v1_5.csv`: `yellow_pre_transition_entries`, `green_pre_transition_entries`, `unaffiliated_pre_transition_entries`, `yellow_resolution_window`, `green_resolution_window`, `total_prediction_error_events`, `prediction_error_complete`, as specified in Section 2.4.

**Distribution summaries.** Per (cost, run length) cell: mean, standard deviation, minimum, and maximum of `yellow_resolution_window` and `green_resolution_window` across all runs where the field is non-None. These are the Category γ substrate for the resolution-window finding.

---

## 6. Pre-registered interpretation categories

Six interpretation categories are pre-registered.

### 6.1 Category α: Preservation of v1.4 architecture under v1.5 extension

With `--no-prediction-error`, the v1.5 batch runner produces output byte-identical to the v1.4 baseline at matched seeds on all v1.4 metrics. Category α succeeds if all six pre-flight verifications pass.

### 6.2 Category β: Per-encounter records are internally consistent

The per-encounter records in `prediction_error_v1_5.csv` should be internally consistent across all 240 runs:

- For every run, the `yellow_pre_transition_entries` and `green_pre_transition_entries` summary fields must match the count of pre-transition approach records in `prediction_error_v1_5.csv` for that run at the respective cell.
- The `yellow_pre_transition_entries` per-run distribution must match the `pre_transition_entries_per_cell` (5,8) values in `run_data_v1_4.csv` at matched seeds, since no architectural change affects agent behaviour.
- Every encounter record where `encounter_type = resolved_surprise` must have a non-None `transformed_at_step` and a positive `resolution_window`.
- Every encounter record where `encounter_type = unresolved_approach` must have `transformed_at_step = None` and `resolution_window = None`.
- Every encounter record where `encounter_type = clean_first_entry` must have `precondition_met = True`.
- `prediction_error_complete` must be `True` in all runs where `total_prediction_error_events > 0`.

Category β succeeds if all six conditions hold across all 240 runs.

### 6.3 Category γ: Resolution window as a quantitative finding

The primary substantive finding of the iteration. The resolution window — `transformed_at_step − first_approach_step` for family hazard cells — is the gap between the agent's first structural mismatch and its eventual resolution. The pre-registered expectations, grounded in the v1.4 data:

**Component 1: Yellow resolution window distribution.** At 320k, 36 of 60 runs show at least one yellow pre-transition approach (v1.4 data: mean 1.417, max 3). All 60 runs complete the yellow transformation at 320k (0 unresolved approaches in the v1.4 batch at this run length). The yellow resolution window at 320k is therefore a distribution of 36 non-None values — all resolved surprises. The pre-registered expectation: the distribution is wide relative to the green resolution window, reflecting the architectural fact that agents typically arrive at the yellow pyramid (the higher-cost family cell) earlier in their developmental trajectory than they have the resources to unlock it. The expected direction: `mean(yellow_resolution_window) > mean(green_resolution_window)` at 320k.

**Component 2: Green resolution window distribution.** At 320k, a smaller number of runs show green pre-transition approaches (v1.4 data: mean 0.233, max 3). The pre-registered expectation: the green resolution window is present but narrower than the yellow, consistent with the 51/60 green-first mastery ordering — agents arrive at the green sphere with the yellow pyramid's structural lesson partially incorporated.

**Component 3: Encounter-type distribution across run lengths.** The proportion of resolved surprises, unresolved approaches, and clean first entries is expected to vary systematically with run length. At short run lengths (20k), unresolved approaches should constitute a non-trivial fraction of yellow pre-transition encounters — agents that approach the yellow pyramid before attractor mastery and do not complete the transformation within the run window. At longer run lengths, the unresolved proportion should decline toward zero as the run window is sufficient for resolution. The pre-registered expectation: unresolved approaches are present at 20k, substantially reduced at 80k, and near zero at 320k.

**Component 4: Unaffiliated cell prediction-error records.** The three unaffiliated hazard cells — (5,9), (6,8), (14,13) — use the global competency gate. Pre-transition entries for these cells (v1.4 data: mean 0.539 per cell at 320k, total across all three) are expected to produce per-encounter records with `family = None`. The encounter-type distribution for unaffiliated cells is expected to differ from family cells: the global competency gate is less specific than the family-specific gate, and the structural mismatch for unaffiliated cells does not carry the same developmental meaning. This comparison is reported as an exploratory finding, not a confirmatory one.

Category γ succeeds if Component 1 shows a non-degenerate yellow resolution window distribution at 320k, Component 2 shows a narrower green distribution in the anticipated direction, and Component 3 shows the expected run-length dependence of encounter-type proportions.

### 6.4 Category δ: Pre-anticipated findings

Two findings are anticipated and committed to honest reporting.

**Zero unresolved yellow approaches at 320k.** The v1.4 data confirms that the yellow transformation completes in all 60 runs at 320k. The prediction-error observer will therefore find zero unresolved approach records for the yellow pyramid at 320k — every pre-transition entry is either a resolved surprise (if followed by transformation within the run) or a clean first entry (if the precondition was met before the approach). This is not a failure of the prediction-error observer; it is the expected consequence of a sufficient run window. The 20k and 80k run lengths are where unresolved approaches are expected to appear.

**Pre-transition entry counts match v1.4 at matched seeds.** Since the prediction-error observer introduces no behavioural change, the `yellow_pre_transition_entries` and `green_pre_transition_entries` fields in `run_data_v1_5.csv` must match the corresponding `pre_transition_entries_per_cell` values in `run_data_v1_4.csv` exactly at matched seeds. This is both an internal-consistency requirement (Category β) and a pre-anticipated finding: the v1.5 extension adds interpretive structure to a signal that already existed in the v1.4 data. It does not generate new events — it classifies events that were already occurring.

### 6.5 Category Φ: Honesty constraint on the prediction-error claim

The prediction-error observer records structural mismatch between what the agent's action produced and what the architecture's structural rule would have produced if the precondition had been met. This is not the same as the agent experiencing surprise. The agent does not have an expectation model that is violated; it has a value function that is updated by the discrepancy between predicted and received reward. The prediction-error record is an external characterisation of a structural gap in the agent's developmental trajectory — not a first-person account of failed prediction.

The honest claim v1.5 supports: the architecture now holds a per-encounter record from which the gap between structural mismatch and resolution can be measured. The architecture can identify where surprises occurred in the developmental record, whether they were resolved, and at what cost. This is the raw material SICC Commitment 8 requires — self-knowledge as derivative of object-knowledge — but it is not yet self-knowledge. The agent does not read these records. The reading layer is v1.6.

Both readings — the architecture records structural mismatch, versus the agent experiences prediction error — are consistent with the v1.5 batch data. The reporting iteration is the methodological vehicle for distinguishing them.

### 6.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and γ all pass.

The claim: pre-transition approach events in the prepared environment constitute a structurally meaningful class of encounter that can be characterised, counted, typed, and temporally bounded. The prediction-error observer, reading from agent state and world state during the run, produces per-encounter records that are internally consistent, architecturally complete, and individually variable in ways that reflect each agent's developmental trajectory. The architecture now holds, for the first time, a record that distinguishes between three qualitatively different kinds of encounter with a hazard cell — the agent that arrived too early and had to return, the agent that arrived too early and ran out of time, and the agent that arrived exactly when the developmental conditions were in place — and can measure the gap between the first kind and the transformation that resolved it.

The deeper claim, reserved for v1.6: when the agent is eventually given access to this record, it should be able to say not just what it learned but where it was surprised, and whether the surprise was resolved. The resolution window is the measure that makes that statement precise. The v1.5 observer builds the record. The v1.6 reporting layer builds the reading.

---

## 7. Connection to the SICC trajectory

v1.5 advances the SICC trajectory on one commitment.

**Commitment 7 (prediction-error as learning signal)** is advanced at the per-encounter record layer. The v1.4 iteration established that the structural similarity between families is detectable from the architecture's own records. The v1.5 iteration establishes that developmental mismatch — the gap between what the agent's action produced and what the architecture's structural rule would have produced — is detectable at per-encounter resolution, classifiable by type, and temporally bounded by the resolution window. This is prediction-error elevated from a count in a summary field to a first-class record in its own output file.

The commitments not yet advanced by v1.5 — self-knowledge as derivative of object-knowledge (Commitment 8), auditable reporting (Commitment 11) — remain reserved. v1.5 extends the substrate; the substrate now includes a prediction-error record (v1.5). The first time the agent speaks, at v1.6, it speaks from the richest possible record of its own developmental history.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.5 implementation work begins.

**Matched-seed comparison.** Seeds loaded from `run_data_v1_4.csv` at every (cost, run length, run index) cell.

**Pre-flight verifications.** All six levels pass before the full v1.5 batch runs.

**Single-architectural-change discipline.** v1.5 introduces the prediction-error observer as the singular architectural extension. The parallel-observer pattern is preserved for a sixth layer.

**Amendment policy.** Three amendments available. One amendment is provisionally reserved for the encounter-type classification boundary: the distinction between `resolved_surprise` and `clean_first_entry` depends on whether the precondition is assessed at the step of entry or at the step of transformation. If the boundary requires sharpening after the observer is implemented, an amendment will record the resolution. Two further amendments are available for unanticipated operational issues.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before any v1.5 code is written.

---

## 9. Stopping rule

The v1.5 iteration completes when:

- All six pre-flight verifications pass.
- The full 240-run batch has run.
- Categories α, β, γ, δ, Φ, and Ω have been characterised in the v1.5 paper.
- The v1.5 paper is drafted.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve.

---

## 10. References

Baker, N.P.M. (2026a–v) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.2. Full reference list inherited from v1.3 paper.

Baker, N.P.M. (2026w) 'v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026x) 'v1.3.1 Pre-Registration Amendment', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026y) 'v1.3.2 Pre-Registration Amendment: Family-Specific Competency Gating', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026z) 'Relational Property Families in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026aa) 'v1.4 Pre-Registration: Cross-Family Structural Comparison via Parallel Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026ab) 'Cross-Family Structural Comparison in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before any v1.5 code is written.
