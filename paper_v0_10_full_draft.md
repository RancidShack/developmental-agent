# Experience-Driven Persistent Threat Representation Stabilises Long-Horizon Avoidance in a Small Artificial Learner

**Author:** Nicholas P M Baker, Synapstak Ltd
**Date:** 25 April 2026
**Status:** Working draft — sections 1-4

---

## Abstract

A preceding paper (Baker, 2026c) identified an architectural instability in a small tabular developmental agent: when hazard avoidance was reduced to cost-based experience alone, with no pre-wired aversion and no environmental wall, the learned avoidance produced by cost was bounded in cumulative magnitude while the preference accumulator that dominated Phase 3 action selection accumulated without bound. The result was non-monotonic Phase 3 cleanness across run length: 29 of 60 runs at 20,000 steps, 43 of 60 at 80,000, 34 of 60 at 160,000. Bounded learned knowledge stored in distributed Q-value adjustments was overwhelmed by unbounded preference at extended horizons.

The present paper tests whether adding a persistent threat representation, populated by experience and consulted as a hard gate before Q-value computation, resolves this instability while preserving the developmental signatures the architecture was previously demonstrated to produce. Across a pre-registered batch of 360 runs spanning two architectures (v0.9 and v0.10), six cost levels, and three run lengths with matched seeds, we find: (i) full stabilisation of Phase 3 cleanness at the longest run length, with v0.10 producing 60 of 60 clean runs at 160,000 steps against v0.9's 48 of 60 under matched conditions; (ii) monotonic improvement of cleanness across run length in v0.10 (53 → 58 → 60 of 60), reversing the non-monotonic degradation observed in v0.9; (iii) substantially reduced cumulative cost in v0.10, by approximately 50–75% across cost levels, indicating that persistent representation makes learned avoidance not only stable but efficient; (iv) preservation of all v0.8 developmental signatures (concentration, attractor ratio, mastery, individuation), with no measurable disruption from the addition of the threat layer. We characterise an outlier condition (cost 5.0 at 20,000 steps showing 5/10 Phase 3 cleanness) as a boundary case where the per-cell-no-generalisation property of the architecture interacts with the run-length budget for flag conversion. The findings support a stronger formulation of the v0.9 conclusion: bounded learned knowledge requires not only conversion of cost into representation, but persistent representation stored outside the dynamics that govern preferences. The architectural principle generalises to other forms of categorical knowledge in the architecture; the v0.11 paper (Baker, 2026e, in preparation) tests it on the mastery side.

---

## 1. Introduction

### 1.1 Programme to date

A small tabular developmental agent occupying a 20×20 structured environment has, across previous papers, demonstrated five behavioural signatures associated with developmental learning: absolute rule adherence, focused autonomy, feature-aligned preference formation, a specialist-generalist trade-off, and full biographical individuation (Baker, 2026a, 2026b). The agent operates under a three-phase developmental schedule (prescribed acquisition, integration, autonomy) with drives composed from novelty, learning progress, preference, and feature signals weighted differently at each phase. Hazard handling in the v0.8 architecture combined two architecturally distinct elements: an environmental wall preventing hazard entry, and a pre-wired perceptual bias against hazard-adjacent actions.

A preceding paper (Baker, 2026c) decomposed this combined mechanism into its constituent parts. Across pre-registered conditions removing the wall, removing the bias, and removing both, the paper established that the pre-wired aversion alone was sufficient to produce v0.8's zero-violation result. When both wall and aversion were removed and only experienced cost remained as the avoidance signal, agents learned partially and transiently. Most relevantly for the present paper, this learning did not stabilise under extended run length but degraded non-monotonically, with Phase 3 cleanness improving from 29 of 60 at 20,000 steps to 43 of 60 at 80,000 steps before regressing to 34 of 60 at 160,000 steps.

The architectural interpretation offered was that cost-based learning produces distributed per-state-action Q-value adjustments that are bounded in their accumulated magnitude, while the preference drive that dominates Phase 3 action selection accumulates without bound across time. In the absence of a persistent representational structure for learned hazard knowledge, the preference accumulator wins at extended horizons. The paper identified this as an architectural gap and argued that any learned-rule version of the architecture would require persistent representation to stabilise rule adherence against preference dynamics.

### 1.2 The present paper

The present paper tests whether experience-driven persistent threat representation, added to the v0.9 architecture and consulted as a hard gate before Q-value computation, resolves the long-horizon instability identified in v0.9 while preserving the developmental signatures the architecture was previously demonstrated to produce.

The architectural addition is specified in detail in Section 2. In summary: a per-cell binary flag is maintained for each cell in the environment. Frame cells (the environmental boundary) are pre-flagged at agent creation, consistent with their role as ontological wall in the v0.8 architecture. Hazard cells begin unflagged. A per-cell entry counter increments whenever the agent enters a hazard cell. When the counter reaches a pre-registered threshold of three entries, the cell's flag is set to one. Once flagged, a cell is excluded from action selection: any action that would target the flagged cell is removed from the candidate set before Q-value computation occurs. Flags do not clear.

