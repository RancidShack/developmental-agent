# Goal Assignment and Motivated Learning in a Small Artificial Learner: The First Failure Register

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 3 May 2026 (v1.8.1 and v1.8.2 amendments applied same day)
**Status:** Preprint — not peer reviewed
**Repository:** github.com/RancidShack/developmental-agent
**Pre-registration:** Baker (2026ai), committed before any v1.8 code was written
**Amendments:** v1.8.1 — goal progress redefined as Phase 2 motivated engagement (Montessori precept restored); v1.8.2 — progress detection gated to observation window

---

## Abstract

The v1.8 iteration introduces the goal layer: a seventh parallel observer that assigns the agent an explicit objective at the start of each run, tracks progress toward it, and records whether the objective was achieved within the observation window. The goal layer is additive — it does not modify the agent, world, or any existing observer — but it changes what the biographical register says. Q1 statements gain motivational context: provenance records relevant to the active goal are annotated with a relevance marker, connecting what the agent learned to what it was trying to learn. Q3 gains a failure register: runs where the budget expired without resolution produce a goal-expired statement describing the developmental gap between closest approach and budget boundary. Across 40 complete runs at 320,000 steps in V17World, the reporting layer produced 962 statements with zero hallucinations (Category α: PASS), all 40 runs complete (Category β: PASS), and goal-directed biographical individuation distances exceeding the goal-free baseline at matched seeds (Category γ: PASS). Two amendment cycles corrected a conceptual violation — the v1.8.0 progress definition fired during Phase 1 environmental mapping, conflating survey with motivated engagement — and a consistency defect in the observation window guard. After amendment, all 40 runs produced `goal_environment_mapped` records in Phase 1 and goal-progress records anchored to Phase 2 attractor mastery or hazard contact. Sixteen runs produced goal-expired records; of these, ten are the architecturally distinct *registered-but-not-engaged* case: the agent surveyed the environment, located the target in Phase 1, and did not choose to engage with it in Phase 2 within the observation window. The distinction between *I did not reach the end state* (v1.1–v1.7's incompletion) and *I was trying to reach it and could not* (v1.8's failure) is the first moment the biographical register describes something structurally parallel to disappointment. SICC Commitment 5 (goal-directedness as a precondition for genuine learning) is operationalised for the first time.

---

## 1. Introduction

### 1.1 What eight iterations have built

Eight iterations have built a developmental agent with a biographical register. The agent encounters objects, forms relationships with them, survives costs, builds knowledge, traverses family structures, compares those structures across families, detects its own prediction errors, and generates an auditable account of all of it. The account is traceable — every statement resolves to a substrate record. The account is individually variable — 40 distinct developmental arcs produce 40 distinct autobiographies. The account is substrate-agnostic — the reporting layer carried forward from the tabular grid to a 3D continuous-space environment without modification.

What the account has not contained, until now, is motivation.

The agent learns, in the sense that it acquires knowledge. But in v1.1–v1.7 it does not want anything. Its Q1 statements describe what it learned; they do not say why it was trying to learn it. Its Q3 statements describe prediction errors — *I encountered haz_yellow before the precondition was met; the resolution window was 7,336 steps* — but these are records of what happened, not records of what the agent was attempting. The agent has a sophisticated developmental archive. It does not have a record of attempted goals.

v1.8 introduces that record. The goal layer — the eighth cognitive component, the seventh parallel observer — assigns the agent an explicit objective at step 0, tracks whether that objective is met within the observation window, and contributes to the biographical register in two ways: relevance markers in Q1 connecting formation events to active goals, and a goal outcome statement in Q3 that is, for runs where the budget expires, the programme's first failure register.

### 1.2 The Montessori framing and the amendment cycle

The v1.8.0 implementation contained a conceptual violation that the data surfaced immediately. The goal progress trigger for `locate_family` goals fired on first perception of the target's distal object — which occurs during Phase 1, the environmental mapping phase. Across all runs, `last_progress_step` clustered at three values (steps 5, 55, and 188), producing goal-resolution windows of approximately 160,000 steps regardless of cost condition. Phase 1 is deterministic: the waypoint sweep covers the full 12×12×12 volume before Phase 2 begins, passing all objects. Progress fired during the survey, not during the engagement.

