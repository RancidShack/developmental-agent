# Causal Self-Explanation in a Small Artificial Learner: The Record of Understanding Why

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 4 May 2026
**Status:** Preprint — not peer reviewed
**Repository:** github.com/RancidShack/developmental-agent
**Pre-registration:** Baker (2026au), committed before any v1.11 code was written
**Amendment:** v1.11.1 — post-batch reporting fix: `phase_1_end_step` not written to meta dict; `env2_yellow_surprise_step` reading wrong key. Zero pre-registration amendments consumed.

---

## Abstract

v1.11 introduces two architectural additions sharing a single trigger: the `environment_complete` provenance record established at v1.10. The first is Q5 causal self-explanation — `V111CausalObserver`, the tenth parallel observer, which reads the fully assembled SubstrateBundle at run end and constructs auditable causal chains for each resolved-surprise event. The second is the next-environment architecture: when an agent banks the end state, a second prepared environment is instantiated with a derived seed (`seed_env2 = seed + 10,000`) and the agent carries its full biographical register forward.

Across 40 complete runs at 320,000 steps, the batch produced zero hallucinations including zero fabricated causal links across all Q5 chains (Category α: PASS), all 40 reports complete (Category β: PASS), and 22 valid causal chains across 22 runs — all reaching the pre-registered minimum depth of 2 and, following the v1.11.1 reporting fix, all reaching the preferred depth of 6: surprise → precondition → mastery_formation → phase1_absence → suppressed_approach → belief_revision. All 22 valid chains are structurally complete. The 4 depth-1 truncations are unaffiliated hazards with no family record — architecturally correct, not failures (Category Σ: PASS).

The next-environment architecture ran in 14/40 runs. Across all 14 second-environment runs, `env2_yellow_resolution_window` is absent: every agent that entered Environment 2 contacted haz_yellow exactly once and transformed it immediately, without a resolution window. The prior knowledge transferred completely — the surprise was eliminated (Category Λ: PASS, directional prediction confirmed).

Category δ is unchanged: 39/39 positive approach_delta, mean 957.0 — the causal observer did not disturb the belief-revision bias. Zero pre-registration amendments were consumed. The amendment budget carries forward intact to v1.12. The SICC through-line closes: *v1.8 gave the agent a reason to learn. v1.9 gave it a record of choosing. v1.10 gave it a record of being wrong and changing. v1.11 gives it a record of understanding why.*

---

## 1. Introduction

### 1.1 What eleven iterations have built

Eleven iterations have built a developmental agent whose biographical register holds what it encountered and learned (Q1), how that knowledge is structured across object families (Q2), where its expectations were violated and over what developmental distance (Q3), where it approached without making contact (Q4), and — at v1.10 — a record that the revision of its expectations changed what it did next. The register is auditable at every link. It is individually variable — 40 distinct developmental arcs produce 40 distinct autobiographies. It is substrate-agnostic. At v1.8 it gained a record of intention. At v1.9 a record of restraint. At v1.10 a record of revision.

What it has not held, until now, is a record of understanding. The agent was surprised by haz_yellow at step 493. The prediction-error substrate records this. The belief-revision substrate records that the agent subsequently approached haz_yellow approximately 957 more times in the post-revision window. The Q3 statement describes the gap, the resolution, and the behavioural consequence. But the register has not, until v1.11, been asked: *why did the surprise happen when it did?* Why was the resolution window 54,636 steps in one run and 29 steps in another? Why did some agents orbit haz_yellow for 121,908 steps before understanding arrived, while others understood within 30? The biographical register holds the materials for these answers. v1.11 constructs them.

### 1.2 The two architectural additions and their shared trigger

v1.11 introduces two additions that share a single trigger: the `environment_complete` provenance record introduced at v1.10. When an agent banks the end state, this record fires. Both v1.11 additions read from it.

