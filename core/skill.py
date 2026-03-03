#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BaseSkill - 医疗 Agent Skill 基座 (v2.0 重构版)

设计原则：
1. 零 LangChain 依赖，原生支持 Anthropic/Claude Tool Schema
2. Pydantic v2 强类型约束，确保医疗输入参数安全
3. 显式上下文传递 (SkillContext)，支持跨技能状态共享
4. 统一的错误重试机制 (指数退避)，提高外部 API 调用可靠性
5. 渐进式披露准备：支持 SKILL.md 元数据加载

Author: TianTan Brain Metastases Agent Team
Version: 2.0.0
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Generic, TypeVar
from datetime import datetime
import inspect
import json
import time
import os

# === Pydantic v2 导入 ===
try:
    from pydantic import BaseModel, Field, ConfigDict
    from pydantic_core import SchemaValidator
except ImportError:
    raise ImportError("Pydantic v2 is required. Install with: pip install pydantic>=2.0")


# === 类型定义 ===
T = TypeVar('T')  # 用于 Skill 输入 Schema 的泛型


# =============================================================================
# SkillContext - 跨技能共享上下文 (显式传递)
# =============================================================================

class SkillCallRecord(BaseModel):
    """单次 Skill 调用记录 (用于审计和调试)"""
    skill_name: str
    timestamp: datetime
    input_args: Dict[str, Any]
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    retry_count: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SkillContext:
    """
    跨 Skill 的共享上下文容器。

    设计原则：
    - 显式传递：在 execute() 方法中通过参数显式接收
    - 会话隔离：每个患者问诊会话一个独立 Context
    - 审计追踪：自动记录所有 Skill 调用历史

    使用示例：
        context = SkillContext(session_id="patient_123")
        context.set("patient_info", {"name": "张三", "age": 58})

        # Skill A 执行
        result_a = skill_a.execute(context=context, ...)
        context.set("skill_a_result", result_a)

        # Skill B 执行时可以读取 Skill A 的结果
        result_b = skill_b.execute(context=context, ...)
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._created_at = datetime.now()
        self._data: Dict[str, Any] = {}
        self._history: List[SkillCallRecord] = []
        self._metadata: Dict[str, Any] = {}

    # --- 数据存取 ---
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self._data[key] = value

    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._data

    def delete(self, key: str) -> bool:
        """删除上下文数据"""
        if key in self._data:
            del self._data[key]
            return True
        return False

    # --- 元数据管理 ---
    def set_metadata(self, key: str, value: Any) -> None:
        """设置会话元数据 (如患者 ID、病例号等)"""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取会话元数据"""
        return self._metadata.get(key, default)

    # --- 调用历史 ---
    def record_call(self, record: SkillCallRecord) -> None:
        """记录一次 Skill 调用"""
        self._history.append(record)

    def get_history(self) -> List[SkillCallRecord]:
        """获取所有 Skill 调用历史"""
        return self._history.copy()

    def get_last_call(self, skill_name: Optional[str] = None) -> Optional[SkillCallRecord]:
        """获取最后一次 (或指定 Skill 的) 调用记录"""
        if not self._history:
            return None
        if skill_name:
            for record in reversed(self._history):
                if record.skill_name == skill_name:
                    return record
            return None
        return self._history[-1]

    # --- 生命周期 ---
    def clear_data(self) -> None:
        """清空数据 (保留历史)"""
        self._data.clear()

    def get_summary(self) -> Dict[str, Any]:
        """获取上下文摘要 (用于调试)"""
        return {
            "session_id": self.session_id,
            "created_at": self._created_at.isoformat(),
            "data_keys": list(self._data.keys()),
            "call_count": len(self._history),
            "metadata_keys": list(self._metadata.keys())
        }

    def __repr__(self) -> str:
        return f"SkillContext(session_id={self.session_id!r}, calls={len(self._history)})"


# =============================================================================
# 重试配置
# =============================================================================

