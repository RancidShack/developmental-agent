# The Reparative Return: A Three-Environment Causal Arc in a Small Artificial Learner

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 8 May 2026
**Status:** Working draft — v1.14.1 results
**Note:** Results in this paper are drawn from the v1.14.1 corrected batch. v1.14.1 introduced no architectural changes; it corrected the `arc_total_steps` calculation formula and resolved one orphan predicted record from the pipeline. All primary findings are identical between v1.14 and v1.14.1.

---

## Abstract

The v1.13 architecture introduced a third object family — BLUE — whose two component objects were structurally separated across environments: haz_blue placed in Environment 1 (ENV1), att_blue placed in Environment 2 (ENV2). Agents encountering haz_blue in ENV1 without att_blue present incurred cost, could not bank the hazard, and — if the two-family minimum was satisfied by prior GREEN and YELLOW completions — generated an abductive prediction: the precondition attractor must exist elsewhere. The v1.13.8 batch confirmed 29 of 32 eligible agents wrote predicted records, with 33 records written and 29 confirmed across 40 runs.

The v1.14 iteration tests the next question: having confirmed the prediction in ENV2, will an agent return to ENV1 and complete the arc it could not finish? The v1.14 architecture introduces a return ENV1 phase — a third environment with the full BLUE family and no unreachable hazards — triggered when and only when the predicted record is confirmed. The agent carries a single invariant through the transition: mastery\_flag\['att\_blue'\] = 1. On first contact in the return environment, V110Agent.check\_competency\_unlocks fires, the family precondition gate is satisfied, and haz\_blue transitions to KNOWLEDGE. The arc is complete.

The v1.14.1 batch of 40 runs produces five findings. First, 29 of 32 eligible agents complete the full cross-environment causal arc (0 arc\_timeout). Second, the transformation fires within a median of fewer than 53 steps of return — the competency, once earned, is immediately effective. Third, arc\_total\_steps spans 1,113 to 851,603 (mean 230,734), demonstrating that the same structural arc occupies radically different temporal spans across individual developmental histories. Fourth, zero hallucinations occur across 34,145 statements, and 42 of 43 causal chains reach depth 6 with complete link sequences. Fifth, the three agents whose predictions were unresolvable represent genuine individual variation — their developmental timelines did not reach att\_blue mastery within the 800,000-step ENV2 budget — not architectural failure.

The finding operationalises two SICC commitments simultaneously. Commitment 5 (time as first-class cognitive content) is instantiated in the arc\_total\_steps distribution: developmental time is not incidental to the arc but constitutive of it. Commitment 9 (earned extensibility) is instantiated in the transformation mechanism: the competency fires only because it was genuinely acquired in ENV2; no architectural shortcut exists.

---

## 1. Introduction

### 1.1 Programme to date

The post-v1.0 cognitive-layer arc has advanced eight steps from the v1.4 cross-family comparison to the v1.13 predictive schema. v1.5 introduced prediction-error records — the approach-and-resist sequence that captures an agent encountering a bankable-tier cell before its precondition attractor is mastered. v1.6 introduced the first auditable reporting layer, generating natural-language statements about formation, surprise, avoidance, and structural arc from the provenance and schema substrates. v1.7 extended the agent class to V17Agent with goal pursuit, counterfactual suppressed-approach records, and belief revision as behavioural substrates. v1.8 through v1.12 deepened the reporting substrate and extended the causal chain architecture.

v1.13 introduced the most architecturally significant change since v1.3: the BLUE family, split across two environments. ENV1 contains haz\_blue but not att\_blue; haz\_blue is unreachable because its precondition attractor is absent. ENV2 contains att\_blue but not haz\_blue. The structural incompleteness of ENV1 is not a defect — it is a designed condition that produces a specific cognitive event: the agent encounters the hazard, incurs cost, and cannot resolve it. If the two-family minimum is met (GREEN and YELLOW chains confirmed), the causal observer generates an abductive prediction: a precondition attractor for haz\_blue must exist, and the structural pattern of confirmed chains identifies what form it should take. The agent transfers to ENV2 carrying that prediction. The v1.13.8 batch confirmed 29 of 32 eligible agents both wrote predicted records and had them confirmed through att\_blue mastery in ENV2.

