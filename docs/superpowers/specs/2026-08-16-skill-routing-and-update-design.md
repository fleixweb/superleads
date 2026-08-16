# Superleads Skill Routing And Update Design

## Goal

Make the three public Superleads business routes predictable while keeping
internal research stages callable only with valid upstream context. Version,
help, status, feedback, and update requests remain fast metadata operations;
only an explicit update request may contact GitHub.

## Confirmed Baseline

- The active plugin manifest now registers no Hook, and both packaged Hook
  configuration files are empty. A normal startup, resume, metadata request,
  and ordinary research request do not perform a remote update check.
- The runtime package still contains legacy Bash and PowerShell startup scripts
  that fetch a `master` manifest. They are unregistered but must not remain in
  the runtime package.
- The deterministic intake route already protects help and basic version
  questions, but lacks dedicated handling for single-object contact checks,
  export help and export prerequisites, current-run status, and current-run
  feedback corrections.
- The plugin registers all thirteen Skills. The host configuration exposes no
  documented visibility or group property, so internal-stage visibility cannot
  be reliably hidden through manifest metadata.

## Public Skill Surface

The only public business entry Skills are:

1. `using-superleads`: **批量发现公开客户信息**. It accepts product or
   keyword, target market, and customer type; it returns a sourced candidate
   pool with unknowns and source restrictions, never a customer recommendation.
2. `researching-customer-background`: **背调指定公司、品牌、域名或地址**. It
   stays bound to the user-specified object and its public contact association.
3. `analyzing-product-outbound-market`: **分析产品出口到目标市场的客观信息**.
   It covers only requested public modules and does not decide market entry.

The plugin-level default prompt lists the same three names in the same order.
`using-superleads` no longer advertises single-object contact or market work,
so its description cannot compete with the other two public entries.

The other ten Skills remain package capabilities because the three routes need
them internally. Since the host cannot reliably hide or group them, each
`agents/openai.yaml` labels the Skill as an internal stage, gives an exact
parent-route trigger, and says not to start it from a bare user prompt. Their
short descriptions and default prompts must not use the generic “Use $skill
for a Superleads lead-research task” wording.

## Invocation Contract

A new pure invocation-contract helper validates a host-supplied context before
an internal stage is selected. It does no file, network, cache, graph, or
research operation. The context can carry only the current request state:

- parent route and task mode;
- `run_id` where the stage works inside a research run;
- Brief presence;
- plan/source/observation/evidence/validation state;
- allowed output modes and requested output;
- explicit feedback-save consent, feedback target, and feedback class.

Each stage declares the smallest valid prerequisites. Scoping accepts a public
entry and creates the Brief; planning requires a Brief; execution requires a
Run, Brief, and Plan; contacts require an in-scope Run, Brief, and opened
source; assessment, identity resolution, review, validation, and export
require their relevant upstream evidence. Export additionally requires a
current legal graph and an allowed output mode. A missing prerequisite returns
a short user-facing stop message and no invented report, source, contact,
Claim, or export.

Feedback has two distinct paths. A correction such as “this candidate does not
meet the request” changes only the current Run when supplied with a current
Run context. Long-term feedback is unavailable unless the user explicitly
asks to save it, identifies the run and feedback class, and confirms saving.
No correction becomes an ICP rule or durable profile automatically.

## Deterministic Intake Priority

The router evaluates one route in this order and emits one public entry or a
short clarification, never a set of competing Skill names:

1. Metadata: help, installed version, current status, capabilities, feedback
   instructions, and explicit update checks.
2. Material triage: organization of only the user-provided document, image,
   spreadsheet, or text.
3. One specified object: company, brand, domain, address, phone, email, or
   public social URL, including a public-contact-only request.
4. Batch discovery: product or keywords plus a customer-discovery scope.
5. Product outbound market analysis: a product and destination-market question
   about requested market, access, tax, price, logistics, or related facts.
6. Contact supplementation: only after the router distinguishes a single
   object, a batch route, or a bound existing table.
7. Existing-table enrichment: only for a supplied table and requested fields.
8. Export: help remains metadata; execution is blocked until a current valid
   result context exists.
9. Explicit formal review or deep verification: preserves the selected
   business route while selecting formal research mode.

Metadata always wins over business keywords. Material triage never searches,
and its wording avoids internal objects such as Run and Brief. An export word
does not make an Excel request table enrichment. A status request returns the
current host-supplied stage summary or a clear no-current-task response, never
creates research state.

## Composite Parent Tasks And Isolated Subroutes

One user request may contain several explicit business objectives. The router
creates one composite parent task and a separate subroute for each objective;
it never asks the user to split a request merely to match internal structure.
The parent extracts only shared, explicit input: the specified object,
product/model/category, destination, customer type, supplied material, output
request, and declared dependencies. It may create a customer-background,
market-facts, batch-discovery, table-enrichment, public-contact, and deferred
export subroute in the same parent.