class RetryConfig(BaseModel):
    """重试配置"""
    max_retries: int = 3
    initial_delay_ms: int = 1000  # 初始延迟 1 秒
    max_delay_ms: int = 10000     # 最大延迟 10 秒
    exponential_base: float = 2.0  # 指数退避底数
    retryable_exceptions: List[Type[Exception]] = [
        TimeoutError,
        ConnectionError,
        OSError,
    ]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_delay(self, attempt: int) -> float:
        """计算第 N 次重试的延迟时间 (秒)"""
        delay_ms = min(
            self.initial_delay_ms * (self.exponential_base ** attempt),
            self.max_delay_ms
        )
        return delay_ms / 1000.0


# =============================================================================
# BaseSkill - 抽象基类
# =============================================================================

class BaseSkill(ABC, Generic[T]):
    """
    所有医疗 Skill 的抽象基类。

    子类需要实现：
    1. name: Skill 名称 (英文，用于 Tool 调用)
    2. description: Skill 描述 (英文，告诉 LLM 何时使用)
    3. input_schema_class: Pydantic 模型类，定义输入参数 Schema
    4. execute(args, context): 执行逻辑

    核心特性：
    - Pydantic v2 强类型验证
    - 统一的重试机制 (指数退避)
    - 显式上下文传递
    - 调用审计追踪

    示例：
        class PDFInspectorInput(BaseModel):
            file_path: str = Field(..., description="Path to the PDF file")
            extract_images: bool = Field(default=False, description="Whether to extract images")

        class PDFInspector(BaseSkill[PDFInspectorInput]):
            name = "parse_medical_pdf"
            description = "Parse medical PDF and extract text and images"
            input_schema_class = PDFInspectorInput

            def execute(self, args: PDFInspectorInput, context: Optional[SkillContext] = None) -> str:
                # args.file_path 已获得类型安全访问
                # context 可用于跨技能状态传递
                return result
    """

    # === 子类必须覆盖的类属性 ===
    name: str = ""
    description: str = ""
    input_schema_class: Optional[Type[T]] = None  # Pydantic 模型类

    # === 可选配置 ===
    retry_config: RetryConfig = RetryConfig()
    strict: bool = True  # 是否启用严格模式 (强制 schema 验证)

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        定义输入参数的 JSON Schema (用于导出到 LLM)。

        默认实现会从 input_schema_class 自动生成。
        子类可以覆盖此属性来自定义 Schema。

        返回格式必须符合 Anthropic Tool Use API:
        {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string|integer|boolean|array|object",
                    "description": "...",
                    "enum": [...],  # 可选
                    "default": ...   # 可选
                }
            },
            "required": ["param1", ...]  # 可选
        }
        """
        if self.input_schema_class is not None:
            return self.input_schema_class.model_json_schema()
        return {"type": "object", "properties": {}}

    @abstractmethod
    def execute(self, args: T, context: Optional[SkillContext] = None) -> Any:
        """
        执行 Skill 的核心逻辑。

        Args:
            args: 已验证的输入参数 (Pydantic 模型实例)
            context: 可选的跨技能上下文 (显式传递)

        Returns:
            执行结果 (字符串、字典或其他可序列化对象)

        Raises:
            SkillExecutionError: 执行失败时抛出
        """
        pass

    def validate_input(self, raw_input: Dict[str, Any]) -> T:
        """
        验证输入参数并转换为 Pydantic 模型。

        Args:
            raw_input: 原始输入字典 (通常来自 LLM 工具调用)

        Returns:
            验证后的 Pydantic 模型实例

        Raises:
            SkillValidationError: 验证失败时抛出
        """
        if self.input_schema_class is None:
            # 如果没有定义 schema_class，返回原始输入
            return raw_input  # type: ignore

        try:
            return self.input_schema_class(**raw_input)
        except Exception as e:
            raise SkillValidationError(
                f"Input validation failed for {self.name}: {str(e)}"
            ) from e

    def execute_with_retry(self, raw_input: Dict[str, Any], context: Optional[SkillContext] = None) -> Any:
        """
        带重试的执行入口 (内部调用)。

        自动处理：
        1. 输入验证
        2. 指数退避重试
        3. 调用历史审计

        Args:
            raw_input: 原始输入字典
            context: 可选的跨技能上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()
        retry_count = 0
        last_error: Optional[Exception] = None

        # 输入验证 (严格模式下)
        if self.strict and self.input_schema_class is not None:
            args = self.validate_input(raw_input)
        else:
            args = raw_input  # type: ignore

        # 重试循环
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # 执行 Skill
                result = self.execute(args, context)

                # 记录成功调用
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                record = SkillCallRecord(
                    skill_name=self.name,
                    timestamp=start_time,
                    input_args=raw_input,
                    output=result,
                    duration_ms=duration_ms,
                    retry_count=retry_count
                )
                if context:
                    context.record_call(record)

                return result

            except Exception as e:
                last_error = e

                # 检查是否可重试
                if not self._is_retryable(e):
                    break

                # 达到最大重试次数
                if attempt >= self.retry_config.max_retries:
                    break

                # 指数退避
                delay = self.retry_config.get_delay(attempt)
                time.sleep(delay)
                retry_count += 1

        # 所有重试失败
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        record = SkillCallRecord(
            skill_name=self.name,
            timestamp=start_time,
            input_args=raw_input,
            error=str(last_error),
            duration_ms=duration_ms,
            retry_count=retry_count
        )
        if context:
            context.record_call(record)

        raise SkillExecutionError(
            f"Skill '{self.name}' failed after {retry_count + 1} attempts: {last_error}"
        ) from last_error

    def _is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        for exc_type in self.retry_config.retryable_exceptions:
            if isinstance(error, exc_type):
                return True
        return False

    def to_tool_definition(self) -> Dict[str, Any]:
        """
        生成 Anthropic/Claude 原生的 Tool 定义。

        返回格式：
        {
            "name": "skill_name",
            "description": "Skill description",
            "input_schema": { ... }
        }

        用于直接传递给 Claude API 的 tools 参数。
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }

    def to_openai_tool(self) -> Dict[str, Any]:
        """
        生成 OpenAI Function Calling 格式的 Tool 定义。

        返回格式：
        {
            "type": "function",
            "function": {
                "name": "skill_name",
                "description": "Skill description",
                "parameters": { ... }
            }
        }
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


