"""
v1_0_recorder.py
----------------
v1.0 heavy instrumentation: per-snapshot recording at cross-layer
coupling moments. Implements the recording-layer specification in
Section 3 of the v1.0 pre-registration.

DESIGN DISCIPLINE
-----------------
The recorder is a separate layer with read-only access to the agent
and world. It does not modify any architectural state, action-selection
logic, drive computation, or update rule. With recording disabled
(the default), the v0.14 behaviour is bit-for-bit identical to the
existing v0.14 batches. With recording enabled, the only side effect
is the accumulation of snapshot rows in memory and their serialisation
to a per-snapshot CSV at run completion.

COUPLING MOMENT CLASSES (pre-reg Section 3.1)
---------------------------------------------
Six classes, each defined unambiguously in terms of architectural
events:

  ATTRACTOR_BANKING       — third entry to an attractor cell
                            (mastery_flag transitions 0 -> 1)
  CELL_TYPE_TRANSITION    — competency reaches a hazard cell's
                            threshold; cell_type transitions
                            HAZARD -> KNOWLEDGE
  KNOWLEDGE_BANKING       — third post-transition entry to a
                            knowledge cell (knowledge_banked
                            transitions False -> True)
  THREAT_FLAG_CLEAR       — threat_flag transitions 1 -> 0 at
                            knowledge banking; co-occurs with
                            KNOWLEDGE_BANKING but recorded
                            separately for clarity
  END_STATE_ACTIVATION    — amended end-state activation signal
                            first fires (all_attractors_mastered
                            AND all_hazards_banked_as_knowledge)
  END_STATE_BANKING       — first entry to the end-state cell
                            post-activation

Maximum coupling moments per run: 5 + 5 + 5 + 5 + 1 + 1 = 22.
Each moment produces three snapshots (before, at, after), so per-run
snapshot count is bounded at 66.

SNAPSHOT TRIPLE MECHANICS
-------------------------
"Step before" cannot be captured proactively because most coupling
events are not predictable from the prior step's state alone. The
recorder maintains a one-step-buffered pre-event state, captured at
each step's pre-action moment and overwritten as the step progresses.
When a coupling event fires inside record_action_outcome, the buffered
pre-event state is materialised as the "before" snapshot, the at-event
state is captured immediately, and a flag is set to capture the
"after" snapshot at the next step's pre-action moment.

This produces snapshot triples whose timing relative to the coupling
event is:
  before:  the action-selection state at step N (the step preceding
           the event)
  at:      the post-event state at step N (the moment the event fires)
  after:   the action-selection state at step N+1 (the step following
           the event)

"Action-selection state" means the state available at the start of
choose_action: drive-weighted scores, Q-values, primitive bias,
preferences, gate exclusion set, threat-flag state, cell-type state.
"Post-event state" means the same fields evaluated immediately after
the event has updated the relevant agent/world state.

Multiple coupling events in the same step are recorded as separate
event entries; their "before" snapshots share the buffered pre-event
state from that step (because the step's action selection happened
once); their "at" snapshots reflect the cumulative state after each
event fires in the order the agent's main loop fires them; their
"after" snapshots are captured at the next step.

OUTPUT
------
The recorder serialises snapshots to a CSV with one row per snapshot.
Variable-length fields use pipe-separated string encoding parallel to
the v0.14 metric conventions. The schema is documented in
SNAPSHOT_FIELDS below.
"""

from __future__ import annotations

import csv
from typing import List, Dict, Optional, Tuple, Any
import numpy as np

# Cell-type constants imported lazily to avoid circular import at
# module load. The recorder is given the constants by the caller.


