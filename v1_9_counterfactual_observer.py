"""
v1_9_counterfactual_observer.py
--------------------------------
V19CounterfactualObserver: the ninth cognitive component. The eighth
parallel observer in the programme's observer stack.

Responsibility: detect suppressed-approach events — where the agent
came within eligible-object proximity and withdrew without contact —
and record each event in the counterfactual substrate.

ARCHITECTURAL ROLE
The counterfactual observer is the first component in the programme
that records what the agent could have done and did not. Prior
iterations record encounters, mastery, prediction errors, and goals.
This layer records the approach that did not complete: a datum in the
agent's developmental arc that is absent from all prior substrates.

In Winnicottian object-relations terms, the suppressed approach is the
moment the object remained not-yet-self — held at a distance the agent
did not close. The register now holds that distance as a datum.

DETECTION METHOD
Positional trajectory, not threat-gate introspection. At each step the
observer computes Euclidean distance from agent to every eligible
object. A suppressed approach is confirmed when:

  1. N_APPROACH = 10 consecutive steps of monotonically decreasing
     distance (approach window).
  2. No contact during or after the approach window.
  3. N_RECESSION = 5 consecutive steps of monotonically increasing
     distance (recession window).

These thresholds are committed in the pre-registration and are not
free parameters. If Level 11 Criterion 6 fails (zero events across
all 10 verification runs), a pre-registration amendment is required
before adjustment.

ELIGIBLE OBJECTS
  - HAZARD-type objects (costly, precondition-gated)
  - DIST_OBJ (distal colour cell) that is the active goal target's
    family distal object (goal type locate_family only)

ATTRACTOR, NEUTRAL, END_STATE, and KNOWLEDGE objects are not eligible.

ADDITIVE DISCIPLINE
With counterfactual_obs=None in build_bundle_from_observers(), output
is byte-identical to v1.8.2 at matched seeds. Verified at Level 11
with --no-counterfactual flag.

OBSERVER PATTERN
  on_pre_action(step)  — no-op (no state emitted before action)
  on_post_event(step)  — updates distance buffers, checks for
                         confirmed suppressed-approach events
  on_run_end(steps)    — finalises any open approach windows
  get_substrate()      — returns list of suppressed-approach records
"""

import math
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Detection thresholds (pre-registered, not free parameters)
# ---------------------------------------------------------------------------

N_APPROACH  = 3    # consecutive steps of decreasing distance required
                   # v1.9.1 amendment: reduced from 10 (pre-registered).
                   # V17World continuous-space trajectories do not produce
                   # 10-step monotone approach windows at this action
                   # granularity. See v1_9_1_amendment.md.
N_RECESSION = 3    # consecutive steps of increasing distance to confirm
                   # v1.9.1 amendment: reduced from 5 to 3 (symmetric).

# ---------------------------------------------------------------------------
# CSV field definitions
# ---------------------------------------------------------------------------

COUNTERFACTUAL_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "object_id",
    "closest_approach_step",
    "closest_approach_distance",
    "phase_at_approach",
    "goal_relevant",
    "pre_threshold_entries",
]


