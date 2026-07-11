from __future__ import annotations

import pytest

from agent_session_gates.result import GateResult, GateStatus


def test_status_members() -> None:
    assert {s.name for s in GateStatus} == {"PASS", "BLOCK", "ERROR"}


def test_pass_result_is_ok() -> None:
    r = GateResult(gate="demo", status=GateStatus.PASS, reason="all good")
    assert r.ok is True


@pytest.mark.parametrize("status", [GateStatus.BLOCK, GateStatus.ERROR])
def test_non_pass_result_is_not_ok(status: GateStatus) -> None:
    r = GateResult(gate="demo", status=status, reason="nope")
    assert r.ok is False


def test_result_is_frozen() -> None:
    r = GateResult(gate="demo", status=GateStatus.PASS, reason="ok")
    with pytest.raises(Exception):
        r.reason = "mutated"  # type: ignore[misc]


def test_to_dict_is_json_serialisable() -> None:
    import json

    r = GateResult(
        gate="grounding",
        status=GateStatus.BLOCK,
        reason="ungrounded",
        details={"evidence_count": 0},
    )
    d = r.to_dict()
    assert d["gate"] == "grounding"
    assert d["status"] == "BLOCK"
    assert d["reason"] == "ungrounded"
    assert d["details"] == {"evidence_count": 0}
    assert json.loads(json.dumps(d)) == d


def test_details_defaults_to_empty_mapping() -> None:
    r = GateResult(gate="demo", status=GateStatus.PASS, reason="ok")
    assert r.details == {}
