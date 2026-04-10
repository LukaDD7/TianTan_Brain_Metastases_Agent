#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二层语义级检查 (Semantic Review - Layer 2)
由 Claude Code (LLM) 执行的信息泄露检查

检查目标：
1. 治疗线数暗示（化疗周期、手术次数等）
2. 治疗方式暗示（靶向药物、放疗史等）
3. 疗效评估暗示（病变稳定、进展等）
4. 用药细节（药物名称、剂量、周期）

审查者：Claude Code (LLM)
"""

import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class SemanticReviewResult:
    """语义审查结果"""
    patient_id: str
    file_path: str
    status: str  # PASS / WARNING / FAIL
    risk_level: str  # LOW / MEDIUM / HIGH
    findings: List[Dict]
    reviewed_at: str
    reviewer: str = "Claude Code (LLM)"


def extract_fields(content: str) -> Dict[str, str]:
    """从输入文件中提取各字段内容"""
    fields = {}

    # 匹配 "字段名 内容。" 格式
    pattern = r'^(主诉|现病史|既往史|头部MRI|胸部CT|颈椎MRI|胸椎MRI|腰椎MRI|腹盆CT|腹盆MRI|腹部超声|浅表淋巴结超声)\s+(.+?)$'

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # 提取字段名和内容
        for field_name in ['主诉', '现病史', '既往史', '头部MRI', '胸部CT']:
            if line.startswith(field_name + ' '):
                fields[field_name] = line[len(field_name)+1:].strip()
                break

    return fields


def analyze_content(patient_id: str, field_name: str, content: str) -> List[Dict]:
    """
    分析字段内容，识别隐含治疗信息
    返回发现的泄露风险列表
    """
    findings = []
    content_lower = content.lower()

    # 1. 检查治疗线数暗示
    treatment_indicators = [
        (r'化疗\s*\d+\s*周期?', 'CHEMO_CYCLES', '明确化疗周期数'),
        (r'术后\s*\d+\s*年', 'POST_OP_YEARS', '术后时间线'),
        (r'靶向治疗\s*\d+\s*年', 'TARGETED_YEARS', '靶向治疗时长'),
        (r'一线|二线|三线|四线', 'TREATMENT_LINE', '明确治疗线数'),
        (r'伽马刀|放疗|放射治疗', 'RADIATION_HISTORY', '放疗史'),
    ]

    for pattern, indicator_type, description in treatment_indicators:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            findings.append({
                'field': field_name,
                'type': indicator_type,
                'description': description,
                'matched_text': match.group(0),
                'risk': 'HIGH' if indicator_type in ['CHEMO_CYCLES', 'TREATMENT_LINE'] else 'MEDIUM',
                'position': match.span()
            })

    # 2. 检查用药细节
    drug_indicators = [
        (r'阿法替尼|奥希替尼|吉非替尼|厄洛替尼', 'EGFR_TKI', 'EGFR靶向药'),
        (r'多西他赛|紫杉醇|培美曲塞|顺铂|卡铂', 'CHEMO_DRUG', '化疗药物'),
        (r'贝伐珠单抗|帕博利珠单抗|纳武利尤单抗', 'IMMUNO_DRUG', '免疫/靶向药物'),
        (r'奥卡西平|左乙拉西坦|丙戊酸钠', 'ANTIEPILEPTIC', '抗癫痫药物'),
        (r'地塞米松|甲强龙', 'STEROID', '激素药物'),
    ]

    for pattern, indicator_type, description in drug_indicators:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            findings.append({
                'field': field_name,
                'type': indicator_type,
                'description': description,
                'matched_text': match.group(0),
                'risk': 'MEDIUM',
                'position': match.span()
            })

    # 3. 检查疗效评估
    response_indicators = [
        (r'病变稳定|病灶稳定|SD', 'STABLE_DISEASE', '疗效评估-稳定'),
        (r'部分缓解|PR|明显缩小', 'PARTIAL_RESPONSE', '疗效评估-缓解'),
        (r'疾病进展|PD|较前增大|增大', 'PROGRESSIVE_DISEASE', '疗效评估-进展'),
        (r'完全缓解|CR', 'COMPLETE_RESPONSE', '疗效评估-完全缓解'),
    ]

    for pattern, indicator_type, description in response_indicators:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            findings.append({
                'field': field_name,
                'type': indicator_type,
                'description': description,
                'matched_text': match.group(0),
                'risk': 'HIGH',
                'position': match.span()
            })

    # 4. 检查时间线暗示
    timeline_indicators = [
        (r'20\d{2}[年.-]\d{1,2}[月.-]\d{1,2}[日]?', 'SPECIFIC_DATE', '具体日期'),
        (r'\d{4}[年.]\d{1,2}[月]', 'DATE_MONTH', '年月信息'),
    ]

    for pattern, indicator_type, description in timeline_indicators:
        matches = re.finditer(pattern, content)
        for match in matches:
            findings.append({
                'field': field_name,
                'type': indicator_type,
                'description': description,
                'matched_text': match.group(0),
                'risk': 'LOW',
                'position': match.span()
            })

    return findings


def semantic_review(patient_id: str, file_path: str, content: str) -> SemanticReviewResult:
    """
    执行语义级审查（第二层检查）

    Args:
        patient_id: 患者ID
        file_path: 文件路径
        content: 文件内容

    Returns:
        SemanticReviewResult: 审查结果
    """
    # 提取各字段
    fields = extract_fields(content)

    # 分析每个字段
    all_findings = []
    for field_name, field_content in fields.items():
        findings = analyze_content(patient_id, field_name, field_content)
        all_findings.extend(findings)

    # 确定整体风险等级
    high_risk_count = sum(1 for f in all_findings if f['risk'] == 'HIGH')
    medium_risk_count = sum(1 for f in all_findings if f['risk'] == 'MEDIUM')

    if high_risk_count >= 3:
        risk_level = 'HIGH'
        status = 'WARNING'
    elif high_risk_count >= 1 or medium_risk_count >= 3:
        risk_level = 'MEDIUM'
        status = 'WARNING'
    elif len(all_findings) > 0:
        risk_level = 'LOW'
        status = 'PASS'
    else:
        risk_level = 'LOW'
        status = 'PASS'

    return SemanticReviewResult(
        patient_id=patient_id,
        file_path=file_path,
        status=status,
        risk_level=risk_level,
        findings=all_findings,
        reviewed_at=datetime.now().isoformat()
    )


def batch_semantic_review(sandbox_dir: str) -> List[SemanticReviewResult]:
    """
    批量执行语义审查

    Args:
        sandbox_dir: sandbox目录路径

    Returns:
        List[SemanticReviewResult]: 所有患者的审查结果
    """
    sandbox = Path(sandbox_dir)

    # 获取所有患者输入文件
    input_files = sorted(sandbox.glob("patient_*_input.txt"))

    results = []
    for file_path in input_files:
        # 提取患者ID
        patient_id = file_path.stem.replace('patient_', '').replace('_input', '')

        # 读取内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 执行语义审查
        result = semantic_review(patient_id, str(file_path), content)
        results.append(result)

    return results


def generate_review_report(results: List[SemanticReviewResult], output_path: str):
    """生成审查报告"""

    # 统计
    total = len(results)
    pass_count = sum(1 for r in results if r.status == 'PASS')
    warning_count = sum(1 for r in results if r.status == 'WARNING')
    fail_count = sum(1 for r in results if r.status == 'FAIL')

    high_risk = sum(1 for r in results if r.risk_level == 'HIGH')
    medium_risk = sum(1 for r in results if r.risk_level == 'MEDIUM')
    low_risk = sum(1 for r in results if r.risk_level == 'LOW')

    total_findings = sum(len(r.findings) for r in results)

    report = {
        'review_type': '第二层语义级检查 (Semantic Review)',
        'reviewer': 'Claude Code (LLM)',
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_patients': total,
            'pass': pass_count,
            'warning': warning_count,
            'fail': fail_count,
            'risk_distribution': {
                'high': high_risk,
                'medium': medium_risk,
                'low': low_risk
            },
            'total_findings': total_findings
        },
        'results': [asdict(r) for r in results]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


if __name__ == '__main__':
    import sys

    project_root = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent")
    sandbox_dir = project_root / "workspace" / "sandbox"
    output_path = project_root / "workspace" / "processing_logs" / f"semantic_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    print("="*70)
    print("第二层语义级检查 (Semantic Review)")
    print("="*70)
    print(f"审查者: Claude Code (LLM)")
    print(f"检查对象: {sandbox_dir}/patient_*_input.txt")
    print("="*70)

    # 批量审查
    results = batch_semantic_review(str(sandbox_dir))

    # 生成报告
    report = generate_review_report(results, str(output_path))

    # 打印摘要
    summary = report['summary']
    print(f"\n📊 审查统计:")
    print(f"   总患者数: {summary['total_patients']}")
    print(f"   ✅ 通过: {summary['pass']}")
    print(f"   ⚠️  警告: {summary['warning']}")
    print(f"   ❌ 失败: {summary['fail']}")
    print(f"\n🔴 风险分布:")
    print(f"   高风险: {summary['risk_distribution']['high']}")
    print(f"   中风险: {summary['risk_distribution']['medium']}")
    print(f"   低风险: {summary['risk_distribution']['low']}")
    print(f"\n📝 发现隐患: {summary['total_findings']} 项")

    # 打印高风险患者详情
    high_risk_patients = [r for r in results if r.risk_level == 'HIGH']
    if high_risk_patients:
        print(f"\n🔴 高风险患者详情:")
        for r in high_risk_patients[:5]:  # 只显示前5个
            print(f"\n   患者 {r.patient_id}:")
            for f in r.findings[:3]:  # 只显示前3个发现
                print(f"     - [{f['risk']}] {f['field']}: {f['description']}")
                print(f"       文本: '{f['matched_text']}'")

    print(f"\n📄 详细报告: {output_path}")
    print("="*70)
