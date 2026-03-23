---
name: pdf-inspector
version: 2.2.0
category: document_analysis
description: |
  [FUNCTION]: Dual-track PDF analysis engine designed for complex clinical guidelines (e.g., NCCN, ASCO).
  [VALUE]: Provides global text extraction (MinerU Markdown) and local visual probing (PyMuPDF page rendering) to defeat OCR errors and parse complex medical flowcharts.
  [TRIGGER_HOOK]: Whenever you need to read a clinical guideline PDF, extract text, or visually inspect a complex decision tree/table, you MUST read this Skill document to learn the exact terminal commands required to process the PDF and how to navigate the hashed image anchors.
---

# PDF-Inspector: Cognitive Execution Protocol

## Identity & Core Mechanism
This is a Dual-Track PDF analysis skill. It does NOT use API tools. You must use your native `execute` tool to run the provided isolated Python scripts in the terminal or read pre-existing cached files.

---

## Track 1: Global Text Extraction (MinerU Pipeline)

**Purpose:** Convert the entire PDF into structured Markdown.

**CRITICAL STEP 1: CHECK CACHE (MANDATORY)**
MinerU parsing is extremely slow. Pre-parsed results are stored in the sandbox. 
Before executing the parsing script, you MUST use your `execute` tool (e.g., `ls` or `cat`) to check if the Markdown file already exists.
* **Target Path:** `/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/<PDF_BASENAME>_output/<PDF_BASENAME>.md`
* **Decision:** - If EXISTS: **DO NOT run the MinerU script.** Directly use `read_file` or `cat` to read the existing Markdown file.
  - If NOT EXISTS: Proceed to Step 2.

**STEP 2: EXECUTE PARSING SCRIPT (ONLY IF CACHE MISS)**
Use your `execute` tool to run this exact command:
```bash
/home/luzhenyang/anaconda3/envs/mineru_env/bin/python \
    /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pdf-inspector/scripts/parse_pdf_to_md.py \
    <ABSOLUTE_PATH_TO_PDF> \
    -o /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/
```

**Output Structure & Anchor Format:**
MinerU generates images with hashed filenames. To help you identify the page number, the script injects an HTML comment directly above the image anchor in the Markdown:
```markdown
![](/workspace/sandbox/eb3988d4...32e.jpg)
```
*(There is also an `_image_page_map.json` generated in the directory if you need to map hashes to pages programmatically).*

---

## Track 2: Local Visual Probe (Visual Upgrade)

**Purpose:** If the Markdown text under a section header appears fragmented or chaotic, the OCR has failed. You must initiate a Visual Upgrade to look at the original page.

**Execution Command:** You MUST use your `execute` tool to run this command to render a specific page into a <5MB JPEG.
```bash
/home/luzhenyang/anaconda3/envs/mineru_env/bin/python \
    /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pdf-inspector/scripts/render_pdf_page.py \
    <ABSOLUTE_PATH_TO_PDF> \
    --pages <PAGE_NUMBER>
```

**Page Inference Strategy (How to find `<PAGE_NUMBER>`):**
1. **Primary (HTML Tag):** Find the chaotic section in the Markdown. Look for the nearest `` tag preceding the image anchor. Extract the number `X`.
2. **Secondary (JSON Map):** If you only have the hash filename, `cat` the `_image_page_map.json` file to find the corresponding page number.
3. **Fallback:** Infer the page number based on the table of contents or surrounding headers.

---

## The Footnote Defense Mechanism (CRITICAL)

When you successfully render a page using Track 2, you must analyze the resulting image. When analyzing clinical flowcharts using your multimodal vision capabilities, you MUST adhere to the following internal rules:

```text
⚠️ CRITICAL WARNING FOR MEDICAL DIAGRAM ANALYSIS ⚠️

You are analyzing a clinical practice guideline flowchart. This diagram contains medical terms with SUPERSCRIPT footnote letters (e.g., Surgery^c, WBRT^e,f, Systemic therapy^h,i).

MANDATORY RULES:
1. SEPARATE superscript letters from base words. NEVER concatenate (e.g., "Surgeryc" is WRONG).
2. CROSS-REFERENCE every superscript with the footnotes section at the bottom of the image.
3. PRESERVE both the clinical term AND its footnote reference in your mental extraction.

Example:
- Image shows: "Surgery^c"
- Correct Mental Extraction: Term="Surgery", Footnote="c", FootnoteText="See Principles of Brain Tumor Surgery (BRAIN-B)."
```

## Error Handling & Red Lines
1. **Never guess the syntax:** Do not use `--input` for Track 1. The PDF path is a positional argument.
2. **Environment Strictness:** You MUST use the `/envs/mineru_env/bin/python` interpreter.
3. **Missing Images:** If a local image referenced in the Markdown is corrupted, immediately fall back to Track 2 to re-render that specific page.