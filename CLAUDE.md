# TianTan Brain Metastases MDT Agent — AI 协作与开发协议

> **版本**: v7.1  
> **更新**: 2026-04-28  
> **宣言**: *"We build an intellectual Agent, not an LLM with skills."*

本项目致力于打造具备**自适应路由、统计冲突量化、形式化安全保障、自进化能力**的医疗多智能体系统，面向 Nature Medicine 等顶级期刊。

---

## 1. 架构总览 (v7.1 Adaptive MDT Architecture)

```
用户输入（病历/影像报告）
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Triage Gate (分诊门)  ←── WS-1 新增                        │
│  输出: complexity(simple/moderate/complex) + required_SAs   │
└───────────────────────┬─────────────────────────────────────┘
                        │ Dynamic Routing
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     [3 SA subset] [5 SA subset] [All 5 SA + Debate]
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1.5: Cross-Agent Validator + Conflict Calculator     │
│  → Cohen's κ (pairwise) + Kendall's W (overall)            │
└───────────────────────┬─────────────────────────────────────┘
                        │ if conflicts && complex
                        ▼
              [Structured Debate ←── WS-6]
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Evidence Auditor (三重审计: 物理/一致/EBM等级)               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  submit_mdt_report: 三重关卡                                 │
│  Gate 1: Audit marker   Gate 2: Structure   Gate 3: Safety  │
│          (EGR≥0.85)     (9 Modules)         (15 Invariants) │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. SubAgent 完整矩阵 (v7.1: 1+7 体系)

| # | Agent | 名称 | 标准输出 Schema | 核心职责 |
|:--|:------|:-----|:----------------|:---------|
| 0 | **triage-gate** | 分诊门 | `TriageOutput` | 病例复杂度分级 + SA 动态路由 |
| 1 | **imaging-specialist** | 神经影像专家 | `ImagingOutput` | 客观几何参数提取（病灶数/大小/中线移位）|
| 2 | **primary-oncology-specialist** | 原发系统专家 | `PrimaryOncologyOutput` | 原发灶状态 + CNS 穿透率 + 治疗线 |
| 3 | **neurosurgery-specialist** | 神经外科专家 | `NeurosurgeryOutput` | 手术指征 + 围手术期风险 |
| 4 | **radiation-oncology-specialist** | 放疗科专家 | `RadiationOutput` | SRS/WBRT 方案 + 双轨剂量验证 |
| 5 | **molecular-pathology-specialist** | 分子病理专家 | `MolecularOutput` | OncoKB 证据解读 + 检测建议 |
| 6 | **evidence-auditor** | 证据审计专家 | `AuditorOutput` | 三重审计 (物理/支撑一致/EBM等级) |

> Triage Gate 始终被 Orchestrator 首先调用。其余 SA 仅在 `required_subagents` 列表中时被激活。

---

## 3. v7.1 核心创新点 (论文贡献点)

### 3.1 WS-1: 自适应复杂度路由 (Triage Gate)
- **文件**: `agents/triage_prompt.py`, `schemas/triage_schema.py`
- **机制**: 5维特征分析（病灶数/中线移位/原发知否/治疗线/急症标志）→ simple/moderate/complex 三级路由
- **价值**: 避免 simple 病例过度激活 SA（节约 token/时间），complex 病例激活 Debate

### 3.2 WS-2: 统计冲突量化 (Conflict Quantification)
- **文件**: `schemas/conflict_schema.py`, `tools/conflict_calculator.py`
- **机制**: 每个 SA 对 5 个标准 KDP (Key Decision Points) 投票 → 计算 Cohen's κ (成对) + Kendall's W (整体)
- **价值**: 冲突不再是"有/无"二元，而是统计量化的连续值，可作为论文核心指标

### 3.3 WS-3: LLM-as-Judge 评估管线
- **文件**: `evaluation/llm_as_judge.py`
- **机制**: 8维度40分制 Rubric（D1指南遵循~D8内部一致性），支持多模型聚合
- **价值**: 提供自动化评估信号，驱动 R1-R3 进化迭代

### 3.4 WS-4: 不确定性量化 (Uncertainty Quantification)
- **文件**: `schemas/v6_expert_schemas.py` (CitedClaim 扩展)
- **机制**: `CitedClaim.confidence` (0-1) + `uncertainty_type` (epistemic/aleatoric) + 决策级 `decision_confidence`
- **价值**: 实现声明级不确定性的精细化表达

### 3.5 WS-5: 形式化安全不变量 (Safety Invariants)
- **文件**: `core/safety_invariants.py`
- **机制**: 15条规则（6 Critical / 4 Major / 5 Minor），Critical 一票否决提交
- **关键规则**: SI-001 (KRAS+抗EGFR), SI-002 (SRS≤24Gy), SI-006 (T790M→奥希替尼)

### 3.6 WS-6: 结构化辩论协议 (Structured Debate)
- **文件**: `schemas/conflict_schema.py` (DebateRecord/DebateResponse)
- **机制**: complex 病例触发最多 2 轮 Round-Robin 辩论，持反对意见的 SA 互发 rebuttal
- **价值**: 透明化冲突解决过程，可追溯

### 3.7 WS-7: 三要素自进化引擎 (Self-Evolution)
- **文件**: `core/arbitration_weights.py`, `core/experience_library.py`
- **机制三要素**:
  1. **Prompt Refinement** — 基于 R0 失败 Case 分析，修改 SA prompt 文件
  2. **Experience Library** — JSONL 存储历史 Case，检索相似经验注入 Orchestrator context
  3. **Arbitration Weight Tuning** — JSON 配置可进化仲裁权重，开发者通过 `adjust_weight()` 微调
- **进化不需要模型微调**: qwen3.6-plus 始终 API 调用，进化改变 prompt/context/规则参数

---

## 4. 关键文件索引

### 4.1 必须了解的文件（修改前必读）
| 文件 | 角色 | 修改风险 |
|:-----|:-----|:-------:|
| `interactive_main.py` | 全局入口，SA注册，三重关卡，工具调用上限，流式输出 | 🔴 极高 |
| `agents/orchestrator_prompt.py` | 5阶段工作流协议 | 🔴 极高 |
| `utils/llm_factory.py` | Orchestrator/SubAgent 独立 LLM 客户端工厂（thinking 模式分离） | 🟡 中 |
| `core/safety_invariants.py` | 15条临床安全规则 | 🟡 中 |
| `schemas/v6_expert_schemas.py` | 所有 SA 输出 Schema | 🟡 中 |
| `config.py` | API Key / 阈值常量 | 🟢 低 |

### 4.2 v7.0/v7.1 新增文件（可独立修改）
```
schemas/
  triage_schema.py          # Triage Gate 输出 Schema
  conflict_schema.py        # KDP投票/冲突记录/辩论协议
  debate_schema.py          # 辩论Schema导出

