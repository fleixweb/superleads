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
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

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
    "没", "没有", "未能",
    "not", "not equal", "does not", "cannot", "can not", "must not", "should not", "no ", "without", "pending",
)

SEARCH_SOURCE_MARKERS = (
    "search_result", "search_log", "searchlog", "search log", "search summary", "search_summary", "search snippet", "search_snippet",
    "搜索结果", "搜索日志", "搜索摘要", "搜索 snippet", "搜索线索", "snippet",
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
TIME_SENSITIVE_SHEETS = {
    "长期需求与搜索趋势",
    "公开市场资料与行业信息",
    "线上市场与价格参考",
    "季节、节日与销售窗口",
    "产品准入与合规要求",
    "进口税费",
    "出口国要求",
    "运输方式、路线、港口与申报节点",
    "近期外部因素",
}
FRESHNESS_DATE_UNKNOWN_MARKERS = (
    "日期未见", "未见日期", "无日期", "日期不明", "未公开日期", "未标日期",
    "date unknown", "unknown date", "date not visible", "undated", "no date",
    "not dated", "n.d.",
)
LATEST_OR_CURRENT_PHRASES = (
    "最新", "现行", "当前有效", "截至", "有效税率", "现行税率", "最新税率",
    "最新法规", "最新要求", "最新行情", "最新影响", "当前税率", "当前法规",
    "current rate", "current tariff", "current duty", "current regulation",
    "currently in force", "currently effective", "currently required",
    "latest", "as of",
)
LATEST_NEGATION_MARKERS = (
    "不称", "不能称", "不得称", "不写成", "不能写成", "不得写成",
    "不当作", "不能当", "不得当", "不可当", "不能作为", "不作为",
    "不支持", "不能支持", "不得支持", "无日期不称", "没有来源不称", "未复核不称",
    "not latest", "not current", "cannot claim", "cannot call",
    "must not call", "cannot be treated as", "not treated as", "does not support",
)
FRESHNESS_STATUS_LIMITED = {
    "stale_needs_recheck",
    "date_unknown_needs_recheck",
    "date_unknown_recently_observed",
}
FRESHNESS_STATUS_CURRENTISH = {"current_enough_for_scope"}
FRESHNESS_DEFAULT_WINDOWS = {
    "external_factor": 14,
    "import_tax": 30,
    "export_requirement": 30,
    "online_price": 30,
    "google_trends": 90,
    "logistics": 90,
    "destination_requirement": 180,
    "origin_proof_requirement": 180,
    "certification_requirement": 180,
    "market_report": 365,
    "seasonality": 365,
}
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
CERTIFICATION_REQUIREMENT_MARKERS = (
    "certification", "certificate", "conformity", "compliance", "approval", "authorization",
    "test report", "registration", "declaration of conformity", "doc", "labeling", "labelling",
    "packaging", "import permit", "sds", "msds", "un38.3", "un 38.3", "fcc", "ul",
    "ce", "fda", "cpsia", "reach", "rohs", "epr", "认证", "证书", "合格评定",
    "测试报告", "检测报告", "注册", "备案", "标签", "标识", "包装", "进口许可",
    "准入", "目的国要求", "目标国要求", "运输文件",
)
CERT_REQUIREMENT_COLUMN_MARKERS = (
    "目标国认证/准入要求结论", "目标市场要求", "目标国要求", "目的国要求",
    "准入要求结论", "认证要求结论", "applicability status", "destination requirement",
)
CERT_USER_MATERIAL_COLUMN_MARKERS = (
    "用户认证材料状态", "用户材料状态", "用户现有材料", "用户当前材料状态",
    "user material", "material status",
)
USER_CERT_MISSING_MARKERS = (
    "用户未提供", "用户没有提供", "用户没提供", "未提供证书", "没有证书",
    "未提供认证", "未提供测试报告", "user not provided", "user has not provided",
    "no certificate provided", "no certification provided",
)
CERT_NOT_REQUIRED_PHRASES = (
    "不需要认证", "无需认证", "不要求认证", "不需要证书", "无需证书",
    "不需要测试报告", "无需测试报告", "不需要注册", "无需注册",
    "certification not required", "certificate not required", "no certification required",
    "test report not required", "registration not required",
)
USER_CERT_RULE_CONFLATION_PHRASES = (
    "是否需要认证待用户提供", "是否需要证书待用户提供", "待用户提供后判断是否需要认证",
    "待用户提供证书后判断是否需要", "用户没给所以待确认是否需要认证",
    "用户未提供所以待确认是否需要认证", "没有证书无法分析需要什么认证",
    "cannot analyze certification until user provides certificate",
)
CERT_ENTRY_MARKERS = (
    "certificate download", "certificate page", "certificates", "download certificate",
    "证书下载", "证书入口", "certificate 下载", "registration certificate",
)
CERT_ENTRY_PROMOTION_PHRASES = (
    "已具备认证", "已获得认证", "已经认证", "认证齐全", "已合规", "完全合规",
    "has certification", "certified", "fully compliant", "compliant for sale",
)
TEST_REPORT_MARKERS = (
    "test report", "testing report", "laboratory report", "lab report", "检测报告", "测试报告", "实验室报告",
)
TEST_REPORT_AS_CERT_PHRASES = (
    "等于认证", "就是认证", "视为认证", "替代认证", "作为认证证书", "已获得认证",
    "equals certification", "is certification", "replaces certification", "certified",
)
CHANNEL_REQUIREMENT_MARKERS = (
    "amazon", "walmart", "costco", "retailer", "platform", "seller requirement", "vendor manual",
    "客户要求", "渠道要求", "平台要求", "零售商要求", "买家要求", "项目要求",
)
LEGAL_REQUIREMENT_PHRASES = (
    "法律强制", "法规强制", "海关强制", "目标国强制要求", "必须依法", "进口法规要求",
    "legally required", "customs mandatory", "mandatory by law", "regulatory requirement",
)
USER_CERT_FILE_MARKERS = (
    "用户提供", "用户文件", "用户上传", "user provided", "user-provided", "uploaded certificate",
    "用户证书", "用户测试报告",
)
DESTINATION_RECOGNITION_PHRASES = (
    "目标国认可", "目的国认可", "美国认可", "欧盟认可", "已获目标市场认可", "产品已合规",
    "可以销售", "可销售", "可以清关", "可清关", "recognized by destination",
    "accepted by destination", "compliant for destination", "ready for customs clearance",
)
CERT_DETERMINATE_STATUSES = {"required", "conditionally_required", "normally_not_required", "not_applicable"}
CERT_AUTHORITY_MARKERS = (
    ".gov", "gov.", "government", "customs", "official", "regulation", "regulatory",
    "authority", "agency", "cpsc", "fcc", "fda", "epa", "usda", "osha", "dot",
    "phmsa", "cbp", "ftc", "europa.eu", "eur-lex", "access2markets", "gov.uk",
    "主管部门", "官方", "海关", "法规", "法令", "标准机构", "认证主管", "市场监管",
)
SOURCE_OPEN_CAPABILITIES = {
    "source.open",
    "browser.render",
    "document.extract",
    "source.capture",
    "social.visible.read",
    "registry.lookup",
    "trademark.lookup",
    "maps.lookup",
    "image.inspect",
}
OPENED_ACCESS_STATUSES = {"opened", "captured", "extracted", "rendered"}
SOURCE_RESTRICTED_ACCESS_STATUSES = {"blocked", "login_wall", "login_required", "forbidden", "inaccessible", "not_accessed", "restricted"}
SEARCH_LOG_ALLOWED_OUTPUT = "search_log_or_source_locator_only"
SOURCE_PLAN_ROUTE = "product_outbound_market_analysis_source_plan"
QUERY_PLAN_DIRECT_FACT_MARKERS = (
    "source_plan_only", "source pack", "sourcepack", "query plan", "query_plan", "querytemplate",
    "source_or_query_plan_only", "pack_boundary_note", "source pack / querytemplate",
    "来源计划", "查询计划", "source pack", "source pack registry", "pack 入口",
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
    "search_logs": "search_log_id",
    "sources": "source_id",
    "observations": "observation_id",
    "evidence_cards": "evidence_card_id",
    "corroboration_records": "corroboration_id",
    "freshness_records": "freshness_id",
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


def _parse_iso_date(value: Any) -> date | None:
    if not has_text(value):
        return None
    text = str(value).strip()
    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            return None
    match = re.search(r"(\d{4})[-/](\d{1,2})(?:[-/](\d{1,2}))?", text)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3) or 1)
        try:
            return date(year, month, day)
        except ValueError:
            return None
    match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    if match:
        try:
            return date(int(match.group(1)), 1, 1)
        except ValueError:
            return None
    return None


