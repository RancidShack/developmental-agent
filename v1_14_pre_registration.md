# v1.14 Pre-Registration: The Reparative Return and the First Complete Cross-Environment Causal Chain

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 8 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.14 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

v1.13.8 confirmed the first cross-environment predictive arc in the programme. The agent encountered `haz_blue` in Environment 1, registered the truncated causal chain, and wrote a predicted schema record: *I believe `att_blue` must exist, because the structural pattern of the YELLOW and GREEN family chains predicts it.* It transferred carrying that open prediction. In Environment 2 it found `att_blue`, mastered it, and the predicted record updated to `confirmed`. 29 of 40 runs completed this arc. Zero hallucinations across 40,486 statements.

What v1.13.8 could not produce — and did not claim to produce — is the completion of the BLUE family arc in Environment 1. `haz_blue` remains an encountered but untransformed hazard. The causal chain for `haz_blue` has four links: surprise at contact (ENV1), truncated precondition link (ENV1), prediction written (ENV1), confirmation of `att_blue` (ENV2). It is missing two: the agent's return to ENV1 carrying the confirmed prediction, and the transformation of `haz_blue` to KNOWLEDGE. The arc that v1.13 opened is not closed. The room was left before the work was finished.

v1.14 closes it.

The return-to-environment architecture introduces a third phase: after ENV2 confirmation of `att_blue`, the agent re-enters ENV1 with `mastery_flag['att_blue'] = 1` carried forward. In the return ENV1, `haz_blue` is no longer unreachable — the precondition has been mastered. The agent goes directly to `haz_blue`. On first approach, the family precondition gate fires and `haz_blue` transforms to KNOWLEDGE. The causal chain acquires its fifth and sixth links: `LINK_RETURN` and `LINK_TRANSFORMATION`. `arc_complete` fires.

This is the Winnicottian capacity for concern made operationally complete. The agent returned to finish what it started, with the knowledge it needed that was absent when it left. The biographical register now spans three environment visits, a prediction, a transfer, a confirmation, a return, and a transformation. The cross-environment causal narrative — *I was surprised at haz_blue at step N. I predicted att_blue must exist. I transferred to Environment 2. At step M I found att_blue and confirmed my prediction. I returned to Environment 1. At step P I completed the BLUE family arc* — becomes substrate-auditable for the first time.

The v1.13 pre-registration committed the `arc_complete` concept at that iteration: *"The concept is introduced here; the record is operationalised at v1.14."* This pre-registration operationalises it.

---

## 2. What v1.14 changes

### 2.1 The arc_complete vs environment_complete distinction, operationalised

`environment_complete` records that a single environment's end-state has been banked. It is a per-environment record, scoped to one visit. It fired in zero runs at v1.13 (the step-fraction phase machinery issue, carried forward as a known limitation).

`arc_complete` is a new record type introduced at v1.14. It is scoped to the full developmental arc and fires when three conditions are simultaneously satisfied:

1. All predicted schema records are in a terminal state (`confirmed` or `unresolvable`). No open or pending records remain.
2. `haz_blue` has transformed to KNOWLEDGE in the return ENV1 visit (BLUE family arc closed).
3. The cross-environment causal chain for `haz_blue` has all six links present.

`arc_complete` is explicitly distinct from `environment_complete` in the output schema, in the record type field, and in the analytical framing. An agent that confirmed `att_blue` in ENV2 and banked ENV2's end-state has achieved `environment_complete` for ENV2; it has not achieved `arc_complete`. The distinction is not terminological: it is the architectural expression of the difference between a room being finished and an open question being answered.

### 2.2 Return-to-environment architecture

After `att_blue` is confirmed in ENV2 — `predicted_record_state = confirmed` AND `att_blue_mastery_step` set — a new transfer gate fires: `return_to_env1_condition_met`. This gate is distinct from the ENV1→ENV2 transfer gate. It does not require ENV2 end-state banking (which the step-fraction issue prevents). It requires only that the prediction the agent carried from ENV1 is now resolved.

