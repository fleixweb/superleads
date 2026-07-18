# Claim and Source Policy

## Customer-direction boundary

Formal source eligibility proves only the stated Claim. It does not prove that
the Entity belongs in the user's current development direction. For a new
customer-development Brief, a positive Assessment additionally requires the
current Brief's `customer_selection_contract` and an in-scope ScopeDecision
whose rule evidence is same-Entity, formal ClaimEvidence. Search terms,
similar keywords, contact completeness, Candidate clues, user material,
mail.read, image.inspect, and Hypotheses cannot replace this independent
direction check. See `targeting-and-scope-policy.md`.

Treat Superleads as a weak-evidence research workflow. Weak evidence may be delivered only when it is explicitly labeled as weak, provisional, or requiring manual check.

## Default discovery branch

Default discovery does not require every Candidate to become
Entity → Claim → ClaimEvidence → ScopeDecision → Assessment → Review → Audit.
It may deliver a large candidate pool with:

- discovery source and de-duplication basis;
- business relevance status;
- public signal statuses (`observed`, `not_observed`, `not_searched`, `identity_pending`, `source_restricted`);
- sourced contacts plus ownership status;
- unknowns, restrictions, and next verification steps.

Do not silently delete a Candidate only because formal evidence is insufficient.
Formal Claim/Assessment gates remain mandatory only for standard delivery,
formal company checks, contactable lists, and explicit deep verification work.

For `directly_related`, `possibly_related`, and
`explicitly_excluded_or_unrelated`, the Candidate's `business_match` signal
must be `observed`, contain a non-empty business summary, and retain at least
one source label or safe public HTTP(S) URL. `business_relevance_basis` explains
the current-task classification but cannot substitute for that observed signal.
`identity_pending` and `insufficient_information` may retain identity conflict,
unknown, or source-gap notes without inventing an observed business signal or
creating a Claim, ClaimEvidence, Assessment, Review, or Audit.

Candidate `source_url`, `discovery_refs[].url`, and public-signal
`items[].source_url` are user-facing URL fields. When non-empty they use the
same runtime credential-free public HTTP(S) validation as Sources; labels,
user-file names, and restricted-source notes remain usable when no URL is
available.

## Artifact boundaries

- `search.web` output may create Candidate clues and formal SearchLog rows only.
- A SearchLog records the actual query, target geography literals, current
  contract/rule binding when present, capability/provider record, candidate
  result locators, and coverage traces such as new-vs-duplicate candidates,
  opened/failed/restricted sources, and dedupe basis. Its fixed
  `result_use=candidate_seed_only` means it is never a
  Source, Observation, Claim, ClaimEvidence, ScopeDecision, Assessment, or
  ready-contact evidence. Query text, snippets, actor/session IDs, and tool
  internals are never exported to workbooks or user-facing manifests.
- A native host `web_search` call is still `search.web` unless that same
  session separately verifies an opened HTTP(S) source with a source
  identifier, verbatim excerpt, and locator. A search result summary, link,
  or citation cannot become an Observation or ClaimEvidence.
- A Source exists only after a URL, document, spreadsheet, map result, directory entry, or user-provided material is opened or otherwise inspectable.
- An Observation records visible or extracted content from a Source, including access status and locator.
- In a graph containing multiple Runs, each Observation must carry its own
  `run_id`; capability checks use only that Run. An unknown or absent Run ID
  fails closed. Single-Run graphs may use the current compatibility association.
- If that Run carries a native capability adapter report, the Observation's
  capability must be explicitly present in its canonical capabilities with
  status `available`; an omitted capability is not evidence authorization.
- For a Codex shell HTTP Observation, `platform=codex_cli`,
  `capability=source.open`, and the concrete reader (`curl`, `wget`, or
  `python_requests`) remain separate fields. The reader needs a verified
  public-GET provider report and may not be inferred from a tool name or a
  successful shell command alone.
- A Claim is a fact directly supported by Observation evidence.
- A Hypothesis is a business inference or outreach angle. It must not become a Claim.
- An Assessment is this run's development judgment and must cite Claim IDs as its qualification basis.
- Every formal `supports` ClaimEvidence must carry source-visible anchors for the Claim subject, predicate, claim type, and typed value. A Claim field without a source anchor is not a formal fact.
- A translated Observation may support a Claim only when its `derived_from_observation_id` chain terminates at an accessible, same-entity, non-translated original Observation.
- Formal Claim support must pass one controlled source branch:
  - public branch: strict credential-free public `http` or `https` Source URLs and a non-empty Observation excerpt; local/private/loopback/link-local/reserved/multicast/unspecified hosts, localhost/local names, and legacy numeric IPv4 spellings are not public sources;
  - published-copy branch: `provenance=user_provided`, `material_role=published_source_copy`, `medium=document|spreadsheet`, a lowercase SHA-256 and safe display filename, `document.extract`, non-empty excerpt/content hash, and a same-hash `artifact:sha256:<hash>#...` locator.

## User-provided file evidence exception

This is a controlled file-evidence exception, not an exception for chat text, pasted prose, `manual_input`, or model memory. A document locator must identify a page, section, or chapter. A spreadsheet locator must identify both a sheet and a cell/range. `snapshot_ref` may not contain a path, `file:`, control characters, or `..`.

The graph gate validates hash format, source/observation linkage, material role, and reference consistency. It does not claim to re-compute an uploaded file's SHA-256 unless the original binary is retained by the execution environment. All ClaimEvidence relation semantics, same-Entity attribution, translation-origin checks, contradictions, Reviews, Audits, and Manifests remain unchanged. See `material-intake-policy.md` for the purpose matrix.

Public-URL validation is intentionally offline and does not resolve arbitrary
domains. It blocks known IP text bypasses, not DNS rebinding. Any actual HTTP
executor must re-check the resolved address on connection and each redirect,
and reject a non-global target. This does not change the controlled
user-provided PDF/Excel artifact branch.

## Mail and inquiry boundary

`connected_account` inbound correspondence uses `material_role=connected_inbound_correspondence`, `medium=correspondence`, `mail.read`, a message-content SHA-256, and a safe `mail:sha256:<hash>#...` excerpt locator. It may create an Inquiry, Candidate clue, or an explicitly sourced contact note. It cannot support a formal Claim, Assessment basis, qualification conclusion, trademark ownership, purchase authority, or `ready` contact. A mailbox sender is a reply lead, not an official or verified contact by default.

## Hard prohibitions

- Do not write search summaries as verified facts.
- Do not create facts from inaccessible, blocked, login-wall, or unobserved pages.
- Do not use Hypothesis IDs as `Assessment.basis_claim_ids`.
- Do not convert LinkedIn-visible role text into purchasing authority facts.
- Do not hide conflicting evidence; preserve contradictions as ClaimEvidence or ReviewFinding.

## Evidence relation semantics

- `supports`: the observation directly supports the Claim.
- `contradicts`: the observation conflicts with the Claim.
- `contextual`: the observation explains context but does not independently prove the Claim.

If evidence is insufficient, downgrade the lead tier instead of deleting useful weak leads. Block only misleading errors: guessed contacts, source-less facts, identity mismatch, contact misassignment, and stale audit delivery.

## Assessment contract

- Every Assessment belongs to one `run_id`; delivery may use only Assessments from the current Run.
- `rationale_structured` contains `basis_claim_ids` only. It must not carry unanchored factual prose for user delivery.