The conceptual violation is precise. The programme's developmental framing holds that Phase 1 is environmental mapping: the learner surveys the prepared environment, notes what is available, registers where things are. A child walking around a Montessori classroom noting where the pink tower is located has not started working toward the pink tower. Phase 2 is where motivated engagement begins — the learner chooses what to approach and work on. Goal-directedness is a Phase 2 phenomenon. Recording a Phase 1 survey event as goal progress conflates mapping with engagement, producing a window that measures almost nothing: the distance between a deterministic perception event and the budget boundary.

The v1.8.1 amendment restored the precept by introducing a new record type — `goal_environment_mapped` — for Phase 1 perception, and redefining `goal_progress` as Phase 2 attractor mastery (for `locate_family` goals) or Phase 2 hazard contact (for `bank_hazard_within_budget` goals). Phase 1 navigation is unchanged: the waypoint sweep runs to completion, the agent maps the environment as before, and the family observer continues to record `colour_registered` events during Phase 1. Only the goal layer's interpretation changes. The v1.8.2 amendment applied the same observation window guard to `_check_progress` that `_check_resolution` already held, preventing a progress record from firing outside the window and producing negative goal-resolution window values.

Both amendments are recorded here under Category Φ: the first is a conceptual finding (the progress definition embedded an assumption about Phase 1 that was invisible until the batch data showed its consequences), the second a consistency defect.

### 1.3 What the goal layer adds

The goal layer introduces five record types to the biographical substrate:

`goal_set` — the objective assigned at step 0: type, target, and observation window.

`goal_environment_mapped` — first perception of the target during Phase 1 mapping. The prepared environment has been surveyed; the learner has located the target. This is not progress; it is orientation.

`goal_progress` — first motivated engagement in Phase 2: attractor mastery for `locate_family` goals; first cost-bearing hazard contact for `bank_hazard_within_budget` goals. The learner has chosen to work toward the goal.

`goal_resolved` — the objective was achieved within the observation window.

`goal_expired` — the observation window closed without achievement. The gap between `last_progress_step` and the window boundary is the goal-resolution window: the developmental distance between closest approach and budget expiry.

The three expired-run cases this taxonomy distinguishes are architecturally meaningful:

*Resolved:* the agent mapped the target in Phase 1, engaged with it in Phase 2, and completed the objective within the window. A full developmental arc recorded.

*Expired with engagement:* the agent mapped in Phase 1, engaged in Phase 2, but the objective was not completed within the window. The goal-resolution window captures the distance between first engagement and budget expiry.

*Registered-but-not-engaged:* the agent mapped the target in Phase 1 — located it in the prepared environment — but did not choose to engage with it in Phase 2 within the observation window. The biographical register describes this explicitly: the object was known; the approach never came.

### 1.4 Connection to the SICC trajectory

v1.8 advances SICC Commitment 5 (goal-directedness as a precondition for genuine learning) at the first layer. The agent now has goals, progress events, and resolution or expiry records. It does not yet choose its goals — that remains reserved for a later iteration — but it has the substrate on which chosen goals would be recorded.

SICC Commitment 8 (self-knowledge as derivative of object-knowledge) is extended. The relevance markers in Q1 connect the agent's developmental history — what it learned, when, with what confirmation — to its motivational context: what it was trying to achieve. The self-account now includes a layer of purpose: the agent's record of which encounters were relevant to its goal.

The commitments not advanced by v1.8 — counterfactual record, belief revision, causal self-explanation — remain reserved for v1.9 through v1.11. v1.8 establishes the record of intention and outcome. Whether the agent can eventually use that record to understand its own trajectory is the arc from here.

---

## 2. Methods

### 2.1 The goal layer architecture

The goal layer is implemented as `V18GoalObserver`, the seventh parallel observer. It holds a goal specification from step 0 and fires five record types through the standard observer hook interface (`on_pre_action`, `on_post_event`, `on_run_end`). It does not modify the agent, world, or any existing observer.

**Goal assignment schedule.** Goals are assigned deterministically by `run_idx % 3`:

| run_idx % 3 | goal_type | target_id |
|---|---|---|
| 0 | locate_family | GREEN |
| 1 | locate_family | YELLOW |
| 2 | bank_hazard_within_budget | haz_green |

