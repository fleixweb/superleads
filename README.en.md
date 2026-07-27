# Superleads

[中文（GitHub 首页）](README.md) | **English**

> Help foreign-trade professionals use AI agents for customer development, customer due diligence, and product outbound market analysis with fewer LLM hallucinations and more reliable results.

Superleads is a foreign-trade intelligence Skill Suite for traditional export and international B2B trade workflows. It helps foreign-trade professionals use Claude, Codex, the ChatGPT app, and Hermes across three routes: bulk customer development, single-customer background research, and product outbound market analysis. Outputs must separate verified information, candidate clues, pending checks, restricted sources, and not-executed modules instead of turning unclear or unverified information into sales conclusions.

## What You Get

- **Bulk customer development**: find importers, distributors, wholesalers, retailers, brands, project buyers, OEM buyers, and other traditional B2B prospect types by product, country, channel, and customer type.
- **Single-customer background research**: check one company, brand, website, business activity, product fit, public contacts, and contact routes; identify same-name companies, mismatched websites, competitors, and risk items.
- **Product outbound market analysis**: for one product entering or exporting to a target country/region, organize Google Trends search-interest signals, public market information, online price references, seasonality and holidays, destination compliance, certification / testing / registration / labeling requirements, proof-of-origin requirements, import duties/taxes, export-country requirements, logistics routes, and recent external factors.
- **Deliverable tables**: export Markdown, CSV, or Excel. Markdown is easier to read directly in Codex / ChatGPT app conversations; CSV / XLSX is better for sales review, filtering, and handoff.
- **Existing-material enrichment**: use your existing customer lists, websites, product manuals, catalogs, trade-fair lists, or public materials while preserving the original information, then deduplicate, complete, and review it.

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

## Why The Agent Is Not A Black Box

Superleads requires the Agent to distinguish verified information from leads that still need checking. It retains public-source references, contact ownership, and the basis for business judgment. When evidence is insufficient, the result is marked as candidate, pending check, source restricted, or not executed instead of presenting an assumption as fact.

You can therefore review the research, continue unfinished due diligence, remove unreliable companies, and hand usable information to sales for follow-up. In product outbound market analysis, Superleads also separates default export-declaration country, origin/manufacturing source, and actual departure node/port. Destination proof-of-origin, certification, testing, registration, labeling, and packaging-file requirements are checked against public authoritative sources; whether the user already has a certificate is only a material-readiness status and does not decide the regulation.

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

After installation, you can say:

### 1. Bulk customer development

```text
I want to develop [customer type] in [country or region] for [product]. Prioritize [channels or traits] and exclude [conditions]. Use Superleads to prepare an actionable candidate customer table with websites, sources, public contacts, follow-up angles, and pending checks. Do not present unverified leads as facts.
```

### 2. Single-customer background research

```text
Research this customer for me: [company name / website / brand / email / address]. Use tables to show who it is, what it publicly does, related brands or entities, where to contact it, what to check before follow-up, and where the information came from. Do not use search summaries as facts.
```

### 3. Product outbound market analysis

```text
Analyze outbound market conditions for [product/model] entering [target country/region]. The default export-declaration country is [China / another country], the origin country is [if known], and the departure node is [if known]. Use tables for Google Trends, public market and price references, compliance, destination certification/testing/registration/labeling requirements, COO/proof of origin, import duties/taxes, export-country requirements, logistics routes/pre-filing, and recent external factors. I do not know which certificates are needed; first check target-market requirements. Provide objective references only; do not decide whether the market is worth entering.
```

## Output And Export

Ordinary users can ask the Agent to show Markdown tables directly in the chat. Developers or local workflows can use the unified Markdown delivery command:

```bash
python3 scripts/export_superleads_markdown.py input.json --route auto --output report.md --format json
```

You can also specify the route explicitly:

```bash
python3 scripts/export_superleads_markdown.py input.json --route bulk_customer_development --output bulk-report.md --format json
python3 scripts/export_superleads_markdown.py input.json --route customer_background_research --output background-report.md --format json
python3 scripts/export_superleads_markdown.py input.json --route product_outbound_market_analysis --output market-report.md --format json
```

The Markdown delivery command validates the user-visible output before writing the file. CSV / XLSX is better for table delivery and team review. See [Superleads common commands](docs/superleads-common-commands.md).

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

## Technical Documentation

- [Technical installation and update guide (English)](docs/INSTALL-AND-UPDATE.en.md)
- [技术安装与更新说明（中文）](docs/INSTALL-AND-UPDATE.md)
- [Superleads common commands](docs/superleads-common-commands.md)
