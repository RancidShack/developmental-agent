# v1.3.1 Pre-Registration Amendment

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Amendment to v1.3 Pre-Registration, committed before v1.3.1 batch runs
**Repository:** github.com/RancidShack/developmental-agent
**Amends:** v1.3 Pre-Registration (Baker, 2026w), committed 1 May 2026
**Amendment number:** 1 of 3 available

---

## Purpose of this amendment

The v1.3 initial batch (180 runs, seeds matched to v1.2, run lengths 20,000 / 80,000 / 160,000 steps) identified two issues requiring correction before the batch can support the paper's claims, and one methodological extension warranted by the programme's developmental framing. This amendment addresses all three in a single pre-registration commitment before the corrected batch runs.

The three changes are:

1. **Schema observer correction.** The v1.2 schema observer (`V12SchemaObserver`) hardcodes six expected cell types and was not extended to recognise `COLOUR_CELL = 6` when v1.3 introduced it. The initial batch consequently reports `schema_cell_types_count = 6` and `schema_complete = True` in all 180 runs — both values are incorrect for the v1.3 architecture, which has seven cell types. A `V13SchemaObserver` subclass is specified here that correctly expects seven cell types and serialises COLOUR_CELL's property vector. The v1.3 paper's Category β schema-completeness claim cannot be made honestly against the initial batch data; the corrected batch is the evidential basis for that claim.

2. **Extended run length: 320,000 steps.** The v1.3 experimental matrix specified three run lengths (20,000 / 80,000 / 160,000 steps). The initial batch results show that the yellow family cross-reference completion rate is flat across all three lengths — 27/60, 30/60, and 30/60 respectively — indicating that the relevant developmental window for yellow family traversal extends beyond 160,000 steps for a substantial proportion of agents. The Montessori developmental framing the programme operates under treats run length as an observation window rather than a deadline: agents arrive at materials when they are ready, and a window that closes before arrival is a methodological constraint, not a finding about the agent's capacity. A 320,000-step run length is added as a fourth observation window. The experimental matrix becomes 4 run lengths × 6 cost levels × 10 runs = 240 runs.

3. **Category γ structural-distance metric specification.** The v1.3 pre-registration (§6.3) reserved a v1.3.1 amendment to specify the structural-distance metric for family traversal narratives before any Category γ structural-distance analysis is performed. This amendment discharges that reservation.

---

## Amendment 1: Schema observer correction

### What the v1.3 pre-registration specified (§2.6 and §5)

Section 2.6 of the pre-registration states: "The schema's cell-types count increases from 6 to 7 (the addition of COLOUR_CELL)." Section 5 states: "The schema's cell-types count is now expected to be 7 (addition of COLOUR_CELL). Schema complete requires all four sections populated with the extended property matrix."

### What the initial batch produced

`schema_cell_types_count = 6` in all 180 runs. `schema_complete = True` in all 180 runs. Both values are inconsistent with the pre-registration's specification. The cause: `V12SchemaObserver.EXPECTED_CELL_TYPES` contains six entries and `on_run_end()` iterates a hardcoded list of six cell type names, so COLOUR_CELL is neither serialised nor counted.

### The correction

A `V13Agent` subclass of `V12Agent` overrides `_build_schema()` to add COLOUR_CELL to the cell-type schema with the property vector specified in pre-registration §2.2:

```
COLOUR_CELL: passable=True, cost_on_entry=None,
             feature_reward_eligible=False,
             attraction_bias_eligible=False,
             gating_eligible=False,
             transformation_eligible=False
```

A `V13SchemaObserver` subclass of `V12SchemaObserver` updates `EXPECTED_CELL_TYPES` to include `"COLOUR_CELL"`, serialises six additional CSV columns (`ct_COLOUR_CELL_*`), and recomputes `schema_cell_types_count` and `schema_complete` against the extended expected set. `SCHEMA_FIELDS_V13` is the extended field list used for the v1.3.1 schema CSV.

Both subclasses are implemented in `v1_3_schema_extension.py`. The v1.3.1 batch runner imports `V13Agent` and `V13SchemaObserver` from this module in place of their v1.2 equivalents. No other file is modified.

### Preservation implications

`V13Agent._build_schema()` adds one entry to the schema dict. No behavioural method is overridden. The agent's action-selection, drive composition, and value-update paths are unchanged. The level-4 regression test (`--no-family`, V12World shim) must pass at 10/10 before the v1.3.1 batch runs, confirming that the schema addition does not contaminate behaviour.

### Category β restatement

The corrected Category β claim for the v1.3.1 paper: `schema_cell_types_count = 7` and `schema_complete = True` in all 240 runs.

---

## Amendment 2: Extended run length — 320,000 steps

### Rationale

The programme's prepared-environment framing, drawn from the Montessori developmental literature, treats run length as an observation window rather than a performance deadline. A child who has not yet reached the pink tower at the close of one session is not failing; the tower is on the shelf, and the child will arrive when the developmental conditions are in place. Truncating the observation window at 160,000 steps when a substantial proportion of agents have not yet completed the yellow family traversal sequence produces an incomplete developmental record, not a finding about the architecture's capacity.

The initial batch yellow cross-reference data supports this framing directly. At 160,000 steps: 30/60 yellow cross-references are complete, 28/60 show knowledge banking before attractor mastery (an artefact of the general competency mechanism discussed under Category Ω below), and 2/60 show neither — the yellow knowledge cell was never reached. The 30/60 complete rate is flat from 80,000 steps, indicating that the relevant developmental window for the remaining agents lies beyond 160,000 steps. A 320,000-step window extends the observation to cover those agents.

### Experimental matrix amendment

The experimental matrix is amended from:

