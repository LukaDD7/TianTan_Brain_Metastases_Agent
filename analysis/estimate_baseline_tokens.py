#!/usr/bin/env python3
"""
估算Baseline方法的Token数量并更新效率指标
由于之前的Baseline运行未保存token数据，使用基于字符数的估算方法
"""

import json
import re
from pathlib import Path
import statistics

ROOT = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent")
PATIENT_IDS = ['605525', '612908', '638114', '640880', '648772', '665548', '708387', '747724', '868183']


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


def extract_baseline_tokens(method: str) -> dict:
    """从baseline结果中估算token数量"""
    results = {}

    if method == "direct_llm":
        base_path = ROOT / "baseline/set1_results/direct_llm"
    elif method == "rag":
        base_path = ROOT / "baseline/set1_results/rag"
    elif method == "websearch":
        base_path = ROOT / "baseline/set1_results_v2/websearch"
    else:
        return results

    for pid in PATIENT_IDS:
        file_path = base_path / f"{pid}_baseline_results.json"
        if not file_path.exists():
            continue

        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
            result_key = list(data.get('results', {}).keys())[0]
            result = data['results'][result_key]

            # 估算输入token（patient_input_preview）
            patient_input = data.get('patient_input_preview', '')
            input_tokens = estimate_tokens(patient_input)

            # 估算输出token（report）
            report = result.get('report', '')
            output_tokens = estimate_tokens(report)

            results[pid] = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'io_ratio': input_tokens / output_tokens if output_tokens > 0 else 0
            }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    return results


def calculate_statistics(values):
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
    print("=" * 70)
    print("估算Baseline方法的Token数量")
    print("=" * 70)
    print()

    # 提取各方法的token估算
    print("[1/3] 估算 Direct LLM tokens...")
    direct_tokens = extract_baseline_tokens("direct_llm")

    print("[2/3] 估算 RAG V2 tokens...")
    rag_tokens = extract_baseline_tokens("rag")

    print("[3/3] 估算 Web Search V2 tokens...")
    web_tokens = extract_baseline_tokens("websearch")

    # 打印结果
    print("\n" + "=" * 70)
    print("Token估算结果")
    print("=" * 70)

    methods_data = {
        'Direct LLM': direct_tokens,
        'RAG V2': rag_tokens,
        'Web Search V2': web_tokens,
    }

    for method_name, tokens in methods_data.items():
        if not tokens:
            continue

        input_values = [t['input_tokens'] for t in tokens.values()]
        output_values = [t['output_tokens'] for t in tokens.values()]
        ratio_values = [t['io_ratio'] for t in tokens.values() if t['io_ratio'] > 0]

        input_stats = calculate_statistics(input_values)
        output_stats = calculate_statistics(output_values)
        ratio_mean = statistics.mean(ratio_values) if ratio_values else 0

        print(f"\n【{method_name}】")
        print(f"  输入Tokens: {input_stats['mean']:.0f} ± {input_stats['std']:.0f}")
        print(f"  输出Tokens: {output_stats['mean']:.0f} ± {output_stats['std']:.0f}")
        print(f"  I/O比值: {ratio_mean:.2f}")

    # 保存估算结果
    output_file = ROOT / "analysis/baseline_token_estimates.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'note': 'Token数量基于字符数估算（中文字符1.5 tokens/字，英文单词1.3 tokens/词）',
            'methods': {
                'direct_llm': direct_tokens,
                'rag': rag_tokens,
                'websearch': web_tokens
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n估算结果已保存: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
