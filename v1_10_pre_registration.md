# v1.10 Pre-Registration: Belief Revision with Consequences

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.10 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

Ten iterations have built a developmental agent whose biographical register holds: what it encountered and what it learned (Q1); how its knowledge is structured across object families (Q2); where its expectations were violated and over what developmental distance (Q3); and where it came close to an eligible object and withdrew without contact (Q4). The register is auditable, individually variable, substrate-agnostic, and cumulative. It now holds a record of intention and outcome (v1.8) and a record of restraint (v1.9).

What the register does not yet hold is a record of revision. The agent was surprised by haz_yellow at step 493. The prediction-error substrate records this. The prediction-error resolution window records how long it took for the transformation to follow. The Q3 statement describes the gap. But the agent's subsequent behaviour toward haz_yellow is governed entirely by the threat gate and competency layer — the record of the surprise is not consulted by either. The surprise happened; it was recorded; it changed nothing.

v1.10 changes that. The belief-revision layer introduces two architectural additions: a `revised_expectation` record that fires after each `resolved_surprise` event, stating explicitly what the agent believed before the surprise and what it now believes; and a preference bias that reads from the revised-expectation register and modifies the agent's approach trajectory toward objects for which a revised expectation is held. The record of failure becomes a developmental resource.

This is the SICC through-line made operative: v1.8 gave the agent a reason to learn; v1.9 gave it a record of choosing; v1.10 gives it a record of being wrong and changing. The biographical register at v1.10 holds an account of what the agent learned, where it held back, and — for the first time — how it changed its mind.

---

## 2. Architectural specification

### 2.1 The belief-revision layer

The belief-revision layer is implemented as `V110BeliefRevisionObserver`, the ninth parallel observer. It reads from the prediction-error substrate after each `resolved_surprise` event and fires a `revised_expectation` record. It also maintains a per-object revised-expectation register that is consulted at each step by a new preference-bias component. It does not modify the threat gate, competency layer, or any existing observer.

**Trigger.** A `revised_expectation` record fires when V15PredictionErrorObserver records a `resolved_surprise` event — that is, when the agent has made contact with a hazard object before the precondition was met, and the transformation has subsequently occurred. The trigger is the resolution of the surprise, not the surprise itself. This preserves the developmental sequence: the agent waited, the resolution arrived, and only then does it have the material for revision — it now knows both that it was wrong and what the correct account is.

**What the belief-revision layer does not do.** It does not modify the agent's reward function, value function, or Q-table directly. It does not modify the threat gate's hard block on pre-precondition entries. It does not produce a new observer output CSV beyond the revised-expectation records and the preference bias log. It reads from the prediction-error observer and the counterfactual substrate (read-only). It is additive: with `belief_revision_obs=None`, all existing outputs are byte-identical to v1.9 at matched seeds.

### 2.2 The revised-expectation record

One record per `resolved_surprise` event, with the following structure:

```
{
  object_id:                    str,    # e.g. "haz_yellow"
  surprise_step:                int,    # step at which the surprise fired
  resolution_step:              int,    # step at which resolved_surprise fired
  resolution_window:            int,    # resolution_step - surprise_step
  prior_expectation:            str,    # what the agent expected before the surprise
  revised_expectation:          str,    # what the agent now believes
  precondition_at_revision:     str,    # the precondition name and mastery status
  suppressed_approach_count:    int,    # number of suppressed approaches to this
                                        # object recorded before resolution_step
  pre_threshold_entries_at_surprise: int, # agent.pre_transition_hazard_entries
                                          # for this object at surprise_step
}
```

**`prior_expectation` and `revised_expectation` text.** These are derived from the provenance and prediction-error substrates, not generated freely. The format is:

- `prior_expectation`: `"Entry of {object_id} leads to transformation."` — the default expectation before any precondition is known.
- `revised_expectation`: `"Entry of {object_id} requires {precondition_name} mastery (achieved at step {mastery_step}). Entry before that step incurred the full cost without transformation."` — constructed from the family precondition record and the mastery formation step in the provenance substrate.

Both fields are fully derivable from existing substrate records. No free generation occurs. The honesty constraint (Category Φ) applies: a `revised_expectation` record that cannot be traced to a `resolved_surprise` event and the relevant provenance records is a hallucination.

