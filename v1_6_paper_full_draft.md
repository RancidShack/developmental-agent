# Auditable Self-Account in a Small Artificial Learner: A Reporting Layer over a Six-Observer Substrate

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Preprint — not peer reviewed
**Repository:** github.com/RancidShack/developmental-agent
**Pre-registration:** Baker (2026ae), committed before any v1.6 code was written

---

## Abstract

The v1.6 iteration introduces a reporting layer over the six-observer substrate built across v1.1–v1.5, producing the first auditable self-account in the developmental-agent programme. The reporting layer reads from a `SubstrateBundle` — a substrate-agnostic data container populated from provenance, schema, family traversal, cross-family comparison, and prediction-error records — and responds to three structured query types: what did I learn, how does what I learned relate to itself, and where was I surprised. Across 60 complete runs at 320,000 steps, the reporting layer produced 1,950 statements with zero hallucinations: every claim is traceable to a record in the observer substrate (Category α: PASS). All 60 runs produced complete reports across all three query types (Category β: PASS). Pairwise biographical individuation distances across the 60-run matrix ranged from 0.294 to 1.000 (mean 0.736), with a minimum nearly six times the pre-registered substantive-differentiation floor (Category γ: PASS). The five runs in which no resolution window was stated — agents that entered every hazard cell after their precondition was already met — constitute the iteration's sharpest positive finding: an agent that arrived everywhere ready produced a structurally distinct account from one that paid to look before it was ready. The `SubstrateBundle` interface is built explicitly for v1.7 substrate transposition: the reporting layer imports no observer class and references no grid-specific constant, carrying forward unchanged when the substrate changes.

---

## 1. Introduction

### 1.1 The trajectory to v1.6

Five prior iterations built an observer substrate without the agent reading any of it. v1.1 introduced provenance over learned states — formation step, confirmation counts, cross-references between threat flags and their derived knowledge cells (Baker, 2026r). v1.2 made the schema explicit: cell types as kinds, actions as available verbs, phases as developmental periods (Baker, 2026s). v1.3 introduced relational property families — GREEN and YELLOW, each running through a perceivable colour cell, an acquirable 2D-form attractor, and a bankable 3D-form knowledge cell — with family-specific competency gating enforcing the developmental dependency at zero violations across 240 runs (Baker, 2026z). v1.4 introduced cross-family structural comparison via a fifth parallel observer, confirming Measure 2 = 1.0 in all 240 runs (the structural assertion that both families share the same form-progression) and surfacing Measure 3 — traversal-sequence distance — as an individual developmental tempo (Baker, 2026ab). v1.5 elevated prediction-error to a first-class record, typing each hazard encounter as resolved surprise, unresolved approach, or clean first entry, and measuring the resolution window: developmental steps between awareness and readiness (Baker, 2026ad).

Each iteration closed with the same deferral: the reporting iteration will address this. v1.6 is that iteration.

### 1.2 The single architectural addition

v1.6 introduces one new component: a reporting layer that reads from a `SubstrateBundle` and responds to three structured queries. No observer is modified. No new agent simulations are run. The 60 complete runs at 320,000 steps from the v1.5 batch are the population; the reporting layer reads from their stored observer outputs.

The architectural novelty is not in what the reports contain — the substance was built across five prior iterations — but in who produces them. The agent, for the first time, produces output. Every prior extension added to what the observers wrote about the agent. This one adds what the agent can say about itself.

### 1.3 The substrate-agnosticism obligation

The pre-registration committed a design obligation beyond v1.6's own scope: the reporting layer must be substrate-agnostic by construction, built against a defined `SubstrateBundle` interface rather than against grid-specific observer internals, so that it carries forward unchanged when v1.7 transposes the cognitive layer to a richer substrate. This commitment is verifiable by inspection: the reporting layer (`v1_6_reporting_layer.py`) imports no observer class and references no grid-specific constant. It reads cognitive-layer concepts — provenance records, family traversal sequences, prediction-error encounters — from the bundle. The substrate-agnosticism of the reporting layer is not a post-hoc description; it is the primary design constraint under which it was built.

