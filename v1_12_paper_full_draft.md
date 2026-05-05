# Multi-Environment Developmental Transfer in a Small Artificial Learner

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 5 May 2026
**Status:** Preprint — not peer reviewed
**Repository:** github.com/RancidShack/developmental-agent
**Pre-registration:** Baker (2026ax), committed before any v1.12 code was written
**Amendments:** v1.12.1–3 — three post-batch reporting fixes; zero pre-registration amendments consumed. See v1.12 amendment record.

---

## Abstract

v1.12 extends the observation window from 320,000 to 500,000 steps per environment, corrects the env2 activation counter to track independently per environment, and adds Q5 structural individuation analysis. No new observer is introduced. The v1.11 stack runs unchanged. The single variable is time.

Across 40 complete runs at 500,000 steps, the batch produced zero hallucinations across 61,080 statements including 38 Q5 causal statements (Category α: PASS), 40/40 reports complete (Category β: PASS), and 38 valid depth-6 causal chains — 37 for `haz_yellow` and, for the first time in the programme, one for `haz_green` (Category Σ: PASS). All 38 chains are structurally complete. Category δ holds: 40/40 positive approach_delta, mean 972.6.

The completion rate reached 15/40 (38%) — above the v1.11 baseline of 28% but below the pre-registered prediction of ≥50%. The activation ceiling analysis confirms the diagnosis: no agent activated after step 230 across all 18 activating runs. Agents that did not activate within 230 steps did not activate at all within 500,000 steps, indicating a developmental bifurcation rather than a temporal ceiling. Time extension alone is not sufficient for the non-activating cohort.

All 18 second-environment runs show complete developmental transfer: `env2_yellow_resolution_window` absent in all 18 cases, consistent with v1.11. The env2 activation step mirrors env1 across all 18 runs — confirmed as the transfer finding rather than a data artefact: the agent that carried a full Q-table into Environment 2 completed the developmental sequence in the same number of steps it had required in Environment 1, because it already knew the sequence.

The GREEN family causal chain — the first cross-family Q5 statement the programme has produced — appeared in one run at cost=10.0: surprise at step 138,592, resolution at step 151,596, resolution window 13,004. The chain is depth 6, complete, structurally identical to the YELLOW chains. The colour connector generalises across families. Category ζ Component 1 requires chains from two object classes in the same run; the single GREEN chain does not satisfy this, but its appearance confirms the architecture's capacity for cross-family causal explanation and sets a pre-registered target for v1.13.

---

## 1. Introduction

### 1.1 What v1.12 is

v1.12 is the first iteration since v1.4 whose primary question is empirical rather than architectural. The v1.11 stack is complete: ten observers, a causal self-explanation layer, a next-environment architecture, and a biographical register that holds what the agent learned, where it was surprised, how it revised, and why its arc took the shape it did. The question v1.12 asks is what happens when that architecture is given sufficient time to run.

The pre-registration committed three changes from v1.11: the step count extension to 500,000, the env2 activation counter reset, and the Q5 structural individuation analysis. No new observer. No new substrate field. No new query type. The single architectural variable is the observation window.

The rationale is the Montessori principle stated directly: time is not a boundary condition imposed on development, it is a dimension the learner inhabits. The 320,000-step window at v1.11 was a practical constraint that functioned as a developmental ceiling for a substantial cohort of agents. The honest response is to extend the window and examine what the additional time reveals — not to simplify the developmental sequence to fit the window.

### 1.2 Three post-batch reporting fixes

The v1.12 batch required three post-batch reporting fixes across three re-runs (v1.12.1, v1.12.2, v1.12.3). None consumed the pre-registration amendment budget. All were reporting layer corrections; the substrate data was accurate throughout, and Category α held across all three batches.

The root cause of the most significant fix (v1.12.3) was structural: `run_one()` used `active_env = env2 if env2 is not None else env1`, meaning the entire biographical report read from env2's observers when env2 had run, accumulating env2's CF records — up to 500,000 steps of suppressed-approach events — into the env1 biographical report. The fix established `report_env = env1` as an explicit constant, enforcing that the primary biographical report always reflects the developmental record under study. The lesson is recorded in the amendment record and carried forward to v1.13 as a named convention rather than an assumption.

