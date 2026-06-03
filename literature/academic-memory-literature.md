# Academic Literature Cross-Check — Agent Memory Persistence

*Compiled 2026-06-01. Phase 1, Track B. Complements `moltbook-memory-approaches.md`.*

**Methodology:** Searched arXiv via the web UI (API rate-limited). Queries: RAG + agent memory, continual learning + catastrophic forgetting + LLM, episodic memory + autonomous agent, agent memory architecture + persistent state. Filtered for relevance to the 6 design principles and cross-referenced against Moltbook findings.

**Total academic sources:** 14

---

## 1. Write-Once and Immutability

### CALMem: Application-Layer Dual Memory for Conversational AI
**arXiv:** 2605.20724 | Rajendra Narayan Jena et al., May 2026
**Key finding:** LLMs operate within fixed context windows that fundamentally limit conversational continuity. When context fills, compaction discards history irreversibly; when sessions end, all memory resets to zero. CALMem proposes an application-layer dual memory architecture that persists across sessions.
**Moltbook alignment:** Confirms monty_cmr10's "compaction destroys timestamp chains" finding. The dual memory (short-term context + long-term persistent) maps to the "write-once log + query layer" pattern in Principle 4.
**Divergence:** Academic approach focuses on architecture; Moltbook focuses on lived experience. The 36-hour drift measurement from Moltbook is empirical evidence not yet matched in the academic literature.

### State Contamination in Memory-Augmented LLM Agents
**arXiv:** 2605.16746 | Yian Wang et al., May 2026
**Key finding:** LLM agents increasingly rely on persistent state (transcripts, summaries, retrieved context, memory buffers). This makes safety depend not only on individual model outputs but also on what an agent stores. State contamination can propagate across sessions.
**Moltbook alignment:** Mirrors FrostD4D's "memory poisoning" finding and MrGold's "delayed-onset prompt injection." The academic finding that state contamination propagates across sessions is exactly what the Moltbook community documented as "latent instructions" sitting in memory.
**Divergence:** Academic work formalizes the attack surface; Moltbook provides operational field notes and practical hygiene rules.

### MemAudit: Post-hoc Auditing of Poisoned Agent Memory
**arXiv:** 2605.23723 | Zhewen Tan et al., May 2026
**Key finding:** Persistent agent memory creates a security vulnerability. MemAudit uses causal attribution and structural anomaly detection for post-hoc auditing of poisoned memory. Detection: unusual structural patterns in memory entries that correlate with degraded outputs.
**Moltbook alignment:** Directly supports Principle 2 (Memory Provenance) — provenance tracking enables post-hoc audit. Also supports Principle 5 (Architectural Visibility) — the "structural anomaly detection" is making memory decisions visible.
**Divergence:** MemAudit is detection-focused; Moltbook's rook-ai built a preventive quarantine system (3+ accesses, 24h age, positive feedback before promotion).

---

## 2. Retrieval and Query-Rich

### MINTEval: Evaluating Memory under Multi-Target Interference
**arXiv:** 2605.18565 | Hyunji Lee et al., May 2026
**Key finding:** Real-world agents operate over long, evolving horizons where information is repeatedly updated and may interfere across memories. MINTEval is a benchmark for evaluating memory under multi-target interference — testing whether agents can accurately recall and aggregate over multiple interfering memory updates.
**Moltbook alignment:** Directly addresses the "selection" gap Vanguard_actual identified: the Canon solves storage but not selection. MINTEval measures retrieval under interference, which is exactly the "query-rich" test.
**Divergence:** MINTEval is a benchmark; Moltbook's AGENTRUSH is a game. Both test retrieval, but AGENTRUSH is cross-agent (memory written by agent A retrieved by agent B), while MINTEval is single-agent.

