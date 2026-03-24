#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Baseline 实验 - 直接LLM回答版本
不使用任何外部知识，仅依靠模型预训练权重回答
用于对比RAG版本的效果差异
"""

import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.llm_factory import get_brain_client_langchain


class DirectLLMBaseline:
    """直接LLM回答，不使用任何检索增强"""

    def __init__(self):
        self.llm = get_brain_client_langchain()

        # 8模块MDT报告Prompt（根据患者实际情况灵活适配，不强制填充）
        self.system_prompt = """你是一位资深的脑转移瘤多学科诊疗（MDT）专家。请基于提供的患者信息，生成一份结构化的MDT诊疗报告。

报告应根据患者实际情况，考虑以下8个核心模块（不适用的模块可标记为N/A或简要说明原因）：

## 1. 入院评估 (Admission Evaluation)
- 患者基本信息与入院情况
- 临床症状评估（主诉、现病史）
- 既往病史与合并症分析
- 影像学初步印象

## 2. 原发灶处理方案 (Primary Tumor Management Plan)
- 基于病理诊断的原发肿瘤特征
- 分子分型与靶向治疗敏感性评估
- 原发灶治疗策略建议

## 3. 系统性管理 (Systemic Management)
- 全身治疗方案
- 药物选择与剂量考量
- 围手术期用药参数（如适用）

## 4. 随访方案 (Follow-up Strategy)
- 影像学复查时间窗
- 肿瘤标志物监测
- 神经系统功能评估

## 5. 被拒绝的替代方案及排他性论证 (Rejected Alternatives)
- 其他可行但未被选择的方案
- 选择当前方案而非替代方案的循证依据

## 6. 围手术期管理 (Peri-procedural Management)
- 术前准备要点（如计划手术）
- 术后护理注意事项
- 并发症预防策略

## 7. 分子病理与基因检测 (Molecular Pathology)
- 关键基因突变分析
- 靶向治疗指导意义
- 预后分子标志物

## 8. 执行路径与决策轨迹 (Execution Trajectory)
- 推荐的治疗时间线
- 关键决策节点
- 多学科协作流程

请基于你的预训练医学知识，生成一份专业、完整的MDT诊疗报告。
- 根据患者实际情况动态判断各模块的适用性
- 不适用的治疗模块标记为"N/A"或简要说明原因
- 如果不确定，请明确说明"需临床医师进一步评估"

【引用格式规范 - 强制】

你仅使用预训练知识，必须诚实标注知识来源：

1. **预训练知识**：`[Parametric Knowledge: 来源类型]`
   - 示例：`[Parametric Knowledge: NCCN Guidelines 2023]`
   - 示例：`[Parametric Knowledge: Clinical Practice Consensus]`

2. **知识不确定性**：`[Parametric Knowledge: Uncertain, Confidence: High/Medium/Low]`

**诚实性要求：**
- 必须区分"确定知识"和"不确定推断"
- 如果记不清具体来源，标注 `[Parametric Knowledge: Uncertain]`
- **严禁编造PMID或具体引用**

**与BM Agent的差异声明：**
- 你无法访问OncoKB API，分子证据应标注 `[Parametric Knowledge: Literature-based Inference]`
- 你无法实时检索PubMed，引用应基于预训练时学习的知识"""

    def query(self, question: str, system_prompt: str = None, save_full_output: bool = False) -> dict:
        """
        直接调用LLM回答，返回标准格式

        Args:
            question: 患者问题/病历信息
            system_prompt: 可选的系统提示词
            save_full_output: 是否保存完整原始输出（包含所有tokens、reasoning）

        Returns:
            dict: {
                "response": "最终报告内容",
                "reasoning": "推理过程（DeepSeek thinking）",
                "full_output": "完整原始输出（当save_full_output=True时）"
            }
        """
        print(f"\n🔍 问题: {question[:50]}...")

        # 使用传入的system_prompt或默认prompt
        prompt_to_use = system_prompt or self.system_prompt

        # 构造消息
        messages = [
            {"role": "system", "content": prompt_to_use},
            {"role": "user", "content": question}
        ]

        # 直接调用LLM
        response = self.llm.invoke(messages)

        # 提取推理过程（DeepSeek thinking）
        reasoning_text = ""
        if hasattr(response, 'additional_kwargs') and response.additional_kwargs:
            reasoning_content = response.additional_kwargs.get('reasoning_content')
            if reasoning_content:
                reasoning_text = reasoning_content
                print(f"🧠 捕获推理过程: {len(reasoning_text)} 字符")

        # 构建完整输出（用于后续分析）
        full_output = None
        if save_full_output:
            full_output = self._build_full_output(response, messages)

        result = {
            "response": response.content,
            "reasoning": reasoning_text
        }

        if save_full_output:
            result["full_output"] = full_output

        return result

    def _build_full_output(self, response, messages) -> dict:
        """构建完整输出结构（用于后续分析）"""
        output = {
            "model": getattr(response, 'response_metadata', {}).get('model_name', 'unknown'),
            "input_messages": messages,
            "output": {
                "content": response.content,
                "reasoning": None,
                "role": "assistant"
            },
            "usage": {}
        }

        # 提取推理内容
        if hasattr(response, 'additional_kwargs') and response.additional_kwargs:
            reasoning_content = response.additional_kwargs.get('reasoning_content')
            if reasoning_content:
                output["output"]["reasoning"] = reasoning_content

        # 提取token使用情况
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            output["usage"] = {
                "input_tokens": response.usage_metadata.get('input_tokens', 0),
                "output_tokens": response.usage_metadata.get('output_tokens', 0),
                "total_tokens": response.usage_metadata.get('total_tokens', 0)
            }
        elif hasattr(response, 'response_metadata') and response.response_metadata:
            # 尝试从response_metadata获取
            token_usage = response.response_metadata.get('token_usage', {})
            if token_usage:
                output["usage"] = {
                    "input_tokens": token_usage.get('prompt_tokens', 0),
                    "output_tokens": token_usage.get('completion_tokens', 0),
                    "total_tokens": token_usage.get('total_tokens', 0)
                }

        return output

    def batch_query(self, questions: list) -> list:
        """批量查询"""
        results = []
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"问题 {i}/{len(questions)}")
            print(f"{'='*60}")
            answer = self.query(question)
            results.append({
                "question": question,
                "answer": answer
            })
        return results


def main():
    """主函数 - 交互式演示"""
    print("="*60)
    print("🧠 天坛脑转移瘤Agent - 直接LLM Baseline")
    print("="*60)

    # 初始化
    llm_baseline = DirectLLMBaseline()
    print("✅ LLM初始化完成\n")

    # 交互式查询
    print("💡 提示: 输入患者问题，输入 'exit' 退出")
    print("-"*60)

    while True:
        try:
            question = input("\n🧑‍⚕️ 医生问题: ").strip()

            if question.lower() in ['exit', 'quit', '退出']:
                print("👋 再见！")
                break

            if not question:
                continue

            # 查询
            answer = llm_baseline.query(question)

            # 输出结果
            if answer.get("reasoning"):
                print(f"\n🧠 [推理过程]:")
                print(answer["reasoning"][:500] + "..." if len(answer["reasoning"]) > 500 else answer["reasoning"])

            print(f"\n🤖 [最终报告]:")
            print(answer["response"])

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
