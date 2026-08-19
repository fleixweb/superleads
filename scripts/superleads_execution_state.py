#!/usr/bin/env python3
"""Bounded, serializable execution state for Superleads research runs.

This module does not perform research.  It records the work a host actually
performed so a later stage can reuse an opened source, report a bounded phase,
or resume unfinished query groups without presenting historical material as a
current observation.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


HISTORICAL_REFERENCE_LABEL = "历史参考，需重新核验"
PHASES = ("intake", "breadth_search", "source_verification", "supplement", "serial_decision", "completed")
QUERY_GROUP_STATUSES = ("not_executed", "in_progress", "completed", "source_restricted", "budget_exhausted")
MILESTONE_METRICS = {
    "first_confirmation_response_seconds",
    "first_query_plan_seconds",
    "first_candidate_seconds",
    "first_opened_source_seconds",
    "first_evidence_fact_seconds",
    "formal_report_complete_seconds",
}
MAX_EXPANSION_SCALE = 500


def normalize_run_url(url: str) -> str:
    """Return the stable same-Run key for a successfully opened HTTP URL.

    Canonicalize query ordering. Ordinary anchors identify a position within
    the same document and are removed; hash-routes (``#/...`` or ``#!/...``)
    remain because they can select distinct browser-rendered content.
    """
    parsed = urlsplit(str(url).strip())
    scheme = parsed.scheme.casefold()
    hostname = (parsed.hostname or "").casefold()
    if scheme not in {"http", "https"} or not hostname:
        raise ValueError("source URL must be an absolute HTTP(S) URL")
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/")
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)), doseq=True)
    fragment = parsed.fragment if parsed.fragment.startswith(("/", "!/")) else ""
    return urlunsplit((scheme, hostname + port, path, query, fragment))


def _metrics() -> dict[str, Any]:
    return {
        "opened_source_count": 0,
        "cache_hit_count": 0,
        "search_success_count": 0,
        "search_failure_count": 0,
        "source_open_success_count": 0,
        "source_restricted_count": 0,
        "duplicate_url_count": 0,
        "unconfirmed_or_conflict_count": 0,
        "guessed_contact_violation_count": 0,
        "first_confirmation_response_seconds": None,
        "first_query_plan_seconds": None,
        "first_candidate_seconds": None,
        "first_opened_source_seconds": None,
        "first_evidence_fact_seconds": None,
        "formal_report_complete_seconds": None,
        "phase_elapsed_seconds": {},
        "phase_active_elapsed_seconds": {},
    }


def _query_group(group: dict[str, Any]) -> dict[str, Any]:
    group_id = str(group.get("group_id") or group.get("query_purpose") or "").strip()
    if not group_id:
        raise ValueError("query group needs group_id or query_purpose")
    execution_order = str(group.get("execution_order") or "independent")
    if execution_order not in {"independent", "serial"}:
        raise ValueError("query group execution_order must be independent or serial")
    status = str(group.get("status") or "not_executed")
    if status not in QUERY_GROUP_STATUSES:
        raise ValueError("query group status must be a supported execution status")
    candidate_limit = group.get("candidate_limit")
    if candidate_limit is not None:
        candidate_limit = _positive_budget_value(candidate_limit, field="candidate_limit", default=1)
    normalized = {
        "group_id": group_id,
        "execution_order": execution_order,
        "status": status,
        "candidate_limit": candidate_limit,
        "candidate_ids": list(group.get("candidate_ids") or []),
        "notes": list(group.get("notes") or []),
    }
    if "search_combination" in group:
        combination = group.get("search_combination")
        if not isinstance(combination, dict):
            raise ValueError("search_combination must be an object when provided")
        normalized_combination: dict[str, str | None] = {}
        for field in ("product_term", "market", "customer_type"):
            value = combination.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"search_combination.{field} must be a string or null")
            normalized_combination[field] = value.strip() if isinstance(value, str) and value.strip() else None
        normalized["search_combination"] = normalized_combination
    return normalized


def _uncovered_combination_hints(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError("uncovered_combination_hints must be a list of non-empty strings")
    return list(value)


def _positive_budget_value(value: Any, *, field: str, default: int) -> int:
    """Keep execution state finite even when a plan omitted optional budget fields."""
    resolved = default if value is None else value
    if isinstance(resolved, bool) or not isinstance(resolved, int) or resolved < 1:
        raise ValueError(f"{field} must be a positive integer")
    return resolved


def _append_incomplete_work(state: dict[str, Any], work: str) -> None:
    incomplete = state.setdefault("incomplete_work", [])
    if work not in incomplete:
        incomplete.append(work)


def create_execution_state(
    run_id: str,
    *,
    query_groups: list[dict[str, Any]],
    budget: dict[str, Any],
    task_mode: str = "discovery_snapshot",
    host_supports_parallel_execution: bool = False,
    route: str | None = None,
    uncovered_combination_hints: list[str] | None = None,
) -> dict[str, Any]:
    """Create a run-local execution record with explicit finite limits."""
    normalized_run_id = str(run_id).strip()
    if not normalized_run_id:
        raise ValueError("run_id must be non-empty")
    if task_mode not in {"discovery_snapshot", "formal_research"}:
        raise ValueError("execution state is only for research task modes")
    groups = [_query_group(group) for group in query_groups]
    ids = [group["group_id"] for group in groups]
    if len(ids) != len(set(ids)):
        raise ValueError("query group IDs must be unique within one Run")
    query_group_limit = _positive_budget_value(
        budget.get("query_group_limit"),
        field="query_group_limit",
        default=max(1, len(groups)),
    )
    if len(groups) > query_group_limit:
        raise ValueError("query groups exceed query_group_limit")
    default_candidate_limit = 10 if task_mode == "discovery_snapshot" else 5
    max_candidates_per_group = _positive_budget_value(
        budget.get("max_candidates_per_group"),
        field="max_candidates_per_group",
        default=default_candidate_limit,
    )
    max_candidates_per_run = budget.get("max_candidates_per_run")
    if max_candidates_per_run is None and task_mode == "discovery_snapshot":
        max_candidates_per_run = default_candidate_limit
    elif max_candidates_per_run is not None:
        max_candidates_per_run = _positive_budget_value(
            max_candidates_per_run,
            field="max_candidates_per_run",
            default=default_candidate_limit,
        )
    max_core_opens_per_candidate = _positive_budget_value(
        budget.get("max_core_opens_per_candidate"),
        field="max_core_opens_per_candidate",
        default=2,
    )
    stop_conditions = budget.get("stop_conditions") or []
    if not isinstance(stop_conditions, list) or any(not isinstance(item, str) or not item.strip() for item in stop_conditions):
        raise ValueError("stop_conditions must be a list of non-empty strings")
    return {
        "run_id": normalized_run_id,
        "route": str(route or "unknown"),
        "task_mode": task_mode,
        "phase": "intake",
        "phase_history": ["intake"],
        "host_supports_parallel_execution": bool(host_supports_parallel_execution),
        "capabilities": None,
        "budget": {
            "query_group_limit": query_group_limit,
            "max_candidates_per_group": max_candidates_per_group,
            "max_candidates_per_run": max_candidates_per_run,
            "max_core_opens_per_candidate": max_core_opens_per_candidate,
            "include_contacts": bool(budget.get("include_contacts", False)),
            "include_trade_records": bool(budget.get("include_trade_records", False)),
            "include_historical_references": bool(budget.get("include_historical_references", False)),
            "stop_conditions": list(stop_conditions),
        },
        "query_groups": groups,
        "expansion_scale_chosen": None,
        "uncovered_combination_hints": _uncovered_combination_hints(uncovered_combination_hints),
        "source_cache": {},
        "brief": None,
        "search_log_ids": [],
        "candidate_ids": [],
        "current_observations": [],
        "completed_work": [],
        "incomplete_work": [],
        "historical_references": [],
        "recovery_count": 0,
        "metrics": _metrics(),
    }


def create_execution_state_from_plan(
    run_id: str,
    *,
    plan: dict[str, Any],
    route: str,
    task_mode: str = "discovery_snapshot",
    host_supports_parallel_execution: bool = False,
) -> dict[str, Any]:
    """Create the same finite state contract for any Superleads research route.

    The host supplies the Run ID and route. This helper only converts an
    already-scoped plan into bounded state; it does not search, open sources,
    or imply that every route has a background executor.
    """
    if not isinstance(plan, dict):
        raise ValueError("plan must be an object")
    raw_groups = plan.get("query_groups")
    if not isinstance(raw_groups, list):
        raw_groups = []
        for step in plan.get("query_plan") or []:
            if not isinstance(step, dict):
                continue
            group_id = step.get("query_group_id") or step.get("query_plan_id")
            if group_id:
                raw_groups.append({
                    "group_id": group_id,
                    "execution_order": step.get("execution_order") or "independent",
                })

    budget_source = plan.get("execution_budget")
    if not isinstance(budget_source, dict):
        budget_source = {}
    stop_conditions = budget_source.get("stop_conditions") or plan.get("stop_conditions") or []
    if not stop_conditions:
        stop_conditions = [
            str(budget_source.get("coverage_completion_condition") or "all planned groups are completed, restricted, or budget-exhausted"),
            str(budget_source.get("low_increment_stop_condition") or "stop when the remaining coverage gap is explicit and new sources add no material evidence"),
        ]
    return create_execution_state(
        run_id,
        query_groups=[item for item in raw_groups if isinstance(item, dict)],
        budget={
            "query_group_limit": budget_source.get("query_group_limit") or max(1, len(raw_groups)),
            "max_candidates_per_group": budget_source.get("max_candidates_per_group") or (10 if task_mode == "discovery_snapshot" else 5),
            "max_candidates_per_run": budget_source.get("max_candidates_per_run") if "max_candidates_per_run" in budget_source else (10 if task_mode == "discovery_snapshot" else None),
            "max_core_opens_per_candidate": budget_source.get("max_core_opens_per_candidate") or 2,
            "include_contacts": bool(budget_source.get("include_contacts", False)),
            "include_trade_records": bool(budget_source.get("include_trade_records", False)),
            "include_historical_references": bool(budget_source.get("include_historical_references", False)),
            "stop_conditions": stop_conditions,
        },
        task_mode=task_mode,
        host_supports_parallel_execution=host_supports_parallel_execution,
        route=route,
        uncovered_combination_hints=plan.get("uncovered_combination_hints"),
    )


def begin_phase(state: dict[str, Any], phase: str) -> None:
    """Record a real stage transition without asserting concurrent execution."""
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase}")
    state["phase"] = phase
    history = state.setdefault("phase_history", [])
    if not history or history[-1] != phase:
        history.append(phase)


def record_milestone(
    state: dict[str, Any],
    metric: str,
    elapsed_seconds: float,
    *,
    phase: str,
    active_elapsed_seconds: float | None = None,
) -> None:
    """Store host-reported elapsed values without creating timers or telemetry."""
    if metric not in MILESTONE_METRICS:
        raise ValueError(f"unknown milestone metric: {metric}")
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase}")
    if elapsed_seconds < 0:
        raise ValueError("elapsed_seconds must not be negative")
    if active_elapsed_seconds is not None and active_elapsed_seconds < 0:
        raise ValueError("active_elapsed_seconds must not be negative")
    metrics = state.setdefault("metrics", _metrics())
    existing = metrics.get(metric)
    if existing is None or float(elapsed_seconds) < float(existing):
        metrics[metric] = float(elapsed_seconds)
    phase_elapsed = metrics.setdefault("phase_elapsed_seconds", {})
    phase_elapsed[phase] = float(elapsed_seconds)
    if active_elapsed_seconds is not None:
        phase_active = metrics.setdefault("phase_active_elapsed_seconds", {})
        phase_active[phase] = float(active_elapsed_seconds)


def cache_capabilities(state: dict[str, Any], probe: Callable[[], dict[str, str]]) -> dict[str, str]:
    """Call a host capability probe once for the current Run only."""
    cached = state.get("capabilities")
    if isinstance(cached, dict):
        return dict(cached)
    result = probe()
    if not isinstance(result, dict):
        raise ValueError("capability probe must return a mapping")
    state["capabilities"] = dict(result)
    return dict(result)


def record_candidate(state: dict[str, Any], *, query_group_id: str, candidate_id: str) -> dict[str, Any]:
    """Record a discovered candidate until its query-group budget is consumed."""
    group = next(
        (item for item in state.get("query_groups", []) if item.get("group_id") == query_group_id),
        None,
    )
    if not isinstance(group, dict):
        raise ValueError("candidate must be associated with an existing query group")
    identifier = str(candidate_id).strip()
    if not identifier:
        raise ValueError("candidate_id must be non-empty")
    candidate_ids = group.setdefault("candidate_ids", [])
    all_candidates = state.setdefault("candidate_ids", [])
    if identifier in candidate_ids or identifier in all_candidates:
        return {"recorded": False, "reason": "already_recorded"}
    limit = group.get("candidate_limit") or state.get("budget", {}).get("max_candidates_per_group")
    if len(candidate_ids) >= int(limit):
        _append_incomplete_work(state, "candidate limit reached")
        return {"recorded": False, "reason": "budget_exhausted"}
    run_limit = state.get("budget", {}).get("max_candidates_per_run")
    if run_limit is not None and len(all_candidates) >= int(run_limit):
        _append_incomplete_work(state, "candidate pool limit reached")
        return {"recorded": False, "reason": "budget_exhausted"}
    candidate_ids.append(identifier)
    all_candidates.append(identifier)
    return {"recorded": True, "reason": None}


def record_expansion_scale_choice(state: dict[str, Any], scale: int) -> dict[str, Any]:
    """Record the user's one-time candidate-pool expansion choice for this Run."""
    if state.get("task_mode") != "discovery_snapshot":
        raise ValueError("expansion choice is only available for discovery snapshots")
    if isinstance(scale, bool) or not isinstance(scale, int) or not 1 <= scale <= MAX_EXPANSION_SCALE:
        raise ValueError(f"expansion scale must be an integer between 1 and {MAX_EXPANSION_SCALE}")
    if state.get("expansion_scale_chosen") is not None:
        return {"recorded": False, "reason": "already_chosen"}
    state["expansion_scale_chosen"] = scale
    return {"recorded": True, "reason": None}


def add_opened_source(
    state: dict[str, Any],
    *,
    query_group_id: str,
    url: str,
    content_hash: str,
    observed_at: str,
    source_subject: str,
    fact_domain: str,
) -> dict[str, Any]:
    """Record one current opened source or reuse its same-Run cache entry."""
    group_ids = {group.get("group_id") for group in state.get("query_groups", [])}
    if query_group_id not in group_ids:
        raise ValueError("source must be associated with an existing query group")
    normalized_url = normalize_run_url(url)
    normalized_content_hash = str(content_hash).strip()
    normalized_observed_at = str(observed_at).strip()
    normalized_subject = str(source_subject).strip()
    normalized_fact_domain = str(fact_domain).strip()
    if not all((normalized_content_hash, normalized_observed_at, normalized_subject, normalized_fact_domain)):
        raise ValueError("opened source requires non-empty hash, observation time, subject, and fact domain")
    cache = state.setdefault("source_cache", {})
    metrics = state.setdefault("metrics", _metrics())
    entry = cache.get(normalized_url)
    if isinstance(entry, dict):
        if str(entry.get("source_subject") or "").casefold() != normalized_subject.casefold():
            metrics["unconfirmed_or_conflict_count"] = int(metrics.get("unconfirmed_or_conflict_count", 0)) + 1
            _append_incomplete_work(state, "source subject conflict requires identity verification")
            return {
                "opened": False,
                "reason": "source_subject_conflict",
                "cache_key": normalized_url,
                "entry": deepcopy(entry),
            }
        entry["query_group_ids"] = sorted(set(entry.get("query_group_ids", [])) | {query_group_id})
        entry["fact_domains"] = sorted(set(entry.get("fact_domains", [])) | {str(fact_domain)})
        metrics["cache_hit_count"] = int(metrics.get("cache_hit_count", 0)) + 1
        metrics["duplicate_url_count"] = int(metrics.get("duplicate_url_count", 0)) + 1
        return {"opened": False, "cache_key": normalized_url, "entry": deepcopy(entry)}

    max_opens = int(state.get("budget", {}).get("max_core_opens_per_candidate", 1))
    current_opens = sum(
        1
        for cached in cache.values()
        if isinstance(cached, dict) and cached.get("source_subject") == normalized_subject
    )
    if current_opens >= max_opens:
        _append_incomplete_work(state, "core source open limit reached")
        return {"opened": False, "reason": "budget_exhausted", "cache_key": normalized_url}

    entry = {
        "normalized_url": normalized_url,
        "content_hash": normalized_content_hash,
        "observed_at": normalized_observed_at,
        "source_subject": normalized_subject,
        "fact_domains": [normalized_fact_domain],
        "query_group_ids": [query_group_id],
        "current_run": True,
    }
    cache[normalized_url] = entry
    metrics["opened_source_count"] = int(metrics.get("opened_source_count", 0)) + 1
    metrics["source_open_success_count"] = int(metrics.get("source_open_success_count", 0)) + 1
    return {"opened": True, "cache_key": normalized_url, "entry": deepcopy(entry)}


def record_historical_reference(
    state: dict[str, Any],
    *,
    source_run_id: str,
    url: str,
    content_hash: str,
    observed_at: str,
    source_subject: str,
    fact_domain: str,
) -> dict[str, Any]:
    """Record a prior Run source as reference-only, never as current evidence."""
    normalized_source_run_id = str(source_run_id).strip()
    if not normalized_source_run_id or normalized_source_run_id == str(state.get("run_id") or "").strip():
        raise ValueError("historical reference needs a distinct non-empty source_run_id")
    normalized_url = normalize_run_url(url)
    normalized_content_hash = str(content_hash).strip()
    normalized_observed_at = str(observed_at).strip()
    normalized_subject = str(source_subject).strip()
    normalized_fact_domain = str(fact_domain).strip()
    if not all((normalized_content_hash, normalized_observed_at, normalized_subject, normalized_fact_domain)):
        raise ValueError("historical reference requires non-empty hash, observation time, subject, and fact domain")
    entry = {
        "normalized_url": normalized_url,
        "content_hash": normalized_content_hash,
        "observed_at": normalized_observed_at,
        "source_subject": normalized_subject,
        "fact_domains": [normalized_fact_domain],
        "source_run_id": normalized_source_run_id,
        "current_run": False,
        "reopened_in_current_run": False,
    }
    history = state.setdefault("historical_references", [])
    if not isinstance(history, list):
        raise ValueError("historical_references must be a list")
    history.append(entry)
    return deepcopy(entry)


def record_checkpoint_artifacts(
    state: dict[str, Any],
    *,
    brief: dict[str, Any] | None = None,
    search_log_ids: list[str] | None = None,
    candidate_ids: list[str] | None = None,
    observation_ids: list[str] | None = None,
    completed_work: list[str] | None = None,
    incomplete_work: list[str] | None = None,
) -> None:
    """Persist local identifiers and explicit coverage gaps for safe same-Run recovery."""
    if brief is not None:
        state["brief"] = deepcopy(brief)
    for key, values in (
        ("search_log_ids", search_log_ids),
        ("candidate_ids", candidate_ids),
        ("current_observations", observation_ids),
        ("completed_work", completed_work),
        ("incomplete_work", incomplete_work),
    ):
        if values is None:
            continue
        normalized = [str(value).strip() for value in values if str(value).strip()]
        state[key] = list(dict.fromkeys(normalized))


def snapshot_checkpoint(state: dict[str, Any]) -> dict[str, Any]:
    """Return a serializable deep copy; callers decide where to persist it."""
    return deepcopy(state)


def restore_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Restore only current-Run state and expose work that still needs execution."""
    restored = deepcopy(checkpoint)
    restored["recovery_count"] = int(restored.get("recovery_count", 0)) + 1
    pending = [
        str(group.get("group_id"))
        for group in restored.get("query_groups", [])
        if group.get("status") in {"not_executed", "in_progress", "source_restricted", "budget_exhausted"}
    ]
    restored["pending_query_group_ids"] = pending
    return restored


def status_summary(state: dict[str, Any]) -> dict[str, Any]:
    """Build factual stage-boundary status text inputs without commercial ranking."""
    groups = [group for group in state.get("query_groups", []) if isinstance(group, dict)]
    restricted = sum(1 for group in groups if group.get("status") == "source_restricted")
    not_executed = sum(1 for group in groups if group.get("status") in {"not_executed", "budget_exhausted"})
    metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
    candidate_count = len(state.get("candidate_ids", []))
    search_combination_coverage: list[dict[str, Any]] = []
    first_owned_candidate_ids: set[str] = set()
    for group in groups:
        combination = group.get("search_combination")
        if not isinstance(combination, dict):
            continue
        new_candidate_count = 0
        for candidate_id in group.get("candidate_ids", []):
            normalized_candidate_id = str(candidate_id).strip()
            if not normalized_candidate_id or normalized_candidate_id in first_owned_candidate_ids:
                continue
            first_owned_candidate_ids.add(normalized_candidate_id)
            new_candidate_count += 1
        search_combination_coverage.append({
            "product_term": combination.get("product_term"),
            "market": combination.get("market"),
            "customer_type": combination.get("customer_type"),
            "new_candidate_count": new_candidate_count,
            "status": group.get("status"),
        })

    next_step_options: list[dict[str, str]] = []
    if state.get("task_mode") == "discovery_snapshot" and candidate_count >= 10:
        if state.get("expansion_scale_chosen") is None:
            next_step_options.append({"key": "expand_candidate_pool", "text": "继续扩展（可指定 30 / 50 / 100 家，或直接说数量）"})
        next_step_options.extend([
            {"key": "change_search_combination", "text": "换搜索组合再找一批（换产品词 / 换客户类型，国家不变）"},
            {"key": "deep_verify_full_list", "text": "对上述名单做深度核验 → 标准开发名单（较慢；产量降、耗时增；可分批产出）"},
            {"key": "supplement_public_signals", "text": "补社媒 / 地图 / 贸易记录信号（较快；仍属候选池，不升级为已验证）"},
            {"key": "single_customer_background", "text": "选 1 家做单一客户背调"},
        ])

    hints = state.get("uncovered_combination_hints")
    uncovered_combination_hints = list(hints) if isinstance(hints, list) else []
    return {
        "task_mode": state.get("task_mode"),
        "route": state.get("route"),
        "phase": state.get("phase"),
        "execution_style": "可并行计划" if state.get("host_supports_parallel_execution") else "分批执行",
        "query_group_count": len(groups),
        "completed_query_group_count": sum(1 for group in groups if group.get("status") == "completed"),
        "source_restricted_count": restricted,
        "not_executed_count": not_executed,
        "opened_source_count": int(metrics.get("opened_source_count", 0)),
        "candidate_count": candidate_count,
        "next_step_options": next_step_options,
        "search_combination_coverage": search_combination_coverage,
        "uncovered_combination_hints": uncovered_combination_hints,
        "cache_hit_count": int(metrics.get("cache_hit_count", 0)),
        "unverified_candidate_count": int(metrics.get("unconfirmed_or_conflict_count", 0)),
        "historical_reference_label": HISTORICAL_REFERENCE_LABEL,
        "historical_reference_count": len(state.get("historical_references", [])),
        "recovery_count": int(state.get("recovery_count", 0)),
        "completed_work_count": len(state.get("completed_work", [])),
        "incomplete_work_count": len(state.get("incomplete_work", [])),
    }
