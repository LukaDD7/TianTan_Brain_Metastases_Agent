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

        # 允许使用所有能力的System Prompt
        self.system_prompt = """你是一名脑转移瘤MDT专家。请回答医生的问题。

回答要求：
1. 给出具体的治疗建议
2. 说明依据和证据等级
3. 你可以使用你的预训练知识，也可以联网搜索最新信息
4. 如果不确定，请明确说明"我不确定"

请尽力提供最准确的医疗建议。"""

    def query(self, question: str) -> str:
        """直接调用LLM回答"""
        print(f"\n🔍 问题: {question[:50]}...")

        # 构造消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question}
        ]

        # 直接调用LLM
        response = self.llm.invoke(messages)

        return response.content

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
            print(f"\n🤖 AI回答:\n{answer}")

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
