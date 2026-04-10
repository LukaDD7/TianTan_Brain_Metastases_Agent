#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量患者数据处理器
Batch Patient Data Processor

批量处理所有患者的输入数据，生成干净的输入文件。

使用:
    python batch_process.py
    python batch_process.py --excel ../workspace/test_cases_wide.xlsx --output ../workspace/sandbox/
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skills.patient_data_processor.scripts.patient_data_processor import PatientDataProcessor


def main():
    parser = argparse.ArgumentParser(
        description='批量处理患者输入数据（清理敏感字段）'
    )
    parser.add_argument(
        '--excel',
        default=str(PROJECT_ROOT / 'workspace' / 'test_cases_wide.xlsx'),
        help='Excel源文件路径'
    )
    parser.add_argument(
        '--output-dir',
        default=str(PROJECT_ROOT / 'workspace' / 'sandbox'),
        help='输出目录'
    )
    parser.add_argument(
        '--patients',
        help='指定患者ID列表（逗号分隔，如：640880,708387,747724）'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='仅验证现有输入文件，不重新生成'
    )

    args = parser.parse_args()

    print("="*80)
    print("  批量患者数据处理器")
    print("  Batch Patient Data Processor v1.0")
    print("="*80)
    print(f"\n数据源: {args.excel}")
    print(f"输出目录: {args.output_dir}")

    if args.validate_only:
        print("\n模式: 仅验证现有文件")
        _validate_existing_files(args.output_dir, args.excel)
        return

    # 初始化处理器
    processor = PatientDataProcessor(args.excel)

    # 确定患者列表
    if args.patients:
        patient_ids = [p.strip() for p in args.patients.split(',')]
        print(f"指定患者: {patient_ids}")
    else:
        patient_ids = None
        print(f"处理全部 {len(processor.df)} 例患者")

    # 执行批量处理
    results = processor.batch_process(args.output_dir, patient_ids)

    # 生成报告
    report = processor.generate_report(results)
    report_path = Path(args.output_dir) / f"batch_processing_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md"

    import pandas as pd  # 用于时间戳
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n详细报告: {report_path}")

    # 打印关键统计
    success = sum(1 for r in results if r.success)
    with_warnings = sum(1 for r in results if r.warnings)

    print("\n" + "="*80)
    print(f"  处理完成: {success}/{len(results)} 成功")
    print(f"  警告: {with_warnings} 例需要人工复核")
    print("="*80)

    # 返回退出码
    if success == len(results) and with_warnings == 0:
        print("\n✅ 全部清理完成，无警告")
        sys.exit(0)
    elif success == len(results):
        print("\n⚠️ 全部清理完成，但有警告需要复核")
        sys.exit(0)
    else:
        print("\n❌ 部分处理失败")
        sys.exit(1)


def _validate_existing_files(output_dir: str, excel_path: str):
    """验证现有输入文件"""
    import pandas as pd
    from pathlib import Path

    output_dir = Path(output_dir)
    processor = PatientDataProcessor(excel_path)

    # 查找所有patient_*.txt文件
    input_files = list(output_dir.glob("patient_*_input.txt"))

    if not input_files:
        print("\n未找到输入文件")
        return

    print(f"\n找到 {len(input_files)} 个输入文件")
    print("-"*80)

    violations_found = []
    clean_files = []

    for file_path in sorted(input_files):
        result = processor.validate_input_file(str(file_path))

        patient_id = file_path.stem.replace('patient_', '').replace('_input', '')

        if result.is_valid and not result.warnings:
            print(f"✅ {patient_id}: 干净")
            clean_files.append(patient_id)
        elif result.is_valid:
            print(f"⚠️  {patient_id}: 通过但有警告")
            for w in result.warnings[:3]:
                print(f"   - {w}")
        else:
            print(f"❌ {patient_id}: 验证失败")
            for v in result.violations:
                print(f"   - {v}")
            violations_found.append((patient_id, result.violations))

    print("-"*80)
    print(f"\n统计:")
    print(f"  干净文件: {len(clean_files)}")
    print(f"  污染文件: {len(violations_found)}")

    if violations_found:
        print("\n❌ 发现污染文件，需要重新处理:")
        for pid, violations in violations_found:
            print(f"\n  患者 {pid}:")
            for v in violations:
                print(f"    - {v}")


if __name__ == "__main__":
    main()
