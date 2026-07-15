---
name: collecting-contact-intelligence
description: "Extract, normalize, source, and classify Superleads contact intelligence as ContactPoint, ContactClaim, or UnassignedContactLead. Use when emails, phones, WhatsApp, forms, portals, LinkedIn visible pages, people, titles, addresses, maps, PDFs, or directories must be collected with source and ownership status."
---

# Collecting Contact Intelligence

## Purpose

Maximize recall of sourced contact intelligence while preventing guessed, source-less, or misassigned contacts from being exported as ready.

## Required references

Read `../../shared/policies/contact-intelligence-policy.md` and `../../shared/schemas/contact-intelligence.schema.json`.

## Workflow

1. Extract visible contact details from Observations only.
2. Create `ContactPoint` for the literal value and its source observation.
3. Create `ContactClaim` only when there is context linking the contact to an entity, person, department, role, or source section.
4. Use `UnassignedContactLead` for valuable contacts with unclear ownership.
5. Assign export status: `ready`, `export_with_source_note`, `needs_manual_association_review`, `hold_no_source`, or `hold_inferred`.

## Inline red flags

- Do not construct `info@domain.com` or any email pattern.
- Do not attach a phone to a company without association context.
- Treat LinkedIn job titles as role clues, not procurement authority facts.
- Treat email verification as quality only, never as source evidence.
- Keep ambiguous contacts as 待确认归属 instead of dropping them.
