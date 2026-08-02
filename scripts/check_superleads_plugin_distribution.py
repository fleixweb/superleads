#!/usr/bin/env python3
"""Check that a Superleads plugin install/cache contains the runtime files the Skills reference.

The check is intentionally distribution-oriented: it compares the installed or
packaged plugin root against the source repository's ``skills/`` directory, then
verifies the product-market route's required files and every ``../../spec`` /
``../../shared`` relative reference found in installed ``SKILL.md`` files.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUIRED_SKILLS = ("analyzing-product-outbound-market",)
DEFAULT_REQUIRED_FILES = (
    Path("shared/references/product-outbound-market-intake.md"),
)
RELATIVE_REFERENCE_RE = re.compile(r"\.\./\.\./(?:spec|shared)/[A-Za-z0-9._/\-]+")


def _issue(code: str, message: str, **extra: str) -> dict[str, str]:
    payload = {"code": code, "message": message}
    payload.update({key: value for key, value in extra.items() if value})
    return payload


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _skill_dirs(root: Path) -> list[str]:
    skills_root = root / "skills"
    if not skills_root.exists() or not skills_root.is_dir():
        return []
    return sorted(item.name for item in skills_root.iterdir() if item.is_dir())


def _scan_skill_references(plugin_root: Path) -> tuple[list[dict[str, str]], int]:
    issues: list[dict[str, str]] = []
    checked = 0
    root_resolved = plugin_root.resolve()
    skills_root = plugin_root / "skills"
    for skill_md in sorted(skills_root.glob("*/SKILL.md")) if skills_root.exists() else []:
        try:
            text = skill_md.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive IO path
            issues.append(_issue(
                "plugin_distribution_skill_read_failed",
                f"failed to read Skill file: {exc}",
                path=str(skill_md),
            ))
            continue
        for match in RELATIVE_REFERENCE_RE.finditer(text):
            checked += 1
            rel = match.group(0)
            target = skill_md.parent / rel
            target_resolved = target.resolve(strict=False)
            if not _is_relative_to(target_resolved, root_resolved):
                issues.append(_issue(
                    "plugin_distribution_reference_escapes_root",
                    f"Skill relative reference escapes plugin root: {rel}",
                    path=str(skill_md.relative_to(plugin_root)),
                    reference=rel,
                    resolved=str(target_resolved),
                ))
                continue
            if not target.exists():
                issues.append(_issue(
                    "plugin_distribution_reference_missing",
                    f"Skill relative reference is missing from plugin distribution: {rel}",
                    path=str(skill_md.relative_to(plugin_root)),
                    reference=rel,
                    resolved=str(target.relative_to(plugin_root)),
                ))
    return issues, checked


def check_distribution(
    plugin_root: Path,
    source_root: Path,
    required_skills: tuple[str, ...] = DEFAULT_REQUIRED_SKILLS,
    required_files: tuple[Path, ...] = DEFAULT_REQUIRED_FILES,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    plugin_root = plugin_root.resolve()
    source_root = source_root.resolve()

    if not plugin_root.exists() or not plugin_root.is_dir():
        issues.append(_issue(
            "plugin_distribution_root_missing",
            "plugin root does not exist or is not a directory",
            path=str(plugin_root),
        ))
        return {
            "ok": False,
            "issue_count": len(issues),
            "issues": issues,
            "plugin_root": str(plugin_root),
            "source_root": str(source_root),
        }

    plugin_skills_root = plugin_root / "skills"
    source_skills_root = source_root / "skills"
    if not plugin_skills_root.exists() or not plugin_skills_root.is_dir():
        issues.append(_issue(
            "plugin_distribution_skills_dir_missing",
            "plugin distribution lacks skills/ directory",
            path=str(plugin_skills_root),
        ))
    if not source_skills_root.exists() or not source_skills_root.is_dir():
        issues.append(_issue(
            "plugin_distribution_source_skills_dir_missing",
            "source root lacks skills/ directory",
            path=str(source_skills_root),
        ))

    plugin_skill_names = _skill_dirs(plugin_root)
    source_skill_names = _skill_dirs(source_root)
    plugin_skill_set = set(plugin_skill_names)
    source_skill_set = set(source_skill_names)

    if source_skill_names and len(plugin_skill_names) != len(source_skill_names):
        issues.append(_issue(
            "plugin_distribution_skill_count_mismatch",
            f"plugin skills count {len(plugin_skill_names)} does not match source skills count {len(source_skill_names)}",
            plugin_count=str(len(plugin_skill_names)),
            source_count=str(len(source_skill_names)),
        ))
    for name in sorted(source_skill_set - plugin_skill_set):
        issues.append(_issue(
            "plugin_distribution_skill_missing",
            f"source skill is missing from plugin distribution: {name}",
            path=f"skills/{name}",
        ))
    for name in sorted(plugin_skill_set - source_skill_set):
        issues.append(_issue(
            "plugin_distribution_unexpected_skill",
            f"plugin distribution contains a skill not present in source: {name}",
            path=f"skills/{name}",
        ))

    for name in required_skills:
        skill_file = plugin_root / "skills" / name / "SKILL.md"
        if not skill_file.exists():
            issues.append(_issue(
                "plugin_distribution_required_skill_missing",
                f"required Skill file missing from plugin distribution: skills/{name}/SKILL.md",
                path=str(skill_file.relative_to(plugin_root)) if _is_relative_to(skill_file, plugin_root) else str(skill_file),
            ))

    for rel in required_files:
        target = plugin_root / rel
        if not target.exists():
            issues.append(_issue(
                "plugin_distribution_required_file_missing",
                f"required runtime file missing from plugin distribution: {rel.as_posix()}",
                path=rel.as_posix(),
            ))

    reference_issues, reference_count = _scan_skill_references(plugin_root)
    issues.extend(reference_issues)

    return {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "plugin_root": str(plugin_root),
        "source_root": str(source_root),
        "plugin_skill_count": len(plugin_skill_names),
        "source_skill_count": len(source_skill_names),
        "plugin_skills": plugin_skill_names,
        "source_skills": source_skill_names,
        "checked_skill_relative_reference_count": reference_count,
        "required_skills": list(required_skills),
        "required_files": [path.as_posix() for path in required_files],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root",
        default=str(ROOT),
        help="Installed/cache/package plugin root to check. Defaults to this repository root.",
    )
    parser.add_argument(
        "--source-root",
        default=str(ROOT),
        help="Source repository root used for skills/ parity. Defaults to this repository root.",
    )
    parser.add_argument(
        "--required-skill",
        action="append",
        dest="required_skills",
        help="Required skill directory name. May be repeated. Defaults to the product-market skill.",
    )
    parser.add_argument(
        "--required-file",
        action="append",
        dest="required_files",
        help="Required runtime file relative to plugin root. May be repeated. Defaults to the product-market intake reference.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required_skills = tuple(args.required_skills) if args.required_skills else DEFAULT_REQUIRED_SKILLS
    required_files = tuple(Path(item) for item in args.required_files) if args.required_files else DEFAULT_REQUIRED_FILES
    payload = check_distribution(Path(args.plugin_root), Path(args.source_root), required_skills, required_files)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"ok={str(payload['ok']).lower()} issue_count={payload['issue_count']}")
        for issue in payload["issues"]:
            print(f"- {issue['code']}: {issue['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
