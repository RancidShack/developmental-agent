# The First Other Agent: Social Observation, Epistemic Corroboration, and the Limits of Witnessed Navigation

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 8 May 2026
**Status:** Working draft — complete across all sections
**ARCH versions covered:** v1_15, v1_15_1, v1_15_2, v1_15_3

---

## Abstract

The v1.14 iteration established that the agent returns to complete what it started: a cross-environment causal chain spanning ENV1 surprise, abductive prediction, ENV2 confirmation, and return-ENV1 transformation. What v1.14 did not introduce was a second agent. The agent's predicted record had no one to corroborate it. The developmental trajectory produced no record of another learner at the same problem.

The v1.15 iteration introduces a second agent into the shared world. The primary developmental question is whether witnessed navigation informs an open prediction — whether Agent B, observing Agent A approach att_blue in Environment 2, acquires a socially corroborated predicted record that shortens its own developmental arc.

The answer is a careful composite. The social observation architecture works correctly across three verified sub-versions. The epistemic distinction holds in every run: socially_corroborated is a genuine fourth schema state, not a shortcut to confirmation, and own mastery is required in every case. The being_observed substrate — the programme's first second-person record — fires on first contact in 23 of 29 events. Q6 statements are produced without hallucination. The individuation finding from the first build is confirmed: two agents in a shared world produce genuinely different developmental arcs, with Agent B measurably faster than the naive single-agent baseline in 11 of 13 socially corroborated runs.

What the architecture does not demonstrate is a causal effect of social observation on arc length. Agent B's arc_total_steps is bit-for-bit identical across v1.15, v1.15.1, v1.15.2, and v1.15.3 for the same seeds. Three successive interventions — geometry correction, Q6 repair, and waypoint injection at observation fire — produced no change in the developmental arc. The architectural diagnosis identifies the cause: the ENV2 directed search toward att_blue is pre-loaded for all agents at the transfer gate, regardless of social observation. There is no undirected search period for the social observation to interrupt. The ZPD hypothesis is present in the architecture and absent in the measurement.

This is reported under Category Φ. The version map criteria for v1.15 are met. The causal isolation question is documented as an open finding and deferred. The programme proceeds to v1.16.

---

## 1. Introduction

### 1.1 Programme to date

The V1 arc has advanced through three phases. The first established the base cognitive layer: provenance over learned states (v1.1), explicit schema (v1.2), relational property families with attractor-gated hazard transformation (v1.3), and cross-family structural comparison (v1.4). The second phase, v1.12 through v1.14, operationalised the cross-environment arc: schema transfer across environment boundaries, abductive prediction written before its confirmation was possible, and reparative return — the agent re-entering ENV1 after confirming att_blue in ENV2 to complete the haz_blue transformation it had carried as an open question. At v1.14.1, the cross-environment causal chain closed completely: surprise, prediction, transfer, confirmation, return, transformation. arc_complete in 29 of 29 eligible runs; zero timeouts; mean arc_total_steps 230,734 across a range of 1,113 to 851,603 steps.

What v1.14 did not hold was any record of another agent. The predicted schema had no corroborating source. The developmental arc was entirely private: written, transferred, and confirmed without a witness. The agent's Q5 self-explanation spanned both environments and produced no hallucinations, but the narrative had a single subject throughout.

### 1.2 The v1.15 question

The introduction of a second agent asks a specific question that the single-agent architecture could not ask: does observed performance at the predicted object change the observer's developmental trajectory? The question is not whether the agent can represent another agent — v1.15 does not introduce theory of mind. The question is narrower and empirical. Agent B writes a predicted record in ENV1: att_blue exists as the precondition for haz_blue, inferred from the structural pattern of completed family chains. Agent B then enters ENV2. If Agent B observes Agent A approach att_blue in ENV2 before B has found it, does that observation change when B confirms its own prediction?

