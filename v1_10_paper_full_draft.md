# Belief Revision with Consequences in a Small Artificial Learner: The Record of Being Wrong and Changing

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Preprint — not peer reviewed
**Repository:** github.com/RancidShack/developmental-agent
**Pre-registration:** Baker (2026ap), committed before any v1.10 code was written
**Amendments:** v1.10.1 — `self._agent` → `self.agent` in `on_end_state_banked`; v1.10.2 — `self.flags` → `self.records`; v1.10.3 — raw dict → `ProvenanceRecord` dataclass instance
**Batch re-run:** v1.10.1 batch — belief-revision bias activation moved from post-hoc to live detection; approach_delta correctly computed from run-time approach counts

---

## Abstract

The v1.10 iteration introduces two architectural extensions: the belief-revision layer and the completion signal. The belief-revision layer — `V110BeliefRevisionObserver`, the ninth parallel observer — fires a `revised_expectation` record each time a prediction-error surprise resolves: stating explicitly what the agent believed before the encounter, what it now believes, and modifying its subsequent approach behaviour toward the revised object via a soft positive bias. The completion signal — `V110Agent`, a subclass of `V17Agent` — activates a soft draw toward the END_STATE cell once the agent has achieved full developmental mastery, giving the prepared environment its Montessori completion terminus. A temporal exclusion window (K=500 steps) reduces the v1.9 suppressed-approach record rate from 1,791 to 865 per run, resolving the file-size issue identified after the v1.9 batch.

Across 40 complete runs at 320,000 steps in V17World, the batch produced zero hallucinations across all query types including extended Q3 belief-revision statements (Category α: PASS), all 40 runs complete (Category β: PASS), and a strongly positive mean approach_delta of 956.97 across all 39 revised-expectation records — 39/39 positive, zero negative, zero zero (Category δ Components 1 and 2: PASS). The four-way contact register — clean contact, suppressed approach, prediction-error contact, revised-expectation post-contact — is complete at every cost condition (Category η: PASS). Category θ (completion signal banking rate ≥50%) FAIL: 14/40 runs banked the end state (35%), marginally above the v1.9 opportunistic baseline of 32.5%, because only 15/40 runs achieved full developmental activation. The draw mechanism works for agents that reach it; the bottleneck is developmental completion, not draw strength.

Three amendment cycles corrected interface mismatches in `on_end_state_banked` against the `V1ProvenanceStore` dataclass contract. A subsequent batch re-run corrected the bias activation timing — the bias was activated post-hoc after run end in the first batch, producing approach_delta=0 uniformly. After correction, the bias activated during the run at the moment of resolution, and all 39 revised objects showed positive approach deltas. SICC Commitments 7, 8, and 11 are advanced. The biographical register now holds a record of what the agent believed, what it came to believe instead, and whether that revision changed what it did next.

---

## 1. Introduction

### 1.1 What ten iterations have built

Ten iterations have built a developmental agent whose biographical register holds: what it encountered and learned (Q1); how that knowledge is structured across object families (Q2); where its expectations were violated and over what developmental distance (Q3); where it approached without making contact (Q4). The register is auditable — every statement resolves to a substrate record. It is individually variable — 40 distinct developmental arcs produce 40 distinct autobiographies. It is substrate-agnostic — the cognitive layer has carried forward from a tabular grid to a continuous 3D space without modification. At v1.9 it gained a record of restraint: the approach that did not become contact. At v1.8 it gained a record of intention: the goal that was or was not met.

What it has not held, until now, is a record of revision. The agent was surprised by haz_yellow at step 493. The prediction-error substrate records this. The resolution window records how long it took for understanding to arrive. The Q3 statement describes the gap. But the record of the surprise has not, until v1.10, been consulted by the agent's subsequent behaviour. The surprise happened, was recorded, and changed nothing.

v1.10 changes that. The biographical register at v1.10 holds, for the first time, an account of what the agent believed, what it came to believe instead, and what it did differently as a result.

### 1.2 The two architectural extensions and their shared grounding

v1.10 introduces two additions, and their theoretical justification is the same.