The return ENV1 is a fresh environment visit, architecturally a third environment phase. It is constructed using `V113World` with the full BLUE family present: both `haz_blue` and `att_blue` in the return ENV1 world. `haz_blue` is **not** declared as an unreachable hazard in the return ENV1. The precondition has been mastered; the gate that made it unreachable no longer applies.

The `family_precondition_attractor` for `haz_blue` in the return ENV1 is `att_blue`. Since `agent.mastery_flag['att_blue'] = 1` is carried forward via the `carry_agent` block, the precondition gate fires on first approach. `haz_blue` transforms to KNOWLEDGE immediately.

`haz_blue` is injected at position 0 in the return ENV1 Phase 1 waypoint queue. The agent goes directly to the completion target. The return ENV1 is architecturally directed: the agent is not re-exploring ENV1, it is returning to a specific unfinished item with the knowledge it did not have on the first visit.

### 2.3 Return ENV1 world construction

The return ENV1 world differs from the original ENV1 world in exactly one respect: `haz_blue` is no longer in `unreachable_hazard_ids`. All other family objects, positions, and structural parameters are identical to the original ENV1 construction. The YELLOW family (`att_yellow`, `haz_yellow`), GREEN family (`att_green`, `haz_green`), and unaffiliated hazards (`haz_unaff_0/1/2`) are present at their original positions. They do not require re-completion: their KNOWLEDGE status is carried forward in the agent's `knowledge_banked` state.

This construction is the minimal return that satisfies the developmental requirement: the agent needs to be in a world where `haz_blue` is completable and it can reach it. Nothing else needs to change.

### 2.4 The carry_agent block for return ENV1

The `carry_agent` block for the return ENV1 inherits from the v1.13.8 carry_agent block (full dict replacement for `mastery_flag` and `knowledge_banked`) with the following modifications:

**Preserve across ENV2:**
- `mastery_flag['att_blue'] = 1` — do NOT reset. This is the precondition for BLUE family completion in the return ENV1. Resetting it would negate the developmental arc.
- `knowledge_banked` entries for `haz_yellow`, `haz_green`, `haz_unaff_0`, `haz_unaff_1`, `haz_unaff_2` — these were banked in the original ENV1 visit and remain valid.
- Q-table — the agent's accumulated preference gradient. The return ENV1 benefits from the agent's full developmental history in navigation.

**Reset for return ENV1:**
- `mastery_flag` entries for ENV1 attractor cells (`att_yellow`, `att_green`, `att_free_0`, `att_free_1`, `att_free_2`, `att_free_3`) — these cells are at their original ENV1 positions in the return ENV1; the ENV2 mastery entries are not applicable.
- `knowledge_banked` entries for any hazards specific to ENV2 that are not present in the return ENV1.

The critical invariant: `mastery_flag['att_blue'] = 1` survives the carry_agent block unchanged. The chain of custody from ENV2 confirmation to return ENV1 precondition satisfaction is the architectural expression of the reparative return.

### 2.5 Cross-environment causal chain extension

The v1.11 causal observer chain for `haz_blue` at v1.13 has four links:
- `LINK_SURPRISE` — first contact with `haz_blue` in ENV1
- `LINK_PRECONDITION` — truncated: `att_blue` absent from ENV1 schema
- `LINK_PREDICTION` — predicted schema record written (prediction_step populated)
- `LINK_CONFIRMATION` — `att_blue` mastered in ENV2 (confirmation_step, confirming_env populated)

v1.14 adds two further links:

**`LINK_RETURN`:** Records the return-to-ENV1 event. Fields: `return_step` (the step at which the return ENV1 visit begins), `confirming_env` (ENV2 — the environment in which the prediction was confirmed before return). This link is the architectural record that the agent did not complete the arc in ENV2 and did not abandon it: it returned.

**`LINK_TRANSFORMATION`:** Records `haz_blue`'s KNOWLEDGE transformation in the return ENV1. Fields: `transformation_step` (step at which `haz_blue` → KNOWLEDGE fires), `transformation_env` (return ENV1). This link is the completion of the BLUE family arc: the hazard that generated the original surprise is now resolved.

The complete six-link chain is recorded as a single cross-environment record keyed by `haz_blue`. The chain is honest about its own temporal structure: the six links span original ENV1, ENV2, and return ENV1. The record states explicitly which environment each link was resolved in. No link is marked as resolved without a substrate anchor in provenance.

