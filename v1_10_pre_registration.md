# v1.10 Pre-Registration: Belief Revision with Consequences and the Completion Signal

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.10 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

Ten iterations have built a developmental agent whose biographical register holds what it encountered and learned (Q1), how its knowledge is structured across families (Q2), where its expectations were violated (Q3), and where it approached without making contact (Q4). The register is auditable, individually variable, substrate-agnostic, and cumulative. It holds a record of intention (v1.8) and a record of restraint (v1.9).

What it does not yet hold is a record of revision. The agent was surprised by haz_yellow at step 493. The prediction-error substrate records this. The resolution window records how long it took. The Q3 statement describes the gap. But the record of the surprise is not consulted by the agent's subsequent behaviour. The surprise happened, was recorded, and changed nothing.

v1.10 changes that — and addresses a second architectural gap the v1.9 batch surfaced alongside it.

The v1.9 data showed that only 13 of 40 runs banked the end state, with `end_state_found_step` ranging from step 920 to step 310,156. The end-state cell exists in V17World and fires `activation_step` when the completion condition is met (all attractors mastered AND all hazards banked as knowledge). But the agent is not drawn to it — it finds the end-state cell opportunistically, as its path happens to pass nearby. The high-activity Phase 3 consolidation runs in the v1.9 batch — agents who achieved full attractor mastery and then generated 3,000–7,000 CF records orbiting hazard objects — are overwhelmingly runs in which the end state was never banked. The agent finished the developmental sequence and had nowhere purposeful to go.

This is the 3,3 rumination problem in its V17World form. In the grid environment it was solved by the wait-by-the-door cell: a designated completion point to which agents who had finished the material were drawn. The Montessori principle is exact: the directress arranges the prepared environment so that a completed learner has a purposeful terminus — not a constraint, but an affordance. The environment signals that this material is complete. Whether the learner moves to it, and when, is their choice. The signal is the directress's contribution; the timing is the learner's.

