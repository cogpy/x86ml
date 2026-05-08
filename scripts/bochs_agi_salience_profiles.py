#!/usr/bin/env python3
"""Generate deterministic AGI salience profiles from ``bochs/agi.bochsrc``.

The profile set operationalizes a "cognitive grip" tuning strategy across
high-salience Bochs controls:

* temporal determinism
* observability / introspection density
* throughput
* asynchronous tool responsiveness

In addition to the rendered ``.bochsrc`` files, this module writes a
machine-readable ``manifest.json`` so downstream CogHood pilots and other
agents can reason about the profile contract without parsing comments.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import re
from typing import Dict, Iterable, List, Mapping, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = REPO_ROOT / "bochs" / "agi.bochsrc"
OUTPUT_DIR = REPO_ROOT / "bochs" / "profiles"
MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA_VERSION = "1.0.0"

# Normalized weighting over the profile's own salience dimensions. These are not
# project-wide architectural-grip weights; they are the local profile-selection
# weights used to rank an operating point for a concrete run.
SALIENCE_WEIGHTS: Mapping[str, float] = {
    "determinism": 1.4,
    "observability": 1.4,
    "throughput": 1.1,
    "tool_latency": 1.0,
}


@dataclass(frozen=True)
class Profile:
    name: str
    summary: str
    salience_vector: Dict[str, int]
    replacements: Dict[str, str]


CPU_MAX_GRIP = (
    'cpu: model=arrow_lake, count=1:4:2, quantum=1, ips=80000000, '
    'reset_on_triple_fault=1, ignore_bad_msrs=1, msrs="msrs.def"'
)
CPU_BALANCED = (
    'cpu: model=arrow_lake, count=1:4:2, quantum=10, ips=200000000, '
    'reset_on_triple_fault=1, ignore_bad_msrs=1, msrs="msrs.def"'
)
CPU_THROUGHPUT = (
    'cpu: model=arrow_lake, count=1:4:2, quantum=64, ips=400000000, '
    'reset_on_triple_fault=1, ignore_bad_msrs=1, msrs="msrs.def"'
)

PROFILES = (
    Profile(
        name="max-grip",
        summary="Maximum architecture-awareness salience and deterministic replay fidelity.",
        salience_vector={
            "determinism": 10,
            "observability": 10,
            "throughput": 3,
            "tool_latency": 7,
        },
        replacements={
            r"^cpu: model=.*(?:\n[ \t]+.*)?$": CPU_MAX_GRIP,
            r"^memory: .*$": "memory: guest=4096, host=3072, block_size=128",
            r"^vga: .*$": "vga: extension=vbe, update_freq=10, realtime=0, ddc=builtin_gui",
            r"^clock: .*$": "clock: sync=slowdown, time0=0, rtc_sync=0",
            r"^info: action=.*$": "info: action=report",
            r"^debug: action=.*$": "debug: action=report",
            r"^log: .*$": "log: bochs-agi-max-grip.log",
            r"^com3: .*$": "com3: enabled=1, mode=file, dev=max-grip-agent-log.jsonl",
            r"^e1000: .*$": 'e1000: enabled=1, mac=b0:c4:20:00:00:11, ethmod=vnet, ethdev="."',
        },
    ),
    Profile(
        name="balanced",
        summary="Balanced profile for mixed inference/training with strong introspection.",
        salience_vector={
            "determinism": 8,
            "observability": 8,
            "throughput": 7,
            "tool_latency": 8,
        },
        replacements={
            r"^cpu: model=.*(?:\n[ \t]+.*)?$": CPU_BALANCED,
            r"^memory: .*$": "memory: guest=4096, host=2048, block_size=128",
            r"^vga: .*$": "vga: extension=vbe, update_freq=30, realtime=1, ddc=builtin_gui",
            r"^clock: .*$": "clock: sync=slowdown, time0=0, rtc_sync=0",
            r"^info: action=.*$": "info: action=report",
            r"^debug: action=.*$": "debug: action=ignore",
            r"^log: .*$": "log: bochs-agi-balanced.log",
            r"^com3: .*$": "com3: enabled=1, mode=file, dev=balanced-agent-log.jsonl",
            r"^e1000: .*$": 'e1000: enabled=1, mac=b0:c4:20:00:00:21, ethmod=vnet, ethdev="."',
        },
    ),
    Profile(
        name="throughput",
        summary="High-throughput profile for large salience sweeps and broad search.",
        salience_vector={
            "determinism": 4,
            "observability": 5,
            "throughput": 10,
            "tool_latency": 9,
        },
        replacements={
            r"^cpu: model=.*(?:\n[ \t]+.*)?$": CPU_THROUGHPUT,
            r"^memory: .*$": "memory: guest=4096, host=1536, block_size=256",
            r"^vga: .*$": "vga: extension=vbe, update_freq=5, realtime=0, ddc=builtin_gui",
            r"^clock: .*$": "clock: sync=none, time0=0, rtc_sync=0",
            r"^info: action=.*$": "info: action=report",
            r"^debug: action=.*$": "debug: action=ignore",
            r"^log: .*$": "log: bochs-agi-throughput.log",
            r"^com3: .*$": "com3: enabled=1, mode=file, dev=throughput-agent-log.jsonl",
            r"^e1000: .*$": 'e1000: enabled=1, mac=b0:c4:20:00:00:31, ethmod=vnet, ethdev="."',
        },
    ),
)


def directive_token(pattern: str) -> str:
    """Return the target directive token for a replacement regex.

    Example: ``^clock: .*$`` becomes ``clock``. The CPU pattern includes a
    multiline continuation matcher, so this helper deliberately uses only the
    first directive-like token.
    """

    match = re.search(r"\^?([A-Za-z0-9_]+):", pattern)
    return match.group(1) if match else pattern


def profile_score(profile: Profile) -> float:
    """Return a normalized 0..1 salience score for a profile."""

    weighted = 0.0
    total_weight = 0.0
    for key, value in profile.salience_vector.items():
        weight = float(SALIENCE_WEIGHTS.get(key, 1.0))
        weighted += max(0, min(10, int(value))) * weight
        total_weight += 10.0 * weight
    if total_weight == 0.0:
        return 0.0
    return round(weighted / total_weight, 4)


def replacement_directives(profile: Profile) -> List[str]:
    """List the Bochs directives modified by a profile."""

    return [directive_token(pattern) for pattern in profile.replacements]


def profile_manifest_entry(profile: Profile) -> Dict[str, object]:
    """Build the manifest entry for one rendered profile."""

    return {
        "name": profile.name,
        "file": f"agi-{profile.name}.bochsrc",
        "summary": profile.summary,
        "salience_vector": dict(profile.salience_vector),
        "salience_score": profile_score(profile),
        "replacement_directives": replacement_directives(profile),
        "control_surfaces": {
            "supervisor_channel": "com1",
            "telemetry_channel": "com2",
            "agent_log_channel": "com3",
            "parallel_bulk_output": "parport1",
            "debug_stub": "gdbstub:1234",
            "zero_overhead_observation": "port_e9_hack",
            "network_tool_surface": "e1000",
        },
    }


def build_manifest(base_config: Path, output_dir: Path, profiles: Iterable[Profile] = PROFILES) -> Dict[str, object]:
    """Build a typed manifest for generated salience profiles."""

    profile_entries = [profile_manifest_entry(profile) for profile in profiles]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project": "x86ml",
        "base_config": str(base_config.relative_to(REPO_ROOT)),
        "profile_directory": str(output_dir.relative_to(REPO_ROOT)) if output_dir.is_relative_to(REPO_ROOT) else str(output_dir),
        "generator": "scripts/bochs_agi_salience_profiles.py",
        "salience_weights": dict(SALIENCE_WEIGHTS),
        "profile_count": len(profile_entries),
        "profiles": profile_entries,
    }


def apply_profile(base_text: str, profile: Profile) -> str:
    rendered = base_text
    for pattern, replacement in profile.replacements.items():
        rendered, count = re.subn(pattern, replacement, rendered, count=1, flags=re.MULTILINE)
        if count != 1:
            detail = "zero matches" if count == 0 else f"{count} matches"
            token = directive_token(pattern)
            candidate_lines = [
                line for line in rendered.splitlines() if line.startswith(f"{token}:")
            ][:3]
            context = " | ".join(candidate_lines) if candidate_lines else "no similar directive lines found"
            raise ValueError(
                "Failed to apply replacement for profile "
                f"'{profile.name}': {detail}; pattern={pattern!r}; replacement={replacement!r}; "
                f"context={context}"
            )

    vector = ", ".join(f"{k}={v}" for k, v in profile.salience_vector.items())
    header = (
        f"# GENERATED PROFILE: {profile.name}\n"
        f"# SUMMARY: {profile.summary}\n"
        f"# SALIENCE_VECTOR: {vector}\n"
        f"# SALIENCE_SCORE: {profile_score(profile):.4f}\n"
        "# SOURCE: bochs/agi.bochsrc\n"
        "# MANIFEST: bochs/profiles/manifest.json\n"
        "# Generated by scripts/bochs_agi_salience_profiles.py\n\n"
    )
    return header + rendered


def write_manifest(base_config: Path, output_dir: Path) -> Path:
    """Write ``manifest.json`` beside the generated profiles and return its path."""

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / MANIFEST_NAME
    manifest = build_manifest(base_config, output_dir)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def write_profiles(base_config: Path, output_dir: Path) -> Tuple[List[Path], Path]:
    base_text = base_config.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    for profile in PROFILES:
        output_text = apply_profile(base_text, profile)
        out_file = output_dir / f"agi-{profile.name}.bochsrc"
        out_file.write_text(output_text, encoding="utf-8")
        written.append(out_file)

    manifest_path = write_manifest(base_config, output_dir)
    return written, manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate AGI salience profile bochsrc files and a typed manifest."
    )
    parser.add_argument(
        "--base-config",
        type=Path,
        default=BASE_CONFIG,
        help=f"Base bochsrc file (default: {BASE_CONFIG})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory for generated profiles (default: {OUTPUT_DIR})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    written, manifest_path = write_profiles(args.base_config, args.output_dir)
    print(f"Wrote {len(written)} profiles and manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
