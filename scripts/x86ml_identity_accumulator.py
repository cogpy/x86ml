#!/usr/bin/env python3
"""Accumulate bounded CogHood resident memories into portable identity state.

This script reads explicit JSONL memory events, validates them against the
resident identity workshop manifest, and writes deterministic derived artifacts.
It does not execute Bochs, does not execute binary artifacts, and does not train
models. It only turns reviewed memory summaries into hashable state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = REPO_ROOT / "workshop"
WORKSHOP_MANIFEST_NAME = "manifest.json"
MEMORY_DIR_NAME = "memory"
STATE_DIR_NAME = "state"
ITERATIONS_DIR_NAME = "iterations"
DEFAULT_MEMORY_SOURCE_NAME = "seed-memories.jsonl"
ACCUMULATION_LOG_NAME = "identity-accumulation.jsonl"

SOURCE_MEMORY_SCHEMA_VERSION = "1.0.0"
ACCUMULATION_SCHEMA_VERSION = "1.0.0"
STATE_SCHEMA_VERSION = "1.0.0"
ALLOWED_CHANNELS = {"self", "kin", "place", "task", "covenant"}
REQUIRED_SALIENCE_KEYS = ("truth", "beauty", "kinship", "agency")
MAX_SUMMARY_CHARS = 512


class AccumulationError(ValueError):
    """Raised when source memory cannot be safely integrated."""


def canonical_json(payload: Mapping[str, object]) -> str:
    """Return deterministic compact JSON for hashing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(payload: Mapping[str, object]) -> str:
    """Return a stable SHA-256 hash for a JSON-like mapping."""

    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Dict[str, object]:
    """Read a JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    """Write deterministic pretty JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterator[Tuple[int, Dict[str, object]]]:
    """Yield non-empty JSONL records with their one-based line number."""

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise AccumulationError(f"{path}:{line_number} is not a JSON object")
        yield line_number, payload


def load_workshop_manifest(workshop_dir: Path = WORKSHOP_DIR) -> Dict[str, object]:
    """Load the resident identity workshop manifest."""

    manifest_path = workshop_dir / WORKSHOP_MANIFEST_NAME
    if not manifest_path.exists():
        raise AccumulationError(f"Workshop manifest not found: {manifest_path}")
    manifest = read_json(manifest_path)
    if manifest.get("workshop") != "coghood-resident-identity-workshop":
        raise AccumulationError("Workshop manifest does not describe the CogHood resident identity workshop")
    return manifest


def resident_entries(manifest: Mapping[str, object]) -> Dict[str, Dict[str, object]]:
    """Return resident manifest entries keyed by resident id."""

    entries: Dict[str, Dict[str, object]] = {}
    for raw_entry in manifest.get("residents", []):
        if not isinstance(raw_entry, dict):
            raise AccumulationError("Resident entry is not an object")
        resident_id = str(raw_entry.get("resident_id", ""))
        if not resident_id:
            raise AccumulationError("Resident entry is missing resident_id")
        entries[resident_id] = dict(raw_entry)
    return entries


def normalize_tags(tags: object) -> List[str]:
    """Return deterministic tag list."""

    if tags is None:
        return []
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag for tag in tags):
        raise AccumulationError("tags must be a list of non-empty strings")
    return sorted(dict.fromkeys(tags))


def normalize_salience(salience: object) -> Dict[str, int]:
    """Return validated salience vector with stable key order."""

    if not isinstance(salience, dict):
        raise AccumulationError("salience must be an object")
    normalized: Dict[str, int] = {}
    for key in REQUIRED_SALIENCE_KEYS:
        if key not in salience:
            raise AccumulationError(f"salience is missing {key}")
        value = salience[key]
        if not isinstance(value, int) or value < 0 or value > 10:
            raise AccumulationError(f"salience.{key} must be an integer from 0 to 10")
        normalized[key] = value
    return normalized