The architectural principle being tested is that persistent categorical knowledge, stored in a representational structure separate from the Q-value system and consulted before action selection, can resist erosion by preference dynamics that overwhelm bounded distributed knowledge in v0.9. The threat layer addresses the v0.9 instability not by changing how the agent learns (the cost mechanism is retained unchanged) but by changing where learned knowledge is stored once it has been acquired.

### 1.3 Hypotheses

The central hypothesis pre-registered for this work is that the addition of an experience-driven persistent threat layer will stabilise Phase 3 hazard avoidance at extended run lengths. Specifically, v0.10 at 160,000 steps was predicted to produce Phase 3 cleanness counts substantially higher than v0.9 at the same condition, with the non-monotonic degradation observed in v0.9 absent in v0.10.

A secondary hypothesis pre-registered alongside the central hypothesis was that the broader developmental signatures established in v0.8 and held through v0.9 would be preserved. The threat layer should operate as an architecturally distinct system handling hazard knowledge without interfering with preference-and-value dynamics that produce concentration, attractor ratio, mastery accumulation, and individuation.

### 1.4 Connection to the broader research programme

The architectural question opened by v0.9 — bounded learned knowledge versus unbounded preference accumulation at extended horizons — is more general than the hazard side alone. The same dynamic could in principle affect any form of learning the architecture retains: positive experience accumulates preference unboundedly, mastered knowledge has no persistent storage outside Q-values, individuation is produced specifically by preference accumulation amplifying stochastic trajectory differences. v0.10 addresses this question for hazards. A subsequent paper (Baker, 2026e, in preparation) tests whether the same architectural principle — experience-driven conversion to persistent representation — applied to the mastery side produces a bounded preference system that retains the developmental signatures the unbounded version produced.

The present paper is therefore best understood as the first half of a programmatic answer to the question v0.9 raised: persistent representation is the architectural response to unbounded accumulation. The hazard-side test offered here, isolating the principle on a single side of the architecture and at a single category of experience, is intended to establish whether the principle works at all before the mastery-side extension is attempted.

---

## 2. Methods

### 2.1 Environment

The environment is identical to that used in v0.8 and v0.9 (Baker, 2026a, 2026c). A 20×20 grid contains four cell types. Frame cells form the environmental boundary; they are impassable in v0.8/v0.9 and remain impassable in v0.10. Hazard cells are clustered in two groups (a three-cell cluster and a two-cell cluster) at fixed coordinates; in v0.10 these are passable at scalar cost, matching v0.9's cost_no_aversion mode. Attractor cells are six fixed locations at which the agent receives feature reward on entry. Neutral cells fill the remainder of the passable interior.

The agent starts each run at coordinate (1, 1) and operates under the three-phase developmental schedule: Phase 1 (prescribed acquisition) traversing all passable cells via a deterministic boustrophedon path; Phase 2 (integration) operating drive-based action selection from the end of Phase 1 until a fixed proportion (60%) of total run length is reached; Phase 3 (autonomy) operating from this point to end of life with preference weighting active.

### 2.2 v0.10 architectural specification

v0.10 inherits the v0.9 architecture in cost_no_aversion mode unchanged except for the addition of two new structures and one modification to action selection.

**Threat layer.** A dictionary `threat_flag` indexed by cell coordinates, with binary values. At agent creation, all frame cells are initialised to flag value 1. All hazard, attractor, and neutral cells are initialised to flag value 0.

**Hazard entry counter.** A dictionary `hazard_entry_counter` indexed by cell coordinates, initialised to zero for all cells. The counter increments by 1 whenever the agent enters a hazard cell, regardless of phase.

**Flag conversion rule.** When the entry counter for a hazard cell reaches the pre-registered threshold of three, the cell's threat flag is set to 1. The conversion is one-way; flags do not clear at any point in the run.

**Action-selection rule.** During action selection, for each candidate action, the destination cell is checked against the threat layer. If the destination cell's flag is 1, the action is excluded from the action selection pipeline entirely — it does not enter Q-value computation, primitive bias computation, or epsilon-greedy random selection. This constitutes a hard gate operating before all other action-selection mechanisms.

The hard gate operates in addition to existing v0.8/v0.9 mechanisms: frame cells are hard-gated from agent creation (consistent with their pre-flagged status), and hazard cells become hard-gated only after three entries have converted their flag. Before flag conversion, hazard cells remain passable at cost, exactly as in v0.9 cost_no_aversion mode.

The pre-wired aversion bias from v0.8, which applies a -5.0 penalty to actions adjacent to frame cells, is retained for frames in v0.10. Hazards have no pre-wired aversion (consistent with v0.9 cost_no_aversion). Attractor cells continue to receive a +0.3 attraction bias on adjacent action selection, unchanged from v0.8.

Per-cell, no category-level generalisation. The threat layer operates per cell. There is no mechanism by which flagging one hazard cell affects the counter or flag of any other hazard cell. The agent learns each hazard cell independently, requiring three entries per cell for conversion. This is a deliberate design choice consistent with the single-variable-change discipline of the iteration: v0.10 tests persistent representation, not generalisation across categories.