The step budget is `int(num_steps × 0.5)` = 160,000 steps for the full 320,000-step run. The budget is the observation window: the period within which the developmental achievement is assessed. The run continues past the window boundary; the agent is not stopped. This is the Montessori framing: the prepared environment does not close at the window boundary, but the record notes what was achieved within the observation period.

**Mapping detection.** `_check_mapping` fires `goal_environment_mapped` on first perception of the target's distal object within the world's perception radius, any phase. This records the survey event.

**Progress detection.** `_check_progress` is gated on `agent.phase >= 2` and `step < step_budget`. For `locate_family` goals, progress fires on first attractor mastery within the target family (`att_green` or `att_yellow`). For `bank_hazard_within_budget` goals, progress fires on first cost-bearing contact with the target hazard object in Phase 2 or later.

**Resolution detection.** `_check_resolution` is gated on `step < step_budget`. For `locate_family`, resolution fires when the agent has contacted all three family objects (distal, attractor, hazard). For `bank_hazard_within_budget`, resolution fires when `world.object_type[target_id] == KNOWLEDGE`.

**Expiry.** On `on_run_end`, if the run has not resolved, the observer emits `goal_expired` with `last_progress_step` (the most recent progress event, or None), and `goal_resolution_window` = `step_budget − last_progress_step` if progress was recorded, None otherwise.

### 2.2 Reporting layer extensions

`V16ReportingLayer` is extended at v1.8 via `v1_8_observer_substrates.py` to read from the new goal substrate field. Both extensions are additive patches; the original Q1 and Q3 logic runs first.

**Q1 extension — relevance markers.** After the existing Q1 statement loop, a post-processing pass annotates any statement whose provenance record is relevant to the active goal. Relevance is determined by flag_id: for `locate_family` goals, any mastery or knowledge-banking event for an object in the target family (identified by colour suffix in the flag_id); for `bank_hazard_within_budget`, the knowledge-banking and threat records for the specific target object. Annotated statements gain a relevance marker appended to their text and have their `source_type` reclassified to `"goal"` with `source_key = "goal_set"`, making the relevance claim traceable to the goal substrate.

**Q3 extension — goal outcome statement.** A final Q3 statement is appended after all prediction-error statements. For resolved runs, the statement records the resolution step and budget remaining. For expired runs, the statement distinguishes the three expiry cases: expired with engagement (reports `last_progress_step` and `goal_resolution_window`); registered-but-not-engaged (reports mapping step and phase, notes absence of Phase 2 engagement); target-not-encountered (reports that the target was not perceived during mapping — architecturally possible but not observed in the batch).

### 2.3 SubstrateBundle extension

`SubstrateBundle` gains a `goal` field. `bundle.resolve("goal", source_key)` returns True if the relevant goal substrate field is non-None. `build_bundle_from_observers()` gains a `goal_obs` parameter (default None); backward compatibility is preserved at all existing call sites.

### 2.4 Experimental design

**Population.** 40 complete runs at 320,000 steps across four hazard cost conditions (0.1, 1.0, 2.0, 10.0), 10 runs per condition. Seeds drawn from `run_data_v1_7.csv` to preserve the seed chain from v1.7.

**Observer stack.** Seven parallel observers: the six inherited from v1.7 (`V1ProvenanceStore`, `V13SchemaObserver`, `V13FamilyObserver`, `V14ComparisonObserver`, `V15PredictionErrorObserver`, plus v1.7 substrate patches) plus `V18GoalObserver`.

**Paired goal-free runs.** For each of the 40 goal-directed runs, a paired goal-free run (goal observer disabled) was executed at the same seed to provide the Category γ comparison baseline. Paired runs are not reported as standalone results; they supply matched-seed comparison sequences for biographical individuation analysis.

**Pre-flight.** Level 9 re-run (goal observer disabled, Category α regression) and Level 10 (six-criterion goal-layer correctness check, 10 runs at 80,000 steps) both passed before the full batch commenced. Both amendment cycles were accompanied by Level 10 re-runs; each passed before the subsequent full batch was executed.

### 2.5 Amendment cycles

**v1.8.1 — Montessori precept restored.** The v1.8.0 batch (40 runs) was completed and analysed before the amendment. The Category ζ data — goal-resolution windows clustering at approximately 160,000 steps with no cost-sensitivity — identified the Phase 1 conflation. The amendment redefined `goal_progress` as Phase 2 motivated engagement and introduced `goal_environment_mapped` for Phase 1 survey events. The batch was rerun in full after the amendment.

