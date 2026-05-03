"""
v1_6_substrate_bundle.py
-------------------------
SubstrateBundle: the substrate-agnostic data container that the v1.6
reporting layer reads from exclusively.

ARCHITECTURAL ROLE
The reporting layer (V16ReportingLayer) does not import observer classes,
reference grid coordinates directly, or read CSV files. It receives a
SubstrateBundle populated from the six observer outputs after on_run_end
has been called. Each observer exposes a get_substrate() method (added by
v1.6) that returns the observer's complete readable state as a typed dict.

This module defines:

  SubstrateBundle       — the container class. Holds six substrate dicts
                          plus run_meta. Has no knowledge of grid specifics.

  build_bundle_from_observers(...)
                        — populates a SubstrateBundle from live observer
                          instances at the end of a run. Called by the
                          batch runner after on_run_end has been called on
                          all observers.

  build_bundle_from_csvs(...)
                        — reconstructs a SubstrateBundle from stored CSV
                          data for a specific (run_idx, num_steps, seed).
                          Used by the v1.6 batch runner, which reads from
                          the v1.5 output files rather than re-running
                          the agent. Also used by verify_v1_6_substrate.py
                          (Level 7 pre-flight).

SUBSTRATE-AGNOSTICISM COMMITMENT (pre-registration §2.1)
The SubstrateBundle fields name cognitive-layer concepts — provenance
records, schema structure, family traversal, comparison measures,
prediction-error encounters — not grid-specific constructs. At v1.7,
when the tabular observers are replaced by richer-substrate observers,
those observers implement the same get_substrate() contract and populate
the same SubstrateBundle fields. The reporting layer carries forward
unchanged. This is verifiable by inspection: no field name in
SubstrateBundle references a grid-specific constant.

SUBSTRATE FIELD CONTRACTS
Each substrate field is a dict with a defined structure. The reporting
layer reads exclusively from these contracts; it must not assume any
structure beyond what is defined here.

  provenance:
    {flag_id: ProvenanceSubstrateRecord, ...}
    ProvenanceSubstrateRecord fields (all present, may be None):
      flag_type, flag_coord_str, flag_id, flag_set_step,
      confirming_observations, disconfirming_observations,
      last_confirmation_step, last_observation_step,
      transformed_at_step, derived_knowledge_flag_id,
      derived_from_threat_flag_id

  schema:
    Flat dict of schema fields as produced by V13SchemaObserver._row.
    Keys: arch, hazard_cost, num_steps, run_idx, seed, plus all
    ct_* and action_* and phase_* fields from the schema CSV.
    Key 'schema_complete' is always present.

  family:
    Flat dict of family fields as produced by V13FamilyObserver.full_record().
    Keys: arch, hazard_cost, num_steps, run_idx, seed, plus all
    green_* and yellow_* fields, family_traversal_narrative.

  comparison:
    Flat dict of comparison fields as produced by V14ComparisonObserver._row.
    Keys: arch, hazard_cost, num_steps, run_idx, seed,
    tier_structure_similarity, form_progression_parallelism,
    traversal_sequence_distance, green_traversal_complete,
    yellow_traversal_complete, both_complete, green_first,
    traversal_interleaving, cross_family_comparison_complete.
    May be None if comparison observer was not active.

  prediction_error:
    List of encounter dicts. Each dict has:
      arch, hazard_cost, num_steps, run_idx, seed,
      step, cell, family, precondition_met, cost_paid,
      transformed_at_step, resolution_window, encounter_type.
    Empty list if no encounters were recorded.

  run_meta:
    {arch, hazard_cost, num_steps, run_idx, seed}
"""

import csv
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# ProvenanceSubstrateRecord
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceSubstrateRecord:
    """Substrate-level representation of one provenance record.

    Field names match PROVENANCE_FIELDS from v1_1_provenance.py.
    All fields are present; grid-specific values (flag_coord) are
    preserved as strings rather than tuples so that the reporting layer
    does not depend on a grid-specific coordinate type.
    """
    flag_type:                   str
    flag_coord_str:              Optional[str]   # "(x, y)" or "" — string
    flag_id:                     str
    flag_set_step:               Optional[int]
    confirming_observations:     int             = 0
    disconfirming_observations:  int             = 0
    last_confirmation_step:      Optional[int]   = None
    last_observation_step:       Optional[int]   = None
    transformed_at_step:         Optional[int]   = None
    derived_knowledge_flag_id:   Optional[str]   = None
    derived_from_threat_flag_id: Optional[str]   = None


# ---------------------------------------------------------------------------
# SubstrateBundle
# ---------------------------------------------------------------------------

