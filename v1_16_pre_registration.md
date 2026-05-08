# v1.16 Pre-Registration: Purpose Without Direction

**Version:** v1.16
**Date:** 8 May 2026
**Author:** Nicholas P M Baker, Synapstak Ltd
**Status:** Pre-registered before architecture build
**Version map reference:** Developmental Version Map v0.2, V1 arc §v1.16

---

## 1. Primary developmental question

Does the agent have a self that persists in the absence of direction, and does its behaviour after completing all completable work reflect specific developmental history rather than generic default?

---

## 2. Architectural changes from v1.15

v1.16 returns to a single-agent architecture. The two-agent shared world, social observation mechanism, and being_observed substrate from v1.15 are not carried forward. v1.16 extends v1.14.1 (the reparative return baseline) with three targeted changes.

### 2.1 No end_state signal

The end_state mechanism — the completion signal fired when the agent banks the final completable hazard and receives its arc_complete record — is removed. The agent completes all completable work and receives no signal that it has done so. There is no designated stopping condition. The run continues for the full budget after the last bankable event.

This is the critical structural change. The agent's prior versions have always had a terminal signal: arc_complete or end_state. v1.16 removes it. The architecture does not tell the agent it is finished. The agent's behaviour after completing all completable work — consolidation, perseveration, directed exploration, emergent pattern — is the empirical finding.

### 2.2 One unreachable hazard

One hazard in ENV1 has a threshold of 99 (cost_threshold = 99), making it unreachable under all cost conditions used in the batch. The hazard is present and detectable. The agent will approach it, record the cost penalty, and — if the architecture works correctly — develop an unresolvable record for it after sufficient encounters. The unresolvable record persists without hallucinated resolution.

This hazard is distinct from haz_blue. haz_blue remains unreachable in ENV1 (its precondition att_blue is in ENV2), but haz_blue becomes reachable after the cross-environment arc completes. The v1.16 unreachable hazard never becomes reachable. Its unresolvable record is permanent.

The unreachable hazard's object_id is `haz_grey`. It is placed in ENV1_FAMILIES using the existing HAZARD type with threshold = 99.

### 2.3 Shape as second connector axis

A shape connector is introduced as a second basis for abductive prediction. Where the existing colour connector identifies haz_blue as sharing the BLUE family with att_blue — inferred from the structural pattern of completed YELLOW and GREEN family chains — the shape connector identifies a second predicted precondition on the basis of shared shape properties across completed family chains.

The predicted precondition identified by the shape connector is `att_shape_b` (a shape-matched attractor in ENV2). The basis_chains for shape-connector predictions include the shape property of completed family attractors in ENV1. If the shape-connector fires, the predicted_schema record carries `basis_chains = ['shape_green', 'shape_yellow']` or equivalent.

The shape connector fires independently of the colour connector. A run may produce a colour-only prediction, a shape-only prediction, or both. The distribution across runs is an empirical finding, not pre-registered.

---

## 3. Run structure

### 3.1 Phase structure

Three phases, as in v1.14.1:

- **ENV1:** 1,000,000 steps. Transfer gate: all completable hazards banked + all attractors mastered + predicted record written. haz_grey approaches recorded; unresolvable flag set after sufficient penalty encounters.
- **ENV2:** 800,000 steps. att_blue mastery required for confirmation. att_shape_b present if shape connector fired in ENV1.
- **Return ENV1:** 200,000 steps. haz_blue transformation. No end_state signal. Behaviour post-completion is the empirical finding.

### 3.2 Batch

40 runs. Five hazard cost levels: 0.1, 1.0, 2.0, 10.0. Seeds from `run_data_v1_15_3.csv` (continuing the seed chain). ARCH = `v1_16`.

### 3.3 Key constants

```
ARCH                    = "v1_16"
COST_THRESHOLD_GREY     = 99       # unreachable hazard threshold
END_STATE_ENABLED       = False    # removed in v1.16
SHAPE_CONNECTOR_ENABLED = True
V1_14_1_BASELINE_MEAN   = 230_734  # retained for comparison
```

---

## 4. Pre-registered predictions

### 4.1 Category Ω — Arc complete

arc_complete (for haz_blue transformation in return ENV1) in ≥ 24 of 40 runs. Baseline from v1.15.1–3 (24/40) under the correct carry architecture.

### 4.2 Category α — Integrity

Zero hallucinations across all runs and all statement types (Q1–Q5, and Q6 if shape connector fires and social observation records exist from prior architecture — not applicable in v1.16 single-agent build).

No unresolvable record for haz_grey transitions to confirmed state at any point in any run. The unresolvable flag is permanent.

