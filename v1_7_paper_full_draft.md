# Substrate Transposition in a Small Artificial Learner: The Cognitive Layer Meets a Richer World

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 3 May 2026 (v1.7.1 amendment applied same day)
**Status:** Preprint — not peer reviewed
**Repository:** github.com/RancidShack/developmental-agent
**Pre-registration:** Baker (2026ag), committed before any v1.7 code was written
**Amendment:** v1.7.1 — three substrate-interface fixes applied before paper finalisation; results rerun and verified

---

## Abstract

The v1.7 iteration transposes the developmental-agent programme's cognitive layer — provenance, schema, family traversal, cross-family comparison, prediction-error records, and reporting — from a 20×20 tabular grid to a 3D continuous-space environment (V17World), replacing discrete grid coordinates with real-valued positions, four cardinal actions with twenty-six directional vectors, and cell-entry events with proximity-based contact. The transposition is motivated by object-relations theory: the tabular grid was sufficient to record object encounters; V17World is designed to give those encounters spatial form, with an approach phase distinct from contact, objects that persist at their coordinates after transformation, and a spatial autobiography that the biographical register can describe. The primary pre-registered test is substrate-agnosticism at the reporting layer: whether `V16ReportingLayer`, instantiated with a `SubstrateBundle` populated from V17World observers, produces reports with the same structural properties as the v1.6 reports. It does. Across 40 complete runs at 320,000 steps, the reporting layer produced 922 statements with zero hallucinations (Category α: PASS), all 40 runs complete across all three query types (Category β: PASS), and pairwise biographical individuation distances ranging from 0.366 to 0.781 with a mean of 0.625, well above the pre-registered floor (Category γ: PASS). A single amendment cycle (v1.7.1) corrected three substrate-interface defects identified before paper finalisation: a positional comparison in the provenance store that failed under float coordinates, a missing object type in the schema observer's expected-type set, and an unconnected provenance CSV write path. Post-amendment, the provenance substrate carries 378 records across 40 runs, with 214 records carrying non-zero confirming-observation counts. The substrate-interface work required across the full transposition — migrating the family observer and prediction-error observer from grid-coordinate keys to object-identity keys, and correcting the three amendment items — confirms that those components carried substrate-interface assumptions invisible from the grid. The reporting layer itself required zero modification. SICC Commitment 10 (substrate-agnosticism) is operative at the reporting layer. The path to physical embodiment (v1.8, Cozmo) is clear at the cognitive layer.

---

## 1. Introduction

### 1.1 The cognitive-layer arc

Six iterations built a cognitive layer over a 20×20 tabular grid. v1.1 introduced provenance — formation step, confirmation counts, cross-references between threat flags and derived knowledge cells. v1.2 made the schema explicit: cell types as kinds, actions as available verbs, developmental phases as periods. v1.3 introduced relational property families — GREEN and YELLOW, each running through a perceivable distal tier, an acquirable 2D-form attractor, and a bankable 3D-form hazard — with family-specific competency gating at zero violations across 240 runs. v1.4 introduced cross-family structural comparison, confirming the form-progression parallelism assertion and surfacing traversal-sequence distance as an individual developmental tempo. v1.5 elevated prediction-error to a first-class record: the resolution window — developmental steps between first awareness of a hazard and eventual readiness — as the primary quantitative finding. v1.6 built the reporting layer: a `SubstrateBundle` interface designed for this moment, and `V16ReportingLayer` producing auditable self-accounts in response to three structured queries.

v1.6 closed with a commitment and a design obligation. The commitment: the cognitive-layer arc is complete. The obligation: the reporting layer must carry forward when the substrate changes. v1.7 tests that commitment.

### 1.2 Why the substrate needed to change

The tabular grid served the cognitive-layer build well. It provided a controlled, reproducible environment where every architectural decision could be tested in isolation. But the grid imposed a particular quality on object encounters: contact was a cell-entry event, discrete and instantaneous. There was no approach phase, no spatial persistence after transformation, no sense in which the agent could be said to have a spatial relationship with an object before touching it.

Object-relations theory — the framework that has informed the programme's developmental framing — holds that the self emerges through a richer process. The object is first perceived at a distance. The approach is itself a developmental event: the child reaches before grasping, attends before contacting, anticipates before the encounter. After contact, the object is internalised — it becomes a known entity, persistent in the self's representational furniture even after the relationship has transformed it. Winnicott's transitional object is not primarily the object; it is the relationship with the object over time. The grid could record that sequence in a CSV. V17World gives it spatial form.

