"""
schemas/debate_schema.py
v7.0 — Structured Debate Protocol (re-exports from conflict_schema for clarity)

WS-6: Inter-Agent Structured Debate
"""

# Re-export debate-specific classes for clean imports
from schemas.conflict_schema import DebateResponse, DebateRecord

__all__ = ["DebateResponse", "DebateRecord"]
