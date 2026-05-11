# v1.0.2 Pre-Registration Amendment: Extended-Run Batch for Time-to-Completion Characterisation and Route-Shortening Analysis

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 28 April 2026
**Status:** Amendment to v1.0 pre-registration (Baker, 2026p), committed before the extended-run batch runs.
**Amendment budget:** 2 of 3 used (v1.0.1 is the first; this is the second).

---

## 1. Scope

This amendment specifies a supplementary batch under the v1.0 pre-registration: the v0.14 architecture run at extended run length, sufficient to permit the great majority of agents to reach the architectural completion state (end-state cell banked) within the experimental window. The supplementary batch produces three empirical characterisations the original v1.0 batch's three run lengths (20k, 80k, 160k) cannot:

- The distribution of time-to-completion across the population, under conditions where the experimental window does not truncate the developmental arc.
- The relationship between cell-type transition timing and post-activation discovery time, characterising the route-shortening dynamics the v0.14 architecture produces.
- The effect of hazard-competency-threshold permutation on completion time, informing how the prepared environment's structure interacts with completion efficiency.

The architecture is unchanged. The instrumentation is unchanged (heavy snapshot recording is not required for these characterisations). The matched-seed apparatus extends the seed chain to the new run length. The amendment is operational, not architectural.

## 2. Why this batch is justified under the v1.0 pre-registration

The v1.0 pre-registration's Section 9 empirical-versus-interpretive boundary states what v1.0 is testing and what v1.0 is not testing. Among the items v1.0 is not testing is: "Whether the architectural principles generalise beyond the present tabular environment to richer environments." The supplementary batch does not extend the architecture's domain. It characterises behaviour the present architecture produces at run lengths the original batch could not measure.

The original v1.0 batch's three run lengths were chosen to match the v0.13/v0.14 inheritance-chain matrix for matched-seed comparison. At 160,000 steps, 51 of 60 runs reach end-state banking; 9 do not. Among runs reaching activation but not completion, post-activation windows average ~123,000 steps but maximum observed discovery times reach 67,257 steps. The 160,000-step window is therefore at the boundary of comfortable completion: most runs finish, some do not, and the distribution of finishing times is partially censored by the window itself.

The Foundation Learning Architecture (FLA) framing the v1.0 paper's methodological reflection adopts treats the experimental run length as *external to the architecture*. The architecture's developmental primitives — competency thresholds, mastery banking, end-state activation, end-state banking — are keyed on the agent's state, not on elapsed time. Run length is the experimenter's instrument for sampling the architecture's pace distribution, not a property of the architecture itself. To characterise that distribution cleanly, the sampling window must be wide enough that it does not act as a censor.

The supplementary batch widens the window. The architectural claim does not extend; the measurement does.

## 3. Experimental matrix

### 3.1 Run length

The supplementary batch uses run length 320,000 steps. The choice is calibrated against the v1.0 batch's observed dynamics:

- Activation steps for fully-converged runs at 160k cluster between approximately 30,000 and 60,000 steps.
- Maximum observed discovery time at 160k was 67,257 steps.
- A run reaching activation at the upper end (~60,000) and discovery at the upper end (~70,000 or slightly more) would complete at ~130,000 steps total. 320,000 steps gives every agent approximately 250,000 steps post-activation in the worst case, comfortably above any observed completion timing.

A longer run length (e.g. 500,000) would provide additional safety margin but doubles the compute requirement without proportional empirical yield. 320,000 is the working choice; if the supplementary batch reveals runs that still do not reach completion within this window, the v1.0 paper reports the residual non-completion rate honestly and the implication is that those runs require additional architectural support beyond longer run length, which is a substantive finding rather than a measurement gap.

### 3.2 Cost levels

The supplementary batch uses three cost levels: 1.0, 5.0, 10.0. The choice covers the cost range without the redundancy the original six-cost matrix provides for cross-iteration comparison. The reasoning:

- Cost only affects the pre-transition hazard-entry period. Once a hazard transitions to KNOWLEDGE, cost is irrelevant for that cell.
- The cost level governs how much the agent slows down on the way to competency. Three levels (low, medium, high) characterise the cost-effect on completion time without requiring all six.
- The matched-seed apparatus uses the existing v1.0 batch's seeds at these three cost levels, preserving comparability.

### 3.3 Runs per condition

Ten runs per (cost, 320k) cell, matching the original v1.0 matrix's per-cell run count. Three cost levels × ten runs = thirty runs total.

### 3.4 Seeds

