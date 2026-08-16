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

Read `../../shared/policies/contact-intelligence-policy.md`, `../../shared/schemas/contact-intelligence.schema.json`, and `../../shared/references/superleads-user-guidance.md` for terminal user-delivery footer rules. A final public-contact check follows those rules; progress updates and standalone clarifications do not append the footer.

## Workflow

1. Extract visible contact details from Observations only.
2. Create `ContactPoint` for the literal value and its source observation.
3. Create `ContactClaim` only when there is context linking the contact to an entity, person, department, role, or source section.
4. Use `UnassignedContactLead` for valuable contacts with unclear ownership.
5. Assign export status: `ready`, `export_with_source_note`, `needs_manual_association_review`, `hold_no_source`, or `hold_inferred`.
6. In default discovery, keep `needs_manual_association_review` and
   `UnassignedContactLead` visible as 待确认归属 instead of hiding them.

## Public contact query templates

When the current Brief calls for public contact enrichment, keep every query
anchored to the named company, domain, or person. Use the following patterns
as applicable (replace the quoted values with the current object):

- `site:linkedin.com/in "<公司名>"`
- `"<公司名>" founder OR owner OR CEO OR "managing director" OR "purchasing manager"`
- `"<公司名>" 邮箱 OR 联系方式 OR contact OR "get in touch"`
- `"<公司名>" + <展会名> / <行业协会> / <公开目录站>`
- `"<人名>" "<公司名>"` for cross-checking the same person
- Public Facebook, Instagram, X, or YouTube company pages and public personal pages

The collection target is not limited to purchasing roles. Publicly visible
founders, shareholders, general managers, sales staff, and technical leads are
all useful role clues. A title is never proof of purchasing authority or that
the person is the purchasing lead. Only create a ContactPoint or Observation
from content that was actually opened and inspected; a search-result snippet
can keep a URL as an unverified lead marked `仅搜索结果可见，未打开验证`, but
must not expose the snippet's person name or title as a verified contact.

For a public social or map page, use only normally accessible visible content
that was opened in the current Run. A social company page is separate from a
public professional-person page. A map address or phone is a public contact
clue, not proof of legal-entity identity or procurement ownership. Stop at
login, CAPTCHA, 403, Cloudflare/human verification, payment wall, explicit
automation restriction, or unreadable dynamic content; record 来源受限 and ask
the user to manually check or provide a public link, screenshot, PDF, Excel,
or de-identified material. Do not request or use platform credentials,
Cookies, Tokens, API Keys, paid APIs, or proxy/access-control workarounds.

For `published_source_copy`, source and association Observations must each be eligible `document.extract` records with matching artifact-hash locators. Preserve literal, normalization, and Entity association checks exactly as for public sources; a row or page containing multiple companies is not enough by itself. Historical CRM/dataset and correspondence exports can only be `export_with_source_note`, with explicit same-Entity context. Pasted notes and image/OCR contacts remain Candidate or UnassignedContactLead until independently verified.

Inbound `mail.read` can capture a reply email as a sourced contact lead only when the literal occurs in the bounded mail Observation and entity context is explicit. It is `export_with_source_note` at most and must display as 来信联系人/待核验, never ready, official, or procurement-authority evidence. A From address alone has no automatic company ownership or authority.

## Inline red flags

- Do not construct `info@domain.com` or any email pattern.
- Do not attach a phone to a company without association context.
- Treat LinkedIn job titles as role clues, not procurement authority facts.
- Treat email verification as quality only, never as source evidence.
- Keep ambiguous contacts as 待确认归属 instead of dropping them.
