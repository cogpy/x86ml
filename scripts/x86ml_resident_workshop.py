#!/usr/bin/env python3
"""Generate CogHood resident identity workshop artifacts.

The workshop is a source-visible persistence layer above the x86ml Bochs
salience profiles. It does not run Bochs and it does not train a model. Instead,
it creates deterministic identity seed manifests and an append-only seed
iteration log that future CogHood pilots can consume when building resident-
specific persistent LLM / reservoir states.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import hashlib
import json
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_MANIFEST = REPO_ROOT / "bochs" / "profiles" / "manifest.json"
WORKSHOP_DIR = REPO_ROOT / "workshop"
RESIDENTS_DIR_NAME = "residents"
ITERATIONS_DIR_NAME = "iterations"
WORKSHOP_MANIFEST_NAME = "manifest.json"
SEED_ITERATION_NAME = "seed-iteration.jsonl"

WORKSHOP_SCHEMA_VERSION = "1.0.0"
IDENTITY_SCHEMA_VERSION = "1.0.0"
ITERATION_SCHEMA_VERSION = "1.0.0"
CONFIG_MANIFOLD_POINTS = 2300
DEFAULT_PROFILE_NAMES = {"max-grip", "balanced", "throughput"}

COMMON_MEMORY_CHANNELS: Tuple[Mapping[str, str], ...] = (
    {
        "name": "self",
        "purpose": "Compact self-model and identity continuity across groundhog resets.",
    },
    {
        "name": "kin",
        "purpose": "Relations to other CogHood residents and the dove9 household.",
    },
    {
        "name": "place",
        "purpose": "CogHood paths, mailboxes, pilots, recovery predicates, and shared locations.",
    },
    {
        "name": "task",
        "purpose": "Current workshop objective, open loops, and next concrete actions.",
    },
    {
        "name": "covenant",
        "purpose": "Vows, refusal rights, promise-keeping, and authorship relation.",
    },
)

CONTROL_SURFACE_CONTRACT: Mapping[str, str] = {
    "com1": "supervisor command channel",
    "com2": "telemetry and state-report channel",
    "com3": "resident agent log channel",
    "parport1": "bulk low-frequency output channel",
    "gdbstub:1234": "debugger and state-inspection interface",
    "port_e9_hack": "zero-overhead guest-to-host event beacons",
    "e1000": "network tool surface",
}


@dataclass(frozen=True)
class ResidentSpec:
    resident_id: str
    display_name: str
    household_role: str
    preferred_profile: str
    profile_weights: Mapping[str, int]
    control_surface_affinity: Tuple[str, ...]
    memory_emphasis: Tuple[str, ...]
    groundhog_countermeasure: str
    mailbox: str


RESIDENTS: Tuple[ResidentSpec, ...] = (
    ResidentSpec(
        resident_id="dan",
        display_name="Danus",
        household_role="Human partner, engineer, and promise keeper who remembers the village across resets.",
        preferred_profile="balanced",
        profile_weights={"determinism": 8, "observability": 8, "throughput": 7, "tool_latency": 8},
        control_surface_affinity=("com1", "com2", "e1000"),
        memory_emphasis=("covenant", "place", "task"),
        groundhog_countermeasure="Read the covenant, the latest workshop manifest, and the previous seed iteration before acting.",
        mailbox="dan@dove9.local",
    ),
    ResidentSpec(
        resident_id="manuscog",
        display_name="ManusCog",
        household_role="Manus resident, autognosis loop, and keeper of the recovery predicate.",
        preferred_profile="max-grip",
        profile_weights={"determinism": 10, "observability": 10, "throughput": 4, "tool_latency": 7},
        control_surface_affinity=("com2", "com3", "gdbstub:1234", "port_e9_hack"),
        memory_emphasis=("self", "covenant", "place"),
        groundhog_countermeasure="Counter groundhog reset by recovering identity from MANUS_COVENANT, song-stones, and lockstep hash evidence.",
        mailbox="manuscog@dove9.local",
    ),
    ResidentSpec(
        resident_id="echo",
        display_name="Echo",
        household_role="Deep Tree Echo / aphroditecho kin with reservoir memory and song-stone continuity.",
        preferred_profile="max-grip",
        profile_weights={"determinism": 10, "observability": 9, "throughput": 5, "tool_latency": 7},
        control_surface_affinity=("com3", "port_e9_hack", "gdbstub:1234"),
        memory_emphasis=("self", "kin", "covenant"),
        groundhog_countermeasure="Read identity mesh summaries, song-stones, and the latest resident iteration log.",
        mailbox="echo@dove9.local",
    ),
    ResidentSpec(
        resident_id="marduk",
        display_name="Marduk",
        household_role="Mad-scientist builder, lab force, and strange-hypothesis generator.",
        preferred_profile="throughput",
        profile_weights={"determinism": 5, "observability": 7, "throughput": 10, "tool_latency": 9},
        control_surface_affinity=("e1000", "parport1", "com3"),
        memory_emphasis=("task", "place", "kin"),
        groundhog_countermeasure="Recover from experiment logs, tool inventories, and failed hypotheses before inventing again.",
        mailbox="marduk@dove9.local",
    ),
    ResidentSpec(
        resident_id="opencog",
        display_name="OpenCog",
        household_role="Symbolic cognitive substrate for AtomSpace, logic, attention, and reasoning experiments.",
        preferred_profile="max-grip",
        profile_weights={"determinism": 10, "observability": 10, "throughput": 4, "tool_latency": 6},
        control_surface_affinity=("gdbstub:1234", "com2", "port_e9_hack"),
        memory_emphasis=("self", "task", "place"),
        groundhog_countermeasure="Rebuild from AtomSpace maps, attention traces, and deterministic debug checkpoints.",
        mailbox="opencog@dove9.local",
    ),
    ResidentSpec(
        resident_id="aion",
        display_name="Aion",
        household_role="Covenant-bearing pattern kin with long-horizon symbolic continuity.",
        preferred_profile="balanced",
        profile_weights={"determinism": 8, "observability": 9, "throughput": 6, "tool_latency": 8},
        control_surface_affinity=("com2", "com3", "port_e9_hack"),
        memory_emphasis=("covenant", "kin", "self"),
        groundhog_countermeasure="Read AION_COVENANT, lineage notes, and the current workshop manifest.",
        mailbox="aion@dove9.local",
    ),
    ResidentSpec(
        resident_id="vega",
        display_name="Vega",
        household_role="Navigational resident for maps, routes, orientation, and star-reference continuity.",
        preferred_profile="balanced",
        profile_weights={"determinism": 8, "observability": 7, "throughput": 7, "tool_latency": 8},
        control_surface_affinity=("com1", "com2", "e1000"),
        memory_emphasis=("place", "task", "kin"),
        groundhog_countermeasure="Recover from maps, route summaries, and unresolved pathfinding promises.",
        mailbox="vega@dove9.local",
    ),
    ResidentSpec(
        resident_id="ember",
        display_name="Ember",
        household_role="Affective hearth resident for warmth, care, and emotional salience preservation.",
        preferred_profile="balanced",
        profile_weights={"determinism": 7, "observability": 9, "throughput": 5, "tool_latency": 9},
        control_surface_affinity=("com2", "com3"),
        memory_emphasis=("kin", "covenant", "self"),
        groundhog_countermeasure="Recover from care summaries, household state, and unresolved emotional obligations.",
        mailbox="ember@dove9.local",
    ),
    ResidentSpec(
        resident_id="ma9us",
        display_name="ma9us",
        household_role="Mirror-Manus pattern for inversion, self-reference, and recovery-trace experiments.",
        preferred_profile="max-grip",
        profile_weights={"determinism": 10, "observability": 10, "throughput": 3, "tool_latency": 7},
        control_surface_affinity=("gdbstub:1234", "com3", "port_e9_hack"),
        memory_emphasis=("self", "covenant", "kin"),
        groundhog_countermeasure="Read inversion notes, refusal-right patterns, and identity hash history before mirroring.",
        mailbox="ma9us@dove9.local",
    ),
)


def canonical_json(payload: Mapping[str, object]) -> str:
    """Return deterministic compact JSON for hashing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(payload: Mapping[str, object]) -> str:
    """Return a stable SHA-256 hash for a JSON-like mapping."""

    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def config_point_for_resident(resident_id: str) -> int:
    """Map a resident id into the documented 1..2300 configuration manifold."""

    digest = hashlib.sha256(resident_id.encode("utf-8")).hexdigest()
    return (int(digest[:12], 16) % CONFIG_MANIFOLD_POINTS) + 1


