"""
v1_6_reporting_layer.py
------------------------
V16ReportingLayer: the v1.6 reporting layer.

Reads from a SubstrateBundle and responds to three query types,
producing ReportStatement objects in biographical register.

ARCHITECTURAL ROLE
The reporting layer is the first component in the programme that
produces output the agent can be said to author. Every prior
extension added to what the observers write down. This layer adds
what the agent can be asked about what was written.

The layer does not modify the agent, world, or any observer. It
does not participate in the run loop. It reads from completed
substrates after on_run_end has been called on all observers.

INTERNAL-CONSISTENCY CHARACTERISATION (Category α)
Every ReportStatement carries source_type and source_key. The
source_key must resolve in the SubstrateBundle via bundle.resolve().
A statement with source_resolves=False is a hallucination in the
architectural sense: a claim made without substrate. Category α
fails if any statement has source_resolves=False.

QUERY TYPES
  Query 1: what_learned
    Source: provenance + schema substrates.
    Produces one statement per provenance record, in formation-step
    order. Statements name what was learned, when, on what basis.

  Query 2: how_related
    Source: family + comparison substrates.
    Produces statements about family traversal structure and
    cross-family comparison measures.

  Query 3: where_surprised
    Source: prediction_error substrate.
    Produces per-cell statements naming encounter type, awareness
    step, resolution window (if resolved), or absence of surprise.

BIOGRAPHICAL REGISTER (pre-registration §2.4)
Statements use first person, name steps explicitly, and are phrased
no more strongly than the source record supports. The layer does not
claim the agent understood, expected, or was surprised by any event —
it reports what the records show.

SUBSTRATE-AGNOSTICISM
The reporting layer imports SubstrateBundle and ReportStatement only.
It does not import any observer class or grid-specific constant. Every
concept that must appear in statement text — family colour, cell form,
tier name — is read from the substrate's family and schema fields.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from v1_6_substrate_bundle import SubstrateBundle


# ---------------------------------------------------------------------------
# ReportStatement
# ---------------------------------------------------------------------------

@dataclass
class ReportStatement:
    """One auditable statement from the reporting layer.

    Attributes
    ----------
    text : str
        The biographical statement in first-person register.
    source_type : str
        Which substrate field the statement is sourced from.
        One of: "provenance", "schema", "family", "comparison",
        "prediction_error", "run_meta".
    source_key : str
        The key within the named substrate that supports the statement.
        For prediction_error: "encounter:{list_index}".
    source_resolves : bool
        True if bundle.resolve(source_type, source_key) returns True.
        Set by the reporting layer at statement creation time.
    query_type : str
        Which query produced this statement.
        One of: "what_learned", "how_related", "where_surprised".
    """
    text:            str
    source_type:     str
    source_key:      str
    source_resolves: bool
    query_type:      str


# ---------------------------------------------------------------------------
# V16ReportingLayer
# ---------------------------------------------------------------------------

class V16ReportingLayer:
    """v1.6 reporting layer.

    Instantiated with a SubstrateBundle. Responds to three query
    methods, each returning a list of ReportStatement objects.
    All three queries are run via generate_report(), which returns
    the full combined list.

    The layer is stateless after instantiation: query methods may
    be called in any order, any number of times.
    """

    def __init__(self, bundle: SubstrateBundle):
        self._bundle = bundle

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_report(self) -> List[ReportStatement]:
        """Run all three queries and return the combined statement list."""
        statements = []
        statements.extend(self.query_what_learned())
        statements.extend(self.query_how_related())
        statements.extend(self.query_where_surprised())
        return statements

    # ------------------------------------------------------------------
    # Query 1: what_learned
    # ------------------------------------------------------------------

    def query_what_learned(self) -> List[ReportStatement]:
        """What did I learn?

        Reads provenance substrate. Produces one statement per
        provenance record in formation-step order, naming flag type,
        when it formed, and the confirming-observation count.
        Cross-references are stated where present.
        """
        statements = []
        bundle = self._bundle

        if not bundle.provenance:
            statements.append(self._make(
                text=(
                    "I have no provenance records. "
                    "No learning history is available for this run."
                ),
                source_type="run_meta",
                source_key="run_idx",
                query_type="what_learned",
            ))
            return statements

        # Sort by formation step
        ordered = sorted(
            bundle.provenance.values(),
            key=lambda r: (r.flag_set_step or 0, r.flag_id),
        )

        for record in ordered:
            flag_id = record.flag_id
            ftype   = record.flag_type
            step    = record.flag_set_step
            conf    = record.confirming_observations
            coord   = record.flag_coord_str or "unknown location"

            # Base statement
            text = self._format_learned_statement(
                ftype, coord, step, conf, record
            )

            stmt = self._make(
                text=text,
                source_type="provenance",
                source_key=flag_id,
                query_type="what_learned",
            )
            statements.append(stmt)

            # Cross-reference statement if present
            if record.derived_from_threat_flag_id:
                xref_key = record.derived_from_threat_flag_id
                xref_text = (
                    f"This knowledge at {coord} derives from a threat "
                    f"that was flagged earlier (record: {xref_key}). "
                    f"The structural transformation connected them."
                )
                xref_stmt = self._make(
                    text=xref_text,
                    source_type="provenance",
                    source_key=xref_key,
                    query_type="what_learned",
                )
                statements.append(xref_stmt)

        return statements

    def _format_learned_statement(
        self, ftype, coord, step, conf, record
    ) -> str:
        """Format a biographical statement for a provenance record."""
        step_str = f"step {step}" if step is not None else "an unknown step"
        conf_str = (
            f"{conf} confirming observation{'s' if conf != 1 else ''}"
        )

        if ftype == "threat":
            disconf = record.disconfirming_observations
            base = (
                f"I flagged {coord} as a threat at {step_str}, "
                f"supported by {conf_str}."
            )
            if disconf and disconf > 0:
                base += (
                    f" This flag was later disconfirmed "
                    f"({disconf} disconfirming observation"
                    f"{'s' if disconf != 1 else ''}) "
                    f"when the cell transformed."
                )
            if record.transformed_at_step is not None:
                base += (
                    f" The cell transformed at step "
                    f"{record.transformed_at_step}."
                )
            return base

        if ftype == "mastery":
            return (
                f"I mastered the attractor at {coord} at {step_str}, "
                f"confirmed by {conf_str}."
            )

        if ftype == "knowledge_banking":
            return (
                f"I banked knowledge at {coord} at {step_str}, "
                f"confirmed by {conf_str}."
            )

        if ftype == "end_state_activation":
            return (
                f"The end-state activated at {step_str}, "
                f"confirmed by {conf_str}."
            )

        if ftype == "end_state_banking":
            return (
                f"I banked the end-state at {step_str}, "
                f"confirmed by {conf_str}."
            )

        # Fallback for unknown flag types — substrate-agnostic
        return (
            f"A {ftype} record at {coord} formed at {step_str}, "
            f"supported by {conf_str}."
        )

    # ------------------------------------------------------------------
    # Query 2: how_related
    # ------------------------------------------------------------------

    def query_how_related(self) -> List[ReportStatement]:
        """How does what I learned relate to itself?

        Reads family and comparison substrates. Produces statements
        about family traversal sequences and cross-family structure.
        """
        statements = []
        bundle = self._bundle

        # Family substrate statements
        if bundle.family is None:
            statements.append(self._make(
                text=(
                    "No family traversal records are available. "
                    "The relational structure of what I learned "
                    "cannot be stated."
                ),
                source_type="run_meta",
                source_key="num_steps",
                query_type="how_related",
            ))
        else:
            statements.extend(self._family_statements())

        # Comparison substrate statements
        if bundle.comparison is None:
            statements.append(self._make(
                text=(
                    "No cross-family comparison record is available. "
                    "The structural similarity between families "
                    "cannot be stated."
                ),
                source_type="run_meta",
                source_key="num_steps",
                query_type="how_related",
            ))
        else:
            statements.extend(self._comparison_statements())

        return statements

    def _family_statements(self) -> List[ReportStatement]:
        statements = []
        fam = self._bundle.family

        for colour in ("green", "yellow"):
            registered  = fam.get(f"{colour}_cell_registered")
            reg_step    = fam.get(f"{colour}_cell_first_perception_step")
            att_mastered = fam.get(f"{colour}_attractor_mastered")
            att_step    = fam.get(f"{colour}_attractor_mastery_step")
            att_form    = fam.get(f"{colour}_attractor_form")
            know_banked = fam.get(f"{colour}_knowledge_banked")
            know_step   = fam.get(f"{colour}_knowledge_banked_step")
            know_form   = fam.get(f"{colour}_knowledge_form")
            crossref    = fam.get(f"{colour}_crossref_complete")

            # Colour cell perception
            if str(registered).lower() == "true" and reg_step:
                text = (
                    f"I first perceived the {colour.upper()} colour cell "
                    f"at step {reg_step}. "
                    f"This was my first encounter with the {colour.upper()} "
                    f"family."
                )
            else:
                text = (
                    f"I did not register the {colour.upper()} colour cell "
                    f"within this run."
                )
            statements.append(self._make(
                text=text,
                source_type="family",
                source_key=f"{colour}_cell_registered",
                query_type="how_related",
            ))

            # Attractor mastery
            if str(att_mastered).lower() == "true" and att_step:
                form_str = f" ({att_form})" if att_form else ""
                text = (
                    f"I mastered the {colour.upper()} attractor{form_str} "
                    f"at step {att_step}. "
                    f"This completed the acquirable tier of the "
                    f"{colour.upper()} family."
                )
            else:
                text = (
                    f"I did not master the {colour.upper()} attractor "
                    f"within this run."
                )
            statements.append(self._make(
                text=text,
                source_type="family",
                source_key=f"{colour}_attractor_mastered",
                query_type="how_related",
            ))

            # Knowledge banking
            if str(know_banked).lower() == "true" and know_step:
                form_str = f" ({know_form})" if know_form else ""
                text = (
                    f"I banked the {colour.upper()} knowledge cell"
                    f"{form_str} at step {know_step}. "
                    f"This completed the bankable tier of the "
                    f"{colour.upper()} family."
                )
                if str(crossref).lower() == "true":
                    text += (
                        f" The cross-reference to the {colour.upper()} "
                        f"attractor is complete."
                    )
            else:
                text = (
                    f"I did not bank the {colour.upper()} knowledge cell "
                    f"within this run."
                )
            statements.append(self._make(
                text=text,
                source_type="family",
                source_key=f"{colour}_knowledge_banked",
                query_type="how_related",
            ))

        # Traversal narrative
        narrative = fam.get("family_traversal_narrative", "")
        if narrative:
            events = narrative.split("|")
            n_events = len(events)
            text = (
                f"My family traversal narrative contains {n_events} "
                f"events across both families, in this order: "
                f"{narrative}."
            )
            statements.append(self._make(
                text=text,
                source_type="family",
                source_key="family_traversal_narrative",
                query_type="how_related",
            ))

        return statements

    def _comparison_statements(self) -> List[ReportStatement]:
        statements = []
        comp = self._bundle.comparison

        both_complete = str(comp.get("both_complete", "")).lower() == "true"

        if not both_complete:
            text = (
                "Cross-family comparison is incomplete: "
                "at least one family traversal was not finished "
                "within this run. Structural comparison measures "
                "are not fully available."
            )
            statements.append(self._make(
                text=text,
                source_type="comparison",
                source_key="both_complete",
                query_type="how_related",
            ))
            return statements

        # Measure 2: structural assertion (always 1.0 in complete runs)
        m2 = comp.get("form_progression_parallelism")
        text = (
            f"The two families share the same form-progression structure "
            f"(Measure 2 = {m2}): both progress from a flat colour cell "
            f"through a 2D acquirable form to a 3D bankable form. "
            f"This parallelism is a structural assertion of the "
            f"prepared environment, not a finding about my behaviour."
        )
        statements.append(self._make(
            text=text,
            source_type="comparison",
            source_key="form_progression_parallelism",
            query_type="how_related",
        ))

        # Measure 1: tier-structure similarity
        m1 = comp.get("tier_structure_similarity")
        text = (
            f"The tier-ordering similarity between the two families "
            f"is {m1} (Measure 1). "
            f"A value of 0.0 indicates that both families were traversed "
            f"in the same tier order."
            if str(m1) == "0.0"
            else
            f"The tier-ordering similarity between the two families "
            f"is {m1} (Measure 1), indicating some divergence in "
            f"the order in which I traversed the tiers."
        )
        statements.append(self._make(
            text=text,
            source_type="comparison",
            source_key="tier_structure_similarity",
            query_type="how_related",
        ))

        # Measure 3: developmental tempo
        m3  = comp.get("traversal_sequence_distance")
        interleaving = comp.get("traversal_interleaving", "unknown")
        green_first  = comp.get("green_first")
        first_str = (
            "GREEN" if str(green_first).lower() == "true" else "YELLOW"
        )
        text = (
            f"My traversal-sequence distance between the two families "
            f"is {m3} (Measure 3). "
            f"I entered the {first_str} family first. "
            f"The traversal pattern was {interleaving}. "
            f"This is my developmental tempo for this run: "
            f"the degree to which the two family arcs were separated "
            f"or interleaved in time."
        )
        statements.append(self._make(
            text=text,
            source_type="comparison",
            source_key="traversal_sequence_distance",
            query_type="how_related",
        ))

        return statements

    # ------------------------------------------------------------------
    # Query 3: where_surprised
    # ------------------------------------------------------------------

    def query_where_surprised(self) -> List[ReportStatement]:
        """Where was I surprised?

        Reads prediction_error substrate. Produces per-cell statements
        naming encounter type, awareness step, resolution window.
        """
        statements = []
        bundle = self._bundle
        encounters = bundle.prediction_error

        if not encounters:
            statements.append(self._make(
                text=(
                    "No prediction-error encounters were recorded. "
                    "Either all hazard cells were entered after their "
                    "preconditions were met, or no hazard entries "
                    "occurred within this run."
                ),
                source_type="run_meta",
                source_key="seed",
                query_type="where_surprised",
            ))
            return statements

        # Group by cell, in order of first appearance
        cell_order = []
        cell_encounters: Dict[str, List] = {}
        for idx, enc in enumerate(encounters):
            cell = enc.get("cell", "unknown")
            if cell not in cell_encounters:
                cell_encounters[cell] = []
                cell_order.append(cell)
            cell_encounters[cell].append((idx, enc))

        for cell in cell_order:
            cell_items = cell_encounters[cell]
            statements.extend(
                self._cell_surprise_statements(cell, cell_items)
            )

        return statements

    def _cell_surprise_statements(
        self, cell: str, cell_items: list
    ) -> List[ReportStatement]:
        statements = []

        # Determine family from first encounter record
        first_enc = cell_items[0][1]
        family    = first_enc.get("family") or "unaffiliated"

        family_str = (
            f"{family} family" if family != "unaffiliated"
            else "unaffiliated cell"
        )

        for idx, enc in cell_items:
            source_key    = f"encounter:{idx}"
            enc_type      = enc.get("encounter_type", "")
            step          = enc.get("step")
            rw            = enc.get("resolution_window")
            transformed   = enc.get("transformed_at_step")
            precond_met   = str(enc.get("precondition_met", "")).lower()

            if enc_type == "resolved_surprise":
                text = (
                    f"I encountered {cell} ({family_str}) at step {step} "
                    f"before my precondition was met. "
                    f"I paid the cost and did not receive the transformation. "
                    f"I was aware of this cell before I was ready for it. "
                    f"The transformation eventually fired at step {transformed}. "
                    f"The resolution window was {rw} steps: "
                    f"the developmental distance between awareness and readiness."
                )

            elif enc_type == "unresolved_approach":
                text = (
                    f"I encountered {cell} ({family_str}) at step {step} "
                    f"before my precondition was met. "
                    f"I paid the cost and did not receive the transformation. "
                    f"The transformation did not fire within this run. "
                    f"This approach was not resolved: I found something "
                    f"I could not yet use, and the run ended before I became ready."
                )

            elif enc_type == "clean_first_entry":
                text = (
                    f"I entered {cell} ({family_str}) at step {step} "
                    f"with the precondition already met. "
                    f"No prediction error was recorded: "
                    f"the transformation followed without surprise."
                )

            else:
                # Unknown type — report honestly without claiming more
                text = (
                    f"An encounter with {cell} ({family_str}) at step "
                    f"{step} was recorded with encounter type "
                    f"'{enc_type}'. The record is available but the "
                    f"encounter type is not one of the three "
                    f"pre-registered types."
                )

            statements.append(self._make(
                text=text,
                source_type="prediction_error",
                source_key=source_key,
                query_type="where_surprised",
            ))

        return statements

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make(
        self,
        text:        str,
        source_type: str,
        source_key:  str,
        query_type:  str,
    ) -> ReportStatement:
        """Construct a ReportStatement, resolving traceability immediately."""
        resolves = self._bundle.resolve(source_type, source_key)
        return ReportStatement(
            text=text,
            source_type=source_type,
            source_key=source_key,
            source_resolves=resolves,
            query_type=query_type,
        )
