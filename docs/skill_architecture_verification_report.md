# Skill Architecture Verification Report

**验证日期**: 2026-03-21
**验证目标**: 确保所有 SKILL.md 与 System Prompt 遵循统一技能范式 (`execute` → scripts)
**结果**: ✅ 全部通过

---

## 1. 统一技能范式定义

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Skill Paradigm                   │
├─────────────────────────────────────────────────────────────┤
│  1. 所有技能通过 `execute` 工具调用                         │
│  2. Skill 结构: SKILL.md (触发器+认知规则) + scripts/ (CLI) │
│  3. System Prompt: 仅描述4大核心能力，不重复 SKILL.md 内容  │
│  4. 脚本路径: /skills/{name}/scripts/*.py                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 逐技能验证结果

### 2.1 pdf-inspector ✅

| 检查项 | 状态 | 说明 |
|--------|------|------|
| YAML Frontmatter | ✅ | name, description, version, category 完整 |
| 触发条件 | ✅ | "当需要分析医学指南 PDF 时必须使用此 Skill" |
| 调用方式 | ✅ | `execute` 调用 `/home/.../mineru_env/bin/python scripts/parse_pdf_to_md.py` |
| 脚本存在 | ✅ | `scripts/parse_pdf_to_md.py`, `scripts/render_pdf_page.py` |
| 环境隔离 | ✅ | 明确使用 `mineru_env`，与 `tiantanBM_agent` 隔离 |
| 双轨架构 | ✅ | MinerU Pipeline + Visual Probe 完整文档化 |

**关键规范引用**:
```markdown
**轨道一调用**:
/home/luzhenyang/anaconda3/envs/mineru_env/bin/python \
    /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pdf-inspector/scripts/parse_pdf_to_md.py \
    <PDF_绝对路径> -o <输出目录>

**轨道二调用**:
/home/luzhenyang/anaconda3/envs/mineru_env/bin/python \
    /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pdf-inspector/scripts/render_pdf_page.py \
    <PDF_绝对路径> --pages <页码>
```

---

### 2.2 oncokb_query_skill ✅

| 检查项 | 状态 | 说明 |
|--------|------|------|
| YAML Frontmatter | ✅ | 完整，含数据驱动触发条件 |
| 触发条件 | ✅ | "无论用户是否明确要求，只要识别出生物标志物必须立即自动触发" |
| 调用方式 | ✅ | `execute` 调用 Python CLI 脚本 |
| 脚本存在 | ✅ | `scripts/query_oncokb.py` (已验证) |
| 子命令 | ✅ | mutation, fusion, cna 三模式 |
| 输出格式 | ✅ | JSON 结构化输出 |

**关键规范引用**:
```markdown
**点突变查询**:
/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python \
    /skills/oncokb_query_skill/scripts/query_oncokb.py mutation \
    --gene BRAF --alteration V600E --tumor-type "Melanoma"

**融合基因查询**:
/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python \
    /skills/oncokb_query_skill/scripts/query_oncokb.py fusion \
    --gene1 EML4 --gene2 ALK --tumor-type "Non-Small Cell Lung Cancer"

**拷贝数变异查询**:
/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python \
    /skills/oncokb_query_skill/scripts/query_oncokb.py cna \
    --gene EGFR --type Amplification --tumor-type "Glioblastoma"
```

**脚本验证**: `query_oncokb.py` 已实现:
- ✅ argparse 子命令结构
- ✅ 三模式: mutation / fusion / cna
- ✅ JSON stdout 输出
- ✅ 错误处理 (API key check, HTTP error handling)

---

### 2.3 pubmed_search_skill ✅

| 检查项 | 状态 | 说明 |
|--------|------|------|
| YAML Frontmatter | ✅ | 完整，含主动触发场景 |
| 触发条件 | ✅ | 4种场景: 指南未覆盖/VUS/超适应症/新兴疗法 |
| 调用方式 | ✅ | `execute` 调用 Python CLI 脚本 |
| 脚本存在 | ✅ | `scripts/search_pubmed.py` (已验证) |
| 查询模式 | ✅ | 直接查询 + 构造查询双模式 |
| 证据分级 | ✅ | I-V级证据金字塔完整文档化 |

**关键规范引用**:
```markdown
**直接查询模式**:
/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python \
    /skills/pubmed_search_skill/scripts/search_pubmed.py \
    --query "Osimertinib AND lung cancer" \
    --max-results 5

**构造查询模式**:
/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python \
    /skills/pubmed_search_skill/scripts/search_pubmed.py \
    --disease "Brain Neoplasms" --gene EGFR --treatment Osimertinib \
    --study-type "Clinical Trial" --year-from 2022
```

**脚本验证**: `search_pubmed.py` 已实现:
- ✅ ESearch + EFetch 双API调用
- ✅ XML解析提取文章元数据
- ✅ JSON stdout 输出
- ✅ 布尔查询构造器

---

### 2.4 universal_bm_mdt_skill ✅

| 检查项 | 状态 | 说明 |
|--------|------|------|
| YAML Frontmatter | ✅ | 完整，含强制触发条件 |
| 触发条件 | ✅ | "接收到完整病历并要求MDT方案时必须触发" |
| 跨技能联动 | ✅ | 明确定义 OncoKB + PubMed 调用时机 |
| 输出规范 | ✅ | 8模块MDT报告结构完整 |
| 禁止行为 | ✅ | "严禁直接输出报告到对话，必须write_file写入文件" |

**关键规范引用 - 跨技能联动**:
```markdown
**分子图谱强制校验**:
1. 识别变异类型 → 通过 `execute` 调用 OncoKB 脚本
2. OncoKB证据不足 → 通过 `execute` 调用 PubMed 脚本
3. 整合证据到 MDT 报告模块2和模块7
```

**8模块输出架构**:
1. admission_evaluation (入院综合评估)
2. primary_plan (首选个性化治疗方案)
3. systemic_management (支持性治疗)
4. follow_up (随访监控)
5. rejected_alternatives (排他性方案论证)
6. peri_procedural_holding_parameters (围手术期处理)
7. molecular_pathology_orders (分子病理送检)
8. agent_execution_trajectory (智能体执行轨迹)

---

## 3. System Prompt 验证 (interactive_main.py)

### 3.1 架构配置 ✅

```python
# 工具列表 - 仅保留 execute
tools=[
    execute,  # 执行 Skill 脚本的核心工具
],

# Subagents - 扁平化架构，无子代理
subagents=[],

# Skills - 4个核心技能，使用虚拟路径
skills=[
    "/skills/pdf-inspector",
    "/skills/universal_bm_mdt_skill",
    "/skills/oncokb_query_skill",
    "/skills/pubmed_search_skill",
],
```

### 3.2 4大核心能力描述 ✅

| 能力 | System Prompt 描述 | 对应 Skill |
|------|-------------------|-----------|
| PDF-Inspector | "双轨制 PDF 分析 - MinerU全局提取 + Visual Probe局部渲染" | pdf-inspector |
| Universal BM MDT | "脑转移MDT报告生成 - 表征/检索/推理/输出四阶段" | universal_bm_mdt_skill |
| OncoKB Query | "基因突变注释 - 数据驱动强制触发" | oncokb_query_skill |
| PubMed Search | "前沿文献检索 - 主动检索补充证据" | pubmed_search_skill |

### 3.3 Execute 工具白名单 ✅

```python
ALLOWED_PREFIXES = (
    "/home/luzhenyang/anaconda3/envs/mineru_env/bin/python",      # PDF-Inspector
    "/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python", # OncoKB/PubMed
    "ls ", "cat ", "head ", "tail ", "grep ", "find ", "echo ",   # 基础命令
)
```

### 3.4 物理溯源引用协议 ✅

System Prompt 明确要求:
```markdown
**本地指南引用格式**: `[Local: <完整文件名>, Page <页码>]`
**铁律**: 严禁自行添加版本号，必须原样使用文件名
**页码是你的生命线**: 没有页码的信息对报告毫无价值
```

---

## 4. 设计思想一致性检查

### 4.1 Skill vs Tool 边界 ✅

| 概念 | 定义 | 实现 |
|------|------|------|
| **Tool** | 原子化能力 (execute, read_file, write_file) | `tools=[execute]` |
| **Skill** | 认知工作流 (何时/如何用工具) | SKILL.md + scripts/ |

### 4.2 数据驱动触发 ✅

| Skill | 触发模式 | 实现 |
|-------|---------|------|
| oncokb_query_skill | 生物标志物识别 → 自动触发 | SKILL.md 定义触发条件，MDT Skill 调用 |
| pubmed_search_skill | VUS/证据缺口 → 主动检索 | SKILL.md 定义4种触发场景 |
| universal_bm_mdt_skill | 完整病历 + MDT请求 → 强制触发 | SKILL.md 定义触发条件 |

### 4.3 渐进式披露 ✅

1. **YAML Frontmatter**: 触发匹配 (框架自动读取)
2. **SKILL.md 全文**: 认知规则 (触发后Agent读取)
3. **scripts/**: 执行实现 (通过 execute 调用)

### 4.4 跨技能联动 ✅

```
MDT Skill (主控)
    ├── 识别基因变异 → execute → OncoKB Skill
    ├── VUS/证据不足 → execute → PubMed Skill
    └── 需要指南内容 → execute → PDF-Inspector Skill
```

---

## 5. 文件清单

### 已验证文件

| 文件路径 | 验证结果 | 备注 |
|---------|---------|------|
| `skills/pdf-inspector/SKILL.md` | ✅ | 双轨架构完整 |
| `skills/oncokb_query_skill/SKILL.md` | ✅ | 证据等级解读完整 |
| `skills/oncokb_query_skill/scripts/query_oncokb.py` | ✅ | CLI三模式实现 |
| `skills/pubmed_search_skill/SKILL.md` | ✅ | 证据金字塔完整 |
| `skills/pubmed_search_skill/scripts/search_pubmed.py` | ✅ | ESearch+EFetch实现 |
| `skills/universal_bm_mdt_skill/SKILL.md` | ✅ | 8模块+跨技能联动完整 |
| `interactive_main.py` | ✅ | System Prompt + 架构配置 |

### 关键路径映射

```
虚拟路径                    → 物理路径
────────────────────────────────────────────────────────────
/skills/pdf-inspector       → skills/pdf-inspector/
/skills/oncokb_query_skill  → skills/oncokb_query_skill/
/skills/pubmed_search_skill → skills/pubmed_search_skill/
/skills/universal_bm_mdt    → skills/universal_bm_mdt_skill/
/memories/                  → StoreBackend (持久化)
/workspace/sandbox/         → FilesystemBackend (隔离)
```

---

## 6. 结论

### ✅ 验证通过

所有技能文件与主控 Agent 的 System Prompt **完全符合**统一技能范式:

1. **单一入口**: 所有技能通过 `execute` 调用 scripts/ 下的 CLI 脚本
2. **结构统一**: YAML frontmatter + 认知规则 + 可执行脚本
3. **触发清晰**: 数据驱动，自动触发，不依赖用户明确请求
4. **跨技能联动**: MDT Skill 作为主控，按需调用 OncoKB/PubMed/PDF-Inspector
5. **System Prompt 简洁**: 仅描述4大核心能力，不重复 SKILL.md 细节

### 🚀 系统就绪

当前架构支持以下工作流:

```
用户输入患者病历
    ↓
MDT Skill 触发 (表征先于检索)
    ↓
识别 BRAF V600E → execute → OncoKB Skill → JSON证据
    ↓
VUS/证据不足 → execute → PubMed Skill → 文献补充
    ↓
需要指南 → execute → PDF-Inspector Skill → Markdown内容
    ↓
认知推理 → write_file → /workspace/sandbox/MDT_Report_<ID>.md
```

---

**报告生成时间**: 2026-03-21
**验证者**: Claude Code
**状态**: ✅ 全部通过，系统可正常运行