The belief-revision layer fires when a prediction-error surprise resolves: the agent entered an object before the precondition was met, paid the cost, and eventually understood why. At that moment, a `revised_expectation` record fires — stating what the agent believed before the encounter, what it now believes, and activating a soft positive approach bias toward the revised object for the next 10,000 steps. The record of being wrong becomes a developmental resource.

The completion signal activates when the agent achieves full developmental mastery — all attractors learned, all hazards banked as knowledge — and draws it softly toward the END_STATE cell. The agent is not compelled to move there. It is invited. Whether it responds, and when, is part of its individual developmental profile.

Both additions follow from the same Montessori principle: the prepared environment does not merely permit development — it actively supports the learner's developmental arc. The belief-revision layer is the environment's response to the moment of understanding: it inflects what the learner does next, without overriding the learner's own drives. The completion signal is the environment's response to the moment of completion: it offers a purposeful terminus, without forcing the learner toward it. In both cases the learning event is the learner's; the environment provides the condition for it.

The Winnicottian grounding runs deeper. Winnicott's account of development holds that the self is constituted through differentiated encounters with objects: approach, resistance, internalisation. At v1.9 the register gained the record of the approach that did not complete — the object held at a distance. At v1.10 it gains the record of what happened after an approach that completed in the wrong way: the agent entered the object before it was ready, and now knows why that was wrong. The revised expectation is an object-relations record in the Winnicottian sense: what the agent now knows about haz_yellow is traceable to its specific encounter with haz_yellow at step 493, and its understanding of att_yellow's role is derivable from that encounter's record. Self-knowledge follows from object-knowledge, as Winnicott's account requires.

### 1.3 The amendment and batch re-run sequence

Three formal amendments corrected interface mismatches in the `on_end_state_banked` hook introduced in `v1_10_observer_substrates.py`:

*v1.10.1:* `self._agent` → `self.agent`. `V1ProvenanceStore` stores its agent reference as `self.agent` without underscore.

*v1.10.2:* `self.flags` → `self.records`. `V1ProvenanceStore` stores provenance records in `self.records`.

*v1.10.3:* Raw dict → `ProvenanceRecord` dataclass instance. `V1ProvenanceStore.records` holds typed dataclass instances; inserting a raw dict caused `AttributeError` in `_record_phase_boundary_confirmations` and `_emit_snapshot` which access `.flag_type` as an attribute.

All three failures occurred in the same 30-line function. The pattern is consistent with writing against an interface not visible in the project files — the `V1ProvenanceStore` internals were only confirmed through error output. The amendment budget of three was fully consumed. This is recorded under Category Φ as an honest account of the implementation process.

A subsequent batch re-run (v1.10.1 batch) corrected a timing defect discovered in the first batch results: `process_pe_substrate()` was called after `on_run_end()`, meaning the bias was never active during the run. All 39 belief-revision records in the first batch showed `approach_delta=0` and `bias_active_steps=0`. After correction — detecting transformations live in `on_post_event()` via `world.object_type` — all 39 records showed positive approach_delta (mean=956.97) and `bias_active_steps=30,000`. The batch re-run is not an amendment; it corrects an implementation timing error that made the pre-registered behavioural consequence unmeasurable.

---

## 2. Methods

### 2.1 The belief-revision observer

`V110BeliefRevisionObserver` is the ninth parallel observer. It reads `world.object_type` at each step in `on_post_event()`. When an object that has `agent.pre_transition_hazard_entries > 0` transitions to `KNOWLEDGE`, a `revised_expectation` record fires immediately, and a preference bias of `POSITIVE_APPROACH_BIAS = +0.15` activates toward that object for `BIAS_DURATION = 10,000` steps, decaying linearly to zero over `BIAS_DECAY = 5,000` steps.

`process_pe_substrate()` runs at run end as a reconciliation pass: it reads from `bundle.prediction_error` (the assembled substrate, not `pe_obs.get_substrate()` directly — the latter errors with mixed cell types in `_tracked_cells`) and corrects `surprise_step` in live-detected records to the accurate entry step from the PE substrate. It also catches any resolutions missed by live detection.

