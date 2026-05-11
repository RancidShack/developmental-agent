# v1.1 Pre-Registration: Provenance Over Learned States via Formation Records on Existing Flag Structures

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 29 April 2026
**Status:** Pre-registration document, committed to public repository before any v1.1 code is written
**Repository:** github.com/RancidShack/developmental-agent

---

## 1. Purpose

The v1.0 integration audit closed the second arc of the developmental-agent programme, demonstrating that the architecture under v0.14 inheritance supports persistent categorical knowledge across two layers, late-target activation through random-location cell sampling, competency-gated content transformation, and biographical individuation at trajectory-and-completion scale (Baker, 2026q, in preparation). Cross-layer behavioural coupling was mechanistically confirmed at three iterations, and the methodological apparatus — pre-registration before code, matched-seed comparison across the inheritance chain, single-architectural-change-per-iteration discipline — held throughout.

What the v1.0 architecture does not do, and what the post-v1.0 trajectory is reserved to address in stages, is hold its learned states as records of their own formation. A threat flag in v1.0 is a binary state: the flag is set or it is not, the architecture consults it, and the flag carries no representation of how it came to be set, when it was set, or what observations have sustained it since. The same structural property holds for mastery flags, knowledge-banking flags, and end-state activation and banking flags. The architecture acts on its flags; it does not yet hold a relationship with them.

The v1.1 iteration operationalises one cognitive-architecture commitment from the Substrate-Independent Cognitive Commitments document (Baker, internal record, drafted alongside v0.13): provenance over beliefs (Commitment 4). The architectural extension is contained at the research-question level — existing flag structures acquire formation history and become records of their own conditions of formation — and is the smallest substantive step from v1.0 toward the cognitive-layer commitments the SICC document specifies. The agent does not yet read its own records (reserved for the reporting iteration that subsequently realises Commitment 11); the records do not yet drive different behaviour from differently-provenanced flags (reserved for predict-and-surprise iterations that subsequently realise Commitment 7). What v1.1 establishes is that the architecture now holds objects of a different kind — flags as records rather than flags as switches — and that subsequent iterations will read from, reason about, and act on those objects.

The developmental purpose the records serve is the agent's eventual capacity to give an account of its own learning history when asked. In a Montessori-prepared environment, the child's traversal through the materials produces a learning sequence that is the child's rather than the teacher's, and what the child later carries away includes the route by which competencies were acquired — the recollection that the cylinders preceded the binomial cube, that the sandpaper letters grounded the moveable alphabet. The route is part of what the child knows about themselves and is what makes the learning the child's own rather than something done to them. The v0.14 architecture, with knowledge cells as foundational and competency-gated hazard cells as advanced, is the prepared environment for the agent. v1.0 instruments that the trajectory through this environment happens. v1.1 records the trajectory in the agent's own state, in a form that can later be queried.

## 2. Architectural specification

The v1.1 architecture inherits v1.0 (which inherits v0.14) unchanged except for the addition of provenance records to four flag types and bidirectional cross-references between two of those types. No agent-side capability to read provenance is introduced; no behavioural modification to action selection, drive composition, or value learning is introduced. The architectural change is contained to what the architecture remembers about its own state.

### 2.1 Provenance fields per flag type

Each flag of the four affected types acquires a provenance record at the moment of flag formation. The record is held alongside the binary flag state for v1.1's purposes; subsequent iterations may restructure the storage but the v1.1 implementation does not require the binary state to be subsumed into the record. Five fields are common to all flag types:

`flag_set_step` — the integer step at which the flag transitioned from unset to set. For threat flags this is the step at which FLAG_THRESHOLD entries accumulated under v0.10 dynamics or at which v0.12 signature-matching first-entry conversion fired. For mastery flags this is the step of the third entry to the attractor cell that triggers banking under v0.11.2 dynamics. For knowledge-banking flags this is the step of the third post-transition entry to the transformed cell under v0.14 dynamics. For end-state activation this is the step at which the all-attractors-mastered signal first fires under v0.13 dynamics (as amended by v0.14 if that amendment is operative); for end-state banking this is the step of first post-activation entry to the end-state cell.

