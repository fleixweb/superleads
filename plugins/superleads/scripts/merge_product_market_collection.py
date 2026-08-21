#!/usr/bin/env python3
"""Merge manual Source/Observation collection into a market-analysis graph.

Code Slice L keeps the bridge deliberately small:

* input 1: an existing ProductMarketAnalysisGraph;
* input 2: a Slice K collection output containing only Source/Observation
  records plus a manifest;
* output: a merged graph that can immediately pass validate/audit/export.

The merge never creates EvidenceCards, MatrixRows, tax/certification/logistics
facts, market judgements, or search records.  Source/Observation records remain
only inputs for later evidence-card review.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _superleads_common import has_text, issue
from audit_product_market_analysis import audit_graph
from export_product_market_workbook import export_graph
from validate_product_market_analysis import ensure_list, load_market_fixture, validate_graph

COLLECTION_ROUTE = "product_outbound_market_analysis_source_collection"
MERGE_ROUTE = "product_outbound_market_analysis_collection_merge"
SOURCE_PLAN_ROUTE = "product_outbound_market_analysis_source_plan"
COLLECTION_ALLOWED_OUTPUT = "source_and_observation_records_only"

FACT_OBJECT_KEYS = {
    "runs",
    "briefs",
    "products",
    "trade_premises",
    "attributes",
    "search_logs",
    "evidence_cards",
    "matrix_rows",
    "gaps",
    "conflicts",
    "handoffs",
    "state_transitions",
    "candidates",
    "entities",
    "claims",
    "claim_evidence",
    "assessments",
    "contact_points",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _id_map(items: list[Any], id_field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict) and has_text(item.get(id_field)):
            result[str(item[id_field])] = item
    return result


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)


def _manifest(collection: dict[str, Any]) -> dict[str, Any]:
    manifest = collection.get("collection_manifest")
    return manifest if isinstance(manifest, dict) else {}


def _collection_scope_issues(graph: dict[str, Any], collection: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    manifest = _manifest(collection)
    run_id = str(manifest.get("run_id") or "")
    brief_id = str(manifest.get("brief_id") or "")
    brief_version_id = str(manifest.get("brief_version_id") or "")

    runs = _id_map(ensure_list(graph, "runs"), "run_id")
    briefs = _id_map(ensure_list(graph, "briefs"), "brief_id")
    run = runs.get(run_id)
    brief = briefs.get(brief_id)

    for field, value in (("run_id", run_id), ("brief_id", brief_id), ("brief_version_id", brief_version_id)):
        if not has_text(value):
            issues.append(issue("critical", "market_collection_scope_missing", f"collection_manifest requires {field}", f"collection_manifest.{field}"))

    if has_text(run_id) and run_id not in runs:
        issues.append(issue("critical", "market_collection_graph_scope_mismatch", "collection run_id does not exist in target ProductMarketAnalysisGraph", "collection_manifest.run_id"))
    if has_text(brief_id) and brief_id not in briefs:
        issues.append(issue("critical", "market_collection_graph_scope_mismatch", "collection brief_id does not exist in target ProductMarketAnalysisGraph", "collection_manifest.brief_id"))
    if isinstance(run, dict):
        if has_text(brief_id) and run.get("brief_id") != brief_id:
            issues.append(issue("critical", "market_collection_graph_scope_mismatch", "collection brief_id does not match the target run", "collection_manifest.brief_id"))
        if has_text(brief_version_id) and run.get("brief_version_id") != brief_version_id:
            issues.append(issue("critical", "market_collection_graph_scope_mismatch", "collection brief_version_id does not match the target run", "collection_manifest.brief_version_id"))
    if isinstance(brief, dict) and has_text(brief_version_id) and brief.get("brief_version_id") != brief_version_id:
        issues.append(issue("critical", "market_collection_graph_scope_mismatch", "collection brief_version_id does not match the target brief", "collection_manifest.brief_version_id"))

    for idx, observation in enumerate(ensure_list(collection, "observations")):
        if not isinstance(observation, dict):
            continue
        if observation.get("run_id") != run_id:
            issues.append(issue("critical", "market_collection_graph_scope_mismatch", "collection Observation run_id must match collection_manifest.run_id", f"observations[{idx}].run_id"))
    return issues


def _collection_boundary_issues(collection: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if collection.get("ok") is not True:
        issues.append(issue("critical", "market_collection_not_ok", "collection output must be ok=true before merge", "ok"))
    if collection.get("route") != COLLECTION_ROUTE:
        issues.append(issue("critical", "market_collection_route_invalid", "collection route must be product_outbound_market_analysis_source_collection", "route"))
    if collection.get("source_plan_route") != SOURCE_PLAN_ROUTE:
        issues.append(issue("critical", "market_collection_source_plan_route_invalid", "collection must stay tied to the Product Market Source Plan route", "source_plan_route"))
    if collection.get("execution_level") != "manual_source_collection_records_only":
        issues.append(issue("critical", "market_collection_execution_level_invalid", "collection execution_level must be manual_source_collection_records_only", "execution_level"))
    if collection.get("allowed_output") != COLLECTION_ALLOWED_OUTPUT:
        issues.append(issue("critical", "market_collection_allowed_output_invalid", "collection allowed_output must be source_and_observation_records_only", "allowed_output"))

    for flag in ("not_evidence", "does_not_search_web", "does_not_open_sources", "does_not_create_evidence_cards", "does_not_create_matrix_rows"):
        if collection.get(flag) is not True:
            issues.append(issue("critical", "market_collection_not_evidence_missing", f"collection must preserve {flag}=true", flag))

    for key in sorted(FACT_OBJECT_KEYS):
        if key in collection and collection.get(key) not in (None, []):
            issues.append(issue("critical", "market_collection_fact_objects_forbidden", f"collection merge accepts only sources/observations; fact-bearing key is forbidden: {key}", key))

    raw_issues = collection.get("issues")
    if raw_issues not in (None, []):
        issues.append(issue("critical", "market_collection_embedded_issues", "collection output contains unresolved issues and cannot be merged", "issues"))

    sources = collection.get("sources")
    observations = collection.get("observations")
    if not isinstance(sources, list) or not sources:
        issues.append(issue("critical", "market_collection_empty", "collection must contain at least one Source record", "sources"))
    if not isinstance(observations, list) or not observations:
        issues.append(issue("critical", "market_collection_empty", "collection must contain at least one Observation record", "observations"))
    return issues


def _collection_record_issues(graph: dict[str, Any], collection: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    existing_sources = set(_id_map(ensure_list(graph, "sources"), "source_id"))
    existing_observations = set(_id_map(ensure_list(graph, "observations"), "observation_id"))
    collection_sources = [item for item in ensure_list(collection, "sources") if isinstance(item, dict)]
    collection_observations = [item for item in ensure_list(collection, "observations") if isinstance(item, dict)]
    source_ids = [str(item.get("source_id")) for item in collection_sources if has_text(item.get("source_id"))]
    observation_ids = [str(item.get("observation_id")) for item in collection_observations if has_text(item.get("observation_id"))]

    for idx, item in enumerate(ensure_list(collection, "sources")):
        if not isinstance(item, dict):
            issues.append(issue("critical", "market_collection_source_invalid", "collection sources must be objects", f"sources[{idx}]"))
        elif not has_text(item.get("source_id")):
            issues.append(issue("critical", "market_collection_source_id_missing", "collection Source requires source_id", f"sources[{idx}].source_id"))
    for idx, item in enumerate(ensure_list(collection, "observations")):
        if not isinstance(item, dict):
            issues.append(issue("critical", "market_collection_observation_invalid", "collection observations must be objects", f"observations[{idx}]"))
        elif not has_text(item.get("observation_id")):
            issues.append(issue("critical", "market_collection_observation_id_missing", "collection Observation requires observation_id", f"observations[{idx}].observation_id"))

    for source_id in _duplicates(source_ids):
        issues.append(issue("critical", "market_collection_duplicate_source_id", "collection contains duplicate Source IDs", f"sources.{source_id}"))
    for observation_id in _duplicates(observation_ids):
        issues.append(issue("critical", "market_collection_duplicate_observation_id", "collection contains duplicate Observation IDs", f"observations.{observation_id}"))
    for source_id in sorted(set(source_ids) & existing_sources):
        issues.append(issue("critical", "market_collection_duplicate_source_id", "collection Source ID already exists in target graph", f"sources.{source_id}"))
    for observation_id in sorted(set(observation_ids) & existing_observations):
        issues.append(issue("critical", "market_collection_duplicate_observation_id", "collection Observation ID already exists in target graph", f"observations.{observation_id}"))

    collection_source_set = set(source_ids)
    for idx, observation in enumerate(collection_observations):
        source_id = str(observation.get("source_id") or "")
        if source_id not in collection_source_set:
            issues.append(issue("critical", "market_collection_observation_source_missing", "collection Observation must reference a Source included in the same collection output", f"observations[{idx}].source_id"))
    return issues


def validate_collection_for_merge(graph: dict[str, Any], collection: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    issues.extend(_collection_boundary_issues(collection))
    issues.extend(_collection_scope_issues(graph, collection))
    issues.extend(_collection_record_issues(graph, collection))
    return issues


def merge_collection(graph: dict[str, Any], collection: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]], dict[str, Any]]:
    issues = validate_collection_for_merge(graph, collection)
    manifest = _manifest(collection)
    merge_manifest: dict[str, Any] = {
        "merge_route": MERGE_ROUTE,
        "collection_run_id": manifest.get("collection_run_id"),
        "run_id": manifest.get("run_id"),
        "brief_id": manifest.get("brief_id"),
        "brief_version_id": manifest.get("brief_version_id"),
        "query_plan_id": manifest.get("query_plan_id"),
        "query_group_id": manifest.get("query_group_id"),
        "source_count_before": len(ensure_list(graph, "sources")),
        "observation_count_before": len(ensure_list(graph, "observations")),
        "merged_source_ids": [],
        "merged_observation_ids": [],
        "records_are_not_evidence": True,
        "does_not_create_evidence_cards": True,
        "does_not_create_matrix_rows": True,
    }
    if issues:
        return None, issues, merge_manifest

    merged = deepcopy(graph)
    merged.setdefault("sources", [])
    merged.setdefault("observations", [])
    sources = [deepcopy(item) for item in ensure_list(collection, "sources") if isinstance(item, dict)]
    observations = [deepcopy(item) for item in ensure_list(collection, "observations") if isinstance(item, dict)]
    merged["sources"].extend(sources)
    merged["observations"].extend(observations)
    merge_manifest.update({
        "source_count_after": len(ensure_list(merged, "sources")),
        "observation_count_after": len(ensure_list(merged, "observations")),
        "merged_source_ids": [item.get("source_id") for item in sources],
        "merged_observation_ids": [item.get("observation_id") for item in observations],
    })
    return merged, [], merge_manifest


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _base_result(stage: str = "pre_merge") -> dict[str, Any]:
    return {
        "ok": False,
        "stage": stage,
        "route": MERGE_ROUTE,
        "not_evidence": True,
        "does_not_search_web": True,
        "does_not_open_sources": True,
        "does_not_create_evidence_cards": True,
        "does_not_create_matrix_rows": True,
        "allowed_output": "merged_graph_and_optional_exports_only",
        "issues": [],
        "issue_count": 0,
        "guardrails": [
            "Collection merge 只追加 Source / Observation。",
            "不创建 EvidenceCard、不创建 MatrixRow、不生成事实结论。",
            "导出器只展示来源入口和待确认事项，不因新增来源自动改变市场事实矩阵。",
            "Source / Observation 仍需后续 EvidenceCard 互证后才能支撑事实。",
        ],
    }


def build_merge_result(
    graph: dict[str, Any],
    collection: dict[str, Any],
    output_path: Path,
    export_dir: Path | None = None,
    markdown_path: Path | None = None,
    export_manifest_path: Path | None = None,
) -> dict[str, Any]:
    merged, issues, merge_manifest = merge_collection(graph, collection)
    if issues or merged is None:
        result = _base_result("pre_merge")
        result.update({"issues": issues, "issue_count": len(issues), "merge_manifest": merge_manifest})
        return result

    validation_issues = [item for item in validate_graph(merged) if item.get("severity") in {"critical", "major"}]
    if validation_issues:
        result = _base_result("validate")
        result.update({"issues": validation_issues, "issue_count": len(validation_issues), "merge_manifest": merge_manifest})
        return result

    audit = audit_graph(merged)
    if not audit.get("ok"):
        result = _base_result("audit")
        result.update({"audit": audit, "issues": audit.get("issues", []), "issue_count": audit.get("issue_count", 0), "merge_manifest": merge_manifest})
        return result

    _write_json(output_path, merged)
    export_result: dict[str, Any] | None = None
    if export_dir is not None:
        export_result = export_graph(merged, export_dir, markdown_path, export_manifest_path)
        if not export_result.get("ok"):
            result = _base_result("export")
            result.update({
                "merged_graph_path": str(output_path),
                "audit": audit,
                "export": export_result,
                "issues": export_result.get("issues", []),
                "issue_count": export_result.get("issue_count", 0),
                "merge_manifest": merge_manifest,
            })
            return result

    result = _base_result("done")
    result.update({
        "ok": True,
        "issue_count": 0,
        "merged_graph_path": str(output_path),
        "merge_manifest": merge_manifest,
        "validation": {"ok": True, "issue_count": 0, "issues": []},
        "audit": audit,
        "export": export_result,
        "generated_at": _now_iso(),
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, help="Existing ProductMarketAnalysisGraph JSON")
    parser.add_argument("--collection", required=True, help="Slice K source collection output JSON")
    parser.add_argument("--output", required=True, help="Path for merged ProductMarketAnalysisGraph JSON")
    parser.add_argument("--export-dir", help="Optional directory for CSV export after successful merge/audit")
    parser.add_argument("--markdown", help="Optional Markdown report path; requires --export-dir")
    parser.add_argument("--manifest", help="Optional export manifest path; requires --export-dir")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    try:
        graph = load_market_fixture(Path(args.graph))
        collection = _load_json_object(Path(args.collection))
    except Exception as exc:
        result = _base_result("load")
        result.update({
            "issues": [issue("critical", "market_collection_merge_load_failed", f"could not load graph or collection: {exc}", "input")],
            "issue_count": 1,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    if args.markdown and not args.export_dir:
        result = _base_result("args")
        result.update({
            "issues": [issue("critical", "market_collection_merge_args_invalid", "--markdown requires --export-dir", "markdown")],
            "issue_count": 1,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    if args.manifest and not args.export_dir:
        result = _base_result("args")
        result.update({
            "issues": [issue("critical", "market_collection_merge_args_invalid", "--manifest requires --export-dir", "manifest")],
            "issue_count": 1,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result = build_merge_result(
        graph,
        collection,
        Path(args.output),
        Path(args.export_dir) if args.export_dir else None,
        Path(args.markdown) if args.markdown else None,
        Path(args.manifest) if args.manifest else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
