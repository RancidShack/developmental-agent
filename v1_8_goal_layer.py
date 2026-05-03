"""
v1_8_goal_layer.py  (v1.8.1 amendment applied)
-------------------
V18GoalObserver: the eighth cognitive component. The seventh parallel
observer in the programme's observer stack.

Responsibility: assign a deterministic goal to each run, track
environmental mapping and motivated engagement separately, and emit
five record types for inclusion in the SubstrateBundle.

ARCHITECTURAL ROLE
The goal layer is the first component in the programme that gives the
agent's developmental arc a direction. Prior iterations recorded what
happened; this layer records what the agent was trying to achieve,
when it located the target in the environment, when it first engaged
with it, and whether it succeeded.

V1.8.1 AMENDMENT — MONTESSORI PRECEPT RESTORED
Phase 1 is environmental mapping: the agent surveys the prepared
environment, perceives what is available, registers where things are.
Phase 2 is motivated engagement: the agent chooses what to approach
and work on. Goal-directedness is a Phase 2 phenomenon.

The v1.8 implementation recorded first perception (Phase 1) as
goal_progress. This conflated mapping with engagement, producing
goal-resolution windows anchored to deterministic Phase 1 events
with no cost-sensitivity. The amendment corrects this:

  goal_environment_mapped  — fires on first perception of the target's
                             distal object, any phase (mapping event)
  goal_progress            — fires on first ATTRACTOR MASTERY within
                             the target family (Phase 2+) for
                             locate_family goals; on first HAZARD
                             CONTACT (cost paid, Phase 2+) for
                             bank_hazard_within_budget goals

Phase 1 navigation is unchanged. The waypoint sweep runs to completion.
The agent continues to map the environment in Phase 1. Only the goal
layer's interpretation of Phase 1 perception changes.

ADDITIVE DISCIPLINE
The goal observer does not modify the agent, world, or any existing
observer. With goal_obs=None, output is byte-identical to v1.7.

OBSERVER PATTERN
  on_pre_action(step)  — emits goal_set record at step 0 only.
  on_post_event(step)  — checks mapping, progress, and resolution.
  on_run_end(step)     — finalises expiry if not already resolved.
  get_substrate()      — returns the complete goal substrate dict.

GOAL TYPES (v1.8.1 progress definitions)

  locate_family:
    Target: a family colour ("GREEN" or "YELLOW").
    Mapping:  first perception of dist_green / dist_yellow (any phase).
    Progress: first attractor mastery within target family (Phase 2+).
    Resolution: agent contacted all three family objects within budget.

  bank_hazard_within_budget:
    Target: a specific hazard object_id ("haz_green").
    Mapping:  first perception of target hazard (any phase).
    Progress: first contact with target hazard (cost paid, Phase 2+).
    Resolution: world.object_type[target_id] == KNOWLEDGE.

  achieve_end_state:
    Target: "end_state".
    Mapping:  not applicable.
    Progress: agent.activation_step non-None (Phase 2/3).
    Resolution: activation within step budget.

GOAL ASSIGNMENT SCHEDULE
  run_idx % 3 == 0  =>  locate_family,            target="GREEN"
  run_idx % 3 == 1  =>  locate_family,            target="YELLOW"
  run_idx % 3 == 2  =>  bank_hazard_within_budget, target="haz_green"

  step_budget = int(num_steps * BUDGET_FRACTION)  (BUDGET_FRACTION = 0.5)

GOAL-RESOLUTION WINDOW
  Developmental distance between last_progress_step (first motivated
  engagement, Phase 2+) and step_budget. Cost-sensitive: anchored to
  Phase 2 behaviour. None if goal_progress never fired (agent surveyed
  environment but never engaged with target in Phase 2).
"""

import csv

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BUDGET_FRACTION = 0.5

GOAL_SCHEDULE = {
    0: ("locate_family",             "GREEN"),
    1: ("locate_family",             "YELLOW"),
    2: ("bank_hazard_within_budget", "haz_green"),
}

_FAMILY_OBJECTS = {
    "GREEN":  frozenset({"dist_green",  "att_green",  "haz_green"}),
    "YELLOW": frozenset({"dist_yellow", "att_yellow", "haz_yellow"}),
}
_DISTAL_OID = {
    "GREEN":  "dist_green",
    "YELLOW": "dist_yellow",
}
_ATTRACTOR_OID = {
    "GREEN":  "att_green",
    "YELLOW": "att_yellow",
}

GOAL_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps",
    "goal_type", "target_id", "step_budget", "set_at_step",
    "mapped_at_step", "mapped_in_phase",
    "goal_resolved", "resolution_step", "budget_remaining",
    "goal_expired", "last_progress_step", "goal_resolution_window",
    "progress_event_count",
]


