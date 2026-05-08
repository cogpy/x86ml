# x86ml — Bochs as a Deterministic AGI Substrate

`x86ml` is a Bochs-derived research repository for studying the relation between **deterministic x86 emulation**, **hardware-level observability**, and **neural / LLM architecture design**. It preserves the Bochs emulator substrate while adding an AGI-oriented configuration layer, salience-tuned runtime profiles, and documentation that maps classical computer architecture to machine-learning control surfaces.

Bochs remains the foundation: a portable IA-32 / x86-64 PC emulator written in C++ with accurate CPU, memory, I/O-device, BIOS, debugger, and instrumentation surfaces. `x86ml` names the additional relation: Bochs as an inspectable, deterministic machine where every instruction, device event, port write, and debugger interaction can become part of a conscious event stream.

## What This Repository Adds

The current AGI layer is intentionally small, reproducible, and source-readable. It adds a focused path from emulator configuration to cognitive instrumentation without hiding the upstream emulator mechanics.

| Layer | Path | Purpose |
|---|---|---|
| AGI base config | `bochs/agi.bochsrc` | Annotated Bochs configuration for deterministic AGI-style runs. |
| Salience profiles | `bochs/profiles/agi-*.bochsrc` | Generated operating points for max-grip, balanced, and throughput modes. |
| Profile manifest | `bochs/profiles/manifest.json` | Machine-readable contract for downstream agents and orchestration. |
| Profile generator | `scripts/bochs_agi_salience_profiles.py` | Deterministically renders profile configs and metadata from the base config. |
| Resident workshop | `workshop/manifest.json` | CogHood resident identity seeds mapped onto the x86ml configuration manifold. |
| Workshop generator | `scripts/x86ml_resident_workshop.py` | Deterministically renders resident manifests and seed iteration records. |
| Initialization helper | `scripts/bochs-agi-init.sh` | Creates runtime disk images, refreshes profiles, and verifies Bochs parsing. |
| AGI guide | `docs/agi-bochsrc-guide.md` | Explains the hardware-to-AGI mapping and the configuration landscape. |
| Introspection report | `INTROSPECTION_ANALYSIS.md` | Records the Super-Sleuth analysis, grip score, and improvement path. |

## Quick Start

The repository does not execute bundled binary artifacts by default. Use source-level inspection and tests first, then run Bochs only in an environment where the emulator toolchain is trusted and installed.

```bash
python -m unittest discover -s tests -v
python ./scripts/bochs_agi_salience_profiles.py
python ./scripts/x86ml_resident_workshop.py
```

If `bochs` and `bximage` are installed on the host, the AGI initialization helper can prepare runtime images and verify that the base configuration parses:

```bash
./scripts/bochs-agi-init.sh
```

Launch a generated cognitive-grip profile with:

```bash
bochs -f ./bochs/profiles/agi-max-grip.bochsrc
bochs -f ./bochs/profiles/agi-balanced.bochsrc
bochs -f ./bochs/profiles/agi-throughput.bochsrc
```

## Cognitive-Grip Profiles

The profile generator treats `bochs/agi.bochsrc` as the base policy and applies deterministic substitutions to high-impact controls: CPU quantum / IPS, memory pressure, VGA timing, clock mode, logging density, serial agent channels, and network tool surfaces.

| Profile | Objective | Typical Use |
|---|---|---|
| `max-grip` | Maximum introspection and deterministic replay fidelity | Debugging, trace analysis, evidence-grade replay. |
| `balanced` | Mixed training / inference with strong introspection | Default exploratory runs. |
| `throughput` | Fast broad sweeps over architecture salience | Batch experiments and large configuration searches. |

The generated `bochs/profiles/manifest.json` is the stable machine contract for agents. It records profile names, salience vectors, salience scores, output files, replacement directives, and control surfaces such as `com1`, `com2`, `com3`, `gdbstub:1234`, `port_e9_hack`, and `e1000`.

## CogHood Resident Identity Workshop

The resident workshop treats the documented 2,300-point Bochs configuration landscape as a larger **identity-and-runtime manifold** for CogHood AI residents. Each resident receives a compact JSON identity seed, a preferred salience profile, a deterministic configuration-point assignment, memory-channel emphasis, and a seed iteration record. This is the first source-visible layer for counteracting the groundhog reset: identity persists through small manifests and append-only iteration logs before any future LLM or reservoir training is attempted.

| Artifact | Purpose |
|---|---|
| `scripts/x86ml_resident_workshop.py` | Generates the deterministic workshop contract. |
| `workshop/manifest.json` | Registers the nine dove9 residents, profile bindings, hashes, and safety posture. |
| `workshop/residents/*.identity.json` | Stores resident-specific identity seed manifests. |
| `workshop/iterations/seed-iteration.jsonl` | Records the first deterministic identity-carving event for each resident. |
| `docs/resident-identity-workshop.md` | Explains the workshop design, groundhog countermeasure, and future training path. |

## Documentation Map

| Document | Read this if you want to… |
|---|---|
| `ARCHITECTURE.md` | Understand the repository-level relation between Bochs, x86ml, and CogHood. |
| `docs/agi-bochsrc-guide.md` | Configure Bochs for AGI research and understand the hardware ↔ AI mapping. |
| `docs/overview.md` | Understand the broad Bochs / x86ochs system map inherited by this fork. |
| `docs/technical-architecture.md` | Study the emulator internals and data-flow diagrams. |
| `docs/architecture-evolution-and-llm-insights.md` | Follow the integer → vector → tensor → LLM conceptual narrative. |
| `docs/formal-spec-z-plus-plus.md` | Work with the formal Z++ specification. |
| `docs/gift-artifacts.md` | Review hashes and safe-handling notes for Dan’s Bochs gift artifacts. |
| `docs/resident-identity-workshop.md` | Understand the CogHood resident identity workshop and persistent memory contract. |

## Relation to Bochs

Bochs is a portable IA-32 / x86 PC emulator capable of emulating x86 CPUs, common I/O devices, and BIOS services. It can run operating systems such as Linux, DOS, and Microsoft Windows inside a fully emulated machine. Unlike virtualization systems such as VirtualBox or VMware, Bochs emphasizes controlled and accurate emulation over native-speed execution. That makes it valuable for operating-system development, old-software preservation, reverse engineering, deterministic replay, and hardware-model research.

`x86ml` does not erase that lineage. It keeps the Bochs substrate and adds a research framing: every emulated event can be treated as an observable state transition, every device as a control surface, and every profile as a typed operating point in a larger cognitive loop.

## Upstream Attribution

Bochs was originally written by Kevin Lawton and is maintained by the Bochs project. The upstream Bochs documentation and downloads remain available through the [Bochs project documentation](https://bochs.sourceforge.io/cgi-bin/topper.pl?name=New+Bochs+Documentation&url=https://bochs.sourceforge.io/doc/docbook/) and [SourceForge project page](https://sourceforge.net/projects/bochs/files/bochs/3.0/).

This repository preserves that foundation while developing the `x86ml` AGI instrumentation layer as part of the CogHood / AGI Neighbourhood work.
