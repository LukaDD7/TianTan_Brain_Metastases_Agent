
# 图表说明摘要

## Figure 1: 五维度雷达图 (Figure1_radar_chart)
- 展示四种方法在CCR、PTR、MQR、1-CER、CPI五个维度的表现
- BM Agent在所有维度均表现最优
- Baseline方法在PTR维度为0

## Figure 2: CPI对比柱状图 (Figure2_cpi_comparison)
- BM Agent CPI: 0.888 ± 0.045 (最高)
- Enhanced RAG CPI: 0.802 ± 0.037
- Direct LLM CPI: 0.520 ± 0.030
- WebSearch LLM CPI: 0.570 ± 0.030
- 添加误差线显示标准差

## Figure 3: 效率指标对比 (Figure3_efficiency_comparison)
- 三个子图: 延迟(秒)、Token消耗(K)、工具调用
- BM Agent延迟最长(263.7s)且Token消耗最高(581.5K)
- BM Agent工具调用次数显著高于其他方法

## Figure 4: CER对比图 (Figure4_cer_comparison)
- 水平条形图展示CER
- BM Agent CER: 0.052 (最低)
- Baseline方法CER: 0.600-0.667 (高风险)
- 添加安全阈值线(0.200)和高风险线(0.600)

## Figure 5: 成本效益散点图 (Figure5_cost_effectiveness)
- X轴: 成本(USD) - 更新后BM Agent $1.83
- Y轴: CPI
- 标注理想区域(绿色)和不可接受区域(红色)
- BM Agent位于高成本高效率区域

## Figure 6: BM Agent个体患者CPI分布 (Figure6_individual_patients)
- 9例患者的CPI分布
- 均值0.888 ± 0.045，中位数0.900
- 所有患者CPI均>0.780

## Figure 7: CER错误类型分解 (Figure7_error_breakdown)
- 按严重、主要、次要错误分类
- Baseline方法100%存在严重错误(忽视手术史)
- BM Agent严重错误数为0

## Figure 8: 患者级别关键指标折线图 (Figure8_patient_line_charts)
- 四子图: CPI、CCR、PTR、MQR
- BM Agent (9例) vs Enhanced RAG (8例, Case8缺失)
- 展示个体患者间指标波动和组间差异
- 均值线标注和极值点标注

## Figure 9: CPI详细对比图 (Figure9_cpi_detailed)
- BM Agent vs Enhanced RAG逐患者对比
- 均值差异区域填充显示
- 标注具体CPI数值
- 直观展示CPI提升幅度 (+0.082)

## 文件位置
所有图表保存在: analysis/final_figures/
格式: PNG (300 DPI) + PDF (矢量图)
- Figure 1-7: 方法级对比 (4种方法)
- Figure 8-9: 患者级对比 (个体患者折线)
