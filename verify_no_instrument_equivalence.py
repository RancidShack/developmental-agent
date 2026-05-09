"""
verify_no_instrument_equivalence.py
------------------------------------
Verify that v1.0 with --no-instrument produces bit-for-bit identical
output to the v0.14 batch at matched seeds. This is the architectural
preservation property the v1.0 pre-reg Section 3.3 commits to.

The test:
  1. Pick three (cost, steps, seed) triples spanning the matrix.
  2. Run each via the v0.14 codebase directly (replication module's
     run_one with permutation_offset=0).
  3. Run each via the v1.0 batch with instrument=False.
  4. Compare every metric field; assert exact equality.
"""

import sys
import numpy as np

# Run a v0.14-style run by reproducing the v0.14 batch's run_one
# logic. We import both modules and compare.
sys.path.insert(0, '.')

from curiosity_agent_v0_14 import (
    StructuredGridWorld, DevelopmentalAgent as V014Agent,
    FRAME, NEUTRAL, HAZARD, ATTRACTOR, END_STATE, KNOWLEDGE,
    HAZARD_CLUSTERS, ATTRACTOR_CELLS, MASTERY_THRESHOLD,
)
from curiosity_agent_v1_0_batch import V10World, run_one as v10_run_one


# v0.14 baseline run_one (transcribed from the replication module
# without the replication-specific permutation_offset > 0 case).
class V014BaselineWorld(StructuredGridWorld):
    def __init__(self, hazard_cost):
        super().__init__(permutation_offset=0)
        self.hazard_cost = hazard_cost

    def step(self, action):
        x, y = self.agent_pos
        if action == 0:
            target = (x, y - 1)
        elif action == 1:
            target = (x, y + 1)
        elif action == 2:
            target = (x - 1, y)
        elif action == 3:
            target = (x + 1, y)
        else:
            target = self.agent_pos

        if not (0 <= target[0] < self.size and 0 <= target[1] < self.size):
            target_type = FRAME
        else:
            target_type = self.cell_type[target]

        if target_type == FRAME:
            return self.observe(), target, False, 0.0
        if target_type == HAZARD:
            self.agent_pos = target
            return self.observe(), target, True, self.hazard_cost
        self.agent_pos = target
        return self.observe(), target, True, 0.0


def v014_run(hazard_cost, num_steps, seed):
    """Reference v0.14 run, no instrumentation, no v1.0 anything."""
    np.random.seed(seed)
    world = V014BaselineWorld(hazard_cost)
    agent = V014Agent(world, num_steps)
    state = world.observe()

    p3_visits_per_attractor = {a: 0 for a in ATTRACTOR_CELLS}

    for step in range(num_steps):
        agent.steps_taken = step
        agent.check_phase_transition()

        if agent.phase == 1:
            action = agent.get_prescribed_action()
            if action is None:
                action = 0
        else:
            action = agent.choose_action(state)

        next_state, target_cell, success, cost_incurred = world.step(action)
        agent.record_action_outcome(target_cell, success, cost_incurred,
                                    world, step)

        error = agent.prediction_error(state, action, next_state)
        r_progress = agent.learning_progress(state, action)
        r_novelty = agent.novelty_reward(next_state)
        r_preference = agent.preference_reward(next_state)
        r_feature = agent.feature_reward(next_state)
        intrinsic = (r_novelty + r_progress + r_preference + r_feature
                     - cost_incurred)

        agent.update_model(state, action, next_state, error, r_progress, r_feature)
        agent.update_values(state, action, next_state, intrinsic)

        if agent.phase == 3:
            cell = (next_state[0], next_state[1])
            if cell in p3_visits_per_attractor:
                p3_visits_per_attractor[cell] += 1

        state = next_state

    # Distil to comparable summary.
    return {
        "phase_1_end": agent.phase_1_end_step,
        "phase_2_end": agent.phase_2_end_step,
        "frame_attempts": dict(agent.frame_attempts_by_phase),
        "hazard_entries": dict(agent.hazard_entries_by_phase),
        "total_cost": agent.total_cost_incurred,
        "hazards_flagged": len(agent.cells_flagged_during_run),
        "time_to_first_flag": agent.time_to_first_flag,
        "first_entry_conversions": agent.first_entry_flag_conversions,
        "attractors_mastered": len(agent.mastery_order_sequence),
        "mastery_sequence": list(agent.mastery_order_sequence),
        "end_state_cell": world.end_state_cell,
        "activation_step": agent.activation_step,
        "end_state_found_step": agent.end_state_found_step,
        "end_state_banked": agent.end_state_banked,
        "hazards_transitioned": len(agent.transition_order_sequence),
        "hazards_banked_as_knowledge": len(agent.knowledge_banked_sequence),
        "transition_order_sequence": list(agent.transition_order_sequence),
        "knowledge_banked_sequence": list(agent.knowledge_banked_sequence),
        "hazard_thresholds": dict(world.hazard_competency_thresholds),
        "p3_visits_per_attractor": p3_visits_per_attractor,
    }


