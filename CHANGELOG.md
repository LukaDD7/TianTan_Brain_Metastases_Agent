# Changelog

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
