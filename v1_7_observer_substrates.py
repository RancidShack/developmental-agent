"""
v1_7_observer_substrates.py
-----------------------------
v1.7 additive patch: overrides the v1.6 get_substrate() implementations
where V17World's object_id-keyed substrate differs from V13World's
coord-keyed substrate, and patches V15PredictionErrorObserver to use
V17World object_ids rather than grid coordinate frozensets.

ARCHITECTURE PRINCIPLE
This module extends v1_6_observer_substrates.py. It is imported AFTER
v1_6_observer_substrates in the v1.7 batch runner, so that any method
it re-patches takes precedence over the v1.6 patch.

SUBSTRATE-INTERFACE CHANGES AT V1.7
The three changes confirmed as substrate-interface work at v1.7:

  1. V15PredictionErrorObserver._tracked_cells
     Was: frozenset of (row, col) coordinate tuples.
     Now: frozenset of object_id strings from V17World.
     The UNAFFILIATED_HAZARD_CELLS constant is replaced by the world's
     UNAFFILIATED_HAZARD_IDS set.

  2. V15PredictionErrorObserver._cell_family
     Was: keyed by (row, col) tuples, built from FAMILY_COLOUR_BY_COORD.
     Now: keyed by object_id strings, built from V17World.object_colour.

  3. V1ProvenanceStore flag_id format
     Was: "mastery:(4, 15)" — hardcoded coordinate string.
     Now: "mastery:att_green" — object_id string.
     This is the substrate-interface migration of the flag_id format.
     The provenance store's get_substrate() method converts flag_ids
     to ProvenanceSubstrateRecord entries keyed by the same flag_id.
     The SubstrateBundle patch in build_bundle_from_csvs_v17 replaces
     the v1.6 coord-based mastery patch with the object_id-based one.

COGNITIVE-LAYER COMPONENTS CONFIRMED UNCHANGED
  - V16ReportingLayer: no import of object_ids or grid coordinates.
    Level 9 pre-flight tests this directly.
  - SubstrateBundle and ProvenanceSubstrateRecord: no grid-specific fields.
  - V13SchemaObserver: schema structure unchanged; cell-type vocab now
    includes DIST_OBJ = 6 alongside the existing six types.
  - V13FamilyObserver: family traversal logic unchanged; coord lookups
    replaced by object_id lookups via patched _build_family_lookup().
  - V14ComparisonObserver: reads completed family records; no coord imports.
"""

import v1_6_observer_substrates  # noqa: F401 — ensure v1.6 patches applied first

from v1_5_prediction_error_observer import V15PredictionErrorObserver
from curiosity_agent_v1_7_world import (
    HAZARD, KNOWLEDGE,
    UNAFFILIATED_HAZARD_IDS,
    OBJECT_COLOUR,
    FAMILY_PRECONDITION,
)


# ---------------------------------------------------------------------------
# Patch V15PredictionErrorObserver for V17World
# ---------------------------------------------------------------------------
# The observer's __init__ builds _tracked_cells, _cell_family, and
# _family_preconditions from world attributes. In V17World, all of these
# are keyed by object_id strings. The observer's __init__ reads:
#   - world.family_precondition_attractor  (dict: hazard_id -> attractor_id)
#   - FAMILY_COLOUR_BY_COORD (imported from v1_3_world)
#   - UNAFFILIATED_HAZARD_CELLS (module-level frozenset of grid coords)
#
# We patch the observer's __init__ to detect V17World and use object_ids.

_original_pe_init = V15PredictionErrorObserver.__init__


