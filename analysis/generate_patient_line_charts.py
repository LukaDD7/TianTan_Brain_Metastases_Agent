#!/usr/bin/env python3
"""
患者级别关键指标折线图生成脚本
Patient-Level Key Metrics Line Chart Generation
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
output_dir = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/analysis/final_figures")
output_dir.mkdir(exist_ok=True)

# ========== 患者级别数据 (严格审计后) ==========

# 患者顺序 (Case5缺失)
patient_ids = ['648772', '640880', '868183', '665548', '638114', '612908', '605525', '708387', '747724']
case_labels = ['Case1', 'Case2', 'Case3', 'Case4', 'Case6', 'Case7', 'Case8', 'Case9', 'Case10']
x_pos = np.arange(len(patient_ids))

# BM Agent 数据
bm_ccr = [3.4, 3.4, 3.7, 2.8, 3.2, 3.3, 3.4, 3.6, 3.5]
bm_ptr = [1.000, 1.000, 1.000, 1.000, 0.900, 1.000, 1.000, 1.000, 1.000]
bm_mqr = [4.0, 3.9, 4.0, 3.7, 3.7, 3.9, 4.0, 4.0, 3.9]
bm_cpi = [0.890, 0.910, 0.920, 0.780, 0.860, 0.890, 0.910, 0.930, 0.900]

# Enhanced RAG 数据 (8例患者, Case8缺失)
rag_patient_indices = [0, 1, 2, 3, 4, 5, 7, 8]  # 对应Case1-4,6,7,9,10
rag_ccr = [2.4, 2.2, 2.4, 2.4, 2.2, 2.4, 2.8, 2.8]
rag_ptr = [0.676, 0.719, 0.708, 0.778, 0.692, 0.867, 0.750, 0.929]
rag_mqr = [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]
rag_cpi = [0.779, 0.772, 0.787, 0.804, 0.766, 0.827, 0.833, 0.877]

# 颜色定义
bm_color = '#2E8B57'  # 绿色
rag_color = '#4682B4'  # 蓝色
mean_line_color = '#E74C3C'  # 红色

def plot_patient_line_charts():
    """患者级别关键指标折线图 (4子图)"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 绘制单个指标的函数
    def plot_metric(ax, title, ylabel, bm_data, rag_data, ylim, show_legend=False):
        # BM Agent 折线
        ax.plot(x_pos, bm_data, '-o', color=bm_color, linewidth=2.5,
                markersize=8, label='BM Agent', markerfacecolor='white',
                markeredgewidth=2, markeredgecolor=bm_color)

        # Enhanced RAG 折线
        rag_x = [x_pos[i] for i in rag_patient_indices]
        ax.plot(rag_x, rag_data, '-s', color=rag_color, linewidth=2.5,
                markersize=8, label='Enhanced RAG', markerfacecolor='white',
                markeredgewidth=2, markeredgecolor=rag_color)

        # 均值线
        bm_mean = np.mean(bm_data)
        ax.axhline(y=bm_mean, color=bm_color, linestyle='--', alpha=0.5, linewidth=1.5)
        ax.text(len(x_pos)-0.5, bm_mean, f'{bm_mean:.3f}',
                color=bm_color, fontsize=10, va='center', ha='right')

        if rag_data:
            rag_mean = np.mean(rag_data)
            ax.axhline(y=rag_mean, color=rag_color, linestyle='--', alpha=0.5, linewidth=1.5)
            ax.text(len(x_pos)-0.5, rag_mean, f'{rag_mean:.3f}',
                    color=rag_color, fontsize=10, va='center', ha='right')

        ax.set_xticks(x_pos)
        ax.set_xticklabels(case_labels, rotation=45, ha='right')
        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylim(ylim)
        ax.grid(True, alpha=0.3, linestyle='--')
        if show_legend:
            ax.legend(loc='best', fontsize=10)

        # 标注极值
        bm_max_idx = np.argmax(bm_data)
        bm_min_idx = np.argmin(bm_data)
        ax.annotate(f'{bm_data[bm_max_idx]:.3f}',
                    xy=(x_pos[bm_max_idx], bm_data[bm_max_idx]),
                    xytext=(0, 10), textcoords='offset points',
                    ha='center', fontsize=9, color=bm_color, fontweight='bold')
        ax.annotate(f'{bm_data[bm_min_idx]:.3f}',
                    xy=(x_pos[bm_min_idx], bm_data[bm_min_idx]),
                    xytext=(0, -15), textcoords='offset points',
                    ha='center', fontsize=9, color=bm_color, fontweight='bold')

    # Subplot 1: CPI
    plot_metric(axes[0, 0], 'Comprehensive Performance Index (CPI)', 'CPI (0-1)',
                bm_cpi, rag_cpi, (0.7, 1.0), show_legend=True)

    # Subplot 2: CCR
    plot_metric(axes[0, 1], 'Clinical Consistency Rate (CCR)', 'CCR (0-4)',
                bm_ccr, rag_ccr, (1.5, 4.0))

    # Subplot 3: PTR
    plot_metric(axes[1, 0], 'Physical Traceability Rate (PTR)', 'PTR (0-1)',
                bm_ptr, rag_ptr, (0.5, 1.05))

    # Subplot 4: MQR
    plot_metric(axes[1, 1], 'MDT Quality Rate (MQR)', 'MQR (0-4)',
                bm_mqr, rag_mqr, (3.5, 4.1))

    plt.suptitle('Patient-Level Key Metrics Comparison\n(BM Agent vs Enhanced RAG)',
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    plt.savefig(output_dir / 'Figure8_patient_line_charts.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'Figure8_patient_line_charts.pdf', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Figure 8: Patient-level line charts generated")

def plot_cpi_comparison_detailed():
    """CPI详细对比图 (单独大图)"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # BM Agent
    ax.plot(x_pos, bm_cpi, '-o', color=bm_color, linewidth=3,
            markersize=10, label='BM Agent', markerfacecolor='white',
            markeredgewidth=2.5, markeredgecolor=bm_color)

    # Enhanced RAG
    rag_x = [x_pos[i] for i in rag_patient_indices]
    ax.plot(rag_x, rag_cpi, '-s', color=rag_color, linewidth=3,
            markersize=10, label='Enhanced RAG', markerfacecolor='white',
            markeredgewidth=2.5, markeredgecolor=rag_color)

    # 均值线和区域
    bm_mean = np.mean(bm_cpi)
    rag_mean = np.mean(rag_cpi)

    ax.axhline(y=bm_mean, color=bm_color, linestyle='--', alpha=0.5, linewidth=2)
    ax.axhline(y=rag_mean, color=rag_color, linestyle='--', alpha=0.5, linewidth=2)

    # 填充均值差异区域
    ax.fill_between([-0.5, len(x_pos)-0.5], rag_mean, bm_mean,
                    alpha=0.1, color='green', label=f'CPI Advantage (+{bm_mean-rag_mean:.3f})')

    # 标注每个点
    for i, (x, y) in enumerate(zip(x_pos, bm_cpi)):
        ax.annotate(f'{y:.3f}', xy=(x, y), xytext=(0, 15),
                   textcoords='offset points', ha='center', fontsize=9,
                   color=bm_color, fontweight='bold')

    for i, (idx, y) in enumerate(zip(rag_patient_indices, rag_cpi)):
        ax.annotate(f'{y:.3f}', xy=(x_pos[idx], y), xytext=(0, -20),
                   textcoords='offset points', ha='center', fontsize=9,
                   color=rag_color, fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'{pid}\n({case})' for pid, case in zip(patient_ids, case_labels)],
                       fontsize=9)
    ax.set_ylabel('CPI Score (0-1)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Patient ID (Case)', fontsize=12, fontweight='bold')
    ax.set_title('CPI Comparison Across Individual Patients\n' +
                 f'BM Agent: {bm_mean:.3f} ± {np.std(bm_cpi, ddof=1):.3f} vs ' +
                 f'Enhanced RAG: {rag_mean:.3f} ± {np.std(rag_cpi, ddof=1):.3f}',
                 fontsize=14, fontweight='bold')
    ax.set_ylim(0.70, 0.98)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='lower right', fontsize=11)

    plt.tight_layout()
    plt.savefig(output_dir / 'Figure9_cpi_detailed.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'Figure9_cpi_detailed.pdf', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Figure 9: CPI detailed comparison generated")

def main():
    """主函数"""
    print("="*60)
    print("患者级别折线图生成")
    print("="*60)
    print(f"\n输出目录: {output_dir}\n")

    plot_patient_line_charts()
    plot_cpi_comparison_detailed()

    print("\n" + "="*60)
    print("患者级别折线图生成完成!")
    print("="*60)
    print("\n生成的文件:")
    print("  - Figure8_patient_line_charts.{png,pdf}")
    print("  - Figure9_cpi_detailed.{png,pdf}")

if __name__ == "__main__":
    main()
