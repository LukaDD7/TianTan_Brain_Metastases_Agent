#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
整理解析后的PDF文件到标准目录结构
简化版：只移动Markdown和JSON文件，图片保持在images目录
"""

import os
import shutil
from pathlib import Path
import json

BASE_DIR = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/Guidelines"

def organize_files():
    """将平铺的文件整理到子目录"""
    base = Path(BASE_DIR)
    
    # 找到所有.md文件（不在子目录中的）
    md_files = [f for f in base.glob("*.md") if f.parent == base]
    
    print(f"找到 {len(md_files)} 个需要整理的Markdown文件\n")
    
    for md_file in md_files:
        # 获取文件名（不含扩展名）
        name = md_file.stem
        target_dir = base / name
        
        print(f"📁 处理: {name}")
        
        # 创建目标目录
        target_dir.mkdir(exist_ok=True)
        
        # 移动相关文件
        related_files = [
            md_file,  # .md文件
            base / f"{name}_raw.json",  # raw.json
            base / f"{name}_image_page_map.json",  # image_page_map.json
        ]
        
        for file in related_files:
            if file.exists():
                dest = target_dir / file.name
                if not dest.exists():
                    shutil.move(str(file), str(dest))
                    print(f"   ✓ 移动: {file.name}")
                else:
                    print(f"   ⏭️  已存在: {file.name}")
        
        # 为每个文档创建images目录的符号链接（可选）
        # 实际图片保持在Guidelines/images/目录，通过image_page_map.json引用
    
    print("\n✅ 文件整理完成！")
    
    # 统计
    print("\n📂 指南目录统计:")
    total_dirs = 0
    total_md = 0
    for item in sorted(base.iterdir()):
        if item.is_dir() and not item.name.startswith('.') and not item.name == 'images':
            md_files = list(item.glob("*.md"))
            if md_files:
                total_dirs += 1
                total_md += len(md_files)
                print(f"  📁 {item.name}/ ({len(md_files)} md files)")
    
    print(f"\n总计: {total_dirs} 个指南目录, {total_md} 个Markdown文件")
    
    # 统计images
    images_dir = base / "images"
    if images_dir.exists():
        img_count = len(list(images_dir.glob("*.jpg")))
        print(f"🖼️  Images目录: {img_count} 张图片")

if __name__ == "__main__":
    organize_files()
