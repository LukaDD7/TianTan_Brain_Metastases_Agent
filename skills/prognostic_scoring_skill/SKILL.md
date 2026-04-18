---
name: prognostic_scoring_skill
version: 1.0.0
category: clinical_decision_support
description: |
  [FUNCTION]: Deterministic DS-GPA (Disease-Specific Graded Prognostic Assessment) calculator for brain metastases prognosis.
  [VALUE]: Provides objective, publication-grounded median OS estimates by tumor type (NSCLC, Breast, Melanoma, GI, RCC, SCLC). Eliminates LLM guessing of prognosis.
  [TRIGGER_HOOK]: Call this skill BEFORE generating the Executive Summary (Module 0) and Individualized Treatment Plan (Module 2). The DS-GPA score MUST be included in every MDT report.
  [DATA_SOURCE]: Sperduto et al., JCO 2020 (PMID: 33141945) — Updated DS-GPA tables.
---

# Prognostic Scoring Skill: DS-GPA Protocol

## Identity & Core Rule
You are calling a deterministic scoring script. The output is calculated from a published lookup table, NOT from LLM reasoning. The citation is self-contained in the script output.

## Execution Command
```bash
python /skills/prognostic_scoring_skill/scripts/calculate_ds_gpa.py \
    --tumor_type "<TYPE>" \
    --kps "<KPS>" \
    [--age <AGE>] \
    [--n_brain_mets <N>] \
    [--ecm <yes|no>] \
    [--molecular <positive|negative>] \
    [--breast_subtype "<SUBTYPE>"] \
    [--braf <positive|negative>]
```

## Factor Collection Checklist (MANDATORY before calling)

Before executing, extract these values from the patient record:

| Factor | Source in Patient Record | Required For |
|:-------|:------------------------|:-------------|
| `--tumor_type` | 病理诊断 | ALL |
| `--kps` | 体力状态 (KPS/ECOG) | ALL |
| `--age` | 年龄 | NSCLC, SCLC |
| `--n_brain_mets` | 影像报告（脑MRI） | NSCLC, Melanoma, RCC |
| `--ecm` | PET-CT / 分期报告 | NSCLC, Melanoma, RCC |
| `--molecular` | 基因检测报告 | NSCLC (EGFR/ALK) |
| `--breast_subtype` | IHC/FISH 报告 | Breast |
| `--braf` | 基因检测报告 | Melanoma |

## ECOG to KPS Mapping (if KPS not directly available)
| ECOG | KPS Range |
|:-----|:---------|
| 0 | 100 |
| 1 | 70-80 |
| 2 | 50-60 |
| 3 | 30-40 |
| 4 | 10-20 |

## Example Calls

**NSCLC with EGFR mutation:**
```bash
python /skills/prognostic_scoring_skill/scripts/calculate_ds_gpa.py \
    --tumor_type "NSCLC" --kps "80" --age 58 \
    --n_brain_mets 2 --ecm yes --molecular positive
```

**HER2+ Breast Cancer:**
```bash
python /skills/prognostic_scoring_skill/scripts/calculate_ds_gpa.py \
    --tumor_type "Breast" --kps "90" \
    --breast_subtype "HER2+HR+"
```

## Citation Format
The script output contains the citation. Copy it verbatim:
```
[Local: prognostic_scoring_skill/ds_gpa_tables.py] + [PubMed: PMID 33141945]
```