Chain depth at completion: 6. This matches the depth of the complete YELLOW and GREEN family chains at v1.12. The BLUE family chain reaches full depth for the first time, and does so across two environments and a return.

### 2.6 arc_complete record fields

The `arc_complete` record is produced at run end for runs in which all three firing conditions are met. Fields:

| Field | Value |
|---|---|
| `object_id` | `haz_blue` |
| `arc_complete` | `True` |
| `env1_surprise_step` | Step of original `haz_blue` contact in ENV1 |
| `prediction_step` | Step at which predicted record was written in ENV1 |
| `transfer_step` | Step at which ENV1→ENV2 transfer gate fired |
| `confirmation_step` | Step at which `att_blue` mastered in ENV2 |
| `confirming_env` | `2` |
| `return_step` | Step at which return ENV1 visit began |
| `transformation_step` | Step at which `haz_blue` → KNOWLEDGE in return ENV1 |
| `arc_total_steps` | `transformation_step − env1_surprise_step` |
| `arc_env_span` | `3` (ENV1, ENV2, return ENV1) |
| `causal_chain_depth` | `6` |
| `causal_chain_complete` | `True` |

Runs where `arc_complete` does not fire (unresolvable predictions, budget exhaustion) hold `arc_complete = False` and `arc_timeout = True` where the return ENV1 budget was exhausted without transformation.

### 2.7 arc_timeout condition

If `arc_complete` does not fire within the return ENV1 budget of 50,000 steps, the run is recorded as `arc_timeout`. The biographical register holds the full arc to the point of timeout: prediction written, transfer, confirmation, return, budget exhausted before transformation. This is an honest finding: the return was attempted; the work was not completed within the available window.

The 50,000-step return ENV1 budget is set tight by design. The agent has a directed waypoint (`haz_blue` at position 0) and a satisfied precondition (mastery_flag['att_blue'] = 1). If arc_complete does not fire within 50,000 steps in the majority of return ENV1 runs, this is a finding about the waypoint injection mechanism or the carry_agent navigation transfer — and constitutes a pre-registered analytical result, not an amendment trigger.

### 2.8 Eligible run set

The return-to-environment mechanism fires only in runs where:
- `predicted_record_state = confirmed` at the end of ENV2

From v1.13.8: 29 of 40 runs are eligible. The 3 runs with `unresolvable` predictions and the 7 runs with no predicted record written (`GREEN` chain absent at `haz_blue` contact) are not eligible. The 1 run with `predicted` state (partially consumed budget) is carried forward as a pre-registered edge case: if the batch runner encounters this run with `predicted_record_state = predicted` at ENV2 end, it records the run as ineligible for return and populates `arc_complete = False`, `ineligible_reason = 'prediction_unresolved'`.

This pre-registered eligible run set means that the v1.14 pre-registered arc_complete count has an upper bound of 29. The empirical question is how many of those 29 eligible runs achieve arc_complete within the return ENV1 budget.

### 2.9 What v1.14 does not change

All v1.13.8 architecture is inherited unchanged. The agent (`V110Agent`), world (`V113World` with the return-ENV1 modification specified in Section 2.3), all seven observers, the ENV1→ENV2 transfer gate, the predicted schema mechanism, and all output CSVs from v1.13 carry forward. The step-fraction phase machinery issue (ENV2 Phase 1 not completing, ENV2 end-state not banking) is carried forward as a known limitation. It does not affect v1.14's primary mechanism: the return gate fires on `confirmed` prediction, not on ENV2 end-state banking.

The `--no-return` flag provides a regression baseline: with `--no-return`, output is byte-identical to v1.13.8 at matched seeds. This is the v1.14 Level-15 pre-flight regression test.

---

## 3. Experimental design

**Batch scale.** 40 runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition. Seeds from `run_data_v1_13_8.csv` at matched (cost, run_idx) cells. Same seeds as v1.13.8: the comparison is direct.

