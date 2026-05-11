# v1.1.1 Pre-Registration Amendment: Category γ Structural-Distance Metric Specification

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 30 April 2026
**Status:** Pre-registration amendment, committed to public repository before any reanalysis of the v1.1 batch is performed
**Repository:** github.com/RancidShack/developmental-agent
**Amendment scope:** Operational, not architectural
**Amendment budget:** 1 of 3 (per v1.1 pre-registration §7)

---

## 1. Purpose of this amendment

The v1.1 pre-registration (§5.3) committed to a *family* of structural-distance metrics for Category γ — pairwise measures of difference between agents' formation narratives, satisfying four required properties (formation order, cross-reference structure, confirmation patterns, not driven primarily by timestamp differences) — and reserved the specific operationalisation for v1.1.1 amendment after the records existed to be examined.

The records now exist (Baker, 2026r, in preparation, v1.1 batch). This amendment commits the specific operationalisation before any Category γ analysis is performed on the batch. The v1.1.1 amendment is operational rather than architectural: no v1.1 code is modified, no batch is re-run, no architectural specification changes. What changes is the analytical machinery the v1.1 paper applies to the existing records.

The amendment is committed in advance of the analysis on the same methodological principle that has held throughout the programme: thresholds and metrics are pre-specified before the data they apply to is examined for fit.

## 2. Operationalisation

The Category γ metric is a **pairwise structural distance** between formation narratives, operating at the per-agent-pair level. For each pair of agents (i, j) in the batch, the metric produces a non-negative real-valued distance d(i, j) representing the structural difference between their learning histories as recorded in the v1.1 provenance store.

The metric has four components, each addressing one of the required properties from §5.3 of the pre-registration. Each component is normalised to [0, 1] so that the components are commensurable. The composite distance is the weighted sum of the four components with equal weights (0.25 each); equal weighting is committed in this amendment to avoid post-hoc weight calibration. The composite distance lies in [0, 1].

### 2.1 Component 1: Formation-order distance d_order

Treats each agent's formation narrative as the ordered sequence of flag identifiers (`flag_type:coord` strings, with `end_state_activation` as a fixed sentinel). Computes the **normalised Kendall tau distance** between the two sequences over the symmetric set of flag identifiers shared between them. Flag identifiers present in only one agent's narrative are excluded from the order computation; the asymmetric content is captured by the next component.

Formally: let S_i and S_j be the sets of flag identifiers present in agents i and j respectively. Let S_∩ = S_i ∩ S_j. For each pair (a, b) ∈ S_∩ × S_∩ with a ≠ b, count whether the relative order of (a, b) differs between i and j. Normalise by the maximum possible discordant pairs (|S_∩| × (|S_∩| − 1) / 2). If |S_∩| < 2, d_order = 0 (no order to disagree about).

This component captures whether two agents that formed the same flags formed them in different orders.

### 2.2 Component 2: Content-set distance d_content

Captures the asymmetric content. Computes the **Jaccard distance** between the flag identifier sets:

d_content = 1 − |S_i ∩ S_j| / |S_i ∪ S_j|

where S_i and S_j are as above. d_content = 0 when both agents formed exactly the same set of flag identifiers; d_content = 1 when they share none.

This component captures the case where two agents differ not in the order of formation but in *which* flags formed at all — for example, one agent formed a threat flag at coordinate (5, 8) and the other did not.

### 2.3 Component 3: Cross-reference structure distance d_xref

Captures the structural differentiation made possible by the v1.1 cross-reference fields. For each agent, construct the set of cross-reference pairs, where each pair is a tuple (threat_flag_id, knowledge_banking_flag_id) for every threat flag whose `derived_knowledge_flag_id` resolved within the run, plus a sentinel marker for every threat flag with `transformed_at_step` set but cross-reference unresolved (the pending-cross-reference case).

Let X_i and X_j be these cross-reference sets. Compute the Jaccard distance:

d_xref = 1 − |X_i ∩ X_j| / |X_i ∪ X_j|

If both X_i and X_j are empty, d_xref = 0 (no cross-reference structure to differ about).

