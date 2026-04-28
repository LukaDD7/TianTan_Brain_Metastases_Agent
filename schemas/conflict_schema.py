"""
schemas/conflict_schema.py
v7.0 — 冲突分类学 (Conflict Taxonomy) + Agreement Matrix + Debate Protocol

WS-2: Conflict Quantification
WS-6: Structured Debate
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


# ===========================================================
# 关键决策点 (Key Decision Points, KDP) 定义
# ===========================================================

# 标准 5 个 KDP — 系统中所有 SubAgent 均对此表达投票
STANDARD_KDP_IDS = [
    "local_therapy_modality",
    "surgery_indication",
    "systemic_therapy_class",
    "treatment_urgency",
    "molecular_testing_need",
]

KDP_OPTIONS: Dict[str, List[str]] = {
    "local_therapy_modality": [
        "SRS", "fSRT", "WBRT", "HA-WBRT", "Surgery", "Observation", "None"
    ],
    "surgery_indication": [
        "Emergency_Surgery", "Elective_Surgery", "Biopsy_Only", "No_Surgery"
    ],
    "systemic_therapy_class": [
        "Targeted_TKI", "Immunotherapy", "Chemotherapy", "Combined",
        "BSC", "Clinical_Trial", "Not_Applicable"
    ],
    "treatment_urgency": [
        "Emergency_24h", "Urgent_1week", "Semi_Elective_2weeks", "Elective"
    ],
    "molecular_testing_need": [
        "Mandatory_NGS", "Targeted_Panel", "Single_Gene",
        "No_Additional_Testing", "Not_Applicable"
    ],
}

KDP_DESCRIPTIONS: Dict[str, str] = {
    "local_therapy_modality": "脑部局部治疗方式选择 (SRS/fSRT/WBRT/手术/观察)",
    "surgery_indication": "手术指征判断 (急诊/择期/活检/不手术)",
    "systemic_therapy_class": "系统治疗类别 (靶向/免疫/化疗/联合/BSC/临床试验)",
    "treatment_urgency": "治疗紧迫性 (急诊24h/紧急1周/半择期2周/择期)",
    "molecular_testing_need": "分子检测需求 (全套NGS/靶向Panel/单基因/无需)",
}


# ===========================================================
# SubAgent KDP 投票
# ===========================================================

class AgentKDPVote(BaseModel):
    """单个 SubAgent 对某个 KDP 的投票"""
    agent_name: str = Field(description="投票的 SubAgent 名称")
    kdp_id: str = Field(description="决策点 ID，必须在 STANDARD_KDP_IDS 中")
    chosen_option: str = Field(description="该 Agent 选择的选项，必须在 KDP_OPTIONS[kdp_id] 中")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="该 Agent 对此选择的置信度 (0-1)"
    )
    rationale_summary: str = Field(
        description="选择理由，50字以内，必须引用证据等级"
    )
    evidence_level: Literal["Level 1", "Level 2", "Level 3", "Level 4"] = Field(
        description="支持该投票的最高证据等级"
    )


# ===========================================================
# 冲突记录
# ===========================================================

class ConflictRecord(BaseModel):
    """单个冲突记录 — 当 SubAgent 对同一 KDP 有不同选择时触发"""
    conflict_type: Literal[
        "Modality_Conflict",       # 治疗模态分歧 (SRS vs Surgery)
        "Dose_Conflict",           # 剂量方案分歧
        "Sequencing_Conflict",     # 治疗时序分歧 (先放疗 vs 先手术)
        "Urgency_Conflict",        # 紧迫性分歧
        "Evidence_Level_Conflict", # 证据等级分歧 (同modality但来源不同)
    ] = Field(description="冲突类型分类")
    kdp_id: str = Field(description="发生冲突的 KDP 标识")
    conflicting_agents: List[str] = Field(description="持不同意见的 Agent 列表")
    conflicting_options: List[str] = Field(description="各方选择的不同选项")
    resolution_method: Literal[
        "EBM_Arbitration",   # 按证据等级自动裁决
        "Debate",            # 激活 Structured Debate
        "Orchestrator_Override",  # Orchestrator 直接依临床优先级裁决
    ] = Field(description="冲突解决方法")
    resolved_option: str = Field(description="最终采纳的选项")
    resolution_rationale: str = Field(
        description="裁决理由，必须引用具体 EBM Level 和 Clinical Priority Weight"
    )
    resolution_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Orchestrator 对此裁决的置信度"
    )


# ===========================================================
# Agreement Matrix (一致性统计矩阵)
# ===========================================================

class AgreementMatrix(BaseModel):
    """SubAgent 间一致性量化统计 — 由 conflict_calculator.py 计算后填入"""

    kendall_w_approx: float = Field(
        ge=0.0, le=1.0,
        description=(
            "Kendall's W 近似值 (多方总体一致性系数)。"
            "1.0=完全一致，0.0=完全随机分歧。"
            "分类变量场景下用每 KDP 一致率均值近似。"
        )
    )
    pairwise_kappa: Dict[str, float] = Field(
        description=(
            "成对 Agent 间的 Cohen's κ 一致性系数。"
            "key 格式: 'agentA_vs_agentB'，值范围 [-1, 1]，"
            "1.0=完全一致，0=随机水平，<0=系统性分歧。"
        )
    )
    per_kdp_agreement: Dict[str, float] = Field(
        description=(
            "每个 KDP 的一致率 (unanimous votes / total participating agents)。"
            "key 为 kdp_id，值为 [0, 1]。"
        )
    )
    total_agents_participating: int = Field(
        description="参与本次投票的 SubAgent 总数（根据 Triage 路由决定）"
    )
    total_conflicts: int = Field(description="检测到的冲突总数")
    conflict_records: List[ConflictRecord] = Field(
        default_factory=list,
        description="所有冲突的详细记录"
    )
    conflict_heatmap_summary: str = Field(
        default="",
        description=(
            "冲突热力图文字摘要，说明哪些 KDP 冲突频率高，"
            "格式: 'KDP_X: N次冲突 (类型); KDP_Y: M次冲突 (类型)'"
        )
    )


# ===========================================================
# Structured Debate Protocol (WS-6)
# ===========================================================

class DebateResponse(BaseModel):
    """SubAgent 在结构化辩论中的回应"""
    agent_name: str
    kdp_id: str
    debate_round: int = Field(description="辩论轮次 (1 或 2)")
    original_position: str = Field(description="该 Agent 的原始立场 (chosen_option)")
    revised_position: Optional[str] = Field(
        default=None,
        description="若被对方论据说服，修正后的立场；None 表示坚持原立场"
    )
    rebuttal_claims: List[Dict[str, Any]] = Field(
        description=(
            "反驳对方的证据列表，每条格式: "
            "{claim: str, citation: str, evidence_level: str, confidence: float}"
        )
    )
    concession_points: List[str] = Field(
        default_factory=list,
        description="承认对方部分有道理的点，有助于 Orchestrator 做出综合裁决"
    )
    final_confidence: float = Field(
        ge=0.0, le=1.0,
        description="辩论后对自己当前立场的置信度"
    )


class DebateRecord(BaseModel):
    """一次完整辩论过程的记录"""
    kdp_id: str
    trigger_reason: str = Field(description="触发辩论的原因 (复杂度=complex)")
    round_1_responses: List[DebateResponse] = Field(default_factory=list)
    round_2_responses: List[DebateResponse] = Field(default_factory=list)
    final_verdict: str = Field(description="辩论后的最终裁决选项")
    verdict_rationale: str = Field(description="裁决理由")
    verdict_confidence: float = Field(ge=0.0, le=1.0)
