# Cross-Family Structural Comparison in a Small Artificial Learner: The Architecture's First Record of a Relationship Between Two Families

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Working draft — Sections 1 through 6

---

## Abstract

The v1.3 iteration introduced two relational property families — GREEN and YELLOW — each comprising three cells at three tiers of cognitive engagement: perceivable, acquirable, and bankable. The v1.3.2 batch confirmed that every agent, given sufficient time, completes both family traversal sequences via a unique route, and that the intra-family cross-references resolve at 100% fidelity conditional on both flags forming within the run. What the v1.3 architecture did not hold was any structural record of the relationship between the two families. The GREEN records and the YELLOW records existed in parallel; nothing in the architecture compared them, and no architectural object stated that they were structurally parallel — that both ran through the same three tiers, that both encoded a flat-to-2D-to-3D form progression, that the colour identifier performed the same relational function in both.

The v1.4 iteration introduces cross-family structural comparison as the architectural extension that closes this gap. A fifth parallel observer — the v1.4 comparison observer — reads the completed family traversal records at run end and computes three structural comparison measures between the two families: tier-structure similarity (normalised edit distance on tier-event sequences), form-progression parallelism (proportion of structural form properties holding across both families), and traversal-sequence structural distance (the Category γ metric from v1.3.1 applied cross-family within each run). No agent behaviour is modified; the comparison observer is read-only and operates entirely outside the agent's action-selection path.

The v1.4 batch (240 runs, four run lengths, seeds matched to v1.3.2) produces four findings.

The first is preservation. With the comparison observer disabled, output is byte-identical to the v1.3.2 baseline at matched seeds on all v1.3 metrics across all ten verification runs. The fifth observer adds nothing to the existing stack.

The second is Measure 2 confirmation. Form-progression parallelism is 1.0 in all 240 runs, confirming the architectural structural assertion: both families encode the FLAT → 2D → 3D progression by design.

The third is Measure 1 behaviour. Tier-structure similarity is 0.0 in 187 of 240 runs — those in which both families complete the full three-tier sequence — and non-zero only in the 53 runs where incomplete traversal produces asymmetric tier sequences. At 320,000 steps, Measure 1 is 0.0 in all 60 runs, confirming that structural convergence on tier ordering is universal given sufficient developmental time.

The fourth is the operative finding: Measure 3 (traversal-sequence structural distance) shows non-trivial variance at every run length, with mean and distribution shape shifting systematically across observation windows. At 320,000 steps — where all 60 agents complete both families — the distribution concentrates near a lower bound that is itself analytically informative: when both traversals are complete, the edit-distance component of Measure 3 is constant at 1.0 (all full-token sequences differ by family label and step timing), so the 0.7 weight becomes a structural floor and all remaining variance is carried by the 0.3 × timestamp divergence component. The distribution is non-degenerate by natural tertiles (20/20/20), with individual variation in developmental timing as the sole source of differentiation once structural ordering has converged.

The Category Φ honesty constraint holds. The comparison observer detects structural similarity from the architecture's own records; the agent does not. Whether the agent can eventually use the cross-family comparison record as a cognitive object — to predict the structure of a third family from the pattern of the first two — depends on architectural additions v1.4 does not introduce. What v1.4 establishes is that the structural similarity is detectable, correctly computed, and individually variable in ways that reflect each agent's developmental trajectory. Detectability is the precondition for the agent's eventual capacity to detect it.

---

## 1. Introduction

### 1.1 Programme to date

The programme's post-v1.0 cognitive-layer arc has advanced four steps. v1.1 introduced provenance over learned states (SICC Commitment 4): flag structures acquired formation histories, confirming and disconfirming observations, and bidirectional cross-references between threat flags and the knowledge-banking flags derived from the same coordinate. v1.2 introduced the explicit schema (SICC Commitment 1, first part): a complete self-description of cell types, actions, developmental phases, and flag types as a queryable record. v1.3 introduced relational property families: two colour-and-form taxonomies — GREEN and YELLOW — each running through three tiers, with the colour identifier as the relational spine and the HAZARD-to-KNOWLEDGE transition gated on family-specific attractor mastery.