agents/
  triage_prompt.py          # 分诊门 System Prompt

core/
  safety_invariants.py      # 15条安全不变量
  arbitration_weights.py    # 可进化仲裁权重
  experience_library.py     # JSONL经验库存取
  episodic_memory.py        # SQLite FTS5跨会话记忆

tools/
  conflict_calculator.py    # Cohen's κ + Kendall's W计算
  cross_agent_validator.py  # 5条横向一致性检查

utils/
  llm_factory.py            # Orchestrator/SubAgent 独立 LLM 客户端工厂（v7.1 新增）

evaluation/
  llm_as_judge.py           # 8维度LLM-as-Judge管线

scripts/
  setup_workspace.py        # 部署一键初始化

docs/
  V7_Implementation_Plan.md       # 技术实施方案 (v1.1)
  V7_Test_Plan_and_Config_Guide.md # 测试规划书 + 配置说明
  TiantanBM_Gap_Analysis.md       # 科研范式 Gap 分析
```

---

## 5. 协作铁律 (The Iron Laws)

### 5.1 临床安全铁律
1. **Safety First**: `run_safety_check()` 是 `submit_mdt_report` 的第三道关卡，任何 Critical 违规一票否决
2. **引用零容忍**: 严禁伪造引用。EGR (Evidence Grounding Rate) 阈值 = 0.85
3. **双轨验证**: 剂量相关声明（Gy 值）必须文本 + 视觉双轨验证（`dose_dual_track_verified=True`）

### 5.2 开发协作铁律
4. **版本锁定**: `interactive_main.py` 和 `orchestrator_prompt.py` 修改前必须创建 git tag
5. **安全推送**: Push 前核查 `.env`、`config.py` 确保 API Key 未硬编码
6. **单轮单机制**: 每个进化轮次（R1/R2/R3）只新增一个进化机制（增量消融设计）
7. **权重阻尼**: `adjust_weight()` 每次调整 ≤ 5%，防止单 Case 导致过拟合
8. **后台禁止**: 禁止在后台静默运行 `interactive_main.py`
9. **工具调用上限**: `MAX_TOOL_CALLS_PER_RUN = 200`，每个 Case 最多 200 次 execute 调用，防止异常循环烧光预算
10. **流式输出**: 使用 `agent.stream()` 而非 `agent.invoke()`，确保终端实时可见 SubAgent 委派和工具调用状态

---

## 6. 数据与评估

### 6.1 数据资产
- **训练集**: 56 Cases（Set1: 10例 + Set2: 46例）
- **多中心数据**: 接入中（待定）
- **进化轮次**: R0（基线）→ R1（Prompt）→ R2（Experience）→ R3（Weight）

### 6.2 评估指标体系
| 指标 | 类型 | 含义 |
|:-----|:----:|:-----|
| **EGR** | 自动 | Evidence Grounding Rate（引用覆盖率）|
| **SCR** | 自动 | Support Consistency Rate（引用一致性）|
| **ESR** | Judge | Expert Scoring Rate（8维度LLM评分，/40）|
| **CCR** | 自动 | Clinical Correctness Rate（安全不变量通过率）|
| **PTR** | 自动 | Protocol Adherence Rate（指南遵循率）|
| **Kendall's W** | 自动 | 多专家整体一致性系数 |
| **Cohen's κ** | 自动 | 成对专家一致性系数 |

---

## 7. 运行环境

```bash
# 环境激活
conda activate tiantanBM_agent