def _v17_pe_init(self, agent, world, run_metadata):
    """V17World-aware __init__ for V15PredictionErrorObserver.

    If world is a V17World instance, uses object_id-keyed structures.
    Otherwise falls back to original __init__ for backward compatibility.
    """
    from curiosity_agent_v1_7_world import V17World
    if not isinstance(world, V17World):
        _original_pe_init(self, agent, world, run_metadata)
        return

    # V17World path
    self._agent = agent
    self._world = world
    self._meta  = run_metadata

    # Family precondition map from world
    self._family_preconditions = dict(
        getattr(world, 'family_precondition_attractor', {})
    )

    # Cell family: object_id -> colour string or None
    self._cell_family = {}
    for oid, colour in world.object_colour.items():
        if oid in self._family_preconditions:
            self._cell_family[oid] = colour
    for oid in UNAFFILIATED_HAZARD_IDS:
        self._cell_family[oid] = None

    # All hazard object_ids we track
    self._tracked_cells = (
        set(self._family_preconditions.keys()) | set(UNAFFILIATED_HAZARD_IDS)
    )

    # Per-cell approach events and transition tracking
    self._approach_events  = {oid: [] for oid in self._tracked_cells}
    self._transition_step  = {oid: None for oid in self._tracked_cells}
    self._prev_cell_type   = {
        oid: world.object_type.get(oid, HAZARD)
        for oid in self._tracked_cells
    }
    self._last_step_processed = -1


V15PredictionErrorObserver.__init__ = _v17_pe_init


# ---------------------------------------------------------------------------
# Patch _detect_entries for V17World
# ---------------------------------------------------------------------------
# The original _detect_entries reads agent.pre_transition_hazard_entries[cell]
# where cell is a coord tuple. In V17World, cell is an object_id string.
# This is the same dict structure on the agent; only the key type changes.
# The original implementation works unchanged because it reads by key, and
# V17Agent.pre_transition_hazard_entries is keyed by object_id. No patch needed.

# ---------------------------------------------------------------------------
# Patch _precondition_met_at_entry for V17World
# ---------------------------------------------------------------------------
# The original reads agent.mastery_flag[precondition_attractor] where the
# key is a coord tuple. In V17World, the key is an object_id string.
# V17Agent.mastery_flag is keyed by object_id. No patch needed — the
# dict lookup is the same; only the key type changed.

# ---------------------------------------------------------------------------
# build_bundle_from_csvs_v17
# ---------------------------------------------------------------------------
# The v1.6 build_bundle_from_csvs has a coord-based mastery patch:
#   GREEN_ATT_FLAG  = "mastery:(4, 15)"
#   YELLOW_ATT_FLAG = "mastery:(16, 3)"
# At v1.7, the flag IDs use object_ids:
#   GREEN_ATT_FLAG  = "mastery:att_green"
#   YELLOW_ATT_FLAG = "mastery:att_yellow"
# This function wraps build_bundle_from_csvs with the v1.7 patch applied.

# ---------------------------------------------------------------------------
# Patch V13FamilyObserver for V17World
# ---------------------------------------------------------------------------
# The family observer's substrate-interface dependencies on grid coordinates:
#   1. _coord_to_colour: (x,y) -> colour  =>  object_id -> colour
#   2. COLOUR_CELL_COORDS lookup           =>  dist_green/dist_yellow ids
#   3. FAMILY_ATTRACTOR_COORDS/HAZARD_COORDS =>  att_green/haz_green etc
#   4. perceive_adjacent_with_coords()     =>  perceive_within_radius()
#   5. agent_pos == colour_cell_coord      =>  contact_at_pos(DIST_OBJ)
#   6. FAMILY_COLOUR_BY_COORD/FORM lookups =>  world.object_colour/form
#   7. flag_id format "mastery:(4,15)"     =>  "mastery:att_green"
#
# The traversal logic — what constitutes a traversal event, the narrative
# format, the cross-reference resolution — is unchanged. Only the identity
# keys change from coordinate tuples to object_id strings.

from v1_3_family_observer import V13FamilyObserver
from curiosity_agent_v1_3_world import GREEN, YELLOW

# V17World object_id layout for family tiers
_V17_DIST_IDS     = {GREEN: "dist_green",  YELLOW: "dist_yellow"}
_V17_ATT_IDS      = {GREEN: "att_green",   YELLOW: "att_yellow"}
_V17_HAZ_IDS      = {GREEN: "haz_green",   YELLOW: "haz_yellow"}