Seeds are loaded from the existing v1.0 batch CSV (`run_data_v1_0.csv`) at the same `(hazard_cost, run_idx)` cells. Specifically, the supplementary run at `cost=1.0, run_idx=3` uses the same seed as the v1.0 batch's run at `cost=1.0, num_steps=160000, run_idx=3`, but executes for 320,000 steps instead of 160,000.

This preserves matched-seed comparability: the extended-run agent's pre-160,000-step trajectory is byte-for-byte identical to the v1.0 batch's run at the same `(cost, run_idx)`. After step 160,000 the extended-run agent continues in whatever architectural state it was in; the v1.0 batch's run terminated. Direct comparison is therefore possible between the "would have finished" trajectories the extended batch reveals and the "did not finish in time" runs the v1.0 batch recorded.

### 3.5 Instrumentation

The supplementary batch runs with `--no-instrument`. Heavy per-snapshot instrumentation is not required for the three target characterisations, which are derivable from the per-run CSV. Disabling the recorder reduces compute time and output volume without affecting the analysis.

The pre-flight verification (`verify_no_instrument_equivalence.py`, already passed) confirms that the no-instrument batch produces output bit-for-bit identical to the v0.14 baseline at matched seeds. The supplementary batch therefore inherits the architectural-preservation guarantee.

## 4. Analysis questions

The supplementary batch produces a per-run CSV (`run_data_v1_0_extended.csv`) with the same schema as the v1.0 batch. The analysis answers three questions, each operationalised against fields already in the schema.

### 4.1 Time-to-completion distribution

Across the thirty runs, what proportion reach the architectural completion state (`end_state_banked == True`) within 320,000 steps? Among completing runs, what is the distribution of completion times, computed as the step at which `end_state_found_step` is recorded?

Decomposition: the completion time decomposes into four phases.

- Phase-1-and-2 time: from run start to first attractor mastery (`time_to_first_mastery`).
- Mastery accumulation time: from first to final mastery (`time_to_final_mastery − time_to_first_mastery`).
- Activation latency: from final mastery to end-state activation (`activation_step − time_to_final_mastery`). This is the time the agent spends completing knowledge banking after attractor mastery is finished.
- Discovery time: from activation to end-state banking (`end_state_found_step − activation_step`).

The decomposition characterises which phase contributes most to total completion time, and how the contributions vary across runs.

### 4.2 Route-shortening characterisation

Within each run, what is the relationship between transition timing and discovery time? Specifically:

- The earliest transition step (`time_to_first_transition`) and the latest (`time_to_final_transition`).
- The discovery time given activation (`discovery_time`).
- The per-cell competency unlock steps (`competency_unlock_steps`).

The analysis tests whether runs with earlier final transitions show shorter discovery times, controlling for activation step. The architectural prediction: earlier transitions open routes earlier, shorter routes accelerate post-activation locating, and discovery time correlates negatively with the activation-to-final-transition gap. The extended batch produces enough completing runs at consistent run length to estimate this relationship.

### 4.3 Threshold-permutation effect

The hazard cells are assigned competency thresholds {1, 2, 3, 4, 5} via random permutation per run. The permutation is recorded in the `hazard_thresholds` field of the per-run CSV. Different permutations produce different unlock orderings, which interact with the environment's geometry to produce different route-opening sequences.

The analysis tests whether some permutations systematically produce faster completion than others. Specifically: across the thirty extended-run agents, which permutations are associated with shortest and longest completion times? Are the differences cost-dependent?

The result informs how the prepared environment's threshold-assignment structure interacts with completion efficiency. If certain permutations consistently accelerate completion in the present geometry, the principle generalises (with appropriate caution) to environment-construction guidance for richer settings: assign thresholds in orders that maximise route-opening efficiency given the environment's geometry.

This is the FLA-grounded operational claim the supplementary batch supports: real run data tells us how to construct the prepared environment for the architecture to meet the learner's pace efficiently. The claim is bounded — it operates in the present tabular geometry, with the present five-hazard layout — but the principle it instantiates is generalisable in a way the architecture's primitives directly support.

## 5. What the extended-run batch does not test

The discipline of the v1.0 pre-registration's Section 9 holds. The supplementary batch does not test:

- Generalisation to richer environments, multi-modal sensory contexts, or non-tabular representations. These are reserved for subsequent work.
- The H2 inversion's two readings (obstacle-removal mechanistic versus developmental). The extended batch will produce additional data consistent with the obstacle-removal reading, but the v0.15 obstacle-removal-isolation work specified in earlier amendments remains the methodological vehicle for adjudication.
- Architectural extensions to the threshold-assignment mechanism (e.g. adaptive thresholds responsive to agent state). The supplementary batch operates on the v0.14 random-permutation rule unchanged.
- Multi-agent or cooperative settings. The architecture is single-agent throughout.

