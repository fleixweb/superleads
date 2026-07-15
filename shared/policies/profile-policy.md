# Profile Policy

## No core ICP defaults

Superleads core must not assume any country, industry, company size, channel, buyer type, or platform. Do not import legacy Skill defaults into routing, scoring, assessment, or output.

## Allowed profile use

Profiles may appear only as user-provided inputs, optional search constraints, eval fixtures, failure cases, or conditional search experience tied to the current brief.

## Legacy material

Legacy skill material may live only under `evals/legacy-derived/` as failure cases, anti-pattern prompts, tool misuse examples, contact hallucination cases, and identity mismatch cases.

## Feedback use

User feedback may adjust future ranking, source quality preference, and search-query choices. It must not become Claim evidence, automatic Assessment evidence, or proof of purchase intent.
