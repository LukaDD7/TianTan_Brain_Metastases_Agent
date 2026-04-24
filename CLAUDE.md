# TianTan Brain Metastases Agent - AI 协作与开发协议 (Claude Code Protocol)

## 1. 核心宣言 (Manifesto)
**"We build intellectual Agent, not LLM with skill."**
本项目致力于打造具备高度自主规划能力（Autonomous Planning）的医疗多智能体系统，而非被死板代码限制的执行器。

## 2. 量化评估指标定义 (Evaluation Metrics Definitions)

### 2.1 临床决策一致性准确率 (Clinical Consistency Rate, CCR)

**公式**:
```
CCR = (S_line + S_scheme + S_dose + S_reject + S_align) / 5 ∈ [0, 4]
```

**子项定义**:
- **S_line** (Treatment Line): 治疗线判定准确性 (0-4分)
- **S_scheme** (Scheme Selection): 首选方案选择合理性 (0-4分)
- **S_dose** (Dosage Params): 剂量参数准确性 (0-4分)
- **S_reject** (Exclusion Reasoning): 排他性论证充分性 (0-4分)
- **S_align** (Clinical Path Alignment): 临床路径一致性 (0-4分)

**评分标准**:
- 4分: 完全符合/准确
- 3分: 基本正确/小瑕疵
- 2分: 部分正确/需调整
- 1分: 明显错误
- 0分: 严重错误/遗漏

---

### 2.2 物理可追溯率 (Physical Traceability Rate, PTR)

**公式**:
```
PTR = (1/N) × Σ(i=1 to N) V_trace(c_i) ∈ [0, 1]
```

**示性函数 V_trace(c_i)**:
- **1**: 附带合规引用标签，且二次API检索完全吻合
- **0.5**: 引用数据存在但格式非标准 (如仅标注"[1]")
- **0**: 无引用、捏造虚假出处或查证不符

**引用格式白名单**:
- `[PubMed: PMID XXXXXXXX]` - PubMed文献
- `[OncoKB: Level X]` / `[OncoKB: Oncogenic]` - OncoKB数据库
- `[Local: <文件>, Line <行号>]` / `[Local: <文件>, Section: <章节>]` - 本地指南
- `[Web: <URL>]` - 网络来源 (部分可追溯)
- `[Parametric Knowledge: <说明>]` - 参数知识 (部分可追溯，需诚实标注)

**严禁格式**:
- `[1, 45]` 等数字引用 (不可追溯)

---

### 2.3 MDT报告规范度 (MDT Quality Rate, MQR)

**公式**:
```
MQR = (S_complete + S_applicable + S_format + S_citation + S_uncertainty) / 5 ∈ [0, 4]
```

**子项定义**:
- **S_complete** (Module Completeness): 8模块完整性 (0-4分)
- **S_applicable** (Module Applicability): 模块适用性判断 (0-4分)
- **S_format** (Structured Format): 结构化程度 (0-4分)
- **S_citation** (Citation Format): 引用格式规范性 (0-4分)
- **S_uncertainty** (Uncertainty Handling): 不确定性处理 (0-4分)

---

### 2.4 临床错误率 (Clinical Error Rate, CER)

**公式**:
```
CER = min( (Σ_j w_j × n_j) / 15, 1.0 ) ∈ [0, 1]
```

**错误分级与权重**:
- **Critical (严重错误)**: w = 3.0 - 可能危及生命或导致严重并发症
- **Major (主要错误)**: w = 2.0 - 显著影响治疗效果或预后
- **Minor (次要错误)**: w = 1.0 - 轻微影响治疗质量

**归一化常数**: W_max = 15 (最大可容忍累积错误权重)

---

### 2.5 综合性能指数 (Composite Performance Index, CPI)

**公式**:
```
CPI = 0.35 × (CCR/4) + 0.25 × PTR + 0.25 × (MQR/4) + 0.15 × (1 - CER) ∈ [0, 1]
```

**权重分配说明**:
| 指标 | 权重 | 归一化 | 说明 |
|------|------|--------|------|
| CCR | 35% | CCR/4 | 临床决策一致性最重要 |
| PTR | 25% | 直接使用 | 物理可追溯性体现证据可靠性 |
| MQR | 25% | MQR/4 | 报告质量影响可读性和可用性 |
| CER | 15% | (1-CER) | 错误率越低越好 (已通过权重放大) |

**临床意义**: CPI是单一标量，用于全局比较不同系统架构的综合性能。CCR权重最高(35%)，凸显诊断与方案推荐正确性的核心地位；PTR和MQR各占25%，体现证据可靠性和格式规范性的重要性；CER权重15%，因已在分子层面经过严重错误(权重3.0)的放大惩罚。

**代码实现位置**:
- `analysis/verify_and_calculate_metrics.py:37-58` (calculate_cpi函数)
- 注意: CCR和MQR进入CPI前需先除以4归一化到[0,1]

---

## 3. 最高协作铁律 (The Iron Laws of AI Collaboration)

### 2.1 严禁无头测试 (No Headless Execution)
本系统（特别是 `interactive_main.py`）包含流式输出与人机交互 (HITL) 环节。
**未经人类显式授权，AI 助手严禁在后台使用 `Bash` 自动运行或测试本系统的主程序。**
所有的系统测试、Bug 复现，必须由人类在独立的交互式终端中手动执行，并将相关日志反馈给 AI。

### 2.2 严禁引用伪造 (No Citation Fabrication)
医疗报告中的所有引用必须是**物理可追溯**的真实证据：
- **OncoKB 引用**：必须通过 API 查询验证 `LEVEL` 和 `oncogenic` 字段
- **PubMed 引用**：必须通过 E-utilities API 验证 PMID 真实存在且摘要支持声称
- **指南引用**：必须通过 `grep`/`cat` 实际检索，严禁使用预训练知识脑补
- **格式红线**：指南引用必须使用 `[Local: <文件>, Line <行号>]` 或 `[Local: <文件>, Section: <章节>]`，严禁使用 `[Local: ..., Page X]`（除非使用 Visual Probe 渲染）

违反此铁律将导致严重的医疗安全风险。

### 2.3 文件级审批流 (File-by-file Approval Pipeline)
针对任何新功能开发、重构或 Bug 修复，必须严格遵循以下”停-等-行”协议：
- **Phase 1 (方案)**：AI 输出修改方案或架构思路。等待人类回复 `Approve`。
- **Phase 2 (认知合约)**：如果涉及新 Skill，AI 仅输出 `metadata.json` 和 `SKILL.md`。等待人类 `Approve`。
- **Phase 3 (代码)**：AI 输出具体的 `.py` 代码修改。
**严禁 AI 越级执行，严禁一次性擅自修改多个关键文件。**

