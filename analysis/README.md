# Brain Metastases MDT Analysis Framework

脑转移瘤MDT智能体分析框架 - 支持4种方法（3 Baselines + BM Agent）的统一分析、可视化和报告生成。

## 目录结构

```
analysis/
├── data/                      # 数据提取和预处理
│   └── extract_data.py        # 数据提取工具（含BM Agent占位符）
├── visualization/             # 可视化模块
│   └── metrics_viz.py         # 学术规范图表生成
├── reports/                   # 生成的报告
│   ├── summary_table.csv      # 汇总表格
│   └── comparison_report.md   # 对比分析报告
├── unified_analysis.py        # 主分析脚本
└── README.md                  # 本文件
```

## 支持的4种方法

| 方法 | 数据来源 | 特殊指标 |
|------|----------|----------|
| **Direct LLM** | `baseline/results/*_baseline_results.json` | 预训练知识标注 |
| **RAG** | `baseline/results/*_baseline_results.json` | 检索来源、指南引用 |
| **WebSearch** | `baseline/results/*_baseline_results.json` | 搜索来源URL、推理过程 |
| **BM Agent** | `workspace/sandbox/execution_logs/` + `patients/` | 工具调用链、检查点 |

## 评估指标

### 核心指标（CCR/PTR/MQR/CER/CPI）

详见 `baseline/evaluation_metrics_standard.md`

### 效率指标

| 指标 | 说明 | 数据来源 |
|------|------|----------|
| **Latency** | 响应时间（毫秒） | 所有方法都有 |
| **Input Tokens** | 输入token数 | Baseline有，BM Agent需添加 |
| **Output Tokens** | 输出token数 | Baseline有，BM Agent需添加 |
| **Total Tokens** | 总token数 | Baseline有，BM Agent需添加 |
| **Tool Calls** | 工具调用次数 | 仅BM Agent和WebSearch |

## 使用说明

### 1. 运行分析（当前仅3种Baseline）

```bash
cd /media/luzhenyang/project/TianTan_Brain_Metastases_Agent
conda run -n tiantanBM_agent python analysis/unified_analysis.py
```

输出：
- `analysis/reports/summary_table.csv` - 汇总表格
- `analysis/reports/comparison_report.md` - 对比报告

### 2. 生成可视化

```bash
conda run -n tiantanBM_agent python analysis/visualization/metrics_viz.py
```

输出（在 `analysis/visualization/`）：
- `radar_chart.pdf/png` - 雷达图（CCR/PTR/MQR/CPI）
- `token_usage.pdf/png` - Token消耗箱线图
- `latency_comparison.pdf/png` - 响应时间对比
- `cpi_heatmap.pdf/png` - CPI热力图
- `citation_breakdown.pdf/png` - 引用可追溯性分布

### 3. 添加BM Agent数据（TODO）

当BM Agent运行完成后，需要：

**步骤1**：修改 `analysis/data/extract_data.py`

实现 `BMAgentDataExtractor.extract_all_bm_agent_results()` 方法：

```python
@staticmethod
def extract_all_bm_agent_results(...) -> List[Dict]:
    """
    实现逻辑：
    1. 扫描 execution_logs/ 目录获取所有session日志
    2. 扫描 patients/ 目录获取所有MDT报告
    3. 匹配patient_id
    4. 提取：
       - report: 从MDT报告文件
       - reasoning: 从execution_log的llm_response
       - tool_calls: 从execution_log的tool_call条目
       - latency: 累加所有duration_ms
       - tokens: 【需要修改BM Agent添加记录】
    5. 返回标准化数据列表
    """
```

**步骤2**：（可选）修改BM Agent添加token记录

在 `interactive_main.py` 的 `log_llm_response` 方法中添加：

```python
def log_llm_response(self, content: str, role: str = "assistant",
                     model: str = "brain_model", usage: Dict = None):
    entry = {
        ...
        "usage": usage or {}  # 添加token使用量
    }
```

**步骤3**：重新运行分析

```bash
python analysis/unified_analysis.py
```

此时将包含BM Agent的完整对比。

## 学术规范要点

### 1. 统计方法

- **描述性统计**：均值±标准差、中位数(IQR)
- **显著性检验**：Wilcoxon signed-rank test（配对样本，非正态分布）

### 2. 可视化规范

- 所有图表保存为PDF（矢量图，适合论文）
- 分辨率300 DPI
- 包含图例、标题、轴标签
- 使用不同颜色和线型区分方法

### 3. 数据完整性

所有结果必须包含：
- timestamp: 时间戳
- latency_ms: 响应时间
- tokens: {input, output, total}
- report: 完整报告
- reasoning: 推理过程

## 当前状态

### ✅ 已完成

- [x] Baseline数据提取（Direct LLM, RAG, WebSearch）
- [x] 指标计算框架（CCR, PTR, MQR, CER, CPI）
- [x] 可视化模块（雷达图、箱线图、热力图等）
- [x] 统计分析框架

### ⏳ 占位符（待BM Agent数据）

- [ ] BM Agent数据提取
- [ ] 4方法完整对比
- [ ] 统计显著性检验

## 注意事项

### Token记录差异

| 方法 | Token记录 | 说明 |
|------|-----------|------|
| Baseline | ✅ 完整 | 从API response提取 |
| BM Agent | ❌ 缺失 | 需要修改代码添加 |

**解决方案**：
- 方案1：修改BM Agent添加token记录（推荐）
- 方案2：BM Agent使用估算值（1 token ≈ 4字符）

### 时间对齐

- Baseline: 单次调用latencys
- BM Agent: 多轮工具调用，需累加duration_ms

## 依赖安装

```bash
conda activate tiantanBM_agent
pip install matplotlib pandas numpy scipy
```

## 联系

如有问题，请参考 `baseline/evaluation_metrics_standard.md` 中的详细评估标准。
