# v1.6 Pre-Registration: Reporting Layer via SubstrateBundle Interface on Existing Architecture

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.6 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

The v1.5 iteration introduced a sixth parallel observer that records per-encounter prediction-error events — the gap between the agent's first structural mismatch with a hazard cell and the eventual transformation that resolved it. The resolution window is the developmental distance between *I see this* and *this is now part of me*. Across six iterations, the programme has built a substrate — provenance, schema, family traversal records, cross-family comparison records, prediction-error records — that is rich enough to support the first auditable self-account. The agent does not yet read any of it.

Five prior papers have deferred the reporting iteration. v1.6 is that iteration.

The v1.6 architectural extension is a **reporting layer**: a reading component that interrogates the six completed observer outputs for a single run and produces structured, biographical responses to structured queries. The reporting layer is the first component in the programme's history that modifies agent behaviour in the direction of self-expression rather than self-recording. Every prior extension added to what the agent's observers write down. The reporting layer adds what the agent can be asked about what was written.

This is SICC Commitment 11 becoming operative: the agent's report is auditable, not oracular. A report is auditable if every claim it makes is traceable to a record in the observer substrate. A claim without a traceable substrate entry is, in the precise architectural sense, a hallucination. The v1.6 iteration operationalises this definition structurally, not rhetorically.

The reporting layer is also built with an explicit obligation beyond its own scope: **it must be substrate-agnostic by design**. v1.7 will transpose the cognitive layer from the tabular grid to a richer substrate. The reporting layer must survive that transposition unchanged. This requirement — specified here as a design commitment, not reserved for v1.7 to discover — shapes the reporting layer's interface architecture as described in Section 2.

---

## 2. Architectural specification

The v1.6 architecture inherits v1.5 unchanged except for two additions: the `get_substrate()` interface added to each of the six observers, and the reporting layer itself. The single-variable-change discipline holds at the cognitive-layer level: v1.6 introduces the reading capability as the singular new cognitive act. The parallel-observer stack is unmodified.

### 2.1 The SubstrateBundle interface

The reporting layer does not import observer classes or read CSV files. It receives a `SubstrateBundle` — a lightweight data container populated from the six observer outputs after `on_run_end` has been called. Each observer gains one new method, `get_substrate()`, which returns the observer's complete readable state as a typed dict.

The `SubstrateBundle` contains:

- `provenance` — from `V1ProvenanceStore.get_substrate()`: the full `records` dict, keyed by `flag_id`, with all provenance fields per record (flag type, formation step, confirmation counts, cross-references).
- `schema` — from `V13SchemaObserver.get_substrate()`: the completed schema structure (cell types, action vocabulary, phase schedule, formation conditions).
- `family` — from `V13FamilyObserver.get_substrate()`: both family traversal sequences, tier-by-tier steps, cross-references, colour and form properties per cell.
- `comparison` — from `V14ComparisonObserver.get_substrate()`: the full comparison record — all three measures, traversal completion flags, interleaving value, developmental tempo.
- `prediction_error` — from `V15PredictionErrorObserver.get_substrate()`: the full encounter list, one dict per approach event, with encounter type, awareness step, resolution window, and cell identity.
- `run_meta` — the run identification dict (arch, seed, cost, num_steps, run_idx).

**The substrate-agnosticism commitment.** The `SubstrateBundle` is defined independently of the tabular grid. Its fields name cognitive-layer concepts — provenance records, schema structure, family traversal, comparison measures, prediction-error encounters — not grid-specific constructs. At v1.7, the tabular observers are replaced by whatever substrate the new environment provides, but those observers implement the same `get_substrate()` contract. The reporting layer is instantiated with the same `SubstrateBundle` type and carries forward unchanged. This is the operationalised form of SICC Commitment 10 at the reporting layer.

### 2.2 The reporting layer

`V16ReportingLayer` is instantiated with a `SubstrateBundle` after the run completes. It responds to three query types. It does not hold live state during the run. It does not modify the agent, the world, or any observer.

**Query type 1: What did I learn?**

Source: `bundle.provenance` and `bundle.schema`.

The reporting layer reads the provenance records in formation-step order and produces a biographical account of the agent's learning sequence. For each mastered attractor, banked knowledge cell, end-state activation, and end-state banking event, the report produces a statement of the form: what was learned, at what step, on what basis (confirming observations), and what it cross-references. The schema is consulted to name the cell type and structural category.