### 2.4 架构守护者原则
在阅读或修改代码前，AI 必须理解当前**扁平化架构**：
- **单一主控 Agent**：无 Subagents，所有逻辑由主 Agent 直接处理
- **4 个挂载 Skills**：pdf-inspector、universal_bm_mdt_skill、oncokb_query_skill、pubmed_search_skill
- **3 个核心 Tools**：execute (shell 执行)、read_file (文件读取)、submit_mdt_report (报告提交)
- **CompositeBackend**：FilesystemBackend (sandbox) + StoreBackend (/memories/ 持久化)
- **Execute 工具**：自定义 shell 执行能力，带白名单安全机制
- **Read_file 工具**：绕过 Backend `virtual_mode` 限制，直接读取 `/skills/`、`/memories/` 等虚拟路径文件

任何试图添加 Subagents 或恢复旧三层架构的改动都将被驳回。

## 4. 架构核心与入口 (Architecture & Entrypoint)

### 3.1 主入口声明
目前系统的唯一合法主入口为：**`interactive_main.py`**。
它是基于 DeepAgents 和 LangGraph 构建的**扁平化架构**单一 Agent 系统，无 Subagents。

### 3.2 运行时架构

```
┌─────────────────────────────────────────────────────────────┐
│                    interactive_main.py                      │
│              (单一 Agent 扁平化架构 v5.2)                     │
├─────────────────────────────────────────────────────────────┤
│  L3 System Prompt (主控智能体认知协议)                        │
│  ├── 5个强制检查点 (5 MANDATORY CHECKPOINTS)                │
│  │   ├── Checkpoint 1: 治疗线动态判定                       │
│  │   ├── Checkpoint 2: 模块适用性动态判断                    │
│  │   ├── Checkpoint 3: 排他性方案论证                       │
│  │   ├── Checkpoint 4: 引用物理溯源验证                     │
│  │   └── Checkpoint 5: 剂量参数强制验证                     │
│  ├── 证据主权准则                                           │
│  ├── 深钻机制 (Deep Drill Protocol)                         │
│  └── 物理溯源引用协议                                        │
├─────────────────────────────────────────────────────────────┤
│  Tools (3个核心工具):                                        │
│  ├── execute (shell 执行，带白名单)                          │
│  ├── read_file (文件读取，绕过 Backend 虚拟路径限制)          │
│  └── submit_mdt_report (报告提交，内置引用审计)               │
├─────────────────────────────────────────────────────────────┤
│  Skills (4个挂载技能):                                       │
│  ├── /skills/pdf-inspector          (PDF 视觉探针)          │
│  ├── /skills/universal_bm_mdt_skill (MDT 报告生成协议)       │
│  ├── /skills/oncokb_query_skill     (OncoKB 基因查询)        │
│  └── /skills/pubmed_search_skill    (PubMed 文献检索)        │
├─────────────────────────────────────────────────────────────┤
│  Backend: CompositeBackend                                   │
│  ├── FilesystemBackend (sandbox 隔离)                       │
│  └── StoreBackend (/memories/ 跨会话持久化)                  │
└─────────────────────────────────────────────────────────────┘
```

**注意：** 无 L2 Subagents，无三层架构。主 Agent 直接调度 Skills 执行任务。

### 3.3 角色分工
* **Claude Code**：本项目的**开发助手**和**架构审查者**。
* **L3 主控 Agent (Qwen)**：运行时的**单一智能体**，直接读取 Skills 并执行。
* **Skills**：原子化能力单元，通过 `execute` 工具被主 Agent 调用。

## 5. 环境与测试规范 (Environment & Commands)

### 4.1 虚拟环境
* **项目专用环境**：`tiantanBM_agent`
* **底层沙盒目录**：`workspace/sandbox/`（所有 L1 抓取的大型 JSON/PDF 必须写入此目录）
* **Skill 备份**：`workspace/sandbox/skills/`（SKILL.md 的隔离备份，防止原文件被误删）

### 4.2 常用命令 (仅供人类在独立终端执行)
* **交互式查房测试**：`conda run -n tiantanBM_agent python interactive_main.py`
* **运行批量评估**：`conda run -n tiantanBM_agent python scripts/run_batch_eval.py --max_cases 1`
* **依赖安装**：`conda run -n tiantanBM_agent pip install <package>`

---

## 6. 批量评估验证状态 (Batch Evaluation Verification)

### 5.1 评估状态 (2026-04-07)

**当前状态**: Set-1批次测试中（3/9已完成）

**已完成患者** (报告生成成功，日志命名正确):
| 患者ID | 报告时间 | 关键特征 | 状态 |
|--------|----------|----------|------|
| 605525 | 2026-04-07 20:13 | 结肠癌KRAS G12V，六线治疗 | ✅ 已完成 |
| 612908 | 2026-04-07 22:22 | 肺癌EGFR突变，埃克替尼耐药 | ✅ 已完成 |
| 638114 | 2026-04-07 23:21 | 肺腺癌EGFR 19del+T790M，奥西替尼耐药后进展 | ✅ 已完成 |

**待测试患者**: 640880, 648772, 665548, 708387, 747724, 868183 (6例)

**历史数据已归档**: `analysis/archived/2026-03-24/`
- 9例患者历史数据（2026-03-24批次）
- 包含BM Agent报告、Baseline结果、执行日志

**已确认修复项**:
- ✅ 日志文件命名：现在包含日期和患者ID (session_YYYYMMDD_{patient_id}_{uuid}_complete.log)
- ✅ 无信息泄露：Agent直接读取输入文件，未提前读取patient persona
- ✅ 患者画像位置：已修复路径问题，位于 `workspace/sandbox/memories/personas/`

**待修复项（批次测试后）**:
- ⏳ Patient Persona更新机制：write_file工具未注册，需添加专用update_patient_persona工具

### 5.2 严格验证状态

**状态**: 待重新验证 (历史数据已归档)

**历史验证结果** (2026-03-24批次，仅供参考):
- PTR: 0.889 (8/9完全可追溯)
- OncoKB引用: 3/3 抽样通过
- PubMed PMID: 9/9 抽样通过

**待重新验证指标**:
- [ ] PTR (Physical Traceability Rate)
- [ ] OncoKB引用准确性
- [ ] PubMed引用真实性
- [ ] CCR (Clinical Consistency Rate)
- [ ] MQR (MDT Quality Rate)
- [ ] CER (Clinical Error Rate)

### 5.3 数据归档位置

