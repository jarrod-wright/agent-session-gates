"""Result primitives shared by every gate.

A gate never raises to signal a policy outcome; it returns a
:class:`GateResult`. Exceptions are reserved for genuinely unexpected
failures, which the runner converts into an ``ERROR`` result (fail-closed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class GateStatus(Enum):
    """Outcome of evaluating a single gate.

    ``PASS``  - the gate's condition is satisfied.
    ``BLOCK`` - the condition is violated (an expected, policy-level stop).
    ``ERROR`` - the gate could not be evaluated (fail-closed / treat as blocking).
    """

    PASS = "PASS"
    BLOCK = "BLOCK"
    ERROR = "ERROR"


_EMPTY: Mapping[str, Any] = MappingProxyType({})


@dataclass(frozen=True)
class GateResult:
    """An immutable record of one gate evaluation."""

    gate: str
    status: GateStatus
    reason: str
    details: Mapping[str, Any] = field(default_factory=lambda: _EMPTY)

    @property
    def ok(self) -> bool:
        """True only when the gate passed."""
        return self.status is GateStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        """A plain, JSON-serialisable representation."""
        return {
            "gate": self.gate,
            "status": self.status.value,
            "reason": self.reason,
            "details": dict(self.details),
        }
