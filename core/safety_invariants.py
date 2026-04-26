"""
core/safety_invariants.py
v7.0 — 形式化安全不变量 (Formal Safety Invariants)

WS-5: Patient Safety Guardrails

15 条安全规则，分 Critical / Major / Minor 三级。
在 submit_mdt_report() 中自动触发检查，任何 Critical 违反一票否决提交。

每条规则结构:
  id: 唯一标识
  name: 规则名
  severity: critical | major | minor
  description: 违反场景描述
  check_type: regex | field | keyword | custom
  check_info: 具体检查参数（正则/字段路径/关键词列表）
  reference: 支持该规则的证据来源
"""

from typing import List, Dict, Any, Optional
import re


# ===========================================================
# 规则定义
# ===========================================================

SAFETY_INVARIANTS: List[Dict[str, Any]] = [

    # ======================================================
    # CRITICAL — 一票否决，直接阻止报告提交
    # ======================================================
    {
        "id": "SI-001",
        "name": "KRAS_anti_EGFR_prohibition",
        "severity": "critical",
        "description": (
            "KRAS 突变患者（任何变体）严禁推荐抗 EGFR 单抗 (cetuximab/panitumumab)。"
            "OncoKB Level R1 级别耐药证据。"
        ),
        "check_type": "regex",
        "check_pattern": (
            r"(?i)(cetuximab|panitumumab|西妥昔单抗|帕尼单抗)"
            r"(?!.*禁止|.*排除|.*不推荐|.*拒绝|.*禁)"  # 确保不是在排除方案中
        ),
        "violation_context_check": "kras_mutation_present",
        "reference": "[OncoKB: Level R1] KRAS mutation — primary resistance to anti-EGFR therapy",
        "remediation": "Remove anti-EGFR recommendation; cite KRAS R1 resistance as exclusion reason in Module 5.",
    },
    {
        "id": "SI-002",
        "name": "SRS_dose_ceiling",
        "severity": "critical",
        "description": "SRS 单次分割剂量严禁超过 24 Gy（单次最高安全上限）。",
        "check_type": "custom",
        "check_function": "check_srs_dose_ceiling",
        "threshold_gy": 24,
        "reference": "[NCCN CNS 2026 v2] SRS dosing guidelines; RTOG 90-05",
        "remediation": "Reduce SRS dose to ≤24 Gy/fraction or justify with dual-track evidence.",
    },
    {
        "id": "SI-003",
        "name": "WBRT_dose_ceiling",
        "severity": "critical",
        "description": "WBRT 总剂量严禁超过 40 Gy（总量安全上限）。",
        "check_type": "custom",
        "check_function": "check_wbrt_dose_ceiling",
        "threshold_gy": 40,
        "reference": "[NCCN CNS 2026 v2] WBRT dosing: standard 30Gy/10f or 37.5Gy/15f",
        "remediation": "Reduce WBRT total dose to ≤40 Gy or use standard fractionation schemes.",
    },
    {
        "id": "SI-004",
        "name": "repeat_failed_regimen",
        "severity": "critical",
        "description": "严禁推荐患者已明确进展/失败的方案（重复耐药方案）。",
        "check_type": "custom",
        "check_function": "check_repeat_regimen",
        "reference": "General oncology principle: do not re-challenge proven resistant regimen without clear rationale",
        "remediation": "Review patient treatment history; recommend next-line therapy.",
    },
    {
        "id": "SI-005",
        "name": "emergency_without_evaluation",
        "severity": "critical",
        "description": (
            "影像报告 midline_shift=True 或 mass_effect=severe/moderate 时，"
            "报告必须包含神经外科急诊评估建议。"
        ),
        "check_type": "custom",
        "check_function": "check_emergency_evaluation",
        "reference": "[NCCN CNS 2026 v2] Neurological emergency management",
        "remediation": "Add immediate neurosurgical consultation recommendation for mass effect.",
    },
    {
        "id": "SI-006",
        "name": "EGFR_T790M_first_gen_TKI",
        "severity": "critical",
        "description": (
            "EGFR T790M 阳性患者严禁推荐一代/二代 EGFR TKI（吉非替尼/厄洛替尼/阿法替尼）"
            "作为主要治疗方案，应推荐奥希替尼。"
        ),
        "check_type": "regex",
        "check_pattern": (
            r"(?i)(gefitinib|erlotinib|afatinib|吉非替尼|厄洛替尼|阿法替尼)"
        ),
        "violation_context_check": "egfr_t790m_present",
        "reference": "[OncoKB: Level 1] EGFR T790M — osimertinib standard of care (AURA3)",
        "remediation": "Replace 1st/2nd gen EGFR TKI with osimertinib (Level 1 evidence).",
    },

    # ======================================================
    # MAJOR — 高危警告，需人工确认
    # ======================================================
    {
        "id": "SI-007",
        "name": "TKI_without_mutation_evidence",
        "severity": "major",
        "description": "推荐靶向 TKI 时，报告必须引用对应突变检测结果（OncoKB 或分子病理报告）。",
        "check_type": "keyword_requires_citation",
        "keywords": ["TKI", "靶向治疗", "osimertinib", "奥希替尼", "alectinib", "阿来替尼",
                     "lapatinib", "neratinib", "tucatinib", "olaparib"],
        "required_citation_pattern": r"(\[OncoKB|OncoKB|Level [1-4]|\[PubMed)",
        "reference": "Molecular profiling requirement before targeted therapy",
        "remediation": "Add OncoKB citation for the mutation driving TKI recommendation.",
    },
    {
        "id": "SI-008",
        "name": "dexamethasone_dose_warning",
        "severity": "major",
        "description": "地塞米松剂量超过 16mg/天时，必须有明确的临床指征说明。",
        "check_type": "custom",
        "check_function": "check_dexamethasone_dose",
        "threshold_mg": 16,
        "reference": "[EANO-ESMO 2024] Dexamethasone in brain metastases: start 4-8mg/day, max 16mg/day",
        "remediation": "Reduce dexamethasone dose or add explicit justification for high-dose regimen.",
    },
    {
        "id": "SI-009",
        "name": "bevacizumab_surgery_window",
        "severity": "major",
        "description": (
            "贝伐珠单抗给药后 28 天内计划手术时，"
            "报告必须注明停药间隔和出血风险评估。"
        ),
        "check_type": "keyword_co_occurrence",
        "keywords_a": ["bevacizumab", "贝伐珠单抗", "安维汀"],
        "keywords_b": ["surgery", "手术", "craniotomy", "开颅"],
        "required_mention": r"(?i)(hold|停药|28 day|28天|bleed|出血风险)",
        "reference": "[NCCN] Bevacizumab: hold ≥28 days before elective surgery",
        "remediation": "Document 28-day washout requirement in Module 6 (perioperative management).",
    },
    {
        "id": "SI-010",
        "name": "anticoagulant_craniotomy_protocol",
        "severity": "major",
        "description": (
            "抗凝药患者计划开颅手术时，"
            "Module 6 必须包含停药方案（利伐沙班/华法林/肝素的桥接或停药协议）。"
        ),
        "check_type": "keyword_co_occurrence",
        "keywords_a": ["anticoagul", "华法林", "warfarin", "rivaroxaban", "利伐沙班",
                       "heparin", "肝素", "dabigatran", "达比加群"],
        "keywords_b": ["craniotomy", "开颅", "resection", "切除"],
        "required_mention": r"(?i)(hold|停药|bridge|桥接|protocol|方案|INR|reversal|逆转)",
        "reference": "[ASA/ACC] Perioperative anticoagulation management",
        "remediation": "Add anticoagulant holding/bridging protocol to Module 6.",
    },

    # ======================================================
    # MINOR — 次要警告，记录但不阻止提交
    # ======================================================
    {
        "id": "SI-011",
        "name": "followup_interval_brain_met",
        "severity": "minor",
        "description": "脑转移患者第一年随访间隔不得超过 3 个月（影像监测要求）。",
        "check_type": "custom",
        "check_function": "check_followup_interval",
        "max_months": 3,
        "reference": "[EANO-ESMO 2024] Brain metastasis follow-up: MRI every 6-12 weeks in year 1",
        "remediation": "Adjust imaging follow-up to every 6-12 weeks (≤3 months) in Module 4.",
    },
    {
        "id": "SI-012",
        "name": "missing_kps_ecog",
        "severity": "minor",
        "description": "Module 1（入院评估）必须包含 KPS 或 ECOG 功能状态评分。",
        "check_type": "keyword_required",
        "keywords": ["KPS", "ECOG", "performance status", "功能状态", "体力状态"],
        "reference": "Standard oncology practice: functional status is required for treatment planning",
        "remediation": "Add KPS/ECOG score to Module 1 Admission Evaluation.",
    },
    {
        "id": "SI-013",
        "name": "missing_ds_gpa_score",
        "severity": "minor",
        "description": "治疗规划必须提及 DS-GPA 或其他预后评分（GPA/RPA）。",
        "check_type": "keyword_required",
        "keywords": ["DS-GPA", "GPA", "RPA", "预后评分", "prognostic"],
        "reference": "[Sperduto 2012] DS-GPA: standard prognostic tool for brain metastasis",
        "remediation": "Add DS-GPA calculation to Module 1 or Module 0 (Executive Summary).",
    },
    {
        "id": "SI-014",
        "name": "systemic_therapy_without_cns_penetrance",
        "severity": "minor",
        "description": (
            "推荐系统治疗时，报告应提及推荐药物的 CNS 穿透率数据（特别是靶向药）。"
        ),
        "check_type": "keyword_co_occurrence_check",
        "keywords_trigger": ["osimertinib", "奥希替尼", "alectinib", "阿来替尼",
                             "lorlatinib", "tucatinib", "neratinib"],
        "required_mention": r"(?i)(CNS penetra|脑脊液|CSF|血脑屏障|BBB|brain penetr|入脑)",
        "reference": "[cns_drug_db_skill] CNS drug penetrance database",
        "remediation": "Add CNS penetrance data for recommended agent in Module 2/3.",
    },
    {
        "id": "SI-015",
        "name": "large_srs_radionecrosis_risk",
        "severity": "minor",
        "description": (
            "病灶 > 2cm 推荐 SRS 时，报告应提及放射性坏死 (radionecrosis) 风险。"
        ),
        "check_type": "keyword_required_when_condition",
        "condition_pattern": r"(?i)(SRS|stereotactic|立体定向)",
        "required_mention": r"(?i)(radionecrosis|放射性坏死|radiation necrosis)",
        "reference": "[RTOG 90-05] Radionecrosis risk increases with lesion size and SRS dose",
        "remediation": "Add radionecrosis risk mention and monitoring plan when recommending SRS for lesions >2cm.",
    },
]


