# Medical PDF Inspector Skill

Extract and analyze text and high-value clinical images (like MRI scans, CT scans, or NCCN clinical algorithmic flowcharts) from medical PDF documents.

## When to Use
- When you are given a raw patient EHR (Electronic Health Record) in PDF format.
- When you need to read an oncology clinical guideline (e.g., ASCO, NCCN) to find the standard of care.
- When you suspect there is a critical decision-tree flowchart that cannot be understood via pure text.

## How to Use
Use your shell execution tool to run this script. 

`python skills/pdf_inspector/parse_pdf.py --file_path "PATH_TO_PDF" [--page_start N] [--page_end M] [--extract_images]`

### Arguments
- `--file_path` (required): Absolute or relative path to the local PDF file.
- `--page_start` (optional): The starting page number (1-indexed).
- `--page_end` (optional): The ending page number.
- `--extract_images` (flag): Include this flag if you want to extract large medical images or flowcharts to the `workspace/temp_visuals/` directory for subsequent VLM (Vision-Language Model) analysis.

### Important Clinical Rules
1. Medical papers often use **two-column layouts**. This tool automatically handles column reading.
2. If the tool extracts an image to `workspace/temp_visuals/`, your NEXT immediate step should be utilizing your Vision capabilities to interpret that clinical flowchart or scan.