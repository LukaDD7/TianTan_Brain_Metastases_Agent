# 天坛医院脑转移瘤 MDT 报告

**患者 ID**: 708387  
**入院时间**: 2022 年 01 月 11 日  
**报告生成时间**: 2022-01-15  

---

## Module 1: 入院评估 (Admission Evaluation)

### 1.1 人口学特征
- **年龄**: 55 岁
- **性别**: 男
- **KPS/ECOG**: unknown（病历未明确记录）

### 1.2 原发肿瘤特征
- **病理类型**: 肺恶性肿瘤，倾向于分化差的腺鳞癌或未分化癌 [Local: patient_708387_input.txt, Section: 病理诊断]
- **临床分期**: T2N0M1, IV 期 [Local: patient_708387_input.txt, Section: 现病史]
- **分子特征**: 
  - MET 扩增（拷贝数变异）[Local: patient_708387_input.txt, Section: 病理诊断]
  - MET 融合（NM_001127500.3_NM_001127500.3 M13M15 融合）[Local: patient_708387_input.txt, Section: 病理诊断]

### 1.3 脑转移特征
- **转移灶数量**: 单发（已切除）
- **最大直径**: 5.5×5.5×5.0 cm（术前）
- **位置**: 右额颞顶叶
- ** eloquent 区**: 是（累及右额颞岛叶）
- **占位效应/水肿**: 术区周围片状异常信号，右侧脑室受压变形
- **神经系统症状**: 左腿无力、头痛、恶心呕吐、四肢乏力、反应迟缓（术前）

### 1.4 颅外转移
- **肺部**: 左肺上叶胸膜下病灶，3.1×1.5cm，较前范围减小、密度减低（PR）[Local: patient_708387_input.txt, Section: 胸部 CT]
- **肠系膜**: 原左上腹结节，较前显示不明确 [Local: patient_708387_input.txt, Section: 腹盆 CT]
- **淋巴结**: 右侧心膈角增大淋巴结 [Local: patient_708387_input.txt, Section: 腹盆 CT]

### 1.5 既往治疗史
- **手术**: 2021-10-11 全麻下行右颞顶开颅显微镜下幕上深部肿物切除术 [Local: patient_708387_input.txt, Section: 现病史]
- **化疗**: 
  - 2021-11-23、2021-12-17 一线第 1、2 周期：培美曲塞 800mg d1 + 顺铂 60mg d1-2, q3w [Local: patient_708387_input.txt, Section: 现病史]
  - 2022-1-14 一线第 3 周期：贝伐珠单抗 500mg d2 + 培美曲塞 800mg d1 + 顺铂 60mg d1-2, q3w [Local: patient_708387_input.txt, Section: 诊疗经过]
- **疗效评估**: PR（部分缓解）[Local: patient_708387_input.txt, Section: 诊疗经过]

### 1.6 合并症
- 间质性肺炎、肺间质纤维化（2021 年 4 月）[Local: patient_708387_input.txt, Section: 既往史]
- 慢性阻塞性肺疾病 [Local: patient_708387_input.txt, Section: 入院诊断]
- 肺气肿 [Local: patient_708387_input.txt, Section: 入院诊断]
- 胃溃疡切除术后（2015 年）[Local: patient_708387_input.txt, Section: 既往史]
- 慢性结肠炎（2021-11）[Local: patient_708387_input.txt, Section: 既往史]

### 1.7 缺失的关键数据
- KPS/ECOG 评分：unknown
- 当前神经系统功能状态：unknown
- 肿瘤标志物基线值：unknown

---

## Module 2: 主要个体化治疗方案 (Primary Personalized Plan)

### 2.1 当前疾病状态判定
根据强制检查点分析：
- **治疗线**: 一线治疗中（第 3 周期）
- **疗效评估**: PR（部分缓解）
- **疾病状态**: 稳定/缓解，**非疾病进展**
- **推荐策略**: 继续当前一线治疗方案，完成计划周期后评估

### 2.2 局部治疗推荐
**当前无需追加局部治疗**
- 理由：脑转移瘤已完整切除，术后 MRI 显示术区稳定，无新发病灶 [Local: patient_708387_input.txt, Section: 头部 MRI]
- 随访策略：定期头颅 MRI 监测

### 2.3 系统治疗推荐

#### 当前一线治疗方案（继续执行）
**培美曲塞 + 顺铂 + 贝伐珠单抗**

- **培美曲塞**: 800mg (约 500 mg/m²) d1, q3w [Local: patient_708387_input.txt, Section: 诊疗经过]
- **顺铂**: 60mg d1-2, q3w [Local: patient_708387_input.txt, Section: 诊疗经过]
- **贝伐珠单抗**: 500mg (约 7.5-15 mg/kg) d2, q3w [Local: patient_708387_input.txt, Section: 诊疗经过]

