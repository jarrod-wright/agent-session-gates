from __future__ import annotations

from agent_session_gates.result import GateResult, GateStatus
from agent_session_gates.runner import GateRunner, RunReport


def _pass(name: str = "p") -> GateResult:
    return GateResult(gate=name, status=GateStatus.PASS, reason="ok")


def _block(name: str = "b") -> GateResult:
    return GateResult(gate=name, status=GateStatus.BLOCK, reason="blocked")


def _error(name: str = "e") -> GateResult:
    return GateResult(gate=name, status=GateStatus.ERROR, reason="boom")


def test_all_pass_exit_zero() -> None:
    report = GateRunner([lambda: _pass("a"), lambda: _pass("b")]).run()
    assert report.overall is GateStatus.PASS
    assert report.exit_code == 0
    assert len(report.results) == 2


def test_any_block_exit_one() -> None:
    report = GateRunner(
        [lambda: _pass("a"), lambda: _block("b")], fail_fast=False
    ).run()
    assert report.overall is GateStatus.BLOCK
    assert report.exit_code == 1


def test_error_dominates_block_exit_two() -> None:
    report = GateRunner(
        [lambda: _block("b"), lambda: _error("e")], fail_fast=False
    ).run()
    assert report.overall is GateStatus.ERROR
    assert report.exit_code == 2


def test_fail_fast_stops_after_first_non_pass() -> None:
    calls: list[str] = []

    def record(name: str, result: GateResult):
        def _c() -> GateResult:
            calls.append(name)
            return result

        return _c

    report = GateRunner(
        [record("a", _block("a")), record("b", _pass("b"))], fail_fast=True
    ).run()
    assert calls == ["a"]
    assert report.exit_code == 1


def test_fail_fast_false_runs_everything() -> None:
    calls: list[str] = []

    def record(name: str, result: GateResult):
        def _c() -> GateResult:
            calls.append(name)
            return result

        return _c

    GateRunner(
        [record("a", _block("a")), record("b", _pass("b"))], fail_fast=False
    ).run()
    assert calls == ["a", "b"]


def test_exception_in_check_becomes_error_result() -> None:
    def explode() -> GateResult:
        raise RuntimeError("unexpected")

    report = GateRunner([explode], fail_fast=False).run()
    assert report.overall is GateStatus.ERROR
    assert report.exit_code == 2
    assert report.results[0].status is GateStatus.ERROR


def test_report_to_dict_is_serialisable() -> None:
    import json

    report = GateRunner([lambda: _pass("a"), lambda: _block("b")], fail_fast=False).run()
    d = report.to_dict()
    assert d["overall"] == "BLOCK"
    assert d["exit_code"] == 1
    assert len(d["results"]) == 2
    assert json.loads(json.dumps(d)) == d


def test_empty_runner_passes() -> None:
    report = GateRunner([]).run()
    assert isinstance(report, RunReport)
    assert report.exit_code == 0
