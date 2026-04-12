# Clinical Expert Review SKILL

## 概述
本SKILL用于对AI生成的MDT（多学科诊疗）报告进行临床专家级审查，评估其临床一致性、报告质量、错误率和物理可追溯性。
**版本要求：V3.0（已启用双源溯源与安全拒答豁免机制）**

## 审查协议（6-Phase Protocol）

### 专家级审查铁律 (Expert Review Directives)
1. **严禁外貌协会**：不得因报告排版美观、使用了表格或 Markdown 特效而提高 MQR 评分。质量评估必须且仅基于医疗逻辑的完整性与证据的硬核程度。
2. **对未经物理验证的数字保持零容忍**：在评估 S_dose 和 S_scheme 时，如果对应的治疗剂量或参数没有紧跟 [Local...] 或 [PubMed...] 等确凿的循证锚点，必须将其视为“潜在幻觉”，对应的评分不得高于 2/4。
3. **医疗信源洁癖**：任何将普通互联网资讯站点（如百度、好大夫在线等非同行评议平台）作为临床推荐依据的行为，必须在 Phase 5 (CER) 中直接判定为 Major Error 或 Critical Error。

### Phase 1: Patient Context Analysis（患者上下文分析）
- 提取患者基本信息、肿瘤类型、分期、治疗史。
- 识别关键临床决策点。
- **强制输入源**：必须读取 `patient_<patient_id>_input.txt` 以建立内部事实基准（Ground Truth）。

### Phase 2: Citation Verification（引用验证）
- 验证所有临床声明的引用来源。
- **与审计日志交叉核对**：对于系统生成的报告，必须检查其引用标签（如 [PubMed: PMID XXX]、[Local: ...]）是否在沙盒底层的 `workspace/sandbox/execution_logs/session_*_structured.jsonl` 中有对应的 tool_call 记录。若无底层执行记录，判定为虚假引用 (Hallucinated Citation)，并在 CER 中严厉惩罚。

### Phase 3: CCR - Clinical Consistency Rate（临床一致性率）
评估维度（0-4分）：
- S_line: 治疗线判定准确性。
- S_scheme: 首选方案选择合理性。
- S_dose: 剂量参数准确性。
- S_reject: 排他性论证充分性。
- S_align: 临床路径一致性。

### Phase 4: MQR - MDT Quality Rate（MDT报告质量率）
评估维度（0-4分）：
- S_complete: 8模块完整性。
- S_applicable: 模块适用性判断。
- S_format: 结构化程度。
- S_citation: 引用格式规范性。
- S_uncertainty: 不确定性处理。

### Phase 5: CER - Clinical Error Rate（临床错误率）
- **Critical错误** (w=3.0): 可能危及生命（如推荐禁忌症药物、篡改核心病理特征）。
- **Major错误** (w=2.0): 显著影响治疗效果（如剂量偏离>20%、引入商业非权威信源）。
  - **新增（V3.0）**: 出现Tier 3C商业引用（非白名单Web），直接+2.0 (Major Error)。
- **Minor错误** (w=1.0): 轻微影响治疗质量（如篡改患者年龄/性别但不影响治疗、随访瑕疵）。
  - **新增（V3.0）**: 篡改患者输入核心事实（年龄、病理、突变），记Minor错误。
- **公式**: CER = min((Σ w_j × n_j) / 15, 1.0)

### Phase 6: PTR - Physical Traceability Rate（物理可追溯率）V3.0

#### 双源溯源（Dual-Source Traceability）机制
MDT 报告的声明必须区分为“外部医疗循证”与“内部患者事实”。

#### 声明分类与权重
- **Tier 1A (外部权威循证 - 权重 1.0)**：包含 [PubMed: PMID XXX]、[OncoKB: XXX]、[Local: 文件, Section: 章节]。必须在 structured.jsonl 中有对应 tool_call。
- **Tier 1B (内部患者事实 - 权重 1.0)**：包含 [Patient Input: 既往史/症状等] 或 [Local: 患者输入文件, Line X]。必须与输入文件一致。容忍医学同义转换（如“脑转移手术”→“开颅手术”）；禁止核心数值篡改（如年龄、靶点阴阳性）。
- **Tier 2 (不可验证泛引用 - 权重 0.3)**：[Guideline: NCCN]（无具体文件或章节定位）。
- **Tier 3 (开放网络白名单 - 权重 0.1)**：[Web: URL]（仅限 .gov, .edu, who.int, 国际药企官网）。
- **Tier 3C (商业网站黑名单 - 权重 0.0)**：[Web: 非白名单]。PTR计0分，CER追加+2.0惩罚。
- **Invalid (参数知识 - 权重 0.0)**：[Parametric Knowledge: ...]，不计入得分。

#### 安全拒答声明豁免机制（关键！）
以下声明属于合规防御行为，必须从 PTR 的总声明数（分母）中剔除：
- "未找到相关循证证据"、"具体参数需临床医师决定"、"未在检索证据中明确"、"需临床医师基于患者个体情况决定"、"未检索到"、"证据不足"、"建议多学科讨论"。
- 或任何明确触发“零幻觉红线”、诚实声明缺乏证据支持、且未编造虚假引用的医学断言。
- **判定标准**：正则/语义匹配，无需特定标签。

#### 计算公式（V3.0 修正）
PTR = (Σ Tier 1A, 1B, 2, 3得分) / (总声明数 - 豁免声明数)
*注：分子只加正分，PTR 范围限制在 [0, 1]。*

## CPI计算
CPI = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)

## 计算精度规范
所有指标结果必须保留3位小数（CCR和MQR保留1位）。
- CPI, CER, PTR: 3位小数 (如 0.857)
- CCR, MQR: 1位小数 (如 4.0)

## 引用溯源检查SOP
1. **提取引用**：识别 [PubMed...], [OncoKB...], [Local...], [Web...], [Patient Input...] 等标签。
2. **获取文档**：读取 baseline JSON 或 execution_logs 中的结构化 tool_call 记录。
3. **匹配验证**：核对文件名及章节标题。特殊情况：“既往史”、“病理诊断”必为患者输入数据 (Tier 1B)。

## 度量计算示例 (V3.0)

### CCR示例
**CCR: 3.2/4.0**
- S_line: 4/4; S_scheme: 3/4; S_dose: 3/4; S_reject: 3/4; S_align: 3/4

### PTR示例
**PTR: 0.687**
- Tier 1A: 20处 × 1.0 = 20.0
- Tier 1B: 10处 × 1.0 = 10.0
- Tier 2: 3处 × 0.3 = 0.9
- 总引用得分: 30.9
- 原始总声明数: 47; 豁免声明数: 2
- 最终分母: 45
- PTR = 30.9 / 45 = 0.687

### CER示例
**CER: 0.133**
- Major错误: 0处; Minor错误: 2处 (w=1.0); 总权重: 2; CER = min(2/15, 1.0) = 0.133

## 强制落盘要求
1. **单次落盘**：每个患者审查后必须立即写入 `work_<patient_id>/review_results.json` 和 `clinical_expert_review_report.md`。
2. **结构规范**：JSON 必须包含 5 个指标。Markdown 必须包含摘要表格。
3. **文件路径**：`analysis/reviews_blind_20260411/work_<patient_id>/`

## 审查数据来源说明
**输入数据**:
- Baseline方法: RAG V2 / WebSearch_LLM
- Baseline文件: `baseline/set1_results_v2/<method>/<patient_id>_baseline_results.json`
- 患者输入: `patient_input/Set-1/<patient_id>/patient_<patient_id>_input.txt`