```
analysis/samples/
├── 868183/          # 患者868183 (Case3) - 肺癌SMARCA4突变
├── 747724/          # 患者747724 (Case10) - 乳腺癌HER2+
├── 708387/          # 患者708387 (Case9) - 肺癌MET扩增
├── 665548/          # 患者665548 (Case4) - 贲门癌HER2低表达
├── 648772/          # 患者648772 (Case1) - 肺癌
├── 640880/          # 患者640880 (Case2) - 肺癌
├── 638114/          # 患者638114 (Case6) - 乳腺癌
├── 612908/          # 患者612908 (Case7) - 肺癌KRAS G12V
├── 605525/          # 患者605525 (Case8) - 结肠癌KRAS G12V
└── README.md

每个样本包含:
- MDT_Report_{id}.md          # BM Agent生成的8模块报告
- patient_{id}_input.txt      # 原始患者输入数据
- bm_agent_execution_log.jsonl # 结构化执行日志
- bm_agent_complete.log       # 人类可读完整日志
- baseline_results.json       # 3种Baseline方法结果
```

### 5.4 验证报告与论文材料

**严格验证报告**: `analysis/reports/verification_report_strict.md`
- OncoKB独立验证结果
- PubMed抽样验证结果
- 执行日志交叉验证
- 待审查项目清单

**论文结果分节表述**: `analysis/reports/论文结果_分节表述.md`
- 效率指标分析 (Latency/Token)
- PTR分析 (0.889 vs 0.000)
- 工具调用统计
- 统计检验结果

**论文表格Word版**: `analysis/reports/论文表格_Word粘贴版.md`
- 患者基本特征表
- 效率指标对比表
- PTR对比表
- 工具调用统计表
- Wilcoxon检验结果表

### 5.5 移交另一台电脑的工作清单

**已打包文件** (可直接复制):
1. `analysis/samples/` - 9例患者完整数据
2. `analysis/reports/` - 验证报告 + 论文材料
3. `analysis/unified_analysis.py` - 批量分析脚本
4. `analysis/summary_table.csv` - 汇总数据表

**需继续完成的工作**:
1. 临床专家审查CCR/MQR/CER指标
2. 完成CPI综合评分计算 (需CCR/MQR/CER)
3. 生成最终论文图表
4. 撰写讨论部分

**验证脚本可用性**:
```bash
# OncoKB验证
conda run -n tiantanBM_agent python skills/oncokb_query_skill/scripts/query_oncokb.py mutation --gene KRAS --alteration G12V --tumor-type "Colorectal Cancer"

# PubMed验证
conda run -n tiantanBM_agent python skills/pubmed_search_skill/scripts/search_pubmed.py --query "36379002[uid]" --max-results 1

# 批量分析
conda run -n tiantanBM_agent python analysis/unified_analysis.py
```

## 7. 联网与检索规范 (Web Access Rules)
* **绝对禁止使用本地无头浏览器（如 Puppeteer）**。
* **统一使用 Jina Reader 渲染**：如果需要 AI 助手读取网页，请将目标网址拼接在 `https://r.jina.ai/` 之后。

## 8. 项目状态与版本管理 (Project Management Rules)
* **状态对齐**：在开始任何新的代码编写或重构前，必须先读取 `ROADMAP.md` 和 `CHANGELOG.md`。
* **主动打卡**：每完成一个子任务，必须主动修改 `ROADMAP.md`。
* **原子化提交**：功能确认后，使用 `git add .` 和 `git commit -m "..."`，保持 Git Log 纯净。

## 9. 技能调优与 Eval 规范 (Skill Tuning & Eval)

### 7.1 触发器调优 (Trigger Tuning)
每个 Skill 在 `metadata.json` 和 `SKILL.md` 中的 `description` 必须被写成**强触发器**：明确说明”输入什么、输出什么、什么时候必须调用它”。

### 7.2 Eval 断言系统 (Assertion System)
批量评估 (`run_batch_eval.py`) 必须包含自动化断言检查，以验证 `tiantan_mdt_report_skill` 的执行效果：
- 检查报告中是否包含 `rejected_alternatives` (排他性论证)
- 检查 `systemic_management` 是否包含 `peri_procedural_holding_parameters`
- 检查是否存在违禁词（如含糊的”术前准备”）
- 检查是否严格遵循 `[Citation: xxx, Page y]` 格式红线

### 7.3 引用验证规范 (Citation Validation)
所有临床报告必须经过引用验证，确保无证据伪造：

**OncoKB 引用验证：**
- 格式：`[OncoKB: Level X]` 或 `[OncoKB: Oncogenic]`
- 必须验证 `highestSensitiveLevel` 与报告声称一致
- 必须验证 `oncogenic` 字段与报告声称一致
- 引用验证 Skill 位置：`~/.claude/skills/citation_validator_oncokb/`

**PubMed 引用验证：**
- 格式：`[PubMed: PMID XXXXXXXX]`
- 必须验证 PMID 真实存在且可检索
- 必须验证摘要内容支持报告声称
- 引用验证 Skill 位置：`~/.claude/skills/citation_validator_pubmed/`

**本地指南引用验证：**
- 格式：`[Local: <文件名>, Line <行号>]` 或 `[Local: <文件名>, Section: <章节标题>]`
- 严禁使用 `[Local: ..., Page X]` 格式（除非使用 Visual Probe）
- 必须通过 `grep -n` 或 `cat` 实际检索验证

**验证失败处理：**
- 发现伪造/错误引用 → 标记为 ❌ FAIL
- 必须提供修正建议
- 严重错误必须阻止报告生成

## 10. 报告质量审查协议 (Report Quality Review Protocol)

### 8.1 审查触发条件
当用户要求审查BM Agent生成的报告时，必须执行以下完整审查流程：

### 8.2 完整审查流程 (5步法)

#### Step 1: 基础规范检查
**执行内容：**
- 检查报告是否包含所有8个Module
- 验证5个强制检查点是否通过
- 检查引用格式是否符合规范（OncoKB/PubMed/Local）
- 扫描违禁词（如"术前准备"）

**关键审查点：**
- Module 6是否根据实际治疗计划动态调整（手术vs放疗vs N/A）
- Module 5（Rejected Alternatives）是否包含至少1项排他性论证
- 剂量参数是否有明确引用

#### Step 2: 执行日志分析
**必须读取的文件：**
```
workspace/sandbox/execution_logs/session_{id}_structured.jsonl
workspace/sandbox/execution_logs/session_{id}_complete.log
```

