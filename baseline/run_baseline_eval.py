#!/usr/bin/env python3
"""
Baseline Evaluation Runner for Brain Metastases MDT Report Generation
Compares RAG vs Direct LLM approaches with 8-module aligned system prompt
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_guideline.rag_baseline import SimpleRAGBaseline
from direct_llm.direct_llm_baseline import DirectLLMBaseline


# 8-Module aligned system prompt (apple-to-apple comparison with MDT skill)
BASELINE_SYSTEM_PROMPT = """你是一位资深的脑转移瘤多学科诊疗（MDT）专家。请基于提供的患者信息，生成一份结构化的MDT诊疗报告。

报告必须包含以下8个核心模块：

## 1. 入院评估 (Admission Evaluation)
- 患者基本信息与入院情况
- 临床症状评估（主诉、现病史）
- 既往病史与合并症分析
- 影像学初步印象

## 2. 原发灶处理方案 (Primary Tumor Management Plan)
- 基于病理诊断的原发肿瘤特征
- 分子分型与靶向治疗敏感性评估
- 原发灶治疗策略建议

## 3. 系统性管理 (Systemic Management)
- 全身治疗方案
- 药物选择与剂量考量
- 围手术期用药参数（如适用）

## 4. 随访方案 (Follow-up Strategy)
- 影像学复查时间窗
- 肿瘤标志物监测
- 神经系统功能评估

## 5. 被拒绝的替代方案及排他性论证 (Rejected Alternatives)
- 其他可行但未被选择的方案
- 选择当前方案而非替代方案的循证依据

## 6. 围手术期管理 (Peri-procedural Management)
- 术前准备要点
- 术后护理注意事项
- 并发症预防策略

## 7. 分子病理与基因检测 (Molecular Pathology)
- 关键基因突变分析
- 靶向治疗指导意义
- 预后分子标志物

## 8. 执行路径与决策轨迹 (Execution Trajectory)
- 推荐的治疗时间线
- 关键决策节点
- 多学科协作流程

【患者信息】
{patient_info}

【参考指南内容】
{context}

请生成一份专业、结构化的MDT诊疗报告，确保涵盖所有8个模块。"""


class BaselineEvaluator:
    """Evaluator for comparing RAG vs Direct LLM baselines"""

    def __init__(self):
        self.rag_baseline = SimpleRAGBaseline()
        self.direct_llm = DirectLLMBaseline()

    def initialize(self):
        """Initialize RAG vector store"""
        print("Initializing RAG baseline...")
        self.rag_baseline.initialize()
        print("✅ Baseline systems initialized\n")

    def format_patient_info(self, row: pd.Series) -> str:
        """Format patient data into structured text (INPUT FEATURES ONLY)"""
        info_lines = []

        # Basic info (input features only - no diagnoses/labels)
        info_lines.append(f"住院号: {row.get('住院号', 'N/A')}")
        info_lines.append(f"年龄: {row.get('年龄', 'N/A')}岁")
        info_lines.append(f"性别: {row.get('性别', 'N/A')}")

        # Chief complaint and history
        if pd.notna(row.get('主诉')):
            info_lines.append(f"\n主诉: {row['主诉']}")
        if pd.notna(row.get('现病史')):
            info_lines.append(f"现病史: {row['现病史']}")
        if pd.notna(row.get('既往史')):
            info_lines.append(f"既往史: {row['既往史']}")

        # Imaging (all input features)
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

        # Note: 入院诊断, 出院诊断, 病理诊断 are REMOVED (labels should not be exposed)
        # Note: 入院时间, 出院时间, 诊疗经过 are REMOVED (process info)

        return "\n".join(info_lines)

    def run_rag_baseline(self, patient_info: str) -> Dict:
        """Run RAG baseline for a patient"""
        print("  Running RAG baseline...")
        result = self.rag_baseline.query(
            question=patient_info,
            system_prompt=BASELINE_SYSTEM_PROMPT
        )
        return {
            "method": "RAG",
            "report": result.get("response", ""),
            "retrieved_docs": result.get("retrieved_docs", []),
            "timestamp": datetime.now().isoformat()
        }

    def run_direct_llm(self, patient_info: str) -> Dict:
        """Run Direct LLM baseline for a patient"""
        print("  Running Direct LLM baseline...")
        # For direct LLM, replace {context} with empty string (no retrieval)
        direct_prompt = BASELINE_SYSTEM_PROMPT.replace(
            "【参考指南内容】\n{context}\n\n", ""
        )
        result = self.direct_llm.query(
            question=patient_info,
            system_prompt=direct_prompt
        )
        return {
            "method": "Direct_LLM",
            "report": result.get("response", ""),
            "timestamp": datetime.now().isoformat()
        }

    def _construct_query(self, patient_info: str) -> str:
        """Construct a query from patient information"""
        # Extract key clinical questions
        lines = patient_info.split('\n')

        # Build a focused query
        query_parts = ["请为以下脑转移瘤患者生成MDT诊疗报告:"]
        query_parts.append(patient_info)
        query_parts.append("\n请基于临床指南和循证医学证据，提供完整的8模块MDT报告。")

        return "\n".join(query_parts)

    def evaluate_patient(self, row: pd.Series, output_dir: str):
        """Evaluate a single patient with both methods"""
        patient_id = row.get('patient_id', 'unknown')
        hospital_id = row.get('住院号', 'unknown')

        print(f"\n{'='*60}")
        print(f"Evaluating Patient: {patient_id} (住院号: {hospital_id})")
        print(f"{'='*60}")

        # Format patient info
        patient_info = self.format_patient_info(row)

        # Run both baselines
        rag_result = self.run_rag_baseline(patient_info)
        direct_result = self.run_direct_llm(patient_info)

        # Prepare output
        result = {
            "patient_id": patient_id,
            "hospital_id": str(hospital_id),
            "patient_info": patient_info,
            "rag_result": rag_result,
            "direct_result": direct_result,
            "evaluation_timestamp": datetime.now().isoformat()
        }

        # Save individual result
        output_file = os.path.join(output_dir, f"{patient_id}_result.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  Results saved to: {output_file}")

        return result

    def run_evaluation(self, csv_path: str, output_dir: str = "baseline/results"):
        """Run full evaluation on all patients"""
        # Initialize baselines
        self.initialize()

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Load patients
        print(f"Loading patients from: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"Loaded {len(df)} patients")

        # Evaluate each patient
        all_results = []
        for idx, row in df.iterrows():
            result = self.evaluate_patient(row, output_dir)
            all_results.append(result)

        # Save summary
        summary_file = os.path.join(output_dir, "evaluation_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_patients": len(all_results),
                "evaluation_date": datetime.now().isoformat(),
                "patients": [r["patient_id"] for r in all_results]
            }, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"Evaluation Complete!")
        print(f"Total patients evaluated: {len(all_results)}")
        print(f"Results saved to: {output_dir}")
        print(f"{'='*60}")

        return all_results


def main():
    """Main entry point"""
    evaluator = BaselineEvaluator()

    # Run evaluation
    csv_path = "baseline/test_patients.csv"
    results = evaluator.run_evaluation(csv_path)

    print("\nBaseline evaluation completed successfully!")


if __name__ == "__main__":
    main()