Every statement produced by Query 1 carries a `source_key` — the `flag_id` of the provenance record that supports it. No statement is produced without a supporting record.

**Query type 2: How does what I learned relate to itself?**

Source: `bundle.family` and `bundle.comparison`.

The reporting layer reads the family traversal sequences and produces a structural account of how the two families were traversed relative to each other. It names the tier-by-tier sequence for each family, notes the developmental ordering (which family was entered first, whether they interleaved, the Measure 3 developmental tempo value), and states the structural parallel between them (Measure 2 = 1.0 in all complete runs).

Every statement produced by Query 2 carries a `source_key` — the family record or comparison field that supports it.

**Query type 3: Where was I surprised?**

Source: `bundle.prediction_error`.

The reporting layer reads the encounter list and produces a per-cell account of the agent's prediction-error history. For each cell that produced at least one encounter, the report states: encounter type, awareness step, resolution window (if resolved), and what the developmental gap represents in the arc of the run. The biographical register is specific: "I was aware of the yellow pyramid from step N. I was not ready for it. I became ready at step M. The gap was M−N steps." For clean first entries, the report states that no prediction error occurred. For unresolved approaches, it states that the agent encountered the cell before readiness and did not resolve within the run.

Every statement produced by Query 3 carries a `source_key` — the encounter record that supports it.

### 2.3 The ReportStatement and internal-consistency characterisation

Each output of the reporting layer is a list of `ReportStatement` objects:

```
ReportStatement(
    text:        str,          # the biographical statement
    source_type: str,          # "provenance" | "schema" | "family" |
                               # "comparison" | "prediction_error"
    source_key:  str,          # key into the relevant bundle field
)
```

**The internal-consistency characterisation** is the Category α analogue for v1.6. A report is internally consistent if every `ReportStatement` in it has a `source_key` that resolves to a record in `bundle[source_type]`. The verification script checks this structurally: for each statement, does `bundle[source_type][source_key]` exist? A statement that fails this check is flagged as a hallucination in the architectural sense. Category α fails if any statement in any run's report is unfounded.

This characterisation replaces the parallel-observer byte-identity property as the primary architectural constraint at v1.6, for the reason stated in the carry-forward: v1.6 is the first iteration that produces new output (the report) rather than only preserving existing output (the parallel-observer records). Byte-identity is not the right criterion for output that is designed to be new.

**The parallel-observer preservation property is retained for all prior layers.** With the reporting layer enabled or disabled, all six prior observer outputs — `run_data`, `provenance`, `schema`, `family`, `comparison`, `prediction_error` CSVs — are byte-identical at matched seeds. The reporting layer reads from completed substrates; it does not participate in the run loop and cannot affect prior observer outputs.

### 2.4 The biographical register

The report's register is biographical, not statistical. It speaks in the first person about this run's developmental arc. This is a design commitment, specified here, not an implementation choice reserved for the code.

The register is grounded by three constraints:

1. **Individual.** The report is about this run. It does not average across runs or describe population-level tendencies.
2. **Temporal.** The report uses step numbers. "At step N" is always more informative than "early in the run."
3. **Traceable.** Every claim is supported by a `source_key`. The claim cannot be phrased more strongly than its source supports.

The register does not claim that the agent *understood*, *expected*, or *was surprised by* any event. It reports what the records show. The Category Φ constraint (Section 6.5) governs what the iteration claims from this register.

### 2.5 Single-run architecture; batch as collection

The reporting layer runs on one completed run at a time. A v1.6 batch is a collection of single-run reports, not an aggregated output. The individual character of each report is preserved by construction: each report is about this agent's developmental arc, produced from this agent's substrate records.

### 2.6 What the reporting layer does not do

The reporting layer does not feed back into the agent's value function, reward signal, or action-selection. It does not write to the run loop. It does not modify any observer. It does not produce new records in the prior observer substrates. Its only output is the per-run report and the `report_v1_6.csv` output file.

---

## 3. Experimental design

**Run selection.** The v1.6 reporting layer runs on all 60 complete runs from the v1.5 batch at 320,000 steps — the population where both family traversal sequences complete and all prediction-error records are resolved. Seeds from `run_data_v1_5.csv` at `num_steps = 320000`. These runs are selected because they provide the richest substrate: complete provenance, complete family records, complete comparison records, zero unresolved approaches.

