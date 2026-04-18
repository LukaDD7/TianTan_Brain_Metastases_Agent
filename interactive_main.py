#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TianTan Brain Metastases MDT Agent - Interactive Main Entry (v6.0 Hierarchical Agentic MDT)

架构核心变更 (v5.2 → v6.0)：
1. 单一扁平 Agent → Orchestrator + 5 个专科 SubAgent 分层架构
2. 4 个 Domain SubAgent (神外/放疗/内科/分子病理) 并行执行专科评估
3. 1 个 Evidence Auditor SubAgent 负责报告引用真实性验证
4. 报告格式由 Pydantic Schema 强制约束（schemas/mdt_report.py）
5. 双轨强制确认机制：剂量/决策树参数必须文本+视觉双轨验证
6. 全面升级至 qwen3.6-plus（统一 Orchestrator 和 SubAgent 模型）
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
from config import SUBAGENT_MODEL_NAME, AUDITOR_EGR_THRESHOLD, AUDITOR_MAX_RETRY

# Import SubAgent system prompts
from agents.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from agents.neurosurgery_prompt import NEUROSURGERY_SYSTEM_PROMPT
from agents.radiation_prompt import RADIATION_SYSTEM_PROMPT
from agents.medical_oncology_prompt import MEDICAL_ONCOLOGY_SYSTEM_PROMPT
from agents.molecular_pathology_prompt import MOLECULAR_PATHOLOGY_SYSTEM_PROMPT
from agents.auditor_prompt import AUDITOR_SYSTEM_PROMPT


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

# Skills 路径常量（用于 SubAgent skills 分配）
_S = lambda name: os.path.join(SKILLS_DIR, name)

# Core: pdf-inspector + pubmed (all agents)
CORE_SKILLS = [
    _S("pdf-inspector"),
    _S("pubmed_search_skill"),
]

# P0 New Skills (v6.0)
_CNS_DB       = _S("cns_drug_db_skill")          # CNS 穿透性数据库
_PERIOP       = _S("perioperative_safety_skill")  # 围手术期停药数据库
_DDI          = _S("drug_interaction_skill")      # 药物相互作用 RxNav API
_ONCOKB       = _S("oncokb_query_skill")          # OncoKB 分子靶点
_PROG         = _S("prognostic_scoring_skill")    # DS-GPA 预后评分

# SubAgent skill bundles
# 神经外科：核心 + 围手术期停药 + 药物相互作用
NEUROSURGERY_SKILLS = CORE_SKILLS + [_PERIOP, _DDI]

# 放疗：核心（只需指南+文献，剂量由双轨验证）
RADIATION_SKILLS = CORE_SKILLS

# 内科：核心 + OncoKB + CNS穿透性数据库 + 药物相互作用
MEDICAL_ONCOLOGY_SKILLS = CORE_SKILLS + [_ONCOKB, _CNS_DB, _DDI]

# 分子病理：核心 + OncoKB
MOLECULAR_PATHOLOGY_SKILLS = CORE_SKILLS + [_ONCOKB]

# Evidence Auditor：核心（验证引用，不做临床推理）
AUDITOR_SKILLS = CORE_SKILLS

# Orchestrator：报告模板 + 预后评分
ORCHESTRATOR_SKILLS = [
    _S("universal_bm_mdt_skill"),
    _PROG,
]


# =============================================================================
# 全局执行历史记录器（保持向后兼容）
# =============================================================================

execution_logger: Optional['ExecutionLogger'] = None


def get_logger() -> Optional['ExecutionLogger']:
    return execution_logger


