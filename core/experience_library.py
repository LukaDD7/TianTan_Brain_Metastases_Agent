"""
core/experience_library.py
v7.0 — 经验库 (Experience Library)

WS-7: Self-Evolution Engine — Experience-Based Learning

存储格式: JSON Lines (JSONL)，每行一条 Case 经验记录
索引策略: 基于癌种 × 突变类型 × 治疗线 × 复杂度的多维匹配
检索时机: Case 开始时由 Orchestrator 通过 read_file 注入相似经验
更新时机: Case 完成 + LLM-as-Judge 评分后追加
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

EXPERIENCE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workspace", "evolution", "experience_library.jsonl"
)

INSIGHTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workspace", "evolution", "distilled_insights.json"
)


# ===========================================================
# 经验记录结构
# ===========================================================

def make_experience_record(
    case_id: str,
    cancer_type: str,
    mutation: str,
    treatment_line: int,
    complexity: str,  # "simple" | "moderate" | "complex"
    evolution_round: str,  # "R0" | "R1" | "R2" | "R3"
    # 关键决策摘要
    final_local_therapy: str,  # e.g. "SRS 18Gy/1f"
    final_systemic_therapy: str,  # e.g. "Osimertinib 80mg QD"
    triage_subagents_used: List[str],
    # 评估结果
    judge_scores: Optional[Dict[str, Any]] = None,  # LLM-as-Judge 评分
    auto_metrics: Optional[Dict[str, float]] = None,  # EGR, SCR, PTR 等
    # 错误与洞察
    errors_detected: Optional[List[str]] = None,
    expert_corrections: Optional[List[str]] = None,
    key_insights: Optional[List[str]] = None,
    # 冲突信息
    total_conflicts: int = 0,
    kendall_w: float = 1.0,
) -> Dict[str, Any]:
    """创建一条标准化的经验记录"""
    return {
        "case_id": case_id,
        "cancer_type": cancer_type,
        "mutation": mutation,
        "treatment_line": treatment_line,
        "complexity": complexity,
        "evolution_round": evolution_round,
        "timestamp": datetime.now().isoformat(),

        # 决策摘要
        "final_local_therapy": final_local_therapy,
        "final_systemic_therapy": final_systemic_therapy,
        "triage_subagents_used": triage_subagents_used,
        "subagent_count": len(triage_subagents_used),

        # 评估分数
        "judge_scores": judge_scores or {},
        "auto_metrics": auto_metrics or {},

        # 错误与洞察（用于 Prompt Refinement）
        "errors_detected": errors_detected or [],
        "expert_corrections": expert_corrections or [],
        "key_insights": key_insights or [],

        # 冲突统计
        "total_conflicts": total_conflicts,
        "kendall_w": kendall_w,

        # 快速质量标签（用于过滤检索）
        "is_high_quality": (
            judge_scores is not None and
            judge_scores.get("esr_total", 0) >= 30  # ≥30/40 视为高质量
        ),
        "has_critical_error": bool(errors_detected),
    }


# ===========================================================
# 写入操作
# ===========================================================

def append_experience(record: Dict[str, Any]):
    """追加一条经验记录到 JSONL 文件"""
    os.makedirs(os.path.dirname(EXPERIENCE_FILE), exist_ok=True)
    with open(EXPERIENCE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_all_experiences() -> List[Dict[str, Any]]:
    """加载全部经验记录（返回列表，按时间正序）"""
    if not os.path.exists(EXPERIENCE_FILE):
        return []
    records = []
    with open(EXPERIENCE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


# ===========================================================
# 检索操作
# ===========================================================

def search_similar_cases(
    cancer_type: str,
    mutation: str = "",
    treatment_line: int = -1,
    complexity: str = "",
    top_k: int = 3,
    high_quality_only: bool = True,
) -> List[Dict[str, Any]]:
    """
    基于多维相似度检索历史经验。

    相似度评分（总分 10）:
      - 癌种完全匹配: +4
      - 突变完全匹配: +3
      - 治疗线完全匹配: +2
      - 复杂度完全匹配: +1
    """
    all_records = load_all_experiences()
    if not all_records:
        return []

    scored: List[tuple] = []
    for record in all_records:
        # 可选：只返回高质量 Case
        if high_quality_only and not record.get("is_high_quality", False):
            continue

        score = 0
        if record.get("cancer_type", "").lower() == cancer_type.lower():
            score += 4
        if mutation and record.get("mutation", "").lower() == mutation.lower():
            score += 3
        if treatment_line >= 0 and record.get("treatment_line") == treatment_line:
            score += 2
        if complexity and record.get("complexity", "").lower() == complexity.lower():
            score += 1

        if score > 0:
            scored.append((record, score))

    scored.sort(key=lambda x: (-x[1], x[0].get("timestamp", "")))
    return [r for r, _ in scored[:top_k]]


# ===========================================================
# Context 注入格式化
# ===========================================================

def format_for_context_injection(similar_cases: List[Dict[str, Any]]) -> str:
    """
    将检索到的相似案例格式化为 Orchestrator context 注入文本。
    保持简洁，避免 context 噪声。
    """
    if not similar_cases:
        return ""

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "■ Experience Library: 相似历史案例参考 (仅供参考，不替代当前证据检索)",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    for i, case in enumerate(similar_cases, 1):
        lines.append(f"\n【案例 {i}】{case.get('case_id', 'N/A')}")
        lines.append(f"  诊断: {case.get('cancer_type', '?')} | 突变: {case.get('mutation', '?')} | 治疗线: {case.get('treatment_line', '?')}")
        lines.append(f"  局部治疗: {case.get('final_local_therapy', '?')}")
        lines.append(f"  系统治疗: {case.get('final_systemic_therapy', '?')}")
        lines.append(f"  质量评分: ESR={case.get('judge_scores', {}).get('esr_total', 'N/A')}/40")

        errors = case.get("errors_detected", [])
        if errors:
            lines.append(f"  ⚠️ 历史错误: {'; '.join(errors[:2])}")

        insights = case.get("key_insights", [])
        if insights:
            lines.append(f"  💡 关键洞察: {'; '.join(insights[:2])}")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


# ===========================================================
# 提炼洞察 (Distilled Insights)
# ===========================================================

def load_distilled_insights() -> Dict[str, List[str]]:
    """加载从经验中提炼的持久化洞察（按癌种分类）"""
    if not os.path.exists(INSIGHTS_FILE):
        return {}
    with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def add_distilled_insight(cancer_type: str, insight: str):
    """添加一条提炼洞察（去重）"""
    insights = load_distilled_insights()
    if cancer_type not in insights:
        insights[cancer_type] = []
    if insight not in insights[cancer_type]:
        insights[cancer_type].append(insight)
        os.makedirs(os.path.dirname(INSIGHTS_FILE), exist_ok=True)
        with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2, ensure_ascii=False)


def get_insights_for_context(cancer_type: str, max_insights: int = 3) -> str:
    """获取特定癌种的提炼洞察，格式化为 context 注入文本"""
    all_insights = load_distilled_insights()
    insights = all_insights.get(cancer_type, [])
    if not insights:
        return ""

    lines = [f"■ Distilled Insights ({cancer_type}):"]
    for insight in insights[:max_insights]:
        lines.append(f"  • {insight}")
    return "\n".join(lines)


# ===========================================================
# 统计信息
# ===========================================================

def get_library_stats() -> Dict[str, Any]:
    """获取经验库统计信息"""
    all_records = load_all_experiences()
    if not all_records:
        return {
            "total_cases": 0,
            "by_cancer_type": {},
            "by_round": {},
            "high_quality_cases": 0,
            "error_cases": 0,
        }

    from collections import Counter
    cancer_counter = Counter(r.get("cancer_type", "Unknown") for r in all_records)
    round_counter = Counter(r.get("evolution_round", "R0") for r in all_records)

    return {
        "total_cases": len(all_records),
        "by_cancer_type": dict(cancer_counter),
        "by_round": dict(round_counter),
        "high_quality_cases": sum(1 for r in all_records if r.get("is_high_quality")),
        "error_cases": sum(1 for r in all_records if r.get("has_critical_error")),
    }