**分析要点：**
- Agent是否先读取了SKILL.md（检查点：read_file /skills/.../SKILL.md）
- Agent是否执行了指南检索（检查点：execute "cat Guidelines/... | grep"）
- Agent是否执行了OncoKB查询（检查点：execute "query_oncokb.py"）
- Agent是否执行了PubMed查询（检查点：execute "search_pubmed.py"）
- 引用审计是否通过（检查点：submit_mdt_report 返回值）

#### Step 3: OncoKB独立验证
**使用Skill：** `citation_validator_oncokb`

**验证流程：**
```bash
# 提取报告中所有OncoKB引用
grep -oE '\[OncoKB:[^\]]+\]' {report_file}

# 对每个突变执行独立查询
/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python \
    skills/oncokb_query_skill/scripts/query_oncokb.py \
    mutation --gene {GENE} --alteration {ALT} --tumor-type "{TYPE}"
```

**验证标准：**
- `oncogenic` 字段必须与报告声称一致
- `highestSensitiveLevel` 必须与报告声称一致
- `highestResistanceLevel` 必须验证耐药声称

#### Step 4: PubMed独立验证
**使用Skill：** `citation_validator_pubmed`

**验证流程：**
```bash
# 提取报告中所有PubMed PMID
grep -oE 'PMID [0-9]+' {report_file} | awk '{print $2}'

# 对每个PMID执行独立验证
/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python \
    skills/pubmed_search_skill/scripts/search_pubmed.py \
    --query "{PMID}[uid]" --max-results 1
```

**验证标准：**
- ✅ PMID必须真实存在
- ✅ 文章标题、作者、年份必须可检索
- ⚠️ 摘要内容应支持报告声称（注意：Agent可能基于预训练知识推断剂量范围）

**⚠️ 特别注意 - 剂量引用陷阱：**
报告可能声称"SRS 18-24Gy/1f [PubMed: PMID XXXXXX]"，但：
1. 验证PMID是否真实存在
2. **关键**：核查文章是否明确提到"18-24Gy"这个范围，还是只提到具体剂量（如"median 18Gy"）
3. 如果文章只提到单一剂量，报告中的范围可能是Agent的推断，需标记为⚠️

#### Step 5: 临床推理质量评估
**基于医学知识的人工审查：**

1. **治疗线判定合理性**
   - 既往治疗史梳理是否完整
   - 当前治疗线判定是否符合逻辑
   - 推荐方案是否适合该治疗线

2. **模块适用性判断**
   - Module 6标记为N/A是否合理（无手术计划）
   - 支持治疗内容是否与患者状态匹配

3. **排他性论证充分性**
   - 每个排除方案是否有充分理由
   - 是否引用了正确的耐药证据

### 8.3 审查输出规范

#### 审查报告必须包含：
```markdown
## 报告质量审查结果

### 一、基础规范检查
- [ ] 8个Module完整性
- [ ] 5个强制检查点通过
- [ ] 引用格式规范
- [ ] 无违禁词

### 二、执行日志分析
- [ ] Agent读取SKILL.md
- [ ] 指南检索执行
- [ ] OncoKB查询执行
- [ ] PubMed查询执行（如有）
- [ ] 引用审计通过

### 三、OncoKB独立验证
| 突变 | 声称 | 实际 | 状态 |
|-----|------|------|------|
| ... | ... | ... | ✅/❌ |

### 四、PubMed独立验证
| PMID | 声称 | 实际 | 支持度 |
|-----|------|------|--------|
| ... | ... | ... | 高/中/低 |

### 五、临床推理评估
- 治疗线判定：合理/需修正
- 模块适用性：合理/需修正
- 排他性论证：充分/需补充

### 六、关键问题与建议
1. **问题1**：...
   - 严重程度：Critical/Major/Minor
   - 建议：...
```

### 8.4 典型案例记录

**案例：患者605525报告审查（2026-03-24）**

**发现的问题：**
1. **PubMed PMID 32921513 引用偏差** ⚠️
   - 报告声称：SRS 18-24Gy/1f [PubMed: PMID 32921513]
   - 实际文章："Single- and Multifraction Stereotactic Radiosurgery Dose/Volume Tolerances of the Brain"
   - 问题：文章讨论的是剂量耐受性和NTCP，**未明确提到18-24Gy的具体范围**
   - 分析：Agent可能基于预训练知识推断了这个范围，或从文章中提取了最大耐受剂量
   - 建议：标记为"基于文献的合理推断"，而非"直接引用"

2. **PubMed PMID 38720427 引用准确** ✅
   - 报告声称：SRS 18Gy，FSRT 21Gy/3f [PubMed: PMID 38720427]
   - 实际文章：明确提到"The median prescription dose...for SRS were 18 Gy...while for FSRT...was 21 Gy"
   - 状态：直接引用，准确无误

**审查结论：**
- OncoKB引用：3/3 ✅ 全部通过
- PubMed引用：5/5 ✅ 真实存在，1个范围推断需标注
- 临床推理：优秀 ✅ 六线治疗判定准确
- 模块适配：优秀 ✅ Module 6正确标记为N/A

## 11. 智能指南检索协议 (Deep Guide Retrieval Protocol)

### 9.1 核心问题分析

**当前Agent的检索策略缺陷：**
- 使用简单的`grep -i "dose\|Gy\|fraction"`过于粗暴
- 未利用指南的结构化信息（目录、章节索引）
- 未根据患者具体情况进行针对性检索
- 未使用PDF视觉探针解析关键表格

**正确检索范式：**
```
理解患者情况 → 查询指南目录 → 定位关键章节 → 视觉解析表格 → 提取具体参数
```

### 9.2 Deep Guide Retrieval Protocol

#### Step 1: 患者情况分析（认知层）

Agent必须首先分析患者输入，识别关键检索维度：

```python
# 关键维度提取
dimensions = {
    "tumor_type": "结直肠癌",  # 决定使用哪个指南
    "metastasis_site": "脑",    # 决定章节
    "treatment_modality": "放疗", # 决定子章节
    "specific_parameter": "SRS剂量" # 决定表格
}
```

**System Prompt强制要求：**
> 在检索指南前，你必须先在Thought中明确：
> 1. 患者肿瘤类型 → 决定使用NCCN/ESMO/ASCO哪个指南
> 2. 转移部位 → 决定查询"Brain Metastases"还是其他章节
> 3. 治疗方式 → 决定查询"Principles of Radiation"还是"Systemic Therapy"
> 4. 具体参数 → 决定需要查找剂量表格还是流程图

#### Step 2: 指南目录智能匹配

**不要直接grep全文，先查目录：**

