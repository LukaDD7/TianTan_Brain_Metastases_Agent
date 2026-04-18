#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query script for CNS Penetration Data
"""

import os
import json
import argparse

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cns_penetration_db.json')

def load_db() -> dict:
    if not os.path.exists(db_path):
        return {}
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def query_drug(drug_name: str) -> str:
    db = load_db()
    
    drug_key = drug_name.lower().strip()
    match_key = None
    for k in db.keys():
        if drug_key in k.replace("_", "") or k.replace("_", "") in drug_key:
            match_key = k
            break
            
    if not match_key:
        return f"未找到药物 '{drug_name}' 的 CNS 穿透性数据。建议回退使用 search_pubmed 工具查询：search_pubmed --query \"{drug_name} brain metastases CNS penetration\""
        
    data = db[match_key]
    
    lines = []
    lines.append(f"【CNS 穿透性档案】: {match_key.capitalize()}")
    lines.append(f"• 药物类别: {data.get('drug_class')}")
    
    if 'csf_plasma_ratio' in data:
        lines.append(f"• CSF/血浆浓度比: {data.get('csf_plasma_ratio')}" + 
                     (f" (范围: {data.get('csf_plasma_ratio_range')})" if 'csf_plasma_ratio_range' in data else ""))
    
    if 'csf_penetration' in data:
        lines.append(f"• 穿透性评级: {data.get('csf_penetration')}")
        
    if 'cns_orr_percent' in data:
        lines.append(f"• 颅内客观缓解率 (CNS ORR): {data.get('cns_orr_percent')}%")

    if 'cns_pfs_improvement' in data:
        lines.append(f"• CNS PFS 获益: {data.get('cns_pfs_improvement')}")
        
    if 'note' in data:
        lines.append(f"• 临床要点: {data.get('note')}")
        
    if 'mechanism' in data:
        lines.append(f"• 穿透机制: {data.get('mechanism')}")

    lines.append(f"\n[证据基础]")
    if 'key_study' in data:
        lines.append(f"• 关键研究: {data.get('key_study')}")
    
    lines.append(f"• 证据层级: {data.get('evidence_level')}")
    
    pmids = data.get('pmid', [])
    if pmids:
        pmid_str = ", ".join([f"PMID {p}" for p in pmids])
        lines.append(f"• 文献支持: [PubMed: {pmid_str}]")
        
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Query CNS penetration data for a drug.")
    parser.add_argument("--drug", required=True, help="Drug name (e.g., osimertinib)")
    
    args = parser.parse_args()
    
    result = query_drug(args.drug)
    print(result)

if __name__ == "__main__":
    main()
