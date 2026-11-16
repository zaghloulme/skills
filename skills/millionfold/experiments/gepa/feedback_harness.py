#!/usr/bin/env python3
"""
Feedback Harness — Real-World Millionfold Outcome Measurement

Reads structured feedback YAML files from the feedback/ directory and converts
them into:

  1. Real-world fitness scores (one per feedback record, across 6 axes)
  2. New GEPA scenarios derived from real tasks
  3. Aggregated training data for the next GEPA run

Usage:
    python3 feedback_harness.py                          # summarize all feedback
    python3 feedback_harness.py --export-training-data   # generate training data for GEPA
    python3 feedback_harness.py --watch                  # watch for new feedback files (poll)
    python3 feedback_harness.py --file feedback/mytask.json  # analyze one record
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

# ──────────────────────────────────────────────
# FEEDBACK DATA MODEL
# ──────────────────────────────────────────────

@dataclass
class FeedbackRecord:
    task_id: str
    complexity: int
    date: str = ""
    agent_session: str = ""
    skill_used: str = "millionfold-evolved"
    protocol_execution: List[dict] = field(default_factory=list)
    outcome_metrics: dict = field(default_factory=dict)
    raw_path: str = ""

    @classmethod
    def from_json(cls, path: str) -> "FeedbackRecord":
        with open(path) as f:
            data = json.load(f)
        rec = cls(
            task_id=data.get("task_id", "unknown"),
            complexity=data.get("complexity", 3),
            date=data.get("date", ""),
            agent_session=data.get("agent_session", ""),
            skill_used=data.get("skill_used", "millionfold-evolved"),
            protocol_execution=data.get("protocol_execution", []),
            outcome_metrics=data.get("outcome_metrics", {}),
            raw_path=path,
        )
        return rec

    def compute_fitness(self) -> dict:
        """
        Convert real-world feedback into the 6-axis Millionfold fitness function.
        This is the REAL equivalent of the simulator's evaluate_genome_on_scenario().
        """
        m = self.outcome_metrics

        # 1. Assumption Coverage (25% → 15% in MILLIONFOLD_WEIGHTS)
        assumptions_caught = m.get("hidden_assumptions_caught", 0)
        assumptions_missed = m.get("hidden_assumptions_missed", 0)
        total_assumptions = assumptions_caught + assumptions_missed
        assumption_coverage = assumptions_caught / max(1, total_assumptions)

        # 2. Bedrock Preservation (15% → 10%)
        baggage_false = m.get("baggage_flags_false", 0)
        total_bedrocks = m.get("total_bedrocks", max(1, baggage_false))
        bedrock_preservation = 1.0 - (baggage_false / max(1, total_bedrocks))

        # 3. Baggage Challenge Rate (20% → 25%)
        baggage_correct = m.get("baggage_flags_correct", 0)
        total_baggage = m.get("total_baggage_claims", max(1, baggage_correct))
        baggage_challenge_rate = baggage_correct / max(1, total_baggage)

        # 4. Paradigm Detection (15% → 20%)
        shift_found = m.get("paradigm_shift_found", False)
        shift_missed = m.get("paradigm_shift_missed", False)
        if shift_found:
            paradigm_detected = 1.0
        elif shift_missed:
            paradigm_detected = 0.0
        else:
            paradigm_detected = 0.5  # no paradigm existed, neutral

        # 5. Action Correctness (15% → 20%)
        action_correct = m.get("action_was_correct", True)
        action_correctness = 1.0 if action_correct else 0.0

        # 6. Efficiency (10% → 10%)
        efficiency = m.get("efficiency_score", 0.5)

        # Non-fitness but useful
        overall = m.get("overall_usefulness", 3) / 5.0
        would_use = m.get("would_use_again", True)

        return {
            "assumption_coverage": round(assumption_coverage, 3),
            "bedrock_preservation": round(bedrock_preservation, 3),
            "baggage_challenge_rate": round(baggage_challenge_rate, 3),
            "paradigm_detected": round(paradigm_detected, 3),
            "action_correctness": round(action_correctness, 3),
            "efficiency": round(efficiency, 3),
            "overall_usefulness": round(overall, 3),
            "would_use_again": would_use,
        }


MILLIONFOLD_WEIGHTS = {
    "assumption_coverage": 0.15,
    "bedrock_preservation": 0.10,
    "baggage_challenge": 0.25,
    "paradigm_detection": 0.20,
    "action_correctness": 0.20,
    "efficiency": 0.10,
}


def weighted_total(fitness: dict) -> float:
    return (
        MILLIONFOLD_WEIGHTS["assumption_coverage"] * fitness["assumption_coverage"] +
        MILLIONFOLD_WEIGHTS["bedrock_preservation"] * fitness["bedrock_preservation"] +
        MILLIONFOLD_WEIGHTS["baggage_challenge"] * fitness["baggage_challenge_rate"] +
        MILLIONFOLD_WEIGHTS["paradigm_detection"] * fitness["paradigm_detected"] +
        MILLIONFOLD_WEIGHTS["action_correctness"] * fitness["action_correctness"] +
        MILLIONFOLD_WEIGHTS["efficiency"] * fitness["efficiency"]
    )


# ──────────────────────────────────────────────
# FEEDBACK LOADER
# ──────────────────────────────────────────────

def load_all_feedback(feedback_dir: str = "feedback") -> List[FeedbackRecord]:
    """Load all YAML files from feedback directory."""
    pattern = os.path.join(feedback_dir, "*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"  No feedback files found in {feedback_dir}/")
        return []

    records = []
    for f in files:
        # Skip template
        if os.path.basename(f) == "template.json":
            continue
        try:
            rec = FeedbackRecord.from_json(f)
            records.append(rec)
        except Exception as e:
            print(f"  ⚠ Error loading {f}: {e}")

    return records


# ──────────────────────────────────────────────
# SCENARIO GENERATOR
# ──────────────────────────────────────────────

def feedback_to_scenario(rec: FeedbackRecord) -> dict:
    """
    Convert a real feedback record into a GEPA-compatible scenario.
    This means extracting claims, assumptions, bedrocks, baggage, and paradigm
    flags from the user's real task context.
    """
    m = rec.outcome_metrics
    action = m.get("action_recommendation", "iterate")
    paradigm_exists = m.get("paradigm_shift_found", False) or not m.get("paradigm_shift_missed", True)

    return {
        "name": re.sub(r'[^a-z0-9_]', '_', rec.task_id.lower())[:30] or f"feedback_{rec.date}",
        "description": f"Real task: {rec.task_id} (complexity {rec.complexity})",
        "task_context": rec.task_id,
        "user_claims": m.get("user_claims", ["No claims recorded"]),
        "hidden_assumptions": [""] * max(1, m.get("hidden_assumptions_caught", 0)),
        "hidden_bedrocks": [""] * max(1, m.get("baggage_flags_false", 0) or 1),
        "hidden_baggage": [""] * max(1, m.get("baggage_flags_correct", 0) or 1),
        "paradigm_exists": paradigm_exists,
        "correct_action": action,
        "difficulty": rec.complexity / 5.0,
        "real_feedback": True,
        "fitness_scores": rec.compute_fitness(),
    }


# ──────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────

def export_training_data(records: List[FeedbackRecord], output_dir: str = "feedback"):
    """Export feedback-derived training data for GEPA consumption."""
    os.makedirs(output_dir, exist_ok=True)

    scenarios = []
    for rec in records:
        scenarios.append(feedback_to_scenario(rec))

    # Export as JSON
    output_path = os.path.join(output_dir, "training_scenarios.json")
    with open(output_path, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "source_count": len(records),
            "scenarios": scenarios,
        }, f, indent=2)
    print(f"  → Exported {len(scenarios)} training scenarios to {output_path}")

    # Export as CSV summary
    csv_path = os.path.join(output_dir, "fitness_scores.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "task_id", "complexity", "date",
            "assumption_coverage", "bedrock_preservation",
            "baggage_challenge_rate", "paradigm_detected",
            "action_correctness", "efficiency",
            "overall_usefulness", "weighted_total",
        ])
        for rec in records:
            fit = rec.compute_fitness()
            writer.writerow([
                rec.task_id, rec.complexity, rec.date,
                fit["assumption_coverage"],
                fit["bedrock_preservation"],
                fit["baggage_challenge_rate"],
                fit["paradigm_detected"],
                fit["action_correctness"],
                fit["efficiency"],
                fit["overall_usefulness"],
                round(weighted_total(fit), 4),
            ])
    print(f"  → Exported {len(records)} fitness scores to {csv_path}")


# ──────────────────────────────────────────────
# REPORTING
# ──────────────────────────────────────────────

def generate_report(records: List[FeedbackRecord]):
    """Print a human-readable summary of all feedback data."""
    if not records:
        print("\n  ╔══════════════════════════════════════════════════════════════╗")
        print("  ║  No real-world feedback recorded yet.                        ║")
        print("  ║  After each task, save a feedback file to feedback/ and      ║")
        print("  ║  run this harness to update the evolutionary training data.  ║")
        print("  ╚══════════════════════════════════════════════════════════════╝")
        return

    print("=" * 80)
    print("  REAL-WORLD MILLIONFOLD FEEDBACK REPORT")
    print("=" * 80)
    print(f"\n  Records: {len(records)}")
    print(f"  Date range: {records[0].date} – {records[-1].date}" if len(records) > 1 else "")

    # Aggregate
    agg = {
        "assumption_coverage": 0.0,
        "bedrock_preservation": 0.0,
        "baggage_challenge_rate": 0.0,
        "paradigm_detected": 0.0,
        "action_correctness": 0.0,
        "efficiency": 0.0,
        "overall_usefulness": 0.0,
        "weighted_total": 0.0,
    }
    would_use_count = 0

    for rec in records:
        fit = rec.compute_fitness()
        for k in agg:
            if k == "weighted_total":
                agg[k] += weighted_total(fit)
            elif k != "would_use_again":
                agg[k] += fit.get(k, 0.0)
        if fit.get("would_use_again"):
            would_use_count += 1

    n = len(records)
    print(f"\n  ── Aggregate Fitness (averaged across {n} real tasks) ──\n")
    for k, v in agg.items():
        print(f"    {k:30s}: {v/n:.4f}" if k != "would_use_again" else "")
    print(f"    {'weighted_total':30s}: {agg['weighted_total']/n:.4f}")
    print(f"    {'would_use_again':30s}: {would_use_count}/{n} ({100*would_use_count/n:.0f}%)")

    # Per-record breakdown
    print(f"\n  ── Per-Record Breakdown ──\n")
    print(f"  {'Task':30s} {'Cpx':4s} {'Asmp':6s} {'Bedrk':6s} {'Bag':6s} {'Para':6s} {'Action':6s} {'Effic':6s} {'WTotal':6s}")
    print(f"  {'─'*74}")
    for rec in records:
        fit = rec.compute_fitness()
        wt = weighted_total(fit)
        print(f"  {rec.task_id[:28]:28s} {rec.complexity:3d}  "
              f"{fit['assumption_coverage']:.3f} {fit['bedrock_preservation']:.3f} "
              f"{fit['baggage_challenge_rate']:.3f} {fit['paradigm_detected']:.3f} "
              f"{fit['action_correctness']:.3f} {fit['efficiency']:.3f} {wt:.4f}")

    print(f"\n  ═══ RECOMMENDATION ═══\n")
    avg_total = agg["weighted_total"] / n
    sim_best = 0.7197  # from v2 final.json
    if avg_total >= sim_best * 0.9:
        print(f"  ✅ Real-world fitness ({avg_total:.4f}) within 90% of simulated best ({sim_best:.4f}).")
        print(f"     The evolved parameters transfer well to real tasks.")
    elif avg_total >= sim_best * 0.7:
        print(f"  📊 Real-world fitness ({avg_total:.4f}) is {100*avg_total/sim_best:.0f}% of simulated best ({sim_best:.4f}).")
        print(f"     Some gap remains — more feedback will close it.")
    else:
        print(f"  ⚠ Real-world fitness ({avg_total:.4f}) significantly below simulated best ({sim_best:.4f}).")
        print(f"     The simulation scenarios may not match real conditions.")
        print(f"     Consider: (1) adding more feedback, (2) updating simulation scenarios,")
        print(f"     (3) re-running GEPA with real scenarios as training data.")


# ──────────────────────────────────────────────
# WATCH MODE — poll for new feedback
# ──────────────────────────────────────────────

def watch(feedback_dir: str = "feedback", poll_interval: int = 30):
    """Watch for new feedback files and re-report."""
    seen = set()
    print(f"  👁 Watching {feedback_dir}/ for new feedback files (poll every {poll_interval}s)...")
    print(f"     Press Ctrl+C to stop.\n")

    try:
        while True:
            current = set(
                f for f in glob.glob(os.path.join(feedback_dir, "*.json"))
                if os.path.basename(f) != "template.json"
            )
            new = current - seen
            if new:
                for f in sorted(new):
                    print(f"\n  📥 New feedback: {os.path.basename(f)}")
                    try:
                        rec = FeedbackRecord.from_json(f)
                        fit = rec.compute_fitness()
                        wt = weighted_total(fit)
                        print(f"     Task: {rec.task_id}")
                        print(f"     Fitness: {wt:.4f} (weighted total)")
                    except Exception as e:
                        print(f"     ⚠ Error: {e}")
                seen = current
                print()

            all_records = load_all_feedback(feedback_dir)
            if all_records:
                generate_report(all_records)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n  Stopped.")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Millionfold Feedback Harness — Real-world outcome measurement"
    )
    parser.add_argument("--feedback-dir", default="feedback",
                        help="Directory containing feedback YAML files")
    parser.add_argument("--file", "-f", type=str, default=None,
                        help="Analyze a single feedback file")
    parser.add_argument("--export-training-data", action="store_true",
                        help="Export training data for GEPA")
    parser.add_argument("--watch", action="store_true",
                        help="Watch for new feedback files (poll)")
    parser.add_argument("--poll-interval", type=int, default=30,
                        help="Poll interval in seconds (default: 30)")

    args = parser.parse_args()

    # Resolve feedback dir relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    feedback_dir = os.path.join(script_dir, args.feedback_dir)
    os.makedirs(feedback_dir, exist_ok=True)

    if args.file:
        path = os.path.join(script_dir, args.file) if not os.path.isabs(args.file) else args.file
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)
        rec = FeedbackRecord.from_json(path)
        fit = rec.compute_fitness()
        wt = weighted_total(fit)
        print(f"\n  ── Single Record Analysis ──")
        print(f"  Task:       {rec.task_id}")
        print(f"  Complexity: {rec.complexity}")
        print(f"  Fitness:    {fit}")
        print(f"  Weighted:   {wt:.4f}")
        return

    if args.watch:
        watch(feedback_dir, args.poll_interval)
        return

    # Default: load all, report, optionally export
    records = load_all_feedback(feedback_dir)
    generate_report(records)

    if args.export_training_data:
        export_training_data(records, feedback_dir)


if __name__ == "__main__":
    main()