# =============================================================================
# 异常类
# =============================================================================

class SkillExecutionError(Exception):
    """Skill 执行异常时抛出"""
    pass


class SkillValidationError(Exception):
    """Skill 输入验证失败时抛出"""
    pass


# =============================================================================
# SkillRegistry - 轻量级注册中心
# =============================================================================

class SkillRegistry:
    """
    轻量级 Skill 注册中心。

    功能：
    1. 动态注册 Skill 实例
    2. 按名称获取 Skill
    3. 批量导出 Tool Definitions
    4. 支持从 SKILL.md 加载元数据 (渐进式披露准备)

    使用示例：
        registry = SkillRegistry()
        registry.register(PDFInspector())
        registry.register(ClinicalWriter())

        # 获取所有 Tool 定义 (用于 API 调用)
        tools = registry.get_all_tool_definitions()

        # 创建上下文并执行
        context = SkillContext(session_id="patient_123")
        skill = registry.get("parse_medical_pdf")
        result = skill.execute_with_retry({"file_path": "..."}, context=context)
    """

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._skill_metadata: Dict[str, Dict[str, Any]] = {}  # 用于存储 SKILL.md 元数据

    def register(self, skill: BaseSkill) -> None:
        """注册一个 Skill 实例"""
        if not isinstance(skill, BaseSkill):
            raise TypeError(f"Expected BaseSkill subclass, got {type(skill)}")
        if not skill.name:
            raise ValueError("Skill must have a non-empty 'name' attribute")

        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[BaseSkill]:
        """按名称获取 Skill"""
        return self._skills.get(name)

    def has(self, name: str) -> bool:
        """检查 Skill 是否已注册"""
        return name in self._skills

    def unregister(self, name: str) -> bool:
        """注销一个 Skill"""
        if name in self._skills:
            del self._skills[name]
            return True
        return False

    def list_names(self) -> List[str]:
        """列出所有已注册的 Skill 名称"""
        return list(self._skills.keys())

    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        导出所有 Skill 的 Tool 定义 (Anthropic 格式)。

        直接用于 Claude API:
            response = client.messages.create(
                model="claude-opus-4-6",
                tools=registry.get_all_tool_definitions(),
                ...
            )
        """
        return [skill.to_tool_definition() for skill in self._skills.values()]

    def get_all_openai_tools(self) -> List[Dict[str, Any]]:
        """导出所有 Skill 的 OpenAI 格式 Tool 定义"""
        return [skill.to_openai_tool() for skill in self._skills.values()]

    def __len__(self) -> int:
        return len(self._skills)

    def __iter__(self):
        return iter(self._skills.values())

    def __repr__(self) -> str:
        names = ", ".join(self._skills.keys())
        return f"SkillRegistry([{names}])"

    # --- SKILL.md 支持 (渐进式披露准备) ---

    def load_skill_metadata(self, skill_dir: str) -> Optional[Dict[str, Any]]:
        """
        从 SKILL.md 加载元数据 (不加载完整技能)。

        返回 YAML frontmatter 中的 metadata 部分。
        用于启动时的"发现阶段"。
        """
        import re

        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_md_path):
            return None

        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 YAML frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return None

        try:
            import yaml
            frontmatter = yaml.safe_load(match.group(1))
            self._skill_metadata[frontmatter.get('name', '')] = frontmatter
            return frontmatter
        except Exception:
            return None

    # --- 目录加载 (保留向后兼容) ---

    @classmethod
    def from_directory(cls, skills_dir: str, prefix: str = "") -> "SkillRegistry":
        """
        从目录自动加载所有 Skill。

        约定：
        - 每个 Skill 放在独立子目录中：skills/<skill_name>/skill.py
        - 或者扁平放置：skills/<skill_name>_skill.py

        Args:
            skills_dir: Skills 目录路径
            prefix: 模块名前缀 (如 "skills.")

        Returns:
            自动填充的 SkillRegistry 实例
        """
        import importlib

        registry = cls()

        if not os.path.isdir(skills_dir):
            raise ValueError(f"Skills directory not found: {skills_dir}")

        # 扫描子目录
        for item in os.listdir(skills_dir):
            item_path = os.path.join(skills_dir, item)

            # 模式 1: 子目录模式 skills/<name>/skill.py
            if os.path.isdir(item_path):
                skill_file = os.path.join(item_path, "skill.py")
                if os.path.exists(skill_file):
                    module_name = f"{prefix}{item}.skill" if prefix else f"{item}.skill"
                    registry._load_from_module(module_name, skill_file)

                # 同时尝试加载 SKILL.md 元数据
                registry.load_skill_metadata(item_path)

            # 模式 2: 扁平模式 skills/<name>_skill.py
            elif item.endswith("_skill.py"):
                skill_name = item[:-9]  # 移除 "_skill.py"
                module_name = f"{prefix}{item[:-3]}" if prefix else item[:-3]
                registry._load_from_module(module_name, item_path)

        return registry

    def _load_from_module(self, module_name: str, file_path: str) -> None:
        """从模块文件加载 Skill"""
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 查找模块中所有 BaseSkill 的子类实例
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, BaseSkill):
                self.register(attr)


# =============================================================================
# 辅助函数：医疗数据类型 Schema
# =============================================================================

class MedicalDataType(str):
    """医疗数据类型枚举"""
    PDF_REPORT = "pdf_report"
    DICOM_SERIES = "dicom_series"
    VCF_FILE = "vcf_genomic_data"
    PATHOLOGY_WSI = "pathology_whole_slide_image"
    TEXT_SNIPPET = "text_snippet"


def pdf_report_schema(required: bool = True, with_page_range: bool = False) -> Dict[str, Any]:
    """生成 PDF 报告的输入 Schema"""
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "PDF 文件的绝对或相对路径"
            }
        }
    }

    if with_page_range:
        schema["properties"]["page_start"] = {
            "type": "integer",
            "description": "起始页码 (1-indexed)",
            "default": 1
        }
        schema["properties"]["page_end"] = {
            "type": "integer",
            "description": "结束页码 (可选)"
        }

    if required:
        schema["required"] = ["file_path"]

    return schema


def dicom_series_schema(required: bool = True) -> Dict[str, Any]:
    """生成 DICOM 序列的输入 Schema"""
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "series_uid": {
                "type": "string",
                "description": "DICOM Series UID"
            },
            "dicom_dir": {
                "type": "string",
                "description": "DICOM 文件所在目录"
            }
        }
    }

    if required:
        schema["required"] = ["series_uid"]

    return schema