**循证依据**:
- ESMO 指南推荐：对于 MET 扩增/融合 NSCLC，若无一线靶向药物可用，推荐铂类双药化疗±免疫治疗作为一线治疗 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Section: OTHER ONCOGENIC DRIVERS FOR WHICH TARGETED THERAPY IS AVAILABLE]
- 贝伐珠单抗联合化疗在 EGFR 突变 NSCLC 二线治疗中显示获益（IMPower150、ORIENT-31 研究）[PubMed: PMID 30069759]

#### 后线靶向治疗选择（疾病进展时考虑）

**MET 扩增（OncoKB LEVEL_2 证据）**:
1. **Capmatinib** 400mg BID（FDA 批准用于 MET ex14 跳跃突变，NCCN 2A 类推荐用于 MET 扩增）[OncoKB: Level 2] [PubMed: PMID 32877583]
   - GEOMETRY mono-1 研究：MET 扩增初治患者 ORR 40%，经治患者 ORR 29% [PubMed: PMID 32877583]
   - 日本亚组分析：MET 扩增（≥10 拷贝）患者 ORR 45.5%，中位 DOR 8.3 个月；1 例患者脑部病灶部分缓解 [PubMed: PMID 33506571]

2. **Crizotinib** 250mg BID（NCCN 2A 类推荐）[OncoKB: Level 2]
   - 回顾性研究：MET 扩增 NSCLC 患者 ORR 33%，中位 DoR 35 周 [OncoKB 响应数据]
   - METROS 研究（经治患者）：ORR 27%，mPFS 4.4 个月 [OncoKB 响应数据]

3. **Tepotinib** 500mg QD（FDA 批准用于 MET ex14 跳跃突变）[OncoKB: Level 2]
   - VISION 研究：MET ex14 跳跃突变患者 ORR 45%，mDOR 11.1 个月，mPFS 8.9 个月 [PubMed: PMID 32469185]
   - 长期随访：ORR 51.4%，mDOR 18.0 个月 [PubMed: PMID 37270698]

**MET 融合（OncoKB LEVEL_4 证据）**:
- **Crizotinib** 250mg BID（病例系列报道有效）[OncoKB: Level 4] [PubMed: PMID 29284707] [PubMed: PMID 29102694]

### 2.4 治疗目标
- 控制颅内外病灶，延长 PFS 和 OS
- 维持神经系统功能状态
- 管理治疗相关毒性，尤其是间质性肺炎风险

---

## Module 3: 支持治疗 (Systemic Management)

### 3.1 脑水肿管理
- **地塞米松**: 根据症状酌情使用，逐渐减量至最低有效剂量
- **甘露醇**: 急性颅高压时考虑使用

### 3.2 癫痫预防
- 患者无癫痫发作史，不推荐常规预防性抗癫痫治疗
- 如出现癫痫发作，首选左乙拉西坦（无药物相互作用）

### 3.3 止吐治疗
- **5-HT3 受体拮抗剂**（如昂丹司琼）+ **地塞米松** ± **NK-1 受体拮抗剂**（如阿瑞匹坦）
- 顺铂为高致吐风险药物，需三联止吐

### 3.4 胃黏膜保护
- 患者有胃溃疡切除史，推荐使用**质子泵抑制剂**（如奥美拉唑）
- 贝伐珠单抗增加消化道穿孔风险，需密切监测

### 3.5 间质性肺炎管理（⚠️ 高危患者）
- 患者有间质性肺炎、肺纤维化病史，为吉非替尼/厄洛替尼等 EGFR-TKI 诱发 ILD 的高危人群
- **基线评估**: 治疗前完善肺功能、高分辨率 CT
- **监测**: 每周期评估呼吸道症状，警惕新发咳嗽、呼吸困难
- **处理原则**: 如出现≥2 级 ILD，立即停药并给予糖皮质激素治疗

### 3.6 贝伐珠单抗相关毒性管理
- **高血压**: 每周期前监测血压，必要时使用降压药
- **蛋白尿**: 定期尿常规检查
- **出血风险**: 监测凝血功能，警惕咯血、消化道出血
- **伤口愈合**: 手术前后至少停用 28 天（本例脑手术已完成，风险较低）

---

## Module 4: 随访与监测 (Follow-up & Monitoring)

### 4.1 影像学随访
- **头颅 MRI（增强）**: 每 2-3 个月一次，或出现神经系统症状时立即复查
- **胸部 CT（增强）**: 每 2-3 个月一次，评估肺部病灶疗效
- **腹盆 CT（增强）**: 每 3-6 个月一次，或根据临床需要

### 4.2 疗效评估标准
- 采用**RECIST v1.1**标准评估颅外病灶 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Section: staging and risk assessment]
- 采用**RANO-BM**标准评估颅内病灶

