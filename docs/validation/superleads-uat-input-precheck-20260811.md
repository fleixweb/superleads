# Superleads UAT Structured Input Precheck

Date: 2026-08-11

## Scope

This change adds a read-only structural gate before the existing formal
validator for the three formal Superleads routes:

- `bulk_customer_development`
- `customer_background_research`
- `product_outbound_market_analysis`

The gate is intentionally narrow. It does not search, open URLs, mutate a
graph, create evidence, or make a business conclusion. It catches four input
mistakes that repeatedly caused real-UAT repair loops:

1. source literals and field-level quotes not anchored in the cited Observation;
2. ContactPoint / ContactClaim source and association bindings;
3. graph and compact-note enum or shape errors;
4. user-provided product attributes that fail to project into the existing
   `产品档案与触发项` MatrixRow.

## Implementation

`scripts/precheck_superleads_uat_input.py` returns `precheck_only=true` and
`uat_precheck_*` diagnostics. Research routes use the existing
`research-graph.schema.json`, `_superleads_common.py` anchor helpers, and
contact association checks. Product-market runs use the existing product-market
schema; an optional `--notes` input checks compact evidence notes before
compilation, while a second graph-only pass checks compiled EvidenceCard refs
and user-attribute projection. The precheck never replaces the formal
validator, audit, or claimed-path check.

The `input_precheck` result is recorded by `measure_superleads_uat.py` as a
required UAT gate. The route Skills and the fixed UAT checklist document the
ordering and the repair rule: fix a structural precheck failure before running
the formal validator again.

## Regression Coverage

The existing pass graphs for all three routes pass the precheck. Negative tests
prove that the gate fails early for:

- a contact literal absent from the cited Observation;
- an association sentence absent from its association Observation;
- an invalid contact enum;
- a compact market-note quote absent from the Observation;
- a user-provided product attribute without a matching visible product-profile
  row.

## Verification

| Check | Result |
|---|---|
| `py_compile` for precheck, measurement, compiler and main eval runner | passed |
| Precheck / measurement / compiler unit tests | 13/13 passed |
| Product-market analysis suite | 75/75 passed |
| Customer-background suite | 7/7 passed |
| Markdown delivery suite | 9/9 passed |
| User-visible output suite | 15/15 passed |
| `check_superleads_formal_markdown_delivery.py` smoke | `ok=true`, `issue_count=0` |
| Skill quick validation | `using-superleads`: valid; `analyzing-product-outbound-market`: valid |
| `python3 evals/run_evals.py --suite default` | 128/128 passed |
| `python3 evals/run_evals.py --suite all` | 721/721 passed |
| `python3 evals/run_evals.py --suite deep` | 678/678 passed |
| Runtime package build | 124 files, 1,867,191 bytes |
| Source runtime-package strict check | passed |
| Plugin distribution suite | 9/9 passed |
| Installed `0.1.14` cache strict check | passed; 124 files, 1,867,191 bytes |
| `diff -qr dist/superleads /home/fleix/.codex/plugins/cache/fleix/superleads/0.1.14` | no differences |
| `git diff --check` | passed |

No live research UAT was run as part of this code change. Existing route
behavior and `tmp/stage5_chillys/` were left unchanged. The current
`0.1.14` runtime package and installed cache are synchronized; no new
SearchLog, Source, Observation, or Claim was created.
