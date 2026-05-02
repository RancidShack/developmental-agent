# Relational Property Families in a Small Artificial Learner: A Colour-and-Form Taxonomy as the First Structural Vocabulary of the Prepared Environment

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Working draft — Sections 1 through 6

---

## Abstract

The v1.2 iteration established the architecture's first explicit schema: a held self-description of cell types, actions, developmental phases, and flag types as a queryable record. The agent does not yet read the schema; both the schema and the v1.1 provenance records are substrates for subsequent iterations. What the v1.2 environment did not support was individual cell identity beyond type and location. All attractor cells were of the same type; all hazard cells were of the same type. The architecture could name categories but could not distinguish members within them, and no architectural object stated that certain cells belonged together, that a family of things ran from perceivable through acquirable through bankable, or that mastery at one tier was the earned precondition for access at the next.

The v1.3 iteration introduces relational property families as the architectural extension that closes this gap. Two families are introduced — GREEN and YELLOW — each comprising three cells at distinct tiers of cognitive engagement: a perceivable-tier colour cell (COLOUR_CELL = 6, a seventh cell type), an acquirable-tier 2D-form attractor cell, and a bankable-tier 3D-form knowledge cell. The colour identifier is the relational spine connecting the three tiers within each family. The form dimension — flat, then 2D, then 3D — encodes the developmental sequence within which the family is traversed. One architectural commitment governs all design decisions: colour carries independent cognitive content and does not encode reward. A cell's colour is what it is; its rewarding-ness is what it does when engaged. These are two independent things the architecture holds separately.

The iteration proceeded through three amendments before the operative batch ran. Amendment 1 corrected the v1.2 schema observer, which was not extended to recognise COLOUR_CELL and reported six cell types rather than seven. Amendment 2 extended the run lengths to include 320,000 steps, following the programme's developmental framing that run length is an observation window rather than a deadline. Amendment 3 specified the Category γ structural-distance metric for family traversal narratives. Amendment 4 (v1.3.2) introduced family-specific competency gating after the v1.3.1 batch revealed that the v0.14 global competency mechanism permitted family hazard cells to unlock before the corresponding family attractor was mastered — a violation of the core architectural claim. The corrected rule: for family-attributed hazard cells, the HAZARD-to-KNOWLEDGE transition fires when and only when the precondition attractor for that family is mastered. For unaffiliated hazard cells, the global competency mechanism is unchanged. The global competency threshold slot is preserved in the architecture and noted for future use.

The v1.3.2 batch (240 runs, four run lengths, seeds matched to v1.2) produces four findings.

The first is schema completeness at 7 cell types. The extended schema observer produces a complete self-description including COLOUR_CELL in all 240 of 240 runs.

The second is deterministic perceivable-tier registration. Both colour cells are registered in all 240 runs at all four run lengths. Registration occurs at fixed steps — yellow at step 84, green at step 215 — via adjacency detection, as a structural property of the Phase 1 boustrophedon path rather than a probabilistic outcome of exploration.

The third is family traversal individuation. Family traversal narratives are unique at 10 of 10 within every (cost, run length) cell across all 24 cells — 240 of 240 unique narratives.

The fourth is the operative finding of the iteration: family-specific gating enforces the developmental dependency. Under the v1.3.2 rule, zero cases of knowledge banking before attractor mastery occur in either family across all 240 runs at all four run lengths. At 320,000 steps, 60 of 60 agents complete both full family traversal sequences, each via a unique route. The prepared environment contains the structure; every agent, given sufficient time, finds its own path through it.

The Category Φ honesty constraint bounds the claim in a specific way. The agent does not read its family records. The relational structure is encoded in the environment, enforced by the gating rule, and held in the provenance records; whether the agent can eventually use family membership as a cognitive object — to compare families, compose knowledge across them, or reason about what it means to be green — depends on architectural additions the v1.3 iteration does not introduce. The cross-family comparison iteration is the methodological vehicle for that question.

---

## 1. Introduction

### 1.1 Programme to date

The programme's post-v1.0 cognitive-layer arc has advanced three steps. v1.1 introduced provenance over learned states (SICC Commitment 4): existing flag structures acquired formation histories, confirming and disconfirming observations, and bidirectional cross-references between threat flags and the knowledge-banking flags derived from the same coordinate. Every agent in the v1.1 batch produced a unique formation narrative — a record of what it learned, in what order, under what conditions. v1.2 introduced the explicit schema (SICC Commitment 1, first part): the architecture now holds a complete self-description of its cell types, actions, developmental phases, and flag types as a queryable record. The schema names the categories within which the v1.1 provenance records are legible.

