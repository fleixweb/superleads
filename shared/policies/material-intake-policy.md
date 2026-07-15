# Material Intake Policy

Every submitted material is classified before it is used as evidence. Submission to Superleads does not make content an external fact.

| material_role | Formal Claim / Assessment basis | Contact export | Candidate / search work |
|---|---|---|---|
| public HTTP(S) source | Allowed through existing gates | `ready` or source note when eligible | Allowed |
| `published_source_copy` | Allowed through hash, locator, excerpt, entity, translation, Review, Audit, and Manifest gates | `ready` or source note when eligible | Allowed |
| `user_business_dataset` | Not allowed alone | `export_with_source_note` only when literal and Entity association are explicit | Allowed |
| `correspondence_export` | Not allowed as qualification basis | `export_with_source_note` only when literal and Entity association are explicit | Allowed |
| `user_authored_note` | Not allowed | Not exportable | Allowed |
| `visual_reference` | Not allowed | Not exportable | Allowed |
| `connected_inbound_correspondence` | Not allowed | `export_with_source_note` only with literal, same-Entity context, and `mail.read` | Allowed; may create Inquiry |
| `unknown` | Not allowed | Not exportable | Allowed |

`material_role` is required for `user_provided`, `manual_input`, and `connected_account`. When a file's nature is unclear, use `user_business_dataset` or `unknown`; never upgrade it automatically to `published_source_copy`. Ask only: "这份材料是原始公开/对方资料，还是你自己整理的历史名单或备注？"

All uploaded binaries, including images, require a safe display filename, SHA-256, content hash, and safe artifact locator. Do not store or export paths, `file:` URIs, drive-qualified names, or artifact hashes. The metadata proves a graph reference to a fixed artifact; it does not prove the artifact is official or current.

`correspondence_export` may record that a person stated something in a supplied communication record. It cannot establish corporate qualifications, purchase authority, current demand, trademark ownership, or company relationships, and it cannot enter `Assessment.basis_claim_ids`.

`image.inspect` records OCR text verbatim or an explicitly labeled visual description. It may create Candidates, search tasks, Hypotheses, or UnassignedContactLeads. A logo, product photo, screenshot, or business-card photo is never direct ownership, trademark, purchasing-authority, or ready-contact proof.

## Inbound mail and inquiry

Connected inbound mail is a separate, read-only intake route. It needs a host opaque `mailbox_ref`, inbound direction, received time, sender/subject literals, message-content SHA-256, bounded excerpt, and a safe `mail:sha256:<hash>#part=...` locator. It creates an `Inquiry` for follow-up, not a verified buyer or formal lead assessment. Mail attachments default to `unknown`; only an explicitly classified `published_source_copy` attachment can enter the controlled document/spreadsheet evidence branch.

MailIntakeRule scope is explicit: a non-empty folder/label list, a time window for one-shot runs, inbound direction, read-only true, and only create-inquiry/candidate/source-note-contact/entity-resolution actions. Continuous rules require user approval and host scheduling support. No password, token, absolute path, `file:` URI, complete mail body, message ID, or thread ID is put into a workbook or user-facing manifest.
