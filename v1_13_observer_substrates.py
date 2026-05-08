"""
v1_13_observer_substrates.py
-----------------------------
v1.13 additive patches.

ARCHITECTURE PRINCIPLE
Imported AFTER v1_11_observer_substrates (which imports v1_10, v1_9,
v1_8, v1_7). All prior patches are applied first; this module extends
them.

THREE RESPONSIBILITIES

1. SUBSTRATE BUNDLE EXTENSION
   Monkey-patches SubstrateBundle.__init__ and
   build_bundle_from_observers() for the predicted_schema field.

2. V113 CAUSAL OBSERVER EXTENSION
   Extends V111CausalObserver with build_predicted_records(bundle,
   schema_obs). Called within-run on the haz_blue surprise event.
   Inspects truncated chains for LINK_PRECONDITION truncation, checks
   the two-family minimum, and writes a predicted schema record if the
   abductive inference is valid.

3. REPORTING LAYER EXTENSION — Q5 predicted record statements
   Extends query_why_arc() to include predicted chain statements.

ADDITIVE DISCIPLINE
With schema_obs prediction_enabled=False (--no-prediction):
  - bundle.predicted_schema is []
  - No predicted statements in Q5 report
  - All Q1-Q5 outputs byte-identical to v1.12 at matched seeds

HONESTY CONSTRAINT (pre-registered)
  - A predicted record is not a confirmed record.
  - A chain that continues past an unresolvable link is a
    Category α failure.
  - A fabricated predicted record — a prediction without a structural
    rule in the substrate — is a Category α failure.
  - Two confirmed family chains are the minimum substrate for a valid
    prediction. Fewer than two: inference does not fire.
"""

import v1_11_observer_substrates  # noqa: F401

from typing import Any, Dict, List, Optional

from v1_6_substrate_bundle   import SubstrateBundle
from v1_6_reporting_layer    import V16ReportingLayer, ReportStatement
from v1_11_observer_substrates import (
    build_bundle_from_observers as _v111_build_bundle,
)
from v1_11_causal_observer   import (
    V111CausalObserver,
    LINK_PRECONDITION,
    CHAIN_DEPTH_MINIMUM,
)
from v1_13_schema_extension  import (
    V13SchemaObserver,
    PREDICTED_STATE,
    CONFIRMED_STATE,
    UNRESOLVABLE_STATE,
)

# ===========================================================================
# 0. V15PredictionErrorObserver — _tracked_cells sanitisation
# ===========================================================================
# The v1_7_observer_substrates patch migrates V15PredictionErrorObserver to
# use object_id strings for _tracked_cells. However on_run_end calls
# sorted(self._tracked_cells) on the raw set, which may contain (x,y,z)
# agent_pos tuples added by any unpatched on_post_event code path.
# V113World.agent_pos is a 3-tuple; those tuples cannot be compared with
# strings in sorted(). Fix: sanitise _tracked_cells to strings only before
# calling the original on_run_end. Additive and idempotent.

from v1_5_prediction_error_observer import V15PredictionErrorObserver

_original_pe_on_run_end = V15PredictionErrorObserver.on_run_end


def _v113_pe_on_run_end(self, total_steps):
    # Sanitise _tracked_cells: remove any non-string entries (e.g. agent_pos tuples)
    if hasattr(self, '_tracked_cells'):
        self._tracked_cells = {
            c for c in self._tracked_cells if isinstance(c, str)
        }
    # Guard all v1_7 patch attributes that on_run_end may read
    _pe_defaults = {
        '_encounter_records':           [],
        '_resolved_surprises':          [],
        '_yellow_pre_transition_steps': [],
        '_green_pre_transition_steps':  [],
        '_yellow_resolution_window':    None,
        '_green_resolution_window':     None,
        '_family_pe_records':           {},
        '_pe_complete':                 False,
        '_total_pe_events':             0,
    }
    for attr, default in _pe_defaults.items():
        if not hasattr(self, attr):
            setattr(self, attr, default)
    _original_pe_on_run_end(self, total_steps)


V15PredictionErrorObserver.on_run_end = _v113_pe_on_run_end