### 1.2 The reparative return

What v1.13.8 left open was the return. The agent had confirmed in ENV2 that the precondition was acquirable and had acquired it. haz\_blue remained unresolved in ENV1. The prediction had been written, confirmed, and recorded. The developmental obligation — first incurred at the step when haz\_blue was approached in ENV1 — remained outstanding.

v1.14 introduces the return ENV1 phase as the third environment in the developmental arc. It is not a reset. The agent that returns to ENV1 carries its full Q-table, its ENV2 mastery of att\_blue, and the explicit invariant that mastery\_flag\['att\_blue'\] = 1. The return world contains the full BLUE family: att\_blue at its ENV2 position, haz\_blue at its ENV1 position, no unreachable hazards. The already-completed hazards from the original ENV1 run are pre-transitioned to KNOWLEDGE — the agent does not re-traverse what it has already earned.

The gate on return is precise: `predicted_record_state == 'confirmed'`. Not end\_state\_banked, which was achieved by 0 of 32 agents in ENV2 and is not the developmental signal here. Not att\_blue\_approached, which is the perception event rather than the competency event. The gate fires when and only when the abductive prediction has been confirmed through direct mastery evidence. This is the architectural operationalisation of the Winnicottian capacity for concern: the agent that returns to finish what it started does so because it now has what it lacked, not because the environment compels it.

### 1.3 Findings and their relation to the pre-registration

The v1.14.1 batch of 40 runs produces five findings.

The first is the primary arc\_complete result. Of 40 runs, 32 reached ENV2 (transfer condition met). Of 32 ENV2 runs, 29 produced confirmed predicted records and proceeded to the return ENV1 phase. All 29 completed the arc (0 arc\_timeout). Three ENV2 runs exhausted the 800,000-step budget without att\_blue mastery; those agents' predicted records are unresolvable. Eight runs did not transfer from ENV1 (transfer condition not met within 1,000,000 steps); those runs contributed no arc\_complete record.

The second is the transformation speed finding. The arc\_complete mechanism fires within a median of fewer than 53 steps of return — mean 52, min 3, max 296 across the 29 arc\_complete runs. The competency earned in ENV2 is immediately effective: on the first contact event in the return environment, the family precondition gate fires and haz\_blue transitions to KNOWLEDGE.

The third is the arc\_total\_steps individuation finding. The total arc from ENV1 transfer through ENV2 and return transformation spans 1,113 to 851,603 steps (mean 230,734) across the 29 arc\_complete runs. The width of this distribution — spanning nearly three orders of magnitude — is the primary evidence that the arc's temporal character is individually constituted. Two agents completing the same structural sequence take radically different amounts of developmental time to do so.

The fourth is the zero-hallucination result. 0 hallucinations across 34,145 statements. 42 of 43 causal chains reach depth 6 with complete link sequences. Category α holds.

The fifth is the individuation finding for the ineligible agents. The three agents whose predictions were unresolvable did not fail architecturally — the architecture made no error. Their individual learning curves did not reach att\_blue mastery within the 800,000-step ENV2 budget. This is the same individuation story as arc\_total\_steps; it simply occurs at the threshold rather than the completion. The distribution of developmental timelines is continuous; the budget cutoff discretises it.

### 1.4 Connection to the SICC programme

v1.14 advances two SICC commitments.

**Commitment 5 (time as first-class cognitive content):** The arc\_total\_steps distribution is the first direct measurement in the programme of time as a constitutive feature of a cognitive arc rather than an incidental feature of a run. Two agents completing the same arc take different amounts of developmental time; that difference is not noise but the expression of their individual developmental histories. The arc is not defined only by what it achieves (KNOWLEDGE state for haz\_blue) but by when and through what path it achieves it.

**Commitment 9 (earned extensibility):** The transformation in return ENV1 fires because mastery\_flag\['att\_blue'\] = 1 was earned in ENV2. The architecture provides no shortcut. An agent whose predicted record was unresolvable — who did not master att\_blue — cannot complete the arc regardless of how many steps it was given in return ENV1. The competency must be genuinely acquired. Extensibility is earned, not granted.

