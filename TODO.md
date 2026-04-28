# TODO: NCCN Guideline Graph Processing & Pipeline

This document tracks the pending tasks and actionable next steps following the v7.2.0 architecture update.

## 1. Pipeline Infrastructure (Ollama)
- [ ] **Ollama Dispatcher Script**: Write a Python dispatcher script (`scripts/ollama_dispatcher.py`) that handles assigning PDF processing jobs to multiple Ollama instances running on different ports across the 7x A40 GPUs.
- [ ] **Ollama Deployment SOP**: Document the exact commands to fetch the binary and start the 7 instances without root/docker.

## 2. NCCN Offline Pre-processing Pipeline
- [ ] **Page Classification Script**: Implement `scripts/classify_pages.py` to index the `NCCN_CNS.pdf` and identify which pages contain flowcharts, data tables, or text principles.
- [ ] **Flowchart Extraction Script**: Implement `scripts/extract_all_flowcharts.py` using the Pydantic schema defined in `nccn_flowchart_schema_design.md`. This script should loop over the classified pages and call the local Ollama Qwen2.5-VL-7B endpoints.
- [ ] **Cross-Page Stitching Logic**: Implement `scripts/stitch_algorithm_graphs.py` to resolve `continuation` nodes (e.g., `Recurrence (GLIO-7)`) and merge the single-page JSON fragments into a cohesive graph.

## 3. Online Agent Integration
- [ ] **Evolution Cache Integration**: Validate that `check_guideline_cache` correctly queries the generated offline structures before falling back to rendering the PDF.
- [ ] **Confidence Fallback Mechanism**: Build logic to route extremely low-confidence extractions from the 7B model to the online `qwen-vl-plus` API for human-in-the-loop verification.
- [ ] **Semantic MD Renderer**: Implement a utility that converts the JSON `NCCNAlgorithmGraph` back into structured Markdown so the Agent can ingest it easily into its context window.
