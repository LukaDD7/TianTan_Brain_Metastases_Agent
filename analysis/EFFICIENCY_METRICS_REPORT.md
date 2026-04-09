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
| RAG V2 | 95607.1 ± 19435.5 | 73923 - 134051 |
| Web Search V2 | 113708.6 ± 9439.8 | 101237 - 130060 |

### 2. 单例平均输入 (tokens)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
| Direct LLM | 506 ± 59 | 429 - 580 |
| RAG V2 | 506 ± 59 | 429 - 580 |
| Web Search V2 | 506 ± 59 | 429 - 580 |
| BM Agent | 690224 ± 357916 | 331158 - 1513558 |

### 3. 单例平均输出 (tokens)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
| Direct LLM | 4075 ± 253 | 3795 - 4587 |
| RAG V2 | 3622 ± 224 | 3320 - 3981 |
| Web Search V2 | 5750 ± 532 | 4908 - 6387 |
| BM Agent | 7670 ± 5924 | 2299 - 20239 |

### 4. 输入/输出比值

| 方法 | Mean |
|------|------|
| Direct LLM | 0.12 |
| RAG V2 | 0.14 |
| Web Search V2 | 0.09 |
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
- **RAG V2**: baseline/set1_results/rag/*_baseline_results.json
- **Web Search V2**: baseline/set1_results_v2/websearch/*_baseline_results.json
- **BM Agent**: workspace/sandbox/execution_logs/*_structured.jsonl

## 备注

- **Direct LLM、RAG V2、Web Search V2的Token数据**：
  - 由于Baseline运行未记录API返回的token使用量，采用基于字符数的估算方法
  - 估算规则：中文字符1.5 tokens/字，英文单词1.3 tokens/词，标点符号0.5 tokens/个
  - 实际API调用可能与此估算存在偏差，仅供参考

- **BM Agent的Token数据**：
  - 从结构化日志中直接提取，包含实际的API调用记录
  - 输入token包括：系统提示、用户输入、工具返回结果等
  - 反映了多轮工具调用和推理过程的总token消耗

- **工具调用统计**：
  - 仅适用于BM Agent（其他Baseline方法不使用工具调用）
  - 包括文件读取、OncoKB查询、PubMed搜索等外部API调用