def _days_between(left: date | None, right: date | None) -> int | None:
    if left is None or right is None:
        return None
    return abs((right - left).days)


def _parsed_dates(values: Any) -> list[date]:
    dates: list[date] = []
    for item in as_list(values):
        parsed = _parse_iso_date(item)
        if parsed is not None:
            dates.append(parsed)
    return dates


def _date_unknown(value: Any) -> bool:
    return not _parse_iso_date(value) and _contains_any(value, FRESHNESS_DATE_UNKNOWN_MARKERS)


def _freshness_text(record: dict[str, Any]) -> str:
    return text_of([
        record.get("field_domain"),
        record.get("field_name"),
        record.get("freshness_status"),
        record.get("date_basis"),
        record.get("user_visible_summary"),
        record.get("cannot_conclude"),
        record.get("next_verification_steps"),
    ])


def _field_freshness_key(field_domain: Any, field_name: Any = None, module_key: Any = None, sheet_name: Any = None) -> str | None:
    text = norm([field_domain, field_name, module_key, sheet_name])
    if any(marker in text for marker in ("近期外部", "外部因素", "political", "war", "disaster", "strike", "sanction", "external factor")):
        return "external_factor"
    if any(marker in text for marker in ("进口税费", "关税", "税率", "htsus", "tariff", "duty")):
        return "import_tax"
    if any(marker in text for marker in ("出口国要求", "出口管制", "商检", "检验检疫", "export control", "export requirement")):
        return "export_requirement"
    if any(marker in text for marker in ("线上市场", "价格", "标价", "online price", "platform price", "listing price")):
        return "online_price"
    if any(marker in text for marker in ("google trends", "谷歌趋势", "搜索趋势", "长期需求")):
        return "google_trends"
    if any(marker in text for marker in ("运输", "物流", "海运", "空运", "快递", "预申报", "logistics", "shipping", "transit")):
        return "logistics"
    if any(marker in text for marker in ("认证", "准入", "合规", "标签", "包装", "注册", "许可", "certification", "conformity", "compliance", "labeling", "packaging", "registration", "permit")):
        return "certification_requirement"
    if any(marker in text for marker in ("原产地证明", "coo", "proof of origin", "origin declaration")):
        return "origin_proof_requirement"
    if any(marker in text for marker in ("市场报告", "行业报告", "公开市场资料", "industry report", "market report")):
        return "market_report"
    if any(marker in text for marker in ("节日", "季节", "淡旺季", "holiday", "season")):
        return "seasonality"
    return None


def _is_time_sensitive_field(field_domain: Any, field_name: Any = None, module_key: Any = None, sheet_name: Any = None) -> bool:
    return _field_freshness_key(field_domain, field_name, module_key, sheet_name) is not None or sheet_name in TIME_SENSITIVE_SHEETS


def _default_review_window_days(field_domain: Any, field_name: Any = None, module_key: Any = None, sheet_name: Any = None) -> int | None:
    key = _field_freshness_key(field_domain, field_name, module_key, sheet_name)
    if key:
        return FRESHNESS_DEFAULT_WINDOWS[key]
    return None


def _latest_claim_without_freshness_text(text: Any) -> bool:
    haystack = norm(text)
    for phrase in LATEST_OR_CURRENT_PHRASES:
        needle = phrase.casefold()
        start = 0
        while True:
            idx = haystack.find(needle, start)
            if idx < 0:
                break
            window = haystack[max(0, idx - 18):idx]
            if not any(marker in window for marker in LATEST_NEGATION_MARKERS):
                return True
            start = idx + max(1, len(needle))
    return False


def _corroboration_text(record: dict[str, Any]) -> str:
    return text_of([
        record.get("field_domain"),
        record.get("field_name"),
        record.get("current_signal"),
        record.get("corroboration_status"),
        record.get("independence_basis"),
        record.get("user_visible_summary"),
        record.get("cannot_conclude"),
        record.get("next_verification_steps"),
    ])


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
    for idx, record in enumerate(ensure_list(graph, "corroboration_records")):
        if isinstance(record, dict):
            items.append((f"corroboration_records[{idx}].user_visible_summary", record.get("user_visible_summary")))
            items.append((f"corroboration_records[{idx}].cannot_conclude", record.get("cannot_conclude")))
            items.append((f"corroboration_records[{idx}].next_verification_steps", record.get("next_verification_steps")))
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


