#!/usr/bin/env bash
set -euo pipefail

checks=(
  "http://localhost:8000/healthz"
  "http://localhost:8101/health"
  "http://localhost:8102/health"
  "http://localhost:8103/health"
  "http://localhost:8104/health"
  "http://localhost:8105/health"
)

for url in "${checks[@]}"; do
  echo "[health] $url"
  curl -fsS "$url" >/dev/null
  echo "  -> ok"
done
