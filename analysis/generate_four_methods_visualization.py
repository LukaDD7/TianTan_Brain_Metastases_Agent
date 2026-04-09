#!/usr/bin/env python3
"""
Clinical Expert Review Visualization - 4 Methods Comparison
生成日期: 2026-04-09

功能: 基于专家审查结果生成4种方法的对比可视化图表
方法: Direct LLM V2, RAG V2, Web Search V2, BM Agent
输入: analysis/reviews_*/work_<patient_id>/review_results.json
输出: analysis/final_figures/ 中的高分辨率图表(PNG+PDF)
"""

import json
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
OUTPUT_DIR = ROOT / 'final_figures'

# 4种方法的颜色配置
METHOD_COLORS = {
    'Direct_LLM': '#CD5C5C',    # 印度红
    'RAG': '#4682B4',            # 钢蓝色
    'WebSearch': '#2E8B57',      # 海绿色
    'BM_Agent': '#DAA520',       # 金黄色
}

METHOD_LABELS = {
    'Direct_LLM': 'Direct LLM',
    'RAG': 'RAG V2',
    'WebSearch': 'Web Search V2',
    'BM_Agent': 'BM Agent',
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

# 方法目录映射
METHOD_DIRS = {
    'Direct_LLM': ROOT / 'reviews_direct_v2',
    'RAG': ROOT / 'reviews_rag_v2',
    'WebSearch': ROOT / 'reviews_websearch_v2',
    'BM_Agent': ROOT / 'reviews_bm_agent',
}


def load_review_data(method: str, patient_id: str) -> Dict:
    """加载指定方法和患者的审查数据"""
    review_file = METHOD_DIRS[method] / f'work_{patient_id}' / 'review_results.json'
    if review_file.exists():
        return json.loads(review_file.read_text(encoding='utf-8'))
    return None


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


def load_all_data() -> Dict[str, pd.DataFrame]:
    """加载所有方法的数据"""
    dataframes = {}

    for method in ['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']:
        rows = []
        for pid in PATIENT_IDS:
            review_data = load_review_data(method, pid)
            metrics = extract_metrics(review_data)
            if metrics:
                metrics['case_name'] = CASE_NAMES.get(pid, pid)
                rows.append(metrics)

        if rows:
            dataframes[method] = pd.DataFrame(rows)

    return dataframes


def calculate_statistics(dfs: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    """计算各方法的统计指标"""
    stats = {}

    for method, df in dfs.items():
        stats[method] = {}
        for metric in ['ccr', 'mqr', 'cer', 'ptr', 'cpi']:
            values = df[metric].values
            stats[method][metric.upper()] = {
                'mean': values.mean(),
                'std': values.std(ddof=1),
                'min': values.min(),
                'max': values.max(),
            }

    return stats


def save_figure(fig, stem: str):
    """保存图表为PNG和PDF"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dated_stem = f"{stem}_2026-04-09"
    fig.savefig(OUTPUT_DIR / f'{dated_stem}.png', dpi=300, bbox_inches='tight')
    fig.savefig(OUTPUT_DIR / f'{dated_stem}.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {dated_stem}.png/pdf")


def plot_figure1_radar_comparison(stats: Dict[str, Dict]):
    """图1: 4方法雷达图对比"""
    categories = ['CCR/4', 'PTR', 'MQR/4', '1-CER', 'CPI']
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    for method in ['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']:
        if method not in stats:
            continue

        values = [
            stats[method]['CCR']['mean'] / 4.0,
            stats[method]['PTR']['mean'],
            stats[method]['MQR']['mean'] / 4.0,
            1 - stats[method]['CER']['mean'],
            stats[method]['CPI']['mean'],
        ]
        values += values[:1]

        ax.plot(angles, values, linewidth=2.5, marker='o', markersize=8,
                label=METHOD_LABELS[method], color=METHOD_COLORS[method])
        ax.fill(angles, values, alpha=0.12, color=METHOD_COLORS[method])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=13, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=11)
    ax.set_title('Figure 1. Four-Method Comparison: Radar Chart\n(Mean values across 9 patients)',
                 fontsize=15, fontweight='bold', pad=25)

    save_figure(fig, 'Figure1_four_method_radar')


def plot_figure2_cpi_comparison(dfs: Dict[str, pd.DataFrame], stats: Dict[str, Dict]):
    """图2: CPI分患者对比（4方法）"""
    x = np.arange(len(PATIENT_IDS))
    width = 0.2

    fig, ax = plt.subplots(figsize=(16, 7))

    for i, method in enumerate(['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']):
        if method not in dfs:
            continue
        cpi_values = [dfs[method][dfs[method]['patient_id'] == pid]['cpi'].values[0] for pid in PATIENT_IDS]
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, cpi_values, width, label=METHOD_LABELS[method],
                      color=METHOD_COLORS[method], alpha=0.85)

    ax.set_ylabel('CPI (Composite Performance Index)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 2. Patient-level CPI Comparison (4 Methods)',
                 fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([CASE_NAMES[pid] for pid in PATIENT_IDS], rotation=0, fontsize=9)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    ax.set_ylim(0.3, 1.05)

    save_figure(fig, 'Figure2_cpi_four_methods')


def plot_figure3_metrics_grouped(stats: Dict[str, Dict]):
    """图3: 五指标分组柱状图对比 (Mean±SD)"""
    metrics = ['CCR', 'MQR', 'CER', 'PTR', 'CPI']
    x = np.arange(len(metrics))
    width = 0.2

    fig, ax = plt.subplots(figsize=(14, 7))

    for i, method in enumerate(['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']):
        if method not in stats:
            continue

        means = [stats[method][m]['mean'] for m in metrics]
        stds = [stats[method][m]['std'] for m in metrics]
        offset = (i - 1.5) * width

        bars = ax.bar(x + offset, means, width, yerr=stds, label=METHOD_LABELS[method],
                      color=METHOD_COLORS[method], alpha=0.85, capsize=4)

    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Figure 3. Quantitative Metrics Comparison (Mean ± SD)\nFour Methods',
                 fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    save_figure(fig, 'Figure3_four_methods_meansd')


def plot_figure4_cpi_bars(stats: Dict[str, Dict]):
    """图4: CPI均值对比柱状图"""
    methods = ['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']
    cpi_means = [stats[m]['CPI']['mean'] for m in methods if m in stats]
    cpi_stds = [stats[m]['CPI']['std'] for m in methods if m in stats]
    labels = [METHOD_LABELS[m] for m in methods if m in stats]
    colors = [METHOD_COLORS[m] for m in methods if m in stats]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(labels, cpi_means, yerr=cpi_stds, capsize=8,
                  color=colors, alpha=0.85, edgecolor='black', linewidth=1.5)

    ax.set_ylabel('CPI (Composite Performance Index)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 4. Mean CPI Comparison (4 Methods)\nwith Standard Deviation',
                 fontsize=15, fontweight='bold')
    ax.set_ylim(0, 1.05)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    # 添加数值标签
    for bar, mean, std in zip(bars, cpi_means, cpi_stds):
        ax.text(bar.get_x() + bar.get_width()/2, mean + std + 0.02,
                f'{mean:.3f}±{std:.3f}', ha='center', va='bottom',
                fontsize=11, fontweight='bold')

    save_figure(fig, 'Figure4_cpi_mean_comparison')


def plot_figure5_improvement_bars(stats: Dict[str, Dict]):
    """图5: 相对于Direct LLM的提升幅度"""
    baseline = stats['Direct_LLM']

    metrics = ['CPI', 'CCR', 'MQR', 'PTR']
    methods_compare = ['RAG', 'WebSearch', 'BM_Agent']

    x = np.arange(len(metrics))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, method in enumerate(methods_compare):
        if method not in stats:
            continue

        improvements = []
        for metric in metrics:
            baseline_val = baseline[metric]['mean']
            current_val = stats[method][metric]['mean']
            if metric == 'CER':
                # CER是反向指标
                improvement = ((baseline_val - current_val) / baseline_val * 100) if baseline_val > 0 else 0
            else:
                improvement = ((current_val - baseline_val) / baseline_val * 100) if baseline_val > 0 else 0
            improvements.append(improvement)

        offset = (i - 1) * width
        bars = ax.bar(x + offset, improvements, width, label=METHOD_LABELS[method],
                      color=METHOD_COLORS[method], alpha=0.85)

    ax.set_ylabel('Improvement vs Direct LLM (%)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 5. Performance Improvement vs Direct LLM\n(Percentage change)',
                 fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11)
    ax.axhline(0, color='black', linewidth=1)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    save_figure(fig, 'Figure5_improvement_vs_direct')


def plot_figure6_ptr_comparison(stats: Dict[str, Dict]):
    """图6: PTR详细对比"""
    methods = ['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']
    ptr_means = [stats[m]['PTR']['mean'] for m in methods if m in stats]
    labels = [METHOD_LABELS[m] for m in methods if m in stats]
    colors = [METHOD_COLORS[m] for m in methods if m in stats]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(labels, ptr_means, color=colors, alpha=0.85, edgecolor='black', linewidth=1.5)

    ax.set_ylabel('PTR (Physical Traceability Rate)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 6. Physical Traceability Rate Comparison\n(4 Methods)',
                 fontsize=15, fontweight='bold')
    ax.set_ylim(0, 1.05)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    # 添加数值标签和等级标注
    for bar, mean in zip(bars, ptr_means):
        # 等级判断
        if mean >= 0.8:
            level = "High"
            color = '#2E8B57'
        elif mean >= 0.4:
            level = "Medium"
            color = '#F39C12'
        else:
            level = "Low"
            color = '#E74C3C'

        ax.text(bar.get_x() + bar.get_width()/2, mean + 0.03,
                f'{mean:.3f}\n({level})', ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=color)

    save_figure(fig, 'Figure6_ptr_comparison')


def generate_summary_table(dfs: Dict[str, pd.DataFrame], stats: Dict[str, Dict]) -> str:
    """生成汇总表格（Markdown格式）"""

    lines = []
    lines.append("# Set-1 Batch 四方法可视化分析汇总")
    lines.append("")
    lines.append(f"**生成日期**: 2026-04-09")
    lines.append(f"**样本量**: 9例患者")
    lines.append(f"**对比方法**: Direct LLM V2, RAG V2, Web Search V2, BM Agent")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 一、统计汇总 (Mean±SD)")
    lines.append("")
    lines.append("| 指标 | Direct LLM | RAG V2 | Web Search V2 | BM Agent |")
    lines.append("|------|------------|--------|---------------|----------|")

    for metric in ['CPI', 'CCR', 'MQR', 'CER', 'PTR']:
        row = [metric]
        for method in ['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']:
            if method in stats:
                mean = stats[method][metric]['mean']
                std = stats[method][metric]['std']
                row.append(f"{mean:.3f}±{std:.3f}")
            else:
                row.append("N/A")
        lines.append(f"| {' | '.join(row)} |")

    lines.append("")
    lines.append("## 二、方法排名 (按CPI)")
    lines.append("")

    cpi_ranking = []
    for method in ['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']:
        if method in stats:
            cpi_ranking.append((METHOD_LABELS[method], stats[method]['CPI']['mean']))

    cpi_ranking.sort(key=lambda x: x[1], reverse=True)

    for i, (method, cpi) in enumerate(cpi_ranking, 1):
        lines.append(f"{i}. **{method}**: {cpi:.3f}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**数据来源**: analysis/reviews_*/")
    lines.append("**输出目录**: analysis/final_figures/")

    return "\n".join(lines)


def main():
    print("=" * 70)
    print("4 Methods Clinical Expert Review Visualization")
    print("生成日期: 2026-04-09")
    print("=" * 70)
    print()

    # 加载数据
    print("[1/8] 加载审查数据...")
    dfs = load_all_data()
    for method, df in dfs.items():
        print(f"      {METHOD_LABELS[method]}: {len(df)} patients")

    # 计算统计
    print("\n[2/8] 计算统计指标...")
    stats = calculate_statistics(dfs)

    # 生成图表
    print("\n[3/8] 生成图1: 雷达图对比...")
    plot_figure1_radar_comparison(stats)

    print("[4/8] 生成图2: CPI分患者对比...")
    plot_figure2_cpi_comparison(dfs, stats)

    print("[5/8] 生成图3: 指标Mean±SD对比...")
    plot_figure3_metrics_grouped(stats)

    print("[6/8] 生成图4: CPI均值对比...")
    plot_figure4_cpi_bars(stats)

    print("[7/8] 生成图5-6...")
    plot_figure5_improvement_bars(stats)
    plot_figure6_ptr_comparison(stats)

    # 生成汇总表格
    print("\n[8/8] 生成汇总表格...")
    summary_md = generate_summary_table(dfs, stats)
    summary_file = OUTPUT_DIR / 'FOUR_METHODS_SUMMARY_2026-04-09.md'
    summary_file.write_text(summary_md, encoding='utf-8')
    print(f"      汇总表格: {summary_file}")

    print("\n" + "=" * 70)
    print("可视化生成完成!")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 70)

    # 打印关键统计
    print("\n【关键统计】")
    print("-" * 50)
    for method in ['Direct_LLM', 'RAG', 'WebSearch', 'BM_Agent']:
        if method in stats:
            cpi = stats[method]['CPI']['mean']
            ptr = stats[method]['PTR']['mean']
            print(f"{METHOD_LABELS[method]:20s} CPI: {cpi:.3f}  PTR: {ptr:.3f}")


if __name__ == '__main__':
    main()
