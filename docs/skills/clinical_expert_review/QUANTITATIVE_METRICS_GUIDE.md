# Clinical Expert Review SKILL - 量化指标计算规范

## 分值来源声明

**所有分数的唯一来源：专家审查打分**

| 指标 | 来源 | 说明 |
|------|------|------|
| CCR | 专家打分 | S_line, S_scheme, S_dose, S_reject, S_align (0-4分) |
| MQR | 专家打分 | S_complete, S_applicable, S_format, S_citation, S_uncertainty (0-4分) |
| CER | 专家分级 | Critical/Major/Minor错误识别及权重分配 |
| PTR | 专家统计 | PubMed/Guideline/Web/Local引用数量统计 |

**严禁**：使用自动化工具生成分数，所有分数必须经专家审查后手动录入。

---

## 计算流程规范

### 步骤1: 专家打分录入

创建打分文件 `expert_scores.json`:
```json
{
  "patient_id": "868183",
  "expert_name": "Claude Code",
  "review_date": "2026-04-09",
  "ccr_scores": {
    "s_line": 3,
    "s_scheme": 3,
    "s_dose": 2,
    "s_reject": 3,
    "s_align": 2
  },
  "mqr_scores": {
    "s_complete": 4,
    "s_applicable": 4,
    "s_format": 4,
    "s_citation": 2,
    "s_uncertainty": 2
  },
  "cer_errors": [
    {"level": "Major", "weight": 2.0, "description": "..."},
    {"level": "Major", "weight": 2.0, "description": "..."}
  ],
  "ptr_counts": {
    "pubmed": 0,
    "guideline": 0,
    "web": 0,
    "local": 7,
    "parametric": 5,
    "insufficient": 3,
    "total_claims": 30
  }
}
```

### 步骤2: 自动化计算

使用统一的Python脚本计算（见下方`calculate_metrics.py`）。

### 步骤3: 结果验证

- 核对计算结果与手工计算是否一致
- 验证CPI公式计算正确性
- 生成分项计算说明

### 步骤4: 生成手工报告

提取最终结果，生成人类可读的审查报告。

---

## 自动化计算脚本

### calculate_metrics.py

