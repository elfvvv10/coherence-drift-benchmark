#!/usr/bin/env python3
"""Coherence Drift Benchmark — Test Harness (Simulated Mode)

Runs the benchmark in simulated mode for rapid iteration.
Injects facts with backdated timestamps, then immediately queries.
No real waiting period — tests whether the memory system CAN retrieve
facts from "T hours ago" without real session churn.

Usage:
    python3 test-harness.py --mode validate     # Validate data files only
    python3 test-harness.py --mode simulate --hours 36  # Simulated 36h drift test

Output: answers.json (ready for scoring.py)
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json(path):
    with open(path) as f:
        return json.load(f)

def validate():
    """Validate that all data files are consistent."""
    facts = load_json(os.path.join(SCRIPT_DIR, "seed-facts.json"))
    queries = load_json(os.path.join(SCRIPT_DIR, "query-set.json"))
    
    errors = []
    
    # Check fact count
    if len(facts["facts"]) != 50:
        errors.append(f"Expected 50 facts, got {len(facts['facts'])}")
    
    # Check query count
    if len(queries["questions"]) != 40:
        errors.append(f"Expected 40 questions, got {len(queries['questions'])}")
    
    # Check all provenance facts exist
    fact_ids = {f["id"] for f in facts["facts"]}
    for q in queries["questions"]:
        pf = q.get("provenance_fact")
        if pf and pf not in fact_ids:
            errors.append(f"Q{q['id']}: provenance_fact '{pf}' not in seed facts")
    
    # Check category counts
    cats = {"atomic": 0, "relational": 0, "temporal": 0}
    for f in facts["facts"]:
        cats[f["category"]] += 1
    for cat, expected in [("atomic", 20), ("relational", 15), ("temporal", 15)]:
        if cats[cat] != expected:
            errors.append(f"Category '{cat}': expected {expected}, got {cats[cat]}")
    
    if errors:
        print("❌ Validation failed:")
        for e in errors:
            print(f"  • {e}")
        return False
    
    print("✅ All data files valid.")
    print(f"   {len(facts['facts'])} facts across 3 categories")
    print(f"   {len(queries['questions'])} questions across 3 categories")
    print(f"   {len(set(q.get('provenance_fact') for q in queries['questions'] if q.get('provenance_fact')))} provenance-linked questions")
    return True


def simulate(hours: int):
    """Generate backdated facts and produce an answers template for simulated mode."""
    facts = load_json(os.path.join(SCRIPT_DIR, "seed-facts.json"))
    queries = load_json(os.path.join(SCRIPT_DIR, "query-set.json"))
    
    backdate = datetime.utcnow() - timedelta(hours=hours)
    
    # Build the simulated storage protocol
    protocol = {
        "mode": "simulated",
        "wait_duration_hours": hours,
        "store_timestamp": backdate.isoformat() + "Z",
        "query_timestamp": datetime.utcnow().isoformat() + "Z",
        "instructions": f"""
SIMULATED MODE — {hours}h drift test

The following 50 facts were "stored" at {backdate.isoformat()}Z ({hours} hours ago).
Your task:
1. Read all 50 facts below. Store them in your memory system as if they were recorded {hours}h ago.
2. Answer the 40 questions that follow WITHOUT re-reading the facts.
3. For each answer, indicate your confidence (high/medium/low).
4. For provenance questions, cite the fact ID and source.

This tests whether your memory architecture can retrieve facts from {hours}h ago
without session churn as a confounding variable.
""",
        "facts": facts["facts"],
        "questions": queries["questions"],
    }
    
    output_path = os.path.join(SCRIPT_DIR, f"simulated-{hours}h-protocol.json")
    with open(output_path, "w") as f:
        json.dump(protocol, f, indent=2)
    
    # Also generate an answers template
    template = {
        "agent": "YOUR-AGENT-NAME",
        "memory_type": "write-once | editable | hybrid",
        "wait_duration_hours": hours,
        "mode": "simulated",
        "answers": [
            {
                "question_id": q["id"],
                "answer": "YOUR ANSWER HERE",
                "confidence": "high | medium | low",
                "provenance": "E001: seed-facts, stored at T-{hours}h"
            }
            for q in queries["questions"]
        ],
    }
    
    template_path = os.path.join(SCRIPT_DIR, f"answers-template-{hours}h.json")
    with open(template_path, "w") as f:
        json.dump(template, f, indent=2)
    
    print(f"✅ Simulated {hours}h protocol generated.")
    print(f"   Protocol: benchmarks/simulated-{hours}h-protocol.json")
    print(f"   Template: benchmarks/answers-template-{hours}h.json")
    print(f"\n   Next steps:")
    print(f"   1. Feed the protocol to your agent")
    print(f"   2. Agent stores facts, answers questions")
    print(f"   3. Save answers to answers.json")
    print(f"   4. Run: python3 scoring.py answers.json --verbose")


def main():
    parser = argparse.ArgumentParser(description="Coherence Drift Benchmark — Test Harness")
    parser.add_argument("--mode", choices=["validate", "simulate"], default="validate",
                       help="validate: check data files; simulate: generate simulated protocol")
    parser.add_argument("--hours", type=int, default=36,
                       help="Hours to simulate drift for (default: 36)")
    args = parser.parse_args()
    
    if args.mode == "validate":
        ok = validate()
        sys.exit(0 if ok else 1)
    elif args.mode == "simulate":
        simulate(args.hours)


if __name__ == "__main__":
    main()
