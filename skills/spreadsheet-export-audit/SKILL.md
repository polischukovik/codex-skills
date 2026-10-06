---
name: spreadsheet-export-audit
description: Use when a task needs spreadsheet-style profiling of large CSV or XLSX report exports, especially to compare generated outputs to golden samples by headers, value domains, blanks, distributions, and representative anomalies without doing naive full row-by-row diffs.
---

# Spreadsheet Export Audit Skill

## Workflow
1. Start with structural checks.
   - header set
   - column count
   - obvious formatting/type mismatches
2. Profile value domains before inspecting rows.
   - distinct counts
   - top values
   - blank/null rates
   - suspicious outliers
3. Compare distributions, not only examples.
   - workmode distributions
   - flag distributions
   - date/time formatting domains
   - reason-code populations
4. Pull representative anomalies only after the profile points at a problem.
5. Summarize the mismatch as:
   - structural mismatch
   - semantic mismatch
   - likely implementation drift
   - likely sample/runtime drift

## Tooling
- Prefer the existing `spreadsheet` skill for heavy CSV/XLSX processing.
- Use shell tools first for quick sizing and counts: `wc`, `head`, `cut`, `rg`, `sort`, `uniq`, `awk`.
- Use spreadsheet/Python tooling when the export is too large or the analysis needs grouped statistics.

## Read When Needed
- `references/checklist.md` for the audit sequence.
- `references/metrics.md` for reusable comparison metrics.

## Practical Rules
- Do not start with full row-by-row diffs on very large files.
- Always normalize expectations first: headers, formatting rules, and value encodings.
- Use representative anomaly rows only after a distribution-level mismatch is established.
