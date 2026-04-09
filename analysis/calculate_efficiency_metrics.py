#!/usr/bin/env python3
"""
效率指标计算脚本 - 4方法对比
计算：平均端到端延迟、单例平均输入、单例平均输出、输入/输出比值、底层环境调用总频次

数据来源：
- Baseline结果: baseline/set1_results/*/*_baseline_results.json
- BM Agent日志: workspace/sandbox/execution_logs/*_structured.jsonl
"""

import json
import glob
import re
from pathlib import Path
from typing import Dict, List
import statistics

# 患者列表
PATIENT_IDS = ['605525', '612908', '638114', '640880', '648772', '665548', '708387', '747724', '868183']

ROOT = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent")


def estimate_tokens(text: str) -> int:
    """基于字符数估算token数量
    估算规则：
    - 中文字符：1.5 tokens/字
    - 英文单词：1.3 tokens/词
    - 标点符号：0.5 tokens/个
    """
    if not text:
        return 0

    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    punct = len(re.findall(r'[^\w\u4e00-\u9fff\s]', text))

    return int(cn_chars * 1.5 + en_words * 1.3 + punct * 0.5)


def extract_baseline_metrics(method: str) -> Dict[str, Dict]:
    """从baseline结果中提取效率指标"""
    results = {}

    base_path = ROOT / "baseline"
    if method == "direct_llm":
        path = base_path / "set1_results/direct_llm"
    elif method == "rag":
        path = base_path / "set1_results/rag"
    elif method == "websearch":
        path = base_path / "set1_results_v2/websearch"
    else:
        return results

    for pid in PATIENT_IDS:
        file_path = path / f"{pid}_baseline_results.json"
        if not file_path.exists():
            continue

        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
            result_key = list(data.get('results', {}).keys())[0]
            result = data['results'][result_key]

            # 获取报告内容用于估算tokens
            report = result.get('report', '')
            patient_input = data.get('patient_input_preview', '')

            # 估算token（如果实际值不存在或为0）
            stored_input_tokens = result.get('input_tokens', 0)
            stored_output_tokens = result.get('output_tokens', 0)

            if stored_input_tokens > 0:
                input_tokens = stored_input_tokens
            else:
                # 估算输入token
                input_tokens = estimate_tokens(patient_input)

            if stored_output_tokens > 0:
                output_tokens = stored_output_tokens
            else:
                # 估算输出token
                output_tokens = estimate_tokens(report)

            results[pid] = {
                'latency_ms': result.get('latency_ms', 0),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'report_length': len(report),
            }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return results


def extract_bm_agent_metrics() -> Dict[str, Dict]:
    """从BM Agent日志中提取效率指标"""
    results = {}

    log_dir = ROOT / "workspace/sandbox/execution_logs"

    for pid in PATIENT_IDS:
        # 查找该患者的日志文件
        pattern = f"session_*_{pid}_*_structured.jsonl"
        log_files = list(log_dir.glob(pattern))

        if not log_files:
            print(f"No log file found for patient {pid}")
            continue

        # 使用最新的日志文件
        log_file = sorted(log_files)[-1]

        try:
            total_input_tokens = 0
            total_output_tokens = 0
            tool_calls = 0
            start_time = None
            end_time = None

            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)

                        # 记录时间
                        if start_time is None:
                            start_time = record.get('timestamp')
                        end_time = record.get('timestamp')

                        # 统计token
                        if 'usage' in record and record['usage']:
                            usage = record['usage']
                            total_input_tokens += usage.get('input_tokens', 0)
                            total_output_tokens += usage.get('output_tokens', 0)

                        # 统计工具调用
                        if record.get('type') == 'tool_call':
                            tool_calls += 1

                    except json.JSONDecodeError:
                        continue

            results[pid] = {
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'tool_calls': tool_calls,
                'log_file': str(log_file.name),
            }

        except Exception as e:
            print(f"Error reading {log_file}: {e}")

    return results


def calculate_statistics(values: List[float]) -> Dict:
    """计算统计指标"""
    if not values:
        return {'mean': 0, 'std': 0, 'min': 0, 'max': 0}

    return {
        'mean': statistics.mean(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values),
    }


