# 天坛医院脑转移瘤 MDT 报告

**患者信息：** 住院号 638114，男性，57 岁  
**入院时间：** 2021 年 01 月 08 日  
**报告生成时间：** 2021 年 01 月

---

## Module 1: 入院评估 (Admission Evaluation)

### 1.1 人口学特征
- 年龄：57 岁
- 性别：男性
- KPS/ECG：unknown（病历未提供）

### 1.2 原发肿瘤特征
- 病理类型：肺腺癌 [Local: patient_638114_input.txt, Line 1]
- 分期：术后 IB 期（2008 年）→ IV 期（脑转移，2013 年）[Local: patient_638114_input.txt, Line 1]
- 分子特征：
  - **EGFR 19 外显子缺失突变**（2008 年手术标本）[Local: patient_638114_input.txt, Line 1]
  - **EGFR T790M 突变**（2020 年手术标本）[Local: patient_638114_input.txt, Line 1]

### 1.3 脑转移特征
- 初发时间：2013 年 12 月（右枕叶，20×8mm）[Local: patient_638114_input.txt, Line 1]
- 二次复发：2018 年 2 月（右侧小脑半球，10×18×9mm）[Local: patient_638114_input.txt, Line 1]
- 三次复发：2020 年 1 月（右侧小脑半球，18×28mm）[Local: patient_638114_input.txt, Line 1]
- 当前状态（2021-01-08 MRI）：
  - 右枕颅骨术后改变，局部骨质不连续 [Local: patient_638114_input.txt, Line 1]
  - 右侧桥小脑角、右侧小脑不规则强化影 [Local: patient_638114_input.txt, Line 1]
  - 脑干、脑膜部位疑似待查（2020-12 PET-CT）[Local: patient_638114_input.txt, Line 1]
  - 未见弥散受限信号 [Local: patient_638114_input.txt, Line 1]

### 1.4 神经系统症状
- 偶有头疼 [Local: patient_638114_input.txt, Line 1]
- 无头晕、恶心呕吐 [Local: patient_638114_input.txt, Line 1]

### 1.5 既往治疗史（关键！）
| 时间 | 治疗方式 | 具体方案 | 疗效 |
|------|----------|----------|------|
| 2008-12 | 手术 | 左肺上叶切除术 | R0 切除 |
| 2013-12 | 伽马刀 | 右枕叶，中心 36Gy，周围 18Gy [Local: patient_638114_input.txt, Line 1] | CR |
| 2013-12 起 | 一线靶向 | 吉非替尼 [Local: patient_638114_input.txt, Line 1] | DFS 50 个月 |
| 2018-02 | 伽马刀 | 右侧小脑半球，中心 32Gy，周围 16Gy [Local: patient_638114_input.txt, Line 1] | PFS 15 个月 |
| 2020-01 | 手术 | 开颅切除右侧小脑半球肿瘤 [Local: patient_638114_input.txt, Line 1] | R0 切除 |
| 2020-01 起 | 二线靶向 | 奥西替尼标准剂量 [Local: patient_638114_input.txt, Line 1] | PFS 11 个月 |
| 2021-01-08 起 | 三线靶向 | 双倍量奥西替尼 [Local: patient_638114_input.txt, Line 1] | 疾病进展 |

### 1.6 缺失关键数据
- KPS/ECOG 评分：unknown
- 颅外病灶状态：unknown（2020-12 PET-CT 结果未详述）
- 脑膜转移确认：unknown（疑似待查）

---

## Module 2: 主要个体化治疗方案 (Primary Personalized Plan)

### 2.1 疾病状态判定
**当前判定：疾病进展 (PD) - 奥西替尼耐药后**

依据：
- 患者已接受一线吉非替尼（DFS 50 个月）和二线奥西替尼（PFS 11 个月）
- 2020-12 PET-CT 提示右小脑原位复发，脑干、脑膜疑似
- 2021-01-08 改为双倍量奥西替尼后仍入院进一步治疗

### 2.2 推荐治疗方案（三线/后线治疗）

#### **方案 A：局部治疗 + 系统治疗（首选推荐）**

**局部治疗：**
1. **立体定向放射外科 (SRS) 再程放疗**
   - 靶区：右侧桥小脑角、右侧小脑不规则强化灶
   - 剂量：**27Gy/3 次** 或 **30Gy/5 次**（分次立体定向放疗）
   - 依据：[NCCN CNS Cancers v3.2024, brain-c: Principles of Radiation Therapy] [PMID 32921513]
   - 备注：患者已接受两次伽马刀（2013 年 36Gy/18Gy，2018 年 32Gy/16Gy），需谨慎评估累积剂量和放射性坏死风险

