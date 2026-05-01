# Provenance Over Learned States in a Small Artificial Learner: Formation Records as the Substrate for an Eventual Self-Account

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 30 April 2026
**Status:** Working draft — Sections 1 through 4

---

## Abstract

A preceding integration audit (Baker, 2026q, in preparation) closed the second arc of the developmental-agent programme, demonstrating that the architecture under v0.14 inheritance supports persistent categorical knowledge across two layers, late-target activation through random-location cell sampling, competency-gated content transformation, and biographical individuation at trajectory-and-completion scale. By the close of v1.0 the architecture acts on its learned states; it does not yet hold a relationship with them. Threat flags, mastery flags, knowledge-banking flags, and end-state flags are binary states the architecture consults, with no representation of how each came to be set, when it was set, or what observations have sustained it since.

v1.1 operationalises one cognitive-architecture commitment from the Substrate-Independent Cognitive Commitments document (Baker, internal record, drafted alongside v0.13): provenance over beliefs. The architectural extension is contained at the research-question level — existing flag structures acquire formation history and become records of their own conditions of formation — and is the smallest substantive step from v1.0 toward the cognitive-layer commitments the SICC document specifies. The agent does not yet read its own records; the records do not yet drive different behaviour from differently-provenanced flags. What v1.1 establishes is that the architecture now holds objects of a different kind — flags as records rather than flags as switches — and that subsequent iterations will read from, reason about, and act on those objects.

The architectural change is implemented as a parallel observer module modelled on the v1.0 instrumentation pattern. The agent and world are unmodified; record-writing is performed by an external store with read-only access to the agent's state. With the store either disabled or absent, the v1.1 batch produces v0.14-baseline-identical or v1.0-baseline-identical output respectively at matched seeds. Both pre-flight verifications passed at 10 of 10 runs against the relevant baselines. Per-flag provenance fields capture formation step, confirming-observations counts (operationalised per flag type), last-confirmation step, disconfirming-observations counts (under narrow semantics restricted to the v0.14 transformation case), and bidirectional cross-references between threat flags and the knowledge-banking flags that derive from the same coordinate through competency-gated transformation.

Across a pre-registered batch of 180 runs spanning six cost levels and three run lengths, with seeds matched to the v1.0 batch, v1.1 produces four findings.

The first concerns Category α preservation. The v1.1 architectural extension introduces no behavioural modification; the architecture's per-run metrics under v1.1 match v1.0 baseline byte-for-byte at matched seeds in the level-2 verification, and match v0.14 baseline byte-for-byte under the level-1 verification with all instrumentation disabled. Internal consistency between v1.0 metric fields and v1.1 provenance counts holds at 180 of 180 runs across every coupling tested. The architecture's behaviour is preserved at the strongest resolution any iteration in the programme has committed to.

The second concerns Category β alignment between the v1.1 records and the v1.0 snapshot data. Cross-reference structure resolves cleanly: 160 of 160 bidirectional pairs connect threat flags to their derived knowledge-banking flags, with zero unidirectional anomalies, zero missing identifiers, zero inconsistent forward references. Five pending cross-references occur at the 20,000-step run length, all in the expected pattern (cell transformed but knowledge-banking flag had not yet formed by run end). The bookkeeping is correct.

The third concerns Category γ record-scale individuation, and is the load-bearing finding of the iteration. Across all three run lengths and all six cost levels, every single run produces a unique formation narrative — 60 of 60 unique within every (cost, run length) cell, 180 of 180 unique across the full batch. The pre-registered structural-distance metric (specified in the v1.1.1 amendment, Baker, 2026s) produces per-pair distances substantially exceeding the substantive-differentiation floor at every (cost, run length) cell, with within-cell mean distances ranging from 0.32 to 0.53 against a threshold of 0.05. The criterion's across-vs-within ordering succeeds at 13 of 18 cells; in the remaining 5 cells, within-cell distances meet or exceed the across-cell aggregate. Per-component decomposition shows that three of the four metric components (formation order, content set, cross-reference structure) carry within-cell variation approximately equal to across-cell variation, while only confirmation density modestly stratifies by experimental condition. The records carry agent-individual structural variation that is largely orthogonal to the experimental conditions: two agents at matched seeds within the same cell produce records as structurally different from each other as two agents at completely different conditions. This is the substrate-as-individuation finding the iteration was designed to test, surfaced in a sharper form than the criterion anticipated.

The fourth concerns Category δ pre-anticipated negative findings, all of which landed as the pre-registration committed. Threat-flag confirmation density is structurally sparse (mean 0.4 to 0.7 across run lengths) under the present architecture's epistemic conditions for threat-flag confirmation. Disconfirming-observations counts are dominated by zero across most flag types but consistently 1.0 for threat flags whose cells transform — every threat flag whose cell undergoes v0.14 competency-gated transformation receives exactly one disconfirming observation under the narrow semantics. Cross-reference completion rate is bounded by v0.14 transformation dynamics. The honest reporting commitments hold; the negative findings are reported directly.

The pre-registered Category Φ honesty constraint applies. The records v1.1 introduces are the substrate for an eventual self-account; whether subsequent iterations can construct an auditable account of agent learning from these primitives is the question the reporting iteration answers. v1.1's contribution is that the substrate exists, in the form the pre-registration committed to, with the architectural property that subsequent iterations need: bidirectional cross-references that constitute learning narratives rather than collections of independent records, per-flag-type confirmation operationalisations that are honest about epistemic differences across flag types, and individuation at the record scale that surfaces in matched-seed comparison without behavioural modification.

The methodological discipline that has held throughout the programme held during this iteration in modified form. Pre-registration was committed before any v1.1 code was written. The architecture was implemented as a parallel observer module, with the agent and world unmodified; the byte-identical preservation property was therefore stronger than any prior iteration's. One amendment was issued (v1.1.1, specifying the Category γ structural-distance metric operationalisation), committed after the records existed to be examined and before any reanalysis was performed. The amendment budget for v1.1 stands at one of three at the close of the iteration.

## 1. Introduction

### 1.1 Programme to date

A small tabular developmental agent occupying a 20×20 structured environment has, across two arcs of preceding work, demonstrated a set of behavioural signatures associated with developmental learning and progressively acquired the architectural machinery required to support them across extended horizons. The first arc (v0.1 through v0.8) established the signatures: rule adherence, focused autonomy, feature-aligned preference formation, a specialist-generalist trade-off, and full biographical individuation (Baker, 2026a, 2026b). The second arc (v0.9 through v0.14) built persistent categorical knowledge across two layers, demonstrated cross-layer behavioural coupling at three iterations, and closed with competency-gated content transformation: hazard cells transition to knowledge cells when the agent's competency reaches each cell's pre-registered threshold. The v1.0 integration audit (Baker, 2026q, in preparation) characterised the cumulative inheritance chain through 180 runs at matched seeds, confirming that the architecture supports late-target activation through inherited Phase 3 dynamics, that biographical individuation persists at trajectory-and-completion scale, and that cross-layer behavioural coupling is mechanistically confirmed in three distinct iterations.

What the v1.0 architecture does not do, and what subsequent iterations are reserved to address in stages, is hold its learned states as records of their own formation. The threat layer's persistent flag is a primitive form of knowledge: the cell was learned about, the learning persists, the architecture acts on it. The mastery flag and the knowledge-banking flag are similar primitives. The end-state activation and banking flags complete the set. Each is a binary state. The architecture consults the state; it does not interrogate it. Whether a threat flag was set on the third entry to a hazard cell or on the first entry through v0.12 signature-matching, whether it has been revisited in the gating mechanism since formation, whether the cell underneath the flag has subsequently transformed into a knowledge cell — the architecture under v1.0 has no representation of these distinctions. The agent acts on the bit; the bit's history is not part of the system.

This is the gap the v1.1 iteration is designed to close. The architectural extension is contained: existing flag structures acquire formation history and become records of their own conditions of formation. The records do not yet drive behaviour; the agent does not yet read them. What changes is the kind of object the architecture holds. v1.1 is, in this sense, the smallest substantive step from v1.0 toward the cognitive-layer commitments the Substrate-Independent Cognitive Commitments document specifies (Baker, internal record, drafted alongside v0.13).

### 1.2 The intent of provenance, and the Montessori parallel

The intent of v1.1's architectural extension is named explicitly in the SICC document's Commitment 4: provenance is what makes the difference between an agent that has beliefs and an agent that has a relationship with its beliefs. A value without provenance is a value the agent cannot reason about. It can act on it, but it cannot weight it against newer evidence, revise it intelligently, or report on its reliability when asked. Provenance is the audit trail of cognition.

The developmental purpose the records serve, in a deeper sense than the SICC commitment alone makes explicit, is the agent's eventual capacity to give an account of its own learning history when asked. The Montessori parallel: in a prepared environment of materials arranged so that the child's own choices about what to engage with, in what order, produce a learning sequence that is the child's rather than the teacher's, what the child later carries away includes the route by which competencies were acquired. The recollection that the cylinders preceded the binomial cube, that the sandpaper letters grounded the moveable alphabet, that the practical-life work grounded the abstraction. The route is part of what the child knows about themselves and is what makes the learning the child's own rather than something done to them.

The v0.14 architecture, with knowledge cells as foundational and competency-gated hazard cells as advanced, is the prepared environment for the agent. v1.0 instruments that the trajectory through this environment happens. v1.1 records the trajectory in the agent's own state, in a form that can later be queried.

This framing matters for how the records are designed. The records are not metadata attached to flags; they are the architectural object the flags become. A flag in v1.1 is a record of its formation, of which the binary "set or not set" state is the answer to one particular question the record could be asked. The framing is consequential: it means the v1.1 records are the substrate for the eventual reporting iteration to read, not data structures requiring further translation. The reporting iteration that subsequently realises Commitment 11 of the SICC framework does not need to reconstruct the records' meaning from their fields; it reads the records directly.

