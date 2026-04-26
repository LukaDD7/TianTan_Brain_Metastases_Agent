"""
schemas/v6_expert_schemas.py
v7.0 — 分层架构专家 SubAgent 结构化输出 Schema

v7.0 升级:
  - CitedClaim: 新增 confidence (WS-4) 和 uncertainty_type (WS-4)
  - 所有专科 Schema: 新增 kdp_votes (WS-2) 用于冲突量化
  - 所有专科 Schema: 新增 decision_confidence (WS-4) 用于决策级置信度聚合
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


# ===========================================================
# 通用基础类型
# ===========================================================

class CitedClaim(BaseModel):
    """一条带物理引用且具备支撑一致性校验的临床声明 (v7.0 升级)"""
    claim: str = Field(description="具体的临床陈述")
    citation: str = Field(description="物理溯源引用格式 [Local/PubMed/OncoKB]")
    source_core_summary: str = Field(description="文献/指南中的原话摘要或核心结论，用于Auditor进行支撑性校验")
    evidence_level: Literal["Level 1", "Level 2", "Level 3", "Level 4"] = Field(
        description="循证医学等级：1(RCT), 2(队列), 3(病例对照), 4(专家共识/指南)"
    )

    # ─── v7.0 WS-4: 声明级不确定性量化 ─────────────────────────
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description=(
            "对该声明的置信度 (0-1)。计算规则: "
            "Level 1 基础分=0.90, Level 2=0.70, Level 3=0.50, Level 4=0.30; "
            "多源交叉验证 +0.05/每个额外来源(最多+0.10); "
            "双轨视觉验证通过 +0.05; 最终值 clamp 到 [0.05, 1.0]"
        )
    )
    uncertainty_type: Optional[Literal["epistemic", "aleatoric"]] = Field(
        default=None,
        description=(
            "不确定性类型: "
            "epistemic=证据不足导致(可通过更多检索降低); "
            "aleatoric=病例本身歧义性(无法通过更多证据消除, 如原发灶类型本身不确定)"
        )
    )


# ===========================================================
# KDP 投票类型（用于 WS-2 冲突量化）
# ===========================================================

class KDPVote(BaseModel):
    """关键决策点 (KDP) 投票（内嵌在各专科 Schema 中）"""
    kdp_id: str = Field(
        description="KDP 标识，必须是 5 个标准 KDP 之一: "
                    "local_therapy_modality / surgery_indication / "
                    "systemic_therapy_class / treatment_urgency / molecular_testing_need"
    )
    chosen_option: str = Field(
        description="该 Agent 在此 KDP 上的选择，必须是该 KDP 的合法选项之一"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="对此投票的置信度")
    evidence_level: Literal["Level 1", "Level 2", "Level 3", "Level 4"] = Field(
        description="支持此投票的最高证据等级"
    )
    rationale_summary: str = Field(description="选择理由，50字以内")


# ===========================================================
# 1. Imaging-Specialist (神经影像专家)
# ===========================================================

class ImagingOutput(BaseModel):
    """神经影像专家输出 (v7.0)"""
    max_diameter_cm: float
    lesion_count: int
    midline_shift: bool
    mass_effect_level: Literal["none", "mild", "moderate", "severe"]
    hydrocephalus: bool
    is_eloquent_area: bool
    location_details: str
    edema_index: float
    hemorrhage_present: bool
    imaging_citations: List[CitedClaim]
    local_rejected_alternatives: List[str] = Field(
        description="在影像判定过程中排除的疑似诊断或测量误差考虑"
    )

    # ─── v7.0 WS-2: KDP 投票 ─────────────────────────────────
    kdp_votes: List[KDPVote] = Field(
        default_factory=list,
        description=(
            "影像科对各 KDP 的投票。"
            "影像科主要对 local_therapy_modality (病灶大小/数量决定SRS可行性)、"
            "surgery_indication (占位效应程度)、treatment_urgency (急症程度) 有权表达意见。"
            "无法判断的 KDP 不填或 chosen_option='Not_Applicable'。"
        )
    )

    # ─── v7.0 WS-4: 整体决策置信度 ──────────────────────────────
    decision_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="影像评估的整体置信度（影像质量好/清晰可靠时高，模糊或伪影时低）"
    )


# ===========================================================
# 2. Primary-Oncology-Specialist (原发系统治疗专家)
# ===========================================================

class PrimaryOncologyOutput(BaseModel):
    """原发系统治疗专家输出 (v7.0)"""
    primary_tumor_type: str
    histology: Optional[str]
    systemic_control_status: Literal["controlled", "stable", "progressive", "unknown"]
    kps_score: int
    has_targetable_mutation: bool
    cns_penetrance_level: Literal["high", "medium", "low", "none"]
    recommended_systemic_drug: Optional[str]
    treatment_line: int
    oncology_citations: List[CitedClaim]
    local_rejected_alternatives: List[str] = Field(
        description="排除的治疗线判定或其他全身方案及其理由"
    )

    # ─── v7.0 WS-2: KDP 投票 ─────────────────────────────────
    kdp_votes: List[KDPVote] = Field(
        default_factory=list,
        description=(
            "内科对各 KDP 的投票。"
            "内科主要对 systemic_therapy_class、treatment_line、"
            "molecular_testing_need、local_therapy_modality(与系统治疗的协同) 表达意见。"
        )
    )

    # ─── v7.0 WS-4: 整体决策置信度 ──────────────────────────────
    decision_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="系统治疗建议的整体置信度（靶点明确/高级别证据时高，靶点不明/证据稀少时低）"
    )


# ===========================================================
# 3. Neurosurgery-Specialist (神经外科专家)
# ===========================================================

class NeurosurgeryOutput(BaseModel):
    """神经外科专家输出 (v7.0)"""
    surgical_urgency: Literal["emergency", "elective", "not_recommended"]
    surgical_goal: Literal["decompression", "resection", "biopsy", "none"]
    surgical_rationale: List[CitedClaim]
    anesthesia_risk_asa: int
    bleeding_risk_concern: bool
    medication_holding: List[str]
    local_rejected_alternatives: List[str] = Field(
        description="排除的手术入路或不建议手术的理由"
    )

    # ─── v7.0 WS-2: KDP 投票 ─────────────────────────────────
    kdp_votes: List[KDPVote] = Field(
        default_factory=list,
        description=(
            "神外对各 KDP 的投票。"
            "神外主要对 surgery_indication、treatment_urgency、"
            "local_therapy_modality (手术 vs SRS) 表达意见。"
        )
    )

    # ─── v7.0 WS-4: 整体决策置信度 ──────────────────────────────
    decision_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="手术建议的整体置信度（风险评估充分/影像清晰时高，感染风险/功能区不确定时低）"
    )


# ===========================================================
# 4. Radiation-Specialist (放疗科专家)
# ===========================================================

class RadiationOutput(BaseModel):
    """放疗科专家输出 (v7.0)"""
    is_radioresistant_histology: bool
    radiation_modality: Literal["SRS", "fSRT", "WBRT", "Hippocampal-sparing WBRT", "none"]
    dose_fractionation: str
    dose_dual_track_verified: bool
    radionecrosis_risk_score: float
    radiation_citations: List[CitedClaim] = Field(default_factory=list)
    local_rejected_alternatives: List[str] = Field(
        description="排除的放疗技术（如为何不选WBRT）及其理由"
    )

    # ─── v7.0 WS-2: KDP 投票 ─────────────────────────────────
    kdp_votes: List[KDPVote] = Field(
        default_factory=list,
        description=(
            "放疗科对各 KDP 的投票。"
            "放疗科主要对 local_therapy_modality (SRS/fSRT/WBRT 选择)、"
            "treatment_urgency 表达意见。"
        )
    )

    # ─── v7.0 WS-4: 整体决策置信度 ──────────────────────────────
    decision_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="放疗方案置信度（剂量经双轨验证时+0.05，放射敏感性不确定时低）"
    )


# ===========================================================
# 5. Molecular-Pathology-Specialist (分子病理专家)
# ===========================================================

class MolecularOutput(BaseModel):
    """分子病理专家输出 (v7.0)"""
    oncokb_evidence_level: Optional[str]
    variant_details: List[str]
    further_testing_required: bool
    testing_priority: str
    molecular_citations: List[CitedClaim] = Field(default_factory=list)
    local_rejected_alternatives: List[str] = Field(
        description="排除的突变意义解读或不推荐的检测"
    )

    # ─── v7.0 WS-2: KDP 投票 ─────────────────────────────────
    kdp_votes: List[KDPVote] = Field(
        default_factory=list,
        description=(
            "分子病理对各 KDP 的投票。"
            "分子病理主要对 molecular_testing_need、systemic_therapy_class "
            "(靶点是否支持特定类别) 表达意见。"
        )
    )

    # ─── v7.0 WS-4: 整体决策置信度 ──────────────────────────────
    decision_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="分子解读置信度（OncoKB Level 1/2时高，VUS或未检测时低）"
    )


# ===========================================================
# 6. Evidence-Auditor (证据审计)
# ===========================================================

class AuditFinding(BaseModel):
    """审计发现"""
    claim: str
    citation: str
    physical_traceability: bool = Field(description="该引用在物理上是否存在？")
    support_consistency: bool = Field(description="文献内容是否真实支撑了Agent的陈述？")
    ebm_level_correctness: bool = Field(description="Agent标注的证据等级是否准确？")
    audit_comments: str = Field(description="具体的审计意见，若不通过需说明理由")


class AuditorOutput(BaseModel):
    """审计专家输出"""
    evidence_grounding_rate: float
    support_consistency_rate: float = Field(description="支撑一致性比率")
    audit_findings: List[AuditFinding]
    pass_threshold: bool
    revision_suggestions: str

