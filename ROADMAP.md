# TianTan Brain Metastases Agent 项目路线图

> 最后更新：2026-03-04
> 版本：v2.3.0

---

## 项目愿景

构建一个符合 **AgentSkills 规范** 的医疗智能体系统，用于肿瘤脑转移的多学科诊疗 (MDT) 辅助决策。

**核心原则：**
- 零 LangChain/LangGraph 依赖
- 极简 OpenClaw / Skill 范式
- 渐进式披露 (Progressive Disclosure)
- 医疗循证严谨性

---

## v2.0 基础重构 (2026-03-03)

### 已完成 ✅

- [x] **BaseSkill 架构升级**
  - [x] 引入 Pydantic v2 强类型约束
  - [x] 添加 `SkillContext` 跨技能上下文类
  - [x] 实现 `execute_with_retry()` 指数退避机制
  - [x] 添加 `SkillCallRecord` 审计追踪
  - [x] 统一异常类 (`SkillExecutionError`, `SkillValidationError`)

- [x] **SKILL.md 规范引入**
  - [x] 为 `pdf_inspector` 创建 SKILL.md
  - [x] 为 `clinical_writer` 创建 SKILL.md
  - [x] YAML frontmatter 元数据 (name/description/version/metadata)

- [x] **旧 Skill 逻辑升级**
  - [x] `parse_pdf.py` 重写为 `PDFInspector` 类
  - [x] `generate_report.py` 重写为 `MDTReportGenerator` 类
  - [x] `validate_report.py` 重写为 `ReportValidator` 类
  - [x] 所有 Skill 显式接收 `SkillContext`

- [x] **工程文档完善**
  - [x] 创建 `main_oncology_agent_v2.py` 使用示例
  - [x] 创建 `ROADMAP.md` 项目路线图
  - [x] 创建 `CHANGELOG.md` 更新日志

- [x] **物理目录三层结构改造** (AgentSkills 规范)
  - [x] 移动执行代码到 `scripts/` 子目录
  - [x] 创建 `references/` 存放诊疗指南/表单模板
  - [x] 创建 `examples/` 存放使用示例
  - [x] 更新 `SkillRegistry.from_directory()` 适配新结构 (2026-03-04)

- [x] **工程文档完善** (2026-03-04)
  - [x] 创建 `requirements.txt` 依赖管理
  - [x] 更新 `.gitignore` 配置
  - [x] 更新 `ROADMAP.md` 和 `CHANGELOG.md`

### 待完成 📋 - 下一阶段重点

- [x] **接入 OncoKB API** (2026-03-04)

- [x] **接入 PubMed API** (2026-03-04)

- [ ] **Skills 整合与端到端调试** (优先级：最高 - 下一阶段核心任务)
  - [ ] 将全新升级的 Skills 整合进 `main_oncology_agent_v2.py`
  - [ ] 端到端流程调试
  - [ ] 结合临床医生反馈优化主 Agent 推理 Prompt
  - [ ] 测试 10 个真实病历 Case

- [ ] **医疗数据类型 Schema 库** (优先级：中)
  - [ ] 完善 `pdf_report_schema()`
  - [ ] 实现 `dicom_series_schema()` (Cancelled - 超出单模态范围)
  - [ ] 实现 `vcf_file_schema()`
  - [ ] 实现 `pathology_wsi_schema()` (Cancelled - 超出单模态范围)

- [ ] **单元测试覆盖** (优先级：低 - 延后)
  - [ ] `core/skill.py` 单元测试
  - [ ] `SkillContext` 测试
  - [ ] `PDFInspector` 集成测试
  - [ ] `MDTReportGenerator` 验证测试

- [ ] **CI/CD 集成** (优先级：低 - 延后)
  - [ ] GitHub Actions 工作流配置
  - [ ] pytest 自动执行
  - [ ] 代码覆盖率报告

---

## v2.1 能力扩展 (规划中) - 单模态文本决策

> 注：本项目专注于单模态文本决策，不考虑影像等多模态数据。以下"多模态"相关规划已取消。

- [ ] **长文本病历结构化**
  - [ ] 电子病历 (EHR) 解析 Skill
  - [ ] 时序信息提取 (治疗线数、疗效评估)
  - [ ] 医学术语标准化 (ICD-10/SNOMED CT)

- [ ] **诊疗指南知识库**
  - [ ] NCCN 指南结构化存储
  - [ ] ESMO 指南结构化存储
  - [ ] CSCO 指南结构化存储
  - [ ] 指南版本追踪与更新

- [ ] **HITL (Human-In-The-Loop) 机制**
  - [ ] 关键决策点人工确认
  - [ ] 药物剂量审核流程
  - [ ] 放疗靶区确认流程

~~- [ ] **多模态影像分析** (Cancelled - 超出单模态 MVP 范围)
  - ~~[ ] 接入视觉模型分析提取的医学影像~~
  - ~~[ ] DICOM 序列解析 Skill~~
  - ~~[ ] 病理切片 (WSI) 分析 Skill~~

---

## v3.0 多智能体协同 (远期规划)

- [ ] **多 Agent 架构**
  - [ ] 诊断 Agent (负责病情分析)
  - [ ] 用药 Agent (负责药物推荐)
  - [ ] 放疗 Agent (负责放疗规划)
  - [ ] 质控 Agent (负责合规审核)

- [ ] **Agent 间通信协议**
  - [ ] 定义 Agent 消息格式
  - [ ] 实现 Agent 握手 (handoff) 机制
  - [ ] 共享上下文同步

- [ ] **长期记忆系统**
  - [ ] 患者病史跨会话追踪
  - [ ] 诊疗决策历史记录
  - [ ] 医学知识向量检索

---

## 技术债务

| 债务项 | 影响 | 优先级 |
|--------|------|--------|
| 旧 `main_oncology_agent.py` 未迁移 | 代码重复 | 中 |
| ~~`SkillRegistry.from_directory()` 未适配三层结构~~ | ~~无法自动加载~~ | ~~高~~ ✅已解决 |
| ~~无单元测试~~ | ~~回归风险~~ | ~~高~~ (已延后) |
| ~~无依赖管理 (requirements.txt)~~ | ~~部署困难~~ | ~~中~~ ✅已解决 |
| ~~无 `.gitignore` 配置~~ | ~~可能提交敏感文件~~ | ~~中~~ ✅已解决 |
| ~~OncoKB/PubMed 集成未测试~~ | ~~API 调用风险~~ | ~~高~~ ✅已测试 |

---

## 参考规范

- [AgentSkills Specification](https://github.com/anthropics/anthropic-skills)
- [OpenClaw Skills](https://github.com/samueles/openclaw)
- [CLAUDE.md](./CLAUDE.md) - 项目架构红线

---

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-03-04 | v2.3.0 | 聚焦单模态 MVP：删除多模态影像分析规划；明确下一阶段任务为 Skills 整合与临床验证 (10 个真实病历测试)；单元测试延后 |
| 2026-03-04 | v2.2.0 | 接入 PubMed API:4 种查询类型、PubMedClient 封装、完整文档；修复 SkillRegistry.from_directory() 适配三层结构；创建 requirements.txt 和 .gitignore |
| 2026-03-03 | v2.1.0 | 接入 OncoKB API：6 种查询类型、API 客户端封装、完整文档 |
| 2026-03-03 | v2.0.0 | 基础重构：Pydantic + SkillContext + 重试机制 + 物理三层结构 |
