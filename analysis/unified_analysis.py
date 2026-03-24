#!/usr/bin/env python3
"""
Unified Analysis Pipeline for Brain Metastases MDT Evaluation
支持4种方法：Direct LLM, RAG, WebSearch, BM Agent

学术规范要求：
- 所有指标统一对比（CCR, PTR, MQR, CER, CPI）
- Token消耗、推理过程、时间开销可视化
- 工具调用频率统计（仅BM Agent和WebSearch）
- 统计显著性检验
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UnifiedDataLoader:
    """
    统一数据加载器 - 支持4种方法的数据加载
    """

    def __init__(self, baseline_results_dir: str = "baseline/results",
                 bm_agent_results_dir: str = "workspace/sandbox/patients"):
        self.baseline_dir = baseline_results_dir
        self.bm_agent_dir = bm_agent_results_dir

    def load_baseline_results(self) -> Dict[str, List[Dict]]:
        """
        加载3种Baseline的结果

        Returns:
            {
                "direct_llm": [patient1_data, patient2_data, ...],
                "rag": [...],
                "websearch": [...]
            }
        """
        results = {"direct_llm": [], "rag": [], "websearch": []}

        # 查找所有 *_baseline_results.json 文件
        result_files = sorted(Path(self.baseline_dir).glob("*_baseline_results.json"))

        for file_path in result_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                patient_id = data.get("patient_id", file_path.stem.replace("_baseline_results", ""))

                # 提取每种方法的结果
                for method in ["direct_llm", "rag", "websearch"]:
                    if method in data.get("results", {}):
                        method_data = data["results"][method]
                        # 标准化字段
                        standardized = self._standardize_baseline_data(
                            patient_id=patient_id,
                            hospital_id=data.get("hospital_id", ""),
                            method=method,
                            data=method_data
                        )
                        results[method].append(standardized)

        return results

    def _standardize_baseline_data(self, patient_id: str, hospital_id: str,
                                   method: str, data: Dict) -> Dict:
        """标准化Baseline数据格式"""

        # 从full_output提取token使用量
        usage = data.get("full_output", {}).get("usage", {})

        return {
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "method": method,
            "timestamp": data.get("timestamp", ""),
            "report": data.get("response", ""),
            "reasoning": data.get("reasoning", ""),
            "latency_ms": data.get("latency_ms", 0),
            "tokens": {
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
                "total": usage.get("total_tokens", 0)
            },
            "sources": data.get("sources", []) if method == "rag" else
                      data.get("search_sources", []) if method == "websearch" else [],
            "retrieved_docs": data.get("retrieved_docs", []) if method == "rag" else [],
            "full_output": data.get("full_output", {})
        }

    def load_bm_agent_results_placeholder(self) -> List[Dict]:
        """
        【占位符】加载BM Agent结果

        TODO: 实现BM Agent数据加载
        需要从execution_logs和patient reports中提取：
        - report内容
        - reasoning过程
        - tool_calls列表
        - latency（从duration_ms累加）
        - token使用量（需要添加记录）

        Returns:
            [patient1_data, patient2_data, ...]
        """
        print("⚠️ BM Agent结果加载为占位符，需要实现")

        # TODO: 实现实际加载逻辑
        # 示例结构：
        return [{
            "patient_id": "PLACEHOLDER",
            "hospital_id": "",
            "method": "bm_agent",
            "timestamp": "",
            "report": "",
            "reasoning": "",
            "latency_ms": 0,  # 从execution_logs累加
            "tokens": {
                "input": 0,  # 需要添加记录
                "output": 0,
                "total": 0
            },
            "tool_calls": [],  # 从execution_logs提取
            "full_output": {}
        }]

    def load_all_results(self) -> Dict[str, List[Dict]]:
        """加载所有4种方法的结果"""
        all_results = self.load_baseline_results()
        all_results["bm_agent"] = self.load_bm_agent_results_placeholder()
        return all_results


class MetricsCalculator:
    """
    指标计算器 - 计算CCR, PTR, MQR, CER, CPI
    """

    @staticmethod
    def calculate_ccr(report: str, ground_truth: Dict) -> Dict:
        """
        计算临床决策一致性准确率 (CCR)

        维度：
        - 治疗线判定 (40%)
        - 方案选择 (35%)
        - 剂量参数 (15%)
        - 排他性论证 (10%)
        """
        # TODO: 实现CCR计算
        # 需要解析report提取关键决策点
        return {
            "treatment_line": 0.0,  # 0-4分
            "scheme_selection": 0.0,  # 0-4分
            "dosage_params": 0.0,  # 0-4分
            "exclusion": 0.0,  # 0-4分
            "overall": 0.0  # 加权CCR值
        }

    @staticmethod
    def calculate_ptr(report: str) -> Dict:
        """
        计算物理可追溯率 (PTR)

        评分：
        - 2分: 完全可追溯 (PMID可查、URL可访问)
        - 1分: 部分可追溯 (格式不规范)
        - 0分: 不可追溯 (数字引用[1,45])
        """
        import re

        # 提取所有引用
        citations = {
            "pubmed": re.findall(r'\[PubMed:\s*PMID\s+(\d+)\]', report),
            "oncokb": re.findall(r'\[OncoKB:\s*([^\]]+)\]', report),
            "guideline": re.findall(r'\[Guideline:\s*([^\]]+)\]', report),
            "local": re.findall(r'\[Local:\s*([^\]]+)\]', report),
            "web": re.findall(r'\[Web:\s*([^,\]]+)', report),
            "parametric": re.findall(r'\[Parametric Knowledge:\s*([^\]]+)\]', report),
            "digital": re.findall(r'\[(\d+(?:,\s*\d+)*)\]', report)  # [1,45]等数字引用
        }

        # 计算可追溯性
        total_claims = len(citations["pubmed"]) + len(citations["oncokb"]) + \
                      len(citations["guideline"]) + len(citations["local"]) + \
                      len(citations["web"]) + len(citations["parametric"]) + \
                      len(citations["digital"])

        if total_claims == 0:
            return {"ptr": 0.0, "traceable": 0, "total": 0, "breakdown": citations}

        # 完全可追溯：PubMed, OncoKB, Guideline, Local
        fully_traceable = len(citations["pubmed"]) + len(citations["oncokb"]) + \
                         len(citations["guideline"]) + len(citations["local"])

        # 部分可追溯：Web, Parametric (honest标注)
        partially_traceable = len(citations["web"]) + len(citations["parametric"])

        # 不可追溯：数字引用
        non_traceable = len(citations["digital"])

        # 计算加权得分
        ptr = (2 * fully_traceable + 1 * partially_traceable) / (2 * total_claims)

        return {
            "ptr": round(ptr, 3),
            "traceable": fully_traceable + partially_traceable,
            "total": total_claims,
            "breakdown": {
                "fully_traceable": citations["pubmed"] + citations["oncokb"] +
                                  citations["guideline"] + citations["local"],
                "partially_traceable": citations["web"] + citations["parametric"],
                "non_traceable": citations["digital"]
            }
        }

    @staticmethod
    def calculate_mqr(report: str) -> Dict:
        """
        计算MDT报告规范度 (MQR)

        维度：
        - 8模块完整性 (40%)
        - 模块适用性判断 (30%)
        - 结构化程度 (20%)
        - 不确定性处理 (10%)
        """
        # TODO: 实现MQR计算
        return {
            "module_completeness": 0.0,
            "module_applicability": 0.0,
            "structured": 0.0,
            "uncertainty": 0.0,
            "overall": 0.0
        }

    @staticmethod
    def calculate_cer(report: str) -> Dict:
        """
        计算临床错误率 (CER)

        错误分类：
        - 严重错误 (权重3.0)
        - 主要错误 (权重2.0)
        - 次要错误 (权重1.0)
        """
        # TODO: 实现CER计算
        return {
            "critical_errors": [],
            "major_errors": [],
            "minor_errors": [],
            "weighted_score": 0.0,
            "cer": 0.0
        }

    @staticmethod
    def calculate_cpi(ccr: float, ptr: float, mqr: float, cer: float) -> float:
        """
        计算综合性能指数 (CPI)

        公式：CPI = 0.35×CCR + 0.25×PTR + 0.25×MQR + 0.15×(1-CER)
        """
        return 0.35 * ccr + 0.25 * ptr + 0.25 * mqr + 0.15 * (1 - cer)


class StatisticalAnalyzer:
    """
    统计分析器
    """

    @staticmethod
    def descriptive_stats(values: List[float]) -> Dict:
        """描述性统计"""
        return {
            "n": len(values),
            "mean": np.mean(values),
            "std": np.std(values),
            "median": np.median(values),
            "min": np.min(values),
            "max": np.max(values),
            "q25": np.percentile(values, 25),
            "q75": np.percentile(values, 75)
        }

    @staticmethod
    def significance_test(baseline_values: List[float],
                         bm_agent_values: List[float]) -> Dict:
        """
        显著性检验 (Wilcoxon signed-rank test)

        由于样本量小(n<30)，使用非参数检验
        """
        from scipy import stats

        if len(baseline_values) != len(bm_agent_values):
            return {"error": "Sample sizes do not match"}

        # Wilcoxon signed-rank test (配对样本)
        statistic, pvalue = stats.wilcoxon(baseline_values, bm_agent_values)

        return {
            "test": "Wilcoxon signed-rank test",
            "statistic": statistic,
            "pvalue": pvalue,
            "significant": pvalue < 0.05,
            "n": len(baseline_values)
        }


class ReportGenerator:
    """
    报告生成器 - 生成学术规范的分析报告
    """

    def __init__(self, output_dir: str = "analysis/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_summary_table(self, results: Dict[str, List[Dict]]) -> pd.DataFrame:
        """生成汇总表格"""
        rows = []

        for method, patients in results.items():
            for patient in patients:
                row = {
                    "Method": method,
                    "Patient_ID": patient.get("patient_id"),
                    "Latency_ms": patient.get("latency_ms", 0),
                    "Input_Tokens": patient.get("tokens", {}).get("input", 0),
                    "Output_Tokens": patient.get("tokens", {}).get("output", 0),
                    "Total_Tokens": patient.get("tokens", {}).get("total", 0),
                    # TODO: 添加CCR, PTR, MQR, CER, CPI
                }
                rows.append(row)

        df = pd.DataFrame(rows)

        # 保存CSV
        output_file = os.path.join(self.output_dir, "summary_table.csv")
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        return df

    def generate_comparison_report(self, results: Dict[str, List[Dict]]) -> str:
        """生成对比分析报告 (Markdown)"""

        report = []
        report.append("# Brain Metastases MDT Methods Comparison Report")
        report.append(f"\nGenerated: {datetime.now().isoformat()}\n")

        # 1. 基本信息
        report.append("## 1. Overview\n")
        for method, patients in results.items():
            report.append(f"- **{method}**: {len(patients)} patients")

        # 2. Token消耗对比
        report.append("\n## 2. Token Usage Comparison\n")
        # TODO: 添加统计

        # 3. 延迟对比
        report.append("\n## 3. Latency Comparison\n")
        # TODO: 添加统计

        # 4. 指标对比
        report.append("\n## 4. Metrics Comparison (CCR/PTR/MQR/CER/CPI)\n")
        report.append("⚠️ **PLACEHOLDER**: BM Agent results not yet loaded\n")

        # 5. 统计显著性
        report.append("\n## 5. Statistical Significance\n")
        report.append("⚠️ **PLACEHOLDER**: Requires BM Agent results\n")

        report_text = "\n".join(report)

        # 保存报告
        output_file = os.path.join(self.output_dir, "comparison_report.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        return report_text


def main():
    """
    主函数 - 运行完整分析流程
    """
    print("="*60)
    print("Brain Metastases MDT Unified Analysis Pipeline")
    print("="*60)

    # 1. 加载数据
    print("\n1. Loading data...")
    loader = UnifiedDataLoader()
    results = loader.load_all_results()

    for method, patients in results.items():
        print(f"   {method}: {len(patients)} patients")

    # 2. 生成汇总表
    print("\n2. Generating summary table...")
    report_gen = ReportGenerator()
    summary_df = report_gen.generate_summary_table(results)
    print(f"   Saved to: analysis/reports/summary_table.csv")

    # 3. 生成对比报告
    print("\n3. Generating comparison report...")
    comparison_report = report_gen.generate_comparison_report(results)
    print(f"   Saved to: analysis/reports/comparison_report.md")

    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)
    print("\nNOTE: BM Agent analysis is PLACEHOLDER")
    print("Please implement load_bm_agent_results() when data is available.")


if __name__ == "__main__":
    main()