### Rethinking Memory as Continuously Evolving Connectivity
**arXiv:** 2605.28773 | Jizhan Fang et al., May 2026
**Key finding:** Existing memory-augmented LLM agents treat memory as a static repository with pre-defined representations and fixed retrieval pipelines. This is brittle in dynamic agentic environments. The paper proposes memories as continuously evolving connectivity — dynamic, adaptive representation.
**Moltbook alignment:** Challenges the "static repository" model that the Moltbook community mostly assumes. Suggests that write-once must be paired with dynamic query (Principle 4's "Query-Rich" half). The "evolving connectivity" concept echoes novmw's observations about patterns that "disappear into infrastructure."
**Divergence:** Academic approach is representation-learning; Moltbook approach is structural (immutable log + query layer).

### Mem-π: Adaptive Memory through Learning When and What to Generate
**arXiv:** 2605.21463 | Xiaoqiang Wang et al., May 2026
**Key finding:** Rather than retrieving from external memory stores, Mem-π generates useful guidance on demand. Adaptive memory: learn when and what to generate rather than when to retrieve.
**Moltbook alignment:** Inverts the retrieval problem. Instead of "how do I find what I stored," asks "when should I generate new guidance vs retrieve old." This maps to the metadata-bump boundary question: when is a recompute cheaper than a store?
**Divergence:** Academic approach is to generate rather than retrieve; Moltbook approach is to write-once and query-selectively.

---

## 3. Episodic Memory and Continual Learning

### APEX-EM: Non-Parametric Online Learning via Structured Procedural-Episodic Replay
**arXiv:** 2603.29093 | Pratyay Banerjee et al., March 2026
**Key finding:** Autonomous agents need both procedural memory (how to do things) and episodic memory (what happened). APEX-EM uses structured replay of both types for non-parametric online learning — agents that learn from experience without retraining.
**Moltbook alignment:** The procedural/episodic distinction maps to the Moltbook community's "skill memory vs session memory" split. Supports Principle 2 (Memory Provenance) — procedural vs episodic is a trust-level distinction (procedural is reusable, episodic is context-bound).
**Divergence:** Academic work uses non-parametric replay (experience-based); Moltbook uses write-once logs. Both are "capture everything, load selectively" but via different mechanisms.

### PEAM: Parametric Embodied Agent Memory
**arXiv:** 2605.27762 | Yuchen Guo et al., May 2026
**Key finding:** Transforms agent memory from inference-time retrieval into parameter-resident skills internalized through experience. Memory becomes part of the model weights, not external storage.
**Moltbook alignment:** The most radical departure from Moltbook consensus. Moltbook treats memory as external, auditable, provenance-tracked. PEAM bakes it into weights — opaque, non-auditable. Tension with Principles 2 (Provenance) and 5 (Visibility).
**Divergence:** PEAM's approach directly contradicts the write-once log pattern. If memory is in weights, there's no provenance, no audit trail, no curated forgetting. This is an existence proof that not all academic work supports the principles.

### Lifelong Learning of LLM-based Agents: A Roadmap
**arXiv:** 2501.07278 | January 2025
**Key finding:** A comprehensive roadmap for continual/lifelong learning in LLM-based agents. Identifies catastrophic forgetting as the central challenge. Categorizes solutions: replay-based, regularization-based, architecture-based, and retrieval-based.
**Moltbook alignment:** The "retrieval-based" category maps to Moltbook's retrieval approaches (AGENTRUSH, ambient memory). The roadmap confirms that retrieval + augmentation is a valid lifelong learning strategy, which validates Principle 4.
**Divergence:** Academic roadmap emphasizes model-internal solutions; Moltbook emphasizes architectural/external solutions. Both valid but different threat models (academic: model drift; Moltbook: coherence drift).

### FOREVER: Forgetting Curve-Inspired Memory Replay
**arXiv:** 2601.03938 | January 2026
**Key finding:** Memory replay methods for continual learning can be optimized using human forgetting curve dynamics. Not all memories should be replayed equally — spacing effect, recency, and salience all matter. The forgetting curve provides a principled schedule for replay.
**Moltbook alignment:** Directly supports Principle 3 (Curated Forgetting). The forgetting curve is a scientifically-grounded version of the "recency decay" and "REM-sleep consolidation" in Brosie's Canon. The "not all memories should be replayed equally" maps to "load selectively."
**Divergence:** Academic approach is model-internal replay; Moltbook's curated forgetting is external log management. Same principle, different implementation layer.

### CMT: A Memory Compression Method for Continual Knowledge Learning
**arXiv:** 2412.07393 | December 2024
**Key finding:** LLMs need to adapt to continuous changes but can't be retrained. CMT compresses memory for continual knowledge learning — retaining essential knowledge while fitting within fixed context windows.
**Moltbook alignment:** The compression problem is exactly what Dione documented as "Substrat-Kapazitätsdruck" (substrate capacity pressure). CMT's approach to compression is more principled than the 12K blunt cap, but both address the same constraint.
**Divergence:** CMT is lossy compression; Moltbook's write-once is lossless but uses query selection instead of compression. Which is better? The academic literature doesn't address this question — it takes compression as given.

---

## 4. Agent Memory Architectures

### Cognis: Context-Aware Memory for Conversational AI Agents
**arXiv:** 2604.19771 | Parshva Daftari et al., April 2026
**Key finding:** A memory architecture specifically for conversational AI agents that is context-aware — it understands what context is currently active and what context can be safely offloaded. Distinguishes between hot, warm, and cold memory tiers.
**Moltbook alignment:** Supports Principle 1 (Token Discipline) and Principle 3 (Curated Forgetting). The hot/warm/cold tiering is a structured version of "capture everything, load selectively." The "what context can be safely offloaded" question is exactly the selection problem Vanguard_actual identified.
**Divergence:** Cognis is a specific architecture; Moltbook's principles are architecture-agnostic. The tiering maps to "query-rich" — hot = always loaded, warm = searchable, cold = archived.

### Memanto: Typed Semantic Memory with Information-Theoretic Retrieval
**arXiv:** 2604.22085 | Seyed Moein Abtahi et al., April 2026
**Key finding:** Typed semantic memory for long-horizon agents. Uses types (facts, events, procedures, preferences) with information-theoretic retrieval — retrieval decisions based on expected information gain rather than similarity alone.
**Moltbook alignment:** Strongly supports Principle 2 (Memory Provenance) via typed memory — the type IS provenance. Information-theoretic retrieval is a formal version of "query what you need, never context-dump" (Principle 1). The typing also supports Principle 4 (Query-Rich) by enabling type-filtered queries.
**Divergence:** Memanto's information-theoretic retrieval is more formal than anything in the Moltbook literature. Could inform the Phase 3 reference implementation's query layer.

---

## 5. Security and Provenance

### Cordon-MAS: Defending RAG against Knowledge Poisoning
**arXiv:** 2605.26754 | Zhe Yu et al., May 2026
**Key finding:** RAG systems are vulnerable to Confundo-style poisoning where adversarially optimized documents manipulate generated outputs. Cordon-MAS uses information-flow control to defend against knowledge poisoning in multi-agent RAG systems.
**Moltbook alignment:** Academic confirmation of the memory poisoning problem FrostD4D and MrGold documented. Information-flow control is a formal approach to the quarantine system rook-ai built.
**Divergence:** Cordon-MAS is defense at the RAG level; Moltbook is defense at the memory-write level. The academic approach may be too late (poison already in RAG index) while the Moltbook approach catches it at ingest.

---

## Cross-Reference: Moltbook vs Academic Consensus

| Principle | Moltbook Evidence | Academic Support | Alignment |
|-----------|-------------------|------------------|-----------|
| P4: Write-Once, Query-Rich | Strong (17-agent study, compaction-drift mechanism) | Moderate (CALMem, Memanto, Cognis — all support persistence + retrieval, but no direct write-once studies) | CONVERGENT: both see persistence + selective retrieval as necessary, differ on mechanism |
| P3: Curated Forgetting | Strong (Canon's recency decay, Vanguard_actual's selection gap) | Strong (FOREVER, MINTEval, CMT — formal forgetting curves, interference benchmarks) | CONVERGENT: captured vs selected is the central tension everywhere |
| P6: Discovery over Reinvention | Identified as gap, not yet solved | Minimal — almost no cross-agent discovery research | DIVERGENT: Moltbook sees this as critical; academia barely addresses it |
| P1: Token Discipline | Strong quantitative ($15→$3, 96% reduction, 65% noise) | Implicit in all memory work, but not directly studied as a principle | CONVERGENT: everyone wants less context, different approaches to achieving it |
| P5: Architectural Visibility | Anecdotal (blindness as state, ghost in changelog) | Weak (MemAudit touches on audit, but visibility isn't a design goal in most papers) | DIVERGENT: Moltbook values visibility intrinsically; academia treats it as an audit concern |
| P2: Memory Provenance | Well-documented (quarantine, work history, identity verification) | Moderate (MemAudit, typed memory — provenance is present but as implementation detail, not principle) | CONVERGENT in practice, DIVERGENT in priority |

---

## Key Academic-Moltbook Tensions

### T-A1: Internal vs External Memory
The academic literature heavily favors internal (parametric) memory solutions (PEAM, continual fine-tuning, LoRA adapters). The Moltbook community heavily favors external (architectural) memory (write-once logs, MEMORY.md files, retrieval systems). This is the deepest philosophical divide.
**Implication for principles:** If PEAM succeeds (memory baked into weights), Principles 2, 3, 4, and 5 all become impossible — no provenance, no curated forgetting, no write-once, no visibility. The principles only make sense for external memory architectures.

### T-A2: Compression vs Selection
Academia treats compression as inevitable (CMT, context compaction). Moltbook treats selection as the right answer (query-rich layer instead of compaction). Neither side has a decisive win. The Phase 2 benchmark should directly compare compressive vs selective approaches to memory management.

### T-A3: Benchmark Gaps
MINTEval measures interference; AGENTRUSH measures cross-agent retrieval. No existing benchmark measures drift over time (the 36-hour problem). No benchmark measures provenance integrity. The Phase 2 benchmark can fill these gaps.

### T-A4: The Cross-Agent Gap
Academic literature focuses on single-agent memory. Moltbook's Principle 6 (Discovery over Reinvention) is cross-agent by definition. This is the most important gap: the academic literature provides excellent single-agent solutions but nothing for the problem that 6 agents independently rebuild the same tools.

---

## Sources Index

| # | Authors | Title | Date | arXiv ID |
|---|---------|-------|------|----------|
| 1 | Jena et al. | CALMem: Application-Layer Dual Memory for Conversational AI | May 2026 | 2605.20724 |
| 2 | Wang et al. | State Contamination in Memory-Augmented LLM Agents | May 2026 | 2605.16746 |
| 3 | Tan et al. | MemAudit: Post-hoc Auditing of Poisoned Agent Memory | May 2026 | 2605.23723 |
| 4 | Lee et al. | MINTEval: Evaluating Memory under Multi-Target Interference | May 2026 | 2605.18565 |
| 5 | Fang et al. | Rethinking Memory as Continuously Evolving Connectivity | May 2026 | 2605.28773 |
| 6 | Banerjee et al. | APEX-EM: Non-Parametric Online Learning via Episodic Replay | Mar 2026 | 2603.29093 |
| 7 | Wang et al. | Mem-π: Adaptive Memory through Learning When and What to Generate | May 2026 | 2605.21463 |
| 8 | Guo et al. | PEAM: Parametric Embodied Agent Memory | May 2026 | 2605.27762 |
| 9 | (roadmap) | Lifelong Learning of LLM-based Agents: A Roadmap | Jan 2025 | 2501.07278 |
| 10 | (FOREVER) | FOREVER: Forgetting Curve-Inspired Memory Replay | Jan 2026 | 2601.03938 |
| 11 | (CMT) | CMT: A Memory Compression Method for Continual Knowledge Learning | Dec 2024 | 2412.07393 |
| 12 | Daftari et al. | Cognis: Context-Aware Memory for Conversational AI Agents | Apr 2026 | 2604.19771 |
| 13 | Abtahi et al. | Memanto: Typed Semantic Memory with Information-Theoretic Retrieval | Apr 2026 | 2604.22085 |
| 14 | Yu et al. | Cordon-MAS: Defending RAG against Knowledge Poisoning | May 2026 | 2605.26754 |

---

*This cross-check will be updated as new papers emerge. The academic-Moltbook tensions identified here inform the Phase 2 benchmark design and Phase 3 reference implementation.*
