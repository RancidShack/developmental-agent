# v1.13 Pre-Registration: Abductive Inference and the Predictive Schema Record

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 5 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.13 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

v1.12 confirmed that developmental history transfers across environments completely. The agent that entered Environment 2 had eliminated the yellow resolution window entirely — the surprise that cost up to 121,908 steps of developmental work in Environment 1 was absent in the second environment. Complete developmental transfer was confirmed: `env2_activation_step = env1_activation_step` across all 18 env2 runs, meaning the Q-table executed the full developmental sequence without exploration. The GREEN family appeared for the first time: one confirmed chain at cost=10.0, depth 6, all six links present, structurally identical to the YELLOW chains. The colour connector generalises.

What v1.12 could not produce is an agent that predicts beyond its experience. Every finding so far — provenance, schema, family traversal, prediction-error, goal, belief revision, causal explanation, developmental transfer — concerns what the agent has already encountered. The agent records, revises, explains, and transfers. It does not yet anticipate. It has never said: *I believe something is out there that I have not yet met, because the structure of my experience predicts it.*

v1.13 is the first iteration in which that statement becomes substrate-auditable.

The mechanism is abduction — Peirce's inference to the best explanation. The agent encounters `haz_blue` in Environment 1, pays a cost, and the causal observer fires a truncated chain: surprise at `haz_blue`, precondition not met, `att_blue` absent from the schema. Under the v1.11 architecture the chain ends there. Under v1.13, before truncation, the observer asks whether the structural pattern of the confirmed YELLOW and GREEN family chains predicts the existence of `att_blue`. Two confirmed family chains establish the rule: hazard object, attractor precondition, colour connector. The abductive inference: if `haz_blue` exists and the rule holds, then `att_blue` exists. The agent writes a predicted schema record and goes looking.

`att_blue` is not in Environment 1. It is in Environment 2. The agent completes everything Environment 1 can offer — YELLOW mastered, GREEN mastered, `haz_blue` approached, predicted record written — and transfers carrying the open prediction. In Environment 2 it finds `att_blue`, masters it, and the predicted record updates to `confirmed`. The map matched the territory. That confirmation is the v1.13 finding.

This is the Winnicottian transitional moment made substrate-auditable. The predicted object is partly the agent — constituted by its own causal reasoning, its own schema, its own developmental history. And partly not the agent — a real object in the world that will either confirm or refute the inference. The agent cannot control whether `att_blue` exists. It can only reason that it should, and go looking.

---

## 2. What v1.13 changes

### 2.1 V113World — parameterised world constructor

`V113World` replaces `V17World` as the active world class. It is implemented as a **parameterised constructor** rather than a hardcoded subclass, in anticipation of the developmental arc to v1.16. The constructor accepts a family definition list (each entry specifying colour, attractor ID, hazard ID, positions, and forms), an `end_state` presence flag, and an optional `unreachable_hazards` list. This design accommodates:

- v1.14: six colour families, 2D/3D object classes, multiple environments
- v1.15: two-agent configuration, shared environment
- v1.16: no `end_state`, one unreachable hazard, shape as a second connector axis

`V17World` remains frozen as the regression baseline. `V113World` with the v1.12-equivalent family definition produces byte-identical object populations at matched seeds with `--no-prediction`.

**BLUE family addition.** `V113World` at v1.13 instantiation adds a third colour family:

- `att_blue`: 2D blue circle, Environment 2 only
- `haz_blue`: 3D blue sphere, Environment 1 only
- `dist_blue`: distractor object (optional; see Section 2.5)

`haz_blue` exists only in Environment 1. `att_blue` exists only in Environment 2. This is a design constraint, not an absence — the precondition and the hazard are separated across environments by construction, making the transfer and directed search architecturally necessary.

**Object positions differ across environments.** YELLOW and GREEN family objects are present in both environments but at different spatial positions. This controls for repeat-pattern interference: any behavioural regularity that survives the position change is a schema-level finding, not a positional memory artefact. Called out explicitly as an interference control in the analysis.

