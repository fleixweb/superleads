# Superleads Conversational Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give ChatGPT users a compact, language-adaptive Superleads first-use guide and ensure formal user-facing delivery has one non-duplicated support-and-security footer.

**Architecture:** A small shared reference contains one set of business-language rules for the model, including help routing, language adaptation, boundaries, and final-message footer placement. A pure Python guidance module provides deterministic help-intent detection and footer rendering for the intake eval harness and formal Markdown exporter; it performs no I/O. The existing route classifier stays the single task-routing authority, while the existing Markdown renderer stays the single formal-report renderer.

**Tech Stack:** Python 3 standard library, `unittest`, JSON route/eval fixtures, Markdown Skill references.

---

## File Map

| Path | Responsibility |
| --- | --- |
| `shared/references/superleads-user-guidance.md` | Sole human/model-facing source for compact guide, dynamic-language rule, boundaries, and footer semantics. |
| `scripts/superleads_user_guidance.py` | Pure help-intent classifier, stable guide-response contract, language hint, and idempotent Markdown footer helper. |
| `scripts/route_superleads_intake.py` | Calls the pure helper before business-route detection and returns a `first_use_guide` route. |
| `scripts/export_superleads_markdown.py` | Appends the footer exactly once before the existing visible-output validation. |
| `scripts/validate_superleads_user_visible_output.py` | Treats a missing or duplicated footer as a user-visible delivery contract failure. |
| `skills/using-superleads/SKILL.md` | Makes static guide handling the first branch, before formal-run work; describes direct-task bypass and final-message footer use. |
| `skills/analyzing-product-outbound-market/SKILL.md` | Refers final market delivery and capability-stop output to the shared guidance. |
| `skills/researching-customer-background/SKILL.md` | Refers final background-report delivery to the shared guidance. |
| `skills/exporting-lead-workbooks/SKILL.md` | Refers Excel/CSV completion messages and Markdown delivery to the shared guidance. |
| `skills/collecting-contact-intelligence/SKILL.md` | Refers final contact-check delivery to the shared guidance. |
| `skills/using-superleads/agents/openai.yaml`, `.codex-plugin/plugin.json` | Use the three user business entries rather than technical lead-research wording in exposed descriptions/prompts. |
| `tests/test_superleads_user_guidance.py` | Unit coverage for static intent/language metadata, footer semantics, idempotency, and no-I/O helpers. |
| `evals/cases/superleads_route_cases.json` | End-to-end classifier assertions for Chinese/English help and direct task routing. |
| `evals/cases/superleads_markdown_delivery_cases.json` | Generated bulk/background/market reports must include exactly one footer. |
| `evals/cases/superleads_user_visible_output_cases.json`, `evals/user_visible_outputs/*.md` | Require the canonical Chinese footer in final report fixtures and add negative missing/duplicate cases. |

## Task 1: Create the Shared Contract and Its Failing Tests

**Files:**
- Create: `shared/references/superleads-user-guidance.md`
- Create: `scripts/superleads_user_guidance.py`
- Create: `tests/test_superleads_user_guidance.py`

- [ ] **Step 1: Write the failing unit tests**

Create `tests/test_superleads_user_guidance.py`, add `scripts/` to `sys.path`, and define the following assertions before the module exists:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import superleads_user_guidance as guidance


class SuperleadsUserGuidanceTest(unittest.TestCase):
    def test_bare_invocation_and_help_questions_are_static_help(self) -> None:
        self.assertEqual("first_use_guide", guidance.static_help_response("@superleads")["route"])
        self.assertEqual("first_use_guide", guidance.static_help_response("你能干嘛？")["route"])
        self.assertEqual("first_use_guide", guidance.static_help_response("What can you do?")["route"])

    def test_real_tasks_do_not_match_static_help(self) -> None:
        for text in (
            "找德国做工业传感器的进口商",
            "查一下 example.com 这家公司做什么",
            "分析中国出口保温杯到越南的公开价格和准入要求",
        ):
            self.assertIsNone(guidance.static_help_response(text))

    def test_help_response_has_language_hint_and_no_run_side_effects(self) -> None:
        response = guidance.static_help_response("What can you do?")
        self.assertEqual("en", response["language"])
        self.assertEqual([], response["operations"])
        self.assertIn("help", response["response_contract"])

    def test_footer_is_localized_and_idempotent(self) -> None:
        zh = guidance.append_final_footer("# 报告\n", language="zh")
        self.assertIn("https://github.com/fleixweb/superleads/issues", zh)
        self.assertIn("小红书搜索 Fleixweb", zh)
        self.assertEqual(zh, guidance.append_final_footer(zh, language="zh"))
        self.assertEqual(1, zh.count(guidance.SUPPORT_FOOTER_MARKER))

    def test_footer_has_no_network_or_filesystem_dependency(self) -> None:
        self.assertEqual([], guidance.guidance_side_effects())
        self.assertNotIn("http", guidance.append_final_footer("done", language="en").splitlines()[0])
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest tests/test_superleads_user_guidance.py -v
```

Expected: `ModuleNotFoundError: No module named 'superleads_user_guidance'`.

- [ ] **Step 3: Add the one shared Markdown reference**

Write `shared/references/superleads-user-guidance.md` with the following required content, all in one document:

```markdown
# Superleads User Conversation Guidance

