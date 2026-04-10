# 天坛医院脑转移瘤 MDT 报告

**患者 ID**: 638114  
**入院时间**: 2021 年 01 月 08 日  
**报告生成日期**: 2021-01-12  

---

## Module 1: 入院评估 (Admission Evaluation)

### 1.1 人口学特征
- **年龄**: 57 岁
- **性别**: 男

### 1.2 原发肿瘤特征
- **病理类型**: 肺腺癌
- **分期**: 术后 IB 期 (2008 年)，现 IV 期伴脑转移
- **分子特征**: 
  - EGFR 19 外显子缺失突变 (2008 年手术标本) [Local: patient_638114_input.txt, Line 1]
  - EGFR T790M 突变 (2020 年 1 月手术标本) [Local: patient_638114_input.txt, Line 1]
  - 血 NGS 检测未见新基因突变 (2021-1-12) [Local: patient_638114_input.txt, Line 1]

### 1.3 脑转移特征
- **转移部位**: 右侧小脑半球（原位复发）、右侧桥小脑角、脑干及脑膜疑似转移
- **病灶大小**: 2020 年 1 月约 18×28mm，2021-1-8 MRI 示片状长 T2 长 T1 信号，不规则强化影 [Local: patient_638114_input.txt, Line 1]
- **症状**: 偶有头疼，无头晕、恶心呕吐 [Local: patient_638114_input.txt, Line 1]
- **KPS/ECOG**: unknown（病历未明确记录）

### 1.4 颅外疾病状态
- **胸部 CT**: 左肺上叶切除术后状态，左残肺条索影及微小结节影，左侧胸膜增厚 [Local: patient_638114_input.txt, Line 1]
- **腹部**: 肝实质密度减低，肝内低密度结节（性质待查）[Local: patient_638114_input.txt, Line 1]

### 1.5 既往治疗史
| 时间 | 治疗类型 | 具体方案 | 疗效 |
|------|----------|----------|------|
| 2008-12 | 手术 | 左肺上叶切除术 | DFS 60 个月 |
| 2013-12 | 放疗 | 伽马刀（右枕叶，36Gy/18Gy） | CR |
| 2013-12 起 | 靶向治疗 | 吉非替尼（一线） | DFS 50 个月 |
| 2018-02 | 放疗 | 伽马刀（右侧小脑半球，32Gy/16Gy） | PFS 15 个月 |
| 2020-01 | 手术 | 开颅肿瘤切除术 | PD |
| 2020-01 起 | 靶向治疗 | 奥西替尼（二线） | PFS 11 个月 |
| 2020-12 | 疾病进展 | 右小脑原位复发，脑干、脑膜疑似转移 | PD |
| 2021-01-08 | 靶向治疗 | 双倍量奥西替尼 | 病情平稳 |
| 2021-01-11 | 放疗 | 伽马刀（颅内病灶） | 治疗中 |

### 1.6 入院诊断
1. 恶性肿瘤靶向治疗
2. 肺腺癌术后
3. 脑继发恶性肿瘤
4. 反流性食管炎
5. 脑膜转移待除外 [Local: patient_638114_input.txt, Line 1]

---

## Module 2: 个体化治疗方案 (Primary Personalized Plan)

### 2.1 治疗线判定
**关键检查点**：
- ✅ 患者已接受系统治疗：一线吉非替尼 (2013-2018) + 二线奥西替尼 (2020-2020-12)
- ✅ 当前为疾病进展 (PD)：2020-12 右小脑原位复发
- ✅ **治疗线判定**: 后线治疗（三线及以上）

### 2.2 推荐治疗方案

#### 局部治疗（已完成）
- **立体定向放射外科 (SRS/伽马刀)**: 2021-1-11 已行伽马刀治疗
  - 推荐剂量：15-24 Gy 单次，或 27 Gy/3 次分割，或 30 Gy/5 次分割 [Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: BRAIN METASTASES]
  - 依据：NCCN 指南推荐 SRS 优先于 WBRT 用于有限脑转移瘤，可保护认知功能 [Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: BRAIN METASTASES]
  - 文献支持：术后 SRS 相比 WBRT 可改善局部控制并保持认知功能 [PubMed: PMID 28687377]

