"""
v1_10_observer_substrates.py
------------------------------
v1.10 additive patches.

ARCHITECTURE PRINCIPLE
Imported AFTER v1_9_observer_substrates (which imports v1_8, which
imports v1_7). All prior patches are applied first; this module
extends them.

FOUR RESPONSIBILITIES

1. SUBSTRATE BUNDLE EXTENSION
   Monkey-patches SubstrateBundle.__init__, resolve(), and
   build_bundle_from_observers() for the belief_revision field.

2. REPORTING LAYER EXTENSION — Q3 belief-revision statements
   Monkey-patches V16ReportingLayer.query_where_surprised() to append
   belief-revision statements after all existing Q3 statements.

3. TEMPORAL EXCLUSION WINDOW
   Monkey-patches V19CounterfactualObserver._ObjectWindow to apply
   K_EXCLUSION=500 at record-emission stage. Detection at N=3/3 is
   unchanged; records within 500 steps of a prior emission for the
   same object are discarded.

4. ENVIRONMENT_COMPLETE PROVENANCE RECORD
   Monkey-patches V1ProvenanceStore to add on_end_state_banked() hook,
   firing an environment_complete record when the agent banks the end
   state.

ADDITIVE DISCIPLINE
With belief_revision_obs=None and --no-completion-signal:
  - bundle.belief_revision is None
  - No belief-revision statements in Q3
  - CF records are reduced by temporal exclusion window
  - All Q1/Q2/Q4 outputs identical to v1.9 at matched seeds
"""

# Ensure v1.9 patches applied first (imports v1.8 → v1.7 internally)
import v1_9_observer_substrates  # noqa: F401

from typing import Any, Dict, List, Optional

from v1_6_substrate_bundle import (
    SubstrateBundle,
    ProvenanceSubstrateRecord,
    build_bundle_from_observers as _original_build_bundle,
)
from v1_6_reporting_layer import V16ReportingLayer, ReportStatement
from v1_9_observer_substrates import (
    build_bundle_from_observers as _v19_build_bundle,
)

# K_EXCLUSION: temporal exclusion window per object (steps)
K_EXCLUSION = 500   # pre-registered; see v1_10_pre_registration.md


# ===========================================================================
# 1. SubstrateBundle extension
# ===========================================================================

_v19_bundle_init = SubstrateBundle.__init__


def _v110_bundle_init(
    self,
    provenance,
    schema,
    family,
    comparison,
    prediction_error,
    run_meta,
    goal             = None,
    counterfactual   = None,
    belief_revision  = None,   # NEW
):
    """Extended __init__: adds belief_revision substrate field."""
    _v19_bundle_init(
        self, provenance, schema, family, comparison,
        prediction_error, run_meta, goal, counterfactual
    )
    self.belief_revision = belief_revision   # None or list of records


SubstrateBundle.__init__ = _v110_bundle_init


# ---------------------------------------------------------------------------
# Patch resolve() for "belief_revision" source_type
# ---------------------------------------------------------------------------

_v19_bundle_resolve = SubstrateBundle.resolve


def _v110_bundle_resolve(self, source_type: str, source_key: str) -> bool:
    """Extended resolve: adds "belief_revision" source_type.

    source_key format: "revised_expectation:{object_id}:{surprise_step}"
    Returns True if a matching record exists in bundle.belief_revision.
    """
    if source_type != "belief_revision":
        return _v19_bundle_resolve(self, source_type, source_key)

    if not isinstance(getattr(self, 'belief_revision', None), list):
        return False

    parts = source_key.split(":")
    if len(parts) != 3 or parts[0] != "revised_expectation":
        return False

    oid_key = parts[1]
    try:
        step_key = int(parts[2])
    except ValueError:
        return False

    for rec in self.belief_revision:
        if (rec.get("object_id") == oid_key
                and rec.get("surprise_step") == step_key):
            return True

    return False


SubstrateBundle.resolve = _v110_bundle_resolve


# ---------------------------------------------------------------------------
# Patch build_bundle_from_observers()
# ---------------------------------------------------------------------------

def build_bundle_from_observers(
    provenance_obs,
    schema_obs,
    family_obs,
    comparison_obs,
    prediction_error_obs,
    run_meta: Dict[str, Any],
    goal_obs              = None,
    counterfactual_obs    = None,
    belief_revision_obs   = None,   # NEW
) -> SubstrateBundle:
    """Extended: adds belief_revision field to bundle."""
    bundle = _v19_build_bundle(
        provenance_obs=provenance_obs,
        schema_obs=schema_obs,
        family_obs=family_obs,
        comparison_obs=comparison_obs,
        prediction_error_obs=prediction_error_obs,
        run_meta=run_meta,
        goal_obs=goal_obs,
        counterfactual_obs=counterfactual_obs,
    )
    bundle.belief_revision = (
        belief_revision_obs.get_substrate()
        if belief_revision_obs is not None
        else None
    )
    return bundle


__all__ = ["build_bundle_from_observers"]


# ===========================================================================
# 2. Reporting layer extension — Q3 belief-revision statements
# ===========================================================================

_v19_query_where_surprised = V16ReportingLayer.query_where_surprised


