---
name: collecting-contact-intelligence
description: "Use when public business contacts need collection, source tracking, or ownership-status handling in Superleads."
---

# Collecting Contact Intelligence

## Purpose

Maximize recall of sourced contact intelligence while preventing guessed, source-less, or misassigned contacts from being exported as ready.

For default discovery, use this as an internal/on-demand `discovery` guide
when public contact material is encountered; it is not a mandatory standalone
stage or a reason to require ContactPoint or ContactClaim for every Candidate.

## Required references

Read `../../shared/policies/contact-intelligence-policy.md` and `../../shared/schemas/contact-intelligence.schema.json`.

## Workflow

1. Extract visible contact details from Observations only.
2. Create `ContactPoint` for the literal value and its source observation.
3. Create `ContactClaim` only when there is context linking the contact to an entity, person, department, role, or source section.
4. Use `UnassignedContactLead` for valuable contacts with unclear ownership.
5. Assign export status: `ready`, `export_with_source_note`, `needs_manual_association_review`, `hold_no_source`, or `hold_inferred`.
6. In default discovery, keep `needs_manual_association_review` and
   `UnassignedContactLead` visible as 待确认归属 instead of hiding them.

For `published_source_copy`, source and association Observations must each be eligible `document.extract` records with matching artifact-hash locators. Preserve literal, normalization, and Entity association checks exactly as for public sources; a row or page containing multiple companies is not enough by itself. Historical CRM/dataset and correspondence exports can only be `export_with_source_note`, with explicit same-Entity context. Pasted notes and image/OCR contacts remain Candidate or UnassignedContactLead until independently verified.

Inbound `mail.read` can capture a reply email as a sourced contact lead only when the literal occurs in the bounded mail Observation and entity context is explicit. It is `export_with_source_note` at most and must display as 来信联系人/待核验, never ready, official, or procurement-authority evidence. A From address alone has no automatic company ownership or authority.

## Inline red flags

- Do not construct `info@domain.com` or any email pattern.
- Do not attach a phone to a company without association context.
- Treat LinkedIn job titles as role clues, not procurement authority facts.
- Treat email verification as quality only, never as source evidence.
- Keep ambiguous contacts as 待确认归属 instead of dropping them.