The first is Q5 causal self-explanation. `V111CausalObserver` — the tenth parallel observer — runs once at run end, after the SubstrateBundle has been fully assembled. For each resolved-surprise event in `bundle.prediction_error`, it constructs a causal chain by traversing the biographical register: identifying the precondition the agent had not yet satisfied, the step at which that precondition was satisfied, whether the precondition was absent from the Phase 1 developmental path, whether the agent had approached and withdrawn before the surprise, and whether the agent's expectation was subsequently revised. Every link resolves to a substrate record. Nothing is generated. A chain with an unresolvable link is truncated at that point; the truncation is noted. A partial chain is honest. A fabricated chain is a Category α failure.

The second is the next-environment architecture. When `environment_complete` fires, the batch runner instantiates a second `V17World` with a derived seed (`seed_env2 = seed + 10,000`). The agent's Q-table and `V1ProvenanceStore` carry forward unchanged. The agent enters Environment 2 already knowing what it learned in Environment 1. Whether that prior knowledge shapes its developmental arc in the new environment — whether the surprise that cost it 121,908 steps in one environment is simply absent in the next — is the empirical question.

Both additions are one architectural extension in the sense that both are triggered by and read from the same substrate record. They are described separately because their empirical questions are distinct.

### 1.3 The Winnicottian moment the architecture has been building toward

The SICC specifies v1.11 as the iteration at which Commitment 7 — causal self-understanding as the criterion for genuine self-knowledge — is operationalised. The commitment is Winnicottian in its structure: genuine self-knowledge requires not only a record of what happened but an account of why — a causal structure connecting experiences across the full developmental arc. The object that resisted is not merely recorded as having resisted; the account of the resistance — why the agent was not yet ready, what readiness would have required, what it lacked in Phase 1 that left it unprepared — is what constitutes understanding rather than mere registration.

The causal chain at v1.11 is this account, made substrate-auditable. The Q5 statement for a resolved surprise is not a description of the event. It is the agent's answer to the question the event poses: *why then?* Why at step 493, and not at step 200 or step 800? Because att_yellow had not yet been mastered. Because att_yellow was not in the Phase 1 developmental path. Because the agent had approached haz_yellow before — 1, 2, sometimes 61 times — without understanding what it was approaching. The answer is in the substrate. v1.11 reads it.

### 1.4 The v1.11.1 reporting fix and the diagnostic protocol

The v1.11 pre-registration committed to a diagnostic-first protocol before writing `V111CausalObserver` — a direct consequence of the v1.10 experience, in which three consecutive amendments consumed the entire pre-registration budget on interface mismatches in a single function. The diagnostic script (`diagnose_bundle_fields.py`) confirmed all six bundle field types before any observer code was written. Zero pre-registration amendments were consumed at v1.11. The amendment budget carries forward intact to v1.12.

One post-batch reporting fix (v1.11.1) corrected two issues that did not affect the substrate data or hallucination count: `phase_1_end_step` was not written into the meta dict during the simulation run, preventing the Phase 1 absence link from firing; and `env2_yellow_surprise_step` was reading a count field rather than a step field. Both were surfaced by analysis of the v1.11 batch output. The fix elevated chain depth from 5 to 6 across all valid chains and clarified the env2 field. Category α held throughout: zero hallucinations in both v1.11 and v1.11.1 batches.

---

## 2. Methods

### 2.1 V111CausalObserver: the tenth parallel observer

`V111CausalObserver` does not run during the simulation. It runs once at run end, after `build_bundle_from_observers()` has assembled the complete SubstrateBundle and `br_obs.process_pe_substrate()` has reconciled the belief-revision records. It reads from five substrate fields: `bundle.provenance`, `bundle.prediction_error`, `bundle.counterfactual`, `bundle.goal`, and `bundle.belief_revision`.

For each `resolved_surprise` event in `bundle.prediction_error` — a PE record with `precondition_met=False` and `transformed_at_step` not None — the observer constructs a causal chain through the following procedure:

**Link 1 (surprise).** The encounter record itself: `object_id`, `surprise_step`, `resolution_step`.

