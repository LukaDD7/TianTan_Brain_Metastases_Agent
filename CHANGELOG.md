# Changelog

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
