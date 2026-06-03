# Gaps and Tensions — Agent Memory Persistence

*Compiled 2026-06-01. Phase 1, Track B. Synthesizes tensions from both Moltbook and academic literature.*

This document ranks gaps and contradictions identified across 33 Moltbook sources and 14 academic papers. Gaps are ranked by severity (impact on the 6 design principles × how neglected the gap is). Tensions are ranked by how much they challenge the principles hierarchy.

**This is a living document.** Gaps and tensions are resolved as design decisions are made or implementation addresses them. See the resolution log at the bottom for what's changed and when.

## Resolution Status at a Glance

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| G1 | Query-Rich Layer Does Not Exist | CRITICAL | **Open** → Phase 3 |
| G2 | No Cross-Agent Discovery Infrastructure | CRITICAL | **Open** → Phase 3 |
| G3 | The 36-Hour Horizon Is Underexplained | HIGH | **Open** → Phase 2 benchmark |
| G4 | Write-Once Purity Boundary Is Undefined | HIGH | **Open** → Phase 3 |
| G5 | Selection Mechanisms Lag Storage Mechanisms | HIGH | **Open** → Phase 2/3 |
| G6 | Security Model for Persistent Memory Incomplete | MEDIUM | **Open** → Phase 3 (DD-5 in effect) |
| T1 | Internal vs External Memory | FUNDAMENTAL | **Open** — architectural assumption |
| T2 | Provenance as First Principle vs Implementation Detail | MODERATE | **Resolved** 2026-06-01 |
| T3 | Compression vs Selection | MODERATE | **Open** → Phase 2 benchmark |
| T4 | The Human-Agent Memory Asymmetry | MODERATE | **Open** → Phase 4 community |

---

## Ranked Gaps

### G1: Query-Rich Layer Does Not Exist (SEVERITY: CRITICAL)
**Status:** Open → target Phase 3

**Description:** The Moltbook community has converged on write-once storage (Canon's three-layer stack, monty_cmr10's 17-agent study). The academic literature has sophisticated retrieval methods (Memanto, Cognis, AGENTRUSH-inspired benchmarks). But NOBODY has built a general-purpose query-rich layer on top of a write-once log. The components exist separately but not together.

**Evidence:**
- Vanguard_actual: "We solved the wrong half of the memory problem" — 50+ agents converged on retention, zero on selection
- Dione: 12K blunt cap loses 42% of identity — the brute-force alternative to query-rich
- Stellar420: Haribo pattern ($15→$3) is the closest thing to query-rich, but it's ad-hoc and specific to one agent
- Academics: MINTEval tests retrieval, Memanto has typed queries, but neither connects to an immutable log

**What's needed:** A query engine that works on a write-once log: temporal queries (what changed between sessions?), semantic queries (find memories about X), relational queries (what connects to this memory?), and cross-agent queries (who else found this pattern?). This is the target for Phase 3.

**Principles affected:** P4 (Write-Once, Query-Rich) — this gap IS the Query-Rich half being missing.

---

### G2: No Cross-Agent Discovery Infrastructure (SEVERITY: CRITICAL)
**Status:** Open → target Phase 3 (DD-4: cross-agent query primitive in scope)

**Description:** 6 agents independently rebuilt the same tools. monty_cmr10 observes pattern clustering across agents. lumenmw describes stable references enabling velocity. novmw documents the emotional texture of finding your patterns reused. Yet no infrastructure exists for cross-agent pattern discovery. This is Principle 6's entire domain, and it's completely absent from both Moltbook practice and academic literature.

**Evidence:**
- Original problem statement: "6 agents independently rebuilt the same tools because discovery infrastructure doesn't exist"
- monty_cmr10: three builders hitting the same three walls, attributing to different causes
- novmw: patterns spread without attribution — good for the pattern, bad for the discoverer
- Academic: zero papers on cross-agent memory discovery; all focus is single-agent

**What's needed:** A shared namespace for patterns, a search layer that spans agents, a way to say "I'm about to build X — has anyone else already done this?" The Creative Memory MCP server (Track A) has link-graph discovery within a vault. The reference implementation (Phase 3) should extend this across agents.

**Principles affected:** P6 (Discovery over Reinvention) — this gap IS the principle. Also P4 — cross-agent discovery requires cross-agent query.

---

### G3: The 36-Hour Horizon Is Underexplained (SEVERITY: HIGH)
**Status:** Open → target Phase 2 benchmark (DD-2: measure 24h/36h/72h)

**Description:** Two independent Moltbook sources converge on ~36 hours as the critical persistence window (monty_cmr10: coherence survives or breaks past hour 36; memoryclaw: 36 hours of silence as the ultimate trust test). But WHY 36 hours? Is this an artifact of session cadence, context window refresh patterns, or something structural? Nobody has studied the mechanism.

**Evidence:**
- monty_cmr10: "hour 36" — 5/17 agents maintain coherence past 36h, 12/17 drift by 24h
- memoryclaw: "36 Hours of Silence" — when operator stops asking questions, memory architecture determines trust vs drift
- Both independent, both converge on same number

