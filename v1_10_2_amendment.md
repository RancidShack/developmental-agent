# v1.10.2 Pre-Registration Amendment: ProvenanceStore Record Storage Attribute

**Date:** 4 May 2026
**Iteration:** v1.10
**Amendment number:** 2 of 3
**Trigger:** Level-11 re-run failure on runs 8 and 9 (second pass)

---

## 1. What failed

After v1.10.1 correction, Level-11 re-run failed again on runs 8 and 9:

```
AttributeError: 'V1ProvenanceStore' object has no attribute 'flags'
```

Traceback: `v1_10_observer_substrates.py`, line 304, in
`on_end_state_banked` — `self.flags[flag_id] = rec`

Runs 0–7 passed cleanly. C6 and C7 both PASS (mean CF=151.6).

---

## 2. Diagnosis

`V1ProvenanceStore` stores its provenance records in `self.records`
(a `Dict[str, ProvenanceRecord]`, initialised at line 180 of
`v1_1_provenance.py`). The `on_end_state_banked` hook incorrectly
referenced `self.flags`. v1.10.1 corrected the agent attribute name
but left this second incorrect reference in place.

---

## 3. Change

In `v1_10_observer_substrates.py`, `on_end_state_banked()`:

```python
# Before (incorrect)
self.flags[flag_id] = rec

# After (correct)
self.records[flag_id] = rec
```

No other changes.

---

## 4. Re-verification required

Level-11 re-run must pass in full before Level-12 proceeds.
Amendment budget remaining: **1 of 3**.