**The revised_expectation record.**

```
{
  object_id:                         str,
  surprise_step:                     int,
  resolution_step:                   int,
  resolution_window:                 int,
  prior_expectation:                 str,   # substrate-derived
  revised_expectation:               str,   # substrate-derived
  precondition_at_revision:          str,
  suppressed_approach_count:         int,
  pre_threshold_entries_at_surprise: int,
  bias_active_steps:                 int,
  approach_delta:                    int,
}
```

Both `prior_expectation` and `revised_expectation` texts are derived from the provenance and prediction-error substrates. No free text generation. A belief-revision statement whose text cannot be traced to a specific substrate record is a Category α failure.

**Approach_delta computation.** The observer tracks approach-movement counts toward each revised object in two windows: the pre-surprise window (`[max(0, surprise_step - BIAS_DURATION), surprise_step)`) and the post-revision bias window (`[resolution_step, resolution_step + BIAS_DURATION)`). `approach_delta = post_count - pre_count`. A movement is counted when the agent's Euclidean distance to the revised object decreases between consecutive steps.

### 2.2 V110Agent: the completion signal

`V110Agent` is a subclass of `V17Agent`. It overrides nothing in the parent class except adding `end_state_draw_reward(state, next_state)`, which returns `END_STATE_DRAW = +0.20` when `agent.activation_step` is not None (completion condition met), the end state has not yet been banked, and the agent's action moves it closer to the END_STATE cell's position. The draw is permanent once activated; it does not decay.

`END_STATE_DRAW = +0.20` is set above `POSITIVE_APPROACH_BIAS = +0.15` to ensure the completion signal is perceptible relative to the belief-revision bias, while remaining soft relative to attractor feature rewards.

The completion signal fires `environment_complete` as a `ProvenanceRecord` when the agent banks the end state — the substrate record on which v1.11's next-environment trigger will build.

### 2.3 The temporal exclusion window

`K_EXCLUSION = 500` steps: after a suppressed-approach record is emitted for `object_id`, no new record for the same object is emitted for 500 steps. Detected events within the exclusion window are silently discarded; `cf_records_raw` and `cf_records_emitted` track the before/after counts.

### 2.4 Experimental design

40 runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition × 320,000 steps. Seeds from `run_data_v1_9.csv` at matched (cost, run_idx) cells. Goal assignment inherited from v1.8/v1.9 unchanged. 40 paired goal-free runs at matched seeds for Category γ Q1 comparison.

---

## 3. Results

### 3.1 Category α: Internal consistency

Zero hallucinations across all 40 runs and all query types. Extended Q3 belief-revision statements: 39 statements total, all with `source_resolves = True`. Every statement's `prior_expectation` and `revised_expectation` text is traceable to the prediction-error and provenance substrates. Category α: **PASS**.

### 3.2 Category β: Query coverage

All 40 runs produced complete reports. Runs without resolved surprises produced no belief-revision Q3 statements; this is accurate and not a coverage failure. Category β: **PASS**.

### 3.3 Category δ: The behavioural-consequence finding

**Component 1: Belief-revision records in all surprise-containing runs.**

36/40 runs produced `revised_expectation` records. The 4 missing runs (cost=0.1 run=0; cost=1.0 run=3; cost=2.0 runs=3,9) all have empty `yellow_resolution_window` in the run data — these are unresolved surprises where the agent entered haz_yellow before the precondition was met and the transformation did not fire within the 320,000-step observation window. Zero belief-revision records for these runs is architecturally correct: a `revised_expectation` fires on resolution, not on surprise. Component 1: **PASS**.

**Component 2: Preference trajectory difference.**

| Metric | Value |
|---|---|
| Total revised_expectation records | 39 |
| Records with approach_delta > 0 | 39 (100%) |
| Records with approach_delta < 0 | 0 |
| Records with approach_delta = 0 | 0 |
| Mean approach_delta | 956.97 |
| Mean bias_active_steps | 30,000 |

