"""
v1_8_observer_substrates.py
-----------------------------
v1.8 additive patches for the goal layer.

ARCHITECTURE PRINCIPLE
This module is imported AFTER v1_7_observer_substrates in the v1.8 batch
runner and verifier, so that all v1.7 substrate-interface patches are
applied first and this module extends them.

THREE RESPONSIBILITIES

1. SUBSTRATE BUNDLE EXTENSION
   Monkey-patches SubstrateBundle.__init__, SubstrateBundle.resolve(),
   and build_bundle_from_observers() to support the new goal substrate
   field. All changes are additive; goal=None by default preserves full
   backward compatibility with all existing callers.

2. REPORTING LAYER EXTENSION
   Monkey-patches V16ReportingLayer.query_what_learned() and
   query_where_surprised() to read from the goal substrate field where
   present. Neither method is replaced; the original logic runs first
   and the goal-layer additions are appended.

3. WORLD INTERFACE — no patches required at v1.8
   perceive_within_radius() is already present on V17World (used by the
   v1.7 family observer patch). world._contact_at_pos() is already
   present. V18GoalObserver reads both via the established interfaces.
   No world or agent patching is needed at v1.8.

ADDITIVE DISCIPLINE
With goal_obs=None in build_bundle_from_observers(), the v1.8 stack
produces output byte-identical to v1.7 at matched seeds:
  - SubstrateBundle.goal is None
  - No goal-sourced statements are appended to Q1 or Q3
  - All existing source_type/source_key combinations are unchanged
This is verified at Level 9 re-run before Level 10.
"""

# Ensure v1.7 patches are applied first
import v1_7_observer_substrates  # noqa: F401

from typing import Any, Dict, List, Optional

from v1_6_substrate_bundle import (
    SubstrateBundle,
    ProvenanceSubstrateRecord,
    build_bundle_from_observers as _original_build_bundle,
)
from v1_6_reporting_layer import V16ReportingLayer, ReportStatement


# ===========================================================================
# 1. SubstrateBundle extension
# ===========================================================================

# ---------------------------------------------------------------------------
# Patch SubstrateBundle.__init__ to accept goal field
# ---------------------------------------------------------------------------

_original_bundle_init = SubstrateBundle.__init__


def _v18_bundle_init(
    self,
    provenance:       Dict[str, ProvenanceSubstrateRecord],
    schema:           Optional[Dict[str, Any]],
    family:           Optional[Dict[str, Any]],
    comparison:       Optional[Dict[str, Any]],
    prediction_error: List[Dict[str, Any]],
    run_meta:         Dict[str, Any],
    goal:             Optional[Dict[str, Any]] = None,   # NEW
):
    """Extended __init__: adds goal substrate field.

    All existing positional parameters are unchanged. goal defaults to
    None; passing goal=None is equivalent to the v1.7 constructor.
    """
    _original_bundle_init(
        self, provenance, schema, family, comparison, prediction_error, run_meta
    )
    self.goal = goal   # None if goal observer not active


SubstrateBundle.__init__ = _v18_bundle_init


# ---------------------------------------------------------------------------
# Patch SubstrateBundle.resolve() to handle "goal" source_type
# ---------------------------------------------------------------------------

_original_bundle_resolve = SubstrateBundle.resolve


def _v18_bundle_resolve(self, source_type: str, source_key: str) -> bool:
    """Extended resolve: adds "goal" source_type handling.

    source_key for goal substrate:
      "goal_set"      — resolves if goal_set dict is present
      "goal_progress" — resolves if goal_progress list is non-empty
      "goal_resolved" — resolves if goal_resolved dict is present
      "goal_expired"  — resolves if goal_expired dict is present
      "goal_summary"  — resolves if goal_summary dict is present

    All other source_types delegate to the original resolve().
    """
    if source_type != "goal":
        return _original_bundle_resolve(self, source_type, source_key)

    if self.goal is None:
        return False

    if source_key == "goal_progress":
        val = self.goal.get("goal_progress")
        return isinstance(val, list) and len(val) > 0

    # goal_environment_mapped resolves if the mapped record is present
    # (agent perceived the target during environmental survey)
    val = self.goal.get(source_key)
    return val is not None


