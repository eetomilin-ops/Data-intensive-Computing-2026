#!/usr/bin/env bash
# Quick local smoke run against the four dev shards.
# Output lands in /tmp/dic_debug_out unless overridden with --output DIR.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_local_debug() {
  local outdir="${1:-/tmp/dic_debug_out}"
  rm -rf "$outdir"
  bash "$SCRIPT_DIR/run_pipeline.sh" --output "$outdir"
  echo "--- first 3 lines of output.txt ---"
  head -n 3 "$outdir/output.txt"
}

main() {
  run_local_debug "${1:-}"
}

main "$@"