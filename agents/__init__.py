"""
agents/__init__.py
v6.0 — SubAgent System Prompts Package
"""

from agents.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from agents.neurosurgery_prompt import NEUROSURGERY_SYSTEM_PROMPT
from agents.radiation_prompt import RADIATION_SYSTEM_PROMPT
from agents.medical_oncology_prompt import MEDICAL_ONCOLOGY_SYSTEM_PROMPT
from agents.molecular_pathology_prompt import MOLECULAR_PATHOLOGY_SYSTEM_PROMPT
from agents.auditor_prompt import AUDITOR_SYSTEM_PROMPT

__all__ = [
    "ORCHESTRATOR_SYSTEM_PROMPT",
    "NEUROSURGERY_SYSTEM_PROMPT",
    "RADIATION_SYSTEM_PROMPT",
    "MEDICAL_ONCOLOGY_SYSTEM_PROMPT",
    "MOLECULAR_PATHOLOGY_SYSTEM_PROMPT",
    "AUDITOR_SYSTEM_PROMPT",
]
