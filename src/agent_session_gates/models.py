"""Input data models parsed from a session manifest.

These are deliberately small, frozen value objects. Parsing lives in
``from_dict`` classmethods so the CLI and library share one validation path
and malformed input fails loudly with :class:`ValueError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class EvidenceKind(Enum):
    """How a piece of grounding evidence can be located."""

    FILE = "file"
    URL = "url"
    COMMAND = "command"
    ID = "id"

    @classmethod
    def parse(cls, value: str) -> "EvidenceKind":
        try:
            return cls(value)
        except ValueError as exc:  # pragma: no cover - message re-raised below
            allowed = ", ".join(k.value for k in cls)
            raise ValueError(
                f"unknown evidence kind {value!r}; expected one of: {allowed}"
            ) from exc


@dataclass(frozen=True)
class Evidence:
    """A single grounding reference attached to a decision."""

    kind: EvidenceKind
    locator: str
    checksum: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Evidence":
        if "locator" not in data or not str(data.get("locator", "")).strip():
            raise ValueError("evidence requires a non-empty 'locator'")
        if "kind" not in data:
            raise ValueError("evidence requires a 'kind'")
        checksum = data.get("checksum")
        return cls(
            kind=EvidenceKind.parse(str(data["kind"])),
            locator=str(data["locator"]),
            checksum=str(checksum) if checksum is not None else None,
        )


@dataclass(frozen=True)
class Decision:
    """A claim/decision that must be grounded before it may be ratified."""

    id: str
    statement: str
    evidence: tuple[Evidence, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Decision":
        raw = data.get("evidence", [])
        if not isinstance(raw, list):
            raise ValueError("decision 'evidence' must be a list")
        return cls(
            id=str(data.get("id", "")),
            statement=str(data.get("statement", "")),
            evidence=tuple(Evidence.from_dict(e) for e in raw),
        )


@dataclass(frozen=True)
class JobSpec:
    """A unit of work that must be fully specified before dispatch.

    ``open_questions is None`` means the field was *absent* from the manifest
    -- treated as a harder failure than an explicit empty list, because it
    signals the author never asserted the spec was complete.
    """

    id: str
    open_questions: tuple[str, ...] | None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "JobSpec":
        if "open_questions" not in data:
            open_questions: tuple[str, ...] | None = None
        else:
            raw = data["open_questions"]
            if not isinstance(raw, list):
                raise ValueError("spec 'open_questions' must be a list when present")
            open_questions = tuple(str(q) for q in raw)
        return cls(id=str(data.get("id", "")), open_questions=open_questions)
