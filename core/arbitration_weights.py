"""
core/arbitration_weights.py
v7.0 — 可进化的仲裁权重配置 (Evolvable Arbitration Weights)

WS-7: Self-Evolution Engine — Weight Tuning

将 Orchestrator Prompt 中硬编码的仲裁权重迁移到可配置文件，
支持基于 LLM-as-Judge 反馈的自适应微调。
每次 tune 产生一条 evolution_log 记录，追踪进化轨迹。
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from copy import deepcopy

# 权重文件路径
WEIGHTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workspace", "evolution", "arbitration_weights.json"
)


# ===========================================================
# 默认权重 (与 v6.0 Orchestrator prompt 中的值保持一致)
# ===========================================================

DEFAULT_WEIGHTS: Dict[str, Any] = {
    "version": "v7.0_R0",
    "created_at": "",  # 初始化时填入
    "last_updated": "",

    # EBM 证据等级评分
    "ebm_level_scores": {
        "Level 1": 100,   # RCT / Meta-analysis
        "Level 2": 70,    # Cohort study
        "Level 3": 40,    # Case-control / Case series
        "Level 4": 20,    # Expert consensus / Guideline
    },

    # 临床优先级权重
    "clinical_priority_weights": {
        "Life-saving": 5.0,           # 生命急救（中线移位/脑疝）
        "Diagnostic_Necessity": 3.0,  # 诊断黑洞（原发不明）
        "Functional_Survival": 2.0,   # 功能与高效靶向
        "Local_Control": 1.0,         # 常规局部控制
    },

    # 置信度调整系数（用于 WS-4 不确定性聚合）
    "confidence_adjustments": {
        "multi_source_bonus_per_source": 0.05,  # 每增加一个佐证来源 +5%
        "dual_track_verified_bonus": 0.05,      # 双轨验证通过 +5%
        "max_confidence": 1.0,
    },

    # Debate 结果权重（用于 WS-6 辩论裁决）
    "debate_verdict_weights": {
        "evidence_level_weight": 0.60,  # 证据等级对裁决的影响权重
        "confidence_weight": 0.25,       # Agent 置信度对裁决的影响权重
        "concession_bonus": 0.15,        # 一方承认对方部分有理时给对方额外权重
    },

    # 进化日志
    "evolution_log": [],
}


# ===========================================================
# 工具函数
# ===========================================================

def load_weights() -> Dict[str, Any]:
    """加载当前权重配置，若文件不存在则返回并持久化默认值"""
    if os.path.exists(WEIGHTS_FILE):
        with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # 首次初始化
    weights = deepcopy(DEFAULT_WEIGHTS)
    weights["created_at"] = datetime.now().isoformat()
    weights["last_updated"] = weights["created_at"]
    save_weights(weights)
    return weights


def save_weights(weights: Dict[str, Any]):
    """持久化权重到文件"""
    os.makedirs(os.path.dirname(WEIGHTS_FILE), exist_ok=True)
    weights["last_updated"] = datetime.now().isoformat()
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, ensure_ascii=False)


def get_ebm_score(level: str, weights: Optional[Dict] = None) -> float:
    """获取指定 EBM Level 的评分"""
    if weights is None:
        weights = load_weights()
    return weights["ebm_level_scores"].get(level, 20)  # 默认 Level 4 分数


def get_priority_weight(priority: str, weights: Optional[Dict] = None) -> float:
    """获取临床优先级权重"""
    if weights is None:
        weights = load_weights()
    return weights["clinical_priority_weights"].get(priority, 1.0)


def compute_selection_priority(
    ebm_level: str,
    clinical_priority: str,
    weights: Optional[Dict] = None
) -> float:
    """
    Selection_Priority = EBM_Level_Score × Clinical_Priority_Weight
    复现 Orchestrator prompt 中的仲裁公式，但使用可进化的权重值。
    """
    if weights is None:
        weights = load_weights()
    ebm_score = get_ebm_score(ebm_level, weights)
    priority_weight = get_priority_weight(clinical_priority, weights)
    return ebm_score * priority_weight


def adjust_weight(
    factor_path: str,
    direction: str,
    case_id: str,
    reason: str,
    damping: float = 0.05,
    weights: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    微调某个权重因子。

    Args:
        factor_path: 点分隔的路径，如 "ebm_level_scores.Level 2" 或
                     "clinical_priority_weights.Functional_Survival"
        direction: "increase" 或 "decrease"
        case_id: 触发本次调整的病例 ID
        reason: 调整原因（来自 LLM-as-Judge 反馈摘要）
        damping: 每次调整幅度（默认 5%，防止过拟合单个 case）
        weights: 当前权重字典（None 时自动从文件加载）

    Returns:
        更新后的权重字典
    """
    if weights is None:
        weights = load_weights()

    # 导航到目标字段
    keys = factor_path.split(".")
    current_dict = weights
    for k in keys[:-1]:
        if k not in current_dict:
            raise KeyError(f"Weight path '{factor_path}' not found at key '{k}'")
        current_dict = current_dict[k]

    leaf_key = keys[-1]
    if leaf_key not in current_dict:
        raise KeyError(f"Weight key '{leaf_key}' not found in '{'.'.join(keys[:-1])}'")

    old_val = current_dict[leaf_key]
    if direction == "increase":
        new_val = old_val * (1 + damping)
    elif direction == "decrease":
        new_val = old_val * (1 - damping)
    else:
        raise ValueError(f"direction must be 'increase' or 'decrease', got '{direction}'")

    new_val = round(new_val, 4)
    current_dict[leaf_key] = new_val

    # 记录进化日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "case_id": case_id,
        "factor_path": factor_path,
        "direction": direction,
        "old_value": old_val,
        "new_value": new_val,
        "damping": damping,
        "reason": reason,
    }
    weights["evolution_log"].append(log_entry)

    # 推进版本号
    round_num = len(set(e["case_id"] for e in weights["evolution_log"]))
    weights["version"] = f"v7.0_R{round_num}"

    save_weights(weights)

    print(f"[ArbitrationWeights] {factor_path}: {old_val} → {new_val} "
          f"({direction}, case={case_id})")

    return weights


def get_evolution_summary() -> Dict[str, Any]:
    """获取权重进化历史摘要"""
    weights = load_weights()
    log = weights.get("evolution_log", [])
    if not log:
        return {"version": weights["version"], "total_adjustments": 0, "log": []}

    return {
        "version": weights["version"],
        "total_adjustments": len(log),
        "distinct_cases": len(set(e["case_id"] for e in log)),
        "factors_adjusted": list(set(e["factor_path"] for e in log)),
        "last_adjustment": log[-1] if log else None,
        "log": log,
    }


def reset_to_defaults() -> Dict[str, Any]:
    """重置权重为默认值（保留历史日志）"""
    old_weights = load_weights()
    old_log = old_weights.get("evolution_log", [])

    new_weights = deepcopy(DEFAULT_WEIGHTS)
    new_weights["created_at"] = old_weights.get("created_at", datetime.now().isoformat())
    new_weights["version"] = f"v7.0_R0_reset_{datetime.now().strftime('%Y%m%d')}"

    # 保留历史日志 + 添加 reset 记录
    new_weights["evolution_log"] = old_log + [{
        "timestamp": datetime.now().isoformat(),
        "event": "RESET_TO_DEFAULTS",
        "reason": "Manual reset",
    }]

    save_weights(new_weights)
    return new_weights
