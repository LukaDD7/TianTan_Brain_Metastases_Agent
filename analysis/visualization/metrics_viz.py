#!/usr/bin/env python3
"""
Visualization Module for Brain Metastases MDT Evaluation
生成学术规范的可视化图表
"""

import os
import sys
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
from typing import Dict, List
from pathlib import Path

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class MetricsVisualizer:
    """
    指标可视化器 - 生成学术规范的图表
    """

    def __init__(self, output_dir: str = "analysis/visualization"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_radar_chart(self, results: Dict[str, List[Dict]], save: bool = True) -> plt.Figure:
        """
        雷达图 - 4种方法在CCR/PTR/MQR/CPI上的对比

        学术规范：
        - 使用不同颜色和线型区分方法
        - 添加图例和标题
        - 保存为高分辨率PDF（用于论文）
        """
        # 指标名称
        categories = ['CCR', 'PTR', 'MQR', 'CPI']
        num_vars = len(categories)

        # 计算角度
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # 闭合

        # 创建图形
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

        # TODO: 从results计算实际均值
        # 示例数据（占位符）
        method_scores = {
            "Direct LLM": [0.6, 0.2, 0.7, 0.5],
            "RAG": [0.7, 0.5, 0.75, 0.65],
            "WebSearch": [0.65, 0.4, 0.7, 0.6],
            "BM Agent": [0.95, 1.0, 0.9, 0.95]  # PLACEHOLDER
        }

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        line_styles = ['-', '--', '-.', ':']

        for i, (method, scores) in enumerate(method_scores.items()):
            scores += scores[:1]  # 闭合
            ax.plot(angles, scores, line_styles[i], linewidth=2,
                   label=method, color=colors[i])
            ax.fill(angles, scores, alpha=0.15, color=colors[i])

        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=12)
        ax.set_ylim(0, 1)

        # 添加网格和图例
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

        plt.title('Multi-dimensional Performance Comparison\n(CCR/PTR/MQR/CPI)',
                 fontsize=14, pad=20)

        if save:
            plt.savefig(f"{self.output_dir}/radar_chart.pdf",
                       bbox_inches='tight', dpi=300)
            plt.savefig(f"{self.output_dir}/radar_chart.png",
                       bbox_inches='tight', dpi=300)

        return fig

    def plot_token_usage(self, results: Dict[str, List[Dict]], save: bool = True) -> plt.Figure:
        """
        Token消耗对比 - 箱线图

        学术规范：
        - 显示中位数、四分位数、异常值
        - 不同方法使用不同颜色
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        metrics = [
            ('Input Tokens', 'input'),
            ('Output Tokens', 'output'),
            ('Total Tokens', 'total')
        ]

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

        for idx, (title, key) in enumerate(metrics):
            ax = axes[idx]

            # TODO: 从results提取实际token数据
            # 示例数据（占位符）
            data = [
                [1000, 1200, 1100, 1300, 1250],  # Direct LLM
                [3000, 3200, 3100, 3400, 3300],  # RAG
                [2000, 2500, 2300, 2600, 2400],  # WebSearch
                [1500, 1800, 1700, 2000, 1900]   # BM Agent (PLACEHOLDER)
            ]

            bp = ax.boxplot(data, labels=['Direct LLM', 'RAG', 'WebSearch', 'BM Agent'],
                           patch_artist=True)

            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)

            ax.set_ylabel('Token Count', fontsize=11)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.grid(True, axis='y', alpha=0.3)

        plt.suptitle('Token Usage Comparison Across Methods',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()

        if save:
            plt.savefig(f"{self.output_dir}/token_usage.pdf",
                       bbox_inches='tight', dpi=300)
            plt.savefig(f"{self.output_dir}/token_usage.png",
                       bbox_inches='tight', dpi=300)

        return fig

    def plot_latency_comparison(self, results: Dict[str, List[Dict]], save: bool = True) -> plt.Figure:
        """
        响应时间对比 - 柱状图（均值+标准差）
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        methods = ['Direct LLM', 'RAG', 'WebSearch', 'BM Agent']

        # TODO: 从results提取实际延迟数据
        # 示例数据（占位符）
        means = [5000, 15000, 25000, 12000]  # ms
        stds = [1000, 2000, 5000, 3000]

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

        bars = ax.bar(methods, means, yerr=stds, capsize=5,
                     color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

        ax.set_ylabel('Latency (ms)', fontsize=12)
        ax.set_title('Response Latency Comparison\n(Mean ± SD)', fontsize=14, fontweight='bold')
        ax.grid(True, axis='y', alpha=0.3)

        # 在柱子上添加数值标签
        for bar, mean in zip(bars, means):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{mean/1000:.1f}s',
                   ha='center', va='bottom', fontsize=10)

        plt.tight_layout()

        if save:
            plt.savefig(f"{self.output_dir}/latency_comparison.pdf",
                       bbox_inches='tight', dpi=300)
            plt.savefig(f"{self.output_dir}/latency_comparison.png",
                       bbox_inches='tight', dpi=300)

        return fig

    def plot_heatmap(self, results: Dict[str, List[Dict]], save: bool = True) -> plt.Figure:
        """
        热力图 - 患者×方法的指标矩阵
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        # TODO: 从results构建实际热力图数据
        # 示例：CPI热力图
        patients = [f'Case{i}' for i in range(1, 10)]
        methods = ['Direct LLM', 'RAG', 'WebSearch', 'BM Agent']

        # 示例数据（占位符）
        data = np.random.rand(9, 4) * 0.5 + 0.3
        data[:, 3] = np.random.rand(9) * 0.1 + 0.85  # BM Agent higher

        im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

        # 设置刻度
        ax.set_xticks(np.arange(len(methods)))
        ax.set_yticks(np.arange(len(patients)))
        ax.set_xticklabels(methods, fontsize=11)
        ax.set_yticklabels(patients, fontsize=11)

        # 添加数值标签
        for i in range(len(patients)):
            for j in range(len(methods)):
                text = ax.text(j, i, f'{data[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=9)

        ax.set_title('CPI Heatmap: Patient × Method', fontsize=14, fontweight='bold', pad=20)
        plt.colorbar(im, ax=ax, label='CPI Score')

        plt.tight_layout()

        if save:
            plt.savefig(f"{self.output_dir}/cpi_heatmap.pdf",
                       bbox_inches='tight', dpi=300)
            plt.savefig(f"{self.output_dir}/cpi_heatmap.png",
                       bbox_inches='tight', dpi=300)

        return fig

    def plot_citation_breakdown(self, results: Dict[str, List[Dict]], save: bool = True) -> plt.Figure:
        """
        引用来源分布 - 堆叠柱状图
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        methods = ['Direct LLM', 'RAG', 'WebSearch', 'BM Agent']

        # TODO: 从results提取实际引用数据
        # 示例数据（占位符）
        categories = ['Fully Traceable', 'Partially Traceable', 'Non-traceable']
        data = np.array([
            [0.1, 0.3, 0.6],   # Direct LLM
            [0.4, 0.4, 0.2],   # RAG
            [0.3, 0.3, 0.4],   # WebSearch
            [0.95, 0.05, 0.0]  # BM Agent
        ])

        colors = ['#2ECC71', '#F39C12', '#E74C3C']

        bottom = np.zeros(len(methods))
        for i, (category, color) in enumerate(zip(categories, colors)):
            ax.bar(methods, data[:, i], bottom=bottom, label=category, color=color, alpha=0.8)
            bottom += data[:, i]

        ax.set_ylabel('Proportion', fontsize=12)
        ax.set_title('Citation Traceability Distribution', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.set_ylim(0, 1)

        plt.tight_layout()

        if save:
            plt.savefig(f"{self.output_dir}/citation_breakdown.pdf",
                       bbox_inches='tight', dpi=300)
            plt.savefig(f"{self.output_dir}/citation_breakdown.png",
                       bbox_inches='tight', dpi=300)

        return fig

    def generate_all_plots(self, results: Dict[str, List[Dict]]):
        """生成所有图表"""
        print("\nGenerating visualizations...")

        print("  1. Radar chart (CCR/PTR/MQR/CPI)")
        self.plot_radar_chart(results)

        print("  2. Token usage comparison")
        self.plot_token_usage(results)

        print("  3. Latency comparison")
        self.plot_latency_comparison(results)

        print("  4. CPI heatmap")
        self.plot_heatmap(results)

        print("  5. Citation traceability breakdown")
        self.plot_citation_breakdown(results)

        print(f"\nAll plots saved to: {self.output_dir}/")
        print("  - radar_chart.pdf/png")
        print("  - token_usage.pdf/png")
        print("  - latency_comparison.pdf/png")
        print("  - cpi_heatmap.pdf/png")
        print("  - citation_breakdown.pdf/png")


def main():
    """测试可视化"""
    print("="*60)
    print("Visualization Generator Test")
    print("="*60)

    visualizer = MetricsVisualizer()

    # 测试数据（占位符）
    test_results = {
        "direct_llm": [],
        "rag": [],
        "websearch": [],
        "bm_agent": []
    }

    visualizer.generate_all_plots(test_results)

    print("\n" + "="*60)
    print("Visualization test complete!")
    print("="*60)


if __name__ == "__main__":
    main()
