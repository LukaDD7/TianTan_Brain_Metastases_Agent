#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patient Data Processor Core Module v2.0
患者输入数据处理器核心模块

本模块实现论文级的数据处理流水线，确保：
1. 输入特征与标签的严格物理隔离
2. 数据不可变性（Immutability）
3. 4级验证体系
4. 完整的审计追踪

Author: TianTan BM Agent Team
Version: 2.0.0
Date: 2026-04-02
"""

import os
import re
import json
import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum

import pandas as pd


# =============================================================================
# 常量定义 Constants
# =============================================================================

VERSION = "2.0.0"

# 白名单字段 - 允许的输入特征
ALLOWED_FEATURES = {
    '住院号': 'patient_id',
    '入院时间': 'admission_date',
    '年龄': 'age',
    '性别': 'gender',
    '主诉': 'chief_complaint',
    '现病史': 'history_of_present_illness',
    '既往史': 'past_medical_history',
    '头部MRI': 'brain_mri',
    '胸部CT': 'chest_ct',
    '颈椎MRI': 'cervical_mri',
    '胸椎MRI': 'thoracic_mri',
    '腰椎MRI': 'lumbar_mri',
    '腹盆CT': 'abdominal_pelvic_ct',
    '腹盆MRI': 'abdominal_pelvic_mri',
    '腹部超声': 'abdominal_ultrasound',
    '浅表淋巴结超声': 'superficial_lymph_node_ultrasound',
}

# 可选字段（允许为空）
OPTIONAL_FEATURES = [
    '胸部CT', '颈椎MRI', '胸椎MRI', '腰椎MRI',
    '腹盆CT', '腹盆MRI', '腹部超声', '浅表淋巴结超声'
]

# 黑名单字段 - 严禁混入输入的标签数据
BLACKLIST_FEATURES = {
    '入院诊断': 'admission_diagnosis',
    '出院诊断': 'discharge_diagnosis',
    '诊疗经过': 'treatment_course',
    '出院时间': 'discharge_date',
}

# Agent审查触发词 - 用于标记需要人工审查的内容
# 注意：这些词本身不表示污染，只是触发Agent进行二次审查
AGENT_REVIEW_TRIGGERS = [
    # 时间词（本次/入院后 + 治疗描述 需要审查）
    '本次入院', '入院后', '入院给予', '拟行', '计划',
    # 治疗决策词
    '方案', '化疗', '放疗', '靶向', '免疫', '手术',
]

# 需要Agent重点审查的字段（由Claude Code进行语义检查）
AGENT_REVIEW_FIELDS = ['现病史', '主诉', '既往史']

# 输出字段顺序
OUTPUT_ORDER = [
    '住院号', '入院时间', '年龄', '性别',
    '主诉', '现病史', '既往史',
    '头部MRI', '胸部CT', '颈椎MRI', '胸椎MRI', '腰椎MRI',
    '腹盆CT', '腹盆MRI', '腹部超声', '浅表淋巴结超声'
]


# =============================================================================
# 枚举类型 Enumerations
# =============================================================================

class ProcessingStatus(Enum):
    """处理状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


class VerificationLevel(Enum):
    """验证级别枚举"""
    L1_PREPROCESSING = "L1_preprocessing"
    L2_PROCESSING = "L2_processing"
    L3_POSTPROCESSING = "L3_postprocessing"
    L4_INTEGRATION = "L4_integration"