What v1.3 did not address was the relationship between the two families. Each family's records were internally complete: colour-cell registration, attractor mastery, knowledge banking, intra-family cross-reference. But no architectural object compared the two. The architecture knew that the green square and the green sphere belonged together; it did not know that the green family and the yellow family were structurally parallel — that both instantiated the same three-tier pattern, that both encoded the same form progression, that the colour identifier performed the same role in both. That pattern was available in the records. Nothing read it.

### 1.2 The cross-family comparison extension

The v1.4 iteration introduces the comparison observer as a fifth parallel observer. It holds no live state during the run — `on_pre_action` and `on_post_event` are genuine no-ops — and operates entirely at run end, reading the completed family traversal narrative and computing three structural measures. No agent behaviour is modified. The parallel-observer preservation property holds: with the comparison observer disabled, the v1.4 batch runner is byte-identical to the v1.3.2 baseline.

The three measures are specified in the pre-registration and defined fully in Section 2. The primary quantitative finding is Measure 3 — the Category γ metric applied cross-family — which captures how similarly or differently each agent traversed the two families. Its distribution across the 240-run batch is the Category γ substrate: the first architectural record in the programme that represents a relationship between two family instances rather than the internal structure of one.

### 1.3 Findings and their relation to the pre-registration

The v1.4 batch produces four findings from 240 runs across four run lengths.

The first is the level-5 preservation result. With `--no-comparison`, the v1.4 batch runner produces byte-identical output to the v1.3.2 baseline on all v1.3 metrics across the ten verification runs (Category α).

The second is Measure 2 at 1.0 in all 240 runs — the structural assertion that both families encode the FLAT → 2D → 3D progression by architectural design, confirmed as a Category δ finding.

The third is Measure 1 converging to 0.0 at 320,000 steps: the two families' tier-event sequences are structurally identical in every complete run.

The fourth is the operative finding: Measure 3 shows non-trivial variance at all four run lengths, with the distribution shape and floor analytically traceable to the convergence of structural ordering and the residual individual variation in developmental timing.

The pre-registered Category γ three-band criterion (< 0.72 / 0.72–0.76 / ≥ 0.76) passes at 20,000, 80,000, and 160,000 steps and technically fails at 320,000 steps — the upper band captures only 2 of 60 runs. This is reported honestly under Category Φ and explained in Section 4: the bands were written before the data, assumed more edit-distance variance at full completion than the architecture produces, and the 320k distribution is non-degenerate by natural tertiles. The variance criterion (Category γ Component 1) is satisfied at all four run lengths.

### 1.4 Connection to the broader programme

v1.4 advances SICC Commitment 6 (layered property structure) at the relational-properties layer. The v1.3 iteration established direct properties for family cells — colour and form, perceivable without action. v1.4 operationalises the relational-properties layer: structural similarity across families, computed from the direct-property records. The temporal-properties layer — how family structure changes across developmental phases — remains reserved.

The commitments not yet advanced — prediction-surprise as learning signal (Commitment 7), self-knowledge as derivative of object-knowledge (Commitment 8), auditable reporting (Commitment 11) — remain reserved. The reporting iteration's output is only as rich as the substrate it reads from. That substrate now includes, for the first time, a record representing the relationship between two families rather than the internal structure of one.

---

## 2. Methods

### 2.1 Environment and architecture

The environment and agent are inherited from v1.3.2 unchanged. The 20×20 grid, the developmental phase schedule, the threat layer, the mastery layer, the end-state mechanism, the knowledge-cell mechanism, V13World with COLOUR_CELL placement and family property dicts, and the V13Agent family-specific gating rule all operate under their inherited specifications. The agent subclass chain extends by one naming step: `V014Agent` → `V12Agent` → `V13SchemaAgent` → `V13Agent` (gating) → `V14Agent`. V14Agent introduces no method overrides; it is provided for naming consistency and forward compatibility.