def assign_goal(run_idx, num_steps):
    """Return (goal_type, target_id, step_budget) for this run_idx."""
    goal_type, target_id = GOAL_SCHEDULE[run_idx % 3]
    step_budget = int(num_steps * BUDGET_FRACTION)
    return goal_type, target_id, step_budget


class V18GoalObserver:
    """Seventh parallel observer. v1.8.1: mapping and engagement separated."""

    def __init__(self, agent, world, run_meta, goal_type, target_id, step_budget):
        self._agent       = agent
        self._world       = world
        self._meta        = run_meta
        self._goal_type   = goal_type
        self._target_id   = target_id
        self._step_budget = step_budget

        self._family_objects = (
            _FAMILY_OBJECTS.get(target_id, frozenset())
            if goal_type == "locate_family" else frozenset()
        )

        self._contacts_made    = set()
        self._goal_set_record  = None
        self._mapped_record    = None
        self._mapped           = False
        self._progress_records = []
        self._resolved_record  = None
        self._expired_record   = None
        self._resolved         = False
        self._prev_mastery_len = 0
        self._hazard_contacted = False

    # ------------------------------------------------------------------
    # Hook methods
    # ------------------------------------------------------------------

    def on_pre_action(self, step):
        if step == 0:
            self._goal_set_record = {
                "goal_type":   self._goal_type,
                "target_id":   self._target_id,
                "step_budget": self._step_budget,
                "set_at_step": 0,
            }

    def on_post_event(self, step):
        if self._resolved:
            return
        self._check_mapping(step)
        self._check_progress(step)
        self._check_resolution(step)

    def on_run_end(self, total_steps):
        if not self._resolved:
            last_progress = (
                self._progress_records[-1]["progress_step"]
                if self._progress_records else None
            )
            goal_rw = (
                self._step_budget - last_progress
                if last_progress is not None else None
            )
            self._expired_record = {
                "expired_at_step":        self._step_budget,
                "last_progress_step":     last_progress,
                "goal_resolution_window": goal_rw,
            }

    # ------------------------------------------------------------------
    # Mapping (Phase 1+): environmental survey
    # ------------------------------------------------------------------

    def _check_mapping(self, step):
        """Record first perception of the target — any phase.

        This is the survey event: the agent has located the target in
        the prepared environment. It is not goal progress.
        """
        if self._mapped:
            return

        if self._goal_type == "locate_family":
            distal_id = _DISTAL_OID.get(self._target_id, "")
            if distal_id and distal_id in self._get_perceived_objects():
                self._mapped = True
                self._mapped_record = {
                    "mapped_at_step":  step,
                    "mapped_in_phase": getattr(self._agent, 'phase', None),
                }

        elif self._goal_type == "bank_hazard_within_budget":
            if self._target_id in self._get_perceived_objects():
                self._mapped = True
                self._mapped_record = {
                    "mapped_at_step":  step,
                    "mapped_in_phase": getattr(self._agent, 'phase', None),
                }

    # ------------------------------------------------------------------
    # Progress (Phase 2+): motivated engagement
    # ------------------------------------------------------------------

    def _check_progress(self, step):
        """Record first motivated engagement — Phase 2+ only, within window.

        locate_family:            first attractor mastery in target family.
        bank_hazard_within_budget: first hazard contact with cost paid.
        achieve_end_state:        end-state activation.

        Gated on agent.phase >= 2 (Phase 1 is mapping, not engagement)
        and step < step_budget (progress outside the observation window
        does not count toward the goal-resolution window calculation).
        """
        if getattr(self._agent, 'phase', 1) < 2:
            return
        if step >= self._step_budget:
            return   # outside observation window

        if self._goal_type == "locate_family":
            att_oid = _ATTRACTOR_OID.get(self._target_id, "")
            if not att_oid:
                return
            mastery_seq = getattr(self._agent, 'mastery_order_sequence', [])
            current_len = len(mastery_seq)
            if current_len > self._prev_mastery_len:
                newly_mastered = mastery_seq[self._prev_mastery_len:]
                self._prev_mastery_len = current_len
                if att_oid in newly_mastered and not self._progress_records:
                    self._progress_records.append({
                        "progress_type": "attractor_mastered",
                        "progress_step": step,
                    })
            else:
                self._prev_mastery_len = current_len

        elif self._goal_type == "bank_hazard_within_budget":
            if not self._hazard_contacted and not self._progress_records:
                contact = self._world._contact_at_pos(self._world.agent_pos)
                if contact == self._target_id:
                    pre_entries = getattr(
                        self._agent, 'pre_transition_hazard_entries', {}
                    )
                    if pre_entries.get(self._target_id, 0) > 0:
                        self._hazard_contacted = True
                        self._progress_records.append({
                            "progress_type": "hazard_first_contact",
                            "progress_step": step,
                        })

        elif self._goal_type == "achieve_end_state":
            if (not self._progress_records
                    and getattr(self._agent, 'activation_step', None) is not None):
                self._progress_records.append({
                    "progress_type": "end_state_activated",
                    "progress_step": step,
                })

    # ------------------------------------------------------------------
    # Resolution (within observation window only)
    # ------------------------------------------------------------------

    def _check_resolution(self, step):
        """Detect resolution within the observation window.

        Budget is a measurement window, not a time pressure.
        The learner continues; the record notes what was achieved
        within the observation period.
        """
        if step >= self._step_budget:
            return

        if self._goal_type == "locate_family":
            contact = self._world._contact_at_pos(self._world.agent_pos)
            if contact and contact in self._family_objects:
                self._contacts_made.add(contact)
            if self._contacts_made >= self._family_objects:
                self._fire_resolved(step)

        elif self._goal_type == "bank_hazard_within_budget":
            from curiosity_agent_v1_7_world import KNOWLEDGE
            if self._world.object_type.get(self._target_id) == KNOWLEDGE:
                self._fire_resolved(step)

        elif self._goal_type == "achieve_end_state":
            if getattr(self._agent, 'activation_step', None) is not None:
                self._fire_resolved(step)

    def _fire_resolved(self, step):
        if self._resolved:
            return
        self._resolved = True
        self._resolved_record = {
            "resolved_at_step": step,
            "budget_remaining": max(0, self._step_budget - step),
        }

    # ------------------------------------------------------------------
    # Perceived objects helper
    # ------------------------------------------------------------------

    def _get_perceived_objects(self):
        world = self._world
        pos   = world.agent_pos
        if hasattr(world, 'perceive_within_radius'):
            r = getattr(world, 'perception_radius',
                        getattr(world, 'r_perceive', 3.0))
            return {oid for _, oid in world.perceive_within_radius(pos, r)}
        contact = world._contact_at_pos(pos)
        return {contact} if contact else set()

    # ------------------------------------------------------------------
    # Substrate interface
    # ------------------------------------------------------------------

    def get_substrate(self):
        resolved = self._resolved_record is not None
        expired  = self._expired_record  is not None
        return {
            "goal_set":               self._goal_set_record,
            "goal_environment_mapped": self._mapped_record,
            "goal_progress":          list(self._progress_records),
            "goal_resolved":          self._resolved_record,
            "goal_expired":           self._expired_record,
            "goal_summary": {
                "goal_type":              self._goal_type,
                "target_id":              self._target_id,
                "step_budget":            self._step_budget,
                "mapped":                 self._mapped,
                "mapped_at_step": (
                    self._mapped_record["mapped_at_step"]
                    if self._mapped_record else None
                ),
                "mapped_in_phase": (
                    self._mapped_record["mapped_in_phase"]
                    if self._mapped_record else None
                ),
                "resolved":               resolved,
                "resolution_step": (
                    self._resolved_record["resolved_at_step"]
                    if resolved else None
                ),
                "budget_remaining": (
                    self._resolved_record["budget_remaining"]
                    if resolved else None
                ),
                "expired":                expired,
                "last_progress_step": (
                    self._expired_record["last_progress_step"]
                    if expired else None
                ),
                "goal_resolution_window": (
                    self._expired_record["goal_resolution_window"]
                    if expired else None
                ),
            },
        }

    def goal_row(self):
        sub = self.get_substrate()
        s   = sub["goal_summary"]
        return {
            "arch":                   self._meta.get("arch", "v1_8"),
            "run_idx":                self._meta.get("run_idx"),
            "seed":                   self._meta.get("seed"),
            "hazard_cost":            self._meta.get("hazard_cost"),
            "num_steps":              self._meta.get("num_steps"),
            "goal_type":              self._goal_type,
            "target_id":              self._target_id,
            "step_budget":            self._step_budget,
            "set_at_step":            0,
            "mapped_at_step":         s["mapped_at_step"],
            "mapped_in_phase":        s["mapped_in_phase"],
            "goal_resolved":          s["resolved"],
            "resolution_step":        s["resolution_step"],
            "budget_remaining":       s["budget_remaining"],
            "goal_expired":           s["expired"],
            "last_progress_step":     s["last_progress_step"],
            "goal_resolution_window": s["goal_resolution_window"],
            "progress_event_count":   len(self._progress_records),
        }

    def write_goal_csv(self, path, append=False):
        def _file_has_rows(p):
            try:
                with open(p) as f:
                    return sum(1 for l in f if l.strip()) > 1
            except FileNotFoundError:
                return False
        mode = "a" if append else "w"
        write_header = (not append) or (not _file_has_rows(path))
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=GOAL_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {k: self.goal_row().get(k, "") for k in GOAL_FIELDS}
            )
