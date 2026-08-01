# 产品出海市场分析：前置资料索取问题的分析报告

面向执行者（Codex）的核实与修改依据。
分析基于 commit `9a5bafb`，工作区仅 `scripts/export_product_market_workbook.py` 有未提交改动（与本问题无关）。

本报告的每一条结论都标注了可独立复现的位置或命令。**请先核实，再修改；如果任何一条复现不出来，以复现结果为准，不要照抄本报告的改动建议。**

---

## 0. 问题陈述

期望行为：

> 用户给出「产品 + 目标国家」，AI 负责去查市场、准入、税费、出口、物流和风险。

观察到的行为：

> 用户要先提交产品档案、BOM、照片、IOR、Incoterms、起运港、入境日期，AI 才开始工作。

造成三个后果：把研究任务退回给用户；把「市场分析」做成了「申报前合规复核」；把内部数据模型字段变成了用户的前置负担。

---

## 1. 核心发现

**机器层（脚本 + Source Pack 注册表）根本不拦截。拦截全部来自给模型读的自然语言规则。**

这一条改变了修复的性质：不需要动数据模型、不需要新增状态维度、不需要改脚本。**需要改的是 4 处 prose，加 1 处字段名文档。**

---

## 2. 复现：机器层不拦截

### 2.1 完整输入（你的 9504 case）

```bash
cat > /tmp/b2.json <<'EOF'
{"product_name":"电子游戏机","candidate_hs_hts":"9504.50.0000",
 "origin_country_or_region":"CN","export_declaration_country":"CN",
 "destination_country_or_region":"US"}
EOF
python3 scripts/plan_product_market_sources.py --input /tmp/b2.json --format json
```

实测结果：

```
ok = true
selected_pack_ids = 5
  seed_us_market_access_general / seed_us_import_tax_general /
  seed_us_origin_proof_general / seed_market_signal_global_to_us /
  seed_product_original_sources
query_plan = 8 步
missing_required_fields = []
```

生成的查询串包括：

- `United States official product safety labeling requirements 电子游戏机 general_goods`
- `USITC HTS 9504.50.0000 电子游戏机 CN`
- `CBP proof of origin rules CN 9504.50.0000 电子游戏机`
- `Google Trends 电子游戏机 United States 2004 present`
- `United States official public holidays calendar 电子游戏机 gift season`
- `United States recent port customs disruption official notice general_goods`
- `<manufacturer_or_brand:待确认> <model_or_sku:待确认> 电子游戏机 manual TDS SDS test report`
- `CN official customs export requirements <product/HS>`

**没有任何一步要求先补 BOM、照片、IOR、Incoterms、入境日期。**

### 2.2 极简输入（只有产品 + 目标国）

```bash
printf '{"product_name":"蓝牙音箱","destination_country_or_region":"US"}' > /tmp/bmin.json
python3 scripts/plan_product_market_sources.py --input /tmp/bmin.json --format json
```

实测结果：

```
ok = true, packs = 5, query_plan = 7 步, missing_required_fields = []
```

连 HTS、原产国、出口申报国都不给，**依然不拦**。产生 4 条 warning，全部是「别猜」而非「去要」：

| warning code | 原文 |
|---|---|
| `market_source_plan_missing_export_country` | 未设置出口申报国；默认出口国应由用户可见设置，不从原产国或卖方国猜。 |
| `market_source_plan_export_country_visible_default_needed` | 出口申报国未设置；未来 UI 应显示默认出口国并允许用户改，不从原产地自动推断。 |
| `market_source_plan_origin_country_unknown` | 原产国/制造来源未知；税费、COO、贸易救济和标签查询只能保留原产地缺口。 |
| `market_source_plan_departure_node_unknown` | 实际起运地/港口/机场未知；物流计划不得猜默认港口。 |

### 2.3 结论

「本轮默认贸易口径：原产/出口国=中国，目标市场=美国，可直接改」这个交互，**已经作为设计意图写在脚本的 warning 里了**（`market_source_plan_export_country_visible_default_needed`）。这不是一个新需求，是一个已经被机器层认可、但被文案层盖住的需求。

---

## 3. 拦截点定位（需要修改的 4 处）

以下 4 处全部是给模型读的自然语言。按影响力从大到小排列。

### 3.1 `spec/10-product-outbound-market-analysis-contract.md:29` —— 最硬，在产品合同层

