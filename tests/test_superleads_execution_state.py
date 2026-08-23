#!/usr/bin/env python3
"""Regression coverage for bounded, host-neutral research execution state."""
from __future__ import annotations

import sys
import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from superleads_execution_state import (
    HISTORICAL_REFERENCE_LABEL,
    add_opened_source,
    begin_phase,
    cache_capabilities,
    create_execution_state_from_plan,
    create_execution_state,
    record_historical_reference,
    record_candidate,
    record_checkpoint_artifacts,
    record_expansion_scale_choice,
    record_tool_call,
    record_milestone,
    restore_checkpoint,
    snapshot_checkpoint,
    status_summary,
)
from plan_product_market_sources import build_empty_collection_run


class SuperleadsExecutionStateTest(unittest.TestCase):
    def test_same_run_url_is_opened_once_and_reused_by_independent_groups(self) -> None:
        state = create_execution_state(
            "run-1",
            query_groups=[
                {"group_id": "company-search", "execution_order": "independent"},
                {"group_id": "association-search", "execution_order": "independent"},
            ],
            budget={"query_group_limit": 2, "max_candidates_per_group": 3, "max_core_opens_per_candidate": 1},
        )

        first = add_opened_source(
            state,
            query_group_id="company-search",
            url="https://Example.com/company/?ref=one#about",
            content_hash="sha256:first",
            observed_at="2026-08-16T00:00:00Z",
            source_subject="Example Co.",
            fact_domain="identity",
        )
        reused = add_opened_source(
            state,
            query_group_id="association-search",
            url="https://example.com/company?ref=one",
            content_hash="sha256:first",
            observed_at="2026-08-16T00:00:00Z",
            source_subject="Example Co.",
            fact_domain="public_contact",
        )

        self.assertTrue(first["opened"])
        self.assertFalse(reused["opened"])
        self.assertEqual(first["cache_key"], reused["cache_key"])
        self.assertEqual(
            ["association-search", "company-search"],
            state["source_cache"][first["cache_key"]]["query_group_ids"],
        )
        self.assertEqual(1, state["metrics"]["opened_source_count"])
        self.assertEqual(1, state["metrics"]["cache_hit_count"])

    def test_same_run_url_cache_refuses_to_reuse_a_source_for_a_different_subject(self) -> None:
        state = create_execution_state(
            "run-subject-conflict",
            query_groups=[{"group_id": "company-search", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 3, "max_core_opens_per_candidate": 2},
        )
        add_opened_source(
            state,
            query_group_id="company-search",
            url="https://example.com/company",
            content_hash="sha256:company-a",
            observed_at="2026-08-16T00:00:00Z",
            source_subject="Company A",
            fact_domain="identity",
        )

        conflict = add_opened_source(
            state,
            query_group_id="company-search",
            url="https://example.com/company",
            content_hash="sha256:company-a",
            observed_at="2026-08-16T00:00:00Z",
            source_subject="Company B",
            fact_domain="identity",
        )

        self.assertFalse(conflict["opened"])
        self.assertEqual("source_subject_conflict", conflict["reason"])
        self.assertEqual("Company A", state["source_cache"][conflict["cache_key"]]["source_subject"])
        self.assertEqual(1, state["metrics"]["unconfirmed_or_conflict_count"])

    def test_same_run_url_cache_keeps_distinct_query_values_separate(self) -> None:
        state = create_execution_state(
            "run-query-values",
            query_groups=[{"group_id": "company-search", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 3, "max_core_opens_per_candidate": 3},
        )

        first = add_opened_source(
            state,
            query_group_id="company-search",
            url="https://example.com/company?id=1&view=public",
            content_hash="sha256:first",
            observed_at="2026-08-16T00:00:00Z",
            source_subject="Example Co.",
            fact_domain="identity",
        )
        second = add_opened_source(
            state,
            query_group_id="company-search",
            url="https://example.com/company?view=public&id=2",
            content_hash="sha256:second",
            observed_at="2026-08-16T00:01:00Z",
            source_subject="Example Co.",
            fact_domain="identity",
        )

        self.assertTrue(first["opened"])
        self.assertTrue(second["opened"])
        self.assertNotEqual(first["cache_key"], second["cache_key"])
        self.assertEqual(2, state["metrics"]["opened_source_count"])

    def test_same_run_cache_canonicalizes_query_order_and_preserves_hash_routes(self) -> None:
        state = create_execution_state(
            "run-query-order",
            query_groups=[{"group_id": "company-search", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 3, "max_core_opens_per_candidate": 4},
        )

        first = add_opened_source(
            state,
            query_group_id="company-search",
            url="https://example.com/company?view=public&id=1#/overview",
            content_hash="sha256:first",
            observed_at="2026-08-16T00:00:00Z",
            source_subject="Example Co.",
            fact_domain="identity",
        )
        reused = add_opened_source(
            state,
            query_group_id="company-search",
            url="https://example.com/company?id=1&view=public#/overview",
            content_hash="sha256:first",
            observed_at="2026-08-16T00:01:00Z",
            source_subject="Example Co.",
            fact_domain="public_contact",
        )
        second = add_opened_source(
            state,
            query_group_id="company-search",
            url="https://example.com/company?id=1&view=public#/contacts",
            content_hash="sha256:second",
            observed_at="2026-08-16T00:02:00Z",
            source_subject="Example Co.",
            fact_domain="public_contact",
        )

        self.assertTrue(first["opened"])
        self.assertFalse(reused["opened"])
        self.assertTrue(second["opened"])
        self.assertNotEqual(first["cache_key"], second["cache_key"])

    def test_execution_state_rejects_values_its_schema_cannot_accept(self) -> None:
        budget = {"query_group_limit": 1, "max_candidates_per_group": 2, "max_core_opens_per_candidate": 1}
        with self.assertRaises(ValueError):
            create_execution_state("", query_groups=[], budget=budget)
        with self.assertRaises(ValueError):
            create_execution_state("run-invalid-status", query_groups=[{"group_id": "website", "status": "paused"}], budget=budget)
        with self.assertRaises(ValueError):
            create_execution_state("run-invalid-limit", query_groups=[{"group_id": "website", "candidate_limit": 0}], budget=budget)
        with self.assertRaises(ValueError):
            create_execution_state("run-invalid-stop", query_groups=[], budget={**budget, "stop_conditions": ["valid", 2]})

        state = create_execution_state("run-invalid-open", query_groups=[{"group_id": "website"}], budget=budget)
        for invalid_field, kwargs in (
            ("content_hash", {"content_hash": ""}),
            ("observed_at", {"observed_at": ""}),
            ("source_subject", {"source_subject": ""}),
            ("fact_domain", {"fact_domain": ""}),
        ):
            with self.subTest(invalid_field=invalid_field):
                values = {
                    "content_hash": "sha256:example",
                    "observed_at": "2026-08-16T00:00:00Z",
                    "source_subject": "Example Co.",
                    "fact_domain": "identity",
                }
                values.update(kwargs)
                with self.assertRaises(ValueError):
                    add_opened_source(
                        state,
                        query_group_id="website",
                        url="https://example.com/about",
                        **values,
                    )

    def test_checkpoint_resume_keeps_completed_work_and_marks_unstarted_work(self) -> None:
        state = create_execution_state(
            "run-2",
            query_groups=[
                {"group_id": "website", "execution_order": "independent"},
                {"group_id": "directory", "execution_order": "independent"},
            ],
            budget={"query_group_limit": 2, "max_candidates_per_group": 2, "max_core_opens_per_candidate": 1},
        )
        begin_phase(state, "breadth_search")
        state["query_groups"][0]["status"] = "completed"
        checkpoint = snapshot_checkpoint(state)

        restored = restore_checkpoint(checkpoint)

        self.assertEqual(1, restored["recovery_count"])
        self.assertEqual("completed", restored["query_groups"][0]["status"])
        self.assertEqual("not_executed", restored["query_groups"][1]["status"])
        self.assertEqual(["directory"], restored["pending_query_group_ids"])

    def test_capabilities_are_cached_once_per_run_and_not_rechecked(self) -> None:
        state = create_execution_state("run-3", query_groups=[], budget={})
        calls: list[str] = []

        def probe() -> dict[str, str]:
            calls.append("probe")
            return {"search.web": "available", "source.open": "available"}

        self.assertEqual({"search.web": "available", "source.open": "available"}, cache_capabilities(state, probe))
        self.assertEqual({"search.web": "available", "source.open": "available"}, cache_capabilities(state, probe))
        self.assertEqual(["probe"], calls)

    def test_historical_cache_is_reference_only_until_reopened_in_current_run(self) -> None:
        state = create_execution_state("run-4", query_groups=[], budget={})
        record_historical_reference(
            state,
            source_run_id="prior-run",
            url="https://example.com/about",
            content_hash="sha256:old",
            observed_at="2025-01-01T00:00:00Z",
            source_subject="Example Co.",
            fact_domain="identity",
        )

        summary = status_summary(state)

        self.assertEqual(HISTORICAL_REFERENCE_LABEL, summary["historical_reference_label"])
        self.assertEqual(0, summary["opened_source_count"])
        self.assertEqual(1, summary["historical_reference_count"])
        self.assertEqual([], state["current_observations"])

    def test_historical_references_have_a_prior_run_marker_and_cannot_be_current_observations(self) -> None:
        state = create_execution_state("run-current", query_groups=[], budget={})
        historical = record_historical_reference(
            state,
            source_run_id="run-prior",
            url="https://example.com/about",
            content_hash="sha256:old",
            observed_at="2025-01-01T00:00:00Z",
            source_subject="Example Co.",
            fact_domain="identity",
        )

        self.assertFalse(historical["current_run"])
        self.assertFalse(historical["reopened_in_current_run"])
        self.assertEqual("run-prior", historical["source_run_id"])
        self.assertNotIn(historical["normalized_url"], state["source_cache"])

    def test_generic_plan_state_supports_bulk_and_background_runs(self) -> None:
        plan = {
            "query_groups": [
                {"query_purpose": "official website", "execution_order": "independent"},
                {"query_purpose": "identity resolution", "execution_order": "serial"},
            ],
            "execution_budget": {
                "query_group_limit": 2,
                "max_candidates_per_group": 3,
                "max_core_opens_per_candidate": 2,
                "coverage_completion_condition": "all query groups reached a visible terminal state",
                "low_increment_stop_condition": "remaining gaps are explicit",
            },
        }
        for route in ("bulk_customer_development", "customer_background_research"):
            with self.subTest(route=route):
                state = create_execution_state_from_plan("run-" + route, plan=plan, route=route)
                self.assertEqual(route, state["route"])
                self.assertEqual(["independent", "serial"], [group["execution_order"] for group in state["query_groups"]])
                self.assertEqual(2, state["budget"]["query_group_limit"])

    def test_phase_summary_only_reports_host_supported_batched_progress(self) -> None:
        state = create_execution_state(
            "run-5",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 2, "max_core_opens_per_candidate": 1},
            host_supports_parallel_execution=False,
        )
        begin_phase(state, "source_verification")
        state["query_groups"][0]["status"] = "source_restricted"

        summary = status_summary(state)

        self.assertEqual("source_verification", summary["phase"])
        self.assertEqual("分批执行", summary["execution_style"])
        self.assertEqual(1, summary["source_restricted_count"])
        self.assertEqual(0, summary["unverified_candidate_count"])

    def test_discovery_snapshot_defaults_to_ten_candidates_and_exposes_next_step_menu(self) -> None:
        state = create_execution_state(
            "run-fast-snapshot",
            query_groups=[
                {"group_id": "website", "execution_order": "independent"},
                {"group_id": "directory", "execution_order": "independent"},
            ],
            budget={"query_group_limit": 2},
            task_mode="discovery_snapshot",
        )
        self.assertEqual(10, state["budget"]["max_candidates_per_run"])
        self.assertEqual(10, state["budget"]["max_candidates_per_group"])
        for index in range(5):
            self.assertTrue(record_candidate(state, query_group_id="website", candidate_id=f"candidate-{index}")["recorded"])
            self.assertTrue(record_candidate(state, query_group_id="directory", candidate_id=f"candidate-{index + 5}")["recorded"])
        self.assertEqual(
            {"recorded": False, "reason": "budget_exhausted"},
            record_candidate(state, query_group_id="directory", candidate_id="candidate-10"),
        )

        summary = status_summary(state)

        self.assertEqual(10, summary["candidate_count"])
        self.assertNotIn("expansion_prompt", summary)
        self.assertEqual(
            [
                "expand_candidate_pool",
                "change_search_combination",
                "deep_verify_full_list",
                "supplement_public_signals",
                "single_customer_background",
            ],
            [item["key"] for item in summary["next_step_options"]],
        )
        self.assertEqual("继续扩展（可指定 30 / 50 / 100 家，或直接说数量）", summary["next_step_options"][0]["text"])
        self.assertEqual(
            "对上述名单做深度核验 → 标准开发名单（含社媒 / 地图 / 贸易记录 + 联系人归属核验；交付表格文件 + 配套报告；较慢；产量降、耗时增；可分批产出）",
            summary["next_step_options"][2]["text"],
        )
        self.assertEqual(
            "只补社媒 / 地图 / 贸易记录信号（不做主体与联系人核验；较快，仍属候选池，不升级为已验证）",
            summary["next_step_options"][3]["text"],
        )

    def test_expansion_choice_hides_the_one_time_expansion_option_for_the_run(self) -> None:
        state = create_execution_state(
            "run-expanded-snapshot",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1},
            task_mode="discovery_snapshot",
        )
        for index in range(10):
            self.assertTrue(record_candidate(state, query_group_id="website", candidate_id=f"candidate-{index}")["recorded"])

        self.assertEqual({"recorded": True, "reason": None}, record_expansion_scale_choice(state, 100))
        self.assertEqual(100, state["expansion_scale_chosen"])
        self.assertNotIn("expand_candidate_pool", [item["key"] for item in status_summary(state)["next_step_options"]])
        self.assertEqual({"recorded": False, "reason": "already_chosen"}, record_expansion_scale_choice(state, 50))

    def test_expansion_choice_requires_a_bounded_positive_integer(self) -> None:
        state = create_execution_state(
            "run-bounded-expansion",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1},
            task_mode="discovery_snapshot",
        )

        for invalid in (0, -1, True, 501):
            with self.subTest(scale=invalid):
                with self.assertRaisesRegex(ValueError, "between 1 and 500"):
                    record_expansion_scale_choice(state, invalid)
        self.assertIsNone(state["expansion_scale_chosen"])

    def test_next_step_menu_is_absent_before_ten_candidates_but_present_for_formal_research(self) -> None:
        snapshot = create_execution_state(
            "run-under-ten",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1},
            task_mode="discovery_snapshot",
        )
        for index in range(9):
            self.assertTrue(record_candidate(snapshot, query_group_id="website", candidate_id=f"candidate-{index}")["recorded"])
        self.assertEqual([], status_summary(snapshot)["next_step_options"])

        formal = create_execution_state(
            "run-formal-menu",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 10, "max_candidates_per_run": 10},
            task_mode="formal_research",
        )
        unavailable_file_options = status_summary(formal)["next_step_options"]
        self.assertEqual(
            [
                "chat_table_when_file_unavailable",
                "supplement_pending_verification",
                "change_search_combination",
                "single_customer_background",
            ],
            [item["key"] for item in unavailable_file_options],
        )
        self.assertIn("对话内输出表格", unavailable_file_options[0]["text"])

        formal["capabilities"] = {"file.write": "available"}
        available_file_options = status_summary(formal)["next_step_options"]
        self.assertEqual(
            [
                "export_table_file",
                "supplement_pending_verification",
                "change_search_combination",
                "single_customer_background",
            ],
            [item["key"] for item in available_file_options],
        )
        self.assertIn("换格式重新导出 / 重命名工作簿", available_file_options[0]["text"])
        self.assertIn("标准交付已包含表格文件", available_file_options[0]["text"])

    def test_search_combination_coverage_uses_first_query_group_ownership_and_preserves_hints(self) -> None:
        state = create_execution_state(
            "run-combination-coverage",
            query_groups=[
                {
                    "group_id": "primary-importers",
                    "execution_order": "independent",
                    "status": "completed",
                    "search_combination": {
                        "product_term": "CLAAS 零件",
                        "market": "爱尔兰",
                        "customer_type": "进口商",
                    },
                },
                {
                    "group_id": "secondary-dealers",
                    "execution_order": "independent",
                    "status": "source_restricted",
                    "search_combination": {
                        "product_term": "CLAAS/Jaguar 零件",
                        "market": "爱尔兰",
                        "customer_type": "经销商",
                    },
                },
            ],
            budget={"query_group_limit": 2, "max_candidates_per_run": 10},
            uncovered_combination_hints=["已观察到的 silage 术语 + 爱尔兰 + 维修厂"],
        )
        self.assertTrue(record_candidate(state, query_group_id="primary-importers", candidate_id="candidate-alpha")["recorded"])
        self.assertTrue(record_candidate(state, query_group_id="primary-importers", candidate_id="candidate-beta")["recorded"])
        self.assertTrue(record_candidate(state, query_group_id="secondary-dealers", candidate_id="candidate-gamma")["recorded"])
        # A restored or merged state can retain the same candidate in a later
        # group. Coverage must still count it only at first group ownership.
        state["query_groups"][1]["candidate_ids"].append("candidate-alpha")

        summary = status_summary(state)

        self.assertEqual(
            [
                {
                    "product_term": "CLAAS 零件",
                    "market": "爱尔兰",
                    "customer_type": "进口商",
                    "new_candidate_count": 2,
                    "status": "completed",
                },
                {
                    "product_term": "CLAAS/Jaguar 零件",
                    "market": "爱尔兰",
                    "customer_type": "经销商",
                    "new_candidate_count": 1,
                    "status": "source_restricted",
                },
            ],
            summary["search_combination_coverage"],
        )
        self.assertEqual(["已观察到的 silage 术语 + 爱尔兰 + 维修厂"], summary["uncovered_combination_hints"])

        legacy = create_execution_state(
            "run-legacy-combination",
            query_groups=[{"group_id": "legacy", "execution_order": "independent"}],
            budget={"query_group_limit": 1},
        )
        self.assertNotIn("search_combination", legacy["query_groups"][0])
        self.assertEqual([], status_summary(legacy)["search_combination_coverage"])

    def test_formal_research_keeps_a_separate_default_candidate_budget(self) -> None:
        state = create_execution_state(
            "run-formal-budget",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1},
            task_mode="formal_research",
        )
        self.assertEqual(5, state["budget"]["max_candidates_per_group"])

    def test_run_and_plan_schemas_accept_additive_execution_contracts(self) -> None:
        run_schema = json.loads((ROOT / "shared" / "schemas" / "run.schema.json").read_text(encoding="utf-8"))
        plan_schema = json.loads((ROOT / "shared" / "schemas" / "plan.schema.json").read_text(encoding="utf-8"))

        execution_state = run_schema["$defs"]["executionState"]
        self.assertFalse(execution_state["additionalProperties"])
        self.assertIn("source_cache", execution_state["properties"])
        self.assertIn("checkpoint", execution_state["properties"])
        self.assertIn("metrics", execution_state["properties"])
        self.assertIn("expansion_scale_chosen", execution_state["properties"])
        expansion = execution_state["properties"]["expansion_scale_chosen"]
        self.assertEqual(["integer", "null"], expansion["type"])
        self.assertEqual(1, expansion["minimum"])
        self.assertEqual(500, expansion["maximum"])
        self.assertNotIn("enum", expansion)
        self.assertIn("uncovered_combination_hints", execution_state["properties"])
        self.assertIn("search_combination", run_schema["$defs"]["executionQueryGroup"]["properties"])
        self.assertIn("execution_budget", plan_schema["properties"])
        self.assertIn("execution_order", plan_schema["properties"]["query_groups"]["items"]["properties"])

        plan_budget = plan_schema["properties"]["execution_budget"]
        run_budget = run_schema["$defs"]["executionBudget"]
        for budget in (plan_budget, run_budget):
            self.assertIn("max_tool_calls_per_run", budget["properties"])
            self.assertIn("interim_delivery_batch_size", budget["properties"])
            self.assertNotIn("max_tool_calls_per_run", budget.get("required", []))
            self.assertNotIn("interim_delivery_batch_size", budget.get("required", []))

    def test_formal_research_budget_defaults_to_160_calls_and_batches_three_candidates(self) -> None:
        state = create_execution_state(
            "run-l2-default",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={},
            task_mode="formal_research",
            route="bulk_customer_development",
        )
        self.assertEqual(160, state["budget"]["max_tool_calls_per_run"])
        self.assertEqual(3, state["budget"]["interim_delivery_batch_size"])
        self.assertEqual(0, status_summary(state)["counted_tool_call_count"])

    def test_formal_research_budget_accepts_240_but_rejects_more(self) -> None:
        state = create_execution_state(
            "run-l2-240",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"max_tool_calls_per_run": 240, "interim_delivery_batch_size": 4},
            task_mode="formal_research",
        )
        self.assertEqual(240, state["budget"]["max_tool_calls_per_run"])
        self.assertEqual(4, state["budget"]["interim_delivery_batch_size"])
        with self.assertRaises(ValueError):
            create_execution_state(
                "run-l2-too-large",
                query_groups=[{"group_id": "website"}],
                budget={"max_tool_calls_per_run": 241},
                task_mode="formal_research",
            )

    def test_plan_budget_fields_are_forwarded_to_the_formal_run(self) -> None:
        state = create_execution_state_from_plan(
            "run-l2-plan-budget",
            plan={
                "query_groups": [{"group_id": "website"}],
                "execution_budget": {
                    "max_tool_calls_per_run": 200,
                    "interim_delivery_batch_size": 5,
                },
            },
            route="bulk_customer_development",
            task_mode="formal_research",
        )
        self.assertEqual(200, state["budget"]["max_tool_calls_per_run"])
        self.assertEqual(5, state["budget"]["interim_delivery_batch_size"])

    def test_l1_calls_do_not_consume_a_new_l2_run_allowance(self) -> None:
        l1 = create_execution_state("run-l1", query_groups=[], budget={}, task_mode="discovery_snapshot")
        self.assertFalse(record_tool_call(l1, operation="search.web")["counted"])
        l2 = create_execution_state("run-l2-after-l1", query_groups=[], budget={}, task_mode="formal_research")
        self.assertEqual(0, status_summary(l2)["counted_tool_call_count"])

    def test_only_l2_search_and_source_open_calls_consume_run_budget(self) -> None:
        state = create_execution_state(
            "run-l2-counted",
            query_groups=[{"group_id": "website"}],
            budget={"max_tool_calls_per_run": 2},
            task_mode="formal_research",
        )
        self.assertTrue(record_tool_call(state, operation="search.web")["counted"])
        self.assertTrue(record_tool_call(state, operation="source.open")["counted"])
        self.assertEqual(2, status_summary(state)["counted_tool_call_count"])
        self.assertEqual({"status": "budget_exhausted", "counted": False}, record_tool_call(state, operation="search.web"))
        self.assertEqual(2, status_summary(state)["counted_tool_call_count"])
        for operation in ("file.write", "validator", "script.call", "audit"):
            self.assertFalse(record_tool_call(state, operation=operation)["counted"])
        self.assertEqual(2, status_summary(state)["counted_tool_call_count"])

    def test_execution_state_schema_declares_helper_checkpoint_fields(self) -> None:
        run_schema = json.loads((ROOT / "shared" / "schemas" / "run.schema.json").read_text(encoding="utf-8"))
        properties = run_schema["$defs"]["executionState"]["properties"]

        self.assertIn("run_id", properties)
        self.assertIn("pending_query_group_ids", properties)

    def test_emitted_execution_state_satisfies_required_schema_contract(self) -> None:
        try:
            import jsonschema
        except ImportError as exc:  # pragma: no cover - repository validation requires jsonschema.
            self.fail(f"jsonschema is required for this regression: {exc}")

        run_schema = json.loads((ROOT / "shared" / "schemas" / "run.schema.json").read_text(encoding="utf-8"))
        execution_state = create_execution_state(
            "run-schema",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 2, "max_core_opens_per_candidate": 1},
            route="bulk_customer_development",
        )
        record_historical_reference(
            execution_state,
            source_run_id="run-schema-prior",
            url="https://example.com/historical",
            content_hash="sha256:historical",
            observed_at="2026-08-15T00:00:00Z",
            source_subject="Example Co.",
            fact_domain="identity",
        )
        run_shell = {
            "run_id": "run-schema",
            "status": "planned",
            "created_at": "2026-08-16T00:00:00Z",
            "platform": "codex_cli",
            "execution_state": execution_state,
        }

        errors = list(jsonschema.Draft202012Validator(run_schema).iter_errors(run_shell))
        self.assertEqual([], errors, [error.message for error in errors])

    def test_collection_shell_carries_a_finite_planned_execution_state(self) -> None:
        shell = build_empty_collection_run({
            "execution_budget": {
                "query_group_limit": 2,
                "max_candidates_per_group": 4,
                "max_core_opens_per_candidate": 2,
                "include_contacts": False,
                "include_trade_records": False,
                "include_historical_references": False,
                "stop_conditions": ["all planned groups are completed, restricted, or budget-exhausted"],
            },
            "query_plan": [
                {"query_plan_id": "qp-1", "query_group_id": "market_signal"},
                {"query_plan_id": "qp-2", "query_group_id": "destination_compliance"},
            ],
        })

        state = shell["execution_state"]
        self.assertEqual("intake", state["phase"])
        self.assertEqual("product_outbound_market_analysis", state["route"])
        self.assertEqual(["destination_compliance", "market_signal"], sorted(group["group_id"] for group in state["query_groups"]))
        self.assertEqual(2, state["budget"]["query_group_limit"])
        self.assertEqual([], state["current_observations"])
        self.assertTrue(shell["does_not_search_web"])

    def test_collection_shell_uses_the_shared_state_constructor_for_each_research_route(self) -> None:
        plan = {
            "execution_budget": {
                "query_group_limit": 1,
                "max_candidates_per_group": 2,
                "max_core_opens_per_candidate": 1,
            },
            "query_plan": [{"query_plan_id": "qp-1", "query_group_id": "website"}],
        }
        for route in ("bulk_customer_development", "customer_background_research"):
            with self.subTest(route=route):
                shell = build_empty_collection_run(plan, business_route=route)
                self.assertEqual(route + "_source_collection", shell["route"])
                self.assertEqual(route, shell["execution_state"]["route"])

    def test_checkpoint_retains_recoverable_research_artifacts_and_completion_gaps(self) -> None:
        state = create_execution_state(
            "run-6",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 2, "max_core_opens_per_candidate": 1},
        )

        record_checkpoint_artifacts(
            state,
            brief={"brief_id": "brief-1", "product": "industrial sensors"},
            search_log_ids=["search-1"],
            candidate_ids=["candidate-1"],
            observation_ids=["observation-1"],
            completed_work=["website search"],
            incomplete_work=["open official company page"],
        )
        restored = restore_checkpoint(snapshot_checkpoint(state))

        self.assertEqual("brief-1", restored["brief"]["brief_id"])
        self.assertEqual(["search-1"], restored["search_log_ids"])
        self.assertEqual(["candidate-1"], restored["candidate_ids"])
        self.assertEqual(["observation-1"], restored["current_observations"])
        self.assertEqual(["website search"], restored["completed_work"])
        self.assertEqual(["open official company page"], restored["incomplete_work"])

    def test_budget_limits_candidates_and_core_opens_without_dropping_the_gap(self) -> None:
        state = create_execution_state(
            "run-7",
            query_groups=[{"group_id": "website", "execution_order": "independent"}],
            budget={"query_group_limit": 1, "max_candidates_per_group": 1, "max_core_opens_per_candidate": 1},
        )

        self.assertTrue(record_candidate(state, query_group_id="website", candidate_id="candidate-1")["recorded"])
        limited_candidate = record_candidate(state, query_group_id="website", candidate_id="candidate-2")
        self.assertFalse(limited_candidate["recorded"])
        self.assertEqual("budget_exhausted", limited_candidate["reason"])

        first_open = add_opened_source(
            state,
            query_group_id="website",
            url="https://example.com/about",
            content_hash="sha256:first",
            observed_at="2026-08-16T00:00:00Z",
            source_subject="candidate-1",
            fact_domain="identity",
        )
        limited_open = add_opened_source(
            state,
            query_group_id="website",
            url="https://example.com/contact",
            content_hash="sha256:second",
            observed_at="2026-08-16T00:01:00Z",
            source_subject="candidate-1",
            fact_domain="public_contact",
        )
        self.assertTrue(first_open["opened"])
        self.assertFalse(limited_open["opened"])
        self.assertEqual("budget_exhausted", limited_open["reason"])
        self.assertIn("candidate limit reached", state["incomplete_work"])
        self.assertIn("core source open limit reached", state["incomplete_work"])

    def test_metrics_are_recorded_only_when_a_host_reports_real_elapsed_values(self) -> None:
        state = create_execution_state(
            "run-8",
            query_groups=[],
            budget={"query_group_limit": 1, "max_candidates_per_group": 1, "max_core_opens_per_candidate": 1},
            route="bulk_customer_development",
        )

        record_milestone(state, "first_query_plan_seconds", 0.25, phase="intake", active_elapsed_seconds=0.2)
        record_milestone(state, "first_candidate_seconds", 0.75, phase="breadth_search", active_elapsed_seconds=0.5)

        self.assertEqual("bulk_customer_development", state["route"])
        self.assertEqual(0.25, state["metrics"]["first_query_plan_seconds"])
        self.assertEqual(0.75, state["metrics"]["first_candidate_seconds"])
        self.assertEqual(0.2, state["metrics"]["phase_active_elapsed_seconds"]["intake"])
        self.assertEqual(0.5, state["metrics"]["phase_active_elapsed_seconds"]["breadth_search"])


if __name__ == "__main__":
    unittest.main()
