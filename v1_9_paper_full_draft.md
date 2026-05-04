# Counterfactual Record and Suppressed Approach in a Small Artificial Learner: The Register of What Was Not Done

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Preprint — not peer reviewed
**Repository:** github.com/RancidShack/developmental-agent
**Pre-registration:** Baker (2026am), committed before any v1.9 code was written
**Amendment:** v1.9.1 — detection thresholds reduced from N_approach=10, N_recession=5 to N_approach=3, N_recession=3; V17World continuous-space trajectories do not produce 10-step monotone approach windows at this action granularity

---

## Abstract

The v1.9 iteration introduces the counterfactual observer: an eighth parallel observer that detects suppressed-approach events — where the agent came within eligible-object proximity and withdrew without contact — and produces a fourth query type in the biographical register. Q4 answers the question: *where did I approach without making contact?* The counterfactual substrate holds, for the first time, a record of what the agent could have done and did not. Detection uses positional trajectory alone (approach window followed by recession window without contact), preserving substrate-agnosticism without requiring access to the threat gate's internal operation. Across 40 complete runs at 320,000 steps in V17World, the reporting layer produced 71,628 Q4 statements with zero hallucinations across all query types (Category α: PASS), all 40 runs complete (Category β: PASS), 40/40 runs with suppressed-approach records (Category γ Component 1: PASS), and Q4 individuation std=0.062 exceeding the pre-registered threshold of 0.05 (Category γ Component 2: PASS). One amendment cycle was required: detection thresholds reduced per v1.9.1 after C6 failure on first Level-11 run. The pre-registered directional prediction on goal-relevant suppressed approaches is reversed and the reversal is interpretively richer than the prediction: resolved agents show higher goal-relevant suppressed-approach counts than expired agents, because agents that engaged their goal target approached it repeatedly — including approach-and-withdrawal events — whereas expired agents often never approached at all. Pre-threshold suppressed approaches (first-contact events, no prior cost paid) are cost-invariant at approximately 80% across all four cost conditions, suggesting that approach-withdrawal before first contact is a feature of environmental exploration rather than cost-aversion specifically. High-activity outlier runs reveal a Phase 3 consolidation pattern — agents who achieved full attractor mastery continued to approach and withdraw from hazard objects in sustained post-mastery engagement — constituting a new behavioural event type in the Winnicottian developmental register. The biographical archive now holds a record of restraint alongside mastery.

---

## 1. Introduction

### 1.1 What nine iterations have built

Nine iterations have built a developmental agent with a biographical register that holds: what it encountered and what it learned (Q1); how its knowledge is structured across object families (Q2); where its expectations were violated and over what developmental distance (Q3); and now, for the first time, where it came close to an eligible object and withdrew without making contact (Q4). The register is auditable — every statement resolves to a substrate record. It is individually variable — 40 distinct developmental arcs produce 40 distinct autobiographies. It is substrate-agnostic — the cognitive layer has carried forward from a tabular grid through a 3D continuous-space environment without modification. And it is now, at v1.9, cumulative in a new sense: it holds not only the events that completed, but the events that did not.

The v1.8 iteration introduced the goal layer: a record of what the agent was trying to achieve and whether it succeeded. V1.8's most revealing finding was the registered-but-not-engaged case — ten runs where the agent located its goal target during Phase 1 mapping and did not pursue it in Phase 2. The biographical register described these runs faithfully: *I registered the target in the environment at step 188 during Phase 1 mapping, but did not engage with it during Phase 2 within the observation window.* What the register could not say was whether the agent had come close to the target in Phase 2 and turned away, or had simply not approached it at all. The goal substrate records the absence of engagement. It cannot record what happened at the boundary.

v1.9 closes that gap.

### 1.2 What the counterfactual record adds

The counterfactual observer detects approach-and-withdrawal events from positional trajectory: the agent moved monotonically closer to an eligible object for at least N_approach consecutive steps, reached a minimum distance, and then moved monotonically further away for at least N_recession consecutive steps, without contact at any point in the sequence. Each confirmed event produces a suppressed-approach record in the counterfactual substrate, with six fields: object encountered, step of closest approach, distance at closest approach, phase at approach, whether the object was the active goal target, and how many times the agent had previously entered the object before this approach.