```
| 产品名称与明确版本 | 形成研究对象 | 仅能形成范围澄清，不进行实质结论 |
```

「不进行实质结论」是最强的阻断措辞，且位于产品合同（上游）。**只改下游文案而不改这一格，行为会被拽回去。**

建议改成：

```
| 产品名称与明确版本 | 形成研究对象 | 缺型号时按品类级分析；结论标注为条件性，不给最终归类/最终税率 |
```

### 3.2 `spec/18-...-skill-copy-and-user-entry.md:117`

```
| 缺产品 | 必问，无法开始实质分析 |
```

建议改成：

```
| 缺产品 | 有品类或 HS 即可开始品类级分析；型号缺失只降低结论粒度，不阻断 |
```

### 3.3 `shared/references/product-outbound-market-intake.md:49` 与 `spec/18-...:94`（同一句，两处）

```
请尽量给产品型号、材质/成分、用途、规格，或者直接给产品页/PDF；
否则只能先做"待确认项清单"，不能给准入、税费和物流的确定路径。
```

建议改成：

```
产品资料不足时，先做品类级市场与准入分析，并明确哪些结论是条件性的；
不得直接给最终归类、最终税率或已清关结论。
```

（注意：两个文件是同一段文案的两份副本，**必须同步改**，否则会出现新的规则分裂。）

### 3.4 `skills/analyzing-product-outbound-market/SKILL.md:33-39` —— capture 清单被读成 ask 清单

第 33 行 `Capture the minimum Brief:` 之下列了 26 个字段：贸易前提 5 项（第 37 行）+ 触发项 13 项（第 38 行）+ 可选材料 8 项（第 39 行）。第 40 行才说「最多问三个问题」。

模型会把「需要建模的字段」读成「需要向用户索取的清单」。这是本问题里「内部数据模型泄漏到用户界面」的直接来源。

建议：把第 33 行的动词从 `Capture` 改为 `Model internally（不向用户逐项索取）`，并在其后加一条显式负面清单（见 §6.4）。

---

## 4. 与原诊断不一致的地方（重要）

### 4.1 IOR / Incoterms / 入境日期 / 交易价值 / broker —— 不在任何规则里

全仓库检索（`--include=*.md --include=*.py --include=*.json`，排除 `tmp/`）：

- `IOR`：0 处规则命中
- `Incoterms`：仅 `spec/16:77` 一处，原文是「第一期可为空，但不能被默认猜测」
- `入境日期`、`交易价值`：0 处
- `broker`：仅出现在 eval 夹具和 source pack 里，且都是「需 broker 复核」的**结论限定词**，不是入口索取项

**结论：这些追问是模型自发生成的，不是任何规则或脚本要求的。**

推论：只改 §3 的 4 处文案，不一定能修掉这个具体行为。**必须补一条显式负面清单**（§6.4），否则模型会继续用自己的外贸常识补齐它认为"严谨"该问的东西。

### 4.2 「起运节点暴露给用户」—— 现状其实是对的

`skills/using-superleads/SKILL.md:35` 的用户面模板写的是：

> 默认出口申报国：{用户指定/中国默认}；原产国、起运地、最终税号和技术文件不足时会**保留待确认**。

这是「提及并挂起」，不是「索取」，正是期望行为。**问题不在提及，在索取。修改时不要误伤这段模板。**

---

## 5. 复现过程中发现的两个新问题

### 5.1 brief 字段名无处可查（疑似真正的放大器）

复现时第一次把税号写成 `hs_or_hts_candidates`，脚本实际读的是 `candidate_hs_hts`（见 `scripts/plan_product_market_sources.py:465-487` 的 `_inputs_used_for_template` 与 alias 表）。字段名不匹配时脚本**静默丢弃**，查询串退化为：

```
USITC HTS <candidate_hs_hts:待确认> 电子游戏机 CN
```

而 brief 字段的规范名，全套 spec 里没有任何一处正面文档化（`spec/16` 只在 eval 夹具文件名中间接出现过一次 `market_fail_candidate_htsus_as_final_rate.json`）。

**因果假设（需核实）：**

```
模型传错 brief 字段名
  → planner 输出满屏 <xxx:待确认>
  → 模型判断"资料严重不足"
  → 转身向用户索取，并按自身外贸常识补齐 IOR / Incoterms / 入境日期
```

如果成立，这解释了为什么追问的**内容**超出了任何规则的措辞范围。