_original_family_init = V13FamilyObserver.__init__


def _v17_family_init(self, agent, world, run_metadata, provenance_store=None):
    """V17World-aware __init__ for V13FamilyObserver."""
    from curiosity_agent_v1_7_world import V17World
    if not isinstance(world, V17World):
        _original_family_init(self, agent, world, run_metadata, provenance_store)
        return

    self.agent  = agent
    self.world  = world
    self.meta   = run_metadata
    self._provenance_store_ref = provenance_store

    # Colour registration state (unchanged structure)
    self._colour_registered = {GREEN: False, YELLOW: False}
    self._colour_first_step = {GREEN: None,  YELLOW: None}
    self._colour_first_mode = {GREEN: None,  YELLOW: None}

    # Object_id -> colour for distal objects (replaces _coord_to_colour)
    self._oid_to_colour = {
        "dist_green":  GREEN,
        "dist_yellow": YELLOW,
    }

    # Traversal events and cross-reference state (unchanged structure)
    self._traversal_events   = []
    self._prev_mastery_len   = 0
    self._prev_knowledge_len = 0
    self._crossref_complete  = {GREEN: False, YELLOW: False}
    self._crossref_flag_id   = {GREEN: None,  YELLOW: None}

    # Cached row (set by get_substrate via full_record)
    self._row = None


V13FamilyObserver.__init__ = _v17_family_init


def _v17_family_on_pre_action(self, step):
    """V17World: detect distal object within perception radius."""
    from curiosity_agent_v1_7_world import V17World, DIST_OBJ
    if not isinstance(self.world, V17World):
        # Fall back to original for non-V17 worlds
        _original_family_on_pre_action(self, step)
        return

    pos = self.world.agent_pos
    perceived = self.world.perceive_within_radius(pos, self.world.perception_radius
                                                   if hasattr(self.world, 'perception_radius')
                                                   else 3.0)
    for obj_type, oid in perceived:
        if obj_type == DIST_OBJ:
            colour = self._oid_to_colour.get(oid)
            if colour and not self._colour_registered[colour]:
                self._colour_registered[colour] = True
                self._colour_first_step[colour]  = step
                self._colour_first_mode[colour]  = "adjacent"
                self._traversal_events.append((step, "colour_registered", colour))


def _v17_family_on_post_event(self, step):
    """V17World: check mastery/knowledge events using object_ids."""
    from curiosity_agent_v1_7_world import V17World, DIST_OBJ

    if not isinstance(self.world, V17World):
        _original_family_on_post_event(self, step)
        return

    # Entry-mode distal object registration (agent contacted dist object)
    contact_oid = self.world._contact_at_pos(self.world.agent_pos)
    if contact_oid is not None:
        colour = self._oid_to_colour.get(contact_oid)
        if colour and not self._colour_registered[colour]:
            self._colour_registered[colour] = True
            self._colour_first_step[colour]  = step
            self._colour_first_mode[colour]  = "entry"
            self._traversal_events.append((step, "colour_registered", colour))

    # New attractor masteries
    current_mastery_len = len(self.agent.mastery_order_sequence)
    if current_mastery_len > self._prev_mastery_len:
        newly_mastered = self.agent.mastery_order_sequence[self._prev_mastery_len:]
        for oid in newly_mastered:
            colour = self.world.object_colour.get(oid)
            if colour is not None:
                self._traversal_events.append((step, "attractor_mastered", colour))
        self._prev_mastery_len = current_mastery_len

    # New knowledge bankings
    current_knowledge_len = len(self.agent.knowledge_banked_sequence)
    if current_knowledge_len > self._prev_knowledge_len:
        newly_banked = self.agent.knowledge_banked_sequence[self._prev_knowledge_len:]
        for oid in newly_banked:
            colour = self.world.object_colour.get(oid)
            if colour is not None:
                self._traversal_events.append((step, "knowledge_banked", colour))
                _v17_populate_crossref(self, oid, colour)
        self._prev_knowledge_len = current_knowledge_len


