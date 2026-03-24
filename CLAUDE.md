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

## 8. 报告质量审查协议 (Report Quality Review Protocol)

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

## 9. 智能指南检索协议 (Deep Guide Retrieval Protocol)

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

## 10. 启动序列 (Boot Sequence)
每次新会话启动，在回答用户任何问题前，Claude Code 你**必须静默执行以下思考**：
1. 读取并理解 `ARCHITECTURE.md`。
2. 读取 `CHANGELOG.md` 确认最新进度。
3. 牢记绝不能在后台运行 `interactive_main.py` 或测试脚本。