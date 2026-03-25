#!/usr/bin/env python3
"""
批量运行Enhanced RAG Baseline
运行所有剩余患者样本
"""

import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.timestamp_utils import get_timestamped_filename

# 患者列表 (住院号)
PATIENTS = [
    "612908",  # Case7
    "638114",  # Case6
    "640880",  # Case2
    "648772",  # Case1
    "665548",  # Case4
    "708387",  # Case9
    "747724",  # Case10
    # 605525 (Case8) 已完成
]

def run_single_patient(patient_id):
    """运行单个患者"""
    print(f"\n{'='*80}")
    print(f"开始运行患者: {patient_id}")
    print(f"{'='*80}")

    cmd = [
        "conda", "run", "-n", "tiantanBM_agent",
        "python", "rag_baseline_enhanced.py", patient_id
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10分钟超时
            cwd="/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/baseline/rag_guideline"
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"✅ 患者 {patient_id} 运行成功")
            return True
        else:
            print(f"❌ 患者 {patient_id} 运行失败 (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️ 患者 {patient_id} 运行超时")
        return False
    except Exception as e:
        print(f"❌ 患者 {patient_id} 运行异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("Enhanced RAG Baseline 批量运行")
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"患者列表: {PATIENTS}")
    print("=" * 80)

    results = {}
    success_count = 0

    for i, patient_id in enumerate(PATIENTS, 1):
        print(f"\n进度: {i}/{len(PATIENTS)} ({i/len(PATIENTS)*100:.1f}%)")
        success = run_single_patient(patient_id)
        results[patient_id] = success
        if success:
            success_count += 1

    # 汇总报告
    print("\n" + "=" * 80)
    print("批量运行完成")
    print(f"结束时间: {datetime.now().isoformat()}")
    print(f"成功: {success_count}/{len(PATIENTS)}")
    print("=" * 80)

    print("\n运行结果:")
    for patient_id, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {patient_id}: {status}")

    # 保存汇总结果 - 使用带时间戳的文件名
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_patients": len(PATIENTS),
        "success_count": success_count,
        "results": results
    }

    output_filename = get_timestamped_filename("batch_summary", "json")
    output_path = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/baseline/results_enhanced") / output_filename
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n汇总结果已保存: {output_path}")

if __name__ == "__main__":
    main()
