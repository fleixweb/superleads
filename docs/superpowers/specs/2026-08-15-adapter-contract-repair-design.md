# Adapter Contract Repair Design

## Scope

Repair the confirmed source-open contract defects, prevent ignored plugin-evaluation data from entering a runtime package, and bring release records current through version 0.1.19.

## Decisions

1. A failed source-open record may omit URL and extraction fields, as the Run schema permits. Binding first requires matching non-empty `source_id` and `observation_id`; each optional URL, title, excerpt, and locator field must agree when it is present. A failed record with no identifying binding fields remains insufficient. When metadata-only verified records are otherwise identical, bind each Observation to an unconsumed operation before reporting reuse.
2. Shell HTTP credential and local-path scanning applies only to `curl`, `wget`, and `python_requests` observations. Native source-opening tools retain their existing URL, operation, and evidence checks without receiving a shell-specific error.
3. Runtime package construction must exclude ignored development/evaluation directories at every depth. Distribution validation must report nested forbidden directories, so a manually polluted package cannot pass.
4. Product-market validation shares the public source-restricted status set with the source-open contract, including the supported `login-wall` spelling.
5. Changelog and handoff/task records will summarize released versions 0.1.6 through 0.1.19 without inventing release facts beyond the existing repository history.

## Verification

- Regression tests prove the failed-operation and shell-scope behavior before implementation.
- Package tests build from a tree containing an ignored nested `.plugin-eval` directory and assert it is excluded; validation rejects a package that contains it.
- Run focused tests, standard-library discovery, product-market evaluations, and the complete evaluation suite. Build and validate a package from a clean `HEAD` export before release claims.