## Static First-Use Help

For a bare `@superleads`, “你能干嘛”, “怎么用”, “帮助”, “新手入门”,
“What can you do?”, “how do I use this?”, or an equivalent request for usage,
reply without tools. Do not create a Run Context or research record; do not
search, open a source, run preflight, export, validate, check versions, scan
caches, or make a network request.

Choose the response language from the user's current message. Keep the same
three entries, input fields, examples, evidence boundaries, and footer meaning
in every language. Do not maintain a second language file or use internal
search-language settings as the user-interface language.

## Guide Structure

Use a compact chat reply: one identity sentence; one sentence saying `@` ->
select Superleads -> describe the need; `批量开发客户`, `单一客户背调`, and
`目标市场分析`, each with `请提供` and one copyable `例如`; then `更多用法`,
the evidence/decision boundary, and the final footer. Do not use cards,
tables, buttons, marketing claims, or internal terms.

## Final Footer

Use the final footer only once on a completed or stopped user delivery. Do not
add it to progress messages or a standalone clarification. Keep the GitHub
Issues URL, Xiaohongshu `搜索 Fleixweb` instruction, and sensitive-data warning.
```

The document must also contain the user-approved Chinese guide wording and the
canonical Chinese footer verbatim. It must state that a candidate pool is not
a formal development list, search results are not facts, Superleads does not
choose customers or decide market entry, and public contacts do not prove a
private identity or purchasing authority.

- [ ] **Step 4: Implement the pure helper**

Create `scripts/superleads_user_guidance.py` with these public names and no
imports other than `re` and typing helpers:

```python
SUPPORT_FOOTER_MARKER = "<!-- superleads-support-and-safety -->"

def static_help_response(text: str) -> dict[str, object] | None:
    """Return static help metadata, never a research operation."""

def append_final_footer(text: str, *, language: str = "zh") -> str:
    """Append one localized final footer without fetching its support URL."""

def has_exactly_one_final_footer(text: str) -> bool:
    """Check the stable marker count used by the delivery contract."""

def guidance_side_effects() -> list[str]:
    """Expose the empty static-operation contract for regression tests."""
```

`static_help_response` must only match a normalized bare invocation or a
narrow Chinese/English help phrase. It returns:

```python
{
    "route": "first_use_guide",
    "next_skill": "using-superleads",
    "response_contract": "static_first_use_help",
    "language": "zh" | "en" | "user_language",
    "operations": [],
    "response_lines": [],
}
```

It intentionally returns guide metadata, rather than a second hard-coded
English guide. The Skill renders the shared business content in the user's
language. `append_final_footer` holds one marker and two short localized
renderings in the same helper; its English rendering must preserve the Issues
URL, the instruction to search Xiaohongshu for `Fleixweb`, and the sensitive
data warning.

- [ ] **Step 5: Run the focused unit test to verify it passes**

Run:

```bash
python3 -m unittest tests/test_superleads_user_guidance.py -v
```

Expected: all `SuperleadsUserGuidanceTest` tests pass.

## Task 2: Route Static Help Before Research Intake

**Files:**
- Modify: `scripts/route_superleads_intake.py`
- Modify: `evals/cases/superleads_route_cases.json`
- Modify: `evals/run_superleads_route_evals.py`

- [ ] **Step 1: Add failing route cases**

Prepend these cases to `evals/cases/superleads_route_cases.json`:

```json
{
  "name": "bare Superleads invocation shows static Chinese guide",
  "text": "@superleads",
  "expected_route": "first_use_guide",
  "expected_next_skill": "using-superleads",
  "expected_split_customer_development": false,
  "expected_missing_fields": [],
  "expected_response_contract": "static_first_use_help",
  "expected_language": "zh"
}
```

Add an analogous Chinese `你能干嘛` case and an English `What can you do?`
case with `expected_language: "en"`. Add direct cases for the approved bulk,
single-domain, market-analysis, and table-enrichment inputs and assert their
route is not `first_use_guide`.

Extend `_run_case` in `evals/run_superleads_route_evals.py` to compare
`response_contract` and `language` whenever the case supplies
`expected_response_contract` or `expected_language`:

```python
for key, expected_key in (
    ("response_contract", "expected_response_contract"),
    ("language", "expected_language"),
):
    if expected_key in case and actual.get(key) != case.get(expected_key):
        problems.append(f"{key} expected {case.get(expected_key)!r} got {actual.get(key)!r}")
