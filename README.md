# Developmental Agent

A small tabular artificial learner exploring architectural conditions for developmental behaviour.

This repository contains the code accompanying the research paper *Staged Development in a Small Artificial Learner: Architectural Conditions for Rule Adherence, Focused Autonomy, and Biographical Individuation* (Baker, 2026). The paper and its companion essay are forthcoming; a DOI and preprint link will be added to this README when they are available.

## What the project is

Across twelve architectural iterations, this project developed a small tabular agent whose behaviour in a structured grid environment exhibits the signatures we associate with developmental learning: rule adherence that holds under subsequent learning pressures, focused autonomous behaviour that emerges reliably, preference formation grounded in environmentally marked features, and biographical individuation across agents that begin from identical conditions.

The work is motivated by a question that mainstream artificial intelligence research has largely bracketed: whether the staged developmental structure characteristic of biological learners — exposure before evaluation, primitive perceptual priors, progressive internalisation of extrinsic value — is architecturally important for the kinds of learning we recognise as developmental, and whether it can be demonstrated in a system small enough that the mechanism is inspectable in closed form.

The final architecture (version 0.8) operates in a 20x20 grid with four cell types, staged drive activation across three developmental phases, primitive perceptual aversion and attraction, and preference accumulation that tracks both intrinsic learning progress and extrinsic feature reward. Across a pre-registered batch of ten independent agent lives, the architecture produces zero rule violations, Phase 3 attention concentration above 50x uniform in every run, feature-aligned preferences across all runs, and full individuation — every available attractor in the environment is chosen as the primary settled focus of at least one agent.

## Repository structure

- agents/ contains the final architecture (v0.8 and v0.8_batch).
- earlier_versions/ contains the twelve-iteration arc (v0.1 through v0.7.1).
- outputs/ is where generated files land when the code is run (empty at commit).
- requirements.txt lists Python dependencies.
- LICENSE (MIT) and this README complete the top level.

The agents/ directory contains the final architecture described in the paper. The earlier_versions/ directory contains the full twelve-iteration arc that preceded it, preserved for methodological transparency. Each intermediate version is a stable architectural state with specific findings; the arc is described in the companion essay (Baker, in prep.).

## Running the code

Requirements: Python 3.9 or later, NumPy, matplotlib.

Install dependencies:

    pip install -r requirements.txt

Run a single agent life:

    python agents/curiosity_agent_v0_8.py

This takes approximately 5 to 10 seconds on a standard laptop. Outputs are written to the outputs/ directory: a PNG file showing phase-wise heatmaps, coverage, drive signals, and mastery accumulation, and a text file with per-run metrics.

Run a batch of ten independent agent lives:

    python agents/curiosity_agent_v0_8_batch.py

This takes approximately 50 seconds. The batch report writes to meta_report_v0_8.txt in the outputs/ directory.

All agent behaviour is stochastic with respect to epsilon-greedy action selection, so successive runs will produce slightly different specific numbers, but the architectural findings are stable across the distribution. The paper's batch was run once on the released code; the same code produces a comparable distribution on re-run.

## Version arc

The final architecture emerged through twelve iterations. For readers interested in the methodological path:

- v0.1 to v0.3: Intrinsic motivation baselines (novelty, surprise, learning progress) in 10x10 environments.
- v0.4 to v0.4.1: Explicit scope and time horizons; coverage drives; discovery of the intention-action gap.
- v0.5 to v0.6: Reflection mechanisms; finding that reflection-shaped output can be architecturally cosmetic.
- v0.4.2 to v0.4.3: Phase-structured development through drive suppression (failed).
- v0.4.4: Prescribed Phase 1 traversal; focused autonomy emerges but lands on trajectory accidents rather than features.
- v0.7 to v0.7.1: Extrinsic feature drive; preference accumulation that tracks feature reward.
- v0.8: The 20x20 structured environment with four cell types, primitive priors, and the full developmental schedule. Findings reported in the paper.

The full narrative of this arc, including the findings from each iteration and the architectural reasoning that motivated each transition, appears in the companion essay (Baker, in prep.). This repository preserves the code for every stable version, permitting replication of any intermediate finding.

## Code provenance and authorship

The code was developed iteratively by the author in collaboration with Anthropic's Claude, used as a pair-programming assistant. Architectural decisions, interpretation of findings, and the overall research direction are the author's. Implementation details were developed in dialogue. The iterative development process itself, with each version responding to findings from its predecessor, is part of the methodological contribution and is documented in the companion essay.

## Citation

When citing this code, please cite the paper:

Baker, N.P.M. (2026) Staged Development in a Small Artificial Learner: Architectural Conditions for Rule Adherence, Focused Autonomy, and Biographical Individuation. Preprint / DOI to be inserted.

## Licence

MIT. See LICENSE for full terms.

## Contact

Nicholas P M Baker, Synapstak Ltd
Email: nicholas.baker@synapstak.com
ORCID: 0009-0009-7181-8655