class SubstrateBundle:
    """Substrate-agnostic container for the six observer outputs.

    Populated either from live observer instances (build_bundle_from_observers)
    or from stored CSV data (build_bundle_from_csvs). The reporting layer
    reads exclusively from this container.

    Attributes
    ----------
    provenance : Dict[str, ProvenanceSubstrateRecord]
        Keyed by flag_id. All provenance records for this run.

    schema : Dict[str, Any]
        Flat dict of schema fields. Key 'schema_complete' always present.
        May be None if schema observer was not active.

    family : Dict[str, Any]
        Flat dict of family fields including family_traversal_narrative.
        May be None if family observer was not active.

    comparison : Dict[str, Any]
        Flat dict of comparison fields.
        May be None if comparison observer was not active.

    prediction_error : List[Dict[str, Any]]
        List of per-encounter dicts. Empty list if no encounters.

    run_meta : Dict[str, Any]
        {arch, hazard_cost, num_steps, run_idx, seed}
    """

    def __init__(
        self,
        provenance:       Dict[str, ProvenanceSubstrateRecord],
        schema:           Optional[Dict[str, Any]],
        family:           Optional[Dict[str, Any]],
        comparison:       Optional[Dict[str, Any]],
        prediction_error: List[Dict[str, Any]],
        run_meta:         Dict[str, Any],
    ):
        self.provenance       = provenance
        self.schema           = schema
        self.family           = family
        self.comparison       = comparison
        self.prediction_error = prediction_error
        self.run_meta         = run_meta

    def resolve(self, source_type: str, source_key: str) -> bool:
        """Return True if source_key resolves in source_type substrate.

        This is the traceability check used by the internal-consistency
        characterisation (Category α). A ReportStatement's source_key
        must resolve here for the statement to be grounded.

        source_type: one of "provenance", "schema", "family",
                     "comparison", "prediction_error", "run_meta"
        source_key:  the key within the named substrate.
        """
        if source_type == "provenance":
            return source_key in self.provenance
        if source_type == "schema":
            return (self.schema is not None
                    and source_key in self.schema)
        if source_type == "family":
            return (self.family is not None
                    and source_key in self.family)
        if source_type == "comparison":
            return (self.comparison is not None
                    and source_key in self.comparison)
        if source_type == "prediction_error":
            # source_key is "encounter:{idx}" — index into the list
            try:
                idx = int(source_key.split(":", 1)[1])
                return 0 <= idx < len(self.prediction_error)
            except (IndexError, ValueError):
                return False
        if source_type == "run_meta":
            return source_key in self.run_meta
        return False


# ---------------------------------------------------------------------------
# _coerce helpers
# ---------------------------------------------------------------------------

def _int_or_none(val) -> Optional[int]:
    if val is None or val == "" or val != val:  # last: NaN check
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def _str_or_none(val) -> Optional[str]:
    if val is None or val == "":
        return None
    return str(val)


# ---------------------------------------------------------------------------
# build_bundle_from_observers
# ---------------------------------------------------------------------------

def build_bundle_from_observers(
    provenance_obs,
    schema_obs,
    family_obs,
    comparison_obs,
    prediction_error_obs,
    run_meta: Dict[str, Any],
) -> SubstrateBundle:
    """Populate a SubstrateBundle from live observer instances.

    Called by the batch runner immediately after on_run_end has been
    called on all observers. Each observer's get_substrate() method
    returns its complete readable state.

    Observers may be None (if disabled for this run); the corresponding
    substrate field is set to None / empty list accordingly.
    """
    # Provenance
    prov_substrate: Dict[str, ProvenanceSubstrateRecord] = {}
    if provenance_obs is not None:
        prov_substrate = provenance_obs.get_substrate()

    # Schema
    schema_substrate = None
    if schema_obs is not None:
        schema_substrate = schema_obs.get_substrate()

    # Family
    family_substrate = None
    if family_obs is not None:
        family_substrate = family_obs.get_substrate()

    # Comparison
    comparison_substrate = None
    if comparison_obs is not None:
        comparison_substrate = comparison_obs.get_substrate()

    # Prediction-error
    pe_substrate: List[Dict[str, Any]] = []
    if prediction_error_obs is not None:
        pe_substrate = prediction_error_obs.get_substrate()

    return SubstrateBundle(
        provenance=prov_substrate,
        schema=schema_substrate,
        family=family_substrate,
        comparison=comparison_substrate,
        prediction_error=pe_substrate,
        run_meta=dict(run_meta),
    )


# ---------------------------------------------------------------------------
# build_bundle_from_csvs
# ---------------------------------------------------------------------------