```

- [ ] **Step 2: Run the route eval to verify it fails**

Run:

```bash
python3 evals/run_superleads_route_evals.py --suite all
```

Expected: new help cases fail because `@superleads` currently resolves to bulk
development and help questions resolve to `unknown`.

- [ ] **Step 3: Add the early pure help branch**

At the beginning of `classify` in `scripts/route_superleads_intake.py`, import
and call `static_help_response` before any marker/routing work:

```python
from superleads_user_guidance import static_help_response

def classify(text: str) -> dict[str, Any]:
    static_help = static_help_response(text)
    if static_help is not None:
        return static_help
    # Existing business routing follows unchanged.
```

Do not create a Run, invoke a preflight, inspect versions/caches, or add any
subprocess/network call. Keep the existing unknown-task clarification unchanged
for non-help text that lacks task intent.

- [ ] **Step 4: Run the route eval to verify it passes**

Run:

```bash
python3 evals/run_superleads_route_evals.py --suite all
```

Expected: all route cases pass, including Chinese and English help and the
four direct task cases.

## Task 3: Add One Footer to Formal Markdown Output and Its Contract

**Files:**
- Modify: `scripts/export_superleads_markdown.py`
- Modify: `scripts/validate_superleads_user_visible_output.py`
- Modify: `evals/cases/superleads_markdown_delivery_cases.json`
- Modify: `evals/cases/superleads_user_visible_output_cases.json`
- Modify: relevant final-output fixtures under `evals/user_visible_outputs/`

- [ ] **Step 1: Write failing footer contract cases**

Add these generated-Markdown assertions to every passing case in
`superleads_markdown_delivery_cases.json`:

```json
"must_contain": [
  "Superleads 支持",
  "https://github.com/fleixweb/superleads/issues",
  "小红书搜索 Fleixweb",
  "未经脱敏的客户敏感资料"
],
"footer_count": 1
```

Extend `evals/run_superleads_markdown_delivery_evals.py` to count
`superleads-support-and-safety` in generated text when `footer_count` exists.
Append the canonical Chinese footer and marker to every existing passing
final-report fixture in `evals/user_visible_outputs/`, then add two compact
fixtures/cases: one missing the footer and one with it twice. Both must fail
with the new stable codes:

```text
user_visible_support_footer_missing
user_visible_support_footer_duplicated
```

- [ ] **Step 2: Run the focused output evals to verify they fail**

Run:

```bash
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
python3 evals/run_superleads_user_visible_output_evals.py --suite all
```

Expected: generated reports and unchanged report fixtures fail for a missing
footer; the deliberate duplicate fixture fails for a duplicate footer.

- [ ] **Step 3: Append the footer before validating formal Markdown**

Import `append_final_footer` in `scripts/export_superleads_markdown.py` and
apply it after the selected route renderer returns text, before
`validate_user_visible_markdown` is called:

```python
if text is not None:
    text = append_final_footer(text, language="zh")
```

Do not modify the graph, source data, audit result, CSV/XLSX data sheets, or
export order. This exporter currently renders Chinese reports, so the formal
artifact uses Chinese; the shared Skill rule localizes the surrounding chat
completion for a user writing in another language.

- [ ] **Step 4: Enforce exactly one footer in the visible-output validator**

Import `has_exactly_one_final_footer` and add a final check in `validate`:

```python
if SUPPORT_FOOTER_MARKER not in text:
    issues.append(_issue("user_visible_support_footer_missing", "final delivery must include the Superleads support and security footer"))
elif not has_exactly_one_final_footer(text):
    issues.append(_issue("user_visible_support_footer_duplicated", "final delivery must include the support and security footer exactly once"))
