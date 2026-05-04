# v1.12 Pre-Registration: Multi-Environment Developmental Transfer

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Pre-registration document, committed to public repository before any v1.12 code is written
**Repository:** github.com/RancidShack/developmental-agent
**Amendment budget:** Three

---

## 1. Purpose

v1.11 demonstrated that developmental history transfers across environments. Every agent that entered a second prepared environment had eliminated the yellow resolution window entirely — the surprise that cost up to 121,908 steps of developmental work in Environment 1 was absent in Environment 2. The prior knowledge transferred completely.

What v1.11 could not answer is whether the transfer accelerates the full developmental sequence, or merely eliminates a single known surprise. The Q-table carries attractor mastery; does it also carry the developmental structure that produces *faster* mastery of new objects in Environment 2? Does the Phase 1 path shorten? Does activation come earlier? Does the causal chain from Environment 1 — the agent's record of *why* it was surprised — contribute to Environment 2 behaviour beyond what the Q-table alone would produce?

These are the v1.12 empirical questions. No new observer is introduced. No new substrate field. No new query type. The v1.11 stack runs unchanged. The single variable is the observation window: 500,000 steps per environment, replacing 320,000. This is the Montessori principle applied directly — time is not a boundary, and the correct response to a developmental ceiling is to extend the window, not simplify the sequence.

v1.12 is the first iteration since v1.4 whose primary question is empirical rather than architectural. The architecture built at v1.8–v1.11 is sufficient. The question now is what it reveals when given sufficient time to run.

---

## 2. What v1.12 changes

### 2.1 Step count extension

`BATCH_STEPS = 500_000` per environment, replacing 320,000. All other parameters inherited unchanged from v1.11.

**Rationale.** At v1.11, 25/40 agents did not complete the developmental sequence within 320,000 steps. The maximum activation step was 218,587 — well within the window — meaning no agent was close to completing at step 320,000. The window was functioning as a ceiling: agents that hadn't activated by step 218,587 were genuinely incomplete rather than close. At 500,000 steps the completion rate is predicted to rise substantially; the pre-registered expectation is ≥50% (20/40 runs banking the end state), compared to 28% at v1.11.

### 2.2 env2 activation counter reset

`agent.activation_step` and `agent.end_state_banked` are reset to `None` and `False` respectively at the start of Environment 2. `env2_activation_step` is tracked independently and written to `env2_run_data_v1_12.csv`. This corrects the v1.11 data collection artefact in which `env2_activation_step` mirrored `env1_activation_step` because the counter was not reset.

The corrected field enables the primary Category Λ analysis: whether `env2_activation_step < env1_activation_step` — whether agents complete the developmental sequence faster in the second environment than the first.

### 2.3 Q5 structural individuation search

`V111CausalObserver` is inherited unchanged. The Category γ extension for Q5 — structural distance between causal chains within and across runs — is added to the batch runner's post-run analysis.

**Why individuation was absent at v1.11.** All 22 valid chains in the v1.11 batch involved a single object class (haz_yellow) and therefore shared a single link-type sequence (depth 6, all six links). Structural Q5 individuation requires multiple resolved surprises per run from different object classes. At 500,000 steps, GREEN family surprises should appear: `haz_green` requires `att_green` mastery, which has a different formation sequence, a different Phase 1 relationship, and potentially a different resolution window. When chains for both `haz_yellow` and `haz_green` exist in the same run, structural Q5 individuation can be measured.

**The individuation metric.** Chain-type sequence distance: edit distance over the ordered list of link types in each chain, normalised to [0,1]. Applied pairwise across all valid chains within a run (within-run structural distance) and across runs (between-run structural distance). Pre-registered expectation: between-run mean distance > within-run mean distance, consistent with the Q1 individuation finding across all prior iterations.

### 2.4 What v1.12 does not change

All eleven observers are inherited unchanged. `V111CausalObserver` is inherited unchanged. `V110Agent`, `V17World`, the phase schedule, the drive composition, the goal assignment schedule, and all substrate fields are inherited unchanged. `seed_env2 = seed + 10,000` is inherited from v1.11. The causal chain construction, the Q5 statement format, and the honesty constraint are inherited unchanged.

---

## 3. Experimental design

**Batch scale.** 40 runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition × 500,000 steps. Seeds from `run_data_v1_11.csv` at matched (cost, run_idx) cells (fallback: `run_data_v1_10_1.csv`).

**Second environment.** Runs with `environment_complete` records receive a second environment at `seed_env2 = seed + 10,000`, up to 500,000 additional steps. env2 activation counter reset at start of Environment 2.

**Output files.** All v1.11 output CSVs tagged `v1_12`, plus:
- `env2_run_data_v1_12.csv` extended with `env2_activation_step` (independently tracked), `env2_phase_1_end_step`, `env2_yellow_resolution_window`, `env2_green_resolution_window`
- `causal_v1_12.csv` extended with `env` field (1 or 2) per chain
- `q5_individuation_v1_12.csv` — pairwise chain structural distances: `run_idx_a`, `run_idx_b`, `chain_object_a`, `chain_object_b`, `link_sequence_distance`, `within_run` (bool)

