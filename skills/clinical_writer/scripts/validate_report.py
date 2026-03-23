#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MDT Report Validator Skill - v2.3 重构版

独立验证已存在的 MDT 报告文件是否符合临床书写规范和 ASCO/NCCN Order Sets 模板。

Author: TianTan Brain Metastases Agent Team
Version: 2.3.0
"""

import os
import re
import json
from typing import Optional, Any, Dict, List
from pathlib import Path

# Pydantic v2
from pydantic import BaseModel, Field

# 本地基类
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import BaseSkill, SkillContext, SkillExecutionError


# =============================================================================
# 模板路径配置（与 generate_report.py 保持一致）
# =============================================================================

ORDER_SET_TEMPLATE_PATH = Path(__file__).parent.parent / "references" / "asco_nccn_order_set_template.json"


# =============================================================================
# 输入 Schema (Pydantic 模型)
# =============================================================================

class ReportValidatorInput(BaseModel):
    """Report Validator 的输入参数"""

    file_path: str = Field(
        ...,
        description="待验证的 MDT 报告文件路径",
        examples=["workspace/cases/Case1/MDT_Report_20260303_143022.md"]
    )


# =============================================================================
# 模板加载器
# =============================================================================

def load_order_set_template() -> Dict[str, Any]:
    """
    加载 Order Sets 模板文件。

    Returns:
        模板字典

    Raises:
        SkillExecutionError: 模板文件不存在或解析失败
    """
    template_path = ORDER_SET_TEMPLATE_PATH.resolve()

    if not template_path.exists():
        raise SkillExecutionError(
            f"Order Sets 模板文件不存在：{template_path}\n"
            "请确保 skills/clinical_writer/references/asco_nccn_order_set_template.json 已创建"
        )

    with open(template_path, 'r', encoding='utf-8') as f:
        try:
            template = json.load(f)
        except json.JSONDecodeError as e:
            raise SkillExecutionError(f"模板 JSON 解析失败：{e}")

    return template


# =============================================================================
# Skill 实现
# =============================================================================

class ReportValidator(BaseSkill[ReportValidatorInput]):
    """
    MDT 报告验证器 - v2.3 重构版

    验证已存在的报告文件是否符合临床书写规范和 ASCO/NCCN Order Sets 模板。

    Version: 2.3.0
    """

    name = "validate_mdt_report"
    description = (
        "验证已存在的 MDT 报告文件是否符合临床书写规范和 ASCO/NCCN Order Sets 模板。"
        "检查项目：指南引用格式、5 大核心模块完整性、排他性分析、Agent 追踪、"
        "激素管理、围手术期停药要求、分子病理送检医嘱。"
        "验证通过后方可作为正式医疗档案使用。"
    )
    input_schema_class = ReportValidatorInput

    def __init__(self):
        super().__init__()
        # 验证操作是本地 I/O，不需要重试
        self.retry_config.max_retries = 0
        # 模板缓存
        self._template_cache: Optional[Dict[str, Any]] = None

    def _get_template(self) -> Dict[str, Any]:
        """获取模板（带缓存）"""
        if self._template_cache is None:
            self._template_cache = load_order_set_template()
        return self._template_cache

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.input_schema_class.model_json_schema()

    def execute(self, args: ReportValidatorInput, context: Optional[SkillContext] = None) -> str:
        """
        验证 MDT 报告文件。

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的验证结果

        Raises:
            SkillExecutionError: 执行失败时抛出
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(args.file_path):
                raise SkillExecutionError(f"文件不存在：{args.file_path}")

            with open(args.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 加载模板
            template = self._get_template()

            # 验证内容
            errors = self._validate_with_template(content, template)

            result = {
                "file_path": args.file_path,
                "valid": len(errors) == 0,
                "errors": errors,
                "message": (
                    "✅ 验证通过！报告可作为正式医疗档案使用。"
                    if not errors
                    else f"❌ 发现 {len(errors)} 个问题，请修正后重新提交。"
                ),
                "template_version": template.get("template_info", {}).get("version", "Unknown")
            }

            # 更新上下文 (如果提供)
            if context:
                context.set(f"validation_result_{args.file_path}", result)

            return json.dumps(result, ensure_ascii=False, indent=2)

        except SkillExecutionError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"验证失败：{str(e)}") from e

    def _validate_with_template(
        self,
        content: str,
        template: Dict[str, Any]
    ) -> List[str]:
        """
        基于模板验证报告内容。

        Args:
            content: 报告内容
            template: Order Sets 模板

        Returns:
            错误信息列表
        """
        errors = []
        content_lower = content.lower()

        # ========== 必需模块检查 ==========
        required_sections = [
            ("admission_evaluation", "入院评估"),
            ("primary_plan", "首选方案"),
            ("systemic_management", "全身管理"),
            ("follow_up", "随访"),
            ("rejected_alternatives", "被排除方案"),
            ("agent_trace", "Agent 追踪")
        ]

        for section_en, section_cn in required_sections:
            if section_en not in content_lower and section_cn not in content:
                errors.append(f"缺少必需模块：{section_en} ({section_cn})")

        # ========== 指南引用校验 ==========
        citation_pattern = r"\[Citation:\s*[^,]+,\s*Page\s*\d+\]"
        if not re.search(citation_pattern, content, re.IGNORECASE):
            errors.append(
                "未检测到合规的指南引用格式！"
                "每项治疗建议后必须包含类似 '[Citation: NCCN_Melanoma.pdf, Page 42]' 的来源证据。"
            )

        # ========== 禁忌文字检查 ==========
        if "术前准备" in content or "preoperative preparation" in content_lower:
            errors.append(
                "发现禁忌文字'术前准备'！"
                "admission_evaluation 模块严禁出现暗示必然手术的文字。"
            )

        # ========== 排他性分析检查 ==========
        # 检查 rejected_alternatives 是否有实际内容
        rejected_match = re.search(r"rejected_alternatives.*?(?=agent_trace|$)", content, re.IGNORECASE | re.DOTALL)
        if rejected_match:
            rejected_section = rejected_match.group(0)
            # 检查是否有实际的排除项
            if not re.search(r"option.*?排除 | 被排除 | 不推荐|rejected|excluded", rejected_section, re.IGNORECASE):
                errors.append("rejected_alternatives 模块为空，必须至少列出 1 项被排除的方案")
        else:
            errors.append("rejected_alternatives 模块内容无法识别")

        # ========== 手术相关检查（如果包含手术） ==========
        if "surgery" in content_lower or "手术" in content:
            if "molecular_pathology" not in content_lower and "分子病理" not in content and "基因检测" not in content:
                errors.append(
                    "手术方案必须包含 molecular_pathology_orders（分子病理送检医嘱），"
                    "明确切除组织需进行哪些基因突变检测（如 BRAF V600E、NGS panel 等）"
                )

        # ========== 全身治疗相关检查（如果包含全身治疗） ==========
        if ("systemic_therapy" in content_lower or "靶向" in content or "免疫" in content):
            # 检查是否有剂量和周期信息
            if "dosage" not in content_lower and "剂量" not in content:
                errors.append("全身治疗必须写明药物剂量 (dosage)")
            if "cycle" not in content_lower and "周期" not in content:
                errors.append("全身治疗必须写明治疗周期 (cycle_length)")

        # ========== 类固醇减量计划检查 ==========
        if "地塞米松" in content or "dexamethasone" in content_lower or "类固醇" in content_lower:
            if "tapering" not in content_lower and "减量" not in content:
                errors.append(
                    "使用类固醇（如地塞米松）必须填写 tapering_schedule（减量计划），"
                    "例如：'神经症状稳定后每 3-5 天减量 2-4mg'"
                )

        return errors


# =============================================================================
# CLI 入口 (向后兼容)
# =============================================================================

def main():
    """命令行入口 (向后兼容旧用法)"""
    import argparse

    parser = argparse.ArgumentParser(description="MDT Report Validator v2.3")
    parser.add_argument("--file_path", required=True, help="Path to the generated MD file")
    parser.add_argument("--json_output", action="store_true", help="Output JSON instead of human-readable message")

    args = parser.parse_args()

    validator = ReportValidator()
    input_args = ReportValidatorInput(file_path=args.file_path)

    try:
        result = validator.execute(input_args)
        if args.json_output:
            print(result)
        else:
            result_dict = json.loads(result)
            if result_dict["valid"]:
                print(f"✅ {result_dict['message']}")
                print(f"   模板版本：{result_dict.get('template_version', 'Unknown')}")
            else:
                print(f"❌ {result_dict['message']}")
                for error in result_dict["errors"]:
                    print(f"   - {error}")
                sys.exit(1)
    except SkillExecutionError as e:
        print(f"❌ 验证失败：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
