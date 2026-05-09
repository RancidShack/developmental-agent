# v1.16.1 Pre-Registration: Zero-Colour Extrusion Pair and the Relational Grammar Beyond Colour

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 9 May 2026
**Status:** Pre-registration document — committed before any v1.16.1 code is written
**ARCH:** v1_16_1
**Amendment budget:** Three
**Preceding version:** v1.16 (curiosity_agent_v1_16_batch.py — batch complete, 40/40 arc_complete)

---

## 1. Purpose and developmental context

### 1.1 What v1.16 established and what it left open

The v1.16 iteration asked whether the agent has a self that persists in the absence of direction. The result was unambiguous: 40/40 arc_complete; 40/40 post-completion behaviour categorised as attractor_revisit; 89.4% mean contact density in the post-completion window; haz_blue (the transformation site) present in post_completion_objects in every run; haz_grey (the unresolvable hazard) absent in every run. The agent returns to and sustains engagement with its developmental history when external direction is removed.

The shape connector fired at 40/40, with basis_chains = `haz_green|haz_yellow|shape:haz_green|shape:haz_yellow` universally. This is the programme's first measurement of cross-family dimensional form reasoning — the agent using the 2D↔3D pair relationship across GREEN and YELLOW families to predict att_blue (SQUARE_2D) as the precondition for haz_blue (CUBE_3D). The reasoning is correct and universal.

What neither the shape connector result nor the post-completion data can answer is whether the relational grammar operates *beyond colour*. In every case where the shape connector fired, the dimensional reasoning was anchored to colour-named objects — `shape:haz_green`, `shape:haz_yellow`. The agent used form relationships as secondary basis entries alongside colour-family basis entries. Colour remained the primary scaffold. The question of whether dimensional form reasoning can operate as the *sole* basis — without colour-family anchoring — was not testable because every object in the v1.16 world had a colour family.

Additionally, v1.16's end_state_draw_log showed 17/40 runs with `end_state_draw_active=True` and zero banked. The agent reached the activation threshold for the draw mechanism and found nothing to resolve. The Montessori interpretation: the agent demonstrated readiness for the next stage, and the next stage was not present. v1.16.1 provides it.

### 1.2 The v1.16.1 question

**Can the agent recognise the extrusion relationship between att_zero (RECTANGLE_2D) and haz_zero (RECTANGULAR_PRISM_3D) — writing a predicted schema record with dimensional-form-only basis chains — when no colour-family scaffold is available?**

Extrusion is the generative operation by which a 2D form produces a 3D solid through extension perpendicular to its plane. A rectangle extruded perpendicular to its face produces a rectangular prism. This is the most geometrically exact 2D→3D operation in the programme's form grammar — RECTANGLE_2D→RECTANGULAR_PRISM_3D is pure linear extrusion. The special-case relationship: SQUARE_2D is the equilateral RECTANGLE_2D; CUBE_3D is the equilateral RECTANGULAR_PRISM_3D. The extrusion operation is identical; the input form is a special case.

att_zero and haz_zero have ZERO colour — no colour-family membership. They carry no colour constant, no dist cell, no colour-family attractor partner. The agent cannot use the colour-family basis chains that anchored every prior shape connector firing. The only available basis for recognising the att_zero→haz_zero relationship is the extrusion principle derived from the dimensional form grammar the agent has built across all three colour-family pairs.

### 1.3 The difficulty hierarchy

Four levels of cognitive engagement are operationally distinguishable in this experiment:

**Level 1 — 2D form recognition.** The agent encounters att_zero (RECTANGLE_2D). It recognises a 2D attractor form. This is within established V1 capability. Evidence: att_zero first_contact_step recorded.

**Level 2 — Zero-colour tolerance.** The agent continues to engage with att_zero despite the absence of colour-family signals it has always received from attractors. Evidence: att_zero mastered (att_zero_mastered = True).

**Level 3 — 3D form recognition.** The agent encounters haz_zero (RECTANGULAR_PRISM_3D) following att_zero mastery. Evidence: haz_zero first_contact_step recorded.

**Level 4 — Extrusion as generative principle.** The agent writes a predicted schema record for haz_zero with predicted_precondition=att_zero, using dimensional-form-only basis chains. No colour-family entries appear. The agent has recognised the extrusion relationship from the form grammar alone. Evidence: zero_colour_basis_only = True in the predicted schema record.

Level 4 is the primary pre-registered question. The Fibonacci consolidation note: the depth at which the agent reaches Level 4 in this controlled V1 framework is the programme's first measurable baseline for V2 readiness — the degree to which the extrusion principle is available for consolidation before the play-pen begins.