This component captures whether two agents whose flag-formation histories differ structurally in their threat-to-knowledge transitions: which threat flags transformed into knowledge cells and which did not, which knowledge cells were preceded by threat-flag formation and which transformed before any threat flag formed.

### 2.4 Component 4: Confirmation-pattern distance d_conf

Captures the confirmation density structure across flag types. For each agent, compute the *confirmation density vector* of length five, with one entry per flag type (threat, mastery, knowledge_banking, end_state_activation, end_state_banking). Each entry is the mean confirming-observations count for that flag type across formed flags, normalised by the post-flag-formation window length, treating the case where no flags of that type formed as a zero entry rather than missing.

Let v_i and v_j be these vectors. Compute the **normalised L1 distance**:

d_conf = (1 / 5) × Σ_t |v_i[t] − v_j[t]| / max(v_i[t] + v_j[t], ε)

where t ranges over flag types and ε is a small positive constant (10⁻⁶) preventing division by zero when both entries are zero. This produces a per-flag-type relative-difference measure summed and averaged across the five types. Each flag-type entry contributes [0, 1] to the average; the total d_conf lies in [0, 1].

This component captures whether two agents differ in *how* their flags were sustained, not just *which* flags formed. An agent whose mastery flags accumulated dense post-banking visits has a different confirmation pattern from an agent whose mastery flags formed late and accumulated few visits.

### 2.5 Composite distance d(i, j)

d(i, j) = 0.25 × d_order + 0.25 × d_content + 0.25 × d_xref + 0.25 × d_conf

The composite distance lies in [0, 1]. Equal weighting is committed in this amendment.

## 3. Why these four components

The four components are derived from the four required properties committed in §5.3 of the pre-registration:

- d_order addresses the formation-order property (two agents that formed the same flags in different orders are at non-zero distance).
- d_xref addresses the cross-reference structure property (two agents whose threat-flag-to-knowledge-banking-flag pairings differ are at non-zero distance even where individual flag formations are identical).
- d_conf addresses the confirmation-pattern structure property (two agents whose confirmation densities differ across flag types are at non-zero distance).
- The fourth required property (not driven primarily by raw timestamp differences) is addressed by the *omission* of any timestamp-based component. d_order operates on ordinal sequences, not absolute steps; d_content operates on identifier sets; d_xref operates on cross-reference pairs; d_conf operates on density ratios that normalise out absolute timing. None of the four components is primarily driven by when in absolute step terms a flag formed.

d_content is included beyond the four required properties because it is the natural complement to d_order: d_order captures permutation differences over shared content, d_content captures the asymmetric content. Together they capture the full structural difference at the formation-event level.

## 4. What this metric is *not*

Two clarifications worth committing in this amendment, on the SICC-honest principle that what the metric does *not* measure is part of what the metric is.

The metric does *not* measure behavioural divergence at the action-selection level. Two agents whose actions differ at every step but whose flag formations are identical in identifier set, order, cross-reference structure, and confirmation pattern would have d(i, j) = 0 under this metric. This is appropriate: Category γ is record-scale individuation, not behavioural individuation. The v0.13 paper documented the latter as a separate phenomenon (cross-layer effects). The v1.1 paper's contribution is that *records* differ even when behaviour at the action level is identical (which under matched seeds it broadly is, modulo the post-activation cross-layer effects v0.13 documented).

The metric does *not* incorporate phase boundaries (the Phase 1 → 2 and Phase 2 → 3 transitions inherited from v0.10/v0.11.2/v0.12 and earlier). Phase boundaries are architectural moments that affect what flag formations can occur but they are v1.0-visible structure, not v1.1-introduced structure. Including them would muddy the architectural attribution: any individuation surfaced by the metric should be attributable to v1.1's record-scale extension rather than to v1.0-and-earlier inheritance. Phase boundaries may be referenced narratively in the v1.1 paper as context for when in the developmental schedule a particular record formed, but they do not enter the metric computation.

## 5. Pre-registered Category γ verdict thresholds

The pre-registration's §5.3 committed three success criteria for Category γ:

> Mean structural distance between agent pairs at non-matched conditions exceeds mean structural distance at matched seeds (v1.1 against v1.1) by a margin to be specified in the v1.1.1 amendment.

This amendment specifies the margin operationally as follows. Compute, per (cost, run length) cell:

