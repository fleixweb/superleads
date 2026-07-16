# Platform Adapters

Map platform-specific tools to Superleads capabilities before planning or execution. If a platform cannot provide a capability, record it in Run Context and lower the deliverable tier instead of inventing evidence.

| Superleads capability | Codex examples | Claude Code examples | Hermes examples | WorkBuddy examples | Degrade when missing |
|---|---|---|---|---|---|
| `search.web` | native `web_search` or another host-exposed search tool | WebSearch | Local/web search | built-in search | Use user-provided materials or write plan only. |
| `source.open` | host operation that actually opens source text | WebFetch/browser | Local Browser | browser/source tool | Do not create Claims from search snippets. |
| `browser.render` | host-exposed rendered-page operation | browser | Local Browser | browser tool | Use text fetch or document extraction; label dynamic-page gaps. |
| `document.extract` | local Python/PDF/CSV tools | file tools | file operations | document tools | Ask for pasted text or export initial list only. |
| `image.inspect` | local OCR/image tools | image/file tools | local vision/file operations | image/OCR workflow | Ask for a clearer image, readable brand text, or a public link; do not infer ownership. |
| `mail.read` | host-authorized read-only mail adapter | host mail reader | host mail reader | host mail workflow | Ask for EML/PDF/mail export; never emulate mailbox access. |
| `source.capture` | files + hash scripts | file snapshots | file snapshots | workflow artifact | Keep excerpt and locator; mark no snapshot hash. |
| `url.canonicalize` | Python/url helpers | URL parsing helpers | URL helpers | URL normalization step | Keep original URL and avoid identity claims from URL normalization. |
| `entity.dedupe` | local normalization script | entity comparison task | local comparison | dedupe workflow | Keep entities provisional; route to identity review. |
| `translate.text` | model/local translation | model translation | translation tool | translation workflow | Preserve original text and avoid translated-only evidence. |
| `company.enrich` | company/enrichment MCP | enrichment tools | enrichment tools | enrichment workflow | Use only as Candidate/contextual clue. |
| `email.verify` | email verify tool | email tool | email tool | email workflow | Do not use as source or ownership proof. |
| `domain.check` | DNS/domain tools | domain tools | domain tools | domain workflow | Treat as technical observation, not company ownership. |
| `social.visible.read` | rendered visible pages | browser visible read | browser visible read | browser visible read | Do not infer purchasing authority from visible role text. |
| `registry.lookup` | registry MCP/browser | registry fetch | registry lookup | registry workflow | Entity claims need other source or manual check. |
| `trademark.lookup` | trademark MCP/browser | trademark fetch | trademark lookup | trademark workflow | Brand/trademark claims need manual or source note. |
| `maps.lookup` | maps MCP/browser | map/browser | map lookup | map workflow | Map phone/address can be contact clue with source note. |
| `memory.recall` | local memory/MemOS | project memory | memory | workflow memory | Use only to prioritize plans; never Claim/Assessment evidence. |

## Codex CLI Native Web Search

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

The report records one actual, read-only public `GET` success with original
and final public HTTP(S) URLs, a 2xx result, source identifier, verbatim
excerpt, and locator. It may explicitly allow only `curl`, `wget`, or
`python_requests`; every shell-backed Observation must use a tool in that
Run's verified allowlist. Local/file URLs, private or loopback IP URLs,
credentials, cookies, Authorization data, tokens, passwords, POST requests,
login-required pages, and restricted endpoints are outside this provider.

A Run may contain both this report and the native Web Search report. Their
capability mappings are aggregated only when the mappings agree; two verified
providers may not simultaneously own the same available capability. Native
search plus shell source opening is valid because native search records
`source.open=unknown` while shell HTTP owns `source.open=available`.

- A visible native `web_search` with a verified `search` operation maps only
  to `search.web=available`. Its output is a search log or initial candidate
  clue, so the maximum capability-only delivery is an initial lead list.
- `source.open=available` requires a separately verified `open_source`
  operation with the original HTTP(S) URL, a page title or equivalent source
  identifier, a non-empty verbatim source excerpt, and its locator. A search
  summary, link, citation, tool name, CLI flag, model name, or provider name
  is not this verification.
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
