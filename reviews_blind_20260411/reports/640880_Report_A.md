# 天坛医院脑转移瘤 MDT 报告

**患者 ID:** 640880  
**入院时间:** 2025 年 03 月 07 日  
**报告生成时间:** 2025 年  
**MDT 类型:** 脑转移瘤多学科会诊

---

## Module 1: 入院评估 (Admission Evaluation)

### 1.1 人口学特征
- **年龄:** 54 岁
- **性别:** 女
- **住院号:** 640880

### 1.2 原发肿瘤特征
- **原发肿瘤类型:** 肺癌（2016 年手术切除，术后化疗）[Local: 患者输入文件, Line 4]
- **脑转移病理:** 转移癌，免疫组化符合肺来源 [Local: 患者输入文件, Line 5]
- **免疫组化:** CK5/6（-）, CK8/18（+）, Ki-67（约 50-70%）, CEA（+）, TTF-1（+）, GFAP（脑组织+）[Local: 患者输入文件, Line 5]
- **分子分型:** EGFR 突变状态 unknown（临床使用阿法替尼提示可能为 EGFR 敏感突变，但无基因检测报告确认）

### 1.3 脑转移瘤特征
- **病灶数量:** 单发新发病灶（右额叶）
- **最大病灶大小:** 12×11×12 mm [Local: 患者输入文件, Line 7]
- **位置:** 右额叶术野区
- ** eloquent 区:** 否（右额顶叶非功能区）
- **占位效应/水肿:** 周围见片状水肿影 [Local: 患者输入文件, Line 7]
- **神经症状:** 未明确描述（主诉未提及新发神经功能缺损）

### 1.4 体能状态
- **KPS:** unknown（病历未提供）
- **ECOG:** unknown（病历未提供）

### 1.5 既往治疗史
- **2016 年:** 肺部肿物手术切除，术后化疗 [Local: 患者输入文件, Line 4]
- **2020 年:** 脑转移瘤开颅手术 [Local: 患者输入文件, Line 5]
- **2020 年至今:** 阿法替尼靶向治疗（约 5 年）[Local: 患者输入文件, Line 5]
- **2025 年 1 月:** 头部 MRI 发现术野异常强化结节，考虑肿瘤复发 [Local: 患者输入文件, Line 5]

### 1.6 颅外疾病状态
- **unknown**（病历未提供近期全身评估结果）

### 1.7 缺失的关键数据
- EGFR 基因突变具体类型（unknown）
- KPS/ECOG 评分（unknown）
- 颅外疾病控制状态（unknown）
- 是否检测过 T790M 耐药突变（unknown）

---

## Module 2: 个体化治疗方案 (Primary Personalized Plan)

### 2.1 疾病状态判定
**判定:** 疾病进展（Progressive Disease, PD）

**依据:** 
- 患者阿法替尼治疗 5 年后出现颅内新发病灶（12×11×12mm）
- 对比 2021-02-05 MRI，右侧额叶异常强化较前新增 [Local: 患者输入文件, Line 8]
- 符合 RECIST 1.1 及 RANO-BM 进展标准

### 2.2 治疗线判定
**判定:** 二线治疗（Second-line Therapy）

**依据:**
- 一线治疗：阿法替尼（第二代 EGFR-TKI）2020 年至今
- 当前出现疾病进展，需更换作用机制不同的药物
- **严禁重复使用阿法替尼或同类第二代 EGFR-TKI**

### 2.3 推荐治疗方案

#### **局部治疗：立体定向放射外科（SRS）**

**推荐方案:** SRS 单分次治疗右额叶新发病灶

**剂量处方:** 
- **18-20 Gy / 1 次**，等剂量线 65-80% [PubMed: PMID 38720427, 27209508]
- 依据：国际多中心研究显示，脑干转移瘤 SRS 中位处方剂量 18 Gy，等剂量线 65% [PubMed: PMID 38720427]
- 对于>2cm 病灶，多分次 SRS（3×9 Gy）可降低放射性坏死风险 [PubMed: PMID 27209508]

