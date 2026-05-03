"""
v1_6_observer_substrates.py
-----------------------------
v1.6 additive patch: adds get_substrate() to each of the five observers
that hold state the reporting layer reads from.

ARCHITECTURE PRINCIPLE
This module monkey-patches get_substrate() onto the five observer classes
at import time. No existing method is modified. The patch is applied by
importing this module in the v1.6 batch runner before any observer is
instantiated. The observers remain byte-for-byte identical in their
run-loop behaviour; get_substrate() is a read-only accessor that does
not alter observer state.

This approach preserves the observers as they exist in the inheritance
chain — no copies, no subclasses — while adding the v1.6 interface.
Each get_substrate() must be called after on_run_end() has fired.

SUBSTRATE CONTRACTS (defined in v1_6_substrate_bundle.py)
  V1ProvenanceStore.get_substrate()
    -> Dict[str, ProvenanceSubstrateRecord]
       keyed by flag_id; all provenance records for this run.

  V13SchemaObserver.get_substrate()
    -> Dict[str, Any] | None
       flat dict of schema fields (the observer's _row), or None.

  V13FamilyObserver.get_substrate()
    -> Dict[str, Any] | None
       flat dict from full_record(), or None if no traversal events.

  V14ComparisonObserver.get_substrate()
    -> Dict[str, Any] | None
       flat dict (_row), or None if comparison was not computed.

  V15PredictionErrorObserver.get_substrate()
    -> List[Dict[str, Any]]
       list of per-encounter dicts; empty list if no encounters.
"""

from v1_1_provenance import V1ProvenanceStore, ProvenanceRecord
from v1_3_schema_extension import V13SchemaObserver
from v1_3_family_observer import V13FamilyObserver
from v1_4_comparison_observer import V14ComparisonObserver
from v1_5_prediction_error_observer import V15PredictionErrorObserver

from v1_6_substrate_bundle import ProvenanceSubstrateRecord


# ---------------------------------------------------------------------------
# V1ProvenanceStore.get_substrate()
# ---------------------------------------------------------------------------

def _provenance_get_substrate(self):
    """Return the provenance records as a substrate dict.

    Converts ProvenanceRecord dataclass instances to
    ProvenanceSubstrateRecord instances, preserving all fields.
    flag_coord is serialised to string (or None) so the substrate
    carries no grid-specific coordinate type.

    Must be called after on_run_end().
    """
    result = {}
    for flag_id, record in self.records.items():
        coord = record.flag_coord
        if coord is not None:
            coord_str = str(coord)
        else:
            coord_str = None

        result[flag_id] = ProvenanceSubstrateRecord(
            flag_type=record.flag_type,
            flag_coord_str=coord_str,
            flag_id=record.flag_id,
            flag_set_step=record.flag_set_step,
            confirming_observations=record.confirming_observations,
            disconfirming_observations=record.disconfirming_observations,
            last_confirmation_step=record.last_confirmation_step,
            last_observation_step=record.last_observation_step,
            transformed_at_step=record.transformed_at_step,
            derived_knowledge_flag_id=record.derived_knowledge_flag_id,
            derived_from_threat_flag_id=record.derived_from_threat_flag_id,
        )
    return result


V1ProvenanceStore.get_substrate = _provenance_get_substrate


# ---------------------------------------------------------------------------
# V13SchemaObserver.get_substrate()
# ---------------------------------------------------------------------------

def _schema_get_substrate(self):
    """Return the schema row as a flat dict, or None.

    Returns a copy of self._row. Must be called after on_run_end().
    """
    if self._row is None:
        return None
    return dict(self._row)


V13SchemaObserver.get_substrate = _schema_get_substrate


# ---------------------------------------------------------------------------
# V13FamilyObserver.get_substrate()
# ---------------------------------------------------------------------------

def _family_get_substrate(self):
    """Return the full family record as a flat dict, or None.

    Calls full_record(), which includes all summary fields plus the
    per-family coordinate strings, colour, form, crossref, and the
    family_traversal_narrative. Returns None if no traversal events
    were recorded (empty run).

    Must be called after on_run_end().
    """
    if not self._traversal_events and not any(
        self._colour_registered.values()
    ):
        return None
    try:
        return self.full_record()
    except Exception:
        return None


V13FamilyObserver.get_substrate = _family_get_substrate


# ---------------------------------------------------------------------------
# V14ComparisonObserver.get_substrate()
# ---------------------------------------------------------------------------

def _comparison_get_substrate(self):
    """Return the comparison row as a flat dict, or None.

    Returns a copy of self._row. Must be called after on_run_end().
    Returns None if on_run_end did not produce a row (e.g. family
    traversal incomplete at run end).
    """
    if self._row is None:
        return None
    return dict(self._row)


V14ComparisonObserver.get_substrate = _comparison_get_substrate


# ---------------------------------------------------------------------------
# V15PredictionErrorObserver.get_substrate()
# ---------------------------------------------------------------------------

def _prediction_error_get_substrate(self):
    """Return the per-encounter records as a list of dicts.

    Returns a copy of self._encounter_records. Must be called after
    on_run_end(). Returns empty list if no encounters were recorded.
    """
    if not hasattr(self, "_encounter_records"):
        return []
    return [dict(r) for r in self._encounter_records]


V15PredictionErrorObserver.get_substrate = _prediction_error_get_substrate
