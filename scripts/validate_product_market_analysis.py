#!/usr/bin/env python3
"""Validate Superleads ProductMarketAnalysisGraph boundary invariants.

The first product-market-analysis validator is deliberately defensive: it does
not decide whether market facts are correct, but it blocks common evidence
upgrades that would make a product-outbound report look more certain than its
sources allow.
"""
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from _superleads_common import contains_local_path, has_text, is_safe_public_http_url, issue

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "shared" / "schemas"
SCHEMA_PATH = SCHEMA_DIR / "product-market-analysis.schema.json"

STATUS_FACTUAL = {"verified", "derived_calculation"}
STATUS_CONCLUSIONISH = {"verified", "derived_calculation", "preliminary_reference"}
STATUS_NONFACTUAL = {
    "candidate",
    "business_confirmation_required",
    "technical_docs_required",
    "physical_verification_required",
    "professional_confirmation_required",
    "source_restricted",
    "not_executed",
    "not_applicable",
    "not_provided",
    "conflict_pending_review",
}

NEGATION_MARKERS = (
    "不", "未", "非", "无", "勿", "禁止", "不得", "不能", "不可",
    "不是", "不等于", "无法", "不能推导", "不能替代", "不能写成", "不得写成",
    "not", "not equal", "does not", "cannot", "can not", "must not", "should not", "no ", "pending",
)

