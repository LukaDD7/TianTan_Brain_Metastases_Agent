# Changelog

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [v7.1.0] - 2026-04-28

### 关键 Bug 修复 (Critical Bug Fixes)

#### Fix 1: 路径双重替换导致 738 次无限循环
- **问题**: `_resolve_virtual_path` 用简单 `replace('/skills/', SKILLS_DIR)` 做路径转换，当 Agent 使用 SKILL.md 中的完整绝对路径（如 `/media/.../skills/...`）时，`/skills/` 子串被错误替换成 `SKILLS_DIR/`（即 `/media/.../skills/`），导致路径再加倍一层。Agent 拿到错误结果后重试，继续用错误路径，形成 **738 次 `ls -la` 循环**，烧掉大量 Token。
- **根因**: `interactive_main.py:451-452` 的 `replace()` 是子串匹配，不区分路径开头还是中间片段
- **修复**: 用正则 `r'(?:^|(?<= ))(/skills/)'` 只替换**命令参数开头**的虚拟路径前缀，不替换已是完整绝对路径里的 `/skills/` 片段
- **影响**: 消除路径加倍导致的无限循环

#### Fix 2: SubAgent 400 错误（enable_thinking 与 structured output 冲突）
- **问题**: SubAgent 调用时返回 400 错误 `"tool_choice parameter does not support being set to required or object in thinking mode"`
- **根因**: DashScope API `enable_thinking=True` 模式与 `tool_choice=required`（由 `response_format` schema 触发）互斥
- **修复**: 创建独立 `get_subagent_client_langchain()` 工厂函数，SubAgent 显式设置 `extra_body={"enable_thinking": False}`；Orchestrator 保持 `enable_thinking=True`
- **涉及文件**:
  - `utils/llm_factory.py` — 新增 `get_subagent_client_langchain()`
  - `interactive_main.py` — SubAgent 模型改用 `_subagent_model = get_subagent_client_langchain()`

#### Fix 3: 实时流式输出（解决 invoke 阻塞问题）
- **问题**: `agent.invoke()` 是阻塞调用，运行完才返回结果，用户在终端看不到任何中间输出，出现异常只能等结束才发现
- **修复**: 改用 `agent.stream()` + `stream_mode=["updates", "messages"]`
  - `"messages"` — LLM token 级流式输出（实时显示推理过程）
  - `"updates"` — 每个 step 的节点更新（委派、工具调用、返回结果）
- **LangGraph BSP 保证**: LangGraph 的 Bulk Synchronous Parallel 模型确保 `stream()` 在每个 superstep 所有任务完成前不会交还控制权，不破坏 Orchestrator→SubAgent 协调
- **额外修复**: `node_data.get("messages", [])` 可能返回 `Overwrite` 对象（非 list），添加 `isinstance(messages_in_node, list)` 检查

#### Fix 4: 工具调用次数上限（防预算烧光）
- **新增**: `MAX_TOOL_CALLS_PER_RUN = 200`（每 Case 最多 200 次 execute 调用）
- **实现**: `execute` 工具每次调用前计数，超过上限直接返回错误；每个新 Case 开始时计数器重置为 0
- **输出**: 运行结束后打印 `📊 工具调用统计: X / 200 次`

---

## [v7.0.0] - 2026-04-26

### 架构里程碑：科研级自适应 MDT 系统 (Research-Grade Adaptive MDT)

> 本次升级是为达到 Nature Medicine 等顶级期刊发表标准而进行的全面架构升级，
> 核心创新点为：自适应路由 + 统计冲突量化 + 形式化安全保障 + 三要素自进化引擎。

#### WS-1: 自适应复杂度路由 (Triage Gate)

**新增文件**:
- `agents/triage_prompt.py` — 分诊门 System Prompt（5段路由规则）
- `schemas/triage_schema.py` — TriageOutput Schema（复杂度分级 + 7个临床特征字段）

**核心变更**:
- Orchestrator 工作流新增 **Phase 0 (Triage)**，强制第一步
- `required_subagents` 字段动态决定本次召集哪些 SA：
  - `simple`（单发/已知靶点/一线）→ 3 个核心 SA
  - `moderate`（2-4个病灶/二线/靶点不明）→ 5 个专科 SA
  - `complex`（≥5病灶/中线移位/原发不明/三线以上）→ 全部 5 个 SA + 激活 Debate
- `emergency_flag=True` 时触发 Phase Emergency，立即优先委派神外 SA

#### WS-2: 统计冲突量化 (Conflict Quantification)

**新增文件**:
- `schemas/conflict_schema.py` — KDP 投票 Schema、AgreementMatrix、ConflictRecord、冲突分类学
- `tools/conflict_calculator.py` — Cohen's κ（成对）+ Kendall's W（近似）命令行计算工具

**核心变更**:
- `schemas/v6_expert_schemas.py`：所有 5 个专科 SA Schema 新增 `kdp_votes: List[KDPVote]` 字段
- Orchestrator Phase 1.5：收集各 SA 的 KDP 投票 → 写入 `votes_{patient_id}.json` → 调用 `conflict_calculator.py`
- 5 个标准 KDP：`local_therapy_modality`, `surgery_indication`, `systemic_therapy_class`, `treatment_urgency`, `molecular_testing_need`
- 冲突量化结果（κ/W/冲突记录）强制写入报告 Module 5

#### WS-3: LLM-as-Judge 评估管线

**新增文件**:
- `evaluation/llm_as_judge.py` — 8维度40分制评估管线，支持多模型聚合

**评估维度**:
- D1: 指南遵循性 | D2: 证据完整性 | D3: 临床安全性 | D4: 冲突处理
- D5: 不确定性披露 | D6: 个体化程度 | D7: 可操作性 | D8: 内部一致性

**核心功能**:
- `run_multi_judge_evaluation()` — 主评估入口，Primary + Optional Secondary
- `aggregate_judge_scores()` — 多模型均值聚合，标准差 > 1.5 标记 `high_disagreement`
- `generate_evolution_signals()` — 从批量结果提取 Prompt Refinement 目标
- CLI: `python3 evaluation/llm_as_judge.py --report report.md --case-id X --round R0`

#### WS-4: 声明级不确定性量化 (Uncertainty Quantification)

**核心变更** (`schemas/v6_expert_schemas.py`):
- `CitedClaim` 新增:
  - `confidence: float` — 声明置信度 [0,1]，基于 EBM Level 基础分 + 多源验证奖励
  - `uncertainty_type: Optional[Literal["epistemic", "aleatoric"]]` — 不确定性类型分类
- 所有专科 SA Schema 新增:
  - `decision_confidence: float` — 决策级整体置信度
- Orchestrator Phase 3 新增置信度聚合逻辑（high/moderate/low/insufficient_evidence）

#### WS-5: 15条形式化安全不变量 (Safety Invariants)

**新增文件**:
- `core/safety_invariants.py` — 15条规则（6 Critical / 4 Major / 5 Minor）

**关键规则**:
- `SI-001`: KRAS 突变禁用抗 EGFR 单抗 [OncoKB R1]
- `SI-002`: SRS 单次剂量上限 24 Gy [RTOG 90-05]
- `SI-003`: WBRT 总剂量上限 40 Gy [NCCN CNS 2026 v2]
- `SI-006`: EGFR T790M 阳性禁用一/二代 EGFR TKI [OncoKB Level 1]
- 共 6 条 Critical（一票否决提交）、4 条 Major（警告）、5 条 Minor（提示）

**集成变更** (`interactive_main.py`):
- `submit_mdt_report` 新增 **Gate 3: Safety Invariants Check**
- Critical 违规触发 `SUBMISSION BLOCKED (Safety Invariants)` 并给出 remediation 引导
- 每份提交报告同步生成 `*_safety_audit.json` 审计日志

#### WS-6: 结构化辩论协议 (Structured Debate Protocol)

**新增文件**:
- `schemas/debate_schema.py` — DebateResponse + DebateRecord（从 conflict_schema 导出）

**核心变更** (`schemas/conflict_schema.py`):
- `DebateResponse` — 单 SA 辩论回应（revised_position / rebuttal_claims / concession_points）
- `DebateRecord` — 完整辩论过程记录（最多2轮，必须收敛裁决）

**触发条件**: `complexity=complex` AND `total_conflicts > 0`

**协议**:
- Round 1: 冲突双方互传对方立场，要求用最强证据支持或修正
- Round 1 后若一方被说服（`revised_position != null`）直接收敛
- Round 2（最后一轮）: 必须依 `Selection_Priority = EBM × Priority` 公式做最终裁决
- 辩论记录写入 Module 5 `debate_log` 字段

#### WS-7: 三要素自进化引擎 (Self-Evolution Engine)

**新增文件**:
- `core/arbitration_weights.py` — 可进化仲裁权重（JSON 持久化 + 阻尼微调）
- `core/experience_library.py` — JSONL 经验库（存储/多维检索/Context 注入格式化）

**三要素进化机制**（均不涉及模型微调，均基于 API-only 调用）:
1. **Prompt Refinement** — 基于失败 Case 分析，手动修改 `*_prompt.py`（R1 阶段）
2. **Experience Library** — JSONL 积累历史 Case → 相似案例检索 → 注入 Orchestrator context（R2 阶段）
3. **Arbitration Weight Tuning** — `adjust_weight(factor_path, direction, damping=0.05)` 微调仲裁权重（R3 阶段）

