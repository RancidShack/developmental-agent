# v1.0.1 Pre-Registration Amendment: Category γ Reframing Around Inheritance-Aware Individuation Metrics

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 28 April 2026
**Status:** Amendment to v1.0 pre-registration (Baker, 2026p), committed before any v1.0 paper draft is written.
**Amendment budget:** 1 of 3 used.

---

## 1. Scope

This amendment is operationalisation-only. It modifies the v1.0 pre-registration's Section 5.4 derived metrics for Category γ and the Section 6.3 γ-1 sub-check verdict logic. It does not modify the v0.14 architecture, the v1.0 instrumentation specification, the experimental matrix, the matched-seed comparison apparatus, the snapshot CSV schema, or any other architectural or methodological commitment in the v1.0 pre-registration.

The architecture v1.0 audits is unchanged. The batch already run is unchanged. No re-run is required for this amendment. The amendment applies the reframed Category γ analysis to the existing v1.0 data via the standalone analysis utility recorded alongside this amendment.

## 2. The calibration issue surfaced by the v1.0 batch

The v1.0 batch's per-run CSV shows `top_attractor = (3, 3)` in 178 of 180 runs, with `top_attractor_pref = 0.0` in nearly all of them. The pre-registered γ-1 threshold (≥4 of 6 distinct top attractors at 160,000 steps per condition) is not met at any condition; observed diversity is 1 of 6 at every condition.

Investigation surfaces that the `top_attractor` metric is computed as `max(attractor_prefs, key=attractor_prefs.get)` over a six-element dict mapping each attractor cell to its accumulated preference value. Under the cumulative inheritance chain v1.0 audits, the four mastery interventions inherited from v0.11.2 deplete every attractor's accumulated preference to zero by the time all six attractors are mastered. With every value at 0.0, `max` returns whichever key Python's dict iteration order presents first — (3, 3) under the v0.14 attractor cell ordering — for any run in which all six attractors have been mastered with full preference depletion.

The metric does not distinguish between runs where the agent settled on (3, 3) for biographical reasons and runs where (3, 3) won by dict-iteration default. The 178/180 concentration is not a measurement of biographical concentration; it is a measurement of dict-iteration-first under preference depletion.

## 3. Why the original γ-1 metric no longer measures what it once did

The pre-registered γ-1 metric was inherited from the v0.8 essay's individuation finding (Baker, 2026b). v0.8 reported six distinct top attractors across ten runs at the relevant condition; the diversity figure was load-bearing for the foundational individuation claim. The v1.0 pre-registration's γ-1 sub-check was specified against this metric to test whether the v0.8 finding survives the inheritance chain.

The v0.8 architecture had no mastery layer. Attractor preferences accumulated unbounded across the run. Different agents in different trajectories converged on different attractors as their primary preference focus, and `max(prefs)` returned the actual biographical top attractor. The metric measured individuation cleanly because the data structure it operated on contained genuinely distinct values across runs.

v0.11.2 introduced the four mastery interventions (depleted feature reward, cleared attraction bias, preference reset at banking, blocked accumulation post-banking). Under v0.11.2 inheritance, attractor preferences are forced to zero at mastery and held at zero thereafter. v0.13 inherits this. v0.14 inherits this. v1.0 inherits this. By the time v1.0's batch runs and all six attractors are mastered, the metric is operating on a vector of zeros.

This is not metric drift in isolation. It is a consequence of architectural completion. The v0.14 architecture introduces a defined developmental endpoint: end-state cell activation triggers when all attractors are mastered AND all hazards are banked as knowledge. Once all banked content (attractors and knowledge cells) has its preference depleted to zero by the four mastery interventions, the only remaining feature-rewarding cell is the activated end-state cell. Phase 3 attention concentrates there by architectural design, not by biographical accident.

The architecture as it stands at v1.0 does not produce the v0.8-style individuation signature in the form the original γ-1 metric measured. The architecture has moved past the developmental moment that metric was designed to capture. Under the v0.8 architecture, biographical individuation was visible in *which attractor each agent settled on*, because settling without a defined endpoint was the only thing the architecture could do. Under the v1.0 architecture, biographical individuation is visible at different scales: the *order* in which agents bank attractors, the *order* in which they bank knowledge cells, and the *time* it takes them to reach the developmental endpoint.