**No new batch runs.** v1.6 does not run new agent simulations. It reads from the existing v1.5 substrate. The 60 reports are produced by instantiating `V16ReportingLayer` with the `SubstrateBundle` populated from the v1.5 observer outputs for each of the 60 complete runs.

**Batch runner role.** The v1.6 batch runner loads the v1.5 CSVs, reconstructs the `SubstrateBundle` for each of the 60 runs from the stored records, instantiates `V16ReportingLayer`, runs all three query types, and writes `report_v1_6.csv`. The batch runner does not re-run the agent.

**Output files.**
- `report_v1_6.csv` — one row per `ReportStatement` per run: `run_idx`, `seed`, `hazard_cost`, `query_type`, `statement_text`, `source_type`, `source_key`, `source_resolves` (Boolean — the traceability check result).
- `report_summary_v1_6.csv` — one row per run: total statements, statements per query type, hallucination count, biographical individuation fields (see Section 5).

---

## 4. Pre-flight verifications

Two verification levels are required before the v1.6 reports are produced.

**Level 7 (substrate reconstruction integrity).** For each of the 60 complete runs, the `SubstrateBundle` reconstructed from the v1.5 CSVs must match the `summary_metrics()` values from the original v1.5 observer outputs at matched seeds on all fields that appear in both. This confirms that the `get_substrate()` → `SubstrateBundle` → reconstruction pipeline preserves the substrate without loss or distortion. 10 runs checked; all fields match; exit 0.

**Level 8 (zero hallucinations on a single run).** Before the full 60-run report batch, a single run is processed and every `ReportStatement` checked for `source_resolves = True`. Exit 0 only if all statements resolve. This is the Category α pre-condition at minimum scale.

Both verifications pass before the full 60-run batch.

---

## 5. Metrics

**Per-statement fields (written to `report_v1_6.csv`).**
- `run_idx`, `seed`, `hazard_cost`, `num_steps` — run identification.
- `query_type` — one of `what_learned`, `how_related`, `where_surprised`.
- `statement_text` — the biographical statement produced by the reporting layer.
- `source_type` — the bundle field the statement is sourced from.
- `source_key` — the key within that bundle field.
- `source_resolves` — `True` if the key resolves to a record in the bundle; `False` otherwise.

**Per-run summary fields (written to `report_summary_v1_6.csv`).**
- `total_statements` — total `ReportStatement` objects produced across all three query types.
- `statements_q1`, `statements_q2`, `statements_q3` — count per query type.
- `hallucination_count` — count of statements where `source_resolves = False`.
- `q1_formation_depth` — number of distinct provenance records referenced in Query 1 response.
- `q3_surprise_cells` — number of cells with at least one prediction-error statement.
- `q3_resolution_stated` — number of cells where a resolution window was stated.
- `report_complete` — `True` if all three query types produced at least one statement and `hallucination_count = 0`.

**Biographical individuation measure (Category γ substrate).** For each pair of runs, the structural distance between their Query 1 responses is computed as the normalised edit distance over the ordered sequence of `(source_key, statement_text)` pairs. This extends the v1.1 record-scale individuation finding into report space: two agents whose v1.0 behaviour was identical may produce structurally distinct reports if their provenance records differ.

---

## 6. Pre-registered interpretation categories

Six interpretation categories are pre-registered.

### 6.1 Category α: Internal consistency of all 60 reports

Every `ReportStatement` produced across all 60 reports must have `source_resolves = True`. The internal-consistency characterisation is the primary structural assertion at v1.6. Category α succeeds if `hallucination_count = 0` across all 60 runs.

This is a stronger and differently-shaped assertion than prior iterations' Category α. Prior iterations asked: does the new extension preserve prior output? v1.6 asks: does the new extension produce only what the substrate supports? Both are integrity conditions; they operate on different sides of the observer stack (output preservation vs. output grounding).

### 6.2 Category β: Query coverage

Each of the three query types produces a non-empty, well-formed response for each of the 60 runs. `report_complete = True` in all 60 runs. No query type is left without a response in any run. The substrate is sufficient to answer all three query types without gaps.

