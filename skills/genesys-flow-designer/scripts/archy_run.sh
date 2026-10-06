#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: archy_run.sh [qa|prod|none] <archy-args...>

Examples:
  archy_run.sh none --help
  archy_run.sh qa export --flowName "My Flow" --flowType inboundemail --exportType yaml --outputDir /tmp/out
  archy_run.sh prod publish --file /abs/path/flow.yaml
EOF
}

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 64
fi

env_name="$1"
shift

if [[ -n "${ARCHY_BIN:-}" ]]; then
  binary="$ARCHY_BIN"
elif command -v archy >/dev/null 2>&1; then
  binary="$(command -v archy)"
else
  echo "Archy is not on PATH. Install it or set ARCHY_BIN to its executable path." >&2
  exit 66
fi

if [[ ! -x "$binary" ]]; then
  echo "Archy binary not found or not executable: $binary" >&2
  exit 66
fi

options_file=""
case "$env_name" in
  qa)
    options_file="${ARCHY_QA_OPTIONS_FILE:-$HOME/.config/genesys/archy/env.qa.yaml}"
    ;;
  prod)
    options_file="${ARCHY_PROD_OPTIONS_FILE:-$HOME/.config/genesys/archy/env.prod.yaml}"
    ;;
  none)
    ;;
  *)
    echo "Unknown environment selector: $env_name" >&2
    usage >&2
    exit 64
    ;;
esac

if [[ -n "$options_file" && ! -f "$options_file" ]]; then
  echo "Archy options file not found: $options_file" >&2
  echo "Set ARCHY_QA_OPTIONS_FILE or ARCHY_PROD_OPTIONS_FILE, or pass 'none' and --optionsFile explicitly." >&2
  exit 66
fi

args=("$@")

has_options_file=false
for ((i = 0; i < ${#args[@]}; i++)); do
  if [[ "${args[i]}" == "--optionsFile" ]]; then
    has_options_file=true
    break
  fi
done

if [[ -n "$options_file" && "$has_options_file" == false ]]; then
  args+=("--optionsFile" "$options_file")
fi

exec "$binary" "${args[@]}"
