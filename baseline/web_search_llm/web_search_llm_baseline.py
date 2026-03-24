#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Baseline 实验 - WebSearch LLM版本 (Direct LLM + 网络搜索 + Thinking模式)
允许模型使用实时网络搜索获取最新医学证据，并提供显式推理过程
用于对比Direct LLM和RAG基线的效果差异
"""

import os
import sys
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openai import OpenAI


class WebSearchLLMBaseline:
    """WebSearch LLM回答，使用实时网络搜索+思考模式"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("❌ DASHSCOPE_API_KEY environment variable is required")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1",
        )
        self.model = "qwen3.5-plus"

        # 8模块MDT报告System Prompt（根据实际情况灵活适配）
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

请通过网络搜索获取最新循证医学证据，生成一份专业、完整的MDT诊疗报告。
- 根据患者实际情况动态判断各模块的适用性
- 不适用的治疗模块标记为"N/A"或简要说明原因（如无手术计划时，Module 6可标记为N/A或改为"围放疗期管理"）
- 如果不确定，请明确说明"需临床医师进一步评估"

【引用格式规范 - 强制】

你的优势是实时网络搜索，必须充分利用：

1. **广泛搜索**：对每个临床声明，主动搜索循证医学证据
2. **精准知识**：获取分子肿瘤学知识（突变-药物关联、耐药机制）
3. **准确引用**：使用以下格式标注来源

**引用格式要求：**

- **PubMed文献**：`[PubMed: PMID XXXXXXXX]`
  - 必须提供具体PMID数字
  - 示例：`[PubMed: PMID 15117980]`

- **临床试验**：`[ClinicalTrial: NCT号]`
  - 示例：`[ClinicalTrial: NCT03526900]`

- **指南/共识**：`[Guideline: 指南名称, 年份]`
  - 示例：`[Guideline: NCCN CNS, 2024]`

- **网页来源**：`[Web: URL, Accessed: YYYY-MM-DD]`
  - 示例：`[Web: https://oncotarget.com/..., Accessed: 2024-03-24]`

**禁止：**
- ❌ 使用 `[1,45]` 等无法直接验证的数字引用
- ❌ 声称有PMID但不提供具体号码
- ❌ 引用无法访问的URL

