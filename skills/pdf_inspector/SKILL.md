---
name: parse_medical_pdf
description: |
  从医疗 PDF 文档中提取文本和高分辨率医学影像。
  适用于：
  - 解析患者电子病历 (EHR) PDF
  - 提取肿瘤诊疗指南 (如 NCCN、ESMO、CSCO) 的关键内容
  - 识别并提取 CT/MRI 影像图片或 NCCN 决策树流程图

  注意：提取的图片会保存到 workspace/temp_visuals/ 目录，后续可配合视觉模型分析。
version: 2.0.0
author: TianTan Brain Metastases Agent Team
metadata:
  openclaw:
    os: ["linux", "darwin", "windows"]
    requires:
      binaries: ["python3"]
      env: ["PYMU PDF_AVAILABLE"]
      config: []
  dependencies:
    - pymupdf>=1.23.0
user-invocable: true
---

## 使用说明

### 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_path | string | 是 | PDF 文件路径 (绝对或相对路径) |
| page_start | integer | 否 | 起始页码，默认为 1 (1-indexed) |
| page_end | integer | 否 | 结束页码，默认为全部 |
| extract_images | boolean | 否 | 是否提取图片，默认为 false |

### 输出格式

返回 JSON 格式结果：
```json
{
  "metadata": { ... PDF 元数据 ... },
  "total_pages": 10,
  "extracted_pages": [
    {
      "page_num": 1,
      "text_snippet": "提取的文本内容..."
    }
  ],
  "extracted_visuals": [
    {
      "page_num": 3,
      "local_path": "workspace/temp_visuals/med_vis_p3_0.png",
      "hint": "This is a large clinical image..."
    }
  ]
}
```

## 临床使用场景

1. **患者病历解析**: 当收到患者的 PDF 格式电子病历时，使用此技能提取关键信息
2. **指南查阅**: 当需要查阅 NCCN/ESMO 指南的具体推荐时，解析指南 PDF
3. **影像提取**: 当 PDF 中包含重要的 CT/MRI 影像或决策流程图时，启用 `extract_images` 参数

## 重要规则

1. **双栏排版处理**: 本工具自动处理医学论文常见的双栏排版，按正确阅读顺序提取
2. **图片阈值过滤**: 仅提取大于 30KB 的图片，避免页眉页脚的小 Logo
3. **后续步骤**: 如果提取了图片，下一步应使用视觉模型能力分析这些临床影像

## 依赖说明

- 需要安装 `PyMuPDF` (pip install pymupdf)
- 图片提取功能需要 writable 的 `workspace/temp_visuals/` 目录

## 相关文件

- `scripts/parse_pdf.py` - 主要实现代码
- `README.md` - 简要使用说明

## 目录结构

```
pdf_inspector/
├── SKILL.md           # 元数据和使用说明
├── README.md          # 快速开始
├── scripts/
│   └── parse_pdf.py   # 执行脚本
├── references/        # 参考资料 (可选)
└── examples/          # 使用示例 (可选)
```