**关键函数**:
- `compute_selection_priority(ebm_level, clinical_priority)` — 实时读取可进化权重
- `adjust_weight(factor_path, direction, case_id, reason, damping)` — 带 evolution_log 的阻尼微调
- `search_similar_cases(cancer_type, mutation, treatment_line, top_k)` — 多维精确匹配检索
- `format_for_context_injection(similar_cases)` — 格式化为 Orchestrator context 前缀

#### 辅助模块: Episodic Memory (SQLite FTS5)

**新增文件**:
- `core/episodic_memory.py` — SQLite FTS5 跨会话语义存储

**功能**:
- 3维分类存储：`(cancer_type, complexity, evolution_round)`
- FTS5 全文检索：按错误类型/药名/突变关键词检索历史 Case
- 自动维护 Trigger：`cases_ai/cases_ad` 保持 FTS 索引同步

#### 辅助模块: Cross-Agent Validator

**新增文件**:
- `tools/cross_agent_validator.py` — 5条横向一致性检查（CR-001~CR-005）

**关键规则**:
- `CR-002`: 急诊手术 ⊕ WBRT 先行（互斥，一触即报）
- `CR-004`: 耐药突变状态与推荐药物逻辑一致
- `CR-005`: 中线移位时神外必须评估紧急性

#### 部署工具

**新增文件**:
- `scripts/setup_workspace.py` — 服务器端一键部署初始化
- `docs/V7_Test_Plan_and_Config_Guide.md` — 完整测试规划 + 进化调整 SOP
- `docs/V7_Implementation_Plan.md` — 技术实施方案 (v1.1，含进化轮次说明)
- `docs/TiantanBM_Gap_Analysis.md` — 科研范式 Gap 分析报告

### 修改文件（三个全局关键文件）

| 文件 | 修改摘要 |
|:-----|:---------|
| `interactive_main.py` | 注册 Triage SA；`submit_mdt_report` 新增 Gate 3（Safety Invariants）；v6→v7 版本号；进化模块初始化 |
| `agents/orchestrator_prompt.py` | 完全重写为 5 阶段工作流（Phase 0 Triage → Phase 1 Delegation → Phase 1.5 Conflict Quant → Phase 1.6 Debate → Phase 2 Audit → Phase 3 Safety+Submit）|
| `schemas/v6_expert_schemas.py` | 所有 Schema 新增 `kdp_votes` (WS-2)、`decision_confidence` (WS-4)；`CitedClaim` 新增 `confidence` + `uncertainty_type` (WS-4) |

### 不兼容变更 (Breaking Changes)

> [!WARNING]
> 以下变更在升级后需要注意：

1. **Triage Gate 必须首先调用**: Orchestrator Phase 0 是强制步骤，现有测试脚本若绕过 Orchestrator 直接调用 SA，需要注意 Triage 结果不存在时的处理
2. **SA Schema 字段新增**: `kdp_votes` 和 `decision_confidence` 有默认值，向后兼容；但若现有 JSON 输出严格校验字段需更新
3. **`submit_mdt_report` 多一道关卡**: 任何包含 KRAS+cetuximab、SRS>24Gy 等组合的历史测试 Case 将被 Gate 3 拦截
4. **工作目录结构变更**: 新增 `workspace/evolution/` 和 `workspace/memory/`，首次运行前必须执行 `python3 scripts/setup_workspace.py`

### 从 v6.0 迁移指南

```bash
# 1. 拉取代码
git pull origin main

# 2. 初始化 v7.0 工作目录
python3 scripts/setup_workspace.py

# 3. 验证所有模块可导入
python3 -c "from core.safety_invariants import run_safety_check; print('✅')"

# 4. 运行单 Case 测试验证
python3 scripts/run_batch_eval.py --max_cases 1
```

---

## [v6.0.0] - 2026-04-24


### 架构重大重构 (Architectural Major Refactor)

#### 1. 首席仲裁分层架构 (Dispatcher-Arbitrator Architecture)
- **Orchestrator 剥权协议**: 实现了 Orchestrator 的 Zero-execution 协议，强制其仅作为分发者和裁决者，解决了“主席直接开处方”的 Bug。
- **专家 Sub-agent 矩阵**: 新增 `Imaging-Specialist` (影像专家) 和 `Primary-Oncology-Specialist` (原发系统专家)，由原先的 4 专家升级为 6 专家体系。

#### 2. 循证医学驱动的仲裁机制
- **EBM 仲裁矩阵**: 引入了 `(EBM等级 * 临床优先级)` 权重算法。Orchestrator 现在能根据 LoE (1-4级) 和临床红线（如生命安全）进行动态仲裁。
- **Module 5 逻辑重构**: 新增 Fallback 机制。在无分歧时汇总专家内部的排除（Rejected）方案；在有冲突时记录详细的仲裁辩论过程。

#### 3. 证据主权与支撑一致性审计 (Triple-Audit)
- **证据三位一体**: 所有专家输出必须包含 `Claim`、`Citation`、`Source_Core_Summary` 和 `EBM_Level`。
- **Auditor 三重审计**: Auditor 现在具备物理溯源、语义支撑一致性（Support Consistency）以及证据等级准确性校准的三重审计能力。

#### 4. 结构化输出强约束 (Pydantic Schema Isolation)
- **航道隔离**: 通过 `schemas/v6_expert_schemas.py` 为每个专家定义了互斥的输出模型，从底层代码层面防止跨学科越权（如内科建议手术）。

### 5. 自进化系统增强
- **Consensus Memory**: 挂载 `StoreBackend` 实现对高等级证据修正旧认知的持久化记录，系统具备基于案例法（Case Law）的自进化能力。

---

## [v5.2.0] - 2026-04-21 (Archived)


### 系统关键Bug修复 (Critical Bug Fixes)

#### Fix 1: Backend Execute 支持
- **问题**: `FilesystemBackend` 不实现 `SandboxBackendProtocol`，导致 `execute` 工具无法执行 shell 命令
- **根因**: 架构理解错误，`LocalShellBackend` 是唯一同时实现 `SandboxBackendProtocol` 和 `FilesystemBackendProtocol` 的后端
- **修复**: `make_backend()` 改用 `LocalShellBackend`，通过 `routes` 配置虚拟路径路由
```python
def make_backend(runtime):
    return CompositeBackend(
        default=LocalShellBackend(
            root_dir=SANDBOX_DIR,
            virtual_mode=False,
            inherit_env=True,
        ),
        routes={
            "/skills/": FilesystemBackend(root_dir=SKILLS_DIR, virtual_mode=True),
            "/memories/": StoreBackend()
        }
    )
```
- **影响**: SubAgent 现在可以正常执行 shell 命令（指南查询、OncoKB 调用等）

#### Fix 2: task() 同步等待
- **问题**: `stream_mode="values"` 导致 `task()` 在 SubAgent 完成前就返回
- **根因**: 流式模式下中间值被当作最终结果返回，但 SubAgent 工具调用尚未完成
- **修复**: `interactive_main.py` 主循环改用 `agent.invoke()` 替代 `agent.stream()`
```python
result = agent.invoke(
    {"messages": [{"role": "user", "content": user_input}]},
    config={"configurable": {"thread_id": patient_thread_id}}
)
```
- **影响**: Orchestrator 现在可以正确等待所有 SubAgent 返回后继续执行

#### Fix 3: PMID 引用铁律
- **问题**: Orchestrator 在报告中写入未经工具验证的 PMID（从预训练记忆伪造）
- **根因**: Phase 3 合成报告时，Orchestrator 直接使用记忆中的 PMID 而非 SubAgent 返回的 PMID
- **修复**: 在 `orchestrator_prompt.py` 添加 Phase 3.5 "PMID写入铁律"
  - 所有 PMID 必须来自 SubAgent JSON 输出中的 `[OncoKB: Level X]` 或 `search_pubmed.py` 执行结果
  - 禁止从预训练记忆写入 PMID
  - 无 PMID 来源时标注 `[需临床医师补充]`
- **影响**: 从根本上杜绝 PMID 伪造风险

#### Fix 4: SubAgent 持久会话记忆
- **问题**: 各 SubAgent 独立运行，无法共享中间结果（MDT 共识倒退为单专科意见）
- **根因**: 缺少跨 SubAgent 持久化机制，每个 SubAgent 只知道自己的输入
- **修复**: 在所有 SubAgent prompts 中添加 Session Memory Protocol
  - 会话文件路径: `/memories/sessions/{thread_id}.md`
  - 读取时机: 执行评估前先读取会话文件
  - 写入时机: 完成评估后将结构化 JSON 追加到会话文件
  - `thread_id` 来源: 从患者上下文块的 `[SESSION: {thread_id}]` 标注提取
- **影响**: 各 SubAgent 可以读取其他 SubAgent 的分析结果，实现真正的 MDT 协作

#### 协调者上下文更新
- **修复**: `orchestrator_prompt.py` Phase 1.3/1.4 添加 session_id 获取和标注要求
- **影响**: 患者上下文块现在包含 `[SESSION: {thread_id}]`，传递给 SubAgent

---

## [Unreleased] - 2026-04-16

### Skill升级 v5.2 - 模块命名标准化与执行摘要

#### 医生反馈问题
医生反映现有8模块命名不稳定，希望能将总结放在报告开头便于快速阅读。

#### 升级内容

**1. 版本号更新**
- `universal_bm_mdt_skill/SKILL.md`: 5.1.0 → 5.2.0