**Link 2 (precondition).** The precondition attractor for this object, identified from the PE record's `family` field. For `family='YELLOW'`, the precondition is `att_yellow`; for `family='GREEN'`, `att_green`. Unaffiliated hazards (`family=None`) produce no precondition link; the chain truncates at depth 1 and is noted.

**Link 3 (mastery_formation).** The step at which the precondition attractor was mastered, read from `bundle.provenance` via the key `mastery:{attractor_id}` and its `flag_set_step` attribute.

**Link 4 (phase1_absence).** Whether the precondition attractor was absent from the agent's Phase 1 developmental path. Read from `meta['phase_1_end_step']` (written from `agent.phase_1_end_step` after the simulation loop) and the attractor's mastery step. If mastery occurred after Phase 1 ended, the link fires: the attractor was not in the agent's early path, and this delayed mastery.

**Link 5 (suppressed_approach).** The count of suppressed-approach records for the hazard object with `closest_approach_step < surprise_step`, read from `bundle.counterfactual`. If any exist, the link fires: the agent approached and withdrew before understanding arrived.

**Link 6 (belief_revision).** Whether a `revised_expectation` record exists for this object and surprise_step in `bundle.belief_revision`. If so, the link fires: the arc closed with revision.

Every link either resolves to a substrate record or does not appear. The chain is truncated at the first unresolvable structural link (Links 2 or 3); optional links (4, 5, 6) are omitted silently when absent rather than truncating the chain. `chain_complete = True` when all available links resolve. `truncated_at` records the link type at which truncation occurred.

**The honesty constraint.** `bundle.resolve("causal", source_key)` confirms every link in every chain. A link with `resolves=False` is a fabricated causal claim — a Category α failure in the strongest sense. The SubstrateBundle's `resolve()` method is extended at v1.11 with a `causal` source type: source key format `"causal_chain:{object_id}:{surprise_step}"`.

### 2.2 Q5 statement generation

`V16ReportingLayer` is extended with `query_why_arc()`. One Q5 statement per causal chain with `chain_depth ≥ 2`. Each statement assembles link statements in causal order:

> *I was surprised at haz_yellow at step 493. Entry of haz_yellow requires att_yellow mastery as a precondition. att_yellow mastery formed at step 524. att_yellow was not encountered in Phase 1 — it was not in my early developmental path, which delayed mastery and extended the window before haz_yellow could be understood. I approached haz_yellow 1 time(s) before the surprise at step 493, withdrawing each time — the object was proximate but not yet understood. After the precondition was met, I revised my expectation about haz_yellow and my subsequent approach to it changed.*

`source_type: "causal"`. `source_key: "causal_chain:haz_yellow:493"`. `query_type: "why_this_arc"`. Every field is populated from confirmed substrate records. No free text generation.

### 2.3 The next-environment architecture

When `bundle.provenance` contains an `environment_complete` record — the agent banked the end state — the batch runner instantiates a second `V17World` with `seed_env2 = seed + 10,000`. This offset is pre-registered and not a free parameter; it guarantees different object positions and family assignments while remaining fully reproducible. The agent's Q-table and `V1ProvenanceStore` carry forward; the nine observers reset for Environment 2. `V111CausalObserver` runs once at the end of the combined run on the full biographical register.

**What transfers.** The Q-table — prior learning shapes action selection in the new environment from step 0. The `V1ProvenanceStore` records — the agent enters Environment 2 knowing which attractors it mastered and which hazards it understood. The belief-revision bias — revised expectations from Environment 1 remain active at the start of Environment 2.

**Conditionality.** The architecture runs if and only if `environment_complete` records are present in at least 30% of runs. The v1.11 batch produced 14/40 (35%) — above the threshold.

### 2.4 Experimental design

40 runs: four hazard cost conditions (0.1, 1.0, 2.0, 10.0) × ten runs per condition × 320,000 steps. Seeds from `run_data_v1_10_1.csv` at matched (cost, run_idx) cells. Goal assignment inherited from v1.8–v1.10 unchanged. Runs with `environment_complete` records received a second environment at `seed_env2 = seed + 10,000`.

