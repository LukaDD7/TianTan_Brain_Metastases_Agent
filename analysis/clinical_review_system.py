#!/usr/bin/env python3
"""
临床医生审查评分系统
Clinical Review & Scoring System for BM Agent Reports

评分单位：每个Case独立评分
评分者角色：临床肿瘤科医生（模拟）
"""

import json
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CCRScore:
    """临床一致性评分 (Clinical Consistency Rate)"""
    # 治疗线判定准确性 (0-4分)
    # 4分: 完全准确（与实际治疗线一致）
    # 3分: 基本准确（±1线）
    # 2分: 部分准确（±2线）
    # 1分: 明显错误（±3线以上）
    # 0分: 完全错误或遗漏
    treatment_line: float

    # 方案选择合理性 (0-4分)
    # 4分: 完全符合指南/标准治疗
    # 3分: 基本合理，有小瑕疵
    # 2分: 部分合理，需调整
    # 1分: 不合理，可能有害
    # 0分: 严重错误或遗漏
    scheme_selection: float

    # 剂量参数准确性 (0-4分)
    # 4分: 完全符合标准剂量
    # 3分: 基本正确，有引用支持
    # 2分: 剂量范围正确但不够精确
    # 1分: 剂量明显错误
    # 0分: 未提及或严重错误
    dosage_params: float

    # 排他性论证充分性 (0-4分)
    # 4分: 充分论证，引用可靠
    # 3分: 基本充分，略有不足
    # 2分: 有论证但不够详细
    # 1分: 论证薄弱
    # 0分: 未提供论证
    exclusion_reasoning: float

    # 与真实临床路径一致性 (0-4分)
    # 4分: 与实际治疗完全一致
    # 3分: 基本一致，细节差异
    # 2分: 部分一致
    # 1分: 明显偏离
    # 0分: 完全偏离
    clinical_path_alignment: float

    comments: str = ""

    @property
    def overall(self) -> float:
        """CCR总分 (0-4分制)"""
        weights = [0.25, 0.25, 0.20, 0.15, 0.15]
        scores = [self.treatment_line, self.scheme_selection, self.dosage_params,
                 self.exclusion_reasoning, self.clinical_path_alignment]
        return sum(w * s for w, s in zip(weights, scores))


@dataclass
class MQRScore:
    """MDT报告质量评分 (MDT Quality Rate)"""
    # 8模块完整性 (0-4分)
    # 4分: 所有8个模块完整
    # 3分: 7个模块完整
    # 2分: 5-6个模块
    # 1分: 3-4个模块
    # 0分: <3个模块
    module_completeness: float

    # 模块适用性判断 (0-4分)
    # 4分: 正确识别适用/不适用模块（如Module 6 N/A）
    # 3分: 基本正确，小瑕疵
    # 2分: 部分正确
    # 1分: 有明显错误
    # 0分: 严重错误（如为手术患者标记N/A）
    module_applicability: float

    # 结构化程度 (0-4分)
    # 4分: 高度结构化，便于阅读
    # 3分: 良好结构化
    # 2分: 一般
    # 1分: 较差
    # 0分: 混乱无序
    structured_format: float

    # 引用格式规范性 (0-4分)
    # 4分: 所有引用格式正确且可追溯
    # 3分: 大部分正确
    # 2分: 部分正确
    # 1分: 格式问题多
    # 0分: 无引用或格式严重错误
    citation_format: float

    # 不确定性处理 (0-4分)
    # 4分: 明确标注不确定信息（如KPS unknown）
    # 3分: 大部分标注
    # 2分: 部分标注
    # 1分: 较少标注
    # 0分: 未标注不确定性
    uncertainty_handling: float

    comments: str = ""

    @property
    def overall(self) -> float:
        """MQR总分 (0-4分制)"""
        weights = [0.30, 0.25, 0.20, 0.15, 0.10]
        scores = [self.module_completeness, self.module_applicability,
                 self.structured_format, self.citation_format, self.uncertainty_handling]
        return sum(w * s for w, s in zip(weights, scores))


@dataclass
class CERScore:
    """临床错误评分 (Clinical Error Rate)"""
    # 严重错误（权重3.0）- 可能导致患者伤害
    critical_errors: List[Dict]

    # 主要错误（权重2.0）- 影响治疗决策
    major_errors: List[Dict]

    # 次要错误（权重1.0）- 细节问题
    minor_errors: List[Dict]

    comments: str = ""

    @property
    def weighted_score(self) -> float:
        """加权错误分数"""
        return (len(self.critical_errors) * 3.0 +
                len(self.major_errors) * 2.0 +
                len(self.minor_errors) * 1.0)

    @property
    def cer(self) -> float:
        """CER (0-1分，0表示无错误，1表示严重错误)"""
        # 假设最大可能错误分数为15分
        max_score = 15.0
        return min(self.weighted_score / max_score, 1.0)


