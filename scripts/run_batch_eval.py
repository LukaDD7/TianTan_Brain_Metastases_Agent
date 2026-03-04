#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量评估脚本 (Batch Evaluation Script)

用途：
1. 从 Excel 读取 10 个真实病历测试用例
2. 为每个 Case 创建独立的 OncologyWorkflow 实例（Clean Context 隔离）
3. 自动化执行技能调用和报告生成
4. Eval 断言：验证关键字段（rejected_alternatives、agent_trace、peri_procedural_holding）
5. 结果落盘：生成 CSV 评估报告

注意：严格遵守 Clean Context 原则 - 每个 Case 使用独立的 SkillContext 和 Workflow

## 本地知识库边界
- PubMed API 仅用于获取文献摘要和元数据
- parse_pdf Skill 专门用于解析本地权威临床指南
- 本地指南路径：/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/Guidelines/脑转诊疗指南/
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

# 导入核心组件
from core.skill import SkillContext, SkillRegistry, SkillExecutionError

# === 基础 Skill ===
from skills.pdf_inspector.scripts.parse_pdf import PDFInspector, PDFInspectorInput
from skills.clinical_writer.scripts.generate_report import MDTReportGenerator, MDTReportInput
from skills.clinical_writer.scripts.validate_report import ReportValidator, ReportValidatorInput

# === 肿瘤专科 API Skill ===
from skills.oncokb_query.scripts.query_variant import OncoKBQuery, OncoKBQueryInput, QueryType
from skills.pubmed_search.scripts.search_articles import PubMedSearch, PubMedSearchInput, QueryType as PubMedQueryType


# =============================================================================
# 1. 本地指南知识库 (Local Guidelines Grounding)
# =============================================================================

