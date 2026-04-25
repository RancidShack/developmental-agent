# Bounded Mastery Through Persistent Representation: Architectural Intervention at Multiple Code Paths in a Small Artificial Learner

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 25 April 2026
**Status:** Working draft — sections 1-4

---

## Abstract

A preceding paper (Baker, 2026d) demonstrated that experience-driven persistent threat representation resolves the long-horizon hazard-avoidance instability identified in v0.9. The architectural principle established was that categorical learned knowledge, stored persistently in a representational structure separate from the dynamics that govern preferences, can resist erosion by unbounded preference accumulation. The present paper tests whether the same principle applied to the mastery side — repeated attractor visits converting to depleted, banked categorical mastery — produces a bounded preference system that retains the developmental signatures the unbounded version produced.

The paper is structured around two parallel threads. The architectural thread reports the experimental result: across a pre-registered batch of 360 runs comparing v0.10 and v0.11.2 architectures across six cost levels and three run lengths with matched seeds, v0.11.2 produces Category A — full mastery trajectory — at 160,000 steps, with mean attractors mastered of 5.87 of 6 and Phase 3 cleanness of 58 of 60 (matching v0.10's behavioural preservation baseline). All three pre-registered Category F (individuation collapse) signals come back negative: 5 of 6 distinct first-banked attractors, dominant mastery sequence accounting for 10% of runs (well below the 40% threshold), and Pearson correlation between mastery rank and Manhattan distance from start of -0.076. The bounded mastery architecture preserves biographical individuation while producing the predicted systematic working-through-attractors developmental trajectory.

The methodological thread reports the implementation sequence required to achieve this result. The v0.11 architecture as originally pre-registered did not produce the predicted behaviour. A single-run probe revealed that suppressing feature reward and primitive attraction bias for mastered attractors, while leaving the cell preference accumulator unmodified, allowed pre-mastery preference deposits to dominate Phase 3 action selection. A first amendment (v0.11.1) reset preference at the banking step but preserved ongoing accumulation, which compounded across many post-mastery visits to reproduce the fixation pattern. A second amendment (v0.11.2) blocked preference accumulation entirely on mastered cells, producing the architectural intent of "no signal pulling back" through coordinated intervention at four distinct code paths. A diagnostic investigation, run before declaring the iteration's stopping rule activated, revealed that an apparent fixation in v0.11.2's single-run probe was a seed-specific outlier rather than representative of the architecture's typical behaviour. The full batch confirmed this. The substantive methodological finding is that achieving "no architectural mechanism reinforces returning" required intervention at four code paths simultaneously: feature reward depletion, primitive bias clearing, banking-time preference reset, and post-mastery accumulation blocking. The amendment sequence decomposes the abstract architectural goal into the specific implementation interventions it required.

The combined contribution is a bounded mastery architecture that resolves the unbounded-accumulation problem on the mastery side, parallel to v0.10's resolution on the hazard side. v0.10 and v0.11.2 together establish persistent categorical representation as the architectural response to unbounded accumulation across both valences of categorical experience.

---

## 1. Introduction

### 1.1 The architectural question opened by v0.9

A preceding paper (Baker, 2026c) identified an architectural instability in a small tabular developmental agent: when hazard avoidance was reduced to cost-based experience alone, the bounded learned knowledge produced by cost was overwhelmed by the unbounded preference accumulator that dominated Phase 3 action selection. The result was non-monotonic Phase 3 cleanness across run length, with avoidance partially learned at intermediate horizons but degrading at extended ones. The architectural interpretation offered was that cost-based learning produces distributed per-state-action Q-value adjustments bounded in their accumulated magnitude, while preference accumulates without bound across visits. In the absence of persistent representational structure for learned categorical knowledge, the preference accumulator wins at extended horizons.

A subsequent paper (Baker, 2026d) tested whether persistent threat representation resolved this for the hazard side. The result was Category A — full stabilisation — at 160,000 steps, with v0.10 producing 60 of 60 clean Phase 3 runs against v0.9's 48 of 60. The architectural principle the result demonstrated was that categorical learned knowledge stored in a representational structure separate from the Q-value system, and consulted as a hard gate before action selection, resists erosion by preference dynamics that overwhelm bounded distributed knowledge. The persistent representation does not compete with preferences on the same axis; it operates as a gate before the value computation occurs at all.

The present paper tests whether the same architectural principle generalises to the mastery side. The unbounded-accumulation problem v0.9 identified is not specific to hazards. Any form of categorical learning that the architecture acquires through experience could in principle face the same dynamic: the preference accumulator that dominates Phase 3 grows without bound across visits, and any bounded categorical knowledge stored only in distributed Q-values must compete with it on the same axis. The hazard-side test established that persistent representation resolves this for negative-valence categorical learning. The mastery-side test asks whether the same approach resolves it for positive-valence categorical learning.

### 1.2 The mastery-side architectural question

In the v0.8/v0.9/v0.10 architecture, attractor cells deliver feature reward on every visit indefinitely. This produces strong settling behaviour in Phase 3: the agent finds a rewarding cell and accumulates preference on it through repeated visits, with the unbounded accumulation producing the focused-autonomy and individuation findings of v0.8. But this same unbounded accumulation is structurally identical to the dynamic v0.9 identified as problematic on the hazard side. The architecture has no mechanism that converts repeated positive experience into categorical persistent mastery; the only signal of accumulated experience is the preference accumulator itself, which is graded and unbounded.

The architectural question is whether converting attractors from "always rewarding" to "rewarding until mastered, then banked categorically" produces a bounded preference system that retains the developmental signatures the unbounded version produced. The proposal is parallel to v0.10's threat layer: each attractor is visited some number of times, after which the cell is banked in a persistent mastery layer and ceases to deliver feature reward. The preference accumulator becomes bounded because mastered attractors no longer accumulate from feature signals, and the developmental trajectory shifts from "find and settle" to "systematically master and move on."

The pre-registered prediction (Baker, 2026e) was that v0.11 would produce a Phase 3 visit distribution shifted toward unmastered attractors when any remained, with mastery completion expected at extended run lengths. The secondary prediction was that v0.8 developmental signatures — concentration, attractor ratio, mastery accumulation, individuation, rule adherence — would be preserved under the new architecture. A particular concern named explicitly in the pre-registration was that the new mechanism could produce geographically-determined exploration trajectories in which all agents master attractors in the same order, collapsing individuation into a deterministic geometric pattern. The pre-registration committed to a three-signal Category F test that would measure whether this occurred.

### 1.3 The dual-thread structure of the present paper

This paper differs from its predecessors in being structured around two parallel threads.

The architectural thread reports the experimental finding. v0.11.2 — the architecture as implemented after two amendments — produces Category A, full mastery trajectory, at 160,000 steps. The bounded mastery architecture works as predicted on the central hypothesis. All v0.8 developmental signatures, including individuation, are preserved. The Category F test for individuation collapse comes back negative on all three signals. The architectural arc opened by v0.9 — bounded learning of any kind requires persistent categorical representation — is established for the mastery side as v0.10 established it for the hazard side.

The methodological thread reports the implementation sequence required to achieve this result. v0.11 as originally pre-registered did not produce the predicted behaviour. The architectural goal of "no architectural mechanism reinforces returning to a mastered cell" required coordinated intervention at four distinct code paths: feature reward depletion, primitive attraction bias clearing, banking-time preference reset, and post-mastery preference accumulation blocking. The pre-registered architecture addressed two of the four; subsequent amendments (v0.11.1 and v0.11.2) addressed the remaining two as implementation-time discoveries surfaced them. A diagnostic investigation, run before the iteration's stopping rule was activated, revealed that an apparent fixation in v0.11.2's single-run probe was a seed-specific outlier and that the full batch would confirm Category A.

The two threads are genuinely parallel rather than sequential. The architectural finding (Category A, individuation preserved) is independent of the methodological finding (bounded mastery requires four-path intervention) in the sense that either could in principle be reported without the other. But they emerged together: the methodological discipline of pre-registration before code, amendment before amended code, and diagnostic investigation before stopping rule activation is what produced the architecturally clean result. A v0.11 paper that reported only Category A would understate what the iteration actually demonstrated. A v0.11 paper that reported only the amendment sequence would foreground methodological self-examination at the expense of the architectural contribution. The dual-thread structure attempts to give both their proper weight.

### 1.4 Connection to the broader research programme

v0.10 and v0.11.2 together establish persistent categorical representation as the architectural response to the unbounded-accumulation problem v0.9 identified, across both valences of categorical experience. The research programme to date can be read as a sequence of single architectural changes each addressing a specific gap identified by its predecessor: v0.8 established the developmental signatures, v0.9 decomposed rule adherence and identified the unbounded-accumulation problem, v0.10 closed the gap on the hazard side, and v0.11 closes it on the mastery side. What remains for v1.0 is the integration paper that demonstrates the combined architecture passing the behavioural preservation audit across all prior findings.

The methodological discipline that has held throughout the programme — pre-registration before computation, single-variable change per iteration, behavioural preservation audit, honest reporting of findings as they occur — has, in this iteration, shown a property of itself worth naming. The amendment sequence demonstrates that single-variable change at the architectural level (one new mechanism: bounded mastery) can require multi-variable change at the implementation level (four code paths intervening simultaneously). The single-variable discipline is preserved when the architectural intent is held constant across amendments and the amendments are themselves committed before the amended code is written. This is not a weakening of the discipline but a more nuanced understanding of how architectural goals decompose into implementation interventions.

---

## 2. Methods

### 2.1 Environment and inheritance from v0.10

The environment is identical to that used in v0.8, v0.9, and v0.10 (Baker, 2026a, 2026c, 2026d). A 20×20 grid contains four cell types. Frame cells form the impassable boundary; hazard cells are passable at scalar cost; attractor cells are six fixed locations at which the agent receives feature reward on entry; neutral cells fill the remainder of the passable interior. The agent starts at coordinate (1, 1) and operates under the three-phase developmental schedule.

v0.11.2 inherits the v0.10 architecture unchanged on the hazard side. The threat layer with N=3 flag conversion threshold, hard-gate consultation before Q-value computation, frame pre-flagging, and persistent flag retention is operative throughout v0.11.2 in exactly the form Baker (2026d) reported. The drives, learning parameters, phase schedule, and Q-value reset multipliers are unchanged.

### 2.2 The v0.11 architectural intent

The v0.11 pre-registration (Baker, 2026e) specified a single architectural intent: bounded mastery through experience-driven depletion and persistent banking. After a pre-registered threshold of three visits to an attractor cell, the cell is banked in a persistent mastery layer, and from that moment forward the cell produces no architectural signal that pulls the agent back toward it. The cell remains visitable — the agent can still pass through it during exploration — but no architectural mechanism reinforces returning.

The architectural intent decomposes into four distinct code-path interventions, each corresponding to a specific signal the architecture can use to pull the agent toward a cell.

**Feature reward.** Attractor cells in v0.8/v0.9/v0.10 deliver a feature reward of 0.15 on every entry. For mastered cells, this signal must be zero, because continued reward on mastered cells would maintain the agent's drive to return to them.

**Primitive attraction bias.** Cells adjacent to attractor cells receive a primitive bias of +0.3 in the agent's perceptual machinery, applied during action selection in v0.8/v0.9/v0.10. For mastered cells, this bias must be cleared, because the agent's pre-wired orientation toward attractors should no longer apply once the attractor's developmental purpose is complete.

**Banking-time preference deposit.** Pre-mastery visits accumulate preference on the cell through the standard mechanism of preference accumulation from feature reward and learning progress. At the banking step itself, this accumulated mass plus the mastery bonus becomes a preference deposit that, multiplied by the Phase 3 preference weight of 0.8, produces a substantial action-selection signal pulling the agent back to the just-banked cell.

**Post-mastery preference accumulation.** On any visit to a mastered cell after banking, the standard preference accumulation continues to fire on learning-progress reward (feature reward is now zero, but learning-progress reward is generally non-zero across cells). Across many post-banking visits, this accumulation compounds into substantial preference mass on the mastered cell, again producing action-selection pull.

The architectural intent — no signal pulling back — requires intervention at all four of these code paths simultaneously. If any one is left unaddressed, the corresponding signal can dominate Phase 3 action selection and reproduce the fixation pattern the architecture is designed to prevent.

### 2.3 The v0.11 implementation sequence

The sequence of three implementations and two amendments is the methodological core of this paper. We describe each in turn.

**v0.11 (the original pre-registered implementation).** Addresses two of the four code paths: feature reward and primitive attraction bias. After three visits to an attractor, the cell is banked in the mastery layer; from that moment, feature reward returns zero and the primitive bias of +0.3 is no longer applied to adjacent cells.

A single-run probe at HAZARD_COST=1.0, MASTERY_THRESHOLD=3, MASTERY_BONUS=1.0, NUM_STEPS=20000 revealed the architecture did not produce the predicted behaviour. The mastered attractor at coordinate (16, 3) was visited 1000 times despite being banked early. Phase 3 visits to mastered attractors were 69; Phase 3 visits to unmastered ones were 0. The architecture's fixation pattern reproduced on a banked cell. Diagnostic inspection of the agent's preference accumulator revealed accumulated preference of approximately 1.45 units on the cell at the banking step (three pre-mastery feature rewards plus the mastery bonus), with continued growth from learning-progress accumulation across the 997 post-banking visits.

The architectural diagnosis was that addressing only feature reward and attraction bias is insufficient. The preference accumulator continues to operate on mastered cells and produces a fixation signal at the Phase 3 preference weight of 0.8 even when the other two signals are correctly zeroed. This was a finding the original pre-registration had not anticipated — the pre-registration treated the four code paths as a single architectural goal without decomposing them.

**v0.11.1 (first amendment).** Addresses three of the four code paths. The amendment specifies that at the banking step, the cell's accumulated preference is reset to zero. A v0.11.1 amendment document was committed to the public repository before any v0.11.1 code was written. The amendment addressed the third code path (banking-time preference deposit) but did not yet address the fourth.

A v0.11.1 single-run probe revealed substantially improved Phase 2 mastery dynamics: five attractors mastered by step 3,506, with a clean spread of mastery order across the environment. But Phase 3 reproduced the fixation pattern on a different mastered cell, with attractor (15, 16) visited 944 times after banking. The mechanism was identifiable: the banking-time reset zeroed preference on the cell at the moment of banking, but on every subsequent visit, ongoing preference accumulation from learning-progress reward continued to fire. Across 944 visits, even small per-visit accumulations compounded into substantial preference mass that, multiplied by the Phase 3 preference weight, reproduced the fixation pull.

**v0.11.2 (second amendment).** Addresses all four code paths. The amendment specifies that on cells whose mastery flag is set to 1, preference accumulation in update_model is blocked entirely. A v0.11.2 amendment document was committed to the public repository before any v0.11.2 code was written. The v0.11.2 amendment also named an explicit stopping rule: if v0.11.2 produced another implementation-time discovery requiring further architectural change, no v0.11.3 would follow; the v0.11 architectural goal would instead be re-examined at a more fundamental level.

A v0.11.2 single-run probe initially appeared to reproduce a fixation pattern at attractor (9, 10), with 888 post-banking visits. The interpretation of this result is addressed in Section 2.4 below.

### 2.4 The diagnostic investigation

The v0.11.2 single-run probe appeared to invoke the iteration's stopping rule. Before invoking it, a diagnostic version of the v0.11.2 architecture was implemented and run to characterise the fixation mechanism. The architecture in the diagnostic version was unchanged from v0.11.2; only the reporting was extended to dump preference values for cells in the neighbourhood of mastered attractors and Q-values for state-action pairs targeting mastered cells, allowing distinction between three hypotheses: H1 (fixation driven by preference accumulation on cells adjacent to mastered attractors), H2 (fixation driven by Q-values around mastered cells from MASTERY_BONUS propagation through TD learning), or H3 (combination of H1 and H2 or unidentified mechanism).

The diagnostic run produced a substantially different result from the original v0.11.2 probe: 6 of 6 attractors mastered, with modest post-banking visit counts. The earlier interpretation that v0.11.2 produced fixation patterns was therefore based on a single-seed outlier rather than on the architecture's typical behaviour. Both H1 and H2 ratios in the diagnostic data were consistent with no elevated signal on neighbour preferences or approach-path Q-values.

This finding — that single-run probes can produce seed-specific outliers misleadingly suggestive of architectural failure — is itself methodologically informative. The discipline of running the full pre-registered batch before invoking stopping rules is what produced the corrected interpretation. The single-run probes during the implementation sequence were useful for detecting clear architectural problems (the v0.11 and v0.11.1 probes correctly identified the fixation mechanism each implementation produced), but a single probe is insufficient to distinguish a representative failure from a seed-specific outlier. The batch is the appropriate evidence base for that determination.

The full batch was run subsequently and confirmed the diagnostic finding: v0.11.2 produces Category A across the 160,000-step matrix. The methodological learning is that a single-run probe is sufficient to identify architectural mechanisms but insufficient to settle whether an apparent failure is the architecture's typical behaviour. The implementation sequence depended on single-run probes for diagnostic speed, but the architectural interpretation properly required the full batch.

### 2.5 v0.11.2 architectural specification (final)

For clarity, we state the v0.11.2 architecture as run in the batch in full.

**Inherited from v0.10 unchanged.** Three-phase schedule, drive composition, learning parameters, threat layer, hazard handling, frame handling, environment layout, Phase 1 prescribed traversal.

**Mastery counter.** A dictionary `attractor_visit_counter` indexed by cell coordinates, initialised to zero for all attractor cells. Increments by 1 on every entry to an attractor cell, regardless of phase.

**Mastery flag.** A dictionary `mastery_flag` indexed by cell coordinates, with binary values. Initialised to 0 for all attractor cells; not present for non-attractor cells. Set to 1 when the visit counter reaches MASTERY_THRESHOLD = 3. One-way; does not clear.

**Mastery bonus.** A pre-registered scalar value of 1.0 delivered to the intrinsic reward stream at the banking step (the third visit to an attractor cell), replacing the standard feature reward of 0.15 for that visit. Subsequent visits return zero feature reward. The bonus flows through Q-value updates via the standard TD learning mechanism but is not deposited into preference (see below).

**Feature reward modification.** Attractor cells with visit counter < 3 produce the standard feature reward of 0.15 on entry. The cell whose counter reaches exactly 3 (the banking visit) produces MASTERY_BONUS = 1.0 instead. Cells with counter > 3 (post-banking visits) produce zero feature reward.

**Primitive attraction bias modification.** The +0.3 attraction bonus on action selection toward adjacent attractor cells applies only to unmastered attractors. For cells with mastery_flag = 1, the bonus is not applied.

**Preference accumulation block.** In `update_model`, the standard preference accumulation `cell_preference[cell] += r_progress + r_feature` is wrapped in a conditional that fires only when `mastery_flag.get(cell, 0) == 0`. For mastered cells, no preference accumulation occurs.

**Banking-time preference reset.** A redundant safeguard. After the standard preference accumulation block, if the cell has just been banked (mastery_flag = 1 AND counter = MASTERY_THRESHOLD exactly), preference is set to zero. Under the v0.11.2 accumulation block this is operationally redundant — the block prevents the increment that the reset would zero — but it is retained for architectural clarity and as a safeguard against future modifications that might inadvertently bypass the accumulation block.

The four code-path interventions thus operate together: feature reward returns zero on mastered cells (path 1); primitive attraction bias does not apply (path 2); banking-time deposit is prevented by accumulation block (path 3); ongoing accumulation is blocked (path 4). The mastered cell becomes inert with respect to all preference and feature signals.

### 2.6 Experimental matrix and matched-seed comparison

The experimental matrix is two architectures crossed with six cost levels crossed with three run lengths crossed with ten runs per cell, totalling 360 runs. The architectures are v0.10 (as published in Baker, 2026d) and v0.11.2 (the implementation specified in Section 2.5 above). Cost levels are 0.1, 0.5, 1.0, 2.0, 5.0, 10.0. Run lengths are 20,000, 80,000, and 160,000 steps. Matched seeds across architectures ensure within-seed comparison up to the point at which the mastery layer first intervenes in v0.11.2.

The v0.10 architecture is reimplemented within the batch runner as a class parameterised by hazard cost, matching the approach used in v0.10's batch (Baker, 2026d). This allows the batch to vary cost without requiring file modifications between cells.

### 2.7 Metrics

All metrics from v0.8, v0.9, and v0.10 are retained. Additional metrics specific to v0.11 are listed below.

**Attractors mastered per run.** Count of attractor cells with mastery_flag = 1 at end of run. Primary measure for v0.11's central hypothesis.

**Time to first mastery.** Step at which the first attractor was banked.

**Time to final mastery.** Step at which the most recently banked attractor was set.

**First-banked attractor.** The coordinates of the attractor banked first in each run. Used in the Category F analysis to test individuation in mastery initiation.

**Mastery sequence.** The full ordered sequence of attractor coordinates in the order banked. Used in the Category F analysis to test individuation in mastery progression.

**Post-mastery visits total.** Sum across all mastered attractors of visits beyond the mastery threshold (i.e., ongoing visits to banked cells). Used to assess whether bounded mastery produces bounded post-banking activity.

**Phase 3 visits to mastered/unmastered split.** Count of Phase 3 visits to attractor cells whose mastery_flag is 1 vs 0 at end of run. Used to test whether the predicted developmental shift toward unmastered targets occurs.

### 2.8 Pre-registered interpretation categories

Six interpretation categories were pre-registered before the batch was run.

Category A — full mastery trajectory: mean attractors mastered ≥ 5.0 at 160,000 steps. Category B — partial mastery: 3.0 to 4.9. Category C — weak mastery: < 3.0. Category D — over-mastery: full 6/6 mastery at 20,000 steps across most runs (architecture too aggressive). Category E — developmental degradation: secondary signatures from v0.8 substantially reduced. Category F — individuation collapse: high mastery but order of mastery convergent across runs.

Category F is operationalised by three pre-registered signals at the 160,000-step run length. Signal 1: distinct first-banked attractors fewer than 4 of 6 across the batch. Signal 2: the dominant mastery sequence accounting for more than 40% of runs. Signal 3: Pearson correlation between mastery rank and Manhattan distance from start cell exceeding 0.7. Two of three signals trigger Category F classification.

The pre-registration document, the v0.11.1 amendment, and the v0.11.2 amendment are each committed to the public repository at github.com/RancidShack/developmental-agent and timestamped before the corresponding code was written.

---

## 3. Architectural results

### 3.1 Headline finding: Category A — full mastery trajectory

At 160,000 steps, v0.11.2 produced a mean of 5.87 attractors mastered per run across 60 runs (six cost levels times ten runs). The pre-registered Category A threshold of 5.0 is exceeded by a substantial margin. The distribution at 160,000 steps shows 53 of 60 runs mastering all six attractors, 6 of 60 mastering five, and 1 of 60 mastering four. No run mastered fewer than four.

The pattern across run lengths shows the architecture's mastery dynamics scaling with time. At 20,000 steps the mean attractors mastered was 4.62 of 6; at 80,000 steps, 5.47 of 6; at 160,000 steps, 5.87 of 6. Mastery completion improves monotonically with run length, consistent with the per-cell-no-generalisation property of the architecture: each attractor requires three visits before banking, and longer runs allow more attractors to receive their three visits each.

**Table 1. Distribution of attractors mastered per run, by run length, across all 60 v0.11.2 runs at each run length.**

| Attractors mastered | 20,000 steps | 80,000 steps | 160,000 steps |
|---|---|---|---|
| 1 of 6 | 1 run | 0 runs | 0 runs |
| 2 of 6 | 3 runs | 1 run | 0 runs |
| 3 of 6 | 8 runs | 2 runs | 0 runs |
| 4 of 6 | 7 runs | 4 runs | 1 run |
| 5 of 6 | 28 runs | 14 runs | 6 runs |
| 6 of 6 | 13 runs | 39 runs | 53 runs |

### 3.2 Phase 3 dynamics: predicted trajectory observed

The pre-registered prediction was that v0.11.2 agents would shift Phase 3 visits toward unmastered attractors when any remained, with Phase 3 visits to mastered attractors becoming "passable terrain" rather than fixation targets.

The data shows the predicted shift unambiguously. Mean Phase 3 visits to unmastered attractors across the batch at 160,000 steps was 0.0 — but this is because nearly all agents had already mastered all six attractors before Phase 3 began. The substantive measure is the distribution of Phase 3 visits to mastered attractors: a mean of 436.7 across the batch at 160,000 steps, distributed across mastered cells rather than concentrated on any single cell. This is the architecture's "settled biographical state" expressed differently from v0.8's settled-on-one-attractor pattern. Agents pass through mastered cells during Phase 3 exploration without fixating on any particular one.

The mean post-mastery visit total per run (sum across all mastered attractors of visits beyond banking) at 160,000 steps was 4399. This is the architecture-level signature of the bounded-mastery developmental trajectory: agents continue to move through mastered cells substantially in Phase 3, but the visits are distributed across multiple cells rather than concentrating fixation on any single one.

### 3.3 Time-to-mastery dynamics

The temporal profile of mastery acquisition is informative about the architecture's developmental trajectory.

**Table 2. Time-to-mastery summary across run lengths in v0.11.2.**

| Run length | Mean time to first mastery | Mean time to final mastery | Mean attractors mastered |
|---|---|---|---|
| 20,000 | 514 (min 338, max 1,590) | 8,333 (min 638, max 19,783) | 4.62 of 6 |
| 80,000 | 786 (min 338, max 5,285) | 23,599 (min 1,764, max 54,846) | 5.47 of 6 |
| 160,000 | 652 (min 338, max 2,228) | 36,839 (min 3,860, max 107,083) | 5.87 of 6 |

The first attractor is mastered very early in all run lengths — typically within a few hundred to a few thousand steps. The final attractor is mastered substantially later, with substantial variance across runs. At 160,000 steps the maximum time to final mastery is 107,083, indicating that some agents discover and master attractors very late in their developmental trajectory.

The temporal profile demonstrates that mastery acquisition is not instantaneous but scales with available developmental time. Mean time to final mastery grows from 8,333 steps at the 20,000-step run length to 23,599 at 80,000 steps to 36,839 at 160,000 steps, with individual runs reaching as late as 107,083 steps for their final attractor. This is the architectural signature of bounded mastery: the trajectory does not rush to complete the full attractor set but lets mastery emerge at the rate the agent's specific exploration trajectory permits. The architecture takes time. Given more time, it produces more complete mastery; the relationship is not linear but is monotonic across the tested range.

The pattern is consistent with the architectural design: the agent encounters and masters attractors at the rate its specific exploration trajectory permits, with no architectural mechanism enforcing rapid completion of the full set. This produces the variation in time-to-final-mastery across runs that the per-cell-no-generalisation design choice predicts.

### 3.4 Behavioural preservation: rule adherence retained

The v0.10 threat-layer mechanism for hazard avoidance is inherited unchanged in v0.11.2. The behavioural preservation question is whether the addition of the mastery layer disrupts hazard avoidance or other v0.8 signatures.

At 160,000 steps, v0.11.2 produced Phase 3 cleanness of 58 of 60 runs. v0.10 at the same condition produced 60 of 60 (Baker, 2026d). The two-run difference is within the noise envelope of the matched-seed comparison and does not represent a meaningful degradation of hazard avoidance. The rule adherence finding established by v0.10 holds under v0.11.2 within measurement resolution.

Other v0.8 developmental signatures are also preserved. Mean state-action pairs mastered at 160,000 steps in v0.11.2 was 437.8, comparable to v0.10's range. Phase 3 attractor visit ratios and concentration values were within the v0.8/v0.9/v0.10 ranges. The pre-registered Category E (developmental degradation) is firmly not triggered.

---

## 4. Category F results: individuation under bounded mastery

The Category F test was the most architecturally substantive question the pre-registration committed to. v0.11.2's central mechanism deliberately changes the developmental trajectory from "find and settle" to "systematically master and move on," and the concern was that this change could collapse individuation into a deterministic geometric pattern in which all agents master attractors in the same order. The pre-registered three-signal test addressed this question rigorously.

### 4.1 Signal 1 — first-banked attractor distribution

At 160,000 steps, the distribution of first-banked attractors across 60 runs in v0.11.2 was:

- (4, 15): 47 runs
- (9, 10): 7 runs
- (15, 16): 3 runs
- (3, 3): 2 runs
- (11, 5): 1 run
- (16, 3): 0 runs

Five of six attractors appear as first-banked across the batch, with one attractor (4, 15) accounting for the majority of first-banked positions. The pre-registered Category F threshold of fewer than 4 of 6 distinct first-banked attractors is not triggered (5 of 6 distinct).

The dominance of (4, 15) reflects the geographic structure of the environment. The agent starts at (1, 1); the attractor at (4, 15) is reachable via Phase 2 trajectory paths that the drive-based exploration tends to produce early in Phase 2, given the prescribed Phase 1 traversal pattern that ends with the agent in proximity to that region. The Manhattan distance from start to (4, 15) is 17, comparable to other attractor distances, but the trajectory pattern that emerges from drive-based action selection in the early Phase 2 frequently leads to (4, 15) before other attractors. This is environmental geometry interacting with stochastic exploration, not a deterministic pattern.

### 4.2 Signal 2 — mastery sequence dominance

The mastery sequence (the ordered sequence of attractor coordinates in the order banked) was extracted from each run. Across the 60 v0.11.2 runs at 160,000 steps, the most common mastery sequence accounted for 6 of 60 runs (10.0% of the batch). The pre-registered Category F threshold of more than 40% is not triggered.

The data shows 42 distinct mastery sequences across 60 runs. Seventy percent of sequences appeared in only one run; the most common sequence appeared in only six. The mastery trajectory is genuinely individuated: different agents master attractors in different orders, with the variation reflecting biographical differences arising from stochastic exploration rather than deterministic architectural constraints.

### 4.3 Signal 3 — mastery rank vs distance from start correlation

The Pearson correlation between mastery rank (1 = first banked, 2 = second banked, etc.) and Manhattan distance from the start cell (1, 1) was computed across all banked attractors pooled across 60 runs at 160,000 steps. The result was -0.076.

The pre-registered Category F threshold of correlation > 0.7 is firmly not triggered. The correlation is essentially zero, indicating no relationship between mastery order and geographic distance from start. Agents do not master nearer attractors first and farther ones later in any systematic way; the mastery order is genuinely independent of environmental geometry at the pooled level.

This is the most architecturally substantive of the three Category F findings. It directly tests whether the bounded-mastery architecture produces geographically-determined exploration patterns. The data shows it does not. The mastery sequence in v0.11.2 is shaped by the agent's specific stochastic trajectory rather than by environmental layout.

### 4.4 Category F assessment

Zero of three Category F signals are triggered. Category F is firmly not triggered. The bounded-mastery architecture preserves individuation: different agents master attractors in genuinely different orders, with variation arising from biographical trajectory rather than from environmental geometry.

The substantive architectural finding is that bounding the preference signal does not require accepting a loss of individuation. The v0.8 individuation finding was originally produced by unbounded preference accumulation amplifying stochastic trajectory differences. The concern was that bounding the accumulation might remove the amplification mechanism and collapse individuation into deterministic patterns. The data shows that the amplification mechanism is not the only source of individuation in this architecture: stochastic exploration shapes Phase 2 trajectories, and the trajectories themselves produce individuated mastery orderings independent of post-mastery preference dynamics. Individuation in v0.11.2 originates earlier in the developmental sequence than v0.8's mechanism predicted — at the level of which attractors are reached when, rather than which attractor becomes the settled focus.

This is a finding the pre-registration did not predict but that the data clearly supports. Bounded mastery preserves individuation through a different mechanism than unbounded accumulation produces it. The architecture's biographical signature is robust across the change in how mastery is stored.

### 4.5 End-state preference convergence: a different category of finding

One result merits explicit honest reporting alongside the Category F findings, but framed correctly. While the mastery sequence individuation is preserved across all three pre-registered Category F signals, the *end-of-life top-preferred cell* converges across the batch as run length increases. At 20,000 steps, the top-preferred cell distribution shows 4 of 6 distinct attractors. At 80,000 steps, this collapses to 2 of 6, with one attractor accounting for 59 of 60 runs. At 160,000 steps, all 60 of 60 runs have the same top-preferred cell.

It would be misleading to compare this directly against v0.10's top-preferred cell distribution and conclude v0.11.2 produces less individuation. The two architectures are not measuring the same thing at end of life.

In v0.10, attractors continue to deliver feature reward indefinitely. The agent can always be drawn back to an attractor cell by its continuing pull, and end-of-life top preference reflects which attractor's biographical competition the agent's developmental trajectory selected. Individuation in v0.10's top-preferred cell is biographical settling among real attractors that retain their attractive force throughout the agent's life.

In v0.11.2, all attractors have been mastered by the end of run length 160,000 in the substantial majority of runs. Mastered attractors produce zero feature reward, no primitive attraction bias, and no preference accumulation. They produce no architectural signal pulling the agent toward them. The end-of-life top-preferred cell is therefore not "the attractor I settled on" — it is "the cell I happened to traverse most during post-mastery exploration." With no attractor pull active at end of life, the only signal shaping post-mastery preference is which neutral cells get traversed most frequently, which is shaped by the geometry of the environment, the threat layer's gating of certain regions, and the agent's habits of post-mastery exploration.

The convergence is therefore the expected architectural signature of an end-state in which no pulling signal remains. Different agents traverse similar exploration paths in the absence of attractor pull because the underlying environmental geometry is the same. The end-state of v0.11.2 is "what an agent does when there is nothing left to attract it" — and the answer is that agents do similar things, because the structural features that shape exploration in the absence of pull (frame avoidance, threat gating, neutral cell connectivity) are common across runs.

This is not a loss of individuation in any sense parallel to what v0.10 demonstrates. Individuation in v0.11.2 is expressed at the mastery-trajectory level (which attractors get banked when, in what order) rather than at the end-state-settling level (which cell becomes the favourite). The two architectures express biographical individuation through different mechanisms appropriate to their respective structures.

The substantive question the convergence raises is whether bounded mastery should also produce individuated end-state settling. In the current architecture there is no mechanism that activates after mastery completion to give the agent a developmental target beyond the bounded mastery trajectory itself. A bounded-mastery learner that has completed its exploration of available attractors continues to explore neutral terrain because it has nothing else available — but if the architecture provided a "next phase" target that became active after mastery completion, agents might settle on that target in biographically individuated ways. The v0.10 architecture provides this implicitly through unbounded attractor pull; the v0.11.2 architecture does not provide it at all.

This is a genuinely open architectural question that the v0.11.2 findings open. Whether the bounded-mastery architecture can produce individuated end-state settling by introducing a mechanism that activates after mastery completion — analogous to the way a child's developmental progression provides "next stage" targets after each prior stage is mastered — is a question reserved for subsequent work and discussed further in Section 6.4.

The architectural finding to record from this section is precise: bounded mastery preserves individuation in the dimensions where individuation has architectural correlates (mastery sequence, first-banked distribution, geographic-distance independence). Where the architecture provides no end-state target, agents converge on similar post-mastery exploration patterns because the underlying environmental geometry is shared. This is the predicted signature of "no pulling signal at end state" rather than a degradation of biographical individuation.

---




## 5. Methodological discussion

### 5.1 Architectural intent decomposing into implementation interventions

The most substantive methodological finding of this iteration is that a single architectural intent — bounded mastery, expressed as "no architectural mechanism reinforces returning to a banked attractor" — required intervention at four distinct code paths to be implemented correctly. The pre-registered architecture addressed two of the four. The first amendment addressed three. The second amendment addressed all four. Each intervening implementation produced a distinct fixation pattern that the prior implementation had not anticipated, and each pattern was traceable to a specific code path where a pulling signal could be reintroduced.

This is not a finding the pre-registration could have anticipated. The pre-registration treated bounded mastery as a single architectural change, with depleted feature reward and cleared attraction bias specified as the implementation. The decomposition into four code paths emerged through the implementation sequence: each probe revealed a code path the prior specification had left unaddressed, and the corresponding amendment closed it. The amendment sequence is therefore not a record of error-correction in the implementation but a record of architectural decomposition through testing. The abstract architectural goal does not specify its own implementation; the implementation reveals what the goal actually requires.

The substantive methodological lesson generalises beyond this iteration. Architectural goals expressed at the level of "the agent should not do X" or "the cell should produce no signal Y" tend to require intervention at every code path where X could occur or Y could be reintroduced. The number of such code paths is rarely apparent from the architectural specification alone. Implementation reveals it. The discipline of pre-registration before code, amendment before amended code, and probe before batch is what surfaces this kind of decomposition without compromising the methodological record.

### 5.2 Single-variable-change discipline under multi-amendment iteration

The single-variable-change discipline that has held throughout the programme requires explicit re-examination in light of v0.11's three-implementation sequence. At the surface level, the discipline appears strained: three implementations within a single iteration suggests three architectural changes rather than one. A more careful reading shows the discipline holding at the level it was meant to address.

The single-variable-change discipline operates at the level of the iteration's research question, not the level of code modifications. v0.11's research question — does experience-driven attractor depletion with persistent banking produce a bounded mastery system that retains v0.8 developmental signatures — is a single architectural question that does not change across the amendment sequence. Each amendment refines the implementation toward the architectural intent the original pre-registration specified. The intent is held constant; what changes is the operational specification of what the intent requires.

The discipline is meaningful precisely because it is held at the right level. If the discipline were held at the level of code modifications, every implementation-time discovery would force a new iteration, and the research programme would fragment into many partial iterations each addressing a small implementation detail. Held at the level of research questions, the discipline allows multi-amendment iteration when implementation surfaces the operational requirements of an architectural goal — provided each amendment is committed to the public record before the amended code is written, with explicit reasoning for what the amendment changes.

The amendment sequence within v0.11 thus reads as a single research question being progressively decomposed into the architectural interventions it requires. The pre-registration document and the two amendment documents together specify the iteration's design decisions; the three single-run probes provide the diagnostic evidence motivating each decomposition; the final batch tests the architectural intent expressed through all four interventions operating together. The discipline is preserved because the research record is preserved.

### 5.3 Diagnostic investigation as methodological safeguard

The single-run probe under v0.11.2 initially appeared to invoke the iteration's stopping rule by reproducing a fixation pattern at attractor (9, 10) with 888 post-banking visits. The interpretation at the time was that v0.11.2 had failed and that the iteration's design itself required reconsideration rather than further amendment. A diagnostic version of v0.11.2 was implemented and run before invoking the stopping rule, with the architecture unchanged and the reporting extended to dump preference values and Q-values around mastered cells.

The diagnostic produced a substantially different result from the original probe: 6 of 6 attractors mastered with modest post-banking visit counts. The earlier interpretation that v0.11.2 produced fixation was therefore based on a single-seed outlier. Both H1 (preference accumulation on neighbour cells) and H2 (Q-value reinforcement of approach paths) returned negative ratios. The full batch run subsequently confirmed Category A.

The methodological lesson is that single-run probes are sufficient to identify architectural mechanisms but insufficient to settle whether an apparent failure represents the architecture's typical behaviour. The implementation sequence depended on single-run probes for diagnostic speed — a probe completes in under a minute, whereas a full batch takes 7–8 minutes — and probes correctly identified the fixation mechanisms each implementation produced, because those mechanisms were architecturally reproducible across seeds. But probes are insufficient to characterise a distribution. A single seed can produce a non-representative outcome whose mechanism is plausibly architectural but is in fact stochastic in its specific manifestation.

The discipline of running the diagnostic before invoking the stopping rule preserved the iteration's methodological integrity in two ways. First, it prevented a substantially incorrect conclusion (that v0.11.2 had failed) from being recorded. Second, it surfaced a generalisable principle: stopping rules should not be invoked on the basis of single-probe interpretations, because single probes can misleadingly suggest architectural failures that batch data would refute. The principle generalises to subsequent iterations: when a probe appears to invoke a stopping rule, the appropriate next step is the diagnostic investigation, not the stopping rule itself.

### 5.4 The role of the public record in methodological discipline

The amendment sequence produced seven documents on the public record within a single iteration: the v0.11 pre-registration, the v0.11.1 amendment, the v0.11.2 amendment, the v0.11 single-run probe outputs, the v0.11.1 single-run probe outputs, the v0.11.2 single-run probe outputs, and the v0.11.2 diagnostic outputs. Each was committed before the corresponding code was written or run. The chronological commit history makes the iteration's full methodological story visible to any reader of the repository.

The substantive role of this discipline is that it prevents post-hoc reshaping. Each amendment document specifies what changed and why before the change was tested. Each probe output documents what the architecture produced before the next amendment was specified. Anyone reading the repository can verify the sequence: the v0.11 architecture was specified, implemented, probed, found to produce fixation; the v0.11.1 amendment was specified to address this, implemented, probed, found to produce fixation through a different mechanism; the v0.11.2 amendment was specified to address that, implemented, probed, found to produce an apparent fixation that diagnostic investigation revealed as a seed outlier; the batch confirmed Category A.

The discipline is methodologically substantial because it is verifiable. Without it, the v0.11 paper could plausibly claim that v0.11.2's batch result represents the architecture as originally designed, with the amendment sequence treated as implementation details. With it, the paper cannot make that claim because the public record contradicts it. The amendment sequence becomes part of the contribution rather than something to manage around.

---

## 6. Architectural discussion

### 6.1 Bounded mastery as the mastery-side parallel to v0.10's threat layer

The substantive architectural finding of this paper is that the same architectural principle that resolved the unbounded-accumulation problem on the hazard side in v0.10 — categorical learned knowledge stored persistently in a representational structure separate from the dynamics that govern preferences — resolves the corresponding problem on the mastery side in v0.11.2. The mastery layer is structurally parallel to the threat layer: both are populated through experience-driven N-threshold conversion, both store binary categorical knowledge per cell, both operate as architectural interventions that bound what would otherwise be unbounded accumulation.

The two layers operate on different mechanisms but the architectural principle is the same. The threat layer prevents action selection toward flagged cells, removing them from the action-selection space entirely. The mastery layer prevents continued reward and preference accumulation on banked cells, making them inert with respect to action-selection signals. Both produce bounded effects on the agent's behaviour through interventions that operate outside the Q-value system.

v0.10 and v0.11.2 together establish persistent categorical representation as the architectural response to the unbounded-accumulation problem identified in v0.9, across both valences of categorical experience. The hazard-side test established that the principle works for negative-valence categorical learning. The mastery-side test establishes that it works for positive-valence categorical learning. The two findings together support the broader architectural claim: bounded learning of any kind in this architecture requires persistent categorical representation, stored separately from the dynamics that handle graded preferences.

### 6.2 Individuation under bounded mastery

The Category F findings establish that bounded mastery preserves individuation in the dimensions where it has architectural correlates: which attractors are banked first across runs, the order in which attractors are banked, and the absence of geographic determinism in the mastery sequence. This is a substantive finding because the v0.8 individuation finding was originally produced by unbounded preference accumulation amplifying stochastic trajectory differences. The concern was that bounding the accumulation might remove the amplification mechanism and collapse individuation into deterministic patterns. The data shows that the amplification mechanism is not the only source of individuation in the architecture.

The mechanism by which v0.11.2 preserves individuation is illuminating. Stochastic exploration shapes Phase 2 trajectories, and the trajectories themselves produce individuated mastery orderings independent of post-mastery preference dynamics. Individuation in v0.11.2 originates earlier in the developmental sequence than v0.8's mechanism predicted — at the level of which attractors are reached when, rather than which attractor becomes the settled focus. This is a different temporal layer of biographical signature, more upstream in the developmental trajectory and less dependent on the dynamics of post-Phase-2 preference accumulation.

The architectural implication is that biographical individuation in this architecture has multiple temporal layers, not all of which depend on the same mechanism. v0.8's individuation depended on unbounded accumulation amplifying trajectory differences across the full run. v0.11.2's individuation depends on stochastic exploration producing different mastery sequences during Phase 2. Both are biographical signatures; both are produced by the architecture; neither requires the other.

### 6.3 The end-state convergence finding and what it indicates

The end-state preference convergence reported in Section 4.5 is not a degradation of individuation in any sense parallel to what v0.10 demonstrates. It is the predicted architectural signature of an end-state in which no pulling signal remains. With all attractors mastered, no pre-wired bias active on mastered cells, no continued feature reward, and no preference accumulation, the agent's post-mastery exploration is shaped only by environmental geometry, the threat layer's gating of certain regions, and stochastic action selection. Different agents traverse similar exploration patterns because the underlying environmental structure is the same.

The substantive question this opens is whether bounded mastery should produce an end-state developmental target — something that activates after mastery completion to give the agent an architectural goal beyond continued exploration of neutral terrain. v0.10 provides this implicitly through unbounded attractor pull; mastered attractors in v0.10 still pull, so end-of-life settling is biographically individuated. v0.11.2 provides nothing equivalent; mastered attractors are inert, so end-of-life settling is determined by environmental geometry rather than biographical history.

Whether this is a feature or a limitation depends on what the architecture is being designed to demonstrate. As a model of bounded mastery in a single developmental phase, v0.11.2 is correct: completion of available learning produces no further pulling signals, and post-completion behaviour is exploratory rather than goal-directed. As a model of multi-stage developmental progression — in which completion of one stage activates the next — v0.11.2 is incomplete: it has no architectural mechanism for transitioning from "all available attractors mastered" to "next developmental target activated."

### 6.4 v0.13 research question: end-state target activation

The architectural question opened by the end-state convergence finding is whether introducing a mechanism that activates after mastery completion produces individuated settling on a new target. The proposal would introduce a single high-value cell that becomes available only when all six attractors have been mastered. Agents would then have an architectural reason to seek out the new target after mastery completion, and the mechanism by which they reach it would express biographical individuation parallel to but distinct from the mastery sequence.

The Montessori analogy is instructive without doing the architectural work. A child who completes their work in a Montessori classroom transitions to a next activity — perhaps queuing at the door, perhaps moving to free play, perhaps selecting a new material. The transition is provided by the structure of the environment, not by an internal drive that would activate spontaneously. Without the structural transition, the child would continue working with the materials at hand. With it, the child's biographical individuation extends to the new phase: how they transition, how quickly, with what emotional register.

A v0.13 iteration would test the analogous architectural mechanism in the developmental learner. After mastery completion, a single end-state target would activate; the agent's path to that target, time taken to reach it, and stability of preference for it would each express biographical individuation. The pre-registered hypothesis would be that introducing such a mechanism produces end-state preference distributions that show individuated settling on the new target, parallel to v0.10's settled-on-favourite signature but expressed at the post-mastery phase.

This is reserved for v0.13 specifically, with v0.12 retained for the category-level generalisation work flagged in v0.10's outlier characterisation (Baker, 2026d, Section 5.4). The two iterations address architecturally distinct questions: v0.12 tests whether categorical generalisation across hazard cells eliminates the late-encountered-hazard boundary effect; v0.13 tests whether end-state target activation produces individuated post-mastery settling. Neither depends on the other; they could be implemented in either order.

### 6.5 The architectural arc to v1.0

The research programme to date establishes a coherent architectural arc. v0.8 established the developmental signatures. v0.9 decomposed rule adherence and identified the unbounded-accumulation problem. v0.10 closed the gap on the hazard side through persistent threat representation. v0.11 closes the gap on the mastery side through persistent mastery representation, with the implementation sequence revealing that the closure requires intervention at four code paths simultaneously. v0.12 will address category-level generalisation in the threat layer. v0.13 will address end-state target activation. v0.14 and beyond may address other architectural questions the integrated architecture surfaces.

What remains for v1.0 is the integration paper that demonstrates the combined architecture passing the behavioural preservation audit across all prior findings. v1.0 is not "all iterations implemented" but "all iterations implemented and all behavioural signatures preserved across the integrated architecture." A v1.0 candidate that achieves each iteration's narrow goal but disrupts earlier findings would fail the preservation audit and would require revision before claiming baseline status.

The behavioural preservation audit is the methodological commitment that protects the programme's coherence. Each iteration to date has named what it preserves alongside what it changes. v0.10 preserved all v0.8 signatures while adding bounded hazard avoidance. v0.11.2 preserves all v0.10 signatures (rule adherence within measurement resolution, individuation in mastery sequence, attractor ratio, mastery accumulation) while adding bounded mastery. The integrated v1.0 must preserve everything any iteration has demonstrated, with the integration itself producing no novel disruption.

### 6.6 Limits of the present work

Three limits of the present work warrant explicit naming.

The architecture remains tabular and small-scale. v0.11.2 inherits the 20×20 grid, the six attractors, the five hazards, and the per-cell representation of all v0.8/v0.9/v0.10 work. Whether bounded mastery via experience-driven depletion and persistent banking generalises to non-tabular architectures, larger environments, or richer attractor structures is an open question this work does not address. The principle has been demonstrated at the smallest scale at which it can be tested; whether it scales is a separate research question.

The mastery layer in v0.11.2 is binary and per-cell, parallel to v0.10's threat layer. There is no graded mastery representation, no propagation across similar attractors, and no decay or revision. These choices were deliberate single-variable decisions matching v0.10's design philosophy. Whether richer mastery architectures (graded mastery, propagating mastery across attractor categories, revisable mastery) produce different developmental signatures is a question reserved for subsequent work.

The behavioural preservation finding (Category E firmly not triggered, individuation preserved per Category F) demonstrates that v0.10 signatures hold under v0.11.2 at the resolution the metrics measure. The end-state preference convergence finding indicates that some signatures previously not measured at this granularity (end-of-life preference distribution) are differently expressed under v0.11.2 than under v0.10. A more detailed comparison of within-phase trajectory shapes, individual-agent biographical patterns, or the temporal structure of preference accumulation might reveal additional differences not captured by the aggregate metrics reported here. The conservative reading is that v0.11.2 preserves the v0.8/v0.10 findings at the granularity at which they were originally characterised, with the end-state convergence as a measurable property at a granularity the prior characterisations did not address.

---

## 7. Conclusion

This paper has tested whether the architectural principle established in v0.10 — categorical learned knowledge stored persistently in a representational structure separate from the dynamics that govern preferences — generalises to the mastery side of the architecture. Across a pre-registered batch of 360 runs comparing v0.10 and v0.11.2 architectures across six cost levels and three run lengths with matched seeds, v0.11.2 produces Category A — full mastery trajectory — at 160,000 steps, with mean attractors mastered of 5.87 of 6 and Phase 3 cleanness of 58 of 60. All v0.8 developmental signatures are preserved, including individuation in the mastery sequence as measured by the three pre-registered Category F signals. The bounded mastery architecture works as predicted on the central hypothesis.

The paper has reported two distinct findings of equal substantive weight. The architectural finding establishes that experience-driven attractor depletion with persistent banking produces a bounded preference system that retains the developmental signatures the unbounded version produced. The methodological finding establishes that the abstract architectural goal of "no architectural mechanism reinforces returning to a banked attractor" required intervention at four distinct code paths to be implemented correctly: feature reward depletion, primitive attraction bias clearing, banking-time preference reset, and post-mastery preference accumulation blocking. The amendment sequence within the iteration decomposes the abstract goal into the operational interventions it requires, with each amendment committed to the public record before the amended code was written.

A diagnostic investigation, run before invoking the iteration's stopping rule on what appeared to be a fixation pattern in v0.11.2's single-run probe, revealed that the apparent fixation was a seed-specific outlier rather than the architecture's typical behaviour. The full batch confirmed Category A. The methodological learning is that single-run probes are sufficient to identify architectural mechanisms but insufficient to settle whether an apparent failure is the architecture's typical behaviour; stopping rules should not be invoked on the basis of single-probe interpretations.

Two findings warrant explicit honest reporting. The end-of-life top-preferred cell converges across the batch under v0.11.2, with all 60 runs at 160,000 steps showing the same top-preferred cell. This is not a loss of individuation parallel to v0.10's settled-on-favourite signature; it is the predicted architectural signature of an end-state in which no pulling signal remains. The architecture provides no mechanism that activates after mastery completion to produce individuated end-state settling, and post-mastery exploration is shaped by environmental geometry rather than biographical history. A v0.13 iteration is reserved for testing whether end-state target activation produces individuated post-mastery settling parallel to v0.10's biographical settling on attractors. The mastery acquisition profile demonstrates that mastery is not instantaneous but scales with available developmental time, with mean time to final mastery growing from 8,333 steps at the 20,000-step run length to 36,839 at 160,000, and individual runs reaching as late as step 107,083. This is the architectural signature of bounded mastery: the trajectory does not rush to complete the full attractor set but lets mastery emerge at the rate the agent's specific exploration trajectory permits.

The combined contribution of v0.10 and v0.11.2 is the architectural establishment of persistent categorical representation as the response to the unbounded-accumulation problem v0.9 identified, across both valences of categorical experience. The research arc to v1.0 continues with v0.12 (category-level generalisation in the threat layer) and v0.13 (end-state target activation in the mastery layer), with v1.0 reserved for the integration paper that demonstrates the combined architecture passing the behavioural preservation audit.

---

## 8. Code and Data Availability

All code, pre-registration documents, amendment documents, batch outputs, per-run CSV data, single-run probe outputs, diagnostic outputs, and paper drafts referenced in this work are available in the public repository at github.com/RancidShack/developmental-agent. The chronological commit history makes the full implementation sequence visible.

The v0.11 pre-registration document (committed before any v0.11 code was written) is timestamped 24 April 2026. The v0.11.1 amendment document (committed before any v0.11.1 code was written) is timestamped 24 April 2026. The v0.11.2 amendment document, including the explicit stopping rule named in its Section 7, is timestamped 24 April 2026. The v0.11.2 implementation, the diagnostic implementation, the batch runner, and the 360-run batch outputs are timestamped 24 April 2026.

Per-run data from all 360 runs in the comparative batch is available as `run_data_v0_11_2.csv` in the repository, alongside the meta-report `meta_report_v0_11_2.txt` from which the aggregate findings in this paper are derived. The single-run probe outputs from each implementation in the sequence (`self_report_v0_11_c1.0.txt`, `self_report_v0_11_1_c1.0.txt`, `self_report_v0_11_2_c1.0.txt`, and the corresponding plot files) are retained in the repository as part of the methodological record. The diagnostic implementation outputs (`self_report_v0_11_2_diagnostic_c1.0.txt`, `run_output_v0_11_2_diagnostic_c1.0.png`) are available alongside.

---

## 9. References

Baker, N.P.M. (2026a) 'Staged Development in a Small Artificial Learner: Architectural Conditions for Rule Adherence, Focused Autonomy, and Biographical Individuation', OSF Preprint, v1.0, 21 April 2026.

Baker, N.P.M. (2026b) 'The Childhood AI Never Had: Twelve Iterations of a Computational Developmental Learner', preprint in preparation for resubmission, v1.0, 21 April 2026.

Baker, N.P.M. (2026c) 'Learning Without the Wall: Decomposing Rule Adherence in a Small Artificial Learner into Pre-Wired Aversion and Cost-Based Experience', preprint v0.1, 22 April 2026.

Baker, N.P.M. (2026d) 'Experience-Driven Persistent Threat Representation Stabilises Long-Horizon Avoidance in a Small Artificial Learner', preprint v0.1, 25 April 2026.

Baker, N.P.M. (2026e) 'v0.11 Pre-Registration: Experience-Driven Attractor Depletion and Persistent Mastery Representation', GitHub repository, github.com/RancidShack/developmental-agent, 24 April 2026.

Baker, N.P.M. (2026f) 'v0.11.1 Pre-Registration Amendment: Preference Reset on Mastery', GitHub repository, github.com/RancidShack/developmental-agent, 24 April 2026.

Baker, N.P.M. (2026g) 'v0.11.2 Pre-Registration Amendment: Preference Accumulation Blocked on Mastered Cells', GitHub repository, github.com/RancidShack/developmental-agent, 24 April 2026.

---

## 10. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper. The treatment of FLA principles in the broader programme is bounded; the computational findings reported here are claimed on their own architectural terms, with FLA serving as a process scaffold for experimental design rather than as the framework being instantiated.

The Montessori analogy used in Section 6.4 is a conceptual reference to Maria Montessori's prepared environment principle in early childhood education. The analogy is deployed to clarify the architectural principle of end-state target activation; no claim is made that the v0.11.2 architecture or any subsequent iteration models Montessori pedagogy specifically, or that Montessori principles are derivable from the architectural findings reported here. The analogy is used as a conceptual aid rather than as theoretical foundation.

No human participant data were collected. No external parties had access to drafts of this paper prior to its preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
