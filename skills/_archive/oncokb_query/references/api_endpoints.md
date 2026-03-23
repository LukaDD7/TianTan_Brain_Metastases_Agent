# OncoKB API 端点参考

> 最后更新：2026-03-04
> API 版本：v1

---

## API 基础 URL

- **认证 API** (需要 Token): `https://www.oncokb.org/api/v1`

获取 API Token: https://www.oncokb.org/account

---

## 变异注释端点

### 1. 按蛋白质改变查询变异

```
GET /annotate/mutations/byProteinChange
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| hugoSymbol | string | 是 | HGNC 基因符号 |
| alteration | string | 是 | 蛋白质水平变异描述 |
| tumorType | string | 否 | 癌症类型 |
| consequence | string | 否 | 变异后果 |
| proteinStart | integer | 否 | 蛋白质起始位置 |
| proteinEnd | integer | 否 | 蛋白质结束位置 |

**示例：**
```bash
curl "https://www.oncokb.org/api/v1/annotate/mutations/byProteinChange?hugoSymbol=EGFR&alteration=L858R"
```

---

### 2. 按基因组坐标查询变异

```
GET /annotate/variants/byGenomicChange
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chromosome | string | 是 | 染色体 |
| start | integer | 是 | 起始位置 |
| end | integer | 是 | 结束位置 |
| variantType | string | 是 | 变异类型 (SNV/INDEL/FUSION) |

**示例：**
```bash
curl "https://public.api.oncokb.org/api/v1/annotate/variants/byGenomicChange?chromosome=7&start=55259515&end=55259515&variantType=SNV"
```

---

### 3. 批量查询变异

```
POST /annotate/variants/byProteinChanges
```

**请求体：**
```json
{
  "queries": [
    {"hugoSymbol": "EGFR", "alteration": "L858R"},
    {"hugoSymbol": "BRAF", "alteration": "V600E"}
  ]
}
```

---

## 肿瘤类型注释端点

### 查询肿瘤类型敏感性

```
GET /annotate/tumorTypes
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| hugoSymbol | string | 是 | 基因符号 |
| alteration | string | 是 | 变异描述 |
| tumorType | string | 否 | 癌症类型 |

---

## 生物标志物端点

### 查询生物标志物

```
GET /annotate/biomarkers
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| biomarkerName | string | 是 | 生物标志物名称 |
| tumorType | string | 否 | 癌症类型 |

---

## 证据端点

### 获取证据详情

```
GET /evidence/{uuid}
```

### 获取证据类型

```
GET /evidence/types
```

返回所有证据类型定义。

---

## 基因端点

### 查询基因信息

```
GET /genes/{hugoSymbol}
```

---

## 药物端点

### 查询药物信息

```
GET /drugs/{drugName}
```

---

## 癌症类型端点

### 查询癌症类型治疗推荐

```
GET /tumorTypes
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tumorType | string | 是 | 癌症类型 |
| evidenceLevel | string | 否 | 证据等级过滤 |

---

## 证据等级定义

| 等级 | 描述 |
|------|------|
| LEVEL_1 | FDA 批准的生物标志物指导治疗 |
| LEVEL_2A | NCCN 等权威指南推荐 |
| LEVEL_2B | 专家共识推荐 |
| LEVEL_3A | 多个临床试验支持 |
| LEVEL_3B | 单个临床试验支持 |
| LEVEL_4 | 临床前研究支持 |
| LEVEL_R1 | FDA 批准或试验证实耐药 |
| LEVEL_R2 | 临床前或个案报道耐药 |
| LEVEL_Pt | 基于患者特异性分析 |

---

## 致癌性分类

| 分类 | 描述 |
|------|------|
| Oncogenic | 致癌 |
| Likely Oncogenic | 可能致癌 |
| Benign | 良性 |
| Likely Benign | 可能良性 |
| Uncertain Significance | 意义不明 |

---

## 治疗敏感性分类

| 分类 | 描述 |
|------|------|
| Sensitive | 敏感 |
| Resistant | 耐药 |

---

## 速率限制

| API 类型 | 速率限制 |
|---------|---------|
| 公共 API | 约 10 请求/分钟 |
| 认证 API | 约 100 请求/分钟 |

---

## 错误码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 (Token 无效) |
| 403 | 禁止访问 |
| 404 | 资源未找到 |
| 429 | 请求频率超限 |
| 500 | 服务器错误 |