**Eligible run set.** 29 runs enter the return ENV1 phase (confirmed predictions from v1.13.8). 11 runs do not (7 no predicted record, 3 unresolvable, 1 predicted-open). The 11 ineligible runs produce v1.13.8-equivalent output and serve as regression data.

**Budgets.** ENV1: 1,000,000 steps with early exit on transfer condition met. ENV2: 800,000 steps with early exit on `att_blue` confirmed. Return ENV1: 50,000 steps with early exit on `arc_complete`.

**Output files.** All v1.13.8 output CSVs tagged `v1_14`, plus:
- `arc_complete_v1_14.csv` — one row per run: `run_idx`, `seed`, `hazard_cost`, `arc_complete`, `arc_timeout`, `ineligible_reason`, `env1_surprise_step`, `prediction_step`, `transfer_step`, `confirmation_step`, `return_step`, `transformation_step`, `arc_total_steps`, `arc_env_span`, `causal_chain_depth`, `causal_chain_complete`
- `return_env1_v1_14.csv` — one row per return ENV1 run: `run_idx`, `seed`, `hazard_cost`, `return_env1_steps`, `haz_blue_approach_step_in_return`, `transformation_step`, `arc_complete`, `return_env1_yellow_pre_transition_entries`, `return_env1_green_pre_transition_entries`

**Pre-flight.** `verify_v1_14_level15.py`:
- All Level-14 criteria inherited
- Additional Level-15 criteria:
  - `return_to_env1_condition_met` fires correctly for confirmed-prediction runs and does not fire for unresolvable/ineligible runs
  - `mastery_flag['att_blue'] = 1` is preserved through the carry_agent block into return ENV1
  - `haz_blue` waypoint fires at position 0 in return ENV1 Phase 1 queue
  - `haz_blue` transformation occurs on first approach in return ENV1 for a confirmed-prediction run
  - `arc_complete` record is produced with all six causal chain links populated
  - `arc_complete = False` is produced for an unresolvable-prediction run (gate correctly blocked)
  - `--no-return` flag produces byte-identical output to v1.13.8 at matched seeds

Pre-flight: 10 runs (5 at cost=1.0, 5 at cost=10.0), drawn from confirmed-prediction seeds only. Full batch proceeds only after all Level-15 criteria pass.

---

## 4. Pre-registered interpretation categories

All v1.13.8 categories inherited. Two updated, two new.

### 4.1 Category α: Internal consistency — extended honesty constraint

Inherited from v1.13. Zero hallucinations across all Q-type outputs. Extended at v1.14 to cover arc_complete records:

- **`arc_complete` is gated on confirmed prediction only.** An `arc_complete` record for a run where `predicted_record_state ≠ confirmed` is a Category α failure. Unresolvable and no-prediction runs must hold `arc_complete = False`.
- **`LINK_TRANSFORMATION` requires a substrate-anchored transformation event.** A chain reported as six-link-complete without a `haz_blue → KNOWLEDGE` transformation event in provenance is a Category α failure.
- **`LINK_RETURN` requires a documented return ENV1 visit.** A chain with `LINK_RETURN` populated but no return ENV1 run recorded is a Category α failure.
- **`arc_complete ≠ environment_complete` in all records.** The two record types are distinct. Any run that conflates them — reporting `arc_complete = True` because ENV2 end-state was banked, or `environment_complete = True` because arc_complete fired — is a Category α failure.

The chain that claims closure before the transformation is in is the most architecturally specific hallucination v1.14 considers. The honesty constraint is correspondingly precise.

### 4.2 Category θ: Completion signal — arc_complete rate

New primary completion metric. Pre-registered upper bound: 29 eligible runs (confirmed predictions from v1.13.8). Pre-registered direction: the majority of eligible runs achieve arc_complete within the 50,000-step return ENV1 budget. The directed waypoint and satisfied precondition make this the most constrained developmental task in the programme to date.

If the arc_complete rate among eligible runs is substantially below the confirmation rate (29/40 from v1.13.8), this is a finding about the return ENV1 architecture — the waypoint injection or carry_agent navigation transfer is not performing as specified — and constitutes a pre-registered analytical result triggering diagnostic inspection rather than an amendment.

### 4.3 Category Λ: Developmental transfer — return ENV1 schema signal