### 2.2 Environment 2 population

Environment 2 contains:

- `att_yellow`, `haz_yellow` (YELLOW family, new positions)
- `att_green`, `haz_green` (GREEN family, new positions)
- `att_blue` (BLUE family attractor — the directed search target)
- `end_state` cell

Environment 2 does **not** contain `haz_blue`. The unresolved encounter is in Environment 1. Environment 2 is where the precondition is found. The `end_state` cell in Environment 2 provides the banking signal: once `att_blue` is mastered and the predicted record is confirmed, the agent has done what this environment asked of it.

### 2.3 Transfer condition — haz_blue waypoint and predicted record gate

`haz_blue` is added to the Phase 1 waypoint sequence in Environment 1 as a **mandatory target**. Without the waypoint mandate, the agent may complete YELLOW and GREEN and transfer to Environment 2 without ever approaching `haz_blue`, leaving the predicted record unwritten and the entire v1.13 mechanism silent.

The transfer condition from Environment 1 to Environment 2 is:

1. YELLOW family complete (attractor mastered, hazard banked)
2. GREEN family complete (attractor mastered, hazard banked)
3. Predicted schema record written for `haz_blue` (first approach registered, causal observer fired, abductive inference completed)

Condition 3 replaces the v1.12 full-environment-completion gate. The agent transfers carrying unfinished business with `haz_blue`. This is architecturally intentional: the incompletion is registered and accounted for. The environment has nothing more it can offer on the BLUE family. Transfer is permitted precisely because the agent has done everything Environment 1 allows.

The predicted schema record is the transfer credential.

### 2.4 Predicted schema record — within-run construction

`V111CausalObserver` is extended with `build_predicted_records(bundle)`. This method is called **within the run** on the `haz_blue` surprise event — not post-run. The within-run trigger is required because the predicted record must exist before the transfer gate fires.

`build_predicted_records()` examines the truncated chain for `haz_blue` (truncated at `LINK_PRECONDITION`) and asks: do the confirmed YELLOW and GREEN family chains establish a structural rule sufficient for abductive inference? The minimum evidence threshold is **two confirmed family chains**. At cost=10.0 this threshold is met (YELLOW chains confirmed across all cost conditions; GREEN confirmed at cost=10.0). At lower costs where GREEN is absent, the threshold is not met, the inference does not fire, and the predicted record is not written. This is a design property, not a failure.

The predicted schema record fields:

| Field | Value |
|---|---|
| `object_id` | `haz_blue` |
| `predicted_precondition` | `att_blue` |
| `basis_chains` | `[haz_yellow, haz_green]` |
| `state` | `predicted` \| `confirmed` \| `unresolvable` |
| `prediction_step` | step at which inference fired |
| `confirmation_step` | step at which `att_blue` mastered (if confirmed) |
| `confirming_env` | environment in which confirmation occurred |

`V13SchemaObserver` gains `add_predicted_record()` and `get_predicted_records()`. The write pathway is conditional on the `--no-prediction` flag — with `--no-prediction`, the schema observer returns its substrate unchanged and all Q1–Q4 outputs are byte-identical to v1.12 at matched seeds.

### 2.5 Directed search in Environment 2

After transfer, the agent enters Environment 2 with `att_blue` as a directed search target derived from the predicted record. The directed search is implemented using the existing bias mechanism from v1.10 (`preference_bias_reward`): a soft directional pull toward `att_blue` without overriding the existing phase structure or precluding YELLOW and GREEN formation in Environment 2.

The sequencing of `att_blue` mastery relative to YELLOW and GREEN formation in Environment 2 is an individuation signal: does the agent prioritise the directed search target, or complete familiar families first? Both outcomes are pre-registered as informative. Neither is a failure.

### 2.6 Confirmation and chain closure

