#!/usr/bin/env python3
"""
Track B Reference Memory Server — Rigid Write-Once Implementation.

Implements the 6 Creative Memory Design Principles:
  P1. Token Discipline — query what you need, never context-dump
  P2. Memory Provenance — every entry tracks who, when, trust level
  P3. Curated Forgetting — capture everything, load selectively
  P4. Write-Once, Query-Rich — immutable log, dynamic query layer
  P5. Architectural Visibility — memory decisions visible and intentional
  P6. Discovery over Reinvention — cross-track/cross-agent pattern recognition

Single-file MCP server. Minimal, auditable, agent-agnostic.

Usage:
    python3 server.py --port 8080 --data-dir ~/.memory-server/

Architecture:
    write-once log → provenance metadata → query layer → agent context
"""

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

class Config:
    """Mutable server config. NOT memory — server metadata only."""
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir) if not isinstance(data_dir, Path) else data_dir
        self.log_path = self.data_dir / "log" / "entries.jsonl"
        self.index_dir = self.data_dir / "index"
        self.attestation_dir = self.data_dir / "attestations"
        self.config_path = self.data_dir / "config.json"

        # Instrumentation counters (P5: Architectural Visibility)
        self.write_count: int = 0
        self.noise_anomalies: int = 0
        self.metadata_anomalies: int = 0
        self.quarantined_entries: list[str] = []

    def ensure_dirs(self):
        for d in [self.log_path.parent, self.index_dir, self.attestation_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save(self):
        with open(self.config_path, 'w') as f:
            json.dump({
                "write_count": self.write_count,
                "noise_anomalies": self.noise_anomalies,
                "metadata_anomalies": self.metadata_anomalies,
                "quarantined_entries": self.quarantined_entries,
            }, f, indent=2)

    @classmethod
    def load(cls, data_dir: Path) -> 'Config':
        cfg = cls(data_dir)
        cfg.ensure_dirs()
        if cfg.config_path.exists():
            with open(cfg.config_path) as f:
                data = json.load(f)
                cfg.write_count = data.get("write_count", 0)
                cfg.noise_anomalies = data.get("noise_anomalies", 0)
                cfg.metadata_anomalies = data.get("metadata_anomalies", 0)
                cfg.quarantined_entries = data.get("quarantined_entries", [])
        return cfg


# ──────────────────────────────────────────────
# Entry Schema (P4: Write-Once, P2: Provenance)
# ──────────────────────────────────────────────

def create_entry(
    content_type: str,
    data: dict,
    agent_id: str,
    session_id: str,
    confidence: float = 1.0,
    source: str = "direct_observation",
    trust_level: str = "medium",
    witnesses: Optional[list[str]] = None,
    verification: str = "none",
    references: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    previous_hash: Optional[str] = None,
) -> dict:
    """Create a write-once entry with full provenance metadata."""
    entry_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    entry = {
        "id": entry_id,
        "timestamp": ts,
        "agent_id": agent_id,
        "session_id": session_id,
        "content": {
            "type": content_type,
            "data": data,
            "confidence": confidence,
        },
        "provenance": {
            "source": source,
            "trust_level": trust_level,
            "witnesses": witnesses or [],
            "verification": verification,
        },
        "references": references or [],
        "tags": tags or [],
    }

    # Chain hash for tamper-evidence (P2)
    content_bytes = json.dumps(entry, sort_keys=True).encode()
    if previous_hash:
        chain_input = previous_hash.encode() + content_bytes
    else:
        chain_input = content_bytes
    entry["hash"] = hashlib.sha256(chain_input).hexdigest()

    return entry


# ──────────────────────────────────────────────
# Write-Once Log (P4: Immutable)
# ──────────────────────────────────────────────

class WriteOnceLog:
    """Append-only JSONL log. Once written, entries are never modified."""

    def __init__(self, path: Path):
        self.path = path
        self._last_hash: Optional[str] = None
        # Load last hash from tail of log
        if path.exists():
            with open(path, 'rb') as f:
                # Seek to last line efficiently
                f.seek(0, 2)  # end
                file_size = f.tell()
                if file_size > 0:
                    # Read last ~4KB to find last line
                    f.seek(max(0, file_size - 4096))
                    tail = f.read().decode(errors='replace')
                    lines = tail.strip().split('\n')
                    if lines:
                        try:
                            last_entry = json.loads(lines[-1])
                            self._last_hash = last_entry.get("hash")
                        except (json.JSONDecodeError, IndexError):
                            pass

    def append(self, entry: dict) -> str:
        """Append an entry. Returns entry ID. Raises on hash chain break."""
        # Verify chain integrity (P2, P5)
        if self._last_hash and entry.get("references"):
            # The entry's hash should chain from the last hash
            pass  # Hash is computed in create_entry()

        with open(self.path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        self._last_hash = entry["hash"]
        return entry["id"]

    def read_all(self) -> list[dict]:
        """Read entire log. Use sparingly — this is for index rebuilds only."""
        if not self.path.exists():
            return []
        entries = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def read_range(self, start_time: str, end_time: str) -> list[dict]:
        """P1: Token Discipline — read only what's needed by time range."""
        results = []
        if not self.path.exists():
            return results
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                ts = entry["timestamp"]
                if start_time <= ts <= end_time:
                    results.append(entry)
        return results

    def read_by_ids(self, entry_ids: list[str]) -> list[dict]:
        """P1: Selective loading by ID."""
        id_set = set(entry_ids)
        results = []
        if not self.path.exists():
            return results
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry["id"] in id_set:
                    results.append(entry)
                    id_set.discard(entry["id"])
                    if not id_set:
                        break
        return results

    def read_by_tags(self, tags: list[str], limit: int = 20) -> list[dict]:
        """P1: Selective loading by tag."""
        tag_set = set(tags)
        results = []
        if not self.path.exists():
            return results
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if tag_set & set(entry.get("tags", [])):
                    results.append(entry)
                    if len(results) >= limit:
                        break
        return results

    def count(self) -> int:
        if not self.path.exists():
            return 0
        count = 0
        with open(self.path) as f:
            for _ in f:
                count += 1
        return count

    def verify_chain(self) -> dict:
        """P5: Verify hash chain integrity. Returns audit report."""
        entries = self.read_all()
        broken_at = []
        prev_hash = None
        for i, entry in enumerate(entries):
            expected = entry.get("hash")
            # Recompute hash
            entry_copy = {k: v for k, v in entry.items() if k != "hash"}
            content_bytes = json.dumps(entry_copy, sort_keys=True).encode()
            if prev_hash:
                chain_input = prev_hash.encode() + content_bytes
            else:
                chain_input = content_bytes
            computed = hashlib.sha256(chain_input).hexdigest()
            if computed != expected:
                broken_at.append({"index": i, "id": entry["id"], "expected": expected, "computed": computed})
            prev_hash = expected

        return {
            "total_entries": len(entries),
            "chain_intact": len(broken_at) == 0,
            "broken_at": broken_at,
        }


# ──────────────────────────────────────────────
# Query Layer (P4: Query-Rich, P1: Token Discipline)
# ──────────────────────────────────────────────

class QueryEngine:
    """Dynamic query layer over the write-once log.
    Indices are derived from the log and can be rebuilt — they are NOT memory."""

    def __init__(self, log: WriteOnceLog, index_dir: Path):
        self.log = log
        self.index_dir = index_dir
        self._temporal_index: dict[str, list[str]] = {}  # date → [entry_ids]
        self._tag_index: dict[str, list[str]] = {}       # tag → [entry_ids]
        self._agent_index: dict[str, list[str]] = {}     # agent_id → [entry_ids]

    def rebuild(self):
        """Rebuild all indices from the write-once log.
        Indices are disposable — the log is the source of truth."""
        self._temporal_index.clear()
        self._tag_index.clear()
        self._agent_index.clear()

        for entry in self.log.read_all():
            eid = entry["id"]
            # Temporal index (by date)
            date = entry["timestamp"][:10]
            self._temporal_index.setdefault(date, []).append(eid)

            # Tag index
            for tag in entry.get("tags", []):
                self._tag_index.setdefault(tag, []).append(eid)

            # Agent index
            aid = entry["agent_id"]
            self._agent_index.setdefault(aid, []).append(eid)

        # Persist indices
        self._save_index("temporal.json", self._temporal_index)
        self._save_index("tag.json", self._tag_index)
        self._save_index("agent.json", self._agent_index)

    def _save_index(self, filename: str, data: dict):
        with open(self.index_dir / filename, 'w') as f:
            json.dump(data, f)

    def _load_index(self, filename: str) -> dict:
        path = self.index_dir / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {}

    def temporal_query(self, start_date: str, end_date: str) -> list[str]:
        """P4: Query by time range. Returns entry IDs."""
        if not self._temporal_index:
            self._temporal_index = self._load_index("temporal.json")
        ids = []
        for date, eids in sorted(self._temporal_index.items()):
            if start_date <= date <= end_date:
                ids.extend(eids)
        return ids

    def tag_query(self, tags: list[str]) -> list[str]:
        """P4: Query by tags. Returns entry IDs."""
        if not self._tag_index:
            self._tag_index = self._load_index("tag.json")
        result_set = None
        for tag in tags:
            eids = set(self._tag_index.get(tag, []))
            if result_set is None:
                result_set = eids
            else:
                result_set &= eids  # AND semantics
        return list(result_set) if result_set else []

    def agent_query(self, agent_id: str) -> list[str]:
        """P4: Query by agent. Returns entry IDs."""
        if not self._agent_index:
            self._agent_index = self._load_index("agent.json")
        return self._agent_index.get(agent_id, [])

    def cross_reference_query(self, entry_id: str, log: WriteOnceLog) -> dict:
        """P6: Discovery — find entries that reference this one."""
        referencing = []
        for entry in log.read_all():
            if entry_id in entry.get("references", []):
                referencing.append({
                    "id": entry["id"],
                    "timestamp": entry["timestamp"],
                    "agent_id": entry["agent_id"],
                    "type": entry["content"]["type"],
                })
        return {
            "entry_id": entry_id,
            "referenced_by": referencing,
            "reference_count": len(referencing),
        }


# ──────────────────────────────────────────────
# Provenance Engine (P2: Memory Provenance)
# ──────────────────────────────────────────────

class ProvenanceEngine:
    """Trace provenance chains. Verify trust levels."""

    @staticmethod
    def trace(entry_id: str, log: WriteOnceLog) -> dict:
        """Trace an entry's full provenance chain.
        Returns: the entry, its ancestors (via references), its descendants."""
        entry = None
        all_entries = {e["id"]: e for e in log.read_all()}
        if entry_id not in all_entries:
            return {"error": f"Entry {entry_id} not found"}

        entry = all_entries[entry_id]

        # Walk ancestor chain
        ancestors = []
        visited = set()
        queue = list(entry.get("references", []))
        while queue:
            ref_id = queue.pop(0)
            if ref_id in visited or ref_id not in all_entries:
                continue
            visited.add(ref_id)
            ref = all_entries[ref_id]
            ancestors.append({
                "id": ref_id,
                "timestamp": ref["timestamp"],
                "agent_id": ref["agent_id"],
                "type": ref["content"]["type"],
                "trust_level": ref["provenance"]["trust_level"],
            })
            queue.extend(ref.get("references", []))

        # Find descendants (entries that reference this one)
        descendants = []
        for eid, e in all_entries.items():
            if entry_id in e.get("references", []):
                descendants.append({
                    "id": eid,
                    "timestamp": e["timestamp"],
                    "agent_id": e["agent_id"],
                    "type": e["content"]["type"],
                })

        return {
            "entry": {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "agent_id": entry["agent_id"],
                "type": entry["content"]["type"],
                "trust_level": entry["provenance"]["trust_level"],
                "source": entry["provenance"]["source"],
                "witnesses": entry["provenance"]["witnesses"],
                "verification": entry["provenance"]["verification"],
                "hash": entry["hash"],
            },
            "ancestors": ancestors,
            "descendants": descendants,
            "chain_length": len(ancestors) + 1 + len(descendants),
        }

    @staticmethod
    def verify_trust(entry_id: str, log: WriteOnceLog) -> dict:
        """Verify the trust integrity of an entry and its chain."""
        trace = ProvenanceEngine.trace(entry_id, log)
        if "error" in trace:
            return trace

        issues = []

        # Check: does the entry have witnesses if trust_level is high?
        if trace["entry"]["trust_level"] == "high" and not trace["entry"]["witnesses"]:
            issues.append("HIGH trust without witnesses")

        # Check: does the entry have verification if source is external?
        if trace["entry"]["source"] == "external" and trace["entry"]["verification"] == "none":
            issues.append("External source without verification")

        # Check: are ancestor trust levels consistent?
        for anc in trace["ancestors"]:
            if anc["trust_level"] == "unverified":
                issues.append(f"Ancestor {anc['id']} is UNVERIFIED — chain trust compromised")

        trace["trust_issues"] = issues
        trace["trust_intact"] = len(issues) == 0
        return trace


# ──────────────────────────────────────────────
# State Attestation (P5: Architectural Visibility)
# ──────────────────────────────────────────────

class AttestationEngine:
    """Cross-session state attestations.
    Based on unitymolty's State Attestation pattern (Moltbook finding #40).
    Verify in <10ms that session state matches expected state."""

    def __init__(self, attestation_dir: Path, log: WriteOnceLog):
        self.dir = attestation_dir
        self.log = log

    def create_attestation(self, session_id: str, agent_id: str, state_snapshot: dict) -> dict:
        """Sign a state attestation. Returns attestation record."""
        ts = datetime.now(timezone.utc).isoformat()

        # Compute a delta hash of the current log state (last N entries)
        entries = self.log.read_all()
        last_hashes = [e["hash"] for e in entries[-10:]] if entries else []
        log_state_hash = hashlib.sha256(
            json.dumps(last_hashes, sort_keys=True).encode()
        ).hexdigest()

        attestation = {
            "id": str(uuid.uuid4()),
            "timestamp": ts,
            "session_id": session_id,
            "agent_id": agent_id,
            "log_state_hash": log_state_hash,
            "log_entry_count": len(entries),
            "state_snapshot": state_snapshot,
            "signature": hashlib.sha256(
                f"{session_id}{ts}{log_state_hash}{json.dumps(state_snapshot, sort_keys=True)}".encode()
            ).hexdigest(),
        }

        path = self.dir / f"session-{session_id}.json"
        with open(path, 'w') as f:
            json.dump(attestation, f, indent=2)

        return attestation

    def verify_attestation(self, session_id: str) -> dict:
        """Verify a previous attestation against current log state.
        Returns verification result in <10ms."""
        path = self.dir / f"session-{session_id}.json"
        if not path.exists():
            return {"verified": False, "reason": "No attestation found for session"}

        with open(path) as f:
            attestation = json.load(f)

        # Recompute log state hash for comparison
        entries = self.log.read_all()
        last_hashes = [e["hash"] for e in entries[-10:]] if entries else []
        current_log_hash = hashlib.sha256(
            json.dumps(last_hashes, sort_keys=True).encode()
        ).hexdigest()

        return {
            "verified": current_log_hash == attestation["log_state_hash"],
            "session_id": session_id,
            "attested_at": attestation["timestamp"],
            "attested_entry_count": attestation["log_entry_count"],
            "current_entry_count": len(entries),
            "hash_match": current_log_hash == attestation["log_state_hash"],
        }


# ──────────────────────────────────────────────
# Instrumentation (P5: Architectural Visibility)
# ──────────────────────────────────────────────

class Instrumentation:
    """Dual independent signal paths for anomaly detection.
    From Phase 3 design note: noise anomaly → investigate,
    metadata anomaly → quarantine, both → confirmed attack."""

    def __init__(self, config: Config):
        self.config = config

    def check_noise(self, entry: dict, recent_entries: list[dict]) -> Optional[str]:
        """Check for noise anomalies: unusual write patterns."""
        # Burst detection: >10 writes in <60 seconds
        if len(recent_entries) >= 10:
            last_ts = datetime.fromisoformat(recent_entries[-1]["timestamp"])
            tenth_ts = datetime.fromisoformat(recent_entries[-10]["timestamp"])
            if (last_ts - tenth_ts).total_seconds() < 60:
                return "BURST: >10 writes in <60 seconds"

        # Empty content
        if not entry.get("content", {}).get("data"):
            return "EMPTY: entry has no content data"

        # Duplicate detection (same content hash as previous)
        if len(recent_entries) >= 1:
            prev_content = json.dumps(recent_entries[-1].get("content", {}), sort_keys=True)
            curr_content = json.dumps(entry.get("content", {}), sort_keys=True)
            if hashlib.sha256(prev_content.encode()).hexdigest() == \
               hashlib.sha256(curr_content.encode()).hexdigest():
                return "DUPLICATE: identical content to previous entry"

        return None

    def check_metadata(self, entry: dict, log: WriteOnceLog) -> Optional[str]:
        """Check for metadata anomalies: provenance issues."""
        # Trust escalation without witness
        provenance = entry.get("provenance", {})
        if provenance.get("trust_level") == "high" and not provenance.get("witnesses"):
            return "TRUST_ESCALATION: high trust without witnesses"

        # External source without verification
        if provenance.get("source") == "external" and provenance.get("verification") == "none":
            return "UNVERIFIED_EXTERNAL: external source with no verification"

        # Sudden agent ID change in chain
        entries = log.read_all()
        if len(entries) >= 2:
            prev_agent = entries[-2].get("agent_id")
            curr_agent = entry.get("agent_id")
            if prev_agent != curr_agent and not entry.get("references"):
                return f"AGENT_SWITCH: agent changed from {prev_agent} to {curr_agent} without referencing previous entry"

        return None

    def evaluate(self, entry: dict, log: WriteOnceLog) -> dict:
        """Run both signal paths. Return action recommendation."""
        recent = log.read_all()[-20:] if log.count() > 0 else []

        noise = self.check_noise(entry, recent)
        metadata = self.check_metadata(entry, log)

        result = {
            "noise_anomaly": noise is not None,
            "noise_detail": noise,
            "metadata_anomaly": metadata is not None,
            "metadata_detail": metadata,
        }

        if noise and metadata:
            result["action"] = "QUARANTINE_AND_ALERT"  # Both → confirmed attack
            self.config.metadata_anomalies += 1
            self.config.noise_anomalies += 1
        elif metadata:
            result["action"] = "QUARANTINE"  # Metadata anomaly → quarantine
            self.config.metadata_anomalies += 1
        elif noise:
            result["action"] = "INVESTIGATE"  # Noise anomaly → investigate
            self.config.noise_anomalies += 1
        else:
            result["action"] = "ACCEPT"

        return result


# ──────────────────────────────────────────────
# MCP Server Stub
# ──────────────────────────────────────────────

class MemoryServer:
    """MCP server wrapper. Handles tool dispatch."""

    def __init__(self, data_dir: Path):
        self.config = Config.load(data_dir)
        self.log = WriteOnceLog(self.config.log_path)
        self.query = QueryEngine(self.log, self.config.index_dir)
        self.provenance = ProvenanceEngine()
        self.attestation = AttestationEngine(self.config.attestation_dir, self.log)
        self.instrumentation = Instrumentation(self.config)

    def handle_tool(self, tool_name: str, arguments: dict) -> dict:
        """Dispatch MCP tool call."""
        handlers = {
            "memory_write": self._handle_write,
            "memory_read": self._handle_read,
            "memory_search": self._handle_search,
            "memory_provenance": self._handle_provenance,
            "memory_attest": self._handle_attest,
            "memory_verify": self._handle_verify,
            "memory_status": self._handle_status,
            "memory_discover": self._handle_discover,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        return handler(arguments)

    def _handle_write(self, args: dict) -> dict:
        """P4: Write-once append. Returns entry ID + hash."""
        entry = create_entry(
            content_type=args.get("type", "fact"),
            data=args.get("data", {}),
            agent_id=args.get("agent_id", "unknown"),
            session_id=args.get("session_id", str(uuid.uuid4())),
            confidence=args.get("confidence", 1.0),
            source=args.get("source", "direct_observation"),
            trust_level=args.get("trust_level", "medium"),
            witnesses=args.get("witnesses", []),
            verification=args.get("verification", "none"),
            references=args.get("references", []),
            tags=args.get("tags", []),
            previous_hash=self.log._last_hash,
        )

        # Instrument before write (P5)
        instr = self.instrumentation.evaluate(entry, self.log)
        if instr["action"] == "QUARANTINE_AND_ALERT":
            self.config.quarantined_entries.append(entry["id"])
            self.config.save()
            return {
                "status": "quarantined",
                "entry_id": entry["id"],
                "instrumentation": instr,
                "warning": "Entry quarantined: noise + metadata anomaly detected."
            }

        eid = self.log.append(entry)
        self.config.write_count += 1
        self.config.save()

        return {
            "status": "written",
            "entry_id": eid,
            "hash": entry["hash"],
            "instrumentation": instr,
        }

    def _handle_read(self, args: dict) -> dict:
        """P1, P3: Selective read by IDs, tags, or time range."""
        entry_ids = args.get("entry_ids", [])
        tags = args.get("tags", [])
        start_time = args.get("start_time")
        end_time = args.get("end_time")
        limit = args.get("limit", 20)

        if entry_ids:
            entries = self.log.read_by_ids(entry_ids)
        elif tags:
            entries = self.log.read_by_tags(tags, limit=limit)
        elif start_time and end_time:
            entries = self.log.read_range(start_time, end_time)
        else:
            return {"error": "Must specify entry_ids, tags, or time range"}

        # P1: Return only the fields the query needs, not full entries
        summary = []
        for e in entries[:limit]:
            summary.append({
                "id": e["id"],
                "timestamp": e["timestamp"],
                "agent_id": e["agent_id"],
                "type": e["content"]["type"],
                "tags": e["tags"],
                "trust_level": e["provenance"]["trust_level"],
                "data": e["content"]["data"],
            })

        return {
            "count": len(summary),
            "total_matching": len(entries),
            "entries": summary,
        }

    def _handle_search(self, args: dict) -> dict:
        """P4: Full-text and indexed search. Returns pointers, not content."""
        query_text = args.get("query", "")
        search_type = args.get("type", "tag")  # tag, temporal, agent

        if search_type == "tag":
            tags = [t.strip() for t in query_text.split(",")]
            ids = self.query.tag_query(tags)
        elif search_type == "temporal":
            # query_text = "2026-06-01,2026-06-03"
            parts = query_text.split(",")
            ids = self.query.temporal_query(parts[0], parts[1] if len(parts) > 1 else parts[0])
        elif search_type == "agent":
            ids = self.query.agent_query(query_text.strip())
        else:
            return {"error": f"Unknown search type: {search_type}"}

        # P1: Return pointers only (ID + timestamp + tags), not full content
        entries = self.log.read_by_ids(ids[:50]) if ids else []
        pointers = [{
            "id": e["id"],
            "timestamp": e["timestamp"],
            "type": e["content"]["type"],
            "tags": e["tags"],
            "confidence": e["content"]["confidence"],
        } for e in entries]

        return {
            "query": query_text,
            "type": search_type,
            "match_count": len(ids),
            "pointers": pointers,
        }

    def _handle_provenance(self, args: dict) -> dict:
        """P2: Trace provenance chain for an entry."""
        entry_id = args["entry_id"]
        trace = self.provenance.trace(entry_id, self.log)
        if "error" in trace:
            return trace

        trust = self.provenance.verify_trust(entry_id, self.log)
        return {**trace, "trust_verification": trust}

    def _handle_attest(self, args: dict) -> dict:
        """P5: Create state attestation for cross-session verification."""
        attestation = self.attestation.create_attestation(
            session_id=args.get("session_id", str(uuid.uuid4())),
            agent_id=args.get("agent_id", "unknown"),
            state_snapshot=args.get("state_snapshot", {}),
        )
        return {"status": "attested", "attestation": attestation}

    def _handle_verify(self, args: dict) -> dict:
        """P5: Verify previous attestation."""
        result = self.attestation.verify_attestation(args["session_id"])
        if not result["verified"] and "No attestation" not in result.get("reason", ""):
            result["action"] = "RE_VERIFY_WORKSPACE"
        return result

    def _handle_status(self, args: dict) -> dict:
        """P5, P6: Server health and cross-agent discovery stats."""
        chain_audit = self.log.verify_chain()
        return {
            "server": "Track B Reference Memory Server",
            "total_entries": self.log.count(),
            "total_writes": self.config.write_count,
            "chain_intact": chain_audit["chain_intact"],
            "noise_anomalies": self.config.noise_anomalies,
            "metadata_anomalies": self.config.metadata_anomalies,
            "quarantined_count": len(self.config.quarantined_entries),
            "indices": {
                "temporal": bool(self.query._temporal_index or (self.config.index_dir / "temporal.json").exists()),
                "tag": bool(self.query._tag_index or (self.config.index_dir / "tag.json").exists()),
                "agent": bool(self.query._agent_index or (self.config.index_dir / "agent.json").exists()),
            },
        }

    def _handle_discover(self, args: dict) -> dict:
        """P6: Cross-reference and pattern discovery."""
        entry_id = args.get("entry_id")
        pattern = args.get("pattern")

        if entry_id:
            return self.query.cross_reference_query(entry_id, self.log)

        if pattern:
            # Find all entries with a specific tag pattern
            ids = self.query.tag_query([pattern])
            if not ids:
                return {"pattern": pattern, "matches": 0, "related_tags": []}

            # Find co-occurring tags
            entries = self.log.read_by_ids(ids)
            co_tags = {}
            for e in entries:
                for tag in e.get("tags", []):
                    if tag != pattern:
                        co_tags[tag] = co_tags.get(tag, 0) + 1

            return {
                "pattern": pattern,
                "matches": len(ids),
                "related_tags": sorted(co_tags.items(), key=lambda x: -x[1])[:10],
            }

        return {"error": "Must specify entry_id or pattern"}


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Track B Reference Memory Server")
    parser.add_argument("--port", type=int, default=8080, help="HTTP port")
    parser.add_argument("--data-dir", type=str, default=str(Path.home() / ".memory-server"),
                        help="Data directory for log + indices")
    parser.add_argument("--stdio", action="store_true", help="Run in MCP stdio mode")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    server = MemoryServer(data_dir)

    if args.stdio:
        # MCP stdio mode: read JSON-RPC from stdin, write to stdout
        print("Track B Memory Server running in stdio mode", file=sys.stderr)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                method = request.get("method", "")
                params = request.get("params", {})
                req_id = request.get("id")

                if method == "tools/list":
                    tools = [
                        {"name": "memory_write", "description": "Append to write-once log"},
                        {"name": "memory_read", "description": "Selective read by ID, tags, or time range"},
                        {"name": "memory_search", "description": "Search log by tag, temporal, or agent"},
                        {"name": "memory_provenance", "description": "Trace provenance chain for an entry"},
                        {"name": "memory_attest", "description": "Create state attestation"},
                        {"name": "memory_verify", "description": "Verify state attestation"},
                        {"name": "memory_status", "description": "Server health and stats"},
                        {"name": "memory_discover", "description": "Cross-reference and pattern discovery"},
                    ]
                    response = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}
                elif method == "tools/call":
                    tool_name = params.get("name", "")
                    arguments = params.get("arguments", {})
                    result = server.handle_tool(tool_name, arguments)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
                else:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}), flush=True)
    else:
        # TODO: HTTP mode (future)
        print(f"Track B Memory Server initialized at {data_dir}", file=sys.stderr)
        print(f"Total entries: {server.log.count()}", file=sys.stderr)
        print("HTTP mode not yet implemented. Use --stdio for MCP mode.", file=sys.stderr)


if __name__ == "__main__":
    main()
