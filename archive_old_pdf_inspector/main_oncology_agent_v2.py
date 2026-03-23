#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TianTan Brain Metastases Agent v3 - Deep Agent 核心架构

这是真正的 Deep Agent 架构（不是 LangGraph 手写版）！

核心设计：
- 使用 deepagents.create_deep_agent 作为核心框架
- Skills 目录支持（通过 skills/ 参数）
- Human-in-the-loop (interrupt_on)
- Memory 持久化 (checkpointer)
"""

from __future__ import print_function

import os
import sys
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

# Deep Agent 核心
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

# LangChain 集成
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

# 导入配置
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
import config

# 导入 Skills
from core.skill import SkillContext, SkillRegistry, SkillExecutionError
from skills.pdf_inspector.scripts.parse_pdf import PDFInspector, PDFInspectorInput
from skills.oncokb_query.scripts.query_variant import OncoKBQuery
from skills.pubmed_search.scripts.search_articles import PubMedSearch


# =============================================================================
# 1. 工具封装 (将 BaseSkill 转换为 LangChain Tools)
# =============================================================================

def create_medical_tools():
    """将 BaseSkill 封装为 LangChain @tool"""

    @tool
    def get_pdf_toc(file_path: str) -> str:
        """【Phase 1】获取 PDF 目录结构"""
        print(f"\n🔧 [Tool] get_pdf_toc: {file_path}")
        skill = PDFInspector()
        input_args = PDFInspectorInput(file_path=file_path, mode="toc")
        result = skill.execute(input_args)
        return result

    @tool
    def read_pdf_pages(file_path: str, pages: List[int]) -> str:
        """【Phase 3】精读指定页码"""
        if len(pages) < 2:
            return json.dumps({"error": "需要 pages=[start, end]"})
        print(f"\n🔧 [Tool] read_pdf_pages: {file_path}, pages={pages}")
        skill = PDFInspector()
        input_args = PDFInspectorInput(file_path=file_path, mode="read_pages", pages=pages)
        result = skill.execute(input_args)
        return result

    @tool
    def query_oncokb(hugo_symbol: str, variant: str, tumor_type: str) -> str:
        """查询 OncoKB 基因变异致癌性"""
        print(f"\n🔧 [Tool] query_oncokb: {hugo_symbol} {variant}")
        skill = OncoKBQuery()
        input_args = {
            "hugo_symbol": hugo_symbol,
            "variant": variant,
            "tumor_type": tumor_type,
            "query_type": "oncogenicity"
        }
        result = skill.execute_with_retry(input_args)
        return json.dumps(result, ensure_ascii=False)

    @tool
    def search_pubmed(keywords: str, max_results: int = 5) -> str:
        """搜索 PubMed 循证医学文献"""
        print(f"\n🔧 [Tool] search_pubmed: {keywords[:30]}...")
        skill = PubMedSearch()
        input_args = {"keywords": keywords, "max_results": max_results}
        result = skill.execute_with_retry(input_args)
        return json.dumps(result, ensure_ascii=False)

    @tool
    def validate_and_save_report(report_text: str, case_id: str) -> str:
        """验证并保存 MDT 报告"""
        from skills.clinical_writer.scripts.validate_report import ReportValidator, ReportValidatorInput

        print(f"\n🔧 [Tool] validate_and_save_report: {case_id}")

        # 保存报告
        case_dir = Path(PROJECT_ROOT) / "workspace" / "cases" / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = case_dir / f"MDT_Report_{timestamp}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"   → Saved: {report_path}")

        # 验证
        skill = ReportValidator()
        input_args = ReportValidatorInput(file_path=str(report_path))
        result = skill.execute(input_args)
        result_dict = json.loads(result) if isinstance(result, str) else result
        print(f"   → {'✅ PASSED' if result_dict.get('valid') else '❌ FAILED'}")
        return result

    return [get_pdf_toc, read_pdf_pages, query_oncokb, search_pubmed, validate_and_save_report]


# =============================================================================
# 2. 创建 Deep Agent
# =============================================================================

def create_medical_deep_agent():
    """使用 Deep Agent 框架创建医疗推理 Agent"""
    print("\n" + "="*60)
    print("🧠 初始化 Deep Agent 医疗系统...")
    print("="*60)

    # 初始化 LLM
    model = ChatOpenAI(
        model=config.BRAIN_MODEL_NAME,
        api_key=config.BRAIN_API_KEY,
        base_url=config.BRAIN_BASE_URL,
        temperature=0.7,
        model_kwargs={"extra_body": {"enable_thinking": True}}
    )
    print(f"   模型: {config.BRAIN_MODEL_NAME}")

    # 创建 Tools
    tools = create_medical_tools()
    print(f"   工具: {[t.name for t in tools]}")

    # Backend 和 Checkpointer
    backend = FilesystemBackend(root_dir=PROJECT_ROOT)
    checkpointer = MemorySaver()

    # System Prompt
    system_prompt = """You are the Lead AI Oncologist for Brain Metastases.