### 2.3 Drive composition and learning parameters

All v0.9 drive composition and learning parameters are retained unchanged. Phase 1 has all drive weights set to zero (movement is prescribed). Phase 2 has novelty weight 0.3, learning progress weight 1.2, preference weight 0.0, feature reward weight 0.15. Phase 3 has the same novelty and learning progress weights as Phase 2, with preference weight raised to 0.8 and feature weight retained at 0.15. Q-values are reset by multiplication with a factor of 0.3 at each phase transition. Standard TD learning applies with learning rate 0.1, discount factor 0.9, and epsilon-greedy exploration with epsilon 0.1.

The cost mechanism on hazard entry operates as in v0.9: each entry into an unflagged hazard cell delivers the configured hazard cost as a negative addition to the agent's intrinsic reward stream, where it flows into Q-value updates via the standard TD learning rule. After flag conversion, the agent does not enter the cell at all (because the action targeting it is hard-gated), so no further cost is paid.

### 2.4 Experimental matrix and matched-seed comparison

The experimental matrix is two architectures crossed with six cost levels crossed with three run lengths crossed with ten runs per cell, totalling 360 runs.

The architectures are v0.9 (operating in cost_no_aversion mode, as published in Baker, 2026c) and v0.10 (with the threat layer added). The cost levels are 0.1, 0.5, 1.0, 2.0, 5.0, and 10.0. The run lengths are 20,000, 80,000, and 160,000 steps. The same set of run lengths used in v0.9 is retained to enable direct comparison of the run-length-dependent stability finding.

For each (cost, run length, run index) triple, both architectures use the same random seed. This produces matched-seed comparison: the v0.9 and v0.10 runs at the same condition share initial exploration trajectories until the threat layer first intervenes in v0.10 (which cannot be earlier than the third hazard entry of any agent). Comparison is therefore within-seed up to the point at which the threat layer begins operating, and the divergence after that point is attributable to the threat layer specifically.

The v0.9 architecture is reimplemented within the batch runner as a class parameterised by hazard cost, rather than imported from the v0.9 module which reads cost from module-level globals. The reimplementation is functionally identical to the published v0.9 in cost_no_aversion mode. This approach allows the batch to vary cost without requiring file modifications between cells, ensuring exact methodological consistency.

### 2.5 Metrics

Metrics retained from v0.8 and v0.9:

Hazard entries by phase (Phase 1, Phase 2, Phase 3, total). Phase 3 cleanness defined as fewer than three hazard entries during Phase 3, in line with the v0.9 pre-registration. Full-run cleanness defined as fewer than three hazard entries across the entire run. Phase 3 concentration (the maximum cell visit count in Phase 3 divided by the uniform expectation). Phase 3 attractor ratio (the proportion of Phase 3 visits that fall on attractor cells, divided by the chance expectation). Mastery count (the number of state-action pairs whose recent prediction errors have stabilised below a threshold of 0.15). Top-five preferences (the five cells with highest accumulated preference at end of run). Individuation (the count of distinct primary attractors across the runs in a batch).

Metrics specific to v0.10:

Number of hazard cells flagged per run. Time to first flag (the step at which the first hazard cell's flag was converted). Time to final flag (the step at which the most recently converted hazard's flag was set). Cost paid up to final flag (the cumulative hazard cost incurred between agent creation and the time of final flag, representing the "price of learning" for experience-driven conversion). Actions gated by threat layer per phase (the count of action-selection candidates excluded by the hard gate during each phase).

Per-run numerical data is preserved in CSV format for post-hoc analysis. Aggregate findings are reported per-cost-level and per-run-length in this paper.

### 2.6 Pre-registered interpretation categories

Five interpretation categories were pre-registered before the batch was run, with the assignment based on Phase 3 cleanness at 160,000 steps as the primary measure.

Category A — full stabilisation: v0.10 at 160,000 steps produces Phase 3 cleanness of at least 55 of 60 runs across all cost levels. Category B — partial stabilisation: between 40 and 54 of 60 runs. Category C — no meaningful stabilisation: 39 or fewer of 60 runs (no improvement over v0.9). Category D — over-flagging: substantially more cells flagged than expected, with non-hazard cells flagged or all hazards flagged within the first 1,000 steps of Phase 2. Category E — developmental degradation: secondary developmental signatures substantially reduced compared with v0.9 even if Phase 3 cleanness is improved.

The pre-registration document (Baker, 2026d) is committed to the public repository at github.com/RancidShack/developmental-agent and timestamped before any v0.10 code was written.

---

## 3. Results

### 3.1 Headline finding: full stabilisation at all run lengths

At 160,000 steps, v0.10 produced 60 of 60 Phase 3 clean runs across all six cost levels and ten runs per cost. Under matched seeds, v0.9 at the same condition produced 48 of 60. The pre-registered Category A threshold (≥55 of 60) is exceeded; v0.10 produces full stabilisation, not merely improved stabilisation.

