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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_FILENAME = "uat_measurement.json"
METRICS_FILENAME = "uat_metrics.json"
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


def _first_pass_failure_classes(summary: dict[str, dict[str, Any]], required_gates: list[str]) -> list[str]:
    classes: list[str] = []
    for gate in required_gates:
        status = summary.get(gate, {})
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

    started_at = _now()
    before = _capture_git_status(run_dir, "git-before.txt")
    ledger = {
        "schema_version": 1,
        "run_id": args.run_id or run_dir.name,
        "route": args.route,
        "run_dir": str(run_dir),
        "started_at_utc": started_at,
        "token_usage_availability": args.token_usage_availability,
        "token_usage_evidence": args.token_usage_evidence or None,
        "git_before": before,
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
    event = {
        "gate": args.gate,
        "result": args.result,
        "recorded_at_utc": _now(),
        "failure_class": args.failure_class or None,
        "note": args.note or None,
        "artifact_path": str(Path(args.artifact).resolve()) if args.artifact else None,
    }
    ledger.setdefault("gate_events", []).append(event)
    _save_ledger(run_dir, ledger)
    result = _base_result(ledger)
    result.update({"ok": True, "gate_event": event, "gate_summary": _gate_summary(ledger)})
    return result, 0


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
    if _open_interval(ledger) is not None:
        measurement_issues.append("active_interval_open")
    if not git_unchanged:
        measurement_issues.append("git_capture_mismatch")
    first_pass_success = all(
        summary.get(gate, {}).get("first_result") == "passed"
        for gate in args.required_gate
    )
    repair_cycle_count = sum(int(status.get("failure_count", 0)) for status in summary.values())
    result = _base_result(ledger)
    result.update({
        "finished_at_utc": finished_at,
        "wall_elapsed_seconds": _seconds_between(str(ledger["started_at_utc"]), finished_at),
        "active_elapsed_seconds": _active_elapsed_seconds(ledger),
        "gate_summary": summary,
        "required_gates": args.required_gate,
        "first_pass_success": first_pass_success,
        "first_pass_failure_classes": _first_pass_failure_classes(summary, args.required_gate),
        "repair_cycle_count": repair_cycle_count,
        "git_unchanged": git_unchanged,
        "git_before": ledger.get("git_before"),
        "git_after": git_after,
        "measurement_issues": measurement_issues,
        "formal_uat_protocol_status": "passed" if not measurement_issues else "failed",
    })
    result["ok"] = result["formal_uat_protocol_status"] == "passed"
    _write_json(run_dir / METRICS_FILENAME, result)
    ledger["finalized_at_utc"] = finished_at
    ledger["final_metrics_path"] = str(run_dir / METRICS_FILENAME)
    _save_ledger(run_dir, ledger)
    return result, 0 if result["ok"] else 1


def _add_common_run_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-dir", required=True, help="Dedicated UAT directory under /tmp; never a repository directory.")


def _add_format(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("json", "text"), default="text")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a UAT measurement ledger and capture exact Git status bytes.")
    _add_common_run_dir(init)
    init.add_argument("--route", choices=ROUTES, required=True)
    init.add_argument("--run-id")
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
    record_gate.add_argument("--artifact", help="Optional saved JSON/log path emitted by the real gate command.")
    _add_format(record_gate)

    finalize = subparsers.add_parser("finalize", help="Capture final Git status and calculate UAT protocol metrics.")
    _add_common_run_dir(finalize)
    finalize.add_argument("--required-gate", action="append", default=[], required=True)
    _add_format(finalize)
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
