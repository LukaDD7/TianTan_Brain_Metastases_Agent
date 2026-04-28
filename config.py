import os

# --- 1. THE BRAIN (Tongyi Qwen3.6-Plus) ---
# v6.0 升级：qwen3.6-plus 对 Agent Harness（工具调用链、长步骤规划）有显著提升
BRAIN_MODEL_NAME = "qwen3.6-plus"
BRAIN_API_KEY = os.getenv("DASHSCOPE_API_KEY")
BRAIN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# --- 2. THE EYES (Tongyi Qwen-VL) ---
# v7.1 升级：使用专用 VLM 模型（qwen-vl-plus），成本更低，视觉能力更强
# 仅用于 Dual-Track 双轨验证中的 PDF 页面分析，不参与文本推理
VLM_MODEL_NAME = "qwen-vl-plus"   # 替代 qwen3.6-plus，专用 VLM，降低成本 50-70%
VLM_API_KEY = os.getenv("DASHSCOPE_API_KEY")
VLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# --- 3. 环境路径 ---
MEDICAL_PYTHON_PATH = "/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python"

# --- 4. v6.0 架构常量 ---
# SubAgent 模型（统一，便于消融实验中替换对比）
SUBAGENT_MODEL_NAME = "qwen3.6-plus"

# Auditor 通过阈值（EGR: Evidence Grounding Rate）
AUDITOR_EGR_THRESHOLD = 0.85
AUDITOR_MAX_RETRY = 2  # 审计不通过允许的最大修正轮次