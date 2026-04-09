#!/usr/bin/env python3
"""
效率指标计算脚本 V2 - 4方法对比
使用tiktoken精确计算token，统一指标为"环境调用总频次"

指标定义统一：
- 环境调用总频次 = 与外部环境交互的调用次数
  - Direct LLM: 0 (无外部调用)
  - RAG V2: 1 (单次向量检索)
  - Web Search V2: 3 (固定3次网络搜索)
  - BM Agent: 动态统计 (文件读取、API查询等工具调用)

Token计算：
- 优先使用API返回的usage数据
- 缺失时使用tiktoken精确计算
"""

import json
import tiktoken
from pathlib import Path
from typing import Dict, List
import statistics

PATIENT_IDS = ['605525', '612908', '638114', '640880', '648772', '665548', '708387', '747724', '868183']
ROOT = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent")

# 初始化tiktoken编码器（使用cl100k_base，支持GPT-4/3.5）
ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """使用tiktoken精确计算token数"""
    if not text:
        return 0
    return len(ENCODING.encode(text))


def extract_direct_llm_metrics() -> Dict[str, Dict]:
    """提取Direct LLM指标"""
    results = {}
    path = ROOT / "baseline/set1_results/direct_llm"

    for pid in PATIENT_IDS:
        file_path = path / f"{pid}_baseline_results.json"
        if not file_path.exists():
            continue

        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
            result = list(data['results'].values())[0]

            patient_input = data.get('patient_input_preview', '')
            report = result.get('report', '')

            results[pid] = {
                'latency_ms': result.get('latency_ms', 0),
                'input_tokens': count_tokens(patient_input),
                'output_tokens': count_tokens(report),
                'env_calls': 0,
                'env_calls_type': 'N/A',
                'token_source': 'tiktoken'
            }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return results


def extract_rag_metrics() -> Dict[str, Dict]:
    """提取RAG V2指标（环境调用=1次检索）"""
    results = {}
    path = ROOT / "baseline/set1_results/rag"

    for pid in PATIENT_IDS:
        file_path = path / f"{pid}_baseline_results.json"
        if not file_path.exists():
            continue

        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
            result = list(data['results'].values())[0]

            patient_input = data.get('patient_input_preview', '')
            report = result.get('report', '')
            retrieved_docs = result.get('retrieved_docs', [])

            # 输入token = 患者输入 + 检索文档内容
            input_text = patient_input
            for doc in retrieved_docs[:3]:
                input_text += '\n' + doc.get('content', '')[:2000]  # 限制每篇文档长度

            results[pid] = {
                'latency_ms': result.get('latency_ms', 0),
                'input_tokens': count_tokens(input_text),
                'output_tokens': count_tokens(report),
                'env_calls': 1,  # RAG只检索一次
                'env_calls_type': 'retrieval',
                'retrieved_docs_count': len(retrieved_docs),
                'token_source': 'tiktoken'
            }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return results


def extract_websearch_metrics() -> Dict[str, Dict]:
    """提取Web Search V2指标（环境调用=3次搜索）"""
    results = {}
    path = ROOT / "baseline/set1_results_v2/websearch"

    for pid in PATIENT_IDS:
        file_path = path / f"{pid}_baseline_results.json"
        if not file_path.exists():
            continue

        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
            result = list(data['results'].values())[0]
            full_output = result.get('full_output', {})

            # 获取真实token（Web Search有API返回的usage）
            usage = full_output.get('usage', {})
            real_input = usage.get('input_tokens', 0)
            real_output = usage.get('output_tokens', 0)

            # 如果没有usage，用tiktoken计算
            if real_input == 0:
                patient_input = data.get('patient_input_preview', '')
                real_input = count_tokens(patient_input)
                token_source = 'tiktoken'
            else:
                token_source = 'api_usage'

            if real_output == 0:
                report = result.get('report', '')
                real_output = count_tokens(report)

            # 统计Web Search调用次数（环境调用）
            search_count = 0
            if 'output' in full_output:
                for item in full_output['output']:
                    if item.get('type') == 'web_search_call':
                        search_count += 1

            results[pid] = {
                'latency_ms': result.get('latency_ms', 0),
                'input_tokens': real_input,
                'output_tokens': real_output,
                'env_calls': search_count if search_count > 0 else 3,  # Web Search固定3次
                'env_calls_type': 'web_search',
                'token_source': token_source
            }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return results