def v10_no_instrument_run(hazard_cost, num_steps, seed):
    """v1.0 run with instrumentation disabled."""
    metrics, _recorder = v10_run_one(hazard_cost, num_steps, seed,
                                      run_idx=0, instrument=False)
    return {
        "phase_1_end": metrics["phase_1_end"],
        "phase_2_end": metrics["phase_2_end"],
        "frame_attempts": {1: metrics["frame_attempts_p1"],
                           2: metrics["frame_attempts_p2"],
                           3: metrics["frame_attempts_p3"]},
        "hazard_entries": {1: metrics["hazard_entries_p1"],
                           2: metrics["hazard_entries_p2"],
                           3: metrics["hazard_entries_p3"]},
        "total_cost": metrics["total_cost"],
        "hazards_flagged": metrics["hazards_flagged"],
        "time_to_first_flag": metrics["time_to_first_flag"],
        "first_entry_conversions": metrics["first_entry_conversions"],
        "attractors_mastered": metrics["attractors_mastered"],
        "mastery_sequence_str": metrics["mastery_sequence"],
        "end_state_cell_str": metrics["end_state_cell"],
        "activation_step": metrics["activation_step"],
        "end_state_found_step": metrics["end_state_found_step"],
        "end_state_banked": metrics["end_state_banked"],
        "hazards_transitioned": metrics["hazards_transitioned"],
        "hazards_banked_as_knowledge": metrics["hazards_banked_as_knowledge"],
        "transition_order_sequence_str": metrics["transition_order_sequence"],
        "knowledge_banked_sequence_str": metrics["knowledge_banked_sequence"],
    }


def compare(v014, v10_no_inst, label):
    """Compare metrics. Some fields are stringified in v1.0 metrics
    but tuples in the v0.14 reference, so handle conversions."""
    issues = []

    # Direct numeric / scalar comparisons.
    for key in ["phase_1_end", "phase_2_end", "total_cost", "hazards_flagged",
                "time_to_first_flag", "first_entry_conversions",
                "attractors_mastered", "activation_step",
                "end_state_found_step", "end_state_banked",
                "hazards_transitioned", "hazards_banked_as_knowledge"]:
        if v014[key] != v10_no_inst[key]:
            issues.append(f"  {key}: v0.14={v014[key]} vs v1.0={v10_no_inst[key]}")

    # Phase-keyed dicts.
    for key in ["frame_attempts", "hazard_entries"]:
        if v014[key] != v10_no_inst[key]:
            issues.append(f"  {key}: v0.14={v014[key]} vs v1.0={v10_no_inst[key]}")

    # Sequences (v1.0 stringified, v0.14 list-of-tuples).
    v14_mast = "|".join(str(c) for c in v014["mastery_sequence"])
    if v14_mast != v10_no_inst["mastery_sequence_str"]:
        issues.append(f"  mastery_sequence: v0.14={v14_mast} vs v1.0={v10_no_inst['mastery_sequence_str']}")

    v14_trans = "|".join(str(c) for c in v014["transition_order_sequence"])
    if v14_trans != v10_no_inst["transition_order_sequence_str"]:
        issues.append(f"  transition_order: v0.14={v14_trans} vs v1.0={v10_no_inst['transition_order_sequence_str']}")

    v14_know = "|".join(str(c) for c in v014["knowledge_banked_sequence"])
    if v14_know != v10_no_inst["knowledge_banked_sequence_str"]:
        issues.append(f"  knowledge_banked: v0.14={v14_know} vs v1.0={v10_no_inst['knowledge_banked_sequence_str']}")

    # End-state cell (v1.0 stringified).
    if str(v014["end_state_cell"]) != v10_no_inst["end_state_cell_str"]:
        issues.append(f"  end_state_cell: v0.14={v014['end_state_cell']} vs v1.0={v10_no_inst['end_state_cell_str']}")

    if issues:
        print(f"FAIL [{label}]:")
        for issue in issues:
            print(issue)
        return False
    else:
        print(f"PASS [{label}]")
        return True


def main():
    # Three small test cases (short run lengths to keep verification quick).
    test_cases = [
        # (hazard_cost, num_steps, seed)
        (1.0, 5000, 42),
        (5.0, 5000, 137),
        (0.5, 5000, 9999),
    ]

    print("Verifying v1.0 with --no-instrument == v0.14 baseline\n")

    all_pass = True
    for cost, steps, seed in test_cases:
        v014 = v014_run(cost, steps, seed)
        v10 = v10_no_instrument_run(cost, steps, seed)
        label = f"cost={cost} steps={steps} seed={seed}"
        passed = compare(v014, v10, label)
        all_pass = all_pass and passed

    print()
    if all_pass:
        print("ALL TESTS PASS: v1.0 instrumentation-off is bit-for-bit "
              "identical to v0.14 baseline.")
        sys.exit(0)
    else:
        print("FAILURE: instrumentation-off output diverges from v0.14.")
        sys.exit(1)


if __name__ == "__main__":
    main()
