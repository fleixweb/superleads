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
    "learning-from-feedback": "exporting-lead-workbooks：当前交付结果与指定反馈对象",
    "resolving-company-identity": "executing-research-plans：当前 Run 中已打开来源出现主体冲突",
    "reviewing-lead-research": "assessing-research-evidence：显式深度核验或标准名单的当前证据",
    "scoping-lead-research": "using-superleads：已确认的批量客户发现请求",
    "verification-before-delivery": "executing-research-plans 或 reviewing-lead-research：当前待交付 graph",
    "writing-research-plans": "scoping-lead-research：当前 Brief 已建立",
}
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
    def test_only_three_skill_configs_are_described_as_public_business_entries(self) -> None:
        configs = read_skill_interfaces(ROOT / "skills")

        self.assertEqual(PUBLIC_SKILLS, public_skill_names(configs))
        self.assertEqual(set(INTERNAL_TRIGGERS), internal_skill_names(configs))
        self.assertEqual(PUBLIC_SKILLS | set(INTERNAL_TRIGGERS), set(configs))
        for name in PUBLIC_SKILLS:
            with self.subTest(skill=name):
                self.assertIn("不", configs[name]["short_description"])
                self.assertIn("公开业务入口", configs[name]["display_name"])

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
        self.assertIn("verification-before-delivery", content)
        self.assertIn(
            "executing-research-plans` -> `verification-before-delivery` -> `exporting-lead-workbooks",
            content,
        )

    def test_batch_entry_keeps_multi_objective_requests_in_one_isolated_composite_parent(self) -> None:
        content = (ROOT / "skills" / "using-superleads" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("组合任务", content)
        self.assertIn("不得要求用户为了内部架构而拆成多次调用", content)
        self.assertIn("一个父级组合任务", content)
        for subroute in (
            "客户背调子任务",
            "产品市场分析子任务",
            "批量客户发现子任务",
            "表格补全子任务",
            "公开联系人补充子任务",
            "最终导出子任务",
        ):
            with self.subTest(subroute=subroute):
                self.assertIn(subroute, content)
        self.assertIn("等待必要信息", content)
        self.assertIn("不得让一个子任务的来源自动升级为另一个子任务的事实", content)
        self.assertIn("同一主体的身份合并", content)
        self.assertIn("最终审核、正式导出和组合报告汇总", content)
        self.assertIn("不得伪造后台、流式进度或并行工具能力", content)

    def test_every_public_entry_accepts_any_two_explicit_objectives_as_one_composite_parent(self) -> None:
        for skill_name in PUBLIC_SKILLS:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")

                self.assertIn("任意两个或以上明确业务目标", content)
                self.assertIn("一个父级组合任务", content)
                self.assertIn("不得要求用户为了内部架构而拆成多次调用", content)

    def test_internal_stages_name_parent_trigger_and_stop_bare_calls(self) -> None:
        for skill_name, trigger in INTERNAL_TRIGGERS.items():
            with self.subTest(skill=skill_name):
                interface = read_yaml_interface(skill_name)
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")

                self.assertIn("内部阶段", interface["display_name"])
                self.assertIn(f"父路线触发：{trigger}", interface["short_description"])
                self.assertIn("不要直接调用", interface["default_prompt"])
                self.assertIn("缺少上述上下文必须停止", interface["default_prompt"])
                self.assertIn("## 内部阶段前置条件", content)
                self.assertIn(f"父路线触发：{trigger}", content)
                self.assertIn("不要直接调用", content)
                self.assertIn("缺少上述上下文必须停止", content)
                self.assertIn("不得虚构报告", content)


if __name__ == "__main__":
    unittest.main()