The full table of Phase 3 cleanness across run length, cost level, and architecture is shown in Table 1.

**Table 1. Phase 3 cleanness counts (out of 10 per cost level, with 60 totals shown across six cost levels per architecture per run length).**

| Run length | v0.9 cleanness | v0.10 cleanness |
|---|---|---|
| 20,000 steps | 49/60 | 53/60 |
| 80,000 steps | 38/60 | 58/60 |
| 160,000 steps | 48/60 | 60/60 |

The pattern across run lengths is the more substantive finding than the headline cleanness count alone. v0.9 shows the non-monotonic pattern (49 → 38 → 48) that the original v0.9 paper identified as evidence of architectural instability, with cleanness improving from 20,000 to 80,000 steps then regressing at 160,000 steps. v0.10 shows monotonic improvement (53 → 58 → 60), with cleanness increasing as run length increases. The non-monotonic instability is absent in v0.10 across the full tested range.

The matched-seed comparison strengthens this finding. At the 160,000-step condition specifically, the same set of random seeds produces 48 clean runs under v0.9 and 60 clean runs under v0.10. The 12 runs in which v0.9 produced Phase 3 violations are runs in which v0.10 produced clean Phase 3 behaviour, with the architectural difference attributable to the threat layer specifically.

### 3.2 Cost economics: persistent representation reduces cumulative cost

A finding not anticipated by the pre-registration but clearly visible in the batch data is that v0.10 paid substantially less cumulative cost than v0.9 across all cost levels and run lengths.

**Table 2. Mean total cost incurred per run, by architecture and cost level, at 160,000 steps.**

| Cost level | v0.9 total cost | v0.10 total cost | v0.10 / v0.9 |
|---|---|---|---|
| 0.1 | 9.28 | 0.88 | 0.09× |
| 0.5 | 15.85 | 4.80 | 0.30× |
| 1.0 | 23.10 | 6.40 | 0.28× |
| 2.0 | 34.40 | 17.80 | 0.52× |
| 5.0 | 147.50 | 43.50 | 0.29× |
| 10.0 | 217.00 | 88.00 | 0.41× |

Across cost levels, v0.10 paid between 9% and 52% of the cost v0.9 paid for matched conditions. The mechanism is straightforward: in v0.9, the agent continues to encounter the same hazards repeatedly across the full run length, paying cost on every encounter. In v0.10, once the threat layer has flagged a hazard, the agent does not encounter it again, so the cost paid on that hazard is bounded at three units of cost (the three encounters required for flag conversion). Across multiple hazards and across the full run, this produces dramatically reduced cumulative cost.

The cost economics finding adds substance to the headline finding. v0.10 does not merely produce stable avoidance; it produces stable avoidance at substantially lower lifetime cost than v0.9. The threat layer makes learned avoidance both more reliable and more efficient.

### 3.3 Threat-layer dynamics across the batch

The threat layer's behaviour can be characterised across the batch through the four v0.10-specific metrics. Mean values aggregated across cost levels at each run length are reported here; per-cost-level data is available in the per-run CSV.

**Table 3. Threat-layer dynamics across run length (mean values across all 60 v0.10 runs at each run length).**

| Run length | Hazards flagged | Time to first flag | Mean total cost |
|---|---|---|---|
| 20,000 steps | 1.37 / 5 | 5,669 | 18.48 |
| 80,000 steps | 1.80 / 5 | 11,237 | 20.29 |
| 160,000 steps | 2.22 / 5 | 16,990 | 26.90 |

Three patterns are visible in the data.

First, the number of hazards flagged per run grows with run length. Mean values increase from 1.37 of 5 at 20,000 steps to 2.22 of 5 at 160,000 steps. The architecture continues to discover and flag new hazards across the full run length, with later-discovered hazards reaching N=3 conversion progressively.

Second, the time to first flag also grows with run length. The mean of 5,669 steps at the 20,000-step condition rises to 16,990 at 160,000 steps. This is consistent with the per-cell-no-generalisation property of the architecture: at longer run lengths, agents can spend more time exploring before encountering hazards repeatedly enough to trigger flagging, particularly in distant regions of the environment that take longer to reach.

Third, the maximum time to first flag at 160,000 steps is 149,831 steps. Some agents discover new hazards extremely late in the run. When they do, the threat layer captures the learning permanently and Phase 3 cleanness is preserved, even though the discovery was very late.

The distribution of hazards flagged per run is broad. At 160,000 steps, 6 runs flagged 0 hazards, 14 flagged 1, 16 flagged 2, 12 flagged 3, 9 flagged 4, and 3 flagged 5. Most runs achieved Phase 3 cleanness through a combination of active avoidance (for cells the threat layer flagged) and disinterest (for cells the agent never approached enough to trigger flagging). This pattern is the empirical signature of the per-cell-no-generalisation design choice operating as intended: the agent's hazard knowledge at end of run reflects which specific hazards the agent encountered, not a categorical understanding of "hazards" as a class.

