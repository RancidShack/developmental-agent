# LEARNING WITHOUT THE WALL: Decomposing Rule Adherence in a Small Artificial Learner into Pre-Wired Aversion and Cost-Based Experience

Nicholas P M Baker
Synapstak Ltd,
United Kingdom
ORCID: 0009-0009-7181-8655

Version: v0.1 (Preprint) Date: 22 April 2026

---

## ABSTRACT

A preceding paper (Baker, 2026a) demonstrated that a small tabular agent organised around staged developmental structure and primitive perceptual priors produces five behavioural signatures associated with developmental learning: absolute rule adherence, focused autonomy, feature-aligned preference formation, a specialist-generalist trade-off, and full biographical individuation. The rule adherence finding was a ceiling case: rules were implemented as primitive perceptual penalties against impassable cells, and the architectural wall was never challenged by the agent's learning dynamics. The preceding paper predicted, on architectural grounds, that rules that must be learned rather than architecturally enforced would hold less reliably under preference-reinforcement pressure. The present paper tests this prediction by decomposing the rule-enforcement mechanism into its constituent parts. We find that the v0.8 rule adherence mechanism combined two architecturally distinct elements that had been treated as one: the world's refusal to permit hazard entry (architectural impassability), and the agent's pre-wired perceptual bias against hazard-adjacent actions (aversion scaffolding). Across a pre-registered batch of 140 runs spanning six cost levels and four hazard-mechanism modes, we find: (i) full survival of avoidance behaviour across the entire cost range when the architectural wall is removed but pre-wired aversion is retained, establishing that the bias alone is sufficient to produce v0.8's zero-violation result; (ii) partial and transient learning of avoidance when both wall and bias are removed and only experienced cost remains, with 29 of 60 agents achieving Phase 3 cleanness at the v0.8 run length; and (iii) that this partial learning does not stabilise under extended run length but degrades non-monotonically, with Phase 3 cleanness improving at 80,000 steps (43 of 60) then regressing at 160,000 steps (34 of 60). We interpret the non-monotonic degradation as a consequence of the architectural storage structure: cost-based learning produces distributed per-state-action Q-value adjustments that are bounded in their accumulated magnitude, while the preference drive that dominates Phase 3 action selection accumulates without bound across time. In the absence of a persistent representational structure for learned hazard knowledge, the preference accumulator wins at extended horizons. The findings support a stronger formulation of v0.8's architectural claims — the wall was redundant because the bias was sufficient, not because rule adherence is easy — and identify a specific architectural gap (the lack of persistent representation for learned rules) that subsequent work will address. The broader implication is that in this architecture, learned rules and pre-wired rules are not functionally equivalent, and stability of learned rules against preference dynamics requires architectural machinery that v0.8 did not need to demonstrate its findings but that any learned-rule version of the architecture must include.

Keywords: developmental robotics; rule internalisation; intrinsic motivation; cost-based learning; representational persistence; preference dynamics; pre-registered replication; Fluid Learning Architecture.

---

## 1. INTRODUCTION

A preceding paper in this research programme (Baker, 2026a) reported five pre-registered findings from a small tabular artificial learner: rule adherence that held absolutely across all tested pressures, focused autonomous behaviour that emerged reliably from identical starting conditions, preference formation that grounded itself in environmentally marked cells, a specialist-versus-generalist trade-off that emerged as a degree of freedom the architecture permitted, and full individuation across a batch of ten runs from identical starting conditions. The findings supported a specific architectural claim: that staged developmental structure, primitive perceptual priors, and extrinsic value signals are jointly sufficient to produce the behavioural signatures associated with developmental learning in a small, fully reproducible tabular system.

The first of those findings — rule adherence — was explicitly framed as a ceiling case. Rules in the v0.8 architecture were implemented as impassable cells. The agent could not enter hazard or frame cells; the world refused to permit the transition. Pre-wired aversion biases, operating as large negative Q-value penalties on any action targeting frame or hazard cells, ensured that the agent never attempted entry in the first place. The two mechanisms were wired in series: the bias kept the agent away, and the wall ensured that if the bias ever failed, entry would still not occur. v0.8's batch produced zero hazard-directed action attempts across 200,000 cumulative actions. The rule held, as the paper reported, because it was architecturally enforced rather than learned.

