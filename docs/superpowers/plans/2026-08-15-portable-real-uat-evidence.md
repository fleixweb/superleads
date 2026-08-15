# Portable Real UAT Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make real-business UAT evidence version-bound, self-contained, hash-verifiable, and unable to pass from an ephemeral or incomplete run.

**Architecture:** `measure_superleads_uat.py` remains a route-neutral ledger and gains only evidence-capture responsibilities. `init` stages a runtime package and writes release identity; `record-gate` snapshots supplied artifacts; `finalize` produces a relative evidence manifest and treats portability/identity/artifact failures as formal UAT failures; `verify` recomputes the stored hashes in a copied run directory.

**Tech Stack:** Python 3 standard library (`argparse`, `hashlib`, `json`, `shutil`, `tempfile`, `pathlib`), existing unittest suite, existing runtime package builder.

---

### Task 1: Define the UAT Evidence Regression Contract

**Files:**
- Modify: `tests/test_superleads_uat_measurement.py`
- Test: `tests/test_superleads_uat_measurement.py`

- [ ] **Step 1: Add durable-run and runtime-package test helpers**

Add a helper that creates test runs only below ignored `.plugin-eval/manual/uat-test-runs/`, and a helper that creates a minimal runtime package directory containing `.codex-plugin/plugin.json`:

```python
def _durable_run_dir(self, tmp: tempfile.TemporaryDirectory[str], name: str) -> Path:
    root = ROOT / ".plugin-eval" / "manual" / "uat-test-runs" / Path(tmp.name).name
    run_dir = root / name
    run_dir.mkdir(parents=True)
    self.addCleanup(shutil.rmtree, root, ignore_errors=True)
    return run_dir

def _runtime_package(self, directory: Path, version: str = "0.1.18") -> Path:
    manifest = directory / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": "superleads", "version": version}), encoding="utf-8")
    (directory / "skills" / "sample.txt").parent.mkdir(parents=True)
    (directory / "skills" / "sample.txt").write_text("runtime payload\n", encoding="utf-8")
    return directory
```

- [ ] **Step 2: Add the failing portable-success test**

Write `test_finalize_seals_staged_artifacts_with_release_identity`. It must initialize with `--runtime-package`, record `preflight`, `source_evidence`, and `validator` with an external JSON artifact, finalize with those three required gates, and assert all of the following:

```python
self.assertEqual(payload["formal_uat_protocol_status"], "passed")
self.assertTrue(payload["portable_evidence"])
self.assertEqual(payload["release_identity"]["plugin_version"], "0.1.18")
self.assertTrue((run_dir / "release_identity.json").is_file())
self.assertTrue((run_dir / "evidence_manifest.json").is_file())
self.assertTrue((run_dir / "runtime_package").is_dir())
self.assertTrue((run_dir / "artifacts").is_dir())
verify = self._run("verify", "--run-dir", str(run_dir))
self.assertTrue(verify["ok"])
```

Run: `python3 -m unittest tests/test_superleads_uat_measurement.py -v`

Expected: FAIL because `init` lacks `--runtime-package`, `verify` does not exist, and current `finalize` has no portable evidence fields.

- [ ] **Step 3: Add the failing ephemeral-run rejection test**

Write `test_finalize_rejects_temporary_run_directory_even_when_gates_pass`. Use `tempfile.TemporaryDirectory()` directly as the run root, initialize it with a valid runtime package, record required gates with artifacts, and assert:

```python
self.assertEqual(payload["formal_uat_protocol_status"], "failed")
self.assertIn("evidence_run_dir_ephemeral", payload["measurement_issues"])
self.assertFalse(payload["portable_evidence"])
```

Run: `python3 -m unittest tests/test_superleads_uat_measurement.py -v`

Expected: FAIL because a `/tmp` ledger can currently finalize passed.

- [ ] **Step 4: Add the failing staged-artifact integrity tests**

Write two tests using a durable run and a valid runtime package:

