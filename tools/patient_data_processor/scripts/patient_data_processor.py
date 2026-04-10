#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
患者输入数据处理器
Patient Data Processor

核心功能：
1. 从Excel读取原始患者数据
2. 自动清理敏感字段（入院诊断、出院诊断、诊疗经过）
3. 生成符合BM Agent输入标准的干净数据文件
4. 提供验证机制确保无数据污染

使用示例：
    from patient_data_processor import PatientDataProcessor

    processor = PatientDataProcessor("workspace/test_cases_wide.xlsx")
    processor.process_patient("640880", "workspace/sandbox/patient_640880_input.txt")
"""

import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    patient_id: str
    output_path: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    removed_fields: List[str] = field(default_factory=list)
    included_fields: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class PatientDataProcessor:
    """
    患者输入数据处理器

    字段定义：
    - ALLOWED_FIELDS: 允许的输入特征字段
    - SENSITIVE_FIELDS: 必须移除的Ground Truth字段
    - TREATMENT_KEYWORDS: 治疗相关的敏感关键词
    """

    # 允许的输入字段（白名单）
    ALLOWED_FIELDS = [
        '住院号',
        '入院时间',
        '年龄',
        '性别',
        '主诉',
        '现病史',
        '既往史',
        '头部MRI',
        '胸部CT',
        '颈椎MRI',
        '腰椎MRI',
        '腹盆CT',
        '病理诊断',
    ]

    # 可选字段（允许为空）
    OPTIONAL_FIELDS = [
        '胸部CT',
        '颈椎MRI',
        '腰椎MRI',
        '腹盆CT',
        '病理诊断',
    ]

    # 敏感字段（必须移除）
    SENSITIVE_FIELDS = [
        '入院诊断',
        '出院诊断',
        '诊疗经过',
        '出院时间',  # 通常包含诊疗结果信息
    ]

    # 治疗相关敏感关键词（内容检测）
    TREATMENT_KEYWORDS = [
        '一线化疗', '二线化疗', '三线治疗',
        '放疗后', '化疗后', '术后给予',
        'mg', 'Gy', '静脉滴注', '静点',
        'q3w', 'q2w', 'd1', '周期',
        '疗效评估', 'PR', 'CR', 'PD', 'SD',
        '部分缓解', '完全缓解', '疾病进展',
        '培美曲塞', '顺铂', '卡铂', '贝伐珠单抗',
        '曲妥珠单抗', '卡培他滨',
    ]

    # 剂量模式（正则检测）
    DOSAGE_PATTERNS = [
        r'\d+\s*mg',           # 500mg
        r'\d+\s*Gy',           # 16Gy
        r'\d+\s*g\s*早',       # 1.5g 早
        r'q\d+w',              # q3w
        r'd\d+',               # d1
    ]

    def __init__(self, excel_path: str):
        """
        初始化处理器

        Args:
            excel_path: Excel文件路径
        """
        self.excel_path = Path(excel_path)
        self.df = None
        self._load_excel()

    def _load_excel(self):
        """加载Excel数据"""
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel文件不存在: {self.excel_path}")

        self.df = pd.read_excel(self.excel_path)
        print(f"[INFO] 加载Excel: {self.excel_path}")
        print(f"[INFO] 共 {len(self.df)} 例患者, {len(self.df.columns)} 个字段")

        # 检查敏感字段是否存在
        sensitive_found = [f for f in self.SENSITIVE_FIELDS if f in self.df.columns]
        if sensitive_found:
            print(f"[WARNING] Excel中包含敏感字段: {sensitive_found}")
            print(f"[INFO] 处理时将自动移除这些字段")

    def process_patient(self, patient_id: str, output_path: Optional[str] = None) -> ProcessingResult:
        """
        处理单个患者数据

        Args:
            patient_id: 患者ID（住院号）
            output_path: 输出文件路径（可选）

        Returns:
            ProcessingResult: 处理结果
        """
        result = ProcessingResult(success=True, patient_id=patient_id)

        # 查找患者
        patient_row = self.df[self.df['住院号'].astype(str) == str(patient_id)]
        if len(patient_row) == 0:
            result.success = False
            result.errors.append(f"未找到患者: {patient_id}")
            return result

        row = patient_row.iloc[0]

        # 提取允许的字段
        clean_data = {}
        for field in self.ALLOWED_FIELDS:
            if field in self.df.columns:
                value = row.get(field)
                if pd.notna(value):
                    clean_data[field] = str(value).strip()
                    result.included_fields.append(field)

        # 记录移除的敏感字段
        for field in self.SENSITIVE_FIELDS:
            if field in self.df.columns and field not in self.ALLOWED_FIELDS:
                result.removed_fields.append(field)

        # 内容安全检查
        content_violations = self._check_content_safety(clean_data)
        if content_violations:
            result.warnings.extend(content_violations)

        # 生成输出文本
        output_text = self._format_output(clean_data)

        # 保存文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            result.output_path = str(output_path)
            print(f"[INFO] 已保存: {output_path}")

        return result

    def _check_content_safety(self, data: Dict[str, str]) -> List[str]:
        """
        检查内容安全性（检测敏感关键词）

        Args:
            data: 清理后的数据字典

        Returns:
            警告信息列表
        """
        warnings = []

        for field, value in data.items():
            # 检查治疗关键词
            for keyword in self.TREATMENT_KEYWORDS:
                if keyword in value:
                    warnings.append(
                        f"字段'{field}'可能包含治疗信息: '{keyword}'"
                    )

            # 检查剂量模式
            for pattern in self.DOSAGE_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    match = re.search(pattern, value, re.IGNORECASE).group(0)
                    warnings.append(
                        f"字段'{field}'可能包含剂量信息: '{match}'"
                    )
                    break

        return warnings

    def _format_output(self, data: Dict[str, str]) -> str:
        """
        格式化输出文本

        Args:
            data: 清理后的数据字典

        Returns:
            格式化的文本
        """
        lines = []

        # 基本信息
        basic_info = []
        for field in ['住院号', '入院时间', '年龄', '性别']:
            if field in data:
                basic_info.append(f"{field} {data[field]}")
        if basic_info:
            lines.append("。".join(basic_info) + "。")

        # 主诉
        if '主诉' in data:
            lines.append(f"主诉 {data['主诉']}。")

        # 现病史
        if '现病史' in data:
            lines.append(f"现病史 {data['现病史']}。")

        # 既往史
        if '既往史' in data:
            lines.append(f"既往史 {data['既往史']}。")

        # 影像信息
        for field in ['头部MRI', '胸部CT', '颈椎MRI', '腰椎MRI', '腹盆CT']:
            if field in data:
                lines.append(f"{field} {data[field]}。")

        # 病理诊断
        if '病理诊断' in data:
            lines.append(f"病理诊断 {data['病理诊断']}。")

        return "\n".join(lines)

    def validate_input_file(self, file_path: str) -> ValidationResult:
        """
        验证输入文件是否符合规范

        Args:
            file_path: 输入文件路径

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)

        file_path = Path(file_path)
        if not file_path.exists():
            result.is_valid = False
            result.violations.append(f"文件不存在: {file_path}")
            return result

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查敏感字段
        for sensitive in self.SENSITIVE_FIELDS:
            if sensitive in content:
                result.is_valid = False
                result.violations.append(f"包含敏感字段: {sensitive}")

        # 检查必须字段
        required_fields = ['主诉', '现病史', '头部MRI']
        for required in required_fields:
            if required not in content:
                result.is_valid = False
                result.violations.append(f"缺少必要字段: {required}")

        # 内容安全检查
        for keyword in self.TREATMENT_KEYWORDS:
            if keyword in content:
                result.warnings.append(f"可能包含治疗信息: '{keyword}'")

        # 统计信息
        result.details = {
            'file_size': len(content),
            'has_chief_complaint': '主诉' in content,
            'has_history': '现病史' in content,
            'has_mri': '头部MRI' in content,
            'line_count': len(content.split('\n')),
        }

        return result

    def batch_process(self, output_dir: str, patient_ids: Optional[List[str]] = None) -> List[ProcessingResult]:
        """
        批量处理患者数据

        Args:
            output_dir: 输出目录
            patient_ids: 指定患者ID列表（可选，默认处理全部）

        Returns:
            ProcessingResult列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if patient_ids is None:
            patient_ids = self.df['住院号'].astype(str).tolist()

        results = []
        for patient_id in patient_ids:
            output_path = output_dir / f"patient_{patient_id}_input.txt"
            result = self.process_patient(patient_id, str(output_path))
            results.append(result)

        # 打印汇总
        success_count = sum(1 for r in results if r.success)
        print(f"\n{'='*60}")
        print(f"批量处理完成: {success_count}/{len(results)} 成功")
        print(f"输出目录: {output_dir}")
        print(f"{'='*60}")

        return results

    def generate_report(self, results: List[ProcessingResult]) -> str:
        """
        生成处理报告

        Args:
            results: 处理结果列表

        Returns:
            报告文本
        """
        lines = [
            "# 患者输入数据处理报告",
            f"\n生成时间: {datetime.now().isoformat()}",
            f"数据源: {self.excel_path}",
            f"\n## 处理统计",
            f"\n总例数: {len(results)}",
        ]

        success_count = sum(1 for r in results if r.success)
        lines.append(f"成功: {success_count}")
        lines.append(f"失败: {len(results) - success_count}")

        # 敏感字段移除统计
        all_removed = []
        for r in results:
            all_removed.extend(r.removed_fields)
        unique_removed = list(set(all_removed))
        if unique_removed:
            lines.append(f"\n## 自动移除的敏感字段")
            for field in unique_removed:
                lines.append(f"- {field}")

        # 警告统计
        all_warnings = []
        for r in results:
            all_warnings.extend(r.warnings)
        if all_warnings:
            lines.append(f"\n## 内容安全警告 ({len(all_warnings)} 项)")
            for warning in all_warnings[:20]:  # 只显示前20条
                lines.append(f"- ⚠️ {warning}")

        # 详细结果
        lines.append(f"\n## 详细处理结果")
        for r in results:
            status = "✅" if r.success else "❌"
            lines.append(f"\n### {status} 患者 {r.patient_id}")
            if r.output_path:
                lines.append(f"- 输出: {r.output_path}")
            lines.append(f"- 包含字段: {', '.join(r.included_fields)}")
            if r.removed_fields:
                lines.append(f"- 移除字段: {', '.join(r.removed_fields)}")
            if r.warnings:
                lines.append(f"- 警告: {len(r.warnings)} 项")
            if r.errors:
                lines.append(f"- 错误: {'; '.join(r.errors)}")

        return "\n".join(lines)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='患者输入数据处理器')
    parser.add_argument('--excel', default='workspace/test_cases_wide.xlsx',
                        help='Excel文件路径')
    parser.add_argument('--patient-id', help='指定患者ID（住院号）')
    parser.add_argument('--output', help='输出文件/目录路径')
    parser.add_argument('--batch', action='store_true', help='批量处理模式')
    parser.add_argument('--validate', help='验证指定输入文件')

    args = parser.parse_args()

    # 验证模式
    if args.validate:
        processor = PatientDataProcessor(args.excel)
        result = processor.validate_input_file(args.validate)
        print(f"\n验证结果: {'✅ 通过' if result.is_valid else '❌ 失败'}")
        if result.violations:
            print("\n违规项:")
            for v in result.violations:
                print(f"  ❌ {v}")
        if result.warnings:
            print("\n警告:")
            for w in result.warnings:
                print(f"  ⚠️ {w}")
        return

    # 初始化处理器
    processor = PatientDataProcessor(args.excel)

    # 单例处理
    if args.patient_id and not args.batch:
        output_path = args.output or f"workspace/sandbox/patient_{args.patient_id}_input.txt"
        result = processor.process_patient(args.patient_id, output_path)

        print(f"\n{'='*60}")
        print(f"处理结果: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"患者ID: {result.patient_id}")
        print(f"输出路径: {result.output_path}")
        print(f"包含字段: {', '.join(result.included_fields)}")
        print(f"移除字段: {', '.join(result.removed_fields)}")
        if result.warnings:
            print(f"\n⚠️ 警告 ({len(result.warnings)} 项):")
            for w in result.warnings:
                print(f"  - {w}")
        print(f"{'='*60}")
        return

    # 批量处理
    if args.batch:
        output_dir = args.output or "workspace/sandbox"
        results = processor.batch_process(output_dir)

        # 生成报告
        report = processor.generate_report(results)
        report_path = Path(output_dir) / "processing_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存: {report_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