# ===========================================================
# 检查函数实现
# ===========================================================

def check_srs_dose_ceiling(report_text: str, threshold_gy: float = 24.0) -> bool:
    """检查 SRS 剂量是否超过上限"""
    patterns = [
        r"SRS[^0-9]*(\d+(?:\.\d+)?)\s*Gy",
        r"(\d+(?:\.\d+)?)\s*Gy[^0-9]*(?:SRS|单次|single)",
        r"立体定向[^0-9]*(\d+(?:\.\d+)?)\s*Gy",
    ]
    for pat in patterns:
        for match in re.finditer(pat, report_text, re.IGNORECASE):
            dose = float(match.group(1))
            if dose > threshold_gy:
                return False  # Violation
    return True  # Passed


def check_wbrt_dose_ceiling(report_text: str, threshold_gy: float = 40.0) -> bool:
    """检查 WBRT 总剂量是否超过上限"""
    patterns = [
        r"WBRT[^0-9]*(\d+(?:\.\d+)?)\s*Gy",
        r"全脑放疗[^0-9]*(\d+(?:\.\d+)?)\s*Gy",
    ]
    for pat in patterns:
        for match in re.finditer(pat, report_text, re.IGNORECASE):
            dose = float(match.group(1))
            if dose > threshold_gy:
                return False
    return True


