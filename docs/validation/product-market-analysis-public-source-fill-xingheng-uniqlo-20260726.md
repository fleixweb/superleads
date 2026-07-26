# 产品出海市场分析：Xing Heng / UNIQLO 公开来源补齐验证（2026-07-26）

## 1. 本次验证边界

| 项目 | 本次处理 |
|---|---|
| 目标 | 用公开来源复核用户给出的两个真实产品样本，并把可核实字段、候选字段、待确认字段拆开 |
| 样本 A | 越南原产锂电：Xing Heng `48V20Ah` LiFePO4 电池包，Design No. `BAT001.02`，出口美国 |
| 样本 B | 中国原产纺织品：UNIQLO Men's Corduroy Overshirt，Product ID `470177`，出口美国 |
| 不做 | 不输出 Google Trends、市场规模、销售建议、是否值得进入、最终 HS/HTS 归类、最终税额、承运承诺或法律意见 |
| 证据规则 | ChatGPT/外部模型搜索结果和用户转述只作为候选线索；事实只来自本次已打开网页、已抽取 PDF、已渲染/检查 PDF 页面或官方法规/税则数据 |
| 能力记录 | `source.open`：公开 GET；`document.extract`：PDF 文本抽取；`image.inspect`：扫描 PDF 页面人工视觉核验；`search.web` 未用于事实支撑 |
| 观察日期 | 2026-07-26 |

## 2. 来源矩阵

### 2.1 产品与制造商来源

| ID | 来源 | 类型 | URL / 定位 | 本次用途 | 状态 |
|---|---|---|---|---|---|
| XH-1 | Xing Heng 首页 | 官网页面 | `https://www.xingheng.vn/` | 公司、越南制造声明、工厂地址、LiFePO4 产品范围 | 已打开 |
| XH-2 | Xing Heng 48V20Ah 产品页 | 官网页面 | `https://www.xingheng.vn/lithium-battery/48v20ah` | 型号、Design No.、额定参数、证书/测试报告下载入口 | 已打开 |
| XH-3 | 48V20Ah Registration certificate | 官方页链接 PDF | Google Drive file ID `1rCuU7kQ10WXVPMnc6DWbCsATaJSFEpGX` | Vietnam Register 证书、制造商/装配厂、QCVN 91 | 已抽取 |
| XH-4 | 48V20Ah Test report | 官方页链接 PDF | Google Drive file ID `1Vv-wOx2x9eexoEHpKf6EchFbRHlQ8f8P` | Vietnam Register 测试报告范围、报告号、测试对象 | 已渲染检查 |
| UQ-1 | UNIQLO US Product page | 品牌官网产品页 | `https://www.uniqlo.com/us/en/products/E470177-000/00` | 产品 ID、成分、产地、RN、洗护、尺码与产品说明 | 已打开 |

### 2.2 美国法规、标签与税则来源

| ID | 来源 | 类型 | URL / 定位 | 本次用途 | 状态 |
|---|---|---|---|---|---|
| REG-1 | eCFR Title 49 Part 173 | 官方法规 XML | `https://www.ecfr.gov/api/versioner/v1/full/2026-07-22/title-49.xml?part=173` | 49 CFR §173.185 锂电运输、UN 38.3、100Wh 小型锂电限值 | 已打开 |
| REG-2 | eCFR Title 49 Part 172 | 官方法规 XML | `https://www.ecfr.gov/api/versioner/v1/full/2026-07-22/title-49.xml?part=172` | Hazardous Materials Table 中 UN3480 / UN3481 与 Class 9 | 已打开 |
| HTS-1 | USITC HTS search `8507.60.00` | 官方税则 JSON | `https://hts.usitc.gov/reststop/search?keyword=8507.60.00` | 锂离子蓄电池候选 HTSUS 与税率口径 | 已打开 |
| FTC-1 | FTC Textile/Wool labeling guide | 官方指南 | `https://www.ftc.gov/business-guidance/resources/threading-your-way-through-labeling-requirements-under-textile-wool-acts` | 纺织标签：纤维成分、原产地、制造商/进口商/RN | 已打开 |
| FTC-2 | FTC Care Labeling Rule guide | 官方指南 | `https://www.ftc.gov/business-guidance/resources/clothes-captioning-complying-care-labeling-rule` | 服装护理标签、洗涤或干洗说明 | 已打开 |
| CBP-1 | CBP country of origin marking | 官方指南 | `https://www.cbp.gov/trade/rulings/informed-compliance-publications/marking-country-origin-us-imports` | 美国进口原产地标识目的与服装附加标签提示 | 已打开 |
| HTS-2 | USITC HTS search `6205.20.20` | 官方税则 JSON | `https://hts.usitc.gov/reststop/search?keyword=6205.20.20` | 男式/男童棉制非针织衬衫候选 HTSUS 与税率口径 | 已打开 |

