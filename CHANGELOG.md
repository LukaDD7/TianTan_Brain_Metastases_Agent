# Changelog

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [2.4.4] - 2026-03-05

### 修复

#### 致命医学架构问题：指南优先级倒置
- **问题**：`parse_pdf`（本地 NCCN 指南）和 `pubmed_search`（零星文献）平行执行，导致 Agent 偷懒只查 PubMed
- **解决方案**：
  - 新增 `LocalGuidelinesManager` 智能路由管理器，自动匹配肿瘤类型与指南文件
  - 新增 `query_guideline_mandatory()` 强制指南查询（不可跳过）
  - 新增 `_analyze_guideline_coverage()` 防幻觉覆盖判定
  - 新增 `should_degrade_to_pubmed()` 降级触发器（仅当指南未覆盖或需反面证据时）
- **效果**：
  - ✅ 指南作为顶级证据（基石），强制执行
  - ✅ OncoKB 与指南并行作为顶级证据
  - ✅ PubMed 降级为补充证据（仅在必要时调用）
  - ✅ 打印明确警告日志，防止幻觉覆盖判定

### 新增

#### 智能指南路由（Smart Guideline Routing）
- 根据肿瘤类型（NSCLC、Melanoma、Breast 等）自动匹配最相关的 1-2 个指南文件
- 支持中英文肿瘤类型映射
- 优先返回 Practice Guidelines，其次返回 Review Articles
- 未匹配时使用 CNS 指南兜底

### 变更

#### `main_oncology_agent_v2.py` v2.4
- **参数变更**：移除 `guideline_pdf_path`，由 `LocalGuidelinesManager` 自动路由
- **证据层级**：
  ```
  顶级证据：OncoKB + 指南（并行）
  降级证据：PubMed（条件性调用）
  ```
- **强制流程**：
  1. 解析患者病历
  2. 【并行】查询 OncoKB + 强制查询指南
  3. 【条件】判定是否降级调用 PubMed
  4. 生成报告 + 验证

#### `run_full_workflow()` 函数
- **新签名**：`run_full_workflow(case_id, patient_pdf_path, gene_symbol, gene_variant, tumor_type, literature_keywords)`
- **智能路由**：根据 `tumor_type` 自动匹配指南
- **降级触发**：仅在指南未覆盖或需反面证据时调用 PubMed
- **日志增强**：打印明确的证据优先级和降级原因

### 文档

- **`ROADMAP.md`**：标记指南优先级重构为已完成
- **`CHANGELOG.md`**：记录本次致命修复详情

### 工程改进

- **Git 提交**：`fix: enforce guideline priority, PubMed as degraded evidence only`
- **版本号**：v2.3 → v2.4（重大架构变更）

---

## [2.4.3] - 2026-03-04

### 新增

#### 本地知识库集成
- **`LocalGuidelinesManager`** - 本地权威指南管理器类
  - 扫描 `/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/Guidelines/脑转诊疗指南/` 目录
  - 自动索引 21 个权威指南文件（9 个临床实践指南 + 12 个综述文章）
  - 生成 System Prompt 友好的指南索引格式
- **`scripts/run_batch_eval.py`** - 扩展批量评估脚本
  - 集成本地知识库扫描和索引功能
  - 添加 `LocalGuidelinesManager` 到 OncologyWorkflowForEval
  - 支持动态注入指南索引到 Agent System Prompt

#### 宽表格式转换
- **`scripts/prepare_test_cases.py`** - 数据预处理脚本
  - 将长表格式（127 行）转换为宽表格式（9 行）
  - 每行 = 1 个病例，包含所有特征字段
  - 添加预期结果列（expected_modality, expected_gene, expected_variant）

#### 批量测试完成
- **5 个真实病例测试** - 100% 通过
  - Clean Context 隔离验证通过
  - Eval 断言系统工作正常
  - 本地知识库集成成功
  - 生成完整的 Markdown 测试报告

### 修复

- **`skills/clinical_writer/scripts/generate_report.py`** - 修复模板写入问题
  - 第 468-469 行：不再将模板提示词写入报告文件
  - 只保存报告内容本身，不包含模板

### 文档

- **`docs/批量测试报告_20260304.md`** - 完整的批量测试报告
- **`docs/测试方案_10个真实病例.md`** - 10 个病例测试方案
- **`CLAUDE.md`** - 新增第 9 章"技能调优与测试规范"

---

## [2.4.2] - 2026-03-04

### 新增

