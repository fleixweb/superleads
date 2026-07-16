# Codex Native Web Search Host Acceptance

Status: manual host acceptance, not an automated model-behavior evaluation.

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
