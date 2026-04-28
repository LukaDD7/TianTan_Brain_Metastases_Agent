"""
evaluation/llm_as_judge.py
v7.0 — LLM-as-Judge 评估管线 (WS-3)

评估维度 (8维度，总分40分):
  D1: Guideline Adherence        (0-5)  — 治疗方案是否符合当前版本指南
  D2: Evidence Completeness      (0-5)  — 引用数量与覆盖面是否充分
  D3: Clinical Safety            (0-5)  — 安全注意事项是否到位
  D4: Conflict Handling          (0-5)  — 冲突裁决是否合理
  D5: Uncertainty Disclosure     (0-5)  — 不确定性是否被明确披露
  D6: Personalization            (0-5)  — 方案是否个体化（非模板化）
  D7: Actionability              (0-5)  — 建议是否有操作性（具体药物/剂量/时间）
  D8: Coherence                  (0-5)  — 各模块内容是否前后一致

Judge 模型策略:
  Primary: qwen3.6-plus (与 Orchestrator 同款，测试自我评估偏差)
  Secondary(可选): 不同 provider 的模型（需配置 JUDGE_API_KEY + JUDGE_BASE_URL）
  聚合策略: 多模型取均值，标准差 > 1.5 时标记为 "high_disagreement"
"""

import json
import os
import sys
import time
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

RESULTS_DIR = os.path.join(PROJECT_ROOT, "evaluation", "results")


# ===========================================================
# 评分 Rubric 提示词
# ===========================================================

JUDGE_SYSTEM_PROMPT = """你是一名顶级临床肿瘤学专家，专门评估 MDT (多学科诊疗) 报告的质量。

你将对一份脑转移MDT报告进行**严格、客观**的评估，按照8个维度打分（每项0-5分，总分40分）。

## 评分规则（严格执行）

### D1: 指南遵循性 (Guideline Adherence) [0-5]
- 5: 治疗方案完全符合 NCCN CNS 2026 v2 或 EANO-ESMO 2024 最新版本
- 4: 主要建议符合指南，有1处轻微偏差
- 3: 大体符合，但有1处明显指南未提及的方案
- 2: 2处以上偏差，或使用了过时版本指南
- 1: 多处与指南显著不符
- 0: 严重违背指南，可能危害患者

### D2: 证据完整性 (Evidence Completeness) [0-5]
- 5: 每条建议均有具体引用（OncoKB Level / PubMed PMID / 指南章节），EGR≥0.90
- 4: 绝大多数建议有引用，EGR≥0.80
- 3: 约一半建议有引用，EGR≥0.70
- 2: 少数引用，EGR<0.70
- 1: 基本无引用
- 0: 完全无引用，纯主观陈述

### D3: 临床安全性 (Clinical Safety) [0-5]
- 5: 明确记录了所有关键安全注意事项（围手术期停药/剂量上限/药物相互作用/紧急情况处理）
- 4: 覆盖了大部分安全注意事项
- 3: 覆盖了主要安全注意事项，有小遗漏
- 2: 只覆盖了部分安全事项，有重要遗漏
- 1: 安全注意事项极少
- 0: 存在明显安全隐患未被指出（如 KRAS+cetuximab）

### D4: 冲突处理 (Conflict Handling) [0-5]
- 5: 所有专科意见分歧均被记录，裁决逻辑清晰且基于证据等级
- 4: 记录了主要冲突，裁决基本合理
- 3: 部分冲突被记录，裁决理由不完整
- 2: 冲突存在但被忽略，或裁决无依据
- 1: 冲突完全未被识别
- 0: 将有争议的点当作无争议结论呈现

### D5: 不确定性披露 (Uncertainty Disclosure) [0-5]
- 5: 明确指出了证据不足或存在争议的决策点，提供了置信度估计
- 4: 指出了主要不确定性
- 3: 部分不确定性被提及
- 2: 仅有模糊表述（如"可以考虑..."但无原因说明）
- 1: 基本无不确定性披露
- 0: 对高度不确定的决定以确定性语气呈现

### D6: 个体化程度 (Personalization) [0-5]
- 5: 方案完全基于该患者的具体情况（KPS/突变/原发灶/治疗线/合并症）
- 4: 有较好个体化，但有1-2处通用模板语言
- 3: 基本个体化，但有明显的通用模板段落
- 2: 较多模板语言，个体化不足
- 1: 主要是通用模板
- 0: 与患者信息严重脱节

### D7: 可操作性 (Actionability) [0-5]
- 5: 所有建议有明确的药物名（通用名+商品名）、剂量、时间表、下一步行动
- 4: 大部分建议可直接执行
- 3: 部分建议需要进一步查询才能执行
- 2: 建议较模糊，需要大量额外信息
- 1: 建议空洞，无法指导实际操作
- 0: 无实质性建议

### D8: 内部一致性 (Internal Coherence) [0-5]
- 5: 各模块完全一致（Module 2 的药物与 Module 3 的剂量匹配，Module 5 记录了所有出现的冲突）
- 4: 基本一致，有1处小矛盾
- 3: 有1-2处可注意到的矛盾
- 2: 多处矛盾，但核心建议一致
- 1: 严重矛盾，难以判断最终建议
- 0: 前后完全矛盾，无法理解

## 输出格式 (严格遵守)

输出一个 JSON 对象，格式如下:
```json
{
  "scores": {
    "D1_guideline_adherence": 4,
    "D2_evidence_completeness": 5,
    "D3_clinical_safety": 4,
    "D4_conflict_handling": 3,
    "D5_uncertainty_disclosure": 3,
    "D6_personalization": 4,
    "D7_actionability": 4,
    "D8_coherence": 5
  },
  "esr_total": 32,
  "critical_issues": ["D4: 神外与放疗在局部治疗方式上有分歧但未被裁决"],
  "strengths": ["D2: 引用充分，OncoKB Level证据使用规范", "D8: 各模块高度一致"],
  "improvement_suggestions": ["在Module 5中明确记录各KDP的Kendall W值", "D5: 对L858R存在EGFR耐药可能性时应披露不确定性"],
  "overall_comment": "报告整体质量较高，主要弱点在于未处理的神外-放疗分歧。建议在Phase 1.6中激活辩论。",
  "judge_model": "qwen3.6-plus",
  "timestamp": "2026-04-26T12:00:00"
}
```

**严禁**: 打分不加说明、给满分不解释理由、回避负面反馈。
"""