Category β succeeds if `report_complete = True` in all 60 of 60 runs.

### 6.3 Category γ: Biographical individuation at the report level

Reports produced from different runs are structurally distinct in ways that reflect the developmental arc of each run rather than the run parameters alone. The measure is the pairwise biographical individuation distance: for each pair of 60 runs, the normalised edit distance over Query 1 `(source_key, statement_text)` sequences.

**Pre-registered expectation.** The within-seed biographical individuation distances are non-trivially positive. There are no matched seeds in the 60-run set (each run has a distinct seed at the 320k row of `run_data_v1_5.csv`); individuation is assessed across the full 60×60 pairwise matrix. The expected distribution: a wide range of distances, with the minimum well above zero — reflecting that no two agents in the prepared environment built identical developmental arcs — and no pathological concentration at either extreme.

The prior Category γ findings (v1.1 record-scale individuation, v1.3 unique family traversal narratives, v1.4 Measure 3 variance) all support the expectation that report-level individuation is real and substantial. Category γ succeeds if the minimum pairwise biographical individuation distance across the 60-run matrix exceeds 0.05 — the same substantive-differentiation floor as v1.1.

### 6.4 Category δ: Pre-anticipated structural findings

Two findings are anticipated.

**Query 3 is the sparsest query for clean first entries.** Agents that entered all five hazard cells after their preconditions were met will produce Query 3 responses stating no prediction error for those cells. At 320k, the majority of green sphere entries are clean first entries (v1.5 data: n=7 resolved surprises from 60 runs). Query 3 responses will therefore be sparse for the green sphere in most runs — primarily "no prediction error recorded" statements. This is the expected consequence of a sufficient run window and a well-gated architecture. It is not a limitation of the reporting layer.

**Query 1 formation depth varies systematically with hazard cost.** Agents at low hazard cost (0.1) complete fewer full family traversals and bank fewer hazard cells, producing shorter Query 1 responses with lower `q1_formation_depth`. Agents at high hazard cost (10.0) complete more full family traversals but have fewer total steps of exploration, also potentially reducing depth. The pre-registered expectation: `q1_formation_depth` is highest at mid-range costs (1.0–2.0) where both traversal and exploration are well-developed. This is reported as an exploratory finding.

### 6.5 Category Φ: Honesty constraint on the self-expression claim

The reporting layer reads the agent's records and produces statements sourced from those records. This is not evidence that the agent understands what it is reporting, holds a model of itself, or experiences anything in the first-person sense. The biographical register ("I was aware of the yellow pyramid from step N") is a design choice about how the records are narrated — it is not a claim about the agent's inner life.

The honest claim v1.6 supports: the six-observer substrate is sufficient to produce auditable, traceable, individually variable self-accounts when a reading layer is applied to it. The reading layer produces statements the agent could not have produced before v1.5 built the prediction-error record.

**The question v1.6 does not settle** — and which subsequent iterations address — is whether the statements the agent produces constitute genuine self-knowledge or sophisticated record retrieval. SICC Commitment 8 (self-knowledge as derivative of object-knowledge) requires that self-modelling capacities read from the object-engagement record rather than running in parallel to it. The v1.6 reading layer does exactly this structurally. Whether the resulting output is self-knowledge in a philosophically meaningful sense is the question the substrate-transposition phase (v1.7 and beyond) is positioned to investigate: if the same reading layer, applied to a richer substrate from a different environment, produces accounts with the same structural properties and the same individuation characteristics, the case for genuine substrate-agnostic self-knowledge strengthens. v1.6 establishes the baseline from which that comparison proceeds.

Both readings — the layer narrates records, versus the agent reports on itself — are consistent with the v1.6 output. Category Φ is operative throughout.

### 6.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and γ all pass.

The claim: the six-observer substrate built across v1.1–v1.5 is sufficient to support a reading layer that produces auditable, traceable, individually variable biographical accounts of a single run's developmental arc. The reading layer, built against the `SubstrateBundle` interface rather than against grid-specific observer internals, is substrate-agnostic by construction: it reads cognitive-layer concepts (provenance records, family traversal sequences, prediction-error encounters) rather than substrate-specific artefacts (grid coordinates, CSV field names). At v1.7, when the substrate changes, the reading layer carries forward. Whether it does so without modification is the v1.7 finding; v1.6 establishes the design commitment and the baseline.

