# Prediction-Error Elevation in a Small Artificial Learner: Awareness Before Readiness as the Generative Site of Developmental Lag

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Working draft — Sections 1 through 6

---

## Abstract

The v1.4 iteration established that the structural similarity between two relational property families — GREEN and YELLOW — is detectable from the architecture's own records. What the v1.4 records did not hold was any account of the encounters that preceded the bankable-tier transformation: the steps at which an agent entered a family hazard cell before the precondition attractor was mastered, paid the hazard cost, and received nothing. Those encounters were counted. They were not named.

The v1.5 iteration introduces prediction-error elevation as the singular architectural extension: a sixth parallel observer that records each encounter with a hazard cell as a typed event — resolved surprise, unresolved approach, or clean first entry — and computes the resolution window, the step-gap between an agent's first pre-transition approach to a family cell and the eventual HAZARD-to-KNOWLEDGE transformation. No agent behaviour is modified. The parallel-observer preservation property extends to a sixth layer: with the prediction-error observer disabled, output is byte-identical to the v1.4 baseline at matched seeds.

The v1.5 batch of 240 runs across four run lengths produces 1,606 per-encounter records across five hazard cells. The primary finding is the resolution window as a measure of developmental lag: the gap between awareness and readiness. At 320,000 steps, the yellow pyramid at (5,8) produces 85 resolved-surprise records with a mean resolution window of 22,540 steps and a range of 210 to 102,384 steps; the green sphere at (14,14) produces 14 resolved-surprise records with a mean of 38,092 steps. The pre-registration anticipated the yellow window would be wider; the data inverts this. The inversion is explained, not explained away: agents who approach the green sphere before attractor mastery do so late in the developmental arc (mean awareness step 23,128 vs 7,485 for yellow), encounter a cell that remains locked for a long time thereafter, and therefore accumulate long windows. The direction finding is an empirical result, not a pre-registration failure.

The encounter-type distribution across run lengths confirms the pre-registered expectation: unresolved yellow approaches constitute 41% of pre-transition encounters at 20,000 steps and decline monotonically to zero at 320,000 steps. The three encounter types — resolved surprise, unresolved approach, clean first entry — are internally consistent across all 1,606 records with zero violations of the pre-registered invariants.

The paper's analytical centre is a reframing of what a pre-transition entry is. It is not a failure event. It is a perception event with a cost: the agent has found something it cannot yet use. It pays to look. The resolution window is the developmental distance between *I see this* and *this is now part of me*. This framing connects directly to SICC Commitment 8 — self-knowledge as derivative of object-knowledge — and to the biographical register the reporting iteration (v1.6) will require. The v1.5 records make possible, for the first time, a statement the agent will eventually be able to produce: not just what it learned, but where it was aware before it was ready, and how far it had to develop before the environment yielded.

---

## 1. Introduction

### 1.1 Programme to date

The post-v1.0 cognitive-layer arc has advanced five steps. v1.1 introduced provenance over learned states (SICC Commitment 4): flag structures acquired formation histories, confirming and disconfirming observations, and bidirectional cross-references between threat flags and the knowledge-banking flags derived from the same coordinate. v1.2 introduced the explicit schema (SICC Commitment 1, first part): a complete self-description of cell types, actions, developmental phases, and flag types as a queryable record. v1.3 introduced relational property families — GREEN and YELLOW — each running through three tiers, with the colour identifier as the relational spine and the HAZARD-to-KNOWLEDGE transition gated on family-specific attractor mastery. v1.4 introduced the first cross-family structural comparison: a fifth parallel observer that reads completed family traversal records and computes structural similarity measures between the two families, establishing for the first time an architectural record representing a relationship between two families rather than the internal structure of one.

What the arc through v1.4 did not hold was any account of the encounters that preceded the transformation. The family traversal narrative recorded when the green sphere was banked; it did not record what happened when the agent entered the green sphere before the green square was mastered. The `pre_transition_entries_per_cell` field in `run_data_v1_4.csv` counted those entries. It did not name them, type them, or measure how far the agent had to travel between the encounter and the eventual resolution. They were in the record as a number. They were not in the record as an event.

