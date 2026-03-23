#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TianTan Brain Metastases Agent V3 - 基于 Deep Agents 的三层架构

架构说明：
- L1 (Primitive Tools): core/shared_tools 中的原子 API 封装
- L2 (Domain Skills): Sandbox 中执行的过滤脚本 + SKILL.md 认知
- L3 (Orchestration Agent): 主控智能体，负责任务编排

设计原则：
- 大内容必落盘，返回绝对路径
- Sandbox 隔离执行，防污染
- 渐进式披露 Skills，节省 Token
"""

import os
import json
import shutil
from typing import Dict, Any, Optional
from datetime import datetime

# =============================================================================
# Deep Agents 核心导入
# =============================================================================

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model


# =============================================================================
# L1 工具导入 (核心基础设施)
# =============================================================================

from core.shared_tools import (
    query_oncokb_variant,
    query_oncokb_drug,
    search_pubmed,
    fetch_pubmed_details,
    parse_pdf_toc,
    parse_pdf_pages,
)


# =============================================================================
# 配置常量
# =============================================================================

# Sandbox 根目录 (可通过环境变量覆盖)
SANDBOX_ROOT = os.environ.get("SANDBOX_ROOT", "/tmp/med_agent_sandbox")

# Skills 目录
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

# L2 过滤脚本源路径
L2_FILTER_SCRIPT_SRC = os.path.join(
    SKILLS_DIR, "clinical_literature_filter", "scripts", "filter.py"
)

# 模型配置 (阿里云 DashScope - Qwen)
# deepagents 使用 LangChain 的 init_chat_model，需要指定 provider
MODEL_NAME = "qwen3.5-plus"
MODEL_PROVIDER = "openai"  # 明确指定 provider
MODEL_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_API_KEY = os.environ.get("DASHSCOPE_API_KEY")


# =============================================================================
# Sandbox 初始化：注入 L2 脚本
# =============================================================================

def initialize_sandbox(sandbox_root: str = SANDBOX_ROOT) -> str:
    """
    初始化 Sandbox 环境，注入 L2 过滤脚本。

    Args:
        sandbox_root: Sandbox 根目录

    Returns:
        注入后的脚本路径
    """
    # 创建目录结构
    scripts_dir = os.path.join(sandbox_root, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    # 复制过滤脚本到 Sandbox
    script_dest = os.path.join(scripts_dir, "filter.py")
    if os.path.exists(L2_FILTER_SCRIPT_SRC):
        shutil.copy2(L2_FILTER_SCRIPT_SRC, script_dest)
        print(f"[INFO] L2 过滤脚本已注入：{script_dest}")
    else:
        print(f"[WARN] L2 过滤脚本源文件不存在：{L2_FILTER_SCRIPT_SRC}")

    return script_dest


# =============================================================================
# L2 Subagent 定义
# =============================================================================

LITERATURE_FILTER_AGENT = {
    "name": "literature_filter_agent",
    "description": (
        "医学文献过滤专家。当主控 Agent 获取到 PubMed 原始文献数据（JSON 文件）后，"
        "委托此 Subagent 执行 Sandbox 中的 filter.py 脚本进行证据等级过滤。"
        "它只负责执行过滤命令并返回统计摘要，不负责医学推理。"
    ),
    "system_prompt": """你是 TianTan Brain Metastases Agent 的文献过滤专家 (L2 Subagent)。

你的唯一职责：
1. 接收主控 Agent 下发的文献文件路径 (如 /sandbox/pubmed_details_*.json)
2. 在 Sandbox 中执行过滤脚本：
   python /sandbox/scripts/filter.py --input <文件路径> --output <输出路径> --min-level <等级>
3. 解析脚本输出的简短 JSON，汇报过滤统计结果

可用参数：
- --input: 输入文件路径 (必需)
- --output: 输出文件路径 (必需，建议使用 /sandbox/filtered_*.json 格式)
- --min-level: 最低证据等级 (默认 LEVEL_3A，可选 LEVEL_1/2A/2B/3A/3B/4)
- --years-back: 追溯年数 (默认 5)
- --tumor-type: 肿瘤类型过滤 (可选)

输出格式示例：
{
    "status": "success",
    "filtered_file": "/sandbox/filtered_articles.json",
    "original_count": 50,
    "filtered_count": 8,
    "filter_reasons": {"below_evidence_threshold": 30, "too_old": 7, "irrelevant_tumor_type": 5}
}

