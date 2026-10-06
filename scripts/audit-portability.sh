#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_root="$repo_root/skills"
status=0

if [[ ! -d "$skills_root" ]]; then
  echo "Missing skills directory: $skills_root" >&2
  exit 1
fi

while IFS= read -r -d '' skill_dir; do
  skill_file="$skill_dir/SKILL.md"
  if [[ ! -f "$skill_file" ]]; then
    echo "Missing SKILL.md: $skill_dir" >&2
    status=1
    continue
  fi

  if ! sed -n '1,12p' "$skill_file" | rg -q '^name:[[:space:]]*'; then
    echo "Missing name frontmatter: $skill_file" >&2
    status=1
  fi
  if ! sed -n '1,12p' "$skill_file" | rg -q '^description:[[:space:]]*'; then
    echo "Missing description frontmatter: $skill_file" >&2
    status=1
  fi
done < <(find "$skills_root" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)

if rg -n --hidden \
  -g '!**/__pycache__/**' -g '!*.png' -g '!*.svg' \
  '(/mnt/[a-z]/dev/|/home/[^/]+/|[A-Za-z]:\\\\Users\\\\)' "$skills_root"; then
  echo "Found a machine- or project-specific absolute path." >&2
  status=1
fi

if rg -n --hidden \
  -g '!**/__pycache__/**' -g '!*.png' -g '!*.svg' \
  '(client[_-]?secret|api[_-]?key|access[_-]?token|password)[[:space:]]*[:=][[:space:]]*[^<${[:space:]]' "$skills_root"; then
  echo "Found a possible committed secret assignment; inspect each match." >&2
  status=1
fi

while IFS= read -r -d '' script; do
  bash -n "$script" || status=1
done < <(find "$skills_root" -type f -name '*.sh' -print0)

while IFS= read -r -d '' script; do
  PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/codex-skills-pycache" python3 -m py_compile "$script" || status=1
done < <(find "$skills_root" -type f -name '*.py' -print0)

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

echo "Portability audit passed."