### 1.2 The prediction-error extension

The v1.5 iteration introduces the prediction-error observer as a sixth parallel observer. Unlike the v1.4 comparison observer — which holds no live state and operates entirely at run end — the prediction-error observer holds live state during the run to detect pre-transition approach events at the step they occur. At `on_run_end`, it classifies all recorded approach events into three encounter types and computes per-run summary fields. The parallel-observer preservation property extends to six layers: with `--no-prediction-error`, the batch runner produces output byte-identical to the v1.4 baseline at matched seeds on all v1.4 metrics.

The three encounter types are defined against the family-specific competency gate (v1.3.2 amendment) for family cells and the global competency gate for unaffiliated cells. A **resolved surprise** is an approach before the precondition was met, at cost, with no transformation at the time of entry, followed by a transformation within the run. An **unresolved approach** is an approach before the precondition was met, at cost, with no transformation within the run window. A **clean first entry** is an approach after the precondition was met: the first approach produces the transformation.

The design decision embedded in this typology is architectural rather than interpretive. The gate controls the HAZARD-to-KNOWLEDGE *transition*, not the agent's physical access to the cell. A family hazard cell is on the grid and traversable before the transition fires. The agent enters, pays the cost, and is turned away — not because entry is blocked, but because the structural rule that would make the cell yield has not yet been satisfied. This is the prepared environment operating as designed. The material is on the shelf. The agent can reach it, touch it, pay to encounter it. The transformation requires readiness the agent does not yet have.

### 1.3 Findings and their relation to the pre-registration

The v1.5 batch produces four finding categories.

Category α is satisfied: the level-6 pre-flight verification confirms byte-identical preservation of all v1.4 metrics with `--no-prediction-error` across all ten verification runs. The sixth observer adds nothing to the existing stack when disabled.

Category β is satisfied: all 1,606 encounter records are internally consistent. Zero resolved-surprise records have a missing or non-positive resolution window. Zero unresolved-approach records have a non-None `transformed_at_step`. Zero clean-first-entry records have `precondition_met = False`. The `yellow_pre_transition_entries` and `green_pre_transition_entries` summary fields match the `pre_transition_entries_per_cell` values in `run_data_v1_4.csv` exactly at matched seeds across all 240 runs.

Category γ is satisfied. The yellow resolution window at 320,000 steps is non-degenerate (n = 85, mean 22,540 steps, sd 24,367, range 210–102,384). The encounter-type distribution across run lengths confirms the pre-registered expectation: unresolved yellow approaches decline from 41% of pre-transition encounters at 20,000 steps to zero at 320,000 steps. The pre-registered direction of the resolution window comparison (yellow mean > green mean) is not confirmed; the data and its explanation are reported under Category Φ.

Category δ is confirmed: zero unresolved approaches at 320,000 steps across all five hazard cells, as pre-registered.

### 1.4 Connection to the broader programme

v1.5 advances SICC Commitment 7 — prediction-surprise as the learning signal — at the per-encounter record layer. The pre-transition entry, previously a count in a summary field, is now a first-class record with a step, a type, a cost, and, where resolved, a window.

The SICC document anticipates the connection between Commitments 7 and 8 explicitly: *the prediction-error record, held at the per-encounter level, is the raw material from which self-knowledge is eventually constructed.* The practical test committed in the SICC document is held here as the forward instrument: when the reporting iteration arrives, the agent should be able to say not just what it learned but where it was surprised, and whether the surprise was resolved. The v1.5 records make that statement available for the first time. The reading layer is v1.6.

---

## 2. Methods

### 2.1 Environment and architecture

