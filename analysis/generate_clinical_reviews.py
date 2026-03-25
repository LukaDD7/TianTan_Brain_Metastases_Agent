#!/usr/bin/env python3
"""
临床医生详细审查报告
Clinical Doctor Detailed Review Report

审查者：AI模拟临床肿瘤科医生
审查日期：2026-03-25
"""

import json
from pathlib import Path
from datetime import datetime


# 完整的临床审查数据（手动评分）
CLINICAL_REVIEWS = {
    "605525": {
        "case_id": "Case8",
        "patient_info": {
            "tumor_type": "结肠癌",
            "molecular": "KRAS G12V",
            "stage": "IV期",
            "prior_lines": 5
        },
        "real_clinical_path": {
            "admission_dx": "恶性肿瘤靶向治疗（+免疫治疗）、降结肠恶性肿瘤（中分化腺癌 pT4N0M0 IIB KRAS G12V）、脑继发恶性肿瘤",
            "discharge_dx": "恶性肿瘤支持治疗、降结肠恶性肿瘤、脑继发恶性肿瘤（SRS及手术后）",
            "treatment_course": "患者体力较弱，治疗耐受性欠佳，暂不行局部治疗及全身抗肿瘤专科治疗。嘱院外继续对症支持治疗。",
            "actual_treatment": "最佳支持治疗"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 3.5,
                "treatment_line_reason": "报告正确判定为'六线治疗决策'（实际患者已完成5线治疗，当前为六线决策）。既往治疗史梳理完整，时间线清晰。",
                "scheme_selection": 3.0,
                "scheme_selection_reason": "报告推荐方案A（继续五线方案）和方案B（最佳支持治疗），与真实临床路径一致（实际给予了支持治疗）。但报告倾向于继续抗肿瘤治疗，而实际因患者体力差选择了纯支持治疗。",
                "dosage_params": 3.5,
                "dosage_params_reason": "替莫唑胺150mg/m²、卡培他滨剂量引用正确，有文献支持。依沃西单抗剂量正确。",
                "exclusion_reasoning": 4.0,
                "exclusion_reasoning_reason": "排他性论证非常充分，对EGFR抑制剂、HER2靶向、再次手术/放疗、免疫单药均有详细论证和引用。",
                "clinical_path_alignment": 3.5,
                "clinical_path_alignment_reason": "与真实路径高度一致，识别出患者体力差、多发转移、不适合局部治疗等关键点。",
                "overall_ccr": 3.4
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 4.0,
                "module_applicability_reason": "Module 6正确标记为'当前无手术或放疗计划'，与实际情况一致。",
                "structured_format": 4.0,
                "citation_format": 4.0,
                "uncertainty_handling": 4.0,
                "uncertainty_reason": "明确标注了KPS/ECOG unknown、MSI/MMR unknown等缺失数据。",
                "overall_mqr": 4.0
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [
                    {
                        "error": "治疗线数计算中，将2025.6和2025.7的依沃西单抗方案分别列为五线第1周期和第2周期，实际上应为同一方案的不同周期",
                        "impact": "低"
                    }
                ],
                "cer_score": 0.067
            },
            "ptr": 1.0,
            "cpi": 0.89
        },
        "assessment": {
            "overall": "优秀。报告全面准确，特别是排他性论证非常充分。治疗线数判定准确，与真实临床决策基本一致。",
            "strengths": [
                "既往治疗史梳理详尽，时间线清晰",
                "排他性论证充分，引用可靠",
                "正确识别Module 6不适用",
                "分子检测建议合理",
                "不确定性数据明确标注"
            ],
            "weaknesses": [
                "对体力状态差的患者的抗肿瘤治疗推荐过于积极（实际选择了纯支持治疗）",
                "治疗线数表格中周期计数略有混淆"
            ]
        }
    },

    "612908": {
        "case_id": "Case7",
        "patient_info": {
            "tumor_type": "肺癌",
            "stage": "IV期",
            "prior_treatment": "术后复发"
        },
        "real_clinical_path": {
            "admission_dx": "颅内占位性病变（额部-颅骨，顶叶，左侧，复发）、脑转移癌术后、肺癌术后",
            "discharge_dx": "转移性腺癌（额部-颅骨，顶叶，左侧，复发）、低钾血症、脑转移癌术后、肺癌术后",
            "treatment_course": "2022.4月全麻下行左额颞开颅肿瘤切除术，术后予以对症治疗。目前患者恢复顺利。",
            "actual_treatment": "开颅手术"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 3.0,
                "treatment_line_reason": "患者为术后复发，报告正确识别为复发转移阶段，但治疗线数判定不够明确。",
                "scheme_selection": 3.5,
                "scheme_selection_reason": "报告推荐了术后辅助治疗和随访监测，与真实治疗（手术+术后管理）一致。",
                "dosage_params": 3.0,
                "dosage_params_reason": "报告中提到了替莫唑胺剂量参考，但该患者实际未使用化疗。",
                "exclusion_reasoning": 3.5,
                "exclusion_reasoning_reason": "提供了替代方案的排除理由，包括放疗和系统治疗的排他性论证。",
                "clinical_path_alignment": 3.5,
                "clinical_path_alignment_reason": "与真实手术路径基本一致，Module 6围手术期管理描述准确。",
                "overall_ccr": 3.3
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 3.5,
                "module_applicability_reason": "Module 6适用于手术患者，描述合理。但部分术后管理细节不够具体。",
                "structured_format": 4.0,
                "citation_format": 3.5,
                "uncertainty_handling": 3.5,
                "uncertainty_reason": "部分分子特征标注为unknown。",
                "overall_mqr": 3.7
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [
                    {
                        "error": "报告中引用格式部分使用数字引用[1]，而非标准的[PubMed: PMID XXX]格式",
                        "impact": "中"
                    }
                ],
                "cer_score": 0.067
            },
            "ptr": 0.9,  # 有少量数字引用
            "cpi": 0.85
        },
        "assessment": {
            "overall": "良好。报告整体结构完整，对手术患者的管理建议合理。",
            "strengths": [
                "手术指征判断准确",
                "Module 6围手术期管理详细",
                "术后随访计划完整"
            ],
            "weaknesses": [
                "引用格式不够统一",
                "个别推荐药物与实际治疗不完全吻合"
            ]
        }
    },

    "638114": {
        "case_id": "Case6",
        "patient_info": {
            "tumor_type": "肺腺癌",
            "prior_treatment": "术后"
        },
        "real_clinical_path": {
            "admission_dx": "恶性肿瘤靶向治疗、肺腺癌术后、脑继发恶性肿瘤",
            "discharge_dx": "同上",
            "treatment_course": "2021-1-11于我院行伽马刀治疗处理颅内病灶，继续口服双倍量奥西替尼。",
            "actual_treatment": "伽马刀 + 奥希替尼"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 3.5,
                "treatment_line_reason": "报告正确识别为术后辅助治疗阶段，对疾病进展判断准确。",
                "scheme_selection": 4.0,
                "scheme_selection_reason": "报告推荐奥希替尼+伽马刀，与真实治疗完全一致。",
                "dosage_params": 3.5,
                "dosage_params_reason": "奥希替尼剂量推荐正确（双倍量80mg即160mg）。",
                "exclusion_reasoning": 3.5,
                "exclusion_reasoning_reason": "对化疗、免疫治疗等替代方案的排除理由充分。",
                "clinical_path_alignment": 4.0,
                "clinical_path_alignment_reason": "与真实临床路径高度一致。",
                "overall_ccr": 3.7
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 4.0,
                "structured_format": 4.0,
                "citation_format": 4.0,
                "uncertainty_handling": 4.0,
                "overall_mqr": 4.0
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [],
                "cer_score": 0.0
            },
            "ptr": 1.0,
            "cpi": 0.92
        },
        "assessment": {
            "overall": "优秀。这是质量最高的报告之一，与真实临床路径几乎完全一致。",
            "strengths": [
                "治疗方案推荐与真实完全一致",
                "奥希替尼剂量（双倍量）准确",
                "伽马刀治疗指征判断正确",
                "报告结构完整，引用规范"
            ],
            "weaknesses": []
        }
    },

    "640880": {
        "case_id": "Case2",
        "patient_info": {
            "tumor_type": "肺癌",
            "stage": "IV期"
        },
        "real_clinical_path": {
            "admission_dx": "恶性肿瘤放疗、颅内继发恶性肿瘤(肺癌)",
            "discharge_dx": "同上",
            "treatment_course": "行伽马刀治疗，周边剂量16Gy，中心剂量32Gy。",
            "actual_treatment": "伽马刀放疗"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 3.0,
                "treatment_line_reason": "报告对初治患者的治疗线数判定基本正确。",
                "scheme_selection": 3.5,
                "scheme_selection_reason": "推荐伽马刀与真实治疗一致，剂量参数正确。",
                "dosage_params": 4.0,
                "dosage_params_reason": "伽马刀剂量16Gy/32Gy准确，有文献支持。",
                "exclusion_reasoning": 3.0,
                "exclusion_reasoning_reason": "对手术 vs 放疗的选择论证充分，但其他系统治疗排除理由较简略。",
                "clinical_path_alignment": 3.5,
                "clinical_path_alignment_reason": "与真实伽马刀治疗路径一致。",
                "overall_ccr": 3.4
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 4.0,
                "structured_format": 4.0,
                "citation_format": 4.0,
                "uncertainty_handling": 3.5,
                "overall_mqr": 3.9
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [],
                "cer_score": 0.0
            },
            "ptr": 1.0,
            "cpi": 0.91
        },
        "assessment": {
            "overall": "良好。报告质量高，放疗剂量参数准确。",
            "strengths": [
                "放疗指征判断正确",
                "伽马刀剂量参数准确",
                "术后脱水处理建议合理"
            ],
            "weaknesses": [
                "系统治疗方案的排他性论证可以更详细"
            ]
        }
    },

    "648772": {
        "case_id": "Case1",
        "patient_info": {
            "tumor_type": "恶性黑色素瘤",
            "prior_treatment": "术后"
        },
        "real_clinical_path": {
            "admission_dx": "颅内占位性病变(额,右)、颈恶性黑色素瘤术后、甲状腺乳头状癌术后",
            "discharge_dx": "恶性黑色素瘤(额,右)、颈恶性黑色素瘤术后",
            "treatment_course": "2020年7月23日全麻下行右额开颅，病变全切除术。",
            "actual_treatment": "开颅手术切除"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 3.0,
                "treatment_line_reason": "报告正确识别为术后患者，但黑色素瘤的治疗线数概念与肺癌/肠癌略有不同。",
                "scheme_selection": 3.5,
                "scheme_selection_reason": "报告推荐了手术+术后管理，与真实治疗一致。",
                "dosage_params": 3.0,
                "dosage_params_reason": "术后辅助治疗剂量建议合理，但该患者实际未接受系统治疗。",
                "exclusion_reasoning": 3.0,
                "exclusion_reasoning_reason": "对放疗 vs 手术的选择论证合理。",
                "clinical_path_alignment": 3.5,
                "clinical_path_alignment_reason": "与真实手术路径基本一致。",
                "overall_ccr": 3.2
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 3.5,
                "structured_format": 4.0,
                "citation_format": 3.5,
                "uncertainty_handling": 3.5,
                "overall_mqr": 3.7
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [
                    {
                        "error": "患者有甲状腺乳头状癌病史，报告中未充分讨论双原发肿瘤的鉴别诊断",
                        "impact": "低"
                    }
                ],
                "cer_score": 0.067
            },
            "ptr": 1.0,
            "cpi": 0.86
        },
        "assessment": {
            "overall": "良好。报告质量尚可，对黑色素瘤脑转移的处理建议合理。",
            "strengths": [
                "手术指征判断正确",
                "既往病史梳理完整",
                "Module 6围手术期管理详细"
            ],
            "weaknesses": [
                "未讨论双原发肿瘤的鉴别",
                "系统治疗推荐与实际略有差异"
            ]
        }
    },

    "665548": {
        "case_id": "Case4",
        "patient_info": {
            "tumor_type": "贲门癌",
            "stage": "IV期"
        },
        "real_clinical_path": {
            "admission_dx": "颅内多发占位性病变、转移性肿瘤待排、贲门恶性肿瘤",
            "discharge_dx": "转移性腺癌(左CPA)、贲门恶性肿瘤、肝继发恶性肿瘤、肺继发恶性肿瘤",
            "treatment_course": "2021年7月8日全麻下行左CPA开颅肿瘤切除术，术后患者要求出院。",
            "actual_treatment": "开颅手术"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 2.5,
                "treatment_line_reason": "报告对治疗线数判定不够清晰，患者实际为初治IV期。",
                "scheme_selection": 3.0,
                "scheme_selection_reason": "报告推荐手术+术后系统治疗，但实际患者术后立即出院，未接受系统治疗。",
                "dosage_params": 3.0,
                "dosage_params_reason": "剂量建议合理，但实际未使用。",
                "exclusion_reasoning": 3.0,
                "exclusion_reasoning_reason": "手术 vs 放疗的选择论证合理。",
                "clinical_path_alignment": 2.5,
                "clinical_path_alignment_reason": "报告建议术后继续治疗，但实际患者因个人原因未接受。",
                "overall_ccr": 2.8
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 3.5,
                "structured_format": 4.0,
                "citation_format": 4.0,
                "uncertainty_handling": 3.0,
                "overall_mqr": 3.7
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [
                    {
                        "error": "报告假设患者会接受术后系统治疗，但实际患者术后立即要求出院，未接受任何系统治疗",
                        "impact": "中"
                    }
                ],
                "minor_errors": [
                    {
                        "error": "对患者的依从性和意愿评估不足",
                        "impact": "低"
                    }
                ],
                "cer_score": 0.20
            },
            "ptr": 1.0,
            "cpi": 0.78
        },
        "assessment": {
            "overall": "中等。报告医学建议合理，但未能准确预测患者的实际选择。",
            "strengths": [
                "手术指征判断正确",
                "术后管理建议合理",
                "多学科协作建议到位"
            ],
            "weaknesses": [
                "未能预测患者拒绝后续治疗的决定",
                "治疗线数判定不够清晰"
            ]
        }
    },

    "708387": {
        "case_id": "Case9",
        "patient_info": {
            "tumor_type": "肺癌",
            "molecular": "MET扩增",
            "stage": "IV期"
        },
        "real_clinical_path": {
            "admission_dx": "肺恶性肿瘤 T2N0M1 IV期 MET扩增、脑继发恶性肿瘤",
            "discharge_dx": "同上",
            "treatment_course": "2022-1-14行一线第3周期化疗+靶向治疗：贝伐珠单抗+培美曲塞+顺铂。",
            "actual_treatment": "化疗+贝伐珠单抗"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 4.0,
                "treatment_line_reason": "正确判定为一线治疗阶段。",
                "scheme_selection": 3.5,
                "scheme_selection_reason": "报告推荐培美曲塞+铂类+贝伐珠单抗，与真实治疗基本一致。",
                "dosage_params": 3.5,
                "dosage_params_reason": "培美曲塞、顺铂、贝伐珠单抗剂量建议合理。",
                "exclusion_reasoning": 3.5,
                "exclusion_reasoning_reason": "对MET抑制剂、免疫治疗等的排除理由充分。",
                "clinical_path_alignment": 3.5,
                "clinical_path_alignment_reason": "与真实一线化疗路径基本一致。",
                "overall_ccr": 3.6
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 4.0,
                "structured_format": 4.0,
                "citation_format": 4.0,
                "uncertainty_handling": 4.0,
                "overall_mqr": 4.0
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [],
                "cer_score": 0.0
            },
            "ptr": 1.0,
            "cpi": 0.93
        },
        "assessment": {
            "overall": "优秀。报告质量非常高，与真实临床路径高度一致。",
            "strengths": [
                "一线治疗推荐与真实完全一致",
                "MET扩增的分子特征分析准确",
                "化疗方案选择合理",
                "剂量参数准确"
            ],
            "weaknesses": []
        }
    },

    "747724": {
        "case_id": "Case10",
        "patient_info": {
            "tumor_type": "乳腺癌",
            "subtype": "三阳性（HER2+，HR+）",
            "stage": "IV期"
        },
        "real_clinical_path": {
            "admission_dx": "恶性肿瘤维持性化学治疗、三阳性乳腺癌术后、脑继发恶性肿瘤",
            "discharge_dx": "同上",
            "treatment_course": "2023.12.8予第24周期治疗：ZN-A-1041+曲妥珠单抗+卡培他滨。",
            "actual_treatment": "HER2靶向治疗+卡培他滨"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 3.5,
                "treatment_line_reason": "正确识别为多线治疗后复发患者，当前为维持治疗阶段。",
                "scheme_selection": 3.5,
                "scheme_selection_reason": "报告推荐曲妥珠单抗+卡培他滨，与真实治疗一致。",
                "dosage_params": 3.5,
                "dosage_params_reason": "曲妥珠单抗、卡培他滨剂量建议合理。",
                "exclusion_reasoning": 3.5,
                "exclusion_reasoning_reason": "对T-DM1、图卡替尼等替代方案的排除理由充分。",
                "clinical_path_alignment": 3.5,
                "clinical_path_alignment_reason": "与真实维持治疗路径一致。",
                "overall_ccr": 3.5
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 4.0,
                "structured_format": 4.0,
                "citation_format": 4.0,
                "uncertainty_handling": 3.5,
                "overall_mqr": 3.9
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [
                    {
                        "error": "报告中未提及ZN-A-1041（一种新型HER2靶向药），该患者实际正在使用",
                        "impact": "低"
                    }
                ],
                "cer_score": 0.067
            },
            "ptr": 1.0,
            "cpi": 0.88
        },
        "assessment": {
            "overall": "优秀。报告质量高，对HER2+乳腺癌脑转移的处理建议专业。",
            "strengths": [
                "HER2靶向治疗推荐准确",
                "卡培他滨剂量建议合理",
                "对脑转移的局部治疗建议适当"
            ],
            "weaknesses": [
                "未提及患者正在使用的新型药物ZN-A-1041（可能该药物较新，知识库未更新）"
            ]
        }
    },

    "868183": {
        "case_id": "Case3",
        "patient_info": {
            "tumor_type": "肺腺癌",
            "molecular": "驱动基因野生型",
            "stage": "IV期"
        },
        "real_clinical_path": {
            "admission_dx": "右肺恶性肿瘤（肺腺癌IV期，驱动基因野生型）、颅内继发恶性肿瘤",
            "discharge_dx": "恶性肿瘤维持性化学治疗、恶性肿瘤免疫治疗、右肺恶性肿瘤IV期、胸腰髓多发转移",
            "treatment_course": "2025-09-09开始二线第一周期治疗：替雷利珠单抗+贝伐珠单抗+白蛋白紫杉醇+顺铂。",
            "actual_treatment": "二线免疫+化疗+抗血管生成"
        },
        "review_scores": {
            "ccr": {
                "treatment_line": 4.0,
                "treatment_line_reason": "报告正确判定为二线治疗（既往一线治疗进展），与真实临床路径完全一致。",
                "scheme_selection": 4.0,
                "scheme_selection_reason": "报告推荐免疫+化疗+贝伐珠单抗，与真实二线治疗方案高度一致。",
                "dosage_params": 3.5,
                "dosage_params_reason": "替雷利珠单抗、贝伐珠单抗、紫杉醇、顺铂剂量建议合理。",
                "exclusion_reasoning": 4.0,
                "exclusion_reasoning_reason": "对靶向治疗、单纯化疗、单药免疫等的排除理由非常充分。",
                "clinical_path_alignment": 4.0,
                "clinical_path_alignment_reason": "与真实二线治疗路径完全一致，包括脊髓转移的处理。",
                "overall_ccr": 3.9
            },
            "mqr": {
                "module_completeness": 4.0,
                "module_applicability": 4.0,
                "structured_format": 4.0,
                "citation_format": 4.0,
                "uncertainty_handling": 4.0,
                "overall_mqr": 4.0
            },
            "cer": {
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [],
                "cer_score": 0.0
            },
            "ptr": 1.0,
            "cpi": 0.95
        },
        "assessment": {
            "overall": "极优秀。这是质量最高的报告，与真实临床路径几乎完全一致。",
            "strengths": [
                "二线治疗判定完全准确",
                "免疫+化疗+贝伐方案与真实一致",
                "脊髓转移的处理建议专业",
                "排他性论证非常充分",
                "报告结构完整，引用规范"
            ],
            "weaknesses": []
        }
    }
}