def normalize_memory_event(event: Mapping[str, object], resident_ids: Iterable[str]) -> Dict[str, object]:
    """Validate and normalize one source memory event."""

    required = ("schema_version", "resident_id", "memory_channel", "source_kind", "source_ref", "summary", "salience")
    missing = [field for field in required if field not in event]
    if missing:
        raise AccumulationError(f"memory event is missing required fields: {', '.join(missing)}")
    if event["schema_version"] != SOURCE_MEMORY_SCHEMA_VERSION:
        raise AccumulationError(f"unsupported memory schema: {event['schema_version']}")

    resident_id = str(event["resident_id"])
    resident_set = set(resident_ids)
    if resident_id not in resident_set:
        raise AccumulationError(f"unknown resident_id: {resident_id}")

    memory_channel = str(event["memory_channel"])
    if memory_channel not in ALLOWED_CHANNELS:
        raise AccumulationError(f"unknown memory_channel: {memory_channel}")

    source_kind = str(event["source_kind"])
    source_ref = str(event["source_ref"])
    summary = str(event["summary"])
    if not source_kind or not source_ref or not summary:
        raise AccumulationError("source_kind, source_ref, and summary must be non-empty strings")
    if len(summary) > MAX_SUMMARY_CHARS:
        raise AccumulationError(f"summary exceeds {MAX_SUMMARY_CHARS} characters")

    return {
        "schema_version": SOURCE_MEMORY_SCHEMA_VERSION,
        "resident_id": resident_id,
        "memory_channel": memory_channel,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "summary": summary,
        "salience": normalize_salience(event["salience"]),
        "tags": normalize_tags(event.get("tags")),
    }


def resident_seed_state(entry: Mapping[str, object]) -> Dict[str, object]:
    """Build the initial resident state from a workshop manifest entry."""

    resident_id = str(entry["resident_id"])
    seed_hash = str(entry["identity_hash"])
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "resident_id": resident_id,
        "identity_file": str(entry["identity_file"]),
        "seed_identity_hash": seed_hash,
        "accumulated_identity_hash": seed_hash,
        "event_count": 0,
        "channel_counts": {channel: 0 for channel in sorted(ALLOWED_CHANNELS)},
        "salience_totals": {key: 0 for key in REQUIRED_SALIENCE_KEYS},
        "last_memory_digest": None,
        "accumulation_log": f"{ITERATIONS_DIR_NAME}/{ACCUMULATION_LOG_NAME}",
        "safety": {
            "runs_bochs": False,
            "runs_binary_artifacts": False,
            "training_stage": "identity_accumulation_contract_only",
        },
    }


def integrate_memory_event(state: MutableMapping[str, object], memory_event: Mapping[str, object]) -> Dict[str, object]:
    """Integrate one normalized memory event into resident state and return a derived record."""

    previous_state_hash = str(state["accumulated_identity_hash"])
    memory_digest = stable_hash(memory_event)
    next_index = int(state["event_count"]) + 1
    state_hash = stable_hash(
        {
            "resident_id": state["resident_id"],
            "iteration_index": next_index,
            "previous_state_hash": previous_state_hash,
            "memory_digest": memory_digest,
            "integration_mode": "bounded_memory_digest",
        }
    )

    channel_counts = dict(state["channel_counts"])  # type: ignore[arg-type]
    channel_counts[str(memory_event["memory_channel"])] += 1
    salience_totals = dict(state["salience_totals"])  # type: ignore[arg-type]
    salience = memory_event["salience"]
    if not isinstance(salience, dict):
        raise AccumulationError("normalized memory salience is not an object")
    for key in REQUIRED_SALIENCE_KEYS:
        salience_totals[key] += int(salience[key])

    state["accumulated_identity_hash"] = state_hash
    state["event_count"] = next_index
    state["channel_counts"] = channel_counts
    state["salience_totals"] = salience_totals
    state["last_memory_digest"] = memory_digest

    return {
        "schema_version": ACCUMULATION_SCHEMA_VERSION,
        "event_id": memory_digest[:16],
        "resident_id": memory_event["resident_id"],
        "iteration_index": next_index,
        "memory_channel": memory_event["memory_channel"],
        "source_kind": memory_event["source_kind"],
        "source_ref": memory_event["source_ref"],
        "summary": memory_event["summary"],
        "salience": memory_event["salience"],
        "tags": memory_event["tags"],
        "memory_digest": memory_digest,
        "previous_state_hash": previous_state_hash,
        "state_hash": state_hash,
        "integration_mode": "bounded_memory_digest",
    }