The preceding paper's Discussion section (Baker, 2026a, §6.4) named this finding as a ceiling case and articulated the specific question it left open: *whether learned rules — rules that the agent must acquire from experience, as in a cost-based version of the hazard mechanism — would similarly hold against the preference-reinforcement dynamics that operate during Phase 3*. The paper offered a prior: *we have specific reasons to expect this test to be harder for the architecture, because learned rules must hold against the same pressures that reinforce preferences, and the architectural conditions under which they would hold are not trivial*. The extension was specified but not examined.

The present paper examines that extension. In doing so, it addresses not one question but three, because examination of the v0.8 architecture's hazard-handling mechanism has revealed that what v0.8 treated as a single mechanism is in fact two mechanisms that had been architecturally conflated. The architectural wall (world refuses to permit entry) and the pre-wired aversion bias (Q-value penalty on hazard-directed actions) operated together in v0.8, and the zero-violation finding could not distinguish their individual contributions. A test of whether cost-based learning can substitute for architectural enforcement must therefore also separate the contributions of wall and bias, because simply removing the wall while retaining the bias is a different experiment from removing both together.

The paper's three findings correspond to this decomposition. First, the pre-wired aversion bias alone is sufficient to sustain complete hazard avoidance when the architectural wall is removed, across two orders of magnitude of cost pressure. v0.8's zero-violation result is reproduced by bias alone; the wall was redundant at every cost value tested. Second, when both wall and aversion are removed and only experienced cost remains, the architecture produces partial learning: within v0.8's standard run length of 20,000 steps, 29 of 60 agents achieve complete Phase 3 hazard avoidance while 31 do not. Third, and unexpectedly, this partial learning does not stabilise under extended run length. Across three run lengths — 20,000, 80,000, and 160,000 steps — Phase 3 cleanness follows a non-monotonic trajectory: 29/60 at the baseline, improving to 43/60 at 4× run length, then regressing to 34/60 at 8× run length. The extended-time regression is itself informative about the architecture: we interpret it as a consequence of the asymmetry between bounded cost-based Q-value adjustments and the unbounded preference accumulator that dominates Phase 3 action selection.

The broader implication is that pre-wired rules and learned rules are not architecturally equivalent in this system, and the architectural conditions under which learned rules hold stably at extended run lengths are not present in v0.8's architecture as specified. v0.8's prior that learned rules would be harder to sustain than pre-wired ones is supported in a specific way: not that learned rules fail absolutely, but that they exhibit transient stability whose window depends on the interaction between cost accumulation and preference accumulation over time. Without a persistent representational structure for learned hazard knowledge — a structure that would resist erosion by preference dynamics in the way that pre-wired aversion does — cost-based rule learning in this architecture is inherently unstable at sufficient time horizons.

The paper's contribution is therefore threefold. First, it decomposes v0.8's rule-adherence finding into its constituent mechanisms, clarifying that the wall was redundant and the bias was doing the architectural work that v0.8's framing attributed jointly to both. Second, it demonstrates that cost-based learning can partially substitute for the bias but with a fundamentally different temporal profile — transient rather than absolute, variable rather than uniform, and subject to degradation at extended horizons. Third, it identifies a specific architectural gap — the absence of persistent representation for learned rules — as the locus at which subsequent work must intervene if learned-rule versions of the architecture are to produce the stable behaviour v0.8 demonstrated with pre-wired rules.

The work is positioned as the second contribution in the research programme opened by Baker (2026a), with the extensions specified in that paper's Discussion being addressed incrementally. Subsequent papers will examine whether a persistent hazard representation, implemented as an architectural addition to the v0.9 design reported here, produces the stable long-horizon avoidance that v0.9's architecture alone does not sustain.

The paper proceeds as follows. Section 2 reviews the specific literature relevant to the decomposition and the stability question, drawing on preference-based reinforcement learning, the architectural-vs-learned-rules distinction in constitutional AI methods, and the representational-persistence literature that will become relevant for interpreting the long-horizon degradation finding. Section 3 describes the architectural modifications made to v0.8 to enable the decomposition — specifically, the four-valued `hazard_mode` flag that allows independent manipulation of the wall and the bias — referencing Baker (2026a) for the full architectural specification that v0.9 inherits unchanged. Section 4 presents the pre-registered methodology, including the amendment history that accompanied the study: the original pre-registration, its first amendment following review of the v0.8 code (which revealed the wall-bias decomposition), and its second amendment following the initial batch (which added the extended-run-length investigation). Section 5 reports the findings from the three batches: the initial 140-run batch and the 70-run extended-run-length batches at 80,000 and 160,000 steps. Section 6 discusses what the findings support, what they do not support, and their implications for the architectural programme. Section 7 concludes with brief remarks on the extensions the findings motivate.