def build_bundle_from_csvs(
    run_idx:    int,
    num_steps:  int,
    seed:       int,
    provenance_csv:       str,
    schema_csv:           str,
    family_csv:           str,
    comparison_csv:       str,
    prediction_error_csv: str,
    run_data_csv:         str,
) -> SubstrateBundle:
    """Reconstruct a SubstrateBundle from stored v1.5 CSV files.

    Used by the v1.6 batch runner (which reads stored data rather than
    re-running the agent) and by verify_v1_6_substrate.py (Level 7).

    Rows are matched by (run_idx, num_steps, seed). For prediction_error
    this produces multiple rows (one per encounter); for all others it
    produces one row per run.

    Returns a fully populated SubstrateBundle, or raises ValueError if
    the run cannot be found in the CSVs.
    """
    run_id_match = (
        lambda row: (
            str(row.get("run_idx")) == str(run_idx)
            and str(row.get("num_steps")) == str(num_steps)
            and str(row.get("seed")) == str(seed)
        )
    )

    # --- run_meta from run_data_csv ---
    run_meta: Dict[str, Any] = {}
    with open(run_data_csv) as f:
        for row in csv.DictReader(f):
            if run_id_match(row):
                run_meta = {
                    "arch":        row.get("arch", "v1_5"),
                    "hazard_cost": float(row["hazard_cost"]),
                    "num_steps":   int(row["num_steps"]),
                    "run_idx":     int(row["run_idx"]),
                    "seed":        int(row["seed"]),
                }
                break
    if not run_meta:
        raise ValueError(
            f"Run not found in {run_data_csv}: "
            f"run_idx={run_idx}, num_steps={num_steps}, seed={seed}"
        )

    # --- Provenance ---
    prov_substrate: Dict[str, ProvenanceSubstrateRecord] = {}
    with open(provenance_csv) as f:
        for row in csv.DictReader(f):
            if not run_id_match(row):
                continue
            flag_id = row.get("flag_id", "")
            if not flag_id:
                continue
            prov_substrate[flag_id] = ProvenanceSubstrateRecord(
                flag_type=row.get("flag_type", ""),
                flag_coord_str=_str_or_none(row.get("flag_coord")),
                flag_id=flag_id,
                flag_set_step=_int_or_none(row.get("flag_set_step")),
                confirming_observations=int(
                    row.get("confirming_observations") or 0
                ),
                disconfirming_observations=int(
                    row.get("disconfirming_observations") or 0
                ),
                last_confirmation_step=_int_or_none(
                    row.get("last_confirmation_step")
                ),
                last_observation_step=_int_or_none(
                    row.get("last_observation_step")
                ),
                transformed_at_step=_int_or_none(
                    row.get("transformed_at_step")
                ),
                derived_knowledge_flag_id=_str_or_none(
                    row.get("derived_knowledge_flag_id")
                ),
                derived_from_threat_flag_id=_str_or_none(
                    row.get("derived_from_threat_flag_id")
                ),
            )

    # --- Schema ---
    schema_substrate: Optional[Dict[str, Any]] = None
    with open(schema_csv) as f:
        for row in csv.DictReader(f):
            if run_id_match(row):
                schema_substrate = dict(row)
                break

    # --- Family ---
    family_substrate: Optional[Dict[str, Any]] = None
    with open(family_csv) as f:
        for row in csv.DictReader(f):
            if run_id_match(row):
                family_substrate = dict(row)
                break

    # Patch: green_attractor_mastery_step and yellow_attractor_mastery_step
    # are empty in the family CSV when the live observer could not read them
    # from a provenance store (the store is a live reference, not serialised).
    # The provenance substrate already loaded holds the same data under
    # flag_id "mastery:(4, 15)" and "mastery:(16, 3)". Patch here so the
    # Level-7 comparison succeeds and the reporting layer has the steps.
    if family_substrate is not None:
        GREEN_ATT_FLAG  = "mastery:(4, 15)"
        YELLOW_ATT_FLAG = "mastery:(16, 3)"

        if not family_substrate.get("green_attractor_mastery_step"):
            rec = prov_substrate.get(GREEN_ATT_FLAG)
            if rec is not None and rec.flag_set_step is not None:
                family_substrate["green_attractor_mastery_step"] = (
                    str(rec.flag_set_step)
                )

        if not family_substrate.get("yellow_attractor_mastery_step"):
            rec = prov_substrate.get(YELLOW_ATT_FLAG)
            if rec is not None and rec.flag_set_step is not None:
                family_substrate["yellow_attractor_mastery_step"] = (
                    str(rec.flag_set_step)
                )

    # --- Comparison ---
    comparison_substrate: Optional[Dict[str, Any]] = None
    with open(comparison_csv) as f:
        for row in csv.DictReader(f):
            if run_id_match(row):
                comparison_substrate = dict(row)
                break

    # --- Prediction-error ---
    pe_substrate: List[Dict[str, Any]] = []
    with open(prediction_error_csv) as f:
        for row in csv.DictReader(f):
            if run_id_match(row):
                pe_substrate.append({
                    "arch":               row.get("arch", ""),
                    "hazard_cost":        row.get("hazard_cost", ""),
                    "num_steps":          row.get("num_steps", ""),
                    "run_idx":            row.get("run_idx", ""),
                    "seed":               row.get("seed", ""),
                    "step":               _int_or_none(row.get("step")),
                    "cell":               row.get("cell", ""),
                    "family":             _str_or_none(row.get("family")),
                    "precondition_met":   row.get("precondition_met", ""),
                    "cost_paid":          row.get("cost_paid", ""),
                    "transformed_at_step": _int_or_none(
                        row.get("transformed_at_step")
                    ),
                    "resolution_window":  _int_or_none(
                        row.get("resolution_window")
                    ),
                    "encounter_type":     row.get("encounter_type", ""),
                })

    return SubstrateBundle(
        provenance=prov_substrate,
        schema=schema_substrate,
        family=family_substrate,
        comparison=comparison_substrate,
        prediction_error=pe_substrate,
        run_meta=run_meta,
    )
