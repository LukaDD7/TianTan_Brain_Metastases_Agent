#!/usr/bin/env python3
import os
import re

sandbox_dir = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox"

# 获取所有 .jpg 文件
jpg_files = [f for f in os.listdir(sandbox_dir) if f.endswith('.jpg')]

# 64位十六进制哈希的正则表达式模式 (64个十六进制字符)
hash_pattern = re.compile(r'^[a-f0-9]{64}\.jpg$')

# 识别哈希命名的文件
hash_files = []
for f in jpg_files:
    if hash_pattern.match(f):
        hash_files.append(f)

print(f"发现 {len(jpg_files)} 个 .jpg 文件")
print(f"其中 {len(hash_files)} 个是64位十六进制哈希命名的文件")
print("\n即将删除以下文件:")
for f in hash_files:
    print(f"  - {f}")

# 删除文件
deleted_count = 0
for f in hash_files:
    filepath = os.path.join(sandbox_dir, f)
    try:
        os.remove(filepath)
        deleted_count += 1
    except Exception as e:
        print(f"删除失败 {f}: {e}")

print(f"\n成功删除了 {deleted_count} 个文件")

# 验证剩余文件
remaining_jpg = [f for f in os.listdir(sandbox_dir) if f.endswith('.jpg')]
print(f"\n剩余的 .jpg 文件数量: {len(remaining_jpg)}")
if remaining_jpg:
    print("剩余文件:")
    for f in remaining_jpg:
        print(f"  - {f}")
