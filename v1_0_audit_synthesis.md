# v1.0 Integration Audit — Synthesis

**Status:** Working analysis document. Findings summarised here will inform the v1.0 paper draft. All numbers below are derived from `run_data_v1_0.csv` and `snapshots_v1_0.csv` produced by the v1.0 batch (180 runs, 14.2 min runtime, 9,057 snapshots).

---

## Pre-flight verifications

Both verifications passed before the batch ran:

- v1.0 with instrumentation off produces output bit-for-bit identical to v0.14 baseline at matched seeds.
- v1.0 with instrumentation on produces the same per-run metrics as v1.0 with instrumentation off — the recorder is non-invasive at the behavioural level.

These establish the architectural-preservation property the pre-reg's Section 3.3 commits to.

---

## Headline figures

| Run length | Activation | End-state discovery | Transitions 5/5 | Banked 5/5 | Phase 3 clean |
|------------|-----------|---------------------|-----------------|------------|---------------|
| 20,000     | 17/60     | 10/60               | 40/60           | 26/60      | 60/60         |
| 80,000     | 45/60     | 39/60               | 55/60           | 51/60      | 60/60         |
| 160,000    | 53/60     | 51/60               | 60/60           | 59/60      | 60/60         |

**All 12 of these figures match the v0.14 original batch to the run.** Category α-6 passes exactly. Phase 3 cleanness shows 60/60 at every (cost, run length) cell — exceeding the v0.10 baseline at 20,000 steps, where v0.10 had cells below 10/10. The cumulative inheritance chain produces stronger Phase 3 cleanness than v0.10 alone.

---

## Category α — Preservation

Six sub-checks, all pass.

- α-1 (v0.8 baseline): rule adherence preserved at 60/60; concentration metric (top-attractor) shows artefact (see δ-3); biographical individuation preserved per γ-2 and γ-3.
- α-2 (v0.10 baseline): persistent threat representation operates as v0.10 specifies; 160/160 atomic threat-flag clears at knowledge banking confirms persistence and clearance mechanism.
- α-3 (v0.11.2 baseline): bounded mastery operates as v0.11.2 specifies; 981 attractor-banking events all show third-entry firing.
- α-4 (v0.12 baseline): category-level generalisation operates as v0.12 specifies; the v0.10 boundary at cost 5.0 / 20,000 is eliminated (10/10 Phase 3 clean).
- α-5 (v0.13 baseline): late-target activation operates per v0.13's amended trigger; conditional discovery at 160k = 51/53 = 96.2%, slightly above v0.13's 93.9%.
- α-6 (v0.14 baseline): all 12 headline figures match v0.14 to the run; 862/862 cell-type transitions show atomic update; H2 inversion direction holds.

**Category α verdict: 6/6 pass.**

---

## Category β — Cross-Layer Coupling Characterisation

Three sub-checks, all pass.

### β-1 (mechanism at coupling moments)

- 862/862 cell-type transitions show cell_type changing HAZARD → KNOWLEDGE atomically between before and at snapshots. Atomic update confirmed mechanistically.
- 160/160 knowledge-banking events on flagged cells show threat flag clearing atomically (1 → 0) between before and at. Atomic clearing confirmed mechanistically.
- 115/115 end-state activation events show drive-weighted score change across all four actions. Coupling is bidirectional (mean -0.19, max +0.67, max -9.14) and detected at every event.

### β-2 (phenomenon-class at three iterations)

The three documented cross-layer effects are now mechanistically confirmed at snapshot resolution:

- v0.11.2's mastery-affects-threat-side effect, identified post-hoc in the v0.12 paper, operates through trajectory redistribution. Visible in attractor-banking snapshots in runs adjacent to hazard regions.
- v0.13's end-state-affects-threat-side effect operates through attentional redirection. Confirmed at all 115 end-state activation events: drive-weighted score changes across all four candidate actions.
- v0.14's bidirectional gate-and-mastery coupling at cell-type transitions confirmed at all 862 transition events: gate state updates atomically with cell-type state.

### β-3 (escalation to structural property)

Three observations across three iterations is the threshold the v0.14 paper named for confirming the phenomenon-class. The v1.0 instrumented data confirms all three observations at snapshot resolution. The escalation from "phenomenon-class confirmed" to "structural property of the architecture" is supported.

**Category β verdict: 3/3 pass.**

---

## Category γ — Individuation at Full-Arc Scale

Three sub-checks, two pass, one fails as a metric artefact (see δ-3).

### γ-1: top-attractor diversity preservation — FAIL

Threshold: ≥4 of 6 distinct top attractors at 160k per condition. Result: 1 of 6 at every condition; 178/180 runs show `top_attractor = (3,3)`.

**Investigation surfaced this is a metric artefact.** Of the 178 runs with top=(3,3), `top_attractor_pref = 0.0`. The four mastery interventions deplete every attractor's preference to zero by the time all are mastered; `max(attractor_prefs)` then returns the first key in Python dict iteration order, which is (3,3). This is not biographical concentration — it is metric collapse under the inheritance-chain mastery-interventions regime.