def main():
    print("=" * 80)
    print("效率指标计算 - 4方法对比")
    print("=" * 80)
    print()

    # 提取各方法指标
    print("[1/4] 提取 Direct LLM 指标...")
    direct_metrics = extract_baseline_metrics("direct_llm")

    print("[2/4] 提取 RAG V2 指标...")
    rag_metrics = extract_baseline_metrics("rag")

    print("[3/4] 提取 Web Search V2 指标...")
    web_metrics = extract_baseline_metrics("websearch")

    print("[4/4] 提取 BM Agent 指标...")
    bm_metrics = extract_bm_agent_metrics()

    # 计算汇总统计
    print("\n" + "=" * 80)
    print("效率指标汇总")
    print("=" * 80)

    methods_data = {
        'Direct LLM': direct_metrics,
        'RAG V2': rag_metrics,
        'Web Search V2': web_metrics,
        'BM Agent': bm_metrics,
    }

    summary = {}

    for method_name, metrics in methods_data.items():
        if not metrics:
            continue

        latencies = [m.get('latency_ms', 0) for m in metrics.values() if m.get('latency_ms', 0) > 0]
        input_tokens = [m.get('input_tokens', 0) for m in metrics.values() if m.get('input_tokens', 0) > 0]
        output_tokens = [m.get('output_tokens', 0) for m in metrics.values() if m.get('output_tokens', 0) > 0]
        tool_calls = [m.get('tool_calls', 0) for m in metrics.values() if m.get('tool_calls', 0) > 0]

        summary[method_name] = {
            'latency': calculate_statistics(latencies) if latencies else None,
            'input_tokens': calculate_statistics(input_tokens) if input_tokens else None,
            'output_tokens': calculate_statistics(output_tokens) if output_tokens else None,
            'tool_calls': calculate_statistics(tool_calls) if tool_calls else None,
            'io_ratio': statistics.mean([i/o for i, o in zip(input_tokens, output_tokens) if o > 0]) if input_tokens and output_tokens else None,
        }

    # 打印结果表格
    print("\n【1. 平均端到端延迟 (ms)】")
    print("-" * 60)
    for method, data in summary.items():
        if data['latency']:
            print(f"{method:20s}: {data['latency']['mean']:>10.1f} ± {data['latency']['std']:.1f} ms")

    print("\n【2. 单例平均输入 (tokens)】")
    print("-" * 60)
    for method, data in summary.items():
        if data['input_tokens']:
            print(f"{method:20s}: {data['input_tokens']['mean']:>10.0f} ± {data['input_tokens']['std']:.0f} tokens")
        else:
            print(f"{method:20s}: {'N/A':>10s}")

    print("\n【3. 单例平均输出 (tokens)】")
    print("-" * 60)
    for method, data in summary.items():
        if data['output_tokens']:
            print(f"{method:20s}: {data['output_tokens']['mean']:>10.0f} ± {data['output_tokens']['std']:.0f} tokens")
        else:
            print(f"{method:20s}: {'N/A':>10s}")

    print("\n【4. 输入/输出比值】")
    print("-" * 60)
    for method, data in summary.items():
        if data['io_ratio']:
            print(f"{method:20s}: {data['io_ratio']:>10.2f}")
        else:
            print(f"{method:20s}: {'N/A':>10s}")

    print("\n【5. 底层环境调用总频次 (tool_calls)】")
    print("-" * 60)
    for method, data in summary.items():
        if data['tool_calls']:
            print(f"{method:20s}: {data['tool_calls']['mean']:>10.1f} ± {data['tool_calls']['std']:.1f} calls")
        else:
            print(f"{method:20s}: {'N/A':>10s}")

    # 保存详细结果
    output_file = ROOT / "analysis/efficiency_metrics_summary.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': summary,
            'raw_data': {
                'direct_llm': direct_metrics,
                'rag': rag_metrics,
                'websearch': web_metrics,
                'bm_agent': bm_metrics,
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n详细结果已保存: {output_file}")

    # 生成Markdown报告
    md_content = """# 效率指标汇总报告

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
"""

    for method, data in summary.items():
        if data['latency']:
            md_content += f"| {method} | {data['latency']['mean']:.1f} ± {data['latency']['std']:.1f} | {data['latency']['min']:.0f} - {data['latency']['max']:.0f} |\n"

    md_content += """
### 2. 单例平均输入 (tokens)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
"""

    for method, data in summary.items():
        if data['input_tokens']:
            md_content += f"| {method} | {data['input_tokens']['mean']:.0f} ± {data['input_tokens']['std']:.0f} | {data['input_tokens']['min']:.0f} - {data['input_tokens']['max']:.0f} |\n"
        else:
            md_content += f"| {method} | N/A | N/A |\n"

    md_content += """
### 3. 单例平均输出 (tokens)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
"""

    for method, data in summary.items():
        if data['output_tokens']:
            md_content += f"| {method} | {data['output_tokens']['mean']:.0f} ± {data['output_tokens']['std']:.0f} | {data['output_tokens']['min']:.0f} - {data['output_tokens']['max']:.0f} |\n"
        else:
            md_content += f"| {method} | N/A | N/A |\n"

    md_content += """
### 4. 输入/输出比值

| 方法 | Mean |
|------|------|
"""

    for method, data in summary.items():
        if data['io_ratio']:
            md_content += f"| {method} | {data['io_ratio']:.2f} |\n"
        else:
            md_content += f"| {method} | N/A |\n"

    md_content += """
### 5. 底层环境调用总频次 (tool_calls)

| 方法 | Mean ± SD | Range |
|------|-----------|-------|
"""

    for method, data in summary.items():
        if data['tool_calls']:
            md_content += f"| {method} | {data['tool_calls']['mean']:.1f} ± {data['tool_calls']['std']:.1f} | {data['tool_calls']['min']:.0f} - {data['tool_calls']['max']:.0f} |\n"
        else:
            md_content += f"| {method} | N/A | N/A |\n"

    md_content += """
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
"""

    md_file = ROOT / "analysis/EFFICIENCY_METRICS_REPORT.md"
    md_file.write_text(md_content, encoding='utf-8')
    print(f"Markdown报告已保存: {md_file}")

    print("\n" + "=" * 80)
    print("效率指标计算完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
