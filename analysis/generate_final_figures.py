#!/usr/bin/env python3
"""
统一终版图表生成脚本。
所有 BM Agent 数据均从 analysis/final_results/final_metrics.json 读取，
避免脚本内硬编码患者级结果继续漂移。
"""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['figure.dpi'] = 300

ROOT = Path(__file__).resolve().parent
FINAL_RESULTS_DIR = ROOT / 'final_results'
FINAL_METRICS_JSON = FINAL_RESULTS_DIR / 'final_metrics.json'
FINAL_FIGURES_DIR = ROOT / 'final_figures'

METHOD_COLORS = {
    'BM Agent': '#2E8B57',
    'RAG': '#4682B4',
    'Direct LLM': '#CD5C5C',
    'WebSearch': '#DAA520',
}

BASELINE_SUMMARY = {
    'Direct LLM': {'CCR': 1.51, 'PTR': 0.000, 'MQR': 1.98, 'CER': None, 'CPI': 0.420},
    'RAG': {'CCR': 2.01, 'PTR': 0.000, 'MQR': 2.49, 'CER': None, 'CPI': 0.520},
    'WebSearch': {'CCR': 2.21, 'PTR': 0.000, 'MQR': 2.59, 'CER': None, 'CPI': 0.570},
}

EFFICIENCY_SUMMARY = {
    'Direct LLM': {'latency': 94.3, 'tokens': 7.2, 'tool_calls': 0.0},
    'RAG': {'latency': 106.2, 'tokens': 9.0, 'tool_calls': 1.0},
    'WebSearch': {'latency': 127.4, 'tokens': 42.9, 'tool_calls': 2.0},
    'BM Agent': {'latency': 260.4, 'tokens': 581.5, 'tool_calls': 41.6},
}

CITATION_BREAKDOWN = {
    'PubMed': 14.1,
    'OncoKB': 2.0,
    'Local': 20.7,
}


def load_final_metrics():
    with open(FINAL_METRICS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patient_scores = data['patient_scores']
    ordered_ids = sorted(patient_scores.keys(), key=lambda pid: int(patient_scores[pid]['case'].replace('Case', '')))
    patient_rows = []
    for pid in ordered_ids:
        row = {'patient_id': pid, **patient_scores[pid]}
        patient_rows.append(row)

    patient_df = pd.DataFrame(patient_rows)
    stats = data['statistics']
    return patient_df, stats, data


def save_figure(fig, stem: str):
    FINAL_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FINAL_FIGURES_DIR / f'{stem}.png', dpi=300, bbox_inches='tight')
    fig.savefig(FINAL_FIGURES_DIR / f'{stem}.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_figure1_overview(patient_df, stats):
    methods = ['Direct LLM', 'RAG', 'WebSearch', 'BM Agent']
    categories = ['CCR', 'PTR', 'MQR', '1-CER', 'CPI']
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    bm_values = [
        stats['CCR']['mean'] / 4.0,
        stats['PTR']['mean'],
        stats['MQR']['mean'] / 4.0,
        1 - stats['CER']['mean'],
        stats['CPI']['mean'],
    ]

    method_values = {
        'Direct LLM': [BASELINE_SUMMARY['Direct LLM']['CCR'] / 4.0, 0.0, BASELINE_SUMMARY['Direct LLM']['MQR'] / 4.0, 0.4, BASELINE_SUMMARY['Direct LLM']['CPI']],
        'RAG': [BASELINE_SUMMARY['RAG']['CCR'] / 4.0, 0.0, BASELINE_SUMMARY['RAG']['MQR'] / 4.0, 0.5, BASELINE_SUMMARY['RAG']['CPI']],
        'WebSearch': [BASELINE_SUMMARY['WebSearch']['CCR'] / 4.0, 0.0, BASELINE_SUMMARY['WebSearch']['MQR'] / 4.0, 1 - 0.667, BASELINE_SUMMARY['WebSearch']['CPI']],
        'BM Agent': bm_values,
    }

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    for method in methods:
        values = method_values[method] + method_values[method][:1]
        ax.plot(angles, values, linewidth=2.5, marker='o', markersize=7, label=method, color=METHOD_COLORS[method])
        ax.fill(angles, values, alpha=0.12, color=METHOD_COLORS[method])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=13, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', bbox_to_anchor=(1.28, 1.15), fontsize=11)
    ax.set_title('Figure 1. Multi-metric overview across four methods', fontsize=15, fontweight='bold', pad=25)
    save_figure(fig, 'Figure1_multimetric_overview')


def plot_figure2_patient_heatmap(patient_df):
    plot_df = patient_df.copy()
    plot_df['CCR_norm'] = plot_df['ccr'] / 4.0
    plot_df['MQR_norm'] = plot_df['mqr'] / 4.0
    plot_df['One_minus_CER'] = 1 - plot_df['cer']
    matrix = plot_df[['CCR_norm', 'ptr', 'MQR_norm', 'One_minus_CER', 'cpi']].to_numpy()
    row_labels = [f"{row.patient_id}\n({row.case})" for row in plot_df.itertuples()]
    col_labels = ['CCR/4', 'PTR', 'MQR/4', '1-CER', 'CPI']

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels, fontsize=12, fontweight='bold')
    ax.set_yticklabels(row_labels, fontsize=10)
    ax.set_title('Figure 2. Patient-level normalized performance matrix', fontsize=15, fontweight='bold', pad=16)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax.text(j, i, f'{value:.2f}', ha='center', va='center', color='black', fontsize=9, fontweight='bold')

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Score (0-1)', fontsize=11)
    save_figure(fig, 'Figure2_patient_matrix')


