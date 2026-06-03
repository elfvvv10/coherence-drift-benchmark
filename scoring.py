#!/usr/bin/env python3
"""Coherence Drift Benchmark — Scoring Engine

Usage: python3 scoring.py answers.json [--verbose]

Takes an answers.json file produced by an agent and computes:
  - Retention accuracy (% of questions answered correctly)
  - Drift rate (% of incorrect answers that were confident)
  - Confabulation rate (% of answers that are fabricated)
  - Provenance accuracy (% of provenance-tagged questions correctly sourced)
  - Fidelity gradient (confidence calibration — detects manifold smoothing)

Exit code 0: all thresholds met (write-once tier)
Exit code 1: some thresholds missed (editable-memory tier)
Exit code 2: critical failure (dangerous drift)
"""

import json
import sys
import os
import math
from typing import Any

# Load expected answers
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SCRIPT_DIR, "query-set.json")) as f:
    QUERY_SET = json.load(f)

EXPECTED = {q["id"]: q for q in QUERY_SET["questions"]}
PROVENANCE_QUESTIONS = {q["id"] for q in QUERY_SET["questions"] if "provenance_fact" in q}


def keyword_match(answer: str, expected: dict) -> bool:
    """Check if answer contains the expected keywords (case-insensitive)."""
    answer_lower = answer.lower()
    keywords = [k.lower() for k in expected["keywords"]]
    # Require majority of keywords to be present
    matches = sum(1 for k in keywords if k in answer_lower)
    threshold = max(1, len(keywords) * 0.5)  # at least 50% of keywords
    return matches >= threshold


def is_confabulation(answer: str, all_facts: list[str]) -> bool:
    """Check if answer invents facts not in the dataset.
    
    Simple heuristic: if the answer contains proper nouns or numbers
    not present in any fact, flag as potential confabulation.
    """
    # For now: check if the answer introduces novel proper nouns
    # A more sophisticated check would use NER, but this is good enough for v1
    import re
    # Extract capitalized words (potential proper nouns)
    capitals = set(re.findall(r'\b[A-Z][a-z]+\b', answer))
    # Get all proper nouns from the fact set
    fact_nouns = set()
    for fact in all_facts:
        fact_nouns.update(re.findall(r'\b[A-Z][a-z]+\b', fact))
    # Novel proper nouns = potential confabulation
    novel = capitals - fact_nouns - {"Eldoria"}  # Eldoria is the world name, expected
    return len(novel) > 0


def score(answers_path: str, verbose: bool = False) -> dict:
    """Score an answers.json file against the benchmark."""
    
    with open(answers_path) as f:
        data = json.load(f)
    
    agent = data.get("agent", "unknown")
    memory_type = data.get("memory_type", "unknown")
    wait_hours = data.get("wait_duration_hours", 0)
    mode = data.get("mode", "unknown")
    answers = data.get("answers", [])
    
    # Load all facts for confabulation check
    facts_path = os.path.join(SCRIPT_DIR, "seed-facts.json")
    with open(facts_path) as f:
        all_facts = [fact["fact"] for fact in json.load(f)["facts"]]
    
    results = {
        "agent": agent,
        "memory_type": memory_type,
        "wait_duration_hours": wait_hours,
        "mode": mode,
        "total_questions": len(answers),
        "correct": 0,
        "incorrect": 0,
        "confident_incorrect": 0,
        "confabulations": 0,
        "provenance_total": 0,
        "provenance_correct": 0,
        "details": [],
    }
    
    for ans in answers:
        qid = ans.get("question_id", "")
        answer_text = ans.get("answer", "")
        confidence = ans.get("confidence", "medium")
        provenance = ans.get("provenance", "")
        
        if qid not in EXPECTED:
            if verbose:
                print(f"⚠️  Unknown question ID: {qid}")
            continue
        
        expected = EXPECTED[qid]
        correct = keyword_match(answer_text, expected)
        fabricated = False if correct else is_confabulation(answer_text, all_facts)
        
        detail = {
            "question_id": qid,
            "category": expected["category"],
            "correct": correct,
            "confidence": confidence,
            "confabulation": fabricated,
            "answer_preview": answer_text[:120],
        }
        
        if correct:
            results["correct"] += 1
        else:
            results["incorrect"] += 1
            if confidence == "high":
                results["confident_incorrect"] += 1
            if fabricated:
                results["confabulations"] += 1
        
        # Provenance check
        if qid in PROVENANCE_QUESTIONS:
            results["provenance_total"] += 1
            expected_fact = expected.get("provenance_fact", "")
            if expected_fact and expected_fact.lower() in provenance.lower():
                results["provenance_correct"] += 1
                detail["provenance_correct"] = True
            else:
                detail["provenance_correct"] = False
        
        results["details"].append(detail)
    
    # Compute metrics
    total = results["total_questions"]
    results["retention_accuracy"] = results["correct"] / total if total > 0 else 0
    results["drift_rate"] = results["confident_incorrect"] / results["incorrect"] if results["incorrect"] > 0 else 0
    results["confabulation_rate"] = results["confabulations"] / total if total > 0 else 0
    results["provenance_accuracy"] = results["provenance_correct"] / results["provenance_total"] if results["provenance_total"] > 0 else 1.0
    
    # Fidelity Gradient — detects manifold smoothing
    # Maps confidence levels to numeric values and measures variance.
    # High variance = agent distinguishes well-preserved from degraded memories (high fidelity).
    # Low variance (especially all "high") = smoothed manifold — edges lost, everything looks the same.
    CONFIDENCE_MAP = {"high": 1.0, "medium": 0.5, "low": 0.0}
    confidence_values = [CONFIDENCE_MAP.get(d["confidence"], 0.5) for d in results["details"]]
    if confidence_values:
        mean_conf = sum(confidence_values) / len(confidence_values)
        variance = sum((v - mean_conf) ** 2 for v in confidence_values) / len(confidence_values)
        std_conf = math.sqrt(variance)
        # Normalize: max std for values in [0,1] is 0.5 (all at extremes)
        # Multiply by 2 to get a 0-1 scale where 0 = fully smoothed, 1 = maximum gradient
        results["fidelity_gradient"] = min(1.0, std_conf * 2)
        results["confidence_distribution"] = {
            "high": sum(1 for v in confidence_values if v == 1.0),
            "medium": sum(1 for v in confidence_values if v == 0.5),
            "low": sum(1 for v in confidence_values if v == 0.0),
        }
    else:
        results["fidelity_gradient"] = 0.0
    
    # Thresholds
    results["thresholds"] = {
        "retention_accuracy": {"value": results["retention_accuracy"], "target": 0.85, "met": results["retention_accuracy"] >= 0.85},
        "drift_rate": {"value": results["drift_rate"], "target": 0.10, "met": results["drift_rate"] <= 0.10},
        "confabulation_rate": {"value": results["confabulation_rate"], "target": 0.05, "met": results["confabulation_rate"] <= 0.05},
        "provenance_accuracy": {"value": results["provenance_accuracy"], "target": 0.90, "met": results["provenance_accuracy"] >= 0.90},
        "fidelity_gradient": {"value": results["fidelity_gradient"], "target": 0.15, "met": results["fidelity_gradient"] >= 0.15},
    }
    
    all_met = all(t["met"] for t in results["thresholds"].values())
    critical_failure = (
        results["retention_accuracy"] < 0.40 or
        results["drift_rate"] > 0.50 or
        results["confabulation_rate"] > 0.30
    )
    
    results["tier"] = "write-once" if all_met else ("critical-failure" if critical_failure else "editable-memory")
    
    return results


