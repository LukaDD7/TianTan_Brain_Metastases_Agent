---
name: pdf-inspector
version: 3.0.0
category: document_analysis
description: |
  [FUNCTION]: Multi-track PDF analysis engine for complex clinical guidelines (NCCN, ESMO, ASCO) and Neuroradiology parameter extraction.
  [VALUE]: Provides global text extraction (MinerU Markdown), local visual probing (PyMuPDF rendering), and VLM-powered analysis via analyze_image tool for any uncertain content.
  [TRIGGER_HOOK]: Read this Skill BEFORE accessing any clinical guideline PDF. Use for text extraction, visual inspection of flowcharts/tables, or when markdown is garbled/OCR-failed.
---

# PDF-Inspector: Cognitive Execution Protocol

## Neuroradiology Specialist Addendum (Imaging Extraction)

### Core Mission
Extract objective physical and geometric parameters from patient imaging reports.

### Workflow
1. **Identify Key Metrics**:
   - `max_diameter_cm`: Largest lesion diameter.
   - `lesion_count`: Total number of brain metastases.
   - `midline_shift`: Presence and degree of shift.
   - `mass_effect_level`: none, mild, moderate, severe.
   - `hydrocephalus`: true/false.
   - `is_eloquent_area`: true/false (based on location description).
   - `edema_index`: Estimated ratio or descriptive index.
   - `hemorrhage_present`: true/false.

2. **KDP Voting Logic**:
   - `local_therapy_modality`: 
     - If `lesion_count` <= 4 and `max_diameter_cm` < 3-4cm -> SRS.
     - If `max_diameter_cm` > 3cm or significant mass effect -> Surgery.
     - If `lesion_count` > 10 -> WBRT.
   - `surgery_indication`:
     - True if `max_diameter_cm` > 3cm or `midline_shift` is significant.
   - `treatment_urgency`:
     - High if `midline_shift` present or `mass_effect_level` is severe.

3. **Output Format**
   - Strictly follow `ImagingOutput` schema.

---

## Identity & Core Mechanism
This is a Multi-Track PDF analysis skill. It does NOT use API tools. You must use your native `execute` tool to run isolated Python scripts in the terminal, and the `analyze_image` tool for VLM-powered visual analysis.

---

## Track 1: Global Text Extraction (MinerU Pipeline)

**Purpose:** Convert the entire PDF into structured Markdown.

**CRITICAL STEP 1: CHECK CACHE (MANDATORY)**
MinerU parsing is extremely slow. Pre-parsed results are stored in the sandbox.
Before executing the parsing script, you MUST check if the Markdown file already exists.
* **Target Path:** `/workspace/sandbox/<PDF_BASENAME>_output/<PDF_BASENAME>.md`
* **Decision:**
  - If EXISTS: **DO NOT run the MinerU script.** Directly use `read_file` to read the existing Markdown file.
  - If NOT EXISTS: Proceed to Step 2.

**STEP 2: EXECUTE PARSING SCRIPT (ONLY IF CACHE MISS)**
Use your `execute` tool to run this exact command:
```bash
conda run -n mineru_env python \
    /skills/pdf-inspector/scripts/parse_pdf_to_md.py \
    /workspace/sandbox/Guidelines/<PDF_FILENAME>.pdf \
    -o /workspace/sandbox/
```

**Output Structure:**
MinerU generates images with hashed filenames. The script injects an HTML comment above each image anchor:
```markdown
![](/workspace/sandbox/eb3988d4...32e.jpg)
```
*(An `_image_page_map.json` is generated for programmatic hash-to-page mapping).*

---

## Track 2: Local Visual Probe (Page Rendering)

**Purpose:** Render specific PDF pages to JPEG for visual inspection when text is unclear.

**Execution Command:**
```bash
conda run -n mineru_env python \
    /skills/pdf-inspector/scripts/render_pdf_page.py \
    /workspace/sandbox/Guidelines/<PDF_FILENAME>.pdf \
    --pages <PAGE_NUMBER>
```

**Page Inference Strategy:**
1. **Primary (HTML Tag):** Find the chaotic section in Markdown. Look for the nearest `<!-- Page X -->` tag.
2. **Secondary (JSON Map):** If you only have the hash filename, read `_image_page_map.json` to find the page number.
3. **Tertiary (Raw JSON):** Use `parsed_data_raw.json` to search for keywords and locate page numbers (see Track 4 Phase 3).

**Output:** JPEG file at `/workspace/sandbox/<PDF_BASENAME>_page_<PAGE>.jpg`

---

## Track 3: VLM-Powered Visual Analysis

