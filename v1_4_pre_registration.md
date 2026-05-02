# v1.4 Pre-Registration: Cross-Family Structural Comparison via Parallel Observer on Existing Architecture

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.4 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

The v1.3 iteration introduced two relational property families — GREEN and YELLOW — each comprising three cells at three tiers: perceivable (colour cell), acquirable (2D-form attractor), and bankable (3D-form knowledge cell). The family-specific competency gate enforces the developmental dependency: the bankable tier is inaccessible until the acquirable tier is mastered. The v1.3.2 batch confirmed that every agent, given sufficient time, completes both family traversal sequences via a unique route, and that the intra-family cross-references resolve at 100% fidelity conditional on both flags forming within the run.

What the v1.3 architecture does not hold is any structural comparison *between* the two families. The GREEN family's records and the YELLOW family's records exist in parallel but are not related to each other as an architectural object. The architecture knows that the green square and the green sphere belong together; it does not yet know that the green family and the yellow family are structurally parallel — that both run through the same three tiers, that both encode the same flat-to-2D-to-3D progression, that the colour identifier performs the same relational function in both. That pattern is available in the records; nothing in the architecture reads it.

The v1.4 iteration introduces **cross-family structural comparison** as the architectural extension that begins to close this gap. A fifth parallel observer — the v1.4 comparison observer — reads the completed family records at run end and computes structural similarity measures between the two families across three dimensions: tier structure, form progression, and traversal sequence. The comparison observer produces a per-run cross-family comparison record that holds, for the first time, an architectural object representing the relationship between two families rather than the internal structure of one.

This is the SICC document's Commitment 6 relational-properties layer becoming operative. Relational properties require comparison across encounters — sameness of structure across cells, similarity of sequence across families. The comparison observer performs this comparison from the architecture's own records without the agent being directed to perform it, and without modifying the agent's behaviour.

The v1.4 iteration remains a parallel-observer addition. The agent does not read the comparison records. The comparison is performed by an external observer at run end; it is held as a record alongside the family records, the provenance records, and the schema. Whether the agent can eventually use the cross-family comparison as a cognitive object — to notice that green and yellow are instances of a class, to generalise from one family to a new one, to predict the structure of a third family from the pattern of the first two — is the question the reporting iteration addresses. v1.4 establishes that the structural similarity is detectable from the architecture's own records. Detectability is the precondition for the agent's eventual capacity to detect it.

---

## 2. Architectural specification

The v1.4 architecture inherits v1.3.2 unchanged except for the addition of the comparison observer module. The single-variable-change discipline holds: v1.4 introduces cross-family structural comparison as the singular architectural extension.

### 2.1 The comparison observer

The v1.4 comparison observer (`V14ComparisonObserver`) is a fifth parallel observer implementing the same three-hook interface as the existing four. It holds no state during the run — `on_pre_action` and `on_post_event` are no-ops. At `on_run_end`, it reads the completed family records from the v1.3 family observer and computes three structural comparison measures.

**Measure 1: Tier-structure similarity.** For each family, extract the ordered set of tier types traversed within the run (from the family traversal narrative): which of {colour_registered, attractor_mastered, knowledge_banked} events occurred, and in what order. Compute the normalised edit distance between the two families' tier-event sequences, treating each event type as an atomic token. A value of 0 indicates identical tier sequences; a value of 1 indicates maximum dissimilarity. For a run in which both families complete the full three-tier sequence in the same order, this measure is 0.

**Measure 2: Form-progression parallelism.** For each family, the form progression is encoded as a tuple: (perceivable-form, acquirable-form, bankable-form). For GREEN: (FLAT, SQUARE_2D, SPHERE_3D). For YELLOW: (FLAT, TRIANGLE_2D, PYRAMID_3D). The structural similarity of the two progressions is assessed on three binary properties: (a) both perceivable-tier forms are FLAT, (b) both acquirable-tier forms are 2D (SQUARE_2D or TRIANGLE_2D), (c) both bankable-tier forms are 3D (SPHERE_3D or PYRAMID_3D). The form-progression parallelism score is the proportion of these three properties that hold — 0, 0.33, 0.67, or 1.0. Under the present architecture, all three properties hold by design, so this measure is 1.0 in all runs. It is recorded as a structural assertion rather than a variable finding, and its constancy is confirmed as part of Category β.

**Measure 3: Traversal-sequence structural distance.** Using the Category γ metric specified in the v1.3.1 amendment — normalised Levenshtein edit distance on event-order sequences (weighted 0.7) supplemented by timestamp divergence (weighted 0.3) — compute the structural distance between the GREEN family traversal narrative and the YELLOW family traversal narrative within each run. This measure captures how similarly or differently each agent traversed the two families: an agent that mastered green before yellow and banked green before yellow will show a different intra-run cross-family distance from an agent that interleaved the two families closely. The distribution of this measure across the 240-run batch is the primary quantitative finding of the iteration.

### 2.2 The cross-family comparison record

The comparison observer produces one record per run with the following fields:

