#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全链路冒烟测试脚本 (Smoke Test for Skills)

测试目标：
1. OncoKB Query - 验证 API 调用和响应解析
2. PubMed Search - 验证文献检索和摘要抓取
3. Clinical Writer - 验证 Order Sets 模板验证规则

注意：本测试使用真实 API 调用，请确保环境变量已设置：
- ONCOKB_API_KEY
- PUBMED_EMAIL

运行方式：
    python scripts/smoke_test_skills.py
"""

import os
import sys
import json
import time

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.skill import SkillContext, SkillExecutionError, SkillValidationError


# =============================================================================
# 测试工具函数
# =============================================================================

def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(test_name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {test_name}")
    if details:
        print(f"       {details}")


# =============================================================================
# Test 1: OncoKB Query
# =============================================================================

def test_oncokb_query():
    """测试 OncoKB 基因变异查询"""
    print_header("Test 1: OncoKB Query Skill")

    from skills.oncokb_query.scripts.query_variant import OncoKBQuery, OncoKBQueryInput, QueryType

    # 检查环境变量
    api_key = os.environ.get("ONCOKB_API_KEY")
    if not api_key:
        print_result("环境变量检查", False, "ONCOKB_API_KEY 未设置，跳过测试")
        return False

    print_result("环境变量检查", True, "ONCOKB_API_KEY 已设置")

    # 创建 Skill 实例和上下文
    skill = OncoKBQuery()
    context = SkillContext(session_id="smoke_test_oncokb")

    # 测试用例：EGFR L858R
    input_args = OncoKBQueryInput(
        query_type=QueryType.VARIANT,
        hugo_symbol="EGFR",
        variant="L858R",
        tumor_type="Non-Small Cell Lung Cancer",
        include_evidence=True
    )

    print("正在查询 OncoKB API (EGFR L858R in NSCLC)...")

    try:
        result_json = skill.execute_with_retry(input_args.model_dump(), context=context)
        result = json.loads(result_json)

        # 验证响应结构
        if not result.get("success"):
            print_result("API 响应", False, "success 字段为 false")
            return False

        print_result("API 响应", True, "success = true")

        # 检查 data 字段
        data = result.get("data", {})

        # OncoKB API 响应结构可能有所不同，需要检查多种可能
        # 可能的字段：oncogenic, oncogenicity, mutationEffect
        oncogenicity = (
            data.get("oncogenicity") or
            data.get("oncogenic") or
            data.get("mutationEffect") or
            ""
        )

        # 如果是字典，提取 text 字段
        if isinstance(oncogenicity, dict):
            oncogenicity = oncogenicity.get("text") or oncogenicity.get("label") or str(oncogenicity)

        if not oncogenicity:
            # 不一定非要 oncogenicity，检查是否有治疗推荐
            treatments = data.get("treatments", [])
            if len(treatments) == 0:
                print_result("致癌性判定/治疗推荐", False, "oncogenicity 字段为空且无治疗推荐")
                # 打印完整响应以便调试
                print(f"   调试信息 - 完整响应：{json.dumps(data, indent=2)[:500]}...")
                return False
            else:
                oncogenicity = "Unknown (但有治疗推荐)"

        print_result("致癌性判定", True, f"oncogenicity = {oncogenicity}")

        # 验证治疗推荐
        treatments = data.get("treatments", [])
        if len(treatments) == 0:
            print_result("治疗推荐", False, "未找到治疗推荐")
        else:
            print_result("治疗推荐", True, f"找到 {len(treatments)} 条治疗推荐")

        # 打印摘要
        print("\n📌 OncoKB 响应摘要:")
        gene_info = data.get("gene", {})
        if isinstance(gene_info, dict):
            print(f"   基因：{gene_info.get('hugoSymbol', 'Unknown')}")
        else:
            print(f"   基因：{gene_info}")

        variant_info = data.get("variant", {})
        if isinstance(variant_info, dict):
            print(f"   变异：{variant_info.get('name', 'Unknown')}")
        else:
            print(f"   变异：{variant_info}")

        print(f"   致癌性：{oncogenicity}")
        print(f"   治疗推荐数：{len(treatments)}")

        # 验证 SkillContext 记录
        history = context.get_history()
        if len(history) == 0:
            print_result("Context 记录", False, "调用历史为空")
            return False

        print_result("Context 记录", True, f"记录 {len(history)} 次调用")

        return True

    except SkillExecutionError as e:
        print_result("API 调用", False, f"SkillExecutionError: {e}")
        return False
    except Exception as e:
        print_result("API 调用", False, f"Unexpected error: {e}")
        return False


# =============================================================================
# Test 2: PubMed Search
# =============================================================================

def test_pubmed_search():
    """测试 PubMed 文献检索"""
    print_header("Test 2: PubMed Search Skill")

    from skills.pubmed_search.scripts.search_articles import PubMedSearch, PubMedSearchInput, QueryType

    # 检查环境变量
    pubmed_email = os.environ.get("PUBMED_EMAIL")
    if not pubmed_email:
        print_result("环境变量检查", False, "PUBMED_EMAIL 未设置，跳过测试")
        return False

    print_result("环境变量检查", True, "PUBMED_EMAIL 已设置")

    # 创建 Skill 实例和上下文
    skill = PubMedSearch()
    context = SkillContext(session_id="smoke_test_pubmed")

    # 测试用例：Melanoma Brain Metastases Immunotherapy
    input_args = PubMedSearchInput(
        query_type=QueryType.SEARCH,
        keywords="Melanoma Brain Metastases Immunotherapy",
        max_results=2,
        sort="relevance"
    )

    print("正在检索 PubMed (Melanoma Brain Metastases Immunotherapy)...")
    print("注意：PubMed API 可能有网络波动，最多重试 3 次...")

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            result_json = skill.execute_with_retry(input_args.model_dump(), context=context)
            result = json.loads(result_json)

            # 验证响应结构
            if not result.get("success"):
                print_result("API 响应", False, "success 字段为 false")
                return False

            print_result("API 响应", True, "success = true")

            # 验证文献列表
            data = result.get("data", {})
            articles = data.get("articles", [])

            if len(articles) == 0:
                print_result("文献检索", False, "未找到任何文献")
                return False

            print_result("文献检索", True, f"找到 {len(articles)} 篇文献")

            # 打印第一篇文献摘要
            first_article = articles[0]
            print("\n📌 第一篇文献摘要:")
            print(f"   PMID: {first_article.get('pmid', 'Unknown')}")
            print(f"   标题：{first_article.get('title', 'No Title')[:80]}...")
            print(f"   期刊：{first_article.get('journal', 'Unknown')}")
            print(f"   年份：{first_article.get('year', 'Unknown')}")

            # 验证摘要内容
            abstract = first_article.get("abstract", "")
            if "No Abstract" in str(abstract):
                print_result("摘要内容", False, "无可用摘要")
            else:
                print_result("摘要内容", True, f"摘要长度 = {len(abstract)} 字符")

            # 验证 SkillContext 记录
            history = context.get_history()
            if len(history) == 0:
                print_result("Context 记录", False, "调用历史为空")
                return False

            print_result("Context 记录", True, f"记录 {len(history)} 次调用")

            return True

        except SkillExecutionError as e:
            last_error = e
            if "SSL" in str(e) or "Connection" in str(e):
                print(f"   尝试 {attempt + 1}/{max_retries}: SSL/连接错误，等待后重试...")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                print_result("API 调用", False, f"SkillExecutionError: {e}")
                return False
        except Exception as e:
            last_error = e
            print_result("API 调用", False, f"Unexpected error: {e}")
            return False

    # 所有重试失败
    print_result("API 调用", False, f"所有 {max_retries} 次重试失败：{last_error}")
    return False


# =============================================================================
# Test 3: Clinical Writer 模板验证 (故意传入不合规内容)
# =============================================================================

def test_clinical_writer_validation():
    """测试临床报告验证规则 - 故意传入不合规内容"""
    print_header("Test 3: Clinical Writer Template Validation")

    from skills.clinical_writer.scripts.generate_report import MDTReportGenerator, MDTReportInput
    from skills.clinical_writer.scripts.validate_report import ReportValidator, ReportValidatorInput

    # 创建 Skill 实例
    generator = MDTReportGenerator()
    validator = ReportValidator()
    context = SkillContext(session_id="smoke_test_clinical")

    # ========== 测试用例 A: 使用违禁词"术前准备" ==========
    print("\n--- 测试用例 A: 使用违禁词'术前准备' ---")

    invalid_report_a = """
