"""
regenerate_meta_report_v0_13.py
-------------------------------
Standalone utility to regenerate meta_report_v0_13.txt from the
existing run_data_v0_13.csv and run_data_v0_12.csv, applying the
v0.13.1-amended audit logic (Check 4a + Check 4b split) without
requiring the batch to be re-executed.

Use case: the v0.13 batch ran with the original audit logic that
confounded pre-activation byte-identical preservation with full-run
aggregate comparison. The v0.13.1 amendment splits the audit into
Check 4a (byte-identical, restricted to non-activated runs) and
Check 4b (post-activation cross-layer effect characterisation,
activated runs). This utility re-runs the audit on the existing CSVs
under the amended logic.

Run from terminal with:
    python3 regenerate_meta_report_v0_13.py

Requires run_data_v0_13.csv and run_data_v0_12.csv in the working
directory. Produces meta_report_v0_13.txt as output.
"""

import csv
from collections import defaultdict, Counter
import numpy as np


def load_csv(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    # Coerce numeric fields to native types where appropriate
    for r in rows:
        for f in ("hazard_cost",):
            try:
                r[f] = float(r[f])
            except (ValueError, KeyError):
                pass
        for f in ("num_steps", "run_idx", "phase_1_end", "phase_2_end",
                  "frame_attempts_p1", "frame_attempts_p2",
                  "frame_attempts_p3",
                  "hazard_entries_p1", "hazard_entries_p2",
                  "hazard_entries_p3",
                  "hazards_flagged",
                  "time_to_first_flag", "time_to_second_flag",
                  "time_to_final_flag",
                  "first_entry_conversions",
                  "actions_gated_p2", "actions_gated_p3",
                  "attractors_mastered",
                  "time_to_first_mastery", "time_to_final_mastery",
                  "activation_step", "end_state_found_step",
                  "end_state_visits", "post_activation_window",
                  "discovery_time"):
            v = r.get(f)
            if v in (None, "", "None"):
                r[f] = None
            else:
                try:
                    r[f] = int(v)
                except (ValueError, TypeError):
                    pass
        for f in ("total_cost", "cost_on_sig_matched"):
            v = r.get(f)
            if v in (None, "", "None"):
                r[f] = None
            else:
                try:
                    r[f] = float(v)
                except (ValueError, TypeError):
                    pass
        # end_state_banked is a bool stored as string
        v = r.get("end_state_banked")
        if v in ("True", "true", "1"):
            r["end_state_banked"] = True
        elif v in ("False", "false", "0"):
            r["end_state_banked"] = False
    return rows


def main():
    print("Loading run_data_v0_13.csv ...")
    results = load_csv("run_data_v0_13.csv")
    print(f"  {len(results)} v0.13 runs loaded.")

    print("Loading run_data_v0_12.csv ...")
    baseline = load_csv("run_data_v0_12.csv")
    print(f"  {len(baseline)} v0.12 baseline runs loaded.")
    print()

    # Build v0.12 lookup
    v12_lookup = {}
    for r in baseline:
        if r["arch"] != "v0_12":
            continue
        try:
            key = (r["hazard_cost"], r["num_steps"], int(r["run_idx"]))
            v12_lookup[key] = r
        except (ValueError, KeyError, TypeError):
            continue

    audit_fields = [
        "phase_1_end", "phase_2_end",
        "frame_attempts_p1", "frame_attempts_p2", "frame_attempts_p3",
        "hazard_entries_p1", "hazard_entries_p2",
        "hazards_flagged",
        "time_to_first_flag", "time_to_second_flag", "time_to_final_flag",
        "first_entry_conversions",
        "attractors_mastered",
        "time_to_first_mastery", "time_to_final_mastery",
        "first_banked", "mastery_sequence",
    ]

    # ---- Check 4a: non-activated runs ----
    n_4a_audited = 0
    n_4a_matching = 0
    mismatches_4a = defaultdict(int)
    examples_4a = []
    for r13 in results:
        if r13.get("activation_step") is not None:
            continue
        key = (r13["hazard_cost"], r13["num_steps"], r13["run_idx"])
        if key not in v12_lookup:
            continue
        r12 = v12_lookup[key]
        n_4a_audited += 1
        matches = True
        run_mismatches = []
        for field in audit_fields:
            v13_v = r13.get(field)
            v12_v = r12.get(field)
            v13_s = "" if v13_v is None else str(v13_v)
            v12_s = "" if v12_v in (None, "None") else str(v12_v)
            if v13_s != v12_s:
                matches = False
                run_mismatches.append((field, v13_s, v12_s))
                mismatches_4a[field] += 1
        if matches:
            n_4a_matching += 1
        elif len(examples_4a) < 3:
            examples_4a.append((key, run_mismatches))

    check_4a_pass = (n_4a_audited > 0 and n_4a_matching == n_4a_audited)

    # ---- Check 4b: activated runs ----
    threat_fields = {"hazards_flagged", "hazard_entries_p1",
                     "hazard_entries_p2", "time_to_first_flag",
                     "time_to_second_flag", "time_to_final_flag",
                     "first_entry_conversions"}
    mastery_fields = {"attractors_mastered", "time_to_first_mastery",
                      "time_to_final_mastery", "first_banked",
                      "mastery_sequence"}
    n_4b_audited = 0
    n_4b_divergent = 0
    threat_only = mastery_only = both = 0
    mismatches_4b = defaultdict(int)
    v13_higher = defaultdict(int)
    v12_higher = defaultdict(int)
    directional = ["hazards_flagged", "hazard_entries_p2",
                   "first_entry_conversions"]

    for r13 in results:
        if r13.get("activation_step") is None:
            continue
        key = (r13["hazard_cost"], r13["num_steps"], r13["run_idx"])
        if key not in v12_lookup:
            continue
        r12 = v12_lookup[key]
        n_4b_audited += 1
        diverged_fields = set()
        for field in audit_fields:
            v13_v = r13.get(field)
            v12_v = r12.get(field)
            v13_s = "" if v13_v is None else str(v13_v)
            v12_s = "" if v12_v in (None, "None") else str(v12_v)
            if v13_s != v12_s:
                diverged_fields.add(field)
                mismatches_4b[field] += 1
        if diverged_fields:
            n_4b_divergent += 1
            t = bool(diverged_fields & threat_fields)
            m = bool(diverged_fields & mastery_fields)
            if t and m:
                both += 1
            elif t:
                threat_only += 1
            elif m:
                mastery_only += 1
        for field in directional:
            if field not in diverged_fields:
                continue
            try:
                v13_n = int(r13.get(field) or 0)
                v12_raw = r12.get(field)
                v12_n = (int(v12_raw) if v12_raw not in (None, "", "None")
                         else 0)
                if v13_n > v12_n:
                    v13_higher[field] += 1
                elif v12_n > v13_n:
                    v12_higher[field] += 1
            except (ValueError, TypeError):
                pass

    # ---- Build the report ----
    lines = []
    lines.append("=" * 76)
    lines.append("v0.13 BATCH META-REPORT (regenerated under v0.13.1 amendment)")
    lines.append("=" * 76)
    lines.append(f"v0.13 runs:  {len(results)}")
    lines.append(f"v0.12 baseline: {len(baseline)} runs")
    lines.append(f"Activated runs: "
                 f"{sum(1 for r in results if r.get('activation_step') is not None)}")
    lines.append(f"Non-activated runs: "
                 f"{sum(1 for r in results if r.get('activation_step') is None)}")
    lines.append("")

    # Discovery rates per run length
    lines.append("--- v0.13 END-STATE FINDINGS (HEADLINE) ---")
    for steps in sorted(set(r["num_steps"] for r in results)):
        slc = [r for r in results if r["num_steps"] == steps]
        n_act = sum(1 for r in slc if r.get("activation_step") is not None)
        n_disc = sum(1 for r in slc if r.get("end_state_found_step") is not None)
        lines.append(f"\nRun length {steps}:")
        lines.append(f"  Activation rate: {n_act}/{len(slc)} "
                     f"({100*n_act/len(slc):.1f}%)")
        lines.append(f"  Discovery rate:  {n_disc}/{len(slc)} "
                     f"({100*n_disc/len(slc):.1f}%)")
        if n_act > 0:
            cond_pct = 100 * n_disc / n_act
            lines.append(f"  Conditional discovery (given activation): "
                         f"{n_disc}/{n_act} ({cond_pct:.1f}%)")

        act_steps = [r["activation_step"] for r in slc
                     if r.get("activation_step") is not None]
        if act_steps:
            lines.append(f"  Activation step: mean {np.mean(act_steps):.0f} "
                         f"(min {min(act_steps)}, max {max(act_steps)}, "
                         f"n={len(act_steps)})")
        windows = [r["post_activation_window"] for r in slc
                   if r.get("post_activation_window") is not None]
        if windows:
            lines.append(f"  Post-activation window: mean {np.mean(windows):.0f} "
                         f"(min {min(windows)}, max {max(windows)})")
        disc_times = [r["discovery_time"] for r in slc
                      if r.get("discovery_time") is not None]
        if disc_times:
            lines.append(f"  Discovery time: mean {np.mean(disc_times):.0f} "
                         f"(min {min(disc_times)}, max {max(disc_times)}, "
                         f"n={len(disc_times)})")

    # Check 4a
    lines.append("\n\n--- v0.13 CHECK 4a: PRE-ACTIVATION PRESERVATION ---")
    lines.append("(Restricted to non-activated runs per v0.13.1 amendment)")
    pct_4a = (100 * n_4a_matching / n_4a_audited) if n_4a_audited > 0 else 0.0
    lines.append(f"  Non-activated runs audited: {n_4a_audited}")
    lines.append(f"  Byte-identical to v0.12 baseline: "
                 f"{n_4a_matching}/{n_4a_audited} ({pct_4a:.1f}%)")
    if mismatches_4a:
        lines.append(f"  Field mismatch counts:")
        for field, count in sorted(mismatches_4a.items(),
                                   key=lambda x: -x[1]):
            lines.append(f"    {field}: {count} mismatches")
    if check_4a_pass:
        lines.append(f"  CHECK 4a PASS: byte-identical preservation holds")
        lines.append(f"  across all {n_4a_audited} non-activated matched-seed runs.")
    elif n_4a_audited == 0:
        lines.append(f"  CHECK 4a INCONCLUSIVE: no non-activated runs in batch.")
    else:
        lines.append(f"  CHECK 4a FAIL: pre-activation divergence detected.")

    # Check 4b
    lines.append("\n\n--- v0.13 CHECK 4b: POST-ACTIVATION CROSS-LAYER EFFECT ---")
    lines.append("(Characterisation of activated runs per v0.13.1 amendment)")
    pct_4b = (100 * n_4b_divergent / n_4b_audited) if n_4b_audited > 0 else 0.0
    lines.append(f"  Activated runs audited: {n_4b_audited}")
    lines.append(f"  Divergent from v0.12 baseline: "
                 f"{n_4b_divergent}/{n_4b_audited} ({pct_4b:.1f}%)")
    lines.append(f"  Divergence category breakdown:")
    lines.append(f"    Threat-layer fields only:  {threat_only} runs")
    lines.append(f"    Mastery-layer fields only: {mastery_only} runs")
    lines.append(f"    Both threat and mastery:   {both} runs")
    if mismatches_4b:
        lines.append(f"  Field-level divergence (top fields):")
        for field, count in sorted(mismatches_4b.items(),
                                   key=lambda x: -x[1])[:6]:
            lines.append(f"    {field}: {count} runs")
    if v13_higher or v12_higher:
        lines.append(f"  Direction of divergence:")
        for field in directional:
            if field in v13_higher or field in v12_higher:
                lines.append(f"    {field}: v0.13 higher in "
                             f"{v13_higher.get(field, 0)}, v0.12 higher in "
                             f"{v12_higher.get(field, 0)}")
    lines.append("")
    if mastery_only == 0 and both == 0:
        lines.append("  Mastery dynamics are byte-identical to v0.12 in all")
        lines.append(f"  {n_4b_audited} activated runs. Category E NOT triggered.")
    else:
        lines.append(f"  WARNING: {mastery_only + both} activated runs show")
        lines.append(f"  mastery-layer divergence; investigate before paper.")

    # Category A assessment
    lines.append("\n\n--- v0.13 PRE-REGISTERED CATEGORY ASSESSMENT ---")
    cat_a_thresholds = {20000: 30, 80000: 50, 160000: 55}
    cat_a_checks = {}
    for steps in sorted(set(r["num_steps"] for r in results)):
        slc = [r for r in results if r["num_steps"] == steps]
        n_disc = sum(1 for r in slc
                     if r.get("end_state_found_step") is not None)
        threshold = cat_a_thresholds.get(steps)
        if threshold is not None:
            ok = (n_disc >= threshold)
            cat_a_checks[steps] = ok
            lines.append(f"  Check (discovery rate >= {threshold}/60 "
                         f"at {steps} steps): {n_disc}/{len(slc)} - "
                         f"{'PASS' if ok else 'FAIL'}")

    lines.append(f"  Check 4a (byte-identical, non-activated runs): "
                 f"{n_4a_matching}/{n_4a_audited} - "
                 f"{'PASS' if check_4a_pass else 'FAIL'}")

    lines.append("")
    all_disc_pass = all(cat_a_checks.values()) if cat_a_checks else False
    if all_disc_pass and check_4a_pass:
        lines.append("  CATEGORY A — successful late-target location with full preservation.")
    else:
        lines.append("  CATEGORY A NOT MET")
        if not all_disc_pass:
            failing = [s for s, ok in cat_a_checks.items() if not ok]
            if failing:
                lines.append(f"    Failed: discovery rate at run length(s) {failing}")
        if not check_4a_pass and n_4a_audited > 0:
            lines.append(f"    Failed: pre-activation divergence in non-activated runs")

    # Category F (honesty constraint)
    lines.append("")
    lines.append("  CATEGORY F (HONESTY CONSTRAINT) — applies regardless of")
    lines.append("  the operational result. The locating capability operates")
    lines.append("  through inherited v0.11.2 / v0.12 Phase 3 dynamics.")

    # Write
    report = "\n".join(lines)
    print(report)
    with open("meta_report_v0_13.txt", "w") as f:
        f.write(report)
    print(f"\nMeta-report saved to meta_report_v0_13.txt")


if __name__ == "__main__":
    main()
