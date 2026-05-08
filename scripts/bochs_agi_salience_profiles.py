#!/usr/bin/env python3
"""Generate deterministic AGI salience profiles from bochs/agi.bochsrc.

The profile set operationalizes a "cognitive grip" tuning strategy across
high-salience Bochs controls:
  - temporal determinism
  - observability / introspection density
  - throughput
  - asynchronous tool responsiveness
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re
from typing import Dict


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = REPO_ROOT / "bochs" / "agi.bochsrc"
OUTPUT_DIR = REPO_ROOT / "bochs" / "profiles"


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


def apply_profile(base_text: str, profile: Profile) -> str:
    rendered = base_text
    for pattern, replacement in profile.replacements.items():
        rendered, count = re.subn(pattern, replacement, rendered, count=1, flags=re.MULTILINE)
        if count != 1:
            detail = "zero matches" if count == 0 else f"{count} matches"
            # Derive a lightweight directive prefix (e.g. "cpu:", "clock:")
            # from the regex pattern so we can print nearby matching lines.
            token = pattern.lstrip("^").split(" ")[0].replace(".*", "").replace("(?:\\n[", "")
            candidate_lines = []
            if token:
                candidate_lines = [
                    line for line in rendered.splitlines() if line.startswith(token)
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
        "# SOURCE: bochs/agi.bochsrc\n"
        "# Generated by scripts/bochs_agi_salience_profiles.py\n\n"
    )
    return header + rendered


def write_profiles(base_config: Path, output_dir: Path) -> None:
    base_text = base_config.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    for profile in PROFILES:
        output_text = apply_profile(base_text, profile)
        out_file = output_dir / f"agi-{profile.name}.bochsrc"
        out_file.write_text(output_text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate AGI salience profile bochsrc files."
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
    write_profiles(args.base_config, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