```python
def test_record_gate_stages_artifact_before_original_is_removed(self) -> None:
    artifact = external_dir / "preflight.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    self._run("record-gate", "--run-dir", str(run_dir), "--gate", "preflight",
              "--result", "passed", "--artifact", str(artifact))
    artifact.unlink()
    self.assertTrue(self._run("verify", "--run-dir", str(run_dir))["ok"])

def test_verify_and_finalize_reject_tampered_staged_artifact(self) -> None:
    staged = next((run_dir / "artifacts").glob("*-validator-*"))
    staged.write_text('{"ok": false}\n', encoding="utf-8")
    verify = self._run("verify", "--run-dir", str(run_dir), expected=1)
    self.assertIn("evidence_artifact_hash_mismatch:" + staged.relative_to(run_dir).as_posix(),
                  verify["verification_issues"])
```

In both tests, use the same `_record_required_passes` helper to record
`preflight`, `source_evidence`, and `validator` with a distinct external JSON
artifact, then call `finalize` with those three `--required-gate` arguments.
The second test also asserts that `finalize` exits `1` and retains the hash
mismatch in `measurement_issues`.

Run: `python3 -m unittest tests/test_superleads_uat_measurement.py -v`

Expected: FAIL because `record-gate` only records the original absolute path and no verification exists.

- [ ] **Step 5: Add the failing release-identity completeness test**

Write `test_finalize_rejects_missing_runtime_package_identity`: initialize a durable ledger without `--runtime-package`, record passing artifacts for every required gate, finalize, and assert `release_identity_runtime_package_missing` is present and the status is failed.

Run: `python3 -m unittest tests/test_superleads_uat_measurement.py -v`

Expected: FAIL because the existing ledger has no release identity requirement.

- [ ] **Step 6: Commit the red tests**

```bash
git add tests/test_superleads_uat_measurement.py
git commit -m "test: define portable UAT evidence contract"
```

### Task 2: Implement Sealed Evidence Capture and Verification

**Files:**
- Modify: `scripts/measure_superleads_uat.py`
- Test: `tests/test_superleads_uat_measurement.py`

- [ ] **Step 1: Add deterministic identity and artifact helpers**

Add `shutil` and `tempfile` imports plus a helper section with
`_sha256_bytes`, `_sha256_file`, `_relative_to_run`, `_is_ephemeral_directory`,
`_directory_inventory`, `_directory_digest`, `_stage_artifact`, and
`_capture_release_identity`. Keep all hashes SHA-256 and all stored evidence
paths relative to `run_dir`.

`_stage_artifact` must reject unreadable sources, symlinks, and a source that is the whole run directory or inside `run_dir/artifacts`. It copies a regular file with `copy2` and a directory with `copytree` configured not to retain symlinks, then returns `relative_path`, `kind`, `sha256`, `byte_count`, and a deterministic file inventory for directories. `_capture_release_identity` must stage the runtime package at `runtime_package/`, parse the manifest's string `name` and `version`, and write `release_identity.json` containing only portable identity fields plus `git_head`, manifest hash, and runtime package inventory digest.

- [ ] **Step 2: Extend `init` and `record-gate` without weakening old failure semantics**

Change the parsers and ledger layout as follows:

```python
init.add_argument("--plugin-manifest", type=Path, default=ROOT / ".codex-plugin" / "plugin.json")
init.add_argument("--runtime-package", type=Path)
record_gate.add_argument("--artifact", action="append", default=[],
                         help="File or directory to snapshot into the UAT evidence bundle.")
```

`command_init` must increment `schema_version` to `2`, create `artifacts/`, call `_capture_release_identity`, and store its relative reference in the ledger. `command_record_gate` must stage every artifact before appending the event. Replace `artifact_path` with `artifacts`, a list of staged descriptors. Preserve failure-class validation and event ordering.

- [ ] **Step 3: Add manifest verification and a `verify` subcommand**

Implement `_evidence_manifest(ledger, run_dir)`, `_verify_evidence(run_dir,
ledger)`, and `command_verify(args)`. `_evidence_manifest` produces the
portable JSON object; `_verify_evidence` returns a list of stable issue IDs;
`command_verify` serializes that result under `verification_issues` and exits
nonzero when the list is non-empty.

The manifest must include a schema version, run ID, SHA-256 of `release_identity.json`, and every staged artifact descriptor. `_verify_evidence` must recompute each file/directory digest and return stable issue IDs:

```text
release_identity_missing
release_identity_manifest_invalid
release_identity_runtime_package_missing
evidence_artifact_missing:<relative-path>
evidence_artifact_hash_mismatch:<relative-path>
evidence_artifact_path_not_relative:<relative-path>
```

Register `verify` in `parse_args()` and `main()`. It returns `ok=true` only with zero verification issues; it does not alter any research result.

