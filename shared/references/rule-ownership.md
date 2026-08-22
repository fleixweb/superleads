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

The following cross-cutting owners are explicit and should be linked rather
than reimplemented by lower layers:

| Cross-cutting contract | Owner | Responsibility |
|---|---|---|
| No-script delivery | `shared/references/no-script-delivery-contract.md` | 无脚本交付、准确披露语义和禁止运行时自救。 |
| Canonical disclosure | `scripts/_superleads_common.py` | `DETERMINISTIC_VALIDATION_DISCLOSURE` and `SCHEMA_PROFILE_UNAVAILABLE_DISCLOSURE`. |
| 最终用户可见边界 | `scripts/validate_superleads_user_visible_output.py` | 终局回复、路径、宿主指令、运行时细节和支持页脚的最终检查。 |
| 交付门禁 | `scripts/audit_delivery.py` | 交付状态、审计证据和可交付层级门禁。 |
| 结构门禁 | `scripts/validate_research_graph.py` | 图谱结构与确定性业务不变量校验。 |

The default Candidate minimum structure is implemented by
`validate_research_graph.py` and exercised by the default eval suite; its
business explanation belongs in the default-discovery policy/reference. URL
safety is implemented by `_superleads_common.py` and reused by validators and
exporters. Do not duplicate either implementation in Skills.