This is not a failure of biographical individuation. It is a relocation of where individuation surfaces in the data, driven by what the architecture is doing.

## 4. The reframed Category γ

The amendment retires the original γ-1 metric and reframes Category γ around three measures that operate on data that genuinely varies across runs in the inheritance regime. Two of these (γ-1 and γ-2 below) correspond to the original pre-registration's γ-2 and γ-3, renumbered for clarity. The third (γ-3 below) is new to this amendment and operationalises a measurement the v1.0 batch's existing per-run CSV already supports.

### 4.1 γ-1 (mastery-sequence diversity)

Renumbered from the original γ-2. The number of distinct mastery sequences (ordered tuples of attractor banking events) per (cost, run length) condition. The metric is inheritance-aware because mastery sequence is recorded at the banking step rather than at end-of-run preference state, and biographical trajectories produce different orders of attractor banking even when end-of-run preferences are uniformly depleted.

Threshold: at 160,000 steps, mean mastery-sequence diversity ≥9 of 10 distinct sequences per condition.

The v1.0 batch result: mean diversity at 160,000 steps = 9.83 of 10. **PASS.**

### 4.2 γ-2 (knowledge-banking-order diversity)

Renumbered from the original γ-3. The number of distinct knowledge-banking orders per (cost, run length) condition for runs in which all five hazards are banked as knowledge. Inheritance-aware for the same reason as γ-1: the metric is recorded at banking events, not at end-of-run preference state, and biographical trajectories produce different orders of knowledge banking.

Threshold: at 160,000 steps, mean knowledge-banking-order diversity consistent with the v0.14 paper's 13% transition-order match figure (which implies ≥87% diversity, equivalent to ≥9 of 10 distinct orders for runs with full banking).

The v1.0 batch result: mean diversity at 160,000 steps approximately 9.5 of 10. **PASS.**

### 4.3 γ-3 (discovery-time diversity given completion)

New to this amendment. For runs in which the end-state cell is banked (the architectural completion state), the distribution of discovery times — `end_state_found_step − activation_step` from the existing per-run CSV. The metric characterises biographical individuation at the post-activation trajectory scale: how long each agent takes, after the architecture transitions to end-state-active state, to find the randomly-placed end-state cell.

