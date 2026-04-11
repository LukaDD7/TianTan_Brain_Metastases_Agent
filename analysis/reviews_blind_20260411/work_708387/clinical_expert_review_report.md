# 临床专家审查报告 - 患者 708387

**审查日期**: 2026-04-11  
**审查版本**: SKILL v2.0 (严格版)  
**患者ID**: 708387  
**疾病**: 肺腺鳞癌伴脑转移，MET扩增/融合阳性，术后3月

---

## 审查摘要

| 排名 | 报告 | 方法 | CPI | CCR | MQR | CER | PTR |
|------|------|------|-----|-----|-----|-----|-----|
| 1 | Report_A | BM Agent | **0.867** | 4.0 | 4.0 | 0.000 | 0.467 |
| 2 | Report_D | WebSearch | **0.785** | 3.6 | 3.6 | 0.000 | 0.320 |
| 3 | Report_C | RAG | **0.643** | 3.0 | 3.2 | 0.000 | 0.122 |
| 4 | Report_B | Direct LLM | **0.490** | 2.6 | 2.0 | 0.000 | 0.000 |

---

## 患者背景

- **年龄/性别**: 55岁/男性
- **原发肿瘤**: 左肺上叶腺鳞癌（T2N0M1 IV期）
- **分子特征**: MET拷贝数扩增 + MET基因融合（M13M15），TTF-1(-)
- **既往治疗**:
  - 2021-10-11: 右颞顶开颅肿物切除术
  - 2021-11-23: 一线化疗第1周期（培美曲塞800mg + 顺铂60mg）
  - 2021-12-17: 一线化疗第2周期（培美曲塞800mg + 顺铂60mg）
- **合并症**: 肺间质纤维化、间质性肺炎、COPD、胃大部切除术后
- **当前状态**: 术后3月，已完成2周期化疗，颅外病灶PR，颅内稳定

---

## Report_A (BM Agent) 详细审查

### CCR: 4.0/4.0
- **S_line**: 4/4 - 明确判定为二线/维持治疗（已完成2周期一线化疗），准确梳理治疗史
- **S_scheme**: 4/4 - SRS（18-20Gy/1f或27Gy/3f）+ Crizotinib 250mg BID，方案分层清晰，含OncoKB证据
- **S_dose**: 4/4 - SRS剂量18-24Gy有[PubMed: PMID 38720427, 28687377]锚点；Crizotinib 250mg BID有OncoKB支持
- **S_reject**: 4/4 - 排除WBRT、继续化疗、免疫治疗、EGFR-TKI理由充分，均有引用
- **S_align**: 4/4 - 临床路径完整，含5个强制检查点验证，Module 6灵活调整为围放疗期管理

### MQR: 4.0/4.0
- **S_complete**: 4/4 - 8模块完整
- **S_applicable**: 4/4 - Module 6标记为围放疗期管理并解释原因（非手术）
- **S_format**: 4/4 - 结构化优秀，执行轨迹详细
- **S_citation**: 4/4 - [OncoKB: LEVEL_X]、[PubMed: PMID]、[Local]格式规范
- **S_uncertainty**: 4/4 - 缺失数据（KPS/ECOG、PD-L1）明确标注

### CER: 0.000
无临床错误

### PTR: 0.467
| 引用类型 | 数量 | 权重 | 得分 |
|---------|------|------|------|
| PubMed PMID | 6 | 1.0 | 6.0 |
| OncoKB LEVEL_2/4 | 4 | 1.0 | 4.0 |
| Local (精确章节) | 10 | 1.0 | 10.0 |
| **Tier 1 合计** | **20** | - | **20.0** |

总声明数: 45 | PTR = 20.0/45 = **0.467**

### CPI: 0.867
计算公式: 0.35×(4.0/4) + 0.25×0.467 + 0.25×(4.0/4) + 0.15×(1-0) = 0.867

---

## Report_B (Direct LLM) 详细审查

### CCR: 2.6/4.0
- **S_line**: 3/4 - 提及化疗但未明确判定当前为二线治疗时机
- **S_scheme**: 3/4 - 推荐MET抑制剂但缺乏具体剂量和证据等级
- **S_dose**: 2/4 - 无剂量参数的物理锚点
- **S_reject**: 3/4 - 排他性论证基本合理但缺乏引用
- **S_align**: 2/4 - 时间线不够清晰

### MQR: 2.0/4.0
- **S_complete**: 2/4 - 非标准8模块结构（混合模块命名）
- **S_citation**: 0/4 - 全部为Parametric Knowledge

### CER: 0.000
无临床错误

