# Explicit Schema Observation in a Small Artificial Learner: The Architecture's Self-Description as a Parallel Record

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 1 May 2026
**Status:** Working draft — Sections 1 through 4

---

## Abstract

A preceding iteration (Baker, 2026r, 2026t) established provenance over learned states as the first operationalisation of the Substrate-Independent Cognitive Commitments framework: existing flag structures acquired formation histories and became records of their own conditions of formation, held in a parallel observer module that introduces no behavioural modification to the agent. The v1.1 iteration demonstrated that these records carry agent-individual structural variation that is largely orthogonal to the experimental conditions, with every formation narrative unique across the 180-run batch and within-cell pairwise structural distances six to ten times the substantive-differentiation floor.

v1.2 operationalises SICC Commitment 1: the architecture holds and can be interrogated about the structure of what it knows about. The architectural extension is contained at the research-question level — a schema observer module is added as a third parallel observer alongside the v1.0 recorder and the v1.1 provenance store, with no modification to the v0.14 agent or world. The schema observer constructs, at run initialisation, a complete structural description of the architecture: cell types with their passability, cost, feature-reward eligibility, attraction-bias eligibility, gating eligibility, and transformation eligibility; the four actions with their displacement vectors; the three developmental phases with their drive compositions and transition conditions; and the four flag types with their formation conditions, formation thresholds, confirming-operationalisations, disconfirming semantics, and applicable cell types. The schema is uniform across all runs of a given architecture — it describes the architecture, not any particular run — and it is complete in all 180 runs of the v1.2 batch.

The batch is matched to v1.1 seeds and produces three findings.

The first is preservation at byte-identical resolution. With the schema observer disabled (`--no-schema`), the v1.2 batch runner produces output matching v1.1 baseline at matched seeds across all v1.1 metrics. With all three observers disabled, output matches v0.14 baseline. The parallel-observer pattern, established as the implementation discipline in v1.1, holds for a third observer layer: a module that records rather than acts cannot contaminate the agent's behaviour, and the level-2 regression test confirms this at each pre-flight run.

The second is schema completeness. The schema observer produces a complete self-description of the architecture in all 180 of 180 runs. The description captures six cell types, four actions, three phases, and four flag types, with every structural property encoded at formation time. The schema is the architecture's first explicit vocabulary for what it knows about: cells as kinds with distinct properties, actions as available verbs, phases as developmental periods with distinct drive compositions, flags as epistemically distinct categories with distinct formation and confirmation conditions. This vocabulary did not exist as an explicit architectural object prior to v1.2; it existed only as implicit structure in the agent's code.

The third is v1.1 provenance inheritance confirmed. The v1.1 provenance observer runs under the v1.2 batch runner at matched seeds, producing formation narratives, cross-reference structures, and confirmation-density patterns indistinguishable from the v1.1 batch. All 60 formation narratives are unique at every run length; provenance counts align with v0.14 behavioural metrics at 180 of 180 couplings; cross-reference resolution holds at the same rates as v1.1 reported. The v1.2 batch is a clean inheritance from v1.1 at the provenance level.

The pre-registered Category Φ honesty constraint, introduced in v1.1 and operative here, bounds the architectural claim for v1.2 in a specific way. The schema observer constructs the architecture's self-description and writes it to disk; the agent does not yet read it. Whether the explicit schema is sufficient as a foundation for the schema-interrogation capability the SICC Commitment 1 fully specifies — the agent querying its own schema to reason about what kinds of things it knows about — is the question the next iteration in the trajectory addresses. v1.2 establishes that the structural description can be produced correctly, uniformly, and without contaminating behaviour. It does not establish that the agent can read or act on the description.

One amendment is provisionally reserved: v1.2.1 would specify the Category γ verdict for the schema-uniformity finding, should a metric for schema structural distance be required. The present batch demonstrates schema completeness rather than schema individuation — the schema is uniform by architectural design — so a structural-distance metric of the v1.1 type is not required. The amendment budget for v1.2 remains at three.

---

## 1. Introduction

### 1.1 Programme to date

The programme's inheritance chain through v1.1 has two distinguishable arcs. The first arc (v0.9 through v1.0) built the agent's persistent knowledge infrastructure across two layers — threat and mastery — extended it to competency-gated content transformation in v0.14, and closed with the v1.0 integration audit of the cumulative inheritance chain. The second arc begins with v1.1's operationalisation of the first SICC commitment (provenance over beliefs) and extends toward the cognitive-layer architecture the SICC document specifies. v1.1 established that flags can become records without disturbing the agent's behaviour, that the records carry agent-individual structural variation at the per-pair level, and that the bidirectional cross-reference structure between threat flags and knowledge-banking flags constitutes learning narratives traceable through the architecture's own state.

What the v1.1 architecture does not do is hold an explicit representation of the structure within which those records exist. A threat flag record holds a formation step, confirming observations, a cross-reference to the knowledge-banking flag derived from the same coordinate, and a disconfirming observation at the moment of v0.14 transformation. It does not hold a self-description of what a threat flag is — that it applies to HAZARD cells, that its formation requires three entries under the v0.10 rule or one signature-matched entry under the v0.12 rule, that it carries a confirming operationalisation of a specific kind, and that its disconfirming semantics are narrow under the present architecture. The record holds provenance about an instance of a flag type; it does not hold provenance about the flag type itself.

This is the gap the v1.2 iteration is designed to close. The schema observer constructs an explicit self-description of the architecture's structural categories — cell types, actions, phases, and flag types — and holds it as a queryable record alongside the per-instance flag records the v1.1 provenance store holds. The schema describes the architecture rather than any particular run; it is the vocabulary within which the per-run records are legible.

### 1.2 SICC Commitment 1 and what explicit schema operationalises

