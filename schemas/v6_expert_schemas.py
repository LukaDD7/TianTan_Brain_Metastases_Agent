"""
schemas/v6_expert_schemas.py
v6.0 — 分层架构专家 SubAgent 结构化输出 Schema

定义了六个核心专家的输出模型，用于 Orchestrator 的冲突裁决逻辑。
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ===========================================================
# 通用基础类型
# ===========================================================

class CitedClaim(BaseModel):
    """一条带物理引用且具备支撑一致性校验的临床声明"""
    claim: str = Field(description="具体的临床陈述")
    citation: str = Field(description="物理溯源引用格式 [Local/PubMed/OncoKB]")
    source_core_summary: str = Field(description="文献/指南中的原话摘要或核心结论，用于Auditor进行支撑性校验")
    evidence_level: Literal["Level 1", "Level 2", "Level 3", "Level 4"] = Field(description="循证医学等级：1(RCT), 2(队列), 3(病例对照), 4(专家共识/指南)")


# ===========================================================
# 1. Imaging-Specialist (神经影像专家)
# ===========================================================

class ImagingOutput(BaseModel):
    """神经影像专家输出"""
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
    
    # 本地排除逻辑 (Fallback)
    local_rejected_alternatives: List[str] = Field(description="在影像判定过程中排除的疑似诊断或测量误差考虑")


# ===========================================================
# 2. Primary-Oncology-Specialist (原发系统治疗专家)
# ===========================================================

class PrimaryOncologyOutput(BaseModel):
    """原发系统治疗专家输出"""
    primary_tumor_type: str
    histology: Optional[str]
    systemic_control_status: Literal["controlled", "stable", "progressive", "unknown"]
    kps_score: int
    has_targetable_mutation: bool
    cns_penetrance_level: Literal["high", "medium", "low", "none"]
    recommended_systemic_drug: Optional[str]
    treatment_line: int
    oncology_citations: List[CitedClaim]
    
    # 本地排除逻辑
    local_rejected_alternatives: List[str] = Field(description="排除的治疗线判定或其他全身方案及其理由")


# ===========================================================
# 3. Neurosurgery-Specialist (神经外科专家)
# ===========================================================

class NeurosurgeryOutput(BaseModel):
    """神经外科专家输出"""
    surgical_urgency: Literal["emergency", "elective", "not_recommended"]
    surgical_goal: Literal["decompression", "resection", "biopsy", "none"]
    surgical_rationale: List[CitedClaim]
    anesthesia_risk_asa: int
    bleeding_risk_concern: bool
    medication_holding: List[str]
    
    # 本地排除逻辑
    local_rejected_alternatives: List[str] = Field(description="排除的手术入路或不建议手术的理由")


# ===========================================================
# 4. Radiation-Specialist (放疗科专家)
# ===========================================================

class RadiationOutput(BaseModel):
    """放疗科专家输出"""
    is_radioresistant_histology: bool
    radiation_modality: Literal["SRS", "fSRT", "WBRT", "Hippocampal-sparing WBRT", "none"]
    dose_fractionation: str
    dose_dual_track_verified: bool
    radionecrosis_risk_score: float
    radiation_citations: List[CitedClaim] = Field(default_factory=list)
    
    # 本地排除逻辑
    local_rejected_alternatives: List[str] = Field(description="排除的放疗技术（如为何不选WBRT）及其理由")


# ===========================================================
# 5. Molecular-Pathology-Specialist (分子病理专家)
# ===========================================================

class MolecularOutput(BaseModel):
    """分子病理专家输出"""
    oncokb_evidence_level: Optional[str]
    variant_details: List[str]
    further_testing_required: bool
    testing_priority: str
    molecular_citations: List[CitedClaim] = Field(default_factory=list)
    
    # 本地排除逻辑
    local_rejected_alternatives: List[str] = Field(description="排除的突变意义解读或不推荐的检测")


# ===========================================================
# 6. Evidence-Auditor (证据审计)
# ===========================================================

class AuditFinding(BaseModel):
    """审计发现"""
    claim: str
    citation: str
    
    # 物理溯源审计
    physical_traceability: bool = Field(description="该引用在物理上是否存在？")
    
    # 支撑一致性审计 (Support Consistency)
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