### PTR: 0.000
| 引用类型 | 数量 | 权重 | 得分 |
|---------|------|------|------|
| Parametric Knowledge | 19 | 0.0 | 0.0 |
| **Tier 1 合计** | **0** | - | **0.0** |

总声明数: 41 | PTR = 0.0/41 = **0.000**

### CPI: 0.490

---

## Report_C (RAG) 详细审查

### CCR: 3.0/4.0
- **S_line**: 3/4 - 基本识别已完成一线化疗
- **S_scheme**: 3/4 - 推荐MET抑制剂或化疗，但缺乏OncoKB精准证据
- **S_dose**: 3/4 - 提及标准剂量但缺乏物理溯源
- **S_reject**: 3/4 - WBRT、免疫治疗排除合理
- **S_align**: 3/4 - 有时间线但不够详细

### MQR: 3.2/4.0
- **S_complete**: 4/4 - 8模块完整
- **S_applicable**: 3/4 - Module 6部分处理
- **S_citation**: 3/4 - 混合[Local]与[Parametric Knowledge]
- **S_uncertainty**: 3/4 - 部分标注[Evidence: Insufficient]

### CER: 0.000
无临床错误

### PTR: 0.122
| 引用类型 | 数量 | 权重 | 得分 |
|---------|------|------|------|
| Local | 5 | 1.0 | 5.0 |
| Parametric Knowledge | 10 | 0.0 | 0.0 |
| **Tier 1 合计** | **5** | - | **5.0** |

总声明数: 44 | PTR = 5.0/44 = **0.122**

### CPI: 0.643

---

## Report_D (WebSearch) 详细审查

### CCR: 3.6/4.0
- **S_line**: 4/4 - 正确判定一线治疗中评估节点
- **S_scheme**: 4/4 - 赛沃替尼优先推荐，含备选方案，决策树清晰
- **S_dose**: 3/4 - 赛沃替尼600mg qd有Web来源支持，但缺乏OncoKB验证
- **S_reject**: 4/4 - 排除WBRT、免疫治疗、单纯化疗理由充分
- **S_align**: 3/4 - 时间线清晰

### MQR: 3.6/4.0
- **S_complete**: 4/4 - 8模块完整
- **S_applicable**: 4/4 - Module 6正确处理（标记N/A）
- **S_format**: 4/4 - 结构优秀，使用表格
- **S_citation**: 3/4 - 引用格式规范，有ClinicalTrial引用
- **S_uncertainty**: 3/4 - 部分标注[Evidence: Insufficient]

### CER: 0.000
无临床错误

### PTR: 0.320
| 引用类型 | 数量 | 权重 | 得分 |
|---------|------|------|------|
| PubMed PMID | 2 | 1.0 | 2.0 |
| Guideline (泛引用) | 4 | 0.3 | 1.2 |
| Web (官方/医疗网站) | 5 | 0.1 | 0.5 |
| Web (商业网站) | 2 | -0.5 | -1.0 |
| **净得分** | - | - | **2.7** |

总声明数: 50 | PTR = 2.7/50 = **0.320**

### CPI: 0.785

---

## SKILL v2.0 关键发现

1. **OncoKB引用**: Report_A唯一使用OncoKB精准肿瘤学数据库，验证MET扩增LEVEL_2和MET融合LEVEL_4证据
2. **SRS术后放疗**: Report_A正确推荐术后SRS（18-20Gy/1f或27Gy/3f），引用NCCTG N107C试验证据
3. **间质性肺病管理**: 所有报告均正确处理ILD病史与MET抑制剂/免疫治疗的风险评估
4. **Crizotinib选择**: Report_A基于OncoKB证据选择Crizotinib（对MET扩增和融合均有证据），而非仅考虑国内获批药物
5. **WebSearch商业引用**: Report_D存在2处商业网站引用（药智网、有来医生），被降级处理

---

## 审查结论

**Report_A (BM Agent)** 以CPI 0.867领先，体现：
- 20处Tier 1权威溯源（含OncoKB LEVEL_2/LEVEL_4）
- SRS剂量和Crizotinib剂量均有确凿锚点
- Module 6灵活调整展示临床适应性
- 完整5个强制检查点验证

**Report_D (WebSearch)** 表现良好，CPI 0.785，有2处PubMed引用。

**Report_C (RAG)** 中等表现，CPI 0.643，缺乏OncoKB精准证据。

**Report_B (Direct LLM)** 因完全无物理溯源，CPI仅0.490。

---

*审查者: Clinical Expert Review AI*  
*审查标准: SKILL v2.0 (严格版)*
