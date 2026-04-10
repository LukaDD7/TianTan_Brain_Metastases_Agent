#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Baseline 实验 - RAG 临床指南版本 (V2 - 支持API usage统计)
使用 qwen3-vl-embedding 通过 dashscope
使用原生OpenAI client以获取准确usage数据
"""

import os
import sys
import time
from pathlib import Path
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from openai import OpenAI

# 直接使用原生OpenAI client获取usage数据
def get_openai_client():
    """获取原生OpenAI client（用于准确统计usage）"""
    import config
    if not config.BRAIN_API_KEY:
        raise ValueError("❌ DASHSCOPE_API_KEY not found")
    return OpenAI(
        api_key=config.BRAIN_API_KEY,
        base_url=config.BRAIN_BASE_URL
    )


class DashScopeEmbeddings(Embeddings):
    """Custom Embeddings class using DashScope qwen3-vl-embedding"""

    def __init__(self, api_key: str = None):
        import dashscope
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        dashscope.api_key = self.api_key
        self.model = "qwen3-vl-embedding"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        import dashscope
        embeddings = []
        for text in texts:
            resp = dashscope.MultiModalEmbedding.call(
                model=self.model,
                input=[{'text': text}]
            )
            if resp.status_code == 200:
                embeddings.append(resp.output['embeddings'][0]['embedding'])
            else:
                print(f"⚠️ Embedding failed: {resp.message}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 3072)  # qwen3-vl-embedding is 3072 dims
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        import dashscope
        resp = dashscope.MultiModalEmbedding.call(
            model=self.model,
            input=[{'text': text}]
        )
        if resp.status_code == 200:
            return resp.output['embeddings'][0]['embedding']
        else:
            print(f"⚠️ Query embedding failed: {resp.message}")
            return [0.0] * 3072


class SimpleRAGBaseline:
    """简化版RAG - V2支持API usage统计"""

    # 8模块MDT报告默认Prompt（根据患者实际情况灵活适配，不强制填充）
    DEFAULT_SYSTEM_PROMPT = """你是一位资深的脑转移瘤多学科诊疗（MDT）专家。请基于提供的患者信息和临床指南，生成一份结构化的MDT诊疗报告。

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

【患者信息】
{patient_info}

【参考指南内容】
{context}

请基于临床指南和循证医学证据，生成一份专业、完整的MDT诊疗报告。
- 根据患者实际情况动态判断各模块的适用性
- 不适用的治疗模块标记为"N/A"或简要说明原因

【引用格式规范 - 强制 - 与BM Agent统一】

所有临床声明必须附带可追溯的引用标签：

1. **指南引用（强制）**：`[Local: <文件名>, Section: <章节标题>]`
   - 必须提供具体的文件名和章节/段落信息
   - 示例：`[Local: NCCN_CNS.md, Section: Brain Metastases - Systemic Therapy]`
   - 示例：`[Local: ESMO_NSCLC.md, Line: 245-250]`

2. **预训练知识推断**：`[Parametric Knowledge: <来源说明>]`
   - 当基于预训练知识进行合理推断时使用
   - 必须诚实标注来源
   - 示例：`[Parametric Knowledge: NCCN Guidelines 2023]`

3. **不确定性声明**：`[Evidence: Insufficient in Retrieved Guidelines]`
   - 当检索到的指南片段不足以支持结论时**必须**使用
   - 这是RAG的局限性，诚实标注是正确的做法

**引用质量要求：**
- 每个临床声明（治疗建议、剂量参数、随访方案）都应有引用支撑
- 引用必须指向具体的指南文件和章节
- 严禁编造不存在的章节或页码
- 如果记不清具体位置，使用`[Parametric Knowledge: ...]`诚实标注

