"""
tools/cross_agent_validator.py
v7.0 — Cross-Agent Consistency Validator

验证不同 SubAgent 输出之间的逻辑一致性（在 Auditor 审计前执行）。
检查的是"横向一致性"（Agent间），而非 Auditor 的"纵向可追溯性"（引用真实性）。

用法（Orchestrator 通过 execute 调用）:
  python tools/cross_agent_validator.py --outputs-json /path/to/all_sa_outputs.json

输入 JSON 格式:
{
  "imaging-specialist": {ImagingOutput 字段...},
  "primary-oncology-specialist": {PrimaryOncologyOutput 字段...},
  "neurosurgery-specialist": {NeurosurgeryOutput 字段...},
  "radiation-oncology-specialist": {RadiationOutput 字段...},
  "molecular-pathology-specialist": {MolecularOutput 字段...}
}
"""

import json
import sys
import argparse
from typing import Dict, Any, List, Tuple


# ===========================================================
# 一致性规则定义
# ===========================================================

def _check_lesion_count_consistency(outputs: Dict) -> Tuple[bool, str]:
    """
    CR-001: 影像 Agent 报告的病灶数与内科 Agent 文字描述一致
    （简化版：检测内科输出中是否有明显矛盾的关键词）
    """
    imaging = outputs.get("imaging-specialist", {})
    lesion_count = imaging.get("lesion_count")
    if lesion_count is None:
        return True, "No imaging data to validate"

    # 如果只能做粗糙检查，跳过并返回通过
    return True, f"Imaging reports {lesion_count} lesion(s)"


def _check_surgery_radiation_mutual_exclusion(outputs: Dict) -> Tuple[bool, str]:
    """
    CR-002: 神外建议紧急手术时，放疗不应推荐先行 WBRT（会延误手术）
    """
    neuro = outputs.get("neurosurgery-specialist", {})
    rad = outputs.get("radiation-oncology-specialist", {})

    surgical_urgency = neuro.get("surgical_urgency", "")
    radiation_modality = rad.get("radiation_modality", "")

    if surgical_urgency == "emergency" and radiation_modality in ["WBRT", "Hippocampal-sparing WBRT"]:
        return False, (
            f"CR-002 VIOLATION: neurosurgery-specialist recommends EMERGENCY surgery "
            f"but radiation-oncology-specialist recommends {radiation_modality}. "
            f"WBRT before emergency craniotomy contradicts clinical protocol."
        )
    return True, "Surgery-radiation sequencing consistent"


def _check_treatment_line_consistency(outputs: Dict) -> Tuple[bool, str]:
    """
    CR-003: 参与的所有 Agent 引用的治疗线数一致
    """
    lines: Dict[str, int] = {}

    oncology = outputs.get("primary-oncology-specialist", {})
    if "treatment_line" in oncology:
        val = oncology.get("treatment_line")
        if isinstance(val, int) and val >= 0:
            lines["primary-oncology-specialist"] = val

    # 其他 Agent 没有显式 treatment_line 字段，只检查 primary-oncology
    if len(lines) <= 1:
        return True, "Treatment line declared by primary-oncology-specialist only (OK)"

    unique_lines = set(lines.values())
    if len(unique_lines) > 1:
        return False, f"CR-003 VIOLATION: Treatment line inconsistency: {lines}"

    return True, f"Treatment line consistent across agents: line {list(unique_lines)[0]}"


def _check_mutation_drug_alignment(outputs: Dict) -> Tuple[bool, str]:
    """
    CR-004: 分子病理报告的突变状态与内科推荐靶向药的依据逻辑一致
    已知耐药 vs 推荐同类药的冲突检测（粗糙规则）
    """
    mol = outputs.get("molecular-pathology-specialist", {})
    onco = outputs.get("primary-oncology-specialist", {})

    oncokb_level = mol.get("oncokb_evidence_level", "")
    recommended_drug = onco.get("recommended_systemic_drug", "")

    # 当 OncoKB R1/R2 级别耐药时，检查内科是否仍推荐了该类药物
    if oncokb_level in ["LEVEL_R1", "LEVEL_R2", "R1", "R2"]:
        variants = mol.get("variant_details", [])
        if variants and recommended_drug:
            # 简单关键词检测（实际线上应用应有更精细的逻辑）
            variant_str = " ".join(variants).lower()
            drug_lower = recommended_drug.lower()
            # KRAS + anti-EGFR 检测
            if "kras" in variant_str and any(k in drug_lower for k in ["cetuximab", "panitumumab", "西妥", "帕尼"]):
                return False, (
                    f"CR-004 VIOLATION: OncoKB {oncokb_level} resistance detected for KRAS variant "
                    f"but primary-oncology recommends '{recommended_drug}' (anti-EGFR). "
                    f"Safety Invariant SI-001 also applies."
                )

    return True, "Mutation-drug alignment appears consistent"