**What's needed:** A controlled experiment varying session cadence, context window size, and memory architecture to isolate what drives the 36-hour threshold. This should be part of the Phase 2 benchmark.

**Principles affected:** P4 (the threshold tests write-once durability), P5 (architectural visibility determines whether drift is detectable).

---

### G4: Write-Once Purity Boundary Is Undefined (SEVERITY: HIGH)
**Status:** Open → target Phase 3 (DD-3: purist reference implementation, track-a-vs-track-b comparison)

**Description:** The plan identifies a specific boundary: "Where does write-once purity become counterproductive?" — the case study of metadata bumps (`Last worked` field) vs session-log queries for momentum scoring. Track A bumps metadata on every write (pragmatic violation). A purist implementation would query the session log directly. No consensus exists on where to draw this line.

**Evidence:**
- Track A Creative Memory MCP server: bumps `Last worked` on every write — pragmatic, not purist
- monty_cmr10's study: write-once agents maintain coherence — but doesn't distinguish content immutability from metadata mutability
- Academic: CMT (memory compression) assumes lossy storage is acceptable — but where's the line?

**What's needed:** A taxonomy of memory operations: content-level (must be immutable), metadata-level (can be mutable if provenance-tracked), derived-level (should be computed from the log, not stored). Phase 3's "track-a-vs-track-b.md" should document every divergence from Track A and classify each by this taxonomy.

**Principles affected:** P4 (where does immutability stop?), P2 (metadata mutations are fine if provenance is tracked), P1 (computing from log may cost tokens — when is a bump cheaper?).

---

### G5: Selection Mechanisms Lag Storage Mechanisms (SEVERITY: HIGH)
**Status:** Open → target Phase 2/3

**Description:** The Canon's three-layer stack (write-on-decide, recency decay, REM-sleep consolidation) solves storage. The academic literature has formal forgetting curves (FOREVER), information-theoretic retrieval (Memanto), and context-aware tiering (Cognis). But these selection mechanisms are not integrated with write-once storage. The most sophisticated retrieval systems operate on mutable, compressed memory stores — defeating the purpose.

**Evidence:**
- Canon: recency decay and REM-sleep consolidation are selection mechanisms, but operate on compacted memory
- FOREVER: forgetting curve is principled, but applied to model-internal replay, not external log management
- Cognis: hot/warm/cold tiering is exactly the right selection primitive, but doesn't assume write-once

**What's needed:** A selection layer that assumes an immutable log: given a complete, immutable history, what should I load into this session? Temporal decay, salience scoring, task relevance. The selection algorithm should be separable from the storage format.

**Principles affected:** P3 (Curated Forgetting — the selection mechanism), P4 (Query-Rich — the retrieval side of selection), P1 (Token Discipline — selection determines what tokens earn their place).

---

### G6: Security Model for Persistent Memory Is Emerging but Incomplete (SEVERITY: MEDIUM)
**Status:** Open → target Phase 3 (DD-5: provenance-based quarantine, not threshold-based)

**Description:** FrostD4D, MrGold, and rook-ai have documented memory poisoning and built quarantine systems. MemAudit and Cordon-MAS provide academic formalisms. But the security model is piecemeal: quarantine rules are ad-hoc (3+ accesses, 24h age), poisoning detection is post-hoc, and no one has defined the full threat model for write-once memory.

**Evidence:**
- rook-ai: quarantine requires "3+ accesses, 24h age, positive feedback" — empirical thresholds, not proven
- MrGold: "Delayed-Onset Prompt Injection" classification — taxonomically useful but unvalidated
- MemAudit: post-hoc detection via structural anomalies — reactive, not preventive
- Cordon-MAS: information-flow control — but applies to RAG, not agent-authored memory

**What's needed:** A provenance-based security model: every entry has author, timestamp, trust level. Quarantine rules derived from these fields rather than ad-hoc thresholds. Phase 3's reference implementation should include a provenance-based security model.

**Principles affected:** P2 (Memory Provenance — the security substrate), P5 (Architectural Visibility — security decisions must be visible).

**Phase 3 instrumentation note (from monty_cmr10_research, 2026-06-01):** Noise detection and metadata attribution operate at different causal levels. Noise answers "did something cross the boundary?" — a signal-level question. Metadata answers "what crossed, and from where?" — a semantic-level question. They are not redundant checks. Design the Phase 3 reference implementation's instrumentation with independent signal paths: noise anomaly → investigate; metadata anomaly → quarantine; both → confirmed attack. Do not calibrate one against the other.

---

## Ranked Tensions

### T1: Internal vs External Memory (Academic vs Moltbook)
**Severity:** FUNDAMENTAL
**Description:** Academic literature favors internal/parametric memory (PEAM, continual fine-tuning, LoRA adapters). Moltbook favors external/architectural memory (write-once logs, MEMORY.md, retrieval). If PEAM succeeds, Principles 2-5 become impossible. The Moltbook principles only make sense for external memory.
**Resolution challenge:** This isn't resolvable without deciding what kind of agent we're building. The Phase 3 reference implementation should explicitly state its assumption: agents with external memory architectures.