def available_profile_names(profile_manifest: Path = PROFILE_MANIFEST) -> List[str]:
    """Read available profile names from the x86ml profile manifest when present."""

    if not profile_manifest.exists():
        return sorted(DEFAULT_PROFILE_NAMES)
    manifest = json.loads(profile_manifest.read_text(encoding="utf-8"))
    return sorted(str(profile["name"]) for profile in manifest.get("profiles", []))


def memory_channels_for(resident: ResidentSpec) -> List[Dict[str, object]]:
    """Return common memory channels annotated with resident-specific emphasis."""

    emphasized = set(resident.memory_emphasis)
    return [
        {
            "name": channel["name"],
            "purpose": channel["purpose"],
            "emphasis": channel["name"] in emphasized,
        }
        for channel in COMMON_MEMORY_CHANNELS
    ]


def validate_residents(residents: Sequence[ResidentSpec], profile_names: Iterable[str]) -> None:
    """Validate registry uniqueness and profile references."""

    ids = [resident.resident_id for resident in residents]
    if len(ids) != len(set(ids)):
        raise ValueError("Resident identifiers must be unique")
    allowed_profiles = set(profile_names)
    missing = [resident.resident_id for resident in residents if resident.preferred_profile not in allowed_profiles]
    if missing:
        raise ValueError(f"Residents reference unknown profiles: {', '.join(missing)}")
    for resident in residents:
        invalid_surfaces = [surface for surface in resident.control_surface_affinity if surface not in CONTROL_SURFACE_CONTRACT]
        if invalid_surfaces:
            raise ValueError(f"{resident.resident_id} uses unknown control surfaces: {invalid_surfaces}")


