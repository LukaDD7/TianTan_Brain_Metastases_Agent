import subprocess
import os
from langchain.tools import tool

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 强制指定你的医疗专属虚拟环境 Python 解释器绝对路径
MEDICAL_PYTHON_EXE = "/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python"

@tool
def execute_shell_command(command: str) -> str:
    """
    [DANGEROUS] Executes a shell command in the terminal. 
    Use this to run Python scripts found in the 'skills/' directory.
    Example: 'python skills/historical-mining/mine_events.py --date "January 29"'
    """
    if "rm " in command or "sudo" in command:
        return "Error: Forbidden command."
    
    # 🔥 核心工程修复：环境劫持 (Environment Hijacking)
    # 如果 Agent 试图调用 python，强制替换为虚拟环境的绝对路径
    if command.strip().startswith("python "):
        command = command.replace("python ", f"{MEDICAL_PYTHON_EXE} ", 1)
    
    try:
        # 为了更彻底地传递 Conda 环境，我们在环境变量中强行加入
        env = os.environ.copy()
        env["PATH"] = f"/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin:{env.get('PATH', '')}"
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '../')),
            timeout=300,
            env=env  # 注入净化后的环境变量
        )
        
        if result.returncode == 0:
            stdout = result.stdout
            if len(stdout) > 5000:
                stdout = stdout[:5000] + "\n...[Output Truncated]..."
            return f"STDOUT:\n{stdout}"
        else:
            return f"STDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 300 seconds."
    except Exception as e:
        return f"Execution Error: {e}"