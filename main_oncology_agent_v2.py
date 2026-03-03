#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 肿瘤主治医师 v2.0 - 基于新 Skill 架构

与 v1 的区别：
- 直接使用 Python 调用 Skill 类，而非通过 execute_shell_command
- 显式管理 SkillContext，追踪跨技能状态
- 利用 Pydantic Schema 进行输入验证
- 自动重试和错误处理

适用场景：需要更精细控制 Skill 执行流程和状态管理的场景
"""

import os
import sys
import uuid
import json
from typing import Optional

# 引入 Skill 架构
from core.skill import SkillContext, SkillRegistry, SkillExecutionError
from skills.pdf_inspector.scripts.parse_pdf import PDFInspector, PDFInspectorInput
from skills.clinical_writer.scripts.generate_report import MDTReportGenerator, MDTReportInput
from skills.clinical_writer.scripts.validate_report import ReportValidator, ReportValidatorInput

# 引入 deepagents (保留原有框架)
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from utils.llm_factory import get_brain_client_langchain


# =============================================================================
# 1. 严格锁定工作区 (Sandbox Isolation)
# =============================================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CASES_DIR = os.path.join(PROJECT_ROOT, "workspace", "cases")
TEMP_DIR = os.path.join(PROJECT_ROOT, "workspace", "temp")
os.makedirs(CASES_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# =============================================================================
# 2. 注册 Skill
# =============================================================================

def create_skill_registry() -> SkillRegistry:
    """创建并注册所有可用的 Skill"""
    registry = SkillRegistry()

    # 注册 PDF Inspector
    registry.register(PDFInspector())

    # 注册 MDT Report Generator
    registry.register(MDTReportGenerator())

    # 注册 Report Validator
    registry.register(ReportValidator())

    return registry


# =============================================================================
# 3. 临床工作流编排器
# =============================================================================

class OncologyWorkflow:
    """
    肿瘤诊疗工作流编排器。

    负责：
    1. 初始化 SkillContext (每患者一会话)
    2. 按顺序调用各个 Skill
    3. 在 Context 中传递中间结果
    """

    def __init__(self, case_id: str, registry: SkillRegistry):
        self.case_id = case_id
        self.registry = registry
        # 每个患者一个独立的上下文
        self.context = SkillContext(session_id=case_id)

        # 设置元数据
        self.context.set_metadata("case_id", case_id)
        self.context.set_metadata("project_root", PROJECT_ROOT)

    def parse_patient_record(self, pdf_path: str, extract_images: bool = True) -> dict:
        """
        Step 1: 解析患者病历 PDF

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

        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        result = json.loads(result_json)

        # 存入 Context，供后续步骤使用
        self.context.set("patient_record_parsed", result)

        return result

    def query_guideline(self, guideline_path: str, topic: str) -> dict:
        """
        Step 2: 查询诊疗指南

        Args:
            guideline_path: 指南 PDF 路径
            topic: 查询主题 (如 "NSCLC second-line treatment")

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

        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        result = json.loads(result_json)

        # 存入 Context
        self.context.set(f"guideline_{topic}", result)

        return result

    def generate_mdt_report(self, report_content: str, skip_validation: bool = False) -> dict:
        """
        Step 3: 生成 MDT 报告

        Args:
            report_content: 报告内容 (Markdown)
            skip_validation: 是否跳过验证

        Returns:
            生成结果
        """
        skill = self.registry.get("generate_mdt_report")
        if not skill:
            raise RuntimeError("Skill 'generate_mdt_report' not found")

        input_args = MDTReportInput(
            case_id=self.case_id,
            report_content=report_content,
            skip_validation=skip_validation
        )

        result_json = skill.execute_with_retry(input_args.model_dump(), context=self.context)
        result = json.loads(result_json)

        # 存入 Context
        self.context.set("mdt_report_path", result.get("report_path"))

        return result

    def validate_report(self, report_path: str) -> dict:
        """
        Step 4: 验证报告合规性

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

    def get_context_summary(self) -> dict:
        """获取当前上下文摘要 (用于调试)"""
        return self.context.get_summary()

    def get_call_history(self) -> list:
        """获取所有 Skill 调用历史"""
        return self.context.get_history()


# =============================================================================
# 4. 主函数 - 完整诊疗流程示例
# =============================================================================

