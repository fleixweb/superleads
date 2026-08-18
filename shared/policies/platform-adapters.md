# Platform Adapters

Map platform-specific tools to Superleads capabilities before planning or execution. If a platform cannot provide a capability, record it in Run Context and lower the deliverable tier instead of inventing evidence.

Before probing a named tool, inspect the tools the current host actually exposes. ChatGPT Desktop, Codex CLI, Claude Code, Hermes, and WorkBuddy may use different concrete names for the same `search.web` or `source.open` capability. Never call `web__run`, `web_search`, WebSearch, or another adapter merely because it appears in this document; use it only when that exact operation is present in the current host. A failure from one adapter applies only to that adapter. Do not retry the same failed adapter, but do check another already-exposed native provider before concluding that the host has no Web capability.

宿主能力按当前会话的实际操作结果记录。不按安装方式推断，不沿用历史会话结论，不因某个适配器失败就判定整类能力不可用；同一平台在不同会话可能暴露不同工具。

## Runtime Host Identity

- `Run.platform` records the canonical ID of the current runtime host, not its installation origin. Installation through a Codex environment does not make the current host `codex_cli`.
- Determine the host from tools actually exposed in the current session: a host exposing `web__run` is `codex_cli`; ChatGPT Desktop or the Codex app using built-in browsing and search records `chatgpt_desktop`.
- `chatgpt_desktop` uses the generic capability self-reporting path and does not require a dedicated adapter report. Do not create a dedicated ChatGPT adapter modeled on `codex_cli_web_run`, `codex_cli_native_web_search`, or `codex_cli_shell_http_source_open`; doing so would incorrectly copy the Codex-only failure path.

For ChatGPT Desktop, prefer the app's actually exposed built-in browsing/search and source-opening operations. A Codex-only `web__run` 404 is not evidence that ChatGPT Desktop has no search capability. Record the successful host capability and concrete operation that were actually used; do not record the failed Codex probe in a formal Run graph.

| Superleads capability | Codex examples | ChatGPT Desktop examples | Claude Code examples | Hermes examples | WorkBuddy examples | Degrade when missing |
|---|---|---|---|---|---|---|
| `search.web` | native `web__run.search_query`, `web_search`, or another host-exposed search tool | actually exposed built-in browsing/search | WebSearch | Local/web search | built-in search | Use user-provided materials or write plan only. |
| `source.open` | native `web__run.open` or another host operation that actually opens source text | built-in source-opening/read operation that actually opens source text | WebFetch/browser | Local Browser | browser/source tool | Do not create Claims from search snippets. |
| `browser.render` | host-exposed rendered-page operation | built-in rendered-page operation, if exposed | browser | Local Browser | browser tool | Use text fetch or document extraction; label dynamic-page gaps. |
| `document.extract` | local Python/PDF/CSV tools | built-in file/document reading, if exposed | file tools | file operations | document tools | Ask for pasted text or export initial list only. |
| `image.inspect` | local OCR/image tools | built-in image inspection, if exposed | image/file tools | local vision/file operations | image/OCR workflow | Ask for a clearer image, readable brand text, or a public link; do not infer ownership. |
| `mail.read` | host-authorized read-only mail adapter | host-provided read-only mail operation, if exposed | host mail reader | host mail reader | host mail workflow | Ask for EML/PDF/mail export; never emulate mailbox access. |
| `source.capture` | files + hash scripts | host-provided file/snapshot operation, if exposed | file snapshots | file snapshots | workflow artifact | Keep excerpt and locator; mark no snapshot hash. |
| `url.canonicalize` | Python/url helpers | host-provided URL normalization, if exposed | URL parsing helpers | URL helpers | URL normalization step | Keep original URL and avoid identity claims from URL normalization. |
| `entity.dedupe` | local normalization script | host-provided entity comparison, if exposed | entity comparison task | local comparison | dedupe workflow | Keep entities provisional; route to identity review. |
| `translate.text` | model/local translation | host-provided translation, if exposed | model translation | translation tool | translation workflow | Preserve original text and avoid translated-only evidence. |
| `company.enrich` | company/enrichment MCP | host-provided enrichment, if exposed | enrichment tools | enrichment tools | enrichment workflow | Use only as Candidate/contextual clue. |
| `email.verify` | email verify tool | host-provided email verification, if exposed | email tool | email tool | email workflow | Do not use as source or ownership proof. |
| `domain.check` | DNS/domain tools | host-provided domain check, if exposed | domain tools | domain tools | domain workflow | Treat as technical observation, not company ownership. |
| `social.visible.read` | rendered visible pages | host-provided visible-page read, if exposed | browser visible read | browser visible read | browser visible read | Do not infer purchasing authority from visible role text. |
| `registry.lookup` | registry MCP/browser | host-provided registry lookup, if exposed | registry fetch | registry lookup | registry workflow | Entity claims need other source or manual check. |
| `trademark.lookup` | trademark MCP/browser | host-provided trademark lookup, if exposed | trademark fetch | trademark lookup | trademark workflow | Brand/trademark claims need manual or source note. |
| `maps.lookup` | maps MCP/browser | host-provided map lookup, if exposed | map/browser | map lookup | map workflow | Map phone/address can be contact clue with source note. |
| `memory.recall` | local memory/MemOS | host-provided session memory, if exposed | project memory | memory | workflow memory | Use only to prioritize plans; never Claim/Assessment evidence. |