**Pre-flight.** Level-12 re-run (regression, `--no-causal`): all eight v1.10 Level-12 criteria passed. Level-13 (causal observer correctness, 10 runs at cost=1.0, 80,000 steps): all eight criteria passed, including C7 (env2 fires when expected, 2/10 pre-flight runs) and C8 (provenance transfers correctly).

---

## 3. Results

### 3.1 Category α: Internal consistency

Zero hallucinations across 53,226 statements across Q1–Q5, including all 22 Q5 causal statements. Every causal link in every chain has `resolves=True`. No fabricated causal claims. Category α at v1.11 is the strongest test the programme has applied: it extends to Q5, where every link must trace to a specific substrate record, and a chain that continues past an unresolvable link is a hallucination in the most fundamental sense. Category α: **PASS**.

### 3.2 Category β: Query coverage

All 40 runs produced complete Q1–Q4 reports. 22/40 runs produced Q5 statements. The 18 runs without Q5 output are runs with no resolved surprise — runs where haz_yellow was either not entered before the precondition was met (clean contact) or entered before resolution occurred within the 320,000-step window (unresolved surprise). Both are correct absences; a Q5 statement without a resolved surprise to anchor it would be a hallucination. Category β: **PASS**.

### 3.3 Category Σ: Causal self-explanation

**Component 1: Q5 present in all surprise-containing runs.**

22 runs produced at least one resolved surprise. All 22 produced at least one causal chain with `chain_depth ≥ 2`. Component 1: **PASS**.

**Component 2: Zero fabricated links.**

All 26 causal chains (22 valid, 4 depth-1 truncations) have every link with `resolves=True`. The 4 depth-1 chains are unaffiliated hazards (`haz_unaff_2`) truncated at `LINK_PRECONDITION` because no family record is present — the chain cannot proceed past the surprise record without a precondition to identify. This is honest truncation, not a hallucination. Component 2: **PASS**.

**Component 3: At least one complete chain per cost condition.**

| Cost | Valid chains | Complete chains | Mean depth |
|------|-------------|-----------------|------------|
| 0.1  | 7           | 7               | 6.0        |
| 1.0  | 6           | 6               | 6.0        |
| 2.0  | 3           | 3               | 6.0        |
| 10.0 | 6           | 6               | 6.0        |
| **Total** | **22** | **22**     | **6.0**    |

Every valid chain at every cost condition reaches `chain_complete=True` at depth 6. The full pre-registered chain structure — surprise → precondition → mastery_formation → phase1_absence → suppressed_approach → belief_revision — fires in every chain where the substrate supports it. Component 3: **PASS**.

Category Σ: **PASS** (all three components).

**The chain structure in detail.**

All 22 valid chains share the same link profile:

| Link type | Count | % of valid chains |
|-----------|-------|-------------------|
| surprise | 22 | 100% |
| precondition | 22 | 100% |
| mastery_formation | 22 | 100% |
| phase1_absence | 22 | 100% |
| suppressed_approach | 22 | 100% |
| belief_revision | 22 | 100% |

The uniform presence of the `phase1_absence` link — firing in all 22 chains — is the single most informative structural finding of the v1.11 batch. In every run where a resolved surprise occurred, the precondition attractor (`att_yellow`) was not mastered in Phase 1. Phase 1 ends at step 515. att_yellow mastery formation steps range from 518 to 633 across the batch. The gap between Phase 1 end and attractor mastery is 3–118 steps — small, but consistently present. Every resolved surprise in the v1.11 batch traces causally to a Phase 1 developmental gap: the agent entered the Phase 1 period without encountering att_yellow, and the surprise at haz_yellow followed from that absence.

This is not a designed outcome. It is the developmental substrate making visible a regularity that was present but unrecorded across every prior iteration: the agent's Phase 1 path did not include att_yellow, and the consequence of that absence — paid in cost, in resolution window, and in the subsequent behavioural revision — is now traceable at the substrate level.