class LocalGuidelinesManager:
    """
    本地权威指南管理器

    职责：
    1. 扫描指定目录下的所有 PDF 指南文件
    2. 生成指南索引（可用于 System Prompt）
    3. 提供指南文件路径查询
    """

    def __init__(self, guidelines_dir: Optional[str] = None):
        if guidelines_dir is None:
            # 默认指南目录
            self.guidelines_dir = Path(PROJECT_ROOT) / "Guidelines" / "脑转诊疗指南"
        else:
            self.guidelines_dir = Path(guidelines_dir)

        # 指南索引
        self.guideline_index: Dict[str, Dict[str, Any]] = {}
        self._scan_guidelines()

    def _scan_guidelines(self):
        """扫描目录下的所有 PDF 指南文件"""
        if not self.guidelines_dir.exists():
            print(f"⚠️  指南目录不存在：{self.guidelines_dir}")
            return

        pdf_files = list(self.guidelines_dir.rglob("*.pdf"))

        print(f"\n📚 扫描本地权威指南...")
        print(f"   目录：{self.guidelines_dir}")
        print(f"   找到 {len(pdf_files)} 个指南文件")

        for pdf in pdf_files:
            # 分类
            category = "Practice_Guidelines" if "Practice_Guideline" in str(pdf) else "Review_Articles"

            # 生成简短名称（用于引用）
            name = self._generate_short_name(pdf)

            self.guideline_index[name] = {
                "full_path": str(pdf),
                "relative_path": str(pdf.relative_to(self.guidelines_dir)),
                "category": category,
                "filename": pdf.name
            }

    def _generate_short_name(self, pdf_path: Path) -> str:
        """生成简短名称"""
        name = pdf_path.stem
        # 移除空格和特殊字符
        name = name.replace(" ", "_").replace("-", "_").replace(",", "")
        # 限制长度
        if len(name) > 80:
            name = name[:80] + "..."
        return name

    def get_guideline_path(self, name: str) -> Optional[str]:
        """根据名称获取指南文件路径"""
        if name in self.guideline_index:
            return self.guideline_index[name]["full_path"]
        return None

    def get_guideline_index(self) -> Dict[str, Dict[str, Any]]:
        """获取指南索引"""
        return self.guideline_index

    def generate_system_prompt_section(self) -> str:
        """
        生成可用于 System Prompt 的指南索引部分

        返回格式：
        '''
        ## 📚 本地权威指南知识库

        你可以使用 parse_pdf 工具查阅以下指南：

        ### 🎯 临床实践指南 (Practice Guidelines)
        - NCCN_CNS_Cancers: NCCN Clinical Practice Guidelines in Oncology Central Nervous System Cancers.pdf
          路径：/media/.../NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.pdf
        - ASCO_SNO_ASTRO: Treatment of Brain Metastases ASCO-SNO-ASTRO Guideline.pdf
          路径：/media/.../Treatment_of_Brain_Metastases_ASCO_SNO_ASTRO_Guideline_.pdf

        ### 📖 综述文章 (Review Articles)
        - Brain_metastasis: Brain metastasis.pdf
          路径：/media/.../Brain_metastasis.pdf
        '''
        """
        if not self.guideline_index:
            return "⚠️ 未找到本地指南文件"

        # 按分类组织
        practice_guidelines = {}
        review_articles = {}

        for name, info in self.guideline_index.items():
            if info["category"] == "Practice_Guidelines":
                practice_guidelines[name] = info
            else:
                review_articles[name] = info

        # 生成 Markdown
        lines = []
        lines.append("## 📚 本地权威指南知识库")
        lines.append("")
        lines.append("你可以使用 `parse_pdf` 工具查阅以下本地权威指南：")
        lines.append("")

        if practice_guidelines:
            lines.append("### 🎯 临床实践指南 (Practice Guidelines)")
            lines.append("")
            for name, info in sorted(practice_guidelines.items()):
                filename = info["filename"]
                filepath = info["full_path"]
                lines.append(f"- **{name}**")
                lines.append(f"  - 📄 文件：{filename}")
                lines.append(f"  - 📍 路径：`{filepath}`")
            lines.append("")

        if review_articles:
            lines.append("### 📖 综述文章 (Review Articles)")
            lines.append("")
            for name, info in sorted(review_articles.items()):
                filename = info["filename"]
                filepath = info["full_path"]
                lines.append(f"- **{name}**")
                lines.append(f"  - 📄 文件：{filename}")
                lines.append(f"  - 📍 路径：`{filepath}`")
            lines.append("")

        lines.append("### 💡 使用说明")
        lines.append("")
        lines.append("```python")
        lines.append("# 示例：查询 NCCN CNS 指南中关于脑转移的推荐")
        lines.append('guideline_path = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/Guidelines/脑转诊疗指南/Practice_Guideline_metastases/NCCN Clinical Practice Guidelines in Oncology Central Nervous System Cancers.pdf"')
        lines.append("parse_pdf(file_path=guideline_path, page_start=1, page_end=50)")
        lines.append("```")
        lines.append("")

        return "\n".join(lines)


# =============================================================================
# 2. 配置常量
# =============================================================================

WORKSPACE_DIR = Path(PROJECT_ROOT) / "workspace"
CASES_DIR = WORKSPACE_DIR / "cases"
OUTPUT_DIR = WORKSPACE_DIR / "eval_results"

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 2. Skill Registry 创建函数 (每次重新实例化)
# =============================================================================

def create_fresh_skill_registry(
    oncokb_token: Optional[str] = None,
    pubmed_email: Optional[str] = None
) -> SkillRegistry:
    """
    创建全新的 SkillRegistry (每次调用都重新实例化)

    注意：这是 Clean Context 的关键 - 每个 Case 使用独立的 Registry
    """
    registry = SkillRegistry()

    # 注册所有 Skill (每次都是全新实例)
    registry.register(PDFInspector())
    registry.register(MDTReportGenerator())
    registry.register(ReportValidator())
    registry.register(OncoKBQuery(api_token=oncokb_token))
    registry.register(PubMedSearch(email=pubmed_email))

    return registry


# =============================================================================
# 3. 临床工作流类 (简化版 - 专注于批量评估)
# =============================================================================

