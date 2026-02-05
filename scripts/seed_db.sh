#!/usr/bin/env bash
set -euo pipefail
python apps/api/manage.py loaddata initial_data || true
