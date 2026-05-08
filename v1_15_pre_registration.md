# v1.15 Pre-Registration: Developmental Individuation in a Shared Prepared Environment — Two Agents, One World

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 8 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.15 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

The v1.14 iteration confirmed that 29 of 32 eligible agents complete the full three-environment causal arc — ENV1 surprise, ENV2 confirmation, return ENV1 transformation — within a single developmental run. arc\_total\_steps ranged from 1,113 to 851,603 (mean 230,734), establishing that the same structural arc occupies radically different temporal spans across individual developmental histories. The three unresolvable agents did not complete the arc within budget; their developmental timelines simply did not reach att\_blue mastery within 800,000 steps.

Every run in the programme to date has involved a single agent in a single world instance. The individuation findings — different routes, different timelines, different causal sequences — are compelling evidence that the architecture produces genuinely distinct developmental biographies. But they are confounded by the fact that each agent runs in isolation. No run has tested whether two agents, given the same prepared environment simultaneously, produce the same developmental biography or different ones.

The v1.15 iteration places two V110Agents in a single shared V113World instance. Each agent has its own cognitive state — its own Q-table, mastery\_flag, knowledge\_banked, phase schedule, and all inherited cognitive-layer structures. The world is shared: object positions are identical, and object-type mutations (HAZARD → KNOWLEDGE transformations) propagate to both agents immediately. The two agents run simultaneously, alternating steps within each world tick.

The primary question is whether the developmental biography is intrinsic to each agent or a product of the environment. If individuation is intrinsic, two agents in the same world will follow different developmental paths, reach different objects at different steps, and complete the arc at different times — possibly very different times, as v1.14's arc\_total\_steps distribution suggests they might. If individuation collapses under shared environment — if the two agents converge toward the same path because the world's state changes synchronously — the finding challenges the biography thesis.

A secondary question follows from the shared world: when agent A transforms haz\_blue to KNOWLEDGE via the v1.14 arc, the world's object\_type changes. Agent B, which may not have mastered att\_blue, now encounters haz\_blue as KNOWLEDGE rather than HAZARD. The cost is no longer incurred. The prediction — which fires only on haz\_blue surprise (cost incurred, transformation impossible) — may never be written by agent B. The v1.15 architecture must handle this case explicitly. Whether agent B's developmental path is altered — accelerated, disrupted, or redirected — by agent A's prior transformation is the secondary finding of the iteration.

---

## 2. Architectural specification

v1.15 inherits v1.13/v1.14 unchanged except for the addition of the two-agent runner and the inter-agent perception layer. The single-variable-change discipline extends: v1.15 introduces the shared-world multi-agent run as the singular architectural extension.

### 2.1 The shared world

A single V113World instance is created per run. Both agents operate within this instance. Object positions are identical for both agents. Object-type mutations — `transform_to_knowledge(object_id)` — write to the shared `object_type` dict; both agents observe the mutation on their next perception event.

The world's `knowledge_unlocked` dict is shared. This has the following implication: if agent A's `check_competency_unlocks` fires `world.transform_to_knowledge('haz_blue')`, `world.knowledge_unlocked['haz_blue']` becomes True for both agents simultaneously. Agent B, which may not have mastered att\_blue, will encounter haz\_blue as KNOWLEDGE on its next contact. It will not incur cost; it will not write a predicted record; its competency for haz\_blue will be updated via `update_knowledge_layer` rather than the family precondition gate.

This is not a failure mode. It is a designed condition that tests whether the developmental sequence can be shortcut by environmental modification. The pre-registered interpretation (Section 6.3) addresses both outcomes.

### 2.2 Agent construction and cognitive independence

Two V110Agent instances are constructed for each run: `agent_a` and `agent_b`. Each has an independent cognitive state:

- Independent Q-tables (initialised with the same architecture, different behaviour from the first divergent action)
- Independent mastery\_flag, knowledge\_banked, \_knowledge\_unlocked
- Independent threat\_flag, phase schedule, visit\_counts
- Independent provenance store, causal observer, and all parallel observers

The two agents do not share any cognitive state. There is no mechanism by which agent A's mastery of att\_blue sets mastery\_flag\['att\_blue'\] = 1 in agent B. The only shared state is the world's object\_type dict.

Each agent uses a different seed, drawn from the same seed chain used in v1.13/v1.14. The two seeds per run are specified in advance and committed to the pre-registration.

### 2.3 Step alternation