#### 系统治疗（继续当前方案）
- **奥西替尼双倍量**: 160mg QD（标准剂量 80mg QD 的双倍）
  - 依据：患者 2021-1-8 起已改为双倍量奥西替尼，目前病情平稳 [Local: patient_638114_input.txt, Line 1]
  - 指南推荐：EGFR 敏感突变阳性脑转移瘤首选奥西替尼 [Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: brain metastasesA: systemic therapy]
  - 证据等级：奥西替尼在 T790M 阳性患者中 PFS 显著优于铂类双药化疗 (10.1 vs 4.4 个月) [PubMed: PMID 28565936]
  - CNS 穿透性：奥西替尼具有更高的血脑屏障穿透能力，CNS 缓解率>60% [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]

#### 备选方案（如奥西替尼耐药）
- **铂类双药化疗**: 卡铂/顺铂 + 培美曲塞
  - 依据：奥西替尼耐药后标准治疗为铂类双药化疗 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]
  - 指南推荐：奥西替尼进展后推荐铂类双药化疗 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]
  - 文献支持：铂类药物是 NSCLC 标准化疗方案 [PubMed: PMID 35265202]

### 2.3 治疗目标
- 控制颅内病灶进展
- 延缓神经系统症状恶化
- 维持生活质量
- 延长生存期

---

## Module 3: 支持治疗 (Systemic Management)

### 3.1 颅内压管理
- **甘露醇**: 已使用（2021-1-11 伽马刀后）[Local: patient_638114_input.txt, Line 1]
  - 推荐剂量：20% 甘露醇 125-250ml 静脉滴注 Q6-8H（根据颅内压调整）
- **地塞米松**: 已使用（2021-1-11 伽马刀后）[Local: patient_638114_input.txt, Line 1]
  - 推荐剂量：4-8mg IV/PO Q12H，根据症状逐渐减量
  - 注意：长期使用需预防消化道出血、骨质疏松、血糖升高等并发症

### 3.2 癫痫预防
- 患者目前无癫痫发作，不推荐预防性抗癫痫治疗
- 如出现癫痫发作，首选左乙拉西坦（与靶向药物相互作用少）

### 3.3 脑膜转移管理（待排除）
- 2021-1-12 腰椎穿刺：压力 160mmH2O，脑脊液送检常规、生化、免疫、病理 [Local: patient_638114_input.txt, Line 1]
- 如确诊脑膜转移：
  - 可考虑奥西替尼双倍量（已有证据支持）
  - 或鞘内注射化疗（甲氨蝶呤/阿糖胞苷）
  - 全脑全脊髓放疗（选择性病例）

### 3.4 一般支持治疗
- 营养支持：保证足够热量和蛋白质摄入
- 心理支持：评估焦虑/抑郁状态
- 康复治疗：根据神经功能缺损情况进行康复训练

---

## Module 4: 随访与监测 (Follow-up & Monitoring)

### 4.1 影像学随访
- **头部 MRI 增强**: 每 2-3 个月复查（SRS 后建议每 2 个月）[Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: LIMITED BRAIN METASTASES]
  - 序列要求：T1 增强、T2、FLAIR、DWI
  - 评估标准：RANO-BM 标准
- **胸部 CT**: 每 3 个月复查
- **全身评估**: 每 6 个月或症状变化时行 PET-CT

### 4.2 疗效评估
- **颅内病灶**: RANO-BM 标准（CR/PR/SD/PD）
- **颅外病灶**: RECIST 1.1 标准
- **神经系统症状**: 记录头疼、头晕、肢体活动、认知功能等变化

### 4.3 不良反应监测
- **奥西替尼相关**: 
  - 皮疹、腹泻、甲沟炎（常见）
  - QT 间期延长、间质性肺病（罕见但严重）
  - 监测：心电图、肝功能、肾功能每 3 个月
- **放疗相关**:
  - 放射性坏死（SRS 后 3-6 个月高发）
  - 认知功能下降
  - 如出现新发神经症状，及时行 MRI 鉴别肿瘤进展 vs 放射性坏死

### 4.4 随访时间表
| 时间点 | 检查项目 |
|--------|----------|
| 出院后 1 个月 | 神经系统查体、头部 MRI |
| 出院后 2 个月 | 头部 MRI、血常规、生化 |
| 出院后 3 个月 | 头部 MRI、胸部 CT、心电图 |
| 之后每 2-3 个月 | 头部 MRI、临床评估 |

