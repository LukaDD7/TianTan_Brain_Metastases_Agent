#!/usr/bin/env python3
import os
import glob

sandbox = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox"

# 统计清理前
hash_jpgs = glob.glob(os.path.join(sandbox, "*.jpg"))
mds = glob.glob(os.path.join(sandbox, "*.md"))

print(f"=== 清理前 ===")
print(f"哈希命名的JPG图片: {len(hash_jpgs)} 个")
print(f"Markdown文件: {len(mds)} 个")

# 删除哈希命名的JPG (64位16进制哈希)
deleted_jpgs = 0
for jpg in hash_jpgs:
    basename = os.path.basename(jpg)
    name_without_ext = basename.replace('.jpg', '')
    if len(name_without_ext) == 64 and all(c in '0123456789abcdef' for c in name_without_ext.lower()):
        os.remove(jpg)
        deleted_jpgs += 1
        print(f"  删除: {basename}")

print(f"\n=== 已删除哈希图片 ===")
print(f"删除了 {deleted_jpgs} 个哈希命名的JPG文件")

# 列出保留的内容
print(f"\n=== 清理后 ===")
remaining = os.listdir(sandbox)
print(f"根目录剩余项目数: {len(remaining)}")
dirs = [d for d in remaining if os.path.isdir(os.path.join(sandbox, d))]
print(f"保留的目录: {dirs}")