Within each world tick, agent A takes one step and then agent B takes one step. The world is not advanced simultaneously; actions resolve sequentially in a fixed A-then-B order. This is the simplest alternation rule that allows both agents to operate in the same environment without requiring a simultaneous-action resolution protocol.

A fixed ordering (A always acts before B within each tick) introduces a first-mover advantage: agent A's action may change the world state before agent B acts. This is reported honestly as a feature of the current implementation. A simultaneous-action variant is reserved for a subsequent iteration.

### 2.4 Inter-agent perception

In v1.15, each agent is invisible to the other. Neither agent's position appears in the other's perception radius; neither agent's presence affects the other's state observations. This isolates the individuation question from social perception: any divergence or convergence in developmental trajectories must be attributed to the shared world state rather than to direct mutual observation.

The addition of agent perception — each agent perceiving the other as a new object type AGENT within PERCEPTION\_RADIUS — is reserved for v1.15.1 or a subsequent iteration.

### 2.5 Three-phase structure

The v1.15 run follows the v1.14 three-phase structure for each agent independently:

**ENV1:** Both agents run simultaneously in ENV1. Each agent independently evaluates the transfer condition. ENV1 terminates when both agents have either met the transfer condition or exhausted the budget. Each agent carries its own `predicted_record_written` flag and its own `transfer_triggered_step`.

**ENV2:** Agents are carried to ENV2 independently. If agent A met the transfer condition but agent B did not, agent A proceeds to ENV2 and agent B's run is recorded as no-transfer. ENV2 runs both eligible agents simultaneously in a shared ENV2 world instance (same object positions, shared knowledge\_unlocked). Each agent independently evaluates att\_blue mastery. ENV2 terminates when both eligible agents have either confirmed att\_blue mastery or exhausted the budget.

**Return ENV1:** Both agents that confirmed att\_blue mastery are carried to the return ENV1 phase. The shared return world is constructed with RETURN\_ENV1\_FAMILIES and no unreachable hazards. Pre-transitions are applied per agent's ENV1 completion record: an object is pre-transitioned only if both agents completed it in ENV1 (the conservative choice; this is committed and not subject to amendment without budget expenditure). Each agent's CRITICAL INVARIANT is applied independently. The return ENV1 phase terminates when both eligible agents have either achieved arc\_complete or exhausted the budget.

### 2.6 arc\_complete record for two-agent runs

Each run produces two arc\_complete rows — one per agent — plus a paired comparison row. The paired comparison row contains:

- `run_idx`, `seed_a`, `seed_b`, `hazard_cost`
- `arc_complete_a`, `arc_complete_b` — individual arc outcomes
- `both_arc_complete` — True if both agents completed the arc
- `arc_total_steps_a`, `arc_total_steps_b` — individual arc durations
- `arc_total_steps_delta` — |arc\_total\_steps\_a − arc\_total\_steps\_b|
- `transformation_step_a`, `transformation_step_b`
- `transfer_triggered_step_a`, `transfer_triggered_step_b`
- `env2_actual_steps_a`, `env2_actual_steps_b`
- `first_transformer` — 'a' or 'b' or 'tie' (which agent transformed haz\_blue first)
- `haz_blue_shared_benefit` — True if one agent's transformation preceded the other's att\_blue mastery (the second agent encountered haz\_blue as KNOWLEDGE)
- `individuation_confirmed` — True if arc\_total\_steps\_delta > 0 (different developmental timelines)

---

## 3. Experimental matrix

40 runs: four hazard costs (0.1, 1.0, 2.0, 10.0) × ten runs per cost. Each run uses two seeds from the v1.14.1 seed chain: seed\_a = seed from `run_data_v1_14_1.csv` at (cost, run\_idx); seed\_b = seed\_a + 20,000 (offset to avoid correlation while maintaining reproducibility).

All 40 paired arc\_complete records are produced regardless of individual agent outcomes.

---

## 4. Pre-flight verifications

Seven verification levels are required before the v1.15 batch runs.

**Levels 1–6:** Inherited from v1.14 pipeline (v1.14 pre-flight criteria 14.1–14.6 and 14.8).

**Level 7 (two-agent independence):** Construct a shared V113World with RETURN\_ENV1\_FAMILIES. Create agent\_a and agent\_b with different seeds. Apply the CRITICAL INVARIANT to both. Run 100 steps alternating A and B. Verify: (a) mastery\_flag\['att\_blue'\] = 1 in both agents after carry; (b) arc\_complete fires independently for each agent when haz\_blue → KNOWLEDGE; (c) agent\_a's cognitive state (mastery\_flag, Q-table values) is not identical to agent\_b's at step 100.

