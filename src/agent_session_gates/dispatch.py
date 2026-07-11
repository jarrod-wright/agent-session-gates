"""Dispatch lock.

Principle: a unit of work may not be dispatched while it is underspecified.
The lock is a hard fail with no advisory override. The spec's
``open_questions`` list must be *present and empty*:

* absent (``None``)  -> BLOCK (the author never asserted completeness)
* non-empty          -> BLOCK (residual open questions)
* contains a blank or ambiguous sentinel (TBD/TODO/FIXME/?/TBC)
  -> BLOCK (an "empty-looking" list that is not actually resolved)
* present and empty  -> PASS
"""

from __future__ import annotations

from .models import JobSpec
from .result import GateResult, GateStatus

_AMBIGUOUS = frozenset({"tbd", "tbc", "todo", "fixme", "?", "??", "xxx", "n/a"})


def _is_unresolved(entry: str) -> bool:
    token = entry.strip().lower()
    return token == "" or token in _AMBIGUOUS


class DispatchLock:
    """Blocks dispatch of an underspecified job spec."""

    name = "dispatch-lock"

    def check(self, spec: JobSpec) -> GateResult:
        if spec.open_questions is None:
            return GateResult(
                gate=self.name,
                status=GateStatus.BLOCK,
                reason="open_questions list is absent; completeness was never asserted",
                details={"spec_id": spec.id},
            )

        unresolved = [q for q in spec.open_questions if _is_unresolved(q)]
        open_count = len(spec.open_questions)

        if open_count > 0:
            return GateResult(
                gate=self.name,
                status=GateStatus.BLOCK,
                reason=f"{open_count} residual open question(s) block dispatch",
                details={
                    "spec_id": spec.id,
                    "open_count": open_count,
                    "ambiguous_or_blank": len(unresolved),
                },
            )

        return GateResult(
            gate=self.name,
            status=GateStatus.PASS,
            reason="no residual open questions; spec is dispatch-ready",
            details={"spec_id": spec.id, "open_count": 0},
        )