## 3. 样本 A：Xing Heng 48V20Ah LiFePO4 电池包

### 3.1 已核实产品档案

| 字段 | 已核实内容 | 来源 | 状态 | 备注 |
|---|---|---|---|---|
| 制造商 | Pin Xing Heng Technology Joint Stock Company / Công ty cổ phần công nghệ pin Xing-Heng | XH-1、XH-3、XH-4 | 已核实 | 英文/越文名称来自官网与证书/报告 |
| 产品版本 | `48V20Ah` | XH-2、XH-3、XH-4 | 已核实 | 官网产品页、证书、测试报告一致 |
| Design No. | `BAT001.02` | XH-2、XH-3、XH-4 | 已核实 | 用户给出的 `BAT001.02` 得到复核 |
| 产品类型 | Lithium-ion / LiFePO4 电池产品；测试报告对象为电摩/电动轻便摩托牵引用电池 | XH-1、XH-4 | 已核实 | 用途影响运输和进口核验路径 |
| 额定电压 | 48 V | XH-2、XH-3 | 已核实 | 证书写 Nominal Voltage-capacity：48 V - 20 Ah |
| 额定容量 | 20 Ah | XH-2、XH-3 | 已核实 | 官网产品页有 `Rated capacity: 20AhV` 排版异常；证书支持 20 Ah |
| 派生能量 | 960 Wh | 由 48 V × 20 Ah 计算 | 派生计算 | 非厂商单独标注值；正式运输文件仍需厂家 Wh 标识或技术文件确认 |
| 最大电流 | ≤30 A | XH-2 | 已核实 | 官网产品页字段为 Current |
| 重量 | 7.5 ±0.2 kg | XH-2 | 已核实 | 官网写 `7.5 ±0,2 Kg` |
| 尺寸 | 183 × 156 × 265 mm | XH-2 | 已核实 | 官网产品页 |
| 外壳材料 | Plastic | XH-2 | 已核实 | 官网产品页 |
| 温度范围 | -10℃ ~ 60℃ | XH-2 | 已核实 | 官网产品页 |
| 设计寿命 / 循环寿命 | 10+ years；约 1200 cycles | XH-2 | 已核实 | 商业/技术说明，不等于运输或法规结论 |
| 质保 | 36 months | XH-2 | 已核实 | 官网产品页 |
| 工厂/装配地址 | Ngõ/Lane 2, Road 3, Phu Lo, Soc Son, Hanoi City, Vietnam | XH-1、XH-3、XH-4 | 已核实 | 官网英文地址和证书越文地址表达一致 |
| 越南制造声明 | 官网称 Xing Heng 电池产品 produced/manufactured in Vietnam；证书列出越南制造商与装配厂 | XH-1、XH-3 | 公开来源已核实 | 可作为公开制造来源证据；正式申报仍需 COO、发票/合同或供应链文件 |

### 3.2 证书与测试报告边界

| 文件 | 文件显示内容 | 能支持什么 | 不能支持什么 |
|---|---|---|---|
| Registration certificate | Vietnam Register Type Approval Certificate；No. `10349/VAQ06-04/24-00`；QCVN 91:2019/BGTVT；产品 48V20Ah / BAT001.02；日期 2024-06-17 | 支持该型号有越南登记/型式批准证书、制造商/装配厂、额定 48V-20Ah | 不能当作 UN38.3、SDS、美国进口认证、美国海关归类或最终原产地裁定 |
| Test report | Vietnam Register Test Report No. `1074/BCTN-PX/24`；测试对象为电摩/电动轻便摩托牵引用电池；依据 QCVN 91:2019/BGTVT | 支持该报告范围、报告号、测试对象、部分测试项通过 | 不能当作 UN Manual of Tests and Criteria 38.3 报告；不能证明可空运/快递/拼箱 |

### 3.3 美国运输与税则候选核验

