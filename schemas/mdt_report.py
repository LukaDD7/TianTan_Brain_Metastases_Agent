from typing import List, Optional
from pydantic import BaseModel, Field

# ==========================================
# 基础结构：强制包含引用和证据的信息对象
# ==========================================

class ClinicalClaim(BaseModel):
    """一个包含证据支持的临床声明"""
    claim_text: str = Field(description="具体的临床陈述或建议")
    citation_source: str = Field(description="必须符合特定格式，如 [Local: <FILE>.md, Line X] 或 [PubMed: PMID XXX]")
    evidence_level: Optional[str] = Field(description="如 Level 1A, Level 3B 等")
    dual_track_verified: bool = Field(default=False, description="是否已经过文本+视觉的双轨验证（针对剂量、安全阈值等高危参数）")

class ClinicalIntervention(BaseModel):
    """具体的医疗干预（手术、放疗、药物）"""
    intervention_type: str = Field(description="如 SRS, Surgery, Targeted Therapy")
    details: str = Field(description="剂量、频次、周期等核心参数")
    rationale: List[ClinicalClaim] = Field(description="推荐理由和证据树")

# ==========================================
# Module 1: 入院评估
# ==========================================

class BiomarkerStatus(BaseModel):
    marker: str = Field(description="标志物名称，如 EGFR, KRAS, PD-L1")
    status: str = Field(description="状态，如 Positive, 19del, Unknown")
    source: str = Field(description="信息来源（如: 组织NGS, 患者病历）")

class AdmissionEvaluation(BaseModel):
    patient_age: int
    patient_sex: str
    kps_score: str = Field(description="KPS评分或预估范围")
    primary_tumor_type: str
    primary_stage: str
    brain_mets_characteristics: str = Field(description="病灶数量、最大径、位置等")
    extracranial_status: str
    prior_treatments: List[str] = Field(description="既往关键治疗史，标明线数")
    current_disease_state: str = Field(description="主要判定当前是否为疾病进展(PD)、稳定(SD)等")
    missing_critical_data: List[str] = Field(description="影响决策缺失的基线数据")

# ==========================================
# Module 2: 个体化治疗方案
# ==========================================

class PrimaryPersonalizedPlan(BaseModel):
    treatment_line: str = Field(description="当前决策处于第几线治疗")
    primary_recommendations: List[ClinicalIntervention] = Field(description="首选或联合治疗方案")
    alternative_plans: List[ClinicalIntervention] = Field(description="备选治疗方案，包含触发条件")
    treatment_sequencing: str = Field(description="建议的治疗先后顺序（如: 紧急脱水 -> SRS -> 基因检测结果 -> 靶向用药）")

# ==========================================
# Module 3: 支持治疗
# ==========================================

class SupportiveCare(BaseModel):
    edema_management: Optional[ClinicalIntervention] = Field(description="脑水肿管理，地塞米松指征与剂量")
    seizure_management: Optional[ClinicalIntervention] = Field(description="抗癫痫用药建议")
    nutritional_support: Optional[ClinicalIntervention]
    other_support: List[ClinicalIntervention]

# ==========================================
# Module 4: 随访与监测
# ==========================================

class FollowupMonitoring(BaseModel):
    imaging_schedule: str = Field(description="影像随访频率与类型")
    evaluation_criteria: List[str] = Field(description="如 RANO-BM, RECIST 1.1")
    toxicity_monitoring: List[str] = Field(description="需要特别关注的药物毒性或并发症")

# ==========================================
# Module 5: 被排除方案
# ==========================================

class RejectedAlternative(BaseModel):
    rejected_plan: str = Field(description="被拒绝的干预手段，如 WBRT, 继续原方案等")
    rejection_reasons: List[ClinicalClaim] = Field(description="拒绝的明确证据或临床推理")

class RejectedAlternatives(BaseModel):
    rejected_interventions: List[RejectedAlternative]

# ==========================================
# Module 6: 围手术期/放疗期管理
# ==========================================

class PerioperativeManagement(BaseModel):
    anti_angiogenic_holding: Optional[ClinicalIntervention] = Field(description="贝伐珠单抗等停药窗口")
    tki_chemo_holding: Optional[ClinicalIntervention] = Field(description="靶向或化疗停药窗口")
    corticosteroid_tapering: Optional[ClinicalIntervention] = Field(description="围手术放疗期激素梯度缩减策略")

# ==========================================
# Module 7: 分子病理学检测建议
# ==========================================

class PathologyOrder(BaseModel):
    test_target: str = Field(description="如 EGFR T790M, MSI")
    sample_type: str = Field(description="如 ctDNA, Tissue")
    urgency: str = Field(description="Emergency, Routine, Exploratory")
    rationale: ClinicalClaim

class MolecularPathologyOrders(BaseModel):
    completed_tests: List[BiomarkerStatus]
    recommended_orders: List[PathologyOrder]

# ==========================================
# Module 8: 智能体执行轨迹
# ==========================================

class TrajectoryLog(BaseModel):
    guideline_searches: List[str] = Field(description="执行的指南 grep 或查看命令/关键字")
    pubmed_queries: List[str] = Field(description="执行的 PubMed 检索式及相关 PMID")
    oncokb_queries: List[str] = Field(description="执行的 OncoKB 搜索记录")

class AgentExecutionTrajectory(BaseModel):
    search_trajectory: TrajectoryLog
    key_decision_points: List[str] = Field(description="列出决定最终导向的关键分叉路径")

# ==========================================
# 全局报告结构 (MDTReport)
# ==========================================

class ExecutiveSummary(BaseModel):
    brief_patient_profile: str
    core_decision_summary: str = Field(description="不超过3句话的结论性高管摘要")
    consensus_status: str = Field(description="各专科达成的一致状态或冲突解决结果")

class MDTReport(BaseModel):
    """MDT 报告输出的终极强制结构，保证格式 100% 统一，且便于 Auditor 核发"""
    
    # 头部元数据
    patient_id: str
    admission_date: str
    report_date: str
    mdt_type: str = Field(description="如: 肺癌脑转移初诊、结直肠癌多线失败、乳腺癌脑转移等")
    
    # 核心执行模块
    executive_summary: ExecutiveSummary
    module_1_admission: AdmissionEvaluation
    module_2_treatment_plan: PrimaryPersonalizedPlan
    module_3_supportive_care: SupportiveCare
    module_4_followup: FollowupMonitoring
    module_5_rejected: RejectedAlternatives
    module_6_perioperative: PerioperativeManagement
    module_7_molecular: MolecularPathologyOrders
    module_8_trajectory: AgentExecutionTrajectory
    
    # 尾部元数据
    mdt_members: List[str]
    next_evaluation: str
