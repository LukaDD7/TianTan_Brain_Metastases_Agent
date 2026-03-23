#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
batch_parse_guidelines.py - 批量解析临床指南 PDF

功能:
1. 自动为每个 PDF 创建独立子目录
2. 支持 GPU 选择 (CUDA_VISIBLE_DEVICES)
3. 批量处理所有指南文件
4. 生成图片-页码映射文件

输出结构:
workspace/sandbox/
├── NCCN_CNS/
│   ├── NCCN_CNS.md
│   ├── NCCN_CNS_image_page_map.json
│   └── images/
│       └── xxx.jpg
├── ASCO_SNO_ASTRO_Brain_Metastases/
│   ├── ASCO_SNO_ASTRO_Brain_Metastases.md
│   ├── ASCO_SNO_ASTRO_Brain_Metastases_image_page_map.json
│   └── images/
│       └── xxx.jpg
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed

# 指南文件列表 (相对于 Guidelines/ 目录)
DEFAULT_GUIDELINES = [
    "NCCN_CNS.pdf",
    "ASCO_SNO_ASTRO_Brain_Metastases.pdf",
]


def parse_single_pdf(
    pdf_path: str,
    output_base_dir: str,
    gpu_id: int = None,
    parse_method: str = "auto",
    lang: str = "en"
) -> Dict[str, Any]:
    """
    解析单个 PDF 文件到独立子目录

    Args:
        pdf_path: PDF 文件路径
        output_base_dir: 输出基础目录 (sandbox)
        gpu_id: 指定 GPU ID (None 表示使用 CPU)
        parse_method: 解析方法 (auto/ocr/txt)
        lang: OCR 语言

    Returns:
        解析结果字典
    """
    pdf_name = Path(pdf_path).stem

    # 创建子目录: sandbox/{pdf_name}/
    output_dir = os.path.join(output_base_dir, pdf_name)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

    # 构建命令
    script_path = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/skills/pdf-inspector/scripts/parse_pdf_to_md.py"
    python_path = "/home/luzhenyang/anaconda3/envs/mineru_env/bin/python"

    cmd = [
        python_path,
        script_path,
        pdf_path,
        "-o", output_dir,
        "--method", parse_method,
        "--lang", lang,
        "--debug"  # 保留中间文件以便调试
    ]

    # 设置环境变量
    env = os.environ.copy()
    if gpu_id is not None:
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        env["VIRTUAL_VRAM_SIZE"] = "0"  # 强制使用实际 GPU
    else:
        env["VIRTUAL_VRAM_SIZE"] = "0"  # CPU 模式

    print(f"\n{'='*60}")
    print(f"解析: {pdf_name}")
    print(f"输出: {output_dir}")
    if gpu_id is not None:
        print(f"GPU: {gpu_id}")
    else:
        print(f"GPU: CPU 模式")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800  # 30 分钟超时
        )

        if result.returncode == 0:
            print(f"✅ {pdf_name} 解析成功")
            return {
                "pdf_name": pdf_name,
                "status": "success",
                "output_dir": output_dir,
                "stdout": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout  # 最后 500 字符
            }
        else:
            print(f"❌ {pdf_name} 解析失败")
            return {
                "pdf_name": pdf_name,
                "status": "error",
                "output_dir": output_dir,
                "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
            }

    except subprocess.TimeoutExpired:
        return {
            "pdf_name": pdf_name,
            "status": "timeout",
            "output_dir": output_dir,
            "error": "解析超时 (>30分钟)"
        }
    except Exception as e:
        return {
            "pdf_name": pdf_name,
            "status": "error",
            "output_dir": output_dir,
            "error": str(e)
        }


def get_available_gpus() -> List[int]:
    """获取可用的 GPU 列表"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.free",
             "--format=csv,noheader"],
            capture_output=True,
            text=True
        )
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(',')
                idx = int(parts[0].strip())
                util = int(parts[1].strip().replace(' %', ''))
                mem_free = parts[2].strip()
                # 选择空闲 GPU (利用率 < 50%)
                if util < 50:
                    gpus.append(idx)
        return gpus
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="批量解析临床指南 PDF")
    parser.add_argument(
        "--guidelines-dir",
        default="/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/Guidelines",
        help="指南 PDF 所在目录"
    )
    parser.add_argument(
        "--output-dir",
        default="/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox",
        help="输出基础目录"
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=None,
        help="指定 GPU ID (默认自动选择空闲 GPU)"
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="强制使用 CPU 模式"
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="指定要解析的 PDF 文件名 (如 NCCN_CNS.pdf)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="并行解析多个 PDF (每个 PDF 使用一个 GPU)"
    )

    args = parser.parse_args()

    # 确定要解析的文件列表
    if args.files:
        pdf_files = [os.path.join(args.guidelines_dir, f) for f in args.files]
    else:
        pdf_files = [os.path.join(args.guidelines_dir, f) for f in DEFAULT_GUIDELINES]

    # 过滤存在的文件
    pdf_files = [f for f in pdf_files if os.path.exists(f)]

    if not pdf_files:
        print("❌ 没有找到要解析的 PDF 文件")
        sys.exit(1)

    print(f"📋 将要解析 {len(pdf_files)} 个 PDF 文件:")
    for f in pdf_files:
        print(f"   - {Path(f).name}")

    # 确定 GPU 使用策略
    if args.cpu:
        gpu_strategy = "cpu"
        print("\n🖥️  使用 CPU 模式")
    elif args.gpu is not None:
        gpu_strategy = "single"
        selected_gpu = args.gpu
        print(f"\n🎮 使用指定 GPU: {selected_gpu}")
    else:
        available_gpus = get_available_gpus()
        if available_gpus:
            gpu_strategy = "auto"
            selected_gpu = available_gpus[0]
            print(f"\n🎮 自动选择空闲 GPU: {selected_gpu} (可用: {available_gpus})")
        else:
            gpu_strategy = "cpu"
            print("\n🖥️  没有可用 GPU，使用 CPU 模式")

    # 执行解析
    results = []

    if args.parallel and len(pdf_files) > 1:
        # 并行模式 (每个 PDF 使用一个 GPU)
        available_gpus = get_available_gpus()
        if not available_gpus:
            print("⚠️  没有可用 GPU，无法并行处理")
            available_gpus = [None]

        with ProcessPoolExecutor(max_workers=min(len(pdf_files), len(available_gpus))) as executor:
            futures = {}
            for i, pdf_file in enumerate(pdf_files):
                gpu_id = available_gpus[i % len(available_gpus)]
                future = executor.submit(
                    parse_single_pdf,
                    pdf_file,
                    args.output_dir,
                    gpu_id,
                    "auto",
                    "en"
                )
                futures[future] = pdf_file

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
    else:
        # 串行模式
        for pdf_file in pdf_files:
            gpu_id = None if gpu_strategy == "cpu" else selected_gpu
            result = parse_single_pdf(
                pdf_file,
                args.output_dir,
                gpu_id,
                "auto",
                "en"
            )
            results.append(result)

    # 打印汇总
    print(f"\n{'='*60}")
    print("📊 解析结果汇总")
    print(f"{'='*60}")

    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] != "success")

    for r in results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        print(f"{status_icon} {r['pdf_name']}: {r['status']}")
        if r["status"] == "success":
            print(f"   输出: {r['output_dir']}")
        else:
            print(f"   错误: {r.get('error', r.get('stderr', '未知错误'))}")

    print(f"\n总计: {len(results)} 个文件")
    print(f"成功: {success_count}")
    print(f"失败: {error_count}")

    # 返回状态码
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
