"""
v1_11_observer_substrates.py
------------------------------
v1.11 additive patches.

ARCHITECTURE PRINCIPLE
Imported AFTER v1_10_observer_substrates (which imports v1_9, v1_8,
v1_7). All prior patches are applied first; this module extends them.

THREE RESPONSIBILITIES

1. SUBSTRATE BUNDLE EXTENSION
   Monkey-patches SubstrateBundle.__init__, resolve(), and
   build_bundle_from_observers() for the causal field.

2. REPORTING LAYER EXTENSION — Q5 why_this_arc statements
   Monkey-patches V16ReportingLayer to add query_why_arc() and
   extends generate_report() to include Q5 statements.

3. RE-EXPORTS
   Re-exports build_bundle_from_observers so the batch runner can
   import from a single substrate module.

ADDITIVE DISCIPLINE
With causal_obs=None and --no-causal:
  - bundle.causal is None
  - No Q5 statements in report
  - All Q1–Q4 outputs byte-identical to v1.10 at matched seeds
"""

import v1_10_observer_substrates  # noqa: F401

from typing import Any, Dict, List, Optional

from v1_6_substrate_bundle import SubstrateBundle
from v1_6_reporting_layer  import V16ReportingLayer, ReportStatement
from v1_10_observer_substrates import (
    build_bundle_from_observers as _v110_build_bundle,
)

from v1_11_causal_observer import (
    V111CausalObserver,
    CHAIN_DEPTH_MINIMUM,
    LINK_SURPRISE, LINK_PRECONDITION, LINK_MASTERY_FORMATION,
    LINK_PHASE1_ABSENCE, LINK_SUPPRESSED_APPROACH, LINK_BELIEF_REVISION,
)


# ===========================================================================
# 1. SubstrateBundle extension — causal field
# ===========================================================================

_v110_bundle_init = SubstrateBundle.__init__


def _v111_bundle_init(
    self,
    provenance,
    schema,
    family,
    comparison,
    prediction_error,
    run_meta,
    goal            = None,
    counterfactual  = None,
    belief_revision = None,
    causal          = None,
):
    _v110_bundle_init(
        self, provenance, schema, family, comparison,
        prediction_error, run_meta, goal, counterfactual, belief_revision,
    )
    self.causal = causal


SubstrateBundle.__init__ = _v111_bundle_init


_v110_bundle_resolve = SubstrateBundle.resolve


def _v111_bundle_resolve(self, source_type: str, source_key: str) -> bool:
    if source_type != "causal":
        return _v110_bundle_resolve(self, source_type, source_key)

    if not isinstance(getattr(self, 'causal', None), list):
        return False

    # source_key format: "causal_chain:{object_id}:{surprise_step}"
    parts = source_key.split(":")
    if len(parts) != 3 or parts[0] != "causal_chain":
        return False

    oid_key = parts[1]
    try:
        step_key = int(parts[2])
    except ValueError:
        return False

    for rec in self.causal:
        if (rec.get("object_id") == oid_key
                and rec.get("surprise_step") == step_key):
            return True
    return False


SubstrateBundle.resolve = _v111_bundle_resolve


def build_bundle_from_observers(
    provenance_obs,
    schema_obs,
    family_obs,
    comparison_obs,
    prediction_error_obs,
    run_meta: Dict[str, Any],
    goal_obs            = None,
    counterfactual_obs  = None,
    belief_revision_obs = None,
    causal_obs          = None,
) -> SubstrateBundle:
    bundle = _v110_build_bundle(
        provenance_obs=provenance_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comparison_obs=comparison_obs,
        prediction_error_obs=prediction_error_obs,
        run_meta=run_meta,
        goal_obs=goal_obs,
        counterfactual_obs=counterfactual_obs,
        belief_revision_obs=belief_revision_obs,
    )
    bundle.causal = (
        causal_obs.get_substrate()
        if causal_obs is not None
        else None
    )
    return bundle


__all__ = ["build_bundle_from_observers"]


# ===========================================================================
# 2. Reporting layer — Q5 why_this_arc statements
# ===========================================================================

def query_why_arc(self) -> List[ReportStatement]:
    """Generate Q5 causal self-explanation statements.

    One statement per causal chain with chain_depth >= CHAIN_DEPTH_MINIMUM.
    Chains below minimum depth are skipped (not a coverage failure).
    """
    bundle   = self._bundle
    causal   = getattr(bundle, 'causal', None)
    if not causal:
        return []

    statements = []
    for rec in causal:
        if rec.get("chain_depth", 0) < CHAIN_DEPTH_MINIMUM:
            continue

        oid           = rec["object_id"]
        surp_step     = rec["surprise_step"]
        chain_complete = rec.get("chain_complete", False)
        truncated_at   = rec.get("truncated_at")
        links          = rec.get("links", [])

        # Build statement from link statements in causal order
        link_sentences = [lnk["statement"] for lnk in links
                          if lnk.get("statement")]

        if chain_complete:
            closure = "The causal chain is complete."
        elif truncated_at:
            closure = (
                f"The causal chain cannot be extended beyond "
                f"{truncated_at}: the required substrate record "
                f"is absent."
            )
        else:
            closure = ""

        body_parts = [f"I was surprised at {oid} at step {surp_step}."]
        body_parts.extend(link_sentences[1:])  # skip duplicate surprise sentence
        if closure:
            body_parts.append(closure)

        text = " ".join(body_parts)

        source_key = f"causal_chain:{oid}:{surp_step}"
        statements.append(ReportStatement(
            text=text,
            source_type="causal",
            source_key=source_key,
            source_resolves=bundle.resolve("causal", source_key),
            query_type="why_this_arc",
        ))

    return statements


V16ReportingLayer.query_why_arc = query_why_arc


# Extend generate_report to include Q5 after Q4
_v110_generate_report = V16ReportingLayer.generate_report


def _v111_generate_report(self) -> List[ReportStatement]:
    statements = _v110_generate_report(self)
    statements.extend(self.query_why_arc())
    return statements


V16ReportingLayer.generate_report = _v111_generate_report
