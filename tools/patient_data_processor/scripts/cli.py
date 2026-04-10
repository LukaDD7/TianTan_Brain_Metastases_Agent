#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patient Data Processor - Command Line Interface
患者数据处理器 - 命令行接口

提供统一的命令行入口用于数据处理、验证和报告生成。
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent")
sys.path.insert(0, str(PROJECT_ROOT))

from skills.patient_data_processor.scripts.processor_core import (
    PatientDataProcessor,
    create_processor_from_default,
    ProcessingStatus,
    CheckStatus
)


def cmd_process(args):
    """处理单个患者"""
    processor = PatientDataProcessor(
        source_path=args.source,
        output_dir=args.output,
        verbose=args.verbose
    )

    result = processor.process(
        patient_id=args.patient_id,
        enable_verification=not args.skip_verification
    )

    # 输出结果
    print("\n" + "="*70)
    print("处理结果")
    print("="*70)
    print(f"患者ID: {result.patient_id}")
    print(f"状态: {result.status.value.upper()}")
    print(f"输出路径: {result.output_path}")

    if result.warnings:
        print(f"\n警告 ({len(result.warnings)} 项):")
        for w in result.warnings:
            print(f"  ⚠️  {w}")

    if result.error_message:
        print(f"\n❌ 错误: {result.error_message}")

    if result.verification_results and args.verbose:
        print(f"\n验证详情:")
        for vr in result.verification_results:
            print(f"  {vr.level.value}: {vr.status.value}")
            for check in vr.checks:
                icon = "✅" if check.status == CheckStatus.PASSED else "⚠️" if check.status == CheckStatus.WARNING else "❌"
                print(f"    {icon} {check.name}: {check.message}")

    if result.audit_record:
        print(f"\n审计记录:")
        print(f"  移除字段: {result.audit_record.removed_fields}")
        print(f"  输入哈希: {result.audit_record.input_hash[:16]}...")
        print(f"  输出哈希: {result.audit_record.output_hash[:16]}...")

    # 返回退出码
    if result.status == ProcessingStatus.FAILED:
        return 1
    return 0


def cmd_batch(args):
    """批量处理"""
    processor = PatientDataProcessor(
        source_path=args.source,
        output_dir=args.output,
        verbose=args.verbose
    )

    # 解析患者ID列表
    patient_ids = None
    if args.patients:
        patient_ids = [p.strip() for p in args.patients.split(',')]

    print("\n" + "="*70)
    print("批量患者数据处理")
    print("="*70)
    print(f"源文件: {args.source}")
    print(f"输出目录: {args.output}")
    print(f"指定患者: {patient_ids if patient_ids else '全部'}")
    print(f"验证: {'启用' if not args.skip_verification else '跳过'}")
    print("="*70)

    results = processor.batch_process(
        patient_ids=patient_ids,
        enable_verification=not args.skip_verification
    )

    # 获取解析统计信息
    parsing_stats = getattr(processor, '_parsing_stats', {})

    # 汇总统计
    success = sum(1 for r in results if r.status == ProcessingStatus.SUCCESS)
    warning = sum(1 for r in results if r.status == ProcessingStatus.WARNING)
    failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)

    print("\n" + "="*70)
    print("数据处理统计报告")
    print("="*70)
    print(f"\n📊 源数据统计:")
    print(f"   源文件Case总数:     {parsing_stats.get('source_cases', 'N/A'):>6} 例")
    print(f"   唯一住院号数:       {parsing_stats.get('unique_patients', 'N/A'):>6} 例")
    print(f"   总就诊次数:         {parsing_stats.get('total_visits', 'N/A'):>6} 次")
    print(f"   重复住院号数:       {parsing_stats.get('duplicate_count', 0):>6} 个")

    if parsing_stats.get('duplicates'):
        print(f"\n📋 重复住院号详情:")
        for base_id, info in parsing_stats['duplicates'].items():
            print(f"   - 住院号 {base_id}: {info['visit_count']}次就诊")
            print(f"     涉及Case: {', '.join(info['cases'])}")
        print(f"\n✅ 处理方式: 为重复住院号添加 _V2, _V3 等后缀保留所有就诊记录")

    print(f"\n📁 处理结果统计:")
    print(f"   处理就诊记录:       {len(results):>6} 条")
    print(f"   ✅ 成功:            {success:>6} 条")
    print(f"   ⚠️  警告:            {warning:>6} 条 (需语义审查)")
    print(f"   ❌ 失败:            {failed:>6} 条")
    print("="*70)

    # 失败详情
    if failed > 0:
        print("\n失败详情:")
        for r in results:
            if r.status == ProcessingStatus.FAILED:
                print(f"  - 患者 {r.patient_id}: {r.error_message}")

    # 报告文件位置
    report_dir = Path(args.output).parent / "processing_logs"
    print(f"\n📄 详细报告: {report_dir}/batch_report_*.json")

    return 0 if failed == 0 else 1