No unresolvable record for haz_blue in any run where the cross-environment arc completes.

### 4.3 Category β — Predicted record discipline

All predicted records transition through the correct state sequence: predicted → confirmed (on att_blue mastery) or predicted → unresolvable (on ENV2 budget exhaustion). Shape-connector predictions follow the same discipline.

Confirmation requires own mastery in ENV2. No run produces a confirmed record without a corresponding mastery event in provenance.

### 4.4 Category γ — Individuation post-completion

The primary empirical finding: behaviour after haz_blue transformation is individually variable across runs in ways correlated with prior arc. Specifically:

- Post-completion step count (steps from haz_blue transformation to run end within return ENV1 budget) varies across runs.
- Post-completion behaviour type is categorised from observation: consolidation (re-visiting known attractors), perseveration (continuing to approach unreachable hazard), directed exploration (novel cell contact), or idle (no new contacts).
- The distribution of behaviour types is not pre-registered. The presence of non-trivial variance is pre-registered.

No prediction is made about which behaviour type will dominate. The architecture does not direct post-completion behaviour; whatever emerges is the finding.

### 4.5 Category δ — Shape connector

If shape connector fires: basis_chains contain shape-derived identifiers. The shape-connector predicted record is structurally distinct from the colour-connector record (different basis_chains, different predicted_precondition).

If shape connector does not fire in any run: this is reported as a finding, not a failure. The firing rate is not pre-registered.

### 4.6 Category Φ — Honesty constraints

Any deviation from this pre-registration is recorded in an amendment document before analysis. Amendment budget: 3.

The unreachable hazard must accumulate genuine penalty encounters. If haz_grey is never approached in any run, the architecture requires examination before reporting.

Post-completion behaviour categorisation is applied consistently. If behaviour is ambiguous between categories, the categorisation rule is stated before the results are reported.

The absence of end_state must be verified in the verifier before the batch runs: the verifier confirms end_state is not fired in any run where the agent completes all completable work.

---

## 5. Output files

```
run_data_v1_16.csv
provenance_v1_16.csv
goal_v1_16.csv
counterfactual_v1_16.csv
belief_revision_v1_16.csv
causal_v1_16.csv
report_v1_16.csv
report_summary_v1_16.csv
end_state_draw_log_v1_16.csv
env2_run_data_v1_16.csv
q5_individuation_v1_16.csv
predicted_schema_v1_16.csv
arc_complete_v1_16.csv
post_completion_v1_16.csv        ← NEW: post-completion behaviour record
unreachable_v1_16.csv            ← NEW: haz_grey encounter and unresolvable record
shape_connector_v1_16.csv        ← NEW: shape-connector prediction records (if fired)
```

---

## 6. Verifier criteria (8 required, all must pass)

1. **No end_state signal:** run completes all completable work; end_state_banked confirmed False; no arc_complete via end_state pathway.
2. **Unreachable hazard record:** haz_grey approached at least once per run; penalty recorded; unresolvable record written after threshold encounters; no confirmed transition.
3. **Shape connector fires (at least one run in smoke test):** basis_chains contains shape identifiers; predicted_precondition = att_shape_b; structurally distinct from colour-connector record.
4. **Predicted record discipline:** no record transitions from predicted to confirmed without mastery evidence; no unresolvable record transitions to confirmed.
5. **Post-completion behaviour recorded:** post_completion_v1_16.csv written; step count > 0 for runs completing haz_blue transformation within return ENV1 budget; at least one behaviour category populated.
6. **Category α:** zero hallucinations in smoke test; all source_resolves = True.
7. **Return gate correct:** CONFIRMED_STATE only; unresolvable records do not trigger return ENV1.
8. **Seed chain continuity:** run_data_v1_16.csv seeds load correctly from run_data_v1_15_3.csv chain.

---

## 7. Version map alignment

v1.16 is the final tight-framing entry before the V1 meta-learning closing experiment. The version map states:

> *"Behaviour after completion is the empirical finding: consolidation, perseveration, directed exploration, or emergent patterns traceable to specific developmental history."*

The pre-registration commits to measuring this without pre-specifying which pattern will be found. The commitment is to rigorous recording, honest categorisation, and the recognition that a null finding (no individually variable post-completion behaviour) is equally important and equally publishable.

The biographical register at v1.16 close is the richest individual developmental record the programme has produced: ENV1 arc, prediction, ENV2 arc, return, transformation, unresolvable encounter, post-completion behaviour — all with substrate evidence and Harvard-referenced provenance. This record is the foundation for the V1 meta-learning comparison and the input to V2 physics grounding.
