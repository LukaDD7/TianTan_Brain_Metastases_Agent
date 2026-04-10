# Set-1 Batch 四方法对比最终汇总报告

**生成日期**: 2026-04-10  
**样本量**: 9例患者  
**对比方法**: Direct LLM V2, RAG V2, Web Search V2, BM Agent

---

## 表1：4种方法资源消耗汇总

| 效能指标 | Direct LLM | RAG Baseline | WebSearch | BM Agent |
|---------|------------|--------------|-----------|----------|
| 平均端到端延迟±SD（秒） | 160.5±53.8 | 95.6±19.4 | 113.7±9.4 | N/A |
| 单例平均输入Tokens（K） | 0.59±0.04 | 0.78±0.04 | **40.25±4.76** | **690.22±357.92** |
| 单例平均输出Tokens（K） | 4.49±0.31 | 3.96±0.31 | 5.51±0.42 | 7.67±5.92 |
| 输入/输出比值（I/O Ratio） | 0.13 | 0.20 | **7.34** | **118.09** |
| 底层环境调用总频次 | 0 | 1 | **3** | **44.8±10.9** |

**数据说明**:
- Token计算使用tiktoken（cl100k_base编码）
- Web Search V2使用API返回的真实usage数据
- BM Agent从结构化执行日志累加统计
- 环境调用定义：
  - Direct LLM: 无外部调用
  - RAG: 1次向量检索（固定3篇文档）
  - Web Search: 3次网络搜索（实际观测值）
  - BM Agent: 动态工具调用（文件读取、API查询等）

---

## 表2：4种方法MDT报告生成量化指标

| 方法 | 临床一致性（CCR，0-4）| 物理可追溯率（PTR，0-1）| 报告规范度（MQR，0-4）| 临床错误率（CER，0-1）| 综合性能指数（CPI，0-1）|
|------|---------------------|------------------------|---------------------|---------------------|------------------------|
| Direct LLM | 1.489±0.176 | 0.000±0.000 | 2.000±0.245 | 0.385±0.080 | 0.419±0.043 |
| RAG Baseline | 2.867±0.245 | 0.125±0.065 | 3.422±0.233 | 0.200±0.058 | 0.616±0.044 |
| WebSearch | 3.133±0.200 | 0.386±0.027 | 3.467±0.141 | 0.170±0.049 | 0.712±0.036 |
| **BM Agent** | **3.422±0.315** | **0.982±0.020** | **3.822±0.205** | **0.045±0.047** | **0.931±0.046** |

**指标定义**:
- **CCR**: Clinical Consistency Rate，临床决策一致性（0-4分）
- **PTR**: Physical Traceability Rate，物理可追溯率（0-1）
- **MQR**: MDT Quality Rate，报告规范度（0-4分）
- **CER**: Clinical Error Rate，临床错误率（0-1）
- **CPI**: Composite Performance Index = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)

---

## 关键发现

### 1. 效率对比
- **延迟**: RAG最快(95.6s)，Direct LLM最慢(160.5s)
- **Token消耗**: BM Agent输入token是Web Search的17倍，是Direct LLM的1173倍
- **I/O比值**: BM Agent(118.09) >> Web Search(7.34) >> RAG(0.20) > Direct LLM(0.13)
- **环境调用**: BM Agent平均44.8次，远超其他方法

### 2. 质量对比
- **CPI排名**: BM Agent(0.931) > Web Search(0.712) > RAG(0.616) > Direct LLM(0.419)
- **PTR突破**: BM Agent达到0.982，接近完全可追溯；Direct LLM为0
- **CER控制**: BM Agent错误率最低(0.045)，Direct LLM最高(0.385)
- **CCR优势**: BM Agent临床一致性显著领先(3.422 vs 1.489)

### 3. 效率-质量权衡
- **高消耗高回报**: BM Agent消耗最多资源，但质量最优
- **性价比之选**: Web Search在质量和效率间取得平衡
- **基线局限**: Direct LLM虽快但质量差，RAG提升有限

---

## 数据来源

- **效率指标**: `analysis/efficiency_metrics_v2.json`
- **量化指标**: `analysis/final_figures/FOUR_METHODS_SUMMARY_2026-04-09.md`
- **原始数据**:
  - Baseline结果: `baseline/set1_results/`, `baseline/set1_results_v2/`
  - BM Agent日志: `workspace/sandbox/execution_logs/`
  - 专家审查: `analysis/reviews_*/`

---

## 相关文件索引

### 核心报告（最新）
- 本汇总: `analysis/FINAL_SUMMARY_2026-04-10.md`
- 效率指标详细: `analysis/EFFICIENCY_METRICS_REPORT.md`
- 可视化图表: `analysis/final_figures/Figure*.png`
- 量化分析汇总: `analysis/final_figures/FOUR_METHODS_SUMMARY_2026-04-09.md`

### 核心脚本
- 效率计算: `analysis/calculate_efficiency_metrics_v2.py`
- 可视化生成: `analysis/generate_four_methods_visualization.py`
- 量化指标计算: `analysis/calculate_final_metrics.py`

### SKILL文档
- 专家审查SKILL: `~/.claude/skills/clinical_expert_review/`
- 可视化SKILL: `~/.claude/skills/clinical_visualization/`
- 量化指标规范: `QUANTITATIVE_METRICS_GUIDE.md`

---

**报告维护者**: Claude Code  
**最后更新**: 2026-04-10