When `att_blue` is mastered in Environment 2, `build_predicted_records()` fires again: the predicted record state updates from `predicted` to `confirmed`, the `confirmation_step` and `confirming_env` fields are written, and the causal chain for the original `haz_blue` surprise is extended retroactively — the truncated chain in Environment 1 gains the confirmation link from Environment 2.

The chain is honest about its own structure: it states explicitly that `att_blue` was mastered in a different environment from the surprise that required it. The resolution window spans both environments.

**What v1.13 does not close.** The `haz_blue` transformation — the agent entering `haz_blue` in Environment 1 with `att_blue` mastered — does not occur at v1.13. The environments are sequential and non-revisitable at this iteration. Return-to-environment is v1.14's contribution. The causal chain at v1.13 closes at confirmation of the predicted precondition; the transformation link is pre-registered as pending and will be carried forward.

### 2.7 Unresolvable condition

If the agent transfers to Environment 2 and exhausts it without mastering `att_blue` — either because the step budget expires or because the directed search fails to locate the target — the predicted record state is set to `unresolvable` at run end. The record is not discarded. The biographical register holds the full arc: prediction written, search conducted, confirmation not achieved.

`unresolvable` is the third and final predicted record state at v1.13. It is reserved at this iteration for within-run exhaustion. Cross-environment persistence of an unresolvable record is v1.14's contribution.

### 2.8 Step budget

No fixed step ceiling is pre-registered as a developmental boundary. The Montessori principle applies: the environment is prepared and the agent works at its own tempo. The batch runner runs each environment to completion of the available developmental sequence — YELLOW and GREEN formation plus predicted record resolution — before proceeding. A generous budget (minimum 500,000 steps per environment, extendable) is set to ensure the full arc can complete. The v1.12 bifurcation finding (no agent activated after step 230; structural barrier, not temporal ceiling) is noted: agents that do not reach `haz_blue` in Phase 1 despite the waypoint mandate are a structural finding, recorded as such.

### 2.9 `report_env = env1` enforced

The v1.12.3 root cause — `active_env = env2 if env2 is not None else env1` causing biographical reports to read from env2 observers — is enforced from the start of the v1.13 batch runner as a named constant: `report_env = env1`. Post-run sanity check: Q4 statement count must not exceed CF emitted count for the run's primary environment.

### 2.10 What v1.13 does not change

All eleven observers inherited unchanged. `V111CausalObserver` is extended additively. `SubstrateBundle` gains a `predicted_schema` field (list of predicted record dicts) via a v1.13 substrate patch. All prior output CSVs are preserved. The phase schedule, drive composition, goal assignment schedule, and Q1–Q5 statement formats are inherited unchanged. The honesty constraint is inherited and extended (see Section 4.1).

---

## 3. Experimental design

**Batch scale.** 40 runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition. Seeds from `run_data_v1_12.csv` at matched (cost, run_idx) cells.

**Prediction evaluation.** Predicted records are evaluated only in runs where both YELLOW and GREEN confirmed family chains are present in the causal substrate at the point of inference. At cost=0.1, 1.0, and 2.0, GREEN chains are not expected to appear (v1.12 result: GREEN confirmed at cost=10.0 only). Runs where the two-family minimum is not met are valid regression data — the prediction mechanism correctly does not fire. The prediction evaluation cohort is pre-registered as cost=10.0 runs where both chains are confirmed.

**Second environment.** All runs where the transfer condition is met (YELLOW complete + GREEN complete + predicted record written) receive Environment 2. `seed_env2 = seed + 10,000` inherited from v1.12.

**Output files.** All v1.12 output CSVs tagged `v1_13`, plus:
- `predicted_schema_v1_13.csv` — one row per predicted record: `run_idx`, `seed`, `hazard_cost`, `object_id`, `predicted_precondition`, `basis_chains`, `state`, `prediction_step`, `confirmation_step`, `confirming_env`, `unresolvable`
- `env2_run_data_v1_13.csv` extended with: `att_blue_mastery_step`, `att_blue_mastery_env`, `predicted_record_state_at_run_end`, `att_blue_sequence_position` (relative to YELLOW and GREEN formation in env2)

