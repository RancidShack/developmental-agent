# v1.7 Pre-Registration: Substrate Transposition to a Richer Simulated Environment

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 3 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.7 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

Six iterations have built a cognitive layer — provenance, schema, family traversal, cross-family comparison, prediction-error records, reporting — on a tabular 20×20 grid. The cognitive layer's concepts were specified at the cognitive level: flag types, formation steps, family traversal sequences, resolution windows, biographical registers. None of these specifications referenced the grid in their definitions. Whether they are grid-specific in their implementations is a question only transposition can answer.

v1.7 is that transposition.

The v1.6 iteration completed the cognitive-layer arc. It built a reporting layer designed explicitly to survive substrate change — the `SubstrateBundle` interface names cognitive-layer concepts, not grid-specific constructs. The v1.6 pre-registration stated the substrate-agnosticism obligation as a design commitment before any v1.6 code was written. v1.7 tests whether that commitment was met.

The v1.7 architectural extension is a **new simulated environment** — a 3D continuous-space substrate that replaces the tabular grid — and the substrate-interface work required to connect the existing cognitive layer to it. The cognitive layer itself is not the variable. What changes is the substrate; what is tested is the cognitive layer's response to that change.

**The theoretical grounding of this transposition.** The programme's developmental framing — a prepared environment in which a small learner builds identity through repeated object encounters — requires a substrate in which object contact has the quality of an encounter rather than a cell-entry event. Object-relations theory (Winnicott, Klein, Bowlby) holds that the self emerges through internalisations of repeated object encounters: the object is first perceived at a distance, then approached, then contacted, then internalised — held as a known entity that has been transformed by the relationship rather than erased by it. The tabular grid supported the recording of these events. The v1.7 substrate is designed to support their spatial embodiment: objects that can be perceived before contact, approached across continuous space, and retained as known entities after transformation. This is the Montessori prepared environment principle made spatially operative: the environment's structure does the developmental work; the agent's trajectory through it is the autobiography.

The v1.7 research question: when the tabular grid is replaced by a richer simulated environment, which parts of the cognitive layer carry forward unchanged, and which parts require rebuilding at the substrate interface? Both outcomes are findings. Parts that carry forward confirm the SICC commitments were genuinely operative at the cognitive layer. Parts that require rebuilding identify where grid-specific assumptions were embedded invisibly.

---

## 2. Architectural specification

### 2.1 The new substrate: V17World

V17World is a 3D continuous-space environment. The agent has a real-valued (x, y, z) position and navigates by velocity vector. Objects exist at fixed real-valued coordinates. The environment is bounded. The simulation is fully deterministic given a seed.

**Object types.** V17World contains objects analogous to the six cell types in the tabular grid. The mapping is explicit at the substrate interface and invisible to the cognitive layer:

| Grid cell type | V17World object type | Cognitive-layer concept |
|---|---|---|
| COLOUR_CELL | Distal object | Perceivable tier — family member, perceivable at distance |
| ATTRACTOR | Acquirable object | Acquirable tier — mastery event on contact |
| HAZARD | Costly object | Bankable tier — costly on approach; transforms on precondition |
| KNOWLEDGE | Known object | Post-transformation state of a banked costly object |
| END_STATE | Threshold object | Activation on full-family completion |
| NEUTRAL | Open space | Traversable without event |

**Perception is radial and graduated.** The agent has a bounded perception sphere of radius `r_perceive`. Objects within the sphere are perceivable; their properties (colour, form, family membership) become available as the agent approaches. Objects become fully present on contact (distance below `r_contact`). This gives the approach phase a record distinct from the contact event — the agent can have a first-perception entry in its provenance distinct from first-contact. This two-event structure is the spatial correlate of the object-relational encounter: recognition before acquisition.

**Objects persist after transformation.** After a costly object is banked as known, it remains at its coordinates in a transformed state. The spatial location retains meaning after the cognitive event. The agent can return to the location. The provenance record links the before and after states. This is the internalisation event given spatial form.

**Family structure preserved.** The GREEN and YELLOW family tier structure is carried forward:

