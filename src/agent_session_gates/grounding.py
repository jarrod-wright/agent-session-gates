"""Grounding gate.

Principle: no decision is ratified without measured grounding. A decision
must carry at least one well-formed piece of evidence. If a resolver is
supplied, file evidence is additionally *verified* (the file must exist and,
when a checksum is given, its SHA-256 must match) -- turning a structural
assertion into a re-runnable measurement.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from .models import Decision, Evidence, EvidenceKind
from .result import GateResult, GateStatus


class EvidenceResolver(Protocol):
    """Verifies that a piece of evidence actually resolves.

    Returns ``None`` when the evidence is out of scope for this resolver
    (e.g. a URL passed to a file resolver), or a failure string describing
    why resolution failed.
    """

    def resolve(self, evidence: Evidence) -> str | None:
        ...


class FileEvidenceResolver:
    """Resolves ``FILE`` evidence against the local filesystem."""

    def resolve(self, evidence: Evidence) -> str | None:
        if evidence.kind is not EvidenceKind.FILE:
            return None
        path = Path(evidence.locator)
        if not path.is_file():
            return f"file not found: {evidence.locator}"
        if evidence.checksum is not None:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest.lower() != evidence.checksum.lower():
                return (
                    f"checksum mismatch for {evidence.locator}: "
                    f"expected {evidence.checksum}, measured {digest}"
                )
        return None


class GroundingGate:
    """Blocks a decision that is not grounded in evidence."""

    name = "grounding"

    def __init__(
        self,
        resolver: EvidenceResolver | None = None,
        require_checksum: bool = False,
    ) -> None:
        self._resolver = resolver
        self._require_checksum = require_checksum

    def check(self, decision: Decision) -> GateResult:
        count = len(decision.evidence)
        if count == 0:
            return GateResult(
                gate=self.name,
                status=GateStatus.BLOCK,
                reason="decision is ungrounded: no evidence supplied",
                details={"decision_id": decision.id, "evidence_count": 0},
            )

        for evidence in decision.evidence:
            if not evidence.locator.strip():
                return GateResult(
                    gate=self.name,
                    status=GateStatus.BLOCK,
                    reason="evidence has a blank locator",
                    details={"decision_id": decision.id},
                )
            if (
                self._require_checksum
                and evidence.kind is EvidenceKind.FILE
                and evidence.checksum is None
            ):
                return GateResult(
                    gate=self.name,
                    status=GateStatus.BLOCK,
                    reason=f"file evidence {evidence.locator} lacks a required checksum",
                    details={"decision_id": decision.id},
                )
            if self._resolver is not None:
                failure = self._resolver.resolve(evidence)
                if failure is not None:
                    return GateResult(
                        gate=self.name,
                        status=GateStatus.BLOCK,
                        reason=failure,
                        details={"decision_id": decision.id, "locator": evidence.locator},
                    )

        return GateResult(
            gate=self.name,
            status=GateStatus.PASS,
            reason=f"decision grounded in {count} evidence item(s)",
            details={"decision_id": decision.id, "evidence_count": count},
        )