def _v17_populate_crossref(self, bankable_oid, colour):
    """V17World: cross-reference by object_id."""
    precondition_oid = self.world.family_precondition_attractor.get(bankable_oid)
    if precondition_oid is None:
        return
    if precondition_oid in self.agent.mastery_order_sequence:
        self._crossref_complete[colour] = True
        self._crossref_flag_id[colour]  = str(precondition_oid)
    else:
        self._crossref_flag_id[colour] = (
            f"pending_precondition_not_mastered:{precondition_oid}"
        )


def _v17_attractor_mastery_step(self, att_oid):
    """V17World: mastery step lookup by object_id."""
    if att_oid not in self.agent.mastery_order_sequence:
        return None
    prov = getattr(self, "_provenance_store_ref", None)
    if prov is not None:
        flag_id = f"mastery:{att_oid}"
        record = prov.records.get(flag_id)
        if record is not None:
            try:
                return int(record.flag_set_step)
            except (TypeError, ValueError, AttributeError):
                return None
    return None


def _v17_family_summary_metrics(self):
    """V17World: summary_metrics using object_ids."""
    from curiosity_agent_v1_7_world import V17World
    if not isinstance(self.world, V17World):
        return _original_family_summary_metrics(self)

    green_att  = _V17_ATT_IDS[GREEN]
    yellow_att = _V17_ATT_IDS[YELLOW]
    green_haz  = _V17_HAZ_IDS[GREEN]
    yellow_haz = _V17_HAZ_IDS[YELLOW]

    return {
        "green_cell_registered":           self._colour_registered[GREEN],
        "green_cell_first_perception_step": self._colour_first_step[GREEN],
        "yellow_cell_registered":           self._colour_registered[YELLOW],
        "yellow_cell_first_perception_step": self._colour_first_step[YELLOW],
        "green_attractor_mastered":
            green_att in self.agent.mastery_order_sequence,
        "green_attractor_mastery_step":
            _v17_attractor_mastery_step(self, green_att),
        "yellow_attractor_mastered":
            yellow_att in self.agent.mastery_order_sequence,
        "yellow_attractor_mastery_step":
            _v17_attractor_mastery_step(self, yellow_att),
        "green_knowledge_banked":
            self.agent.knowledge_banked.get(green_haz, False),
        "green_knowledge_banked_step":
            self.agent.knowledge_banked_step.get(green_haz),
        "yellow_knowledge_banked":
            self.agent.knowledge_banked.get(yellow_haz, False),
        "yellow_knowledge_banked_step":
            self.agent.knowledge_banked_step.get(yellow_haz),
        "green_crossref_complete":   self._crossref_complete[GREEN],
        "yellow_crossref_complete":  self._crossref_complete[YELLOW],
        "family_traversal_narrative": self._build_traversal_narrative(),
    }