```python
#!/usr/bin/env python3
"""
Clinical Expert Review - 量化指标自动化计算脚本
所有输入分数必须来自专家审查打分
"""

import json
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExpertScores:
    """专家打分数据"""
    patient_id: str
    ccr_scores: Dict[str, int]  # s_line, s_scheme, s_dose, s_reject, s_align
    mqr_scores: Dict[str, int]  # s_complete, s_applicable, s_format, s_citation, s_uncertainty
    cer_errors: List[Dict]      # level, weight, description
    ptr_counts: Dict[str, int]  # pubmed, guideline, web, local, parametric, insufficient, total_claims


class MetricsCalculator:
    """量化指标计算器"""
    
    # 权重常量（CPI公式）
    CPI_WEIGHT_CCR = 0.35
    CPI_WEIGHT_PTR = 0.25
    CPI_WEIGHT_MQR = 0.25
    CPI_WEIGHT_CER = 0.15
    
    # CER归一化常数
    CER_MAX_WEIGHT = 15.0
    
    # PTR引用权重
    PTR_WEIGHTS = {
        "pubmed": 1.0,
        "guideline": 0.8,
        "local": 0.8,
        "web": 0.5,
        "parametric": 0.0,
        "insufficient": 0.0
    }
    
    @staticmethod
    def calculate_ccr(ccr_scores: Dict[str, int]) -> Tuple[float, str]:
        """
        计算CCR (Clinical Consistency Rate)
        
        公式: CCR = (S_line + S_scheme + S_dose + S_reject + S_align) / 5
        
        Args:
            ccr_scores: 包含5个子项分数的字典
            
        Returns:
            (CCR分数, 计算说明)
        """
        required_keys = ["s_line", "s_scheme", "s_dose", "s_reject", "s_align"]
        
        if not all(k in ccr_scores for k in required_keys):
            raise ValueError(f"CCR打分不完整，需要: {required_keys}")
        
        scores = [ccr_scores[k] for k in required_keys]
        ccr = sum(scores) / len(scores)
        
        explanation = (
            f"CCR = ({scores[0]} + {scores[1]} + {scores[2]} + {scores[3]} + {scores[4]}) / 5 = {ccr:.1f} / 4.0\n"
            f"  - S_line: {scores[0]}/4 (治疗线判定准确性)\n"
            f"  - S_scheme: {scores[1]}/4 (首选方案选择合理性)\n"
            f"  - S_dose: {scores[2]}/4 (剂量参数准确性)\n"
            f"  - S_reject: {scores[3]}/4 (排他性论证充分性)\n"
            f"  - S_align: {scores[4]}/4 (临床路径一致性)"
        )
        
        return round(ccr, 1), explanation
    
    @staticmethod
    def calculate_mqr(mqr_scores: Dict[str, int]) -> Tuple[float, str]:
        """
        计算MQR (MDT Quality Rate)
        
        公式: MQR = (S_complete + S_applicable + S_format + S_citation + S_uncertainty) / 5
        
        Args:
            mqr_scores: 包含5个子项分数的字典
            
        Returns:
            (MQR分数, 计算说明)
        """
        required_keys = ["s_complete", "s_applicable", "s_format", "s_citation", "s_uncertainty"]
        
        if not all(k in mqr_scores for k in required_keys):
            raise ValueError(f"MQR打分不完整，需要: {required_keys}")
        
        scores = [mqr_scores[k] for k in required_keys]
        mqr = sum(scores) / len(scores)
        
        explanation = (
            f"MQR = ({scores[0]} + {scores[1]} + {scores[2]} + {scores[3]} + {scores[4]}) / 5 = {mqr:.1f} / 4.0\n"
            f"  - S_complete: {scores[0]}/4 (8模块完整性)\n"
            f"  - S_applicable: {scores[1]}/4 (模块适用性判断)\n"
            f"  - S_format: {scores[2]}/4 (结构化程度)\n"
            f"  - S_citation: {scores[3]}/4 (引用格式规范性)\n"
            f"  - S_uncertainty: {scores[4]}/4 (不确定性处理)"
        )
        
        return round(mqr, 1), explanation
    
    @staticmethod
    def calculate_cer(cer_errors: List[Dict]) -> Tuple[float, str]:
        """
        计算CER (Clinical Error Rate)
        
        公式: CER = min((Σ w_j × n_j) / 15, 1.0)
        
        错误权重:
        - Critical: 3.0 (可能危及生命)
        - Major: 2.0 (显著影响治疗效果)
        - Minor: 1.0 (轻微影响治疗质量)
        
        Args:
            cer_errors: 错误列表，每项包含level和weight
            
        Returns:
            (CER分数, 计算说明)
        """
        error_weights = {"Critical": 3.0, "Major": 2.0, "Minor": 1.0}
        
        total_weight = 0
        error_counts = {"Critical": 0, "Major": 0, "Minor": 0}
        
        for error in cer_errors:
            level = error["level"]
            weight = error.get("weight", error_weights.get(level, 1.0))
            total_weight += weight
            error_counts[level] += 1
        
        cer = min(total_weight / MetricsCalculator.CER_MAX_WEIGHT, 1.0)
        
        explanation_parts = []
        for level, count in error_counts.items():
            if count > 0:
                w = error_weights[level]
                explanation_parts.append(f"{count}个{level}×{w}={count*w:.1f}")
        
        explanation = (
            f"CER = min(({ ' + '.join(explanation_parts) }) / 15, 1.0)\n"
            f"     = min({total_weight:.1f} / 15, 1.0) = {cer:.3f}"
        )
        
        return round(cer, 3), explanation
    
    @classmethod
    def calculate_ptr(cls, ptr_counts: Dict[str, int], method: str = "rag") -> Tuple[float, str]:
        """
        计算PTR (Physical Traceability Rate)
        
        公式: PTR = Σ(各类型引用数 × 权重) / 总声明数
        
        引用权重:
        - PubMed: 1.0
        - Guideline: 0.8
        - Local: 0.8
        - Web: 0.5
        - Parametric: 0.0
        - Insufficient: 0.0
        
        Args:
            ptr_counts: 引用统计字典
            method: "rag" 或 "websearch"，影响PTR计算方式
            
        Returns:
            (PTR分数, 计算说明)
        """
        total_claims = ptr_counts.get("total_claims", 1)
        if total_claims == 0:
            return 0.0, "总声明数为0，PTR=0"
        
        weighted_sum = 0
        calculation_parts = []
        
        for cite_type, weight in cls.PTR_WEIGHTS.items():
            count = ptr_counts.get(cite_type, 0)
            if count > 0:
                contribution = count * weight
                weighted_sum += contribution
                calculation_parts.append(f"{count}×{weight}={contribution:.1f}")
        
        ptr = weighted_sum / total_claims
        
        explanation = (
            f"PTR = ({ ' + '.join(calculation_parts) }) / {total_claims}\n"
            f"    = {weighted_sum:.1f} / {total_claims} = {ptr:.3f}"
        )
        
        return round(ptr, 3), explanation
    
    @classmethod
    def calculate_cpi(cls, ccr: float, mqr: float, cer: float, ptr: float) -> Tuple[float, str]:
        """
        计算CPI (Composite Performance Index)
        
        公式: CPI = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)
        
        权重分配:
        - CCR: 35% (临床决策最重要)
        - PTR: 25% (证据可靠性)
        - MQR: 25% (报告质量)
        - CER: 15% (错误惩罚，已归一化)
        
        Args:
            ccr: CCR分数 (0-4)
            mqr: MQR分数 (0-4)
            cer: CER分数 (0-1)
            ptr: PTR分数 (0-1)
            
        Returns:
            (CPI分数, 计算说明)
        """
        ccr_component = cls.CPI_WEIGHT_CCR * (ccr / 4)
        ptr_component = cls.CPI_WEIGHT_PTR * ptr
        mqr_component = cls.CPI_WEIGHT_MQR * (mqr / 4)
        cer_component = cls.CPI_WEIGHT_CER * (1 - cer)
        
        cpi = ccr_component + ptr_component + mqr_component + cer_component
        
        explanation = (
            f"CPI = 0.35×({ccr:.1f}/4) + 0.25×{ptr:.3f} + 0.25×({mqr:.1f}/4) + 0.15×(1-{cer:.3f})\n"
            f"    = 0.35×{ccr/4:.3f} + 0.25×{ptr:.3f} + 0.25×{mqr/4:.3f} + 0.15×{1-cer:.3f}\n"
            f"    = {ccr_component:.3f} + {ptr_component:.3f} + {mqr_component:.3f} + {cer_component:.3f}\n"
            f"    = {cpi:.3f}"
        )
        
        return round(cpi, 3), explanation


def calculate_all_metrics(expert_scores: ExpertScores) -> Dict:
    """
    计算所有指标
    
    Args:
        expert_scores: 专家打分数据
        
    Returns:
        包含所有指标的字典
    """
    calc = MetricsCalculator()
    
    # 计算各项指标
    ccr, ccr_exp = calc.calculate_ccr(expert_scores.ccr_scores)
    mqr, mqr_exp = calc.calculate_mqr(expert_scores.mqr_scores)
    cer, cer_exp = calc.calculate_cer(expert_scores.cer_errors)
    ptr, ptr_exp = calc.calculate_ptr(expert_scores.ptr_counts)
    cpi, cpi_exp = calc.calculate_cpi(ccr, mqr, cer, ptr)
    
    return {
        "patient_id": expert_scores.patient_id,
        "ccr": {"score": ccr, "explanation": ccr_exp},
        "mqr": {"score": mqr, "explanation": mqr_exp},
        "cer": {"score": cer, "explanation": cer_exp},
        "ptr": {"score": ptr, "explanation": ptr_exp},
        "cpi": {"score": cpi, "explanation": cpi_exp}
    }


def generate_statistics(values: List[float]) -> Dict:
    """
    计算统计指标（均值、标准差、范围）
    
    Args:
        values: 数值列表
        
    Returns:
        统计指标字典
    """
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)
    
    return {
        "n": n,
        "mean": round(mean, 3),
        "std": round(std, 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "range": round(max(values) - min(values), 3)
    }


# 示例使用
if __name__ == "__main__":
    # 示例：专家打分
    scores = ExpertScores(
        patient_id="868183",
        ccr_scores={"s_line": 3, "s_scheme": 3, "s_dose": 2, "s_reject": 3, "s_align": 2},
        mqr_scores={"s_complete": 4, "s_applicable": 4, "s_format": 4, "s_citation": 2, "s_uncertainty": 2},
        cer_errors=[
            {"level": "Major", "weight": 2.0, "description": "患者输入数据被错误标注"},
            {"level": "Major", "weight": 2.0, "description": "Parametric Knowledge标注过多"}
        ],
        ptr_counts={"local": 7, "parametric": 5, "insufficient": 3, "total_claims": 30}
    )
    
    # 计算所有指标
    results = calculate_all_metrics(scores)
    
    # 打印结果
    print("=" * 60)
    print(f"患者 {results['patient_id']} 审查结果")
    print("=" * 60)
    print(f"\nCCR: {results['ccr']['score']:.1f}")
    print(results['ccr']['explanation'])
    print(f"\nMQR: {results['mqr']['score']:.1f}")
    print(results['mqr']['explanation'])
    print(f"\nCER: {results['cer']['score']:.3f}")
    print(results['cer']['explanation'])
    print(f"\nPTR: {results['ptr']['score']:.3f}")
    print(results['ptr']['explanation'])
    print(f"\nCPI: {results['cpi']['score']:.3f}")
    print(results['cpi']['explanation'])
```

