# Superleads: Foreign-Trade Customer Development and Export Market Research

[中文（GitHub 首页）](README.md) | **English**

> An evidence-backed research toolkit for export manufacturers, trading companies, and B2B sales teams: discover overseas customers, research importers and distributors, investigate companies, and understand export-market requirements.

Superleads is an evidence-backed foreign-trade research toolkit. It helps export teams discover overseas customers, research importers and distributors, investigate companies and brands, and understand export-market requirements. It supports Claude, Codex, ChatGPT, and Hermes, while keeping verified information, candidate leads, pending checks, source restrictions, and items not covered in the current run separate.

## What You Can Do with Superleads

- **Develop overseas customers**: find importers, distributors, wholesalers, retailers, brands, project buyers, and OEM customers by product, country, channel, and customer type.
- **Investigate a company or brand**: check its public business, product fit, related entities, public contacts, and follow-up risks; identify same-name companies and mismatched websites.
- **Understand an export market**: organize public demand signals, price references, destination requirements, certification and labeling, proof of origin, duties and taxes, export requirements, and logistics considerations.
- **Complete existing research materials**: review customer lists, websites, product catalogs, trade-fair lists, and other public materials while preserving the original information and marking what still needs checking.

## Choose The Right Route

| What you need | Example request | Deliverable | What it will not do |
|---|---|---|---|
| Bulk customer development | “Find customer prospects for a product in a country and customer type.” | Candidate pool, public business signals, websites/sources, public contact routes, pending checks | Will not present candidates as guaranteed buyers or purchase probability |
| Single-customer background research | “Research this company / brand / website.” | Tabular background report: who it is, visible business, related parties, contact routes, cautions, sources | Will not turn public clues into confirmed purchase intent or confirmed purchasing contacts |
| Product outbound market analysis | “Analyze trends, prices, compliance, taxes, logistics, and COO requirements for this product entering this country.” | Product market and access matrix: trade premise, trends/price references, regulatory barriers, taxes, logistics, missing materials | Will not decide whether the market is worth entering, recommend quotations, or turn candidate HS/HTS into final duty rates |

## Who It Is For

- Traditional export manufacturers, trading companies, foreign-trade freelancers, export brands, and B2B sales teams.
- Teams developing importers, distributors, wholesalers, retail chains, brands, project buyers, or OEM customers.
- Teams that want to understand the customer, product, country, compliance, duty, and logistics boundaries before quoting, prospecting, or attending trade fairs.
- Anyone who needs to know whom to contact next, why the prospect matters, and which information still needs human confirmation.

## Why Results Are More Reliable

Superleads requires the Agent to distinguish verified information from leads that still need checking. It retains public-source references, contact ownership, and the basis for business judgment. Search snippets are discovery clues, not facts. Candidates are not guaranteed buyers, and public contacts are not confirmed purchasing contacts.

When evidence is insufficient, the result is marked as candidate, pending check, source restricted, or not reviewed instead of presenting an assumption as fact.

You can therefore review the research, continue unfinished due diligence, remove unreliable companies, and hand usable information to sales for follow-up. In product outbound market analysis, Superleads also separates default export-declaration country, origin/manufacturing source, and actual departure node/port. Destination proof-of-origin, certification, testing, registration, labeling, and packaging-file requirements are checked against public authoritative sources; whether the user already has a certificate is only a material-readiness status and does not decide the regulation.

## Example Output

The table below shows the delivery structure only; it is not a judgment about a real company.

| Company | Type | Public business signal | Contact route | Status |
|---|---|---|---|---|
| Example Importer | Importer | Public directory lists relevant product categories | Company contact page | Candidate, pending check |

Superleads provides research with sources and pending checks. It is not a guaranteed-buyer list or a list of confirmed purchase intentions.

## Supported Agents

- **Claude Code**: used as a Claude Code plugin.
- **ChatGPT / Codex app and Codex CLI**: share one Codex environment installation; no second installation is needed.
- **Hermes**: used as a complete local Skill package.

