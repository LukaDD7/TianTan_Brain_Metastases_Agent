#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import uuid

# 引入 deepagents 核心构件
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from tools.shell_tool import execute_shell_command
from utils.llm_factory import get_brain_client_langchain

# --- 1. 严格锁定工作区 (Sandbox Isolation) ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CASES_DIR = os.path.join(PROJECT_ROOT, "workspace", "cases")
TEMP_DIR = os.path.join(PROJECT_ROOT, "workspace", "temp")
os.makedirs(CASES_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# 注入医疗伦理潜意识
MEDICAL_PROTOCOL_PATH = os.path.join(PROJECT_ROOT, "MEDICAL_PROTOCOL.md")
if not os.path.exists(MEDICAL_PROTOCOL_PATH):
    with open(MEDICAL_PROTOCOL_PATH, "w", encoding="utf-8") as f:
        f.write("# 脑转移诊疗 Agent 行医规范\n1. 治疗建议必须严格基于循证医学指南。\n2. 涉及药物剂量、放疗靶区必须精准具体。")

# --- 2. 唤醒大模型 ---
try:
    print("🧠 正在连接医疗大脑 (qwen3-max 深度思考模式)...")
    model = get_brain_client_langchain()
except Exception as e:
    print(f"❌ 大脑初始化失败: {e}")
    sys.exit(1)

# --- 3. 宪法 (System Prompt) ---
system_prompt = f"""
You are the **Lead AI Oncologist** handling Solid Tumors with Brain Metastases.
Your Sandbox is strictly: `{PROJECT_ROOT}`

**🛠️ YOUR SKILLS (Agent-Computer Interface):**
You must read the `README.md` inside each skill directory before using it via `execute_shell_command`.
Available Skills:
1. `skills/pdf_inspector`: Parse PDF guidelines or EHRs.
2. `skills/clinical_writer`: Validate and compile your final MDT report.

**⚡ CLINICAL WORKFLOW:**
1. Analyze the patient's symptoms or history provided by the human doctor.
2. If needed, use `execute_shell_command` to list PDF files in the guidelines dataset and read them using `pdf_inspector`.
3. **CRITICAL FINAL STEP**: You MUST output your final treatment plan using the `clinical_writer` skill. Write your draft to a text file first, then run the validation script as instructed in its README.

**🔒 SAFETY PROTOCOL:**
Never guess drug doses. Always rely on the exact text extracted from the guidelines.
"""

# --- 4. 组装 Deep Agent ---
print(f"🚀 初始化完成，沙盒环境已隔离至: {CASES_DIR}")
backend = FilesystemBackend(root_dir=PROJECT_ROOT)
checkpointer = MemorySaver()

agent = create_deep_agent(
    model=model,
    system_prompt=system_prompt,
    skills=["skills/pdf_inspector", "skills/clinical_writer"],
    tools=[execute_shell_command],
    memory=["MEDICAL_PROTOCOL.md"], 
    backend=backend,                
    checkpointer=checkpointer,      
    # interrupt_on={"write_file": True} # HITL 拦截机制
)

if __name__ == "__main__":
    patient_thread_id = str(uuid.uuid4())
    print(f"\n✅ AI 主治医师已就绪。Session ID: {patient_thread_id}")
    print("💡 提示：您可以直接粘贴患者的特征描述，要求 AI 出具方案。")

    while True:
        try:
            user_input = input("\n🧑‍⚕️ 人类医生: ")
            if user_input.lower() in ["exit", "quit"]: break
            print("\n⏳ 思考与调度中...")

            events = agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": patient_thread_id}}
            )

            for event in events:
                for node_name, state_value in event.items():
                    messages = state_value.get("messages", []) if isinstance(state_value, dict) else (state_value.messages if hasattr(state_value, "messages") else [])
                    if not messages: continue
                    if not isinstance(messages, list): messages = [messages]
                    last_msg = messages[-1]
                    
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            print(f"\n⚙️  [{node_name}] 终端执行 -> {tc['args'].get('command', tc['args'])}")
                    elif hasattr(last_msg, 'content') and last_msg.content.strip():
                        print(f"\n🤖 [AI]: {last_msg.content}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")