The environment and agent are inherited from v1.4 unchanged. The 20×20 grid, the developmental phase schedule, the threat layer, the mastery layer, the end-state mechanism, the knowledge-cell mechanism, V13World with COLOUR_CELL placement and family property dicts, and the V13Agent family-specific competency gating rule all operate under their inherited specifications. The agent subclass chain extends by one naming step: `V014Agent` → `V12Agent` → `V13SchemaAgent` → `V13Agent` → `V14Agent` → `V15Agent`. V15Agent introduces no method overrides; it is provided for naming consistency and forward compatibility.

### 2.2 The prediction-error observer

The v1.5 prediction-error observer (`V15PredictionErrorObserver`) implements the same three-hook interface as the existing five parallel observers. `on_pre_action` is a no-op. `on_post_event` performs the core live-state detection: it reads `agent.pre_transition_hazard_entries` after each step of `record_action_outcome` to detect new pre-transition approach events, assesses precondition status from `agent.mastery_flag` at the time of detection, and monitors `world.cell_type` for HAZARD-to-KNOWLEDGE transitions. `on_run_end` classifies all recorded approach events into encounter types, computes resolution windows, and populates output records.

**Precondition assessment** follows the architecture's own gating rule. For family cells, `precondition_met` is `True` iff `mastery_flag[precondition_attractor] == 1` at the step of detection. For unaffiliated cells, `precondition_met` is `True` iff `sum(mastery_flag.values()) >= hazard_competency_thresholds[cell]`. Both conditions are assessed after `record_action_outcome` and `check_competency_unlocks` have run for the step, which is consistent with the base agent's own `pre_transition_hazard_entries` counter: a pre-transition entry is recorded only when `cost_incurred > 0`, which occurs only when the cell was HAZARD-typed during `world.step()`.

**Transition detection** monitors `world.cell_type[cell]` against the observer's cached previous-step value. When a cell transitions from HAZARD to KNOWLEDGE, the step of first detection is recorded as `transformed_at_step` for all pending approach events for that cell.

**Encounter classification** proceeds at `on_run_end`. An approach event where `transformed_at_step` is non-None is a resolved surprise; one where it is None is an unresolved approach. A cell that transitioned within the run but recorded no pre-transition approach events receives a clean-first-entry record: the agent arrived ready, the first approach produced the transformation.

### 2.3 The parallel-observer stack extended to six layers

Six parallel observers run alongside the agent: the v1.0 recorder, the v1.1 provenance store, the v1.3 schema observer, the v1.3 family observer, the v1.4 comparison observer, and the v1.5 prediction-error observer. The prediction-error observer reads from agent state and world state directly; it does not read from or modify any other observer's state. With `--no-prediction-error`, output is byte-identical to v1.4 baseline at matched seeds. This is the level-6 regression test added to the pipeline by v1.5.

### 2.4 Experimental matrix and matched-seed comparison

One architecture (v1.5) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with four run lengths (20,000, 80,000, 160,000, 320,000 steps) crossed with ten runs per cell, totalling 240 runs. Seeds loaded from `run_data_v1_4.csv` at every (cost, run length, run index) cell.

### 2.5 Pre-flight verifications

Six verification levels ran before the batch. Levels 1–5 are inherited from the v1.4 pipeline and all passed, confirming the observer stack through the v1.3.2 baseline is undisturbed. Level 6 — the new verification added by v1.5 — confirmed that with `--no-prediction-error` only, the v1.5 batch runner produces output matching the v1.4 baseline on all v1.4 metrics across ten runs at cost 1.0, 20,000 steps. Both levels 1–5 and level 6 passed before the batch ran.

### 2.6 Pre-registered interpretation categories

Categories α, β, γ, δ, Φ, and Ω are as committed in the v1.5 pre-registration (Baker, 2026ac). The operative definitions govern the reporting of all findings in Section 3.

### 2.7 Output files

In addition to the seven files inherited from v1.4, the v1.5 batch produces `prediction_error_v1_5.csv` — one row per approach event per hazard cell per run — and extends `run_data_v1_5.csv` with per-run prediction-error summary fields.