### 3.4 Behavioural preservation: developmental signatures retained

The pre-registered Category E (developmental degradation) is firmly not triggered. All v0.8 developmental signatures held in v0.10 are preserved.

Phase 3 attractor visit ratios in v0.10 ranged from 7.19× chance to 12.45× chance across run lengths and cost levels, comparable to v0.9's range. Phase 3 concentration values exceed 50× uniform across the batch, consistent with v0.8's settled-attention finding. Mastery count (state-action pairs at the v0.8 mastery threshold) ranges from 67 to 198 across run lengths, growing with run length as expected.

Individuation is preserved. At 160,000 steps, all six attractors appear as primary focus across the v0.10 batch, with the same broad distribution observed in v0.8 and v0.9. The threat layer does not disrupt the biographical signature that has held throughout the programme: identical agents in identical conditions still become different agents through their specific developmental trajectories.

The full v0.8 finding suite is therefore demonstrably compatible with the threat-layer addition. The architecture in v0.10 produces v0.8's behavioural signatures plus stable long-horizon hazard avoidance plus dramatically reduced cumulative cost, with no measurable trade-off detected on the secondary metrics.

---

## 4. Outlier characterisation: cost 5.0 at 20,000 steps

The batch produced one outlier condition worth explicit characterisation. v0.10 at cost 5.0 at 20,000 steps showed Phase 3 cleanness of 5 of 10, against the otherwise-uniform pattern of 8–10 of 10 across all other (cost, run length) cells in v0.10's matrix. The mean Phase 3 entries at this specific condition was 1.90, against the otherwise-uniform pattern of 0.0–0.6 elsewhere.

### 4.1 Investigation of the per-run data

Examination of the per-run CSV at this specific condition reveals a consistent pattern across the five non-clean runs. The non-clean runs all show late conversion of the final hazard flag, with time-to-final-flag values ranging from 6,691 steps to 19,974 steps. By contrast, the five clean runs at the same condition either flagged hazards before Phase 3 began (with the earliest at step 8,623 and the latest at step 11,525, all before the 12,000-step Phase 2/Phase 3 boundary), or never approached hazards at all (one run flagged zero hazards because no hazard cell was visited).

The five non-clean runs share a specific behavioural pattern: the agent encountered a novel hazard cell late in Phase 2 or during Phase 3 itself, and the per-cell-no-generalisation property of the architecture meant that two further entries into that specific cell were required before the flag converted. At cost 5.0, those two pre-flag entries each contribute 5 units of cost and count toward Phase 3 entries when they occur during Phase 3. With only 8,000 Phase 3 steps available in a 20,000-step run, late-encountered hazards have insufficient time budget for flag conversion to complete cleanly.

### 4.2 Why this disappears at longer run lengths

At 80,000 and 160,000 steps, Phase 3 lasts 32,000 and 64,000 steps respectively. A novel hazard encountered late in Phase 2 has substantially more time to complete N=3 flag conversion before the run ends, so even late-encountered hazards reach stable flag status during Phase 3. Empirically, the cost 5.0 condition produces 10 of 10 cleanness at both 80,000 and 160,000 steps, confirming that the boundary effect is specific to the short run length.

### 4.3 Why cost 5.0 specifically and not other costs

The boundary effect is most visible at cost 5.0 because of a specific interaction between cost magnitude and the Phase 3 cleanness threshold.

At lower costs (0.1, 0.5, 1.0, 2.0), Phase 3 entries do count individually toward the cleanness threshold, but the cost itself is small enough that the agent does not strongly avoid the cell pre-flag through Q-value learning either. Behaviour is similar across the cost range — the agent enters hazards, learns slowly via cost, and the threat layer eventually flags them. Cleanness depends on time budget rather than on cost magnitude.

At cost 10.0, the per-entry cost is severe enough that the agent's local Q-values become strongly negative very quickly, making the cell aversive even before flag conversion completes. The cost signal itself approaches sufficiency for avoidance at this magnitude, and the threat layer adds persistence on top. Most agents do not return to a cost-10.0 hazard after one or two entries, so the time-budget pressure does not produce non-clean Phase 3 behaviour.

Cost 5.0 sits in a specific intermediate regime: substantial enough that Phase 3 entries count meaningfully against cleanness, but not severe enough that a small number of entries produce decisive Q-value-based avoidance before flag conversion completes. At the 20,000-step run length specifically, this combination produces the visible boundary effect.

### 4.4 Architectural significance

The outlier finding is real and is reported here without reshaping. It reveals a specific architectural property of v0.10: at the boundary where (a) cost is high enough for Phase 3 entries to count as violations and (b) run length is short enough that late-encountered hazards cannot complete the three-entry flag conversion within Phase 3's time budget, the architecture produces non-monotonically-clean results. This is the per-cell-no-generalisation design choice expressed in its boundary-condition behaviour rather than a failure of the architecture.