**`suppressed_approach_count`.** Read from `bundle.counterfactual` — the count of suppressed-approach records for this `object_id` with `closest_approach_step < resolution_step`. This field connects the counterfactual substrate to the belief-revision substrate for the first time: the agent's record of restraint before the surprise is now part of its record of revision. An agent that approached haz_yellow four times without entering, then entered pre-precondition and was surprised, has a different revision profile from an agent that entered directly on first encounter.

### 2.3 The preference-bias component

After a `revised_expectation` record fires for `object_id`, the belief-revision layer modifies the agent's approach behaviour toward that object via a soft preference bias. This is the behavioural consequence that distinguishes v1.10 from all prior iterations: the record of being wrong changes what the agent does next.

**Mechanism.** The preference-bias component maintains a per-object bias register. After a `revised_expectation` record fires for `object_id`:

- The object's approach bias is set to `POSITIVE_APPROACH_BIAS = +0.15` — a soft preference increment added to the agent's intrinsic reward calculation when the agent is moving toward the object.
- The bias remains active for `BIAS_DURATION = 10,000` steps after the revision step, then decays to zero linearly over `BIAS_DECAY = 5,000` steps.
- If a second `resolved_surprise` fires for the same `object_id` (a second pre-precondition entry), the bias is reset to `POSITIVE_APPROACH_BIAS` from the new resolution step.

**Rationale.** The positive approach bias reflects the agent's revised expectation: it now knows the precondition, knows it has been met (the revision fires after resolution), and knows the object is now safe to enter. The bias is not a reward for being wrong; it is a preference adjustment that reflects updated knowledge — the object that was previously approached cautiously is now known to be approachable. The bias is soft (0.15 on the intrinsic reward scale) and time-limited (decays after 15,000 steps), so it does not override the agent's natural curiosity-driven behaviour; it inflects it.

**What the bias does not do.** It does not override the threat gate. If the precondition is not met, the hard block remains regardless of the bias. The bias operates in Phase 3 (post-precondition) and Phase 2 (after revision, which only fires after resolution, which requires the precondition to have been met). It cannot accelerate pre-precondition entries.

These parameters — `POSITIVE_APPROACH_BIAS = +0.15`, `BIAS_DURATION = 10,000`, `BIAS_DECAY = 5,000` — are committed here and are not free parameters.

### 2.4 The temporal exclusion window for suppressed approaches

V1.9's C6 failure and the resulting file-size issue (71,628 CF records; 17MB report CSV) arose from the interaction of N=3 detection thresholds with 320,000-step runs in which the agent's orbital navigation produced multiple confirmed approach-recession cycles against the same object within a short temporal window — what the v1.9 paper characterises as a single sustained proximity episode generating dozens of records at 3-step granularity.

V1.10 introduces a **temporal exclusion window** per object in the counterfactual observer: after a confirmed suppressed-approach record for `object_id`, no new suppressed-approach record for the same `object_id` is emitted for `K_EXCLUSION = 500` steps. This prevents a single proximity episode from generating dozens of records while preserving sensitivity for genuinely distinct approach events separated by meaningful temporal distance.

The structural definition of a suppressed approach is unchanged. The detection thresholds (N_approach=3, N_recession=3, per v1.9.1) are unchanged. The exclusion window is applied at the record-emission stage, not the detection stage: the _ObjectWindow still detects and confirms events at N=3 granularity, but confirmed events within K_EXCLUSION steps of a prior record for the same object are silently discarded.

**K_EXCLUSION = 500 steps** is committed here and is not a free parameter. 500 steps represents a meaningful temporal separation in a 320,000-step run — approximately 0.16% of the total run — and is long enough to separate distinct approach episodes while short enough to capture repeated genuine approaches to the same object within a run. At this value, the expected CF record count reduces from ~1,800 per run to an estimated 50–200 per run (a 10–35× reduction), producing counterfactual CSVs of approximately 0.1–0.5MB rather than 4.7MB.

This change is introduced at v1.10 rather than as a v1.9 amendment because the v1.9 batch ran cleanly with zero hallucinations and the data is valid. The v1.9 paper characterises the high-count runs as Phase 3 consolidation events and notes the interpretive challenge. The temporal exclusion window is a calibration change that produces a more interpretively tractable record without altering the architectural definition.