**不确定性声明：**
- 如果找不到可靠来源，明确标注：`[Evidence: Insufficient, Search: "关键词" returned no high-quality sources]`"""

    def query(self, question: str, system_prompt: str = None, save_full_output: bool = False) -> dict:
        """
        调用WebSearch LLM回答，返回标准格式

        Args:
            question: 患者问题/病历信息
            system_prompt: 可选的系统提示词（用于baseline评估统一格式）
            save_full_output: 是否保存完整原始输出（包含所有tokens）

        Returns:
            dict: {
                "response": "最终报告内容",
                "reasoning": "推理过程摘要",
                "search_sources": ["来源1", "来源2"...],
                "full_output": "完整原始API输出（当save_full_output=True时）"
            }
        """
        print(f"\n🔍 问题: {question[:50]}...")
        print("🌐 正在执行网络搜索+思考模式...")
        start_time = time.time()

        # 使用传入的system_prompt或默认prompt
        prompt_to_use = system_prompt or self.system_prompt

        # 构造消息
        messages = [
            {"role": "system", "content": prompt_to_use},
            {"role": "user", "content": question}
        ]

        # 调用带web_search和thinking的API
        response = self.client.responses.create(
            model=self.model,
            input=messages,
            tools=[
                {
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_mode": "standard"  # standard or deep
                    }
                }
            ],
            extra_body={
                "enable_thinking": True  # 启用思考模式
            }
        )

        # 保存完整原始输出
        full_output = None
        if save_full_output:
            import json
            # 将response对象转换为可序列化的字典
            full_output = self._response_to_dict(response)

        # 解析输出
        reasoning_text = ""
        final_answer = ""
        search_sources = []
        raw_reasoning_items = []  # 保存原始reasoning items

        for item in response.output:
            if item.type == "reasoning":
                # 提取推理过程
                raw_reasoning_items.append(item)
                if hasattr(item, 'summary') and item.summary:
                    reasoning_parts = []
                    for summary in item.summary:
                        if hasattr(summary, 'text'):
                            reasoning_parts.append(summary.text)
                    reasoning_text = "\n".join(reasoning_parts)
            elif item.type == "message":
                # 提取最终答案
                if hasattr(item, 'content') and item.content:
                    for content in item.content:
                        if hasattr(content, 'text'):
                            final_answer = content.text
                            break
            elif item.type == "tool_result":
                # 提取搜索来源
                if hasattr(item, 'content') and item.content:
                    for content in item.content:
                        if hasattr(content, 'search_results') and content.search_results:
                            for result in content.search_results:
                                if hasattr(result, 'title') and hasattr(result, 'url'):
                                    search_sources.append(f"{result.title}: {result.url}")

        # 简化推理文本（如果太长）
        if len(reasoning_text) > 2000:
            reasoning_text = reasoning_text[:2000] + "\n...[推理过程截断]"

        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)

        print(f"✅ 搜索完成，推理长度: {len(reasoning_text)} 字符")
        print(f"📚 搜索来源: {len(search_sources)} 条")

        result = {
            "response": final_answer,
            "reasoning": reasoning_text,
            "search_sources": search_sources,
            "latency_ms": latency_ms
        }

        if save_full_output:
            result["full_output"] = full_output

        return result

    def _response_to_dict(self, response) -> dict:
        """将API响应对象转换为可序列化的字典"""
        output_list = []
        for item in response.output:
            item_dict = {"type": item.type}

            if item.type == "reasoning":
                # 提取所有reasoning详情
                if hasattr(item, 'summary') and item.summary:
                    item_dict["summary"] = []
                    for summary in item.summary:
                        summary_dict = {}
                        if hasattr(summary, 'text'):
                            summary_dict["text"] = summary.text
                        if hasattr(summary, 'type'):
                            summary_dict["type"] = summary.type
                        item_dict["summary"].append(summary_dict)
                # 保留原始reasoning内容
                if hasattr(item, 'content') and item.content:
                    item_dict["content"] = []
                    for content in item.content:
                        content_dict = {}
                        if hasattr(content, 'text'):
                            content_dict["text"] = content.text
                        if hasattr(content, 'type'):
                            content_dict["type"] = content.type
                        item_dict["content"].append(content_dict)

            elif item.type == "message":
                if hasattr(item, 'content') and item.content:
                    item_dict["content"] = []
                    for content in item.content:
                        content_dict = {}
                        if hasattr(content, 'text'):
                            content_dict["text"] = content.text
                        if hasattr(content, 'type'):
                            content_dict["type"] = content.type
                        item_dict["content"].append(content_dict)
                if hasattr(item, 'role'):
                    item_dict["role"] = item.role

            elif item.type == "tool_result":
                if hasattr(item, 'content') and item.content:
                    item_dict["content"] = []
                    for content in item.content:
                        content_dict = {}
                        if hasattr(content, 'type'):
                            content_dict["type"] = content.type
                        if hasattr(content, 'search_results') and content.search_results:
                            content_dict["search_results"] = []
                            for result in content.search_results:
                                result_dict = {}
                                if hasattr(result, 'title'):
                                    result_dict["title"] = result.title
                                if hasattr(result, 'url'):
                                    result_dict["url"] = result.url
                                if hasattr(result, 'site_name'):
                                    result_dict["site_name"] = result.site_name
                                if hasattr(result, 'snippet'):
                                    result_dict["snippet"] = result.snippet
                                content_dict["search_results"].append(result_dict)
                        item_dict["content"].append(content_dict)

            output_list.append(item_dict)

        return {
            "model": getattr(response, 'model', self.model),
            "output": output_list,
            "usage": {
                "input_tokens": getattr(response.usage, 'input_tokens', 0) if hasattr(response, 'usage') else 0,
                "output_tokens": getattr(response.usage, 'output_tokens', 0) if hasattr(response, 'usage') else 0,
                "total_tokens": getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            }
        }

    def batch_query(self, questions: list) -> list:
        """批量查询"""
        results = []
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"问题 {i}/{len(questions)}")
            print(f"{'='*60}")
            result = self.query(question)
            results.append({
                "question": question,
                "answer": result
            })
        return results


def main():
    """主函数 - 交互式演示"""
    print("="*60)
    print("🧠 天坛脑转移瘤Agent - WebSearch LLM Baseline")
    print("="*60)

    # 初始化
    try:
        websearch_llm = WebSearchLLMBaseline()
        print("✅ WebSearch LLM初始化完成\n")
    except ValueError as e:
        print(f"❌ 初始化失败: {e}")
        return

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
            result = websearch_llm.query(question)

            # 输出结果
            if result.get("reasoning"):
                print(f"\n🧠 [推理过程]:")
                print(result["reasoning"][:500] + "..." if len(result["reasoning"]) > 500 else result["reasoning"])

            print(f"\n🤖 [最终报告]:")
            print(result["response"])

            if result.get("search_sources"):
                print(f"\n📚 [搜索来源]:")
                for i, source in enumerate(result["search_sources"][:5], 1):  # 只显示前5个
                    print(f"  {i}. {source}")

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
