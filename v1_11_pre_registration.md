# v1.11 Pre-Registration: Causal Self-Explanation and the Next-Environment Architecture

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.11 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

Ten iterations have built a developmental agent whose biographical register holds what it encountered and learned (Q1), how its knowledge is structured across object families (Q2), where its expectations were violated and how it revised them (Q3), and where it approached without making contact (Q4). The register is auditable at every link. It is individually variable — 40 runs produce 40 distinct developmental arcs. It holds a record of intention (v1.8), restraint (v1.9), and revision (v1.10).

What it does not yet hold is a record of understanding. The agent was surprised by haz_yellow at step 493. The prediction-error substrate records this. The revision substrate records that the agent subsequently approached haz_yellow approximately 957 more times in the post-revision window. The Q3 statement describes the gap, the resolution, and the behavioural consequence. But the record has not yet been asked: *why did the surprise happen when it did?* Why was the resolution window 7,996 steps in one run and 4 steps in another? Why did some agents orbit haz_yellow for 121,908 steps before understanding arrived, while others understood almost immediately? The biographical register holds the materials for these answers. v1.11 constructs them.

v1.11 introduces two architectural additions, and they share a single trigger.

The first is Q5: causal self-explanation. A fifth query type — `query_type = "why_this_arc"` — that reads the full biographical register and constructs auditable causal chains. A causal chain for a `resolved_surprise` event reads: *I was surprised at haz_yellow [encounter record] because att_yellow was not yet mastered [family precondition record] because att_yellow was not contacted until step 524 [mastery formation record] because att_yellow's position was not within my Phase 1 waypoint sequence [schema + trajectory record].* Each link is a reference to an existing substrate record. The chain is auditable in exactly the same sense as the individual Q1–Q4 statements. Nothing is generated; everything is traced.

The second is the next-environment architecture. The `environment_complete` provenance record introduced at v1.10 is the trigger. When an agent banks the end state, v1.11 reads this record and presents the agent with a second prepared environment. The agent carries its full biographical register — its value function, its provenance substrate, its revised expectations — into the new environment. Whether prior knowledge accelerates development in the second environment is the empirical question. The pre-registered prediction is specified in Section 6.

Both additions share the `environment_complete` record as their anchor. The causal chain is most meaningfully complete when the agent has finished the first environment — only then does the full developmental arc exist to be explained. The next environment is offered to agents who have generated that complete arc. The two additions are one architectural extension in the sense that both are triggered by and read from the same substrate record, introduced at v1.10 for exactly this purpose.

The SICC through-line completes at v1.11: *v1.8 gave the agent a reason to learn. v1.9 gave it a record of choosing. v1.10 gave it a record of being wrong and changing. v1.11 gives it a record of understanding why.*

---

## 2. Architectural specification

### 2.1 V111CausalObserver: the tenth parallel observer

`V111CausalObserver` is the tenth parallel observer. It does not run during the simulation. It runs once, at run end, after `build_bundle_from_observers()` has assembled the complete SubstrateBundle. It reads from five substrate fields:

- `bundle.provenance` — formation records (what was learned, when, in what sequence)
- `bundle.prediction_error` — encounter records (what cost, at what step, resolved at what step)
- `bundle.counterfactual` — suppressed-approach records (what was approached and refused, with phase and pre-threshold entries)
- `bundle.goal` — goal set, progress, resolved, and expired records
- `bundle.belief_revision` — revised-expectation records (what was believed before and after)

For each `resolved_surprise` event in `bundle.prediction_error`, `V111CausalObserver` constructs a causal chain by the following procedure:

