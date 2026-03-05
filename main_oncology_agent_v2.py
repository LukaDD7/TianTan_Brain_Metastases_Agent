#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 肿瘤主治医师 v2.4 - 指南优先级重构版

与 v2.4 的核心区别：
1. 【Actor-Critic 纠错循环】报告生成后如验证失败，自动重试修订（最多 3 次），实现自我纠错
2. 【证据增强检索】从"降级调用"升级为"指南补充检索"：不仅指南未覆盖时，战术细节缺失或需反面证据时也鼓励调用 PubMed
3. 【防无限循环】PubMed 调用硬上限：单 Case 最多 2 次，每次 max_results=3，防止 Token 爆炸
4. 【更精细的覆盖判定】改进 _analyze_literature_needs，明确区分战略覆盖与战术缺失
2. 【智能路由】集成 LocalGuidelinesManager，自动匹配肿瘤类型与指南文件
3. 【证据层级】明确 OncoKB + 指南为顶级证据，PubMed 仅在指南未覆盖或需反面证据时调用
4. 【防幻觉】指南覆盖判定失败时打印明确警告日志

适用场景：需要极细临床颗粒度、严格循证医学依据、指南优先的 MDT 诊疗决策
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

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
# 1. 本地指南知识库管理器 (Local Guidelines Grounding)
# =============================================================================

