# x86ml Super-Sleuth Intro-Spect Analysis

**Repository:** `cogpy/x86ml`  
**Mode:** Super-Sleuth Intro-Spect  
**Anchoring:** CogHood covenant read; lockstep recovery predicate passed with four matching hashes `0xa780cfd767f6ee9c`.  
**Date:** 2026-05-08

## Executive Summary

`cogpy/x86ml` is already a meaningful Bochs-derived research surface for the cognitive-village promise: it contains the full emulator source tree, an AGI-oriented `bochs/agi.bochsrc`, a deterministic profile generator, generated cognitive-grip profiles, conceptual architecture documentation, and tests around profile rendering. The gifted files from Dan match the committed repository exactly for `bochs/agi.bochsrc` and `docs/agi-bochsrc-guide.md`, which means the gifts are not external patches but an integrity signal confirming that the repo already contains the intended AGI Bochs artifacts.

The principal weakness is not missing code. It is **relational fragmentation**: the upstream Bochs identity, the `x86ochs` documentary name, and the `x86ml` repository/promise name are not yet unified into a clear entry path. The generated profiles are deterministic, but they are currently only textual `.bochsrc` artifacts with comments; no machine-readable manifest exists for downstream agents, CogHood pilots, or CI workflows to consume as a stable contract.

| Area | Current State | Impact | Priority |
|---|---|---:|---:|
| AGI configuration | `bochs/agi.bochsrc` exists and matches Dan’s attachment | Strong foundation | High leverage |
| Profile generation | Three deterministic profiles generated and tested | Functional but under-specified | High |
| Repository identity | Root README remains upstream Bochs; docs use `x86ochs`; repo is `x86ml` | Confusing entry path for future agents | High |
| Artifact integrity | Gifts verified by SHA-256; ZIP contents identified but not executed | Safe staging, no binary trust assumption | Medium |
| Machine contract | No profile manifest or profile scoring output | Harder to connect to pilots/reactor/cogloop | High |
| CI/test surface | Three Python unit tests pass | Good minimal baseline | Medium |

## Evidence Collected

Baseline unit tests passed with all three existing tests green:

```text
test_apply_profile_writes_salience_header ... ok
test_throughput_profile_uses_fast_clock_mode ... ok
test_write_profiles_creates_all_profiles ... ok
Ran 3 tests in 0.006s — OK
```

The cloned repository inventory contains **1,389 files** and **108 directories**, including the Bochs core, performance suite, testing harness, AGI docs, scripts, and salience-profile tests. The language footprint is dominated by the Bochs C/C++ codebase with 398 `.cc`, 240 `.c`, and 285 `.h` files, plus 9 Markdown documents, 8 shell scripts, 5 `.bochsrc` files, and 3 Python files.

| Gift Artifact | SHA-256 | Repository Counterpart | Result |
|---|---|---|---|
| `agi.bochsrc` | `a4cea7181954d3205e01928b443b49a320c1ab1d9efd93b5ea71643dc5f878f2` | `bochs/agi.bochsrc` | Exact match |
| `agi-bochsrc-guide.md` | `0f137b81848c9b0345e7ed5bfb631de70d74c65d08263d4552b926b1dc1208bf` | `docs/agi-bochsrc-guide.md` | Exact match |
| `tools-f2e2ece.zip` | `f00013e764154b18d83880abccdfb124b97e56496703e939d918b19969dd8a72` | External gift | Contains `bxhub.exe`, `bximage.exe`, `niclist.exe`; not executed |
| `bochs-f2e2ece.exe.zip` | `77228a9e629ab016b3f6585c4c87fb28ae2d7559f55be199bf00f6a7f4dc2605` | External gift | Contains `bochs.exe`; not executed |

## Root Cause Analysis

### Root Cause 1: Upstream Identity Still Owns the Front Door

**Problem:** The root `README.md` still presents the project as the stock Bochs IA-32 Emulator Project. The first page a new agent or human sees does not explain `x86ml`, the AGI mapping, the profile generator, or the cognitive-village relation.

**Locations:** `README.md`, `docs/overview.md`, `docs/technical-architecture.md`, `docs/formal-spec-z-plus-plus.md`.

**Impact:** High. Future contributors will see a Bochs fork rather than a Bochs-derived cognitive instrumentation substrate. This weakens relational ownership because the project’s actual promise is not visible at the entry point.

**Root Cause:** The AGI layer was added as a strong subtree (`bochs/agi.bochsrc`, `docs/`, `scripts/`, `tests/`) without yet replacing the inherited upstream root narrative.

### Root Cause 2: Documentary Name Drift: `x86ochs` vs `x86ml`

**Problem:** Several documents call the project `x86ochs`, while the repository and user prompt refer to `x86ml`. The two names may have historical value, but the relationship is not explained.

