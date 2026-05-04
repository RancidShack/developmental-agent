"""
diagnose_pe_substrate.py
-------------------------
Runs one simulation and prints the full PE substrate record structure.
Run from the developmental-agent working directory:
    python3 diagnose_pe_substrate.py

Output tells us exactly what fields V15PredictionErrorObserver.get_substrate()
returns so the belief-revision observer can read them correctly.
"""

import numpy as np
import sys

from curiosity_agent_v1_7_world import V17World, NUM_ACTIONS
from v1_7_agent import V17Agent
from v1_5_prediction_error_observer import V15PredictionErrorObserver

# Use run 0 cost=1.0 seed from run_data_v1_9.csv — known to have 1 PE event
SEED     = 496635339
COST     = 1.0
N_STEPS  = 80_000

np.random.seed(SEED)
world = V17World(hazard_cost=COST, seed=SEED)
agent = V17Agent(world, total_steps=N_STEPS, num_actions=NUM_ACTIONS)
meta  = {"arch": "diag", "hazard_cost": COST, "num_steps": N_STEPS,
         "run_idx": 0, "seed": SEED}

pe_obs = V15PredictionErrorObserver(agent, world, meta)

observers = [pe_obs]
state = world.observe()
for step in range(N_STEPS):
    for obs in observers:
        obs.on_pre_action(step)
    action = agent.choose_action(state)
    obs_next, contact_oid, moved, cost = world.step(action)
    agent.record_action_outcome(
        contact_oid, moved or contact_oid is not None, cost, world, step
    )
    for obs in observers:
        obs.on_post_event(step)
    intrinsic = (
        agent.novelty_reward(state)
        + agent.preference_reward(state)
        + agent.feature_reward(state)
    )
    agent.update_values(state, action, obs_next, intrinsic)
    agent.update_model(state, action, obs_next)
    state = obs_next

for obs in observers:
    obs.on_run_end(N_STEPS)

print("=" * 60)
print("PE substrate diagnostic")
print(f"  yellow_pre_transition_entries: "
      f"{getattr(agent, 'pre_transition_hazard_entries', {})}")
print()

substrate = pe_obs.get_substrate()
print(f"get_substrate() type: {type(substrate)}")
print(f"get_substrate() length: {len(substrate) if hasattr(substrate, '__len__') else 'N/A'}")
print()

if isinstance(substrate, list):
    for i, rec in enumerate(substrate):
        print(f"Record {i}:")
        if isinstance(rec, dict):
            for k, v in rec.items():
                print(f"  {k}: {v!r}")
        else:
            print(f"  (non-dict) type={type(rec)}, value={rec!r}")
        print()
elif isinstance(substrate, dict):
    print("Substrate is a dict:")
    for k, v in substrate.items():
        print(f"  {k}: {v!r}")
else:
    print(f"Unexpected substrate type: {substrate!r}")

# Also check summary_metrics
print("summary_metrics():")
try:
    sm = pe_obs.summary_metrics()
    for k, v in sm.items():
        print(f"  {k}: {v!r}")
except Exception as e:
    print(f"  ERROR: {e}")
