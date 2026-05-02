"""
v1_4_agent.py
-------------
V14Agent: the v1.4 agent.

No behavioural change from v1.3.2. The v1.4 architectural extension
is the V14ComparisonObserver — a fifth parallel observer that reads
completed family records at run end. The agent's action-selection,
drive composition, value functions, schema construction, and
competency-gating rule are all inherited from V13Agent unchanged.

V14Agent is provided as a named class for two reasons:

  1. Consistency with the programme's iteration naming convention.
     Each iteration has a named agent class. Importing V13Agent
     directly into the v1.4 batch runner would obscure the
     architectural record.

  2. Forward compatibility. If a v1.4 amendment requires a
     behavioural change, the override belongs here rather than
     in v1_3_agent.py.

Inheritance chain:
  V14Agent → V13Agent (v1.3.2 family-specific gating)
           → V13Agent (v1_3_schema_extension, COLOUR_CELL schema)
           → V12Agent (v1_2_schema, schema construction)
           → V014Agent (curiosity_agent_v0_14, base behaviour)

The parallel-observer preservation property holds: with
--no-comparison, the v1.4 batch runner produces output byte-identical
to the v1.3.2 baseline at matched seeds. V14Agent does not affect
this property — it is behaviourally identical to V13Agent.
"""

from v1_3_agent import V13Agent


class V14Agent(V13Agent):
    """v1.4 agent. Inherits V13Agent unchanged.

    No method is overridden. All behaviour — action selection,
    drive composition, value updates, schema construction, and
    family-specific competency gating — is identical to V13Agent.
    """
    pass
