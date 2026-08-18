#!/usr/bin/env python3
"""Regression coverage for Superleads public Skill exposure boundaries.

Baseline before this contract: every internal stage exposed a generic English
default prompt inviting direct use for a Superleads lead-research task. A bare
export or contact request therefore had no visible parent-context stop.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SKILLS = {
    "using-superleads",
    "researching-customer-background",
    "analyzing-product-outbound-market",
}
INTERNAL_TRIGGERS = {
    "assessing-research-evidence": "executing-research-plans：当前 Run 已有已打开来源或待评估证据",
    "collecting-contact-intelligence": "executing-research-plans：当前 Run、Brief 与已打开来源",
    "executing-research-plans": "writing-research-plans：当前 Run、Brief 与 Plan",
    "exporting-lead-workbooks": "verification-before-delivery：当前合法已验证 graph 与允许的输出模式",
    "learning-from-feedback": "using-superleads 或 exporting-lead-workbooks：当前 Run 与指定反馈对象",
    "resolving-company-identity": "executing-research-plans：当前 Run 中已打开来源出现主体冲突",
    "reviewing-lead-research": "assessing-research-evidence：显式深度核验或标准名单的当前证据",
    "scoping-lead-research": "using-superleads：已确认的批量客户发现请求",
    "verification-before-delivery": "executing-research-plans 或 reviewing-lead-research：当前待交付 graph",
    "writing-research-plans": "scoping-lead-research：当前 Brief 已建立",
}
INTERNAL_STAGE_ROOT = ROOT / "shared" / "internal-stages"
FORBIDDEN_PUBLIC_PROMISES = (
    "提供客户推荐",
    "推荐优先客户",
    "预测采购意愿",
    "判断采购意愿",
    "建议跟进",
    "决定是否进入市场",
)


def read_yaml_interface(skill_name: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / "skills" / skill_name / "agents" / "openai.yaml").read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = line.strip().split(":", 1)
        if key == "interface":
            continue
        values[key.strip()] = value.strip().strip('"')
    return values


def read_skill_interfaces(skills_root: Path) -> dict[str, dict[str, str]]:
    return {
        skill_dir.name: read_yaml_interface(skill_dir.name)
        for skill_dir in skills_root.iterdir()
        if (skill_dir / "agents" / "openai.yaml").is_file()
    }


def public_skill_names(configs: dict[str, dict[str, str]]) -> set[str]:
    return {
        name
        for name, interface in configs.items()
        if "公开业务入口" in interface.get("display_name", "")
    }


def internal_skill_names(configs: dict[str, dict[str, str]]) -> set[str]:
    return {
        name
        for name, interface in configs.items()
        if "内部阶段" in interface.get("display_name", "")
    }


class SuperleadsSkillExposureTest(unittest.TestCase):
    def test_only_three_public_skills_are_registered_for_user_discovery(self) -> None:
        configs = read_skill_interfaces(ROOT / "skills")

        self.assertEqual(PUBLIC_SKILLS, public_skill_names(configs))
        self.assertEqual(PUBLIC_SKILLS, set(configs))
        for name in PUBLIC_SKILLS:
            with self.subTest(skill=name):
                self.assertIn("不", configs[name]["short_description"])
                self.assertIn("公开业务入口", configs[name]["display_name"])

    def test_internal_stage_guidance_is_packaged_as_on_demand_references_not_user_skills(self) -> None:
        for skill_name, trigger in INTERNAL_TRIGGERS.items():
            with self.subTest(stage=skill_name):
                reference = INTERNAL_STAGE_ROOT / f"{skill_name}.md"
                self.assertTrue(reference.is_file())
                content = reference.read_text(encoding="utf-8")
                self.assertIn("## 内部阶段前置条件", content)
                self.assertIn(f"父路线触发：{trigger}", content)
                self.assertIn("不要直接调用", content)
                self.assertIn("不得虚构报告", content)

        feedback = (INTERNAL_STAGE_ROOT / "learning-from-feedback.md").read_text(encoding="utf-8")
        self.assertIn("current_run_correction", feedback)
        self.assertIn("persistent_save", feedback)
        self.assertIn("明确同意", feedback)

    def test_plugin_default_prompt_names_only_the_three_public_business_entries(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(
            [
                "批量发现公开客户信息（只交付带来源状态的候选池，不推荐客户）",
                "背调指定公司、品牌、域名或地址（事实受公开来源约束）",
                "分析产品出口到目标市场的客观信息（不判断是否进入市场）",
            ],
            manifest["interface"]["defaultPrompt"],
        )

    def test_public_default_prompts_do_not_promise_business_decisions(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        configs = read_skill_interfaces(ROOT / "skills")
        prompts = [*manifest["interface"]["defaultPrompt"]]
        prompts.extend(configs[name]["default_prompt"] for name in PUBLIC_SKILLS)

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                for forbidden in FORBIDDEN_PUBLIC_PROMISES:
                    self.assertNotIn(forbidden, prompt)

    def test_using_superleads_is_batch_discovery_only(self) -> None:
        content = (ROOT / "skills" / "using-superleads" / "SKILL.md").read_text(encoding="utf-8")
        interface = read_yaml_interface("using-superleads")

        self.assertIn("批量发现公开客户信息", content)
        self.assertIn("不得用于单一客户背调或产品出海市场分析", content)
        self.assertIn("只交付带来源状态的候选池", interface["short_description"])
        self.assertIn("internal-stages", content)

    def test_composite_task_policy_has_one_detailed_authority(self) -> None:
        reference = ROOT / "shared" / "references" / "composite-task-routing.md"
        self.assertTrue(reference.is_file())
        authority = reference.read_text(encoding="utf-8")
        self.assertIn("一个父级组合任务", authority)
        self.assertIn("不得要求用户为了内部架构而拆成多次调用", authority)
        self.assertIn("不得让一个子任务的来源自动升级为另一个子任务的事实", authority)
        self.assertIn("同一主体的身份合并", authority)
        self.assertIn("最终审核、正式导出和组合报告汇总", authority)

        for skill_name in PUBLIC_SKILLS:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("../../shared/references/composite-task-routing.md", content)

    def test_every_public_entry_accepts_any_two_explicit_objectives_as_one_composite_parent(self) -> None:
        for skill_name in PUBLIC_SKILLS:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")

                self.assertIn("任意两个或以上明确业务目标", content)

    def test_public_entries_use_the_deterministic_router_before_route_references(self) -> None:
        router_command = "python3 ../../scripts/route_superleads_intake.py"
        for skill_name in PUBLIC_SKILLS:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(router_command, content)
                self.assertNotIn("static_help_response()", content)

    def test_public_router_is_an_optional_accelerator_with_an_inline_fallback(self) -> None:
        router_command = "python3 ../../scripts/route_superleads_intake.py"
        for skill_name in PUBLIC_SKILLS:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
                router = content.index(router_command)
                availability_window = content[max(0, router - 300) : router]
                fallback_window = content[router : router + 700]

                self.assertIn("脚本可用时", availability_window)
                self.assertIn("脚本不可用时", fallback_window)
                self.assertRegex(fallback_window, r"直接判断路线|内联判断路线")

    def test_global_policy_makes_scripts_optional_accelerators(self) -> None:
        policy = (ROOT / "shared" / "policies" / "tool-capability-policy.md").read_text(encoding="utf-8")

        self.assertIn("任何 `scripts/*.py`", policy)
        self.assertIn("脚本是加速器，不是交付前提", policy)
        self.assertIn("无脚本的等价路径", policy)

    def test_every_public_entry_handles_help_without_tools_before_router_execution(self) -> None:
        router_command = "python3 ../../scripts/route_superleads_intake.py"
        for skill_name in PUBLIC_SKILLS:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
                router = content.index(router_command)
                guard_text = content[:router]
                self.assertRegex(guard_text, r"用户只输入 `@`|用户只输入 `@superleads`|询问简短使用方法")
                self.assertRegex(guard_text, r"不要调用 shell|不运行工具")
                self.assertIn("不搜索", guard_text)
                self.assertRegex(guard_text, r"能力预检|预检")

    def test_market_terminal_facts_require_validation_and_audit_before_delivery(self) -> None:
        skill = (ROOT / "skills" / "analyzing-product-outbound-market" / "SKILL.md").read_text(encoding="utf-8")
        runtime = (ROOT / "shared" / "references" / "product-market-runtime.md").read_text(encoding="utf-8")

        for content in (skill, runtime):
            self.assertRegex(content, r"用户可见事实|最终交付")
            self.assertIn("validate_product_market_analysis.py", content)
            self.assertIn("audit_product_market_analysis.py", content)
            self.assertNotIn("只有来源已打开且用户明确要求正式报告或导出时", content)

    def test_market_preflight_can_be_emulated_when_python_is_unavailable(self) -> None:
        skill = (ROOT / "skills" / "analyzing-product-outbound-market" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("运行或模拟", skill)
        self.assertIn("宿主实际暴露", skill)
        self.assertIn("降低交付层级", skill)
        self.assertNotIn("真实来源能力缺失时停止正式路线", skill)

    def test_market_fact_delivery_has_an_equivalent_no_script_self_check(self) -> None:
        skill = (ROOT / "skills" / "analyzing-product-outbound-market" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("脚本可用时", skill)
        self.assertIn("脚本不可用时", skill)
        self.assertIn("逐项自检", skill)
        self.assertIn("本环境未运行确定性校验", skill)
        self.assertIn("搜索摘要仍只作为线索", skill)

    def test_background_export_has_a_truthful_chat_fallback_without_scripts(self) -> None:
        skill = (ROOT / "skills" / "researching-customer-background" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("脚本不可用时", skill)
        self.assertIn("在对话中按上述六张表交付", skill)
        self.assertIn("本环境未运行确定性校验", skill)
        self.assertIn("不得声称已生成 Markdown、CSV 或 XLSX 文件", skill)

    def test_fast_discovery_uses_host_exposed_search_and_does_not_hard_stop_on_one_adapter_404(self) -> None:
        batch = (ROOT / "shared" / "references" / "batch-discovery-execution.md").read_text(encoding="utf-8")
        execution = (ROOT / "shared" / "internal-stages" / "executing-research-plans.md").read_text(encoding="utf-8")
        adapters = (ROOT / "shared" / "policies" / "platform-adapters.md").read_text(encoding="utf-8")

        for content in (batch, execution, adapters):
            self.assertIn("宿主实际暴露", content)
            self.assertIn("同一失败适配器", content)
        self.assertNotIn("stop the fast candidate-pool path", execution)
        self.assertNotIn("停止快速候选池", batch)

    def test_part_number_is_a_valid_product_anchor_but_requires_public_identity_lookup(self) -> None:
        intake = (ROOT / "shared" / "references" / "user-intake.md").read_text(encoding="utf-8")
        market = (ROOT / "shared" / "references" / "product-outbound-market-intake.md").read_text(encoding="utf-8")

        for content in (intake, market):
            self.assertIn("part number", content.casefold())
            self.assertIn("料号", content)
            self.assertIn("公开检索", content)
            self.assertIn("不是模型推断", content)

    def test_market_entry_defers_development_specs_until_an_explicit_formal_request(self) -> None:
        content = (ROOT / "skills" / "analyzing-product-outbound-market" / "SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("../../spec/", content)
        self.assertIn("../../shared/references/product-market-runtime.md", content)

    def test_bulk_execution_strategy_has_single_bounded_authority(self) -> None:
        strategy = (ROOT / "shared" / "references" / "bulk-execution-strategy.md").read_text(encoding="utf-8")

        for marker in (
            "批量来源优先",
            "并行与分批",
            "滚动去重",
            "中间交付",
            "断点续跑",
        ):
            self.assertIn(marker, strategy)
        self.assertLess(len(strategy), 1000)
        self.assertNotRegex(strategy, r"scripts/|python3")

        composite = (ROOT / "shared" / "references" / "composite-task-routing.md").read_text(encoding="utf-8")
        self.assertIn("bulk-execution-strategy.md", composite)
        self.assertNotIn("独立查询组、来源打开、候选联系人补充和资料整理可以并行规划", composite)

        discovery = (ROOT / "shared" / "references" / "default-discovery-reference.md").read_text(encoding="utf-8")
        self.assertIn("bulk-execution-strategy.md", discovery)
        self.assertNotIn("独立查询组只能标“可并行计划”", discovery)

    def test_public_routes_conditionally_load_bulk_execution_strategy(self) -> None:
        reference = "../../shared/references/bulk-execution-strategy.md"
        for skill_name in PUBLIC_SKILLS:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(reference, content)
                self.assertRegex(content, r"批量、多主体或多查询项|多个主体|多查询项")
                self.assertRegex(content, r"仅在.*读取|单一对象.*不读取")

    def test_table_enrichment_points_to_bulk_execution_strategy(self) -> None:
        user_intake = (ROOT / "shared" / "references" / "user-intake.md").read_text(encoding="utf-8")
        batch = (ROOT / "shared" / "references" / "batch-discovery-execution.md").read_text(encoding="utf-8")

        self.assertIn("bulk-execution-strategy.md", user_intake)
        self.assertIn("bulk-execution-strategy.md", batch)

    def test_platform_capabilities_are_recorded_from_current_session_results(self) -> None:
        adapters = (ROOT / "shared" / "policies" / "platform-adapters.md").read_text(encoding="utf-8")

        self.assertIn("宿主能力按当前会话的实际操作结果记录", adapters)
        self.assertIn("不按安装方式推断", adapters)
        self.assertIn("不沿用历史会话结论", adapters)


if __name__ == "__main__":
    unittest.main()