- `arch`, `hazard_cost`, `num_steps`, `run_idx`, `seed` — run identification
- `tier_structure_similarity` — Measure 1 (normalised edit distance, lower = more similar)
- `form_progression_parallelism` — Measure 2 (proportion of structural properties holding)
- `traversal_sequence_distance` — Measure 3 (cross-family traversal structural distance)
- `green_traversal_complete` — boolean, True if all three GREEN family events occurred
- `yellow_traversal_complete` — boolean, True if all three YELLOW family events occurred
- `both_complete` — boolean, True if both families fully traversed within the run
- `green_first` — boolean, True if the GREEN acquirable tier was mastered before the YELLOW acquirable tier
- `traversal_interleaving` — categorical: `green_then_yellow`, `yellow_then_green`, `interleaved` (where interleaved means the families' events overlap temporally rather than one completing before the other begins)
- `cross_family_comparison_complete` — boolean, True if all three measures are computed

### 2.3 The parallel-observer stack extended to five layers

Five parallel observers run alongside the agent: the v1.0 recorder, the v1.1 provenance store, the v1.3 schema observer, the v1.3 family observer, and the v1.4 comparison observer. The comparison observer reads from the family observer's completed records at `on_run_end`; it does not modify the family observer's state.

With `--no-comparison`, output is byte-identical to v1.3.2 baseline at matched seeds. The comparison observer is the only addition; the agent, world, and all existing observers are inherited unchanged.

### 2.4 What v1.4 does not change

The v0.14 agent, V13World, the four existing observers, the phase schedule, the drive composition, and all inherited architectural elements are preserved unchanged. The family-specific competency gating rule (v1.3.2) is inherited. No flag type is added; no cell type is added; no property dimension is added. The comparison observer reads from completed records; it does not write to the agent's state.

---

## 3. Experimental matrix and matched-seed comparison

The experimental matrix matches v1.3.2: one architecture (v1.4) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with four run lengths (20,000, 80,000, 160,000, 320,000 steps) crossed with ten runs per cell, totalling 240 runs. Seeds loaded from `run_data_v1_3.csv`.

With `--no-comparison`, the v1.4 batch runner produces output byte-identical to v1.3.2 baseline at matched seeds. Category α is operationalised as the level-5 `--no-comparison` regression test.

---

## 4. Pre-flight verifications

Five verification levels are required before the v1.4 batch runs:

**Levels 1–4:** Inherited from v1.3.2 pipeline unchanged.

**Level 5 (v1.3.2 baseline, comparison observer disabled).** With `--no-comparison` only, output matches v1.3.2 baseline byte-for-byte on all v1.3.2 metrics. 10 runs at cost 1.0, 20,000 steps. This is the permanent level-5 regression test added to the pipeline by v1.4.

All five verifications are pre-conditions for the v1.4 batch.

---

## 5. Metrics

All v1.3.2 metrics are retained unchanged. The following metrics are added for v1.4:

**Cross-family structural measures.** Per run: `tier_structure_similarity`, `form_progression_parallelism`, `traversal_sequence_distance` as specified in Section 2.1.

**Traversal completeness and ordering.** Per run: `green_traversal_complete`, `yellow_traversal_complete`, `both_complete`, `green_first`, `traversal_interleaving`.

**Comparison completeness.** Per run: `cross_family_comparison_complete` (boolean).

**Distribution summaries.** Per (cost, run length) cell: mean, standard deviation, minimum, and maximum of `traversal_sequence_distance` across the ten runs. These are the Category γ substrate for the cross-family individuation finding.

---

## 6. Pre-registered interpretation categories

Six interpretation categories are pre-registered.

### 6.1 Category α: Preservation of v1.3.2 architecture under v1.4 extension

With `--no-comparison`, the v1.4 batch runner produces output byte-identical to v1.3.2 baseline at matched seeds on all v1.3.2 metrics. Category α succeeds if all five pre-flight verifications pass.

### 6.2 Category β: Structural comparison resolves correctly

The cross-family comparison record should be internally consistent across all 240 runs:

- `form_progression_parallelism = 1.0` in all 240 runs (both families encode FLAT → 2D → 3D by architectural design).
- `tier_structure_similarity = 0.0` in all runs where both families complete the full three-tier sequence in the same order.
- `cross_family_comparison_complete = True` in all runs where both `green_traversal_complete` and `yellow_traversal_complete` are True.
- The `both_complete` rate at each run length should match the v1.3.2 family completion rates.

Category β succeeds if all four conditions hold.

### 6.3 Category γ: Cross-family traversal individuation

The load-bearing substantive finding of the iteration. Two components:

**Component 1: Intra-run cross-family distance distribution.** The `traversal_sequence_distance` measure should vary meaningfully across the 240 runs — not all agents traverse the two families at equal structural distance from each other. The distribution of intra-run cross-family distances across all runs where both families are complete is the primary quantitative finding. The pre-registered expectation: the distribution has non-trivial variance (standard deviation > 0.10 across the both-complete runs), reflecting genuine individuation in how agents relate to the two families within a single run.

**Component 2: Traversal-interleaving distribution.** The `traversal_interleaving` field captures whether agents traverse the families sequentially or concurrently. The pre-registered expectation based on v1.3.2 data: the large majority of agents traverse green-then-yellow (consistent with the 51/60 green-first finding at 320k), with a minority interleaving or completing yellow first. The distribution should be non-degenerate — at least three runs in each of the three categories across the 320k run length.

Category γ succeeds if Component 1 shows non-trivial variance and Component 2 shows a non-degenerate distribution.

### 6.4 Category δ: Pre-anticipated findings

Two negative findings are anticipated and committed to honest reporting:

**Form-progression parallelism is a structural assertion, not a variable finding.** The v1.4 architecture encodes FLAT → 2D → 3D for both families by design. The `form_progression_parallelism` measure will be 1.0 in all 240 runs. This is reported as a confirmed structural property of the architecture, not as a quantitative finding about agent behaviour.

**Cross-family comparison is incomplete in runs where one or both families are not fully traversed.** At the 20,000-step run length, a proportion of runs will have incomplete family traversal (consistent with the v1.3.2 rates: 43/60 green complete, 35/60 yellow complete). The comparison observer produces partial records in these runs — it computes whatever measures are available from the completed portions of each family's traversal narrative. Partial records are reported honestly with `cross_family_comparison_complete = False`.

### 6.5 Category Φ: Honesty constraint on the cross-family comparison claim

The comparison observer detects structural similarity between the two families from the architecture's own records. Whether this detection constitutes the agent *noticing* the similarity — whether it is available to the agent as a cognitive object that shapes behaviour — depends on architectural additions v1.4 does not introduce.

The substantive reading: the cross-family comparison record establishes that the structural similarity is detectable from the v1.3 records, that it varies across agents in ways reflecting individual traversal patterns, and that it provides the comparison base the reporting iteration needs to produce statements about family-level patterns rather than individual-cell histories.

The deflationary reading: the comparison observer performs the comparison; the agent does not. Whether the agent can eventually use family membership as a generalisation basis — predicting the structure of a third family from the pattern of the first two — depends on the reporting and schema-interrogation iterations.

Both readings are consistent with the v1.4 batch. The reporting iteration is the methodological vehicle for distinguishing them.

### 6.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and γ all pass.

The claim: the structural similarity between the two relational property families introduced in v1.3 is detectable from the architecture's own records without external direction. The comparison observer, reading from completed family traversal records, produces cross-family structural measures that are internally consistent, architecturally correct, and individually variable in ways that reflect each agent's developmental trajectory through the prepared environment. The architecture now holds, for the first time, a record that represents a relationship between two families rather than the internal structure of one.

The deeper claim, reserved: this is the structural substrate for generalisation across families. When the architecture eventually introduces a third family, the comparison record from v1.4 establishes the pattern against which the third family's structure can be compared. Whether the agent can perform that comparison — extending what it knows about green and yellow to a new family it has not yet encountered — is the question the cross-family generalisation iteration addresses.

---

## 7. Connection to the SICC trajectory

v1.4 advances the SICC trajectory on one commitment.

**Commitment 6 (layered property structure)** is advanced at the relational-properties layer. The v1.3 iteration established direct properties for family cells (colour and form, perceivable without action). The v1.4 iteration operationalises the next layer: relational properties, which require comparison across encounters. The comparison observer computes relational properties — structural similarity across families — from the architecture's direct-property records. The temporal-properties layer (how family structure changes across developmental phases, whether agents approach the two families differently in Phase 2 versus Phase 3) remains reserved for a subsequent iteration.

The commitments not yet advanced by v1.4 — prediction-surprise as learning signal (Commitment 7), self-knowledge as derivative of object-knowledge (Commitment 8), auditable reporting (Commitment 11) — remain reserved. The full structure must be in place before the agent is given access to it.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.4 implementation work begins.

**Matched-seed comparison.** Seeds loaded from `run_data_v1_3.csv` at every (cost, run length, run index) cell.

**Pre-flight verifications.** All five levels pass before the full v1.4 batch runs.

**Single-architectural-change discipline.** v1.4 introduces the cross-family comparison observer as the singular architectural extension. The parallel-observer pattern is preserved for a fifth layer.

**Amendment policy.** Three amendments available. No amendment is provisionally reserved at the opening of the iteration; the comparison measures are specified here with sufficient precision that a metric-specification amendment is not anticipated. Two available for unanticipated operational issues; one held in reserve.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before any v1.4 code is written.

---

## 9. Stopping rule

The v1.4 iteration completes when:

- All five pre-flight verifications pass.
- The full 240-run batch has run.
- Categories α, β, γ, δ, Φ, and Ω have been characterised in the v1.4 paper.
- The v1.4 paper is drafted.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve.

---

## 10. References

Baker, N.P.M. (2026a–v) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.2. Full reference list inherited from v1.3 paper.

Baker, N.P.M. (2026w) 'v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026x) 'v1.3.1 Pre-Registration Amendment', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026y) 'v1.3.2 Pre-Registration Amendment: Family-Specific Competency Gating', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026z) 'Relational Property Families in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026aa) 'v1.4 Pre-Registration: Cross-Family Structural Comparison via Parallel Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (internal record, v0.2 current) 'Substrate-Independent Cognitive Commitments'.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before any v1.4 implementation work begins.
