# TianTan Brain Metastases Agent - AI 协作与开发协议 (Claude Code Protocol)

## 1. 核心宣言 (Manifesto)
**"We build intellectual Agent, not LLM with skill."**
本项目致力于打造具备高度自主规划能力（Autonomous Planning）的医疗多智能体系统，而非被死板代码限制的执行器。

## 2. 最高协作铁律 (The Iron Laws of AI Collaboration)

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

## 3. 架构核心与入口 (Architecture & Entrypoint)

### 3.1 主入口声明
目前系统的唯一合法主入口为：**`interactive_main.py`**。
它是基于 DeepAgents 和 LangGraph 构建的**扁平化架构**单一 Agent 系统，无 Subagents。

### 3.2 运行时架构

```
┌─────────────────────────────────────────────────────────────┐
│                    interactive_main.py                      │
│              (单一 Agent 扁平化架构 v5.1)                     │
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

## 4. 环境与测试规范 (Environment & Commands)

### 4.1 虚拟环境
* **项目专用环境**：`tiantanBM_agent`
* **底层沙盒目录**：`workspace/sandbox/`（所有 L1 抓取的大型 JSON/PDF 必须写入此目录）
* **Skill 备份**：`workspace/sandbox/skills/`（SKILL.md 的隔离备份，防止原文件被误删）

### 4.2 常用命令 (仅供人类在独立终端执行)
* **交互式查房测试**：`conda run -n tiantanBM_agent python interactive_main.py`
* **运行批量评估**：`conda run -n tiantanBM_agent python scripts/run_batch_eval.py --max_cases 1`
* **依赖安装**：`conda run -n tiantanBM_agent pip install <package>`

## 5. 联网与检索规范 (Web Access Rules)
* **绝对禁止使用本地无头浏览器（如 Puppeteer）**。
* **统一使用 Jina Reader 渲染**：如果需要 AI 助手读取网页，请将目标网址拼接在 `https://r.jina.ai/` 之后。

## 6. 项目状态与版本管理 (Project Management Rules)
* **状态对齐**：在开始任何新的代码编写或重构前，必须先读取 `ROADMAP.md` 和 `CHANGELOG.md`。
* **主动打卡**：每完成一个子任务，必须主动修改 `ROADMAP.md`。
* **原子化提交**：功能确认后，使用 `git add .` 和 `git commit -m "..."`，保持 Git Log 纯净。

## 7. 技能调优与 Eval 规范 (Skill Tuning & Eval)

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

## 8. 启动序列 (Boot Sequence)
每次新会话启动，在回答用户任何问题前，Claude Code 你**必须静默执行以下思考**：
1. 读取并理解 `ARCHITECTURE.md`。
2. 读取 `CHANGELOG.md` 确认最新进度。
3. 牢记绝不能在后台运行 `interactive_main.py` 或测试脚本。