**Pre-flight.** Level-12 re-run (`--no-causal`) on the v1.12 stack at 500,000 steps, 10 runs at cost=1.0: all v1.10 Level-12 criteria must pass. Level-13 re-run at 500,000 steps: all eight Level-13 criteria must pass. No new verification level is required — the architecture is unchanged; the only variable is step count.

---

## 4. Pre-registered interpretation categories

All v1.11 categories inherited. Two updated and one new.

### 4.1 Category α: Internal consistency

Inherited. Zero hallucinations across Q1–Q5 including all causal links. The pre-registered expectation is that GREEN family causal chains will appear at 500,000 steps and will produce the same zero-hallucination result as YELLOW family chains. If GREEN family chains introduce a new failure mode — for example, `att_green` mastery not being found in provenance via the `mastery:att_green` key — this is a Category α failure and an amendment, not a new finding.

### 4.2 Category θ: Completion signal

Updated threshold. Pre-registered expectation: ≥50% of runs (20/40) bank the end state at 500,000 steps, compared to 28% at v1.11. The Montessori principle is the justification: extending the window does not change the developmental sequence, it gives the learner sufficient time to complete it. If the completion rate does not rise substantially above 28% at 500,000 steps, this is a finding about the developmental architecture — the sequence requires more than 500,000 steps for two-thirds of agents — and the case for 750,000 steps at v1.13 becomes the SICC recommendation.

### 4.3 Category Λ: Developmental transfer (updated)

**Component 1 (inherited): Yellow resolution window eliminated in env2.**
Pre-registered expectation: `env2_yellow_resolution_window` absent in all env2 runs, consistent with the v1.11 finding. If any env2 run shows a yellow resolution window, this is a new finding — prior knowledge did not fully transfer for that agent — and requires characterisation.

**Component 2 (new): env2 activation faster than env1.**
Pre-registered direction: `env2_activation_step < env1_activation_step` across all runs where both values are available. The mechanism: the agent enters Environment 2 with a mature Q-table that already encodes precondition relationships, reducing the developmental work required to reach activation. The prediction is that env2 activation is substantially earlier — not marginally — because the agent does not need to rediscover the attractor-hazard dependency from scratch.

**Component 3 (new): Green family transfer.**
At 500,000 steps, GREEN family resolved surprises should appear in Environment 1 for some runs. For agents that carry a `haz_green` resolved-surprise record into Environment 2, the pre-registered prediction is that `env2_green_resolution_window` is absent, consistent with the yellow finding. If GREEN family transfer is incomplete — if some env2 agents show a green resolution window despite carrying a green resolved-surprise record — this is informative: it suggests that Q-table transfer is object-class specific, and that the transfer of the yellow precondition does not automatically extend to the green precondition.

Category Λ succeeds if Components 1 and 2 hold. Component 3 is exploratory.

### 4.4 Category ζ (Q5 structural individuation): new

**Component 1: Multi-object chains present.**
At least one run produces causal chains for both `haz_yellow` and `haz_green`. This is the structural prerequisite for Q5 individuation — without multiple chain types, structural distance is undefined.

**Component 2: Between-run chain distance exceeds within-run distance.**
Pairwise edit distance over link-type sequences. Pre-registered direction: between-run mean distance > within-run mean distance. If chains for the same object class show the same link-type sequence across all runs (as in v1.11), this finding is absent. If GREEN family chains produce a structurally different sequence from YELLOW chains — for example, if `att_green` mastery is in Phase 1 for some agents and not others, producing variable `phase1_absence` link presence — structural individuation emerges.

**Component 3: Phase 1 absence link variability.**
The v1.11 finding was that the `phase1_absence` link fired in all 22 chains — `att_yellow` was consistently absent from Phase 1. The v1.12 prediction: at 500,000 steps with a richer developmental record, some agents may achieve `att_yellow` mastery within Phase 1 in some runs (Phase 1 ends at step 515; mastery at step 518 in many v1.11 runs is within 3 steps). If any agents master `att_yellow` before Phase 1 ends, those chains will lack the `phase1_absence` link, producing structural variation across chains.

Category ζ: Component 1 is a prerequisite. Components 2 and 3 are the substantive individuation findings.

### 4.5 Category γ: Biographical individuation extended to Q5

Q5 individuation is assessed as a derived property: whether agents with distinct Q1–Q4 developmental arcs produce structurally distinct causal chains. The pre-registered direction is positive — the individuation of Q5 is bounded below by the individuation of its inputs. Assessed using the chain structural distance metric (Section 2.3).

---

## 5. Pre-registered predictions

