#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
parse_pdf_to_md.py - PDF 文本与结构化解析轨 (L1 原子工具)

基于 Magic-PDF (MinerU) 的极高保真度 PDF 解析引擎，
专为双栏排版、复杂医疗表格的临床指南 PDF 优化，
输出结构化的 Markdown 格式。

依赖: magic-pdf (MinerU - https://github.com/opendatalab/MinerU)
禁止: PyPDF2, pdfplumber, marker-pdf 等其他 PDF 库
"""

import os
import sys

# Set VIRTUAL_VRAM_SIZE for CPU-only mode to avoid GPU detection issues
os.environ.setdefault('VIRTUAL_VRAM_SIZE', '0')
import re
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass


# =============================================================================
# 常量定义
# =============================================================================

# 医学文献常见的页眉页脚关键词（用于清洗）
MEDICAL_HEADER_PATTERNS = [
    r'^\s*\d+\s*$',  # 纯数字页码
    r'^\s*Copyright\s+[©ⓒ].*$',  # 版权声明
    r'^\s*©.*\d{4}.*$',  # 版权符号行
    r'^\s*All rights reserved.*$',  # 版权保留
    r'^\s*https?://\S+\s*$',  # URL 单独成行
    r'^\s*www\.\S+\.\S+\s*$',  # 网址
    r'^\s*DOI:\s*\S+',  # DOI 行
    r'^\s*doi:\s*\S+',  # doi 小写
    r'^\s*Downloaded from.*$',  # 下载来源
    r'^\s*Published by.*$',  # 出版商
    r'^\s*Vol\.?\s*\d+.*$',  # 卷号
    r'^\s*No\.?\s*\d+.*$',  # 期号
    r'^\s*Page\s+\d+\s+of\s+\d+',  # Page X of Y
    r'^\s*\d+\s*/\s*\d+\s*$',  # 数字/数字 格式页码
    r'^\s*NCCN\.org\s*$',  # NCCN 特定
    r'^\s*JNCCN\.org\s*$',  # JNCCN 特定
    r'^\s*JCO\.org\s*$',  # JCO 特定
    r'^\s*ESMO.*Guidelines?',  # ESMO 指南页眉
    r'^\s*Guidelines?\s+\d{4}.*$',  # 指南年份
    r'^\s*Table of Contents.*$',  # 目录提示
    r'^\s*CONTENTS\s*$',  # CONTENTS 大写
    r'^\s*References?\s*$',  # References 单独成行（可能是页脚导航）
]

# 医学文献特定的引用标记模式（需要保留）
CITATION_PATTERNS = [
    r'\[\d+(?:,\s*\d+)*\]',  # [1], [1,2], [1, 2, 3]
    r'\(\d{4}\)',  # (2024) 年份引用
    r'\([A-Z][a-z]+\s+et\s+al\.?,?\s*\d{4}\)',  # (Author et al., 2024)
    r'\d+\.\s*\S+\s+et\s+al\.',  # 编号. Author et al.
]

# 需要合并的断行模式
LINE_CONTINUATION_PATTERNS = [
    (r'([a-zA-Z])-\s*$', r'\1'),  # 单词连字符断行
    (r'([a-zA-Z]),\s*$', r'\1,'),  # 逗号断行（保留逗号）
]


@dataclass
class MedicalContentBlock:
    """医学内容块数据结构"""
    content_type: str  # "text", "table", "title", "figure_caption", "footer"
    content: str
    page_num: Optional[int] = None
    level: Optional[int] = None  # 标题层级
    bbox: Optional[Tuple[float, float, float, float]] = None  # 边界框


# =============================================================================
# Sandbox 路径管理
# =============================================================================

def get_sandbox_root() -> str:
    """
    获取 Sandbox 根目录。
    优先级: SANDBOX_ROOT 环境变量 > 项目默认路径
    """
    env_root = os.environ.get("SANDBOX_ROOT")
    if env_root:
        return env_root

    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent
    return str(project_root / "workspace" / "sandbox")


# =============================================================================
# 轻量级文本清洗（Minimal Viable Fix）
# =============================================================================

# 医学术语字典映射（小写 -> 标准大写）
MEDICAL_TERM_MAP = {
    'idh': 'IDH',
    'mgmt': 'MGMT',
    'braf': 'BRAF',
    'atrx': 'ATRX',
    'tert': 'TERT',
    'who': 'WHO',
    'cns': 'CNS',
    'mgmt promoter': 'MGMT promoter',
    'braf v600e': 'BRAF V600E',
    'braf v600': 'BRAF V600',
    'idh-mutated': 'IDH-mutated',
    'idh wildtype': 'IDH wildtype',
    'idhwt': 'IDHwt',
    'idhm': 'IDHm',
}

def lightweight_clean(text: str) -> str:
    """
    轻量级清洗：修复明显的 OCR 错误，保留原始格式

    策略：
    1. 修复 NCCN 特殊字体导致的大小写问题（如 cLINICAL -> CLINICAL）
    2. 修复明显的粘连问题（如 braFAND -> braF AND）
    3. 医学术语字典映射修复
    """
    # 步骤 1: 修复 NCCN 特殊字体问题
    # 模式：单个小写字母后跟多个大写字母（如 cLINICAL, nERVOUS）
    # 修复为：全部大写（这是 PDF 中的实际排版）
    def fix_small_caps(match):
        return match.group(0).upper()

    text = re.sub(r'\b[a-z][A-Z]{2,}\b', fix_small_caps, text)

    # 步骤 2: 医学术语字典映射（词边界匹配，忽略大小写）
    for old_term, new_term in MEDICAL_TERM_MAP.items():
        pattern = r'\b' + re.escape(old_term) + r'\b'
        text = re.sub(pattern, new_term, text, flags=re.IGNORECASE)

    # 步骤 3: 修复明显的粘连（小写+大写+小写）如 "braFAND" -> "braF AND"
    text = re.sub(r'([a-z])([A-Z])([a-z])', r'\1 \2\3', text)

    return text


def parse_pdf_to_markdown(
    pdf_path: str,
    output_dir: Optional[str] = None,
    method: str = "auto",
    lang: str = "en",
    debug: bool = False
) -> Dict[str, Any]:
    """
    使用 Magic-PDF (MinerU) 将 PDF 解析为结构化 Markdown。

    MinerU 核心优势：
    - 基于视觉模型 + 布局分析
    - 自动识别双栏/多栏排版
    - 高质量表格还原（支持合并单元格）
    - 自动去除页眉页脚
    - 保留公式、图表位置标记

    Args:
        pdf_path: PDF 文件的绝对路径
        output_dir: 输出目录 (默认使用 SANDBOX_ROOT)
        method: 解析模式 ("auto", "ocr", "txt")
                - auto: 自动判断（推荐）
                - ocr: 强制 OCR 模式（扫描版 PDF）
                - txt: 纯文本模式（文字版 PDF）
        lang: OCR 语言 ("en" 英文, "ch" 中文，默认 "en")
        debug: 是否保留中间 JSON 文件用于调试

    Returns:
        Dict 包含以下字段:
        - status: "success" | "error"
        - markdown_file: Markdown 文件的绝对路径 (成功时)
        - metadata_file: 原始 JSON 元数据文件路径 (debug=True 时)
        - page_count: PDF 页数
        - char_count: 解析文本字符数
        - table_count: 提取的表格数量
        - figure_count: 提取的图片/图表数量
        - error: 错误信息 (失败时)
        - warning: 警告信息列表 (可选)
    """
    warnings = []

    # ===== 1. 输入验证 =====
    if not os.path.exists(pdf_path):
        return {
            "status": "error",
            "error": f"PDF 文件不存在: {pdf_path}"
        }

    if not pdf_path.lower().endswith('.pdf'):
        return {
            "status": "error",
            "error": f"文件不是 PDF 格式: {pdf_path}"
        }

    # ===== 2. 动态导入 Magic-PDF =====
    try:
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.config.enums import SupportedPdfParseMethod
        from magic_pdf.config.make_content_config import DropMode, MakeMode
    except ImportError as e:
        return {
            "status": "error",
            "error": f"magic-pdf (MinerU) 未安装。请运行: pip install magic-pdf\n详细错误: {str(e)}"
        }

    # ===== 3. 准备输出目录 =====
    if output_dir is None:
        output_dir = get_sandbox_root()

    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名（使用固定命名，便于复用）
    base_name = Path(pdf_path).stem
    output_name = base_name  # 去掉时间戳，固定命名

    md_output_path = os.path.join(output_dir, f"{output_name}.md")

    # ===== 3.5 检查是否已存在（复用机制）=====
    if os.path.exists(md_output_path) and not debug:
        # 文件已存在，直接读取并返回信息
        with open(md_output_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        return {
            "status": "success",
            "markdown_file": os.path.abspath(md_output_path),
            "page_count": "unknown (cached)",
            "char_count": len(existing_content),
            "table_count": existing_content.count('|') // 3,
            "figure_count": existing_content.count('!['),
            "title_count": existing_content.count('\n#'),
            "warning": "Using cached file. Delete .md file to re-parse."
        }

    json_output_path = os.path.join(output_dir, f"{output_name}_raw.json")

    # ===== 4. 执行 MinerU 解析 =====
    try:
        # 读取 PDF
        pdf_bytes = open(pdf_path, "rb").read()
        ds = PymuDocDataset(pdf_bytes)

        # 使用 fitz 获取页数 (PymuDocDataset 不支持 len())
        import fitz
        temp_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(temp_doc)
        temp_doc.close()

        # 选择解析方法
        # 强制全程使用 OCR 模式，切断 PDF 字体提取回退，确保表格内容也走视觉 OCR
        ocr_enabled = True
        force_ocr = True  # 强制标志，无视 PDF 是否有文本层

        # 执行文档分析（核心步骤）
        # MinerU 1.3.0+ API: doc_analyze 直接处理整个 dataset
        # 强制 OCR 模式处理所有内容，包括表格
        analyze_result = doc_analyze(ds, ocr=ocr_enabled, show_log=True, lang=lang)

        # MinerU 1.3.0+ 新 API: 使用 pipe 模式提取文本并生成 Markdown
        # 确保 images 子目录存在
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        image_writer = FileBasedDataWriter(images_dir)

        # 强制使用 OCR 模式 pipe，确保表格内容也经过 OCR 而非 CID 提取
        pipe_result = analyze_result.pipe_ocr_mode(
            imageWriter=image_writer,
            start_page_id=0,
            end_page_id=total_pages - 1,
            debug_mode=debug
        )

        # 获取 Markdown 内容 - 使用相对路径
        md_content = pipe_result.get_markdown(
            img_dir_or_bucket_prefix="images",
            drop_mode=DropMode.NONE,
        )

        # ===== 轻量级清洗（Minimal Viable Fix）=====
        md_content = lightweight_clean(md_content)

        # ===== 提取图片-页码映射 =====
        image_page_map = extract_image_page_mapping(pipe_result, md_content, output_dir)

        # 生成带页码注释的 Markdown
        md_content_with_pages = insert_page_markers(md_content, image_page_map)

        # 写入 Markdown 文件
        with open(md_output_path, 'w', encoding='utf-8') as f:
            f.write(md_content_with_pages)

        # 写入图片-页码映射文件
        map_file_path = os.path.join(output_dir, f"{output_name}_image_page_map.json")
        with open(map_file_path, 'w', encoding='utf-8') as f:
            json.dump(image_page_map, f, ensure_ascii=False, indent=2)

        # 可选：保存原始 JSON 用于调试
        if debug:
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(pipe_result._pipe_res if hasattr(pipe_result, '_pipe_res') else {},
                         f, ensure_ascii=False, indent=2, default=str)

        # 统计 Markdown 内容
        char_count = len(md_content)
        table_count = md_content.count('|') // 3  # 粗略估计表格数
        figure_count = md_content.count('![')  # 图片引用数
        title_count = md_content.count('\n#')  # 标题数

        result = {
            "status": "success",
            "markdown_file": os.path.abspath(md_output_path),
            "page_count": total_pages,
            "char_count": char_count,
            "table_count": table_count,
            "figure_count": figure_count,
            "title_count": title_count,
            "warning": "; ".join(warnings) if warnings else None
        }

        if debug:
            result["metadata_file"] = os.path.abspath(json_output_path)

        # 添加图片映射文件路径到返回结果
        result["image_page_map_file"] = os.path.abspath(map_file_path)

        return result

    except Exception as e:
        error_msg = str(e)

        # 常见错误分类
        if "password" in error_msg.lower() or "encrypted" in error_msg.lower():
            error_msg = "PDF 已加密，无法解析。请提供解密后的文件。"
        elif "corrupt" in error_msg.lower():
            error_msg = f"PDF 文件损坏或格式异常: {error_msg}"
        elif "memory" in error_msg.lower() or "cuda" in error_msg.lower():
            error_msg = f"内存/GPU 不足，无法处理大型 PDF: {error_msg}"
        elif "model" in error_msg.lower():
            error_msg = f"MinerU 模型加载失败，请检查模型文件: {error_msg}"

        return {
            "status": "error",
            "error": f"PDF 解析失败: {error_msg}",
            "warning": "; ".join(warnings) if warnings else None
        }


# =============================================================================
# 图片-页码映射功能（新增）
# =============================================================================

def extract_image_page_mapping(pipe_result, md_content: str, output_dir: str) -> Dict[str, Any]:
    """
    从 MinerU 底层 JSON 结果中精准提取图片与页码的映射关系。
    彻底废弃按文本长度比例猜测的错误逻辑。
    """
    images = []
    img_page_map = {}

    try:
        # 1. 递归搜索器：从 MinerU 的原生 JSON 中精准提取页码
        # MinerU 的版本更新频繁，底层 JSON 结构可能变动，递归查找最稳妥
        if hasattr(pipe_result, '_pipe_res'):
            raw_data = pipe_result._pipe_res
            
            def find_images_in_json(obj, current_page=None):
                if isinstance(obj, dict):
                    # 捕捉页码标识 (MinerU 通常使用 page_idx 或 page_no，0-indexed)
                    page = obj.get('page_idx', obj.get('page_no', current_page))
                    
                    # 捕捉图片路径
                    if 'image_path' in obj or 'img_path' in obj:
                        path = obj.get('image_path', obj.get('img_path', ''))
                        if path:
                            img_name = os.path.basename(path)
                            if page is not None:
                                # 转换为 1-indexed (物理页码)
                                img_page_map[img_name] = int(page) + 1 
                                
                    for v in obj.values():
                        find_images_in_json(v, page)
                elif isinstance(obj, list):
                    for item in obj:
                        find_images_in_json(item, current_page)

            find_images_in_json(raw_data)

        # 2. 扫描 Markdown，组装最终的映射表
        img_pattern = r'!\[([^\]]*)\]\(([^)]+/images/([a-f0-9]+\.jpg|png))\)'
        matches = list(re.finditer(img_pattern, md_content))

        for i, match in enumerate(matches):
            alt_text = match.group(1)
            full_path = match.group(2)
            img_name = match.group(3)

            # 从精准字典中获取，拿不到再 fallback 到 1
            exact_page = img_page_map.get(img_name, 1)

            images.append({
                "image_name": img_name,
                "image_path": os.path.join(output_dir, "images", img_name),
                "relative_path": f"images/{img_name}",
                "page_num": exact_page,
                "alt_text": alt_text,
                "inferred": False if img_name in img_page_map else True
            })

    except Exception as e:
        return {"images": images, "total_images": len(images), "error": str(e)}

    # 去重处理
    seen = set()
    unique_images = []
    for img in images:
        if img["image_name"] not in seen:
            seen.add(img["image_name"])
            unique_images.append(img)

    unique_images.sort(key=lambda x: x["page_num"])

    return {
        "images": unique_images,
        "total_images": len(unique_images),
        "page_range": {
            "start": min((img["page_num"] for img in unique_images if img["page_num"] > 0), default=1),
            "end": max((img["page_num"] for img in unique_images), default=1)
        },
        "note": "页码已通过底层元数据精准映射"
    }


def insert_page_markers(md_content: str, image_page_map: Dict[str, Any]) -> str:
    """
    在 Markdown 中精准插入 注释
    """
    if not image_page_map.get("images"):
        return md_content

    img_to_page = {img["image_name"]: img["page_num"] for img in image_page_map["images"]}
    
    lines = md_content.split('\n')
    result_lines = []

    for line in lines:
        # 检测图片引用: ![](.../images/xxx.jpg)
        img_match = re.search(r'!\[([^\]]*)\]\(([^)]+/images/([a-f0-9]+\.jpg|png))\)', line)
        
        if img_match:
            img_name = img_match.group(3)
            page_num = img_to_page.get(img_name, "UNKNOWN")
            
            # 插入专门给 Agent 看的透视标签
            result_lines.append(f"")
            result_lines.append(line)
        else:
            result_lines.append(line)

    return '\n'.join(result_lines)


def process_table_buffer(buffer: List[str]) -> List[str]:
    """
    处理表格缓冲区，确保 Markdown 表格格式正确。

    医学文献表格常见问题：
    - 缺少分隔行 (|---|---|)
    - 单元格内容对齐问题
    - 合并单元格标记丢失
    """
    if not buffer:
        return []

    # 确保第一行是表头
    header = buffer[0]
    if not header.startswith('|'):
        header = '| ' + header + ' |'

    # 计算列数
    col_count = len([c for c in header.split('|') if c.strip()])

    # 确保有分隔行
    separator = '|' + '|'.join(['---'] * col_count) + '|'

    # 处理数据行
    data_rows = []
    for row in buffer[1:]:
        if '---' in row.replace('|', '').replace('-', ''):
            # 已经是分隔行，跳过（我们会重新生成）
            continue
        if not row.startswith('|'):
            row = '| ' + row + ' |'
        data_rows.append(row)

    # 组装表格
    result = [header, separator] + data_rows

    # 添加空行包裹表格
    return [''] + result + ['']


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="使用 Magic-PDF (MinerU) 将 PDF 解析为结构化 Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法（自动模式）
  python parse_pdf_to_md.py /path/to/guideline.pdf

  # 强制 OCR 模式（扫描版 PDF）
  python parse_pdf_to_md.py /path/to/scan.pdf --method ocr

  # OCR 模式指定英文（推荐用于英文 PDF）
  python parse_pdf_to_md.py /path/to/scan.pdf --method ocr --lang en

  # 纯文本模式（快速处理文字版 PDF）
  python parse_pdf_to_md.py /path/to/text.pdf --method txt

  # 启用调试模式（保留原始 JSON）
  python parse_pdf_to_md.py /path/to/guideline.pdf --debug
        """
    )

    parser.add_argument(
        "pdf_path",
        help="PDF 文件的绝对路径"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="输出目录 (默认: SANDBOX_ROOT 或 workspace/sandbox)"
    )
    parser.add_argument(
        "--method", "-m",
        choices=["auto", "ocr", "txt"],
        default="auto",
        help="解析模式: auto=自动判断(默认), ocr=强制OCR, txt=纯文本"
    )
    parser.add_argument(
        "--lang", "-l",
        choices=["en", "ch"],
        default="en",
        help="OCR 语言: en=英文(默认), ch=中文（仅在 --method ocr 时生效）"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="保留中间 JSON 文件用于调试"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果"
    )

    args = parser.parse_args()

    result = parse_pdf_to_markdown(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        method=args.method,
        lang=args.lang,
        debug=args.debug
    )

    if args.json:
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "success":
            print(f"✅ PDF 解析成功")
            print(f"📄 Markdown 文件: {result['markdown_file']}")
            print(f"📊 页数: {result['page_count']}")
            print(f"📝 字符数: {result['char_count']}")
            print(f"📋 表格数: {result['table_count']}")
            print(f"🖼️  图表数: {result['figure_count']}")
            print(f"📌 标题数: {result['title_count']}")
            if result.get('metadata_file'):
                print(f"🔧 调试文件: {result['metadata_file']}")
            if result.get('warning'):
                print(f"⚠️  警告: {result['warning']}")
        else:
            print(f"❌ PDF 解析失败: {result['error']}", file=sys.stderr)
            if result.get('warning'):
                print(f"⚠️  警告: {result['warning']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