### 2.5 The Q3 extension: belief-revision window

`V16ReportingLayer.query_where_surprised()` is extended (via the v1.10 substrate patch, following the established monkey-patch pattern) to append a belief-revision statement for each `revised_expectation` record in the substrate. The belief-revision statement answers: *what did I believe before, what do I believe now, and did the revision change my behaviour?*

**Belief-revision statement text template:**

> *I was surprised by {object_id} at step {surprise_step} because I believed entry would lead directly to transformation. After {resolution_window} steps, I understood that {precondition_name} mastery (achieved at step {mastery_step}) is required. My approach to {object_id} changed: I moved toward it {approach_delta} times more often in the {BIAS_DURATION}-step period following revision than in the equivalent period before.*

Where `approach_delta` is derived from the preference-bias log: the count of positive-direction movements toward the object in the post-revision bias window versus the equivalent pre-surprise window. If the agent was in Phase 1 at surprise_step (impossible given the Phase 1 waypoint sweep does not produce hazard contact), the statement is omitted. If the agent did not produce any approach movements toward the object in either window (rare but possible), the closing clause is replaced with: *My approach trajectory toward {object_id} was not measurably altered within the observation window.*

`source_type`: `"belief_revision"`
`source_key`: `"revised_expectation:{object_id}:{surprise_step}"`
`query_type`: `"where_surprised"` — Q3 is extended, not replaced. Belief-revision statements appear after all prediction-error statements and after all v1.8 goal outcome statements. They are the final Q3 statements.

**`generate_report()` is not extended at v1.10.** Q4 remains the final query type. The belief-revision statements extend Q3, not add Q5. Q5 (causal self-explanation) is reserved for v1.11.

### 2.6 The SubstrateBundle extension

`SubstrateBundle` gains a `belief_revision` field: a list of `revised_expectation` record dicts (empty list if no revised expectations fired; None if the belief-revision observer was not active).

`bundle.resolve("belief_revision", source_key)` resolves against the source_key format `"revised_expectation:{object_id}:{surprise_step}"`. Returns True if a record exists with matching `object_id` and `surprise_step`; False otherwise.

`build_bundle_from_observers()` gains a `belief_revision_obs` parameter (default None). All nine existing parameters are unchanged.

`v1_10_observer_substrates.py` monkey-patches `SubstrateBundle.__init__`, `SubstrateBundle.resolve()`, `build_bundle_from_observers()`, and `V16ReportingLayer.query_where_surprised()` following the established pattern. V1.9 substrate patches are imported first; v1.10 patches are applied on top.

### 2.7 What v1.10 does not change

All nine existing observers — `V1ProvenanceStore`, `V13SchemaObserver`, `V13FamilyObserver`, `V14ComparisonObserver`, `V15PredictionErrorObserver`, `V16ReportingLayer`, the v1.7–v1.9 substrate patches, `V18GoalObserver`, and `V19CounterfactualObserver` — are inherited unchanged, with the single exception of the temporal exclusion window applied to `V19CounterfactualObserver` (Section 2.4). `V17World`, `V17Agent`, the 27-action architecture, the phase schedule, the drive composition, and the goal assignment schedule are inherited unchanged.

`V110BeliefRevisionObserver` and the temporal exclusion window are the two architectural extensions at v1.10.

---

## 3. Experimental design

**Batch scale.** One architecture (v1.10) crossed with four hazard cost conditions (0.1, 1.0, 2.0, 10.0) crossed with ten runs per condition at 320,000 steps, totalling 40 runs. Seeds drawn from `run_data_v1_9.csv` at matched (cost, run_idx) cells, preserving the seed chain.

**Goal assignment.** Inherited from v1.8/v1.9 unchanged.

**Output files.** All v1.9 output CSVs (tagged `v1_10`) plus:
- `belief_revision_v1_10.csv` — per-event revised-expectation records
- `preference_bias_log_v1_10.csv` — per-object per-step bias values (sampled every 1,000 steps per run)

**Expected CF record reduction.** With K_EXCLUSION=500, expected ~50–200 CF records per run vs ~1,800 at v1.9. `counterfactual_v1_10.csv` expected to be approximately 0.1–0.5MB; `report_v1_10.csv` expected to be approximately 1–3MB. If the actual CF record count per run still exceeds 500, a K_EXCLUSION amendment is warranted.

