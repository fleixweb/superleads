# Portable Real UAT Evidence Design

## Goal

Make a completed Superleads real-business UAT independently reviewable and
portable. A successful result must prove the exact plugin/runtime package,
the real source-collection chain, every delivery gate, and the final artifacts.
An interrupted run must remain an explicitly failed or blocked evidence bundle.

## Scope

This changes only the UAT measurement and evidence-capture layer. It does not
change research schemas, source eligibility, validators, business conclusions,
or exporter behavior.

## Decision

Extend `scripts/measure_superleads_uat.py` into the owner of a sealed UAT
evidence directory.

1. `init` records a release identity: plugin manifest version and SHA-256,
   Git HEAD, exact Git status snapshot, and a deterministic inventory/hash of
   the runtime plugin package used for the run.
2. `record-gate --artifact` copies each supplied file or directory into the
   run's `artifacts/` directory before recording its relative path and
   SHA-256. The original may subsequently disappear without invalidating the
   captured evidence.
3. `finalize` writes an evidence manifest containing only relative artifact
   paths and hashes. It verifies every recorded artifact, the required gates,
   a closed active interval, unchanged source checkout state, and a
   non-ephemeral evidence location before it can report formal UAT success.
4. Formal runs must include a `source_evidence` gate containing the current
   Run's operation record and the graph/Observation evidence. For the product
   market route, `compiler` remains a required gate whenever it is used.

The normal durable location is an ignored subdirectory below
`.plugin-eval/manual/uat-runs/`. It is outside `/tmp`, does not pollute the
source Git status, and is copyable as a self-contained directory. The evidence
manifest permits a reviewer to verify a copied directory without relying on
the original absolute paths.

## Success Contract

A measurement may return `formal_uat_protocol_status=passed` only when all of
the following hold:

- all declared required gates finally pass and all first attempts pass for a
  first-pass success claim;
- every required gate has a readable, staged artifact;
- the UAT directory is not under `/tmp` or another system temporary directory;
- the release identity includes a readable manifest and runtime package
  inventory;
- the generated evidence manifest verifies each staged artifact hash;
- no active interval remains open and the source Git status bytes are
  unchanged.

Otherwise `finalize` writes the same ledger, metrics, identity, and evidence
manifest but returns nonzero with explicit failure reasons. It must never
convert an external model/service interruption into a successful UAT.

## Evidence Layout

```text
.plugin-eval/manual/uat-runs/<utc-run-id>/
  release_identity.json
  uat_measurement.json
  uat_metrics.json
  evidence_manifest.json
  git-before.txt
  git-after.txt
  artifacts/
    001-preflight-...
    002-source_evidence-...
    ...
```

`evidence_manifest.json` stores artifact logical IDs, relative paths, file
hashes, directory inventories, and the release-identity hash. It intentionally
does not claim that a retained artifact makes an unexecuted gate pass.

## Tests

Add measurement regressions for:

- a formal success with a durable directory, staged gate artifacts, and a
  versioned runtime package inventory;
- a temporary-directory run that cannot claim formal success;
- an artifact removed after `record-gate` while its staged copy remains
  independently verifiable;
- a missing/tampered staged artifact that makes `finalize` fail;
- an absent release identity/runtime package that makes `finalize` fail.

Update the real-business UAT checklist and common commands to require the
durable directory, `source_evidence`, release identity, and the evidence
manifest. Then execute one new source-capable product-market UAT. Its result is
published only as passed when the sealed bundle is complete; otherwise it is
published as a retained blocked/failed attempt.
