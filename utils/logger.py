import logging
import os
from datetime import datetime

os.makedirs("workspace/logs", exist_ok=True)

def setup_logger(name="MedicalAgent"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # 文件日志：详细记录，用于复盘和审计
        log_file = f"workspace/logs/agent_run_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
        
        # 控制台日志：仅输出关键信息
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('🤖 %(message)s'))
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logger()