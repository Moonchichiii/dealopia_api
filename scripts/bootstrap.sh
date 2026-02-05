#!/usr/bin/env bash
set -euo pipefail

echo "[bootstrap] Installing Python dependencies with uv"
uv pip install --system -e apps/api

echo "[bootstrap] Installing JavaScript workspace dependencies with bun"
bun install