- [ ] **Step 4: Tighten `finalize` only for formal success claims**

Before computing status, write `evidence_manifest.json`, invoke `_verify_evidence`, and add its issues to `measurement_issues`. Add `evidence_run_dir_ephemeral` when the resolved run directory is under `tempfile.gettempdir()`. For each required gate, require that at least its final passing event has one staged artifact; append `required_gate_artifact_missing:<gate>` otherwise.

Set the following result fields:

```python
"release_identity": ledger.get("release_identity"),
"evidence_manifest": "evidence_manifest.json",
"portable_evidence": not any(issue.startswith((
    "evidence_run_dir_ephemeral", "release_identity_", "evidence_artifact_",
    "required_gate_artifact_missing:"
)) for issue in measurement_issues),
```

Continue writing `uat_metrics.json`, even for all failures. Do not change the existing meanings of `first_pass_success`, repair cycles, capability failures, or Git snapshot mismatches.

- [ ] **Step 5: Run the measurement tests through green**

Run: `python3 -m unittest tests/test_superleads_uat_measurement.py -v`

Expected: all original tests adapted to record artifacts and use durable roots; all new evidence tests pass. Then run: `python3 -m py_compile scripts/measure_superleads_uat.py`.

- [ ] **Step 6: Commit the implementation**

```bash
git add scripts/measure_superleads_uat.py tests/test_superleads_uat_measurement.py
git commit -m "feat: seal portable UAT evidence bundles"
```

### Task 3: Update the Formal UAT Operating Contract

**Files:**
- Modify: `docs/validation/superleads-real-business-uat-checklist.md`
- Modify: `docs/superleads-common-commands.md`
- Modify: `docs/validation/superleads-uat-measurement-20260811.md`
- Modify: `skills/using-superleads/SKILL.md`

- [ ] **Step 1: Document a durable UAT directory and release identity**

Replace `/tmp/superleads-uat-example` examples with:

```bash
RUN_DIR="$PWD/.plugin-eval/manual/uat-runs/superleads-uat-$(date -u +%Y%m%dT%H%M%SZ)"
python3 scripts/build_superleads_plugin_package.py --output "$PWD/dist/superleads" --format json
python3 scripts/measure_superleads_uat.py init \
  --run-dir "$RUN_DIR" \
  --route product_outbound_market_analysis \
  --runtime-package "$PWD/dist/superleads" \
  --token-usage-availability unavailable --format json
```

State explicitly that a `/tmp` run may preserve diagnostics but can never be reported as a portable formal UAT success.

- [ ] **Step 2: Require source evidence and staged artifacts**

Add the mandatory market-route gate order:

```text
preflight -> source_evidence -> input_precheck_notes -> compiler ->
input_precheck_graph -> validator -> audit -> markdown_export ->
workbook_export -> user_visible -> claimed_path
```

For each gate command use `--artifact` with the actual result, graph, source adapter report, report, or workbook directory. State that `source_evidence` must retain current-run search/open operation records and the graph containing their resulting Sources/Observations; it is not a search-summary substitute.

- [ ] **Step 3: Document sealing and copied-directory verification**

Add:

```bash
python3 scripts/measure_superleads_uat.py finalize --run-dir "$RUN_DIR" \
  --required-gate preflight --required-gate source_evidence \
  --required-gate input_precheck_notes --required-gate compiler \
  --required-gate input_precheck_graph --required-gate validator \
  --required-gate audit --required-gate markdown_export \
  --required-gate workbook_export --required-gate user_visible \
  --required-gate claimed_path --format json
python3 scripts/measure_superleads_uat.py verify --run-dir "$RUN_DIR" --format json
```

Define a valid UAT handoff as the complete durable directory plus a passing `verify` result. Add `release_identity.json` and `evidence_manifest.json` to the required UAT fields table.

- [ ] **Step 4: Run documentation consistency checks**

Run:

```bash
rg -n '/tmp/superleads-uat-example|measure_superleads_uat.py init' \
  docs/superleads-common-commands.md docs/validation/superleads-real-business-uat-checklist.md \
  docs/validation/superleads-uat-measurement-20260811.md skills/using-superleads/SKILL.md
git diff --check
```

Expected: formal command examples point to the durable root; any remaining `/tmp` mention describes rejected/diagnostic behavior only.

