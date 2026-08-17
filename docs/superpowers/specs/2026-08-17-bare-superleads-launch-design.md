# Bare Superleads Launch Design

## Goal

Make a bare `@superleads` activation a compact, static response in ChatGPT
Desktop and Codex, without loading batch-research references or initializing a
research workflow.

## Root Cause

The public batch-discovery Skill currently instructs the model to read several
large references before it reaches its metadata-mode classifier. A bare plugin
selection can therefore enter the batch Skill and load research context before
the static help response is considered. The external Superpowers startup Skill
may still add host-owned overhead, but Superleads must not add further work.

## Design

`skills/using-superleads/SKILL.md` becomes a small public dispatcher. Its first
rule handles bare `@`, `@superleads`, and help requests by using
`static_help_response()` with no reference reads, shell commands, research
objects, preflight, search, source opening, export, or validation. It links to
a new batch-discovery execution reference only after a concrete batch request
has been classified.

The existing detailed batch workflow and composite-task guidance move unchanged
in meaning to `shared/references/batch-discovery-execution.md`. The public
entry Skill stays under a 6KB source budget. Its OpenAI agent prompt repeats
the fast-path constraint so the host's displayed entry does not begin a batch
workflow for an empty activation.

## Boundaries

This does not alter evidence rules, formal research, route decisions, caches,
or external Superpowers startup behavior. It does not add a fourth displayed
Skill or an English-specific variant.

## Verification

Regression tests assert that the entry contract precedes every reference read,
contains the zero-operation bare-help rule, remains within its size budget, and
keeps real batch requests routed to the existing discovery path. The existing
help, routing, evaluator, and package-distribution suites remain required.
