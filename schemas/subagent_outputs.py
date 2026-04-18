"""
schemas/subagent_outputs.py
v6.0 — SubAgent 结构化输出 Schema

每个专科 SubAgent 必须在返回中包含一个 JSON block（```json ... ```），
其结构由以下 Pydantic Model 定义。

Orchestrator 从 SubAgent 的自然语言返回中提取 JSON block，
并用这些 Schema 进行解析和共识计算。
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ===========================================================
# 通用基础类型
# ===========================================================

class CitedClaim(BaseModel):
    """一条带物理引用的临床声明（所有专科通用）"""
    claim: str = Field(description="具体的临床陈述")
    citation: str = Field(
        description=(
            "物理溯源引用，必须是以下格式之一：\n"
            "  [Local: <FILENAME>.md, Line <N>]\n"
            "  [Local: <FILENAME>.pdf, Page <N>, Dual-Track Verified ✓]\n"
            "  [PubMed: PMID <NNNNNNNN>]\n"
            "  [OncoKB: Level <X>]"
        )
    )
    evidence_level: Optional[str] = Field(
        default=None,
        description="如 Level 1A (RCT/Meta-analysis), Level 2A (Prospective), Level 3 (Retrospective)"
    )
    dual_track_verified: bool = Field(
        default=False,
        description="是否已执行文本+视觉双轨验证（仅适用于剂量/安全阈值参数）"
    )


class ConflictFlag(BaseModel):
    """标记本专科与其他专科潜在分歧的字段"""
    topic: str = Field(description="分歧议题，如 '局部治疗时序' 或 '系统治疗选择'")
    my_position: str = Field(description="本专科的立场")
    anticipated_conflict: str = Field(
        description="预计其他专科可能持有的不同观点"
    )
    resolution_suggestion: str = Field(
        description="本专科建议的证据权重裁决方向"
    )


# ===========================================================
# 1. 神经外科专科输出
# ===========================================================

class SurgicalRiskProfile(BaseModel):
    """手术风险分层"""
    kps_adequacy: str = Field(description="KPS 是否满足手术条件 (adequate/borderline/inadequate)")
    eloquent_area_risk: str = Field(description="功能区风险等级 (low/medium/high/critical)")
    bleeding_risk: str = Field(description="出血风险评估")
    anesthesia_risk: str = Field(description="麻醉风险评级")

class PerioperativeHolding(BaseModel):
    """围手术期停药参数"""
    drug_name: str
    hold_before_surgery_days: int = Field(description="术前停药天数")
    resume_after_surgery_days: int = Field(description="术后恢复天数")
    citation: str

class NeurosurgeryOutput(BaseModel):
    """神经外科专科 SubAgent 的结构化返回"""

    # 核心推荐
    surgical_recommendation: str = Field(
        description=(
            "最终手术推荐，必须是以下之一：\n"
            "  'resection' (手术切除)\n"
            "  'biopsy_only' (仅活检)\n"
            "  'no_surgery' (不手术)\n"
            "  'deferred' (暂缓，待进一步评估)"
        )
    )
    recommendation_rationale: List[CitedClaim] = Field(
        description="推荐理由（每条都必须有引用）"
    )

    # 手术方案细节（仅当 surgical_recommendation = 'resection' 时填写）
    surgical_approach: Optional[str] = Field(
        default=None,
        description="手术入路和方式，如 '显微镜下左额顶叶转移瘤切除术 + 神经导航'"
    )
    intraoperative_adjuncts: Optional[List[str]] = Field(
        default=None,
        description="术中辅助技术，如 ['清醒开颅', '荧光引导', '神经电生理监测']"
    )

    # 风险评估
    risk_profile: SurgicalRiskProfile

    # 围手术期管理（如推荐手术或SRS，均需填写）
    perioperative_holding: List[PerioperativeHolding] = Field(
        default_factory=list,
        description="需要停药的药物清单（包含具体天数和引用）"
    )

    # 与放疗的协同意见
    local_therapy_sequencing: str = Field(
        description="建议的局部治疗时序，如 '手术后4-6周进行术腔SRS'"
    )

    # 分歧预警
    potential_conflicts: List[ConflictFlag] = Field(
        default_factory=list,
        description="预计与其他专科的分歧点"
    )


# ===========================================================
# 2. 放射肿瘤科专科输出
# ===========================================================

class RadiationDoseScheme(BaseModel):
    """放疗剂量方案（必须双轨验证）"""
    modality: str = Field(description="治疗方式，如 'SRS', 'SRT', 'WBRT', 'Hippocampal-sparing WBRT'")
    total_dose_gy: float = Field(description="总剂量（Gy），如 20.0, 24.0, 30.0")
    fractions: int = Field(description="分割次数，如 1, 3, 5, 10")
    dose_per_fraction_gy: float = Field(description="每次剂量（Gy）")
    target_lesion_size_constraint: Optional[str] = Field(
        default=None,
        description="剂量适用的病灶大小限制，如 '≤2cm', '>3cm 不推荐单次SRS'"
    )
    citation: str = Field(description="剂量方案的物理溯源引用（必须 Dual-Track Verified）")
    dual_track_verified: bool = Field(description="是否已执行PDF视觉双轨验证")

class RadiationOncologyOutput(BaseModel):
    """放射肿瘤科专科 SubAgent 的结构化返回"""

    # 核心推荐
    radiation_recommendation: str = Field(
        description=(
            "放疗推荐，必须是以下之一：\n"
            "  'SRS_upfront' (立体定向放射外科，首选)\n"
            "  'SRS_deferred' (SRS 暂缓，等待系统治疗评估)\n"
            "  'SRT' (立体定向放疗，分割版)\n"
            "  'WBRT' (全脑放疗)\n"
            "  'WBRT_hippocampal_sparing' (保海马全脑放疗)\n"
            "  'no_radiation' (不推荐放疗)\n"
            "  'cavity_SRS' (术腔SRS，手术后)"
        )
    )
    recommendation_rationale: List[CitedClaim]

    # 剂量方案（必须包含引用和双轨验证标记）
    primary_dose_scheme: RadiationDoseScheme
    alternative_dose_scheme: Optional[RadiationDoseScheme] = Field(
        default=None,
        description="备选方案（如功能区限制时的替代分割方案）"
    )

    # 安全评估
    radionecrosis_risk: str = Field(description="放射性坏死风险评级 (low/medium/high) 及依据")
    radionecrosis_monitoring_plan: str = Field(description="放射性坏死监测随访计划")

    # 与系统治疗的时序
    systemic_therapy_timing: str = Field(
        description=(
            "放疗与系统治疗的推荐时序，如：\n"
            "  'SRS优先，EGFR-TKI于SRS后3-5天恢复'\n"
            "  '先系统治疗，6-8周后评估局部治疗必要性'"
        )
    )

    # WBRT 认知毒性评估（如推荐WBRT时必填）
    wbrt_cognitive_risk: Optional[str] = Field(
        default=None,
        description="如推荐WBRT，必须评估认知毒性风险并说明是否使用Memantine/保海马技术"
    )

    # 分歧预警
    potential_conflicts: List[ConflictFlag] = Field(default_factory=list)


# ===========================================================
# 3. 肿瘤内科专科输出
# ===========================================================

class SystemicTherapyOption(BaseModel):
    """系统治疗方案选项"""
    option_label: str = Field(description="如 'Option_A_T790M阳性', 'Option_B_T790M阴性'")
    trigger_condition: str = Field(description="触发该方案的临床条件")
    drugs: List[str] = Field(description="药物列表，如 ['奥希替尼 80mg QD', '顺铂 75mg/m² Q3W']")
    drug_citations: List[CitedClaim] = Field(description="每个关键剂量的物理引用（双轨验证）")
    drug_interactions: Optional[List[str]] = Field(
        default=None,
        description="重要药物相互作用警告"
    )
    expected_cns_penetration: Optional[str] = Field(
        default=None,
        description="CNS 穿透性评估，如 '奥希替尼 CSF/血浆比 0.25，CNS ORR >60%'"
    )

class MedicalOncologyOutput(BaseModel):
    """肿瘤内科专科 SubAgent 的结构化返回"""

    # 治疗线判定
    treatment_line: str = Field(description="如 '一线初治', '二线（EGFR-TKI耐药后）', '六线后线'")
    treatment_line_rationale: List[CitedClaim]

    # 系统治疗方案（按场景分支）
    systemic_options: List[SystemicTherapyOption] = Field(
        description="按临床场景列出的系统治疗选项（至少1个主选项，可有备选）"
    )

    # 推荐优先顺序
    preferred_option_label: str = Field(description="当前最优选项的 option_label")
    preference_rationale: List[CitedClaim]

    # 局部治疗时序意见
    local_therapy_opinion: str = Field(
        description="内科对局部治疗时序的意见，如 '症状性BM应先局部治疗，不应延迟'"
    )

    # 分歧预警
    potential_conflicts: List[ConflictFlag] = Field(default_factory=list)


# ===========================================================
# 4. 分子病理科专科输出
# ===========================================================

class MolecularTestOrder(BaseModel):
    """分子检测医嘱"""
    test_name: str = Field(description="如 'EGFR T790M ctDNA', 'MSI-H/dMMR IHC'")
    sample_type: str = Field(description="如 '血浆ctDNA', '组织活检', 'CSF'")
    urgency: str = Field(description="'Emergency'(48h内), 'Routine'(1周内), 'Exploratory'(择期)")
    clinical_implication: CitedClaim = Field(description="该检测的临床意义及引用")
    expected_turnaround: str = Field(description="预计报告时间，如 '3-5工作日'")

class MolecularPathologyOutput(BaseModel):
    """分子病理科专科 SubAgent 的结构化返回"""

    # 已知分子信息解读
    known_biomarkers: List[CitedClaim] = Field(
        description="对已知分子结果的解读（EGFR状态、OncoKB证据等级等）"
    )

    # 推荐补充检测
    recommended_tests: List[MolecularTestOrder] = Field(
        description="优先级排序的检测医嘱列表"
    )

    # 治疗相关性总结
    actionable_alterations: List[CitedClaim] = Field(
        description="可干预的分子靶点及对应治疗选项（含OncoKB Evidence Level）"
    )
    resistance_mechanisms: List[CitedClaim] = Field(
        default_factory=list,
        description="已知或疑似的耐药机制（如T790M, MET扩增等）"
    )

    # 禁忌用药（分子层面）
    molecular_contraindications: List[CitedClaim] = Field(
        default_factory=list,
        description="基于分子特征的禁忌用药，如 'KRAS突变→禁用西妥昔单抗 [OncoKB: Level R1]'"
    )


# ===========================================================
# 5. 证据审计 SubAgent 输出
# ===========================================================

class AuditFinding(BaseModel):
    """单条审计发现"""
    location: str = Field(description="报告中的位置标识，如 'Module 2, Section 2.2'")
    claim_excerpt: str = Field(description="被审计的声明摘录（前50字符）")
    cited_source: str = Field(description="声明引用的来源字符串")
    verification_result: str = Field(
        description=(
            "验证结果，必须是以下之一：\n"
            "  'verified'       — 引用可在实际文件中找到且内容一致\n"
            "  'unverifiable'   — 引用格式正确但无法验证（如内容过于泛指）\n"
            "  'fabricated'     — 引用格式正确但实际不存在此内容\n"
            "  'inaccurate'     — 引用来源存在但内容与声明不符\n"
            "  'missing_dual_track' — 剂量类参数缺乏双轨验证标记"
        )
    )
    actual_content: Optional[str] = Field(
        default=None,
        description="如果 inaccurate，实际找到的内容是什么"
    )
    severity: str = Field(
        description="'critical'（强制修正）/ 'major'（建议修正）/ 'minor'（提示）"
    )
    recommendation: str = Field(description="具体修正建议")

class AuditorOutput(BaseModel):
    """证据审计 SubAgent 的结构化返回"""

    # 统计摘要
    total_claims_audited: int
    verified_count: int
    unverifiable_count: int
    fabricated_count: int
    inaccurate_count: int
    missing_dual_track_count: int

    # EGR 计算
    evidence_grounding_rate: float = Field(
        description=(
            "EGR = verified_count / total_claims_audited\n"
            "仅 'verified' 的声明计入分子，其余（fabricated/inaccurate/missing）均降低 EGR"
        )
    )

    # 审计通过判定
    pass_threshold: bool = Field(
        description=(
            "综合通过判定：\n"
            "  True  → EGR >= 0.85 且 fabricated_count == 0\n"
            "  False → 任一条件不满足，报告必须退回修正"
        )
    )
    fail_reasons: List[str] = Field(
        default_factory=list,
        description="不通过的具体原因列表（用于 Orchestrator 指导修正）"
    )

    # 具体审计发现（仅 critical/major 发现必须列出）
    findings: List[AuditFinding] = Field(
        description="所有 critical 和 major 发现的完整记录"
    )

    # 双轨验证覆盖率
    dual_track_verification_count: int = Field(
        description="经过 Dual-Track 视觉验证的剂量/安全参数数量"
    )
    dual_track_coverage_rate: float = Field(
        description="双轨验证覆盖率 = dual_track_verification_count / 剂量类参数总数"
    )

    # 修正建议（按优先级排序）
    priority_corrections: List[str] = Field(
        default_factory=list,
        description="Orchestrator 修正报告时应优先处理的项目（按 critical → major 排序）"
    )