### 1.3 Pre-registered scope and what v1.1 deliberately does not do

The v1.1 pre-registration (Baker, 2026r) committed the architectural extension to four flag types — threat, mastery, knowledge-banking, and end-state activation and banking — and committed five common provenance fields per record (formation step, confirming-observations count, last-confirmation step, disconfirming-observations count, last-observation step) plus type-specific cross-reference fields. Three things are explicitly out of scope for v1.1 and reserved for subsequent iterations.

The agent does not read its own records under v1.1. This is the explicit boundary that distinguishes the provenance phase from the reporting phase. Adding agent-side reading capability to v1.1 would operationalise two SICC commitments simultaneously — Commitment 4 provenance and Commitment 11 auditability — and the iteration would no longer be contained at the single-architectural-change level the methodological discipline requires. v1.1 establishes the records; the reporting iteration establishes the agent's relationship with them.

The records do not drive behavioural modification. The agent's perception, drive composition, action selection, value learning, and model updates do not consult the records at any point. This is the architectural property that makes Category α preservation achievable as byte-identical behaviour across the full 180-run batch — record-writing happens through a parallel observer module with read-only access to the agent; the agent has no awareness of the observer's existence. Subsequent iterations that introduce predict-and-surprise dynamics (operationalising SICC Commitment 7) are the methodological vehicle for letting differently-provenanced flags drive different behaviour.

The disconfirming-observations slot exists in v1.1 but is populated only under one narrow condition — when a threat flag's cell undergoes v0.14 competency-gated transformation. The architecture under v1.1 does not retract flags; it does not have richer disconfirmation events to record. The slot's existence is the substantive architectural commitment, on the SICC-honest principle that distinguishing a value not observed from a slot that does not exist is the architecture's first vocabulary for knowing what it does not yet do (Commitment 3). Subsequent iterations that introduce flag retraction or competency-loss may extend the semantics; v1.1 holds the slot in narrow form.

### 1.4 Findings and their relation to the pre-registration

The paper reports four substantive findings.

The first is the Category α preservation finding. v1.1's record-writing machinery introduces no behavioural modification; under matched seeds the agent's per-run metrics under v1.1 match v1.0 baseline byte-for-byte, and under the all-instrumentation-disabled configuration match v0.14 baseline byte-for-byte. Both pre-flight verifications committed in the pre-registration (§6) passed at 10 of 10 runs. Internal consistency between v1.0 metric fields and v1.1 provenance counts holds at 180 of 180 runs across every coupling tested: every run that mastered six attractors produced exactly six mastery records; every run that banked knowledge cells produced matching knowledge-banking records; every activation_step in the v1.0 fields aligns with an activation record in the provenance store. The architecture's behaviour is preserved at the strongest resolution the programme has committed to.

The second is the Category β alignment finding. The cross-reference structure introduced by v1.1's bidirectional linkage between threat flags and knowledge-banking flags resolves cleanly across the batch: 160 of 160 bidirectional pairs connect threat flags to their derived knowledge-banking flags, zero unidirectional anomalies, zero missing identifiers, zero inconsistent forward references. The five pending cross-references at the 20,000-step run length are all in the expected pattern (cell transformed but knowledge-banking flag had not yet formed by end-of-run). The bookkeeping logic operationalises the §2.4 specification of the pre-registration correctly across the full batch.

The third is the Category γ record-scale individuation finding, and is the load-bearing finding of the iteration. The pre-registration committed Category γ to a structural-distance metric whose family was specified at pre-registration time and whose specific operationalisation was reserved for v1.1.1 amendment (Baker, 2026s) after the records existed to be examined. The amendment specified a four-component pairwise metric — formation order via normalised Kendall tau distance, content set via Jaccard distance, cross-reference structure via Jaccard distance over linkage pairs, and confirmation density via normalised L1 distance over per-flag-type vectors — with equal weighting committed in advance. Across all three run lengths and all six cost levels, the metric produces per-pair distances substantially exceeding the substantive-differentiation floor at every cell, with within-cell mean distances ranging from 0.32 to 0.53 against a threshold of 0.05. The criterion's across-vs-within ordering succeeds at 13 of 18 cells; in the remaining 5 cells, within-cell distances meet or exceed the across-cell aggregate. The per-component decomposition surfaces a substantive structural finding: three of the four metric components carry within-cell variation approximately equal to across-cell variation, with only confirmation density modestly stratifying by experimental condition. The records differentiate agent-individual structural variation that is largely orthogonal to the experimental conditions. Section 3.4 develops this finding directly.