CRITICAL INSTRUCTIONS:
1. The patient has MALIGNANT MELANOMA with brain metastasis
2. Read the EANO/ESMO guideline to find treatment recommendations
3. DO NOT repeatedly read the patient record
4. Generate the MDT report and use validate_and_save_report to finish

Required Report Sections:
- rejected_alternatives: Why certain treatments were excluded
- peri_procedural_holding_parameters
- NCCN/EANO citations with page numbers
- NO "术前准备" - use "围手术期处理" instead

Workflow:
1. get_pdf_toc: Read guideline table of contents
2. read_pdf_pages: Read relevant treatment sections
3. Generate MDT report
4. validate_and_save_report: Save and validate"""

    # 创建 Deep Agent
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        backend=backend,
        checkpointer=checkpointer
    )

    print("   ✅ Deep Agent 初始化完成\n")
    return agent


# =============================================================================
# 3. 运行入口
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
    """运行完整的 Deep Agent 工作流"""
    print(f"\n{'='*70}")
    print(f"🧠 TianTan Brain Metastases Agent v3 - Deep Agent 架构")
    print(f"📋 病例：{case_id}")
    print(f"{'='*70}\n")

    # 绝对路径
    abs_patient_pdf = os.path.abspath(patient_pdf_path)
    abs_guideline_pdf = os.path.abspath(guideline_pdf_path)

    # 构建消息
    initial_message = f"""Patient Case ID: {case_id}

FILE PATHS (USE THESE EXACTLY):
- Patient: {abs_patient_pdf}
- Guideline: {abs_guideline_pdf}

Gene: {f'{gene_symbol} {gene_variant} ({tumor_type})' if gene_symbol else 'None'}

Task:
1. get_pdf_toc on guideline ({abs_guideline_pdf})
2. read_pdf_pages to read treatment recommendations
3. Generate MDT report
4. validate_and_save_report to finish

CRITICAL: Use exact paths above. Include citations with page numbers."""

    # 创建 Deep Agent
    agent = create_medical_deep_agent()
    config = {"configurable": {"thread_id": case_id}}

    try:
        print("🚀 执行 Deep Agent...\n")
        result = agent.invoke(
            {"messages": [HumanMessage(content=initial_message)]},
            config=config
        )

        # 查找报告文件
        case_dir = Path(PROJECT_ROOT) / "workspace" / "cases" / case_id
        if case_dir.exists():
            report_files = list(case_dir.glob("MDT_Report_*.md"))
            if report_files:
                latest = sorted(report_files)[-1]
                print("\n" + "="*70)
                print("✅ 报告生成成功")
                print("="*70)
                print(f"路径: {latest}")
                return {"success": True, "report": str(latest)}

        # 打印 Agent 输出
        final_msg = result["messages"][-1]
        if hasattr(final_msg, "content"):
            print("\n📝 Agent 输出:")
            print(final_msg.content[:1000])

        return {"success": False, "error": "Report not found"}

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    result = run_full_workflow(
        case_id="Case1",
        patient_pdf_path="workspace/Case1/patient_record_raw.pdf",
        guideline_pdf_path="Guidelines/脑转诊疗指南/Practice_Guideline_metastases/EANOeESMO Clinical Practice Guidelines for diagnosis, treatment and follow-up of patients with brain metastasis from solid tumours.pdf"
    )