SubstrateBundle.resolve = _v18_bundle_resolve


# ---------------------------------------------------------------------------
# Patch build_bundle_from_observers() to accept goal_obs parameter
# ---------------------------------------------------------------------------

def build_bundle_from_observers(
    provenance_obs,
    schema_obs,
    family_obs,
    comparison_obs,
    prediction_error_obs,
    run_meta: Dict[str, Any],
    goal_obs=None,   # NEW — default None preserves backward compatibility
) -> SubstrateBundle:
    """Extended build_bundle_from_observers: adds goal substrate field.

    All six existing parameters are unchanged. goal_obs defaults to None;
    passing goal_obs=None produces output identical to v1.7.

    Parameters
    ----------
    goal_obs : V18GoalObserver or None
        The goal observer for this run. None if goal layer is disabled.
    """
    # Build the six-field bundle via the original function
    bundle = _original_build_bundle(
        provenance_obs=provenance_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comparison_obs=comparison_obs,
        prediction_error_obs=prediction_error_obs,
        run_meta=run_meta,
    )

    # Add goal substrate (None if goal observer not active)
    bundle.goal = (
        goal_obs.get_substrate() if goal_obs is not None else None
    )

    return bundle


# Make the patched version importable from this module
# (batch runner imports from here; v1_6_substrate_bundle is still the
# canonical source for the original six-field version)
__all__ = ["build_bundle_from_observers"]


# ===========================================================================
# 2. Reporting layer extension
# ===========================================================================

# ---------------------------------------------------------------------------
# Q1: relevance markers appended to goal-relevant what_learned statements
# ---------------------------------------------------------------------------

_original_query_what_learned = V16ReportingLayer.query_what_learned


def _v18_query_what_learned(self) -> List[ReportStatement]:
    """Extended query_what_learned: appends relevance markers.

    Runs the original Q1 logic first, then post-processes the statement
    list. Statements for provenance records relevant to the active goal
    have their source_type changed to "goal" and a relevance marker
    appended to their text. Statements for irrelevant records are
    returned unchanged.

    If no goal substrate is present (goal=None), returns original output
    unchanged — full backward compatibility.
    """
    statements = _original_query_what_learned(self)

    bundle   = self._bundle
    goal_sub = getattr(bundle, 'goal', None)

    if goal_sub is None or goal_sub.get("goal_set") is None:
        return statements

    summary   = goal_sub.get("goal_summary", {})
    goal_type = summary.get("goal_type", "")
    target_id = summary.get("target_id", "")

    relevant_flag_ids = _relevant_flag_ids(goal_type, target_id, bundle)
    if not relevant_flag_ids:
        return statements

    result = []
    for stmt in statements:
        if (stmt.query_type == "what_learned"
                and stmt.source_type == "provenance"
                and stmt.source_key in relevant_flag_ids):
            marker = (
                f" (relevant to active goal: {goal_type} — {target_id})"
            )
            result.append(ReportStatement(
                text=stmt.text + marker,
                source_type="goal",
                source_key="goal_set",
                source_resolves=bundle.resolve("goal", "goal_set"),
                query_type="what_learned",
            ))
        else:
            result.append(stmt)

    return result