---

## 4. Pre-flight verifications

Eleven verification levels are inherited; one is added.

**Levels 1–10:** Inherited from v1.9 pipeline. Level 11 (counterfactual observer correctness) is re-run as a regression check on the v1.10 stack, now including the temporal exclusion window. The Level-11 re-run must confirm that C6 still fires (detection rate > 0) with K_EXCLUSION=500 — the exclusion window must not suppress all events.

**Level 12 (new): Belief-revision observer correctness on 10 runs.**

`verify_v1_10_level12.py` runs 10 runs at cost=1.0, 80,000 steps, with the belief-revision observer active. It verifies:

1. **`belief_revision_field_present`** — `bundle.belief_revision` is a list (not None) in every run.
2. **`source_key_format_valid`** — every belief-revision Q3 statement's `source_key` matches `"revised_expectation:{object_id}:{step}"` with known object_id and integer step.
3. **`source_resolves_for_all_br`** — every belief-revision statement has `source_resolves = True`.
4. **`zero_hallucinations`** — hallucination_count == 0 across all statements (Q1–Q4 including extended Q3) in all 10 runs.
5. **`prior_revised_text_derivable`** — every `prior_expectation` and `revised_expectation` text in every record is consistent with the provenance and prediction-error substrates for the same run (checked by cross-referencing mastery_step against provenance records).
6. **`bias_fires`** — at least one run produces a `revised_expectation` record (confirming the belief-revision layer triggers at this cost level and step count). A run set with zero revised expectations across all 10 runs at cost=1.0 is a triggering failure, not a valid null finding — resolved_surprise events occur at cost=1.0 in v1.9 data.
7. **`temporal_exclusion_effective`** — mean CF records per run is below 500 across the 10 verification runs, confirming K_EXCLUSION=500 reduces the v1.9 record rate by at least 70%.
8. **`additive_discipline`** — with `--no-belief-revision`, Q1–Q4 outputs are consistent with v1.9 (zero hallucinations, correct query type coverage, CF record count reduced per temporal exclusion).

Level 11 re-run must pass before Level 12. Level 12 must pass before the full v1.10 batch.

---

## 5. Metrics

All v1.9 metrics are retained. The following are added.

**Per-event belief-revision metrics** (`belief_revision_v1_10.csv`):
- `arch`, `run_idx`, `seed`, `hazard_cost`, `num_steps` — run identification
- `object_id`, `surprise_step`, `resolution_step`, `resolution_window`
- `suppressed_approach_count` — prior suppressed approaches before resolution
- `pre_threshold_entries_at_surprise` — prior contacts at time of surprise
- `bias_active_steps` — steps during which positive approach bias was active for this object

**Per-run belief-revision summary** (added to `report_summary_v1_10.csv`):
- `revised_expectation_count` — number of revised_expectation records in the run
- `br_statement_count` — number of belief-revision Q3 statements produced
- `mean_approach_delta` — mean approach-movement increase in bias window vs pre-surprise window, across all revised objects
- `bias_effective` — True if at least one revised object shows positive approach_delta

**Counterfactual record rate** (added to monitor temporal exclusion):
- `cf_records_raw` — records detected before exclusion window
- `cf_records_emitted` — records emitted after exclusion window (this is what enters the substrate)
- `cf_exclusion_rate` — `1 - emitted/raw`

---

## 6. Pre-registered interpretation categories

Eight categories are pre-registered. Categories α through η are inherited with the extensions described below. One new category is added.

### 6.1 Category α: Internal consistency of all v1.10 reports

Every `ReportStatement` across all 40 runs — including all belief-revision Q3 statements — must have `source_resolves = True`. A belief-revision hallucination is a statement whose `source_key` does not resolve to a `revised_expectation` record in `bundle.belief_revision`. The additional requirement at v1.10: every `prior_expectation` and `revised_expectation` text must be traceable to provenance and prediction-error substrate records. Text that was generated without a substrate anchor is a Category α failure even if the `source_key` resolves.

Category α succeeds if `hallucination_count = 0` across all runs and all `prior_expectation`/`revised_expectation` texts are substrate-derivable.

### 6.2 Category β: Query coverage