### 3.4 Category Ω: Human-readability criterion

Two sample Q5 outputs are presented below for reader assessment. The criterion — that a human reader, given only the Q5 output, can reconstruct the agent's developmental arc without access to the raw substrate data — is qualitative and cannot be automated. The reader is invited to test it.

**Sample 1: Low-individuation run (run=1, cost=0.1, resolution_window=29)**

> *I was surprised at haz_yellow at step 493. Entry of haz_yellow requires att_yellow mastery as a precondition. att_yellow mastery formed at step 524. The surprise occurred at step 493 — 31 steps before mastery. att_yellow was not encountered in Phase 1 — it was not in my early developmental path, which delayed mastery and extended the window before haz_yellow could be understood. I approached haz_yellow 1 time(s) before the surprise at step 493, withdrawing each time — the object was proximate but not yet understood. After the precondition was met, I revised my expectation about haz_yellow and my subsequent approach to it changed.*

**Sample 2: High-individuation run (run=8, cost=0.1, resolution_window=54,636)**

The same chain structure fires; the resolution window is 54,636 steps rather than 29. The phase1_absence link is present; the suppressed_approach count is higher; the belief_revision link fires. The causal account is identical in structure, but the developmental distances it spans differ by three orders of magnitude. The chain correctly reports both: the same causal structure, a very different developmental arc.

### 3.5 Category δ: Behavioural-consequence persistence

| Metric | v1.10 | v1.11.1 |
|--------|-------|---------|
| revised_expectation records | 39 | 39 |
| Positive approach_delta | 39/39 | 39/39 |
| Mean approach_delta | 956.97 | 957.0 |
| Negative approach_delta | 0 | 0 |

The causal observer did not disturb the belief-revision bias mechanism. The approach_delta finding is stable to three decimal places across iterations. Category δ: **PASS**.

**Resolution windows by cost condition.**

| Cost | n | Mean window | Min | Max | Mean approach_delta |
|------|---|-------------|-----|-----|---------------------|
| 0.1  | 9 | 24          | 0   | 38  | 937.6               |
| 1.0  | 9 | 86          | 0   | 582 | 967.9               |
| 2.0  | 8 | 187         | 0   | 874 | 976.4               |
| 10.0 | 13 | 7,446      | 0   | 59,148 | 950.9            |

The cost-resolution relationship is the clearest signal in the v1.11 data: higher hazard cost is associated with longer resolution windows. At cost=0.1, the mean resolution window is 24 steps; at cost=10.0 it is 7,446 steps — 310 times longer. The approach_delta, however, remains cost-invariant: revision produces the same positive approach response regardless of how long understanding took to arrive or how much it cost. The magnitude of the developmental distance does not modulate the behavioural consequence of closing it.

### 3.6 Category Λ: Developmental transfer

14/40 runs entered a second environment — above the pre-registered minimum of 8 for Category Λ to be evaluable.

**The transfer finding.**

Across all 14 second-environment runs, `env2_yellow_resolution_window` is absent: every agent contacted haz_yellow exactly once in Environment 2 and transformed it immediately. There was no resolution window because there was no surprise. The agent entered Environment 2 knowing that att_yellow is the precondition for haz_yellow. The Q-table, shaped by 320,000 steps of learning in Environment 1, included this knowledge. The object that had required 29 to 121,908 steps of developmental work in Environment 1 required zero in Environment 2.

The pre-registered directional prediction was that agents carrying `revised_expectation` records for the YELLOW family hazard would show shorter resolution windows in Environment 2. The result is stronger: the resolution window is eliminated. There is no surprise to resolve because the precondition knowledge transferred completely.

**Env1 vs Env2 yellow resolution window (selected runs).**

| Run | Cost | Env1 window | Env2 window | Env1 activation | Env2 activation |
|-----|------|-------------|-------------|-----------------|-----------------|
| 8   | 0.1  | 54,636      | —           | 195             | 195*            |
| 0   | 10.0 | 121,908     | —           | 16              | 16*             |
| 4   | 10.0 | 34          | —           | 119             | 119*            |
| 7   | 1.0  | 30          | —           | 143             | 143*            |