## 入院评估
- performance_status: KPS ≥70
- neurological_status: 神志清楚

## 术前准备
患者拟行开颅手术，完善术前检查...

## 首选治疗方案
- modality: surgery
"""

    # 直接调用验证方法
    template = generator._get_template()
    errors_a = generator._validate_with_template(invalid_report_a, template)

    # 应该检测到"术前准备"违禁词
    preop_error_found = any("术前准备" in err for err in errors_a)
    print_result("违禁词检测 (术前准备)", preop_error_found,
                 f"发现 {len(errors_a)} 个错误：{errors_a[:2]}")

    # ========== 测试用例 B: 缺少 rejected_alternatives 模块 ==========
    print("\n--- 测试用例 B: 缺少 rejected_alternatives 模块 ---")

    invalid_report_b = """
## 入院评估
- performance_status: KPS ≥70

## 首选治疗方案
- modality: systemic_therapy

## 随访计划
- imaging: MRI every 3 months
"""

    errors_b = generator._validate_with_template(invalid_report_b, template)

    # 应该检测到缺少 rejected_alternatives
    rejected_error_found = any("rejected" in err.lower() or "排除" in err for err in errors_b)
    print_result("缺失模块检测 (rejected_alternatives)", rejected_error_found,
                 f"发现 {len(errors_b)} 个错误：{errors_b[:2]}")

    # ========== 测试用例 C: 缺少指南引用 ==========
    print("\n--- 测试用例 C: 缺少指南引用格式 ---")

    invalid_report_c = """