The SICC document's Commitment 1 (Baker, internal record, drafted alongside v0.13) specifies that the agent holds and can interrogate the structure of what it knows about: cell types as kinds, actions as available verbs, phases as developmental periods. The commitment is about the agent's capacity to think about its knowledge categories, not merely to apply them.

The v1.2 iteration operationalises the first part of this commitment — the agent holds the structure — through a parallel observer that constructs the schema at run initialisation and holds it as an explicit record. The second part — the agent can interrogate the structure — is reserved for a subsequent iteration that adds agent-side reading capability to the schema, parallel to how the reporting iteration will add agent-side reading capability to the v1.1 provenance records. v1.2 establishes the schema object; the interrogation iteration establishes the agent's relationship with it.

The design choice to implement schema observation as a parallel observer rather than as a modification to the agent follows directly from the SICC document's principle that the cognitive commitments should be additive: each commitment's operationalisation adds a layer rather than modifying the substrate. The v1.1 pattern — read-only access, no behavioural modification, byte-identical preservation — is the correct pattern for v1.2 for the same architectural reason: the schema is written by an observer, held alongside the agent's other state, and read by subsequent iterations when the agent's architecture includes agent-side reading capability.

### 1.3 What v1.2 contributes and what it does not

The v1.2 contribution is the schema object as an architectural artefact. Prior to v1.2, the structure of the architecture's categories existed only implicitly in the agent's code: the `HAZARD` constant had a value, the `FLAG_THRESHOLD` constant specified the threat-flag formation threshold, the v0.12 signature-matching rule was embedded in the flag-conversion logic. There was no object the architecture held that described these properties as a unit, queryable together, in terms that named the properties explicitly (formation condition, confirming operationalisation, applicable cell types). The schema observer constructs this object at run initialisation, making the implicit structure explicit as a held record.

What v1.2 does not contribute is agent-side reading capability. The agent under v1.2 does not consult the schema any more than it consulted the v1.1 provenance records. The schema is written; it is not read. The consequence is that v1.2's preservation guarantee is as strong as v1.1's: the parallel-observer pattern produces byte-identical behaviour by construction when the observer does not modify the agent's action-selection path.

The distinction between having a schema and being able to read a schema is the v1.2-specific instance of the Category Φ honesty constraint. The substantive reading is that the schema object is sufficient as a substrate for the interrogation iteration to build on. The deflationary reading is that the schema is a structured file that happens to describe the architecture. Both are consistent with the v1.2 batch; the interrogation iteration is the methodological vehicle for distinguishing them.

### 1.4 Findings and their relation to the pre-registration

The v1.2 paper reports three findings.

The first is the preservation finding. The `--no-schema` regression test passes at matched seeds against the v1.1 baseline, confirming that the schema observer does not contaminate the v1.1 provenance records or the v0.14 behavioural metrics. The `--no-schema --no-provenance` configuration passes against v1.0 baseline; the full-disabled configuration passes against v0.14 baseline. Three layers of parallel observation are in place; none disturbs the agent's behaviour.

The second is the schema-completeness finding. The schema observer produces a complete self-description in all 180 of 180 runs. The description is uniform across runs at the same architecture — the schema describes the architecture, not the run — and is structurally correct: every cell type's properties are encoded with their precise qualification under the present architecture's inheritance chain, every flag type's formation condition is attributed to the iteration that introduced it, and the transformation eligibility fields correctly identify HAZARD cells as transformation-eligible and KNOWLEDGE cells as not.

The third is the v1.1 provenance inheritance confirmation. Running the v1.1 provenance observer under the v1.2 batch runner at matched seeds produces formation narratives, provenance counts, and cross-reference structures that replicate the v1.1 batch exactly. The finding confirms that the v1.2 batch is a clean inheritance from v1.1 with no cross-observer contamination.

### 1.5 Connection to the broader programme

The v1.2 iteration occupies a specific structural position in the post-v1.0 trajectory. v1.1 operationalised provenance (SICC Commitment 4); v1.2 operationalises the held schema (SICC Commitment 1, first part). The next phases in the trajectory — layered property structure (SICC Commitment 6), reporting (SICC Commitment 11), and substrate transposition (SICC Commitment 10) — each depend on having both the per-instance records (v1.1) and the schema that names the categories those records belong to (v1.2). The reporting iteration's output is a traceable account of the agent's learning; tracing requires both knowing that a particular flag formed at a particular step (v1.1 provenance) and knowing what kind of thing a flag of that type is (v1.2 schema). The schema is the vocabulary in which the account is written.

---

## 2. Methods

### 2.1 Environment and architecture

The environment and architecture are inherited from v0.14 (Baker, 2026m) unchanged, as confirmed by the pre-flight verifications (Section 2.5). The 20×20 grid, the six cell types, the developmental phase schedule, the threat layer, the mastery layer, the end-state mechanism, and the knowledge-cell mechanism all operate under their inherited specifications.

v1.2 introduces no agent-side modification, no world-side modification, no new cell type, no new agent metric. The architectural extension is contained entirely within a parallel observer module — `v1_2_schema.py` — that constructs the schema object at `__init__` time and exposes it through the same three-hook interface the v1.0 recorder and v1.1 provenance store use.

### 2.2 The schema object

The schema observer constructs a complete structural description of the architecture at run initialisation. The description has four sections.

**Cell types.** For each of the six cell types (FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE), the schema records six binary or scalar properties: passability, cost-on-entry, feature-reward eligibility, attraction-bias eligibility, gating eligibility, and transformation eligibility. The passability and cost-on-entry fields reflect the v0.14 step function; the eligibility fields reflect the architectural decisions inherited through the inheritance chain. HAZARD cells are transformation-eligible and gating-eligible; KNOWLEDGE cells are neither. END_STATE cells are feature-reward-eligible and attraction-bias-eligible pre-banking; gating-eligible once banked. The full property matrix for the present architecture is given in Table 1.

