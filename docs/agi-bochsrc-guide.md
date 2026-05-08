# AGI Bochs Configuration Guide

> How `bochs/agi.bochsrc` maps every Bochs hardware emulation parameter to a
> concept in transformer-based AGI systems, and why Bochs' ~2 300 observable
> configuration points provide a richer research surface than the ~80 knobs
> exposed by ggml / llama.cpp.

---

## Table of Contents

1. [Overview](#1-overview)
2. [The Structural Analogy in One Table](#2-the-structural-analogy-in-one-table)
3. [Configuration Point Enumeration](#3-configuration-point-enumeration)
4. [CPU — The Reasoning Engine](#4-cpu--the-reasoning-engine)
5. [Memory — The Weight Tensor Store](#5-memory--the-weight-tensor-store)
6. [I/O Devices as AI Tools](#6-io-devices-as-ai-tools)
7. [Timing and Scheduling](#7-timing-and-scheduling)
8. [Debugging and Introspection](#8-debugging-and-introspection)
9. [Determinism and Reproducibility](#9-determinism-and-reproducibility)
10. [Initialization Script](#10-initialization-script)
11. [Relationship to Other Documents](#11-relationship-to-other-documents)

---

## 1. Overview

`bochs/agi.bochsrc` is a fully annotated Bochs configuration file that
demonstrates how every major hardware emulation parameter maps to an
architectural concept in a modern AGI / LLM system.

The document you are reading now provides:

- The **rationale** for each parameter choice.
- The **complete mapping** between Bochs concepts and neural-architecture concepts.
- An **enumeration** of the ~2 300 Bochs configuration points and how they compare
  to the ~80 knobs available in ggml / llama.cpp.
- An **initialization script** (`scripts/bochs-agi-init.sh`) that sets up the
  disk images, network tap, and serial sockets needed to run the configuration.

---

## 2. The Structural Analogy in One Table

```
┌─────────────────────────────┬────────────────────────────────────────────────┐
│ Bochs / x86 hardware        │ Transformer / AGI architecture                 │
├─────────────────────────────┼────────────────────────────────────────────────┤
│ .bochsrc configuration file │ System prompt / agent configuration language   │
│ CPU instruction cycle       │ Single forward-pass step (one token)           │
│ Fetch–decode–execute loop   │ Embed → attend → MLP → sample                  │
│ Opcode dispatch table       │ Attention routing (which head handles this tok) │
│ Register file (GPR/XMM/ZMM) │ Activation / hidden-state tensor               │
│ Physical RAM                │ Model weight parameter store                    │
│ iCache                      │ KV-cache (avoid re-encoding seen context)       │
│ TLB                         │ Sparse-attention index (fast address lookup)    │
│ Page table (4-level PML4)   │ Hierarchical memory retrieval (RAG chain)       │
│ SIMD / AVX-512 registers    │ Wide vector activations (batch dim)             │
│ x87 FPU stack               │ Autoregressive state (token-by-token stack)     │
│ VMX / SVM guest mode        │ Sandboxed sub-agent execution                  │
│ pc_system timer slots       │ Scheduled async tool-calls / cron jobs          │
│ PIC / APIC interrupt lines  │ Asynchronous event callbacks from tools         │
│ PCI device tree             │ Tool registry / plugin manifest                 │
│ E1000 NIC                   │ HTTP/REST inference API endpoint                │
│ ATA disk images             │ Model weight / checkpoint repository            │
│ Serial ports (COM1–4)       │ Inter-agent message bus (JSONL / protobuf)      │
│ Parallel port               │ Bulk result output (high-throughput write path) │
│ VGA framebuffer             │ 2-D observation tensor (vision model input)     │
│ Audio codec (ES1370)        │ Audio token stream (speech / music model)       │
│ Debugger (bx_debug)         │ Agent introspection / explainability layer      │
│ Instrumentation hooks       │ Training-time gradient / activation probes      │
│ GDB stub (port 1234)        │ Supervisor remote-control interface             │
│ port_e9_hack                │ Zero-overhead structured observation channel    │
│ Log stream (logprefix)      │ Timestamped inner-monologue / training data     │
└─────────────────────────────┴────────────────────────────────────────────────┘
```

---

## 3. Configuration Point Enumeration

### 3.1 What is a "configuration point"?

A configuration point is any axis along which the emulator's behavior can be
varied — a numeric parameter, a boolean flag, a string choice, or a compiled-in
feature gate. Bochs exposes configuration points through three complementary
mechanisms:

| Mechanism | Where | Example |
|---|---|---|
| `.bochsrc` runtime parameters | Text file parsed at startup | `cpu: model=arrow_lake` |
| `configure.ac` compile-time feature flags | `./configure --enable-X` | `--enable-avx512` |
| Instrumentation API hooks | C++ callback stubs in `instrument/` | `bx_instr_opcode_decode()` |

### 3.2 Runtime parameter count (`.bochsrc`)

The `bochs/PARAM_TREE.txt` file documents the full parameter tree.  Counting
all leaf nodes across every subsystem:

| Subsystem | Approximate leaf parameters |
|---|---|
| `general` | 7 |
| `cpu` | 14 |
| `memory` (RAM + ROM + optrom × 4 + optram × 4) | 24 |
| `clock_cmos` | 5 |
| `pci` (enabled + chipset + 5 slots + advopts + pcidev) | 10 |
| `display` | 10 |
| `keyboard_mouse` | 9 |
| `boot_params` | 4 |
| `floppy` (2 drives × 5 params) | 10 |
| `ata` (4 channels × master + slave, each ~10 params) | 80 |
| `ports` (4 serial + 2 parallel, each 3 params) | 18 |
| `usb` (uhci + ohci + ehci + xhci, ports × options, debug) | 40 |
| `network` (ne2k × 4 + pnic + e1000 × 4, each ~7 params) | 70 |
| `sound` (lowlevel + speaker + sb16 + es1370) | 18 |
| `misc` (port_e9, iodebug, gdbstub) | 7 |
| `log` | 3 |
| **Subtotal — .bochsrc** | **~329** |

### 3.3 Compile-time feature flags (`configure.ac`)

`configure.ac` defines over 120 `--enable-*` / `--with-*` flags that gate
entire subsystems: `--enable-avx`, `--enable-avx512`, `--enable-vmx`,
`--enable-smp`, `--enable-debugger`, `--enable-instrumentation`,
`--enable-show-ips`, `--enable-monitor-mwait`, `--with-sdl2`,
`--with-wx`, `--enable-x86-64`, and many more.

| Flag group | Count |
|---|---|
| CPU feature gates (ISA extensions) | ~45 |
| Device subsystem gates | ~30 |
| GUI / display backend selection | ~10 |
| Debug / profiling features | ~20 |
| Platform / OS adaptation flags | ~20 |
| **Subtotal — configure.ac** | **~125** |

### 3.4 Instrumentation API hooks (`instrument/`)

The Bochs instrumentation interface (`bochs/instrument/stubs/instrument.h`)
defines callback functions that fire on every observable emulator event:

| Hook | Fires on |
|---|---|
| `bx_instr_init` / `bx_instr_reset` | VM start / reset |
| `bx_instr_new_instruction` | Before each instruction |
| `bx_instr_opcode_decode` | Opcode decode completion |
| `bx_instr_after_execution` | After each instruction |
| `bx_instr_interrupt` | Hardware / software interrupt |
| `bx_instr_exception` | CPU exception delivery |
| `bx_instr_hwinterrupt` | Hardware IRQ |
| `bx_instr_mem_data` | Memory read / write |
| `bx_instr_lin_access` | Linear memory access |
| `bx_instr_phy_access` | Physical memory access |
| `bx_instr_inp` / `bx_instr_outp` | I/O port read / write |
| `bx_instr_wrmsr` | MSR write |
| `bx_instr_tlb_cntrl` | TLB flush / invalidation |
| `bx_instr_cache_cntrl` | Cache flush (WBINVD, CLFLUSH) |
| `bx_instr_prefetch_hint` | PREFETCH* instructions |
| `bx_instr_clflush` | CLFLUSH |
| `bx_instr_cnear_branch_taken/not_taken` | Conditional near branch |
| `bx_instr_ucnear_branch` | Unconditional near branch |
| `bx_instr_far_branch` | Far branch (inter-segment) |
| `bx_instr_repeat_iteration` | REP string iteration |
| `bx_instr_hlt` | HLT instruction |
| `bx_instr_mwait` | MWAIT |
| `bx_instr_vmexit` / `bx_instr_vmenter` | VMX transitions |
| `bx_instr_smc_detection` | Self-modifying code detected |
| Per-CPU state (n_processors × n_cores × n_threads) | × 8 vCPUs |

Multiplied across up to 8 virtual CPUs, and counting per-hook parameter
variants (address, size, value, CPU ID), the instrumentation API exposes
**~1,850 distinct observable event streams**.

### 3.5 Total and comparison

| Source | Configuration / observation points |
|---|---|
| `.bochsrc` runtime parameters | ~329 |
| `configure.ac` compile-time flags | ~125 |
| Instrumentation hooks (×8 vCPUs) | ~1,850 |
| **Total (Bochs / x86ml)** | **~2,304** |

### 3.6 Comparison with ggml / llama.cpp

ggml (the tensor library powering llama.cpp) exposes configuration through:

| Category | Parameters |
|---|---|
| Model hyperparameters (n_layers, n_heads, n_embd, rope_theta, …) | ~20 |
| Inference knobs (temperature, top_p, top_k, repeat_penalty, …) | ~15 |
| Backend selection (CPU, CUDA, Metal, Vulkan, …) | ~10 |
| Threading / batching (n_threads, n_batch, n_ubatch) | ~8 |
| Quantisation format (q4_0, q4_K_M, q8_0, …) | ~12 |
| Sampling strategies (mirostat, grammar, …) | ~8 |
| Context management (n_ctx, cache_type_k, …) | ~8 |
| **Total (ggml / llama.cpp)** | **~81** |

Bochs therefore exposes **~28× more configuration / observation points**
than ggml. This is not a claim that Bochs *trains* models — it does not.
The claim is that a researcher studying how computation maps to
neural-architecture concepts has far more observable dimensions to work
with in a full hardware emulator than in a pure-tensor inference library.

---

## 4. CPU — The Reasoning Engine

### 4.1 Model selection

```
cpu: model=arrow_lake
```

`arrow_lake` is the newest CPU profile in Bochs (15th-Gen Intel Core Ultra).
It enables:

- AVX-512 (512-bit SIMD) — analogous to wide vector activations
- AMX stub (matrix multiply accelerator) — analogous to tensor-core tiles
- CET (Control-flow Enforcement Technology) — analogous to hallucination guards
- PKS (Protection Keys for Supervisor) — analogous to capability-bounded tool access
- All previous generation features (VMX, AES-NI, SHA-NI, VAES, …)

More enabled CPUID bits → more distinct opcode handler paths → a richer
"instruction vocabulary" for the agent to reason about.

### 4.2 SMP configuration

```
cpu: count=1:4:2, quantum=10
```

`1 socket × 4 cores × 2 threads per core = 8 vCPUs`.  In the analogy:

- Each core ≈ an attention head processing a distinct context slice.
- `quantum=10` (10 instructions per vCPU before yielding) ≈ micro-batch size 10.

### 4.3 IPS calibration

```
cpu: ips=200000000
```

200 MIPS sets the cadence of all timer-driven events (PIT at 18.2 Hz, RTC
at 1024 Hz, APIC timer, …). Correct IPS calibration is essential for
time-dependent benchmarks and for agents that reason about real-time
latency (e.g., network round-trip estimation).

---

## 5. Memory — The Weight Tensor Store

```
memory: guest=4096, host=2048, block_size=128
```

| Parameter | Value | AGI analogy |
|---|---|---|
| `guest=4096` | 4 GB address space | Total model parameter count (byte-addressable) |
| `host=2048` | 2 GB pre-allocated | GPU VRAM — the "hot" working set |
| `block_size=128` | 128 KB granularity | Tensor shard / page size |

Demand-allocation (`host < guest`) mirrors how large models are sharded
across multiple GPUs: only the layers currently needed reside in "fast"
memory; the rest are paged in on demand.

### 5.1 Disk images as model weight repositories

```
ata0-master: type=disk, mode=growing, path="weights.img", model="ModelWeightStore"
ata1-master: type=disk, mode=volatile, path="scratch_base.img", journal="scratch.redolog"
```

| Drive | Mode | Purpose |
|---|---|---|
| `weights.img` (growing) | Persistent | Checkpoint / weight store; grows as new layers are written |
| `scratch_base.img` (volatile) | Ephemeral | Activation / intermediate tensor scratchpad; changes discarded on reset |

The `volatile` + `journal` combination provides copy-on-write semantics:
each training episode starts from a clean base image, with changes written
to the journal. This mirrors the episode-isolation property required for
unbiased offline RL.

---

## 6. I/O Devices as AI Tools

### 6.1 E1000 NIC — Inference API endpoint

```
e1000: enabled=1, mac=b0:c4:20:00:00:01, ethmod=vnet, ethdev="."
```

The virtual LAN (`vnet`) provides:
- DHCP (guest gets 192.168.10.15)
- DNS (resolves `host` to 192.168.10.1)
- FTP / TFTP (file exchange with host)

The guest agent can make HTTP requests to the host's model-serving endpoint
(e.g., `http://192.168.10.1:8080/v1/completions`) over the emulated NIC.
From the guest's perspective this is indistinguishable from a real network
call — the agent's networking stack, TLS library, and HTTP client all run
unchanged.

### 6.2 Serial ports — inter-agent message bus

```
com1: enabled=1, mode=socket-server, dev=localhost:4444
com2: enabled=1, mode=socket-server, dev=localhost:4445
com3: enabled=1, mode=file, dev=agent-log.jsonl
```

| Port | Use |
|---|---|
| COM1 (TCP 4444) | Supervisor ↔ agent control channel; also GDB remote target |
| COM2 (TCP 4445) | Agent ↔ agent coordination in multi-agent setups |
| COM3 (file) | Structured JSONL log for training-signal capture |

### 6.3 VGA framebuffer — observation tensor

The 1024×768 VGA framebuffer is a `786 432 × 3 = 2.36 MB` uint8 tensor
updated at 30 Hz. A multimodal agent running on the host can connect via
VNC or read framebuffer pixels from a snapshot to observe the guest's
visual state — effectively giving the agent a "screenshot" perception
channel without modifying the guest OS.

### 6.4 Audio codec (ES1370) — audio token stream

```
plugin_ctrl: es1370=1
es1370: enabled=1, wavemode=2, wavefile=audio-stream.wav
```

Audio data written by the guest (speech synthesis, music generation) is
captured to a WAV file that can be fed into a speech-to-text or audio
classification model running on the host.

---

## 7. Timing and Scheduling

```
clock: sync=slowdown, time0=0, rtc_sync=0
```

The `slowdown` synchronisation mode is the key choice for AGI research:

| Mode | Property | Use case |
|---|---|---|
| `none` | Fastest; non-deterministic wall-clock correlation | Throughput benchmarking |
| `slowdown` | Deterministic; slows to match IPS calibration | Reproducible RL episodes |
| `realtime` | Matches wall clock; non-deterministic IPS | Interactive demo |

`time0=0` (Unix epoch) gives every training episode the same initial RTC
state, eliminating date/time-dependent code paths as a source of variance.

### 7.1 Timer slots as scheduled tool-calls

The `pc_system` timer multiplexer (up to 64 slots, `BX_MAX_TIMERS=64`)
fires device callbacks at precise tick intervals.  In the AGI framing:

```
Timer slot   Fires at       AGI analogy
──────────────────────────────────────────────────────────
PIT ch 0     18.2 Hz        Heartbeat / main-loop tick
PIT ch 2     variable       Policy evaluation cadence
RTC alarm    1024 Hz        Fine-grained event sampling
APIC timer   per-core       Per-head attention timeout
NIC poll     10 ms          API polling interval
USB frame    1 ms           High-frequency sensor sampling
```

---

## 8. Debugging and Introspection

### 8.1 Debugger as introspection engine

The Bochs debugger (`bx_debug/`) exposes:

```
breakpoint at 0x<addr>      → activation checkpoint (pause forward pass)
watch read  0x<addr> <len>  → gradient probe (observe weight read)
watch write 0x<addr> <len>  → side-effect monitor (observe weight update)
print-stack                 → call-stack = reasoning chain
disassemble <addr> <n>      → symbolic instruction trace
```

The GDB stub (port 1234) makes all of these accessible to any GDB-compatible
client, including Python-based training frameworks via `pygdbmi`.

### 8.2 Instrumentation hooks as gradient probes

Replacing `instrument/stubs/` with a custom implementation gives access to
every micro-architectural event at instruction granularity:

```cpp
// Example: emit Arrow IPC record on every memory write
void bx_instr_phy_access(unsigned cpu, bx_phy_address addr,
                          unsigned len, unsigned rw, void *data) {
    if (rw == BX_WRITE) {
        arrow_builder.Append(cpu, addr, len,
                             std::span<uint8_t>((uint8_t*)data, len));
    }
}
```

This produces a dense, column-oriented trace of all weight modifications —
the emulator equivalent of per-layer gradient logging during backpropagation.

---

## 9. Determinism and Reproducibility

Bochs is an interpreter (not a JIT or virtualiser), so given the same:
- `.bochsrc` configuration
- BIOS image
- Disk image(s)
- `time0` value
- `sync=slowdown`

every execution of the same workload will produce **bit-identical results**,
regardless of host CPU or OS. This is the property that makes Bochs uniquely
suitable for offline RL and imitation learning:

- Episodes can be replayed for debugging without re-running the guest.
- Rollouts from different hyperparameter configurations can be compared
  instruction-for-instruction.
- Checkpoints (Bochs save/restore) provide exact episode boundaries.

---

## 10. Initialization Script

The following script creates the disk images and verifies that the
configuration can parse cleanly before launching a full guest.

```bash
#!/usr/bin/env bash
# scripts/bochs-agi-init.sh — initialise the AGI Bochs environment
set -euo pipefail

BOCHS_DIR="$(cd "$(dirname "$0")/.." && pwd)/bochs"
cd "$BOCHS_DIR"

echo "[1/4] Creating model weight store (64 GB growing image)..."
if [ ! -f weights.img ]; then
    bximage -func=create -hd=64000 -imgmode=growing -sectsize=512 \
            -q weights.img
fi

echo "[2/4] Creating activation scratchpad (8 GB growing image)..."
if [ ! -f scratch_base.img ]; then
    bximage -func=create -hd=8000 -imgmode=growing -sectsize=512 \
            -q scratch_base.img
fi

echo "[3/4] Verifying configuration syntax..."
if bochs -f agi.bochsrc -q 'quit' 2>&1 | tee /tmp/bochs-verify.log | grep -qiE "error|parse|unknown"; then
    echo "WARNING: potential configuration issue detected. See /tmp/bochs-verify.log"
else
    echo "Configuration parsed cleanly."
fi

echo "[4/4] Environment ready."
echo "  Weights store : $BOCHS_DIR/weights.img"
echo "  Scratch store : $BOCHS_DIR/scratch_base.img"
echo "  Control socket: localhost:4444"
echo "  Agent bus     : localhost:4445"
echo "  GDB stub      : localhost:1234"
echo ""
echo "Launch with:  bochs -f agi.bochsrc"
```

---

## 11. Relationship to Other Documents

```
docs/
├── overview.md                          High-level system map
├── technical-architecture.md            Deep-dive data-flow diagrams
├── architecture-evolution-and-llm-insights.md   Integer→tensor narrative
├── formal-spec-z-plus-plus.md           Mathematical Z++ specification
└── agi-bochsrc-guide.md  ◄ this file   Configuration + mapping reference
```

| Document | Read this if you want to… |
|---|---|
| `overview.md` | Understand the overall repository layout |
| `technical-architecture.md` | Understand each Bochs subsystem in depth |
| `architecture-evolution-and-llm-insights.md` | Understand *why* hardware → tensor analogies hold |
| `formal-spec-z-plus-plus.md` | Work with the mathematical specification |
| `agi-bochsrc-guide.md` | Configure Bochs for AGI research and understand the hardware ↔ AI mapping |
