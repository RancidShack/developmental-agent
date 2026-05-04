"""
v1_10_belief_revision_observer.py
-----------------------------------
V110BeliefRevisionObserver: the ninth parallel observer.

Responsibility: fire revised_expectation records after each
resolved_surprise event; maintain a per-object preference-bias
register that modifies the agent's approach behaviour toward revised
objects.

ARCHITECTURAL ROLE
v1.5 recorded the prediction-error surprise. v1.9 recorded restraint
during the resolution window. v1.10 records the revision of behaviour
following resolution. The prediction-surprise mechanism is now
complete at its first layer: prediction, surprise, resolution,
revision, behavioural consequence.

The revised_expectation record is the programme's first statement that
explicitly names what the agent believed before an encounter and what
it now believes. Both beliefs are substrate-derived — constructed from
the provenance substrate and the prediction-error substrate — not
generated freely. Category α requires every prior_expectation and
revised_expectation text to be traceable to specific substrate records.

TRIGGER
A revised_expectation record fires when V15PredictionErrorObserver
fires a resolved_surprise event: the agent made contact with a hazard
object before the precondition was met, and the transformation has
subsequently occurred. Detection is via the prediction-error observer's
get_substrate() — specifically the prediction_error_complete flag and
the per-object resolution records.

PREFERENCE BIAS
After revision fires for object_id, a positive approach bias is
applied: POSITIVE_APPROACH_BIAS = +0.15 added to the agent's intrinsic
reward when moving toward the object. Active for BIAS_DURATION = 10,000
steps, then decays linearly over BIAS_DECAY = 5,000 steps.

These parameters are pre-registered and not free parameters.

APPROACH DELTA
The observer tracks approach-movement counts toward each revised
object in two windows:
  pre-window:  [max(0, surprise_step - BIAS_DURATION), surprise_step)
  post-window: [revision_step, revision_step + BIAS_DURATION)
approach_delta = post_count - pre_count.
Used in the Q3 belief-revision statement.

ADDITIVE DISCIPLINE
With belief_revision_obs=None in build_bundle_from_observers(), all
existing outputs are byte-identical to v1.9 at matched seeds.
"""

import math
from typing import Any, Dict, List, Optional

# Pre-registered parameters
POSITIVE_APPROACH_BIAS = 0.15
BIAS_DURATION          = 10_000
BIAS_DECAY             = 5_000

# CSV field definitions
BELIEF_REVISION_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "object_id",
    "surprise_step",
    "resolution_step",
    "resolution_window",
    "suppressed_approach_count",
    "pre_threshold_entries_at_surprise",
    "bias_active_steps",
    "approach_delta",
]