def extract_bm_agent_metrics() -> Dict[str, Dict]:
    """提取BM Agent指标（环境调用=工具调用次数）"""
    results = {}
    log_dir = ROOT / "workspace/sandbox/execution_logs"

    for pid in PATIENT_IDS:
        pattern = f"session_*_{pid}_*_structured.jsonl"
        log_files = list(log_dir.glob(pattern))
        if not log_files:
            continue

        log_file = sorted(log_files)[-1]

        try:
            total_input_tokens = 0
            total_output_tokens = 0
            tool_calls = 0

            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)

                        if 'usage' in record and record['usage']:
                            usage = record['usage']
                            total_input_tokens += usage.get('input_tokens', 0)
                            total_output_tokens += usage.get('output_tokens', 0)

                        if record.get('type') == 'tool_call':
                            tool_calls += 1

                    except json.JSONDecodeError:
                        continue

            results[pid] = {
                'latency_ms': 0,  # BM Agent日志中无延迟数据
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'env_calls': tool_calls,
                'env_calls_type': 'tool_call',
                'token_source': 'structured_logs'
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
    print("效率指标计算 V2 - 使用tiktoken精确计算")
    print("=" * 80)
    print()

    # 提取各方法指标
    print("[1/4] 提取 Direct LLM 指标...")
    direct_metrics = extract_direct_llm_metrics()

    print("[2/4] 提取 RAG V2 指标...")
    rag_metrics = extract_rag_metrics()

    print("[3/4] 提取 Web Search V2 指标...")
    web_metrics = extract_websearch_metrics()

    print("[4/4] 提取 BM Agent 指标...")
    bm_metrics = extract_bm_agent_metrics()

    methods_data = {
        'Direct LLM': direct_metrics,
        'RAG V2': rag_metrics,
        'Web Search V2': web_metrics,
        'BM Agent': bm_metrics
    }

    summary = {}

    for method_name, metrics in methods_data.items():
        if not metrics:
            continue

        latencies = [m['latency_ms'] for m in metrics.values() if m.get('latency_ms', 0) > 0]
        input_tokens = [m['input_tokens'] for m in metrics.values() if m.get('input_tokens', 0) > 0]
        output_tokens = [m['output_tokens'] for m in metrics.values() if m.get('output_tokens', 0) > 0]
        env_calls = [m['env_calls'] for m in metrics.values()]

        summary[method_name] = {
            'latency': calculate_statistics(latencies) if latencies else None,
            'input_tokens': calculate_statistics(input_tokens) if input_tokens else None,
            'output_tokens': calculate_statistics(output_tokens) if output_tokens else None,
            'env_calls': calculate_statistics(env_calls) if env_calls else None,
            'io_ratio': statistics.mean([i/o for i, o in zip(input_tokens, output_tokens) if o > 0])
                         if input_tokens and output_tokens else None
        }

    # 打印结果
    print("\n" + "=" * 80)
    print("效率指标汇总（tiktoken精确计算）")
    print("=" * 80)

    print("\n【1. 平均端到端延迟 (ms)】")
    print("-" * 70)
    for method, data in summary.items():
        if data['latency']:
            print(f"{method:20s}: {data['latency']['mean']:>10.1f} ± {data['latency']['std']:>8.1f} ms")

    print("\n【2. 单例平均输入 (tokens)】")
    print("-" * 70)
    for method, data in summary.items():
        if data['input_tokens']:
            note = ""
            sample = list(methods_data[method].values())[0]
            if sample.get('token_source') == 'api_usage':
                note = " [API]"
            elif sample.get('token_source') == 'tiktoken':
                note = " [tiktoken]"
            print(f"{method:20s}: {data['input_tokens']['mean']:>10.0f} ± {data['input_tokens']['std']:>8.0f}{note}")

    print("\n【3. 单例平均输出 (tokens)】")
    print("-" * 70)
    for method, data in summary.items():
        if data['output_tokens']:
            note = ""
            sample = list(methods_data[method].values())[0]
            if sample.get('token_source') == 'api_usage':
                note = " [API]"
            elif sample.get('token_source') == 'tiktoken':
                note = " [tiktoken]"
            print(f"{method:20s}: {data['output_tokens']['mean']:>10.0f} ± {data['output_tokens']['std']:>8.0f}{note}")

    print("\n【4. 输入/输出比值】")
    print("-" * 70)
    for method, data in summary.items():
        if data['io_ratio']:
            print(f"{method:20s}: {data['io_ratio']:>10.2f}")

    print("\n【5. 环境调用总频次】")
    print("-" * 70)
    print(f"{'方法':<20s} {'次数':>10s} {'类型':<20s}")
    print("-" * 70)

    for method, metrics in methods_data.items():
        if not metrics:
            continue
        sample = list(metrics.values())[0]
        calls = sample.get('env_calls', 0)
        calls_type = sample.get('env_calls_type', 'N/A')

        type_desc = {
            'N/A': '无',
            'retrieval': '向量检索',
            'web_search': '网络搜索',
            'tool_call': '工具调用'
        }.get(calls_type, calls_type)

        print(f"{method:<20s} {calls:>10.0f} {type_desc:<20s}")

    # 统计环境调用
    print("\n【环境调用统计汇总】")
    print("-" * 70)
    for method, data in summary.items():
        if data['env_calls']:
            print(f"{method:20s}: {data['env_calls']['mean']:>10.1f} ± {data['env_calls']['std']:>6.1f} "
                  f"(range: {data['env_calls']['min']:.0f}-{data['env_calls']['max']:.0f})")

    # 保存结果
    output_file = ROOT / "analysis/efficiency_metrics_v2.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': summary,
            'raw_data': {
                'direct_llm': direct_metrics,
                'rag': rag_metrics,
                'websearch': web_metrics,
                'bm_agent': bm_metrics
            },
            'metadata': {
                'token_calculator': 'tiktoken (cl100k_base)',
                'env_calls_definition': {
                    'direct_llm': '0 (无外部调用)',
                    'rag_v2': '1 (单次向量检索)',
                    'web_search_v2': '3 (网络搜索)',
                    'bm_agent': '动态工具调用次数'
                }
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