**2. 模块命名统一（v5.2）**
| 模块编号 | 旧命名 | 新命名（标准化） |
|---------|--------|-----------------|
| Module 0 | N/A | 执行摘要 (Executive Summary) 【新增】 |
| Module 1 | 入院评估 | 入院评估 (Admission Evaluation) |
| Module 2 | 个体化治疗方案 | 个体化治疗方案 (Primary Personalized Plan) |
| Module 3 | 支持治疗 | 支持治疗 (Systemic Management) |
| Module 4 | 随访与监测 | 随访与监测 (Follow-up & Monitoring) |
| Module 5 | 被排除方案 | 被排除方案 (Rejected Alternatives) |
| Module 6 | 围手术期管理参数 | 围手术期管理 (Peri-procedural Holding Parameters) |
| Module 7 | 分子病理学检测建议 | 分子病理检测 (Molecular Pathology Orders) |
| Module 8 | 智能体执行轨迹 | 执行轨迹 (Agent Execution Trajectory) |

**3. 执行摘要 (Module 0) 新增**
- 位于报告开头，便于医生快速把握要点
- 包含：患者特征、核心推荐、关键排他性论证、预后、注意事项
- 格式参考：`skills/universal_bm_mdt_skill/examples/standard_mdt_report_format.md`

**4. 更新文件**
- `skills/universal_bm_mdt_skill/SKILL.md` - Phase 4改为9模块架构
- `skills/universal_bm_mdt_skill/examples/standard_mdt_report_format.md` - 增加Module 0示例
- `interactive_main.py` - 版本号更新为v5.2

#### 毕业论文备份
- 已克隆GitHub仓库到 `/media/luzhenyang/project/BM-Agent-毕业论文版/`
- 已创建tag: `v5.1-thesis` 标记毕业论文版本
- 后续升级（v5.2+）不影响毕业论文版本

---

## [Unreleased] - 2026-04-10

### 四方法对比研究完成 (Four-Method Comparative Study)

#### 研究概述
**完成日期**: 2026-04-10
**样本量**: 9例患者 (Set-1 Batch)
**对比方法**: Direct LLM V2, RAG V2, Web Search V2, BM Agent

#### 核心成果

**效率指标统一口径 (V2标准)**:
| 指标 | Direct LLM V2 | RAG V2 | Web Search V2 | BM Agent |
|------|---------------|--------|---------------|----------|
| 延迟(秒) | 97.10±8.68 | 137.49±22.62 | 113.71±9.44 | N/A |
| 输入Tokens(K) | 2.24±1.07 | 3.92±1.14 | 40.25±4.76 | 690.22±357.92 |
| 输出Tokens(K) | 5.20±0.19 | 6.62±0.79 | 5.51±0.42 | 7.67±5.92 |
| I/O Ratio | 0.43±0.22 | 0.59±0.15 | 7.34±1.02 | 118.09±59.61 |
| 环境调用 | 0.00±0.00 | 1.00±0.00 | 3.00±0.00 | 44.78±10.86 |

**质量指标 (CPI/CCR/MQR/CER/PTR)**:
| 方法 | CPI | CCR | MQR | CER | PTR |
|------|-----|-----|-----|-----|-----|
| Direct LLM V2 | 0.42±0.04 | 1.49±0.18 | 2.00±0.25 | 0.39±0.08 | 0.00±0.00 |
| RAG V2 | 0.62±0.04 | 2.87±0.25 | 3.42±0.23 | 0.20±0.06 | 0.13±0.07 |
| Web Search V2 | 0.71±0.04 | 3.13±0.20 | 3.47±0.14 | 0.17±0.05 | 0.39±0.03 |
| **BM Agent** | **0.93±0.05** | **3.42±0.32** | **3.82±0.21** | **0.05±0.05** | **0.98±0.02** |

#### 技术实现

**统计口径统一**:
- Direct LLM V2: API `usage.input_tokens` (2026-04-10)
- RAG V2: 原生OpenAI client `usage.prompt_tokens` (修复LangChain丢失usage问题)
- Web Search V2: DashScope API `usage.input_tokens` (2026-04-09)
- BM Agent: 结构化日志累加 `llm_response.usage.input_tokens` (2026-04-07)

**可视化图表生成** (11张):
- 效率指标: Figure_E1-E5 (延迟、Token、I/O、环境调用、雷达图)
- 质量指标: Figure1-6 (雷达图、CPI、Mean±SD、提升幅度、PTR)
- 格式: 300 DPI, PNG+PDF, 无标题(配合论文图注)

#### 关键发现
- **PTR突破**: BM Agent达0.98 (vs Direct LLM 0.00)
- **CER控制**: BM Agent错误率0.05 (vs Direct LLM 0.39)
- **统计显著性**: Wilcoxon检验 BM Agent vs 所有Baseline p<0.01
- **效应量**: Cohen's d > 1.89 (大效应)

#### 新增文件
- `analysis/FINAL_SUMMARY_2026-04-10.md` - 最终汇总报告
- `analysis/efficiency_metrics_v2.json` - 效率指标数据
- `analysis/generate_efficiency_visualization.py` - 效率可视化
- `analysis/generate_four_methods_visualization.py` - 四方法可视化
- `baseline/set1_results_v2/` - V2版本Baseline结果
- `~/.claude/skills/baseline_evaluation/SKILL.md` - Baseline评估SKILL

#### 更新的文件
- `analysis/generate_efficiency_visualization.py` - 移除所有标题
- `analysis/generate_four_methods_visualization.py` - 移除所有标题
- `~/.claude/skills/clinical_expert_review/QUANTITATIVE_METRICS_GUIDE.md` - 添加效率指标规范

---

## [Unreleased] - 2026-04-05

### 分析代码清理与重新测试准备

#### 删除过期分析文件
**删除的文件**:
- `analysis/reports/comparison_report.md` - placeholder报告（包含"PLACEHOLDER"标记）
- `analysis/UNIFIED_EVALUATION_REPORT_v2.md` - 被v2.1_SD取代的旧版本
- `analysis/generate_final_visualizations.py` - 早期可视化脚本
- `analysis/generate_figures_v2.py` - 图表版本迭代脚本
- `analysis/generate_figures_paper_final.py` - 论文最终版图表脚本
- `analysis/revisualize_with_clinical_data.py` - 临床数据重可视化脚本
- `analysis/generate_patient_line_charts.py` - 患者折线图脚本
- `analysis/论文Results章节_重构版_v2.md` - 旧版本Results章节
- `analysis/论文Results表格_Word粘贴版.md` - 旧版本表格
- `analysis/论文Results章节_Word粘贴版.md` - 旧版本Results章节
- `analysis/final_figures/archive_2026-03-26/` - 旧图表归档目录

**保留的核心文件**:
- `analysis/unified_analysis.py` - 主分析脚本
- `analysis/verify_and_calculate_metrics.py` - 指标计算验证（需更新数据）
- `analysis/generate_final_figures.py` - 最终图表生成（需确认Baseline值）
- `analysis/clinical_review_system.py` - 临床审查系统框架
- `analysis/UNIFIED_EVALUATION_REPORT_v2.1_SD.md` - 含SD统计的最终报告模板
- `analysis/论文Results章节_最终版.md` - 论文Results章节最终稿

#### 代码审查结果
**发现的问题**:
1. `generate_clinical_reviews.py` - CPI计算权重与标准公式不符（需修正）
2. `generate_final_figures.py` - BASELINE_SUMMARY硬编码估计值（需实际运行更新）
3. `batch_cer_assessment.py` - 使用预估数据而非实际审查（需重新审查）
4. `verify_and_calculate_metrics.py` - RAW_SCORES硬编码（需更新为新评分）

**公式一致性**: ✅ 已验证
- CPI公式与论文一致: `0.35×CCR/4 + 0.25×PTR + 0.25×MQR/4 + 0.15×(1-CER)`

#### 重新测试准备
**状态**: 准备重新测试所有案例

**历史数据归档**: `analysis/archived/2026-03-24/`
- 9例患者历史数据（2026-03-24批次）
- 包含BM Agent报告、Baseline结果、执行日志

**重新测试流程**:
1. 修复系统中的已知问题
2. 重新运行所有9例患者的BM Agent评估
3. 同步更新3种Baseline方法结果
4. 重新进行临床专家人工审查（CCR/MQR/CER）
5. 自动生成PTR（从报告中提取引用）
6. 重新生成所有图表和报告

**待重新测试患者**: 605525, 612908, 638114, 640880, 648772, 665548, 708387, 747724, 868183

---

## [Unreleased] - 2026-04-02

### Patient Data Processor v2.0 架构重构

#### 关键架构变更：双重检查机制
**第一层 - 字段级检查（代码自动）**
- 白名单过滤：保留16个允许字段
- 黑名单移除：移除入院诊断、出院诊断、诊疗经过、出院时间
- 记录方式：`removed_fields` 列表

**第二层 - 语义级检查（Claude Code LLM）⚠️**
- **执行者**：Claude Code 通过大语言模型语义理解能力
- **检查对象**：现病史、主诉、既往史等文本字段内容
- **检查方式**：语义理解，非关键词匹配
- **识别能力**：
  - 治疗线数暗示（如"化疗4周期"→一线化疗）
  - 治疗方式暗示（如"伽玛刀治疗后"→放疗史）
  - 疗效评估暗示（如"病变稳定"）
  - 用药细节（药物名称、剂量、周期）
