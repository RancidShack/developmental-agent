# v1.15 Pre-Registration: Amended Record

**Author:** Nicholas P M Baker, Synapstak Ltd
**Original pre-registration date:** 8 May 2026
**Amendment date:** 8 May 2026
**Amendment number:** 1 of 3
**Status:** Formally amended before v1.15 paper submission
**Repository:** github.com/RancidShack/developmental-agent

---

## Amendment statement

This document formally amends the v1.15 pre-registration committed on 8 May 2026. The amendment is made before the v1.15 paper is written and submitted. It is not a post-hoc revision of results; it is an honest account of the deviation between the pre-registered developmental version map and the iteration as built and run.

The amendment is registered under the programme's honesty constraint (Category Φ). An iteration that does not answer its stated developmental question must say so. The v1.15 results stand as valid. They do not answer the primary developmental question on the version map.

---

## 1. The stated developmental question

The developmental version map (Path\_to\_Robotic\_AI\_SICC\_v0\_9.docx, §8) states the primary question for v1.15 as:

> Does witnessed navigation inform an open prediction, and does social observation shorten the developmental arc?

The key capabilities required to answer this question were specified as:

- Agent B observes Agent A approach att\_blue while Agent B holds an open prediction for haz\_blue
- Socially corroborated schema state — distinct from predicted, confirmed, and unresolvable — firing on witnessed navigation
- Q6 statement: prediction written at step N, social observation at step M, location known, own mastery still required
- Agent B's arc measurably shorter than the naive v1.14 baseline
- Being\_observed record in Agent A's substrate
- Inter-agent convergence records

---

## 2. What was actually built

The v1.15 batch as built and run introduced two V110Agents in a single shared V113World instance. Agents were cognitively independent (separate Q-tables, mastery\_flag, observers). The world's object\_type and knowledge\_unlocked dicts were shared, producing the designed shared-benefit case (one agent's HAZARD→KNOWLEDGE transformation visible to the other). The three-phase v1.14 arc (ENV1 → ENV2 → return ENV1) ran for both agents simultaneously with step alternation.

**What was absent:**

- Inter-agent perception: agents were invisible to each other. Agent B could not detect Agent A's position.
- Social observation mechanism: no detection of Agent A approaching att\_blue while Agent B held an open prediction.
- Socially corroborated schema state: not implemented.
- Q6 statement generator: not implemented.
- Being\_observed record: not implemented.
- ZPD measurement: not computed.

The primary developmental question was not answered. The iteration answered a different question.

---

## 3. What was found

The v1.15 batch of 40 runs (80 agent-runs) produced four valid findings, none of which were the stated primary finding.

**Finding 1: Developmental individuation holds under shared-environment conditions.**
38 of 40 runs produced both\_arc\_complete = True. In all 38 completing runs, arc\_total\_steps\_delta > 0. Two agents in the same world, at the same time, with the same architectural endowment, always completed the arc at different times. The range of deltas was 563 to 654,155 steps (mean approximately 150,820). This is Category γ: developmental individuation is intrinsic to the cognitive architecture, not a product of environmental variation.

**Finding 2: The shared-benefit case is architecturally real and correctly handled.**
The haz\_blue\_shared\_benefit flag detected cases where Agent A's transformation of haz\_blue preceded Agent B's first contact in return ENV1. These cases are reported as environmental modification events, not social learning. The distinction between environmental modification and witnessed navigation is precisely what v1.15.1 is designed to test.

**Finding 3: Shared environment does not split arc\_complete eligibility.**
In every run where at least one agent completed, both completed. The two non-completing runs (runs 8 and 15) saw neither agent complete. The conditions that make arc\_complete possible are jointly sufficient for both agents.

**Finding 4: Category α preserved at 80 agent-runs.**
Zero hallucinations across 61,065 statements. The architecture scales to two simultaneous agents without integrity failure.

---

## 4. What the deviation established

The v1.15 run establishes the shared-environment foundation on which the correct v1.15.1 implementation depends. The two-agent phase runner, the AgentCtx cognitive independence architecture, the shared world mutation propagation, and the CRITICAL INVARIANT carry across both agents are all validated. v1.15.1 inherits this foundation and adds the social observation layer.

The individuation finding is not a consolation finding. It is a genuine advance: it eliminates the confound present in v1.14 (where individuation might have been attributed to environmental variation rather than agent biography) and confirms the stronger claim. But it is not the finding the version map was targeting.

---

## 5. Formal amendment to pre-registered categories

**Category β (cognitive independence):** Confirmed. Each agent maintained an independent cognitive state throughout all three phases.

**Category γ (developmental individuation under shared environment):** Confirmed. arc\_total\_steps\_delta > 0 in 38/38 completing runs. Standard deviation clearly exceeds the pre-registered threshold of 50,000. Component 2 (first\_transformer distribution) was not confirmed from data due to file access constraints; this will be reported in the v1.15 paper from repository data.

**Category δ (shared benefit honestly reported):** Confirmed architecturally. Exact count of shared\_benefit cases not confirmed from data due to file access constraints; reported from repository data in v1.15 paper.

**Category Φ (honesty constraint):** This amendment is the Category Φ entry for v1.15. The iteration did not answer its stated developmental question. The deviation is registered before paper submission. v1.15.1 addresses it.

**Category Ω (architectural statement claim):** Partially confirmed. Developmental individuation persists under shared-environment conditions. The stronger claim — that witnessed navigation informs an open prediction and shortens the developmental arc — is not confirmed because witnessing was not implemented.

---

## 6. v1.15.1

The correct implementation of the stated v1.15 developmental question is reserved for v1.15.1. v1.15.1 adds inter-agent perception, the socially corroborated schema state, the Q6 statement generator, the being\_observed record, and the ZPD measurement to the v1.15 shared-world architecture. It does not re-run the individuation study; it builds on it.

The v1.15.1 pre-registration is committed separately and supersedes the unanswered components of the original v1.15 pre-registration.

---

## 7. What the v1.15 paper will state

The v1.15 paper will:

- Report the four valid findings (individuation, shared benefit, joint eligibility, Category α) in full.
- Include an explicit section stating that the primary developmental question on the version map was not answered by this iteration, specifying which capabilities were absent and why.
- Report the deviation from the pre-registered version map as a Category Φ finding.
- State that v1.15.1 implements the correct specification and supersedes the unanswered components.
- Not claim findings the iteration did not produce.

---

**Amendment committed:** github.com/RancidShack/developmental-agent, 8 May 2026, before v1.15 paper submission.
