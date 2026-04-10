#!/usr/bin/env python3
"""
效率指标可视化 - 4 Methods Comparison
生成日期: 2026-04-10

功能: 基于最新效率指标生成4种方法的对比可视化图表
输入: analysis/efficiency_metrics_v2.json
输出: analysis/final_figures/efficiency_*.png
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / 'final_figures'
OUTPUT_DIR.mkdir(exist_ok=True)

# 加载数据
with open(ROOT / 'efficiency_metrics_v2.json') as f:
    data = json.load(f)

# 准备数据
methods = ['Direct LLM V2', 'RAG V2', 'Web Search V2', 'BM Agent']
colors = ['#CD5C5C', '#4682B4', '#2E8B57', '#DAA520']

# 提取统计数据
stats = data['summary']

# 1. 延迟对比图
fig, ax = plt.subplots(figsize=(10, 6))
latencies = [stats[m]['latency']['mean']/1000 if stats[m]['latency'] else 0 for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]
latencies[3] = 0  # BM Agent无延迟数据
lat_stds = [stats[m]['latency']['std']/1000 if stats[m]['latency'] else 0 for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]
lat_stds[3] = 0

x = np.arange(len(methods))
bars = ax.bar(x, latencies, yerr=lat_stds, capsize=5, color=colors, alpha=0.8, edgecolor='black')
ax.set_ylabel('Latency (seconds)', fontsize=12)
ax.set_title('End-to-End Latency Comparison (Mean±SD)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(methods, rotation=15, ha='right')
ax.set_ylim(0, max(latencies)*1.2)
for i, (v, s) in enumerate(zip(latencies, lat_stds)):
    if v > 0:
        ax.text(i, v + s + 5, f'{v:.1f}±{s:.1f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'Figure_E1_Latency_Comparison.png', dpi=300, bbox_inches='tight')
plt.savefig(OUTPUT_DIR / 'Figure_E1_Latency_Comparison.pdf', bbox_inches='tight')
plt.close()
print("✅ Figure_E1_Latency_Comparison.png/pdf saved")

# 2. Token消耗对比图
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 输入Tokens
input_tokens = [stats[m]['input_tokens']['mean']/1000 for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]
input_stds = [stats[m]['input_tokens']['std']/1000 for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]

ax = axes[0]
bars = ax.bar(x, input_tokens, yerr=input_stds, capsize=5, color=colors, alpha=0.8, edgecolor='black')
ax.set_ylabel('Input Tokens (K)', fontsize=12)
ax.set_title('Input Token Consumption (Mean±SD)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(methods, rotation=15, ha='right')
ax.set_yscale('log')  # 使用对数刻度因为BM Agent数值太大
for i, (v, s) in enumerate(zip(input_tokens, input_stds)):
    ax.text(i, v * 1.2, f'{v:.1f}±{s:.1f}', ha='center', va='bottom', fontsize=8)

# 输出Tokens
output_tokens = [stats[m]['output_tokens']['mean']/1000 for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]
output_stds = [stats[m]['output_tokens']['std']/1000 for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]

ax = axes[1]
bars = ax.bar(x, output_tokens, yerr=output_stds, capsize=5, color=colors, alpha=0.8, edgecolor='black')
ax.set_ylabel('Output Tokens (K)', fontsize=12)
ax.set_title('Output Token Consumption (Mean±SD)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(methods, rotation=15, ha='right')
for i, (v, s) in enumerate(zip(output_tokens, output_stds)):
    ax.text(i, v + s + 0.2, f'{v:.1f}±{s:.1f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'Figure_E2_Token_Consumption.png', dpi=300, bbox_inches='tight')
plt.savefig(OUTPUT_DIR / 'Figure_E2_Token_Consumption.pdf', bbox_inches='tight')
plt.close()
print("✅ Figure_E2_Token_Consumption.png/pdf saved")

# 3. I/O比值对比图
fig, ax = plt.subplots(figsize=(10, 6))
io_ratios = [stats[m]['io_ratio'] for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]

bars = ax.bar(x, io_ratios, color=colors, alpha=0.8, edgecolor='black')
ax.set_ylabel('I/O Ratio (Input/Output)', fontsize=12)
ax.set_title('Input/Output Token Ratio Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(methods, rotation=15, ha='right')
ax.set_yscale('log')  # 对数刻度
for i, v in enumerate(io_ratios):
    ax.text(i, v * 1.2, f'{v:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'Figure_E3_IO_Ratio.png', dpi=300, bbox_inches='tight')
plt.savefig(OUTPUT_DIR / 'Figure_E3_IO_Ratio.pdf', bbox_inches='tight')
plt.close()
print("✅ Figure_E3_IO_Ratio.png/pdf saved")

# 4. 环境调用对比图
fig, ax = plt.subplots(figsize=(10, 6))
env_calls = [stats[m]['env_calls']['mean'] for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]
env_stds = [stats[m]['env_calls']['std'] for m in ['Direct LLM', 'RAG V2', 'Web Search V2', 'BM Agent']]

bars = ax.bar(x, env_calls, yerr=env_stds, capsize=5, color=colors, alpha=0.8, edgecolor='black')
ax.set_ylabel('Environment Calls (count)', fontsize=12)
ax.set_title('External Environment Calls (Mean±SD)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(methods, rotation=15, ha='right')
for i, (v, s) in enumerate(zip(env_calls, env_stds)):
    ax.text(i, v + s + 2, f'{v:.1f}±{s:.1f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'Figure_E4_Env_Calls.png', dpi=300, bbox_inches='tight')
plt.savefig(OUTPUT_DIR / 'Figure_E4_Env_Calls.pdf', bbox_inches='tight')
plt.close()
print("✅ Figure_E4_Env_Calls.png/pdf saved")

# 5. 综合效率雷达图
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

# 归一化数据用于雷达图 (0-1范围)
categories = ['Speed\n(1/Latency)', 'Token\nEfficiency', 'Output\nQuality', 'Traceability']
N = len(categories)

# 为每种方法计算归一化值
method_values = {
    'Direct LLM': [1/97.10, 1/2.24, 5.20/10, 0.00],  # 归一化
    'RAG V2': [1/137.49, 1/3.92, 6.62/10, 0.13],
    'Web Search': [1/113.71, 1/40.25, 5.51/10, 0.39],
    'BM Agent': [0, 1/690.22, 7.67/10, 0.98],
}

# 归一化到0-1
for method in method_values:
    vals = method_values[method]
    vals[0] = vals[0] / (1/97.10)  # 相对于最快
    vals[1] = vals[1] / (1/2.24)   # 相对于最少token
    vals[2] = vals[2]  # 已经归一化
    vals[3] = vals[3]  # 已经0-1

angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

for method, color in zip(['Direct LLM', 'RAG V2', 'Web Search', 'BM Agent'], colors):
    values = method_values[method]
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=method, color=color)
    ax.fill(angles, values, alpha=0.15, color=color)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 1)
ax.set_title('Efficiency Metrics Radar Chart (Normalized)', fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'Figure_E5_Efficiency_Radar.png', dpi=300, bbox_inches='tight')
plt.savefig(OUTPUT_DIR / 'Figure_E5_Efficiency_Radar.pdf', bbox_inches='tight')
plt.close()
print("✅ Figure_E5_Efficiency_Radar.png/pdf saved")

print("\n" + "="*60)
print("效率指标可视化生成完成!")
print("="*60)
print(f"输出目录: {OUTPUT_DIR}")
print("\n生成的图表:")
print("  1. Figure_E1_Latency_Comparison.png/pdf - 延迟对比")
print("  2. Figure_E2_Token_Consumption.png/pdf - Token消耗对比")
print("  3. Figure_E3_IO_Ratio.png/pdf - I/O比值对比")
print("  4. Figure_E4_Env_Calls.png/pdf - 环境调用对比")
print("  5. Figure_E5_Efficiency_Radar.png/pdf - 综合效率雷达图")