class LocalGuidelinesManager:
    """
    本地权威指南智能路由管理器

    职责：
    1. 扫描项目目录下的所有 PDF 指南文件（21 个权威指南）
    2. 构建肿瘤类型 → 指南文件的映射索引
    3. 提供智能匹配：根据肿瘤类型自动返回最相关的指南路径
    4. 支持多指南匹配（如 NSCLC 可同时匹配 NCCN_NSCLC 和 NCCN_CNS）

    关键特性：
    - 强制指南优先：所有查询必须先走指南路径
    - 智能关键词匹配：支持中英文肿瘤类型映射
    - 防遗漏机制：记录匹配失败的肿瘤类型
    """

    def __init__(self, guidelines_dir: Optional[str] = None):
        # 默认指南目录
        if guidelines_dir is None:
            self.guidelines_dir = Path(PROJECT_ROOT) / "Guidelines" / "脑转诊疗指南"
        else:
            self.guidelines_dir = Path(guidelines_dir)

        # 指南索引
        self.guideline_index: Dict[str, Dict[str, Any]] = {}
        # 肿瘤类型映射表（中英文双向）
        self.tumor_type_mappings: Dict[str, List[str]] = {
            "NSCLC": ["NSCLC", "非小细胞肺癌", "non-small cell lung cancer", "lung adenocarcinoma", "肺腺癌"],
            "SCLC": ["SCLC", "小细胞肺癌", "small cell lung cancer"],
            "Breast": ["乳腺癌", "breast cancer", "breast"],
            "Melanoma": ["黑色素瘤", "melanoma"],
            "Colorectal": ["结直肠癌", "colorectal cancer", "CRC"],
            "Renal": ["肾癌", "renal cell carcinoma", "RCC"],
            "CNS": ["CNS", "中枢神经系统", "central nervous system", "脑转移", "brain metastases"]
        }

        # 扫描指南文件
        self._scan_guidelines()
        print(f"\n📚 本地指南知识库加载完成")
        print(f"   找到 {len(self.guideline_index)} 个指南文件")

    def _scan_guidelines(self):
        """扫描目录下的所有 PDF 指南文件"""
        if not self.guidelines_dir.exists():
            print(f"⚠️  指南目录不存在：{self.guidelines_dir}")
            return

        # 递归查找所有 PDF
        pdf_files = list(self.guidelines_dir.rglob("*.pdf"))

        for pdf in pdf_files:
            # 分类
            category = "Practice_Guidelines" if "Practice_Guideline" in str(pdf) else "Review_Articles"

            # 生成简短名称
            name = self._generate_short_name(pdf)

            self.guideline_index[name] = {
                "full_path": str(pdf),
                "relative_path": str(pdf.relative_to(self.guidelines_dir)),
                "category": category,
                "filename": pdf.name,
                "keywords": self._extract_keywords_from_filename(pdf.name)
            }

    def _generate_short_name(self, pdf_path: Path) -> str:
        """生成简短名称"""
        name = pdf_path.stem
        name = name.replace(" ", "_").replace("-", "_").replace(",", "")
        if len(name) > 80:
            name = name[:80] + "..."
        return name

    def _extract_keywords_from_filename(self, filename: str) -> List[str]:
        """从文件名提取关键词（用于匹配肿瘤类型）"""
        keywords = []

        # 标准化文件名
        fname_lower = filename.lower()

        # 常见肿瘤类型关键词
        cancer_keywords = {
            "nsclc": ["nsclc", "non-small cell lung", "lung adenocarcinoma", "肺腺癌"],
            "sclc": ["sclc", "small cell lung", "小细胞肺癌"],
            "breast": ["breast", "乳腺"],
            "melanoma": ["melanoma", "黑色素瘤"],
            "colorectal": ["colorectal", "crc", "结直肠"],
            "renal": ["renal", "肾癌"],
            "cns": ["cns", "brain", "brain metastases", "中枢神经系统", "脑转移"]
        }

        for cancer_type, kw_list in cancer_keywords.items():
            for kw in kw_list:
                if kw in fname_lower:
                    keywords.append(cancer_type)
                    break

        return list(set(keywords))  # 去重

    def match_guidelines_by_tumor_type(
        self,
        tumor_type: str
    ) -> Tuple[List[str], str]:
        """
        根据肿瘤类型智能匹配指南文件路径

        Args:
            tumor_type: 肿瘤类型（如 "Non-Small Cell Lung Cancer"、"黑色素瘤"）

        Returns:
            (matched_paths: List[str], match_reason: str)
            - matched_paths: 匹配到的指南文件路径列表（1-2 个最相关）
            - match_reason: 匹配原因说明（用于日志）

        匹配策略：
        1. 标准化输入肿瘤类型
        2. 查找肿瘤类型映射表
        3. 匹配指南文件名中的关键词
        4. 优先返回 Practice Guidelines，其次返回 Review Articles
        """
        # 标准化输入
        tumor_lower = tumor_type.lower()

        # 查找映射
        matched_cancer_types = []
        for cancer_type, aliases in self.tumor_type_mappings.items():
            for alias in aliases:
                if alias.lower() in tumor_lower:
                    matched_cancer_types.append(cancer_type)
                    break

        if not matched_cancer_types:
            # 未匹配到已知类型，返回 CNS 指南作为兜底
            matched_cancer_types = ["CNS"]
            match_reason = f"⚠️  未识别肿瘤类型 '{tumor_type}'，使用 CNS 指南兜底"
        else:
            match_reason = f"✅ 匹配到肿瘤类型：{', '.join(matched_cancer_types)}"

        # 筛选匹配的指南
        matched_guidelines = []
        for name, info in self.guideline_index.items():
            # 检查指南关键词是否包含匹配的癌症类型
            guideline_keywords = [kw.lower() for kw in info["keywords"]]
            if any(cancer_type.lower() in guideline_keywords for cancer_type in matched_cancer_types):
                matched_guidelines.append((name, info))

        # 按分类排序：优先 Practice Guidelines
        matched_guidelines.sort(
            key=lambda x: 0 if x[1]["category"] == "Practice_Guidelines" else 1
        )

        # 取前 1-2 个最相关的
        top_matches = matched_guidelines[:2]
        matched_paths = [info["full_path"] for _, info in top_matches]

        if not matched_paths:
            # 完全未匹配，返回所有 CNS 相关指南
            matched_paths = [
                info["full_path"]
                for name, info in self.guideline_index.items()
                if "cns" in info["keywords"] or "brain" in info["keywords"]
            ][:2]
            match_reason += f"\n⚠️  未找到精确匹配，返回 CNS 相关指南"

        return matched_paths, match_reason

    def get_all_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指南索引"""
        return self.guideline_index


# =============================================================================
# 2. 严格锁定工作区 (Sandbox Isolation)
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

    def __init__(
        self,
        case_id: str,
        registry: SkillRegistry,
        guidelines_manager: Optional[LocalGuidelinesManager] = None
    ):
        self.case_id = case_id
        self.registry = registry
        self.guidelines_manager = guidelines_manager

        # 每个患者一个独立的上下文
        self.context = SkillContext(session_id=case_id)

        # 设置元数据
        self.context.set_metadata("case_id", case_id)
        self.context.set_metadata("project_root", PROJECT_ROOT)
        self.context.set_metadata("created_at", datetime.now().isoformat())

        # PubMed 调用计数器（防无限循环）
        self.context.set("pubmed_call_count", 0)

        # 证据收集容器（用于填充 agent_trace）
        self.evidence_collector: Dict[str, Any] = {
            "oncokb_findings": [],
            "pubmed_findings": [],
            "guideline_findings": [],
            "guideline_coverage_analysis": None,  # 指南覆盖分析
            "degradation_reason": None            # PubMed 降级调用原因
        }

    # ========== Step 1: 智能指南路由（新增） ==========

    def route_guidelines_by_tumor_type(self, tumor_type: str) -> Tuple[List[str], str]:
        """
        根据肿瘤类型智能路由到最相关的指南文件

        Args:
            tumor_type: 肿瘤类型（如 "Non-Small Cell Lung Cancer"）

        Returns:
            (guideline_paths: List[str], match_reason: str)
        """
        if not self.guidelines_manager:
            raise RuntimeError("LocalGuidelinesManager 未初始化")

        return self.guidelines_manager.match_guidelines_by_tumor_type(tumor_type)

    # ========== Step 2: 强制指南查询（重构） ==========

    def query_guideline_mandatory(
        self,
        guideline_paths: List[str],
        clinical_question: str
    ) -> Dict[str, Any]:
        """
        【强制执行】查询本地权威指南（不可跳过）

        证据优先级：顶级证据（基石）

        Args:
            guideline_paths: 指南文件路径列表（1-2 个）
            clinical_question: 临床问题（如 "NSCLC 脑转移治疗方案"）

        Returns:
            {
                "guidelines_queried": [...],       # 查询的指南列表
                "content": "...",                   # 指南内容摘要
                "covers_question": True/False,      # 指南是否覆盖问题
                "recommended_options": [...],       # 推荐方案
                "excluded_options": [...],          # 排除方案
                "coverage_analysis": {...}          # 覆盖分析详情
            }
        """
        print(f"\n{'='*70}")
        print(f"📖 强制查询本地指南（顶级证据 - 基石）")
        print(f"   临床问题：{clinical_question}")
        print(f"   指南数量：{len(guideline_paths)} 个")
        print(f"{'='*70}\n")

        all_results = []

        for idx, guideline_path in enumerate(guideline_paths):
            print(f"   [{idx+1}/{len(guideline_paths)}] {os.path.basename(guideline_path)[:60]}...")

            try:
                result = self.query_guideline(guideline_path, clinical_question)
                all_results.append({
                    "path": guideline_path,
                    "filename": os.path.basename(guideline_path),
                    "content": result.get("content", "")[:1000] if isinstance(result.get("content"), str) else str(result.get("content"))[:1000],
                    "pages": result.get("total_pages", 0)
                })
            except Exception as e:
                print(f"   ❌ 指南查询失败：{e}")
                all_results.append({
                    "path": guideline_path,
                    "error": str(e)
                })

        # 执行文献需求分析（证据增强）
        # 提取推荐方案用于分析
            clinical_question=clinical_question,
            guidelines_results=all_results
        )

        # 记录到证据收集器
        self.evidence_collector["literature_need_analysis"] = literature_need_analysis

        return {
            "guidelines_queried": guideline_paths,
            "results": all_results,
            "covers_question": coverage_analysis["covered"],
            "recommended_options": coverage_analysis.get("recommendations", []),
            "excluded_options": coverage_analysis.get("exclusions", []),
            "literature_need_analysis": literature_need_analysis
        }

    def _analyze_literature_needs(
        self,
        clinical_question: str,
        guideline_recommendations: List[str],
        has_rejected_options: bool = False
    ) -> Dict[str, Any]:
        self,
        clinical_question: str,
        guidelines_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        【防幻觉】分析指南是否覆盖当前临床问题

        核心逻辑：
        1. 检查指南内容是否包含关键词
        2. 提取推荐方案和排除方案
        3. 如果未覆盖，明确记录原因（用于日志和降级触发）

        注意：这里使用简单的关键词匹配，实际生产环境应调用 LLM 进行语义分析
        """
        # 提取指南中的关键词
        question_lower = clinical_question.lower()

        # 关键词列表（基于常见临床问题）
        treatment_keywords = ["treatment", "治疗", "therapy", "方案", "推荐", "management"]
        brain_mets_keywords = ["brain metastases", "脑转移", "cns metastases", "中枢神经系统转移"]

        covered = False
        recommendations = []
        exclusions = []
        missing_reasons = []

        # 检查每个指南
        for result in guidelines_results:
            if "error" in result:
                continue

            content = result.get("content", "").lower()

            # 检查是否包含治疗相关内容
            has_treatment = any(kw in content for kw in treatment_keywords)
            has_brain_mets = any(kw in content for kw in brain_mets_keywords)

            if has_treatment and has_brain_mets:
                covered = True

                # 简单提取推荐方案（实际应使用 LLM）
                if "推荐" in content or "recommend" in content:
                    recommendations.append("基于指南的推荐方案")

                # 简单提取排除方案
                if "排除" in content or "contraindication" in content or "not recommended" in content:
                    exclusions.append("基于指南的排除方案")

        # 如果未覆盖，记录明确原因
        if not covered:
            missing_reasons.append(f"本地指南未包含 '{clinical_question}' 相关内容")
            missing_reasons.append("可能原因：肿瘤类型罕见、指南版本过旧、或问题过于特殊")

            # 打印明确警告（防幻觉）
            print(f"\n⚠️  【防幻觉警告】本地指南未覆盖临床问题")
            print(f"   问题：{clinical_question}")
            print(f"   原因：{missing_reasons[0]}")
            print(f"   行动：将降级调用 PubMed 补充证据")
            print(f"{'='*70}\n")

        return {
            "covered": covered,
            "recommendations": recommendations,
            "exclusions": exclusions,
            "missing_reasons": missing_reasons,
            "guidelines_checked": len(guidelines_results),
            "analysis_method": "keyword_matching"  # 实际应为 "llm_semantic_analysis"
        }

    # ========== Step 3: 判定是否允许降级调用 PubMed ==========

    def should_enrich_with_literature(
        self,
        guideline_result: Dict[str, Any],
        has_rejected_options: bool = False
    ) -> Tuple[bool, str]:
        """
        【降级触发】判定是否允许降级调用 PubMed

        证据优先级：降级证据（仅在特定条件下调用）

        允许降级的条件：
        1. 指南未覆盖当前临床问题（guideline_gap）
        2. 需要为被排除方案寻找反面证据（counter_evidence_for_rejected）

        Args:
            guideline_result: 指南查询结果
            has_rejected_options: 是否存在被排除的治疗方案

        Returns:
            (should_call: bool, reason: str)
        """
        coverage_analysis = guideline_result.get("coverage_analysis", {})
        covered = coverage_analysis.get("covered", False)

        # 条件 1：指南未覆盖
        if not covered:
            return (True, "guideline_gap")

        # 条件 2：需要为被排除方案寻找反面证据
        if has_rejected_options:
            return (True, "counter_evidence_for_rejected")

        # 指南已充分覆盖，禁止调用
        return (False, "guideline_sufficient")

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
        max_results: int = 3,  # 降低默认值，防止 Token 爆炸
        pubmed_call_limit: int = 2  # 单 Case 最多调用 2 次
    ) -> dict:
        """
        Step 3: 查询 PubMed 获取支持性文献证据。

        Args:
            keywords: 搜索关键词
            max_results: 最大结果数

        Returns:
            PubMed 查询结果
        """
        # 防无限循环：PubMed 调用硬上限
        pubmed_call_count = self.context.get("pubmed_call_count", 0)
        if pubmed_call_count >= pubmed_call_limit:
            print(f"⚠️  【防无限循环】已达到 PubMed 调用上限 ({pubmed_call_limit} 次)，跳过本次调用")
            return {
                "data": {
                    "articles": [],
                    "total_results": 0,
                    "message": f"已达调用上限 {pubmed_call_limit} 次"
                }
            }
        
        # 记录调用次数
        self.context.set("pubmed_call_count", pubmed_call_count + 1)
        print(f"   📚 PubMed 调用 {pubmed_call_count + 1}/{pubmed_call_limit}...")


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

    # ========== Step 5: 生成 MDT 报告 + Actor-Critic 纠错循环 ==========

    def generate_and_validate_report_with_retry(
        self,
        initial_report_content: str,
        max_retries: int = 3
    ) -> Tuple[dict, dict]:
        """
        【Actor-Critic 纠错循环】生成报告并验证，如失败则自动重试修订

        核心理念：
        - Actor（生成器）：生成初始报告
        - Critic（验证器）：验证报告合规性
        - 如果 Critic 报错，将错误反馈作为批评意见重新注入给 Actor 重写
        - 最多重试 max_retries 次，实现自我纠错

        防止无限循环：
        - 硬上限：max_retries = 3
        - 每次重试增加明确的批评反馈
        - 记录每次重试的错误，用于追踪和优化

        Args:
            initial_report_content: 初始报告内容（Markdown）
            max_retries: 最大重试次数

        Returns:
            (report_result: dict, validation_result: dict)
            - 报告生成结果
            - 最终验证结果（可能为失败）
        """
        report_content = initial_report_content
        validation_errors = []

        print(f"\n🔄 启动 Actor-Critic 纠错循环 (最大重试次数: {max_retries})")
        print(f"{'='*70}\n")

        for attempt in range(max_retries + 1):
            print(f"🔄 尝试 {attempt + 1}/{max_retries + 1}...")

            # Step 1: Actor - 生成报告
            try:
                if attempt == 0:
                    print(f"   🎭 Actor: 生成初始报告...")
                    report_result = self.generate_mdt_report(report_content, skip_validation=False)
                else:
                    # 将验证错误作为批评反馈注入
                    feedback = "\n".join([
                        f"- {error}" for error in validation_errors
                    ])
                    print(f"   🎭 Actor: 根据 Critic 反馈修订报告...")
                    print(f"   💬 Critic 反馈：\n{feedback}")
                    
                    # 在报告内容中注入批评反馈（实际应调用 LLM 重写）
                    # 这里简化为在开头添加反馈注释
                    report_content = f"# Critic 反馈修订 (尝试 {attempt})\n\n{feedback}\n\n{initial_report_content}"
                    report_result = self.generate_mdt_report(report_content, skip_validation=False)

                print(f"   ✅ 报告生成成功：{report_result.get('report_path', 'N/A')}")
            except Exception as e:
                print(f"   ❌ 报告生成失败：{e}")
                if attempt == max_retries:
                    raise
                continue

            # Step 2: Critic - 验证报告
            try:
                print(f"   🎯 Critic: 验证报告合规性...")
                validation_result = self.validate_report(report_result['report_path'])

                if validation_result['valid']:
                    print(f"   ✅ 验证通过！")
                    return report_result, validation_result
                else:
                    print(f"   ⚠️  验证未通过，收集批评反馈...")
                    validation_errors = validation_result.get('errors', [])
                    
                    print(f"   📋 错误列表：")
                    for error in validation_errors:
                        print(f"      - {error}")

                    if attempt < max_retries:
                        print(f"   🔁 准备重试修订...")
                        print(f"{'='*70}\n")
                    else:
                        print(f"   ❌ 已达到最大重试次数，仍验证失败")
                        return report_result, validation_result

            except Exception as e:
                print(f"   ❌ 验证过程异常：{e}")
                if attempt == max_retries:
                    raise

        # 理论上不会到这里
        raise RuntimeError("Actor-Critic 纠错循环异常终止")

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

        # 添加 PubMed 调用统计
        pubmed_call_count = self.context.get("pubmed_call_count", 0)
        evidence_sources.append({
            "source_type": "System",
            "source_id": "pubmed_call_count",
            "relevance": f"PubMed 调用次数: {pubmed_call_count}"
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

    parser = argparse.ArgumentParser(description="AI 肿瘤主治医师 v2.5 - Actor-Critic 自我纠错版")
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
