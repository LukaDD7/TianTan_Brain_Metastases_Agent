#!/usr/bin/env python3
"""
Data Extraction Utilities
从各种来源提取数据并标准化
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BaselineDataExtractor:
    """
    从Baseline结果文件提取数据
    """

    @staticmethod
    def extract_from_result_file(file_path: str) -> Optional[Dict]:
        """
        从单个Baseline结果文件提取数据

        Returns:
            {
                "patient_id": str,
                "hospital_id": str,
                "direct_llm": {...},
                "rag": {...},
                "websearch": {...}
            }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    @staticmethod
    def extract_all_baseline_results(results_dir: str = "baseline/results") -> Dict[str, List[Dict]]:
        """
        提取所有Baseline结果

        Returns:
            {
                "direct_llm": [patient1, patient2, ...],
                "rag": [...],
                "websearch": [...]
            }
        """
        results = {"direct_llm": [], "rag": [], "websearch": []}

        result_files = sorted(Path(results_dir).glob("*_baseline_results.json"))

        for file_path in result_files:
            data = BaselineDataExtractor.extract_from_result_file(str(file_path))
            if not data:
                continue

            patient_id = data.get("patient_id", file_path.stem.replace("_baseline_results", ""))

            for method in ["direct_llm", "rag", "websearch"]:
                if method not in data.get("results", {}):
                    continue

                method_data = data["results"][method]

                # 标准化
                standardized = {
                    "patient_id": patient_id,
                    "hospital_id": data.get("hospital_id", ""),
                    "method": method,
                    "timestamp": method_data.get("timestamp", ""),
                    "report": method_data.get("response", ""),
                    "reasoning": method_data.get("reasoning", ""),
                    "latency_ms": method_data.get("latency_ms", 0),
                    "tokens": BaselineDataExtractor._extract_tokens(method_data),
                    "sources": method_data.get("sources", []) if method == "rag" else
                              method_data.get("search_sources", []) if method == "websearch" else [],
                    "tool_calls": [],  # Baseline无工具调用记录
                }

                results[method].append(standardized)

        return results

    @staticmethod
    def _extract_tokens(method_data: Dict) -> Dict:
        """提取token使用量"""
        full_output = method_data.get("full_output", {})
        usage = full_output.get("usage", {})

        return {
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
            "total": usage.get("total_tokens", 0)
        }


class BMAgentDataExtractor:
    """
    【占位符】从BM Agent执行日志和报告提取数据

    TODO: 实现完整的数据提取逻辑
    """

    @staticmethod
    def extract_from_execution_log(log_file: str) -> Dict:
        """
        从execution_log提取执行数据

        提取字段：
        - tool_calls: 工具调用列表
        - latency: 各步骤耗时（从duration_ms累加）
        - tokens: 从llm_response的usage提取
        - timestamp: 时间戳
        """
        tool_calls = []
        total_duration_ms = 0
        total_tokens = {"input": 0, "output": 0, "total": 0}
        reasoning_parts = []

        try:
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

                        elif entry_type == "agent_thinking":
                            # 收集推理过程
                            thinking = entry.get("content", "")
                            if thinking:
                                reasoning_parts.append(thinking)

                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading log {log_file}: {e}")

        return {
            "tool_calls": tool_calls,
            "num_tool_calls": len(tool_calls),
            "total_duration_ms": total_duration_ms,
            "tokens": total_tokens,
            "reasoning": "\n".join(reasoning_parts[:5])  # 前5个思考片段
        }

    @staticmethod
    def extract_from_report(report_file: str) -> Dict:
        """
        从MDT报告提取数据

        需要提取的字段：
        - report: 完整报告内容
        - citations: 引用列表
        """
        print(f"⚠️ [PLACEHOLDER] Extracting from {report_file}")

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()

            # 提取引用
            citations = {
                "pubmed": re.findall(r'\[PubMed:\s*PMID\s+(\d+)\]', report_content),
                "oncokb": re.findall(r'\[OncoKB:\s*([^\]]+)\]', report_content),
                "local": re.findall(r'\[Local:\s*([^\]]+)\]', report_content),
            }

            return {
                "report": report_content,
                "citations": citations,
                "citation_count": sum(len(v) for v in citations.values())
            }
        except Exception as e:
            print(f"Error reading report: {e}")
            return {"report": "", "citations": {}, "citation_count": 0}

    @staticmethod
    def extract_all_bm_agent_results(
        execution_logs_dir: str = "workspace/sandbox/execution_logs",
        reports_dir: str = "workspace/sandbox/patients"
    ) -> List[Dict]:
        """
        提取所有BM Agent结果

        【占位符】需要实现完整的匹配逻辑
        """
        print("⚠️ [PLACEHOLDER] BM Agent extraction not fully implemented")

        # TODO: 实现以下逻辑：
        # 1. 扫描execution_logs目录，获取所有session日志
        # 2. 扫描patients目录，获取所有报告
        # 3. 匹配patient_id（从日志中的user_input提取patient_id）
        # 4. 提取token使用量（需要修改BM Agent添加记录）
        # 5. 标准化数据结构

        # 返回空列表作为占位符
        return []