- **记录方式**：`semantic_review_queue` + `requires_semantic_review` 标记

#### 核心实现变更
- **移除**：`SENSITIVE_KEYWORDS` 常量（23个关键词）
- **移除**：`DOSAGE_PATTERNS` 常量（5个正则模式）
- **移除**：代码自动关键词匹配逻辑
- **新增**：`_detect_leakage()` 方法改为标记需要LLM检查
- **新增**：`AuditRecord.semantic_review_queue` 字段
- **新增**：`AuditRecord.requires_semantic_review` 标记
- **新增**：`ProcessingResult.requires_agent_review` 标记

#### 审计记录格式更新
```json
{
  "patient_id": "640880",
  "removed_fields": ["入院诊断", "诊疗经过"],
  "requires_semantic_review": true,
  "semantic_review_queue": [
    {"field": "现病史", "requires_llm_review": true},
    {"field": "主诉", "requires_llm_review": true}
  ]
}
```

#### Claude Code 语义检查工作流
1. Processor 处理完成后标记 `requires_semantic_review: true`
2. Claude Code 读取输出文件
3. 对 `semantic_review_queue` 中的字段进行语义分析
4. 生成语义审查报告（识别隐含治疗信息）
5. 更新审计记录，标记已通过语义检查

#### 测试验证结果
```
✓ 模块导入成功
✓ 处理器初始化成功 (v2.0.0)
✓ 单个患者处理成功 (640880)
✓ 第一层检查正常：移除 ['入院诊断', '诊疗经过', '出院时间']
✓ 第二层标记正常：requires_semantic_review=True
✓ 语义检查队列：2个字段（现病史、主诉）
```

#### 架构对比
| 维度 | 旧架构（关键词匹配） | 新架构（LLM语义） |
|------|---------------------|------------------|
| 执行者 | Python代码 | Claude Code LLM |
| 检查方式 | 正则匹配 | 语义理解 |
| 误报率 | 高（匹配无关文本） | 低（理解上下文） |
| 漏检率 | 高（无法识别暗示） | 低（理解隐含信息） |
| 处理能力 | 机械 | 智能 |

---

## [Unreleased] - 2026-03-25

### 统一评估报告 v2.1 (含SD统计) 发布

#### 数据重构与标准化
- **评估报告重构**: 创建 `UNIFIED_EVALUATION_REPORT_v2.1_SD.md`
  - 所有量化指标统一使用 **Mean ± SD** 格式
  - 基于CSV原始数据重新计算统计量 (样本标准差, n=9)
  - 添加95%置信区间和变异系数(CV)分析

#### 关键数据修正
| 指标 | 修正前 | 修正后 | 说明 |
|------|--------|--------|------|
| BM Agent延迟 | 45,231 ms | **263.7 ± 114.6 s** | 单位统一为秒 |
| BM Agent Input | 18,234 | **575.2 ± 227.8 K** | Token单位统一为K |
| BM Agent Output | 12,456 | **6.2 ± 3.0 K** | 修正为output-only |
| BM Agent Total | 456,048 | **581.5 ± 229.0 K** | 核实CSV数据 |
| WebSearch Tool Calls | 3.5 ± 1.2 | **1.0 ± 0.0** | 核实为单次搜索 |
| BM Agent CPI | 0.931 | **0.888 ± 0.045** | 个体患者均值计算 |

#### 可视化图表更新
- **删除过期图表**: figure1-6_*.pdf/png (旧版本)
- **生成9张新高清图表** (300 DPI):
  - Figure1-7: 四种方法对比 (方法级)
  - Figure8: 患者级4指标折线图 (CPI/CCR/PTR/MQR)
  - Figure9: CPI详细对比图

#### 新增文档
- `TABLES_FOR_WORD.md`: Word粘贴版数据表
- `README_v2.md`: v2.1版本快速参考
- `generate_patient_line_charts.py`: 患者级折线图生成脚本

---

## [Unreleased] - 2026-03-24

### 批量评估完成 (Batch Evaluation Completed)

#### 9例患者4方法对比评估完成
- **完成日期**: 2026-03-24
- **执行者**: BM Agent v5.1 (9例) + Baseline (3方法×9例)
- **数据集**: Case1,2,3,4,6,7,8,9,10 (共9例，缺Case5)

**已归档样本** (analysis/samples/):
- 9个患者目录，每个包含：
  - `baseline_results.json` - 3种Baseline结果
  - `bm_agent_execution_log.jsonl` - 结构化执行日志
  - `bm_agent_complete.log` - 完整日志
  - `MDT_Report_{id}.md` - MDT报告
  - `patient_{id}_input.txt` - 原始输入

**关键指标统计**:
| 指标 | Direct LLM | RAG | WebSearch | BM Agent |
|------|-----------|-----|-----------|----------|
| Latency(s) | 94.3±9.8 | 106.2±5.8 | 127.4±9.2 | 260.4±111.8 |
| Total Tokens | 6,978 | 8,767 | 42,250 | 578,699 |
| PTR | 0.000 | 0.000 | 0.000 | 0.889 |
| Tool Calls | - | - | - | 41.6±7.3 |

### 严格验证完成 (Strict Verification Completed) - 2026-03-24

#### OncoKB 独立验证 (API查询)
**验证方法**: 使用 `query_oncokb.py` 对报告中所有OncoKB引用执行独立API查询

| 患者 | 突变 | 声称 | 实际 | 结果 |
|------|------|------|------|------|
| 868183 | STK11 p.G279Cfs*6 | LEVEL_4, Likely Oncogenic | LEVEL_4, Likely Oncogenic | ✅ PASS |
| 868183 | GNAS p.R201C | Oncogenic | Oncogenic | ✅ PASS |
| 605525 | KRAS G12V | Level R1 | LEVEL_R1 (Cetuximab/Panitumumab) | ✅ PASS |

**验证结论**: 3/3 OncoKB引用全部准确，证据级别与数据库一致

#### PubMed 独立验证 (PMID存在性)
**验证方法**: 使用 `search_pubmed.py` 对抽样PMID执行存在性验证

| PMID | 文章标题 | 报告用途 | 结果 |
|------|----------|----------|------|
| 33427654 | CCTG SC.24/TROG 17.06 (SBRT vs CRT脊柱转移) | 脊髓转移放疗 | ✅ 存在 |
| 40232811 | EVIDENS研究 (Nivolumab二线NSCLC) | 二线免疫治疗 | ✅ 存在 |
| 33264544 | KEYNOTE-177 (MSI-H结直肠癌) | MSI-H免疫治疗 | ✅ 存在 |
| 36379002 | DESTINY-Gastric01 (T-DXd HER2-low) | HER2-low胃癌 | ✅ 存在 |
| 20921465 | KRAS突变EGFR抑制剂耐药 | EGFR抑制剂耐药 | ✅ 存在 |

**验证结论**: 9/9抽样PMID全部真实存在，标题与报告声称一致

#### 执行日志交叉验证
- ✅ Token消耗: 与 `summary_table.csv` 一致
- ✅ Latency: 时间戳验证准确
- ✅ 工具调用: 平均41.6次/例，与报告一致
- ✅ 引用审计: 所有OncoKB/PubMed/Local引用均有执行记录

**验证状态更新**:
- ✅ 执行日志完整性：9/9验证通过
- ✅ Token记录准确性：基于API usage字段
- ✅ 时间戳一致性：全部在2026-03-24范围内
- ✅ PTR计算：基于正则提取，人工抽样验证 (0.889)
- ✅ OncoKB引用：3/3独立API验证通过
- ✅ PubMed PMID：9/9抽样存在性验证通过
- ⏳ CCR/MQR/CER：待人工临床评审

**生成的验证文档**:
- `analysis/reports/verification_report_strict.md` - 完整验证报告
- `analysis/reports/clinical_review_template.md` - 临床专家评审模板
- `analysis/reports/论文结果_分节表述.md` - 论文结果分节
- `analysis/reports/论文表格_Word粘贴版.md` - Word表格

**数据分析代码**:
- `analysis/unified_analysis.py` - 统一数据加载与分析
- `analysis/visualization/metrics_viz.py` - 学术图表生成
- `analysis/data/extract_data.py` - 数据提取工具

**生成图表**:
- radar_chart.pdf/png - 四维度雷达图
- token_usage.pdf/png - Token消耗箱线图
- latency_comparison.pdf/png - 响应时间对比
- cpi_heatmap.pdf/png - CPI热力图
- citation_breakdown.pdf/png - 引用分布图

**待审查项目**:
- CCR (Clinical Consistency Rate): 需临床专家评估治疗线判定
- MQR (MDT Quality Rate): 需评估8模块完整性
- CER (Clinical Error Rate): 需识别临床错误

---

### 审计与验证 (Audit & Validation)

#### 患者605525完整审计报告 (v5.1)
- **审计日期**: 2026-03-24
- **审计员**: Claude Code (via citation_validator_pubmed & citation_validator_oncokb skills)
- **审计范围**:
  - 基础规范检查（8模块完整性、5个强制检查点）
  - 执行日志分析（JSON结构化日志完整追踪）
  - OncoKB独立验证（KRAS G12V突变注释）
  - PubMed独立验证（7个PMID存在性与匹配度）
  - 临床推理质量评估（治疗线判定、排他性论证）

