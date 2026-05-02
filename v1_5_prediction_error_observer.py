"""
v1_5_prediction_error_observer.py
-----------------------------------
v1.5 prediction-error observer. The sixth parallel observer in the
programme's observer stack, running alongside the v1.0 recorder,
v1.1 provenance store, v1.2/v1.3 schema observer, v1.3 family observer,
and v1.4 comparison observer.

Responsibility: record each encounter with a hazard cell as a typed
event — resolved_surprise, unresolved_approach, or clean_first_entry —
and compute the resolution window (gap between first pre-transition
approach and eventual HAZARD-to-KNOWLEDGE transformation) for each
family cell.

Unlike the v1.4 comparison observer (which holds no live state and
operates entirely at run end), this observer must hold live state
during the run in order to detect pre-transition approach events
as they occur.

Observer pattern:
  - on_pre_action(step)  — no-op.
  - on_post_event(step)  — core live-state detection. Reads world
                           and agent state after each action to detect
                           hazard entries, precondition status,
                           cost paid, and transformation events.
  - on_run_end(step)     — classifies all recorded approach events
                           into the three encounter types, computes
                           per-run summary fields, and populates
                           output records.
  - with --no-prediction-error, this observer is not instantiated;
    the batch runner produces byte-identical output to v1.4 baseline.

Encounter types (per pre-registration §2.2):

  resolved_surprise:    agent entered a hazard cell before the
                        precondition was met, paid the cost, did not
                        receive the transformation at entry time;
                        the transformation fired later within the run.

  unresolved_approach:  agent entered a hazard cell before the
                        precondition was met, paid the cost, and the
                        transformation did not fire within the run.

  clean_first_entry:    agent entered a hazard cell after the
                        precondition was met; first approach produces
                        the transformation. No prediction error.

Precondition assessment:
  Family cells (green sphere at (14,14), yellow pyramid at (5,8)):
    precondition_met = mastery_flag[family_precondition_attractor] == 1
    at the step of entry.
  Unaffiliated cells ((5,9), (6,8), (14,13)):
    precondition_met = sum(mastery_flag.values()) >=
                       hazard_competency_thresholds[cell]
    at the step of entry.

The reserved pre-registration amendment covers the encounter-type
classification boundary: precondition is assessed at the step of
entry (i.e. in on_post_event, after the agent has moved but before
check_competency_unlocks has run for this step). This is consistent
with pre_transition_hazard_entries in the base agent, which is
incremented in record_action_outcome when cost_incurred > 0 — before
check_competency_unlocks is called. The observer's pre-transition
count therefore matches the agent's pre_transition_hazard_entries
field exactly, as required by Category β.

Transformation detection:
  A HAZARD-to-KNOWLEDGE transition for cell C fires when
  world.cell_type[C] changes from HAZARD to KNOWLEDGE. This is
  detected in on_post_event by comparing world.cell_type[C] against
  the observer's cached cell_type from the previous step. The step
  at which the transition is first detected is recorded as
  transformed_at_step.

Output files:
  prediction_error_v1_5.csv  — per-encounter records (one row per
                                approach event per hazard cell per run).
  run_data_v1_5.csv          — per-run metrics: all v1.4 fields
                                retained plus v1.5 summary fields.
"""

import csv

from curiosity_agent_v0_14 import HAZARD, KNOWLEDGE

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Family hazard cells and their precondition attractors.
# Derived from world.family_precondition_attractor at instantiation;
# held here for documentation.
#   GREEN family:  bankable tier (14,14) → precondition (4,15)
#   YELLOW family: bankable tier (5,8)  → precondition (16,3)

# Unaffiliated hazard cells (use global competency gate).
UNAFFILIATED_HAZARD_CELLS = frozenset([(5, 9), (6, 8), (14, 13)])

# ---------------------------------------------------------------------------
# Output field definitions
# ---------------------------------------------------------------------------

PREDICTION_ERROR_SUMMARY_FIELDS = [
    "yellow_pre_transition_entries",
    "green_pre_transition_entries",
    "unaffiliated_pre_transition_entries",
    "yellow_resolution_window",
    "green_resolution_window",
    "total_prediction_error_events",
    "prediction_error_complete",
]