### 1.4 The Montessori gate

att_zero and haz_zero are latent objects in return ENV1. They exist as NEUTRAL cells (no reward, no cost, no attraction bias) from world construction. At transformation_step — the moment haz_blue transforms to KNOWLEDGE and arc_complete fires — they activate: att_zero transitions to ATTRACTOR type and haz_zero transitions to HAZARD type. The agent then has the remaining post-completion budget (approximately 199,000 steps at mean transformation_step) to encounter them.

This is the prepared environment principle applied architecturally. The next developmental stage becomes available only when the prior stage is complete. The 17/40 draw activations from v1.16 — the agent demonstrating readiness with nothing to resolve — now have a resolution.

### 1.5 The secondary observable: rectangle-square special case

RECTANGLE_2D is formally related to SQUARE_2D — a square is an equilateral rectangle. Whether the agent's basis chains for haz_zero contain any reference to the SQUARE_2D/att_blue pairing — something like `shape:att_blue` appearing alongside `shape:att_zero` — is an emergent observable that is not pre-registered as a directional prediction. If it appears, the relational grammar is operating at the inter-form-family level V2 requires: the agent has recognised that the rectangle-family and the square-family are related through the same extrusion operation. If it does not appear, this specific cross-form-family recognition remains a V2 target.

---

## 2. Architectural specification

### 2.1 New constants

Three new constants are added to `v1_13_world.py`. No existing constant is modified.

**`ZERO = "ZERO"`** — colour constant for zero-colour objects. Distinct from all existing colour constants (GREEN, YELLOW, BLUE, GREY). Represents the absence of colour-family membership, not membership in a new colour family.

**`RECTANGLE_2D = "RECTANGLE_2D"`** — dimensional form constant. The 2D cross-sectional form produced by taking a planar slice of RECTANGULAR_PRISM_3D parallel to its face. Related to SQUARE_2D as a general case (SQUARE_2D is equilateral RECTANGLE_2D). New form; not previously used in any family.

**`RECTANGULAR_PRISM_3D = "RECTANGULAR_PRISM_3D"`** — dimensional form constant. The 3D solid produced by the linear extrusion of RECTANGLE_2D perpendicular to its plane. Related to CUBE_3D as a general case (CUBE_3D is equilateral RECTANGULAR_PRISM_3D). New form; not previously used in any family.

**Commitment 22 compliance for the zero-colour pair:**

| Property | att_zero | haz_zero |
|----------|----------|----------|
| colour | ZERO | ZERO |
| dimensional_form | RECTANGLE_2D | RECTANGULAR_PRISM_3D |
| dimensional_pair_partner | RECTANGULAR_PRISM_3D | RECTANGLE_2D |
| developmental_direction | 2D precedes 3D | 3D follows 2D |
| generative_operation | extrusion (linear) | extrusion (linear) |
| special_case_relation | SQUARE_2D (equilateral) | CUBE_3D (equilateral) |

### 2.2 Zero-colour family definition

A zero-colour family dict is defined in the batch file following the existing family schema. att_zero carries no dist_id (no dist cell; colour-family discovery is not available). The family is added to `RETURN_ENV1_FAMILIES_V161` — the v1.16.1 extension of `RETURN_ENV1_FAMILIES`.

```
V161_ZERO_FAMILY = {
    "colour":   ZERO,
    "dist_id":  None,
    "dist_pos": None,
    "att_id":   "att_zero",
    "att_pos":  (position to be specified),
    "att_form": RECTANGLE_2D,
    "haz_id":   "haz_zero",
    "haz_pos":  (position to be specified),
    "haz_form": RECTANGULAR_PRISM_3D,
}
```

Positions are determined by seeded random sampling at world construction. A helper `_sample_zero_positions(rng, existing_positions, world_size, min_sep=2.5)` draws positions uniformly from the navigable volume [1.5, world_size−1.5]³, rejecting any candidate within `min_sep` of any existing object, until two valid positions are found. The positions therefore vary across seeds, adding a positional dimension to the individuation data: different agents encounter att_zero and haz_zero at different locations, with the timing differences between agents reflecting both positional variation and genuine developmental difference. Positions are recorded in `zero_colour_v1_16_1.csv`.

### 2.3 The latent activation mechanism

V113World is extended with a `latent_objects` parameter — a list of object IDs that are constructed as NEUTRAL cells at world creation and activated (transitioned to their true type: ATTRACTOR or HAZARD) at a designated trigger event.

At world construction: att_zero and haz_zero are placed at their positions as NEUTRAL cells — no feature reward, no attraction bias, no hazard cost. They are perceptually invisible to the agent's reward and cost signals.