## 入院评估
- performance_status: KPS ≥70

## 首选治疗方案
- modality: surgery
- rationale: 患者适合手术

## 被排除方案
- option: 放疗
  reason: 不适合

## Agent Trace
skills_called: []
"""

    errors_c = generator._validate_with_template(invalid_report_c, template)

    # 应该检测到缺少 Citation
    citation_error_found = any("citation" in err.lower() or "引用" in err for err in errors_c)
    print_result("指南引用检测 (Citation)", citation_error_found,
                 f"发现 {len(errors_c)} 个错误：{errors_c[:2]}")

    # ========== 测试用例 D: 合规报告（应通过验证） ==========
    print("\n--- 测试用例 D: 合规报告（应通过验证） ---")

    valid_report = """
## admission_evaluation 入院评估与一般治疗
- performance_status: KPS ≥70
- neurological_status: 神志清楚
- baseline_labs: ["血常规", "肝肾功能"]

## primary_plan 首选治疗方案
- modality: systemic_therapy
- rationale: 患者适合全身治疗
- evidence_citation: [Citation: NCCN_NSCLC.pdf, Page 12]
- systemic_therapy:
  - regimen_name: Osimertinib
    drugs: [{drug_name: Osimertinib, dosage: 80mg}]

## systemic_management 后续治疗与全身管理
- targeted_therapy: Osimertinib

## follow_up 全程管理与随访计划
- imaging_schedule: [{modality: MRI Brain, frequency: 每 3 个月, duration: 前 2 年}]
- clinical_visit_schedule: 每周期治疗前复诊
- toxicity_monitoring: [{parameter: 肝功能，frequency: 每周期前}]

## rejected_alternatives 被排除的治疗方案
- rejected_options:
  - option: 手术切除
    reason: 患者不适合手术
    evidence_level: NCCN Category 2A
    citation: {source: NCCN CNS Cancers v3.2024}

## agent_trace
- skills_called: []
- evidence_sources: []
- reasoning_confidence: High
"""

    errors_d = generator._validate_with_template(valid_report, template)

    # 合规报告应通过验证
    passed = len(errors_d) == 0
    print_result("合规报告验证", passed,
                 f"错误数：{len(errors_d)}" if not passed else "验证通过")

    # ========== 测试用例 E: 使用 ReportValidator 验证文件 ==========
    print("\n--- 测试用例 E: ReportValidator 文件验证 ---")

    import tempfile
    import os

    # 创建一个临时文件（包含违禁词）
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(invalid_report_a)
        temp_path = f.name

    try:
        input_args = ReportValidatorInput(file_path=temp_path)
        result_json = validator.execute(input_args, context=context)
        result = json.loads(result_json)

        # 应该验证失败
        if result.get("valid"):
            print_result("ReportValidator 文件验证", False, "应验证失败但通过了")
        else:
            errors = result.get("errors", [])
            print_result("ReportValidator 文件验证", True, f"正确拦截不合规报告：{len(errors)} 个错误")
    finally:
        os.unlink(temp_path)

    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("  Clinical Writer 验证测试总结")
    print("=" * 70)

    all_passed = preop_error_found and rejected_error_found and citation_error_found and passed
    return all_passed


# =============================================================================
# 主函数
# =============================================================================

def main():
    """运行所有冒烟测试"""
    print("\n" + "=" * 70)
    print("  🏥 TianTan Brain Metastases Agent - 全链路冒烟测试")
    print("  Version: v2.4.0")
    print("=" * 70)

    results = {
        "OncoKB Query": test_oncokb_query(),
        "PubMed Search": test_pubmed_search(),
        "Clinical Writer Validation": test_clinical_writer_validation()
    }

    # 打印汇总
    print_header("📊 测试结果汇总")

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"[{status}] {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 所有测试通过！系统已准备好进行 10 个真实 Case 的端到端测试")
    else:
        print("  ⚠️  部分测试失败，请检查错误原因并修复")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
