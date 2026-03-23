import os

# --- 1. THE BRAIN (Tongyi Qwen3-Max) ---
BRAIN_MODEL_NAME = "qwen3.5-plus" # 阿里云最新最强推理模型
BRAIN_API_KEY = os.getenv("DASHSCOPE_API_KEY") 
BRAIN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# --- 2. THE EYES (Tongyi Qwen-VL) ---
VLM_MODEL_NAME = "qwen3.5-plus" # 处理复杂的 NCCN 临床指南流程图，建议用 max
VLM_API_KEY = os.getenv("DASHSCOPE_API_KEY") 
VLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 新增：医疗 Agent 专属虚拟环境路径
MEDICAL_PYTHON_PATH = "/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python"