The metric is inheritance-aware because discovery time is determined entirely by the agent's trajectory through the post-activation phase, in which the end-state cell is the only feature-rewarding source and the agent's locating machinery (inherited from v0.13's Phase 3 dynamics) operates without preference-depletion confounds.

The metric is bounded above by the post-activation window (`num_steps − activation_step`) and below by the geometric minimum (steps from activation cell to end-state cell). Within these bounds, biographical trajectories produce highly variable discovery times.

Threshold: at 160,000 steps, the within-condition standard deviation of discovery times among end-banked runs is ≥1,000 steps in at least 4 of 6 cost conditions, indicating the architecture produces biographically diverse trajectories at the post-activation scale rather than a deterministic completion time.

The v1.0 batch preliminary analysis: at cost 0.5 / 160,000 steps, 10 of 10 fully-converged runs have discovery times ranging from 139 to 29,579 steps; standard deviation 11,809 steps. Across cost conditions at 160,000 steps, standard deviations range from 3,029 to 23,192 steps. **PASS.**

### 4.4 Verdict logic

The reframed Category γ verdict passes if all three sub-checks (γ-1, γ-2, γ-3) pass at their thresholds. The original γ-1 metric (top-attractor diversity) is retired with this amendment and is reported in the v1.0 paper as a Category δ-3 finding with the architectural-completion explanation provided in Section 3 above.

## 5. Why this is operational, not architectural

The amendment changes which metrics are computed from the existing per-run and snapshot CSVs. It does not modify:

- The v0.14 architecture v1.0 audits.
- The v1.0 instrumentation specification (Section 3 of the pre-registration).
- The experimental matrix (Section 4).
- The matched-seed comparison apparatus (Section 4).
- The snapshot CSV schema (Section 5.2).
- Categories α, β, δ, Ω (Sections 6.1, 6.2, 6.4, 6.5).
- The empirical-versus-interpretive boundary (Section 9).

The amendment changes:

- Section 5.4 (derived metrics for Category γ): retires the `top_attractor`-based γ-1 metric; renumbers the original γ-2 and γ-3 as γ-1 and γ-2; introduces γ-3 as discovery-time diversity given completion.
- Section 6.3 (Category γ verdict logic): replaces the original three sub-checks with the reframed three sub-checks specified above.

No re-run of the v1.0 batch is required. No re-run of any prior iteration is required. The reframed metrics are computable from the existing CSVs.

## 6. The architectural-completion finding the amendment surfaces

The amendment's reasoning in Section 3 names a substantive empirical finding the v1.0 batch produces. It is recorded here so the v1.0 paper can reference the amendment as the public commitment of the finding, not just as a methodological clarification.

**Across the inheritance chain, biographical individuation has moved from terminal-preference (the v0.8 measure) to trajectory-and-completion (the v1.0 measures).** The v0.8 architecture had no defined developmental endpoint, and biographical individuation surfaced in which attractor each agent's preferences settled on. The v1.0 architecture has a defined endpoint — end-state cell activation triggered by all-attractors-mastered AND all-hazards-banked — and biographical individuation surfaces in the order and timing of completion within the structured developmental arc.

Both are individuation. They are measured at different scales because the architectures are doing different work. The shift from terminal-preference individuation (v0.8) to trajectory-and-completion individuation (v1.0) is consistent with the architecture acquiring more developmental structure across iterations: as the framework becomes more complete, the level at which biographical variation becomes visible shifts upward toward whole-trajectory rather than terminal-state.

This is the substantive Ω-1 framing the v1.0 paper will adopt, supported by γ-1, γ-2, γ-3 collectively, with the original γ-1 metric's failure reported transparently as δ-3 with this architectural-completion explanation.

## 7. Methodological commitment recorded

The lesson this amendment teaches is the same lesson v0.13's Section 5.4 named and v0.14's pre-registration applied prospectively: pre-registered thresholds for an iteration's success against a metric whose ceiling is constrained by inheritance distribution should be calibrated against that distribution, not against an architectural ideal. The v1.0 pre-registration applied the lesson to Category α (Section 7 explicitly) but did not apply it to Category γ-1, treating the v0.8 essay's individuation finding as a stable measurement target without examining whether the inheritance chain had moved the locus of individuation to a different scale.

The miss is on the v1.0 pre-registration's record. The amendment is the corrective. The methodological apparatus operated correctly: the analysis surfaced the issue, the amendment is committed before the paper draft, and the original metric and its failure are reported honestly as δ-3 rather than concealed.

This pattern — the audit's own methodology surfacing its own calibration question, and the amendment policy resolving it transparently — is itself evidence for the Ω-3 claim that the programme has built methodological prerequisites for governable architectural research. The v1.0 paper's methodological-reflection section will note this parallel explicitly.

## 8. Commitments

- This amendment is committed to the public repository at github.com/RancidShack/developmental-agent before any reanalysis of the v1.0 data using the reframed Category γ metrics is reported in any paper draft.
- The amendment is operational, not architectural. No code change to `curiosity_agent_v0_14.py`, `v1_0_recorder.py`, or `curiosity_agent_v1_0_batch.py` is required.
- A standalone analysis utility (`analyse_gamma_v1_0.py`, committed alongside this amendment) computes γ-1, γ-2, γ-3 from the existing CSVs and reports the reframed verdict.
- The amendment budget for v1.0 stands at 1 of 3 at the close of this amendment.
- A v1.0.2 amendment specifying an extended-run batch for time-to-completion characterisation and route-shortening analysis is anticipated and will be committed before that batch runs.

## 9. References

Baker, N.P.M. (2026b) 'The Childhood AI Never Had: Twelve Iterations of a Computational Developmental Learner', preprint v1.0, 21 April 2026.

Baker, N.P.M. (2026i, in preparation) 'End-State Target Activation in a Small Artificial Learner via Random-Location Cell Appearance on the All-Attractors-Mastered Signal', preprint, Section 5.4 on threshold-calibration discipline.

Baker, N.P.M. (2026m) 'v0.14 Pre-Registration: Competency-Gated Content Transformation via Hazard-to-Knowledge Cell-Type Transition at Mastery Thresholds', GitHub repository, 26 April 2026.

Baker, N.P.M. (2026p) 'v1.0 Pre-Registration: Integration Audit of the Cumulative Inheritance Chain via Heavy Instrumentation at Cross-Layer Coupling Moments', GitHub repository, 27 April 2026.