The fourth is the Category δ pre-anticipated negative findings. Threat-flag confirmation density is structurally sparse, as the pre-registration committed (the present architecture's epistemic conditions for threat-flag confirmation are limited; the gating mechanism prevents most direct flag testing). Disconfirming-observations counts are dominated by zero across most flag types but reach exactly 1.0 for threat flags whose cells transform under v0.14 dynamics. Cross-reference completion rate is bounded by v0.14 transformation dynamics. All three were anticipated in the pre-registration and reported directly without aggregation across types.

### 1.5 Connection to the broader programme and the SICC trajectory

The v1.1 iteration is the first iteration of the post-v1.0 trajectory and the first operationalisation of an SICC commitment beyond what the v0.1–v0.14 arc had done implicitly. The SICC document (Baker, internal record, drafted alongside v0.13) specifies twelve cognitive-architecture commitments the agent must hold across substrates. The v1.0 architecture has weak or strong analogues for several of them — persistent threat flags as primitive provenance, competency-gated transformation as primitive earned extensibility, the four-action vocabulary and five cell types as implicit a priori schema — but none are fully operationalised at the cognitive-layer level the document specifies. v1.1 takes one commitment (provenance over beliefs, Commitment 4) and operationalises it concretely as record-writing on the existing flag structures.

The post-v1.0 trajectory has further phases reserved for subsequent iterations: explicit schema (operationalising SICC Commitment 1, the agent holds and can interrogate the structure of what it knows about); layered property structure (operationalising SICC Commitment 6, properties organised in direct/interactional/relational/temporal layers); reporting (operationalising SICC Commitment 11, the agent produces auditable accounts traceable through provenance to specific encounters); and substrate transposition (operationalising SICC Commitment 10, initially to richer simulated environments, subsequently to physical embodiment with the cognitive layer running on Raspberry Pi external to the robot, eventually to migration onto embedded compute). These phases are reserved. v1.1 operationalises only provenance.

The discipline of single-architectural-change-per-iteration that has held across the inheritance chain holds for v1.1. The architecture under v1.1 is v0.14 unchanged at the agent and world level; what is added is the parallel observer module that writes records as flag-state changes occur. The byte-identical preservation property that follows from this design choice is the strongest such property any iteration in the programme has demonstrated, and it is what makes Category α achievable at the resolution of the full 180-run batch rather than at the population-restricted resolution of v0.13 (Baker, 2026i, in preparation, Section 3.5).

The methodological discipline carries forward. Pre-registration before code. Matched-seed comparison across the inheritance chain. Single-architectural-change at the research-question level. Operational amendments rather than architectural ones, committed before reanalysis. The v1.1.1 amendment that specifies the Category γ metric operationalisation (Baker, 2026s) was committed before any Category γ analysis was performed on the v1.1 batch; the script that implements the metric is fully deterministic given the input CSVs and was written after the amendment but before any verdict was produced.

## 2. Methods

### 2.1 Environment and architecture

The environment and architecture are inherited from v0.14 (Baker, 2026m) unchanged. The 20×20 grid contains six cell types: frame cells form the impassable boundary; hazard cells are clustered in two groups (a three-cell cluster and a two-cell cluster) and pay scalar cost on entry until they undergo competency-gated transformation; attractor cells are six fixed locations carrying feature reward; neutral cells fill the passable interior; end-state cells are the v0.13 contribution, sampled at run start at a random neutral coordinate and activated when the v0.14-amended trigger fires; knowledge cells are the v0.14 contribution, formed from hazard cells when the agent's competency reaches each cell's pre-registered threshold from the permutation of {1, 2, 3, 4, 5}.

The agent operates under the three-phase developmental schedule inherited unchanged: prescribed acquisition (Phase 1), drive-based integration (Phase 2), and preference-weighted autonomy (Phase 3), with phase transitions at the deterministic completion of the boustrophedon path and at 60 per cent of total run length respectively. The threat layer (v0.10/v0.12 inherited), the mastery layer (v0.11.2 inherited), the end-state mechanism (v0.13/v0.14-amended), and the knowledge-cell mechanism (v0.14) all operate under their inherited specifications without modification.

v1.1 introduces no agent-side modification, no world-side modification, no new cell type, no new metric on the agent itself. The v1.1 architectural extension is contained entirely within a parallel observer module that writes records as flag-state changes occur, with read-only access to the agent and world. The agent is unaware of the observer's existence; the observer reads the agent's exposed state attributes.

### 2.2 The provenance record schema

Each formed flag acquires a provenance record at the moment of formation. The record holds five common fields:

`flag_set_step` — the integer step at which the flag transitioned from unset to set. For threat flags, this is the step at which FLAG_THRESHOLD entries accumulated under v0.10 dynamics or v0.12 signature-matching first-entry conversion fired. For mastery flags, this is the step of the third entry to the attractor cell. For knowledge-banking flags, this is the step of the third post-transition entry to the transformed cell. For end-state activation, this is the step at which the v0.14-amended trigger fired; for end-state banking, this is the step of first post-activation entry to the end-state cell.

`confirming_observations` — an integer count of post-formation observations consistent with the flag's continued correctness. Operationalised per flag type as specified in §2.3 below.

`last_confirmation_step` — the integer step at which the most recent confirming observation was recorded, or null if `confirming_observations` is zero.

`disconfirming_observations` — an integer count of observations that, under the v1.1 architecture's narrow semantics, fail to sustain the flag. Under the present architecture this count is zero for all flag types except threat flags whose cells undergo v0.14 transformation, in which case it is incremented exactly once per transformation event.

`last_observation_step` — the integer step at which the flag's underlying state was most recently observed, regardless of whether the observation was confirming or disconfirming.

Type-specific cross-reference fields capture the bidirectional linkage between threat flags and the knowledge-banking flags that derive from the same coordinate through v0.14 transformation. Threat flags acquire `transformed_at_step` (the step at which the cell underwent transformation) and `derived_knowledge_flag_id` (the identifier of the knowledge-banking flag that subsequently forms on the transformed cell). Knowledge-banking flags acquire `derived_from_threat_flag_id` (the identifier of the threat flag whose transformation produced the cell, or null for cells transformed before any threat flag formed).

### 2.3 Per-flag-type confirmation operationalisation

The four flag types are formed and sustained under different epistemic conditions in the present architecture, and the confirming-observations count operationalises differently for each. The pre-registration (§2.2) committed a per-flag-type operationalisation in advance of the batch:

For threat flags, three observation events count toward the confirming-observations count: a v0.12 signature-matching first-entry conversion at an adjacent cell of the same category as the flagged cell (which confirms the flag's category-membership prediction by extension); a forced entry to the flagged cell in the rare cases where the gating mechanism's exclusion of the flagged action leaves no other action available (which the architecture should record honestly when it occurs); and an observation of the flagged cell's persistence as a hazard cell across the developmental phase boundary from Phase 2 to Phase 3 (recorded as a confirmation that the cell has not been transformed under v0.14 dynamics). The third event is the most frequent and produces the bulk of the threat-flag confirming-observations counts.

For mastery flags, a confirming observation is a post-banking visit to the mastered attractor cell. The architecture's existing post-banking visit handling enforces the four mastery interventions (zero feature reward, cleared attraction bias, blocked preference accumulation, preference at zero) by construction; the visit is the confirmation. Mastery-flag confirmation is dense relative to threat-flag confirmation because the architecture does not gate against re-entry to mastered cells.

For knowledge-banking flags, the confirmation operationalisation is identical to mastery flags applied to the post-transition population.

For end-state activation, confirming observations are post-activation steps in which the all-attractors-mastered AND all-hazards-banked-as-knowledge condition continues to hold. Under the present architecture, neither condition can subsequently fail to hold (mastery flags do not retract; knowledge-banking flags do not retract); the count is therefore deterministically equal to the post-activation window length. The substantive information is in the formation step rather than the count, and the v1.1 paper reports this honestly. For end-state banking, confirming observations are post-banking visits to the end-state cell, operationally identical to mastery-flag confirmation.

The per-flag-type operationalisation is committed in advance and the v1.1 paper reports counts per flag type without aggregation across types, on the principle that a confirmation in one epistemic regime is not the same kind of evidence as a confirmation in another (pre-registration §2.2).

### 2.4 Cross-reference resolution

When a hazard cell with threat flag F undergoes v0.14 competency-gated transformation at step N, the threat flag's record acquires the `transformed_at_step` value N, the `derived_knowledge_flag_id` field is set to the identifier the eventual knowledge-banking flag K will carry (constructible from the cell's coordinate before K exists), and the disconfirming-observations count is incremented by one. The transformation event is the only event under v1.1's narrow semantics that increments any flag's disconfirming-observations count.

When the knowledge-banking flag K subsequently forms on the transformed cell at step M (M > N, after the third post-transition entry), K's record acquires the back-reference `derived_from_threat_flag_id = F.flag_id` if F exists in the records (i.e. the cell was threat-flagged before transformation). F's `derived_knowledge_flag_id` placeholder is updated from the placeholder to the resolved K identifier at the same moment.

Cells that undergo transformation without prior threat-flag formation produce knowledge-banking records with `derived_from_threat_flag_id = null`; the null case is recorded explicitly as an epistemic state worth preserving (pre-registration §2.4, on the SICC-honest slot-existence principle).

### 2.5 Implementation as a parallel observer module

The v1.1 implementation is contained in `v1_1_provenance.py`, a parallel observer module modelled on the v1.0 instrumentation pattern (`v1_0_recorder.py`). The module exposes three hook methods called by the v1.1 batch runner (`curiosity_agent_v1_1_batch.py`) at three points in the agent's main loop: `on_pre_action(step)` immediately before action selection, `on_post_event(step)` after `record_action_outcome` completes, and `on_run_end(step)` once at end-of-run. The module's hook handlers detect flag-formation events by comparing the agent's current state against the store's recorded flags, create new provenance records when newly-formed flags are detected, increment confirming-observations counts where the per-flag-type confirmation logic fires, and handle cross-reference resolution when a v0.14 transformation event is observed.

The module does not modify the agent or the world. The architecture under v1.1 is byte-identical to v1.0 with the module either instantiated or not; what differs is what gets written to disk. The v1.1 batch runner operates two parallel observer modules in series (the v1.0 recorder and the v1.1 provenance store), each receiving hook calls at the same points and writing to its own output files.

### 2.6 Pre-flight verifications

The pre-registration (§6) committed two pre-flight verifications, both run before the v1.1 batch.

Level 1, byte-identical preservation against v0.14 baseline with all instrumentation disabled (`verify_v1_1_disabled.py`): the v1.1 batch runner with both the v1.0 recorder suppressed (`--no-instrument`) and the v1.1 provenance store suppressed (`--no-provenance`) produces output bit-for-bit identical to v0.14 baseline at matched seeds. This confirms that the parallel observer modules genuinely do not interfere with the agent's RNG state, computation, or output when not instantiated. The verification ran on 10 matched-seed runs at cost 1.0, 20,000 steps; result: 10 of 10 runs match v0.14 baseline byte-for-byte.

Level 2, byte-identical preservation against v1.0 baseline with v1.0 instrumentation enabled but v1.1 provenance disabled (`verify_v1_1_no_provenance.py`): the v1.1 batch runner with v1.0 instrumentation active (`--no-provenance` only) produces output bit-for-bit identical to v1.0 baseline at matched seeds. This is the permanent regression test the pre-registration committed to keeping in the verification pipeline, catching future drift if subsequent iterations couple to provenance state. The verification ran on the same 10 matched-seed runs; result: 10 of 10 runs match v1.0 baseline byte-for-byte.

Both verifications passing was the precondition for the v1.1 batch to run.

### 2.7 Experimental matrix and matched-seed comparison

The experimental matrix matches the v1.0 batch: one architecture (v1.1) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with three run lengths (20,000, 80,000, 160,000 steps) crossed with ten runs per cell, totalling 180 runs.

For each (cost, run length, run index) triple, the random seed is matched to the v1.0 batch (Baker, 2026q, in preparation), which itself matched v0.14, v0.13, v0.12, v0.11.2, and v0.10 at the same conditions. Seeds are loaded from `run_data_v1_0.csv` rather than regenerated. The seed chain links every iteration of the inheritance arc at every (cost, run length, run index) cell.

The matched-seed comparison produces a within-seed comparison at byte-identical resolution for v1.0-visible metrics, because the v1.1 architectural extension introduces no behavioural modification. Every action the agent takes under v1.1 at a given seed is identical to the action it takes under v1.0 at the same seed; the two architectures diverge only in what they hold about their own state, not in what they do.

### 2.8 Metrics

All v1.0 metrics are retained unchanged. v1.1 adds per-run aggregate provenance metrics to the per-run CSV: per-flag-type counts of formed flags, mean of formation step per flag type, mean of confirming-observations per flag type, mean of disconfirming-observations per flag type, count of cross-referenced flag pairs (resolved and pending), and the formation narrative as an ordered "step:flag_id" tuple. The full per-flag formation records are written to a separate provenance CSV (`provenance_v1_1.csv`) with one row per formed flag per run; the v1.1 snapshot CSV (`snapshots_v1_1.csv`) records snapshots at flag-formation events plus end-of-run.

### 2.9 Pre-registered interpretation categories

Five interpretation categories are pre-registered in the v1.1 pre-registration (Baker, 2026r, §5): α preservation, β alignment, γ record-scale individuation, δ negative findings, Φ honesty constraint, plus Ω the architectural-statement claim. Section 3 reports against each category in turn. The Category γ structural-distance metric is specified in the v1.1.1 amendment (Baker, 2026s) and computed by the analysis script `analyse_v1_1_category_gamma.py`.

## 3. Results

### 3.1 Category α: byte-identical preservation across the full batch

Both pre-flight verifications passed before the batch ran: Level 1 at 10 of 10 runs against v0.14 baseline, Level 2 at 10 of 10 runs against v1.0 baseline. The pre-registered preservation property holds: with the v1.1 architectural extension introducing no behavioural modification, the agent's behaviour under v1.1 is byte-identical to the relevant baseline at matched seeds.

The full 180-run batch confirms preservation through internal consistency. Every coupling between a v1.0 metric field and the corresponding v1.1 provenance count holds at 180 of 180 runs:

- `attractors_mastered` equals `prov_mastery_count` in 180 of 180 runs.
- `hazards_banked_as_knowledge` equals `prov_knowledge_banking_count` in 180 of 180 runs.
- `hazards_flagged` equals `prov_threat_count` in 180 of 180 runs.
- A non-null `activation_step` corresponds to `prov_end_state_activation_count` of 1 in 180 of 180 runs.
- `end_state_banked` is True if and only if `prov_end_state_banking_count` is non-zero in 180 of 180 runs.

The provenance store is observing exactly what the v0.14 architecture produces, with no double-counting, no skipped events, and no spurious records. Combined with the byte-identical pre-flight verifications, Category α is comprehensively satisfied.

### 3.2 Category β: cross-reference structure resolves cleanly

The v1.1 architectural extension introduces bidirectional cross-references between threat flags and the knowledge-banking flags that derive from the same coordinate through v0.14 transformation. Across the 180-run batch, the cross-reference structure resolves as follows:

- 165 threat-flag records have `transformed_at_step` set (i.e. the cell underwent v0.14 transformation during the run).
- Of these, 160 have `derived_knowledge_flag_id` resolved to a knowledge-banking record that exists in the same run; the remaining 5 are pending (the cell transformed but the knowledge-banking flag had not yet formed by end-of-run).
- Of the 165, zero have an inconsistent missing identifier (the placeholder is set in every transformation event, even when the placeholder remains pending).

Knowledge-banking back-references resolve identically: 160 knowledge-banking records carry a non-null `derived_from_threat_flag_id`, all of which resolve to threat-flag records that exist in the same run. Bidirectional consistency is exact: 160 of 160 forward references match a corresponding back-reference, with zero unidirectional anomalies.

The five pending cross-references all occur at the 20,000-step run length. This is the expected pattern: at the shorter run length, some cells transform too late in the run for the three post-transition entries required for knowledge-banking to complete before the run ends. At 80,000 and 160,000 steps, no pending cross-references occur — every transformation that fires has its derived knowledge-banking flag form before end-of-run. The bookkeeping logic operationalises the §2.4 specification correctly across the full batch.

### 3.3 Activation rate, formation rate, and the inheritance ceiling

The v1.1 architectural extension introduces no modification to the conditions under which flags form. The flag-formation distribution under v1.1 is therefore the v1.0 inheritance distribution, which is in turn the v0.14 inheritance distribution. Table 1 summarises the per-run-length distribution.

**Table 1.** v1.1 per-run-length flag formation summary. Activation count and end-state banking count are bounded above by the rate at which the v0.14-amended trigger fires (all-attractors-mastered AND all-hazards-banked-as-knowledge). Mastery and knowledge-banking counts are bounded above by the cell counts in the environment (six attractors, five hazards).

| Run length | n | Activated | End-state banked | Full mastery | Full knowledge banking | Total records |
|------------|---|-----------|------------------|--------------|------------------------|---------------|
| 20,000     | 60 | 17 | 10 | 19 | 26 | 579 |
| 80,000     | 60 | 45 | 39 | 46 | 51 | 768 |
| 160,000    | 60 | 53 | 51 | 54 | 59 | 832 |

The activation rate scales with run length, as the inheritance from v0.13 / v0.14 dynamics predicts. End-state banking is bounded above by activation. Total record counts (sum across all flag types for all runs at a given run length) grow with run length but level off at the longer horizons because most flag-formation events are bounded by the architectural completion conditions.

### 3.4 Category γ: record-scale individuation

The Category γ structural-distance metric (specified in the v1.1.1 amendment, Baker, 2026s) was computed for all 180 × 179 / 2 = 16,110 unordered agent pairs in the batch. The metric has four components — formation order via normalised Kendall tau distance, content set via Jaccard distance, cross-reference structure via Jaccard distance over linkage pairs, and confirmation density via normalised L1 distance over per-flag-type vectors — combined with equal weighting. The composite distance lies in [0, 1].

Per-(cost, run length) cell within-cell statistics are summarised in Table 2.

**Table 2.** Per-(cost, run length) cell within-cell pairwise structural distance (45 pairs per cell). The within-cell mean substantially exceeds the substantive-differentiation floor of 0.05 at every cell. The standard deviation exceeds 0.02 at every cell, comprehensively passing the v1.1.1 amendment's diversity criterion.

| Cost | Steps   | n  | Mean  | Std   | Min   | Max   |
|------|---------|----|-------|-------|-------|-------|
| 0.1  | 20,000  | 45 | 0.526 | 0.109 | 0.229 | 0.709 |
| 0.1  | 80,000  | 45 | 0.472 | 0.102 | 0.134 | 0.616 |
| 0.1  | 160,000 | 45 | 0.480 | 0.111 | 0.178 | 0.649 |
| 0.5  | 20,000  | 45 | 0.441 | 0.166 | 0.133 | 0.764 |
| 0.5  | 80,000  | 45 | 0.363 | 0.156 | 0.118 | 0.600 |
| 0.5  | 160,000 | 45 | 0.443 | 0.084 | 0.157 | 0.555 |
| 1.0  | 20,000  | 45 | 0.320 | 0.124 | 0.090 | 0.600 |
| 1.0  | 80,000  | 45 | 0.506 | 0.108 | 0.178 | 0.729 |
| 1.0  | 160,000 | 45 | 0.470 | 0.108 | 0.165 | 0.642 |
| 2.0  | 20,000  | 45 | 0.428 | 0.172 | 0.072 | 0.688 |
| 2.0  | 80,000  | 45 | 0.448 | 0.172 | 0.116 | 0.718 |
| 2.0  | 160,000 | 45 | 0.456 | 0.104 | 0.155 | 0.643 |
| 5.0  | 20,000  | 45 | 0.470 | 0.169 | 0.175 | 0.872 |
| 5.0  | 80,000  | 45 | 0.481 | 0.149 | 0.144 | 0.677 |
| 5.0  | 160,000 | 45 | 0.439 | 0.138 | 0.124 | 0.629 |
| 10.0 | 20,000  | 45 | 0.372 | 0.135 | 0.155 | 0.701 |
| 10.0 | 80,000  | 45 | 0.490 | 0.124 | 0.149 | 0.663 |
| 10.0 | 160,000 | 45 | 0.459 | 0.128 | 0.127 | 0.657 |

The across-cell aggregate (computed over all 15,300 inter-cell pairs) is mean = 0.479, std = 0.147.

The pre-registered Category γ verdict has two criteria. The first criterion (within-cell mean ≥ 0.05 AND across-cell distance > within-cell distance) succeeds at 13 of 18 cells: every cell exceeds the 0.05 floor by a factor of 6 to 10, but in 5 of 18 cells the within-cell mean meets or exceeds the across-cell aggregate (cost 0.1 at 20k, cost 1.0 at 80k, cost 5.0 at 80k, cost 10.0 at 80k, plus one borderline). The second criterion (standard deviation ≥ 0.02 in at least 4 cells) succeeds comprehensively, with all 18 cells exceeding the threshold.

Per-component decomposition surfaces a substantive structural finding the criterion as written did not anticipate. Table 3 reports the four components separately, comparing within-cell and across-cell means.

**Table 3.** Per-component decomposition of the structural-distance metric. The across-vs-within ratio measures how strongly each component stratifies by experimental condition. d_conf is the only component with a substantial ratio above 1; the other three components carry within-cell variation approximately equal to across-cell variation.

| Component       | Within-cell mean | Across-cell mean | Ratio  |
|-----------------|------------------|------------------|--------|
| d_order         | 0.353            | 0.357            | 1.011  |
| d_content       | 0.341            | 0.356            | 1.044  |
| d_xref          | 0.700            | 0.731            | 1.045  |
| d_conf          | 0.399            | 0.474            | 1.188  |
| **d_composite** | **0.448**        | **0.479**        | **1.070** |

The pattern is clean. Three of the four components — formation order, content set, cross-reference structure — show within-cell variation that is approximately equal to across-cell variation. Only confirmation density carries a substantive across-vs-within ratio, and that is the component most directly tied to run length and cost mechanics: longer runs produce more post-formation confirmations, higher costs alter the agent's exposure pattern to cells, and these together stratify the confirmation-density distribution by experimental condition. The other three components are largely orthogonal to the experimental conditions.

The substantive interpretation: the records carry agent-individual structural variation that is largely orthogonal to the experimental conditions. Two agents at matched seeds within the same (cost, run length) cell produce records as structurally different from each other as two agents at completely different conditions — except in the confirmation-density dimension, where the experimental conditions modestly stratify. The architectural extension v1.1 introduces produces records whose structural variation reflects the agent's individual traversal of the prepared environment more than the parameters of the run.

This is the substrate-as-individuation finding the iteration was designed to test, surfaced in a sharper form than the criterion anticipated. The pre-registration's first criterion was framed against the assumption that experimental conditions would stratify the distribution clearly enough that within-cell variation would be a fraction of across-cell variation. The actual finding is that within-cell and across-cell variation are comparable in magnitude, which means the records differentiate agents *more strongly than the experimental conditions stratify them*. The criterion as written reads partial pass; the substantive reading is that the records exceed what the criterion was designed to test for.

Per the pre-registration's §5.3 and the v1.1.1 amendment's §6 honest-reporting commitments, the partial-pass verdict is reported directly here without post-hoc threshold revision. The substantive finding sits alongside it: the records substantively differentiate every agent from every other agent in the batch (every within-cell mean is six to ten times the substantive-differentiation floor), and the differentiation is approximately as strong within experimental conditions as across them.

### 3.5 Category δ: pre-anticipated negative findings

The pre-registration committed three categories of negative finding to honest reporting (§5.4). All three landed as anticipated.

**Sparse threat-flag confirmation.** The threat-flag confirming-observations count under the present architecture's epistemic conditions is structurally sparse. Mean threat-flag confirming counts across runs with at least one threat flag formed: 0.7 at 20k, 0.4 at 80k, 0.4 at 160k. The architecture's gating mechanism prevents most direct flag testing; the three confirmation events the pre-registration committed (signature-matching at adjacent same-category cells, forced entry, phase-boundary persistence) do not fire frequently enough to produce dense confirmation counts. The v1.1 paper reports this directly: threat-flag confirmation under the present architecture is structurally limited; the count is not the substantive carrier of provenance information for this flag type. The formation step and the cross-reference structure are.

**Disconfirming-observations counts dominated by zero.** Under the v1.1 narrow semantics (§2.3), the disconfirming-observations count is non-zero only for threat flags whose cells undergo v0.14 transformation. Across the 180-run batch, 165 threat-flag records have non-zero disconfirming counts, and the value is exactly 1.0 in every case. Mean disconfirming counts across all flag types are zero in 180 of 180 runs except for threat flags whose cells transform. This is the expected outcome under the narrow semantics; the slot's existence is the substantive architectural commitment, not the slot's frequent population.

**Cross-reference completion rate bounded by v0.14 dynamics.** Cross-reference completion rate is bounded above by the rate at which flagged hazard cells transform to knowledge cells and subsequently bank within the run length. The 160 of 165 resolution rate represents the achievable completion under the v0.14 inheritance. The 5 pending cases all occur at 20,000 steps; at 80,000 and 160,000 steps every transformation that fires resolves to a banked knowledge cell within the run. The v1.1 paper reports the rate against the v0.14 baseline rather than against an architectural ideal.

### 3.6 Category Φ: the honesty constraint

The Category Φ constraint (pre-registration §5.6) bounds the architectural claim made in any v1.1 paper. The records v1.1 introduces are the substrate for an eventual self-account; whether the substrate is sufficient for the eventual self-account is not directly demonstrated by the v1.1 batch.

The substantive reading: the records hold the structural information necessary for the agent, in subsequent iterations, to give an account of its own learning that is auditable, traceable through provenance to specific encounters, and individuated in ways v1.0 individuation could not surface. The Category γ finding (Section 3.4) supports this reading by demonstrating that the records carry agent-individual structural variation at the per-pair level.

The deflationary reading: the records hold formation timestamps, confirmation counts, and cross-reference identifiers; whether subsequent iterations can construct a self-account from these primitives is an open question, and v1.1 establishes only that the primitives exist.

Both readings are consistent with the v1.1 batch. The reporting iteration that subsequently realises Commitment 11 of the SICC framework is the methodological vehicle for distinguishing them. v1.1's contribution is that the substrate exists in the form the pre-registration committed to, with the architectural property that subsequent iterations need: bidirectional cross-references that constitute learning narratives rather than collections of independent records, per-flag-type confirmation operationalisations honest about epistemic differences across flag types, and individuation at the record scale that surfaces in matched-seed comparison without behavioural modification.

The Category Φ constraint is operative throughout the discussion that follows.

## 4. The substantive Category γ finding and the Montessori parallel

The Category γ partial-pass-with-stronger-finding is the load-bearing result of the iteration. This section develops the finding directly, on the principle that a partial-pass verdict combined with a substantive finding richer than the criterion anticipated requires careful presentation: neither the partial-pass framing nor the substantive finding alone tells the full story.

### 4.1 The finding restated in plain terms

The pre-registered structural-distance metric was designed to test whether the records v1.1 introduces carry enough structural information to differentiate agents at the per-pair level. The expected pattern, against which the criteria were calibrated, was that experimental conditions (cost and run length) would stratify the formation-narrative distribution clearly enough that within-cell pairwise distances would be a fraction of across-cell pairwise distances. Under this expectation, the criterion's across-vs-within ordering would pass robustly, and the substantive finding would be that the records differentiate agents.

The actual data shows two things simultaneously. First, the records substantively differentiate agents at the per-pair level — every within-cell mean is six to ten times the substantive-differentiation floor of 0.05. The substantive differentiation is comprehensively present. Second, the experimental conditions do not strongly stratify the distribution. Within-cell pairwise distances are approximately equal to across-cell pairwise distances; in 5 of 18 cells they meet or exceed the across-cell aggregate.

The finding is that the records carry agent-individual structural variation that is largely orthogonal to the experimental conditions. The cost level and the run length set the parameters of the experiment; the agent's traversal within those parameters reflects the individual agent's encounter sequence and produces a formation narrative that is structurally distinct from every other agent's, regardless of whether those other agents share the same parameters or not.

### 4.2 The per-component decomposition refines the reading

The four components of the structural-distance metric measure four different aspects of formation-narrative structure (pre-registration §5.3, v1.1.1 amendment §2). Three of the four show within-cell variation approximately equal to across-cell variation; only one shows experimental-condition stratification.

`d_order` (formation-order distance) measures whether two agents formed the same flags in different orders. Within-cell mean 0.353; across-cell mean 0.357; ratio 1.011. Two agents at matched seeds form their flags in different orders almost as often as two agents at completely different conditions. The order in which the agent encounters and processes the prepared environment is largely an agent-individual property rather than a parameter-driven one.

`d_content` (content-set distance) measures whether two agents formed different sets of flags. Within-cell mean 0.341; across-cell mean 0.356; ratio 1.044. Which flags formed at all differs between agents within a cell almost as much as between agents across cells. Some agents form threat flags on hazard cells before competency thresholds fire; some do not. The pattern is largely agent-individual.

`d_xref` (cross-reference structure distance) measures whether two agents have different threat-flag-to-knowledge-banking-flag linkage structures. Within-cell mean 0.700; across-cell mean 0.731; ratio 1.045. This is the highest within-cell mean of any component, with median within-cell distance at 1.0 — meaning more than half of within-cell pairs share zero cross-reference items in common. The cross-reference structure differentiates agents most strongly of all the components, and it differentiates within cells almost as much as across cells.

`d_conf` (confirmation-density distance) measures whether two agents differ in how their flags were sustained. Within-cell mean 0.399; across-cell mean 0.474; ratio 1.188. This is the only component with a substantive across-vs-within ratio, and it is the component most directly tied to run length and cost mechanics: longer runs produce more post-formation confirmations, and the cost level affects the agent's exposure pattern to cells.

The pattern is clean. Three of four components — formation order, content set, cross-reference structure — are largely agent-individual; one component — confirmation density — is partly experimental-condition-driven. The composite metric averages these four with equal weight, producing the modest 1.070 across-vs-within ratio that triggered the partial pass on criterion 1.

### 4.3 The Montessori parallel made operative

The design conversation that preceded the v1.1 pre-registration drafting (Baker, internal record, 28 April 2026) named the Montessori parallel as the developmental purpose the records serve. In a Montessori-prepared environment the materials are arranged so that the child's own choices about what to engage with, in what order, produce a learning sequence that is the child's rather than the teacher's. The route the child takes through the prepared environment becomes part of what the child knows about themselves.

The Category γ finding makes this parallel operative in the architecture's own terms. The prepared environment under v0.14 is the same across runs at the same parameters (cost, run length, seed): the same 20×20 grid, the same hazard clusters, the same attractors, the same competency-threshold permutation under matched seeds. What differs across runs at matched parameters is the agent's traversal — the order in which the agent encounters cells, the points at which the agent's competency builds, the sequence in which transformation events fire relative to threat-flag formation events. The records carry the trajectory.

The three-trajectory-pattern observation surfaced in the batch's Section 3.2 cross-reference statistics is the same finding from a different angle. The 97 runs with at least one resolved threat-to-knowledge cross-reference are agents whose trajectory included learning to avoid before learning to engage. The 70 runs with knowledge formations but no threat flags are agents whose competency outpaced their threat-flag formation. The 13 runs with threat flags but no transformations are agents whose run length truncated the trajectory before the relevant competency thresholds fired. These are not three architectural states; they are three windows onto the same underlying developmental trajectory at different points of progression.

The Category γ finding makes the further claim that even within the same window — even at matched parameters and matched seeds — the agents' formation narratives are structurally distinct. The trajectory through the prepared environment is what the agent did individually, and the records carry the doing.

### 4.4 What this finding does not claim

Three clarifications worth naming explicitly here, on the SICC-honest principle that what the finding does not claim is part of what the finding is.

The finding does not claim that the records constitute a self-account. The agent does not yet read its own records under v1.1; what the records will support when subsequent iterations enable agent-side reading is the open question Category Φ reserves. The substantive Category γ result is about the records' structural content, not about what the agent can do with that content.

The finding does not claim that the experimental conditions are uninformative. The d_conf component shows that confirmation density does stratify modestly by experimental condition, and the per-cell statistics in Table 2 show some variation in within-cell mean across cells. The claim is that the conditions do not stratify the formation-narrative distribution as strongly as agent-individual variation does — not that they fail to stratify at all.

The finding does not claim that the equal-weighting choice in the metric is the optimal one. The v1.1.1 amendment committed to equal weighting in advance to avoid post-hoc tuning, on the methodological principle that weighting after seeing the data is exactly the kind of analysis the pre-registration discipline exists to prevent. If subsequent iterations introduce different cognitive operations on the records (the reporting iteration in particular), the weighting that best reflects the agent's read of the records may turn out to differ from equal weighting; that is a question for subsequent iterations to answer, not a question the v1.1 paper takes a position on.

### 4.5 The finding's methodological implication for subsequent iterations

The Category γ finding has one methodological implication worth naming for subsequent iterations.

The pre-registration's first criterion was calibrated against the implicit assumption that experimental conditions would stratify the formation-narrative distribution. The data shows they do not, in three of the four metric components. This is the kind of mistake the v0.13 paper named in its Section 5.4: pre-registered thresholds calibrated against an implicit model of the data that the actual data does not match. The v0.13 paper named the lesson as: pre-registered thresholds for an iteration's operational success should be tied to the inheritance distribution where the iteration's mechanism is bounded by inherited dynamics. The v1.1 paper carries the lesson forward in a new form: pre-registered thresholds that depend on assumed stratification structure should be calibrated against the inheritance distribution's actual stratification, which may or may not match the assumed structure.

The methodological discipline the partial pass demonstrates is the lesson's operative test. The pre-registered criterion is reported against the data as committed; the substantive finding is reported alongside; no post-hoc threshold revision is performed. Subsequent iterations that introduce metrics with stratification-dependent criteria should calibrate the criteria against the v1.1 distribution where applicable.


## 5. Discussion

### 5.1 Provenance as architectural object: what the records change

The architectural principle the v1.1 result demonstrates is bounded but identifiable. The architecture's flag structures, inherited from v0.10 (threat), v0.11.2 (mastery), v0.13 (end-state activation and banking), and v0.14 (knowledge-banking), can be transformed from binary states into records of their own formation through a parallel observer module that introduces no behavioural modification. The records carry formation step, confirming-observations counts under per-flag-type operationalisations, last-confirmation step, disconfirming-observations counts under narrow semantics, and bidirectional cross-references between threat flags and the knowledge-banking flags that derive from the same coordinate through v0.14 transformation. With both pre-flight verifications passing at byte-identical resolution against the v0.14 and v1.0 baselines, the architectural property the iteration was designed to demonstrate is in place: the move from flag-as-state to flag-as-record can be made on the existing primitives without disturbing the agent's behaviour.

What the records change at the architectural level is the kind of object the architecture holds. Under v1.0, a threat flag is a switch the agent's gating mechanism consults; the switch's history is not part of the system. Under v1.1, the threat flag is a record of which the switch state is one queryable property. The record carries the conditions of its own formation, the observations that have sustained it, the events (notably v0.14 transformation) that have rendered its prediction structurally untestable in its original form, and the cross-reference to the knowledge-banking flag that subsequently formed on the same cell. The record is the architectural object; the binary state is the answer to one question the record could be asked.

This framing matters for the iterations that follow. The reporting iteration that operationalises SICC Commitment 11 (the agent's report is auditable, traceable through provenance to specific encounters) does not need to reconstruct the records' meaning from their fields. It reads the records directly, queries the cross-references to recover learning narratives, and produces accounts whose origins are traceable to specific formation events. The schema iteration that operationalises SICC Commitment 1 (the agent holds and can interrogate the structure of what it knows about) does not need to invent a separate representation of what the records contain; the records are themselves the substrate the schema interrogates. The v1.1 records' design — bidirectional cross-references that constitute learning narratives rather than collections of independent records, per-flag-type confirmation operationalisations honest about epistemic differences across flag types, slot-existence even where semantics are deferred — is what makes these subsequent iterations buildable as extensions rather than requiring schema rebuilds.

### 5.2 The Category γ finding and what individuation at the record scale means

The Category γ finding (Section 3.4 and the development in Section 4) is the load-bearing substantive result of the iteration. The records carry agent-individual structural variation that is largely orthogonal to the experimental conditions: every within-cell mean exceeds the substantive-differentiation floor by a factor of six to ten, and three of the four metric components show within-cell variation approximately equal to across-cell variation. The architectural extension v1.1 introduces produces records whose structural content reflects the agent's individual traversal of the prepared environment more than the parameters of the run.

The v1.0 paper documented biographical individuation at trajectory-and-completion scale: agents differ in what they did and when, and those differences are visible in the v1.0 metrics. v1.1's record-scale individuation is a different kind of finding. It is not that agents differ in their behaviour (they may, modulo the cross-layer effects v0.13 documented; or they may not, under matched seeds where pre-activation behaviour is byte-identical). It is that the records the agents produce — the formation narratives that capture what the agent has learned, when, in what order, with what cross-references and what confirmation patterns — carry structural distinctions that v1.0 individuation could not surface. Agents at matched seeds within the same (cost, run length) cell, whose v1.0-visible behaviour is byte-identical or close to it, produce records that differ from each other approximately as much as records produced by agents at completely different conditions.

This is the substrate-as-individuation property the v1.1 iteration was designed to test. The records do not merely describe the agent's behaviour; they constitute a different kind of differentiation between agents, visible at the per-pair level through structural-distance computation. Two agents that mastered the same six attractors and banked the same five hazard cells in the same v1.0-visible terms can have produced these outcomes through structurally distinct formation narratives — different orders of formation, different cross-reference patterns, different confirmation densities — and the records carry the difference.

The Montessori parallel made operative in Section 4.3 captures the developmental significance of this finding. The prepared environment is the same across runs at matched parameters; what differs is the agent's traversal, and the records carry the trajectory. The finding is consistent with the SICC document's Commitment 8 (self-knowledge as derivative of object-knowledge): the agent eventually knows itself through patterns in how it engaged with what is not itself, and the records are the architectural substrate from which those patterns will be readable. v1.1 establishes the substrate; subsequent iterations make it readable.

### 5.3 The honesty constraint applied: the substantive vs deflationary readings

The Category Φ honesty constraint (Section 3.6) bounds the architectural claim made in this paper in a specific way that is worth developing.

The substantive reading is that the records hold the structural information necessary for the agent, in subsequent iterations, to give an account of its own learning that is auditable, traceable through provenance to specific encounters, and individuated in ways v1.0 individuation could not surface. The Category γ finding supports this reading: the records carry agent-individual structural variation comprehensively distributed across the batch, and the cross-reference structure provides the linkage that turns independent records into learning narratives. If the substantive reading is correct, the records are sufficient as a foundation for the reporting iteration to construct genuine self-accounts, and the schema and layered-property iterations have a substrate to build on.

The deflationary reading is that the records hold formation timestamps, confirmation counts, and cross-reference identifiers — primitives whose adequacy for self-account construction is an open question. Under this reading, the v1.1 finding is that the primitives exist; whether they are sufficient is for subsequent iterations to demonstrate. The deflationary reading is supported by the observation that the v1.1 architecture does not yet read its own records, does not yet act on differently-provenanced flags differently, and does not yet produce any output the agent itself could be said to author. The records are written; the agent has no engagement with them.

Both readings are consistent with the v1.1 batch. The reporting iteration that subsequently realises Commitment 11 of the SICC framework is the methodological vehicle for distinguishing them. Under the reporting iteration, the agent acquires a thin layer over the provenance store that produces auditable accounts when queried; the test of the substantive vs deflationary reading is whether those accounts have the qualities the SICC document specifies — traceability through provenance to specific encounters, accuracy, the kind of self-report that invites scrutiny rather than oracular pronouncement. If the reports have these qualities, the substantive reading gains support. If they do not — if the records turn out to require richer primitives than v1.1 introduces, or if the agent's read of them produces accounts that are formally complete but substantively hollow — the deflationary reading is supported and the v1.1 substrate would need extension.

The v1.1 paper does not anticipate the reporting iteration's findings. The architectural claim made here is bounded: v1.1 establishes that the substrate exists in the form the pre-registration committed to, with the architectural property that subsequent iterations need. Whether the substrate is sufficient for the eventual self-account is reserved.

This bounding has a parallel to the v0.13 paper's Category F honesty constraint: the locating capability v0.13 demonstrated was performed by inherited Phase 3 dynamics rather than by v0.13-specific addition, and the architectural claim was bounded accordingly. The v1.1 Category Φ constraint operates on the same structural principle. The records v1.1 produces are real architectural objects; what the agent will eventually do with them is the question the next iteration in the trajectory addresses.

### 5.4 The partial-pass verdict and what it teaches about pre-registration calibration

The Category γ partial pass (Sections 3.4 and 4) is a methodologically significant outcome that warrants direct discussion as a finding in its own right.

The pre-registered first criterion required within-cell mean ≥ 0.05 (the substantive-differentiation floor) AND across-cell distance > within-cell distance (the experimental-condition stratification). The data shows the first half of the criterion satisfied comprehensively — every within-cell mean is six to ten times the floor — and the second half satisfied at 13 of 18 cells. The 5 cells where the second half fails are not isolated outliers; they include two of the three run lengths at multiple cost levels, suggesting that the within-vs-across stratification the criterion assumed is genuinely weaker than the calibration anticipated.

The mistake in the calibration was not the substantive-differentiation floor (which the data exceeds by an order of magnitude) but the across-vs-within ordering as a binary criterion. The criterion assumed that experimental conditions would stratify the formation-narrative distribution clearly enough that across-cell distances would dominate within-cell distances by a comfortable margin. The actual data shows the two are comparable in magnitude — the records differentiate agents approximately as strongly within cells as across them. This is the substantive finding the criterion was not designed to surface.

The v0.13 paper named the analogous mistake (Section 5.4) as: pre-registered thresholds for an iteration's operational success should be tied to the inheritance distribution where the iteration's mechanism is bounded by inherited dynamics. The v1.1 lesson is a structural cousin: pre-registered criteria that depend on assumed stratification structure should be calibrated against the inheritance distribution's actual stratification, not against an implicit model of how the data ought to be structured. The v1.1.1 amendment specified the metric and the criteria before the records existed to be examined; the discipline is intact. What the partial pass teaches is that even disciplined pre-registration can produce criteria that the data exceeds in ways the criteria were not designed to capture.

The disciplined response to this is the one the paper takes. The partial pass is reported against the criterion as committed. The substantive finding — that the records carry agent-individual variation comparable in magnitude to experimental-condition variation — is reported alongside without post-hoc threshold revision. Subsequent iterations that introduce metrics with stratification-dependent criteria should calibrate against the v1.1 distribution where applicable; the inheritance-aware threshold-calibration discipline (a methodological commitment that has been operative since the v0.13 paper) extends naturally to stratification-aware criterion calibration.

The methodological lesson generalises forward to the iterations the SICC trajectory reserves. The reporting iteration will need a metric for the auditability of the agent's self-accounts; the schema iteration will need a metric for the agent's capacity to interrogate its schema; the layered-properties iteration will need metrics for distinguishing direct, interactional, relational, and temporal properties. Each of these will be calibrated against an implicit model of how the data ought to be structured, and each calibration may turn out to misread the actual data structure. The v1.1 partial-pass-with-stronger-finding outcome is the methodological case the programme can refer back to: report the verdict honestly, develop the substantive finding alongside, do not retrofit thresholds.

### 5.5 The parallel-observer pattern and the byte-identical preservation property

The implementation pattern v1.1 uses — a parallel observer module modelled on the v1.0 instrumentation pattern, with the agent and world unmodified — is worth naming as a methodological contribution beyond the substantive provenance finding.

Prior iterations in the programme introduced architectural extensions that touched the agent or the world directly. v0.10 added the threat layer to the agent. v0.11 modified the agent's preference accumulation, feature reward, and primitive bias mechanisms. v0.12 added signature-matching to the threat layer's flag-conversion logic. v0.13 introduced a new cell type, the activation signal, and the cell-type transition. v0.14 added the competency-gated transformation mechanism with its associated metrics and timing fields. Each iteration's preservation property required either restricting the comparison to populations where the architectural extension did not fire (v0.13's Check 4a as amended by v0.13.1) or characterising the cross-layer effects the extension produced (v0.12's threat-side cleanness improvement, v0.13's cross-layer encounter effect).

v1.1 introduces an architectural extension that touches neither the agent nor the world. The records are written by a parallel observer that reads the agent's exposed state attributes and produces output to disk; the agent is unaware of the observer's existence. This design choice produces the strongest preservation property any iteration in the programme has demonstrated: byte-identical behaviour across the full 180-run batch under matched seeds, against both the v0.14 baseline (with all instrumentation disabled) and the v1.0 baseline (with v1.0 instrumentation enabled and v1.1 provenance disabled).

The pattern has implications for subsequent iterations that go beyond v1.1's specific extension. Architectural extensions that can be implemented as parallel observers — extensions that require the architecture to *record* something rather than to *do* something — inherit the byte-identical preservation property by construction. Extensions that require the agent to act on the records (the reporting iteration, the predict-and-surprise iteration) will not inherit this property; they will need to characterise their preservation in the v0.13 / v0.14 mode (population restriction or cross-layer effect characterisation). The methodological discipline accommodates both modes; the parallel-observer pattern is the cleaner one, and the programme should reach for it whenever the iteration's research question permits.

The level-2 verification (`verify_v1_1_no_provenance.py`), committed as a permanent regression test in the verification pipeline, operationalises the methodological commitment to preserving the parallel-observer pattern's preservation property. If a subsequent iteration accidentally couples the v1.0 instrumentation to v1.1 provenance state (or to any subsequent iteration's parallel-observer state), the level-2 verification will catch the coupling at the next pre-flight run. The cost of keeping the test in the pipeline is negligible; the protective value is real.

