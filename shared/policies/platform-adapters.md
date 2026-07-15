# Platform Adapters

Map platform-specific tools to Superleads capabilities before planning or execution. If a platform cannot provide a capability, record it in Run Context and lower the deliverable tier instead of inventing evidence.

| Superleads capability | Codex examples | Claude Code examples | Hermes examples | WorkBuddy examples | Degrade when missing |
|---|---|---|---|---|---|
| `search.web` | web/search MCP or browser search | WebSearch | Local/web search | built-in search | Use user-provided materials or write plan only. |
| `source.open` | web open/fetch/browser | WebFetch/browser | Local Browser | browser/source tool | Do not create Claims from search snippets. |
| `browser.render` | Playwright/browser MCP | browser | Local Browser | browser tool | Use text fetch or document extraction; label dynamic-page gaps. |
| `document.extract` | local Python/PDF/CSV tools | file tools | file operations | document tools | Ask for pasted text or export initial list only. |
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