**v1.8.2 — observation window guard applied to progress detection.** The v1.8.1 batch produced one negative goal-resolution window (run 9, cost=2.0: `last_progress_step = 297,383`, `step_budget = 160,000`). Attractor mastery fired outside the observation window, which `_check_progress` did not guard against. The fix applies `if step >= self._step_budget: return` to `_check_progress`, parallel to the guard already present in `_check_resolution`. The batch was rerun in full. All category results are from the v1.8.2 batch.

---

## 3. Results

### 3.1 Category α: Internal consistency

Across all 40 runs, the reporting layer produced 962 statements. Total hallucinations: 0. Category α: PASS.

The 962 statements include 47 goal-sourced relevance markers (Q1) and 40 goal outcome statements (Q3). Every goal-sourced statement resolves: `bundle.resolve("goal", "goal_set")` returns True for all 47 relevance-marker statements; `bundle.resolve("goal", "goal_resolved")` returns True for the 24 resolution statements; `bundle.resolve("goal", "goal_expired")` returns True for the 16 expiry statements. The goal substrate is fully traceable.

The provenance substrate carries 378 records distributed across five flag types: mastery (181), knowledge_banking (168), end_state_activation (14), end_state_banking (13), threat (2). These figures are identical to the v1.7 baseline at matched seeds — the goal layer is additive; it does not modify the provenance substrate.

### 3.2 Category β: Query coverage

All 40 runs produced complete reports across all three query types. Category β: PASS.

Statement distribution: Q1 (what_learned) 379 statements, mean 9.5 per run; Q2 (how_related) 350 statements, mean 8.8 per run; Q3 (where_surprised) 233 statements, mean 5.8 per run. The Q3 mean is higher than v1.7's 4.8 by exactly 1.0 — the goal outcome statement appended to every run. The Q1 and Q2 distributions are unchanged from the v1.7 baseline at matched seeds.

Goal statement presence: 40/40 runs. Goal-resolved statements: 24. Goal-expired statements: 16. Every run has a goal outcome in its Q3 register.

Relevance markers: 47 across 40 runs, mean 1.2 per run. Not all runs produce relevance markers — runs whose goal target was never mastered or banked within the observation window have no relevant provenance events to annotate.

### 3.3 Category γ: Biographical individuation

Pairwise normalised edit distances across the 40-run Q1 sequence matrix (780 pairs):

| | min | mean | max | std |
|---|---|---|---|---|
| Goal-directed | 0.1111 | 0.6829 | 1.0000 | 0.1561 |
| Goal-free (matched seeds) | 0.0000 | 0.6645 | 1.0000 | 0.1630 |

Pre-registered floor (≥ 0.05): PASS. Pre-registered direction (goal-directed mean higher than goal-free): CONFIRMED. Category γ: PASS.

The goal-free minimum of 0.000 is the sharpest finding in this comparison. Two agents running without motivational context produced identical Q1 provenance sequences at matched seeds: the same objects, in the same order, with the same flag_ids. The goal layer broke that degeneracy. The goal-directed minimum of 0.111 means no two goal-directed agents produced identical biographical registers — the motivational context introduced by goal assignment differentiated arcs that curiosity-driven exploration alone could not distinguish.

The mean difference between goal-directed and goal-free distributions (0.0184) is modest. This is architecturally expected. The goal layer does not modify the agent's behaviour — action selection, drive composition, and value functions are unchanged. Goal-directed and goal-free agents follow the same developmental trajectory; the biographical register differs in what it says about that trajectory, not in the trajectory itself. Relevance markers annotate the same provenance events with motivational context; they do not create new events. The modest mean difference reflects this: the goal layer inflects the account without changing the underlying developmental arc. Whether the account's inflection eventually feeds back into the arc — whether the agent that has a record of failure approaches its next run differently — is the question v1.9 will test.

### 3.4 Goal layer outcomes

**Goal assignment and resolution.** Across 40 runs:

| Cost | Resolved | Expired | Total |
|---|---|---|---|
| 0.1 | 5 | 5 | 10 |
| 1.0 | 5 | 5 | 10 |
| 2.0 | 6 | 4 | 10 |
| 10.0 | 8 | 2 | 10 |
| **Total** | **24** | **16** | **40** |