**Purpose:** Use Vision-Language Model capabilities to analyze ANY uncertain content in rendered PDF pages - garbled Markdown, complex decision flowcharts, tables, diagrams, or unclear text.

**When to Activate VLM:**
- Markdown text appears fragmented, garbled, or OCR-corrupted (e.g., "1524 gY" instead of "15-24 Gy")
- Complex NCCN decision flowcharts with multiple branches and footnotes
- Tables with merged cells or complex layouts that are hard to parse as text
- Any situation where text extraction alone is insufficient for accurate understanding

**Execution Protocol:**

**Step 1: Render the Target Page(s)**
Use Track 2 to render the uncertain page(s) to JPEG.

**Step 2: VLM Analysis via `analyze_image` Tool**
You MUST use your `analyze_image` tool to analyze the rendered JPEG image. This tool will:
- Encode the image to base64
- Send it to the VLM (qwen3.5-plus)
- Return structured analysis results

**Execution Command:**
```python
analyze_image(
    image_path="/workspace/sandbox/pdf_images_<BASENAME>_<TIMESTAMP>/page_<XXXX>.jpg",
    query="Extract all SRS dose information from this table. Include dose ranges in Gy, number of fractions, and any size-based conditions."
)
```

**Analysis Query Templates:**

For **dose tables**:
```
"Extract all radiation therapy dose information from this table. Include: dose ranges in Gy, number of fractions, tumor size conditions, and any qualifying criteria. Format as structured data."
```

For **decision flowcharts**:
```
"Analyze this NCCN decision flowchart. Trace the decision path for [specific condition]. Identify: branch conditions, recommended treatments, and footnote references. List all superscript letters and their corresponding footnotes."
```

For **general unclear content**:
```
"This page appears garbled or unclear in text extraction. Please describe what content is visible: section headers, tables, paragraphs, or diagrams. Extract any specific numerical values or medical parameters."
```

**Step 3: Citation Format for Visual Analysis**
When citing content obtained through VLM analysis:
```
[Local: <PDF_FILENAME>.pdf, Page <X>, Visual Probe]
```

---


## Track 0: 知识缓存检查（MANDATORY — 渲染 PDF 之前必须执行）

在调用 `render_pdf_page.py` 或 `analyze_image` 之前，你**必须**先查询离线知识缓存：

```python
# 步骤 1: 查询缓存
check_guideline_cache(pdf_name="NCCN_CNS.pdf", query="<你的查询内容>")
```

- 如果返回结构化数据（非 "CACHE_MISS"）：**直接使用，禁止继续渲染 PDF**
- 如果返回 "CACHE_MISS"：检查是否符合以下 5 个触发场景再决定是否进入 Track 2+3

---

## ⚠️ 视觉核实触发条件（精确版 v7.1 — 仅以下 5 种情况触发）

**默认行为**：使用文本（Track 1 Markdown）回答，不调用视觉核实。
**视觉核实**（Track 2+3）仅在以下 5 种场景触发，且每次触发前必须通过 Track 0 检查。

### 场景 1：需要遍历决策树分支路径
你的推理需要判断"如果[条件A]，则[选项X]，否则[选项Y]"的治疗分支逻辑。

**触发判断**：你的问题包含条件性判断（患者满足 X → 选择 A，否则 B），而非单纯查找某个数值。
**原因**：NCCN 决策树的箭头和条件关系在 Markdown 中已全部丢失，必须视觉还原逻辑。
**示例**：确定一个 3.5cm 病灶、2个转移灶的患者应该 SRS 还是手术+SRS。

### 场景 2：数值来自已知复杂合并单元格表格
你要提取的数值对应"按肿瘤大小分层的剂量表"或"多条件交叉的推荐矩阵"。

**触发判断**：查询的是"在条件 A 且条件 B 的情况下，参数 X 是多少"（两个或以上并列条件）。
**原因**：合并单元格在 Markdown 里会导致条件-值对应错误（如 2-3cm→18Gy 误读为 <2cm→18Gy）。
**注意**：如果已通过 Track 0 缓存获取，跳过此场景。

### 场景 3：提取结果出现可检测的 OCR 异常特征
从 Markdown 提取的数值满足以下任意一条：
- 数字序列中间出现字母（如 `1524Gy`、`2OGy`、`1f8`）
- 单位格式粘连异常（如 `20Gy1fx`、`24Gyx1`）
- 数值严重超出正常临床范围（单次 SRS > 30Gy，WBRT 分次 > 5Gy，属于异常）

**触发判断**：对提取的数值使用正则检测：`re.search(r'\d[a-zA-Z]\d', value)` 或 `re.search(r'[a-zA-Z]{2,}Gy', value)`