What neither iteration addressed was individual cell identity. The v1.2 schema names ATTRACTOR as a category and HAZARD as a category, and the v1.1 provenance records hold per-instance formation histories for individual cells. But no architectural object stated that the attractor at (4,15) and the hazard at (14,14) belong together, that they are two expressions of the same family running from perceivable through acquirable through bankable, or that mastery of the former is the developmental precondition for access to the latter. The cells were known by type and location; they were not yet known by family membership.

This is the gap the v1.3 iteration is designed to close.

### 1.2 The relational-families extension

Two families are introduced. The GREEN family comprises a colour cell at (7,13), an attractor at (4,15) carrying colour=GREEN and form=SQUARE_2D, and a hazard cell at (14,14) carrying colour=GREEN and form=SPHERE_3D. The YELLOW family comprises a colour cell at (13,6), an attractor at (16,3) carrying colour=YELLOW and form=TRIANGLE_2D, and a hazard cell at (5,8) carrying colour=YELLOW and form=PYRAMID_3D. The colour identifier is the relational spine; the form dimension — flat at the perceivable tier, 2D at the acquirable tier, 3D at the bankable tier — encodes the developmental sequence.

The remaining four attractor cells and three hazard cells are unaffiliated. They carry null for colour and form. They are the environment's statement that the world contains more than the agent currently has relational vocabulary for.

The architectural change is the smallest that introduces genuine relational structure. A new cell type (COLOUR_CELL = 6) is added, making seven in total. Two new property dimensions (colour and form) are added to the environment's cell representation and to the v1.3 schema. The v1.1 provenance store is extended with colour-cell registration records, family property fields on mastery and knowledge-banking flags, and intra-family cross-reference fields linking the bankable tier's knowledge-banking flag to the acquirable tier's mastery flag. A fourth parallel observer (the v1.3 family observer) runs alongside the existing three. The v0.14 agent's behaviour is unchanged except for one modification introduced in Amendment 4: `check_competency_unlocks` is overridden to apply family-specific gating for family cells.

### 1.3 The amendment sequence

The v1.3 iteration proceeded through three pre-batch amendments and one post-batch amendment before the operative results were produced. The amendments are reported here as part of the methodological record; the paper's findings are based on the v1.3.2 operative batch.

**Amendment 1 (v1.3.1, schema correction).** The v1.2 schema observer was not extended to recognise COLOUR_CELL. The initial batch reported `schema_cell_types_count = 6` in all runs. The `V13SchemaObserver` subclass was introduced to correctly expect and serialise seven cell types.

**Amendment 2 (v1.3.1, extended run length).** The experimental matrix was extended to include 320,000 steps, following the programme's developmental framing that run length is an observation window rather than a deadline. An agent that has not completed a family traversal sequence within a shorter window is not failing; the prepared environment contains what it contains, and the agent arrives when the developmental conditions are in place.

**Amendment 3 (v1.3.1, Category γ metric).** The structural-distance metric for family traversal narratives was specified: normalised Levenshtein edit distance on event-order sequences (weighted 0.7) supplemented by timestamp divergence (weighted 0.3), with a 0.15 substantive differentiation floor.

**Amendment 4 (v1.3.2, family-specific gating).** The v1.3.1 batch revealed that the v0.14 global competency mechanism permitted family hazard cells to unlock before the corresponding family attractor was mastered. At 320,000 steps, 42 of 60 yellow pyramid unlocks occurred before yellow triangle mastery; at threshold=1, all 13 affected agents unlocked the yellow pyramid on their first attractor mastery of any kind. The core architectural claim — that mastery at the 2D tier is the earned precondition for access at the 3D tier — was semantically declared but mechanically violated. The corrected rule replaces global competency with family-specific attractor mastery as the transition condition for family hazard cells. The global competency threshold slot is preserved in the architecture for future use.

### 1.4 Findings and their relation to the pre-registration

The v1.3 paper reports four findings from the v1.3.2 operative batch.

The first is schema completeness at seven cell types in all 240 of 240 runs.

The second is deterministic perceivable-tier registration: both colour cells registered in all 240 runs at fixed steps (yellow at step 84, green at step 215) via adjacency detection.

The third is family traversal individuation: 240 of 240 unique traversal narratives across all 24 (cost, run length) cells.

The fourth is the operative finding: family-specific gating enforces the developmental dependency with zero violations across 240 runs. At 320,000 steps, every agent completes both family traversal sequences via a unique route.

