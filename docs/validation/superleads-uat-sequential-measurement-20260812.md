# Superleads Sequential UAT Measurement Follow-up

Date: 2026-08-12

## Finding

The three real-UAT result directories were not stale cache replays. Their
business gate timestamps and graph/report file mtimes show separate work:

- bulk gates: approximately 17:27-17:33 UTC;
- background gates: approximately 17:37-17:45 UTC;
- market gates: approximately 18:12-18:20 UTC.

However, all three measurement ledgers were initialized at approximately
17:18:32 UTC, opened their active intervals at approximately 17:18:48 UTC,
and finalized together at approximately 18:26:44 UTC. The reported
`active_elapsed_seconds` and `wall_elapsed_seconds` therefore include the same
overlapping session span three times and must not be compared between routes.
The fixed checklist now requires one complete route ledger before the next
route starts and rejects fixed `T000000Z` run-directory naming as a measurement
warning.

## Changes

`measure_superleads_uat.py` now treats any recorded gate's first failure as a
failure of end-to-end first-pass success, even if the caller omitted that
intermediate gate from `--required-gate`. This prevents a market compiler
failure from being reported as `first_pass_success=true` merely because later
delivery gates passed. Product-market UAT instructions require:

```text
preflight -> input_precheck_notes -> compiler -> input_precheck_graph ->
validator -> audit -> markdown_export -> workbook_export -> user_visible -> claimed_path
```

The input precheck also requires `ready` and `export_with_source_note`
ContactClaim association evidence to name its resolved Entity. Manual-review
public officer or career clues remain exempt because they are intentionally
shown as pending association rather than exportable confirmed contacts.

## Verification

| Check | Result |
|---|---|
| Measurement + input-precheck tests | 7/7 passed |
| `python3 evals/run_evals.py --suite all` | 721/721 passed |
| `python3 evals/run_evals.py --suite deep` | 678/678 passed |
| Plugin distribution eval | 9/9 passed |
| Runtime package | 124 files, 1,868,485 bytes |
| Installed cache | `superleads@fleix 0.1.15`, byte-identical to `dist/superleads` |
| Skill quick validation | passed |
| Formal Markdown smoke | passed |
| `git diff --check` | passed |

The existing three UAT reports remain valid for final gate outcomes and
evidence-boundary review, but their route-level elapsed-time metrics are
explicitly not a comparable baseline. No new live UAT was run in this code
change.
