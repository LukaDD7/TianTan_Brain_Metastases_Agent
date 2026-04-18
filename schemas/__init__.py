"""
schemas/__init__.py
v6.0 — Pydantic Schema Package
"""

from schemas.mdt_report import MDTReport, ClinicalClaim, ClinicalIntervention
from schemas.subagent_outputs import (
    NeurosurgeryOutput,
    RadiationOncologyOutput,
    MedicalOncologyOutput,
    MolecularPathologyOutput,
    AuditorOutput,
    CitedClaim,
    AuditFinding,
    ConflictFlag,
)

__all__ = [
    # MDT Report
    "MDTReport",
    "ClinicalClaim",
    "ClinicalIntervention",
    # SubAgent Outputs
    "NeurosurgeryOutput",
    "RadiationOncologyOutput",
    "MedicalOncologyOutput",
    "MolecularPathologyOutput",
    "AuditorOutput",
    "CitedClaim",
    "AuditFinding",
    "ConflictFlag",
]
