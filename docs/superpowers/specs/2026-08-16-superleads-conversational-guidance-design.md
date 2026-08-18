# Superleads Conversational Guidance Design

## Goal

Make Superleads easier to start in a ChatGPT conversation without changing its
research evidence model, delivery gates, or business-decision boundaries. The
first response should teach a non-technical foreign-trade user what to type
next. Every completed or stopped user delivery should end with the same
support-and-security information.

## Current Behaviour

- `@superleads` currently routes to `bulk_customer_development` with
  `product_or_scope` missing.
- Chinese and English help questions route to `unknown` and ask the user to
  restate a task.
- The main Skill starts formal-run setup before it has a help-specific branch.
- Markdown delivery renderers and the visible-output contract have no shared
  support-and-security footer.

## Design

### One Shared Guidance Reference

Create one shared reference for the business-language rules. It is the sole
maintenance location for:

- the static-help trigger and no-side-effect requirement;
- the compact conversation guide structure;
- dynamic user-language selection rules;
- the evidence and decision boundaries; and
- the support-and-security footer semantics and placement rules.

Skills and delivery code reference this source instead of carrying copied
Chinese or English footer text. English and other languages are generated from
the same semantic instructions, not from a second Skill, locale, or template.

### Static First-Use Help

The intake classifier receives a dedicated `help` route before all research
routes when the meaningful user text is only an invocation, or is a Chinese or
English request for capability, help, or how to use Superleads. It returns the
guide payload directly and does not create a Run Context or invoke research,
preflight, source opening, export, validation, version checks, cache scans, or
network work.

The guide is compact ChatGPT Markdown, not a card, table, picker, button set,
web page, or marketing layout. In the user's language it contains, in order:

1. one sentence identifying Superleads as help for batch customer development,
   single-customer background research, and target-market analysis;
2. one sentence explaining `@` -> select Superleads -> describe the need;
3. three short titled entries, each with only a minimum input format and one
   copyable example;
4. `更多用法` / its translated equivalent with Excel or CSV export, uploaded
   customer-table enrichment, and public contact association checks;
5. the evidence and decision boundary in plain business language; and
6. the shared support-and-security footer.

The Chinese wording follows the user-approved conversation example. English
uses the same three business entries, input fields, examples, boundaries, and
footer meaning, without Chinese headings or internal implementation terms.

### Direct Task Routing

Help detection is deliberately narrow and runs first. A concrete request keeps
the existing route:

- product keyword + market + customer type: `bulk_customer_development`;
- company name, domain, email, phone, address, brand, or user material:
  `customer_background_research` when the request is about that object;
- product + target market + market-information request:
  `product_outbound_market_analysis`;
- uploaded/identified customer table with a completion request:
  `existing_table_enrichment`.

No complete guide is sent before such a request. Missing fields result only in
the existing minimal clarification that can change research direction.

### Shared Final Footer

Provide one delivery helper that appends the localized footer only to terminal
user-facing output. It detects an existing exact footer marker and preserves
it, so repeated rendering cannot duplicate the text. It is used by formal
Markdown delivery for all three routes and by final static failure/limited
delivery language specified in the Skills. Progress updates and standalone
clarifying questions do not call it.

The Chinese canonical semantic is:

```text
Superleads 支持

在使用 Superleads 过程中，如遇问题或有改进建议，欢迎通过 [GitHub Issues](https://github.com/fleixweb/superleads/issues) 反馈，或在小红书搜索 Fleixweb 联系 Fleix。

使用 AI 开发客户时，请勿提交密码、API Key 或未经脱敏的客户敏感资料。
```

Localized variants retain the GitHub Issues URL, the instruction to search
Xiaohongshu for `Fleixweb`, and the password/API-key/unsanitized-sensitive-data
warning. Appending a footer is pure text work; it does not fetch the link or
perform any other tool action.

### Boundaries

The guide and footer state that Superleads organizes public sources,
verifiable facts, source information, and open questions. They do not:

- convert search snippets into facts;
- guess missing information;
- rank or choose customers for the user;
- decide whether a market should be entered;
- turn a candidate pool into a confirmed development list; or
- present weak evidence as a conclusion.

User-visible copy must not expose internal Skill names, route names, graph
objects, validator/audit language, rule IDs, local paths, or implementation
capability names.

## Implementation Boundaries

- Keep one business-content source and one footer helper; do not add English
  Skill files, English help documents, locale trees, or version changes.
- Do not alter research schemas, evidence validation, weak-evidence handling,
  or route decisions beyond the new narrow `help` route.
- Do not modify installation caches, backups, temporary directories, or the
  preserved `tmp/stage5_chillys/` directory.
- Do not commit or push this work.

## Test Strategy

Add deterministic tests before implementation for:

- Chinese bare invocation and help-question guide output;
- English help-question guide output;
- direct routing for bulk development, single-object research, market analysis,
  and existing-table enrichment;
- all three guide entries, input formats, examples, more-use cases, boundaries,
  localized footer, and prohibited internal terms;
- localized footer on all three formal Markdown routes, and idempotent footer
  appending;
- no footer on progress or isolated clarification text; and
- static guide/footer behaviour that does not call research, network, preflight,
  export, validation, version, or cache operations.

Run the focused tests, the existing user-visible and route evals, the complete
unit suite, and the complete eval suite after the change. Baseline before this
design: unit tests 57/57, visible-output evals 15/15, and full evals 731/731
all passed.
