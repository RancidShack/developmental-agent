"""
v1_3_agent.py
-------------
V13Agent: subclass of V12Agent (which subclasses V014Agent) implementing
family-specific competency gating (v1.3.2 amendment).

The single behavioural change from v1.2/v1.3.1: check_competency_unlocks
is overridden to apply different unlock conditions depending on whether
a hazard cell is family-attributed or unaffiliated.

Family-attributed hazard cells (green sphere at (14,14), yellow pyramid
at (5,8)): transition fires when the precondition attractor for that
family is mastered — mastery_flag[precondition_attractor] == 1. The
global competency threshold is not consulted. The threshold slot is
preserved in world.hazard_competency_thresholds and in the schema, but
it does not govern the transition under this rule (v1.3.2 amendment §3).

Unaffiliated hazard cells: global competency gate unchanged from v0.14.
Transition fires when sum(mastery_flag.values()) >= threshold.

The precondition map is read from world.family_precondition_attractor,
populated by V13World at initialisation. If the world does not carry
this attribute (e.g. in the --no-family regression configuration using
V12World), the method falls back to the global rule for all cells,
preserving byte-identical behaviour in that configuration.

No other method is overridden. Schema construction, drive composition,
action selection, value updates, and all other inherited behaviour are
identical to V12Agent.
"""

from v1_3_schema_extension import V13Agent as _V13SchemaAgent


class V13Agent(_V13SchemaAgent):
    """v1.3.2 agent. Adds family-specific competency gating.

    Inherits from V13Agent in v1_3_schema_extension (which itself
    inherits from V12Agent → V014Agent), adding only the override
    of check_competency_unlocks.
    """

    def check_competency_unlocks(self, step):
        """Family-specific competency gating (v1.3.2 rule).

        For family-attributed hazard cells: transition fires when the
        precondition attractor for that family is mastered.

        For unaffiliated hazard cells: global competency gate from
        v0.14 unchanged.
        """
        # Read family precondition map from world if available.
        # Falls back to empty dict (all cells use global gate) when
        # running with V12World in regression configuration.
        family_preconditions = getattr(
            self.world, 'family_precondition_attractor', {}
        )

        # Global competency — still needed for unaffiliated cells.
        current_competency = sum(self.mastery_flag.values())

        for cell in sorted(self.world.hazard_cells):
            if self.world.knowledge_unlocked.get(cell, False):
                continue

            precondition_attractor = family_preconditions.get(cell)

            if precondition_attractor is not None:
                # Family cell: gate on specific attractor mastery only.
                # The global threshold is not consulted (v1.3.2 rule).
                if self.mastery_flag.get(precondition_attractor, 0) == 1:
                    self.world.transition_hazard_to_knowledge(cell)
                    self.competency_unlock_step[cell] = step
                    self.transition_order_sequence.append(cell)
                    if self.time_to_first_transition is None:
                        self.time_to_first_transition = step
                    self.time_to_final_transition = step
            else:
                # Unaffiliated cell: global competency gate unchanged.
                threshold = self.hazard_competency_thresholds.get(cell)
                if threshold is None:
                    continue
                if current_competency >= threshold:
                    self.world.transition_hazard_to_knowledge(cell)
                    self.competency_unlock_step[cell] = step
                    self.transition_order_sequence.append(cell)
                    if self.time_to_first_transition is None:
                        self.time_to_first_transition = step
                    self.time_to_final_transition = step