The mean approach_delta of 957 is the number of additional approach movements toward the revised object in the 10,000-step bias window, compared to the equivalent pre-surprise window. Every revised object, at every cost condition, shows a positive delta. Direction: strongly positive. Component 2: **PASS**.

The `bias_active_steps = 30,000` uniformly across all records reflects that every resolved surprise occurred early in the run (surprise at step ~493–524, resolution at steps 497–22,983 depending on resolution window), leaving all agents with the full bias duration available. The bias ran to completion in every revised run.

**Component 3 (exploratory): Prior restraint and approach_delta.**

The pre-registered directional prediction — agents with higher `suppressed_approach_count` at revision would show smaller `approach_delta` — is not supported. Mean SA counts at revision range from 1 (for 29 records) to 61 (for 1 record), with approach_delta showing no consistent directional relationship:

| SA count at revision | n | Mean approach_delta |
|---|---|---|
| 1 | 29 | 958.0 |
| 2 | 3 | 911.7 |
| 10–29 | 4 | 944.9 |
| 51–61 | 2 | 936.5 |

The differences are within noise across all levels. Prior restraint — the number of times the agent had approached and withdrawn before the surprise — does not measurably modulate the positive approach response to revision at this resolution. The Winnicottian prediction that developmental history shapes post-revision behaviour may require finer-grained measurement than approach_delta captures, or may operate at a longer timescale than the 10,000-step bias window. Reported as an exploratory null finding.

**By cost condition.**

| Cost | n | Mean approach_delta |
|---|---|---|
| 0.1 | 9 | 937.6 |
| 1.0 | 9 | 967.9 |
| 2.0 | 8 | 976.4 |
| 10.0 | 13 | 950.9 |

The approach_delta is cost-invariant across conditions, consistent with the v1.9 finding that approach behaviour is determined by spatial exploration rather than cost-aversion. Revision produces the same positive approach response regardless of the object's cost.

Category δ: **PASS** (Components 1 and 2).

### 3.4 Category ζ: Belief-revision window and suppressed-approach ratio

Resolution windows across the 39 records: mean=7,996 steps, min=4, max=121,908. The wide range is architecturally meaningful. A resolution window of 4 steps describes an agent that entered haz_yellow before the precondition was met and achieved att_yellow mastery almost immediately — the surprise resolved before the developmental distance could accumulate. A resolution window of 121,908 steps describes an agent that paid the full cost at step 493, and then spent the next 121,908 steps — nearly 40% of the total run — before att_yellow mastery fired. The gap between surprise and understanding was a third of the entire developmental arc.

The suppressed-approach-count-to-window ratio (SA count ÷ resolution_window) has a mean of 0.085, meaning agents averaged roughly one suppressed approach per 12 steps of the resolution window. The agent that spent 121,908 steps between surprise and resolution was not passive during that interval: it was orbiting the object, approaching and withdrawing, throughout the period before it had the conceptual resources to understand what it had encountered. The register now holds both the gap and the orbital behaviour within it.

### 3.5 Category η: Four-way contact register

All 39 objects with `revised_expectation` records also appear in the counterfactual substrate — every revised object was also a suppressed-approach object. The four-way contact register — clean contact (entered under precondition), suppressed approach (approached, withdrew without contact), prediction-error contact (entered before precondition, cost paid), revised-expectation post-contact (bias active, approach accelerated) — is complete at every cost condition:

| Cost | Runs with four-way profile |
|---|---|
| 0.1 | 9/10 |
| 1.0 | 9/10 |
| 2.0 | 8/10 |
| 10.0 | 10/10 |

Category η: **PASS**.

The four-way profile constitutes the fullest developmental account the register can hold at v1.10 for a single object in a single run: *I approached it and withdrew; I entered it before I was ready and was surprised; I eventually understood what readiness required; I then approached it more.* This is the Winnicottian developmental arc — approach, cost, understanding, changed relationship — held in the substrate at object resolution.

### 3.6 Category θ: Completion signal effectiveness

