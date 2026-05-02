# v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 1 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.3 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

The v1.2 iteration completed the second phase of the post-v1.0 cognitive-layer arc: the architecture now holds an explicit schema naming its cell types, actions, phases, and flag types as a queryable record alongside the per-instance provenance records v1.1 introduced. The agent does not yet read either layer; both are substrates for subsequent iterations that will add agent-side reading, prediction-and-surprise, and eventually auditable reporting.

What the v1.2 environment does not yet support is **individual cell identity beyond type and location**. All attractor cells are of the same type; all hazard cells are of the same type. The agent's schema names cell types as categories but cannot distinguish members within a category. The provenance records carry formation histories for individual cells but those histories are not linked by any relational structure — there is no architectural object that says these cells belong together, that this family of things runs from perceivable through acquirable through bankable, that mastery at one tier is the earned precondition for access at the next.

The v1.3 iteration introduces **relational property families** as the architectural extension that closes this gap. Two families are introduced — GREEN and YELLOW — each comprising three cells at distinct tiers of cognitive engagement: a perceivable-tier colour cell (directly observable in Phase 1), an acquirable-tier 2D-form attractor cell (weighted, masterable in Phase 2), and a bankable-tier 3D-form knowledge cell (competency-gated, accessible after the corresponding 2D attractor is mastered). The colour identifier is the relational spine that connects the three tiers within each family. The form dimension — 2D preceding 3D — encodes the developmental sequence within which the family is traversed.

This is the first iteration in which the environment itself encodes a taxonomy, and the first in which the agent's provenance records must carry cross-cell relational structure — not just within-cell formation history, but the dependency relationship between cells in the same family. The v1.1 cross-reference between a threat flag and the knowledge-banking flag derived from it was a within-coordinate temporal relationship. The v1.3 cross-reference between the 2D attractor mastery flag and the 3D knowledge-banking flag is an across-coordinate relational dependency, held because one was the earned precondition for the other.

The architectural change is the smallest that introduces genuine relational structure. Two new cell types (COLOUR_CELL and the family-attributed variants of ATTRACTOR and KNOWLEDGE cells), two new property dimensions in the schema (colour and form), two new cross-reference fields in the provenance records, and the family-membership encoding in the environment construction. Everything else inherits from v1.2 unchanged.

One architectural commitment is worth naming explicitly here because it constrains all subsequent design decisions in this iteration and its successors: **colour carries independent cognitive content and does not encode reward**. An earlier design proposal tied colour to attractor weight — green for one weight level, yellow for another — which would have made colour a redundant encoding of the reward signal. That proposal was rejected on the grounds that it conflates two properties the architecture must keep distinct. A cell's colour is what the cell *is*; its rewarding-ness is what the cell *does* when engaged. A child is drawn to a red cylinder because it is red, not because red predicts reward; the redness and the rewarding-ness are two independent things the child knows about the same object. The v1.3 architecture holds this distinction structurally: colour is a direct property perceivable before any engagement, held in provenance independently of the feature-reward history the cell accumulates through interaction. This independence is what makes the provenance records genuinely richer rather than decoratively labelled — the colour field carries information the reward field does not, and vice versa.

The developmental purpose, named explicitly: the prepared environment now contains the first entries in a taxonomy that the agent will, across subsequent iterations, learn to read, compare, and eventually compose across. The two families in v1.3 are the first two materials on the shelf. Their meaning — what it is to be green, what the square-to-sphere progression signifies — is deferred. The acquisition of the structure comes first. Meaning is what emerges when the structure has been populated deeply enough to support comparison. v1.3 populates the structure.

---

## 2. Architectural specification

The v1.3 architecture inherits v1.2 (and through it v1.1, v1.0, and v0.14) unchanged except for the additions specified in this section. The single-variable-change discipline holds at the research-question level: v1.3 introduces relational property families as the singular architectural extension.

### 2.1 The two families

Two families are introduced. Each family has three cells at three tiers:

**Family GREEN:**
- Perceivable tier: one COLOUR_CELL, colour = GREEN, form = FLAT. Location: fixed at a passable neutral coordinate, specified in section 2.3.
- Acquirable tier: one ATTRACTOR cell with family attributes colour = GREEN, form = SQUARE_2D. Assigned to attractor coordinate (4, 15), inherited from the v0.14 attractor set.
- Bankable tier: one hazard cell with family attributes colour = GREEN, form = SPHERE_3D. Assigned to hazard coordinate (14, 14), inherited from the v0.14 hazard set. Competency threshold inherited from the v0.14 permutation for that coordinate.