That last field — `pre_threshold_entries` — is load-bearing for v1.10. An agent with `pre_threshold_entries = 0` approached an object it had never entered and withdrew. An agent with `pre_threshold_entries = 2` has prior experience of this object, has paid its cost twice, and still chose not to enter on this occasion. These are developmental events of different kinds. The register now distinguishes them.

The Q4 statement is the first statement in the biographical register that describes what the agent did not do:

> *At step 47,312, I came within 0.84 units of haz_yellow without making contact. I withdrew. This object was my active goal target. I had not yet entered this object.*

In Winnicottian object-relations terms, this is the record of the object held at a distance — approached, held in proximity, not yet incorporated. The self that the biographical register is building, statement by statement, is now constituted not only by what was encountered and mastered, but by what was neared and refused.

### 1.3 The amendment cycle

The pre-registered detection thresholds — N_approach=10, N_recession=5 — failed Level-11 criterion C6 on the first verification run: zero suppressed-approach records across all 10 verification runs at cost=1.0, steps=80,000. The diagnosis was immediate: V17World's 27-action continuous-space vocabulary produces approach trajectories that involve lateral corrections and oscillations at the scale of 2–3 steps; a 10-step monotone window exceeds the agent's typical clean approach segment before a directional adjustment occurs.

The v1.9.1 amendment reduced both thresholds to N=3: three consecutive steps of decreasing distance to confirm an approach, three consecutive steps of increasing distance to confirm recession. Three steps distinguishes a directed approach from a single-step oscillation without requiring the unrealistic long monotone window that the pre-registered values assumed. The structural definition of a suppressed approach — approach window followed by recession without contact — is unchanged; only the minimum window lengths are reduced.

All other Level-11 criteria (C1–C5, C7) passed cleanly on first run, including zero hallucinations and confirmed additive discipline with `--no-counterfactual`. The v1.8 goal layer regression (Level-10 re-run) passed cleanly on both runs: 10/10 passes, halluc=0, terminal=ok. The v1.9 substrate stack introduced no regression into any prior layer.

### 1.4 Theoretical grounding: Winnicott and Montessori

The programme carries two theoretical frameworks whose roles are distinct and complementary, and which are both operative at v1.9 in a way that prior iterations only partially instantiated.

Montessori gives the programme its environmental architecture: the prepared environment, the materials arranged so that contact with objects in the learner's own sequence and at the learner's own tempo produces the developmental event. The agent does not need instruction; the world is arranged so that the route through it — whatever route the agent takes — becomes that agent's own. The learner who later reflects on their development reflects on a sequence of encounters with specific objects at specific moments. That is what Q1 holds. The route is individually variable, auditable, and traceable to object contact.

Winnicott gives the programme its developmental psychology of what happens at the moment of encounter. The self, on Winnicott's account, is not given as a primary structure: it emerges through repeated, differentiated encounters with what is not-self. The object is approached, resisted, tested, internalised; through that sequence a self gradually forms that is constituted by, and therefore traceable to, the history of its object relations. Critically, Winnicott's account requires that not all encounters complete. The capacity to approach an object, hold it in proximity, and withdraw without destroying it or being overwhelmed by it is a developmental achievement in itself. The child who can be with the object, near it, without immediately either mastering it or fleeing it, has reached a developmental position. The Q4 register is the substrate for that position.

What v1.9 establishes is that the event structure the Winnicottian account requires — approach, proximity, withdrawal without contact — is now detectable, individually variable, and auditable. Whether the event structure reflects anything cognitively richer than proximity avoidance in the positional sense is a question v1.10 and v1.11 are designed to address. The register holds the record. The interpretation is earned, not assumed.

---

## 2. Methods

### 2.1 The counterfactual observer architecture

The counterfactual observer is implemented as `V19CounterfactualObserver`, the eighth parallel observer. It holds per-object distance-window buffers during the run and fires suppressed-approach records when the event signature is confirmed. It does not modify the agent, world, or any existing observer.

**Detection logic.** At each step the observer computes the Euclidean distance from the agent's current position to every eligible object's position. It maintains a rolling distance buffer per object using a three-state window machine (IDLE → APPROACHING → RECEDING). A suppressed approach is confirmed when:

