# Tool Capability Policy

Capability discovery starts from the current host's actual tool inventory, not from a preferred adapter name in this repository. A named adapter is eligible only when the host exposes that operation. Separate capability-missing failures from call failures: an unexposed tool, `missing-tool`, or the tool itself returning 404 is a missing capability and must not be retried; a timeout, rate limit, 5xx, adapter-internal error, or other single-call exception means the capability exists but this attempt failed. In particular, a Codex `web__run` failure must not erase a verified ChatGPT Desktop, Claude Code, Hermes, or WorkBuddy capability.

## Script portability

无脚本交付的唯一契约是
`../references/no-script-delivery-contract.md`；本政策只定义能力边界和禁止事项，不复制第二套无脚本交付清单。

任何 `scripts/*.py` 在 `SKILL.md` 中出现时，都必须同时给出无脚本的等价路径。脚本是加速器，不是交付前提；Python 或 shell 不可用不等于宿主的搜索、来源打开或文档能力不可用。无脚本路径必须内联执行相同的路由、证据和用户可见边界；整个确定性脚本校验链未运行时标注“本环境未运行确定性校验”。如果核心业务规则校验已经运行并通过，只是补充结构检查未运行，则改用“本次已完成核心业务规则校验；补充结构检查未运行。”，不得把它写成整个确定性校验未执行。这项兼容约定不允许把搜索摘要升级为事实，也不放宽主体、联系人、来源或访问限制。缺少校验依赖时不得为了跑通脚本在运行时安装依赖、创建临时依赖目录或设置 `PYTHONPATH`；不得搜索、借用或调用其他应用程序的 Python 环境、虚拟环境或解释器，包括其他 Agent、IDE 或桌面应用自带的 venv；必须走无脚本路径，并按实际执行范围使用上述对应标注。

## Runtime-detail visibility

预检脚本名与预检机制、适配器判定或自我纠偏过程、Python 解释器与依赖安装、工作区目录和 `PYTHONPATH` 均为内部执行细节，任何用户可见文本都不得出现，包括阶段性进度旁白。用户可见说明只交代当前可用的交付层级和所需能力；无脚本完成时使用“本环境未运行确定性校验”，核心业务规则已运行而仅补充结构检查未运行时使用“本次已完成核心业务规则校验；补充结构检查未运行。”，均不得叙述内部恢复过程。

## Adapter-local failure recovery

当一次实际检索或来源打开失败时，先区分能力缺失和调用失败。工具未暴露、返回 `missing-tool` 或工具本身返回 404 时，停止重试该失败适配器，按不可用处理；超时、限流、5xx、适配器内部错误或单次调用异常时，能力仍视为存在，应在同一适配器上继续尝试，但同一 Run 对同一能力最多 3 次。每次重试必须更换查询词、语言、`site:` 限定或本地目录/行业协会名录方向，不得原样重发。若有第二个已经暴露的原生检索或来源打开操作，优先使用它；单 provider 宿主也必须先换查询方向，而不是一击出局。三次调用失败后才允许把该能力标为不可用。成功检索只记录为检索能力；只有实际打开来源并保留 URL、可见原文和位置后，才记录来源打开能力。

若能力确实缺失，快速发现只能降级为用户资料整理或有界查询计划；正式公开来源研究按正式门禁停止，并建议用户切换到具备所需能力的环境。若能力存在但 3 次更换方向后仍失败，也不得伪造候选、来源、正式图谱或事实；应说明已尝试的次数，建议用户提供名录/注册库链接、上传已有名单或稍后重试，不要求切换环境。用户可见说明只交代当前可用的交付层级和下一步，不暴露适配器、provider 或错误细节。

恢复前先查看当前会话实际暴露的操作；若存在不同的已暴露原生检索或来源打开操作，优先直接使用它。
不得以 shell/curl 代替公开检索。

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

Formal public-source foreign-trade research requires both `search.web` and at
least one source-opening capability: `source.open`, `browser.render`, or
`document.extract`. If either prerequisite is genuinely missing, stop formal
customer development, customer background research, and product-market
analysis, and tell the user to switch to an Agent/environment with Web Search
and source-opening capability. If a capability exists but its calls have
failed, use the bounded changed-query recovery above before declaring it
missing. Do not present a research plan, discovery candidate pool, or market
report as a substitute delivery.

An internal source plan may still be produced for later execution, but is not a
user-facing formal deliverable. Reviewing only materials the user already
provided is allowed as a limited materials-review task; label it as such and do
not call it public-source market analysis, customer development, or a formal
research report.

## Codex CLI Native Web Search

When a current Codex session exposes `web__run`, use
`codex_cli_web_run` rather than treating it as the older `web_search` tool.
Its verified `search_query` operation maps to `search.web`; its verified
`open` operation maps to `source.open` only with the actual public URL, source
identifier, non-empty verbatim excerpt, and locator. Each related SearchLog
and Observation records `concrete_tool: web__run` in that same Run.

`click`, `find`, `screenshot`, and `image_query` do not independently map to
formal canonical capabilities. They cannot upgrade a search summary into a
Source or fact, and no adapter report is written without actual current-Run
operation results.

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

For a discovered public HTML/text URL, `scripts/capture_public_http_source.py`
is the local `curl` executor for this provider. It only sends a credential-free
GET, records a successful 2xx final URL, title, visible verbatim excerpt, and
locator, and returns no record on failure. It validates the initial URL, each
DNS resolution, and every redirect target as public. It must be paired with a
separately successful `web__run.search_query` or `web_search` adapter report
to meet formal-research preflight; it never creates or promotes `search.web`.

The graph gate accepts only canonical host IDs when a platform is recorded:
lowercase ASCII letters, digits, and underscores. This preserves generic hosts
such as `hermes`, `claude`, `chatgpt_desktop`, and `workbuddy`; it rejects tool
names, whitespace, uppercase, and hyphen variants. The graph gate does not
perform DNS lookup. It
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
  returns summaries, record the gap and stop formal research. A
  `research_plan_only` artifact is internal preparation for a later
  source-capable session, never a formal user delivery. A discovery candidate
  pool likewise requires the formal source-capability prerequisite.

This policy does not bind Superleads to a model, provider, platform API, or
external tool server. It does not change the `mail.read` contract below.

`mail.read` is a host-neutral capability contract, not a Gmail, Outlook, OAuth, MCP, model, or API integration. It reads only the user-approved mailbox reference, folders/labels, time scope, filters, and inbound direction. It never sends, replies, marks read, moves, archives, deletes, or modifies mail. Without it, request an EML/PDF/mail export. Continuous rules only run when the host provides a compliant read-only scheduler/event mechanism; otherwise they are filters applied on the next user-run query.