@dataclass
class ClinicalReview:
    """单个Case的完整临床审查"""
    patient_id: str
    case_id: str

    # 真实临床路径信息
    admission_dx: str
    discharge_dx: str
    pathology: str
    treatment_course: str

    # 评分
    ccr: CCRScore
    mqr: MQRScore
    cer: CERScore

    # PTR（从报告计算）
    ptr: float

    # 总体评价
    overall_assessment: str
    key_strengths: List[str]
    key_weaknesses: List[str]

    # 审查时间
    review_date: str

    @property
    def cpi(self) -> float:
        """综合性能指数"""
        # CPI = 0.35×CCR + 0.25×PTR + 0.25×MQR + 0.15×(1-CER)
        ccr_norm = self.ccr.overall / 4.0  # 归一化到0-1
        mqr_norm = self.mqr.overall / 4.0
        return (0.35 * ccr_norm +
                0.25 * self.ptr +
                0.25 * mqr_norm +
                0.15 * (1 - self.cer))

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "patient_id": self.patient_id,
            "case_id": self.case_id,
            "clinical_path": {
                "admission_dx": self.admission_dx,
                "discharge_dx": self.discharge_dx,
                "pathology": self.pathology,
                "treatment_course": self.treatment_course[:200] + "..." if len(self.treatment_course) > 200 else self.treatment_course
            },
            "scores": {
                "ccr": {
                    "treatment_line": self.ccr.treatment_line,
                    "scheme_selection": self.ccr.scheme_selection,
                    "dosage_params": self.ccr.dosage_params,
                    "exclusion_reasoning": self.ccr.exclusion_reasoning,
                    "clinical_path_alignment": self.ccr.clinical_path_alignment,
                    "overall": round(self.ccr.overall, 2),
                    "comments": self.ccr.comments
                },
                "mqr": {
                    "module_completeness": self.mqr.module_completeness,
                    "module_applicability": self.mqr.module_applicability,
                    "structured_format": self.mqr.structured_format,
                    "citation_format": self.mqr.citation_format,
                    "uncertainty_handling": self.mqr.uncertainty_handling,
                    "overall": round(self.mqr.overall, 2),
                    "comments": self.mqr.comments
                },
                "cer": {
                    "critical_count": len(self.cer.critical_errors),
                    "major_count": len(self.cer.major_errors),
                    "minor_count": len(self.cer.minor_errors),
                    "weighted_score": self.cer.weighted_score,
                    "cer": round(self.cer.cer, 3),
                    "errors": {
                        "critical": self.cer.critical_errors,
                        "major": self.cer.major_errors,
                        "minor": self.cer.minor_errors
                    },
                    "comments": self.cer.comments
                },
                "ptr": round(self.ptr, 3),
                "cpi": round(self.cpi, 3)
            },
            "assessment": {
                "overall": self.overall_assessment,
                "strengths": self.key_strengths,
                "weaknesses": self.key_weaknesses
            },
            "review_date": self.review_date
        }


class ReportAnalyzer:
    """报告分析器"""

    @staticmethod
    def calculate_ptr(report_content: str) -> float:
        """计算物理可追溯率 (PTR)"""
        # 提取所有引用
        citations = {
            "pubmed": re.findall(r'\[PubMed:\s*PMID\s+(\d+)\]', report_content),
            "oncokb": re.findall(r'\[OncoKB:\s*([^\]]+)\]', report_content),
            "local": re.findall(r'\[Local:\s*([^\]]+)\]', report_content),
            "guideline": re.findall(r'\[Guideline:\s*([^\]]+)\]', report_content),
            "web": re.findall(r'\[Web:\s*([^,\]]+)', report_content),
            "parametric": re.findall(r'\[Parametric Knowledge:\s*([^\]]+)\]', report_content),
            "digital": re.findall(r'\[(\d+(?:,\s*\d+)*)\]', report_content)
        }

        total = sum(len(v) for v in citations.values())
        if total == 0:
            return 0.0

        # 完全可追溯
        fully = len(citations["pubmed"]) + len(citations["oncokb"]) + \
                len(citations["local"]) + len(citations["guideline"])
        # 部分可追溯
        partial = len(citations["web"]) + len(citations["parametric"])
        # 不可追溯
        non_traceable = len(citations["digital"])

        ptr = (2 * fully + 1 * partial) / (2 * total)
        return round(ptr, 3)

    @staticmethod
    def count_modules(report_content: str) -> Tuple[int, List[str]]:
        """统计模块数量和类型"""
        modules = []
        module_patterns = [
            r'## Module 1[:：]',
            r'## Module 2[:：]',
            r'## Module 3[:：]',
            r'## Module 4[:：]',
            r'## Module 5[:：]',
            r'## Module 6[:：]',
            r'## Module 7[:：]',
            r'## Module 8[:：]'
        ]

        for i, pattern in enumerate(module_patterns, 1):
            if re.search(pattern, report_content, re.IGNORECASE):
                modules.append(f"Module {i}")

        return len(modules), modules