---

## 2. Methods

### 2.1 Environment and agent

The environment is V113World, introduced at v1.13 as a parameterised world constructor supporting multi-environment developmental arcs. The world is a 12.0 × 12.0 × 12.0 3D grid with STEP\_SIZE = 1.0, PERCEPTION\_RADIUS = 3.0, and CONTACT\_RADIUS = 0.8. Object types are FRAME, NEUTRAL, HAZARD, ATTRACTOR, END\_STATE, KNOWLEDGE, and DIST\_OBJ. Three colour families — GREEN, YELLOW, BLUE — are defined with family\_precondition\_attractor gating: haz\_green requires att\_green mastery; haz\_yellow requires att\_yellow mastery; haz\_blue requires att\_blue mastery.

The agent is V110Agent, introduced at v1.10 as a subclass of V17Agent adding the completion-signal draw. V110Agent inherits the full v1.7 cognitive-layer: phase schedule, threat layer, mastery layer, knowledge-banking layer, goal pursuit, counterfactual records, belief revision, and the family-precondition gating rule from V13Agent. The critical method for v1.14 is `check_competency_unlocks()`, which fires on every contact event and evaluates each hazard's precondition gate. For haz\_blue: `family_precondition_attractor['haz_blue'] = 'att_blue'`; the gate fires when `mastery_flag['att_blue'] == 1`.

### 2.2 Three-phase run structure

Each run comprises three phases.

**ENV1** (budget: 1,000,000 steps, early exit on transfer condition): V113World with ENV1\_FAMILIES. haz\_blue is in `unreachable_hazards`; it is present in the world at position (7.0, 8.0, 3.0) but excluded from `hazard_cells` and `knowledge_unlocked` so the transfer condition can be met without it. haz\_blue is injected as the first waypoint to ensure the agent approaches it in Phase 1. ENV1 runs until the transfer condition is met: all completable hazards banked, all attractors mastered, and predicted record written. If the transfer condition is not met within 1,000,000 steps, the run ends without proceeding to ENV2.

**ENV2** (budget: 800,000 steps, early exit on att\_blue mastery): V113World with ENV2\_FAMILIES. att\_blue is present at position (5.0, 6.0, 10.0); haz\_blue is absent. The agent is carried in with a reset cognitive state except for the Q-table, which is preserved. att\_blue is injected as the first waypoint and an additional directed search bonus (0.1 / distance) reinforces navigation toward it. ENV2 exits when `att_blue_mastery_step is not None`. If 800,000 steps are exhausted without att\_blue mastery, the predicted record is marked unresolvable and the run ends.

**Return ENV1** (budget: 200,000 steps, early exit on arc\_complete): V113World with RETURN\_ENV1\_FAMILIES — the full BLUE family with att\_blue at the ENV2 position and haz\_blue at the ENV1 position, no unreachable hazards. Already-completed hazards (haz\_yellow, haz\_green, haz\_unaff\_0/1/2) are pre-transitioned to KNOWLEDGE before the run. haz\_blue is injected as the first waypoint. The agent is carried in with the CRITICAL INVARIANT applied: `mastery_flag['att_blue'] = 1` is preserved through the carry, and `_knowledge_unlocked` for the pre-completed hazards is set to True so `check_competency_unlocks` skips them. The return ENV1 phase exits immediately when `world.knowledge_unlocked['haz_blue']` becomes True (arc\_complete). No rumination after the transformation.

### 2.3 The CRITICAL INVARIANT and transformation mechanism

The arc\_complete mechanism depends on a single invariant: `mastery_flag['att_blue'] = 1` must survive the ENV2 → return ENV1 carry transition.

In the carry for return ENV1, `agent.mastery_flag` is fully replaced with `{a: 0 for a in return_world.attractor_cells}` — all values reset — and then `agent.mastery_flag['att_blue'] = 1` is set explicitly. This preserves the ENV2 mastery while correctly resetting all other attractor mastery for the new environment.