---

## Module 5: 被排除方案 (Rejected Alternatives)

### 5.1 全脑放疗 (WBRT)
- **排除理由**: 
  - 患者为有限脑转移瘤（目前主要为右侧小脑半球复发灶）
  - NCCN 指南推荐 SRS 优先于 WBRT，因 WBRT 与认知功能下降和生活质量降低相关 [Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: LIMITED BRAIN METASTASES]
  - 文献证据：SRS 相比 WBRT 可保持认知功能且总生存期相当 [PubMed: PMID 28687377]
  - 患者已接受过 2 次伽马刀治疗，尽量避免 WBRT 以减少累积毒性

### 5.2 第一代/第二代 EGFR-TKI（吉非替尼/厄洛替尼/阿法替尼）
- **排除理由**:
  - 患者已对吉非替尼耐药（DFS 50 个月后进展）
  - 存在 T790M 突变，对第一/二代 TKI 耐药
  - 指南推荐：T790M 阳性患者应使用奥西替尼 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]
  - 第一/二代 TKI  CNS 穿透性较差，对脑转移控制不佳

### 5.3 单纯化疗（无靶向治疗）
- **排除理由**:
  - 患者存在 EGFR 敏感突变和 T790M 突变，对 TKI 治疗敏感
  - 奥西替尼在 T790M 阳性患者中 PFS 显著优于化疗 [PubMed: PMID 28565936]
  - 化疗仅作为奥西替尼耐药后的备选方案
  - 患者目前对双倍量奥西替尼反应良好，病情平稳

### 5.4 再次手术切除
- **排除理由**:
  - 患者 2020 年 1 月已行开颅手术切除
  - 目前病灶位于右侧桥小脑角、小脑，手术风险高
  - 已行伽马刀治疗，局部控制率可期
  - 患者一般状况可，但多次开颅手术创伤大、恢复慢

---

## Module 6: 围手术期/放疗期管理 (Peri-procedural Holding Parameters)

**注**: 患者当前治疗为放疗 + 系统治疗，无手术计划。本模块针对放疗期间系统治疗管理。

### 6.1 奥西替尼围放疗期管理
- **推荐**: 奥西替尼可继续服用，无需停药
  - 依据：奥西替尼与放疗联合安全性良好，无显著增加放射性坏死风险
  - 文献支持：奥西替尼与 SRS 联合治疗脑转移瘤安全有效 [PubMed: PMID 33435596]
  - 监测：注意皮疹、腹泻等不良反应叠加

### 6.2 地塞米松管理
- **放疗期间**: 4-8mg Q12H，预防放疗后脑水肿
- **放疗后**: 根据症状逐渐减量，每 3-5 天减量一次
- **停药指征**: 无颅内高压症状，MRI 示水肿消退

### 6.3 甘露醇使用
- **指征**: 颅内高压症状（头疼、恶心呕吐、视乳头水肿）
- **剂量**: 20% 甘露醇 125-250ml 静脉滴注 Q6-8H
- **停药**: 症状缓解后逐渐减量停药

### 6.4 放射性坏死监测
- **高危因素**: 既往多次放疗（患者已接受 3 次伽马刀）
- **监测**: SRS 后 3-6 个月行 MRI 增强检查
- **鉴别**: 肿瘤进展 vs 放射性坏死（必要时行灌注 MRI、波谱分析或 PET）
- **治疗**: 如确诊放射性坏死，可考虑贝伐珠单抗治疗

---

## Module 7: 分子病理建议 (Molecular Pathology Orders)

### 7.1 已完成检测
- **EGFR 19 外显子缺失突变**: 阳性 (2008 年手术标本) [Local: patient_638114_input.txt, Line 1]
- **EGFR T790M 突变**: 阳性 (2020 年手术标本) [Local: patient_638114_input.txt, Line 1]
- **血 NGS 检测**: 未见新基因突变 (2021-1-12) [Local: patient_638114_input.txt, Line 1]

### 7.2 待补充检测（如疾病再次进展）
- **组织再活检**: 推荐对复发灶行穿刺或手术活检
  - 检测内容：NGS 大 panel（包括 EGFR C797S、MET 扩增、HER2 扩增等奥西替尼耐药机制）
  - 依据：奥西替尼耐药机制多样，需明确耐药突变指导后线治疗 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]
  - 指南推荐：奥西替尼进展后推荐 NGS 检测 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]