- GREEN family: distal object at fixed coordinates (colour=GREEN, form=FLAT), acquirable object (colour=GREEN, form=SQUARE_2D), costly object (colour=GREEN, form=SPHERE_3D)
- YELLOW family: distal object at fixed coordinates (colour=YELLOW, form=FLAT), acquirable object (colour=YELLOW, form=TRIANGLE_2D), costly object (colour=YELLOW, form=PYRAMID_3D)

The family-specific competency gating rule (v1.3.2 amendment) carries forward: the GREEN costly object cannot be banked until the GREEN acquirable object is mastered; equivalently for YELLOW. This rule is defined at the cognitive level and requires only that the substrate interface supply object identities to the competency-gating check.

**Seeds are settable; runs are reproducible.** All stochastic elements (agent start position, object placement within bounded regions) are seeded. The Level-N pre-flight discipline is fully applicable.

### 2.2 The substrate interface: what changes

The following components require new implementation or modification for V17World:

**New implementation (expected):**
- `V17World` — the world class; replaces `V13World`
- The substrate-interface layer — how `perceive_within_radius` works; how object identity is keyed; how approach events are detected
- Object placement — family object coordinates become 3D real-valued positions
- `get_substrate()` implementations for new-substrate observers, if observer internal structure changes

**Modification may be required (the diagnostic surface):**
- `family_precondition_attractor` — currently a coord-keyed dict; must generalise to object-identity keys. Whether this is substrate-interface work or requires touching the family observer's logic is an open question.
- The `mastery:(4, 15)` flag ID format — currently hardcodes grid coordinates. Must generalise to object identities. Whether this is substrate-interface work or requires cognitive-layer amendment is an open question.
- `V15PredictionErrorObserver` — built around grid-entry events (discrete step-onto-cell). In V17World, the analogous event is approach-within-contact-radius. Whether the encounter concept generalises without cognitive-layer modification is an open question and a primary diagnostic surface.

**Expected to carry forward unchanged:**
- `V16ReportingLayer` and `ReportStatement` — built against SubstrateBundle; imports no grid-specific constant
- `SubstrateBundle` and `build_bundle_from_observers()` — cognitive-layer contracts only
- `ProvenanceSubstrateRecord` — substrate-agnostic field set
- The three query types and biographical register — reads from bundle fields, not grid state
- `V1ProvenanceStore` — cognitive-layer provenance; substrate interface only in flag_id format
- `V13SchemaObserver` — may require schema extension for new object types; cognitive-layer structure unchanged
- `V13FamilyObserver` — family traversal logic; substrate interface in coord lookups only
- `V14ComparisonObserver` — reads completed family records; no grid imports anticipated

### 2.3 The new cognitive-layer contribution: approach-phase provenance

The two-event structure of the v1.7 encounter — first perception at distance, distinct from first contact — is a new substrate capability with no tabular-grid equivalent. The grid had only contact events; V17World has approach events.

This creates a pre-registration decision point. Two options:

**Option A (substrate portability only).** v1.7 tests whether the existing cognitive layer carries forward to the new substrate without modification. The approach event is recorded at the substrate interface but not surfaced as a new cognitive-layer capability. The reporting layer produces the same three query types as v1.6. The new capability is reserved for v1.8.

