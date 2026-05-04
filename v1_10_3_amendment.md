# v1.10.3 Pre-Registration Amendment: ProvenanceRecord Dataclass Required

**Date:** 4 May 2026
**Iteration:** v1.10
**Amendment number:** 3 of 3 — final amendment
**Trigger:** Level-11 re-run failure on runs 8 and 9 (third pass)

---

## 1. What failed

After v1.10.2 correction, Level-11 re-run failed again on runs 8 and 9:

```
AttributeError: 'dict' object has no attribute 'flag_type'
```

Two call sites:
- `v1_1_provenance.py`, line 404, `_record_phase_boundary_confirmations`:
  `if record.flag_type != "threat":`
- `v1_1_provenance.py`, line 479, `_emit_snapshot`:
  `"flag_type": record.flag_type`

Runs 0–7 passed cleanly on all three passes.
C6 and C7 both PASS throughout (mean CF=151.6).

---

## 2. Diagnosis

`V1ProvenanceStore.records` is typed `Dict[str, ProvenanceRecord]`
where `ProvenanceRecord` is a dataclass defined in `v1_1_provenance.py`.
The store's own methods — `_record_phase_boundary_confirmations` and
`_emit_snapshot` — iterate over `self.records.items()` and access
`.flag_type` as a dataclass attribute.

The `on_end_state_banked` hook was storing a raw dict. A dict does not
have a `.flag_type` attribute; attribute access on a dict raises
`AttributeError`. The v1.10.2 fix corrected `self.flags` → `self.records`
but did not correct the dict → ProvenanceRecord issue.

---

## 3. Change

In `v1_10_observer_substrates.py`, `on_end_state_banked()`:

The raw dict is replaced with a `ProvenanceRecord` dataclass instance.
`steps_since_activation` is encoded in `confirming_observations` — the
only spare integer field on the dataclass — since the dataclass schema
does not include custom fields. The full `steps_since_activation` value
is independently held in the `end_state_draw_log_v1_10.csv` output.

```python
# After (correct)
from v1_1_provenance import ProvenanceRecord

flag_id = "environment_complete:end_state"
rec = ProvenanceRecord(
    flag_type="environment_complete",
    flag_coord=None,
    flag_id=flag_id,
    flag_set_step=step,
    confirming_observations=steps_since,   # encodes steps_since_activation
    last_observation_step=step,
)
self.records[flag_id] = rec
```

---

## 4. Amendment budget exhausted

This is amendment 3 of 3. The amendment budget is now exhausted.
If Level-11 re-run fails again, the iteration must be reset and the
`on_end_state_banked` hook redesigned before re-pre-registration.

If Level-11 passes, Level-12 proceeds. No further amendments are
available for v1.10.
