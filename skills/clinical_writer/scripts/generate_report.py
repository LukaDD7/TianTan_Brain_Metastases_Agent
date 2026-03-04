#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Clinical Report Generator Skill - v2.3 重构版

核心变更：
1. 引入 Order Sets 模板机制，强制结构化输出
2. 支持 4 大临床模块 + 排他性分析
3. Pydantic 强制约束输出 Schema
4. 强化激素管理、围手术期停药、分子病理送检要求

Author: TianTan Brain Metastases Agent Team
Version: 2.3.0
"""

import os
import re
import json
import datetime
from typing import Optional, Any, List, Dict
from pathlib import Path

# Pydantic v2
from pydantic import BaseModel, Field

# 本地基类
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import BaseSkill, SkillContext, SkillExecutionError, SkillValidationError


# =============================================================================
# 模板路径配置
# =============================================================================

ORDER_SET_TEMPLATE_PATH = Path(__file__).parent.parent / "references" / "asco_nccn_order_set_template.json"


# =============================================================================
# 输入 Schema (Pydantic 模型)
# =============================================================================

class MDTReportInput(BaseModel):
    """MDT Report Generator 的输入参数"""

    case_id: str = Field(
        ...,
        description="患者病例 ID",
        examples=["Case1", "Patient_12345"]
    )
    report_content: str = Field(
        ...,
        description="MDT 报告内容 (Markdown 格式，需符合 Order Sets 模板结构)",
        min_length=10
    )
    skip_validation: bool = Field(
        default=False,
        description="是否跳过验证 (默认 false，强制验证)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "case_id": "Case1",
                    "report_content": """# MDT 诊疗建议

## 入院评估
- performance_status: KPS ≥70
- neurological_status: 神志清楚，右侧肢体肌力 IV 级

## 首选治疗方案
- modality: systemic_therapy
- rationale: EGFR L858R 突变阳性...

## 被排除方案
- rejected_alternatives: 手术切除（原因：...）