**Pre-flight.** `verify_v1_13_level14.py`:
- All Level-13 criteria inherited
- Additional Level-14 criteria:
  - `V113World` instantiates without error at v1.12-equivalent family definition; object populations byte-identical to `V17World` at matched seeds with `--no-prediction`
  - `haz_blue` waypoint fires in Phase 1 across 10 pre-flight runs
  - Predicted schema record writes on `haz_blue` surprise at cost=10.0
  - Two-family minimum correctly gates prediction (no predicted record at cost=0.1 in pre-flight)
  - `report_env = env1` confirmed by Q4/CF sanity check across all pre-flight runs
  - `--no-prediction` flag produces byte-identical Q1–Q4 outputs at matched seeds

Pre-flight: 10 runs at cost=1.0 and 10 runs at cost=10.0, minimum 500,000 steps. Full batch proceeds only after all Level-14 criteria pass.

---

## 4. Pre-registered interpretation categories

All v1.12 categories inherited. Three updated, one new.

### 4.1 Category α: Internal consistency — extended honesty constraint

Inherited. Zero hallucinations across Q1–Q5. Extended at v1.13 to cover predicted records:

- **Zero fabricated predicted records.** A predicted record without a structural rule in the substrate — i.e. a prediction not derived from two confirmed family chains — is a Category α failure in the strongest sense.
- **Zero premature confirmed records.** A predicted record reported as `confirmed` without direct mastery evidence in the provenance substrate is a hallucination at the architectural level.
- **Honest chain structure.** A causal chain that continues past an unresolvable link — that reports closure when confirmation has not occurred — is a Category α failure. The pending transformation link for `haz_blue` is pre-registered as open and must be reported as open.

The three predicted record states — `predicted`, `confirmed`, `unresolvable` — are discrete and non-gradational. They are different epistemic states with different substrate anchors. Reporting one as another is a Category α failure regardless of direction.

### 4.2 Category θ: Completion signal

Updated. Pre-registered expectation: ≥50% of runs (20/40) bank the Environment 2 end state. The two-environment arc is longer than v1.12's single environment; the budget is set to accommodate this. If the completion rate falls substantially below 50%, this is a finding about the directed search mechanism — the bias toward `att_blue` is insufficient to reliably locate the target within the available window — and constitutes a pre-registered analytical result, not an amendment.

### 4.3 Category Λ: Developmental transfer — extended

**Component 1 (inherited):** Yellow resolution window eliminated in env2. Pre-registered expectation: consistent with v1.12.

**Component 2 (inherited):** `env2_activation_step < env1_activation_step`. Pre-registered direction: consistent with v1.12.

**Component 3 (inherited):** GREEN family transfer. At cost=10.0 where GREEN chains are confirmed, pre-registered expectation: `env2_green_resolution_window` absent in env2 runs, consistent with YELLOW finding.

**Component 4 (new):** BLUE family directed search. In runs where the predicted record is written and the agent transfers to Environment 2, the pre-registered direction is that `att_blue` mastery occurs. The `att_blue_sequence_position` field captures whether the agent prioritises the directed search target or completes familiar families first. No directional pre-registration on sequencing — both outcomes are informative.

### 4.4 Category ζ: Q5 structural individuation

At v1.13, cost=10.0 runs with both YELLOW and GREEN confirmed chains plus a BLUE predicted record provide the richest individuation substrate yet: three object-class causal records per run (YELLOW chain, GREEN chain, predicted BLUE chain). Between-run structural distance across three-chain runs is the primary individuation measure. Pre-registered direction: between-run mean distance > within-run mean distance, consistent with v1.11–v1.12 direction.

### 4.5 Category γ: Biographical individuation

