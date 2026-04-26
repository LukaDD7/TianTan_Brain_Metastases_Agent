# TianTan Brain Metastases Agent - AI 协作与开发协议 (v6.0.20250424)

## 1. 核心宣言 (Manifesto)
**"We build intellectual Agent, not LLM with skill."**
本项目致力于打造具备高度自主规划能力与临床循证逻辑的医疗多智能体系统。

## 2. 架构定义 (v6.0 Dispatcher-Arbitrator Architecture)

### 2.1 角色分工 (Sub-agent Matrix)
系统采用 **1 主席 + 6 专家** 的分层架构，各专家通过 Pydantic Schema 实现物理航道隔离：

1.  **MDT Orchestrator (主席/调度员)**:
    - 职责：剥夺临床执行权，仅负责任务分发、证据等级仲裁及报告合成。
    - 仲裁逻辑：`Selection_Priority = (EBM_Level_Score) * (Clinical_Priority_Weight)`。
2.  **Imaging-Specialist (影像专家)**:
    - 职责：参数化提取病灶大小、数量、中线移位、功能区受累等客观几何数据。
3.  **Primary-Oncology-Specialist (原发系统专家)**:
    - 职责：判定原发癌种，评估全身控制状态及药物 CNS 穿透性 (CNS Penetrance)。
4.  **Neurosurgery-Specialist (神外专家)**:
    - 职责：仅评估手术指征及围手术期风险。
5.  **Radiation-Specialist (放疗专家)**:
    - 职责：制定 SRS/WBRT 方案，必须执行双轨验证。
6.  **Molecular-Pathology-Specialist (病理专家)**:
    - 职责：解读突变，对接 OncoKB 实时证据等级。
7.  **Evidence-Auditor (证据审计专家)**:
    - 职责：三重审计（物理存在、支撑一致性、EBM等级校准）。

### 2.2 核心协议 (Core Protocols)
- **零执行协议 (Zero-execution Policy)**: Orchestrator 严禁直接给出临床建议。
- **证据主权协议 (Evidence Sovereignty)**: 所有临床声明必须包含 `claim`, `citation`, `source_core_summary`, `evidence_level`。
- **自进化机制**: 系统通过 `StoreBackend` 记录高等级证据修正低等级建议的先例，实现知识闭环。

---

## 3. 协作铁律 (The Iron Laws)
1. **严禁无头执行**: 禁止在后台运行 `interactive_main.py`。
2. **引用零容忍**: 严禁伪造。Auditor 拥有一票否决权。
3. **安全推送**: Push 前必须核查 `.env` 和敏感路径。

## 4. 运行环境 (v6.0)
- **环境名称**: `tiantanBM_agent`
- **主入口**: `interactive_main.py`
- **Schema 定义**: `schemas/v6_expert_schemas.py`

---

## 6. 临床指南管理规范 (Guideline Management)

### 6.1 指南版本同步要求
**所有指南必须保持日期一致性（统一为2024-2025年版），禁止混用不同时期的指南。**

### 6.2 当前指南状态

**Practice Guidelines (需下载更新版):**
| 指南 | 当前版本 | 目标版本 | 状态 |
|------|---------|---------|------|
| NCCN CNS Cancers | v3.2024 | v3.2024 | ✅ 已就绪 |
| Congress of Neurological Surgeons | June 2025 | June 2025 | ✅ 已就绪 |
| EANO-ESMO Brain Metastasis | © 2021 | 2024 | ❌ 需下载 |
| ESMO Metastatic Breast Cancer | © 2021 | 2024 | ❌ 需下载 |
| ESMO Oncogene-addicted NSCLC | © 2023 | 2024 | ❌ 需下载 |
| ESMO Non-Oncogene-addicted NSCLC | © 2023 | 2024 | ❌ 需下载 |
| ASCO-SNO-ASTRO Brain Mets | 2022 | 2024 | ❌ 需下载 |
| Radiation Therapy for Brain Mets | 2008-2020 | 2024 | ❌ 需下载 |

**完全缺失需下载:**
| 指南 | 目标版本 |
|------|---------|
| ESMO Colorectal Cancer CPG | 2024 |
| ESMO Melanoma CPG | 2024 |
| ESMO Gastric Cancer/GEJ CPG | 2024 |
| ESMO Ovarian Cancer CPG | 2024 |

### 6.3 指南来源优先级
1. **Annals of Oncology** (https://www.annalsoncology.org) — ESMO指南
2. **ASCO Guidelines** (https://ascopubs.org/guidelines) — ASCO指南
3. **ESMO Guidelines** (https://www.esmo.org/guidelines) — ESMO主页
4. **NCCN Guidelines** (https://www.nccn.org) — NCCN指南

### 6.4 下载后操作
1. 保存到 `/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/Guidelines/脑转诊疗指南/Practice_Guideline_metastases/`
2. 执行文本转换: `pdftotext {filename}.pdf {filename}.txt`
3. 验证日期一致性

---

## 7. 网络访问与搜索回退规则 (Web Access Fallback)

### 5.1 WebSearch 工具优先级
当需要搜索外部信息时，按以下优先级尝试：

1. **`mcp__MiniMax__web_search`** — 首选，通过 MiniMax API 搜索（走 MiniMax 代理）
2. **`mcp__WebSearch__bailian_web_search`** — 次选，通过阿里百炼/通义搜索
3. **`curl` Bash 命令** — 终极回退，直接 curl 目标 URL
4. **放弃搜索** — 如果以上全部失败，标注 `[无法验证]` 并继续

### 5.2 WebFetch 工具失效时的处理
`WebFetch` 工具在以下情况可能失效：
- 目标域名被企业安全策略屏蔽（github.com, docs.langchain.com 等）
- 云服务器 IP 被目标网站加入黑名单或 rate limit

**回退策略**：
1. 尝试用 `curl -sL --max-time 30 <url>` 直接在 Bash 中获取页面内容
2. 如果 curl 也失败，放弃该信息源，在响应中标注 `[WebFetch unavailable: <domain>]`
3. **严禁无休止地反复尝试同一失效的 URL**

### 5.3 禁止行为
- **严禁**使用 Puppeteer/Selenium/Playwright 等无头浏览器进行网页抓取
- **严禁**在 WebFetch/WebSearch 失败后尝试 VPN 代理配置（除非用户明确要求）
- 如果所有网络工具都失效，**直接告知用户**并建议手动提供链接内容

### 5.4 Jina Reader 使用
如需渲染网页为 Markdown，优先使用 Jina Reader：
```bash
curl -sL "https://r.jina.ai/https://target-url.com"
```
如果目标服务器拒绝（返回非200），标记为 `[Jina blocked]` 并回退到上述策略。