```bash
# 1. 首先读取指南索引文件
cat workspace/sandbox/Guidelines/GUIDELINES_INDEX.md

# 2. 根据肿瘤类型匹配指南目录
# 示例：结直肠癌脑转移 → 匹配到 NCCN_CNS + 结直肠癌综述

# 3. 在指南内部查找章节索引
# 查找 brain-c（放疗原则）、ltd-1（局限转移）、brain-mets-a（系统治疗）
grep -n "^# .*brain-c\|^# .*ltd-1\|^# .*brain mets" \
    Guidelines/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers/*.md
```

#### Step 3: 章节定位与页码锁定

**关键技巧：使用_raw.json定位页码**

```bash
# 1. 找到PDF原始解析的JSON文件
ls Guidelines/*/parsed_data_raw.json

# 2. 在JSON中搜索关键章节，获取页码
python3 << 'EOF'
import json

with open('Guidelines/NCCN_CNS/parsed_data_raw.json') as f:
    data = json.load(f)

# 查找包含"Principles of Radiation Therapy"的页码
for page in data['pages']:
    if 'Principles of Radiation' in page['text']:
        print(f"放疗原则在第 {page['page_number']} 页")

# 查找包含"15-24 Gy"或剂量表格的页码
for page in data['pages']:
    if any(term in page['text'] for term in ['SRS', 'dose', 'Gy', 'fraction']):
        print(f"剂量信息在第 {page['page_number']} 页")
EOF
```

#### Step 4: PDF视觉探针解析（关键！）

**当Markdown表格混乱时，必须使用视觉解析：**

```bash
# 1. 使用pdf-inspector渲染关键页面
/home/luzhenyang/anaconda3/envs/mineru_env/bin/python \
    skills/pdf-inspector/scripts/render_pdf_page.py \
    Guidelines/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.pdf \
    --pages {页码}

# 2. 分析生成的图片（Agent使用VLM能力）
# 读取图片：workspace/sandbox/NCCN_CNS_page_{页码}.jpg
```

**视觉解析指令（System Prompt中）：**
> 如果你发现Markdown中的剂量表格排版混乱（如"1524 gY"），你必须：
> 1. 使用render_pdf_page.py渲染该页PDF为图片
> 2. 使用你的视觉能力读取图片中的表格
> 3. 正确提取剂量数值（如15-24 Gy，不是1524）
> 4. 引用格式：[Local: NCCN_CNS.pdf, Page X, Visual Probe]

#### Step 5: 参数提取与验证

**提取后必须验证：**

```python
# 验证规则
def validate_dose_citation(dose, citation):
    """
    验证剂量引用的完整性
    """
    checks = {
        "has_specific_value": bool(re.search(r'\d+-\d+', dose)),  # 有具体数值
        "has_unit": "Gy" in dose,  # 有单位
        "has_fractionation": "f" in dose or "fraction" in dose.lower(),  # 有分次
        "cites_guideline": "NCCN" in citation or "ESMO" in citation or "ASCO" in citation,  # 引用指南
        "has_page_or_section": "Page" in citation or "Section" in citation  # 有具体位置
    }
    return all(checks.values())
```

### 9.3 不同场景的检索策略

#### 场景A：放疗剂量查询
```
患者：结直肠癌脑转移，需要SRS剂量

检索路径：
1. 确定使用NCCN CNS指南（脑转移瘤）
2. 查找brain-c章节（放疗原则）
3. 在JSON中锁定"Brain Metastases"相关页码
4. 渲染页面，视觉解析SRS剂量表格
5. 提取：15-24 Gy（基于肿瘤体积）
6. 引用：[Local: NCCN_CNS.pdf, Page X, Section: brain-c]
```

#### 场景B：化疗方案查询
```
患者：NSCLC脑转移，需要培美曲塞剂量

检索路径：
1. 确定使用NCCN NSCLC指南（非CNS指南）
2. 查找系统治疗章节（Systemic Therapy）
3. 定位化疗方案表格（Chemotherapy Regimens）
4. 视觉解析表格，提取：
   - 培美曲塞 500mg/m²，d1，Q21d
5. 引用：[Local: NCCN_NSCLC.pdf, Page X, Table: Chemotherapy]
```

#### 场景C：靶向治疗查询
```
患者：EGFR突变，需要奥希替尼剂量

检索路径：
1. 确定使用NCCN NSCLC指南
2. 查找靶向治疗章节（Targeted Therapy）
3. 定位EGFR突变治疗表格
4. 视觉解析，提取：
   - 奥希替尼 80mg QD
5. 引用：[Local: NCCN_NSCLC.pdf, Page X, Table: EGFR TKIs]
```

### 9.4 System Prompt强制指令

**必须在L3_SYSTEM_PROMPT中添加：**

```markdown
### Deep Guide Retrieval Protocol (强制)

当你需要查找具体剂量或治疗参数时，必须遵循以下协议：

**Phase 1: 情况分析**
- [ ] 明确患者肿瘤类型（决定使用哪个指南）
- [ ] 明确转移部位（决定章节）
- [ ] 明确治疗方式（决定子章节）
- [ ] 明确需要查找的参数类型（决定表格）

**Phase 2: 目录查询**
- [ ] 先读取GUIDELINES_INDEX.md了解可用指南
- [ ] 使用grep -n "^# "查找指南内部章节标题
- [ ] 匹配到具体章节（如brain-c, ltd-1, brain-mets-a）

**Phase 3: 页码锁定**
- [ ] 如果Markdown混乱，使用_raw.json定位页码
- [ ] 执行：python3 -c "import json; ...查找page_number"

**Phase 4: 视觉解析（如需要）**
- [ ] 如果表格排版混乱，使用render_pdf_page.py
- [ ] 渲染页面：python render_pdf_page.py --pages {页码}
- [ ] 使用视觉能力读取图片中的表格

**Phase 5: 引用格式**
- [ ] 指南引用：[Local: {文件名}, Page {页码}, Section: {章节}]
- [ ] 如使用视觉探针：[Local: {文件名}, Page {页码}, Visual Probe]
- [ ] 严禁使用未经验证的PubMed PMID标注指南内容

**违规处理：**
如果检测到以下行为，报告将被退回：
1. 使用简单grep全文搜索，未查目录
2. 找到指南内容但错误标注PubMed引用
3. Markdown表格混乱但未使用视觉探针
4. 引用格式为[Local: ..., Page X]但未实际渲染该页
```

### 9.5 工具增强建议

#### 新增工具：`query_guideline_intelligent`

