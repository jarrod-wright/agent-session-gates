from __future__ import annotations

from agent_session_gates.dispatch import DispatchLock
from agent_session_gates.models import JobSpec
from agent_session_gates.result import GateStatus


def test_absent_list_blocks() -> None:
    result = DispatchLock().check(JobSpec(id="S", open_questions=None))
    assert result.status is GateStatus.BLOCK
    assert "absent" in result.reason.lower()


def test_empty_list_passes() -> None:
    result = DispatchLock().check(JobSpec(id="S", open_questions=()))
    assert result.status is GateStatus.PASS


def test_populated_list_blocks_with_count() -> None:
    result = DispatchLock().check(
        JobSpec(id="S", open_questions=("q1", "q2", "q3"))
    )
    assert result.status is GateStatus.BLOCK
    assert result.details["open_count"] == 3


def test_blank_entry_counts_as_unresolved() -> None:
    result = DispatchLock().check(JobSpec(id="S", open_questions=("  ",)))
    assert result.status is GateStatus.BLOCK


def test_ambiguous_sentinels_block() -> None:
    for token in ("TBD", "todo", "FIXME", "?", "tbc"):
        result = DispatchLock().check(JobSpec(id="S", open_questions=(token,)))
        assert result.status is GateStatus.BLOCK, token


def test_gate_name_is_stable() -> None:
    assert DispatchLock().name == "dispatch-lock"
