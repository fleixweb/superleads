# Review and Remediation Policy

## Review modes and provenance

- `independent`: a separate reviewer pass checks semantics and evidence. Standard delivery requires one current passed `ReviewAttestation` binding Run, Brief, Plan, review cycle, opaque executor/reviewer actor and session IDs, conclusion, reviewed formal Entity/Assessment IDs, and the reviewed subject hash.
- `self_review_fallback`: the same agent reviews because independent review is unavailable. Standard delivery may proceed only with disclosure; full-review delivery is not allowed.
- `not_run`: no review. Only initial or clearly pending outputs may be delivered.

`reviewed_subject_hash` is SHA-256 over the documented canonical semantic
projection: all research-conclusion inputs, including Run, Brief, Plan,
Candidates, Entities, Sources, Observations, Claims, ClaimEvidence,
ScopeDecisions, Assessments, ReviewFindings, SearchLogs, contacts, and other
research records. It excludes only `review_attestations`, `audits`, and
`delivery_manifests` to avoid self-reference; collections are sorted by their
formal IDs before canonical JSON serialization. It is not a raw JSON file-byte
hash.

In this local deployment, `provenance_level` is always
`declared_separate_session`. It permits standard delivery only with the
disclosure “本次复核由独立会话声明完成，未获得平台身份验证。”.
`full_review_package` is not available in this local deployment. Different
JSON IDs prove structured declarations only; they cannot by themselves prove
truly independent people or models.

A failed attestation consumes its `review_cycle_id`; a later independent
review must use a new cycle. Audit snapshots and DeliveryManifests must cite
the current attestation, subject hash, provenance level, and Run cycle.

## Review checklist

Check source support for every Claim, contact association evidence, Hypothesis/Claim separation, Assessment certainty, identity matching, conflict preservation, delivery status labels, and whether the current Brief's customer-selection contract was followed.

For new customer development, independently compare the user's retained
wording with the free-text contract, verify that the Plan covers every
selection and exclusion rule, and check that each positive Entity has a
same-Run/Brief in-scope ScopeDecision. Treat keyword similarity, a prominent
brand, manufacturer status, or a complete contact record as insufficient by
itself. A referenced competitor/brand must be `reference_only` unless the
current Brief expressly permits it. Do not describe `not_observed` as proof
that an excluded business fact does not exist.

## Finding severities

- `critical`: misleading or unsafe-for-delivery error, such as guessed contacts or wrong company-contact assignment.
- `major`: materially incomplete or overstated evidence, unresolved required source, or unclosed review issue.
- `minor`: presentation, wording, or non-blocking completeness issue.

Use only statuses: `open`, `remediation_submitted`, `re_reviewed`, `verified_fixed`, `accepted_with_disclosure`, `rejected_with_reviewer_reason`.

Critical and major findings are blocking until `verified_fixed`. `accepted_with_disclosure` may be used only for non-misleading weak evidence or minor limitations. `rejected_with_reviewer_reason` records disagreement with a finding but does not close critical or major delivery blockers.