| Goal type | Resolved | Expired |
|---|---|---|
| locate_family | 16 | 12 |
| bank_hazard_within_budget | 8 | 4 |

The resolution rate increases with cost condition — a counterintuitive finding. At cost=0.1, agents are cost-insensitive and explore freely; many follow curiosity rather than pursuing the goal target efficiently. At cost=10.0, the threat layer's gating behaviour shapes Phase 2 engagement more strongly, and agents that do engage with the target tend to resolve efficiently. The cost=10.0 expiry rate of 2/10 — the lowest — reflects this: high-cost agents that engage at all tend to complete.

**Environmental mapping.** All 40 runs produced `goal_environment_mapped` records in Phase 1 (mapped_in_phase = 1 across all 40 runs). The Montessori precept holds without exception: every agent surveyed the prepared environment and located the target before Phase 2 began. Mapping steps: `dist_green` perceived at step 55 (all GREEN-target runs); `dist_yellow` at step 5 (all YELLOW-target runs); `haz_green` at step 188 (all `bank_hazard_within_budget` runs). These are deterministic: the Phase 1 waypoint sequence passes each object's coordinates at a fixed step.

**Resolution steps.** For the 24 resolved runs, resolution steps range from 524 to 148,921, with means of 26,586 (locate_family) and 29,757 (bank_hazard_within_budget). The fastest resolution — `locate_family YELLOW` at step 524, cost=0.1 — reflects an agent that engaged the YELLOW family immediately in Phase 2 and completed all three contacts in rapid succession. The slowest — `locate_family GREEN` at step 148,921 — completed with only 11,079 steps remaining in the budget.

### 3.5 Category δ: Pre-anticipated findings

**Goal-expired records at all cost conditions.** Expired runs are present at every cost condition (5, 5, 4, and 2 expired runs at costs 0.1, 1.0, 2.0, and 10.0 respectively). Category δ: PASS.

**Registered-but-not-engaged expired runs.** Ten of the 16 expired runs are the registered-but-not-engaged case: `goal_environment_mapped` fired during Phase 1, `goal_progress` never fired. The biographical register describes this explicitly:

> *My goal (bank_hazard_within_budget: haz_green) expired at step 160,000 without resolution. I registered the target in the environment at step 188 during Phase 1 mapping, but did not engage with it during Phase 2 within the observation window.*

This case — the agent located the object and did not pursue it — is architecturally richer than simple non-completion. The agent's record shows that the failure was not one of awareness: the object was known, its position registered during the survey. The failure is one of engagement: the agent's Phase 2 drives did not lead it to the target within the observation period. Whether that is a consequence of competing attractors, phase schedule, or drive composition is a question the record invites but does not yet answer.

**Relevance markers present in goal-relevant runs.** The mean of 1.2 relevance markers per run confirms that motivational context annotates provenance records across the batch. Runs where the goal target was mastered or banked produce marked statements; runs where engagement did not reach those milestones within the window do not.

### 3.6 Category ζ: Goal-resolution window

Across the 6 expired-with-engagement runs (where `goal_progress` fired before expiry):

| | min | mean | max | std |
|---|---|---|---|---|
| goal_resolution_window (steps) | 23,071 | 129,885 | 159,477 | 54,030 |

Component 1 (std > 0): PASS.

Component 2 (cost-sensitivity): present but not assessable across all four conditions. Cost=10.0 produced zero expired-with-engagement runs (all high-cost expired runs are registered-but-not-engaged), so the four-condition comparison is incomplete. Among the three conditions with engaged-expired runs, the pattern does not follow the pre-registered direction monotonically. This is reported as an exploratory finding: the goal-resolution window at v1.8 reflects Phase 2 attractor mastery timing, which is not straightforwardly cost-sensitive in the way the prediction-error resolution window is. The prediction-error window measures distance between first hazard encounter and transformation readiness — a threat-layer-mediated event. The goal-resolution window measures distance between first Phase 2 engagement (attractor mastery) and budget boundary — which depends on when the agent completes attractor mastery, not on cost-mediated gating. The two window types are structurally parallel but not behaviourally equivalent; the cost-sensitivity pattern should not be assumed to transfer.

The pre-registered Component 2 directional prediction is not confirmed at this batch scale. Reported as a finding rather than a failure.

