"""
tools/conflict_calculator.py
v7.0 — 冲突量化计算工具

供 Orchestrator 通过 execute 调用:
  python tools/conflict_calculator.py --votes-json /path/to/votes_{patient_id}.json

输入 JSON 格式:
{
  "imaging-specialist":           {"local_therapy_modality": "SRS",   "surgery_indication": "No_Surgery", ...},
  "primary-oncology-specialist":  {"local_therapy_modality": "SRS",   "systemic_therapy_class": "Targeted_TKI", ...},
  "neurosurgery-specialist":      {"surgery_indication": "No_Surgery", ...},
  "radiation-oncology-specialist":{"local_therapy_modality": "SRS",   ...},
  "molecular-pathology-specialist":{"molecular_testing_need": "Targeted_Panel", ...}
}

(每个 Agent 只填写其有权评估的 KDP，其他 KDP 填 "Not_Applicable" 或省略)

输出 JSON (AgreementMatrix 格式):
{
  "kendall_w_approx": 0.92,
  "pairwise_kappa": {"agentA_vs_agentB": 0.85, ...},
  "per_kdp_agreement": {"local_therapy_modality": 1.0, "surgery_indication": 0.75, ...},
  "total_agents_participating": 5,
  "total_conflicts": 1,
  "conflicts": [
    {
      "kdp_id": "surgery_indication",
      "conflicting_agents": ["neurosurgery-specialist"],
      "majority_option": "No_Surgery",
      "minority_options": {"neurosurgery-specialist": "Elective_Surgery"},
      "agreement_rate": 0.75
    }
  ]
}
"""

import json
import sys
import argparse
from itertools import combinations
from collections import Counter
from typing import Dict, List, Tuple, Any

# KDP 中认为是"弃权"的标记值（不参与冲突检测）
ABSTAIN_VALUES = {"Not_Applicable", "N/A", "NA", "none", "None", ""}


def cohens_kappa(votes_a: List[str], votes_b: List[str]) -> float:
    """
    计算两个评分者间的 Cohen's Kappa。
    自动忽略任一方弃权的 KDP。
    返回 [-1, 1]，值越接近 1 越一致。
    """
    # 过滤双方都有有效投票的 KDP
    valid_pairs = [
        (a, b) for a, b in zip(votes_a, votes_b)
        if a not in ABSTAIN_VALUES and b not in ABSTAIN_VALUES
    ]

    if len(valid_pairs) == 0:
        return 1.0  # 无共同决策点，视为一致

    n = len(valid_pairs)
    va = [p[0] for p in valid_pairs]
    vb = [p[1] for p in valid_pairs]

    # 观测一致率
    po = sum(1 for a, b in zip(va, vb) if a == b) / n

    # 期望一致率
    all_labels = set(va + vb)
    pe = 0.0
    for label in all_labels:
        pa = va.count(label) / n
        pb = vb.count(label) / n
        pe += pa * pb

    if pe >= 1.0:
        return 1.0
    return round((po - pe) / (1.0 - pe), 4)