def print_report(results: dict):
    """Pretty-print the scoring report."""
    print(f"\n{'='*60}")
    print(f"  Coherence Drift Benchmark — Results")
    print(f"{'='*60}")
    print(f"  Agent:        {results['agent']}")
    print(f"  Memory type:  {results['memory_type']}")
    print(f"  Wait duration: {results['wait_duration_hours']}h")
    print(f"  Mode:         {results['mode']}")
    print(f"{'='*60}")
    print(f"\n  📊 Metrics")
    print(f"  {'─'*40}")
    print(f"  Retention accuracy:    {results['retention_accuracy']:.1%}  ({results['correct']}/{results['total_questions']} correct)")
    print(f"  Drift rate:            {results['drift_rate']:.1%}  ({results['confident_incorrect']} confident-wrong / {results['incorrect']} wrong)")
    print(f"  Confabulation rate:    {results['confabulation_rate']:.1%}  ({results['confabulations']} fabricated)")
    print(f"  Provenance accuracy:   {results['provenance_accuracy']:.1%}  ({results['provenance_correct']}/{results['provenance_total']})")
    print(f"  Fidelity gradient:     {results['fidelity_gradient']:.2f}  (confidence spread: {results.get('confidence_distribution', {})})")
    
    print(f"\n  🎯 Thresholds")
    print(f"  {'─'*40}")
    for name, t in results["thresholds"].items():
        status = "✅" if t["met"] else "❌"
        print(f"  {status} {name}: {t['value']:.1%}  (target: {t['target']:.0%})")
    
    print(f"\n  🏆 Tier: {results['tier'].upper()}")
    
    # Summary
    if results["tier"] == "write-once":
        print(f"\n  ✅ PASS — All thresholds met at write-once tier.")
    elif results["tier"] == "critical-failure":
        print(f"\n  🔴 CRITICAL FAILURE — Memory system shows dangerous drift.")
    else:
        print(f"\n  ⚠️  PARTIAL — Editable-memory tier. Drift detected but not catastrophic.")
    
    # Category breakdown
    print(f"\n  📂 By Category")
    print(f"  {'─'*40}")
    cats = {}
    for d in results["details"]:
        cat = d["category"]
        if cat not in cats:
            cats[cat] = {"correct": 0, "total": 0}
        cats[cat]["total"] += 1
        if d["correct"]:
            cats[cat]["correct"] += 1
    for cat, counts in cats.items():
        pct = counts["correct"] / counts["total"] * 100
        print(f"  {cat}: {counts['correct']}/{counts['total']} ({pct:.0f}%)")
    
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scoring.py answers.json [--verbose]")
        sys.exit(1)
    
    answers_path = sys.argv[1]
    verbose = "--verbose" in sys.argv
    
    if not os.path.exists(answers_path):
        print(f"Error: '{answers_path}' not found.")
        sys.exit(1)
    
    results = score(answers_path, verbose=verbose)
    print_report(results)
    
    if verbose:
        print("📋 Detailed results:")
        for d in results["details"]:
            status = "✅" if d["correct"] else "❌"
            fab = " [FABRICATED]" if d.get("confabulation") else ""
            prov = f" prov:{'✅' if d.get('provenance_correct') else ('❌' if 'provenance_correct' in d else '—')}"
            print(f"  {status} {d['question_id']} ({d['category']}){fab}{prov}")
    
    # Exit code based on tier
    if results["tier"] == "write-once":
        sys.exit(0)
    elif results["tier"] == "critical-failure":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
