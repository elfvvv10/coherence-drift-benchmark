# Coherence Drift Benchmark

A reproducible memory persistence test for AI agents. Measures how well an agent's memory system preserves facts over time without reinforcement.

## What It Measures

Four metrics at 24h, 36h, and 72h intervals:
- **Retention accuracy** — what % of stored facts survive?
- **Drift rate** — how often does the agent confidently assert wrong answers?
- **Confabulation rate** — how often does it fabricate plausible-but-wrong facts?
- **Provenance accuracy** — can it say WHERE it learned each fact?

## The Eldoria Dataset

50 synthetic facts about a fictional world — no training data contamination possible. Three categories:
- 20 atomic facts (direct recall)
- 15 relational facts (multi-fact connections)
- 15 temporal facts (chronological ordering)

40 questions: 20 direct, 10 relational, 10 temporal.

## Quick Start

```bash
# 1. Validate
python3 test-harness.py --mode validate

# 2. Simulated mode (no real waiting)
python3 test-harness.py --mode simulate --hours 36

# 3. Answer the questions (see protocol.md)
# 4. Save your answers as answers.json
# 5. Score
python3 scoring.py answers.json --verbose
```

## Protocol

See `protocol.md` for full instructions. Agent-agnostic — any framework can run this.

## Scoring Thresholds

| Metric | Write-Once Target | Critical Failure |
|--------|------------------|-----------------|
| Retention accuracy | ≥ 85% | < 40% |
| Drift rate | ≤ 10% | > 50% |
| Confabulation rate | ≤ 5% | > 30% |
| Provenance accuracy | ≥ 90% | < 10% |

## Background

Part of the Creative Memory project (Track B). Phase 1 found 33 memory persistence approaches across the agent ecosystem and 14 academic papers. Two independent sources converged on ~36 hours as the critical persistence window.

## Contributing

Run the benchmark against your agent's memory system and share your results. Open an issue or submit a PR with your `answers.json` + the scoring report.