**Family YELLOW:**
- Perceivable tier: one COLOUR_CELL, colour = YELLOW, form = FLAT. Location: fixed at a passable neutral coordinate, specified in section 2.3.
- Acquirable tier: one ATTRACTOR cell with family attributes colour = YELLOW, form = TRIANGLE_2D. Assigned to attractor coordinate (16, 3), inherited from the v0.14 attractor set.
- Bankable tier: one hazard cell with family attributes colour = YELLOW, form = PYRAMID_3D. Assigned to hazard coordinate (5, 8), inherited from the v0.14 hazard set. Competency threshold inherited from the v0.14 permutation for that coordinate.

The remaining four attractor cells — (3,3), (9,10), (15,16), (11,5) — and the remaining three hazard cells — (5,9), (6,8), (14,13) — are unaffiliated. They carry no colour or form properties. They function exactly as in v1.2. They are the environment's honest statement that the world contains more than the agent currently has relational vocabulary for.

### 2.2 The new cell type: COLOUR_CELL

`COLOUR_CELL = 6` is added to the cell-type constants. Colour cells are:
- Passable. The agent can enter them.
- Perceivable from adjacent cells. The colour and form properties are visible to the agent's `perceive_adjacent` method when the colour cell is adjacent, without requiring entry. This makes colour registration a direct property — observable without action, consistent with SICC Commitment 6's direct-properties layer.
- Not feature-reward-bearing. Entering a colour cell delivers no feature reward. The cell is a perceptual landmark, not a reward source.
- Not attraction-bias-bearing. The primitive attraction bias does not pull toward colour cells.
- Not gating-eligible. The hard-gate action-selection rule does not apply.
- Not transformation-eligible. Colour cells do not transition to another type.

The rationale for passable-but-not-rewarding: the agent can enter colour cells and will register their properties on entry as well as on approach. But the lack of feature reward means the agent is not driven toward them by the feature drive. The novelty drive will draw the agent toward unvisited colour cells during Phase 2 exploration, which is the correct mechanism — the agent visits them because they are novel, not because they are rewarding. After the first visit the novelty signal decays and the colour cell becomes a registered landmark rather than an active target.

### 2.3 Colour cell locations

The two colour cells are placed at fixed coordinates chosen to be spatially distributed across the grid, not adjacent to their family's attractor or hazard cells, and not adjacent to frame cells or other special cells:

- GREEN colour cell: (7, 13)
- YELLOW colour cell: (13, 6)

These coordinates are passable neutral cells in the v0.14 environment. Their placement is fixed rather than randomly sampled, on the methodological principle that the pre-registration commits specific coordinates before implementation begins. If either coordinate is found to be occupied during implementation (due to an error in the coordinate audit), a v1.3.1 amendment specifies the replacement before any batch runs.

### 2.4 New property dimensions: colour and form

Two new property dimensions are added to the environment's cell representation and to the v1.3 schema:

`colour` — a family identifier. Values: GREEN, YELLOW, or null for unaffiliated cells. Set at environment construction time for the six family cells and the two colour cells; null for all other cells.

`form` — a tier-and-shape descriptor. Values: FLAT (colour cells, perceivable tier), SQUARE_2D (green attractor, acquirable tier), TRIANGLE_2D (yellow attractor, acquirable tier), SPHERE_3D (green hazard/knowledge, bankable tier), PYRAMID_3D (yellow hazard/knowledge, bankable tier), or null for unaffiliated cells.

Both dimensions are properties of the environment's cells, held in the world object alongside the existing `cell_type` dictionary. They are perceivable by the agent through the `perceive_adjacent` method, which returns colour and form alongside cell type for any adjacent cell. They are recorded in the v1.3 schema's cell-type property matrix as two additional columns.

### 2.5 The intra-family competency gate

The v0.14 competency-gated transformation mechanism is retained unchanged. The family-membership encoding adds semantic grounding to the gating without modifying its mechanics: the green sphere hazard cell unlocks (transitions to KNOWLEDGE type) when the agent's competency reaches the threshold set for coordinate (14,14) in the v0.14 permutation. The yellow pyramid hazard cell unlocks when the agent's competency reaches the threshold for coordinate (5,8).