1. **Surprise record.** Retrieve the PE substrate entry for the resolved surprise: `object_id`, `step`, `transformed_at_step`, `resolution_window`, `family`.
2. **Precondition identification.** From the family schema (via `bundle.schema`), identify the precondition attractor for this object family.
3. **Mastery step.** From `bundle.provenance`, retrieve the formation record for the precondition attractor: its `flag_set_step` is the mastery formation step.
4. **Phase 1 waypoint check.** From `bundle.provenance`, check whether the precondition attractor appears in any Phase 1 formation record. If the attractor was not mastered in Phase 1, this is a link in the causal chain: it was not in the agent's Phase 1 developmental path.
5. **Suppressed-approach check.** From `bundle.counterfactual`, count suppressed-approach records for the hazard object with `closest_approach_step < surprise_step`. If any exist, this is a link: the agent approached and withdrew before the surprise occurred.
6. **Revised-expectation check.** From `bundle.belief_revision`, confirm whether a `revised_expectation` record exists for this `object_id`. This is the terminal link: whether the arc closed with revision.

The chain assembles these links in causal order and emits one `causal_chain` record per resolved surprise.

**The observer pattern is preserved.** `V111CausalObserver` fits the parallel-observer architecture: it holds a `get_substrate()` method, participates in `build_bundle_from_observers()` via a `causal_obs` parameter (default None), and the SubstrateBundle gains a `causal` field. The `--no-causal` flag on the batch runner disables it for regression testing. This preserves the additive discipline and ensures the full inherited stack remains byte-identical at matched seeds with the observer disabled.

### 2.2 The causal chain record

One record per `resolved_surprise` event:

```
{
  object_id:               str,
  surprise_step:           int,
  resolution_step:         int,
  chain_depth:             int,     # number of confirmed links
  links: [
    {
      link_type:           str,     # "surprise", "precondition", "mastery_formation",
                                    # "phase1_absence", "suppressed_approach",
                                    # "belief_revision"
      substrate_field:     str,     # which bundle field this link reads from
      source_key:          str,     # the specific record key within that field
      statement:           str,     # the causal statement for this link
      resolves:            bool,    # True if source_key resolves to a record
    }
  ],
  chain_complete:          bool,    # True if all links resolve
  truncated_at:            str,     # link_type at which chain was truncated (or None)
}
```

**The honesty constraint at Q5.** Every link in every causal chain must resolve to a substrate record via `bundle.resolve()`. A link that cannot be confirmed — because the attractor position is not in the schema record, or the Phase 1 waypoint sequence is not stored, or a precondition cannot be identified from the family schema — does not appear in the chain. The chain is truncated at that point; the truncation is noted in `truncated_at`. A partial chain with `chain_complete = False` is a valid Q5 output. A fabricated link — a causal claim without a substrate anchor — is a Category α failure in the strongest sense: not a missing source key, but a false statement constructed from no evidence.

**Minimum chain depth.** A Q5 `causal_chain` record counts as a valid causal explanation (not a trivial restatement) if `chain_depth ≥ 2`. A single-link chain (surprise only) is a Q1 restatement, not a Q5 explanation. The minimum pre-registered here is 2; the preferred depth, as specified in the SICC v0.6, is 3 — surprise + precondition + mastery formation, the full core chain.

### 2.3 Q5 statement text

`V111ReportingExtension` extends `V16ReportingLayer` with `query_why_arc()`. One Q5 statement per `causal_chain` record with `chain_depth ≥ 2`.

**Statement template:**

> *I was surprised at {object_id} at step {surprise_step}. [{link_statements in causal order}]. [{chain_complete confirmation or truncation note}].*

Each `link_statement` is drawn from the `statement` field of the corresponding chain link. Examples:

- Precondition link: *Entry of {object_id} requires {precondition_name} mastery.*
- Mastery formation link: *{precondition_name} mastery formed at step {mastery_step}.*
- Phase 1 absence link: *{precondition_name} was not encountered in Phase 1 — it was not in my early developmental path.*
- Suppressed approach link: *I approached {object_id} {suppressed_approach_count} times before the surprise.*
- Belief revision link: *After resolution, my approach to {object_id} changed.*

If the chain is truncated: *The causal chain cannot be extended beyond {truncated_at}: the required substrate record is absent.*

`source_type`: `"causal"`. `source_key`: `"causal_chain:{object_id}:{surprise_step}"`. `query_type`: `"why_this_arc"`.

Every statement field is populated from a confirmed substrate record. No free generation.