def run_full_workflow(case_id: str, patient_pdf_path: str, guideline_pdf_path: str):
    """
    运行完整的诊疗工作流。

    流程：
    1. 解析患者病历
    2. 查询诊疗指南
    3. 生成 MDT 报告
    4. 验证报告合规性

    Args:
        case_id: 患者病例 ID
        patient_pdf_path: 患者病历 PDF 路径
        guideline_pdf_path: 诊疗指南 PDF 路径
    """
    print(f"\n{'='*60}")
    print(f"🏥 开始肿瘤诊疗工作流 - 病例：{case_id}")
    print(f"{'='*60}\n")

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

    # Step 2: 查询诊疗指南
    print("\n📚 Step 2: 查询诊疗指南...")
    try:
        guideline = workflow.query_guideline(guideline_pdf_path, "nsclc_treatment")
        print(f"   ✅ 指南解析成功，共 {guideline['total_pages']} 页")
    except SkillExecutionError as e:
        print(f"   ❌ 指南查询失败：{e}")
        return

    # Step 3: 生成 MDT 报告 (这里需要 AI 生成实际内容)
    print("\n📝 Step 3: 生成 MDT 报告...")
    sample_report = """# MDT 多学科诊疗报告

## 患者信息
- 病例 ID: {case_id}
- 诊断：非小细胞肺癌 (NSCLC) 伴脑转移

## 治疗方案
根据 NCCN 指南推荐，对于 EGFR 突变阳性患者，一线治疗推荐奥希替尼 80mg QD。
[Citation: NCCN_NSCLC.pdf, Page 12]

## 放疗建议
建议行全脑放疗 (WBRT) 30Gy/10F，靶向病灶加量至 45Gy。
[Citation: ESMO_BrainMets.pdf, Page 8]

## 随访计划
每 2 个月复查头颅 MRI 和胸部 CT。
""".format(case_id=case_id)

    try:
        report_result = workflow.generate_mdt_report(sample_report)
        print(f"   ✅ 报告已生成：{report_result['report_path']}")
    except SkillExecutionError as e:
        print(f"   ❌ 报告生成失败：{e}")
        return

    # Step 4: 验证报告合规性
    print("\n✅ Step 4: 验证报告合规性...")
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

    # 输出上下文摘要
    print("\n" + "="*60)
    print("📊 工作流执行完成")
    print("="*60)
    print(f"Context 摘要：{json.dumps(workflow.get_context_summary(), indent=2, ensure_ascii=False)}")
    print(f"\nSkill 调用历史：共 {len(workflow.get_call_history())} 次调用")
    for record in workflow.get_call_history():
        status = "✅" if not record.error else "❌"
        print(f"  {status} {record.skill_name} ({record.duration_ms:.1f}ms, 重试{record.retry_count}次)")


# =============================================================================
# 5. 与 DeepAgent 集成 (可选)
# =============================================================================

def create_agent_with_skills():
    """
    创建集成新 Skill 架构的 Deep Agent。

    这个函数展示如何将 SkillRegistry 与 deepagents 框架集成。
    """
    # 唤醒大模型
    try:
        print("🧠 正在连接医疗大脑...")
        model = get_brain_client_langchain()
    except Exception as e:
        print(f"❌ 大脑初始化失败：{e}")
        sys.exit(1)

    # 创建 SkillRegistry
    registry = create_skill_registry()

    # 构建 System Prompt，包含 Skill 列表
    system_prompt = f"""
You are the **Lead AI Oncologist** handling Solid Tumors with Brain Metastases.
Your Sandbox is strictly: `{PROJECT_ROOT}`

**🛠️ YOUR SKILLS (可直接调用的工具):**
"""
    for tool_def in registry.get_all_tool_definitions():
        system_prompt += f"\n- `{tool_def['name']}`: {tool_def['description']}"

    system_prompt += f"""

**⚡ CLINICAL WORKFLOW:**
1. 接收患者症状或病史描述
2. 使用 `parse_medical_pdf` 解析患者病历 PDF 或诊疗指南
3. 综合信息后生成治疗建议
4. **最后必须使用** `generate_mdt_report` 生成正式报告

**🔒 SAFETY PROTOCOL:**
- 药物剂量必须基于指南原文，不得猜测
- 每项治疗建议后必须添加引用：[Citation: 文件名，Page 页码]
"""

    # 组装 Agent
    backend = FilesystemBackend(root_dir=PROJECT_ROOT)
    checkpointer = MemorySaver()

    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[],  # Skill 将通过工具定义动态添加
        memory=["MEDICAL_PROTOCOL.md"],
        backend=backend,
        checkpointer=checkpointer,
    )

    return agent, registry


# =============================================================================
# 6. CLI 入口
# =============================================================================

if __name__ == "__main__":
    # 示例：运行完整工作流
    # 用法：python main_oncology_agent_v2.py [--demo]

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # 演示模式 - 需要实际的 PDF 文件
        print("🎯 演示模式 - 请确保以下测试文件存在:")
        print("   - workspace/test_data/patient_record.pdf")
        print("   - workspace/test_data/NCCN_NSCLC.pdf")

        # 这里可以添加演示数据检查逻辑
        print("\n⚠️  演示数据不存在，跳过执行。")
        print("💡 提示：修改下方的 case_id、patient_pdf_path、guideline_pdf_path 后直接运行")

    else:
        # 默认：运行完整工作流示例
        # TODO: 根据实际情况修改以下参数
        case_id = "Case1"
        patient_pdf_path = "workspace/test_data/patient_record.pdf"
        guideline_pdf_path = "workspace/test_data/NCCN_NSCLC.pdf"

        # 检查文件是否存在
        if not os.path.exists(patient_pdf_path):
            print(f"❌ 患者病历文件不存在：{patient_pdf_path}")
            print("💡 请修改 main_oncology_agent_v2.py 中的路径配置")
        elif not os.path.exists(guideline_pdf_path):
            print(f"❌ 诊疗指南文件不存在：{guideline_pdf_path}")
            print("💡 请修改 main_oncology_agent_v2.py 中的路径配置")
        else:
            run_full_workflow(case_id, patient_pdf_path, guideline_pdf_path)