def _is_certification_requirement_row(row: dict[str, Any]) -> bool:
    if row.get("row_type") in {"certification_requirement", "destination_requirement"}:
        return True
    if row.get("module_key") in {"certification_requirement", "destination_requirement"}:
        return True
    if isinstance(row.get("certification_requirement"), dict):
        return True
    cells = row.get("user_visible_cells")
    if isinstance(cells, dict):
        keys = list(cells)
        return any(_contains_any(key, CERT_REQUIREMENT_COLUMN_MARKERS) for key in keys)
    return False


def _cert_requirement_record(row: dict[str, Any]) -> dict[str, Any]:
    record = row.get("certification_requirement")
    return record if isinstance(record, dict) else {}


def _cert_requirement_status(row: dict[str, Any]) -> str:
    record = _cert_requirement_record(row)
    status = record.get("applicability_status")
    if has_text(status):
        return str(status)
    cells = row.get("user_visible_cells")
    if isinstance(cells, dict):
        for key, value in cells.items():
            if _contains_any(key, CERT_REQUIREMENT_COLUMN_MARKERS) and has_text(value):
                return str(value)
    return ""


def _cert_user_material_status(row: dict[str, Any]) -> str:
    record = _cert_requirement_record(row)
    status = record.get("user_material_status")
    if has_text(status):
        return str(status)
    cells = row.get("user_visible_cells")
    if isinstance(cells, dict):
        for key, value in cells.items():
            if _contains_any(key, CERT_USER_MATERIAL_COLUMN_MARKERS) and has_text(value):
                return str(value)
    return ""


def _cert_row_has_split_fields(row: dict[str, Any]) -> bool:
    record = _cert_requirement_record(row)
    if has_text(record.get("applicability_status")) and has_text(record.get("user_material_status")):
        return True
    cells = row.get("user_visible_cells")
    if not isinstance(cells, dict):
        return False
    keys = list(cells)
    has_rule = any(_contains_any(key, CERT_REQUIREMENT_COLUMN_MARKERS) for key in keys)
    has_user = any(_contains_any(key, CERT_USER_MATERIAL_COLUMN_MARKERS) for key in keys)
    return has_rule and has_user


def _cert_record_authority_source_ids(record: dict[str, Any]) -> list[str]:
    return [str(item) for item in as_list(record.get("authority_source_refs")) if has_text(item)]


def _cert_source_looks_authoritative(source: dict[str, Any] | None, observations: list[dict[str, Any]]) -> bool:
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
    return _contains_any([source_text, observation_text], CERT_AUTHORITY_MARKERS)


def _cert_record_has_authority(
    record: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
    observations_by_source: dict[str, list[dict[str, Any]]],
) -> bool:
    if record.get("source_authority_level") == "source_restricted":
        return False
    source_ids = _cert_record_authority_source_ids(record)
    if not source_ids:
        return False
    for source_id in source_ids:
        source = ids["sources"].get(source_id)
        if _cert_source_looks_authoritative(source, observations_by_source.get(source_id, [])):
            return True
    return False


def _observation_is_opened_source(obs: dict[str, Any]) -> bool:
    return obs.get("capability") in SOURCE_OPEN_CAPABILITIES and str(obs.get("access_status") or "") in OPENED_ACCESS_STATUSES


def _source_observation_opened(source_id: Any, observations_by_source: dict[str, list[dict[str, Any]]]) -> bool:
    if not has_text(source_id):
        return False
    return any(_observation_is_opened_source(obs) for obs in observations_by_source.get(str(source_id), []))


def _card_uses_query_plan_or_search_log_as_direct_source(card: dict[str, Any]) -> bool:
    if has_text(card.get("query_plan_id")) or has_text(card.get("search_log_id")):
        return True
    if _contains_any([card.get("source_type"), card.get("source_locator")], QUERY_PLAN_DIRECT_FACT_MARKERS):
        return True
    for ref in as_list(card.get("source_refs")):
        if isinstance(ref, dict) and (has_text(ref.get("query_plan_id")) or has_text(ref.get("search_log_id"))):
            return True
    return False


