# v1.8.1 Pre-Registration Amendment: Goal Progress Redefined as Phase 2 Motivated Engagement

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 3 May 2026
**Status:** Amendment to v1.8 pre-registration (Baker, 2026ai)
**Repository:** github.com/RancidShack/developmental-agent
**Amendment number:** 1 of 3 available

---

## 1. Trigger

The v1.8 batch produced a Category ζ finding that exposes a conceptual
violation in the goal layer's progress definition.

Across all 16 expired runs, the `last_progress_step` values cluster at
three values — 5, 55, and 188 steps — producing goal-resolution windows
of approximately 159,812–159,995 steps regardless of cost condition. The
anticipated cost-sensitivity pattern (Component 2) is absent. The
distribution has non-trivial variance (std=65, Component 1: PASS), but
that variance is noise around a near-constant value rather than a
meaningful developmental signal.

The diagnosis: the `goal_progress` event for `locate_family` goals fires
on first perception of the distal object within the perception radius.
In V17World, the Phase 1 waypoint sweep is deterministic — it covers the
full 12×12×12 volume at fixed 2.5-unit spacing before Phase 2 begins.
The distal objects (`dist_green`, `dist_yellow`) fall within the sweep
path, so perception fires at steps 5, 55, or 188 across all seeds,
regardless of cost condition. The progress event is a Phase 1 mapping
event, not a Phase 2 motivated engagement event.

---

## 2. The Montessori precept violated

The programme's developmental framing holds that Phase 1 is
environmental mapping: the learner surveys the prepared environment,
perceives what is available, and registers where things are. This is
legitimate and necessary — the Montessori prepared environment is
designed to be visible to the learner during the survey phase. A child
walking around the classroom noting where the pink tower is located has
not started working toward the pink tower.

Phase 2 is where motivated engagement begins. The learner chooses what
to approach, interact with, and work on. Goal-directedness — the
subject of v1.8 — is a Phase 2 phenomenon. Recording a Phase 1
survey-phase perception as goal progress conflates the two phases and
produces a goal-resolution window that measures almost nothing: the
distance between a deterministic mapping event and the budget boundary.

The v1.8 goal layer, as implemented, violates this precept. The
amendment corrects it.

---

## 3. Architectural correction

### 3.1 New record type: `goal_environment_mapped`

A new record type is introduced between `goal_set` and `goal_progress`
in the developmental sequence. It fires when the distal-tier object of
the target family first enters the perception radius, regardless of
phase. This records the mapping event honestly — the agent has located
the object in the environment — without treating it as motivated
engagement.

Fields:
- `mapped_at_step` — the step at which the distal object was first
  perceived
- `mapped_in_phase` — the agent's phase at the time of perception
  (expected to be 1 in almost all runs)

The `goal_environment_mapped` record is not a progress event. It does
not contribute to the goal-resolution window. It is a mapping record,
held in the goal substrate alongside the progress records.

### 3.2 `goal_progress` redefined

`goal_progress` for `locate_family` goals now fires on first *attractor
mastery* within the target family — `att_green` mastered (for GREEN
goals) or `att_yellow` mastered (for YELLOW goals) — rather than on
first perception of the distal object.

Attractor mastery is a Phase 2 event: it requires the agent to
voluntarily approach and repeatedly contact the attractor object,
which occurs only after Phase 1 mapping is complete and the agent's
curiosity and preference drives are active. It is cost-sensitive:
at high cost conditions, the threat layer's gating behaviour shapes
when the agent approaches objects, producing different mastery timings
across conditions.

The progress_type field for this event is `"attractor_mastered"` rather
than `"first_perception"`.

For `bank_hazard_within_budget` goals, `goal_progress` continues to
fire on first perception of the target hazard — but is now also gated
on Phase 2, consistent with the motivated-engagement principle. The
hazard is perceived during Phase 1 mapping; voluntary approach begins
in Phase 2. The progress event fires on first *contact* with the target
hazard (cost paid) in Phase 2 or later, rather than on first perception.

The progress_type field for this event is `"hazard_first_contact"`.

For `achieve_end_state` goals, the progress definition is unchanged:
progress fires when `agent.activation_step` becomes non-None, which is
already a Phase 2/3 event.

### 3.3 Goal-resolution window (redefined)

The goal-resolution window remains: the gap between `last_progress_step`
and `step_budget` in expired runs. With `goal_progress` now anchored to
Phase 2 events, the window measures the developmental distance between
first motivated engagement with the target and the budget boundary.

Expired runs where `goal_environment_mapped` fired but `goal_progress`
did not are the architecturally interesting case: the agent registered
the target in the environment during Phase 1, but never engaged with it
in Phase 2 within the observation window. The biographical register
describes this explicitly: the agent knew where the object was; it did
not choose to pursue it.