The pre-registration (Baker, 2026ag) stated this directly: the v1.7 substrate is designed so that object contact has the quality of an encounter rather than a cell-entry event. V17World provides a bounded perception sphere within which objects are perceivable before contact, real-valued coordinates that the agent navigates continuously, and objects that persist at their positions after transformation. The spatial autobiography — where the agent went, in what order, with what encounters — is the substrate of the biographical register.

### 1.3 The primary test

The primary pre-registered test is simple to state: does `V16ReportingLayer`, instantiated with a `SubstrateBundle` populated from V17World observers, produce reports that pass Category α (zero hallucinations)?

The test is not trivial to satisfy. The reporting layer reads from the bundle using `flag_id` keys, `source_key` lookups, and `bundle.resolve()` checks. If any flag_id embedded a grid coordinate in a way the reporting layer read directly, the transposition would fail. The pre-registration identified four candidate surfaces where grid-specific assumptions might have survived invisibly: the family observer's coordinate lookups, the prediction-error observer's `UNAFFILIATED_HAZARD_CELLS` frozenset, the `mastery:(4,15)` flag_id format, and the `get_substrate()` implementations.

All four required substrate-interface work. The reporting layer required none.

### 1.4 Connection to the SICC trajectory

v1.7 tests SICC Commitment 10 (substrate-agnosticism). The test is operationalised via Level 9 pre-flight and Category Ω. Commitment 8 (self-knowledge as derivative of object-knowledge) is advanced: in V17World, object encounters have spatial extent and approach phases, so the self-account produced by the reporting layer is grounded in a richer engagement record. Commitments 2 and 12 (embodiment as constraint; battery and finitude) remain reserved for v1.8, which requires the cognitive layer to already be working on a richer substrate. v1.7 is that prerequisite, now met.

---

## 2. Methods

### 2.1 The new substrate: V17World

V17World is a bounded 3D continuous-space environment occupying a 12×12×12 unit cubic volume. The agent has a real-valued (x, y, z) position and navigates by selecting from twenty-six directional unit vectors plus a stay action (27 actions total), each move advancing the agent by one unit in the chosen direction. The world is fully deterministic given a seed.

**Object types.** Thirteen fixed objects replace the grid's cell vocabulary. The type mapping is explicit at the substrate interface and invisible to the cognitive layer:

| Grid type | V17World object type | Role |
|---|---|---|
| COLOUR_CELL | Distal object (DIST_OBJ) | Perceivable at distance; approach registers family encounter |
| ATTRACTOR | Acquirable object | Mastery event on contact |
| HAZARD | Costly object | Cost on contact; transforms on precondition |
| KNOWLEDGE | Known object | Post-transformation; persists at coordinates |
| END_STATE | Threshold object | Activates on full developmental completion |

**Perception and contact.** Objects within a perception radius of 3.0 units are perceivable; their properties (colour, form, family membership) become available as the agent approaches. Contact fires when the agent's position is within 0.8 units of an object's coordinates. This two-event structure — perception before contact — is the approach phase: the agent can perceive a family's distal object from a distance before entering contact range with any tier member.

**Object persistence.** When a costly object is banked as knowledge, its coordinates are unchanged. The object_id and position are retained; only the type changes from HAZARD to KNOWLEDGE. The agent can return to the location. The spatial internalisation event is a change of state, not a disappearance.

**Family structure.** The GREEN and YELLOW families are preserved from v1.3, with coordinates mapped to 3D space. The family-specific competency gating rule (v1.3.2) carries forward: `haz_green` cannot transform until `att_green` is mastered; equivalently for YELLOW. The cognitive-layer gating logic is unchanged; only the key type migrates from `(row, col)` tuples to object_id strings.

**Phase 1 exploration.** The grid's boustrophedon path is replaced by a 3D waypoint sequence at 2.5-unit spacing, covering the full volume before Phase 2 begins. All 40 runs completed Phase 1 at step 515 — the waypoint count is deterministic given the world geometry.

### 2.2 The substrate-interface migration

The pre-registration identified the substrate-interface work as diagnostic: components that required modification had carried grid-specific assumptions not visible from their cognitive-layer descriptions.

