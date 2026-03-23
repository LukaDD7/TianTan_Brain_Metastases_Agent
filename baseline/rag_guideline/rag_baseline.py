#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Baseline 实验 - RAG 临床指南版本 (简化版)
"""

import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.llm_factory import get_brain_client_langchain


class SimpleRAGBaseline:
    """简化版RAG"""

    def __init__(self, guidelines_dir: str = None):
        # 使用绝对路径
        self.guidelines_dir = guidelines_dir or "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/Guidelines"
        self.vector_store = None
        self.llm = get_brain_client_langchain()

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
        """创建向量存储"""
        print("🔍 正在创建向量存储...")
        embeddings = OpenAIEmbeddings(
            model="text-embedding-v3",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
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

    def query(self, question: str) -> dict:
        """查询"""
        if not self.vector_store:
            raise ValueError("RAG系统未初始化")

        print(f"\n🔍 查询: {question[:50]}...")

        # 检索相关文档
        docs = self.vector_store.similarity_search(question, k=3)
        context = "\n\n".join([d.page_content for d in docs])

        # 构造Prompt
        prompt = f"""基于以下临床指南内容回答医生的问题。

【指南内容】
{context}

【医生问题】
{question}

请根据指南内容提供专业的诊疗建议，并引用指南来源。"""

        # 调用LLM
        response = self.llm.invoke([{"role": "user", "content": prompt}])

        return {
            "answer": response.content,
            "sources": [d.metadata.get('source', 'unknown') for d in docs]
        }


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