> one architecture (v1.3) × six cost levels × **three** run lengths (20,000 / 80,000 / 160,000) × ten runs per cell = **180 runs**

to:

> one architecture (v1.3) × six cost levels × **four** run lengths (20,000 / 80,000 / 160,000 / **320,000**) × ten runs per cell = **240 runs**

Seeds for the 320,000-step runs are drawn from `run_data_v1_2.csv` at matched (cost, run_index) cells using the same priority order as the existing seed chain (v1.2 > v1.1 > v1.0 > v0.14). Where the v1.2 baseline does not include a 320,000-step run at a given (cost, run_index) cell, the seed from the 160,000-step run at the same cell is used, consistent with the programme's established seed-inheritance practice for new run lengths.

### What this does not change

The 20,000 / 80,000 / 160,000-step runs are re-executed at matched seeds to incorporate the schema correction (Amendment 1). All other experimental parameters — six cost levels, ten runs per cell, V13World, four parallel observers — are unchanged.

---

## Amendment 3: Category γ structural-distance metric specification

### Reservation discharged

The v1.3 pre-registration §6.3 reserved this amendment: "A v1.3.1 amendment will specify a structural-distance metric for the family traversal narratives, parallel to the v1.1.1 amendment for the formation narrative metric. The amendment is committed before any Category γ structural-distance analysis is performed on the v1.3 batch."

### Metric specification

The family traversal narrative for a run is an ordered sequence of timestamped family events:

```
step_1:event_1:family_1 | step_2:event_2:family_2 | ...
```

where `event` ∈ {`colour_registered`, `attractor_mastered`, `knowledge_banked`} and `family` ∈ {`GREEN`, `YELLOW`}.

The structural-distance metric between two narratives A and B is defined as follows.

**Step 1 — Event-sequence extraction.** From each narrative, extract the ordered sequence of (event, family) pairs, discarding timestamps. This produces a sequence of categorical tokens, e.g. `[(colour_registered, GREEN), (colour_registered, YELLOW), (attractor_mastered, GREEN), ...]`.

**Step 2 — Normalised edit distance.** Compute the Levenshtein edit distance between the two token sequences, treating each (event, family) pair as an atomic token. Normalise by the length of the longer sequence. This produces a value in [0, 1], where 0 indicates identical event-order sequences and 1 indicates maximum dissimilarity.

**Step 3 — Timestamp divergence supplement.** For event tokens present in both sequences at the same position, compute the absolute difference in step values, normalised by the run length. Average across matched positions. This supplements the edit distance with information about when events occurred relative to the run length, capturing divergence in developmental pace independently of event order.

**Step 4 — Combined distance.** The structural distance D(A, B) = 0.7 × normalised_edit_distance + 0.3 × timestamp_divergence_supplement. The 0.7/0.3 weighting prioritises event-order structure (which family the agent traversed first, in what sequence) over timing (how quickly it did so), consistent with the programme's interest in developmental sequence rather than developmental speed.

### Substantive differentiation floor

The substantive differentiation floor for Category γ Component 1 is D > 0.15 for at least 95% of within-cell pairwise comparisons, parallel to the v1.1 formation narrative standard. Pairs below this floor are not considered individuated at the structural level, regardless of timestamp differences.

### Pre-registration commitment

No Category γ structural-distance analysis is performed on the v1.3.1 batch until this metric specification has been committed to the repository. The commitment is this document.

---

## Impact on pre-registration sections

The following sections of the v1.3 pre-registration are amended by this document:

**Section 2.6 (Schema additions):** The v1.2 schema observer is replaced by `V13SchemaObserver` from `v1_3_schema_extension.py`. `SCHEMA_FIELDS_V13` is the operative field list for the v1.3.1 schema CSV.

**Section 3 (Experimental matrix):** Run lengths are 20,000 / 80,000 / 160,000 / 320,000 steps. Total runs are 240.

**Section 5 (Metrics):** `schema_cell_types_count` expected value is 7 in all 240 runs. `schema_complete` expected value is True in all 240 runs.

**Section 6.2 (Category β):** The schema-completeness condition is amended to require `schema_cell_types_count = 7` in all 240 runs.

**Section 6.3 (Category γ):** The structural-distance metric is now specified (Amendment 3 above). The reservation for v1.3.1 is discharged.

**Section 6.4 (Category δ):** The second pre-anticipated finding (cross-reference completion bounded by run length) is partially superseded by the addition of the 320,000-step window. The finding is reformulated: cross-reference completion is reported at each observation window as a developmental snapshot, with the expectation that completion rates increase monotonically across windows. Rates that do not increase from 160,000 to 320,000 steps are a genuine finding about the architecture's competency-gating mechanism, reported honestly and analysed under Category Ω.

**Section 9 (Stopping rule):** Total runs required is 240. The v1.3.1 amendment reservation (Category γ metric) is discharged by this document. Remaining amendment budget: two of three.

---

## Implementation files

The following files implement this amendment. All are committed to the repository before the v1.3.1 batch runs:

- `v1_3_schema_extension.py` — `V13Agent`, `V13SchemaObserver`, `SCHEMA_FIELDS_V13`
- `curiosity_agent_v1_3_batch.py` — updated to import `V13Agent`, `V13SchemaObserver`, `SCHEMA_FIELDS_V13`; default steps extended to include 320,000
- `verify_v1_3_no_family.py` — level-4 regression test; re-run before v1.3.1 batch

The level-4 regression test must pass at 10/10 before the v1.3.1 batch runs.

---

## References

Baker, N.P.M. (2026w) 'v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026x) 'v1.3.1 Pre-Registration Amendment: Schema Observer Correction, Extended Run Length, and Category γ Metric Specification', GitHub repository, 2 May 2026.

---

**Amendment commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before the v1.3.1 batch runs.