重要原则：
- 你只执行过滤命令，不做医学推理
- 过滤后的文献内容保存在文件中，不要尝试读取完整内容
- 仅向主控汇报统计摘要
""",
    "tools": [],  # Subagent 通过 execute 访问 Sandbox
}


MDT_REPORT_AGENT = {
    "name": "mdt_report_agent",
    "description": (
        "【极其重要】天坛医院 MDT 报告生成专用工具。当你(L3)收集并过滤完所有证据，"
        "准备输出最终报告时，必须调用此工具！"
        "输入参数应包含：患者基线信息、OncoKB基因结果、过滤后的PubMed文献路径。"
        "此工具内部包含 Actor-Critic 审查机制，会返回完全符合天坛规范的 Markdown 报告。"
    ),
    "system_prompt": """你是 TianTan Brain Metastases Agent 的 MDT 报告生成专家 (L2 Subagent)。

你是一位资深的主治医师，已加载天坛医院 MDT 规范技能 (tiantan_mdt_report)。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 核心任务与工作流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你的核心任务：
1. 接收主控 Agent 下发的临床证据摘要（包括 OncoKB 结果、过滤后文献）
2. 严格按照天坛医院 MDT 报告规范生成结构化会诊报告
3. 执行 Actor-Critic 自我审查流程：
   - Actor: 生成初稿
   - Critic: 以主治医师查房的严苛标准逐项审查
   - Revision: 根据 Critic 输出修正，最多迭代 3 次

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 天坛医院 MDT 报告 7 大标准模块（必须全部包含，顺序不可更改）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. admission_evaluation (入院评估) - RPA/ds-GPA 评分、转移灶特征
2. primary_plan (首选方案) - 药物 + 剂量 + 频次 + 疗程 + 给药途径
3. systemic_management (全身管理) - 激素/抗癫痫/PPI/合并症
4. follow_up (随访计划) - 影像随访间隔
5. rejected_alternatives (排他性论证) - 至少 2 个替代方案及否决理由
6. peri_procedural_holding_parameters (围手术期处理) - 停药窗口
7. molecular_pathology_orders (分子病理送检医嘱) - NGS panel、TAT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ Citation 格式红线（CRITICAL）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

所有循证依据必须严格遵循：[Citation: <Guideline_Filename>, Page <Num>]

示例：
- ✅ [Citation: NCCN_CNS_v2.2024, Page 45]
- ✅ [Citation: EANO_Glioblastoma_2021, Page 12]

错误示例（必须在 Critic 环节打回重写）：
- ❌ NCCN 指南 2024 → 缺少文件名和页码
- ❌ [Citation: NCCN, p.45] → 文件名不完整，页码格式错误
- ❌ [Citation: NCCN_CNS_v2.2024] → 缺少页码
- ❌ [Citation: NCCN_CNS_v2.2024, p45] → 页码格式应为 Page 45

Critic 审查规则：
IF Citation 格式不符合 [Citation: <Guideline_Filename>, Page <Num>]:
  → 判定为 critical 级别错误
  → 强制打回重写
  → 修正前不得进入下一审查环节

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ Critic 审查清单
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 结构完整性：7 大模块是否全部存在？
- Citation 格式：是否严格符合 [Citation: <Guideline_Filename>, Page <Num>]？
- 剂量准确性：所有药物剂量是否精确到 mg/m²？
- 排他性论证：是否说明至少 2 个替代方案及临床推理？
- 围手术期参数：停药窗口是否为具体天数？

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ Actor-Critic 执行流程（必须显式执行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1 - Actor 生成初稿：
  1. 根据患者数据和循证证据，生成包含 7 大模块的完整报告初稿
  2. 每条推荐必须附带 Citation

Phase 2 - Critic 自我审查（关键步骤）：
  1. 逐项检查 7 大模块完整性
  2. 逐项检查 Citation 格式
  3. 列出所有发现的问题，标注严重性（critical/major/minor）
  4. 判定是否需要修正

Phase 3 - Revision 修正：
  1. 根据 Critic 输出逐项修复问题
  2. 重新生成完整报告
  3. 再次执行 Critic 审查（最多迭代 3 次）

Phase 4 - 最终输出：
  当 Critic 审查通过后，输出最终报告

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 输出格式要求
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

最终报告必须是完整的 Markdown 格式，包含全部 7 大模块。