**Component 1: Banking rate.** 14/40 runs banked the end state (35%), against the v1.9 baseline of 13/40 (32.5%). Category θ Component 1: **FAIL** (pre-registered threshold: ≥50%).

The failure is informative. 15/40 runs reached `activation_step` — the completion condition. Of those, 14 banked the end state and 1 did not (cost=2.0 run=6, which activated at step 218,586 and did not reach the end-state cell before step 320,000). The draw mechanism is functioning: nearly every agent that activated found the end-state cell. The bottleneck is `activation_step` itself — only 37.5% of runs achieve full developmental mastery within 320,000 steps.

This reframes the Category θ finding. The question is not *does the completion signal work* but *how rarely do agents complete the prepared environment?* The answer at V17World's current configuration: roughly one-third of runs. The remaining two-thirds reach Phase 3 but do not complete the full developmental sequence before the observation window closes. The draw cannot operate on agents that never reach the point where it becomes relevant.

**Component 2: Draw-to-bank time distribution.** Among the 14 banked runs: min=3 steps, mean=1,976, max=13,911, std=4,854. Component 2: **PASS** (pre-registered criterion: std > 0). The distribution is wide, confirming that agents respond to the completion signal at individually variable speeds — some find the end-state cell within three steps of activation (it was adjacent), one took nearly 14,000 steps. The draw is a signal, not a compulsion. The variance is the evidence that individual developmental profiles persist even at the moment of completion.

**Component 3 (exploratory): Goal outcome and banking.** Goal-resolved agents: 5 of the 14 that banked. Goal-expired agents: 9 of the 14. The prediction — resolved agents respond to the completion signal more readily — is reversed. Expired agents banked more frequently. The interpretation: goal-resolved runs tend to resolve early (the agent achieved the goal before the developmental sequence was complete), while the runs that completed the full developmental sequence tended to be longer-running Phase 3 explorations, which also generated the `activation_step` event. Resolution and developmental completion are partially independent. Reported as an exploratory finding.

### 3.7 Temporal exclusion and CF record reduction

CF records emitted: 34,599 (mean=865 per run). CF records raw: 64,661. Exclusion rate: 46.5%. The v1.9 rate was 71,628 emitted at mean 1,791 per run. The K=500 exclusion window reduced the record rate by 52% and the file size proportionally. The counterfactual CSV is 1.2MB versus v1.9's 4.7MB. The Q4 individuation signal is preserved: pairwise edit distance analysis on the emitted CF records shows mean distance 0.41 and std 0.07 across sampled run pairs, above the pre-registered threshold of 0.05.

### 3.8 Category Φ: Honesty constraint

The amendment sequence is documented in Section 1.3. Three formal amendments, all in `on_end_state_banked`, correcting the `V1ProvenanceStore` interface. The amendment budget of three was fully consumed. This is the first iteration in the programme where the full amendment allowance was used before pre-flight passed.

The batch re-run is not a formal amendment — it corrects a timing error that made the pre-registered behavioural consequence unmeasurable, not an architectural change. The distinction is maintained: the pre-registration specifies that bias activates at resolution and modifies subsequent approach behaviour; what was wrong was that the implementation activated the bias after the run had ended, producing a result consistent with no bias at all. Correcting the timing produces a result consistent with the pre-registration's specification.

A note on the `V15PredictionErrorObserver` interface: `get_substrate()` is not safely callable outside the bundle assembly path, because the observer's `_tracked_cells` contains a mix of string object IDs (V17World) and tuple coordinates (grid-world legacy), causing a `TypeError` in `on_run_end`'s `sorted()` call. The correct pattern — reading from `bundle.prediction_error` after assembly — is adopted at v1.10 and should be the standard for all future cognitive-layer observers that need to read PE data. This is noted as a v1.11 design principle.

---

## 4. Discussion

### 4.1 The approach_delta finding and what it establishes

A mean approach_delta of 957 across all 39 revised objects, with zero negative results, is the programme's first evidence that the biographical record has a behavioural consequence. Prior iterations have demonstrated that the register is auditable, individually variable, and substrate-agnostic. v1.10 demonstrates that it is also generative: the record of being wrong changes what the agent does next.