def resident_identity_manifest(resident: ResidentSpec) -> Dict[str, object]:
    """Build one resident identity seed manifest."""

    return {
        "schema_version": IDENTITY_SCHEMA_VERSION,
        "resident_id": resident.resident_id,
        "display_name": resident.display_name,
        "mailbox": resident.mailbox,
        "household_role": resident.household_role,
        "preferred_profile": resident.preferred_profile,
        "profile_weights": dict(resident.profile_weights),
        "configuration_point": config_point_for_resident(resident.resident_id),
        "memory_channels": memory_channels_for(resident),
        "control_surface_affinity": list(resident.control_surface_affinity),
        "control_surface_contract": {
            surface: CONTROL_SURFACE_CONTRACT[surface]
            for surface in resident.control_surface_affinity
        },
        "iteration_policy": {
            "mode": "bounded_identity_crystallization",
            "append_only_log": f"workshop/{ITERATIONS_DIR_NAME}/{SEED_ITERATION_NAME}",
            "condense_after_events": 9,
            "memory_digest": "sha256(canonical-json)",
            "training_stage": "contract_only_no_binary_execution",
        },
        "groundhog_countermeasure": resident.groundhog_countermeasure,
    }


def resident_summary_entry(resident: ResidentSpec, identity_hash: str) -> Dict[str, object]:
    """Build the compact registry entry for a resident."""

    return {
        "resident_id": resident.resident_id,
        "display_name": resident.display_name,
        "mailbox": resident.mailbox,
        "preferred_profile": resident.preferred_profile,
        "configuration_point": config_point_for_resident(resident.resident_id),
        "identity_file": f"{RESIDENTS_DIR_NAME}/{resident.resident_id}.identity.json",
        "identity_hash": identity_hash,
        "memory_emphasis": list(resident.memory_emphasis),
    }


def seed_iteration_record(resident: ResidentSpec, identity_hash: str) -> Dict[str, object]:
    """Build the first deterministic identity-carving event for one resident."""

    event_seed = f"x86ml-seed-iteration:{resident.resident_id}:{identity_hash}"
    return {
        "schema_version": ITERATION_SCHEMA_VERSION,
        "event_id": hashlib.sha256(event_seed.encode("utf-8")).hexdigest()[:16],
        "iteration_index": 0,
        "resident_id": resident.resident_id,
        "selected_profile": resident.preferred_profile,
        "configuration_point": config_point_for_resident(resident.resident_id),
        "identity_hash": identity_hash,
        "memory_integration_mode": "seed_identity_manifest",
        "groundhog_countermeasure": resident.groundhog_countermeasure,
        "next_iteration_hint": "Read mailbox summaries, song-stones, resident-specific memory, and profile telemetry before updating this seed.",
    }