```

The validator remains static: it must not dereference the GitHub URL, perform
search, make a version request, or inspect cache directories.

- [ ] **Step 5: Run focused output evals to verify they pass**

Run:

```bash
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
python3 evals/run_superleads_user_visible_output_evals.py --suite all
```

Expected: all existing output cases pass with the new positive/footer-negative
coverage, and each generated bulk/background/market report has exactly one
marker.

## Task 4: Make Skills and Exposed Prompts Follow the Shared Contract

**Files:**
- Modify: `skills/using-superleads/SKILL.md`
- Modify: `skills/analyzing-product-outbound-market/SKILL.md`
- Modify: `skills/researching-customer-background/SKILL.md`
- Modify: `skills/exporting-lead-workbooks/SKILL.md`
- Modify: `skills/collecting-contact-intelligence/SKILL.md`
- Modify: `skills/using-superleads/agents/openai.yaml`
- Modify: `.codex-plugin/plugin.json`

- [ ] **Step 1: Add failing documentation assertions**

Extend `tests/test_superleads_user_guidance.py` so it reads the one shared
reference and the five Skill files. Assert that the shared reference contains
the three Chinese entry titles, their minimum-format phrases, all three
more-use cases, the Issues URL, `小红书搜索 Fleixweb`, the password/API-key
warning, no internal-title words such as `Run Context`, and the static
no-search/no-preflight rule. Assert that every final-delivery Skill points to
`../../shared/references/superleads-user-guidance.md` and does not contain a
copied full footer heading/URL.

- [ ] **Step 2: Run the unit test to verify it fails**

Run:

```bash
python3 -m unittest tests/test_superleads_user_guidance.py -v
```

Expected: shared-reference and Skill-reference assertions fail before the
documentation edits.

- [ ] **Step 3: Apply only shared-reference links and user-facing rules**

In `skills/using-superleads/SKILL.md`, make the guide reference the first
required reference and add a zero-tool help branch before Workflow step 1.
It must supply the approved compact structure, dynamically use the current
user language, and bypass the full guide for a real task. At the normal
completion point, require the shared footer only for final delivery, including
capability-limited termination and material review; explicitly exclude progress
updates and isolated questions.

In the other four Skills, add only a single shared-reference link and a short
rule for their final output category. Do not paste the full Chinese or English
footer into any Skill.

Revise exposed configuration language to name the three business jobs without
claims such as “best customers”, “high-quality leads”, or technical terms. For
example:

```yaml
interface:
  display_name: "Superleads"
  short_description: "批量开发客户、单一客户背调与目标市场分析"
```

Keep plugin version, manifests, capabilities, and default research routing
unchanged.

- [ ] **Step 4: Run documentation and static-helper tests to verify they pass**

Run:

```bash
python3 -m unittest tests/test_superleads_user_guidance.py -v
python3 -m py_compile scripts/superleads_user_guidance.py scripts/route_superleads_intake.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py
```

Expected: all guidance tests and syntax checks pass.

## Task 5: Full Regression and Review

**Files:**
- Verify only; do not edit unrelated files.

- [ ] **Step 1: Run targeted regressions**

Run:

```bash
python3 -m unittest tests/test_superleads_user_guidance.py -v
python3 evals/run_superleads_route_evals.py --suite all
python3 evals/run_superleads_user_visible_output_evals.py --suite all
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
```

Expected: all pass. Inspect the JSON output to confirm all three generated
routes contain one footer and static help cases carry `operations: []`.

- [ ] **Step 2: Run repository regressions**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 evals/run_evals.py --suite all
git diff --check
git status --short
```

Expected: the test suites and whitespace check pass. The status may include
pre-existing user work; do not revert it.

- [ ] **Step 3: Perform the final manual contract check**

Read a generated Markdown report for each of bulk, background, and market.
Confirm the footer is last, appears once, includes the Issues URL, Fleixweb
search instruction, and sensitive-data warning. Read the bare-invocation and
English-help route JSON; confirm they are `first_use_guide` with no operations.
Confirm a real bulk request, a domain request, a product-market request, and a
table-enrichment request bypass help.

- [ ] **Step 4: Do not commit or push**

The user explicitly prohibited Git commits and pushes for this change. Report
the exact changed source files and test results, but leave all changes
uncommitted. Do not touch plugin caches, backups, temporary directories, or
`tmp/stage5_chillys/`.