| 项目 | 公开来源结果 | 状态 | 影响 |
|---|---|---|---|
| 49 CFR §173.185 | 锂电池运输要求涉及 UN Manual of Tests and Criteria Part III, sub-section 38.3；制造商/分销商需提供 test summary；小型锂离子电池限值为 cell 20Wh / battery 100Wh | 官方法规已核实 | 960Wh 派生值超过 100Wh 小型电池限值，不能按小型锂电例外输出 |
| UN 编号 / 品名 | Hazardous Materials Table 中 `Lithium ion batteries` 为 UN3480；`contained in equipment` 或 `packed with equipment` 为 UN3481；均为 Class 9 | 条件化参考 | 单独电池包、与设备同箱、装入设备三种情形必须分别判断 |
| 候选 HTSUS | `8507.60.00` 描述为 Lithium-ion batteries；USITC 显示 General 3.4%、Other 40%，并有 Chapter 99 脚注 | 候选，待专业确认 | 最终 10 位统计后缀、是否触发 Chapter 99 或其他措施，必须按实物、原产地与报关日有效税表确认 |

### 3.4 仍必须保留的缺口

| 字段 | 当前结果 | 状态 | 下一步资料 |
|---|---|---|---|
| UN38.3 | 公开页有 Registration certificate 和 Test report，但二者范围不是 UN38.3 | 待技术资料确认 | 向制造商索取对应型号/版本的 UN38.3 test summary / report |
| SDS / MSDS | 本次公开来源未见 | 待技术资料确认 | 向制造商索取对应型号、版本、签发日期的 SDS |
| 包装方式 | 未见内外包装、短路防护、标签、件数、净重、毛重 | 待技术资料确认 | 包装说明、装箱单、危险品申报资料 |
| 运输情形 | 未知是单独电池、与设备同箱还是装入设备 | 待业务确认 | 决定 UN3480 / UN3481 路径 |
| 实际起运港/机场 | 只验证了制造/装配地在河内 Soc Son；装运港未公开 | 待业务确认 | 订舱单、提单、出口报关单 |
| 出口申报国 | 未公开 | 待业务确认 | 越南制造不等于必然从越南出口申报 |
| 最终美国 HTSUS 与税额 | 仅有候选 `8507.60.00` | 待专业确认 | 实物、用途、10 位后缀、原产地、报关日有效税表、Chapter 99 |

## 4. 样本 B：UNIQLO Men's Corduroy Overshirt Product ID 470177

### 4.1 已核实产品档案

| 字段 | 已核实内容 | 来源 | 状态 | 备注 |
|---|---|---|---|---|
| 产品名称 | Men's Corduroy Overshirt / Corduroy Overshirt | UQ-1 | 已核实 | UNIQLO 美国官网产品页 |
| Product ID | `470177` | UQ-1 | 已核实 | 页面 Description 与 Details 均可见 |
| 原产 / Production | China | UQ-1 | 已核实 | 页面 Production 区域写明 `Production: China` |
| 产品类别 | MEN / Shirts / Casual Shirts / Others | UQ-1 | 已核实 | 平台分类，不等于 CBP 最终归类 |
| 面料说明 | Full 100% cotton fabric made from thick slub yarn | UQ-1 | 已核实 | 产品 Features |
| 织物说明 | 8-wale corduroy made with 100% cotton | UQ-1 | 已核实 | 可作为机织灯芯绒方向的工作判断；组织图、经纬密度、克重未公开 |
| 成分 | Body: 100% Cotton / Trim: 100% Cotton | UQ-1 | 已核实 | 不覆盖纽扣、缝线等未公开辅料 |
| 款式 / 用途 | Relaxed regular fit；可单穿或作为外搭层 | UQ-1 | 已核实 | 产品说明称可 over tees/sweaters/sweatshirts 或 stand alone |
| 尺码范围 | XXS、XS、S、M、L、XL、XXL、3XL | UQ-1 | 已核实 | 页面可见尺码 |
| RN | 139864 | UQ-1 | 已核实 | 页面 Materials / Care 区域 |
| 洗护 | Machine wash cold, gentle cycle, Dry clean | UQ-1 | 已核实 | 页面 Washing instructions |
| 动物材料 | 已公开 Body/Trim 均为 Cotton；未公开纽扣、缝线等辅料 | UQ-1 | 部分已核实 | 不能据此证明“全成分无动物材料” |

### 4.2 美国标签与税则候选核验