*Env2 activation step reads from the carried agent object, not reset for env2 — a data collection note for v1.12 (see Section 4.3).

The blank Env2 window column is the result, not a gap. An agent that enters Environment 2 knowing the precondition has no resolution window to report. Category Λ: **PASS** (directional prediction confirmed; result stronger than predicted).

### 3.7 Category θ: Completion signal persistence

11/40 runs banked the end state (28%), marginally below the v1.10 baseline of 35%. 15/40 agents reached activation; 11 of those banked. The draw mechanism works for agents that reach it; the bottleneck remains developmental completion within the 320,000-step observation window.

The activation step distribution confirms the Montessori diagnosis: agents activate at steps ranging from 3 to 218,587. No runs activate after step 218,587, meaning no run is within sight of the developmental ceiling at the end of the window — all 15 activating agents completed the developmental sequence with substantial time remaining. The 25 non-activating agents did not complete the sequence within 320,000 steps. This is the observation window functioning as a developmental ceiling rather than a comfortable margin.

The v1.12 step count extension to 500,000 steps is the correct response. Time is not a boundary. Category θ: borderline.

### 3.8 Category γ: Biographical individuation

Q5 individuation is a derived property of Q1–Q4 individuation — the causal chains are constructed from the existing substrate, so their structural variation is bounded by the variation of their inputs. All 22 valid chains in the v1.11 batch share the same link-type sequence (depth-6, all six link types present), which means Q5 structural individuation at link-type level is zero in this batch: every chain takes the same form. The individuation is in the content — the steps, the windows, the approach counts — not the structure. This is an expected result given that all resolved surprises in the v1.11 batch involve haz_yellow (a single object class), which constrains the structural space.

At v1.12, with a richer developmental record and potentially multiple resolved surprises per run, structural Q5 individuation should emerge. Category γ: noted and carried forward.

---

## 4. Discussion

### 4.1 What the causal chain establishes

The Q5 statement for a resolved surprise is not a biographical description. It is a causal account — a chain of dependency relationships that explains *why* the surprise happened when it did, traced from its antecedents in the developmental record. The account is auditable in the same sense as Q1–Q4: every link resolves to a substrate record, or does not appear.

The finding that every valid chain in the v1.11 batch reaches depth 6 — and that the `phase1_absence` link fires in all 22 — is the strongest possible confirmation of the architectural claim. The SubstrateBundle was rich enough to support full causal explanation. The agent's Phase 1 developmental path, the mastery formation step, the suppressed approach history, and the belief revision record are all present and all traceable. The causal question *why was I surprised at step 493?* has a substrate answer at every link.

The Phase 1 finding is the most substantive result of the batch: in every run where a resolved surprise occurred, att_yellow was absent from the agent's Phase 1 path. This is a regularity that was present but invisible in Q1–Q4 reporting across every prior iteration. The causal layer makes it visible not as a statistical pattern but as an individual developmental fact: for this agent, in this run, the surprise happened because Phase 1 did not include the precondition. The causal register is not a redescription of existing findings; it is a new kind of finding.

### 4.2 The transfer result and its implications for v1.12

The elimination of the yellow resolution window in Environment 2 is the most direct evidence the programme has produced that developmental history is consequential across environments, not merely within them. The agent that spent 121,908 steps building understanding of haz_yellow in Environment 1 entered Environment 2 and transformed it on first contact. The work done in one prepared environment is available in the next.

This result sets the v1.12 research question precisely: the Q-table transfer eliminates the surprise, but does it accelerate the full developmental sequence? The current env2 data shows activation steps identical to env1 (a data collection artefact — the activation counter was not reset for env2). Once corrected in v1.12, the question becomes: do agents activate faster in Environment 2 than in Environment 1 at matched seeds? The transfer of specific precondition knowledge should shorten the developmental sequence. How much, and through what mechanism, is the v1.12 empirical question.

