"""
v1_4_comparison_observer.py
----------------------------
v1.4 comparison observer. The fifth parallel observer in the programme's
observer stack, running alongside the v1.0 recorder, v1.1 provenance
store, v1.2 schema observer, and v1.3 family observer.

Responsibility: at run end, read the completed family traversal records
from the v1.3 family observer and compute three structural comparison
measures between the GREEN and YELLOW families.

Observer pattern:
  - on_pre_action(step)  — no-op. No live state is held.
  - on_post_event(step)  — no-op. No live state is held.
  - on_run_end(step)     — reads family observer's completed traversal
                           narrative and computes all three measures.
  - with --no-comparison, this observer is not instantiated; the batch
    runner produces byte-identical output to v1.3.2 baseline.

The three structural comparison measures (pre-registration §2.1):

  Measure 1 — tier_structure_similarity
    Normalised edit distance (Levenshtein) between the ordered sequences
    of event types (colour_registered, attractor_mastered, knowledge_banked)
    for each family within the run. 0 = identical sequence; 1 = maximum
    dissimilarity. For a run in which both families complete the full
    three-tier sequence in the same order, this value is 0.

  Measure 2 — form_progression_parallelism
    Proportion of three binary structural properties that hold across both
    families: (a) both perceivable-tier forms are FLAT, (b) both
    acquirable-tier forms are 2D, (c) both bankable-tier forms are 3D.
    This is 1.0 in all runs by architectural design (Category δ finding).
    Recorded as a structural assertion; its constancy is confirmed as
    part of Category β.

  Measure 3 — traversal_sequence_distance
    The Category γ metric from v1.3.1, applied cross-family:
      0.7 × normalised Levenshtein edit distance on full event tokens
      (step:event:family concatenated) +
      0.3 × normalised timestamp divergence between corresponding events.
    This is the primary quantitative finding. Distribution across 240 runs
    is the Category γ substrate.

Output fields (written to comparison_v1_4.csv):
  arch, hazard_cost, num_steps, run_idx, seed
  tier_structure_similarity
  form_progression_parallelism
  traversal_sequence_distance
  green_traversal_complete
  yellow_traversal_complete
  both_complete
  green_first
  traversal_interleaving
  cross_family_comparison_complete

Per-run summary fields (written to run_data_v1_4.csv):
  All fields above except arch/hazard_cost/num_steps/run_idx/seed
  (those are already in the run record).
"""

import csv

from curiosity_agent_v1_3_world import (
    GREEN, YELLOW,
    FAMILY_ATTRACTOR_COORDS,
    FLAT, SQUARE_2D, TRIANGLE_2D, SPHERE_3D, PYRAMID_3D,
)

# ---------------------------------------------------------------------------
# Output field definitions
# ---------------------------------------------------------------------------

COMPARISON_SUMMARY_FIELDS = [
    "tier_structure_similarity",
    "form_progression_parallelism",
    "traversal_sequence_distance",
    "green_traversal_complete",
    "yellow_traversal_complete",
    "both_complete",
    "green_first",
    "traversal_interleaving",
    "cross_family_comparison_complete",
]

COMPARISON_RECORD_FIELDS = [
    "arch", "hazard_cost", "num_steps", "run_idx", "seed",
] + COMPARISON_SUMMARY_FIELDS

# ---------------------------------------------------------------------------
# Levenshtein edit distance (pure Python, no external dependency)
# ---------------------------------------------------------------------------

def _levenshtein(seq_a, seq_b):
    """Compute Levenshtein edit distance between two sequences of tokens.

    Each element of seq_a / seq_b is treated as an atomic token.
    Returns integer edit distance.
    """
    len_a, len_b = len(seq_a), len(seq_b)
    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a

    # dp[i][j] = edit distance between seq_a[:i] and seq_b[:j]
    dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]
    for i in range(len_a + 1):
        dp[i][0] = i
    for j in range(len_b + 1):
        dp[0][j] = j

    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost # substitution
            )
    return dp[len_a][len_b]


def _normalised_levenshtein(seq_a, seq_b):
    """Normalised Levenshtein edit distance.

    Returns float in [0, 1]. 0 = identical; 1 = maximum dissimilarity.
    If both sequences are empty, returns 0.
    """
    max_len = max(len(seq_a), len(seq_b))
    if max_len == 0:
        return 0.0
    return _levenshtein(seq_a, seq_b) / max_len


# ---------------------------------------------------------------------------
# Traversal narrative parsing
# ---------------------------------------------------------------------------

def _parse_narrative(narrative):
    """Parse a family_traversal_narrative string into a list of event tuples.

    Input format: "step:event:family|step:event:family|..."
    Returns list of (step_int, event_str, family_str), sorted by step.
    Returns empty list for empty or None narrative.
    """
    if not narrative:
        return []
    events = []
    for token in narrative.split("|"):
        token = token.strip()
        if not token:
            continue
        parts = token.split(":")
        if len(parts) != 3:
            continue
        try:
            step = int(parts[0])
        except ValueError:
            continue
        events.append((step, parts[1], parts[2]))
    return sorted(events, key=lambda e: e[0])