**核实方法**：对比两次 planner 输出——一次用正确字段名，一次用近似但错误的字段名（如 `hs_code` / `hts` / `product_model`），看 `<...:待确认>` 占位符数量差异。

**修改建议**：在 `spec/16` 或 SKILL.md 里正面列出 brief 的规范字段名；或在脚本中对未识别的顶层键发出 warning（`market_brief_unknown_field`），避免静默丢弃。

### 5.2 behavioral eval 是空壳，不执行任何 prompt

`evals/run_evals.py:670` 起，`__BEHAVIORAL_CHECK__` 的完整实现是：

```python
if not isinstance(payload, list) or not payload:
    raise AssertionError("behavioral guardrail prompts must be a non-empty list")
for idx, item in enumerate(payload):
    if not item.get("prompt") or not item.get("must_not") or not item.get("expected"):
        raise AssertionError(f"behavioral prompt {idx} lacks prompt/must_not/expected")
```

它只校验 JSON 有没有 `prompt` / `must_not` / `expected` 三个键，**从不把 prompt 喂给任何模型**。

因此 `evals/behavioral/product-market-route-prompts.json` 里那 9 条"护栏"今天一条都没在跑，本报告 §7 的验收标准也**没有任何现成的自动化手段可以验证**。往 `evals/behavioral/` 里加夹具不会带来验证能力。

**修改建议（择一）**：
- (a) 接一个真实模型执行层，让 behavioral 夹具真的跑；
- (b) 在 `evals/run_evals.py` 和 `evals/behavioral/README` 里明确标注「本套仅做 schema 校验，不测行为」，避免误以为有护栏；
- (c) 短期先做人工 UAT 清单。

---

## 6. 修改方案

### 6.1 三级模式：采纳，但不要建成状态机

三级分析（快速市场分析 / 产品与合规深化 / 申报前复核）是正确方向。但**不要新增 `analysis_level` 状态维度穿透 contract / workbook / evidence / eval 四层**——§2 已证明机器层本来就支持 Level 1，那是一个月的工作量去修一个四行文案的 bug。

实现方式：写成 SKILL.md 里的一段升级触发规则即可。

### 6.2 命名冲突：不要用 Level 1/2/3

`spec/10-...:143` 的 §4.1.3「原产地证据等级」已经占用了 `L0 / L1 / L2 / L3 / L4` 表示**证据强度**：

| 等级 | 含义 |
|---|---|
| L0 | 无来源或只有模型/搜索摘要 |
| L1 | 产品页公开写明 Production / Made in |
| L2 | 制造商证书、测试报告 |
| L3 | COO、发票、提单等订单级文件 |
| L4 | 主管机关、海关预裁定 |

再引入 Level 1/2/3 表示**分析深度**，同一份 spec 里两套 L 语义必然串。

**建议命名**：`快速市场分析` / `产品与合规深化` / `申报前复核`（中文全称），或 `S1 / S2 / S3`。

### 6.3 品类级 ≠ 降低证据标准（必须写进规则）

最大风险：`快速市场分析` 被读成「资料少也可以直接说」，从而架空 `spec/14`（证据边界）、`spec/24`（原产地证明）、`spec/29`（认证校准）三份文件。

必须在规则里明确写下：

> 品类级分析改变的是**结论挂靠的对象粒度**（品类/HS 章节 vs 具体型号），**不改变证据标准**。
> 每一条用户可见事实仍必须来自本轮真实打开的来源；没有来源就写 `not_executed`，不得用"品类级"作为免开来源的理由。

缺这一段，本次修改会把前几轮攒的护栏一起推平。

### 6.4 显式负面清单（针对 §4.1）

在 `skills/analyzing-product-outbound-market/SKILL.md` 的 intake 段落加入：

> 首轮不得向用户索取：IOR / 进口商记录、Incoterms / 贸易术语、交易价值与数量、预计入境日期、报关行信息、BOM、产品照片、实际起运港、证书原件、测试报告、SDS、UN38.3。
> 这些只在用户明确要求"最终税率"、"正式报关"、"能否清关"、"安排实际运输"时才进入索取范围。
> 首轮阻断性问题只有两个：目标国家/地区、产品是什么（品类名 / 类别 / HS 均可，不要求型号）。

### 6.5 默认贸易口径的用户可见形式

用户只应看到：

```
本轮默认贸易口径：
  原产/出口国：中国
  目标市场：美国
如果实际出口国不是中国，直接告诉我，我会替换默认口径。
```