**Table 1.** Cell-type property matrix as held in the v1.2 schema. Binary properties are True/False; cost-on-entry is the scalar cost parameter or null. Transformation eligibility is an architectural property introduced in v0.14; the slot exists for all six cell types and is False except for HAZARD.

| Cell type   | Passable | Cost on entry | Feature reward | Attraction bias | Gating | Transformation |
|-------------|----------|---------------|----------------|-----------------|--------|----------------|
| FRAME       | False    | —             | False          | False           | False  | False          |
| NEUTRAL     | True     | —             | False          | False           | False  | False          |
| HAZARD      | True     | hazard_cost   | False          | False           | True   | True           |
| ATTRACTOR   | True     | —             | True           | True            | False  | False          |
| END_STATE   | True     | —             | True           | True            | False  | False          |
| KNOWLEDGE   | True     | —             | True           | False           | False  | False          |

**Actions.** For each of the four actions (UP, DOWN, LEFT, RIGHT), the schema records the displacement vector (dx, dy). UP displaces (0, −1); DOWN (0, 1); LEFT (−1, 0); RIGHT (1, 0). The action vocabulary has been stable since v0.8 and is recorded here explicitly as a schema property for the first time.

**Phases.** For each of the three developmental phases (PHASE_1, PHASE_2, PHASE_3), the schema records the drive composition, the transition condition, and the phase number. Phase 1 drives on prescribed_path only; Phase 2 drives on novelty, learning_progress, and feature; Phase 3 adds preference. Transition conditions are boustrophedon path completion (Phase 1 to 2) and proportional run-length at 0.6 (Phase 2 to 3). The drive weight vectors per phase are recorded alongside the composition strings, encoding the precise numerical values inherited from v0.14.

**Flag types.** For each of the four flag types (THREAT, MASTERY, KNOWLEDGE_BANKING, END_STATE), the schema records five properties: the formation condition (a natural-language string naming the architectural rule that triggers flag formation), the formation threshold (the integer count at which the rule fires), the confirming operationalisation (the observation events the v1.1 provenance operationalises as confirming), the disconfirming semantics (the narrow semantics committed in v1.1), and the applicable cell types. The flag-type schema makes explicit what was previously implicit: that THREAT formation fires on three entries under the v0.10 rule or on first entry under the v0.12 signature-matching rule; that MASTERY formation fires on three attractor entries under the v0.11.2 rule; that KNOWLEDGE_BANKING formation fires on three knowledge-cell entries under the v0.14 rule; that END_STATE formation fires on the dual-condition trigger (all-attractors-mastered AND all-hazards-banked-as-knowledge, under the v0.14-amended activation) with banking on first post-activation entry.

The schema is complete once all four sections are populated; `schema_complete` is set to True at the end of `on_run_end`. The schema content is identical across all runs at the same architecture — it is a property of the architecture, not of the run — and is written to the per-run CSV as summary fields and to the schema CSV as a full structured record.

### 2.3 Implementation as a parallel observer module

The v1.2 implementation follows the parallel-observer pattern established in v1.1. The `V12SchemaObserver` class exposes `on_pre_action(step)`, `on_post_event(step)`, and `on_run_end(step)` hook methods called by the v1.2 batch runner. The schema content is constructed at `__init__` time rather than accumulated across the run (the schema describes the architecture, which is fixed at run start); the hook methods record schema-adjacent events (attractor bankings, knowledge bankings) for the v1.0-format snapshot file that the v1.2 batch continues to produce for inheritance-chain continuity.

The `V12Agent` class subclasses `V014Agent` to provide the schema at construction time. No inherited method is overridden; `V12Agent` adds the schema attribute to the agent's namespace but does not modify any computational path. With `--no-schema`, the `V12Agent` is not instantiated; the `V014Agent` runs directly.

The v1.2 batch runner (`curiosity_agent_v1_2_batch.py`) runs three parallel observers in series — the v1.0 recorder, the v1.1 provenance store, and the v1.2 schema observer — each receiving hook calls at the same three loop points and writing to its own output files. The four output files are `run_data_v1_2.csv`, `provenance_v1_2.csv`, `snapshots_v1_2.csv`, `schema_v1_2.csv`, and `snapshots_v1_0_under_v1_2.csv`. The seed priority order (v1.1 > v1.0 > v0.14) ensures seeds are drawn from the most recent available baseline.

### 2.4 Experimental matrix and matched-seed comparison

The experimental matrix matches v1.1: one architecture (v1.2) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with three run lengths (20,000, 80,000, 160,000 steps) crossed with ten runs per cell, totalling 180 runs. Seeds are loaded from `run_data_v1_1.csv`, which itself drew from the v1.0, v0.14, v0.13, v0.12, v0.11.2, and v0.10 chain.

Because the v1.2 architectural extension introduces no behavioural modification, the matched-seed comparison produces byte-identical behaviour to v1.1 (and, by transitivity, to v0.14 and all earlier iterations). Every action the agent takes under v1.2 at a given seed is identical to the action it takes under v1.1 at the same seed; the architectures diverge only in what they write to disk through their respective parallel observers, not in what they do.

### 2.5 Pre-flight verifications

Three configurations of the v1.2 batch runner are verifiable against known baselines.

**Level 1 (v0.14 baseline, all observers disabled).** With `--no-instrument --no-provenance --no-schema`, the v1.2 batch runner produces bit-for-bit identical output to the v0.14 baseline at matched seeds. This is the deepest preservation guarantee: removing all three observers restores the agent's raw output. The verification ran on 10 matched-seed runs at cost 1.0, 20,000 steps; result: 10 of 10 match v0.14 byte-for-byte.