PREDICTION_ERROR_ENCOUNTER_FIELDS = [
    "arch", "hazard_cost", "num_steps", "run_idx", "seed",
    "step",
    "cell",
    "family",
    "precondition_met",
    "cost_paid",
    "transformed_at_step",
    "resolution_window",
    "encounter_type",
]


# ---------------------------------------------------------------------------
# V15PredictionErrorObserver
# ---------------------------------------------------------------------------

class V15PredictionErrorObserver:
    """Sixth parallel observer for v1.5 prediction-error elevation.

    Instantiated once per run. Holds live state during the run to detect
    pre-transition approach events at the step they occur.

    Parameters
    ----------
    agent : DevelopmentalAgent (V14Agent)
        The agent instance for this run.
    world : V13World
        The world instance for this run.
    run_metadata : dict
        Keys: arch, hazard_cost, num_steps, run_idx, seed.
    """

    def __init__(self, agent, world, run_metadata):
        self._agent = agent
        self._world = world
        self._meta  = run_metadata

        # Build family precondition map from world if available.
        # Maps hazard_coord -> precondition_attractor_coord.
        # For unaffiliated cells the key is absent.
        self._family_preconditions = dict(
            getattr(world, 'family_precondition_attractor', {})
        )

        # Reverse map: hazard_coord -> family name (GREEN/YELLOW/None)
        # Built from family_precondition_attractor keys and the
        # FAMILY_COLOUR_BY_COORD lookup if available.
        self._cell_family = {}
        try:
            from curiosity_agent_v1_3_world import FAMILY_COLOUR_BY_COORD
            for coord in self._family_preconditions:
                self._cell_family[coord] = FAMILY_COLOUR_BY_COORD.get(coord)
        except ImportError:
            pass
        for coord in UNAFFILIATED_HAZARD_CELLS:
            self._cell_family[coord] = None

        # All hazard cells we track (family + unaffiliated).
        self._tracked_cells = (
            set(self._family_preconditions.keys()) | UNAFFILIATED_HAZARD_CELLS
        )

        # Per-cell: list of _ApproachEvent dicts (pre-transition approaches).
        # Each dict: {step, cost_paid, precondition_met_at_entry,
        #             transformed_at_step (None until resolved)}
        self._approach_events = {cell: [] for cell in self._tracked_cells}

        # Per-cell: the step at which the HAZARD→KNOWLEDGE transition
        # was first detected. None until detected.
        self._transition_step = {cell: None for cell in self._tracked_cells}

        # Per-cell: cached cell_type from the *end* of the previous step,
        # used to detect transitions in on_post_event.
        self._prev_cell_type = {
            cell: world.cell_type.get(cell, HAZARD)
            for cell in self._tracked_cells
        }

        # Track which cells were entered this step to avoid double-counting
        # (on_post_event is called once per step).
        self._last_step_processed = -1

    # ------------------------------------------------------------------
    # Hook methods
    # ------------------------------------------------------------------

    def on_pre_action(self, step):
        """No-op. Prediction-error observer does not modify agent behaviour."""
        pass

    def on_post_event(self, step):
        """Core live-state detection.

        Called after agent.record_action_outcome and
        agent.check_competency_unlocks have both run for this step.
        Therefore:
          - world.cell_type[cell] reflects any transition that fired
            at this step.
          - agent.mastery_flag reflects any mastery earned this step.
          - agent.pre_transition_hazard_entries has been incremented
            if a pre-transition hazard entry occurred this step.

        Precondition assessment:
          The precondition is assessed BEFORE the transition fires —
          i.e., using the pre-transition state. Because the agent's
          pre_transition_hazard_entries counter is only incremented when
          cost_incurred > 0 (i.e. the cell was still HAZARD-typed at
          world.step() time), and check_competency_unlocks runs AFTER
          the cost is paid in record_action_outcome, the precondition
          state at the time of entry is the mastery_flag state BEFORE
          the current step's update_mastery_layer ran.

        To assess "was the precondition met at the step of entry"
        precisely, we use a proxy: if the cell is still HAZARD-typed
        after on_post_event runs (or was HAZARD-typed in _prev_cell_type),
        then the precondition was not met at the time of entry. If the
        transition fired THIS step (prev=HAZARD, current=KNOWLEDGE),
        the entry at this step was the transition-triggering entry —
        which is the first post-precondition entry (clean_first_entry
        if no prior pre-transition approaches, or the resolving entry
        for a resolved_surprise if prior approaches exist).

        This approach is consistent with the base agent's
        pre_transition_hazard_entries counter, which only counts
        entries when cost_incurred > 0 (HAZARD-typed entry with cost).
        """
        agent = self._agent
        world = self._world
        agent_pos = world.agent_pos

        # Detect transitions: prev=HAZARD, current=KNOWLEDGE.
        for cell in self._tracked_cells:
            current_type = world.cell_type.get(cell, HAZARD)
            prev_type    = self._prev_cell_type[cell]
            if prev_type == HAZARD and current_type == KNOWLEDGE:
                # Transition fired at this step (or earlier; record step
                # of first detection).
                if self._transition_step[cell] is None:
                    self._transition_step[cell] = step
            self._prev_cell_type[cell] = current_type

        # Detect hazard entries: agent moved onto a tracked cell this step.
        # A hazard entry is confirmed by cost_incurred > 0 in the base agent.
        # We detect it here by checking:
        #   (a) agent_pos == cell
        #   (b) cell was HAZARD-typed in _prev_cell_type (before the update
        #       above) — i.e. it was HAZARD when the agent entered, meaning
        #       cost was paid.
        # Note: _prev_cell_type was updated above for transitions. We need
        # the pre-update value. To handle this correctly, we check whether
        # the agent's pre_transition_hazard_entries counter incremented for
        # this cell this step — but that requires a per-step delta which is
        # awkward without state. Instead, we use the direct indicator:
        # cost was paid iff the cell was HAZARD-typed when world.step() ran,
        # which is equivalent to _prev_cell_type[cell] == HAZARD *before* the
        # transition check above updated it.
        #
        # To preserve this, we recompute from the current world state:
        # if world.cell_type[cell] == KNOWLEDGE and the transition was
        # detected THIS step (transition_step == step), then the cell was
        # HAZARD-typed during world.step() — the agent may or may not
        # have entered it. If agent_pos == cell and transition fired this
        # step, this is the transition-triggering entry. If agent_pos ==
        # cell and the cell is still HAZARD-typed, this is a pre-transition
        # entry with cost paid.
        #
        # We use agent.pre_transition_hazard_entries as the ground truth
        # source and detect new increments by comparing against our own
        # cached totals. This is the cleanest approach and avoids any
        # double-counting risk.

        if step != self._last_step_processed:
            self._last_step_processed = step
            self._detect_entries(step)

    def _detect_entries(self, step):
        """Detect new pre-transition hazard entries at this step.

        Uses agent.pre_transition_hazard_entries as the authoritative
        source. A new pre-transition entry for cell C is detected when
        agent.pre_transition_hazard_entries[C] exceeds the count we
        held from the previous step.

        For clean first entries (agent at a cell that just transitioned),
        we detect the transition-triggering entry separately.
        """
        agent = self._agent
        world = self._world

        for cell in self._tracked_cells:
            # --- Pre-transition entries ---
            # agent.pre_transition_hazard_entries[cell] is the total count
            # of HAZARD-type entries with cost paid for this cell since
            # run start. Our _approach_events list length is our cached
            # count of pre-transition entries we have recorded.
            agent_pretrans_count = agent.pre_transition_hazard_entries.get(
                cell, 0
            )
            our_recorded_count = len(self._approach_events[cell])

            if agent_pretrans_count > our_recorded_count:
                # New pre-transition entries recorded by the base agent
                # since our last check (normally exactly one per step).
                new_count = agent_pretrans_count - our_recorded_count
                for _ in range(new_count):
                    precondition_met = self._precondition_met_at_entry(cell)
                    cost = world.hazard_cost if hasattr(world, 'hazard_cost') \
                        else agent.hazard_competency_thresholds.get(cell, 0)
                    # Retrieve actual cost from agent state.
                    # The hazard cost is stored on the world as world.hazard_cost
                    # for V13World. We read it directly.
                    actual_cost = getattr(world, 'hazard_cost',
                                          agent.total_cost_incurred)
                    # Use world.hazard_cost if it exists (V13World stores it).
                    # For the cost of this specific entry, world.hazard_cost
                    # is the per-entry cost (all hazard cells use the same
                    # cost in V13World).
                    entry_cost = getattr(world, 'hazard_cost', None)
                    if entry_cost is None:
                        # Fallback: cannot determine per-entry cost precisely;
                        # record None to avoid fabricating a value.
                        entry_cost = None

                    self._approach_events[cell].append({
                        "step":                   step,
                        "precondition_met":       precondition_met,
                        "cost_paid":              entry_cost,
                        "transformed_at_step":    None,  # resolved at run_end
                    })

    def _precondition_met_at_entry(self, cell):
        """Assess whether the precondition for cell was met at this step.

        For family cells: precondition_met iff mastery_flag[precondition
        attractor] == 1 at the time of entry. Since check_competency_unlocks
        runs AFTER the cost is paid, and mastery_flag is updated in
        update_mastery_layer (called in record_action_outcome for ATTRACTOR
        entries only), the mastery state at entry time is the mastery state
        at the point on_post_event is called — which is after all of
        record_action_outcome has run, including check_competency_unlocks.

        This means: if the precondition attractor was mastered at THIS step
        (i.e. the agent entered the attractor this step), mastery_flag will
        already reflect it — but in that case the hazard cell transition
        would also fire this step, so the entry would be classified as a
        transition-triggering entry, not a pre-transition entry.

        For unaffiliated cells: precondition_met iff sum(mastery_flag) >=
        threshold at the time on_post_event is called.
        """
        agent = self._agent
        precondition_attractor = self._family_preconditions.get(cell)

        if precondition_attractor is not None:
            # Family cell
            return agent.mastery_flag.get(precondition_attractor, 0) == 1
        else:
            # Unaffiliated cell
            threshold = agent.hazard_competency_thresholds.get(cell)
            if threshold is None:
                return False
            return sum(agent.mastery_flag.values()) >= threshold

    # ------------------------------------------------------------------
    # Run-end processing
    # ------------------------------------------------------------------

    def on_run_end(self, step):
        """Classify approach events and compute per-run summary fields.

        For each recorded pre-transition approach event, determine whether
        the transformation fired within the run (resolved_surprise) or
        not (unresolved_approach). Also record clean_first_entry events
        for cells where the first approach was post-precondition.
        """
        agent = self._agent
        world = self._world

        # Resolve transformation steps for all approach events.
        for cell in self._tracked_cells:
            trans_step = self._transition_step.get(cell)
            for event in self._approach_events[cell]:
                if trans_step is not None and trans_step >= event["step"]:
                    event["transformed_at_step"] = trans_step
                    event["resolution_window"]   = trans_step - event["step"]
                else:
                    event["transformed_at_step"] = None
                    event["resolution_window"]   = None

        # Build full encounter record list (including clean first entries).
        self._encounter_records = []

        for cell in sorted(self._tracked_cells):
            family      = self._cell_family.get(cell)
            trans_step  = self._transition_step.get(cell)
            pre_entries = self._approach_events[cell]

            # Pre-transition approach events
            for event in pre_entries:
                if event["transformed_at_step"] is not None:
                    enc_type = "resolved_surprise"
                else:
                    enc_type = "unresolved_approach"

                self._encounter_records.append({
                    "arch":               self._meta.get("arch", "v1_5"),
                    "hazard_cost":        self._meta.get("hazard_cost"),
                    "num_steps":          self._meta.get("num_steps"),
                    "run_idx":            self._meta.get("run_idx"),
                    "seed":               self._meta.get("seed"),
                    "step":               event["step"],
                    "cell":               str(cell),
                    "family":             family,
                    "precondition_met":   event["precondition_met"],
                    "cost_paid":          event["cost_paid"],
                    "transformed_at_step": event["transformed_at_step"],
                    "resolution_window":  event["resolution_window"],
                    "encounter_type":     enc_type,
                })

            # Clean first entry: transformation fired AND no pre-transition
            # approaches recorded — the first approach was post-precondition.
            if trans_step is not None and len(pre_entries) == 0:
                # The transformation-triggering step is the clean first entry.
                # Cost is zero at this entry (cell was KNOWLEDGE-typed from
                # the world's perspective after transition, but the entry
                # that triggered the transition paid no cost — the transition
                # fires via check_competency_unlocks, not on entry).
                # Record the transformation step as the entry step.
                self._encounter_records.append({
                    "arch":               self._meta.get("arch", "v1_5"),
                    "hazard_cost":        self._meta.get("hazard_cost"),
                    "num_steps":          self._meta.get("num_steps"),
                    "run_idx":            self._meta.get("run_idx"),
                    "seed":               self._meta.get("seed"),
                    "step":               trans_step,
                    "cell":               str(cell),
                    "family":             family,
                    "precondition_met":   True,
                    "cost_paid":          0.0,
                    "transformed_at_step": trans_step,
                    "resolution_window":  0,
                    "encounter_type":     "clean_first_entry",
                })

    # ------------------------------------------------------------------
    # Summary metrics and output
    # ------------------------------------------------------------------

    def summary_metrics(self):
        """Return per-run summary dict for inclusion in run_data_v1_5.csv.

        Must be called after on_run_end.
        """
        # Pre-transition entry counts
        yellow_pre = 0
        green_pre  = 0
        unaff_pre  = 0

        for cell in self._tracked_cells:
            count = len(self._approach_events[cell])
            family = self._cell_family.get(cell)
            if family == "YELLOW":
                yellow_pre += count
            elif family == "GREEN":
                green_pre += count
            else:
                unaff_pre += count

        # Resolution windows (first approach only, per pre-registration §2.4)
        yellow_rw = None
        green_rw  = None

        for cell in self._tracked_cells:
            family = self._cell_family.get(cell)
            events = self._approach_events[cell]
            if not events:
                continue
            first_event = events[0]
            rw = first_event.get("resolution_window")
            if family == "YELLOW" and yellow_rw is None:
                yellow_rw = rw
            elif family == "GREEN" and green_rw is None:
                green_rw = rw

        total_pe = yellow_pre + green_pre + unaff_pre
        complete = total_pe > 0 or len(self._encounter_records) > 0

        return {
            "yellow_pre_transition_entries":    yellow_pre,
            "green_pre_transition_entries":     green_pre,
            "unaffiliated_pre_transition_entries": unaff_pre,
            "yellow_resolution_window":         yellow_rw,
            "green_resolution_window":          green_rw,
            "total_prediction_error_events":    total_pe,
            "prediction_error_complete":        complete,
        }

    def write_prediction_error_csv(self, path, append=False):
        """Write per-encounter records to prediction_error_v1_5.csv."""
        if not hasattr(self, '_encounter_records'):
            return

        def _file_has_rows(p):
            try:
                with open(p) as f:
                    lines = [l for l in f if l.strip()]
                return len(lines) > 1
            except FileNotFoundError:
                return False

        mode = "a" if append else "w"
        write_header = (not append) or (not _file_has_rows(path))
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=PREDICTION_ERROR_ENCOUNTER_FIELDS
            )
            if write_header:
                writer.writeheader()
            for row in self._encounter_records:
                writer.writerow(
                    {k: row.get(k, "") for k in PREDICTION_ERROR_ENCOUNTER_FIELDS}
                )

    def reset(self):
        """Reset mutable state. Called by batch runner between runs."""
        self._approach_events     = {cell: [] for cell in self._tracked_cells}
        self._transition_step     = {cell: None for cell in self._tracked_cells}
        self._prev_cell_type      = {
            cell: self._world.cell_type.get(cell, HAZARD)
            for cell in self._tracked_cells
        }
        self._last_step_processed = -1
        if hasattr(self, '_encounter_records'):
            self._encounter_records = []
