#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 肿瘤主治医师 v2.3 - 基于专家级临床约束的重构版

与 v2.0 的区别：
1. 整合 OncoKB 和 PubMed 外部 API Skill，形成网状推理调用
2. 引入 Order Sets 模板机制，强制结构化临床输出
3. 支持 4 大临床模块 + 排他性分析 + Agent 追踪
4. 强化激素管理、围手术期停药、分子病理送检要求

适用场景：需要极细临床颗粒度和循证医学依据的 MDT 诊疗决策
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

# 引入 Skill 架构
from core.skill import SkillContext, SkillRegistry, SkillExecutionError

# === 基础 Skill ===
from skills.pdf_inspector.scripts.parse_pdf import PDFInspector, PDFInspectorInput
from skills.clinical_writer.scripts.generate_report import MDTReportGenerator, MDTReportInput
from skills.clinical_writer.scripts.validate_report import ReportValidator, ReportValidatorInput

# === 肿瘤专科 API Skill (v2.2.0 新增) ===
from skills.oncokb_query.scripts.query_variant import OncoKBQuery, OncoKBQueryInput, QueryType
from skills.pubmed_search.scripts.search_articles import PubMedSearch, PubMedSearchInput, QueryType as PubMedQueryType


# =============================================================================
# 1. 严格锁定工作区 (Sandbox Isolation)
# =============================================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CASES_DIR = os.path.join(PROJECT_ROOT, "workspace", "cases")
TEMP_DIR = os.path.join(PROJECT_ROOT, "workspace", "temp")
os.makedirs(CASES_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# =============================================================================
# 2. 注册 Skill (整合所有 6 个 Skill)
# =============================================================================

def create_skill_registry(oncokb_token: Optional[str] = None, pubmed_email: Optional[str] = None) -> SkillRegistry:
    """
    创建并注册所有可用的 Skill。

    Args:
        oncokb_token: OncoKB API Token，可选（默认从环境变量读取）
        pubmed_email: PubMed 注册邮箱，可选（默认从环境变量读取）

    Returns:
        已注册的 SkillRegistry 实例
    """
    registry = SkillRegistry()

    # 注册 PDF Inspector
    registry.register(PDFInspector())

    # 注册 MDT Report Generator
    registry.register(MDTReportGenerator())

    # 注册 Report Validator
    registry.register(ReportValidator())

    # 注册 OncoKB Query (v2.2.0)
    registry.register(OncoKBQuery(api_token=oncokb_token))

    # 注册 PubMed Search (v2.2.0)
    registry.register(PubMedSearch(email=pubmed_email))

    return registry


# =============================================================================
# 3. 临床工作流编排器 (重构版 - 网状推理)
# =============================================================================

class OncologyWorkflow:
    """
    肿瘤诊疗工作流编排器 - v2.3 重构版。

    核心变更：
    1. 从线性流程升级为网状推理：先查询 OncoKB/PubMed 获取循证依据，再生成报告
    2. 每个患者一个独立的 SkillContext，追踪所有调用历史
    3. 支持动态分支：根据患者情况选择手术/放疗/全身治疗

    工作流：
    1. 解析患者病历 PDF → 提取关键信息（基因变异、癌症类型、KPS 评分）
    2. 查询 OncoKB → 获取变异致癌性和药物敏感性
    3. 查询 PubMed → 获取支持性文献证据
    4. 查询诊疗指南 → 获取 NCCN/ESMO 推荐
    5. 综合所有证据生成 MDT 报告（Order Sets 模板填空）
    6. 验证报告合规性
    """

    def __init__(self, case_id: str, registry: SkillRegistry):
        self.case_id = case_id
        self.registry = registry
        # 每个患者一个独立的上下文
        self.context = SkillContext(session_id=case_id)

        # 设置元数据
        self.context.set_metadata("case_id", case_id)
        self.context.set_metadata("project_root", PROJECT_ROOT)
        self.context.set_metadata("created_at", datetime.now().isoformat())

        # 证据收集容器（用于填充 agent_trace）
        self.evidence_collector: Dict[str, Any] = {
            "oncokb_findings": [],
            "pubmed_findings": [],
            "guideline_findings": []
        }

    # ========== Step 1: 解析患者病历 ==========

    def parse_patient_record(self, pdf_path: str, extract_images: bool = True) -> dict:
        """
        Step 1: 解析患者病历 PDF。

        Args:
            pdf_path: 病历 PDF 路径
            extract_images: 是否提取影像图片

        Returns:
            解析结果字典
        """
        skill = self.registry.get("parse_medical_pdf")
        if not skill:
            raise RuntimeError("Skill 'parse_medical_pdf' not found")

        input_args = PDFInspectorInput(
            file_path=pdf_path,
            page_start=1,
            page_end=None,
            extract_images=extract_images
        )

        start_time = datetime.now()
        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = json.loads(result_json)

        # 记录到证据收集器
        self.evidence_collector["patient_record_parsed"] = {
            "total_pages": result.get("total_pages"),
            "extracted_visuals_count": len(result.get("extracted_visuals", [])),
            "timestamp": start_time.isoformat()
        }

        # 存入 Context，供后续步骤使用
        self.context.set("patient_record_parsed", result)

        return result

    # ========== Step 2: 查询 OncoKB (新增) ==========

    def query_variant_oncogenicity(
        self,
        hugo_symbol: str,
        variant: str,
        tumor_type: str
    ) -> dict:
        """
        Step 2: 查询 OncoKB 获取基因变异的致癌性和治疗敏感性。

        Args:
            hugo_symbol: 基因符号（如 "EGFR"）
            variant: 变异描述（如 "L858R"）
            tumor_type: 癌症类型（如 "Non-Small Cell Lung Cancer"）

        Returns:
            OncoKB 查询结果
        """
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

        start_time = datetime.now()
        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = json.loads(result_json)

        # 提取关键发现
        data = result.get("data", {})
        key_findings = []

        # 提取致癌性判定
        oncogenicity = data.get("oncogenicity", "")
        if oncogenicity:
            key_findings.append(f"OncoKB 判定：{oncogenicity}")

        # 提取治疗推荐
        treatments = data.get("treatments", [])
        for tx in treatments[:3]:  # 最多取前 3 条
            drug = tx.get("drug", {}).get("drugName", "Unknown")
            level = tx.get("level", {}).get("level", "Unknown")
            key_findings.append(f"推荐药物：{drug} (证据等级：{level})")

        # 记录到证据收集器
        self.evidence_collector["oncokb_findings"].append({
            "gene": hugo_symbol,
            "variant": variant,
            "oncogenicity": oncogenicity,
            "treatments_count": len(treatments),
            "key_findings": key_findings,
            "duration_ms": duration_ms,
            "timestamp": start_time.isoformat()
        })

        # 存入 Context
        self.context.set(f"oncokb_{hugo_symbol}_{variant}", result)

        return result

    # ========== Step 3: 查询 PubMed (新增) ==========

    def search_supporting_literature(
        self,
        keywords: str,
        max_results: int = 5
    ) -> dict:
        """
        Step 3: 查询 PubMed 获取支持性文献证据。

        Args:
            keywords: 搜索关键词
            max_results: 最大结果数

        Returns:
            PubMed 查询结果
        """
        skill = self.registry.get("search_pubmed")
        if not skill:
            raise RuntimeError("Skill 'search_pubmed' not found")

        input_args = PubMedSearchInput(
            query_type=PubMedQueryType.SEARCH,
            keywords=keywords,
            max_results=max_results,
            sort="relevance"
        )

        start_time = datetime.now()
        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = json.loads(result_json)

        # 提取关键发现
        data = result.get("data", {})
        articles = data.get("articles", [])

        key_findings = []
        pmids = []
        for article in articles[:3]:  # 最多取前 3 篇
            title = article.get("title", "No Title")
            pmid = article.get("pmid", "Unknown")
            journal = article.get("journal", "Unknown")
            year = article.get("year", "Unknown")
            key_findings.append(f"{title[:80]}... ({journal}, {year}) PMID: {pmid}")
            pmids.append(pmid)

        # 记录到证据收集器
        self.evidence_collector["pubmed_findings"].append({
            "search_query": keywords,
            "total_results": data.get("total_results", 0),
            "pmids": pmids,
            "key_findings": key_findings,
            "duration_ms": duration_ms,
            "timestamp": start_time.isoformat()
        })

        # 存入 Context
        self.context.set(f"pubmed_{keywords.replace(' ', '_')}", result)

        return result

    # ========== Step 4: 查询诊疗指南 ==========

    def query_guideline(self, guideline_path: str, topic: str) -> dict:
        """
        Step 4: 查询诊疗指南。

        Args:
            guideline_path: 指南 PDF 路径
            topic: 查询主题

        Returns:
            指南相关内容
        """
        skill = self.registry.get("parse_medical_pdf")
        if not skill:
            raise RuntimeError("Skill 'parse_medical_pdf' not found")

        input_args = PDFInspectorInput(
            file_path=guideline_path,
            page_start=1,
            extract_images=False
        )

        start_time = datetime.now()
        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = json.loads(result_json)

        # 记录到证据收集器
        self.evidence_collector["guideline_findings"].append({
            "guideline_path": guideline_path,
            "topic": topic,
            "total_pages": result.get("total_pages"),
            "duration_ms": duration_ms,
            "timestamp": start_time.isoformat()
        })

        # 存入 Context
        self.context.set(f"guideline_{topic}", result)

        return result

    # ========== Step 5: 生成 MDT 报告 (重构版) ==========

    def generate_mdt_report(
        self,
        report_content: str,
        skip_validation: bool = False
    ) -> dict:
        """
        Step 5: 生成 MDT 报告（基于 Order Sets 模板）。

        Args:
            report_content: 报告内容（Markdown，需符合 Order Sets 模板结构）
            skip_validation: 是否跳过验证

        Returns:
            生成结果
        """
        skill = self.registry.get("generate_mdt_report")
        if not skill:
            raise RuntimeError("Skill 'generate_mdt_report' not found")

        # 构建 agent_trace 内容
        agent_trace = self._build_agent_trace()

        # 将 agent_trace 追加到报告内容中
        full_content = f"{report_content}\n\n## Agent Trace\n\n```json\n{json.dumps(agent_trace, ensure_ascii=False, indent=2)}\n```"

        input_args = MDTReportInput(
            case_id=self.case_id,
            report_content=full_content,
            skip_validation=skip_validation
        )

        start_time = datetime.now()
        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = json.loads(result_json)

        # 存入 Context
        self.context.set("mdt_report_path", result.get("report_path"))

        return result

    def _build_agent_trace(self) -> Dict[str, Any]:
        """
        构建 Agent Trace 内容。

        Returns:
            Agent Trace 字典
        """
        skills_called = []

        # 从 Context 获取调用历史
        history = self.context.get_history()
        for record in history:
            key_findings = []

            # 根据 skill 类型提取关键发现
            if record.skill_name == "query_oncokb":
                findings = self.evidence_collector["oncokb_findings"]
                for f in findings:
                    key_findings.extend(f.get("key_findings", []))
            elif record.skill_name == "search_pubmed":
                findings = self.evidence_collector["pubmed_findings"]
                for f in findings:
                    key_findings.extend(f.get("key_findings", []))

            skills_called.append({
                "skill_name": record.skill_name,
                "query_type": None,  # 可根据需要补充
                "key_findings": key_findings,
                "duration_ms": record.duration_ms,
                "timestamp": record.timestamp.isoformat()
            })

        # 构建证据来源
        evidence_sources = []

        for onco in self.evidence_collector.get("oncokb_findings", []):
            evidence_sources.append({
                "source_type": "OncoKB",
                "source_id": f"{onco.get('gene', '')}_{onco.get('variant', '')}",
                "relevance": f"基因变异临床意义：{onco.get('oncogenicity', '')}"
            })

        for pubmed in self.evidence_collector.get("pubmed_findings", []):
            for pmid in pubmed.get("pmids", []):
                evidence_sources.append({
                    "source_type": "PubMed",
                    "source_id": str(pmid),
                    "relevance": f"支持性文献证据"
                })

        # 自我评估信心
        reasoning_confidence = "Moderate"
        if len(evidence_sources) >= 3:
            reasoning_confidence = "High"
        elif len(evidence_sources) == 0:
            reasoning_confidence = "Low"

        return {
            "skills_called": skills_called,
            "evidence_sources": evidence_sources,
            "reasoning_confidence": reasoning_confidence,
            "uncertainty_factors": []  # 可根据需要补充
        }

    # ========== Step 6: 验证报告 ==========

    def validate_report(self, report_path: str) -> dict:
        """
        Step 6: 验证报告合规性。

        Args:
            report_path: 报告文件路径

        Returns:
            验证结果
        """
        skill = self.registry.get("validate_mdt_report")
        if not skill:
            raise RuntimeError("Skill 'validate_mdt_report' not found")

        input_args = ReportValidatorInput(file_path=report_path)

        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        result = json.loads(result_json)

        return result

    # ========== 上下文管理 ==========

    def get_context_summary(self) -> dict:
        """获取当前上下文摘要（用于调试）"""
        return self.context.get_summary()

    def get_call_history(self) -> list:
        """获取所有 Skill 调用历史"""
        return self.context.get_history()

    def get_evidence_summary(self) -> dict:
        """获取证据摘要"""
        return self.evidence_collector


# =============================================================================
# 4. 主函数 - 完整诊疗流程示例
# =============================================================================

def run_full_workflow(
    case_id: str,
    patient_pdf_path: str,
    guideline_pdf_path: str,
    gene_symbol: Optional[str] = None,
    gene_variant: Optional[str] = None,
    tumor_type: Optional[str] = None,
    literature_keywords: Optional[str] = None
):
    """
    运行完整的诊疗工作流。

    流程：
    1. 解析患者病历
    2. 查询 OncoKB（基因变异临床意义）
    3. 查询 PubMed（支持性文献）
    4. 查询诊疗指南
    5. 生成 MDT 报告（Order Sets 模板填空）
    6. 验证报告合规性

    Args:
        case_id: 患者病例 ID
        patient_pdf_path: 患者病历 PDF 路径
        guideline_pdf_path: 诊疗指南 PDF 路径
        gene_symbol: 基因符号（如 "EGFR"）
        gene_variant: 变异描述（如 "L858R"）
        tumor_type: 癌症类型（如 "Non-Small Cell Lung Cancer"）
        literature_keywords: 文献搜索关键词
    """
    print(f"\n{'='*70}")
    print(f"🏥 AI 肿瘤主治医师 v2.3 - 专家级临床约束版")
    print(f"📋 病例：{case_id}")
    print(f"{'='*70}\n")

    # 初始化
    registry = create_skill_registry()
    workflow = OncologyWorkflow(case_id, registry)

    # Step 1: 解析患者病历
    print("📄 Step 1: 解析患者病历 PDF...")
    try:
        patient_record = workflow.parse_patient_record(patient_pdf_path)
        print(f"   ✅ 解析成功，共 {patient_record['total_pages']} 页")
        if patient_record.get('extracted_visuals'):
            print(f"   🖼️  提取了 {len(patient_record['extracted_visuals'])} 张医学影像")
    except SkillExecutionError as e:
        print(f"   ❌ 解析失败：{e}")
        return

    # Step 2: 查询 OncoKB
    if gene_symbol and gene_variant and tumor_type:
        print(f"\n🧬 Step 2: 查询 OncoKB ({gene_symbol} {gene_variant})...")
        try:
            oncokb_result = workflow.query_variant_oncogenicity(
                hugo_symbol=gene_symbol,
                variant=gene_variant,
                tumor_type=tumor_type
            )
            data = oncokb_result.get("data", {})
            oncogenicity = data.get("oncogenicity", "Unknown")
            treatments = data.get("treatments", [])
            print(f"   ✅ OncoKB 判定：{oncogenicity}")
            print(f"   💊 治疗推荐：{len(treatments)} 条")
        except SkillExecutionError as e:
            print(f"   ❌ OncoKB 查询失败：{e}")
    else:
        print("\n⏭️  Step 2: 跳过 OncoKB 查询（缺少 gene_symbol/variant/tumor_type 参数）")

    # Step 3: 查询 PubMed
    if literature_keywords:
        print(f"\n📚 Step 3: 查询 PubMed ({literature_keywords[:30]}...)...")
        try:
            pubmed_result = workflow.search_supporting_literature(
                keywords=literature_keywords,
                max_results=5
            )
            data = pubmed_result.get("data", {})
            total = data.get("total_results", 0)
            print(f"   ✅ 检索到 {total} 篇文献")
        except SkillExecutionError as e:
            print(f"   ❌ PubMed 查询失败：{e}")
    else:
        print("\n⏭️  Step 3: 跳过 PubMed 查询（缺少 keywords 参数）")

    # Step 4: 查询诊疗指南
    print("\n📖 Step 4: 查询诊疗指南...")
    try:
        guideline = workflow.query_guideline(guideline_pdf_path, "nsclc_treatment")
        print(f"   ✅ 指南解析成功，共 {guideline['total_pages']} 页")
    except SkillExecutionError as e:
        print(f"   ❌ 指南查询失败：{e}")
        return

    # Step 5: 生成 MDT 报告
    print("\n📝 Step 5: 生成 MDT 报告（Order Sets 模板填空）...")

    # 这里需要 AI 大模型生成实际内容
    # 下面是示例内容，实际使用时应调用 LLM 生成
    sample_report = f"""## 入院评估与一般治疗

### performance_status
KPS ≥70

### neurological_status
神志清楚，无局灶神经系统体征，无癫痫发作史

### symptom_management
- medication: 地塞米松
  indication: 脑水肿预防
  dosage: 4mg
  frequency: BID
  tapering_schedule: 神经症状稳定后每 3-5 天减量 2mg，目标最低有效剂量或停药

### baseline_labs
["血常规", "肝肾功能", "电解质", "凝血功能", "心电图"]

## 首选治疗方案

### modality
systemic_therapy

### systemic_therapy
- regimen_name: Osimertinib 单药方案
- drugs:
  - drug_name: Osimertinib
    dosage: 80mg
    route: PO
    frequency: QD
    cycle_length: 21
    interval: 每日一次，连续服用
    duration: 直至疾病进展或不可耐受毒性
    peri_procedural_holding_parameters: SRS 治疗前后各停药 3 天，以降低放射性脑坏死风险

### rationale
患者 {gene_symbol or 'EGFR'} {gene_variant or 'L858R'} 突变阳性，根据 OncoKB 判定为 Oncogenic，推荐 Osimertinib 一线治疗

### evidence_citation
[Citation: NCCN_NSCLC.pdf, Page 12]

## 后续治疗与全身管理

### targeted_therapy
- gene_target: {gene_symbol or 'EGFR'}
- variant: {gene_variant or 'L858R'}
- drug: Osimertinib
- dosage: 80mg PO QD
- cycle_length: 21
- interval: 每日一次
- duration: 直至疾病进展或不可耐受毒性
- peri_procedural_holding_parameters: SRS 治疗前后各停药 3 天

## 全程管理与随访计划

### imaging_schedule
- modality: MRI Brain
  frequency: 每 2-3 个月
  duration: 前 2 年，之后每 6 个月
- modality: CT Chest/Abdomen
  frequency: 每 3 个月
  duration: 直至进展

### clinical_visit_schedule
每周期治疗前复诊，或出现新发症状时随诊

### toxicity_monitoring
- parameter: 肝功能
  frequency: 每周期前
- parameter: 心电图
  frequency: 基线及每 3 个月

## 被排除的治疗方案

### rejected_options
1. option: 手术切除
   reason: 患者为多发脑转移，且 KPS 评分良好，首选全身治疗
   evidence_level: NCCN Category 2A
   citation:
     source: NCCN CNS Cancers v3.2024
     section: Principles of Surgical Resection

2. option: WBRT
   reason: 患者病灶数量有限，优先选择 SRS 以保留认知功能
   evidence_level: NCCN Category 2A
   citation:
     source: NCCN CNS Cancers v3.2024
     section: Radiation Therapy
"""

    try:
        report_result = workflow.generate_mdt_report(sample_report)
        print(f"   ✅ 报告已生成：{report_result['report_path']}")
        print(f"   📋 模板版本：{report_result.get('template_version', 'Unknown')}")
    except SkillExecutionError as e:
        print(f"   ❌ 报告生成失败：{e}")
        return

    # Step 6: 验证报告
    print("\n✅ Step 6: 验证报告合规性...")
    try:
        validation_result = workflow.validate_report(report_result['report_path'])
        if validation_result['valid']:
            print(f"   ✅ 验证通过：{validation_result['message']}")
        else:
            print(f"   ⚠️  验证未通过:")
            for error in validation_result['errors']:
                print(f"      - {error}")
    except SkillExecutionError as e:
        print(f"   ❌ 验证失败：{e}")
        return

    # 输出总结
    print("\n" + "="*70)
    print("📊 工作流执行完成")
    print("="*70)

    # 证据摘要
    evidence = workflow.get_evidence_summary()
    print(f"\n📌 证据摘要:")
    print(f"   - OncoKB 查询：{len(evidence.get('oncokb_findings', []))} 次")
    print(f"   - PubMed 检索：{len(evidence.get('pubmed_findings', []))} 次")
    print(f"   - 指南解析：{len(evidence.get('guideline_findings', []))} 次")

    # Skill 调用历史
    history = workflow.get_call_history()
    print(f"\n🔧 Skill 调用历史：共 {len(history)} 次调用")
    for record in history:
        status = "✅" if not record.error else "❌"
        print(f"  {status} {record.skill_name} ({record.duration_ms:.1f}ms, 重试{record.retry_count}次)")

    print(f"\n💾 报告路径：{report_result['report_path']}")


# =============================================================================
# 5. CLI 入口
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI 肿瘤主治医师 v2.3")
    parser.add_argument("--case_id", default="Case1", help="患者病例 ID")
    parser.add_argument("--patient_pdf", default="workspace/test_data/patient_record.pdf", help="患者病历 PDF 路径")
    parser.add_argument("--guideline_pdf", default="workspace/test_data/NCCN_NSCLC.pdf", help="诊疗指南 PDF 路径")
    parser.add_argument("--gene_symbol", help="基因符号（如 EGFR）")
    parser.add_argument("--gene_variant", help="变异描述（如 L858R）")
    parser.add_argument("--tumor_type", help="癌症类型")
    parser.add_argument("--keywords", help="PubMed 检索关键词")
    parser.add_argument("--demo", action="store_true", help="演示模式")

    args = parser.parse_args()

    if args.demo:
        print("🎯 演示模式 - 请确保以下测试文件存在:")
        print("   - workspace/test_data/patient_record.pdf")
        print("   - workspace/test_data/NCCN_NSCLC.pdf")
        print("\n💡 使用示例:")
        print("   python main_oncology_agent_v2.py \\")
        print("     --case_id Case1 \\")
        print("     --gene_symbol EGFR \\")
        print("     --gene_variant L858R \\")
        print("     --tumor_type 'Non-Small Cell Lung Cancer' \\")
        print("     --keywords 'EGFR L858R NSCLC treatment'")
    else:
        # 检查文件是否存在
        if not os.path.exists(args.patient_pdf):
            print(f"❌ 患者病历文件不存在：{args.patient_pdf}")
        elif not os.path.exists(args.guideline_pdf):
            print(f"❌ 诊疗指南文件不存在：{args.guideline_pdf}")
        else:
            run_full_workflow(
                case_id=args.case_id,
                patient_pdf_path=args.patient_pdf,
                guideline_pdf_path=args.guideline_pdf,
                gene_symbol=args.gene_symbol,
                gene_variant=args.gene_variant,
                tumor_type=args.tumor_type,
                literature_keywords=args.keywords
            )