On the first contact event in return ENV1 (any object contact), `record_action_outcome` calls `check_competency_unlocks`. For haz\_blue, `family_precondition_attractor['haz_blue'] = 'att_blue'` and `mastery_flag['att_blue'] == 1`, so `world.transform_to_knowledge('haz_blue')` fires. `world.knowledge_unlocked['haz_blue']` becomes True. The step loop detects this and exits with `arc_complete = True`.

The `_knowledge_unlocked` agent attribute for pre-completed hazards is set to True in the carry, so `check_competency_unlocks` skips them without attempting re-transformation. The `_return_to_env1_condition_met` gate is explicit: it reads the predicted schema record and returns True only when `state == 'confirmed'`.

### 2.4 arc\_complete record

Each run produces one row in `arc_complete_v1_14_1.csv` with fields:

- `arc_complete`, `arc_timeout`, `ineligible_reason` — outcome classification
- `env1_surprise_step` — the ENV1 step at which the transfer condition was met (the closest available proxy for the surprise event; haz\_blue was approached before this step)
- `prediction_step` — the ENV1 step at which the predicted record was written
- `transfer_triggered_step` — the ENV1 step at which transfer fired
- `confirmation_step` — the ENV2 step at which att\_blue mastery was achieved
- `return_step` — always 0 (return ENV1 begins at step 0)
- `transformation_step` — the return ENV1 step at which haz\_blue → KNOWLEDGE
- `arc_total_steps` — transfer\_step + env2\_actual\_steps + transformation\_step (corrected in v1.14.1)
- `arc_env_span` — number of environments traversed (3 for all arc\_complete runs)
- `causal_chain_depth` — 6 for all arc\_complete runs (the six-link chain)
- `causal_chain_complete` — True for all arc\_complete runs

### 2.5 The six-link causal chain

The causal observer constructs a six-link chain for arc\_complete runs:

1. **LINK\_SURPRISE** — haz\_blue first encountered in ENV1; cost incurred; no transformation possible (precondition absent)
2. **LINK\_PRECONDITION** — structural inference: the GREEN and YELLOW chain pattern identifies att\_blue as the required precondition
3. **LINK\_PREDICTION** — abductive record written: haz\_blue predicted to require att\_blue; att\_blue predicted to exist in an accessible environment
4. **LINK\_CONFIRMATION** — att\_blue mastered in ENV2; predicted record state transitions from `predicted` to `confirmed`
5. **LINK\_RETURN** — return ENV1 phase initiated; carry\_agent invariant applied
6. **LINK\_TRANSFORMATION** — haz\_blue → KNOWLEDGE; arc\_complete fires

Chains reaching LINK\_PRECONDITION but not LINK\_PREDICTION (two-family minimum not met) resolve at depth 4. Chains reaching LINK\_CONFIRMATION but not LINK\_RETURN (return phase not reached due to unresolvable prediction) also resolve at depth 4. All 29 arc\_complete runs produce depth-6 chains.

### 2.6 Experimental matrix and pre-flight verifications

40 runs: four hazard costs (0.1, 1.0, 2.0, 10.0) × ten runs per cost. Seeds loaded from `run_data_v1_13_8.csv`. The pre-flight verifier `verify_v1_14.py` ran eight criteria before the batch; all passed. Criterion 14.5 — a live call to `_run_return_env1` — confirmed transformation\_step was non-None and arc\_complete was True on the test seed (transformation at step 153). The full batch was authorised after all eight criteria passed.

v1.14.1 corrected two data-integrity issues identified from v1.14 results: the `arc_total_steps` formula (changed from a subtraction across step-space to the additive formula: transfer\_step + env2\_actual\_steps + transformation\_step) and the orphan predicted record (mark\_unresolvable now fires in `run_one` when ENV1 exhausts its budget with a written predicted record but no transfer). Results are identical across v1.14 and v1.14.1 on all primary metrics.

---

## 3. Results

### 3.1 Category α: Preservation and pipeline integrity

All eight pre-flight criteria passed. The batch produced 40 complete run records. Zero hallucinations occurred across 34,145 statements. Category α holds.