The SICC formulation is precise on this point. Social corroboration is not a transfer of knowledge. The observed agent's mastery does not become the observer's mastery. The schema transition from predicted to socially_corroborated is a record that the prediction has external support and that the target's location is now known. Confirmation — att_blue mastery — remains exclusive to the confirming agent's own contact. What social observation provides is location evidence and the navigational advantage that should follow from it.

The experimental design tests whether that advantage is real.

### 1.3 Version history and the honest deviation record

The v1.15 iteration was built across four sub-versions, two of which were diagnostic corrections and one of which was an honest deviation from the original specification.

**v1.15 (wrong build).** The first v1.15 build implemented the two-agent shared world without inter-agent perception and without the social observation mechanism. This was a deviation from the version map specification, which required both. The deviation was detected after the batch ran. Rather than discarding the results, the programme recorded them under Category Φ (honesty) as v1.15_pre_registration_amended.md and reported them as a valid finding under a different developmental question: does cognitive individuation emerge in a shared world? The answer was affirmative, and those results are reported in Section 3.1.

**v1.15.1 (correct build, geometry fault).** The correct build added inter-agent perception, the social observation mechanism, the socially_corroborated schema state, Q6 statement generation, and being_observed substrate records. The verifier passed 8/8 criteria. The batch ran and produced 25 social observation events across 24 runs. However, a geometry fault in the firing condition meant that Agent B was at most 3.8 units from att_blue when the observation fired — combining PERCEPTION_RADIUS (3.0) with CONTACT_RADIUS (0.8). Mean gap from social observation to confirmation: 5 steps. The 5× directed search bonus at SOCIALLY_CORROBORATED_STATE was injected too close to the destination to redirect navigation. Additionally, the Q6 generator returned plain dict objects rather than SimpleNamespace objects; the report writer used getattr() and silently dropped all 25 statements to empty strings.

**v1.15.2 (geometry corrected, Q6 repaired).** Two targeted fixes: SOCIAL_PERCEPTION_RADIUS = 10.0, replacing PERCEPTION_RADIUS in the social observation gate condition only; and SimpleNamespace for Q6 objects. Both were confirmed in the verifier. The batch ran. Social observation now fired at ENV2 steps 16–2,433 in most runs, with a mean gap to confirmation of 72,977 steps. The being_observed distribution inverted: 23 of 29 events showed own_mastery=False, confirming B was watching A at first contact rather than on revisits. Q6 statements: 29, all with source_resolves=True. arc_total_steps_b: identical to v1.15 and v1.15.1 for all 13 soc=S runs.

**v1.15.3 (waypoint injection).** The directed search bonus (0.5/d) was identified as insufficient to redirect Q-table navigation against 1M+ ENV1 training steps. The fix injected SOCIAL_OBS_WAYPOINT_COUNT = 5 waypoints at att_pos into the world object at social observation fire — the same mechanism that reliably directs agents in the transfer phase. The batch ran. arc_total_steps_b: bit-for-bit identical across v1.15, v1.15.1, v1.15.2, and v1.15.3 for all 13 soc=S runs.

The architectural diagnosis is reported in Section 4.

---

## 2. Methods

### 2.1 Shared world architecture

Two agents — Agent A and Agent B — operate in the same world object across all three phases: ENV1 (1,000,000 steps), ENV2 (800,000 steps), and return ENV1 (200,000 steps). The world is genuinely shared: knowledge banked by either agent in ENV1 propagates to both. Hazard contacts, attractor masteries, and family causal chain completions are world-level events, not agent-private events. The shared world is the mechanism by which v1.15 differs from running two independent v1.14.1 agents: each agent's developmental history is shaped in part by what the other has already done.

Agent A uses seed_a from run_data_v1_15.csv. Agent B uses seed_a + SEED_B_OFFSET (20,000). The seed offset ensures cognitive independence: both agents face the same world but develop different Q-tables, different attractor mastery sequences, and different prediction timing. Forty runs across five hazard cost levels (0.1, 1.0, 2.0, 10.0) constitute the batch.

### 2.2 Transfer gate and CRITICAL INVARIANT

