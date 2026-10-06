---
name: sql-contract-audit
description: Use when auditing consistency between transform SQL, mapping CSVs, and playbooks, especially to check final SELECT order, CSV shape, missing or extra fields, field-name drift, and contract mismatches before or after editing report mappings.
---

# SQL Contract Audit Skill

## Workflow
1. Treat the mapping CSV as the field contract.
2. Compare three artifacts together:
   - mapping CSV
   - transform SQL final output
   - report playbook field notes
3. Check structure first.
   - mapping CSV parses as 6 columns
   - final SELECT aliases match expected field names and order
4. Check drift next.
   - fields present in SQL but not the mapping
   - fields present in mapping but not SQL
   - playbook statements that contradict either one
5. Finish with static hygiene.
   - `git diff --check`
   - focused CSV parsing
   - concise mismatch summary

## Recommended Commands
- `python3 - <<'PY' ... csv.reader ... PY` for 6-column checks
- `rg` for field names and notes
- `sed` / `awk` / `nl` for final SELECT inspection
- compare only the touched report files unless the task is repo-wide

## Read When Needed
- `references/checklist.md`
- `references/mismatch-types.md`

## Practical Rules
- Do not trust one artifact alone.
- Call out whether a mismatch is implementation drift or documentation drift.
- If the final SELECT is complex, audit the final projection instead of upstream staging aliases.
- Keep summaries severity-ordered when reporting findings.