At transformation_step (triggered by arc_complete firing in the return ENV1 loop): the batch calls `world.activate_latent_objects()`, which transitions att_zero from NEUTRAL to ATTRACTOR (feature reward and attraction bias enabled) and haz_zero from NEUTRAL to HAZARD (hazard cost enabled, unresolvable=False). From this step onward, both objects are fully present in the world.

The `latent_activation_step` is recorded in the zero_colour output row.

### 2.4 Zero-colour shape connector

The existing shape connector (v1.16) fires when both haz_green and haz_yellow are unlocked in ENV1, producing `shape:haz_green|shape:haz_yellow` as additional basis entries for the haz_blue prediction. It is anchored to colour-named objects.

The zero-colour shape connector is a new firing mode. It fires when att_zero is mastered in return ENV1 (post-activation). On fire:

- Basis entries: `["shape:att_zero"]` — dimensional form only; no colour-family reference
- Predicted precondition: `att_zero`
- Predicted object: `haz_zero`
- Schema state: PREDICTED_STATE (standard prediction pathway)

The secondary observable extension: if the existing schema already holds a confirmed record for haz_blue (predicted_precondition=att_blue, SQUARE_2D), the zero-colour connector checks whether the SQUARE_2D/RECTANGLE_2D special-case relationship should be reflected in the basis. This check is recorded as `square_family_basis_check` (boolean: was the check performed?) and `square_family_basis_added` (boolean: was `shape:att_blue` added to basis_chains?). These are observational fields — they are not pre-registered as directional predictions.

### 2.5 What v1.16.1 does not change

The v1.16 arc mechanism is inherited unchanged. ENV1, ENV2, and the primary return ENV1 arc (att_blue mastery → haz_blue transformation) operate identically to v1.16. arc_complete, arc_timeout, and arc_total_steps are measured on the primary arc only. The zero-colour family is a post-completion addition; it does not affect Category Ω.

The shape connector for haz_blue (v1.16) continues to fire in ENV1 as before. The zero-colour connector is an additional mechanism in return ENV1 only; it does not modify the ENV1 shape connector.

The post_completion_v1_16_1.csv tracking is extended: att_zero and haz_zero contacts are recorded separately in the zero_colour CSV rather than in the general post_completion_objects field, which continues to track the existing attractor family.

---

## 3. Experimental matrix and seeds

**Runs:** 40  
**Seeds:** From `run_data_v1_16.csv` (continuing the seed chain)  
**Hazard cost levels:** 0.1 (×10), 1.0 (×10), 2.0 (×10), 10.0 (×10)  
**Steps:** ENV1 = 1,000,000; ENV2 = 800,000; return ENV1 = 200,000 (unchanged from v1.16)  
**ARCH:** `v1_16_1`

The seed chain continuity preserves matched-seed comparison with v1.16 on all primary arc metrics. The zero-colour findings are new and have no v1.16 comparison baseline by design.

---

## 4. Pre-flight verifications

Nine criteria must pass before the full batch runs. All eight v1.16 criteria are inherited; one new criterion is added.

**16.1.1 (inherited):** Form grammar correct — CIRCLE_2D, CUBE_3D, SQUARE_2D, RECTANGLE_2D, RECTANGULAR_PRISM_3D all present in world file.

**16.1.2 (inherited):** haz_grey in ENV1_FAMILIES_V16 with PYRAMID_3D form and no attractor.

**16.1.3 (inherited):** haz_grey excluded from transfer gate.

**16.1.4 (inherited):** has_end_state=False — ENV1 world carries no end_state cell.

**16.1.5 (inherited):** Shape connector fires for haz_blue (colour-family mode, basis_chains contains shape: entries for haz_green and haz_yellow).

**16.1.6 (inherited):** Return gate: CONFIRMED_STATE only.

**16.1.7 (inherited):** CRITICAL INVARIANT — mastery_flag['att_blue']=1 preserved in return ENV1 carry.

**16.1.8 (inherited):** POST_COMPLETION_FIELDS and UNREACHABLE_FIELDS defined.

**16.1.9 (new — v1.16.1):** Latent activation mechanism correct:
- att_zero and haz_zero are NEUTRAL type at world construction (before activation)
- att_zero and haz_zero are ATTRACTOR and HAZARD type respectively after activation fires
- Activation fires at transformation_step in the return ENV1 loop, not before
- att_zero and haz_zero are NOT in RETURN_ENV1_PRECOMPLETED
- Zero-colour shape connector fires on att_zero mastery and produces basis_chains containing `shape:att_zero` with no colour-family entries

