# v1.15.1 Pre-Registration: Witnessed Navigation and the Socially Corroborated Prediction

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 8 May 2026
**Status:** Pre-registration committed before any v1.15.1 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Supersedes:** Unanswered components of v1.15 pre-registration (8 May 2026)
**Amendment budget:** Three

---

## 1. Purpose

v1.15.1 implements the primary developmental question of the v1.15 version map specification, which the v1.15 iteration did not answer:

> Does witnessed navigation inform an open prediction, and does social observation shorten the developmental arc?

The v1.15 iteration confirmed that two agents in the same world produce individuated developmental timelines. It did not implement inter-agent perception and therefore could not test whether witnessed navigation updates a prediction state. v1.15.1 adds the social observation layer to the validated v1.15 architecture and answers the stated question.

The SICC document (v0\_9, §8) provides the exact specification:

> Agent B, searching for att\_blue in Environment 2, observes Agent A approach att\_blue without cost. The observation is not just that the object is safe. It is that the object answers my open question. The social corroboration of a predicted schema record is a more powerful update than the corroboration of a simple preference: not only does Agent B's prediction receive support, but Agent B now knows where the answer is. The scaffold is not instruction. It is witnessed search — and it reduces the remaining distance to confirmation from the entire environment to a specific location.

---

## 2. Architectural specification

v1.15.1 inherits the complete v1.15 architecture unchanged and adds four targeted components. The single-architectural-change discipline applies: each component is necessary to answer the stated question; none goes beyond it.

### 2.1 Inter-agent perception

Agent B maintains a perception of Agent A's position at every step. When Agent A is within PERCEPTION\_RADIUS (3.0) of Agent B's current position, Agent B's observation includes an AGENT object at Agent A's position. Agent B does not observe Agent A's cognitive state — only its position and (by inference from behaviour) its relationship to nearby objects.

The AGENT object type is new. It is not HAZARD, ATTRACTOR, KNOWLEDGE, or DIST\_OBJ. It carries no cost and no mastery signal. Its presence is a positional fact, not a semantic one. Agent B's Q-table can develop preferences about proximity to AGENT objects, but this is not engineered — it is observed.

Agent A's perception is symmetric: Agent A perceives Agent B when within PERCEPTION\_RADIUS. This symmetry produces the being\_observed record (§2.4) without requiring asymmetric architecture.

### 2.2 Social observation mechanism

The social observation fires in ENV2 when all three conditions are simultaneously true:

1. Agent B holds an open prediction for haz\_blue (schema\_v13\_obs state == 'predicted')
2. Agent A is within CONTACT\_RADIUS (0.8) of att\_blue — Agent A is at the predicted location
3. Agent B is within PERCEPTION\_RADIUS of Agent A's position — Agent B can perceive Agent A

When these conditions are met:

- A social observation event is recorded at step M in Agent B's social\_observation substrate
- Agent B's predicted schema record transitions to SOCIALLY\_CORROBORATED\_STATE
- att\_blue's position is injected as Agent B's next waypoint (the search space is reduced to a point)
- A being\_observed event is recorded in Agent A's substrate at step M

The social observation fires once per prediction per agent. It does not fire again for the same object\_id if the record is already socially corroborated.

### 2.3 Socially corroborated schema state

The v1.13 schema extension (V13SchemaObserver) is extended with a fourth state:

```
PREDICTED_STATE          = "predicted"
SOCIALLY_CORROBORATED_STATE = "socially_corroborated"   ← v1.15.1 new
CONFIRMED_STATE          = "confirmed"
UNRESOLVABLE_STATE       = "unresolvable"
```

State transitions:
- predicted → socially\_corroborated: social observation fires (§2.2)
- socially\_corroborated → confirmed: Agent B masters att\_blue independently
- socially\_corroborated → unresolvable: ENV2 budget exhausted without mastery
- predicted → confirmed: Agent B masters att\_blue without prior social observation (same as v1.14)
- predicted → unresolvable: budget exhausted without social observation or mastery

A socially corroborated record that is not subsequently confirmed is not a confirmation. The Q6 statement is explicit: own mastery is still required. Social corroboration reduces the search space; it does not replace the developmental work.

The socially\_corroborated state is architecturally distinct from confirmed and from predicted. It is a third epistemic state with a different substrate anchor: a social observation event rather than a personal mastery event.

### 2.4 Being\_observed record

When Agent A is within CONTACT\_RADIUS of att\_blue and Agent B is within PERCEPTION\_RADIUS of Agent A, Agent A receives a being\_observed record in its provenance substrate:

```
{
    "step":           M,
    "observed_by":    "b",
    "object_id":      "att_blue",
    "observer_pos":   (x, y, z),
    "own_mastery":    True/False  # has Agent A already mastered att_blue at step M?
}
```