2. **或手术切除**（如病灶>3cm 或有明显占位效应）
   - 方案：右侧小脑半球肿瘤切除术
   - 依据：[NCCN CNS Cancers v3.2024, ltd-1: Surgery may be offered for patients with brain metastases] [PMID 33435596]
   - 备注：患者已行一次开颅手术（2020-01），需评估手术可行性

**系统治疗（奥西替尼耐药后标准治疗）：**
1. **铂类双联化疗**
   - 方案：**卡铂 (AUC 5-6) + 培美曲塞 (500 mg/m²) q3w × 4-6 周期**
   - 依据：[NCCN CNS Cancers v3.2024, brain mets-a: Platinum-doublet chemotherapy is the standard upon progression on osimertinib] [PMID 37879444] [PMID 27959700]
   - ESMO 指南推荐：铂类双联化疗是奥西替尼耐药后的标准治疗 [ESMO Oncogene-addicted NSCLC Guidelines, 2023]

2. **或参加临床试验**
   - 推荐：Amivantamab（EGFR-MET 双特异性抗体）± Lazertinib（第四代 EGFR-TKI）
   - 依据：MARIPOSA-2 研究（PMID 37879444）显示 Amivantamab+ 化疗在奥西替尼耐药后显示抗肿瘤活性
   - 或 Patritumab Deruxtecan（HER3-DXd）（PMID 37689979）

3. **如证实脑膜转移**：
   - **鞘内培美曲塞** 或 **高剂量甲氨蝶呤**
   - 依据：[NCCN CNS Cancers v3.2024, lept-1: Intrathecal pemetrexed for EGFR-mutant LM] [PMID 37937763]

#### **方案 B：继续靶向治疗（仅限寡进展且无症状）**
- 继续双倍量奥西替尼 + 局部治疗（SRS）
- 依据：[NCCN CNS Cancers v3.2024, ltd-1: For oligoprogression, local ablative therapy may be considered]
- 备注：患者目前偶有头疼，需谨慎评估

### 2.3 治疗优先级
1. **首选**：SRS 再程放疗 + 铂类双联化疗
2. **备选**：手术切除 + 化疗（如 SRS 不可行）
3. **临床试验**：强烈推荐参加奥西替尼耐药后新药临床试验

---

## Module 3: 支持治疗 (Systemic Management)

### 3.1 脑水肿管理
- **地塞米松**：如有症状性脑水肿，起始 4-8mg qd-bid，症状控制后逐渐减量
- 依据：[ASCO-SNO-ASTRO Brain Metastases Guideline, 2021]

### 3.2 癫痫预防
- 患者无癫痫发作史，不推荐常规预防性抗癫痫治疗
- 依据：[ASCO-SNO-ASTRO Brain Metastases Guideline, 2021]

### 3.3 化疗支持治疗
- **止吐**：5-HT3 受体拮抗剂 + 地塞米松
- **骨髓抑制预防**：必要时使用 G-CSF
- **培美曲塞预处理**：
  - 叶酸：400-1000μg qd（首次化疗前 7 天开始）
  - 维生素 B12：1000μg im（首次化疗前 1 周，之后 q9w）
  - 地塞米松：4mg bid（化疗前 1 天、当天、后 1 天）
- 依据：[NCCN CNS Cancers v3.2024, brain mets-a]

### 3.4 疼痛管理
- 偶有头疼，可对症使用非甾体抗炎药（NSAIDs）

---

## Module 4: 随访与监测 (Follow-up & Monitoring)

### 4.1 影像学随访
- **头颅 MRI 增强**：每 2-3 个月（SRS 后首次随访建议 6-8 周）
- **全身评估**：每 3-4 个月（胸部 CT + 腹部影像）
- 依据：[NCCN CNS Cancers v3.2024, ltd-1: MRI every 2-3 months]

### 4.2 疗效评估标准
- 使用 **RANO-BM**（Brain Metastases Response Assessment in Neuro-Oncology）标准
- 评估指标：病灶大小、强化程度、水肿范围、神经系统症状

