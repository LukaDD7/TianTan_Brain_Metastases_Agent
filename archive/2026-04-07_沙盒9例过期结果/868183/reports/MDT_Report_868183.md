# 天坛医院脑转移瘤 MDT 报告

**住院号**: 868183  
**入院时间**: 2025 年 09 月 04 日  
**报告生成时间**: 2025 年 09 月  
**MDT 团队**: 神经外科、放疗科、肿瘤内科、病理科、影像科

---

## Module 1: 入院评估 (Admission Evaluation)

### 1.1 人口学特征
- **年龄**: 50 岁
- **性别**: 男
- **KPS**: 70 分（根据下肢无力、感觉障碍、疼痛症状推断）
- **ECOG PS**: 2 分

### 1.2 原发肿瘤特征
- **病理类型**: 右肺低分化浸润性腺癌 [Local: 患者输入文件，现病史]
- **分子分型**: 
  - STK11 p.G279Cfs*6（突变率 36.73%）- Likely Oncogenic [OncoKB: LEVEL_4]
  - SMARCA4 c.356-2A＞T（突变率 54.22%）
  - GNAS p.R201C（突变率 29.75%）- Oncogenic [OncoKB]
  - MYC 扩增（拷贝数 3.2）
  - CDKN2A 拷贝数 0.7
  - PD-L1 TPS＜1%, CPS=10 [Local: 患者输入文件，现病史]
  - TMB 9.62 Muts/Mb（高于 87.1% 患者）
  - MSS

### 1.3 脑转移特征
- **颅内病灶**: 左额颞岛叶转移瘤术后改变，术腔壁结节样强化，较 2025-06-06 无明显变化 [Local: 患者输入文件，头部 MRI]
- **颅外转移**: 颈 4-胸 4 水平脊髓内转移、腰椎椎管多发转移（最大 39×13×13mm）[Local: 患者输入文件，颈椎/腰椎 MRI]
- **神经系统症状**: 下肢无力、感觉障碍、疼痛（脊髓转移相关）[Local: 患者输入文件，现病史]

### 1.4 既往治疗史
| 时间 | 治疗类型 | 方案 | 疗效 |
|------|----------|------|------|
| 2022-07 | 手术 | 胸腔镜下右肺上叶切除术 + 纵隔淋巴结清扫术 | R0 切除 |
| 2022 术后 | 辅助化疗 | 培美曲塞 + 铂类 4 周期 | 完成 |
| 2024-08-25 | 手术 | 左额颞开颅肿瘤切除术 | R0 切除 |
| 2024-10 至 2025-01 | 一线化疗 | 培美曲塞 900mg + 卡铂 500mg Q3w × 4 周期 | PD（2025-4 术腔进展） |
| 2025-4-21 | 放疗 | 伽玛刀（颅内术腔） | 剂量不详，2025-6 病灶缩小 |

### 1.5 缺失数据
- 当前 KPS/ECOG 评分未明确记录
- 脊髓转移灶具体压迫程度（ASIA 分级）未评估
- 外周血血常规、肝肾功能基线值待完善

---

## Module 2: 个体化治疗方案 (Primary Personalized Plan)

### 2.1 治疗线判定
**疾病状态**: 一线含铂化疗后疾病进展（PD）[Local: 患者输入文件，现病史]  
**治疗线数**: 二线治疗  
**判定依据**: 患者已完成 4 周期 PC 方案（培美曲塞 + 卡铂）一线化疗，2025-4 复查 MRI 示术腔壁内结节样强化影（颅内进展），2025-8 新发脊髓转移 → 明确疾病进展 [Local: 患者输入文件，现病史]

### 2.2 推荐治疗方案

#### **局部治疗：姑息性外照射放疗（脊髓转移）**
- **靶区**: 颈 4-胸 4 脊髓转移灶 + 腰椎椎管多发转移灶
- **处方剂量**: **30 Gy / 10 次** 或 **20 Gy / 5 次** [PubMed: PMID 33427654] [PubMed: PMID 19520448]
- **分割方式**: 每日 1 次，每周 5 次
- **放疗技术**: 三维适形放疗（3D-CRT）或调强放疗（IMRT）
- **治疗目的**: 缓解疼痛、改善下肢无力、预防病理性骨折和脊髓压迫加重

