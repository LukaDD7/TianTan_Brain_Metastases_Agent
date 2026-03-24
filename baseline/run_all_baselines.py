#!/usr/bin/env python3
"""
Unified Baseline Evaluation Runner for Brain Metastases MDT Report Generation
支持三种Baseline方法：Direct LLM、RAG、WebSearch
每种方法使用各自的system_prompt，保留完整执行记录
BM Agent由用户单独运行（有HITL）
"""

import os
import sys
import json
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baseline.rag_guideline.rag_baseline import SimpleRAGBaseline
from baseline.direct_llm.direct_llm_baseline import DirectLLMBaseline
from baseline.web_search_llm.web_search_llm_baseline import WebSearchLLMBaseline


class UnifiedBaselineEvaluator:
    """统一评估器，支持三种Baseline方法"""

    def __init__(self):
        self.rag_baseline = None
        self.direct_llm = DirectLLMBaseline()
        self.websearch_llm = WebSearchLLMBaseline()

    def initialize_rag(self):
        """初始化RAG（可选，因为初始化耗时）"""
        print("Initializing RAG baseline...")
        self.rag_baseline = SimpleRAGBaseline()
        self.rag_baseline.initialize()
        print("✅ RAG initialized\n")

    def format_patient_info(self, row: pd.Series) -> str:
        """格式化患者信息（仅输入特征，不含标签）"""
        info_lines = []

        # 基本信息
        info_lines.append(f"住院号: {row.get('住院号', 'N/A')}")
        info_lines.append(f"年龄: {row.get('年龄', 'N/A')}岁")
        info_lines.append(f"性别: {row.get('性别', 'N/A')}")

        # 主诉和病史
        if pd.notna(row.get('主诉')):
            info_lines.append(f"\n主诉: {row['主诉']}")
        if pd.notna(row.get('现病史')):
            info_lines.append(f"现病史: {row['现病史']}")
        if pd.notna(row.get('既往史')):
            info_lines.append(f"既往史: {row['既往史']}")

        # 影像学
        if pd.notna(row.get('头部MRI')):
            info_lines.append(f"\n头部MRI: {row['头部MRI']}")
        if pd.notna(row.get('胸部CT')) and str(row.get('胸部CT', '')).strip():
            info_lines.append(f"胸部CT: {row['胸部CT']}")
        if pd.notna(row.get('颈椎MRI')) and str(row.get('颈椎MRI', '')).strip():
            info_lines.append(f"颈椎MRI: {row['颈椎MRI']}")
        if pd.notna(row.get('腰椎MRI')) and str(row.get('腰椎MRI', '')).strip():
            info_lines.append(f"腰椎MRI: {row['腰椎MRI']}")
        if pd.notna(row.get('腹盆CT')) and str(row.get('腹盆CT', '')).strip():
            info_lines.append(f"腹盆CT: {row['腹盆CT']}")

        return "\n".join(info_lines)

    def run_direct_llm(self, patient_info: str) -> Dict:
        """运行Direct LLM Baseline"""
        print("  Running Direct LLM baseline...")
        result = self.direct_llm.query(
            question=patient_info,
            save_full_output=True  # 保存完整输出
        )
        return {
            "method": "Direct_LLM",
            "report": result.get("response", ""),
            "reasoning": result.get("reasoning", ""),
            "latency_ms": result.get("latency_ms", 0),
            "full_output": result.get("full_output", {}),
            "timestamp": datetime.now().isoformat()
        }

    def run_rag(self, patient_info: str) -> Dict:
        """运行RAG Baseline"""
        if not self.rag_baseline:
            raise ValueError("RAG not initialized. Call initialize_rag() first.")
        print("  Running RAG baseline...")
        result = self.rag_baseline.query(
            question=patient_info,
            save_full_output=True  # 保存完整输出
        )
        return {
            "method": "RAG",
            "report": result.get("response", ""),
            "reasoning": result.get("reasoning", ""),
            "sources": result.get("sources", []),
            "retrieved_docs": result.get("retrieved_docs", []),
            "latency_ms": result.get("latency_ms", 0),
            "full_output": result.get("full_output", {}),
            "timestamp": datetime.now().isoformat()
        }

    def run_websearch(self, patient_info: str) -> Dict:
        """运行WebSearch LLM Baseline"""
        print("  Running WebSearch LLM baseline...")
        result = self.websearch_llm.query(
            question=patient_info,
            save_full_output=True  # 保存完整输出
        )
        return {
            "method": "WebSearch_LLM",
            "report": result.get("response", ""),
            "reasoning": result.get("reasoning", ""),
            "search_sources": result.get("search_sources", []),
            "latency_ms": result.get("latency_ms", 0),
            "full_output": result.get("full_output", {}),
            "timestamp": datetime.now().isoformat()
        }

    def evaluate_patient(self, row: pd.Series, output_dir: str, methods: List[str] = None):
        """评估单个患者，使用指定的methods"""
        patient_id = row.get('patient_id', f"Case{row.get('住院号', 'unknown')}")
        hospital_id = row.get('住院号', 'unknown')

        methods = methods or ["direct_llm", "rag", "websearch"]

        print(f"\n{'='*60}")
        print(f"Evaluating Patient: {patient_id} (住院号: {hospital_id})")
        print(f"Methods: {', '.join(methods)}")
        print(f"{'='*60}")

        # 格式化患者信息
        patient_info = self.format_patient_info(row)

        # 运行指定的baselines
        results = {}
        if "direct_llm" in methods:
            try:
                results["direct_llm"] = self.run_direct_llm(patient_info)
            except Exception as e:
                print(f"  ❌ Direct LLM failed: {e}")
                results["direct_llm"] = {"error": str(e)}

        if "rag" in methods:
            try:
                results["rag"] = self.run_rag(patient_info)
            except Exception as e:
                print(f"  ❌ RAG failed: {e}")
                results["rag"] = {"error": str(e)}

        if "websearch" in methods:
            try:
                results["websearch"] = self.run_websearch(patient_info)
            except Exception as e:
                print(f"  ❌ WebSearch failed: {e}")
                results["websearch"] = {"error": str(e)}

        # 准备输出
        output = {
            "patient_id": patient_id,
            "hospital_id": str(hospital_id),
            "patient_info": patient_info,
            "results": results,
            "evaluation_timestamp": datetime.now().isoformat()
        }

        # 保存结果
        output_file = os.path.join(output_dir, f"{patient_id}_baseline_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"  Results saved to: {output_file}")

        return output

    def run_evaluation(self, csv_path: str, output_dir: str = "baseline/results",
                       methods: List[str] = None, max_patients: int = None):
        """
        运行完整评估

        Args:
            csv_path: 患者CSV文件路径
            output_dir: 输出目录
            methods: 要运行的方法列表 ["direct_llm", "rag", "websearch"]
            max_patients: 最大评估患者数（None表示全部）
        """
        methods = methods or ["direct_llm", "rag", "websearch"]

        # 如果需要RAG，先初始化
        if "rag" in methods:
            self.initialize_rag()

        # 创建输出目录结构
        os.makedirs(output_dir, exist_ok=True)
        for method in methods:
            os.makedirs(os.path.join(output_dir, method), exist_ok=True)

        # 加载患者
        print(f"Loading patients from: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"Loaded {len(df)} patients")

        # 限制患者数
        if max_patients and max_patients < len(df):
            df = df.head(max_patients)
            print(f"Evaluating first {max_patients} patients")

        # 评估每个患者
        all_results = []
        for idx, row in df.iterrows():
            result = self.evaluate_patient(row, output_dir, methods)
            all_results.append(result)

        # 保存汇总
        summary_file = os.path.join(output_dir, "baseline_evaluation_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_patients": len(all_results),
                "methods": methods,
                "evaluation_date": datetime.now().isoformat(),
                "patients": [r["patient_id"] for r in all_results]
            }, f, ensure_ascii=False, indent=2)

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

    parser = argparse.ArgumentParser(description="Unified Baseline Evaluation")
    parser.add_argument("--csv", default="baseline/test_patients.csv",
                        help="Path to patients CSV file")
    parser.add_argument("--output", default="baseline/results",
                        help="Output directory")
    parser.add_argument("--methods", nargs="+",
                        choices=["direct_llm", "rag", "websearch"],
                        default=["direct_llm", "rag", "websearch"],
                        help="Methods to evaluate")
    parser.add_argument("--max-patients", type=int, default=None,
                        help="Maximum number of patients to evaluate")

    args = parser.parse_args()

    evaluator = UnifiedBaselineEvaluator()

    # 运行评估
    results = evaluator.run_evaluation(
        csv_path=args.csv,
        output_dir=args.output,
        methods=args.methods,
        max_patients=args.max_patients
    )

    print("\n✅ Baseline evaluation completed successfully!")
    print("\nOutput structure:")
    for method in args.methods:
        print(f"  {args.output}/{method}/")
        print(f"    - {method}_results.json (individual results)")
    print(f"  {args.output}/baseline_evaluation_summary.json")


if __name__ == "__main__":
    main()
