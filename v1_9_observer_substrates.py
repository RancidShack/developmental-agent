"""
v1_9_observer_substrates.py
-----------------------------
v1.9 additive patches for the counterfactual layer.

ARCHITECTURE PRINCIPLE
This module is imported AFTER v1_8_observer_substrates in the v1.9
batch runner and verifier, so that all v1.8 substrate-interface
patches are applied first and this module extends them.

THREE RESPONSIBILITIES

1. SUBSTRATE BUNDLE EXTENSION
   Monkey-patches SubstrateBundle.__init__, SubstrateBundle.resolve(),
   and build_bundle_from_observers() to support the new counterfactual
   substrate field. All changes are additive; counterfactual=None by
   default preserves full backward compatibility with all existing
   callers.

2. REPORTING LAYER EXTENSION — Q4
   Monkey-patches V16ReportingLayer to add query_where_held_back()
   (Q4: where did I approach without making contact?). Also patches
   generate_report() to include Q4 after Q3.
   Q1, Q2, and Q3 are unchanged.

3. WORLD INTERFACE — no patches required at v1.9
   All required world interfaces (agent_pos, object_positions,
   object_type, _contact_at_pos) were established at v1.7/v1.8.
   No world or agent patching is needed.

ADDITIVE DISCIPLINE
With counterfactual_obs=None in build_bundle_from_observers(), the
v1.9 stack produces output byte-identical to v1.8.2 at matched seeds:
  - SubstrateBundle.counterfactual is None
  - query_where_held_back() returns []
  - generate_report() Q4 section is empty
  - All Q1/Q2/Q3 source_type/source_key combinations are unchanged
This is verified at Level 11 with --no-counterfactual before
Level 11 full verification.
"""

# Ensure v1.8 patches are applied first (which imports v1.7 internally)
import v1_8_observer_substrates  # noqa: F401

from typing import Any, Dict, List, Optional

from v1_6_substrate_bundle import (
    SubstrateBundle,
    ProvenanceSubstrateRecord,
    build_bundle_from_observers as _original_build_bundle,
)
from v1_6_reporting_layer import V16ReportingLayer, ReportStatement

# Import v1.8 build_bundle as the base for our extension
from v1_8_observer_substrates import (
    build_bundle_from_observers as _v18_build_bundle,
)


# ===========================================================================
# 1. SubstrateBundle extension
# ===========================================================================

# ---------------------------------------------------------------------------
# Patch SubstrateBundle.__init__ to accept counterfactual field
# ---------------------------------------------------------------------------

_original_bundle_init = SubstrateBundle.__init__


def _v19_bundle_init(
    self,
    provenance:       Dict[str, ProvenanceSubstrateRecord],
    schema:           Optional[Dict[str, Any]],
    family:           Optional[Dict[str, Any]],
    comparison:       Optional[Dict[str, Any]],
    prediction_error: List[Dict[str, Any]],
    run_meta:         Dict[str, Any],
    goal:             Optional[Dict[str, Any]] = None,
    counterfactual:   Optional[List[Dict[str, Any]]] = None,  # NEW
):
    """Extended __init__: adds counterfactual substrate field.

    All existing positional parameters are unchanged. counterfactual
    defaults to None; passing counterfactual=None preserves full
    backward compatibility with v1.8 callers.

    Note: the v1.8 patch already extended __init__ with the goal field.
    We chain through it here so the goal field is also populated.
    """
    _original_bundle_init(
        self, provenance, schema, family, comparison, prediction_error, run_meta
    )
    self.goal           = goal          # populated by v1.8 patch; re-set here
                                        # so both fields are always present
    self.counterfactual = counterfactual  # None or list of event dicts


SubstrateBundle.__init__ = _v19_bundle_init


# ---------------------------------------------------------------------------
# Patch SubstrateBundle.resolve() to handle "counterfactual" source_type
# ---------------------------------------------------------------------------

_v18_bundle_resolve = SubstrateBundle.resolve   # already patched by v1.8


def _v19_bundle_resolve(self, source_type: str, source_key: str) -> bool:
    """Extended resolve: adds "counterfactual" source_type handling.

    source_key format for counterfactual substrate:
      "suppressed_approach:{object_id}:{closest_approach_step}"

    Returns True if a record exists in bundle.counterfactual with the
    matching object_id and closest_approach_step.

    All other source_types delegate to the v1.8 resolve().
    """
    if source_type != "counterfactual":
        return _v18_bundle_resolve(self, source_type, source_key)

    if not isinstance(getattr(self, 'counterfactual', None), list):
        return False

    # Parse source_key: "suppressed_approach:{object_id}:{step}"
    parts = source_key.split(":")
    if len(parts) != 3 or parts[0] != "suppressed_approach":
        return False

    oid_key  = parts[1]
    try:
        step_key = int(parts[2])
    except ValueError:
        return False

    for rec in self.counterfactual:
        if (rec.get("object_id") == oid_key
                and rec.get("closest_approach_step") == step_key):
            return True

    return False