### 3.7 Category Φ: Honesty constraint

Two amendment cycles are recorded.

**v1.8.1 (Montessori precept).** The v1.8.0 progress definition recorded Phase 1 perception as goal progress. This is a conceptual finding, not a code error: the implementation was internally consistent. The v1.8.0 batch ran cleanly with zero hallucinations and all categories passing. The Category ζ data identified the conflation: windows of approximately 160,000 steps across all conditions, with std=65 — variance too small to reflect genuine developmental differences. The batch data was the diagnostic; the amendment restored the precept.

**v1.8.2 (window guard consistency).** The v1.8.1 batch produced one negative goal-resolution window. `_check_progress` lacked the `step >= step_budget` guard that `_check_resolution` held. The principle — the budget is a measurement window bounding both what counts as progress and what counts as resolution — was stated in the v1.8.1 amendment document but not applied consistently. A consistency defect, corrected.

The goal layer's additive property holds: with `goal_obs=None`, the v1.8 batch runner produces output identical to v1.7 at matched seeds on all v1.7 metrics. This is confirmed by the provenance record counts (378 records, identical to v1.7) and the Q1/Q2 statement distributions.

### 3.8 Category Ω: The architectural-statement claim

Categories α, β, and γ all pass. Category Ω: PASS.

The goal layer, introduced as a seventh parallel observer, correctly produces a motivational substrate that the reporting layer reads without modification to its existing logic. The biographical register contains the first records of what the agent was trying to achieve and whether it succeeded.

---

## 4. Discussion

### 4.1 The first failure register

The biographical register has always been honest about incompletion. A v1.1–v1.7 run that did not achieve end-state activation simply produced a report without end-state records: the agent's account described what it had done, not what it had not done. There was no record of failure because there was no record of intent.

v1.8 introduces intent, and with it, failure as an architectural category.