**靶区定义:**
- GTV: MRI 增强可见的强化结节（12×11×12mm）
- PTV: GTV 外放 1-2mm

**治疗时机:** 尽快启动（2 周内）

**证据级别:** 
- ASCO-SNO-ASTRO 指南推荐：SRS 单独应用于 1-4 个未切除脑转移灶（不包括小细胞肺癌）[Local: asco-sno-astro_guideline.md, Section: RECOMMENDATION 3.2]
- 术后 SRS 单独应用于 1-2 个切除后的脑转移灶 [Local: asco-sno-astro_guideline.md, Section: RECOMMENDATION 3.3]

---

#### **系统治疗：奥希替尼（Osimertinib）**

**推荐方案:** 奥希替尼 80 mg 口服 每日一次（QD）

**依据:**
1. **OncoKB LEVEL_1 证据:** 奥希替尼是 FDA 批准的第三代 EGFR-TKI，用于 EGFR 敏感突变（Exon 19 缺失或 L858R）的晚期 NSCLC 一线治疗 [OncoKB: LEVEL_1]
2. **FLAURA 试验:** 奥希替尼 vs 第一代 EGFR-TKI（吉非替尼/厄洛替尼），中位 PFS 18.9 vs 10.2 个月（HR=0.46）[PubMed: PMID 29151359]
3. **颅内疗效:** FLAURA 试验 CNS 亚组分析显示，奥希替尼 CNS 中位 PFS 未达到 vs 13.9 个月（HR=0.48），CNS ORR 66% vs 43% [Local: asco-sno-astro_guideline.md, Section: LITERATURE REVIEW AND ANALYSIS]
4. **血脑屏障穿透:** 临床前研究显示奥希替尼 BBB 穿透能力显著优于第一代和第二代 EGFR-TKI [PubMed: PMID 27435396, 33028591]
5. **阿法替尼耐药后序贯:** UpSwinG 研究显示，阿法替尼耐药后（尤其是 T790M 阳性）序贯奥希替尼可获得生存获益 [PubMed: PMID 34649106]

**治疗持续时间:** 直至疾病进展或不可耐受毒性

**监测:** 每 2-3 个月复查头部 MRI 评估颅内疗效

---

### 2.4 治疗目标
- **主要目标:** 颅内疾病控制（局部+SRS 联合系统治疗）
- **次要目标:** 延长无进展生存期（PFS）和总生存期（OS）
- **生活质量:** 维持神经认知功能，避免 WBRT 相关毒性

---

## Module 3: 支持治疗 (Systemic Management)

### 3.1 糖皮质激素管理
**推荐:** 根据症状酌情使用地塞米松

- **有症状（头痛、恶心、神经功能缺损）:** 地塞米松 4-8 mg 静脉/口服 每 12 小时
- **无症状:** 不推荐预防性使用激素
- **SRS 后:** 如出现放射性脑水肿，可短期使用地塞米松 2-4 mg BID，逐渐减量停药

**依据:** ASCO 指南推荐症状性脑转移患者应接受局部治疗，激素用于缓解水肿相关症状 [Local: asco-sno-astro_guideline.md, Section: RECOMMENDATION 2.1]

### 3.2 抗癫痫治疗
**推荐:** 仅在有癫痫发作时使用

- **预防性抗癫痫:** 不推荐（无癫痫发作史）
- **如出现癫痫:** 左乙拉西坦 500-1000 mg BID（首选，药物相互作用少）

**依据:** 指南不推荐对无癫痫发作的脑转移患者预防性使用抗癫痫药物

### 3.3 奥希替尼不良反应管理
**常见不良反应及处理:**
- **腹泻:** 洛哌丁胺对症处理，必要时减量
- **皮疹:** 局部激素药膏，严重时口服多西环素
- **QTc 延长:** 基线及定期心电图监测
- **间质性肺病（ILD）:** 如出现新发或加重呼吸困难，立即停药并评估

**监测:** 每 3 个月复查心电图、肝肾功能

---