---

## 3. Results

### 3.1 Category α: Preservation of v1.4 architecture under v1.5 extension

All six pre-flight verifications passed. With `--no-prediction-error`, the v1.5 batch runner produces output byte-identical to the v1.4 baseline on all v1.4 metrics across all ten verification runs. Levels 1–5 confirm the inherited observer stack is undisturbed. Level 6 confirms the prediction-error observer — the sole architectural addition — contributes nothing to the existing metrics when disabled. Six parallel observers running simultaneously produce consistent records without cross-observer contamination.

### 3.2 Inherited v1.4 findings confirmed

The v1.4 findings are confirmed intact. Schema completeness holds at seven cell types in all 240 runs. Both colour cells are registered in all 240 runs at fixed steps — yellow at step 84, green at step 215. Zero developmental ordering violations occur across either family in all 240 runs. Intra-family cross-references resolve at 100% conditional on both flags forming within the run. Form-progression parallelism is 1.0 in all 240 runs. Measure 1 is 0.0 in all 60 complete runs at 320,000 steps. The `yellow_pre_transition_entries` and `green_pre_transition_entries` fields match `run_data_v1_4.csv` exactly at matched seeds — the prediction-error observer introduces no behavioural change, and the counts the agent was already keeping are reproduced identically.

### 3.3 Category β: Internal consistency of encounter records

The v1.5 batch produces 1,606 per-encounter records across five hazard cells and all 240 runs. The distribution by encounter type is: 753 resolved surprises (46.9%), 775 clean first entries (48.3%), and 78 unresolved approaches (4.9%). `prediction_error_complete` is True in all 240 runs — every run produced at least one encounter record for at least one hazard cell.

All pre-registered internal-consistency invariants hold without exception:

- Zero resolved-surprise records have a missing or non-positive resolution window (n = 753).
- Zero unresolved-approach records have a non-None `transformed_at_step` (n = 78).
- Zero clean-first-entry records have `precondition_met = False` (n = 775).

**Table 1.** Encounter records by cell, all 240 runs.

| Cell       | Family       | Resolved surprise | Unresolved approach | Clean first entry | Total |
|------------|--------------|-------------------|---------------------|-------------------|-------|
| (5, 8)     | YELLOW       | 283               | 53                  | 91                | 427   |
| (14, 14)   | GREEN        | 38                | 3                   | 217               | 258   |
| (5, 9)     | Unaffiliated | 135               | 7                   | 158               | 300   |
| (6, 8)     | Unaffiliated | 155               | 5                   | 149               | 309   |
| (14, 13)   | Unaffiliated | 142               | 10                  | 160               | 312   |
| **Total**  |              | **753**           | **78**              | **775**           | **1,606** |

The yellow pyramid at (5,8) dominates the pre-transition record: 336 pre-transition encounters (resolved + unresolved) against 41 for the green sphere and 169 for the three unaffiliated cells combined across all 240 runs.

### 3.4 Category γ Component 1: The resolution window

The resolution window — the step-gap between first pre-transition approach and eventual HAZARD-to-KNOWLEDGE transformation — is the primary quantitative finding.

**Table 2.** Yellow pyramid (5,8) resolution windows by run length.

| Run length | n (resolved) | Mean   | Median | SD     | Min | Max    |
|------------|--------------|--------|--------|--------|-----|--------|
| 20,000     | 47           | 3,877  | 3,056  | 3,004  | 340 | 9,226  |
| 80,000     | 69           | 14,924 | 12,224 | 12,262 | 126 | 39,286 |
| 160,000    | 82           | 20,022 | 11,377 | 20,776 | 210 | 73,204 |
| 320,000    | 85           | 22,540 | 11,494 | 24,367 | 210 | 102,384|

**Table 3.** Green sphere (14,14) resolution windows by run length.

