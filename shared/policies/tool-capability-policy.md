# Tool Capability Policy

| Capability | Highest allowed layer | Rule |
|---|---|---|
| `search.web` | 初筛客户 / Search Log | Never supports Claim. |
| `source.open` | Observation | Can create Source and Observation. |
| `browser.render` | Observation | Can create Source and Observation. |
| `document.extract` | Observation | Can create document Source and Observation. |
| `image.inspect` | Observation / Candidate clue | May preserve OCR text or visual descriptions and create candidate/search leads. Never supports formal Claim, trademark ownership, or ready contact evidence. |
| `mail.read` | Inquiry / source-note contact | Read-only inbound-mail excerpts may create Inquiry and `export_with_source_note` contact evidence; never supports formal Claim, Assessment basis, or `ready`. |
| `source.capture` | Observation | Store excerpt, locator, and hash. |
| `url.canonicalize` | Source / Entity helper | Normalization only. |
| `entity.dedupe` | Provisional Entity helper | Not final identity resolution. |
| `translate.text` | Observation transform | Preserve original text and link derived observation. |
| `company.enrich` | Candidate clue / contextual | Cannot alone support main table facts. |
| `email.verify` | Contact quality | Does not prove source or ownership. |
| `domain.check` | Technical observation | Does not prove company ownership. |
| `social.visible.read` | Observation | Does not prove purchasing authority. |
| `registry.lookup` | Observation | Can support entity claims. |
| `trademark.lookup` | Observation | Can support brand/trademark claims. |
| `maps.lookup` | Observation | Can support map address/phone claims. |
| `memory.recall` | Plan priority | Never enters Claim or Assessment evidence. |

When a tool is missing, degrade output level instead of fabricating evidence. If no source-opening capability exists, provide a research plan or initial lead list only.

`mail.read` is a host-neutral capability contract, not a Gmail, Outlook, OAuth, MCP, model, or API integration. It reads only the user-approved mailbox reference, folders/labels, time scope, filters, and inbound direction. It never sends, replies, marks read, moves, archives, deletes, or modifies mail. Without it, request an EML/PDF/mail export. Continuous rules only run when the host provides a compliant read-only scheduler/event mechanism; otherwise they are filters applied on the next user-run query.