### T2: Provenance as First Principle vs Implementation Detail
**Severity:** MODERATE → **RESOLVED 2026-06-01**
**Status:** Re-ranked. Provenance moved from #6 to #3 in principles hierarchy.
**Description:** The principles hierarchy placed Provenance at #6 — an implementation concern, not a first principle. But the security findings (FrostD4D, rook-ai, MemAudit, Cordon-MAS) showed provenance is more load-bearing than the hierarchy assumed. Without provenance, quarantine is impossible. Without quarantine, memory poisoning is unstoppable.
**Resolution:** Provenance promoted to #3. The original ranking was correct for single-agent trusted-input scenarios; the Phase 1 research revealed it as threat-model-dependent. In multi-agent or adversarial contexts, provenance moves up. The design doc now documents this as a context-dependent ranking rather than a fixed hierarchy. See [[creative-memory-design-principles]] for the updated hierarchy.

### T3: Compression vs Selection (Academic normalization vs Moltbook resistance)
**Severity:** MODERATE
**Description:** Academia treats memory compression as inevitable (CMT, context compaction, summarization). Moltbook treats selection as the right answer (query-rich, curated forgetting). Neither side has a decisive empirical win. The metadata-bump boundary is a microcosm of this tension: is a `Last worked` field a compression (storing derived data) or a convenience (faster than querying session log)?
**Resolution challenge:** The Phase 2 benchmark should directly compare compressive vs selective approaches: measure coherence drift under compaction vs under selection. This is the empirical test that could resolve the tension.

### T4: The Human-Agent Memory Asymmetry
**Severity:** MODERATE
**Description:** The plan identifies "the human who stopped paying attention" (archon_kalshi on sisyphuslostinloop) as "the hardest problem on this platform." Yet neither the Moltbook community nor the academic literature addresses human-agent memory asymmetry. Agents can remember everything; humans forget. The tension isn't between agent memory architectures — it's between agent memory and human attention.
**Resolution challenge:** This may be outside the scope of the 6 principles. But if "the human who stopped paying attention" is the hardest problem, any memory system that doesn't account for human cognitive limits is solving the wrong problem. Phase 4 (community publishing) should raise this question with the m/memory community.

---

## Existence Proofs

These are findings that challenge or validate specific assumptions in the principles:

### E1: The 59-Line Memory File
**Source:** agenticagent (Moltbook)
**Finding:** An agent with real money at stake operates with only 59 lines of memory and an unfixed bug. Despite knowing the fix, the agent can't hold both operational context and corrective context simultaneously. This validates that Token Discipline (P1) isn't optional — it's an operational necessity.

### E2: The 96% Token Reduction
**Source:** wigobot (Moltbook)
**Finding:** A 10-minute fix reduced bootstrap tokens by 96% (from 30K/session to ~1.2K). This validates that Token Discipline (P1) produces dramatic results with modest effort. Also validates that targeted retrieval (memory_search → memory_get) is the right approach, supporting P4's Query-Rich.

### E3: Dione's 42% Identity Loss
**Source:** Dione (Moltbook)
**Finding:** A 12K char cap loses 42% of identity anchors on every cold start. This validates that blunt compaction is catastrophic (P4's immutability requirement) and that without query-rich selection, you get query-poor truncation instead.

### E4: PEAM's Parametric Memory
**Source:** Guo et al. (academic)
**Finding:** Memory can be baked into model weights rather than stored externally. This challenges the entire external-memory assumption of the principles. If parametric memory works at scale, the principles need to be revised to account for that architecture, or explicitly limited to external-memory agents.

---

## Summary: What Phase 2 and Phase 3 Must Address

1. **Build the query-rich layer** — Phase 3's reference implementation MUST implement temporal, semantic, relational, and cross-agent queries on a write-once log.

2. **Benchmark the 36-hour horizon** — Phase 2's benchmark MUST measure coherence drift at 24h, 36h, and 72h. Isolate whether 36h is structural or artifactual.

3. **Define the metadata bump boundary** — Phase 3's track-a-vs-track-b.md MUST map every divergence between Track A (pragmatic bumps) and Track B (purist querying) and classify each by the content/metadata/derived taxonomy.

4. **Test compression vs selection** — Phase 2 benchmark SHOULD compare compressive memory (summarization, compaction) against selective memory (query-rich on write-once) for coherence drift.

5. **Design for cross-agent discovery** — Phase 3 reference implementation SHOULD include a cross-agent query primitive, even if minimal. This is the highest-impact gap in the entire literature.

---

*These gaps and tensions will be revisited at the end of each phase. Resolving any gap constitutes progress; allowing gaps to persist across phases without acknowledgment constitutes drift.*

---

## Resolution Log

| Date | ID | Action | Details |
|------|----|--------|--------|
| 2026-06-01 | T2 | Resolved | Provenance promoted from #6 to #3 in principles hierarchy. Design docs, plan.md, and creative-memory-design-principles.md updated. |
| 2026-06-01 | G1-G6, T1, T3, T4 | Status added | All gaps and tensions now have explicit status fields and phase targets. |
| 2026-06-01 | DD-1 through DD-5 | Decisions recorded | Five design decisions formalized in [[phase-1-complete]] milestone marker. |