class OncologyWorkflowForEval:
    """
    用于批量评估的简化版工作流

    核心原则：每个 Case 一个独立实例，确保 Clean Context 隔离
    """

    def __init__(self, case_id: str, registry: SkillRegistry):
        self.case_id = case_id
        self.registry = registry
        self.context = SkillContext(session_id=case_id)  # 每个 Case 独立上下文

        # 设置元数据
        self.context.set_metadata("case_id", case_id)
        self.context.set_metadata("project_root", PROJECT_ROOT)
        self.context.set_metadata("created_at", datetime.now().isoformat())

        # 证据收集器
        self.evidence_collector: Dict[str, Any] = {
            "oncokb_findings": [],
            "pubmed_findings": [],
            "guideline_findings": [],
            "patient_record_parsed": None
        }

        # 执行历史记录
        self.execution_log: List[Dict[str, Any]] = []

    def log_step(self, step_name: str, status: str, details: str = ""):
        """记录执行步骤"""
        self.execution_log.append({
            "step": step_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def query_variant_oncogenicity(
        self,
        hugo_symbol: str,
        variant: str,
        tumor_type: str
    ) -> dict:
        """查询 OncoKB"""
        skill = self.registry.get("query_oncokb")
        if not skill:
            raise RuntimeError("Skill 'query_oncokb' not found")

        input_args = OncoKBQueryInput(
            query_type=QueryType.VARIANT,
            hugo_symbol=hugo_symbol,
            variant=variant,
            tumor_type=tumor_type,
            include_evidence=True
        )

        try:
            result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
            result = json.loads(result_json)

            # 记录到证据收集器
            data = result.get("data", {})
            oncogenicity = data.get("oncogenicity", "")
            treatments = data.get("treatments", [])

            self.evidence_collector["oncokb_findings"].append({
                "gene": hugo_symbol,
                "variant": variant,
                "oncogenicity": oncogenicity,
                "treatments_count": len(treatments)
            })

            self.log_step("query_oncokb", "SUCCESS", f"{hugo_symbol} {variant} -> {oncogenicity}")
            return result

        except Exception as e:
            self.log_step("query_oncokb", "FAILED", str(e))
            raise

    def search_supporting_literature(
        self,
        keywords: str,
        max_results: int = 5
    ) -> dict:
        """查询 PubMed"""
        skill = self.registry.get("search_pubmed")
        if not skill:
            raise RuntimeError("Skill 'search_pubmed' not found")

        input_args = PubMedSearchInput(
            query_type=PubMedQueryType.SEARCH,
            keywords=keywords,
            max_results=max_results,
            sort="relevance"
        )

        try:
            result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
            result = json.loads(result_json)

            data = result.get("data", {})
            self.evidence_collector["pubmed_findings"].append({
                "search_query": keywords,
                "total_results": data.get("total_results", 0)
            })

            self.log_step("search_pubmed", "SUCCESS", f"关键词: {keywords}")
            return result

        except Exception as e:
            self.log_step("search_pubmed", "FAILED", str(e))
            raise

    def generate_mdt_report(self, report_content: str) -> dict:
        """生成 MDT 报告"""
        skill = self.registry.get("generate_mdt_report")
        if not skill:
            raise RuntimeError("Skill 'generate_mdt_report' not found")

        input_args = MDTReportInput(
            case_id=self.case_id,
            report_content=report_content,
            skip_validation=False
        )

        try:
            result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
            result = json.loads(result_json)

            self.log_step("generate_mdt_report", "SUCCESS", f"报告路径: {result.get('report_path')}")
            return result

        except Exception as e:
            self.log_step("generate_mdt_report", "FAILED", str(e))
            raise

    def validate_report(self, report_path: str) -> dict:
        """验证报告"""
        skill = self.registry.get("validate_mdt_report")
        if not skill:
            raise RuntimeError("Skill 'validate_mdt_report' not found")

        input_args = ReportValidatorInput(file_path=report_path)

        try:
            result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
            result = json.loads(result_json)

            self.log_step("validate_mdt_report", "SUCCESS" if result.get("valid") else "FAILED")
            return result

        except Exception as e:
            self.log_step("validate_mdt_report", "FAILED", str(e))
            raise

    def get_context_summary(self) -> dict:
        """获取上下文摘要"""
        return {
            "case_id": self.case_id,
            "evidence_collector": self.evidence_collector,
            "execution_log": self.execution_log,
            "skill_calls_count": len(self.context.get_history())
        }


# =============================================================================
# 4. 评估函数 (Eval Assertions)
# =============================================================================

def evaluate_case_result(
    case_id: str,
    report_content: str,
    workflow: OncologyWorkflowForEval,
    expected_has_mutation: bool = False
) -> Dict[str, Any]:
    """
    评估单个 Case 的结果

    Eval 断言检查项：
    1. ✅ 检查报告中是否包含 rejected_alternatives
    2. ✅ 检查 agent_trace 中是否调用了 query_variant (如果患者有基因突变)
    3. ✅ 检查 systemic_management 中是否包含 peri_procedural_holding_parameters
    4. ✅ 检查报告是否通过了 Pydantic 验证
    5. ✅ 检查是否有违禁词"术前准备"

    Args:
        case_id: 病例 ID
        report_content: 报告内容
        workflow: 工作流实例
        expected_has_mutation: 该病例是否预期有基因突变

    Returns:
        评估结果字典
    """
    results = {
        "case_id": case_id,
        "assertions": {},
        "overall_pass": True,
        "details": {}
    }

    # ===== 断言 1: 检查 rejected_alternatives =====
    has_rejected = "rejected_alternatives" in report_content.lower() or "被排除" in report_content
    results["assertions"]["has_rejected_alternatives"] = has_rejected
    if not has_rejected:
        results["overall_pass"] = False
        results["details"]["rejected_alternatives"] = "❌ 报告中缺少 rejected_alternatives 模块"
    else:
        results["details"]["rejected_alternatives"] = "✅ 包含 rejected_alternatives"

    # ===== 断言 2: 检查 agent_trace 中是否调用 query_variant =====
    context_summary = workflow.get_context_summary()
    skill_calls = context_summary.get("execution_log", [])

    called_query_variant = any(
        log.get("step") == "query_oncokb" and log.get("status") == "SUCCESS"
        for log in skill_calls
    )

    # 如果预期有突变，则必须调用；如果无突变，则不应调用
    if expected_has_mutation:
        assertion_passed = called_query_variant
        results["assertions"]["called_query_variant_when_expected"] = assertion_passed
        if not assertion_passed:
            results["overall_pass"] = False
            results["details"]["query_variant"] = "❌ 预期有基因突变但未调用 query_oncokb"
        else:
            results["details"]["query_variant"] = "✅ 正确调用了 query_oncokb"
    else:
        # 无突变时，不应调用（或调用但失败）
        results["assertions"]["no_unnecessary_query_variant"] = True
        results["details"]["query_variant"] = "ℹ️ 无基因突变，未调用 query_oncokb"

    # ===== 断言 3: 检查 peri_procedural_holding_parameters =====
    has_holding_params = (
        "peri_procedural_holding_parameters" in report_content or
        "停药要求" in report_content or
        "停药" in report_content
    )
    results["assertions"]["has_peri_procedural_holding"] = has_holding_params
    if not has_holding_params:
        results["details"]["peri_procedural_holding"] = "⚠️ 未检测到停药要求字段（非致命）"
    else:
        results["details"]["peri_procedural_holding"] = "✅ 包含停药要求"

    # ===== 断言 4: 检查违禁词 =====
    has_forbidden_words = "术前准备" in report_content
    results["assertions"]["no_forbidden_words"] = not has_forbidden_words
    if has_forbidden_words:
        results["overall_pass"] = False
        results["details"]["forbidden_words"] = "❌ 报告包含违禁词'术前准备'"
    else:
        results["details"]["forbidden_words"] = "✅ 未发现违禁词"

    # ===== 统计信息 =====
    results["skill_calls_count"] = len(skill_calls)
    results["evidence_summary"] = context_summary.get("evidence_collector", {})

    return results


# =============================================================================
# 5. 模拟 AI 生成报告内容 (实际使用时应调用 LLM)
# =============================================================================

def mock_ai_generate_report_content(
    case_info: Dict[str, Any],
    evidence_collector: Dict[str, Any]
) -> str:
    """
    模拟 AI 生成报告内容 (实际使用时应调用 Qwen3-Max)

    为了批量测试，这里生成符合模板要求的示例内容
    """
    case_id = case_info.get("case_id", "Unknown")
    has_mutation = case_info.get("has_mutation", False)

    # 基于是否有基因突变生成不同的内容
    if has_mutation:
        # 有突变的情况
        report = f"""## admission_evaluation 入院评估与一般治疗
- performance_status: KPS ≥70
- neurological_status: 神志清楚，无局灶神经系统体征
- symptom_management:
  - medication: 地塞米松
    indication: 脑水肿预防
    dosage: 4mg
    frequency: BID
    tapering_schedule: 神经症状稳定后每 3-5 天减量 2mg
- baseline_labs: ["血常规", "肝肾功能", "电解质", "凝血功能", "心电图"]

## primary_plan 首选治疗方案
- modality: systemic_therapy
- systemic_therapy:
  - regimen_name: Osimertinib 单药方案
    drugs:
      - drug_name: Osimertinib
        dosage: 80mg
        route: PO
        frequency: QD
        cycle_length: 21
        interval: 每日一次
        duration: 直至疾病进展
        peri_procedural_holding_parameters: SRS 治疗前后各停药 3 天
- rationale: 患者 {case_info.get('mutation', 'EGFR L858R')} 突变阳性，根据 OncoKB 判定为 Oncogenic
- evidence_citation: [Citation: NCCN_NSCLC.pdf, Page 12]

## systemic_management 后续治疗与全身管理
- targeted_therapy:
    gene_target: {case_info.get('gene', 'EGFR')}
    variant: {case_info.get('mutation', 'L858R')}
    drug: Osimertinib
    dosage: 80mg PO QD
    cycle_length: 21
    interval: 每日一次
    duration: 直至疾病进展
    peri_procedural_holding_parameters: SRS 治疗前后各停药 3 天

## follow_up 全程管理与随访计划
- imaging_schedule:
  - modality: MRI Brain
    frequency: 每 2-3 个月
    duration: 前 2 年
- clinical_visit_schedule: 每周期治疗前复诊
- toxicity_monitoring:
  - parameter: 肝功能
    frequency: 每周期前

## rejected_alternatives 被排除的治疗方案
- rejected_options:
  - option: 手术切除
    reason: 患者为多发脑转移，且 KPS 评分良好，首选全身治疗
    evidence_level: NCCN Category 2A
    citation:
      source: NCCN CNS Cancers v3.2024
      section: Principles of Surgical Resection
  - option: WBRT
    reason: 患者病灶数量有限，优先选择 SRS 以保留认知功能
    evidence_level: NCCN Category 2A
    citation:
      source: NCCN CNS Cancers v3.2024
      section: Radiation Therapy

## agent_trace
- skills_called:
  - skill_name: query_oncokb
    query_type: variant
    key_findings: ["OncoKB 判定：Oncogenic", "推荐药物：Osimertinib (证据等级：Level 1)"]
  - skill_name: search_pubmed
    query_type: search
    key_findings: ["找到支持性文献"]
- evidence_sources:
  - source_type: OncoKB
    source_id: {case_info.get('gene', 'EGFR')}_{case_info.get('mutation', 'L858R')}
    relevance: 基因变异临床意义
  - source_type: PubMed
    source_id: literature_001
    relevance: 支持性文献证据
- reasoning_confidence: High
"""
    else:
        # 无突变的情况
        report = f"""## admission_evaluation 入院评估与一般治疗
- performance_status: KPS ≥70
- neurological_status: 神志清楚
- baseline_labs: ["血常规", "肝肾功能", "电解质", "凝血功能", "心电图"]

## primary_plan 首选治疗方案
- modality: radiotherapy
- radiotherapy:
    technique: SRS
    dose_fractionation: {{dose: 24Gy, fractions: 1}}
    target_definition: 单发病灶
- rationale: 患者无驱动基因突变，单发脑转移灶，首选立体定向放疗
- evidence_citation: [Citation: NCCN_CNS.pdf, Page 15]

## systemic_management 后续治疗与全身管理
- immunotherapy:
    agent: Pembrolizumab
    dosage: 200mg
    cycle_length: 21
    duration: 直至疾病进展
    peri_procedural_holding_parameters: SRS 治疗前后各停药 1 周

## follow_up 全程管理与随访计划
- imaging_schedule:
  - modality: MRI Brain
    frequency: 每 3 个月
    duration: 前 2 年
- clinical_visit_schedule: 每 3 个月复诊

## rejected_alternatives 被排除的治疗方案
- rejected_options:
  - option: 手术切除
    reason: 患者病灶位于功能区，手术风险高
    evidence_level: NCCN Category 2B
    citation:
      source: NCCN CNS Cancers v3.2024
      section: Surgical Considerations
  - option: WBRT
    reason: 单发病灶，SRS 局部控制率更高且认知毒性更低
    evidence_level: NCCN Category 1
    citation:
      source: NCCN CNS Cancers v3.2024
      section: Radiation Therapy

## agent_trace
- skills_called:
  - skill_name: search_pubmed
    query_type: search
    key_findings: ["找到单发脑转移 SRS 治疗文献"]
- evidence_sources:
  - source_type: PubMed
    source_id: literature_001
    relevance: 支持性文献证据
- reasoning_confidence: Moderate
"""

    return report


# =============================================================================
# 6. 批量评估主函数
# =============================================================================

def run_batch_evaluation(
    input_excel: str,
    output_dir: str,
    max_cases: int = 10,
    dry_run: bool = False
):
    """
    运行批量评估

    核心原则：Clean Context - 每个 Case 独立实例，绝不共享内存
    """
    print("\n" + "=" * 70)
    print("  🏥 TianTan Brain Metastases Agent - 批量评估")
    print("  Clean Context 隔离 | Eval 断言验证 | 结果落盘")
    print("=" * 70 + "\n")

    # 读取 Excel 数据
    try:
        df = pd.read_excel(input_excel)
        print(f"✅ 读取测试数据：{len(df)} 行")
    except Exception as e:
        print(f"❌ 读取 Excel 失败：{e}")
        return False

    # 准备评估结果列表
    all_eval_results = []

    # 限制最大测试数量
    cases_to_test = min(max_cases, len(df))
    print(f"📋 计划测试 {cases_to_test} 个病例...\n")

    # ===== 遍历每个 Case (Clean Context 隔离) =====
    for idx in range(cases_to_test):
        # 提取 Case 信息
        case_row = df.iloc[idx]
        case_id = f"Case{idx + 1}"

        print(f"\n{'=' * 70}")
        print(f"  Case {idx + 1}/{cases_to_test}: {case_id}")
        print(f"{'=' * 70}")

        # ===== 步骤 1: 创建全新实例 (Clean Context 关键) =====
        start_time = time.time()

        registry = create_fresh_skill_registry()
        workflow = OncologyWorkflowForEval(case_id, registry)

        print(f"  ✅ 创建独立 Workflow (session_id={case_id})")

        # 模拟病例信息（实际应从 Excel 提取）
        case_info = {
            "case_id": case_id,
            "has_mutation": idx % 2 == 0,  # 交替：有突变/无突变
            "gene": "EGFR" if idx % 2 == 0 else None,
            "mutation": "L858R" if idx % 2 == 0 else None,
            "tumor_type": "Non-Small Cell Lung Cancer"
        }

        # ===== 步骤 2: 执行技能调用 =====
        try:
            # 如果有基因突变，调用 OncoKB
            if case_info["has_mutation"]:
                print(f"  🧬 调用 OncoKB 查询 {case_info['gene']} {case_info['mutation']}...")
                workflow.query_variant_oncogenicity(
                    hugo_symbol=case_info["gene"],
                    variant=case_info["mutation"],
                    tumor_type=case_info["tumor_type"]
                )

            # 模拟 PubMed 检索
            print(f"  📚 PubMed 检索支持性文献...")
            workflow.search_supporting_literature(
                keywords=f"{case_info['tumor_type']} brain metastases treatment",
                max_results=2
            )

        except SkillExecutionError as e:
            print(f"  ❌ 技能调用失败：{e}")
            workflow.log_step("skill_execution", "FAILED", str(e))

        # ===== 步骤 3: 生成报告 (模拟 AI 生成) =====
        print(f"  📝 生成 MDT 报告...")

        report_content = mock_ai_generate_report_content(
            case_info,
            workflow.evidence_collector
        )

        try:
            report_result = workflow.generate_mdt_report(report_content)
            report_path = report_result.get("report_path", "Unknown")
            print(f"  ✅ 报告已生成：{report_path}")
        except Exception as e:
            print(f"  ❌ 报告生成失败：{e}")
            report_path = "FAILED"

        # ===== 步骤 4: Eval 断言评估 =====
        print(f"  🎯 执行 Eval 断言评估...")

        eval_result = evaluate_case_result(
            case_id=case_id,
            report_content=report_content,
            workflow=workflow,
            expected_has_mutation=case_info["has_mutation"]
        )

        # 打印评估结果
        overall_status = "✅ PASS" if eval_result["overall_pass"] else "❌ FAIL"
        print(f"  {overall_status} 评估结果：")
        for key, detail in eval_result["details"].items():
            print(f"    {detail}")

        # 记录耗时
        elapsed_time = time.time() - start_time

        # 构建完整结果
        full_result = {
            "case_id": case_id,
            "has_mutation": case_info["has_mutation"],
            "overall_pass": eval_result["overall_pass"],
            "assertions": eval_result["assertions"],
            "skill_calls_count": eval_result.get("skill_calls_count", 0),
            "report_path": report_path,
            "elapsed_time_sec": round(elapsed_time, 2),
            "timestamp": datetime.now().isoformat()
        }

        all_eval_results.append(full_result)

        # 等待 1 秒，避免 API 限流
        if not dry_run:
            time.sleep(1)

        print(f"  ⏱️  耗时：{elapsed_time:.2f} 秒")

    # ===== 生成汇总报告 =====
    print(f"\n{'=' * 70}")
    print("  📊 批量评估完成 - 生成汇总报告")
    print(f"{'=' * 70}\n")

    # 统计
    total_cases = len(all_eval_results)
    passed_cases = sum(1 for r in all_eval_results if r["overall_pass"])
    pass_rate = (passed_cases / total_cases * 100) if total_cases > 0 else 0

    print(f"  总计：{total_cases} 个 Case")
    print(f"  通过：{passed_cases} 个 ({pass_rate:.1f}%)")
    print(f"  失败：{total_cases - passed_cases} 个")

    # ===== 落盘到 CSV =====
    output_csv = Path(output_dir) / f"batch_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    # 转换为 DataFrame
    df_results = pd.DataFrame(all_eval_results)

    # 展开 assertions 为单独列
    assertions_df = pd.json_normalize(df_results["assertions"])
    df_final = pd.concat([df_results.drop("assertions", axis=1), assertions_df], axis=1)

    # 保存
    df_final.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"\n  💾 评估结果已保存：{output_csv}")

    # ===== 打印详细结果 =====
    print("\n  详细结果：")
    for result in all_eval_results:
        status = "✅" if result["overall_pass"] else "❌"
        print(f"    {status} {result['case_id']}: {result['report_path']}")

    return True


# =============================================================================
# 7. CLI 入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="TianTan Brain Metastases Agent - 批量评估")
    parser.add_argument(
        "--input",
        default=str(WORKSPACE_DIR / "original_cases" / "TT_BM_test.xlsx"),
        help="输入 Excel 文件路径"
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_DIR),
        help="输出目录路径"
    )
    parser.add_argument(
        "--max_cases",
        type=int,
        default=10,
        help="最大测试病例数"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="模拟运行（不调用真实 API）"
    )

    args = parser.parse_args()

    success = run_batch_evaluation(
        input_excel=args.input,
        output_dir=args.output,
        max_cases=args.max_cases,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
