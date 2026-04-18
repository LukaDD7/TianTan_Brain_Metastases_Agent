#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query script for Drug-Drug Interactions using NLM RxNav API
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Any, List

def check_drug_interaction(drug1: str, drug2: str) -> str:
    """
    使用 NLM RxNav 免费 API 检查药物相互作用
    """
    base_url = "https://rxnav.nlm.nih.gov"
    
    try:
        # Step 1: 查 RxCUI for drug 1
        r1 = requests.get(f"{base_url}/REST/rxcui.json?name={drug1}", timeout=10)
        data1 = r1.json()
        if "idGroup" not in data1 or "rxnormId" not in data1["idGroup"]:
            return f"❌ 无法在 NLM 数据库中找到药物 '{drug1}' 的标准编码。"
        cui1 = data1["idGroup"]["rxnormId"][0]
        
        # Step 2: 查 RxCUI for drug 2
        r2 = requests.get(f"{base_url}/REST/rxcui.json?name={drug2}", timeout=10)
        data2 = r2.json()
        if "idGroup" not in data2 or "rxnormId" not in data2["idGroup"]:
            return f"❌ 无法在 NLM 数据库中找到药物 '{drug2}' 的标准编码。"
        cui2 = data2["idGroup"]["rxnormId"][0]
        
        # Step 3: 查询相互作用
        r3 = requests.get(f"{base_url}/REST/interaction/list.json?rxcuis={cui1}+{cui2}", timeout=10)
        interaction_data = r3.json()
        
        if "fullInteractionTypeGroup" not in interaction_data:
            return f"✅ 在 NLM DrugBank/ONC 数据库中未发现 '{drug1}' 与 '{drug2}' 之间的严重相互作用记录。"
            
        lines = [f"⚠️ 发现 '{drug1}' 与 '{drug2}' 之间的药物相互作用！"]
        lines.append("="*40)
        
        found = False
        for group in interaction_data["fullInteractionTypeGroup"]:
            source = group.get("sourceName", "Unknown Source")
            for interaction_type in group.get("fullInteractionType", []):
                for interaction in interaction_type.get("interactionPair", []):
                    desc = interaction.get("description", "无详细描述")
                    severity = interaction.get("severity", "N/A")
                    lines.append(f"• 来源: {source}")
                    lines.append(f"• 严重级别: {severity}")
                    lines.append(f"• 临床指导: {desc}")
                    lines.append("-" * 20)
                    found = True
                    
        if not found:
            return f"✅ 未发现 '{drug1}' 与 '{drug2}' 之间的临床明显相互作用。"
            
        lines.append("[引用格式]: [NLM RxNav Interaction API: DrugBank/ONC High Priority List]")
        return "\n".join(lines)
        
    except requests.exceptions.RequestException as e:
        return f"❌ NLM API 请求失败 (网络或超时): {str(e)}。由于缺少直接的交互数据，请根据一般 CYP450 规律进行人工风险提示。"

def main():
    parser = argparse.ArgumentParser(description="Check drug interactions via NLM RxNav.")
    parser.add_argument("--drug1", required=True, help="First drug name")
    parser.add_argument("--drug2", required=True, help="Second drug name")
    
    args = parser.parse_args()
    
    result = check_drug_interaction(args.drug1, args.drug2)
    print(result)

if __name__ == "__main__":
    main()