### 5.6 Limits of the present work

Three limits of the present work are worth naming explicitly, beyond the Category Φ honesty constraint already discussed.

The architecture remains tabular and small-scale. The 20×20 grid is sufficient for testing the provenance extension but does not address scale-related questions. Whether the records' structural information scales to environments with thousands or millions of states, whether the cross-reference structure remains tractable when the inventory of related cells grows large, whether confirmation density operationalisations remain sensible when the agent's exposure pattern to cells is sparser than in the present environment — these are questions the present work does not address. The architectural principle is demonstrated in a sandbox; whether it survives migration to richer environments is a question for the substrate-transposition phase to answer.

The provenance fields v1.1 introduces are minimal. The pre-registration committed to the SICC document's stated minimum (formation step, confirmation counts, last-confirmation step, plus the v1.1.1 cross-reference fields), and v1.1 implements exactly this minimum. Whether richer fields would carry information the present minimum does not — confidence as a function of counts and recency, distinguishing between confirmation events of different epistemic weights, recording the agent's location at formation as a first-class property — is reserved for subsequent iterations that operationalise SICC commitments beyond Commitment 4. v1.1 is the substrate; the substrate's adequacy is for the reporting iteration to test.

The Category γ metric committed in the v1.1.1 amendment is one of many possible operationalisations of structural-distance between formation narratives. The four-component decomposition with equal weighting is defensible at pre-registration time but is not the only defensible choice. Subsequent work that proposes alternative metrics — weighted versions, metrics that incorporate phase boundaries (the v1.1 metric explicitly excludes them, per amendment §4), metrics that operate on different temporal scales — would produce different verdicts on the same data. The v1.1 finding is committed to the metric that was committed; whether that metric is the optimal one for the substrate is a question subsequent work can address.

