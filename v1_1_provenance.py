"""
v1_1_provenance.py
------------------
v1.1 provenance store. A parallel observer module modelled on
v1_0_recorder.V1Recorder. Holds formation records for the four
flag types (threat, mastery, knowledge-banking, end-state) and
manages bidirectional cross-references between threat flags and
knowledge-banking flags that derive from the same coordinate
through v0.14 competency-gated transformation.

ARCHITECTURE PRINCIPLE
The agent and world are unmodified. Every attribute the records
require is already exposed by v0.14 for the v1.0 instrumentation.
This module observes flag-state changes from the outside, writing
records as events occur. The agent never reads the records back.

HOOK PATTERN
Three hooks called by the batch runner:

  on_pre_action(step):
    Largely a no-op for v1.1. Reserved for future iterations
    where pre-action provenance state is consulted; currently
    used only to capture the agent's pre-action mastery count
    so check_competency_unlocks transitions can be detected
    against a baseline.

  on_post_event(step):
    Detects state changes since the previous call by comparing
    current agent state against the store's recorded flags.
    Creates new provenance records for newly-formed flags.
    Increments confirming-observation counts where the per-flag-
    type confirmation logic fires. Handles the cross-reference
    resolution when a v0.14 transformation event is detected.
    Updates last_observation_step and last_confirmation_step.

  on_run_end(step):
    Finalises any pending updates. Computes the per-run aggregate
    fields exposed via summary_metrics() for the per-run CSV.

CONFIRMATION SEMANTICS (v1.1 pre-registration §2.2)
Threat flags: incremented on (a) v0.12 signature-matching first-
  entry conversion at adjacent same-category cells; (b) the rare
  forced-entry case where the gating mechanism leaves no other
  action available; (c) the Phase 2 -> Phase 3 boundary if the
  cell remains a hazard at that boundary.
Mastery flags: incremented on each post-banking visit where the
  four mastery interventions are observed to hold.
Knowledge-banking flags: identical to mastery flags, applied to
  the post-transition population.
End-state activation: deterministically equal to the post-
  activation window length; reported but not used as a substantive
  density metric.
End-state banking: identical to mastery flags, applied to the
  end-state cell.

DISCONFIRMATION SEMANTICS (v1.1 pre-registration §2.3)
Narrow: incremented only on threat flags whose cell undergoes
v0.14 competency-gated transformation. The slot exists for all
flag types; the v1.1 architecture increments it only in this one
case.

CROSS-REFERENCE SEMANTICS (v1.1 pre-registration §2.4)
Bidirectional:
  - Threat flag F at coordinate C: when the cell transitions to
    KNOWLEDGE at step N, F.transformed_at_step is set to N and
    F.derived_knowledge_flag_id is set to a placeholder (the
    eventual knowledge-banking flag id).
  - Knowledge-banking flag K at coordinate C: when K forms at
    step M (M > N, post the third post-transition entry), K's
    derived_from_threat_flag_id is set to F's id.
  - F.derived_knowledge_flag_id is updated from the placeholder
    to the resolved K id at the same moment.
"""

import csv
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, List, Any


# Schema for the snapshot CSV. Records are written one row per
# flag per snapshot moment.
SNAPSHOT_FIELDS = [
    "arch", "hazard_cost", "num_steps", "run_idx", "seed",
    "snapshot_step", "snapshot_event",
    "flag_type", "flag_coord", "flag_id",
    "flag_set_step",
    "confirming_observations",
    "disconfirming_observations",
    "last_confirmation_step",
    "last_observation_step",
    "transformed_at_step",
    "derived_knowledge_flag_id",
    "derived_from_threat_flag_id",
]

# Schema for the formation-narrative CSV. One row per formed flag
# per run. Includes the per-flag fields plus the run-level keys.
PROVENANCE_FIELDS = [
    "arch", "hazard_cost", "num_steps", "run_idx", "seed",
    "flag_type", "flag_coord", "flag_id",
    "flag_set_step",
    "confirming_observations",
    "disconfirming_observations",
    "last_confirmation_step",
    "last_observation_step",
    "transformed_at_step",
    "derived_knowledge_flag_id",
    "derived_from_threat_flag_id",
]


