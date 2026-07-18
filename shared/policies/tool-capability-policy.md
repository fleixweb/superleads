# Tool Capability Policy

| Capability | Highest allowed layer | Rule |
|---|---|---|
| `search.web` | 发现候选池 / SearchLog | Never supports Claim. |
| `source.open` | Observation | Can create Source and Observation. |
| `browser.render` | Observation | Can create Source and Observation. |
| `document.extract` | Observation | Can create document Source and Observation. |
| `image.inspect` | Observation / Candidate clue | May preserve OCR text or visual descriptions and create candidate/search leads. Never supports formal Claim, trademark ownership, or ready contact evidence. |
| `mail.read` | Inquiry / source-note contact | Read-only inbound-mail excerpts may create Inquiry and `export_with_source_note` contact evidence; never supports formal Claim, Assessment basis, or `ready`. |
| `source.capture` | Observation | Store excerpt, locator, and hash. |
| `url.canonicalize` | Source / Entity helper | Normalization only. |
| `entity.dedupe` | Provisional Entity helper | Not final identity resolution. |
| `translate.text` | Observation transform | Preserve original text and link derived observation. |
| `company.enrich` | Candidate clue / contextual | Cannot alone support main table facts. |
| `email.verify` | Contact quality | Does not prove source or ownership. |
| `domain.check` | Technical observation | Does not prove company ownership. |
| `social.visible.read` | Observation | Does not prove purchasing authority. |
| `registry.lookup` | Observation | Can support entity claims. |
| `trademark.lookup` | Observation | Can support brand/trademark claims. |
| `maps.lookup` | Observation | Can support map address/phone claims. |
| `memory.recall` | Plan priority | Never enters Claim or Assessment evidence. |

When a tool is missing, degrade output level instead of fabricating evidence. If no source-opening capability exists, provide a research plan or discovery candidate pool only.

## Codex CLI Native Web Search

For a Codex CLI session launched with `codex --search`, the Agent may report
the current session's native `web_search` through the controlled
`codex_cli_native_web_search` adapter format. The adapter is host-neutral at
the Superleads layer: it reads a host-provided report and never discovers
tools itself or installs/configures an external integration.

The native adapter owns only `search.web` and `source.open`. A valid report
overrides only those two values. `browser.render`, `document.extract`,
`image.inspect`, `mail.read`, and all other canonical capabilities are
independent host reports and are merged rather than discarded. An invalid
adapter yields no native search/source capability, but cannot downgrade a
separately available document or rendering capability.

For a Run carrying the native adapter report, every Observation capability
must also be explicitly reported as `available` by that same Run. This applies
to independent rendering or document capabilities as well as the two adapter-
owned capabilities. Omitted, `unknown`, and `missing` reports cannot support a
formal source.

## Codex CLI Shell HTTP Source Open

The `codex_cli_shell_http_source_open` provider can grant `source.open` after
one recorded public, read-only HTTP(S) `GET` succeeds. Its concrete tools are
`curl`, `wget`, and `python_requests`; they are implementation details under
the `codex_cli` host, not platform values and not a search capability. The
provider report and each Observation must show an explicitly available Run
capability, a permitted concrete tool, public credential-free HTTP(S) URLs,
source text, and a locator.

This provider never grants `search.web`; search summaries and links remain
discovery clues. It cannot use POST, cookies, Authorization headers, tokens,
passwords, private/loopback/local URLs, login-only pages, or any mechanism to
avoid access controls. A missing provider report, unverified GET, unlisted
tool, or conflicting source-opening provider fails closed.

The graph gate accepts only canonical host IDs when a platform is recorded:
lowercase ASCII letters, digits, and underscores. This preserves generic hosts
such as `hermes`, `claude`, and `workbuddy`; it rejects tool names, whitespace,
uppercase, and hyphen variants. The graph gate does not perform DNS lookup. It
rejects literal private or legacy numeric IP forms, but a real Shell HTTP
executor must also enforce global-address checks for each DNS resolution and
redirect to defend against DNS rebinding.

- `web_search` with a verified `search` operation grants `search.web` only.
  It may create SearchLogs and discovery candidates, never formal facts or
  contact evidence.
- `source.open` remains missing or unknown unless the same session actually
  opens a specific HTTP(S) URL and records its source identifier, non-empty
  verbatim excerpt, and locator. Search summaries, citations, and links do
  not meet that condition.
- A verified source-open capability raises only the preflight capability
  ceiling. It never bypasses the Source, Observation, formal evidence,
  identity, review, audit, freshness, contact, or delivery gates.
- If the tool is absent, fails, has no verified `search` operation, or only
  returns summaries, record the gap and use `research_plan_only` or
  `initial_lead_list` as applicable.

This policy does not bind Superleads to a model, provider, platform API, or
external tool server. It does not change the `mail.read` contract below.

`mail.read` is a host-neutral capability contract, not a Gmail, Outlook, OAuth, MCP, model, or API integration. It reads only the user-approved mailbox reference, folders/labels, time scope, filters, and inbound direction. It never sends, replies, marks read, moves, archives, deletes, or modifies mail. Without it, request an EML/PDF/mail export. Continuous rules only run when the host provides a compliant read-only scheduler/event mechanism; otherwise they are filters applied on the next user-run query.