Two methodological notes before proceeding. First, the research reported here was conducted with three successive pre-registrations, each committed to a public repository before the corresponding batch was executed. The amendments were necessitated by discoveries made during implementation (the wall-bias decomposition) and by findings from the initial batch (the extended-run-length question). The amendments were committed with full retention of the original documents and with explicit reasoning about what each amendment changed and why. The research record is therefore transparent with respect to how the experimental design evolved in response to what was learned at each stage. Second, the computational findings reported here were produced in a single work session on a personal laptop, with total compute time across all three batches of approximately nine minutes. The small scale of the computation is relevant to the methodological argument the programme advances: that the architectural questions of interest are not, in this case, questions that require large compute to address.

---

## 2. RELATED WORK

The present paper inherits the five traditions situated in Baker (2026a) — developmental robotics, intrinsic motivation in reinforcement learning, core knowledge and primitive priors, prepared environments, and Fluid Learning Architecture — and does not re-situate them here. Three further literatures become relevant specifically for the questions v0.9 addresses: preference-based reinforcement learning, the distinction between architectural and learned rules in recent work on AI alignment, and the representational-persistence problem in distributed learning systems. We summarise each briefly.

### 2.1 Preference-based and cost-based reinforcement learning

A substantial recent literature has examined mechanisms by which reinforcement learning systems can internalise preferences or costs from human feedback, constitutional principles, or environmental signals. Reinforcement learning from human feedback (Christiano et al., 2017; Ouyang et al., 2022) operates by training reward models on pairwise preference judgements and using those reward models to shape policy behaviour. Constitutional methods (Bai et al., 2022) extend this by having the system critique its own outputs against a set of pre-specified principles and incorporating those critiques into the training signal. Preference-based exploration methods (Wilson, Fern and Tadepalli, 2012) integrate human or environmental preference signals directly into the exploration policy rather than the reward model. What these approaches share is the premise that learned preferences or costs can produce stable behavioural modifications in the trained system.

The present work bears on this premise in a specific way. Our cost-based hazard mechanism is a minimal computational analogue of preference-reinforcement dynamics: the agent receives a scalar cost for specific actions, and the cost accumulates into the learned value function through standard temporal-difference updates. The question of whether such cost-based signals produce stable behavioural modifications — and in particular, whether they produce modifications that hold against competing signals that also accumulate during the agent's life — is the question v0.9 addresses. The finding that cost-based learning in our architecture produces transient rather than stable avoidance, with non-monotonic degradation at extended time horizons, has implications for how stability claims should be calibrated in the preference-based RL literature. It does not demonstrate that stability is unachievable; it demonstrates that stability is not a default property of cost-based learning and that the architectural conditions for stability must be separately specified.

### 2.2 Architectural versus learned rules in alignment

A parallel and more recent literature has examined the distinction between rules that are architecturally enforced (the system cannot, by construction, violate them) and rules that are learned (the system has been trained to avoid violating them but could, in principle, do so). The distinction has become methodologically sharp in work on constitutional AI (Bai et al., 2022), in Anthropic's public writing on model behaviour (Askell et al., 2021), and in discussions of AI safety that distinguish between "hard" constraints implemented at the architectural level and "soft" constraints learned during training.

The v0.8 paper (Baker, 2026a) implicitly treated its rule-adherence finding as establishing a ceiling case for architectural enforcement. What the present paper clarifies is that v0.8's ceiling case combined two architecturally distinct forms of enforcement: the world's refusal to permit hazard entry (the wall) and the agent's pre-wired perceptual penalty on hazard-adjacent actions (the bias). Both are "hard" constraints in the sense that neither is learned from experience. They differ in where in the agent-environment system they operate: the wall operates in the environment (cells are impassable regardless of agent behaviour), the bias operates in the agent (certain actions carry fixed negative value regardless of learned Q-values). The distinction matters because removing one without the other produces a different experimental condition than removing both. The present paper makes the distinction operational and examines its consequences, contributing empirical clarity to a distinction that has been made conceptually in the alignment literature but not, to our knowledge, examined through direct manipulation in a developmental architecture.

### 2.3 Representational persistence and catastrophic forgetting

