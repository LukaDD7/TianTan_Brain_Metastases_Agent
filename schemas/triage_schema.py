"""
schemas/triage_schema.py
v7.0 — Triage Gate 输出 Schema

WS-1: Adaptive Complexity Routing
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class TriageOutput(BaseModel):
    """分诊门输出：决定病例复杂度和需要召集的 SubAgent 矩阵"""

    complexity_level: Literal["simple", "moderate", "complex"] = Field(
        description=(
            "simple: 单发≤3cm病灶 + 已知原发灶 + 明确靶点 + 初治/一线 → 召集3个核心SA; "
            "moderate: 2-4个病灶 OR 二线治疗 OR 靶点不明 → 召集5个SA; "
            "complex: ≥5病灶 OR 中线移位 OR 原发不明 OR 三线失败 OR KPS≤50 → 全部6个SA + 激活Debate"
        )
    )

    required_subagents: List[Literal[
        "imaging-specialist",
        "primary-oncology-specialist",
        "neurosurgery-specialist",
        "radiation-oncology-specialist",
        "molecular-pathology-specialist",
    ]] = Field(
        description=(
            "本次需要召集的专科 SubAgent 列表（不含 evidence-auditor，该角色由 Orchestrator 固定调用）。"
            "simple 时最少3个，complex 时全部5个。"
        )
    )

    activate_debate: bool = Field(
        default=False,
        description="仅 complexity_level='complex' 时为 True，激活 Orchestrator 的 Structured Debate 协议"
    )

    triage_rationale: str = Field(
        description="分诊理由，100字以内，说明为何判定该复杂度等级"
    )

    # 关键临床特征提取（供 Orchestrator 快速上下文决策，避免重复解析）
    estimated_lesion_count: int = Field(
        ge=0,
        description="从主诉/现病史/影像描述中估计的脑转移病灶数量，无法确定时写 -1"
    )
    midline_shift_suspected: bool = Field(
        description="是否怀疑中线移位（从症状描述或影像报告推断）"
    )
    primary_known: bool = Field(
        description="原发灶是否已知（True=已知原发如肺/乳腺等；False=原发不明/待查）"
    )
    estimated_treatment_line: int = Field(
        ge=0,
        description="估计当前治疗线数（0=初治，1=一线，2=二线…，无法判断时写 -1）"
    )
    emergency_flag: bool = Field(
        description=(
            "是否存在急诊信号：True 表示有脑疝风险/急性颅高压/意识障碍等，"
            "Orchestrator 接收后需立即优先委派 neurosurgery-specialist"
        )
    )
    cancer_type_hint: str = Field(
        default="",
        description="原发灶类型的初步判断（如 'NSCLC', 'Breast', 'Unknown'），便于后续 SA 快速定位指南"
    )