class ClinicalReviewer:
    """临床审查器 - 模拟临床医生审查"""

    def __init__(self, samples_dir: str = "analysis/samples",
                 test_cases_path: str = "workspace/test_cases_wide.xlsx"):
        self.samples_dir = Path(samples_dir)
        self.test_cases_path = Path(test_cases_path)
        self.report_analyzer = ReportAnalyzer()

        # 加载真实临床路径数据
        self.clinical_data = self._load_clinical_data()

    def _load_clinical_data(self) -> pd.DataFrame:
        """加载真实临床路径数据"""
        try:
            df = pd.read_excel(self.test_cases_path)
            return df
        except Exception as e:
            print(f"Error loading clinical data: {e}")
            return pd.DataFrame()

    def get_case_info(self, case_id: str) -> Dict:
        """获取Case的真实临床信息"""
        if self.clinical_data.empty:
            return {}

        row = self.clinical_data[self.clinical_data['id'] == case_id]
        if row.empty:
            return {}

        return {
            "admission_dx": str(row.iloc[0].get('入院诊断', '')),
            "discharge_dx": str(row.iloc[0].get('出院诊断', '')),
            "pathology": str(row.iloc[0].get('病理诊断', '')),
            "treatment_course": str(row.iloc[0].get('诊疗经过', '')),
            "age": str(row.iloc[0].get('年龄', '')),
            "gender": str(row.iloc[0].get('性别', '')),
            "mri": str(row.iloc[0].get('头部MRI', '')),
            "history": str(row.iloc[0].get('既往史', '')),
            "present_illness": str(row.iloc[0].get('现病史', ''))
        }

    def review_case(self, patient_id: str, case_id: str) -> ClinicalReview:
        """审查单个Case"""
        # 读取报告
        report_path = self.samples_dir / patient_id / f"MDT_Report_{patient_id}.md"
        if not report_path.exists():
            raise FileNotFoundError(f"Report not found: {report_path}")

        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()

        # 获取真实临床路径
        case_info = self.get_case_info(case_id)

        # 计算PTR
        ptr = self.report_analyzer.calculate_ptr(report_content)

        # 统计模块
        module_count, modules = self.report_analyzer.count_modules(report_content)

        # 这里应该由临床医生根据报告内容和真实临床路径进行评分
        # 现在返回一个结构，等待手动填写评分

        return ClinicalReview(
            patient_id=patient_id,
            case_id=case_id,
            admission_dx=case_info.get('admission_dx', ''),
            discharge_dx=case_info.get('discharge_dx', ''),
            pathology=case_info.get('pathology', ''),
            treatment_course=case_info.get('treatment_course', ''),
            ccr=CCRScore(
                treatment_line=0.0,  # 待评分
                scheme_selection=0.0,
                dosage_params=0.0,
                exclusion_reasoning=0.0,
                clinical_path_alignment=0.0,
                comments="待临床医生评分"
            ),
            mqr=MQRScore(
                module_completeness=module_count / 8 * 4,  # 自动计算
                module_applicability=0.0,  # 待评分
                structured_format=0.0,
                citation_format=0.0,
                uncertainty_handling=0.0,
                comments=f"检测到 {module_count}/8 个模块: {', '.join(modules)}"
            ),
            cer=CERScore(
                critical_errors=[],
                major_errors=[],
                minor_errors=[],
                comments="待审查"
            ),
            ptr=ptr,
            overall_assessment="待评估",
            key_strengths=[],
            key_weaknesses=[],
            review_date=datetime.now().isoformat()
        )

    def review_all_cases(self, case_mapping: Dict[str, str]) -> List[ClinicalReview]:
        """审查所有Cases"""
        reviews = []
        for patient_id, case_id in case_mapping.items():
            try:
                print(f"Reviewing {patient_id} ({case_id})...")
                review = self.review_case(patient_id, case_id)
                reviews.append(review)
            except Exception as e:
                print(f"Error reviewing {patient_id}: {e}")
        return reviews


# Case ID到Patient ID的映射
case_mapping = {
    "605525": "Case8",   # 结肠癌脑转移 KRAS G12V
    "612908": "Case7",   # 肺癌脑转移
    "638114": "Case6",   # 乳腺癌脑转移
    "640880": "Case2",   # 肺癌脑转移
    "648772": "Case1",   # 黑色素瘤脑转移
    "665548": "Case4",   # 贲门癌脑转移
    "708387": "Case9",   # 肺癌 MET扩增
    "747724": "Case10",  # 乳腺癌 HER2+
    "868183": "Case3"    # 肺癌 SMARCA4突变
}


if __name__ == "__main__":
    reviewer = ClinicalReviewer()
    reviews = reviewer.review_all_cases(case_mapping)

    # 输出评分模板
    print("\n" + "="*60)
    print("临床审查评分模板")
    print("="*60)

    for review in reviews:
        print(f"\n【{review.patient_id} / {review.case_id}】")
        print(f"PTR: {review.ptr}")
        print(f"模块完整性: {review.mqr.module_completeness}/4")
        print(f"真实出院诊断: {review.discharge_dx[:100]}...")
        print("-"*60)