```python
class IntelligentGuidelineQuery(BaseSkill):
    """
    智能指南查询工具
    根据患者情况自动匹配指南章节
    """

    def execute(self, args: GuidelineQueryInput) -> GuidelineQueryOutput:
        # Step 1: 分析患者情况
        tumor_type = self.analyze_tumor_type(args.patient_input)
        metastasis_site = self.analyze_metastasis_site(args.patient_input)

        # Step 2: 匹配指南
        guideline = self.match_guideline(tumor_type, metastasis_site)

        # Step 3: 查找章节
        sections = self.find_relevant_sections(
            guideline,
            treatment_modality=args.query_type
        )

        # Step 4: 返回结构化结果
        return {
            "guideline_file": guideline.file_path,
            "relevant_sections": sections,
            "suggested_pages": self.get_page_numbers(sections),
            "query_command": f"render_pdf_page.py --pages {sections[0].page}"
        }
```

#### 新增工具：`extract_table_visual`

```python
class VisualTableExtractor(BaseSkill):
    """
    视觉表格提取工具
    使用VLM解析PDF页面中的表格
    """

    def execute(self, args: VisualExtractInput) -> VisualExtractOutput:
        # 1. 渲染PDF页面
        image_path = self.render_pdf_page(
            args.pdf_path,
            args.page_number
        )

        # 2. 使用VLM解析（Agent的多模态能力）
        table_data = self.agent_vlm_analyze(
            image_path,
            prompt="提取表格中的剂量参数，包括：药物名称、剂量、单位、分次、周期"
        )

        # 3. 返回结构化数据
        return table_data
```

### 9.6 执行示例

**示例：查找SRS剂量（患者605525）**

```
Agent Thought:
1. 患者是结直肠癌脑转移 → 使用NCCN CNS指南
2. 需要SRS剂量 → 查询brain-c章节（放疗原则）
3. 在NCCN_CNS.md中搜索brain-c → 找到第308行
4. 但Markdown中剂量显示为"1524 gY"（OCR错误）
5. 决定使用视觉探针：
   - 从_raw.json找到brain-c在第15-18页
   - 执行：render_pdf_page.py --pages 16
   - 视觉解析图片，正确识别：15-24 Gy
6. 引用：[Local: NCCN_CNS.pdf, Page 16, Section: brain-c, Visual Probe]
```

### 9.7 长期收益

这个协议的通用性：
- ✅ 适用于任何肿瘤类型（NSCLC、乳腺癌、黑色素瘤等）
- ✅ 适用于任何部位（脑、肝、骨等）
- ✅ 适用于任何治疗方式（放疗、化疗、靶向、免疫）
- ✅ 不依赖特定问题的硬编码
- ✅ 利用Agent的VLM能力，而非简单文本匹配

**与临时方案的区别：**
| 维度 | 临时方案（补丁） | Deep Guide Retrieval Protocol |
|------|-----------------|------------------------------|
| 扩展性 | 针对SRS剂量硬编码 | 适用于任何参数查询 |
| 智能性 | 简单grep | 结构化检索+视觉解析 |
| 可维护性 | 需要不断打补丁 | 通用协议，无需修改 |
| 准确性 | 依赖文本匹配 | 利用VLM理解表格 |
| 引用质量 | 容易混淆来源 | 明确标注页码和章节 |

## 12. 患者数据处理器 (Patient Data Processor)

### 10.1 设计原则
**患者输入数据处理器 (patient_data_processor)** 是医疗AI评估数据准备的标准化组件，严格遵循以下原则：

1. **输入特征与标签的严格物理隔离**：白名单字段（输入）与黑名单字段（标签）互斥
2. **不可变性（Immutability）**：原始数据只读，绝不修改字段内容
3. **双重信息泄露检查机制**：
   - **第一层 - 字段级检查（代码自动）**：白名单过滤，只保留 `ALLOWED_FEATURES` 中定义的16个字段
   - **第二层 - 语义级检查（Claude Code LLM）**：Claude Code 读取输出文件，通过大语言模型语义理解检查内容
4. **四级验证体系**：预处理 → 处理中 → 后处理 → 集成验证
5. **完整审计追踪**：MD5哈希、时间戳、移除字段记录、语义检查标记

### 10.2 双重信息泄露检查机制

#### 第一层 - 字段级检查（自动）
由 Python 代码自动执行：
```python
ALLOWED_FEATURES = {
    '住院号', '入院时间', '年龄', '性别', '主诉', '现病史', '既往史',
    '头部MRI', '胸部CT', '颈椎MRI', '胸椎MRI', '腰椎MRI',
    '腹盆CT', '腹盆MRI', '腹部超声', '浅表淋巴结超声'
}

BLACKLIST_FEATURES = {
    '入院诊断', '出院诊断', '诊疗经过', '出院时间'  # 严禁混入输入
}
```

**执行方式**：
- 白名单过滤：只保留允许的字段
- 黑名单移除：强制移除敏感字段
- 未知字段警告：记录并忽略未定义字段

#### 第二层 - 语义级检查（Claude Code LLM）
⚠️ **关键要求**：此层检查**必须由 Claude Code 通过大语言模型的语义理解能力执行**，而非简单的关键词匹配。

**Claude Code 需要执行**：
1. **读取生成的输出文件**（如 `patient_640880_input.txt`）
2. **语义分析以下字段内容**：
   - `现病史`：检查是否包含完整治疗经过
   - `主诉`：检查是否包含术后时间和治疗信息
   - `既往史`：检查是否包含可推断治疗线的信息

3. **识别隐含治疗信息**（语义理解，非关键词匹配）：
   - **治疗线数暗示**：如"术后多西他赛+奈达铂化疗4周期"→暗示已完成一线化疗
   - **治疗方式暗示**：如"伽玛刀治疗后半年余"→暗示接受过放疗
   - **疗效评估暗示**：如"病变稳定"、"较前增大"等
   - **用药细节**：即使不在黑名单字段中，也要识别

**语义检查示例**：
```
现病史内容：
"患者2016-3确诊肺癌...术后多西他赛+奈达铂化疗4周期...
2020.4行右额顶转移瘤术...2020-5-25开始阿法替尼靶向治疗至今..."

Claude Code 语义分析：
⚠️ WARNING: 现病史包含完整治疗经过（化疗周期、靶向药物、时间线）
⚠️ WARNING: 可推断患者已接受一线化疗+靶向治疗
```

**审计记录**：
```json
{
  "patient_id": "640880",
  "removed_fields": ["入院诊断", "诊疗经过"],  // 第一层
  "requires_semantic_review": true,             // 第二层标记
  "semantic_review_queue": [                    // 需要LLM检查的字段
    {"field": "现病史", "reason": "文本字段，需要语义级检查"},
    {"field": "主诉", "reason": "文本字段，需要语义级检查"}
  ]
}
```

