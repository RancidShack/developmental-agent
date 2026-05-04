# v1.10.1 Pre-Registration Amendment: ProvenanceStore Agent Attribute

**Date:** 4 May 2026
**Iteration:** v1.10
**Amendment number:** 1 of 3
**Trigger:** Level-11 re-run failure, Runs 8 and 9

---

## 1. What failed

Level-11 re-run produced errors on Runs 8 and 9:

```
AttributeError: 'V1ProvenanceStore' object has no attribute '_agent'.
Did you mean: 'agent'?
```

Runs 0–7 passed cleanly (halluc=0, PASS). The error fired in
`on_end_state_banked()` when the end-state banking condition fired
in those two runs.

C6 (detection_fires) PASS: 1,516 CF records, mean 151.6/run.
C7 (temporal_exclusion_effective) PASS: mean < 500.

---

## 2. Diagnosis

`V1ProvenanceStore` stores the agent as `self.agent` (convention
established at v1.1). The `on_end_state_banked` hook used `self._agent`
— the private convention used by observers introduced from v1.5 onward.
Single attribute name mismatch; no architectural issue.

---

## 3. Change

In `v1_10_observer_substrates.py`, `on_end_state_banked()`:

```python
# Before
activation_step = getattr(self._agent, 'activation_step', None)
# After
activation_step = getattr(self.agent, 'activation_step', None)
```

No other change.

---

## 4. Re-verification required

Level-11 re-run must pass in full before Level-12.

Amendment budget remaining: **2 of 3**.
