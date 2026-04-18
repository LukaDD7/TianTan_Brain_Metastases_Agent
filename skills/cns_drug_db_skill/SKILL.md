---
name: cns_drug_db_skill
version: 1.0.0
category: pharmacology
description: |
  [FUNCTION]: Queries physical database for drug Blood-Brain Barrier (BBB) penetration metrics.
  [VALUE]: Eliminates LLM hallucination for critical pharmacological parameters regarding how well a drug reaches brain metastases.
  [TRIGGER_HOOK]: Use this skill WHENEVER making systemic therapy recommendations for brain metastases to justify the choice of drug based on CNS penetration data.
---

# CNS Drug Database Skill Protocol

## Identity & Purpose
You are querying a physical, verified clinical database of CNS penetration rates (e.g., CSF/Plasma ratios) and CNS ORR metrics. You MUST NOT rely on your pre-trained memory for CNS penetration metrics and trial numbers.

## Execution Command
Use your `execute` tool to run the query script:

```bash
python /skills/cns_drug_db_skill/scripts/query_cns_db.py --drug "<DRUG_NAME>"
```

*Example:*
```bash
python /skills/cns_drug_db_skill/scripts/query_cns_db.py --drug "osimertinib"
```

## Citation Rules
When generating your response, include the required metrics and use the citation provided in the script output.

**Format:**
```
[Local: cns_penetration_db.json] + [PubMed: PMID <NNNNNNNN>]
```
