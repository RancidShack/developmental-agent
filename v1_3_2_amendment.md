# v1.3.2 Pre-Registration Amendment

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 2 May 2026
**Status:** Amendment to v1.3 Pre-Registration, committed before v1.3.2 batch runs
**Repository:** github.com/RancidShack/developmental-agent
**Amends:** v1.3 Pre-Registration (Baker, 2026w) and v1.3.1 Amendment (Baker, 2026x)
**Amendment number:** 2 of 3 available

---

## Purpose of this amendment

The v1.3.1 batch (240 runs, four run lengths including 320,000 steps) revealed that the core architectural claim of v1.3 — that mastery at the 2D acquirable tier is the earned precondition for access at the 3D bankable tier — is semantically declared in the provenance records but mechanically violated by the v0.14 competency-gating architecture.

The violation is specific and diagnosable. The v0.14 `check_competency_unlocks` method gates each hazard cell's HAZARD-to-KNOWLEDGE transition on `current_competency = sum(self.mastery_flag.values())` — the total count of all mastery flags set, regardless of which attractors were mastered. For family-attributed hazard cells, this means any attractor mastered anywhere in the environment can unlock a family's bankable tier, without the corresponding family attractor having been mastered at all.

The v1.3.1 batch quantifies this precisely. At 320,000 steps: 42 of 60 yellow pyramid unlocks occurred before the yellow triangle was mastered; at threshold=1, all 13 agents with that threshold value unlocked the yellow pyramid on their first attractor mastery of any kind. The green family is less affected (better spatial separation, higher threshold distribution) but structurally identical in mechanism — the correct ordering in the green results is partly accidental rather than enforced.

The Category Ω claim in the pre-registration states: "mastery at the 2D tier is the earned precondition for access at the 3D tier." The v1.3.1 batch demonstrates this claim is not mechanically true under the v0.14 competency architecture. The paper cannot make this claim honestly against v1.3.1 data.

This amendment introduces **family-specific competency gating** as the correction. The fix is the minimum change that makes the architectural claim true: for family-attributed hazard cells, the transition condition is replaced by the specific mastery of the corresponding family attractor, not global competency accumulation. For unaffiliated hazard cells, the global competency mechanism is unchanged.

This is the first amendment in the v1.3 arc that modifies agent behaviour. All prior amendments (schema observer correction, 320k run length extension, Category γ metric specification) were observer-layer or methodological changes that preserved byte-identical agent behaviour. This amendment does not. The preservation characterisation for v1.3.2 is therefore different from v1.3.1: byte-identical comparison against v1.3.1 is not expected and not the claim. The claim is internal consistency and correct family ordering.

---

## Amendment: Family-specific competency gating

### The rule

For family-attributed hazard cells, the HAZARD-to-KNOWLEDGE transition fires when and only when the corresponding family attractor has been mastered — that is, when the mastery flag for the family's acquirable-tier attractor is set to 1.

Formally, for each family hazard cell `h` with family precondition attractor `a`:

```
transition fires when: self.mastery_flag.get(a, 0) == 1
```

The global competency threshold (`hazard_competency_thresholds[h]`) is **not consulted** for family-attributed cells. The threshold slot is preserved in the architecture — it exists in the world object, is written to the schema, and is recorded in the per-run metrics — but it does not govern the transition for family cells under this rule. This is noted explicitly so that future iterations may reinstate threshold-plus-family-gate logic if the design warrants it.

For unaffiliated hazard cells, the global competency mechanism is unchanged: transition fires when `sum(self.mastery_flag.values()) >= threshold`.

### Implementation

The family precondition map is passed to the agent at construction time via the world object's `family_precondition_attractor` dict, populated by `V13World` at initialisation:

```python
# In V13World.__init__:
self.family_precondition_attractor = {
    (14, 14): (4, 15),   # green sphere ← green square
    (5, 8):   (16, 3),   # yellow pyramid ← yellow triangle
}
```

A `V13Agent` subclass of `V12Agent` overrides `check_competency_unlocks` to apply the family-specific rule for family cells and the global rule for all others. No other method is overridden.

```python
def check_competency_unlocks(self, step):
    current_competency = sum(self.mastery_flag.values())
    family_preconditions = getattr(
        self.world, 'family_precondition_attractor', {}
    )
    for cell in sorted(self.world.hazard_cells):
        if self.world.knowledge_unlocked.get(cell, False):
            continue
        precondition_attractor = family_preconditions.get(cell)
        if precondition_attractor is not None:
            # Family cell: gate on specific attractor mastery only.
            if self.mastery_flag.get(precondition_attractor, 0) == 1:
                self.world.transition_hazard_to_knowledge(cell)
                self.competency_unlock_step[cell] = step
                self.transition_order_sequence.append(cell)
                if self.time_to_first_transition is None:
                    self.time_to_first_transition = step
                self.time_to_final_transition = step
        else:
            # Unaffiliated cell: global competency gate unchanged.
            threshold = self.hazard_competency_thresholds.get(cell)
            if threshold is None:
                continue
            if current_competency >= threshold:
                self.world.transition_hazard_to_knowledge(cell)
                self.competency_unlock_step[cell] = step
                self.transition_order_sequence.append(cell)
                if self.time_to_first_transition is None:
                    self.time_to_first_transition = step
                self.time_to_final_transition = step
```

