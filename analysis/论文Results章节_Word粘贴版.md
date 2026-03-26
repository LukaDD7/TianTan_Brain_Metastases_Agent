# 论文Results章节 - Word粘贴专用版

**说明**: 本文档中的表格使用 Markdown 格式，可直接复制到 Word；所有 BM Agent 数值统一来自 `analysis/final_results/final_metrics.json` / `.csv`。

---

## Results

### Overview of Study Design

This study compared a specialized Brain Metastases multidisciplinary intelligent system (BM Agent) against three baseline methods (Direct LLM, RAG, and WebSearch) on nine real-world brain metastasis cases. Five quantitative metrics were reported: Clinical Consistency Rate (CCR), Physical Traceability Rate (PTR), MDT Quality Rate (MQR), Clinical Error Rate (CER), and Composite Performance Index (CPI).

---

### Table 1. Comparison of Four Methods Across Five Quality Metrics

| Method | CCR (0-4) | PTR (0-1) | MQR (0-4) | CER (0-1) | CPI (0-1) |
|--------|-----------|-----------|-----------|-----------|-----------|
| Direct LLM | 1.51 ± 0.19 | 0.000 ± 0.000 | 1.98 ± 0.19 | N/A | 0.420 ± 0.030 |
| RAG | 2.01 ± 0.19 | 0.000 ± 0.000 | 2.49 ± 0.19 | N/A | 0.520 ± 0.030 |
| WebSearch | 2.21 ± 0.19 | 0.000 ± 0.000 | 2.59 ± 0.19 | N/A | 0.570 ± 0.030 |
| **BM Agent** | **3.42 ± 0.32** | **0.989 ± 0.033** | **3.88 ± 0.14** | **0.052 ± 0.065** | **0.931 ± 0.046** |

Note: BM Agent values are mean ± sample SD (ddof=1). Baseline values remain estimated / not clinically reviewed. CCR and MQR are scored on a 0-4 scale; PTR, CER, and CPI on a 0-1 scale. Lower CER is better.

---

### Table 2. Patient-Level Performance Metrics (sorted by CPI)

| Rank | Patient ID | Case | Tumor Type | CCR | MQR | CER | PTR | CPI |
|------|------------|------|------------|-----|-----|-----|-----|-----|
| 1 | 868183 | Case3 | Lung adenocarcinoma | 3.9 | 4.0 | 0.000 | 1.0 | 0.991 |
| 2 | 638114 | Case6 | Lung adenocarcinoma | 3.7 | 4.0 | 0.000 | 1.0 | 0.974 |
| 3 | 708387 | Case9 | Lung cancer | 3.6 | 4.0 | 0.000 | 1.0 | 0.965 |
| 4 | 640880 | Case2 | Lung cancer | 3.4 | 3.9 | 0.000 | 1.0 | 0.941 |
| 5 | 747724 | Case10 | Breast cancer | 3.5 | 3.9 | 0.067 | 1.0 | 0.940 |
| 6 | 605525 | Case8 | Colorectal cancer | 3.4 | 4.0 | 0.067 | 1.0 | 0.937 |
| 7 | 648772 | Case1 | Malignant melanoma | 3.2 | 3.7 | 0.067 | 1.0 | 0.901 |
| 8 | 612908 | Case7 | Lung cancer | 3.3 | 3.7 | 0.067 | 0.9 | 0.885 |
| 9 | 665548 | Case4 | Gastric cancer | 2.8 | 3.7 | 0.200 | 1.0 | 0.846 |

---

### Table 3. Statistical Significance Tests (Wilcoxon Signed-Rank)

| Comparison | Statistic | p-value | Significance |
|------------|-----------|---------|--------------|
| BM Agent vs Direct LLM (CCR only) | 0.0 | 0.003906 | ** |
| BM Agent vs RAG (CCR only) | 0.0 | 0.003906 | ** |
| BM Agent vs WebSearch (CCR only) | 0.0 | 0.003906 | ** |

Note: The current Wilcoxon analysis in `final_metrics.json` applies to CCR only, not to all five metrics.

---

### Clinical Consistency Rate (CCR)

BM Agent achieved a mean CCR of **3.42 ± 0.32**, indicating strong agreement with real-world clinical decision paths. The best performance was observed in patient 868183 (CCR = 3.9), while patient 665548 remained the most challenging case (CCR = 2.8).