The supplementary batch's contribution is bounded: characterisation of the architecture's pace distribution and route-shortening dynamics under conditions where the experimental window does not censor the data. Forward-looking implications are named in the v1.0 paper's discussion section without being claimed by the supplementary batch's findings directly.

## 6. Implementation

The supplementary batch runs through the existing batch runner (`curiosity_agent_v1_0_batch.py`) with the following invocation:

```
python3 curiosity_agent_v1_0_batch.py \
    --steps 320000 \
    --cost 1.0 5.0 10.0 \
    --runs 10 \
    --out run_data_v1_0_extended.csv \
    --baseline run_data_v0_14.csv \
    --no-instrument
```

The baseline is `run_data_v0_14.csv` rather than `run_data_v1_0.csv` because the existing batch runner's seed-loading filter accepts `v0_14` and `v0_14_repl` archs (the canonical seed sources in the inheritance chain). The seeds at the `(cost, run_idx)` cells the extended batch needs are the same in both CSVs by construction — the v1.0 batch loaded its seeds from `run_data_v0_14.csv` itself — so using the v0.14 CSV as baseline is operationally equivalent and avoids requiring a code change to the batch runner.

Estimated runtime: approximately thirty minutes on a personal laptop, based on the 19-second-per-100k-steps rate observed in the original v1.0 batch (without instrumentation overhead, which is small but non-zero).

Output: `run_data_v1_0_extended.csv` (~10 KB, thirty runs).

The v1.0 paper's analysis section combines the original v1.0 batch's CSV (`run_data_v1_0.csv`) with the extended batch's CSV (`run_data_v1_0_extended.csv`) for the time-to-completion characterisation. The two batches are matched-seed comparable at the (cost=1.0, run_idx=*), (cost=5.0, run_idx=*), and (cost=10.0, run_idx=*) cells: the extended batch's pre-160,000-step trajectory is byte-for-byte identical to the v1.0 batch's run at the same (cost, run_idx) cell.

## 7. Methodological commitment

The supplementary batch operates under the same methodological discipline as the original v1.0 batch:

- Pre-registered before the batch runs.
- Architecture unchanged.
- Matched-seed apparatus preserved.
- Output format consistent with prior batches.
- Analysis questions specified in advance against fields already in the data schema.

The amendment policy holds: no architectural change, no surprise reanalysis, no metric introduction without justification grounded in the architecture's existing primitives.

## 8. Commitments

- This amendment is committed to the public repository at github.com/RancidShack/developmental-agent before the extended-run batch executes.
- The amendment is operational, not architectural. No code change to `curiosity_agent_v0_14.py`, `v1_0_recorder.py`, or `curiosity_agent_v1_0_batch.py` is required; the existing batch runner accepts the extended-run parameters via command-line flags.
- The amendment budget for v1.0 stands at 2 of 3 at the close of this amendment. One amendment remains in reserve.
- The v1.0 paper's analysis sections will combine `run_data_v1_0.csv` and `run_data_v1_0_extended.csv` for the time-to-completion characterisation; the original instrumented snapshots in `snapshots_v1_0.csv` remain the source for Category β characterisations.

## 9. References

Baker, N.P.M. (2026b) 'The Childhood AI Never Had: Twelve Iterations of a Computational Developmental Learner', preprint v1.0, 21 April 2026.

Baker, N.P.M. (2026m) 'v0.14 Pre-Registration: Competency-Gated Content Transformation via Hazard-to-Knowledge Cell-Type Transition at Mastery Thresholds', GitHub repository, 26 April 2026.

Baker, N.P.M. (2026o, in preparation) 'Competency-Gated Content Transformation in a Small Artificial Learner: Hazard Cells Becoming Knowledge Cells at Mastery Thresholds', preprint, 27 April 2026.

Baker, N.P.M. (2026p) 'v1.0 Pre-Registration: Integration Audit of the Cumulative Inheritance Chain via Heavy Instrumentation at Cross-Layer Coupling Moments', GitHub repository, 27 April 2026.

Baker, N.P.M. (2026q) 'v1.0.1 Pre-Registration Amendment: Category γ Reframing Around Inheritance-Aware Individuation Metrics', GitHub repository, 28 April 2026.
