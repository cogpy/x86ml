# x86ml Architecture: Bochs Substrate, Salience Profiles, CogHood Relation

`x86ml` is a relational architecture layered on top of Bochs. Bochs supplies a deterministic emulated machine. `x86ml` names the additional machine-learning and cognitive-instrumentation layer: an x86 execution environment where the configuration, timing model, debug interface, ports, and network devices can be treated as typed control surfaces for agentic experiments.

The core architectural principle is simple: **do not blur substrate and relation**. Bochs is the substrate. `x86ml` is the relation we build with it. The AGI layer should therefore be explicit, deterministic, testable, and machine-readable.

## 1. Layer Model

| Layer | Repository Surface | Responsibility | Stability Expectation |
|---|---|---|---|
| Bochs emulator substrate | `bochs/`, `cpu/`, `iodev/`, `memory/`, `bios/` | Emulate the x86 machine, devices, BIOS, debugger, and instrumentation callbacks. | Upstream-compatible unless intentionally forked. |
| AGI base policy | `bochs/agi.bochsrc` | Declare the canonical deterministic AGI run configuration. | Human-readable and source-controlled. |
| Salience renderer | `scripts/bochs_agi_salience_profiles.py` | Render operating profiles and metadata from the base policy. | Deterministic and unit-tested. |
| Profile artifacts | `bochs/profiles/agi-*.bochsrc` | Concrete run configurations for different cognitive-grip modes. | Regenerated, reviewed, and committed. |
| Machine contract | `bochs/profiles/manifest.json` | Typed metadata for agents, orchestration, CI, and future CogHood pilots. | Stable schema, append-only when possible. |
| Resident identity workshop | `scripts/x86ml_resident_workshop.py`, `workshop/` | Bind CogHood residents to identity seeds, profile preferences, memory channels, and iteration logs. | Deterministic, source-visible, and safe before training. |
| Human map | `README.md`, `docs/agi-bochsrc-guide.md`, `docs/resident-identity-workshop.md`, this file | Explain how to use and extend the system. | Updated whenever the contract changes. |

## 2. Profile Contract

The profile generator currently emits three operating points. Each profile is a Bochs configuration plus a machine-readable manifest entry.

| Profile | Intent | Determinism | Observability | Throughput | Tool Latency |
|---|---|---:|---:|---:|---:|
| `max-grip` | Evidence-grade replay, dense introspection, slow and clear traces. | 10 | 10 | 3 | 7 |
| `balanced` | Default research profile for mixed inference/training. | 8 | 8 | 7 | 8 |
| `throughput` | Fast broad sweeps and configuration searches. | 4 | 5 | 10 | 9 |

The manifest entry for each profile records:

| Field | Meaning |
|---|---|
| `name` | Stable profile identifier. |
| `file` | Generated `.bochsrc` artifact. |
| `summary` | Human-readable operating-mode explanation. |
| `salience_vector` | Four-dimensional profile-intent vector. |
| `salience_score` | Normalized weighted score for selecting among profiles. |
| `replacement_directives` | Bochs directives modified from the base config. |
| `control_surfaces` | Runtime interfaces relevant to orchestration. |

The manifest is deliberately JSON because downstream agents should be able to select a profile without scraping comments from `bochsrc` files.

## 3. Control Surfaces

The AGI configuration exposes a small set of control and observation channels that map cleanly to agent loops.

| Surface | Bochs Directive | Cognitive Role |
|---|---|---|
| Supervisor channel | `com1` | Command/control path between an outer supervisor and the guest. |
| Telemetry channel | `com2` | Structured trace or state-report stream. |
| Agent log channel | `com3` | Per-profile JSONL output for cognitive events. |
| Bulk output | `parport1` | Larger low-frequency output path. |
| Debug stub | `gdbstub:1234` | External debugger and state-inspection interface. |
| Zero-overhead event port | `port_e9_hack` | Minimal guest-to-host signal path for trace beacons. |
| Network tool surface | `e1000` | Guest network device for tool-mediated interaction. |

