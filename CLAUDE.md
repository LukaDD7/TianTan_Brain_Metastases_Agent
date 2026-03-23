# TianTan Brain Metastases Agent 项目指南

## 1. 项目背景与目标
本项目是一个用于肿瘤脑转移辅助决策的医疗多智能体系统。核心任务是处理长文本电子病历、多模态医疗数据，并进行严谨的循证推理。

## 2. 架构核心 (Architecture Core)

### 2.1 Deep Agent 框架（核心框架）
* **使用 `deepagents.create_deep_agent`** 作为核心入口
* 框架基于 LangGraph runtime，提供内置的：
  - Skills 支持（SKILL.md 目录结构）
  - File System 工具
  - Human-in-the-loop (interrupt_on)
  - Long-term memory (checkpointer)

### 2.2 BaseSkill 范式
* 所有工具必须继承自 `core/skill.py` 中的 `BaseSkill`
* 每个 Skill 必须显式定义 Pydantic Input Schema
* Skill 的 `description` 必须极其详尽（这是给 Agent 大脑看的说明书）

### 2.3 工具分层
| 层级 | 说明 |
|------|------|
| Deep Agent | 核心框架 (create_deep_agent) |
| BaseSkill | 原子化工具 (PDF Inspector, OncoKB, PubMed) |
| LangChain @tool | 封装 BaseSkill 为 LangChain Tool |

### 2.4 医疗严谨性
* 在处理诊断、用药建议时，必须调用 `OncoKB` 或 `PubMed` 寻找依据
* 禁止凭空捏造基因变异信息或药物剂量

## 3. Claude Code 与项目的关系

### 3.1 角色定位
* **Claude Code** 是本项目的**开发助手**和**代码审查者**
* **Deep Agent (qwen3.5-plus)** 是运行时的**推理引擎**

### 3.2 协作模式
1. Claude Code 负责：编写代码、调试、代码审查、提交
2. Deep Agent 负责：运行时推理、Tool-calling、报告生成

### 3.3 调试时的分工
* **代码逻辑错误** → Claude Code 修复
* **Agent 行为异常** → 调整 System Prompt 或 Tool 定义
* **验证失败** → 检查 validate_report.py 的检查规则

## 4. 代码规范 (Coding Standards)
* 所有 Python 代码使用 Type Hints
* 使用 Pydantic v2 进行输入验证

## 5. 虚拟环境 (Virtual Environment)
* **项目专用环境**：`tiantanBM_agent`
* **启动命令**：`conda run -n tiantanBM_agent python <script.py>`
* **依赖安装**：`conda run -n tiantanBM_agent pip install pandas openpyxl`

## 6. 常用调试命令 (Commands)
* 运行批量评估：`conda run -n tiantanBM_agent python scripts/run_batch_eval.py --max_cases 1`
* 运行全量测试：`pytest tests/`
* 测试单个 Skill：`python -m core.skill_tester [skill_name]`

## 7. 联网与检索规范 (Web Access Rules)
* **绝对禁止使用本地无头浏览器（如 Puppeteer）**
* **统一使用 Jina Reader 渲染**：将目标网址拼接在 `https://r.jina.ai/` 之后

## 8. 项目状态与版本管理规范 (Project Management Rules)
* **状态对齐**：在开始任何新的代码编写或重构前，必须先读取 `ROADMAP.md`
* **主动打卡**：每完成一个子任务，必须主动修改 `ROADMAP.md`
* **原子化提交**：使用 `git add .` 和 `git commit -m "..."`

## 9. Agent 启动序列 (Boot Sequence)
每次新会话启动或发生记忆压缩后，在回答用户任何问题前，你**必须**：
1. 运行 `tree skills/` 获取所有可用的原子技能清单
2. 检查 main_oncology_agent_v2.py 是否使用 Deep Agent 架构
3. 确认代码与文档一致

## 10. 技能调优与测试规范 (Skill Tuning & Testing Rules)

### 10.1 Trigger Tuning
每个 Skill 的 `description` 必须重写为**强触发器**：
- **【触发条件】**：当且仅当...（明确的触发边界）
- **【查询范围】**：用于...
- **【医疗严谨性】**：领域特定约束

### 10.2 Clean Context
批量测试时必须遵守**上下文隔离原则**：
- **每个 Case 必须重新实例化** Agent
- **每个 Case 必须创建全新的** `SkillContext(session_id=case_id)`
- **使用不同的 thread_id** 避免状态污染

### 10.3 Eval 断言系统
批量评估必须包含自动化断言检查：
- 检查报告中是否包含 `rejected_alternatives`
- 检查 `systemic_management` 是否包含 `peri_procedural_holding_parameters`
- 检查是否有违禁词"术前准备"
- 检查是否有 NCCN/EANO citation

### 10.4 结果落盘
评估结果必须自动生成结构化报告：
- **CSV 格式**：包含每个 Case 的 Pass/Fail 状态
- **时间戳**：记录测试时间和耗时
- **报告路径**：保存生成的报告文件路径