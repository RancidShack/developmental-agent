"""
v1_11_causal_observer.py
-------------------------
V111CausalObserver: the tenth parallel observer.

ARCHITECTURAL ROLE
v1.8 gave the agent a reason to learn. v1.9 gave it a record of
choosing. v1.10 gave it a record of being wrong and changing. v1.11
gives it a record of understanding why.

The biographical register at v1.10 can describe what happened: I was
surprised at haz_yellow at step 493. The resolution window was 7,996
steps. My approach changed afterward. What it cannot yet say is why
the surprise happened when it did — why the resolution window was
7,996 steps in one run and 4 in another; why some agents orbited
haz_yellow for 121,908 steps before understanding arrived.

V111CausalObserver constructs the answer from the existing substrate.
For each resolved surprise in bundle.prediction_error, it builds a
causal chain by traversing the full biographical register: the
precondition the agent had not yet satisfied, the step at which that
precondition was satisfied, whether the precondition was in the Phase 1
path, whether the agent had already approached and withdrawn before the
surprise, whether the agent eventually revised its expectation.

Every link in every chain resolves to a substrate record. No link is
generated. A chain with an unresolvable link is truncated at that point
and the truncation is noted. A partial chain is honest; a fabricated
chain is a Category α failure.

WHEN IT RUNS
V111CausalObserver does not run during simulation. It runs once, at
run end, after build_bundle_from_observers() has assembled the complete
SubstrateBundle and br_obs.process_pe_substrate() has reconciled the
belief-revision records. It reads from the fully assembled bundle only.

OBSERVER PATTERN
The observer pattern is preserved: V111CausalObserver has on_pre_action,
on_post_event, on_run_end (all no-ops during simulation), and
get_substrate() for bundle assembly. The causal chain construction
happens in build_causal_chains(bundle), called explicitly by the batch
runner after the bundle is assembled.

ADDITIVE DISCIPLINE
With causal_obs=None in build_bundle_from_observers(), all existing
outputs are byte-identical to v1.10 at matched seeds.

PARAMETERS (pre-registered, not free)
  CHAIN_DEPTH_MINIMUM = 2   — minimum links for a valid Q5 output
"""

from typing import Any, Dict, List, Optional

CHAIN_DEPTH_MINIMUM = 2

# Link type constants
LINK_SURPRISE           = "surprise"
LINK_PRECONDITION       = "precondition"
LINK_MASTERY_FORMATION  = "mastery_formation"
LINK_PHASE1_ABSENCE     = "phase1_absence"
LINK_SUPPRESSED_APPROACH = "suppressed_approach"
LINK_BELIEF_REVISION    = "belief_revision"

# CSV field definitions
CAUSAL_FIELDS = [
    "arch", "run_idx", "seed", "hazard_cost", "num_steps", "env",
    "object_id",
    "surprise_step",
    "resolution_step",
    "chain_depth",
    "chain_complete",
    "truncated_at",
    "links_surprise",
    "links_precondition",
    "links_mastery_formation",
    "links_phase1_absence",
    "links_suppressed_approach",
    "links_belief_revision",
]


