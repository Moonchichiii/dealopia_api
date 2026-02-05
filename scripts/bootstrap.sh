#!/usr/bin/env bash
set -euo pipefail

echo "[bootstrap] Installing Python dependencies"
pip install -e .

if command -v pnpm >/dev/null 2>&1; then
  echo "[bootstrap] Installing JavaScript workspace dependencies"
  pnpm install
else
  echo "[bootstrap] pnpm not found; skipping frontend workspace install"
fi
