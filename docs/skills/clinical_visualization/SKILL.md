# Clinical Visualization SKILL

## 简介

本SKILL用于基于临床专家审查结果生成对比可视化图表，支持RAG V2 vs Web Search V2等多方法对比。

## 核心功能

### 1. 支持的图表类型

| 图表 | 文件名 | 说明 |
|------|--------|------|
| 雷达图 | Figure1_radar_comparison_*.png | 多指标综合对比 |
| CPI对比 | Figure2_cpi_comparison_*.png | 分患者CPI柱状图 |
| Mean±SD对比 | Figure3_metrics_meansd_*.png | 五指标统计对比 |
| 提升幅度 | Figure4_improvement_percentage_*.png | 百分比提升图 |
| 热力图 | Figure5_patient_heatmap_*.png | 患者级指标热力图 |
| 引用分解 | Figure6_citation_breakdown_*.png | 引用来源分析 |

### 2. 输入数据格式

```json
{
  "patient_id": "868183",
  "ccr": {"score": 2.6, "breakdown": {...}},
  "mqr": {"score": 3.2, "breakdown": {...}},
  "cer": {"score": 0.267, "errors": [...]},
  "ptr": {"score": 0.187, "details": {...}},
  "cpi": 0.574
}
```

### 3. 输出规范

- **格式**: PNG (300 DPI) + PDF (矢量)
- **命名**: `{图表名}_YYYY-MM-DD.{格式}`
- **字体**: 支持中文 (SimHei/DejaVu Sans)
- **尺寸**: 论文级别 (适合期刊投稿)

## 使用方法

### 命令行调用

```bash
python3 analysis/generate_visualization_YYYY-MM-DD.py
```

### Python API

```python
from clinical_visualization import load_all_data, plot_figure1_radar_comparison

rag_df, web_df = load_all_data()
stats = calculate_statistics(rag_df, web_df)
plot_figure1_radar_comparison(rag_df, web_df, stats)
```

## 文件结构

```
clinical_visualization/
├── metadata.json          # Skill元数据
├── SKILL.md              # 本文件
└── scripts/
    └── generate_visualization.py  # 主脚本
```

## 命名规范

### 输入目录
```
analysis/
├── reviews_rag_v2/
│   └── work_<patient_id>/
│       └── review_results.json
└── reviews_websearch_v2/
    └── work_<patient_id>/
        └── review_results.json
```

### 输出目录
```
analysis/final_figures/
├── Figure1_radar_comparison_YYYY-MM-DD.png
├── Figure1_radar_comparison_YYYY-MM-DD.pdf
├── Figure2_cpi_comparison_YYYY-MM-DD.png
├── ...
└── VISUALIZATION_SUMMARY_YYYY-MM-DD.md
```

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| DPI | 300 | 输出分辨率 |
| 颜色-RAG | #4682B4 | 钢蓝色 |
| 颜色-Web | #2E8B57 | 海绿色 |
| 字体大小 | 10-14 | 根据图表调整 |

## 版本历史

- v1.0.0 (2026-04-09): 初始版本，支持6种图表类型

---

**维护者**: Claude Code
**最后更新**: 2026-04-09