def _events_for_family(parsed_events, family):
    """Filter parsed events to a single family.

    Returns list of (step, event_type) for the given family,
    in chronological order.
    """
    return [
        (step, event)
        for step, event, fam in parsed_events
        if fam == family
    ]


# ---------------------------------------------------------------------------
# Measure computations
# ---------------------------------------------------------------------------

TIER_EVENT_TYPES = ("colour_registered", "attractor_mastered", "knowledge_banked")

def _measure1_tier_structure_similarity(green_events, yellow_events):
    """Normalised edit distance between the two families' tier-event sequences.

    Operates on event-type tokens only (ignoring step timestamps).
    Returns float in [0, 1].
    """
    green_seq  = [e for _, e in green_events]
    yellow_seq = [e for _, e in yellow_events]
    return _normalised_levenshtein(green_seq, yellow_seq)


def _measure2_form_progression_parallelism():
    """Structural assertion: proportion of form-progression properties holding.

    Under the present architecture:
      (a) Both perceivable-tier forms are FLAT         — True by design
      (b) Both acquirable-tier forms are 2D            — True by design
          (SQUARE_2D for GREEN, TRIANGLE_2D for YELLOW)
      (c) Both bankable-tier forms are 3D              — True by design
          (SPHERE_3D for GREEN, PYRAMID_3D for YELLOW)

    All three properties hold in all runs. Returns 1.0.
    This is a Category δ structural assertion, not a variable finding.
    """
    prop_a = (FLAT == FLAT)                        # both perceivable = FLAT
    prop_b = (SQUARE_2D.endswith("2D")             # both acquirable = 2D
              and TRIANGLE_2D.endswith("2D"))
    prop_c = (SPHERE_3D.endswith("3D")             # both bankable = 3D
              and PYRAMID_3D.endswith("3D"))
    return sum([prop_a, prop_b, prop_c]) / 3.0


def _measure3_traversal_sequence_distance(green_events, yellow_events,
                                           num_steps):
    """Category γ metric applied cross-family within a run.

    0.7 × normalised Levenshtein on full event tokens (step:event) +
    0.3 × normalised timestamp divergence between corresponding events.

    Full event tokens include the step timestamp, so two agents that
    mastered green-then-yellow at different step intervals produce
    different token sequences even if the event order was identical.

    Timestamp divergence: mean absolute difference between corresponding
    event steps (matched by position), normalised by num_steps.
    For sequences of different length, the shorter is padded with
    num_steps (end-of-run sentinel) for divergence calculation.

    Returns float in [0, 1], or None if both sequences are empty.
    """
    if not green_events and not yellow_events:
        return None

    # Build full token sequences: "step:event"
    green_tokens  = [f"{s}:{e}" for s, e in green_events]
    yellow_tokens = [f"{s}:{e}" for s, e in yellow_events]

    # Component 1: normalised edit distance on full tokens
    edit_dist = _normalised_levenshtein(green_tokens, yellow_tokens)

    # Component 2: normalised timestamp divergence
    # Pad shorter sequence to equal length with num_steps sentinel
    g_steps = [s for s, _ in green_events]
    y_steps = [s for s, _ in yellow_events]
    max_len = max(len(g_steps), len(y_steps))
    g_padded = g_steps + [num_steps] * (max_len - len(g_steps))
    y_padded = y_steps + [num_steps] * (max_len - len(y_steps))

    if max_len == 0 or num_steps == 0:
        ts_divergence = 0.0
    else:
        mean_abs_diff = sum(
            abs(g - y) for g, y in zip(g_padded, y_padded)
        ) / max_len
        ts_divergence = min(mean_abs_diff / num_steps, 1.0)

    return round(0.7 * edit_dist + 0.3 * ts_divergence, 6)


# ---------------------------------------------------------------------------
# Traversal ordering and interleaving
# ---------------------------------------------------------------------------

def _traversal_ordering(green_events, yellow_events):
    """Determine green_first and traversal_interleaving.

    green_first: True if the GREEN acquirable tier was mastered before
    the YELLOW acquirable tier. None if neither or only one family has
    an attractor_mastered event.

    traversal_interleaving: one of:
      "green_then_yellow"  — all GREEN events complete before first YELLOW event
      "yellow_then_green"  — all YELLOW events complete before first GREEN event
      "interleaved"        — events from both families overlap temporally
      None                 — insufficient events to determine
    """
    green_mastery_steps = [s for s, e in green_events if e == "attractor_mastered"]
    yellow_mastery_steps = [s for s, e in yellow_events if e == "attractor_mastered"]

    if green_mastery_steps and yellow_mastery_steps:
        green_first = green_mastery_steps[0] < yellow_mastery_steps[0]
    elif green_mastery_steps:
        green_first = True
    elif yellow_mastery_steps:
        green_first = False
    else:
        green_first = None

    # Interleaving: compare step ranges
    if green_events and yellow_events:
        green_steps  = [s for s, _ in green_events]
        yellow_steps = [s for s, _ in yellow_events]
        green_min,  green_max  = min(green_steps),  max(green_steps)
        yellow_min, yellow_max = min(yellow_steps), max(yellow_steps)

        # No overlap: one family's events entirely precede the other's
        if green_max < yellow_min:
            interleaving = "green_then_yellow"
        elif yellow_max < green_min:
            interleaving = "yellow_then_green"
        else:
            interleaving = "interleaved"
    else:
        interleaving = None

    return green_first, interleaving


