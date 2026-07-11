"""Gate runner.

Composes an ordered sequence of zero-argument checks (callables returning a
:class:`GateResult`) into one deterministic pass, aggregates their outcomes,
and derives a process exit code:

    0 -> all gates PASS
    1 -> at least one BLOCK (and no ERROR)
    2 -> at least one ERROR (fail-closed; dominates BLOCK)

Any exception raised by a check is caught and recorded as an ERROR result so a
misbehaving gate can never be mistaken for a pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from .result import GateResult, GateStatus

Check = Callable[[], GateResult]

_EXIT_CODE = {GateStatus.PASS: 0, GateStatus.BLOCK: 1, GateStatus.ERROR: 2}


@dataclass(frozen=True)
class RunReport:
    """Aggregate outcome of a runner pass."""

    results: tuple[GateResult, ...]

    @property
    def overall(self) -> GateStatus:
        if any(r.status is GateStatus.ERROR for r in self.results):
            return GateStatus.ERROR
        if any(r.status is GateStatus.BLOCK for r in self.results):
            return GateStatus.BLOCK
        return GateStatus.PASS

    @property
    def exit_code(self) -> int:
        return _EXIT_CODE[self.overall]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall.value,
            "exit_code": self.exit_code,
            "results": [r.to_dict() for r in self.results],
        }


class GateRunner:
    """Runs a sequence of checks and reports the aggregate result."""

    def __init__(self, checks: Sequence[Check], fail_fast: bool = True) -> None:
        self._checks = list(checks)
        self._fail_fast = fail_fast

    def run(self) -> RunReport:
        results: list[GateResult] = []
        for index, check in enumerate(self._checks):
            results.append(self._run_one(check, index))
            if self._fail_fast and results[-1].status is not GateStatus.PASS:
                break
        return RunReport(results=tuple(results))

    @staticmethod
    def _run_one(check: Check, index: int) -> GateResult:
        try:
            return check()
        except Exception as exc:  # fail-closed: a broken gate never passes
            return GateResult(
                gate=getattr(check, "__name__", f"check[{index}]"),
                status=GateStatus.ERROR,
                reason=f"gate raised {type(exc).__name__}: {exc}",
            )