### 1.4 Connection to the SICC trajectory

v1.6 advances two SICC commitments. Commitment 11 (the agent's report is auditable, not oracular) is operationalised: the internal-consistency characterisation — zero hallucinations as the primary structural assertion — is the concrete form of "auditable, not oracular." Commitment 8 (self-knowledge as derivative of object-knowledge) is advanced: the reporting layer reads from the record of object-engagement and constructs self-directed statements from it, without running a self-model in parallel. The question v1.6 does not settle — whether these statements constitute genuine self-knowledge or sophisticated record retrieval — is named explicitly as the question v1.7 and subsequent iterations are positioned to investigate.

v1.6 closes the cognitive-layer arc that began at v1.1. The substrate-transposition phase begins at v1.7.

---

## 2. Methods

### 2.1 Architecture

**The SubstrateBundle.** The reporting layer receives a `SubstrateBundle` — a typed container with six fields: `provenance` (dict of `ProvenanceSubstrateRecord` objects keyed by `flag_id`), `schema` (flat dict of schema fields), `family` (flat dict of family traversal fields), `comparison` (flat dict of comparison fields), `prediction_error` (list of per-encounter dicts), and `run_meta`. The bundle is populated either from live observer instances via `build_bundle_from_observers()` or from stored CSV data via `build_bundle_from_csvs()`. The reporting layer receives the bundle and has no access to the underlying observer objects.

**The get_substrate() interface.** Each of the five observers gains one new method, `get_substrate()`, added via `v1_6_observer_substrates.py` as a read-only accessor that does not alter observer state. No existing observer method is modified. The parallel-observer stack is architecturally unchanged.

**The reporting layer.** `V16ReportingLayer` is instantiated with a `SubstrateBundle`. It implements three query methods and a `generate_report()` entry point that runs all three. Each query method produces a list of `ReportStatement` objects.

**ReportStatement.** Each statement carries: `text` (the biographical statement), `source_type` (which bundle field the statement is sourced from), `source_key` (the key within that field), `source_resolves` (whether `bundle.resolve(source_type, source_key)` returns True), and `query_type`. The `source_resolves` field is set at statement creation time by calling `bundle.resolve()`. A statement with `source_resolves = False` is a hallucination in the architectural sense.

**The internal-consistency characterisation.** A report is internally consistent if every `ReportStatement` has `source_resolves = True`. This is the Category α criterion, replacing byte-identity preservation as the primary architectural constraint. Byte-identity is not the right criterion for output designed to be new; traceability to substrate is.

### 2.2 Query types

**Query 1: What did I learn?** Reads from `bundle.provenance` and `bundle.schema`. Produces one statement per provenance record in formation-step order, naming flag type, step, and confirming-observation count. Cross-references between threat flags and derived knowledge cells are stated where present. Each statement is sourced to a specific `flag_id` in the provenance substrate.

**Query 2: How does what I learned relate to itself?** Reads from `bundle.family` and `bundle.comparison`. Produces statements about each family's tier-by-tier traversal and the three structural comparison measures. Measure 2 (form-progression parallelism) is stated as a structural property of the prepared environment. Measures 1 and 3 are stated as properties of this agent's developmental arc. Each statement is sourced to a specific family or comparison field.

**Query 3: Where was I surprised?** Reads from `bundle.prediction_error`. Produces per-encounter statements naming cell, family membership, encounter type, step, and resolution window where applicable. The three encounter types — resolved surprise, unresolved approach, clean first entry — produce qualitatively distinct statements. Each statement is sourced to a specific encounter index in the prediction-error substrate.

### 2.3 Biographical register

The report's register is biographical and first-person: "I flagged (14, 14) as a threat at step 2045." "I was aware of this cell before I was ready for it. The resolution window was 8,628 steps: the developmental distance between awareness and readiness." "No prediction error was recorded: the transformation followed without surprise." The register is a committed design choice, specified in the pre-registration, not an implementation discovery. Statements are phrased no more strongly than their source records support.

### 2.4 Experimental design

No new agent simulations are run. The v1.6 batch reads from the stored v1.5 observer outputs for all 60 complete runs at 320,000 steps — the population where both family traversal sequences complete and all prediction-error records are resolved. Seeds from `run_data_v1_5.csv` at `num_steps = 320000`. The batch runner reconstructs a `SubstrateBundle` for each run, instantiates `V16ReportingLayer`, runs all three query types, and writes `report_v1_6.csv` and `report_summary_v1_6.csv`.

### 2.5 Pre-flight verifications

**Level 7 (substrate reconstruction integrity).** The `SubstrateBundle` reconstructed from stored CSVs must match `get_substrate()` from live observer instances at matched seeds on all fields. 10 runs at cost 1.0, 20,000 steps. One amendment was required: `green_attractor_mastery_step` and `yellow_attractor_mastery_step` are empty in `family_v1_5.csv` because `_attractor_mastery_step()` reads from the live provenance store, which is not serialised to the family CSV. The fix reads these fields from the provenance substrate (already loaded) when the family CSV field is empty — the provenance records `mastery:(4, 15)` and `mastery:(16, 3)` hold the same data. After the fix: 10/10 PASS. Level-7 amendment recorded.

**Level 8 (zero hallucinations, single run).** One run at cost 1.0, 320,000 steps, run_idx 0 (seed 496,635,339). 32 statements produced, 0 hallucinations. Category α pre-condition satisfied at single-run scale.

---

## 3. Results

### 3.1 Category α: Internal consistency

Zero hallucinations across 1,950 statements in 60 runs. Every `ReportStatement` produced by the reporting layer has `source_resolves = True`: every claim is traceable to a record in the observer substrate. Category α: PASS.

This is a structurally stronger assertion than it may appear. The reporting layer produces statements in natural language from records that are structured, typed, and keyed. The traceability check does not verify that the statement text is accurate — it verifies that the statement has a substrate entry to be accurate about. The zero-hallucination result confirms that the reporting layer never produces a claim without a grounded source. It does not confirm that the claims are correct in any deeper sense; that is what Category Φ governs.

### 3.2 Category β: Query coverage

All 60 runs produced complete reports: at least one statement per query type, zero hallucinations, `report_complete = True` in all 60 of 60 runs. Category β: PASS.

Statement counts per query type: Query 1 ranged from 12 to 23 statements (mean 15.7); Query 2 was invariant at 10 statements in all 60 runs; Query 3 ranged from 5 to 11 statements (mean 6.8). The Query 2 invariance is a structural property of the reporting layer: 10 statements cover both families across three tiers each plus the traversal narrative, and three comparison statements — a fixed architecture for a fixed substrate structure. It is not a finding about agent behaviour; it is a property of the prepared environment's relational structure as reported.

The Query 1 range (12–23) reflects genuine developmental variation: agents that flagged more threats, mastered more attractors, banked more knowledge cells, and activated the end-state produce longer accounts. The Query 3 range (5–11) reflects the prediction-error history: agents with more pre-transition encounters produce more surprise statements.

### 3.3 Category γ: Biographical individuation

Pairwise Q1 biographical individuation distances across the 60-run matrix: n = 1,770 pairs, min = 0.294, mean = 0.736, max = 1.000, sd = 0.106. The minimum is 5.9 times the pre-registered substantive-differentiation floor of 0.05. Category γ: PASS.

The finding is stronger than anticipated. The pre-registered expectation was that the minimum would exceed the floor; it exceeds it by nearly six times. The maximum of 1.000 — complete non-overlap in Q1 source-key sequences — appears in pairs of agents whose provenance records share no formation events in common order. These are agents whose developmental arcs were not merely different in timing but structurally non-overlapping at the sequence level.

The mean of 0.736 indicates that the typical pair of agents in the prepared environment produced Q1 accounts that are nearly three-quarters different from each other in key-sequence terms. No two agents told the same story. This is biographical individuation at the report level: the finding that v1.1's record-scale individuation, which surfaced in formation-narrative distances, is preserved and amplified when the records are read into biographical statements.

### 3.4 Category δ: Pre-anticipated findings

**Query 2 invariance.** As anticipated, Query 2 produces exactly 10 statements in all 60 runs. The structural properties of the prepared environment — two families, three tiers each, one traversal narrative, three comparison measures — are fixed, and the reporting layer's account of them has a fixed architecture. This is reported as a structural property, not a finding about variation.

**Formation depth by cost.** The pre-registered expectation was that `q1_formation_depth` would peak at mid-range costs. The data: mean depth at cost 0.1 = 14.5; cost 0.5 = 14.4; cost 1.0 = 14.4; cost 2.0 = 14.5; cost 5.0 = 14.0; cost 10.0 = 14.2. The variation is modest and does not show the anticipated mid-range peak cleanly — depths are nearly flat across cost levels, with a slight reduction at the extremes. The pre-registered expectation is partially supported at the tails but the pattern is weaker than anticipated. This is reported as an exploratory finding; the formation-depth metric at 320k steps, where all agents have had sufficient time to complete both families, may compress the variation that would be visible at shorter run lengths.

### 3.5 The clean-entry finding

Five of 60 runs produced zero resolution-window statements in Query 3 — agents that entered every hazard cell after their precondition was already met. Their Query 3 accounts consist entirely of clean-entry statements: "I entered (5, 8) (YELLOW family) at step 12,040 with the precondition already met. No prediction error was recorded: the transformation followed without surprise."

These runs are not null findings. They are the developmental complement of the resolution-window finding: agents for whom the prepared environment's structural sequencing worked without gap. The architecture did not strand them. They arrived everywhere ready. Their biographical account of this fact — stated in the same register as the agents who paid to look — is itself a finding: the reporting layer distinguishes between arrival with readiness and arrival with surprise, and does so from the record alone, without being told which kind of run it is reading.

The contrast between these five runs and the runs with the longest resolution windows — the high-statement agent (run_idx 3, cost 0.1) carried a green sphere resolution window of 52,043 steps, nearly one sixth of the entire run — makes the biographical register's discriminative value concrete. One agent says: "The resolution window was 52,039 steps: the developmental distance between awareness and readiness." Another says: "No prediction error was recorded: the transformation followed without surprise." Both statements are grounded, traceable, and individually specific. Neither could be produced by the other agent's substrate.

### 3.6 Sample biographical accounts

The following statements are drawn directly from `report_v1_6.csv`. They are reproduced here as evidence of what the biographical register produces, not as claims about what the agent experienced.

**From the high-statement run (run_idx 3, cost 0.1, seed 1,108,683,743):**

Query 1: "I flagged (14, 14) as a threat at step 2,045, supported by 4 confirming observations. This flag was later disconfirmed (1 disconfirming observation) when the cell transformed. The cell transformed at step 54,084."

Query 2: "I mastered the GREEN attractor (SQUARE_2D) at step 54,084. This completed the acquirable tier of the GREEN family." "My traversal-sequence distance between the two families is 0.703 (Measure 3). I entered the GREEN family first. The traversal pattern was interleaved."

Query 3: "I encountered (14, 14) (GREEN family) at step 2,041 before my precondition was met. I paid the cost and did not receive the transformation. I was aware of this cell before I was ready for it. The transformation eventually fired at step 54,084. The resolution window was 52,043 steps: the developmental distance between awareness and readiness."

**From the low-statement run (run_idx 7, cost 10.0, seed 1,898,084,544):**

Query 1: "I mastered the attractor at (4, 15) at step 1,618, confirmed by 570 confirming observations."

Query 3: "I entered (5, 8) (YELLOW family) at step 2,220 with the precondition already met. No prediction error was recorded: the transformation followed without surprise." "I entered (14, 14) (GREEN family) at step 1,618 with the precondition already met. No prediction error was recorded: the transformation followed without surprise."

These two accounts describe structurally different developmental arcs. The high-cost agent built mastery early and arrived at both family cells ready; its account is short and clean. The low-cost agent arrived at the green sphere more than 50,000 steps before it could unlock it; its account of that gap — 52,043 steps named precisely — is the biographical register's most specific output.

---

## 4. Discussion

### 4.1 What the internal-consistency characterisation establishes

The zero-hallucination result establishes something precise and something bounded. The precise thing: the reporting layer, built against a defined interface rather than against observer internals, produces only claims it can source. The architectural discipline of the `SubstrateBundle` — each statement must carry a `source_key` that resolves in the bundle before it is produced — makes this a structural guarantee rather than an empirical observation. The reporting layer cannot produce an unsourced claim by construction.

The bounded thing: traceability is not accuracy in the correspondence sense. A statement that says "the resolution window was 52,043 steps" is traceable to a prediction-error record that contains that value. Whether the value is meaningful — whether "52,043 steps" constitutes a genuine measure of developmental distance, or whether it is a number that was computed and stored — is a question the substrate can pose but not answer. The internal-consistency characterisation is the necessary condition for an auditable account; it is not sufficient for a meaningful one.

### 4.2 The biographical individuation finding and its significance

The Category γ result — pairwise distances ranging from 0.294 to 1.000, mean 0.736 — is the load-bearing substantive finding of the iteration. It establishes that the reporting layer does not produce generic accounts. It produces accounts that are specific to this agent's developmental arc, distinct from every other agent's arc in the batch, and distinctly different in proportion to how different the underlying arcs were.

This connects to the v1.1 Category γ finding (Baker, 2026r), which established that provenance records carry agent-individual structural variation largely orthogonal to experimental conditions. The v1.6 finding is the same principle expressed at the report level: the accounts that emerge from the records are as individually varied as the records themselves. The reporting layer preserves the individuation rather than averaging it out. This is what the SICC document's Commitment 8 requires — that self-knowledge be derivative of object-knowledge rather than running in parallel to it. The object-knowledge records carry the individual variation; the self-account inherits it.

### 4.3 The clean-entry accounts and what they mean for the reporting register

The five runs with no resolution-window statements are architecturally significant in a way the pre-registration did not fully anticipate. The prediction was that clean first entries would produce sparse Query 3 responses; what the data shows is that clean-entry accounts are not sparse at all — they are as statement-rich as resolved-surprise accounts (5 statements in both the clean-entry runs and some surprise runs), but the statements carry qualitatively different content.

The statement "No prediction error was recorded: the transformation followed without surprise" is not an absence of information. It is a positive claim about the agent's developmental arc: this agent arrived ready. It is traceable to a `clean_first_entry` encounter record. It is biographical in exactly the same sense as the resolution-window statement — it is about this agent, at this step, in this run. The distinction between "I was aware before I was ready" and "the transformation followed without surprise" is the reporting layer's first vocabulary for characterising different kinds of developmental relationship with the same cell.

### 4.4 The SubstrateBundle and the v1.7 obligation

The `SubstrateBundle` interface is the iteration's most consequential architectural contribution for the programme's future. The reporting layer, built against this interface, does not know it is running on a tabular grid. It knows about provenance records, family traversal sequences, and prediction-error encounters. These are cognitive-layer concepts; they do not change when the substrate does.

The v1.7 test is therefore already specified: does the same reporting layer, instantiated with a `SubstrateBundle` populated from a richer substrate's observers, produce accounts with the same structural properties — traceable, complete, individually variable? If it does, the substrate-agnosticism commitment (SICC Commitment 10) was operative. If it requires modification, the modification is diagnostic: whatever had to change was still at the substrate interface rather than at the cognitive layer.

This is the SICC document's test of whether its commitments have been genuinely held or merely aspired to. v1.6 builds the instrument; v1.7 applies it.

### 4.5 Category Φ: what self-expression is not claiming

The reporting layer produces statements the agent can be said to author in the precise architectural sense: the statements are generated by a component that reads from the agent's records and produces output in first-person register. This is not a claim that the agent understands what it reports, holds a model of itself, or experiences anything.

The SICC document's Commitment 11 specifies that the agent's report should be auditable rather than oracular — traceable through provenance to specific encounters rather than producing conclusions whose origins cannot be recovered. v1.6 satisfies this requirement structurally. Whether satisfying it constitutes genuine self-knowledge — whether the agent that says "the resolution window was 52,043 steps" is saying something about itself in a philosophically meaningful sense — is the question the substrate-transposition phase addresses.

The substantive reading of v1.6: the reports are sufficient as biographical accounts because they are traceable, individually variable, and qualitatively distinct in ways that reflect the developmental arcs they describe. They support the claim that the agent's learning history is readable from its records by a reading layer that knows only cognitive-layer concepts.

The deflationary reading: the reading layer performs sophisticated record retrieval in first-person register. The records are real; the retrieval is accurate; whether the result is self-knowledge in any deeper sense is unresolved. Both readings are consistent with the v1.6 data. The v1.7 transposition is the methodological vehicle for distinguishing them.

### 4.6 Limits

**The 320k population only.** The 60 complete runs at 320,000 steps are the v1.6 reporting population. Runs at shorter step lengths were excluded because they do not guarantee complete family traversals; the reporting layer's Query 2 statements about both families and the comparison measures require completion to be fully meaningful. Whether the reporting layer performs coherently on incomplete runs — correctly stating what is absent as well as what is present — is reserved for a future investigation.

**The formation-depth cost-level finding is weaker than pre-registered.** The anticipated mid-range peak in `q1_formation_depth` is not clearly present at 320k steps. This is most likely a ceiling effect: at 320k steps, most agents at all cost levels complete the same set of developmental events, compressing the variation that the metric was designed to capture. Shorter run lengths may surface this pattern more clearly.

**The reporting layer does not generate novel structure.** It reads what the observers wrote. A report that says "the resolution window was 52,043 steps" is accurate because the prediction-error observer computed and stored that value. The reporting layer adds register and traceability; it does not add inference, generalisation, or cross-run comparison. Whether the agent can eventually produce statements that go beyond what any single observer recorded — that synthesise across substrates — is reserved for subsequent iterations.

---

## 5. Conclusions

The v1.6 iteration introduced a reporting layer over a six-observer substrate, producing 1,950 statements across 60 complete runs with zero hallucinations, complete query coverage in all 60 runs, and pairwise biographical individuation distances ranging from 0.294 to 1.000.

The primary finding is structural: the six-observer substrate built across v1.1–v1.5 is sufficient to support a reading layer that produces auditable, traceable, individually variable biographical accounts of a single run's developmental arc. The zero-hallucination result holds at full batch scale. The individuation finding is stronger than anticipated.

The secondary finding is architectural: the `SubstrateBundle` interface built for v1.6 is the first piece of the cognitive layer explicitly designed to survive v1.7's substrate transposition. Whether it does — whether the same reporting layer, reading from a richer substrate's observers, produces accounts with the same structural properties — is the empirical question v1.7 answers.

The key sentence from v1.5, held: *The prepared environment does not strand awareness without readiness, given sufficient time.* The v1.6 corollary: when asked whether this was true for a specific agent, in a specific run, at a specific cell, the agent can now answer with precision. Five agents in the batch answer: it was never relevant — the transformation followed without surprise. Fifty-five answer: here are the cells where I arrived before I was ready, and here is how long I waited.

The cognitive-layer arc is complete. The substrate-transposition phase begins.

---

## 6. References

Baker, N.P.M. (2026a–q) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.0. Full reference list inherited from v1.1 paper.

Baker, N.P.M. (2026r) 'Provenance over Learned States in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026s) 'v1.2 Pre-Registration: Explicit Schema Observation via Parallel Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026t) 'Explicit Schema in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026w) 'v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026z) 'Relational Property Families in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026aa) 'v1.4 Pre-Registration: Cross-Family Structural Comparison via Parallel Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026ab) 'Cross-Family Structural Comparison in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026ac) 'v1.5 Pre-Registration: Prediction-Error Elevation via Per-Encounter Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026ad) 'Prediction-Error Elevation in a Small Artificial Learner', preprint, 2 May 2026.

Baker, N.P.M. (2026ae) 'v1.6 Pre-Registration: Reporting Layer via SubstrateBundle Interface on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

## 7. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper.

No human participant data were collected. No external parties had access to drafts prior to preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