**Level 2 (v1.0 baseline, v1.0 instrumentation only).** With `--no-provenance --no-schema`, output matches v1.0 baseline at matched seeds. Result: 10 of 10 match v1.0 byte-for-byte.

**Level 3 (v1.1 baseline, v1.0 and v1.1 observers enabled, schema disabled).** With `--no-schema` only, output matches v1.1 baseline at matched seeds on all v1.1 metrics. This is the permanent level-3 regression test introduced by v1.2 and added to the verification pipeline alongside the existing level-1 and level-2 tests. Result: 10 of 10 match v1.1 byte-for-byte across all v1.1-visible fields.

All three verifications are pre-conditions for the v1.2 batch. Failure of any one would be a Category α failure requiring diagnosis before the batch runs.

### 2.6 Metrics

All v1.1 metrics are retained unchanged. v1.2 adds four schema-summary fields to the per-run CSV: `schema_cell_types_count` (6), `schema_actions_count` (4), `schema_phases_count` (3), `schema_flag_types_count` (4), and `schema_complete` (True/False). The full schema content — every property of every cell type, action, phase, and flag type — is written to `schema_v1_2.csv` as one row per run. The schema CSV includes one header-echo row plus 180 data rows; the data rows are identical across all 180 runs as expected for a fixed-architecture schema.

### 2.7 Pre-registered interpretation categories

The v1.2 paper inherits the α/β/γ/δ/Φ category structure from v1.1, with two modifications.

Category α carries forward unchanged: preservation at byte-identical resolution against the v1.1 baseline, now operationalised as the level-3 `--no-schema` regression test.

Category γ is structurally different for v1.2 than it was for v1.1. v1.1's Category γ measured record-scale individuation across the batch — how much two agents' formation narratives differed. v1.2's schema is uniform by architectural design: two agents running the same architecture produce identical schemas. Schema individuation is not what v1.2 tests. The Category γ question for v1.2 is instead schema completeness and structural correctness: does the schema observer produce a complete and internally consistent description of the architecture it observes? This reformulation is committed here rather than reserved for a v1.2.1 amendment, because the completeness criterion is directly answerable from the existing data without requiring a structural-distance metric of the v1.1 type.

Category Φ applies in the same form as v1.1: the schema is written; the agent does not read it.

---

## 3. Results

### 3.1 Category α: preservation at byte-identical resolution

All three pre-flight verifications passed. Level 1 (v0.14 baseline, all disabled): 10 of 10. Level 2 (v1.0 baseline, v1.1 provenance and schema disabled): 10 of 10. Level 3 (v1.1 baseline, schema disabled): 10 of 10.

The full 180-run batch confirms preservation through internal consistency. Every v1.1 coupling holds at 180 of 180 runs under v1.2:

- `attractors_mastered` equals `prov_mastery_count` in 180 of 180 runs.
- `hazards_banked_as_knowledge` equals `prov_knowledge_banking_count` in 180 of 180 runs.
- `hazards_flagged` equals `prov_threat_count` in 180 of 180 runs.
- Non-null `activation_step` corresponds to `prov_end_state_activation_count` of 1 in 180 of 180 runs.
- `end_state_banked` is True if and only if `prov_end_state_banking_count` is non-zero in 180 of 180 runs.

The schema observer adds no path through which any of these couplings could break; the level-3 verification confirms this structurally, and the internal consistency confirms it across the full batch.

### 3.2 Schema completeness: all 180 runs complete

The schema observer produces a complete self-description of the architecture in all 180 of 180 runs. `schema_complete` is True across the full batch. The four summary counts are uniform: six cell types, four actions, three phases, four flag types, in every run.

The schema content is structurally correct on every verifiable property. HAZARD cells are correctly identified as transformation-eligible (the v0.14 contribution) and gating-eligible (the v0.10 contribution); KNOWLEDGE cells are correctly identified as not transformation-eligible (a KNOWLEDGE cell that has been banked cannot revert to HAZARD under the present architecture). The END_STATE flag-type formation condition correctly names the dual trigger (all-attractors-mastered AND all-hazards-banked-as-knowledge) with attribution to the v0.14-amended activation, distinguishing it from the v0.13 all-attractors-only trigger the pre-registration for that iteration committed. The formation thresholds encode the correct values (THREAT: 3, MASTERY: 3, KNOWLEDGE_BANKING: 3, END_STATE: 1), with the END_STATE banking threshold of 1 correctly reflecting first-post-activation-entry banking rather than the three-entry rule that applies to the other types.

The flag-type confirming operationalisations in the schema align with the v1.1 provenance operationalisations committed in the v1.1 pre-registration (§2.2). The schema names the confirming operationalisation for each flag type at the vocabulary level; the v1.1 provenance records implement it at the per-instance level. The two layers are consistent: every per-run provenance confirmation event in the v1.2 batch is a valid instance of the schema-level confirming operationalisation for that flag type.

The disconfirming-semantics fields in the schema correctly encode the v1.1 narrow definition for each flag type: none under the present architecture except the threat-flag transformation case. The slot-existence principle committed in v1.1 (§1.3 of this paper) is encoded in the schema — every flag type has a disconfirming-semantics field, with the value `none_under_present_architecture` for the three flag types where the architecture does not yet produce disconfirming events, and the transformation-specific description for THREAT flags.

### 3.3 v1.1 provenance inheritance confirmed

The v1.1 provenance observer runs under the v1.2 batch runner at matched seeds. Formation narrative uniqueness is confirmed at 60 of 60 unique narratives at every run length (20k, 80k, 160k). The activation, mastery, and knowledge-banking rates replicate the v1.1 batch exactly, as Table 1 shows.