### 5.7 Architectural questions opened

Three architectural questions are opened or sharpened by the v1.1 findings, each plausibly addressable through a separate iteration.

The first is the reporting question. v1.1 establishes that the records exist in a form the agent could read, but the agent does not yet read them. The reporting iteration that operationalises SICC Commitment 11 is the methodological vehicle for testing whether the records are sufficient as a substrate for auditable self-accounts. The substantive vs deflationary readings of v1.1's contribution (Section 5.3) are distinguished by the reporting iteration's output. The v1.1 paper does not anticipate the answer; the iteration is reserved.

The second is the schema question. The records v1.1 introduces are written in a form that assumes a fixed schema — the four flag types are enumerated in advance, the cross-reference structure is fixed at threat-to-knowledge-banking linkage, the per-flag-type confirmation operationalisations are committed in advance. Whether the agent could be given an explicit representation of this schema, queryable in its own right (operationalising SICC Commitment 1), is the question the schema iteration addresses. The schema iteration would not change the records; it would add a layer above them that names what the records contain.

The third is the layered-properties question. The records v1.1 carries are at the formation-event level — when a flag formed, what observations have sustained it, what it cross-references. The SICC document's Commitment 6 specifies a richer layered structure (direct, interactional, relational, temporal properties, each requiring different cognitive operations to discover). Whether the v1.1 substrate could support an extension into layered properties — whether the present records' formation-step granularity is the right granularity, whether the per-flag-type confirmation operationalisations extend naturally to per-layer operationalisations — is the question the layered-properties iteration addresses.