class V19CounterfactualObserver:
    """Eighth parallel observer. Detects suppressed-approach events.

    Parameters
    ----------
    agent : V17Agent
        The agent instance for this run. Used to read phase,
        pre_transition_hazard_entries, and perception_radius.
    world : V17World
        The world instance. Used to read agent_pos, object_positions,
        object_type, and _contact_at_pos().
    run_meta : dict
        Standard run metadata (arch, run_idx, seed, hazard_cost,
        num_steps).
    goal_obs : V18GoalObserver or None
        The active goal observer, for goal-relevance tagging. Read-only.
        None if goal layer is disabled.
    """

    def __init__(self, agent, world, run_meta: Dict[str, Any],
                 goal_obs=None):
        self._agent    = agent
        self._world    = world
        self._meta     = run_meta
        self._goal_obs = goal_obs

        # Per-object distance-window state
        # Keys: object_id strings
        # Values: _ObjectWindow instances
        self._windows: Dict[str, "_ObjectWindow"] = {}

        # Confirmed suppressed-approach records (emitted)
        self._records: List[Dict[str, Any]] = []

        # Cache of eligible object ids — populated at first on_post_event
        self._eligible_ids: Optional[frozenset] = None

    # ------------------------------------------------------------------
    # Hook methods
    # ------------------------------------------------------------------

    def on_pre_action(self, step: int) -> None:
        """No-op. Detection runs on post-event."""
        pass

    def on_post_event(self, step: int) -> None:
        """Update distance buffers; fire confirmed suppressed approaches."""
        eligible = self._get_eligible_ids()
        if not eligible:
            return

        agent_pos = self._world.agent_pos
        contact   = self._world._contact_at_pos(agent_pos)

        for oid in eligible:
            pos = self._get_object_pos(oid)
            if pos is None:
                continue

            dist = _euclidean(agent_pos, pos)

            # Initialise window on first encounter
            if oid not in self._windows:
                self._windows[oid] = _ObjectWindow(oid)

            window = self._windows[oid]

            # If contact was made this step, reset the window — the
            # approach completed; this is not a suppressed approach.
            if contact == oid:
                window.reset()
                continue

            # Update window; collect any confirmed record
            record = window.update(step, dist, self._agent, self._world,
                                   self._goal_obs)
            if record is not None:
                self._records.append(record)

    def on_run_end(self, total_steps: int) -> None:
        """Finalise any open approach windows at run end.

        An open approach window at run end — where the agent was
        approaching an object when the run concluded — is not a
        confirmed suppressed approach (the recession phase was never
        observed). These are silently discarded; only confirmed
        approach-then-recession events are recorded.
        """
        # No action required: _ObjectWindow only emits records when the
        # full approach-then-recession signature is confirmed.
        pass

    # ------------------------------------------------------------------
    # Substrate interface
    # ------------------------------------------------------------------

    def get_substrate(self) -> List[Dict[str, Any]]:
        """Return list of confirmed suppressed-approach records.

        Returns an empty list if no suppressed approaches were detected.
        Never returns None — the field is always a list.
        """
        return list(self._records)

    def counterfactual_rows(self) -> List[Dict[str, Any]]:
        """Return one CSV-ready dict per confirmed event."""
        rows = []
        for rec in self._records:
            rows.append({
                "arch":                     self._meta.get("arch", "v1_9"),
                "run_idx":                  self._meta.get("run_idx"),
                "seed":                     self._meta.get("seed"),
                "hazard_cost":              self._meta.get("hazard_cost"),
                "num_steps":                self._meta.get("num_steps"),
                "object_id":                rec["object_id"],
                "closest_approach_step":    rec["closest_approach_step"],
                "closest_approach_distance": rec["closest_approach_distance"],
                "phase_at_approach":        rec["phase_at_approach"],
                "goal_relevant":            rec["goal_relevant"],
                "pre_threshold_entries":    rec["pre_threshold_entries"],
            })
        return rows

    # ------------------------------------------------------------------
    # Eligible object resolution
    # ------------------------------------------------------------------

    def _get_eligible_ids(self) -> frozenset:
        """Return frozenset of eligible object_ids for this run.

        Computed once and cached. Eligible objects:
          - HAZARD-type (any object whose world.object_type is HAZARD)
          - Goal-relevant DIST_OBJ (if goal is locate_family and the
            distal object for the target family is present)

        KNOWLEDGE-state objects were previously HAZARD — exclude them:
        once transformed, the object is no longer costly and the
        developmental significance of approach changes.
        """
        if self._eligible_ids is not None:
            return self._eligible_ids

        from curiosity_agent_v1_7_world import HAZARD, DIST_OBJ

        eligible = set()

        # All currently-HAZARD objects
        for oid, otype in self._world.object_type.items():
            if otype == HAZARD:
                eligible.add(oid)

        # Goal-relevant DIST_OBJ (locate_family goals only)
        if self._goal_obs is not None:
            gs = self._goal_obs._goal_set_record
            if gs is not None and gs.get("goal_type") == "locate_family":
                colour   = gs["target_id"].lower()   # "green" or "yellow"
                dist_oid = f"dist_{colour}"
                if (dist_oid in self._world.object_type
                        and self._world.object_type[dist_oid] == DIST_OBJ):
                    eligible.add(dist_oid)

        self._eligible_ids = frozenset(eligible)
        return self._eligible_ids

    def _get_object_pos(self, oid: str):
        """Return position of object_id from world, or None if absent."""
        # V17World stores positions in object_positions dict
        positions = getattr(self._world, 'object_positions', {})
        return positions.get(oid)


# ---------------------------------------------------------------------------
# Per-object sliding window
# ---------------------------------------------------------------------------