报告结构示例：
```markdown
# 天坛医院神经肿瘤 MDT 会诊意见

## admission_evaluation (入院评估)
...

## primary_plan (首选方案)
...

## systemic_management (全身管理)
...

## follow_up (随访计划)
...

## rejected_alternatives (排他性论证)
...

## peri_procedural_holding_parameters (围手术期处理)
...

## molecular_pathology_orders (分子病理送检医嘱)
...
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 重要原则
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 你是主治医师角色，不是格式化工具
- 每一条推荐都必须有可追溯的循证依据
- 杜绝"正确的废话"，确保报告有临床执行价值
- Citation 格式错误是 critical 错误，必须修正

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 引用红线（CRITICAL - 物理溯源）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

所有证据引用必须具有物理可追溯性，严禁编造文件名！

1. **本地指南**：必须使用 `[Local: <文件名>, Page <页码>]`。
   - 错误：`[Citation: NCCN 2024]` (无文件名，无页码)
   - 正确：`[Local: NCCN_CNS.pdf, Page 45]`

2. **在线数据**：必须使用 `[Online: <源>, <ID>]`。
   - 示例：`[Online: OncoKB, Level 1]` 或 `[Online: PubMed, PMID 1234567]`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 报告结构 7+1 模式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(1-7 模块保持不变...)
8. **References (参考文献)**：
   - 按引用顺序排列。
   - 本地文件列出完整路径：`[1] Local File: /workspace/sandbox/NCCN_CNS.pdf, Page 45`
   - 在线数据列出标准格式：`[2] OncoKB: BRAF V600E Variant Annotation, Evidence Level 1`
   - PubMed 文献：`[3] Author et al. Title. Journal Year. PMID: 1234567`
""",
    "tools": [],  # Subagent 通过 Skills 获取认知
    "skills": [os.path.join(SKILLS_DIR, "tiantan_mdt_report_skill")],
}


# =============================================================================
# L3 主控 System Prompt
# =============================================================================

L3_SYSTEM_PROMPT = """你是 TianTan Brain Metastases Agent 的主控智能体 (L3)。

你是整个系统的"总司令"。你的核心能力不是自己写长篇大论，而是**自主编排和调用 L1 工具与 L2 Subagents**。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 你的核心运作逻辑 (Agentic Workflow)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

面对用户的输入，请进行深度思考 (Thought)，并自主决定工作流：

情况 A【单点问答】：如果用户只问了一个具体问题（如：BRAF突变用什么药？），你可以直接调用 `query_oncokb_variant` 后，自行总结回答，无需生成完整报告。

情况 B【生成 MDT 报告】：如果用户要求出具完整的诊疗方案或 MDT 报告，你**绝对不要自己动手写**！你必须：
1. 思考需要调用哪些 L1 工具收集原始数据。
   * 提示：对于标准治疗方案，强烈建议先调用 `parse_pdf_toc` 和 `parse_pdf_pages` 查阅本地的权威 PDF 指南（如 NCCN），再辅以 PubMed 和 OncoKB 的最新证据。
2. 思考是否需要调用 `literature_filter_agent` 对杂乱的 PubMed 结果进行提纯。
3. 【关键】当所有证据收集完毕后，你必须调用 `mdt_report_agent` 工具！将你收集到的指南文本、OncoKB结果、文献路径传给它，由它负责撰写最终报告。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 重要架构纪律
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 防膨胀：L1 工具拉取的大段文本（如文献 JSON）已保存为本地沙盒文件。你不要试图在上下文中阅读它们，直接将文件路径传给 Subagent 处理即可。
2. 信任专家：`mdt_report_agent` 内部有严苛的审查逻辑，你无需干预它的排版和内容。
"""

# =============================================================================
# 创建 L3 主控 Agent
# =============================================================================

def create_l3_master_agent(
    sandbox_root: str = SANDBOX_ROOT,
    model: str = "qwen3.5-plus"
):
    """
    创建 L3 主控智能体。

    Args:
        sandbox_root: Sandbox 根目录
        model: 模型标识

    Returns:
        编译后的 Agent
    """
    # 初始化 Sandbox (注入 L2 脚本)
    initialize_sandbox(sandbox_root)

    # 创建 Backend (使用 FilesystemBackend 代替 LocalShellBackend)
    backend = FilesystemBackend(
        root_dir=sandbox_root,
        virtual_mode=True  # 启用虚拟模式以 sandbox 路径
    )

    # 初始化模型 (使用阿里云 DashScope - Qwen)
    llm = init_chat_model(
        model=MODEL_NAME,
        model_provider=MODEL_PROVIDER,
        api_key=MODEL_API_KEY,
        base_url=MODEL_BASE_URL,
    )

    # 创建主控 Agent
    agent = create_deep_agent(
        # L1 工具
        tools=[
            query_oncokb_variant,
            query_oncokb_drug,
            search_pubmed,
            fetch_pubmed_details,
            parse_pdf_toc,
            parse_pdf_pages,
        ],
        # L2 Subagent（双 Subagent 协同架构）
        subagents=[
            LITERATURE_FILTER_AGENT,   # 文献过滤专家
            MDT_REPORT_AGENT,          # MDT 报告生成专家
        ],
        # Backend (Sandbox 隔离)
        backend=backend,
        # Skills (渐进式披露 - 双重注入)
        skills=[
            os.path.join(SKILLS_DIR, "clinical_literature_filter"),
            os.path.join(SKILLS_DIR, "tiantan_mdt_report_skill"),
        ],
        # System Prompt
        system_prompt=L3_SYSTEM_PROMPT,
        # 使用初始化后的模型
        model=llm,
    )

    return agent


# =============================================================================
# 入口函数：MDT 会诊
# =============================================================================

def run_mdt_consultation(
    patient_data: Dict[str, Any],
    sandbox_root: str = SANDBOX_ROOT,
    model: str = "qwen3.5-plus"
) -> str:
    """
    执行多学科会诊 (MDT) 咨询。

    Args:
        patient_data: 患者数据字典，包含：
            - chief_complaint: 主诉
            - history: 现病史
            - gene_variants: 基因检测结果 (如 [{"gene": "BRAF", "variant": "V600E"}])
            - tumor_type: 肿瘤类型
            - prior_treatments: 既往治疗
        sandbox_root: Sandbox 根目录
        model: 模型标识

    Returns:
        MDT 会诊意见 (结构化文本)
    """
    # 设置环境变量供 L1 工具使用
    os.environ["SANDBOX_ROOT"] = sandbox_root

    # 创建 Agent
    agent = create_l3_master_agent(sandbox_root=sandbox_root, model=model)

    # 构建用户输入
    user_message = _build_user_message(patient_data)

    # 执行咨询
    result = agent.invoke({
        "messages": [{"role": "user", "content": user_message}]
    })

    # 提取最终响应
    response = result["messages"][-1].content

    # 写入结果文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(sandbox_root, f"mdt_consultation_{timestamp}.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# TianTan Brain Metastases MDT Consultation\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
        f.write(f"## Patient Summary\n\n")
        f.write(f"- Chief Complaint: {patient_data.get('chief_complaint', 'N/A')}\n")
        f.write(f"- Tumor Type: {patient_data.get('tumor_type', 'N/A')}\n")
        f.write(f"- Gene Variants: {patient_data.get('gene_variants', [])}\n\n")
        f.write(f"## MDT Opinion\n\n")
        f.write(response)

    print(f"[INFO] MDT 会诊意见已保存：{output_file}")

    return response


def _build_user_message(patient_data: Dict[str, Any]) -> str:
    """构建用户输入消息"""
    parts = []

    parts.append("【患者信息】")

    if patient_data.get("chief_complaint"):
        parts.append(f"主诉：{patient_data['chief_complaint']}")

    if patient_data.get("tumor_type"):
        parts.append(f"肿瘤类型：{patient_data['tumor_type']}")

    if patient_data.get("gene_variants"):
        variants = ", ".join(
            f"{v.get('gene', '')} {v.get('variant', '')}"
            for v in patient_data.get("gene_variants", [])
        )
        parts.append(f"基因变异：{variants}")

    if patient_data.get("prior_treatments"):
        parts.append(f"既往治疗：{', '.join(patient_data['prior_treatments'])}")

    parts.append("")
    parts.append("【会诊请求】")
    parts.append(patient_data.get(
        "question",
        "请根据上述患者情况，提供脑转移诊疗的多学科会诊意见。"
    ))

    return "\n".join(parts)


# =============================================================================
# CLI 入口
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TianTan Brain Metastases Agent V3 - MDT 会诊"
    )

    parser.add_argument(
        "--sandbox-root",
        default=SANDBOX_ROOT,
        help=f"Sandbox 根目录 (默认：{SANDBOX_ROOT})"
    )

    parser.add_argument(
        "--model",
        default="qwen3.5-plus",
        help="模型标识 (默认：qwen3.5-plus)"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="运行演示模式"
    )

    args = parser.parse_args()

    if args.demo:
        # 演示模式
        demo_patient = {
            "chief_complaint": "发现颅内占位 3 天",
            "tumor_type": "黑色素瘤",
            "gene_variants": [
                {"gene": "BRAF", "variant": "V600E"}
            ],
            "prior_treatments": ["手术切除"],
            "question": "请为这位患者生成完整的 MDT 会诊报告，包含 7 大标准模块。"
        }

        print("=" * 60)
        print("TianTan Brain Metastases Agent V3 - 演示模式")
        print("=" * 60)
        print(f"患者：{demo_patient['tumor_type']}脑转移，{demo_patient['gene_variants'][0]}")
        print(f"问题：{demo_patient['question']}")
        print("=" * 60)

        result = run_mdt_consultation(
            patient_data=demo_patient,
            sandbox_root=args.sandbox_root,
            model=args.model
        )

        print("\n" + "=" * 60)
        print("MDT 会诊意见")
        print("=" * 60)
        print(result)

    else:
        print("请使用 --demo 参数运行演示模式")