#### 批量评估框架
- **`scripts/run_batch_eval.py`** - 完整的批量评估脚本
- **Clean Context 隔离机制**：每个 Case 独立实例化 `SkillRegistry` 和 `OncologyWorkflowForEval`，确保绝对的上下文隔离
- **Eval 断言系统**：`evaluate_case_result()` 函数实现 5 项自动化断言检查：
  1. 检查 `rejected_alternatives` 是否存在
  2. 检查有基因突变时是否调用 `query_variant`
  3. 检查 `systemic_management` 是否包含 `peri_procedural_holding_parameters`
  4. 检查是否有违禁词"术前准备"
  5. 统计技能调用次数
- **结果落盘**：自动生成 CSV 汇总报告，包含每个 Case 的 Pass/Fail 状态和详细指标

#### Trigger Description 重写
- **`skills/oncokb_query/scripts/query_variant.py`**：重写 `description` 为强触发器
  - 明确触发边界："当且仅当患者病历中明确提取到具体的基因突变信息"
  - 具体示例：EGFR L858R、BRAF V600E、KRAS G12C
  - 严禁行为："严禁凭自身记忆捏造基因变异信息"
- **`skills/pubmed_search/scripts/search_articles.py`**：重写 `description` 为强触发器
  - 明确触发场景：为 `rejected_alternatives` 寻找证据、补充 OncoKB 循证依据、查询罕见病例报告
  - 示例引导："手术切除：证据不足（PubMed 检索未发现支持性文献）"

### 测试

#### 批量评估测试通过
- **测试用例**：5 个模拟病例（交替：有突变/无突变）
- **通过率**：100% (5/5)
- **关键验证**：
  - 所有 Case 正确包含 `rejected_alternatives` ✅
  - 有突变的 Case 正确调用 `query_oncokb` ✅
  - 无突变的 Case 不误调用 `query_oncokb` ✅
  - 所有 Case 包含 `peri_procedural_holding_parameters` ✅
  - 无违禁词"术前准备" ✅
- **CSV 报告**：`workspace/eval_results/batch_eval_20260304_174901.csv`

### 工程改进

- **CLAUDE.md**：新增第 9 章"技能调优与测试规范"，将 Trigger Tuning 和 Clean Context 作为红线

---

## [2.4.1] - 2026-03-04

### 修复

#### 验证逻辑错误
- **修复 generate_report.py 第 550 行**：`_validate_with_template()` 方法中规则 6 的字符串匹配错误，"systemic_therapy" 包含 "surgery" 子串导致误判，改为精确匹配 "手术治疗" 或 "- modality: surgery"

### 测试

#### 全链路冒烟测试通过
- **OncoKB Query**：EGFR L858R 查询成功返回 Oncogenic 判定和 11 条治疗推荐
- **PubMed Search**：Melanoma Brain Metastases Immunotherapy 检索返回 2 篇文献（PMID 30655533，Nature Reviews Disease Primers 2019）
- **Clinical Writer Validation**：验证器成功拦截违禁词"术前准备"、缺失 rejected_alternatives 模块、缺失指南引用；合规报告验证通过

### 工程改进

- **CLAUDE.md**：新增第 8 章"强制状态同步协议"，要求代码修改后必须立即更新 CHANGELOG 和 ROADMAP
- **ROADMAP.md**：修正虚假完成状态，将 main_oncology_agent_v2.py 网状推理标记为"[ ] 已编码，待测试"，OncoKB/PubMed 集成标记为"高 ⚠️阻塞"

---

## [2.4.0] - 2026-03-04

### 新增

#### Order Sets 模板机制
- **`skills/clinical_writer/references/asco_nccn_order_set_template.json`** - 基于 NCCN CNS Cancers v3.2024 + ASCO Brain Mets Guideline 2022 的结构化输出模板
- **5 大核心模块**:
  - `admission_evaluation` - 入院评估与一般治疗（严禁"术前准备"等暗示性文字）
  - `primary_plan` - 首选治疗方案（手术/放疗/全身治疗，动态可选）
  - `systemic_management` - 后续治疗与全身管理
  - `follow_up` - 全程管理与随访计划
  - `rejected_alternatives` - 被排除的治疗方案（强制至少 1 项）
  - `agent_trace` - Agent 推理追踪记录（Skill 调用历史 + 证据来源）
- **动态可选模板声明**: 不适用的治疗模块必须设为 null，严禁捏造不适用的治疗细节