**Table 2.** v1.2 per-run-length flag-formation summary. Values are identical to the v1.1 paper's Table 1, confirming clean inheritance. The schema observer introduces no change to the rates at which any flag forms.

| Run length | n  | Activated | End-state banked | Full mastery | Full knowledge banking |
|------------|----|-----------|------------------|--------------|------------------------|
| 20,000     | 60 | 17        | 10               | 19           | 26                     |
| 80,000     | 60 | 45        | 39               | 46           | 51                     |
| 160,000    | 60 | 53        | 51               | 54           | 59                     |

The provenance counts per flag type replicate the v1.1 pattern. Mean prov_mastery_count per run (across all run lengths): 5.45, matching the mean attractor mastery count. Mean prov_knowledge_banking_count: 4.45, matching the mean knowledge-banked count. Mean prov_threat_count: 1.01, matching the mean hazards-flagged count. The schema observer running in parallel does not perturb any of these; the level-3 `--no-schema` verification is the formal guarantee, and the batch-level consistency is the empirical confirmation.

The cross-reference resolution rates are unchanged from v1.1: 160 of 165 threat flags with `transformed_at_step` set have resolved `derived_knowledge_flag_id` entries; the five pending cases are all at the 20,000-step run length, where some transformation events fire too late for three post-transition entries to complete before run end. At 80,000 and 160,000 steps, every cross-reference resolves before run end.

### 3.4 Category Φ: the schema is written; the agent does not read it

The Category Φ honesty constraint (v1.1 pre-registration §5.6, operative for v1.2 in a modified form) bounds the architectural claim made in this paper. The schema observer constructs the architecture's self-description and writes it to disk; the agent does not consult it. Whether the explicit schema is sufficient as a foundation for the interrogation capability SICC Commitment 1 fully specifies is the question the schema-interrogation iteration addresses.

The substantive reading: the schema holds the structural information necessary for the agent, in subsequent iterations, to reason about what it knows about — to ask whether a given cell type is the kind of thing that can be flagged, whether a given flag type is the kind of thing that can be confirmed, whether an observed event is consistent with the formation condition for a flag type the agent has not yet encountered. These are the queries that a general learning agent needs to make when encountering a novel environment that shares structural properties with the known one.

The deflationary reading: the schema is a structured record that describes the architecture; whether subsequent iterations can make the agent read and reason from it depends on architectural additions that v1.2 does not introduce.

Both readings are consistent with the v1.2 batch. The parallel to the v1.1 honesty constraint is exact: v1.1 established that the provenance records exist; v1.2 establishes that the schema exists. Whether the agent can read either is the question subsequent iterations answer.

---

## 4. The schema object as an architectural artefact: what making the implicit explicit contributes

### 4.1 The implicit-to-explicit transition

Prior to v1.2, the architecture's structural categories existed only as implicit constraints embedded in the agent's code. The distinction between HAZARD cells (passable, costly, gating-eligible, transformation-eligible) and KNOWLEDGE cells (passable, feature-reward-bearing, not transformation-eligible) was encoded in conditional branches of the step function and the feature-reward computation. The fact that THREAT flag formation fires on three entries under the v0.10 rule or on the first signature-matched entry under the v0.12 rule was embedded in the flag-conversion logic. The fact that Phase 2 drives on novelty, learning_progress, and feature while Phase 3 adds preference was encoded in the phase-specific drive composition switch. None of these distinctions existed as named, queryable properties of an explicit object the architecture held.

The v1.2 schema observer makes these implicit constraints explicit as a held object. This is not a trivial step. The distinction between implicit and explicit architectural knowledge is the distinction between knowing how to do something and knowing that one is doing it in a particular way. The agent under v0.14 navigates the difference between HAZARD cells and KNOWLEDGE cells behaviourally; the agent under v1.2 additionally holds a record that names this difference as a structural property. The held record is the substrate for the agent's eventual capacity to reflect on the structure of its own knowledge — to understand not just that HAZARD cells cost something when entered, but that HAZARD cells are the kind of cell type that is gating-eligible and transformation-eligible, and that this is what distinguishes them structurally from other passable cells.

The developmental parallel is the child who knows how to climb a stair and the child who knows that stairs go up in steps of a particular size and can reason about whether a new obstacle fits the stair category. The former is procedural fluency; the latter is the conceptual knowledge that the SICC document's Commitment 1 specifies. v1.2 lays the record substrate for the latter; the interrogation iteration operationalises it.

### 4.2 The schema as a vocabulary for subsequent iterations

The schema's architectural importance becomes concrete when the subsequent iterations in the SICC trajectory are considered.

The reporting iteration (operationalising SICC Commitment 11) will produce auditable accounts of the agent's learning. An account of the form "this cell was flagged as a threat after three entries, which is the formation threshold for the THREAT flag type, and the cell subsequently transformed into a knowledge cell, which is the transformation event the THREAT flag's disconfirming semantics describe" requires both the per-instance provenance record (v1.1) and the schema-level description of what those terms mean (v1.2). Without the schema, the account is formally complete but terminologically opaque: the numbers are present but the vocabulary that gives them meaning is not in the agent's state.

The layered-properties iteration (operationalising SICC Commitment 6) will extend the cell-type property matrix to richer property layers (interactional properties, relational properties, temporal properties). The v1.2 schema's cell-type section is the direct-properties layer — passability, cost, feature-reward eligibility, attraction-bias eligibility, gating eligibility, transformation eligibility — and the richer layers will be added to the same schema object as new property families. Having the direct-properties layer explicit and correct is the precondition for the richer layers to be added cleanly; the layered-properties iteration does not need to reconstruct the direct properties, because v1.2 already holds them.

