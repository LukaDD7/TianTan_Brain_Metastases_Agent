# OncoKB 查询示例

## 示例 1：查询 EGFR L858R 突变临床意义

**场景：** 患者基因检测发现 EGFR L858R 突变，查询其临床意义和治疗推荐。

**输入：**
```json
{
  "query_type": "variant",
  "hugo_symbol": "EGFR",
  "variant": "L858R",
  "tumor_type": "Non-Small Cell Lung Cancer",
  "include_evidence": true
}
```

**命令：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type variant \
  --hugo_symbol EGFR \
  --variant L858R \
  --tumor_type "Non-Small Cell Lung Cancer"
```

**预期输出要点：**
- Oncogenicity: Oncogenic
- 敏感药物：Osimertinib、Gefitinib、Erlotinib 等
- 证据等级：Level 1 (FDA 批准)

---

## 示例 2：查询 BRAF V600E 对 Vemurafenib 的敏感性

**场景：** 黑色素瘤患者携带 BRAF V600E 突变，查询对 Vemurafenib 的敏感性。

**输入：**
```json
{
  "query_type": "drug",
  "hugo_symbol": "BRAF",
  "variant": "V600E",
  "drug_name": "Vemurafenib",
  "tumor_type": "Melanoma"
}
```

**命令：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type drug \
  --hugo_symbol BRAF \
  --variant V600E \
  --drug_name Vemurafenib
```

**预期输出要点：**
- Sensitivity: Sensitive
- 证据等级：Level 1

---

## 示例 3：查询 MSI-H 生物标志物

**场景：** 结直肠癌患者检测出 MSI-H，查询相关治疗推荐。

**输入：**
```json
{
  "query_type": "biomarker",
  "biomarker_name": "MSI-H",
  "tumor_type": "Colorectal Cancer"
}
```

**命令：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type biomarker \
  --biomarker_name "MSI-H" \
  --tumor_type "Colorectal Cancer"
```

**预期输出要点：**
- PD-1 抑制剂 (Pembrolizumab、Nivolumab) 敏感
- 证据等级：Level 1 (FDA 批准用于 MSI-H 实体瘤)

---

## 示例 4：查询非小细胞肺癌治疗推荐

**场景：** 查询非小细胞肺癌的标准治疗推荐。

**输入：**
```json
{
  "query_type": "tumor_type",
  "tumor_type": "Non-Small Cell Lung Cancer",
  "evidence_level": "LEVEL_1"
}
```

**命令：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type tumor_type \
  --tumor_type "Non-Small Cell Lung Cancer" \
  --evidence_level LEVEL_1
```

**预期输出要点：**
- 列出所有 Level 1 证据支持的治疗方案
- 包括相应的生物标志物

---

## 示例 5：查询 KRAS G12C 突变

**场景：** 患者携带 KRAS G12C 突变，查询靶向治疗选择。

**输入：**
```json
{
  "query_type": "variant",
  "hugo_symbol": "KRAS",
  "variant": "G12C",
  "tumor_type": "Non-Small Cell Lung Cancer"
}
```

**命令：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type variant \
  --hugo_symbol KRAS \
  --variant G12C \
  --tumor_type "Non-Small Cell Lung Cancer"
```

**预期输出要点：**
- Oncogenicity: Oncogenic
- 敏感药物：Sotorasib、Adagrasib
- 证据等级：Level 3A/Level 2

---

## 示例 6：批量查询多个变异

**场景：** 患者基因检测发现多个突变，需要批量查询。

**Python 代码示例：**
```python
from skills.oncokb_query.scripts.oncokb_client import OncoKBClient

client = OncoKBClient()

queries = [
    {"hugoSymbol": "EGFR", "alteration": "L858R"},
    {"hugoSymbol": "TP53", "alteration": "R175H"},
    {"hugoSymbol": "PIK3CA", "alteration": "H1047R"}
]

results = client.batch_query_variants(queries, include_evidence=True)

for result in results:
    gene = result.get("gene", {}).get("hugoSymbol", "Unknown")
    variant = result.get("variant", "")
    oncogenicity = result.get("oncogenic", "")
    print(f"{gene} {variant}: {oncogenicity}")
```

---

## 示例 7：查询基因基本信息

**场景：** 查询 EGFR 基因的基本信息。

**输入：**
```json
{
  "query_type": "gene",
  "hugo_symbol": "EGFR"
}
```

**命令：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type gene \
  --hugo_symbol EGFR
```

**预期输出：**
- 基因全称
- Entrez Gene ID
- 染色体位置
- 相关癌症类型

---

## 常见问题解答

### Q1: 如何确定变异描述的格式？
OncoKB 接受多种格式的变异描述：
- 蛋白质水平：L858R、V600E、exon19del
- HGVS 格式：p.Leu858Arg、p.Val600Glu

### Q2: 如果查询结果返回空怎么办？
可能原因：
- 基因符号不标准 (使用 HGNC 标准命名)
- 变异描述格式不正确
- 该变异尚未被 OncoKB 收录

### Q3: 如何获取 API Token？
访问 https://www.oncokb.org/account 注册账号后获取。

### Q4: 公共 API 和认证 API 有什么区别？
- 公共 API：无需认证，速率受限 (约 10 请求/分钟)
- 认证 API：需要 Token，速率更高 (约 100 请求/分钟)
