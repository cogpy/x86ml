#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOCHS_DIR="$REPO_ROOT/bochs"
cd "$BOCHS_DIR"

echo "[1/5] Creating model weight store (64 GB growing image)..."
if [ ! -f weights.img ]; then
  bximage -func=create -hd=64000 -imgmode=growing -sectsize=512 -q weights.img
fi

echo "[2/5] Creating activation scratchpad (8 GB growing image)..."
if [ ! -f scratch_base.img ]; then
  bximage -func=create -hd=8000 -imgmode=growing -sectsize=512 -q scratch_base.img
fi

echo "[3/5] Generating salience-tuned profile set..."
python "$REPO_ROOT/scripts/bochs_agi_salience_profiles.py"

echo "[4/5] Verifying bochsrc parse..."
VERIFY_LOG="/tmp/bochs-verify.log"
if bochs -f agi.bochsrc -q 'quit' >"$VERIFY_LOG" 2>&1; then
  if grep -qiE "error|parse|unknown" "$VERIFY_LOG"; then
    echo "WARNING: potential configuration issue detected. See $VERIFY_LOG"
  else
    echo "Configuration parsed cleanly."
  fi
else
  cat "$VERIFY_LOG"
  echo "ERROR: bochs failed while parsing agi.bochsrc"
  exit 1
fi

echo "[5/5] Environment ready."
echo "  Base config     : $BOCHS_DIR/agi.bochsrc"
echo "  Profile configs : $BOCHS_DIR/profiles/agi-{max-grip,balanced,throughput}.bochsrc"
echo "  Weights store   : $BOCHS_DIR/weights.img"
echo "  Scratch store   : $BOCHS_DIR/scratch_base.img"
echo "  Control socket  : localhost:4444"
echo "  Agent bus       : localhost:4445"
echo "  GDB stub        : localhost:1234"