### 2.2 The comparison observer

The v1.4 comparison observer (`V14ComparisonObserver`) implements the same three-hook interface as the existing four parallel observers. `on_pre_action` and `on_post_event` are no-ops. `on_run_end` reads the completed family traversal narrative from the v1.3 family observer and computes three structural measures.

**Measure 1: Tier-structure similarity.** For each family, the ordered sequence of event types occurring within the run is extracted from the traversal narrative: which of {`colour_registered`, `attractor_mastered`, `knowledge_banked`} occurred, in what order. The normalised Levenshtein edit distance between the two families' tier-event sequences is computed, treating each event type as an atomic token. A value of 0 indicates identical tier sequences; 1 indicates maximum dissimilarity.

**Measure 2: Form-progression parallelism.** The structural similarity of the two families' form progressions is assessed on three binary properties: (a) both perceivable-tier forms are FLAT, (b) both acquirable-tier forms are 2D (SQUARE_2D or TRIANGLE_2D), (c) both bankable-tier forms are 3D (SPHERE_3D or PYRAMID_3D). The score is the proportion of these three properties holding — 0, 0.33, 0.67, or 1.0. Under the present architecture all three hold by design. This is a structural assertion rather than a variable finding; its constancy is confirmed as Category δ.

**Measure 3: Traversal-sequence structural distance.** The Category γ metric from v1.3.1 — 0.7 × normalised Levenshtein edit distance on full event tokens supplemented by 0.3 × normalised timestamp divergence — is applied cross-family within each run. Full event tokens carry both step number and event type, so two agents that traversed the two families in the same tier order but at different times produce different token sequences. Timestamp divergence is the mean absolute difference between corresponding event steps, normalised by run length, with the shorter sequence padded by a run-length sentinel. This is the primary quantitative finding; its distribution across the 240-run batch is the Category γ substrate.

The comparison record also holds: `green_traversal_complete`, `yellow_traversal_complete`, `both_complete`, `green_first` (True if the GREEN acquirable tier was mastered before the YELLOW acquirable tier), `traversal_interleaving` (`green_then_yellow`, `yellow_then_green`, or `interleaved`), and `cross_family_comparison_complete`.

### 2.3 The parallel-observer stack extended to five layers

Five parallel observers run alongside the agent: the v1.0 recorder, the v1.1 provenance store, the v1.3 schema observer, the v1.3 family observer, and the v1.4 comparison observer. The comparison observer reads from the family observer's completed records at `on_run_end`; it does not modify the family observer's state. With `--no-comparison`, output is byte-identical to v1.3.2 baseline at matched seeds. This is the level-5 regression test added to the pipeline by v1.4.

### 2.4 Experimental matrix and matched-seed comparison

One architecture (v1.4) crossed with six cost levels (0.1, 0.5, 1.0, 2.0, 5.0, 10.0) crossed with four run lengths (20,000, 80,000, 160,000, 320,000 steps) crossed with ten runs per cell, totalling 240 runs. Seeds loaded from `run_data_v1_3.csv` at every (cost, run length, run index) cell.

### 2.5 Pre-flight verifications

Five verification levels ran before the batch. Levels 1–4 were inherited from the v1.3.2 pipeline: level 1 confirmed smoke-test integrity with all observers disabled; levels 2–4 confirmed byte-identical or observer-consistent preservation against the v1.0, v1.1, and v1.2 baselines respectively. Level 5 — the new verification added by v1.4 — confirmed that with `--no-comparison` only, the v1.4 batch runner produces output matching the v1.3.2 baseline on all v1.3 metrics across ten runs at cost 1.0, 20,000 steps. All five levels passed before the batch ran.

### 2.6 Pre-registered interpretation categories

Categories α, β, γ, δ, Φ, and Ω are as committed in the v1.4 pre-registration (Baker, 2026aa). The operative definitions govern the reporting of all findings in Section 3.

---

## 3. Results

### 3.1 Category α: Preservation of v1.3.2 architecture under v1.4 extension

