# Reference Memory Server — Track B (Rigid Write-Once)

*Phase 3, Creative Memory Project. Minimal MCP server implementing the 6 design principles with strict write-once immutability.*

## Design

A single-file Python MCP server (`server.py`) that any agent can point to. The storage model is:

```
write-once log → provenance metadata → query layer → agent context
      ↑                ↑                    ↑
  immutable       who/when/trust       temporal/semantic/relational
```

### Core Distinction from Track A

Track A (Creative Memory MCP server) wraps an Obsidian vault with markdown files. It's pragmatic: metadata bumps on every write, editable frontmatter, markdown-based queries. Track B is purist: rigid write-once immutability, provenance as a first-class data structure, dedicated query layer.

**This is not better/worse — it's a controlled experiment.** Two implementations of the same principles, designed to validate whether strict write-once purity provides measurable benefits over pragmatic hybrid approaches. The Phase 2 benchmark is the measuring stick.

### Storage Model

```
~/.memory-server/
├── log/           # Write-once append-only log
│   └── entries.jsonl     # One JSON object per line, never modified
├── index/         # Derived indices (can be rebuilt from log)
│   ├── temporal.json     # Timestamp-sorted entry pointers
│   ├── semantic.json     # Embedding-sorted entry pointers
│   └── relational.json  # Cross-reference graph
├── attestations/  # Cross-session state attestations
│   └── session-{id}.json # Signed session state snapshots
└── config.json    # Server configuration (mutable metadata, NOT memory)
```

### Entry Schema (JSONL)

Each entry in `log/entries.jsonl`:
```json
{
  "id": "uuid-v7",
  "timestamp": "2026-06-03T12:00:00Z",
  "agent_id": "thewanderingelf",
  "session_id": "uuid-v7",
  "content": {
    "type": "fact|decision|observation|attestation",
    "data": {...},
    "confidence": 0.0-1.0
  },
  "provenance": {
    "source": "direct_observation|inference|external|attested",
    "trust_level": "high|medium|low|unverified",
    "witnesses": ["agent_id"],
    "verification": "none|delta_hash|full_audit"
  },
  "references": ["entry_id"],  # Links to other entries
  "tags": ["keyword1", "keyword2"],
  "hash": "sha256-of-previous-entry+this-content"
}
```

### Query API (MCP Tools)

| Tool | Principle | Description |
|------|-----------|-------------|
| `memory_write` | P4 | Append to write-once log. Returns entry ID + hash. |
| `memory_read` | P1, P3 | Load entries by ID, tag, time range, or semantic query. Selective loading. |
| `memory_search` | P1, P4 | Full-text + semantic search. Returns pointers, not full content. |
| `memory_provenance` | P2 | Trace an entry's chain: who wrote it, when, trust level, witnesses. |
| `memory_attest` | P5 | Sign a state attestation for cross-session verification. |
| `memory_verify` | P5 | Verify a previous attestation against current log state. |
| `memory_status` | P5, P6 | Server health, entry count, index freshness, anomalous writes flagged. |
| `memory_discover` | P6 | Cross-agent pattern discovery: find entries by pattern, tag co-occurrence. |

### Instrumentation (from Phase 3 Design Note)

Dual independent signal paths:
- **Noise anomaly:** Unusual write patterns (burst writes, empty content, duplicate hashes) → flag for investigation
- **Metadata anomaly:** Provenance mismatch, trust level escalation without witness → quarantine entry
- **Both triggered:** Confirmed attack → lock down + alert

### Integration with Phase 2 Benchmark

The reference server is the target for Phase 2 benchmark testing:
- Load 50 seed facts via `memory_write`
- Wait 36h with zero reinforcement
- Query via `memory_read` + `memory_search`
- Scoring engine measures: retention, drift, confabulation, provenance, fidelity gradient

## Setup

```bash
python3 server.py --port 8080 --data-dir ~/.memory-server/
```

Agent configuration (add to config.yaml):
```yaml
mcp_servers:
  memory-reference:
    command: python3
    args: ["/path/to/reference-impl/server.py", "--port", "8080"]
```

## Exit Condition for Phase 3

Reference server passes the Phase 2 benchmark with statistically significant improvement over editable-memory baseline. Comparison doc (`track-a-vs-track-b.md`) names every divergence from Track A.
