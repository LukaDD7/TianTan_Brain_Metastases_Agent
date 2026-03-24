#!/usr/bin/env python3
"""
Baseline对比实验学术分析报告生成器
用于论文中的统计分析和图表数据
"""

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

results_dir = Path('baseline/results')
files = [f for f in results_dir.iterdir() if f.suffix == '.json' and not f.name.startswith('evaluation')]

stats = {
    'patients': [],
    'rag_tokens': [],
    'direct_tokens': [],
    'retrieved_docs': [],
    'module_coverage': {'rag': [], 'direct': []},
    'evidence_types': {'rag': [], 'direct': []}
}

def estimate_tokens(text):
    """估算token数量"""
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    punct = len(re.findall(r'[^\w\u4e00-\u9fff\s]', text))
    return int(cn_chars * 1.5 + en_words * 1.3 + punct * 0.5)

def extract_evidence_patterns(text):
    """提取证据类型模式"""
    patterns = {
        'guideline_citation': len(re.findall(r'指南|guideline|NCCN|ASCO|NBO|CSCO', text, re.I)),
        'reference_citation': len(re.findall(r'研究|study|trial|文献|证据', text)),
        'level_evidence': len(re.findall(r'Level [I1-5]|证据等级|推荐等级|Grade', text, re.I)),
        'specific_drug': len(re.findall(r'培美曲塞|顺铂|紫杉醇|贝伐|免疫|靶向|PD-1|EGFR|ALK|替莫唑胺', text)),
        'specific_procedure': len(re.findall(r'SRS|WBRT|伽玛刀|开颅|切除|放疗', text)),
    }
    return patterns

def check_modules(text):
    """检查8模块覆盖情况"""
    modules = {
        '入院评估': ['入院评估', 'Admission', '基本信息', '临床症状'],
        '原发灶': ['原发灶', 'Primary', '病理诊断', '分子分型'],
        '系统性管理': ['系统性管理', 'Systemic', '全身治疗', '化疗', '靶向'],
        '随访': ['随访', 'Follow-up', '复查', '监测'],
        '替代方案': ['替代方案', 'Rejected', '其他方案', '备选'],
        '围手术期': ['围手术期', 'Peri-procedural', '术前', '术后'],
        '分子病理': ['分子病理', 'Molecular', '基因检测', '突变'],
        '执行路径': ['执行路径', 'Trajectory', '时间线', '决策节点']
    }
    coverage = {}
    for module, keywords in modules.items():
        coverage[module] = any(kw in text for kw in keywords)
    return coverage