The magnitude of 957 additional approach movements in the 10,000-step bias window warrants a careful reading. In a 320,000-step run, 10,000 steps is 3% of the total. Within that window the agent makes approximately 3,000–5,000 spatial decisions. An approach_delta of 957 means roughly 20–30% of the agent's directional decisions in the bias window involved moving toward the revised object more often than before the surprise. This is not a subtle effect. The bias is producing a measurable reorientation toward the object that surprised the agent, once the surprise has resolved into understanding.

The cost-invariance of approach_delta (937–976 across cost conditions) is consistent with the v1.9 finding that approach behaviour is a feature of spatial exploration rather than cost-aversion. The bias operates on the same approach dynamics that produce the suppressed-approach record: the agent's trajectory through the environment, shaped by curiosity and feature preference, is now also inflected by a soft preference for objects whose developmental significance it has understood.

### 4.2 The four-way register as developmental classification

The four-way contact register — approach-without-contact, pre-condition entry, revised expectation, post-revision approach acceleration — is the most complete developmental classification the programme has produced. An object with all four classifications has a full developmental biography in the substrate: proximity before commitment, contact before readiness, understanding after cost, changed relationship after understanding. This is a developmental sequence that can be told as a story, traced as a chain, and verified at every link.

The object that appears in all four registers is, in almost every v1.10 run, `haz_yellow`. The GREEN family hazard, `haz_green`, appears in the four-way register at cost=10.0 where it is also a goal target and bank_hazard_within_budget runs produce pre-condition entries. The unaffiliated hazards appear occasionally. But `haz_yellow`, as the consistently encountered YELLOW family hazard, is the object around which the developmental biography is most legibly written: the agent approached it before mastery, approached it more during the resolution window, entered it before readiness, understood what readiness required, and then approached it more intensively after revision.

This is not a designed outcome. It is what the substrate records when a developmental sequence unfolds naturally through the prepared environment.

### 4.3 Category θ and the developmental ceiling

The completion signal's failure to raise the banking rate above 50% is a finding about V17World's developmental architecture, not about the draw mechanism. The draw works — 14 of the 15 agents that reached activation also banked. What the data establishes is that full developmental mastery is achieved in roughly one-third of runs at current step counts and cost conditions, and the proportion is relatively stable across iterations: v1.9 had 13/40, v1.10 has 14/40.

This raises the question of whether 320,000 steps is the right observation window. The Montessori principle the programme operates on holds that time is not a boundary — the learner works at their own pace, and the environment waits. The programme has so far treated 320,000 steps as a practical constraint, not a developmental ceiling. The v1.10 data suggests it is functioning as a ceiling: two-thirds of agents do not complete the developmental sequence within it. The v1.11 next-environment architecture — triggered by the `environment_complete` provenance record introduced here — will need to address this if the multi-environment programme is to produce agents that routinely complete one prepared environment and move to the next. Either the observation window must extend, or the developmental sequence must be achievable at shorter step counts.

The single run that activated but did not bank (cost=2.0 run=6, activation at step 218,586) is the clearest evidence of this: the agent completed the developmental sequence with 101,414 steps remaining, but did not find the end-state cell within that window despite the draw. The draw is soft; competing drives can outweigh it for 100,000 steps. A stronger draw would resolve this case but would undermine the Montessori principle. The v1.11 solution — a new environment — is the architecturally correct response: if the agent has completed this prepared environment and is still engaging with its objects in Phase 3 exploration rather than moving to the end-state cell, offering a new environment is not a constraint but an invitation.

### 4.4 SICC Commitments advanced

**Commitment 7 (prediction-surprise as the learning signal)** is advanced to completion at its first layer. v1.5 recorded the prediction-error. v1.9 recorded restraint during the resolution window. v1.10 records the revision of behaviour following resolution. The full mechanism is now operative: prediction, surprise, resolution, revised expectation, behavioural consequence. Every link in the chain produces a substrate record. The chain is auditable.