def compute_per_kdp_agreement(
    data: Dict[str, Dict[str, str]],
    kdps: List[str]
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """
    计算每个 KDP 的一致率，并识别冲突。

    Returns:
        per_kdp: {kdp_id: agreement_rate}
        conflicts: list of conflict records
    """
    per_kdp: Dict[str, float] = {}
    conflicts: List[Dict[str, Any]] = []
    agents = list(data.keys())

    for kdp in kdps:
        # 获取各 Agent 对该 KDP 的有效投票
        votes = {
            agent: data[agent].get(kdp, "Not_Applicable")
            for agent in agents
        }
        valid_votes = {
            a: v for a, v in votes.items() if v not in ABSTAIN_VALUES
        }

        if len(valid_votes) == 0:
            per_kdp[kdp] = 1.0  # 全部弃权，视为不适用
            continue

        counter = Counter(valid_votes.values())
        most_common_option, most_common_count = counter.most_common(1)[0]
        agreement_rate = most_common_count / len(valid_votes)
        per_kdp[kdp] = round(agreement_rate, 4)

        if agreement_rate < 1.0:
            # 找出与多数不同的 Agent
            minority = {a: v for a, v in valid_votes.items() if v != most_common_option}
            conflicts.append({
                "kdp_id": kdp,
                "conflicting_agents": list(minority.keys()),
                "majority_option": most_common_option,
                "all_options": dict(valid_votes),
                "minority_options": minority,
                "agreement_rate": round(agreement_rate, 4),
                "participating_agents": len(valid_votes),
            })

    return per_kdp, conflicts


def compute_kendall_w_approx(per_kdp: Dict[str, float]) -> float:
    """
    对于分类变量，用各 KDP 一致率的加权均值近似 Kendall's W。
    真实 Kendall's W 仅对排序变量有意义，此处作为论文报告的近似指标。
    """
    if not per_kdp:
        return 1.0
    return round(sum(per_kdp.values()) / len(per_kdp), 4)


def main():
    parser = argparse.ArgumentParser(
        description="TiantanBM v7.0 Conflict Calculator — Computes κ/W/Agreement Matrix"
    )
    parser.add_argument(
        "--votes-json", required=True,
        help="Path to votes JSON file (agent → kdp_id → chosen_option)"
    )
    parser.add_argument(
        "--kdps", nargs="+",
        default=[
            "local_therapy_modality",
            "surgery_indication",
            "systemic_therapy_class",
            "treatment_urgency",
            "molecular_testing_need",
        ],
        help="KDP IDs to evaluate (default: all 5 standard KDPs)"
    )
    args = parser.parse_args()

    # Load votes
    with open(args.votes_json, "r", encoding="utf-8") as f:
        data: Dict[str, Dict[str, str]] = json.load(f)

    if len(data) < 2:
        print(json.dumps({
            "error": "At least 2 agents required for agreement calculation",
            "agents_found": list(data.keys())
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    agents = list(data.keys())
    kdps = args.kdps

    # 1. Per-KDP agreement + conflicts
    per_kdp, conflicts = compute_per_kdp_agreement(data, kdps)

    # 2. Pairwise Cohen's κ
    pairwise_kappa: Dict[str, float] = {}
    for agent_a, agent_b in combinations(agents, 2):
        votes_a = [data[agent_a].get(k, "Not_Applicable") for k in kdps]
        votes_b = [data[agent_b].get(k, "Not_Applicable") for k in kdps]
        kappa = cohens_kappa(votes_a, votes_b)
        key = f"{agent_a}_vs_{agent_b}"
        pairwise_kappa[key] = kappa

    # 3. Kendall's W approximation
    w_approx = compute_kendall_w_approx(per_kdp)

    # 4. Mean kappa summary
    mean_kappa = round(
        sum(pairwise_kappa.values()) / len(pairwise_kappa), 4
    ) if pairwise_kappa else 1.0

    # 5. Conflict heatmap summary text
    heatmap_parts = []
    for c in conflicts:
        conflict_type = "Urgency_Conflict" if "urgency" in c["kdp_id"] else \
                        "Modality_Conflict" if "modality" in c["kdp_id"] else \
                        "Sequencing_Conflict" if "sequence" in c["kdp_id"] else \
                        "Evidence_Level_Conflict"
        heatmap_parts.append(
            f"{c['kdp_id']}: {len(c['conflicting_agents'])} agent(s) dissenting "
            f"({conflict_type}, agreement={c['agreement_rate']:.2f})"
        )
    heatmap_summary = "; ".join(heatmap_parts) if heatmap_parts else "All KDPs: unanimous"

    result = {
        "kendall_w_approx": w_approx,
        "mean_pairwise_kappa": mean_kappa,
        "pairwise_kappa": pairwise_kappa,
        "per_kdp_agreement": per_kdp,
        "total_agents_participating": len(agents),
        "agents": agents,
        "total_conflicts": len(conflicts),
        "conflicts": conflicts,
        "conflict_heatmap_summary": heatmap_summary,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