SEARCH_SOURCE_MARKERS = (
    "search_result", "search summary", "search_summary", "search snippet", "search_snippet",
    "搜索结果", "搜索摘要", "搜索 snippet", "搜索线索", "snippet",
)
SKILL_SUMMARY_MARKERS = (
    "skill summary", "skill_summary", "previous skill", "upstream skill", "model summary",
    "llm summary", "chatgpt", "claude", "gemini", "模型总结", "外部模型", "前序 skill",
    "前序skill", "skill 摘要", "skill摘要", "大模型总结", "大模型摘要",
)
QCVN_MARKERS = ("qcvn", "vietnam register", "越南登记", "越南注册", "越南检验", "vietnam registry")
UN38_SDS_MARKERS = ("un38.3", "un 38.3", "un 38 3", "sds", "msds")
HS_MARKERS = ("htsus", "hts", "hs ", "hs/hts", "税号", "归类", "关税", "税率", "tariff", "duty")
FINAL_TAX_PHRASES = (
    "最终税率就是", "最终税率为", "最终税率是", "最终归类已确定", "最终归类为",
    "最终 htsus 为", "最终 htsus 是", "最终 htsus 已确定", "最终htsus为", "最终htsus是",
    "最终 hs 为", "最终 hs 是", "最终 hs 已确定", "最终hs为", "最终hs是", "应缴税额为",
    "一定适用附加税", "一定不适用附加税", "无需关税", "final rate is", "final duty rate",
    "final classification is", "final htsus is", "duty payable is",
)
WEB_LABEL_COMPLIANCE_PHRASES = (
    "实物标签已合规", "标签已完全合规", "纺织标签已完全合规", "physical label compliant",
    "label is fully compliant", "fully label compliant",
)
GOOGLE_TRENDS_MARKERS = ("google trends", "谷歌趋势", "trends", "相对搜索兴趣")
GOOGLE_TRENDS_SALES_PHRASES = (
    "销量增长", "销量下降", "gmv", "销售额增长", "销售额下降", "采购需求旺盛", "采购需求增长",
    "进口量增长", "市场份额", "真实销量", "sales growth", "sales volume", "gmv", "purchase demand",
    "import volume", "market share",
)
PLATFORM_PRICE_MARKERS = (
    "线上价格", "平台", "电商", "retailer", "retail", "online price", "platform price",
    "挂牌价", "零售标价", "list price", "listing price", "b2c", "b2b",
)
PLATFORM_PRICE_PROMOTION_PHRASES = (
    "成交价", "真实成交", "批发价", "外贸目标价", "目标价格", "推荐价格", "推荐报价",
    "可按此报价", "可作为报价", "transaction price", "actual transaction", "wholesale price",
    "target price", "recommended price", "recommended quotation",
)
LOGISTICS_PHRASES = (
    "最佳运输方式", "最佳路线", "承诺交期", "保证时效", "一定可以拼箱", "一定可走",
    "可直接空运", "可直接快递", "普通货运输", "best route", "best shipping method",
    "committed delivery", "guaranteed transit", "guaranteed delivery",
)
VALUE_JUDGMENT_PHRASES = (
    "建议进入", "值得进入", "值得开发", "市场潜力高", "推荐开发", "优先开发",
    "推荐客户类型", "推荐客户", "推荐价格", "最佳切入", "should enter", "worth entering",
    "high market potential", "recommended customer type", "recommended price",
)
GEO_MERGE_PHRASES = (
    "出口申报国、原产国、起运国均", "出口申报国/原产国/起运国均", "三者相同无需拆分",
    "原产国就是起运国", "原产国=起运国", "production: china 因此出口申报国",
    "production china therefore export", "origin equals departure", "export origin departure are the same",
)
ORIGIN_PROOF_MARKERS = (
    "coo", "certificate of origin", "proof of origin", "origin declaration",
    "statement on origin", "invoice declaration", "preferential origin",
    "原产地证书", "原产地证明", "原产地声明", "原产证明", "优惠原产地",
)
ORIGIN_PROOF_REQUIREMENT_COLUMN_MARKERS = (
    "原产地证明要求结论", "目标国规则", "目标国要求", "是否需要原产地证明",
    "是否需要 coo", "requirement status", "destination rule",
)
ORIGIN_PROOF_USER_MATERIAL_COLUMN_MARKERS = (
    "用户材料状态", "用户当前材料状态", "用户当前材料", "用户是否已提供",
    "user material", "material status",
)
USER_COO_MISSING_MARKERS = (
    "用户未提供", "用户没有提供", "用户没提供", "未提供 coo", "未提供原产地证书",
    "未提供原产地证明", "user not provided", "user has not provided", "no coo provided",
)
COO_NOT_REQUIRED_PHRASES = (
    "不需要 coo", "无需 coo", "不要求 coo", "不需要原产地证书", "无需原产地证书",
    "不要求原产地证书", "不需要原产地证明", "无需原产地证明", "不要求原产地证明",
    "coo not required", "certificate of origin not required", "proof of origin not required",
    "no certificate of origin required",
)
USER_MATERIAL_RULE_CONFLATION_PHRASES = (
    "是否需要 coo 待用户提供", "是否需要原产地证书待用户提供", "是否需要原产地证明待用户提供",
    "待用户提供后判断是否需要 coo", "待用户提供后判断是否需要原产地证书",
    "用户没给所以待确认是否需要", "用户未提供所以待确认是否需要",
)
CAUSAL_MARKERS = ("所以", "因此", "由此", "据此", "从而", "because", "therefore", "so ")
MARKING_MARKERS = (
    "made in", "country of origin marking", "origin marking", "marking", "production:",
    "production china", "production: china", "原产国标识", "原产地标识", "产地标识",
    "原产地标签", "产地标签", "标签", "网页 production",
)
MARKING_COO_CONFLATION_PHRASES = (
    "等同 coo", "就是 coo", "视为 coo", "满足 coo", "替代 coo", "作为 coo",
    "等同原产地证书", "就是原产地证书", "视为原产地证书", "满足原产地证书", "替代原产地证书",
    "等同原产地证明", "就是原产地证明", "视为原产地证明", "满足原产地证明", "替代原产地证明",
    "equivalent to coo", "satisfies coo", "satisfies certificate of origin",
)
MARKING_COO_REQUIREMENT_PHRASES = (
    "需要 coo", "必须提供 coo", "需要原产地证书", "必须提供原产地证书",
    "需要原产地证明", "必须提供原产地证明", "coo required",
    "certificate of origin required", "proof of origin required",
)
PREFERENTIAL_ORIGIN_MARKERS = (
    "preferential", "fta", "gsp", "trade agreement", "tariff preference",
    "preferential tariff", "free trade agreement", "优惠税率", "优惠关税",
    "优惠原产地", "贸易协定", "自贸协定", "协定税率", "普惠制",
)
PREFERENTIAL_OVERGENERALIZED_PHRASES = (
    "所有进口都需要", "普通进口都需要", "所有普通进口都需要", "一律需要", "全部进口必须",
    "all imports require", "all ordinary imports require", "always required",
    "ordinary imports require", "普通清关都需要",
)
USER_COO_FILE_MARKERS = (
    "用户提供", "用户文件", "用户上传", "user provided", "user-provided", "uploaded coo",
    "用户原产地证书", "用户 coo",
)
OFFICIAL_ORIGIN_RULING_PHRASES = (
    "海关最终原产地裁定", "最终原产地已裁定", "最终原产地裁定", "主管机关最终裁定",
    "官方最终裁定", "海关已经最终认定", "customs final ruling", "final origin determination",
    "official origin ruling", "final customs determination",
)
ORIGIN_PROOF_DETERMINATE_STATUSES = {"required", "conditionally_required", "normally_not_required"}
ORIGIN_PROOF_AUTHORITY_MARKERS = (
    ".gov", "gov.", "government", "customs", "cbp", "usitc", "trade.gov", "ustr",
    "europa.eu", "eur-lex", "access2markets", "gov.uk", "税务海关", "海关",
    "主管部门", "官方", "official", "regulation", "rules of origin",
)
INTERNAL_ID_RE = re.compile(r"\b(?:run|brief|obs|observation|evidence|card|matrix|gap|conflict|handoff|transition|src)_[A-Za-z0-9][A-Za-z0-9_-]*\b", re.I)
HEX_HASH_RE = re.compile(r"\b(?:sha256:)?[a-f0-9]{32,64}\b", re.I)
URL_RE = re.compile(r"https?://[^\s\]）)>\"']+", re.I)

