---
name: generate_mdt_report
description: |
  生成并验证肿瘤多学科诊疗 (MDT) 报告。
  适用于：
  - 将 AI 生成的治疗建议格式化为标准 MDT 报告
  - 强制验证报告包含指南引用 (Citation Pattern)
  - 自动归档到患者专属沙盒目录

  注意：这是诊疗流程的最后一步，确保所有建议都有循证依据。
version: 2.0.0
author: TianTan Brain Metastases Agent Team
metadata:
  openclaw:
    os: ["linux", "darwin", "windows"]
    requires:
      binaries: ["python3"]
      env: []
      config: []
  dependencies: []
user-invocable: true
---

## 使用说明

### 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | 患者病例 ID (如 "Case1") |
| report_content | string | 是 | MDT 报告内容 (Markdown 格式) |
| skip_validation | boolean | 否 | 是否跳过验证 (默认为 false，强制验证) |

### 输出格式

返回 JSON 格式结果：
```json
{
  "success": true,
  "report_path": "workspace/cases/Case1/MDT_Report_20260303_143022.md",
  "validation_errors": [],
  "message": "报告已通过医疗合规校验"
}
```

## 临床使用场景

1. **MDT 报告生成**: 完成诊疗分析后，将建议格式化为标准报告
2. **合规验证**: 确保每项治疗建议都有指南引用支持
3. **自动归档**: 报告自动保存到患者专属目录，便于后续查阅

## 强制临床书写规则

1. **引用格式**: 每项治疗建议后必须包含 `[Citation: <文件名>, Page <页码>]`
2. **结构完整**: 报告必须包含"治疗"或"建议"区块
3. **循证依据**: 不得凭空捏造药物剂量或放疗靶区

## 验证失败处理

如果验证失败，错误信息会返回，需要：
1. 根据错误提示修改报告内容
2. 补充缺失的指南引用
3. 重新调用本技能提交

## 相关文件

- `scripts/generate_report.py` - 报告生成主逻辑
- `scripts/validate_report.py` - 验证器

## 目录结构

```
clinical_writer/
├── SKILL.md              # 元数据和使用说明
├── README.md             # 快速开始
├── scripts/
│   ├── generate_report.py    # MDT 报告生成器
│   └── validate_report.py    # 报告验证器
├── references/           # 参考资料 (可选)
└── examples/             # 使用示例 (可选)
```