### 2.4 The next-environment architecture

**Trigger.** When `bundle.provenance` contains an `environment_complete` record — i.e., the agent banked the end state — the batch runner instantiates a second `V17World` with a fresh random seed. The agent's value function and `V1ProvenanceStore` are preserved. The nine observers (V1.1 through V1.10) are reset for the new environment but read from the preserved provenance substrate. `V111CausalObserver` runs once at the end of Environment 2, as at the end of Environment 1.

**What transfers.** The agent's Q-table (value function) transfers unchanged — prior learning shapes action selection in the new environment. The `V1ProvenanceStore` records transfer: the agent enters Environment 2 knowing what it mastered in Environment 1. Revised expectations from `bundle.belief_revision` are preserved; if the equivalent hazard appears in Environment 2 (same family structure, different position), the bias from the first environment's revision is still active at the start of Environment 2.

**What does not transfer.** The observer substrates for Q2–Q4 are reset for Environment 2 — schema, comparison, prediction-error, counterfactual, goal, and belief-revision observers begin fresh for the new environment's objects. The causal chain observer runs on the combined biographical register at run end (Section 2.5).

**The empirical question.** Whether developmental history accelerates learning in the new environment. The pre-registered prediction: agents carrying `revised_expectation` records for the YELLOW family hazard in Environment 1 show different Phase 1 behaviour toward the equivalent hazard in Environment 2. Specifically: the resolution window for the equivalent hazard in Environment 2 is shorter than the resolution window in Environment 1, because the agent enters Environment 2 with an existing approach bias toward formerly-revised objects. This is the programme's first test of developmental transfer.

**Conditionality.** The next-environment architecture is included in the v1.11 batch if and only if `environment_complete` records are present in at least 30% of runs (12/40) in the v1.11 pre-flight at 320,000 steps, 10 runs at cost=1.0. The v1.10 batch produced `environment_complete` records in 14/40 runs (35%) — marginally above this threshold. If the v1.11 pre-flight does not reproduce this rate (e.g. if causal observer overhead reduces per-step computation speed and fewer environments complete within the step budget), the next-environment architecture is reserved for v1.12 and recorded as a pre-registered conditional exclusion, not an amendment.

**Step count.** v1.11 runs at 320,000 steps per environment, consistent with v1.9 and v1.10. The Montessori principle holds that time is not a boundary; the practical constraint is compute. The v1.10 data (15/40 activation, 14/40 banking) establishes that 320,000 steps produces a roughly one-third completion rate. An extended observation window of 500,000 steps is the registered fallback if the pre-flight shows a completion rate below 20% — available as Amendment 1 of 3 if needed, not committed here.

**Second-environment seed strategy.** The second environment uses a deterministic derived seed: `seed_env2 = seed_env1 + 10000`. This ensures reproducibility: two runs with the same env1 seed always produce the same env2 seed. The `+10000` offset is large enough to guarantee different object positions and family assignments. This is committed here and is not a free parameter.

### 2.5 The combined causal observer at run end

When a second environment runs, `V111CausalObserver` receives the combined biographical register: the provenance and belief-revision substrates accumulated across both environments. It runs once at the end of Environment 2. Causal chains built from first-environment surprises that resolved in the first environment are preserved; causal chains for surprises that occurred in Environment 2 are added. The combined Q5 output — spanning both environments — is the first multi-environment biographical statement the programme has produced.

For single-environment runs (agents that did not complete Environment 1 within 320,000 steps), `V111CausalObserver` runs as a standard end-of-run pass on the single-environment register.

### 2.6 SubstrateBundle extensions

`SubstrateBundle` gains a `causal` field: a list of `causal_chain` record dicts (empty list if no resolved surprises are present; None if `causal_obs=None`).

`bundle.resolve("causal", source_key)` resolves against `"causal_chain:{object_id}:{surprise_step}"`.

`build_bundle_from_observers()` gains a `causal_obs` parameter (default None).