def plot_figure3_cpi_ranking(patient_df, stats):
    ranked = patient_df.sort_values('cpi', ascending=False).reset_index(drop=True)
    colors = [METHOD_COLORS['BM Agent']] * len(ranked)

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(ranked['patient_id'], ranked['cpi'], color=colors, alpha=0.85, edgecolor='black', linewidth=1)
    ax.axhline(stats['CPI']['mean'], color='#E74C3C', linestyle='--', linewidth=2, label=f"Mean CPI = {stats['CPI']['mean']:.3f}")
    ax.set_ylim(0.8, 1.02)
    ax.set_ylabel('CPI', fontsize=12, fontweight='bold')
    ax.set_title('Figure 3. Patient-level CPI ranking', fontsize=15, fontweight='bold')
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    ax.legend(loc='lower left', fontsize=10)

    for bar, case, value in zip(bars, ranked['case'], ranked['cpi']):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.004, f'{case}\n{value:.3f}', ha='center', va='bottom', fontsize=9)

    save_figure(fig, 'Figure3_cpi_ranking')


def plot_figure4_efficiency():
    methods = ['Direct LLM', 'RAG', 'WebSearch', 'BM Agent']
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    metrics = [
        ('latency', 'Latency (s)', 'Latency'),
        ('tokens', 'Total Tokens (K)', 'Token consumption'),
        ('tool_calls', 'Tool Calls', 'Tool calls'),
    ]

    for ax, (key, ylabel, title) in zip(axes, metrics):
        values = [EFFICIENCY_SUMMARY[m][key] for m in methods]
        bars = ax.bar(methods, values, color=[METHOD_COLORS[m] for m in methods], alpha=0.85)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(True, axis='y', linestyle='--', alpha=0.3)
        ax.tick_params(axis='x', rotation=25)
        for bar, value in zip(bars, values):
            label = f'{value:.1f}' if value else '0'
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02, label, ha='center', va='bottom', fontsize=9)

    fig.suptitle('Figure 4. Efficiency trade-offs across methods', fontsize=15, fontweight='bold', y=1.02)
    save_figure(fig, 'Figure4_efficiency_tradeoffs')


def plot_figure5_traceability_support(stats):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ptr_counts = [8, 1, 0]
    ptr_labels = ['PTR=1.0', 'PTR=0.9', 'PTR=0.0']
    ptr_colors = ['#2E8B57', '#F39C12', '#E74C3C']
    axes[0].bar(ptr_labels, ptr_counts, color=ptr_colors, alpha=0.85, edgecolor='black')
    axes[0].set_title('PTR distribution across 9 patients', fontsize=13, fontweight='bold')
    axes[0].set_ylabel('Number of patients', fontsize=11)
    axes[0].grid(True, axis='y', linestyle='--', alpha=0.3)
    for x, y in zip(ptr_labels, ptr_counts):
        axes[0].text(x, y + 0.1, str(y), ha='center', va='bottom', fontsize=10, fontweight='bold')

    citation_labels = list(CITATION_BREAKDOWN.keys())
    citation_values = list(CITATION_BREAKDOWN.values())
    wedges, texts, autotexts = axes[1].pie(
        citation_values,
        labels=citation_labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=['#4682B4', '#9B59B6', '#2E8B57'],
        wedgeprops={'edgecolor': 'white', 'linewidth': 1},
    )
    axes[1].set_title('Mean traceable evidence composition', fontsize=13, fontweight='bold')

    fig.suptitle(
        f"Figure 5. Traceability support for BM Agent (mean PTR={stats['PTR']['mean']:.3f})",
        fontsize=15,
        fontweight='bold',
        y=1.02,
    )
    save_figure(fig, 'Figure5_traceability_support')


def plot_figure6_patient_lines(patient_df):
    ordered = patient_df.copy()
    x = np.arange(len(ordered))

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    metrics = [
        ('cpi', 'CPI', (0.82, 1.01)),
        ('ccr', 'CCR (0-4)', (2.6, 4.0)),
        ('ptr', 'PTR', (0.88, 1.01)),
        ('mqr', 'MQR (0-4)', (3.6, 4.05)),
    ]

    for ax, (field, title, ylim) in zip(axes.flatten(), metrics):
        ax.plot(x, ordered[field], '-o', color=METHOD_COLORS['BM Agent'], linewidth=2.5, markersize=7, markerfacecolor='white', markeredgewidth=2)
        ax.set_xticks(x)
        ax.set_xticklabels(ordered['case'], rotation=45, ha='right')
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_ylim(*ylim)
        ax.grid(True, linestyle='--', alpha=0.3)
        mean_value = ordered[field].mean()
        ax.axhline(mean_value, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.7)
        ax.text(len(x) - 0.4, mean_value, f'{mean_value:.3f}', ha='right', va='bottom', fontsize=9, color='#E74C3C')

    fig.suptitle('Figure 6. Patient-level BM Agent metric profiles', fontsize=15, fontweight='bold', y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save_figure(fig, 'Figure6_patient_profiles')


def main():
    patient_df, stats, raw_data = load_final_metrics()
    plot_figure1_overview(patient_df, stats)
    plot_figure2_patient_heatmap(patient_df)
    plot_figure3_cpi_ranking(patient_df, stats)
    plot_figure4_efficiency()
    plot_figure5_traceability_support(stats)
    plot_figure6_patient_lines(patient_df)
    print(f'Figures saved to: {FINAL_FIGURES_DIR}')


if __name__ == '__main__':
    main()