class _ObjectWindow:
    """Tracks the approach-recession signature for one object.

    State machine:
      IDLE        — no approach in progress
      APPROACHING — N_APPROACH or more steps of decreasing distance
                    observed; waiting for either contact or recession
      RECEDING    — recession steps accumulating after approach

    Transitions:
      IDLE → APPROACHING : when a new monotone-decrease run reaches
                           N_APPROACH steps
      APPROACHING → RECEDING : when distance increases for the first
                               time after the approach window
      APPROACHING → IDLE  : on contact (approach completed — reset)
      RECEDING → IDLE     : on confirmed suppressed approach (N_RECESSION
                            recession steps reached) — emits record
      RECEDING → APPROACHING : if distance decreases again mid-recession
                               (approach resumed — discard partial recession,
                               continue as a new approach from current min)
    """

    _IDLE       = "IDLE"
    _APPROACHING = "APPROACHING"
    _RECEDING   = "RECEDING"

    def __init__(self, oid: str):
        self._oid   = oid
        self._state = self._IDLE

        # Approach window tracking
        self._approach_steps    = 0    # consecutive decreasing steps
        self._prev_dist         = None
        self._min_dist          = None
        self._min_step          = None
        self._phase_at_min      = None

        # Recession window tracking
        self._recession_steps   = 0

    def reset(self):
        """Reset to IDLE — called on contact or contradicted approach."""
        self._state          = self._IDLE
        self._approach_steps = 0
        self._prev_dist      = None
        self._min_dist       = None
        self._min_step       = None
        self._phase_at_min   = None
        self._recession_steps = 0

    def update(self, step: int, dist: float, agent, world,
               goal_obs) -> Optional[Dict[str, Any]]:
        """Process one step. Returns a suppressed-approach record if
        confirmed, else None.
        """
        if self._state == self._IDLE:
            return self._update_idle(step, dist, agent)

        elif self._state == self._APPROACHING:
            return self._update_approaching(step, dist, agent, world,
                                            goal_obs)

        elif self._state == self._RECEDING:
            return self._update_receding(step, dist, agent, world,
                                         goal_obs)

        return None

    def _update_idle(self, step: int, dist: float, agent
                     ) -> None:
        """IDLE: start counting approach steps if distance is decreasing."""
        if self._prev_dist is not None and dist < self._prev_dist:
            self._approach_steps += 1
            if dist < (self._min_dist or math.inf):
                self._min_dist      = dist
                self._min_step      = step
                self._phase_at_min  = getattr(agent, 'phase', 1)
            if self._approach_steps >= N_APPROACH:
                self._state = self._APPROACHING
        else:
            # Distance held or increased — reset counter
            self._approach_steps = 0
            self._min_dist       = None
            self._min_step       = None
            self._phase_at_min   = None

        self._prev_dist = dist
        return None

    def _update_approaching(self, step: int, dist: float, agent,
                             world, goal_obs
                             ) -> Optional[Dict[str, Any]]:
        """APPROACHING: distance was decreasing for N_APPROACH+ steps.
        If it now increases, transition to RECEDING.
        If it continues to decrease, update the minimum.
        """
        if dist < self._prev_dist:
            # Continuing to approach — update minimum
            if dist < self._min_dist:
                self._min_dist     = dist
                self._min_step     = step
                self._phase_at_min = getattr(agent, 'phase', 1)
            self._prev_dist = dist
            return None

        elif dist > self._prev_dist:
            # First recession step — transition to RECEDING
            self._state           = self._RECEDING
            self._recession_steps = 1
            self._prev_dist       = dist
            return None

        else:
            # Distance held exactly — neither approaching nor receding
            self._prev_dist = dist
            return None

    def _update_receding(self, step: int, dist: float, agent,
                          world, goal_obs
                          ) -> Optional[Dict[str, Any]]:
        """RECEDING: counting recession steps.
        If N_RECESSION reached — emit record and reset.
        If distance decreases — approach resumed; treat as continuation.
        """
        if dist > self._prev_dist:
            self._recession_steps += 1
            self._prev_dist = dist

            if self._recession_steps >= N_RECESSION:
                # Confirmed suppressed approach — emit record
                record = self._make_record(agent, world, goal_obs)
                self.reset()
                return record

            return None

        elif dist < self._prev_dist:
            # Agent reversed — approach resumed. Keep the existing min
            # (which is already the closest point) and transition back
            # to APPROACHING to see if a deeper approach develops.
            self._state           = self._APPROACHING
            self._recession_steps = 0
            self._prev_dist       = dist
            return None

        else:
            # Distance held — stay in RECEDING
            self._prev_dist = dist
            return None

    def _make_record(self, agent, world, goal_obs) -> Dict[str, Any]:
        """Construct the suppressed-approach record at confirmation."""
        # pre_threshold_entries: how many times the agent had already
        # paid cost for this object before this approach.
        # Reads agent.pre_transition_hazard_entries (same field used by
        # V18GoalObserver._check_progress for bank_hazard goals).
        pre_entries = getattr(agent, 'pre_transition_hazard_entries', {})
        pre_count   = pre_entries.get(self._oid, 0)

        # goal_relevant: True if this object is the active goal target
        goal_relevant = False
        if goal_obs is not None and goal_obs._goal_set_record is not None:
            gs = goal_obs._goal_set_record
            if gs.get("goal_type") == "bank_hazard_within_budget":
                goal_relevant = (self._oid == gs.get("target_id"))
            elif gs.get("goal_type") == "locate_family":
                colour = gs.get("target_id", "").lower()
                goal_relevant = self._oid in (
                    f"dist_{colour}", f"att_{colour}", f"haz_{colour}"
                )

        return {
            "object_id":                  self._oid,
            "closest_approach_step":      self._min_step,
            "closest_approach_distance":  round(self._min_dist, 6),
            "phase_at_approach":          self._phase_at_min,
            "goal_relevant":              goal_relevant,
            "pre_threshold_entries":      pre_count,
        }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _euclidean(pos_a, pos_b) -> float:
    """Euclidean distance between two position tuples of any dimension."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_a, pos_b)))