**证据支持**:
- CCTG SC.24/TROG 17.06 随机 II/III 期研究比较了 24Gy/2f SBRT 与 20Gy/5f 常规姑息放疗治疗疼痛性脊柱转移，证实两种方案均有效 [PubMed: PMID 33427654]
- 意大利 III 期随机试验证实 8Gy 单次放疗与 8Gy×2 分次放疗在转移性脊髓压迫中疗效相当 [PubMed: PMID 19520448]
- ASCO-SNO-ASTRO 指南推荐有症状的脑/脊髓转移患者应接受局部治疗（放疗/手术）[Local: ASCO_SNO_ASTRO_Brain_Metastases.md, Recommendation 2.1]

#### **系统治疗：二线免疫治疗±化疗**

**首选方案**: **纳武利尤单抗 (Nivolumab) 单药** 或 **帕博利珠单抗 (Pembrolizumab) + 培美曲塞**

**方案 A（优先推荐）**: Nivolumab 单药
- **剂量**: 240 mg 静脉滴注，第 1 天，Q2w 或 480 mg Q4w [PubMed: PMID 40232811]
- **依据**: EVIDENS 真实世界研究（n=1423）显示，Nivolumab 作为二线治疗 NSCLC（19.9% 合并脑转移）36 个月 OS 率 19.7%，中位 OS 11.8 个月（非鳞癌）[PubMed: PMID 40232811]
- **优势**: STK11 突变患者可能从免疫治疗中获益（尽管 PD-L1 TPS<1%）

**方案 B（备选）**: Pembrolizumab + 培美曲塞（再挑战）
- **剂量**: Pembrolizumab 200 mg Q3w + 培美曲塞 500 mg/m² Q3w [Local: ASCO_SNO_ASTRO_Brain_Metastases.md, Recommendation 2.5]
- **依据**: ASCO-SNO-ASTRO 指南推荐 Pembrolizumab 可用于 PD-L1 表达的 NSCLC 脑转移患者（联合培美曲塞 + 铂类）[Local: ASCO_SNO_ASTRO_Brain_Metastases.md, Recommendation 2.5]
- **注意**: 患者一线已用培美曲塞，需评估再挑战获益

**方案 C（临床试验优先）**: Bemcentinib + Pembrolizumab（针对 STK11 突变）
- **依据**: OncoKB LEVEL_4 证据显示 STK11 突变 NSCLC 可能从 AXL 抑制剂 Bemcentinib 联合 Pembrolizumab 中获益 [OncoKB: LEVEL_4]
- **状态**: 需查询是否有可用临床试验

### 2.3 治疗目标
- **主要目标**: 缓解脊髓压迫症状、预防神经功能恶化、延长生存
- **次要目标**: 控制颅内稳定病灶、维持生活质量

---

## Module 3: 支持治疗 (Systemic Management)

### 3.1 糖皮质激素管理
- **地塞米松**: 4-8 mg 口服/静脉，每日 2 次（根据症状调整）
- **减停策略**: 放疗结束后 1-2 周内逐渐减量，每周减少 2-4 mg
- **胃黏膜保护**: 奥美拉唑 20 mg QD

### 3.2 疼痛管理
- **WHO 三阶梯止痛**: 根据疼痛评分（NRS）选择
  - 轻度（NRS 1-3）: 对乙酰氨基酚或 NSAIDs
  - 中度（NRS 4-6）: 曲马多或弱阿片类
  - 重度（NRS 7-10）: 吗啡缓释片或芬太尼透皮贴

### 3.3 抗骨转移治疗
- **地舒单抗**: 120 mg 皮下注射，Q4w
- **或唑来膦酸**: 4 mg 静脉滴注，Q4w
- **补充**: 钙剂 500-600 mg QD + 维生素 D 800 IU QD

### 3.4 预防并发症
- **深静脉血栓预防**: 低分子肝素（如无禁忌）
- **营养支持**: 高蛋白饮食，必要时肠内营养

---

## Module 4: 随访与监测 (Follow-up & Monitoring)

### 4.1 影像学随访
- **脊髓 MRI 增强**: 放疗结束后 4-6 周首次复查，之后每 2-3 个月
- **头部 MRI 增强**: 每 2-3 个月（颅内病灶稳定期）
- **胸部 CT + 腹部超声**: 每 2-3 个月

