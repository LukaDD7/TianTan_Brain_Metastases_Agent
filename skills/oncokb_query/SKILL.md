---
name: query_oncokb
description: |
  查询 OncoKB 癌症知识库获取基因变异的临床意义、药物敏感性、生物标志物等信息。

  OncoKB 是一个精准肿瘤学知识库，提供：
  - 基因变异致癌性评估 (Oncogenic/Benign/Likely Oncogenic 等)
  - 治疗敏感性预测 (Sensitive/Resistant 等)
  - 证据等级分级 (Level 1-4, R1-R3)
  - FDA 批准的生物标志物信息

  适用于以下查询场景：
  1. **变异查询**：查询特定基因变异的临床意义 (如 EGFR L858R)
  2. **药物查询**：查询药物对特定变异的敏感性 (如奥希替尼对 EGFR 突变)
  3. **生物标志物查询**：查询生物标志物信息 (如 MSI-H、TMB-H)
  4. **癌症类型查询**：查询特定癌症类型的治疗推荐

  注意：需要提供 OncoKB API Token，请在环境变量中设置 `ONCOKB_API_KEY`。
version: 2.1.0
author: TianTan Brain Metastases Agent Team
metadata:
  openclaw:
    os: ["linux", "darwin", "windows"]
    requires:
      binaries: ["python3"]
      env: ["ONCOKB_API_KEY"]
      config: []
  dependencies:
    - requests>=2.28.0
user-invocable: true
---

## 使用说明

### 查询类型

OncoKB Query Skill 支持多种查询类型，Agent 可根据需要选择：

| 查询类型 | 方法 | 适用场景 |
|---------|------|---------|
| `variant` | `query_type="variant"` | 查询基因变异的临床意义、致癌性 |
| `drug` | `query_type="drug"` | 查询药物对特定变异的敏感性 |
| `biomarker` | `query_type="biomarker"` | 查询生物标志物信息 |
| `tumor_type` | `query_type="tumor_type"` | 查询特定癌症类型的治疗推荐 |
| `evidence` | `query_type="evidence"` | 获取特定证据的详细信息 |

### 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query_type | string | 是 | 查询类型：variant/drug/biomarker/tumor_type/evidence |
| hugo_symbol | string | 条件必填 | 基因符号 (如 EGFR、TP53)，variant/drug 查询需要 |
| variant | string | 条件必填 | 变异描述 (如 L858R、V600E)，variant 查询需要 |
| drug_name | string | 条件必填 | 药物名称，drug 查询需要 |
| biomarker_name | string | 条件必填 | 生物标志物名称，biomarker 查询需要 |
| tumor_type | string | 条件必填 | 癌症类型 (如 "Non-Small Cell Lung Cancer") |
| evidence_level | string | 否 | 证据等级过滤 (如 "LEVEL_1", "LEVEL_2A") |
| include_evidence | boolean | 否 | 是否返回详细证据说明，默认 true |

### 输出格式

返回 JSON 格式结果：
```json
{
  "query_type": "variant",
  "gene": {"hugoSymbol": "EGFR", "entrezGeneId": 1956},
  "variant": "L858R",
  "oncogenicity": "Oncogenic",
  "treatments": {
    "sensitive": [...],
    "resistant": [...]
  },
  "evidence": [...],
  "last_updated": "2026-03-03T12:00:00Z"
}
```

## 临床使用场景

### 场景 1：基因变异解读
```
患者基因检测发现 EGFR L858R 突变，查询其临床意义。
→ 使用 query_type="variant", hugo_symbol="EGFR", variant="L858R"
```

### 场景 2：药物敏感性查询
```
患者携带 BRAF V600E 突变，查询对维莫非尼 (Vemurafenib) 的敏感性。
→ 使用 query_type="drug", hugo_symbol="BRAF", variant="V600E", drug_name="Vemurafenib"
```

### 场景 3：生物标志物查询
```
患者检测出 MSI-H (微卫星不稳定性高)，查询相关治疗推荐。
→ 使用 query_type="biomarker", biomarker_name="MSI-H"
```

### 场景 4：癌症类型治疗推荐
```
非小细胞肺癌 (NSCLC) 的标准治疗推荐有哪些？
→ 使用 query_type="tumor_type", tumor_type="Non-Small Cell Lung Cancer"
```

## 证据等级说明

OncoKB 使用以下证据等级系统：

| 等级 | 描述 | 示例 |
|------|------|------|
| Level 1 | FDA 批准的生物标志物 | FDA 批准药物用于特定变异 |
| Level 2A | NCCN 等权威指南推荐 | NCCN 指南推荐药物 |
| Level 2B | 专家共识推荐 | 专业学会共识 |
| Level 3A | 多个临床试验支持 | 多个二期/三期试验 |
| Level 3B | 单个临床试验支持 | 单臂二期试验 |
| Level 4 | 临床前研究支持 | 细胞系/动物模型数据 |
| R1 | 耐药性证据 | FDA 批准或试验证实耐药 |
| R2 | 耐药性证据 | 临床前或个案报道 |

## 依赖说明

- 需要安装 `requests` (pip install requests)
- 需要 OncoKB API Token (https://www.oncokb.org/account)
- 环境变量设置：`export ONCOKB_API_KEY=your_token_here`

## 目录结构

```
oncokb_query/
├── SKILL.md                   # 本文件
├── README.md                  # 快速开始
├── scripts/
│   ├── oncokb_client.py       # API 客户端封装
│   ├── query_variant.py       # 变异查询实现
│   ├── query_drug.py          # 药物查询实现
│   ├── query_biomarker.py     # 生物标志物查询实现
│   └── query_tumor_type.py    # 癌症类型查询实现
├── references/
│   ├── api_endpoints.md       # API 端点参考
│   └── evidence_levels.md     # 证据等级详解
└── examples/
    ├── example_queries.md     # 查询示例
    └── sample_responses.json  # 示例响应
```

## 错误处理

| 错误码 | 含义 | 处理建议 |
|--------|------|---------|
| 401 | API Token 无效或缺失 | 检查 ONCOKB_API_TOKEN 环境变量 |
| 404 | 基因/变异未找到 | 检查基因符号和变异描述是否正确 |
| 429 | 请求频率超限 | 稍后重试，建议添加延迟 |
| 500 | 服务器错误 | 稍后重试 |

## 相关资源

- [OncoKB 官方网站](https://www.oncokb.org/)
- [OncoKB API 文档](https://docs.oncokb.org/)
- [证据等级定义](https://www.oncokb.org/evidenceLevels)
