# v1.10 Batch Fix: Belief-Revision Bias Activation Timing

**Date:** 4 May 2026
**Iteration:** v1.10
**Type:** Batch re-run (not a pre-registration amendment — architecture unchanged)
**Trigger:** approach_delta=0 and bias_active=0 across all 39 BR records in v1.10 batch

---

## 1. What was wrong

`process_pe_substrate()` was called from the batch runner after
`build_bundle_from_observers()` — at the end of the run, after
`on_run_end()` had already been called on all observers. This meant:

- The bias was never active during the run
- The approach-counting windows never accumulated counts
- `approach_delta` and `bias_active_steps` were zero for all records
- Category δ Component 2 could not be evaluated

The pre-registration architecture was correct: bias activates at
revision, bias modifies approach behaviour. The implementation
activated the bias post-hoc, after the run had completed.

---

## 2. Fix

`V110BeliefRevisionObserver.on_post_event()` now detects
HAZARD→KNOWLEDGE transformations in real time by reading
`world.object_type` directly. When an object transitions to KNOWLEDGE
and has `pre_transition_hazard_entries > 0`, the revised_expectation
record fires immediately and the bias activates for the remaining
steps of the run.

`process_pe_substrate()` now runs as a reconciliation pass at run end:
it corrects the `surprise_step` field from the PE substrate's actual
entry step (replacing any fallback value used by live detection) and
handles any resolutions missed by live detection.

This is an implementation fix, not an architectural change. The
pre-registration's behavioural-consequence specification is unchanged.

---

## 3. Re-run

`curiosity_agent_v1_10_1_batch.py` — identical to v1.10 batch runner
except outputs tagged `v1_10_1`. Seeds unchanged (run_data_v1_9.csv).
All 40 runs re-run.
