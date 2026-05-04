"""
v1_10_agent.py
--------------
V110Agent: subclass of V17Agent adding the completion-signal draw
component.

ARCHITECTURAL ROLE
The wait-by-the-door cell is the Montessori prepared environment's
signal to a learner who has completed the current material: the
directress has arranged an inviting terminus. The agent is not
compelled to move there; it is drawn. Whether it responds, and when,
is its own.

In V17World the completion condition is agent.activation_step becoming
non-None (all attractors mastered AND all hazards banked as knowledge).
Prior to v1.10, agents finding the END_STATE cell was entirely
opportunistic: 13/40 v1.9 runs banked the end state, with
end_state_found_step ranging from step 920 to step 310,156. The high-
activity Phase 3 consolidation runs — agents who generated 3,000–7,000
suppressed-approach records orbiting hazard objects — are
overwhelmingly runs in which the end state was never banked.

V110Agent adds one method: end_state_draw_reward(next_state). This
returns END_STATE_DRAW (+0.20) when:
  - agent.activation_step is not None (completion condition met), AND
  - the agent's distance to end_state_cell is decreasing in next_state
    relative to the current state.

The draw is permanent once activated (no decay), soft (0.20 on the
intrinsic scale, below attractor feature rewards of 0.5–2.0), and
additive — it is included in the intrinsic reward calculation by the
batch runner alongside novelty_reward, preference_reward, and
feature_reward.

SUBCLASS PATTERN
The agent subclass chain at v1.10:
  V014Agent → V12Agent → V13Agent (schema/family) → V17Agent → V110Agent

V110Agent overrides nothing in V17Agent except adding
end_state_draw_reward(). All drive composition, action selection,
value updates, phase schedule, and threat/mastery/competency logic
are inherited unchanged.

The batch runner imports V110Agent and instantiates it in place of
V17Agent. With --no-completion-signal the batch runner instantiates
V17Agent directly, producing v1.9-equivalent behaviour.

PARAMETER (pre-registered, not free)
  END_STATE_DRAW = +0.20
"""

import math
from v1_7_agent import V17Agent

END_STATE_DRAW = 0.20   # pre-registered; see v1_10_pre_registration.md


class V110Agent(V17Agent):
    """v1.10 agent. Adds completion-signal draw toward END_STATE cell.

    All behaviour is inherited from V17Agent. The single addition is
    end_state_draw_reward(), called by the batch runner each step
    alongside the existing intrinsic reward components.
    """

    # ------------------------------------------------------------------
    # Completion signal
    # ------------------------------------------------------------------

    def end_state_draw_reward(self, state, next_state) -> float:
        """Return END_STATE_DRAW if moving toward end_state_cell post-
        activation, else 0.0.

        Parameters
        ----------
        state : object
            Current observation (before the step).
        next_state : object
            Next observation (after the step).

        Returns
        -------
        float
            END_STATE_DRAW if the completion condition is met and the
            agent moved closer to the end-state cell this step.
            0.0 otherwise.

        Notes
        -----
        activation_step is set by V17Agent (inherited from the v0.14
        end-state mechanism) when all attractors are mastered AND all
        hazards are banked as knowledge. It remains non-None for the
        rest of the run once set.

        end_state_cell is the world's end-state cell position tuple,
        set at world initialisation.

        Distance is Euclidean over the position tuples. If the world
        does not expose agent_pos or end_state_cell (regression
        configurations), the method returns 0.0 safely.
        """
        # Completion condition not yet met
        if self.activation_step is None:
            return 0.0

        # End state already banked — draw satisfied, no further signal
        if self.end_state_banked:
            return 0.0

        # Read positions safely
        es_pos = getattr(self.world, 'end_state_cell', None)
        if es_pos is None:
            return 0.0

        agent_pos = getattr(self.world, 'agent_pos', None)
        if agent_pos is None:
            return 0.0

        # Current distance to end-state cell
        current_dist = _euclidean(agent_pos, es_pos)

        # Project next position from next_state if available
        # V17World observations encode agent position; if next_state
        # carries agent_pos directly we use it, otherwise we fall back
        # to the world's current agent_pos (already updated by step()).
        next_pos = getattr(self.world, 'agent_pos', None)
        if next_pos is None:
            return 0.0

        next_dist = _euclidean(next_pos, es_pos)

        # Draw fires when moving closer
        if next_dist < current_dist:
            return END_STATE_DRAW

        return 0.0

    # ------------------------------------------------------------------
    # Convenience property
    # ------------------------------------------------------------------

    @property
    def end_state_draw_active(self) -> bool:
        """True from activation_step onward (completion condition met)."""
        return self.activation_step is not None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _euclidean(pos_a, pos_b) -> float:
    """Euclidean distance between two position tuples of any dimension."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_a, pos_b)))