**Option B (approach event as v1.7's cognitive-layer contribution).** v1.7 adds a seventh observer — or extends the prediction-error observer — to record first-perception events separately from first-contact events. The reporting layer gains a fourth query type: *When did I first perceive this object, and how long before I was ready to contact it?* This is the approach window — the developmental distance between recognition and readiness — and extends the resolution window concept from contact to perception.

**Pre-registered choice: Option A for the substrate portability test; Option B reserved as the first available amendment.**

The methodological reason: Option B introduces two architectural changes simultaneously — new substrate and new cognitive capability. The single-variable-change discipline requires that the substrate transposition be completed and verified before the new capability is added. If the transposition is clean (Level 9 passes, Category α holds), Option B is activated via the first amendment. If the transposition requires rebuilding at the substrate interface, Option B is deferred to v1.8 after the interface work is complete.

### 2.4 The Level 9 pre-flight

v1.7 adds Level 9 to the pre-flight pipeline:

**Level 9 (SubstrateBundle portability).** With V17World's observers instantiated and a new-substrate SubstrateBundle constructed from them, `V16ReportingLayer` must produce reports that pass Category α (zero hallucinations) on 10 runs before the full v1.7 batch. This is the substrate-agnosticism commitment operationalised at minimum scale.

Exit 0: Category α holds on all 10 runs. The reporting layer carried forward. Proceed to full batch.
Exit 1: Category α fails on at least one run. A hallucination was produced — a statement whose source_key does not resolve in the new-substrate bundle. Diagnose the specific source_type of the failing statement. The failure identifies exactly where a grid-specific assumption survived into the reporting layer or the bundle construction. Correct and re-run Level 9 before proceeding.

Level 9 is the primary operationalisation of SICC Commitment 10 (substrate-agnosticism) at the reporting layer.

---

## 3. Experimental design

**Run selection.** The v1.7 batch uses seeds drawn from `run_data_v1_5.csv` at `num_steps = 320000`, matching the v1.6 seed chain. New agent simulations are run in V17World, producing new observer output files. The six-observer stack (provenance, schema, family, comparison, prediction-error) runs in parallel during each simulation, as in prior iterations.

**Batch scale.** 60 complete runs at 320,000 steps (four hazard cost conditions × 15 runs per condition, as in v1.5–v1.6), subject to confirmation that run-length requirements for family traversal completion hold in V17World. If the continuous-space dynamics require a different run length for comparable traversal completion rates, a pre-registered amendment will specify the adjustment before any batch runs are made.

**Output files.** The v1.7 batch produces the standard six observer output CSVs (`run_data_v1_7.csv`, `provenance_v1_7.csv`, `schema_v1_7.csv`, `family_v1_7.csv`, `comparison_v1_7.csv`, `prediction_error_v1_7.csv`) plus the reporting layer outputs (`report_v1_7.csv`, `report_summary_v1_7.csv`).

**Baseline comparison.** The v1.7 report summary is compared against v1.6 on: total statements per run, statements per query type, hallucination count, q1_formation_depth distribution, q3_surprise_cells distribution. The comparison is qualitative and exploratory — the substrate change is expected to produce some differences in these distributions. The pre-registered criterion is not that the distributions match, but that the structural properties (auditable, traceable, individually variable) hold.

---

## 4. Pre-flight verifications

Levels 1–8 are inherited from the prior architecture and applied to V17World:

- **Level 1:** V17World without any observers runs and produces plausible trajectories.
- **Level 2:** With all new-substrate observers disabled, the agent's behaviour in V17World is baseline-stable (no observer side-effects).
- **Level 3:** The provenance observer runs correctly on V17World — formation events recorded, cross-references resolved.
- **Level 4:** Family observer runs correctly — traversal sequences recorded for both families in V17World.
- **Level 5:** Comparison observer runs correctly — structural measures computed from new-substrate family records.
- **Level 6:** Prediction-error observer runs correctly — encounter events detected and recorded under the new approach-event definition.
- **Level 7:** SubstrateBundle reconstructed from v1.7 observer outputs matches observer `get_substrate()` outputs on all summary fields for 10 runs.
- **Level 8:** Single-run hallucination check — all ReportStatements from `V16ReportingLayer` instantiated with a v1.7 SubstrateBundle have `source_resolves = True`. Exit 1 triggers diagnosis before proceeding.

**Level 9 (new):** 10-run Category α pre-flight as specified in Section 2.4.

Levels 1–6 are run in order before Level 7. Level 7 before Level 8. Level 8 before Level 9. Level 9 before full batch.

---

## 5. Metrics

Metrics are inherited from v1.6 with one addition.

**Inherited metrics (unchanged):**
- Per-statement: `run_idx`, `seed`, `hazard_cost`, `num_steps`, `query_type`, `statement_text`, `source_type`, `source_key`, `source_resolves`
- Per-run summary: `total_statements`, `statements_q1`, `statements_q2`, `statements_q3`, `hallucination_count`, `q1_formation_depth`, `q3_surprise_cells`, `q3_resolution_stated`, `report_complete`
- Biographical individuation: pairwise normalised edit distance over Q1 `(source_key, statement_text)` sequences

**New metric:**
- `substrate_type` — field added to all output CSVs. Value `"v1_7_continuous_3d"`. Enables clean comparison with v1.6 (`"v1_6_tabular_grid"`) without ambiguity in the combined record.

---

## 6. Pre-registered interpretation categories

Six categories are inherited; one is added.

### 6.1 Category α: Internal consistency of all v1.7 reports

Every `ReportStatement` produced across all v1.7 runs must have `source_resolves = True`. Category α succeeds if `hallucination_count = 0` across all runs. Failure in any run identifies the specific source_type of the unresolvable statement — the precise location of a substrate-interface assumption that survived into the reporting layer.

### 6.2 Category β: Query coverage

Each of the three query types produces a non-empty, well-formed response for each run. `report_complete = True` in all runs. The substrate is sufficient to answer all three query types without gaps.

Category β succeeds if `report_complete = True` in all runs at full batch scale.

### 6.3 Category γ: Biographical individuation at the report level

Pairwise normalised edit distances over Q1 statement sequences must show a non-degenerate distribution with minimum above 0.05. This is the same floor as v1.6 and v1.1. Category γ succeeds if the minimum pairwise biographical individuation distance across all run pairs exceeds 0.05.

A secondary exploratory finding is whether the individuation distances in v1.7 are higher or lower than v1.6 — reflecting whether the richer substrate produces more or less differentiated developmental arcs at the report level.

### 6.4 Category δ: Pre-anticipated structural findings

Two findings are pre-anticipated.

**The approach event increases prediction-error resolution windows.** In V17World, the agent can perceive a costly object before it can contact it. If the agent first perceives a family-costly object before its precondition is met, the prediction-error observer records an encounter at first perception rather than first contact. This extends the resolution window — the developmental distance between awareness and readiness — beyond the v1.5 values. The pre-registered expectation: mean resolution window in v1.7 is equal to or greater than the v1.5 mean, reflecting the addition of the approach phase to the developmental arc.

**Substrate-interface rebuilding will be required in at least one component.** The carry-forward identifies four candidate surfaces: `family_precondition_attractor` keying, the `mastery:(x,y)` flag ID format, the prediction-error encounter event definition, and the `get_substrate()` implementations. The pre-registration commits that at least one of these will require modification. A v1.7 run that required no rebuilding at all would be a finding in the other direction — and would be reported as such, with the Category δ criterion noted as falsified.

### 6.5 Category Φ: Honesty constraint on the substrate-agnosticism claim

The substrate-agnosticism claim is bounded. The claim is: the cognitive layer's concepts — provenance, schema, family traversal, comparison, prediction-error, reporting — are definable independently of the tabular grid, and the implementations across v1.1–v1.6 were genuinely at the cognitive layer rather than smuggling grid-specific assumptions.

The honest operationalisation: wherever v1.7 implementation requires modifying a component that was described as cognitive-layer, that modification is reported as a finding that the component had a substrate-interface dependency that was not visible from the grid. This is not a failure of the programme; it is the diagnostic the transposition is designed to produce. Category Φ fails only if such a finding is concealed or reported in a way that misrepresents its significance.

The deeper claim this iteration makes available: if `V16ReportingLayer` carries forward to V17World without modification, and the reports it produces from V17World are auditable, traceable, and individually variable in the same structural sense as the v1.6 reports, then the biographical self-account — the agent's statement about where it was surprised and how long it waited — is not a property of a grid. It is a property of an agent that has encountered objects, formed relationships with them, and built a developmental history. The substrate changed. The autobiography did not.

### 6.6 Category Ω: The architectural-statement claim

Category Ω succeeds if Categories α, β, and γ all pass.

The claim: the cognitive layer built across v1.1–v1.6 is substrate-agnostic at the level of the reporting layer. The `SubstrateBundle` interface, built in v1.6 for this moment, correctly abstracted the cognitive-layer concepts away from the tabular grid. At v1.7, the reporting layer carries forward and produces reports with the same structural properties on a richer substrate.

The architectural implication: SICC Commitment 10 (substrate-agnosticism) is operative at the reporting layer. The cognitive-layer arc is confirmed as portable. The path to Cozmo (v1.8) is clear at the cognitive layer.

---

## 7. Connection to the SICC trajectory

v1.7 advances the SICC trajectory on one commitment and positions two further commitments.

**Commitment 10 (substrate-agnosticism)** is tested. The test is operationalised via Level 9 and Category Ω. The result — whether the cognitive layer carries forward cleanly or requires substrate-interface rebuilding — is the v1.7 finding regardless of direction.

**Commitment 8 (self-knowledge as derivative of object-knowledge)** is advanced by the richer substrate. In V17World, object encounters have spatial extent, approach phases, and persistence after transformation. The self-account produced by the reporting layer is therefore grounded in a richer object-engagement record — one in which the agent's relationship with an object includes the approach, not only the contact. If the reporting layer produces the same structural account (traceable, individually variable, auditable) from this richer substrate, the grounding of self-knowledge in object-knowledge is confirmed at a new scale.

**Commitments 2 and 12 (embodiment as constraint; battery and finitude)** remain reserved for v1.8. They require the cognitive layer to be already working on a richer substrate before they can be tested meaningfully. v1.7 is the prerequisite.

The v1.7 iteration also positions the approach-phase provenance capability (Section 2.3, Option B) as the first available amendment — ready to activate as the v1.7 cognitive-layer contribution once the substrate transposition is confirmed clean.

---

## 8. Methodological commitments

**Pre-registration before code.** This document is committed to the public repository before any v1.7 implementation work begins.

**Single-architectural-change discipline.** The singular new variable at v1.7 is the substrate. The cognitive layer is not the variable. Where components must be modified to connect to the new substrate, those modifications are classified as substrate-interface work and reported as such. If a modification turns out to require changes to a component's cognitive-layer logic, that finding is reported as a Category Φ finding — an invisible substrate-interface dependency surfaced by the transposition.

**Level 9 before batch.** The full v1.7 batch does not run until Level 9 passes. A Level 9 failure triggers diagnosis and correction before any batch runs are made.

**Parallel-observer preservation.** With all new-substrate observers enabled, the six observer output files must be internally consistent at matched seeds — the same run at the same seed produces the same records. The continuous-space dynamics introduce floating-point determinism requirements; seed-reproducibility is verified at Level 1 before any observer is added.

**Option B activation policy.** The approach-phase provenance capability (Section 2.3, Option B) is activated via the first available amendment if and only if Level 9 passes on the base configuration (Option A). It is not activated if the substrate transposition itself requires an amendment. The amendment budget is not spent twice on the same iteration boundary.

**Amendment policy.** Three amendments available. The first is provisionally reserved for Option B activation (approach-phase provenance), subject to the condition above. The second is reserved for run-length adjustment if V17World requires a different step count for comparable family traversal completion rates. The third is available for unanticipated operational issues.

**Public record.** This pre-registration is committed to the public repository at github.com/RancidShack/developmental-agent on 3 May 2026, before any v1.7 code is written.

---

## 9. Stopping rule

The v1.7 iteration completes when:

- Levels 1–9 all pass.
- All runs at full batch scale have been processed.
- Categories α, β, γ, δ, Φ, and Ω have been characterised in the v1.7 paper.
- The v1.7 paper is drafted.
- The carry-forward note for v1.8 is written.

The iteration is reset if the amendment budget of three is exhausted before completion, or if a Category α failure requires architectural change to resolve and no amendments remain.

---

## 10. References

Baker, N.P.M. (2026a–v) Prior preprints and pre-registrations in the developmental-agent programme: v0.8 through v1.2. Full reference list inherited from v1.3 paper.

Baker, N.P.M. (2026w–z) v1.3 pre-registration, amendments, and paper. See v1.6 reference list.

Baker, N.P.M. (2026aa–ab) v1.4 pre-registration and paper. See v1.6 reference list.

Baker, N.P.M. (2026ac–ad) v1.5 pre-registration and paper. See v1.6 reference list.

Baker, N.P.M. (2026ae) 'v1.6 Pre-Registration: Reporting Layer via SubstrateBundle Interface on Existing Architecture', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026af) 'Biographical Self-Account in a Small Artificial Learner: The Reporting Layer as Substrate-Agnostic Reading Component', preprint, 2 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

---

**Pre-registration commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 3 May 2026, before any v1.7 code is written.