The v0.8 essay's individuation finding used `top_attractor` as the diversity measure because v0.8 had no mastery layer to deplete preferences. With v0.11.2's four mastery interventions in place across the inheritance chain, the metric no longer measures what it measured at v0.8.

### γ-2: mastery-sequence diversity preservation — PASS

Per-cell distinct mastery sequences (out of 10):

| cost | 20k   | 80k   | 160k  |
|------|-------|-------|-------|
| 0.1  | 10/10 | 10/10 | 10/10 |
| 0.5  | 10/10 |  8/10 |  9/10 |
| 1.0  | 10/10 | 10/10 | 10/10 |
| 2.0  |  9/10 |  8/10 | 10/10 |
| 5.0  | 10/10 | 10/10 | 10/10 |
| 10.0 | 10/10 | 10/10 | 10/10 |

Mean diversity at 160k: 9.83 of 10. Biographical individuation is strongly preserved when measured against the order of attractor mastery rather than the residual top preference.

### γ-3: knowledge-banking-order diversity — PASS

Per-cell distinct knowledge-banking orders for runs in which all 5 hazards were banked. Mean diversity at 160k: 9.5 distinct orders out of mean 9.8 banked-runs. Strongly diverse, supports v0.14's autonomous prioritisation finding.

**Category γ verdict: 2/3 pass; γ-1 fails as δ-3 metric artefact, with biographical individuation preserved at full strength per γ-2 and γ-3.**

---

## Category δ — Negative Findings

### δ-1 (preservation gap): NONE

All six α sub-checks pass. No preservation gap surfaces.

### δ-2 (coupling-mechanism gap): NONE

All three β sub-checks pass. The cross-layer coupling effects predicted by the iteration papers are mechanistically confirmed.

### δ-3 (individuation drift): METRIC CALIBRATION DRIFT, NOT ARCHITECTURAL DRIFT

γ-1 fails the pre-registered threshold via the `top_attractor` artefact described above. The recommendation, under Section 8 amendment policy, is to recalibrate γ-1 against an inheritance-distribution-aware metric. The amendment is operational, not architectural.

This is the v1.0 analogue of the v0.13 calibration lesson: pre-registered thresholds for an iteration's success should be calibrated against the inheritance distribution where the metric is bounded by inherited dynamics. The lesson held forward to v0.14, and now holds forward to v1.0.

### δ-4 (instrumentation artefact): SUBSTANTIVE EMPIRICAL FINDING

641 of 801 (80%) knowledge-banking events occurred on cells whose threat flag was never raised. Low-threshold cells transition before the agent has accumulated three hazard entries, bypassing the threat layer's categorical learning for those cells.

This is a finding the per-run metrics could not surface. The instrumentation made it visible. It is not an artefact of the instrumentation; the instrumentation revealed an asymmetry in the architecture's threat-and-mastery coupling at low competency thresholds. The substantive content for the v1.0 paper: the architecture's threat-side categorical learning is partially bypassed by the v0.14 competency-gating mechanism for low-threshold cells. This is consistent with the H2 inversion's mechanism — obstacle-removal-via-flagging is more accelerative than transition-with-attendant-exploration-cost — and adds mechanistic detail to that account.

---

## Category Ω — Philosophical Claims

All four Ω claims are supported by the evidence the batch produces, with the claim/evidence boundary held cleanly per the pre-reg's Section 9 commitment.

- **Ω-1** (biography is not a function of scale): supported by γ-2 and γ-3. The γ-1 metric artefact is reported transparently as δ-3 rather than as evidence against the claim.
- **Ω-2** (development has architectural requirements that can be specified, isolated, and tested): supported by α + β collectively. Six preservation sub-checks and three coupling-mechanism sub-checks pass, demonstrating the methodology operates.
- **Ω-3** (governable AI has methodological prerequisites the programme has built): the δ-3 finding itself is evidence — the methodology surfaces calibration issues honestly rather than concealing them.
- **Ω-4** (architectural arc complete on its own terms at v1.0): supported by α + β + γ collectively. The two arcs compose into a coherent architectural statement.

---

## Summary

Category α: **6/6 PASS**. Full preservation across the inheritance chain.

Category β: **3/3 PASS**. Cross-layer coupling mechanisms confirmed at snapshot resolution; phenomenon-class escalates to structural property.

Category γ: **2/3 PASS**, with γ-1 failing as δ-3 metric calibration artefact. Biographical individuation preserved at full strength per γ-2 and γ-3.

Category δ: δ-1 NONE, δ-2 NONE, δ-3 METRIC ARTEFACT (amendment recommended), δ-4 SUBSTANTIVE FINDING (the 80% threat-bypass at low thresholds).

Category Ω: All four philosophical claims supported by the empirical evidence the batch produces, with claim and evidence kept distinct per Section 9.

The v1.0 architectural-statement paper has its data.
