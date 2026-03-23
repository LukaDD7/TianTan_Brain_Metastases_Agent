# MDT 报告标准输出范例 B (不确定性与多分支规划 Few-Shot)

**Agent 内部指令**：本示例演示了当患者存在“关键基因信息缺失”且伴有脑水肿时，应如何表达不确定性（Calibration）、如何制定多分支/分阶段（Phased/Branched）的治疗方案，以及如何在执行轨迹中体现“基于证据而非自我触发”的严密逻辑。

---

## 1. admission_evaluation (入院综合评估)

**结构化患者伪影 (Structured Patient Artifacts)**：
- **基本信息**：男，62 岁
- **原发肿瘤**：肺腺癌 (初治)
- **分子病理**：**【关键数据缺失】** EGFR、ALK、ROS1 等核心驱动基因检测结果尚未回报。
- **转移灶特征**：多发脑转移（>10 个病灶）。最大病灶位于左侧顶叶，大小约 2.1×1.8 cm，伴中度瘤周水肿；余病灶散在分布于双侧大脑半球，无脑干及小脑受累。
- **临床体征**：KPS 评分 80，偶发轻度头痛及右侧肢体轻度乏力。
- **器官功能**：基线血常规及肝肾功能正常。

## 2. primary_plan (首选个性化治疗方案规划)

**不确定性声明 (Calibration Statement)**：
鉴于当前核心驱动基因（EGFR/ALK/ROS1等）结果未知，根据 NCCN 循证医学指南，当前**绝对禁忌**盲目启动经验性靶向治疗或全身化疗。首选方案需拆分为对症控制期（Phase 1）与靶向/全身决策期（Phase 2）。

**2.1 Phase 1：急性期对症与局部控制 (Immediate Management)**
- **脑水肿控制**：鉴于患者存在中度瘤周水肿及轻微局灶性神经症状，立即启动糖皮质激素治疗。
  - **方案**：地塞米松 4 mg PO/IV BID（每日两次）[Local: NCCN_CNS_v1.2024.pdf, Page 22]。
- **局部放射治疗评估**：因脑转移灶 >10 个，且为非小细胞肺癌（NSCLC），暂不具备立体定向放射外科 (SRS) 优先指征。是否进行全脑放疗 (WBRT) 需视 Phase 2 的基因结果决定。

**2.2 Phase 2：基因结果驱动的多分支规划 (Branched Systemic Strategy)**
待 NGS 基因检测结果回报后，依据以下决策树执行：

- **Branch A（若检出 EGFR 敏感突变，如 Exon 19 del 或 L858R）**：
  - **全身治疗**：首选第三代 EGFR-TKI 越过血脑屏障控制颅内外病灶。
  - **方案**：Osimertinib (奥希替尼) 80 mg PO QD [Online: BioMCP_FDA_Label, Osimertinib]。
  - **局部治疗降级**：因 Osimertinib 颅内控制率极高，对于无紧急生命危险的多发脑转移，可暂缓 WBRT，密切进行 MRI 监测 [Local: NCCN_NSCLC_v3.2024.pdf, Page 158]。

- **Branch B（若检出 ALK 融合阳性）**：
  - **全身治疗**：首选新一代高透脑率 ALK-TKI。
  - **方案**：Alectinib (阿来替尼) 600 mg PO BID 或 Lorlatinib (劳拉替尼) 100 mg PO QD [Local: NCCN_NSCLC_v3.2024.pdf, Page 162]。

- **Branch C（若所有高频驱动基因均阴性，即野生型）**：
  - **局部治疗**：鉴于单纯化疗/免疫治疗的颅内缓解率相对靶向药较低，建议尽快启动海马回避全脑放疗 (HA-WBRT) 联合美金刚以控制颅内病灶 [Local: NCCN_CNS_v1.2024.pdf, Page 64]。
  - **全身治疗**：结合 PD-L1 表达水平，启动含铂双药化疗联合免疫检查点抑制剂 (如 Pembrolizumab) 的系统性治疗。

## 3. systemic_management (支持性治疗与毒性管理)

- **应激性溃疡预防**：在使用地塞米松期间，常规联用质子泵抑制剂（如奥美拉唑 20mg PO QD）。
- **癫痫预防**：患者当前无癫痫发作史，指南不推荐预防性使用抗癫痫药物 (AEDs) [Local: ASCO_Brain_Mets_2022.pdf, Page 12]。

## 4. follow_up (随访监控)

- 启动 Phase 2 靶向治疗或放疗后，前 3 个月内每 6-8 周进行一次高分辨头部强化 MRI 复查，此后病情稳定可延长至每 12 周一次。

## 5. rejected_alternatives (备选方案与排他性方案的深度辩证)

1. **排除立即进行全脑放疗 (WBRT) 而不等待基因结果**：
   - **排他理由**：虽然患者为多发脑转移，但目前神经症状轻微且可通过激素控制。若患者存在 EGFR/ALK 突变，前期临床试验显示单用第三代 TKI 即可获得优异的颅内缓解，从而使患者免受或推迟 WBRT 带来的严重神经认知毒性 [Local: NCCN_CNS_v1.2024.pdf, Page 24]。因此，等待靶点明确是符合生存质量最大化原则的。
2. **排除经验性化疗**：
   - **排他理由**：单纯化疗药物穿透血脑屏障的效率极低，对多发脑转移的控制力弱。在驱动基因明确前使用化疗，不仅可能延误高效靶向治疗，还可能因化疗毒性导致患者后续无法耐受最佳治疗。

## 6. peri_procedural_holding_parameters (围手术期处理)

- 不适用。当前无有创性外科手术规划。

## 7. molecular_pathology_orders (分子病理送检医嘱)

- **紧急督导**：病理科/分子诊断中心加急处理 NGS 骨干 Panel（必须覆盖 EGFR, ALK, ROS1, BRAF, MET, RET, NTRK），以及 PD-L1 IHC (22C3) 检测。确保周转时间 (TAT) 控制在 7-10 个工作日内。

## 8. agent_execution_trajectory (智能体执行轨迹)

- `[Action]` 提取患者特征：多发脑转移(>10)，肺腺癌，**驱动基因缺失**。
- `[Tool: PDF Parser]` 检索本地 `NCCN_NSCLC_v3.2024.pdf` 中关于初治肺腺癌脑转移且基因状态未知的流程图。
- `[Reasoning]` 获取指南证据：NCCN 明确建议在症状可控前提下，等待基因测序结果以决定是否使用 TKI，避免盲目全脑放疗。**未自我触发经验性开药指令。**
- `[Action]` 根据证据生成多分支规划：启动地塞米松控制水肿（Phase 1），并基于可能回报的基因结果分化为 Branch A/B/C（Phase 2）。
- `[Tool: BioMCP]` 查询 Osimertinib 与 Alectinib 的 FDA 标准给药剂量，填补至对应分支。
- `[Reasoning]` 交叉校验完成：确认无不恰当的超前用药；组装带有不确定性校准声明的报告。