`confirming_observations` — an integer count of post-formation observations consistent with the flag's continued correctness. The operationalisation differs per flag type and is specified in section 2.2.

`last_confirmation_step` — the integer step at which the most recent confirming observation was recorded, or null if `confirming_observations` is zero.

`disconfirming_observations` — an integer count of observations that, under the v1.1 architecture's narrow definition, fail to sustain the flag. Under the present architecture this count is zero for all flag types except where the v0.14 transformation case described in section 2.3 applies. The slot is held regardless of whether it is incremented, on the SICC-honest principle that distinguishing a value not observed from a slot that does not exist is the architecture's first vocabulary for knowing what it does not yet do.

`last_observation_step` — the integer step at which the flag's underlying state was most recently observed, regardless of whether the observation was confirming or disconfirming. This field exists so that subsequent iterations distinguish flags that are actively engaged with from flags that are dormant, without requiring those iterations to amend the schema.

### 2.2 Per-flag-type operationalisation of confirming observations

The four flag types are formed and sustained under different epistemic conditions in the present architecture, and the confirming-observations count operationalises differently for each.

**Threat flags.** A confirming observation is an event in which the flag's prediction is tested in the architecture's available terms. Under the present architecture, the gating mechanism prevents the agent from re-entering flagged hazard cells, so direct confirmation by re-entry is structurally rare. Three observation events count toward the threat-flag confirming-observations count: a v0.12 signature-matching first-entry conversion at an adjacent cell of the same category as the flagged cell (which confirms the flag's category-membership prediction by extension); a forced entry to the flagged cell in the rare cases where the gating mechanism's exclusion of the flagged action leaves no other action available (which the architecture should record honestly when it occurs); and an observation of the flagged cell's persistence as a hazard cell across the developmental phase boundary (Phase 2 to Phase 3), recorded as a confirmation that the cell has not been transformed under v0.14 dynamics. The third event is the most frequent and produces the bulk of the threat-flag confirming-observations counts.

The v1.1 paper will report threat-flag confirming-observations counts honestly as sparse relative to the other flag types. This is a finding about the present architecture's epistemic conditions for threat-flag confirmation, not a defect of the metric.

**Mastery flags.** A confirming observation is a post-banking visit to the mastered attractor cell where the four mastery interventions are observed to hold: zero feature reward delivered, attraction bias cleared, preference accumulation blocked, preference at zero. The architecture's existing post-banking visit handling already checks these properties; v1.1 increments the confirming-observations count when the check passes. Mastery-flag confirmation is dense relative to threat-flag confirmation because the architecture does not gate against re-entry to mastered cells.

**Knowledge-banking flags.** Operationally identical to mastery flags but applied to the post-transition population: confirming observations are post-banking visits to the transformed cell where the four mastery interventions hold. Knowledge-banking flag confirmation is moderately dense, bounded above by the agent's post-banking attention to the transformed cell.

**End-state flags.** Two flags are tracked: activation (the all-attractors-mastered signal having fired) and banking (the end-state cell having been entered after activation). For activation, confirming observations are post-activation steps in which the all-attractors-mastered condition continues to hold (which under the present architecture is every subsequent step, because mastery flags do not retract); the v1.1 paper will note that this count is therefore deterministically equal to the post-activation window length, and the substantive information is in the formation step rather than the count. For banking, confirming observations are post-banking visits to the end-state cell where the four mastery interventions hold, operationally identical to mastery-flag confirmation.

The per-flag-type operationalisation is specified in advance and committed in this pre-registration. The v1.1 paper will report counts per flag type without aggregation across types, on the principle that a confirmation in one epistemic regime is not the same kind of evidence as a confirmation in another.

### 2.3 Disconfirming observations: narrow semantics

The v1.1 architecture does not retract flags. The disconfirming-observations slot is held regardless, with semantics defined narrowly for the one case where the present architecture produces an event the slot can hold.

When a hazard cell with threat flag F undergoes v0.14 competency-gated transformation to a knowledge cell at step N, the transformation event is not a retraction of F (F remains set) but it is an event the threat flag's record should hold. F's `disconfirming_observations` count is incremented by one at step N to record that the cell the flag was about has undergone a state change rendering F's prediction structurally untestable in its original form. F's `transformed_at_step` field (defined in section 2.4) is set to N. No other event under the present architecture increments any flag's disconfirming-observations count.

This narrow semantics is committed in the pre-registration. Subsequent iterations that introduce flag retraction, competency-loss, or richer disconfirmation events may extend the semantics; the v1.1 paper will not extend it.

### 2.4 Cross-references between threat flags and knowledge-banking flags

The architectural connection that makes the formation history a learning narrative rather than a collection of independent records is the link between threat flags and the knowledge-banking flags that derive from the same coordinate through v0.14 competency-gated transformation. v1.1 introduces bidirectional cross-references between these records.

When a flagged hazard cell at coordinate C undergoes transformation to a knowledge cell at step N, two record updates occur. The threat flag F at coordinate C acquires a new field `transformed_at_step = N` and a new field `derived_knowledge_flag = K`, where K is the identifier of the knowledge-banking flag that will subsequently form on the transformed cell. K does not yet exist at step N; the field is set to a forward-reference placeholder that resolves when K forms (at the third post-transition entry to the cell under v0.14 dynamics).

When the knowledge-banking flag K subsequently forms on the transformed cell at step M (M > N), K's record acquires a new field `derived_from_threat_flag = F` recording the back-reference to the threat flag whose transformation produced the cell K is about. F's `derived_knowledge_flag` field is updated from the placeholder to the resolved K identifier.

The bidirectional cross-reference is the architectural substrate for the learning-narrative property the records support. Without it, F and K would be independent records about the same coordinate; with it, they constitute a linked pair representing a single trajectory of learning about that coordinate — first as something to avoid, later as something to engage with under earned competency. The Montessori parallel: the advanced material does not appear alongside the foundational; it builds on it, and the record holds the building.

Coordinates that are flagged as hazards but never undergo transformation (because the agent does not reach the v0.14 competency threshold within the run length) carry F records with `transformed_at_step` and `derived_knowledge_flag` set to null. Coordinates that are knowledge-banked without prior threat-flag formation (where the cell was not flagged before transformation, which the v0.14 architecture does permit in principle for cells that transform before threat-flag formation completes) carry K records with `derived_from_threat_flag` set to null. The null cases are recorded explicitly, on the SICC-honest principle that the slot exists and its emptiness is itself an epistemic state worth preserving.

### 2.5 Record-write timing and storage

Records are written at coupling moments, inheriting the v1.0 snapshot infrastructure. The v1.0 instrumentation captures snapshots at six classes of coupling moment (specified in the v1.0 paper's instrumentation section); v1.1 extends the snapshot data to include the provenance records at each snapshot, and additionally writes provenance state at the moment of any flag-formation, flag-confirmation, or flag-disconfirmation event regardless of whether the event coincides with an existing snapshot moment.

End-of-run provenance state is written to the per-run CSV alongside the existing v1.0 fields. The provenance fields added to the per-run CSV are: per-flag-type counts of formed flags, mean and distribution of `flag_set_step` per flag type, mean and distribution of `confirming_observations` per flag type, mean and distribution of `disconfirming_observations` per flag type, count of cross-referenced flag pairs (threat-flag-to-knowledge-banking-flag), and the list of formation events ordered by step (the formation narrative for the run). The list of formation events is the substrate for Category γ analysis (section 5.3).

### 2.6 What v1.1 does not change

All architectural elements from v1.0 (and v0.14, v0.13, v0.12, v0.11.2, v0.10) are preserved unchanged. The threat layer operates as v0.12 specifies: three-entry conversion for the first hazard cell of a category; signature-matching first-entry conversion for subsequent cells; hard-gate action selection. The mastery layer operates as v0.11.2 specifies: three-entry banking; four mastery interventions on banked cells. The knowledge cell layer operates as v0.14 specifies: competency-gated transformation; three-entry banking on transformed cells; four mastery interventions on knowledge-banked cells. The end-state mechanism operates as v0.13 (with v0.14 amendments) specifies: random-location sampling at run start; cell-type transition on activation; one-entry banking. The three-phase developmental schedule, drive composition, learning rate, discount factor, epsilon, and the pre-wired aversion bias of −5.0 for frame-adjacent actions are inherited unchanged.

No agent-side capability to read provenance records is introduced. The agent's perception, drive composition, action selection, value learning, and model updates do not consult the provenance records at any point in the v1.1 architecture. The records are written; they are not read by the agent.

The single-variable-change discipline holds at the research-question level: v1.1 introduces provenance over learned states as the singular architectural extension. All prior architectural elements are preserved.

## 3. Experimental matrix and matched-seed comparison

The experimental matrix matches v1.0 initially: one architecture (v1.1) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with three run lengths (20,000, 80,000, 160,000 steps) crossed with ten runs per cell, totalling 180 runs.

For each (cost, run length, run index) triple, the random seed is matched to the v1.0 batch, which itself matched v0.14, v0.13, v0.12, v0.11.2, and v0.10 at the same conditions. Seeds are loaded from `run_data_v1_0.csv` rather than regenerated. The seed chain links every iteration of the inheritance arc at every (cost, run length, run index) cell.

The matched-seed comparison produces a within-seed comparison up to the precision the v1.1 architectural extension permits. Because v1.1 introduces no behavioural modification — the records are written, not read — every action the agent takes under v1.1 at a given seed is identical to the action it takes under v1.0 at the same seed. The two architectures diverge only in what they hold about their own state, not in what they do. This is the strongest preservation guarantee any iteration in the programme has committed to: byte-identical behaviour across the full 180-run batch under matched seeds.

## 4. Metrics

All v1.0 metrics are retained unchanged.

The provenance fields specified in section 2.5 are added to the per-run CSV. The snapshot CSV is extended to include the per-snapshot provenance state per flag.

Three derived metrics are computed for analytical convenience.

**Formation narrative.** For each run, the ordered tuple of (flag_id, flag_type, flag_set_step) entries across all formed flags, with cross-reference fields included. The formation narrative is the substrate for Category γ analysis (section 5.3).

**Confirmation density.** For each flag type, the mean ratio of `confirming_observations` to `(num_steps - flag_set_step)`. This is the rate at which the flag is confirmed per post-formation step, normalised for post-formation window length. The metric makes confirmation densities comparable across flag types and across runs of different lengths.

**Cross-reference completion rate.** The fraction of threat flags whose `derived_knowledge_flag` field is non-null at end of run, computed per (cost, run length) cell. This is the rate at which threat flags trace forward to a derived knowledge-banking flag within the run length and serves as a proxy for the v0.14 transformation engagement under v1.1's matched-seed conditions.

## 5. Pre-registered interpretation categories

Five interpretation categories are pre-registered. The category labels follow the v1.0 paper's α / β / γ / δ / Ω convention; the substantive content is v1.1-specific.

### 5.1 Category α: Preservation of the v1.0 architecture under v1.1 extension

The architectural extension v1.1 introduces is record-writing, with no behavioural modification. The expected preservation result is therefore stronger than any prior iteration's: byte-identical behaviour across the full 180-run batch at matched seeds, on every metric that v1.0 records.

Category α succeeds if:

- All v1.0 metrics on all 180 runs match v1.0 baseline byte-for-byte at matched seeds.
- The pre-flight verification with provenance recording disabled produces output bit-for-bit identical to v1.0 baseline at matched seeds.
- The pre-flight verification with provenance recording enabled produces output matching v1.0 baseline on all v1.0 metrics (the new provenance fields are additions, not modifications).

Category α failure is a substantive finding: it would indicate that the record-writing machinery has somehow contaminated the agent's behaviour, which would require diagnosis before the v1.1 batch could be interpreted. The pre-flight verifications are mandatory before the v1.1 batch runs.

### 5.2 Category β: Provenance state at coupling moments aligns with v1.0 snapshot data

The v1.0 instrumentation captured snapshot data at six classes of coupling moment, recording the architecture's state at each moment. The v1.1 provenance records, by construction, should align with the v1.0 snapshots at corresponding moments: the formation step of any flag should equal the step at which the v1.0 snapshot first records the flag as set; the confirming-observations count at any snapshot moment should equal the count of v1.0-instrumented confirmation events between flag formation and the snapshot moment.

Category β succeeds if:

- Per-flag formation steps in v1.1 records match v1.0 snapshot first-set steps to the integer.
- Per-flag confirming-observations counts at every snapshot moment match the count of v1.0-instrumented confirmation events between formation and snapshot.
- Cross-reference field values (threat-flag `transformed_at_step`, knowledge-banking flag `derived_from_threat_flag`) match the v0.14 transformation events recorded in the v1.0 snapshot data.

Category β failure indicates an alignment defect between the v1.1 record-writing logic and the v1.0 instrumentation, which must be diagnosed before substantive findings can be reported.

### 5.3 Category γ: Record-scale individuation

The v1.0 paper documented biographical individuation at trajectory-and-completion scale: agents differ in what they did and when, and their final knowledge representations carry the difference. v1.1's record-scale individuation question is whether agents with different trajectories produce records that, when later read, would constitute different self-accounts of how they learned — not just differing timestamps, but structural differences in formation order, dependencies, confirmation patterns, and cross-references.

The metric for Category γ is a structural-distance measure between formation narratives at agent-pair level. The metric family is committed in this pre-registration; the specific operationalisation is reserved for v1.1.1 amendment after the records exist to be examined. The metric family has four required properties:

- It takes formation order into account (two agents that form the same set of flags in different orders are at non-zero distance).
- It takes cross-reference structure into account (two agents whose threat-flag-to-knowledge-banking-flag pairings differ are at non-zero distance even where the individual flag formations are identical).
- It takes confirmation-pattern structure into account (two agents whose confirmation densities differ across flag types are at non-zero distance).
- It is not driven primarily by raw timestamp differences (the metric should distinguish trajectories that differ only in timing from trajectories that differ structurally; the latter is the substantive individuation).

Category γ succeeds if:

- Mean structural distance between agent pairs at non-matched conditions exceeds mean structural distance at matched seeds (v1.1 against v1.1) by a margin to be specified in the v1.1.1 amendment.
- The distribution of structural distances exhibits diversity comparable to or greater than the diversity observed in v1.0's trajectory-scale individuation metrics.
- The v1.1.1 amendment is committed before any reanalysis of the v1.1 batch is performed.

Category γ failure (or partial failure) is honestly reported. If the records turn out to encode less structural diversity than the trajectories that produced them, the finding is informative: it would indicate that v1.1's record schema has under-resolved the individuation v1.0 surfaced, and a richer schema would be the natural follow-on. If an issue is flagged on initial analysis, the v1.1 paper's reporting would extend the run length or adjust counts to either prove the structural-distance signal or discount it, with the methodology committed before the extended analysis runs.

### 5.4 Category δ: Negative findings honestly recorded

Three categories of negative finding are anticipated and pre-committed to honest reporting:

**Sparse threat-flag confirmation.** The threat-flag confirming-observations count under the present architecture's epistemic conditions for threat-flag confirmation is structurally sparse. The v1.1 paper will report this finding directly rather than aggregate threat-flag counts with mastery and knowledge-banking counts.

**Disconfirming-observations counts dominated by zero.** Under the narrow semantics of section 2.3, the disconfirming-observations count is non-zero only for threat flags whose cells undergo v0.14 transformation. Across the 180-run batch, the proportion of flags with non-zero disconfirming counts is bounded above by the v0.14 transformation rate, which is itself bounded by the agent's progression to the v0.14 competency thresholds. The v1.1 paper will report the proportion honestly; the slot's existence is the substantive architectural commitment, not the slot's frequent population.

**Cross-reference completion rate bounded by v0.14 dynamics.** The cross-reference completion metric (section 4) is bounded above by the rate at which flagged hazard cells transform to knowledge cells and subsequently bank within the run length. The v1.1 paper will report the rate against the v0.14 baseline rather than against an architectural ideal.

### 5.5 Category Ω: The architectural-statement claim

Category Ω names the substantive architectural claim the v1.1 paper makes if Categories α, β, and γ all succeed (or if Category γ partially succeeds in a recoverable form).

The claim: provenance over learned states is the substrate for an eventual self-account, and the present substrate supports this without architectural revision. The records v1.1 introduces are not behavioural modifications and do not yet enable the agent to read its own learning history; they are the architectural objects that subsequent iterations will read from, reason about, and act on. The v1.1 iteration establishes that the move from flag-as-state to flag-as-record can be made on the existing primitives, that the resulting records align with the v1.0 snapshot data at coupling moments, and that the records carry the structural difference between agents' learning histories in a form that constitutes record-scale individuation.

The Category Ω claim is bounded by Category Φ (defined below) on the same honesty principle that bounded the v0.13 paper's locating-mechanism claim.

### 5.6 Category Φ: Honesty constraint on the substrate-as-self-account claim

The claim that v1.1's records constitute the substrate for an eventual self-account is structural rather than behavioural. The agent does not read its records under v1.1; the records' adequacy as a self-account substrate is therefore not directly demonstrated by the v1.1 batch. The claim is consistent with two readings the v1.1 batch alone cannot distinguish.

The substantive reading: the records hold the structural information necessary for the agent, in subsequent iterations, to give an account of its own learning that is auditable, traceable through provenance to specific encounters, and individuated in ways v1.0 individuation could not surface.

The deflationary reading: the records hold formation timestamps and confirmation counts; whether subsequent iterations can construct a self-account from these primitives is an open question, and v1.1 establishes only that the primitives exist.

Both readings are consistent with the v1.1 batch. The reporting iteration that subsequently realises Commitment 11 of the SICC framework is the methodological vehicle for distinguishing them. v1.1's pre-registration commits to reporting this honestly: the architectural claim made in any v1.1 paper is bounded by Category Φ. The substrate-claim is the v1.1-specific finding; whether the substrate is sufficient for the eventual self-account is the question subsequent iterations answer.

## 6. Methodological commitments

Pre-registration before code: this document is committed to the public repository before any v1.1 implementation work begins.

Matched-seed comparison: seeds are loaded from `run_data_v1_0.csv` at every (cost, run length, run index) cell. No re-run of v1.0 or earlier iterations is performed; the comparisons reported in the v1.1 paper use the published baseline CSVs directly.

Pre-flight verifications, both mandatory before the v1.1 batch runs:

1. With provenance recording disabled (a configuration flag in the v1.1 implementation that suppresses all record-writing while preserving every other architectural property), the v1.1 architecture must produce output bit-for-bit identical to v1.0 baseline at matched seeds across a representative sample of conditions (minimum: one full cost-by-run-length cell, ten runs).

2. With provenance recording enabled (the production configuration for the v1.1 batch), the v1.1 architecture must produce output matching v1.0 baseline on every v1.0 metric across the same sample. The provenance fields are additions; they must not modify any v1.0 field.

Both verifications are run before the full v1.1 batch. Failure of either verification is a Category α failure and the v1.1 batch does not run until the verification passes.

Single-architectural-change-per-iteration discipline: v1.1 introduces provenance over learned states as the singular architectural extension. All prior architectural elements are preserved. No SICC commitment beyond Commitment 4 is operationalised in v1.1; subsequent iterations operationalise the remaining commitments in their own pre-registrations.

Public-record commitments: this pre-registration document is committed to the public repository at github.com/RancidShack/developmental-agent before any v1.1 code is written. Subsequent implementation, batch outputs, per-run CSV data, the v1.1 paper draft, and any amendments are committed to the same repository under timestamped commits.

## 7. Amendment policy

The amendment budget for v1.1 is three. Amendments are operational rather than architectural where possible — clarifications to audit operationalisation, threshold calibration, metric specification — and are committed to the public repository before any reanalysis of the v1.1 batch is performed.

One amendment is provisionally reserved for v1.1.1: the specific operationalisation of the structural-distance metric for Category γ (section 5.3). The metric family is committed in this pre-registration; the specific form is committed in v1.1.1 after the records exist to be examined. The provisional reservation is explicit on the public record so that the v1.1.1 amendment is not a discovery of need but the execution of a pre-committed plan.

Two amendments remain available for unanticipated operational issues. Architectural amendments (those that modify the v1.1 architecture itself rather than its audit operationalisation) require the iteration to be reset and the pre-registration redrafted; they are not within the amendment budget.

## 8. Stopping rule

The v1.1 iteration completes when:

- Pre-flight verifications pass (Category α verification).
- The full 180-run batch has run.
- The v1.1.1 amendment specifying the Category γ metric operationalisation is committed.
- Categories α, β, γ, δ, and Φ have been characterised in the v1.1 paper.
- The v1.1 paper is drafted, with Category Ω stated to the extent the operational results support.

The iteration is reset (and the pre-registration redrafted) if:

- The amendment budget of three is exhausted before iteration completion.
- An architectural amendment becomes necessary (modification to v1.1's architecture, rather than to its audit operationalisation).
- A Category α failure is diagnosed as requiring architectural change to v1.1's record-writing machinery.

## 9. Connection to the post-v1.0 trajectory

v1.1 is the first iteration of the post-v1.0 trajectory. The trajectory's subsequent phases are reserved for separate iterations with their own pre-registrations:

- **Explicit schema** (operationalising SICC Commitment 1). The agent holds and can interrogate the structure of what it knows about: cell types as kinds, actions as available verbs, phases as developmental periods. v1.1's records are written in a form that the schema iteration can read; the agent does not yet read them.

- **Layered property structure** (operationalising SICC Commitment 6). Cells acquire properties of multiple kinds — direct, interactional, relational, temporal — each requiring a different cognitive operation to discover and maturing at different rates.

- **Reporting** (operationalising SICC Commitment 11). The agent produces auditable reports traceable through provenance to specific encounters. This is the iteration in which the records v1.1 introduces become readable by the agent.

- **Substrate transposition** (operationalising SICC Commitment 10). Initially to richer simulated environments, subsequently to physical embodiment with the cognitive layer running on Raspberry Pi external to the robot, eventually to migration onto embedded compute.

These phases are reserved. v1.1 operationalises only provenance. The discipline of single-architectural-change-per-iteration that has held across the inheritance chain holds for v1.1 and for each subsequent phase.

## 10. References

Baker, N.P.M. (2026a–p) Prior preprints in the developmental-agent programme: v0.8 through v0.14 inheritance chain, end-state activation (v0.13), category-level generalisation (v0.12), bounded mastery (v0.11.2), persistent threat representation (v0.10). Full reference list is held in the v1.0 paper's reference section and is inherited unchanged for v1.1.

Baker, N.P.M. (2026q) 'v1.0 Integration Audit of the Developmental-Agent Inheritance Chain', preprint in preparation, April 2026.

Baker, N.P.M. (internal record, drafted alongside v0.13) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent', v0.1.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 29 April 2026, before any v1.1 implementation work begins. Subsequent v1.1 work — implementation, pre-flight verification, batch run, analysis, paper drafting — proceeds under the architectural specification and interpretation categories committed here.

The v1.1.1 amendment, when committed, will specify the Category γ structural-distance metric operationalisation. The amendment budget at the close of v1.1 will be reported in the v1.1 paper.
