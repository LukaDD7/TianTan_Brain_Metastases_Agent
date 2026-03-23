#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
render_pdf_page.py - PDF 视觉切片渲染轨 (L1 原子工具)

将 PDF 特定页面高保真渲染为高分辨率 JPG 图片，自动压缩至 < 5MB，用于：
- 医学决策树可视化
- Kaplan-Meier 生存曲线
- 影像学图像
- 复杂图表和流程图

依赖: PyMuPDF (fitz), Pillow (PIL)
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    Image = None


def get_sandbox_root() -> str:
    """
    获取 Sandbox 根目录。
    优先级: SANDBOX_ROOT 环境变量 > 项目默认路径
    """
    env_root = os.environ.get("SANDBOX_ROOT")
    if env_root:
        return env_root

    # 基于当前文件位置推导: skills/pdf-inspector/scripts -> ../../../workspace/sandbox
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent
    return str(project_root / "workspace" / "sandbox")


def compress_image_to_size(
    pil_image: Image.Image,
    max_size_mb: float = 5.0,
    initial_quality: int = 85,
    min_quality: int = 60
) -> bytes:
    """
    使用二分法自动压缩图片至指定大小以下。

    Args:
        pil_image: PIL Image 对象
        max_size_mb: 最大允许大小 (MB)
        initial_quality: 初始 JPEG 质量
        min_quality: 最低 JPEG 质量

    Returns:
        压缩后的 JPEG 字节数据
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    # 首先尝试初始质量
    quality = initial_quality
    buffer = BytesIO()
    pil_image.save(buffer, format='JPEG', quality=quality, optimize=True)
    size = buffer.tell()

    if size <= max_size_bytes:
        return buffer.getvalue()

    # 如果初始质量太大，使用二分法降低质量
    low, high = min_quality, initial_quality

    while low < high - 1:
        mid = (low + high) // 2
        buffer = BytesIO()
        pil_image.save(buffer, format='JPEG', quality=mid, optimize=True)
        size = buffer.tell()

        if size <= max_size_bytes:
            high = mid
        else:
            low = mid

    # 最终使用 high 质量
    buffer = BytesIO()
    pil_image.save(buffer, format='JPEG', quality=high, optimize=True)
    return buffer.getvalue()


def render_pdf_pages(
    pdf_path: str,
    page_numbers: Union[int, List[int]],
    output_dir: Optional[str] = None,
    dpi: int = 200,
    zoom: Optional[float] = None,
    max_size_mb: float = 5.0
) -> Dict[str, Any]:
    """
    将 PDF 指定页面渲染为高分辨率 PNG 图片。

    适用于医学文献中的视觉元素：
    - 决策树 / 流程图
    - Kaplan-Meier 生存曲线
    - 影像学图像
    - 复杂表格和图表

    Args:
        pdf_path: PDF 文件的绝对路径
        page_numbers: 页码或页码列表 (1-indexed)
        output_dir: 输出目录 (默认使用 SANDBOX_ROOT)
        dpi: 渲染分辨率 (默认 200 DPI，医学图像建议 300+)
        zoom: 缩放因子 (覆盖 DPI 设置，例如 2.0 = 2倍放大)

    Returns:
        Dict 包含以下字段:
        - status: "success" | "error" | "partial"
        - image_files: 生成的图片路径列表
        - page_count: 成功渲染的页数
        - failed_pages: 渲染失败的页码列表
        - error: 错误信息 (失败时)
        - warning: 警告信息 (可选)
    """
    # ===== 1. 输入验证 =====
    if not os.path.exists(pdf_path):
        return {
            "status": "error",
            "image_files": [],
            "error": f"PDF 文件不存在: {pdf_path}"
        }

    if not pdf_path.lower().endswith('.pdf'):
        return {
            "status": "error",
            "image_files": [],
            "error": f"文件不是 PDF 格式: {pdf_path}"
        }

    # ===== 2. 动态导入 PyMuPDF =====
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        return {
            "status": "error",
            "image_files": [],
            "error": f"PyMuPDF (fitz) 未安装。请运行: pip install pymupdf\n详细错误: {str(e)}"
        }

    # ===== 3. 规范化页码参数 =====
    if isinstance(page_numbers, int):
        page_numbers = [page_numbers]

    if not page_numbers:
        return {
            "status": "error",
            "image_files": [],
            "error": "未指定页码"
        }

    # ===== 4. 打开 PDF =====
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
    except Exception as e:
        return {
            "status": "error",
            "image_files": [],
            "error": f"无法打开 PDF: {str(e)}"
        }

    # ===== 5. 准备输出目录 =====
    if output_dir is None:
        output_dir = get_sandbox_root()

    # 创建图片子目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(pdf_path).stem
    image_dir = os.path.join(output_dir, f"pdf_images_{base_name}_{timestamp}")
    os.makedirs(image_dir, exist_ok=True)

    # ===== 6. 渲染页面 =====
    image_files = []
    failed_pages = []
    warnings = []

    # 计算缩放矩阵
    # 默认使用 1.5x 缩放以平衡清晰度和大小
    effective_zoom = zoom if zoom is not None else 1.5
    if zoom is None and dpi != 200:
        # 如果指定了 DPI 但没有指定 zoom，使用 DPI 计算
        scale = dpi / 72.0
        effective_zoom = scale

    mat = fitz.Matrix(effective_zoom, effective_zoom)

    for page_num in page_numbers:
        # 页码有效性检查 (1-indexed 转 0-indexed)
        page_idx = page_num - 1

        if page_idx < 0 or page_idx >= total_pages:
            failed_pages.append(page_num)
            warnings.append(f"页码 {page_num} 超出范围 (1-{total_pages})")
            continue

        try:
            page = doc[page_idx]

            # 渲染为 pixmap
            pix = page.get_pixmap(matrix=mat)

            # 转换为 PIL Image
            img_data = pix.tobytes("png")
            pil_image = Image.open(BytesIO(img_data))

            # 转换为 RGB (JPEG 不支持透明度)
            if pil_image.mode in ('RGBA', 'P'):
                pil_image = pil_image.convert('RGB')
            elif pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # 自动压缩至 < 5MB
            if Image is not None:
                compressed_data = compress_image_to_size(
                    pil_image,
                    max_size_mb=max_size_mb,
                    initial_quality=85,
                    min_quality=60
                )
            else:
                # 如果没有 PIL，使用默认质量
                buffer = BytesIO()
                pil_image.save(buffer, format='JPEG', quality=85)
                compressed_data = buffer.getvalue()

            # 生成输出文件名 (JPG 格式)
            output_filename = f"page_{page_num:04d}.jpg"
            output_path = os.path.join(image_dir, output_filename)

            # 保存压缩后的图片
            with open(output_path, 'wb') as f:
                f.write(compressed_data)

            image_files.append(os.path.abspath(output_path))

        except Exception as e:
            failed_pages.append(page_num)
            warnings.append(f"页面 {page_num} 渲染失败: {str(e)}")

    doc.close()

    # ===== 7. 构造返回结果 =====
    status = "success"
    if failed_pages:
        status = "partial" if image_files else "error"

    result = {
        "status": status,
        "image_files": image_files,
        "page_count": len(image_files),
        "effective_zoom": effective_zoom,
        "image_directory": os.path.abspath(image_dir) if image_files else None,
        "format": "JPEG",
        "max_size_constraint": f"{max_size_mb}MB"
    }

    if failed_pages:
        result["failed_pages"] = failed_pages

    if warnings:
        result["warning"] = "; ".join(warnings)

    if status == "error":
        result["error"] = f"所有页面渲染失败。失败页码: {failed_pages}"

    return result


def parse_page_ranges(page_spec: str) -> List[int]:
    """
    解析页码规格字符串为页码列表。

    支持格式:
    - "5" -> [5]
    - "1,3,5" -> [1, 3, 5]
    - "1-5" -> [1, 2, 3, 4, 5]
    - "1-3,5,7-9" -> [1, 2, 3, 5, 7, 8, 9]
    """
    pages = []

    for part in page_spec.split(','):
        part = part.strip()
        if '-' in part:
            # 范围格式: "start-end"
            try:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                pages.extend(range(start, end + 1))
            except ValueError:
                raise ValueError(f"无效的页码范围: {part}")
        else:
            # 单个页码
            try:
                pages.append(int(part))
            except ValueError:
                raise ValueError(f"无效的页码: {part}")

    # 去重并排序
    return sorted(set(pages))


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="将 PDF 页面渲染为压缩后的高分辨率 JPG 图片 (自动控制在 5MB 以内)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 渲染单页 (默认 1.5x 缩放, 自动压缩至 <5MB)
  python render_pdf_page.py /path/to/guideline.pdf --pages 5

  # 渲染多页
  python render_pdf_page.py /path/to/guideline.pdf --pages 1,3,5

  # 渲染页面范围
  python render_pdf_page.py /path/to/guideline.pdf --pages 10-15

  # 指定缩放 (1.5 = 150%, 2.0 = 200%)
  python render_pdf_page.py /path/to/guideline.pdf --pages 20 --zoom 1.5

  # 指定输出目录
  python render_pdf_page.py /path/to/guideline.pdf --pages 1-5 -o /custom/output

说明:
  - 输出格式固定为 JPEG
  - 自动压缩至 < 5MB 以适应 VLM 输入限制
  - 默认使用 1.5x 缩放平衡清晰度与文件大小
        """
    )

    parser.add_argument(
        "pdf_path",
        help="PDF 文件的绝对路径"
    )
    parser.add_argument(
        "--pages", "-p",
        required=True,
        help="页码规格 (如: 5, 1,3,5, 10-15)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="输出目录 (默认: SANDBOX_ROOT 或 workspace/sandbox)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="渲染分辨率 (默认: 200, 已废弃，请使用 --zoom)"
    )
    parser.add_argument(
        "--zoom",
        type=float,
        default=1.5,
        help="缩放因子 (默认: 1.5, 建议范围: 1.0-2.0)"
    )
    parser.add_argument(
        "--max-size",
        type=float,
        default=5.0,
        help="最大文件大小限制 MB (默认: 5.0)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果"
    )

    args = parser.parse_args()

    # 解析页码
    try:
        page_numbers = parse_page_ranges(args.pages)
    except ValueError as e:
        print(f"❌ 页码解析错误: {e}", file=sys.stderr)
        sys.exit(1)

    result = render_pdf_pages(
        pdf_path=args.pdf_path,
        page_numbers=page_numbers,
        output_dir=args.output_dir,
        dpi=args.dpi,
        zoom=args.zoom,
        max_size_mb=args.max_size
    )

    if args.json:
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "success":
            print(f"✅ 页面渲染成功")
            print(f"📁 图片目录: {result['image_directory']}")
            print(f"📄 生成图片数: {result['page_count']}")
            print(f"🖼️  格式: JPEG (自动压缩至 < {result['max_size_constraint']})")
            print(f"🔍 缩放: {result['effective_zoom']}x")
            for img_path in result['image_files']:
                size_mb = os.path.getsize(img_path) / (1024 * 1024)
                print(f"   - {img_path} ({size_mb:.2f}MB)")
        elif result["status"] == "partial":
            print(f"⚠️  部分页面渲染成功")
            print(f"📁 图片目录: {result['image_directory']}")
            print(f"📄 成功渲染: {result['page_count']} 页")
            print(f"❌ 失败页码: {result['failed_pages']}")
            if result.get('warning'):
                print(f"⚠️  警告: {result['warning']}")
        else:
            print(f"❌ 页面渲染失败: {result['error']}", file=sys.stderr)
            if result.get('warning'):
                print(f"⚠️  警告: {result['warning']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
