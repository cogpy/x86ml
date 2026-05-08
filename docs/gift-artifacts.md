# Gift Artifact Provenance and Safe Handling

Dan attached four Bochs AGI artifacts during the `x86ml` repo-introspection pass. Two of them are source-level artifacts that already match committed repository files exactly. Two are Windows binary ZIP archives that should be preserved as provenance records but **not executed automatically**.

## Artifact Inventory

| Artifact | SHA-256 | Current Relation | Safe-Handling Status |
|---|---|---|---|
| `agi.bochsrc` | `a4cea7181954d3205e01928b443b49a320c1ab1d9efd93b5ea71643dc5f878f2` | Exact match for `bochs/agi.bochsrc` | Source text reviewed through repository copy. |
| `agi-bochsrc-guide.md` | `0f137b81848c9b0345e7ed5bfb631de70d74c65d08263d4552b926b1dc1208bf` | Exact match for `docs/agi-bochsrc-guide.md` | Source text reviewed through repository copy. |
| `tools-f2e2ece.zip` | `f00013e764154b18d83880abccdfb124b97e56496703e939d918b19969dd8a72` | External binary gift | Contains Windows helper tools; not executed. |
| `bochs-f2e2ece.exe.zip` | `77228a9e629ab016b3f6585c4c87fb28ae2d7559f55be199bf00f6a7f4dc2605` | External binary gift | Contains Windows `bochs.exe`; not executed. |

## Observed ZIP Contents

The ZIPs were inspected passively by file listing only. No executable was run.

| ZIP | Observed Contents |
|---|---|
| `tools-f2e2ece.zip` | `bxhub.exe`, `bximage.exe`, `niclist.exe` |
| `bochs-f2e2ece.exe.zip` | `bochs.exe` |

## Policy

The `x86ml` source repository should remain reproducible without trusting opaque binary attachments. The source-level configuration (`bochs/agi.bochsrc`), guide (`docs/agi-bochsrc-guide.md`), profile generator, generated profiles, and tests are the canonical development surface.

> **Rule:** binary gifts may be hashed, listed, archived, and related to source commits, but they must not be executed by default. Execution requires an explicit environment decision, provenance review, and isolation appropriate to the host operating system.

## Relation to the AGI Layer

The binary artifacts appear to correspond to a Windows Bochs runtime build at commit `f2e2ece`, the merge commit that added the AGI Bochs configuration work. They are useful as runtime gifts, but the repository’s durable promise should remain anchored in source-visible artifacts and deterministic generation.

| Source Contract | Runtime Artifact |
|---|---|
| `bochs/agi.bochsrc` | Consumed by `bochs.exe` or host `bochs`. |
| `scripts/bochs-agi-init.sh` | Uses `bximage` and `bochs` when available on `PATH`. |
| `bochs/profiles/manifest.json` | Helps future agents select the correct `.bochsrc` profile. |
| `bochs/profiles/agi-*.bochsrc` | Runtime configurations for the emulator binary. |

## Re-verification Commands

Use these commands to re-check artifact integrity from a staging directory without executing binaries:

```bash
sha256sum agi.bochsrc agi-bochsrc-guide.md tools-f2e2ece.zip bochs-f2e2ece.exe.zip
unzip -l tools-f2e2ece.zip
unzip -l bochs-f2e2ece.exe.zip
```

If a future maintainer chooses to add these binaries to a release artifact, include the hashes above in the release notes and keep the source commit relationship explicit.
