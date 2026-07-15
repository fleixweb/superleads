# Review and Remediation Policy

## Review modes

- `independent`: a separate reviewer pass checks semantics and evidence. Full delivery may proceed if no blocking findings remain and the brief requests full-review evidence depth.
- `self_review_fallback`: the same agent reviews because independent review is unavailable. Standard delivery may proceed only with disclosure; full-review delivery is not allowed.
- `not_run`: no review. Only initial or clearly pending outputs may be delivered.

## Review checklist

Check source support for every Claim, contact association evidence, Hypothesis/Claim separation, Assessment certainty, identity matching, conflict preservation, and delivery status labels.

## Finding severities

- `critical`: misleading or unsafe-for-delivery error, such as guessed contacts or wrong company-contact assignment.
- `major`: materially incomplete or overstated evidence, unresolved required source, or unclosed review issue.
- `minor`: presentation, wording, or non-blocking completeness issue.

Use only statuses: `open`, `remediation_submitted`, `re_reviewed`, `verified_fixed`, `accepted_with_disclosure`, `rejected_with_reviewer_reason`.

Critical and major findings are blocking until `verified_fixed`. `accepted_with_disclosure` may be used only for non-misleading weak evidence or minor limitations. `rejected_with_reviewer_reason` records disagreement with a finding but does not close critical or major delivery blockers.