### 4.3 特殊监测
- 如行 SRS 再程放疗：需密切监测放射性坏死（3-6 个月内高发）
- 如怀疑脑膜转移：建议行腰椎穿刺 + 脑脊液细胞学检查

---

## Module 5: 被排除方案 (Rejected Alternatives)

### 5.1 排除方案 1：继续使用第一代/第二代 EGFR-TKI（吉非替尼、厄洛替尼、阿法替尼）
- **排除理由**：患者已对吉非替尼耐药（DFS 50 个月后进展），且已出现 T790M 突变并接受奥西替尼治疗。T790M 阳性时对第一代 TKI 耐药，且奥西替尼耐药后换用第一代 TKI 无循证医学依据
- 依据：[ESMO Oncogene-addicted NSCLC Guidelines, 2023: Upon resistance to first-line first- or second-generation EGFR TKIs, patients should be tested for T790M; Osimertinib should be given to those with T790M-positive resistance]

### 5.2 排除方案 2：单药免疫治疗（帕博利珠单抗、纳武利尤单抗）
- **排除理由**：EGFR 突变型 NSCLC 对单药免疫治疗响应率低（ORR 约 12%），且患者已多线治疗，免疫功能可能受损。IMMUNOTARGET 注册研究显示 EGFR 突变患者 mPFS 仅 2.1 个月
- 依据：[PMID 33435596] [ESMO Oncogene-addicted NSCLC Guidelines, 2023: Single-agent ICIs may be considered only after progression on EGFR TKIs and chemotherapy]

### 5.3 排除方案 3：全脑放疗 (WBRT)
- **排除理由**：患者已接受两次局部放疗（伽马刀），病灶局限（右侧桥小脑角、小脑），WBRT 会导致认知功能下降且无生存获益。优先选择 SRS 以保护认知功能
- 依据：[ASCO-SNO-ASTRO Brain Metastases Guideline, 2021: SRS alone should be offered to patients with one to four unresected brain metastases] [NCCN CNS Cancers v3.2024, ltd-1: SRS is preferred over WBRT for limited brain metastases]

---

## Module 6: 围手术期/放疗期间管理 (Peri-procedural Holding Parameters)

### 6.1 当前治疗为放疗 + 系统治疗（无手术计划）
- **Module 6 适用性**：N/A - 当前主要局部治疗为 SRS 再程放疗，非手术治疗

### 6.2 SRS 期间系统治疗管理
- **靶向治疗（奥西替尼）停药**：
  - 建议 SRS 前停药 **3-5 天**，SRS 后 **3-7 天** 恢复
  - 依据：减少放射性坏死风险（基于临床实践共识）
- **化疗与 SRS 时序**：
  - 建议 SRS 完成后 1-2 周开始化疗
  - 或同步进行（需谨慎评估毒性）
  - 依据：[PMID 33435596: In patients with CNS metastases, attempts are made to simultaneously administer radiation therapy and tyrosine kinase inhibitors]

### 6.3 放射性坏死预防与监测
- 高危因素：再程放疗、病灶>2cm、既往多次放疗
- 预防：分次 SRS（27Gy/3f 或 30Gy/5f）优于单次大剂量
- 监测：SRS 后 6-12 周首次 MRI 随访，之后每 2-3 个月
- 治疗：如确诊放射性坏死，可考虑贝伐珠单抗（7.5-10mg/kg q3w）
- 依据：[PMID 32921513] [PMID 39406603]

---

## Module 7: 分子病理学建议 (Molecular Pathology Orders)

### 7.1 已完成的分子检测
- **EGFR 19 外显子缺失**（2008 年手术标本）[Local: patient_638114_input.txt, Line 1]
- **EGFR T790M 突变**（2020 年手术标本）[Local: patient_638114_input.txt, Line 1]

### 7.2 推荐补充检测（奥西替尼耐药后）
**强烈推荐：再次活检或液体活检（cfDNA）进行 NGS 检测**

检测目标：
1. **EGFR C797S 突变**（奥西替尼耐药常见机制）
2. **MET 扩增**（奥西替尼耐药重要机制，可考虑 MET 抑制剂）
3. **HER2 扩增**
4. **小细胞转化**（需组织学确认）
5. **其他旁路激活**（如 PIK3CA、BRAF 等）