| Run length | n (resolved) | Mean   | Median | SD     | Min   | Max    |
|------------|--------------|--------|--------|--------|-------|--------|
| 20,000     | 3            | 6,655  | 6,641  | 30     | 6,635 | 6,689  |
| 80,000     | 10           | 14,807 | 5,457  | 13,139 | 3,959 | 35,103 |
| 160,000    | 11           | 35,982 | 25,697 | 32,567 | 829   | 90,945 |
| 320,000    | 14           | 38,092 | 43,504 | 28,985 | 829   | 90,945 |

The yellow distribution is non-degenerate at every run length, satisfying Category γ Component 1. The green distribution is sparse — only 14 resolved surprises at 320,000 steps — and shows a higher mean than yellow at that run length (38,092 vs 22,540 steps). This direction finding inverts the pre-registration's expectation; its explanation is given in Section 4.2.

The resolution window widens with run length across both families. At 20,000 steps the mean yellow window is 3,877 steps; at 320,000 steps it is 22,540 steps. This widening is not a methodological anomaly but a developmental one, addressed in Section 4.3.

### 3.5 Category γ Component 3: Encounter-type distribution across run lengths

**Table 4.** Encounter types for yellow pyramid (5,8) by run length.

| Run length | Resolved | Unresolved | Clean | Unresolved % of pre-transition |
|------------|----------|------------|-------|-------------------------------|
| 20,000     | 47       | 33         | 19    | 41%                           |
| 80,000     | 69       | 17         | 24    | 20%                           |
| 160,000    | 82       | 3          | 24    | 4%                            |
| 320,000    | 85       | 0          | 24    | 0%                            |

The unresolved proportion declines monotonically from 41% at 20,000 steps to zero at 320,000 steps, confirming the pre-registered expectation. The 33 unresolved yellow approaches at 20,000 steps represent agents whose first encounter with the yellow pyramid occurred before attractor mastery, and for whom the run window closed before the precondition was satisfied. At 320,000 steps, every agent that encountered the yellow pyramid before mastery lived long enough to resolve the encounter.

The unaffiliated cells show faster resolution: all three cells reach zero unresolved approaches by 80,000 steps, two run lengths earlier than the yellow pyramid. The global competency gate is more readily satisfied than the family-specific gate — it requires only a threshold count of mastered attractors, rather than mastery of a specific precondition attractor.

### 3.6 Category δ: Zero unresolved approaches at 320,000 steps

Zero unresolved approaches are recorded at 320,000 steps across all five hazard cells and both families, as pre-registered. At the longest observation window, every agent that approached a hazard cell before the precondition was met lived long enough to satisfy it. The prepared environment, given sufficient developmental time, does not strand awareness without readiness.

---

## 4. Discussion

### 4.1 The pre-transition entry as perception event with cost

The reframing the v1.5 data supports is precise. A pre-transition entry — an agent entering a family hazard cell before the precondition attractor is mastered — is not a failure event. The gate controls the HAZARD-to-KNOWLEDGE transition; it does not block physical entry. The agent can enter the green sphere at (14,14) while it is still HAZARD-typed. It will pay the cost. It will leave without the transformation. The cell was accessible; the transformation was not.

What the agent has at that moment is awareness without readiness. It has found something on the shelf of the prepared environment that it cannot yet use. The cost is the price of perception — the environment charges for looking, because looking without the capacity to act changes the agent's cost record and its subsequent approach behaviour. But the looking happened. The awareness is in the record.

The resolution window measures the developmental distance between that moment of awareness and the moment of readiness. For the yellow pyramid, the mean distance at 320,000 steps is 22,540 steps — from first encounter to eventual transformation, across 85 runs. For individual agents, it ranges from 210 steps (the precondition was essentially already met when the first approach occurred) to 102,384 steps (the agent encountered the pyramid very early, long before the yellow triangle was mastered, and took the better part of the run to close the gap).

