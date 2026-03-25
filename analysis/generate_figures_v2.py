#!/usr/bin/env python3
"""
Generate two high-quality figures:
1. Dual-axis Bar/Line Chart: System 2 Thinking Depth
2. Multi-baseline Performance Trend Line Chart (redesigned)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set academic style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['figure.dpi'] = 300

# Create output directory
output_dir = '/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/analysis/final_figures'

# ============================================================================
# FIGURE 1: Dual-axis Bar/Line Chart - System 2 Thinking Depth
# ============================================================================

fig1, ax1 = plt.subplots(figsize=(12, 8))

# Data
methods = ['Direct LLM', 'RAG', 'WebSearch', 'BM Agent']
x = np.arange(len(methods))

# Token consumption (in thousands)
tokens = [7.0, 8.8, 42.3, 578.7]  # ×10³
# Tool calls: Direct LLM=0, RAG=0, WebSearch=2 (web search calls), BM Agent=41.6
tool_calls = [0, 0, 2.0, 41.6]

# Colors
colors = ['#95a5a6', '#e67e22', '#27ae60', '#e74c3c']  # Last one is BM Agent - bright red
edge_colors = ['#7f8c8d', '#d35400', '#229954', '#c0392b']

# Left Y-axis: Token consumption (log scale)
ax1.set_xlabel('Technical Paradigm', fontsize=13, fontweight='bold')
ax1.set_ylabel('Total Token Consumption (×10³)', fontsize=13, color='#2c3e50', fontweight='bold')

bars = ax1.bar(x, tokens, width=0.6, color=colors, edgecolor=edge_colors, linewidth=2.5)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, tokens)):
    if i == 3:  # BM Agent
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.1,
                f'{val:.1f}K', ha='center', va='bottom', fontsize=14,
                fontweight='bold', color='#c0392b')
        # Add highlight effect
        bar.set_edgecolor('#c0392b')
        bar.set_linewidth(4)
    else:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.1,
                f'{val:.1f}K', ha='center', va='bottom', fontsize=11,
                fontweight='bold', color='#2c3e50')

ax1.set_yscale('log')
ax1.set_ylim(1, 1500)
ax1.set_xticks(x)
ax1.set_xticklabels(methods, fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#2c3e50', labelsize=11)

# Add grid for log scale
ax1.grid(True, which="both", ls="-", alpha=0.2, axis='y')
ax1.set_axisbelow(True)

# Right Y-axis: Tool call frequency
ax2 = ax1.twinx()
ax2.set_ylabel('Tool Call Frequency', fontsize=13, color='#8e44ad', fontweight='bold')

# Plot tool calls as line with markers
line = ax2.plot(x, tool_calls, '-o', color='#8e44ad', linewidth=3,
                markersize=12, markerfacecolor='#9b59b6',
                markeredgecolor='white', markeredgewidth=2, zorder=10)

# Add value labels for tool calls
for i, (xi, val) in enumerate(zip(x, tool_calls)):
    if val > 0:
        ax2.text(xi, val + 2.5, f'{val:.1f}', ha='center', va='bottom',
                fontsize=13, fontweight='bold', color='#8e44ad')

ax2.tick_params(axis='y', labelcolor='#8e44ad', labelsize=11)
ax2.set_ylim(0, 55)

# Add horizontal line at 0 for baseline methods
ax2.axhline(y=0, color='#95a5a6', linestyle='--', alpha=0.3, linewidth=1.5)

# Title with more space
fig1.suptitle('Figure 2: System 2 Thinking Depth - Token Consumption vs. Tool Orchestration',
              fontsize=15, fontweight='bold', y=0.98)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    mpatches.Patch(facecolor='#e74c3c', edgecolor='#c0392b', linewidth=3, label='Token Consumption (BM Agent)'),
    mpatches.Patch(facecolor='#95a5a6', edgecolor='#7f8c8d', label='Token Consumption (Baselines)'),
    Line2D([0], [0], color='#8e44ad', linewidth=3, marker='o', markersize=10,
           markerfacecolor='#9b59b6', label='Tool Call Frequency', linestyle='-')
]

ax1.legend(handles=legend_elements, loc='upper left', frameon=True,
          fancybox=True, shadow=True, fontsize=10)

# Add annotation for BM Agent
ax1.annotate('Deep System 2 Thinking:\n578K Tokens + 42 Tool Calls',
             xy=(3, 578.7), xytext=(2.2, 800),
             fontsize=11, ha='center', color='#c0392b', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffeaea', edgecolor='#e74c3c', linewidth=2),
             arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2))

plt.tight_layout()
plt.subplots_adjust(top=0.90)

# Save
fig1.savefig(f'{output_dir}/figure_token_tool_dual_axis.pdf', bbox_inches='tight', dpi=300)
fig1.savefig(f'{output_dir}/figure_token_tool_dual_axis.png', bbox_inches='tight', dpi=300)
print("Saved: figure_token_tool_dual_axis.pdf/png")

# ============================================================================
# FIGURE 2: Multi-baseline Performance Trend Line Chart (REDESIGNED)
# ============================================================================

fig2, ax3 = plt.subplots(figsize=(14, 8))

# Data: Case 1-10 (excluding Case5)
cases = ['Case 1', 'Case 2', 'Case 3', 'Case 4', 'Case 6', 'Case 7', 'Case 8', 'Case 9', 'Case 10']
x = np.arange(len(cases))

# BM Agent data
bm_agent_cpi = [0.901, 0.941, 0.991, 0.846, 0.974, 0.909, 0.937, 0.965, 0.940]
bm_agent_ccr = [3.2, 3.4, 3.9, 2.8, 3.7, 3.3, 3.4, 3.6, 3.5]

# Baseline methods (constant)
direct_llm_cpi = [0.42] * len(cases)
direct_llm_ccr = [1.5] * len(cases)
rag_cpi = [0.52] * len(cases)
rag_ccr = [2.0] * len(cases)
websearch_cpi = [0.57] * len(cases)
websearch_ccr = [2.2] * len(cases)

# Colors - higher contrast
color_bm_cpi = '#1e3a8a'  # Dark blue
color_bm_ccr = '#7c3aed'  # Purple
color_direct = '#9ca3af'  # Gray
color_rag = '#f97316'     # Orange
color_web = '#10b981'     # Emerald green

# Left Y-axis: CPI
ax3.set_xlabel('Patient Case', fontsize=13, fontweight='bold')
ax3.set_ylabel('CPI (0-1)', fontsize=13, color='#1e3a8a', fontweight='bold')

# Plot baseline CPI (light dashed)
ax3.plot(x, direct_llm_cpi, '--', color=color_direct, linewidth=2, alpha=0.7, label='Direct LLM')
ax3.plot(x, rag_cpi, '--', color=color_rag, linewidth=2, alpha=0.7, label='RAG')
ax3.plot(x, websearch_cpi, '--', color=color_web, linewidth=2, alpha=0.7, label='WebSearch')

# Plot BM Agent CPI (bold solid with stars)
ax3.plot(x, bm_agent_cpi, '-', color=color_bm_cpi, linewidth=4,
         marker='*', markersize=18, markerfacecolor='#3b82f6',
         markeredgecolor='#1e3a8a', markeredgewidth=2,
         label='BM Agent (CPI)', zorder=10)

# Add value labels for BM Agent CPI
for i, (xi, val) in enumerate(zip(x, bm_agent_cpi)):
    if i == 0 or i == 8 or val == max(bm_agent_cpi) or val == min(bm_agent_cpi):
        ax3.annotate(f'{val:.2f}', xy=(xi, val), xytext=(0, 12),
                    textcoords='offset points', ha='center',
                    fontsize=9, fontweight='bold', color=color_bm_cpi)

ax3.tick_params(axis='y', labelcolor=color_bm_cpi, labelsize=11)
ax3.set_ylim(0.3, 1.08)
ax3.set_xticks(x)
ax3.set_xticklabels(cases, fontsize=10)

# Right Y-axis: CCR
ax4 = ax3.twinx()
ax4.set_ylabel('CCR (0-4)', fontsize=13, color='#7c3aed', fontweight='bold')

# Plot baseline CCR (lighter dotted)
ax4.plot(x, direct_llm_ccr, ':', color=color_direct, linewidth=2, alpha=0.5)
ax4.plot(x, rag_ccr, ':', color=color_rag, linewidth=2, alpha=0.5)
ax4.plot(x, websearch_ccr, ':', color=color_web, linewidth=2, alpha=0.5)

# Plot BM Agent CCR (dashed with circles)
ax4.plot(x, bm_agent_ccr, '--', color=color_bm_ccr, linewidth=3,
         marker='o', markersize=10, markerfacecolor='#a78bfa',
         markeredgecolor='#7c3aed', markeredgewidth=2,
         label='BM Agent (CCR)', zorder=9, alpha=0.8)

ax4.tick_params(axis='y', labelcolor=color_bm_ccr, labelsize=11)
ax4.set_ylim(0.5, 4.3)

# Grid
ax3.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, axis='y')
ax3.set_axisbelow(True)

# Title with more space from legend
fig2.suptitle('Figure 1: Per-Patient CPI and CCR Trends Across Technical Paradigms',
              fontsize=15, fontweight='bold', y=0.96)

# Legend - positioned lower to avoid title overlap
lines1, labels1 = ax3.get_legend_handles_labels()
lines2, labels2 = ax4.get_legend_handles_labels()

# Custom legend with clearer distinction
from matplotlib.lines import Line2D
legend_elements = [
    # CPI items
    Line2D([0], [0], linestyle='-', color=color_bm_cpi, linewidth=3,
           marker='*', markersize=14, label='BM Agent CPI', markerfacecolor='#3b82f6'),
    Line2D([0], [0], linestyle='--', color=color_direct, linewidth=2, label='Direct LLM CPI'),
    Line2D([0], [0], linestyle='--', color=color_rag, linewidth=2, label='RAG CPI'),
    Line2D([0], [0], linestyle='--', color=color_web, linewidth=2, label='WebSearch CPI'),
    # Separator
    Line2D([0], [0], linestyle='none', label=''),
    # CCR items
    Line2D([0], [0], linestyle='--', color=color_bm_ccr, linewidth=3,
           marker='o', markersize=10, label='BM Agent CCR', markerfacecolor='#a78bfa', alpha=0.8),
    Line2D([0], [0], linestyle=':', color=color_direct, linewidth=2, label='Direct LLM CCR', alpha=0.5),
    Line2D([0], [0], linestyle=':', color=color_rag, linewidth=2, label='RAG CCR', alpha=0.5),
    Line2D([0], [0], linestyle=':', color=color_web, linewidth=2, label='WebSearch CCR', alpha=0.5),
]

ax3.legend(handles=legend_elements, loc='upper center',
          bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=True,
          fancybox=True, shadow=True, fontsize=10)

# Adjust layout to make room for legend
plt.tight_layout()
plt.subplots_adjust(top=0.91, bottom=0.22)

# Save
fig2.savefig(f'{output_dir}/figure_line_chart_trends_v2.pdf', bbox_inches='tight', dpi=300)
fig2.savefig(f'{output_dir}/figure_line_chart_trends_v2.png', bbox_inches='tight', dpi=300)
print("Saved: figure_line_chart_trends_v2.pdf/png")

print("\n" + "="*60)
print("FIGURES GENERATED SUCCESSFULLY")
print("="*60)
print("\nFigure 1: System 2 Thinking Depth")
print("  - Tokens: 7.0K / 8.8K / 42.3K / 578.7K")
print("  - Tool Calls: 0 / 0 / 2.0 / 41.6")
print("\nFigure 2: Performance Trends (v2 - redesigned)")
print("  - Higher contrast colors")
print("  - Legend moved below plot (no overlap)")
print("  - Better spacing")
print("="*60)
