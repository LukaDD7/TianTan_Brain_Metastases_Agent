#!/usr/bin/env python3
"""
Generate final figures for paper submission:
Figure 8: Patient-level multi-dimensional metrics (Radar/Heatmap)
Figure 9: Tool call hierarchy structure + Token dual-axis chart
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd

# Set academic style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['figure.dpi'] = 300

output_dir = '/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/analysis/final_figures'

# ============================================================================
# FIGURE 8: Patient-Level Multi-Dimensional Metrics Radar Chart
# ============================================================================

fig8, axes = plt.subplots(3, 3, figsize=(16, 16), subplot_kw=dict(polar=True))
fig8.suptitle('Figure 8: Patient-Level Multi-Dimensional Quality Assessment (CPI/CCR/PTR/MQR)',
              fontsize=16, fontweight='bold', y=0.98)

# Patient data from 论文Results章节_Word粘贴版.md
patients = [
    {'id': '868183', 'case': 'Case3', 'type': 'Lung (SMARCA4+)', 'CPI': 0.991, 'CCR': 3.9, 'PTR': 1.0, 'MQR': 4.0},
    {'id': '708387', 'case': 'Case9', 'type': 'Lung (MET amp)', 'CPI': 0.965, 'CCR': 3.6, 'PTR': 1.0, 'MQR': 4.0},
    {'id': '638114', 'case': 'Case6', 'type': 'Breast', 'CPI': 0.974, 'CCR': 3.7, 'PTR': 1.0, 'MQR': 4.0},
    {'id': '640880', 'case': 'Case2', 'type': 'Lung', 'CPI': 0.941, 'CCR': 3.4, 'PTR': 1.0, 'MQR': 3.9},
    {'id': '747724', 'case': 'Case10', 'type': 'Breast (HER2+)', 'CPI': 0.940, 'CCR': 3.5, 'PTR': 1.0, 'MQR': 3.9},
    {'id': '605525', 'case': 'Case8', 'type': 'CRC (KRAS G12V)', 'CPI': 0.937, 'CCR': 3.4, 'PTR': 1.0, 'MQR': 4.0},
    {'id': '648772', 'case': 'Case1', 'type': 'Melanoma', 'CPI': 0.901, 'CCR': 3.2, 'PTR': 1.0, 'MQR': 3.7},
    {'id': '612908', 'case': 'Case7', 'type': 'Lung (EGFR+)', 'CPI': 0.909, 'CCR': 3.3, 'PTR': 1.0, 'MQR': 3.7},
    {'id': '665548', 'case': 'Case4', 'type': 'Gastric (HER2-low)', 'CPI': 0.846, 'CCR': 2.8, 'PTR': 1.0, 'MQR': 3.7},
]

categories = ['CPI\n(0-1)', 'CCR\n(0-4)', 'PTR\n(0-1)', 'MQR\n(0-4)']
num_vars = len(categories)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

# Color scheme based on CPI performance
def get_color(cpi):
    if cpi >= 0.95: return '#27ae60'  # Excellent - Green
    elif cpi >= 0.90: return '#2980b9'  # Good - Blue
    elif cpi >= 0.85: return '#f39c12'  # Acceptable - Orange
    else: return '#e74c3c'  # Needs improvement - Red

for idx, (ax, patient) in enumerate(zip(axes.flat, patients)):
    # Normalize values to 0-1 scale for radar chart
    values = [
        patient['CPI'],
        patient['CCR'] / 4.0,  # Normalize CCR to 0-1
        patient['PTR'],
        patient['MQR'] / 4.0   # Normalize MQR to 0-1
    ]
    values += values[:1]  # Close the polygon

    color = get_color(patient['CPI'])

    # Plot
    ax.plot(angles, values, 'o-', linewidth=2.5, color=color, markersize=8)
    ax.fill(angles, values, alpha=0.25, color=color)

    # Customize
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0.25', '0.5', '0.75', '1.0'], size=8)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Title with CPI value
    ax.set_title(f"{patient['case']}\n{patient['id']} ({patient['type']})\nCPI={patient['CPI']:.3f}",
                 size=11, fontweight='bold', pad=15,
                 color=color if patient['CPI'] >= 0.95 else '#2c3e50')

plt.tight_layout()
plt.subplots_adjust(top=0.92)

fig8.savefig(f'{output_dir}/figure8_patient_radar_charts.pdf', bbox_inches='tight', dpi=300)
fig8.savefig(f'{output_dir}/figure8_patient_radar_charts.png', bbox_inches='tight', dpi=300)
print("Saved: figure8_patient_radar_charts.pdf/png")

# ============================================================================
# FIGURE 8 Alternative: Heatmap version (for overview)
# ============================================================================

fig8b, ax = plt.subplots(figsize=(12, 8))

# Prepare data for heatmap
patient_ids = [f"{p['case']}\n{p['id']}" for p in patients]
metrics = ['CPI', 'CCR', 'PTR', 'MQR']
data_matrix = np.array([[p['CPI'], p['CCR'], p['PTR'], p['MQR']] for p in patients])

# Normalize for visualization (CCR and MQR divided by 4)
data_normalized = data_matrix.copy().astype(float)
data_normalized[:, 1] /= 4.0  # CCR / 4
data_normalized[:, 3] /= 4.0  # MQR / 4

# Create heatmap
cmap = plt.cm.RdYlGn  # Red-Yellow-Green colormap
im = ax.imshow(data_normalized, cmap=cmap, aspect='auto', vmin=0.7, vmax=1.0)

# Set ticks
ax.set_xticks(np.arange(len(metrics)))
ax.set_yticks(np.arange(len(patient_ids)))
ax.set_xticklabels(metrics, fontsize=13, fontweight='bold')
ax.set_yticklabels(patient_ids, fontsize=11)

# Add value annotations
for i in range(len(patients)):
    for j in range(len(metrics)):
        if j == 0:  # CPI
            text = f"{data_matrix[i, j]:.3f}"
        elif j == 2:  # PTR
            text = f"{data_matrix[i, j]:.1f}"
        else:  # CCR, MQR
            text = f"{data_matrix[i, j]:.1f}"

        color = 'white' if data_normalized[i, j] < 0.85 or data_normalized[i, j] > 0.95 else 'black'
        ax.text(j, i, text, ha='center', va='center',
                fontsize=11, fontweight='bold', color=color)

# Colorbar
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('Normalized Score (0-1)', fontsize=12, fontweight='bold')

# Title and labels
ax.set_title('Figure 8 (Alternative): Patient-Level Performance Heatmap\n(CCR and MQR normalized to 0-1 scale)',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlabel('Quality Metrics', fontsize=13, fontweight='bold', labelpad=10)
ax.set_ylabel('Patient Cases', fontsize=13, fontweight='bold', labelpad=10)

# Add grid
ax.set_xticks(np.arange(len(metrics)+1)-.5, minor=True)
ax.set_yticks(np.arange(len(patients)+1)-.5, minor=True)
ax.grid(which="minor", color="black", linestyle='-', linewidth=1.5)
ax.tick_params(which="minor", size=0)

plt.tight_layout()
fig8b.savefig(f'{output_dir}/figure8b_patient_heatmap.pdf', bbox_inches='tight', dpi=300)
fig8b.savefig(f'{output_dir}/figure8b_patient_heatmap.png', bbox_inches='tight', dpi=300)
print("Saved: figure8b_patient_heatmap.pdf/png")

# ============================================================================
# FIGURE 9: Tool Call Hierarchy Structure (Sunburst-style Stacked Bar)
# ============================================================================

fig9, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Data from Table 7
fig9.suptitle('Figure 9: BM Agent System 2 Thinking Architecture',
              fontsize=16, fontweight='bold', y=0.98)

# Left: Tool Call Hierarchy (Stacked Bar)
tool_categories = ['Local\nGuidelines', 'PubMed\nSearch', 'OncoKB\nQuery', 'PDF\nVisual', 'Other\nTools']
tool_values = [23.1, 11.3, 2.0, 3.0, 2.2]
colors_tools = ['#3498db', '#27ae60', '#e67e22', '#9b59b6', '#95a5a6']

# Create horizontal stacked bar
left = 0
for cat, val, color in zip(tool_categories, tool_values, colors_tools):
    ax1.barh('Tool Calls', val, left=left, color=color, edgecolor='white', linewidth=2, height=0.6)
    # Add label
    if val > 3:
        ax1.text(left + val/2, 0, f'{val}', ha='center', va='center',
                fontsize=14, fontweight='bold', color='white')
    left += val

# Add category labels
left = 0
for cat, val in zip(tool_categories, tool_values):
    ax1.text(left + val/2, -0.4, cat, ha='center', va='top',
            fontsize=11, fontweight='bold', color='#2c3e50')
    left += val

ax1.set_xlim(0, 42)
ax1.set_ylim(-0.6, 0.5)
ax1.set_xlabel('Average Tool Calls per Patient (n=9)', fontsize=13, fontweight='bold')
ax1.set_title('Tool Call Hierarchy\n(Total: 41.6 ± 7.3 calls)', fontsize=14, fontweight='bold', pad=15)
ax1.set_yticks([])
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_visible(False)
ax1.grid(axis='x', alpha=0.3, linestyle='--')

# Add percentage annotations
percentages = [f'{v/sum(tool_values)*100:.0f}%' for v in tool_values]
left = 0
for cat, val, pct in zip(tool_categories, tool_values, percentages):
    ax1.text(left + val/2, 0.25, pct, ha='center', va='center',
            fontsize=10, fontweight='bold', color='white', alpha=0.8)
    left += val

# Right: Token Input/Output Ratio Comparison
methods = ['Direct LLM', 'RAG', 'WebSearch', 'BM Agent']
input_tokens = [2.2, 3.1, 37.7, 575.2]
output_tokens = [5.0, 5.9, 5.2, 6.2]
ratio = [0.44, 0.53, 7.25, 92.8]

x = np.arange(len(methods))
width = 0.35

# Create bars
bars1 = ax2.bar(x - width/2, input_tokens, width, label='Input Tokens (×10³)',
                color='#e74c3c', edgecolor='#c0392b', linewidth=2)
bars2 = ax2.bar(x + width/2, output_tokens, width, label='Output Tokens (×10³)',
                color='#3498db', edgecolor='#2980b9', linewidth=2)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 10,
                f'{height:.1f}K',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

ax2.set_ylabel('Token Count (×10³)', fontsize=13, fontweight='bold')
ax2.set_xlabel('Technical Paradigm', fontsize=13, fontweight='bold')
ax2.set_title('Token Consumption Asymmetry\n(Input/Output Ratio)', fontsize=14, fontweight='bold', pad=15)
ax2.set_xticks(x)
ax2.set_xticklabels(methods, fontsize=12, fontweight='bold')
ax2.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True)
ax2.set_ylim(0, 650)
ax2.grid(axis='y', alpha=0.3, linestyle='--')

# Add ratio annotation
for i, (xi, r) in enumerate(zip(x, ratio)):
    if i == 3:  # BM Agent
        ax2.annotate(f'Ratio: {r:.1f}', xy=(xi, 575), xytext=(xi, 600),
                    fontsize=13, fontweight='bold', color='#c0392b',
                    ha='center', va='bottom',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffeaea',
                             edgecolor='#e74c3c', linewidth=2))

plt.tight_layout()
plt.subplots_adjust(top=0.92)

fig9.savefig(f'{output_dir}/figure9_tool_hierarchy_token.pdf', bbox_inches='tight', dpi=300)
fig9.savefig(f'{output_dir}/figure9_tool_hierarchy_token.png', bbox_inches='tight', dpi=300)
print("Saved: figure9_tool_hierarchy_token.pdf/png")

print("\n" + "="*60)
print("ALL FIGURES GENERATED SUCCESSFULLY")
print("="*60)
print("\nFigure 8: Patient-Level Multi-Dimensional Assessment")
print("  - 9 individual radar charts (one per patient)")
print("  - Alternative: Heatmap view with all metrics")
print("\nFigure 9: System 2 Thinking Architecture")
print("  - Left: Tool call hierarchy (stacked bar)")
print("  - Right: Token consumption asymmetry")
print("="*60)