This is the programme's first second-person substrate record. Agent A has a record of having been seen at the moment of its own contact with att\_blue. It does not know whether Agent B used the observation. It knows only that it was perceived.

The being\_observed record is written to Agent A's provenance substrate regardless of whether Agent B holds an open prediction. The condition for writing is purely observational: Agent A at att\_blue, Agent B within range. Whether Agent B's prediction state was updated is recorded separately.

### 2.5 Q6 statement

The reporting layer generates a Q6 statement for every run in which a socially\_corroborated record exists:

> I predicted att\_blue exists as the precondition for haz\_blue at step N, from the structural pattern of my YELLOW and GREEN family causal chains. At step M in Environment 2, I observed Agent A approach att\_blue without cost. This observation socially corroborates my prediction and locates the target. My predicted record is updated to socially\_corroborated. I know where to find it. Confirmation requires my own mastery.

The Q6 statement reports temporal relationships, not causal ones. The substrate confirms that observation preceded formation. It does not confirm that observation caused formation. The inference is the reader's to make.

Q6 statements are auditable at every link. The prediction step, the social observation step, the confirmation step (if any), and the being\_observed record in Agent A are all substrate-anchored. An agent that reports social corroboration without a social\_observation substrate entry is producing the most sophisticated hallucination the programme has considered — the premature closure of an open question based on claimed witnessing. Category α applies with full force.

### 2.6 ZPD measurement

The Zone of Proximal Development (Vygotsky, §2.1 of SICC v0\_9) is operationalised as the difference between Agent B's arc\_total\_steps in a paired run and the mean arc\_total\_steps in the v1.14.1 naive baseline.

```
zpd_delta = v1_14_1_baseline_mean - agent_b_arc_total_steps
```

v1.14.1 baseline mean: 230,734 steps (40-run batch, all arc\_complete runs).

A positive zpd\_delta means Agent B completed the arc faster than the naive baseline. A negative zpd\_delta means it took longer. The zpd\_delta is reported per run and in aggregate.

The ZPD hypothesis: runs where social corroboration fired (socially\_corroborated → confirmed) show a positive mean zpd\_delta. Runs where social corroboration did not fire (predicted → confirmed or predicted → unresolvable) do not show a consistent zpd\_delta effect.

This is the primary pre-registered prediction for Category γ (v1.15.1).

---

## 3. New output files

`social_observation_v1_15_1.csv` — one row per social observation event:
- arch, run\_idx, agent (b), seed, hazard\_cost
- observation\_step, observer\_pos, observed\_agent (a), observed\_agent\_pos
- object\_id (att\_blue), predicted\_record\_pre\_state, predicted\_record\_post\_state

`being_observed_v1_15_1.csv` — one row per being\_observed event:
- arch, run\_idx, agent (a), seed, hazard\_cost
- step, observed\_by (b), object\_id, observer\_pos, own\_mastery\_at\_step

All v1.15 outputs preserved. arc\_complete\_v1\_15\_1.csv gains:
- social\_corroboration\_fired (bool)
- social\_observation\_step
- zpd\_delta

arc\_paired\_v1\_15\_1.csv gains:
- social\_corroboration\_fired\_b (bool)
- zpd\_delta\_b
- being\_observed\_fired\_a (bool)

---

## 4. Experimental matrix

40 runs: four hazard costs (0.1, 1.0, 2.0, 10.0) × ten runs per cost. Seeds from run\_data\_v1\_15.csv (agent\_a seeds). seed\_b = seed\_a + SEED\_B\_OFFSET (20,000). Same seed chain as v1.15.

Agent A is defined as the agent whose seed matches the run\_data\_v1\_15.csv seed\_a value. Agent B is the observed agent — the one whose developmental arc is being tested for ZPD effect.

Note on Agent A's developmental stage: for the social observation to fire, Agent A must reach att\_blue in ENV2 before Agent B. This is not guaranteed and is not engineered. Runs where Agent B reaches att\_blue before Agent A — or where both reach it simultaneously — are reported under Category δ (witnessing conditions not met). These are not failures; they are the boundary conditions of the ZPD.

---

## 5. Pre-registered interpretation categories

### 5.1 Category α: Integrity under social observation layer

With `--no-social` (social observation disabled), the v1.15.1 batch produces output identical to v1.15 at matched seeds. Zero hallucinations in Q6 statements — every Q6 social corroboration claim resolves to a social\_observation substrate record.

A Q6 statement claiming social corroboration without a corresponding social\_observation record at the stated step is a hallucination. The architecture must not produce this. Category α fails if any such statement occurs.

### 5.2 Category β: Socially corroborated state distinct from confirmed

A socially corroborated record is not a confirmation. Agent B's arc\_complete requires independent att\_blue mastery regardless of social corroboration state. Category β succeeds if every arc\_complete record for Agent B carries confirmation\_step > social\_observation\_step — own mastery after witnessing, never instead of it.