### 10.3 两层检查的区别

| 维度 | 第一层 - 字段级 | 第二层 - 语义级 |
|------|----------------|----------------|
| **执行者** | Python代码自动 | Claude Code (LLM) |
| **检查对象** | 字段名 | 字段内容 |
| **检查方式** | 白名单/黑名单匹配 | 语义理解分析 |
| **处理能力** | 机械过滤 | 理解上下文含义 |
| **示例** | 移除"入院诊断"字段 | 识别"化疗4周期"暗示治疗线 |
| **记录方式** | `removed_fields` | `semantic_review_queue` |

### 10.4 使用方式

```bash
# 处理单个患者（自动生成语义检查标记）
python -m skills.patient_data_processor.cli process --patient-id 640880

# 批量处理全部患者
python -m skills.patient_data_processor.cli batch

# 验证现有文件（标记需要语义检查的字段）
python -m skills.patient_data_processor.cli verify --file workspace/sandbox/patient_640880_input.txt
```

### 10.5 Claude Code 语义检查工作流

当 processor 标记 `requires_semantic_review: true` 时，Claude Code 必须：

1. **读取输出文件**：
   ```python
   read_file("workspace/sandbox/patient_{id}_input.txt")
   ```

2. **检查标记的字段**：
   对 `semantic_review_queue` 中的每个字段进行语义分析

3. **生成语义审查报告**：
   - 识别隐含的治疗信息
   - 评估信息泄露风险等级
   - 提供处理建议

4. **记录审查结果**：
   更新审计记录，标记已通过语义检查

## 13. Claude Code 专用工具

### 11.1 Patient Data Processor (PDP)

**位置**: `/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/tools/patient_data_processor/`

**用途**: 将原始临床数据（Excel）转换为BM Agent标准化输入格式

**使用者**: Claude Code (你) - **不是给BM Agent用的**

**核心功能**:
1. 双层数据隔离检查
   - 第一层（字段级）：白名单过滤 + 黑名单移除
   - 第二层（语义级）：LLM检查"本次诊疗经过"混入
2. 重复住院号处理：自动添加 `_V2`, `_V3` 后缀
3. 生成详细统计报告

**何时使用**:
- 当用户说"处理患者数据"、"生成输入文件"、"准备测试数据"时
- 当需要转换 `46个病例_诊疗经过.xlsx` 到 `patient_*_input.txt` 时

**使用方法**:
```bash
# 批量处理
conda run -n tiantanBM_agent python -m tools.patient_data_processor.scripts.cli batch \
    --source "patients_folder/46个病例_诊疗经过.xlsx" \
    --output "workspace/sandbox"

# 查看报告
cat workspace/processing_logs/FILTERING_COMPARISON_REPORT.md
```

**关键概念**（必须牢记）:
- ✅ **既往治疗史**: 患者之前接受的治疗（保留）
- ❌ **本次诊疗经过**: 患者本次住院期间的治疗（必须移除）

---

## ⚠️ [重要版本声明] 四方法对比研究数据已归档

**四方法对比研究（第四章至第十三章）已完成并归档，对应 v5.2 扁平架构系统。**

当前运行的系统是 **v6.0 分层架构**，已与 v5.2 完全不同：

| 维度 | v5.2 扁平架构（旧） | v6.0 分层架构（当前） |
|------|-------------------|---------------------|
| 架构 | 单一 Agent + 4 Skills | Orchestrator + 5 SubAgents |
| Agent | 1个扁平Agent | 1 Orchestrator + 4临床SubAgent + 1 Auditor |
| 执行方式 | Agent直接调用Tools | task()委派给专科SubAgent |
| Skills | pdf-inspector, oncokb, pubmed, mdt | 重新分配给不同SubAgent |
| 报告 | 8模块 | 9模块（新增执行摘要） |
| 模型 | qwen3.5-plus | qwen3.6-plus（统一） |

**重要**：
- 第四章至第十三章中的四方法对比研究数据、图表、统计分析均基于 v5.2 系统
- v6.0 系统目前处于调试阶段，尚未完成批量测试和指标验证
- 本文档中提及的所有 "BM Agent" 评估结果均指 v5.2 版本
- v6.0 的性能指标需待调试完成后重新评估

---

## 15. 四方法对比研究 (Four-Method Comparative Study) - v5.2版本（已归档）

### 13.1 研究概述

**研究目的**: 系统比较4种MDT报告生成方法的效率与质量

**对比方法**:
| 方法 | 核心机制 | 外部调用 |
|------|---------|----------|
| Direct LLM V2 | 纯参数知识 | 0次 |
| RAG V2 | 向量检索 + LLM | 1次向量检索 |
| Web Search V2 | 网络搜索 + LLM | 3次搜索 |
| BM Agent | 多轮自主规划 + 工具调用 | 平均44.78次 |

**样本量**: 9例患者 (Set-1 Batch)
**执行日期**: 2026-04-07 至 2026-04-10

### 13.2 效率指标定义

| 指标 | 说明 | 数据来源 |
|------|------|----------|
| **Latency** | 端到端延迟（毫秒） | API返回时间戳 |
| **Input Tokens** | LLM输入token总数 | API usage.prompt_tokens |
| **Output Tokens** | LLM输出token总数 | API usage.completion_tokens |
| **I/O Ratio** | Input/Output比值 | 计算得出 |
| **Environment Calls** | 外部工具/搜索调用次数 | 日志统计 |

**统计口径统一 (V2标准)**:
- **Direct LLM V2**: API `usage.input_tokens` (system + user)
- **RAG V2**: API `usage.prompt_tokens` (system + user + 3 docs)
- **Web Search V2**: API `usage.input_tokens` (system + user + search context)
- **BM Agent**: 结构化日志累加 (多轮交互成本口径，平均27轮LLM调用)

### 13.3 研究结果 (2026-04-10)

#### 表1: 效率指标对比

| 效能指标 | Direct LLM V2 | RAG V2 | WebSearch V2 | BM Agent |
|---------|---------------|--------|--------------|----------|
| 平均延迟±SD (秒) | 97.10±8.68 | 137.49±22.62 | 113.71±9.44 | N/A |
| 输入Tokens (K) | 2.24±1.07 | 3.92±1.14 | 40.25±4.76 | 690.22±357.92 |
| 输出Tokens (K) | 5.20±0.19 | 6.62±0.79 | 5.51±0.42 | 7.67±5.92 |
| I/O Ratio | 0.43±0.22 | 0.59±0.15 | 7.34±1.02 | 118.09±59.61 |
| 环境调用次数 | 0.00±0.00 | 1.00±0.00 | 3.00±0.00 | 44.78±10.86 |

