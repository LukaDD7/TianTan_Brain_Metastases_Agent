#!/usr/bin/env python3
"""
完整的效率指标提取脚本 - 4方法对比
支持从所有Baseline结果和BM Agent日志中提取效率指标
"""

import json
import re
from pathlib import Path
from typing import Dict, List
import statistics

PATIENT_IDS = ['605525', '612908', '638114', '640880', '648772', '665548', '708387', '747724', '868183']
ROOT = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent")


def extract_websearch_metrics(patient_id: str) -> Dict:
    """从Web Search结果中提取效率指标，包括搜索次数"""
    file_path = ROOT / f"baseline/set1_results_v2/websearch/{patient_id}_baseline_results.json"
    if not file_path.exists():
        return None

    try:
        data = json.loads(file_path.read_text(encoding='utf-8'))
        result = list(data.get('results', {}).values())[0]
        full_output = result.get('full_output', {})

        # 从usage获取实际token（如果存在）
        usage = full_output.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)

        # 如果没有usage数据，估算
        if input_tokens == 0:
            patient_input = data.get('patient_input_preview', '')
            input_tokens = estimate_tokens(patient_input)

        if output_tokens == 0:
            report = result.get('report', '')
            output_tokens = estimate_tokens(report)

        # 统计搜索次数
        search_count = 0
        if 'output' in full_output:
            for item in full_output['output']:
                if item.get('type') == 'web_search_call':
                    search_count += 1

        return {
            'latency_ms': result.get('latency_ms', 0),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'search_count': search_count,
            'has_real_usage': usage.get('input_tokens', 0) > 0
        }
    except Exception as e:
        print(f"Error extracting Web Search metrics for {patient_id}: {e}")
        return None


def extract_rag_metrics(patient_id: str) -> Dict:
    """从RAG结果中提取效率指标，包括检索文档数"""
    file_path = ROOT / f"baseline/set1_results/rag/{patient_id}_baseline_results.json"
    if not file_path.exists():
        return None

    try:
        data = json.loads(file_path.read_text(encoding='utf-8'))
        result = list(data.get('results', {}).values())[0]
        full_output = result.get('full_output', {})

        # 从usage获取实际token（如果存在）
        usage = full_output.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)

        # 如果没有usage数据，估算
        if input_tokens == 0:
            patient_input = data.get('patient_input_preview', '')
            # RAG的输入还包括检索的文档
            retrieved_docs = result.get('retrieved_docs', [])
            docs_text = '\n'.join([d.get('content', '') for d in retrieved_docs])
            input_tokens = estimate_tokens(patient_input) + estimate_tokens(docs_text[:5000])  # 限制文档长度

        if output_tokens == 0:
            report = result.get('report', '')
            output_tokens = estimate_tokens(report)

        # RAG只检索一次，获取检索文档数
        retrieved_count = len(result.get('retrieved_docs', []))

        return {
            'latency_ms': result.get('latency_ms', 0),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'retrieval_count': 1,  # RAG只检索一次
            'retrieved_docs_count': retrieved_count,
            'has_real_usage': usage.get('input_tokens', 0) > 0
        }
    except Exception as e:
        print(f"Error extracting RAG metrics for {patient_id}: {e}")
        return None


def extract_direct_llm_metrics(patient_id: str) -> Dict:
    """从Direct LLM结果中提取效率指标"""
    file_path = ROOT / f"baseline/set1_results/direct_llm/{patient_id}_baseline_results.json"
    if not file_path.exists():
        return None

    try:
        data = json.loads(file_path.read_text(encoding='utf-8'))
        result = list(data.get('results', {}).values())[0]
        full_output = result.get('full_output', {})

        # 从usage获取实际token（如果存在）
        usage = full_output.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)

        # 如果没有usage数据，估算
        if input_tokens == 0:
            patient_input = data.get('patient_input_preview', '')
            input_tokens = estimate_tokens(patient_input)

        if output_tokens == 0:
            report = result.get('report', '')
            output_tokens = estimate_tokens(report)

        return {
            'latency_ms': result.get('latency_ms', 0),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'has_real_usage': usage.get('input_tokens', 0) > 0
        }
    except Exception as e:
        print(f"Error extracting Direct LLM metrics for {patient_id}: {e}")
        return None


def extract_bm_agent_metrics(patient_id: str) -> Dict:
    """从BM Agent日志中提取效率指标"""
    log_dir = ROOT / "workspace/sandbox/execution_logs"
    pattern = f"session_*_{patient_id}_*_structured.jsonl"
    log_files = list(log_dir.glob(pattern))

    if not log_files:
        return None

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

        return {
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'tool_calls': tool_calls,
            'log_file': str(log_file.name)
        }
    except Exception as e:
        print(f"Error reading {log_file}: {e}")
        return None