- [ ] **Step 5: Commit the operating-contract changes**

```bash
git add docs/validation/superleads-real-business-uat-checklist.md \
  docs/superleads-common-commands.md docs/validation/superleads-uat-measurement-20260811.md \
  skills/using-superleads/SKILL.md
git commit -m "docs: require sealed portable UAT evidence"
```

### Task 4: Build and Execute the Independent Product-Market UAT

**Files:**
- Create: `.plugin-eval/manual/uat-runs/<utc-run-id>/` (ignored evidence bundle)
- Modify: none

- [ ] **Step 1: Verify code and runtime package before research**

Run:

```bash
python3 -m unittest tests/test_superleads_uat_measurement.py -v
python3 evals/run_product_market_analysis_evals.py --suite all
python3 evals/run_evals.py --suite all
python3 scripts/build_superleads_plugin_package.py --output "$PWD/dist/superleads" --format json
python3 scripts/check_superleads_plugin_distribution.py --plugin-root "$PWD/dist/superleads" --source-root "$PWD" --runtime-package --format json
```

Expected: all commands exit zero before the live UAT begins.

- [ ] **Step 2: Initialize the durable ledger and record capability preflight**

Create a UTC-named run directory under `.plugin-eval/manual/uat-runs/`. Run `init --runtime-package "$PWD/dist/superleads"`, then run `preflight_capabilities.py --require-formal-research --format json`, preserve its JSON in the run directory, and record it as the `preflight` artifact.

If the capability gate fails, record it as `failed --failure-class capability_adapter`, stop the active interval, finalize with all required gates, and publish the sealed blocked bundle. Do not fabricate a source-capable success path.

- [ ] **Step 3: Collect and preserve current-run sources**

Use actual native `web__run.search_query` and `web__run.open` where available. When a discovered public page cannot be opened natively, use `capture_public_http_source.py --url <discovered-public-url> --format json`; preserve both the native search adapter record and the curl adapter result. Build the new graph only from current-run, opened Observations. Save the source-operation records and graph together and record them as `source_evidence`.

- [ ] **Step 4: Complete existing UAT gates without manual delivery edits**

For the ordinary 220-240 V, 1500 W Chinese electric-kettle-to-US scenario: run both input prechecks, compiler, graph validator, audit, Markdown export, workbook export, user-visible validation, and claimed-path check. Save each exact command's JSON output and the graph/report/workbook in the durable directory; record every corresponding gate with `--artifact`.

Use the exact required gate list from Task 3. Any source restriction, product-document gap, candidate HS/HTS, tariff, compliance, clearance, route, or market-entry uncertainty remains in the deliverable as a limitation rather than being finalized.

- [ ] **Step 5: Seal and independently verify the UAT bundle**

Stop the active interval, run `finalize` with the full required gate list, then run `verify`. Copy the completed directory to a new temporary review location and run `verify` against the copy:

```bash
COPIED_RUN="$(mktemp -d)/uat-copy"
cp -a "$RUN_DIR" "$COPIED_RUN"
python3 scripts/measure_superleads_uat.py verify --run-dir "$COPIED_RUN" --format json
```

Expected success standard: `formal_uat_protocol_status=passed`, `first_pass_success=true`, `portable_evidence=true`, zero verification issues, and the copied directory also verifies. Otherwise report the retained run as blocked/failed with its exact issue IDs; do not call it a successful real E2E UAT.

- [ ] **Step 6: Record the verification result without changing the outcome**

Add a dated validation note under `docs/validation/` that links the durable run directory, release identity, evidence-manifest digest, final status, gate summaries, and copied-directory verification result. It must state the plugin version from `release_identity.json`, not infer it from the current manifest.

### Final Verification

- [ ] Run `python3 -m unittest tests/test_superleads_uat_measurement.py -v`.
- [ ] Run `python3 evals/run_product_market_analysis_evals.py --suite all`.
- [ ] Run `python3 evals/run_evals.py --suite all`.
- [ ] Run `python3 scripts/check_superleads_plugin_distribution.py --plugin-root "$PWD/dist/superleads" --source-root "$PWD" --runtime-package --format json`.
- [ ] Run `git diff --check`.
- [ ] Inspect the actual UAT `uat_metrics.json`, `release_identity.json`, and `evidence_manifest.json`; run `verify` from a copied directory before asserting success.
