# Superleads Product Market Evidence Compiler Validation

## Scope

Phase 1 adds a compact-note compiler for the existing `ProductMarketAnalysisGraph`.
It does not search, open URLs, classify authorities, add schema objects, or
promote evidence status. It only reduces repeated graph authoring after a real
Source / Observation already exists.

## Changes

- Added `scripts/compile_product_market_evidence.py`.
- Added `tests/test_product_market_evidence_compiler.py`.
- Added product-market Skill and common-command instructions.
- Preserved the existing schema and validator boundary.
- Follow-up UAT adds matrix-row merging, multi-row support, and partial unknown
  product-attribute removal without changing the graph schema.
- Bumped plugin manifests to `0.1.10`.

## Safety Contract

- Evidence notes must reference an existing Observation.
- The Observation must be opened/captured/extracted/rendered and contain a
  non-empty verbatim excerpt.
- `source_excerpt_quote` must occur in that original excerpt.
- User-provided product attributes remain non-final and are not converted to
  `verified`.
- Search summaries, Source Packs, Query Plans, and model summaries cannot be
  compiler input.
- One note may use `row` or `rows`; repeated targets merge EvidenceCard
  references instead of duplicating a user-visible matrix row.
- A row can scope freshness and authority references separately from its
  EvidenceCard when the same source fact appears in multiple tables.

## UAT Comparison

The original ordinary-electric-kettle-to-US UAT graph remained unmodified at
`/tmp/electric_kettle_us_uat_graph_20260810.json`. A temporary source/
Observation graph skeleton plus 6 compact evidence notes and 2 user-provided
attributes was compiled in `/tmp`.

- Compiled graph: 6 EvidenceCards, 13 MatrixRows, 10 Gaps, and 2 attributes.
- Product unknowns retained only unresolved parts, including `频率`; known
  voltage and wattage no longer appeared as wholly unknown.
- Product-market validator and audit passed; Markdown exported with 16 tables
  and `ready_with_limitations`.
- The temporary compact notes occupied 380 formatted JSON lines. This is a
  structure comparison reconstructed from the original graph, not an
  independently timed authoring measurement, so it does not prove a final
  percentage reduction yet.

## Verification

| Check | Result |
|---|---|
| `python3 -m unittest tests/test_product_market_evidence_compiler.py -v` | 5/5 passed |
| `python3 -m py_compile scripts/compile_product_market_evidence.py` | passed |
| `python3 evals/run_product_market_analysis_evals.py --suite all` | 75/75 passed |
| `python3 evals/run_superleads_plugin_distribution_evals.py --suite all` | 6/6 passed |
| `python3 evals/run_evals.py --suite all` | 719/719 passed |

The focused pass test compiles an opened Observation, preserves a user-provided
`1500 W` product attribute, creates linked EvidenceCard / MatrixRow objects, and
validates the resulting graph. The fail test rejects an unopened COO
Observation. Full plugin distribution sync and cross-route regression were the
final release checks for this change, and both passed after installing plugin
version `0.1.10` to `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.10`.