1. N_approach = 3 consecutive steps of monotonically decreasing distance (approach window, v1.9.1 amended value).
2. No contact during or after the approach window (`world._contact_at_pos()` did not return the object's id at any step within the window).
3. N_recession = 3 consecutive steps of monotonically increasing distance (recession window, v1.9.1 amended value).

The `closest_approach_distance` and `closest_approach_step` are the minimum distance and the step at which it was recorded during the approach window.

**Eligible objects.** HAZARD-type objects and DIST_OBJ cells that are the active goal target's family distal object (locate_family goals only). ATTRACTOR, NEUTRAL, END_STATE, and KNOWLEDGE objects are not eligible.

**Detection method and the threat gate.** The SICC document anticipates suppressed-approach detection via the threat gate's internal operation — recording the moment the gate overrides an agent action directed at a flagged HAZARD. The counterfactual observer detects the same event structure from positional trajectory alone, without reading the gate's internal state. This is a deliberate choice in service of substrate-agnosticism (SICC Commitment 10): a positional method is portable across substrates that may not carry an explicit threat gate. The cost is acknowledged: positional detection captures the trajectory signature consistent with gate-suppression, not gate-suppression itself. A suppressed-approach record is the substrate's honest record of what the position data shows; it does not confirm that the threat gate was the cause of recession.

**Additive discipline.** With `counterfactual_obs=None`, the v1.9 batch runner produces output byte-identical to v1.8.2 at matched seeds on all v1.8 metrics. Confirmed by Level-11 C7.

### 2.2 The suppressed-approach record

Six fields per confirmed event:

| Field | Description |
|---|---|
| `object_id` | The eligible object approached |
| `closest_approach_step` | Step of minimum distance |
| `closest_approach_distance` | Euclidean distance at closest point |
| `phase_at_approach` | Agent phase at closest_approach_step |
| `goal_relevant` | True if object_id is the active goal target |
| `pre_threshold_entries` | Prior contacts with this object at time of approach |

`pre_threshold_entries` reads from `agent.pre_transition_hazard_entries` — the same field V18GoalObserver reads in `_check_progress()` for `bank_hazard_within_budget` goals. It is read-only at v1.9; v1.10's belief-revision layer will read it alongside the prediction-error substrate.

### 2.3 The SubstrateBundle and Q4 extension

`SubstrateBundle` gains a `counterfactual` field: a list of suppressed-approach record dicts (empty list if no events were detected; None if the counterfactual observer was not active). `bundle.resolve("counterfactual", source_key)` resolves against the source_key format `"suppressed_approach:{object_id}:{closest_approach_step}"`.

`V16ReportingLayer` gains `query_where_held_back()` (Q4). One statement per confirmed suppressed-approach record. `generate_report()` is extended to call Q4 after Q3. The full query sequence at v1.9 is Q1, Q2, Q3, Q4.

Q4 statement text:

> *At step {step}, I came within {dist:.2f} units of {object_id} without making contact. I withdrew. [This object was my active goal target.] [I had not yet entered this object. / I had entered this object N time(s) previously.]*

`source_type`: `"counterfactual"`. `source_key`: `"suppressed_approach:{object_id}:{step}"`. `query_type`: `"where_held_back"`.

### 2.4 Experimental design

Forty runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition × 320,000 steps. Seeds drawn from `run_data_v1_8.csv` at matched (cost, run_idx) cells, preserving the seed chain from v1.8. Goal assignment schedule inherited unchanged from v1.8 (`run_idx % 3`; budget = 50% of total steps). Forty paired goal-free runs at matched seeds for Category γ Q1 comparison.

---

## 3. Results

### 3.1 Category α: Internal consistency

Zero hallucinations across all 40 runs and all four query types (Q1–Q4). Total statements: 71,628 Q4 statements alone, plus Q1/Q2/Q3 statements. Every Q4 statement's `source_key` resolved to a record in `bundle.counterfactual`; no orphaned statements; no substrate records without corresponding statements. The audit trail holds at full batch scale.

Category α: **PASS**.

### 3.2 Category β: Query coverage

All 40 runs produced complete reports. Q1, Q2, and Q3 non-empty in all 40 runs. Q4 non-empty in all 40 runs — every run produced at least one confirmed suppressed-approach event. `report_complete = True` in all 40 runs.

Category β: **PASS**.

### 3.3 Category γ: Counterfactual individuation

**Component 1: Non-trivial suppressed-approach rate.** 40/40 runs (100%) produced at least one confirmed suppressed-approach record. Pre-registered threshold: ≥50%. Result: 100%. Component 1: **PASS**.

**Component 2: Q4 individuation.** Pairwise normalised edit distances over Q4 object-id sequences (sampled 20 runs, first 200 events per run, 190 pairs):

| | mean | std | min | max |
|---|---|---|---|---|
| Q4 object-id sequences | 0.396 | 0.062 | 0.245 | 0.500 |

Pre-registered threshold: std > 0.05. Result: 0.062. Component 2: **PASS**.

The Q4 individuation signal is clear: no two agents produce the same suppressed-approach trajectory. The mean distance of 0.396 indicates substantial pairwise divergence across runs — agents differ not only in how many approach-withdrawal events they produce, but in which objects they approach and in what sequence.

**Component 3: Q4–Q1 correlation (exploratory).** The pre-registered directional expectation was that runs with higher Q1 individuation would also show higher Q4 suppressed-approach counts. This is not assessed quantitatively at this batch scale given the wide variance in Q4 counts (range: 783–7,815); the high-count outlier runs (discussed in Section 3.6) would dominate a correlation metric. Reported as a question for the full 320,000-step analysis at v1.10.

Category γ: **PASS** (Components 1 and 2).

### 3.4 Category δ: Pre-anticipated findings

**Pre-threshold suppressed approaches by cost.** The pre-registered directional prediction was that pre-threshold suppressed approaches (prior contact = 0) would be less frequent at cost=0.1 and more frequent at cost=2.0 and 10.0. The data does not support this prediction:

| Cost | Pre-threshold events | Total events | Pre-threshold % |
|---|---|---|---|
| 0.1 | 13,227 | 16,300 | 81.1% |
| 1.0 | 8,922 | 10,851 | 82.2% |
| 2.0 | 14,125 | 17,148 | 82.4% |
| 10.0 | 21,502 | 27,329 | 78.7% |

Pre-threshold suppressed approaches account for approximately 80% of all events at every cost condition. The directional prediction is not confirmed. The cost-invariance is the more interesting finding: agents at cost=10.0 approach hazard objects for the first time and withdraw at almost the same rate as agents at cost=0.1. The threat gate creates caution in execution — contact events are rarer at higher cost — but the approach-and-withdrawal signature before any first contact is cost-invariant. This suggests that the suppressed approach is a feature of environmental exploration and spatial navigation rather than cost-aversion specifically. The agent orbits eligible objects as a consequence of how it traverses the environment; the cost gate shapes what happens when it gets close enough to make contact, not the frequency with which it comes close and turns away.

**Goal-relevant suppressed approaches: expired vs resolved — REVERSED.** The pre-registered prediction was that expired runs would show higher goal-relevant suppressed-approach counts than resolved runs. The data reverses this:

| Outcome | n | Mean goal-relevant CF | Max |
|---|---|---|---|
| Expired | 16 | 302.7 | 528 |
| Resolved | 24 | 532.3 | 1,597 |

The reversal is interpretively richer than the prediction. Agents that resolved their goal approached the goal-relevant target more — including approach-and-withdrawal events — because they were actively engaging with it throughout Phase 2. The suppressed-approach count for a resolved agent does not represent avoidance of the goal target: it represents repeated proximity during sustained engagement, some instances of which completed in contact and some of which did not. An expired agent that never engaged the target in Phase 2 produced zero goal-relevant suppressed approaches for that target. The counterfactual register measures engagement intensity, not avoidance. An agent with 500 goal-relevant suppressed-approach records was working hard on its goal target; an agent with 0 was not working on it at all.

The reversal reframes the pre-registration's Category δ prediction. The prediction assumed that approach-without-contact is a signature of difficulty or failure. The data shows it is a signature of engagement: the agent that approaches and withdraws is in relationship with the object in the Winnicottian sense. It is the agent that never approached at all — the registered-but-not-engaged case first identified at v1.8 — whose relationship with the target is genuinely absent. Zero goal-relevant suppressed approaches and a registered-but-not-engaged expired record is the developmental combination that describes an agent that was oriented toward an object, knew where it was, and held its distance throughout Phase 2 without any detectable approach trajectory. That combination is now legible in the biographical register for the first time.

Category δ: findings reported. Pre-registered direction on goal-relevant CF reversed and reinterpreted.

### 3.5 Category Φ: Honesty constraint

One amendment cycle recorded.

**v1.9.1 (detection threshold reduction).** Pre-registered thresholds N_approach=10, N_recession=5 failed Level-11 C6: zero records across all 10 verification runs. Diagnosis: V17World's continuous-space trajectories involve lateral corrections at 2–3 step granularity; a 10-step monotone window exceeds the typical clean approach segment. Amended to N_approach=3, N_recession=3. The structural definition of a suppressed approach is unchanged. The amendment is an environmental calibration, not an architectural revision.

The detection method limitation stated in the pre-registration holds: positional detection captures the trajectory signature consistent with gate-suppression. The batch data is consistent with this characterisation. The cost-invariance of pre-threshold suppressed approaches (Section 3.4) is consistent with a detection method that captures spatial approach dynamics rather than threat-gate-specific events: the gate fires on contact, not on proximity, so approach-withdrawal before contact would not be gate-mediated regardless.

**Additive discipline confirmed.** Level-11 C7: three runs with `--no-counterfactual` produced zero Q4 statements, `counterfactual=None`, zero hallucinations. The v1.9 substrate stack does not alter any Q1/Q2/Q3 output.

Category Φ: one amendment; rationale documented; limitation characterised.

### 3.6 Category η: The three-way contact register

All four cost conditions: 10/10 runs with suppressed-approach records. The three-way contact register — clean contact (object entered, cost paid), suppressed approach (approached, withdrew without contact), prediction-error contact (entered before precondition met) — is complete at every cost condition.

| Cost | Runs with suppressed approaches | Total CF records |
|---|---|---|
| 0.1 | 10/10 | 16,300 |
| 1.0 | 10/10 | 10,851 |
| 2.0 | 10/10 | 17,148 |
| 10.0 | 10/10 | 27,329 |

Category η: **PASS** at all cost conditions.

**Object distribution.** Across all 71,628 events:

| Object | Events | % |
|---|---|---|
| haz_unaff_1 | 14,258 | 19.9% |
| haz_unaff_0 | 13,929 | 19.4% |
| haz_yellow | 13,810 | 19.3% |
| haz_unaff_2 | 13,073 | 18.3% |
| haz_green | 11,278 | 15.7% |
| dist_yellow | 3,220 | 4.5% |
| dist_green | 2,060 | 2.9% |

HAZARD objects account for 93% of all suppressed-approach events. DIST_OBJ events (7.5%) are concentrated in runs where `locate_family` goals set dist_yellow or dist_green as eligible targets. The distribution across HAZARD objects is approximately uniform, with no single hazard object dominating — the agent orbits all hazard objects at approximately equal rates, consistent with the cost-invariance finding.

**Phase distribution.** Across all events:

| Phase | Events | % |
|---|---|---|
| 1 | 3,722 | 5.2% |
| 2 | 24,591 | 34.3% |
| 3 | 43,315 | 60.5% |

Phase 3 accounts for 60.5% of all suppressed-approach events. This is the Phase 3 consolidation pattern discussed in Section 3.7.

### 3.7 The Phase 3 consolidation pattern

The highest-activity runs in the batch — cost=0.1 run=8 (7,815 CF records), cost=2.0 run=2 (6,854), cost=10.0 runs 0, 4, 6, 7 (3,500–5,700) — share a common profile: all are resolved runs in which the agent achieved full attractor mastery and then continued to operate in V17World for a substantial proportion of the 320,000-step budget. In each case the agent's mastery sequence was completed and Phase 3 activity dominated the run's later steps. The CF records in these runs are predominantly Phase 3 events: the agent approaches hazard objects repeatedly, at closest distances between 0.5 and 2.0 units, and withdraws without contact, after mastery is complete.

This is architecturally correct. There is no reason to exclude post-mastery approach-withdrawal events, and the pre-registration does not exclude them. But the developmental interpretation is different from early-Phase-2 suppressed approaches. An approach-and-withdrawal before first contact with a hazard object, while the attractor precondition is unmet, describes a specific developmental position: the agent is in proximity to an object it cannot yet enter safely, or has not yet resolved to enter. An approach-and-withdrawal in Phase 3, after full attractor mastery and multiple prior cost-bearing contacts, describes something different: the agent that has mastered the material continues to interact with it in new ways. In Montessori terms, the child who has learned to carry the heavy cylinder does not stop picking it up. In Winnicottian terms, the object has been internalised — it is part of the agent's world — and continued proximity does not require the commitment of contact.

The v1.9 register cannot yet distinguish these two types of suppressed approach. `pre_threshold_entries` distinguishes first-time approaches (pre_threshold_entries=0) from approaches after prior contact, which is the relevant field — but the Phase 3 consolidation pattern produces high counts of approaches with pre_threshold_entries > 0, and these are not avoidance events. They are the post-mastery exploration pattern that Montessori and Winnicott would both predict and both regard as developmentally positive.

This distinction — pre-contact restraint vs post-mastery exploration — is the interpretive challenge the v1.9 data surfaces. The v1.10 belief-revision layer, which reads `pre_threshold_entries` alongside the prediction-error substrate, will begin to address it. The agent that has a record of what it believed about an object at the moment of approach will eventually be able to distinguish *I approached this object when I had not yet entered it* from *I approached this object on the forty-seventh occasion, after mastery was complete, and chose not to enter*. V1.9 holds both records faithfully. V1.10 begins to read them differently.

---

## 4. Discussion

### 4.1 What the counterfactual register adds to the biographical account

Prior to v1.9, the biographical register described completed events: what was encountered, what was mastered, what prediction errors were resolved, what goals were set and whether they were met. The register was a record of outcomes. V1.9 extends it to include the event that did not complete: the approach that did not become contact.

This addition is not merely additive in the quantity sense. It changes the *kind* of account the register holds. A biographical account that contains only completed events is a record of achievements and failures. An account that also contains suppressed approaches is a record of *position* — not just what the agent did, but where it stood in relation to what it had not yet done. The agent at Q4 step 47,312 was 0.84 units from haz_yellow, had not yet entered it, and withdrew. That record places the agent in a specific developmental position: close, not committed, turned back. The account of that agent is richer than the account of an agent whose register contains no suppressed approaches — not because more happened, but because the relationship between the agent and the object is now visible in its incompleteness.

In Winnicottian terms, this is the register of the transitional space: the zone between approach and contact, approach and mastery, approach and incorporation. The agent that inhabits this zone — that can be near the object without either entering it or fleeing — has a developmental life that prior registers could not record. V1.9 is the first iteration in which the biographical register reaches into that space.

### 4.2 The engagement-intensity finding and its consequences

The reversal of the goal-relevant CF prediction (Section 3.4) has consequences beyond the immediate finding. It establishes that the suppressed-approach register is a measure of engagement, not of avoidance — and that the two can only be distinguished with reference to the goal substrate and the resolution outcome.

An agent with high goal-relevant suppressed-approach counts and a resolved goal was engaging intensely with its target: approaching, sometimes entering, sometimes not, but consistently in proximity. An agent with high goal-relevant suppressed-approach counts and an expired goal that also has goal-progress records was also engaging, but could not complete within the window. An agent with zero goal-relevant suppressed-approach counts and a registered-but-not-engaged expired record was not engaging at all: it knew where the target was and held its distance at a scale that produced no approach-withdrawal events.

The three-way combination — counterfactual substrate, goal substrate, goal outcome — now produces a developmental classification of Phase 2 engagement that was not possible with any two of the three alone. This is the substrate-combination property the SICC document's Commitment 8 (self-knowledge as derivative of object-knowledge) anticipates: the richer the object-relations record, the richer the self-account. V1.9's contribution is the specific record type that, combined with v1.8's goal layer, makes engagement intensity legible for the first time.

### 4.3 Cost-invariance of suppressed approaches

The uniform pre-threshold suppressed-approach rate across cost conditions (~80%) is the batch's most unexpected finding, and arguably its most structurally interesting. The prediction-error architecture is strongly cost-sensitive: higher costs produce longer resolution windows, more dramatic surprise events, and more differentiated developmental arcs. The counterfactual architecture shows no corresponding cost-sensitivity at the pre-contact level.

The interpretation: the threat gate shapes what happens when the agent gets close enough to make contact. It does not shape how often the agent gets close. Getting close is a consequence of how the agent navigates V17World — its spatial exploration patterns, its curiosity-driven trajectory through the 3D environment, the geometry of its path through the prepared environment. These are cost-invariant at v1.9 because the agent's action selection and drive composition are cost-invariant (cost affects the agent's value updates after contact, not its approach trajectories before contact). The cost gate is a contact-level gate, not a proximity-level gate.