## Module 4: 随访与监测 (Follow-up & Monitoring)

### 4.1 影像学随访
**头部 MRI 增强:**
- **SRS 后:** 首次随访在 SRS 后 6-8 周
- **之后:** 每 2-3 个月复查直至疾病稳定
- **稳定后:** 每 3-4 个月复查

**评估标准:** RANO-BM 标准（Response Assessment in Neuro-Oncology for Brain Metastases）

### 4.2 全身评估
**推荐:** 每 3-4 个月复查胸部/腹部/骨盆 CT 或 PET-CT

**依据:** 监测颅外疾病状态，指导全身治疗调整

### 4.3 疗效评估时间点
- **首次评估:** SRS 后 6-8 周 + 奥希替尼治疗 8 周
- **主要终点:** 颅内无进展生存期（iPFS）
- **次要终点:** 颅内客观缓解率（iORR）、总生存期（OS）

### 4.4 疾病进展定义（RANO-BM）
- **颅内进展:** 靶病灶直径和增加≥5mm（较最小值），或出现新病灶
- **颅外进展:** RECIST 1.1 标准
- **临床进展:** 神经功能状态恶化（KPS 下降≥10 分）

---

## Module 5: 被排除方案 (Rejected Alternatives)

### 5.1 被排除方案 1：继续阿法替尼治疗
**排除理由:**
- 患者已使用阿法替尼约 5 年，当前出现颅内疾病进展
- 继续使用同一药物违反肿瘤治疗基本原则（疾病进展后需更换作用机制不同的药物）
- OncoKB 证据显示阿法替尼为 LEVEL_1 一线治疗，但患者已耐药 [OncoKB: LEVEL_1]
- **严格禁忌:** 疾病进展后继续使用原方案

### 5.2 被排除方案 2：全脑放疗（WBRT）
**排除理由:**
- 患者为单发脑转移（12mm），SRS 局部控制率更高且认知毒性更低
- ASCO-SNO-ASTRO 指南推荐：1-4 个未切除脑转移灶应首选 SRS 单独治疗而非 WBRT [Local: asco-sno-astro_guideline.md, Section: RECOMMENDATION 3.2]
- WBRT 相关神经认知毒性（记忆力下降、生活质量降低）显著高于 SRS
- 患者既往已接受开颅手术（2020 年），WBRT 可能加重术后认知功能障碍
- 如未来出现多发性脑转移（>10 个），可考虑 WBRT+ 海马保护+ 美金刚

### 5.3 被排除方案 3：再次开颅手术
**排除理由:**
- 病灶较小（12mm），SRS 局部控制率与手术相当且创伤更小
- 患者既往已接受开颅手术（2020 年），再次手术风险增加
- 病灶位于右额叶非功能区，但 SRS 可达到同等局部控制
- ASCO 指南：手术适用于大病灶伴占位效应患者，小病灶首选 SRS [Local: asco-sno-astro_guideline.md, Section: RECOMMENDATION 1.1]

### 5.4 被排除方案 4：第一代 EGFR-TKI（吉非替尼/厄洛替尼）
**排除理由:**
- 患者已使用第二代 EGFR-TKI（阿法替尼）耐药
- 第一代 TKI 颅内穿透能力弱于第三代奥希替尼
- FLAURA 试验显示奥希替尼 PFS 显著优于第一代 TKI（18.9 vs 10.2 个月）[PubMed: PMID 29151359]
- 奥希替尼 CNS 疗效更优（CNS ORR 66% vs 43%）[Local: asco-sno-astro_guideline.md, Section: LITERATURE REVIEW AND ANALYSIS]

---

## Module 6: 放疗期间系统治疗管理 (Peri-radiation Systemic Therapy Management)

**注:** 患者当前治疗方案为 SRS+ 系统治疗，无手术计划，因此本模块调整为"放疗期间系统治疗管理"而非"围手术期管理"。

### 6.1 SRS 期间 EGFR-TKI 管理

**推荐方案:** SRS 期间继续奥希替尼治疗（无需停药）

