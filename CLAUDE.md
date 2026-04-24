# TianTan Brain Metastases Agent - AI 协作与开发协议 (v6.0 Hierarchical)

## 1. 核心宣言 (Manifesto)
**"We build intellectual Agent, not LLM with skill."**
本项目致力于打造具备高度自主规划能力与临床循证逻辑的医疗多智能体系统。

## 2. 架构定义 (v6.0 Dispatcher-Arbitrator Architecture)

### 2.1 角色分工 (Sub-agent Matrix)
系统采用 **1 主席 + 6 专家** 的分层架构，各专家通过 Pydantic Schema 实现物理航道隔离：

1.  **MDT Orchestrator (主席/调度员)**:
    - 职责：剥夺临床执行权，仅负责任务分发、证据等级仲裁及报告合成。
    - 仲裁逻辑：`Selection_Priority = (EBM_Level_Score) * (Clinical_Priority_Weight)`。
2.  **Imaging-Specialist (影像专家)**:
    - 职责：参数化提取病灶大小、数量、中线移位、功能区受累等客观几何数据。
3.  **Primary-Oncology-Specialist (原发系统专家)**:
    - 职责：判定原发癌种，评估全身控制状态及药物 CNS 穿透性 (CNS Penetrance)。
4.  **Neurosurgery-Specialist (神外专家)**:
    - 职责：仅评估手术指征及围手术期风险。
5.  **Radiation-Specialist (放疗专家)**:
    - 职责：制定 SRS/WBRT 方案，必须执行双轨验证。
6.  **Molecular-Pathology-Specialist (病理专家)**:
    - 职责：解读突变，对接 OncoKB 实时证据等级。
7.  **Evidence-Auditor (证据审计专家)**:
    - 职责：三重审计（物理存在、支撑一致性、EBM等级校准）。

### 2.2 核心协议 (Core Protocols)
- **零执行协议 (Zero-execution Policy)**: Orchestrator 严禁直接给出临床建议。
- **证据主权协议 (Evidence Sovereignty)**: 所有临床声明必须包含 `claim`, `citation`, `source_core_summary`, `evidence_level`。
- **自进化机制**: 系统通过 `StoreBackend` 记录高等级证据修正低等级建议的先例，实现知识闭环。

---

## 3. 协作铁律 (The Iron Laws)
1. **严禁无头执行**: 禁止在后台运行 `interactive_main.py`。
2. **引用零容忍**: 严禁伪造。Auditor 拥有一票否决权。
3. **安全推送**: Push 前必须核查 `.env` 和敏感路径。

## 4. 运行环境 (v6.0)
- **环境名称**: `tiantanBM_agent`
- **主入口**: `interactive_main.py`
- **Schema 定义**: `schemas/v6_expert_schemas.py`