All seven verifications are pre-conditions for the v1.15 batch.

---

## 5. Metrics

All v1.14 metrics are retained for each agent individually. The following are added for v1.15.

**Per-agent metrics (per run, two rows per run):** All v1.14 arc\_complete fields with agent suffix: `arc_complete_a/b`, `transformation_step_a/b`, `arc_total_steps_a/b`, `env2_actual_steps_a/b`.

**Paired comparison metrics (one row per run):** As specified in Section 2.6: `arc_total_steps_delta`, `first_transformer`, `haz_blue_shared_benefit`, `individuation_confirmed`.

**Individuation distribution:** Across all runs where both agents complete the arc: distribution of `arc_total_steps_delta` (absolute difference in arc duration between the two agents). This is the Category γ substrate for v1.15.

**Shared-benefit cases:** Count of runs where `haz_blue_shared_benefit = True`. Distribution of the developmental-stage difference between the first transformer and the second agent at the time of transformation (did the second agent have att\_blue mastery already, or did the world change before it did?).

---

## 6. Pre-registered interpretation categories

Six interpretation categories are pre-registered.

### 6.1 Category α: Preservation of v1.14 architecture under two-agent extension

With `--single-agent` (one agent only, identical to v1.14 behaviour), the v1.15 batch runner produces output identical to the v1.14.1 baseline at matched seeds. Category α succeeds if all seven pre-flight verifications pass.

### 6.2 Category β: Cognitive independence confirmed

Each agent maintains an independent cognitive state throughout all three phases. `mastery_flag['att_blue']` is 1 in agent A only if agent A mastered att\_blue; the same for agent B. No mechanism propagates cognitive-state values between agents.

Category β succeeds if: for every run where agent A's arc\_complete = True and agent B's arc\_complete = False, agent A's mastery\_flag\['att\_blue'\] = 1 and agent B's mastery\_flag\['att\_blue'\] = 0 at the end of ENV2.

### 6.3 Category γ: Developmental individuation under shared environment

The load-bearing finding of the iteration. Two components.

**Component 1: arc\_total\_steps\_delta distribution.** For runs where both agents complete the arc, `arc_total_steps_delta` should be non-trivially positive — the two agents' arc durations should differ. The pre-registered expectation, drawn from the v1.14 arc\_total\_steps distribution (range 1,113 to 851,603 within-cost), is that two agents sharing the same world will show arc\_total\_steps\_delta with standard deviation exceeding 50,000 steps across the both-complete runs. If the shared environment produces identical developmental timelines — if two agents in the same world always take the same amount of time to complete the arc — the individuation thesis is refuted.

**Component 2: first-transformer distribution.** For runs where both agents complete the arc, the `first_transformer` field should be non-degenerate — not always 'a' (which would indicate first-mover advantage dominates) and not always identical (which would indicate simultaneous completion dominates). The pre-registered expectation: both 'a' and 'b' appear as first transformer in at least 3 of the both-complete runs at the 40-run level.

Category γ succeeds if Component 1 shows standard deviation > 50,000 and Component 2 shows a non-degenerate first-transformer distribution.

### 6.4 Category δ: Shared-benefit cases honestly reported

Two pre-anticipated findings are committed to honest reporting.

**haz\_blue\_shared\_benefit cases.** If agent A transforms haz\_blue before agent B has mastered att\_blue, agent B encounters haz\_blue as KNOWLEDGE rather than HAZARD. Agent B incurs no cost; it writes no predicted record; it does not follow the v1.14 arc. This is a designed consequence of the shared world. These cases are reported with `haz_blue_shared_benefit = True` and are excluded from the Category γ Component 1 analysis (they represent a different developmental story, not individuation of the same arc).

**Environmental mutation propagation is immediate.** Because knowledge\_unlocked is shared, `transform_to_knowledge` propagates instantly. There is no delay, no partial propagation, and no agent-specific world state for the shared dict. This is reported as an architectural fact.

### 6.5 Category Φ: Honesty constraint on the individuation claim

The primary claim of v1.15 is that developmental individuation is intrinsic to the cognitive architecture, not a product of environmental variation. If two agents sharing exactly the same environment show different developmental timelines (arc\_total\_steps\_delta > 0), the claim is supported. If they show identical timelines, the claim is challenged.

