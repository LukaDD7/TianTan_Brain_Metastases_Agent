#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Medical PDF Inspector Skill

从医疗 PDF 文档中提取文本和高分辨率医学影像。
"""

import os
import json
from typing import Optional, Any, List, Dict

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
    """PDF Inspector 的输入参数"""

    file_path: str = Field(
        ...,
        description="PDF 文件的绝对或相对路径",
        examples=["workspace/cases/Case1/patient_record.pdf"]
    )
    page_start: int = Field(
        default=1,
        description="起始页码 (1-indexed)",
        ge=1
    )
    page_end: Optional[int] = Field(
        default=None,
        description="结束页码 (可选，默认为全部)",
        ge=1
    )
    extract_images: bool = Field(
        default=False,
        description="是否提取图片 (大于 30KB 的医学影像/流程图)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
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
    医疗 PDF 解析器 - 提取文本和高分辨率医学影像。
    """

    name = "parse_medical_pdf"
    description = (
        "从医疗 PDF 文档中提取文本和高分辨率医学影像。"
        "适用于：解析患者电子病历 (EHR)、提取肿瘤诊疗指南 (NCCN/ESMO/CSCO)、"
        "识别 CT/MRI 影像图片或 NCCN 决策树流程图。"
        "注意：提取的图片会保存到 workspace/temp_visuals/ 目录。"
    )
    input_schema_class = PDFInspectorInput

    def __init__(self):
        super().__init__()
        # 配置重试策略：PDF 解析通常是本地 I/O，不需要重试
        self.retry_config.max_retries = 1

    @property
    def input_schema(self) -> Dict[str, Any]:
        """获取 JSON Schema (用于 LLM Tool 调用)"""
        return self.input_schema_class.model_json_schema()

    def execute(self, args: PDFInspectorInput, context: Optional[SkillContext] = None) -> str:
        """
        执行 PDF 解析。

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的解析结果

        Raises:
            SkillExecutionError: 执行失败时抛出
        """
        try:
            # 延迟导入 PyMuPDF (避免模块未安装时的导入错误)
            try:
                import fitz  # PyMuPDF
            except ImportError:
                raise SkillExecutionError(
                    "PyMuPDF 未安装。请运行：pip install pymupdf"
                )

            # 检查文件是否存在
            if not os.path.exists(args.file_path):
                raise SkillExecutionError(f"文件不存在：{args.file_path}")

            # 打开 PDF
            doc = fitz.open(args.file_path)
            total_pages = len(doc)

            # 计算页码范围
            start_idx = max(0, args.page_start - 1)
            end_idx = min(total_pages, args.page_end) if args.page_end else total_pages

            # 结果容器
            result = {
                "metadata": doc.metadata,
                "total_pages": total_pages,
                "extracted_pages": [],
                "extracted_visuals": []
            }

            # 确保图片存放目录存在
            vis_dir = os.path.abspath("workspace/temp_visuals")
            if args.extract_images:
                os.makedirs(vis_dir, exist_ok=True)

            # 逐页解析
            for p_idx in range(start_idx, end_idx):
                page = doc[p_idx]

                # 1. 文本提取：使用 "blocks" 模式处理双栏排版
                blocks = page.get_text("blocks")
                # 按垂直位置 (y0) 和水平位置 (x0) 排序，还原阅读顺序
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

                # 2. 医学影像提取
                if args.extract_images:
                    image_list = page.get_images(full=True)
                    for img_idx, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        ext = base_image["ext"]

                        # 医学阈值过滤：过滤掉小于 30KB 的页眉页脚 Logo
                        if len(image_bytes) > 30720:
                            img_filename = f"med_vis_p{p_idx + 1}_{img_idx}.{ext}"
                            img_path = os.path.join(vis_dir, img_filename)

                            with open(img_path, "wb") as f:
                                f.write(image_bytes)

                            result["extracted_visuals"].append({
                                "page_num": p_idx + 1,
                                "local_path": img_path,
                                "hint": (
                                    "This is a large clinical image. "
                                    "Recommend using Vision capabilities to read this flowchart or scan."
                                )
                            })

            doc.close()

            # 返回标准 JSON
            return json.dumps(result, ensure_ascii=False, indent=2)

        except SkillExecutionError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"PDF 解析失败：{str(e)}") from e


# =============================================================================
# CLI 入口 (向后兼容)
# =============================================================================

def main():
    """命令行入口 (向后兼容旧用法)"""
    import argparse

    parser = argparse.ArgumentParser(description="Medical PDF Inspector for Agents")
    parser.add_argument("--file_path", required=True, help="Path to the PDF file")
    parser.add_argument("--page_start", type=int, default=1)
    parser.add_argument("--page_end", type=int, default=None)
    parser.add_argument("--extract_images", action="store_true")

    args = parser.parse_args()

    # 使用 Skill 类执行
    inspector = PDFInspector()
    input_args = PDFInspectorInput(
        file_path=args.file_path,
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