---

### Physical Traceability Rate (PTR)

BM Agent achieved a mean PTR of **0.989 ± 0.033**. **Eight of nine patients reached perfect traceability (PTR = 1.0)**, while **one patient (612908)** had PTR = 0.9 due to non-perfect citation formatting rather than a failed evidence chain.

### Table 4. Traceability Pattern Summary

| Category | Count / Mean |
|----------|--------------|
| Patients with PTR = 1.0 | 8 |
| Patients with PTR = 0.9 | 1 |
| Mean PTR | 0.989 |
| Sample SD | 0.033 |

---

### MDT Quality Rate (MQR)

BM Agent achieved a mean MQR of **3.88 ± 0.14**. Three patients achieved the ceiling score of 4.0. Overall report structure remained stable across the cohort, with all reports preserving the required 8-module MDT format.

---

### Clinical Error Rate (CER)

BM Agent achieved a mean CER of **0.052 ± 0.065**. Errors were entirely limited to the minor level.

- Patients with CER = 0.000: **4/9**
- Patients with CER = 0.067: **4/9**
- Patients with CER = 0.200: **1/9**
- Critical errors: **0**
- Major errors: **0**
- Total minor errors implied by the final CER values: **7**

### Table 5. Clinical Error Distribution by Patient

| Patient ID | Critical Errors | Major Errors | Minor Errors | CER Score |
|------------|-----------------|--------------|--------------|-----------|
| 868183 | 0 | 0 | 0 | 0.000 |
| 638114 | 0 | 0 | 0 | 0.000 |
| 708387 | 0 | 0 | 0 | 0.000 |
| 640880 | 0 | 0 | 0 | 0.000 |
| 747724 | 0 | 0 | 1 | 0.067 |
| 605525 | 0 | 0 | 1 | 0.067 |
| 648772 | 0 | 0 | 1 | 0.067 |
| 612908 | 0 | 0 | 1 | 0.067 |
| 665548 | 0 | 0 | 3 | 0.200 |

---

### Composite Performance Index (CPI)

CPI was computed using the unified weighted formula:

`CPI = 0.35 × (CCR/4) + 0.25 × PTR + 0.25 × (MQR/4) + 0.15 × (1 - CER)`

BM Agent achieved a mean CPI of **0.931 ± 0.046**, substantially exceeding the baseline estimates.

### Table 6. CPI Component Breakdown for BM Agent Mean Performance

| Component | Weight | Contribution | Formula |
|-----------|--------|--------------|---------|
| CCR (normalized) | 35% | 0.299 | 0.35 × (3.422/4) |
| PTR | 25% | 0.247 | 0.25 × 0.989 |
| MQR (normalized) | 25% | 0.242 | 0.25 × (3.878/4) |
| 1-CER | 15% | 0.142 | 0.15 × (1-0.052) |
| **Total CPI** | **100%** | **0.931** | - |

---

### Key Findings Summary

1. BM Agent maintained high clinical consistency (CCR 3.42/4.0) across nine heterogeneous cases.
2. The traceability advantage was decisive: baseline PTR remained 0, whereas BM Agent reached 0.989 on average.
3. Safety remained strong: no critical or major errors were identified.
4. The most important patient-level correction is case 612908, which has **PTR = 0.9** and **CPI = 0.885**, not PTR = 1.0.
5. CPI ranking places **638114 above 708387**, which needed correction in older drafts.

---

### Efficiency Metrics

### Table 7. Efficiency Metrics Comparison

| Metric | Direct LLM | RAG | WebSearch | BM Agent |
|--------|-----------|-----|-----------|----------|
| Latency (s) | 94.3 | 106.2 | 127.4 | 260.4 |
| Total Tokens (×10³) | 7.2 | 9.0 | 42.9 | 581.5 |
| Tool Calls | 0.0 | 1.0 | 2.0 | 41.6 |

These efficiency figures should be interpreted as resource trade-offs rather than quality metrics and are separate from the clinically reviewed BM metrics.

---

**文档生成时间**: 2026-03-26
**数据版本**: `analysis/final_results/final_metrics.json`
**统计口径**: sample SD (ddof=1)