class DataAligner:
    """
    数据对齐器 - 确保4种方法的数据格式一致
    """

    REQUIRED_FIELDS = [
        "patient_id",
        "hospital_id",
        "method",
        "timestamp",
        "report",
        "reasoning",
        "latency_ms",
        "tokens",
        "sources",
        "tool_calls"
    ]

    @staticmethod
    def align_data(data: Dict) -> Dict:
        """
        对齐数据字段

        确保所有必需字段存在，缺失的填充默认值
        """
        aligned = {}

        for field in DataAligner.REQUIRED_FIELDS:
            if field in data:
                aligned[field] = data[field]
            else:
                # 填充默认值
                if field == "tokens":
                    aligned[field] = {"input": 0, "output": 0, "total": 0}
                elif field in ["latency_ms", "citation_count"]:
                    aligned[field] = 0
                elif field in ["sources", "tool_calls", "citations"]:
                    aligned[field] = []
                else:
                    aligned[field] = ""

        return aligned

    @staticmethod
    def validate_data(data: Dict) -> bool:
        """验证数据完整性"""
        for field in DataAligner.REQUIRED_FIELDS:
            if field not in data:
                print(f"  Missing field: {field}")
                return False
        return True


def main():
    """测试数据提取"""
    print("="*60)
    print("Data Extraction Test")
    print("="*60)

    # 1. 测试Baseline提取
    print("\n1. Testing Baseline extraction...")
    baseline_results = BaselineDataExtractor.extract_all_baseline_results()

    for method, patients in baseline_results.items():
        print(f"   {method}: {len(patients)} patients")
        if patients:
            print(f"     Sample patient_id: {patients[0]['patient_id']}")
            print(f"     Sample tokens: {patients[0]['tokens']}")

    # 2. 测试BM Agent提取（占位符）
    print("\n2. Testing BM Agent extraction (PLACEHOLDER)...")
    bm_agent_results = BMAgentDataExtractor.extract_all_bm_agent_results()
    print(f"   BM Agent: {len(bm_agent_results)} patients (PLACEHOLDER)")

    # 3. 测试数据对齐
    print("\n3. Testing data alignment...")
    if baseline_results["direct_llm"]:
        aligned = DataAligner.align_data(baseline_results["direct_llm"][0])
        print(f"   Aligned fields: {list(aligned.keys())}")
        is_valid = DataAligner.validate_data(aligned)
        print(f"   Validation: {'PASS' if is_valid else 'FAIL'}")

    print("\n" + "="*60)
    print("Data extraction test complete!")
    print("="*60)


if __name__ == "__main__":
    main()
