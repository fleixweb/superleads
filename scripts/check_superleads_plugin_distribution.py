#!/usr/bin/env python3
"""Check that a Superleads plugin install/cache contains the runtime files the Skills reference.

The check is intentionally distribution-oriented: it compares the installed or
packaged plugin root against the source repository's ``skills/`` directory, then
verifies the product-market route's required files and every ``../../scripts`` /
``../../spec`` / ``../../shared`` relative reference found in installed
``SKILL.md`` files. ``--runtime-package`` additionally rejects development and
historical-data directories that must not ship in an installed plugin.
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
RELATIVE_REFERENCE_RE = re.compile(r"\.\./\.\./(?:scripts|spec|shared)/[A-Za-z0-9._/\-]+")
RUNTIME_TOP_LEVEL_NAMES = {".claude-plugin", ".codex-plugin", "scripts", "shared", "skills", "spec"}
FORBIDDEN_RUNTIME_NAMES = {".agents", ".git", ".plugin-eval", "docs", "evals", "hooks", "tests", "tmp"}
FORBIDDEN_RUNTIME_SUFFIXES = {".pyc", ".pyo", ".pyd"}
AUTOMATIC_HOOK_EVENT_RE = re.compile(r"\b(?:sessionstart|session[-_ ]?start|resume)\b", re.IGNORECASE)
REMOTE_MANIFEST_FETCH_RE = re.compile(
    r"https?://[^\s\"']*(?:raw\.githubusercontent\.com|github\.com)[^\s\"']*(?:plugin\.json|manifest)",
    re.IGNORECASE,
)


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


def _internal_stage_files(root: Path) -> list[str]:
    stages_root = root / "shared" / "internal-stages"
    if not stages_root.exists() or not stages_root.is_dir():
        return []
    return sorted(path.name for path in stages_root.glob("*.md") if path.is_file())


def _scan_skill_references(plugin_root: Path) -> tuple[list[dict[str, str]], int]:
    issues: list[dict[str, str]] = []
    checked = 0
    root_resolved = plugin_root.resolve()
    skills_root = plugin_root / "skills"
    stage_root = plugin_root / "shared" / "internal-stages"
    documents = list(sorted(skills_root.glob("*/SKILL.md"))) if skills_root.exists() else []
    if stage_root.exists():
        documents.extend(sorted(stage_root.glob("*.md")))
    for skill_md in documents:
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


def _check_codex_manifest(plugin_root: Path) -> list[dict[str, str]]:
    """Require a valid Codex manifest before scanning optional artifacts."""
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists() or not manifest_path.is_file():
        return [_issue(
            "plugin_distribution_manifest_missing",
            "plugin distribution lacks .codex-plugin/plugin.json",
            path=".codex-plugin/plugin.json",
        )]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [_issue(
            "plugin_distribution_manifest_invalid",
            f"failed to parse plugin manifest: {exc}",
            path=".codex-plugin/plugin.json",
        )]
    if not isinstance(manifest, dict):
        return [_issue(
            "plugin_distribution_manifest_invalid",
            "plugin manifest must be a JSON object",
            path=".codex-plugin/plugin.json",
        )]
    if "hooks" in manifest:
        return [_issue(
            "plugin_distribution_hook_configuration_forbidden",
            "plugin manifests must not declare hooks",
            path=".codex-plugin/plugin.json",
        )]
    return []


def _check_hook_artifacts(plugin_root: Path) -> tuple[list[dict[str, str]], int]:
    """Reject all startup hooks and automatic remote-update artifacts."""
    issues: list[dict[str, str]] = []
    checked = 0
    hooks_dir = plugin_root / "hooks"
    if hooks_dir.exists():
        issues.append(_issue(
            "plugin_distribution_hook_directory_forbidden",
            "Superleads runtime and source packages must not contain hooks/",
            path="hooks",
        ))

    candidates: list[tuple[Path, bool]] = []
    if hooks_dir.exists() and hooks_dir.is_dir():
        candidates.extend((path, True) for path in hooks_dir.rglob("*") if path.is_file())
    scripts_dir = plugin_root / "scripts"
    if scripts_dir.exists() and scripts_dir.is_dir():
        candidates.extend(
            (path, False)
            for path in scripts_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() not in FORBIDDEN_RUNTIME_SUFFIXES
            and "__pycache__" not in path.parts
        )
    for path, is_hook_artifact in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(_issue(
                "plugin_distribution_hook_artifact_read_failed",
                f"failed to read hook artifact: {exc}",
                path=path.relative_to(plugin_root).as_posix(),
            ))
            continue
        checked += 1
        relative = path.relative_to(plugin_root).as_posix()
        has_event = AUTOMATIC_HOOK_EVENT_RE.search(text) is not None
        has_remote_manifest = REMOTE_MANIFEST_FETCH_RE.search(text) is not None
        if is_hook_artifact and has_event:
            issues.append(_issue(
                "plugin_distribution_automatic_hook_forbidden",
                "startup or resume hook artifacts are forbidden",
                path=relative,
            ))
        if has_remote_manifest and (is_hook_artifact or has_event):
            issues.append(_issue(
                "plugin_distribution_automatic_remote_update_forbidden",
                "automatic hook artifacts must not fetch remote version manifests",
                path=relative,
            ))
    return issues, checked


def _runtime_package_issues(plugin_root: Path) -> tuple[list[dict[str, str]], int, int]:
    issues: list[dict[str, str]] = []
    files = 0
    byte_count = 0
    for item in sorted(plugin_root.iterdir(), key=lambda path: path.name):
        if item.name not in RUNTIME_TOP_LEVEL_NAMES:
            code = "plugin_distribution_forbidden_path" if item.name in FORBIDDEN_RUNTIME_NAMES else "plugin_distribution_unexpected_runtime_path"
            issues.append(_issue(
                code,
                f"runtime plugin package must not contain {item.name}",
                path=item.name,
            ))
    for path in sorted(plugin_root.rglob("*")):
        relative = path.relative_to(plugin_root)
        if path.is_symlink():
            issues.append(_issue(
                "plugin_distribution_runtime_symlink_forbidden",
                "runtime plugin package must not contain symlinks",
                path=relative.as_posix(),
            ))
            continue
        if path.is_dir() and path.parent != plugin_root and path.name in FORBIDDEN_RUNTIME_NAMES:
            issues.append(_issue(
                "plugin_distribution_forbidden_path",
                f"runtime plugin package must not contain {relative.as_posix()}",
                path=relative.as_posix(),
            ))
        if path.is_dir() and path.name == "__pycache__":
            issues.append(_issue(
                "plugin_distribution_forbidden_path",
                "runtime plugin package must not contain Python bytecode caches",
                path=relative.as_posix(),
            ))
        if path.is_file():
            files += 1
            byte_count += path.stat().st_size
            if path.suffix.lower() in FORBIDDEN_RUNTIME_SUFFIXES:
                issues.append(_issue(
                    "plugin_distribution_forbidden_path",
                    "runtime plugin package must not contain Python bytecode",
                    path=relative.as_posix(),
                ))
    return issues, files, byte_count


def check_distribution(
    plugin_root: Path,
    source_root: Path,
    required_skills: tuple[str, ...] = DEFAULT_REQUIRED_SKILLS,
    required_files: tuple[Path, ...] = DEFAULT_REQUIRED_FILES,
    runtime_package: bool = False,
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

    plugin_internal_stages = _internal_stage_files(plugin_root)
    source_internal_stages = _internal_stage_files(source_root)
    plugin_internal_stage_set = set(plugin_internal_stages)
    source_internal_stage_set = set(source_internal_stages)
    if source_internal_stages and len(plugin_internal_stages) != len(source_internal_stages):
        issues.append(_issue(
            "plugin_distribution_internal_stage_count_mismatch",
            f"plugin internal stage count {len(plugin_internal_stages)} does not match source count {len(source_internal_stages)}",
            plugin_count=str(len(plugin_internal_stages)),
            source_count=str(len(source_internal_stages)),
        ))
    for name in sorted(source_internal_stage_set - plugin_internal_stage_set):
        issues.append(_issue(
            "plugin_distribution_internal_stage_missing",
            f"on-demand internal stage is missing from plugin distribution: {name}",
            path=f"shared/internal-stages/{name}",
        ))
    for name in sorted(plugin_internal_stage_set - source_internal_stage_set):
        issues.append(_issue(
            "plugin_distribution_unexpected_internal_stage",
            f"plugin distribution contains an internal stage not present in source: {name}",
            path=f"shared/internal-stages/{name}",
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

    runtime_issues: list[dict[str, str]] = []
    runtime_file_count = 0
    runtime_byte_count = 0
    if runtime_package:
        runtime_issues, runtime_file_count, runtime_byte_count = _runtime_package_issues(plugin_root)
        issues.extend(runtime_issues)

    issues.extend(_check_codex_manifest(plugin_root))
    hook_issues, checked_hook_artifact_count = _check_hook_artifacts(plugin_root)
    issues.extend(hook_issues)

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
        "plugin_internal_stage_count": len(plugin_internal_stages),
        "source_internal_stage_count": len(source_internal_stages),
        "plugin_internal_stages": plugin_internal_stages,
        "source_internal_stages": source_internal_stages,
        "checked_skill_relative_reference_count": reference_count,
        "required_skills": list(required_skills),
        "required_files": [path.as_posix() for path in required_files],
        "manifest_hook_path": None,
        "checked_hook_command_target_count": 0,
        "checked_hook_artifact_count": checked_hook_artifact_count,
        "runtime_package": runtime_package,
        "runtime_file_count": runtime_file_count,
        "runtime_byte_count": runtime_byte_count,
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
    parser.add_argument(
        "--runtime-package",
        action="store_true",
        help="Require a minimal runtime package with no development or historical-data directories.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required_skills = tuple(args.required_skills) if args.required_skills else DEFAULT_REQUIRED_SKILLS
    required_files = tuple(Path(item) for item in args.required_files) if args.required_files else DEFAULT_REQUIRED_FILES
    payload = check_distribution(
        Path(args.plugin_root),
        Path(args.source_root),
        required_skills,
        required_files,
        runtime_package=args.runtime_package,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"ok={str(payload['ok']).lower()} issue_count={payload['issue_count']}")
        for issue in payload["issues"]:
            print(f"- {issue['code']}: {issue['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