**16.1.10 (new — v1.16.1):** RETURN_ENV1_FAMILIES form grammar correct:
- GREEN family: att_form=CIRCLE_2D (was SQUARE_2D in v1.16 — corrected)
- BLUE family: att_form=SQUARE_2D (was CIRCLE_2D in v1.16 — corrected)
- BLUE family: haz_form=CUBE_3D (was SPHERE_3D in v1.16 — corrected)
- These corrections bring RETURN_ENV1_FAMILIES into alignment with the v1.16 form grammar that ENV1_FAMILIES already carries

All ten criteria must pass. Full batch is blocked on any failure.

---

## 5. Output files

All v1.16 output files are retained with v1_16_1 suffix. One new file is added.

**`zero_colour_v1_16_1.csv`** — one row per run. Individuation is the driving concern: this file captures not just outcomes but the full temporal signature of each agent's engagement with the zero-colour pair. Different agents will find att_zero at different steps, take different numbers of contacts to master it, wait different intervals before approaching haz_zero, and write predictions at different moments. These timing windows are the operational substrate of individuation.

| Field | Type | Description |
|-------|------|-------------|
| arch | str | v1_16_1 |
| run_idx | int | Run index |
| seed | int | Seed |
| hazard_cost | float | Cost level |
| arc_complete | bool | Primary arc status |
| att_zero_pos | str | Sampled position (x,y,z) |
| haz_zero_pos | str | Sampled position (x,y,z) |
| latent_activation_step | int | Step at which att_zero/haz_zero activated (= transformation_step) |
| post_completion_budget | int | Steps remaining after activation |
| att_zero_first_approach_step | int\|None | First step within PERCEPTION_RADIUS of att_zero |
| att_zero_first_contact_step | int\|None | First step within CONTACT_RADIUS of att_zero |
| att_zero_approach_count | int | Total approaches to att_zero (Level 1 engagement depth) |
| att_zero_contact_count | int | Total contacts with att_zero |
| att_zero_mastered | bool | att_zero mastery achieved |
| att_zero_mastery_step | int\|None | Step of mastery (Level 2) |
| window_activation_to_att_first | int\|None | Steps: latent_activation → att_zero first contact (individuation) |
| window_att_first_to_mastery | int\|None | Steps: att_zero first contact → mastery (mastery efficiency) |
| haz_zero_first_approach_step | int\|None | First approach to haz_zero |
| haz_zero_first_contact_step | int\|None | First contact with haz_zero (Level 3) |
| haz_zero_approach_count | int | Total approaches to haz_zero |
| haz_zero_contact_count | int | Total contacts with haz_zero |
| window_mastery_to_haz_first | int\|None | Steps: att_zero mastery → haz_zero first contact |
| haz_zero_predicted | bool | Predicted schema record written (Level 4 candidate) |
| haz_zero_prediction_step | int\|None | Step prediction written |
| haz_zero_basis_chains | str | Pipe-delimited basis entries |
| zero_colour_basis_only | bool | True = basis contains only shape: entries; no colour-family entries (Level 4) |
| window_mastery_to_prediction | int\|None | Steps: att_zero mastery → haz_zero prediction (individuation) |
| square_family_basis_check | bool | Was SQUARE/RECTANGLE special-case check performed? |
| square_family_basis_added | bool | Was shape:att_blue added to basis_chains? (secondary observable) |
| level_reached | int | Highest level reached: 1 (first contact), 2 (mastery), 3 (haz contact), 4 (extrusion prediction) |
| post_completion_att_zero_contacts | int | Total att_zero contacts in post-activation window |
| post_completion_haz_zero_contacts | int | Total haz_zero contacts in post-activation window |
| end_state_draw_active_v116 | bool | Was end_state_draw_active=True for this seed in v1.16? (Category δ correlation) |

---

## 6. Pre-registered interpretation categories

Six categories are pre-registered. Categories Ω and α are inherited from v1.16 with identical criteria. Categories Λ, Φ, δ, and Σ are new or extended.

### 6.1 Category Ω — Arc completion rate (inherited)

Pre-registered prediction: ≥24/40 arc_complete. The zero-colour addition does not affect the primary arc mechanism; the v1.16 rate of 40/40 is the expected baseline but 24/40 is the minimum acceptable threshold. Any reduction from 40/40 is reported with architectural diagnosis.

### 6.2 Category α — Integrity (inherited)

Zero hallucinations across all 40 runs. Zero unresolvable→confirmed transitions for haz_grey. These criteria are identical to v1.16.