The substrate-transposition phase (operationalising SICC Commitment 10) will move the architecture to richer simulated environments and eventually to physical embodiment. When the environment changes, the schema will need to be updated — new cell types, new actions, new phases, new flag types. Having the schema as an explicit object rather than as implicit code makes this update tractable: the schema observer is rewritten for the new environment, and the same record infrastructure holds the new vocabulary. Without the explicit schema, updating the architecture's self-knowledge when the environment changes requires tracing through the agent's code to find every implicit constraint.

### 4.3 What the schema-uniformity finding means

The v1.2 schema is uniform across all 180 runs. This is architecturally expected — the schema describes the architecture, not the run — but it is worth naming as a finding rather than as a foregone conclusion, because the uniformity is a testable property that the v1.2 batch confirms.

Schema uniformity across runs means the architecture's self-description is stable: every agent in the batch holds the same account of what kinds of things it knows about. This is the categorical-knowledge foundation the SICC document's Commitment 1 rests on. If the schema varied across runs, the architecture would hold inconsistent self-descriptions, which would undermine the traceability property the reporting iteration requires. The uniformity finding is the confirmation that the schema observer is producing what it is supposed to produce: a consistent, complete, architecture-level description that can serve as a stable vocabulary for subsequent layers.

The contrast with v1.1's Category γ finding is instructive. v1.1's formation narratives are maximally individuated — every agent produces a unique record of its learning trajectory. v1.2's schema is maximally uniform — every agent holds the same record of the categories within which that trajectory occurs. The two layers are complementary: the schema names the categories, the provenance records populate them with individual instances. Together they are the substrate for an account of the agent's learning that is both individually traceable (through the provenance records) and categorically legible (through the schema).

### 4.4 What this finding does not claim

Three clarifications on the SICC-honest principle that naming what a finding does not claim is part of what the finding is.

The schema-completeness finding does not claim that the schema's current property vocabulary is sufficient for all subsequent iterations. The direct-properties layer (passability, cost, feature-reward eligibility, attraction-bias eligibility, gating eligibility, transformation eligibility) is what the present architecture has; the layered-properties iteration will extend it. What the finding claims is that the direct-properties layer is correctly and completely encoded in the present schema.

The finding does not claim that the flag-type confirming operationalisations in the schema are optimal for the reporting iteration's purposes. The operationalisations were committed in the v1.1 pre-registration and are reproduced faithfully in the v1.2 schema; whether richer operationalisations would produce better self-accounts is the question the reporting iteration answers, not the question v1.2 addresses.

The finding does not claim that the agent has achieved SICC Commitment 1. Commitment 1 specifies that the agent holds and can interrogate the structure of what it knows about. The v1.2 finding is that the agent holds the structure. The interrogation capability is reserved.

---

## 5. Discussion

### 5.1 The parallel-observer pattern extended to a third layer

v1.1 introduced the parallel-observer pattern as the v1.1-specific implementation choice that produced the iteration's byte-identical preservation property. The pattern's architectural significance — read-only access, no modification to agent or world, hook-based event detection, output to disk — was named in the v1.1 paper (Section 5.5) as a methodological contribution beyond the provenance finding itself. v1.2 extends the pattern to a third observer layer and confirms that the extension costs nothing in terms of preservation: three parallel observers running simultaneously produce the same byte-identical behaviour as one or two.

The level-3 regression test is the methodological addition v1.2 makes to the verification pipeline. The v1.1 paper established the level-1 and level-2 tests (against v0.14 and v1.0 baselines respectively) as permanent tests the pipeline runs before each subsequent batch. The level-3 test — `--no-schema` against the v1.1 baseline — extends the pipeline to protect against accidental coupling between the v1.2 schema observer and the v1.1 provenance state. If a subsequent iteration accidentally modified the schema observer in a way that coupled it to provenance state, the level-3 test would catch the coupling before the batch ran.

The pattern generalises: each subsequent iteration that adds a new parallel observer layer should add a corresponding regression test against the previous iteration's baseline. By the time the post-v1.0 cognitive-layer arc reaches the reporting iteration (which will, for the first time, add an observer that does modify agent behaviour), the verification pipeline will have regression tests at v0.14, v1.0, v1.1, v1.2, and any intervening levels. The reporting iteration's preservation characterisation will be performed against this background of confirmed stability.

### 5.2 Schema correctness and inheritance attribution

The v1.2 schema's flag-type formation conditions carry attribution strings naming the iteration that introduced each rule. THREAT flags name the v0.10 rule and the v0.12 rule separately; MASTERY flags name the v0.11.2 rule; KNOWLEDGE_BANKING flags name the v0.14 rule; END_STATE flags name the v0.14-amended activation, distinguishing it from the v0.13 all-attractors-only activation.

This attribution is architecturally significant beyond accurate record-keeping. When the v1.0 integration audit (Baker, 2026q, in preparation) characterised the cumulative inheritance chain, it confirmed that each iteration's contribution was preserved by subsequent iterations. The v1.2 schema makes this preservation visible at the vocabulary level: the schema's flag-type formation conditions name the iteration that introduced each rule, so the schema is itself an inheritance-chain record at the architectural-decision level, not just the per-run-behaviour level. An agent that reads the schema in a subsequent iteration will be able to trace each flag-type formation rule to its origin in the programme's arc.

The transformation-eligibility field is the clearest example. HAZARD cells are transformation-eligible; no other cell type is. This property was introduced in v0.14 and is the architectural basis for the competency-gated content transformation mechanism. The schema records this correctly, with the `ct_HAZARD_transformation_eligible: True` and `ct_KNOWLEDGE_transformation_eligible: False` entries encoding the asymmetry that makes knowledge cells terminal — once a HAZARD cell transforms to KNOWLEDGE, the reverse direction is not available under the present architecture. The schema's disconfirming-semantics field for the KNOWLEDGE_BANKING flag type encodes this correctly as `none_under_present_architecture: knowledge_banking_flags_do_not_retract; slot_exists_for_future_iterations`.