The two agents do not share seeds. Their different initial Q-table random draws, different action selections in the first steps, and different visit-count accumulations produce different developmental histories even from the same starting position. The claim is not that randomness produces individuation — it is that the cognitive architecture produces individual developmental biographies from randomness, that these biographies are stable and structured (not noise), and that sharing the environment does not collapse them.

The deflationary reading is acknowledged: if `arc_total_steps_delta` is very small on average — if the two agents tend to reach the same milestones at nearly the same steps — the shared world may be doing more developmental work than the individual biography. This outcome would be reported honestly and would motivate an investigation into whether single-agent runs are more individuated than two-agent runs at matched seeds.

### 6.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, γ, and Φ all produce positive findings.

The claim: developmental individuation persists under shared-environment conditions. Two agents with identical architectural endowment, sharing the same prepared environment simultaneously, follow different developmental paths and complete the three-environment causal arc at different times. The developmental biography is not a function of the environment alone; it is co-constituted by the agent's cognitive history and the environment's structure.

The deeper claim, reserved: the conditions under which one agent's developmental arc creates developmental affordances or obstacles for another — the shared-benefit and developmental-interference cases — are the foundation for a social cognition architecture. v1.15 does not build social cognition; it identifies its preconditions.

---

## 7. Connection to the SICC trajectory

v1.15 advances two SICC commitments.

**Commitment 5 (time as first-class)** is tested at the paired level. If arc\_total\_steps\_delta is large, time is individually constituted even in a shared environment. If it is small, the shared environment imposes temporal convergence. The distribution of arc\_total\_steps\_delta is the v1.15 measurement of this commitment.

**Commitment 8 (self-knowledge as derivative of object-knowledge)** receives its first indirect test. When agent A transforms haz\_blue and agent B encounters it as KNOWLEDGE, agent B has received a form of environmental testimony about the world's state — not from agent A directly, but from the world that agent A modified. Whether and how agent B's provenance records reflect this modified world state, and whether the reporting layer can distinguish agent B's KNOWLEDGE event from agent A's, is a question v1.15 generates the data to examine without yet fully answering.

Commitments not yet advanced by v1.15 — direct inter-agent communication (Commitment 10), shared biographical records across agents — remain reserved.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.15 implementation work begins.

**Matched-seed chain.** Seeds drawn from `run_data_v1_14_1.csv` with offset seed\_b = seed\_a + 20,000.

**Pre-flight verifications.** All seven levels pass before the full v1.15 batch runs.

**Single-architectural-change discipline.** v1.15 introduces the shared-world two-agent run as the singular architectural extension. No new cognitive-layer structures are added. No new object types. No inter-agent cognitive-state sharing. The comparison observer from v1.4 is extended to produce paired comparison rows, but its individual-agent logic is inherited unchanged.

**Amendment policy.** Three amendments available. One is provisionally reserved for the pre-transition handling rule for shared-benefit cases (whether objects should be pre-transitioned per-agent or per-pair). Two remain available for unanticipated operational issues.

**Public record.** This pre-registration is committed to github.com/RancidShack/developmental-agent on 8 May 2026, before any v1.15 code is written.

---

## 9. Stopping rule

The v1.15 iteration completes when:

- All seven pre-flight verifications pass.
- The full 40-run batch (80 agent-runs) has completed.
- Categories α, β, γ, δ, Φ, and Ω have been characterised in the v1.15 paper.
- The v1.15 paper is drafted.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve.

---

## 10. References

Baker, N.P.M. (2026a–aa) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.4. Full reference list inherited from v1.4 paper.

Baker, N.P.M. (2026ab) 'v1.13 Pre-Registration: BLUE Family Split-Environment Architecture and Abductive Prediction', GitHub repository, May 2026.

Baker, N.P.M. (2026ac) 'v1.14 Pre-Registration: The Reparative Return and the First Complete Cross-Environment Causal Arc', GitHub repository, 8 May 2026.

Baker, N.P.M. (2026ad) 'The Reparative Return: A Three-Environment Causal Arc in a Small Artificial Learner', preprint, 8 May 2026.

Baker, N.P.M. (2026ae) 'v1.15 Pre-Registration: Developmental Individuation in a Shared Prepared Environment', GitHub repository, 8 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 8 May 2026, before any v1.15 implementation work begins.
