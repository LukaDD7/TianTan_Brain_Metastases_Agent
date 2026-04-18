---
name: pdf-inspector
version: 3.0.0
category: document_analysis
description: |
  [FUNCTION]: Multi-track PDF analysis engine for complex clinical guidelines (NCCN, ESMO, ASCO).
  [VALUE]: Provides global text extraction (MinerU Markdown), local visual probing (PyMuPDF rendering), and VLM-powered analysis via analyze_image tool for any uncertain content.
  [TRIGGER_HOOK]: Read this Skill BEFORE accessing any clinical guideline PDF. Use for text extraction, visual inspection of flowcharts/tables, or when markdown is garbled/OCR-failed.
---

# PDF-Inspector: Cognitive Execution Protocol

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

## ⚠️ DUAL-TRACK MANDATORY VERIFICATION (v6.0 新增，MANDATORY)

**触发条件**：当你的推理涉及以下任何关键词时，**必须**同时使用 Track 1（文本）和 Track 3（VLM视觉）：

### 强制触发词集合（Trigger Keywords）

| 类别 | 触发词 |
|:-----|:------|
| **剂量单位** | `Gy`, `cGy`, `mg`, `mg/m²`, `mg/kg`, `AUC`, `μg` |
| **放疗参数** | `fraction`, `分割`, `分次`, `dose`, `剂量`, `SRS`, `SRT`, `WBRT` |
| **决策节点** | `decision tree`, `决策树`, `pathway`, `flowchart`, `流程图`, `criteria` |
| **安全阈值** | `禁忌`, `contraindication`, `停药`, `hold`, `resume`, `washout` |
| **数值标准** | `≤`, `≥`, `<`, `>`, `threshold`, `cutoff` |
| **时间窗口** | `days`, `weeks`, `天`, `周`, `before surgery`, `after surgery` |

### 双轨执行步骤（MANDATORY Protocol）

**Step 1: 文本轨道（Track 1）**
```bash
grep -n -A 5 "<TRIGGER_KEYWORD>" /workspace/sandbox/Guidelines/<FILE>.md
```
记录：文件名、行号、文本内容。

**Step 2: 视觉轨道（Track 2 + 3）**
1. 从 `<!-- Page X -->` 标签或 `_image_page_map.json` 确定页码
2. 使用 Track 2 渲染该页：
```bash
conda run -n mineru_env python \
    /skills/pdf-inspector/scripts/render_pdf_page.py \
    /workspace/sandbox/Guidelines/<FILE>.pdf \
    --pages <PAGE_NUMBER>
```
3. 使用 Track 3 VLM 分析：
```python
analyze_image(
    image_path="/workspace/sandbox/<FILE>_page_<N>.jpg",
    query="精确提取所有剂量参数、数值标准和时间窗口（包含单位）。验证以下数字是否准确：<CLAIM_FROM_TEXT>"
)
```

**Step 3: 比对与决策**
| 结果 | 处理方式 |
|:-----|:--------|
| 文本 = 视觉（完全一致） | ✅ 使用文本值，引用标注 `[Dual-Track Verified ✓]` |
| 文本 ≠ 视觉（存在差异） | 🔴 以视觉为准（OCR可能有误），注明差异，引用标注 `[Dual-Track: Visual Override]` |
| 视觉无法识别 | ⚠️ 标注 `[Dual-Track: Visual Unreadable, Text Only]`，降低置信度 |

**Step 4: 引用格式（Dual-Track 专用）**
```
[Local: <FILENAME>.pdf, Page <N>, Dual-Track Verified ✓]
```
此格式表示该数值已经过文本+视觉双重确认，可直接写入报告。
未经双轨验证的剂量参数**不得**写入正式报告中。

### ⛔ 违禁行为（Dual-Track 红线）

- **严禁**：仅凭 Markdown 文本直接引用剂量（如 `[Local: NCCN.md, Line 280]`），
  如果被引用的内容是剂量/停药天数/安全阈值，则必须额外完成视觉验证
- **严禁**：视觉验证失败时仍使用文本数值而不标注差异
- **严禁**：估算行号（`Line 约 380`）—— 必须实际 grep 定位

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