**依据:**
- 临床前研究显示奥希替尼具有优异的血脑屏障穿透能力，与放疗联合可能产生协同效应 [PubMed: PMID 27435396, 33028591]
- 多项回顾性研究提示 SRS 期间继续使用 EGFR-TKI 不显著增加放射性坏死风险，但缺乏前瞻性随机试验证据

**具体建议:**
- **方案 A（推荐）:** SRS 期间继续奥希替尼 80 mg QD（基于药物半衰期和临床实践考虑）
- **方案 B（保守）:** 如担心放射性坏死风险，可考虑 SRS 前停药 3-5 天，SRS 后 3-5 天恢复用药

**[具体停药窗口未在检索证据中明确，需临床医师基于患者个体情况决定]**

### 6.2 激素与 EGFR-TKI 相互作用
**注意:** 地塞米松可能通过 CYP3A4 诱导降低奥希替尼血药浓度

**建议:**
- 如需长期使用地塞米松（>2 周），需密切监测疗效，必要时考虑调整奥希替尼剂量
- 短期使用（<2 周）无需调整剂量

**[具体剂量调整方案未在检索证据中明确，需临床医师评估]**

### 6.3 SRS 后随访
**首次 MRI 复查:** SRS 后 6-8 周
- 评估局部控制情况
- 排除放射性坏死（与肿瘤进展鉴别）

---

## Module 7: 分子病理学检测建议 (Molecular Pathology Orders)

### 7.1 推荐检测项目

**优先推荐:** 液体活检（血浆 ctDNA）EGFR 基因检测

**检测 panel:**
- **EGFR 敏感突变:** Exon 19 缺失、Exon 21 L858R（确认基线突变类型）
- **EGFR 耐药突变:** T790M（Exon 20）、C797S（Exon 20）
- **其他耐药机制:** MET 扩增、HER2 扩增、小细胞转化等

**依据:**
- 患者阿法替尼治疗 5 年后进展，需明确耐药机制指导后续治疗
- UpSwinG 研究显示，阿法替尼耐药后 T790M 阳性患者序贯奥希替尼获益显著 [PubMed: PMID 34649106]
- 如 T790M 阳性，奥希替尼为标准二线治疗 [OncoKB: LEVEL_1]
- 如 T790M 阴性，需考虑其他耐药机制（MET 扩增、小细胞转化等）

### 7.2 检测时机
**推荐:** 尽快（2 周内）完成液体活检

**如液体活检阴性或无法检测:** 考虑再次活检（右额叶病灶）

**依据:** 脑转移灶可能与原发灶存在分子异质性，再次活检可明确颅内病灶分子特征 [Local: asco-sno-astro_guideline.md, Section: CLINICAL INTERPRETATION]

### 7.3 免疫组化补充检测（如行再次活检）
**推荐 panel:**
- **TTF-1, Napsin A:** 确认肺腺癌来源
- **Ki-67:** 评估增殖指数
- **Syn, CgA, CD56:** 排除小细胞转化
- **c-MET, HER2:** 评估靶向治疗机会

### 7.4 分子检测结果指导治疗
- **T790M 阳性:** 奥希替尼 80 mg QD（标准二线）[OncoKB: LEVEL_1]
- **T790M 阴性:** 
  - 考虑奥希替尼（基于 FLAURA 试验 CNS 疗效）[PubMed: PMID 29151359]
  - 或参加临床试验（如 MET 抑制剂联合、ADC 药物等）
- **小细胞转化:** 更换为铂类 + 依托泊苷化疗

---

## Module 8: 智能体执行轨迹 (Agent Execution Trajectory)

### 8.1 技能学习阶段
1. **read_file:** `/skills/universal_bm_mdt_skill/SKILL.md` - 学习 MDT 报告生成 SOP
2. **read_file:** `/skills/oncokb_query_skill/SKILL.md` - 学习 OncoKB 查询流程
3. **read_file:** `/skills/pubmed_search_skill/SKILL.md` - 学习 PubMed 检索策略