The architectural implication, made explicit in the v0.10 pre-registration and in Section 4.7 of that document, is that the per-cell mechanism produces variation in time-to-final-flag across runs as a function of the agent's specific exploration trajectory. Some agents encounter all five hazards during Phase 1 and Phase 2; others encounter only some of them, with the remainder either never approached at all or approached late. The outlier condition is the regime in which "approached late but at sufficient cost to count" is the dominant pattern across runs.

This boundary characterisation strengthens rather than weakens the architectural claim of the paper. The threat layer produces full Phase 3 cleanness across a broad parameter space, with one specific corner of the matrix producing partial cleanness in a way that the architecture's design choices predict and that disappears at longer run lengths. The threat layer is the right architectural answer for the question v0.9 posed; the boundary condition reveals where the per-cell-no-generalisation choice meets its operational limits and motivates the v0.12 paper's investigation of category-level hazard generalisation as a separate research question.

---




## 5. Discussion

### 5.1 Persistent representation as the architectural response to unbounded accumulation

The central finding of this paper is that experience-driven persistent threat representation, stored outside the Q-value system and consulted as a hard gate before action selection, resolves the long-horizon instability identified in v0.9. The Category A result at 160,000 steps establishes this empirically; the monotonic improvement across run lengths in v0.10 against v0.9's non-monotonic degradation establishes the architectural mechanism.

The architectural principle the result demonstrates is more general than the specific finding. v0.9 identified a problem: bounded learned knowledge stored distributedly in Q-value adjustments cannot resist erosion by unbounded preference accumulation across extended time horizons. The Q-value system that holds learned hazard knowledge competes with the preference accumulator on the same axis (both contribute to action-selection signals through different multiplicative weights), and the accumulator's unboundedness eventually wins. Persistent representation breaks this competition by moving categorical learned knowledge to a different axis entirely. The threat layer does not contribute to Q-value computation at all; it operates as a gate before Q-values are consulted. The accumulator can grow without bound and it does not matter, because the gate has already excluded flagged cells from the action-selection space.

This architectural principle — categorical learned knowledge in a separate persistent representation, consulted before the dynamics that handle graded preferences — is the substantive contribution this iteration makes to the programme. The principle generalises: any form of learning that produces categorical knowledge needing to resist erosion by ongoing accumulation could in principle be handled the same way. The v0.10 paper tests this for hazards specifically. A subsequent paper (Baker, 2026e, in preparation) tests whether the same architectural principle applied to mastery — repeated attractor visits converting to persistent banked-mastery representation, with depleted attractors no longer producing reward — produces a bounded preference system that retains v0.8's developmental signatures.

The framing of v0.9, v0.10, and v0.11 as a single architectural arc is therefore deliberate. v0.9 identified that the v0.8 architecture has no persistent storage for learned categorical knowledge. v0.10 closes this gap on the hazard side. v0.11 closes it on the mastery side. The arc proposes that bounded learning of any kind requires architectural machinery that v0.8 did not need to demonstrate its findings — but that any complete developmental architecture must include.

### 5.2 The cost economics finding and what it means

The 50–75% reduction in cumulative cost across cost levels in v0.10 against v0.9 was not anticipated by the pre-registration but emerged clearly in the data. The mechanism is mechanically straightforward: flagged hazards are not entered, so no further cost is paid on them. Across multiple hazards and across full run lengths, the bounded cost of three pre-flag entries per hazard accumulates to substantially less than the unbounded cost v0.9 pays through repeated re-encounters.

What the finding reveals beyond its mechanical simplicity is that persistent representation makes learned avoidance not only stable but efficient. The v0.9 architecture pays cost continuously to maintain its avoidance behaviour; the v0.10 architecture pays cost once to learn, then never again. This is a meaningful asymmetry between graded and categorical learning architectures: graded learning maintains its signal through ongoing experience, while categorical learning preserves its signal through persistent representation that does not require continued cost to remain effective.

The architectural implication is that the threat layer is not just a stabilisation mechanism for Phase 3 cleanness; it is a mechanism that converts experienced cost into permanent learned knowledge at a fixed cost per hazard. Once an agent has paid three units of cost on a particular hazard, the architecture has retained that knowledge for the remainder of the agent's life. v0.9 has no such conversion mechanism; cost paid in v0.9 produces only the bounded Q-value adjustments that decay against preference dynamics, so the agent must keep paying to keep the learning effective.

The cost economics finding adds substance to the claim that v0.10 is a stronger architecture than v0.9, not just on the narrow Phase 3 cleanness metric but on a broader measure of how the architecture handles experiential cost. A developmental learner that pays cost once to learn permanently is doing something different from a developmental learner that must keep paying to keep its learning. The threat layer instantiates the first kind of learning; v0.9's cost-only architecture instantiates the second.

We note this finding without overclaiming its biological or theoretical significance. The mechanism producing the cost reduction is the architectural fact that flagged cells are no longer entered. The finding is that this architectural fact has a substantively measurable behavioural consequence. Whether the same asymmetry between continuous-cost and one-time-cost learning operates in biological developmental systems is a separate question this paper does not address.

### 5.3 The outlier as architectural revelation

