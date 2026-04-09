# Clinical Visualization SKILL

## 简介

本SKILL用于基于临床专家审查结果生成对比可视化图表，支持**4种方法**的对比：
1. Direct LLM V2
2. RAG V2
3. Web Search V2
4. BM Agent

## 核心功能

### 1. 支持的图表类型（4方法对比）

| 图表 | 文件名 | 说明 |
|------|--------|------|
| 雷达图 | Figure1_four_method_radar_*.png | 4方法多指标雷达对比 |
| CPI对比 | Figure2_cpi_four_methods_*.png | 分患者CPI柱状图（4方法） |
| Mean±SD对比 | Figure3_four_methods_meansd_*.png | 五指标统计对比（4方法） |
| CPI均值 | Figure4_cpi_mean_comparison_*.png | CPI均值柱状图 |
| 提升幅度 | Figure5_improvement_vs_direct_*.png | 相对于Direct LLM的提升 |
| PTR对比 | Figure6_ptr_comparison_*.png | 可追溯率对比 |

### 2. 输入数据格式

```
analysis/
├── reviews_direct_v2/work_<patient_id>/review_results.json
├── reviews_rag_v2/work_<patient_id>/review_results.json
├── reviews_websearch_v2/work_<patient_id>/review_results.json
└── reviews_bm_agent/work_<patient_id>/review_results.json
```

每个review_results.json包含：
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
- **颜色编码**:
  - Direct LLM: 印度红 (#CD5C5C)
  - RAG V2: 钢蓝色 (#4682B4)
  - Web Search V2: 海绿色 (#2E8B57)
  - BM Agent: 金黄色 (#DAA520)

## 使用方法

### 命令行调用

```bash
# 2方法对比（RAG vs Web Search）
python3 analysis/generate_visualization_YYYY-MM-DD.py

# 4方法对比（Direct/RAG/Web/BM）
python3 analysis/generate_four_methods_visualization.py
```

### Python API

```python
from clinical_visualization import load_all_data, plot_figure1_radar_comparison

# 加载4方法数据
dfs = load_all_data()  # 返回Dict[str, DataFrame]

# 计算统计
stats = calculate_statistics(dfs)

# 生成图表
plot_figure1_radar_comparison(stats)
```

## 文件结构

```
clinical_visualization/
├── metadata.json          # Skill元数据
├── SKILL.md              # 本文件
└── scripts/
    ├── generate_visualization.py           # 2方法对比脚本
    └── generate_four_methods_visualization.py  # 4方法对比脚本
```

## 4方法对比示例结果

**Set-1 Batch (2026-04-09)**:

| 方法 | Mean CPI | Mean PTR | 特点 |
|------|----------|----------|------|
| Direct LLM | 0.419 | 0.000 | 无真实引用 |
| RAG V2 | 0.616 | 0.125 | Parametric Knowledge过多 |
| Web Search V2 | 0.712 | 0.386 | PubMed引用丰富 |
| BM Agent | **0.931** | **0.982** | 引用规范完整 |

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| DPI | 300 | 输出分辨率 |
| 患者数 | 9 | Set-1 Batch样本量 |
| 指标数 | 5 | CPI/CCR/MQR/CER/PTR |

## 版本历史

- v1.1.0 (2026-04-09): 增加4方法对比支持
- v1.0.0 (2026-04-09): 初始版本，支持2方法对比

---

**维护者**: Claude Code
**最后更新**: 2026-04-09
