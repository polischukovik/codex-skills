#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: gc_json_query.sh <gc command...>" >&2
  echo "example: cat query.json | gc_json_query.sh analytics users details query create" >&2
  exit 2
fi

workdir="/tmp/gc-cli"
mkdir -p "$workdir"
tmpfile="$(mktemp "$workdir/query.XXXXXX.json")"
trap 'rm -f "$tmpfile"' EXIT

cat > "$tmpfile"
gc "$@" -f "$tmpfile"