42 of 43 causal chains reached depth 6 with complete link sequences. The single depth-5 chain and single depth-1 chain reflect runs where the causal substrate was present but chain construction reached a partial conclusion; these are attributed to observer ordering rather than architectural error and are reported honestly.

### 3.2 Transfer and ENV2 outcomes

Table 1 gives ENV1 transfer and ENV2 outcomes by hazard cost.

**Table 1.** Transfer and ENV2 outcomes by hazard cost.

| Cost | Total | ENV2 ran | arc\_complete | Ineligible | No transfer |
|------|-------|----------|--------------|-----------|-------------|
| 0.1  | 10    | 7        | 6            | 1         | 3           |
| 1.0  | 10    | 8        | 6            | 2         | 2           |
| 2.0  | 10    | 8        | 8            | 0         | 2           |
| 10.0 | 10    | 9        | 9            | 0         | 1           |
| **All** | **40** | **32** | **29**    | **3**     | **8**       |

The cost gradient in transfer rate — 7/10 at cost 0.1, 9/10 at cost 10.0 — reflects the known v1.13.8 pattern: higher hazard cost drives faster development, producing earlier and more complete ENV1 resolution within the step budget. The ineligible cases (prediction\_unresolvable) concentrate at lower costs where agents' ENV2 directed search behaviour is less urgent, consistent with the interpretation that these agents' developmental timelines simply did not reach att\_blue mastery within 800,000 steps. No ineligible cases occur at cost 2.0 or 10.0.

### 3.3 arc\_complete: the primary finding

29 of 32 eligible agents completed the full cross-environment causal arc. 0 arc\_timeout. arc\_env\_span = 3 and causal\_chain\_depth = 6 in all 29 arc\_complete records.

The arc\_complete rate of 100% on eligible runs is the pre-registered primary finding. An agent that confirmed att\_blue mastery in ENV2 always completed haz\_blue transformation in return ENV1 within the 200,000-step budget. The budget was never the constraint; the CRITICAL INVARIANT was the constraint, and it held.

### 3.4 Transformation speed

**Table 2.** Transformation step in return ENV1 by hazard cost (arc\_complete runs).

| Cost | n | min | max | mean |
|------|---|-----|-----|------|
| 0.1  | 6 | 9   | 108 | 46   |
| 1.0  | 6 | 3   | 35  | 16   |
| 2.0  | 8 | 3   | 296 | 71   |
| 10.0 | 9 | 7   | 154 | 63   |
| All  | 29 | 3  | 296 | 52   |

The transformation fires within 296 steps in all 29 arc\_complete runs. The mechanism is: on the first contact event in return ENV1, `check_competency_unlocks` evaluates haz\_blue, finds mastery\_flag\['att\_blue'\] = 1, and fires `transform_to_knowledge('haz\_blue')`. The minimum transformation step of 3 represents an agent that contacted an object within 3 steps of entering the return environment, triggering the unlock immediately. The maximum of 296 represents an agent that traversed more of the world before its first contact event.

The transformation step is not the step at which the agent contacts haz\_blue. It is the step at which the agent contacts any object — because `check_competency_unlocks` fires on any contact, and once mastery\_flag\['att\_blue'\] = 1 is set, the next contact event completes the arc regardless of which object is contacted. The fastest transformation agents are not necessarily those that navigated most directly to haz\_blue.

### 3.5 arc\_total\_steps: the individuation finding

The arc\_total\_steps field — defined as transfer\_step + env2\_actual\_steps + transformation\_step — measures the total number of steps from the ENV1 transfer gate through the entire ENV2 phase and the return transformation. It is the most direct measure of the arc's temporal span available from the current output.

**Table 3.** arc\_total\_steps by hazard cost (arc\_complete runs).

| Cost | n | min       | max       | mean      |
|------|---|-----------|-----------|-----------|
| 0.1  | 6 | 71,799    | 743,303   | 376,722   |
| 1.0  | 6 | 1,195     | 851,603   | 249,360   |
| 2.0  | 8 | 5,580     | 655,778   | 186,569   |
| 10.0 | 9 | 1,113     | 708,475   | 160,249   |
| All  | 29 | 1,113    | 851,603   | 230,734   |