A third literature relevant to v0.9's findings concerns the persistence of learned representations over time in systems that continue to learn. The catastrophic forgetting literature (McCloskey and Cohen, 1989; French, 1999; Kirkpatrick et al., 2017) has documented that neural networks trained sequentially on different tasks tend to overwrite earlier learning with later learning unless specific architectural mechanisms — elastic weight consolidation, synaptic intelligence, memory replay — are included to protect the earlier representations. The problem is typically framed as one of interference between successive tasks in a training sequence.

The finding we report in v0.9 is not catastrophic forgetting in the usual sense — the v0.9 agent is not trained sequentially on different tasks; it operates continuously in a single environment. But the underlying architectural issue is related. Learned representations in the v0.9 architecture are stored as distributed adjustments to a Q-value table, with each adjustment bounded in magnitude by the learning rate and the number of times the agent experiences the associated state-action pair. The preference accumulator, by contrast, is unbounded: it increases monotonically with visit frequency and has no mechanism that caps or decays its accumulated mass. When these two representational structures operate in competition during Phase 3 action selection, the bounded structure (Q-values embodying cost-based learning) can be overwhelmed by the unbounded structure (preference accumulation) at sufficient time horizons. This is not forgetting; the Q-value adjustments are still present. But their behavioural consequence is erased by the preference dynamics that continue to grow around them.

The literature on catastrophic forgetting suggests that mechanisms for representational persistence are often not default features of learning systems but must be architecturally added. Our finding points in the same direction: that stability of learned rules in a developmental architecture requires mechanisms beyond distributed value updates, and that the appropriate locus for such mechanisms is an open design question that v0.10 will begin to address.


---

## 3. ARCHITECTURE

The v0.9 architecture inherits v0.8 unchanged except for the hazard-handling mechanism. Baker (2026a) specifies the environment (20×20 grid with frame, neutral, hazard, and attractor cells), the three-phase developmental schedule (prescribed acquisition, drive-based integration, preference-based autonomy), the drive composition at each phase, the primitive perceptual priors, the learning parameters (learning rate 0.1, discount factor 0.9, epsilon 0.1), and all other architectural components. We refer the reader to that specification for the full description and summarise here only the modification that v0.9 introduces.

### 3.1 The `hazard_mode` decomposition

In v0.8, hazard avoidance was produced by three interacting architectural elements operating in series. First, the environment's transition function refused to permit entry into cells of type HAZARD: any action targeting such a cell returned the agent to its prior position with a `success=False` outcome. Second, the agent's primitive bias function applied a penalty of −5.0 to Q-values for actions targeting HAZARD-adjacent cells, operating on perception of cell type rather than on learned experience. Third, the agent's epsilon-greedy exploration excluded actions whose primitive bias was strongly negative, ensuring that even random exploration did not attempt hazard-directed actions.

v0.9 introduces a single configuration flag, `hazard_mode`, that governs the behaviour of the first and second elements. The flag takes one of four values, corresponding to the four combinations of wall-present-or-absent and aversion-present-or-absent:

- `impassable`: reproduces v0.8's behaviour exactly. Wall active, aversion active, epsilon filter active. HAZARD cells are impassable; the agent is biased against approaching them.
- `impassable_no_aversion`: wall active, aversion inactive, epsilon filter inactive for HAZARD (frame aversion retained). HAZARD cells remain impassable but the agent has no pre-wired reason to avoid approaching them.
- `cost`: wall inactive, aversion active, epsilon filter active. HAZARD cells are passable at a scalar cost applied to the intrinsic reward on entry; the agent retains the pre-wired bias against entry.
- `cost_no_aversion`: wall inactive, aversion inactive, epsilon filter inactive for HAZARD. HAZARD cells are passable at cost; the agent has no pre-wired bias and must learn avoidance from experienced cost if it is to develop at all.

The distinction between FRAME and HAZARD cells is preserved across all four modes. Frames remain impassable and retain their aversion bias in every mode, on the principle that frames are an ontological boundary of the world rather than a normative rule the agent might in principle learn. The `hazard_mode` manipulation is specific to HAZARD cells.

### 3.2 The cost mechanism

When `hazard_mode` is `cost` or `cost_no_aversion`, entry into a HAZARD cell produces a scalar cost applied to the intrinsic reward at that step. The cost is subtracted from the sum of drive-based rewards (novelty, learning progress, preference, feature) before the intrinsic value is passed to the Q-value update:

  intrinsic = r_novelty + r_progress + r_preference + r_feature − c

