#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patient Data Processor Skill
患者数据处理器Skill

本模块提供医疗AI评估所需的标准化患者数据预处理功能，
确保输入特征与Ground Truth标签的严格物理隔离。

Usage:
    from skills.patient_data_processor import PatientDataProcessor

    processor = PatientDataProcessor(
        source_path="patients_folder/46个病例_诊疗经过.xlsx",
        output_dir="workspace/sandbox"
    )

    result = processor.process("640880")

Author: TianTan BM Agent Team
Version: 2.0.0
"""

from .scripts.processor_core import (
    PatientDataProcessor,
    ProcessingResult,
    VerificationResult,
    AuditRecord,
    ProcessingStatus,
    VerificationLevel,
    CheckStatus,
    create_processor_from_default,
)

__version__ = "2.0.0"
__author__ = "TianTan BM Agent Team"

__all__ = [
    'PatientDataProcessor',
    'ProcessingResult',
    'VerificationResult',
    'AuditRecord',
    'ProcessingStatus',
    'VerificationLevel',
    'CheckStatus',
    'create_processor_from_default',
]