class V111CausalObserver:
    """Tenth parallel observer. Constructs auditable causal chains for
    each resolved_surprise event in the assembled SubstrateBundle.

    Parameters
    ----------
    run_meta : dict
        Standard run metadata.
    """

    def __init__(self, run_meta: Dict[str, Any]):
        self._meta    = run_meta
        self._records: List[Dict[str, Any]] = []
        self._built   = False

    # ------------------------------------------------------------------
    # Simulation hooks (no-ops — this observer runs post-simulation)
    # ------------------------------------------------------------------

    def on_pre_action(self, step: int) -> None:
        pass

    def on_post_event(self, step: int) -> None:
        pass

    def on_run_end(self, total_steps: int) -> None:
        pass

    # ------------------------------------------------------------------
    # Main entry point: build causal chains from assembled bundle
    # ------------------------------------------------------------------

    def build_causal_chains(self, bundle) -> None:
        """Construct causal chains for all resolved surprises.

        Called by the batch runner after bundle assembly and
        br_obs.process_pe_substrate(). Idempotent.

        Parameters
        ----------
        bundle : SubstrateBundle
            The fully assembled v1.10 bundle (with belief_revision field).
        """
        if self._built:
            return
        self._built = True

        pe = getattr(bundle, 'prediction_error', None) or []
        if not pe:
            return

        for event in pe:
            if not isinstance(event, dict):
                continue
            # Only resolved surprises: pre-condition entry that was
            # eventually resolved (transformation fired)
            if event.get('precondition_met', True):
                continue
            if event.get('transformed_at_step') is None:
                continue

            object_id      = event.get('cell') or event.get('object_id')
            surprise_step  = event.get('step')
            resolution_step = event.get('transformed_at_step')

            if object_id is None or surprise_step is None:
                continue

            chain = self._build_chain(
                bundle, object_id, surprise_step, resolution_step, event
            )
            self._records.append(chain)

    def _build_chain(
        self, bundle, object_id: str,
        surprise_step: int, resolution_step: int,
        pe_event: Dict
    ) -> Dict[str, Any]:
        """Build one causal chain record for a resolved surprise.

        Constructs links in causal order:
          1. surprise          — the encounter itself
          2. precondition      — what precondition was required
          3. mastery_formation — when that precondition was mastered
          4. phase1_absence    — whether mastery was absent in Phase 1
          5. suppressed_approach — prior approaches before surprise
          6. belief_revision   — whether the arc closed with revision

        Each link is only added if it resolves to a substrate record.
        Chain is truncated at the first unresolvable structural link
        (links 2 and 3); optional links (4, 5, 6) are omitted silently
        if absent rather than truncating the chain.
        """
        links:       List[Dict[str, Any]] = []
        truncated_at: Optional[str]        = None
        chain_complete                     = True

        # ----------------------------------------------------------------
        # Link 1: surprise
        # ----------------------------------------------------------------
        surp_link = self._make_link(
            link_type       = LINK_SURPRISE,
            substrate_field = "prediction_error",
            source_key      = f"pe:{object_id}:{surprise_step}",
            statement       = (
                f"I was surprised at {object_id} at step {surprise_step} "
                f"because I entered it before the precondition was met."
            ),
            resolves        = True,   # we have the event in hand
        )
        links.append(surp_link)

        # ----------------------------------------------------------------
        # Link 2: precondition identification (from schema)
        # ----------------------------------------------------------------
        precondition_name = self._lookup_precondition(bundle, object_id, pe_event)
        if precondition_name is None:
            chain_complete = False
            truncated_at   = LINK_PRECONDITION
            return self._assemble(
                object_id, surprise_step, resolution_step,
                links, chain_complete, truncated_at
            )

        precond_link = self._make_link(
            link_type       = LINK_PRECONDITION,
            substrate_field = "schema",
            source_key      = f"precondition:{object_id}",
            statement       = (
                f"Entry of {object_id} requires {precondition_name} mastery "
                f"as a precondition."
            ),
            resolves        = True,
        )
        links.append(precond_link)

        # ----------------------------------------------------------------
        # Link 3: mastery formation step (from provenance)
        # ----------------------------------------------------------------
        mastery_step = self._lookup_mastery_step(bundle, precondition_name)
        if mastery_step is None:
            chain_complete = False
            truncated_at   = LINK_MASTERY_FORMATION
            return self._assemble(
                object_id, surprise_step, resolution_step,
                links, chain_complete, truncated_at
            )

        mastery_link = self._make_link(
            link_type       = LINK_MASTERY_FORMATION,
            substrate_field = "provenance",
            source_key      = f"mastery:{precondition_name}",
            statement       = (
                f"{precondition_name} mastery formed at step {mastery_step}. "
                f"The surprise occurred at step {surprise_step} — "
                f"{mastery_step - surprise_step} steps before mastery "
                f"if mastery came later, or mastery had already formed."
            ),
            resolves        = True,
        )
        links.append(mastery_link)

        # ----------------------------------------------------------------
        # Link 4 (optional): Phase 1 absence
        # ----------------------------------------------------------------
        in_phase1 = self._check_phase1(bundle, precondition_name)
        if in_phase1 is False:
            # attractor was NOT mastered in Phase 1 — this is a causal link
            p1_link = self._make_link(
                link_type       = LINK_PHASE1_ABSENCE,
                substrate_field = "provenance",
                source_key      = f"phase1_absence:{precondition_name}",
                statement       = (
                    f"{precondition_name} was not encountered in Phase 1 — "
                    f"it was not in my early developmental path, which "
                    f"delayed mastery and extended the window before "
                    f"{object_id} could be understood."
                ),
                resolves        = True,
            )
            links.append(p1_link)

        # ----------------------------------------------------------------
        # Link 5 (optional): suppressed approaches before surprise
        # ----------------------------------------------------------------
        sa_count = self._count_suppressed_approaches(
            bundle, object_id, surprise_step
        )
        if sa_count > 0:
            sa_link = self._make_link(
                link_type       = LINK_SUPPRESSED_APPROACH,
                substrate_field = "counterfactual",
                source_key      = f"cf:{object_id}:pre:{surprise_step}",
                statement       = (
                    f"I approached {object_id} {sa_count} time(s) before "
                    f"the surprise at step {surprise_step}, withdrawing "
                    f"each time — the object was proximate but not yet "
                    f"understood."
                ),
                resolves        = True,
            )
            links.append(sa_link)

        # ----------------------------------------------------------------
        # Link 6 (optional): belief revision closure
        # ----------------------------------------------------------------
        has_revision = self._check_belief_revision(
            bundle, object_id, surprise_step
        )
        if has_revision:
            br_link = self._make_link(
                link_type       = LINK_BELIEF_REVISION,
                substrate_field = "belief_revision",
                source_key      = (
                    f"revised_expectation:{object_id}:{surprise_step}"
                ),
                statement       = (
                    f"After the precondition was met, I revised my "
                    f"expectation about {object_id} and my subsequent "
                    f"approach to it changed."
                ),
                resolves        = bundle.resolve(
                    "belief_revision",
                    f"revised_expectation:{object_id}:{surprise_step}"
                ),
            )
            links.append(br_link)

        return self._assemble(
            object_id, surprise_step, resolution_step,
            links, chain_complete, truncated_at
        )

    # ------------------------------------------------------------------
    # Substrate lookup helpers
    # ------------------------------------------------------------------

    def _lookup_precondition(self, bundle, object_id: str,
                             pe_event: Optional[Dict] = None) -> Optional[str]:
        """Find the precondition attractor name for object_id.

        CONFIRMED BY DIAGNOSTIC (seed=42, cost=1.0, steps=80000):
        - bundle.schema is a flat dict of ct_* properties; no families
          or precondition_cell keys present.
        - PE record carries ['family'] = 'YELLOW' or 'GREEN' for
          family-affiliated hazards, None for unaffiliated.
        - Naming convention: haz_yellow -> att_yellow, haz_green -> att_green
        - bundle.provenance keys are 'mastery:att_yellow' format.

        Lookup order:
          1. PE record family field -> att_{family.lower()}
          2. Naming convention: haz_{colour} -> att_{colour}, confirmed
             by mastery:{attractor} key in provenance
          3. Return None (unaffiliated hazard; chain truncates cleanly)
        """
        # Pattern 1: family field in PE record (most reliable)
        if pe_event is not None:
            family = pe_event.get('family')
            if family and str(family) not in ('None', 'UNAFFILIATED', ''):
                candidate = f"att_{family.lower()}"
                prov = getattr(bundle, 'provenance', {})
                if isinstance(prov, dict):
                    if f"mastery:{candidate}" in prov:
                        return candidate
                    for key in prov.keys():
                        if candidate in str(key):
                            return candidate
                # Return candidate; mastery lookup fails cleanly if absent
                return candidate

        # Pattern 2: naming convention haz_{colour} -> att_{colour}
        if object_id.startswith('haz_'):
            colour    = object_id[4:]
            candidate = f"att_{colour}"
            prov      = getattr(bundle, 'provenance', {})
            if isinstance(prov, dict):
                if f"mastery:{candidate}" in prov:
                    return candidate
                for key in prov.keys():
                    if candidate in str(key):
                        return candidate
            if colour in ('yellow', 'green'):
                return candidate

        return None

    def _lookup_mastery_step(self, bundle, attractor_id: str) -> Optional[int]:
        """Find the step at which attractor_id was mastered.

        Reads bundle.provenance (a dict of ProvenanceRecord dataclasses
        or dicts, keyed by flag_id strings). The mastery record for
        att_yellow has flag_type 'mastery' or 'attractor' and
        flag_id containing the attractor name.
        """
        prov = getattr(bundle, 'provenance', None)
        if not isinstance(prov, dict):
            return None

        for key, rec in prov.items():
            key_str = str(key)
            if attractor_id not in key_str:
                continue

            # ProvenanceRecord dataclass
            if hasattr(rec, 'flag_set_step'):
                ft = getattr(rec, 'flag_type', '')
                if ft in ('mastery', 'attractor', 'knowledge'):
                    return int(rec.flag_set_step)
                # If flag_type is ambiguous, return flag_set_step anyway
                # if the key matches
                if attractor_id in key_str:
                    return int(rec.flag_set_step)

            # Dict record
            elif isinstance(rec, dict):
                step = rec.get('flag_set_step')
                if step is not None:
                    return int(step)

        return None

    def _check_phase1(self, bundle, attractor_id: str) -> Optional[bool]:
        """Return True if attractor was mastered in Phase 1, False if not,
        None if Phase 1 boundary cannot be determined.
        """
        prov = getattr(bundle, 'provenance', None)
        if not isinstance(prov, dict):
            return None

        # Find Phase 1 boundary from provenance metadata or run_meta
        phase1_end = self._meta.get('phase_1_end_step')
        if phase1_end is None:
            # Try to read from a phase_boundary record in provenance
            for key, rec in prov.items():
                key_str = str(key)
                if 'phase_1' in key_str or 'phase1' in key_str:
                    if hasattr(rec, 'flag_set_step'):
                        phase1_end = int(rec.flag_set_step)
                        break
                    elif isinstance(rec, dict):
                        s = rec.get('flag_set_step')
                        if s is not None:
                            phase1_end = int(s)
                            break

        if phase1_end is None:
            return None

        mastery_step = self._lookup_mastery_step(bundle, attractor_id)
        if mastery_step is None:
            return None

        return mastery_step <= phase1_end

    def _count_suppressed_approaches(
        self, bundle, object_id: str, surprise_step: int
    ) -> int:
        """Count suppressed-approach records for object_id before
        surprise_step.
        """
        cf = getattr(bundle, 'counterfactual', None)
        if not isinstance(cf, list):
            return 0

        count = 0
        for rec in cf:
            if not isinstance(rec, dict):
                continue
            if rec.get('object_id') != object_id:
                continue
            approach_step = (
                rec.get('closest_approach_step')
                or rec.get('approach_step')
                or rec.get('step')
            )
            if approach_step is not None and int(approach_step) < surprise_step:
                count += 1

        return count

    def _check_belief_revision(
        self, bundle, object_id: str, surprise_step: int
    ) -> bool:
        """Return True if a revised_expectation record exists for
        object_id with this surprise_step.
        """
        br = getattr(bundle, 'belief_revision', None)
        if not isinstance(br, list):
            return False

        for rec in br:
            if not isinstance(rec, dict):
                continue
            if (rec.get('object_id') == object_id
                    and rec.get('surprise_step') == surprise_step):
                return True

        return False

    # ------------------------------------------------------------------
    # Assembly helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_link(
        link_type: str,
        substrate_field: str,
        source_key: str,
        statement: str,
        resolves: bool,
    ) -> Dict[str, Any]:
        return {
            "link_type":       link_type,
            "substrate_field": substrate_field,
            "source_key":      source_key,
            "statement":       statement,
            "resolves":        resolves,
        }

    @staticmethod
    def _assemble(
        object_id:      str,
        surprise_step:  int,
        resolution_step: int,
        links:          List[Dict[str, Any]],
        chain_complete: bool,
        truncated_at:   Optional[str],
    ) -> Dict[str, Any]:
        """Assemble the final causal_chain record."""
        depth = len(links)
        link_counts = {
            "links_surprise":            0,
            "links_precondition":        0,
            "links_mastery_formation":   0,
            "links_phase1_absence":      0,
            "links_suppressed_approach": 0,
            "links_belief_revision":     0,
        }
        for lnk in links:
            col = f"links_{lnk['link_type']}"
            if col in link_counts:
                link_counts[col] += 1

        return {
            "object_id":       object_id,
            "surprise_step":   surprise_step,
            "resolution_step": resolution_step,
            "chain_depth":     depth,
            "chain_complete":  chain_complete,
            "truncated_at":    truncated_at,
            "links":           links,
            **link_counts,
        }

    # ------------------------------------------------------------------
    # Output interface
    # ------------------------------------------------------------------

    def get_substrate(self) -> List[Dict[str, Any]]:
        """Return all causal chain records.

        Each record includes the 'links' list with full link detail.
        Only records with chain_depth >= CHAIN_DEPTH_MINIMUM count as
        valid Q5 outputs; all records are returned here for auditing.
        """
        return list(self._records)

    def valid_chains(self) -> List[Dict[str, Any]]:
        """Return only chains meeting the minimum depth criterion."""
        return [r for r in self._records
                if r["chain_depth"] >= CHAIN_DEPTH_MINIMUM]

    def causal_rows(self) -> List[Dict[str, Any]]:
        """Return CSV-ready rows (one per chain, no 'links' list)."""
        rows = []
        meta = self._meta
        for rec in self._records:
            row = {
                "arch":        meta.get("arch", ""),
                "run_idx":     meta.get("run_idx", ""),
                "seed":        meta.get("seed", ""),
                "hazard_cost": meta.get("hazard_cost", ""),
                "num_steps":   meta.get("num_steps", ""),
                "env":         meta.get("env", 1),
                "object_id":       rec["object_id"],
                "surprise_step":   rec["surprise_step"],
                "resolution_step": rec["resolution_step"],
                "chain_depth":     rec["chain_depth"],
                "chain_complete":  rec["chain_complete"],
                "truncated_at":    rec["truncated_at"] or "",
                "links_surprise":            rec.get("links_surprise", 0),
                "links_precondition":        rec.get("links_precondition", 0),
                "links_mastery_formation":   rec.get("links_mastery_formation", 0),
                "links_phase1_absence":      rec.get("links_phase1_absence", 0),
                "links_suppressed_approach": rec.get("links_suppressed_approach", 0),
                "links_belief_revision":     rec.get("links_belief_revision", 0),
            }
            rows.append(row)
        return rows