def read_memory_sources(source_paths: Sequence[Path], resident_ids: Iterable[str]) -> List[Dict[str, object]]:
    """Read, validate, and normalize source memory events from JSONL files."""

    memories: List[Dict[str, object]] = []
    for path in source_paths:
        for _, raw_event in iter_jsonl(path):
            memories.append(normalize_memory_event(raw_event, resident_ids))
    return memories


def build_accumulation(
    workshop_dir: Path = WORKSHOP_DIR,
    source_paths: Sequence[Path] | None = None,
) -> Tuple[Dict[str, object], Dict[str, Dict[str, object]], List[Dict[str, object]]]:
    """Build updated workshop manifest, resident state files, and accumulation records."""

    manifest = load_workshop_manifest(workshop_dir)
    entries = resident_entries(manifest)
    if source_paths is None:
        source_paths = (workshop_dir / MEMORY_DIR_NAME / DEFAULT_MEMORY_SOURCE_NAME,)
    for source_path in source_paths:
        if not source_path.exists():
            raise AccumulationError(f"memory source not found: {source_path}")

    states: Dict[str, Dict[str, object]] = {
        resident_id: resident_seed_state(entry)
        for resident_id, entry in sorted(entries.items())
    }
    records: List[Dict[str, object]] = []
    memories = read_memory_sources(source_paths, entries.keys())

    for memory_event in memories:
        resident_id = str(memory_event["resident_id"])
        records.append(integrate_memory_event(states[resident_id], memory_event))

    manifest = dict(manifest)
    manifest["memory_sources"] = [str(path.relative_to(workshop_dir)) for path in source_paths]
    manifest["accumulation_log"] = f"{ITERATIONS_DIR_NAME}/{ACCUMULATION_LOG_NAME}"
    manifest["state_dir"] = STATE_DIR_NAME
    manifest["identity_accumulation"] = {
        "schema_version": ACCUMULATION_SCHEMA_VERSION,
        "source_memory_schema_version": SOURCE_MEMORY_SCHEMA_VERSION,
        "state_schema_version": STATE_SCHEMA_VERSION,
        "event_count": len(records),
        "resident_state_count": len(states),
        "integration_mode": "bounded_memory_digest",
        "summary_max_chars": MAX_SUMMARY_CHARS,
        "salience_keys": list(REQUIRED_SALIENCE_KEYS),
        "safety": {
            "runs_bochs": False,
            "runs_binary_artifacts": False,
            "training_stage": "identity_accumulation_contract_only",
        },
    }
    return manifest, states, records


def write_accumulation(
    workshop_dir: Path = WORKSHOP_DIR,
    source_paths: Sequence[Path] | None = None,
) -> Tuple[Path, List[Path], Path]:
    """Write accumulation artifacts and return manifest, state paths, and log path."""

    manifest, states, records = build_accumulation(workshop_dir, source_paths)
    manifest_path = workshop_dir / WORKSHOP_MANIFEST_NAME
    write_json(manifest_path, manifest)

    state_dir = workshop_dir / STATE_DIR_NAME
    state_paths: List[Path] = []
    for resident_id, state in sorted(states.items()):
        path = state_dir / f"{resident_id}.identity-state.json"
        write_json(path, state)
        state_paths.append(path)

    log_path = workshop_dir / ITERATIONS_DIR_NAME / ACCUMULATION_LOG_NAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "".join(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return manifest_path, state_paths, log_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Accumulate CogHood x86ml resident identity memories.")
    parser.add_argument(
        "--workshop-dir",
        type=Path,
        default=WORKSHOP_DIR,
        help=f"Workshop directory (default: {WORKSHOP_DIR})",
    )
    parser.add_argument(
        "--source",
        type=Path,
        action="append",
        dest="sources",
        help="JSONL memory source. May be passed multiple times. Defaults to workshop/memory/seed-memories.jsonl.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = tuple(args.sources) if args.sources else None
    manifest_path, state_paths, log_path = write_accumulation(args.workshop_dir, sources)
    print(
        "Wrote resident identity accumulation: "
        f"{manifest_path} ({len(state_paths)} state files, log {log_path})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