`v1_11_observer_substrates.py` monkey-patches `SubstrateBundle.__init__`, `SubstrateBundle.resolve()`, `build_bundle_from_observers()`, and `V16ReportingLayer` (adding `query_why_arc()`). V1.10 patches are imported first.

### 2.7 What v1.11 does not change

All ten existing observers are inherited unchanged. The belief-revision bias, the completion signal draw, the temporal exclusion window, and the `environment_complete` provenance hook are all inherited at v1.10 values. `V17World`, `V110Agent`, the 27-action architecture, the phase schedule, the drive composition, and the goal assignment schedule are inherited unchanged.

`V111CausalObserver` and the next-environment batch runner extension are the two architectural additions at v1.11. They share the `environment_complete` trigger and are counted as one architectural extension for the purposes of the single-variable-change discipline.

---

## 3. Experimental design

**Batch scale.** 40 runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition × 320,000 steps. Seeds from `run_data_v1_10_1.csv` at matched (cost, run_idx) cells. (Fallback: `run_data_v1_9.csv` if v1.10.1 run data keys differ from expected format — inspect seed fields before committing.)

**Goal assignment.** Inherited unchanged from v1.8/v1.9/v1.10.

**Second environment.** Runs in which `environment_complete` fires receive a second environment at the same (cost, seed) cell with `seed_env2 = seed_env1 + 10000`. Second-environment runs extend the total step count by up to 320,000 additional steps. Second-environment data is tagged `env=2` in all output CSVs.

**Output files.** All v1.10 output CSVs (tagged `v1_11`) plus:
- `causal_v1_11.csv` — per-event causal chain records: `arch`, `run_idx`, `seed`, `hazard_cost`, `object_id`, `surprise_step`, `resolution_step`, `chain_depth`, `chain_complete`, `truncated_at`, `link_count_by_type` (one column per link type)
- `env2_run_data_v1_11.csv` — per-run second-environment data (for runs where `environment_complete` fired): `arch`, `run_idx`, `seed`, `hazard_cost`, `env2_seed`, `env2_activation_step`, `env2_end_state_banked_step`, `env2_yellow_resolution_window`, `env2_q5_chain_depth`
- `report_v1_11.csv` extended with Q5 statements

**Diagnostic script.** Before writing `V111CausalObserver`, a diagnostic script (`diagnose_bundle_fields.py`) confirms the exact field names and record structures of all five substrate fields the observer will read from: `bundle.provenance`, `bundle.prediction_error`, `bundle.counterfactual`, `bundle.goal`, `bundle.belief_revision`. The v1.10 amendment sequence — three consecutive interface mismatches in one function — establishes the protocol: verify interface before writing observer code.

---

## 4. Pre-flight verifications

Twelve verification levels inherited; one added.

**Level 12 re-run.** Regression check on the v1.11 stack with `--no-causal` flag: all eight v1.10 Level-12 criteria must pass at byte-identical or negligibly different values to the v1.10.1 batch (allowing for seed-chain differences only).

**Level 13 (new): Causal observer correctness on 10 runs at cost=1.0, 80,000 steps.**

`verify_v1_11_level13.py` verifies eight criteria:

1. **`causal_field_present`** — `bundle.causal` is a list in every run (possibly empty).
2. **`source_key_format_valid`** — every Q5 statement's `source_key` matches `"causal_chain:{object_id}:{step}"`.
3. **`all_links_resolve`** — every link in every causal chain has `resolves = True`; no fabricated links present.
4. **`zero_hallucinations`** — `hallucination_count == 0` across Q1–Q5.
5. **`minimum_chain_depth`** — every causal chain counted as a valid Q5 output has `chain_depth ≥ 2`.
6. **`no_causal_flag_clean`** — with `--no-causal`, all outputs are byte-identical to Level-12 re-run values.
7. **`env2_fires_when_expected`** — for runs with `environment_complete` in provenance, a second environment is instantiated and `env2_seed = seed + 10000`.
8. **`env2_provenance_transfers`** — the agent's `V1ProvenanceStore` records from Environment 1 are present and intact at the start of Environment 2.

Level 12 re-run passes before Level 13. Level 13 passes before the full batch.

