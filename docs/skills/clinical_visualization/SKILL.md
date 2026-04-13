# Clinical Visualization SKILL

## 简介

本SKILL用于基于临床专家审查结果生成对比可视化图表，支持**4种方法**的对比：
1. Direct LLM V2
2. RAG V2
3. Web Search V2
4. BM Agent

## 核心功能

### 0. 患者标识规范（重要！）

**数据匿名化要求**:
- 所有分患者图表必须使用 **Case1-9** 匿名化标签
- **严禁**在图表x轴、图例或标题中显示原始患者ID
- 患者ID与Case编号映射关系：

| Case | 患者ID | 原发癌种 | 驱动基因 |
|------|--------|----------|----------|
| Case1 | 605525 | 结肠癌 | KRAS G12V |
| Case2 | 612908 | 肺癌 | 阴性 |
| Case3 | 638114 | 肺腺癌 | EGFR 19del+T790M |
| Case4 | 640880 | 肺腺癌 | EGFR突变 |
| Case5 | 648772 | 恶性黑色素瘤 | BRAF突变 |
| Case6 | 665548 | 贲门腺癌 | HER2低表达 |
| Case7 | 708387 | 肺腺癌 | MET扩增+融合 |
| Case8 | 747724 | 乳腺癌 | HER2+ |
| Case9 | 868183 | 肺腺癌 | SMARCA4+STK11 |

**受影响图表**: Figure2 (CPI by Case)

### 1. 支持的图表类型（4方法对比）

| 图表 | 文件名 | 说明 |
|------|--------|------|
| 雷达图 | Figure1_four_method_radar_*.png | 4方法多指标雷达对比 |
| CPI对比 | Figure2_cpi_by_case_*.png | **分Case CPI柱状图（使用Case1-9标签）** |
| Mean±SD对比 | Figure3_four_methods_meansd_*.png | 五指标统计对比（4方法） |
| CPI均值 | Figure4_cpi_mean_comparison_*.png | CPI均值柱状图 |
| 提升幅度 | Figure5_improvement_vs_direct_*.png | 相对于Direct LLM的提升 |
| PTR对比 | Figure6_ptr_comparison_*.png | 可追溯率对比 |

### 2. 输入数据格式

**数据匿名化要求**:
所有患者数据在可视化前必须进行匿名化处理，原始患者ID映射为Case1-9编号。

**输入文件结构**:
```
analysis/reviews_blind_20260411/
├── QUANTITATIVE_SUMMARY_20260411.json    # 主数据源（含患者ID与Case映射）
├── PATIENT_COHORT_TABLE.md               # 患者详情表（已匿名化）
└── work_<patient_id>/review_results.json # 单个患者审查结果
```

**数据映射示例**:
```python
# 患者ID到Case编号的映射
case_mapping = {
    '605525': 'Case1', '612908': 'Case2', '638114': 'Case3',
    '640880': 'Case4', '648772': 'Case5', '665548': 'Case6',
    '708387': 'Case7', '747724': 'Case8', '868183': 'Case9'
}

# 在Figure2等分患者图表中，x轴标签必须使用Case编号
```

**JSON数据结构**:
```json
{
  "patient_id": "868183",  // 原始ID，可视化时转换为Case9
  "method": "BM Agent",
  "CPI": 0.917,
  "PTR": 0.689,
  "CCR": 4.0,
  "MQR": 4.0,
  "CER": 0.0
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
| 样本量 | 9 (Case1-9) | Set-1 Batch样本量，使用匿名化标签 |
| 方法数 | 4 | Direct LLM / RAG / WebSearch / BM Agent |
| 指标数 | 5 | CPI/CCR/MQR/CER/PTR |

## 可视化规范检查清单

生成图表前必须检查：

- [ ] **Figure2 (CPI by Case)**: x轴使用Case1-9而非患者ID
- [ ] **颜色一致性**: 4方法颜色编码统一
- [ ] **双格式输出**: PNG (300 DPI) + PDF
- [ ] **标签可读性**: 字体大小、旋转角度合适

## 版本历史

- **v1.2.0 (2026-04-12)**: 修复Figure2患者ID匿名化问题，x轴标签改为Case1-9
- v1.1.0 (2026-04-09): 增加4方法对比支持
- v1.0.0 (2026-04-09): 初始版本，支持2方法对比

---

**维护者**: Claude Code
**最后更新**: 2026-04-12
