#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Medical PDF Inspector Skill - 拟人化层级阅读版

支持三层阅读模式：
1. Phase 1 (看目录): mode="toc" - 返回 PDF 目录结构和章节页码
2. Phase 2 (做决策): Agent 根据临床问题决定阅读范围
3. Phase 3 (精读): mode="read_pages" - 仅返回指定页码内容
"""

import os
import json
import re
from typing import Optional, Any, List, Dict, Union

# Pydantic v2
from pydantic import BaseModel, Field

# 本地基类
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import BaseSkill, SkillContext, SkillExecutionError


# =============================================================================
# 输入 Schema (Pydantic 模型)
# =============================================================================

class PDFInspectorInput(BaseModel):
    """PDF Inspector 的输入参数 - 支持拟人化层级阅读"""

    file_path: str = Field(
        ...,
        description="PDF 文件的绝对或相对路径",
        examples=["workspace/cases/Case1/patient_record.pdf"]
    )
    mode: str = Field(
        default="full",
        description="阅读模式: full=全部解析, toc=获取目录, read_pages=精读指定页码",
        pattern="^(full|toc|read_pages)$"
    )
    page_start: int = Field(
        default=1,
        description="起始页码 (1-indexed, 仅 mode=full/read_pages 时有效)",
        ge=1
    )
    page_end: Optional[int] = Field(
        default=None,
        description="结束页码 (可选，仅 mode=full/read_pages 时有效)",
        ge=1
    )
    pages: Optional[List[int]] = Field(
        default=None,
        description="精读模式专用：指定要读取的页码列表，如 [45, 67] 表示读 45-67 页",
    )
    extract_images: bool = Field(
        default=False,
        description="是否提取图片 (大于 30KB 的医学影像/流程图)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                # Phase 1: 看目录
                {
                    "file_path": "Guidelines/脑转诊疗指南/Practice_Guideline_metastases/NCCN_CNS.pdf",
                    "mode": "toc"
                },
                # Phase 3: 精读
                {
                    "file_path": "Guidelines/脑转诊疗指南/Practice_Guideline_metastases/NCCN_CNS.pdf",
                    "mode": "read_pages",
                    "pages": [45, 67]
                },
                # 传统模式
                {
                    "file_path": "workspace/cases/Case1/patient_record.pdf",
                    "page_start": 1,
                    "page_end": 5,
                    "extract_images": True
                }
            ]
        }


# =============================================================================
# Skill 实现
# =============================================================================

class PDFInspector(BaseSkill[PDFInspectorInput]):
    """
    医疗 PDF 解析器 - 拟人化层级阅读版

    支持三层阅读模式，模拟真实医生翻阅指南的行为：
    - Phase 1 (toc): 先看目录结构，了解有哪些章节
    - Phase 2 (决策): Agent 根据临床问题决定要读哪些章节
    - Phase 3 (read_pages): 只读取需要的页面，节省 Token
    """

    name = "parse_medical_pdf"
    description = (
        "【拟人化层级阅读】从医疗 PDF 文档中提取信息。"
        "支持三种模式：(1) mode='toc' 获取目录和章节页码；(2) mode='read_pages' 精读指定页码；(3) mode='full' 全部解析。"
        "适用于：Phase 1 先看指南目录定位目标章节，Phase 3 精读具体内容。"
    )
    input_schema_class = PDFInspectorInput

    def __init__(self):
        super().__init__()
        self.retry_config.max_retries = 1

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.input_schema_class.model_json_schema()

    def _extract_toc_fallback(self, doc) -> List[Dict[str, Any]]:
        """
        Fallback 机制：当 PDF 没有内置书签时，读取前 5 页尝试提取目录
        使用正则表达式匹配常见的目录格式
        """
        toc_entries = []
        max_pages = min(5, len(doc))

        for p_idx in range(max_pages):
            page = doc[p_idx]
            text = page.get_text()

            # 匹配目录格式：章节标题 + 页码
            # 常见格式：1. Principles of Surgery ............ 12
            #          1.1 Systemic Therapy ................. 45
            #          Chapter 2: Radiation Therapy ........ 67
            patterns = [
                r'^(\d+(?:\.\d+)*)\.?\s*([^.]+?)\s*\.{5,}\s*(\d+)$',  # 1. Title ....... 12
                r'^Chapter\s*(\d+):?\s*([^.]+?)\s*\.{5,}\s*(\d+)$',   # Chapter 1: Title .... 12
                r'^([A-Z])\.?\s*([^.]+?)\s*\.{5,}\s*(\d+)$',           # A. Title ....... 12
                r'^第(\d+)章[：:]?\s*([^。]+?)\s*\.{5,}\s*(\d+)$',      # 第1章：标题 ....... 12
                r'^(\d+)[、.]([^。]+?)\s*\.{5,}\s*(\d+)$',            # 1、标题 ....... 12
            ]

            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                matched = False
                for pattern in patterns:
                    match = re.match(pattern, line, re.MULTILINE)
                    if match:
                        groups = match.groups()
                        if len(groups) >= 3:
                            try:
                                page_num = int(groups[-1])
                                title = ' - '.join(groups[:-1])
                                toc_entries.append({
                                    "title": title.strip(),
                                    "page": page_num,
                                    "source": "text_analysis"
                                })
                                matched = True
                                break
                            except ValueError:
                                continue

        # 去重并按页码排序
        seen = set()
        unique_toc = []
        for entry in toc_entries:
            key = (entry["title"], entry["page"])
            if key not in seen:
                seen.add(key)
                unique_toc.append(entry)

        unique_toc.sort(key=lambda x: x["page"])
        return unique_toc

    def execute(self, args: PDFInspectorInput, context: Optional[SkillContext] = None) -> str:
        """
        执行 PDF 解析 - 支持拟人化层级阅读

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的解析结果
        """
        try:
            try:
                import fitz  # PyMuPDF
            except ImportError:
                raise SkillExecutionError("PyMuPDF 未安装。请运行：pip install pymupdf")

            if not os.path.exists(args.file_path):
                raise SkillExecutionError(f"文件不存在：{args.file_path}")

            doc = fitz.open(args.file_path)
            total_pages = len(doc)

            # ==================== Phase 1: 看目录 ====================
            if args.mode == "toc":
                # 尝试获取内置书签
                toc = doc.get_toc()

                if toc:
                    # 有内置书签，直接使用
                    chapters = []
                    for level, title, page_num in toc:
                        # PyMuPDF 返回的页码是 1-indexed
                        chapters.append({
                            "level": level,
                            "title": title,
                            "page": page_num
                        })
                else:
                    # Fallback: 使用正则提取前 5 页的目录
                    chapters = self._extract_toc_fallback(doc)

                doc.close()

                return json.dumps({
                    "mode": "toc",
                    "file_path": args.file_path,
                    "total_pages": total_pages,
                    "chapters": chapters,
                    "chapter_count": len(chapters),
                    "note": "如果没有内置书签，将尝试从文本中提取目录"
                }, ensure_ascii=False, indent=2)

            # ==================== Phase 2 & 3: 精读指定页码 ====================
            if args.mode == "read_pages":
                if not args.pages or len(args.pages) < 2:
                    raise SkillExecutionError("精读模式需要指定 pages 参数，如 pages=[45, 67]")

                start_page = args.pages[0]
                end_page = args.pages[1]

                # 边界检查
                if start_page < 1:
                    start_page = 1
                if end_page > total_pages:
                    end_page = total_pages
                if start_page > end_page:
                    start_page, end_page = end_page, start_page

                extracted_pages = []
                for p_idx in range(start_page - 1, end_page):
                    page = doc[p_idx]
                    blocks = page.get_text("blocks")
                    blocks.sort(key=lambda b: (b[1], b[0]))
                    page_text = "\n".join(
                        [b[4].replace("\n", " ").strip() for b in blocks if b[6] == 0]
                    )

                    extracted_pages.append({
                        "page_num": p_idx + 1,
                        "text": page_text
                    })

                doc.close()

                return json.dumps({
                    "mode": "read_pages",
                    "file_path": args.file_path,
                    "pages_requested": args.pages,
                    "pages_returned": [p["page_num"] for p in extracted_pages],
                    "extracted_pages": extracted_pages,
                    "total_pages_read": len(extracted_pages)
                }, ensure_ascii=False, indent=2)

            # ==================== 传统模式: 全部解析 ====================
            start_idx = max(0, args.page_start - 1)
            end_idx = min(total_pages, args.page_end) if args.page_end else total_pages

            result = {
                "metadata": doc.metadata,
                "total_pages": total_pages,
                "extracted_pages": [],
                "extracted_visuals": []
            }

            vis_dir = os.path.abspath("workspace/temp_visuals")
            if args.extract_images:
                os.makedirs(vis_dir, exist_ok=True)

            for p_idx in range(start_idx, end_idx):
                page = doc[p_idx]
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (b[1], b[0]))
                page_text = "\n".join(
                    [b[4].replace("\n", " ").strip() for b in blocks if b[6] == 0]
                )

                result["extracted_pages"].append({
                    "page_num": p_idx + 1,
                    "text_snippet": (
                        page_text[:1500] + "..."
                        if len(page_text) > 1500 else page_text
                    )
                })

                if args.extract_images:
                    image_list = page.get_images(full=True)
                    for img_idx, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        ext = base_image["ext"]

                        if len(image_bytes) > 30720:
                            img_filename = f"med_vis_p{p_idx + 1}_{img_idx}.{ext}"
                            img_path = os.path.join(vis_dir, img_filename)

                            with open(img_path, "wb") as f:
                                f.write(image_bytes)

                            result["extracted_visuals"].append({
                                "page_num": p_idx + 1,
                                "local_path": img_path,
                                "hint": "This is a large clinical image."
                            })

            doc.close()
            return json.dumps(result, ensure_ascii=False, indent=2)

        except SkillExecutionError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"PDF 解析失败：{str(e)}") from e


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Medical PDF Inspector - Hierarchical Reading")
    parser.add_argument("--file_path", required=True, help="Path to the PDF file")
    parser.add_argument("--mode", default="full", choices=["full", "toc", "read_pages"],
                        help="Reading mode: full, toc, or read_pages")
    parser.add_argument("--pages", type=int, nargs=2, default=None,
                        help="Pages range for read_pages mode, e.g., --pages 45 67")
    parser.add_argument("--page_start", type=int, default=1)
    parser.add_argument("--page_end", type=int, default=None)
    parser.add_argument("--extract_images", action="store_true")

    args = parser.parse_args()

    inspector = PDFInspector()

    if args.mode == "read_pages" and args.pages:
        input_args = PDFInspectorInput(
            file_path=args.file_path,
            mode=args.mode,
            pages=args.pages,
            extract_images=args.extract_images
        )
    else:
        input_args = PDFInspectorInput(
            file_path=args.file_path,
            mode=args.mode,
            page_start=args.page_start,
            page_end=args.page_end,
            extract_images=args.extract_images
        )

    try:
        result = inspector.execute(input_args)
        print(result)
    except SkillExecutionError as e:
        print(json.dumps({"error": str(e)}))
        exit(1)


if __name__ == "__main__":
    main()