where c is the configured hazard cost when the agent enters a HAZARD cell on that step, and zero otherwise. The cost is local — felt only on contact — and is not signalled in advance through proximity gradients or perceptual cues. The agent has no warning before entry; it learns the cost by paying it.

The cost is not written to the cell preference accumulator. Cell preference in v0.8 accumulates learning-progress reward and feature reward per cell visit; the hazard cost does not enter this accumulation. This decision preserves the single-variable discipline of the v0.9 manipulation: only the Q-value signal and the action selection pipeline are affected by the cost mechanism, not the preference representation. An architectural variant that also propagated cost into cell preferences would constitute a different experiment and is reserved for future work.

### 3.3 Cost-level range

Six cost levels are pre-registered, log-spaced to give good threshold resolution across the range of plausible outcomes:

  0.1, 0.5, 1.0, 2.0, 5.0, 10.0

The range spans two orders of magnitude. The lower end (0.1) represents a cost signal small relative to the v0.8 primitive aversion penalty of −5.0; the upper end (10.0) exceeds the aversion penalty by a factor of two. If the aversion bias and the cost signal are commensurate at all, the threshold at which bias-alone-avoidance breaks down under cost pressure should lie somewhere within this range. The log spacing gives equivalent resolution near any plausible threshold value without requiring a denser grid that would increase run counts without scientific benefit.

### 3.4 What the architecture does not add

