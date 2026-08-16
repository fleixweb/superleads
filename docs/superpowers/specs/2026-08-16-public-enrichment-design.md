# Public Enrichment Design

## Goal

Extend bulk customer development with public social-page, map-listing, and
third-party trade-aggregator coverage without adding a platform API, account,
credential, proxy, or access-control bypass.

## Design

The existing public-source flow remains the only executor. `search.web` may
discover public URLs and search-summary clues; only a successful, current-Run
`source.open` or `browser.render` may create a social, map, or
trade-aggregator Source and Observation. A declared `social.visible.read` or
`maps.lookup` capability is never assumed. When ordinary source opening reads
such a page, its Source medium is `social`, `map`, or `trade_aggregator` and
its Observation records the actual capability and concrete tool.

Default-discovery Candidates gain three required signal states:

- `social_company` for company or brand public pages;
- `social_person` for public professional role clues; and
- `map_listing` for public map business listings.

The existing `trade_record` signal remains the per-candidate coverage state so
older graphs stay compatible. Optional `public_trade_summaries` preserve only
visible, third-party aggregate fields. They are not Claim, ClaimEvidence,
Assessment, official customs data, or an automatic entity merge.

Each new signal has both the existing evidence status and a collection status.
The latter is projected as `本轮未检索`, `已检索未见`, `搜索摘要可见`, `公开页面已打开`,
`详情受限`, `疑似，主体待确认`, or `用户提供资料`. Opened rows must bind a
same-candidate Source and Observation. Search-summary rows cannot create a
contact or a fact.

The initial workbook and ChatGPT Markdown report add independent business
sections for social/professional clues, maps/operating addresses, and third-
party trade summaries. Restricted or skipped coverage produces an explicit
pending row and a manual-check message; it is never omitted or restated as
absence. Trade rows always carry the fixed non-official disclaimer.

## Boundaries

The plan and execution Skills require company/domain/city anchored queries,
deduplicate the same URL within a Run, set category budgets, and stop after a
login wall, CAPTCHA, 403, Cloudflare challenge, paywall, dynamic unreadable
shell, or other restricted result. They do not purchase, call, or request an
API; ask for a platform account, Cookie, token, password, or API key; use
proxy rotation or browser evasion; read private profiles, lists, messages, or
hidden contacts; or infer purchasing authority from a public role.

User-supplied links, screenshots, PDFs, spreadsheets, and de-identified third-
party exports remain explicitly labeled as user-provided material. Screenshots
and OCR stay clues until the company association can be independently checked.

## Verification

Tests derive from the existing default-discovery pass graph and cover opened
social/map rows, search-summary-only and restricted trade rows, same-name map
conflicts, non-purchasing role wording, no guessed contact values, explicit
not-searched output, user-provided material, and the fixed restriction/manual
check disclosure. Existing graph, workbook, Markdown, and full eval suites
remain the regression gates.