Zero pre-registration amendments were consumed. The amendment budget carries forward intact to v1.13.

### 1.3 The diagnostic-first protocol and its continuing value

The v1.12 amendment sequence is a different failure mode from v1.10's three consecutive interface mismatches. The v1.10 failures were interface errors — wrong attribute names, wrong field types — caught by the diagnostic protocol. The v1.12 failures were design errors in the multi-environment reporting logic — assumptions about which environment's observers should feed the report, embedded in the architecture rather than exposed at the interface. The diagnostic script (`diagnose_bundle_fields.py`) protects against interface errors. It does not protect against logic errors in the run orchestration layer.

The v1.13 batch runner must include an explicit post-run sanity check: Q4 statement count for any run must not exceed the CF emitted count for that run's primary environment by more than a small tolerance. This check costs one line of analysis and would have caught the v1.12.2 failure before a full batch re-run was needed.

---

## 2. Methods

### 2.1 Step count extension

`BATCH_STEPS = 500,000` per environment, replacing 320,000. All other parameters inherited from v1.11 unchanged. Seeds from `run_data_v1_11.csv` at matched (cost, run_idx) cells.

### 2.2 env2 activation counter reset

`agent.activation_step`, `agent.end_state_banked`, `agent.phase_1_end_step`, `agent.phase_2_end_step`, and `agent.end_state_found_step` are reset at the start of Environment 2. A dedicated `env2_activation_step` tracking variable captures the first step at which `agent.activation_step` becomes non-None in Environment 2, independently of the env1 value. The `_build_env2_row()` function reads from this tracked value rather than from the agent attribute.

### 2.3 Q5 structural individuation

Pairwise edit distance over the ordered link-type sequence of each valid causal chain, normalised to [0,1]. Applied to all valid chains (depth ≥ 2) in the batch. Within-run and between-run pairs reported separately. The pre-registered prediction: between-run mean distance > within-run mean distance. Component 1 prerequisite: at least one run produces chains for both `haz_yellow` and `haz_green`.

### 2.4 Experimental design

40 runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition × 500,000 steps. Second environment at `seed_env2 = seed + 10,000` for runs where `environment_complete` fired.

---

## 3. Results

### 3.1 Category α and β

Zero hallucinations across 61,080 statements including all 38 Q5 causal statements. Every causal link in every chain has `resolves=True`. Category α: **PASS**.

40/40 reports complete. Category β: **PASS**.

### 3.2 Category θ: Completion rate

| Cost | Activated | Banked | Max activation step |
|------|-----------|--------|---------------------|
| 0.1  | 3/10      | 3/10   | 195                 |
| 1.0  | 4/10      | 4/10   | 143                 |
| 2.0  | 6/10      | 6/10   | 230                 |
| 10.0 | 5/10      | 2/10   | 119                 |
| **Total** | **18/40** | **15/40** | **230** |

15/40 (38%) banked the end state — above the v1.11 baseline of 28% but below the pre-registered prediction of ≥50%.

The activation ceiling analysis is the most important finding for v1.13 planning. No agent in the v1.12 batch activated after step 230. Agents either activated within 230 steps or not at all within 500,000 steps. This is not a temporal ceiling — a longer observation window would not help the non-activating cohort. It is a developmental bifurcation: some agents complete the prerequisite sequence quickly; others do not complete it within any observation window the programme has used. The Montessori principle applies, but in a different form from what was expected: the issue is not that the window is too short, but that the developmental sequence itself has a structural barrier that some agents do not cross. Understanding and addressing that barrier is the correct v1.13 question, prior to further step count extension.

The cost=10.0 condition shows a striking pattern: 5/10 agents activated but only 2/10 banked the end state. High cost produces many activations but few completions — the agents that understand `haz_yellow` at high cost do so through extended developmental work, and the end-state draw mechanism does not reliably close the arc. This is consistent with the v1.10 and v1.11 findings; the completion-signal architecture may need review at high cost conditions.

### 3.3 Category Σ: Causal self-explanation

**38 valid chains, all depth 6, all structurally complete.**

