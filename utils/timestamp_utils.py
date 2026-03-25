"""
时间戳命名工具模块
为项目输出文件提供统一的带时间戳命名功能
"""

from datetime import datetime
from pathlib import Path


def get_timestamp() -> str:
    """获取当前时间戳，格式: YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_timestamped_filename(base_name: str, ext: str = "", separator: str = "_") -> str:
    """
    生成带时间戳的文件名

    Args:
        base_name: 基础文件名（不含扩展名）
        ext: 文件扩展名（不含点，如 'json', 'md'）
        separator: 基础名与时间戳之间的分隔符

    Returns:
        带时间戳的文件名，如: "Case1_results_20260325_143022.json"
    """
    timestamp = get_timestamp()
    if ext:
        return f"{base_name}{separator}{timestamp}.{ext}"
    return f"{base_name}{separator}{timestamp}"


def get_timestamped_path(directory: str | Path, base_name: str, ext: str = "") -> Path:
    """
    生成带时间戳的完整路径

    Args:
        directory: 输出目录
        base_name: 基础文件名（不含扩展名）
        ext: 文件扩展名

    Returns:
        带时间戳的完整路径
    """
    return Path(directory) / get_timestamped_filename(base_name, ext)


# 预定义的命名模板
def get_rag_result_filename(patient_id: str, method: str = "enhanced") -> str:
    """生成RAG结果文件名"""
    return get_timestamped_filename(f"Case{patient_id}_{method}_rag_results", "json")


def get_mdt_report_filename(patient_id: str) -> str:
    """生成MDT报告文件名"""
    return get_timestamped_filename(f"MDT_Report_{patient_id}", "md")


def get_evaluation_filename(method: str = "enhanced") -> str:
    """生成评估结果文件名"""
    return get_timestamped_filename(f"evaluation_results_{method}", "json")


def get_batch_summary_filename() -> str:
    """生成批量运行摘要文件名"""
    return get_timestamped_filename("batch_summary", "json")


def get_analysis_report_filename(report_type: str = "analysis") -> str:
    """生成分析报告文件名"""
    return get_timestamped_filename(f"{report_type}_report", "md")


if __name__ == "__main__":
    # 测试示例
    print("时间戳示例:")
    print(f"  当前时间戳: {get_timestamp()}")
    print(f"  RAG结果: {get_rag_result_filename('123')}")
    print(f"  MDT报告: {get_mdt_report_filename('456')}")
    print(f"  评估结果: {get_evaluation_filename()}")
    print(f"  批量摘要: {get_batch_summary_filename()}")
