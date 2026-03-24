# Archive: 2026-03-24 v5.1 Old Test Results

## Archive Information
- **Date**: 2026-03-24
- **Version**: v5.1 (before Deep Guide Retrieval Protocol update)
- **Description**: BM Agent test results before implementing Track 3 (VLM-powered analysis) and Track 4 (Deep Guide Retrieval Protocol)

## Contents

### execution_logs/
Contains 2 session logs:
- `session_8422c7a4-b47a-424b-b6d7-afb211df7303_complete.log` - Patient 605525 session
- `session_8422c7a4-b47a-424b-b6d7-afb211df7303_structured.jsonl` - Structured JSON log
- `session_906cd044-8f4a-4558-9575-0f5c65e5388d_complete.log` - Previous session
- `session_906cd044-8f4a-4558-9575-0f5c65e5388d_structured.jsonl` - Structured JSON log

### patients/
Contains reports for 2 patients:
- `605525/reports/MDT_Report_605525.md`
- `868183/reports/MDT_Report_868183.md`

### Root Files
- `execution_audit_log.txt` - Complete audit trail (5294 lines)

## Known Issues in These Reports
1. **Citation Source Errors**: SRS dose information incorrectly cited as [PubMed: PMID 32921513] when it should reference NCCN guidelines
2. **Simplistic Search Strategy**: Used broad `grep -i "dose\|Gy\|fraction"` instead of structured Deep Guide Retrieval
3. **No VLM Analysis**: Did not use visual probe for garbled Markdown tables

## Improvements in New Version
- Added `analyze_image` tool for VLM-powered visual analysis
- Implemented Deep Guide Retrieval Protocol (Track 4)
- Updated SKILL.md with structured page locking via parsed_data_raw.json
- Fixed System Prompt to mandate visual probe usage for unclear tables