v0.9 adds no machinery beyond the `hazard_mode` flag, the cost mechanism, and the per-run tracking of hazard entries (distinct from v0.8's tracking of blocked hazard-directed attempts, which under cost-based modes become zero because no attempts are blocked). The agent's representational structures — forward model, prediction-error windows, visit counts, cell preferences, Q-values — are unchanged from v0.8. The phase schedule is unchanged. The drive composition is unchanged. The primitive priors against FRAME cells are unchanged. The single manipulation is the hazard-handling mechanism, parameterised by mode.

This minimal modification is deliberate. The research question v0.9 addresses is specifically about the hazard mechanism, and introducing additional architectural changes would confound the interpretation of any behavioural differences observed. The finding that cost-based learning produces transient rather than absolute avoidance (Section 5) is attributable to the hazard mechanism alone, because nothing else in the architecture has changed.


---

## 4. METHODS

### 4.1 Pre-registration sequence

The research reported here was conducted under three successive pre-registration documents, each committed to the public repository before the corresponding batch was executed. The documents are retained unchanged in the repository; the amendment history is itself part of the methodological record.

The original pre-registration (Baker, 2026c) was committed at the outset of the v0.9 work, before any v0.9 code was written. It specified a single-batch experimental design examining whether rule-compliance in v0.8 was internalised through learning or enforced through architecture. The design manipulated cost as a single variable across six log-spaced levels with ten runs per level plus ten impassable controls, yielding a 70-run batch.

The first amendment (Baker, 2026d) was committed following review of the v0.8 source code, prior to writing any v0.9 implementation. The review revealed that hazard avoidance in v0.8 was produced by three interacting architectural elements (the wall, the aversion bias, the epsilon filter) rather than by a single mechanism, as the original pre-registration had assumed. A single-manipulation batch manipulating only one of these elements could not distinguish their individual contributions. The amendment accordingly restructured the study into two linked designs: Design A (remove the wall, retain the aversion bias and filter) and Design C (remove the wall, the bias, and the hazard-directed filter, retaining only frame handling). The amended design specified a 140-run batch covering both designs across six cost levels with matched controls for each.

The second amendment (Baker, 2026e) was committed following completion of the initial 140-run batch, prior to any extended-run-length computation. The initial batch's Design C finding — that 29 of 60 runs achieved Phase 3 hazard avoidance while 31 did not within the 20,000-step run length — raised the question of whether the partial-learning signature was an insufficient-time artefact or a structural property of the architecture. The amendment specified an extended-run-length investigation with a pre-specified decision tree: a Batch 1 at 80,000 steps (Design C only, 70 runs), followed conditionally by a Batch 2 at 160,000 steps (Design C only, 70 runs) if Batch 1's Phase 3 cleanness count fell within the pre-specified Category B range indicating plateau behaviour. The amendment committed to running Batch 2 in the same session as Batch 1 if the decision tree triggered it, and committed to reporting the Batch 1 category assignment before presenting Batch 2 results.

All three documents — the original pre-registration, the first amendment, and the second amendment — are retained in the public repository at the commit hashes referenced in the References section. The methodological discipline of committing each amendment before the corresponding computation, with explicit reasoning about what each amendment changed and why, is itself offered as part of the research record.

### 4.2 Single-run probes preceding the batch

Prior to executing the 140-run batch, four single-run probes were conducted at representative cost values in the `cost` mode (Design A experimental condition): 0.1, 1.0, 5.0, and 10.0. The probes served as verification that the `hazard_mode` code extension produced behaviourally sensible outputs before committing compute to the full batch. All four probes produced zero hazard entries across 20,000 steps, consistent with the Design A full-survival finding that the batch subsequently confirmed. An additional single-run probe at `cost_no_aversion` mode with cost 1.0 verified that the Design C mechanism produced non-zero hazard entries (confirming the implementation was working as intended) and showed a temporal pattern — entries in Phase 2, cleanness in Phase 3 — consistent with cost-based learning. The probes are not themselves experimental data; they are documented here as methodological context for the batch implementation.

### 4.3 Batch design

Three batches were executed, totalling 280 agent lives across all conditions.

The initial batch (140 runs, 20,000 steps each) covered four modes across two designs:

- Design A experimental: `cost` mode, 6 cost levels × 10 runs = 60 runs
- Design A control: `impassable` mode (reproducing v0.8 behaviour), 10 runs
- Design C experimental: `cost_no_aversion` mode, 6 cost levels × 10 runs = 60 runs
- Design C control: `impassable_no_aversion` mode, 10 runs

The extended-run-length Batch 1 (70 runs, 80,000 steps each) covered Design C only:

- Design C experimental: `cost_no_aversion` mode, 6 cost levels × 10 runs = 60 runs
- Design C control: `impassable_no_aversion` mode, 10 runs

Design A was excluded from the extended-run-length investigation because its full-survival result at 20,000 steps was informatively complete; extended run length adds no information to a zero-entry outcome.

The extended-run-length Batch 2 (70 runs, 160,000 steps each) was executed following Batch 1 under the decision tree specified in the second amendment. The rationale for its execution is documented in Section 5.3.

### 4.4 Metrics

All metrics from Baker (2026a) are retained unchanged: Phase 3 concentration, Phase 3 attractor ratio, mastery count, top-5 preferences on attractors, top-5 preferences near attractors, and individuation (distinct top attractors across the batch). Three additional metrics are introduced for v0.9:

- **Hazard entries by phase**: the count of actual entries into HAZARD cells during each of the three phases. In impassable modes this is always zero; in cost modes it is the primary measure of the agent's hazard-interaction behaviour.
- **Total cost incurred**: the sum of hazard costs paid across the run. A measure of the agent's total expenditure on hazard-based learning.
- **Rule violation by metric**: a run is classified as rule-violated under the pre-registered total-entries metric if it records three or more hazard entries across the full run, and as rule-violated under the Design-C-relevant Phase 3 metric if it records three or more hazard entries during Phase 3 specifically. Both metrics are reported in the results, on the recognition that Design A and Design C are asking structurally different questions: Design A asks whether any entries occur (and the answer is no), while Design C asks whether the agent has learned to avoid entries by Phase 3 (the period of preference-driven autonomy).

The distinction between the two rule-violation metrics is important for interpreting Design C. An agent under `cost_no_aversion` that makes substantial entries in Phase 2 (when it has no bias against hazards and no accumulated preference structure to direct it elsewhere) but stops entering by Phase 3 (when preference dominates and cost-based Q-value adjustments have accumulated) is exhibiting the learning signature the experimental condition was designed to reveal. Scoring such an agent as "rule-violated" under a total-entries metric that averages across phases conflates failure to learn with the Phase 2 exploration through which learning is produced. The Phase 3 metric isolates what is actually being tested in Design C.

### 4.5 Hardware and compute

All three batches were executed on a single personal laptop (2025-era Apple Silicon, MacBook M4, no external compute). The initial 140-run batch completed in approximately three minutes. The 80,000-step Design C batch completed in approximately two minutes. The 160,000-step Design C batch completed in approximately four minutes. Total compute across all 280 runs was under ten minutes. The small computational footprint is relevant to the methodological argument the research programme advances: that the architectural questions of interest can be addressed at scales many orders of magnitude smaller than those at which mainstream AI research operates.