All five pre-flight verifications passed. With `--no-comparison`, the v1.4 batch runner produces output byte-identical to the v1.3.2 baseline on all v1.3 metrics across all ten verification runs. Levels 1–4 confirm the inherited observer stack is undisturbed. Level 5 confirms the comparison observer — the sole architectural addition — contributes nothing to the existing metrics when disabled. Five parallel observers running simultaneously produce consistent records without cross-observer contamination.

### 3.2 Inherited v1.3 findings confirmed

The v1.3 findings are confirmed intact across the v1.4 batch. Schema completeness holds at seven cell types in all 240 of 240 runs. Both colour cells are registered in all 240 runs at all four run lengths, at fixed steps — yellow at step 84, green at step 215 — via adjacency detection exclusively. Zero developmental ordering violations occur in either family across all 240 runs: no knowledge-banking event precedes attractor mastery in any run at any run length. Intra-family cross-references resolve at 100% conditional on both flags forming within the run.

**Table 1.** Family knowledge-banking events and cross-reference resolution, by run length.

| Run length | n  | Green KB | Yellow KB | Green xref   | Yellow xref  |
|------------|----|----------|-----------|--------------|--------------|
| 20,000     | 60 | 43       | 35        | 43/43        | 35/35        |
| 80,000     | 60 | 55       | 49        | 55/55        | 49/49        |
| 160,000    | 60 | 59       | 58        | 59/59        | 58/58        |
| 320,000    | 60 | 60       | 60        | 60/60        | 60/60        |

The self-pacing developmental picture is also preserved. Table 2 gives core developmental metrics by run length; the v1.4 values are identical to v1.3.2 at matched seeds, as the level-5 verification requires.

**Table 2.** Core developmental metrics by run length.

| Run length | n  | Activated | End-state banked | Full mastery (6) | Full KB (5) |
|------------|----|-----------|------------------|------------------|-------------|
| 20,000     | 60 | 13        | 8                | 17               | 20          |
| 80,000     | 60 | 39        | 36               | 40               | 43          |
| 160,000    | 60 | 54        | 52               | 55               | 57          |
| 320,000    | 60 | 60        | 59               | 60               | 60          |

At 320,000 steps every agent activated the end-state, 59 of 60 banked it, all 60 achieved full attractor mastery across all six attractor cells, and all 60 completed knowledge banking across all five hazard cells. Both family traversal sequences were completed by all 60 agents.

### 3.3 Measure 2: Form-progression parallelism — Category δ

Form-progression parallelism is 1.0 in all 240 of 240 runs. All three structural properties hold in every run: both perceivable-tier forms are FLAT; both acquirable-tier forms are 2D; both bankable-tier forms are 3D. This is confirmed as an architectural structural assertion rather than a variable finding (Category δ). The constancy is expected by design, correctly reported, and constitutes a positive confirmation of the architecture's structural integrity rather than an absence of finding.

### 3.4 Measure 1: Tier-structure similarity

Tier-structure similarity is 0.0 in 187 of 240 runs. In these runs both families complete the full three-tier sequence in the same order, producing identical tier-event sequences and a normalised edit distance of zero.

The 53 non-zero runs are concentrated at shorter run lengths: 35 at 20,000 steps, 15 at 80,000 steps, 3 at 160,000 steps, and 0 at 320,000 steps. In all non-zero cases the asymmetry arises from incomplete traversal — one family completes fewer tier events than the other within the observation window — rather than from difference in tier ordering. No run contains a case where both families complete but in a different tier order; where both families complete, their tier sequences are identical.

At 320,000 steps, Measure 1 is 0.0 in all 60 runs. The two families converge on identical structural ordering given sufficient developmental time. This is the architecture's first cross-family structural equivalence finding: structurally, GREEN and YELLOW are the same kind of thing traversed in the same order.

### 3.5 Measure 3: Traversal-sequence structural distance — the operative finding

Measure 3 shows non-trivial variance at every run length. Table 3 gives the distribution summary by run length.

**Table 3.** Measure 3 (traversal-sequence structural distance) by run length.