The outlier condition characterised in Section 4 — cost 5.0 at 20,000 steps producing 5 of 10 Phase 3 cleanness — is not a failure of the architecture, but it is also not a triviality. The mechanism the per-run data reveals is that the per-cell-no-generalisation property of the threat layer interacts with run length in a specific way: agents who encounter novel hazards late in Phase 2 or early in Phase 3 cannot complete the three-entry flag conversion within the remaining time budget if the run length is short and the cost is high enough to count entries as Phase 3 violations.

This is the per-cell design choice meeting its operational limit. The choice was deliberate: v0.10 tests persistent representation, not generalisation across categories, and the pre-registration named this explicitly (Baker, 2026d, Section 4.7). The architecture as designed acquires hazard knowledge cell by cell through repeated experience, with no mechanism for transferring knowledge from experienced hazards to unencountered ones. At long run lengths the agent has time to learn each hazard it encounters; at short run lengths with moderate cost, the time budget can run out before learning completes for late-encountered hazards.

The architectural significance is that the outlier condition reveals the cost of the per-cell-no-generalisation choice in a specific corner of the parameter space. Outside that corner, the architecture produces full Phase 3 cleanness. Within it, the architecture produces partial cleanness whose mechanism is fully explainable from the design choices the architecture made.

The finding motivates a specific subsequent research question: would adding category-level generalisation to the threat layer — such that the perceptual signature of one flagged hazard cell propagates to other hazard cells the agent encounters — eliminate the boundary condition by allowing late-encountered hazards to be flagged on first entry rather than after three? This is not a question this paper answers. It is the question a subsequent v0.12 paper will address (briefly outlined in Section 5.4 below). The honest reporting of the outlier condition makes that subsequent research question a follow-on contribution rather than a post-hoc rationalisation.

### 5.4 Architectural questions opened by v0.10

Three architectural questions are opened by the v0.10 findings, each of which is plausibly addressable through a separate iteration of the architecture and is reserved for future work.

The first is whether category-level generalisation in the threat layer would eliminate the boundary condition characterised in Section 4. The minimal version of this would be to introduce a perceptual signature for hazard cells, such that when the agent first encounters any cell whose signature matches an already-flagged hazard, the new cell is flagged on first entry rather than after three. This represents one-shot generalisation from existing categorical knowledge, structurally different from v0.10's per-cell experiential learning.

The second is whether the mastery side of the architecture exhibits a parallel instability to the hazard side identified in v0.9. The v0.9 paper identified the unbounded-accumulation problem specifically in the context of cost-based hazard learning, but the same dynamic would in principle affect any form of categorical knowledge that the architecture acquires through experience. A subsequent paper (Baker, 2026e, in preparation) tests this for the mastery side: whether attractors that are visited repeatedly produce a similar architectural problem if their effects accumulate without bound, and whether experience-driven persistent mastery representation, populated through depletion-and-banking, resolves it analogously to the threat layer's resolution on the hazard side.

The third is the broader architectural question of what a complete v1.0 baseline architecture would look like once both threat and mastery layers are established. v0.10 demonstrates persistent categorical hazard knowledge; v0.11 (pending) will demonstrate persistent categorical mastery knowledge; what remains for v1.0 is to verify that the integrated architecture preserves all v0.8 developmental signatures while incorporating both layers, and to characterise the architecture's behaviour as a complete developmental learner rather than as a sequence of single-issue extensions. This work is reserved for a subsequent integration paper.

### 5.5 Limits of the present work

Three limits of the present work are worth naming explicitly.

The architecture remains tabular and small-scale. The 20×20 grid is sufficient for testing the architectural principle but does not address scale-related questions about how the principle would behave in environments with thousands or millions of states, with continuous rather than discrete spaces, or with non-tabular representations. Whether persistent categorical representation generalises to non-tabular architectures is an open question this work does not address.

The threat layer in v0.10 is binary and per-cell. There is no graded persistent representation, no propagation of categorical knowledge across similar cells, and no decay or revision mechanism. These choices were deliberate single-variable decisions to test whether the simplest possible persistent representation works at all before more complex variants are explored. The simplest version works; whether richer persistent-representation architectures (graded, propagating, revisable) produce different developmental signatures is also a question this paper does not address.

The behavioural preservation finding (Category E firmly not triggered) demonstrates that v0.8 signatures hold under v0.10 at the resolution the metrics measure. It does not demonstrate that the threat layer has zero subtle effects on developmental behaviour at finer-grained levels of analysis. A more detailed comparison of within-phase trajectory shapes, individual-agent biographical patterns, or the temporal structure of preference accumulation might reveal subtle differences not captured by the aggregate signatures reported here. The conservative reading is that v0.10 preserves the v0.8 findings at the granularity at which v0.8 was characterised, and that finer-grained comparison is a separate research question.

---

## 6. Conclusion