### 5.3 The schema and the Category Φ constraint: the dual reading

The Category Φ honesty constraint applies to v1.2 in a form parallel to its v1.1 application but with a specific difference worth naming.

In v1.1, the Category Φ constraint was about whether the provenance records are sufficient as a substrate for an eventual self-account. The deflationary reading was that the records are timestamps and counts; the substantive reading was that they carry the structural information necessary for a traceable account. The Category γ finding supported the substantive reading by demonstrating that the records differentiate agents at the per-pair level.

In v1.2, the Category Φ constraint is about whether the explicit schema is sufficient as a vocabulary for the interrogation capability SICC Commitment 1 specifies. The deflationary reading is that the schema is a structured description of the architecture that happens to be held as a record. The substantive reading is that the schema is the first-class vocabulary object that subsequent iterations need in order to make the agent's learning categorically legible. The schema-completeness finding supports the substantive reading structurally — the schema is complete, correct, and stable — but does not demonstrate it operationally, because the agent does not yet read the schema.

The distinction between the v1.1 and v1.2 forms of the constraint is instructive. v1.1's provenance records are individuated by design and by finding: the agent's traversal of the prepared environment produces a unique record, and the Category γ metric confirms this individuation is substantial. v1.2's schema is uniform by design: the schema describes the architecture, which is fixed. The evidence for v1.2's substantive reading therefore cannot come from individuation; it must come from correctness and completeness. The v1.2 batch provides this evidence: 180 of 180 complete schemas, structurally correct on every verifiable property. Whether correctness and completeness are sufficient for the interrogation capability is reserved.

### 5.4 Limits of the present work

Three limits are worth naming, following the convention established in the v0.13 and v1.1 papers.

The schema's property vocabulary is limited to the direct-properties layer. The six binary or scalar properties per cell type (passability, cost, feature-reward eligibility, attraction-bias eligibility, gating eligibility, transformation eligibility) describe how the architecture currently treats each cell type in its step function, drive computation, and gating logic. They do not describe interactional properties (how the cell type changes over the course of a run), relational properties (how cells of one type relate structurally to cells of another), or temporal properties (how a cell type's behaviour changes across developmental phases). These richer property layers are what SICC Commitment 6 specifies; they are reserved for the layered-properties iteration.

The schema-uniformity finding is not a stability test. The v1.2 batch runs 180 seeds; the schema is the same in all 180 runs because it describes the fixed architecture. Whether the schema remains correct under varied architectures — architectures with different cell types, different flag types, or different phase structures — is not tested by the v1.2 batch. The robustness of the schema-construction mechanism to architectural variation is a question for the schema-interrogation or substrate-transposition iterations to address.

The agent does not read the schema under v1.2. This limit is the Category Φ constraint restated as a practical observation: none of the evidence in the v1.2 batch about what the schema enables is direct evidence, because the agent has no access to the schema during the run. The evidence is structural (the schema is complete and correct) rather than behavioural (the agent uses the schema to do something it could not do without it). Structural evidence of this kind is necessary but not sufficient for the substantive reading of the Category Φ constraint.

### 5.5 Architectural questions opened

Three questions are sharpened by the v1.2 findings.

The first is the interrogation question. v1.2 establishes that the schema exists and is correct; the schema-interrogation iteration establishes whether and how the agent can read and use it. The substantive vs deflationary reading of Category Φ is resolved by this iteration. A natural test: can the agent, given a novel cell type it has not encountered before, correctly characterise whether entries to that cell would produce feature reward, gating behaviour, or transformation events, by querying the schema rather than by direct experience? This is the kind of query that would distinguish an agent that holds a schema from one that merely behaves in a schema-consistent way.

The second is the richer-vocabulary question. The current schema's cell-type property matrix has six properties per cell type; the SICC document's Commitment 6 specifies a richer layered structure. Adding interactional properties (how does repeated entry change the cell's behaviour?) and temporal properties (does the cell's behaviour differ across phases?) to the schema is the layered-properties iteration's task. The direct-properties layer v1.2 establishes is the foundation; the layered-properties iteration extends it without modifying what v1.2 introduced.