def _v17_family_full_record(self):
    """V17World: full_record using object_ids."""
    from curiosity_agent_v1_7_world import V17World
    if not isinstance(self.world, V17World):
        return _original_family_full_record(self)

    summary = _v17_family_summary_metrics(self)
    green_att  = _V17_ATT_IDS[GREEN]
    yellow_att = _V17_ATT_IDS[YELLOW]
    green_haz  = _V17_HAZ_IDS[GREEN]
    yellow_haz = _V17_HAZ_IDS[YELLOW]
    green_dist  = _V17_DIST_IDS[GREEN]
    yellow_dist = _V17_DIST_IDS[YELLOW]

    record = dict(self.meta)
    record.update({
        "green_colour_cell_coord":        green_dist,
        "green_attractor_coord":          green_att,
        "green_hazard_coord":             green_haz,
        "green_cell_registered":          summary["green_cell_registered"],
        "green_cell_first_perception_step": summary["green_cell_first_perception_step"],
        "green_cell_first_perception_mode": self._colour_first_mode[GREEN],
        "green_attractor_mastered":       summary["green_attractor_mastered"],
        "green_attractor_mastery_step":   summary["green_attractor_mastery_step"],
        "green_attractor_colour":         self.world.object_colour.get(green_att),
        "green_attractor_form":           self.world.object_form.get(green_att),
        "green_knowledge_banked":         summary["green_knowledge_banked"],
        "green_knowledge_banked_step":    summary["green_knowledge_banked_step"],
        "green_knowledge_colour":         self.world.object_colour.get(green_haz),
        "green_knowledge_form":           self.world.object_form.get(green_haz),
        "green_crossref_complete":        summary["green_crossref_complete"],
        "green_crossref_flag_id":         self._crossref_flag_id[GREEN],
        "yellow_colour_cell_coord":       yellow_dist,
        "yellow_attractor_coord":         yellow_att,
        "yellow_hazard_coord":            yellow_haz,
        "yellow_cell_registered":         summary["yellow_cell_registered"],
        "yellow_cell_first_perception_step": summary["yellow_cell_first_perception_step"],
        "yellow_cell_first_perception_mode": self._colour_first_mode[YELLOW],
        "yellow_attractor_mastered":      summary["yellow_attractor_mastered"],
        "yellow_attractor_mastery_step":  summary["yellow_attractor_mastery_step"],
        "yellow_attractor_colour":        self.world.object_colour.get(yellow_att),
        "yellow_attractor_form":          self.world.object_form.get(yellow_att),
        "yellow_knowledge_banked":        summary["yellow_knowledge_banked"],
        "yellow_knowledge_banked_step":   summary["yellow_knowledge_banked_step"],
        "yellow_knowledge_colour":        self.world.object_colour.get(yellow_haz),
        "yellow_knowledge_form":          self.world.object_form.get(yellow_haz),
        "yellow_crossref_complete":       summary["yellow_crossref_complete"],
        "yellow_crossref_flag_id":        self._crossref_flag_id[YELLOW],
        "family_traversal_narrative":     summary["family_traversal_narrative"],
    })
    # Populate self._row for get_substrate()
    self._row = record
    return record


# Store original methods for non-V17 fallback
_original_family_on_pre_action    = V13FamilyObserver.on_pre_action
_original_family_on_post_event    = V13FamilyObserver.on_post_event
_original_family_summary_metrics  = V13FamilyObserver.summary_metrics
_original_family_full_record      = V13FamilyObserver.full_record

# Apply patches
V13FamilyObserver.on_pre_action   = _v17_family_on_pre_action
V13FamilyObserver.on_post_event   = _v17_family_on_post_event
V13FamilyObserver.summary_metrics = _v17_family_summary_metrics
V13FamilyObserver.full_record     = _v17_family_full_record

# Also patch get_substrate to call full_record for V17World
_original_family_get_substrate = V13FamilyObserver.get_substrate

def _v17_family_get_substrate(self):
    from curiosity_agent_v1_7_world import V17World
    if not isinstance(self.world, V17World):
        return _original_family_get_substrate(self)
    try:
        return _v17_family_full_record(self)
    except Exception:
        return None

V13FamilyObserver.get_substrate = _v17_family_get_substrate


from v1_6_substrate_bundle import build_bundle_from_csvs as _build_v16