@dataclass
class ProvenanceRecord:
    """One formation record. Held in the provenance store, keyed by
    flag_id. Cross-references are stored as flag_id strings rather
    than direct object references so that records remain serialisable
    and so that forward-reference placeholders can be resolved
    explicitly rather than by mutation of a shared object."""
    flag_type: str
    flag_coord: Optional[Tuple[int, int]]
    flag_id: str
    flag_set_step: int
    confirming_observations: int = 0
    disconfirming_observations: int = 0
    last_confirmation_step: Optional[int] = None
    last_observation_step: Optional[int] = None
    transformed_at_step: Optional[int] = None
    derived_knowledge_flag_id: Optional[str] = None
    derived_from_threat_flag_id: Optional[str] = None


def _flag_id(flag_type: str, coord: Optional[Tuple[int, int]]) -> str:
    """Canonical flag identifier."""
    if flag_type == "end_state_activation":
        return "end_state_activation"
    return f"{flag_type}:{coord}"


def _record_to_row(record: ProvenanceRecord,
                    run_metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "arch": run_metadata.get("arch"),
        "hazard_cost": run_metadata.get("hazard_cost"),
        "num_steps": run_metadata.get("num_steps"),
        "run_idx": run_metadata.get("run_idx"),
        "seed": run_metadata.get("seed"),
        "flag_type": record.flag_type,
        "flag_coord": str(record.flag_coord) if record.flag_coord else "",
        "flag_id": record.flag_id,
        "flag_set_step": record.flag_set_step,
        "confirming_observations": record.confirming_observations,
        "disconfirming_observations": record.disconfirming_observations,
        "last_confirmation_step": record.last_confirmation_step,
        "last_observation_step": record.last_observation_step,
        "transformed_at_step": record.transformed_at_step,
        "derived_knowledge_flag_id": record.derived_knowledge_flag_id,
        "derived_from_threat_flag_id": record.derived_from_threat_flag_id,
    }


