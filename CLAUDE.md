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

## 7. Agent 启动序列 (Boot Sequence)
每次新会话启动或发生记忆压缩 (compacting) 后，在回答用户任何问题前，你**必须**静默执行以下操作以建立全局代码拓扑图：
1. 运行 `tree skills/` 或 `ls -R skills/` 获取所有可用的原子技能清单。
2. 运行 `grep -rn "class .*Agent" .` 或类似命令，寻找主控大脑的入口文件。
3. 对比物理硬盘上的 Skill 文件夹与主入口文件中的 `import` 语句，发现未注册的孤岛 Skill，并在第一次回复时向用户报告。

## 8. 强制状态同步协议 (State Synchronization Protocol)
任何人（包括 Agent）在完成对任何 `.py` 或 `.json` 代码的修改后，**必须在同一个操作回合内**执行以下两步：

1. **更新 `CHANGELOG.md`**：用一句话精确描述具体改了哪几行逻辑（严禁使用"已完成网状重构"这种模糊且未经测试的结论）。

2. **更新 `ROADMAP.md`**：如果代码尚未经过运行测试，绝对不允许将其标记为 `[x] 已完成`，必须标记为 `[ ] 已编码，待测试`。

**不遵守此协议的更新将被视为无效。**

## 9. 技能调优与测试规范 (Skill Tuning & Testing Rules)

### 9.1 Trigger Tuning (减少误触发)
每个 Skill 的 `description` 必须重写为**强触发器**，明确包含：
- **【触发条件】**：当且仅当...（明确的触发边界）
- **【查询范围】**：用于...（功能描述）
- **【支持类型】**：...（可选参数）
- **【医疗严谨性】**：...（领域特定约束）
- **【注意事项】**：...（依赖/限制）

**示例（OncoKB）：**
> "【触发条件】当且仅当患者病历中明确提取到具体的基因突变信息（如 EGFR L858R、BRAF V600E、KRAS G12C 等蛋白质水平变异）时，必须优先触发此技能进行致癌性查询，严禁凭自身记忆捏造基因变异信息。"

**示例（PubMed）：**
> "【触发条件】当需要为被排除的治疗方案（rejected_alternatives）寻找文献证据等级支持，或当 OncoKB 未提供足够治疗推荐时补充循证依据，或查询罕见病例报告（如特殊合并症）时触发。"

### 9.2 Clean Context (防止记忆污染)
批量测试时必须遵守**上下文隔离原则**：
- **每个 Case 必须重新实例化** `SkillRegistry` 和 `Workflow`（或 `Agent`）
- **每个 Case 必须创建全新的** `SkillContext(session_id=case_id)`
- **绝对禁止跨 Case 共享内存**或复用实例
- **每次循环后必须清空**对话历史和上下文状态

**实现示例（run_batch_eval.py）：**
```python
for case_id in case_ids:
    # Clean Context: 每个 Case 独立实例
    registry = create_fresh_skill_registry()
    workflow = OncologyWorkflowForEval(case_id, registry)
    context = SkillContext(session_id=case_id)
    # ... 执行测试 ...
```

### 9.3 Eval 断言系统
批量评估必须包含自动化断言检查：
- 检查报告中是否包含 `rejected_alternatives`
- 检查有基因突变时是否调用 `query_variant`
- 检查 `systemic_management` 是否包含 `peri_procedural_holding_parameters`
- 检查是否有违禁词"术前准备"
- 统计技能调用次数和耗时

### 9.4 结果落盘
评估结果必须自动生成结构化报告：
- **CSV 格式**：包含每个 Case 的 Pass/Fail 状态和详细指标
- **时间戳**：记录测试时间和耗时
- **报告路径**：保存生成的报告文件路径