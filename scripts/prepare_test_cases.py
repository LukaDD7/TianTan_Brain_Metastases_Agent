#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将长表格式测试数据转换为宽表格式
"""

import pandas as pd
from pathlib import Path

def convert_long_to_wide(excel_path: str, output_path: str):
    """将长表格式转换为宽表格式"""
    print(f"📚 读取测试数据：{excel_path}")
    df = pd.read_excel(excel_path)

    print(f"   总记录数：{len(df)}")
    print(f"   列：{list(df.columns)}")

    # 透视表：id 为索引，Feature 为列，Value 为值
    print(f"\n🔄 转换为宽表格式...")
    wide_df = df.pivot(index='id', columns='Feature', values='Value')

    # 重置索引，使 id 变为普通列
    wide_df = wide_df.reset_index()

    # 添加预期结果列（待填充）
    wide_df['expected_modality'] = None  # systemic_therapy, radiotherapy, surgery
    wide_df['expected_gene'] = None      # BRAF, EGFR, ALK, etc.
    wide_df['expected_variant'] = None   # V600E, L858R, etc.

    # 保存为新的 Excel
    wide_df.to_excel(output_path, index=False)

    print(f"\n✅ 转换完成：{output_path}")
    print(f"   包含 {len(wide_df)} 个病例")
    print(f"   总字段数：{len(wide_df.columns)}")

    # 显示前 3 行
    print(f"\n📊 前 3 行数据预览：")
    print(wide_df.head(3).to_string())

    # 统计信息
    print(f"\n📈 字段列表：")
    for col in wide_df.columns:
        non_null_count = wide_df[col].notna().sum()
        print(f"   - {col:30s} ({non_null_count}/{len(wide_df)} 非空)")

    return wide_df

if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).parent.parent
    INPUT_PATH = PROJECT_ROOT / "workspace" / "original_cases" / "TT_BM_test.xlsx"
    OUTPUT_PATH = PROJECT_ROOT / "workspace" / "test_cases_wide.xlsx"

    convert_long_to_wide(INPUT_PATH, OUTPUT_PATH)