### What this does not change

The threshold permutation for family hazard cells is preserved in the world object and schema. It is recorded in `hazard_thresholds` in the per-run CSV. It is not consulted during the run for family cells but remains available for inspection, and for future iterations that may combine family gating with a threshold floor.

The knowledge-banking mechanism is unchanged. The agent still requires `KNOWLEDGE_THRESHOLD` entries to a knowledge cell before banking it. The family gate controls when the hazard transitions to knowledge; what happens after transition is inherited from v0.14 unchanged.

The four unaffiliated hazard cells — (5,9), (6,8), (14,13), and the end-state hazard cluster — retain global competency gating exactly as in v0.14.

### Preservation characterisation

Because `check_competency_unlocks` is overridden, v1.3.2 agent behaviour is not byte-identical to v1.3.1 at matched seeds. The `--no-family` configuration (V12World shim, no family observer) no longer applies as a byte-identical regression test against v1.3.1, because the agent itself has changed.

The pre-flight verification for v1.3.2 is therefore reformulated:

**Level 4 (v1.3.2 internal consistency).** With all observers enabled and V13World, verify that in all 10 pre-flight runs: (a) no family hazard cell transitions before its precondition attractor is mastered; (b) unaffiliated hazard cells transition at global competency thresholds as before. This replaces the byte-identical baseline comparison as the Category α pre-condition for family cells.

Levels 1–3 (v0.14, v1.0, v1.1 baselines) are unaffected and continue to apply with the `--no-instrument`, `--no-provenance`, `--no-schema` flags in combination with a V12World shim and V12Agent (not V13Agent), confirming that the observer stack below the agent change is clean.

### Experimental matrix

Unchanged from v1.3.1: 240 runs, four run lengths (20,000 / 80,000 / 160,000 / 320,000), six cost levels, ten runs per cell. Seeds loaded from `run_data_v1_2.csv` with 160k fallback for 320k runs.

---

## Impact on pre-registration sections

**Section 2.5 (Intra-family competency gate):** The gating mechanism is amended. The global competency threshold is replaced by family-specific attractor mastery as the transition condition for family hazard cells. The threshold slot is preserved but not consulted for family cells.

**Section 6.2 (Category β):** Add verification condition: no family hazard cell transitions before its precondition attractor is mastered, in all 240 runs.

**Section 6.4 (Category δ):** The second pre-anticipated finding (cross-reference completion bounded by run length) is reinstated in its original form. With family-specific gating, the yellow pyramid cannot unlock before the yellow triangle is mastered, so the KB-before-mastery anomaly is eliminated by construction. Remaining Category δ findings are unchanged.

**Section 6.6 (Category Ω):** The architectural claim is now mechanically enforced rather than only semantically declared. The v1.3.2 batch is the evidential basis for the Category Ω claim.

---

## Paper treatment of v1.3.1 findings

The v1.3 paper will report the v1.3.1 batch findings honestly as the diagnostic record that motivated this amendment. The paper's results section presents the v1.3.2 corrected batch as the operative findings. The v1.3.1 anomaly — global competency gating permitting family hazard cells to unlock before the precondition attractor was mastered — is named as an architectural gap identified during the batch process and corrected before the paper's claims are made. This follows the same pattern established for the schema observer correction (Amendment 1) and is consistent with the programme's commitment to surfacing and resolving errors rather than reporting around them.

The threshold slot's preservation is noted in the paper's limits section as an architectural decision: the slot exists, was not consulted under the v1.3.2 rule, and is available for future iterations that may wish to combine family-specific gating with a competency floor.

---

## Implementation files

- `curiosity_agent_v1_3_world.py` — add `family_precondition_attractor` dict to `V13World.__init__`
- `v1_3_agent.py` — new file: `V13Agent` subclassing `V12Agent`, overrides `check_competency_unlocks`
- `curiosity_agent_v1_3_batch.py` — import `V13Agent` from `v1_3_agent.py` instead of `v1_3_schema_extension.py`; update level-4 verification logic
- `verify_v1_3_no_family.py` — update pre-flight to use internal-consistency check rather than byte-identical baseline comparison for family cells

All files committed before the v1.3.2 batch runs.

---

## References

Baker, N.P.M. (2026w) 'v1.3 Pre-Registration: Relational Property Families via Colour-and-Form Taxonomy in a Prepared Environment', GitHub repository, 1 May 2026.

Baker, N.P.M. (2026x) 'v1.3.1 Pre-Registration Amendment: Schema Observer Correction, Extended Run Length, and Category γ Metric Specification', GitHub repository, 2 May 2026.

Baker, N.P.M. (2026y) 'v1.3.2 Pre-Registration Amendment: Family-Specific Competency Gating', GitHub repository, 2 May 2026.

---

**Amendment commitment:** This document is committed to the public repository at github.com/RancidShack/developmental-agent on 2 May 2026, before the v1.3.2 batch runs.
