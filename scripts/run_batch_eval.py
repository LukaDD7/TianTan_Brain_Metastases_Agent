#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量评估脚本 (Batch Evaluation Script) - V3 三层架构版

运行：conda run -n tiantanBM_agent python scripts/run_batch_eval.py --max_cases 1
"""

from __future__ import print_function

import os
import pandas as pd
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# 项目根目录
PROJECT_ROOT = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent"
sys.path.insert(0, PROJECT_ROOT)

# 绝对路径配置
WORKSPACE_DIR = Path(PROJECT_ROOT) / "workspace"
CASES_DIR = WORKSPACE_DIR / "cases"
OUTPUT_DIR = WORKSPACE_DIR / "eval_results"
INPUT_EXCEL = WORKSPACE_DIR / "test_cases_wide.xlsx"
GUIDELINES_DIR = Path(PROJECT_ROOT) / "Guidelines" / "脑转诊疗指南"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "=" * 80)
print("  [HC] 环境配置 - 绝对路径确认")
print("=" * 80)
print("  PROJECT_ROOT: %s" % PROJECT_ROOT)
print("  INPUT_EXCEL:  %s" % INPUT_EXCEL)
print("  OUTPUT_DIR:   %s" % OUTPUT_DIR)
print("  GUIDELINES:   %s" % GUIDELINES_DIR)
print("=" * 80 + "\n")


def build_patient_data(row, gene_symbol: Optional[str], gene_variant: Optional[str]) -> Dict[str, Any]:
    """从 Excel 行构建患者数据字典"""
    patient_data = {
        "chief_complaint": "脑转移",
        "tumor_type": "",
        "gene_variants": [],
        "prior_treatments": [],
        "question": "请提供脑转移诊疗的多学科会诊意见"
    }

    # 提取肿瘤类型
    diagnosis_fields = ["出院诊断", "入院诊断", "病理诊断"]
    for field in diagnosis_fields:
        val = row.get(field)
        if pd.notna(val):
            diagnosis_text = str(val)
            if "黑色素" in diagnosis_text:
                patient_data["tumor_type"] = "黑色素瘤"
                break
            elif "肺" in diagnosis_text:
                patient_data["tumor_type"] = "肺癌"
                break

    # 基因信息
    if gene_symbol and gene_variant:
        patient_data["gene_variants"] = [{"gene": gene_symbol, "variant": gene_variant}]

    # 既往治疗
    prior_tx = row.get("既往治疗", "")
    if pd.notna(prior_tx) and str(prior_tx).strip():
        patient_data["prior_treatments"] = [str(prior_tx)]

    return patient_data


def run_real_workflow(
    case_id: str,
    patient_data: Dict[str, Any],
    model_name: str = "qwen3.5-plus"
) -> Dict[str, Any]:
    """
    真实调用 main_oncology_agent_v3.py (三层架构)

    Args:
        case_id: 病例 ID
        patient_data: 患者数据字典
        model_name: 模型名称

    Returns:
        执行结果
    """
    print("\n" + "=" * 80)
    print("  [W] 真实调用 main_oncology_agent_v3.py 主控大脑 (三层架构)")
    print("=" * 80)

    # 读取配置
    try:
        import config
        print("  [M] 使用模型：%s" % (model_name or config.BRAIN_MODEL_NAME))
        print("  [M] API Key 已配置：%s" % ("是" if getattr(config, 'BRAIN_API_KEY', None) else "否"))
    except ImportError:
        print("  [W] config 模块未找到，使用默认模型")

    # 导入 v3 主工作流
    from main_oncology_agent_v3 import run_mdt_consultation

    print("\n  [I] 准备调用 MDT 会诊...")
    print("     患者肿瘤类型：%s" % patient_data.get("tumor_type", "未知"))
    print("     基因变异：%s" % patient_data.get("gene_variants", []))

    start_time = time.time()

    try:
        # 调用 v3 入口函数
        result = run_mdt_consultation(
            patient_data=patient_data,
            sandbox_root=str(WORKSPACE_DIR / "sandbox"),
            model=model_name or "qwen3.5-plus"
        )

        elapsed_time = time.time() - start_time
        print("\n  [T] 工作流执行完成，耗时：%.2f 秒" % elapsed_time)

        return {"success": True, "elapsed_time": elapsed_time, "result": result}

    except Exception as e:
        elapsed_time = time.time() - start_time
        print("\n  [X] 工作流执行失败：%s" % str(e))
        import traceback
        traceback.print_exc()

        return {"success": False, "elapsed_time": elapsed_time, "error": str(e)}


def run_batch_evaluation(input_excel: str, output_dir: str, max_cases: int = 1):
    """运行批量评估"""
    import pandas as pd

    print("\n" + "=" * 80)
    print("  [H] TianTan Brain Metastases Agent V3 - 真实调用批量评估")
    print("  三层架构 | 双 Subagent 协同 | Actor-Critic 审查")
    print("=" * 80 + "\n")

    try:
        df = pd.read_excel(input_excel)
        print("  [OK] 读取测试数据：%d 行" % len(df))
    except Exception as e:
        print("  [X] 读取 Excel 失败：%s" % e)
        return False

    all_eval_results = []
    cases_to_test = min(max_cases, len(df))
    print("  [I] 计划测试 %d 个病例...\n" % cases_to_test)

    # 尝试读取 config 获取模型名
    try:
        import config
        model_name = getattr(config, 'BRAIN_MODEL_NAME', 'qwen3.5-plus')
    except ImportError:
        model_name = 'qwen3.5-plus'

    for idx in range(cases_to_test):
        row = df.iloc[idx]
        case_id = row.get("id", "Case%d" % (idx + 1))

        print("\n" + "=" * 80)
        print("  Case %d/%d: %s" % (idx + 1, cases_to_test, case_id))
        print("=" * 80)

        start_time = time.time()

        # 提取基因信息
        gene_symbol = None
        gene_variant = None
        expected_gene = row.get("expected_gene")
        expected_variant = row.get("expected_variant")

        if pd.notna(expected_gene) and pd.notna(expected_variant):
            gene_symbol = str(expected_gene)
            gene_variant = str(expected_variant)
            print("\n  [G] 基因信息：%s %s" % (gene_symbol, gene_variant))

        # 构建患者数据
        print("\n  [P] 构建患者数据...")
        patient_data = build_patient_data(row, gene_symbol, gene_variant)
        print("     肿瘤类型：%s" % patient_data.get("tumor_type"))
        print("     基因变异：%s" % patient_data.get("gene_variants"))

        # 真实调用
        workflow_result = run_real_workflow(
            case_id=case_id,
            patient_data=patient_data,
            model_name=model_name
        )

        elapsed_time = time.time() - start_time

        # 严格判定
        print("\n" + "=" * 80)
        print("  [E] 严格判定结果")
        print("=" * 80)

        workflow_success = workflow_result.get("success", False)

        if not workflow_success:
            overall_pass = False
            report_path = "FAILED"
            failure_reason = workflow_result.get("error", "Unknown")
            print("  [X] 工作流执行失败：%s" % failure_reason)
        else:
            # 查找报告 (在 sandbox 目录中)
            sandbox_dir = WORKSPACE_DIR / "sandbox"
            report_path = "FAILED"

            if sandbox_dir.exists():
                report_files = list(sandbox_dir.glob("mdt_consultation_*.md"))
                if report_files:
                    report_path = str(sorted(report_files)[-1])
                    print("  [OK] 报告已生成：%s" % report_path)

                    # 验证报告内容
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_content = f.read()

                    checks = {
                        "has_admission_evaluation": "admission_evaluation" in report_content.lower() or "入院评估" in report_content,
                        "has_primary_plan": "primary_plan" in report_content.lower() or "首选方案" in report_content,
                        "has_rejected_alternatives": "rejected_alternatives" in report_content.lower() or "排他性" in report_content or "被否决" in report_content,
                        "has_peri_procedural": "peri_procedural" in report_content.lower() or "围手术期" in report_content or "停药" in report_content,
                        "has_citation_format": "[Citation:" in report_content,
                        "no_forbidden_words": "术前准备" not in report_content
                    }

                    print("\n  [CHECK] 报告内容检查:")
                    for check_name, passed in checks.items():
                        status = "[OK]" if passed else "[X]"
                        print("    %s %s: %s" % (status, check_name, passed))

                    overall_pass = all(checks.values())
                    if not overall_pass:
                        report_path = "FAILED"
                        print("  [X] 报告内容检查未通过")
                else:
                    print("  [X] 未找到生成的报告文件")
                    overall_pass = False
            else:
                print("  [X] Sandbox 目录不存在")
                overall_pass = False

        status = "[OK] PASS" if overall_pass else "[X] FAIL"
        print("\n  %s 整体判定" % status)

        full_result = {
            "case_id": case_id,
            "overall_pass": overall_pass,
            "report_path": report_path,
            "elapsed_time_sec": round(elapsed_time, 2),
            "workflow_success": workflow_success,
            "timestamp": datetime.now().isoformat()
        }

        all_eval_results.append(full_result)
        print("\n  [T] 耗时：%.2f 秒" % elapsed_time)

    # 汇总
    print("\n" + "=" * 80)
    print("  [S] 批量评估完成")
    print("=" * 80 + "\n")

    total_cases = len(all_eval_results)
    passed_cases = sum(1 for r in all_eval_results if r["overall_pass"])
    pass_rate = (passed_cases / total_cases * 100) if total_cases > 0 else 0

    print("  总计：%d 个 Case" % total_cases)
    print("  通过：%d 个 (%.1f%%)" % (passed_cases, pass_rate))
    print("  失败：%d 个" % (total_cases - passed_cases))

    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_csv = OUTPUT_DIR / ("batch_eval_v3_%s.csv" % timestamp_str)

    df_results = pd.DataFrame(all_eval_results)
    df_results.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print("\n  [D] 评估结果已保存：%s" % output_csv)

    print("\n  详细结果：")
    for result in all_eval_results:
        status = "[OK]" if result["overall_pass"] else "[X]"
        print("    %s %s: %s" % (status, result['case_id'], result['report_path']))

    return True


def main():
    parser = argparse.ArgumentParser(description="TianTan Brain Metastases Agent V3 - 真实调用")
    parser.add_argument("--input", default=str(INPUT_EXCEL))
    parser.add_argument("--output", default=str(OUTPUT_DIR))
    parser.add_argument("--max_cases", type=int, default=1)

    args = parser.parse_args()

    success = run_batch_evaluation(args.input, args.output, args.max_cases)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