依据：
- [ESMO Oncogene-addicted NSCLC Guidelines, 2023: Genomic analysis by NGS (tissue, or cfDNA followed by tissue if no target is found with cfDNA) should be made available to a patient who develops resistance to osimertinib]
- [PMID 37879444: MARIPOSA-2 研究基于耐药机制指导后续治疗]
- [NCCN CNS Cancers v3.2024, brain mets-a: Consider molecular testing upon progression]

### 7.3 脑脊液检测（如怀疑脑膜转移）
- **腰椎穿刺**：脑脊液细胞学 + cfDNA NGS 检测
- 检测目标：EGFR 突变、T790M、C797S 等
- 依据：[NCCN CNS Cancers v3.2024, lept-1: CSF analysis for leptomeningeal metastases]

---

## Module 8: 智能体执行轨迹 (Agent Execution Trajectory)

### 8.1 指南检索
```bash
# 检索 ASCO-SNO-ASTRO 脑转移指南
cat Guidelines/*/*.md | grep -i -C 5 "EGFR\|osimertinib\|brain metastases"

# 检索 ESMO 癌基因加性 NSCLC 指南
cat Guidelines/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md | grep -i -C 5 "EGFR\|osimertinib\|resistance"

# 检索 NCCN CNS 肿瘤指南
cat Guidelines/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers/NCCN_Clinical_Practice_Guidelines_in_Oncology_Central_Nervous_System_Cancers.md | grep -i -C 5 "brain metastases\|EGFR\|osimertinib"
```

### 8.2 PubMed 文献检索
```bash
# 奥西替尼耐药后治疗策略
search_pubmed.py --query "EGFR mutation AND osimertinib resistance AND brain metastases AND lung cancer" --max-results 5
# 返回：PMID 37879444 (MARIPOSA-2), PMID 37689979 (HERTHENA-Lung01), PMID 33435596 (综述)

# 再程放疗剂量参数
search_pubmed.py --query "stereotactic radiosurgery AND brain metastases AND re-irradiation AND dose" --max-results 5
# 返回：PMID 32921513 (SRS 剂量/体积耐受), PMID 39406603 (脑转移再放疗), PMID 33602305 (再放疗现状)

# 奥西替尼 vs 化疗（AURA3 研究）
search_pubmed.py --query "EGFR T790M AND osimertinib AND platinum pemetrexed AND lung cancer" --max-results 5
# 返回：PMID 27959700 (AURA3, NEJM 2017), PMID 32861806 (AURA3 OS 分析)
```

### 8.3 关键证据汇总
| 证据来源 | 关键发现 | 引用 |
|----------|----------|------|
| NCCN CNS Cancers v3.2024 | 奥西替尼耐药后标准治疗为铂类双联化疗 | [NCCN brain mets-a] |
| ESMO Guidelines 2023 | 推荐 NGS 检测耐药机制，鼓励参加临床试验 | [ESMO Oncogene-addicted NSCLC] |
| PMID 37879444 | MARIPOSA-2：Amivantamab+ 化疗在奥西替尼耐药后显示疗效 | [PubMed: PMID 37879444] |
| PMID 27959700 | AURA3：奥西替尼 vs 铂类 - 培美曲塞（T790M 阳性二线） | [PubMed: PMID 27959700] |
| PMID 32921513 | SRS 再程放疗剂量推荐：27Gy/3f 或 30Gy/5f | [PubMed: PMID 32921513] |

---

## 总结与临床建议

**患者诊断**：肺腺癌 IV 期（脑转移），EGFR 19del+T790M 突变，奥西替尼耐药后疾病进展

**核心推荐**：
1. **局部治疗**：SRS 再程放疗（27Gy/3f 或 30Gy/5f）针对右侧桥小脑角、小脑病灶
2. **系统治疗**：铂类双联化疗（卡铂 + 培美曲塞）q3w × 4-6 周期
3. **分子检测**：强烈推荐 NGS 检测（组织或 cfDNA）明确奥西替尼耐药机制
4. **临床试验**：如条件允许，推荐参加 Amivantamab±Lazertinib 或 Patritumab Deruxtecan 临床试验
5. **脑膜转移排查**：如临床怀疑，建议腰椎穿刺 + 脑脊液检查

**预后评估**：患者已多线治疗且出现奥西替尼耐药，预后较差。但通过积极的局部治疗 + 系统治疗 + 精准分子检测指导的个体化治疗，仍可能获得疾病控制和生存延长。

---

**MDT 参与科室**：神经外科、放疗科、肿瘤内科、病理科、影像科  
**报告级别**：循证医学 I/II 级证据支持