Both agents must meet the transfer gate before either enters ENV2: all completable hazards banked, all attractors mastered (ENV1 families), predicted record written. The CRITICAL INVARIANT — mastery_flag['att_blue'] = 1 — is carried into ENV2 only by agents who earned att_blue mastery in ENV2. Agents that did not earn it do not receive it. This is the correct carry behaviour, implemented as a deliberate fix in v1.15.1 (the v1.15 bug granted it unconditionally). Return ENV1 eligibility requires CONFIRMED_STATE in the predicted schema record: socially_corroborated is open, not returning.

### 2.3 Social observation mechanism (v1.15.1–3)

The social observation gate fires in ENV2 when three conditions hold simultaneously:

1. Agent B holds an open predicted record (PREDICTED_STATE or SOCIALLY_CORROBORATED_STATE).
2. Agent A is within CONTACT_RADIUS (0.8) of att_blue.
3. Agent B is within SOCIAL_PERCEPTION_RADIUS (10.0) of Agent A.

Condition 3 uses a separate constant from PERCEPTION_RADIUS (3.0), which governs general inter-agent awareness. On fire: predicted schema transitions to socially_corroborated; being_observed record written to Agent A's substrate; social_observation record written to Agent B's substrate; SOCIAL_OBS_WAYPOINT_COUNT (5) waypoints injected at att_blue position in the world (v1.15.3). The observation is one-shot per run per agent: social_observation_fired is set True on first fire.

The socially_corroborated state carries a 5× directed search bonus (0.5/distance toward att_blue, vs 0.1/distance for PREDICTED_STATE). Confirmation requires own mastery — att_blue contact and mastery by Agent B — regardless of the corroboration state.

### 2.4 Q6 statement

A Q6 statement is generated for every run in which Agent B holds a socially_corroborated record at any point. The statement traces: prediction written at step N from structural basis chains, social observation at step M in ENV2, location now known, own mastery required for confirmation, whether own mastery was achieved. source_resolves=True in all cases; a Q6 statement without a social_observation substrate entry is an architectural hallucination. Q6 statements are SimpleNamespace objects in v1.15.2+; the v1.15.1 dict bug is documented in Section 1.3.

### 2.5 ZPD measurement

zpd_delta_b = V1_14_1_BASELINE_MEAN (230,734) − arc_total_steps_b. Positive values indicate Agent B completed the developmental arc faster than the naive single-agent v1.14.1 baseline. This is reported separately for soc=S and soc=- runs. The confound analysis (Category Φ) examines whether arc_total_steps_a on soc=S runs shows the same pattern — if both agents are fast on these seeds, the acceleration may reflect environmental ease rather than social mechanism.

---

## 3. Results

### 3.1 Category Φ (deviation): v1.15 individuation findings

The v1.15 build produced valid findings under a different developmental question. With two agents in a shared world but no inter-agent perception, the question became: does cognitive individuation emerge in a shared world? Results across 40 runs:

- both_arc_complete: 38/40
- Δ > 0 (individuation confirmed, Agent B arc ≠ Agent A arc): 38/38
- first_transformer = 'a': 0/38 (Agent A never transformed haz_blue first; all 38 are ties or b-first)
- Agent B arc mean: 88,916 steps across 38 completing runs

The first_transformer asymmetry is notable. Agent B transforms haz_blue first or simultaneously in all 38 completing runs. Agent A never leads. The shared world architecture, combined with the seed offset structure, systematically positions B to arrive at the transformed state first once the return gate opens. This asymmetry is an architectural feature of the shared world design, not a behavioural finding about Agent A's capability.

The 88,916 step mean for Agent B represents a zpd_delta_b of +141,818 relative to the v1.14.1 baseline — substantially faster, attributable to shared ENV1 knowledge rather than social observation (which does not exist in this build).

### 3.2 Category Ω — Arc complete rate (v1.15.1–3)

