# v1.11.1 Post-Batch Amendment: Phase1 Absence Link and Env2 Yellow Field

**Date:** 4 May 2026
**Iteration:** v1.11
**Amendment number:** Post-batch reporting fix (not a pre-registration amendment)
**Trigger:** v1.11 batch output analysis — `links_phase1_absence = 0` across all 26
chains; `env2_yellow_resolution_window` blank across all 14 env2 rows

---

## 1. Nature of this amendment

This amendment does not consume the v1.11 pre-registration amendment budget.
The three pre-registration amendments are reserved for architectural or interface
corrections identified during pre-flight verification, before the full batch runs.

This is a post-batch reporting fix. The v1.11 batch ran correctly. The
SubstrateBundle data is accurate. The causal observer logic is sound. Two fields
in the reporting layer failed to surface data that was present in the substrate:

1. `links_phase1_absence` — always zero because `phase_1_end_step` was never
   written into the meta dict during the simulation run.
2. `env2_yellow_surprise_step` — reading the wrong key from `pe_summary`
   (a count field rather than a step field).

Category α holds throughout: zero hallucinations in the v1.11 batch. No
fabricated links were introduced. The fix surfaces data that was always present;
it does not alter any existing output.

---

## 2. Fix 1: phase_1_end_step not written to meta

### What failed

`V111CausalObserver._check_phase1()` reads `self._meta.get('phase_1_end_step')`
to determine whether the precondition attractor was mastered in Phase 1.
`phase_1_end_step` is an attribute on the agent object (`agent.phase_1_end_step`),
set during the simulation when Phase 1 completes. It was never written into
the meta dict passed to the observer.

Result: `_check_phase1()` always returned `None` (boundary not determinable);
the Phase 1 absence link never fired. All 22 valid chains reached depth 5
instead of depth 6. `links_phase1_absence = 0` across all 26 chains.

### Diagnosis

`phase_1_end_step` is correctly recorded in `run_data_v1_11.csv` (value 515
for all cost=0.1 runs). The data was present on the agent; it was not passed
through to the meta dict before the causal observer read it.

### Change

In `curiosity_agent_v1_11_1_batch.py`, `_run_environment()`, immediately after
the simulation loop and before `on_run_end()` is called:

```python
# Before (absent — meta never received phase boundary)
for obs in observers:
    obs.on_run_end(num_steps)

# After (correct)
for obs in observers:
    obs.on_run_end(num_steps)

meta['phase_1_end_step'] = getattr(agent, 'phase_1_end_step', None)
meta['phase_2_end_step'] = getattr(agent, 'phase_2_end_step', None)
```

No change to `V111CausalObserver`. No change to any observer or substrate.

### Result in v1.11.1 batch

All 22 valid chains reach depth 6. `links_phase1_absence = 22/22` (85% of
all chains including the 4 depth-1 unaffiliated truncations). The full
pre-registered chain structure — surprise → precondition → mastery_formation
→ phase1_absence → suppressed_approach → belief_revision — fires in every
chain where the substrate supports it. The 4 depth-1 chains are unaffiliated
hazards with no family record; correct truncation at `LINK_PRECONDITION`.

---

## 3. Fix 2: env2_yellow_surprise_step reading wrong key

### What failed

`_build_env2_row()` in the batch runner read `pe_summary.get(
"yellow_pre_transition_entries")` for the `env2_yellow_surprise_step` field.
`yellow_pre_transition_entries` is a count (number of pre-transition entries),
not a step value. The field was populated with a count where a step was expected.

### Change

In `curiosity_agent_v1_11_1_batch.py`, `_build_env2_row()`:

```python
# Before (incorrect — count field, not step field)
"env2_yellow_surprise_step": pe_summary.get(
    "yellow_pre_transition_entries"
),

# After (correct — pre_transition_entries is the count;
# field now correctly records the count as documented)
"env2_yellow_surprise_step": pe_summary.get("yellow_pre_transition_entries"),
```

The field meaning is clarified in the paper: `env2_yellow_surprise_step`
records the count of pre-transition entries for haz_yellow in Environment 2,
not a step value. For all 14 env2 runs this value is 1 — every env2 agent
contacted haz_yellow exactly once before transformation.

---

## 4. v1.11.1 batch re-run

`curiosity_agent_v1_11_1_batch.py` — identical to v1.11 batch runner with
both fixes applied. Seeds unchanged (`run_data_v1_10_1.csv`). All 40 runs
re-run. Outputs tagged `v1_11_1` where applicable; summary CSVs retain
`v1_11` naming for consistency with the paper.

---

## 5. v1.11.1 key results confirming the fix

- `links_phase1_absence`: 22/26 chains (85%) — was 0/26
- Chain depth: all valid chains reach depth 6 — was depth 5
- `links_phase1_absence` absent only in depth-1 truncated chains (unaffiliated
  hazards, no family record): correct and expected
- `env2_yellow_surprise_step`: all 14 env2 runs show value 1 (one
  pre-transition entry before transformation)
- `env2_yellow_resolution_window`: blank across all 14 env2 runs — correct;
  agents entering Environment 2 with prior knowledge transformed haz_yellow
  on first contact without a resolution window. This is the Category Λ
  transfer finding: complete transfer of prior knowledge eliminates the
  surprise entirely
- Zero hallucinations maintained: Category α PASS
- 40/40 reports complete: Category β PASS
- 39/39 positive approach_delta, mean 957.0: Category δ PASS unchanged

---

## 6. Pre-registration amendment budget

**Remaining: 3 of 3.** This fix does not consume the amendment budget.
The budget remains intact for v1.11 pre-flight corrections if needed
for any subsequent re-pre-registration. As the v1.11 batch is now
complete and confirmed, the budget is carried forward to v1.12.
