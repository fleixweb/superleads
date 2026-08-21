#!/usr/bin/env python3
"""Pure prerequisite checks for Superleads internal research stages."""
from __future__ import annotations

from typing import Any


_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "scoping-lead-research": ("route",),
    "writing-research-plans": ("route", "run_id", "brief_present"),
    "executing-research-plans": ("route", "run_id", "brief_present", "plan_present"),
    "collecting-contact-intelligence": ("route", "run_id", "brief_present", "opened_source"),
    "assessing-research-evidence": ("route", "run_id", "brief_present", "evidence_present"),
    "resolving-company-identity": ("route", "run_id", "brief_present", "observation_present"),
    "reviewing-lead-research": ("route", "run_id", "brief_present", "evidence_present"),
    "verification-before-delivery": ("route", "run_id", "brief_present", "evidence_present"),
    "exporting-lead-workbooks": (
        "route", "run_id", "brief_present", "validated_graph", "allowed_output_modes", "requested_output_mode",
    ),
}

_MISSING_MESSAGES = {
    "opened_source": "当前缺少已打开来源，不能整理公开联系方式。",
    "validated_graph": "当前没有可导出的已验证结果，请先完成本轮核验。",
    "allowed_output_modes": "当前结果没有允许的交付方式，不能导出。",
    "requested_output_mode": "请先说明要导出的当前结果格式。",
    "feedback_save_consent": "长期保存反馈前需要你的明确同意。",
    "feedback_class": "请说明反馈是在纠正事实、查询范围，还是长期偏好。",
}


def _present(context: dict[str, Any], field: str) -> bool:
    value = context.get(field)
    if field == "requested_output_mode":
        return isinstance(value, str) and value in set(context.get("allowed_output_modes") or [])
    if field == "allowed_output_modes":
        return isinstance(value, (list, tuple, set)) and bool(value)
    return bool(value)


def _feedback_requirements(context: dict[str, Any]) -> tuple[str, ...]:
    base = ("route", "run_id", "feedback_target")
    if context.get("feedback_action") == "persistent_save":
        return base + ("feedback_save_consent", "feedback_class")
    return base


def _message(missing: list[str]) -> str:
    for field in missing:
        if field in _MISSING_MESSAGES:
            return _MISSING_MESSAGES[field]
    return "当前缺少必要的上游研究上下文，不能直接执行这个内部阶段。"


def validate_internal_invocation(stage: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate host-supplied stage context without I/O, mutation, or research."""
    current = dict(context or {})
    requirements = _feedback_requirements(current) if stage == "learning-from-feedback" else _REQUIREMENTS.get(stage)
    if requirements is None:
        return {
            "allowed": False,
            "missing": ["known_internal_stage"],
            "user_message": "当前内部阶段不可直接调用。",
        }
    missing = [field for field in requirements if not _present(current, field)]
    return {
        "allowed": not missing,
        "missing": missing,
        "user_message": "" if not missing else _message(missing),
    }
