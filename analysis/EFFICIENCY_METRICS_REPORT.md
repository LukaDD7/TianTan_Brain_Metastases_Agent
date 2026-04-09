# 效率指标汇总报告

**生成日期**: 2026-04-09

## 指标定义

| 指标 | 说明 | 数据来源 |
|------|------|----------|
| 平均端到端延迟 | 从输入到生成完整报告的时间 | baseline结果中的latency_ms |
| 单例平均输入 | LLM输入token总数 | BM Agent日志 / Baseline记录 |
| 单例平均输出 | LLM输出token总数 | BM Agent日志 / Baseline记录 |
| 输入/输出比值 | 输入token数 / 输出token数 | 计算得出 |
| 底层环境调用总频次 | 工具调用次数（文件读取、搜索等） | BM Agent日志统计 |

## 结果汇总

### 1. 平均端到端延迟 (ms)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
| Direct LLM | 160547.1 ± 53832.7 | 104743 - 260463 |
| RAG V2 | 137491.4 ± 22624.2 | 99545 - 174213 |
| Web Search V2 | 113708.6 ± 9439.8 | 101237 - 130060 |

### 2. 单例平均输入 (tokens)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
| Direct LLM | N/A | N/A |
| RAG V2 | N/A | N/A |
| Web Search V2 | N/A | N/A |
| BM Agent | 690224 ± 357916 | 331158 - 1513558 |

### 3. 单例平均输出 (tokens)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
| Direct LLM | N/A | N/A |
| RAG V2 | N/A | N/A |
| Web Search V2 | N/A | N/A |
| BM Agent | 7670 ± 5924 | 2299 - 20239 |

### 4. 输入/输出比值

| 方法 | Mean |
|------|------|
| Direct LLM | N/A |
| RAG V2 | N/A |
| Web Search V2 | N/A |
| BM Agent | 118.09 |

### 5. 底层环境调用总频次 (tool_calls)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
| Direct LLM | N/A | N/A |
| RAG V2 | N/A | N/A |
| Web Search V2 | N/A | N/A |
| BM Agent | 44.8 ± 10.9 | 30 - 61 |

## 数据来源说明

- **Direct LLM**: baseline/set1_results/direct_llm/*_baseline_results.json
- **RAG V2**: analysis/set1_baseline_v2_metrics_analysis.json
- **Web Search V2**: analysis/set1_baseline_v2_metrics_analysis.json
- **BM Agent**: workspace/sandbox/execution_logs/*_structured.jsonl

## 备注

- Direct LLM、RAG V2、Web Search V2的baseline结果中未记录input/output tokens
- BM Agent的token数据从结构化日志中提取
