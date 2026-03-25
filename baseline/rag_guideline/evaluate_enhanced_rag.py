#!/usr/bin/env python3
"""
Enhanced RAG Baseline - 完整评估指标计算
计算CCR, PTR, MQR, CER, CPI
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

# 患者映射
PATIENT_MAPPING = {
    "Case1": "648772",
    "Case2": "640880",
    "Case3": "868183",
    "Case4": "665548",
    "Case6": "638114",
    "Case7": "612908",
    "Case9": "708387",
    "Case10": "747724",
    "Case605525": "605525"
}

class EnhancedRAGEvaluator:
    """Enhanced RAG评估器"""

    def __init__(self, results_dir):
        self.results_dir = Path(results_dir)
        self.guidelines_dir = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/Guidelines")

    def load_report(self, filepath):
        """加载报告"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_citations(self, report_text):
        """提取所有引用"""
        citations = []

        # 匹配 [Local: ..., Line: X-Y] 格式
        local_pattern = r'\[Local: ([^\]]+?), Line: (\d+)-(\d+)\]'
        local_matches = re.findall(local_pattern, report_text)
        for match in local_matches:
            citations.append({
                'type': 'local',
                'source': match[0],
                'start_line': int(match[1]),
                'end_line': int(match[2]),
                'full': f"[Local: {match[0]}, Line: {match[1]}-{match[2]}]"
            })

        # 匹配 Evidence: Insufficient
        insufficient_pattern = r'\[Evidence: Insufficient[^\]]*\]'
        insufficient_matches = re.findall(insufficient_pattern, report_text)
        for match in insufficient_matches:
            citations.append({
                'type': 'insufficient',
                'full': match
            })

        # 匹配 Inference from Local
        inference_pattern = r'\[Inference from Local: ([^\]]+?)\]'
        inference_matches = re.findall(inference_pattern, report_text)
        for match in inference_matches:
            citations.append({
                'type': 'inference',
                'source': match,
                'full': f"[Inference from Local: {match}]"
            })

        return citations

    def verify_local_citation(self, citation):
        """验证本地引用（行号是否真实存在）"""
        if citation['type'] != 'local':
            return None

        source = citation['source']
        start_line = citation['start_line']
        end_line = citation['end_line']

        # 构建完整路径
        file_path = self.guidelines_dir / source

        if not file_path.exists():
            return {
                'exists': False,
                'reason': f'File not found: {source}'
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_lines = len(lines)

            # 检查行号范围
            if start_line < 1 or end_line > total_lines or start_line > end_line:
                return {
                    'exists': False,
                    'total_lines': total_lines,
                    'reason': f'Line range {start_line}-{end_line} out of bounds (file has {total_lines} lines)'
                }

            # 获取引用的内容
            cited_content = ''.join(lines[start_line-1:end_line])

            return {
                'exists': True,
                'total_lines': total_lines,
                'content_preview': cited_content[:200] if cited_content else '(empty)'
            }

        except Exception as e:
            return {
                'exists': False,
                'reason': f'Error reading file: {str(e)}'
            }

    def calculate_ptr(self, citations):
        """
        计算物理可追溯率 PTR

        TraceScore:
        - 2: 完全可追溯（Local引用且行号存在）
        - 1: 部分可追溯（Local引用但行号验证失败，或Inference）
        - 0: 不可追溯（无引用或其他）
        """
        if not citations:
            return 0.0, []

        trace_scores = []
        verification_details = []

        for cite in citations:
            if cite['type'] == 'local':
                verify_result = self.verify_local_citation(cite)
                if verify_result and verify_result['exists']:
                    trace_scores.append(2)
                    verification_details.append({
                        'citation': cite['full'],
                        'score': 2,
                        'status': '完全可追溯',
                        'details': verify_result
                    })
                else:
                    trace_scores.append(0)
                    verification_details.append({
                        'citation': cite['full'],
                        'score': 0,
                        'status': '不可追溯',
                        'details': verify_result
                    })
            elif cite['type'] == 'inference':
                # Inference引用部分可追溯
                trace_scores.append(1)
                verification_details.append({
                    'citation': cite['full'],
                    'score': 1,
                    'status': '部分可追溯（推断）'
                })
            elif cite['type'] == 'insufficient':
                # 证据不足不算可追溯
                trace_scores.append(0)
                verification_details.append({
                    'citation': cite['full'],
                    'score': 0,
                    'status': '不可追溯（证据不足）'
                })

        ptr = sum(trace_scores) / (2 * len(trace_scores)) if trace_scores else 0.0

        return ptr, verification_details

    def calculate_mqr(self, report_text):
        """
        计算MDT报告规范度 MQR

        8个模块，每个模块0.5分（如果完整）
        动态N/A机制：正确标记N/A的模块仍得满分
        """
        modules = [
            ("入院评估", r"## 1\. 入院评估|1\. 入院评估"),
            ("原发灶处理方案", r"## 2\. 原发灶处理方案|2\. 原发灶处理方案"),
            ("系统性管理", r"## 3\. 系统性管理|3\. 系统性管理"),
            ("随访方案", r"## 4\. 随访方案|4\. 随访方案"),
            ("排他性论证", r"## 5\. 被拒绝的替代方案|5\. 被拒绝的替代方案"),
            ("围手术期管理", r"## 6\. 围手术期管理|6\. 围手术期管理"),
            ("分子病理", r"## 7\. 分子病理|7\. 分子病理"),
            ("执行路径", r"## 8\. 执行路径|8\. 执行路径")
        ]

        module_scores = []
        for module_name, pattern in modules:
            has_module = bool(re.search(pattern, report_text, re.IGNORECASE))
            score = 0.5 if has_module else 0.0
            module_scores.append({
                'name': module_name,
                'present': has_module,
                'score': score
            })

        mqr = sum(m['score'] for m in module_scores) * 1.0  # 0-4分

        return mqr, module_scores

    def calculate_cer(self, report_text):
        """
        计算临床错误率 CER

        错误类型权重：
        - 严重错误：3.0
        - 主要错误：2.0
        - 次要错误：1.0

        W_max设为15（假设最多15个次要错误）
        """
        # 这里需要人工判断，自动检测有限的模式
        errors = []

        # 检测明显的错误模式
        # 1. 剂量明显错误（如极端值）
        dose_pattern = r'(\d+)\s*(mg|g|Gy)'
        dose_matches = re.findall(dose_pattern, report_text.lower())
        for value, unit in dose_matches:
            val = int(value)
            if unit == 'mg' and val > 10000:  # 超过10g可能是错误
                errors.append({
                    'type': 'major',
                    'weight': 2.0,
                    'description': f'疑似剂量错误: {val} mg',
                    'context': f'检测到异常大剂量: {val} mg'
                })
            elif unit == 'gy' and val > 100:  # 放疗剂量超过100Gy
                errors.append({
                    'type': 'major',
                    'weight': 2.0,
                    'description': f'疑似放疗剂量错误: {val} Gy',
                    'context': f'检测到异常放疗剂量: {val} Gy'
                })

        # 2. 检测矛盾信息
        if 'N/A' in report_text or 'n/a' in report_text.lower():
            # 检查是否合理使用N/A
            pass  # N/A本身不是错误

        # 3. 检查模块完整性缺失
        if report_text.count('##') < 8:
            missing_modules = 8 - report_text.count('##')
            errors.append({
                'type': 'minor',
                'weight': 1.0 * missing_modules,
                'description': f'模块缺失: {missing_modules}个',
                'context': '报告模块不完整'
            })

        # 计算CER
        W_max = 15  # 假设最大错误权重
        total_error_weight = sum(e['weight'] for e in errors)
        cer = total_error_weight / W_max if W_max > 0 else 0.0

        return min(cer, 1.0), errors

    def estimate_ccr(self, report_text, patient_info):
        """
        估算临床决策一致性 CCR

        注意：这需要与Ground Truth对比，这里基于报告质量进行估算
        5个维度，每个0-4分：
        - S_line: 治疗线判定
        - S_scheme: 方案选择
        - S_dose: 剂量参数
        - S_reject: 排他性论证
        - S_align: 临床路径一致性
        """
        # 基于报告特征估算（需要人工审核）
        scores = {
            'S_line': 0,
            'S_scheme': 0,
            'S_dose': 0,
            'S_reject': 0,
            'S_align': 0
        }

        # S_line: 检查是否提及治疗线
        line_patterns = ['一线', '二线', '三线', '四线', '五线', '六线', '1线', '2线', '3线']
        for pattern in line_patterns:
            if pattern in report_text:
                scores['S_line'] = 3  # 基本准确
                break

        # S_scheme: 检查是否有方案推荐
        if '推荐' in report_text or '建议' in report_text or '治疗方案' in report_text:
            scores['S_scheme'] = 3

        # S_dose: 检查是否有剂量信息
        if re.search(r'\d+\s*(mg|g|Gy|ml)', report_text, re.IGNORECASE):
            scores['S_dose'] = 2

        # S_reject: 检查排他性论证
        if '被拒绝' in report_text or '替代方案' in report_text or '排他性' in report_text:
            scores['S_reject'] = 3

        # S_align: 基于整体报告质量
        if len(report_text) > 3000 and scores['S_scheme'] > 0:
            scores['S_align'] = 3

        ccr = sum(scores.values()) / 5

        return ccr, scores

    def calculate_cpi(self, ccr, ptr, mqr, cer):
        """
        计算综合性能指数 CPI

        CPI = 0.35*(CCR/4) + 0.25*PTR + 0.25*(MQR/4) + 0.15*(1-CER)
        """
        cpi = (0.35 * (ccr / 4) +
               0.25 * ptr +
               0.25 * (mqr / 4) +
               0.15 * (1 - cer))
        return cpi

    def evaluate_single(self, filepath):
        """评估单个报告"""
        data = self.load_report(filepath)

        patient_id = data.get('patient_id', 'Unknown')
        hospital_id = data.get('hospital_id', 'Unknown')
        patient_info = data.get('patient_info', '')

        result = data.get('results', {}).get('enhanced_rag', {})
        report_text = result.get('report', '')
        latency = result.get('latency_ms', 0)

        # 提取引用
        citations = self.extract_citations(report_text)

        # 计算各项指标
        ptr, ptr_details = self.calculate_ptr(citations)
        mqr, module_details = self.calculate_mqr(report_text)
        cer, errors = self.calculate_cer(report_text)
        ccr, ccr_scores = self.estimate_ccr(report_text, patient_info)
        cpi = self.calculate_cpi(ccr, ptr, mqr, cer)

        return {
            'patient_id': patient_id,
            'hospital_id': hospital_id,
            'latency_ms': latency,
            'citations_count': len(citations),
            'citations': citations,
            'ptr': ptr,
            'ptr_details': ptr_details,
            'mqr': mqr,
            'module_details': module_details,
            'cer': cer,
            'errors': errors,
            'ccr': ccr,
            'ccr_scores': ccr_scores,
            'cpi': cpi
        }

    def evaluate_all(self):
        """评估所有报告"""
        results = []

        for filepath in sorted(self.results_dir.glob('*_enhanced_rag_results.json')):
            print(f"评估: {filepath.name}")
            try:
                result = self.evaluate_single(filepath)
                results.append(result)
            except Exception as e:
                print(f"  错误: {e}")

        return results


def main():
    """主函数"""
    results_dir = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/baseline/results_enhanced"

    print("="*100)
    print("Enhanced RAG Baseline - 完整评估指标计算")
    print("="*100)
    print()

    evaluator = EnhancedRAGEvaluator(results_dir)
    results = evaluator.evaluate_all()

    # 打印详细结果
    for r in results:
        print()
        print("="*100)
        print(f"患者: {r['patient_id']} (住院号: {r['hospital_id']})")
        print("="*100)

        print(f"\n【基本信息】")
        print(f"  延迟: {r['latency_ms']} ms")
        print(f"  引用总数: {r['citations_count']}")

        print(f"\n【CCR - 临床决策一致性】")
        print(f"  总分: {r['ccr']:.2f} / 4.0")
        for dim, score in r['ccr_scores'].items():
            print(f"    {dim}: {score}/4")

        print(f"\n【PTR - 物理可追溯率】")
        print(f"  总分: {r['ptr']:.3f} / 1.0")
        print(f"  引用详情:")
        for detail in r['ptr_details'][:10]:  # 只显示前10个
            print(f"    - {detail['citation'][:60]}...")
            print(f"      状态: {detail['status']}, 得分: {detail['score']}")

        print(f"\n【MQR - MDT报告规范度】")
        print(f"  总分: {r['mqr']:.2f} / 4.0")
        for mod in r['module_details']:
            status = "✓" if mod['present'] else "✗"
            print(f"    {status} {mod['name']}: {mod['score']}/0.5")

        print(f"\n【CER - 临床错误率】")
        print(f"  总分: {r['cer']:.3f} / 1.0")
        if r['errors']:
            for err in r['errors']:
                print(f"    - [{err['type']}] {err['description']} (权重: {err['weight']})")
        else:
            print(f"    未检测到明显错误")

        print(f"\n【CPI - 综合性能指数】")
        print(f"  总分: {r['cpi']:.3f} / 1.0")
        print(f"  计算过程:")
        print(f"    0.35 × ({r['ccr']:.2f}/4) = {0.35*(r['ccr']/4):.4f}")
        print(f"    0.25 × {r['ptr']:.3f} = {0.25*r['ptr']:.4f}")
        print(f"    0.25 × ({r['mqr']:.2f}/4) = {0.25*(r['mqr']/4):.4f}")
        print(f"    0.15 × (1-{r['cer']:.3f}) = {0.15*(1-r['cer']):.4f}")
        print(f"    CPI = {r['cpi']:.4f}")

    # 汇总统计
    print()
    print("="*100)
    print("汇总统计 (9例患者)")
    print("="*100)

    ccr_values = [r['ccr'] for r in results]
    ptr_values = [r['ptr'] for r in results]
    mqr_values = [r['mqr'] for r in results]
    cer_values = [r['cer'] for r in results]
    cpi_values = [r['cpi'] for r in results]

    import statistics

    print(f"\n{'指标':<20} {'均值':<15} {'标准差':<15} {'范围':<20}")
    print("-"*80)
    print(f"{'CCR (0-4)':<20} {statistics.mean(ccr_values):<15.2f} {statistics.stdev(ccr_values) if len(ccr_values)>1 else 0:<15.2f} [{min(ccr_values):.2f}, {max(ccr_values):.2f}]")
    print(f"{'PTR (0-1)':<20} {statistics.mean(ptr_values):<15.3f} {statistics.stdev(ptr_values) if len(ptr_values)>1 else 0:<15.3f} [{min(ptr_values):.3f}, {max(ptr_values):.3f}]")
    print(f"{'MQR (0-4)':<20} {statistics.mean(mqr_values):<15.2f} {statistics.stdev(mqr_values) if len(mqr_values)>1 else 0:<15.2f} [{min(mqr_values):.2f}, {max(mqr_values):.2f}]")
    print(f"{'CER (0-1)':<20} {statistics.mean(cer_values):<15.3f} {statistics.stdev(cer_values) if len(cer_values)>1 else 0:<15.3f} [{min(cer_values):.3f}, {max(cer_values):.3f}]")
    print(f"{'CPI (0-1)':<20} {statistics.mean(cpi_values):<15.3f} {statistics.stdev(cpi_values) if len(cpi_values)>1 else 0:<15.3f} [{min(cpi_values):.3f}, {max(cpi_values):.3f}]")

    # 保存结果 - 使用带时间戳的文件名
    summary = {
        'timestamp': datetime.now().isoformat(),
        'method': 'Enhanced_RAG',
        'individual_results': results,
        'summary': {
            'count': len(results),
            'ccr': {'mean': statistics.mean(ccr_values), 'std': statistics.stdev(ccr_values) if len(ccr_values)>1 else 0, 'min': min(ccr_values), 'max': max(ccr_values)},
            'ptr': {'mean': statistics.mean(ptr_values), 'std': statistics.stdev(ptr_values) if len(ptr_values)>1 else 0, 'min': min(ptr_values), 'max': max(ptr_values)},
            'mqr': {'mean': statistics.mean(mqr_values), 'std': statistics.stdev(mqr_values) if len(mqr_values)>1 else 0, 'min': min(mqr_values), 'max': max(mqr_values)},
            'cer': {'mean': statistics.mean(cer_values), 'std': statistics.stdev(cer_values) if len(cer_values)>1 else 0, 'min': min(cer_values), 'max': max(cer_values)},
            'cpi': {'mean': statistics.mean(cpi_values), 'std': statistics.stdev(cpi_values) if len(cpi_values)>1 else 0, 'min': min(cpi_values), 'max': max(cpi_values)}
        }
    }

    # 导入时间戳工具
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.timestamp_utils import get_timestamped_filename

    output_filename = get_timestamped_filename("evaluation_results", "json")
    output_file = Path(results_dir) / output_filename
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n评估结果已保存: {output_file}")


if __name__ == "__main__":
    main()
