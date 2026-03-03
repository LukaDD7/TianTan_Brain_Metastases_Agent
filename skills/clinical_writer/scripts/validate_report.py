#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MDT Report Validator Skill

独立验证已存在的 MDT 报告文件是否符合临床书写规范。
"""

import os
import re
import json
from typing import Optional, Any, Dict

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

class ReportValidatorInput(BaseModel):
    """Report Validator 的输入参数"""

    file_path: str = Field(
        ...,
        description="待验证的 MDT 报告文件路径",
        examples=["workspace/cases/Case1/MDT_Report_20260303_143022.md"]
    )


# =============================================================================
# Skill 实现
# =============================================================================

class ReportValidator(BaseSkill[ReportValidatorInput]):
    """
    MDT 报告验证器 - 验证已存在的报告文件是否符合临床书写规范。
    """

    name = "validate_mdt_report"
    description = (
        "验证已存在的 MDT 报告文件是否符合临床书写规范。"
        "检查项目：指南引用格式 (Citation Pattern)、结构完整性、文件存在性。"
        "验证通过后方可作为正式医疗档案使用。"
    )
    input_schema_class = ReportValidatorInput

    def __init__(self):
        super().__init__()
        # 验证操作是本地 I/O，不需要重试
        self.retry_config.max_retries = 0

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

            # 验证规则
            errors = []

            # 规则 1: 指南引用校验
            citation_pattern = r"\[Citation:\s*[^,]+,\s*Page\s*\d+\]"
            if not re.search(citation_pattern, content, re.IGNORECASE):
                errors.append(
                    "未检测到合规的指南引用格式！"
                    "每项治疗建议后必须包含类似 '[Citation: NCCN_Melanoma.pdf, Page 42]' 的来源证据。"
                )

            # 规则 2: 结构完整性校验
            if "治疗" not in content and "建议" not in content:
                errors.append(
                    "报告结构不完整，缺少核心的'治疗建议'区块。"
                )

            # 构建结果
            result = {
                "file_path": args.file_path,
                "valid": len(errors) == 0,
                "errors": errors,
                "message": (
                    "✅ 验证通过！报告可作为正式医疗档案使用。"
                    if not errors
                    else f"❌ 发现 {len(errors)} 个问题，请修正后重新提交。"
                )
            }

            # 更新上下文 (如果提供)
            if context:
                context.set(f"validation_result_{args.file_path}", result)

            return json.dumps(result, ensure_ascii=False, indent=2)

        except SkillExecutionError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"验证失败：{str(e)}") from e


# =============================================================================
# CLI 入口 (向后兼容)
# =============================================================================

def main():
    """命令行入口 (向后兼容旧用法)"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="MDT Report Validator")
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