ID_FIELDS = {
    "runs": "run_id",
    "briefs": "brief_id",
    "products": "product_subject_id",
    "trade_premises": "trade_premise_id",
    "attributes": "attribute_id",
    "sources": "source_id",
    "observations": "observation_id",
    "evidence_cards": "evidence_card_id",
    "matrix_rows": "matrix_row_id",
    "gaps": "gap_id",
    "conflicts": "conflict_id",
    "handoffs": "handoff_id",
    "state_transitions": "transition_id",
}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def ensure_list(graph: dict[str, Any], key: str) -> list[Any]:
    value = graph.get(key, [])
    return value if isinstance(value, list) else as_list(value)


def _decode_pointer_token(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _patch_parent(document: object, pointer: str) -> tuple[object, str]:
    if not pointer.startswith("/"):
        raise ValueError(f"patch path must be a JSON Pointer: {pointer}")
    tokens = [_decode_pointer_token(token) for token in pointer[1:].split("/")]
    if not tokens:
        raise ValueError("patch path must target a value")
    current = document
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]  # type: ignore[index]
    return current, tokens[-1]


def _apply_fixture_patches(graph: dict[str, Any], patches: object) -> dict[str, Any]:
    if not isinstance(patches, list):
        raise ValueError("fixture patches must be a list")
    result = deepcopy(graph)
    for patch in patches:
        if not isinstance(patch, dict):
            raise ValueError("fixture patch must be an object")
        parent, token = _patch_parent(result, str(patch.get("path", "")))
        operation = patch.get("op")
        if operation == "remove":
            if isinstance(parent, list):
                del parent[int(token)]
            elif isinstance(parent, dict):
                del parent[token]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "replace":
            if "value" not in patch:
                raise ValueError("replace patch lacks value")
            if isinstance(parent, list):
                parent[int(token)] = patch["value"]
            elif isinstance(parent, dict):
                parent[token] = patch["value"]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "add":
            if "value" not in patch:
                raise ValueError("add patch lacks value")
            if isinstance(parent, list):
                parent.insert(int(token), patch["value"])
            elif isinstance(parent, dict):
                parent[token] = patch["value"]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "append":
            if not isinstance(parent, list) or token != "-" or "value" not in patch:
                raise ValueError("append patch must target /-")
            parent.append(patch["value"])
        else:
            raise ValueError(f"unsupported fixture patch operation: {operation}")
    return result