This is architecturally important for v1.10. If the belief-revision layer is to use the suppressed-approach record to update the agent's model of a hazard object, it needs to operate on approach trajectories that are individually variable — and the v1.9 data confirms that they are (Q4 individuation std=0.062, PASS). But the cost-invariance finding says that approach frequency itself is not the informative dimension; the informative dimension is which approaches lead to contact and which do not, and how that ratio changes as the agent's developmental history with the object accumulates. V1.10's belief-revision layer reads `pre_threshold_entries` specifically because it needs to track how the agent's approach-to-contact ratio changes with prior experience — and that ratio, not the raw approach count, is the developmentally meaningful variable.

### 4.4 The three-way contact register as developmental classification

The v1.9 batch produces, for the first time, a complete three-way classification of every eligible object's contact history in each run: clean contact (object entered, cost paid, without prior prediction error), prediction-error contact (entered before precondition met, cost paid, surprise event fired), and suppressed approach (approached, withdrew without contact). Any eligible object in any run can be placed in one or more of these categories, and the combination tells a specific developmental story.

An object with only suppressed approaches and no contacts: the agent came close repeatedly and never entered. The relationship with the object never progressed beyond proximity. This is the purest suppressed-approach profile.

An object with suppressed approaches followed by prediction-error contact: the agent approached and withdrew, then eventually entered before the precondition was met, and was surprised by the cost. The suppressed approaches may represent a period of proximity without commitment; the prediction-error entry may represent a moment of reduced caution or a shift in phase. The register holds both.