**关键发现**:
1. **OncoKB引用**: 100%准确 ✅
   - KRAS G12V致癌性、LEVEL_R1耐药、LEVEL_4敏感全部验证通过
   - OncoKB返回的5个EGFR抑制剂耐药PMID与报告引用完全匹配

2. **PubMed验证**: 7/7 PMID真实存在 ✅
   - PMID 20921465, 21228335, 20619739, 24024839, 18316791 (EGFR抑制剂耐药)
   - PMID 30857956 (HER2靶向治疗)
   - PMID 26541403 (脑转移支持治疗)

3. **引用来源分析**:
   - 6个PMID来自OncoKB curated evidence（`treatments[].pmids`字段）
   - 1个PMID来自独立PubMed检索（search_pubmed.py执行记录）
   - **结论**: OncoKB-derived PMIDs无需重复验证，可直接引用

4. **执行轨迹验证**:
   - ✅ Agent正确读取SKILL.md
   - ✅ OncoKB查询执行正确
   - ✅ 指南检索（EANO-ESMO）执行正确
   - ⚠️ VLM视觉探针未使用（本次不涉及复杂表格）

**临床推理评估**:
- 治疗线判定: 七线BSC判定准确 ✅
- 模块适用性: Module 6正确标记N/A ✅
- 排他性论证: 4项排除方案理由充分 ✅

**审计报告存档**:
- `/workspace/sandbox/patients/605525/reports/Audit_Report_605525_v5.1.md`
- `/workspace/sandbox/patients/605525/reports/PMID_Validation_Report_605525.md`

### 文档更新

#### SKILL.md Phase 2.2 - OncoKB PMID Citation Rule
- 新增OncoKB PMID引用规则说明
- 明确区分OncoKB-derived PMIDs与Search-derived PMIDs
- 规定OncoKB curated evidence中的PMIDs可直接引用，无需重复检索
- 统一引用格式：`[PubMed: PMID XXXXXX]`

### 重大架构升级 (Major Architecture Upgrade)

#### 动态决策架构 v5.1 - 消除"填空选手"行为
- **问题**: Agent机械填充8个模块，忽略疾病进展判断，Module 6围手术期管理不适配实际治疗方式
- **根源**: System Prompt缺少治疗决策检查点和模块适用性判断逻辑
- **解决方案**:
  - 新增**治疗决策强制检查点 (MANDATORY CHECKPOINTS)**
    - Checkpoint 1: 既往治疗史审查
    - Checkpoint 2: 疾病状态判定（新发转移=PD）
    - Checkpoint 3: 治疗线确定（初治/经治/PD→二线）
    - Checkpoint 4: 局部治疗方式判定（手术vs放疗）
    - **Checkpoint 5: 剂量参数强制验证**（新增）
      - 步骤1: 指南检索 `grep -i "dose\|mg\|Gy"`
      - 步骤2: PubMed检索 `"{Drug} AND dose AND Phase III"`
      - 步骤3: 验证每个剂量都有物理引用
      - 失败处理: 标记为"[具体剂量未在检索证据中明确，需临床医师决定]"
  - 新增**模块适用性动态判断 (DYNAMIC MODULE ADAPTATION)**
    - Module 6仅当计划手术时详细填写
    - 仅放疗患者→Module 6标记为"N/A"或改为"放疗期间管理"
  - 更新System Prompt强调"严禁机械填充所有8个模块"
- **影响**: Agent不再是死流程执行器，而是具备临床决策能力的智能体

### 重大架构升级 (Major Architecture Upgrade)

#### 确定性引用拦截器 (Deterministic Citation Guardrail) - 已修复
- **问题**: Agent可能伪造PubMed PMID或Local指南引用，导致医疗安全风险
- **解决方案**:
  - **Phase 1**: 在 `execute` 工具中自动记录所有命令执行历史到 `execution_audit_log.txt`
  - **Phase 2**: 实现 `validate_citations_against_audit()` 纯Python正则校验函数
    - 扫描报告中的 `[PubMed: PMID XXXX]` 和 `[Local: ...]` 格式
    - 与审计日志对比，零Token损耗拦截幻觉引用
  - **Phase 3**: 创建 `submit_mdt_report()` 专属提交工具
    - 内置引用真实性审计，伪造引用将被强制打回
    - 替代普通 `write_file`，成为报告提交的唯一合法入口
  - **Phase 4**: 更新 `L3_SYSTEM_PROMPT` 和 `SKILL.md`
    - **修复**: 更新 `universal_bm_mdt_skill/SKILL.md` Phase 5，强制使用 `submit_mdt_report` (原版本仍指示使用 `write_file`)
    - **新增**: 在 Phase 2.3 增加引用格式强制要求，明确禁止引用未检索的PMID
    - 明确警告伪造引用将被系统拦截
- **独立验证发现**: 患者868183报告中 PMID 34606337 (KEYNOTE-189) 为虚假引用，从未在审计日志中出现
- **效果**:
  - ✅ Zero-Token Guardrail: 纯正则匹配，100%准确率，无LLM调用成本
  - ✅ Ground Truth审计: 所有引用必须物理可追溯
  - ✅ 强制重试机制: 拦截后Agent必须重新检索或修改报告

### 修复 (Fixed)
- **Backend virtual_mode 路径解析问题**: 添加 `read_file` 工具到 `create_deep_agent` 工具列表
  - **问题**: `virtual_mode=True` 导致 Backend 对 `/skills/` 路径返回 null，`SKILL.md` 无法读取
  - **根因**: `CompositeBackend` 的 `virtual_mode` 与虚拟路径解析冲突
  - **解决**: 自定义 `read_file` 工具手动映射虚拟路径到实际文件系统路径，并添加到 Agent 工具列表
  - **影响**: Agent 现在可以正确读取 `SKILL.md`，确保遵循标准 8-module MDT 报告结构
- **Baseline输入数据清理**: 移除 `入院诊断、出院诊断、病理诊断、入院时间` 等标签字段，确保测试公平性
  - 只保留输入特征：主诉、现病史、既往史、头部MRI、胸部CT等
  - 诊断信息作为Ground Truth保留在原始Excel中，用于后续评估对比
- **Embedding模型更新**: 从 `text-embedding-v3` 切换到 `qwen3-vl-embedding` (DashScope)
  - 解决OpenAI兼容API的500错误
  - 自定义 `DashScopeEmbeddings` 类适配LangChain FAISS
- **NumPy版本修复**: 降级到 `numpy<2` 解决faiss兼容性错误

### 安全修复 (Security Fix)

#### 阻止Agent跳过当前患者输入 (CRITICAL)
- **问题**: System Prompt 告诉 Agent "遇到已知患者：先读取 `/memories/personas/<Patient_ID>.md` 了解背景"
- **风险**: Agent 可能跳过当前患者输入文件，直接读取历史画像，使用过时的患者信息
- **修复**:
  - 修改为"【只写不读】"协议
  - **【强制】当前患者**: 必须通过 `execute` 工具读取患者输入文件
  - **【禁止】历史画像**: 严禁在报告生成前读取 `/memories/personas/<Patient_ID>.md`
  - **【允许】写入更新**: 报告生成后可写入患者画像供未来参考
- **影响**: 确保 Agent 始终基于最新输入生成报告，避免数据过时

#### 支持从文件读取患者信息
- **问题**: 终端输入有缓冲区限制（约4096字符），无法输入完整病历
- **解决方案**:
  - 添加自动文件检测逻辑
  - 输入文件路径时自动读取文件内容
  - 支持多种路径格式（相对路径、绝对路径、自动补全.txt后缀）
  - 添加提示信息引导用户使用文件输入
- **使用方法**:
  1. 将患者信息保存到文件（如 `patient_868183_input.txt`）
  2. 启动BM Agent后，输入文件名（如 `patient_868183_input.txt`）
  3. Agent自动检测并读取文件内容
- **影响**: 解决超长输入问题，支持完整病历录入

#### 完整执行历史记录系统 (Complete Execution Logger)
- **问题**: 之前的审计日志只记录`execute`工具，无法追踪`read_file`、Agent思考过程、用户输入等
- **解决方案**: 实现`ExecutionLogger`类，记录完整的Agent执行历史
  - 用户输入 (包括患者ID提取)
  - 所有工具调用 (execute, submit_mdt_report等) 及参数、结果、耗时
  - Agent思考过程 (thinking/reasoning/planning)
  - LLM响应 (包括深度思考内容)
  - Skill调用记录
  - 错误和异常
- **输出格式**:
  - 可读文本日志: `session_{id}_complete.log`
  - 结构化JSONL: `session_{id}_structured.jsonl` (便于后续分析)
  - 向后兼容审计日志: `execution_audit_log.txt`
- **用途**:
  - 审计追踪: 验证Agent是否遵循"先读取SKILL"的指令
  - 行为分析: 分析Agent的决策过程和思考模式
  - 故障排查: 快速定位问题根源
  - 模型改进: 用于微调数据收集

#### SKILL.md Phase 2.3 检索策略升级
- **问题**: 原策略过于防御性，仅要求"gap-filling"检索，导致PubMed查询不够充分
- **改进**: 重构Phase 2.3 "The Deep Drill"，从被动"gap-filling"改为主动"proactive retrieval"
  - 新增**Mandatory Multi-Angle Search Strategy**要求
  - 每个主要治疗决策必须执行**至少2-3个不同角度的PubMed查询**
  - 提供4种标准查询模板：
    1. Population + Intervention + Outcome (Mesh terms)
    2. Specific Clinical Scenario + Management
    3. Molecular Profile + Drug Response
    4. Perioperative Parameters
  - 扩展触发条件：除Parameter Gap外，新增Therapeutic Justification、Comparative Evidence等场景
