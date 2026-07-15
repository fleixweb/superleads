# Claim and Source Policy

Treat Superleads as a weak-evidence research workflow. Weak evidence may be delivered only when it is explicitly labeled as weak, provisional, or requiring manual check.

## Artifact boundaries

- `search.web` output may create Candidate clues and Search Log rows only.
- A Source exists only after a URL, document, spreadsheet, map result, directory entry, or user-provided material is opened or otherwise inspectable.
- An Observation records visible or extracted content from a Source, including access status and locator.
- A Claim is a fact directly supported by Observation evidence.
- A Hypothesis is a business inference or outreach angle. It must not become a Claim.
- An Assessment is this run's development judgment and must cite Claim IDs as its qualification basis.
- Every formal `supports` ClaimEvidence must carry source-visible anchors for the Claim subject, predicate, claim type, and typed value. A Claim field without a source anchor is not a formal fact.
- A translated Observation may support a Claim only when its `derived_from_observation_id` chain terminates at an accessible, same-entity, non-translated original Observation.
- Formal Claim support requires an inspectable public `http` or `https` Source URL.

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