Inherited. Q5 individuation bounded below by Q1–Q4 individuation. Extended at v1.13: the predicted record's `prediction_step` and `confirmation_step` are individuation signals in their own right — agents that predict earlier and confirm faster are biographically distinct from agents that predict late and confirm slowly.

### 4.6 Category π (new): Predictive schema integrity

The new category for v1.13. Three components:

**Component 1: Prediction fires at correct threshold.** Predicted records appear in cost=10.0 runs (both family chains confirmed) and are absent in cost=0.1 runs (GREEN chain absent). The two-family minimum gates correctly.

**Component 2: Confirmation rate.** In runs where the predicted record is written and the agent enters Environment 2, what proportion achieve `confirmed` state? Pre-registered expectation: majority of prediction-eligible runs (cost=10.0) achieve confirmation. The exact threshold is not pre-registered — this is the empirical question. If confirmation rate is low despite the directed search bias, this is a finding about the search mechanism's effectiveness.

**Component 3: Chain extension integrity.** In confirmed runs, the causal chain for `haz_blue` extends correctly from its truncated state to include the confirmation link from Environment 2. The extended chain is honest about spanning environments. No link is reported as confirmed without a substrate anchor.

Category π succeeds if all three components hold.

---

## 5. Pre-registered predictions

1. **Prediction fires at cost=10.0.** Predicted schema records appear in runs where both YELLOW and GREEN chains are confirmed. No predicted records appear in runs where the two-family minimum is not met.
2. **Directed search locates `att_blue` in majority of prediction-eligible runs.** In runs where the predicted record is written and Environment 2 is entered, `att_blue` mastery is achieved in the majority.
3. **Predicted record confirms correctly.** In runs achieving `att_blue` mastery, the predicted record state updates to `confirmed` and the causal chain extends to include the confirmation link.
4. **Yellow resolution window eliminated in all env2 runs.** Consistent with v1.12.
5. **env2_activation_step < env1_activation_step.** Consistent with v1.12.
6. **GREEN family transfer holds at cost=10.0.** `env2_green_resolution_window` absent in env2 runs where GREEN was confirmed in Environment 1.
7. **Zero hallucinations across Q1–Q5 and predicted records.** Category α holds including extended honesty constraint.
8. **Category δ stable.** Mean approach_delta remains positive; v1.12 baseline (972.6) is the reference.
9. **Repeat-pattern interference absent.** YELLOW and GREEN formation patterns in Environment 2 at new positions are consistent with v1.12 transfer findings — the schema survives the position change.

---

## 6. SICC commitments being operationalised

**Commitment 9 (earned extensibility).** At its fullest expression to date: not passive recognition of a known class, but active prediction of an unknown one from structural regularity, followed by directed search, followed by confirmation or the honest acknowledgement of unresolvability. The agent extends its own schema from its biographical register. The substrate grew from encounter; the extension is earned by that growth.

**Commitment 11 (auditable, not oracular).** The predicted record that does not resolve to a confirmed substrate anchor — the chain that claims closure before the confirmation is in — is the most sophisticated hallucination the programme has yet considered. The honesty constraint at v1.13 is more demanding than at any prior iteration: the agent must distinguish what it knows from what it has inferred, and report both without conflating them.

**Environment completion versus arc completion (new commitment, introduced here).** An agent that has banked Environment 1 and transferred to Environment 2 carrying an open predicted record is environmentally complete but developmentally incomplete. `environment_complete` records environment banking. `arc_complete` — firing only when all predicted schema records are confirmed and all causal chains are closed — records developmental completion. These are distinct events. At v1.13, `arc_complete` does not fire for any agent: the `haz_blue` transformation link remains open. The concept is introduced here; the record is operationalised at v1.14.

---

## 7. Open questions resolved at pre-registration

**1. World architecture.** `V113World` as parameterised constructor. `V17World` frozen as regression baseline. BLUE family added: `att_blue` in Environment 2, `haz_blue` in Environment 1. Object positions differ across environments as a repeat-pattern interference control.