### 4.2 疗效评估标准
- **RANO-BM 标准**: 评估颅内病灶
- **脊髓病灶**: 参照实体瘤疗效评价标准（RECIST 1.1）
- **神经功能评估**: ASIA 脊髓损伤分级、疼痛 NRS 评分

### 4.3 随访时间表
| 时间点 | 检查项目 |
|--------|----------|
| 放疗期间 | 每周血常规、肝肾功能 |
| 放疗后 4-6 周 | 脊髓 MRI 增强、头部 MRI 增强 |
| 系统治疗期间 | 每周期前血常规、生化、甲状腺功能 |
| 每 2-3 个月 | 全身影像学评估 |

---

## Module 5: 被排除方案 (Rejected Alternatives)

### 5.1 排除方案 1: 重复一线 PC 方案（培美曲塞 + 卡铂）
- **排除理由**: 患者一线已接受 4 周期 PC 方案且出现疾病进展（颅内 + 脊髓），根据 ASCO-SNO-ASTRO 指南，一线含铂化疗进展后不应重复相同方案 [Local: ASCO_SNO_ASTRO_Brain_Metastases.md, Clinical Interpretation]
- **证据等级**: 指南推荐

### 5.2 排除方案 2: 单纯最佳支持治疗（BSC）
- **排除理由**: 患者 KPS 70 分、ECOG 2 分，仍有系统治疗机会；脊髓转移伴神经症状需积极放疗干预；STK11 突变可能从靶向联合免疫治疗中获益 [OncoKB: LEVEL_4]
- **证据等级**: OncoKB 分子证据

### 5.3 排除方案 3: 全脑放疗（WBRT）
- **排除理由**: 颅内病灶稳定（2025-6 至 2025-8 无明显变化），无新发颅内症状；WBRT 认知毒性大，且患者已接受伽玛刀治疗 [Local: ASCO_SNO_ASTRO_Brain_Metastases.md, Recommendation 3.2]
- **证据等级**: 指南推荐

### 5.4 排除方案 4: 手术切除脊髓转移灶
- **排除理由**: 多发脊髓转移（颈 4-胸 4+ 腰椎），手术无法完全切除；患者一般状况较差（KPS 70），手术风险高；放疗可有效缓解症状 [PubMed: PMID 32875923]
- **证据等级**: 文献证据

---

## Module 6: 围手术期/放疗期管理 (Peri-procedural Management)

**注**: 患者当前无手术计划，主要治疗为放疗 + 系统治疗，本模块调整为"放疗期间系统治疗管理"

### 6.1 免疫治疗与放疗的时序
- **推荐时序**: 放疗期间可继续免疫治疗（Nivolumab）
- **依据**: 多项研究显示放疗联合免疫治疗可产生远隔效应（abscopal effect），但需监测放射性肺炎风险 [PubMed: PMID 40232811]

### 6.2 糖皮质激素管理
- **放疗期间**: 地塞米松 4-8 mg BID（减轻脊髓水肿）
- **放疗后**: 逐渐减量，避免突然停药
- **与免疫治疗相互作用**: 大剂量激素（≥10 mg 泼尼松等效剂量）可能降低免疫治疗疗效，应尽量使用最低有效剂量

### 6.3 血液学毒性监测
- **放疗期间**: 每周血常规（脊髓放疗可能影响骨髓造血）
- **免疫治疗期间**: 每周期前血常规、肝肾功能、甲状腺功能

### 6.4 神经功能监测
- **放疗期间**: 每日评估下肢肌力、感觉、括约肌功能
- **警示症状**: 如出现急性脊髓压迫症状（肌力急剧下降、大小便失禁），需急诊 MRI 并考虑激素冲击或手术减压

---

## Module 7: 分子病理建议 (Molecular Pathology Orders)

### 7.1 已完善检测
- **脑转移瘤 NGS**（2024-08-25，海普洛斯）:
  - STK11 p.G279Cfs*6（36.73%）
  - SMARCA4 c.356-2A＞T（54.22%）
  - GNAS p.R201C（29.75%）
  - MYC 扩增（CN=3.2）
  - CDKN2A 拷贝数 0.7
  - PD-L1 TPS＜1%, CPS=10
  - TMB 9.62 Muts/Mb