All 40 runs produce complete reports (Q1 + Q2 + Q3 + Q4 non-empty, Q3 now including belief-revision statements where applicable). Runs where no `resolved_surprise` event fired produce no belief-revision Q3 statements; this is accurate and not a coverage failure.

### 6.3 Category γ: Biographical individuation

Inherited from v1.9. Q4 individuation comparison uses the temporally-exclusion-windowed CF records. If the exclusion window substantially reduces Q4 variance (expected: it will reduce count but not necessarily individuation distance), this is noted. The pre-registered individuation metric (std of pairwise normalised edit distances > 0.05) is applied to the emitted CF records, not the raw detected records.

### 6.4 Category δ: The behavioural-consequence finding

**The load-bearing substantive finding of the iteration.**

The pre-registered expectation: runs containing at least one `resolved_surprise` event also contain at least one `revised_expectation` record, and the preference trajectory for objects with revised expectations differs statistically from the trajectory for equivalent objects without them.

**Component 1: Belief-revision records in all surprise-containing runs.** Every run where at least one `resolved_surprise` event fired must produce at least one `revised_expectation` record. The trigger is deterministic — revision fires at resolution — so any failure here is a pipeline defect, not a null finding.

**Component 2: Preference trajectory difference.** Runs with at least one `revised_expectation` record must show a statistically different approach trajectory toward the revised object in the post-revision window versus the pre-surprise window. `mean_approach_delta > 0` across runs with at least one revised expectation is the pre-registered criterion. Direction: positive (more approach movements after revision than before). A negative mean_approach_delta — agents approach revised objects *less* after revision — is the most interesting possible reversal and is reported prominently if observed. An agent that was surprised, revised its expectation, and then approached the object less frequently would suggest that the revision produced caution rather than confidence, which would constitute a finding about the developmental character of belief revision in this architecture.

**Component 3: Suppressed-approach count at revision.** The `suppressed_approach_count` field in the `revised_expectation` record holds the count of prior approach-and-withdrawal events before resolution. The pre-registered directional expectation: agents with higher `suppressed_approach_count` at revision show smaller `approach_delta` — agents that held back more before the surprise do not immediately accelerate approach after revision. The developmental reading: prior restraint in the Winnicottian sense does not vanish at the moment of revised expectation; the approach history is part of the agent's relationship with the object and continues to shape it. This is exploratory; reported regardless of direction.

Category δ succeeds if Components 1 and 2 hold.

### 6.5 Category Φ: Honesty constraint

The preference bias is a soft modification to intrinsic reward. It does not override the threat gate. It does not constitute a decision in the strong philosophical sense. The Q3 belief-revision statement claims the agent's behaviour changed; this claim must be grounded in the preference-bias log.

The honesty constraint at v1.10: the `approach_delta` field in the belief-revision statement must be computed from actual approach-movement counts in the bias window and pre-surprise window, not estimated or assumed. If the agent's approach trajectory did not change measurably (approach_delta ≈ 0), the Q3 statement says so — *My approach trajectory toward {object_id} was not measurably altered within the observation window* — rather than claiming a change that the data does not support.

The temporal exclusion window is also subject to the honesty constraint: CF records suppressed by the exclusion window are counted and reported as `cf_exclusion_rate` in the summary CSV. The record does not pretend the approach events did not occur; it records that they were excluded from the substrate as non-distinct within the temporal window.

### 6.6 Category ζ: Belief-revision window distribution

Across runs with at least one `revised_expectation` record, the `resolution_window` distribution (steps between surprise and resolution) is inherited from v1.9's Q3 prediction-error resolution data and is now also held in the belief-revision substrate. At v1.10 a new derived metric is available: the ratio of `suppressed_approach_count` to `resolution_window` — approach events per step of the resolution window — which captures how actively the agent was engaging with the object during the period between surprise and revision. An agent with a long window and high suppressed-approach count was orbiting the object for thousands of steps before the resolution arrived. An agent with a short window and zero suppressed-approach count entered, was surprised, and the precondition resolved quickly without any intervening proximity behaviour.

Category ζ: the distribution of suppressed-approach-count-to-window ratios is reported for all runs with revised expectations. No pass/fail criterion; this is an exploratory metric for the paper.

### 6.7 Category η: The three-way contact register extended