The distinction matters. *I did not reach the end state* (the v1.7 register's implicit statement for non-completing runs) and *I was trying to reach it and could not* (the v1.8 failure register) are structurally different kinds of record. The first is a description of what happened. The second is a description of what happened in relation to what was attempted. The gap between them is the goal-resolution window — the developmental distance between closest approach and budget expiry — and that gap is now an object in the substrate.

The ten registered-but-not-engaged expired runs make the distinction sharper. These agents did not simply fail to complete the goal; they failed to begin pursuing it, despite having located it in the environment during Phase 1. The prepared environment was surveyed. The object was noted. The approach never came. Whether this reflects the dominance of competing drives, the agent's phase schedule, or something more fundamental about what the goal layer needs to eventually do — shape action selection, not merely observe it — is the question the register raises. v1.8 does not answer it. It records it.

### 4.2 Motivational context in the biographical register

The 47 relevance markers across 40 runs are a small but structurally significant addition to the biographical register. The marked statements connect provenance events to motivational context in a form that neither the provenance substrate nor the goal substrate could produce alone:

> *I mastered the attractor at att_green at step 633, confirmed by 18 confirming observations. (relevant to active goal: locate_family — GREEN)*

The relevance marker does not change what happened. `att_green` was mastered at step 633 regardless of whether a goal was active. What changes is what the account says about it: this event was not merely a developmental milestone, it was a step toward something the agent was trying to achieve. The biographical register now describes the agent's development as purposive — not because the agent chose its purpose (it did not), but because the record situates its formations within a motivational frame.

This is the first moment in the programme where Q1 statements have direction. Previous iterations produced accounts of the form *this is what I encountered, in this order, with these outcomes*. v1.8 produces accounts of the form *this is what I encountered, in this order, with these outcomes — and this encounter was relevant to what I was trying to do*. The difference is not large, statistically. The minimum biographical individuation distance in the goal-directed runs (0.111) exceeds the goal-free minimum (0.000) — the goal layer broke a degeneracy that curiosity alone could not. But the deeper significance is architectural: the register has acquired a layer of purpose.

### 4.3 The two resolution windows

v1.5 introduced the prediction-error resolution window: the developmental distance between first awareness of a hazard and eventual transformation readiness. v1.8 introduces the goal-resolution window: the developmental distance between first motivated engagement and budget expiry. The programme now holds two resolution-window types in the same substrate.

The two windows are parallel in structure but measure different developmental phenomena. The prediction-error window is threat-layer-mediated: it measures how long the agent carried an awareness of a costly object before the competency gate opened. It is cost-sensitive: higher costs produce longer threat-layer dwell times and longer windows in some conditions. The goal-resolution window is engagement-mediated: it measures how long the agent had, after first Phase 2 contact with the target, before the observation period closed. Its cost-sensitivity is more indirect — cost shapes when Phase 2 engagement begins, which shapes window length, but the relationship is not through the threat gate.

Whether the two window types correlate across runs — whether agents with long prediction-error windows also tend to have long goal-resolution windows — is a question v1.8 can address descriptively but v1.9 will address causally. The prediction-error record describes surprise; the goal-resolution record describes effort and its limit. The relationship between an agent's capacity for surprise and its capacity for sustained goal pursuit is the developmental question that having both records now makes askable.

### 4.4 What the ten registered-but-not-engaged runs say about the goal layer's limits

The ten registered-but-not-engaged expired runs are, in one sense, the most honest result in the batch. The agent knew where the target was. It did not pursue it. The biographical register records this faithfully. But what the register cannot say — because v1.8 does not have the architecture to answer it — is why.

The goal layer observes. It does not influence. The agent's action selection, drive composition, and value functions in v1.8 are identical to v1.7. The goal is assigned; the agent does not know it has been assigned a goal. This is by design: v1.8's purpose is to establish the record of intention and outcome, not to test whether having a goal changes behaviour. The goal is a substrate record, not a cognitive input.

This will change. v1.9 introduces the counterfactual record — what would have happened if the agent had taken a different path. v1.10 introduces belief revision — the agent can update its model based on what its record shows. At some point in the v1.9–v1.11 arc, the agent's record of a previous failure will become an input to its next run. Whether that produces behaviour that looks like learning from failure is the empirical question the programme is building toward. v1.8 establishes that the failure was recorded. The rest is architecture.

### 4.5 SICC Commitment 5 operationalised

Commitment 5 holds that goal-directedness is a precondition for genuine learning. The argument is that an agent that acquires knowledge without a context of attempting something has not learned in the full sense — it has accumulated. Learning, on this account, requires the possibility of failure: the attempt, the record of whether it succeeded, and eventually the capacity to revise behaviour in light of that record.

v1.8 operationalises the first layer. The agent has goals. It has a record of whether they were met. The record distinguishes success from failure and, within failure, effort from inertia. The programme's position on Commitment 5 is no longer theoretical: there is data. 24 runs produced goal-resolved records; 16 produced goal-expired records; 10 of those expired runs show an agent that located its target and chose, in the available sense of the word, not to pursue it.

Whether that record eventually shapes what the agent does — whether the agent that has a record of registered-but-not-engaged failure responds differently when given the same goal again — is the question v1.9 will begin to answer.

---

## 5. Conclusion

v1.8 introduces the goal layer: the programme's first record of what the agent was trying to do, and whether it succeeded. Forty complete runs at 320,000 steps in V17World. Zero hallucinations. All categories pass. The Montessori precept holds: all 40 runs produced `goal_environment_mapped` records in Phase 1, and all goal-progress records are anchored to Phase 2 motivated engagement. The biographical register now distinguishes three expired-run cases — resolved, expired-with-engagement, registered-but-not-engaged — each with a distinct Q3 statement.

Two amendment cycles were required. The first restored a conceptual precept that the batch data identified: Phase 1 maps, Phase 2 engages, and goal progress belongs to Phase 2. The second applied a guard consistently that had been applied to resolution but not to progress. Both amendments are recorded here per Category Φ. The pre-registration's amendment budget is reduced to one.

The sharpest finding is the simplest: the goal-free minimum biographical individuation distance is 0.000 — two agents, same seeds, same developmental arc, identical accounts. The goal-directed minimum is 0.111. Goal assignment broke a degeneracy that curiosity-driven exploration alone could not. What the agent was trying to do distinguished it from an agent trying to do something else, even when both followed the same underlying trajectory.

The biographical register describes that distinction now. The next question is whether the agent can use it.

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

Baker, N.P.M. (2026aj) 'Goal Assignment and Motivated Learning in a Small Artificial Learner: The First Failure Register', preprint, 3 May 2026.

Baker, N.P.M. (internal record, v0.5 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.