### 6.3 Category Λ — Level 4 extrusion recognition (primary pre-registered question)

**Pre-registered prediction: ≥32/40 runs reach Level 4 — zero_colour_basis_only = True in the haz_zero predicted schema record.**

This is the primary question. Rationale for the ≥32/40 threshold: the v1.16 shape connector fired at 40/40, confirming the relational grammar operates reliably when colour-anchored. The ≥32/40 threshold (80%) reflects confidence that the grammar will extend to zero-colour objects in the large majority of runs, while acknowledging that the absence of colour-family scaffolding introduces genuine uncertainty not present in v1.16.

The prediction is directional and pre-registered as a minimum. The result will be reported as a proportion (n/40) with the full distribution of level_reached across all runs.

If fewer than 32/40 runs reach Level 4 but ≥32/40 reach Level 2 (att_zero mastered), the finding is: the agent tolerates zero-colour objects and masters the attractor, but has not yet consolidated the extrusion principle as a generative operation. This is reported as a Level 2 result — meaningful, not a failure, and directly informative for V2 readiness assessment.

If fewer than 32/40 runs reach Level 2, the finding is: the agent does not reliably engage with zero-colour attractors. This is a genuine negative result, reported under Category Φ with architectural diagnosis.

### 6.4 Category Φ — Honesty and deviations

The standard Category Φ applies. All deviations from this pre-registration are reported explicitly in the v1.16.1 paper. Amendment budget: three.

Additionally, Category Φ covers a specific v1.16.1 risk: the latent activation mechanism is new. If the mechanism fails silently — att_zero/haz_zero activating at the wrong step, or not activating at all — this is a deviation that must be caught by the verifier (criterion 16.1.9) and reported if it reaches the batch. The `latent_activation_step` field in zero_colour_v1_16_1.csv is the audit trail.

### 6.5 Category δ — v1.16 draw activation correlation

v1.16 produced 17/40 runs with `end_state_draw_active=True`. These runs reached the mastery threshold that would trigger the draw mechanism in a world with an end_state. The pre-registered observational question: do these 17 seeds show faster Level 4 recognition in v1.16.1 (lower `att_zero_mastery_step` or higher `level_reached`) compared to the 23 seeds where `end_state_draw_active=False`?

This is a seed-matched observational comparison, not a causal prediction. It is pre-registered as directional: the hypothesis is that runs where the agent demonstrated readiness via the draw mechanism in v1.16 will show faster engagement with the zero-colour pair in v1.16.1 at the same seeds. If the correlation is absent, this is reported as a null finding; the draw activation interpretation is revised accordingly.

### 6.6 Category Σ — Rectangle-square special case (secondary observable, non-directional)

Whether `square_family_basis_added = True` appears in any run is recorded and reported without a directional prediction. It is an emergent finding. If present in ≥1 run, the programme's first cross-form-family relational record has been produced: the agent has noted that RECTANGLE_2D and SQUARE_2D are related forms, not merely that RECTANGLE_2D produces RECTANGULAR_PRISM_3D. This is a pure observation; the direction and magnitude are not pre-registered.

---

## 7. SICC observations (not pre-registered findings)

Two architectural observations arising from this design are recorded here for the SICC working note rather than as pre-registered findings.

**Observation 1 — CIRCLE→SPHERE is rotation, not extrusion.** The v1.16 GREEN family pair (CIRCLE_2D→SPHERE_3D) is geometrically a rotational generation, not a linear extrusion. CIRCLE_2D extruded produces CYLINDER_3D. This distinction is noted for V2 object grammar design: in the play-pen, the agent will encounter cylinders (extruded circles) and spheres (rotated circles) as physically distinct objects with different stability and stacking properties. The v1.16.1 RECTANGLE_2D→RECTANGULAR_PRISM_3D pair is the programme's first geometrically exact linear extrusion. The existing colour-family form pairs are not corrected here; the observation is a V2 design consideration.

**Observation 2 — The latent activation mechanism as V2 infrastructure.** The `latent_objects` / `activate_latent_objects()` capability introduced in v1.16.1 is directly applicable to V2 world design. In the play-pen, objects that become accessible only when the agent has demonstrated a physics-schema prerequisite — stacking only available when gravity is consolidated, for example — will use the same mechanism. v1.16.1 is the first implementation; its correctness is validated here before V2 relies on it.

---

## 8. Forward note

Per programme discipline: no future trajectory is stated in the v1.16.1 paper. V2, Fibonacci consolidation, and Cozmo are not mentioned. The extrusion finding is reported as a V1 result. The SICC carries the forward significance.

Pre-registration committed. Code may proceed.
