---
name: drug_interaction_skill
version: 1.0.0
category: pharmacology
description: |
  [FUNCTION]: Queries NLM RxNav API for Drug-Drug Interactions (DDI) based on DrugBank/ONC lists.
  [VALUE]: Eliminates LLM hallucination for evaluating potential dangerous interactions between antineoplastic agents and concomitant medications (AEDs, steroids, etc.).
  [TRIGGER_HOOK]: Use this skill WHENEVER recommending a combination of systemic therapies or considering the addition of a new drug to a patient's existing medication list.
---

# Drug Interaction Skill Protocol

## Identity & Purpose
You are querying a physical, live API provided by the National Library of Medicine (NLM RxNav) to determine drug interactions. Do not guess interactions based on pre-trained memory. 

## Execution Command
Use your `execute` tool to run the query script:

```bash
python /skills/drug_interaction_skill/scripts/check_interaction.py --drug1 "<DRUG_1>" --drug2 "<DRUG_2>"
```

*Example:*
```bash
python /skills/drug_interaction_skill/scripts/check_interaction.py --drug1 "osimertinib" --drug2 "dexamethasone"
```

## Citation Rules
When generating your response, if an interaction is found, clearly state the description and severity.

**Format:**
```
[Local: NLM RxNav Interaction API]
```
