#!/usr/bin/env bash
set -euo pipefail
mkdir -p infra/nginx/ssl
openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes \
  -keyout infra/nginx/ssl/dev.key \
  -out infra/nginx/ssl/dev.crt \
  -subj "/CN=localhost"