---

## 手工报告模板

### 分患者报告模板

```markdown
## 患者 {patient_id} 审查报告

**审查日期**: YYYY-MM-DD
**审查专家**: [专家姓名]
**Baseline方法**: [RAG V2 / Web Search V2]

### 一、患者信息
- 肿瘤类型: [类型]
- 治疗线数: [N]线
- 当前状态: [状态]

### 二、专家打分

#### CCR打分
- S_line: [N]/4 [说明]
- S_scheme: [N]/4 [说明]
- S_dose: [N]/4 [说明]
- S_reject: [N]/4 [说明]
- S_align: [N]/4 [说明]

**CCR计算**: [显示计算公式和过程]

#### MQR打分
- S_complete: [N]/4 [说明]
- S_applicable: [N]/4 [说明]
- S_format: [N]/4 [说明]
- S_citation: [N]/4 [说明]
- S_uncertainty: [N]/4 [说明]

**MQR计算**: [显示计算公式和过程]

#### CER分级
[列出所有识别的错误]

**CER计算**: [显示计算公式和过程]

#### PTR统计
- PubMed引用: [N]处
- Guideline引用: [N]处
- Web引用: [N]处
- Local引用: [N]处
- Parametric Knowledge: [N]处
- Insufficient标记: [N]处
- 总声明数: [N]

**PTR计算**: [显示计算公式和过程]

### 三、CPI综合计算
[显示完整CPI计算公式和过程]

**最终CPI**: [value]

### 四、关键发现
[专家发现的问题和优点]

### 五、审查结论
[总结性评价]
```

