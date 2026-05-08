"""
v1_13_schema_extension.py
--------------------------
V13SchemaObserver write pathway for predicted schema records.

ARCHITECTURAL ROLE
At v1.11, V111CausalObserver truncates a causal chain at
LINK_PRECONDITION when the required precondition attractor is absent
from the schema. The chain ends: the story cannot be continued.

At v1.13, before that truncation, the causal observer asks a different
question: does the structural pattern of confirmed family chains justify
a prediction about what must exist? If yes, it calls
schema_obs.add_predicted_record(record). The schema observer holds the
prediction. The batch runner reads it to inject the directed search
waypoint. The reporting layer reads it for Q5 extension.

WRITE PATHWAY DISCIPLINE
The write pathway is conditional on the prediction flag. With
--no-prediction:
  - add_predicted_record() is a no-op
  - get_predicted_records() returns []
  - get_substrate() returns the schema substrate unchanged
All Q1-Q4 outputs are byte-identical to v1.12 at matched seeds.

PREDICTED RECORD STATES
Three discrete, non-gradational states:
  predicted      — inference written; confirmation not yet received
  confirmed      — att_blue mastered in Environment 2; record updated
  unresolvable   — step budget exhausted; att_blue not found

A predicted record reported as confirmed without direct mastery
evidence in provenance is a hallucination at the architectural level.
These states are not gradations. They have different substrate anchors.

RECORD FORMAT
{
    "object_id":            str,   # haz_blue
    "predicted_precondition": str, # att_blue
    "basis_chains":         list,  # [haz_yellow, haz_green]
    "state":                str,   # predicted | confirmed | unresolvable
    "prediction_step":      int,   # step at which inference fired
    "confirmation_step":    int | None,
    "confirming_env":       int | None,  # environment number
    "unresolvable":         bool,
}
"""

from typing import Any, Dict, List, Optional

PREDICTED_STATE   = "predicted"
CONFIRMED_STATE   = "confirmed"
UNRESOLVABLE_STATE = "unresolvable"

PREDICTED_SCHEMA_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost",
    "object_id",
    "predicted_precondition",
    "basis_chains",
    "state",
    "prediction_step",
    "confirmation_step",
    "confirming_env",
    "unresolvable",
]


class V13SchemaObserver:
    """Schema observer write pathway for v1.13 predicted schema records.

    Parameters
    ----------
    prediction_enabled : bool
        If False (--no-prediction flag), all write operations are no-ops
        and the observer is transparent to the existing stack.
    """

    def __init__(self, prediction_enabled: bool = True):
        self._prediction_enabled = prediction_enabled
        self._predicted_records: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Write pathway
    # ------------------------------------------------------------------

    def add_predicted_record(self, record: Dict[str, Any]) -> None:
        """Add a predicted schema record.

        Called by V113CausalObserver.build_predicted_records() when the
        abductive inference fires. No-op if prediction_enabled=False.

        Parameters
        ----------
        record : dict
            Must contain at minimum: object_id, predicted_precondition,
            basis_chains, prediction_step. State is set to PREDICTED_STATE
            on entry regardless of caller-supplied value.
        """
        if not self._prediction_enabled:
            return

        # Enforce state discipline: caller cannot write confirmed/unresolvable
        # at creation time. State begins as predicted.
        safe_record = dict(record)
        safe_record["state"]             = PREDICTED_STATE
        safe_record["confirmation_step"] = None
        safe_record["confirming_env"]    = None
        safe_record["unresolvable"]      = False

        self._predicted_records.append(safe_record)

    def confirm_predicted_record(
        self,
        object_id:         str,
        confirmation_step: int,
        confirming_env:    int,
    ) -> bool:
        """Update a predicted record to confirmed state.

        Called by the batch runner when att_blue mastery is confirmed
        in Environment 2. Returns True if the record was found and
        updated, False if no matching predicted record exists.

        A record is confirmed only when:
          - state is currently PREDICTED_STATE (not already confirmed
            or unresolvable)
          - mastery evidence exists in provenance (caller responsibility
            to verify before calling)

        Parameters
        ----------
        object_id : str
            The hazard object whose predicted precondition was confirmed
            (e.g. haz_blue).
        confirmation_step : int
            The step at which att_blue mastery was achieved.
        confirming_env : int
            The environment number in which mastery occurred (2 for ENV2).
        """
        if not self._prediction_enabled:
            return False

        for rec in self._predicted_records:
            if (rec["object_id"] == object_id
                    and rec["state"] == PREDICTED_STATE):
                rec["state"]             = CONFIRMED_STATE
                rec["confirmation_step"] = confirmation_step
                rec["confirming_env"]    = confirming_env
                return True
        return False

    def mark_unresolvable(self, object_id: str) -> bool:
        """Mark a predicted record as unresolvable at run end.

        Called by the batch runner when the step budget for Environment 2
        is exhausted without att_blue mastery. Returns True if a
        predicted record was found and marked, False otherwise.

        Only records in PREDICTED_STATE are eligible — a confirmed record
        cannot become unresolvable.
        """
        if not self._prediction_enabled:
            return False

        for rec in self._predicted_records:
            if (rec["object_id"] == object_id
                    and rec["state"] == PREDICTED_STATE):
                rec["state"]       = UNRESOLVABLE_STATE
                rec["unresolvable"] = True
                return True
        return False

    # ------------------------------------------------------------------
    # Read pathway
    # ------------------------------------------------------------------

    def get_predicted_records(self) -> List[Dict[str, Any]]:
        """Return all predicted schema records (copies).

        Returns [] if prediction_enabled=False.
        """
        return [dict(r) for r in self._predicted_records]

    def has_pending_prediction(self, object_id: str) -> bool:
        """Return True if a PREDICTED_STATE record exists for object_id."""
        return any(
            r["object_id"] == object_id and r["state"] == PREDICTED_STATE
            for r in self._predicted_records
        )

    def get_directed_search_target(self) -> Optional[str]:
        """Return the predicted_precondition of the first PREDICTED_STATE
        record, or None if no pending prediction exists.

        Used by the batch runner to inject the directed search waypoint
        in Environment 2.
        """
        for rec in self._predicted_records:
            if rec["state"] == PREDICTED_STATE:
                return rec["predicted_precondition"]
        return None

    # ------------------------------------------------------------------
    # CSV output
    # ------------------------------------------------------------------

    def predicted_schema_rows(self, run_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return CSV-ready rows for predicted_schema_v1_13.csv."""
        rows = []
        for rec in self._predicted_records:
            row = {
                "arch":        run_meta.get("arch", ""),
                "run_idx":     run_meta.get("run_idx", ""),
                "seed":        run_meta.get("seed", ""),
                "hazard_cost": run_meta.get("hazard_cost", ""),
                "object_id":              rec["object_id"],
                "predicted_precondition": rec["predicted_precondition"],
                "basis_chains":           "|".join(rec.get("basis_chains", [])),
                "state":                  rec["state"],
                "prediction_step":        rec.get("prediction_step", ""),
                "confirmation_step":      rec.get("confirmation_step", ""),
                "confirming_env":         rec.get("confirming_env", ""),
                "unresolvable":           rec.get("unresolvable", False),
            }
            rows.append(row)
        return rows
