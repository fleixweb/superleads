#!/usr/bin/env python3
"""Run the manual product-market source collection merge/export pipeline.

Code Slice M is a convenience wrapper around the already-safe Slice K/L steps:

1. collect_product_market_sources.build_collection
2. merge_product_market_collection.build_merge_result
3. validate/audit/export inside the merge step

It deliberately does not search, fetch, open, crawl, download, extract PDFs, or
create EvidenceCards/MatrixRows/SearchLogs.  The only graph mutation is appending
manual Source/Observation records; user-visible facts remain unchanged until a
later evidence-card review step.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _superleads_common import issue
from collect_product_market_sources import build_collection
from merge_product_market_collection import build_merge_result
from validate_product_market_analysis import ensure_list, load_market_fixture

PIPELINE_ROUTE = "product_outbound_market_analysis_collection_pipeline"
ALLOWED_OUTPUT = "collection_merge_validate_audit_optional_export_only"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _counts(graph: dict[str, Any] | None) -> dict[str, int]:
    graph = graph if isinstance(graph, dict) else {}
    return {
        "sources": len(ensure_list(graph, "sources")),
        "observations": len(ensure_list(graph, "observations")),
        "evidence_cards": len(ensure_list(graph, "evidence_cards")),
        "matrix_rows": len(ensure_list(graph, "matrix_rows")),
        "search_logs": len(ensure_list(graph, "search_logs")),
    }


def _collection_summary(collection: dict[str, Any], output_path: Path | None = None) -> dict[str, Any]:
    manifest = collection.get("collection_manifest") if isinstance(collection.get("collection_manifest"), dict) else {}
    summary = {
        "ok": collection.get("ok") is True,
        "route": collection.get("route"),
        "source_plan_route": collection.get("source_plan_route"),
        "execution_level": collection.get("execution_level"),
        "not_evidence": collection.get("not_evidence") is True,
        "does_not_search_web": collection.get("does_not_search_web") is True,
        "does_not_open_sources": collection.get("does_not_open_sources") is True,
        "does_not_create_evidence_cards": collection.get("does_not_create_evidence_cards") is True,
        "does_not_create_matrix_rows": collection.get("does_not_create_matrix_rows") is True,
        "allowed_output": collection.get("allowed_output"),
        "issue_count": len(collection.get("issues", [])) if isinstance(collection.get("issues"), list) else 0,
        "source_count": manifest.get("source_count", len(collection.get("sources", [])) if isinstance(collection.get("sources"), list) else 0),
        "observation_count": manifest.get("observation_count", len(collection.get("observations", [])) if isinstance(collection.get("observations"), list) else 0),
        "opened_observation_count": manifest.get("opened_observation_count", 0),
        "restricted_or_not_accessed_count": manifest.get("restricted_or_not_accessed_count", 0),
        "collection_run_id": manifest.get("collection_run_id"),
        "records_are_not_evidence": manifest.get("records_are_not_evidence") is True,
    }
    if output_path is not None:
        summary["collection_output_path"] = str(output_path)
    return summary


def _merge_summary(merge_result: dict[str, Any]) -> dict[str, Any]:
    audit = merge_result.get("audit") if isinstance(merge_result.get("audit"), dict) else {}
    export = merge_result.get("export") if isinstance(merge_result.get("export"), dict) else None
    summary: dict[str, Any] = {
        "ok": merge_result.get("ok") is True,
        "stage": merge_result.get("stage"),
        "route": merge_result.get("route"),
        "not_evidence": merge_result.get("not_evidence") is True,
        "does_not_search_web": merge_result.get("does_not_search_web") is True,
        "does_not_open_sources": merge_result.get("does_not_open_sources") is True,
        "does_not_create_evidence_cards": merge_result.get("does_not_create_evidence_cards") is True,
        "does_not_create_matrix_rows": merge_result.get("does_not_create_matrix_rows") is True,
        "allowed_output": merge_result.get("allowed_output"),
        "issue_count": merge_result.get("issue_count", 0),
        "merged_graph_path": merge_result.get("merged_graph_path"),
        "merge_manifest": merge_result.get("merge_manifest"),
        "validation": merge_result.get("validation"),
        "audit_status": audit.get("audit_status"),
        "delivery_status": audit.get("delivery_status"),
        "limitation_count": audit.get("limitation_count"),
    }
    if export is not None:
        summary["export"] = {
            "ok": export.get("ok") is True,
            "stage": export.get("stage"),
            "issue_count": export.get("issue_count", 0),
            "generated_files": export.get("generated_files", []),
        }
    return summary


def _base_result(stage: str) -> dict[str, Any]:
    return {
        "ok": False,
        "stage": stage,
        "route": PIPELINE_ROUTE,
        "not_evidence": True,
        "does_not_search_web": True,
        "does_not_open_sources": True,
        "does_not_fetch_or_download_sources": True,
        "does_not_create_search_logs": True,
        "does_not_create_evidence_cards": True,
        "does_not_create_matrix_rows": True,
        "allowed_output": ALLOWED_OUTPUT,
        "issues": [],
        "issue_count": 0,
        "guardrails": [
            "Pipeline 只串联手工 collection 与 merge/export，不搜索、不打开来源。",
            "只追加 Source / Observation，不创建 SearchLog、EvidenceCard 或 MatrixRow。",
            "新增来源只进入信息来源与待确认事项，不自动改变事实矩阵。",
            "PDF URL shell、登录墙和未打开来源仍需后续打开/复核，不能写成事实。",
        ],
    }


def build_pipeline_result(
    graph: dict[str, Any],
    collection_input: dict[str, Any],
    output_path: Path,
    collection_output_path: Path | None = None,
    export_dir: Path | None = None,
    markdown_path: Path | None = None,
    export_manifest_path: Path | None = None,
) -> dict[str, Any]:
    before_counts = _counts(graph)
    collection = build_collection(collection_input)
    if collection_output_path is not None:
        _write_json(collection_output_path, collection)

    if collection.get("ok") is not True:
        result = _base_result("collect")
        issues = collection.get("issues", []) if isinstance(collection.get("issues"), list) else []
        result.update({
            "issues": issues,
            "issue_count": len(issues),
            "graph_counts_before": before_counts,
            "collection": _collection_summary(collection, collection_output_path),
            "merge": {"ok": False, "stage": "not_run", "reason": "collection_failed"},
            "pipeline_manifest": {
                "pipeline_route": PIPELINE_ROUTE,
                "stage": "collect",
                "collection_ok": False,
                "merge_ok": False,
                "export_requested": export_dir is not None,
                "records_are_not_evidence": True,
            },
        })
        return result

    merge_result = build_merge_result(graph, collection, output_path, export_dir, markdown_path, export_manifest_path)
    after_counts: dict[str, int] | None = None
    if merge_result.get("ok") and output_path.exists():
        try:
            after_counts = _counts(_load_json_object(output_path))
        except Exception:
            after_counts = None

    result = _base_result("done" if merge_result.get("ok") else str(merge_result.get("stage") or "merge"))
    result.update({
        "ok": merge_result.get("ok") is True,
        "issues": merge_result.get("issues", []) if isinstance(merge_result.get("issues"), list) else [],
        "issue_count": merge_result.get("issue_count", 0),
        "graph_counts_before": before_counts,
        "graph_counts_after": after_counts,
        "graph_count_delta": {
            key: (after_counts or before_counts).get(key, 0) - before_counts.get(key, 0)
            for key in before_counts
        },
        "collection": _collection_summary(collection, collection_output_path),
        "merge": _merge_summary(merge_result),
        "pipeline_manifest": {
            "pipeline_route": PIPELINE_ROUTE,
            "stage": "done" if merge_result.get("ok") else str(merge_result.get("stage") or "merge"),
            "collection_ok": True,
            "merge_ok": merge_result.get("ok") is True,
            "export_requested": export_dir is not None,
            "records_are_not_evidence": True,
            "does_not_create_search_logs": True,
            "does_not_create_evidence_cards": True,
            "does_not_create_matrix_rows": True,
        },
        "generated_at": _now_iso(),
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, help="Existing ProductMarketAnalysisGraph JSON")
    parser.add_argument("--collection-input", required=True, help="Manual source collection input JSON")
    parser.add_argument("--output", required=True, help="Path for merged ProductMarketAnalysisGraph JSON")
    parser.add_argument("--collection-output", help="Optional path to write Slice K collection output JSON")
    parser.add_argument("--export-dir", help="Optional directory for CSV export after successful merge/audit")
    parser.add_argument("--markdown", help="Optional Markdown report path; requires --export-dir")
    parser.add_argument("--export-manifest", help="Optional export manifest path; requires --export-dir")
    parser.add_argument("--pipeline-manifest", help="Optional path to write a compact pipeline manifest JSON")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    if args.markdown and not args.export_dir:
        result = _base_result("args")
        result.update({
            "issues": [issue("critical", "market_collection_pipeline_args_invalid", "--markdown requires --export-dir", "markdown")],
            "issue_count": 1,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    if args.export_manifest and not args.export_dir:
        result = _base_result("args")
        result.update({
            "issues": [issue("critical", "market_collection_pipeline_args_invalid", "--export-manifest requires --export-dir", "export_manifest")],
            "issue_count": 1,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    try:
        graph = load_market_fixture(Path(args.graph))
        collection_input = _load_json_object(Path(args.collection_input))
    except Exception:  # noqa: BLE001 - CLI emits structured error
        result = _base_result("load")
        result.update({
            "issues": [issue("critical", "market_collection_pipeline_load_failed", "could not load graph or collection input", "input")],
            "issue_count": 1,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    try:
        result = build_pipeline_result(
            graph,
            collection_input,
            Path(args.output),
            Path(args.collection_output) if args.collection_output else None,
            Path(args.export_dir) if args.export_dir else None,
            Path(args.markdown) if args.markdown else None,
            Path(args.export_manifest) if args.export_manifest else None,
        )
        if args.pipeline_manifest:
            manifest_payload = {
                "ok": result.get("ok") is True,
                "route": PIPELINE_ROUTE,
                "stage": result.get("stage"),
                "issue_count": result.get("issue_count", 0),
                "pipeline_manifest": result.get("pipeline_manifest"),
                "collection": result.get("collection"),
                "merge": result.get("merge"),
                "graph_count_delta": result.get("graph_count_delta"),
                "generated_at": result.get("generated_at") or _now_iso(),
            }
            _write_json(Path(args.pipeline_manifest), manifest_payload)
            result["pipeline_manifest_path"] = str(Path(args.pipeline_manifest))
    except Exception:  # noqa: BLE001 - keep CLI structured
        result = _base_result("runtime")
        result.update({
            "issues": [issue("critical", "market_collection_pipeline_runtime_failed", "pipeline execution failed", "pipeline")],
            "issue_count": 1,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