These three iterations together complete the cognitive-layer arc the SICC document specifies. The substrate-transposition phase (operationalising Commitment 10) follows once the cognitive layer is sufficiently mature on the tabular substrate. v1.1 establishes the first piece of this arc; the rest is reserved.

### 5.8 The architectural arc through v1.1

The v0.9 through v0.14 papers traced an architectural arc on the threat-and-mastery side of the architecture, closed by v1.0's integration audit of the cumulative inheritance chain. v1.1 begins a new arc on the cognitive-layer side, operationalising the first of the SICC document's twelve commitments. The shape of this new arc, anticipated in the v1.1 carry-forward note (Baker, internal record, 28 April 2026), proceeds in phases: provenance (v1.1, this paper); explicit schema; layered property structure; reporting; substrate transposition.

The architectural change v1.1 introduces is contained at the research-question level — provenance over learned states is the single architectural extension — but its implications extend across the trajectory. The records the v1.1 substrate produces are what the schema iteration will name, what the reporting iteration will read, what the substrate-transposition iterations will need to remain meaningful when the substrate underneath them changes. Each subsequent iteration inherits what v1.1 has built and extends it, in the same way that v0.10 through v0.14 each inherited and extended the threat-and-mastery substrate the prior iterations produced.

The methodological discipline that has held throughout the programme holds for v1.1 with one specific strengthening worth naming. The parallel-observer pattern (Section 5.5) makes the byte-identical preservation property structurally guaranteed rather than merely aspirational; subsequent iterations that can be implemented as parallel observers should reach for this pattern, and the level-2 verification (`verify_v1_1_no_provenance.py`) is the permanent regression test that protects the pattern's preservation property going forward.