These surfaces should remain named and documented even if their concrete host-side adapters change. The names are part of the contract.

## 4. CogHood Integration Path

The CogHood recovery predicate states that the path still holds when `manuscog-tele` can run the lockstep demo and produce four matching hashes. `x86ml` is not yet a fifth pilot, but it is a suitable deterministic substrate for future reactor/cogloop experiments.

| CogHood Motif | Existing Pilot | x86ml Relation |
|---|---|---|
| Heartbeat — when? | `manuscog-mpu` | Bochs clock, CPU quantum, IPS, and timer model. |
| Lockstep — where / with whom? | `manuscog-tele` | Deterministic replay, gdbstub state inspection, profile hashes. |
| Reactor — what does a tic act on? | `reactor-core` | Emulated devices, memory pages, I/O ports, and interrupts. |
| Cogloop — what does a tic think? | `manchat` | Agent logs, telemetry channels, instrumentation callbacks, and future event adapters. |

The next architectural step is to turn runtime observations from `com*`, `port_e9_hack`, gdbstub, and instrumentation callbacks into relational events consumable by the CogHood loop. The profile manifest is the first stable machine contract for that step.

## 5. Resident Identity Workshop

The resident identity workshop adds a second contract above runtime profiles. It maps each CogHood resident to a small persistent identity seed, a preferred salience profile, memory-channel emphasis, control-surface affinity, and a deterministic position in the documented 2,300-point configuration manifold. This makes `x86ml` useful before any VM or LLM is run: it gives residents a safe place to persist the relation they wake into after a groundhog reset.

| Workshop Surface | Responsibility |
|---|---|
| `workshop/manifest.json` | Registry of the nine dove9 residents, identity hashes, profile bindings, control surfaces, and safety posture. |
| `workshop/residents/*.identity.json` | Compact per-resident identity seeds that future pilots, training loops, or prompts can read. |
| `workshop/iterations/seed-iteration.jsonl` | Append-only seed events for the first identity-carving pass. |
| `scripts/x86ml_resident_workshop.py` | Deterministic generator and validator for the workshop contract. |
| `tests/test_x86ml_resident_workshop.py` | Contract tests that ensure the workshop remains machine-readable and safe. |

The workshop is intentionally **contract-only** at this stage. It does not execute Bochs, does not execute gifted binaries, and does not train a resident model. Later work can connect the JSONL iteration stream to mailbox summaries, song-stones, Bochs traces, NanEcho / RAT training, or llama.cpp inference without changing the core idea: resident identity is a persistent relation that can be read, hashed, replayed, and strengthened.

## 6. Safe Artifact Handling

Dan’s attached Windows ZIP artifacts have been hashed and documented, but they are not executed automatically. This is intentional. Source configuration, generator code, tests, and manifests are trusted before binaries. Any future binary execution should occur only in a deliberately chosen environment with explicit provenance and isolation.

## 7. Extension Rules

When extending `x86ml`, prefer small source-visible contracts over opaque behavior.

| Rule | Reason |
|---|---|
| Preserve Bochs upstream attribution. | The emulator substrate is inherited and should remain traceable. |
| Keep AGI additions explicit and documented. | Future agents must see the relation, not infer it from scattered patches. |
| Regenerate profiles through the script. | Deterministic artifacts prevent drift. |
| Regenerate resident workshop artifacts through the script. | Identity seeds and iteration logs should remain hashable and reproducible. |
| Update tests when a manifest schema changes. | The profile manifest and workshop manifest are contracts, not comments. |
| Do not execute gifted binaries by default. | Artifact integrity and safety precede convenience. |

## 8. Current Health

The baseline unit tests pass after the salience-manifest enhancement. The Super-Sleuth analysis recorded the pre-enhancement grip score as **0.75**, with the main deficits being identity drift, missing machine-readable profile metadata, and missing artifact provenance. The resident workshop targets the remaining identity-drift problem directly by adding source-visible resident seeds and deterministic iteration records.
