#!/usr/bin/env bash
set -euo pipefail

echo "[bootstrap] Installing Python dependencies with uv"
uv sync --project apps/api

echo "[bootstrap] Installing JavaScript workspace dependencies with bun"
bun install
