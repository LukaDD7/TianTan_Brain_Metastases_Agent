#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Set-1 input files from test_cases_wide.xlsx
宽表格式转标准输入文件
"""

import pandas as pd
import os
from pathlib import Path

def main():
    # 读取宽表
    df = pd.read_excel('workspace/test_cases_wide.xlsx')
    print(f"Loaded {len(df)} rows from test_cases_wide.xlsx")

    # 输出目录
    output_dir = Path('patient_input/Set-1')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 字段顺序
    OUTPUT_ORDER = [
        '住院号', '入院时间', '年龄', '性别',
        '主诉', '现病史', '既往史',
        '头部MRI', '胸部CT', '颈椎MRI', '胸椎MRI', '腰椎MRI',
        '腹盆CT', '病理诊断'
    ]

    print("="*60)
    print("Set-1 患者输入文件生成 (test_cases_wide.xlsx)")
    print("="*60)

    removed_summary = ['入院诊断', '出院诊断', '出院时间', '诊疗经过', 'expected_modality', 'expected_gene', 'expected_variant']

    for idx, row in df.iterrows():
        patient_id = str(int(row['住院号']))

        lines = []

        for feature in OUTPUT_ORDER:
            if feature in row and pd.notna(row[feature]):
                value = str(row[feature]).strip()
                if not value.endswith(('。', '.')):
                    value += '。'
                lines.append(f"{feature} {value}")

        output_text = '\n'.join(lines)
        output_path = output_dir / f'patient_{patient_id}_input.txt'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)

        print(f"✓ patient_{patient_id}_input.txt")
        print(f"  第一层移除: {removed_summary}")

    print("="*60)
    print(f"共生成 {len(df)} 个文件")
    print(f"输出目录: {output_dir.absolute()}")
    print("="*60)

if __name__ == "__main__":
    main()