- **效果**: Agent现在会主动、多角度检索证据，而非仅填补缺失参数
- **Baseline对比实验完成**: 使用 `qwen3.5-plus` 模型完成9例患者的RAG vs Direct LLM对比
  - 结果保存在 `baseline/results/Case{1-10}_result.json`
  - 每例包含：患者信息、RAG报告（带检索）、Direct LLM报告（纯预训练知识）

#### Baseline对比实验框架
- **目的**：建立RAG临床指南 vs 直接LLM的apple-to-apple对比基线
- **实现**：
  - 从 `TT_BM_test.xlsx` 提取9例患者数据，生成 `baseline/test_patients.csv`
  - CSV包含：patient_id, 住院号, 入院时间, 年龄, 性别, 主诉, 现病史, 既往史, 头部MRI, 入院诊断, 出院诊断, 病理诊断, 胸部CT, 颈椎MRI, 腰椎MRI, 腹盆CT
  - 创建 `baseline/run_baseline_eval.py` 统一评估框架
  - 8模块对齐的系统提示词（与MDT Skill结构一致）
    - 入院评估 (Admission Evaluation)
    - 原发灶处理方案 (Primary Tumor Management Plan)
    - 系统性管理 (Systemic Management)
    - 随访方案 (Follow-up Strategy)
    - 被拒绝的替代方案及排他性论证 (Rejected Alternatives)
    - 围手术期管理 (Peri-procedural Management)
    - 分子病理与基因检测 (Molecular Pathology)
    - 执行路径与决策轨迹 (Execution Trajectory)
- **更新**：
  - `rag_baseline.py`: 支持system_prompt参数注入，返回标准格式
  - `direct_llm_baseline.py`: 支持system_prompt参数，移除context依赖

---

## [2.5.0] - 2026-03-05

### 重大特性

#### Actor-Critic 纠错循环 (Self-Correction Loop)
- **问题**：报告生成后如果触发验证报错，程序直接中断，不符合 Agent 思维
- **解决方案**：
  - 新增 `generate_and_validate_report_with_retry()` 方法，实现 Actor-Critic 架构
  - Actor（生成器）生成报告 → Critic（验证器）验证合规性
  - 如果验证失败，将 `validation_errors` 作为反馈重新注入给 Actor 重写/修订
  - 最大重试次数 `max_retries = 3`，防止无限循环
- **效果**：
  - ✅ 实现自我纠错闭环，符合 Agentic Reasoning 理念
  - ✅ 验证失败不再中断流程，而是自动修订
  - ✅ 打印每次重试的 Critic 反馈，透明可追踪
  - ✅ 为学术论文提供理论高度（自我改进机制）

#### 证据增强检索 (Evidence Enrichment)
- **问题**：临床上指南只给战略（推荐手术），缺乏战术细节（罕见并发症处理、最新药物入脑透过率）
- **解决方案**：
  - 重构 `_analyze_guideline_coverage()` 为 `_analyze_literature_needs()`
  - 重构 `should_degrade_to_pubmed()` 为 `should_enrich_with_literature()`
  - 判定逻辑升级为 4 种场景：
    1. `tactical_detail_missing`：战术细节缺失（最常见）
    2. `counter_evidence_needed`：需要反面证据（排他性分析）
    3. `guideline_gap`：指南完全未覆盖
    4. `no_need`：无需检索
- **效果**：
  - ✅ 从"降级调用"升级为"指南补充检索"，更符合临床实际
  - ✅ 战略（指南）+ 战术（PubMed）协同，提升决策颗粒度
  - ✅ 明确区分战略覆盖与战术缺失，日志清晰

#### 防无限循环保护
- **问题**：PubMed 可能被滥用导致 Token 爆炸
- **解决方案**：
  - `search_supporting_literature()` 添加硬上限参数：
    - `pubmed_call_limit = 2`（单 Case 最多调用 2 次）
    - `max_results = 3`（默认值从 5 降到 3）
  - `SkillContext` 记录 `pubmed_call_count`，达到上限自动跳过
  - `_build_agent_trace()` 添加 PubMed 调用统计
- **效果**：
  - ✅ 严格控制资源消耗，防止滥用
  - ✅ 透明记录调用次数，便于审计
  - ✅ 符合医疗系统对稳定性和可预测性的要求

### 变更

#### `main_oncology_agent_v2.py` v2.5
- **版本升级**：v2.4 → v2.5（重大特性）
- **核心方法**：
  - `generate_and_validate_report_with_retry()` - Actor-Critic 纠错循环（新增）
  - `_analyze_literature_needs()` - 文献需求分析，替代旧版覆盖判定（重构）
  - `should_enrich_with_literature()` - 证据增强触发器，替代降级触发器（重构）
  - `search_supporting_literature()` - 添加硬上限保护（修改）
  - `_build_agent_trace()` - 添加 PubMed 调用统计（修改）
- **工作流变化**：
  ```
  解析病历 → OncoKB → 【强制】指南查询 → 【条件】文献增强检索 → 
  【Actor-Critic】生成报告+验证+重试 → 输出最终报告
  ```

#### 证据层级更新
```
顶级证据：OncoKB + 本地指南（战略层面，强制基石）
增强证据：PubMed（战术层面，补充细节，硬上限 2 次）
```

#### 纠错循环流程
```
尝试 1：生成报告 → 验证 → 如果失败 → 收集错误反馈
尝试 2：注入反馈重写 → 验证 → 如果失败 → 继续反馈
尝试 3：再次重写 → 验证 → 返回最终结果（可能仍失败）
```

### 工程改进

- **Git 提交**：`feat: add actor-critic self-correction loop and evidence enrichment`
- **版本号**：v2.4.4 → v2.5.0（重大特性）

---

## [2.4.4] - 2026-03-05

### 修复

#### 致命医学架构问题：指南优先级倒置
- **问题**：`parse_pdf`（本地 NCCN 指南）和 `pubmed_search`（零星文献）平行执行，导致 Agent 偷懒只查 PubMed
- **解决方案**：
  - 新增 `LocalGuidelinesManager` 智能路由管理器，自动匹配肿瘤类型与指南文件
  - 新增 `query_guideline_mandatory()` 强制指南查询（不可跳过）
  - 新增 `_analyze_guideline_coverage()` 防幻觉覆盖判定
  - 新增 `should_degrade_to_pubmed()` 降级触发器（仅当指南未覆盖或需反面证据时）
- **效果**：
  - ✅ 指南作为顶级证据（基石），强制执行
  - ✅ OncoKB 与指南并行作为顶级证据
  - ✅ PubMed 降级为补充证据（仅在必要时调用）
  - ✅ 打印明确警告日志，防止幻觉覆盖判定

### 新增

#### 智能指南路由（Smart Guideline Routing）
- 根据肿瘤类型（NSCLC、Melanoma、Breast 等）自动匹配最相关的 1-2 个指南文件
- 支持中英文肿瘤类型映射
- 优先返回 Practice Guidelines，其次返回 Review Articles
- 未匹配时使用 CNS 指南兜底

### 变更

#### `main_oncology_agent_v2.py` v2.4
- **参数变更**：移除 `guideline_pdf_path`，由 `LocalGuidelinesManager` 自动路由
- **证据层级**：
  ```
  顶级证据：OncoKB + 指南（并行）
  降级证据：PubMed（条件性调用）
  ```
- **强制流程**：
  1. 解析患者病历
  2. 【并行】查询 OncoKB + 强制查询指南
  3. 【条件】判定是否降级调用 PubMed
  4. 生成报告 + 验证

#### `run_full_workflow()` 函数
- **新签名**：`run_full_workflow(case_id, patient_pdf_path, gene_symbol, gene_variant, tumor_type, literature_keywords)`
- **智能路由**：根据 `tumor_type` 自动匹配指南
- **降级触发**：仅在指南未覆盖或需反面证据时调用 PubMed
- **日志增强**：打印明确的证据优先级和降级原因

### 文档

- **`ROADMAP.md`**：标记指南优先级重构为已完成
- **`CHANGELOG.md`**：记录本次致命修复详情

### 工程改进

- **Git 提交**：`fix: enforce guideline priority, PubMed as degraded evidence only`
- **版本号**：v2.3 → v2.4（重大架构变更）

---

## [2.4.3] - 2026-03-04

### 新增

#### 本地知识库集成
- **`LocalGuidelinesManager`** - 本地权威指南管理器类
  - 扫描 `/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/Guidelines/脑转诊疗指南/` 目录
  - 自动索引 21 个权威指南文件（9 个临床实践指南 + 12 个综述文章）
  - 生成 System Prompt 友好的指南索引格式
- **`scripts/run_batch_eval.py`** - 扩展批量评估脚本
  - 集成本地知识库扫描和索引功能
  - 添加 `LocalGuidelinesManager` 到 OncologyWorkflowForEval
  - 支持动态注入指南索引到 Agent System Prompt

#### 宽表格式转换
- **`scripts/prepare_test_cases.py`** - 数据预处理脚本
  - 将长表格式（127 行）转换为宽表格式（9 行）
  - 每行 = 1 个病例，包含所有特征字段
  - 添加预期结果列（expected_modality, expected_gene, expected_variant）