# Snapshot CSV schema. Column order is fixed; adding a column requires
# a pre-registration amendment under Section 8 of the v1.0 pre-reg.
SNAPSHOT_FIELDS = [
    # Run identification
    "arch", "hazard_cost", "num_steps", "run_idx", "seed",
    # Snapshot identification
    "step", "event_idx", "event_class", "snapshot_position",
    # Agent state
    "agent_x", "agent_y",
    "phase",
    # Drive-weighted scores per candidate action (4 cardinal directions)
    "drive_score_a0", "drive_score_a1", "drive_score_a2", "drive_score_a3",
    # Q-values per cardinal action
    "q_a0", "q_a1", "q_a2", "q_a3",
    # Primitive bias per cardinal action
    "prim_a0", "prim_a1", "prim_a2", "prim_a3",
    # Preferences over the relevant cell set, pipe-encoded
    # "cell:preference|cell:preference|..."
    "preferences",
    # Gate exclusion set, pipe-encoded coordinate list
    "gate_excluded_cells",
    # Threat-flag state per hazard/knowledge cell, pipe-encoded
    # "cell:flag|cell:flag|..."
    "threat_flags",
    # Cell-type state per cell, pipe-encoded "cell:type|cell:type|..."
    "cell_types",
    # Event-specific payload (the cell at the heart of this event,
    # if applicable; empty for system-level events)
    "event_cell",
    # Mastery state at this snapshot
    "mastery_count",
    "knowledge_banked_count",
    # End-state state at this snapshot
    "activation_step",
    "end_state_banked",
]


# Coupling-moment class strings (used in event_class column)
EVT_ATTRACTOR_BANKING = "ATTRACTOR_BANKING"
EVT_CELL_TYPE_TRANSITION = "CELL_TYPE_TRANSITION"
EVT_KNOWLEDGE_BANKING = "KNOWLEDGE_BANKING"
EVT_THREAT_FLAG_CLEAR = "THREAT_FLAG_CLEAR"
EVT_END_STATE_ACTIVATION = "END_STATE_ACTIVATION"
EVT_END_STATE_BANKING = "END_STATE_BANKING"

# Snapshot position strings (used in snapshot_position column)
POS_BEFORE = "before"
POS_AT = "at"
POS_AFTER = "after"


