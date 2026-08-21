# Codex Native Web Search Host Acceptance

Status: manual host acceptance, not an automated model-behavior evaluation.

Run this procedure in a fresh Codex session that exposes a native web tool.
Prefer `web__run` when it is available; retain the older `web_search` section
only for hosts that expose that exact tool.

## Preferred: Codex `web__run`

1. Invoke `$using-superleads` for a public-company or product-market research
   request.
2. Use `web__run.search_query` once and retain the successful current-Run
   operation result. Record `search.web=available` only after that success.
3. Use `web__run.open` on one public result URL. Retain the original HTTP(S)
   URL, title/source identifier, non-empty visible verbatim excerpt, and a
   page/line/section locator from that opened result.
4. Record one `codex_cli_web_run` adapter report with exactly the `web__run`,
   `search_query`, and `open` operations. Record `source.open=available` only
   after step 3; otherwise leave it `unknown`/`missing` and stop formal
   research at the capability gate.
5. Put search outputs only in SearchLog with `concrete_tool: web__run`. Put
   opened source text in normal Source/Observation records, also with
   `concrete_tool: web__run`, then run existing evidence, audit, and export
   gates.

### `web__run.search_query` plus local public `curl GET`

Use this variant only when the current Run's `search_query` succeeds but
`web__run.open` cannot produce the required source text. It uses no MCP:

1. Retain the successful `web__run.search_query` operation and record a
   `codex_cli_web_run` report with `search.web=available` and
   `source.open=unknown`.
2. For one or more public result URLs that must be opened, run:

```bash
python3 scripts/capture_public_http_source.py \
  --url 'https://public.example/source' \
  --run-id '<current-run-id>' \
  --format json
```

3. Merge its `capability_adapter_reports[0]`, `sources`, and `observations`
   into the same Run. The returned Observation is `source.open` with
   `concrete_tool: curl`; use its captured excerpt verbatim in compact notes.
4. Run preflight again against the combined reports, then continue through the
   normal plan, compiler, validator, audit, and export gates.

The helper is not a search tool. It accepts only a public credential-free URL,
uses a GET without cookies or Authorization, pins every request to a verified
global address, and checks all redirects. A non-2xx response, blocked page,
empty visible text, title-less source, unsafe URL, or failed fetch produces no
Source/Observation. Do not hand-write a successful adapter record when it
fails. If `web__run.search_query` fails, formal research remains blocked even
when `curl` can reach a public site.

`click`, `find`, `screenshot`, and `image_query` do not independently grant
`search.web`, `source.open`, `browser.render`, or `document.extract`. Do not
write a report from tool visibility alone, a model summary, a citation, or a
manually invented excerpt.

## Legacy native `web_search`

Run this procedure in a fresh session:

```bash
codex --search -C /home/fleix/superleads
```

1. Invoke `$using-superleads` for a public-company research request.
2. Confirm whether the current session actually exposes native `web_search`.
3. Search one public company and record whether the host returns only a result
   summary/link/citation or can actually open a specific public URL.
4. Mark `search.web` available only after the search operation succeeds.
5. Mark `source.open` available only when the same session returns the
   original HTTP(S) URL, a title or equivalent source identifier, a non-empty
   verbatim source excerpt, and a locator from an opened source page.
6. When only a summary is available, record `source.open` as unknown or
   missing and produce at most a research plan or initial lead list.
7. When source text is available, enter it as a normal Source and Observation
   and run the existing evidence, review, audit, and export gates before a
   formal delivery.

Do not treat this manual procedure as an automated eval result. It does not
authorize a search summary, link, citation, model memory, or capability report
to support a formal fact or contact.

## Shell HTTP Source Open

Status: manual host acceptance, not an automated model-behavior evaluation.

In a fresh Codex CLI session, use this only when the host authorizes a
read-only shell request to a public company page. Record the host as
`codex_cli`, never as a command name.

1. Perform exactly a public HTTP(S) `GET` using an allowed concrete reader
   (`curl`, `wget`, or `python_requests`), without cookies, authorization,
   credentials, POST, local/private addresses, or access-control workarounds.
2. Retain the original and final URLs, 2xx status, title or equivalent source
   identifier, verbatim excerpt, and locator from the actual page response.
3. Add the controlled shell HTTP provider report and declare `source.open`
   available for the same Run. Record the concrete reader on each Observation.
4. Do not mark `search.web` available from this operation. If native search is
   separately available, record it as its own provider in the same Run.
5. Run normal graph validation, audit, and export gates before delivery.

This manual procedure does not authorize search snippets, private endpoints,
credentials, or a shell command without one recorded public-source success.