1. **Completion rate ≥50%.** The 500,000-step window produces ≥20/40 runs banking the end state.
2. **env2_activation_step < env1_activation_step.** Agents complete the developmental sequence faster in Environment 2 than Environment 1 across all runs where both are measurable.
3. **Yellow resolution window eliminated in all env2 runs.** Consistent with v1.11.
4. **Green family chains present in ≥5 runs.** At 500,000 steps, GREEN family resolved surprises appear in the batch.
5. **Q5 structural individuation present.** At least one run produces chains for both object classes; between-run mean chain distance exceeds within-run mean distance.
6. **Zero hallucinations across all Q1–Q5 outputs.** Category α holds at 500,000 steps and for GREEN family chains.
7. **Category δ stable.** Mean approach_delta remains positive across all revised-expectation records; the 957.0 value from v1.11 is the baseline.

---

## 6. SICC commitment being operationalised

**Commitment 5 (time as a first-class property).** The SICC specifies that time is not a boundary condition imposed on development but a dimension the agent inhabits. The 320,000-step window was a practical constraint; extending it to 500,000 is the programme's first explicit treatment of time as something the agent is given rather than something the experiment restricts. The completion rate finding at v1.12 — whether it rises to ≥50% or whether the ceiling persists — is the empirical test of whether the developmental sequence has a natural timescale that the prior window was truncating, or whether the sequence itself is longer than any single observation window will comfortably contain.

**Commitment 5 across episodes.** The causal chain that spans environments — *I was less surprised in Environment 2 because I had been surprised in the same way in Environment 1* — is the SICC v0.7 formulation of inter-episode developmental time. v1.12 is the first iteration where this chain can be constructed: the agent that carried a resolved-surprise record from Environment 1 into Environment 2 and eliminated the surprise can now, via the causal observer, produce a statement of the form *I was not surprised at haz_yellow in Environment 2 because I had already understood its precondition in Environment 1.* This is Commitment 5 at its most concrete: developmental time is not reset at environment boundaries. What was learned in one episode is available in the next.

---

## 7. Open questions resolved at pre-registration

**1. Seed source.** `run_data_v1_11.csv` is the primary seed source. Fallback: `run_data_v1_10_1.csv`. The seed format is confirmed compatible from v1.11.

**2. Step count.** 500,000 per environment. Pre-registered here; not a free parameter.

**3. env2 activation reset.** `agent.activation_step = None` and `agent.end_state_banked = False` at start of Environment 2. `env2_activation_step` tracked independently.

**4. Q5 individuation metric.** Edit distance over ordered link-type sequences, normalised to [0,1]. Applied pairwise. Reported as within-run and between-run means. Committed here.

**5. No new observer.** The architecture is complete for v1.12's empirical questions. A new observer introduced at v1.12 would be a violation of the single-variable discipline — the step count extension is the variable; any architectural addition is a separate iteration.

---

## 8. Amendment budget strategy

Three amendments available. Most likely candidates: (1) GREEN family chain construction — if `att_green` mastery key differs from expected `mastery:att_green` format in provenance, the causal observer will truncate GREEN chains at `LINK_PRECONDITION`; a one-line fix if confirmed by the Level-13 re-run. (2) Seed key format differences between `run_data_v1_11.csv` and the batch runner's expected format. (3) env2 activation reset — if resetting `agent.activation_step` to None causes unexpected behaviour in V17Agent's phase schedule, a targeted patch may be needed.

The diagnostic-first protocol applies: before any code change, confirm the interface by inspection. The v1.11 lesson holds.

---

## 9. Stopping rule

v1.12 completes when:
- Level-12 re-run passes at 500,000 steps with `--no-causal`.
- Level-13 re-run passes at 500,000 steps.
- The full 40-run batch has run.
- Categories α, β, δ, θ, Λ (Components 1 and 2), ζ, and γ have been characterised.
- The v1.12 paper is drafted.

---

## 10. New files required

- `curiosity_agent_v1_12_batch.py` — batch runner with 500,000-step window, env2 activation counter reset, Q5 individuation analysis, extended env2 output fields
- `v1_12_carry_forward.md` — session carry-forward note

No new observer files. No new substrate files. The v1.11 stack is the v1.12 stack; the batch runner is the only file that changes.

---

## 11. References

Baker, N.P.M. (2026au) 'v1.11 Pre-Registration: Causal Self-Explanation and the Next-Environment Architecture', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026av) 'v1.11.1 Post-Batch Amendment: Phase1 Absence Link and Env2 Yellow Field', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aw) 'Causal Self-Explanation in a Small Artificial Learner: The Record of Understanding Why', preprint, 4 May 2026.

Baker, N.P.M. (2026ax) 'v1.12 Pre-Registration: Multi-Environment Developmental Transfer', GitHub repository, 4 May 2026.

Baker, N.P.M. (internal record, v0.7 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Vygotsky, L.S. (1978) *Mind in Society: The Development of Higher Psychological Processes*. Cambridge, MA: Harvard University Press.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
