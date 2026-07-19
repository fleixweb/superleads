# Batch development export readiness - 2026-07-20

## Scope

This note validates the primary Superleads delivery path, not the temporary
test workbook under `tmp/`.

Primary path:

`product + market/scope -> batch discovery -> standard development workbook`

Customer background research remains a separate branch and is not used as a
precondition for batch development exports.

## Current export contracts

### Initial discovery

Command shape:

```bash
python3 -B scripts/export_workbook.py graph.json --output-dir out --mode initial
```

Expected user-facing sheets:

- `发现候选池`
- `联系方式汇总`
- `官网与来源链接`
- `搜索覆盖与收敛`
- `待核查事项`
- `已排除客户`
- `风险与说明`

Purpose: candidate pool and weak/partial findings with visible status labels.
It is not a formal standard development list.

### Standard development list

Command shape:

```bash
python3 -B scripts/export_workbook.py graph.json --output-dir out --mode standard --manifest out/manifest.json
```

Expected user-facing sheets:

- `客户信息总表`
- `联系方式汇总`
- `开发建议`
- `官网与来源链接`
- `待核查事项`
- `风险与说明`

Formal standard export requires:

- current Brief and Run;
- Plan;
- current customer selection contract for new-customer development;
- current in-scope ScopeDecision for each positive Entity;
- positive Assessment with usable Claim evidence;
- review provenance accepted by the delivery audit;
- graph hash freshness through the delivery audit/manifest chain.

Only current positive Entities marked with the business label
`符合本次方向` are shown in standard customer, contact, and development
suggestion sheets. `需确认`, `不符合本次方向`, and `仅作参考` are kept out of
recommended customer rows.

### Inquiry

Command shape:

```bash
python3 -B scripts/export_workbook.py graph.json --output-dir out --mode inquiry --manifest out/manifest.json
```

Expected user-facing sheets:

- `询盘待办`
- `来信联系人`
- `询盘信息摘要`
- `待补充信息`
- `来源说明`

Inquiry export is a follow-up queue. It is not a buyer qualification or
standard development list.

## Smoke validation

Fixture used:

`evals/fixtures/pass_geography_searchlog_standard.json`

Commands run:

```bash
python3 -B scripts/validate_research_graph.py evals/fixtures/pass_geography_searchlog_standard.json --format json
python3 -B scripts/audit_delivery.py evals/fixtures/pass_geography_searchlog_standard.json --delivery-status standard_development_list --format json
python3 -B scripts/export_workbook.py evals/fixtures/pass_geography_searchlog_standard.json --output-dir /tmp/superleads_batch_export_check.xkPLW3/standard_csv --mode standard --format csv --manifest /tmp/superleads_batch_export_check.xkPLW3/standard_csv/manifest.json
python3 -B scripts/export_workbook.py evals/fixtures/pass_geography_searchlog_standard.json --output-dir /tmp/superleads_batch_export_check.xkPLW3/initial_csv --mode initial --format csv
```

Observed results:

- graph validation: `ok=true`, `issue_count=0`
- standard audit: `ok=true`, `delivery_status=standard_development_list`, `issue_count=0`
- standard export files:
  - `客户信息总表.csv`
  - `联系方式汇总.csv`
  - `开发建议.csv`
  - `官网与来源链接.csv`
  - `待核查事项.csv`
  - `风险与说明.csv`
  - `manifest.json`
- initial export files:
  - `发现候选池.csv`
  - `联系方式汇总.csv`
  - `官网与来源链接.csv`
  - `搜索覆盖与收敛.csv`
  - `待核查事项.csv`
  - `已排除客户.csv`
  - `风险与说明.csv`

User-facing CSV scan found no local paths, internal graph/audit artifact names,
hash labels, or search query fields.

## Regression validation

Commands run:

```bash
python3 -B evals/advanced_gate_tests.py
python3 -B evals/run_evals.py --suite all
git diff --check
```

Results:

- advanced gate regressions: `suite=all groups=42 failures=0`
- full eval suite: `total=662 passed=662 failed=0`
- diff whitespace check: passed

## Readiness conclusion

The batch customer-development export path is currently complete enough for
formal deterministic delivery when the research graph satisfies the standard
contract. The export chain validates, audits, emits the expected Chinese
business sheets, creates a manifest for formal modes, filters non-current or
out-of-scope rows, and redacts held/inferred contacts and local paths.

The temporary workbook in `tmp/` is not part of this readiness conclusion.

## Remaining operational boundary

The repository can formally export a completed, evidence-backed Research Graph.
Actual discovery execution still depends on available search/source-opening
capabilities or user-provided source URLs/materials. Without reliable search
and source opening, the system should stop at planning or initial candidate
samples rather than pretending to have completed a formal standard list.
