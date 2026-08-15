#!/usr/bin/env python3
"""Keep an exact, route-neutral measurement ledger for real Superleads UATs.

This script does not run research or substitute for route validators. It records
the execution evidence around those existing gates so a UAT result can separate
final delivery success, first-pass success, active work time, wall time, and
measurement failures such as a malformed Git snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_FILENAME = "uat_measurement.json"
METRICS_FILENAME = "uat_metrics.json"
RELEASE_IDENTITY_FILENAME = "release_identity.json"
EVIDENCE_MANIFEST_FILENAME = "evidence_manifest.json"
ARTIFACTS_DIRECTORY = "artifacts"
RUNTIME_PACKAGE_DIRECTORY = "runtime_package"
ROUTES = ("bulk_customer_development", "customer_background_research", "product_outbound_market_analysis")
GATE_RESULTS = ("passed", "failed", "skipped")
FAILURE_CLASSES = (
    "capability_adapter",
    "command_invocation",
    "graph_contract",
    "evidence_contract",
    "exporter_completeness",
    "measurement_protocol",
    "other",
)
TOKEN_USAGE_AVAILABILITY = ("available", "unavailable", "unknown")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _seconds_between(start: str, end: str) -> float:
    return round((_parse_timestamp(end) - _parse_timestamp(start)).total_seconds(), 3)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read measurement ledger: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"measurement ledger must be a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def _relative_to_run(run_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(run_dir.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"evidence path is outside the UAT run directory: {path}") from exc


def _within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _is_ephemeral_directory(path: Path) -> bool:
    return _within(path, Path(tempfile.gettempdir()))


def _directory_inventory(path: Path) -> list[dict[str, Any]]:
    if path.is_symlink():
        raise ValueError(f"evidence directory must not be a symlink: {path}")
    inventory: list[dict[str, Any]] = []
    for child in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        if child.is_symlink():
            raise ValueError(f"evidence directory must not contain a symlink: {child}")
        if child.is_dir():
            continue
        if not child.is_file():
            raise ValueError(f"evidence directory contains an unsupported entry: {child}")
        sha256, byte_count = _sha256_file(child)
        inventory.append({
            "relative_path": child.relative_to(path).as_posix(),
            "sha256": sha256,
            "byte_count": byte_count,
        })
    return inventory


def _directory_digest(inventory: list[dict[str, Any]]) -> str:
    content = json.dumps(inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(content)


def _artifact_descriptor(run_dir: Path, path: Path) -> dict[str, Any]:
    relative_path = _relative_to_run(run_dir, path)
    if path.is_symlink():
        raise ValueError(f"evidence artifact must not be a symlink: {path}")
    if path.is_file():
        sha256, byte_count = _sha256_file(path)
        return {
            "relative_path": relative_path,
            "kind": "file",
            "sha256": sha256,
            "byte_count": byte_count,
            "files": [],
        }
    if path.is_dir():
        files = _directory_inventory(path)
        return {
            "relative_path": relative_path,
            "kind": "directory",
            "sha256": _directory_digest(files),
            "byte_count": sum(int(item["byte_count"]) for item in files),
            "files": files,
        }
    raise ValueError(f"evidence artifact must be a readable file or directory: {path}")


def _staged_artifact_path(run_dir: Path, gate: str, attempt: int, source: Path) -> Path:
    safe_gate = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in gate).strip("-") or "gate"
    safe_name = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in source.name).strip("-") or "artifact"
    return run_dir / ARTIFACTS_DIRECTORY / f"{attempt:03d}-{safe_gate}-{safe_name}"


def _stage_artifact(run_dir: Path, gate: str, attempt: int, source: Path) -> dict[str, Any]:
    source = source.resolve()
    artifacts_dir = (run_dir / ARTIFACTS_DIRECTORY).resolve()
    if not source.exists() or source.is_symlink():
        raise ValueError(f"evidence artifact is missing or a symlink: {source}")
    if source == run_dir.resolve() or _within(source, artifacts_dir):
        raise ValueError(f"refusing to stage the UAT directory or an existing staged artifact: {source}")
    destination = _staged_artifact_path(run_dir, gate, attempt, source)
    if destination.exists():
        raise ValueError(f"staged evidence destination already exists: {destination}")
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    elif source.is_dir():
        _directory_inventory(source)
        shutil.copytree(source, destination, symlinks=False)
    else:
        raise ValueError(f"evidence artifact must be a regular file or directory: {source}")
    return _artifact_descriptor(run_dir, destination)


def _git_head() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.decode("utf-8", errors="replace").strip()
    return value or None


def _capture_release_identity(run_dir: Path, manifest: Path, runtime_package: Path | None) -> dict[str, Any]:
    manifest = manifest.resolve()
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError(f"plugin manifest must be a readable regular file: {manifest}")
    try:
        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"plugin manifest is not readable JSON: {manifest}") from exc
    name = manifest_payload.get("name") if isinstance(manifest_payload, dict) else None
    version = manifest_payload.get("version") if isinstance(manifest_payload, dict) else None
    if not isinstance(name, str) or not name or not isinstance(version, str) or not version:
        raise ValueError("plugin manifest must contain non-empty string name and version")

    staged_manifest = run_dir / "plugin_manifest.json"
    shutil.copy2(manifest, staged_manifest)
    manifest_sha256, manifest_bytes = _sha256_file(staged_manifest)
    runtime_descriptor: dict[str, Any] | None = None
    if runtime_package is not None:
        runtime_package = runtime_package.resolve()
        if not runtime_package.is_dir() or runtime_package.is_symlink():
            raise ValueError(f"runtime package must be a readable regular directory: {runtime_package}")
        _directory_inventory(runtime_package)
        staged_runtime_package = run_dir / RUNTIME_PACKAGE_DIRECTORY
        shutil.copytree(runtime_package, staged_runtime_package, symlinks=False)
        runtime_descriptor = _artifact_descriptor(run_dir, staged_runtime_package)

    identity = {
        "schema_version": 1,
        "plugin_name": name,
        "plugin_version": version,
        "plugin_manifest": {
            "relative_path": staged_manifest.name,
            "sha256": manifest_sha256,
            "byte_count": manifest_bytes,
        },
        "git_head": _git_head(),
        "runtime_package": runtime_descriptor,
    }
    identity_path = run_dir / RELEASE_IDENTITY_FILENAME
    _write_json(identity_path, identity)
    identity["relative_path"] = RELEASE_IDENTITY_FILENAME
    identity["sha256"] = _sha256_file(identity_path)[0]
    return identity


def _ledger_path(run_dir: Path) -> Path:
    return run_dir / LEDGER_FILENAME


def _load_ledger(run_dir: Path) -> dict[str, Any]:
    return _read_json(_ledger_path(run_dir))


def _save_ledger(run_dir: Path, ledger: dict[str, Any]) -> None:
    _write_json(_ledger_path(run_dir), ledger)


def _git_status_bytes() -> bytes:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git status failed: {message or result.returncode}")
    return result.stdout


def _capture_git_status(run_dir: Path, name: str) -> dict[str, Any]:
    content = _git_status_bytes()
    path = run_dir / name
    path.write_bytes(content)
    return {
        "path": str(path),
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _open_interval(ledger: dict[str, Any]) -> dict[str, Any] | None:
    for interval in reversed(ledger.get("active_intervals", [])):
        if isinstance(interval, dict) and not interval.get("ended_at_utc"):
            return interval
    return None


def _gate_summary(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for event in ledger.get("gate_events", []):
        if not isinstance(event, dict):
            continue
        gate = event.get("gate")
        if not isinstance(gate, str):
            continue
        current = summary.setdefault(gate, {"attempt_count": 0})
        current["attempt_count"] += 1
        current.setdefault("first_result", event.get("result"))
        current["final_result"] = event.get("result")
        if event.get("result") == "failed":
            current["failure_count"] = int(current.get("failure_count", 0)) + 1
            if "first_failure_class" not in current:
                current["first_failure_class"] = event.get("failure_class")
    return summary


def _required_gate_issues(summary: dict[str, dict[str, Any]], required_gates: list[str]) -> list[str]:
    issues: list[str] = []
    for gate in required_gates:
        status = summary.get(gate)
        if status is None:
            issues.append(f"required_gate_missing:{gate}")
        elif status.get("final_result") != "passed":
            issues.append(f"required_gate_not_passed:{gate}")
    return issues


def _required_gate_artifact_issues(ledger: dict[str, Any], required_gates: list[str]) -> list[str]:
    issues: list[str] = []
    events = ledger.get("gate_events", [])
    for gate in required_gates:
        final_event: dict[str, Any] | None = None
        for event in reversed(events):
            if isinstance(event, dict) and event.get("gate") == gate:
                final_event = event
                break
        if final_event is not None and final_event.get("result") == "passed" and not final_event.get("artifacts"):
            issues.append(f"required_gate_artifact_missing:{gate}")
    return issues


def _safe_evidence_path(run_dir: Path, relative_path: Any) -> tuple[Path | None, str]:
    if not isinstance(relative_path, str) or not relative_path or Path(relative_path).is_absolute():
        return None, str(relative_path)
    candidate = run_dir / relative_path
    if not _within(candidate, run_dir):
        return None, relative_path
    return candidate, relative_path


def _artifact_verification_issue(run_dir: Path, descriptor: Any) -> str | None:
    if not isinstance(descriptor, dict):
        return "evidence_artifact_path_not_relative:<missing>"
    path, relative_path = _safe_evidence_path(run_dir, descriptor.get("relative_path"))
    if path is None:
        return f"evidence_artifact_path_not_relative:{relative_path}"
    if not path.exists() or path.is_symlink():
        return f"evidence_artifact_missing:{relative_path}"
    try:
        actual = _artifact_descriptor(run_dir, path)
    except ValueError:
        return f"evidence_artifact_hash_mismatch:{relative_path}"
    expected = {
        "kind": descriptor.get("kind"),
        "sha256": descriptor.get("sha256"),
        "byte_count": descriptor.get("byte_count"),
        "files": descriptor.get("files", []),
    }
    observed = {
        "kind": actual["kind"],
        "sha256": actual["sha256"],
        "byte_count": actual["byte_count"],
        "files": actual["files"],
    }
    if observed != expected:
        return f"evidence_artifact_hash_mismatch:{relative_path}"
    return None


def _manifest_artifacts(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for event in ledger.get("gate_events", []):
        if not isinstance(event, dict):
            continue
        for descriptor in event.get("artifacts", []):
            if not isinstance(descriptor, dict):
                continue
            artifacts.append({
                "gate": event.get("gate"),
                "attempt": event.get("attempt"),
                **descriptor,
            })
    return artifacts


def _evidence_manifest(ledger: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    identity_path = run_dir / RELEASE_IDENTITY_FILENAME
    identity_sha256 = _sha256_file(identity_path)[0] if identity_path.is_file() else None
    return {
        "schema_version": 1,
        "run_id": ledger.get("run_id"),
        "release_identity": {
            "relative_path": RELEASE_IDENTITY_FILENAME,
            "sha256": identity_sha256,
        },
        "artifacts": _manifest_artifacts(ledger),
    }


def _verify_release_identity(run_dir: Path) -> list[str]:
    issues: list[str] = []
    identity_path = run_dir / RELEASE_IDENTITY_FILENAME
    if not identity_path.is_file() or identity_path.is_symlink():
        return ["release_identity_missing"]
    try:
        identity = _read_json(identity_path)
    except ValueError:
        return ["release_identity_manifest_invalid"]
    if not isinstance(identity.get("plugin_name"), str) or not isinstance(identity.get("plugin_version"), str):
        issues.append("release_identity_manifest_invalid")
    manifest = identity.get("plugin_manifest")
    manifest_path, _ = _safe_evidence_path(run_dir, manifest.get("relative_path") if isinstance(manifest, dict) else None)
    if manifest_path is None or not manifest_path.is_file() or manifest_path.is_symlink() or not isinstance(manifest, dict):
        issues.append("release_identity_manifest_invalid")
    else:
        manifest_sha256, manifest_bytes = _sha256_file(manifest_path)
        if manifest.get("sha256") != manifest_sha256 or manifest.get("byte_count") != manifest_bytes:
            issues.append("release_identity_manifest_invalid")
    runtime_package = identity.get("runtime_package")
    if not isinstance(runtime_package, dict):
        issues.append("release_identity_runtime_package_missing")
    else:
        runtime_issue = _artifact_verification_issue(run_dir, runtime_package)
        if runtime_issue is not None:
            issues.append("release_identity_runtime_package_missing")
    return issues


def _verify_evidence(run_dir: Path, ledger: dict[str, Any]) -> list[str]:
    issues = _verify_release_identity(run_dir)
    for descriptor in _manifest_artifacts(ledger):
        issue = _artifact_verification_issue(run_dir, descriptor)
        if issue is not None and issue not in issues:
            issues.append(issue)
    manifest_path = run_dir / EVIDENCE_MANIFEST_FILENAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        issues.append("evidence_manifest_missing")
    else:
        try:
            manifest = _read_json(manifest_path)
        except ValueError:
            issues.append("evidence_manifest_invalid")
        else:
            expected = _evidence_manifest(ledger, run_dir)
            if manifest != expected:
                issues.append("evidence_manifest_invalid")
    return issues


def _first_pass_failure_classes(summary: dict[str, dict[str, Any]]) -> list[str]:
    classes: list[str] = []
    for status in summary.values():
        if status.get("first_result") != "failed":
            continue
        failure_class = status.get("first_failure_class")
        if isinstance(failure_class, str) and failure_class not in classes:
            classes.append(failure_class)
    return classes


def _active_elapsed_seconds(ledger: dict[str, Any]) -> float:
    total = 0.0
    for interval in ledger.get("active_intervals", []):
        if not isinstance(interval, dict):
            continue
        started = interval.get("started_at_utc")
        ended = interval.get("ended_at_utc")
        if isinstance(started, str) and isinstance(ended, str):
            total += _seconds_between(started, ended)
    return round(total, 3)


def _base_result(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": ledger.get("schema_version"),
        "run_id": ledger.get("run_id"),
        "route": ledger.get("route"),
        "run_dir": ledger.get("run_dir"),
        "started_at_utc": ledger.get("started_at_utc"),
        "token_usage_availability": ledger.get("token_usage_availability"),
        "token_usage_evidence": ledger.get("token_usage_evidence"),
        "release_identity": ledger.get("release_identity"),
    }


def command_init(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = _ledger_path(run_dir)
    if ledger_path.exists() and not args.overwrite:
        raise ValueError(f"measurement ledger already exists: {ledger_path}; pass --overwrite only before recording gates")
    if ledger_path.exists() and args.overwrite:
        existing = _read_json(ledger_path)
        if existing.get("gate_events") or existing.get("active_intervals"):
            raise ValueError("refusing to overwrite a measurement ledger that already contains events")

    (run_dir / ARTIFACTS_DIRECTORY).mkdir(exist_ok=True)
    release_identity = _capture_release_identity(run_dir, args.plugin_manifest, args.runtime_package)
    started_at = _now()
    before = _capture_git_status(run_dir, "git-before.txt")
    ledger = {
        "schema_version": 2,
        "run_id": args.run_id or run_dir.name,
        "route": args.route,
        "run_dir": str(run_dir),
        "started_at_utc": started_at,
        "token_usage_availability": args.token_usage_availability,
        "token_usage_evidence": args.token_usage_evidence or None,
        "git_before": before,
        "release_identity": release_identity,
        "active_intervals": [],
        "gate_events": [],
    }
    _save_ledger(run_dir, ledger)
    result = _base_result(ledger)
    result.update({"ok": True, "measurement_ledger": str(ledger_path), "git_before": before})
    return result, 0


def command_active_start(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_dir = Path(args.run_dir).resolve()
    ledger = _load_ledger(run_dir)
    if _open_interval(ledger) is not None:
        raise ValueError("an active interval is already open; stop it before starting another")
    interval = {"started_at_utc": _now(), "start_note": args.note or None}
    ledger.setdefault("active_intervals", []).append(interval)
    _save_ledger(run_dir, ledger)
    result = _base_result(ledger)
    result.update({"ok": True, "active_interval": interval})
    return result, 0


def command_active_stop(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_dir = Path(args.run_dir).resolve()
    ledger = _load_ledger(run_dir)
    interval = _open_interval(ledger)
    if interval is None:
        raise ValueError("there is no active interval to stop")
    interval["ended_at_utc"] = _now()
    interval["end_note"] = args.note or None
    interval["elapsed_seconds"] = _seconds_between(str(interval["started_at_utc"]), str(interval["ended_at_utc"]))
    _save_ledger(run_dir, ledger)
    result = _base_result(ledger)
    result.update({"ok": True, "active_interval": interval, "active_elapsed_seconds": _active_elapsed_seconds(ledger)})
    return result, 0


def command_record_gate(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_dir = Path(args.run_dir).resolve()
    ledger = _load_ledger(run_dir)
    if args.result == "failed" and not args.failure_class:
        raise ValueError("--failure-class is required when --result failed")
    if args.result != "failed" and args.failure_class:
        raise ValueError("--failure-class is only valid when --result failed")
    attempt = 1 + sum(1 for event in ledger.get("gate_events", []) if isinstance(event, dict) and event.get("gate") == args.gate)
    artifacts = [
        _stage_artifact(run_dir, args.gate, attempt, Path(source))
        for source in args.artifact
    ]
    event = {
        "gate": args.gate,
        "attempt": attempt,
        "result": args.result,
        "recorded_at_utc": _now(),
        "failure_class": args.failure_class or None,
        "note": args.note or None,
        "artifacts": artifacts,
    }
    ledger.setdefault("gate_events", []).append(event)
    _save_ledger(run_dir, ledger)
    result = _base_result(ledger)
    result.update({"ok": True, "gate_event": event, "gate_summary": _gate_summary(ledger)})
    return result, 0


def command_verify(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_dir = Path(args.run_dir).resolve()
    ledger = _load_ledger(run_dir)
    verification_issues = _verify_evidence(run_dir, ledger)
    result = _base_result(ledger)
    result.update({
        "evidence_manifest": EVIDENCE_MANIFEST_FILENAME,
        "verification_issues": verification_issues,
        "ok": not verification_issues,
    })
    return result, 0 if result["ok"] else 1


def command_finalize(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_dir = Path(args.run_dir).resolve()
    ledger = _load_ledger(run_dir)
    finished_at = _now()
    git_after = _capture_git_status(run_dir, "git-after.txt")
    before = (run_dir / "git-before.txt").read_bytes()
    after = (run_dir / "git-after.txt").read_bytes()
    git_unchanged = before == after
    summary = _gate_summary(ledger)
    measurement_issues = _required_gate_issues(summary, args.required_gate)
    measurement_issues.extend(_required_gate_artifact_issues(ledger, args.required_gate))
    if _open_interval(ledger) is not None:
        measurement_issues.append("active_interval_open")
    if not git_unchanged:
        measurement_issues.append("git_capture_mismatch")
    if _is_ephemeral_directory(run_dir):
        measurement_issues.append("evidence_run_dir_ephemeral")
    _write_json(run_dir / EVIDENCE_MANIFEST_FILENAME, _evidence_manifest(ledger, run_dir))
    measurement_issues.extend(issue for issue in _verify_evidence(run_dir, ledger) if issue not in measurement_issues)
    required_gates_first_passed = all(
        summary.get(gate, {}).get("first_result") == "passed"
        for gate in args.required_gate
    )
    # A caller may record an intermediate compiler or source-plan gate that
    # was not listed as a delivery requirement. It still means the end-to-end
    # UAT did not pass on its first attempt and must not be reported as such.
    recorded_gates_first_passed = all(
        status.get("first_result") == "passed"
        for status in summary.values()
    )
    first_pass_success = required_gates_first_passed and recorded_gates_first_passed
    repair_cycle_count = sum(int(status.get("failure_count", 0)) for status in summary.values())
    portable_failure_prefixes = (
        "evidence_run_dir_ephemeral",
        "release_identity_",
        "evidence_artifact_",
        "evidence_manifest_",
        "required_gate_artifact_missing:",
    )
    result = _base_result(ledger)
    result.update({
        "finished_at_utc": finished_at,
        "wall_elapsed_seconds": _seconds_between(str(ledger["started_at_utc"]), finished_at),
        "active_elapsed_seconds": _active_elapsed_seconds(ledger),
        "gate_summary": summary,
        "required_gates": args.required_gate,
        "first_pass_success": first_pass_success,
        "first_pass_failure_classes": _first_pass_failure_classes(summary),
        "repair_cycle_count": repair_cycle_count,
        "git_unchanged": git_unchanged,
        "git_before": ledger.get("git_before"),
        "git_after": git_after,
        "measurement_issues": measurement_issues,
        "evidence_manifest": EVIDENCE_MANIFEST_FILENAME,
        "portable_evidence": not any(issue.startswith(portable_failure_prefixes) for issue in measurement_issues),
        "formal_uat_protocol_status": "passed" if not measurement_issues else "failed",
    })
    result["ok"] = result["formal_uat_protocol_status"] == "passed"
    _write_json(run_dir / METRICS_FILENAME, result)
    ledger["finalized_at_utc"] = finished_at
    ledger["final_metrics_path"] = str(run_dir / METRICS_FILENAME)
    _save_ledger(run_dir, ledger)
    return result, 0 if result["ok"] else 1


def _add_common_run_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-dir", required=True, help="Dedicated UAT evidence directory. Formal success requires a non-temporary location.")


def _add_format(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("json", "text"), default="text")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a UAT measurement ledger and capture exact Git status bytes.")
    _add_common_run_dir(init)
    init.add_argument("--route", choices=ROUTES, required=True)
    init.add_argument("--run-id")
    init.add_argument("--plugin-manifest", type=Path, default=ROOT / ".codex-plugin" / "plugin.json")
    init.add_argument("--runtime-package", type=Path)
    init.add_argument("--token-usage-availability", choices=TOKEN_USAGE_AVAILABILITY, default="unknown")
    init.add_argument("--token-usage-evidence")
    init.add_argument("--overwrite", action="store_true")
    _add_format(init)

    active_start = subparsers.add_parser("active-start", help="Open an agent-active work interval.")
    _add_common_run_dir(active_start)
    active_start.add_argument("--note")
    _add_format(active_start)

    active_stop = subparsers.add_parser("active-stop", help="Close the active work interval.")
    _add_common_run_dir(active_stop)
    active_stop.add_argument("--note")
    _add_format(active_stop)

    record_gate = subparsers.add_parser("record-gate", help="Record one gate attempt without replacing its existing validator.")
    _add_common_run_dir(record_gate)
    record_gate.add_argument("--gate", required=True)
    record_gate.add_argument("--result", choices=GATE_RESULTS, required=True)
    record_gate.add_argument("--failure-class", choices=FAILURE_CLASSES)
    record_gate.add_argument("--note")
    record_gate.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="File or directory to snapshot into the UAT evidence bundle; repeat for multiple artifacts.",
    )
    _add_format(record_gate)

    finalize = subparsers.add_parser("finalize", help="Capture final Git status and calculate UAT protocol metrics.")
    _add_common_run_dir(finalize)
    finalize.add_argument("--required-gate", action="append", default=[], required=True)
    _add_format(finalize)

    verify = subparsers.add_parser("verify", help="Recompute the hashes in a sealed UAT evidence directory.")
    _add_common_run_dir(verify)
    _add_format(verify)
    return parser.parse_args()


def _render_text(result: dict[str, Any]) -> str:
    lines = [
        f"ok={result.get('ok')}",
        f"route={result.get('route')}",
        f"formal_uat_protocol_status={result.get('formal_uat_protocol_status', 'not_finalized')}",
        f"first_pass_success={result.get('first_pass_success', 'not_finalized')}",
        f"active_elapsed_seconds={result.get('active_elapsed_seconds', 'not_finalized')}",
        f"wall_elapsed_seconds={result.get('wall_elapsed_seconds', 'not_finalized')}",
    ]
    if result.get("measurement_issues"):
        lines.append("measurement_issues=" + ",".join(result["measurement_issues"]))
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        command = {
            "init": command_init,
            "active-start": command_active_start,
            "active-stop": command_active_stop,
            "record-gate": command_record_gate,
            "finalize": command_finalize,
            "verify": command_verify,
        }[args.command]
        result, status = command(args)
    except (ValueError, RuntimeError) as exc:
        result = {"ok": False, "error": str(exc)}
        status = 2
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_render_text(result))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