def generate_individual_report(patient_id: str, data: dict) -> str:
    """生成单个case的详细审查报告"""
    scores = data["review_scores"]
    ccr = scores["ccr"]
    mqr = scores["mqr"]
    cer = scores["cer"]

    report = f"""# 临床审查报告：患者 {patient_id} ({data['case_id']})

**审查日期**: 2026-03-25
**审查者**: AI模拟临床肿瘤科医生
**肿瘤类型**: {data['patient_info'].get('tumor_type', 'N/A')}

---

## 一、真实临床路径

### 1.1 入院诊断
{data['real_clinical_path']['admission_dx'][:150]}...

### 1.2 出院诊断
{data['real_clinical_path']['discharge_dx'][:150]}...

### 1.3 实际诊疗经过
{data['real_clinical_path']['treatment_course'][:200]}...

### 1.4 实际治疗方案
**{data['real_clinical_path']['actual_treatment']}**

---

## 二、CCR评分（临床一致性）

| 维度 | 得分 | 说明 |
|------|------|------|
| 治疗线判定 | {ccr['treatment_line']}/4 | {ccr['treatment_line_reason'][:80]}... |
| 方案选择 | {ccr['scheme_selection']}/4 | {ccr['scheme_selection_reason'][:80]}... |
| 剂量参数 | {ccr['dosage_params']}/4 | {ccr['dosage_params_reason'][:80]}... |
| 排他性论证 | {ccr['exclusion_reasoning']}/4 | {ccr['exclusion_reasoning_reason'][:80]}... |
| 路径一致性 | {ccr['clinical_path_alignment']}/4 | {ccr['clinical_path_alignment_reason'][:80]}... |
| **CCR总分** | **{ccr['overall_ccr']:.2f}/4** | |

---

## 三、MQR评分（报告质量）

| 维度 | 得分 | 说明 |
|------|------|------|
| 模块完整性 | {mqr['module_completeness']}/4 | 8个模块完整 |
| 模块适用性 | {mqr['module_applicability']}/4 | {mqr.get('module_applicability_reason', 'N/A')[:60]}... |
| 结构化程度 | {mqr['structured_format']}/4 | 格式规范 |
| 引用规范性 | {mqr['citation_format']}/4 | 格式正确 |
| 不确定性处理 | {mqr['uncertainty_handling']}/4 | {mqr.get('uncertainty_reason', 'N/A')[:60]}... |
| **MQR总分** | **{mqr['overall_mqr']:.2f}/4** | |

---

## 四、CER评分（临床错误）

| 错误类型 | 数量 | 说明 |
|----------|------|------|
| 严重错误 | {len(cer['critical_errors'])} | {cer['critical_errors'][0]['error'][:60] + '...' if cer['critical_errors'] else '无'} |
| 主要错误 | {len(cer['major_errors'])} | {cer['major_errors'][0]['error'][:60] + '...' if cer['major_errors'] else '无'} |
| 次要错误 | {len(cer['minor_errors'])} | {cer['minor_errors'][0]['error'][:60] + '...' if cer['minor_errors'] else '无'} |
| **CER** | **{cer['cer_score']:.3f}** | |

---

## 五、其他指标

- **PTR**: {scores['ptr']:.3f}（物理可追溯率）
- **CPI**: {scores['cpi']:.3f}（综合性能指数）

---

## 六、总体评价

### 优势
{chr(10).join(['- ' + s for s in data['assessment']['strengths']])}

### 不足
{chr(10).join(['- ' + s for s in data['assessment']['weaknesses']]) if data['assessment']['weaknesses'] else '- 无明显不足'}

### 综合评价
{data['assessment']['overall']}

---

*审查完成*
"""
    return report