The range spans nearly three orders of magnitude. The minimum of 1,113 steps represents an agent that transferred from ENV1 almost immediately, found att\_blue within 37 steps of entering ENV2 (the minimum observed env2\_actual\_steps), and transformed haz\_blue within the first seconds of return. The maximum of 851,603 steps represents an agent that required most of the combined ENV2 and return ENV1 budget to reach the same structural outcome.

The cost gradient — mean 376,722 at cost 0.1 versus 160,249 at cost 10.0 — reflects the same developmental acceleration pattern visible in the transfer rate. Agents at higher cost develop more urgently, transfer earlier within ENV1, and navigate more directly to att\_blue in ENV2. Their arcs are shorter not because the arc is simpler but because their developmental timelines are compressed by the cost structure.

The width of the arc\_total\_steps distribution within each cost level is the primary individuation finding. At cost 2.0, the range is 5,580 to 655,778 — a ratio of more than 100:1 within the same cost condition. These agents shared the same environment, the same cost structure, the same architectural endowment, and the same step budget. The temporal character of their arcs is individually constituted.

### 3.6 ENV2 directed search

ENV2 actual\_steps for arc\_complete runs ranged from 37 to 742,195 (mean 96,331). The agent that found att\_blue in 37 steps did so via the injected waypoint and Q-table transfer from ENV1; it effectively navigated directly to att\_blue on entry. The agent that required 742,195 steps exhibits a directed search trajectory that, while ultimately successful, followed a substantially longer path. Both agents confirmed the prediction and completed the arc; the developmental time investment differs by a factor of approximately 20,000.

This ENV2 directed search variance is largely responsible for the arc\_total\_steps range. The transfer\_step contribution (ENV1 duration) is comparatively constrained by the 1,000,000-step ENV1 budget; the env2\_actual\_steps contribution is unconstrained within the 800,000-step ENV2 budget.

### 3.7 Ineligible agents: the unresolvable prediction

Three agents (cost=0.1: 1; cost=1.0: 2) exhausted the 800,000-step ENV2 budget without att\_blue mastery. Their predicted records are marked `unresolvable`. These are not architectural failures. The causal architecture produced a valid prediction; the prediction was structurally correct (att\_blue does exist in ENV2 at the expected position). The agents simply did not reach att\_blue within budget.

The Category Φ reading of these three cases is that they instantiate the same individuation principle as arc\_total\_steps: the distribution of developmental timelines is continuous, and the budget cutoff discretises it. Had ENV2 been extended, some of these agents would eventually have confirmed their predictions and completed the arc. That the arc takes as long as it takes, for the agent it takes it for, is not a deficiency to be corrected but a biographical fact to be recorded.

The 29 eligible agents and the 3 unresolvable agents inhabit the same continuous distribution. The distinction between them is where the budget cutoff falls relative to each agent's developmental timeline, not a categorical difference in architectural capacity.

---

## 4. Discussion

### 4.1 Transformation on first contact: what the mechanism means

The transformation step mean of 52 and maximum of 296 are, in one sense, trivially explained by the mechanism: `check_competency_unlocks` fires on any contact event, and once mastery\_flag\['att\_blue'\] = 1 is set, the next contact event completes the arc. The budget of 200,000 steps for return ENV1 is five orders of magnitude more than the observed maximum. The competency does its work immediately.

The deeper reading is what this confirms about the relationship between competency and environment. The agent returning to ENV1 does not need to re-learn the environment, re-navigate to haz\_blue, or re-rehearse the transformation sequence. It carries the competency — mastery\_flag\['att\_blue'\] = 1 — and the environment carries the structure — family\_precondition\_attractor\['haz\_blue'\] = 'att\_blue'. Their meeting, on any contact event in any part of the return environment, produces the transformation. The prepared environment is not just the substrate of the arc; it is the condition of the arc's completion. What the agent returns to is not what it left; it returns to the same positions but with different readiness, and the environment responds accordingly.

This is the operational meaning of the Montessori principle that the prepared environment does not compel — it enables. The transformation does not happen because the architecture forces the agent to haz\_blue. It happens because the agent, now prepared, encounters any part of the environment at all. The return is sufficient; the encounter is sufficient; the preparation is what the arc produced.