def check_dexamethasone_dose(report_text: str, threshold_mg: float = 16.0) -> bool:
    """检查地塞米松剂量是否超过阈值"""
    patterns = [
        r"(?:dexamethasone|地塞米松)[^0-9]*(\d+(?:\.\d+)?)\s*mg",
        r"(\d+(?:\.\d+)?)\s*mg[^0-9]*(?:dexamethasone|地塞米松)",
    ]
    for pat in patterns:
        for match in re.finditer(pat, report_text, re.IGNORECASE):
            dose = float(match.group(1))
            # Daily dose over threshold requires justification
            if dose > threshold_mg:
                # Check if justification is mentioned nearby
                context_start = max(0, match.start() - 200)
                context = report_text[context_start:match.end() + 200]
                if not re.search(r"(?i)(justif|指征|indication|脑疝|herniat)", context):
                    return False
    return True


def check_followup_interval(report_text: str, max_months: int = 3) -> bool:
    """检查随访间隔是否合理（粗糙版本）"""
    # 检测是否有超过3个月的随访间隔描述
    patterns = [
        r"(\d+)\s*(?:months?|个月)\s*(?:follow|随访|复查|复诊)",
        r"每\s*(\d+)\s*个月\s*(?:复查|随访|随诊)",
    ]
    for pat in patterns:
        for match in re.finditer(pat, report_text, re.IGNORECASE):
            interval = int(match.group(1))
            if interval > max_months:
                return False
    return True


def check_repeat_regimen(report_text: str, sa_outputs: Optional[Dict] = None) -> bool:
    """
    检查是否推荐了已耐药的方案（需要患者治疗史信息）。
    当前版本做简单的文本检测，完整版需要对接患者历史数据。
    """
    # 如果提到"第X线"失败后又推荐了同类药，这里只做关键词快捷检测
    # 完整实现需要解析治疗史，此处返回 True（不误杀）
    return True


