"""agent-session-gates: deterministic pre-flight gates for agent workflows.

Public API:

    from agent_session_gates import (
        GateStatus, GateResult,
        Decision, JobSpec, Evidence, EvidenceKind,
        GroundingGate, FileEvidenceResolver,
        DispatchLock,
        GateRunner, RunReport,
    )
"""

from __future__ import annotations

from .dispatch import DispatchLock
from .grounding import EvidenceResolver, FileEvidenceResolver, GroundingGate
from .models import Decision, Evidence, EvidenceKind, JobSpec
from .result import GateResult, GateStatus
from .runner import GateRunner, RunReport

__version__ = "0.1.0"

__all__ = [
    "GateStatus",
    "GateResult",
    "Decision",
    "JobSpec",
    "Evidence",
    "EvidenceKind",
    "GroundingGate",
    "FileEvidenceResolver",
    "EvidenceResolver",
    "DispatchLock",
    "GateRunner",
    "RunReport",
    "__version__",
]
