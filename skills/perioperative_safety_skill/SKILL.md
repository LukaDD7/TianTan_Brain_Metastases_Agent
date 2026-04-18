---
name: perioperative_safety_skill
version: 1.0.0
category: safety_guideline
description: |
  [FUNCTION]: Queries physical database for perioperative drug holding windows.
  [VALUE]: Eliminates LLM hallucination for critical surgical safety parameters (e.g., Bevacizumab washout).
  [TRIGGER_HOOK]: Use this skill WHENEVER surgery or stereotactic radiosurgery (SRS) is recommended and the patient is on systemic therapies (e.g., targeted therapy, anti-VEGF, anticoagulants).
---

# Perioperative Safety Skill Protocol

## Identity & Purpose
You are querying a physical, verified clinical database of perioperative holding windows. You MUST NOT rely on your pre-trained memory for drug washout periods, as these are critical safety parameters.

## Execution Command
Use your `execute` tool to run the query script:

```bash
python /skills/perioperative_safety_skill/scripts/query_periop_db.py --drug "<DRUG_NAME>"
```

*Example:*
```bash
python /skills/perioperative_safety_skill/scripts/query_periop_db.py --drug "bevacizumab"
```

## Citation Rules
When generating your response, include the required wait times and use the citation provided in the script output.

**Format:**
```
[Local: perioperative_holding_db.json]
```
Add the PubMed IDs if the output provides them:
```
[Local: perioperative_holding_db.json] + [PubMed: PMID 24863066]
```
