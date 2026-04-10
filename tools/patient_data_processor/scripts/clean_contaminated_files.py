#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理现有污染输入文件
Clean Contaminated Input Files

功能：
1. 检测现有输入文件中的数据污染
2. 自动清理敏感字段
3. 备份原文件
4. 生成干净版本

使用:
    python clean_contaminated_files.py --dry-run    # 预览模式，不实际修改
    python clean_contaminated_files.py              # 执行清理
"""

import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import argparse


# 敏感字段模式（检测用）
SENSITIVE_PATTERNS = {
    '入院诊断': [
        r'入院诊断\s*[:：]',
        r'初步诊断',
    ],
    '出院诊断': [
        r'出院诊断\s*[:：]',
        r'确定诊断',
    ],
    '诊疗经过': [
        r'诊疗经过\s*[:：]',
        r'治疗经过',
    ],
}

# 治疗信息关键词
TREATMENT_KEYWORDS = [
    '一线化疗', '二线化疗', '三线治疗',
    '放疗后', '化疗后', '术后给予',
    '伽玛刀', '立体定向',
]


class ContaminationCleaner:
    """污染文件清理器"""

    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = Path(sandbox_dir)
        self.backup_dir = self.sandbox_dir / "input_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []

    def scan_all_files(self) -> List[Path]:
        """扫描所有患者输入文件"""
        pattern = self.sandbox_dir / "patient_*_input.txt"
        return list(self.sandbox_dir.glob("patient_*_input.txt"))

    def analyze_file(self, file_path: Path) -> Dict:
        """分析文件的污染情况"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        result = {
            'file': file_path,
            'patient_id': file_path.stem.replace('patient_', '').replace('_input', ''),
            'contaminated': False,
            'sensitive_fields': [],
            'treatment_keywords': [],
            'dosage_patterns': [],
            'lines': content.split('\n'),
        }

        # 检测敏感字段
        for field, patterns in SENSITIVE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result['contaminated'] = True
                    if field not in result['sensitive_fields']:
                        result['sensitive_fields'].append(field)

        # 检测治疗关键词
        for keyword in TREATMENT_KEYWORDS:
            if keyword in content:
                result['treatment_keywords'].append(keyword)

        # 检测剂量模式
        dosage_patterns = [
            (r'\d+\s*Gy', '剂量'),
            (r'\d+\s*mg\s+iv', '静脉用药'),
            (r'地塞米松\s+\d+', '地塞米松'),
            (r'甘露醇\s+\d+', '甘露醇'),
        ]
        for pattern, desc in dosage_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result['dosage_patterns'].append(desc)

        return result

    def clean_file(self, analysis: Dict, dry_run: bool = True) -> str:
        """清理单个文件"""
        file_path = analysis['file']
        patient_id = analysis['patient_id']

        if not analysis['contaminated'] and not analysis['treatment_keywords']:
            return "clean"

        # 读取原内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 清理策略：移除敏感字段段落
        cleaned_content = self._remove_sensitive_sections(content)

        # 如果内容有变化
        if cleaned_content != original_content:
            if dry_run:
                return "would_clean"

            # 备份原文件
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self.backup_dir / f"{file_path.name}.contaminated"
            shutil.copy2(file_path, backup_path)

            # 写入清理后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)

            return "cleaned"

        return "clean"

    def _remove_sensitive_sections(self, content: str) -> str:
        """移除敏感段落"""
        lines = content.split('\n')
        cleaned_lines = []
        skip_section = False
        current_section = None

        for line in lines:
            # 检测敏感字段标题
            if re.search(r'(入院诊断|出院诊断|诊疗经过)\s*[:：]', line):
                skip_section = True
                current_section = line
                continue

            # 检测新段落开始（非缩进或新字段）
            if skip_section:
                # 如果遇到新的字段标题（主诉、现病史等），结束跳过
                if re.search(r'^(主诉|现病史|既往史|头部MRI|胸部CT|住院号|年龄)', line):
                    skip_section = False
                    current_section = None
                elif re.match(r'^[a-zA-Z\u4e00-\u9fa5]+[:：]', line):
                    # 可能是新字段
                    skip_section = False
                    current_section = None

            if not skip_section:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def run(self, dry_run: bool = True) -> None:
        """执行清理"""
        files = self.scan_all_files()

        print("="*80)
        print("  输入文件污染清理工具")
        print("="*80)
        print(f"\n扫描目录: {self.sandbox_dir}")
        print(f"找到文件: {len(files)} 个")

        if dry_run:
            print("\n模式: 预览 (dry-run)")
            print("提示: 添加 --execute 参数执行实际清理\n")

        contaminated_count = 0
        cleaned_count = 0

        for file_path in sorted(files):
            analysis = self.analyze_file(file_path)

            if analysis['contaminated'] or analysis['treatment_keywords']:
                contaminated_count += 1
                print(f"\n❌ 患者 {analysis['patient_id']}:")

                if analysis['sensitive_fields']:
                    print(f"   敏感字段: {', '.join(analysis['sensitive_fields'])}")
                if analysis['treatment_keywords']:
                    print(f"   治疗关键词: {', '.join(analysis['treatment_keywords'])}")
                if analysis['dosage_patterns']:
                    print(f"   剂量信息: {', '.join(analysis['dosage_patterns'])}")

                # 执行清理
                result = self.clean_file(analysis, dry_run)

                if result == "would_clean":
                    print(f"   [预览] 将被清理")
                elif result == "cleaned":
                    print(f"   ✅ 已清理并备份")
                    cleaned_count += 1
            else:
                print(f"\n✅ 患者 {analysis['patient_id']}: 干净")

        print("\n" + "="*80)
        print(f"统计:")
        print(f"  总文件数: {len(files)}")
        print(f"  污染文件: {contaminated_count}")
        print(f"  干净文件: {len(files) - contaminated_count}")

        if not dry_run:
            print(f"  已清理: {cleaned_count}")
            print(f"  备份位置: {self.backup_dir}")
        else:
            print(f"\n执行实际清理命令:")
            print(f"  python clean_contaminated_files.py --execute")

        print("="*80)


def main():
    parser = argparse.ArgumentParser(description='清理污染的输入文件')
    parser.add_argument('--sandbox-dir',
                        default='/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox',
                        help='sandbox目录路径')
    parser.add_argument('--execute', action='store_true',
                        help='执行实际清理（默认仅预览）')

    args = parser.parse_args()

    cleaner = ContaminationCleaner(args.sandbox_dir)
    cleaner.run(dry_run=not args.execute)


if __name__ == "__main__":
    main()
