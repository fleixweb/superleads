---
name: reviewing-lead-research
description: "Independently review Superleads lead research for source support, contact ownership, Hypothesis/Claim separation, Assessment overcertainty, identity mismatch, and preserved conflicts. Use before standard or full delivery, or as self-review fallback when independent review is unavailable."
---

# Reviewing Lead Research

## Purpose

Perform semantic review before delivery. Check whether the research graph would mislead a sales user.

## Required references

Read `../../shared/policies/review-and-remediation-policy.md`, `../../shared/policies/contact-intelligence-policy.md`, and `../../shared/references/red-flags.md`.

## Review modes

Set `review_mode` to `independent`, `self_review_fallback`, or `not_run`.

## Checklist

- Does every Claim have supporting Observation evidence?
- Are contact associations reasonable and sourced?
- Did any Hypothesis become a Claim or Assessment basis?
- Is the Assessment too certain for the evidence?
- Are company identities merged or assigned correctly?
- Are conflicts preserved rather than silently discarded?
- Are weak leads labeled instead of overstated?

## Output

Create ReviewFinding records with severity, target artifact, issue, required fix, status, reviewer, review mode, and reviewed time.

## Delivery impact

Independent review plus no blocking findings allows full delivery. Self-review fallback requires disclosure. Not-run review limits output to initial or pending tiers.