## Get Started

You do not need to know Git, terminals, or marketplaces. Open the Agent you use, start a new chat, paste the relevant request below, and allow it to perform the installation. If the Agent lacks installation permission, it should state exactly what permission you need to approve instead of leaving you to infer commands.

### Claude Code

```text
Please install the official Superleads package for me. Use the official repository https://github.com/fleixweb/superleads to add the Superleads marketplace, then install superleads@fleix. Confirm that Superleads is enabled when complete. If system permission is required, tell me exactly what I need to approve first. Do not modify my project files.
```

### ChatGPT / Codex App And Codex CLI

The ChatGPT / Codex app and Codex CLI share one Codex environment installation; no second installation is needed.

```text
Please install Superleads in my current Codex environment. Use the official repository https://github.com/fleixweb/superleads to add the Superleads marketplace, then install superleads@fleix. Confirm that it is enabled when complete. If system permission is required, tell me exactly what I need to approve first. Do not modify my project files.
```

### Hermes

```text
Install the official repository https://github.com/fleixweb/superleads as the complete Superleads Skill package in the Skills directory of my current Hermes profile. Do not install it as a Hermes Python plugin and do not copy only one SKILL.md. After installation, confirm that Superleads Skills such as using-superleads are discoverable. Tell me first if permission is required.
```

## Your First Request

After installation, you do not need to learn commands or plan the research yourself. Send one of the requests below to your Agent and replace the bracketed details with your situation.

### You want to develop overseas customers

```text
We manufacture or sell [product] and want to develop importers and distributors in [country or region]. Prioritize companies whose websites show relevant business, exclude obvious mismatches, and organize the candidate companies, websites, public contact routes, sources, useful follow-up angles, and items that still need checking. Do not present unverified leads as facts.
```

### You want to understand one customer before contacting them

```text
I am preparing to contact this company: [company name / website]. Please check what it publicly does, whether it handles [product], which entity it may belong to, where it can be contacted, and what risks I should confirm before follow-up. Keep the sources for every judgment and do not treat search snippets as facts.
```

### You want to understand an export market

```text
I want to sell [product/model] in [country or region]. First help me understand public demand signals, price references, import requirements, certification and labeling, proof of origin, duties and taxes, and logistics requirements. The export country is [China / another country] and the origin country is [if known]. Give me objective references and pending checks only; do not decide whether the market is worth entering.
```

## Updates

You do not need to run Git commands yourself. Paste this request into the same Agent:

```text
Check the official Superleads repository https://github.com/fleixweb/superleads for a newer version. If one is available, update it through my current installation method, then tell me the installed version and whether I need to restart or open a new chat. Do not modify my project files.
```

To receive release notifications, select **Watch -> Custom -> Releases** in this repository.

## License And Releases

Superleads is licensed under [PolyForm Noncommercial 1.0.0](LICENSE). Use, copying, modification, and distribution must follow that license. Before commercial use, resale, hosted services, or inclusion in paid deliverables, review the license boundary and contact Fleix.

Official versions are published from Git tags. Ordinary users only need to use their current Agent installation and update path.

## Feedback

Scan the WeChat QR code below to add Fleix for feedback about Superleads installation, use, prospecting, customer due diligence, or product outbound market analysis.

**Use `Superleads反馈` as the friend-request note. Requests without this note will not be accepted.**

<img src="assets/wechat-feedback-qr.png" alt="Fleix WeChat feedback QR code" width="260">

If Superleads is useful to you, please take a few minutes to register or sign in to GitHub and give this repository a [Star](https://github.com/fleixweb/superleads). Your support helps me maintain and improve Superleads over the long term.

## Technical Documentation

- [Technical installation and update guide (English)](docs/INSTALL-AND-UPDATE.en.md)
- [技术安装与更新说明（中文）](docs/INSTALL-AND-UPDATE.md)
