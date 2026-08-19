#!/usr/bin/env python3
"""Build the minimal Superleads runtime plugin package.

The source repository retains development assets and historical research under
``tmp/``. Codex and Claude runtime installs need only the Skill instructions,
their referenced scripts and rules.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from check_superleads_plugin_distribution import check_distribution

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist" / "superleads"
RUNTIME_DIRECTORIES = (".codex-plugin", "scripts", "shared", "skills", "spec")
RUNTIME_FILES = (Path(".claude-plugin/plugin.json"), Path("requirements.txt"))
EXCLUDED_DIRECTORY_NAMES = {"__pycache__", ".plugin-eval", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pyd"}


def _copy_tree(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"runtime source must not be a symlink: {source}")
    for item in sorted(source.iterdir(), key=lambda path: path.name):
        if item.is_dir():
            if item.name in EXCLUDED_DIRECTORY_NAMES:
                continue
            _copy_tree(item, destination / item.name)
            continue
        if item.is_symlink():
            raise ValueError(f"runtime source must not contain symlinked files: {item}")
        if item.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        target = destination / item.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def _clear_output(output: Path) -> None:
    if output == ROOT or output in ROOT.parents:
        raise ValueError(f"runtime output must not replace the source root: {output}")
    if output.is_symlink() or output.is_file():
        output.unlink()
    elif output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)


def _package_metrics(output: Path) -> tuple[int, int]:
    files = [path for path in output.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def build_package(output: Path) -> dict[str, Any]:
    output = output.resolve()
    _clear_output(output)

    for relative in RUNTIME_DIRECTORIES:
        source = ROOT / relative
        if not source.is_dir():
            raise ValueError(f"required runtime directory is missing: {relative}")
        _copy_tree(source, output / relative)
    for relative in RUNTIME_FILES:
        source = ROOT / relative
        if not source.is_file():
            raise ValueError(f"required runtime file is missing: {relative.as_posix()}")
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    result = check_distribution(output, ROOT, runtime_package=True)
    if not result["ok"]:
        messages = "; ".join(issue["code"] for issue in result["issues"])
        raise ValueError(f"built runtime package failed distribution validation: {messages}")
    file_count, byte_count = _package_metrics(output)
    return {
        "ok": True,
        "output": str(output),
        "file_count": file_count,
        "byte_count": byte_count,
        "included_directories": list(RUNTIME_DIRECTORIES),
        "included_files": [path.as_posix() for path in RUNTIME_FILES],
        "distribution": result,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = build_package(args.output)
    except (OSError, ValueError) as exc:
        payload = {"ok": False, "error": str(exc)}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload["ok"]:
        print(f"ok=true output={payload['output']} files={payload['file_count']} bytes={payload['byte_count']}")
    else:
        print(f"ok=false error={payload['error']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