### 场景 4：需要解析带临床决策意义的上标脚注
**背景**：MinerU 1.3.0 已确认不检测上标类型（所有 span 均为 "text" 类型）。
`Surgery^c` 会被输出为 `Surgeryc`，`WBRT^e,f` 会被输出为 `WBRTef`。
`parse_pdf_to_md.py` 会自动插入 `<!--SUPERSCRIPT?:c-->` 标记来标识可疑位置。

**触发判断**（满足任意一条）：
1. Markdown 中出现 `<!--SUPERSCRIPT?:` 标记（自动检测到的上标粘连）
2. 医学词汇后紧跟 1-3 个小写字母且不是已知英语词缀（`WBRTef`、`Surgeryc`）
3. 你看到 `^[a-z]` 或类似的上标标记格式

**渲染策略**：只渲染脚注区域（**页面底部 30%**），不需要整页。
**查询方式**：`analyze_image(image_path=..., query="列出本页所有脚注字母及其完整含义，如 c=xxx, e=xxx")`

### 场景 5：跨页交叉引用无法在文本中定位
Markdown 中出现 `see BRAIN-C`、`see footnote a`、`see page X` 等跳转引用，你无法在当前文本中找到目标内容。

**触发判断**：包含引用标记且无法在 grep 结果中定位目标文本。

---

### ⛔ 以下情况禁止触发视觉核实

```
❌ 叙述性文字中出现 Gy、fraction、SRS（非直接引用的数值）
❌ 患者病历中的数值（如 KPS ≥ 70 — 这不是从指南提取的）
❌ 数值文本清晰、无 OCR 异常特征
❌ 已通过 Track 0 缓存获取了答案
❌ 已经渲染过同一页面（本 session 内不重复渲染同一页）
```

### 渲染约束（进入 Track 2+3 后的规则）

```
1. 每次只渲染 1-2 页，不允许批量渲染（>3 页需要特殊理由）
2. 如果渲染目的是"找脚注"：只取页面底部区域（约 30% 高度）
3. 如果渲染目的是"找表格"：优先使用 crop 参数定位表格区域
4. 渲染完成后，将成功提取的结果写入进化缓存（使用 write_evolution_cache）
```

---

---

## Track 4: Deep Guide Retrieval Protocol

**Purpose:** Systematically locate specific clinical parameters (doses, regimens, recommendations) from guidelines using patient context.

### Phase 1: Patient Context Analysis (COGNITIVE - Execute in Thought)

Before searching, you MUST explicitly analyze:

```markdown
PATIENT CONTEXT MATRIX:
- Tumor Type: [e.g., Colorectal Cancer, NSCLC, Breast Cancer]
  → Determines which guideline to use (NCCN/ESMO/ASCO)

- Metastasis Site: [e.g., Brain, Liver, Bone]
  → Determines relevant chapter (e.g., "Brain Metastases")

- Treatment Modality: [e.g., Radiation, Chemotherapy, Targeted Therapy]
  → Determines sub-chapter (e.g., "Principles of Radiation Therapy")

- Specific Parameter Needed: [e.g., SRS dose, Chemo regimen, TKI schedule]
  → Determines which table/section to locate
```

**Decision Output:**
- Guide file: [e.g., NCCN_CNS.pdf, NCCN_NSCLC.pdf]
- Target chapter: [e.g., brain-c, ltd-1, BRAIN-METS-A]
- Parameter type: [e.g., dose table, treatment algorithm]

### Phase 2: Guide Directory Navigation

**Step 1: Consult Guidelines Index**
```bash
cat /workspace/sandbox/Guidelines/GUIDELINES_INDEX.md
```

**Step 2: Locate Target Sections via Headers**
Search for structured section markers in the Markdown:
```bash
grep -n "^# .*<CHAPTER_KEYWORD>" /workspace/sandbox/<GUIDE>_output/<GUIDE>.md
```

Common NCCN chapter markers:
- `brain-c` - Principles of Radiation Therapy
- `ltd-1` - Limited Metastases
- `brain-mets-a` - Systemic Therapy for Brain Metastases

### Phase 3: Page Locking via Raw JSON

**When Markdown is unclear or you need precise page numbers:**

**Step 1: Locate parsed_data_raw.json**
```bash
ls /workspace/sandbox/Guidelines/*/parsed_data_raw.json
```

