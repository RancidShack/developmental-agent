# v1.0 Integration Audit Batch

This directory contains the v1.0 batch implementation per the v1.0
pre-registration (Baker, 2026, "v1.0 Pre-Registration: Integration
Audit of the Cumulative Inheritance Chain via Heavy Instrumentation
at Cross-Layer Coupling Moments").

## Files

`curiosity_agent_v0_14.py` — v0.14 architecture, **unchanged**. Imported
verbatim by the v1.0 batch runner. Do not modify.

`v1_0_recorder.py` — Heavy instrumentation recording layer. Captures
state at six classes of cross-layer coupling moment per the pre-reg's
Section 3.1, with snapshot triples (before / at / after) per Section
3.2. Read-only access to agent and world state — does not modify
architectural behaviour.

`curiosity_agent_v1_0_batch.py` — Batch runner. Loads matched seeds
from `run_data_v0_14.csv`, runs the v0.14 architecture under v1.0
instrumentation across the 180-run experimental matrix, and writes
two outputs: `run_data_v1_0.csv` (per-run metrics, schema parallel to
v0.14) and `snapshots_v1_0.csv` (heavy-instrumented per-snapshot data).

`verify_no_instrument_equivalence.py` — Verifies that v1.0 with
instrumentation off produces output bit-for-bit identical to the v0.14
baseline. Tests the architectural-preservation property the pre-reg
Section 3.3 commits to.

`verify_instrumentation_neutrality.py` — Verifies that v1.0 with
instrumentation on produces the same per-run metrics as instrumentation
off. Tests that the recorder is non-invasive at the behavioural level.

## Pre-flight checks

Run both verifications before the full batch:

```
python3 verify_no_instrument_equivalence.py
python3 verify_instrumentation_neutrality.py
```

Both must pass. They take roughly 30 seconds each.

## Running the batch

The batch needs `run_data_v0_14.csv` in the working directory for seed
loading. With that file present:

```
python3 curiosity_agent_v1_0_batch.py
```

Estimated runtime: approximately 50 minutes on a personal laptop, based
on a per-run rate of roughly 19 seconds per 100k steps with
instrumentation enabled. The matrix is 60 × 20k + 60 × 80k + 60 × 160k
= 16,200,000 step-runs in total.

Outputs:
- `run_data_v1_0.csv` (~1 MB, per-run metrics across 180 runs)
- `snapshots_v1_0.csv` (~10–15 MB, per-snapshot heavy instrumentation)

## Running with instrumentation disabled

For verification purposes only — produces v0.14-equivalent output:

```
python3 curiosity_agent_v1_0_batch.py --no-instrument
```

## Running a smaller test

For quick iteration:

```
python3 curiosity_agent_v1_0_batch.py --steps 20000 --runs 2
```

This runs 12 of the 180 runs and produces correspondingly smaller
outputs — useful to verify the batch runs end-to-end before
committing to the full 50-minute run.

## What the batch produces

The two output CSVs together support the v1.0 paper's Categories α, β,
γ, and δ analyses per the pre-reg's Section 6:

- Category α (preservation): comparison of `run_data_v1_0.csv`
  against `run_data_v0_14.csv` and earlier baseline CSVs at matched
  seeds. The v1.0 per-run metrics are schema-compatible with v0.14
  for direct comparison.

- Category β (coupling characterisation): analysis of
  `snapshots_v1_0.csv`. The snapshot triples (before / at / after) at
  each coupling moment provide the mechanistic data the iteration
  papers' aggregate metrics could not carry. Drive-weighted scores,
  Q-values, primitive bias, preferences, gate exclusion set, threat-
  flag state, and cell-type state are all captured at each snapshot.

- Category γ (individuation at full-arc scale): diversity measures
  derived from `run_data_v1_0.csv` (top-attractor, mastery-sequence,
  knowledge-banking-order) compared against v0.8 and v0.14 baselines.

- Category δ (negative findings): any preservation gaps,
  coupling-mechanism gaps, individuation drift, or instrumentation
  artefacts surface during analysis. The snapshot CSV's resolution
  permits identification of artefacts the per-run metrics cannot
  surface.

## What the batch does not produce

Per the pre-reg's Section 9 empirical-versus-interpretive boundary:

- The batch does not adjudicate between the H2 inversion's two
  readings (obstacle-removal mechanistic versus developmental). The
  snapshot data is sufficient to characterise both readings but
  not to distinguish them; that is reserved for v0.15 obstacle-
  removal-isolation work.

- The batch does not test generalisation beyond the present tabular
  environment, beyond the present cell-type set, or beyond the
  present scale.

The batch's contribution is bounded by what the pre-reg specifies:
audit data sufficient to support the v1.0 architectural-statement
paper's Category Ω claims at the level the empirical evidence carries.
