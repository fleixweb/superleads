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
    ("scripts/_superleads_common.py", "Canonical disclosure"),
    ("scripts/validate_superleads_user_visible_output.py", "最终用户可见边界"),
    ("scripts/audit_delivery.py", "交付门禁"),
    ("scripts/validate_research_graph.py", "结构门禁"),
)


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