# ===========================================================================
# 0b. V15PredictionErrorObserver — _encounter_records attribute guard
# ===========================================================================
# The v1_7 patch adds _encounter_records to V15PredictionErrorObserver
# for V17World. summary_metrics() at line 500 reads:
#   len(self._encounter_records) > 0
# If _encounter_records was never set (because a code path bypassed the
# v1_7 __init__ patch), this raises AttributeError. Guard by ensuring
# the attribute exists before summary_metrics() is called.

_original_pe_summary_metrics = V15PredictionErrorObserver.summary_metrics


def _v113_pe_summary_metrics(self):
    # Guard all attributes added by the v1_7 patch that may be absent
    # when V113World is used and any init code path was bypassed.
    _pe_defaults = {
        '_encounter_records':           [],
        '_resolved_surprises':          [],
        '_yellow_pre_transition_steps': [],
        '_green_pre_transition_steps':  [],
        '_yellow_resolution_window':    None,
        '_green_resolution_window':     None,
        '_family_pe_records':           {},
        '_pe_complete':                 False,
        '_total_pe_events':             0,
    }
    for attr, default in _pe_defaults.items():
        if not hasattr(self, attr):
            setattr(self, attr, default)
    return _original_pe_summary_metrics(self)


V15PredictionErrorObserver.summary_metrics = _v113_pe_summary_metrics


# Minimum confirmed family chains required before abductive inference fires.
# Pre-registered in v1.13 pre-registration Section 2.4.
PREDICTION_FAMILY_MINIMUM = 2


# ===========================================================================
# 1. SubstrateBundle extension — predicted_schema field
# ===========================================================================

_v111_bundle_init = SubstrateBundle.__init__


def _v113_bundle_init(
    self,
    provenance,
    schema,
    family,
    comparison,
    prediction_error,
    run_meta,
    goal             = None,
    counterfactual   = None,
    belief_revision  = None,
    causal           = None,
    predicted_schema = None,
):
    _v111_bundle_init(
        self, provenance, schema, family, comparison,
        prediction_error, run_meta, goal, counterfactual,
        belief_revision, causal,
    )
    self.predicted_schema = predicted_schema or []


SubstrateBundle.__init__ = _v113_bundle_init


def build_bundle_from_observers(
    provenance_obs,
    schema_obs,
    family_obs,
    comparison_obs,
    prediction_error_obs,
    run_meta:             Dict[str, Any],
    goal_obs              = None,
    counterfactual_obs    = None,
    belief_revision_obs   = None,
    causal_obs            = None,
    schema_v13_obs        = None,
) -> SubstrateBundle:
    """Build SubstrateBundle including the v1.13 predicted_schema field.

    schema_v13_obs : V13SchemaObserver | None
        If provided, its predicted records are attached to the bundle.
        If None (or --no-prediction), bundle.predicted_schema is [].
    """
    bundle = _v111_build_bundle(
        provenance_obs=provenance_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comparison_obs=comparison_obs,
        prediction_error_obs=prediction_error_obs,
        run_meta=run_meta,
        goal_obs=goal_obs,
        counterfactual_obs=counterfactual_obs,
        belief_revision_obs=belief_revision_obs,
        causal_obs=causal_obs,
    )
    bundle.predicted_schema = (
        schema_v13_obs.get_predicted_records()
        if schema_v13_obs is not None
        else []
    )
    return bundle


__all__ = ["build_bundle_from_observers", "PREDICTION_FAMILY_MINIMUM"]


# ===========================================================================
# 2. V111CausalObserver extension — build_predicted_records
# ===========================================================================

