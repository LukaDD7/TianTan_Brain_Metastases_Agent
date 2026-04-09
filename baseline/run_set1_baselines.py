#!/usr/bin/env python3
"""
Set-1 Baseline Re-evaluation Script
使用与BM Agent完全相同的输入文件重新运行Baseline
确保公平对比
"""

import os
import sys
import json
import time
import glob
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baseline.rag_guideline.rag_baseline import SimpleRAGBaseline
from baseline.direct_llm.direct_llm_baseline import DirectLLMBaseline
from baseline.web_search_llm.web_search_llm_baseline import WebSearchLLMBaseline


class Set1BaselineEvaluator:
    """Set-1 Baseline评估器，使用标准化输入文件"""

    def __init__(self):
        self.rag_baseline = None
        self.direct_llm = DirectLLMBaseline()
        self.websearch_llm = WebSearchLLMBaseline()
        self.patient_mapping = {
            "605525": "Case8",
            "612908": "Case7",
            "638114": "Case6",
            "640880": "Case2",
            "648772": "Case1",
            "665548": "Case4",
            "708387": "Case9",
            "747724": "Case10",
            "868183": "Case3"
        }

    def initialize_rag(self):
        """初始化RAG（可选，因为初始化耗时）"""
        print("Initializing RAG baseline...")
        self.rag_baseline = SimpleRAGBaseline()
        self.rag_baseline.initialize()
        print("✅ RAG initialized\n")

    def load_patient_input(self, file_path: str) -> str:
        """加载患者输入文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def run_direct_llm(self, patient_input: str, patient_id: str) -> Dict:
        """运行Direct LLM Baseline"""
        print(f"  Running Direct LLM baseline for {patient_id}...")
        start_time = time.time()
        result = self.direct_llm.query(
            question=patient_input,
            save_full_output=True
        )
        latency_ms = (time.time() - start_time) * 1000

        # 从full_output中提取token使用情况
        full_output = result.get("full_output", {})
        usage = full_output.get("usage", {})

        return {
            "method": "Direct_LLM",
            "patient_id": patient_id,
            "report": result.get("response", ""),
            "reasoning": result.get("reasoning", ""),
            "latency_ms": latency_ms,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "full_output": full_output,  # 保存完整执行记录
            "timestamp": datetime.now().isoformat()
        }

    def run_rag(self, patient_input: str, patient_id: str) -> Dict:
        """运行RAG Baseline"""
        if not self.rag_baseline:
            raise ValueError("RAG not initialized. Call initialize_rag() first.")

        print(f"  Running RAG baseline for {patient_id}...")
        start_time = time.time()
        result = self.rag_baseline.query(
            question=patient_input,
            save_full_output=True
        )
        latency_ms = (time.time() - start_time) * 1000

        # 从full_output中提取token使用情况
        full_output = result.get("full_output", {})
        usage = full_output.get("usage", {})

        return {
            "method": "RAG",
            "patient_id": patient_id,
            "report": result.get("response", ""),
            "reasoning": result.get("reasoning", ""),
            "sources": result.get("sources", []),
            "retrieved_docs": result.get("retrieved_docs", []),
            "latency_ms": latency_ms,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "full_output": full_output,  # 保存完整执行记录
            "timestamp": datetime.now().isoformat()
        }

    def run_websearch(self, patient_input: str, patient_id: str) -> Dict:
        """运行WebSearch LLM Baseline"""
        print(f"  Running WebSearch LLM baseline for {patient_id}...")
        start_time = time.time()
        result = self.websearch_llm.query(
            question=patient_input,
            save_full_output=True
        )
        latency_ms = (time.time() - start_time) * 1000

        # 从full_output中提取token使用情况
        full_output = result.get("full_output", {})
        usage = full_output.get("usage", {})

        return {
            "method": "WebSearch_LLM",
            "patient_id": patient_id,
            "report": result.get("response", ""),
            "reasoning": result.get("reasoning", ""),
            "search_sources": result.get("search_sources", []),
            "search_queries": result.get("search_queries", []),
            "latency_ms": latency_ms,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "full_output": full_output,  # 保存完整执行记录
            "timestamp": datetime.now().isoformat()
        }

    def evaluate_patient(self, patient_file: str, output_dir: str,
                         methods: List[str] = None) -> Dict:
        """评估单个患者"""
        patient_id = os.path.basename(patient_file).replace('patient_', '').replace('_input.txt', '')
        case_id = self.patient_mapping.get(patient_id, patient_id)

        methods = methods or ["direct_llm", "rag", "websearch"]

        print(f"\n{'='*60}")
        print(f"Evaluating Patient: {patient_id} (Case: {case_id})")
        print(f"Methods: {', '.join(methods)}")
        print(f"{'='*60}")

        # 加载患者输入
        patient_input = self.load_patient_input(patient_file)
        print(f"  Input length: {len(patient_input)} characters")

        # 运行指定的baselines
        results = {}

        if "direct_llm" in methods:
            try:
                results["direct_llm"] = self.run_direct_llm(patient_input, patient_id)
            except Exception as e:
                print(f"  ❌ Direct LLM failed: {e}")
                results["direct_llm"] = {"error": str(e)}

        if "rag" in methods:
            try:
                results["rag"] = self.run_rag(patient_input, patient_id)
            except Exception as e:
                print(f"  ❌ RAG failed: {e}")
                results["rag"] = {"error": str(e)}

        if "websearch" in methods:
            try:
                results["websearch"] = self.run_websearch(patient_input, patient_id)
            except Exception as e:
                print(f"  ❌ WebSearch failed: {e}")
                results["websearch"] = {"error": str(e)}

        # 准备输出
        output = {
            "patient_id": patient_id,
            "case_id": case_id,
            "patient_input_preview": patient_input[:500] + "..." if len(patient_input) > 500 else patient_input,
            "results": results,
            "evaluation_timestamp": datetime.now().isoformat()
        }

        # 保存结果 - 每个方法保存到单独的子目录
        for method in methods:
            if method in results:
                method_dir = os.path.join(output_dir, method)
                os.makedirs(method_dir, exist_ok=True)
                method_output = {
                    "patient_id": patient_id,
                    "case_id": case_id,
                    "patient_input_preview": output["patient_input_preview"],
                    "results": {method: results[method]},
                    "evaluation_timestamp": output["evaluation_timestamp"]
                }
                output_file = os.path.join(method_dir, f"{patient_id}_baseline_results.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(method_output, f, ensure_ascii=False, indent=2)
                print(f"  {method} results saved to: {output_file}")

        return output

    def run_evaluation(self, input_dir: str, output_dir: str = "baseline/set1_results",
                       methods: List[str] = None, max_patients: int = None):
        """
        运行完整评估

        Args:
            input_dir: 患者输入文件目录（包含patient_*.txt文件）
            output_dir: 输出目录
            methods: 要运行的方法列表 ["direct_llm", "rag", "websearch"]
            max_patients: 最大评估患者数（None表示全部）
        """
        methods = methods or ["direct_llm"]

        # 如果需要RAG，先初始化
        if "rag" in methods:
            self.initialize_rag()

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        for method in methods:
            os.makedirs(os.path.join(output_dir, method), exist_ok=True)

        # 加载患者文件
        patient_files = sorted(glob.glob(os.path.join(input_dir, "patient_*.txt")))
        print(f"Found {len(patient_files)} patient files in {input_dir}")

        # 限制患者数
        if max_patients and max_patients < len(patient_files):
            patient_files = patient_files[:max_patients]
            print(f"Evaluating first {max_patients} patients")

        # 评估每个患者
        all_results = []
        for patient_file in patient_files:
            result = self.evaluate_patient(patient_file, output_dir, methods)
            all_results.append(result)

        # 保存汇总
        summary = {
            "total_patients": len(all_results),
            "methods": methods,
            "input_source": input_dir,
            "evaluation_date": datetime.now().isoformat(),
            "patients": [
                {
                    "patient_id": r["patient_id"],
                    "case_id": r["case_id"]
                } for r in all_results
            ],
            "notes": "使用与BM Agent完全相同的Set-1输入文件，确保公平对比"
        }

        summary_file = os.path.join(output_dir, "set1_baseline_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"Evaluation Complete!")
        print(f"Total patients: {len(all_results)}")
        print(f"Methods: {', '.join(methods)}")
        print(f"Results saved to: {output_dir}")
        print(f"{'='*60}")

        return all_results


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Set-1 Baseline Re-evaluation")
    parser.add_argument("--input-dir", default="baseline/set1_inputs",
                        help="Directory containing patient input files")
    parser.add_argument("--output", default="baseline/set1_results",
                        help="Output directory")
    parser.add_argument("--methods", nargs="+",
                        choices=["direct_llm", "rag", "websearch"],
                        default=["direct_llm"],
                        help="Methods to evaluate")
    parser.add_argument("--max-patients", type=int, default=None,
                        help="Maximum number of patients to evaluate")

    args = parser.parse_args()

    evaluator = Set1BaselineEvaluator()

    # 运行评估
    results = evaluator.run_evaluation(
        input_dir=args.input_dir,
        output_dir=args.output,
        methods=args.methods,
        max_patients=args.max_patients
    )

    print("\n✅ Set-1 Baseline re-evaluation completed successfully!")
    print(f"\nOutput structure:")
    print(f"  {args.output}/")
    for method in args.methods:
        print(f"    {method}/")
    print(f"    set1_baseline_summary.json")


if __name__ == "__main__":
    main()