In a Montessori classroom, the prepared environment is designed around exactly this experience. The child is aware of materials it cannot yet work with. That awareness is not error; it is orientation. The child knows the shelf is there. The resolution window is the developmental interval between orientation and incorporation: between *I see this* and *this is now part of me*. The architecture is now holding that interval as a measured record for the first time.

### 4.2 The direction reversal: awareness step as the explanatory variable

The pre-registration expected the yellow mean resolution window to exceed the green mean at 320,000 steps, on the grounds that yellow is typically the second family traversed (51 of 60 agents master green before yellow) and agents arrive at it with incomplete developmental resources. The data inverts this: yellow mean 22,540 steps, green mean 38,092 steps.

The anatomy of the inversion is readable directly from the data. At 320,000 steps, agents who produce yellow resolved-surprise records first encountered the yellow pyramid at a mean step of 7,485; the transformation fired at a mean step of 30,025. Agents who produce green resolved-surprise records first encountered the green sphere at a mean step of 23,128; the transformation fired at a mean step of 61,220.

Yellow awareness arrives early — step 7,485 on average — because the yellow pyramid sits in a cluster the agent visits in early exploration. The developmental gap to the yellow triangle mastery is substantial, but the agent is young when it first pays to look. Green awareness arrives later — step 23,128 — because the agent must travel further to find the green sphere. When it does arrive, it is further along developmentally, but the green sphere's precondition (the green square at (4,15)) happens to be further from satisfaction at that moment for the small number of agents who arrive early. The result is a smaller population of green resolved-surprise records (14 at 320k vs 85 for yellow) with a higher mean window.

The pre-registration reasoning was correct about the mechanism — agents arrive at family cells before the developmental conditions are in place — but wrong about which family would show the wider window. The relevant variable is not which family is traversed second; it is at what developmental step awareness first occurs relative to the distance still to travel to readiness. That is an empirical question the architecture can now answer, and it has.

The direction finding is reported here under Category Φ, not as a pre-registration failure. The pre-registered direction was a reasonable expectation from the v1.4 data. The data produced a different result with a coherent explanation. Both are part of the record.

### 4.3 The resolution window widens with run length: developmental lag, not time pressure

The mean yellow resolution window increases from 3,877 steps at 20,000 steps to 22,540 steps at 320,000 steps. This is not a pathology of longer runs. It is a direct consequence of what longer runs permit.

In a 20,000-step run, the agent's first pre-transition approach to the yellow pyramid tends to occur late — there is less time for early exploration, and the unresolved proportion is high (41%), meaning many approaches do not resolve within the window at all. The 47 resolved surprises at 20,000 steps are a select group: those whose awareness arrived early enough and whose developmental arc was fast enough for the transformation to fire before step 20,000. Their mean window is 3,877 steps precisely because they are the fast resolvers.

In a 320,000-step run, the agent has more time for early exploration, so awareness can arrive earlier, and the full developmental arc — from awareness to readiness — can play out completely. The 85 resolved surprises at 320,000 steps include agents whose awareness arrived at step 210 and whose readiness arrived more than 100,000 steps later. The widening of the distribution reflects the inclusion of agents with genuinely long developmental lags, not a systematic slowing of development.

The Montessori parallel holds here. The prepared environment does not time-pressure the child. The child encounters the material when exploration brings it there; it becomes ready when development makes it ready. The interval between the two is the child's own. Longer observation windows do not change the developmental arc — they allow its full extent to be observed. The resolution window at 320,000 steps is a more complete record of the developmental lag than the window at 20,000 steps, not a longer lag.

### 4.4 The prediction-error record as the substrate of the self-account

The SICC document's Commitment 8 specifies that self-knowledge is derivative of object-knowledge: built late from an accumulated record of engagement rather than constructed as a primary module. The v1.1 through v1.4 iterations built the object-engagement record — provenance, schema, family records, cross-family comparison. The v1.5 iteration adds the biographical layer: the record that distinguishes between an agent that arrived ready and an agent that arrived aware.