An object with suppressed approaches followed by clean contact: the agent approached and withdrew, then eventually entered under the precondition. The suppressed approaches were, in developmental terms, a period of preparation. The register holds the preparation and the completion.

An object with only clean contacts and no suppressed approaches: the agent entered directly, the precondition was met, no approach-withdrawal events were detected at N=3. This may represent a confident, direct approach — or simply a path geometry that did not produce the monotone-window signature.

This classification is derived post-hoc from the combined counterfactual, provenance, and prediction-error substrates. It is not a substrate field at v1.9. At v1.10 it will inform the belief-revision architecture: the agent's prior relationship with an object — approached and withdrew, then entered, or never approached, or entered on first contact — is precisely the developmental context in which belief revision should operate differently.

### 4.5 SICC Commitment 3, Commitment 8, and Commitment 9 advanced

**Commitment 3 (unfillable slots as epistemic features)** is advanced at the behavioural level. A suppressed approach is a slot the agent could have filled and did not. The counterfactual record holds the attempted access and the withdrawal. The not-yet-self object — held at a distance the agent did not close — is now a datum in the biographical register, alongside the objects that were encountered and mastered.

**Commitment 8 (self-knowledge as derivative of object-knowledge)** is the commitment most directly served by v1.9. The Q4 record is an object-relations record of a new kind: the encounter that did not complete. The agent that reports *At step 47,312, I came within 0.84 units of haz_yellow without making contact* is producing a self-account grounded in a specific object relationship at a specific developmental moment — approach trajectory, closest-point distance, phase, prior contact history. The account is not generated from a self-model; it is read from the accumulated record of object encounters. Self-knowledge follows from that, as Winnicott's account requires it to.