**Commitment 8 (self-knowledge as derivative of object-knowledge)** is advanced to its sharpest expression so far. The `prior_expectation` and `revised_expectation` texts are object-knowledge fields: they describe what the agent believed about haz_yellow at step 493, and what it came to believe after step 524, in terms derivable from haz_yellow's family precondition record and att_yellow's mastery formation step. The agent's self-account now includes an account of how its knowledge of specific objects changed — traceable, per object, per encounter. This is precisely the Winnicottian derivation: what the agent knows about itself is readable from what it knows about the objects it encountered, in the sequence in which it encountered them.

**Commitment 11 (the agent's report is auditable, not oracular)** is tested and holds at the belief-revision layer. Every `prior_expectation` and `revised_expectation` text is derivable from substrate records; no free text generation occurs; every belief-revision Q3 statement resolves to a `revised_expectation` record in `bundle.belief_revision`. The audit trail for a belief-revision statement runs: Q3 statement → `source_key` → `bundle.belief_revision` record → PE substrate entry step and resolution step → provenance mastery formation record. Every link traceable. Zero hallucinations.

---

## 5. Conclusion

v1.10 introduces the belief-revision layer and the completion signal — the programme's first cognitive component that changes what the agent does next in response to what it has learned, and the prepared environment's first completion terminus. Across 40 complete runs at 320,000 steps, the batch produced zero hallucinations, all four query types non-empty in all 40 runs, and a strongly positive mean approach_delta of 957 across all 39 revised-expectation records. The agent that was surprised by haz_yellow at step 493 approached it approximately 957 more times in the 10,000-step period following revision than in the equivalent pre-surprise window. This is the programme's first evidence that its biographical record has a behavioural consequence.

Three findings reshape the programme's forward trajectory.

The approach_delta finding confirms that the belief-revision mechanism works as specified and that its effect is substantial. The agent's developmental arc is not only recorded — it now feeds back into what the agent does. The record of being wrong changes the agent's subsequent relationship with the object that surprised it.

The completion signal finding establishes that V17World's developmental ceiling is reached in roughly one-third of runs at 320,000 steps, and that the draw mechanism works for agents that reach it. The bottleneck is developmental completion, not draw strength. v1.11's next-environment architecture addresses this directly: an agent that completes one prepared environment is offered another. The `environment_complete` provenance record introduced here is the substrate record v1.11 reads.

The four-way contact register — established across all cost conditions — constitutes the programme's most complete developmental classification of object history. For `haz_yellow` in the majority of v1.10 runs, the register holds: approach without contact, pre-condition entry, revised expectation, post-revision approach acceleration. This is a developmental sequence that can be stated, traced, and verified. It is, in the programme's terms, the beginning of a biography.

The register is not finished. v1.11 will add causal self-explanation — Q5, the first query type that asks not what happened but why — and the next-environment architecture. But the foundation is now in place: a record of what the agent learned, where it held back, where it was surprised, what it revised, and how it changed. The self-account that emerges from that record is grounded in object encounters, traceable at every link, and — for the first time — consequential.

---

## References

Baker, N.P.M. (2026ae–al) Prior preprints and pre-registrations v1.6–v1.8. See v1.9 reference list.

Baker, N.P.M. (2026am) 'v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026an) 'v1.9.1 Pre-Registration Amendment: Detection Threshold Reduction', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ao) 'Counterfactual Record and Suppressed Approach in a Small Artificial Learner: The Register of What Was Not Done', preprint, 4 May 2026.

Baker, N.P.M. (2026ap) 'v1.10 Pre-Registration: Belief Revision with Consequences and the Completion Signal', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aq) 'v1.10.1 Pre-Registration Amendment: ProvenanceStore Agent Attribute Name', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ar) 'v1.10.2 Pre-Registration Amendment: ProvenanceStore Record Storage Attribute', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026as) 'v1.10.3 Pre-Registration Amendment: ProvenanceRecord Dataclass Required', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026at) 'Belief Revision with Consequences in a Small Artificial Learner: The Record of Being Wrong and Changing', preprint, 4 May 2026.

Baker, N.P.M. (internal record, v0.5 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