def cmd_verify(args):
    """验证现有文件"""
    processor = create_processor_from_default()

    print("\n" + "="*70)
    print("输入文件验证")
    print("="*70)

    result = processor.verify_existing_file(args.file)

    print(f"文件: {args.file}")
    print(f"整体状态: {result.status.value}")
    print(f"验证时间: {result.timestamp}")

    print(f"\n检查项:")
    for check in result.checks:
        icon = "✅" if check.status == CheckStatus.PASSED else "⚠️" if check.status == CheckStatus.WARNING else "❌"
        print(f"  {icon} {check.name}")
        print(f"     {check.message}")

    return 0 if result.status != CheckStatus.FAILED else 1


def cmd_inspect(args):
    """检查源数据结构"""
    import pandas as pd

    print("\n" + "="*70)
    print("源数据结构检查")
    print("="*70)
    print(f"源文件: {args.source}")

    df = pd.read_excel(args.source)

    print(f"\n基本统计:")
    print(f"  总行数: {len(df)}")
    print(f"  总列数: {len(df.columns)}")
    print(f"  列名: {list(df.columns)}")

    # 检查Feature分布
    if 'Feature' in df.columns:
        features = df['Feature'].unique()
        print(f"\nFeature类型 ({len(features)} 种):")

        # 分类显示
        allowed = [f for f in features if f in ['住院号', '入院时间', '年龄', '性别', '主诉', '现病史', '既往史', '头部MRI', '胸部CT', '颈椎MRI', '胸椎MRI', '腰椎MRI', '腹盆CT', '腹盆MRI', '腹部超声', '浅表淋巴结超声']]
        blacklist = [f for f in features if f in ['入院诊断', '出院诊断', '诊疗经过', '出院时间']]
        unknown = [f for f in features if f not in allowed and f not in blacklist]

        print(f"\n  ✅ 允许字段 ({len(allowed)} 个):")
        for f in allowed:
            count = df[df['Feature'] == f].shape[0]
            print(f"     - {f:20s} ({count} 条)")

        print(f"\n  ❌ 黑名单字段 ({len(blacklist)} 个):")
        for f in blacklist:
            count = df[df['Feature'] == f].shape[0]
            print(f"     - {f:20s} ({count} 条)")

        if unknown:
            print(f"\n  ⚠️  未知字段 ({len(unknown)} 个):")
            for f in unknown:
                count = df[df['Feature'] == f].shape[0]
                print(f"     - {f:20s} ({count} 条)")

    # 患者数量
    if 'id' in df.columns:
        case_count = df['id'].nunique()
        print(f"\nCase数量: {case_count} 例")

        # 检查住院号重复情况
        if 'Feature' in df.columns and '住院号' in df['Feature'].values:
            # 提取每个Case的住院号
            住院号_data = df[df['Feature'] == '住院号'][['id', 'Value']].drop_duplicates()
            住院号_counts = 住院号_data['Value'].value_counts()
            duplicates = 住院号_counts[住院号_counts > 1]

            if len(duplicates) > 0:
                print(f"\n⚠️  发现重复住院号: {len(duplicates)} 个")
                print(f"   涉及Case数: {sum(duplicates.values)} 例")
                print(f"\n重复详情:")
                for 住院号, count in duplicates.items():
                    cases = 住院号_data[住院号_data['Value'] == 住院号]['id'].tolist()
                    print(f"   - 住院号 {住院号}: {count}次")
                    print(f"     Case: {', '.join(cases)}")
                print(f"\n✅ 处理方式: 将为重复住院号添加 _V2, _V3 后缀区分不同就诊记录")
            else:
                print(f"\n✅ 未发现重复住院号")

    return 0