The amendment budget for v1.1 stands at one of three at the close of the iteration. Two amendments remain available; if no further amendment is needed the iteration closes with two unused, which is the disciplined outcome.

## 6. Conclusion

The v1.1 iteration tested whether the architecture's existing flag structures could be transformed from binary states into records of their own formation, through an architectural extension contained at the research-question level and implementable as a parallel observer module with no behavioural modification to the agent or the world. Across a pre-registered batch of 180 runs spanning six cost levels and three run lengths, with seeds matched to the v1.0 batch (Baker, 2026q, in preparation), v1.1 produces four findings.

Category α preservation holds at byte-identical resolution. Both pre-flight verifications passed at 10 of 10 runs (level 1 against v0.14 baseline with all instrumentation disabled; level 2 against v1.0 baseline with v1.0 instrumentation enabled and v1.1 provenance disabled). Internal consistency between v1.0 metric fields and v1.1 provenance counts holds at 180 of 180 runs across every coupling tested. The architecture's behaviour under v1.1 is preserved at the strongest resolution any iteration in the programme has committed to — a property that follows by construction from the parallel-observer implementation pattern, which introduces no path through which the v1.1 architectural extension could affect the agent's behaviour.

Category β alignment is exact. The bidirectional cross-reference structure between threat flags and the knowledge-banking flags that derive from the same coordinate through v0.14 transformation resolves at 160 of 160 pairs across the batch, with zero unidirectional anomalies, zero missing identifiers, and zero inconsistent forward references. The five pending cross-references at the 20,000-step run length are all in the expected pattern (cell transformed but knowledge-banking flag had not yet formed by run end). The bookkeeping logic operationalises the §2.4 specification correctly across the full batch.

Category γ record-scale individuation produces a partial pass against the v1.1.1-amendment criterion as written, combined with a substantive finding richer than the criterion was designed to test for. Every within-cell mean exceeds the substantive-differentiation floor of 0.05 by a factor of six to ten; the per-component decomposition shows that three of the four metric components carry within-cell variation approximately equal to across-cell variation, with only confirmation density modestly stratifying by experimental condition. The records carry agent-individual structural variation that is largely orthogonal to the experimental conditions: two agents at matched seeds within the same (cost, run length) cell produce records as structurally different from each other as two agents at completely different conditions, in three of four metric dimensions. This is the substrate-as-individuation finding the iteration was designed to test, surfaced in a sharper form than the criterion anticipated. The Montessori parallel made operative in Section 4 captures the developmental significance: the prepared environment is the same across runs at matched parameters; what differs is the agent's traversal, and the records carry the trajectory.