In these runs, `goal_resolution_window` is None (no progress event),
but `goal_environment_mapped` is present. The Q3 expired statement is
extended to distinguish this case:

> *My goal (locate_family: GREEN) expired at step 160,000 without
> resolution. I registered the GREEN family in the environment at step
> 55 during Phase 1 mapping, but did not engage with it during Phase 2
> within the observation window.*

This is richer than the v1.8 window-based statement and does not
require the amendment candidate flagged post-batch (the "never started"
check) — the `goal_environment_mapped` record carries that information
directly.

### 3.4 Phase 1 navigation unchanged

The waypoint sweep is not modified. The agent continues to navigate
the full 12×12×12 volume during Phase 1, perceiving all objects within
the perception radius as part of the environmental survey. The family
observer continues to record `colour_registered` and
`colour_first_perception_step` during Phase 1 as before. Only the
goal layer's interpretation of Phase 1 perception changes.

---

## 4. Updated goal substrate structure

```
goal_set               — step 0 (unchanged)
goal_environment_mapped — Phase 1 perception of target (NEW)
goal_progress          — Phase 2+ attractor mastery / hazard contact (REDEFINED)
goal_resolved          — full criterion met within budget (unchanged)
goal_expired           — budget expired without resolution (unchanged)
```

The SubstrateBundle `goal` field gains a `goal_environment_mapped` key:

```python
{
    "goal_set":               {...},
    "goal_environment_mapped": {"mapped_at_step": int, "mapped_in_phase": int} | None,
    "goal_progress":          [...],
    "goal_resolved":          {...} | None,
    "goal_expired":           {...} | None,
    "goal_summary":           {...},
}
```

`bundle.resolve("goal", "goal_environment_mapped")` returns True if the
mapped record is non-None.

---

## 5. Updated pre-registered criteria

### Category ζ (revised)

**Component 1:** Distribution of `goal_resolution_window` across expired
runs where `goal_progress` fired (i.e. `last_progress_step` is not None)
must have non-trivial variance (std > 0).

**Component 2 (revised):** Mean `goal_resolution_window` must vary across
cost conditions. Pre-registered directional prediction: cost=2.0 produces
the shortest mean window (agents at this cost level engage most
efficiently with Phase 2 objects); cost=10.0 produces the longest mean
window (high-cost avoidance delays Phase 2 engagement).

**Component 3 (new):** In runs where `goal_environment_mapped` fired but
`goal_progress` did not (registered-but-not-engaged expired runs), the
Q3 statement must describe the mapping event and its absence of Phase 2
follow-through.

### New Category δ criterion

`goal_environment_mapped` fires in all runs where the target family's
distal object falls within the Phase 1 waypoint sweep path. Given
V17World's fixed object placement and deterministic sweep, this is
expected to fire in all 40 runs. A run where `goal_environment_mapped`
is None indicates the distal object is outside the sweep path — a
substrate finding to be reported as Category Φ.

---

## 6. Code changes

**Modified file:** `v1_8_goal_layer.py`

Changes are confined to `V18GoalObserver`:
- `__init__`: add `_mapped_record = None`, `_mapped = False`
- `_check_progress`: split into `_check_mapping` (Phase 1 perception,
  fires `goal_environment_mapped`) and `_check_progress` (Phase 2+
  motivated engagement, fires `goal_progress`)
- `on_post_event`: call `_check_mapping` before `_check_progress`
- `get_substrate`: add `goal_environment_mapped` field
- `goal_row`: add `mapped_at_step`, `mapped_in_phase` fields

**Modified file:** `v1_8_observer_substrates.py`

- `_v18_query_where_surprised`: extend expired statement to include
  mapping context where `goal_environment_mapped` is present but
  `goal_progress` is absent.
- `bundle.resolve("goal", "goal_environment_mapped")`: already handled
  by the generic non-None check in the patched `resolve()`.

**No other files are modified.** The parallel-observer preservation
property holds: with `goal_obs=None`, output is byte-identical to v1.7.

---

## 7. Methodological note

This amendment is triggered by a genuine conceptual finding in the v1.8
batch data, not by a code error. The v1.8 implementation was internally
consistent; it recorded what it was designed to record. The finding is
that what it was designed to record — first perception during Phase 1
mapping — is architecturally inconsistent with the Montessori
developmental framing that distinguishes environmental survey from
motivated engagement.

The amendment restores the precept: Phase 1 maps. Phase 2 engages.
The goal layer records both events, distinguishes them, and measures
the developmental distance between motivated engagement and the
observation window boundary.

---

**Amendment commitment:** This document is committed to the public
repository at github.com/RancidShack/developmental-agent on 3 May 2026,
before any v1.8.1 implementation work begins.
