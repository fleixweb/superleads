# Rule Ownership

Use the following authority order when instructions appear in more than one
place. Lower layers should link to the authority rather than copy its detailed
implementation.

| Rule type | Authoritative layer | Examples |
|---|---|---|
| Deterministic hard constraints | `scripts/` + `evals/` | Search summaries cannot become facts; guessed emails and cross-Entity contacts are blocked; same-name trade records cannot auto-bind; trade records cannot imply China procurement; public URL safety; default Candidate minimum structure. |
| Data shape | `shared/schemas/` | Required fields, IDs, allowed status values, and object relationships. |
| Business semantics | `shared/policies/` + `shared/references/` | Weak-evidence handling, relevance meanings, public-signal interpretation, source boundaries, and export presentation. |
| Agent routing and execution | `skills/` | When to enter discovery, when optional contact/identity guides apply, and when to enter deep verification. |
| Product boundary and overall contract | `SUPERLEADS_DEVELOPMENT_SPEC.md` | Discovery-first product scope, compatibility promises, and non-goals. |

The default Candidate minimum structure is implemented by
`validate_research_graph.py` and exercised by the default eval suite; its
business explanation belongs in the default-discovery policy/reference. URL
safety is implemented by `_superleads_common.py` and reused by validators and
exporters. Do not duplicate either implementation in Skills.