def build_bundle_from_csvs_v17(
    run_idx, num_steps, seed,
    provenance_csv, schema_csv, family_csv,
    comparison_csv, prediction_error_csv, run_data_csv,
):
    """Build a SubstrateBundle from v1.7 CSV files.

    Identical to v1.6's build_bundle_from_csvs except that the mastery
    flag_id patch uses object_id keys ("mastery:att_green") rather than
    coordinate keys ("mastery:(4, 15)").
    """
    bundle = _build_v16(
        run_idx=run_idx,
        num_steps=num_steps,
        seed=seed,
        provenance_csv=provenance_csv,
        schema_csv=schema_csv,
        family_csv=family_csv,
        comparison_csv=comparison_csv,
        prediction_error_csv=prediction_error_csv,
        run_data_csv=run_data_csv,
    )

    # Replace the v1.6 coord-based mastery patch with the v1.7 object_id patch
    if bundle.family is not None:
        GREEN_ATT_FLAG  = "mastery:att_green"
        YELLOW_ATT_FLAG = "mastery:att_yellow"

        if not bundle.family.get("green_attractor_mastery_step"):
            rec = bundle.provenance.get(GREEN_ATT_FLAG)
            if rec is not None and rec.flag_set_step is not None:
                bundle.family["green_attractor_mastery_step"] = str(rec.flag_set_step)

        if not bundle.family.get("yellow_attractor_mastery_step"):
            rec = bundle.provenance.get(YELLOW_ATT_FLAG)
            if rec is not None and rec.flag_set_step is not None:
                bundle.family["yellow_attractor_mastery_step"] = str(rec.flag_set_step)

    return bundle

# ===========================================================================
# AMENDMENT 1 (v1.7.1) — Three substrate-interface fixes
#
# Fix 1: V1ProvenanceStore confirmation checks use world.agent_pos == cell
#         which compares (x,y,z) float tuple against object_id string in
#         V17World — always False. Patch to use world._contact_at_pos().
#
# Fix 2: V13SchemaObserver.EXPECTED_CELL_TYPES does not include DIST_OBJ,
#         causing schema_complete = False in all V17World runs.
#         Patch to add DIST_OBJ to the expected set for V17World.
#
# Fix 3: Provenance CSV not written by batch runner. Wired in via a
#         post-run flush function called from the batch runner.
# ===========================================================================

from v1_1_provenance import V1ProvenanceStore
from v1_3_schema_extension import V13SchemaObserver


# ---------------------------------------------------------------------------
# Fix 1: Provenance confirmation checks for V17World
# ---------------------------------------------------------------------------
# The provenance store fires confirming observations when:
#   self.world.agent_pos == cell  (mastery, knowledge banking, end-state)
# In V17World, agent_pos is (x,y,z) floats; cell is an object_id string.
# Replace with a contact-radius check via world._contact_at_pos().

_original_prov_post_event = V1ProvenanceStore.on_post_event


def _v17_prov_on_post_event(self, step):
    """V17World-aware on_post_event for V1ProvenanceStore.

    Replaces agent_pos == cell comparisons with contact-based detection
    for V17World. For non-V17 worlds falls back to original.
    """
    from curiosity_agent_v1_7_world import V17World
    if not isinstance(self.world, V17World):
        _original_prov_post_event(self, step)
        return

    from v1_1_provenance import _flag_id

    agent = self.agent
    world = self.world

    # Phase boundary (unchanged — uses agent.phase, not position)
    if agent.phase == 3 and not self._phase_boundary_observed:
        self._phase_boundary_observed = True
        self._record_phase_boundary_confirmations(step)

    # Detect new threat flags (uses agent.cells_flagged_during_run —
    # object_id strings in V17World, no positional comparison needed)
    new_threat = agent.cells_flagged_during_run - self._known_threat_flags
    for cell in new_threat:
        self._record_threat_flag_formation(cell, step)
        self._known_threat_flags.add(cell)
        self._record_signature_match_confirmations(cell, step)

    # Contact-based position detection (replaces agent_pos == cell)
    contacted_oid = world._contact_at_pos(world.agent_pos)

    # Mastery flags: formation + confirmation
    for cell in world.attractor_cells:
        if (agent.mastery_flag.get(cell, 0) == 1
                and _flag_id('mastery', cell) not in self.records):
            self._record_mastery_flag_formation(cell, step)
        if (agent.mastery_flag.get(cell, 0) == 1
                and contacted_oid == cell):
            self._record_mastery_confirmation(cell, step)

    # Competency-unlock transitions
    for cell in agent.transition_order_sequence:
        if cell not in self._known_transitions:
            self._known_transitions.add(cell)
            unlock_step = agent.competency_unlock_step.get(cell)
            if unlock_step is not None:
                self._record_threat_flag_transformation(cell, unlock_step)

    # Knowledge banking: formation + confirmation
    for cell in world.hazard_cells:
        if (agent.knowledge_banked.get(cell, False)
                and _flag_id('knowledge_banking', cell) not in self.records):
            banked_step = agent.knowledge_banked_step.get(cell, step)
            self._record_knowledge_banking_flag_formation(cell, banked_step)
        if (agent.knowledge_banked.get(cell, False)
                and contacted_oid == cell):
            self._record_knowledge_banking_confirmation(cell, step)

    # End-state activation
    if agent.activation_step is not None and not self._known_activation:
        self._known_activation = True
        self._record_end_state_activation_formation(agent.activation_step)

    if self._known_activation:
        self._record_end_state_activation_confirmation(step)

    # End-state banking
    if agent.end_state_banked and not self._known_end_state_banked:
        self._known_end_state_banked = True
        self._record_end_state_banking_flag_formation(
            agent.end_state_found_step
        )
    if (agent.end_state_banked
            and contacted_oid == agent.end_state_cell):
        self._record_end_state_banking_confirmation(step)