Updated. Components 1–4 inherited from v1.13.

**Component 5 (new):** Schema transfer signal in return ENV1. Pre-registered expectation: `yellow_pre_transition_entries` and `green_pre_transition_entries` in the return ENV1 are near-zero. The agent's Q-table carries the full YELLOW and GREEN resolution history from the original ENV1 visit. The schema should not re-surprise itself. If resolution windows reappear in the return ENV1 for YELLOW and GREEN objects, this is an artefact of the carry_agent block failing to preserve the relevant Q-table state — a diagnostic finding.

### 4.4 Category π: Predictive schema integrity — arc closure component

Extended from v1.13. Component 4 (new):

**Component 4: arc_complete causal chain integrity.** In arc_complete runs, the causal chain for `haz_blue` has exactly six links: `LINK_SURPRISE`, `LINK_PRECONDITION`, `LINK_PREDICTION`, `LINK_CONFIRMATION`, `LINK_RETURN`, `LINK_TRANSFORMATION`. Each link has a substrate anchor in provenance. The chain is honest about which environment each link was resolved in. No link is reported as resolved without a corresponding provenance event.

Category π Component 4 succeeds if: (a) all arc_complete runs have six-link chains, (b) no non-arc_complete run has a six-link chain, (c) the environmental attribution of each link is correct across all arc_complete runs.

### 4.5 Category Ω (new): The cross-environment causal narrative

The first pre-registered claim of a complete cross-environment causal narrative. The claim has three components:

**Component 1: Substrate-auditable arc.** The full six-event sequence — surprise, prediction, transfer, confirmation, return, transformation — is recorded with provenance-anchored step numbers in the `arc_complete` record. The narrative is reconstructible from the substrate alone without any inferential gap.

**Component 2: Temporal coherence.** `env1_surprise_step < prediction_step < transfer_step < confirmation_step < return_step < transformation_step` in all arc_complete runs. The temporal ordering of the arc is monotonically increasing across all six links. Any violation is a Category α failure.

**Component 3: Individuation range.** `arc_total_steps` varies across arc_complete runs in ways reflecting biographical individuation: agents that predicted early (short time to prediction_step) do not necessarily confirm or transform early (long time to confirmation_step or transformation_step). The arc_total_steps distribution reflects the individual developmental history, not a fixed schedule.

Category Ω succeeds if all three components hold across all arc_complete runs.

### 4.6 Category γ: Biographical individuation

Inherited. Extended: `arc_total_steps` is the new individuation signal of greatest developmental scope in the programme — it spans three environment visits and up to hundreds of thousands of steps. Between-run variance in `arc_total_steps` is the primary individuation measure at v1.14.

---

## 5. Pre-registered predictions

1. **arc_complete fires for the majority of eligible runs.** In runs where `predicted_record_state = confirmed` at v1.13.8 (n=29), `arc_complete = True` is the expected outcome in the majority within the 50,000-step return ENV1 budget.

2. **haz_blue transformation occurs on first approach in return ENV1.** `mastery_flag['att_blue'] = 1` is satisfied before return ENV1 entry; the precondition gate fires at first contact. `haz_blue_approach_step_in_return` and `transformation_step` are equal (or within one step) in all arc_complete runs.

3. **Temporal ordering is monotonically increasing in all arc_complete runs.** `env1_surprise_step < prediction_step < transfer_step < confirmation_step < return_step < transformation_step` without exception.

4. **Causal chain depth is exactly 6 in all arc_complete runs.** No arc_complete run has fewer than six links. No non-arc_complete run has six links.

5. **arc_complete does not fire for unresolvable-prediction runs.** The three v1.13.8 unresolvable runs hold `arc_complete = False` and `ineligible_reason = 'prediction_unresolvable'` without exception.

6. **Return ENV1 yellow and green pre-transition entries are near-zero.** The Q-table carries the full resolution history. The schema transfer signal holds for the return ENV1 as it held for the original ENV2.

7. **Zero hallucinations across all Q-type outputs and arc_complete records.** Category α holds including the extended honesty constraint.