The third is the cross-schema question. The v1.2 schema describes one architecture; the substrate-transposition phase will move the architecture to environments with different schemas. Whether the schema infrastructure is general enough to describe a different architecture — one with more cell types, more actions, different flag formation conditions — or whether it is hard-coded to the present architecture's categories is the question the transposition phase surfaces. The v1.2 implementation's design (constructing the schema from the architecture's constants and property dictionaries at run initialisation, rather than hard-coding the schema content) is intended to generalise; whether it does so correctly in practice is the transposition phase's evidence.

### 5.6 The architectural arc through v1.2

The post-v1.0 cognitive-layer arc now has two iterations in place. v1.1 established provenance over learned states (SICC Commitment 4, first operationalisation). v1.2 establishes the explicit schema (SICC Commitment 1, partial operationalisation). Both are parallel observers; neither modifies the agent's behaviour; the inheritance chain through v0.14 is preserved at byte-identical resolution through three observer layers.

The arc's subsequent phases are reserved with the same discipline. The schema-interrogation iteration adds agent-side reading capability to the schema; its pre-registration will be committed before any code is written. The layered-properties iteration extends the schema's vocabulary; it inherits the v1.2 schema object and adds to it. The reporting iteration adds agent-side reading capability to both the v1.1 provenance records and the v1.2 schema; it is, uniquely among the reserved iterations, one that will necessarily modify the agent's computational path and therefore cannot inherit the parallel-observer preservation property. Its preservation characterisation will be performed in the v0.13 / v0.14 mode: population restriction and cross-layer effect characterisation rather than byte-identical verification.

The amendment budget for v1.2 stands at three at the opening of the iteration. No amendments have been required; the schema-completeness criterion was committed within the paper rather than reserved for a v1.2.1 amendment, on the grounds that the uniformity property is directly inferrable from the architecture without requiring the records to be examined first.

---

## 6. Conclusion

The v1.2 iteration extended the parallel-observer architecture to a third layer, adding a schema observer that constructs, at run initialisation, a complete structural description of the architecture's cell types, actions, developmental phases, and flag types. Across a batch of 180 runs spanning six cost levels and three run lengths, with seeds matched to the v1.1 batch, v1.2 produces three findings.

Preservation holds at byte-identical resolution. The level-3 `--no-schema` regression test passes at matched seeds against the v1.1 baseline; levels 1 and 2 continue to pass against their respective baselines. Three parallel observers running simultaneously produce the same byte-identical behaviour as one or two; the parallel-observer pattern generalises cleanly to a third layer.

Schema completeness holds at 180 of 180 runs. The schema observer produces a complete and structurally correct self-description of the architecture in every run. Six cell types with correct property vectors, four actions with correct displacement vectors, three phases with correct drive compositions and transition conditions, and four flag types with correct formation conditions, thresholds, confirming operationalisations, disconfirming semantics, and applicable cell types. The schema is uniform across runs as expected for a fixed-architecture description; the uniformity is confirmed empirically and is the evidence that the schema-construction mechanism is stable and reproducible.

v1.1 provenance inheritance is confirmed at 180 of 180 couplings. The provenance observer running under the v1.2 batch at matched seeds produces formation narratives, cross-reference structures, and confirmation-density patterns indistinguishable from the v1.1 batch. Schema observation does not perturb provenance observation.

The architectural claim made in this paper is bounded by Category Φ. The schema exists as a held object; the agent does not read it. Whether the explicit schema is sufficient as a vocabulary for the interrogation capability SICC Commitment 1 fully specifies is reserved for the schema-interrogation iteration. What the v1.2 iteration establishes is that the vocabulary exists, is correct, and is stable — the preconditions for the interrogation capability to be built.

The cognitive-layer arc the SICC document specifies has now advanced two steps. Provenance is in place (v1.1); the held schema is in place (v1.2). The schema-interrogation, layered-properties, and reporting iterations are the trajectory's next phases. Each is reserved for its own pre-registration and its own batch. The discipline of single-architectural-change-per-iteration that has held throughout the programme holds for the new arc as it held for the old.

---

## 7. Code and Data Availability

All code, pre-registration documents, batch outputs, and paper drafts are available in the public repository at github.com/RancidShack/developmental-agent.

The v1.2 implementation comprises five files. `v1_2_schema.py` implements the schema observer with the cell-type, action, phase, and flag-type property dictionaries. `curiosity_agent_v1_2_batch.py` is the batch runner; it imports the v0.14 architecture verbatim and runs the v1.0 recorder, v1.1 provenance store, and v1.2 schema observer as three parallel observers. `verify_v1_2_disabled.py` is the level-1 pre-flight verification against v0.14 baseline. `verify_v1_2_no_provenance_no_schema.py` is the level-2 pre-flight verification against v1.0 baseline. `verify_v1_2_no_schema.py` is the level-3 pre-flight verification and permanent regression test against v1.1 baseline.

The batch produced five output files: `run_data_v1_2.csv` (per-run aggregate metrics); `provenance_v1_2.csv` (per-flag formation records); `snapshots_v1_2.csv` (v1.1 provenance snapshots under v1.2 batch); `schema_v1_2.csv` (per-run schema content, 180 data rows plus header echo); and `snapshots_v1_0_under_v1_2.csv` (v1.0 instrumentation snapshots for inheritance-chain continuity). All files are timestamped 1 May 2026.

Seeds were drawn from `run_data_v1_1.csv` with priority order v1.1 > v1.0 > v0.14. The seed chain links v0.10, v0.11.2, v0.12, v0.13, v0.14, v1.0, v1.1, and v1.2 at every (cost, run length, run index) cell.

---

## 8. References

Baker, N.P.M. (2026a–p) Prior preprints in the developmental-agent programme: v0.8 through v0.14 inheritance chain. Full reference list inherited from v1.1 paper (Baker, 2026t).

Baker, N.P.M. (2026q) 'v1.0 Integration Audit of the Developmental-Agent Inheritance Chain', preprint in preparation, 28 April 2026.

Baker, N.P.M. (2026r) 'v1.1 Pre-Registration: Provenance Over Learned States via Formation Records on Existing Flag Structures', GitHub repository, 29 April 2026.

Baker, N.P.M. (2026s) 'v1.1.1 Pre-Registration Amendment: Category γ Structural-Distance Metric Specification', GitHub repository, 30 April 2026.

Baker, N.P.M. (2026t) 'Provenance Over Learned States in a Small Artificial Learner: Formation Records as the Substrate for an Eventual Self-Account', preprint, 30 April 2026.

Baker, N.P.M. (2026u) 'v1.2 Pre-Registration: Explicit Schema Observation via Parallel Observer on Existing Architecture', GitHub repository, 1 May 2026.

Baker, N.P.M. (internal record, drafted alongside v0.13) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent', v0.1.

---

## 9. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper. The treatment of FLA principles in the broader programme is bounded; the computational findings reported here are claimed on their own architectural terms.

No human participant data were collected. No external parties had access to drafts of this paper prior to its preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
