# Bare Superleads Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure bare Superleads activation is a compact static branch before any batch-research context is loaded.

**Architecture:** Keep `using-superleads` as the sole displayed batch entry but reduce it to a dispatcher. Move detailed batch and composite rules into an explicitly on-demand shared reference. Lock the host-facing entry contract with source-level regression tests.

**Tech Stack:** Markdown Skills, OpenAI agent YAML, Python `unittest`, existing plugin distribution builder.

---

### Task 1: Lock the host-facing fast-entry contract

**Files:**
- Modify: `tests/test_superleads_user_guidance.py`
- Modify: `skills/using-superleads/agents/openai.yaml`

- [ ] **Step 1: Write the failing test**

```python
def test_batch_entry_contract_puts_bare_help_before_research_references(self) -> None:
    skill = (ROOT / "skills/using-superleads/SKILL.md").read_text(encoding="utf-8")
    self.assertLess(skill.index("static_help_response()"), skill.index("batch-discovery-execution.md"))
    self.assertIn("do not read any research reference", skill)
    self.assertLess(len(skill.encode("utf-8")), 6_000)
```

- [ ] **Step 2: Run the focused test and confirm it fails because the entry Skill still loads references first.**

Run: `python3 -m unittest tests/test_superleads_user_guidance.py -v`

- [ ] **Step 3: Add the minimal entry contract to the public Skill and the agent prompt.**

The agent prompt must say that an empty activation returns static help before
any task setup. The public Skill must make the same prohibition its first
operational instruction.

- [ ] **Step 4: Run the focused test and confirm it passes.**

Run: `python3 -m unittest tests/test_superleads_user_guidance.py -v`

### Task 2: Defer detailed batch rules until after classification

**Files:**
- Create: `shared/references/batch-discovery-execution.md`
- Modify: `skills/using-superleads/SKILL.md`
- Modify: `tests/test_superleads_user_guidance.py`

- [ ] **Step 1: Write the failing test**

```python
def test_batch_entry_keeps_concrete_batch_route_and_defers_execution_reference(self) -> None:
    response = classify("帮我找丹麦做巡演音响的进口商")
    self.assertEqual("bulk_customer_development", response["route"])
    self.assertIn("batch-discovery-execution.md", skill)
```

- [ ] **Step 2: Run the focused test and confirm the execution reference is absent.**

Run: `python3 -m unittest tests/test_superleads_user_guidance.py -v`

- [ ] **Step 3: Move the existing detailed batch workflow and composite-task rules to the new reference.**

The public Skill links to that file only in its concrete batch branch. Preserve
all evidence, capability, formal-delivery, and composite-task constraints.

- [ ] **Step 4: Run focused routing and help tests.**

Run: `python3 -m unittest tests/test_superleads_user_guidance.py tests/test_superleads_task_modes.py -v`

### Task 3: Verify packaged runtime behavior

**Files:**
- Verify: `skills/using-superleads/SKILL.md`
- Verify: `shared/references/batch-discovery-execution.md`

- [ ] **Step 1: Run the unit and route evaluators.**

Run: `python3 -m unittest discover -s tests`

- [ ] **Step 2: Run the full evaluator suite.**

Run: `python3 evals/run_evals.py --suite all`

- [ ] **Step 3: Build and validate the runtime package.**

Run: `python3 scripts/build_superleads_plugin_package.py --output /tmp/superleads-bare-launch-runtime --format json`

Run: `python3 scripts/check_superleads_plugin_distribution.py --plugin-root /tmp/superleads-bare-launch-runtime --source-root . --runtime-package --format json`

- [ ] **Step 4: Check whitespace and repository status.**

Run: `git diff --check && git status --short`