| Metric | v1.15 | v1.15.1 | v1.15.2 | v1.15.3 |
|--------|-------|---------|---------|---------|
| both_arc_complete | 38/40 | 24/40 | 24/40 | 24/40 |
| arc_complete_a | ~38 | 28/40 | 28/40 | 28/40 |
| arc_complete_b | ~38 | 34/40 | 34/40 | 34/40 |

The drop from 38/40 to 24/40 reflects the carry fix in v1.15.1: agents that did not earn att_blue mastery in ENV2 no longer receive mastery_flag['att_blue'] = 1 in return ENV1. The v1.15 figure of 38/40 was inflated by the unconditional carry bug. 24/40 is the honest rate under the correct architecture. The figure is stable across v1.15.1–3.

### 3.3 Category α — Integrity

| Metric | v1.15.1 | v1.15.2 | v1.15.3 |
|--------|---------|---------|---------|
| Total hallucinations | 0 | 0 | 0 |
| Q6 statements | 0 (bug) | 29 | 29 |
| Q6 source_resolves=True | N/A | 29/29 | 29/29 |

The v1.15.1 Q6 count of zero is the dict/getattr bug documented in Section 1.3. In v1.15.2–3, all 29 Q6 statements are structurally clean. The text of each statement includes the phrase "own mastery is still required" — the epistemic boundary is stated explicitly in the report layer as well as enforced in the schema layer.

### 3.4 Category β — Epistemic boundary

The socially_corroborated state does not confirm. Confirmation requires own mastery. Across all completing soc=S runs in v1.15.2 and v1.15.3:

| Metric | v1.15.1 | v1.15.2/3 |
|--------|---------|----------|
| Mean gap (soc_step → conf_step) | 5 steps | 72,977 steps |
| Min gap | 2 | 2 |
| Max gap | 7 | 660,571 |
| All conf > soc | 13/13 | 13/13 |

The geometry fix produced a categorical shift. In v1.15.1, the 5-step mean reflected B already at the destination when the observation fired. In v1.15.2–3, the observation fires at ENV2 steps 16–2,433 and confirmation follows hundreds or thousands of steps later. Own mastery is always required and always earned independently. Category β holds in full.

### 3.5 Category δ — Witnessing conditions

| Metric | v1.15.1 | v1.15.2/3 |
|--------|---------|----------|
| social_corroboration_fired_b | 13/40 | 14/40 |
| Total social_obs events | 25 | 29 |
| B observes A events | 13 | 14 |
| A observes B events | 12 | 15 |
| being_observed records | 25 | 29 |
| own_mastery=False at observation | 2/25 | 23/29 |

The symmetric observation finding is notable and was not pre-registered. The architecture produces social observation events for both agents depending on who reaches att_blue first in ENV2. In 15 runs in v1.15.2–3, Agent A observes Agent B at att_blue (A holds the open prediction); in 14 runs, Agent B observes Agent A. arc_paired tracks only social_corroboration_fired_b; A's corroboration events are captured in social_observation_v1_15_3.csv but are not compared to a baseline, since the ZPD measurement was defined with respect to Agent B.

The being_observed inversion is the clearest evidence that the geometry fix worked as intended. In v1.15.1, 23 of 25 being_observed events fired on agents that had already mastered att_blue — the observation was recording a revisit, not a first contact. In v1.15.2–3, 23 of 29 events show own_mastery_at_step=False: the observed agent was at att_blue for the first time. B was watching A arrive.

Run 11 produced a mutual simultaneous observation: at ENV2 step 63, A observes B at att_blue; at step 64, B observes A at att_blue. Both being_observed records carry own_mastery=False. Neither agent had mastered att_blue when the other arrived. Both went on to confirm independently. This is the only case in the programme's record of two agents in simultaneous open-prediction, pre-mastery, socially-aware contact at the same object.

### 3.6 Category γ — ZPD effect

| Cohort | n | Mean zpd_delta_b | Positive |
|--------|---|-----------------|---------|
| soc=S (v1.15.2/3) | 13 | +115,396 | 11/13 |
| soc=- (v1.15.2/3) | 21 | +141,657 | 18/21 |