def estimate_tokens(text: str) -> int:
    """基于字符数估算token数量"""
    if not text:
        return 0
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    punct = len(re.findall(r'[^\w\u4e00-\u9fff\s]', text))
    return int(cn_chars * 1.5 + en_words * 1.3 + punct * 0.5)


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
    print("效率指标提取 - 4方法完整对比")
    print("=" * 80)
    print()

    # 存储所有结果
    all_metrics = {
        'direct_llm': {},
        'rag': {},
        'websearch': {},
        'bm_agent': {}
    }

    for pid in PATIENT_IDS:
        print(f"Processing patient {pid}...")

        # 提取各方法指标
        direct = extract_direct_llm_metrics(pid)
        if direct:
            all_metrics['direct_llm'][pid] = direct

        rag = extract_rag_metrics(pid)
        if rag:
            all_metrics['rag'][pid] = rag

        websearch = extract_websearch_metrics(pid)
        if websearch:
            all_metrics['websearch'][pid] = websearch

        bm = extract_bm_agent_metrics(pid)
        if bm:
            all_metrics['bm_agent'][pid] = bm

    # 打印汇总
    print("\n" + "=" * 80)
    print("效率指标汇总")
    print("=" * 80)

    # 延迟对比
    print("\n【1. 平均端到端延迟 (ms)】")
    print("-" * 70)
    for method, label in [('direct_llm', 'Direct LLM'), ('rag', 'RAG V2'), ('websearch', 'Web Search V2')]:
        metrics = all_metrics[method]
        latencies = [m['latency_ms'] for m in metrics.values() if m.get('latency_ms', 0) > 0]
        if latencies:
            stats = calculate_statistics(latencies)
            print(f"{label:20s}: {stats['mean']:>10.1f} ± {stats['std']:>8.1f} ms (n={len(latencies)})")

    # Token对比
    print("\n【2. 单例平均输入 (tokens)】")
    print("-" * 70)
    for method, label in [('direct_llm', 'Direct LLM'), ('rag', 'RAG V2'), ('websearch', 'Web Search V2'), ('bm_agent', 'BM Agent')]:
        metrics = all_metrics[method]
        values = [m['input_tokens'] for m in metrics.values() if m.get('input_tokens', 0) > 0]
        real_count = sum(1 for m in metrics.values() if m.get('has_real_usage', False))
        if values:
            stats = calculate_statistics(values)
            note = f" [{real_count} with real usage]" if real_count > 0 else " [estimated]"
            print(f"{label:20s}: {stats['mean']:>10.0f} ± {stats['std']:>8.0f} tokens{note}")

    print("\n【3. 单例平均输出 (tokens)】")
    print("-" * 70)
    for method, label in [('direct_llm', 'Direct LLM'), ('rag', 'RAG V2'), ('websearch', 'Web Search V2'), ('bm_agent', 'BM Agent')]:
        metrics = all_metrics[method]
        values = [m['output_tokens'] for m in metrics.values() if m.get('output_tokens', 0) > 0]
        real_count = sum(1 for m in metrics.values() if m.get('has_real_usage', False))
        if values:
            stats = calculate_statistics(values)
            note = f" [{real_count} with real usage]" if real_count > 0 else " [estimated]"
            print(f"{label:20s}: {stats['mean']:>10.0f} ± {stats['std']:>8.0f} tokens{note}")

    # I/O比值
    print("\n【4. 输入/输出比值】")
    print("-" * 70)
    for method, label in [('direct_llm', 'Direct LLM'), ('rag', 'RAG V2'), ('websearch', 'Web Search V2'), ('bm_agent', 'BM Agent')]:
        metrics = all_metrics[method]
        ratios = [m['input_tokens'] / m['output_tokens'] for m in metrics.values()
                  if m.get('input_tokens', 0) > 0 and m.get('output_tokens', 0) > 0]
        if ratios:
            mean_ratio = statistics.mean(ratios)
            print(f"{label:20s}: {mean_ratio:>10.2f}")

    # 环境调用统计
    print("\n【5. 底层环境调用统计】")
    print("-" * 70)

    # Web Search搜索次数
    ws_metrics = all_metrics['websearch']
    search_counts = [m['search_count'] for m in ws_metrics.values() if 'search_count' in m]
    if search_counts:
        stats = calculate_statistics(search_counts)
        print(f"Web Search 搜索次数: {stats['mean']:.1f} ± {stats['std']:.1f} (range: {stats['min']:.0f}-{stats['max']:.0f})")

    # RAG检索文档数
    rag_metrics = all_metrics['rag']
    doc_counts = [m['retrieved_docs_count'] for m in rag_metrics.values() if 'retrieved_docs_count' in m]
    if doc_counts:
        stats = calculate_statistics(doc_counts)
        print(f"RAG 检索文档数: {stats['mean']:.1f} ± {stats['std']:.1f} (range: {stats['min']:.0f}-{stats['max']:.0f})")

    # BM Agent工具调用
    bm_metrics = all_metrics['bm_agent']
    tool_counts = [m['tool_calls'] for m in bm_metrics.values() if 'tool_calls' in m]
    if tool_counts:
        stats = calculate_statistics(tool_counts)
        print(f"BM Agent 工具调用: {stats['mean']:.1f} ± {stats['std']:.1f} (range: {stats['min']:.0f}-{stats['max']:.0f})")

    # 保存完整结果
    output_file = ROOT / "analysis/complete_efficiency_metrics.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'patient_ids': PATIENT_IDS,
            'metrics': all_metrics,
            'note': 'Token data: Web Search has real usage from API; others estimated if not available'
        }, f, indent=2, ensure_ascii=False)

    print(f"\n完整结果已保存: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