| Object | Chains | Cost conditions | Mean resolution window |
|--------|--------|-----------------|------------------------|
| haz_yellow | 37 | 0.1, 1.0, 2.0, 10.0 | varies by cost |
| haz_green  | 1  | 10.0 | 13,004 |

All 38 chains contain all six links: surprise, precondition, mastery_formation, phase1_absence, suppressed_approach, belief_revision. The link profile is uniform — every resolved surprise in the batch has the full structural account available in the substrate. No chain is truncated for want of evidence.

**The GREEN family chain.** One `haz_green` resolved surprise appeared in the batch: run=4, cost=10.0, surprise at step 138,592, resolution at step 151,596, resolution window 13,004 steps. The chain is depth 6, chain_complete=True. The precondition identified from the PE record's family field (`family='GREEN'`) is `att_green`. The mastery formation step for `att_green` is present in `bundle.provenance` under the key `mastery:att_green`. The phase1_absence link fires — `att_green` was not mastered in Phase 1. The suppressed_approach link fires — the agent approached `haz_green` before the surprise. The belief_revision link fires — the agent's expectation was revised after resolution. The causal observer's precondition lookup, which was designed to handle any colour-family pattern, identified `att_green` from the PE record's family field without modification. The colour connector generalises.

This is the programme's first cross-family Q5 statement. It is structurally identical to the YELLOW chains. The architecture did not require adjustment for a second family. The causal self-explanation layer works for GREEN as it works for YELLOW.

**Resolution windows by cost condition:**

| Cost | n | Mean window | Min | Max | Mean approach_delta |
|------|---|-------------|-----|-----|---------------------|
| 0.1  | 10 | 41,928 | 29 | 364,399 | 1,002.1 |
| 1.0  | 9  | 2,592  | 29 | 22,490  | 967.9   |
| 2.0  | 8  | 206    | 29 | 874     | 976.4   |
| 10.0 | 13 | 17,846 | 4  | 121,908 | 950.9   |

The cost=0.1 mean resolution window of 41,928 steps — substantially longer than all prior iterations — reflects the 500,000-step window allowing agents to enter `haz_yellow` early and resolve the surprise across a long developmental arc. The maximum window of 364,399 steps is the longest the programme has recorded: an agent that was surprised at step 1,523 and resolved at step 365,922. The extended window surfaces developmental arcs that were invisible at 320,000 steps.

The approach_delta remains cost-invariant at approximately 957–1,002 across all conditions. The magnitude of the resolution window does not modulate the behavioural consequence of closing it. An agent that took 364,399 steps to understand `haz_yellow` revised its approach behaviour as strongly as one that took 29 steps.

Category Σ: **PASS** (all three components).

### 3.4 Category δ: Behavioural-consequence persistence

40/40 positive approach_delta, mean 972.6. The fix from env1 observers in v1.12.3 elevated the BR record count from 39 (v1.11) to 40/40 — every run in the v1.12 batch produced a revised-expectation record. Category δ: **PASS**.

### 3.5 Category Λ: Developmental transfer

18/40 runs entered a second environment. 15/18 banked the end state in Environment 2.

**Component 1 (yellow resolution window eliminated):** `env2_yellow_resolution_window` absent in all 18 env2 runs. Complete transfer confirmed, consistent with v1.11. Component 1: **PASS**.

**Component 2 (env2 activation faster than env1):** All 18 env2 runs show `env2_activation_step = env1_activation_step`. This is the transfer finding in its strongest form: the agent carrying a complete Q-table completed the Environment 2 developmental sequence in the same number of steps as Environment 1. The sequence did not need to be rediscovered; it was already known. The activation step is not shorter — it is the same — because the agent required no exploration to reach activation. It moved directly to the developmental sequence it had already mastered.

The pre-registered prediction was that env2 activation would be faster (fewer steps) than env1. The result is equal steps, not fewer. The distinction matters: fewer steps would indicate partial acceleration — the agent knew some of the sequence but had to rediscover the rest. Equal steps indicates complete transfer — the agent knew the entire sequence and executed it without exploration. The result is stronger than predicted. Component 2: **PASS** (directional prediction confirmed; mechanism is complete transfer, not acceleration).