def _relevant_flag_ids(goal_type, target_id, bundle):
    """Return the set of provenance flag_ids relevant to the active goal.

    Uses the flag_id format established at v1.7: "type:object_id"
    (e.g. "mastery:att_green", "knowledge_banking:haz_green").
    """
    relevant = set()

    if goal_type == "locate_family":
        colour = target_id.lower()   # "green" or "yellow"
        for fid in bundle.provenance:
            # Match any flag_id whose object_id ends with _{colour}
            # e.g. "mastery:att_green", "knowledge_banking:haz_green",
            #      "threat:haz_green"
            if f"_{colour}" in fid:
                relevant.add(fid)

    elif goal_type == "bank_hazard_within_budget":
        # The knowledge_banking record for the specific target hazard
        kb_fid = f"knowledge_banking:{target_id}"
        if kb_fid in bundle.provenance:
            relevant.add(kb_fid)
        # Also the threat record for the same object
        th_fid = f"threat:{target_id}"
        if th_fid in bundle.provenance:
            relevant.add(th_fid)

    elif goal_type == "achieve_end_state":
        for fid in bundle.provenance:
            if fid.startswith("end_state"):
                relevant.add(fid)

    return relevant


V16ReportingLayer.query_what_learned = _v18_query_what_learned


# ---------------------------------------------------------------------------
# Q3: goal statement appended after all prediction-error statements
# ---------------------------------------------------------------------------

_original_query_where_surprised = V16ReportingLayer.query_where_surprised


def _v18_query_where_surprised(self) -> List[ReportStatement]:
    """Extended query_where_surprised: appends goal outcome statement.

    Runs the original Q3 logic first, then appends one goal-sourced
    statement describing whether the goal resolved or expired. The goal
    statement is always the final Q3 statement.

    If no goal substrate is present (goal=None), returns original output
    unchanged — full backward compatibility.
    """
    statements = _original_query_where_surprised(self)

    bundle   = self._bundle
    goal_sub = getattr(bundle, 'goal', None)

    if goal_sub is None:
        return statements

    summary      = goal_sub.get("goal_summary", {})
    goal_type    = summary.get("goal_type", "")
    target_id    = summary.get("target_id", "")
    resolved_rec = goal_sub.get("goal_resolved")
    expired_rec  = goal_sub.get("goal_expired")

    if resolved_rec is not None:
        text = (
            f"My goal ({goal_type}: {target_id}) resolved at step "
            f"{resolved_rec['resolved_at_step']}, with "
            f"{resolved_rec['budget_remaining']} steps remaining "
            f"in the budget."
        )
        statements.append(self._make(
            text=text,
            source_type="goal",
            source_key="goal_resolved",
            query_type="where_surprised",
        ))

    elif expired_rec is not None:
        last_progress = expired_rec.get("last_progress_step")
        rw            = expired_rec.get("goal_resolution_window")
        mapped_rec    = goal_sub.get("goal_environment_mapped")

        if last_progress is not None:
            # Agent engaged in Phase 2 but did not resolve within window
            text = (
                f"My goal ({goal_type}: {target_id}) expired at step "
                f"{expired_rec['expired_at_step']} without resolution. "
                f"My closest approach was at step {last_progress}, "
                f"leaving a goal-resolution window of {rw} steps."
            )
        elif mapped_rec is not None:
            # Agent surveyed the environment and located the target in
            # Phase 1 but never engaged with it in Phase 2
            text = (
                f"My goal ({goal_type}: {target_id}) expired at step "
                f"{expired_rec['expired_at_step']} without resolution. "
                f"I registered the target in the environment at step "
                f"{mapped_rec['mapped_at_step']} during Phase "
                f"{mapped_rec['mapped_in_phase']} mapping, but did not "
                f"engage with it during Phase 2 within the observation window."
            )
        else:
            # Target was never perceived — not in survey path
            text = (
                f"My goal ({goal_type}: {target_id}) expired at step "
                f"{expired_rec['expired_at_step']} without resolution. "
                f"No progress was recorded and the target was not "
                f"encountered during environmental mapping."
            )
        statements.append(self._make(
            text=text,
            source_type="goal",
            source_key="goal_expired",
            query_type="where_surprised",
        ))

    return statements


V16ReportingLayer.query_where_surprised = _v18_query_where_surprised