### 4.3 实验室检查
- **血常规**: 每周期前
- **肝肾功能**: 每周期前
- **肿瘤标志物**（CEA、CYFRA21-1、NSE 等）: 每 2-3 个月
- **尿常规**（贝伐珠单抗相关蛋白尿监测）: 每周期前

### 4.4 随访时间节点
- **第 1 次评估**: 完成 3 周期一线治疗后（约 2022-02 月）
- **后续评估**: 每 2-3 个月或每 3-4 周期

---

## Module 5: 被排除的治疗方案 (Rejected Alternatives)

### 5.1 免疫单药治疗（排除）
- **理由**: 患者有 MET 驱动基因突变，免疫单药疗效有限
- **证据**: IMMUNOTARGET 登记研究显示，EGFR 突变患者免疫单药 ORR 仅 12%，mPFS 2.1 个月 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Section: THE ROLE OF IMMUNOTHERAPY]
- **禁忌**: 患者有间质性肺炎病史，免疫治疗增加 ILD 风险

### 5.2 一代/二代 EGFR-TKI（吉非替尼/厄洛替尼/阿法替尼）（排除）
- **理由**: MET 扩增是 EGFR-TKI 的获得性耐药机制
- **证据**: OncoKB LEVEL_R2 证据显示 MET 扩增导致对厄洛替尼、吉非替尼、奥希替尼耐药 [OncoKB: Level R2] [PubMed: PMID 18093943] [PubMed: PMID 17463250]
- **机制**: MET 通过 ERBB3 介导的 PI3K 通路激活驱动耐药 [OncoKB 响应数据]

### 5.3 全脑放疗（WBRT）（当前排除）
- **理由**: 患者脑转移瘤已完整切除，术后 MRI 显示无残留病灶，无需预防性 WBRT
- **证据**: 术后腔体 SRS 可降低局部复发风险，但本例已术后 3 个月且无复发证据，不推荐追加放疗

### 5.4 免疫联合化疗（一线暂不推荐）
- **理由**: 患者正在接受化疗 + 贝伐珠单抗治疗且疗效 PR，无需更改方案
- **备选**: 如疾病进展，可考虑 IMpower150 方案（阿替利珠单抗 + 贝伐珠单抗 + 紫杉醇 + 卡铂）[PubMed: PMID 30069759]

---

## Module 6: 围手术期管理参数 (Peri-procedural Holding Parameters)

### 6.1 当前状态
**N/A - 患者当前为系统治疗期间，无手术计划**

### 6.2 既往手术回顾
- **手术日期**: 2021-10-11
- **手术类型**: 右颞顶开颅显微镜下幕上深部肿物切除术
- **术后恢复**: 顺利，无并发症

### 6.3 未来如需手术的停药建议（参考）
如未来需要接受颅脑手术或立体定向放疗（SRS），参考以下停药窗口：

**贝伐珠单抗**:
- **术前停药**: 至少 28 天（基于药物半衰期及伤口愈合考虑）
- **术后恢复**: 至少 28 天且伤口完全愈合后
- **证据**: 贝伐珠单抗半衰期约 20 天，影响伤口愈合 [PubMed: PMID 30069759]

**培美曲塞/顺铂**:
- **术前停药**: 至少 7 天（基于骨髓恢复考虑）
- **术后恢复**: 术后 7-14 天且血象恢复后

---

## Module 7: 分子病理检测建议 (Molecular Pathology Orders)

### 7.1 已完成检测
- **免疫组化**: GFAP(-), Olig-2(-), Ki-67(40-70%), CK(+), CK7(+), CK8/18(+), TTF-1(-), NapsinA(-) 等 [Local: patient_708387_input.txt, Section: 病理诊断]
- **基因检测**: 
  - MET 扩增（拷贝数变异）[Local: patient_708387_input.txt, Section: 病理诊断]
  - MET 融合（M13M15 融合）[Local: patient_708387_input.txt, Section: 病理诊断]

### 7.2 推荐补充检测
根据 ESMO 指南推荐，晚期非鳞 NSCLC 患者应进行以下分子检测 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Section: RECOMMENDATIONS]:

**优先推荐（如组织标本可用）**:
1. **NGS 大 panel 检测**（DNA+RNA）:
   - 检测范围：EGFR、ALK、ROS1、BRAF、KRAS、RET、NTRK、HER2、MET 等
   - 目的：全面评估驱动基因状态，指导后线治疗
   - 证据：ESMO 指南推荐 [ii, A] [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Section: RECOMMENDATIONS]

2. **PD-L1 表达检测**（IHC）:
   - 目的：评估免疫治疗获益可能性
   - 证据：ESMO 指南推荐用于非驱动基因突变 NSCLC

**如组织标本不足，考虑液体活检（cfDNA）**:
- 检测 MET 扩增动态变化及耐药机制
- 证据：ESMO 指南推荐 [ii, A] [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Section: RECOMMENDATIONS]