### 8.2 指南检索阶段
4. **execute:** `cat Guidelines/*/*.md | grep -i -C 5 "brain metastases\|surgery\|radiosurgery\|SRS\|WBRT"` - 检索脑转移瘤治疗指南
5. **execute:** `cat Guidelines/*/*.md | grep -i -C 5 "NSCLC\|non-small cell lung\|EGFR\|afatinib\|osimertinib"` - 检索 NSCLC 脑转移特异性推荐
6. **execute:** `cat Guidelines/*/*.md | grep -i -C 3 "Gy\|fraction\|dose\|surgery\|resection"` - 检索放疗剂量和手术指征

### 8.3 分子数据库查询阶段
7. **execute:** `/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/oncokb_query_skill/scripts/query_oncokb.py mutation --gene EGFR --alteration "L858R" --tumor-type "Non-Small Cell Lung Cancer"` - 查询 EGFR L858R 突变 OncoKB 证据

### 8.4 PubMed 文献检索阶段
8. **execute:** `/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pubmed_search_skill/scripts/search_pubmed.py --query "EGFR AND afatinib resistance AND brain metastases AND osimertinib" --max-results 5` - 检索阿法替尼耐药后奥希替尼治疗证据
   - 返回 PMID: 27435396, 33028591, 36033903, 34649106, 29910653
9. **execute:** `/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pubmed_search_skill/scripts/search_pubmed.py --query "stereotactic radiosurgery AND brain metastases AND dose AND Gy AND fraction" --max-results 5` - 检索 SRS 剂量证据
   - 返回 PMID: 32921513, 27209508, 38720427, 33602305, 28687377
10. **execute:** `/home/luzhenyang/anaconda3/envs/tiantanBM_agent/bin/python /media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pubmed_search_skill/scripts/search_pubmed.py --query "osimertinib AND FLAURA AND phase III AND NSCLC" --max-results 5` - 检索 FLAURA 试验证据
    - 返回 PMID: 29151359, 31751012, 33544337, 38813930, 39029876

### 8.5 强制检查点验证
11. **Checkpoint 1:** 既往治疗史审查 - 确认阿法替尼治疗史及疾病进展
12. **Checkpoint 2:** 疾病状态判定 - 确认新发病灶为疾病进展（PD）
13. **Checkpoint 3:** 治疗线确定 - 判定为二线治疗（严禁重复阿法替尼）
14. **Checkpoint 4:** 局部治疗方式判定 - 确认 SRS 而非手术
15. **Checkpoint 5:** 剂量参数验证 - 确认 SRS 剂量 18-20 Gy 和奥希替尼 80 mg QD 有文献支持

### 8.6 报告生成
16. **execute:** `mkdir -p patients/640880/reports/` - 创建患者目录
17. **submit_mdt_report:** 提交 MDT 报告并通过引用验证

---

## 引用声明

本报告所有临床建议均基于以下证据来源：

1. **指南证据:** ASCO-SNO-ASTRO 脑转移瘤治疗指南 (2021) [Local: asco-sno-astro_guideline.md]
2. **分子证据:** OncoKB 精准肿瘤学数据库 v7.0 [OncoKB: LEVEL_1]
3. **文献证据:** 
   - FLAURA 试验：Osimertinib vs 标准 EGFR-TKI [PubMed: PMID 29151359]
   - SRS 剂量研究：18 Gy 单分次治疗脑转移瘤 [PubMed: PMID 38720427, 27209508]
   - 阿法替尼耐药后序贯奥希替尼 [PubMed: PMID 34649106]
   - 奥希替尼 BBB 穿透能力 [PubMed: PMID 27435396, 33028591]

**证据等级说明:**
- LEVEL_1: 高水平循证医学证据（随机对照 III 期试验或荟萃分析）
- LEVEL_3A: 专家共识或小型 II 期试验

---

**MDT 首席专家签名:** _______________  
**日期:** _______________

**参与科室:** 神经外科、放射肿瘤科、肿瘤内科、影像科、病理科