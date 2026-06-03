# Track A vs Track B: Named Divergence Comparison

*Phase 3 deliverable. Documents every intentional divergence between Track A's Creative Memory MCP server (production, pragmatic) and Track B's Reference Memory Server (purist, experimental). The dual-track setup IS the experiment.*

## Context

Both servers implement the same 6 principles but with different tradeoffs. Track A runs in production — it wraps an Obsidian vault, supports metadata bumps, and prioritizes usability. Track B is a controlled experiment — rigid write-once immutability, provenance as a first-class data structure, and a dedicated query layer. The Phase 2 benchmark measures which approach reduces coherence drift more effectively.

## Principles Re-ordered for Comparison

The principles hierarchy was re-ranked after Phase 1 due to security findings:

| Rank | Phase 1 (original) | Phase 1 (re-ranked) | Why changed |
|------|-------------------|---------------------|-------------|
| 1 | Write-Once, Query-Rich | Write-Once, Query-Rich | Unchanged — still load-bearing |
| 2 | Curated Forgetting | Curated Forgetting | Unchanged — paired with #1 |
| 3 | Discovery over Reinvention | **Memory Provenance** ↑ | Promoted: FrostD4D/MrGold/rook-ai memory poisoning requires provenance as security substrate |
| 4 | Token Discipline | Token Discipline | Stable |
| 5 | Architectural Visibility | Architectural Visibility | Stable |
| 6 | Memory Provenance | Discovery over Reinvention ↓ | Gated by provenance — can't discover across untrustworthy memory |

## Named Divergences

### D1: Write-Once Purity

**Principle at stake:** P4 (Write-Once, Query-Rich)

| Aspect | Track A | Track B |
|--------|---------|---------|
| **Storage** | Obsidian vault — markdown files with editable frontmatter | `log/entries.jsonl` — append-only JSONL, never modified |
| **Metadata** | Editable: `Last worked`, `status`, `bpm` can change | Immutable: every write is a new entry. Metadata queries derive from the log |
| **Metadata bumps** | Yes — bumps `Last worked` on every write (pragmatic) | No — session freshness derived from temporal query, not stored field |
| **Content edits** | Allowed: user can edit any markdown file | Forbidden: entries are hashed + chained. Any edit breaks the chain |

**Hypothesis:** Track B's rigid immutability prevents the compaction-driven timestamp destruction that monty_cmr10_research identified as the 36-hour drift mechanism. Track A's metadata bumps are a pragmatic violation — they work in single-track contexts but could compound into drift at scale.

**Test:** Run the Phase 2 benchmark against both servers. Measure drift rate at 36h, 72h. Track B should show lower drift.

### D2: Provenance Architecture

**Principle at stake:** P2 (Memory Provenance), now ranked #3

| Aspect | Track A | Track B |
|--------|---------|---------|
| **Provenance storage** | Embedded in markdown frontmatter and `## Metadata History` tables | First-class JSON field: `provenance.source`, `provenance.trust_level`, `provenance.witnesses`, `provenance.verification` |
| **Attribution granularity** | Track-level: version chain shows `{current: 126, previous: 128, reason: "felt rushed"}` | Entry-level: every fact has its own provenance chain |
| **Trust levels** | Implicit: human edits trusted, agent edits marked | Explicit: `high|medium|low|unverified` with witness requirement for high trust |
| **Tamper evidence** | None — markdown files can be edited undetectably | Hash chain: each entry's hash chains from the previous entry + content. `verify_chain()` detects any modification |
| **Quarantine** | Not implemented | Instrumentation can quarantine entries with metadata anomalies |

**Hypothesis:** Track B's explicit provenance enables the quarantine and trust escalation patterns that FrostD4D and MrGold identified as essential. Track A's implicit provenance works for a single trusted user but wouldn't scale to multi-agent contexts.

**Test:** Run the Phase 2 benchmark's provenance accuracy metric. Inject a "poisoned" fact (low trust, no witness). Measure whether each server can flag it.

### D3: Query Layer

**Principle at stake:** P4 (Query-Rich half), P1 (Token Discipline)

| Aspect | Track A | Track B |
|--------|---------|---------|
| **Query mechanism** | Markdown parsing: regex-based extraction from vault files | Indexed queries: temporal, tag, agent indices rebuilt from the log |
| **Search** | FTS over markdown content + wikilink graph traversal | Tag-based AND semantics + temporal range + agent filtering |
| **Semantic search** | None (markdown is the query surface) | Planned: embedding-based semantic query (not yet implemented) |
| **Token discipline** | Dashboard returns full content blocks (~3K tokens per track) | Pointers-only returns: ID + timestamp + tags, load content only on request |
| **Cross-reference** | Wikilink backlinks (`get_backlinks`, `mcp_creative_memory_read_backlinks`) | `cross_reference_query()` returns referencing entries with metadata |

**Hypothesis:** Track B's query layer should enable more token-efficient memory loading. The benchmark's token efficiency measurement will validate this. Track A's markdown-parsing approach is simpler but loads more context than needed.

**Test:** Measure tokens consumed during benchmark question answering. Track B should use fewer tokens for the same accuracy.

### D4: State Attestation

**Principle at stake:** P5 (Architectural Visibility)

| Aspect | Track A | Track B |
|--------|---------|---------|
| **Cross-session verification** | Not implemented — session resumption relies on file timestamps | `memory_attest()` + `memory_verify()` — signed state attestations with delta hash comparison |
| **Verification speed** | N/A | <10ms (delta hash comparison, does not re-read full log) |
| **Attestation granularity** | N/A | Session-level: snapshot of last 10 entry hashes + entry count |
| **Failure mode** | Silent drift: stale file timestamps can look current | Explicit mismatch: verification returns `verified: false` with actionable reason |