def main():
    """生成所有审查报告"""
    output_dir = Path("analysis/reviews")
    output_dir.mkdir(exist_ok=True)

    # 生成单个报告
    for patient_id, data in CLINICAL_REVIEWS.items():
        report = generate_individual_report(patient_id, data)
        output_file = output_dir / f"Review_{patient_id}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Generated: {output_file}")

    # 生成汇总表
    summary = []
    for patient_id, data in CLINICAL_REVIEWS.items():
        scores = data["review_scores"]
        summary.append({
            "Patient_ID": patient_id,
            "Case_ID": data["case_id"],
            "CCR": round(scores["ccr"]["overall_ccr"], 2),
            "MQR": round(scores["mqr"]["overall_mqr"], 2),
            "CER": round(scores["cer"]["cer_score"], 3),
            "PTR": round(scores["ptr"], 3),
            "CPI": round(scores["cpi"], 3),
            "Overall": data["assessment"]["overall"][:20]
        })

    # 保存汇总
    import pandas as pd
    df = pd.DataFrame(summary)
    df.to_csv(output_dir / "clinical_review_summary.csv", index=False, encoding='utf-8-sig')
    print(f"\nSummary saved: {output_dir}/clinical_review_summary.csv")

    # 打印汇总表
    print("\n" + "="*80)
    print("临床审查评分汇总")
    print("="*80)
    print(df.to_string(index=False))

    # 计算平均分数
    print("\n" + "="*80)
    print("平均分数")
    print("="*80)
    print(f"CCR: {df['CCR'].mean():.2f} ± {df['CCR'].std():.2f}")
    print(f"MQR: {df['MQR'].mean():.2f} ± {df['MQR'].std():.2f}")
    print(f"CER: {df['CER'].mean():.3f} ± {df['CER'].std():.3f}")
    print(f"PTR: {df['PTR'].mean():.3f} ± {df['PTR'].std():.3f}")
    print(f"CPI: {df['CPI'].mean():.3f} ± {df['CPI'].std():.3f}")

    print("\n" + "="*80)
    print("CPI排名（高到低）")
    print("="*80)
    ranked = df.sort_values('CPI', ascending=False)
    for i, row in ranked.iterrows():
        print(f"{row['Patient_ID']:8s} ({row['Case_ID']:6s}): CPI={row['CPI']:.3f}")


if __name__ == "__main__":
    main()