def _v110_query_where_surprised(self) -> List[ReportStatement]:
    """Extended query_where_surprised: appends belief-revision statements.

    Runs the v1.9 Q3 logic first (prediction-error + goal outcome),
    then appends one belief-revision statement per revised_expectation
    record. Belief-revision statements are always the final Q3
    statements.

    If no belief_revision substrate is present, returns v1.9 output
    unchanged.
    """
    statements = _v19_query_where_surprised(self)

    bundle = self._bundle
    br_sub = getattr(bundle, 'belief_revision', None)

    if not br_sub:   # None or empty list
        return statements

    for rec in br_sub:
        oid       = rec["object_id"]
        surp_step = rec["surprise_step"]
        res_win   = rec["resolution_window"]
        revised   = rec.get("revised_expectation", "")
        delta     = rec.get("approach_delta", 0)
        bias_dur  = 10_000   # BIAS_DURATION; imported constant not available
                             # in this scope — use the pre-registered value

        # Extract precondition name and mastery step from revised text
        # for the statement (the full text is already in the record)
        precond_clause = rec.get("precondition_at_revision", "the precondition")

        if delta > 0:
            behaviour_clause = (
                f"My approach to {oid} changed: I moved toward it "
                f"{delta} time(s) more often in the "
                f"{bias_dur:,}-step period following revision than "
                f"in the equivalent period before."
            )
        elif delta < 0:
            behaviour_clause = (
                f"My approach to {oid} changed: I moved toward it "
                f"{abs(delta)} time(s) less often following revision "
                f"than before — caution, not confidence, followed "
                f"from the revised expectation."
            )
        else:
            behaviour_clause = (
                f"My approach trajectory toward {oid} was not "
                f"measurably altered within the observation window."
            )

        text = (
            f"I was surprised by {oid} at step {surp_step} because "
            f"I believed entry would lead directly to transformation. "
            f"After {res_win:,} steps, I understood that "
            f"{precond_clause}. "
            f"{behaviour_clause}"
        )

        source_key = f"revised_expectation:{oid}:{surp_step}"

        statements.append(ReportStatement(
            text=text,
            source_type="belief_revision",
            source_key=source_key,
            source_resolves=bundle.resolve("belief_revision", source_key),
            query_type="where_surprised",
        ))

    return statements


V16ReportingLayer.query_where_surprised = _v110_query_where_surprised


# ===========================================================================
# 3. Temporal exclusion window for V19CounterfactualObserver
# ===========================================================================

def _apply_temporal_exclusion_window():
    """Patch V19CounterfactualObserver to apply K_EXCLUSION=500.

    After a suppressed-approach record is emitted for object_id, no
    new record for the same object_id is emitted for K_EXCLUSION steps.
    Detection at N=3/3 is unchanged; confirmed events within the
    exclusion window are silently discarded at emission.

    The patch is applied to V19CounterfactualObserver.on_post_event
    by wrapping it to track last-emission steps per object.
    """
    try:
        from v1_9_counterfactual_observer import V19CounterfactualObserver
    except ImportError:
        return   # Not available; skip

    _original_on_post_event = V19CounterfactualObserver.on_post_event

    def _v110_on_post_event(self, step: int) -> None:
        """Wrapped on_post_event: applies temporal exclusion window."""
        # Initialise last-emission tracker if absent
        if not hasattr(self, '_last_emission_step'):
            self._last_emission_step = {}

        # Count records before and after to detect new emissions
        count_before = len(self._records)
        _original_on_post_event(self, step)
        count_after  = len(self._records)

        if count_after <= count_before:
            return   # No new records emitted

        # Check each newly emitted record against the exclusion window
        keep = []
        for rec in self._records[count_before:]:
            oid       = rec["object_id"]
            last_step = self._last_emission_step.get(oid)
            if last_step is not None and (step - last_step) < K_EXCLUSION:
                # Within exclusion window — discard
                if not hasattr(self, '_cf_raw_count'):
                    self._cf_raw_count = 0
                self._cf_raw_count += 1
            else:
                # Outside exclusion window — keep and update tracker
                self._last_emission_step[oid] = step
                keep.append(rec)

        # Replace the tail of _records with only the kept records
        self._records = self._records[:count_before] + keep

    V19CounterfactualObserver.on_post_event = _v110_on_post_event

    # Add helper to get raw count (detected before exclusion)
    def _cf_raw_records_count(self) -> int:
        return len(self._records) + getattr(self, '_cf_raw_count', 0)

    V19CounterfactualObserver.raw_records_count = _cf_raw_records_count


_apply_temporal_exclusion_window()


# ===========================================================================
# 4. Environment-complete provenance record
# ===========================================================================

def _apply_environment_complete_hook():
    """Patch V1ProvenanceStore to fire environment_complete record when
    the agent banks the end state.

    The hook is called by the batch runner immediately after
    agent.end_state_banked becomes True. The provenance store's
    existing record structure is extended with one new flag_type:
    'environment_complete'. The record carries:
      completion_step, end_state_banked_step, steps_since_activation.
    """
    try:
        from v1_1_provenance import V1ProvenanceStore
    except ImportError:
        return

    def on_end_state_banked(self, step: int) -> None:
        """Fire environment_complete provenance record.

        Called once per run when agent.end_state_banked first becomes
        True. Idempotent — calling more than once has no effect.
        """
        if getattr(self, '_environment_complete_fired', False):
            return

        activation_step = getattr(self._agent, 'activation_step', None)
        steps_since     = (
            step - activation_step
            if activation_step is not None else None
        )

        rec = {
            "flag_type":               "environment_complete",
            "flag_set_step":           step,
            "completion_step":         step,
            "end_state_banked_step":   step,
            "steps_since_activation":  steps_since,
        }

        # Store in provenance substrate under a fixed key
        flag_id = "environment_complete:end_state"
        self.flags[flag_id] = rec
        self._environment_complete_fired = True

    V1ProvenanceStore.on_end_state_banked = on_end_state_banked


_apply_environment_complete_hook()