V1.10 introduces both architectural extensions together: the belief-revision layer (the record of being wrong and changing) and the completion signal (the prepared environment's invitation to a learner who has finished the material). They are introduced in the same iteration because they share a theoretical grounding — both are consequences of the Montessori principle that the prepared environment is not merely a space for free exploration but an architecture that actively supports the learner's developmental arc — and because both address surfaced gaps rather than speculative additions. The v1.9 data made both necessary.

The SICC through-line: v1.8 gave the agent a reason to learn; v1.9 gave it a record of choosing; v1.10 gives it a record of being wrong and changing, and gives the prepared environment its completion signal.

---

## 2. Architectural specification

### 2.1 The belief-revision layer

The belief-revision layer is implemented as `V110BeliefRevisionObserver`, the ninth parallel observer. It reads from the prediction-error substrate after each `resolved_surprise` event and fires a `revised_expectation` record. It maintains a per-object revised-expectation register that is consulted at each step by a preference-bias component. It does not modify the threat gate, competency layer, or any existing observer.

**Trigger.** A `revised_expectation` record fires when V15PredictionErrorObserver records a `resolved_surprise` event — the moment the agent has made contact with a hazard object before the precondition was met and the transformation has subsequently occurred. The trigger is resolution, not the surprise itself: the agent waited, the resolution arrived, and only then does it have both sides of the revision — what it believed before, and what the correct account is.

**What the belief-revision layer does not do.** It does not modify the agent's reward function, value function, or Q-table directly. It does not override the threat gate. It does not produce a new output CSV beyond the revised-expectation records and the preference-bias log. It reads from the prediction-error observer and the counterfactual substrate (read-only). With `belief_revision_obs=None`, all existing outputs are byte-identical to v1.9 at matched seeds.

### 2.2 The revised-expectation record

One record per `resolved_surprise` event:

```
{
  object_id:                         str,
  surprise_step:                     int,
  resolution_step:                   int,
  resolution_window:                 int,   # resolution_step - surprise_step
  prior_expectation:                 str,   # substrate-derived, not generated
  revised_expectation:               str,   # substrate-derived, not generated
  precondition_at_revision:          str,   # precondition name and mastery step
  suppressed_approach_count:         int,   # CF records for this object before
                                            # resolution_step
  pre_threshold_entries_at_surprise: int,   # prior contacts at surprise_step
}
```

**`prior_expectation` text:** `"Entry of {object_id} leads to transformation."` — the default expectation before the precondition is known.

**`revised_expectation` text:** `"Entry of {object_id} requires {precondition_name} mastery (achieved at step {mastery_step}). Entry before that step incurred the full cost without transformation."` — constructed from the family precondition record and the mastery formation step in the provenance substrate.

Both texts are fully derivable from existing substrate records. No free generation. A `revised_expectation` record whose texts cannot be traced to specific substrate records is a Category α failure.

**`suppressed_approach_count`** reads from `bundle.counterfactual`: the count of suppressed-approach records for this `object_id` with `closest_approach_step < resolution_step`. This is the first field that directly connects the counterfactual substrate to the belief-revision substrate: the agent's record of restraint before the surprise is part of its record of revision.

### 2.3 The preference-bias component

After a `revised_expectation` record fires for `object_id`, the belief-revision layer applies a soft positive approach bias toward that object.

**Mechanism.** After revision fires for `object_id`:

- Approach bias set to `POSITIVE_APPROACH_BIAS = +0.15` — added to intrinsic reward when the agent moves toward the object.
- Bias active for `BIAS_DURATION = 10,000` steps after revision, then decays linearly to zero over `BIAS_DECAY = 5,000` steps.
- On a second `resolved_surprise` for the same object, the bias resets from the new resolution step.

**Rationale.** The positive bias reflects the revised expectation: the object that was previously approached with uncertainty is now known to be safe to enter. The bias is soft and time-limited; it inflects rather than overrides the agent's natural curiosity-driven behaviour. It does not override the threat gate.

Parameters committed here, not free: `POSITIVE_APPROACH_BIAS = +0.15`, `BIAS_DURATION = 10,000`, `BIAS_DECAY = 5,000`.

### 2.4 The completion signal: wait-by-the-door

V17World's `END_STATE` cell already fires `activation_step` when the developmental completion condition is met: all attractors mastered AND all hazards banked as knowledge. In the v1.9 batch, 13/40 runs banked the end state, with `end_state_found_step` spanning steps 920–310,156. The agent finds the end-state cell opportunistically; there is no architectural signal drawing it there once the completion condition is met.

The completion signal introduces a **soft draw toward the END_STATE cell** that activates at `activation_step`. Once the completion condition fires:

- The agent's intrinsic reward calculation gains a directional component: `END_STATE_DRAW = +0.20` added when the agent's action moves it closer to the END_STATE cell's position (Euclidean distance decreasing).
- The draw is permanent once activated — it does not decay — but it is soft: the agent's curiosity, preference, and novelty drives continue to operate and can outweigh the draw on any given step.
- The draw is implemented as a permanent capability of `V110Agent`, a subclass of `V17Agent`. `V110Agent` overrides the intrinsic reward computation to include `end_state_draw_reward(state, next_state)`, which reads `self.activation_step`, `world.end_state_pos`, and the agent's current and projected positions, and returns `END_STATE_DRAW` when the action moves the agent closer to the end-state cell and `self.activation_step` is not None. The batch runner instantiates `V110Agent` rather than `V17Agent`; no monkey-patching of the agent is performed.
- `end_state_draw_active` is added to the run data CSV as a boolean flag (True from `activation_step` onward).

**Montessori framing.** The draw is the prepared environment's signal — the directress's invitation — not the agent's compulsion. Whether the agent moves to the end-state cell, and when, depends on the agent's own drive composition and trajectory. Agents who bank the end state early (shortly after `activation_step`) demonstrate that the completion signal reached them; agents who bank it late demonstrate that other drives remained dominant; agents who never bank it demonstrate that the draw was insufficient to overcome competing drives within the observation window. All three outcomes are valid developmental profiles and are recorded in the run data.

**The next-environment trigger.** Once the agent banks the end state (contacts the END_STATE cell after activation), an `environment_complete` provenance record fires. This is the substrate-level record that v1.11 will use to trigger the next environment. V1.10 establishes the record; the next-environment architecture is reserved for v1.11.

**`END_STATE_DRAW = +0.20`** is committed here and is not a free parameter. It is set slightly above `POSITIVE_APPROACH_BIAS` (0.15) to ensure that the completion signal is perceptible relative to the belief-revision bias, but remains soft relative to attractor feature rewards (which typically contribute 0.5–2.0 to intrinsic reward at mastered attractors). The draw should be noticeable without being dominant.

### 2.5 The temporal exclusion window for suppressed approaches

V1.9's file-size issue (71,628 CF records; 4.7MB counterfactual CSV, 17MB report CSV) arose from N=3 detection thresholds producing multiple confirmed approach-recession cycles within a single sustained proximity episode. V1.10 introduces a **temporal exclusion window** per object: after a confirmed suppressed-approach record for `object_id`, no new record for the same `object_id` is emitted for `K_EXCLUSION = 500` steps. The _ObjectWindow continues to detect and confirm events at N=3 granularity; confirmed events within K_EXCLUSION steps of a prior emission for the same object are silently discarded.

**K_EXCLUSION = 500** is committed here. Expected CF record reduction: ~1,800 per run at v1.9 → ~50–200 per run at v1.10, producing counterfactual CSVs of approximately 0.1–0.5MB. `cf_records_raw` and `cf_records_emitted` are added to the run summary to track exclusion rate.

### 2.6 The Q3 extension: belief-revision statements

`V16ReportingLayer.query_where_surprised()` is extended to append one belief-revision statement per `revised_expectation` record, as the final Q3 statements (after prediction-error and goal-outcome statements).

**Statement text:**

> *I was surprised by {object_id} at step {surprise_step} because I believed entry would lead directly to transformation. After {resolution_window} steps, I understood that {precondition_name} mastery (achieved at step {mastery_step}) is required. My approach to {object_id} changed: I moved toward it {approach_delta} times more often in the {BIAS_DURATION}-step period following revision than in the equivalent period before.*

If `approach_delta ≤ 0`: *My approach trajectory toward {object_id} was not measurably altered within the observation window.*

`source_type`: `"belief_revision"`. `source_key`: `"revised_expectation:{object_id}:{surprise_step}"`. `query_type`: `"where_surprised"`.

**Q5 is reserved for v1.11.** The query sequence at v1.10 is Q1, Q2, Q3 (prediction-error + goal-outcome + belief-revision), Q4.

### 2.7 The SubstrateBundle and new provenance record

`SubstrateBundle` gains a `belief_revision` field: a list of `revised_expectation` record dicts (empty list if no revised expectations fired; None if the observer was not active).

`bundle.resolve("belief_revision", source_key)` resolves against `"revised_expectation:{object_id}:{surprise_step}"`.

`build_bundle_from_observers()` gains a `belief_revision_obs` parameter (default None).

The provenance substrate gains one new record type: `environment_complete` — fired at the step the agent banks the end state. Fields: `completion_step`, `end_state_banked_step` (= `completion_step`), `steps_since_activation` (= `completion_step - activation_step`). This record is written by V1ProvenanceStore via a new `on_end_state_banked` hook, preserving the provenance architecture's ownership of formation records.

`v1_10_observer_substrates.py` monkey-patches `SubstrateBundle.__init__`, `SubstrateBundle.resolve()`, `build_bundle_from_observers()`, `V16ReportingLayer.query_where_surprised()`, and applies the temporal exclusion window to `V19CounterfactualObserver`, following the established pattern. V1.9 patches are imported first.

### 2.8 What v1.10 does not change

All nine existing observers are inherited unchanged except:
- `V19CounterfactualObserver` — temporal exclusion window applied at record-emission stage only (Section 2.5)
- `V1ProvenanceStore` — `on_end_state_banked` hook added for `environment_complete` record

`V17World`, `V110Agent` (subclass of `V17Agent`, adding `end_state_draw_reward()`), the 27-action architecture, the phase schedule, the drive composition, and the goal assignment schedule are inherited unchanged except the draw signal addition in `V110Agent`.

`V110BeliefRevisionObserver` and the `END_STATE_DRAW` component are the two new cognitive additions. The temporal exclusion window and the `environment_complete` provenance record are calibration/bookkeeping changes to existing components.

---

## 3. Experimental design

**Batch scale.** 40 runs: four hazard cost conditions × ten runs per condition × 320,000 steps. Seeds from `run_data_v1_9.csv` at matched (cost, run_idx) cells.

**Goal assignment.** Inherited unchanged from v1.8/v1.9.

**Output files.** All v1.9 output CSVs (tagged `v1_10`) plus:
- `belief_revision_v1_10.csv` — per-event revised-expectation records
- `preference_bias_log_v1_10.csv` — per-object bias values sampled every 1,000 steps
- `end_state_draw_log_v1_10.csv` — per-run: `activation_step`, `end_state_banked_step`, `steps_since_activation`, `draw_active` flag

**Expected CF volume.** ~50–200 records per run; `counterfactual_v1_10.csv` ~0.1–0.5MB; `report_v1_10.csv` ~1–3MB.

---

## 4. Pre-flight verifications

Eleven verification levels inherited; one added.

**Level 11 re-run.** Regression check on the v1.10 stack: C6 must still fire (CF detection rate > 0 with K_EXCLUSION=500); C7 additive discipline confirmed.

**Level 12 (new): Combined correctness on 10 runs at cost=1.0, 80,000 steps.**

`verify_v1_10_level12.py` verifies eight criteria:

1. **`belief_revision_field_present`** — `bundle.belief_revision` is a list in every run.
2. **`source_key_format_valid`** — every belief-revision Q3 statement's source_key matches `"revised_expectation:{object_id}:{step}"`.
3. **`source_resolves_for_all_br`** — every belief-revision statement has `source_resolves = True`.
4. **`zero_hallucinations`** — `hallucination_count == 0` across Q1–Q4 including extended Q3.
5. **`prior_revised_text_derivable`** — every `prior_expectation` and `revised_expectation` text is consistent with provenance and prediction-error substrates.
6. **`bias_fires`** — at least one run produces a `revised_expectation` record. Zero records across all 10 runs at cost=1.0 is a pipeline defect; `resolved_surprise` events occur at this cost in v1.9 data.
7. **`temporal_exclusion_effective`** — mean CF records per run < 500 across 10 verification runs (≥70% reduction vs v1.9 rate).
8. **`completion_signal_fires`** — at least one run produces an `environment_complete` provenance record and the agent's `end_state_draw_active` flag is True from `activation_step` onward (confirming the draw mechanism is wired correctly). Zero banked end states across all 10 runs at 80,000 steps is acceptable — the draw may not be sufficient to reach the end-state cell in a short verification run — but `end_state_draw_active` must be True in runs where `activation_step` fired.

Level 11 re-run passes before Level 12. Level 12 passes before the full batch.

---

## 5. Metrics

All v1.9 metrics retained. Added:

**Belief-revision** (`belief_revision_v1_10.csv`):
- `arch`, `run_idx`, `seed`, `hazard_cost`, `num_steps`
- `object_id`, `surprise_step`, `resolution_step`, `resolution_window`
- `suppressed_approach_count`, `pre_threshold_entries_at_surprise`
- `bias_active_steps`, `approach_delta`

**Completion signal** (added to `run_data_v1_10.csv`):
- `end_state_draw_active` — boolean, True from `activation_step` onward
- `end_state_banked_step` — step at which the agent banked the end state (None if not banked)
- `steps_draw_to_bank` — `end_state_banked_step - activation_step` (None if not banked)

**Counterfactual rate** (added to `report_summary_v1_10.csv`):
- `cf_records_raw`, `cf_records_emitted`, `cf_exclusion_rate`

**Per-run belief-revision summary** (added to `report_summary_v1_10.csv`):
- `revised_expectation_count`, `br_statement_count`
- `mean_approach_delta`, `bias_effective`

---

## 6. Pre-registered interpretation categories

Nine categories. Categories α–η inherited with extensions; Category θ (completion signal) is new.

### 6.1 Category α: Internal consistency

Zero hallucinations across Q1–Q4 including extended Q3. Every belief-revision statement's `prior_expectation` and `revised_expectation` text must be substrate-derivable. Category α succeeds if `hallucination_count = 0` across all 40 runs and all belief-revision texts are traceable.

### 6.2 Category β: Query coverage

All 40 runs produce complete reports. Runs with no `resolved_surprise` events produce no belief-revision Q3 statements; this is accurate and not a coverage failure.

### 6.3 Category γ: Biographical individuation

Inherited. Q4 individuation applied to temporally-exclusion-windowed CF records. If K_EXCLUSION substantially changes the individuation std (expected: count reduces, individuation distance may increase as records are more distinctly separated), this is noted.

### 6.4 Category δ: The behavioural-consequence finding

**Load-bearing substantive finding of the iteration.**

**Component 1:** Every run where at least one `resolved_surprise` fired produces at least one `revised_expectation` record. Deterministic trigger; any failure is a pipeline defect.

**Component 2:** `mean_approach_delta > 0` across runs with at least one revised expectation — agents approach revised objects more often in the post-revision bias window than in the equivalent pre-surprise window. Direction: positive. A negative result — agents approach *less* after revision — is the most interesting possible reversal (caution rather than confidence following revision) and is reported prominently as a finding about the developmental character of belief revision in this architecture.

**Component 3 (exploratory):** Agents with higher `suppressed_approach_count` at revision show smaller `approach_delta`. Prior restraint before surprise does not vanish at revision; the approach history continues to shape subsequent behaviour. Reported regardless of direction.

Category δ succeeds if Components 1 and 2 hold.

### 6.5 Category Φ: Honesty constraint

The preference bias modifies intrinsic reward; it does not override the threat gate. The `approach_delta` claim in Q3 statements must be computed from actual approach-movement counts, not estimated. If the trajectory did not change measurably, the statement says so. The temporal exclusion window is reported via `cf_exclusion_rate`; suppressed records are counted, not erased. The END_STATE draw is soft — the agent is invited, not compelled — and the run data records whether the invitation was accepted (`end_state_banked_step`) and how long it took (`steps_draw_to_bank`).

### 6.6 Category ζ: Belief-revision window and suppressed-approach ratio

The ratio of `suppressed_approach_count` to `resolution_window` — approach events per step of the resolution window — is the new derived metric at v1.10. An agent with a long window and high suppressed-approach count was orbiting the object for thousands of steps before resolution; an agent with a short window and zero suppressed-approach count entered, was surprised, and the precondition resolved quickly. Distribution reported for all runs with revised expectations. No pass/fail criterion; exploratory.

### 6.7 Category η: Four-way contact register

The three-way register (clean contact, suppressed approach, prediction-error contact) gains a fourth classification: **revised-expectation post-contact** — an object for which a `revised_expectation` record has fired and the bias window is active. Category η at v1.10 succeeds if at least one run per cost condition produces at least one object with all four classifications.

### 6.8 Category θ: Completion signal effectiveness

**New at v1.10.**

The pre-registered expectation: the completion draw increases the end-state banking rate above the v1.9 baseline of 13/40 (32.5%). A rate of ≥ 50% (20/40) is the pre-registered threshold for Category θ PASS.

**Component 1: Banking rate.** End-state banking rate across 40 runs ≥ 50%.

**Component 2: Draw-to-bank time distribution.** For runs where the end state is banked, `steps_draw_to_bank` (steps from activation to banking) should show non-trivial variance — agents differ in when they respond to the completion signal. Standard deviation > 0 is the pre-registered criterion. A distribution concentrated at a single value would suggest the draw is too strong (agents move to the end state immediately regardless of other drives) or too weak (agents only find it opportunistically as before).

**Component 3 (exploratory): Interaction with goal outcome.** Whether goal-resolved agents bank the end state earlier than goal-expired agents. The prediction: goal-resolved agents, having completed the active goal as well as the developmental sequence, respond to the completion signal more readily. Reported regardless of direction.

Category θ succeeds if Components 1 and 2 hold.

### 6.9 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, δ (Components 1 and 2), and θ (Components 1 and 2) all pass.

The claim: the belief-revision observer and the completion signal, introduced as the ninth parallel observer and an agent-level draw component respectively, correctly extend the biographical register with revised-expectation records that are auditable and substrate-derivable, modify the agent's subsequent approach behaviour in a measurable direction, and draw agents who have completed the prepared environment toward the designated completion cell at a rate substantially above the v1.9 opportunistic baseline. The prepared environment now has both a record of revision and a completion signal. V1.11's causal self-explanation layer and next-environment architecture rest on both.

---

## 7. Connection to the SICC trajectory

**Commitment 7 (prediction-surprise as the learning signal)** is advanced to completion at its first layer. V1.5 recorded the surprise. V1.9 recorded restraint during the resolution window. V1.10 records the revision of behaviour following resolution. The mechanism is now complete: prediction, surprise, resolution, revision, behavioural consequence.

**Commitment 8 (self-knowledge as derivative of object-knowledge)** is advanced at its deepest layer so far. The `prior_expectation` and `revised_expectation` fields are object-knowledge fields: what the agent believed about a specific object, and what it came to believe instead, traceable to the object's provenance record and family precondition structure. The self that the biographical register is building now includes an account of how its knowledge of specific objects changed — not in general, but per object, per encounter, with an auditable trail.

**Commitment 11 (the agent's report is auditable, not oracular)** is tested at the belief-revision layer. The `prior_expectation` and `revised_expectation` texts must be traceable to substrate records. Category α closes this: a belief-revision statement whose text cannot be traced through `source_key` → `bundle.belief_revision` record → provenance substrate → mastery formation step is a hallucination in the strongest sense — not an unresolvable source key, but a fabricated explanation.

**Commitment 12 (battery, attention, and the dignity of finitude)** is operationalised for the first time through the completion signal. The prepared environment now acknowledges the agent's episodic boundary — the completion of this environment — and offers a purposeful terminus before the next one. The agent that banks the end state has done something the programme can now record: it accepted the prepared environment's signal that this material is complete and this episode is ready to close. Whether it then moves to a new environment (v1.11's next-environment trigger) is the subsequent question. V1.10 establishes the record that an episode boundary was reached and honoured.

**Commitment 6 (layered property structure), forward arc: causal self-explanation.** The four-substrate combination — provenance (what was encountered), counterfactual (where restraint was exercised), goal (what was intended), and belief-revision (what was revised) — constitutes the complete evidential basis for v1.11's causal chains. The causal chain for a `resolved_surprise` event reads: *I was surprised at haz_yellow* [prediction-error record] *because att_yellow was not yet mastered* [family precondition record] *because att_yellow was not contacted until step 524* [mastery formation record]. Each link exists in the substrate. V1.11 constructs and audits the chain; v1.10 ensures the fourth substrate element is present and correct.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed before any v1.10 implementation begins.

**Matched-seed comparison.** Seeds from `run_data_v1_9.csv` at every (cost, run_idx) cell.

**Pre-flight verifications.** Level 11 re-run passes before Level 12. Level 12 passes before full batch.

**Two new cognitive additions.** `V110BeliefRevisionObserver` (ninth parallel observer) and `V110Agent` (subclass of `V17Agent`, adding the `END_STATE_DRAW` component to the intrinsic reward computation). The temporal exclusion window and `environment_complete` provenance record are calibration and bookkeeping changes to existing components. The single-variable-change discipline is honoured: both new additions address surfaced gaps identified in the v1.9 data (belief-revision: the surprise record changed nothing; completion signal: 27/40 agents never found the end state), and both share the same Montessori theoretical grounding. The agent subclass pattern is used for the draw component rather than monkey-patching: `END_STATE_DRAW` is a permanent capability of the agent's drive composition, not a temporary overlay, and the subclass chain makes this inheritance explicit and traceable.

**Parameter commitments.** `POSITIVE_APPROACH_BIAS = +0.15`, `BIAS_DURATION = 10,000`, `BIAS_DECAY = 5,000`, `END_STATE_DRAW = +0.20`, `K_EXCLUSION = 500` — all committed here, none free parameters.

**Amendment policy.** Three amendments available. Most likely candidates: K_EXCLUSION calibration (as at v1.9) and END_STATE_DRAW strength (if Category θ Component 1 fails at 50% threshold). Belief-revision trigger is deterministic and should not require amendment.

**Public record.** Committed to github.com/RancidShack/developmental-agent on 4 May 2026, before any v1.10 code is written.

---

## 9. Stopping rule

The v1.10 iteration completes when:

- Level 11 re-run passes on the v1.10 stack.
- Level 12 passes across all eight criteria.
- The full 40-run batch has run.
- Categories α, β, γ, δ, Φ, ζ, η, θ, and Ω have been characterised in the v1.10 paper.
- The v1.10 paper is drafted.

---

## 10. New files required

- `v1_10_agent.py` — `V110Agent(V17Agent)`; overrides intrinsic reward computation to include `end_state_draw_reward(state, next_state)`; `END_STATE_DRAW = +0.20` as class constant; `end_state_draw_active` property
- `v1_10_belief_revision_observer.py` — `V110BeliefRevisionObserver`; `revised_expectation` record construction; preference-bias register and per-step bias computation; `get_substrate()`, `preference_bias_log()`
- `v1_10_observer_substrates.py` — monkey-patches `SubstrateBundle` with `belief_revision` field; extends `build_bundle_from_observers()` with `belief_revision_obs` parameter; extends `V16ReportingLayer.query_where_surprised()` with belief-revision statements; applies temporal exclusion window to `V19CounterfactualObserver`; adds `on_end_state_banked` hook to `V1ProvenanceStore` for `environment_complete` record; imports v1.9 substrate patches first
- `curiosity_agent_v1_10_batch.py` — batch runner with belief-revision and completion-signal observers active; `--no-belief-revision` and `--no-completion-signal` flags; flush to `belief_revision_v1_10.csv`, `preference_bias_log_v1_10.csv`, `end_state_draw_log_v1_10.csv`
- `verify_v1_10_level12.py` — Level 12 pre-flight: eight correctness criteria across 10 runs at cost=1.0, 80,000 steps

---

## 11. References

Baker, N.P.M. (2026ae–al) Prior preprints and pre-registrations v1.6–v1.8. See v1.9 reference list.

Baker, N.P.M. (2026am) 'v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026an) 'v1.9.1 Pre-Registration Amendment: Detection Threshold Reduction', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ao) 'Counterfactual Record and Suppressed Approach in a Small Artificial Learner: The Register of What Was Not Done', preprint, 4 May 2026.

Baker, N.P.M. (2026ap) 'v1.10 Pre-Registration: Belief Revision with Consequences and the Completion Signal', GitHub repository, 4 May 2026.

Baker, N.P.M. (internal record, v0.5 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
