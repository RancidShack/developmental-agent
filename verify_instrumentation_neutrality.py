"""
verify_instrumentation_neutrality.py
-------------------------------------
Verify that v1.0 with instrumentation ON produces the same per-run
metrics as v1.0 with instrumentation OFF. This tests that the
recorder's read-only state access does not perturb the agent's
behaviour through any unintended side effect (e.g. RNG consumption,
state mutation, etc.).

The test:
  1. Pick three (cost, steps, seed) triples.
  2. Run each with instrument=False.
  3. Run each with instrument=True.
  4. Compare every per-run metric; assert exact equality.

If this passes, the recorder is provably non-invasive at the
behavioural level: the same agent in the same world produces the
same trajectory regardless of whether the recorder is observing.
"""

import sys
sys.path.insert(0, '.')

from curiosity_agent_v1_0_batch import run_one


def compare_metrics(m1, m2, label):
    """Compare two metric dicts. Skip the snapshot_count field (which
    legitimately differs between instrumented and non-instrumented runs)."""
    issues = []
    skip = {"snapshot_count"}
    for key in m1:
        if key in skip:
            continue
        if key not in m2:
            issues.append(f"  missing in m2: {key}")
            continue
        if m1[key] != m2[key]:
            issues.append(f"  {key}: off={m1[key]} vs on={m2[key]}")
    for key in m2:
        if key in skip:
            continue
        if key not in m1:
            issues.append(f"  missing in m1: {key}")

    if issues:
        print(f"FAIL [{label}]:")
        for issue in issues:
            print(issue)
        return False
    else:
        print(f"PASS [{label}]")
        return True


def main():
    test_cases = [
        (1.0, 5000, 42),
        (5.0, 5000, 137),
        (0.5, 5000, 9999),
    ]

    print("Verifying v1.0 instrumentation neutrality "
          "(on vs off must give identical metrics)\n")

    all_pass = True
    for cost, steps, seed in test_cases:
        metrics_off, _ = run_one(cost, steps, seed, run_idx=0,
                                  instrument=False)
        metrics_on, recorder = run_one(cost, steps, seed, run_idx=0,
                                        instrument=True)
        label = f"cost={cost} steps={steps} seed={seed}"
        passed = compare_metrics(metrics_off, metrics_on, label)
        if passed:
            print(f"  ({recorder.snapshot_count()} snapshots captured)")
        all_pass = all_pass and passed

    print()
    if all_pass:
        print("ALL TESTS PASS: instrumentation does not affect agent "
              "behaviour. The recorder is non-invasive.")
        sys.exit(0)
    else:
        print("FAILURE: instrumentation perturbs agent behaviour.")
        sys.exit(1)


if __name__ == "__main__":
    main()
