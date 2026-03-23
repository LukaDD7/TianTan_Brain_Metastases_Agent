# Clinical Report Validator Skill

This is the FINAL step of your reasoning process. It acts as a strict validator for your MDT Report.

## Workflow Instructions
**Step 1: Write the Report**
Use your built-in `write_file` tool to save your final medical report directly to the patient's directory. 
- **Mandatory Naming Convention**: `workspace/cases/<Patient_ID>/<Patient_ID>_<YYYYMMDD>_<Query_Topic>.md`
- *Example*: `workspace/cases/Case1/Case1_20260227_诊疗方案.md`

**Step 2: Validate the Report**
Once the file is written, you MUST validate it by executing this shell command:
`python skills/clinical_writer/validate_report.py --file_path "PATH_TO_YOUR_MD_FILE"`

## Mandatory Clinical Writing Strictures
1. **Mandatory Citation Pattern**: Every clinical recommendation MUST end with a citation block matching this exact regex: `[Citation: <FileName>, Page <Number>]`.
2. **Structural Completeness**: Must contain "治疗" or "建议".
If the validator throws a Validation Error, you must use your tools to edit the file and fix the citations, then run the validation again.