# Superleads Bulk SearchLog-Candidate Precheck

## Scope

This change moves the existing SearchLog/Candidate bidirectional discovery-link
contract into the read-only UAT input precheck. It does not change the research
graph schema, the formal graph validator, route behavior, evidence rules, or
the UAT runner.

The precheck now catches:

- SearchLog `result_refs.candidate_id` values that do not resolve to a Candidate;
- `search_web` Candidates without an existing linked SearchLog;
- Run/Brief/Plan binding mismatches between a Candidate and its linked SearchLog;
- Candidates that are linked from a SearchLog but do not point back to that log;
- Candidates that point to a SearchLog but do not appear in that log's `result_refs`.

## Verification

- Focused precheck tests: 4/4 passed, including the bidirectional-link negative
  case. Existing pass graphs remain accepted; the negative case is a mutated
  copy of `evals/fixtures/pass_default_discovery_candidate_pool.json`.
- `python3 evals/run_evals.py --suite all`: 721/721 passed.
- `python3 evals/run_evals.py --suite deep`: 678/678 passed.
- Runtime distribution eval: 9/9 passed; package and installed cache are
  byte-identical at `0.1.16` (124 files, 1,872,860 bytes).
- `git diff --check` and runtime package strict distribution validation passed.
- No live UAT was run as part of this code change. The next measurement should
  rerun the Bulk route and compare first precheck/validator issue counts and
  repair cycles against the 2026-08-11 sequential baseline.
