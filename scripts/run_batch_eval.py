#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量评估脚本 (Batch Evaluation Script) - 真实调用版

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


def build_raw_clinical_text(row) -> str:
    """从 Excel 行构建完整的原始临床病历文本"""
    fields = []

    field_names = [
        "主诉", "现病史", "入院诊断", "出院诊断",
        "头部MRI", "胸部CT", "腰椎MRI", "腹盆CT", "颈椎MRI",
        "既往史", "诊疗经过", "病理诊断", "年龄", "性别", "住院号", "入院时间", "出院时间"
    ]

    for field in field_names:
        val = row.get(field)
        if pd.notna(val) and str(val).strip():
            fields.append("【%s】\n%s" % (field, val))

    return "\n\n".join(fields)


def save_text_as_pdf(raw_text: str, case_id: str, output_dir: Path) -> Path:
    """将原始临床文本转换为 PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch

    case_dir = output_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = case_dir / "patient_record_raw.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # 分段添加
    lines = raw_text.split('\n')
    for line in lines:
        if line.strip():
            p = Paragraph(line, styles['Normal'])
            story.append(p)
            story.append(Spacer(1, 0.05 * inch))

    doc.build(story)
    print("  [D] 原始病历已转换为 PDF: %s" % pdf_path)
    return pdf_path


def select_guideline_for_tumor_type(row) -> str:
    """根据病历中的肿瘤类型选择合适的指南"""
    diagnosis_fields = ["出院诊断", "入院诊断", "病理诊断", "既往史"]
    diagnosis_text = ""

    for field in diagnosis_fields:
        val = row.get(field)
        if pd.notna(val):
            diagnosis_text += str(val) + " "

    # 黑色素瘤优先
    if "黑色素" in diagnosis_text:
        for pdf in GUIDELINES_DIR.rglob("*.pdf"):
            if "EANO" in pdf.name:
                return str(pdf)

    # 默认选择第一个指南
    pdfs = list(GUIDELINES_DIR.rglob("*.pdf"))
    if pdfs:
        return str(pdfs[0])

    raise RuntimeError("未找到任何指南文件")


def run_real_workflow(case_id: str, patient_pdf_path: str, guideline_path: str,
                       gene_symbol: Optional[str], gene_variant: Optional[str]) -> Dict[str, Any]:
    """真实调用 main_oncology_agent_v2.py"""
    print("\n" + "=" * 80)
    print("  [W] 真实调用 main_oncology_agent_v2.py 主控大脑")
    print("=" * 80)

    # 读取配置
    import config
    print("  [M] 使用模型: %s" % config.BRAIN_MODEL_NAME)
    print("  [M] API Key 已配置: %s" % ("是" if config.BRAIN_API_KEY else "否"))

    # 导入主工作流
    from main_oncology_agent_v2 import run_full_workflow

    print("\n  [I] 准备调用工作流...")
    print("     患者病历: %s" % patient_pdf_path)
    print("     指南文件: %s" % guideline_path)

    start_time = time.time()

    try:
        result = run_full_workflow(
            case_id=case_id,
            patient_pdf_path=patient_pdf_path,
            guideline_pdf_path=guideline_path,
            gene_symbol=gene_symbol,
            gene_variant=gene_variant,
            tumor_type=None,
            literature_keywords=None
        )

        elapsed_time = time.time() - start_time
        print("\n  [T] 工作流执行完成，耗时: %.2f 秒" % elapsed_time)

        return {"success": True, "elapsed_time": elapsed_time, "result": result}

    except Exception as e:
        elapsed_time = time.time() - start_time
        print("\n  [X] 工作流执行失败: %s" % str(e))
        import traceback
        traceback.print_exc()

        return {"success": False, "elapsed_time": elapsed_time, "error": str(e)}


def run_batch_evaluation(input_excel: str, output_dir: str, max_cases: int = 1):
    """运行批量评估"""
    import pandas as pd

    print("\n" + "=" * 80)
    print("  [H] TianTan Brain Metastases Agent - 真实调用批量评估")
    print("  全量原始文本 | 真实 LLM 调用 | 严格判定")
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

    for idx in range(cases_to_test):
        row = df.iloc[idx]
        case_id = row.get("id", "Case%d" % (idx + 1))

        print("\n" + "=" * 80)
        print("  Case %d/%d: %s" % (idx + 1, cases_to_test, case_id))
        print("=" * 80)

        start_time = time.time()

        # 构建原始临床病历
        print("\n" + "=" * 80)
        print("  [P0] 构建原始临床病历文本")
        print("=" * 80)

        raw_clinical_text = build_raw_clinical_text(row)

        print("\n  [C] 【原始临床病历文本前 500 字符】")
        print("  " + "-" * 60)
        print("  %s" % raw_clinical_text[:500])
        print("  ..." if len(raw_clinical_text) > 500 else "")
        print("  总长度: %d 字符" % len(raw_clinical_text))

        # 转换为 PDF
        patient_pdf_path = save_text_as_pdf(raw_clinical_text, case_id, WORKSPACE_DIR)

        # 选择指南
        print("\n" + "=" * 80)
        print("  [P1] 选择合适的指南")
        print("=" * 80)

        try:
            guideline_path = select_guideline_for_tumor_type(row)
            print("  [OK] 选择的指南: %s" % Path(guideline_path).name)
        except Exception as e:
            print("  [X] 选择指南失败: %s" % e)
            continue

        # 提取基因信息
        gene_symbol = None
        gene_variant = None
        expected_gene = row.get("expected_gene")
        expected_variant = row.get("expected_variant")

        if pd.notna(expected_gene) and pd.notna(expected_variant):
            gene_symbol = str(expected_gene)
            gene_variant = str(expected_variant)
            print("\n  [G] 基因信息: %s %s" % (gene_symbol, gene_variant))

        # 真实调用
        workflow_result = run_real_workflow(
            case_id=case_id,
            patient_pdf_path=str(patient_pdf_path),
            guideline_path=guideline_path,
            gene_symbol=gene_symbol,
            gene_variant=gene_variant
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
            print("  [X] 工作流执行失败: %s" % failure_reason)
        else:
            # 查找报告
            case_report_dir = CASES_DIR / case_id
            report_path = "FAILED"

            if case_report_dir.exists():
                report_files = list(case_report_dir.glob("MDT_Report_*.md"))
                if report_files:
                    report_path = str(sorted(report_files)[-1])
                    print("  [OK] 报告已生成: %s" % report_path)

                    # 验证报告内容
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_content = f.read()

                    checks = {
                        "rejected_alternatives": "被排除" in report_content or "rejected_alternatives" in report_content.lower(),
                        "peri_procedural_holding": "停药" in report_content or "peri_procedural" in report_content.lower(),
                        "no_forbidden_words": "术前准备" not in report_content,
                        "has_citation": "Citation:" in report_content or "[Citation" in report_content
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
                print("  [X] 病例目录不存在")
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
    output_csv = OUTPUT_DIR / ("batch_eval_%s.csv" % timestamp_str)

    df_results = pd.DataFrame(all_eval_results)
    df_results.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print("\n  [D] 评估结果已保存：%s" % output_csv)

    print("\n  详细结果：")
    for result in all_eval_results:
        status = "[OK]" if result["overall_pass"] else "[X]"
        print("    %s %s: %s" % (status, result['case_id'], result['report_path']))

    return True


def main():
    parser = argparse.ArgumentParser(description="TianTan Brain Metastases Agent - 真实调用")
    parser.add_argument("--input", default=str(INPUT_EXCEL))
    parser.add_argument("--output", default=str(OUTPUT_DIR))
    parser.add_argument("--max_cases", type=int, default=1)

    args = parser.parse_args()

    success = run_batch_evaluation(args.input, args.output, args.max_cases)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()