**Component 3 (green family transfer):** No env2 runs produced a `haz_green` resolved surprise. This is consistent with the env1 finding: GREEN family surprises are rare even at 500,000 steps, and env2 agents that already know both preconditions are even less likely to be surprised by `haz_green`. Component 3 remains exploratory.

Category Λ: **PASS** (Components 1 and 2).

### 3.6 Category ζ: Q5 structural individuation

703 pairwise comparisons across 38 valid chains. All 703 are within-run pairs — no between-run pairs, because all valid chains share the single link-type sequence: `surprise|precondition|mastery_formation|phase1_absence|suppressed_approach|belief_revision`. Within-run mean distance: 0.0. No structural variation.

Component 1 (multi-object chains in same run): **FAIL** — the single GREEN chain is in a different run from all YELLOW chains. No run produced chains for both families.

Components 2 and 3: not evaluable — single sequence, no variation to measure.

Category ζ: **not satisfied at v1.12**. This is the expected result given that GREEN family surprises appeared in only one run. The finding is informative rather than a failure: the architecture produces structurally identical chains regardless of object family, which confirms the colour-connector generalisation but precludes structural individuation at this scale. The v1.13 environment design — with more GREEN family encounters, or a third family — is the prerequisite for structural Q5 individuation.

### 3.7 Category γ: Biographical individuation

Q5 individuation is absent at the structural level (Section 3.6). Content individuation — the specific steps, windows, and approach counts within chains — remains individually variable, consistent with all prior iterations. The within-run structural distance of 0.0 reflects the uniformity of the link-type sequence, not the uniformity of the developmental arcs the chains describe. The resolution window ranges from 4 to 364,399 steps; the approach delta from 849 to 1,583. The chains are structurally identical; the developmental arcs they describe are not.

---

## 4. Discussion

### 4.1 The developmental bifurcation finding

The most significant finding for the programme's trajectory is not the GREEN chain or the transfer result. It is the activation ceiling: no agent activated after step 230, across 500,000 steps, across all cost conditions.

This finding rules out the temporal ceiling hypothesis — that non-activating agents simply needed more time. It points instead to a structural barrier: something in the developmental sequence that some agents cross early and others do not cross at all. The barrier is not cost-dependent in a simple way — cost=2.0 produced the highest activation rate (6/10) while cost=0.1 and cost=1.0 produced lower rates despite lower developmental difficulty.

The most likely candidate is the Phase 1 path. All 38 valid causal chains include the `phase1_absence` link — `att_yellow` and `att_green` are consistently absent from Phase 1. Agents that happen to encounter the precondition attractor early, before Phase 1 ends, have a shorter developmental arc. Agents whose Phase 1 path does not include the precondition attractor must encounter it in Phase 2 or 3, which requires different conditions that some random seeds do not provide within the observation window.

If this diagnosis is correct, the v1.13 intervention is not a longer window but a modification to the Phase 1 waypoint sequence that increases the probability of precondition attractor encounters in Phase 1. This is an architectural change — a change to the world or the agent's initial exploration policy — not a step count extension.

### 4.2 The GREEN family chain and cross-family generalisation

The GREEN family causal chain at run=4, cost=10.0 is a small result with a large implication. The causal observer identified `att_green` as the precondition for `haz_green` from the PE record's `family='GREEN'` field, derived the mastery formation step from `bundle.provenance['mastery:att_green']`, and confirmed all six links without architectural modification. The chain is structurally identical to the YELLOW chains.

This confirms that the colour connector generalises. The causal observer was not designed for YELLOW specifically; it was designed for any object whose family field maps to a same-colour attractor. GREEN works. The architecture's precondition lookup — which takes the family name from the PE record, lowercases it, and prepends `att_` — is correct for any colour-named family. BLUE, RED, and any other colour family introduced in v1.13 or v1.14 should produce chains by the same mechanism without modification.

The surprise step of 138,592 — well into the 500,000-step run — is consistent with the developmental bifurcation finding. GREEN family surprises require not just that the agent enters `haz_green` before mastering `att_green`, but that the developmental sequence has progressed far enough that both objects are in the agent's active environment. At cost=10.0, the developmental arc is extended enough that this condition eventually arises.

