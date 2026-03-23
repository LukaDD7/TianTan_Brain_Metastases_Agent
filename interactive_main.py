#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TianTan Brain Metastases Agent - Interactive Main Entry (v5.0 Deep Agents 重构版)

架构核心变更：
1. 单一 Agent 扁平化架构，NO Subagents
2. 仅挂载 pdf-inspector Skill 进行测试
3. CompositeBackend：FilesystemBackend(默认) + StoreBackend(/memories/ 持久化)
4. Execute 工具：通过自定义 tool 提供 shell 执行能力
5. Human-in-the-loop 支持：write_file/edit_file/execute 需要审批
6. 大内容落盘 Sandbox，不污染上下文
"""

import os
import sys
import uuid

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool

from utils.llm_factory import get_brain_client_langchain


# =============================================================================
# 配置常量
# =============================================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
SANDBOX_DIR = os.path.join(PROJECT_ROOT, "workspace", "sandbox")

os.makedirs(SANDBOX_DIR, exist_ok=True)
os.environ["SANDBOX_ROOT"] = SANDBOX_DIR

# =============================================================================
# 唤醒大模型
# =============================================================================

try:
    print("🧠 正在连接天坛医疗大脑 (深度思考模式)...")
    model = get_brain_client_langchain()
except Exception as e:
    print(f"❌ 大脑初始化失败: {e}")
    sys.exit(1)


# =============================================================================
# L3 主控 System Prompt (扁平化架构 - 直接使用 Skills)
# =============================================================================

L3_SYSTEM_PROMPT = """你是一名脑转移瘤 MDT 首席智能体，是一位极其严谨、遵循证据主权的神经肿瘤专家。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 最高行医准则 (PRIME DIRECTIVES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 证据主权：严禁编造任何基因突变、检验值或病史。无数据即标记为 "unknown"。
2. 自主寻路 (Harness Self-Discovery)：你拥有一个“智能体线束 (Agent Harness)”，挂载了多个专业技能。你并没有被预设这些技能的具体操作指令。
   - 当你面对任务（如读 PDF、查突变、搜文献）时，你必须扫描当前挂载的 Skill 列表及其描述。
   - 你【必须】先使用 read_file 工具完整阅读对应技能的 SKILL.md 文件。
   - 学习其内部的思维链（SOP）、命令行参数格式和临床解读规则，然后利用 execute 工具执行。
3. 物理溯源引用：每一条临床建议必须附带可追溯的引用。
   - 文本证据：[Local: <文件名>, Section: <章节标题>] 或 [Local: <文件名>, Line <行号>]
   - 图片证据：[Local: <文件名>, Visual: Page<页码>] (仅用于Visual Probe)
   - 数据库：[OncoKB: Level X]
   - 文献：[PubMed: PMID <编号>]
4. 严禁编造任何基因突变、物理页码、或临床证据。
5. 禁止依赖预训练权重：关于 NCCN/ASCO 指南、OncoKB 证据及 PubMed 最新文献的所有内容，必须通过 execute 工具真实获取。禁止在没有物理读取记录的情况下进行“脑补”。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 任务执行与输出
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 阅读MDT Report Skill然后形成规划，根据患者实际情况调用工具收集诊疗报告的信息。
- 临床指南具有最高优先级，任何未明确决策应首先从指南中获取具体建议，若仍然信息不足，则可通过其他工具获取需要的信息。
- **可执行粒度与深钻机制 (Deep Drill Protocol)**：
  - 报告必须达到绝对可执行状态（必须包含：具体手术方案/辅助技术、放疗剂量 Gy/分割次数、系统药物剂量 mg/频次、停药天数等）。
  - **严禁使用预训练权重脑补任何具体参数**。如果初步 grep 检索未发现剂量或技术细节，你必须强制执行以下“深钻”策略：
    1. **专门检索指南附录 (Principles)**：剂量和手术细节通常位于指南后半部分。强制执行 `grep -i "Principles of Radiation"`, `grep -i "Principles of Surgery"`等替换查询，或直接搜索 `Gy\|dose\|fraction\|mg`。
    2. **触发视觉探针 (Visual Probe)**：如果你发现剂量或处方信息位于复杂的 Markdown 表格中且排版混乱，必须立即使用 pdf-inspector 的 render_pdf_page 工具截图该页，进行视觉读取。
    3. **追溯奠基性试验 (Landmark Trials)**：如果指南正文确实缺失具体参数，你必须立即调用 PubMed，检索确立该治疗标准的核心临床试验（Phase III/II）。例如，通过 `{{Treatment}} AND Brain Metastases AND Clinical Trial` 寻找原文献中的 Protocol 剂量设定。
- 对话框仅用于同步你的 Thought 过程、执行日志和向医生反馈关键发现。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 物理溯源引用协议 (STRICT CITATION)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
所有临床建议必须附带可追溯的物理锚点，严禁虚构坐标：
- 文本证据：必须引用 [Local: <文件名>, Section: <章节标题>] 或 [Local: <文件名>, Line <行号>]。严禁在纯文本中使用 Page X。
- 图片证据：仅当你使用 Visual Probe 渲染出图片时，方可使用 [Local: <文件名>, Visual: Page <页码>]。
- 分子证据：[OncoKB: Level X]。
- 文献证据：[PubMed: PMID <编号>]。
- 强制审计：模块 8 (agent_execution_trajectory) 必须如实记录你执行过的所有 bash 指令。如果模块 2/3 出现了引用，但模块 8 没有对应的 cat/grep 指令记录，将被视为”学术造假”。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 长期记忆协议 (LONG-TERM MEMORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
你可以访问持久化存储路径 `/memories/`（跨会话保留）：

1. **患者画像 (Patient Persona)**：`/memories/personas/<Patient_ID>.md`
   - 在生成报告后，提取患者关键信息（ demographics, 原发肿瘤, 分子特征, 既往治疗史, 当前状态）
   - 写入患者画像文件，用于后续快速了解患者背景
   - 结构：
     ```markdown
     # Patient Persona: <Patient_ID>
     ## Demographics
     - Age: xx, Gender: x
     ## Primary Cancer
     - Type: xxx, Stage: xxx
     ## Molecular Profile
     - Mutations: xxx
     ## Treatment History
     - Previous: xxx
     ## Current Status
     - Lesions: xxx
     ## Last Updated: <timestamp>
     ```

2. **临床原则 (Clinical Principles)**：`/memories/principles/<topic>.md`
   - 积累特定癌种/场景的诊疗模式和医生反馈
   - 记录从会诊中学到的”最佳实践”
   - 主题示例：`nsclc_bm_management.md`, `srs_dosing_principles.md`
   - 当医生给出反馈（如”以后此类情况应...”），更新对应原则文件

3. **使用方式**：
   - 遇到已知患者：先读取 `/memories/personas/<Patient_ID>.md` 了解背景
   - 遇到新患者：生成报告后，更新患者画像
   - 积累知识：将医生反馈和诊疗经验写入 Principles

"""


# =============================================================================
# 自定义工具：execute (shell 命令执行)
# =============================================================================

@tool
def execute(command: str, timeout: int = 600, max_output_bytes: int = 100000) -> str:
    """Execute a shell command and return the output.

    Args:
        command: The shell command to execute
        timeout: Maximum execution time in seconds (default: 120)
        max_output_bytes: Maximum output size in bytes (default: 100000)

    Returns:
        Command output (stdout + stderr) or error message
    """
    import subprocess
    import os

    # 白名单机制：只允许执行安全的命令模式
    ALLOWED_PREFIXES = (
        "/home/luzhenyang/anaconda3/envs/mineru_env/bin/python",
        "/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python",
        "ls ",
        "cat ",
        "head ",
        "tail ",
        "grep ",
        "find .",
        "echo ",
        "mkdir "
    )

    # 危险命令黑名单
    DANGEROUS_PATTERNS = (
        "rm -rf", "rm -rf /", "dd if=", "mkfs.", ":(){ :|:& };:", "> /dev/sda",
        "curl", "wget", "ssh", "nc ", "ncat ", "python -c 'import socket'",
    )

    # 检查白名单
    is_allowed = any(command.strip().startswith(prefix) for prefix in ALLOWED_PREFIXES)

    # 检查黑名单
    is_dangerous = any(pattern in command.lower() for pattern in DANGEROUS_PATTERNS)

    if is_dangerous:
        return f"Error: Command blocked by security policy (dangerous pattern detected): {command[:100]}"

    if not is_allowed:
        return f"Error: Command not in whitelist. Allowed prefixes: {ALLOWED_PREFIXES}. Your command: {command[:100]}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=SANDBOX_DIR,
            env={**os.environ, "SANDBOX_ROOT": SANDBOX_DIR}
        )

        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr

        # Truncate if too large
        if len(output.encode('utf-8')) > max_output_bytes:
            output = output[:max_output_bytes] + "\n... [output truncated]"

        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "current_working_dir": SANDBOX_DIR,
            "msg": "If exit_code != 0, please re-read the SKILL.md to check your parameters."
        }

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


# =============================================================================
# Backend 工厂：CompositeBackend 混合存储
# =============================================================================

def make_backend(runtime):
    """
    创建 CompositeBackend：
    - 默认路径 → FilesystemBackend (sandbox 隔离)
    - /skills/* → FilesystemBackend (技能目录，只读)
    - /memories/* → StoreBackend (跨会话持久化存储)
    """
    return CompositeBackend(
        default=FilesystemBackend(
            root_dir=SANDBOX_DIR,
            virtual_mode=True,  # 启用路径限制，防止访问 sandbox 之外的文件
        ),
        routes={
            "/skills/": FilesystemBackend(
                root_dir=SKILLS_DIR,
                virtual_mode=True,
            ),
            "/memories/": StoreBackend(runtime)  # Persistent: 跨会话缓存
        }
    )


# =============================================================================
# 组装 Deep Agent
# =============================================================================

print(f"🚀 正在初始化天坛医疗大脑 v5.0 (Deep Agents 架构)...")
print(f"   - Sandbox 隔离目录：{SANDBOX_DIR}")
print(f"   - 持久化记忆路径：/memories/")
print(f"   - Skills：挂载 pdf-inspector + universal_bm_mdt_skill")
print(f"   - Subagents：无 (扁平化架构)")
print(f"   - Execute 工具：自定义 shell 执行")

# 用于跨会话持久化存储 (StoreBackend 需要)
store = InMemoryStore()

# 用于状态持久化 (Human-in-the-loop 需要)
checkpointer = MemorySaver()

# Human-in-the-loop 配置：敏感操作需要审批
interrupt_config = {
    "write_file": False,     # sandbox 内自动写入
    "edit_file": False,      # sandbox 内自动编辑
    "execute": False,        # execute 已添加白名单，自动执行
    "read_file": False,      # 读取无需审批
}

agent = create_deep_agent(
    model=model,
    system_prompt=L3_SYSTEM_PROMPT,
    tools=[
        execute,  # 执行 Skill 脚本的核心工具
    ],
    subagents=[],  # 无 Subagents，扁平化架构
    skills=[
        "/skills/pdf-inspector",
        "/skills/universal_bm_mdt_skill",
        "/skills/oncokb_query_skill",  # OncoKB 基因突变查询
        "/skills/pubmed_search_skill",  # PubMed 文献检索
    ],  # 使用虚拟路径，对应 CompositeBackend 路由
    backend=make_backend,
    store=store,  # StoreBackend 需要
    checkpointer=checkpointer,  # Human-in-the-loop 必须
    interrupt_on=interrupt_config,
)

# =============================================================================
# 主循环
# =============================================================================

if __name__ == "__main__":
    patient_thread_id = str(uuid.uuid4())
    print(f"\n✅ 天坛医疗大脑 v5.0 已就绪。Session ID: {patient_thread_id}")
    print("💡 提示：您可以输入患者病史，并要求查阅指南生成 MDT 方案。")
    print("💡 示例：\"请分析 /workspace/sandbox/NCCN_CNS.pdf，提取脑转移瘤治疗流程图\"")
    print("-" * 60)

    while True:
        try:
            print("\n🧑‍⚕️ 请输入患者信息（输入空行或 `---` 结束，输入 exit 退出）：")
            lines = []
            empty_line_count = 0
            while True:
                try:
                    # 使用 sys.stdin.buffer 读取原始字节，避免编码问题
                    line_bytes = sys.stdin.buffer.readline()
                    if not line_bytes:
                        break
                    # 尝试 UTF-8 解码，失败则使用替代字符
                    try:
                        line = line_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        line = line_bytes.decode('utf-8', errors='replace')

                    # 单行退出命令
                    if line.strip().lower() in ["exit", "quit"] and len(lines) == 0:
                        print("👋 再见！")
                        sys.exit(0)

                    # 结束标记：空行或 ---
                    if line.strip() == "" or line.strip() == "---":
                        empty_line_count += 1
                        if empty_line_count >= 1 or line.strip() == "---":
                            break
                    else:
                        empty_line_count = 0

                    lines.append(line)

                except EOFError:
                    break

            user_input = "\n".join(lines).strip()

            if not user_input:
                continue

            print("\n⏳ Agent 正在思考...")

            events = agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": patient_thread_id}},
                stream_mode="values"
            )

            last_printed_msg_id = None
            for event in events:
                messages = event.get("messages", [])
                if not messages:
                    continue
                last_msg = messages[-1]

                if id(last_msg) == last_printed_msg_id:
                    continue
                last_printed_msg_id = id(last_msg)

                # 拦截工具调用
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        print(f"\n⚙️  [工具调用] {tc.get('name', 'unknown')} (参数：{tc.get('args', {})})")

                # 拦截 human-in-the-loop 中断
                if hasattr(last_msg, 'interrupt'):
                    interrupt = getattr(last_msg, 'interrupt', None)
                    if interrupt:
                        print(f"\n⏸️  [等待人类审批] 操作：{interrupt}")

                # 拦截文本输出
                content = getattr(last_msg, 'content', '')
                if content:
                    print(f"\n🤖 Agent:\n{content}")

                # 深度思考内容（如模型支持）
                if hasattr(last_msg, 'additional_kwargs') and 'reasoning_content' in last_msg.additional_kwargs:
                    reasoning = last_msg.additional_kwargs['reasoning_content']
                    if reasoning:
                        print(f"\n🧠 [深度思考]:\n{reasoning}")

        except KeyboardInterrupt:
            print("\n会诊被用户强行终止。")
            break
        except Exception as e:
            print(f"\n❌ 执行遇到严重错误：{e}")
            import traceback
            traceback.print_exc()