**与BM Agent的区别（RAG局限性声明）：**
- RAG只能访问本地指南文档，无法实时查询PubMed或OncoKB
- 对于分子靶向治疗证据，如果指南未覆盖，必须标注`[Evidence: Insufficient]`
- 这是正常的RAG局限性，诚实标注比编造引用更可取"""

    def __init__(self, guidelines_dir: str = None):
        # 使用绝对路径
        self.guidelines_dir = guidelines_dir or "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/Guidelines"
        self.vector_store = None
        # 使用原生OpenAI client以获取准确usage数据
        self.client = get_openai_client()
        self.model = config.BRAIN_MODEL_NAME  # 使用与项目统一的模型

    def load_documents(self):
        """加载指南文档"""
        print("📚 正在加载临床指南文档...")
        documents = []
        guidelines_path = Path(self.guidelines_dir)

        for md_file in guidelines_path.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'content': content,
                        'source': str(md_file.relative_to(guidelines_path))
                    })
            except Exception as e:
                print(f"⚠️ 读取失败 {md_file}: {e}")

        print(f"✅ 共加载 {len(documents)} 个文档")
        return documents

    def split_documents(self, documents):
        """分割文档"""
        print("✂️  正在分割文档...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        all_splits = []
        for doc in documents:
            splits = text_splitter.create_documents(
                [doc['content']],
                metadatas=[{'source': doc['source']}]
            )
            all_splits.extend(splits)

        print(f"✅ 共生成 {len(all_splits)} 个片段")
        return all_splits

    def create_vector_store(self, splits):
        """创建向量存储 - 使用 qwen3-vl-embedding"""
        print("🔍 正在创建向量存储 (qwen3-vl-embedding)...")
        embeddings = DashScopeEmbeddings()
        self.vector_store = FAISS.from_documents(splits, embeddings)
        print("✅ 向量存储创建完成")

    def initialize(self):
        """初始化"""
        documents = self.load_documents()
        if not documents:
            raise ValueError("未找到指南文档")
        splits = self.split_documents(documents)
        self.create_vector_store(splits)
        print("\n🎉 RAG系统初始化完成！")

    def query(self, question: str, system_prompt: str = None, save_full_output: bool = False) -> dict:
        """
        查询

        Args:
            question: 患者问题/病历信息
            system_prompt: 可选的系统提示词
            save_full_output: 是否保存完整原始输出（包含所有tokens、reasoning）

        Returns:
            dict: {
                "response": "最终报告内容",
                "reasoning": "推理过程（DeepSeek thinking）",
                "sources": ["来源1", "来源2"...],
                "retrieved_docs": [...],
                "full_output": "完整原始输出（当save_full_output=True时）",
                "latency_ms": 响应时间毫秒
            }
        """
        if not self.vector_store:
            raise ValueError("RAG系统未初始化")

        print(f"\n🔍 查询: {question[:50]}...")
        start_time = time.time()

        # 检索相关文档 - 增加检索数量以获取更充分的证据
        docs = self.vector_store.similarity_search(question, k=5)
        context = "\n\n".join([d.page_content for d in docs])

        # 使用传入的system_prompt或默认prompt
        if system_prompt:
            # 替换模板变量
            prompt = system_prompt.format(
                patient_info=question,
                context=context
            )
        else:
            # 使用默认8模块Prompt
            prompt = self.DEFAULT_SYSTEM_PROMPT.format(
                patient_info=question,
                context=context
            )

        # 调用LLM - 使用原生OpenAI client获取准确usage
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.6
        )

        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)

        # 提取结果和usage
        content = response.choices[0].message.content
        usage = response.usage

        # 提取推理过程（DeepSeek reasoning）
        reasoning_text = ""
        if hasattr(response.choices[0].message, 'reasoning_content'):
            reasoning_text = response.choices[0].message.reasoning_content or ""
            if reasoning_text:
                print(f"🧠 捕获推理过程: {len(reasoning_text)} 字符")

        # 构建完整输出
        full_output = None
        if save_full_output:
            full_output = self._build_full_output(response, prompt, docs, latency_ms, usage)

        result = {
            "response": content,
            "reasoning": reasoning_text,
            "sources": [d.metadata.get('source', 'unknown') for d in docs],
            "retrieved_docs": [{
                "content": d.page_content[:200] + "...",
                "source": d.metadata.get('source', 'unknown')
            } for d in docs],
            "latency_ms": latency_ms
        }

        if save_full_output:
            result["full_output"] = full_output

        return result

    def _build_full_output(self, response, prompt, docs, latency_ms: int, usage) -> dict:
        """构建完整输出结构（V2 - 包含准确usage数据）"""
        output = {
            "model": response.model,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "latency_ms": latency_ms,
            "input_prompt": prompt,
            "retrieved_documents": [{
                "content": d.page_content,
                "source": d.metadata.get('source', 'unknown')
            } for d in docs],
            "output": {
                "content": response.choices[0].message.content,
                "reasoning": getattr(response.choices[0].message, 'reasoning_content', None),
                "role": "assistant"
            },
            "usage": {
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0
            }
        }

        return output


def main():
    print("="*60)
    print("🧠 天坛脑转移瘤Agent - RAG指南Baseline")
    print("="*60)

    rag = SimpleRAGBaseline()
    try:
        rag.initialize()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    print("\n💡 输入患者问题，输入 'exit' 退出")
    print("-"*60)

    while True:
        try:
            question = input("\n🧑‍⚕️ 医生问题: ").strip()
            if question.lower() in ['exit', 'quit']:
                print("👋 再见！")
                break
            if not question:
                continue

            result = rag.query(question)
            print(f"\n🤖 AI回答:\n{result['answer']}")
            print(f"\n📚 引用来源: {', '.join(result['sources'])}")

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