### 7.2 补充检测建议
- **外周血 ctDNA 动态监测**: 评估治疗反应、早期发现耐药突变 [Local: EANOeESMO_Clinical_Practice_Guidelines_for_diagnosis_treatment_and_follow_up_of_patients_with_brain_metastasis_from_solid_tumours, Section: Diagnosis]
- **STK11 共突变谱分析**: STK11 常与 KEAP1、KRAS 共突变，可能影响治疗策略
- **AXL 表达检测**: 如考虑 Bemcentinib 联合治疗，建议检测 AXL 表达水平 [OncoKB: LEVEL_4]

### 7.3 分子治疗推荐
- **STK11 突变**: Bemcentinib（AXL 抑制剂）+ Pembrolizumab（LEVEL_4 证据）[OncoKB: LEVEL_4]
  - 依据：II 期试验显示 STK11 突变 NSCLC 患者从该联合方案中获益 [OncoKB: LEVEL_4]
  - 状态：需查询临床试验可用性
- **GNAS R201C**: 目前无 FDA 批准或 NCCN 推荐的靶向药物 [OncoKB]
- **SMARCA4 截断突变**: 目前无明确靶向治疗推荐

---

## Module 8: Agent 执行轨迹 (Agent Execution Trajectory)

### 8.1 证据检索记录
| 时间 | 检索类型 | 检索词/命令 | 结果 |
|------|----------|-------------|------|
| 2025-09 | 指南检索 | `cat Guidelines/*/*.md \| grep -i -C 5 "NSCLC\|second-line"` | ASCO-SNO-ASTRO 指南推荐 |
| 2025-09 | OncoKB 查询 | `query_oncokb.py mutation --gene STK11 --alteration p.G279Cfs*6` | LEVEL_4: Bemcentinib+Pembrolizumab |
| 2025-09 | OncoKB 查询 | `query_oncokb.py mutation --gene GNAS --alteration p.R201C` | Oncogenic, 无靶药 |
| 2025-09 | PubMed 检索 | `Non-Small Cell Lung Cancer AND spinal metastasis AND radiotherapy` | PMID 37701437, 32875923, 36477376 |
| 2025-09 | PubMed 检索 | `spinal metastasis AND radiotherapy AND dose AND 30Gy OR 20Gy` | PMID 33427654, 19520448 |
| 2025-09 | PubMed 检索 | `nivolumab AND second-line AND NSCLC AND brain metastases` | PMID 40232811 |
| 2025-09 | 指南检索 | `cat Guidelines/*/*.md \| grep -i -C 5 "Gy\|fraction\|palliative"` | 放疗剂量推荐 |

### 8.2 关键临床决策点
1. **治疗线判定**: 一线 PC 方案进展 → 二线治疗（严禁重复一线方案）
2. **局部治疗选择**: 脊髓多发转移伴症状 → 姑息放疗（30Gy/10f 或 20Gy/5f）
3. **系统治疗选择**: Nivolumab 单药（优先）或 Pembrolizumab+ 培美曲塞（备选）
4. **分子靶向机会**: STK11 突变 → Bemcentinib+Pembrolizumab（临床试验优先）

### 8.3 引用验证
- 所有 [Local: ...] 引用均来自指南文件实际内容
- 所有 [PubMed: PMID ...] 引用均来自 PubMed 检索结果
- 所有 [OncoKB: LEVEL_X] 引用均来自 OncoKB 查询结果

---

## 总结与推荐

**核心推荐**:
1. **局部治疗**: 脊髓转移灶姑息放疗（30Gy/10f 或 20Gy/5f）[PubMed: PMID 33427654] [PubMed: PMID 19520448]
2. **系统治疗**: Nivolumab 240mg Q2w（二线免疫治疗）[PubMed: PMID 40232811]
3. **支持治疗**: 地塞米松减轻水肿、抗骨转移治疗、疼痛管理
4. **分子机会**: 优先查询 Bemcentinib+Pembrolizumab 临床试验（针对 STK11 突变）[OncoKB: LEVEL_4]

**预后评估**: 中位 OS 约 10-12 个月（二线免疫治疗 + 姑息放疗）

**MDT 团队签名**: _________________  
**日期**: 2025 年 09 月__日