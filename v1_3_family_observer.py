"""
v1_3_family_observer.py
------------------------
v1.3 family observer. The fourth parallel observer in the programme's
observer stack, running alongside the v1.0 recorder, v1.1 provenance
store, and v1.2 schema observer.

Responsibilities:
  1. Colour-cell registration records — formed on first perception of
     each colour cell (adjacency or entry), recording step, coordinate,
     colour, form, and the coordinates of the family's acquirable and
     bankable tiers.

  2. Family property fields on mastery and knowledge-banking flags —
     when the provenance store forms a mastery flag or knowledge-banking
     flag on a family-attributed cell, the family observer enriches the
     record with cell_colour and cell_form.

  3. Intra-family cross-reference — when a knowledge-banking flag forms
     on a bankable-tier cell, the family observer writes the
     family_2d_mastery_flag_id field, linking it to the mastery flag of
     the corresponding acquirable-tier cell in the same family. This is
     the first across-coordinate relational dependency in the programme
     (pre-registration §2.5).

  4. Family traversal narrative — an ordered string of family events
     across the run: colour_registered, attractor_mastered,
     knowledge_banked, per family. This is the Category γ substrate.

Observer pattern:
  - Read-only access to agent and world state.
  - No modification to agent action-selection, drive composition, or
    value functions.
  - Three hook methods: on_pre_action(step), on_post_event(step),
    on_run_end(step).
  - with --no-family, this observer is not instantiated; the batch
    runner produces v1.2-identical output.

Output fields:
  Per-run summary fields (written to run_data_v1_3.csv):
    green_cell_registered, green_cell_first_perception_step
    yellow_cell_registered, yellow_cell_first_perception_step
    green_attractor_mastered, green_attractor_mastery_step
    yellow_attractor_mastered, yellow_attractor_mastery_step
    green_knowledge_banked, green_knowledge_banked_step
    yellow_knowledge_banked, yellow_knowledge_banked_step
    green_crossref_complete, yellow_crossref_complete
    family_traversal_narrative
    schema_cell_types_count (overridden to 7)

  Per-run family record (written to family_v1_3.csv):
    One row per run. Full registration and cross-reference detail.
"""

import csv

from curiosity_agent_v1_3_world import (
    GREEN, YELLOW,
    COLOUR_CELL_COORDS,
    FAMILY_ATTRACTOR_COORDS,
    FAMILY_HAZARD_COORDS,
    FAMILY_COLOUR_BY_COORD,
    FAMILY_FORM_BY_COORD,
    FAMILY_PRECONDITION,
    COLOUR_CELL,
)

# -------------------------------------------------------------------------
# Output field definitions
# -------------------------------------------------------------------------
FAMILY_SUMMARY_FIELDS = [
    "green_cell_registered",
    "green_cell_first_perception_step",
    "yellow_cell_registered",
    "yellow_cell_first_perception_step",
    "green_attractor_mastered",
    "green_attractor_mastery_step",
    "yellow_attractor_mastered",
    "yellow_attractor_mastery_step",
    "green_knowledge_banked",
    "green_knowledge_banked_step",
    "yellow_knowledge_banked",
    "yellow_knowledge_banked_step",
    "green_crossref_complete",
    "yellow_crossref_complete",
    "family_traversal_narrative",
]

FAMILY_RECORD_FIELDS = [
    "arch", "hazard_cost", "num_steps", "run_idx", "seed",
    # Green family
    "green_colour_cell_coord",
    "green_attractor_coord",
    "green_hazard_coord",
    "green_cell_registered",
    "green_cell_first_perception_step",
    "green_cell_first_perception_mode",   # "adjacent" or "entry"
    "green_attractor_mastered",
    "green_attractor_mastery_step",
    "green_attractor_colour",
    "green_attractor_form",
    "green_knowledge_banked",
    "green_knowledge_banked_step",
    "green_knowledge_colour",
    "green_knowledge_form",
    "green_crossref_complete",
    "green_crossref_flag_id",             # mastery flag id of green attractor
    # Yellow family
    "yellow_colour_cell_coord",
    "yellow_attractor_coord",
    "yellow_hazard_coord",
    "yellow_cell_registered",
    "yellow_cell_first_perception_step",
    "yellow_cell_first_perception_mode",
    "yellow_attractor_mastered",
    "yellow_attractor_mastery_step",
    "yellow_attractor_colour",
    "yellow_attractor_form",
    "yellow_knowledge_banked",
    "yellow_knowledge_banked_step",
    "yellow_knowledge_colour",
    "yellow_knowledge_form",
    "yellow_crossref_complete",
    "yellow_crossref_flag_id",
    # Traversal
    "family_traversal_narrative",
]


