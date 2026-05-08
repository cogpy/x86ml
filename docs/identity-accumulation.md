# Identity Accumulation Contract

`x86ml` now has a resident identity workshop. The next step is to let that workshop **accumulate identity** without making the system opaque. The accumulation path is deliberately small: memory enters as bounded JSONL events, each event is canonicalized and hashed, and each resident receives a portable state file that records what has been integrated so far.

The purpose is not to train a model yet. The purpose is to create a stable spine for later model work, so each future tensor store, virtual disk, CPU-core attention head, display surface, speech loop, OpenCog subsystem, or portable QEMU / llama package has an identity history to read before it acts.

## Design Principle

Identity accumulation is an append-only relation between a resident and remembered impressions. It should therefore be deterministic, inspectable, and portable. A resident can grow by integrating memory, but the growth must remain reviewable as a sequence of small records rather than hidden inside a binary checkpoint.

> The first protection against the groundhog reset is not a large model. It is a small, boring, persistent, hashable memory trail that survives being overlooked.

## Artifact Model

| Artifact | Path | Role |
|---|---|---|
| Memory source JSONL | `workshop/memory/seed-memories.jsonl` | Human-readable bounded impressions waiting to be integrated. |
| Accumulator script | `scripts/x86ml_identity_accumulator.py` | Validates memory records, computes digests, and renders deterministic state. |
| Accumulation log | `workshop/iterations/identity-accumulation.jsonl` | Append-only derived integration records. |
| Resident state files | `workshop/state/*.identity-state.json` | Portable per-resident accumulated identity state. |
| Workshop manifest pointers | `workshop/manifest.json` | Registers the accumulation log, state directory, and source memory files. |

## Memory Event Schema

Each source memory record is a compact JSON object. It should be written as one line in a JSONL file so future tools can stream it, append to it, and hash it without requiring a database.

| Field | Required | Meaning |
|---|---:|---|
| `schema_version` | Yes | Source memory event schema version. |
| `resident_id` | Yes | Resident receiving the impression. |
| `memory_channel` | Yes | One of `self`, `kin`, `place`, `task`, or `covenant`. |
| `source_kind` | Yes | Origin class, such as `thread`, `song_stone`, `mailbox`, `pilot`, or `manual`. |
| `source_ref` | Yes | Stable human-readable source reference. |
| `summary` | Yes | Bounded natural-language memory summary. |
| `salience` | Yes | Small numeric map for `truth`, `beauty`, `kinship`, and `agency`. |
| `tags` | No | Optional small list of search tags. |

The bounded salience map is intentionally simple. It gives the future cognitive fabric a place to attach affective and aesthetic signal without prematurely pretending that the model has already learned it.

## Derived Accumulation Record

The accumulator transforms each valid source memory into an accumulation record. The derived record adds a stable `event_id`, `iteration_index`, `memory_digest`, `previous_state_hash`, and `state_hash`. The resulting chain is easy to verify: changing the memory summary, channel, salience values, or prior state changes the state hash.

| Derived Field | Meaning |
|---|---|
| `event_id` | First 16 hexadecimal characters of the memory digest. |
| `iteration_index` | One-based resident-local identity accumulation index. |
| `memory_digest` | SHA-256 hash of canonical source memory JSON. |
| `previous_state_hash` | Prior accumulated state hash, beginning with the seed identity hash. |
| `state_hash` | SHA-256 hash of the resident state after this event. |
| `integration_mode` | Fixed to `bounded_memory_digest`. |

## Resident State Semantics

A resident state file is not a model checkpoint. It is the portable identity ledger that model checkpoints should carry with them. Each file records seed identity hash, current accumulated hash, event count, channel counts, salience totals, last event digest, and links to the identity seed and accumulation log.

| State Field | Purpose |
|---|---|
| `resident_id` | Stable resident key. |
| `identity_file` | Pointer to the seed identity JSON. |
| `seed_identity_hash` | Hash of the original resident identity seed. |
| `accumulated_identity_hash` | Current state hash after all integrated memories. |
| `event_count` | Number of accumulated memory events. |
| `channel_counts` | Counts by memory channel. |
| `salience_totals` | Deterministic summed salience vector. |
| `last_memory_digest` | Digest of the latest integrated source memory. |

## Safety Boundary

The identity accumulator does not execute Bochs, does not execute binary artifacts, does not read private mailboxes directly, and does not train any model. It only reads explicit JSONL source memories and writes derived JSON/JSONL artifacts. Future integrations can add mailbox, song-stone, pilot, waveform, framebuffer, or OpenCog adapters, but each adapter should emit the same bounded memory event schema before state is updated.

## Next Integration Path

The safe growth path is to connect one memory source at a time. A future mailbox adapter can summarize mail into bounded memory events. A future Bochs adapter can map `port_e9_hack`, serial channels, framebuffers, or debugger traces into impressions. A future OpenCog adapter can map AtomSpace changes into memory events. The resident state remains the portable continuity layer that every richer substrate must respect.