Subroutes run independently when their input is complete. A missing product or
destination leaves only market analysis in `waiting_for_required_input`; it
does not block an independent company background check. Independent query
groups, pages, candidate contacts, supplied files, and lightweight structural
checks may be scheduled in parallel only when the host actually supports it.
Identity merging for one subject, source conflict resolution, Claim/evidence
promotion, declared data dependencies, final validation, export, and parent
delivery aggregation are serial.

Every subroute owns its recorded observations, purpose, scope, status, and
unexecuted/restricted items. An already opened URL can be referenced by more
than one subroute, but each reference records that subroute's use and evidence
boundary. A company source cannot prove market access; a regulatory source
cannot prove a company is a buyer, has intent, or is worth pursuing. Search
summaries remain clues. A restriction, identity uncertainty, or failure in one
subroute does not lower the status of another completed subroute.

The user-facing parent status names only the requested work and its recorded
counts: `进行中`, `等待必要信息`, `已完成`, `部分完成`, `来源受限`, or `无法执行`.
It does not reveal skill names, Run IDs, graph names, Claims, or audits. The
terminal parent report has separate sections for scope/executed subroutes,
company background, market facts, each subroute's sources and gaps, and the
one permitted update notice. It contains only objective facts and statuses,
never customer-value, purchasing-intent, follow-up, or market-entry advice.

## Status Projection

`superleads_execution_state` remains the source of truth for phase, coverage,
opened-source, restriction, unexecuted, and checkpoint counts. A pure
user-facing formatter converts it to the permitted status vocabulary and
removes IDs, hashes, local paths, and rule names.

When the host supplies an actual stage boundary, the router may return one
compact status update. The current host has no proved background or streaming
facility, so it must say only that work is being handled in batches. Terminal
Markdown/workbook export results carry a stage summary derived from the
recorded state; no state is invented for graphs that did not record it.

## Explicit Update Contract

Automatic update checks remain disabled. There is no SessionStart, resume,
startup, normal-research, help, version, or status network check. The runtime
package excludes the legacy `hooks/` directory and distribution validation
rejects any Hook configuration or script that declares SessionStart/resume or
an automatic remote version fetch.

Only the following explicit requests reach the update handler: Chinese
requests to check updates/latest GitHub version, `@superleads update`, and
their English equivalents. The handler receives an active plugin root, a
host-owned session cache, and an injected remote fetcher. It reads the local
version only from `<active root>/.codex-plugin/plugin.json`; it never scans old
caches, backups, temporary directories, or other plugins.

The handler returns a structured result with local version, remote version
when available, source kind and URL, checked time, outcome, optional release
URL, and a non-sensitive cache marker. Its preferred remote source is GitHub
Releases latest stable. A fixed tagged manifest is `tag_manifest`; a branch
manifest is always `repository_version`, never “latest stable”. Failures are
visible as `check_failed` or `not_checked`, not “up to date”. A host-owned
fresh cache is reused without another fetch; callers can explicitly force a
refresh. Without a host session cache or real background task capability,
there is no implicit cache, global state, or background request.

A cached newer stable version may produce one short update notice only when a
terminal user delivery is composed. The notice is outside every research
graph, Source, SearchLog, Claim, Assessment, audit result, and business
conclusion. The same remote version is marked notified in the host session
cache and is not repeated unless the user explicitly checks again.

## Evidence And Delivery Invariants

None of these changes alter the source model or weak-evidence rules. Search
summaries remain clues; public facts and public contacts require a successfully
opened current-run source. Identity conflicts, source restrictions, unexecuted
modules, historical references, and contact ownership uncertainty stay
visible. No route may guess an email, promote a title to purchasing authority,
combine subjects, bypass access controls, rank customer value, infer purchase
intent, recommend follow-up, or decide market entry.

## Test Strategy

Tests are written before each implementation change and first observed to fail.
They cover all three public Skill configurations, internal-stage labels and
precondition stops, one-route-only intent resolution, active-root-only version
reads, explicit update trigger variants, structured update outcomes, host cache
reuse, failures, branch-manifest labeling, one terminal notice, and no startup
or ordinary-request remote call.

They also cover single-company contact routing, export help versus validated
export execution, current-status and current-Run feedback behavior, composite
parent tasks with isolated subroutes, independently schedulable work and
serial merge/export boundaries, partial composite delivery, status projection
without internal leakage, material-triage wording, source/weak evidence
regressions, scoped market modules, checkpoint restoration, package contents,
schema compatibility, unified Markdown delivery, and all existing evaluation
suites. Remote tests use injected deterministic responses and never depend on
live GitHub availability.

## Non-Goals

This change does not add a paid API, a platform account flow, a persistent
customer profile, external telemetry, a global cache, a new English Skill,
version bump, cache installation, Git commit, or Git push. It does not claim
that the host supports hidden Skills, streaming progress, parallel execution,
or background updates when no verified capability exists.
