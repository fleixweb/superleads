# Product-Market Evidence Compiler Phase 1.2

## Goal

Reduce repeated manual JSON authoring in the product outbound market route while
preserving the existing graph schema, validator, authority boundary, and delivery
outputs.

## Frozen baseline

The independent blind electric-kettle-to-US UAT from
`/tmp/superleads-uat-electric-kettle-blind-20260810T144151Z` is the before sample:

- 2,990 seconds elapsed.
- 1,389 lines of base graph plus 622 lines of compact notes.
- 8 opened Sources/Observations, 8 EvidenceCards, 16 MatrixRows, and 12 Gaps.
- Validator, audit, Markdown/CSV/XLSX export, and claimed-path checks passed.

## Implementation tasks

### Task 1: Regression tests first

- [x] Add a compact authority-note test using an opened Observation. Assert that four
  existing Authority arrays are populated and an omitted status defaults to
  `candidate_needs_check` rather than `verified_for_fact_domain`.
- [x] Add a row-template test. Assert that an evidence note can reference a template
  ID through `target_row_ids`, produces the same existing MatrixRow shape, and
  still validates. Keep legacy `row`/`rows` coverage unchanged.
- [x] Run the focused test file and confirm the new tests fail because the input keys
  are not yet accepted.

### Task 2: Compact authority compilation

- [x] Accept `authority_notes` as compiler-only input.
- [x] Require an opened Observation, a verbatim `source_excerpt_quote`, the human
  authority assertion, fact domain, jurisdiction role/name, and explicit support
  and non-support boundaries.
- [x] Compile one note into the existing AuthorityProfile,
  AuthorityIdentityEvidence, AuthorityCapability, and AuthorityVerificationRecord
  objects. Generate stable IDs from `authority_note_id`.
- [x] Copy an explicitly supplied verification status; default to
  `candidate_needs_check` and `not_reviewed`. Never infer an authority from a URL,
  domain, or institution name and never promote a status.
- [x] Allow evidence notes to use `authority_note_ids` as a compact reference; retain
  direct `authority_verification_record_ids` compatibility.

### Task 3: Matrix row templates

- [x] Accept `matrix_row_templates` as compiler-only input. Each template contains an
  ID and the existing row payload.
- [x] Allow evidence notes to use `target_row_ids` instead of `row`/`rows`.
- [x] Resolve templates before compiling notes, reject missing or duplicate IDs, and
  preserve the existing row merge and legacy input behavior.

### Task 4: Verification and documentation

- [x] Run focused unit tests, Python compilation, product-market evals, plugin
  distribution evals, and the full default/all/deep suites.
- [x] Replay the frozen UAT graph with the compact notes as an offline equivalence
  check. This is not a fresh web UAT and must not be reported as one.
- Update `HANDOFF.md`, `TASKS.md`, and add a validation record with before/after
  structural metrics and any inability to run a fresh web UAT in the current
  environment.

Fresh web UAT remains pending until the current Run exposes `search.web` and
`source.open`; the preflight gate was run and correctly blocked it.

## Explicitly out of scope

No country packs, automatic web search, new schema fields, validator/error-code
changes, route changes, delivery-status changes, or weakening of evidence rules.
