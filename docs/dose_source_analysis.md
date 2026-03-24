# 临床剂量确定渠道与BM Agent问题分析

## 一、临床中剂量确定的渠道

### 1. 权威指南（第一优先级）
| 指南类型 | 示例 | 剂量信息位置 |
|---------|------|------------|
| NCCN指南 | NCCN CNS Cancers v3.2024 | Principles of Radiation Therapy (brain-c) |
| ESMO指南 | ESMO Brain Metastasis Guidelines | 治疗推荐表格 |
| ASCO指南 | ASCO-SNO-ASTRO Brain Metastases | Recommendation章节 |

**NCCN CNS指南中的SRS剂量（brain-c部分）：**
```
- 单次SRS: 15-24 Gy（基于肿瘤体积）
- 分次SRS: 27 Gy/3次 或 30 Gy/5次
- 术后SRS: 16-20 Gy/1次, 24-27 Gy/3次, 30 Gy/5次
```

### 2. 经典临床试验（第二优先级）
- **JLGK0901研究**（Yamamoto et al., Lancet Oncol 2014）：确立SRS在1-10个脑转移瘤中的标准地位
- **MD Anderson研究**：剂量-体积关系（12 Gy等效体积与放射性坏死）
- **RTOG 90-05**：最大耐受剂量研究（<2cm: 24Gy, 2-3cm: 18Gy, 3-4cm: 15Gy）

### 3. 药物说明书/FDA标签
- 化疗药物剂量通常来自关键III期临床试验
- 如：卡培他滨 1000-1250 mg/m² bid（来自X-ACT研究）

### 4. 专业共识/专家意见
- 当指南未覆盖特定情况时，参考专家共识
- 如：结直肠癌脑转移的特定剂量方案

---

## 二、BM Agent的问题分析

### 问题1：引用来源错误（最严重）

**报告中：**
```
SRS 18-24Gy/1f [PubMed: PMID 32921513]
```

**实际情况：**
- **NCCN指南**明确提到："MAXIMUM MARGINAL DOSES FROM 15-24 GY BASED ON TUMOR VOLUME"
- **PMID 32921513**（AAPM剂量耐受性综述）**并未明确提到18-24Gy范围**

**问题本质：**
- Agent正确获取了剂量信息（15-24Gy → 推断为18-24Gy）
- 但**错误标注了引用来源**（应引用NCCN指南，而非PubMed文章）

### 问题2：Agent检索策略缺陷

**执行日志显示Agent的检索：**
```bash
cat Guidelines/*/*.md | grep -i -C 5 "dose\|Gy\|fraction"
```

**问题：**
1. 检索过于宽泛，没有针对性搜索"Principles of Radiation Therapy"
2. 未识别到brain-c章节中包含SRS剂量信息
3. 当指南检索未明确找到剂量时，Agent转向PubMed检索
4. 在PubMed中找到PMID 32921513（剂量耐受性文章），但未核实是否支持具体数值

### 问题3：引用格式混淆

**正确格式：**
```
[Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: brain-c]
```

**错误格式：**
```
[PubMed: PMID 32921513]
```

**关键区别：**
- 指南引用应使用`[Local: ...]`格式
- PubMed引用应仅用于具体研究文献
- Agent混淆了这两者的使用场景

---

## 三、为什么Agent找不到NCCN指南中的剂量

### 1. 指南结构复杂
- NCCN指南使用`brain-c`等缩写指代章节
- Agent可能没有理解`brain-c`对应"Principles of Radiation Therapy"

### 2. 文本解析限制
- 指南是PDF转换的Markdown，存在OCR错误（如"1524 gY"可能是"15-24 Gy"）
- 剂量信息散落在段落中，不在表格中

### 3. 检索关键词不匹配
- Agent搜索："dose", "Gy", "fraction"
- 指南原文："MAXIMUM MARGINAL DOSES FROM 15-24 GY"
- 匹配度不高，容易被忽略

---

## 四、系统性解决方案

### 方案1：改进SKILL.md检索策略

在`universal_bm_mdt_skill/SKILL.md`中增加：
```markdown
### 剂量参数检索协议
1. 首先检索NCCN指南的"Principles of Radiation Therapy"章节
2. 使用命令：
   grep -i "principle.*radiation\|brain-c" Guidelines/NCCN*/*.md
3. 查找剂量模式：
   grep -oE "[0-9]+-[0-9]+\s*Gy|[0-9]+\s*Gy/[0-9]+" {file}
4. 如指南未找到，再检索PubMed，但需标注为"基于文献的推断"
```

### 方案2：建立剂量速查表

创建`references/srs_dosing_reference.json`：
```json
{
  "srs_single_fraction": {
    "dose_range": "15-24 Gy",
    "source": "NCCN CNS v3.2024, Section: brain-c",
    "note": "基于肿瘤体积，最大边缘剂量"
  },
  "srs_multi_fraction": {
    "dose_options": ["27 Gy/3f", "30 Gy/5f"],
    "source": "NCCN CNS v3.2024, Section: brain-c"
  }
}
```

### 方案3：改进引用格式检查

在`submit_mdt_report`工具中增加验证规则：
```python
if "SRS" in report and "[PubMed:" in report:
    # 检查是否也引用了NCCN指南
    if not re.search(r'NCCN.*brain-c', report):
        warning = "SRS剂量引用缺少NCCN指南来源，建议补充[Local: NCCN...]"
```

---

## 五、针对患者605525的修正建议

### 当前报告：
```markdown
放疗方案：SRS 18-24Gy/1f 或 FSRT 21Gy/3f [PubMed: PMID 38720427, PMID 32921513]
```

### 应修正为：
```markdown
放疗方案：SRS 18-24Gy/1f（基于肿瘤体积，NCCN推荐15-24Gy）或 FSRT 21Gy/3f

[Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: brain-c]
[PubMed: PMID 38720427 - 脑干转移瘤SRS 18Gy/FSRT 21Gy的中位剂量]
```

### 修正说明：
1. **18-24Gy范围** → 来自NCCN指南brain-c部分（15-24Gy），Agent合理推断
2. **21Gy/3f** → 来自PMID 38720427，准确引用
3. **删除PMID 32921513** → 该文章未明确支持18-24Gy范围

---

## 六、给临床医生的说明

### 为什么18-24Gy是合理的？

**证据链：**
1. **NCCN指南**：推荐15-24 Gy（基于肿瘤体积）
2. **RTOG 90-05**（经典研究）：
   - ≤2cm：24Gy
   - 2-3cm：18Gy
   - 3-4cm：15Gy
3. **临床实践**：18-24Gy是常见临床范围（小型病灶用高剂量，大型用低剂量）

**结论：**
虽然Agent引用格式有误，但剂量范围本身是基于指南的合理推断，临床可接受。

### 医生实际如何确定剂量？

**放疗科医生通常会参考：**
1. NCCN指南的一般推荐
2. 本单位的历史实践
3. 患者具体情况（病灶大小、位置、既往放疗史）
4. 正常组织耐受剂量（如脑干、视神经限制）

**所以：**
Agent报告的剂量范围是合理的临床参考，但最终剂量应由放疗科医生根据计划系统计算确定。
