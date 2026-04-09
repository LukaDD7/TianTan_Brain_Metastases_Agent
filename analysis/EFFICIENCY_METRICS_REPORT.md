# 效率指标汇总报告

**生成日期**: 2026-04-09

## 指标定义

| 指标 | 说明 | 数据来源 |
|------|------|----------|
| 平均端到端延迟 | 从输入到生成完整报告的时间 | baseline结果中的latency_ms |
| 单例平均输入 | LLM输入token总数 | API usage / 估算 |
| 单例平均输出 | LLM输出token总数 | API usage / 估算 |
| 输入/输出比值 | 输入token数 / 输出token数 | 计算得出 |
| 底层环境调用 | 外部工具/搜索调用次数 | 各方法特定 |

## Token数据来源说明

| 方法 | 输入Tokens | 输出Tokens | 说明 |
|------|------------|------------|------|
| Direct LLM | 估算 | 估算 | 无API usage记录，基于字符数估算 |
| RAG V2 | 估算 | 估算 | 输入=患者输入+检索文档 |
| **Web Search V2** | **真实API数据** | **真实API数据** | 从full_output.usage读取 |
| BM Agent | 日志累加 | 日志累加 | 从structured.jsonl累加 |

## 结果汇总

### 1. 平均端到端延迟 (ms)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
| Direct LLM | 160547.1 ± 53832.7 | 104743 - 260463 |
| RAG V2 | 95607.1 ± 19435.5 | 73923 - 134051 |
| Web Search V2 | 113708.6 ± 9439.8 | 101237 - 130060 |

### 2. 单例平均输入 (tokens)

| 方法 | Mean ± SD | Range | 来源 |
|------|-----------|-------|------|
| Direct LLM | 506 ± 59 | 429 - 580 | 估算 |
| RAG V2 | 618 ± 53 | 545 - 695 | 估算 |
| Web Search V2 | 40252 ± 4762 | 34551 - 51419 | 真实API |
| BM Agent | 690224 ± 357916 | 331158 - 1513558 | 估算 |

### 3. 单例平均输出 (tokens)

| 方法 | Mean ± SD | Range | 来源 |
|------|-----------|-------|------|
| Direct LLM | 4075 ± 253 | 3795 - 4587 | 估算 |
| RAG V2 | 3622 ± 224 | 3320 - 3981 | 估算 |
| Web Search V2 | 5510 ± 415 | 4988 - 6123 | 真实API |
| BM Agent | 7670 ± 5924 | 2299 - 20239 | 估算 |

### 4. 输入/输出比值

| 方法 | Mean | 说明 |
|------|------|------|
| Direct LLM | 0.12 |  |
| RAG V2 | 0.17 |  |
| Web Search V2 | 7.34 | 搜索上下文增加输入 |
| BM Agent | 118.09 | 高比值源于多轮工具调用 |

### 5. 底层环境调用统计

| 方法 | 调用次数 | 类型说明 |
|------|----------|----------|
| Direct LLM | 0 | 无环境调用（纯参数知识） |
| RAG V2 | 1次 | 单次检索，固定3篇文档 |
| Web Search V2 | 3次 | 固定3次网络搜索 |
| BM Agent | 44.8±10.9次 | 文件读取、OncoKB、PubMed等工具调用 |

## 关键发现

1. **Web Search V2的真实Token数据**：
   - 输入: 40,252±4,762 tokens（远高于估算值506）
   - 输出: 5,510±415 tokens
   - I/O比值: 7.34（搜索上下文显著增加输入）

2. **BM Agent的高I/O比值**（118.09）：
   - 源于多轮工具调用和复杂推理
   - 平均44.8次工具调用，是Web Search的15倍

3. **RAG的固定模式**：
   - 单次检索（3篇文档）
   - I/O比值0.17，接近Direct LLM

## 数据来源

- **Direct LLM**: `baseline/set1_results/direct_llm/*_baseline_results.json`
- **RAG V2**: `baseline/set1_results/rag/*_baseline_results.json`
- **Web Search V2**: `baseline/set1_results_v2/websearch/*_baseline_results.json`
  - Token数据: `full_output.usage`
  - 搜索次数: 统计`full_output.output`中`web_search_call`类型
- **BM Agent**: `workspace/sandbox/execution_logs/*_structured.jsonl`

## 提取代码参考

### Web Search Token提取
```python
full_output = result['full_output']
input_tokens = full_output['usage']['input_tokens']   # 真实值
output_tokens = full_output['usage']['output_tokens'] # 真实值
search_count = sum(1 for item in full_output['output']
                   if item['type'] == 'web_search_call')  # =3
```

### BM Agent Token提取
```python
for line in structured_jsonl:
    record = json.loads(line)
    if 'usage' in record:
        total_input += record['usage']['input_tokens']
        total_output += record['usage']['output_tokens']
    if record['type'] == 'tool_call':
        tool_calls += 1
```