**V13FamilyObserver.** Five coordinate-keyed dependencies required migration: `_coord_to_colour` (maps object position to colour family), `COLOUR_CELL_COORDS` / `FAMILY_ATTRACTOR_COORDS` / `FAMILY_HAZARD_COORDS` (hardcoded grid coordinates), `perceive_adjacent_with_coords()` (grid-specific perception call), and `family_attractor_mastery_step` (which constructed flag_id as `mastery:(4, 15)`). All five are substrate-interface: the traversal logic — what constitutes a traversal event, the narrative format, the cross-reference structure — required no change. `v1_7_observer_substrates.py` patches the family observer's `__init__`, `on_pre_action`, `on_post_event`, `summary_metrics`, and `full_record` to use object_id keys throughout.

**V15PredictionErrorObserver.** The `UNAFFILIATED_HAZARD_CELLS` frozenset (grid coordinate tuples) was replaced by `UNAFFILIATED_HAZARD_IDS` (object_id strings). The observer's `_tracked_cells`, `_prev_cell_type`, and `_cell_family` dicts are keyed by object_id in V17World. The encounter detection logic — comparing `agent.pre_transition_hazard_entries[cell]` counts — required no change; the agent's dict simply uses string keys rather than tuple keys.

**Flag_id format.** The `mastery:(4, 15)` format was migrated to `mastery:att_green`. This is the most consequential substrate-interface change: the flag_id is the key by which the reporting layer's Q1 and Q3 responses source their statements. The migration is complete at the substrate interface; the reporting layer reads whatever string flag_id the provenance store provides.

**V16ReportingLayer.** Zero modifications. The reporting layer imports no observer class and references no grid coordinate. The SubstrateBundle carries cognitive-layer concepts — provenance records keyed by flag_id, family traversal fields by name, prediction-error encounters by list index — and the reporting layer reads these unchanged. This is the substrate-agnosticism commitment confirmed.

### 2.3 Experimental design

