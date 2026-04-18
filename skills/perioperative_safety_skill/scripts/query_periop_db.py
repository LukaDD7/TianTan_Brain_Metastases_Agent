#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query script for Perioperative Drug Holding Windows
"""

import os
import json
import argparse
from typing import Dict, Any

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'perioperative_holding_db.json')

def load_db() -> dict:
    if not os.path.exists(db_path):
        return {}
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def query_drug(drug_name: str) -> str:
    db = load_db()
    
    drug_key = drug_name.lower().strip()
    # 模糊匹配
    match_key = None
    for k in db.keys():
        if drug_key in k or k in drug_key:
            match_key = k
            break
            
    if not match_key:
        return f"未找到药物 '{drug_name}' 的围手术期管理数据。如果是常见靶向药，请按照半衰期的大约 4-5 倍时间估算停药窗口（需在报告中标注 [需专家复核]）。"
        
    data = db[match_key]
    
    lines = []
    lines.append(f"【围手术期管理档案】: {match_key.capitalize()}")
    lines.append(f"• 药物类别: {data.get('drug_class')}")
    if 'half_life_days' in data:
        lines.append(f"• 半衰期 (T1/2): {data.get('half_life_days')} 天")
        
    lines.append(f"\n[术前停药指导]")
    lines.append(f"• 推荐术前停药: {data.get('hold_before_surgery_days')} 天")
    if 'hold_before_surgery_note' in data:
        lines.append(f"• 详细说明: {data.get('hold_before_surgery_note')}")
    if 'risk_if_not_held' in data:
        lines.append(f"• 未停药风险 (Safety Risk): {data.get('risk_if_not_held')}")
        
    lines.append(f"\n[术后恢复指导]")
    lines.append(f"• 术后恢复时间: {data.get('resume_after_surgery_days')} 天")
    if 'resume_condition' in data:
        lines.append(f"• 恢复条件: {data.get('resume_condition')}")
        
    lines.append(f"\n[证据基础]")
    lines.append(f"• 证据来源: {data.get('source')} ({data.get('evidence_level')})")
    pmids = data.get('pmid_evidence', [])
    if pmids:
        pmid_str = ", ".join([f"PMID {p}" for p in pmids])
        lines.append(f"• 文献支持: [PubMed: {pmid_str}]")
        
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Query perioperative holding window for a drug.")
    parser.add_argument("--drug", required=True, help="Drug name (e.g., bevacizumab, osimertinib)")
    parser.add_argument("--surgery_type", help="Optional surgery type", default="craniotomy")
    
    args = parser.parse_args()
    
    result = query_drug(args.drug)
    print(result)

if __name__ == "__main__":
    main()