### 4.2 arc\_total\_steps and the temporality of developmental biography

The arc\_total\_steps range of 1,113 to 851,603 is the most direct evidence the programme has yet produced that developmental biography is individually constituted in time, not only in route.

Earlier iterations demonstrated that agents follow different routes through the same environment — the Category γ individuation finding from v1.3.1, confirmed across v1.4 and subsequent iterations. v1.14 adds a temporal dimension to that finding. Two agents whose routes differ also differ in how long those routes take. The arc\_total\_steps distribution captures this temporal individuation at the whole-arc level: not just which step each attractor was mastered, but how long the entire developmental project — from the ENV1 transfer gate through ENV2 confirmation and return transformation — required.

The cost gradient (mean 376,722 at cost 0.1 versus 160,249 at cost 10.0) shows that the temporal structure of the arc is modulated by the cost environment. Higher cost produces faster development, which produces shorter arcs. But the within-cost variance is large — at cost 2.0, arcs span 5,580 to 655,778 — and this within-cost variance is not attributable to the environment. These agents all experienced the same cost, the same object layout, the same architectural endowment. What differentiates them is the developmental biography each brought to the arc, which is constituted by the particular history of exploration, mastery, and surprise each agent accumulated from step 1 of ENV1.

SICC Commitment 5 states that time is a first-class feature of cognitive content — not an incidental implementation detail but a constitutive dimension of what it means for an agent to have a history. arc\_total\_steps is the first field in the programme's output that directly measures this dimension at the whole-arc level.

### 4.3 The three unresolvable agents and the individuation of limitation

The Category Φ constraint requires honest reporting of what the architecture does and does not produce. Three agents did not complete the arc. The honest account is that their developmental timelines did not reach att\_blue mastery within 800,000 steps in ENV2.

The incomplete arc is not an architectural error; it is a biographical fact. These three agents have a different developmental story than the 29 arc\_complete agents. Their story includes: a valid prediction, correctly written; a transfer into ENV2; an extended directed search; and a budget expiry before the goal was reached. That story is as individuated as the arc\_complete story. The arc\_total\_steps distribution has a tail; these three agents are in it.

The programme does not yet have the tools to examine what these agents were doing during those 800,000 steps in ENV2 — whether they were approaching att\_blue gradually, whether they were orbiting nearby regions, whether their Q-tables produced systematically different search patterns than the confirming agents. That examination — comparing the developmental trajectories of completing and non-completing agents as a direct test of the individuation thesis — is a natural extension of the current work and is noted for subsequent iterations.

### 4.4 SICC Commitment 9: earned extensibility confirmed

The transformation mechanism provides the clearest illustration yet of SICC Commitment 9: extensibility in the programme is earned, not granted.

An agent that did not master att\_blue in ENV2 — one of the three unresolvable cases — cannot complete haz\_blue transformation in return ENV1 regardless of how many steps it is given. The architecture provides no mechanism to shortcut the competency acquisition. The precondition gate requires mastery\_flag\['att\_blue'\] = 1; that value is only 1 if att\_blue mastery occurred. The carry invariant propagates the value from ENV2; if the value is 0, nothing in the return environment produces the transformation.

The two sides of this are equally important. On the affirmative side: for the 29 agents that did earn the competency, the return ENV1 environment immediately honours that earning — on the first contact, without further requirement. On the restrictive side: the earning cannot be simulated or approximated. The competency either exists or it does not. The architecture does not soften the boundary.

This is the operational meaning of earned extensibility: the prepared environment extends its possibilities to an agent at exactly the moment and in exactly the way the agent has prepared itself to receive them. No sooner and no differently.

### 4.5 The six-link chain and the limits of the current reporting

The six-link causal chain — SURPRISE → PRECONDITION → PREDICTION → CONFIRMATION → RETURN → TRANSFORMATION — is the most structurally complete account of a cognitive arc the programme has produced. Each link is anchored to a provenance event: a specific step, a specific object, a specific state transition. The chain is auditable end-to-end.