V1ProvenanceStore.on_post_event = _v17_prov_on_post_event


# ---------------------------------------------------------------------------
# Fix 2: Schema complete for V17World — add DIST_OBJ to expected set
# ---------------------------------------------------------------------------
# V13SchemaObserver.EXPECTED_CELL_TYPES = {FRAME, NEUTRAL, HAZARD, ATTRACTOR,
#   END_STATE, KNOWLEDGE, COLOUR_CELL}. V17World uses DIST_OBJ instead of
# COLOUR_CELL (same integer constant = 6, different name). Patch the
# expected set for V17World runs at on_run_end time.

_original_schema_on_run_end = V13SchemaObserver.on_run_end


def _v17_schema_on_run_end(self, step):
    from curiosity_agent_v1_7_world import V17World
    _w = getattr(self, "_world", None) or getattr(self, "world", None)
    if not isinstance(_w, V17World):
        _original_schema_on_run_end(self, step)
        return

    # Swap COLOUR_CELL for DIST_OBJ in the expected set
    original_expected = V13SchemaObserver.EXPECTED_CELL_TYPES
    V13SchemaObserver.EXPECTED_CELL_TYPES = (
        original_expected - {'COLOUR_CELL'} | {'DIST_OBJ'}
    )
    try:
        _original_schema_on_run_end(self, step)
        # Update arch tag
        if self._row is not None:
            self._row['arch'] = self._meta.get('arch', 'v1_7')
            # Replace COLOUR_CELL column name with DIST_OBJ in the row
            # (the column was serialised as ct_COLOUR_CELL_* by the parent;
            # rename the keys to ct_DIST_OBJ_*)
            cc_keys = [k for k in self._row if k.startswith('ct_COLOUR_CELL_')]
            for k in cc_keys:
                new_k = k.replace('ct_COLOUR_CELL_', 'ct_DIST_OBJ_')
                self._row[new_k] = self._row.pop(k)
    finally:
        V13SchemaObserver.EXPECTED_CELL_TYPES = original_expected


V13SchemaObserver.on_run_end = _v17_schema_on_run_end


# ---------------------------------------------------------------------------
# Fix 3: Provenance CSV flush helper
# ---------------------------------------------------------------------------
# Called from the batch runner after each run to write provenance records.

def flush_provenance_csv(prov_obs, path, first_run=False):
    """Write provenance records for one run to the provenance CSV.

    first_run=True writes the header; subsequent runs append.
    """
    prov_obs.write_provenance_csv(path, append=not first_run)