### 汇总报告模板

```markdown
## Set-1 Batch 审查汇总报告

### 一、统计摘要

| 指标 | 方法 | Mean±SD | Range | 中位数 |
|------|------|---------|-------|--------|
| CPI | RAG V2 | X.XXX±X.XXX | X.XXX-X.XXX | X.XXX |
| CPI | Web Search V2 | X.XXX±X.XXX | X.XXX-X.XXX | X.XXX |
| CCR | RAG V2 | X.XX±X.XX | X.X-X.X | X.XX |
| ... | ... | ... | ... | ... |

### 二、分患者详细数据

| 患者ID | 方法 | CPI | CCR | MQR | CER | PTR |
|--------|------|-----|-----|-----|-----|-----|
| ... | ... | ... | ... | ... | ... | ... |

### 三、对比分析
[方法间对比和提升幅度]

### 四、审查数据来源
- **专家审查日期**: YYYY-MM-DD
- **专家姓名**: [姓名]
- **计算脚本**: calculate_metrics.py v[X.X]
- **验证状态**: [已验证/待验证]
```

---

## 质量控制检查清单

在生成最终报告前，必须完成以下检查：

- [ ] 所有CCR子项分数已录入（0-4分）
- [ ] 所有MQR子项分数已录入（0-4分）
- [ ] CER错误已完整识别并分级
- [ ] PTR引用已完整统计
- [ ] 使用calculate_metrics.py计算所有指标
- [ ] 手工验证计算结果（抽查至少3例）
- [ ] 生成统计摘要（含Mean±SD）
- [ ] 所有分数来源已标注（专家审查）
- [ ] 报告已包含详细的计算过程说明
