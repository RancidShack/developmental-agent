# v1.9.1 Pre-Registration Amendment: Detection Threshold Reduction

**Date:** 4 May 2026
**Iteration:** v1.9
**Amendment number:** 1 of 3
**Trigger:** Level-11 C6 failure (detection_fires)

---

## 1. What failed

Level-11 pre-flight verification completed with one criterion failure:

**C6 detection_fires: FAIL** — zero suppressed-approach records across
all 10 verification runs at cost=1.0, steps=80,000.

All other criteria passed:

- C1 counterfactual_field_present: PASS
- C2 source_key_format_valid: PASS
- C3 source_resolves_for_all_q4: PASS
- C4 zero_hallucinations: PASS (0 hallucinations across all runs)
- C5 eligible_objects_only: PASS
- C7 additive_discipline: PASS (zero Q4 statements, counterfactual=None
  with --no-counterfactual; zero hallucinations)

Level-10 re-run also passed cleanly: 10/10 runs, halluc=0,
terminal=ok. The v1.9 substrate stack introduced no regression into
the v1.8 goal layer.

---

## 2. Diagnosis

The pre-registered thresholds — N_approach=10 (10 consecutive steps of
monotonically decreasing distance) and N_recession=5 (5 consecutive
steps of increasing distance) — are too conservative for V17World's
continuous 3D space at the agent's action granularity.

In V17World, the agent's 27-action vocabulary produces movement in
continuous space with a step size that results in approach trajectories
that are not monotonically decreasing over 10 consecutive steps. The
agent's path toward an object involves lateral corrections and
oscillations at the scale of a few steps; a 10-step monotone window
is longer than the agent's typical clean approach segment before a
directional adjustment occurs. The detection logic therefore never
confirms an approach window, and no suppressed-approach records are
produced.

The detection architecture is correct. The threshold values are
environment-specific and were set conservatively in the pre-registration
as acknowledged: *"If Level 11 Criterion 6 fails (zero suppressed
approaches across all 10 verification runs), a threshold amendment is
the correct response, not a silent parameter adjustment."*

---

## 3. Change

**In `v1_9_counterfactual_observer.py`, the detection thresholds are
reduced as follows:**

| Parameter   | Pre-registered value | Amended value |
|-------------|----------------------|---------------|
| N_approach  | 10                   | 3             |
| N_recession | 5                    | 3             |

**Rationale for N_approach = 3:** Three consecutive steps of decreasing
distance is the minimum window that distinguishes a directed approach
from a single-step oscillation. One step is noise; two steps is
borderline; three steps constitutes a detectable approach trajectory
in V17World's continuous space at the agent's movement granularity.

**Rationale for N_recession = 3:** Symmetric with the approach window.
Three steps of increasing distance after the approach minimum confirms
that the agent has genuinely redirected away from the object rather
than momentarily paused or oscillated at the closest point.

The structural definition of a suppressed approach — approach window
followed by recession without contact — is unchanged. Only the minimum
window lengths are reduced.

---

## 4. What does not change

- The eligible object set (HAZARD and goal-relevant DIST_OBJ)
- The suppressed-approach record structure (all six fields unchanged)
- The SubstrateBundle.counterfactual field and resolve() logic
- The Q4 statement text template
- All pre-registered interpretation categories (α through η)
- The source_key format (`suppressed_approach:{object_id}:{step}`)
- The additive discipline requirement
- The full-batch experimental design (seeds, costs, run length)

---

## 5. Re-verification required

Level-11 must be re-run in full with the amended thresholds before
the full v1.9 batch proceeds. All seven criteria must pass. C6 in
particular must confirm detection fires at the amended thresholds
across the 10 verification runs.

The amendment budget remaining after v1.9.1: **2 of 3**.

---

**Amendment commitment:** This document is committed to the public
repository at github.com/RancidShack/developmental-agent alongside
the amended `v1_9_counterfactual_observer.py` before the Level-11
re-run begins.