- **脑脊液检测**: 如脑膜转移确诊
  - 检测内容：脑脊液细胞学、NGS 检测（cfDNA）
  - 依据：脑脊液检测可提高脑膜转移诊断敏感性

### 7.3 常见奥西替尼耐药机制及对应治疗
| 耐药机制 | 频率 | 推荐治疗 |
|----------|------|----------|
| EGFR C797S | 10-15% | 一代 + 三代 TKI 联合（如厄洛替尼 + 奥西替尼） |
| MET 扩增 | 5-15% | 奥西替尼 + MET 抑制剂（卡马替尼/特泊替尼） |
| HER2 扩增 | 5-10% | 奥西替尼 + 抗 HER2 治疗 |
| 小细胞转化 | 3-5% | 铂类 + 依托泊苷化疗 |
| 未知机制 | 30-40% | 铂类双药化疗 ± 免疫治疗 |

---

## Module 8: 智能体执行轨迹 (Agent Execution Trajectory)

### 8.1 指南检索
```bash
# 检索 ESMO 指南关于 EGFR 突变 NSCLC 治疗推荐
grep -i -C 5 "EGFR\|osimertinib\|T790M\|dose" Guidelines/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md

# 检索 NCCN CNS 指南关于脑转移瘤放疗剂量
grep -i -C 10 "brain mets\|metastases\|SRS\|WBRT\|dose\|Gy" Guidelines/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md

# 检索脑转移瘤系统治疗推荐
grep -i -A 50 "brain metastasesA: systemic therapy" Guidelines/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md
```

### 8.2 PubMed 检索
```bash
# 检索奥西替尼耐药后治疗
search_pubmed.py --query "EGFR T790M osimertinib resistance brain metastases AND chemotherapy OR platinum" --max-results 5

# 检索奥西替尼耐药后化疗证据
search_pubmed.py --query "osimertinib resistance AND platinum-doublet chemotherapy AND NSCLC AND brain metastases" --max-results 5

# 检索 SRS 放疗剂量
search_pubmed.py --query "stereotactic radiosurgery AND brain metastases AND dose AND fraction AND gamma knife" --max-results 5
```

### 8.3 关键证据汇总
1. **NCCN CNS 指南 (v3.2024)**:
   - SRS 剂量推荐：15-24 Gy 单次，或 27 Gy/3 次，或 30 Gy/5 次 [Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: BRAIN METASTASES]
   - EGFR 突变脑转移首选奥西替尼 [Local: NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md, Section: brain metastasesA: systemic therapy]

2. **ESMO 指南**:
   - T790M 阳性患者推荐奥西替尼 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]
   - 奥西替尼进展后推荐铂类双药化疗 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Line 1]

3. **PubMed 文献**:
   - 奥西替尼在 T790M 阳性患者中 PFS 优于化疗 [PubMed: PMID 28565936]
   - SRS 术后相比 WBRT 保持认知功能 [PubMed: PMID 28687377]
   - 奥西替尼与放疗联合安全 [PubMed: PMID 33435596]

---

## 总结与推荐

### 核心推荐
1. **继续当前双倍量奥西替尼治疗** (160mg QD)，病情平稳
2. **已完成伽马刀治疗**，按计划随访头部 MRI
3. **等待脑脊液检查结果**，排除脑膜转移
4. **如疾病再次进展**，推荐组织活检 + NGS 检测，根据耐药机制选择后线治疗

### 预后评估
- 患者 EGFR 19 外显子突变 + T790M 阳性，对奥西替尼敏感
- 已接受多次局部治疗（2 次伽马刀 +1 次开颅手术），颅内病灶控制尚可
- 需密切监测奥西替尼耐药迹象，及时干预

### 多学科协作建议
- **神经外科**: 定期评估手术指征（如大病灶占位效应明显）
- **放疗科**: 随访放射性坏死，必要时干预
- **肿瘤内科**: 调整系统治疗方案，管理不良反应
- **神经内科**: 评估神经系统症状，指导康复治疗

---

**报告生成时间**: 2021-01-12  
**MDT 团队**: 天坛医院脑转移瘤多学科诊疗团队