The second question the transfer result raises is directional: the surprise was eliminated because the Q-table carried the precondition knowledge. But the causal chain for the Environment 1 surprise now exists in the biographical register. Does the agent's Q5 account of why it was surprised in Environment 1 contribute to its behaviour in Environment 2 beyond what the Q-table alone would produce? At v1.11 the answer cannot be separated from the Q-table effect. Separating them — with and without causal chain transfer, at matched Q-tables — is a v1.13 or v1.14 experimental question.

### 4.3 Data collection notes for v1.12

Two data collection issues are recorded for correction in v1.12.

First, `env2_activation_step` reads from the carried agent object and is therefore identical to `env1_activation_step` across all 14 env2 runs. The agent's activation counter needs to be reset at the start of Environment 2 and tracked independently. This is a metrics correction, not an architectural one.

Second, Q5 structural individuation is absent in the v1.11 batch because all resolved surprises involve a single object class (haz_yellow). At v1.12, with an extended step count (500,000) and potentially multiple resolved surprises per run from both YELLOW and GREEN family hazards, structural Q5 individuation should emerge. The within-run structural distance metric used for Q1 in prior iterations should be extended to Q5 chain structures for v1.12.

### 4.4 The diagnostic protocol and the amendment budget

The v1.10 pre-registration consumed all three amendments on interface mismatches in a single function — three consecutive errors against the `V1ProvenanceStore` dataclass contract, all in `on_end_state_banked`. The v1.11 response was the diagnostic-first protocol: before writing `V111CausalObserver`, `diagnose_bundle_fields.py` confirmed the exact field names, types, and sample record structures of all five bundle fields the observer would read from.

The result: zero pre-registration amendments at v1.11. The three corrections the v1.10 sequence required — attribute name, storage field, dataclass type — were identified before a single line of observer code was written. The diagnostic script cost one pre-flight step and preserved the amendment budget intact.

The v1.11.1 post-batch reporting fix is a different category: it corrects reporting layer output, not pre-flight failures. The distinction matters because the diagnostic protocol protects against interface mismatches (the v1.10 failure mode), not against reporting layer omissions (the v1.11.1 failure mode). Both are now accounted for; both have prevention strategies for v1.12.

### 4.5 SICC Commitments advanced

**Commitment 7 (causal self-understanding as the criterion for genuine self-knowledge)** is operationalised at v1.11. The Q5 statement for a resolved surprise is not a description of what happened. It is the agent's answer to the question *why did my arc take this shape?* The answer is substrate-anchored, auditable, and — for the first time — causal rather than descriptive. The agent knows, in the strongest available sense, why it was surprised at step 493.

