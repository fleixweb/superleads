#!/usr/bin/env python3
"""Check ownership and discovery of the shared Superleads delivery contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


CONTRACT = "shared/references/no-script-delivery-contract.md"
CONSUMERS = (
    "shared/policies/tool-capability-policy.md",
    "shared/references/batch-discovery-execution.md",
    "shared/references/product-market-runtime.md",
    "shared/references/using-superleads-formal-delivery.md",
    "shared/internal-stages/exporting-lead-workbooks.md",
    "skills/using-superleads/SKILL.md",
    "skills/analyzing-product-outbound-market/SKILL.md",
    "skills/researching-customer-background/SKILL.md",
)
DISCLOSURE_CONSUMERS = (
    "scripts/_superleads_common.py",
    "scripts/audit_delivery.py",
    "scripts/audit_product_market_analysis.py",
    "scripts/export_workbook.py",
    "scripts/export_product_market_workbook.py",
)
OWNERSHIP_MARKERS = (
    ("no-script-delivery-contract.md", "无脚本交付"),
    ("bulk-customer-development-l1-template.md", "L1 用户可见 Markdown 版式"),
    ("bulk-customer-development-l2-template.md", "L2 用户可见 Markdown 版式"),
    ("scripts/_superleads_common.py", "Canonical disclosure"),
    ("scripts/validate_superleads_user_visible_output.py", "最终用户可见边界"),
    ("scripts/audit_delivery.py", "交付门禁"),
    ("scripts/validate_research_graph.py", "结构门禁"),
)

BULK_TEMPLATE_MARKERS = {
    "shared/references/bulk-customer-development-l1-template.md": (
        "发现候选池样表（候选池不是正式开发名单）",
        "默认 L1 **整段省略**",
        "只有用户明确要求“补社媒 / 地图 / 贸易记录信号”时",
        "| 分区 | 候选客户 | 品牌名称 | 国家/地区 | 可能客户角色 | 当前看到的业务信号 | 业务相关性 | 依据状态 | 可用联系入口 | 还要确认什么 | 来源 / 来源状态 |",
    ),
    "shared/references/bulk-customer-development-l2-template.md": (
        "本次输出为标准开发名单",
        "| 公司名称 | 官网 | 国家/地区 | 客户类型 | 公开信息状态 | 缺失项 | 需人工核查 | 方向状态 | 说明 |",
        "| 公司名称 | 联系方式类型 | 联系方式 | 原文 | 联系人 | 职位/部门 | 状态 | 来源上下文 | 归属证据 | 来源说明 | 来源链接 | 需人工核查说明 |",
        "暂无可展示记录",
    ),
}


def _read(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.exists() else ""


def check_rule_consistency(root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    contract = _read(root, CONTRACT)
    if not contract:
        return [{"code": "rule_contract_missing", "path": CONTRACT}]
    required_contract_terms = (
        "本环境未运行确定性校验",
        "本次已完成核心业务规则校验；补充结构检查未运行。",
        "PYTHONPATH",
        "validate_superleads_user_visible_output.py",
        "at\nruntime",
    )
    for term in required_contract_terms:
        if term not in contract:
            issues.append({"code": "rule_contract_term_missing", "term": term, "path": CONTRACT})
    for relative in CONSUMERS:
        text = _read(root, relative)
        if not text:
            issues.append({"code": "rule_consumer_missing", "path": relative})
            continue
        if CONTRACT not in text and "no-script-delivery-contract.md" not in text:
            issues.append({"code": "rule_consumer_not_linked", "path": relative})
    common = _read(root, "scripts/_superleads_common.py")
    if "DETERMINISTIC_VALIDATION_DISCLOSURE" not in common or "SCHEMA_PROFILE_UNAVAILABLE_DISCLOSURE" not in common:
        issues.append({"code": "canonical_disclosure_constants_missing", "path": "scripts/_superleads_common.py"})
    for relative in DISCLOSURE_CONSUMERS:
        text = _read(root, relative)
        if "DETERMINISTIC_VALIDATION_DISCLOSURE" not in text and "SCHEMA_PROFILE_UNAVAILABLE_DISCLOSURE" not in text:
            issues.append({"code": "disclosure_consumer_not_using_constants", "path": relative})
    ownership = _read(root, "shared/references/rule-ownership.md")
    for marker, label in OWNERSHIP_MARKERS:
        if marker not in ownership or label not in ownership:
            issues.append({"code": "ownership_marker_missing", "marker": marker, "label": label,
                           "path": "shared/references/rule-ownership.md"})
    for relative, markers in BULK_TEMPLATE_MARKERS.items():
        template = _read(root, relative)
        if not template:
            issues.append({"code": "bulk_template_missing", "path": relative})
            continue
        for marker in markers:
            if marker not in template:
                issues.append({"code": "bulk_template_marker_missing", "marker": marker, "path": relative})
    validator = _read(root, "scripts/validate_superleads_user_visible_output.py")
    if "has_exactly_one_final_footer" not in validator or "contains_local_path" not in validator:
        issues.append({"code": "terminal_validator_boundary_missing", "path": "scripts/validate_superleads_user_visible_output.py"})
    return issues


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    issues = check_rule_consistency(root)
    payload: dict[str, Any] = {"ok": not issues, "issues": issues}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