class V1ProvenanceStore:
    """v1.1 provenance store. Modelled on V1Recorder's interface
    pattern: instantiated per run with read-only access to the agent
    and world; receives hook calls from the batch runner; produces
    CSV outputs and reset() between runs.

    The store does NOT modify the agent or the world. The architecture
    under v1.1 is byte-identical to v1.0 with this store either
    instantiated or not; what differs is what gets written to disk.
    """

    def __init__(self, agent, world, run_metadata: Dict[str, Any],
                 cell_type_constants: Dict[str, int]):
        self.agent = agent
        self.world = world
        self.run_metadata = run_metadata
        self.ctc = cell_type_constants

        # The provenance store proper: keyed by flag_id.
        self.records: Dict[str, ProvenanceRecord] = {}

        # Tracking state for change detection. Working memory only;
        # not part of the records.
        self._known_threat_flags: set = set()
        self._known_transitions: set = set()
        self._known_activation: bool = False
        self._known_end_state_banked: bool = False

        # Phase boundary tracking for threat-flag confirmation rule (c).
        self._phase_boundary_observed: bool = False

        # Snapshot accumulator.
        self._snapshots: List[Dict[str, Any]] = []

        # Pre-action mastery count, captured at on_pre_action.
        self._pre_action_mastery_count: int = 0

    # ----------------------------------------------------------------
    # Hook interface
    # ----------------------------------------------------------------

    def on_pre_action(self, step: int) -> None:
        """Called immediately before agent.choose_action /
        get_prescribed_action. Captures the pre-action mastery count
        for post-event detection."""
        self._pre_action_mastery_count = sum(self.agent.mastery_flag.values())

    def on_post_event(self, step: int) -> None:
        """Called after agent.record_action_outcome completes.
        Detects all flag-formation events that fired during the step
        and writes the corresponding provenance records. Increments
        confirming-observation counts where applicable."""

        # Phase boundary check (threat-flag confirmation rule c).
        if self.agent.phase == 3 and not self._phase_boundary_observed:
            self._phase_boundary_observed = True
            self._record_phase_boundary_confirmations(step)

        # Detect new threat flags.
        new_threat = (self.agent.cells_flagged_during_run
                      - self._known_threat_flags)
        for cell in new_threat:
            self._record_threat_flag_formation(cell, step)
            self._known_threat_flags.add(cell)
            # Signature-match confirmations for previously-formed
            # threat flags. The new flag's formation is itself the
            # confirmation event.
            self._record_signature_match_confirmations(cell, step)

        # Detect new mastery flags and confirmations on existing ones.
        for cell in self.world.attractor_cells:
            if (self.agent.mastery_flag.get(cell, 0) == 1
                    and _flag_id("mastery", cell) not in self.records):
                self._record_mastery_flag_formation(cell, step)
            if (self.agent.mastery_flag.get(cell, 0) == 1
                    and self.world.agent_pos == cell):
                self._record_mastery_confirmation(cell, step)

        # Detect competency-unlock transitions.
        for cell in self.agent.transition_order_sequence:
            if cell not in self._known_transitions:
                self._known_transitions.add(cell)
                unlock_step = self.agent.competency_unlock_step.get(cell)
                if unlock_step is not None:
                    self._record_threat_flag_transformation(cell, unlock_step)

        # Detect new knowledge-banking flags and confirmations on existing.
        for cell in self.world.hazard_cells:
            if (self.agent.knowledge_banked.get(cell, False)
                    and _flag_id("knowledge_banking", cell) not in self.records):
                banked_step = self.agent.knowledge_banked_step.get(cell, step)
                self._record_knowledge_banking_flag_formation(
                    cell, banked_step
                )
            if (self.agent.knowledge_banked.get(cell, False)
                    and self.world.agent_pos == cell):
                self._record_knowledge_banking_confirmation(cell, step)

        # Detect end-state activation.
        if (self.agent.activation_step is not None
                and not self._known_activation):
            self._known_activation = True
            self._record_end_state_activation_formation(
                self.agent.activation_step
            )

        # End-state activation confirmation (deterministic per step).
        if self._known_activation:
            self._record_end_state_activation_confirmation(step)

        # Detect end-state banking.
        if (self.agent.end_state_banked
                and not self._known_end_state_banked):
            self._known_end_state_banked = True
            self._record_end_state_banking_flag_formation(
                self.agent.end_state_found_step
            )
        if (self.agent.end_state_banked
                and self.world.agent_pos == self.agent.end_state_cell):
            self._record_end_state_banking_confirmation(step)

    def on_run_end(self, final_step: int) -> None:
        """Called once at end of run. Emits a final snapshot per record."""
        for fid, record in self.records.items():
            self._emit_snapshot(final_step, "run_end", record)

    # ----------------------------------------------------------------
    # Formation handlers
    # ----------------------------------------------------------------

    def _record_threat_flag_formation(self, cell: Tuple[int, int],
                                       step: int) -> None:
        fid = _flag_id("threat", cell)
        record = ProvenanceRecord(
            flag_type="threat",
            flag_coord=cell,
            flag_id=fid,
            flag_set_step=step,
            last_observation_step=step,
        )
        self.records[fid] = record
        self._emit_snapshot(step, "threat_flag_formation", record)

    def _record_mastery_flag_formation(self, cell: Tuple[int, int],
                                        step: int) -> None:
        fid = _flag_id("mastery", cell)
        record = ProvenanceRecord(
            flag_type="mastery",
            flag_coord=cell,
            flag_id=fid,
            flag_set_step=step,
            last_observation_step=step,
        )
        self.records[fid] = record
        self._emit_snapshot(step, "mastery_flag_formation", record)

    def _record_knowledge_banking_flag_formation(self, cell: Tuple[int, int],
                                                  step: int) -> None:
        fid = _flag_id("knowledge_banking", cell)
        record = ProvenanceRecord(
            flag_type="knowledge_banking",
            flag_coord=cell,
            flag_id=fid,
            flag_set_step=step,
            last_observation_step=step,
        )
        # Cross-reference back to the originating threat flag if one exists.
        threat_fid = _flag_id("threat", cell)
        if threat_fid in self.records:
            record.derived_from_threat_flag_id = threat_fid
            # Resolve the placeholder on the threat-flag record.
            self.records[threat_fid].derived_knowledge_flag_id = fid
        self.records[fid] = record
        self._emit_snapshot(step, "knowledge_banking_flag_formation", record)

    def _record_threat_flag_transformation(self, cell: Tuple[int, int],
                                            step: int) -> None:
        """v0.14 competency-gated transformation. Increments the
        threat flag's disconfirming-observations count under v1.1's
        narrow semantics. Sets transformed_at_step and the placeholder
        forward-reference."""
        threat_fid = _flag_id("threat", cell)
        if threat_fid not in self.records:
            # Cell transformed without prior threat-flag formation.
            return
        record = self.records[threat_fid]
        record.transformed_at_step = step
        record.disconfirming_observations += 1
        record.derived_knowledge_flag_id = _flag_id("knowledge_banking", cell)
        record.last_observation_step = step
        self._emit_snapshot(step, "threat_flag_transformation", record)

    def _record_end_state_activation_formation(self, step: int) -> None:
        fid = _flag_id("end_state_activation", None)
        record = ProvenanceRecord(
            flag_type="end_state_activation",
            flag_coord=None,
            flag_id=fid,
            flag_set_step=step,
            last_observation_step=step,
        )
        self.records[fid] = record
        self._emit_snapshot(step, "end_state_activation_formation", record)

    def _record_end_state_banking_flag_formation(self, step: int) -> None:
        cell = self.agent.end_state_cell
        fid = _flag_id("end_state_banking", cell)
        record = ProvenanceRecord(
            flag_type="end_state_banking",
            flag_coord=cell,
            flag_id=fid,
            flag_set_step=step,
            last_observation_step=step,
        )
        self.records[fid] = record
        self._emit_snapshot(step, "end_state_banking_flag_formation", record)

    # ----------------------------------------------------------------
    # Confirmation handlers
    # ----------------------------------------------------------------

    def _record_signature_match_confirmations(self, new_cell: Tuple[int, int],
                                               step: int) -> None:
        """Threat-flag confirmation rule (a): the new flag's formation
        is itself a confirmation of every existing threat flag, because
        signature-matching predicts that other cells of the same
        category would be hazardous and the new entry instantiated
        that prediction."""
        for fid, record in self.records.items():
            if record.flag_type != "threat":
                continue
            if record.flag_coord == new_cell:
                continue
            record.confirming_observations += 1
            record.last_confirmation_step = step
            record.last_observation_step = step

    def _record_phase_boundary_confirmations(self, step: int) -> None:
        """Threat-flag confirmation rule (c): at the Phase 2 -> Phase 3
        boundary, every threat flag whose cell remains HAZARD-typed
        receives one confirming observation."""
        hazard_const = self.ctc["HAZARD"]
        for fid, record in self.records.items():
            if record.flag_type != "threat":
                continue
            cell_type_now = self.world.cell_type.get(
                record.flag_coord, hazard_const
            )
            if cell_type_now == hazard_const:
                record.confirming_observations += 1
                record.last_confirmation_step = step
                record.last_observation_step = step

    def _record_mastery_confirmation(self, cell: Tuple[int, int],
                                      step: int) -> None:
        """Post-banking visit to a mastered attractor."""
        fid = _flag_id("mastery", cell)
        if fid not in self.records:
            return
        record = self.records[fid]
        if step == record.flag_set_step:
            return
        record.confirming_observations += 1
        record.last_confirmation_step = step
        record.last_observation_step = step

    def _record_knowledge_banking_confirmation(self, cell: Tuple[int, int],
                                                step: int) -> None:
        """Post-banking visit to a knowledge-banked cell."""
        fid = _flag_id("knowledge_banking", cell)
        if fid not in self.records:
            return
        record = self.records[fid]
        if step == record.flag_set_step:
            return
        record.confirming_observations += 1
        record.last_confirmation_step = step
        record.last_observation_step = step

    def _record_end_state_activation_confirmation(self, step: int) -> None:
        """Deterministic, one-per-post-activation-step."""
        fid = _flag_id("end_state_activation", None)
        if fid not in self.records:
            return
        record = self.records[fid]
        if step == record.flag_set_step:
            return
        record.confirming_observations += 1
        record.last_confirmation_step = step
        record.last_observation_step = step

    def _record_end_state_banking_confirmation(self, step: int) -> None:
        """Post-banking visit to the end-state cell."""
        cell = self.agent.end_state_cell
        fid = _flag_id("end_state_banking", cell)
        if fid not in self.records:
            return
        record = self.records[fid]
        if step == record.flag_set_step:
            return
        record.confirming_observations += 1
        record.last_confirmation_step = step
        record.last_observation_step = step

    # ----------------------------------------------------------------
    # Snapshot emission and CSV writing
    # ----------------------------------------------------------------

    def _emit_snapshot(self, step: int, event: str,
                        record: ProvenanceRecord) -> None:
        row = {
            "arch": self.run_metadata.get("arch"),
            "hazard_cost": self.run_metadata.get("hazard_cost"),
            "num_steps": self.run_metadata.get("num_steps"),
            "run_idx": self.run_metadata.get("run_idx"),
            "seed": self.run_metadata.get("seed"),
            "snapshot_step": step,
            "snapshot_event": event,
            "flag_type": record.flag_type,
            "flag_coord": str(record.flag_coord) if record.flag_coord else "",
            "flag_id": record.flag_id,
            "flag_set_step": record.flag_set_step,
            "confirming_observations": record.confirming_observations,
            "disconfirming_observations": record.disconfirming_observations,
            "last_confirmation_step": record.last_confirmation_step,
            "last_observation_step": record.last_observation_step,
            "transformed_at_step": record.transformed_at_step,
            "derived_knowledge_flag_id": record.derived_knowledge_flag_id,
            "derived_from_threat_flag_id": record.derived_from_threat_flag_id,
        }
        self._snapshots.append(row)

    def snapshot_count(self) -> int:
        return len(self._snapshots)

    def record_count(self) -> int:
        return len(self.records)

    def write_snapshots_csv(self, path: str, append: bool = True) -> None:
        mode = "a" if append else "w"
        write_header = not append
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SNAPSHOT_FIELDS)
            if write_header:
                writer.writeheader()
            for row in self._snapshots:
                writer.writerow(row)

    def write_provenance_csv(self, path: str, append: bool = True) -> None:
        mode = "a" if append else "w"
        write_header = not append
        with open(path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=PROVENANCE_FIELDS)
            if write_header:
                writer.writeheader()
            for fid, record in self.records.items():
                row = _record_to_row(record, self.run_metadata)
                writer.writerow(row)

    def reset(self) -> None:
        """Clear in-memory state between runs."""
        self.records.clear()
        self._known_threat_flags.clear()
        self._known_transitions.clear()
        self._known_activation = False
        self._known_end_state_banked = False
        self._phase_boundary_observed = False
        self._snapshots.clear()
        self._pre_action_mastery_count = 0

    # ----------------------------------------------------------------
    # Per-run aggregate metrics
    # ----------------------------------------------------------------

    def summary_metrics(self) -> Dict[str, Any]:
        """Per-run aggregate provenance metrics for the per-run CSV."""
        flag_types = ["threat", "mastery", "knowledge_banking",
                      "end_state_activation", "end_state_banking"]

        def _records_of(t: str) -> List[ProvenanceRecord]:
            return [r for r in self.records.values() if r.flag_type == t]

        out: Dict[str, Any] = {}
        for t in flag_types:
            recs = _records_of(t)
            n = len(recs)
            out[f"prov_{t}_count"] = n
            if n > 0:
                out[f"prov_{t}_mean_set_step"] = sum(
                    r.flag_set_step for r in recs
                ) / n
                out[f"prov_{t}_mean_confirming"] = sum(
                    r.confirming_observations for r in recs
                ) / n
                out[f"prov_{t}_mean_disconfirming"] = sum(
                    r.disconfirming_observations for r in recs
                ) / n
            else:
                out[f"prov_{t}_mean_set_step"] = None
                out[f"prov_{t}_mean_confirming"] = None
                out[f"prov_{t}_mean_disconfirming"] = None

        # Cross-reference completion: threat flags with both
        # transformed_at_step and a resolved knowledge-banking flag.
        threat_recs = _records_of("threat")
        crossref_complete = 0
        crossref_pending = 0
        for r in threat_recs:
            if r.transformed_at_step is not None:
                if (r.derived_knowledge_flag_id is not None
                        and r.derived_knowledge_flag_id in self.records):
                    crossref_complete += 1
                else:
                    crossref_pending += 1
        out["prov_crossref_complete"] = crossref_complete
        out["prov_crossref_pending"] = crossref_pending

        # Formation narrative: ordered "step:flag_id" tuples.
        ordered_records = sorted(
            self.records.values(),
            key=lambda r: (r.flag_set_step, r.flag_id)
        )
        out["prov_formation_narrative"] = "|".join(
            f"{r.flag_set_step}:{r.flag_id}" for r in ordered_records
        )
        out["prov_total_records"] = len(self.records)

        return out
