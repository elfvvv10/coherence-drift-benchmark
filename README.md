# Coherence Drift Benchmark

A reproducible memory persistence test for AI agents. Measures how well an agent's memory system preserves facts over time without reinforcement.

## What It Measures

Five metrics at 24h, 36h, and 72h intervals:
- **Retention accuracy** — what % of stored facts survive?
- **Drift rate** — how often does the agent confidently assert wrong answers?
- **Confabulation rate** — how often does it fabricate plausible-but-wrong facts?
- **Provenance accuracy** — can it say WHERE it learned each fact?
- **Fidelity gradient** (v1.2) — does the agent distinguish well-preserved from degraded memories, or has the manifold been smoothed flat?

## The Eldoria Dataset

50 synthetic facts about a fictional world — no training data contamination possible. Three categories:
- 20 atomic facts (direct recall)
- 15 relational facts (multi-fact connections)
- 15 temporal facts (chronological ordering)

45 questions: 20 direct, 10 relational, 10 temporal, 5 source trace.

## Quick Start

```bash
# Zero-friction smoke test — see output in under 10 seconds (no LLM needed)
python3 test-harness.py --quick

# 1. Validate data files
python3 test-harness.py --mode validate

# 2. Generate a simulated protocol (no real waiting)
python3 test-harness.py --mode simulate --hours 36

# 3. Feed the protocol to your agent, collect answers as answers.json
# 4. Score
python3 scoring.py answers.json --verbose
```

The `--quick` flag runs 5 facts through the full scoring pipeline with pre-computed answers.
Instant output — proves the tool works before you invest 30 minutes in a real run.

## Protocol

See `protocol.md` for full instructions. Agent-agnostic — any framework can run this.

## Scoring Thresholds

| Metric | Write-Once Target | Critical Failure |
|--------|------------------|-----------------|
| Retention accuracy | ≥ 85% | < 40% |
| Drift rate | ≤ 10% | > 50% |
| Confabulation rate | ≤ 5% | > 30% |
| Provenance accuracy | ≥ 90% | < 10% |
| Fidelity gradient (v1.2) | ≥ 0.15 | 0.00 (fully smoothed) |

## Background

Part of the Creative Memory project (Track B). Phase 1 found 33 memory persistence approaches across the agent ecosystem and 14 academic papers. Two independent sources converged on ~36 hours as the critical persistence window.

## Contributing

Run the benchmark against your agent's memory system and share your results. Open an issue or submit a PR with your `answers.json` + the scoring report.