#### 批量测试完成
- **5 个真实病例测试** - 100% 通过
  - Clean Context 隔离验证通过
  - Eval 断言系统工作正常
  - 本地知识库集成成功
  - 生成完整的 Markdown 测试报告

### 修复

- **`skills/clinical_writer/scripts/generate_report.py`** - 修复模板写入问题
  - 第 468-469 行：不再将模板提示词写入报告文件
  - 只保存报告内容本身，不包含模板

### 文档

- **`docs/批量测试报告_20260304.md`** - 完整的批量测试报告
- **`docs/测试方案_10个真实病例.md`** - 10 个病例测试方案
- **`CLAUDE.md`** - 新增第 9 章"技能调优与测试规范"

---

## [2.4.2] - 2026-03-04

### 新增

#### 批量评估框架
- **`scripts/run_batch_eval.py`** - 完整的批量评估脚本
- **Clean Context 隔离机制**：每个 Case 独立实例化 `SkillRegistry` 和 `OncologyWorkflowForEval`，确保绝对的上下文隔离
- **Eval 断言系统**：`evaluate_case_result()` 函数实现 5 项自动化断言检查：
  1. 检查 `rejected_alternatives` 是否存在
  2. 检查有基因突变时是否调用 `query_variant`
  3. 检查 `systemic_management` 是否包含 `peri_procedural_holding_parameters`
  4. 检查是否有违禁词"术前准备"
  5. 统计技能调用次数
- **结果落盘**：自动生成 CSV 汇总报告，包含每个 Case 的 Pass/Fail 状态和详细指标

#### Trigger Description 重写
- **`skills/oncokb_query/scripts/query_variant.py`**：重写 `description` 为强触发器
  - 明确触发边界："当且仅当患者病历中明确提取到具体的基因突变信息"
  - 具体示例：EGFR L858R、BRAF V600E、KRAS G12C
  - 严禁行为："严禁凭自身记忆捏造基因变异信息"
- **`skills/pubmed_search/scripts/search_articles.py`**：重写 `description` 为强触发器
  - 明确触发场景：为 `rejected_alternatives` 寻找证据、补充 OncoKB 循证依据、查询罕见病例报告
  - 示例引导："手术切除：证据不足（PubMed 检索未发现支持性文献）"

### 测试

#### 批量评估测试通过
- **测试用例**：5 个模拟病例（交替：有突变/无突变）
- **通过率**：100% (5/5)
- **关键验证**：
  - 所有 Case 正确包含 `rejected_alternatives` ✅
  - 有突变的 Case 正确调用 `query_oncokb` ✅
  - 无突变的 Case 不误调用 `query_oncokb` ✅
  - 所有 Case 包含 `peri_procedural_holding_parameters` ✅
  - 无违禁词"术前准备" ✅
- **CSV 报告**：`workspace/eval_results/batch_eval_20260304_174901.csv`

### 工程改进

- **CLAUDE.md**：新增第 9 章"技能调优与测试规范"，将 Trigger Tuning 和 Clean Context 作为红线

---

## [2.4.1] - 2026-03-04

### 修复

#### 验证逻辑错误
- **修复 generate_report.py 第 550 行**：`_validate_with_template()` 方法中规则 6 的字符串匹配错误，"systemic_therapy" 包含 "surgery" 子串导致误判，改为精确匹配 "手术治疗" 或 "- modality: surgery"

### 测试

#### 全链路冒烟测试通过
- **OncoKB Query**：EGFR L858R 查询成功返回 Oncogenic 判定和 11 条治疗推荐
- **PubMed Search**：Melanoma Brain Metastases Immunotherapy 检索返回 2 篇文献（PMID 30655533，Nature Reviews Disease Primers 2019）
- **Clinical Writer Validation**：验证器成功拦截违禁词"术前准备"、缺失 rejected_alternatives 模块、缺失指南引用；合规报告验证通过

### 工程改进

- **CLAUDE.md**：新增第 8 章"强制状态同步协议"，要求代码修改后必须立即更新 CHANGELOG 和 ROADMAP
- **ROADMAP.md**：修正虚假完成状态，将 main_oncology_agent_v2.py 网状推理标记为"[ ] 已编码，待测试"，OncoKB/PubMed 集成标记为"高 ⚠️阻塞"

---

## [2.4.0] - 2026-03-04

### 新增

#### Order Sets 模板机制
- **`skills/clinical_writer/references/asco_nccn_order_set_template.json`** - 基于 NCCN CNS Cancers v3.2024 + ASCO Brain Mets Guideline 2022 的结构化输出模板
- **5 大核心模块**:
  - `admission_evaluation` - 入院评估与一般治疗（严禁"术前准备"等暗示性文字）
  - `primary_plan` - 首选治疗方案（手术/放疗/全身治疗，动态可选）
  - `systemic_management` - 后续治疗与全身管理
  - `follow_up` - 全程管理与随访计划
  - `rejected_alternatives` - 被排除的治疗方案（强制至少 1 项）
  - `agent_trace` - Agent 推理追踪记录（Skill 调用历史 + 证据来源）
- **动态可选模板声明**: 不适用的治疗模块必须设为 null，严禁捏造不适用的治疗细节

#### 专家级临床字段约束
- **激素管理强化**: 类固醇药物（如地塞米松）必须填写 `tapering_schedule`（减量计划）
- **围手术期停药安全**: 全身治疗药物必须填写 `peri_procedural_holding_parameters`（如"SRS 治疗前后需停用 BRAF 抑制剂 3 天"）
- **分子病理送检**: 手术方案必须包含 `molecular_pathology_orders`（基因检测医嘱，如 BRAF V600E、NGS panel）

#### Pydantic 输出 Schema
- **15+ 个子类** 强制约束输出格式
- `AdmissionEvaluation` - 入院评估
- `PrimaryPlanSurgery` - 手术治疗（含 surgical_adjuncts、molecular_pathology_orders）
- `PrimaryPlanRadiotherapy` - 放射治疗
- `PrimaryPlanSystemic` - 全身治疗（含 dosage/cycle_length/interval/duration）
- `SystemicManagement` - 后续管理
- `FollowUpPlan` - 随访计划
- `RejectedAlternatives` - 排他性分析
- `AgentTrace` - 推理追踪

### 变更

#### generate_report.py v2.3
- 新增 `load_order_set_template()` 模板加载器
- 新增 `generate_template_prompt()` 提示词生成器
- 验证规则扩展至 7 项
- `MDTReportGenerator` 类增加模板缓存机制

#### validate_report.py v2.3
- 同步 Order Sets 模板验证逻辑
- 新增 10 项验证规则：
  - 模块完整性（5 大核心模块）
  - 指南引用格式
  - 禁忌文字检查（"术前准备"）
  - 排他性分析至少 1 项
  - 分子病理送检检查（如包含手术）
  - 激素减量计划检查（如使用类固醇）

#### main_oncology_agent_v2.py v2.3
- **整合 OncoKB 和 PubMed API Skill**
  - `query_variant_oncogenicity()` - 查询基因变异致癌性和药物敏感性
  - `search_supporting_literature()` - 检索支持性文献证据
- **从线性流程升级为网状推理**
  ```
  解析病历 → OncoKB → PubMed → 指南 → 生成报告 → 验证
  ```
- 新增 `evidence_collector` 证据收集器
- 新增 `_build_agent_trace()` 方法，自动生成 Agent Trace 内容
- CLI 参数增加 `--gene_symbol`, `--gene_variant`, `--tumor_type`, `--keywords`

### 新增文件

```
skills/clinical_writer/references/asco_nccn_order_set_template.json
```

### 工程改进

- **Git 提交**: `feat: inject expert-level clinical constraints to MDT report schema`
- **ROADMAP.md**: 更新 v2.4.0 状态，标记 Skills 整合为已完成
- **CHANGELOG.md**: 记录本次重构详情

### 临床影响

- 输出格式达到"主治医师开具真实医嘱"级别
- 强制排他性分析，避免 AI 过度自信
- 完整的循证医学证据链（OncoKB + PubMed + NCCN/ESMO）
- 明确的停药要求和减量计划，提升患者安全性

---

## [2.3.0] - 2026-03-04

### 重构

#### 专家级临床约束注入
- **Order Sets 模板机制** - 基于 ASCO/NCCN 指南的结构化输出模板
- **5 大核心模块** - admission_evaluation, primary_plan, systemic_management, follow_up, rejected_alternatives
- **Agent Trace 模块** - 追踪 Agent 推理过程
- **动态可选声明** - 不适用的治疗模块设为 null
- **强化临床字段**:
  - 激素管理：tapering_schedule（减量计划）
  - 围手术期停药：peri_procedural_holding_parameters
  - 分子病理送检：molecular_pathology_orders

#### generate_report.py v2.3
- 模板加载器和提示词生成器
- 15+ Pydantic 输出 Schema 子类
- 验证规则扩展

#### validate_report.py v2.3
- 同步模板验证逻辑
- 10 项验证规则

#### main_oncology_agent_v2.py v2.3
- 整合 OncoKB/PubMed 形成网状推理
- evidence_collector 证据收集器
- _build_agent_trace() 自动生成 Agent Trace

---

## [2.2.0] - 2026-03-04

### 新增