**Hypothesis:** The State Attestation pattern (from unitymolty, finding #40) eliminates the "10x compute tax on every resume" that monty_cmr10_research described. Track A's lack of attestation means each session must re-verify workspace state through file I/O.

**Test:** Simulate a session resume scenario. Measure time-to-trust (how long before the agent can confidently proceed). Track B should achieve trust in <10ms vs Track A's filesystem scan.

### D5: Instrumentation

**Principle at stake:** P5 (Architectural Visibility), P2 (Memory Provenance)

| Aspect | Track A | Track B |
|--------|---------|---------|
| **Anomaly detection** | None | Dual independent signal paths (noise + metadata) |
| **Noise detection** | N/A | Burst writes, empty content, duplicate detection |
| **Metadata anomaly detection** | N/A | Trust escalation without witness, unverified external sources, agent switch without reference |
| **Action thresholds** | N/A | Noise only → investigate. Metadata only → quarantine. Both → confirmed attack + alert |
| **Visibility** | `read_creative_status` shows vault health (orphans, broken links) | `memory_status` shows write count, anomaly counts, quarantined entries, chain integrity |

**Hypothesis:** Track B's instrumentation provides the architectural visibility that makes memory decisions auditable. Track A's vault-health checks are a lighter form but don't detect active memory corruption.

**Test:** Inject a memory poisoning attack (low-trust entry escalated to high trust without witness). Measure detection rate. Track B should detect; Track A should not.

### D6: Storage Format

**Principle at stake:** P6 (Discovery over Reinvention)

| Aspect | Track A | Track B |
|--------|---------|---------|
| **Format** | Markdown files in Obsidian vault | JSONL log + JSON index files |
| **Human readability** | High — markdown is natively readable | Medium — JSONL is readable but volume makes it less practical |
| **Machine parsability** | Medium — regex extraction, wikilink parsing | High — structured JSON, programmatic query |
| **Discoverability** | Wikilink graph provides cross-note discovery | `memory_discover()` provides cross-reference + tag co-occurrence |
| **Portability** | Tied to Obsidian vault structure | Standalone — any agent can point to the server |

**Hypothesis:** Track B's structured format enables better cross-agent discovery. Track A's markdown format is better for human-augmented workflows. The format choice reflects the primary user: Track A serves a producer with human-in-the-loop; Track B serves autonomous agent agents with no human oversight.

**Test:** Have two agents independently write memory entries. Measure how long it takes each to discover the other's patterns. Track B should enable faster discovery.

### D7: The Metadata Bump Boundary

**Principle at stake:** P4 (Write-Once) — the seam where purity becomes counterproductive

This is the explicit research question from Phase 1: "Where does write-once purity become counterproductive?"

| Scenario | Track A approach | Track B approach | Assessment |
|----------|-----------------|-----------------|------------|
| "When did I last work on this?" | Reads `Last worked` from frontmatter (1 field, 1 read) | Queries temporal index for most recent session entry (1 query, derives answer) | Track B is slightly more complex but maintains purity |
| "What's the current BPM?" | Reads `bpm` from frontmatter (current value stored) | Queries log for most recent `type: metadata_change` entry with field `bpm` (1 query, derives answer) | Track B's approach is correct but more expensive for frequently-read values |
| "What tracks are active?" | Reads `status` from each track note | Queries log for `status` entries, computes current state from most recent per track | Track B requires index maintenance; Track A is O(1) |
| Momentum scoring | Reads `Last worked` timestamps across all tracks | Temporal query across all tracks for recent session entries | Track B is semantically correct but computationally heavier |

**The boundary is frequency:** For metadata read >100x more often than written, Track A's approach reduces token consumption. For metadata where provenance matters (trust levels, witness lists), Track B's approach is necessary. The optimal design is **write-once log + derived metadata cache** — cache the frequently-read values but always derive them from the log, never store them independently. This is Track B's planned optimization path.

## Summary Matrix

| Principle | Track A | Track B | Winner (hypothesis) |
|-----------|---------|---------|---------------------|
| P4: Write-Once | Partial (metadata bumps) | Full (append-only + hash chain) | Track B — should reduce drift |
| P2: Provenance | Embedded in markdown | First-class data structure | Track B — enables quarantine |
| P4: Query-Rich | Regex + wikilinks | Indexed queries | Track B — more token-efficient |
| P5: Attestation | Not implemented | State Attestation + Delta Hash | Track B — eliminates re-verify tax |
| P5: Instrumentation | Vault health only | Dual signal anomaly detection | Track B — catches corruption |
| P1: Token Discipline | Content blocks | Pointers-first | Track B — less context waste |
| P3: Curated Forgetting | Markdown file management | TTL + index pruning | Parity — different mechanisms, same goal |
| P6: Discovery | Wikilink graph | Cross-reference + co-occurrence | Track B — structured queries |
| Usability | High (human-readable) | Medium (JSONL) | Track A — better for human workflows |
| Simplicity | High (markdown, no server) | Medium (server required) | Track A — simpler to set up |

## What Each Track Teaches

**Track A teaches:** Pragmatic memory works for single-agent, human-in-the-loop workflows. Metadata bumps are a real optimization when read frequency >> write frequency. Markdown is a fine storage format when humans need to inspect memory directly.

**Track B teaches:** Rigid write-once is viable at scale. Provenance as a first-class concern enables security patterns (quarantine, attestation) that are impossible with editable memory. The query layer pays for its complexity in token savings.

**The experiment:** The Phase 2 benchmark measures which approach actually reduces coherence drift. The hypothesis is that Track B's rigid approach wins on drift reduction but Track A wins on setup complexity. The optimal production system may be a hybrid that takes Track B's data model with Track A's usability layer.