### 5.3 Category γ: ZPD operationalised

Primary pre-registered prediction: runs where social corroboration fires show a positive mean zpd\_delta (Agent B's arc shorter than the v1.14.1 naive baseline). Runs where social corroboration does not fire do not show a consistent zpd\_delta direction.

The threshold: the mean zpd\_delta for socially corroborated runs should be positive and the difference between corroborated and non-corroborated zpd\_delta distributions should be distinguishable at the 40-run level. The programme does not claim statistical significance at this run count; it claims directional evidence sufficient to motivate the hypothesis.

Category γ fails if the mean zpd\_delta for socially corroborated runs is negative (Agent B took longer after witnessing) or zero (witnessing had no effect). Both would be reported honestly.

### 5.4 Category δ: Witnessing conditions honestly reported

Not every run will produce a social observation event. Agent A may not reach att\_blue before Agent B. Both agents may arrive simultaneously. Agent B may not hold an open prediction at the moment of observation (prediction may already be unresolvable). These cases are reported under Category δ as boundary conditions, not failures.

The pre-registered expectation: social corroboration fires in at least 15 of the 32 runs expected to reach ENV2 (based on v1.14.1 transfer rates). If it fires in fewer, the ZPD hypothesis is not refuted — it means the witnessing condition was rarely met — and the architecture is reported honestly.

### 5.5 Category Φ: Honesty constraint on social corroboration claim

The claim: social observation accelerates the developmental arc. The deflationary alternative: the timing of social corroboration is confounded with general environmental richness — runs where both agents reach ENV2 and att\_blue early are generally fast runs, and the zpd\_delta merely reflects that the run was easy for both agents, not that witnessing helped.

The pre-registered test for this confound: compare Agent A's arc\_total\_steps against Agent B's arc\_total\_steps in the same run. If zpd\_delta is positive for Agent B but Agent A's arc was also short, the effect may be environmental rather than social. The paired row provides both values.

If the confound is present, it is reported. The programme does not suppress the deflationary reading.

### 5.6 Category Ω: The architectural statement claim

Category Ω succeeds if Categories α, β, γ, and Φ all produce honest positive findings:

Witnessed navigation informs an open prediction. When Agent B observes Agent A at the location its own prediction identified, the search space is reduced from the environment to a point. The predicted schema record transitions to socially corroborated. Agent B's arc is shorter than the naive baseline. Agent A has a being\_observed record of the moment it was seen. The Q6 statement is produced without hallucination.

The SICC document formulation: *The self is not constituted by watching another self succeed. It is constituted by doing the work itself, informed by what it witnessed.*

The substrate must support both halves of that sentence. Category Ω tests whether it does.

---

## 6. Pre-flight verification criteria (eight levels)

Inherits v1.15 criteria 15.1–15.4 (AgentCtx, cognitive independence, CRITICAL INVARIANT, shared mutation).

New criteria:
- **15.1.1:** Inter-agent perception fires when Agent A is within PERCEPTION\_RADIUS of Agent B and does not fire when outside
- **15.1.2:** Social observation fires correctly — all three conditions (prediction open, Agent A at att\_blue, Agent B within range) required simultaneously
- **15.1.3:** Schema state transitions: predicted → socially\_corroborated fires on social observation; socially\_corroborated → confirmed requires independent mastery
- **15.1.4:** Q6 statement produced for socially corroborated record; not produced for predicted or confirmed without social observation; no hallucination in either case

---

## 7. Connection to SICC commitments

**Commitment 11 (auditable, not oracular):** The socially corroborated state is the programme's first substrate record that could be mistaken for a confirmation. The architecture must distinguish them exactly. A prediction that is socially corroborated but not personally confirmed is not confirmed. The being\_observed record and the social\_observation substrate are the audit trail.

**SICC entity question at v1.15.1:** At what point does this agent have a sense of other? The being\_observed record — the first second-person substrate — is the architectural moment at which the programme begins to answer this. An agent that has a record of having been seen, at the moment of its own contact with the object another agent was searching for, is not merely self-aware. It is beginning to be socially aware. Whether that constitutes a sense of other in any philosophically substantive sense is the question v1.15.1 positions the programme to ask.

---

## 8. Methodological commitments

Pre-registration before code. This document committed before any v1.15.1 implementation begins.

Single-architectural-change discipline. Four additions (inter-agent perception, social observation, Q6 generator, being\_observed record) are each necessary to answer the stated question. No addition goes beyond it.

Seed chain continuity. Seeds from run\_data\_v1\_15.csv. seed\_b = seed\_a + 20,000. Matched to v1.15 for direct comparison.

Amendment budget: three. One provisionally reserved for the witnessing-conditions boundary (Agent A/B arrival order). Two available.

---

**Pre-registration commitment:** Committed to github.com/RancidShack/developmental-agent on 8 May 2026, before any v1.15.1 code is written.