- d_within_cell: the mean pairwise distance d(i, j) for all i, j with i ≠ j within the cell (i.e. the same cost and run length but different run indices). With 10 runs per cell, this is 45 pairs per cell.
- d_across_cells: the mean pairwise distance d(i, j) for all i, j with i and j in different (cost, run length) cells. This is the across-cell baseline against which the within-cell signal is measured.

**Category γ first criterion succeeds at a (cost, run length) cell** if d_within_cell > 0 substantively — committed here as d_within_cell ≥ 0.05 — *and* d_across_cells > d_within_cell (i.e. agents at different conditions are more different from each other than agents at the same condition, but agents at the same condition are still substantively differentiated). The threshold 0.05 is a soft floor on substantive differentiation; the relative ordering is the substantive test.

> The distribution of structural distances exhibits diversity comparable to or greater than the diversity observed in v1.0's trajectory-scale individuation metrics.

**Category γ second criterion succeeds** if the distribution of d(i, j) values within (cost, run length) cells exhibits a non-trivial spread — committed here as the standard deviation of d(i, j) within at least four of the eighteen (cost, run length) cells exceeding 0.02. This operationalises "non-trivial diversity" without requiring direct comparison to v1.0 trajectory-scale metrics, which would couple this amendment's specification to a v1.0 metric not designed for the comparison.

> The v1.1.1 amendment is committed before any reanalysis of the v1.1 batch is performed.

This amendment is committed on 30 April 2026, before any Category γ structural-distance computation is performed on the v1.1 batch. The amendment is the commitment.

## 6. What an honest negative finding looks like

Per pre-registration §5.3:

> Category γ failure (or partial failure) is honestly reported. If the records turn out to encode less structural diversity than the trajectories that produced them, the finding is informative.

If d_within_cell falls below 0.05 across most (cost, run length) cells, the finding is that v1.1's record schema has under-resolved the individuation v1.0 surfaced. The v1.1 paper would report this directly as a structural finding about the schema's resolution rather than as a Category γ pass.

If d_across_cells does not exceed d_within_cell substantively, the finding is that the records do not differentiate across-condition variation from within-condition variation — that is, the records are differentiated but not in a way that tracks the experimental conditions. This would also be reported directly.

If the standard-deviation criterion fails in fewer than four cells, the finding is that the diversity is concentrated rather than distributed, which is informative about which conditions produce diverse formation narratives and which produce convergent ones.

Per pre-registration §5.3, if an issue is flagged, the v1.1 paper's reporting may extend the run length or adjust counts to either prove the structural-distance signal or discount it. Such extension would be specified in a v1.1.2 amendment under the remaining amendment budget.

## 7. Implementation

The metric is implemented in a standalone analysis script `analyse_v1_1_category_gamma.py` (to be added to the public repository alongside this amendment), which reads `provenance_v1_1.csv` and `run_data_v1_1.csv` and computes:

- Per-agent-pair distance matrix d(i, j) for all 180 × 179 / 2 = 16,110 ordered pairs.
- Per-component breakdown (d_order, d_content, d_xref, d_conf separately) for diagnostic purposes.
- d_within_cell per (cost, run length) cell with mean and standard deviation.
- d_across_cells aggregate.
- Verdict against the two criteria committed in §5 of this amendment.

The script is fully deterministic given the input CSVs; no random seeds, no model fits, no hyperparameter tuning. The metric is a closed-form computation over the records.

## 8. Amendment record

The v1.1 amendment budget per the v1.1 pre-registration §7 is three. v1.1.1 consumes one of three. Two amendments remain available for unanticipated operational issues during the v1.1 paper drafting and analysis phase.

The amendment is operational rather than architectural: no v1.1 code is modified, no batch is re-run, no architectural specification changes. The amendment specifies the analytical machinery applied to the existing records.

---

**Pre-registration commitment:** This amendment is committed to the public repository at github.com/RancidShack/developmental-agent on 30 April 2026, before any Category γ structural-distance computation is performed on the v1.1 batch. Subsequent Category γ analysis proceeds under the operationalisation specified here.

The v1.1 paper, when drafted, references this amendment as the source of the Category γ metric specification.