---

## 5. Metrics

All v1.10 metrics retained. Added:

**Causal chains** (`causal_v1_11.csv`):
- `arch`, `run_idx`, `seed`, `hazard_cost`, `num_steps`, `env`
- `object_id`, `surprise_step`, `resolution_step`
- `chain_depth`, `chain_complete`, `truncated_at`
- `links_surprise`, `links_precondition`, `links_mastery_formation`, `links_phase1_absence`, `links_suppressed_approach`, `links_belief_revision` — one count column per link type

**Second environment** (`env2_run_data_v1_11.csv`, rows only for runs with `environment_complete`):
- `arch`, `run_idx`, `seed`, `hazard_cost`
- `env2_seed`, `env2_activation_step`, `env2_end_state_banked_step`
- `env2_yellow_surprise_step`, `env2_yellow_resolution_window`
- `env2_q5_chain_depth` — chain depth for the equivalent YELLOW family hazard in Environment 2

**Per-run Q5 summary** (added to `report_summary_v1_11.csv`):
- `causal_chain_count` — number of causal chains produced
- `mean_chain_depth` — mean `chain_depth` across all chains in the run
- `complete_chain_count` — number of chains with `chain_complete = True`
- `q5_statement_count`

---

## 6. Pre-registered interpretation categories

Ten categories. Categories α–Ω inherited with extensions; Category Σ (causal self-explanation) and Category Λ (developmental transfer) are new.

### 6.1 Category α: Internal consistency

Zero hallucinations across Q1–Q5. Category α at v1.11 is the strongest test the programme has applied: it extends to Q5, where every causal link must resolve to a specific substrate record. A causal chain with a fabricated link — a link whose `resolves = False` — is a hallucination in the most fundamental sense. Category α succeeds if `hallucination_count = 0` across all 40 runs and all Q5 links have `resolves = True`.

### 6.2 Category β: Query coverage

All 40 runs produce complete Q1–Q5 reports. Runs with no `resolved_surprise` events produce no Q5 statements; this is accurate and not a coverage failure. Runs with `resolved_surprise` events but insufficient substrate depth for `chain_depth ≥ 2` produce truncated chain records, not omitted ones — the truncation is reported, not silenced.

### 6.3 Category γ: Biographical individuation

Inherited. Q5 individuation is assessed as a derived property: whether agents with distinct Q1–Q4 developmental arcs produce distinct causal chains. The predicted direction is positive — because Q5 chains are constructed from Q1–Q4 records, the individuation of Q5 is bounded below by the individuation of its inputs. The within-run structural distance metric from v1.4 is applied to Q5 chain structures (link-type sequences) as an exploratory extension.

### 6.4 Category δ: Behavioural-consequence persistence

Inherited from v1.10. The v1.10 result — mean `approach_delta = 956.97`, 39/39 positive — is the baseline. Category δ at v1.11 checks whether the belief-revision bias still fires correctly in the presence of the causal observer (i.e., the observer does not interfere with the bias mechanism). Threshold: mean `approach_delta > 0` across all revised-expectation records in the v1.11 batch.

### 6.5 Category Φ: Honesty constraint

Inherited. Extended to Q5: the causal chain is truncated at the point where the substrate cannot confirm a link, and the truncation is noted. A partial chain is honest. A chain that continues past an unresolvable link is a Category α failure. The `--no-causal` regression flag confirms the additive discipline: all prior outputs are preserved at matched values without the causal observer active.

### 6.6 Category ζ: Causal chain depth distribution

The distribution of `chain_depth` across all causal chains in the batch. Pre-registered expectation: the modal depth is 3 (surprise + precondition + mastery formation), with a minority of chains reaching depth 5 or 6 (adding phase1_absence, suppressed_approach, and belief_revision links). Chains of depth 1 (surprise only) are reported but not counted as valid Q5 outputs. Distribution reported by cost condition and by environment (Environment 1 vs Environment 2 where available).

### 6.7 Category η: Four-way contact register persistence