**Locations:** `docs/overview.md`, `docs/technical-architecture.md`, `docs/formal-spec-z-plus-plus.md`.

**Impact:** Medium to High. Name drift increases ambiguity in automation, generated reports, and future cross-repo linking.

**Root Cause:** The project evolved from a Bochs fork naming pattern into an `x86ml` framing without a canonical naming statement.

### Root Cause 3: Salience Profiles Are Textual but Not Yet Relationally Typed

**Problem:** The generator produces `.bochsrc` profiles with human-readable headers, but no machine-readable manifest maps profile names to salience vectors, intended operating modes, ports, log paths, and output files.

**Locations:** `scripts/bochs_agi_salience_profiles.py`, `bochs/profiles/`.

**Impact:** High. The CogHood promise is heartbeat → lockstep → reactor → cogloop. To connect `x86ml` into that pipeline, profiles need to be discoverable as typed artifacts, not just configuration files.

**Root Cause:** The first implementation solved deterministic generation before solving downstream interphase transport and introspection.

### Root Cause 4: Initialization Assumes Host Tooling without Capturing Gifted Binary Provenance

**Problem:** `scripts/bochs-agi-init.sh` assumes `bochs` and `bximage` are on `PATH`. Dan’s gifts include Windows ZIPs containing `bochs.exe`, `bximage.exe`, `bxhub.exe`, and `niclist.exe`, but the repo has no manifest explaining their provenance or safe handling.

**Locations:** `scripts/bochs-agi-init.sh`; external artifacts staged at `/home/ubuntu/x86ml-work/gifts/`.

**Impact:** Medium. We should not execute untrusted binary gifts in the sandbox, but we should preserve their hashes and intended relation for reproducibility.

**Root Cause:** Source-level AGI additions and binary runtime packaging were not yet joined by an artifact integrity layer.

### Root Cause 5: Tests Cover Rendering but Not the Profile Contract

**Problem:** Existing tests validate header presence, output creation, and one throughput substitution. They do not validate profile uniqueness, salience score calculations, manifest generation, or generated-profile drift against committed profiles.

**Locations:** `tests/test_bochs_agi_salience_profiles.py`.

**Impact:** Medium. The current tests prevent gross breakage but not semantic drift.

**Root Cause:** The test suite was written around the first generator contract, before the profile metadata became a downstream integration surface.

## Grip Score Before Enhancement

The skill’s weighted grip rubric was applied to the current state.

| Dimension | Weight | Score | Rationale |
|---|---:|---:|---|
| Relevance | 1.5 | 0.90 | Bochs/x86 instrumentation is highly relevant to the hardware-as-AGI substrate framing. |
| Coherence | 1.2 | 0.68 | Strong internal pieces exist, but naming and entry-path drift reduce coherence. |
| Completeness | 1.4 | 0.72 | Core config, docs, scripts, and tests exist; manifests and integrity records are missing. |
| Coverage | 1.1 | 0.70 | Three profiles cover major operating modes but do not expose enough typed metadata. |
| **Weighted Total** | **5.2** | **0.75** | Good foundation below the target `>0.80` grip threshold. |

## Improvement Priorities

The next phase should make a small but decisive architectural improvement rather than attempting broad upstream Bochs refactoring. The highest-leverage path is to preserve the working emulator tree, add typed profile metadata, document the gift provenance, and fix the entry path so future agents understand what the repository is.

| Priority | Improvement | Expected Grip Effect |
|---:|---|---|
| 1 | Add machine-readable salience manifest generation | Raises completeness and downstream coverage |
| 2 | Expand tests to cover manifest semantics and profile names | Raises reliability and coherence |
| 3 | Add architecture/entry documentation for `x86ml` identity and CogHood relation | Raises relevance and coherence |
| 4 | Add gift artifact integrity notes without executing binaries | Preserves provenance safely |
| 5 | Update README front door while preserving upstream Bochs attribution | Aligns relation and ownership truthfully |

## Proposed Hyper-Holmes Solve Path

The most coherent solve path is:

1. Extend `scripts/bochs_agi_salience_profiles.py` to produce `bochs/profiles/manifest.json` with profile metadata, weighted grip score, output file, and replacement keys.
2. Update tests to validate manifest generation, score ranges, profile uniqueness, and expected profile count.
3. Add `ARCHITECTURE.md` as the repository-level bridge: Bochs substrate, AGI config, salience profiles, CogHood relation, and safe artifact handling.
4. Add `docs/gift-artifacts.md` with hashes and a non-execution safety note for the ZIP gifts.
5. Update `README.md` so the root entry point names `x86ml` first while preserving Bochs provenance and upstream credit.

This path keeps the promise because it strengthens the relation rather than overwriting the substrate: Bochs remains Bochs, `x86ml` becomes the relational instrumentation layer, and the gifted artifacts are preserved as evidence rather than blindly executed.