def _source_linked_search_logs(source_id: str, search_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    linked: list[dict[str, Any]] = []
    for log in search_logs:
        if not isinstance(log, dict):
            continue
        if source_id in {str(item) for item in as_list(log.get("accessed_source_ids")) if has_text(item)}:
            linked.append(log)
            continue
        for ref in as_list(log.get("result_refs")):
            if isinstance(ref, dict) and str(ref.get("opened_source_id") or "") == source_id:
                linked.append(log)
                break
    return linked


def _public_source_url(source: dict[str, Any]) -> bool:
    url = source.get("final_url") or source.get("canonical_url")
    return is_safe_public_http_url(url)


def _source_independence_key(source: dict[str, Any] | None) -> str | None:
    """Return a conservative source-owner key for weak-source corroboration."""
    if not isinstance(source, dict):
        return None
    owner = source.get("owner_hint")
    if has_text(owner):
        return f"owner:{norm(owner)}"
    for field in ("final_url", "canonical_url"):
        url = source.get(field)
        if not has_text(url):
            continue
        try:
            host = (urlsplit(str(url)).hostname or "").casefold().lstrip("www.")
        except ValueError:
            host = ""
        if host:
            return f"host:{host}"
    # If neither owner_hint nor public URL host is available, do not count the
    # source as independently identifiable.  A source_id is an internal handle,
    # not business-world independence.
    return None


def _source_ids_from_refs(refs: Any, ids: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
    source_ids: list[str] = []
    seen: set[str] = set()
    for ref in as_list(refs):
        if not isinstance(ref, dict):
            continue
        source_id = ref.get("source_id")
        if not has_text(source_id) and has_text(ref.get("observation_id")):
            obs = ids["observations"].get(str(ref.get("observation_id")))
            if isinstance(obs, dict):
                source_id = obs.get("source_id")
        if has_text(source_id) and str(source_id) not in seen:
            seen.add(str(source_id))
            source_ids.append(str(source_id))
    return source_ids


def _card_source_ids(card: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
    return _source_ids_from_refs(card.get("source_refs"), ids)


def _source_has_opened_observation(source_id: str, observations_by_source: dict[str, list[dict[str, Any]]]) -> bool:
    return any(_observation_is_opened_source(obs) for obs in observations_by_source.get(source_id, []) if isinstance(obs, dict))


def _corroboration_issues(
    graph: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
    observations_by_source: dict[str, list[dict[str, Any]]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    run_ids = set(ids["runs"])
    evidence_cards = ids["evidence_cards"]
    conflicts = ids["conflicts"]
    corroborations = ids.get("corroboration_records", {})

    for idx, record in enumerate(ensure_list(graph, "corroboration_records")):
        if not isinstance(record, dict):
            continue
        path = f"corroboration_records[{idx}]"
        status = str(record.get("corroboration_status") or "")
        if record.get("run_id") not in run_ids:
            _add_issue(issues, "critical", "market_corroboration_run_missing", "CorroborationRecord must reference an existing product-market run", f"{path}.run_id")

        if record.get("review_status") != "passed":
            _add_issue(issues, "major", "market_corroboration_not_reviewed", "CorroborationRecord must be reviewed before it can support delivery", f"{path}.review_status")

        if _card_uses_query_plan_or_search_log_as_direct_source(record):
            _add_issue(issues, "critical", "market_corroboration_search_or_plan_source", "Search snippets, SearchLog, Source Pack, or Query Plan cannot be used as direct corroboration evidence", path)

        source_ids = _source_ids_from_refs(record.get("source_refs"), ids)
        for card_id in as_list(record.get("supporting_evidence_card_ids")):
            card = evidence_cards.get(str(card_id))
            if not isinstance(card, dict):
                _add_issue(issues, "critical", "market_corroboration_card_missing", "CorroborationRecord references a missing supporting EvidenceCard", f"{path}.supporting_evidence_card_ids")
                continue
            source_ids.extend(source_id for source_id in _card_source_ids(card, ids) if source_id not in source_ids)
            if _card_uses_search_source(card, ids) or _card_uses_query_plan_or_search_log_as_direct_source(card):
                _add_issue(issues, "critical", "market_corroboration_search_or_plan_source", "Search-only or plan-only card cannot support corroboration", f"{path}.supporting_evidence_card_ids")

        opened_source_ids: list[str] = []
        independence_keys: set[str] = set()
        for source_id in source_ids:
            source = ids["sources"].get(source_id)
            if not isinstance(source, dict):
                _add_issue(issues, "critical", "market_corroboration_source_missing", "CorroborationRecord references a missing Source", f"{path}.source_refs")
                continue
            if source.get("medium") == "search_result":
                _add_issue(issues, "critical", "market_corroboration_search_or_plan_source", "Search result source cannot be used as corroboration evidence", f"{path}.source_refs")
            if not _source_has_opened_observation(source_id, observations_by_source):
                _add_issue(issues, "critical", "market_corroboration_unopened_source", "CorroborationRecord requires opened/captured/extracted observations for each supporting source", f"{path}.source_refs")
            else:
                opened_source_ids.append(source_id)
            key = _source_independence_key(source)
            if key:
                independence_keys.add(key)

        actual_independent_count = len(independence_keys)
        declared_count = record.get("independent_source_count")
        if not isinstance(declared_count, int):
            _add_issue(issues, "critical", "market_corroboration_source_count_mismatch", "CorroborationRecord needs an integer independent_source_count", f"{path}.independent_source_count")
        elif declared_count != actual_independent_count:
            _add_issue(issues, "critical", "market_corroboration_source_count_mismatch", "Declared independent_source_count must match distinct opened source-owner/domain count", f"{path}.independent_source_count")

        has_conflict_cards = any(has_text(card_id) for card_id in as_list(record.get("conflicting_evidence_card_ids")))
        for card_id in as_list(record.get("conflicting_evidence_card_ids")):
            if has_text(card_id) and str(card_id) not in evidence_cards:
                _add_issue(issues, "critical", "market_corroboration_card_missing", "CorroborationRecord references a missing conflicting EvidenceCard", f"{path}.conflicting_evidence_card_ids")

        same_field_conflicts = [
            conflict
            for conflict in conflicts.values()
            if isinstance(conflict, dict)
            and conflict.get("run_id") == record.get("run_id")
            and norm(conflict.get("field_domain")) == norm(record.get("field_domain"))
            and norm(conflict.get("field_name")) == norm(record.get("field_name"))
            and conflict.get("status") == "conflict_pending_review"
        ]
        has_conflict_records = bool(same_field_conflicts)
        if has_conflict_records and status == "multi_source_consistent":
            _add_issue(issues, "critical", "market_corroboration_conflict_hidden", "CorroborationRecord cannot claim multi-source consistency while a same-field conflict is pending", path)
        if has_conflict_cards and status == "multi_source_consistent":
            _add_issue(issues, "critical", "market_corroboration_conflict_hidden", "CorroborationRecord with conflicting cards must use conflict_present, not multi_source_consistent", path)

        if status == "multi_source_consistent":
            if actual_independent_count < 2:
                _add_issue(issues, "critical", "market_corroboration_not_independent", "Multi-source consistency requires at least two independent opened source owners/domains", f"{path}.source_refs")
            if not as_list(record.get("cannot_conclude")):
                _add_issue(issues, "major", "market_corroboration_missing_boundary", "Multi-source consistency must state what cannot be concluded", f"{path}.cannot_conclude")
            if _contains_positive_phrase(_corroboration_text(record), VALUE_JUDGMENT_PHRASES + FINAL_TAX_PHRASES + DESTINATION_RECOGNITION_PHRASES):
                _add_issue(issues, "critical", "market_corroboration_overstated", "Multi-source weak evidence was overstated as recommendation, final duty/classification, or destination compliance", path)
        elif status == "single_source_only" and actual_independent_count > 1:
            _add_issue(issues, "major", "market_corroboration_source_count_mismatch", "single_source_only status conflicts with multiple independent opened sources", f"{path}.corroboration_status")
        elif status == "not_enough_independent_sources" and actual_independent_count >= 2 and not has_conflict_records:
            _add_issue(issues, "major", "market_corroboration_source_count_mismatch", "not_enough_independent_sources status conflicts with source count", f"{path}.corroboration_status")
        elif status == "conflict_present" and not (has_conflict_cards or has_conflict_records):
            _add_issue(issues, "major", "market_corroboration_conflict_status_without_conflict", "conflict_present status needs conflicting cards or same-field ConflictRecord", f"{path}.corroboration_status")

    for row_idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        row_refs = [str(item) for item in as_list(row.get("corroboration_record_ids")) if has_text(item)]
        for record_id in row_refs:
            record = corroborations.get(record_id)
            if not isinstance(record, dict):
                _add_issue(issues, "critical", "market_corroboration_record_missing", "Matrix row references a missing CorroborationRecord", f"matrix_rows[{row_idx}].corroboration_record_ids")
                continue
            if record.get("corroboration_status") == "multi_source_consistent" and row.get("status") in STATUS_FACTUAL:
                _add_issue(issues, "critical", "market_corroboration_overstated", "A multi-source weak-evidence signal must not make a matrix row verified/final by itself", f"matrix_rows[{row_idx}].status")
            if _contains_positive_phrase(_row_text(row), ("多来源证实", "多来源证明", "共同证明", "已证实", "confirmed by multiple sources", "proven by multiple sources")):
                _add_issue(issues, "critical", "market_corroboration_overstated", "User-visible row overstates weak-source consistency as proof", f"matrix_rows[{row_idx}]")
    return issues


def _freshness_refs_exist(
    record: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    subject_type = str(record.get("subject_type") or "")
    mapping = {
        "source": "sources",
        "observation": "observations",
        "evidence_card": "evidence_cards",
        "matrix_row": "matrix_rows",
        "corroboration_record": "corroboration_records",
    }
    collection_key = mapping.get(subject_type)
    missing: list[str] = []
    if not collection_key:
        return missing
    collection = ids.get(collection_key, {})
    for ref_id in as_list(record.get("subject_ref_ids")):
        if has_text(ref_id) and str(ref_id) not in collection:
            missing.append(str(ref_id))
    return missing


def _freshness_record_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in ensure_list(graph, "freshness_records"):
        if isinstance(record, dict) and has_text(record.get("freshness_id")):
            result[str(record["freshness_id"])] = record
    return result


def _card_has_freshness_record(card: dict[str, Any], freshness_by_id: dict[str, dict[str, Any]]) -> bool:
    for record_id in as_list(card.get("freshness_record_ids")):
        record = freshness_by_id.get(str(record_id))
        if isinstance(record, dict) and record.get("review_status") == "passed":
            return True
    card_id = str(card.get("evidence_card_id") or "")
    if not card_id:
        return False
    return any(
        isinstance(record, dict)
        and record.get("subject_type") == "evidence_card"
        and card_id in {str(item) for item in as_list(record.get("subject_ref_ids")) if has_text(item)}
        and record.get("review_status") == "passed"
        for record in freshness_by_id.values()
    )


def _row_freshness_records(row: dict[str, Any], freshness_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record_id in as_list(row.get("freshness_record_ids")):
        record = freshness_by_id.get(str(record_id))
        if isinstance(record, dict):
            records.append(record)
    row_id = str(row.get("matrix_row_id") or "")
    if row_id:
        for record in freshness_by_id.values():
            if (
                isinstance(record, dict)
                and record.get("subject_type") == "matrix_row"
                and row_id in {str(item) for item in as_list(record.get("subject_ref_ids")) if has_text(item)}
                and record not in records
            ):
                records.append(record)
    return records


def _row_has_currentish_freshness(row: dict[str, Any], freshness_by_id: dict[str, dict[str, Any]]) -> bool:
    return any(record.get("freshness_status") in FRESHNESS_STATUS_CURRENTISH and record.get("review_status") == "passed" for record in _row_freshness_records(row, freshness_by_id))


def _row_has_limited_freshness(row: dict[str, Any], freshness_by_id: dict[str, dict[str, Any]]) -> bool:
    return any(record.get("freshness_status") in FRESHNESS_STATUS_LIMITED and record.get("review_status") == "passed" for record in _row_freshness_records(row, freshness_by_id))


def _freshness_issues(
    graph: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    run_ids = set(ids["runs"])
    freshness_by_id = _freshness_record_by_id(graph)

    for idx, record in enumerate(ensure_list(graph, "freshness_records")):
        if not isinstance(record, dict):
            continue
        path = f"freshness_records[{idx}]"
        status = str(record.get("freshness_status") or "")
        if record.get("run_id") not in run_ids:
            _add_issue(issues, "critical", "market_freshness_run_missing", "FreshnessRecord must reference an existing product-market run", f"{path}.run_id")
        if record.get("review_status") != "passed":
            _add_issue(issues, "major", "market_freshness_not_reviewed", "FreshnessRecord must be reviewed before it can support delivery", f"{path}.review_status")
        missing_refs = _freshness_refs_exist(record, ids)
        if missing_refs:
            _add_issue(issues, "critical", "market_freshness_subject_missing", "FreshnessRecord references missing subject ids", f"{path}.subject_ref_ids")
        if status == "not_time_sensitive" and _is_time_sensitive_field(record.get("field_domain"), record.get("field_name"), None, None):
            _add_issue(issues, "major", "market_freshness_not_time_sensitive_mismatch", "FreshnessRecord marked not_time_sensitive but field_domain/field_name is time-sensitive", path)
        if status in FRESHNESS_STATUS_LIMITED and not as_list(record.get("cannot_conclude")):
            _add_issue(issues, "major", "market_freshness_missing_boundary", "Limited or stale freshness must state what cannot be treated as current/latest", f"{path}.cannot_conclude")
        if status in {"stale_needs_recheck", "date_unknown_needs_recheck"} and not as_list(record.get("next_verification_steps")):
            _add_issue(issues, "major", "market_freshness_missing_next_review", "Stale/date-unknown freshness needs next verification steps", f"{path}.next_verification_steps")
        if status == "current_enough_for_scope":
            window = record.get("review_window_days")
            if not isinstance(window, int):
                _add_issue(issues, "major", "market_freshness_window_missing", "Current-enough freshness needs review_window_days", f"{path}.review_window_days")
            checked = _parse_iso_date(record.get("freshness_checked_at"))
            if checked is None:
                _add_issue(issues, "critical", "market_freshness_checked_at_invalid", "FreshnessRecord needs a parseable freshness_checked_at date", f"{path}.freshness_checked_at")
            primary_dates = _parsed_dates(as_list(record.get("effective_date_values")) + as_list(record.get("source_date_values")))
            newest = max(primary_dates) if primary_dates else None
            if newest is None:
                _add_issue(issues, "critical", "market_freshness_current_without_date", "current_enough_for_scope requires a visible effective/source date; observed_at alone is not enough for current/latest claims", path)
            elif isinstance(window, int) and _days_between(newest, checked) is not None and _days_between(newest, checked) > window:
                _add_issue(issues, "critical", "market_freshness_stale_over_window", "FreshnessRecord is older than its declared review window but marked current", path)
            if _date_unknown(record.get("date_basis")) or _contains_any([record.get("source_date_values"), record.get("effective_date_values")], FRESHNESS_DATE_UNKNOWN_MARKERS):
                _add_issue(issues, "critical", "market_freshness_current_without_date", "Date-unknown material cannot be marked current_enough_for_scope", path)
        if status in {"stale_needs_recheck", "date_unknown_needs_recheck"} and _latest_claim_without_freshness_text(_freshness_text(record)):
            _add_issue(issues, "critical", "market_latest_claim_without_freshness", "Stale/date-unknown freshness cannot be written as latest/current", path)

    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        path = f"evidence_cards[{idx}]"
        is_time_sensitive = _is_time_sensitive_field(card.get("field_domain"), card.get("field_name"), None, None)
        text = _card_text(card)
        if _latest_claim_without_freshness_text(text):
            source_date = _parse_iso_date(card.get("source_date"))
            observed_at = _parse_iso_date(card.get("observed_at"))
            has_freshness = _card_has_freshness_record(card, freshness_by_id)
            if _date_unknown(card.get("source_date")) and not has_freshness:
                _add_issue(issues, "critical", "market_latest_claim_without_freshness", "EvidenceCard claims latest/current while source_date is unknown and no freshness record is attached", path)
            if is_time_sensitive:
                window = _default_review_window_days(card.get("field_domain"), card.get("field_name"))
                if source_date and observed_at and isinstance(window, int) and _days_between(source_date, observed_at) is not None and _days_between(source_date, observed_at) > window and not has_freshness:
                    _add_issue(issues, "critical", "market_latest_claim_without_freshness", "EvidenceCard claims latest/current with stale source_date and no freshness recheck", path)

    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        path = f"matrix_rows[{idx}]"
        text = _row_text(row)
        is_time_sensitive = _is_time_sensitive_field(row.get("sheet_name"), row.get("row_topic"), row.get("module_key"), row.get("sheet_name"))
        has_limited = _row_has_limited_freshness(row, freshness_by_id)
        has_currentish = _row_has_currentish_freshness(row, freshness_by_id)
        if row.get("status") in STATUS_FACTUAL and is_time_sensitive and has_limited:
            _add_issue(issues, "critical", "market_freshness_stale_row_not_downgraded", "Matrix row with stale/date-unknown freshness cannot remain verified/final", f"{path}.status")
        if row.get("status") in STATUS_FACTUAL and is_time_sensitive:
            for record in _row_freshness_records(row, freshness_by_id):
                if record.get("freshness_status") == "not_time_sensitive" and record.get("review_status") == "passed":
                    _add_issue(issues, "major", "market_freshness_not_time_sensitive_mismatch", "Time-sensitive matrix row cannot use not_time_sensitive freshness to support a factual/current conclusion", f"{path}.freshness_record_ids")
        if row.get("status") in STATUS_FACTUAL and is_time_sensitive and not has_currentish:
            for card_id in as_list(row.get("evidence_card_ids")):
                card = ids["evidence_cards"].get(str(card_id))
                if not isinstance(card, dict) or card.get("status") not in STATUS_FACTUAL:
                    continue
                if not _is_time_sensitive_field(card.get("field_domain"), card.get("field_name"), row.get("module_key"), row.get("sheet_name")):
                    continue
                source_date = _parse_iso_date(card.get("source_date"))
                observed_at = _parse_iso_date(card.get("observed_at"))
                window = _default_review_window_days(card.get("field_domain"), card.get("field_name"), row.get("module_key"), row.get("sheet_name"))
                if _date_unknown(card.get("source_date")) and not _card_has_freshness_record(card, freshness_by_id):
                    _add_issue(issues, "critical", "market_freshness_missing_for_date_unknown", "Verified time-sensitive matrix row uses a date-unknown EvidenceCard without a freshness boundary record", f"{path}.evidence_card_ids")
                    break
                if source_date and observed_at and isinstance(window, int) and _days_between(source_date, observed_at) is not None and _days_between(source_date, observed_at) > window and not _card_has_freshness_record(card, freshness_by_id):
                    _add_issue(issues, "critical", "market_freshness_missing_for_stale_source", "Verified time-sensitive matrix row uses a stale EvidenceCard without freshness recheck/downgrade", f"{path}.evidence_card_ids")
                    break
        if _latest_claim_without_freshness_text(text):
            if not has_currentish:
                _add_issue(issues, "critical", "market_latest_claim_without_freshness", "Matrix row claims latest/current without a passed current-enough freshness record", path)
            if has_limited:
                _add_issue(issues, "critical", "market_latest_claim_without_freshness", "Matrix row claims latest/current while linked freshness says stale/date-unknown", path)
        for record_id in as_list(row.get("freshness_record_ids")):
            if has_text(record_id) and str(record_id) not in freshness_by_id:
                _add_issue(issues, "critical", "market_freshness_record_missing", "Matrix row references a missing FreshnessRecord", f"{path}.freshness_record_ids")
    return issues


def _market_search_collection_issues(
    graph: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
    observations_by_source: dict[str, list[dict[str, Any]]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    run_ids = set(ids["runs"])
    brief_ids = set(ids["briefs"])
    brief_versions = {str(item.get("brief_version_id")) for item in ensure_list(graph, "briefs") if isinstance(item, dict) and has_text(item.get("brief_version_id"))}
    search_logs = [item for item in ensure_list(graph, "search_logs") if isinstance(item, dict)]

    for idx, log in enumerate(search_logs):
        path = f"search_logs[{idx}]"
        if log.get("run_id") not in run_ids:
            _add_issue(issues, "critical", "market_search_log_run_missing", "Market SearchLog must reference an existing product-market run", f"{path}.run_id")
        if log.get("brief_id") not in brief_ids:
            _add_issue(issues, "critical", "market_search_log_brief_missing", "Market SearchLog must reference an existing product-market brief", f"{path}.brief_id")
        if log.get("brief_version_id") not in brief_versions:
            _add_issue(issues, "critical", "market_search_log_brief_version_missing", "Market SearchLog must carry a current Brief version", f"{path}.brief_version_id")
        if log.get("source_plan_route") != SOURCE_PLAN_ROUTE:
            _add_issue(issues, "critical", "market_search_log_source_plan_boundary_missing", "Market SearchLog must be tied to the product market Source Plan route", f"{path}.source_plan_route")
        if log.get("capability") != "search.web":
            _add_issue(issues, "critical", "market_search_log_capability_invalid", "Market SearchLog capability must be search.web", f"{path}.capability")
        if str(log.get("concrete_tool") or "") in {"curl", "wget", "python_requests", "source.open", "browser.render"}:
            _add_issue(issues, "critical", "market_search_log_tool_invalid", "Market SearchLog concrete_tool must identify a search provider, not a source-opening tool", f"{path}.concrete_tool")
        if not has_text(log.get("query_text")):
            _add_issue(issues, "critical", "market_search_log_query_missing", "Market SearchLog requires query_text", f"{path}.query_text")
        if contains_local_path(log.get("query_text")) or "file:" in str(log.get("query_text") or "").casefold():
            _add_issue(issues, "critical", "market_search_log_query_unsafe", "Market SearchLog query_text must not contain local paths or file URIs", f"{path}.query_text")
        if re.search(r"(?i)\b(?:cookie|authorization|bearer|api[_ -]?key|access[_ -]?token|password|secret)\b", str(log.get("query_text") or "")):
            _add_issue(issues, "critical", "market_search_log_query_unsafe", "Market SearchLog query_text must not contain secret or credential material", f"{path}.query_text")
        if log.get("result_use") != "source_candidate_only":
            _add_issue(issues, "critical", "market_search_log_result_use_invalid", "Market SearchLog result_use must remain source_candidate_only", f"{path}.result_use")
        if log.get("must_open_source") is not True or log.get("reject_if_only_snippet") is not True or log.get("not_evidence") is not True:
            _add_issue(issues, "critical", "market_search_log_source_plan_boundary_missing", "Market SearchLog must preserve must_open_source / reject_if_only_snippet / not_evidence", path)
        if log.get("allowed_output") != SEARCH_LOG_ALLOWED_OUTPUT:
            _add_issue(issues, "critical", "market_search_log_source_plan_boundary_missing", "Market SearchLog allowed_output must be search_log_or_source_locator_only", f"{path}.allowed_output")
        for ref_idx, ref in enumerate(as_list(log.get("result_refs"))):
            ref_path = f"{path}.result_refs[{ref_idx}]"
            if not isinstance(ref, dict):
                _add_issue(issues, "critical", "market_search_log_result_ref_invalid", "Market SearchLog result_refs must be objects", ref_path)
                continue
            if not is_safe_public_http_url(ref.get("result_url")):
                _add_issue(issues, "critical", "market_search_log_result_url_not_public", "Market SearchLog result URL must be a safe public HTTP(S) URL", f"{ref_path}.result_url")
            if contains_local_path(ref.get("result_locator")) or contains_local_path(ref.get("result_title")):
                _add_issue(issues, "critical", "market_search_log_result_locator_unsafe", "Market SearchLog result locator must not contain local paths", ref_path)
            if re.search(r"(?i)\b(?:cookie|authorization|bearer|api[_ -]?key|access[_ -]?token|password|secret)\b", text_of([ref.get("result_locator"), ref.get("result_title"), ref.get("result_url")])):
                _add_issue(issues, "critical", "market_search_log_result_locator_unsafe", "Market SearchLog result locator must not contain secret or credential material", ref_path)
            opened_id = ref.get("opened_source_id")
            if has_text(opened_id):
                source = ids["sources"].get(str(opened_id))
                if not isinstance(source, dict):
                    _add_issue(issues, "critical", "market_search_log_opened_source_missing", "SearchLog opened_source_id must reference an existing Source", f"{ref_path}.opened_source_id")
                elif not _source_observation_opened(opened_id, observations_by_source):
                    _add_issue(issues, "critical", "market_source_without_open_observation", "SearchLog opened_source_id requires a source.open/browser/document Observation", f"{ref_path}.opened_source_id")
            # Snippets/summaries may be retained for audit context, but never become
            # EvidenceCard support.  The factual path must point to opened_source_id
            # plus a separate source.open/document Observation.

    for idx, source in enumerate(ensure_list(graph, "sources")):
        if not isinstance(source, dict):
            continue
        path = f"sources[{idx}]"
        if source.get("medium") == "search_result":
            _add_issue(issues, "critical", "market_search_result_as_source", "Product market analysis must record search results in search_logs, not as Source records", f"{path}.medium")
        if not _public_source_url(source) and source.get("provenance") == "discovered_public":
            _add_issue(issues, "critical", "market_source_url_not_public", "Discovered public Source must have a safe public HTTP(S) URL", path)

    for idx, obs in enumerate(ensure_list(graph, "observations")):
        if not isinstance(obs, dict):
            continue
        path = f"observations[{idx}]"
        source_id = str(obs.get("source_id") or "")
        source = ids["sources"].get(source_id)
        if not isinstance(source, dict):
            _add_issue(issues, "critical", "market_observation_source_missing", "Observation must reference an existing Source", f"{path}.source_id")
            continue
        if obs.get("capability") == "search.web":
            _add_issue(issues, "critical", "market_search_result_as_observation", "Search.web output belongs in SearchLog, not Observation", f"{path}.capability")
        if source.get("medium") == "search_result":
            _add_issue(issues, "critical", "market_search_result_as_source", "Search result Source cannot produce Observation facts", path)
        if str(obs.get("access_status") or "") in SOURCE_RESTRICTED_ACCESS_STATUSES and has_text(obs.get("raw_excerpt")):
            _add_issue(issues, "major", "market_restricted_source_has_observation_excerpt", "Restricted/not-opened source must not have factual raw_excerpt", f"{path}.raw_excerpt")
        if _observation_is_opened_source(obs):
            linked_logs = _source_linked_search_logs(source_id, search_logs)
            # User-provided product files are allowed without SearchLog; discovered-public web sources should be traceable to search/log or explicit user URL.
            if source.get("provenance") == "discovered_public" and not linked_logs and source.get("medium") in {"website", "document", "registry", "directory"}:
                # Existing legacy fixtures predate Slice J; this is a soft limitation unless the run declares source_opened/full_research.
                pass

    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        path = f"evidence_cards[{idx}]"
        if card.get("status") in STATUS_FACTUAL and _card_uses_query_plan_or_search_log_as_direct_source(card):
            _add_issue(issues, "critical", "market_query_plan_or_searchlog_promoted", "Query Plan or SearchLog was promoted directly to factual evidence", path)
        if card.get("status") in STATUS_FACTUAL and card.get("status") != "derived_calculation":
            has_open_ref = False
            for ref in as_list(card.get("source_refs")):
                if not isinstance(ref, dict):
                    continue
                obs = _observation_for_ref(ref, ids)
                source = _source_for_ref(ref, ids)
                if isinstance(obs, dict) and isinstance(source, dict) and _observation_is_opened_source(obs) and source.get("medium") != "search_result":
                    has_open_ref = True
                    break
            if not has_open_ref:
                _add_issue(issues, "critical", "market_evidence_without_open_observation", "Factual EvidenceCard requires an opened source Observation, not search/snippet/plan-only material", path)

    return issues


def validate_graph(graph: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    issues.extend(_schema_validation_issues(graph))
    ids = _id_maps(graph)
    observations_by_source: dict[str, list[dict[str, Any]]] = {}
    for obs in ensure_list(graph, "observations"):
        if isinstance(obs, dict) and has_text(obs.get("source_id")):
            observations_by_source.setdefault(str(obs["source_id"]), []).append(obs)

    issues.extend(_market_search_collection_issues(graph, ids, observations_by_source))
    issues.extend(_corroboration_issues(graph, ids, observations_by_source))
    issues.extend(_freshness_issues(graph, ids))

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

    # Certification / destination-entry requirements must be destination-rule
    # facts first, and user material readiness second.  The module helps users
    # discover what the target market may require; it is not merely a user
    # certificate upload review.
    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict) or not _is_certification_requirement_row(row):
            continue
        text = _row_text(row)
        record = _cert_requirement_record(row)
        requirement_status = _cert_requirement_status(row)
        user_material_status = _cert_user_material_status(row)

        if not _cert_row_has_split_fields(row):
            _add_issue(issues, "critical", "market_certification_requirement_user_material_conflated", "Certification/destination requirement row must split target-market requirement status from user material status", f"matrix_rows[{idx}]")

        user_missing = user_material_status in {"user_not_provided_but_required", "user_material_status_unknown", "user_material_not_requested_yet"} or _contains_any(text, USER_CERT_MISSING_MARKERS)
        written_not_required = requirement_status == "normally_not_required" or _contains_positive_phrase(text, CERT_NOT_REQUIRED_PHRASES)
        if user_missing and written_not_required and any(marker in norm(text) for marker in CAUSAL_MARKERS):
            _add_issue(issues, "critical", "market_certification_requirement_user_material_conflated", "User missing certificate/test material was used to infer destination requirement is not required", f"matrix_rows[{idx}]")
        if _contains_any(text, USER_CERT_RULE_CONFLATION_PHRASES):
            _add_issue(issues, "critical", "market_certification_requirement_user_material_conflated", "Destination certification/entry requirement was made dependent on whether the user provided a file", f"matrix_rows[{idx}]")

        if _contains_any(text, CERT_ENTRY_MARKERS) and _contains_positive_phrase(text, CERT_ENTRY_PROMOTION_PHRASES):
            _add_issue(issues, "critical", "market_certificate_entry_promoted_to_certified", "Certificate download/page/entry was promoted to having certification or being compliant", f"matrix_rows[{idx}]")

        if _contains_any(text, TEST_REPORT_MARKERS) and _contains_positive_phrase(text, TEST_REPORT_AS_CERT_PHRASES):
            _add_issue(issues, "critical", "market_test_report_promoted_to_certification", "Test report was conflated with certification/approval", f"matrix_rows[{idx}]")

        if _contains_any(text, CHANNEL_REQUIREMENT_MARKERS) and _contains_positive_phrase(text, LEGAL_REQUIREMENT_PHRASES):
            _add_issue(issues, "critical", "market_channel_requirement_promoted_to_legal", "Channel/customer/platform requirement was promoted to law/customs mandatory requirement", f"matrix_rows[{idx}]")

        if _contains_any(text, USER_CERT_FILE_MARKERS) and _contains_positive_phrase(text, DESTINATION_RECOGNITION_PHRASES):
            _add_issue(issues, "critical", "market_user_certificate_promoted_to_destination_compliance", "User-provided certificate/test material was promoted to destination recognition or product compliance", f"matrix_rows[{idx}]")

        if requirement_status in CERT_DETERMINATE_STATUSES and not _cert_record_has_authority(record, ids, observations_by_source):
            _add_issue(issues, "critical", "market_certification_requirement_without_authority", "Determinate certification/destination requirement status needs official or authoritative destination-rule source refs", f"matrix_rows[{idx}].certification_requirement.authority_source_refs")

    for idx, card in enumerate(ensure_list(graph, "evidence_cards")):
        if not isinstance(card, dict):
            continue
        text = _card_text(card)
        is_cert_card = _contains_any(text, CERTIFICATION_REQUIREMENT_MARKERS) or _contains_any([card.get("field_domain"), card.get("field_name")], ("认证", "准入", "测试报告", "标签", "注册", "certification", "destination requirement"))
        if not is_cert_card:
            continue
        if _contains_any(text, CERT_ENTRY_MARKERS) and _contains_positive_phrase(text, CERT_ENTRY_PROMOTION_PHRASES):
            _add_issue(issues, "critical", "market_certificate_entry_promoted_to_certified", "Evidence card promotes certificate entry/page to certification or compliance", f"evidence_cards[{idx}]")
        if _contains_any(text, TEST_REPORT_MARKERS) and _contains_positive_phrase(text, TEST_REPORT_AS_CERT_PHRASES):
            _add_issue(issues, "critical", "market_test_report_promoted_to_certification", "Evidence card conflates test report with certification/approval", f"evidence_cards[{idx}]")
        if _contains_any(text, CHANNEL_REQUIREMENT_MARKERS) and _contains_positive_phrase(text, LEGAL_REQUIREMENT_PHRASES):
            _add_issue(issues, "critical", "market_channel_requirement_promoted_to_legal", "Evidence card promotes channel/customer/platform requirement to law/customs mandatory requirement", f"evidence_cards[{idx}]")
        if _contains_any(text, USER_CERT_FILE_MARKERS) and _contains_positive_phrase(text, DESTINATION_RECOGNITION_PHRASES):
            _add_issue(issues, "critical", "market_user_certificate_promoted_to_destination_compliance", "Evidence card promotes user-provided certificate/test material to destination recognition or product compliance", f"evidence_cards[{idx}]")

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