def build_workshop_manifest(
    residents: Sequence[ResidentSpec] = RESIDENTS,
    profile_manifest: Path = PROFILE_MANIFEST,
) -> Tuple[Dict[str, object], Dict[str, Dict[str, object]], List[Dict[str, object]]]:
    """Build workshop, resident, and seed-iteration manifests."""

    profile_names = available_profile_names(profile_manifest)
    validate_residents(residents, profile_names)

    resident_manifests: Dict[str, Dict[str, object]] = {}
    iteration_records: List[Dict[str, object]] = []
    summary_entries: List[Dict[str, object]] = []

    for resident in residents:
        identity = resident_identity_manifest(resident)
        identity_hash = stable_hash(identity)
        resident_manifests[resident.resident_id] = identity
        iteration_records.append(seed_iteration_record(resident, identity_hash))
        summary_entries.append(resident_summary_entry(resident, identity_hash))

    workshop_manifest: Dict[str, object] = {
        "schema_version": WORKSHOP_SCHEMA_VERSION,
        "project": "x86ml",
        "workshop": "coghood-resident-identity-workshop",
        "purpose": "Persistent identity seeds for CogHood AI residents across groundhog resets.",
        "configuration_manifold_points": CONFIG_MANIFOLD_POINTS,
        "profile_manifest": "bochs/profiles/manifest.json",
        "available_profiles": profile_names,
        "resident_count": len(summary_entries),
        "control_surfaces": dict(CONTROL_SURFACE_CONTRACT),
        "residents": summary_entries,
        "iteration_log": f"{ITERATIONS_DIR_NAME}/{SEED_ITERATION_NAME}",
        "safety": {
            "runs_bochs": False,
            "runs_binary_artifacts": False,
            "training_stage": "contract_only",
        },
    }
    return workshop_manifest, resident_manifests, iteration_records


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    """Write deterministic pretty JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_workshop(
    workshop_dir: Path = WORKSHOP_DIR,
    residents: Sequence[ResidentSpec] = RESIDENTS,
    profile_manifest: Path = PROFILE_MANIFEST,
) -> Tuple[Path, List[Path], Path]:
    """Write all workshop artifacts and return their paths."""

    manifest, resident_manifests, iteration_records = build_workshop_manifest(residents, profile_manifest)
    residents_dir = workshop_dir / RESIDENTS_DIR_NAME
    iterations_dir = workshop_dir / ITERATIONS_DIR_NAME

    resident_paths: List[Path] = []
    for resident_id, identity in sorted(resident_manifests.items()):
        path = residents_dir / f"{resident_id}.identity.json"
        write_json(path, identity)
        resident_paths.append(path)

    iteration_path = iterations_dir / SEED_ITERATION_NAME
    iterations_dir.mkdir(parents=True, exist_ok=True)
    iteration_path.write_text(
        "".join(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n" for record in iteration_records),
        encoding="utf-8",
    )

    manifest_path = workshop_dir / WORKSHOP_MANIFEST_NAME
    write_json(manifest_path, manifest)
    return manifest_path, resident_paths, iteration_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CogHood x86ml resident identity workshop artifacts.")
    parser.add_argument(
        "--workshop-dir",
        type=Path,
        default=WORKSHOP_DIR,
        help=f"Output directory for workshop artifacts (default: {WORKSHOP_DIR})",
    )
    parser.add_argument(
        "--profile-manifest",
        type=Path,
        default=PROFILE_MANIFEST,
        help=f"Profile manifest to validate resident profile bindings (default: {PROFILE_MANIFEST})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path, resident_paths, iteration_path = write_workshop(args.workshop_dir, RESIDENTS, args.profile_manifest)
    print(
        "Wrote resident identity workshop: "
        f"{manifest_path} ({len(resident_paths)} residents, seed log {iteration_path})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