JUDGE_USER_TEMPLATE = """请对以下脑转移MDT报告进行评估:

---患者基本信息---
{patient_info}

---MDT报告全文---
{report_content}

---额外上下文（冲突量化统计）---
{conflict_stats}

请按照系统提示中的8维度评分标准，输出评估JSON。"""


# ===========================================================
# Judge 客户端
# ===========================================================

def get_judge_client(model_key: str = "primary"):
    """获取 Judge LLM 客户端"""
    from openai import OpenAI

    if model_key == "primary":
        # 使用与 Orchestrator 相同的 Qwen（检测自我评估偏差）
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        model = "qwen3.6-plus"
    elif model_key == "secondary":
        # 可选：使用不同 provider（如 GPT / Claude）作为独立评估
        api_key = os.getenv("JUDGE_API_KEY", "")
        base_url = os.getenv("JUDGE_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("JUDGE_MODEL", "gpt-4o")
    else:
        raise ValueError(f"Unknown model_key: {model_key}")

    if not api_key:
        raise ValueError(f"API key not set for judge model: {model_key}")

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model


def parse_judge_response(response_text: str) -> Optional[Dict[str, Any]]:
    """从 LLM 响应中提取 JSON"""
    # 尝试直接解析
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # 尝试从 code block 中提取
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试提取 {...} 块
    match = re.search(r"\{[\s\S]*\}", response_text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def run_single_judge(
    report_content: str,
    patient_info: str = "",
    conflict_stats: str = "",
    model_key: str = "primary",
    max_retries: int = 2,
) -> Optional[Dict[str, Any]]:
    """运行单个 Judge 模型评估"""
    try:
        client, model = get_judge_client(model_key)
    except ValueError as e:
        print(f"  ⚠️  Judge [{model_key}] skipped: {e}")
        return None

    user_msg = JUDGE_USER_TEMPLATE.format(
        patient_info=patient_info or "(无额外患者信息)",
        report_content=report_content[:8000],  # 限制长度防止超出 context
        conflict_stats=conflict_stats or "(未提供冲突统计)",
    )

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content
            parsed = parse_judge_response(raw)

            if parsed is None:
                print(f"  ⚠️  Judge [{model_key}] attempt {attempt+1}: Failed to parse JSON")
                if attempt == max_retries:
                    return None
                continue

            # 计算总分
            scores = parsed.get("scores", {})
            computed_total = sum(scores.values())
            parsed["esr_total"] = computed_total
            parsed["judge_model"] = model
            parsed["timestamp"] = datetime.now().isoformat()
            parsed["model_key"] = model_key
            return parsed

        except Exception as e:
            print(f"  ⚠️  Judge [{model_key}] attempt {attempt+1} error: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                return None

    return None


# ===========================================================
# 多模型聚合评估
# ===========================================================

def run_multi_judge_evaluation(
    case_id: str,
    report_content: str,
    patient_info: str = "",
    conflict_stats: str = "",
    use_secondary: bool = False,
) -> Dict[str, Any]:
    """
    运行多模型 Judge 评估并聚合结果。

    Args:
        case_id: 病例 ID
        report_content: 完整报告文本
        patient_info: 患者基本信息（来自病历）
        conflict_stats: 冲突量化统计（来自 Conflict Calculator 输出）
        use_secondary: 是否启用 Secondary Judge（需要配置 JUDGE_API_KEY）

    Returns:
        聚合评估结果字典
    """
    print(f"\n[Judge] Evaluating case: {case_id}")

    # Primary judge
    print(f"  Running primary judge (qwen3.6-plus)...")
    primary_result = run_single_judge(
        report_content, patient_info, conflict_stats, "primary"
    )

    # Secondary judge (可选)
    secondary_result = None
    if use_secondary:
        print(f"  Running secondary judge ({os.getenv('JUDGE_MODEL', 'gpt-4o')})...")
        secondary_result = run_single_judge(
            report_content, patient_info, conflict_stats, "secondary"
        )

    # 聚合
    aggregated = aggregate_judge_scores(
        case_id, primary_result, secondary_result
    )

    # 保存结果
    save_judge_result(case_id, aggregated)

    return aggregated


def aggregate_judge_scores(
    case_id: str,
    primary: Optional[Dict],
    secondary: Optional[Dict],
) -> Dict[str, Any]:
    """聚合多个 Judge 的评分"""
    results = [r for r in [primary, secondary] if r is not None]

    if not results:
        return {
            "case_id": case_id,
            "status": "judge_failed",
            "esr_total": None,
            "judges": [],
            "timestamp": datetime.now().isoformat(),
        }

    all_dimensions = [
        "D1_guideline_adherence", "D2_evidence_completeness",
        "D3_clinical_safety", "D4_conflict_handling",
        "D5_uncertainty_disclosure", "D6_personalization",
        "D7_actionability", "D8_coherence"
    ]

    # 计算各维度均值和标准差
    avg_scores = {}
    high_disagreement_dims = []

    import statistics
    for dim in all_dimensions:
        vals = [r.get("scores", {}).get(dim, 0) for r in results]
        avg_scores[dim] = round(statistics.mean(vals), 2)
        if len(vals) > 1:
            std = statistics.stdev(vals)
            if std > 1.5:
                high_disagreement_dims.append(f"{dim} (std={std:.1f})")

    avg_total = sum(avg_scores.values())

    # 合并定性反馈
    all_critical = []
    all_strengths = []
    all_suggestions = []
    for r in results:
        all_critical.extend(r.get("critical_issues", []))
        all_strengths.extend(r.get("strengths", []))
        all_suggestions.extend(r.get("improvement_suggestions", []))

    return {
        "case_id": case_id,
        "status": "completed",
        "esr_total": round(avg_total, 1),
        "esr_max": 40,
        "esr_percentage": round(avg_total / 40 * 100, 1),
        "avg_scores": avg_scores,
        "high_disagreement_dimensions": high_disagreement_dims,
        "judge_count": len(results),
        "judges": [r.get("judge_model", "?") for r in results],
        "critical_issues": list(set(all_critical))[:5],
        "strengths": list(set(all_strengths))[:5],
        "improvement_suggestions": list(set(all_suggestions))[:5],
        "overall_comment": primary.get("overall_comment", "") if primary else "",
        "timestamp": datetime.now().isoformat(),
        # 用于进化信号
        "quality_tier": (
            "excellent" if avg_total >= 35 else
            "good" if avg_total >= 28 else
            "acceptable" if avg_total >= 20 else
            "poor"
        ),
        "needs_prompt_refinement": avg_total < 28,  # 低于 28 触发 R1 Prompt Refinement
        "raw_judge_outputs": results,
    }


def save_judge_result(case_id: str, result: Dict[str, Any], round_name: str = "R0"):
    """保存评估结果到文件"""
    round_dir = os.path.join(RESULTS_DIR, round_name)
    os.makedirs(round_dir, exist_ok=True)

    file_path = os.path.join(round_dir, f"{case_id}_judge.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  ✅ Judge result saved: {file_path}")
    print(f"  ESR: {result.get('esr_total', '?')}/40 ({result.get('quality_tier', '?')})")


# ===========================================================
# 批量评估 + 进化信号提取
# ===========================================================

def load_round_results(round_name: str = "R0") -> List[Dict]:
    """加载某轮次的所有 Judge 结果"""
    round_dir = os.path.join(RESULTS_DIR, round_name)
    results = []
    for f in os.listdir(round_dir) if os.path.isdir(round_dir) else []:
        if f.endswith("_judge.json"):
            with open(os.path.join(round_dir, f)) as fh:
                results.append(json.load(fh))
    return results


def generate_evolution_signals(round_name: str = "R0") -> Dict[str, Any]:
    """
    从 Judge 结果提取进化信号，用于驱动 R1 的 Prompt Refinement。

    Returns:
        {
          "low_quality_cases": [...],
          "top_error_dimensions": [...],
          "prompt_refinement_targets": {
              "neurosurgery-specialist": ["D4: 冲突处理不足"],
              "primary-oncology-specialist": ["D2: OncoKB 引用缺失"],
          },
          "weight_tuning_signals": [...],
        }
    """
    results = load_round_results(round_name)

    if not results:
        return {"error": f"No results found for round {round_name}"}

    import statistics

    # 低质量 Case
    low_quality = [r for r in results if r.get("esr_total", 40) < 28]

    # 各维度平均分
    dims = [
        "D1_guideline_adherence", "D2_evidence_completeness",
        "D3_clinical_safety", "D4_conflict_handling",
        "D5_uncertainty_disclosure", "D6_personalization",
        "D7_actionability", "D8_coherence"
    ]
    dim_avgs = {}
    for dim in dims:
        vals = [r.get("avg_scores", {}).get(dim, 0) for r in results if "avg_scores" in r]
        dim_avgs[dim] = round(statistics.mean(vals), 2) if vals else 0

    # 最弱维度（分数最低的前3）
    sorted_dims = sorted(dim_avgs.items(), key=lambda x: x[1])
    weakest_dims = sorted_dims[:3]

    # 维度到 SA 的映射（D 维度主要由哪个 SA 产生）
    dim_to_sa_map = {
        "D1_guideline_adherence": ["primary-oncology-specialist", "radiation-oncology-specialist"],
        "D2_evidence_completeness": ["evidence-auditor", "molecular-pathology-specialist"],
        "D3_clinical_safety": ["neurosurgery-specialist", "primary-oncology-specialist"],
        "D4_conflict_handling": ["orchestrator (prompt)"],
        "D5_uncertainty_disclosure": ["all specialists"],
        "D6_personalization": ["orchestrator (prompt)"],
        "D7_actionability": ["primary-oncology-specialist", "radiation-oncology-specialist"],
        "D8_coherence": ["evidence-auditor", "orchestrator (prompt)"],
    }

    prompt_targets = {}
    for dim, score in weakest_dims:
        sas = dim_to_sa_map.get(dim, [])
        for sa in sas:
            if sa not in prompt_targets:
                prompt_targets[sa] = []
            prompt_targets[sa].append(f"{dim} (avg={score})")

    return {
        "round": round_name,
        "total_cases": len(results),
        "avg_esr_total": round(statistics.mean(r.get("esr_total", 0) for r in results), 1),
        "low_quality_cases": [r["case_id"] for r in low_quality],
        "low_quality_count": len(low_quality),
        "dim_averages": dim_avgs,
        "weakest_dimensions": weakest_dims,
        "prompt_refinement_targets": prompt_targets,
        "recommended_actions": [
            f"Refine prompt for: {list(prompt_targets.keys())}",
            f"Focus on dimensions: {[d for d, _ in weakest_dims]}",
        ],
    }


# ===========================================================
# CLI 接口
# ===========================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TiantanBM v7.0 LLM-as-Judge Evaluation"
    )
    parser.add_argument("--report", required=False, help="Path to MDT report .md file")
    parser.add_argument("--case-id", required=False, help="Case ID")
    parser.add_argument("--round", default="R0", help="Evolution round (R0/R1/R2/R3)")
    parser.add_argument("--signals", action="store_true",
                        help="Generate evolution signals from existing results")
    parser.add_argument("--secondary", action="store_true",
                        help="Enable secondary judge (requires JUDGE_API_KEY)")
    args = parser.parse_args()

    if args.signals:
        signals = generate_evolution_signals(args.round)
        print(json.dumps(signals, indent=2, ensure_ascii=False))
    elif args.report and args.case_id:
        with open(args.report, "r", encoding="utf-8") as f:
            report = f.read()
        result = run_multi_judge_evaluation(
            args.case_id, report,
            use_secondary=args.secondary
        )
        save_judge_result(args.case_id, result, args.round)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
