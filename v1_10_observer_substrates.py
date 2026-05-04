"""
v1_10_observer_substrates.py
------------------------------
v1.10 additive patches.

AMENDMENT v1.10.1: corrected self._agent → self.agent in
on_end_state_banked(). V1ProvenanceStore stores its agent reference
as self.agent (no underscore). See v1_10_1_amendment.md.

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
   Monkey-patches V19CounterfactualObserver.on_post_event to apply
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
  - CF records reduced by temporal exclusion window
  - All Q1/Q2/Q4 outputs identical to v1.9 at matched seeds
"""

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

K_EXCLUSION = 500


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
    goal            = None,
    counterfactual  = None,
    belief_revision = None,
):
    _v19_bundle_init(
        self, provenance, schema, family, comparison,
        prediction_error, run_meta, goal, counterfactual
    )
    self.belief_revision = belief_revision


SubstrateBundle.__init__ = _v110_bundle_init


_v19_bundle_resolve = SubstrateBundle.resolve


def _v110_bundle_resolve(self, source_type: str, source_key: str) -> bool:
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
) -> SubstrateBundle:
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
# 2. Reporting layer — Q3 belief-revision statements
# ===========================================================================

_v19_query_where_surprised = V16ReportingLayer.query_where_surprised


def _v110_query_where_surprised(self) -> List[ReportStatement]:
    statements = _v19_query_where_surprised(self)

    bundle = self._bundle
    br_sub = getattr(bundle, 'belief_revision', None)
    if not br_sub:
        return statements

    for rec in br_sub:
        oid            = rec["object_id"]
        surp_step      = rec["surprise_step"]
        res_win        = rec["resolution_window"]
        delta          = rec.get("approach_delta", 0)
        precond_clause = rec.get("precondition_at_revision",
                                  "the precondition")
        bias_dur       = 10_000

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
# 3. Temporal exclusion window
# ===========================================================================

def _apply_temporal_exclusion_window():
    try:
        from v1_9_counterfactual_observer import V19CounterfactualObserver
    except ImportError:
        return

    _original_on_post_event = V19CounterfactualObserver.on_post_event

    def _v110_on_post_event(self, step: int) -> None:
        if not hasattr(self, '_last_emission_step'):
            self._last_emission_step = {}
        if not hasattr(self, '_cf_raw_count'):
            self._cf_raw_count = 0

        count_before = len(self._records)
        _original_on_post_event(self, step)
        count_after  = len(self._records)

        if count_after <= count_before:
            return

        keep = []
        for rec in self._records[count_before:]:
            oid       = rec["object_id"]
            last_step = self._last_emission_step.get(oid)
            if last_step is not None and (step - last_step) < K_EXCLUSION:
                self._cf_raw_count += 1
            else:
                self._last_emission_step[oid] = step
                keep.append(rec)

        self._records = self._records[:count_before] + keep

    V19CounterfactualObserver.on_post_event = _v110_on_post_event

    def _raw_records_count(self) -> int:
        return len(self._records) + getattr(self, '_cf_raw_count', 0)

    V19CounterfactualObserver.raw_records_count = _raw_records_count


_apply_temporal_exclusion_window()


# ===========================================================================
# 4. Environment-complete provenance record
# ===========================================================================

def _apply_environment_complete_hook():
    try:
        from v1_1_provenance import V1ProvenanceStore
    except ImportError:
        return

    def on_end_state_banked(self, step: int) -> None:
        """Fire environment_complete provenance record.

        Called once per run when agent.end_state_banked first becomes
        True. Idempotent.

        v1.10.1: self.agent (not self._agent).
        v1.10.2: ProvenanceRecord dataclass instance (not dict).
        v1.10.3: same — stores steps_since_activation in
        confirming_observations, the only spare integer field on
        the ProvenanceRecord dataclass.
        """
        if getattr(self, '_environment_complete_fired', False):
            return

        from v1_1_provenance import ProvenanceRecord

        activation_step = getattr(self.agent, 'activation_step', None)
        steps_since = (
            step - activation_step
            if activation_step is not None else 0
        )

        flag_id = "environment_complete:end_state"
        rec = ProvenanceRecord(
            flag_type="environment_complete",
            flag_coord=None,
            flag_id=flag_id,
            flag_set_step=step,
            confirming_observations=steps_since,
            last_observation_step=step,
        )
        self.records[flag_id] = rec
        self._environment_complete_fired = True

    V1ProvenanceStore.on_end_state_banked = on_end_state_banked


_apply_environment_complete_hook()