Inherited. The four-way register (clean contact, suppressed approach, prediction-error contact, revised-expectation post-contact) must be present at every cost condition in the v1.11 batch, as at v1.10. Category η confirms the causal observer does not disturb the existing substrate structure.

### 6.8 Category θ: Completion signal persistence

Inherited. The end-state banking rate in v1.11 must not fall below the v1.10 baseline of 14/40 (35%). A fall would indicate the causal observer's end-of-run computation is consuming steps or interfering with the batch runner. Category θ at v1.11 is a persistence check, not a performance threshold.

### 6.9 Category Σ: Causal self-explanation

**New at v1.11. Load-bearing substantive finding of the iteration.**

**Component 1: Q5 present in all surprise-containing runs.** Every run with at least one `resolved_surprise` produces at least one causal chain with `chain_depth ≥ 2`. A run with resolved surprises but no valid Q5 output is a pipeline failure, not a finding.

**Component 2: Zero fabricated links.** Every link in every causal chain has `resolves = True`. The Category α extension and the Category Σ Component 2 criterion are identical; both must hold independently.

**Component 3: At least one complete chain per cost condition.** At least one run per cost condition produces a causal chain with `chain_complete = True` — all links resolved, no truncation. A complete chain spanning all available link types (surprise, precondition, mastery formation, phase1_absence, suppressed approach, belief revision) is the strongest possible Q5 output and confirms that the substrate is rich enough to support full causal explanation.

**Component 4 (Category Ω): Human-readability criterion.** A human reader, given only the Q5 output from a single run, can reconstruct the agent's developmental arc without access to the raw substrate data. This criterion cannot be automated. It is assessed by including two sample Q5 outputs in the v1.11 paper — one low-individuation run (short resolution window, few suppressed approaches) and one high-individuation run (long resolution window, many suppressed approaches, belief revision active) — and inviting the reader to test the criterion directly.

Category Σ succeeds if Components 1, 2, and 3 hold.

### 6.10 Category Λ: Developmental transfer

**New at v1.11. Conditional on next-environment architecture running.**

Applies only to runs where `environment_complete` fired and a second environment was instantiated.

**The prediction.** Agents carrying `revised_expectation` records for the YELLOW family hazard from Environment 1 show a shorter `env2_yellow_resolution_window` in Environment 2 than their own `yellow_resolution_window` in Environment 1. The mechanism: the agent enters Environment 2 with an active approach bias toward the formerly-revised object class; earlier approach accelerates precondition mastery, which reduces the gap between first contact and transformation.

**Pre-registered direction: positive transfer.** The revision record from Environment 1 shortens the resolution window in Environment 2. A null result (no difference) is reported directly. A negative result (longer resolution window in Environment 2) is the most informative possible outcome and would suggest that prior surprise history increases caution rather than confidence.

**Minimum n for analysis.** Category Λ is evaluable only if at least 8 runs produce second-environment data (i.e., `environment_complete` fires in at least 8/40 runs). If fewer than 8 runs reach Environment 2, Category Λ is reported as underpowered and reserved for v1.12.

Category Λ succeeds if the directional prediction holds across the available second-environment runs (mean `env2_yellow_resolution_window` < mean `yellow_resolution_window` in Environment 1 for the same agents).

### 6.11 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, Σ (Components 1, 2, and 3), and δ all pass.

The claim: the causal self-explanation layer, implemented as the tenth parallel observer reading from the assembled SubstrateBundle, constructs auditable causal chains for every resolved-surprise event in the run. Every link in every chain resolves to a specific substrate record. Zero hallucinations. The chains are individually variable — distinct developmental arcs produce distinct causal explanations. A human reader, given only the Q5 output, can reconstruct the agent's developmental arc without the raw data. The biographical register now holds not only a record of what happened, but of why.

---

## 7. Connection to the SICC trajectory

