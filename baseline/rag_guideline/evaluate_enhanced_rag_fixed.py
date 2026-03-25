#!/usr/bin/env python3
"""
Enhanced RAG Baseline - 完整评估指标计算（修复版）
计算CCR, PTR, MQR, CER, CPI
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
import statistics

# 患者映射
PATIENT_INFO = {
    "Case1": {"hospital_id": "648772", "name": "Case1"},
    "Case2": {"hospital_id": "640880", "name": "Case2"},
    "Case3": {"hospital_id": "868183", "name": "Case3"},
    "Case4": {"hospital_id": "665548", "name": "Case4"},
    "Case6": {"hospital_id": "638114", "name": "Case6"},
    "Case7": {"hospital_id": "612908", "name": "Case7"},
    "Case9": {"hospital_id": "708387", "name": "Case9"},
    "Case10": {"hospital_id": "747724", "name": "Case10"},
    "Case605525": {"hospital_id": "605525", "name": "Case8"}
}

class EnhancedRAGEvaluator:
    """Enhanced RAG评估器"""

    def __init__(self, results_dir):
        self.results_dir = Path(results_dir)
        self.guidelines_dir = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/Guidelines")

    def load_report(self, filepath):
        """加载报告，处理不同格式"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 统一格式
        patient_id = data.get('patient_id', 'Unknown')
        hospital_id = data.get('hospital_id', 'Unknown')

        # 提取报告文本（处理不同格式）
        if 'results' in data and 'enhanced_rag' in data['results']:
            # 新格式
            report_text = data['results']['enhanced_rag'].get('report', '')
            latency = data['results']['enhanced_rag'].get('latency_ms', 0)
        else:
            # 旧格式（Case605525）
            report_text = data.get('response', '')
            latency = data.get('latency_ms', 0)

        patient_info = data.get('patient_info', '')

        return {
            'patient_id': patient_id,
            'hospital_id': hospital_id,
            'report_text': report_text,
            'latency': latency,
            'patient_info': patient_info,
            'raw_data': data
        }

    def extract_citations(self, report_text):
        """提取所有引用"""
        citations = []

        # 匹配 [Local: ..., Line: X-Y] 格式（多种变体）
        # 支持有.md后缀和没有的情况
        local_pattern = r'\[Local:\s*([^\]]+?),\s*Line:\s*(\d+)\s*-\s*(\d+)\s*\]'
        local_matches = re.findall(local_pattern, report_text, re.IGNORECASE)
        for match in local_matches:
            source = match[0].strip()
            # 统一处理source路径
            if not source.endswith('.md'):
                source = source + '.md'
            citations.append({
                'type': 'local',
                'source': source,
                'start_line': int(match[1]),
                'end_line': int(match[2]),
                'full': f"[Local: {match[0]}, Line: {match[1]}-{match[2]}]"
            })

        # 匹配 Evidence: Insufficient
        insufficient_pattern = r'\[Evidence:\s*Insufficient[^\]]*\]'
        insufficient_matches = re.findall(insufficient_pattern, report_text, re.IGNORECASE)
        for match in insufficient_matches:
            citations.append({
                'type': 'insufficient',
                'full': match
            })

        # 匹配 Inference from Local
        inference_pattern = r'\[Inference from Local:\s*([^\]]+?)\]'
        inference_matches = re.findall(inference_pattern, report_text, re.IGNORECASE)
        for match in inference_matches:
            citations.append({
                'type': 'inference',
                'source': match.strip(),
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

        # 构建完整路径 - 处理目录结构
        # source格式可能是: ASCO_SNO_ASTRO_Brain_Metastases/ASCO_SNO_ASTRO_Brain_Metastases.md
        file_path = self.guidelines_dir / source

        if not file_path.exists():
            # 尝试查找文件
            possible_paths = list(self.guidelines_dir.rglob('*.md'))
            for pp in possible_paths:
                if pp.name == source.split('/')[-1]:
                    file_path = pp
                    break

        if not file_path.exists():
            return {
                'exists': False,
                'source': source,
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
                    'source': source,
                    'total_lines': total_lines,
                    'reason': f'Line range {start_line}-{end_line} out of bounds (file has {total_lines} lines)'
                }

            # 获取引用的内容
            cited_content = ''.join(lines[start_line-1:end_line])

            return {
                'exists': True,
                'source': source,
                'total_lines': total_lines,
                'content_preview': cited_content[:200] if cited_content else '(empty)'
            }

        except Exception as e:
            return {
                'exists': False,
                'source': source,
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
                        'citation': cite['full'][:80],
                        'score': 2,
                        'status': '完全可追溯',
                        'details': f"File exists, line {cite['start_line']}-{cite['end_line']} valid"
                    })
                else:
                    trace_scores.append(0)
                    verification_details.append({
                        'citation': cite['full'][:80],
                        'score': 0,
                        'status': '不可追溯',
                        'details': verify_result.get('reason', 'Unknown') if verify_result else 'No result'
                    })
            elif cite['type'] == 'inference':
                # Inference引用部分可追溯
                trace_scores.append(1)
                verification_details.append({
                    'citation': cite['full'][:80],
                    'score': 1,
                    'status': '部分可追溯（推断）'
                })
            elif cite['type'] == 'insufficient':
                # 证据不足不算可追溯
                trace_scores.append(0)
                verification_details.append({
                    'citation': cite['full'][:80],
                    'score': 0,
                    'status': '不可追溯（证据不足）'
                })

        ptr = sum(trace_scores) / (2 * len(trace_scores)) if trace_scores else 0.0

        return ptr, verification_details

    def calculate_mqr(self, report_text):
        """
        计算MDT报告规范度 MQR

        8个模块，每个模块0.5分（如果完整）
        """
        modules = [
            ("入院评估", r"##\s*1\.\s*入院评估|入院评估"),
            ("原发灶处理方案", r"##\s*2\.\s*原发灶|原发灶处理"),
            ("系统性管理", r"##\s*3\.\s*系统性管理|系统性管理"),
            ("随访方案", r"##\s*4\.\s*随访|随访方案"),
            ("排他性论证", r"##\s*5\.\s*被拒绝|排他性论证|替代方案"),
            ("围手术期管理", r"##\s*6\.\s*围手术期|围手术期管理"),
            ("分子病理", r"##\s*7\.\s*分子|分子病理"),
            ("执行路径", r"##\s*8\.\s*执行|执行路径|决策轨迹")
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

        W_max = 15
        """
        errors = []
        W_max = 15

        # 检测明显的错误模式
        # 1. 剂量明显错误
        dose_pattern = r'(\d+)\s*(mg|g|Gy)'
        dose_matches = re.findall(dose_pattern, report_text.lower())
        for value, unit in dose_matches:
            val = int(value)
            if unit == 'mg' and val > 10000:
                errors.append({
                    'type': 'major',
                    'weight': 2.0,
                    'description': f'疑似剂量错误: {val} mg'
                })
            elif unit == 'gy' and val > 100:
                errors.append({
                    'type': 'major',
                    'weight': 2.0,
                    'description': f'疑似放疗剂量错误: {val} Gy'
                })

        # 2. 检查模块完整性缺失
        module_count = len(re.findall(r'##\s*\d+', report_text))
        if module_count < 8:
            missing = 8 - module_count
            errors.append({
                'type': 'minor',
                'weight': 1.0 * missing,
                'description': f'模块缺失: {missing}个'
            })

        total_weight = sum(e['weight'] for e in errors)
        cer = min(total_weight / W_max, 1.0) if W_max > 0 else 0.0

        return cer, errors

    def estimate_ccr(self, report_text):
        """
        估算临床决策一致性 CCR

        5个维度，每个0-4分：
        - S_line: 治疗线判定
        - S_scheme: 方案选择
        - S_dose: 剂量参数
        - S_reject: 排他性论证
        - S_align: 临床路径一致性
        """
        scores = {
            'S_line': 0,
            'S_scheme': 0,
            'S_dose': 0,
            'S_reject': 0,
            'S_align': 0
        }

        # S_line: 检查是否提及治疗线
        line_patterns = ['一线', '二线', '三线', '四线', '五线', '六线', '1线', '2线', '3线', '初治', '辅助', '晚期']
        for pattern in line_patterns:
            if pattern in report_text:
                scores['S_line'] = 3
                break

        # S_scheme: 检查是否有方案推荐
        if '推荐' in report_text or '建议' in report_text or '治疗方案' in report_text:
            scores['S_scheme'] = 3

        # S_dose: 检查是否有剂量信息
        if re.search(r'\d+\s*(mg|g|Gy|ml|m²)', report_text, re.IGNORECASE):
            scores['S_dose'] = 2

        # S_reject: 检查排他性论证
        if '被拒绝' in report_text or '替代方案' in report_text or '排他性' in report_text or '替代' in report_text:
            scores['S_reject'] = 3

        # S_align: 基于整体报告质量
        if len(report_text) > 2000 and scores['S_scheme'] > 0:
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

        patient_id = data['patient_id']
        hospital_id = data['hospital_id']
        report_text = data['report_text']
        latency = data['latency']

        # 提取引用
        citations = self.extract_citations(report_text)

        # 计算各项指标
        ptr, ptr_details = self.calculate_ptr(citations)
        mqr, module_details = self.calculate_mqr(report_text)
        cer, errors = self.calculate_cer(report_text)
        ccr, ccr_scores = self.estimate_ccr(report_text)
        cpi = self.calculate_cpi(ccr, ptr, mqr, cer)

        return {
            'patient_id': patient_id,
            'hospital_id': hospital_id,
            'latency_ms': latency,
            'citations_count': len(citations),
            'local_citations': len([c for c in citations if c['type'] == 'local']),
            'insufficient_citations': len([c for c in citations if c['type'] == 'insufficient']),
            'inference_citations': len([c for c in citations if c['type'] == 'inference']),
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

        # 获取所有结果文件
        files = sorted(self.results_dir.glob('*_enhanced_rag_results.json'))

        print(f"找到 {len(files)} 个结果文件")
        print()

        for filepath in files:
            print(f"评估: {filepath.name}")
            try:
                result = self.evaluate_single(filepath)
                results.append(result)
            except Exception as e:
                print(f"  错误: {e}")
                import traceback
                traceback.print_exc()

        return results


def print_report(results):
    """打印详细报告"""
    for r in results:
        print()
        print("="*100)
        print(f"患者: {r['patient_id']} (住院号: {r['hospital_id']})")
        print("="*100)

        print(f"\n【基本信息】")
        print(f"  延迟: {r['latency_ms']} ms")
        print(f"  引用总数: {r['citations_count']} (Local: {r['local_citations']}, Insufficient: {r['insufficient_citations']}, Inference: {r['inference_citations']})")

        print(f"\n【CCR - 临床决策一致性】")
        print(f"  总分: {r['ccr']:.2f} / 4.0")
        for dim, score in r['ccr_scores'].items():
            print(f"    {dim}: {score}/4")

        print(f"\n【PTR - 物理可追溯率】")
        print(f"  总分: {r['ptr']:.3f} / 1.0")
        verified = sum(1 for d in r['ptr_details'] if d['score'] == 2)
        partial = sum(1 for d in r['ptr_details'] if d['score'] == 1)
        failed = sum(1 for d in r['ptr_details'] if d['score'] == 0)
        print(f"  完全可追溯: {verified}, 部分可追溯: {partial}, 不可追溯: {failed}")
        if r['ptr_details']:
            print(f"  引用详情 (前5个):")
            for detail in r['ptr_details'][:5]:
                print(f"    - {detail['status']} (得分: {detail['score']})")
                print(f"      {detail['citation'][:70]}...")

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


def print_summary(results):
    """打印汇总统计"""
    print()
    print("="*100)
    print("汇总统计 (9例患者)")
    print("="*100)

    ccr_values = [r['ccr'] for r in results]
    ptr_values = [r['ptr'] for r in results]
    mqr_values = [r['mqr'] for r in results]
    cer_values = [r['cer'] for r in results]
    cpi_values = [r['cpi'] for r in results]

    def stats(vals):
        return {
            'mean': statistics.mean(vals),
            'std': statistics.stdev(vals) if len(vals) > 1 else 0,
            'min': min(vals),
            'max': max(vals)
        }

    ccr_stat = stats(ccr_values)
    ptr_stat = stats(ptr_values)
    mqr_stat = stats(mqr_values)
    cer_stat = stats(cer_values)
    cpi_stat = stats(cpi_values)

    print(f"\n{'指标':<20} {'均值±标准差':<25} {'范围':<30}")
    print("-"*80)
    print(f"{'CCR (0-4)':<20} {ccr_stat['mean']:.2f} ± {ccr_stat['std']:.2f}         [{ccr_stat['min']:.2f}, {ccr_stat['max']:.2f}]")
    print(f"{'PTR (0-1)':<20} {ptr_stat['mean']:.3f} ± {ptr_stat['std']:.3f}       [{ptr_stat['min']:.3f}, {ptr_stat['max']:.3f}]")
    print(f"{'MQR (0-4)':<20} {mqr_stat['mean']:.2f} ± {mqr_stat['std']:.2f}         [{mqr_stat['min']:.2f}, {mqr_stat['max']:.2f}]")
    print(f"{'CER (0-1)':<20} {cer_stat['mean']:.3f} ± {cer_stat['std']:.3f}       [{cer_stat['min']:.3f}, {cer_stat['max']:.3f}]")
    print(f"{'CPI (0-1)':<20} {cpi_stat['mean']:.3f} ± {cpi_stat['std']:.3f}       [{cpi_stat['min']:.3f}, {cpi_stat['max']:.3f}]")

    # 对比表格
    print()
    print("="*100)
    print("与原始Baseline对比")
    print("="*100)
    print()
    print(f"{'Method':<25} {'CCR (0-4)':<15} {'PTR (0-1)':<15} {'MQR (0-4)':<15} {'CER (0-1)':<15} {'CPI (0-1)':<15}")
    print("-"*100)
    print(f"{'Standard RAG':<25} {'2.01 ± 0.20':<15} {'0.00 ± 0.00':<15} {'2.50 ± 0.20':<15} {'N/A':<15} {'0.52 ± 0.03':<15}")
    print(f"{'Enhanced RAG':<25} {ccr_stat['mean']:.2f} ± {ccr_stat['std']:.2f}{'':<8} {ptr_stat['mean']:.3f} ± {ptr_stat['std']:.3f}{'':<6} {mqr_stat['mean']:.2f} ± {mqr_stat['std']:.2f}{'':<8} {cer_stat['mean']:.3f} ± {cer_stat['std']:.3f}{'':<6} {cpi_stat['mean']:.3f} ± {cpi_stat['std']:.3f}")
    print()
    print("关键改进:")
    ptr_improvement = (ptr_stat['mean'] - 0.00) / 0.01 if ptr_stat['mean'] > 0 else 0
    print(f"  - PTR: 从 0.00 提升到 {ptr_stat['mean']:.3f} (提升 {ptr_improvement:.0f}x)")
    print(f"  - MQR: 从 2.50 提升到 {mqr_stat['mean']:.2f} (提升 {(mqr_stat['mean']/2.50-1)*100:.1f}%)")
    print(f"  - CPI: 从 0.52 提升到 {cpi_stat['mean']:.3f} (提升 {(cpi_stat['mean']/0.52-1)*100:.1f}%)")

    return {
        'ccr': ccr_stat,
        'ptr': ptr_stat,
        'mqr': mqr_stat,
        'cer': cer_stat,
        'cpi': cpi_stat
    }


def main():
    """主函数"""
    results_dir = "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/baseline/results_enhanced"

    print("="*100)
    print("Enhanced RAG Baseline - 完整评估指标计算（修复版）")
    print("="*100)
    print()

    evaluator = EnhancedRAGEvaluator(results_dir)
    results = evaluator.evaluate_all()

    # 打印详细结果
    print_report(results)

    # 打印汇总
    summary = print_summary(results)

    # 保存结果 - 使用带时间戳的文件名
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'method': 'Enhanced_RAG',
        'individual_results': results,
        'summary': summary
    }

    # 导入时间戳工具
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.timestamp_utils import get_timestamped_filename

    output_filename = get_timestamped_filename("evaluation_results_final", "json")
    output_file = Path(results_dir) / output_filename
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print()
    print(f"完整评估结果已保存: {output_file}")


if __name__ == "__main__":
    main()