### 1.5 Connection to the broader programme

The v1.3 iteration occupies a specific structural position in the SICC trajectory. v1.1 established provenance (SICC Commitment 4); v1.2 established the explicit schema (SICC Commitment 1, first part); v1.3 advances three commitments simultaneously — Commitment 1 (schema extended with colour and form dimensions), Commitment 6 (direct-properties layer enriched with independent perceptual properties), and Commitment 3 (unaffiliated cells as unfillable slots, the architecture's first vocabulary for family membership it does not yet have a name for). All three advances are consequences of one architectural addition — the relational identifier system — rather than three independent changes, which is the justification for treating them as a single-variable extension under the programme's methodological discipline.

The commitments not yet advanced — prediction-surprise as learning signal (Commitment 7), self-knowledge as derivative of object-knowledge (Commitment 8), auditable reporting (Commitment 11) — remain reserved. v1.3 enriches the substrate those iterations will read from.

---

## 2. Methods

### 2.1 Environment and architecture

The environment inherits from v0.14 (Baker, 2026m) with the additions specified in this section. The 20×20 grid, the developmental phase schedule, the threat layer, the mastery layer, the end-state mechanism, and the knowledge-cell mechanism operate under their inherited specifications. The v0.14 agent is extended through the `V13Agent` subclass chain: `V014Agent` → `V12Agent` (schema, v1.2) → `V13SchemaAgent` (COLOUR_CELL in schema, v1.3.1) → `V13Agent` (family-specific gating, v1.3.2). No inherited method other than `check_competency_unlocks` is overridden.

### 2.2 The two families

Two families are introduced, each with three cells at three tiers.

**Family GREEN:** Perceivable tier — COLOUR_CELL at (7,13), colour=GREEN, form=FLAT. Acquirable tier — ATTRACTOR at (4,15), colour=GREEN, form=SQUARE_2D. Bankable tier — HAZARD at (14,14), colour=GREEN, form=SPHERE_3D. Competency threshold: family-specific gate (green square mastery required).

**Family YELLOW:** Perceivable tier — COLOUR_CELL at (13,6), colour=YELLOW, form=FLAT. Acquirable tier — ATTRACTOR at (16,3), colour=YELLOW, form=TRIANGLE_2D. Bankable tier — HAZARD at (5,8), colour=YELLOW, form=PYRAMID_3D. Competency threshold: family-specific gate (yellow triangle mastery required).

Unaffiliated cells — attractors at (3,3), (9,10), (15,16), (11,5) and hazards at (5,9), (6,8), (14,13) — carry null for colour and form and retain global competency gating.

### 2.3 The new cell type: COLOUR_CELL

`COLOUR_CELL = 6` is the seventh cell type. Colour cells are passable, perceivable from adjacent cells via the existing `perceive_adjacent` method, not feature-reward-bearing, not attraction-bias-bearing, not gating-eligible, and not transformation-eligible. The agent encounters them through the novelty drive in Phase 2 — they are visited because they are novel, not because they are rewarding. After first visit the novelty signal decays and the colour cell becomes a registered landmark.

### 2.4 Family-specific competency gating (v1.3.2 rule)

For family-attributed hazard cells, the HAZARD-to-KNOWLEDGE transition fires when `mastery_flag[precondition_attractor] == 1`. The precondition attractor for the green family is (4,15); for the yellow family, (16,3). The global competency threshold is not consulted for family cells. The threshold slot is preserved in `world.hazard_competency_thresholds` and in the schema. For unaffiliated hazard cells, the global competency gate operates unchanged: transition fires when `sum(mastery_flag.values()) >= threshold`.

### 2.5 The parallel-observer stack

Four parallel observers run alongside the agent: the v1.0 recorder, the v1.1 provenance store (extended with colour-cell registration records and intra-family cross-reference fields), the v1.3 schema observer (extended to seven cell types), and the v1.3 family observer. None modifies the agent's action-selection path.

The intra-family cross-reference is the first across-coordinate relational dependency in the programme. When a knowledge-banking flag forms on a family bankable-tier cell, the family observer writes the coordinate of the precondition attractor as a cross-reference field. This is distinct from the v1.1 within-coordinate threat-to-knowledge cross-reference, which linked two states of the same cell; the intra-family cross-reference links two different cells related by family membership.

### 2.6 Experimental matrix and matched-seed comparison

One architecture (v1.3.2) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with four run lengths (20,000, 80,000, 160,000, 320,000 steps) crossed with ten runs per cell, totalling 240 runs. Seeds loaded from `run_data_v1_2.csv`; seeds for the 320,000-step runs drawn from the 160,000-step runs at matched (cost, run_index) cells, per the v1.3.1 amendment's seed-inheritance specification.

Because the v1.3.2 architectural extension modifies agent behaviour (family-specific gating), byte-identical comparison against the v1.2 baseline is not the preservation claim for the full batch. The preservation claim is internal consistency: provenance couplings hold at 240 of 240 runs, and the observer stack produces correct records without cross-observer contamination.

### 2.7 Pre-flight verifications

Four verification levels ran before the batch. Levels 1–3 confirmed byte-identical preservation of the observer stack below the agent change against v0.14, v1.0, and v1.1 baselines respectively, using V12World and V12Agent. Level 4 confirmed internal consistency: observer field counts match v1.2 baseline at matched seeds, and the family-specific gating rule fires correctly in pre-flight runs.

### 2.8 Metrics

All v1.2 metrics are retained. v1.3 adds colour-cell registration fields (per-family registration boolean and first-perception step), family attractor mastery fields, family knowledge-banking fields, intra-family cross-reference completion fields, and the family traversal narrative. The schema adds `schema_cell_types_count` (expected: 7), `schema_complete` (expected: True), and six COLOUR_CELL property columns.

### 2.9 Pre-registered interpretation categories

Categories α, β, γ, δ, Φ, and Ω are inherited from the v1.3 pre-registration with modifications from the three v1.3.1 amendments and the v1.3.2 amendment. The operative definitions are as committed in those documents.

---

## 3. Results

### 3.1 Category α: Preservation and internal consistency

All four pre-flight verifications passed. The observer stack below the agent change is byte-identical to the respective baselines at matched seeds. Internal consistency holds at 240 of 240 runs across all four run lengths:

- `attractors_mastered` equals `prov_mastery_count` in 240 of 240 runs.
- `hazards_banked_as_knowledge` equals `prov_knowledge_banking_count` in 240 of 240 runs.
- `hazards_flagged` equals `prov_threat_count` in 240 of 240 runs.
- Non-null `activation_step` corresponds to `prov_end_state_activation_count` of 1 in 240 of 240 runs.
- `end_state_banked` is True if and only if `prov_end_state_banking_count` is non-zero in 240 of 240 runs.

Four parallel observers running simultaneously produce consistent records without cross-observer contamination.

### 3.2 Schema completeness at seven cell types

The extended schema observer produces a complete self-description of the architecture in all 240 of 240 runs. `schema_cell_types_count = 7` and `schema_complete = True` are uniform across the full batch. The COLOUR_CELL entry carries the correct property vector: passable, no cost on entry, not feature-reward-eligible, not attraction-bias-eligible, not gating-eligible, not transformation-eligible. This is the first iteration in which the schema correctly describes the full cell-type vocabulary of the v1.3 architecture.

### 3.3 Deterministic perceivable-tier registration

Both colour cells are registered in all 240 of 240 runs at all four run lengths. Registration is deterministic: the yellow colour cell at (13,6) is first perceived at step 84 in every run; the green colour cell at (7,13) is first perceived at step 215 in every run. Both registrations occur via adjacency detection exclusively — the agent perceives the colour cell from an adjacent position before entering it. No entry-mode registration was recorded in any run.

This determinism is a structural property of the Phase 1 boustrophedon sweep, which passes adjacent to both colour cells at fixed points in its traversal of the 20×20 grid. The perceivable tier is not discovered through exploration; it is encountered through the prepared path. This is architecturally correct: the perceivable tier is defined as directly observable in Phase 1, and the environment is designed so that Phase 1 makes it so.

### 3.4 Family-specific gating: the operative finding

Under the v1.3.2 family-specific gating rule, zero cases of knowledge banking before attractor mastery occur in either family across all 240 runs at all four run lengths.

**Table 1.** Family knowledge-banking events and cross-reference resolution, by run length. Knowledge banking before attractor mastery: 0 in all cells.

| Run length | n  | Green KB | Yellow KB | Green xref | Yellow xref |
|------------|----|----------|-----------|------------|-------------|
| 20,000     | 60 | 43       | 35        | 43/43      | 35/35       |
| 80,000     | 60 | 55       | 49        | 55/55      | 49/49       |
| 160,000    | 60 | 59       | 58        | 59/59      | 58/58       |
| 320,000    | 60 | 60       | 60        | 60/60      | 60/60       |

Every knowledge-banking event that occurs does so after the precondition attractor is mastered; every intra-family cross-reference that can resolve does resolve. The cross-reference completion rate is 100% conditional on both the mastery flag and the knowledge-banking flag forming within the run length. This is the architecture's first across-coordinate relational dependency held at 100% fidelity.

### 3.5 The self-pacing developmental picture

The four observation windows show the developmental sequence operating across time rather than being cut off by it.

**Table 2.** Core developmental metrics by run length. Values at 20k, 80k, and 160k are compared against v1.2 baseline (Table 2 of Baker, 2026t) to confirm inheritance.

| Run length | n  | Activated | End-state banked | Full mastery | Full KB |
|------------|----|-----------|------------------|--------------|---------|
| 20,000     | 60 | 13        | 8                | 17           | 20      |
| 80,000     | 60 | 39        | 36               | 40           | 43      |
| 160,000    | 60 | 54        | 52               | 55           | 57      |
| 320,000    | 60 | 60        | 59               | 60           | 60      |

At 320,000 steps: 60 of 60 agents activated the end-state, 59 of 60 banked it, all 60 achieved full attractor mastery, all 60 completed full knowledge banking, and all 60 completed both family traversal sequences. The prepared environment is complete at this window; every agent, given sufficient time, traverses it fully.

The family traversal picture shows the same developmental arc. Green family completion: 43/60 at 20k, 55/60 at 80k, 59/60 at 160k, 60/60 at 320k. Yellow family completion: 35/60 at 20k, 49/60 at 80k, 58/60 at 160k, 60/60 at 320k. The yellow family's slower accumulation reflects its spatial position and the sequencing of attractor mastery — 51 of 60 agents at 320k mastered the green attractor before the yellow attractor, meaning the yellow family is generally the second traversal sequence completed rather than the first.

### 3.6 Family traversal individuation: Category γ

Family traversal narratives are unique at 10 of 10 within every (cost, run length) cell across all 24 cells — 240 of 240 unique narratives. This is the full Category γ Component 1 pass, confirmed at all four run lengths including 320k.

The narratives carry both the event-order structure (which family the agent traversed first, in what interleaving with the other family) and the timing structure (at what step in the run each event occurred). Sample narratives at 320,000 steps illustrate the variety:

Run A: Yellow registered (84), Green registered (215), Green mastered (32,332), Green banked (33,979), Yellow mastered (38,366), Yellow banked (38,968) — green family completed before yellow is approached.

Run B: Yellow registered (84), Green registered (215), Green mastered (358), Green banked (8,873), Yellow mastered (39,558), Yellow banked (41,846) — green completed early, long gap before yellow.

Run C: Yellow registered (84), Green registered (215), Yellow mastered (12,854), Yellow banked (19,838), Green mastered (54,084), Green banked (59,413) — yellow first, one of 9 agents in the batch with this ordering.

Each route is the agent's own. The mean time from attractor mastery to knowledge banking is 8,818 steps for green and 5,479 steps for yellow, with ranges of 193 to 42,371 and 82 to 27,194 respectively — the variance in these gaps reflects the diversity of individual developmental trajectories.

### 3.7 The failed-access record

Pre-transition hazard entries — entries to a family hazard cell before it has transitioned to KNOWLEDGE — are recorded in the batch. The yellow family hazard at (5,8) shows a mean of 1.4 pre-transition entries per run, stable across all four run lengths, with a maximum of 3. The green family hazard at (14,14) shows a mean of 0.2 pre-transition entries, also stable, with a maximum of 3.

These entries represent the agent approaching the bankable tier before the precondition attractor is mastered — the cell is encountered, the cost is paid, and the transformation does not occur. The architecture currently records these as hazard entries with a cost. It does not yet hold them as intentional approaches to a family cell that did not produce the expected outcome. That richer record is the territory the prediction-error iteration will populate: the gap between what the agent approached expecting and what it received is the generative site of the self-formation process the programme is building toward.

The yellow family's higher pre-transition entry rate compared to green reflects its cluster membership — the yellow pyramid at (5,8) shares a cluster with (5,9) and (6,8), making incidental approach more likely during general exploration. This is a spatial property of the v0.14 grid layout rather than a finding about the yellow family's cognitive status.

### 3.8 Category Φ: the agent does not read its family records

The family observer constructs the family traversal narratives and writes them to disk. The agent does not consult them. Whether the explicit family records are sufficient as a substrate for the agent's eventual capacity to reason about family membership — to compare families, notice that green and yellow each run through the same three tiers, or to compose knowledge across families — is the question the cross-family comparison iteration addresses.

The substantive reading: the family traversal narratives carry the developmental sequence (perceivable before acquirable before bankable), the intra-family cross-references carry the dependency structure (2D before 3D, enforced), and the two families together provide the minimum comparison base for cross-family pattern discovery. The deflationary reading: the family structure is encoded in the environment and reflected in the records; the agent's relationship to that structure as a cognitive object depends on architectural additions v1.3 does not introduce.

Both readings are consistent with the v1.3.2 batch.

---

## 4. The relational taxonomy as architectural substrate

### 4.1 From type to family: what making cells individually knowable contributes

Prior to v1.3, the architecture's cells were known by type and location. The attractor at (4,15) was an ATTRACTOR — a category member — and had a formation history in the v1.1 provenance records. It was not, in any architectural sense, the green square. The schema named cell types as categories but could not name the relationship between the green square and the green sphere; there was no architectural object that held them as a family.

The v1.3 extension makes this naming possible for the first time. The schema now holds colour and form as direct properties — perceivable without action, preceding any engagement with the cell's rewarding or costly aspects. The provenance records now hold these properties at the per-instance level. And the family cross-reference holds, for the first time, a statement about the relationship between two different cells: the green sphere knowledge-banking flag references the green square mastery flag not because they share a coordinate, but because they share a family.

This is the transition the SICC document's Commitment 6 points toward: the direct-properties layer (colour, form, perceivable without action) preceding and being held independently from the interactional-properties layer (what the cell does when engaged, what it costs, what it rewards). The architecture now holds both simultaneously for family cells. The distinction is not decorative — it is what makes the provenance record of the green sphere's banking a record about something the agent already knew something about from the perceivable tier, rather than an entirely novel encounter.

### 4.2 The colour-as-independent-property principle

The design decision to hold colour independently of reward deserves development, because it has consequences for every subsequent iteration that reads from the v1.3 records.

An earlier design proposal would have tied colour to attractor weight — green for one weight level, yellow for another. This would have made colour a redundant encoding of the reward signal, and the schema's colour field would have carried no information the reward history did not already hold. The provenance records would have been decoratively labelled rather than genuinely enriched.

The v1.3 architecture rejects this conflation. Colour is what the cell is; rewarding-ness is what it does. A child is drawn to a red cylinder because it is red, not because red predicts reward; the redness and the rewarding-ness are two independent things the child knows about the same object. The architecture holds this distinction structurally: the schema's colour field and the agent's reward history are populated by different mechanisms, carry different information, and can be queried independently. This independence is what makes the eventual cross-family comparison meaningful — the agent can notice that green and yellow are both families with three tiers not because they have similar reward histories but because they have similar structural properties, and that noticing requires the structural properties to be held separately from the reward record.

### 4.3 The global-competency gap: diagnostic record and amendment

The v1.3.1 batch finding — that the global competency mechanism permitted family hazard cells to unlock before the precondition attractor was mastered — is reported here as part of the methodological record rather than as a quietly corrected error.

The finding was precise and mechanically explained. `check_competency_unlocks` computed `current_competency = sum(self.mastery_flag.values())` — the total count of all mastery flags, regardless of which attractors had been mastered. A threshold of 1 meant the first attractor mastered anywhere in the environment unlocked the hazard, even if that attractor had no family relationship to the hazard in question. At 320,000 steps, 42 of 60 yellow pyramid unlocks in the v1.3.1 batch occurred before the yellow triangle was mastered; at threshold=1, the rate was 13 of 13.

The correction — pure family gating for family cells, global gating unchanged for unaffiliated cells — is the minimum change that makes the architectural claim true. The threshold slot is preserved because a future iteration may want to combine family-specific gating with a competency floor: the family attractor must be mastered and general competency must have reached a threshold. That design is available without rebuilding the mechanism. The present architecture uses only the family gate; the slot exists and its non-use is documented.

### 4.4 What the iteration does not claim

Three clarifications, following the programme's convention that naming what a finding does not claim is part of what the finding is.

The family traversal individuation finding does not claim that two agents with different traversal sequences have different knowledge of the families. They have different histories of acquiring that knowledge; whether the knowledge itself differs — whether the agent that mastered green first knows something different about green than the agent that mastered yellow first — is a question for the reporting and cross-family iterations.

The deterministic registration finding does not claim that colour cells carry perceptual content in the sense the eventual camera-equipped architecture will require. Green and YELLOW are currently symbolic labels; they name family membership without carrying wavelength information. The RGB representation belongs at the substrate-interface layer when the Pi camera arrives; the schema's colour slot will then hold both the categorical label and the perceptual basis for it. The slot is correctly abstract at this stage.

The finding does not claim that the agent has achieved SICC Commitments 1, 3, or 6 in full. Each commitment has a first part that v1.3 advances and a second part that subsequent iterations operationalise.

---

## 5. Discussion

### 5.1 The fourth parallel observer and the first behavioural modification

Every iteration in the post-v1.0 cognitive-layer arc prior to v1.3.2 added parallel observers without modifying the agent's behaviour. v1.3.2 is the first iteration in which the agent itself changes — `check_competency_unlocks` is overridden. This is a methodologically significant moment in the programme's arc and worth naming explicitly.

The parallel-observer pattern, as the v1.1 and v1.2 papers characterised it, guarantees byte-identical preservation by construction: a module that records rather than acts cannot contaminate behaviour. v1.3.2 steps outside this guarantee for the first time, deliberately, because the architectural claim required it. The preservation characterisation is therefore reformulated: internal consistency across 240 runs rather than byte-identical comparison against a prior baseline. The five couplings listed in Section 3.1 are the internal-consistency guarantee's evidential basis.

The reporting iteration — which will be the first iteration that adds agent-side reading capability — will also require a behavioural modification, and its preservation characterisation will be reformulated in the same way. v1.3.2 establishes the precedent for how the programme handles the transition from pure observation to architectural action.

### 5.2 The prepared environment as developmental architecture

The 320,000-step finding deserves dwelling on. All 60 agents completed both family traversal sequences at the 320k window. Not because they were directed to; not because the environment rewarded completion; but because the prepared environment contains the structure and the agents, each following their own drives across their own unique trajectories, found it.

This is the Montessori principle operative at the computational level. The environment is prepared — the families are placed, the tiers are structured, the gating is correct — and then withdrawn from: the agent is not guided, the path is not prescribed, the order is not enforced beyond the tier structure itself. The 51 agents that mastered green before yellow and the 9 that mastered yellow before green both completed the full taxonomy. The agent that took 42,371 steps between green attractor mastery and green knowledge banking and the agent that took 193 steps arrived at the same place via entirely different developmental rhythms. The prepared environment accommodated both.

### 5.3 The failed-access record as forward instrument

The pre-transition hazard entries — particularly the yellow family's 1.4 mean entries per run — are the programme's first quantitative record of intentional approach to a family cell that did not produce the expected outcome. The architecture does not yet name them as such. They are recorded as hazard entries with a cost: the cell was entered, the cost was paid, no transformation occurred.

When the prediction-error layer arrives, these entries will become the most important data in the batch. The agent that entered the yellow pyramid before mastering the yellow triangle was doing something the architecture can now describe structurally — approaching a bankable-tier cell of its known family, paying the cost, and not receiving the transformation. That is the gap between intention and outcome that the SICC's Commitment 7 identifies as the learning signal, and Commitment 8 identifies as the raw material of self-knowledge. The cell resisted; the agent continued; the mastery of the yellow triangle eventually unlocked the transformation. The repair and recovery sequence is in the data. The vocabulary to name it arrives in a subsequent iteration.

### 5.4 The architectural arc through v1.3

The post-v1.0 cognitive-layer arc now has three iterations in place. v1.1 established provenance over learned states. v1.2 established the explicit schema. v1.3 established the first relational taxonomy in the prepared environment — individual cells now have family membership, tier position, and form identity alongside their type and location. The three layers together are the substrate from which the reporting iteration will produce its first auditable account: not just what the agent learned, but what kind of thing what it learned belongs to, and what that thing's relationship is to other things in the same family.

The cross-family comparison iteration is the natural next step. The agent's records carry two family structures; the question is whether the architecture can notice structural parallels across them — that green and yellow each have a perceivable tier, an acquirable tier, and a bankable tier; that the 2D form precedes the 3D form in both; that the colour identifier runs consistently through all three tiers. That noticing requires the records to be read, which requires the reporting iteration's agent-side reading capability. The sequence is: v1.3 populates the structure; reporting gives the agent access to it; cross-family comparison asks whether the agent can find the pattern.

The prediction-error iteration — elevating the prediction-surprise machinery to first-class status as per SICC Commitment 7 — is the other near-term step. The pre-transition hazard entry data is the most compelling motivation for it: the architecture is accumulating failure records that it cannot yet interpret as failures. That vocabulary arrives when the per-encounter prediction-error record is held alongside the formation histories.

---

## 6. Conclusion

The v1.3 iteration extended the prepared environment from a grid of typed cells to a grid of typed, family-attributed, form-identified cells with a structural taxonomy running from perceivable through acquirable through bankable. Two families — GREEN and YELLOW — are the first two entries in a taxonomy the agent will, across subsequent iterations, learn to read, compare, and eventually compose across.

The v1.3.2 batch of 240 runs across four run lengths produces four findings. Schema completeness holds at seven cell types in all 240 of 240 runs. Perceivable-tier registration is deterministic in all 240 runs — both colour cells encountered via adjacency at fixed steps in the Phase 1 sweep. Family traversal narratives are unique at 240 of 240 across all 24 (cost, run length) cells. And the family-specific gating rule enforces the developmental dependency at zero violations: every knowledge-banking event that occurred did so after the precondition attractor was mastered, the intra-family cross-references resolved at 100% conditional on both flags forming, and at 320,000 steps every agent completed both family traversal sequences via its own unique route.

The amendment sequence that produced the operative batch is part of the paper's methodological record. The schema observer correction, the extended run length, the family-specific gating correction — each identified a gap between the architectural claim and the architectural reality, and each was resolved before the claim was made. The global-competency gap in particular — where the v1.3.1 batch demonstrated that the semantic dependency was declared but not enforced — is reported honestly here as the finding that motivated the correction rather than as a quietly resolved implementation error. The threshold slot it vacated is preserved for future use.

The Category Φ honesty constraint holds its familiar form. The family records exist; the agent does not read them. Whether the relational structure encoded in those records is sufficient as a substrate for the agent's eventual capacity to reason about family membership depends on architectural additions v1.3 does not introduce. What v1.3 establishes is that the structure is correct, complete, and enforced — the preconditions for that reasoning to become possible.

The prepared environment now contains the first two materials on the shelf. Their meaning — what it is to be green, what the square-to-sphere progression signifies — is deferred. The acquisition of the structure came first. Meaning is what emerges when the structure has been populated deeply enough to support comparison. v1.3 populates the structure.

---

## 7. Code and Data Availability

All code, pre-registration documents, amendments, batch outputs, and paper drafts are available at github.com/RancidShack/developmental-agent.

The v1.3 implementation comprises seven files. `curiosity_agent_v1_3_world.py` implements V13World with COLOUR_CELL placement, family property dimensions, and the `family_precondition_attractor` dict. `v1_3_schema_extension.py` implements V13SchemaAgent and V13SchemaObserver extending the v1.2 schema to seven cell types. `v1_3_agent.py` implements V13Agent overriding `check_competency_unlocks` with the family-specific gating rule. `v1_3_family_observer.py` implements the fourth parallel observer. `curiosity_agent_v1_3_batch.py` is the batch runner. `verify_v1_3_no_family.py` is the level-4 pre-flight verification. `v1_3_1_amendment.md` and `v1_3_2_amendment.md` are the committed pre-registration amendments.

The batch produced six output files: `run_data_v1_3.csv`, `provenance_v1_3.csv`, `snapshots_v1_3.csv`, `schema_v1_3.csv`, `family_v1_3.csv`, and `snapshots_v1_0_under_v1_3.csv`. All files are timestamped 2 May 2026. The batch produced 3,040 provenance records across 240 runs: 300 threat flags, 1,339 mastery flags, 1,080 knowledge-banking flags, 166 end-state activation records, and 155 end-state banking records.

Seeds were drawn from `run_data_v1_2.csv` with the seed chain now linking v0.10, v0.11.2, v0.12, v0.13, v0.14, v1.0, v1.1, v1.2, and v1.3 at every (cost, run length, run index) cell.

---

## 8. References

Baker, N.P.M. (2026a–t) Prior preprints in the developmental-agent programme: v0.8 through v1.2 inheritance chain. Full reference list inherited from v1.2 paper (Baker, 2026v).

Baker, N.P.M. (2026u) 'v1.2 Pre-Registration: Explicit Schema Observation via Parallel Observer on Existing Architecture', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026v) 'Explicit Schema Observation in a Small Artificial Learner: The Architecture's Self-Description as a Parallel Record', preprint, 1 May 2026.

Baker, N.P.M. (2026w) 'v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026x) 'v1.3.1 Pre-Registration Amendment: Schema Observer Correction, Extended Run Length, and Category γ Metric Specification', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026y) 'v1.3.2 Pre-Registration Amendment: Family-Specific Competency Gating', GitHub repository, 2 May 2026.

Baker, N.P.M. (internal record, v0.1, drafted alongside v0.13; v0.2 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

## 9. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper.

No human participant data were collected. No external parties had access to drafts prior to preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