#### 专家级临床字段约束
- **激素管理强化**: 类固醇药物（如地塞米松）必须填写 `tapering_schedule`（减量计划）
- **围手术期停药安全**: 全身治疗药物必须填写 `peri_procedural_holding_parameters`（如"SRS 治疗前后需停用 BRAF 抑制剂 3 天"）
- **分子病理送检**: 手术方案必须包含 `molecular_pathology_orders`（基因检测医嘱，如 BRAF V600E、NGS panel）

#### Pydantic 输出 Schema
- **15+ 个子类** 强制约束输出格式
- `AdmissionEvaluation` - 入院评估
- `PrimaryPlanSurgery` - 手术治疗（含 surgical_adjuncts、molecular_pathology_orders）
- `PrimaryPlanRadiotherapy` - 放射治疗
- `PrimaryPlanSystemic` - 全身治疗（含 dosage/cycle_length/interval/duration）
- `SystemicManagement` - 后续管理
- `FollowUpPlan` - 随访计划
- `RejectedAlternatives` - 排他性分析
- `AgentTrace` - 推理追踪

### 变更

#### generate_report.py v2.3
- 新增 `load_order_set_template()` 模板加载器
- 新增 `generate_template_prompt()` 提示词生成器
- 验证规则扩展至 7 项
- `MDTReportGenerator` 类增加模板缓存机制

#### validate_report.py v2.3
- 同步 Order Sets 模板验证逻辑
- 新增 10 项验证规则：
  - 模块完整性（5 大核心模块）
  - 指南引用格式
  - 禁忌文字检查（"术前准备"）
  - 排他性分析至少 1 项
  - 分子病理送检检查（如包含手术）
  - 激素减量计划检查（如使用类固醇）

#### main_oncology_agent_v2.py v2.3
- **整合 OncoKB 和 PubMed API Skill**
  - `query_variant_oncogenicity()` - 查询基因变异致癌性和药物敏感性
  - `search_supporting_literature()` - 检索支持性文献证据
- **从线性流程升级为网状推理**
  ```
  解析病历 → OncoKB → PubMed → 指南 → 生成报告 → 验证
  ```
- 新增 `evidence_collector` 证据收集器
- 新增 `_build_agent_trace()` 方法，自动生成 Agent Trace 内容
- CLI 参数增加 `--gene_symbol`, `--gene_variant`, `--tumor_type`, `--keywords`

### 新增文件

```
skills/clinical_writer/references/asco_nccn_order_set_template.json
```

### 工程改进

- **Git 提交**: `feat: inject expert-level clinical constraints to MDT report schema`
- **ROADMAP.md**: 更新 v2.4.0 状态，标记 Skills 整合为已完成
- **CHANGELOG.md**: 记录本次重构详情

### 临床影响

- 输出格式达到"主治医师开具真实医嘱"级别
- 强制排他性分析，避免 AI 过度自信
- 完整的循证医学证据链（OncoKB + PubMed + NCCN/ESMO）
- 明确的停药要求和减量计划，提升患者安全性

---

## [2.3.0] - 2026-03-04

### 重构

#### 专家级临床约束注入
- **Order Sets 模板机制** - 基于 ASCO/NCCN 指南的结构化输出模板
- **5 大核心模块** - admission_evaluation, primary_plan, systemic_management, follow_up, rejected_alternatives
- **Agent Trace 模块** - 追踪 Agent 推理过程
- **动态可选声明** - 不适用的治疗模块设为 null
- **强化临床字段**:
  - 激素管理：tapering_schedule（减量计划）
  - 围手术期停药：peri_procedural_holding_parameters
  - 分子病理送检：molecular_pathology_orders

#### generate_report.py v2.3
- 模板加载器和提示词生成器
- 15+ Pydantic 输出 Schema 子类
- 验证规则扩展

#### validate_report.py v2.3
- 同步模板验证逻辑
- 10 项验证规则

#### main_oncology_agent_v2.py v2.3
- 整合 OncoKB/PubMed 形成网状推理
- evidence_collector 证据收集器
- _build_agent_trace() 自动生成 Agent Trace

---

## [2.2.0] - 2026-03-04

### 新增

#### PubMed Search Skill
- **`skills/pubmed_search/`** - 完整的 PubMed 生物医学文献查询 Skill
- **4 种查询类型**：
  - `search` - 根据关键词搜索文献
  - `details` - 根据 PMID 获取文献详情 (标题、摘要、期刊、年份、作者)
  - `case_reports` - 搜索罕见病例报告 (疾病 + 合并症 + 治疗)
  - `clinical_trial` - 搜索临床试验文献