# ---------------------------------------------------------------------------
# V14ComparisonObserver
# ---------------------------------------------------------------------------

class V14ComparisonObserver:
    """Fifth parallel observer for v1.4 cross-family structural comparison.

    Instantiated once per run. Reads the family observer's completed
    traversal narrative at on_run_end; holds no live state during the run.

    The family observer must be passed in at instantiation so that
    on_run_end can call family_observer.summary_metrics() to retrieve
    the completed family_traversal_narrative.
    """

    def __init__(self, family_observer, run_metadata):
        self._family_obs = family_observer
        self._meta       = run_metadata
        self._row        = None   # populated at on_run_end

    # ------------------------------------------------------------------
    # Hook methods
    # ------------------------------------------------------------------

    def on_pre_action(self, step):
        """No-op. Comparison observer holds no live state."""
        pass

    def on_post_event(self, step):
        """No-op. Comparison observer holds no live state."""
        pass

    def on_run_end(self, step):
        """Compute all three structural comparison measures.

        Reads the family observer's completed family_traversal_narrative,
        parses it, and populates self._row with all comparison fields.
        """
        num_steps = self._meta.get("num_steps", step + 1)

        # Retrieve completed narrative from family observer.
        family_summary = self._family_obs.summary_metrics()
        narrative = family_summary.get("family_traversal_narrative", "")

        # Parse full narrative, then split by family.
        all_events = _parse_narrative(narrative)
        green_events  = _events_for_family(all_events, GREEN)
        yellow_events = _events_for_family(all_events, YELLOW)

        # Traversal completeness
        green_event_types  = {e for _, e in green_events}
        yellow_event_types = {e for _, e in yellow_events}
        full_set = set(TIER_EVENT_TYPES)

        green_complete  = full_set.issubset(green_event_types)
        yellow_complete = full_set.issubset(yellow_event_types)
        both_complete   = green_complete and yellow_complete

        # Measure 1: tier-structure similarity
        m1 = _measure1_tier_structure_similarity(green_events, yellow_events)

        # Measure 2: form-progression parallelism (structural assertion)
        m2 = _measure2_form_progression_parallelism()

        # Measure 3: traversal-sequence structural distance
        m3 = _measure3_traversal_sequence_distance(
            green_events, yellow_events, num_steps
        )

        # Traversal ordering and interleaving
        green_first, interleaving = _traversal_ordering(
            green_events, yellow_events
        )

        # Comparison is complete if both families are fully traversed
        # and Measure 3 is not None.
        comparison_complete = both_complete and (m3 is not None)

        self._row = {
            "arch":                          self._meta.get("arch", "v1_4"),
            "hazard_cost":                   self._meta.get("hazard_cost"),
            "num_steps":                     self._meta.get("num_steps"),
            "run_idx":                       self._meta.get("run_idx"),
            "seed":                          self._meta.get("seed"),
            "tier_structure_similarity":     m1,
            "form_progression_parallelism":  m2,
            "traversal_sequence_distance":   m3,
            "green_traversal_complete":      green_complete,
            "yellow_traversal_complete":     yellow_complete,
            "both_complete":                 both_complete,
            "green_first":                   green_first,
            "traversal_interleaving":        interleaving,
            "cross_family_comparison_complete": comparison_complete,
        }

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def summary_metrics(self):
        """Return per-run summary dict for inclusion in run_data_v1_4.csv.

        Returns the COMPARISON_SUMMARY_FIELDS subset of self._row.
        Must be called after on_run_end.
        """
        if self._row is None:
            return {f: None for f in COMPARISON_SUMMARY_FIELDS}
        return {f: self._row.get(f) for f in COMPARISON_SUMMARY_FIELDS}

    def write_comparison_csv(self, path, append=False):
        """Write full comparison record to comparison_v1_4.csv."""
        if self._row is None:
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
            writer = csv.DictWriter(f, fieldnames=COMPARISON_RECORD_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {k: self._row.get(k, "") for k in COMPARISON_RECORD_FIELDS}
            )

    def reset(self):
        """Reset mutable state. Called by batch runner between runs."""
        self._row = None
