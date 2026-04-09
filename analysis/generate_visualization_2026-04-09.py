#!/usr/bin/env python3
"""
Clinical Expert Review Visualization - 临床专家审查可视化
生成日期: 2026-04-09

功能: 基于专家审查结果生成RAG V2 vs Web Search V2的对比可视化图表
输入: analysis/reviews_rag_v2/ 和 analysis/reviews_websearch_v2/ 中的review_results.json
输出: analysis/final_figures/ 中的高分辨率图表(PNG+PDF)
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['figure.dpi'] = 300

# 路径配置
ROOT = Path(__file__).resolve().parent
RAG_DIR = ROOT / 'reviews_rag_v2'
WEB_DIR = ROOT / 'reviews_websearch_v2'
OUTPUT_DIR = ROOT / 'final_figures'

# 颜色配置
COLORS = {
    'RAG_V2': '#4682B4',      # 钢蓝色
    'WebSearch_V2': '#2E8B57', # 海绿色
    'highlight': '#E74C3C',    # 强调色
    'grid': '#CCCCCC',         # 网格色
}

# 患者列表（按Case编号排序）
PATIENT_IDS = ['648772', '640880', '868183', '665548', '638114', '612908', '605525', '708387', '747724']
CASE_NAMES = {
    '648772': 'Case1\n黑色素瘤',
    '640880': 'Case2\n肺癌EGFR',
    '868183': 'Case3\n肺癌SMARCA4',
    '665548': 'Case4\n贲门癌',
    '638114': 'Case6\n肺癌EGFR+T790M',
    '612908': 'Case7\n肺癌EGFR',
    '605525': 'Case8\n结肠癌KRAS',
    '708387': 'Case9\n肺癌MET',
    '747724': 'Case10\n乳腺癌HER2',
}


def load_review_data(patient_id: str) -> Tuple[Dict, Dict]:
    """加载单个患者的RAG和Web Search审查数据"""
    rag_file = RAG_DIR / f'work_{patient_id}' / 'review_results.json'
    web_file = WEB_DIR / f'work_{patient_id}' / 'review_results.json'

    rag_data = json.loads(rag_file.read_text(encoding='utf-8')) if rag_file.exists() else None
    web_data = json.loads(web_file.read_text(encoding='utf-8')) if web_file.exists() else None

    return rag_data, web_data


def extract_metrics(review_data: Dict) -> Dict:
    """从审查数据中提取指标"""
    if not review_data:
        return None

    return {
        'patient_id': review_data.get('patient_id', ''),
        'ccr': review_data.get('ccr', {}).get('score', 0),
        'mqr': review_data.get('mqr', {}).get('score', 0),
        'cer': review_data.get('cer', {}).get('score', 0),
        'ptr': review_data.get('ptr', {}).get('score', 0),
        'cpi': review_data.get('cpi', 0),
    }


def load_all_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """加载所有患者的对比数据"""
    rag_rows = []
    web_rows = []

    for pid in PATIENT_IDS:
        rag_data, web_data = load_review_data(pid)

        rag_metrics = extract_metrics(rag_data)
        web_metrics = extract_metrics(web_data)

        if rag_metrics:
            rag_metrics['case_name'] = CASE_NAMES.get(pid, pid)
            rag_rows.append(rag_metrics)

        if web_metrics:
            web_metrics['case_name'] = CASE_NAMES.get(pid, pid)
            web_rows.append(web_metrics)

    rag_df = pd.DataFrame(rag_rows)
    web_df = pd.DataFrame(web_rows)

    return rag_df, web_df


def calculate_statistics(rag_df: pd.DataFrame, web_df: pd.DataFrame) -> Dict:
    """计算统计指标"""
    stats = {}

    for metric in ['ccr', 'mqr', 'cer', 'ptr', 'cpi']:
        rag_values = rag_df[metric].values
        web_values = web_df[metric].values

        stats[metric.upper()] = {
            'rag_mean': rag_values.mean(),
            'rag_std': rag_values.std(ddof=1),
            'web_mean': web_values.mean(),
            'web_std': web_values.std(ddof=1),
            'improvement': ((web_values.mean() - rag_values.mean()) / rag_values.mean() * 100)
                          if metric != 'cer' else ((rag_values.mean() - web_values.mean()) / rag_values.mean() * 100)
        }

    return stats


def save_figure(fig, stem: str):
    """保存图表为PNG和PDF"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 添加日期标记到文件名
    dated_stem = f"{stem}_2026-04-09"

    fig.savefig(OUTPUT_DIR / f'{dated_stem}.png', dpi=300, bbox_inches='tight')
    fig.savefig(OUTPUT_DIR / f'{dated_stem}.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {dated_stem}.png/pdf")


def plot_figure1_radar_comparison(rag_df: pd.DataFrame, web_df: pd.DataFrame, stats: Dict):
    """
    图1: 多指标雷达图对比
    展示RAG V2和Web Search V2在各指标上的表现
    """
    categories = ['CCR/4', 'PTR', 'MQR/4', '1-CER', 'CPI']
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    # 计算均值并归一化
    rag_values = [
        stats['CCR']['rag_mean'] / 4.0,
        stats['PTR']['rag_mean'],
        stats['MQR']['rag_mean'] / 4.0,
        1 - stats['CER']['rag_mean'],
        stats['CPI']['rag_mean'],
    ]

    web_values = [
        stats['CCR']['web_mean'] / 4.0,
        stats['PTR']['web_mean'],
        stats['MQR']['web_mean'] / 4.0,
        1 - stats['CER']['web_mean'],
        stats['CPI']['web_mean'],
    ]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

    # RAG V2
    values_rag = rag_values + rag_values[:1]
    ax.plot(angles, values_rag, linewidth=2.5, marker='o', markersize=8,
            label='RAG V2', color=COLORS['RAG_V2'])
    ax.fill(angles, values_rag, alpha=0.15, color=COLORS['RAG_V2'])

    # Web Search V2
    values_web = web_values + web_values[:1]
    ax.plot(angles, values_web, linewidth=2.5, marker='s', markersize=8,
            label='Web Search V2', color=COLORS['WebSearch_V2'])
    ax.fill(angles, values_web, alpha=0.15, color=COLORS['WebSearch_V2'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=13, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', bbox_to_anchor=(1.28, 1.15), fontsize=11)
    ax.set_title('Figure 1. Multi-metric Comparison: RAG V2 vs Web Search V2\n(Mean values across 9 patients)',
                 fontsize=14, fontweight='bold', pad=25)

    save_figure(fig, 'Figure1_radar_comparison')


def plot_figure2_cpi_bar_comparison(rag_df: pd.DataFrame, web_df: pd.DataFrame, stats: Dict):
    """
    图2: CPI分患者对比柱状图
    """
    x = np.arange(len(PATIENT_IDS))
    width = 0.35

    rag_cpi = [rag_df[rag_df['patient_id'] == pid]['cpi'].values[0] for pid in PATIENT_IDS]
    web_cpi = [web_df[web_df['patient_id'] == pid]['cpi'].values[0] for pid in PATIENT_IDS]

    fig, ax = plt.subplots(figsize=(13, 6))

    bars1 = ax.bar(x - width/2, rag_cpi, width, label='RAG V2', color=COLORS['RAG_V2'], alpha=0.85)
    bars2 = ax.bar(x + width/2, web_cpi, width, label='Web Search V2', color=COLORS['WebSearch_V2'], alpha=0.85)

    # 添加均值线
    ax.axhline(stats['CPI']['rag_mean'], color=COLORS['RAG_V2'], linestyle='--',
               linewidth=2, alpha=0.7, label=f"RAG Mean: {stats['CPI']['rag_mean']:.3f}")
    ax.axhline(stats['CPI']['web_mean'], color=COLORS['WebSearch_V2'], linestyle='--',
               linewidth=2, alpha=0.7, label=f"Web Mean: {stats['CPI']['web_mean']:.3f}")

    ax.set_ylabel('CPI (Composite Performance Index)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 2. Patient-level CPI Comparison\n(RAG V2 vs Web Search V2)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([CASE_NAMES[pid] for pid in PATIENT_IDS], rotation=0, fontsize=9)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    ax.set_ylim(0.5, 0.85)

    # 添加数值标签
    for bar, value in zip(bars1, rag_cpi):
        ax.text(bar.get_x() + bar.get_width()/2, value + 0.01, f'{value:.3f}',
                ha='center', va='bottom', fontsize=8, color=COLORS['RAG_V2'], fontweight='bold')
    for bar, value in zip(bars2, web_cpi):
        ax.text(bar.get_x() + bar.get_width()/2, value + 0.01, f'{value:.3f}',
                ha='center', va='bottom', fontsize=8, color=COLORS['WebSearch_V2'], fontweight='bold')

    save_figure(fig, 'Figure2_cpi_comparison')


def plot_figure3_metrics_grouped(rag_df: pd.DataFrame, web_df: pd.DataFrame, stats: Dict):
    """
    图3: 五指标分组柱状图对比 (Mean±SD)
    """
    metrics = ['CCR', 'MQR', 'CER', 'PTR', 'CPI']
    x = np.arange(len(metrics))
    width = 0.35

    rag_means = [stats[m]['rag_mean'] for m in metrics]
    rag_stds = [stats[m]['rag_std'] for m in metrics]
    web_means = [stats[m]['web_mean'] for m in metrics]
    web_stds = [stats[m]['web_std'] for m in metrics]

    fig, ax = plt.subplots(figsize=(12, 6))

    bars1 = ax.bar(x - width/2, rag_means, width, yerr=rag_stds, label='RAG V2',
                   color=COLORS['RAG_V2'], alpha=0.85, capsize=5)
    bars2 = ax.bar(x + width/2, web_means, width, yerr=web_stds, label='Web Search V2',
                   color=COLORS['WebSearch_V2'], alpha=0.85, capsize=5)

    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Figure 3. Quantitative Metrics Comparison (Mean ± SD)\nRAG V2 vs Web Search V2',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=12)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    # 添加数值标签
    for i, (m, rag_mean, rag_std, web_mean, web_std) in enumerate(zip(metrics, rag_means, rag_stds, web_means, web_stds)):
        ax.text(i - width/2, rag_mean + rag_std + 0.02, f'{rag_mean:.3f}±{rag_std:.3f}',
                ha='center', va='bottom', fontsize=9, color=COLORS['RAG_V2'])
        ax.text(i + width/2, web_mean + web_std + 0.02, f'{web_mean:.3f}±{web_std:.3f}',
                ha='center', va='bottom', fontsize=9, color=COLORS['WebSearch_V2'])

    save_figure(fig, 'Figure3_metrics_meansd')


def plot_figure4_improvement_percentage(stats: Dict):
    """
    图4: 提升幅度百分比柱状图
    """
    metrics = ['CPI', 'CCR', 'MQR', 'PTR']
    improvements = [stats[m]['improvement'] for m in metrics]

    # CER是反向指标（越低越好）
    cer_improvement = stats['CER']['improvement']

    fig, ax = plt.subplots(figsize=(10, 6))

    colors_list = [COLORS['WebSearch_V2'] if imp > 0 else COLORS['highlight'] for imp in improvements]
    bars = ax.bar(metrics, improvements, color=colors_list, alpha=0.85, edgecolor='black')

    # 单独添加CER（反向指标）
    ax.bar(['CER\n(lower is better)'], [cer_improvement], color=COLORS['WebSearch_V2'], alpha=0.85, edgecolor='black')

    ax.set_ylabel('Improvement (%)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 4. Web Search V2 vs RAG V2: Performance Improvement\n(Percentage change)',
                 fontsize=14, fontweight='bold')
    ax.axhline(0, color='black', linewidth=1)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    # 添加数值标签
    all_metrics = metrics + ['CER\n(lower is better)']
    all_improvements = improvements + [cer_improvement]

    for bar, value in zip(bars, all_improvements[:-1]):
        ax.text(bar.get_x() + bar.get_width()/2, value + (5 if value > 0 else -8),
                f'{value:.1f}%', ha='center', va='bottom' if value > 0 else 'top',
                fontsize=11, fontweight='bold')

    # CER标签
    ax.text(4, cer_improvement + 3, f'{cer_improvement:.1f}%\n(reduction)',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

    save_figure(fig, 'Figure4_improvement_percentage')


def plot_figure5_patient_heatmap(rag_df: pd.DataFrame, web_df: pd.DataFrame):
    """
    图5: 患者级指标热力图对比
    """
    metrics = ['CCR/4', 'PTR', 'MQR/4', '1-CER', 'CPI']

    # 构建矩阵: 患者 x (RAG指标 + Web指标)
    matrix_rows = []
    row_labels = []

    for pid in PATIENT_IDS:
        rag_row = rag_df[rag_df['patient_id'] == pid].iloc[0]
        web_row = web_df[web_df['patient_id'] == pid].iloc[0]

        # RAG值
        rag_values = [
            rag_row['ccr'] / 4.0,
            rag_row['ptr'],
            rag_row['mqr'] / 4.0,
            1 - rag_row['cer'],
            rag_row['cpi'],
        ]

        # Web值
        web_values = [
            web_row['ccr'] / 4.0,
            web_row['ptr'],
            web_row['mqr'] / 4.0,
            1 - web_row['cer'],
            web_row['cpi'],
        ]

        matrix_rows.append(rag_values + web_values)
        row_labels.append(f"{pid}\n{CASE_NAMES[pid].split(chr(10))[1]}")

    matrix = np.array(matrix_rows)

    # 创建列标签
    col_labels = [f'{m}\n(RAG)' for m in metrics] + [f'{m}\n(Web)' for m in metrics]

    fig, ax = plt.subplots(figsize=(14, 8))
    im = ax.imshow(matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels, fontsize=10, fontweight='bold')
    ax.set_yticklabels(row_labels, fontsize=9)

    ax.set_title('Figure 5. Patient-level Performance Heatmap\n(RAG V2 vs Web Search V2)',
                 fontsize=14, fontweight='bold', pad=16)

    # 添加数值
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax.text(j, i, f'{value:.2f}', ha='center', va='center',
                   color='white' if value < 0.5 else 'black', fontsize=8, fontweight='bold')

    # 添加分隔线
    for i in range(len(row_labels)):
        ax.axhline(i + 0.5, color='white', linewidth=2)
    ax.axvline(4.5, color='white', linewidth=3)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Normalized Score (0-1)', fontsize=11)

    save_figure(fig, 'Figure5_patient_heatmap')


def plot_figure6_ptr_breakdown(rag_df: pd.DataFrame, web_df: pd.DataFrame):
    """
    图6: PTR引用来源分解对比
    """
    # 计算引用类型的平均值
    rag_pubmed, rag_guideline, rag_web, rag_local = [], [], [], []
    web_pubmed, web_guideline, web_web, web_local = [], [], [], []

    for pid in PATIENT_IDS:
        rag_file = RAG_DIR / f'work_{pid}' / 'review_results.json'
        web_file = WEB_DIR / f'work_{pid}' / 'review_results.json'

        if rag_file.exists():
            data = json.loads(rag_file.read_text())
            details = data.get('ptr', {}).get('details', {})
            rag_pubmed.append(details.get('pubmed_citations', 0))
            rag_guideline.append(details.get('guideline_citations', 0))
            rag_web.append(details.get('web_citations', 0))
            rag_local.append(details.get('local_citations', 0))

        if web_file.exists():
            data = json.loads(web_file.read_text())
            details = data.get('ptr', {}).get('details', {})
            web_pubmed.append(details.get('pubmed_citations', 0))
            web_guideline.append(details.get('guideline_citations', 0))
            web_web.append(details.get('web_citations', 0))
            web_local.append(details.get('local_citations', 0))

    # 计算平均值
    categories = ['PubMed', 'Guideline', 'Web', 'Local']
    rag_means = [np.mean(rag_pubmed), np.mean(rag_guideline), np.mean(rag_web), np.mean(rag_local)]
    web_means = [np.mean(web_pubmed), np.mean(web_guideline), np.mean(web_web), np.mean(web_local)]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars1 = ax.bar(x - width/2, rag_means, width, label='RAG V2', color=COLORS['RAG_V2'], alpha=0.85)
    bars2 = ax.bar(x + width/2, web_means, width, label='Web Search V2', color=COLORS['WebSearch_V2'], alpha=0.85)

    ax.set_ylabel('Average Number of Citations', fontsize=12, fontweight='bold')
    ax.set_title('Figure 6. Citation Source Breakdown (Mean per Patient)\nRAG V2 vs Web Search V2',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=12)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    # 添加数值标签
    for bar, value in zip(bars1, rag_means):
        ax.text(bar.get_x() + bar.get_width()/2, value + 0.1, f'{value:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    for bar, value in zip(bars2, web_means):
        ax.text(bar.get_x() + bar.get_width()/2, value + 0.1, f'{value:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    save_figure(fig, 'Figure6_citation_breakdown')


def generate_summary_table(rag_df: pd.DataFrame, web_df: pd.DataFrame, stats: Dict) -> str:
    """生成汇总表格（Markdown格式）"""

    lines = []
    lines.append("# Set-1 Batch 可视化分析汇总")
    lines.append("")
    lines.append(f"**生成日期**: 2026-04-09")
    lines.append(f"**样本量**: 9例患者")
    lines.append(f"**对比方法**: RAG V2 vs Web Search V2")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 一、统计汇总 (Mean±SD)")
    lines.append("")
    lines.append("| 指标 | RAG V2 | Web Search V2 | 提升幅度 |")
    lines.append("|------|--------|---------------|---------|")

    for metric in ['CPI', 'CCR', 'MQR', 'CER', 'PTR']:
        rag_mean = stats[metric]['rag_mean']
        rag_std = stats[metric]['rag_std']
        web_mean = stats[metric]['web_mean']
        web_std = stats[metric]['web_std']
        improvement = stats[metric]['improvement']

        direction = "↑" if (metric != 'cer' and improvement > 0) or (metric == 'cer' and improvement > 0) else "↓"

        lines.append(f"| {metric} | {rag_mean:.3f}±{rag_std:.3f} | {web_mean:.3f}±{web_std:.3f} | {direction}{improvement:.1f}% |")

    lines.append("")
    lines.append("## 二、生成的图表")
    lines.append("")
    lines.append("| 图表 | 文件名 | 说明 |")
    lines.append("|------|--------|------|")
    lines.append("| 图1 | Figure1_radar_comparison_2026-04-09.png | 多指标雷达图对比 |")
    lines.append("| 图2 | Figure2_cpi_comparison_2026-04-09.png | CPI分患者对比 |")
    lines.append("| 图3 | Figure3_metrics_meansd_2026-04-09.png | 五指标Mean±SD对比 |")
    lines.append("| 图4 | Figure4_improvement_percentage_2026-04-09.png | 提升幅度百分比 |")
    lines.append("| 图5 | Figure5_patient_heatmap_2026-04-09.png | 患者级热力图 |")
    lines.append("| 图6 | Figure6_citation_breakdown_2026-04-09.png | 引用来源分解 |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**数据来源**: analysis/reviews_rag_v2/ 和 analysis/reviews_websearch_v2/")
    lines.append("**输出目录**: analysis/final_figures/")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Clinical Expert Review Visualization")
    print("生成日期: 2026-04-09")
    print("=" * 60)
    print()

    # 加载数据
    print("[1/7] 加载审查数据...")
    rag_df, web_df = load_all_data()
    print(f"      RAG V2: {len(rag_df)} patients")
    print(f"      Web Search V2: {len(web_df)} patients")

    # 计算统计
    print("[2/7] 计算统计指标...")
    stats = calculate_statistics(rag_df, web_df)

    # 生成图表
    print("[3/7] 生成图1: 雷达图对比...")
    plot_figure1_radar_comparison(rag_df, web_df, stats)

    print("[4/7] 生成图2: CPI对比...")
    plot_figure2_cpi_bar_comparison(rag_df, web_df, stats)

    print("[5/7] 生成图3: 指标Mean±SD对比...")
    plot_figure3_metrics_grouped(rag_df, web_df, stats)

    print("[6/7] 生成图4-6...")
    plot_figure4_improvement_percentage(stats)
    plot_figure5_patient_heatmap(rag_df, web_df)
    plot_figure6_ptr_breakdown(rag_df, web_df)

    # 生成汇总表格
    print("[7/7] 生成汇总表格...")
    summary_md = generate_summary_table(rag_df, web_df, stats)
    summary_file = OUTPUT_DIR / 'VISUALIZATION_SUMMARY_2026-04-09.md'
    summary_file.write_text(summary_md, encoding='utf-8')
    print(f"      汇总表格: {summary_file}")

    print()
    print("=" * 60)
    print("可视化生成完成!")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