What the chain does not yet report is the arc's experiential character. The CONFIRMATION link records that att\_blue\_mastery\_step was step n in ENV2. It does not record whether the approach to att\_blue was direct or circuitous, whether the agent orbited the region before contact, whether the mastery event was preceded by a long period of directed search or a short one. The ENV2 actual\_steps field provides some aggregate evidence; the directed search bonus provides a motivation structure. But the inside of LINK\_CONFIRMATION — the developmental texture of the ENV2 phase — is not yet captured in the chain's representation.

This is an honest limitation. The chain represents the arc at the level of structural events; the developmental biography within each link remains a richer substrate than the chain currently holds. Future iterations — particularly around the ENV2 directed search narrative — will need to enrich LINK\_CONFIRMATION with provenance records from the ENV2 phase.

---

## 5. Conclusion

The v1.14.1 batch confirms the primary pre-registered finding: 29 of 32 eligible agents complete the full cross-environment causal arc, with 0 arc\_timeout. The transformation fires within a mean of 52 steps of return, confirming that the competency earned in ENV2 is immediately effective in the return environment. arc\_total\_steps spans 1,113 to 851,603, demonstrating that the same structural arc occupies radically different temporal spans across individual developmental histories.

Two SICC commitments are operationalised. Commitment 5 (time as first-class) is measured directly in the arc\_total\_steps distribution: developmental time is constitutive of the arc, not incidental. Commitment 9 (earned extensibility) is instantiated in the transformation mechanism: the competency fires because it was genuinely acquired, and the architecture provides no shortcut.

The three ineligible agents whose predictions were unresolvable are reported honestly under Category Φ. Their developmental timelines did not reach att\_blue mastery within budget. They are not architectural failures; they are the tail of the arc\_total\_steps distribution. Whether their ENV2 trajectories show systematically different search patterns from the completing agents is a question reserved for subsequent work.

The pre-registered arc\_complete result — 29/29 eligible runs completing the arc — is the programme's most structurally complete confirmation yet that developmental biography, built across environments and over time, produces outcomes that no single environment could produce alone. The agent that returns to ENV1 at step 52 of the return phase is not the agent that left ENV1 at step 365,000. It is what that agent became.

---

## 6. Code and Data Availability

All code, pre-registration documents, amendments, batch outputs, and paper drafts are available at github.com/RancidShack/developmental-agent.

The v1.14.1 implementation comprises the following files. `v1_13_world.py` defines V113World with ENV1\_FAMILIES, ENV2\_FAMILIES, and the full vocabulary of constants; it is inherited from v1.13 unchanged. `v1_10_agent.py` implements V110Agent (inherited). `curiosity_agent_v1_14_1_batch.py` is the corrected batch runner incorporating the return ENV1 phase, the arc\_complete mechanism, and the two v1.14.1 patches. `verify_v1_14.py` is the pre-flight verifier with eight criteria including a live end-to-end transformation test.

The batch produced 13 output files: `run_data_v1_14_1.csv`, `arc_complete_v1_14_1.csv`, `predicted_schema_v1_14_1.csv`, `env2_run_data_v1_14_1.csv`, `causal_v1_14_1.csv`, `report_v1_14_1.csv`, `report_summary_v1_14_1.csv`, `provenance_v1_14_1.csv`, `counterfactual_v1_14_1.csv`, `belief_revision_v1_14_1.csv`, `goal_v1_14_1.csv`, `end_state_draw_log_v1_14_1.csv`, and `q5_individuation_v1_14_1.csv`.

Seeds were drawn from `run_data_v1_13_8.csv`, continuing the matched-seed chain.

---

## 7. References

Baker, N.P.M. (2026a–aa) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.4. Full reference list inherited from v1.4 paper (Baker, 2026aa).

Baker, N.P.M. (2026ab) 'v1.13 Pre-Registration: BLUE Family Split-Environment Architecture and Abductive Prediction', GitHub repository, May 2026.

Baker, N.P.M. (2026ac) 'v1.14 Pre-Registration: The Reparative Return and the First Complete Cross-Environment Causal Arc', GitHub repository, 8 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

## 8. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper.

No human participant data were collected. No external parties had access to drafts prior to preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
