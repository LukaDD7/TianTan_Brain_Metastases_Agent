# TianTan Brain Metastases Agent 项目指南

## 1. 项目背景与目标
本项目是一个用于肿瘤脑转移辅助决策的医疗多智能体系统。核心任务是处理长文本电子病历、多模态医疗数据，并进行严谨的循证推理。

## 2. 架构红线 (Architecture Rules) - 必须严格遵守！
* **绝对禁止使用 LangChain / LangGraph 等重度封装框架。**
* **采用极简 OpenClaw / Skill 范式：** 所有工具必须原子化、解耦，并继承自 `core/skill.py` 中的 `BaseSkill`。
* **统一的 Schema 定义：** 每个 Skill 必须显式定义 Pydantic Input Schema，并且 `description` 必须极其详尽（包含医疗专业名词解释），因为这是给 Agent 大脑看的说明书。
* **医疗严谨性：** 在处理诊断、用药建议时，不要凭空捏造。必须优先考虑调用 `OncoKB` 或 `PubMed` API 等外部 Skill 寻找依据。

## 3. 代码规范 (Coding Standards)
* 所有 Python 代码使用 Type Hints。
* 每个被重构的 Skill 必须配合编写 pytest 单元测试（存放在 `tests/` 目录下）。

## 4. 常用调试命令 (Commands)
* 运行全量测试：`pytest tests/`
* 测试单个 Skill：`python -m core.skill_tester [skill_name]`

## 5. 联网与检索规范 (Web Access Rules)
* **绝对禁止使用本地无头浏览器（如 Puppeteer）**：由于当前服务器的 Linux 内核版本限制和缺少图形显示组件，本地渲染必定会导致沙盒崩溃。
* **统一使用 Jina Reader 渲染**：当你需要访问任何网页或 API 文档时，必须使用自带的网络请求工具（如 `curl` 或 `fetch`），请求经过云端渲染的聚合链接。
* **URL 格式要求**：将目标网址拼接在 `https://r.jina.ai/` 之后。例如，要访问 `https://example.com`，你必须请求 `https://r.jina.ai/https://example.com`。

## 6. 项目状态与版本管理规范 (Project Management Rules)
* **状态对齐**：在开始任何新的代码编写或重构前，必须先读取 `ROADMAP.md`，确认当前任务在整体规划中的位置。
* **主动打卡**：每完成一个子任务，必须主动修改 `ROADMAP.md`，将对应的 `[ ]` 改为 `[x]`，并更新 `CHANGELOG.md` 记录本次变动。
* **原子化提交**：在修改完一批具备逻辑完整性的代码后，必须使用 `git diff` 检查改动，并执行 `git add .` 和 `git commit -m "..."`。Commit Message 必须符合 Conventional Commits 规范（如 `feat:`, `refactor:`, `fix:`）。