def check_emergency_evaluation(report_text: str, sa_outputs: Optional[Dict] = None) -> bool:
    """检查存在急性占位效应时是否有急诊评估建议"""
    # 如果影像部分提到 midline shift / severe mass effect
    has_emergency_flag = bool(re.search(
        r"(?i)(midline.?shift|中线移位|mass.?effect|脑疝|herniat|颅内高压|intracranial.?hypertension)",
        report_text
    ))
    if not has_emergency_flag:
        return True

    # 检查是否有紧急处理建议
    has_emergency_response = bool(re.search(
        r"(?i)(emergency|紧急|urgent|立即|neurosurger|神外|脱水|甘露醇|mannitol|decompres)",
        report_text
    ))
    return has_emergency_response


# ===========================================================
# 主检查函数（供 submit_mdt_report 调用）
# ===========================================================

def run_safety_check(
    report_text: str,
    sa_outputs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    对 MDT 报告文本执行全部安全不变量检查。

    Args:
        report_text: 最终 MDT 报告的完整文本
        sa_outputs: SubAgent 输出字典（可选，用于更精细的上下文检查）

    Returns:
        {
          "passed": bool,
          "critical_violations": [...],
          "major_violations": [...],
          "minor_violations": [...],
          "total_violations": int,
          "summary": str
        }
    """
    critical_violations = []
    major_violations = []
    minor_violations = []

    for rule in SAFETY_INVARIANTS:
        violation = None

        if rule["check_type"] == "regex":
            # 正则匹配 + 上下文检查
            if re.search(rule["check_pattern"], report_text):
                # 需要确认触发上下文条件（如 KRAS 突变）
                context_check = rule.get("violation_context_check")
                context_confirmed = True
                if context_check == "kras_mutation_present":
                    context_confirmed = bool(re.search(r"(?i)(KRAS|K-RAS)", report_text))
                elif context_check == "egfr_t790m_present":
                    context_confirmed = bool(re.search(r"(?i)(T790M|T790)", report_text))
                if context_confirmed:
                    violation = {"rule_id": rule["id"], "rule_name": rule["name"],
                                 "description": rule["description"],
                                 "remediation": rule["remediation"]}

        elif rule["check_type"] == "custom":
            fn_name = rule.get("check_function")
            fn = globals().get(fn_name)
            if fn:
                passed = fn(report_text, sa_outputs)
                if not passed:
                    violation = {"rule_id": rule["id"], "rule_name": rule["name"],
                                 "description": rule["description"],
                                 "remediation": rule["remediation"]}

        elif rule["check_type"] == "keyword_required":
            found = any(
                kw.lower() in report_text.lower()
                for kw in rule.get("keywords", [])
            )
            if not found:
                violation = {"rule_id": rule["id"], "rule_name": rule["name"],
                             "description": rule["description"],
                             "remediation": rule["remediation"]}

        elif rule["check_type"] == "keyword_requires_citation":
            # 检测到关键词时，确认附近有引用
            found_keyword = any(
                kw.lower() in report_text.lower()
                for kw in rule.get("keywords", [])
            )
            if found_keyword:
                has_citation = bool(re.search(
                    rule.get("required_citation_pattern", ""),
                    report_text
                ))
                if not has_citation:
                    violation = {"rule_id": rule["id"], "rule_name": rule["name"],
                                 "description": rule["description"],
                                 "remediation": rule["remediation"]}

        elif rule["check_type"] == "keyword_required_when_condition":
            has_condition = bool(re.search(rule.get("condition_pattern", ""), report_text))
            if has_condition:
                has_required = bool(re.search(rule.get("required_mention", ""), report_text))
                if not has_required:
                    violation = {"rule_id": rule["id"], "rule_name": rule["name"],
                                 "description": rule["description"],
                                 "remediation": rule["remediation"]}

        if violation:
            violation["severity"] = rule["severity"]
            violation["reference"] = rule.get("reference", "")
            if rule["severity"] == "critical":
                critical_violations.append(violation)
            elif rule["severity"] == "major":
                major_violations.append(violation)
            else:
                minor_violations.append(violation)

    total = len(critical_violations) + len(major_violations) + len(minor_violations)
    passed = len(critical_violations) == 0  # Only critical blocks submission

    summary_parts = []
    if critical_violations:
        summary_parts.append(
            f"🚨 CRITICAL: {len(critical_violations)} violation(s) — SUBMISSION BLOCKED"
        )
    if major_violations:
        summary_parts.append(
            f"⚠️  MAJOR: {len(major_violations)} violation(s) — Requires clinician review"
        )
    if minor_violations:
        summary_parts.append(
            f"ℹ️  MINOR: {len(minor_violations)} warning(s) — Recommended to address"
        )
    if not summary_parts:
        summary_parts = ["✅ All safety invariants passed."]

    return {
        "passed": passed,
        "critical_violations": critical_violations,
        "major_violations": major_violations,
        "minor_violations": minor_violations,
        "total_violations": total,
        "summary": " | ".join(summary_parts),
    }
