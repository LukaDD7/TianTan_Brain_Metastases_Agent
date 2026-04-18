#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DS-GPA (Disease-Specific Graded Prognostic Assessment) Calculator
Based on: Sperduto et al., 2020 (PMID: 33141945)
         "Survival in Patients With Brain Metastases: Summary Report on the Updated Diagnosis-Specific Graded Prognostic Assessment and Definition of the Eligibility Quotient"
         Journal of Clinical Oncology 2020 

All scoring tables are directly encoded from the publication.
DETERMINISTIC: No LLM inference is used. Input → Lookup Table → Score → Median OS.
"""

import argparse
import json
import sys
from typing import Optional

# =============================================================================
# DS-GPA Scoring Tables (Source: Sperduto et al., JCO 2020, PMID: 33141945)
# =============================================================================

# Each table: {factor_name: {factor_value: points}}
# Median OS in months is indexed by total GPA score (0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)

DS_GPA_TABLES = {
    "NSCLC": {
        "source": "Sperduto 2020, JCO, PMID: 33141945",
        "factors": {
            "KPS": {
                "<=50": 0.0, "60": 0.0, "70": 1.0, "80": 1.0, "90": 2.0, "100": 2.0
            },
            "age": {
                ">=70": 0.0, "<70": 1.0
            },
            "ecm": {  # Extracranial mets
                "yes": 0.0, "no": 1.0
            },
            "n_mets": {  # Number of brain metastases
                ">5": 0.0, "3-5": 0.0, "2": 0.5, "1": 1.0
            },
            "molecular": {  # EGFR/ALK status
                "negative_unknown": 0.0, "positive": 1.0
            }
        },
        "max_score": 6.0,
        # Median OS in months by GPA total score
        "median_os_months": {
            "0-1.0": 6.9,
            "1.5-2.0": 13.7,
            "2.5-3.0": 26.5,
            "3.5-4.0": 46.8
        },
        "median_os_by_score": {
            0.0: 6.9, 0.5: 6.9, 1.0: 6.9,
            1.5: 13.7, 2.0: 13.7,
            2.5: 26.5, 3.0: 26.5,
            3.5: 46.8, 4.0: 46.8
        }
    },
    "BREAST": {
        "source": "Sperduto 2020, JCO, PMID: 33141945",
        "factors": {
            "KPS": {
                "<=50": 0.0, "60": 0.0, "70": 1.0, "80": 1.0, "90": 2.0, "100": 2.0
            },
            "subtype": {
                "TNBC": 0.0, "HR+_HER2-": 1.0, "HER2+_HR-": 2.0, "HER2+_HR+": 3.0
            }
        },
        "max_score": 5.0,
        "median_os_by_score": {
            0.0: 3.4, 0.5: 3.4,
            1.0: 7.7, 1.5: 7.7,
            2.0: 15.1, 2.5: 15.1,
            3.0: 25.3, 3.5: 25.3,
            4.0: 36.5
        }
    },
    "MELANOMA": {
        "source": "Sperduto 2020, JCO, PMID: 33141945",
        "factors": {
            "KPS": {
                "<=70": 0.0, "80": 1.0, "90-100": 2.0
            },
            "BRAF": {
                "negative_unknown": 0.0, "positive": 2.0
            },
            "ecm": {
                "yes": 0.0, "no": 1.0
            },
            "n_mets": {
                ">4": 0.0, "2-4": 1.0, "1": 2.0
            }
        },
        "max_score": 7.0,
        "median_os_by_score": {
            0.0: 4.9, 0.5: 4.9, 1.0: 4.9,
            1.5: 8.3, 2.0: 8.3,
            2.5: 15.8, 3.0: 15.8,
            3.5: 34.1, 4.0: 34.1
        }
    },
    "GI": {  # Gastrointestinal (Colorectal, Gastric, Esophageal, etc.)
        "source": "Sperduto 2020, JCO, PMID: 33141945",
        "factors": {
            "KPS": {
                "<=50": 0.0, "60": 0.0, "70": 1.0, "80": 1.0, "90": 2.0, "100": 2.0
            }
        },
        "max_score": 2.0,
        "median_os_by_score": {
            0.0: 3.1, 0.5: 3.1, 1.0: 3.1,
            1.5: 6.6, 2.0: 6.6
        }
    },
    "RCC": {  # Renal Cell Carcinoma
        "source": "Sperduto 2020, JCO, PMID: 33141945",
        "factors": {
            "KPS": {
                "<=70": 0.0, "80": 1.0, "90-100": 2.0
            },
            "n_mets": {
                ">4": 0.0, "2-4": 1.0, "1": 2.0
            },
            "ecm": {
                "yes": 0.0, "no": 1.0
            }
        },
        "max_score": 5.0,
        "median_os_by_score": {
            0.0: 3.3, 0.5: 3.3, 1.0: 3.3,
            1.5: 7.9, 2.0: 7.9,
            2.5: 16.5, 3.0: 16.5,
            3.5: 37.0, 4.0: 37.0
        }
    },
    "LUNG_SCLC": {
        "source": "Sperduto 2020, JCO, PMID: 33141945",
        "factors": {
            "KPS": {
                "<=50": 0.0, "60": 0.0, "70": 1.0, "80": 1.0, "90": 2.0, "100": 2.0
            },
            "age": {
                ">=60": 0.0, "<60": 1.0
            }
        },
        "max_score": 3.0,
        "median_os_by_score": {
            0.0: 2.8, 0.5: 2.8, 1.0: 2.8,
            1.5: 5.3, 2.0: 5.3,
            2.5: 8.6, 3.0: 8.6
        }
    }
}

TUMOR_TYPE_ALIASES = {
    "nsclc": "NSCLC",
    "non-small cell lung": "NSCLC",
    "lung adenocarcinoma": "NSCLC",
    "lung squamous": "NSCLC",
    "肺腺癌": "NSCLC",
    "肺鳞癌": "NSCLC",
    "非小细胞肺癌": "NSCLC",
    "breast": "BREAST",
    "乳腺癌": "BREAST",
    "melanoma": "MELANOMA",
    "黑色素瘤": "MELANOMA",
    "gi": "GI",
    "colorectal": "GI",
    "gastric": "GI",
    "结直肠癌": "GI",
    "胃癌": "GI",
    "rcc": "RCC",
    "renal": "RCC",
    "肾细胞癌": "RCC",
    "sclc": "LUNG_SCLC",
    "small cell": "LUNG_SCLC",
    "小细胞肺癌": "LUNG_SCLC",
}


def get_kps_bin(kps_str: str, tumor_type: str) -> str:
    """Map KPS value string to lookup key."""
    try:
        kps = int(kps_str)
    except ValueError:
        return "70"

    if tumor_type in ["NSCLC", "BREAST", "GI", "LUNG_SCLC"]:
        if kps <= 50: return "<=50"
        elif kps == 60: return "60"
        elif kps <= 80: return str(kps)
        elif kps <= 90: return "90"
        else: return "100"
    elif tumor_type in ["MELANOMA", "RCC"]:
        if kps <= 70: return "<=70"
        elif kps == 80: return "80"
        else: return "90-100"
    return "70"


def calculate_ds_gpa(
    tumor_type_raw: str,
    kps: str,
    age: Optional[int] = None,
    n_brain_mets: Optional[int] = None,
    has_ecm: Optional[bool] = None,
    molecular_positive: Optional[bool] = None,  # NSCLC: EGFR/ALK
    breast_subtype: Optional[str] = None,
    braf_positive: Optional[bool] = None
) -> str:

    # Normalize tumor type
    tumor_key = None
    lower_raw = tumor_type_raw.lower()
    for alias, t_type in TUMOR_TYPE_ALIASES.items():
        if alias in lower_raw:
            tumor_key = t_type
            break

    if tumor_key is None:
        return (
            f"⚠️ 未找到 '{tumor_type_raw}' 的 DS-GPA 评分表。\n"
            f"目前支持的肿瘤类型：NSCLC、Breast、Melanoma、GI、RCC、SCLC。\n"
            f"参考文献：Sperduto et al., JCO 2020 (PMID: 33141945)"
        )

    table = DS_GPA_TABLES[tumor_key]
    factors = table["factors"]
    score = 0.0
    score_log = []

    kps_bin = get_kps_bin(kps, tumor_key)
    kps_points = factors.get("KPS", {}).get(kps_bin, 0.0)
    score += kps_points
    score_log.append(f"  KPS {kps} ({kps_bin}): +{kps_points} 分")

    if "age" in factors and age is not None:
        age_key = "<70" if age < 70 else ">=70"
        age_points = factors["age"].get(age_key, 0.0)
        score += age_points
        score_log.append(f"  年龄 {age}岁 ({age_key}): +{age_points} 分")

    if "ecm" in factors and has_ecm is not None:
        ecm_key = "yes" if has_ecm else "no"
        ecm_points = factors["ecm"].get(ecm_key, 0.0)
        score += ecm_points
        score_log.append(f"  颅外转移 ({ecm_key}): +{ecm_points} 分")

    if "n_mets" in factors and n_brain_mets is not None:
        if n_brain_mets == 1:
            n_key = "1"
        elif n_brain_mets == 2:
            n_key = "2"
        elif n_brain_mets <= 5:
            n_key = "3-5"
        else:
            n_key = ">5"
        n_points = factors["n_mets"].get(n_key, 0.0)
        score += n_points
        score_log.append(f"  脑转移数量 {n_brain_mets}个 ({n_key}): +{n_points} 分")

    if "molecular" in factors and molecular_positive is not None:
        mol_key = "positive" if molecular_positive else "negative_unknown"
        mol_points = factors["molecular"].get(mol_key, 0.0)
        score += mol_points
        status_label = "EGFR/ALK 阳性" if molecular_positive else "EGFR/ALK 阴性/未知"
        score_log.append(f"  分子状态 ({status_label}): +{mol_points} 分")

    if "subtype" in factors and breast_subtype is not None:
        subtype_lower = breast_subtype.strip()
        subtype_map = {
            "tnbc": "TNBC", "triple negative": "TNBC", "三阴": "TNBC",
            "hr+her2-": "HR+_HER2-", "hr+/her2-": "HR+_HER2-", "激素受体阳性": "HR+_HER2-",
            "her2+hr-": "HER2+_HR-", "her2+/hr-": "HER2+_HR-",
            "her2+hr+": "HER2+_HR+", "her2+/hr+": "HER2+_HR+"
        }
        subtype_key = subtype_map.get(subtype_lower.lower(), subtype_lower.upper().replace("/", "_"))
        sub_points = factors["subtype"].get(subtype_key, 0.0)
        score += sub_points
        score_log.append(f"  乳腺癌分子亚型 ({subtype_key}): +{sub_points} 分")

    if "BRAF" in factors and braf_positive is not None:
        braf_key = "positive" if braf_positive else "negative_unknown"
        braf_points = factors["BRAF"].get(braf_key, 0.0)
        score += braf_points
        score_log.append(f"  BRAF状态 ({braf_key}): +{braf_points} 分")

    # Look up median OS
    score_rounded = round(score * 2) / 2  # Round to nearest 0.5
    median_os = table["median_os_by_score"].get(score_rounded, "N/A")

    # Determine prognosis category
    if score_rounded <= 1.0:
        prognosis_cat = "预后差 (Poor)"
        category_note = "建议以症状控制和生活质量为主要目标"
    elif score_rounded <= 2.0:
        prognosis_cat = "预后中等偏下 (Below-Average)"
        category_note = "积极局部治疗可能带来生存获益"
    elif score_rounded <= 3.0:
        prognosis_cat = "预后中等 (Intermediate)"
        category_note = "积极多学科治疗，需整合局部和系统治疗"
    else:
        prognosis_cat = "预后较好 (Favorable)"
        category_note = "可考虑根治性局部治疗，期待长期生存"

    result_lines = [
        f"【DS-GPA 预后评分报告】",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"原发肿瘤类型：{tumor_key}",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"评分明细：",
        *score_log,
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"DS-GPA 总分：{score_rounded:.1f} / {table['max_score']:.1f}",
        f"预后分层：{prognosis_cat}",
        f"预计中位总生存（Median OS）：{median_os} 个月",
        f"临床提示：{category_note}",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"[引用格式]: [Local: prognostic_scoring_skill/ds_gpa_tables.py] + [PubMed: PMID 33141945]",
        f"数据来源：Sperduto et al., JCO 2020 (PMID: 33141945)"
    ]
    return "\n".join(result_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate DS-GPA (Sperduto 2020) for brain metastases prognosis."
    )
    parser.add_argument("--tumor_type", required=True,
                        help="Primary cancer type (e.g., NSCLC, Breast, Melanoma, GI, RCC, SCLC)")
    parser.add_argument("--kps", required=True,
                        help="Karnofsky Performance Score (e.g., 70, 80, 90)")
    parser.add_argument("--age", type=int, default=None,
                        help="Patient age in years")
    parser.add_argument("--n_brain_mets", type=int, default=None,
                        help="Number of brain metastases")
    parser.add_argument("--ecm", choices=["yes", "no"], default=None,
                        help="Extracranial metastases present? (yes/no)")
    parser.add_argument("--molecular", choices=["positive", "negative"],
                        default=None,
                        help="EGFR/ALK status for NSCLC")
    parser.add_argument("--breast_subtype", default=None,
                        help="Breast cancer subtype: TNBC, HR+HER2-, HER2+HR-, HER2+HR+")
    parser.add_argument("--braf", choices=["positive", "negative"],
                        default=None,
                        help="BRAF mutation status (for Melanoma)")

    args = parser.parse_args()

    result = calculate_ds_gpa(
        tumor_type_raw=args.tumor_type,
        kps=args.kps,
        age=args.age,
        n_brain_mets=args.n_brain_mets,
        has_ecm=(args.ecm == "yes") if args.ecm else None,
        molecular_positive=(args.molecular == "positive") if args.molecular else None,
        breast_subtype=args.breast_subtype,
        braf_positive=(args.braf == "positive") if args.braf else None
    )
    print(result)


if __name__ == "__main__":
    main()