Category δ pre-anticipated negative findings landed as the pre-registration committed: threat-flag confirmation density structurally sparse under the present architecture's epistemic conditions; disconfirming-observations counts dominated by zero across most flag types but consistently 1.0 for threat flags whose cells transform under v0.14 dynamics; cross-reference completion rate bounded by v0.14 transformation dynamics. The honest reporting commitments hold; the negative findings are reported directly without aggregation across flag types.

The architectural claim made in this paper is bounded by the pre-registered Category Φ honesty constraint. The records v1.1 introduces are the substrate for an eventual self-account; whether subsequent iterations can construct an auditable account of agent learning from these primitives is the question the reporting iteration answers. v1.1's contribution is that the substrate exists in the form the pre-registration committed to, with the architectural property that subsequent iterations need: bidirectional cross-references that constitute learning narratives rather than collections of independent records, per-flag-type confirmation operationalisations honest about epistemic differences across flag types, and individuation at the record scale that surfaces in matched-seed comparison without behavioural modification.

The methodological discipline that has held throughout the programme held during this iteration with one specific strengthening worth naming. The parallel-observer pattern, modelled on the v1.0 instrumentation, makes byte-identical preservation a structurally guaranteed property of the iteration rather than merely an aspirational target. The level-2 verification is the permanent regression test that protects this preservation property going forward. Subsequent iterations that can be implemented as parallel observers should reach for the pattern; iterations that must modify agent behaviour will inherit the older preservation modes (population restriction, cross-layer effect characterisation) the v0.13 / v0.14 lineage developed.

The cognitive-layer arc the SICC document specifies has now begun. The v1.1 iteration operationalises the first of twelve commitments (provenance over beliefs); the schema iteration, the layered-properties iteration, the reporting iteration, and eventually the substrate-transposition iterations are the trajectory's subsequent phases. Each is reserved for its own iteration with its own pre-registration. The discipline of single-architectural-change-per-iteration that has held across the inheritance chain holds for the new arc as it held for the old.

One amendment was issued during the v1.1 iteration: v1.1.1 (Baker, 2026s), specifying the Category γ structural-distance metric operationalisation, committed after the records existed to be examined and before any reanalysis of the v1.1 batch was performed. The amendment was operational rather than architectural: no v1.1 code was modified, no batch was re-run, no architectural specification changed. The amendment budget for v1.1 stands at one of three at the close of the iteration; two amendments remain available.

The records exist. The agent does not yet read them. The reading is reserved for the next iteration in the trajectory. What this paper records is that the substrate is in place.

## 7. Code and Data Availability

All code, pre-registration documents, batch outputs, per-run CSV data, and paper drafts referenced in this work are available in the public repository at github.com/RancidShack/developmental-agent. The v1.1 pre-registration document was committed before any v1.1 code was written, in accordance with the methodological commitments named in Section 6 of that document.

The v1.1 implementation comprises four files. `v1_1_provenance.py` implements the parallel observer module with the per-flag-type confirmation operationalisations and bidirectional cross-reference resolution. `curiosity_agent_v1_1_batch.py` is the batch runner; it imports the v0.14 architecture verbatim and runs both the v1.0 recorder and the v1.1 provenance store as parallel observers. `verify_v1_1_disabled.py` is the level-1 pre-flight verification (against v0.14 baseline with all instrumentation disabled). `verify_v1_1_no_provenance.py` is the level-2 pre-flight verification and permanent regression test (against v1.0 baseline with v1.0 instrumentation enabled and v1.1 provenance disabled). The Category γ analysis is implemented in `analyse_v1_1_category_gamma.py`, which reads `provenance_v1_1.csv` and `run_data_v1_1.csv` and produces the per-pair distance matrix, per-cell summary, and verdict against the v1.1.1 amendment criteria.

The matched-seed comparison against v1.0 uses seeds drawn from `run_data_v1_0.csv` (Baker, 2026q, in preparation), which itself loaded seeds from the v0.14 batch. The seed chain links v0.10, v0.11.2, v0.12, v0.13, v0.14, v1.0, and v1.1 at every (cost, run length, run index) cell. No re-run of v0.10 through v1.0 was performed for the present paper; the comparisons reported here use the published baseline CSVs directly.

The v1.1 batch produced four output files: `run_data_v1_1.csv` (per-run aggregate metrics including the v1.1 provenance summary fields); `snapshots_v1_0_under_v1_1.csv` (v1.0 instrumentation snapshots produced by the v1.0 recorder running under the v1.1 batch); `snapshots_v1_1.csv` (v1.1 provenance snapshots at flag-formation events plus end-of-run); and `provenance_v1_1.csv` (per-flag formation records, one row per formed flag per run). The Category γ analysis produced three further outputs: `category_gamma_distances.csv` (per-pair distance matrix), `category_gamma_summary.csv` (per-cell statistics), and `category_gamma_verdict.txt` (human-readable verdict). All files are timestamped 30 April 2026.

The v1.1.1 amendment was committed before any Category γ analysis was performed on the v1.1 batch. The amended logic was implemented in `analyse_v1_1_category_gamma.py`; no batch re-run was required. The Category γ verdict (partial pass against criterion 1 with substantive finding; pass against criterion 2; overall partial pass with the substantive finding developed in Section 4) is a deterministic output of the amendment-specified metric on the existing data.

## 8. References

Baker, N.P.M. (2026a) 'Staged Development in a Small Artificial Learner: Architectural Conditions for Rule Adherence, Focused Autonomy, and Biographical Individuation', OSF Preprint, v1.0, 21 April 2026.

Baker, N.P.M. (2026b) 'The Childhood AI Never Had: Twelve Iterations of a Computational Developmental Learner', preprint in preparation for resubmission, v1.0, 21 April 2026.

Baker, N.P.M. (2026c) 'Learning Without the Wall: Decomposing Rule Adherence in a Small Artificial Learner into Pre-Wired Aversion and Cost-Based Experience', preprint v0.1, 22 April 2026.

Baker, N.P.M. (2026d) 'Experience-Driven Persistent Threat Representation Stabilises Long-Horizon Avoidance in a Small Artificial Learner', preprint, 25 April 2026.

Baker, N.P.M. (2026e) 'v0.11 Pre-Registration: Experience-Driven Attractor Depletion and Persistent Mastery Representation', GitHub repository, 24 April 2026.

Baker, N.P.M. (2026f) 'v0.11.1 Pre-Registration Amendment: Preference Reset on Mastery', GitHub repository, 24 April 2026.

Baker, N.P.M. (2026g) 'v0.11.2 Pre-Registration Amendment and Batch: Preference Accumulation Blocked on Mastered Cells', GitHub repository and preprint, 24 April 2026.

Baker, N.P.M. (2026h) 'v0.12 Pre-Registration: Category-Level Generalisation in the Threat Layer via Cell-Type Signature-Matching', GitHub repository, 25 April 2026.

Baker, N.P.M. (2026i) 'Category-Level Generalisation in the Threat Layer of a Small Artificial Learner via Cell-Type Signature-Matching', preprint in preparation, 25 April 2026.

Baker, N.P.M. (2026j) 'v0.13 Pre-Registration: End-State Target Activation via Random-Location Cell Appearing on All-Attractors-Mastered Signal', GitHub repository, 25 April 2026.

Baker, N.P.M. (2026k) 'v0.13.1 Pre-Registration Amendment: Audit Scope Clarification', GitHub repository, 25 April 2026.

Baker, N.P.M. (2026l) 'End-State Target Activation in a Small Artificial Learner via Random-Location Cell Appearance on the All-Attractors-Mastered Signal', preprint in preparation, 26 April 2026.

Baker, N.P.M. (2026m) 'v0.14 Pre-Registration and Implementation: Competency-Gated Content Transformation of Hazard Cells into Knowledge Cells', GitHub repository, 27 April 2026.

Baker, N.P.M. (2026n) 'v0.14.1 Pre-Registration Amendment: Permutation Offset Parameter for Targeted Replication Batch', GitHub repository, 27 April 2026.

Baker, N.P.M. (2026o) 'v1.0 Pre-Registration: Integration Audit of the Cumulative Inheritance Chain', GitHub repository, 28 April 2026.

Baker, N.P.M. (2026p) 'v1.0.1 Pre-Registration Amendment: Inheritance-Aware Category γ Reframing', GitHub repository, 28 April 2026.

Baker, N.P.M. (2026q) 'v1.0 Integration Audit of the Developmental-Agent Inheritance Chain', preprint in preparation, 28 April 2026.

Baker, N.P.M. (2026r) 'v1.1 Pre-Registration: Provenance Over Learned States via Formation Records on Existing Flag Structures', GitHub repository, 29 April 2026.

Baker, N.P.M. (2026s) 'v1.1.1 Pre-Registration Amendment: Category γ Structural-Distance Metric Specification', GitHub repository, 30 April 2026.

Baker, N.P.M. (internal record, drafted alongside v0.13) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent', v0.1.

Baker, N.P.M. (internal record, 28 April 2026) 'v1.1 Carry-Forward: Provenance Phase Orientation Note for the New Chat'.

## 9. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper. The treatment of FLA principles in the broader programme is bounded; the computational findings reported here are claimed on their own architectural terms, with FLA serving as a process scaffold for experimental design rather than as the framework being instantiated.

The Montessori parallel that informs the developmental framing of this paper draws on the broader Montessori literature on prepared environments and the child's individual traversal through them. The parallel is not claimed as a contribution to Montessori scholarship; it is invoked as the developmental motif against which the v1.1 architectural extension's intent is most legibly named.

No human participant data were collected. No external parties had access to drafts of this paper prior to its preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
