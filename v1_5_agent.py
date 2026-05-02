"""
v1_5_agent.py
-------------
V15Agent: the v1.5 agent.

No behavioural change from v1.4. The v1.5 architectural extension
is the V15PredictionErrorObserver — a sixth parallel observer that
holds live state during the run to record per-encounter prediction-
error events. The agent's action-selection, drive composition, value
functions, schema construction, and competency-gating rule are all
inherited from V14Agent (and through it, V13Agent) unchanged.

V15Agent is provided as a named class for consistency with the
programme's iteration naming convention. Each iteration has a named
agent class.

Inheritance chain:
  V15Agent → V14Agent → V13Agent (v1.3.2 family-specific gating)
                      → V13Agent (v1_3_schema_extension, COLOUR_CELL schema)
                      → V12Agent (v1_2_schema, schema construction)
                      → V014Agent (curiosity_agent_v0_14, base behaviour)

The parallel-observer preservation property holds: with
--no-prediction-error, the v1.5 batch runner produces output
byte-identical to the v1.4 baseline at matched seeds. V15Agent does
not affect this property — it is behaviourally identical to V14Agent.
"""

from v1_4_agent import V14Agent


class V15Agent(V14Agent):
    """v1.5 agent. Inherits V14Agent unchanged.

    No method is overridden. All behaviour — action selection,
    drive composition, value updates, schema construction, and
    family-specific competency gating — is identical to V14Agent.
    """
    pass
