#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Parser - L1 原子工具

纯净的 PDF 解析，不含医学推理。
完整内容写入 Sandbox 文件，返回路径。
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime


# =============================================================================
# 核心函数
# =============================================================================

def parse_pdf_toc(
    pdf_path: str,
    sandbox_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    解析 PDF 目录 (TOC)。

    Args:
        pdf_path: PDF 文件路径
        sandbox_root: Sandbox 工作目录

    Returns:
        {
            "status": "success" | "error",
            "pdf_path": str,
            "total_pages": int,
            "toc_file": str,       # 目录 JSON 文件路径
            "chapter_count": int   # 章节数量
        }
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return {
            "status": "error",
            "error": "PyMuPDF 未安装。请运行：pip install pymupdf"
        }

    if not os.path.exists(pdf_path):
        return {
            "status": "error",
            "error": f"文件不存在：{pdf_path}"
        }

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # 获取目录
    toc = doc.get_toc()
    if not toc:
        toc = _extract_toc_fallback(doc)

    chapters = [
        {"level": level, "title": title, "page": page_num}
        for level, title, page_num in (toc or [])
    ]
    doc.close()

    # 目录写入文件
    toc_json = json.dumps(chapters, ensure_ascii=False, indent=2)
    filename = f"pdf_toc_{os.path.basename(pdf_path).replace('.pdf', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    toc_file = _write_to_sandbox(toc_json, filename, sandbox_root)

    return {
        "status": "success",
        "pdf_path": pdf_path,
        "total_pages": total_pages,
        "toc_file": toc_file,
        "chapter_count": len(chapters)
    }


def parse_pdf_pages(
    pdf_path: str,
    page_start: int,
    page_end: int,
    sandbox_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    解析 PDF 指定页码范围。

    Args:
        pdf_path: PDF 文件路径
        page_start: 起始页码 (1-indexed)
        page_end: 结束页码 (1-indexed)
        sandbox_root: Sandbox 工作目录

    Returns:
        {
            "status": "success" | "error",
            "pdf_path": str,
            "pages_requested": [start, end],
            "content_file": str,   # 内容 JSON 文件路径
            "char_count": int      # 字符数
        }
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return {
            "status": "error",
            "error": "PyMuPDF 未安装。请运行：pip install pymupdf"
        }

    if not os.path.exists(pdf_path):
        return {
            "status": "error",
            "error": f"文件不存在：{pdf_path}"
        }

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # 边界检查
    start_idx = max(0, page_start - 1)
    end_idx = min(total_pages, page_end)

    extracted_pages = []
    for p_idx in range(start_idx, end_idx):
        page = doc[p_idx]
        text = page.get_text()
        extracted_pages.append({
            "page_num": p_idx + 1,
            "text": text
        })
    doc.close()

    # 内容写入文件
    content_json = json.dumps(extracted_pages, ensure_ascii=False, indent=2)
    filename = f"pdf_pages_{os.path.basename(pdf_path).replace('.pdf', '')}_{page_start}-{page_end}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    content_file = _write_to_sandbox(content_json, filename, sandbox_root)

    return {
        "status": "success",
        "pdf_path": pdf_path,
        "pages_requested": [page_start, page_end],
        "content_file": content_file,
        "char_count": sum(len(p["text"]) for p in extracted_pages)
    }


# =============================================================================
# 工具函数
# =============================================================================

def _extract_toc_fallback(doc) -> List[tuple]:
    """
    Fallback：当 PDF 没有内置书签时，读取前 5 页尝试提取目录
    """
    import re
    toc_entries = []
    max_pages = min(5, len(doc))

    for p_idx in range(max_pages):
        page = doc[p_idx]
        text = page.get_text()

        patterns = [
            r'^(\d+(?:\.\d+)*)\.?\s*([^.]+?)\s*\.{5,}\s*(\d+)$',
            r'^Chapter\s*(\d+):?\s*([^.]+?)\s*\.{5,}\s*(\d+)$',
            r'^第 (\d+) 章 [：:]?\s*([^。]+?)\s*\.{5,}\s*(\d+)$',
        ]

        for line in text.split('\n'):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    groups = match.groups()
                    try:
                        page_num = int(groups[-1])
                        title = ' - '.join(groups[:-1])
                        toc_entries.append((1, title.strip(), page_num))
                        break
                    except ValueError:
                        continue

    return toc_entries


def _write_to_sandbox(content: str, filename: str, sandbox_root: Optional[str] = None) -> str:
    """
    写入 Sandbox 文件，返回绝对路径。

    路径解析优先级：
    1. SANDBOX_ROOT 环境变量（最高优先级，唯一真理）
    2. 动态推导的备用路径（基于当前文件位置）

    Args:
        content: 文件内容
        filename: 文件名
        sandbox_root: 传入的 Sandbox 根目录（可为 "/sandbox" 虚拟路径）

    Returns:
        写入文件的绝对路径
    """
    root = os.environ.get("SANDBOX_ROOT")

    if root:
        pass
    elif sandbox_root and sandbox_root == "/sandbox":
        root = _get_fallback_sandbox_root()
    elif sandbox_root:
        root = sandbox_root
    else:
        root = _get_fallback_sandbox_root()

    os.makedirs(root, exist_ok=True)
    file_path = os.path.join(root, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(file_path)


def _get_fallback_sandbox_root() -> str:
    """
    动态推导备用 Sandbox 根目录。

    基于当前文件位置（core/shared_tools/pdf_parser.py）向上推导：
    core/shared_tools -> core -> 项目根目录 -> workspace/sandbox

    Returns:
        备用 Sandbox 根目录的绝对路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, '../../workspace/sandbox'))