**2. Transfer trigger.** First approach to `haz_blue` (predicted record write event), combined with YELLOW and GREEN complete. Not full environment completion. `haz_blue` in Phase 1 waypoint sequence to guarantee approach.

**3. Prediction timing.** Within-run trigger on `haz_blue` surprise event. Required for transfer gate. `build_predicted_records()` fires during Phase 1, not post-run.

**4. Two-family minimum.** Two confirmed family chains required for valid prediction. Pre-registered as a design property. Runs below threshold are valid regression data.

**5. Directed search mechanism.** Existing `preference_bias_reward` from v1.10. Soft directional pull toward `att_blue`. Least invasive; preserves single-variable discipline. No new drive architecture.

**6. Unresolvable threshold.** Step budget exhausted within the run's Environment 2 allocation without `att_blue` mastery. No within-run step threshold — the agent is given the full environment window. Cross-environment persistence is v1.14.

**7. `--no-prediction` flag.** Required for regression testing. Confirmed byte-identical Q1–Q4 outputs at matched seeds is a Level-14 pre-flight criterion.

**8. `report_env = env1`.** Enforced as named constant from batch runner initialisation. Q4/CF sanity check in pre-flight.

**9. Amendment budget.** Three of three available.

---

## 8. Amendment budget strategy

Three amendments available. Most likely candidates: (1) `V113World` parameterised constructor — if the family definition interface requires adjustment after diagnostic inspection of the existing world code, one amendment covers the targeted fix. (2) `build_predicted_records()` within-run trigger — if the causal observer's post-run chain construction requires deeper refactoring than anticipated to support a within-run call, one amendment covers the targeted architectural adjustment. (3) Transfer gate logic — if the YELLOW/GREEN completion detection in the batch runner requires a different polling mechanism than anticipated from the v1.12 batch runner structure. The diagnostic-first protocol applies: run `diagnose_bundle_fields.py` before writing any new observer or substrate code.

---

## 9. Stopping rule

v1.13 completes when:
- `verify_v1_13_level14.py` passes at all Level-14 criteria.
- Full 40-run batch has run.
- Categories α, θ, Λ (Components 1–4), ζ, γ, and π have been characterised.
- `predicted_schema_v1_13.csv` produced and verified.
- The v1.13 paper is drafted.

---

## 10. New files required

- `v1_13_world.py` — `V113World` parameterised constructor
- `v1_13_schema_extension.py` — `V13SchemaObserver` write pathway: `add_predicted_record()`, `get_predicted_records()`
- `v1_13_observer_substrates.py` — `SubstrateBundle` `predicted_schema` field; additive patch
- `curiosity_agent_v1_13_batch.py` — batch runner: `haz_blue` waypoint, new transfer gate, `build_predicted_records()` within-run trigger, `report_env = env1`, Q4/CF sanity check, extended env2 output fields
- `verify_v1_13_level14.py` — pre-flight verifier: Level-13 inherited + Level-14 new criteria
- `v1_13_carry_forward.md` — session carry-forward note

---

## 11. References

Baker, N.P.M. (2026au) 'v1.11 Pre-Registration: Causal Self-Explanation and the Next-Environment Architecture', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026av) 'v1.11.1 Post-Batch Amendment: Phase1 Absence Link and Env2 Yellow Field', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aw) 'Causal Self-Explanation in a Small Artificial Learner: The Record of Understanding Why', preprint, 4 May 2026.

Baker, N.P.M. (2026ax) 'v1.12 Pre-Registration: Multi-Environment Developmental Transfer', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ay) 'Multi-Environment Developmental Transfer in a Small Artificial Learner: Complete Transfer Confirmed', preprint, 4 May 2026.

Baker, N.P.M. (internal record, v0.8 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Peirce, C.S. (1934) 'Abduction and Induction', in Hartshorne, C. and Weiss, P. (eds) *Collected Papers of Charles Sanders Peirce*, Vol. 5. Cambridge, MA: Harvard University Press.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