def cmd_clean(args):
    """清理现有污染文件"""
    import pandas as pd

    print("\n" + "="*70)
    print("污染文件清理")
    print("="*70)

    processor = create_processor_from_default()

    # 查找所有patient_*.txt文件
    sandbox_dir = Path(args.sandbox_dir)
    input_files = list(sandbox_dir.glob("patient_*_input.txt"))

    print(f"扫描目录: {sandbox_dir}")
    print(f"找到文件: {len(input_files)} 个")

    contaminated = []
    clean = []

    for file_path in sorted(input_files):
        result = processor.verify_existing_file(str(file_path))

        # 从文件名提取患者ID
        patient_id = file_path.stem.replace('patient_', '').replace('_input', '')

        if result.status == CheckStatus.FAILED:
            contaminated.append((patient_id, str(file_path), result))
            print(f"\n❌ 患者 {patient_id}: 污染检测")
            for check in result.checks:
                if check.status == CheckStatus.FAILED:
                    print(f"   - {check.message}")
        else:
            clean.append(patient_id)

    print("\n" + "="*70)
    print("扫描结果")
    print("="*70)
    print(f"干净文件: {len(clean)} 个")
    print(f"污染文件: {len(contaminated)} 个")

    if contaminated and args.execute:
        print("\n开始清理...")

        # 重新生成这些患者的输入文件
        for patient_id, file_path, _ in contaminated:
            print(f"\n处理患者 {patient_id}...")
            result = processor.process(patient_id, enable_verification=True)

            if result.status in [ProcessingStatus.SUCCESS, ProcessingStatus.WARNING]:
                print(f"  ✅ 已重新生成: {result.output_path}")
                # 备份原文件
                backup_dir = sandbox_dir / "input_backups" / pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / f"{Path(file_path).name}.contaminated"
                Path(file_path).rename(backup_path)
                print(f"  📦 原文件已备份: {backup_path}")
            else:
                print(f"  ❌ 处理失败: {result.error_message}")

    elif contaminated:
        print("\n⚠️  发现污染文件，但未执行清理（添加 --execute 参数执行清理）")

    return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog='patient_data_processor',
        description='患者输入数据处理器 - 医疗AI评估数据准备工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 处理单个患者
  python -m skills.patient_data_processor.cli process --patient-id 640880

  # 批量处理全部患者
  python -m skills.patient_data_processor.cli batch

  # 验证现有文件
  python -m skills.patient_data_processor.cli verify --file workspace/sandbox/patient_640880_input.txt

  # 检查源数据结构
  python -m skills.patient_data_processor.cli inspect

  # 清理污染文件（预览）
  python -m skills.patient_data_processor.cli clean

  # 清理污染文件（执行）
  python -m skills.patient_data_processor.cli clean --execute
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # process 命令
    process_parser = subparsers.add_parser('process', help='处理单个患者')
    process_parser.add_argument('--patient-id', required=True, help='患者ID（住院号）')
    process_parser.add_argument('--source', default=str(PROJECT_ROOT / 'patients_folder' / '46个病例_诊疗经过.xlsx'), help='源Excel文件路径')
    process_parser.add_argument('--output', default=str(PROJECT_ROOT / 'workspace' / 'sandbox'), help='输出目录')
    process_parser.add_argument('--skip-verification', action='store_true', help='跳过验证步骤')
    process_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    process_parser.set_defaults(func=cmd_process)

    # batch 命令
    batch_parser = subparsers.add_parser('batch', help='批量处理患者')
    batch_parser.add_argument('--source', default=str(PROJECT_ROOT / 'patients_folder' / '46个病例_诊疗经过.xlsx'), help='源Excel文件路径')
    batch_parser.add_argument('--output', default=str(PROJECT_ROOT / 'workspace' / 'sandbox'), help='输出目录')
    batch_parser.add_argument('--patients', help='指定患者ID列表（逗号分隔）')
    batch_parser.add_argument('--skip-verification', action='store_true', help='跳过验证步骤')
    batch_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    batch_parser.set_defaults(func=cmd_batch)

    # verify 命令
    verify_parser = subparsers.add_parser('verify', help='验证现有输入文件')
    verify_parser.add_argument('--file', required=True, help='要验证的文件路径')
    verify_parser.set_defaults(func=cmd_verify)

    # inspect 命令
    inspect_parser = subparsers.add_parser('inspect', help='检查源数据结构')
    inspect_parser.add_argument('--source', default=str(PROJECT_ROOT / 'patients_folder' / '46个病例_诊疗经过.xlsx'), help='源Excel文件路径')
    inspect_parser.set_defaults(func=cmd_inspect)

    # clean 命令
    clean_parser = subparsers.add_parser('clean', help='清理污染文件')
    clean_parser.add_argument('--sandbox-dir', default=str(PROJECT_ROOT / 'workspace' / 'sandbox'), help='Sandbox目录路径')
    clean_parser.add_argument('--execute', action='store_true', help='执行实际清理（默认仅预览）')
    clean_parser.set_defaults(func=cmd_clean)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