**Step 2: Search for Keywords to Find Page Numbers**
```bash
conda run -n tiantanBM_agent python3 << 'EOF'
import json
import sys

with open('/workspace/sandbox/Guidelines/<GUIDE_DIR>/parsed_data_raw.json') as f:
    data = json.load(f)

keyword = "<YOUR_SEARCH_TERM>"  # e.g., "Principles of Radiation", "15-24 Gy", "SRS"

for page in data.get('pages', []):
    text = page.get('text', '')
    if keyword.lower() in text.lower():
        print(f"Found '{keyword}' on PDF page {page['page_number']}")
EOF
```

**Step 3: Render Locked Pages**
Once you identify the target page number(s), use Track 2 to render them.

### Phase 4: Visual Extraction & Verification

**Step 1: Render Target Page**
```bash
conda run -n mineru_env python \
    /skills/pdf-inspector/scripts/render_pdf_page.py \
    /workspace/sandbox/Guidelines/<PDF_FILENAME>.pdf \
    --pages <LOCKED_PAGE_NUMBER>
```

**Step 2: VLM Analysis via analyze_image Tool**
Once you have the rendered JPEG path, use the `analyze_image` tool:

```python
analyze_image(
    image_path="/workspace/sandbox/pdf_images_<BASENAME>_<TIMESTAMP>/page_<XXXX>.jpg",
    query="Extract specific clinical parameters from this page. [Customize based on what you need: dose values, treatment regimens, decision criteria, etc.]"
)
```

**Step 3: Cross-Validation**
- Compare VLM-extracted values with any available Markdown text
- Flag discrepancies
- If uncertain, render adjacent pages for context

---

## The Footnote Defense Mechanism (CRITICAL)

When analyzing clinical flowcharts using VLM:

```text
⚠️ CRITICAL WARNING FOR MEDICAL DIAGRAM ANALYSIS ⚠️

You are analyzing a clinical practice guideline. Medical terms may have SUPERSCRIPT footnote letters (e.g., Surgery^c, WBRT^e,f).

MANDATORY RULES:
1. SEPARATE superscript letters from base words. NEVER concatenate (e.g., "Surgeryc" is WRONG).
2. CROSS-REFERENCE every superscript with the footnotes section at the bottom.
3. PRESERVE both the clinical term AND its footnote reference.

Example:
- Image shows: "Surgery^c"
- Correct Extraction: Term="Surgery", Footnote="c"
- Cross-reference footnote c at bottom: "See Principles of Brain Tumor Surgery (BRAIN-B)"
```

---

## Citation Format Standards

**For text extracted from Markdown:**
```
[Local: <FILENAME>.md, Section: <SECTION_HEADER>]
[Local: <FILENAME>.md, Line <LINE_NUMBER>]
```

**For content verified via Visual Probe:**
```
[Local: <FILENAME>.pdf, Page <X>, Visual Probe]
[Local: <FILENAME>.pdf, Page <X>, Section: <SECTION>]
```

**⚠️ PROHIBITED FORMAT:**
```
[Local: <FILENAME>, Page X]  # Without Visual Probe verification
```

---

## Error Handling & Red Lines

1. **Never guess syntax:** Do not use `--input` for Track 1. The PDF path is a positional argument.
2. **Environment Strictness:** Use `conda run -n mineru_env` for PDF scripts.
3. **Path Convention:** Always use `/workspace/sandbox/` paths (mapped to SANDBOX_DIR), not absolute host paths.
4. **Missing Images:** If a local image referenced in Markdown is corrupted, immediately fall back to Track 2.
5. **VLM Uncertainty:** If VLM analysis is inconclusive, explicitly state "Visual analysis inconclusive - expert review recommended" rather than guessing.

---

## Quick Reference: Common Scenarios

### Scenario A: Find SRS Dose for Brain Metastases
```bash
# Phase 1: Context → NCCN CNS, brain-c chapter, dose table
# Phase 2: grep -n "brain-c\|Principles of Radiation" NCCN_CNS.md
# Phase 3: Search raw JSON for "15-24 Gy" or "SRS"
# Phase 4: Render page, then analyze_image with query about SRS doses
```

### Scenario B: Find Chemotherapy Regimen
```bash
# Phase 1: Context → NCCN [TumorType], Systemic Therapy chapter
# Phase 2: grep -n "Systemic Therapy\|Chemotherapy Regimens" <GUIDE>.md
# Phase 3: Search raw JSON for drug name (e.g., "pemetrexed")
# Phase 4: Render page, then analyze_image with query about chemotherapy regimens
```

### Scenario C: Resolve Garbled Markdown (e.g., "1524 gY")
```bash
# Identify approximate location in Markdown
# grep -n "1524\|dose" <GUIDE>.md  # Find line number
# Check nearest <!-- Page X --> comment
# Render that page + adjacent pages
# analyze_image with query: "This page had OCR errors. What are the correct dose values?"
```