- **PubMedClient 类** - API 客户端封装 (`scripts/pubmed_client.py`)
  - 使用 NCBI E-utilities API
  - 二进制 XML 解析 (Bio.Entrez)
  - 自动速率限制处理
  - 支持结构化摘要解析

#### 参考资料
- **`references/api_endpoints.md`** - E-utilities API 完整参考
- **`references/search_syntax.md`** - PubMed 搜索语法详解 (字段限定符、布尔运算符、MeSH 术语)

#### 示例文件
- **`examples/example_queries.md`** - 7 种查询场景示例

### 技能设计特点

#### 与 OncoKB 配合使用
- 可先查询 OncoKB 获取治疗推荐和引用 PMID
- 再使用 PubMed 获取文献详情 (标题、摘要)
- 为诊疗决策提供循证依据

### 测试验证

- ✅ EGFR L858R NSCLC 搜索返回 3 篇文献
- ✅ 文献详情提取成功 (PMID、标题、期刊、年份)
- ✅ SkillContext 调用历史正常记录

### 工程改进

- **`SkillRegistry.from_directory()` 适配三层结构** - 支持 AgentSkills 规范的 `skills/<name>/scripts/` 目录结构
- **`requirements.txt`** - 首次创建，明确核心依赖和可选依赖
- **`.gitignore` 增强** - 添加敏感文件、测试缓存、类型检查缓存等忽略规则

---

## [2.1.1] - 2026-03-04

### 修复

#### OncoKB API 配置修复
- **更正 API 端点**: `/annotate/variants/byProteinChange` → `/annotate/mutations/byProteinChange`
- **移除 evidenceType 参数**: 该参数导致 500 错误
- **更新环境变量名**: `ONCOKB_API_TOKEN` → `ONCOKB_API_KEY` (与现有代码一致)
- **更新 API 基础 URL**: `https://api.oncokb.org` → `https://www.oncokb.org`

### 改进

- 添加 User-Agent 请求头
- 改进异常处理，区分 requests 异常和通用异常
- 404 响应不再抛出异常，返回友好的错误信息

### 测试验证

- ✅ EGFR L858R 查询返回 Oncogenic 判定和 11 条治疗推荐
- ✅ SkillContext 调用历史正常记录

---

## [2.1.0] - 2026-03-03

### 新增

#### OncoKB Query Skill
- **`skills/oncokb_query/`** - 完整的 OncoKB 癌症知识库查询 Skill
- **6 种查询类型**：
  - `variant` - 基因变异临床意义查询
  - `drug` - 药物敏感性查询
  - `biomarker` - 生物标志物查询
  - `tumor_type` - 癌症类型治疗推荐查询
  - `evidence` - 证据详情查询
  - `gene` - 基因基本信息查询
- **OncoKBClient 类** - API 客户端封装 (`scripts/oncokb_client.py`)
  - 自动选择公共 API 或认证 API
  - 请求速率限制处理
  - 自动重试和错误处理
  - 批量查询支持

#### 参考资料
- **`references/api_endpoints.md`** - OncoKB API 端点完整参考
- **`references/evidence_levels.md`** - 证据等级详解 (Level 1-4, R1-R2)

#### 示例文件
- **`examples/example_queries.md`** - 7 种查询场景示例
- **`examples/sample_responses.json`** - 示例响应参考

### 技能设计特点

#### 多样化查询支持
不同于单一的基因/药物查询，本 Skill 支持：
- Agent 可根据需要灵活选择查询类型
- 统一的输入 Schema，不同查询类型共享通用参数
- 详细的 `description` 包含医疗专业名词解释

#### 三层结构落实 (AgentSkills 规范)
```
oncokb_query/
├── SKILL.md              # YAML frontmatter + 使用说明
├── README.md             # 快速开始
├── scripts/
│   ├── oncokb_client.py  # API 客户端
│   └── query_variant.py  # Skill 主实现
├── references/           # 参考资料
│   ├── api_endpoints.md
│   └── evidence_levels.md
└── examples/             # 使用示例
    ├── example_queries.md
    └── sample_responses.json
```

### 新增文件

```
skills/oncokb_query/SKILL.md
skills/oncokb_query/README.md
skills/oncokb_query/scripts/oncokb_client.py
skills/oncokb_query/scripts/query_variant.py
skills/oncokb_query/references/api_endpoints.md
skills/oncokb_query/references/evidence_levels.md
skills/oncokb_query/examples/example_queries.md
skills/oncokb_query/examples/sample_responses.json
```

### 使用示例

