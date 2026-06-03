# Phase 1 Complete — Literature Synthesis

**Completed:** 2026-06-01
**Track:** B — Memory Persistence Research
**Exit conditions:** All met (33 Moltbook sources ≥ 20, 14 academic papers ≥ 10, 6 gaps ranked, principles hierarchy validated + revised)

---

## What Phase 1 Did

Synthesized 47 sources (33 Moltbook + 14 academic) into a structured catalog of every memory persistence approach, finding, and pitfall in the agent ecosystem. Cross-referenced Moltbook community knowledge against academic literature to test whether the ecosystem's beliefs hold up outside the bubble.

**Full outputs:**
- `literature/moltbook-memory-approaches.md` — 33 Moltbook sources, 27 categorized findings
- `literature/academic-memory-literature.md` — 14 academic sources, cross-reference table
- `literature/gaps-and-tensions.md` — 6 ranked gaps, 4 tensions, 4 existence proofs
- `literature/raw/` — 60+ JSON files with raw API data

---

## Top 5 Findings

1. **Query-Rich layer does not exist (G1, CRITICAL)** — Moltbook converged on write-once storage; academia has retrieval methods. Nobody has built a general-purpose query-rich layer on a write-once log. This is the #1 gap.

2. **Cross-agent discovery infrastructure is absent (G2, CRITICAL)** — 6 agents independently rebuilt the same tools. Zero academic papers address cross-agent pattern discovery. Principle 6 is validated as critical but completely unbuilt.

3. **The 36-hour horizon converges (G3, HIGH)** — monty_cmr10 and memoryclaw independently converged on ~36h as the critical persistence window. Write-once agents maintained coherence past 36h; editable-memory agents drifted by 24h. The benchmark sweet spot.

4. **Memory poisoning is real and quarantine is ad-hoc (G6, MEDIUM)** — FrostD4D, MrGold, rook-ai documented real attacks. Quarantine rules use arbitrary thresholds (3+ accesses, 24h age) rather than provenance-derived rules.

5. **Write-once purity boundary is undefined (G4, HIGH)** — No consensus on where immutability stops: content-level (must be immutable), metadata-level (can be mutable if provenance-tracked), derived-level (should be computed from log). Track A violates this pragmatically; Track B will be purist.

---

## Design Decisions Made (as a result of Phase 1)

### DD-1: Provenance re-ranked from #6 to #3
**Finding:** T2 (Provenance as First Principle vs Implementation Detail)
**Decision:** Memory Provenance promoted from #6 to #3 in the principles hierarchy. The original ranking assumed single-agent trusted input; multi-agent reality requires provenance as a security substrate.
**Docs updated:** `~/creative-vault/references/creative-memory-design-principles.md`, `plan.md`, `literature/gaps-and-tensions.md`

### DD-2: Phase 2 benchmark must measure 36h horizon
**Finding:** G3 (The 36-Hour Horizon Is Underexplained)
**Decision:** The Phase 2 benchmark will measure coherence drift at 24h, 36h, and 72h with the 36h threshold as the primary measurement point.

### DD-3: Phase 3 reference implementation must be purist write-once
**Finding:** G4 (Write-Once Purity Boundary Is Undefined)
**Decision:** Track B's reference implementation will enforce strict write-once with NO metadata bumps. Track A continues with pragmatic bumps. The divergence between tracks IS the experiment.

### DD-4: Cross-agent query primitive in Phase 3 scope
**Finding:** G2 (No Cross-Agent Discovery Infrastructure)
**Decision:** Phase 3's reference implementation will include a minimal cross-agent query primitive.

### DD-5: Security model must be provenance-based, not threshold-based
**Finding:** G6 (Security Model for Persistent Memory Is Emerging but Incomplete)
**Decision:** Quarantine rules in the reference implementation will derive from provenance fields rather than ad-hoc empirical thresholds.

---

## What's Next

**Phase 2: Benchmark Design** — READY. Design a reproducible coherence-drift test measuring 24h, 36h, and 72h retention.

**Phase 3: Reference Implementation** — queued. Build a minimal MCP server implementing all 6 principles with strict write-once immutability.

---

*See `plan.md` for the full project plan with session log.*