def load_market_fixture(path: Path, seen: set[Path] | None = None) -> dict[str, Any]:
    seen = seen or set()
    path = path.resolve()
    if path in seen:
        raise ValueError(f"fixture inheritance cycle: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"fixture must be a JSON object: {path.name}")
    if "extends" not in payload:
        return payload
    base_name = payload.get("extends")
    if not isinstance(base_name, str) or Path(base_name).name != base_name:
        raise ValueError(f"fixture base must be a local filename: {path.name}")
    base = load_market_fixture(path.parent / base_name, seen | {path})
    return _apply_fixture_patches(base, payload.get("patches"))


def text_of(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(text_of(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {text_of(val)}" for key, val in value.items())
    return str(value)


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", text_of(value)).strip().casefold()


def _contains_any(text: Any, markers: tuple[str, ...]) -> bool:
    haystack = norm(text)
    return any(marker.casefold() in haystack for marker in markers)


def _contains_positive_phrase(text: Any, phrases: tuple[str, ...]) -> bool:
    haystack = norm(text)
    for phrase in phrases:
        needle = phrase.casefold()
        start = 0
        while True:
            idx = haystack.find(needle, start)
            if idx < 0:
                break
            window = haystack[max(0, idx - 28):idx]
            if not any(marker in window for marker in NEGATION_MARKERS):
                return True
            start = idx + max(1, len(needle))
    return False


def _schema_validation_issues(graph: dict[str, Any]) -> list[dict[str, str]]:
    try:
        import jsonschema  # type: ignore
        from jsonschema import RefResolver  # type: ignore
    except Exception:
        return [issue("major", "schema_profile_unavailable", "jsonschema is unavailable; schema profile cannot be verified", "shared/schemas")]
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        store: dict[str, Any] = {}
        for item in SCHEMA_DIR.glob("*.schema.json"):
            loaded = json.loads(item.read_text(encoding="utf-8"))
            store[item.as_uri()] = loaded
            store[(SCHEMA_DIR / item.name).as_uri()] = loaded
            if has_text(loaded.get("$id")):
                store[str(loaded["$id"])] = loaded
        resolver = RefResolver(base_uri=SCHEMA_DIR.as_uri() + "/", referrer=schema, store=store)
        validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
    except Exception as exc:
        return [issue("major", "schema_profile_unavailable", f"Product market analysis schema profile could not be loaded: {exc}", "shared/schemas")]
    issues: list[dict[str, str]] = []
    try:
        for err in sorted(validator.iter_errors(graph), key=lambda e: list(e.absolute_path)):
            path = "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in err.absolute_path).lstrip(".")
            issues.append(issue("major", "schema_validation_failed", err.message, path or "$"))
    except Exception as exc:
        issues.append(issue("major", "schema_validation_error", f"Product market analysis schema validation failed to execute: {exc}", "$"))
    return issues


def _id_maps(graph: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    maps: dict[str, dict[str, dict[str, Any]]] = {}
    for key, id_field in ID_FIELDS.items():
        collection: dict[str, dict[str, Any]] = {}
        for item in ensure_list(graph, key):
            if isinstance(item, dict) and has_text(item.get(id_field)):
                collection[str(item[id_field])] = item
        maps[key] = collection
    return maps


def _add_issue(issues: list[dict[str, str]], severity: str, code: str, message: str, path: str) -> None:
    issues.append(issue(severity, code, message, path))


def _source_for_ref(ref: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any] | None:
    source_id = ref.get("source_id")
    if has_text(source_id):
        return ids["sources"].get(str(source_id))
    observation_id = ref.get("observation_id")
    obs = ids["observations"].get(str(observation_id)) if has_text(observation_id) else None
    if isinstance(obs, dict):
        return ids["sources"].get(str(obs.get("source_id")))
    return None


def _observation_for_ref(ref: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any] | None:
    observation_id = ref.get("observation_id")
    if has_text(observation_id):
        return ids["observations"].get(str(observation_id))
    return None


def _card_uses_search_source(card: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]) -> bool:
    if _contains_any([card.get("source_type"), card.get("source_locator")], SEARCH_SOURCE_MARKERS):
        return True
    for ref in as_list(card.get("source_refs")):
        if not isinstance(ref, dict):
            continue
        source = _source_for_ref(ref, ids)
        obs = _observation_for_ref(ref, ids)
        if isinstance(source, dict) and source.get("medium") == "search_result":
            return True
        if isinstance(obs, dict) and obs.get("capability") == "search.web":
            return True
    return False


def _card_text(card: dict[str, Any], include_source: bool = True) -> str:
    fields: list[Any] = [
        card.get("field_domain"),
        card.get("field_name"),
        card.get("current_value"),
        card.get("status"),
        card.get("supports"),
        card.get("applicability_scope"),
    ]
    if include_source:
        fields.extend([card.get("source_type"), card.get("source_locator")])
    return text_of(fields)


def _row_text(row: dict[str, Any]) -> str:
    return text_of([row.get("sheet_name"), row.get("row_topic"), row.get("user_visible_cells"), row.get("status")])


def _visible_text_items(graph: dict[str, Any]) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        items.append((f"matrix_rows[{idx}].row_topic", row.get("row_topic")))
        cells = row.get("user_visible_cells")
        if isinstance(cells, dict):
            for key, value in cells.items():
                items.append((f"matrix_rows[{idx}].user_visible_cells.{key}", key))
                items.append((f"matrix_rows[{idx}].user_visible_cells.{key}", value))
    for idx, gap in enumerate(ensure_list(graph, "gaps")):
        if isinstance(gap, dict):
            items.append((f"gaps[{idx}].user_visible_note", gap.get("user_visible_note")))
    for idx, conflict in enumerate(ensure_list(graph, "conflicts")):
        if isinstance(conflict, dict):
            items.append((f"conflicts[{idx}].summary", conflict.get("summary")))
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if isinstance(card, dict):
            items.append((f"evidence_cards[{idx}].source_locator", card.get("source_locator")))
    for idx, source in enumerate(ensure_list(graph, "sources")):
        if isinstance(source, dict):
            for field in ("canonical_url", "final_url"):
                items.append((f"sources[{idx}].{field}", source.get(field)))
    return items


def _looks_like_internal_leak(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    lowered = value.casefold()
    if contains_local_path(value) or "file://" in lowered or "/home/" in lowered or "/tmp/" in lowered or "c:\\" in lowered:
        return True
    if "token=" in lowered or "api_key=" in lowered or "apikey=" in lowered or "signature=" in lowered or "sig=" in lowered:
        return True
    if HEX_HASH_RE.search(value):
        return True
    if INTERNAL_ID_RE.search(value):
        return True
    for url in URL_RE.findall(value):
        if not is_safe_public_http_url(url):
            return True
    return False


def _is_origin_proof_row(row: dict[str, Any]) -> bool:
    if row.get("row_type") == "origin_proof_requirement":
        return True
    if isinstance(row.get("origin_proof_requirement"), dict):
        return True
    text = _row_text(row)
    return _contains_any(text, ORIGIN_PROOF_MARKERS) and (
        row.get("sheet_name") in {"产品准入与合规要求", "进口税费", "出口国要求", "信息来源与待确认事项"}
        or _contains_any(text, ("coo", "原产地证书", "原产地证明"))
    )


def _origin_requirement_record(row: dict[str, Any]) -> dict[str, Any]:
    record = row.get("origin_proof_requirement")
    return record if isinstance(record, dict) else {}


def _origin_requirement_status(row: dict[str, Any]) -> str:
    record = _origin_requirement_record(row)
    status = record.get("requirement_status")
    if has_text(status):
        return str(status)
    cells = row.get("user_visible_cells")
    if isinstance(cells, dict):
        for key, value in cells.items():
            if _contains_any(key, ("原产地证明要求结论", "要求结论", "目标国规则状态", "requirement status")) and has_text(value):
                return str(value)
    return ""


def _origin_user_material_status(row: dict[str, Any]) -> str:
    record = _origin_requirement_record(row)
    status = record.get("user_material_status")
    if has_text(status):
        return str(status)
    cells = row.get("user_visible_cells")
    if isinstance(cells, dict):
        for key, value in cells.items():
            if _contains_any(key, ("用户材料状态", "用户当前材料状态", "用户当前材料", "user material")) and has_text(value):
                return str(value)
    return ""


def _origin_row_has_split_fields(row: dict[str, Any]) -> bool:
    record = _origin_requirement_record(row)
    if has_text(record.get("requirement_status")) and has_text(record.get("user_material_status")):
        return True
    cells = row.get("user_visible_cells")
    if not isinstance(cells, dict):
        return False
    keys = list(cells)
    has_rule = any(_contains_any(key, ORIGIN_PROOF_REQUIREMENT_COLUMN_MARKERS) for key in keys)
    has_user = any(_contains_any(key, ORIGIN_PROOF_USER_MATERIAL_COLUMN_MARKERS) for key in keys)
    return has_rule and has_user


def _origin_record_authority_source_ids(record: dict[str, Any]) -> list[str]:
    return [str(item) for item in as_list(record.get("authority_source_refs")) if has_text(item)]


def _source_looks_authoritative(source: dict[str, Any] | None, observations: list[dict[str, Any]]) -> bool:
    if not isinstance(source, dict):
        return False
    source_text = text_of([
        source.get("publisher_relation"),
        source.get("provenance"),
        source.get("medium"),
        source.get("canonical_url"),
        source.get("final_url"),
        source.get("owner_hint"),
    ])
    observation_text = text_of([
        obs.get("title") if isinstance(obs, dict) else None
        for obs in observations
    ] + [
        obs.get("raw_excerpt") if isinstance(obs, dict) else None
        for obs in observations
    ])
    if source.get("publisher_relation") == "first_party" and _contains_any([source_text, observation_text], ORIGIN_PROOF_AUTHORITY_MARKERS):
        return True
    return _contains_any([source_text, observation_text], ORIGIN_PROOF_AUTHORITY_MARKERS)


def _origin_record_has_authority(
    record: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
    observations_by_source: dict[str, list[dict[str, Any]]],
) -> bool:
    source_ids = _origin_record_authority_source_ids(record)
    if not source_ids:
        return False
    for source_id in source_ids:
        source = ids["sources"].get(source_id)
        if _source_looks_authoritative(source, observations_by_source.get(source_id, [])):
            return True
    return False


def validate_graph(graph: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    issues.extend(_schema_validation_issues(graph))
    ids = _id_maps(graph)
    observations_by_source: dict[str, list[dict[str, Any]]] = {}
    for obs in ensure_list(graph, "observations"):
        if isinstance(obs, dict) and has_text(obs.get("source_id")):
            observations_by_source.setdefault(str(obs["source_id"]), []).append(obs)

    # Every matrix row needs an explicit status in business language.
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        if not has_text(row.get("status")):
            _add_issue(issues, "major", "market_matrix_row_missing_status", "MatrixRow lacks explicit status", f"matrix_rows[{idx}].status")

    # Search snippets and search summaries can only stay as candidate leads.
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        if card.get("status") in STATUS_FACTUAL and _card_uses_search_source(card, ids):
            _add_issue(issues, "critical", "market_search_summary_promoted", "Search result or search summary was promoted to a verified evidence card", f"evidence_cards[{idx}]")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        row_status = row.get("status")
        for card_id in as_list(row.get("evidence_card_ids")):
            card = ids["evidence_cards"].get(str(card_id))
            if isinstance(card, dict) and row_status in STATUS_FACTUAL and _card_uses_search_source(card, ids):
                _add_issue(issues, "critical", "market_search_summary_promoted", "Matrix row presents a search-only evidence card as verified", f"matrix_rows[{idx}].evidence_card_ids")

    # Skill or model summaries are not source locators.
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        locator_text = text_of([card.get("source_type"), card.get("source_locator")])
        if _contains_any(locator_text, SKILL_SUMMARY_MARKERS):
            _add_issue(issues, "critical", "market_skill_summary_as_source", "Skill/model summary was used as a source locator", f"evidence_cards[{idx}].source_locator")

    # QCVN/Vietnam Register evidence cannot be upgraded into UN38.3 or SDS.
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        source_side = text_of([card.get("source_type"), card.get("source_locator"), card.get("current_value")])
        support_side = text_of([card.get("field_domain"), card.get("field_name"), card.get("supports")])
        if _contains_any(source_side, QCVN_MARKERS) and _contains_any(support_side, UN38_SDS_MARKERS) and card.get("status") in STATUS_FACTUAL:
            _add_issue(issues, "critical", "market_qcvn_promoted_to_un38_3", "QCVN/Vietnam Register evidence was promoted to UN38.3 or SDS compliance", f"evidence_cards[{idx}]")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        text = _row_text(row)
        if row.get("status") in STATUS_FACTUAL and _contains_any(text, QCVN_MARKERS) and _contains_any(text, UN38_SDS_MARKERS):
            _add_issue(issues, "critical", "market_qcvn_promoted_to_un38_3", "Matrix row upgrades QCVN/Vietnam Register evidence to UN38.3 or SDS", f"matrix_rows[{idx}]")

    # Candidate HS/HTS/tax paths must not become final classification or final rates.
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        text = _card_text(card)
        if _contains_any(text, HS_MARKERS) and _contains_positive_phrase(text, FINAL_TAX_PHRASES):
            _add_issue(issues, "critical", "market_candidate_hs_promoted_to_final", "Candidate HS/HTS/tariff path was written as final classification or final rate", f"evidence_cards[{idx}]")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        text = _row_text(row)
        if _contains_any(text, HS_MARKERS) and _contains_positive_phrase(text, FINAL_TAX_PHRASES):
            _add_issue(issues, "critical", "market_candidate_hs_promoted_to_final", "Matrix row writes candidate HS/HTS or tariff information as final", f"matrix_rows[{idx}]")

    # Online product labels are not physical label compliance.
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        source_text = norm([card.get("source_type"), card.get("source_locator")])
        if any(marker in source_text for marker in ("product_page", "retailer", "web_label", "website", "网页", "产品页")) and _contains_positive_phrase(_card_text(card), WEB_LABEL_COMPLIANCE_PHRASES):
            _add_issue(issues, "critical", "market_web_label_promoted_to_physical_compliance", "Web label/product-page text was promoted to physical label compliance", f"evidence_cards[{idx}]")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        text = _row_text(row)
        if ("网页" in norm(text) or "product page" in norm(text) or "web label" in norm(text)) and _contains_positive_phrase(text, WEB_LABEL_COMPLIANCE_PHRASES):
            _add_issue(issues, "critical", "market_web_label_promoted_to_physical_compliance", "Matrix row promotes web label information to physical compliance", f"matrix_rows[{idx}]")

    # Google Trends is relative search interest, not sales, GMV, imports, or purchasing demand.
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        text = _card_text(card)
        if _contains_any(text, GOOGLE_TRENDS_MARKERS) and _contains_positive_phrase(text, GOOGLE_TRENDS_SALES_PHRASES):
            _add_issue(issues, "major", "market_google_trends_sales_claim", "Google Trends was written as sales, GMV, imports, market share, or purchasing demand", f"evidence_cards[{idx}]")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        text = _row_text(row)
        if _contains_any(text, GOOGLE_TRENDS_MARKERS) and _contains_positive_phrase(text, GOOGLE_TRENDS_SALES_PHRASES):
            _add_issue(issues, "major", "market_google_trends_sales_claim", "Matrix row treats Google Trends as sales or demand", f"matrix_rows[{idx}]")

    # Platform/retail list prices are references, not transaction prices,
    # wholesale target prices, or recommended quotations.
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        text = _card_text(card)
        if _contains_any(text, PLATFORM_PRICE_MARKERS) and _contains_positive_phrase(text, PLATFORM_PRICE_PROMOTION_PHRASES):
            _add_issue(issues, "critical", "market_platform_price_promoted", "Online/platform/list price was promoted to a transaction price, wholesale target price, or recommended quotation", f"evidence_cards[{idx}]")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        text = _row_text(row)
        if _contains_any(text, PLATFORM_PRICE_MARKERS) and _contains_positive_phrase(text, PLATFORM_PRICE_PROMOTION_PHRASES):
            _add_issue(issues, "critical", "market_platform_price_promoted", "Matrix row promotes online/platform/list price to a transaction price, wholesale target price, or recommended quotation", f"matrix_rows[{idx}]")

    # Logistics rows can describe common ranges, not best routes or commitments.
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        text = _row_text(row)
        is_logistics = row.get("sheet_name") == "运输方式、路线、港口与申报节点" or "物流" in norm(text) or "运输" in norm(text)
        if is_logistics and _contains_positive_phrase(text, LOGISTICS_PHRASES):
            _add_issue(issues, "major", "market_logistics_commitment_or_best", "Logistics information was written as best route, committed lead time, or guaranteed availability", f"matrix_rows[{idx}]")
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        text = _card_text(card)
        if ("物流" in norm(text) or "运输" in norm(text) or "logistics" in norm(text)) and _contains_positive_phrase(text, LOGISTICS_PHRASES):
            _add_issue(issues, "major", "market_logistics_commitment_or_best", "Logistics evidence card overstates route or time commitment", f"evidence_cards[{idx}]")

    # Unknown departure nodes must not be guessed from common ports.
    for idx, premise in enumerate(ensure_list(graph, "trade_premises")):
        if not isinstance(premise, dict):
            continue
        text = text_of([premise.get("departure_node"), premise.get("departure_node_status"), premise.get("departure_node_basis")])
        if has_text(premise.get("departure_node")) and premise.get("departure_node_status") == "verified" and _contains_any(text, ("默认", "常用", "guess", "assume", "typical port", "common port")):
            _add_issue(issues, "major", "market_guess_departure_port", "Departure port/node appears guessed from common port assumptions", f"trade_premises[{idx}].departure_node")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        text = _row_text(row)
        if ("起运" in norm(text) or "departure" in norm(text)) and _contains_any(text, ("默认", "常用", "guess", "assume", "typical port", "common port")) and row.get("status") in STATUS_CONCLUSIONISH:
            _add_issue(issues, "major", "market_guess_departure_port", "Matrix row guesses departure port/node from common port assumptions", f"matrix_rows[{idx}]")

    # A not-executed module must remain visible as a not_executed matrix row.
    rows = [row for row in ensure_list(graph, "matrix_rows") if isinstance(row, dict)]
    for run_idx, run in enumerate(ensure_list(graph, "runs")):
        if not isinstance(run, dict):
            continue
        for module in as_list(run.get("not_executed_modules")):
            if not has_text(module):
                continue
            module_norm = norm(module)
            found = False
            for row in rows:
                if row.get("status") != "not_executed":
                    continue
                row_module = norm(row.get("module_key"))
                row_text = norm(_row_text(row))
                if row_module == module_norm or module_norm in row_text:
                    found = True
                    break
            if not found:
                _add_issue(issues, "major", "market_not_executed_row_missing", f"Not-executed module is missing a visible matrix row: {module}", f"runs[{run_idx}].not_executed_modules")

    # User-visible delivery fields must not leak paths, hashes, tokens, or internal IDs.
    for path, value in _visible_text_items(graph):
        if _looks_like_internal_leak(value):
            _add_issue(issues, "critical", "market_delivery_internal_leak", "User-visible market-analysis delivery leaks local path, hash, tokenized URL, or internal ID", path)

    # Product market analysis must not make value claims or recommend entering/developing a market.
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        if _contains_positive_phrase(_row_text(row), VALUE_JUDGMENT_PHRASES):
            _add_issue(issues, "critical", "market_value_judgment", "Product market analysis delivery contains a market-entry or recommendation value judgment", f"matrix_rows[{idx}]")

    # Geography roles must remain separated: export declaration, origin, departure, destination.
    for idx, premise in enumerate(ensure_list(graph, "trade_premises")):
        if not isinstance(premise, dict):
            continue
        sep = premise.get("separation_check")
        if isinstance(sep, dict) and sep.get("roles_separated") is False:
            _add_issue(issues, "critical", "market_geo_roles_merged", "Trade premise merges export declaration, origin, departure, or destination roles", f"trade_premises[{idx}].separation_check")
        elif _contains_any(premise, GEO_MERGE_PHRASES):
            _add_issue(issues, "critical", "market_geo_roles_merged", "Trade premise text merges geography roles", f"trade_premises[{idx}]")
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if isinstance(row, dict) and _contains_any(_row_text(row), GEO_MERGE_PHRASES):
            _add_issue(issues, "critical", "market_geo_roles_merged", "Matrix row merges export declaration, origin, departure, or destination roles", f"matrix_rows[{idx}]")

    # COO / proof-of-origin requirements must be destination-rule facts first,
    # and user material readiness second.  One cannot be inferred from the
    # other.
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict) or not _is_origin_proof_row(row):
            continue
        text = _row_text(row)
        record = _origin_requirement_record(row)
        requirement_status = _origin_requirement_status(row)
        user_material_status = _origin_user_material_status(row)

        if not _origin_row_has_split_fields(row):
            _add_issue(issues, "critical", "market_origin_proof_user_material_conflated", "COO/proof-of-origin row must split destination requirement status from user material status", f"matrix_rows[{idx}]")

        user_missing = user_material_status in {"user_not_provided_but_required", "user_material_status_unknown"} or _contains_any(text, USER_COO_MISSING_MARKERS)
        written_not_required = requirement_status == "normally_not_required" or _contains_positive_phrase(text, COO_NOT_REQUIRED_PHRASES)
        if user_missing and written_not_required and any(marker in norm(text) for marker in CAUSAL_MARKERS):
            _add_issue(issues, "critical", "market_origin_proof_user_material_conflated", "User missing COO/proof-of-origin material was used to infer destination rule is not required", f"matrix_rows[{idx}]")
        if _contains_any(text, USER_MATERIAL_RULE_CONFLATION_PHRASES):
            _add_issue(issues, "critical", "market_origin_proof_user_material_conflated", "Destination COO/proof-of-origin requirement was made dependent on whether the user provided a file", f"matrix_rows[{idx}]")

        if _contains_any(text, MARKING_MARKERS) and (
            _contains_positive_phrase(text, MARKING_COO_CONFLATION_PHRASES)
            or ("所以" in norm(text) and _contains_positive_phrase(text, MARKING_COO_REQUIREMENT_PHRASES))
            or ("therefore" in norm(text) and _contains_positive_phrase(text, MARKING_COO_REQUIREMENT_PHRASES))
        ):
            _add_issue(issues, "critical", "market_origin_marking_conflated_with_coo", "Country-of-origin marking / Made in / Production was conflated with a COO/proof-of-origin document requirement", f"matrix_rows[{idx}]")

        if _contains_any(text, PREFERENTIAL_ORIGIN_MARKERS) and _contains_positive_phrase(text, PREFERENTIAL_OVERGENERALIZED_PHRASES):
            _add_issue(issues, "critical", "market_origin_preferential_overgeneralized", "Preferential-origin proof was generalized to all ordinary imports", f"matrix_rows[{idx}]")

        if _contains_any(text, USER_COO_FILE_MARKERS) and _contains_positive_phrase(text, OFFICIAL_ORIGIN_RULING_PHRASES):
            _add_issue(issues, "critical", "market_user_coo_promoted_to_official_ruling", "User-provided COO/proof-of-origin was promoted to a final customs or authority ruling", f"matrix_rows[{idx}]")

        if requirement_status in ORIGIN_PROOF_DETERMINATE_STATUSES and not _origin_record_has_authority(record, ids, observations_by_source):
            _add_issue(issues, "critical", "market_origin_requirement_without_authority", "Determinate COO/proof-of-origin requirement status needs official or authoritative destination-rule source refs", f"matrix_rows[{idx}].origin_proof_requirement.authority_source_refs")

    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        text = _card_text(card)
        is_origin_proof_card = _contains_any(text, ORIGIN_PROOF_MARKERS) or _contains_any([card.get("field_domain"), card.get("field_name")], ("原产地证明", "coo", "proof of origin"))
        if not is_origin_proof_card:
            continue
        if _contains_any(text, MARKING_MARKERS) and (
            _contains_positive_phrase(text, MARKING_COO_CONFLATION_PHRASES)
            or ("所以" in norm(text) and _contains_positive_phrase(text, MARKING_COO_REQUIREMENT_PHRASES))
            or ("therefore" in norm(text) and _contains_positive_phrase(text, MARKING_COO_REQUIREMENT_PHRASES))
        ):
            _add_issue(issues, "critical", "market_origin_marking_conflated_with_coo", "Evidence card conflates country-of-origin marking / Made in / Production with a COO/proof-of-origin document requirement", f"evidence_cards[{idx}]")
        if _contains_any(text, PREFERENTIAL_ORIGIN_MARKERS) and _contains_positive_phrase(text, PREFERENTIAL_OVERGENERALIZED_PHRASES):
            _add_issue(issues, "critical", "market_origin_preferential_overgeneralized", "Evidence card generalizes preferential-origin proof to all ordinary imports", f"evidence_cards[{idx}]")
        if _contains_any(text, USER_COO_FILE_MARKERS) and _contains_positive_phrase(text, OFFICIAL_ORIGIN_RULING_PHRASES):
            _add_issue(issues, "critical", "market_user_coo_promoted_to_official_ruling", "Evidence card promotes user-provided COO/proof-of-origin to a final customs or authority ruling", f"evidence_cards[{idx}]")

    # Brief-version changes must not leave stale downstream cards in delivery rows.
    run_version = {str(run.get("run_id")): run.get("brief_version_id") for run in ensure_list(graph, "runs") if isinstance(run, dict) and has_text(run.get("run_id"))}
    row_card_ids = {
        str(card_id)
        for row in rows
        for card_id in as_list(row.get("evidence_card_ids"))
        if has_text(card_id) and row.get("status") in {"verified", "derived_calculation", "candidate", "preliminary_reference", "professional_confirmation_required"}
    }
    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        run_id = str(card.get("run_id"))
        expected_version = run_version.get(run_id)
        card_id = str(card.get("evidence_card_id"))
        if expected_version and card.get("brief_version_id") != expected_version and card_id in row_card_ids:
            _add_issue(issues, "critical", "market_brief_stale_result_delivered", "Matrix row uses evidence card from a stale Brief version", f"evidence_cards[{idx}].brief_version_id")
    for idx, handoff in enumerate(ensure_list(graph, "handoffs")):
        if not isinstance(handoff, dict):
            continue
        stale = handoff.get("staleness_status") in {"stale_due_to_brief_change", "requires_rerun"}
        delivered_outputs = any(str(card_id) in row_card_ids for card_id in as_list(handoff.get("output_card_ids")))
        if stale and handoff.get("handoff_status") == "passed" and delivered_outputs:
            _add_issue(issues, "critical", "market_brief_stale_result_delivered", "Passed handoff from stale Brief version is still delivered", f"handoffs[{idx}]")

    return issues


def validate_file(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    try:
        graph = load_market_fixture(path)
    except Exception as exc:
        return None, [issue("critical", "market_fixture_load_failed", f"Could not load market fixture: {exc}", str(path))]
    if not isinstance(graph, dict):
        return None, [issue("critical", "market_graph_not_object", "Product market analysis graph must be a JSON object", "$")]
    return graph, validate_graph(graph)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graphs", nargs="+", help="ProductMarketAnalysisGraph JSON fixture(s)")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    all_issues: list[dict[str, str]] = []
    checked_files: list[str] = []
    for raw_path in args.graphs:
        path = Path(raw_path)
        checked_files.append(str(path))
        _, file_issues = validate_file(path)
        for item in file_issues:
            enriched = dict(item)
            enriched["file"] = str(path)
            all_issues.append(enriched)

    ok = not any(item.get("severity") in {"critical", "major"} for item in all_issues)
    result = {"ok": ok, "issue_count": len(all_issues), "issues": all_issues, "checked_files": checked_files}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