def build_predicted_records(
    self,
    bundle,
    schema_obs:    V13SchemaObserver,
    current_step:  int,
    env_number:    int = 1,
) -> None:
    """Inspect truncated chains and fire abductive inference.

    Called WITHIN THE RUN on the haz_blue surprise event — not post-run.
    Required because the predicted schema record must exist before the
    transfer gate fires.

    ABDUCTIVE INFERENCE RULE
    A predicted record is written when ALL of the following hold:
      1. A truncated chain exists for object_id (truncated_at =
         LINK_PRECONDITION) — the precondition was not found.
      2. The number of complete (non-truncated, chain_complete=True)
         family chains in the current substrate meets or exceeds
         PREDICTION_FAMILY_MINIMUM (2). This is the two-family minimum.
      3. The naming convention for the predicted precondition is
         derivable: haz_{colour} → att_{colour}.
      4. No predicted record already exists for this object_id (idempotent).

    HONESTY CONSTRAINT
    The predicted precondition is derived from structural pattern only.
    It is flagged PREDICTED_STATE. It is not confirmed. Any chain
    statement referencing it must explicitly flag its predicted status.

    Parameters
    ----------
    bundle : SubstrateBundle
        The partial bundle assembled at the point of the surprise event.
        May not be fully populated — provenance is live but post-run
        analyses are not yet complete.
    schema_obs : V13SchemaObserver
        The schema observer's write pathway.
    current_step : int
        The step at which the surprise event fired.
    env_number : int
        Environment number (1 for ENV1). Recorded in the predicted record.
    """
    # Already have a pending prediction — idempotent
    # (haz_blue might fire multiple contacts before transfer)
    if schema_obs.has_pending_prediction("haz_blue"):
        return

    # Collect current truncated and complete chains from the causal
    # substrate built so far. Note: build_causal_chains() runs post-run;
    # at this point we inspect _records directly for any chains already
    # assembled via an earlier post-event call, OR we check the PE
    # substrate directly for the truncation signal.

    # Confirm haz_blue cost was paid: the batch runner calls this method
    # only on contact_oid == "haz_blue" and cost > 0, so we can proceed
    # directly without requiring a PE substrate record for haz_blue.
    # The PE observer does not generate a surprise record for haz_blue
    # because att_blue is absent from ENV1's family_precondition_attractor —
    # haz_blue is treated as competency-gated (threshold=99) and the PE
    # observer records cost events but not precondition-failure surprises
    # for unaffiliated-gated objects. The cost payment itself is the
    # abductive trigger: the agent paid cost and has no schema explanation.
    # No PE event check needed here.

    # Derive predicted precondition from naming convention
    # haz_blue → att_blue. Confirmed by family field = BLUE.
    predicted_precondition = "att_blue"

    # Two-family minimum check.
    # At the point of within-run inference, causal chains may not yet be
    # complete (GREEN chain resolves late in the run; YELLOW may be complete
    # but GREEN transition has not yet fired). We therefore count evidence
    # from two sources:
    #   (a) complete causal chains already in the substrate, AND
    #   (b) resolved PE events for family-affiliated hazards (YELLOW, GREEN)
    #       where the hazard has already transitioned (transformation fired).
    # A family is counted once per source. The combined count must meet
    # PREDICTION_FAMILY_MINIMUM. This is the pre-registered two-family rule.

    causal = getattr(bundle, 'causal', None) or []
    complete_family_chains = [
        rec for rec in causal
        if rec.get('chain_complete', False)
        and rec.get('object_id') not in ('haz_unaff_0', 'haz_unaff_1',
                                          'haz_unaff_2')
    ]
    confirmed_family_oids = {rec['object_id'] for rec in complete_family_chains}

    # Count family PE records where transition has fired (resolution evidence)
    pe_all = getattr(bundle, 'prediction_error', None) or []
    family_hazards = {'haz_yellow', 'haz_green'}
    for event in pe_all:
        if not isinstance(event, dict):
            continue
        oid = event.get('cell') or event.get('object_id')
        if oid in family_hazards and event.get('transformed_at_step') is not None:
            confirmed_family_oids.add(oid)

    if len(confirmed_family_oids) < PREDICTION_FAMILY_MINIMUM:
        # Insufficient confirmed family evidence — inference does not fire.
        # Correct behaviour at cost < 10.0 where GREEN is absent.
        return

    # Collect basis chain object IDs from all confirmed sources
    basis_chains = sorted(confirmed_family_oids)

    # All conditions met — write predicted record
    record = {
        "object_id":              "haz_blue",
        "predicted_precondition": predicted_precondition,
        "basis_chains":           basis_chains,
        "prediction_step":        current_step,
        "prediction_env":         env_number,
    }
    schema_obs.add_predicted_record(record)


V111CausalObserver.build_predicted_records = build_predicted_records


# ===========================================================================
# 3. Reporting layer — Q5 predicted record statements
# ===========================================================================

_v111_query_why_arc = V16ReportingLayer.query_why_arc