8. **arc_total_steps varies substantially across arc_complete runs.** Between-run variance in the full developmental arc length reflects genuine biographical individuation.

9. **`--no-return` flag produces byte-identical output to v1.13.8 at matched seeds.** Level-15 regression test passes.

---

## 6. SICC commitments being operationalised

**Commitment 5 (time as first-class).** At its fullest expression to date. The `arc_complete` record holds the full temporal sequence of a developmental arc that spans three environment visits. The six fields — `env1_surprise_step`, `prediction_step`, `transfer_step`, `confirmation_step`, `return_step`, `transformation_step` — are time-stamped substrate anchors for the agent's first complete developmental arc. Time is not a parameter of the experiment; it is the medium in which the arc unfolds, and its record is the substrate evidence that the arc was earned step by step rather than designed into the outcome.

**Commitment 9 (earned extensibility).** The predicted schema record acquires its final state transition at v1.14: `predicted → confirmed → arc_complete`. The `arc_complete` firing is not a reset or a new beginning; it is the terminal state of the prediction that was written in ENV1 from the structural evidence of the YELLOW and GREEN families. The chain of inference: two confirmed family chains → structural rule → abductive prediction → directed search → confirmation → return → transformation → arc_complete. Each link in the epistemic chain earned by the developmental work preceding it.

**Environment completion versus arc completion (operationalised).** Introduced as a commitment in the v1.13 pre-registration: *"The concept is introduced here; the record is operationalised at v1.14."* The `arc_complete` record is that operationalisation. The distinction is not terminological. An agent that confirmed `att_blue` in ENV2 has environmentally completed ENV2; it has not arc-completed the BLUE family. The return and transformation are required. This is the architectural expression of the difference between finishing a room and answering an open question.

**The Winnicottian capacity for concern (substrate-auditable).** The developmental psychology framing is precise here and should be held explicitly. Winnicott's capacity for concern — the mature object relation in which the subject acknowledges responsibility for damage done, feels concern for the object, and is moved to make reparation — has a substrate expression in the return-to-environment architecture. The agent approached `haz_blue`, paid a cost, and left an open chain. It transferred carrying that open chain. It confirmed the precondition in ENV2. And it returned to ENV1 to complete the transformation. That return is not coincidental and not scripted: it is the gate condition that connects confirmation to completion. The reparative return is the developmental event. The `arc_complete` record is its substrate evidence.

---

## 7. Open questions resolved at pre-registration

**1. Return ENV1 trigger condition.** `predicted_record_state = confirmed` AND `att_blue_mastery_step` set. Does not require ENV2 end-state banking. The step-fraction limitation is carried forward but does not block v1.14's primary mechanism.

**2. Return ENV1 world construction.** `V113World` with `haz_blue` excluded from `unreachable_hazard_ids`. All other parameters identical to original ENV1. This is the minimal change that makes the return developmental rather than merely sequential.

**3. carry_agent invariant.** `mastery_flag['att_blue'] = 1` is the protected field. The carry_agent block must preserve it through ENV2 and into return ENV1 unchanged. This invariant is a Level-15 pre-flight criterion and is verified before the full batch runs.

**4. Return ENV1 waypoint.** `haz_blue` at position 0 in the return ENV1 Phase 1 waypoint queue. The agent's first directed target in the return visit is the completion target. This is architecturally intentional: the return is not open-ended exploration; it is a directed completion of a specific unfinished item.

**5. Budget.** Return ENV1: 50,000 steps. Tight by design. The satisfied precondition and directed waypoint make this the most constrained developmental task in the programme. If the majority of eligible runs cannot arc_complete within 50,000 steps, the diagnostic is in the navigation transfer (Q-table carry) or the waypoint mechanism, not in the budget being insufficient by principle.

**6. arc_complete eligibility.** Exactly the 29 confirmed-prediction runs from v1.13.8 are eligible. This is a pre-registered constraint, not a finding to be revised mid-batch. The 11 ineligible runs produce v1.13.8-equivalent data and serve as regression baselines.

**7. LINK_TRANSFORMATION anchoring.** `haz_blue → KNOWLEDGE` transformation event in the provenance substrate is the required anchor for `LINK_TRANSFORMATION`. If the transformation event does not appear in provenance for a run reporting arc_complete, that run is a Category α failure. The transformation must be a real substrate event, not an inferred one.