class ExecutionLogger:
    """完整执行历史记录器"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.log_entries: List[Dict[str, Any]] = []
        self.patient_id: Optional[str] = None
        self._finalized = False

        self.main_log_path = os.path.join(
            EXECUTION_LOGS_DIR,
            f"session_{session_id}_complete.log"
        )
        self.json_log_path = os.path.join(
            EXECUTION_LOGS_DIR,
            f"session_{session_id}_structured.jsonl"
        )
        self.audit_log_path = os.path.join(SANDBOX_DIR, "execution_audit_log.txt")
        self._write_header()

    def set_patient_id(self, patient_id: str):
        if self._finalized or not patient_id:
            return
        self.patient_id = patient_id
        date_str = self.start_time.strftime("%Y%m%d")
        new_main = os.path.join(
            EXECUTION_LOGS_DIR,
            f"session_{date_str}_{patient_id}_{self.session_id}_complete.log"
        )
        new_json = os.path.join(
            EXECUTION_LOGS_DIR,
            f"session_{date_str}_{patient_id}_{self.session_id}_structured.jsonl"
        )
        try:
            if os.path.exists(self.main_log_path):
                os.rename(self.main_log_path, new_main)
            if os.path.exists(self.json_log_path):
                os.rename(self.json_log_path, new_json)
            self.main_log_path = new_main
            self.json_log_path = new_json
        except Exception:
            pass

    def _write_header(self):
        header = {
            "timestamp": self.start_time.isoformat(),
            "type": "session_start",
            "session_id": self.session_id,
            "architecture": "v6.0 Hierarchical MDT (Orchestrator + 5 SubAgents)",
            "model": SUBAGENT_MODEL_NAME,
        }
        self._write_log(header)

    def _write_log(self, entry: Dict):
        self.log_entries.append(entry)
        try:
            with open(self.json_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def log_user_input(self, content: str, patient_id: Optional[str] = None):
        self._write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "user_input",
            "patient_id": patient_id,
            "content": content,
            "content_length": len(content)
        })

    def log_tool_call(self, tool_name: str, arguments: Dict, result: Any, duration_ms: int):
        self._write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "tool_call",
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "duration_ms": duration_ms
        })

    def log_agent_thinking(self, content: str, thinking_type: str = "general"):
        self._write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "agent_thinking",
            "content": content,
            "thinking_type": thinking_type
        })

    def log_llm_response(self, content: str, role: str = "assistant",
                         model: str = "brain_model", usage: Dict = None):
        self._write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "llm_response",
            "content": content,
            "role": role,
            "model": model,
            "usage": usage or {}
        })

    def log_error(self, message: str, error_type: str = "runtime_error", traceback_info: str = ""):
        self._write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": message,
            "error_type": error_type,
            "traceback": traceback_info
        })


# =============================================================================
# 唤醒大模型
# =============================================================================

try:
    print("🧠 正在连接天坛医疗大脑 v6.0 (qwen3.6-plus, Hierarchical MDT)...")
    model = get_brain_client_langchain()
except Exception as e:
    print(f"❌ 大脑初始化失败: {e}")
    sys.exit(1)


# =============================================================================
# 自定义工具：analyze_image (VLM-powered)
# =============================================================================

@tool
def analyze_image(image_path: str, query: str = "Analyze this image and describe what you see.") -> str:
    """Analyze an image using VLM (Vision-Language Model).

    Use this tool when you need to:
    - Verify dose values in rendered PDF pages (Dual-Track Verification)
    - Analyze NCCN decision flowcharts or complex tables
    - Cross-check OCR-extracted content against original PDF image

    Args:
        image_path: Path to the image file (e.g., /workspace/sandbox/pdf_images_xxx/page_0016.jpg)
        query: Specific question for VLM analysis

    Returns:
        VLM analysis result with extracted information
    """
    import base64

    try:
        actual_path = image_path
        if image_path.startswith("/workspace/sandbox/"):
            relative = image_path[len("/workspace/sandbox/"):]
            actual_path = os.path.join(SANDBOX_DIR, relative)

        if not os.path.exists(actual_path):
            return f"Error: Image not found: {image_path} (resolved to {actual_path})"

        file_size = os.path.getsize(actual_path)
        if file_size > 10 * 1024 * 1024:
            return f"Error: Image too large ({file_size / 1024 / 1024:.2f}MB > 10MB limit)"

        with open(actual_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        ext = os.path.splitext(actual_path)[1].lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else \
                    "image/png" if ext == ".png" else "image/jpeg"

        from utils.llm_factory import get_vlm_client
        client = get_vlm_client()

        completion = client.chat.completions.create(
            model=SUBAGENT_MODEL_NAME,  # v6.0: 统一使用 qwen3.6-plus
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                    },
                    {"type": "text", "text": query}
                ]
            }]
        )

        result = completion.choices[0].message.content

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
# 自定义工具：read_file
# =============================================================================

@tool
def read_file(path: str, limit: int = 2000, offset: int = 0) -> str:
    """Read a file from the filesystem. Supports virtual paths like /skills/ and /memories/.

    Args:
        path: File path (virtual paths like /skills/pdf-inspector/SKILL.md supported)
        limit: Maximum number of lines to read (default 2000)
        offset: Line offset to start reading from (default 0)

    Returns:
        File content with line numbers
    """
    try:
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

        start = offset
        end = offset + limit if limit > 0 else len(lines)
        selected_lines = lines[start:end]

        result = []
        for i, line in enumerate(selected_lines, start=start + 1):
            result.append(f"{i:4d} | {line}")

        output = ''.join(result)

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
# 自定义工具：execute (shell)
# =============================================================================

ALLOWED_PREFIXES = (
    "/home/luzhenyang/anaconda3/envs/mineru_env/bin/python",
    "/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python",
    "ls ", "cat ", "head ", "tail ", "grep ", "find .",
    "echo ", "mkdir ", "pwd", "cd ", "wc ", "diff ",
    "sort ", "uniq ", "awk ", "sed ", "python ", "python3 ",
)

DANGEROUS_PATTERNS = (
    "rm -rf", "dd if=", "mkfs.", ":(){ :|:& };:", "> /dev/sda",
    "curl", "wget", "ssh", "nc ", "ncat ",
)


@tool
def execute(command: str, timeout: int = 600, max_output_bytes: int = 100000) -> str:
    """Execute a shell command and return the output.

    This tool is the primary interface for: running Python scripts (OncoKB, PubMed),
    grepping guideline files, rendering PDF pages, and reading large files.

    Args:
        command: Shell command (must match the security whitelist)
        timeout: Max execution time in seconds (default 600)
        max_output_bytes: Max output size in bytes (default 100000)

    Returns:
        Command output dict with exit_code, stdout, stderr
    """
    start_time = time.time()

    is_allowed = any(command.strip().startswith(p) for p in ALLOWED_PREFIXES)
    is_dangerous = any(p in command.lower() for p in DANGEROUS_PATTERNS)

    if is_dangerous:
        error_msg = f"Error: Command blocked by security policy: {command[:100]}"
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command}, {"error": error_msg}, 0)
        return error_msg

    if not is_allowed:
        error_msg = (
            f"Error: Command not in whitelist. "
            f"Allowed prefixes: {ALLOWED_PREFIXES}. "
            f"Your command: {command[:100]}"
        )
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command}, {"error": error_msg}, 0)
        return error_msg

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=SANDBOX_DIR,
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
            "msg": "If exit_code != 0, re-read the SKILL.md to check your parameters."
        }

        if get_logger():
            get_logger().log_tool_call("execute", {"command": command}, result_dict, duration_ms)

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
            get_logger().log_tool_call("execute", {"command": command}, {"error": error_msg}, duration_ms)
        return error_msg
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Error executing command: {str(e)}"
        if get_logger():
            get_logger().log_tool_call("execute", {"command": command}, {"error": error_msg}, duration_ms)
        return error_msg


# =============================================================================
# 自定义工具：submit_mdt_report (带基础引用验证)
# =============================================================================

@tool
def submit_mdt_report(patient_id: str, report_content: str) -> str:
    """Submit the final MDT report after Evidence Auditor approval.

    In v6.0, primary citation validation is handled by the evidence-auditor SubAgent.
    This tool performs a final structural check and saves the report.

    Args:
        patient_id: Patient identifier
        report_content: The complete 9-module MDT report content

    Returns:
        Submission result message
    """
    start_time = time.time()

    if get_logger():
        get_logger().log_tool_call(
            "submit_mdt_report",
            {"patient_id": patient_id, "report_length": len(report_content)},
            None, 0
        )

    # Structural validation: check all 9 modules are present
    required_modules = [
        "Module 0", "Module 1", "Module 2", "Module 3",
        "Module 4", "Module 5", "Module 6", "Module 7", "Module 8"
    ]
    missing_modules = [m for m in required_modules if m not in report_content]
    if missing_modules:
        return (
            f"❌ SUBMISSION BLOCKED: Missing modules: {missing_modules}. "
            f"All 9 modules (0-8) must be present in the final report."
        )

    # Check for AUDIT_WARNING flag
    if "[AUDIT WARNING]" in report_content:
        print("⚠️  [提醒] 报告包含审计警告标记，建议人工复核后存档")

    # Save report
    patient_dir = os.path.join(SANDBOX_DIR, "patients", patient_id, "reports")
    os.makedirs(patient_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(patient_dir, f"MDT_Report_{patient_id}_{timestamp}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    duration_ms = int((time.time() - start_time) * 1000)

    result_msg = f"✅ REPORT SUBMITTED SUCCESSFULLY (v6.0 Hierarchical MDT)\nPath: {file_path}"
    if get_logger():
        get_logger().log_tool_call(
            "submit_mdt_report",
            {"patient_id": patient_id},
            {"status": "success", "file_path": file_path},
            duration_ms
        )

    return result_msg


# =============================================================================
# Backend 工厂
# =============================================================================

def make_backend(runtime):
    """CompositeBackend: sandbox(default) + skills(read-only) + memories(persistent)"""
    return CompositeBackend(
        default=FilesystemBackend(root_dir=SANDBOX_DIR, virtual_mode=True),
        routes={
            "/skills/": FilesystemBackend(root_dir=SKILLS_DIR, virtual_mode=True),
            "/memories/": StoreBackend(runtime)
        }
    )


# =============================================================================
# 核心工具集（SubAgent 共享）
# =============================================================================

CORE_TOOLS = [execute, read_file, analyze_image]


# =============================================================================
# v6.0 SubAgent 定义
# =============================================================================

neurosurgery_sa = {
    "name": "neurosurgery-specialist",
    "description": (
        "Neurosurgery specialist for brain metastases MDT. "
        "Evaluates surgical indications, craniotomy vs biopsy, eloquent area risk. "
        "MUST query perioperative_safety_skill for drug holding windows. "
        "MUST query drug_interaction_skill for concomitant medication checks. "
        "Returns structured JSON + narrative with physical citations."
    ),
    "system_prompt": NEUROSURGERY_SYSTEM_PROMPT,
    "tools": CORE_TOOLS,
    "skills": NEUROSURGERY_SKILLS,   # core + perioperative_safety + drug_interaction
    "model": SUBAGENT_MODEL_NAME,
}

radiation_sa = {
    "name": "radiation-oncology-specialist",
    "description": (
        "Radiation oncology specialist for brain metastases MDT. "
        "Determines SRS vs WBRT indications from guideline PDF. "
        "ALL Gy values MUST be dual-track verified (text + VLM visual). "
        "Assesses radionecrosis risk and systemic therapy timing. "
        "Returns structured JSON + narrative."
    ),
    "system_prompt": RADIATION_SYSTEM_PROMPT,
    "tools": CORE_TOOLS,
    "skills": RADIATION_SKILLS,   # core only (pdf-inspector + pubmed)
    "model": SUBAGENT_MODEL_NAME,
}

medical_oncology_sa = {
    "name": "medical-oncology-specialist",
    "description": (
        "Medical oncology specialist for brain metastases MDT. "
        "Recommends systemic therapy (targeted/IO/chemo), determines treatment line, "
        "assesses drug doses and CNS penetration. "
        "MUST query OncoKB FIRST for targeted therapy evidence levels. "
        "MUST query cns_drug_db for CNS penetration metrics (no LLM memory). "
        "MUST query drug_interaction_skill for polypharmacy checks. "
        "Returns structured JSON + narrative."
    ),
    "system_prompt": MEDICAL_ONCOLOGY_SYSTEM_PROMPT,
    "tools": CORE_TOOLS,
    "skills": MEDICAL_ONCOLOGY_SKILLS,  # core + oncokb + cns_db + drug_interaction
    "model": SUBAGENT_MODEL_NAME,
}

molecular_pathology_sa = {
    "name": "molecular-pathology-specialist",
    "description": (
        "Molecular pathology specialist for brain metastases MDT. "
        "Interprets molecular profiling results (NGS, IHC, FISH). "
        "MUST query OncoKB for REAL-TIME evidence levels (not LLM memory). "
        "Recommends additional tests (Emergency/Routine/Exploratory priority). "
        "Identifies molecular contraindications (e.g., KRAS → anti-EGFR forbidden). "
        "Returns structured JSON + narrative."
    ),
    "system_prompt": MOLECULAR_PATHOLOGY_SYSTEM_PROMPT,
    "tools": CORE_TOOLS,
    "skills": MOLECULAR_PATHOLOGY_SKILLS,  # core + oncokb
    "model": SUBAGENT_MODEL_NAME,
}

evidence_auditor_sa = {
    "name": "evidence-auditor",
    "description": (
        "Evidence auditor for the MDT report. "
        "ONLY call AFTER the full 9-module MDT draft is complete. "
        "Verifies ALL citations: [Local:] via grep, [PubMed:] via search_pubmed, "
        "[OncoKB:] via query_oncokb. "
        "Checks dual-track verification coverage for ALL dose parameters. "
        "Computes EGR (Evidence Grounding Rate). "
        "Returns AuditorOutput JSON. pass_threshold=False → Orchestrator MUST revise."
    ),
    "system_prompt": AUDITOR_SYSTEM_PROMPT,
    "tools": CORE_TOOLS,
    "skills": AUDITOR_SKILLS,  # core only (pdf-inspector + pubmed)
    "model": SUBAGENT_MODEL_NAME,
}


# =============================================================================
# 组装 Orchestrator Deep Agent (v6.0)
# =============================================================================

print(f"🚀 正在初始化天坛医疗大脑 v6.0 (Hierarchical Agentic MDT)...")
print(f"   架构     ：Orchestrator + 5 SubAgents")
print(f"   模型     ：{SUBAGENT_MODEL_NAME} (统一)")
print(f"   SubAgents：神外 / 放疗 / 内科 / 分子病理 / Evidence Auditor")
print(f"   EGR阈值  ：{AUDITOR_EGR_THRESHOLD} (最大重试 {AUDITOR_MAX_RETRY} 次)")
print(f"   Sandbox  ：{SANDBOX_DIR}")

store = InMemoryStore()
checkpointer = MemorySaver()

agent = create_deep_agent(
    model=model,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    tools=[submit_mdt_report],          # Orchestrator 只持有提交工具
    subagents=[
        neurosurgery_sa,
        radiation_sa,
        medical_oncology_sa,
        molecular_pathology_sa,
        evidence_auditor_sa,
    ],
    skills=ORCHESTRATOR_SKILLS,         # 报告模板 + 预后评分
    backend=make_backend,
    store=store,
    checkpointer=checkpointer,
    interrupt_on={
        "submit_mdt_report": False,     # 自动提交（已经有 Auditor 关卡）
    },
    name="mdt-orchestrator",
)


# =============================================================================
# 主循环
# =============================================================================

if __name__ == "__main__":
    patient_thread_id = str(uuid.uuid4())
    execution_logger = ExecutionLogger(patient_thread_id)

    print(f"\n✅ 天坛医疗大脑 v6.0 已就绪。Session ID: {patient_thread_id}")
    print(f"📝 执行日志: {execution_logger.main_log_path}")
    print(f"💡 输入患者病史或文件路径（如 patient_868183_input.txt）开始会诊")
    print(f"💡 输入 exit 退出")
    print("-" * 60)

    while True:
        try:
            print("\n🧑‍⚕️ 请输入患者信息（输入空行结束，输入 exit 退出）：")
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

            # 文件路径自动读取
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
                    os.path.join(PROJECT_ROOT, potential_path),
                    os.path.join(PROJECT_ROOT, "patient_input", "Set-1", potential_path),
                    os.path.join(PROJECT_ROOT, "patient_input", "Set-2，0402", potential_path),
                ]
                for path in paths_to_try:
                    if os.path.isfile(path) or os.path.isfile(f"{path}.txt"):
                        actual_path = path if os.path.isfile(path) else f"{path}.txt"
                        print(f"📄 检测到文件路径，正在读取: {actual_path}")
                        try:
                            with open(actual_path, 'r', encoding='utf-8') as f:
                                user_input = f.read()
                            print(f"✅ 已读取文件，{len(user_input)} 字符")
                            file_read_success = True
                            break
                        except Exception as e:
                            print(f"⚠️  读取失败: {e}")
                if file_read_success:
                    break

            # 提取患者ID
            patient_id = None
            patient_match = re.search(r'住院号\s*(\d+)', user_input)
            if patient_match:
                patient_id = patient_match.group(1)

            execution_logger.log_user_input(user_input, patient_id)
            if patient_id:
                execution_logger.set_patient_id(patient_id)

            print(f"\n⏳ MDT Orchestrator 正在协调多专科会诊... (Patient ID: {patient_id or 'N/A'})")
            print(f"   → 并行委派给: 神外 | 放疗 | 内科 | 分子病理")
            print(f"   → 合成后经 Evidence Auditor 审计 (EGR ≥ {AUDITOR_EGR_THRESHOLD})")

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

                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        tool_name = tc.get('name', 'unknown')
                        tool_args = tc.get('args', {})
                        # 区分 Orchestrator 的 task() 调用（委派事件）
                        if tool_name == "task":
                            sa_name = tool_args.get('name', '?')
                            print(f"\n🔀  [委派] → {sa_name}")
                        else:
                            print(f"\n⚙️  [工具] {tool_name}")
                        execution_logger.log_tool_call(tool_name, tool_args, None, 0)

                content = getattr(last_msg, 'content', '')
                if content:
                    print(f"\n🤖 Agent:\n{content}")
                    usage = {}
                    if hasattr(last_msg, 'response_metadata') and last_msg.response_metadata:
                        token_usage = last_msg.response_metadata.get('token_usage', {})
                        if token_usage:
                            usage = {
                                "input_tokens": token_usage.get('prompt_tokens', 0),
                                "output_tokens": token_usage.get('completion_tokens', 0),
                                "total_tokens": token_usage.get('total_tokens', 0)
                            }
                    execution_logger.log_llm_response(content, role="assistant",
                                                      model=SUBAGENT_MODEL_NAME, usage=usage)

                if hasattr(last_msg, 'additional_kwargs') and \
                   'reasoning_content' in last_msg.additional_kwargs:
                    reasoning = last_msg.additional_kwargs['reasoning_content']
                    if reasoning:
                        print(f"\n🧠 [深度思考]:\n{reasoning}")
                        execution_logger.log_agent_thinking(reasoning, "reasoning")

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
