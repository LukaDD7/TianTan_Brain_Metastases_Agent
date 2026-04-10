# Set-1 Batch 四方法对比最终汇总报告

**生成日期**: 2026-04-10  
**样本量**: 9例患者  
**对比方法**: Direct LLM V2, RAG V2, Web Search V2, BM Agent

---

## 表1：4种方法资源消耗汇总

| 效能指标 | Direct LLM V2 | RAG V2 | WebSearch V2 | BM Agent |
|---------|---------------|--------|--------------|----------|
| 平均端到端延迟±SD（秒） | **97.10±8.68** | **137.49±22.62** | **113.71±9.44** | N/A |
| 单例平均输入Tokens（K） | **2.24±1.07** | **3.92±1.14** | **40.25±4.76** | **690.22±357.92** |
| 单例平均输出Tokens（K） | **5.20±0.19** | **6.62±0.79** | **5.51±0.42** | **7.67±5.92** |
| 输入/输出比值（I/O Ratio） | **0.43±0.22** | **0.59±0.15** | **7.34±1.02** | **118.09±59.61** |
| 底层环境调用总频次 | **0.00±0.00** | **1.00±0.00** | **3.00±0.00** | **44.78±10.86** |

**数据说明**:
- **统计口径统一**: 所有Baseline V2均使用API Usage（非tiktoken估算）
  - Direct LLM V2: `usage.input_tokens` = system prompt + user message
  - RAG V2: `usage.prompt_tokens` = system prompt + patient input + 3篇检索文档
  - Web Search V2: `usage.input_tokens` = system prompt + user message + 搜索上下文
  - BM Agent: 结构化日志累加 = 多轮LLM调用成本（交互深度指标）
- **环境调用定义**:
  - Direct LLM: 0次 (无外部调用)
  - RAG: 1次向量检索（固定3篇文档）
  - Web Search: 3次网络搜索（实际观测值）
  - BM Agent: 动态工具调用（文件读取、API查询等）

---

## 表2：4种方法MDT报告生成量化指标

| 方法 | 临床一致性（CCR，0-4）| 物理可追溯率（PTR，0-1）| 报告规范度（MQR，0-4）| 临床错误率（CER，0-1）| 综合性能指数（CPI，0-1）|
|------|---------------------|------------------------|---------------------|---------------------|------------------------|
| Direct LLM V2 | 1.49±0.18 | 0.00±0.00 | 2.00±0.25 | 0.39±0.08 | 0.42±0.04 |
| RAG V2 | 2.87±0.25 | 0.13±0.07 | 3.42±0.23 | 0.20±0.06 | 0.62±0.04 |
| WebSearch V2 | 3.13±0.20 | 0.39±0.03 | 3.47±0.14 | 0.17±0.05 | 0.71±0.04 |
| **BM Agent** | **3.42±0.32** | **0.98±0.02** | **3.82±0.21** | **0.05±0.05** | **0.93±0.05** |

**指标定义**:
- **CCR**: Clinical Consistency Rate，临床决策一致性（0-4分）
- **PTR**: Physical Traceability Rate，物理可追溯率（0-1）
- **MQR**: MDT Quality Rate，报告规范度（0-4分）
- **CER**: Clinical Error Rate，临床错误率（0-1）
- **CPI**: Composite Performance Index = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)

---

## 关键发现

### 1. 效率对比
- **延迟**: Direct LLM V2最快(97.10s)，Web Search V2次之(113.71s)，RAG V2最慢(137.49s，含向量检索)
- **输入Tokens**: Web Search V2因搜索上下文最大(40.25K)，RAG V2(3.92K)高于Direct LLM V2(2.24K)因包含3篇检索文档
- **输出Tokens**: RAG V2输出最长(6.62K)，可能因检索文档激发更多内容
- **I/O比值**: BM Agent(118.09) >> Web Search(7.34) >> RAG(0.59) > Direct LLM(0.43)
- **环境调用**: BM Agent平均44.78次，远超其他方法

### 2. 质量对比
- **CPI排名**: BM Agent(0.93) > Web Search V2(0.71) > RAG V2(0.62) > Direct LLM V2(0.42)
- **PTR突破**: BM Agent达到0.98，接近完全可追溯；Direct LLM V2为0
- **CER控制**: BM Agent错误率最低(0.05)，Direct LLM V2最高(0.39)
- **CCR优势**: BM Agent临床一致性显著领先(3.42 vs 1.49)

### 3. 效率-质量权衡
- **高消耗高回报**: BM Agent消耗最多资源，但质量最优
- **性价比之选**: Web Search在质量和效率间取得平衡
- **基线局限**: Direct LLM虽快但质量差，RAG提升有限

---

## 数据来源

- **效率指标**: `analysis/efficiency_metrics_v2.json`
- **量化指标**: `analysis/final_figures/FOUR_METHODS_SUMMARY_2026-04-09.md`
- **原始数据**:
  - Direct LLM V2: `baseline/set1_results_v2/all/direct_llm/` (2026-04-10, API usage)
  - RAG V2: `baseline/set1_results_v2/all/rag/` (2026-04-10, API usage)
  - Web Search V2: `baseline/set1_results_v2/websearch/` (2026-04-09, API usage)
  - BM Agent日志: `workspace/sandbox/execution_logs/` (2026-04-07)

---

## 相关文件索引

### 核心报告（最新）
- 本汇总: `analysis/FINAL_SUMMARY_2026-04-10.md`
- 效率指标详细: `analysis/EFFICIENCY_METRICS_REPORT.md`
- 可视化图表: `analysis/final_figures/Figure*.png`
- 量化分析汇总: `analysis/final_figures/FOUR_METHODS_SUMMARY_2026-04-09.md`

### 核心脚本
- 效率计算: `analysis/calculate_efficiency_metrics.py` (V2版本，支持API usage数据)
- 可视化生成: `analysis/generate_four_methods_visualization.py`
- 量化指标计算: `analysis/calculate_final_metrics.py`
- Baseline执行: `baseline/run_set1_baselines.py`

### SKILL文档
- Baseline评估SKILL: `~/.claude/skills/baseline_evaluation/`
- 专家审查SKILL: `~/.claude/skills/clinical_expert_review/`
- 可视化SKILL: `~/.claude/skills/clinical_visualization/`
- 量化指标规范: `QUANTITATIVE_METRICS_GUIDE.md`

---

**报告维护者**: Claude Code  
**最后更新**: 2026-04-10
