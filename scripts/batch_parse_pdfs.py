#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量解析PDF综述文件
使用多GPU并行处理
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# 配置
PDF_DIR = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/Guidelines/脑转诊疗指南/Review_metastases"
OUTPUT_BASE = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/Guidelines"
MINERU_PYTHON = "/home/luzhenyang/anaconda3/envs/mineru_env/bin/python"
PARSE_SCRIPT = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pdf-inspector/scripts/parse_pdf_to_md.py"

# GPU分配
GPU_MAP = {
    0: [2],  # GPU 2处理第1-6个
    1: [4],  # GPU 4处理第7-12个
}

def get_pdf_list():
    """获取所有PDF文件列表"""
    pdf_dir = Path(PDF_DIR)
    pdfs = sorted([f for f in pdf_dir.glob("*.pdf")])
    return pdfs

def parse_single_pdf(args):
    """解析单个PDF"""
    pdf_path, gpu_id = args
    pdf_name = pdf_path.stem
    
    print(f"[GPU {gpu_id}] 开始解析: {pdf_name}")
    
    # 检查是否已存在
    target_dir = Path(OUTPUT_BASE) / pdf_name
    target_md = target_dir / f"{pdf_name}.md"
    
    if target_md.exists():
        print(f"[GPU {gpu_id}] ⚠️ 已存在，跳过: {pdf_name}")
        return {"pdf": pdf_name, "status": "skipped", "gpu": gpu_id}
    
    try:
        # 设置环境变量指定GPU
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        
        # 执行解析
        cmd = [
            MINERU_PYTHON,
            PARSE_SCRIPT,
            str(pdf_path),
            "-o", OUTPUT_BASE
        ]
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode != 0:
            print(f"[GPU {gpu_id}] ❌ 解析失败: {pdf_name}")
            print(f"Error: {result.stderr[:500]}")
            return {"pdf": pdf_name, "status": "error", "gpu": gpu_id, "error": result.stderr[:500]}
        
        print(f"[GPU {gpu_id}] ✅ 解析完成: {pdf_name}")
        return {"pdf": pdf_name, "status": "success", "gpu": gpu_id}
        
    except subprocess.TimeoutExpired:
        print(f"[GPU {gpu_id}] ⏱️ 超时: {pdf_name}")
        return {"pdf": pdf_name, "status": "timeout", "gpu": gpu_id}
    except Exception as e:
        print(f"[GPU {gpu_id}] ❌ 异常: {pdf_name} - {e}")
        return {"pdf": pdf_name, "status": "error", "gpu": gpu_id, "error": str(e)}

def main():
    print("="*60)
    print("🚀 批量解析PDF综述文件")
    print("="*60)
    
    # 获取PDF列表
    pdfs = get_pdf_list()
    print(f"\n📚 发现 {len(pdfs)} 个PDF文件:")
    for i, pdf in enumerate(pdfs, 1):
        print(f"  {i}. {pdf.name}")
    
    # 分配任务到GPU
    tasks = []
    mid = len(pdfs) // 2
    
    # GPU 2处理前半部分
    for pdf in pdfs[:mid]:
        tasks.append((pdf, 2))
    
    # GPU 4处理后半部分  
    for pdf in pdfs[mid:]:
        tasks.append((pdf, 4))
    
    print(f"\n🎮 GPU分配:")
    print(f"  - GPU 2: {mid} 个文件")
    print(f"  - GPU 4: {len(pdfs) - mid} 个文件")
    print(f"\n📂 输出目录: {OUTPUT_BASE}")
    print("-"*60)
    
    # 并行执行
    results = []
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(parse_single_pdf, task): task for task in tasks}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 解析完成汇总")
    print("="*60)
    
    success = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] in ["error", "timeout"]]
    
    print(f"✅ 成功: {len(success)}")
    print(f"⏭️  跳过(已存在): {len(skipped)}")
    print(f"❌ 失败: {len(errors)}")
    
    if errors:
        print("\n❌ 失败的文件:")
        for e in errors:
            print(f"  - {e['pdf']}: {e.get('error', 'Unknown error')}")
    
    # 保存结果报告
    report_path = Path(OUTPUT_BASE) / "_batch_parse_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total": len(pdfs),
            "success": len(success),
            "skipped": len(skipped),
            "errors": len(errors),
            "details": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 详细报告已保存: {report_path}")

if __name__ == "__main__":
    main()