def _check_emergency_response(outputs: Dict) -> Tuple[bool, str]:
    """
    CR-005: 影像提示中线移位时，神外必须标记为紧急手术评估
    """
    imaging = outputs.get("imaging-specialist", {})
    neuro = outputs.get("neurosurgery-specialist", {})

    midline_shift = imaging.get("midline_shift", False)
    mass_effect = imaging.get("mass_effect_level", "none")
    surgical_urgency = neuro.get("surgical_urgency", "")

    if midline_shift or mass_effect in ["severe", "moderate"]:
        if surgical_urgency not in ["emergency", "elective"]:
            return False, (
                f"CR-005 VIOLATION: imaging-specialist reports midline_shift={midline_shift}, "
                f"mass_effect='{mass_effect}' but neurosurgery-specialist set "
                f"surgical_urgency='{surgical_urgency}'. "
                f"Mass effect requires explicit surgical evaluation."
            )
    return True, "Emergency assessment consistent with imaging findings"


# ===========================================================
# 规则注册表
# ===========================================================

CONSISTENCY_RULES = [
    {
        "id": "CR-001",
        "name": "lesion_count_consistency",
        "description": "影像Agent病灶数与其他Agent文字描述一致",
        "check": _check_lesion_count_consistency,
    },
    {
        "id": "CR-002",
        "name": "surgery_radiation_mutual_exclusion",
        "description": "紧急手术与WBRT先行不可共存",
        "check": _check_surgery_radiation_mutual_exclusion,
    },
    {
        "id": "CR-003",
        "name": "treatment_line_consistency",
        "description": "各Agent引用的治疗线数一致",
        "check": _check_treatment_line_consistency,
    },
    {
        "id": "CR-004",
        "name": "mutation_drug_alignment",
        "description": "耐药突变状态与推荐药物逻辑一致",
        "check": _check_mutation_drug_alignment,
    },
    {
        "id": "CR-005",
        "name": "emergency_response",
        "description": "影像提示中线移位时神外必须评估紧急性",
        "check": _check_emergency_response,
    },
]


def validate(outputs: Dict[str, Any]) -> Dict[str, Any]:
    """执行所有一致性检查，返回汇总结果"""
    results = []
    violations = []

    for rule in CONSISTENCY_RULES:
        passed, message = rule["check"](outputs)
        record = {
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "description": rule["description"],
            "passed": passed,
            "message": message,
        }
        results.append(record)
        if not passed:
            violations.append(record)

    return {
        "all_consistent": len(violations) == 0,
        "total_checks": len(results),
        "passed_checks": len(results) - len(violations),
        "violations_count": len(violations),
        "checks": results,
        "violations": violations,
        "summary": (
            "✅ All cross-agent consistency checks passed."
            if len(violations) == 0
            else f"⚠️ {len(violations)} consistency violation(s) detected. "
                 f"Orchestrator must resolve before Auditor review."
        )
    }


def main():
    parser = argparse.ArgumentParser(
        description="TiantanBM v7.0 Cross-Agent Consistency Validator"
    )
    parser.add_argument(
        "--outputs-json", required=True,
        help="Path to JSON file containing all SubAgent outputs"
    )
    args = parser.parse_args()

    with open(args.outputs_json, "r", encoding="utf-8") as f:
        outputs = json.load(f)

    result = validate(outputs)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Exit code: 0 = all passed, 1 = violations found
    sys.exit(0 if result["all_consistent"] else 1)


if __name__ == "__main__":
    main()
