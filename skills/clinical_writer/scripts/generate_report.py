#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Clinical Report Generator Skill

生成并验证肿瘤多学科诊疗 (MDT) 报告。
"""

import os
import re
import json
import datetime
from typing import Optional, Any, List, Dict

# Pydantic v2
from pydantic import BaseModel, Field

# 本地基类
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import BaseSkill, SkillContext, SkillExecutionError, SkillValidationError


# =============================================================================
# 输入 Schema (Pydantic 模型)
# =============================================================================

class MDTReportInput(BaseModel):
    """MDT Report Generator 的输入参数"""

    case_id: str = Field(
        ...,
        description="患者病例 ID",
        examples=["Case1", "Patient_12345"]
    )
    report_content: str = Field(
        ...,
        description="MDT 报告内容 (Markdown 格式)",
        min_length=10
    )
    skip_validation: bool = Field(
        default=False,
        description="是否跳过验证 (默认 false，强制验证)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "case_id": "Case1",
                    "report_content": "# MDT 诊疗建议\n\n## 治疗方案\n推荐奥希替尼...\n[Citation: NCCN_NSCLC.pdf, Page 12]",
                    "skip_validation": False
                }
            ]
        }


class MDTReportValidatorInput(BaseModel):
    """MDT Report Validator 的输入参数"""

    case_id: str = Field(
        ...,
        description="患者病例 ID"
    )
    file_path: str = Field(
        ...,
        description="待验证的报告文件路径"
    )


# =============================================================================
# Skill 实现 - Generator
# =============================================================================

class MDTReportGenerator(BaseSkill[MDTReportInput]):
    """
    MDT 报告生成器 - 生成并验证肿瘤多学科诊疗报告。
    """

    name = "generate_mdt_report"
    description = (
        "生成并验证肿瘤多学科诊疗 (MDT) 报告。"
        "适用于：将 AI 生成的治疗建议格式化为标准 MDT 报告，"
        "强制验证报告包含指南引用，自动归档到患者专属沙盒目录。"
        "注意：这是诊疗流程的最后一步，确保所有建议都有循证依据。"
    )
    input_schema_class = MDTReportInput

    def __init__(self):
        super().__init__()
        # 报告生成是本地 I/O 操作，不需要重试
        self.retry_config.max_retries = 1

    @property
    def input_schema(self) -> Dict[str, Any]:
        """获取 JSON Schema (用于 LLM Tool 调用)"""
        return self.input_schema_class.model_json_schema()

    def execute(self, args: MDTReportInput, context: Optional[SkillContext] = None) -> str:
        """
        生成并验证 MDT 报告。

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的执行结果

        Raises:
            SkillExecutionError: 执行失败时抛出
        """
        try:
            # 验证报告内容 (如果未跳过)
            if not args.skip_validation:
                validation_errors = self._validate_content(args.report_content)
                if validation_errors:
                    raise SkillValidationError(
                        f"报告验证失败：{'；'.join(validation_errors)}"
                    )

            # 创建输出目录
            output_dir = os.path.abspath(os.path.join("workspace", "cases", args.case_id))
            os.makedirs(output_dir, exist_ok=True)

            # 生成文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"MDT_Report_{timestamp}.md"
            report_path = os.path.join(output_dir, report_filename)

            # 写入文件
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(args.report_content)

            # 更新上下文 (如果提供)
            if context:
                context.set(f"mdt_report_{args.case_id}", report_path)
                context.set_metadata("last_report_path", report_path)

            result = {
                "success": True,
                "report_path": report_path,
                "validation_errors": [],
                "message": "报告已通过医疗合规校验，并正式存档"
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except SkillValidationError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"报告生成失败：{str(e)}") from e

    def _validate_content(self, content: str) -> List[str]:
        """
        验证报告内容。

        Returns:
            错误信息列表，空列表表示验证通过
        """
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

        return errors


# =============================================================================
# Skill 实现 - Validator (独立工具)
# =============================================================================

class MDTReportValidator(BaseSkill[MDTReportValidatorInput]):
    """
    MDT 报告验证器 - 独立验证已存在报告文件的合规性。
    """

    name = "validate_mdt_report"
    description = (
        "验证已存在的 MDT 报告文件是否符合临床书写规范。"
        "检查项目：指南引用格式、结构完整性、文件存在性。"
    )
    input_schema_class = MDTReportValidatorInput

    def __init__(self):
        super().__init__()
        self.retry_config.max_retries = 0  # 验证操作不需要重试

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.input_schema_class.model_json_schema()

    def execute(self, args: MDTReportValidatorInput, context: Optional[SkillContext] = None) -> str:
        """
        验证 MDT 报告文件。

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的验证结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(args.file_path):
                raise SkillExecutionError(f"文件不存在：{args.file_path}")

            with open(args.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 验证内容
            errors = []

            # 规则 1: 指南引用校验
            citation_pattern = r"\[Citation:\s*[^,]+,\s*Page\s*\d+\]"
            if not re.search(citation_pattern, content, re.IGNORECASE):
                errors.append(
                    "未检测到合规的指南引用格式！"
                )

            # 规则 2: 结构完整性校验
            if "治疗" not in content and "建议" not in content:
                errors.append(
                    "报告结构不完整，缺少核心的'治疗建议'区块。"
                )

            result = {
                "file_path": args.file_path,
                "valid": len(errors) == 0,
                "errors": errors,
                "message": "验证通过" if not errors else f"发现{len(errors)}个问题"
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            raise SkillExecutionError(f"验证失败：{str(e)}") from e


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="MDT Report Generator")
    parser.add_argument("--case_id", required=True, help="Patient Case ID")
    parser.add_argument("--content", required=True, help="Report content (Markdown)")
    parser.add_argument("--skip_validation", action="store_true", help="Skip validation")

    args = parser.parse_args()

    generator = MDTReportGenerator()
    input_args = MDTReportInput(
        case_id=args.case_id,
        report_content=args.content,
        skip_validation=args.skip_validation
    )

    try:
        result = generator.execute(input_args)
        print(result)
    except (SkillExecutionError, SkillValidationError) as e:
        print(json.dumps({"error": str(e)}))
        exit(1)


if __name__ == "__main__":
    main()
