# OncoKB Query Skill

快速查询 OncoKB 癌症知识库，获取基因变异的临床意义、药物敏感性、生物标志物等信息。

## 快速开始

### 1. 设置 API Token (可选但推荐)

```bash
# Linux/macOS
export ONCOKB_API_TOKEN=your_token_here

# Windows PowerShell
$env:ONCOKB_API_TOKEN="your_token_here"
```

获取 Token: https://www.oncokb.org/account

### 2. 安装依赖

```bash
pip install requests
```

### 3. 运行查询

**查询基因变异临床意义：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type variant \
  --hugo_symbol EGFR \
  --variant L858R
```

**查询药物敏感性：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type drug \
  --hugo_symbol BRAF \
  --variant V600E \
  --drug_name Vemurafenib
```

**查询生物标志物：**
```bash
python skills/oncokb_query/scripts/query_variant.py \
  --query_type biomarker \
  --biomarker_name MSI-H
```

## 查询类型

| 类型 | 用途 | 必填参数 |
|------|------|---------|
| `variant` | 基因变异临床意义 | hugo_symbol, variant |
| `drug` | 药物敏感性 | hugo_symbol, variant, drug_name |
| `biomarker` | 生物标志物信息 | biomarker_name |
| `tumor_type` | 癌症类型治疗推荐 | tumor_type |
| `gene` | 基因基本信息 | hugo_symbol |

## 在代码中使用

```python
from skills.oncokb_query.scripts.query_variant import OncoKBQuery, OncoKBQueryInput
from core.skill import SkillContext

# 创建 Skill 实例
skill = OncoKBQuery()

# 创建上下文
context = SkillContext(session_id="patient_001")

# 构建查询
input_args = OncoKBQueryInput(
    query_type="variant",
    hugo_symbol="EGFR",
    variant="L858R",
    tumor_type="Non-Small Cell Lung Cancer"
)

# 执行查询
result_json = skill.execute_with_retry(input_args.model_dump(), context=context)
print(result_json)
```

## 参考资料

- [API 端点参考](references/api_endpoints.md)
- [证据等级详解](references/evidence_levels.md)
- [查询示例](examples/example_queries.md)

## 常见问题

**Q: 没有 API Token 可以用吗？**
A: 可以，会使用公共 API，但速率受限 (约 10 请求/分钟)。

**Q: 如何确定变异描述的格式？**
A: 使用蛋白质水平描述，如 L858R、V600E。也支持 HGVS 格式如 p.Leu858Arg。

**Q: 查询返回空结果怎么办？**
A: 检查基因符号是否为 HGNC 标准命名，变异描述是否准确。