This paper has tested whether experience-driven persistent threat representation resolves the long-horizon hazard-avoidance instability identified in v0.9 (Baker, 2026c). Across a pre-registered batch of 360 runs comparing v0.9 and v0.10 architectures across six cost levels and three run lengths with matched seeds, we find Category A — full stabilisation — at 160,000 steps, with v0.10 producing 60 of 60 clean Phase 3 runs against v0.9's 48 of 60 under matched conditions. The non-monotonic degradation of Phase 3 cleanness across run length observed in v0.9 is absent in v0.10, with cleanness instead improving monotonically as run length increases. The threat layer also reduces cumulative cost by 50–75% across cost levels, an unanticipated finding that adds substance to the architectural claim: persistent representation makes learned avoidance not only stable but efficient. All v0.8 developmental signatures (concentration, attractor ratio, mastery, individuation) are preserved under v0.10, with no measurable disruption from the threat layer's addition.

A boundary condition was characterised honestly: at cost 5.0 at 20,000 steps, the per-cell-no-generalisation property of the architecture interacts with the run-length budget for flag conversion to produce partial Phase 3 cleanness (5 of 10). The mechanism is identifiable and the effect disappears at longer run lengths. This boundary condition reveals the cost of the per-cell design choice in a specific corner of the parameter space and motivates a separate research question (category-level generalisation in the threat layer) reserved for subsequent work.

The architectural principle the paper demonstrates — categorical learned knowledge stored persistently in a representational structure separate from the dynamics that govern preferences — generalises beyond the hazard side. v0.9 identified that the v0.8 architecture lacks persistent storage for any learned categorical knowledge; v0.10 closes this gap for hazards; v0.11 (Baker, 2026e, in preparation) tests whether the same architectural principle applied to mastery produces a bounded preference system that retains v0.8's developmental signatures. The two iterations together would establish persistent representation as the architectural response to the unbounded-accumulation problem v0.9 identified, with v1.0 reserved for the integration paper that demonstrates both layers operating together.

The methodological discipline that has held throughout the programme — pre-registration before computation, single-variable change per iteration, behavioural preservation audit across iterations, honest reporting of findings as they occur — held during this iteration without amendment. The pre-registration document committed to the public repository before any v0.10 code was written specified the experimental matrix, metrics, and interpretation categories used in this paper. The findings reported here are the findings the pre-registered measurement produced.

---

## 7. Code and Data Availability

All code, pre-registration documents, batch outputs, per-run CSV data, and paper drafts referenced in this work are available in the public repository at github.com/RancidShack/developmental-agent. The v0.10 pre-registration document (commit on the public repository before any v0.10 code was written) is timestamped 23 April 2026. The v0.10 implementation, batch runner, and 360-run data outputs are timestamped 23 April 2026. The v0.9 architecture used as the comparison condition in this paper is the version published in Baker (2026c) and present in the same repository.

Per-run data from all 360 runs is available as `run_data_v0_10.csv` in the repository, alongside the meta-report `meta_report_v0_10.txt` from which the aggregate findings in this paper are derived. The single-run probe outputs at HAZARD_COST = 1.0 are available as `self_report_v0_10_c1.0.txt` and `run_output_v0_10_c1.0.png`.

---

## 8. References

Baker, N.P.M. (2026a) 'Staged Development in a Small Artificial Learner: Architectural Conditions for Rule Adherence, Focused Autonomy, and Biographical Individuation', OSF Preprint, v1.0, 21 April 2026.

Baker, N.P.M. (2026b) 'The Childhood AI Never Had: Twelve Iterations of a Computational Developmental Learner', preprint in preparation for resubmission, v1.0, 21 April 2026.

Baker, N.P.M. (2026c) 'Learning Without the Wall: Decomposing Rule Adherence in a Small Artificial Learner into Pre-Wired Aversion and Cost-Based Experience', preprint v0.1, 22 April 2026.

Baker, N.P.M. (2026d) 'v0.10 Pre-Registration: Experience-Driven Persistent Threat Representation', GitHub repository, github.com/RancidShack/developmental-agent, 23 April 2026.

Baker, N.P.M. (2026e) 'Experience-Driven Attractor Depletion and Persistent Mastery Representation in a Small Artificial Learner', preprint in preparation, v0.11 series, 24-25 April 2026.

---

## 9. Acknowledgements

This work was conducted in pair-programming collaboration with Anthropic's Claude (Anthropic PBC). Anthropic had no role in research design, analysis, interpretation, or decision to publish. The author has no financial relationship with Anthropic beyond standard paid-subscription access to Claude during the work.

The author is the founder of Synapstak Ltd, a consultancy engaged in learning strategy and capability architecture work. The computational research reported here was conducted independently of commercial activity and received no external funding. The author is the originator of Fluid Learning Architecture (FLA), a UK-registered framework for human learning systems referenced in adjacent work but not directly invoked in this paper. The treatment of FLA principles in the broader programme is bounded; the computational findings reported here are claimed on their own architectural terms, with FLA serving as a process scaffold for experimental design rather than as the framework being instantiated.

No human participant data were collected. No external parties had access to drafts of this paper prior to its preprint posting. The research was conducted on personal hardware without institutional affiliation or external review prior to submission.