The pre-registered prediction (positive mean zpd_delta_b for soc=S) is met: +115,396 > 0. Both groups are faster than the v1.14.1 naive baseline. The soc=- group shows a higher mean than the soc=S group.

The direct comparison across versions is the decisive finding. Agent B's arc_total_steps is bit-for-bit identical across v1.15 (no social observation), v1.15.1 (observation fires at 5-step gap), v1.15.2 (observation fires at mean 72,977-step gap), and v1.15.3 (waypoint injection at observation fire) for all 13 soc=S seeds. Three successive interventions of increasing navigational strength produced no change. The architectural diagnosis is in Section 4.

**Table: Direct comparison, soc=S completing runs (v1.15.2/3)**

| Run | v1.15 B | v1.15.3 B | zpd_delta_b |
|-----|---------|-----------|-------------|
| 1 | 24,040 | 24,040 | +206,694 |
| 9 | 59,006 | 59,006 | +171,728 |
| 10 | 543,582 | 543,582 | −312,848 |
| 11 | 374,806 | 374,806 | −144,072 |
| 13 | 6,011 | 6,011 | +224,723 |
| 14 | 23,067 | 23,067 | +207,667 |
| 17 | 43,526 | 43,526 | +187,208 |
| 18 | 81,505 | 81,505 | +149,229 |
| 24 | 118,007 | 118,007 | +112,727 |
| 25 | 2,346 | 2,346 | +228,388 |
| 32 | 189,479 | 189,479 | +41,255 |
| 33 | 1,008 | 1,008 | +229,726 |
| 34 | 33,012 | 33,012 | +197,722 |

### 3.7 Category Φ — Confound analysis

On the two soc=S runs with negative zpd_delta_b (runs 10 and 11), Agent A's arc is 59,016 and 9,336 steps respectively — among the fastest A arcs in the batch. Both agents converged on att_blue very early in ENV2. This is the environmental ease confound: on seeds where att_blue is easily located, both agents find it quickly, and Agent B's fast arc reflects the seed condition rather than any social effect. The social observation fired at ENV2 steps 42 and 64 in these runs — the earliest fires in the batch — but the arc_total_steps_b was already large for reasons unrelated to social observation.

The confound operates in both directions. On runs 9, 13, 18, 24, and 34, Agent A's arc is long (440,350–772,162 steps) while Agent B's is comparatively short, with positive zpd_delta. The environmental ease confound does not explain these. The positive zpd_delta on A-slow runs suggests the shared world architecture itself — not social observation — is the source of B's advantage on these seeds.

---

## 4. Discussion

### 4.1 What v1.15 established

The v1.15 iteration, across its four sub-versions, established six things.

The social observation architecture works. The firing gate, the schema state transition, the being_observed substrate, the Q6 statement generation, and the epistemic boundary between corroboration and confirmation all function as designed and are verified across the full batch.

The second-person substrate is real. The being_observed record is the programme's first architectural object that represents an agent as the object of another agent's attention rather than the subject of its own. 23 of 29 events fire on first contact. The substrate holds object_id, step, observer position, and own_mastery_at_step for every event, and resolves cleanly to the social_observation record.

The epistemic boundary holds. Socially_corroborated is not confirmed. Own mastery is required in every case across every version of the architecture. The mean gap from corroboration to confirmation in v1.15.2–3 is 72,977 steps, with individual runs showing gaps of over 660,000 steps. The schema never shortcuts.

Individuation is confirmed. Two agents in a shared world produce distinct developmental arcs. Δ > 0 in 38 of 38 completing runs in v1.15. The distribution of arc lengths, prediction timings, and social observation outcomes is individually variable in ways traceable to each agent's seed and developmental history.

Agent B is faster than the naive baseline. In 11 of 13 soc=S completing runs, zpd_delta_b is positive. The mean acceleration is 115,396 steps. This meets the version map criterion "Agent B's time to att_blue confirmation shorter than naive baseline." The cause of the acceleration is the shared world architecture, not social observation specifically — but the criterion is met.