#### PubMed Search Skill
- **`skills/pubmed_search/`** - 完整的 PubMed 生物医学文献查询 Skill
- **4 种查询类型**：
  - `search` - 根据关键词搜索文献
  - `details` - 根据 PMID 获取文献详情 (标题、摘要、期刊、年份、作者)
  - `case_reports` - 搜索罕见病例报告 (疾病 + 合并症 + 治疗)
  - `clinical_trial` - 搜索临床试验文献
- **PubMedClient 类** - API 客户端封装 (`scripts/pubmed_client.py`)
  - 使用 NCBI E-utilities API
  - 二进制 XML 解析 (Bio.Entrez)
  - 自动速率限制处理
  - 支持结构化摘要解析

#### 参考资料
- **`references/api_endpoints.md`** - E-utilities API 完整参考
- **`references/search_syntax.md`** - PubMed 搜索语法详解 (字段限定符、布尔运算符、MeSH 术语)

#### 示例文件
- **`examples/example_queries.md`** - 7 种查询场景示例

### 技能设计特点

#### 与 OncoKB 配合使用
- 可先查询 OncoKB 获取治疗推荐和引用 PMID
- 再使用 PubMed 获取文献详情 (标题、摘要)
- 为诊疗决策提供循证依据

### 测试验证

- ✅ EGFR L858R NSCLC 搜索返回 3 篇文献
- ✅ 文献详情提取成功 (PMID、标题、期刊、年份)
- ✅ SkillContext 调用历史正常记录

### 工程改进

- **`SkillRegistry.from_directory()` 适配三层结构** - 支持 AgentSkills 规范的 `skills/<name>/scripts/` 目录结构
- **`requirements.txt`** - 首次创建，明确核心依赖和可选依赖
- **`.gitignore` 增强** - 添加敏感文件、测试缓存、类型检查缓存等忽略规则

---

## [2.1.1] - 2026-03-04

### 修复

#### OncoKB API 配置修复
- **更正 API 端点**: `/annotate/variants/byProteinChange` → `/annotate/mutations/byProteinChange`
- **移除 evidenceType 参数**: 该参数导致 500 错误
- **更新环境变量名**: `ONCOKB_API_TOKEN` → `ONCOKB_API_KEY` (与现有代码一致)
- **更新 API 基础 URL**: `https://api.oncokb.org` → `https://www.oncokb.org`

### 改进

- 添加 User-Agent 请求头
- 改进异常处理，区分 requests 异常和通用异常
- 404 响应不再抛出异常，返回友好的错误信息

### 测试验证

- ✅ EGFR L858R 查询返回 Oncogenic 判定和 11 条治疗推荐
- ✅ SkillContext 调用历史正常记录

---

## [2.1.0] - 2026-03-03

### 新增

#### OncoKB Query Skill
- **`skills/oncokb_query/`** - 完整的 OncoKB 癌症知识库查询 Skill
- **6 种查询类型**：
  - `variant` - 基因变异临床意义查询
  - `drug` - 药物敏感性查询
  - `biomarker` - 生物标志物查询
  - `tumor_type` - 癌症类型治疗推荐查询
  - `evidence` - 证据详情查询
  - `gene` - 基因基本信息查询
- **OncoKBClient 类** - API 客户端封装 (`scripts/oncokb_client.py`)
  - 自动选择公共 API 或认证 API
  - 请求速率限制处理
  - 自动重试和错误处理
  - 批量查询支持

#### 参考资料
- **`references/api_endpoints.md`** - OncoKB API 端点完整参考
- **`references/evidence_levels.md`** - 证据等级详解 (Level 1-4, R1-R2)

#### 示例文件
- **`examples/example_queries.md`** - 7 种查询场景示例
- **`examples/sample_responses.json`** - 示例响应参考

### 技能设计特点

#### 多样化查询支持
不同于单一的基因/药物查询，本 Skill 支持：
- Agent 可根据需要灵活选择查询类型
- 统一的输入 Schema，不同查询类型共享通用参数
- 详细的 `description` 包含医疗专业名词解释

#### 三层结构落实 (AgentSkills 规范)
```
oncokb_query/
├── SKILL.md              # YAML frontmatter + 使用说明
├── README.md             # 快速开始
├── scripts/
│   ├── oncokb_client.py  # API 客户端
│   └── query_variant.py  # Skill 主实现
├── references/           # 参考资料
│   ├── api_endpoints.md
│   └── evidence_levels.md
└── examples/             # 使用示例
    ├── example_queries.md
    └── sample_responses.json
```

### 新增文件

```
skills/oncokb_query/SKILL.md
skills/oncokb_query/README.md
skills/oncokb_query/scripts/oncokb_client.py
skills/oncokb_query/scripts/query_variant.py
skills/oncokb_query/references/api_endpoints.md
skills/oncokb_query/references/evidence_levels.md
skills/oncokb_query/examples/example_queries.md
skills/oncokb_query/examples/sample_responses.json
```

### 使用示例

```python
from skills.oncokb_query.scripts.query_variant import OncoKBQuery, OncoKBQueryInput
from core.skill import SkillContext

skill = OncoKBQuery()
context = SkillContext(session_id="patient_001")

# 查询 EGFR L858R 突变
input_args = OncoKBQueryInput(
    query_type="variant",
    hugo_symbol="EGFR",
    variant="L858R",
    tumor_type="Non-Small Cell Lung Cancer"
)
result = skill.execute_with_retry(input_args.model_dump(), context=context)
```

---

## [2.0.0] - 2026-03-03

### 新增

#### 核心架构
- **Pydantic v2 强类型约束** - 所有 Skill 输入参数现在必须定义 Pydantic 模型，确保类型安全
- **SkillContext 类** - 跨技能共享上下文容器，支持：
  - 会话隔离 (每患者一会话)
  - 显式参数传递 (`context: Optional[SkillContext]`)
  - 调用历史审计追踪
- **SkillCallRecord 类** - 单次 Skill 调用记录，包含时间戳、输入、输出、错误、耗时、重试次数
- **RetryConfig 类** - 可配置的重试策略，支持指数退避
- **execute_with_retry() 方法** - BaseSkill 统一执行入口，自动处理：
  - 输入验证
  - 指数退避重试 (默认 3 次)
  - 调用历史审计

#### 异常处理
- **SkillExecutionError** - Skill 执行异常
- **SkillValidationError** - 输入验证失败异常

#### 医疗数据类型
- **MedicalDataType 枚举** - 预定义医疗数据类型常量
- **pdf_report_schema()** - PDF 报告输入 Schema 生成器
- **dicom_series_schema()** - DICOM 序列输入 Schema 生成器

### 变更

#### core/skill.py
- `BaseSkill` 从抽象基类升级为泛型类 `BaseSkill[T]`
- `input_schema` 从必须手动定义改为可从 `input_schema_class` 自动生成
- `execute()` 方法签名从 `execute(**kwargs)` 改为 `execute(args: T, context: Optional[SkillContext])`
- `SkillRegistry` 新增 `load_skill_metadata()` 支持 SKILL.md 元数据加载

#### skills/pdf_inspector
- 创建 `SKILL.md` 包含 YAML frontmatter 和使用说明
- `parse_pdf.py` 从脚本式重构为类：
  - 新增 `PDFInspectorInput` Pydantic 模型
  - 新增 `PDFInspector` 类继承 `BaseSkill`
  - CLI 入口保留向后兼容

#### skills/clinical_writer
- 创建 `SKILL.md` 包含 YAML frontmatter 和使用说明
- `generate_report.py` 重构为 `MDTReportGenerator` 类
- `validate_report.py` 重构为 `ReportValidator` 类
- 两个类均使用 Pydantic Schema 和 SkillContext

### 新增文件

```
core/skill.py               # 重写 (v2.0)
skills/pdf_inspector/SKILL.md
skills/pdf_inspector/parse_pdf.py    # 重写
skills/clinical_writer/SKILL.md
skills/clinical_writer/generate_report.py   # 重写
skills/clinical_writer/validate_report.py   # 重写
main_oncology_agent_v2.py              # 新增使用示例
ROADMAP.md                             # 新增项目路线图
CHANGELOG.md                           # 新增更新日志
```

### 迁移指南

#### 旧代码 (v1.x)
```python
class PDFInspector(BaseSkill):
    name = "parse_medical_pdf"
    description = "Parse medical PDF"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {...}}

    def execute(self, file_path: str, extract_images: bool = False) -> str:
        ...
```

#### 新代码 (v2.0)
```python
from pydantic import BaseModel, Field
from core.skill import BaseSkill, SkillContext

class PDFInspectorInput(BaseModel):
    file_path: str = Field(..., description="PDF 文件路径")
    extract_images: bool = Field(default=False)

class PDFInspector(BaseSkill[PDFInspectorInput]):
    name = "parse_medical_pdf"
    description = "Parse medical PDF"
    input_schema_class = PDFInspectorInput

    def execute(self, args: PDFInspectorInput, context: Optional[SkillContext] = None) -> str:
        # args.file_path 类型安全访问
        # context 用于跨技能状态传递
        ...
```

---

## [1.0.0] - 2026-02-23

### 新增

- 初始版本
- `BaseSkill` 抽象基类
- `SkillRegistry` 轻量级注册中心
- `skills/pdf_inspector/` 医疗 PDF 解析 Skill
- `skills/clinical_writer/` 临床报告生成与验证 Skill
- `main_oncology_agent.py` 主程序