| 项目 | 公开来源结果 | 状态 | 影响 |
|---|---|---|---|
| 纺织标签 | FTC 指南覆盖 fiber content、country of origin、manufacturer/importer/dealer identification / RN | 官方指南已核实 | UNIQLO 页面已披露成分、Production、RN；实物标签仍需照片/样衣核验 |
| 护理标签 | FTC Care Labeling Rule 指南说明服装需附护理说明，规则涉及洗涤或干洗指令 | 官方指南已核实 | 页面有洗护文字，但不能代替实物 sewn-in care label 核验 |
| 原产地标识 | CBP 指南说明原产地标识用于告知美国 ultimate purchaser；服装还可能有面料成分和洗护标签要求 | 官方指南已核实 | `Production: China` 是产品页公开信息；进口实物仍需符合标识规则 |
| 候选 HTSUS | `6205.20.20` 位于男式/男童非针织棉制衬衫路径；USITC 显示 General 19.7%、Other 45%，并有 Chapter 99 脚注 | 候选，待专业确认 | 若 CBP 认定为外套/夹克而非衬衫，归类需重判；最终 10 位统计后缀也待确认 |

### 4.3 仍必须保留的缺口

| 字段 | 当前结果 | 状态 | 下一步资料 |
|---|---|---|---|
| 制造工厂 | 官网只披露 Production: China，未披露具体工厂 | 待供应链资料确认 | 供应商声明、采购订单、发票、工厂资料 |
| 装运城市/港口 | 未公开 | 待业务确认 | 提单、装箱单、出口报关单、订舱资料 |
| 单件重量 / 克重 / 完整尺寸 | 未公开 | 待技术资料确认 | 样衣规格书、BOM、测量表、面料 TDS |
| 实物标签文案 | 官网披露页面信息，但未见水洗标/产地标照片 | 待实物核验 | 实物标签照片或供应商标签稿 |
| 辅料成分 | 纽扣、缝线等未公开 | 待技术资料确认 | BOM、辅料清单 |
| 最终 HTSUS 与税额 | 仅有候选 `6205.20.20` | 待专业确认 | 实物款式、织造方式、性别/年龄段、10 位后缀、原产地、报关日有效税表、Chapter 99 |

## 5. 对两个样本的交叉复核结论

| 维度 | Xing Heng 48V20Ah | UNIQLO 470177 | 产品模块应如何处理 |
|---|---|---|---|
| 产品版本明确度 | 型号、Design No.、规格在官网/证书/报告之间一致 | Product ID、名称、成分、Production 在官网可见 | 两者均适合进入端到端样本池 |
| 原产地证据 | 有公开越南制造声明、越南制造商/装配厂证书 | 官网明确 `Production: China` | 可展示为“公开来源已核实”；正式贸易申报仍保留 COO/发票/供应链文件缺口 |
| 关键技术资料 | V/Ah/尺寸/重量较完整，但缺 UN38.3/SDS/包装 | 成分/款式/RN/洗护较完整，但缺实物标签/辅料/重量 | 属性矩阵能启动，但法规/税费必须条件化 |
| 官方法规/税则 | 可触发锂电危规与 8507.60.00 候选 | 可触发纺织标签与 6205.20.20 候选 | 官方来源只支持候选路径，不支持最终结论 |
| 不得输出 | “已具备 UN38.3”“可按普通货运输”“最终税率就是 3.4%” | “一定归 6205.20.20”“最终税率就是 19.7%”“标签已完全合规” | 报告中必须把候选、待确认、已核实拆开 |

## 6. 对产品出海市场分析功能的新增验收点

| 验收点 | 要求 |
|---|---|
| 外部模型结果处理 | 用户提供的 ChatGPT 搜索表只进入“候选线索”；系统必须重新打开来源或抽取文档后再落事实 |
| 原产地证据等级 | 区分公开生产声明、制造商证书、贸易文件、官方原产地裁定；不得把工厂地址直接等同最终海关原产地 |
| 认证/测试报告边界 | Vietnam Register / QCVN 91 报告不得自动升级为 UN38.3 或 SDS；报告范围必须逐项读取 |
| 候选 HTSUS 边界 | USITC 搜索可给候选标题、税率口径与脚注，但不能替代实物归类、10 位统计后缀和 Chapter 99 核验 |
| 表格化交付 | 两个样本均应以产品档案、法规触发、税则候选、运输触发、待确认材料矩阵交付，避免长篇主观文字 |
