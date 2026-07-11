from __future__ import annotations

import pytest

from agent_session_gates.models import Decision, Evidence, EvidenceKind, JobSpec


def test_evidence_kind_members() -> None:
    assert {k.name for k in EvidenceKind} == {"FILE", "URL", "COMMAND", "ID"}


def test_evidence_from_dict_minimal() -> None:
    e = Evidence.from_dict({"kind": "url", "locator": "https://example.test/x"})
    assert e.kind is EvidenceKind.URL
    assert e.locator == "https://example.test/x"
    assert e.checksum is None


def test_evidence_from_dict_with_checksum() -> None:
    e = Evidence.from_dict(
        {"kind": "file", "locator": "a.txt", "checksum": "deadbeef"}
    )
    assert e.kind is EvidenceKind.FILE
    assert e.checksum == "deadbeef"


def test_evidence_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        Evidence.from_dict({"kind": "telepathy", "locator": "x"})


def test_evidence_rejects_missing_locator() -> None:
    with pytest.raises(ValueError):
        Evidence.from_dict({"kind": "url"})


def test_decision_from_dict_parses_evidence_list() -> None:
    d = Decision.from_dict(
        {
            "id": "D-1",
            "statement": "ship it",
            "evidence": [
                {"kind": "id", "locator": "TICKET-9"},
                {"kind": "file", "locator": "report.md", "checksum": "abc"},
            ],
        }
    )
    assert d.id == "D-1"
    assert d.statement == "ship it"
    assert len(d.evidence) == 2
    assert d.evidence[0].kind is EvidenceKind.ID


def test_decision_evidence_defaults_empty() -> None:
    d = Decision.from_dict({"id": "D-2", "statement": "no evidence"})
    assert d.evidence == ()


def test_jobspec_absent_open_questions_is_none() -> None:
    # key entirely missing -> "absent" (distinct from an explicit empty list)
    s = JobSpec.from_dict({"id": "S-1"})
    assert s.open_questions is None


def test_jobspec_explicit_empty_list() -> None:
    s = JobSpec.from_dict({"id": "S-2", "open_questions": []})
    assert s.open_questions == ()


def test_jobspec_populated_list() -> None:
    s = JobSpec.from_dict(
        {"id": "S-3", "open_questions": ["which region?", "budget?"]}
    )
    assert s.open_questions == ("which region?", "budget?")


def test_decision_evidence_must_be_list() -> None:
    import pytest

    with pytest.raises(ValueError):
        Decision.from_dict({"id": "D", "statement": "s", "evidence": "not-a-list"})


def test_jobspec_open_questions_must_be_list_when_present() -> None:
    import pytest

    with pytest.raises(ValueError):
        JobSpec.from_dict({"id": "S", "open_questions": "nope"})


def test_evidence_missing_kind_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        Evidence.from_dict({"locator": "x"})