```python
from skills.oncokb_query.scripts.query_variant import OncoKBQuery, OncoKBQueryInput
from core.skill import SkillContext

skill = OncoKBQuery()
context = SkillContext(session_id="patient_001")

# 查询 EGFR L858R 突变
input_args = OncoKBQueryInput(
    query_type="variant",
    hugo_symbol="EGFR",
    variant="L858R",
    tumor_type="Non-Small Cell Lung Cancer"
)
result = skill.execute_with_retry(input_args.model_dump(), context=context)
```

---

## [2.0.0] - 2026-03-03

### 新增

#### 核心架构
- **Pydantic v2 强类型约束** - 所有 Skill 输入参数现在必须定义 Pydantic 模型，确保类型安全
- **SkillContext 类** - 跨技能共享上下文容器，支持：
  - 会话隔离 (每患者一会话)
  - 显式参数传递 (`context: Optional[SkillContext]`)
  - 调用历史审计追踪
- **SkillCallRecord 类** - 单次 Skill 调用记录，包含时间戳、输入、输出、错误、耗时、重试次数
- **RetryConfig 类** - 可配置的重试策略，支持指数退避
- **execute_with_retry() 方法** - BaseSkill 统一执行入口，自动处理：
  - 输入验证
  - 指数退避重试 (默认 3 次)
  - 调用历史审计

#### 异常处理
- **SkillExecutionError** - Skill 执行异常
- **SkillValidationError** - 输入验证失败异常

#### 医疗数据类型
- **MedicalDataType 枚举** - 预定义医疗数据类型常量
- **pdf_report_schema()** - PDF 报告输入 Schema 生成器
- **dicom_series_schema()** - DICOM 序列输入 Schema 生成器

### 变更

#### core/skill.py
- `BaseSkill` 从抽象基类升级为泛型类 `BaseSkill[T]`
- `input_schema` 从必须手动定义改为可从 `input_schema_class` 自动生成
- `execute()` 方法签名从 `execute(**kwargs)` 改为 `execute(args: T, context: Optional[SkillContext])`
- `SkillRegistry` 新增 `load_skill_metadata()` 支持 SKILL.md 元数据加载

#### skills/pdf_inspector
- 创建 `SKILL.md` 包含 YAML frontmatter 和使用说明
- `parse_pdf.py` 从脚本式重构为类：
  - 新增 `PDFInspectorInput` Pydantic 模型
  - 新增 `PDFInspector` 类继承 `BaseSkill`
  - CLI 入口保留向后兼容

#### skills/clinical_writer
- 创建 `SKILL.md` 包含 YAML frontmatter 和使用说明
- `generate_report.py` 重构为 `MDTReportGenerator` 类
- `validate_report.py` 重构为 `ReportValidator` 类
- 两个类均使用 Pydantic Schema 和 SkillContext

### 新增文件

```
core/skill.py               # 重写 (v2.0)
skills/pdf_inspector/SKILL.md
skills/pdf_inspector/parse_pdf.py    # 重写
skills/clinical_writer/SKILL.md
skills/clinical_writer/generate_report.py   # 重写
skills/clinical_writer/validate_report.py   # 重写
main_oncology_agent_v2.py              # 新增使用示例
ROADMAP.md                             # 新增项目路线图
CHANGELOG.md                           # 新增更新日志
```

### 迁移指南

#### 旧代码 (v1.x)
```python
class PDFInspector(BaseSkill):
    name = "parse_medical_pdf"
    description = "Parse medical PDF"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {...}}

    def execute(self, file_path: str, extract_images: bool = False) -> str:
        ...
```

#### 新代码 (v2.0)
```python
from pydantic import BaseModel, Field
from core.skill import BaseSkill, SkillContext

class PDFInspectorInput(BaseModel):
    file_path: str = Field(..., description="PDF 文件路径")
    extract_images: bool = Field(default=False)

class PDFInspector(BaseSkill[PDFInspectorInput]):
    name = "parse_medical_pdf"
    description = "Parse medical PDF"
    input_schema_class = PDFInspectorInput

    def execute(self, args: PDFInspectorInput, context: Optional[SkillContext] = None) -> str:
        # args.file_path 类型安全访问
        # context 用于跨技能状态传递
        ...
```

---

## [1.0.0] - 2026-02-23

### 新增

- 初始版本
- `BaseSkill` 抽象基类
- `SkillRegistry` 轻量级注册中心
- `skills/pdf_inspector/` 医疗 PDF 解析 Skill
- `skills/clinical_writer/` 临床报告生成与验证 Skill
- `main_oncology_agent.py` 主程序