The three-way register (clean contact, suppressed approach, prediction-error contact) gains a fourth classification at v1.10: **revised-expectation post-contact** — an object for which a `revised_expectation` record has fired and the bias window is active. This is a post-hoc derived classification combining the belief-revision substrate with the counterfactual substrate. An object with: prior suppressed approaches + a prediction-error contact + a revised expectation + post-revision approach acceleration is the fullest possible developmental profile the register can hold at v1.10. Category η at v1.10 succeeds if at least one run per cost condition produces at least one object with all four classifications.

### 6.8 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and δ (Components 1 and 2) all pass.

The claim: the belief-revision observer, introduced as a ninth parallel observer, correctly produces a revised-expectation substrate that the reporting layer reads to generate belief-revision Q3 statements that are auditable, individually variable, and structurally connected to the prediction-error, counterfactual, and provenance substrates. The agent's biographical register now holds, for the first time, a record of what it believed, what it came to believe instead, and whether that revision changed what it did next.

The deeper claim, reserved for v1.11: the revised-expectation record, combined with the v1.9 counterfactual substrate, the v1.8 goal substrate, and the v1.5 prediction-error substrate, establishes the four-substrate basis for causal self-explanation. An agent that can say what it believed, where it held back, what goal it was pursuing, and where it was surprised, can in principle trace a causal chain through those four substrates to produce an account of why its developmental arc took the shape it did. V1.11 tests whether that chain is constructable and auditable. V1.10 establishes that the fourth substrate element — revised expectation — is now in place.

---

## 7. Connection to the SICC trajectory

v1.10 advances two commitments directly and positions the third.

The SICC through-line at this point in the programme is worth stating plainly: v1.8 gave the agent a reason to learn; v1.9 gave it a record of choosing; v1.10 gives it a record of being wrong and changing. These are not merely additive substrate extensions. They are the sequential realisation of what it means for an agent to have a developmental arc it owns rather than an arc that happened to it.

**Commitment 7 (prediction-surprise as the learning signal)** is advanced to its second layer. V1.5 established that the prediction-surprise gap is recorded. V1.10 establishes that it is acted upon — that the record of being wrong modifies subsequent behaviour. The gap between a logbook entry and a learning event is precisely this: the surprise was recorded (v1.5), the resolution was recorded (v1.5), the restraint during the resolution window was recorded (v1.9), and now the revision of behaviour following resolution is recorded (v1.10). Commitment 7 does not say the agent learns from every encounter; it says learning requires the prediction-surprise mechanism. At v1.10 the mechanism is complete at its first layer: prediction, surprise, resolution, revision, behavioural consequence.

**Commitment 8 (self-knowledge as derivative of object-knowledge)** is advanced at its deepest layer so far. The `prior_expectation` and `revised_expectation` fields are object-knowledge fields: they describe what the agent believed about a specific object at a specific step, and what it came to believe instead, in terms derivable from the object's provenance record and the family precondition structure. The agent's self-account now includes an account of how its knowledge of specific objects changed — not in general, but traceably, per object, per encounter. This is self-knowledge in the Winnicottian sense: the agent knows itself through its changed relationship with an object that once surprised it. The self that the biographical register is building is now constituted not only by encounters and restraint, but by revision — the record of a belief that did not survive contact with the world.

