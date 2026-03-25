#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Baseline 实验 - RAG 临床指南版本 (增强版，带行号追踪)
使用 qwen3-vl-embedding 通过 dashscope
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings

from utils.llm_factory import get_brain_client_langchain


class DashScopeEmbeddings(Embeddings):
    """Custom Embeddings class using DashScope qwen3-vl-embedding"""

    def __init__(self, api_key: str = None):
        import dashscope
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        dashscope.api_key = self.api_key
        self.model = "qwen3-vl-embedding"
        self.embedding_dim = 3072  # qwen3-vl-embedding dimension

    def _get_embedding(self, text: str) -> List[float]:
        """获取单个文本的embedding，带重试逻辑"""
        import dashscope
        import time

        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = dashscope.MultiModalEmbedding.call(
                    model=self.model,
                    input=[{'text': text[:2000]}]  # 限制文本长度
                )
                if resp.status_code == 200:
                    emb = resp.output['embeddings'][0]['embedding']
                    # 验证维度
                    if len(emb) == self.embedding_dim:
                        return emb
                    else:
                        print(f"⚠️ Embedding dimension mismatch: {len(emb)}")
                        return [0.0] * self.embedding_dim
                else:
                    print(f"⚠️ Embedding attempt {attempt+1} failed: {resp.message}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
            except Exception as e:
                print(f"⚠️ Embedding exception (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)

        return [0.0] * self.embedding_dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents with progress tracking"""
        embeddings = []
        total = len(texts)

        for i, text in enumerate(texts):
            if i % 100 == 0:
                print(f"  Embedding progress: {i}/{total} ({i/total*100:.1f}%)")
            emb = self._get_embedding(text)
            embeddings.append(emb)

        # 验证所有embedding维度一致
        dims = [len(e) for e in embeddings]
        if len(set(dims)) > 1:
            print(f"⚠️ Inconsistent embedding dimensions: {set(dims)}")
            # 统一维度
            embeddings = [e if len(e) == self.embedding_dim else [0.0] * self.embedding_dim
                         for e in embeddings]

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self._get_embedding(text)


class TraceableTextSplitter:
    """增强版文本切分器，保留行号信息"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "；", " ", ""]
        )

    def split_with_line_numbers(self, text: str, source: str) -> List[Dict]:
        """
        切分文本并保留行号信息

        Returns:
            List[Dict]: 每个元素包含 {
                'content': 文本内容,
                'source': 文件名,
                'start_line': 起始行号,
                'end_line': 结束行号,
                'char_start': 字符起始位置,
                'char_end': 字符结束位置
            }
        """
        # 首先按行分割，建立字符位置到行号的映射
        lines = text.split('\n')
        line_starts = []
        current_pos = 0
        for line in lines:
            line_starts.append(current_pos)
            current_pos += len(line) + 1  # +1 for '\n'

        # 使用基础切分器切分文本
        chunks = self.base_splitter.split_text(text)

        result = []
        for chunk in chunks:
            # 找到chunk在原文中的位置
            char_start = text.find(chunk)
            if char_start == -1:
                # 如果找不到（可能因为overlap等原因），跳过
                continue
            char_end = char_start + len(chunk)

            # 字符位置映射到行号
            import bisect
            start_line = bisect.bisect_right(line_starts, char_start) - 1
            end_line = bisect.bisect_right(line_starts, char_end) - 1

            # 确保行号在有效范围
            start_line = max(0, start_line)
            end_line = min(len(lines) - 1, end_line)

            result.append({
                'content': chunk,
                'source': source,
                'start_line': start_line + 1,  # 行号从1开始
                'end_line': end_line + 1,
                'char_start': char_start,
                'char_end': char_end
            })

        return result


class EnhancedRAGBaseline:
    """增强版RAG，支持行号追踪"""

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
- 引用指南时必须标注具体来源和精确行号

【引用格式规范 - 强制】

你基于检索到的指南片段，必须精准引用：

1. **指南引用**：`[Local: <文件名>, Line: <起始行>-<结束行>]`
   - 示例：`[Local: NCCN_CNS.md, Line: 245-250]`
   - 示例：`[Local: ESMO_Brain_Metastasis.md, Line: 120-135]`

2. **知识推断**：`[Inference from Local: <文件名>, Line: <行号范围>]`
   - 当基于指南内容进行合理推断时使用
   - 必须提供来源行号范围

**禁止：**
- ❌ 不提供具体的行号信息
- ❌ 使用模糊的章节标题代替行号
- ❌ 将指南内容错误标注为 `[PubMed: ...]`

**重要：**
每个医学建议都必须有可追溯的来源。如果检索到的指南片段不足以支持结论，标注：`[Evidence: Insufficient in Retrieved Guidelines]`"""

    def __init__(self, guidelines_dir: str = None):
        self.guidelines_dir = guidelines_dir or "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/Guidelines"
        self.vector_store = None
        self.llm = get_brain_client_langchain()
        self.splitter = TraceableTextSplitter(chunk_size=1000, chunk_overlap=200)

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
        """切分文档并保留行号"""
        print("✂️  正在切分文档（保留行号信息）...")

        all_splits = []
        for doc in documents:
            splits = self.splitter.split_with_line_numbers(
                doc['content'],
                doc['source']
            )
            all_splits.extend(splits)

        print(f"✅ 共生成 {len(all_splits)} 个带行号的片段")
        return all_splits

    def create_vector_store(self, splits):
        """创建向量存储"""
        print("🔍 正在创建向量存储 (qwen3-vl-embedding)...")

        # 准备文本和元数据
        texts = [s['content'] for s in splits]
        metadatas = [{
            'source': s['source'],
            'start_line': s['start_line'],
            'end_line': s['end_line']
        } for s in splits]

        embeddings = DashScopeEmbeddings()

        # 手动创建FAISS存储
        from langchain_core.documents import Document
        docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
        self.vector_store = FAISS.from_documents(docs, embeddings)

        print("✅ 向量存储创建完成")

    def initialize(self):
        """初始化"""
        documents = self.load_documents()
        if not documents:
            raise ValueError("未找到指南文档")
        splits = self.split_documents(documents)
        self.create_vector_store(splits)
        print("\n🎉 增强版RAG系统初始化完成！")

    def query(self, question: str, system_prompt: str = None, save_full_output: bool = False) -> dict:
        """查询"""
        if not self.vector_store:
            raise ValueError("RAG系统未初始化")

        print(f"\n🔍 查询: {question[:50]}...")
        start_time = time.time()

        # 检索相关文档
        docs = self.vector_store.similarity_search(question, k=5)

        # 构建带行号的context
        context_parts = []
        for i, d in enumerate(docs, 1):
            source = d.metadata.get('source', 'unknown')
            start_line = d.metadata.get('start_line', '?')
            end_line = d.metadata.get('end_line', '?')

            part = f"""[片段 {i}: {source}, Line: {start_line}-{end_line}]
{d.page_content}
---"""
            context_parts.append(part)

        context = "\n\n".join(context_parts)

        # 使用传入的system_prompt或默认prompt
        if system_prompt:
            prompt = system_prompt.format(
                patient_info=question,
                context=context
            )
        else:
            prompt = self.DEFAULT_SYSTEM_PROMPT.format(
                patient_info=question,
                context=context
            )

        # 调用LLM
        response = self.llm.invoke([{"role": "user", "content": prompt}])

        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)

        # 提取推理过程
        reasoning_text = ""
        if hasattr(response, 'additional_kwargs') and response.additional_kwargs:
            reasoning_content = response.additional_kwargs.get('reasoning_content')
            if reasoning_content:
                reasoning_text = reasoning_content

        result = {
            "response": response.content,
            "reasoning": reasoning_text,
            "sources": [f"{d.metadata.get('source', 'unknown')} (Line: {d.metadata.get('start_line', '?')}-{d.metadata.get('end_line', '?')})" for d in docs],
            "retrieved_docs": [{
                "content": d.page_content[:200] + "...",
                "source": d.metadata.get('source', 'unknown'),
                "start_line": d.metadata.get('start_line', '?'),
                "end_line": d.metadata.get('end_line', '?')
            } for d in docs],
            "latency_ms": latency_ms
        }

        return result


def test_traceable_splitter():
    """测试行号追踪功能"""
    print("=" * 70)
    print("测试行号追踪功能")
    print("=" * 70)

    # 测试文本
    test_text = """# 第一章
这是第一行内容。
这是第二行内容。

# 第二章
这是第三行内容。
这是第四行内容。
这是第五行内容。

# 第三章
这是第六行内容。
这是第七行内容。
"""

    splitter = TraceableTextSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split_with_line_numbers(test_text, "test.md")

    print(f"\n共切分 {len(chunks)} 个片段:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"片段 {i}:")
        print(f"  来源: {chunk['source']}")
        print(f"  行号: {chunk['start_line']}-{chunk['end_line']}")
        print(f"  字符位置: {chunk['char_start']}-{chunk['char_end']}")
        print(f"  内容预览: {chunk['content'][:50]}...")
        print()

    # 验证行号映射是否正确
    print("\n验证行号映射:")
    lines = test_text.split('\n')
    for i, chunk in enumerate(chunks):
        start_line_idx = chunk['start_line'] - 1
        end_line_idx = chunk['end_line'] - 1
        if start_line_idx < len(lines):
            actual_start = lines[start_line_idx]
            print(f"  片段{i+1}起始行: {actual_start[:30]}...")


def run_rag_baseline(patient_id: str = "605525", patient_file: str = None, hospital_id: str = None):
    """运行增强版RAG baseline，输出格式与原始baseline对齐"""
    import json
    from datetime import datetime
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.timestamp_utils import get_timestamped_path

    # 默认患者文件路径
    if patient_file is None:
        patient_file = f"/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_{patient_id}_input.txt"

    print(f"\n{'='*70}")
    print(f"运行增强版RAG Baseline - 患者 {patient_id}")
    print(f"{'='*70}")

    # 读取患者输入
    print(f"\n📋 读取患者输入: {patient_file}")
    try:
        with open(patient_file, 'r', encoding='utf-8') as f:
            patient_input = f.read()
        print(f"✅ 患者输入长度: {len(patient_input)} 字符")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None

    # 初始化RAG系统
    rag = EnhancedRAGBaseline()

    try:
        rag.initialize()
    except Exception as e:
        print(f"❌ RAG初始化失败: {e}")
        return None

    # 执行查询
    print(f"\n🤖 正在生成MDT报告...")
    start_time = time.time()
    result = rag.query(patient_input)
    total_latency = int((time.time() - start_time) * 1000)

    # 构建与原始baseline对齐的输出格式
    timestamp = datetime.now().isoformat()

    # 获取LLM模型信息
    model_info = "qwen3.5-plus"  # 默认模型

    # 构建input_prompt（与原始rag baseline一致）
    input_prompt = f"你是一位资深的脑转移瘤多学科诊疗（MDT）专家。请基于提供的患者信息和临床指南，生成一份结构化的MDT诊疗报告。\n\n报告应根据患者实际情况，考虑以下8个核心模块（不适用的模块可标记为N/A或简要说明原因）：\n\n## 1. 入院评估 (Admission Evaluation)\n- 患者基本信息与入院情况\n- 临床症状评估（主诉、现病史）\n- 既往病史与合并症分析\n- 影像学初步印象\n\n## 2. 原发灶处理方案 (Primary Tumor Management Plan)\n- 基于病理诊断的原发肿瘤特征\n- 分子分型与靶向治疗敏感性评估\n- 原发灶治疗策略建议\n\n## 3. 系统性管理 (Systemic Management)\n- 全身治疗方案\n- 药物选择与剂量考量\n- 围手术期用药参数（如适用）\n\n## 4. 随访方案 (Follow-up Strategy)\n- 影像学复查时间窗\n- 肿瘤标志物监测\n- 神经系统功能评估\n\n## 5. 被拒绝的替代方案及排他性论证 (Rejected Alternatives)\n- 其他可行但未被选择的方案\n- 选择当前方案而非替代方案的循证依据\n\n## 6. 围手术期管理 (Peri-procedural Management)\n- 术前准备要点（如计划手术）\n- 术后护理注意事项\n- 并发症预防策略\n\n## 7. 分子病理与基因检测 (Molecular Pathology)\n- 关键基因突变分析\n- 靶向治疗指导意义\n- 预后分子标志物\n\n## 8. 执行路径与决策轨迹 (Execution Trajectory)\n- 推荐的治疗时间线\n- 关键决策节点\n- 多学科协作流程\n\n【患者信息】\n{patient_input[:500]}...\n\n【参考指南内容】\n[指南片段内容已检索，包含行号信息]\n\n请基于临床指南和循证医学证据，生成一份专业、完整的MDT诊疗报告。"

    # 估算token使用量（基于字符数估算）
    input_tokens = len(input_prompt) // 4
    output_tokens = len(result['response']) // 4
    total_tokens = input_tokens + output_tokens

    # 构建输出结构
    output_data = {
        'patient_id': f"Case{patient_id}",
        'hospital_id': hospital_id or patient_id,
        'patient_info': patient_input[:500] + "..." if len(patient_input) > 500 else patient_input,
        'results': {
            'enhanced_rag': {
                'method': 'Enhanced_RAG',
                'report': result['response'],
                'reasoning': result['reasoning'],
                'sources': result['sources'],
                'retrieved_docs': result['retrieved_docs'],
                'latency_ms': total_latency,
                'full_output': {
                    'model': model_info,
                    'timestamp': timestamp,
                    'latency_ms': total_latency,
                    'input_prompt': input_prompt,
                    'retrieved_documents': result['retrieved_docs'],
                    'output': {
                        'content': result['response'],
                        'reasoning': result['reasoning'],
                        'role': 'assistant'
                    },
                    'usage': {
                        'input_tokens': input_tokens,
                        'output_tokens': output_tokens,
                        'total_tokens': total_tokens
                    }
                }
            }
        },
        'timestamp': timestamp
    }

    # 保存结果
    output_dir = f"/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/baseline/results_enhanced"
    import os
    os.makedirs(output_dir, exist_ok=True)

    # 使用带时间戳的文件名
    from utils.timestamp_utils import get_timestamped_filename
    output_filename = get_timestamped_filename(f"Case{patient_id}_enhanced_rag_results", "json")
    output_file = f"{output_dir}/{output_filename}"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 结果已保存: {output_file}")

    # 打印关键信息
    print(f"\n📊 执行统计:")
    print(f"  - 总延迟: {total_latency} ms")
    print(f"  - 检索文档数: {len(result['retrieved_docs'])}")
    print(f"  - 输入Tokens: {input_tokens}")
    print(f"  - 输出Tokens: {output_tokens}")
    print(f"  - 响应长度: {len(result['response'])} 字符")

    print(f"\n📚 引用来源示例 (验证行号追踪):")
    for i, doc in enumerate(result['retrieved_docs'][:3], 1):
        print(f"  [{i}] {doc['source']}")
        print(f"      Line: {doc['start_line']}-{doc['end_line']}")

    # 验证行号格式
    print(f"\n🔍 引用格式检查:")
    if '[Local:' in result['response'] and 'Line:' in result['response']:
        print("  ✅ 响应包含行号引用格式")
        import re
        citations = re.findall(r'\[Local: [^\]]+Line: \d+-\d+[^\]]*\]', result['response'])
        print(f"  📌 找到 {len(citations)} 个行号引用")
        for cite in citations[:3]:
            print(f"     {cite}")
    else:
        print("  ⚠️ 未找到标准行号引用格式")

def run_batch_rag(patients: list, output_dir: str = None):
    """批量运行RAG，复用vector store"""
    import json
    from datetime import datetime
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.timestamp_utils import get_timestamped_filename

    if output_dir is None:
        output_dir = f"/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/baseline/results_enhanced"

    import os
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"批量运行Enhanced RAG - {len(patients)}个患者")
    print(f"{'='*80}")

    # 初始化RAG系统（只执行一次）
    rag = EnhancedRAGBaseline()
    try:
        rag.initialize()
    except Exception as e:
        print(f"❌ RAG初始化失败: {e}")
        return []

    results = []

    for i, (patient_id, hospital_id, patient_file) in enumerate(patients, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(patients)}] 处理患者: {patient_id} (住院号: {hospital_id})")
        print(f"{'='*80}")

        try:
            # 读取患者输入
            with open(patient_file, 'r', encoding='utf-8') as f:
                patient_input = f.read()

            # 执行查询
            start_time = time.time()
            result = rag.query(patient_input)
            total_latency = int((time.time() - start_time) * 1000)

            timestamp = datetime.now().isoformat()
            input_tokens = len(patient_input) // 4
            output_tokens = len(result['response']) // 4
            total_tokens = input_tokens + output_tokens

            # 构建输出
            output_data = {
                'patient_id': patient_id,
                'hospital_id': hospital_id,
                'patient_info': patient_input[:500] + "..." if len(patient_input) > 500 else patient_input,
                'results': {
                    'enhanced_rag': {
                        'method': 'Enhanced_RAG',
                        'report': result['response'],
                        'reasoning': result['reasoning'],
                        'sources': result['sources'],
                        'retrieved_docs': result['retrieved_docs'],
                        'latency_ms': total_latency,
                        'full_output': {
                            'model': 'qwen3.5-plus',
                            'timestamp': timestamp,
                            'latency_ms': total_latency,
                            'input_prompt': patient_input[:1000],
                            'retrieved_documents': result['retrieved_docs'],
                            'output': {
                                'content': result['response'],
                                'reasoning': result['reasoning'],
                                'role': 'assistant'
                            },
                            'usage': {
                                'input_tokens': input_tokens,
                                'output_tokens': output_tokens,
                                'total_tokens': total_tokens
                            }
                        }
                    }
                },
                'timestamp': timestamp
            }

            # 保存结果 - 使用带时间戳的文件名
            output_filename = get_timestamped_filename(f"{patient_id}_enhanced_rag_results", "json")
            output_file = f"{output_dir}/{output_filename}"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 已保存: {output_file}")
            print(f"  - 延迟: {total_latency}ms")
            print(f"  - 输入Tokens: {input_tokens}")
            print(f"  - 输出Tokens: {output_tokens}")

            results.append((patient_id, True, output_file))

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            results.append((patient_id, False, str(e)))

    return results


if __name__ == "__main__":
    import sys

    # 检查是否有命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 仅测试行号追踪功能
        test_traceable_splitter()
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch":
        # 批量运行所有患者
        patients = [
            ("Case1", "648772", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_648772_input.txt"),
            ("Case2", "640880", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_640880_input.txt"),
            ("Case3", "868183", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_868183_input.txt"),
            ("Case4", "665548", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_665548_input.txt"),
            ("Case6", "638114", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_638114_input.txt"),
            ("Case7", "612908", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_612908_input.txt"),
            ("Case9", "708387", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_708387_input.txt"),
            ("Case10", "747724", "/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/workspace/sandbox/patient_747724_input.txt"),
        ]
        run_batch_rag(patients)
    else:
        # 运行单个患者
        patient_id = sys.argv[1] if len(sys.argv) > 1 else "605525"
        run_rag_baseline(patient_id)