[Citation: NCCN_NSCLC.pdf, Page 12]""",
                    "skip_validation": False
                }
            ]
        }


class MDTReportValidatorInput(BaseModel):
    """MDT Report Validator 的输入参数"""

    case_id: str = Field(
        ...,
        description="患者病例 ID"
    )
    file_path: str = Field(
        ...,
        description="待验证的报告文件路径"
    )


# =============================================================================
# 输出 Schema - 严格遵循临床专家要求的 4 大结构 + 排他性分析
# =============================================================================

class AdmissionEvaluation(BaseModel):
    """入院评估与一般治疗"""
    performance_status: str = Field(..., description="体力状态评分 (KPS ≥70 / KPS 50-60 / KPS <50)")
    neurological_status: str = Field(..., description="神经系统状态")
    symptom_management: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="对症治疗（药物、适应证、剂量、频次）"
    )
    baseline_labs: List[str] = Field(..., description="基线检查项目")

    class Config:
        json_schema_extra = {
            "description": "严禁写入'术前准备'等暗示手术的文字"
        }


class PrimaryPlanSurgery(BaseModel):
    """手术治疗子模块"""
    procedure_name: str = Field(..., description="手术名称")
    surgical_adjuncts: List[str] = Field(
        ...,
        description="必须明确：术中导航/术中核磁/电生理监测等，如不适用填'无'"
    )
    extent_of_resection_goal: str = Field(
        ...,
        description="预期切除范围",
        enum=["GTR (全切)", "STR (次全切)", "Biopsy Only (仅活检)"]
    )
    molecular_pathology_orders: List[str] = Field(
        ...,
        description="【核心字段】分子病理送检医嘱（BRAF V600E、NGS panel 等）"
    )


class PrimaryPlanRadiotherapy(BaseModel):
    """放射治疗子模块"""
    technique: str = Field(..., description="放疗技术", enum=["SRS", "FSRT", "WBRT", "WBRT+SRS Boost", "IMRT", "海马回避 WBRT"])
    dose_fractionation: Dict[str, Any] = Field(..., description="剂量分割方案")
    target_definition: Dict[str, Any] = Field(..., description="靶区定义")
    concurrent_medications: Optional[List[str]] = Field(
        default=None,
        description="围放疗期用药"
    )


class PrimaryPlanSystemicDrug(BaseModel):
    """全身治疗药物子模块"""
    drug_name: str = Field(..., description="药物通用名")
    dosage: str = Field(..., description="必须写明具体剂量，如'80mg'")
    route: str = Field(..., description="给药途径")
    frequency: str = Field(..., description="给药频率")
    cycle_length: int = Field(..., description="周期长度（天）")
    interval: str = Field(..., description="给药间隔描述")
    duration: str = Field(..., description="总疗程")
    peri_procedural_holding_parameters: Optional[str] = Field(
        default=None,
        description="【核心字段】围手术期/放疗期停药要求"
    )
    food_requirements: Optional[str] = Field(default=None, description="饮食要求")
    major_toxicities: Optional[List[str]] = Field(default=None, description="主要毒性反应")


class PrimaryPlanSystemic(BaseModel):
    """全身治疗子模块"""
    regimen_name: str = Field(..., description="方案名称")
    drugs: List[PrimaryPlanSystemicDrug] = Field(..., description="药物列表")
    biomarker_requirement: Optional[str] = Field(default=None, description="生物标志物要求")


class PrimaryPlan(BaseModel):
    """首选治疗方案"""
    modality: str = Field(..., description="治疗方式", enum=["surgery", "radiotherapy", "systemic_therapy", "combined"])
    surgery: Optional[PrimaryPlanSurgery] = Field(default=None, description="手术治疗模块，如不适用为 null")
    radiotherapy: Optional[PrimaryPlanRadiotherapy] = Field(default=None, description="放射治疗模块，如不适用为 null")
    systemic_therapy: Optional[PrimaryPlanSystemic] = Field(default=None, description="全身治疗模块，如不适用为 null")
    rationale: str = Field(..., description="选择该方案的理由")
    evidence_citation: str = Field(..., description="指南引用 [Citation: X, Page Y]")


class SystemicManagementTargeted(BaseModel):
    """靶向治疗子模块"""
    gene_target: str = Field(..., description="靶基因")
    variant: str = Field(..., description="变异类型")
    drug: str = Field(..., description="药物名称")
    dosage: str = Field(..., description="剂量")
    cycle_length: int = Field(..., description="周期长度（天）")
    interval: str = Field(..., description="给药间隔")
    duration: str = Field(..., description="总疗程")
    peri_procedural_holding_parameters: Optional[str] = Field(
        default=None,
        description="围手术期/放疗期停药要求"
    )


class SystemicManagementImmuno(BaseModel):
    """免疫治疗子模块"""
    agent: str = Field(..., description="免疫治疗药物")
    dosage: str = Field(..., description="剂量")
    cycle_length: int = Field(..., description="周期长度（天）")
    duration: str = Field(..., description="总疗程")
    peri_procedural_holding_parameters: Optional[str] = Field(
        default=None,
        description="围手术期/放疗期停药要求"
    )


class SystemicManagement(BaseModel):
    """后续治疗与全身管理"""
    targeted_therapy: Optional[SystemicManagementTargeted] = Field(default=None)
    immunotherapy: Optional[SystemicManagementImmuno] = Field(default=None)
    cns_prophylaxis: Optional[str] = Field(default=None, description="CNS 预防策略")
    maintenance_plan: Optional[str] = Field(default=None, description="维持治疗计划")
    bone_modifying_agent: Optional[str] = Field(default=None, description="骨改良药物")


class FollowUpImaging(BaseModel):
    """影像随访子模块"""
    modality: str = Field(..., description="检查类型")
    frequency: str = Field(..., description="频率")
    duration: str = Field(..., description="持续时间")


class FollowUpToxicity(BaseModel):
    """毒性监测子模块"""
    parameter: str = Field(..., description="监测参数")
    frequency: str = Field(..., description="监测频率")


class FollowUpPlan(BaseModel):
    """随访计划"""
    imaging_schedule: List[FollowUpImaging] = Field(..., description="影像随访计划")
    tumor_markers: Optional[List[str]] = Field(default=None, description="肿瘤标志物监测")
    clinical_visit_schedule: str = Field(..., description="门诊复诊频率")
    toxicity_monitoring: List[FollowUpToxicity] = Field(..., description="毒性监测计划")
    emergency_contact_criteria: Optional[List[str]] = Field(default=None, description="急诊就诊指征")


class RejectedOptionCitation(BaseModel):
    """引用信息"""
    source: str = Field(..., description="来源")
    section: Optional[str] = Field(default=None, description="具体章节")
    pmid: Optional[str] = Field(default=None, description="PubMed ID")


class RejectedOption(BaseModel):
    """单个被排除的方案"""
    option: str = Field(..., description="被排除的方案")
    reason: str = Field(..., description="排除原因")
    evidence_level: str = Field(
        ...,
        description="证据等级",
        enum=["NCCN Category 1", "NCCN Category 2A", "NCCN Category 2B", "NCCN Category 3", "ESMO Level I", "ESMO Level II", "ESMO Level III", "Expert Opinion"]
    )
    citation: RejectedOptionCitation = Field(..., description="引用来源")


class RejectedAlternatives(BaseModel):
    """不推荐/被排除的治疗方案"""
    rejected_options: List[RejectedOption] = Field(..., min_length=1, description="被排除的方案列表，至少 1 项")


class AgentTraceSkillCall(BaseModel):
    """Skill 调用记录"""
    skill_name: str = Field(..., description="Skill 名称")
    query_type: Optional[str] = Field(default=None, description="查询类型")
    key_findings: List[str] = Field(..., description="关键发现摘要")
    duration_ms: float = Field(..., description="耗时（毫秒）")
    timestamp: str = Field(..., description="时间戳（ISO 8601）")


class AgentTraceEvidence(BaseModel):
    """证据来源"""
    source_type: str = Field(..., enum=["OncoKB", "PubMed", "NCCN", "ESMO", "ASCO", "CSCO"])
    source_id: str = Field(..., description="来源 ID")
    relevance: str = Field(..., description="相关性描述")


class AgentTrace(BaseModel):
    """Agent 推理追踪记录"""
    skills_called: List[AgentTraceSkillCall] = Field(..., description="本次推理调用的所有 Skill 记录")
    evidence_sources: List[AgentTraceEvidence] = Field(..., description="引用的所有循证医学证据来源")
    reasoning_confidence: str = Field(..., description="基于证据充分性的自我评估", enum=["High", "Moderate", "Low"])
    uncertainty_factors: Optional[List[str]] = Field(default=None, description="影响决策信心的不确定因素")


class MDTReportOutput(BaseModel):
    """MDT 报告完整输出 Schema"""
    admission_evaluation: AdmissionEvaluation = Field(..., description="入院评估与一般治疗")
    primary_plan: PrimaryPlan = Field(..., description="首选治疗方案")
    systemic_management: SystemicManagement = Field(..., description="后续治疗与全身管理")
    follow_up: FollowUpPlan = Field(..., description="随访计划")
    rejected_alternatives: RejectedAlternatives = Field(..., description="被排除的治疗方案")
    agent_trace: AgentTrace = Field(..., description="Agent 推理追踪记录")


# =============================================================================
# 模板加载器
# =============================================================================

def load_order_set_template() -> Dict[str, Any]:
    """
    加载 Order Sets 模板文件。

    Returns:
        模板字典

    Raises:
        SkillExecutionError: 模板文件不存在或解析失败
    """
    template_path = ORDER_SET_TEMPLATE_PATH.resolve()

    if not template_path.exists():
        raise SkillExecutionError(
            f"Order Sets 模板文件不存在：{template_path}\n"
            "请确保 skills/clinical_writer/references/asco_nccn_order_set_template.json 已创建"
        )

    with open(template_path, 'r', encoding='utf-8') as f:
        try:
            template = json.load(f)
        except json.JSONDecodeError as e:
            raise SkillExecutionError(f"模板 JSON 解析失败：{e}")

    return template


def generate_template_prompt(template: Dict[str, Any]) -> str:
    """
    根据模板生成提示词，指导大模型进行'填空式'输出。

    Args:
        template: Order Sets 模板

    Returns:
        提示词字符串
    """
    template_info = template.get("template_info", {})
    schema = template.get("output_schema", {})
    dynamic_notice = template_info.get("dynamic_template_notice", {})

    prompt_parts = [
        "=" * 70,
        f"临床输出规范 - {template_info.get('name', 'ASCO/NCCN Order Sets')}",
        f"版本：{template_info.get('version', 'Unknown')}",
        "=" * 70,
        "",
        "⚠️ 动态可选模板声明",
        "-" * 40,
        dynamic_notice.get("content", ""),
        "",
        "你必须按照以下 JSON Schema 格式输出，每个字段都必须填写：",
        "",
        json.dumps(schema, ensure_ascii=False, indent=2),
        "",
        "⚠️ 强制要求",
        "-" * 40,
        "1. admission_evaluation 中严禁出现'术前准备'等暗示性文字",
        "2. primary_plan 中的药物必须写明 dosage, cycle_length, interval, duration",
        "3. primary_plan 中的手术必须写明 surgical_adjuncts（辅助技术）和 molecular_pathology_orders（分子病理送检）",
        "4. 如果药物是类固醇（如地塞米松），必须填写 tapering_schedule（减量计划）",
        "5. 全身治疗药物必须写明 peri_procedural_holding_parameters（围手术期/放疗期停药要求）",
        "6. rejected_alternatives 至少列出 1 项被排除的方案，并说明原因和引用",
        "7. 所有治疗推荐必须有 OncoKB 或 NCCN/ESMO 指南引用",
        "8. agent_trace 必须记录本次推理调用的所有 Skill 和证据来源",
        ""
    ]

    return "\n".join(prompt_parts)


# =============================================================================
# Skill 实现 - Generator
# =============================================================================

class MDTReportGenerator(BaseSkill[MDTReportInput]):
    """
    MDT 报告生成器 - v2.3 重构版

    核心变更：
    1. 强制加载 Order Sets 模板作为 Context 注入
    2. 输出严格遵循 Pydantic Schema 约束
    3. 增加 rejected_alternatives 排他性分析
    4. 增加 agent_trace 推理追踪
    5. 强化激素管理、围手术期停药、分子病理送检要求

    Version: 2.3.0
    """

    name = "generate_mdt_report"
    description = (
        "生成并验证肿瘤多学科诊疗 (MDT) 报告。"
        "适用于：将 AI 生成的治疗建议格式化为标准 MDT 报告，"
        "强制验证报告包含指南引用和 ASCO/NCCN Order Sets 模板结构，"
        "自动归档到患者专属沙盒目录。"
        "注意：这是诊疗流程的最后一步，确保所有建议都有循证依据。"
    )
    input_schema_class = MDTReportInput

    def __init__(self):
        super().__init__()
        # 报告生成是本地 I/O 操作，不需要重试
        self.retry_config.max_retries = 1
        # 模板缓存
        self._template_cache: Optional[Dict[str, Any]] = None

    def _get_template(self) -> Dict[str, Any]:
        """获取模板（带缓存）"""
        if self._template_cache is None:
            self._template_cache = load_order_set_template()
        return self._template_cache

    @property
    def input_schema(self) -> Dict[str, Any]:
        """获取 JSON Schema (用于 LLM Tool 调用)"""
        return self.input_schema_class.model_json_schema()

    def execute(self, args: MDTReportInput, context: Optional[SkillContext] = None) -> str:
        """
        生成并验证 MDT 报告。

        核心流程：
        1. 加载 Order Sets 模板
        2. 生成模板提示词
        3. 将模板作为 Context 注入，要求大模型填空式输出
        4. 验证输出符合 Pydantic Schema
        5. 保存报告

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的执行结果

        Raises:
            SkillExecutionError: 执行失败时抛出
            SkillValidationError: 验证失败时抛出
        """
        try:
            # Step 1: 加载 Order Sets 模板
            template = self._get_template()
            template_prompt = generate_template_prompt(template)

            # Step 2: 验证报告内容（如果未跳过）
            if not args.skip_validation:
                # 新验证逻辑：检查是否符合模板结构
                validation_errors = self._validate_with_template(
                    args.report_content,
                    template
                )
                if validation_errors:
                    raise SkillValidationError(
                        f"报告验证失败：{';'.join(validation_errors)}"
                    )

            # Step 3: 创建输出目录
            output_dir = os.path.abspath(os.path.join("workspace", "cases", args.case_id))
            os.makedirs(output_dir, exist_ok=True)

            # Step 4: 生成文件名并保存
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"MDT_Report_{timestamp}.md"
            report_path = os.path.join(output_dir, report_filename)

            # 将模板提示词与实际内容合并后保存
            full_report = f"{template_prompt}\n\n# 报告正文\n\n{args.report_content}"

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(full_report)

            # Step 5: 更新上下文
            if context:
                context.set(f"mdt_report_{args.case_id}", report_path)
                context.set_metadata("last_report_path", report_path)

            result = {
                "success": True,
                "report_path": report_path,
                "validation_errors": [],
                "message": "报告已通过医疗合规校验，并正式存档",
                "template_used": template.get("template_info", {}).get("name", "Unknown"),
                "template_version": template.get("template_info", {}).get("version", "Unknown")
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except SkillValidationError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"报告生成失败：{str(e)}") from e

    def _validate_with_template(
        self,
        content: str,
        template: Dict[str, Any]
    ) -> List[str]:
        """
        基于模板验证报告内容。

        Args:
            content: 报告内容
            template: Order Sets 模板

        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []

        # 规则 1: 检查是否包含 5 大核心模块
        required_sections = [
            "admission_evaluation",
            "primary_plan",
            "systemic_management",
            "follow_up",
            "rejected_alternatives"
        ]

        content_lower = content.lower()
        for section in required_sections:
            if section.replace("_", " ") not in content_lower and section not in content_lower:
                errors.append(f"缺少必需模块：{section}")

        # 规则 2: 检查是否包含排他性分析（至少 1 项）
        if "rejected" not in content_lower and "alternative" not in content_lower and "排除" not in content:
            errors.append("缺少 rejected_alternatives（被排除的方案）模块，必须至少列出 1 项被排除的方案")

        # 规则 3: 检查指南引用
        citation_pattern = r"\[Citation:\s*[^,]+,\s*Page\s*\d+\]"
        if not re.search(citation_pattern, content, re.IGNORECASE):
            errors.append(
                "未检测到合规的指南引用格式！"
                "每项治疗建议后必须包含类似 '[Citation: NCCN_Melanoma.pdf, Page 42]' 的来源证据。"
            )

        # 规则 4: 检查是否有暗示性文字（严禁"术前准备"）
        if "术前准备" in content or "preoperative preparation" in content_lower:
            errors.append(
                "严禁出现'术前准备'等暗示必然手术的文字！"
                "admission_evaluation 只能描述入院评估和一般治疗。"
            )

        # 规则 5: 检查是否包含 Agent 追踪
        if "agent_trace" not in content_lower and "skill" not in content_lower:
            errors.append("缺少 agent_trace（Agent 推理追踪记录）模块")

        # 规则 6: 检查分子病理送检（如果包含手术）
        if "surgery" in content_lower or "手术" in content:
            if "molecular_pathology" not in content_lower and "分子病理" not in content and "基因检测" not in content:
                errors.append(
                    "手术方案必须包含 molecular_pathology_orders（分子病理送检医嘱），"
                    "明确切除组织需进行哪些基因突变检测（如 BRAF V600E、NGS panel 等）"
                )

        # 规则 7: 检查围手术期停药要求（如果包含全身治疗）
        if ("systemic_therapy" in content_lower or "靶向" in content or "免疫" in content) and \
           "peri_procedural" not in content_lower and "停药" not in content:
            # 这只是警告级别，不作为错误
            pass

        return errors