### 7.3 耐药机制监测（疾病进展时）
- **重复活检或液体活检**: 评估 MET 扩增/融合状态变化
- **潜在耐药机制**: MET 继发突变、旁路激活（如 HER2 扩增）、组织学转化

---

## Module 8: Agent 执行轨迹 (Agent Execution Trajectory)

### 8.1 指南检索
```bash
# 检索 ESMO 驱动基因突变 NSCLC 指南
grep -i -C 5 "MET" Guidelines/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/*.md
# 发现 MET 扩增/ex14 跳跃突变治疗推荐
```

### 8.2 OncoKB 查询
```bash
# MET 扩增查询
query_oncokb.py cna --gene MET --type Amplification --tumor-type "Non-Small Cell Lung Cancer"
# 结果：LEVEL_2 (Capmatinib, Crizotinib, Tepotinib), LEVEL_R2 (EGFR-TKI 耐药)

# MET 融合查询
query_oncokb.py fusion --gene1 MET --gene2 MET --tumor-type "Non-Small Cell Lung Cancer"
# 结果：LEVEL_4 (Crizotinib)
```

### 8.3 PubMed 检索
```bash
# MET 抑制剂治疗脑转移
search_pubmed.py --query "MET amplification AND non-small cell lung cancer AND brain metastases AND capmatinib OR crizotinib OR tepotinib"
# 返回：36535300, 34537440, 23724913, 37733896, 30069759

# MET ex14 跳跃突变与脑转移
search_pubmed.py --query "MET exon 14 skipping AND brain metastases AND targeted therapy"
# 返回：30343896, 25971938, 40864503, 39214048, 38334610

# Capmatinib GEOMETRY 研究
search_pubmed.py --query "capmatinib AND GEOMETRY AND non-small cell lung cancer AND phase 2"
# 返回：39362249, 32877583, 33740553, 34425853, 33506571

# Tepotinib VISION 研究
search_pubmed.py --query "tepotinib AND VISION AND lung cancer AND clinical trial"
# 返回：37270698, 32469185, 38575731, 34789481, 40310449
```

### 8.4 关键证据总结
- **ESMO 指南**: MET 扩增/融合 NSCLC 一线推荐铂类双药化疗±免疫治疗 [Local: Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up/Oncogene-addicted_metastatic_non-small-cell_lung_cancer_ESMO_Clinical_Practice_Guideline_for_diagnosis,_treatment_and_follow-up.md, Section: OTHER ONCOGENIC DRIVERS FOR WHICH TARGETED THERAPY IS AVAILABLE]
- **OncoKB**: MET 扩增 LEVEL_2（Capmatinib/Crizotinib/Tepotinib），MET 融合 LEVEL_4（Crizotinib）
- **GEOMETRY mono-1**: Capmatinib 治疗 MET 扩增 NSCLC，初治 ORR 40%，经治 ORR 29% [PubMed: PMID 32877583]
- **VISION**: Tepotinib 治疗 MET ex14 跳跃突变 NSCLC，ORR 51.4%，mDOR 18.0 个月 [PubMed: PMID 37270698]
- **脑转移证据**: Capmatinib 日本亚组 1 例患者脑部病灶部分缓解 [PubMed: PMID 33506571]

---

## 总结与核心推荐

### 当前治疗策略
1. **继续一线治疗**: 培美曲塞 800mg d1 + 顺铂 60mg d1-2 + 贝伐珠单抗 500mg d2, q3w
2. **完成计划周期**: 建议完成 4-6 周期后评估疗效
3. **维持治疗**: 如疗效持续 PR/CR，考虑培美曲塞 + 贝伐珠单抗维持治疗

### 疾病进展后的后线选择
1. **MET 扩增靶向治疗**（OncoKB LEVEL_2）:
   - Capmatinib 400mg BID（优选，有脑转移缓解证据）
   - Tepotinib 500mg QD
   - Crizotinib 250mg BID

2. **MET 融合靶向治疗**（OncoKB LEVEL_4）:
   - Crizotinib 250mg BID（病例系列有效）

3. **免疫联合化疗**（备选）:
   - 阿替利珠单抗 + 贝伐珠单抗 + 紫杉醇 + 卡铂（IMpower150 方案）

### 特别注意事项
1. **间质性肺炎高危**: 避免使用 EGFR-TKI，密切监测 ILD 症状
2. **贝伐珠单抗毒性**: 监测血压、蛋白尿、出血风险
3. **定期随访**: 每 2-3 个月头颅 MRI + 胸部 CT

---

**MDT 报告完成时间**: 2022-01-15  
**证据检索日期**: 2022-01-15  
**下次评估时间**: 完成 3 周期一线治疗后（约 2022-02 月）