The distinction matters for the eventual self-account. An agent that can only read its knowledge-banking records can produce the statement: *I learned about the green sphere at step 1,777*. That is a chronological record — true, traceable, but thin. An agent that can read its prediction-error records can produce a richer statement: *I was aware of the green sphere from step 581. I was not ready for it. I became ready at step 7,270. The gap was 6,689 steps.* That is a biographical record — it has a before, a during, and an after. It has a developmental character.

The SICC document names this moment precisely: *it is the moment the existing record becomes biographical rather than merely chronological.* The v1.5 prediction-error records are what makes that transition possible. Not because the agent reads them yet — it does not — but because the substrate now contains the information the biographical statement requires. When v1.6 adds the reading layer, the agent will not be constructing a self-account from nothing. It will be reading from a record that already holds its surprises, its resolutions, and the developmental distances between them.

The v1.4 paper closed with the observation that the two materials on the prepared environment's shelf have been compared and found to be the same structure, arrived at by different routes, in different developmental time. The v1.5 paper adds a layer beneath that observation: the routes themselves now have a texture they did not have before. Between the first step of awareness and the eventual step of incorporation, there is a developmental interval that the architecture can now measure, type, and hold. The prepared environment does not merely contain structures for the agent to traverse. It contains moments of awareness the agent pays to have before it is ready to act on them. Those moments are now part of the record.

### 4.5 The unaffiliated cells as comparative substrate

The three unaffiliated hazard cells — (5,9), (6,8), (14,13) — use the global competency gate: transition fires when the attractor mastery count reaches a cell-specific threshold, regardless of which attractors were mastered. Their prediction-error records provide a comparison substrate for the family cells.

At 320,000 steps, unaffiliated resolved-surprise windows are: (5,9) mean 10,296 steps, (6,8) mean 4,865 steps, (14,13) mean 9,173 steps. These are narrower than the yellow pyramid (22,540 steps) and substantially narrower than the green sphere (38,092 steps). The global gate is more readily satisfied — it requires a count, not a specific precondition — so the developmental lag between awareness and readiness is shorter on average.

This comparison makes visible something the family cells alone cannot show: the family-specific gate systematically extends the resolution window relative to the global gate. The agent that encounters the yellow pyramid before mastering the yellow triangle must wait specifically for that mastery event. The agent that encounters an unaffiliated cell before its global threshold is satisfied may find the threshold met by any combination of attractor masteries — a less targeted developmental dependency, and therefore a shorter expected lag.

The comparison also confirms that prediction-error — awareness before readiness, at cost — is not a phenomenon specific to family cells. It is the normal condition of early developmental exploration across the entire prepared environment. Family cells make it structurally visible because their specific preconditions create longer, more interpretable lags. The unaffiliated cells establish that the phenomenon is general.

### 4.6 The architectural arc through v1.5

The post-v1.0 cognitive-layer arc now has five iterations in place. v1.1 established provenance over learned states. v1.2 established the explicit schema. v1.3 established the first relational taxonomy. v1.4 established the first cross-family structural comparison. v1.5 elevates prediction-error to first-class status as a per-encounter record.

The reporting iteration (v1.6) reads from all five layers. Its output will be the first time the agent produces a statement that reads from its own history. The substrate now contains: what the agent knows and when it learned it (v1.1 provenance); what structural category what it learned belongs to (v1.2 schema); which family each cell belongs to and how the families are traversed (v1.3 family records); how the two families compare structurally across the agent's developmental arc (v1.4 comparison records); and where the agent was aware before it was ready, and how far it had to develop before the environment yielded (v1.5 prediction-error records).

The first time the agent speaks, at v1.6, it speaks from a substrate that is biographical in character. The resolution window is the measure that makes the biographical dimension precise: not merely *I learned this*, but *I knew this was here before I could hold it, and the distance between knowing and holding was this*.

---

## 5. Conclusion