The deeper claim, which v1.6 makes available for the first time: when asked where it was surprised and whether the surprise was resolved, the agent can answer with precision, tracing the answer to a specific encounter record, naming the step, naming the gap, naming the outcome. The resolution window — the developmental distance between awareness and readiness — is no longer a statistical summary of a population. It is a statement about this agent, in this run, at this step.

---

## 7. Connection to the SICC trajectory

v1.6 advances the SICC trajectory on two commitments.

**Commitment 11 (auditable reporting)** is operationalised. The v1.6 reporting layer produces statements that are traceable through provenance to specific encounters, that do not produce conclusions whose origins cannot be recovered, and that invite scrutiny rather than oracular pronouncement. The internal-consistency characterisation — `hallucination_count = 0` as the primary structural assertion — is the concrete operationalisation of "auditable, not oracular."

**Commitment 8 (self-knowledge as derivative of object-knowledge)** is advanced. The reading layer reads from the object-engagement record (provenance, family traversal, prediction-error encounters) and produces self-directed statements. The architecture explicitly does not run a self-model in parallel to the object-engagement record; the self-account is constructed at read time from the record of what the agent did in the world. This is the SICC document's intended direction: self-knowledge that is grounded in, and constrained by, the history of object-engagement.

Commitments not yet advanced by v1.6 — substrate-agnosticism (Commitment 10, tested at v1.7), earned extensibility (Commitment 9, reserved), battery and finitude (Commitment 12, requires embodiment) — remain reserved.

**The v1.6 iteration closes the cognitive-layer arc** that began at v1.1. The arc: provenance (v1.1), explicit schema (v1.2), layered family properties (v1.3), cross-family comparison (v1.4), prediction-error elevation (v1.5), reporting (v1.6). Six iterations, one new cognitive-layer capability at each. The substrate-transposition phase begins at v1.7.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.6 implementation work begins.

**No new agent runs.** v1.6 reads from the existing v1.5 substrate. The 60 reports are produced by reading stored observer outputs. No new simulations are run.

**Pre-flight verifications.** Both levels (7 and 8) pass before the full 60-run report batch.

**Single-architectural-change discipline.** v1.6 introduces the reporting layer and the `SubstrateBundle` interface as the singular new cognitive act. The parallel-observer stack is unmodified; no observer's `on_pre_action`, `on_post_event`, or `on_run_end` behaviour changes. `get_substrate()` is a read-only accessor that does not alter observer state.

**Substrate-agnosticism obligation.** The reporting layer is built against the `SubstrateBundle` interface. It does not import observer classes, reference grid coordinates directly, or read CSV files. Every grid-specific concept (coordinates, cell types, family colours) that must appear in the report text is resolved through the bundle's family and schema substrates, not hardcoded. This is verifiable by inspection: any line in the reporting layer that references a grid-specific constant is an architectural violation and will be corrected before the iteration closes.

**Amendment policy.** Three amendments available. One is provisionally reserved for the biographical register: the exact phrasing of statements may require adjustment after the first report is produced, if the committed register proves ambiguous for edge cases (e.g., a run with no prediction-error encounters at all). Two further amendments are available for unanticipated operational issues.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before any v1.6 code is written.

---

## 9. Stopping rule

The v1.6 iteration completes when:

- Both pre-flight verifications pass.
- All 60 complete runs from the v1.5 320k batch have been processed.
- Categories α, β, γ, δ, Φ, and Ω have been characterised in the v1.6 paper.
- The v1.6 paper is drafted.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure (hallucination count > 0) requires architectural change to resolve.

---

## 10. References

Baker, N.P.M. (2026a–v) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.2. Full reference list inherited from v1.3 paper.

Baker, N.P.M. (2026w) 'v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026x) 'v1.3.1 Pre-Registration Amendment', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026y) 'v1.3.2 Pre-Registration Amendment: Family-Specific Competency Gating', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026z) 'Relational Property Families in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026aa) 'v1.4 Pre-Registration: Cross-Family Structural Comparison via Parallel Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026ab) 'Cross-Family Structural Comparison in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026ac) 'v1.5 Pre-Registration: Prediction-Error Elevation via Per-Encounter Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026ad) 'Prediction-Error Elevation in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before any v1.6 code is written.