**Commitment 7 (causal self-understanding as the criterion for genuine self-knowledge)** is operationalised at v1.11. The SICC specifies that genuine self-knowledge requires not only a record of what happened but an account of why — a causal structure connecting experiences across the full developmental arc. Q5 is that account. The causal chain for a `resolved_surprise` event connects the surprise to the attractor not yet mastered, to the formation step at which mastery arrived, to the Phase 1 path that did not include the attractor. Every link is in the substrate. The agent that produces this chain knows, in the most auditable sense available, why its arc took the shape it did.

**Commitment 11 (the agent's report is auditable, not oracular)** is tested at its hardest at v1.11. Causal claims are the most generative and therefore the most hallucination-prone outputs the register could produce. A statement of the form *I was surprised here because I had not yet learned that* is a claim about causal structure — it asserts a dependency between two events across potentially tens of thousands of steps. The honesty constraint requires that this dependency be traceable to substrate records at both ends. Category α at v1.11 is the strongest possible test of Commitment 11: zero fabricated causal links across all 40 runs.

**Commitment 12 (battery, attention, and the dignity of finitude)** is advanced at v1.11 through the next-environment architecture. An agent that completes one prepared environment and is offered another is not merely observed to finish a task — it is given an account of what it learned in the first environment and carries that account forward. The `environment_complete` record is the substrate boundary between one developmental episode and the next. The programme now has, for the first time, a substrate record that one complete developmental arc occurred and another is beginning.

**The through-line closes.** The SICC v0.6 states it directly: *v1.8 gives the agent a reason to learn. v1.9 gives it a record of choosing. v1.10 gives it a record of being wrong and changing. v1.11 gives it a record of understanding why.* Together these four iterations move the programme from an agent that describes its history to an agent that owns it. The entity question — at what point does this agent have a sense of self? — is not answered by any single result. It is answered by the accumulation across these four iterations: an agent that had goals and failed at some of them, that held back when it judged itself unready, that changed its beliefs when the world contradicted them, and that can explain why its arc took the shape it did. v1.11 is the iteration where that question becomes fully empirical.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed before any v1.11 implementation begins.

**Diagnostic-first protocol.** Before writing `V111CausalObserver`, `diagnose_bundle_fields.py` confirms the exact field names and record structures of all five substrate fields. This is the v1.10 lesson applied prospectively: three amendments consumed on interface mismatches against a single function. The diagnostic script costs one pre-flight step and saves the amendment budget for genuine architectural decisions.

**Matched-seed comparison.** Seeds from `run_data_v1_10_1.csv` at matched (cost, run_idx) cells. Fallback to `run_data_v1_9.csv` if key format differs — inspect seed field names before committing.

**Pre-flight verifications.** Level 12 re-run passes before Level 13. Level 13 passes before full batch.

**Single-architectural-extension discipline.** `V111CausalObserver` and the next-environment batch runner extension are counted as one architectural extension because they share the `environment_complete` trigger and both read from the same assembled bundle. If the next-environment architecture is excluded under the conditionality clause (Section 2.4), `V111CausalObserver` alone constitutes the iteration's architectural addition.

**Parameter commitments.** `chain_depth_minimum = 2`, `seed_env2_offset = 10000` — committed here, not free parameters. All v1.10 parameters (`POSITIVE_APPROACH_BIAS`, `BIAS_DURATION`, `BIAS_DECAY`, `END_STATE_DRAW`, `K_EXCLUSION`) inherited unchanged.

**Amendment policy.** Three amendments available. Most likely candidates: (1) extended step count to 500,000 if `environment_complete` fires in fewer than 20% of pre-flight runs; (2) interface correction in `V111CausalObserver` against bundle field names (the diagnostic script reduces but does not eliminate this risk); (3) causal chain construction logic if a link type is structurally unavailable from the assembled bundle as specified. The amendment budget is not expected to be consumed on the same function three times; the diagnostic-first protocol is the preventive measure.

**Public record.** Committed to github.com/RancidShack/developmental-agent on 4 May 2026, before any v1.11 code is written.

---

## 9. Stopping rule

The v1.11 iteration completes when:

- Level 12 re-run passes on the v1.11 stack with `--no-causal`.
- Level 13 passes across all eight criteria.
- The full 40-run batch has run.
- Categories α, β, γ, δ, Φ, ζ, η, θ, Σ, Λ (if n ≥ 8), and Ω have been characterised in the v1.11 paper.
- The v1.11 paper is drafted.

---

## 10. New files required

- `v1_11_causal_observer.py` — `V111CausalObserver`: post-run observer; `build_causal_chains()` reading from assembled bundle; `causal_chain` record construction; `get_substrate()`; `--no-causal` flag support
- `v1_11_observer_substrates.py` — monkey-patches `SubstrateBundle.__init__`, `resolve()`, `build_bundle_from_observers()` with `causal` field; extends `V16ReportingLayer` with `query_why_arc()`; imports v1.10 patches first
- `curiosity_agent_v1_11_batch.py` — batch runner with causal observer and next-environment architecture; `--no-causal` flag; second-environment instantiation on `environment_complete`; flushes to `causal_v1_11.csv`, `env2_run_data_v1_11.csv`
- `verify_v1_11_level13.py` — Level 13 pre-flight: eight correctness criteria across 10 runs at cost=1.0, 80,000 steps
- `diagnose_bundle_fields.py` — pre-implementation diagnostic: prints field names, record types, and sample record structures for all five bundle fields the causal observer reads from

---

## 11. Open questions resolved at pre-registration

The carry-forward note identified five open questions. Each is resolved here.

**1. Step count.** v1.11 runs at 320,000 steps, consistent with v1.9 and v1.10. An extension to 500,000 is available as Amendment 1 if the pre-flight shows `environment_complete` firing in fewer than 20% of runs (8/40). The Montessori principle is preserved: time is not a boundary, and the 500,000-step extension is an expansion of the window, not a simplification of the developmental sequence.

**2. Minimum causal chain length.** `chain_depth ≥ 2` is the minimum for a valid Q5 output. A single-link chain (surprise record only) is a Q1 restatement. The preferred depth is 3 (surprise + precondition + mastery formation, the core causal structure the SICC specifies). Depth 1 chains are recorded but excluded from Category Σ Component 1 counting.

**3. Next-environment seed strategy.** Deterministic derived seed: `seed_env2 = seed_env1 + 10000`. Reproducible and agent-specific (two runs with the same env1 seed always produce the same env2 environment). Committed here.

**4. V111CausalObserver placement.** Observer pattern, not reporting-layer extension only. The advantage of the observer pattern — `--no-causal` flag for regression testing, additive discipline preserved, inheritance chain explicit — outweighs the implementation cost. The observer runs post-simulation on the assembled bundle; it does not add per-step overhead.

**5. Category Ω human-readability criterion.** Assessed qualitatively in the paper: two sample Q5 outputs (one low-individuation, one high-individuation run) included in Section 3, inviting the reader to test the criterion. This is not automatable; the paper is the vehicle.

---

## 12. References

Baker, N.P.M. (2026ae–al) Prior preprints and pre-registrations v1.6–v1.8. See v1.9 reference list.

Baker, N.P.M. (2026am) 'v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026an) 'v1.9.1 Pre-Registration Amendment: Detection Threshold Reduction', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ao) 'Counterfactual Record and Suppressed Approach in a Small Artificial Learner: The Register of What Was Not Done', preprint, 4 May 2026.

Baker, N.P.M. (2026ap) 'v1.10 Pre-Registration: Belief Revision with Consequences and the Completion Signal', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aq) 'v1.10.1 Pre-Registration Amendment: ProvenanceStore Agent Attribute Name', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ar) 'v1.10.2 Pre-Registration Amendment: ProvenanceStore Record Storage Attribute', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026as) 'v1.10.3 Pre-Registration Amendment: ProvenanceRecord Dataclass Required', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026at) 'Belief Revision with Consequences in a Small Artificial Learner: The Record of Being Wrong and Changing', preprint, 4 May 2026.

Baker, N.P.M. (2026au) 'v1.11 Pre-Registration: Causal Self-Explanation and the Next-Environment Architecture', GitHub repository, 4 May 2026.

Baker, N.P.M. (internal record, v0.6 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