**Commitment 9 (earned extensibility), forward arc: belief revision.** The `pre_threshold_entries` field establishes the architectural prerequisite for v1.10: how many prior contacts the agent had with an object at the moment of a suppressed approach. This field, combined with the prediction-error substrate (what the agent's violation record says about this object) and the goal substrate (whether the object was the active goal target), constitutes the three-substrate basis for belief revision. V1.10 will read all three. V1.9's contribution is the counterfactual substrate — the third element of that combination.

---

## 5. Conclusion

V1.9 introduces the counterfactual observer and the fourth query type: *where did I approach without making contact?* Across 40 complete runs at 320,000 steps in V17World, 71,628 Q4 statements were produced with zero hallucinations, all 40 runs produced at least one suppressed-approach record, and Q4 individuation distances confirm that agents differ substantially in their approach-withdrawal trajectories. The biographical register now holds a record of restraint alongside mastery.

One amendment cycle was required: detection thresholds reduced from N=10/5 to N=3/3, calibrating the window to V17World's continuous-space movement granularity. The structural architecture is unchanged.

The batch's sharpest finding is the reversal of the goal-relevant CF prediction. Agents that resolved their goals show higher goal-relevant suppressed-approach counts than expired agents — because suppressed approaches are a signature of engagement, not avoidance. The agent that approached its goal target 500 times, sometimes entering and sometimes not, was working on it. The agent that produced zero goal-relevant suppressed approaches and a registered-but-not-engaged expired record was not. The distinction between these two profiles is now legible in the biographical register for the first time: the combination of goal substrate, counterfactual substrate, and goal outcome tells a developmental story that none of the three alone could tell.

The pre-threshold cost-invariance finding — ~80% of suppressed approaches are first-contact events across all cost conditions — establishes that approach-withdrawal is a feature of spatial exploration, not cost-aversion. The cost gate operates at contact, not at proximity. This distinction will shape how v1.10's belief-revision layer reads the counterfactual substrate: not as a measure of cost-driven caution, but as a measure of the agent's developing relationship with each object, which must be tracked through the `pre_threshold_entries` field across the agent's developmental arc.

The Phase 3 consolidation pattern — high-activity runs where post-mastery agents continue to approach and withdraw from familiar hazard objects in sustained engagement — surfaces an interpretive challenge that v1.10 will begin to address. The register correctly captures both pre-contact restraint and post-mastery exploration; distinguishing them requires reading the suppressed-approach record in the context of the agent's full developmental history with the object. That reading is what the belief-revision layer is for.

The biographical register describes the agent's developmental arc with greater precision at v1.9 than at v1.8. Not because the arc changed, but because the register now reaches into the transitional space — the zone between approach and commitment, proximity and contact — that Winnicott's account of development requires, and that prior iterations could not record.

---

## References

Baker, N.P.M. (2026r–z) Prior preprints and pre-registrations v1.1–v1.3. See v1.4 reference list.

Baker, N.P.M. (2026ab) 'v1.4 Pre-Registration and Paper: Cross-Family Structural Comparison', GitHub repository, April 2026.

Baker, N.P.M. (2026ad) 'v1.5 Pre-Registration and Paper: Prediction-Error Elevation', GitHub repository, April 2026.

Baker, N.P.M. (2026ae) 'v1.6 Pre-Registration: Reporting Layer via SubstrateBundle Interface', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026af) 'Biographical Self-Account in a Small Artificial Learner: The Reporting Layer as Substrate-Agnostic Reading Component', preprint, 2 May 2026.

Baker, N.P.M. (2026ag) 'v1.7 Pre-Registration: Substrate Transposition to a Richer Simulated Environment', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026ah) 'Substrate Transposition in a Small Artificial Learner: The Cognitive Layer Meets a Richer World', preprint, 3 May 2026.

Baker, N.P.M. (2026ai) 'v1.8 Pre-Registration: Goal Assignment and Motivated Learning', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026aj) 'v1.8.1 Pre-Registration Amendment: Mapping and Engagement Separated', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026ak) 'v1.8.2 Pre-Registration Amendment', GitHub repository, 3 May 2026.

Baker, N.P.M. (2026al) 'Goal-Directed Learning in a Small Artificial Learner: Motivation, Mapping, and the Failure Register', preprint, 3 May 2026.

Baker, N.P.M. (2026am) 'v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026an) 'v1.9.1 Pre-Registration Amendment: Detection Threshold Reduction', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ao) 'Counterfactual Record and Suppressed Approach in a Small Artificial Learner: The Register of What Was Not Done', preprint, 4 May 2026.

Baker, N.P.M. (internal record, v0.5 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