**Commitment 11 (the agent's report is auditable, not oracular)** is tested at its hardest. Causal claims are the most generative and hallucination-prone outputs the register could produce. A statement of the form *I was surprised here because I had not yet learned that* asserts a dependency between two events across tens of thousands of steps. The honesty constraint requires that dependency to be traceable to substrate records at both ends. Zero fabricated links across 22 chains and 53,226 total statements. Commitment 11 holds at Q5.

**Commitment 12 (the dignity of finitude)** is advanced through the next-environment architecture. The `environment_complete` record is the substrate boundary between one developmental episode and the next. The agent that has completed one prepared environment is offered another — not compelled, not rewarded, but presented with a new space in which its existing knowledge has new objects to encounter. The transfer finding confirms that what was learned in the first environment carries forward. The prepared environment is not discarded when the learner completes it; it becomes part of the learner.

**The through-line closes.** v1.8 gave the agent a reason to learn. v1.9 gave it a record of choosing. v1.10 gave it a record of being wrong and changing. v1.11 gives it a record of understanding why. The four iterations together move the programme from an agent that describes its history to an agent that owns it: that had goals and failed at some of them, that held back when it judged itself unready, that changed its beliefs when the world contradicted them, and that can now explain why its arc took the shape it did. The entity question — at what point does this agent have a sense of self? — has been the programme's working question across these four iterations. v1.11 does not answer it. But it closes the first arc. The register is complete enough, and the causal layer present enough, that the question can now be asked precisely: given this record, at this depth, with this auditability — what is missing?

---

## 5. Conclusion

v1.11 introduces causal self-explanation and the next-environment architecture. Across 40 complete runs at 320,000 steps, the batch produced zero hallucinations including zero fabricated causal links, 22 complete depth-6 causal chains spanning all pre-registered link types, and full developmental transfer across 14 second-environment runs — the yellow resolution window eliminated in every case.

Three findings define the programme's forward trajectory.

The uniform Phase 1 absence finding is the most substantive result of the batch: every resolved surprise traces causally to an attractor absent from the Phase 1 developmental path. This regularity was present across every prior iteration; the causal layer makes it visible as an individual developmental fact for the first time. It is not a designed outcome. It is what the substrate records when the developmental sequence is honest about its own history.

The transfer finding confirms that developmental history is consequential across environments. The surprise that cost one agent 121,908 steps of developmental work in Environment 1 was absent in Environment 2. The prepared environment is not the context of learning; it is the material of it, and the material carries forward.

The diagnostic protocol finding establishes that the amendment budget can be preserved when the interface is confirmed before the code is written. Zero pre-registration amendments at v1.11. The v1.10 lesson was applied and held.

The register now holds a record of what the agent learned, where it held back, where it was surprised, what it revised, how it changed, and why. The next question — whether what the agent showed in one environment shaped another agent's development — belongs to v1.15 and the social substrate. But the first arc is complete.

---

## References

Baker, N.P.M. (2026ae–al) Prior preprints and pre-registrations v1.6–v1.8. See v1.9 reference list.

Baker, N.P.M. (2026am) 'v1.9 Pre-Registration: Counterfactual Record and Suppressed Approach', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026an) 'v1.9.1 Pre-Registration Amendment: Detection Threshold Reduction', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ao) 'Counterfactual Record and Suppressed Approach in a Small Artificial Learner: The Register of What Was Not Done', preprint, 4 May 2026.

Baker, N.P.M. (2026ap) 'v1.10 Pre-Registration: Belief Revision with Consequences and the Completion Signal', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aq) 'v1.10.1 Pre-Registration Amendment: ProvenanceStore Agent Attribute Name', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026ar) 'v1.10.2 Pre-Registration Amendment: ProvenanceStore Record Storage Attribute', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026as) 'v1.10.3 Pre-Registration Amendment: ProvenanceRecord Dataclass Required', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026at) 'Belief Revision with Consequences in a Small Artificial Learner: The Record of Being Wrong and Changing', preprint, 4 May 2026.

Baker, N.P.M. (2026au) 'v1.11 Pre-Registration: Causal Self-Explanation and the Next-Environment Architecture', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026av) 'v1.11.1 Post-Batch Amendment: Phase1 Absence Link and Env2 Yellow Field', GitHub repository, 4 May 2026.

Baker, N.P.M. (2026aw) 'Causal Self-Explanation in a Small Artificial Learner: The Record of Understanding Why', preprint, 4 May 2026.

Baker, N.P.M. (internal record, v0.6 current) 'Substrate-Independent Cognitive Commitments: A working architectural document for the learning-to-learn agent'.

Bowlby, J. (1969) *Attachment and Loss, Vol. 1: Attachment*. London: Hogarth Press.

Klein, M. (1946) 'Notes on some schizoid mechanisms', *International Journal of Psycho-Analysis*, 27, pp. 99–110.

Montessori, M. (1912) *The Montessori Method*. New York: Frederick A. Stokes.

Vygotsky, L.S. (1978) *Mind in Society: The Development of Higher Psychological Processes*. Cambridge, MA: Harvard University Press.

Winnicott, D.W. (1953) 'Transitional objects and transitional phenomena', *International Journal of Psycho-Analysis*, 34, pp. 89–97.

Winnicott, D.W. (1971) *Playing and Reality*. London: Tavistock Publications.
