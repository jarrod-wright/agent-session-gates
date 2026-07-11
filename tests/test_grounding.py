from __future__ import annotations

import hashlib
from pathlib import Path

from agent_session_gates.grounding import FileEvidenceResolver, GroundingGate
from agent_session_gates.models import Decision, Evidence, EvidenceKind
from agent_session_gates.result import GateStatus


def _decision(evidence: list[Evidence]) -> Decision:
    return Decision(id="D", statement="s", evidence=tuple(evidence))


def test_no_evidence_blocks() -> None:
    result = GroundingGate().check(_decision([]))
    assert result.status is GateStatus.BLOCK
    assert result.details["evidence_count"] == 0


def test_structural_grounding_passes_without_resolver() -> None:
    ev = [Evidence(EvidenceKind.URL, "https://example.test/report")]
    result = GroundingGate().check(_decision(ev))
    assert result.status is GateStatus.PASS


def test_blank_locator_blocks() -> None:
    ev = [Evidence(EvidenceKind.ID, "   ")]
    result = GroundingGate().check(_decision(ev))
    assert result.status is GateStatus.BLOCK


def test_require_checksum_blocks_file_without_checksum() -> None:
    ev = [Evidence(EvidenceKind.FILE, "a.txt", checksum=None)]
    result = GroundingGate(require_checksum=True).check(_decision(ev))
    assert result.status is GateStatus.BLOCK


def test_file_resolver_passes_on_matching_checksum(tmp_path: Path) -> None:
    f = tmp_path / "artifact.txt"
    f.write_text("measured-content")
    digest = hashlib.sha256(f.read_bytes()).hexdigest()
    ev = [Evidence(EvidenceKind.FILE, str(f), checksum=digest)]
    gate = GroundingGate(resolver=FileEvidenceResolver())
    assert gate.check(_decision(ev)).status is GateStatus.PASS


def test_file_resolver_blocks_on_missing_file(tmp_path: Path) -> None:
    ev = [Evidence(EvidenceKind.FILE, str(tmp_path / "nope.txt"))]
    gate = GroundingGate(resolver=FileEvidenceResolver())
    assert gate.check(_decision(ev)).status is GateStatus.BLOCK


def test_file_resolver_blocks_on_checksum_mismatch(tmp_path: Path) -> None:
    f = tmp_path / "artifact.txt"
    f.write_text("real-content")
    ev = [Evidence(EvidenceKind.FILE, str(f), checksum="0" * 64)]
    gate = GroundingGate(resolver=FileEvidenceResolver())
    result = gate.check(_decision(ev))
    assert result.status is GateStatus.BLOCK
    assert "mismatch" in result.reason.lower()


def test_resolver_ignores_non_file_evidence(tmp_path: Path) -> None:
    ev = [Evidence(EvidenceKind.URL, "https://example.test/x")]
    gate = GroundingGate(resolver=FileEvidenceResolver())
    assert gate.check(_decision(ev)).status is GateStatus.PASS


def test_gate_name_is_stable() -> None:
    assert GroundingGate().name == "grounding"