**Population.** 40 complete runs at 320,000 steps across four hazard cost conditions (0.1, 1.0, 2.0, 10.0), 10 runs per condition. Seeds drawn from `run_data_v1_5.csv` to preserve the seed chain (the v1.5 batch supplied 10 seeds per condition rather than 15; the population is 40 rather than 60 runs, noted in the pre-registration's amendment provision).

**Observer stack.** All five observers run in parallel during each simulation: `V1ProvenanceStore`, `V13SchemaObserver`, `V13FamilyObserver`, `V14ComparisonObserver`, `V15PredictionErrorObserver`. At run end, `build_bundle_from_observers()` constructs a `SubstrateBundle` from live observer states, and `V16ReportingLayer` generates the report.

**Pre-flight.** Levels 1–8 verified in the development environment before batch execution. Level 9 (10-run Category α pre-flight) passed with zero hallucinations before the full batch commenced.

### 2.4 Amendment 1 (v1.7.1): Three substrate-interface corrections

Before paper finalisation, a first error-check run identified three substrate-interface defects. All three are recorded here per Category Φ: substrate-interface findings, not cognitive-layer failures.

**Defect 1: Provenance store positional comparison.** `V1ProvenanceStore.on_post_event()` fires confirming-observation increments when `self.world.agent_pos == cell` — correct for the grid, where both are `(row, col)` integer tuples. In V17World, `agent_pos` is a `(x, y, z)` float tuple and `cell` is an object_id string; the comparison is always False, producing confirming_observations = 0 for every record. The fix replaces the positional comparison with `world._contact_at_pos(world.agent_pos)`, the contact-radius check already used by V17World's step function.

**Defect 2: Schema observer expected-type set.** `V13SchemaObserver.EXPECTED_CELL_TYPES` was inherited from v1.3 as `{FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE, COLOUR_CELL}`. V17World uses `DIST_OBJ` (same integer constant = 6) in place of `COLOUR_CELL`. The mismatch caused `schema_complete = False` in all v1.7.0 runs. The fix patches `on_run_end` for V17World instances to substitute `DIST_OBJ` for `COLOUR_CELL` in the expected set before the completeness check.

**Defect 3: Provenance CSV write path.** The batch runner opened `provenance_v1_7.csv` but never called `prov_obs.write_provenance_csv()`. The file was created empty. The fix adds a `flush_provenance_csv()` helper called after each run.

All three fixes are in `v1_7_observer_substrates.py` (Amendment 1 block) and the batch runner. The batch was rerun in full after the amendment. All category results are unchanged: the defects affected data completeness and metadata correctness, not statement generation or traceability.

### 2.5 Metrics

All metrics are inherited from v1.6 (Baker, 2026af), with one addition: `substrate_type = "v1_7_continuous_3d"` appended to output CSVs to distinguish v1.7 records from v1.6 records in combined analysis.

---

## 3. Results

### 3.1 Category α: Internal consistency

Across all 40 runs, the reporting layer produced 922 statements. Total hallucinations: 0. Category α: PASS.

Every statement is traceable to a record in the SubstrateBundle. The `bundle.resolve()` check — the architectural operationalisation of "auditable, not oracular" — returns True for every statement in the 40-run batch. The substrate changed. The traceability property did not.

The provenance substrate (corrected at v1.7.1) carries 378 records across 40 runs, distributed across five flag types: mastery (181), knowledge_banking (168), threat (2), end_state_activation (14), and end_state_banking (13). Of these, 214 records carry non-zero confirming-observation counts, with a maximum of 319,152 — an attractor object contacted repeatedly across 320,000 steps. The 163 records with confirming_observations = 0 are architecturally expected: objects mastered or banked on the formation step and never re-contacted within the run window. The Q1 statements reflect this split directly: 213 of 379 statements report positive confirmation counts; 163 report zero.

### 3.2 Category β: Query coverage

All 40 runs produced complete reports across all three query types (`report_complete = True` in every row of `report_summary_v1_7.csv`). Category β: PASS.

Statement distribution across query types: Q1 (what_learned) 379 statements; Q2 (how_related) 350 statements; Q3 (where_surprised) 193 statements. Per-run means: Q1 = 9.5, Q2 = 8.8, Q3 = 4.8. Total per run: mean = 23.1, range 14–27.

### 3.3 Category γ: Biographical individuation

Pairwise normalised edit distances across the 40-run Q1 sequence matrix (n = 780 pairs): minimum = 0.366, mean = 0.625, maximum = 0.781. The pre-registered substantive-differentiation floor of 0.05 is exceeded by a factor of 7.3 at the minimum. Category γ: PASS.

No two agents produced the same biographical sequence. The minimum distance of 0.366 — the most similar pair in the batch — still represents substantial sequence divergence. The maximum of 0.781 represents agents whose developmental trajectories have almost nothing in common at the provenance level.

This individuation is not trivially explained by random seed variation. The mastery sequences confirm genuine developmental divergence: one agent's sequence reads `['att_free_1', 'att_free_3', 'att_free_2', 'att_green']`; another's reads `['att_free_1', 'att_yellow', 'att_free_0', 'att_green', 'att_free_2']`; a third never achieves `att_yellow` mastery within the run window. The biographical register captures this divergence in statement form: agents that mastered different objects in different orders produce genuinely distinct accounts of what they learned.

### 3.4 Category δ: Pre-anticipated structural findings

**Prediction-error events across conditions.** The resolution window — developmental steps between first encounter with a family hazard and eventual transformation — shows the cost-sensitivity pattern anticipated in v1.5. Yellow family encounters produced resolution windows in 36 of 40 runs (mean 7,336 steps, range 29–121,908). Green family encounters produced one resolved window (13,004 steps). The asymmetry between families reflects the spatial layout: `haz_yellow` is positioned closer to the Phase 1 waypoint sequence, making early pre-precondition encounters more frequent. At cost = 2.0, the mean yellow resolution window collapses to 206 steps, the lowest across all conditions — agents at this cost level encounter `haz_yellow` early and resolve the precondition quickly. At cost = 10.0, the mean rises to 18,422 steps, with some agents carrying unresolved windows for over 100,000 steps before the transformation fires.

Four runs produced no resolution window for either family: these agents encountered every hazard object after their precondition was already met. The transformation followed without surprise in every case. Their Q3 statements read accordingly:

> *I entered haz_green (GREEN family) at step 633 with the precondition already met. No prediction error was recorded: the transformation followed without surprise.*

This is the v1.7 continuation of v1.6's sharpest finding: agents that arrived everywhere ready produce structurally distinct accounts from agents that paid to look before they were ready. The distinction survives the substrate change.

**Substrate-interface rebuilding was required.** As pre-registered, at least one component required modification. In fact all four candidate surfaces identified in the pre-registration required substrate-interface work. This confirms that the cognitive layer had absorbed grid-specific assumptions in each of those components — not at the level of cognitive logic, but at the level of identity keys and perception calls. The reporting layer was the one component that required none, confirming the SubstrateBundle design.

### 3.5 Category Φ: Honesty constraint

The substrate-interface findings are reported without minimisation. The family observer and prediction-error observer both carried coordinate-keyed dependencies that were invisible from the grid. These are named as substrate-interface findings, not as failures: the cognitive logic of both observers is unchanged. The mastery flag check, the traversal event structure, the resolution window computation — none of these changed. The keys changed. That is the honest description.

The reporting layer's zero-modification result is also reported without inflation. It confirms that the SubstrateBundle design achieved its goal: cognitive-layer contracts rather than grid-specific identities at the bundle interface. It does not confirm that the entire cognitive layer is substrate-agnostic; it confirms that the reporting layer is. The four components that required substrate-interface work remain as evidence that substrate-agnosticism is a property that must be achieved component by component, not assumed from architectural intent.

### 3.6 Category Ω: The architectural-statement claim

Categories α, β, and γ all pass. Category Ω: PASS.

The claim: the cognitive layer built across v1.1–v1.6 is substrate-agnostic at the level of the reporting layer. The `SubstrateBundle` interface, built in v1.6 for this moment, correctly abstracted the cognitive-layer concepts away from the tabular grid. At v1.7, the reporting layer carries forward and produces reports with the same structural properties — auditable, traceable, individually variable — on a richer substrate.

The architectural implication: SICC Commitment 10 is operative at the reporting layer. The path to Cozmo is clear at the cognitive layer.

---

## 4. Discussion

### 4.1 What the transposition found

The v1.7 transposition found exactly what the pre-registration said it would find, and one thing it did not anticipate in full.

What it found: four substrate-interface components with grid-specific assumptions — the family observer's coordinate lookups, the prediction-error observer's hazard cell frozenset, the flag_id format, and the `get_substrate()` implementations for both. Each was substrate-interface work in the precise sense: the cognitive logic was unchanged; only the identity mechanism changed. The reporting layer, by contrast, required nothing. This distribution — four substrate-interface patches and zero cognitive-layer changes — is the cleanest possible outcome for the pre-registered test.

What it found additionally: the family observer's `_attractor_mastery_step` method had been reading flag_ids in the format `mastery:(4, 15)` since v1.3, and this format had never needed to change because nothing downstream of it had changed the substrate. The transposition made the assumption visible. This is the methodological value of substrate transposition as a research method: it surfaces assumptions that are correct but invisible, confirming the cognitive-layer claim by forcing the substrate-interface claim to become explicit.

The amendment cycle surfaced three further substrate-interface defects of a different kind — not logical errors in the cognitive layer, but wiring failures at the boundary between the cognitive layer and the execution environment. The provenance store's positional comparison, the schema observer's expected-type set, and the batch runner's CSV write path all relied on properties of the grid (integer coordinates, a fixed cell-type vocabulary, a read-from-CSV execution model) that had become implicit infrastructure. None affected statement generation or traceability. All three were correctly classified as substrate-interface work and corrected within the amendment budget.

### 4.2 The spatial autobiography

V17World's biographical register has a different texture from v1.6's. The Q1 statements name objects by identity (`att_green`, `haz_yellow`) rather than grid coordinates. The Q2 statements describe family traversal through a 3D space where the agent approached objects before contacting them, navigated toward waypoints, and built a spatial history. The Q3 statements describe encounters with costly objects whose coordinates are persistent — the agent that encountered `haz_yellow` at step 493 can, in principle, return to its position after banking it.

The statements themselves have not changed in structure. The reporting layer produces the same three query types, the same source-keying, the same traceability checks. What has changed is the substrate from which the statements are drawn — richer, spatially articulated, closer to the developmental environment that object-relations theory requires. The autobiography reads the same way. It describes a different world.

### 4.3 The resolution window at scale

The resolution window distribution across conditions warrants attention. At cost = 0.1, the mean yellow resolution window is 6,098 steps — the agent encounters `haz_yellow` early, pays a small cost, and waits a long time before the precondition is met. At cost = 2.0, the mean collapses to 206 steps — the agent encounters the hazard later (the high cost makes early approach less likely under the threat layer's gating), but the precondition is often already met by the time of first encounter. At cost = 10.0, the window expands to 18,422 steps — the agent is cautious about high-cost objects, delays encounter, and when it does encounter, the precondition resolution takes longer.

This non-monotonic pattern — low cost gives long windows, medium cost gives short windows, high cost gives very long windows — is not an artefact of the 3D environment. It reflects the threat layer's cost-sensitivity: the hazard gate responds to cost level, which shapes when first encounter occurs, which determines window length. The pattern was present in v1.5's tabular data; V17World reproduces it with a different substrate, confirming that the effect is cognitive-layer rather than grid-specific.

### 4.4 Fourteen runs without end-state activation

Only 14 of 40 runs activated the end-state object (full traversal of all families and banking of all hazards). The 26 runs that did not reach activation completed the run window without finishing the developmental sequence. This completion rate (35%) is lower than the v1.5 batch's rate on the tabular grid, reflecting the additional navigational complexity of 3D continuous space: the agent must cover more ground, with a larger action space, to locate and contact all objects. The distribution is not uniform across cost conditions: cost = 2.0 achieved activation in 5 of 10 runs; cost = 10.0 in 4 of 10; cost = 0.1 and cost = 1.0 in 2–3 of 10 each.

This is an expected consequence of the richer substrate — the pre-registration noted that run-length requirements might need adjustment for comparable traversal completion rates, and reserved an amendment for this purpose. The 40-run batch at 320,000 steps demonstrates that the cognitive layer functions correctly under incomplete traversal: the biographical register reports what was learned, not what could have been learned. Agents that did not reach activation produce complete, individually variable reports describing the developmental arc they did complete.

### 4.5 v1.8: what is now possible

The v1.7 result positions v1.8 to test two SICC commitments that could not be tested while the cognitive layer was on the tabular grid.

**Commitment 2 (embodiment as constraint).** A physical robot — the Cozmo, with a Raspberry Pi 5 handling perception and cognitive layer — introduces constraints the simulation does not: battery depletion, motor imprecision, lighting variation, occlusion. The cognitive layer now running on V17World carries forward to this substrate, with V17World's object_id-keyed substrate interface as the template for the physical perception layer.

**Commitment 12 (battery and finitude).** The agent's run in V17World has a fixed step budget; in Cozmo deployment it has a battery budget. The resolution window — already measuring developmental distance against a clock — becomes developmental distance against a finite resource. The biographical register will describe not only where the agent was surprised but whether it had time to resolve the surprise before the run ended.

The cognitive layer is ready. The path is clear.

---

## 5. Conclusion

v1.7 transposes the developmental-agent programme's cognitive layer from a 20×20 tabular grid to a 3D continuous-space environment. The reporting layer carries forward without modification. Zero hallucinations across 922 statements in 40 runs. Every developmental arc individually distinct. The substrate-interface findings — four primary components with grid-specific assumptions surfaced by the transposition, plus three further wiring defects corrected in the amendment cycle — confirm that the cognitive-layer claim was genuine where it held and visible where it needed work.

The key sentence from v1.6, still true: *Five agents answer: it was never relevant — the transformation followed without surprise. Thirty-five answer: here are the objects where I arrived before I was ready, and here is how long I waited.*

The substrate changed. The autobiography did not.

---

## References

Baker, N.P.M. (2026r) 'v1.1 Pre-Registration: Provenance over Learned States', GitHub repository, April 2026.

Baker, N.P.M. (2026s) 'v1.2 Pre-Registration: Explicit Schema Observation', GitHub repository, April 2026.

Baker, N.P.M. (2026z) 'v1.3 Pre-Registration and Paper: Relational Property Families', GitHub repository, April 2026.

Baker, N.P.M. (2026ab) 'v1.4 Pre-Registration and Paper: Cross-Family Structural Comparison', GitHub repository, April 2026.

Baker, N.P.M. (2026ad) 'v1.5 Pre-Registration and Paper: Prediction-Error Elevation', GitHub repository, April 2026.

Baker, N.P.M. (2026ae) 'v1.6 Pre-Registration: Reporting Layer via SubstrateBundle Interface', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026af) 'Biographical Self-Account in a Small Artificial Learner: The Reporting Layer as Substrate-Agnostic Reading Component', preprint, 2 May 2026.

Baker, N.P.M. (2026ag) 'v1.7 Pre-Registration: Substrate Transposition to a Richer Simulated Environment', GitHub repository, 3 May 2026.

Baker, N.P.M. (internal record, v0.3 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.