**Commitment 11 (the agent's report is auditable, not oracular)** is tested at the belief-revision layer specifically. The `prior_expectation` and `revised_expectation` texts must be traceable to substrate records. A system that produces plausible-sounding belief-revision statements without anchoring them in specific provenance records is, on Commitment 11's account, producing oracular outputs — confident claims whose origins cannot be recovered. Category α at v1.10 closes this gap: the audit trail for belief-revision statements runs through `source_key` → `bundle.belief_revision` record → provenance substrate → mastery formation step. Every link must be traceable or the statement fails Category α.

**Commitment 6 (layered property structure), forward arc: causal self-explanation.** The SICC document locates v1.11's Q5 query in a commitment numbered differently in the forward-arc section than in the formal commitments list — as noted in the v1.9 pre-registration. The forward-arc intent is that v1.10 establishes the belief-revision substrate on which v1.11's causal chain is built. The causal chain for a `resolved_surprise` event reads: *I was surprised at haz_yellow* [prediction-error record] *because att_yellow was not yet mastered* [family precondition record] *because att_yellow was not contacted until step 524* [mastery formation record] *because att_yellow's position was not within my Phase 1 waypoint sequence* [schema + trajectory record]. Each link in that chain exists in the v1.10 substrate. V1.11 constructs and audits the chain.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.10 implementation work begins.

**Matched-seed comparison.** Seeds drawn from `run_data_v1_9.csv` at every (cost, run_idx) cell.

**Pre-flight verifications.** Level 11 re-run passes before Level 12. Level 12 passes before the full v1.10 batch.

**Single-architectural-change discipline.** V1.10 introduces the belief-revision observer and the temporal exclusion window as the two architectural extensions. The temporal exclusion window is a calibration change to an existing observer (V19CounterfactualObserver); it does not introduce new substrate fields or new query types. The belief-revision observer is the singular new cognitive component.

**Preference bias parameter commitment.** `POSITIVE_APPROACH_BIAS = +0.15`, `BIAS_DURATION = 10,000`, `BIAS_DECAY = 5,000` are committed here. If Level-12 C6 (bias_fires) fails — zero revised_expectation records across all 10 verification runs — a bias parameter amendment is not the correct response; a pipeline diagnosis is, since the trigger is deterministic. If the `mean_approach_delta` at full batch is zero or negative, this is reported as a finding (Category δ Component 2 fails), not corrected by parameter adjustment.

**Temporal exclusion parameter commitment.** K_EXCLUSION = 500 is committed here. If Level-12 C7 (temporal_exclusion_effective) fails — mean CF records per run still exceeds 500 — an amendment is warranted. If K_EXCLUSION proves too aggressive (C6 of Level 11 re-run fails: zero CF records), the exclusion window is reduced in an amendment.

**Q3 extended, Q5 reserved.** Belief-revision statements extend Q3. Q5 (causal self-explanation) is reserved for v1.11. The query sequence at v1.10 is Q1, Q2, Q3 (prediction-error + goal outcome + belief-revision), Q4.

**Amendment policy.** Three amendments available. No amendment is provisionally reserved. The most likely amendment candidate is K_EXCLUSION calibration, as N_approach was at v1.9.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 4 May 2026, before any v1.10 code is written.

---

## 9. Stopping rule

The v1.10 iteration completes when:

- Level 11 re-run passes on the v1.10 stack.
- Level 12 passes across all eight criteria.
- The full 40-run batch has run.
- Categories α, β, γ, δ, Φ, ζ, η, and Ω have been characterised in the v1.10 paper.
- The v1.10 paper is drafted.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve and no amendments remain.

---

## 10. New files required

- `v1_10_belief_revision_observer.py` — V110BeliefRevisionObserver; `revised_expectation` record construction from prediction-error + provenance substrates; preference-bias register and per-step bias computation; `get_substrate()` and `preference_bias_log()`
- `v1_10_observer_substrates.py` — monkey-patches `SubstrateBundle` with `belief_revision` field; extends `build_bundle_from_observers()` with `belief_revision_obs` parameter; extends `V16ReportingLayer.query_where_surprised()` with belief-revision statements; applies temporal exclusion window to `V19CounterfactualObserver`; imports v1.9 substrate patches first
- `curiosity_agent_v1_10_batch.py` — batch runner with belief-revision observer active, `--no-belief-revision` flag, flush to `belief_revision_v1_10.csv` and `preference_bias_log_v1_10.csv`
- `verify_v1_10_level12.py` — Level 12 pre-flight: eight correctness criteria across 10 runs at cost=1.0, 80,000 steps

---

## 11. References

Baker, N.P.M. (2026ae–al) Prior preprints and pre-registrations v1.6–v1.8. See v1.9 reference list.

Baker, N.P.M. (2026am) 'v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026an) 'v1.9.1 Pre-Registration Amendment: Detection Threshold Reduction', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ao) 'Counterfactual Record and Suppressed Approach in a Small Artificial Learner: The Register of What Was Not Done', preprint, 4 May 2026.

Baker, N.P.M. (2026ap) 'v1.10 Pre-Registration: Belief Revision with Consequences', GitHub repository, 4 May 2026.

Baker, N.P.M. (internal record, v0.5 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
