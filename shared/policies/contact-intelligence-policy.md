# Contact Intelligence Policy

Maximize recall of sourced, attributable, and clearly labeled contact intelligence. Do not hide weak but useful contact leads; label them correctly.

## Collectable contact types

Collect company emails, department emails, sales emails, purchasing/supplier portal emails, personal business emails, public phones, mobile numbers, WhatsApp, fax, contact forms, supplier portals, inquiry entries, LinkedIn company pages, LinkedIn personal visible pages, visible names, visible titles, visible departments, addresses, map phones, trade fair contacts, PDF/catalog contacts, and third-party directory contacts.

## Contact artifacts

- `ContactPoint` records the literal contact detail and the observation where it appeared.
- `ContactClaim` records why that contact belongs to an entity, person, department, or role.
- `UnassignedContactLead` keeps useful but ambiguous contact details without pretending ownership is resolved.

## Export status mapping

| Internal export_status | User label | Meaning |
|---|---|---|
| `ready` | 可直接使用 | Source and association are clear enough for direct export. |
| `export_with_source_note` | 建议核查后使用 | Usable with source note or minor uncertainty. |
| `needs_manual_association_review` | 待确认归属 | Contact exists but ownership or role association needs checking. |
| `hold_no_source` | 不可导出 | Contact lacks a source observation. |
| `hold_inferred` | 不可导出 | Contact was guessed or inferred. |

Never mark as `ready`: guessed emails from a domain or name, source-less phone/mobile values, email.verify-only contacts, enrichment-only contacts with no public source, login-wall or hidden content, and contacts with no association evidence.

For standard or full delivery, only `ready` and `export_with_source_note` ContactClaims may expose a contact value, and both must resolve to an Entity. `needs_manual_association_review` stays as an internal pending reference. `hold_no_source` and `hold_inferred` values must be redacted from every user-visible field, including notes, warnings, disclosures, CSV, XLSX, and Manifest output.

Visible job titles are role clues. They are not proof of purchasing authority, decision power, or current procurement responsibility unless an observed source directly says so.