Q6 statements are produced without hallucination. 29 statements, 29/29 source_resolves=True.

### 4.2 What v1.15 did not establish

The causal claim that social observation shortens the developmental arc is not demonstrated. The arc_total_steps_b values are identical across all four versions for the same seeds, despite three successive interventions. The architectural reason is now understood: the ENV2 directed search toward att_blue is pre-loaded for all agents at the transfer gate, through waypoint injection at ENV2 setup. Both soc=S and soc=- agents enter ENV2 already directed toward att_blue. The social observation fires into a search that was already guided. There is no undirected period for the observation to interrupt.

This is not a failure of the social observation mechanism. The mechanism is correct. It is a failure of the experimental design to isolate the social effect. The ENV2 waypoint injection — essential for the transfer phase to work — is also the reason the ZPD comparison is not measurable.

Isolating the causal effect would require making the ENV2 directed search conditional on social observation: Agent B enters ENV2 with the predicted record but without navigational guidance toward att_blue, and only acquires that guidance when and if it observes Agent A. This would be a substantive architectural change to the transfer phase design, with consequences for arc_complete rates and the comparability of results to prior versions. It is recorded here as an open question.

### 4.3 The being_observed finding as an independent contribution

The programme has not previously produced an architectural object representing an agent as the object of another agent's perception. The being_observed substrate record is structurally distinct from the social_observation record that Agent B holds: where B's record describes what B witnessed, A's record describes the fact of having been witnessed — the step at which A was observed, by whom, at which object, and whether A had already mastered that object. In 23 of 29 events, A had not yet mastered att_blue when observed. In two events (run 11), neither agent had mastered it, and both were simultaneously in the being-observed state.

The SICC framing describes this as the beginning of the relational self: the agent's developmental record now includes not only what it encountered and what it learned, but the fact of having been seen encountering it. Whether this record is accessible to the agent as a cognitive object — whether it can form part of the agent's self-account — depends on architectural additions the current iteration does not introduce. What v1.15 establishes is that the record exists, is correctly timestamped, and carries the right substrate anchors.

---

## 5. Pre-registration and version history

The v1.15 iteration operated under four pre-registration documents:

- v1_15_pre_registration.md — original specification (correct architecture)
- v1_15_pre_registration_amended.md — honest amendment recording the wrong-build deviation and the individuation findings under the alternative developmental question
- v1_15_1_pre_registration.md — correct build specification (v1.15.1–3)
- Amendment 1 of 3: Q6 reporting omission (dict/getattr bug in v1.15.1)

The programme's Category Φ commitment requires that deviations from the version map are reported explicitly in papers. The v1.15 wrong build is reported here. The Q6 bug is reported here. The arc-shortening non-finding is reported here. No results are withheld or reframed.

---

## References

Baker, N.P.M. (2026a) 'v1_15_pre_registration.md', *Synapstak developmental programme internal record*, 8 May 2026.

Baker, N.P.M. (2026b) 'v1_15_pre_registration_amended.md', *Synapstak developmental programme internal record*, 8 May 2026.

Baker, N.P.M. (2026c) 'v1_15_1_pre_registration.md', *Synapstak developmental programme internal record*, 8 May 2026.

Baker, N.P.M. (2026d) *Session carry-over: v1.15.1 batch running*, Synapstak Ltd internal document, 8 May 2026.

Baker, N.P.M. and Pollock, R.V.H. (2025) 'Fluid Learning Architecture in practice', in Pollock, R.V.H., Jefferson, A. and Wick, C. (eds.) *The Six Disciplines of Breakthrough Learning*. 4th edn. Hoboken: Wiley.

Bowlby, J. (1969) *Attachment and Loss: Vol. 1. Attachment*. New York: Basic Books.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Vygotsky, L.S. (1978) *Mind in Society: The Development of Higher Psychological Processes*. Cambridge, MA: Harvard University Press.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