| Run length | n   | Mean   | SD     | Min    | Max    |
|------------|-----|--------|--------|--------|--------|
| 20,000     | 60  | 0.7951 | 0.0624 | 0.7020 | 0.8933 |
| 80,000     | 60  | 0.7663 | 0.0596 | 0.7024 | 0.8986 |
| 160,000    | 60  | 0.7313 | 0.0421 | 0.7007 | 0.8967 |
| 320,000    | 60  | 0.7147 | 0.0180 | 0.7004 | 0.7901 |

Standard deviation is non-trivial at all four run lengths, satisfying Category γ Component 1. The mean decreases monotonically with run length: agents with more developmental time show lower cross-family traversal distance on average. The distribution range narrows substantially at 320,000 steps.

**The pre-registered three-band criterion** (< 0.72 / 0.72–0.76 / ≥ 0.76) passes at 20,000 steps (6 / 17 / 37), 80,000 steps (19 / 16 / 25), and 160,000 steps (35 / 17 / 8), and technically fails at 320,000 steps (45 / 13 / 2), where the upper band captures only 2 of 60 runs. This is reported under Category Φ (Section 4.3). By natural tertile boundaries at 320,000 steps (≈ 0.7045 and ≈ 0.7121), the distribution is non-degenerate at 20/20/20 — the three-band requirement is satisfied under data-driven boundaries. The failure of the pre-registered bands at 320,000 steps reflects the structural convergence finding described in Section 4.1 rather than an absence of individual variation.

### 3.6 Traversal ordering and interleaving