# -------------------------------------------------------------------------
# V13FamilyObserver
# -------------------------------------------------------------------------
class V13FamilyObserver:
    """Fourth parallel observer for v1.3 family structure.

    Instantiated once per run. Holds no mutable reference to agent or
    world state beyond what is read at hook call time.
    """

    def __init__(self, agent, world, run_metadata, provenance_store=None):
        self.agent = agent
        self.world = world
        self.meta  = run_metadata
        # Optional provenance store reference for mastery step recovery.
        # Stored under a private name to avoid any confusion with the
        # removed records-iteration approach.
        # records is Dict[str, ProvenanceRecord] — access via .get(flag_id).
        self._provenance_store_ref = provenance_store

        # --- Colour-cell registration state ---
        # First perception: adjacency (perceive_adjacent returns
        # COLOUR_CELL) or entry (agent position == colour cell coord).
        self._colour_registered    = {GREEN: False, YELLOW: False}
        self._colour_first_step    = {GREEN: None,  YELLOW: None}
        self._colour_first_mode    = {GREEN: None,  YELLOW: None}

        # Reverse lookup: coord -> colour family
        self._coord_to_colour = {
            coord: colour
            for colour, coord in COLOUR_CELL_COORDS.items()
        }

        # --- Family event log for traversal narrative ---
        # Each entry: (step, event_type, family)
        # event_type: "colour_registered" | "attractor_mastered" |
        #             "knowledge_banked"
        self._traversal_events = []

        # --- Attractor mastery tracking ---
        # Snapshot of mastery_order_sequence length at previous step,
        # to detect new bankings between hook calls.
        self._prev_mastery_len   = 0
        self._prev_knowledge_len = 0

        # --- Cross-reference state ---
        self._crossref_complete = {GREEN: False, YELLOW: False}
        self._crossref_flag_id  = {GREEN: None,  YELLOW: None}

    # ------------------------------------------------------------------
    # Hook methods
    # ------------------------------------------------------------------

    def on_pre_action(self, step):
        """Called before the agent selects its action for this step.

        Check for colour-cell adjacency perception. The agent's current
        position is world.agent_pos; perceive_adjacent returns the four
        neighbouring cell types. If any adjacent cell is COLOUR_CELL and
        the corresponding family has not yet been registered, register it.
        """
        pos = self.world.agent_pos
        adj_types_and_coords = self.world.perceive_adjacent_with_coords(pos)
        for ctype, coord in adj_types_and_coords:
            if ctype == COLOUR_CELL:
                colour = self._coord_to_colour.get(coord)
                if colour and not self._colour_registered[colour]:
                    self._colour_registered[colour] = True
                    self._colour_first_step[colour]  = step
                    self._colour_first_mode[colour]  = "adjacent"
                    self._traversal_events.append(
                        (step, "colour_registered", colour)
                    )

    def on_post_event(self, step):
        """Called after the agent has acted and updated its state.

        1. Check if the agent entered a colour cell (entry-mode
           registration, catches the case where the agent moves onto
           the cell rather than approaching it).
        2. Check for new attractor masteries in family-attributed cells.
        3. Check for new knowledge bankings in family-attributed cells,
           and populate intra-family cross-references.
        """
        # 1. Entry-mode colour registration
        pos = self.world.agent_pos
        colour = self._coord_to_colour.get(pos)
        if colour and not self._colour_registered[colour]:
            self._colour_registered[colour] = True
            self._colour_first_step[colour]  = step
            self._colour_first_mode[colour]  = "entry"
            self._traversal_events.append(
                (step, "colour_registered", colour)
            )

        # 2. New attractor masteries
        current_mastery_len = len(self.agent.mastery_order_sequence)
        if current_mastery_len > self._prev_mastery_len:
            # Identify newly banked attractors
            newly_banked = self.agent.mastery_order_sequence[
                self._prev_mastery_len:
            ]
            for coord in newly_banked:
                colour = FAMILY_COLOUR_BY_COORD.get(coord)
                if colour is not None:
                    self._traversal_events.append(
                        (step, "attractor_mastered", colour)
                    )
            self._prev_mastery_len = current_mastery_len

        # 3. New knowledge bankings
        current_knowledge_len = len(self.agent.knowledge_banked_sequence)
        if current_knowledge_len > self._prev_knowledge_len:
            newly_knowledge = self.agent.knowledge_banked_sequence[
                self._prev_knowledge_len:
            ]
            for coord in newly_knowledge:
                colour = FAMILY_COLOUR_BY_COORD.get(coord)
                if colour is not None:
                    self._traversal_events.append(
                        (step, "knowledge_banked", colour)
                    )
                    # Populate intra-family cross-reference
                    self._populate_crossref(coord, colour)
            self._prev_knowledge_len = current_knowledge_len

    def on_run_end(self, step):
        """Called at run end. No state changes required; summary
        metrics are computed on demand from accumulated state."""
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _populate_crossref(self, bankable_coord, colour):
        """Populate the intra-family cross-reference for a bankable cell.

        Links the knowledge-banking event at bankable_coord to the mastery
        event of the corresponding acquirable-tier cell in the same family.
        The cross-reference is recorded as the precondition coordinate,
        readable directly in analysis without requiring provenance internals.

        Cross-reference is complete if the precondition coord appears in
        the agent's mastery_order_sequence, which is always the authoritative
        record of which attractors have been banked.

        Per pre-registration §2.5: should always resolve under the present
        architecture's competency-gating logic. If not, pending is recorded
        honestly.
        """
        precondition_coord = FAMILY_PRECONDITION.get(bankable_coord)
        if precondition_coord is None:
            return

        if precondition_coord in self.agent.mastery_order_sequence:
            self._crossref_complete[colour] = True
            self._crossref_flag_id[colour]  = str(precondition_coord)
        else:
            # Architecturally unexpected: bankable tier unlocked without
            # acquirable tier mastered. Recorded honestly.
            self._crossref_flag_id[colour] = (
                f"pending_precondition_not_mastered:{precondition_coord}"
            )

    # ------------------------------------------------------------------
    # Summary metrics and output
    # ------------------------------------------------------------------

    def summary_metrics(self):
        """Return per-run summary dict for inclusion in run_data_v1_3.csv."""
        green_att_coord    = FAMILY_ATTRACTOR_COORDS[GREEN]
        yellow_att_coord   = FAMILY_ATTRACTOR_COORDS[YELLOW]
        green_know_coord   = FAMILY_HAZARD_COORDS[GREEN]
        yellow_know_coord  = FAMILY_HAZARD_COORDS[YELLOW]

        green_att_step = self._attractor_mastery_step(green_att_coord)
        yellow_att_step = self._attractor_mastery_step(yellow_att_coord)

        green_know_step  = self.agent.knowledge_banked_step.get(
            green_know_coord
        )
        yellow_know_step = self.agent.knowledge_banked_step.get(
            yellow_know_coord
        )

        return {
            "green_cell_registered":
                self._colour_registered[GREEN],
            "green_cell_first_perception_step":
                self._colour_first_step[GREEN],
            "yellow_cell_registered":
                self._colour_registered[YELLOW],
            "yellow_cell_first_perception_step":
                self._colour_first_step[YELLOW],
            "green_attractor_mastered":
                green_att_coord in self.agent.mastery_order_sequence,
            "green_attractor_mastery_step":
                green_att_step,
            "yellow_attractor_mastered":
                yellow_att_coord in self.agent.mastery_order_sequence,
            "yellow_attractor_mastery_step":
                yellow_att_step,
            "green_knowledge_banked":
                self.agent.knowledge_banked.get(green_know_coord, False),
            "green_knowledge_banked_step":
                green_know_step,
            "yellow_knowledge_banked":
                self.agent.knowledge_banked.get(yellow_know_coord, False),
            "yellow_knowledge_banked_step":
                yellow_know_step,
            "green_crossref_complete":
                self._crossref_complete[GREEN],
            "yellow_crossref_complete":
                self._crossref_complete[YELLOW],
            "family_traversal_narrative":
                self._build_traversal_narrative(),
        }

    def _attractor_mastery_step(self, coord):
        """Return the step at which coord was mastered, or None.

        Derived from the provenance store's records dict if available,
        using the correct access pattern (records is a dict keyed by
        flag_id string, values are ProvenanceRecord dataclasses).
        Falls back to None if the provenance store is not held or the
        record is not found — the step is not recoverable from agent
        state alone without per-cell mastery step tracking.
        """
        if coord not in self.agent.mastery_order_sequence:
            return None
        # Attempt to read from provenance store if it was passed in.
        # Access pattern: records is Dict[str, ProvenanceRecord].
        # flag_id format: "mastery:(x, y)"
        prov = getattr(self, "_provenance_store_ref", None)
        if prov is not None:
            flag_id = f"mastery:{coord}"
            record = prov.records.get(flag_id)
            if record is not None:
                try:
                    return int(record.flag_set_step)
                except (TypeError, ValueError, AttributeError):
                    return None
        return None

    def _build_traversal_narrative(self):
        """Build the family_traversal_narrative string.

        Format: step:event:family|step:event:family|...
        Events in chronological order.
        Example: 47:colour_registered:GREEN|312:colour_registered:YELLOW|
                 838:attractor_mastered:GREEN
        """
        if not self._traversal_events:
            return ""
        sorted_events = sorted(self._traversal_events, key=lambda e: e[0])
        return "|".join(
            f"{step}:{event}:{colour}"
            for step, event, colour in sorted_events
        )

    def full_record(self):
        """Return full per-run family record dict for family_v1_3.csv."""
        summary = self.summary_metrics()
        green_att_coord   = FAMILY_ATTRACTOR_COORDS[GREEN]
        yellow_att_coord  = FAMILY_ATTRACTOR_COORDS[YELLOW]
        green_know_coord  = FAMILY_HAZARD_COORDS[GREEN]
        yellow_know_coord = FAMILY_HAZARD_COORDS[YELLOW]

        record = dict(self.meta)
        record.update({
            # Green family
            "green_colour_cell_coord":
                str(COLOUR_CELL_COORDS[GREEN]),
            "green_attractor_coord":
                str(green_att_coord),
            "green_hazard_coord":
                str(green_know_coord),
            "green_cell_registered":
                summary["green_cell_registered"],
            "green_cell_first_perception_step":
                summary["green_cell_first_perception_step"],
            "green_cell_first_perception_mode":
                self._colour_first_mode[GREEN],
            "green_attractor_mastered":
                summary["green_attractor_mastered"],
            "green_attractor_mastery_step":
                summary["green_attractor_mastery_step"],
            "green_attractor_colour":
                FAMILY_COLOUR_BY_COORD.get(green_att_coord),
            "green_attractor_form":
                FAMILY_FORM_BY_COORD.get(green_att_coord),
            "green_knowledge_banked":
                summary["green_knowledge_banked"],
            "green_knowledge_banked_step":
                summary["green_knowledge_banked_step"],
            "green_knowledge_colour":
                FAMILY_COLOUR_BY_COORD.get(green_know_coord),
            "green_knowledge_form":
                FAMILY_FORM_BY_COORD.get(green_know_coord),
            "green_crossref_complete":
                summary["green_crossref_complete"],
            "green_crossref_flag_id":
                self._crossref_flag_id[GREEN],
            # Yellow family
            "yellow_colour_cell_coord":
                str(COLOUR_CELL_COORDS[YELLOW]),
            "yellow_attractor_coord":
                str(yellow_att_coord),
            "yellow_hazard_coord":
                str(yellow_know_coord),
            "yellow_cell_registered":
                summary["yellow_cell_registered"],
            "yellow_cell_first_perception_step":
                summary["yellow_cell_first_perception_step"],
            "yellow_cell_first_perception_mode":
                self._colour_first_mode[YELLOW],
            "yellow_attractor_mastered":
                summary["yellow_attractor_mastered"],
            "yellow_attractor_mastery_step":
                summary["yellow_attractor_mastery_step"],
            "yellow_attractor_colour":
                FAMILY_COLOUR_BY_COORD.get(yellow_att_coord),
            "yellow_attractor_form":
                FAMILY_FORM_BY_COORD.get(yellow_att_coord),
            "yellow_knowledge_banked":
                summary["yellow_knowledge_banked"],
            "yellow_knowledge_banked_step":
                summary["yellow_knowledge_banked_step"],
            "yellow_knowledge_colour":
                FAMILY_COLOUR_BY_COORD.get(yellow_know_coord),
            "yellow_knowledge_form":
                FAMILY_FORM_BY_COORD.get(yellow_know_coord),
            "yellow_crossref_complete":
                summary["yellow_crossref_complete"],
            "yellow_crossref_flag_id":
                self._crossref_flag_id[YELLOW],
            # Traversal
            "family_traversal_narrative":
                summary["family_traversal_narrative"],
        })
        return record

    def write_family_csv(self, path, append=False):
        """Write full family record to family_v1_3.csv."""
        mode = "a" if append else "w"
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FAMILY_RECORD_FIELDS)
            row = self.full_record()
            writer.writerow({k: row.get(k, "") for k in FAMILY_RECORD_FIELDS})

    def reset(self):
        """Reset mutable state. Called by batch runner between runs."""
        self._colour_registered    = {GREEN: False, YELLOW: False}
        self._colour_first_step    = {GREEN: None,  YELLOW: None}
        self._colour_first_mode    = {GREEN: None,  YELLOW: None}
        self._traversal_events     = []
        self._prev_mastery_len     = 0
        self._prev_knowledge_len   = 0
        self._crossref_complete    = {GREEN: False, YELLOW: False}
        self._crossref_flag_id     = {GREEN: None,  YELLOW: None}