快速候选池不运行正式研究 preflight。若同一失败适配器返回 404 或超时，停止重试该适配器，并按 `tool-capability-policy.md` 的恢复顺序查看当前会话实际暴露的操作（即宿主实际暴露的操作）：直接使用另一条已暴露的原生检索或来源打开操作完成下一次实际工作；仅在不存在该操作时降级为用户资料整理或有界查询计划。不得伪造候选、来源或正式图谱，也不得以 shell/curl 代替公开检索。

## Codex CLI Native Web Search

### Preferred Codex `web__run` pathway

When the current Codex session exposes `web__run`, Superleads prefers the
controlled `codex_cli_web_run` adapter. It uses no third-party MCP:

- `web__run.search_query` with a verified current-Run success maps to
  `search.web` and can create SearchLog/candidate-locator records only.
- `web__run.open` maps to `source.open` only after the same Run records the
  public original URL, source title or identifier, non-empty verbatim excerpt,
  and excerpt locator from the opened page.
- SearchLogs and Source Observations record `concrete_tool: web__run`; the
  graph validator rejects any other concrete tool under this provider.

`click`, `find`, `screenshot`, and `image_query` are useful follow-up
operations but do not independently grant a canonical formal capability. They
may help navigate or inspect a page only after `search_query`/`open` evidence
has been recorded through their respective gates. A search summary, citation,
or result link is never a Source, Observation, Claim, or contact fact.

The adapter report is created from actual current-Run tool results. Local
scripts validate it; they never infer it from a visible tool list or fabricate
an operation result.

When Codex CLI starts a session with `codex --search`, the current session may
expose the native `web_search` tool. Superleads reads only a capability report
written by the Agent from its current-session tool visibility and actual
operation results. It does not install, configure, or bind any third-party
tool integration.

Use the controlled `codex_cli_native_web_search` adapter report in the Run
only when all of these are recorded: platform `codex_cli`, adapter identifier
and version, detection time/method, `web_search` availability, separate
`search` and `open_source` operation results, and canonical capability
statuses. The local preflight script parses this report; it does not attempt
to discover the model's tools.

The adapter owns only `search.web` and `source.open`. It overrides those two
canonical statuses only after the report is fully valid, including its exact
supported adapter version and its declared mapping. It neither maps nor
overwrites `browser.render`, `document.extract`, `image.inspect`, `mail.read`,
or any other host-reported canonical capability. Those capabilities continue
through their independent generic contracts. An invalid adapter grants neither
of its owned capabilities, but does not erase independently valid document or
rendering capability.

When a Run includes this adapter report, every capability used by one of its
Observations, including an independent capability, must be explicitly present
in that Run's canonical capability report with status `available`. An omitted,
`unknown`, or `missing` capability is not verified for that Observation and
cannot support a formal source. This records an actual host capability; it does
not make the native adapter own independent capabilities.

## Codex CLI Shell HTTP Source Open

Codex CLI may separately use a host-authorized shell HTTP reader to open a
public source. In that case the Run host remains `codex_cli`; `curl`, `wget`,
and `python_requests` are only the Observation's concrete source-reading
tool, never a platform. The controlled `codex_cli_shell_http_source_open`
adapter owns `source.open` only. It does not grant `search.web`, rendering,
document extraction, or any other capability.