class V110BeliefRevisionObserver:
    """Ninth parallel observer. Fires revised_expectation records and
    manages preference bias.

    Parameters
    ----------
    agent : V110Agent
        The agent instance. Read-only access to phase,
        pre_transition_hazard_entries, activation_step.
    world : V17World
        The world instance. Read-only access to agent_pos,
        object_positions.
    run_meta : dict
        Standard run metadata.
    prediction_error_obs : V15PredictionErrorObserver
        The prediction-error observer. Read at on_post_event to detect
        new resolved_surprise events.
    provenance_obs : V1ProvenanceStore
        The provenance observer. Read at revision time to construct
        revised_expectation text from mastery formation records.
    counterfactual_obs : V19CounterfactualObserver or None
        The counterfactual observer. Read at revision time for
        suppressed_approach_count. None if disabled.
    """

    def __init__(self, agent, world, run_meta: Dict[str, Any],
                 prediction_error_obs,
                 provenance_obs,
                 counterfactual_obs=None):
        self._agent              = agent
        self._world              = world
        self._meta               = run_meta
        self._pe_obs             = prediction_error_obs
        self._prov_obs           = provenance_obs
        self._cf_obs             = counterfactual_obs

        # Per-object revised_expectation records (emitted)
        self._records: List[Dict[str, Any]] = []

        # Per-object bias state: {object_id: _BiasWindow}
        self._bias: Dict[str, _BiasWindow] = {}

        # Per-object resolved steps already seen (to avoid re-firing)
        self._resolved_seen: Dict[str, int] = {}

        # Per-object approach-movement counters for approach_delta
        # {object_id: {'pre': count, 'post': count}}
        self._approach_counts: Dict[str, Dict[str, int]] = {}

    # ------------------------------------------------------------------
    # Hook methods
    # ------------------------------------------------------------------

    def on_pre_action(self, step: int) -> None:
        """No-op."""
        pass

    def on_post_event(self, step: int) -> None:
        """Check for new resolved_surprise events; update bias state;
        track approach movements."""
        self._check_new_resolutions(step)
        self._update_approach_counts(step)

    def on_run_end(self, total_steps: int) -> None:
        """Finalise bias_active_steps and approach_delta for all records."""
        for rec in self._records:
            oid    = rec["object_id"]
            bw     = self._bias.get(oid)
            rev_st = rec["resolution_step"]

            # bias_active_steps: steps the bias was > 0
            if bw is not None:
                rec["bias_active_steps"] = bw.active_steps
            else:
                rec["bias_active_steps"] = 0

            # approach_delta
            counts = self._approach_counts.get(oid, {})
            pre    = counts.get("pre", 0)
            post   = counts.get("post", 0)
            rec["approach_delta"] = post - pre

    # ------------------------------------------------------------------
    # Preference bias interface (called by batch runner)
    # ------------------------------------------------------------------

    def preference_bias_reward(self, object_id: str, step: int,
                               moving_closer: bool) -> float:
        """Return preference bias for object_id at this step.

        Called by the batch runner's intrinsic reward calculation for
        each revised object. Returns 0.0 if no bias is active.
        """
        bw = self._bias.get(object_id)
        if bw is None:
            return 0.0
        return bw.get_bias(step) if moving_closer else 0.0

    def active_biased_objects(self, step: int) -> List[str]:
        """Return list of object_ids with active bias at this step."""
        return [oid for oid, bw in self._bias.items()
                if bw.get_bias(step) > 0.0]

    # ------------------------------------------------------------------
    # Substrate interface
    # ------------------------------------------------------------------

    def get_substrate(self) -> List[Dict[str, Any]]:
        """Return list of revised_expectation records."""
        return list(self._records)

    def belief_revision_rows(self) -> List[Dict[str, Any]]:
        """Return CSV-ready dicts for belief_revision_v1_10.csv."""
        rows = []
        for rec in self._records:
            rows.append({
                "arch":         self._meta.get("arch", "v1_10"),
                "run_idx":      self._meta.get("run_idx"),
                "seed":         self._meta.get("seed"),
                "hazard_cost":  self._meta.get("hazard_cost"),
                "num_steps":    self._meta.get("num_steps"),
                "object_id":                   rec["object_id"],
                "surprise_step":               rec["surprise_step"],
                "resolution_step":             rec["resolution_step"],
                "resolution_window":           rec["resolution_window"],
                "suppressed_approach_count":   rec["suppressed_approach_count"],
                "pre_threshold_entries_at_surprise":
                    rec["pre_threshold_entries_at_surprise"],
                "bias_active_steps":           rec.get("bias_active_steps", 0),
                "approach_delta":              rec.get("approach_delta", 0),
            })
        return rows

    # ------------------------------------------------------------------
    # Internal: resolve detection
    # ------------------------------------------------------------------

    def _check_new_resolutions(self, step: int) -> None:
        """Scan prediction-error substrate for new resolved_surprise
        events not yet processed."""
        try:
            pe_sub = self._pe_obs.get_substrate()
        except Exception:
            return

        # pe_sub is a list of prediction-error event dicts.
        # We look for records with event_type == "resolved_surprise"
        # that have a resolution_step <= step and haven't been seen.
        for event in pe_sub:
            if event.get("event_type") != "resolved_surprise":
                continue
            oid      = event.get("object_id", "")
            res_step = event.get("resolution_step")
            surp_step = event.get("surprise_step")
            if res_step is None or surp_step is None:
                continue
            if res_step > step:
                continue
            # Already processed?
            if self._resolved_seen.get(oid) == res_step:
                continue

            # New resolution — fire revised_expectation record
            self._resolved_seen[oid] = res_step
            self._fire_revision(oid, surp_step, res_step, step)

    def _fire_revision(self, oid: str, surprise_step: int,
                       resolution_step: int, step: int) -> None:
        """Construct and store a revised_expectation record."""
        # prior_expectation: default before precondition is known
        prior_text = (
            f"Entry of {oid} leads to transformation."
        )

        # revised_expectation: constructed from provenance substrate
        # Find the precondition attractor mastery step
        precondition_name, mastery_step = self._get_precondition_info(oid)
        if precondition_name and mastery_step is not None:
            revised_text = (
                f"Entry of {oid} requires {precondition_name} mastery "
                f"(achieved at step {mastery_step}). "
                f"Entry before that step incurred the full cost "
                f"without transformation."
            )
        else:
            # Unaffiliated hazard — global competency gate
            revised_text = (
                f"Entry of {oid} requires attractor mastery to reach "
                f"the competency threshold. Entry before that threshold "
                f"incurred the full cost without transformation."
            )

        # suppressed_approach_count: CF records for this oid before
        # resolution_step
        sa_count = self._get_suppressed_approach_count(oid, resolution_step)

        # pre_threshold_entries_at_surprise: prior contacts at
        # surprise_step
        pre_entries = getattr(
            self._agent, 'pre_transition_hazard_entries', {}
        ).get(oid, 0)

        rec = {
            "object_id":                       oid,
            "surprise_step":                   surprise_step,
            "resolution_step":                 resolution_step,
            "resolution_window":               resolution_step - surprise_step,
            "prior_expectation":               prior_text,
            "revised_expectation":             revised_text,
            "precondition_at_revision":        (
                f"{precondition_name} mastered at step {mastery_step}"
                if precondition_name else "global competency threshold"
            ),
            "suppressed_approach_count":       sa_count,
            "pre_threshold_entries_at_surprise": pre_entries,
            "bias_active_steps":               0,   # finalised at on_run_end
            "approach_delta":                  0,   # finalised at on_run_end
        }
        self._records.append(rec)

        # Activate preference bias for this object
        self._bias[oid] = _BiasWindow(
            activation_step=resolution_step,
            duration=BIAS_DURATION,
            decay=BIAS_DECAY,
            bias_value=POSITIVE_APPROACH_BIAS,
        )

        # Initialise approach count tracking
        if oid not in self._approach_counts:
            self._approach_counts[oid] = {"pre": 0, "post": 0}

    def _get_precondition_info(self, oid: str):
        """Return (precondition_name, mastery_step) from provenance.

        Reads the family precondition map from the world to find the
        attractor precondition for this hazard object, then reads the
        mastery formation step from the provenance substrate.
        """
        # World carries family_precondition_attractor:
        # {hazard_pos: attractor_pos} (grid) or
        # {hazard_oid: attractor_oid} (V17World)
        family_preconds = getattr(
            self._world, 'family_precondition_attractor', {}
        )
        precond_key = family_preconds.get(oid)
        if precond_key is None:
            return None, None

        # precond_key is the attractor object_id (e.g. "att_green")
        precondition_name = str(precond_key)

        # Read mastery formation step from provenance substrate
        mastery_step = None
        try:
            prov_sub = self._prov_obs.get_substrate()
            flag_id  = f"mastery:{precond_key}"
            rec      = prov_sub.get(flag_id)
            if rec is not None:
                mastery_step = rec.get("flag_set_step") or rec.get("formation_step")
        except Exception:
            pass

        return precondition_name, mastery_step

    def _get_suppressed_approach_count(self, oid: str,
                                        before_step: int) -> int:
        """Count CF records for oid with closest_approach_step < before_step."""
        if self._cf_obs is None:
            return 0
        try:
            cf_records = self._cf_obs.get_substrate()
            return sum(
                1 for r in cf_records
                if r.get("object_id") == oid
                and r.get("closest_approach_step", before_step) < before_step
            )
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Internal: approach-movement tracking
    # ------------------------------------------------------------------

    def _update_approach_counts(self, step: int) -> None:
        """Track approach movements toward each revised object.

        An approach movement is a step on which the agent's distance to
        the object decreased. Counted in pre-window and post-window for
        each revised object to compute approach_delta at run_end.
        """
        if not self._records:
            return

        agent_pos = getattr(self._world, 'agent_pos', None)
        if agent_pos is None:
            return

        obj_positions = getattr(self._world, 'object_positions', {})

        for rec in self._records:
            oid       = rec["object_id"]
            surp_step = rec["surprise_step"]
            res_step  = rec["resolution_step"]

            obj_pos = obj_positions.get(oid)
            if obj_pos is None:
                continue

            dist = _euclidean(agent_pos, obj_pos)

            # We track the previous distance per object
            key = f"_prev_dist_{oid}"
            prev_dist = getattr(self, key, None)
            if prev_dist is not None and dist < prev_dist:
                # Moving closer — is this in pre or post window?
                pre_start = max(0, surp_step - BIAS_DURATION)
                pre_end   = surp_step
                post_end  = res_step + BIAS_DURATION

                if pre_start <= step < pre_end:
                    self._approach_counts.setdefault(
                        oid, {"pre": 0, "post": 0}
                    )["pre"] += 1
                elif res_step <= step < post_end:
                    self._approach_counts.setdefault(
                        oid, {"pre": 0, "post": 0}
                    )["post"] += 1

            setattr(self, key, dist)


# ---------------------------------------------------------------------------
# Bias window
# ---------------------------------------------------------------------------

class _BiasWindow:
    """Tracks preference bias for one object over time.

    Bias is BIAS_VALUE for DURATION steps after activation_step,
    then decays linearly to zero over DECAY steps.
    """

    def __init__(self, activation_step: int, duration: int,
                 decay: int, bias_value: float):
        self._activation = activation_step
        self._duration   = duration
        self._decay      = decay
        self._value      = bias_value
        self.active_steps = 0

    def get_bias(self, step: int) -> float:
        """Return bias value at this step."""
        elapsed = step - self._activation
        if elapsed < 0:
            return 0.0
        if elapsed < self._duration:
            self.active_steps += 1
            return self._value
        decay_elapsed = elapsed - self._duration
        if decay_elapsed < self._decay:
            fraction = 1.0 - (decay_elapsed / self._decay)
            val = self._value * fraction
            if val > 0:
                self.active_steps += 1
            return val
        return 0.0


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _euclidean(pos_a, pos_b) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_a, pos_b)))