# 处理每个结果文件
for fname in sorted(files):
    with open(fname, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patient_info = data['patient_info']

    # 患者特征
    age_match = re.search(r'年龄:\s*(\d+)', patient_info)
    gender_match = re.search(r'性别:\s*([男女])', patient_info)

    # 判断原发灶
    primary = 'Other'
    if '黑色素瘤' in patient_info:
        primary = 'Melanoma'
    elif '乳腺癌' in patient_info:
        primary = 'Breast'
    elif any(x in patient_info for x in ['肺癌', '肺腺癌', '肺恶性肿瘤', '肺间质']):
        primary = 'Lung'
    elif '贲门癌' in patient_info:
        primary = 'Gastric'
    elif '结肠癌' in patient_info:
        primary = 'Colorectal'
    elif '甲状腺癌' in patient_info:
        primary = 'Thyroid'

    # MRI报告存在性
    has_mri = False
    if '头部MRI:' in patient_info:
        mri_match = re.search(r'头部MRI:\s*(.+?)(?:\n\n|$)', patient_info, re.DOTALL)
        if mri_match and len(mri_match.group(1).strip()) > 20:
            has_mri = True

    # 胸部CT存在性
    has_ct = False
    if '胸部CT:' in patient_info:
        ct_match = re.search(r'胸部CT:\s*(.+?)(?:\n\n|$)', patient_info, re.DOTALL)
        if ct_match and len(ct_match.group(1).strip()) > 10:
            has_ct = True

    stats['patients'].append({
        'id': data['patient_id'],
        'age': int(age_match.group(1)) if age_match else None,
        'gender': gender_match.group(1) if gender_match else 'Unknown',
        'primary': primary,
        'has_mri': has_mri,
        'has_ct': has_ct
    })

    # Token统计
    rag_report = data['rag_result']['report']
    direct_report = data['direct_result']['report']

    stats['rag_tokens'].append(estimate_tokens(rag_report))
    stats['direct_tokens'].append(estimate_tokens(direct_report))

    # 检索文档
    stats['retrieved_docs'].append(len(data['rag_result'].get('retrieved_docs', [])))

    # 模块覆盖
    stats['module_coverage']['rag'].append(check_modules(rag_report))
    stats['module_coverage']['direct'].append(check_modules(direct_report))

    # 证据类型
    stats['evidence_types']['rag'].append(extract_evidence_patterns(rag_report))
    stats['evidence_types']['direct'].append(extract_evidence_patterns(direct_report))

# ================= 报告输出 =================
print('='*90)
print('Baseline对比实验学术分析报告')
print('='*90)
print()

# 1. 患者队列特征
print('【1. 患者队列特征 (Patient Cohort Characteristics)】')
print('-'*90)
ages = [p['age'] for p in stats['patients'] if p['age']]
genders = [p['gender'] for p in stats['patients']]
primaries = [p['primary'] for p in stats['patients']]
has_mri_count = sum(1 for p in stats['patients'] if p['has_mri'])
has_ct_count = sum(1 for p in stats['patients'] if p['has_ct'])

age_mean = sum(ages)/len(ages)
age_std = ((sum((a-age_mean)**2 for a in ages)/len(ages))**0.5)

print(f"样本量 (Sample Size): n={len(stats['patients'])}")
print(f"年龄 (Age): {min(ages)}–{max(ages)} years, mean±SD={age_mean:.1f}±{age_std:.1f}, median={sorted(ages)[len(ages)//2]} years")
print(f"性别 (Gender): Male={genders.count('男')} ({genders.count('男')/len(genders)*100:.1f}%), Female={genders.count('女')} ({genders.count('女')/len(genders)*100:.1f}%)")
print(f"头部MRI (Brain MRI): {has_mri_count}/{len(stats['patients'])} ({has_mri_count/len(stats['patients'])*100:.0f}%)")
print(f"胸部CT (Chest CT): {has_ct_count}/{len(stats['patients'])} ({has_ct_count/len(stats['patients'])*100:.0f}%)")
print()

print("原发肿瘤分布 (Primary Tumor Distribution):")
primary_counts = Counter(primaries)
for tumor, count in primary_counts.most_common():
    print(f"  • {tumor} Cancer: {count} ({count/len(primaries)*100:.1f}%)")
print()

# 2. Token消耗
print('【2. Token消耗统计 (Token Consumption Analysis)】')
print('-'*90)
rag_mean = sum(stats['rag_tokens'])/len(stats['rag_tokens'])
direct_mean = sum(stats['direct_tokens'])/len(stats['direct_tokens'])
rag_std = (sum((t-rag_mean)**2 for t in stats['rag_tokens'])/len(stats['rag_tokens']))**0.5
direct_std = (sum((t-direct_mean)**2 for t in stats['direct_tokens'])/len(stats['direct_tokens']))**0.5

print(f"RAG Method: {rag_mean:.0f}±{rag_std:.0f} tokens/case, Range=[{min(stats['rag_tokens']):,}, {max(stats['rag_tokens']):,}], Total={sum(stats['rag_tokens']):,}")
print(f"Direct LLM: {direct_mean:.0f}±{direct_std:.0f} tokens/case, Range=[{min(stats['direct_tokens']):,}, {max(stats['direct_tokens']):,}], Total={sum(stats['direct_tokens']):,}")
print(f"Difference: Mean Diff={rag_mean-direct_mean:+.0f} tokens ({(rag_mean/direct_mean-1)*100:+.2f}%)")
print()

# 3. 检索性能
print('【3. 检索性能 (Retrieval Performance)】')
print('-'*90)
avg_retrieved = sum(stats['retrieved_docs'])/len(stats['retrieved_docs'])
print(f"平均检索文档数: {avg_retrieved:.1f} documents/case (Fixed k=3)")
print(f"检索文档数分布: {stats['retrieved_docs']}")

# 计算检索来源分布
print("\n检索来源分布 (RAG Retrieved Sources):")
sources = defaultdict(int)
for fname in sorted(files):
    with open(fname, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for doc in data['rag_result'].get('retrieved_docs', []):
        src = doc.get('source', 'unknown')
        # 简化来源名
        if 'Brain_metastasis' in src:
            sources['Brain Metastasis Review'] += 1
        elif 'Breast_Cancer' in src:
            sources['Breast Cancer BM Review'] += 1
        elif 'ASCO_SNO_ASTRO' in src:
            sources['ASCO/SNO/ASTRO Guideline'] += 1
        else:
            sources[os.path.basename(src)] += 1

for src, count in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  • {src}: {count} retrievals")
print()

# 4. 模块覆盖度
print('【4. 8模块覆盖度 (8-Module Coverage Analysis)】')
print('-'*90)
module_names = ['入院评估', '原发灶', '系统性管理', '随访', '替代方案', '围手术期', '分子病理', '执行路径']

print("模块覆盖情况 (每模块覆盖例数/总例数):")
for module in module_names:
    rag_cov = sum(1 for m in stats['module_coverage']['rag'] if m.get(module, False))
    direct_cov = sum(1 for m in stats['module_coverage']['direct'] if m.get(module, False))
    print(f"  • {module:12s}: RAG={rag_cov}/{len(stats['patients'])} ({rag_cov/len(stats['patients'])*100:.0f}%), Direct={direct_cov}/{len(stats['patients'])} ({direct_cov/len(stats['patients'])*100:.0f}%)")

rag_full = sum(1 for m in stats['module_coverage']['rag'] if all(m.values()))
direct_full = sum(1 for m in stats['module_coverage']['direct'] if all(m.values()))
print(f"\n完整8模块覆盖: RAG={rag_full}/{len(stats['patients'])} ({rag_full/len(stats['patients'])*100:.0f}%), Direct={direct_full}/{len(stats['patients'])} ({direct_full/len(stats['patients'])*100:.0f}%)")
print()

# 5. 证据丰富度
print('【5. 证据丰富度分析 (Evidence Richness Analysis)】')
print('-'*90)
evidence_types = ['guideline_citation', 'reference_citation', 'level_evidence', 'specific_drug', 'specific_procedure']

print("平均每例证据引用数:")
print(f"{'Evidence Type':<30s} {'RAG':>10s} {'Direct':>10s} {'Ratio':>10s}")
print('-'*60)
for ev_type in evidence_types:
    rag_avg = sum(e[ev_type] for e in stats['evidence_types']['rag'])/len(stats['evidence_types']['rag'])
    direct_avg = sum(e[ev_type] for e in stats['evidence_types']['direct'])/len(stats['evidence_types']['direct'])
    ratio = rag_avg/direct_avg if direct_avg > 0 else float('inf')
    print(f"{ev_type:<30s} {rag_avg:>10.1f} {direct_avg:>10.1f} {ratio:>10.2f}x")

print()

# 6. 详细统计表（可用于论文表格）
print('【6. 详细统计表 (Detailed Statistics for Tables)】')
print('-'*90)
print("\nTable 1. Per-Patient Statistics")
print("-"*90)
print(f"{'Patient':<10} {'Age':<5} {'Gender':<8} {'Primary':<15} {'RAG Tokens':<12} {'Direct Tokens':<14} {'Retrieved':<10}")
print("-"*90)

for i, p in enumerate(stats['patients']):
    print(f"{p['id']:<10} {p['age']:<5} {p['gender']:<8} {p['primary']:<15} "
          f"{stats['rag_tokens'][i]:<12,} {stats['direct_tokens'][i]:<14,} {stats['retrieved_docs'][i]:<10}")

print()
print('='*90)
print("Analysis complete. Data ready for paper tables and figures.")
print('='*90)