class V1Recorder:
    """Heavy instrumentation recorder for the v1.0 batch.

    Hooked into the agent's main loop at three places:
      1. Before choose_action (pre-action): capture pre-event state
         into the buffer; if the previous step fired any coupling
         events, materialise their "after" snapshots from the current
         pre-action state.
      2. After record_action_outcome (post-event): if any coupling
         events fired during this step, materialise their "before"
         snapshots from the buffered pre-action state and their "at"
         snapshots from the current post-event state.
      3. At run end: serialise accumulated snapshots to CSV.

    The recorder is given the agent and world references at
    construction; it reads their state without modification.
    """

    def __init__(self, agent, world, run_metadata: Dict[str, Any],
                 cell_type_constants: Dict[str, int]):
        self.agent = agent
        self.world = world
        self.run_metadata = run_metadata  # arch, hazard_cost, num_steps, run_idx, seed
        self.constants = cell_type_constants  # FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE

        # Accumulated snapshots, materialised to CSV at run end.
        self.snapshots: List[Dict[str, Any]] = []

        # Buffer for pre-action state at the current step. Updated at
        # each step's pre-action moment; consulted when coupling events
        # fire later in the step.
        self._pre_action_buffer: Optional[Dict[str, Any]] = None
        self._pre_action_step: Optional[int] = None

        # Pending "after" snapshots: events fired in the previous step
        # whose "after" snapshots have not yet been captured. Each
        # entry is a tuple (event_class, event_cell, event_idx).
        self._pending_after: List[Tuple[str, Optional[Tuple[int, int]], int]] = []

        # Event index counter for ordering snapshots within a run.
        self._event_counter = 0

        # Per-step event buffer: events fired during the current step,
        # cleared and processed at the post-event hook.
        self._step_events: List[Tuple[str, Optional[Tuple[int, int]]]] = []

        # Watch state: snapshots of agent state we read at the start of
        # the step, used to detect what changed after record_action_outcome.
        self._step_start_mastery: Optional[Dict[Tuple[int, int], int]] = None
        self._step_start_knowledge_unlocked: Optional[Dict[Tuple[int, int], bool]] = None
        self._step_start_knowledge_banked: Optional[Dict[Tuple[int, int], bool]] = None
        self._step_start_threat_flags: Optional[Dict[Tuple[int, int], int]] = None
        self._step_start_activation_step: Optional[int] = None
        self._step_start_end_state_banked: Optional[bool] = None

    # ------------------------------------------------------------------
    # State capture helpers
    # ------------------------------------------------------------------

    def _capture_state(self, step: int, position: str,
                       event_class: str = "",
                       event_cell: Optional[Tuple[int, int]] = None,
                       event_idx: int = -1) -> Dict[str, Any]:
        """Capture the full snapshot fields. Reads agent and world state
        without modification. Returns a dict matching SNAPSHOT_FIELDS."""
        agent = self.agent
        world = self.world

        # Agent's current state tuple as observe() produces it.
        state = world.observe()
        agent_x, agent_y = state[0], state[1]

        # Drive-weighted scores: for each candidate action, compute the
        # sum of (drive weight * drive value) for the resulting cell.
        # Implemented by simulating what each action would target and
        # querying the agent's drive functions for that next-state.
        drive_scores = self._compute_drive_scores(state)

        # Q-values per cardinal action at the current state.
        q_values = [agent.q_values[(state, a)] for a in range(4)]

        # Primitive bias per cardinal action at the current state.
        primitive_bias = agent._primitive_bias(state).tolist()

        # Preferences over the relevant cell set: current cell, four
        # adjacent cells, six attractor cells, five hazard/knowledge
        # cells, end-state cell.
        preferences = self._capture_preferences()

        # Gate exclusion set: the cells currently excluded by
        # _action_is_gated. Computed by checking each adjacent cell.
        gate_excluded = self._capture_gate_exclusions(state)

        # Threat-flag state per hazard/knowledge cell.
        threat_flags = self._capture_threat_flags()

        # Cell-type state per cell of interest.
        cell_types = self._capture_cell_types()

        # Mastery and knowledge counts at this snapshot.
        mastery_count = sum(agent.mastery_flag.values())
        knowledge_banked_count = sum(
            1 for v in agent.knowledge_banked.values() if v
        )

        return {
            "arch": self.run_metadata.get("arch", "v1_0"),
            "hazard_cost": self.run_metadata.get("hazard_cost"),
            "num_steps": self.run_metadata.get("num_steps"),
            "run_idx": self.run_metadata.get("run_idx"),
            "seed": self.run_metadata.get("seed"),
            "step": step,
            "event_idx": event_idx,
            "event_class": event_class,
            "snapshot_position": position,
            "agent_x": agent_x,
            "agent_y": agent_y,
            "phase": agent.phase,
            "drive_score_a0": drive_scores[0],
            "drive_score_a1": drive_scores[1],
            "drive_score_a2": drive_scores[2],
            "drive_score_a3": drive_scores[3],
            "q_a0": q_values[0],
            "q_a1": q_values[1],
            "q_a2": q_values[2],
            "q_a3": q_values[3],
            "prim_a0": primitive_bias[0],
            "prim_a1": primitive_bias[1],
            "prim_a2": primitive_bias[2],
            "prim_a3": primitive_bias[3],
            "preferences": preferences,
            "gate_excluded_cells": gate_excluded,
            "threat_flags": threat_flags,
            "cell_types": cell_types,
            "event_cell": str(event_cell) if event_cell is not None else "",
            "mastery_count": mastery_count,
            "knowledge_banked_count": knowledge_banked_count,
            "activation_step": (agent.activation_step
                                if agent.activation_step is not None
                                else ""),
            "end_state_banked": int(agent.end_state_banked),
        }

    def _compute_drive_scores(self, state: Tuple) -> List[float]:
        """Compute the drive-weighted score for each cardinal action's
        target cell. The drive-weighted score is the sum of drive-
        weighted contributions to the agent's intrinsic reward at the
        next state, parallel to the intrinsic reward computation in the
        agent's main loop but simulated for each candidate action.

        We compute: novelty_reward + learning_progress + preference_reward
        + feature_reward, evaluated at the next state each action would
        produce. We do NOT subtract cost (cost is only known after the
        step is taken in the actual world step). The score reflects what
        the drive composition pulls the agent toward, which is the
        relevant quantity for cross-layer coupling characterisation.
        """
        agent = self.agent
        world = self.world
        scores: List[float] = []
        x, y = state[0], state[1]
        action_targets = [
            (x, y - 1),  # action 0
            (x, y + 1),  # action 1
            (x - 1, y),  # action 2
            (x + 1, y),  # action 3
        ]
        size = world.size
        for action, target in enumerate(action_targets):
            if not (0 <= target[0] < size and 0 <= target[1] < size):
                # Out-of-bounds: would be FRAME-blocked; agent stays put
                # for the next-state simulation.
                next_cell = (x, y)
            else:
                target_type = world.cell_type.get(target,
                                                   self.constants["FRAME"])
                if target_type == self.constants["FRAME"]:
                    next_cell = (x, y)
                else:
                    next_cell = target
            # Build the next_state tuple as the agent would observe it.
            ctype = world.cell_type[next_cell]
            adj = world.perceive_adjacent(next_cell)
            next_state = (next_cell[0], next_cell[1], ctype, *adj)
            # Compute drive-weighted contributions at the simulated
            # next state. These call the agent's reward functions
            # without modifying state (the functions are read-only with
            # respect to the agent's tables; visit_counts and similar
            # are read but not written by the reward functions).
            r_novelty = agent.novelty_reward(next_state)
            r_progress = agent.learning_progress(state, action)
            r_preference = agent.preference_reward(next_state)
            r_feature = agent.feature_reward(next_state)
            scores.append(r_novelty + r_progress + r_preference + r_feature)
        return scores

    def _capture_preferences(self) -> str:
        """Capture preferences over the relevant cell set. The set is:
        agent's current cell, four adjacent cells, six attractor cells,
        five hazard/knowledge cells, end-state cell. Encoded as
        pipe-separated 'cell:preference' tokens."""
        agent = self.agent
        world = self.world
        x, y = world.agent_pos

        cells_of_interest = set()
        cells_of_interest.add((x, y))
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            adj = (x + dx, y + dy)
            if 0 <= adj[0] < world.size and 0 <= adj[1] < world.size:
                cells_of_interest.add(adj)
        cells_of_interest.update(world.attractor_cells)
        cells_of_interest.update(world.hazard_cells)
        cells_of_interest.add(world.end_state_cell)

        # Sort for deterministic output.
        sorted_cells = sorted(cells_of_interest)
        return "|".join(
            f"{c}:{agent.cell_preference[c]:.4f}"
            for c in sorted_cells
        )

    def _capture_gate_exclusions(self, state: Tuple) -> str:
        """Capture the set of adjacent target cells the action-selection
        hard-gate currently excludes. For each cardinal action, check
        whether _action_is_gated returns True; if so, record the target
        cell."""
        agent = self.agent
        excluded = []
        for action in range(4):
            if agent._action_is_gated(state, action):
                target = agent._get_destination_cell(state, action)
                if target is not None:
                    excluded.append(target)
        return "|".join(str(c) for c in excluded)

    def _capture_threat_flags(self) -> str:
        """Capture threat_flag for each hazard/knowledge cell."""
        agent = self.agent
        world = self.world
        sorted_hazards = sorted(world.hazard_cells)
        return "|".join(
            f"{c}:{agent.threat_flag.get(c, 0)}"
            for c in sorted_hazards
        )

    def _capture_cell_types(self) -> str:
        """Capture cell_type for each hazard/knowledge cell, each
        attractor (with its mastery state), and the end-state cell.
        Encoded as 'cell:type_string' where type_string is the
        symbolic type name."""
        agent = self.agent
        world = self.world
        type_names = {v: k for k, v in self.constants.items()}

        cells_of_interest = sorted(world.hazard_cells)
        cells_of_interest += sorted(world.attractor_cells)
        cells_of_interest.append(world.end_state_cell)

        tokens = []
        for c in cells_of_interest:
            ct = world.cell_type.get(c, self.constants["FRAME"])
            tn = type_names.get(ct, str(ct))
            # Annotate with banking state for attractors and the
            # end-state cell.
            if c in world.attractor_cells and agent.mastery_flag.get(c, 0) == 1:
                tn = f"{tn}_BANKED"
            elif c == world.end_state_cell and agent.end_state_banked:
                tn = f"{tn}_BANKED"
            elif c in world.hazard_cells and agent.knowledge_banked.get(c, False):
                tn = f"{tn}_BANKED"
            tokens.append(f"{c}:{tn}")
        return "|".join(tokens)

    # ------------------------------------------------------------------
    # Hook points called from the agent's main loop
    # ------------------------------------------------------------------

    def on_pre_action(self, step: int):
        """Called before agent.choose_action at each step.

        Two responsibilities:
          (1) Materialise any pending "after" snapshots from the
              previous step's coupling events, using the current
              pre-action state (which is the step-after state for those
              events).
          (2) Capture the pre-action state into the buffer for use by
              any coupling events that fire during this step.
        """
        # (1) Materialise pending "after" snapshots.
        if self._pending_after:
            for event_class, event_cell, event_idx in self._pending_after:
                snapshot = self._capture_state(
                    step=step,
                    position=POS_AFTER,
                    event_class=event_class,
                    event_cell=event_cell,
                    event_idx=event_idx,
                )
                self.snapshots.append(snapshot)
            self._pending_after = []

        # (2) Capture pre-action state into the buffer.
        self._pre_action_buffer = self._capture_state(
            step=step,
            position=POS_BEFORE,
            event_class="",  # filled in when event fires
            event_cell=None,  # filled in when event fires
            event_idx=-1,  # filled in when event fires
        )
        self._pre_action_step = step

        # Snapshot the agent's pre-event state for delta-detection
        # in on_post_event. Shallow copies are sufficient because the
        # agent's mastery_flag, knowledge_banked, etc. are flat dicts
        # of primitives.
        self._step_start_mastery = dict(self.agent.mastery_flag)
        self._step_start_knowledge_unlocked = dict(
            self.world.knowledge_unlocked
        )
        self._step_start_knowledge_banked = dict(
            self.agent.knowledge_banked
        )
        self._step_start_threat_flags = dict(self.agent.threat_flag)
        self._step_start_activation_step = self.agent.activation_step
        self._step_start_end_state_banked = self.agent.end_state_banked

    def on_post_event(self, step: int):
        """Called after agent.record_action_outcome at each step.

        Responsibilities:
          (1) Detect which coupling events (if any) fired during this
              step by diffing the pre-step state against the current
              state.
          (2) For each event detected, materialise a "before" snapshot
              from the buffered pre-action state (with event metadata
              filled in) and an "at" snapshot from the current post-
              event state.
          (3) Queue the events for "after" snapshot capture at the
              next step's pre-action hook.

        Multiple events can fire in the same step. They are recorded
        in a deterministic order: attractor banking first, cell-type
        transition second, knowledge banking third, threat-flag clear
        fourth (co-occurs with knowledge banking), end-state activation
        fifth, end-state banking sixth. This ordering matches the order
        in which the agent's record_action_outcome processes them.
        """
        events: List[Tuple[str, Optional[Tuple[int, int]]]] = []

        # Detect attractor banking (mastery_flag transitions 0 -> 1).
        for cell in self.agent.mastery_flag:
            before = self._step_start_mastery.get(cell, 0)
            after = self.agent.mastery_flag.get(cell, 0)
            if before == 0 and after == 1:
                events.append((EVT_ATTRACTOR_BANKING, cell))

        # Detect cell-type transition (knowledge_unlocked transitions
        # False -> True). The world's record is canonical.
        for cell in self.world.knowledge_unlocked:
            before = self._step_start_knowledge_unlocked.get(cell, False)
            after = self.world.knowledge_unlocked.get(cell, False)
            if not before and after:
                events.append((EVT_CELL_TYPE_TRANSITION, cell))

        # Detect knowledge banking (knowledge_banked transitions
        # False -> True).
        for cell in self.agent.knowledge_banked:
            before = self._step_start_knowledge_banked.get(cell, False)
            after = self.agent.knowledge_banked.get(cell, False)
            if not before and after:
                events.append((EVT_KNOWLEDGE_BANKING, cell))
                # Threat-flag clear co-occurs with knowledge banking
                # by the v0.14 banking rule. Verify and record as a
                # separate event for clarity.
                tf_before = self._step_start_threat_flags.get(cell, 0)
                tf_after = self.agent.threat_flag.get(cell, 0)
                if tf_before == 1 and tf_after == 0:
                    events.append((EVT_THREAT_FLAG_CLEAR, cell))

        # Detect end-state activation (activation_step transitions
        # None -> int).
        if (self._step_start_activation_step is None
                and self.agent.activation_step is not None):
            events.append((EVT_END_STATE_ACTIVATION, self.world.end_state_cell))

        # Detect end-state banking (end_state_banked transitions
        # False -> True).
        if (not self._step_start_end_state_banked
                and self.agent.end_state_banked):
            events.append((EVT_END_STATE_BANKING, self.world.end_state_cell))

        # If no events fired this step, no snapshots to record.
        if not events:
            return

        # For each event, record before, at; queue after.
        for event_class, event_cell in events:
            self._event_counter += 1
            event_idx = self._event_counter

            # "before" snapshot: copy the buffered pre-action state and
            # fill in event metadata.
            if self._pre_action_buffer is not None:
                before_snapshot = dict(self._pre_action_buffer)
                before_snapshot["event_class"] = event_class
                before_snapshot["event_cell"] = (str(event_cell)
                                                 if event_cell is not None
                                                 else "")
                before_snapshot["event_idx"] = event_idx
                # The buffered step is the same as the current step
                # because the pre-action hook fired at the start of
                # this step; assert for clarity.
                assert before_snapshot["step"] == step, (
                    f"pre-action buffer step mismatch: "
                    f"buffer={before_snapshot['step']}, current={step}"
                )
                self.snapshots.append(before_snapshot)

            # "at" snapshot: capture the current state with event
            # metadata.
            at_snapshot = self._capture_state(
                step=step,
                position=POS_AT,
                event_class=event_class,
                event_cell=event_cell,
                event_idx=event_idx,
            )
            self.snapshots.append(at_snapshot)

            # Queue "after" for the next pre-action hook.
            self._pending_after.append(
                (event_class, event_cell, event_idx)
            )

    def on_run_end(self, step: int):
        """Called at run end. If any events fired in the final step,
        their "after" snapshots cannot be captured (no subsequent step
        exists). Flush the pending list as a degenerate-after capture
        from the final state."""
        if self._pending_after:
            for event_class, event_cell, event_idx in self._pending_after:
                snapshot = self._capture_state(
                    step=step,
                    position=POS_AFTER,
                    event_class=event_class,
                    event_cell=event_cell,
                    event_idx=event_idx,
                )
                # Mark as final-step degenerate capture by suffixing
                # the position. Analysis can filter on this.
                snapshot["snapshot_position"] = POS_AFTER + "_final"
                self.snapshots.append(snapshot)
            self._pending_after = []

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def write_csv(self, path: str, append: bool = False):
        """Serialise accumulated snapshots to CSV. Header written only
        on first call (or when append=False). Subsequent calls with
        append=True append rows without rewriting the header."""
        mode = "a" if append else "w"
        write_header = not append
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SNAPSHOT_FIELDS)
            if write_header:
                writer.writeheader()
            for row in self.snapshots:
                writer.writerow({k: row.get(k, "") for k in SNAPSHOT_FIELDS})

    def snapshot_count(self) -> int:
        return len(self.snapshots)

    def reset(self):
        """Clear accumulated snapshots. Called between runs to free
        memory; the CSV writer should be called before reset."""
        self.snapshots = []
        self._pre_action_buffer = None
        self._pending_after = []
        self._event_counter = 0
