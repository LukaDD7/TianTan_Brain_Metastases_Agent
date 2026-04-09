# Set-1 Batch 可视化分析汇总

**生成日期**: 2026-04-09
**样本量**: 9例患者
**对比方法**: RAG V2 vs Web Search V2

---

## 一、统计汇总 (Mean±SD)

| 指标 | RAG V2 | Web Search V2 | 提升幅度 |
|------|--------|---------------|---------|
| CPI | 0.616±0.044 | 0.712±0.036 | ↑15.6% |
| CCR | 2.867±0.245 | 3.133±0.200 | ↑9.3% |
| MQR | 3.422±0.233 | 3.467±0.141 | ↑1.3% |
| CER | 0.200±0.058 | 0.170±0.049 | ↑14.9% |
| PTR | 0.125±0.065 | 0.386±0.027 | ↑208.0% |

## 二、生成的图表

| 图表 | 文件名 | 说明 |
|------|--------|------|
| 图1 | Figure1_radar_comparison_2026-04-09.png | 多指标雷达图对比 |
| 图2 | Figure2_cpi_comparison_2026-04-09.png | CPI分患者对比 |
| 图3 | Figure3_metrics_meansd_2026-04-09.png | 五指标Mean±SD对比 |
| 图4 | Figure4_improvement_percentage_2026-04-09.png | 提升幅度百分比 |
| 图5 | Figure5_patient_heatmap_2026-04-09.png | 患者级热力图 |
| 图6 | Figure6_citation_breakdown_2026-04-09.png | 引用来源分解 |

---

**数据来源**: analysis/reviews_rag_v2/ 和 analysis/reviews_websearch_v2/
**输出目录**: analysis/final_figures/