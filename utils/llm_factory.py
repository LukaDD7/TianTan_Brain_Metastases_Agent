import os
import sys
# 引入 LangChain 的封装，因为 DeepAgents 需要 LangChain 对象，而不是纯 OpenAI client
from langchain_openai import ChatOpenAI 
from openai import OpenAI # 保留原生 Client 给 VLM 用

# 动态加载根目录 config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def get_brain_client_langchain():
    """
    [Orchestrator] 获取支持思考模式的 LangChain 对象（enable_thinking=True）
    用于复杂推理任务（仲裁、报告合成、多阶段规划）
    """
    if not config.BRAIN_API_KEY:
        raise ValueError("❌ MISSING: DASHSCOPE_API_KEY in env.")

    return ChatOpenAI(
        model=config.BRAIN_MODEL_NAME,
        api_key=config.BRAIN_API_KEY,
        base_url=config.BRAIN_BASE_URL,
        temperature=0.6,
        extra_body={
            "enable_thinking": True
        },
    )


def get_subagent_client_langchain():
    """
    [SubAgent] SubAgent 专用 LangChain 对象（关闭思考模式）

    SubAgent 需要结构化输出（response_format: Pydantic Schema），
    DashScope 的 enable_thinking 模式与 tool_choice=required 互斥，
    因此 SubAgent 必须显式设置 enable_thinking=False。
    """
    if not config.BRAIN_API_KEY:
        raise ValueError("❌ MISSING: DASHSCOPE_API_KEY in env.")

    return ChatOpenAI(
        model=config.SUBAGENT_MODEL_NAME,
        api_key=config.BRAIN_API_KEY,
        base_url=config.BRAIN_BASE_URL,
        temperature=0.3,
        extra_body={
            "enable_thinking": False,  # 必须显式关闭，DashScope 结构化输出要求
        },
    )

def get_vlm_client():
    """
    [Vision Tool] 获取 Qwen-VL 的原生 Client (用于 vlm_wrapper)
    """
    if not config.VLM_API_KEY:
        key = config.VLM_API_KEY or os.getenv("OPENAI_API_KEY")
        if not key:
             raise ValueError("❌ MISSING: DASHSCOPE_API_KEY (for Qwen-VL).")
        return OpenAI(api_key=key, base_url=config.VLM_BASE_URL)
    
    return OpenAI(
        api_key=config.VLM_API_KEY,
        base_url=config.VLM_BASE_URL
    )