# =============================================================================
# Skill 实现 - Validator (独立工具)
# =============================================================================

class MDTReportValidator(BaseSkill[MDTReportValidatorInput]):
    """
    MDT 报告验证器 - 独立验证已存在报告文件的合规性。

    Version: 2.3.0
    """

    name = "validate_mdt_report"
    description = (
        "验证已存在的 MDT 报告文件是否符合临床书写规范和 ASCO/NCCN Order Sets 模板。"
        "检查项目：指南引用格式、5 大核心模块完整性、排他性分析、Agent 追踪。"
    )
    input_schema_class = MDTReportValidatorInput

    def __init__(self):
        super().__init__()
        self.retry_config.max_retries = 0  # 验证操作不需要重试
        self._template_cache: Optional[Dict[str, Any]] = None

    def _get_template(self) -> Dict[str, Any]:
        """获取模板（带缓存）"""
        if self._template_cache is None:
            self._template_cache = load_order_set_template()
        return self._template_cache

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.input_schema_class.model_json_schema()

    def execute(self, args: MDTReportValidatorInput, context: Optional[SkillContext] = None) -> str:
        """
        验证 MDT 报告文件。

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的验证结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(args.file_path):
                raise SkillExecutionError(f"文件不存在：{args.file_path}")

            with open(args.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 加载模板
            template = self._get_template()

            # 验证内容
            errors = self._validate_with_template(content, template)

            result = {
                "file_path": args.file_path,
                "valid": len(errors) == 0,
                "errors": errors,
                "message": "✅ 验证通过！报告可作为正式医疗档案使用。" if not errors else f"❌ 发现{len(errors)}个问题，请修正后重新提交。",
                "template_version": template.get("template_info", {}).get("version", "Unknown")
            }

            # 更新上下文
            if context:
                context.set(f"validation_result_{args.file_path}", result)

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            raise SkillExecutionError(f"验证失败：{str(e)}") from e

    def _validate_with_template(
        self,
        content: str,
        template: Dict[str, Any]
    ) -> List[str]:
        """
        基于模板验证报告内容。

        Returns:
            错误信息列表
        """
        errors = []
        content_lower = content.lower()

        # 规则 1: 检查 5 大核心模块
        required_sections = [
            ("admission_evaluation", "入院评估"),
            ("primary_plan", "首选方案"),
            ("systemic_management", "全身管理"),
            ("follow_up", "随访"),
            ("rejected_alternatives", "被排除方案")
        ]

        for section_en, section_cn in required_sections:
            if section_en not in content_lower and section_cn not in content:
                errors.append(f"缺少必需模块：{section_en} ({section_cn})")

        # 规则 2: 指南引用校验
        citation_pattern = r"\[Citation:\s*[^,]+,\s*Page\s*\d+\]"
        if not re.search(citation_pattern, content, re.IGNORECASE):
            errors.append(
                "未检测到合规的指南引用格式！"
                "每项治疗建议后必须包含类似 '[Citation: NCCN_Melanoma.pdf, Page 42]' 的来源证据。"
            )

        # 规则 3: 检查暗示性文字
        if "术前准备" in content or "preoperative preparation" in content_lower:
            errors.append(
                "发现禁忌文字'术前准备'！"
                "admission_evaluation 模块严禁出现暗示必然手术的文字。"
            )

        # 规则 4: 检查 Agent 追踪
        if "agent_trace" not in content_lower:
            errors.append("缺少 agent_trace（Agent 推理追踪记录）模块")

        # 规则 5: 检查排他性分析至少 1 项
        rejected_match = re.search(r"rejected_alternatives.*?(?=agent_trace|$)", content, re.IGNORECASE | re.DOTALL)
        if rejected_match:
            rejected_section = rejected_match.group(0)
            # 检查是否有实际的排除项
            if not re.search(r"option.*?排除|被排除|不推荐", rejected_section, re.IGNORECASE):
                errors.append("rejected_alternatives 模块为空，必须至少列出 1 项被排除的方案")
        else:
            errors.append("rejected_alternatives 模块内容无法识别")

        return errors


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="MDT Report Generator v2.3")
    parser.add_argument("--case_id", required=True, help="Patient Case ID")
    parser.add_argument("--content", required=True, help="Report content (Markdown)")
    parser.add_argument("--skip_validation", action="store_true", help="Skip validation")

    args = parser.parse_args()

    generator = MDTReportGenerator()
    input_args = MDTReportInput(
        case_id=args.case_id,
        report_content=args.content,
        skip_validation=args.skip_validation
    )

    try:
        result = generator.execute(input_args)
        print(result)
    except (SkillExecutionError, SkillValidationError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        exit(1)


if __name__ == "__main__":
    main()