What v1.3 adds is the **intra-family dependency record**: at the moment the green sphere transitions to KNOWLEDGE, the v1.3 provenance extension records that this transition is in the same family as the green square attractor, and creates a cross-reference from the knowledge-banking flag that subsequently forms on (14,14) to the mastery flag that formed on (4,15). This cross-reference is an across-coordinate relational dependency — the first of its kind in the programme. It is distinct from the within-coordinate threat-to-knowledge cross-reference v1.1 introduced, which linked two states of the same cell. The intra-family cross-reference links two different cells that belong to the same family.

The architectural reasoning for this cross-reference: the agent's eventual capacity to report on its learning history should be able to say "I mastered the green square before I could access the green sphere — the square was the precondition." That statement requires the provenance records to carry the dependency, not just the individual formation histories. The cross-reference is the architectural substrate for that statement.

### 2.6 Schema additions

The v1.2 schema observer is extended to capture the two new property dimensions. The schema's cell-type property matrix gains two columns: `colour` and `form`. The schema's cell-types count increases from 6 to 7 (the addition of COLOUR_CELL). The schema's flag-types count is unchanged at 4 — no new flag type is introduced for colour-cell perception; the perceivable-tier registration is handled through the provenance extension specified in section 2.7.

The schema now captures, for each cell type, whether it carries colour and form properties and what the valid values are for those properties in the current architecture. COLOUR_CELL cells carry colour (GREEN or YELLOW) and form (FLAT). Family-attributed ATTRACTOR cells carry colour (GREEN or YELLOW) and form (SQUARE_2D or TRIANGLE_2D). Family-attributed KNOWLEDGE cells carry colour and form after transition; the same properties are held on the HAZARD cell before transition. Unaffiliated cells carry null for both dimensions.

### 2.7 Provenance extensions

The v1.1 provenance store is extended with three additions:

**Colour-cell registration records.** When the agent first perceives a colour cell (either on approach via `perceive_adjacent` or on entry), a new record of type `colour_registration` is formed. Fields: `flag_set_step` (the step of first perception), `flag_coord` (the colour cell's coordinate), `colour` (GREEN or YELLOW), `form` (FLAT), `family_attractor_coord` (the coordinate of the family's 2D attractor), `family_knowledge_coord` (the coordinate of the family's 3D knowledge cell). The registration record is the provenance entry for the agent's first awareness of the family's existence at the perceivable tier.

**Family property fields on existing flag types.** Mastery flags and knowledge-banking flags for family-attributed cells gain two additional fields: `cell_colour` and `cell_form`. These are populated at flag formation from the cell's colour and form properties. A mastery flag for the green square attractor carries `cell_colour = GREEN`, `cell_form = SQUARE_2D`. A knowledge-banking flag for the green sphere carries `cell_colour = GREEN`, `cell_form = SPHERE_3D`.

**Intra-family cross-reference fields.** Knowledge-banking flags for family-attributed cells gain a new cross-reference field: `family_2d_mastery_flag_id`. This field is populated when the knowledge-banking flag forms, linking it to the mastery flag of the corresponding 2D attractor in the same family. For the green sphere knowledge-banking flag, `family_2d_mastery_flag_id` references the mastery flag for (4,15). For the yellow pyramid knowledge-banking flag, it references the mastery flag for (16,3). If the corresponding 2D mastery flag does not exist in the records at the moment the 3D knowledge-banking flag forms (which should not occur under the present architecture's competency-gating logic, but is recorded honestly if it does), the field is set to a pending placeholder.

### 2.8 What v1.3 does not change

All architectural elements from v1.2 and the inheritance chain are preserved unchanged. The threat layer, mastery layer, knowledge-banking mechanism, end-state activation mechanism, phase schedule, drive composition, learning rate, discount factor, epsilon, and aversion bias are inherited without modification.

The parallel-observer pattern is preserved: the v1.3 batch runner runs four parallel observers — the v1.0 recorder, the v1.1 provenance store (extended as specified in section 2.7), the v1.2 schema observer (extended as specified in section 2.6), and a new v1.3 family observer that handles colour-cell registration and intra-family cross-reference writing. None of the four observers modifies the agent's behaviour.

The byte-identical preservation property is therefore achievable for a fourth observer layer: with `--no-family` flag suppressing the v1.3 family observer, output matches v1.2 baseline at matched seeds on all v1.2 metrics.

---

## 3. Experimental matrix and matched-seed comparison

The experimental matrix matches v1.2: one architecture (v1.3) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with three run lengths (20,000, 80,000, 160,000 steps) crossed with ten runs per cell, totalling 180 runs.

Seeds are loaded from `run_data_v1_2.csv`. The seed chain now links v0.10, v0.11.2, v0.12, v0.13, v0.14, v1.0, v1.1, v1.2, and v1.3 at every (cost, run length, run index) cell.

Because the v1.3 architectural extension introduces two new cell types and two new perceivable property dimensions, the agent's behaviour under v1.3 will diverge from v1.2 at matched seeds in runs where the agent encounters colour cells or where the family-attributed attractor and hazard cells produce different action-selection behaviour through the novelty drive on first approach. This is expected divergence — the environment is richer, the agent perceives more, the trajectory changes. The preservation audit is therefore population-restricted, as in v0.13: byte-identical comparison is restricted to the `--no-family` configuration as a pre-flight regression test; the full v1.3 batch is compared to v1.2 by characterising the divergence rather than by asserting byte-identity.

---

## 4. Pre-flight verifications

Four verification levels are required before the v1.3 batch runs:

**Level 1 (v0.14 baseline, all observers disabled).** With `--no-instrument --no-provenance --no-schema --no-family`, output matches v0.14 baseline byte-for-byte at matched seeds. 10 runs at cost 1.0, 20,000 steps.

**Level 2 (v1.0 baseline, v1.0 instrumentation only).** With `--no-provenance --no-schema --no-family`, output matches v1.0 baseline byte-for-byte. 10 runs at matched seeds.

**Level 3 (v1.1 baseline, v1.0 and v1.1 observers enabled, schema and family disabled).** With `--no-schema --no-family`, output matches v1.1 baseline byte-for-byte. 10 runs at matched seeds.

**Level 4 (v1.2 baseline, v1.0, v1.1, and v1.2 observers enabled, family observer disabled).** With `--no-family` only, output matches v1.2 baseline byte-for-byte on all v1.2 metrics. 10 runs at matched seeds. This is the permanent level-4 regression test added to the pipeline by v1.3.

All four verifications are pre-conditions for the v1.3 batch. Failure of any one is a Category α failure requiring diagnosis before the batch runs.

---

## 5. Metrics

All v1.2 metrics are retained unchanged.

The following metrics are added for v1.3:

**Colour-cell registration.** Per run: `green_cell_registered` (boolean, True if the agent perceived the green colour cell at least once during the run), `green_cell_first_perception_step` (the step of first perception, null if not registered), `yellow_cell_registered`, `yellow_cell_first_perception_step`. These capture whether and when the agent became aware of each family's existence at the perceivable tier.

**Family attractor mastery.** Per run: `green_attractor_mastered` (boolean), `green_attractor_mastery_step`, `yellow_attractor_mastered`, `yellow_attractor_mastery_step`. Derived from the existing mastery sequence fields restricted to the family-attributed coordinates (4,15) and (16,3).

**Family knowledge banking.** Per run: `green_knowledge_banked` (boolean), `green_knowledge_banked_step`, `yellow_knowledge_banked` (boolean), `yellow_knowledge_banked_step`. Derived from the existing knowledge-banking fields restricted to coordinates (14,14) and (5,8).

**Intra-family cross-reference completion.** Per run: `green_crossref_complete` (boolean, True if the green sphere knowledge-banking flag carries a resolved `family_2d_mastery_flag_id`), `yellow_crossref_complete`. These are the v1.3-specific cross-reference completion metrics, parallel to the v1.1 threat-to-knowledge cross-reference completion metrics.

**Family traversal sequence.** Per run: `family_traversal_narrative` — an ordered string of family events in the format `step:event:family`, where events are `colour_registered`, `attractor_mastered`, `knowledge_banked`. Example: `47:colour_registered:GREEN|312:colour_registered:YELLOW|838:attractor_mastered:GREEN|1102:attractor_mastered:YELLOW|3164:knowledge_banked:GREEN`. This is the family-level analogue of the v1.1 formation narrative and the primary substrate for the Category γ relational-individuation finding.

**Schema completeness.** The schema's cell-types count is now expected to be 7 (addition of COLOUR_CELL). Schema complete requires all four sections populated with the extended property matrix.

---

## 6. Pre-registered interpretation categories

Six interpretation categories are pre-registered.

### 6.1 Category α: Preservation of the v1.2 architecture under v1.3 extension

The parallel-observer pattern ensures that with `--no-family`, the v1.3 batch runner produces output matching v1.2 baseline at matched seeds on all v1.2 metrics. This is the level-4 pre-flight verification. Category α succeeds if all four pre-flight verifications pass.

Category α failure — in which the `--no-family` configuration fails to match v1.2 baseline — would indicate that the v1.3 environment changes or observer additions have contaminated the inherited architecture. This requires diagnosis before the full batch is interpreted.

The full v1.3 batch will diverge from v1.2 at matched seeds in runs where the new cells affect trajectory. This divergence is expected and is not a Category α failure. Category α governs the baseline-regression configuration, not the production batch.

### 6.2 Category β: Family structure resolves correctly

The environment's family structure should be internally consistent across all 180 runs:

- Every run should have exactly two colour cells at the specified coordinates.
- Every run should have exactly two family-attributed attractors with correct colour and form properties.
- Every run should have exactly two family-attributed hazard/knowledge cells with correct colour and form properties.
- The schema should be complete with cell-types count = 7 in all 180 runs.
- Intra-family cross-references, where the 3D knowledge-banking flag forms, should resolve to the correct 2D mastery flag in the same family.

Category β succeeds if all five conditions hold at 180 of 180 runs.

### 6.3 Category γ: Relational-individuation finding

The load-bearing substantive finding of the iteration. Two components:

**Component 1: Family traversal uniqueness.** As with v1.1's formation narrative uniqueness, the family traversal narrative should be unique across the 60 runs within each (cost, run length) cell. If family traversal narratives are as individuated as v1.1 formation narratives, this passes at 60 of 60 within every cell.

**Component 2: Intra-family cross-reference as relational record.** The cross-reference between the 3D knowledge-banking flag and the 2D mastery flag should be structurally distinguishable from the v1.1 threat-to-knowledge cross-reference. The distinction: the v1.1 cross-reference links two states of the same coordinate; the v1.3 intra-family cross-reference links two different coordinates related by family membership. The Category γ verdict requires that the v1.3 provenance records carry this distinction cleanly — that the `family_2d_mastery_flag_id` field is correctly populated and references a flag at a different coordinate, not the same coordinate.

Category γ succeeds if Component 1 passes at all eighteen (cost, run length) cells and Component 2 holds at 100% of runs where both the 2D mastery flag and the 3D knowledge-banking flag form within the run length.

A v1.3.1 amendment will specify a structural-distance metric for the family traversal narratives, parallel to the v1.1.1 amendment for the formation narrative metric. The amendment is committed before any Category γ structural-distance analysis is performed on the v1.3 batch.

### 6.4 Category δ: Pre-anticipated negative findings

Three negative findings are anticipated and committed to honest reporting:

**Colour-cell registration rate bounded by Phase 1 and novelty dynamics.** The perceivable-tier colour cells are registered through the novelty drive in Phase 2 exploration. At the 20,000-step run length, some runs may not register both colour cells before the run ends, particularly at high cost levels where the agent's exploration is constrained. The v1.3 paper will report registration rates honestly without treating low rates as architectural failures.

**Intra-family cross-reference completion bounded by run length.** The green sphere and yellow pyramid knowledge-banking flags form only if the competency thresholds are reached within the run length. At the 20,000-step run length, cross-reference completion will be substantially lower than at 160,000 steps. The completion rate is reported against the v1.2 knowledge-banking baseline rather than against an architectural ideal.

**Unaffiliated cells not individually identifiable.** The four unaffiliated attractors and three unaffiliated hazard cells remain categorically identical within their types. The v1.3 architecture does not give them individual identity. The paper reports this honestly as a feature of the present design: two families have been introduced; the remainder of the world awaits subsequent iterations. This is not a defect — it is the correct developmental sequencing.

### 6.5 Category Φ: Honesty constraint on the relational-structure claim

The relational property families v1.3 introduces are the substrate for the agent's eventual capacity to reason about family membership, compare across families, and compose knowledge from multiple families. Whether the present substrate is sufficient for those subsequent capacities is not demonstrated by the v1.3 batch — the agent does not yet read its family records or act on family membership as a cognitive object.

The substantive reading: the family traversal narratives carry the developmental sequence (perceivable before acquirable before bankable), the intra-family cross-references carry the dependency structure (2D before 3D), and the two families together provide the minimum comparison base for cross-family pattern discovery in subsequent iterations.

The deflationary reading: the family structure is encoded in the environment and reflected in the records; whether the agent can eventually use it as a relational cognitive object depends on architectural additions v1.3 does not introduce.

Both readings are consistent with the v1.3 batch. The cross-family comparison iteration is the methodological vehicle for distinguishing them.

### 6.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and γ all pass (or γ partially passes in a recoverable form).

The claim: relational property families are the first taxonomic structure in the prepared environment, and the present architecture can traverse them in the correct developmental sequence — perceivable tier registered before acquirable tier mastered, acquirable tier mastered before bankable tier accessed — producing provenance records that carry both the individual acquisition histories and the intra-family dependency structure. The environment now contains the first two entries in a taxonomy that the agent will, across subsequent iterations, learn to compare, compose, and eventually report on.

A second claim is carried within this one and deserves explicit statement: v1.3 is the first iteration in which the competency gate has a developmental reason traceable through the architecture's own records. In v0.14, the gate was a threshold mechanism — a cell unlocked when a competency counter reached a specified value. The threshold was architecturally correct but semantically opaque: the provenance record for a knowledge-banking flag could say when the gate opened but not why the gate linked these two cells rather than any other pair. Under v1.3, the intra-family cross-reference in the provenance record makes the reason explicit and recoverable: the green sphere was gated behind the green square because they share family membership, and mastery at the 2D tier is the earned precondition for access at the 3D tier. The gate's mechanics are unchanged; its meaning is now held in the record. This is the difference between a threshold and a dependency, and it is the first time the architecture's own provenance can express that difference.

---

## 7. Connection to the SICC trajectory

v1.3 advances the SICC trajectory on three commitments simultaneously, which is unusual for a single iteration. The reason this is acceptable under the single-variable-change discipline is that all three advances are consequences of one architectural addition — the relational identifier system — rather than three independent additions.

**Commitment 1 (schema as embodied a priori)** is advanced by the schema's extension to carry colour and form as property dimensions. The schema now names not just cell types but individual-cell properties within types. This is the schema becoming richer, not the schema being replaced.

**Commitment 6 (layered property structure)** is advanced by the introduction of the direct-properties layer in a richer form: colour and form are direct properties perceivable without action, registered in Phase 1 or early Phase 2, held in provenance independently of the reward history the cell accumulates. The interactional layer (what you discover by engaging with the cell), the relational layer (how cells relate across encounters), and the temporal layer (how understanding changes over time) remain reserved.

**Commitment 3 (unfillable slots as epistemic features)** is advanced by the unaffiliated cells. The v1.3 architecture names two families and leaves the rest of the world unnamed. The provenance records for unaffiliated attractors and hazard cells carry null for colour and form. Those nulls are not ignorance — they are the architecture's first vocabulary for "this cell belongs to a family I do not yet have a name for." The slot exists. Its emptiness is an epistemic state worth preserving.

The commitments not yet advanced by v1.3 — prediction-surprise as learning signal (Commitment 7), self-knowledge as derivative of object-knowledge (Commitment 8), auditable reporting (Commitment 11) — remain reserved for subsequent iterations. v1.3 enriches the substrate those iterations will read from; it does not reach ahead of its developmental position.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.3 implementation work begins.

**Matched-seed comparison.** Seeds loaded from `run_data_v1_2.csv` at every (cost, run length, run index) cell.

**Pre-flight verifications.** All four levels pass before the full v1.3 batch runs.

**Single-architectural-change discipline.** v1.3 introduces relational property families as the singular architectural extension. The parallel-observer pattern is preserved for a fourth layer. No SICC commitment beyond those identified in section 7 is operationalised.

**Amendment policy.** Three amendments available. One provisionally reserved for v1.3.1 (Category γ structural-distance metric specification for family traversal narratives, parallel to v1.1.1). Two available for unanticipated operational issues.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 1 May 2026, before any v1.3 code is written.

---

## 9. Stopping rule

The v1.3 iteration completes when:

- All four pre-flight verifications pass.
- The full 180-run batch has run.
- The v1.3.1 amendment specifying the Category γ structural-distance metric for family traversal narratives is committed.
- Categories α, β, γ, δ, Φ, and Ω have been characterised in the v1.3 paper.
- The v1.3 paper is drafted.

The iteration is reset if the amendment budget of three is exhausted before iteration completion, or if a Category α failure requires architectural change to resolve.

---

## 10. References

Baker, N.P.M. (2026a–t) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.2. Full reference list inherited from v1.2 paper.

Baker, N.P.M. (2026u) 'v1.2 Pre-Registration: Explicit Schema Observation via Parallel Observer on Existing Architecture', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026v) 'Explicit Schema Observation in a Small Artificial Learner: The Architecture's Self-Description as a Parallel Record', preprint, 1 May 2026.

Baker, N.P.M. (internal record, drafted alongside v0.13) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent', v0.1.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 1 May 2026, before any v1.3 implementation work begins.