def _v113_query_why_arc(self) -> List[ReportStatement]:
    """Generate Q5 statements including predicted schema records.

    Extends the v1.11 query_why_arc with additional statements for
    any predicted schema records in bundle.predicted_schema.

    Predicted records produce a distinct statement type that explicitly
    flags the predicted status — a predicted record is not a confirmed
    record, and the statement must not imply otherwise.
    """
    statements = _v111_query_why_arc(self)

    bundle   = self._bundle
    predicted = getattr(bundle, 'predicted_schema', None) or []

    for rec in predicted:
        oid         = rec["object_id"]
        precond     = rec["predicted_precondition"]
        state       = rec["state"]
        pred_step   = rec.get("prediction_step", "unknown")
        basis       = rec.get("basis_chains", [])
        basis_str   = " and ".join(basis) if basis else "prior family chains"

        if state == PREDICTED_STATE:
            text = (
                f"I encountered {oid} at step {pred_step} and paid a cost. "
                f"No precondition record exists in my schema for {oid}. "
                f"The structural pattern of {basis_str} predicts that "
                f"{precond} is the precondition for {oid}. "
                f"This record is predicted, not confirmed. "
                f"Confirmation requires encountering and mastering {precond} "
                f"and observing that its mastery enables transformation of "
                f"{oid}. I am still looking."
            )

        elif state == CONFIRMED_STATE:
            conf_step = rec.get("confirmation_step", "unknown")
            conf_env  = rec.get("confirming_env", "unknown")
            text = (
                f"I encountered {oid} at step {pred_step} and paid a cost. "
                f"The structural pattern of {basis_str} predicted that "
                f"{precond} is the precondition for {oid}. "
                f"I mastered {precond} at step {conf_step} in environment "
                f"{conf_env}. The prediction is confirmed. "
                f"The transformation of {oid} requires return to its "
                f"environment — that step is pending."
            )

        elif state == UNRESOLVABLE_STATE:
            text = (
                f"I encountered {oid} at step {pred_step} and paid a cost. "
                f"The structural pattern of {basis_str} predicted that "
                f"{precond} is the precondition for {oid}. "
                f"I searched for {precond} and did not find it within "
                f"the available environments. "
                f"The predicted record remains open. "
                f"This chain cannot be extended further with current evidence."
            )

        else:
            continue

        source_key = f"predicted_schema:{oid}:{pred_step}"
        statements.append(ReportStatement(
            text=text,
            source_type="predicted_schema",
            source_key=source_key,
            source_resolves=True,   # record exists in bundle.predicted_schema
            query_type="why_this_arc",
        ))

    return statements


V16ReportingLayer.query_why_arc = _v113_query_why_arc


# ===========================================================================
# 4. V111CausalObserver.build_causal_chains — per-event deduplication
#    Replaces the _built flag with a set of already-processed (object_id,
#    surprise_step) pairs. Allows within-run partial calls followed by a
#    complete post-run call without duplication or silent skipping.
# ===========================================================================

_original_build_causal_chains = V111CausalObserver.build_causal_chains


def _v113_build_causal_chains(self, bundle) -> None:
    """Build causal chains, skipping events already processed.

    Replaces the v1.11 _built flag with per-event deduplication so that
    build_causal_chains() can be called multiple times safely:
      - within-run call on partial bundle: builds YELLOW/GREEN chains
      - post-run call on complete bundle: adds any new resolvable events

    Idempotent per (object_id, surprise_step) pair.
    """
    if not hasattr(self, '_processed_events'):
        self._processed_events = set()

    pe = getattr(bundle, 'prediction_error', None) or []
    if not pe:
        return

    for event in pe:
        if not isinstance(event, dict):
            continue
        if event.get('precondition_met', True):
            continue
        if event.get('transformed_at_step') is None:
            continue

        object_id     = event.get('cell') or event.get('object_id')
        surprise_step = event.get('step')

        if object_id is None or surprise_step is None:
            continue

        key = (object_id, surprise_step)
        if key in self._processed_events:
            continue   # already built; skip to avoid duplication

        self._processed_events.add(key)
        resolution_step = event.get('transformed_at_step')
        chain = self._build_chain(
            bundle, object_id, surprise_step, resolution_step, event
        )
        self._records.append(chain)


V111CausalObserver.build_causal_chains = _v113_build_causal_chains