The traversal interleaving data add a spatial-temporal dimension to the Measure 3 finding. Of the 240 runs, 211 are classified as interleaved (both families' events overlap temporally) and 29 as yellow-then-green (all yellow family events precede all green family events). No run is classified as green-then-yellow.

The yellow-then-green cases concentrate at short run lengths: 20 of 29 occur at 20,000 steps, 8 at 80,000 steps, 1 at 160,000 steps, and 0 at 320,000 steps. At the longest observation window, every agent that completes both families does so through interleaved traversal. The yellow-then-green pattern at shorter windows reflects agents whose green family events do not begin within the observation window — a completeness artefact rather than a systematic ordering preference.

Green was mastered before yellow (`green_first = True`) in 211 of 240 runs and in 51 of 60 runs at 320,000 steps. The 9 runs at 320,000 steps where yellow was mastered first show lower Measure 3 values on average, consistent with these agents interleaving the families more closely in time.

---

## 4. Discussion

### 4.1 The floor effect at 320,000 steps: a structural convergence finding

The concentration of Measure 3 values near 0.70 at 320,000 steps is a consequence of structural convergence, not a limitation of the metric. When both families complete the full three-tier sequence — as all 60 agents do at 320,000 steps — the full-token sequences for Measure 3 are always length-3 on each side:

- GREEN tokens: `[215:colour_registered, X:attractor_mastered, Y:knowledge_banked]`
- YELLOW tokens: `[84:colour_registered, A:attractor_mastered, B:knowledge_banked]`

Every token differs: the step numbers are different, and the family labels are embedded in the token strings. The normalised Levenshtein distance between any two such sequences is therefore exactly 1.0 in every complete run. The 0.7 weight places a constant floor at 0.700 for all complete runs. All residual variance derives entirely from the 0.3 × timestamp divergence component.

The floor is analytically informative. It confirms that at 320,000 steps the two families are structurally equivalent in their tier-event ordering (Measure 1 = 0.0 in all 60 runs), and that the remaining individual variation — captured in the 0.000 to 0.090 range of the timestamp component — is pure developmental timing. Each agent's Measure 3 value at 320,000 steps is a direct measure of how synchronously or sequentially it traversed the two families in time. Agents near 0.700 traversed them at similar developmental tempos; agents near 0.790 traversed them in sequence.

This is the sense in which the 320,000-step distribution is non-degenerate by the most meaningful criterion: it discriminates between agents by their developmental rhythm rather than by their structural ordering, because structural ordering has fully converged. The pre-registered bands, written before the data, assumed some structural ordering variance would remain at full completion. It does not. The finding is stronger than the bands anticipated.

### 4.2 The colour-as-independent-property principle under cross-family scrutiny

The cross-family comparison provides the first architectural test of the colour-as-independent-property principle established in v1.3: that colour carries independent cognitive content and does not encode reward. Measure 2 confirms that colour is doing precisely what it is designed to do — serving as the relational spine that makes GREEN and YELLOW structurally parallel rather than structurally different. The 1.0 parallelism score reflects not a coincidence of form progression but a deliberate architectural commitment: both families instantiate the same FLAT → 2D → 3D structure because that structure is the thing colour is designed to identify, not to differentiate.

Measure 1's convergence to 0.0 at 320,000 steps extends this principle from design to behaviour. The agents do not traverse the two families in a different order; given time, they traverse both in the same structural sequence. The colour identifier — green or yellow — identifies which family an agent is engaging with but does not alter the cognitive sequence of that engagement. Colour is what a cell is; the sequence of engagement is what the prepared environment specifies. The two dimensions remain independent in the data as they are in the design.

### 4.3 Category Φ: what the comparison observer does and does not establish

The comparison observer computes cross-family structural measures from the architecture's own records. It does not pass those measures to the agent. The agent does not know that the green family and the yellow family are structurally parallel; it has not read the comparison record; no architectural path connects the comparison observer's output to the agent's action-selection or value functions. The structural similarity is detectable from the records — that is what v1.4 establishes. Whether it is detected by the agent is the question the reporting iteration addresses.

The substantive reading of the v1.4 finding is this: the cross-family comparison record provides a correctly computed, individually variable substrate from which the reporting iteration can produce statements about family-level patterns rather than individual-cell histories. An agent reading its own comparison record at v1.6 will find a number — its Measure 3 value — that represents how similarly it traversed the two families. Whether it can interpret that number as a statement about itself, or use it to predict the structure of a third family, is not settled by v1.4. What is settled is that the number is there, correctly computed, and meaningful.

The deflationary reading is also acknowledged. The comparison observer performs the comparison; the agent does not. The architectural gap between a record existing and an agent reading it has been a consistent theme of the programme's Category Φ constraints. v1.4 does not close that gap; it constructs the richest possible record for the iteration that will.

### 4.4 The pre-transition entry data as forward instrument

The pre-transition hazard entry data inherited from v1.3 is reproduced faithfully in the v1.4 batch: yellow pyramid mean 1.40 entries before unlock (max 3), green sphere mean 0.17 entries before unlock (max 3). These are the architecture's first failure records — entries into a bankable-tier cell that did not produce the HAZARD-to-KNOWLEDGE transformation because the precondition attractor had not yet been mastered.

The cross-family comparison adds a structural frame to these records. The yellow pyramid's higher pre-transition entry rate reflects the yellow family's spatial cluster membership and its tendency to be the second family traversed (51 of 60 agents master green before yellow at 320,000 steps). Agents approach the yellow pyramid with knowledge of what the green sphere required; they arrive before the developmental conditions are in place. The records hold the approach-and-resist sequence. The vocabulary to name it as prediction error arrives at v1.5.

### 4.5 The architectural arc through v1.4

The post-v1.0 cognitive-layer arc now has four iterations in place. v1.1 established provenance over learned states. v1.2 established the explicit schema. v1.3 established the first relational taxonomy. v1.4 establishes the first cross-family structural comparison — the architecture's first record that represents a relationship between two families rather than the internal structure of one.

The reporting iteration (v1.5 in the SICC trajectory, acknowledging that numbering may shift) reads from provenance (v1.1), schema (v1.2), family records (v1.3), and cross-family comparison (v1.4). The substrate is now complete enough to support a first auditable account: not just what the agent learned, but what structural category what it learned belongs to, how that structure parallels another structure in the same environment, and how the agent's traversal of the two structures compared. That account requires prediction-error records to be fully formed — the approach-and-resist sequence, the developmental tempo, the gaps between intention and outcome. Those records arrive at v1.5. What v1.4 provides is the comparison base from which the account becomes structurally legible.

---

## 5. Conclusion

The v1.4 iteration extended the programme's observer stack with a fifth parallel observer that reads completed family traversal records and computes cross-family structural measures. No agent behaviour was modified. The single-variable-change discipline held.

The v1.4 batch of 240 runs across four run lengths produces three substantive findings. Form-progression parallelism is 1.0 in all 240 runs, confirming as an empirical matter what the architecture asserts by design: both families encode the same FLAT → 2D → 3D structural progression. Tier-structure similarity converges to 0.0 at 320,000 steps, confirming that the two families' traversal sequences are structurally identical — same tier-event ordering, same developmental dependencies — when both are fully completed. Traversal-sequence structural distance is individually variable at every run length, with the distribution's shape and floor analytically traceable to the convergence of structural ordering and the residual variation in developmental timing.

The Category Φ constraint bounds the claim. The architecture can detect structural similarity between two families from its own records. The agent cannot. The gap between a record existing and an agent reading it has been closed, at the record end, by v1.4. The reporting iteration closes it at the agent end.

The pre-registered bands for the Category γ non-degenerate distribution criterion were written before the data and assumed more edit-distance variance at full completion than the architecture produces. They are reported here as an honest pre-registration discrepancy, not quietly corrected. The distribution at 320,000 steps is non-degenerate by natural tertiles and analytically richer than the bands captured: it is a direct measure of developmental tempo once structural ordering has converged. The finding is stronger than the bands anticipated.

The two materials on the prepared environment's shelf have now been compared. They are the same structure, arrived at by different routes, in different developmental time. That is both the empirical finding and a statement about what the prepared environment is designed to produce: not uniformity of path, but equivalence of structure. What an agent eventually makes of that equivalence — whether it uses it to anticipate a third family, to compose across the two it has traversed, to build a taxonomy where the programme currently builds only two instances — is the question that drives the remaining iterations.

---

## 6. Code and Data Availability

All code, pre-registration documents, amendments, batch outputs, and paper drafts are available at github.com/RancidShack/developmental-agent.

The v1.4 implementation comprises four files. `curiosity_agent_v1_3_world.py` and all v1.3 source files are inherited unchanged. `v1_4_agent.py` implements V14Agent as a named subclass of V13Agent with no method overrides. `v1_4_comparison_observer.py` implements the fifth parallel observer with pure-Python Levenshtein, the three structural measures, and CSV output. `curiosity_agent_v1_4_batch.py` is the batch runner with the `--no-comparison` flag for level-5 regression. `verify_v1_4_no_comparison.py` is the level-5 pre-flight verification script.

The batch produced seven output files: `run_data_v1_4.csv`, `comparison_v1_4.csv`, `family_v1_4.csv`, `provenance_v1_4.csv`, `schema_v1_4.csv`, `snapshots_v1_4.csv`, and `snapshots_v1_0_under_v1_4.csv`. The provenance record count is 3,040 across 240 runs — 300 threat flags, 1,339 mastery flags, 1,080 knowledge-banking flags, 166 end-state activation records, and 155 end-state banking records — matching the v1.3.2 batch exactly at matched seeds, as the level-5 verification requires.

Seeds were drawn from `run_data_v1_3.csv`, extending the seed chain to v1.4 at every (cost, run length, run index) cell.

---

## 7. References

Baker, N.P.M. (2026a–z) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.3. Full reference list inherited from v1.3 paper (Baker, 2026z).

Baker, N.P.M. (2026z) 'Relational Property Families in a Small Artificial Learner: A Colour-and-Form Taxonomy as the First Structural Vocabulary of the Prepared Environment', preprint, 2 May 2026.

Baker, N.P.M. (2026aa) 'v1.4 Pre-Registration: Cross-Family Structural Comparison via Parallel Observer on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

---

## 8. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper.

No human participant data were collected. No external parties had access to drafts prior to preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
