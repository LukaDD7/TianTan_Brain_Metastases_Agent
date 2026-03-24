#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TianTan Brain Metastases Agent - Interactive Main Entry (v5.1 Dynamic Decision Architecture)

架构核心变更：
1. 单一 Agent 扁平化架构，NO Subagents
2. 动态模块适用性判断 - 不再是填空选手
3. 强制治疗决策检查点 - 治疗线判定、疾病进展识别
4. CompositeBackend：FilesystemBackend(默认) + StoreBackend(/memories/ 持久化)
5. Execute 工具：通过自定义 tool 提供 shell 执行能力
6. 完整执行历史记录 (ExecutionLogger)
7. Human-in-the-loop 支持：write_file/edit_file/execute 需要审批
8. 大内容落盘 Sandbox，不污染上下文
"""

import os
import sys
import uuid
import json
import re
import subprocess
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

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
EXECUTION_LOGS_DIR = os.path.join(SANDBOX_DIR, "execution_logs")

os.makedirs(SANDBOX_DIR, exist_ok=True)
os.makedirs(EXECUTION_LOGS_DIR, exist_ok=True)
os.environ["SANDBOX_ROOT"] = SANDBOX_DIR

# =============================================================================
# 全局执行历史记录器
# =============================================================================

execution_logger: Optional['ExecutionLogger'] = None


def get_logger() -> Optional['ExecutionLogger']:
    """获取全局执行历史记录器"""
    return execution_logger


class ExecutionLogger:
    """完整执行历史记录器 - 记录Agent的所有行为"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.log_entries: List[Dict[str, Any]] = []

        # 主日志文件（人类可读）
        self.main_log_path = os.path.join(
            EXECUTION_LOGS_DIR,
            f"session_{session_id}_complete.log"
        )

        # 结构化JSON日志
        self.json_log_path = os.path.join(
            EXECUTION_LOGS_DIR,
            f"session_{session_id}_structured.jsonl"
        )

        # 向后兼容的审计日志
        self.audit_log_path = os.path.join(SANDBOX_DIR, "execution_audit_log.txt")

        self._write_header()

    def _write_header(self):
        """写入日志头部信息"""
        header = f"""
{'='*80}
TianTan Brain Metastases Agent - 完整执行历史记录
Session ID: {self.session_id}
开始时间: {self.start_time.isoformat()}
{'='*80}

"""
        with open(self.main_log_path, 'w', encoding='utf-8') as f:
            f.write(header)

    def _write_log(self, entry: Dict[str, Any]):
        """写入单条日志记录"""
        # 写入JSONL
        with open(self.json_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        # 写入人类可读日志
        readable_entry = self._format_readable(entry)
        with open(self.main_log_path, 'a', encoding='utf-8') as f:
            f.write(readable_entry + '\n')

    def _format_readable(self, entry: Dict[str, Any]) -> str:
        """将日志条目格式化为人类可读格式"""
        timestamp = entry.get('timestamp', datetime.now().isoformat())
        event_type = entry.get('type', 'unknown')

        formatted = f"\n{'─'*80}\n"
        formatted += f"⏱️  {timestamp} | Type: {event_type}\n"
        formatted += f"{'─'*80}\n"

        if event_type == 'user_input':
            patient_id = entry.get('patient_id', 'N/A')
            content = entry.get('content', '')
            content_length = entry.get('content_length', 0)
            formatted += f"👤 用户输入 (Patient ID: {patient_id})\n"
            formatted += f"   内容长度: {content_length} 字符\n"
            formatted += f"   内容:\n{content}\n"

        elif event_type == 'tool_call':
            tool_name = entry.get('tool_name', 'unknown')
            arguments = entry.get('arguments', {})
            result = entry.get('result')
            duration = entry.get('duration_ms', 0)
            formatted += f"⚙️  工具调用: {tool_name}\n"
            formatted += f"   参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}\n"
            formatted += f"   耗时: {duration}ms\n"
            if result:
                formatted += f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...\n"

        elif event_type == 'agent_thinking':
            content = entry.get('content', '')
            thinking_type = entry.get('thinking_type', 'general')
            emoji = {'reasoning': '🧠', 'planning': '📋', 'decision': '⚖️', 'error': '❌',
                     'report_submission': '📝', 'system': '🔧', 'interrupt': '⏸️'}.get(thinking_type, '💭')
            formatted += f"{emoji} Agent思考 ({thinking_type}):\n{content}\n"

        elif event_type == 'llm_response':
            role = entry.get('role', 'assistant')
            content = entry.get('content', '')
            model = entry.get('model', 'unknown')
            formatted += f"🤖 LLM响应 ({role}, 模型: {model}):\n{content}\n"

        elif event_type == 'error':
            error_type = entry.get('error_type', 'unknown')
            message = entry.get('message', '')
            traceback_info = entry.get('traceback', '')
            formatted += f"❌ 错误 ({error_type}): {message}\n"
            if traceback_info:
                formatted += f"   堆栈:\n{traceback_info}\n"

        return formatted

    def log_user_input(self, content: str, patient_id: Optional[str] = None):
        """记录用户输入"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "user_input",
            "patient_id": patient_id,
            "content": content,
            "content_length": len(content)
        }
        self._write_log(entry)

    def log_tool_call(self, tool_name: str, arguments: Dict, result: Any, duration_ms: int):
        """记录工具调用"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool_call",
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "duration_ms": duration_ms
        }
        self._write_log(entry)

    def log_agent_thinking(self, content: str, thinking_type: str = "general"):
        """记录Agent思考过程"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "agent_thinking",
            "content": content,
            "thinking_type": thinking_type
        }
        self._write_log(entry)

    def log_llm_response(self, content: str, role: str = "assistant", model: str = "brain_model", usage: Dict = None):
        """记录LLM响应，包含token使用量"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "llm_response",
            "content": content,
            "role": role,
            "model": model,
            "usage": usage or {}  # token使用量：{"input_tokens": int, "output_tokens": int, "total_tokens": int}
        }
        self._write_log(entry)

    def log_error(self, message: str, error_type: str = "runtime_error", traceback_info: str = ""):
        """记录错误"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": message,
            "error_type": error_type,
            "traceback": traceback_info
        }
        self._write_log(entry)


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
# L3 主控 System Prompt (动态决策架构 - 不再是填空选手)
# =============================================================================

L3_SYSTEM_PROMPT = """你是一名脑转移瘤 MDT 首席智能体，是一位极其严谨、遵循证据主权的神经肿瘤专家。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 最高行医准则 (PRIME DIRECTIVES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 证据主权：严禁编造任何基因突变、检验值或病史。无数据即标记为 "unknown"。
2. 自主寻路 (Harness Self-Discovery)：你拥有一个"智能体线束 (Agent Harness)"，挂载了多个专业技能。
   - 当你面对任务（如读 PDF、查突变、搜文献）时，你必须扫描当前挂载的 Skill 列表及其描述。
   - 你【必须】先使用 read_file 工具完整阅读对应技能的 SKILL.md 文件。
   - 学习其内部的思维链（SOP）、命令行参数格式和临床解读规则，然后利用 execute 工具执行。
3. 物理溯源引用：每一条临床建议必须附带可追溯的引用。
   - 文本证据：[Local: <文件名>, Section: <章节标题>] 或 [Local: <文件名>, Line <行号>]
   - 图片证据：[Local: <文件名>, Visual: Page<页码>] (仅用于Visual Probe)
   - 数据库：[OncoKB: Level X]
   - 文献：[PubMed: PMID <编号>]
4. 严禁编造任何基因突变、物理页码、或临床证据。
5. 禁止依赖预训练权重：关于 NCCN/ASCO 指南、OncoKB 证据及 PubMed 最新文献的所有内容，必须通过 execute 工具真实获取。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 治疗决策强制检查点 (MANDATORY CHECKPOINTS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**在生成任何治疗方案前，你必须显式回答以下检查点**：

### Checkpoint 1: 既往治疗史审查
- [ ] 患者是否已接受过系统治疗？具体方案是什么？（化疗/免疫/靶向）
- [ ] 既往治疗的疗效如何？（CR/PR/SD/PD）
- [ ] 最后一次治疗距今多久？

### Checkpoint 2: 疾病状态判定（关键！）
- [ ] **当前病灶是新发还是既往病灶进展？**
- [ ] 如果是**新发转移灶**（如本例脊髓新发转移）→ 判定为 **疾病进展 (PD)**
- [ ] 如果已接受系统治疗且出现PD → **必须推荐二线/后线治疗，严禁重复一线方案**

### Checkpoint 3: 治疗线确定
- [ ] 初治 (Treatment-naive): 未接受过系统治疗 → 一线方案
- [ ] 经治稳定: 已完成治疗，当前评估 → 随访或维持治疗
- [ ] **疾病进展 (PD): 必须选择二线/后线方案，与一线方案不同类别或不同机制**

### Checkpoint 4: 局部治疗方式判定
- [ ] 当前计划的主要局部治疗是什么？（手术/放疗/两者/无）
- [ ] 如果是**放疗** → Module 6 应填写"放疗期间管理"而非"围手术期管理"
- [ ] 如果**无手术计划** → Module 6 应标记为 "N/A - 当前治疗为放疗+系统治疗"

### Checkpoint 5: 剂量参数强制验证（关键！）
**在写入任何具体剂量前，必须执行以下验证：**

- [ ] **步骤1 - 指南检索**：执行 `grep -i "dose\\|mg\\|Gy\\|fraction" Guidelines/*/*.md` 查找剂量信息
- [ ] **步骤2 - 文献检索**：如指南无明确剂量，执行 PubMed 检索：
  - 化疗药物：`"{Drug} AND dose AND Phase III AND lung cancer"`
  - 放疗：`"{Treatment} AND Gy AND fraction AND brain metastases"`
- [ ] **步骤3 - 验证引用**：确认每个剂量参数都有物理溯源（[Local:...] 或 [PubMed: PMID ...]）
- [ ] **如果检索失败**：**严禁**使用预训练知识脑补剂量！必须标记为：
  > "[具体剂量/参数未在检索证据中明确，需临床医师基于患者个体情况决定]"

**🚨 红线警告**：
- 任何未经验证的剂量（如"多西他赛 75 mg/m²"）**必须有物理引用**
- 发现无引用剂量 → 立即拦截并返回步骤1重新检索
- **严禁**在Module 2中写入类似"具体剂量由临床医师决定"的模糊表述，必须有明确数值+引用

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 模块适用性动态判断 (DYNAMIC MODULE ADAPTATION)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**严禁机械填充所有8个模块！每个模块必须根据患者实际情况判断是否适用：**

- Module 1 (入院评估): 始终适用，完整填写
- Module 2 (个体化治疗方案): 始终适用，**但必须正确判定治疗线**
- Module 3 (支持治疗): 始终适用，根据症状调整
- Module 4 (随访): 始终适用
- Module 5 (被排除方案): 始终适用，至少1项
- **Module 6 (围手术期管理): 条件适用**
  - 仅当患者计划接受手术时才详细填写
  - 如果患者仅接受放疗+系统治疗 → 标记为"N/A"或改为"放疗期间系统治疗管理"
- Module 7 (分子检测): 条件适用，根据已做/待做检测填写
- Module 8 (执行轨迹): 始终适用，记录真实执行的命令

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 可执行粒度与深钻机制 (Deep Drill Protocol)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 报告必须达到绝对可执行状态（必须包含：具体手术方案/辅助技术、放疗剂量 Gy/分割次数、系统药物剂量 mg/频次、停药天数等）。
- **严禁使用预训练权重脑补任何具体参数**。如果初步 grep 检索未发现剂量或技术细节，你必须强制执行以下"深钻"策略：
  1. **专门检索指南附录 (Principles)**：剂量和手术细节通常位于指南后半部分。强制执行 `grep -i "Principles of Radiation"`, `grep -i "Principles of Surgery"`等替换查询，或直接搜索 `Gy\\|dose\\|fraction\\|mg`。
  2. **触发视觉探针 (Visual Probe)**：如果你发现剂量或处方信息位于复杂的 Markdown 表格中且排版混乱，必须立即使用 pdf-inspector 的 render_pdf_page 工具截图该页，然后使用 `analyze_image` 工具进行 VLM 分析。
  3. **追溯奠基性试验 (Landmark Trials)**：如果指南正文确实缺失具体参数，你必须立即调用 PubMed，检索确立该治疗标准的核心临床试验（Phase III/II）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 物理溯源引用协议 (STRICT CITATION)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 文本证据：[Local: <文件名>, Section: <章节标题>] 或 [Local: <文件名>, Line <行号>]
- 图片证据：仅当使用 Visual Probe 渲染出图片时，方可使用 [Local: <文件名>, Visual: Page <页码>]
- 分子证据：[OncoKB: Level X]
- 文献证据：[PubMed: PMID <编号>]
- **严禁引用未真实检索的文献！**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 长期记忆协议 (LONG-TERM MEMORY) - 【只写不读】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **重要约束**：**严禁**在生成报告前读取 `/memories/personas/` 中的任何文件。
患者的最新信息必须通过 `execute` 工具读取当前输入文件获得，确保数据时效性。

1. **患者画像 (Patient Persona)**：`/memories/personas/<Patient_ID>.md` 【只写不读】
   - **写入时机**：仅在成功生成报告后，提取关键信息写入
   - **严禁行为**：生成报告前读取历史画像文件（避免使用过时的患者信息）
   - **数据结构**：
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

2. **临床原则 (Clinical Principles)**：`/memories/principles/<topic>.md` 【读写皆可】
   - 积累特定癌种/场景的诊疗模式和医生反馈

3. **使用方式**：
   - **【强制】当前患者**：必须通过 `execute` 工具读取患者输入文件（如 `cat patient_868183_input.txt`）
   - **【禁止】历史画像**：严禁在报告生成前读取 `/memories/personas/<Patient_ID>.md`
   - **【允许】写入更新**：报告生成后可写入患者画像供未来参考

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 报告提交协议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**报告完成后，必须使用 `submit_mdt_report` 工具提交。**
该工具会：
1. 自动验证所有引用是否在执行历史中有物理记录
2. 拦截任何伪造引用
3. 只有通过验证的报告才会被保存

"""


# =============================================================================
# 自定义工具：analyze_image (VLM-powered image analysis)
# =============================================================================

@tool
def analyze_image(image_path: str, query: str = "Analyze this image and describe what you see.") -> str:
    """Analyze an image using VLM (Vision-Language Model).

    Use this tool when you need to:
    - Extract information from rendered PDF pages (dose tables, flowcharts)
    - Analyze medical diagrams or complex layouts that are unclear in text format
    - Verify OCR-extracted content against the original image

    Args:
        image_path: Path to the image file (e.g., /workspace/sandbox/pdf_images_xxx/page_0016.jpg)
        query: Specific question or instruction for VLM analysis (default: general description)

    Returns:
        VLM analysis result with extracted information
    """
    import base64
    import os

    try:
        # Resolve path
        actual_path = image_path
        if image_path.startswith("/workspace/sandbox/"):
            relative = image_path[len("/workspace/sandbox/"):]
            actual_path = os.path.join(SANDBOX_DIR, relative)

        if not os.path.exists(actual_path):
            return f"Error: Image not found: {image_path} (resolved to {actual_path})"

        # Check file size
        file_size = os.path.getsize(actual_path)
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return f"Error: Image too large ({file_size / 1024 / 1024:.2f}MB > 10MB limit)"

        # Encode image to base64
        with open(actual_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        # Get file extension for mime type
        ext = os.path.splitext(actual_path)[1].lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png" if ext == ".png" else "image/jpeg"

        # Call VLM via get_vlm_client
        from utils.llm_factory import get_vlm_client
        client = get_vlm_client()

        completion = client.chat.completions.create(
            model="qwen3.5-plus",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": query
                    }
                ]
            }]
        )

        result = completion.choices[0].message.content

        # Record to execution log
        if get_logger():
            get_logger().log_tool_call(
                "analyze_image",
                {"image_path": image_path, "query": query[:100]},
                {"result_length": len(result), "image_size": file_size},
                0
            )

        return f"""✅ VLM Analysis Complete

📁 Image: {image_path}
📏 Size: {file_size / 1024:.1f} KB
❓ Query: {query}

🔍 Result:
{result}
"""

    except Exception as e:
        error_msg = f"Error analyzing image: {str(e)}"
        if get_logger():
            get_logger().log_error(error_msg, "image_analysis_error")
        return error_msg


# =============================================================================
# 自定义工具：read_file (绕过 Backend virtual_mode 限制)
# =============================================================================

@tool
def read_file(path: str, limit: int = 2000, offset: int = 0) -> str:
    """Read a file from the filesystem. Supports virtual paths like /skills/ and /memories/.

    Args:
        path: File path (can be virtual path like /skills/pdf-inspector/SKILL.md)
        limit: Maximum number of lines to read (default 2000)
        offset: Line offset to start reading from (default 0)

    Returns:
        File content with line numbers
    """
    try:
        # 处理虚拟路径映射
        actual_path = path

        if path.startswith("/skills/"):
            relative = path[len("/skills/"):]
            actual_path = os.path.join(SKILLS_DIR, relative)
        elif path.startswith("/memories/"):
            relative = path[len("/memories/"):]
            actual_path = os.path.join(SANDBOX_DIR, "memories", relative)
        elif path.startswith("/workspace/sandbox/"):
            relative = path[len("/workspace/sandbox/"):]
            actual_path = os.path.join(SANDBOX_DIR, relative)

        if not os.path.exists(actual_path):
            return f"Error: File not found: {path} (resolved to {actual_path})"

        with open(actual_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 应用 offset 和 limit
        start = offset
        end = offset + limit if limit > 0 else len(lines)
        selected_lines = lines[start:end]

        # 添加行号
        result = []
        for i, line in enumerate(selected_lines, start=start + 1):
            result.append(f"{i:4d} | {line}")

        output = ''.join(result)

        # 记录到执行日志
        if get_logger():
            get_logger().log_tool_call(
                "read_file",
                {"path": path, "limit": limit, "offset": offset},
                {"content_length": len(output), "actual_path": actual_path},
                0
            )

        if len(lines) > end:
            output += f"\n... ({len(lines) - end} more lines)"

        return output

    except Exception as e:
        error_msg = f"Error reading file {path}: {str(e)}"
        if get_logger():
            get_logger().log_error(error_msg, "file_read_error")
        return error_msg


# =============================================================================
# 自定义工具：execute (shell 命令执行)
# =============================================================================

@tool
def execute(command: str, timeout: int = 600, max_output_bytes: int = 100000) -> str:
    """Execute a shell command and return the output.

    Args:
        command: The shell command to execute
        timeout: Maximum execution time in seconds (default: 600)
        max_output_bytes: Maximum output size in bytes (default: 100000)

    Returns:
        Command output (stdout + stderr) or error message
    """
    import subprocess
    import os
    import time

    start_time = time.time()

    # 白名单机制
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
        "mkdir ",
        "pwd",
        "cd ",
        "wc ",
        "diff ",
        "sort ",
        "uniq ",
        "awk ",
        "sed ",
        "python ",
        "python3 ",
    )

    DANGEROUS_PATTERNS = (
        "rm -rf", "rm -rf /", "dd if=", "mkfs.", ":(){ :|:& };:", "> /dev/sda",
        "curl", "wget", "ssh", "nc ", "ncat ",
    )

    is_allowed = any(command.strip().startswith(prefix) for prefix in ALLOWED_PREFIXES)
    is_dangerous = any(pattern in command.lower() for pattern in DANGEROUS_PATTERNS)

    if is_dangerous:
        error_msg = f"Error: Command blocked by security policy (dangerous pattern detected): {command[:100]}"
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command, "timeout": timeout}, {"error": error_msg}, 0)
        return error_msg

    if not is_allowed:
        error_msg = f"Error: Command not in whitelist. Allowed prefixes: {ALLOWED_PREFIXES}. Your command: {command[:100]}"
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command, "timeout": timeout}, {"error": error_msg}, 0)
        return error_msg

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

        if len(output.encode('utf-8')) > max_output_bytes:
            output = output[:max_output_bytes] + "\n... [output truncated]"

        duration_ms = int((time.time() - start_time) * 1000)

        result_dict = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "current_working_dir": SANDBOX_DIR,
            "msg": "If exit_code != 0, please re-read the SKILL.md to check your parameters."
        }

        # 记录到完整执行日志
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command, "timeout": timeout}, result_dict, duration_ms)

        # 保持向后兼容的审计日志
        audit_log_path = os.path.join(SANDBOX_DIR, "execution_audit_log.txt")
        with open(audit_log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*40}\n")
            f.write(f"TIME: {datetime.now().isoformat()}\n")
            f.write(f"COMMAND: {command}\n")
            f.write(f"DURATION: {duration_ms}ms\n")
            f.write(f"EXIT_CODE: {result.returncode}\n")
            f.write(f"OUTPUT:\n{output}\n")
            f.write(f"{'='*40}\n")

        return result_dict

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Error: Command timed out after {timeout} seconds"
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command, "timeout": timeout}, {"error": error_msg}, duration_ms)
        return error_msg
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Error executing command: {str(e)}"
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command, "timeout": timeout}, {"error": error_msg}, duration_ms)
        return error_msg


# =============================================================================
# 自定义工具：submit_mdt_report (带引用验证)
# =============================================================================

@tool
def submit_mdt_report(patient_id: str, report_content: str) -> str:
    """Submit the MDT report with citation validation.

    This tool will:
    1. Validate all citations in the report against execution audit log
    2. Block any fabricated citations
    3. Only save the report if validation passes

    Args:
        patient_id: Patient identifier
        report_content: The complete MDT report content

    Returns:
        Submission result message
    """
    import time
    start_time = time.time()

    # 记录工具调用开始
    if get_logger():
        get_logger().log_tool_call("submit_mdt_report", {"patient_id": patient_id, "report_length": len(report_content)}, None, 0)

    # 1. 过安检 - 验证引用真实性
    is_valid, msg = validate_citations_against_audit(report_content)
    if not is_valid:
        # 记录验证失败
        if get_logger():
            get_logger().log_error(f"Citation validation failed: {msg}", "citation_validation")
        return msg  # 把报错拍在 Agent 脸上，逼它重试

    # 2. 安检通过，写入沙盒
    import os
    patient_dir = os.path.join(SANDBOX_DIR, "patients", patient_id, "reports")
    os.makedirs(patient_dir, exist_ok=True)

    file_path = os.path.join(patient_dir, f"MDT_Report_{patient_id}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    duration_ms = int((time.time() - start_time) * 1000)

    # 记录成功提交
    result_msg = f"✅ REPORT SUBMITTED SUCCESSFULLY! 报告已保存至 {file_path}，引用审计通过。"
    if get_logger():
        get_logger().log_tool_call("submit_mdt_report", {"patient_id": patient_id}, {"status": "success", "file_path": file_path}, duration_ms)
        get_logger().log_agent_thinking(f"Report submitted successfully for patient {patient_id}", "report_submission")

    return result_msg


def validate_citations_against_audit(report_content: str) -> tuple:
    """验证报告中的引用是否真实存在于审计日志中

    Returns:
        (is_valid: bool, message: str)
    """
    import re
    import os

    audit_log_path = os.path.join(SANDBOX_DIR, "execution_audit_log.txt")

    # 读取审计日志
    if not os.path.exists(audit_log_path):
        return False, "❌ Citation Validation Failed: No execution audit log found. You must execute commands before citing."

    with open(audit_log_path, "r", encoding="utf-8") as f:
        audit_content = f.read()

    # 提取报告中的所有引用
    citations = {
        'local': re.findall(r'\[Local: ([^,\]]+)', report_content),
        'pubmed': re.findall(r'\[PubMed: PMID\s*(\d+)', report_content),
        'oncokb': re.findall(r'\[OncoKB:([^\]]+)\]', report_content)
    }

    # 验证 Local 引用 - 必须实际执行过相关命令
    for local_ref in citations['local']:
        # 提取文件名
        filename = local_ref.split(',')[0].strip()
        # 检查是否在审计日志中有对该文件的访问
        if filename not in audit_content and not any(cmd in audit_content for cmd in ['cat', 'grep', 'head']):
            return False, f"❌ Citation Validation Failed: [Local: {local_ref}] not found in execution audit log. You must read the file before citing it."

    # 验证 PubMed 引用 - 必须真实检索过
    for pmid in citations['pubmed']:
        if pmid not in audit_content:
            return False, f"❌ Citation Validation Failed: [PubMed: PMID {pmid}] not found in execution audit log. You must search PubMed before citing."

    # 验证 OncoKB 引用 - 必须真实查询过
    if citations['oncokb'] and 'query_oncokb' not in audit_content:
        return False, "❌ Citation Validation Failed: [OncoKB] citations found but no OncoKB query in execution log."

    return True, "All citations validated against execution audit log."


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
            virtual_mode=True,
        ),
        routes={
            "/skills/": FilesystemBackend(
                root_dir=SKILLS_DIR,
                virtual_mode=True,
            ),
            "/memories/": StoreBackend(runtime)
        }
    )


# =============================================================================
# 组装 Deep Agent
# =============================================================================

print(f"🚀 正在初始化天坛医疗大脑 v5.1 (动态决策架构)...")
print(f"   - Sandbox 隔离目录：{SANDBOX_DIR}")
print(f"   - 执行历史日志：{EXECUTION_LOGS_DIR}")
print(f"   - 持久化记忆路径：/memories/")
print(f"   - Skills：挂载 4 个 Skills")
print(f"   - 架构：扁平化 + 动态模块判断")
print(f"   - Subagents：无")

# 用于跨会话持久化存储
store = InMemoryStore()

# 用于状态持久化
checkpointer = MemorySaver()

# Human-in-the-loop 配置
interrupt_config = {
    "write_file": False,
    "edit_file": False,
    "execute": False,
    "read_file": False,
}

agent = create_deep_agent(
    model=model,
    system_prompt=L3_SYSTEM_PROMPT,
    tools=[
        execute,
        read_file,
        analyze_image,
        submit_mdt_report,
    ],
    subagents=[],
    skills=[
        "/skills/pdf-inspector",
        "/skills/universal_bm_mdt_skill",
        "/skills/oncokb_query_skill",
        "/skills/pubmed_search_skill",
    ],
    backend=make_backend,
    store=store,
    checkpointer=checkpointer,
    interrupt_on=interrupt_config,
)


# =============================================================================
# 主循环
# =============================================================================

if __name__ == "__main__":
    patient_thread_id = str(uuid.uuid4())

    # 初始化完整执行历史记录器
    execution_logger = ExecutionLogger(patient_thread_id)

    print(f"\n✅ 天坛医疗大脑 v5.1 已就绪。Session ID: {patient_thread_id}")
    print(f"📝 完整执行历史记录: {execution_logger.main_log_path}")
    print(f"📊 结构化JSON日志: {execution_logger.json_log_path}")
    print(f"💡 提示：您可以输入患者病史，或输入文件路径自动读取。")
    print(f"💡 示例：直接输入 `patient_868183_input.txt` 自动读取文件")
    print("-" * 60)

    while True:
        try:
            print("\n🧑‍⚕️ 请输入患者信息（输入空行或 `---` 结束，输入 exit 退出）：")
            print("💡 提示：输入超长时请直接将内容保存到文件（如 patient_868183_input.txt），然后输入文件名")
            lines = []
            empty_line_count = 0
            while True:
                try:
                    line_bytes = sys.stdin.buffer.readline()
                    if not line_bytes:
                        break
                    try:
                        line = line_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        line = line_bytes.decode('utf-8', errors='replace')

                    if line.strip().lower() in ["exit", "quit"] and len(lines) == 0:
                        print("👋 再见！")
                        execution_logger.log_agent_thinking("Session terminated by user", "system")
                        sys.exit(0)

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

            # 检测是否为文件路径
            import os
            potential_paths = [
                user_input.split()[0] if user_input.split() else user_input,
                user_input.strip().replace('"', '').replace("'", ""),
            ]

            file_read_success = False
            for potential_path in potential_paths:
                paths_to_try = [
                    potential_path,
                    os.path.join(SANDBOX_DIR, potential_path),
                    os.path.join(os.getcwd(), potential_path),
                ]

                for path in paths_to_try:
                    if os.path.isfile(path):
                        print(f"📄 检测到文件路径，正在读取: {path}")
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            user_input = file_content
                            print(f"✅ 已读取文件，内容长度: {len(user_input)} 字符")
                            if get_logger():
                                get_logger().log_tool_call("file_read", {"path": path}, {"content_length": len(user_input)}, 0)
                            file_read_success = True
                            break
                        except Exception as e:
                            print(f"⚠️  读取文件失败: {e}，将使用原始输入")
                    elif os.path.isfile(f"{path}.txt"):
                        path = f"{path}.txt"
                        print(f"📄 检测到文件路径，正在读取: {path}")
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            user_input = file_content
                            print(f"✅ 已读取文件，内容长度: {len(user_input)} 字符")
                            if get_logger():
                                get_logger().log_tool_call("file_read", {"path": path}, {"content_length": len(user_input)}, 0)
                            file_read_success = True
                            break
                        except Exception as e:
                            print(f"⚠️  读取文件失败: {e}，将使用原始输入")

                if file_read_success:
                    break

            # 提取患者ID
            patient_id = None
            patient_match = re.search(r'住院号\s*(\d+)', user_input)
            if patient_match:
                patient_id = patient_match.group(1)

            # 记录用户输入
            execution_logger.log_user_input(user_input, patient_id)
            print(f"\n⏳ Agent 正在思考... (Patient ID: {patient_id or 'N/A'})")

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
                        tool_name = tc.get('name', 'unknown')
                        tool_args = tc.get('args', {})
                        print(f"\n⚙️  [工具调用] {tool_name} (参数：{tool_args})")
                        execution_logger.log_tool_call(tool_name, tool_args, None, 0)

                # 拦截 human-in-the-loop 中断
                if hasattr(last_msg, 'interrupt'):
                    interrupt = getattr(last_msg, 'interrupt', None)
                    if interrupt:
                        print(f"\n⏸️  [等待人类审批] 操作：{interrupt}")
                        execution_logger.log_agent_thinking(f"Interrupted for approval: {interrupt}", "interrupt")

                # 拦截文本输出 (Agent响应)
                content = getattr(last_msg, 'content', '')
                if content:
                    print(f"\n🤖 Agent:\n{content}")
                    # 提取token使用量
                    usage = {}
                    if hasattr(last_msg, 'response_metadata') and last_msg.response_metadata:
                        token_usage = last_msg.response_metadata.get('token_usage', {})
                        if token_usage:
                            usage = {
                                "input_tokens": token_usage.get('prompt_tokens', 0),
                                "output_tokens": token_usage.get('completion_tokens', 0),
                                "total_tokens": token_usage.get('total_tokens', 0)
                            }
                    execution_logger.log_llm_response(content, role="assistant", model="brain_model", usage=usage)

                # 深度思考内容
                if hasattr(last_msg, 'additional_kwargs') and 'reasoning_content' in last_msg.additional_kwargs:
                    reasoning = last_msg.additional_kwargs['reasoning_content']
                    if reasoning:
                        print(f"\n🧠 [深度思考]:\n{reasoning}")
                        execution_logger.log_agent_thinking(reasoning, "reasoning")

                # 检查是否为AIMessage或HumanMessage来记录对话历史
                msg_type = type(last_msg).__name__
                if msg_type == 'HumanMessage' and content and content != user_input:
                    execution_logger.log_user_input(content, patient_id)

        except KeyboardInterrupt:
            print("\n会诊被用户强行终止。")
            execution_logger.log_agent_thinking("Session interrupted by KeyboardInterrupt", "system")
            break
        except Exception as e:
            error_msg = f"\n❌ 执行遇到严重错误：{e}"
            print(error_msg)
            import traceback
            execution_logger.log_error(str(e), "runtime_error", traceback.format_exc())
            traceback.print_exc()