SubstrateBundle.resolve = _v19_bundle_resolve


# ---------------------------------------------------------------------------
# Patch build_bundle_from_observers() to accept counterfactual_obs parameter
# ---------------------------------------------------------------------------

def build_bundle_from_observers(
    provenance_obs,
    schema_obs,
    family_obs,
    comparison_obs,
    prediction_error_obs,
    run_meta: Dict[str, Any],
    goal_obs=None,
    counterfactual_obs=None,   # NEW — default None preserves v1.8 compat
) -> SubstrateBundle:
    """Extended build_bundle_from_observers: adds counterfactual field.

    All seven existing parameters (including goal_obs from v1.8) are
    unchanged. counterfactual_obs defaults to None; passing None
    produces output identical to v1.8.

    Parameters
    ----------
    counterfactual_obs : V19CounterfactualObserver or None
        The counterfactual observer for this run. None if disabled.
    """
    # Build the seven-field bundle via the v1.8 function
    bundle = _v18_build_bundle(
        provenance_obs=provenance_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comparison_obs=comparison_obs,
        prediction_error_obs=prediction_error_obs,
        run_meta=run_meta,
        goal_obs=goal_obs,
    )

    # Add counterfactual substrate (None if observer not active)
    bundle.counterfactual = (
        counterfactual_obs.get_substrate()
        if counterfactual_obs is not None
        else None
    )

    return bundle


__all__ = ["build_bundle_from_observers"]


# ===========================================================================
# 2. Reporting layer extension — Q4
# ===========================================================================

# ---------------------------------------------------------------------------
# Q4: query_where_held_back — one statement per suppressed-approach record
# ---------------------------------------------------------------------------

def _v19_query_where_held_back(self) -> List[ReportStatement]:
    """Q4: where did I approach without making contact?

    Reads from bundle.counterfactual. Produces one statement per
    confirmed suppressed-approach record. Returns an empty list if
    counterfactual is None or empty — an empty Q4 is not a Category β
    failure; it is an accurate report of a run with no confirmed events.

    Statement text template:
      "At step {step}, I came within {dist:.2f} units of {oid} without
      making contact. I withdrew. [{goal_relevant_clause}]
      [{pre_threshold_clause}]"

    source_type: "counterfactual"
    source_key:  "suppressed_approach:{object_id}:{step}"
    query_type:  "where_held_back"
    """
    bundle = self._bundle
    cf     = getattr(bundle, 'counterfactual', None)

    if not cf:   # None or empty list
        return []

    statements = []
    for rec in cf:
        oid   = rec["object_id"]
        step  = rec["closest_approach_step"]
        dist  = rec["closest_approach_distance"]
        goal_rel   = rec.get("goal_relevant", False)
        pre_entries = rec.get("pre_threshold_entries", 0)

        source_key = f"suppressed_approach:{oid}:{step}"

        # Build text
        parts = [
            f"At step {step}, I came within {dist:.2f} units of "
            f"{oid} without making contact. I withdrew."
        ]
        if goal_rel:
            parts.append("This object was my active goal target.")
        if pre_entries == 0:
            parts.append("I had not yet entered this object.")
        else:
            parts.append(
                f"I had entered this object "
                f"{pre_entries} time(s) previously."
            )

        text = " ".join(parts)

        statements.append(ReportStatement(
            text=text,
            source_type="counterfactual",
            source_key=source_key,
            source_resolves=bundle.resolve("counterfactual", source_key),
            query_type="where_held_back",
        ))

    return statements


V16ReportingLayer.query_where_held_back = _v19_query_where_held_back


# ---------------------------------------------------------------------------
# Patch generate_report() to include Q4 after Q3
# ---------------------------------------------------------------------------

_original_generate_report = V16ReportingLayer.generate_report


def _v19_generate_report(self) -> List[ReportStatement]:
    """Extended generate_report: appends Q4 after Q3.

    Runs the original generate_report() first (Q1 + Q2 + Q3, including
    v1.8 goal extensions), then appends Q4 statements from
    query_where_held_back(). If counterfactual substrate is absent or
    empty, Q4 contributes an empty list and the output is identical to
    v1.8.
    """
    statements = _original_generate_report(self)
    statements.extend(self.query_where_held_back())
    return statements


V16ReportingLayer.generate_report = _v19_generate_report