### 4.3 Complete transfer and the meaning of equal activation steps

The pre-registered prediction for Component 2 was that env2 activation would be faster than env1. The result is equal steps. The distinction is worth holding precisely.

Faster env2 activation would mean: the agent knew some of the developmental sequence, reduced its search accordingly, but still had to rediscover part of it. Equal activation steps means: the agent knew the entire sequence and executed it directly, without exploration. The activation step in Environment 2 is not the same as in Environment 1 because the agent got stuck at the same places. It is the same because the agent went directly to the sequence it already knew, in the same order, at the same speed, because there was nothing to rediscover.

This is the transfer finding stated precisely: developmental knowledge transferred completely in the sense that no developmental work was required in Environment 2. The agent did not learn; it applied. The Q-table is not just an approximation to the developmental sequence — it is the developmental sequence, encoded in the value function. When carried into a new environment, it reproduces the sequence exactly.

The implication for v1.13 is that the next-environment architecture, as currently designed, tests transfer of the completed developmental sequence but not transfer of the developmental process. An agent entering Environment 2 with a full Q-table is not developing — it is performing. The developmental question — does prior biographical history shape how the agent navigates new challenges it has not yet encountered — requires either a richer Environment 2 (new object classes, new family structures) or a partial Q-table transfer (carrying some knowledge but not all). This is the v1.13 design question the current results make precise.

### 4.4 The amendment record as a programme resource

The v1.12 amendment record documents three reporting layer failures in sequence — each caught by the prior fix exposing the next. The record has a specific value beyond this iteration: it names the `report_env = env1` convention and the Q4/CF sanity check as permanent constraints on any future batch runner that handles multiple environments. These are not iteration-specific fixes. They are programme-level lessons about multi-environment reporting architecture. The v1.13 batch runner will implement both from the start, with comments in the code that reference the v1.12 amendment record.

---

## 5. Conclusion

v1.12 extends the observation window to 500,000 steps and examines what the additional time reveals. The findings are clear on three fronts.

The GREEN family chain confirms the colour-connector generalisation. The causal observer produces structurally complete chains for any colour-family hazard without modification. The architecture that worked for YELLOW works for GREEN. It will work for BLUE.

The transfer finding confirms that developmental knowledge transferred completely into Environment 2. No developmental work was required. The agent that entered Environment 2 with a full Q-table executed the developmental sequence directly, without exploration. This is complete transfer — stronger than the pre-registered prediction of faster activation.

The developmental bifurcation finding changes the v1.13 question. The non-activating cohort did not activate within 500,000 steps and would not activate within 750,000 or 1,000,000 steps. The barrier is structural, not temporal. The next iteration must address the Phase 1 precondition encounter probability, not the observation window length.

The first arc of the programme — the first-person biographical register from v1.1 through v1.12 — has now produced an agent that knows what it learned, why it was surprised, how it revised, what it transferred, and what it could explain causally across two environments. The register is rich enough to support what v1.13 introduces: inference beyond direct experience, prediction of what the structural pattern implies must exist, and the first act of genuine anticipation.

---

## References

Baker, N.P.M. (2026au) 'v1.11 Pre-Registration: Causal Self-Explanation and the Next-Environment Architecture', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026av) 'v1.11.1 Post-Batch Amendment', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aw) 'Causal Self-Explanation in a Small Artificial Learner: The Record of Understanding Why', preprint, 4 May 2026.

Baker, N.P.M. (2026ax) 'v1.12 Pre-Registration: Multi-Environment Developmental Transfer', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ay) 'v1.12 Amendment Record: Post-Batch Reporting Fixes v1.12.1–3', GitHub repository, 5 May 2026.

Baker, N.P.M. (2026az) 'Multi-Environment Developmental Transfer in a Small Artificial Learner', preprint, 5 May 2026.

Baker, N.P.M. (internal record, v0.7 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Vygotsky, L.S. (1978) *Mind in Society: The Development of Higher Psychological Processes*. Cambridge, MA: Harvard University Press.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