The report records one operation per actual, read-only public `GET` success,
with original and final public HTTP(S) URLs, a 2xx result, source and
Observation identifiers, verbatim excerpt, and locator. It may explicitly
allow only `curl`, `wget`, or `python_requests`; every shell-backed Observation
must use a tool in that Run's verified allowlist and match exactly one recorded
operation. Local/file URLs, private or loopback IP URLs,
credentials, cookies, Authorization data, tokens, passwords, POST requests,
login-required pages, and restricted endpoints are outside this provider.

`scripts/capture_public_http_source.py` is the supported Codex-local executor
for this provider. It accepts one or more already discovered public URLs, uses
a credential-free `curl GET` for each, pins each request to a freshly resolved
global IP, and validates each redirect target before opening it. Its output is limited to
the source-open adapter record and Source / Observation seeds. It never
searches, creates a SearchLog, or emits business facts; failed capture emits
no Source or Observation. It can complement a successful `web__run.search_query`,
but cannot substitute for one.

A Run may contain both this report and the native Web Search report. Their
capability mappings are aggregated only when the mappings agree; two verified
providers may not simultaneously own the same available capability. Native
search plus shell source opening is valid because native search records
`source.open=unknown` while shell HTTP owns `source.open=available`.

- A visible native `web_search` with a verified `search` operation maps only
  to `search.web=available`. Its output is a search log or initial candidate
  clue, so the maximum capability-only delivery is an initial lead list.
- `source.open=available` requires one or more separately verified
  `open_source` operations. Every opened Observation must match exactly one
  operation by Source URL, title, non-empty verbatim excerpt, and locator. A
  search summary, link, citation, tool name, CLI flag, model name, or provider
  name is not this verification.
- A blocked, login-required, forbidden, inaccessible, or otherwise restricted
  Observation must instead match its own `failed` open operation with the same
  Source URL, title, excerpt, and locator. A failed operation never makes
  `source.open` available and cannot support a Claim.
- The adapter never maps `browser.render`. A host that exposes it must report
  that capability separately through its canonical contract; the same applies
  to `document.extract` and every other independent capability.
- A custom model provider may expose no native tool, fail its call, or return
  only unavailable content. Record that capability gap and degrade to a
  research plan or initial list.

Even after `source.open` is reported, every Source, Observation, Claim,
contact, Review, Audit, hash, freshness, and delivery rule remains unchanged.
The report records only the host capability boundary; it is not a source and
cannot evidence a business fact or contact.

For multi-Run research graphs, every Observation records the Run in which it
was collected. Its capability is checked only against that Run's report;
historical Run capabilities cannot approve or reject a current Observation.
Single-Run graphs retain the existing implicit Run association for compatibility.

See `../../shared/references/codex-native-web-search-host-acceptance.md` for
the separate manual host acceptance procedure. This adapter policy does not
introduce a default country, industry, company size, customer type, or ICP.

`document.extract` is a capability contract, not a binding to a vendor or one parser. Codex, Claude Code, Hermes, WorkBuddy, or another host may use an appropriate local/document tool on Windows, macOS, Linux, or WSL. For a formal user-provided file source, the host must retain only safe metadata in the graph: SHA-256, display filename, extraction excerpt, and page/sheet locator. A pasted chat fragment is not a document extraction and cannot take this branch.

All recorded Run and adapter-report platforms use the same canonical host-ID
rule: lowercase ASCII letters, digits, and underscores only, with no leading
or trailing whitespace, uppercase variant, or hyphen. This does not enumerate
or restrict non-Codex hosts; it only prevents tool names and ambiguous
spellings from changing the adapter path. A Codex adapter report must exactly
match the canonical `codex_cli` Run platform.

The graph validator performs no DNS request. It rejects literal private,
loopback, link-local, reserved, multicast, unspecified, localhost/local, and
legacy numeric IPv4 forms such as `127.1`, `2130706433`, and `0x7f000001`.
This local string check is not DNS rebinding protection. A real Shell HTTP
executor must independently prevent every connection and redirect target from
resolving to a non-global address.

`mail.read` follows the same host-neutral boundary on Windows, macOS, Linux, and WSL. The deterministic `ingest_mail_read_result.py` adapter accepts only already-read normalized data; it does not log in, call a mailbox provider, retain credentials, or execute a mutating mail operation.