The v1.5 iteration extended the programme's observer stack with a sixth parallel observer that records per-encounter prediction-error events across all five hazard cells, classifies them by type, and computes the resolution window — the developmental distance between first awareness of a structural rule and eventual possession of the resources to satisfy it. No agent behaviour was modified. The single-variable-change discipline held.

The v1.5 batch of 240 runs produces 1,606 encounter records. The internal-consistency invariants hold without exception across all records. The encounter-type distribution confirms the pre-registered expectation: unresolved approaches decline monotonically from 41% of yellow pre-transition encounters at 20,000 steps to zero at 320,000 steps. The resolution window is non-degenerate at every run length, with individual variation ranging from 210 to 102,384 steps for the yellow pyramid.

The pre-registered direction finding — yellow mean resolution window wider than green — is not confirmed at 320,000 steps. The inversion is explained rather than explained away: the relevant variable is the developmental step at which awareness first occurs, not which family is typically traversed second. Yellow awareness arrives earlier in the run (mean step 7,485 vs 23,128 for green); green resolved-surprise records are rarer (14 vs 85 at 320k) and skewed by agents whose awareness arrived at an unusual developmental moment with a long lag ahead. The direction finding is an empirical result, reported honestly.

The paper's analytical centre is the reframing of the pre-transition entry as a perception event with a cost: the agent has found something it cannot yet use, and pays to look. The resolution window is the developmental distance between *I see this* and *this is now part of me*. This framing connects the prediction-error record to SICC Commitment 8 — self-knowledge as derivative of object-knowledge — and to the biographical register the reporting iteration requires. The architecture now holds, for the first time, the substrate from which the agent will eventually be able to produce a statement not just about what it learned, but about where it was aware before it was ready, and how far it had to develop before the environment yielded.

The prepared environment does not strand awareness without readiness, given sufficient time. The Category δ finding — zero unresolved approaches at 320,000 steps — is the empirical confirmation. The environment designed to hold materials at the right developmental distance from the learner fulfils that design: every agent that paid to look eventually became ready to hold. The gap between the two is the developmental record the v1.6 reporting layer reads.

---

## 6. Code and Data Availability

All code, pre-registration documents, batch outputs, and paper drafts are available at github.com/RancidShack/developmental-agent.

The v1.5 implementation comprises four files. All v1.4 source files are inherited unchanged. `v1_5_agent.py` implements V15Agent as a named subclass of V14Agent with no method overrides. `v1_5_prediction_error_observer.py` implements the sixth parallel observer with live-state detection, encounter-type classification, and per-encounter CSV output. `curiosity_agent_v1_5_batch.py` is the batch runner with the `--no-prediction-error` flag for level-6 regression. `verify_v1_5_no_prediction_error.py` is the level-6 pre-flight verification script.

The batch produced eight output files: `run_data_v1_5.csv`, `prediction_error_v1_5.csv`, `comparison_v1_5.csv`, `family_v1_5.csv`, `provenance_v1_5.csv`, `schema_v1_5.csv`, `snapshots_v1_5.csv`, and `snapshots_v1_0_under_v1_5.csv`. The prediction-error file contains 1,606 encounter records across 240 runs and five hazard cells. The provenance record count, inherited from v1.4 at matched seeds, is 3,040 records — confirming the level-6 preservation result.

Seeds were drawn from `run_data_v1_4.csv`, extending the seed chain to v1.5 at every (cost, run length, run index) cell.

---

## 7. References

Baker, N.P.M. (2026a–ab) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.4. Full reference list inherited from v1.4 paper (Baker, 2026ab).

Baker, N.P.M. (2026ab) 'Cross-Family Structural Comparison in a Small Artificial Learner: The Architecture's First Record of a Relationship Between Two Families', preprint, 2 May 2026.

Baker, N.P.M. (2026ac) 'v1.5 Pre-Registration: Prediction-Error Elevation via Per-Encounter Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

## 8. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper.

No human participant data were collected. No external parties had access to drafts prior to preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