# 首次部署（服务器端）
python3 scripts/setup_workspace.py

# 单 Case 测试
python3 scripts/run_batch_eval.py --max_cases 1

# 批量基线（R0）
python3 scripts/run_batch_eval.py --max_cases 56 --output_dir workspace/analysis_output/R0/ --evolution_round R0

# LLM-as-Judge 评估
python3 evaluation/llm_as_judge.py --report path/to/report.md --case-id CASE-001 --round R0

# 进化信号提取
python3 evaluation/llm_as_judge.py --signals --round R0

# 主交互入口
python3 interactive_main.py
```

### 7.1 必需环境变量
```bash
DASHSCOPE_API_KEY   # Qwen3.6-plus 推理
ONCOKB_API_KEY      # OncoKB 分子证据
PUBMED_EMAIL        # PubMed 文献检索
```

### 7.2 可选环境变量
```bash
NCBI_API_KEY        # PubMed 速率提升
JUDGE_API_KEY       # Secondary LLM-as-Judge (optional)
JUDGE_BASE_URL      # Secondary Judge API 地址
JUDGE_MODEL         # Secondary Judge 模型名
```

---

## 8. 进化调整 SOP (Standard Operating Procedure)

```
R0 完成 → 分析失败 Case:
  1. python3 evaluation/llm_as_judge.py --signals --round R0
  2. 识别最弱 3 个维度 → 定位对应 SA prompt
  3. 修改 SA prompt → git tag v7.0-R1-[sa]-prompt → run R1

R1 完成 → 填充经验库:
  1. 将 R0+R1 高质量 Case (ESR≥30) 写入 experience_library.jsonl
  2. 在 run_batch_eval.py 中启用 experience 注入 → run R2

R2 完成 → 权重调整:
  1. 对比专家标注 vs 系统裁决，找系统性偏差
  2. from core.arbitration_weights import adjust_weight
  3. adjust_weight(factor_path=..., direction=..., case_id=..., reason=...)
  4. 验证 5 个历史 Case → run R3
```
