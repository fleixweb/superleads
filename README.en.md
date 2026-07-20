# Superleads

[中文（GitHub 首页）](README.md) | **English**

> Customer development with evidence, not a lead list you cannot review.

Superleads is a customer-development and customer due-diligence Skill Suite for traditional foreign-trade and B2B export businesses. It helps Claude, Codex, the ChatGPT app, and Hermes find, research, and organize prospects through a controlled workflow instead of presenting unsupported information as a sales conclusion.

## What You Get

- **Overseas customer development**: find importers, distributors, wholesalers, retailers, brands, project buyers, and OEM buyers by product, market, channel, and customer type.
- **Customer due diligence**: check company identity, brands, websites, actual business activity, product fit, public contacts, and risk signals; identify same-name companies, mismatched websites, competitors, and other issues.
- **Actionable lead lists**: prepare Excel or CSV files with company details, website and source links, public contact information, follow-up suggestions, priorities, pending checks, and risks.
- **Existing-list enrichment**: use your customer lists, websites, directories, and trade-fair lists while preserving original data, then deduplicate, complete, and review it.

## Who It Is For

- Traditional export manufacturers, trading companies, foreign-trade freelancers, export brands, and B2B sales teams.
- Teams developing importers, distributors, wholesalers, retail chains, brands, project buyers, or OEM customers.
- Anyone who needs to know whom to contact next, why the prospect matters, and which information still needs human confirmation.

## Why The Agent Is Not A Black Box

Superleads requires the Agent to distinguish verified information from leads that still need checking. It retains public-source references, contact ownership, and the basis for customer priority. When evidence is insufficient, the result is marked as a candidate or pending check instead of presenting an assumption as fact.

You can therefore review the research, continue unfinished due diligence, remove unreliable companies, and hand usable information to sales for follow-up.

## Supported Agents

- **Claude Code**: used as a Claude Code plugin.
- **Codex CLI and Codex app**: used as a Codex plugin.
- **ChatGPT app**: uses the installed Codex environment and does not need a second Superleads installation.
- **Hermes**: used as a complete local Skill package.

## Get Started

You do not need to know Git, terminals, or marketplaces. Open the Agent you use, start a new chat, paste the relevant request below, and allow it to perform the installation. If the Agent lacks installation permission, it should state exactly what permission you need to approve instead of leaving you to infer commands.

### Claude Code

```text
Please install the official Superleads package for me. Use the official repository https://github.com/fleixweb/superleads to add the Superleads marketplace, then install superleads@superleads-dev. Confirm that Superleads is enabled when complete. If system permission is required, tell me exactly what I need to approve first. Do not modify my project files.
```

### Codex CLI Or Codex App

```text
Please install Superleads in my current Codex environment. Use the official repository https://github.com/fleixweb/superleads to add the Superleads marketplace, then install superleads@superleads-dev. Confirm that it is enabled when complete. If system permission is required, tell me exactly what I need to approve first. Do not modify my project files.
```

### ChatGPT App

Install Superleads once through Codex as described above; no separate installation is needed. Then start a new ChatGPT app chat and say:

```text
Use Superleads to help me develop overseas customers or conduct customer due diligence. Keep the sources, pending checks, and basis for each conclusion.
```

### Hermes

```text
Install the official repository https://github.com/fleixweb/superleads as the complete Superleads Skill package in the Skills directory of my current Hermes profile. Do not install it as a Hermes Python plugin and do not copy only one SKILL.md. After installation, confirm that Superleads Skills such as using-superleads are discoverable. Tell me first if permission is required.
```

## Your First Request

After installation, you can say:

```text
I want to develop [customer type] in [country or region] for [product]. Prioritize [channels or traits] and exclude [conditions]. Use Superleads to prepare an actionable lead list with websites, sources, public contacts, follow-up suggestions, and pending checks. Do not present unverified leads as facts.
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

Scan the WeChat QR code below to add Fleix for feedback about Superleads installation, use, prospecting, or customer due diligence.

**Use `Superleads反馈` as the friend-request note. Requests without this note will not be accepted.**

<img src="assets/wechat-feedback-qr.png" alt="Fleix WeChat feedback QR code" width="260">

## Technical Documentation

- [Technical installation and update guide (English)](docs/INSTALL-AND-UPDATE.en.md)
- [技术安装与更新说明（中文）](docs/INSTALL-AND-UPDATE.md)