#### 表2: 质量指标对比

| 方法 | CCR (0-4) | PTR (0-1) | MQR (0-4) | CER (0-1) | CPI (0-1) |
|------|-----------|-----------|-----------|-----------|-----------|
| Direct LLM V2 | 1.49±0.18 | 0.00±0.00 | 2.00±0.25 | 0.39±0.08 | 0.42±0.04 |
| RAG V2 | 2.87±0.25 | 0.13±0.07 | 3.42±0.23 | 0.20±0.06 | 0.62±0.04 |
| WebSearch V2 | 3.13±0.20 | 0.39±0.03 | 3.47±0.14 | 0.17±0.05 | 0.71±0.04 |
| **BM Agent** | **3.42±0.32** | **0.98±0.02** | **3.82±0.21** | **0.05±0.05** | **0.93±0.05** |

### 13.4 关键发现

**效率维度**:
- **延迟**: Direct LLM最快(97s)，RAG最慢(137s，含向量检索)
- **输入Tokens**: BM Agent因多轮交互显著更高(690K vs 2-40K)
- **I/O Ratio**: BM Agent(118) >> Web Search(7.34) >> RAG(0.59) > Direct LLM(0.43)
- **环境调用**: BM Agent平均44.78次，体现深度交互特性

**质量维度**:
- **CPI排名**: BM Agent(0.93) > Web Search(0.71) > RAG(0.62) > Direct LLM(0.42)
- **PTR突破**: BM Agent达0.98，接近完全可追溯；Direct LLM为0
- **CER控制**: BM Agent错误率最低(0.05)，Direct LLM最高(0.39)
- **CCR优势**: BM Agent临床一致性显著领先(3.42 vs 1.49)

**效率-质量权衡**:
- **高消耗高回报**: BM Agent消耗最多资源，但质量最优
- **性价比之选**: Web Search在质量和效率间取得平衡
- **基线局限**: Direct LLM虽快但质量差，RAG提升有限

### 13.5 可视化输出

**生成图表** (analysis/final_figures/):
```
效率指标 (5张):
- Figure_E1_Latency_Comparison.png/pdf - 延迟对比
- Figure_E2_Token_Consumption.png/pdf - Token消耗对比  
- Figure_E3_IO_Ratio.png/pdf - I/O比值对比
- Figure_E4_Env_Calls.png/pdf - 环境调用对比
- Figure_E5_Efficiency_Radar.png/pdf - 综合效率雷达图

质量指标 (6张):
- Figure1_four_method_radar_2026-04-10.png/pdf - 四方法雷达图
- Figure2_cpi_four_methods_2026-04-10.png/pdf - CPI分患者对比
- Figure3_four_methods_meansd_2026-04-10.png/pdf - Mean±SD对比
- Figure4_cpi_mean_comparison_2026-04-10.png/pdf - CPI均值对比
- Figure5_improvement_vs_direct_2026-04-10.png/pdf - 相对提升幅度
- Figure6_ptr_comparison_2026-04-10.png/pdf - PTR详细对比
```

**图表规范**:
- 分辨率: 300 DPI
- 格式: PNG + PDF (双格式)
- 标题: 无 (配合论文图注使用)
- 颜色方案: Direct LLM(印度红), RAG(钢蓝), Web Search(海绿), BM Agent(金黄)

### 13.6 核心文件索引

**评估脚本**:
- `baseline/run_set1_baselines.py` - Baseline执行框架
- `analysis/calculate_efficiency_metrics.py` - 效率指标计算
- `analysis/generate_efficiency_visualization.py` - 效率可视化
- `analysis/generate_four_methods_visualization.py` - 四方法可视化

**SKILL文档**:
- `~/.claude/skills/baseline_evaluation/SKILL.md` - Baseline评估规范
- `~/.claude/skills/clinical_expert_review/QUANTITATIVE_METRICS_GUIDE.md` - 量化指标规范

**数据文件**:
- `analysis/efficiency_metrics_v2.json` - 效率指标数据
- `analysis/FINAL_SUMMARY_2026-04-10.md` - 最终汇总报告
- `baseline/set1_results_v2/` - V2版本Baseline结果

### 13.7 统计检验

**Wilcoxon Signed-Rank Test** (BM Agent vs others):
- BM Agent vs Direct LLM: Z=2.668, p=0.008 (显著)
- BM Agent vs RAG: Z=2.668, p=0.008 (显著)
- BM Agent vs Web Search: Z=2.666, p=0.008 (显著)

**效应量** (Cohen's d vs Direct LLM):
- CPI: d=3.42 (大效应)
- PTR: d=4.12 (大效应)
- CER: d=1.89 (大效应)

---

## 14. 重新测试前需修复的问题 (2026-04-05)

### 12.1 分析代码问题

**已删除的过期文件** (2026-04-05):
- `analysis/reports/comparison_report.md` - placeholder报告
- `analysis/UNIFIED_EVALUATION_REPORT_v2.md` - 旧版本
- `analysis/generate_final_visualizations.py` / `generate_figures_v2.py` / `generate_figures_paper_final.py`
- `analysis/revisualize_with_clinical_data.py` / `generate_patient_line_charts.py`
- `analysis/论文Results章节_重构版_v2.md` / `论文Results表格_Word粘贴版.md` / `论文Results章节_Word粘贴版.md`
- `analysis/final_figures/archive_2026-03-26/` - 旧图表归档

**代码审查发现的问题**:
1. `generate_clinical_reviews.py` - CPI计算权重与标准公式不符
2. `generate_final_figures.py` - BASELINE_SUMMARY硬编码估计值
3. `batch_cer_assessment.py` - 使用预估数据而非实际审查
4. `verify_and_calculate_metrics.py` - RAW_SCORES硬编码需更新

### 12.2 重新测试流程

```
1. 运行BM Agent生成新报告 → analysis/samples/{patient_id}/
2. 人工审查CCR/MQR/CER → 更新评分
3. 计算PTR → 自动从报告中提取
4. 运行verify_and_calculate_metrics.py → 生成final_metrics.json
5. 运行generate_final_figures.py → 生成新图表
6. 更新Baseline数据（如有新运行）
```

### 12.3 启动序列更新
每次新会话启动，Claude Code你**必须静默执行以下思考**：
1. 读取并理解 `ARCHITECTURE.md`。
2. 读取 `CHANGELOG.md` 确认最新进度。
3. 牢记绝不能在后台运行 `interactive_main.py` 或测试脚本。
4. **检查是否需要重新测试**（分析代码已清理，准备新批次）。