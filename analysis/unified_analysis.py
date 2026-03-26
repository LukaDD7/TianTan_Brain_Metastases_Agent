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

    def load_bm_agent_results_from_samples(self) -> List[Dict]:
        """
        从 analysis/samples/ 目录加载 BM Agent 归档数据

        读取内容：
        - report: 从 MDT_Report_{id}.md
        - reasoning: 从 execution_log 的 llm_response 内容
        - tool_calls: 从 execution_log 的 tool_call 条目
        - latency_ms: 累加所有 duration_ms
        - tokens: 累加所有 llm_response.usage
        """
        results = []
        samples_dir = Path("analysis/samples")

        if not samples_dir.exists():
            print("⚠️ analysis/samples/ 目录不存在")
            return results

        for patient_dir in samples_dir.iterdir():
            if not patient_dir.is_dir():
                continue

            patient_id = patient_dir.name
            report_file = patient_dir / f"MDT_Report_{patient_id}.md"
            log_file = patient_dir / "bm_agent_execution_log.jsonl"

            if not report_file.exists() or not log_file.exists():
                continue

            try:
                # 读取报告
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()

                # 解析执行日志
                tool_calls = []
                reasoning_parts = []
                total_duration_ms = 0
                total_tokens = {"input": 0, "output": 0, "total": 0}
                timestamp = ""

                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_type = entry.get("type")

                            if entry_type == "tool_call":
                                tool_calls.append({
                                    "tool_name": entry.get("tool_name"),
                                    "duration_ms": entry.get("duration_ms", 0),
                                    "timestamp": entry.get("timestamp")
                                })
                                total_duration_ms += entry.get("duration_ms", 0)

                            elif entry_type == "llm_response":
                                # 提取token使用量
                                usage = entry.get("usage", {})
                                if usage:
                                    total_tokens["input"] += usage.get("input_tokens", 0)
                                    total_tokens["output"] += usage.get("output_tokens", 0)
                                    total_tokens["total"] += usage.get("total_tokens", 0)

                                # 收集推理内容
                                content = entry.get("content", "")
                                if content and len(reasoning_parts) < 5:  # 前5个推理片段
                                    reasoning_parts.append(content[:500])  # 限制长度

                            # 记录时间戳
                            if not timestamp and entry.get("timestamp"):
                                timestamp = entry.get("timestamp")

                        except json.JSONDecodeError:
                            continue

                # 构建标准化数据
                patient_data = {
                    "patient_id": patient_id,
                    "hospital_id": patient_id,  # 假设相同
                    "method": "bm_agent",
                    "timestamp": timestamp,
                    "report": report_content,
                    "reasoning": "\n...\n".join(reasoning_parts),
                    "latency_ms": total_duration_ms,
                    "tokens": total_tokens,
                    "tool_calls": tool_calls,
                    "num_tool_calls": len(tool_calls),
                    "sources": []  # 可从报告中提取引用
                }

                results.append(patient_data)
                print(f"   Loaded BM Agent data: {patient_id} ({len(tool_calls)} tool calls, "
                      f"{total_tokens['total']} tokens, {total_duration_ms}ms)")

            except Exception as e:
                print(f"   Error loading {patient_id}: {e}")
                continue

        return results

    def load_all_results(self) -> Dict[str, List[Dict]]:
        """加载所有4种方法的结果"""
        all_results = self.load_baseline_results()
        all_results["bm_agent"] = self.load_bm_agent_results_from_samples()
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

        说明：CCR/MQR 为 0-4 分制，计算 CPI 时需先归一化到 0-1。
        公式：CPI = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)
        """
        return 0.35 * (ccr / 4.0) + 0.25 * ptr + 0.25 * (mqr / 4.0) + 0.15 * (1 - cer)


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
        # 导入时间戳工具
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.timestamp_utils import get_timestamped_filename
        self.get_timestamped_filename = get_timestamped_filename

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

        # 保存CSV - 使用带时间戳的文件名
        output_filename = self.get_timestamped_filename("summary_table", "csv")
        output_file = os.path.join(self.output_dir, output_filename)
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

        # 保存报告 - 使用带时间戳的文件名
        output_filename = self.get_timestamped_filename("comparison_report", "md")
        output_file = os.path.join(self.output_dir, output_filename)
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
