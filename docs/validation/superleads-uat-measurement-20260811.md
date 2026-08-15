# Superleads Real-Business UAT Measurement Ledger

Date: 2026-08-11

## Scope

This change makes real-business UAT measurement repeatable without changing
any research graph schema, business validator, evidence boundary, delivery
status, route, or exporter behavior.

The original `/tmp`-only measurement layout is superseded for formal success
claims. A current formal UAT uses a durable ignored directory below
`.plugin-eval/manual/uat-runs/`, stages its runtime package and gate artifacts,
and emits `release_identity.json` plus `evidence_manifest.json`. The new
`verify` subcommand recomputes the manifest hashes after the directory is
copied. A temporary run can still preserve a failed diagnostic ledger, but
`finalize` cannot report it as a portable formal UAT success.

## Change

`scripts/measure_superleads_uat.py` creates a ledger in a dedicated run
directory. The caller records existing gate results rather than reimplementing
them. `finalize` writes `uat_metrics.json` with:

- first-pass success based on the first result of every required gate;
- total failed attempts as repair cycles and their failure classes;
- separate active and wall-clock seconds;
- exact byte comparison of `git-before.txt` and `git-after.txt`;
- explicit real-token telemetry availability, without an estimate fallback.
- plugin manifest/version, Git HEAD, and staged runtime package identity;
- staged file/directory gate artifacts with relative paths and SHA-256;
- a sealed evidence manifest that is independently checked by `verify`.

The tool returns nonzero when required gates do not finish passed, an active
interval remains open, or the Git snapshots differ. It still writes the metric
file so a failed measurement is inspectable.

## Regression Coverage

`tests/test_superleads_uat_measurement.py` covers:

1. A corrected validator run is final-pass but not first-pass, with one repair
   cycle and unchanged Git bytes.
2. A one-byte newline difference in the Git snapshot is a measurement failure.
3. A missing required gate is neither a formal protocol pass nor first-pass.

## Verification

| Check | Result |
|---|---|
| UAT measurement tests | 3/3 passed |
| `evals/run_evals.py --suite default` | 127/127 passed |
| `evals/run_evals.py --suite all` | 720/720 passed |
| `evals/run_evals.py --suite deep` | 677/677 passed |
| Plugin distribution eval | 9/9 passed |
| Runtime package strict check | passed; 123 files, 1,837,379 bytes |
| Installed cache check | `superleads@fleix 0.1.13` passed |
| Skill quick validation and Markdown delivery smoke | passed |
| `git diff --check` | passed |

No live research UAT was run as part of this code change. The next three-route
measurement must use new business objects and the current host's actual
search/source capabilities.