**8. Amendment budget.** Three of three available. Most likely candidates: (1) carry_agent block — if `mastery_flag['att_blue'] = 1` fails to survive the block in edge cases, a targeted fix covers the specific reset logic. (2) return ENV1 world construction — if `V113World` requires a parameter not anticipated in the current specification to correctly exclude `haz_blue` from `unreachable_hazard_ids` while including it in `hazard_cells` and `knowledge_unlocked`, one amendment covers the adjustment. (3) return-gate timing — if `return_to_env1_condition_met` requires a different polling mechanism than anticipated from the v1.13.8 batch runner structure.

---

## 8. Amendment budget strategy

Three amendments available, none provisionally reserved. The architecture is more precisely specified at this pre-registration than at any prior iteration: the return mechanism, the carry_agent invariant, the world construction, and the arc_complete record fields are all specified to implementation level in the carry-forward note. Amendment candidates are the edge cases — the unexpected interactions between the new transfer gate and the existing batch runner state management — rather than the primary mechanism. The diagnostic-first protocol applies: inspect the carry_agent block output and Level-15 pre-flight failures before writing any new code.

---

## 9. Stopping rule

v1.14 completes when:
- `verify_v1_14_level15.py` passes at all Level-15 criteria.
- Full 40-run batch has run.
- Categories α, θ, Λ (Components 1–5), π (Components 1–4), Ω, and γ have been characterised.
- `arc_complete_v1_14.csv` and `return_env1_v1_14.csv` produced and verified.
- The v1.14 paper is drafted.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve.

---

## 10. New files required

- `curiosity_agent_v1_14_batch.py` — batch runner: return_to_env1_condition_met gate, return ENV1 world construction, carry_agent block with mastery_flag['att_blue'] preservation, haz_blue waypoint at position 0 in return ENV1, arc_complete record construction, arc_timeout handling, --no-return flag
- `v1_14_causal_extension.py` — LINK_RETURN and LINK_TRANSFORMATION additions to V111CausalObserver chain; arc_complete record writer
- `verify_v1_14_level15.py` — pre-flight verifier: Level-14 inherited + Level-15 new criteria
- `v1_14_carry_forward.md` — session carry-forward note

`v1_13_world.py` is used without modification for the return ENV1 construction (the `unreachable_hazards` parameter is passed as empty for the return ENV1 instantiation). No new world file required.

---

## 11. References

Baker, N.P.M. (2026au) 'v1.11 Pre-Registration: Causal Self-Explanation and the Next-Environment Architecture', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026av) 'v1.11.1 Post-Batch Amendment: Phase1 Absence Link and Env2 Yellow Field', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aw) 'Causal Self-Explanation in a Small Artificial Learner: The Record of Understanding Why', preprint, 4 May 2026.

Baker, N.P.M. (2026ax) 'v1.12 Pre-Registration: Multi-Environment Developmental Transfer', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ay) 'Multi-Environment Developmental Transfer in a Small Artificial Learner: Complete Transfer Confirmed', preprint, 4 May 2026.

Baker, N.P.M. (2026az) 'v1.13 Pre-Registration: Abductive Inference and the Predictive Schema Record', GitHub repository, 5 May 2026.

Baker, N.P.M. (2026ba) 'Abductive Inference and Cross-Environment Prediction in a Small Artificial Learner', preprint, 8 May 2026.

Baker, N.P.M. (internal record, v0.10 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Baker, N.P.M. (internal record, May 2026) 'Developmental Version Map: V1 completion → V2 play-pen → V3 Cozmo → V4 autonomous → V5+'.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Peirce, C.S. (1934) 'Abduction and Induction', in Hartshorne, C. and Weiss, P. (eds) *Collected Papers of Charles Sanders Peirce*, Vol. 5. Cambridge, MA: Harvard University Press.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena'. *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Winnicott, D.W. (1965) *The Maturational Processes and the Facilitating Environment*. London: Hogarth Press.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 8 May 2026, before any v1.14 implementation work begins.