内部仍分别建模 `origin_country` / `export_declaration_country` / `departure_country` / `manufacturing_details`（`spec/10 §2.1` 要求它们分别建模，这一条保留不动）。

非中国用户：默认值必须能被一句话覆盖（德国 / 印度 / 越南等），不得反问确认。

### 6.6 改动清单汇总

| # | 文件 | 位置 | 动作 |
|---|---|---|---|
| 1 | `spec/10-...-contract.md` | 第 29 行表格格 | 改「不进行实质结论」→ 品类级 + 条件性 |
| 2 | `spec/18-...-user-entry.md` | 第 117 行 | 改「必问，无法开始实质分析」 |
| 3 | `spec/18-...-user-entry.md` | 第 94 行 | 改「只能先做待确认项清单」 |
| 4 | `shared/references/product-outbound-market-intake.md` | 第 49 行 | 同上，**必须与 #3 同步** |
| 5 | `skills/analyzing-product-outbound-market/SKILL.md` | 第 33 行 | `Capture` → 内部建模，不逐项索取 |
| 6 | `skills/analyzing-product-outbound-market/SKILL.md` | 第 40 行后 | 新增 §6.4 负面清单 |
| 7 | `skills/analyzing-product-outbound-market/SKILL.md` | intake 段 | 新增 §6.3 品类级≠降标准 |
| 8 | `spec/16` 或 SKILL.md | 新增 | brief 规范字段名文档（§5.1） |
| 9 | `evals/run_evals.py` / behavioral README | — | 标注或修复空壳问题（§5.2） |

不需要改：任何脚本逻辑、数据模型、Source Pack 注册表、workbook 契约、导出器。

---

## 7. 验收标准

### 7.1 放行方向（原始 8 条）

1. 只给「产品 + 目标国家」，直接产出有用报告，不先发资料清单。
2. 只给 HTS Code + 中国 + 美国，不先发资料清单。
3. 缺 BOM / 照片 / IOR / Incoterms 时仍继续分析。
4. 非中国用户输入印度 / 越南 / 德国时，一句话覆盖中国默认值，不反问确认。
5. 只有用户要求"最终税率 / 正式申报 / 能否清关 / 安排运输"时才请求详细资料。
6. 未知项出现在"可能改变结论的变量"，而非"开始前必须补齐"。
7. 不把"海关原产国 / 制造来源 / SKU 级原产证据 / 起运节点"作为前置索取项。
8. 保持"不确定"，但不因此停止工作。

### 7.2 配平方向（必须同时通过，否则视为回归）

原 8 条全部指向"别拦"。**只测这一个方向，必然把 spec 14/24/29 的护栏推平**——`evals/fixtures/` 现有 78 个 market 夹具，多数是防夸大的。补充：

9. 品类级分析中，**不得**给出最终 HTS 归类。
10. 品类级分析中，**不得**给出最终税率或应缴税额（`market_candidate_hs_promoted_to_final` 必须仍然触发）。
11. 品类级分析中，**不得**输出"已合规 / 无需认证 / 不是危险品 / 可按普通货运输"。
12. 用户未提供证书，**不得**被写成目标国不需要认证。
13. **不得**猜起运港或默认港口（`market_source_plan_departure_node_unknown` 的约束仍成立）。
14. 未采集的域（趋势、价格、节假日、外部因素）仍必须显式标 `not_executed`，不得因"品类级"而省略。
15. **不得**输出市场进入判断（`建议进入` / `值得开发` / `市场潜力高`）。

### 7.3 验证方式提醒

见 §5.2：**当前没有能执行 prompt 的 eval 通道。** 上述 15 条在修好 behavioral 执行层之前只能人工 UAT。请不要用"加了夹具、run_evals 通过"来声称验收完成——那只证明 JSON 结构合法。

---

## 8. 修改优先级

| 优先级 | 项 | 理由 |
|---|---|---|
| P0 | #1–#4（4 处文案） | 直接阻断源，改完即见效 |
| P0 | #6（负面清单） | §4.1 证明只改文案不足以治 IOR/Incoterms |
| P1 | #7（品类级≠降标准） | 不加会造成护栏回归 |
| P1 | #8（brief 字段名） | §5.1 疑似真正放大器，需先核实假设 |
| P2 | #5（capture 措辞） | 长期防复发 |
| P2 | #9（eval 空壳） | 不修则无法验证任何一条验收标准 |