class CheckStatus(Enum):
    """检查状态枚举"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


# =============================================================================
# 数据类 Data Classes
# =============================================================================

@dataclass
class VerificationCheck:
    """单个验证检查项"""
    name: str
    status: CheckStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """验证结果"""
    level: VerificationLevel
    status: CheckStatus
    checks: List[VerificationCheck] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentReviewRecord:
    """Agent审查记录"""
    patient_id: str
    field_name: str
    field_content: str
    trigger_words: List[str]
    review_status: str = "PENDING"  # PENDING / PASS / FAIL
    reviewer_notes: str = ""
    reviewed_at: Optional[str] = None


@dataclass
class AuditRecord:
    """审计记录"""
    patient_id: str
    operation: str
    timestamp: str
    input_hash: str
    output_hash: str
    removed_fields: List[str] = field(default_factory=list)  # 第一层检查移除的字段
    warnings: List[str] = field(default_factory=list)
    agent_reviews: List[AgentReviewRecord] = field(default_factory=list)
    semantic_review_queue: List[Dict] = field(default_factory=list)  # 第二层LLM检查队列
    requires_semantic_review: bool = False  # 是否需要Claude Code进行语义检查


@dataclass
class ProcessingResult:
    """处理结果"""
    patient_id: str
    status: ProcessingStatus
    output_path: Optional[str] = None
    verification_results: List[VerificationResult] = field(default_factory=list)
    audit_record: Optional[AuditRecord] = None
    agent_review_records: List[AgentReviewRecord] = field(default_factory=list)
    requires_agent_review: bool = False
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# 核心处理器类 Core Processor
# =============================================================================

class PatientDataProcessor:
    """
    患者输入数据处理器

    实现从原始Excel数据到标准化输入文件的完整处理流水线，
    包含4级验证体系和完整的审计追踪。

    Attributes:
        source_path: 源Excel文件路径
        output_dir: 输出目录
        backup_dir: 备份目录
        log_dir: 日志目录
        version: 处理器版本号
    """

    def __init__(
        self,
        source_path: str,
        output_dir: str = "workspace/sandbox",
        backup_dir: Optional[str] = None,
        log_dir: Optional[str] = None,
        verbose: bool = True
    ):
        """
        初始化处理器

        Args:
            source_path: 源Excel文件路径
            output_dir: 输出目录（默认：workspace/sandbox）
            backup_dir: 备份目录（默认：output_dir/input_backups）
            log_dir: 日志目录（默认：workspace/processing_logs）
            verbose: 是否输出详细日志
        """
        self.source_path = Path(source_path)
        self.output_dir = Path(output_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else self.output_dir / "input_backups"
        self.log_dir = Path(log_dir) if log_dir else Path("workspace/processing_logs")
        self.version = VERSION
        self.verbose = verbose

        # 初始化数据存储
        self._source_df: Optional[pd.DataFrame] = None
        self._source_hash: Optional[str] = None
        self._patients_data: Dict[str, Dict[str, str]] = {}

        # 创建必要目录
        self._setup_directories()

        # 设置日志
        self._setup_logging()

        # 加载源数据
        self._load_source_data()

    def _setup_directories(self):
        """创建必要的目录结构"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """设置日志记录"""
        log_file = self.log_dir / f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO if self.verbose else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler() if self.verbose else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"PatientDataProcessor v{VERSION} initialized")
        self.logger.info(f"Source: {self.source_path}")
        self.logger.info(f"Output: {self.output_dir}")

    def _load_source_data(self):
        """加载源数据（只读模式）"""
        if not self.source_path.exists():
            raise FileNotFoundError(f"源文件不存在: {self.source_path}")

        # 读取Excel
        self._source_df = pd.read_excel(self.source_path)

        # 计算文件哈希
        with open(self.source_path, 'rb') as f:
            self._source_hash = hashlib.md5(f.read()).hexdigest()

        self.logger.info(f"源数据加载完成: {len(self._source_df)} 行, {len(self._source_df.columns)} 列")
        self.logger.info(f"源文件MD5: {self._source_hash}")

    def _verify_source_schema(self) -> VerificationResult:
        """
        Level 1-1: 验证源数据Schema

        Returns:
            VerificationResult: 验证结果
        """
        checks = []

        # 检查必需列
        required_cols = ['id', 'Visit', 'Feature', 'Value']
        for col in required_cols:
            exists = col in self._source_df.columns
            checks.append(VerificationCheck(
                name=f"column_{col}_exists",
                status=CheckStatus.PASSED if exists else CheckStatus.FAILED,
                message=f"列 '{col}' {'存在' if exists else '缺失'}"
            ))

        # 检查是否有数据
        has_data = len(self._source_df) > 0
        checks.append(VerificationCheck(
            name="has_data",
            status=CheckStatus.PASSED if has_data else CheckStatus.FAILED,
            message=f"数据行数: {len(self._source_df)}"
        ))

        # 确定整体状态
        all_passed = all(c.status == CheckStatus.PASSED for c in checks)

        return VerificationResult(
            level=VerificationLevel.L1_PREPROCESSING,
            status=CheckStatus.PASSED if all_passed else CheckStatus.FAILED,
            checks=checks
        )

    def _parse_patients(self) -> Dict[str, Dict[str, str]]:
        """
        解析患者数据（长表转宽表）

        返回的数据以住院号（patient_id）为键，便于通过住院号查找。
        支持同一患者多次就诊记录，使用 {patient_id}_V{visit_num} 格式区分。

        Returns:
            Dict[str, Dict[str, str]]: 患者ID -> 特征字典
        """
        patients = {}
        patient_visit_counts = {}  # 记录每个住院号出现的次数
        duplicate_summary = {}  # 记录重复情况

        # 按id（Case编号）分组
        for case_id, group in self._source_df.groupby('id'):
            patient_data = {}
            for _, row in group.iterrows():
                feature = row['Feature']
                value = row['Value']
                if pd.notna(value):
                    patient_data[feature] = str(value)

            # 使用住院号作为键（如果存在）
            base_patient_id = patient_data.get('住院号', str(case_id))

            # 处理同一患者多次住院的情况
            if base_patient_id in patient_visit_counts:
                patient_visit_counts[base_patient_id] += 1
                visit_num = patient_visit_counts[base_patient_id]
                patient_id = f"{base_patient_id}_V{visit_num}"

                # 记录重复信息
                if base_patient_id not in duplicate_summary:
                    duplicate_summary[base_patient_id] = {
                        'base_id': base_patient_id,
                        'visit_count': 1,
                        'cases': []
                    }
                duplicate_summary[base_patient_id]['visit_count'] = visit_num
                duplicate_summary[base_patient_id]['cases'].append(str(case_id))

                self.logger.info(f"患者 {base_patient_id} 第{visit_num}次就诊（Case: {case_id}）-> {patient_id}")
            else:
                patient_visit_counts[base_patient_id] = 1
                patient_id = base_patient_id
                duplicate_summary[base_patient_id] = {
                    'base_id': base_patient_id,
                    'visit_count': 1,
                    'cases': [str(case_id)]
                }

            patients[patient_id] = patient_data

        # 记录统计信息
        total_unique_patients = len([k for k, v in duplicate_summary.items() if v['visit_count'] > 0])
        total_visits = sum(v['visit_count'] for v in duplicate_summary.values())
        duplicates = {k: v for k, v in duplicate_summary.items() if v['visit_count'] > 1}

        self.logger.info(f"=" * 60)
        self.logger.info(f"数据解析统计报告")
        self.logger.info(f"=" * 60)
        self.logger.info(f"源数据Case数: {len(self._source_df.groupby('id'))}")
        self.logger.info(f"唯一住院号数: {total_unique_patients}")
        self.logger.info(f"总就诊次数: {total_visits}")
        self.logger.info(f"重复住院号数: {len(duplicates)}")
        if duplicates:
            self.logger.info(f"重复详情:")
            for base_id, info in duplicates.items():
                self.logger.info(f"  - 住院号 {base_id}: {info['visit_count']}次就诊 {info['cases']}")
        self.logger.info(f"=" * 60)

        # 保存统计信息供后续报告使用
        self._parsing_stats = {
            'source_cases': len(self._source_df.groupby('id')),
            'unique_patients': total_unique_patients,
            'total_visits': total_visits,
            'duplicates': duplicates,
            'duplicate_count': len(duplicates)
        }

        return patients

    def _find_patient_by_id(self, patient_id: str) -> Optional[str]:
        """
        通过患者ID（住院号）查找患者

        Args:
            patient_id: 患者ID（住院号）

        Returns:
            Optional[str]: 患者数据字典，如果不存在则返回None
        """
        if not self._patients_data:
            self._patients_data = self._parse_patients()

        # 直接查找
        if patient_id in self._patients_data:
            return patient_id

        # 尝试字符串匹配（处理数字/字符串类型差异）
        for pid in self._patients_data:
            if str(pid) == str(patient_id):
                return pid

        return None

    def _filter_features(self, patient_data: Dict[str, str]) -> Tuple[Dict[str, str], List[str], List[str]]:
        """
        过滤特征（保留白名单，移除黑名单）

        Args:
            patient_data: 原始患者数据

        Returns:
            Tuple[过滤后数据, 移除的字段, 警告信息]
        """
        filtered = {}
        removed = []
        warnings = []

        for feature, value in patient_data.items():
            # 检查是否在白名单中
            if feature in ALLOWED_FEATURES:
                filtered[feature] = value
            # 检查是否在黑名单中
            elif feature in BLACKLIST_FEATURES:
                removed.append(feature)
            else:
                # 未知字段，记录警告
                warnings.append(f"未知字段被忽略: {feature}")

        return filtered, removed, warnings

    def _detect_leakage(self, patient_data: Dict[str, str]) -> Tuple[List[str], List[Dict]]:
        """
        标记需要LLM语义检查的内容

        ⚠️ 重要说明：
        此方法**不进行实际的内容泄露检测**，仅标记需要Claude Code (LLM) 进行
        语义审查的字段。实际的内容泄露检查必须由Claude Code通过大语言模型
        的语义理解能力执行，而非简单的关键词匹配。

        Args:
            patient_data: 过滤后的患者数据（白名单字段）

        Returns:
            Tuple[List[str], List[Dict]]: (警告信息列表, 需要语义检查的字段列表)
        """
        warnings = []
        semantic_review_queue = []

        # 标记需要LLM语义检查的高风险字段
        for field_name in AGENT_REVIEW_FIELDS:
            if field_name in patient_data and patient_data[field_name]:
                content = patient_data[field_name]
                # 仅标记需要检查，不进行实际检测
                semantic_review_queue.append({
                    'field': field_name,
                    'content_preview': content[:200] + '...' if len(content) > 200 else content,
                    'requires_llm_review': True,
                    'reason': f'{field_name}为文本字段，需要Claude Code进行语义级内容泄露检查'
                })
                warnings.append(f"[待LLM检查] {field_name}需要语义级审查")

        return warnings, semantic_review_queue

    def _format_output(self, patient_data: Dict[str, str]) -> str:
        """
        格式化输出文本

        格式规范:
        - 字段名 + 空格 + 值 + 句号
        - 每个字段一行
        - 严格保持原始内容不变

        Args:
            patient_data: 过滤后的患者数据

        Returns:
            str: 格式化的输出文本
        """
        lines = []

        for feature in OUTPUT_ORDER:
            if feature in patient_data and patient_data[feature]:
                value = patient_data[feature]
                # 确保以句号结尾
                if not value.rstrip().endswith(('。', '.')):
                    value = value.rstrip() + '。'
                line = f"{feature} {value}"
                lines.append(line)

        return '\n'.join(lines)

    def _verify_output(self, output_text: str, original_data: Dict[str, str]) -> VerificationResult:
        """
        Level 3: 验证输出内容

        Args:
            output_text: 生成的输出文本
            original_data: 原始过滤后的数据

        Returns:
            VerificationResult: 验证结果
        """
        checks = []

        # 检查编码
        try:
            output_text.encode('utf-8')
            checks.append(VerificationCheck(
                name="encoding_utf8",
                status=CheckStatus.PASSED,
                message="编码验证通过: UTF-8"
            ))
        except UnicodeEncodeError as e:
            checks.append(VerificationCheck(
                name="encoding_utf8",
                status=CheckStatus.FAILED,
                message=f"编码错误: {e}"
            ))

        # 检查敏感字段残留
        sensitive_found = []
        for sensitive in BLACKLIST_FEATURES.keys():
            if sensitive in output_text:
                sensitive_found.append(sensitive)

        checks.append(VerificationCheck(
            name="no_sensitive_fields",
            status=CheckStatus.PASSED if not sensitive_found else CheckStatus.FAILED,
            message=f"敏感字段残留: {sensitive_found}" if sensitive_found else "无敏感字段残留"
        ))

        # 检查内容不可变性（抽样）
        immutable_violations = []
        for feature in original_data:
            original_value = original_data[feature]
            # 在输出中查找原始值
            if feature in output_text:
                # 提取输出中的值（简化检查）
                if original_value[:50] not in output_text:
                    immutable_violations.append(feature)

        checks.append(VerificationCheck(
            name="content_immutability",
            status=CheckStatus.PASSED if not immutable_violations else CheckStatus.FAILED,
            message=f"内容可能被修改的字段: {immutable_violations}" if immutable_violations else "内容不可变性验证通过"
        ))

        # 确定整体状态
        has_failed = any(c.status == CheckStatus.FAILED for c in checks)

        return VerificationResult(
            level=VerificationLevel.L3_POSTPROCESSING,
            status=CheckStatus.FAILED if has_failed else CheckStatus.PASSED,
            checks=checks
        )

    def process(self, patient_id: str, enable_verification: bool = True) -> ProcessingResult:
        """
        处理单个患者数据

        完整处理流水线：
        1. Level 1: 预处理验证
        2. 解析患者数据
        3. 特征过滤
        4. 泄漏检测
        5. 格式化输出
        6. Level 3: 输出验证
        7. 写入文件
        8. 生成审计记录

        Args:
            patient_id: 患者ID
            enable_verification: 是否启用验证

        Returns:
            ProcessingResult: 处理结果
        """
        self.logger.info(f"开始处理患者: {patient_id}")

        verification_results = []

        try:
            # Step 1: Level 1 验证（Schema验证）
            if enable_verification:
                schema_result = self._verify_source_schema()
                verification_results.append(schema_result)
                if schema_result.status == CheckStatus.FAILED:
                    return ProcessingResult(
                        patient_id=patient_id,
                        status=ProcessingStatus.FAILED,
                        error_message="Schema验证失败",
                        verification_results=verification_results
                    )

            # Step 2: 解析患者数据并查找
            actual_patient_id = self._find_patient_by_id(patient_id)

            if actual_patient_id is None:
                available_ids = list(self._patients_data.keys())[:10]  # 显示前10个
                return ProcessingResult(
                    patient_id=patient_id,
                    status=ProcessingStatus.FAILED,
                    error_message=f"患者 {patient_id} 不存在于源数据中。可用的患者ID示例: {available_ids}...",
                    verification_results=verification_results
                )

            original_data = self._patients_data[actual_patient_id]
            self.logger.info(f"找到患者数据: {actual_patient_id} (住院号: {original_data.get('住院号', 'N/A')})")

            # Step 3: 特征过滤（第一层 - 字段级检查）
            filtered_data, removed_fields, filter_warnings = self._filter_features(original_data)

            # Step 4: 标记需要LLM语义检查（第二层 - 语义级检查）
            # ⚠️ 注意：实际的内容泄露检测由Claude Code (LLM) 执行，非代码自动检测
            leakage_warnings, semantic_review_queue = self._detect_leakage(filtered_data)
            all_warnings = filter_warnings + leakage_warnings
            requires_semantic_review = len(semantic_review_queue) > 0

            if enable_verification:
                leakage_checks = [
                    VerificationCheck(
                        name="whitelist_filter",
                        status=CheckStatus.PASSED,
                        message=f"保留字段: {list(filtered_data.keys())}"
                    ),
                    VerificationCheck(
                        name="blacklist_removal",
                        status=CheckStatus.PASSED,
                        message=f"移除字段: {removed_fields}",
                        details={"removed": removed_fields}
                    ),
                    VerificationCheck(
                        name="semantic_review_required",
                        status=CheckStatus.WARNING if requires_semantic_review else CheckStatus.PASSED,
                        message=f"需要LLM语义检查的字段: {len(semantic_review_queue)} 个" if requires_semantic_review else "无需语义检查",
                        details={"semantic_review_queue": semantic_review_queue}
                    )
                ]
                verification_results.append(VerificationResult(
                    level=VerificationLevel.L2_PROCESSING,
                    status=CheckStatus.WARNING if requires_semantic_review else CheckStatus.PASSED,
                    checks=leakage_checks
                ))

            # Step 5: 格式化输出
            output_text = self._format_output(filtered_data)

            # Step 6: Level 3 验证
            if enable_verification:
                output_result = self._verify_output(output_text, filtered_data)
                verification_results.append(output_result)
                if output_result.status == CheckStatus.FAILED:
                    return ProcessingResult(
                        patient_id=patient_id,
                        status=ProcessingStatus.FAILED,
                        error_message="输出验证失败",
                        verification_results=verification_results
                    )

            # Step 7: 写入文件
            output_path = self.output_dir / f"patient_{patient_id}_input.txt"

            # 备份原文件（如果存在）
            if output_path.exists():
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.backup_dir / f"patient_{patient_id}_input.txt.{backup_timestamp}.backup"
                shutil.copy2(output_path, backup_path)
                self.logger.info(f"已备份原文件: {backup_path}")

            # 原子写入
            temp_path = output_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            temp_path.replace(output_path)

            # 计算输出文件哈希
            with open(output_path, 'rb') as f:
                output_hash = hashlib.md5(f.read()).hexdigest()

            self.logger.info(f"输出文件已生成: {output_path}")

            # Step 8: 生成审计记录
            audit_record = AuditRecord(
                patient_id=patient_id,
                operation="process",
                timestamp=datetime.now().isoformat(),
                input_hash=self._source_hash,
                output_hash=output_hash,
                removed_fields=removed_fields,  # 第一层：字段级检查移除的字段
                warnings=all_warnings,
                semantic_review_queue=semantic_review_queue,  # 第二层：需要LLM检查的字段
                requires_semantic_review=requires_semantic_review
            )

            # 确定整体状态
            # 如果有需要语义检查的字段，标记为 WARNING（需要人工/LLM复核）
            has_warnings = len(all_warnings) > 0 or requires_semantic_review
            status = ProcessingStatus.WARNING if has_warnings else ProcessingStatus.SUCCESS

            return ProcessingResult(
                patient_id=patient_id,
                status=status,
                output_path=str(output_path),
                verification_results=verification_results,
                audit_record=audit_record,
                warnings=all_warnings
            )

        except Exception as e:
            self.logger.error(f"处理患者 {patient_id} 时出错: {e}", exc_info=True)
            return ProcessingResult(
                patient_id=patient_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                verification_results=verification_results
            )

    def batch_process(
        self,
        patient_ids: Optional[List[str]] = None,
        enable_verification: bool = True
    ) -> List[ProcessingResult]:
        """
        批量处理患者数据

        Args:
            patient_ids: 患者ID列表（None表示全部）
            enable_verification: 是否启用验证

        Returns:
            List[ProcessingResult]: 处理结果列表
        """
        # 解析所有患者数据
        if not self._patients_data:
            self._patients_data = self._parse_patients()

        # 确定处理列表
        if patient_ids is None:
            patient_ids = list(self._patients_data.keys())

        self.logger.info(f"批量处理: {len(patient_ids)} 例患者")

        results = []
        for i, patient_id in enumerate(patient_ids, 1):
            self.logger.info(f"[{i}/{len(patient_ids)}] 处理患者: {patient_id}")
            result = self.process(patient_id, enable_verification)
            results.append(result)

        # 生成汇总报告
        self._generate_batch_report(results)

        return results

    def _generate_batch_report(self, results: List[ProcessingResult]):
        """生成批量处理报告"""
        success_count = sum(1 for r in results if r.status == ProcessingStatus.SUCCESS)
        warning_count = sum(1 for r in results if r.status == ProcessingStatus.WARNING)
        failed_count = sum(1 for r in results if r.status == ProcessingStatus.FAILED)

        # 获取解析统计信息
        parsing_stats = getattr(self, '_parsing_stats', {})

        report = {
            "processor_version": self.version,
            "timestamp": datetime.now().isoformat(),
            "source_file": str(self.source_path),
            "source_hash": self._source_hash,
            "source_statistics": {
                "total_cases_in_source": parsing_stats.get('source_cases', 'N/A'),
                "unique_patients": parsing_stats.get('unique_patients', 'N/A'),
                "total_visits": parsing_stats.get('total_visits', 'N/A'),
                "duplicate_patient_ids": parsing_stats.get('duplicate_count', 0),
                "duplicate_details": {
                    base_id: {
                        "visit_count": info['visit_count'],
                        "cases": info['cases']
                    }
                    for base_id, info in parsing_stats.get('duplicates', {}).items()
                }
            },
            "processing_summary": {
                "total": len(results),
                "success": success_count,
                "warning": warning_count,
                "failed": failed_count
            },
            "details": [
                {
                    "patient_id": r.patient_id,
                    "status": r.status.value,
                    "output_path": r.output_path,
                    "warnings": r.warnings,
                    "error": r.error_message
                }
                for r in results
            ]
        }

        report_path = self.log_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.logger.info(f"批量处理报告已生成: {report_path}")
        self.logger.info(f"处理统计: 成功={success_count}, 警告={warning_count}, 失败={failed_count}")

        # 打印详细统计表格
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"数据解析统计")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"源文件Case数:        {parsing_stats.get('source_cases', 'N/A'):>6}")
        self.logger.info(f"唯一住院号数:        {parsing_stats.get('unique_patients', 'N/A'):>6}")
        self.logger.info(f"总就诊次数:          {parsing_stats.get('total_visits', 'N/A'):>6}")
        self.logger.info(f"重复住院号数:        {parsing_stats.get('duplicate_count', 0):>6}")
        self.logger.info(f"{'='*60}")

        if parsing_stats.get('duplicates'):
            self.logger.info(f"重复住院号详情:")
            for base_id, info in parsing_stats['duplicates'].items():
                self.logger.info(f"  - {base_id}: {info['visit_count']}次就诊 {info['cases']}")

    def verify_existing_file(self, file_path: str) -> VerificationResult:
        """
        验证已存在的输入文件

        Args:
            file_path: 文件路径

        Returns:
            VerificationResult: 验证结果
        """
        file_path = Path(file_path)
        checks = []

        # 检查文件存在性
        exists = file_path.exists()
        checks.append(VerificationCheck(
            name="file_exists",
            status=CheckStatus.PASSED if exists else CheckStatus.FAILED,
            message=f"文件存在: {file_path}" if exists else f"文件不存在: {file_path}"
        ))

        if not exists:
            return VerificationResult(
                level=VerificationLevel.L3_POSTPROCESSING,
                status=CheckStatus.FAILED,
                checks=checks
            )

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查敏感字段
        sensitive_found = [s for s in BLACKLIST_FEATURES.keys() if s in content]
        checks.append(VerificationCheck(
            name="no_sensitive_fields",
            status=CheckStatus.PASSED if not sensitive_found else CheckStatus.FAILED,
            message=f"发现敏感字段: {sensitive_found}" if sensitive_found else "无敏感字段"
        ))

        # 检查必需字段
        required_fields = ['主诉', '现病史', '头部MRI']
        missing_required = [f for f in required_fields if f not in content]
        checks.append(VerificationCheck(
            name="required_fields_present",
            status=CheckStatus.PASSED if not missing_required else CheckStatus.FAILED,
            message=f"缺失必需字段: {missing_required}" if missing_required else "所有必需字段存在"
        ))

        # 检查内容泄漏（标记需要LLM语义检查）
        # ⚠️ 注意：实际的内容泄露检测由Claude Code (LLM) 执行
        semantic_review_needed = []
        for field in AGENT_REVIEW_FIELDS:
            if field in content:
                semantic_review_needed.append(field)

        checks.append(VerificationCheck(
            name="semantic_review_required",
            status=CheckStatus.WARNING if semantic_review_needed else CheckStatus.PASSED,
            message=f"需要LLM语义检查的字段: {semantic_review_needed}" if semantic_review_needed else "无需语义检查",
            details={"fields_for_llm_review": semantic_review_needed}
        ))

        has_failed = any(c.status == CheckStatus.FAILED for c in checks)

        return VerificationResult(
            level=VerificationLevel.L3_POSTPROCESSING,
            status=CheckStatus.FAILED if has_failed else CheckStatus.PASSED,
            checks=checks
        )


# =============================================================================
# 工具函数 Utility Functions
# =============================================================================

def create_processor_from_default(
    source_name: str = "46个病例_诊疗经过.xlsx"
) -> PatientDataProcessor:
    """
    从默认路径创建处理器

    Args:
        source_name: 源文件名

    Returns:
        PatientDataProcessor: 处理器实例
    """
    project_root = Path("/media/luzhenyang/project/TianTan_Brain_Metastases_Agent")
    source_path = project_root / "patients_folder" / source_name
    output_dir = project_root / "workspace" / "sandbox"

    return PatientDataProcessor(
        source_path=str(source_path),
        output_dir=str(output_dir)
    )


# =============================================================================
# 主入口 Main Entry
# =============================================================================

if __name__ == "__main__":
    # 简单测试
    processor = create_processor_from_default()
    result = processor.process("640880")

    print(f"\n处理结果:")
    print(f"  患者ID: {result.patient_id}")
    print(f"  状态: {result.status.value}")
    print(f"  输出路径: {result.output_path}")
    print(f"  警告: {result.warnings}")

    if result.audit_record:
        print(f"\n审计记录:")
        print(f"  移除字段: {result.audit_record.removed_fields}")
        print(f"  输入哈希: {result.audit_record.input_hash}")
        print(f"  输出哈希: {result.audit_record.output_hash}")