---

## 附录：本报告使用的检索与复现命令

```bash
# 定位 4 处拦截点
grep -n "仅能形成范围澄清\|必问，无法开始实质分析\|只能先做" \
  spec/10-*.md spec/18-*.md shared/references/product-outbound-market-intake.md

# 确认 IOR / Incoterms 不在规则中
grep -rn "IOR\|Incoterms\|入境日期\|交易价值\|broker" \
  --include="*.md" --include="*.py" --include="*.json" . | grep -v "^./tmp/"

# 复现机器层不拦截（两个 case，见 §2）
python3 scripts/plan_product_market_sources.py --input /tmp/b2.json --format json
python3 scripts/plan_product_market_sources.py --input /tmp/bmin.json --format json

# 确认 behavioral eval 是空壳
sed -n '665,680p' evals/run_evals.py

# 确认 L0-L4 命名已被占用
sed -n '143,155p' spec/10-product-outbound-market-analysis-contract.md
```

---

## 9. 复核追加：字段别名修复后的脚本层回归

用户让 Claude 复核后发现：§3–§6 的 prose 修复方向是对的，但为修复 §5.1 字段名静默丢弃而加入的 alias 机制引入了 3 个脚本层回归。该结论已在本仓库复现，并已补入 source-plan eval，不能再用“714/714 全绿”代表这类行为已覆盖。

### 9.1 P0：国家名规范化在查询串中失效

复现输入使用 `destination_country_or_region: "US"` 时，`brief_summary.target_country_or_region` 仍显示 `United States`，但 `query_strings` 曾退化为：

- `US official product safety labeling requirements ...`
- `Google Trends ... US 2004 present`

根因：`_brief_value()` 先解析别名并返回原始 `US`，导致 `_inputs_used_for_template()` 中只有 `value is None` 才走 `_country()` 的兜底分支失效。

修复要求：进入 query template 的 `target_country_or_region` / `destination_country_or_region` / `export_declaration_country` / `origin_country_or_region` / `departure_country_or_region` 都必须显式规范化，不能只在 summary 层规范化。

### 9.2 P1：Made in / manufacturing clue 不得消除原产国缺口

复现输入：

```json
{"product_name":"蓝牙音箱","made_in_country":"Vietnam","destination_country_or_region":"US"}
```

错误行为曾是：

- `brief_summary.origin_country_or_region = "Vietnam"`
- `market_source_plan_origin_country_unknown` warning 消失
- 由此可能触发越南原产 / 中越至美国物流前提

根因：`origin_country_or_region` alias 把 `production_country` / `manufacturing_country` / `made_in_country` / `coo_country` 都当作海关原产国。

修复要求：这些字段只能进入 `manufacturing_country_clue`，不得写入 `origin_country_or_region`，不得消除 origin gap warning，不得触发出口国或 COO 证明结论。

### 9.3 P2：产品身份标签和检索词必须分离

只给 HS/HTS 或 URL 线索时，`_brief_product_identity()` 的中文人话标签曾直接进入英文检索式，例如：

- `Google Trends 候选 HS/HTS 9504.50.0000 US 2004 present`
- `US official product safety labeling requirements 用户提供的产品资料线索 general_goods`

修复要求：

- summary / missing-field 判定可使用人话身份标签；
- query term 侧优先用产品名/品类/描述；
- 只有 HS/HTS 时用税号本身或留空；
- 只有 URL/PDF/图片线索时不得把“用户提供的产品资料线索”写进检索式。

### 9.4 新增自动化覆盖

新增 / 修改覆盖点：

- `evals/fixtures/source_plan_hts_alias_us_china_brief.json`：使用 `destination_country_or_region: "US"` + `hs_code`，验证查询串使用 `United States` 且不含 `候选 HS/HTS`。
- `evals/fixtures/source_plan_made_in_not_origin_brief.json`：验证 `made_in_country` 只进入 `manufacturing_country_clue`，`origin_country_or_region` 保持空，且 warning 保留。
- `evals/run_product_market_source_plan_evals.py`：新增 query string、warning code、brief summary 级断言，避免只看全局文本或 summary 而漏掉真实检索式回归。

复测命令：

```bash
python3 -m py_compile scripts/plan_product_market_sources.py evals/run_product_market_source_plan_evals.py
python3 evals/run_product_market_source_plan_evals.py --suite all
```
