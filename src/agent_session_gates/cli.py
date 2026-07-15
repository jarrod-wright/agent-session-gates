"""Command-line entry point.

Usage:
    agent-session-gates check MANIFEST.json [--verify-files] [--continue-on-fail]

Reads a session manifest describing a ``decision`` and a ``spec``, runs the
standard gate suite (grounding + dispatch-lock), prints a JSON report to
stdout, and exits with the runner's aggregate code (0 pass / 1 block / 2 error).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .dispatch import DispatchLock
from .grounding import FileEvidenceResolver, GroundingGate
from .models import Decision, JobSpec
from .result import GateResult, GateStatus
from .runner import GateRunner, RunReport


def _error_report(reason: str) -> RunReport:
    return RunReport(
        results=(
            GateResult(gate="cli", status=GateStatus.ERROR, reason=reason),
        )
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-session-gates")
    sub = parser.add_subparsers(dest="command")
    check = sub.add_parser("check", help="run the gate suite over a manifest")
    check.add_argument("manifest", help="path to a JSON session manifest")
    check.add_argument(
        "--verify-files",
        action="store_true",
        help="resolve file evidence against the filesystem (existence + checksum)",
    )
    check.add_argument(
        "--continue-on-fail",
        action="store_true",
        help="run every gate instead of stopping at the first non-pass",
    )
    check.set_defaults(func=_cmd_check)
    return parser


def _cmd_check(args: argparse.Namespace) -> RunReport:
    try:
        with open(args.manifest, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except FileNotFoundError:
        return _error_report(f"manifest not found: {args.manifest}")
    except json.JSONDecodeError as exc:
        return _error_report(f"manifest is not valid JSON: {exc}")

    try:
        decision = Decision.from_dict(manifest.get("decision", {}))
        spec = JobSpec.from_dict(manifest.get("spec", {}))
    except ValueError as exc:
        return _error_report(f"invalid manifest: {exc}")

    resolver = FileEvidenceResolver() if args.verify_files else None
    grounding = GroundingGate(resolver=resolver)
    dispatch = DispatchLock()

    runner = GateRunner(
        [lambda: grounding.check(decision), lambda: dispatch.check(spec)],
        fail_fast=not args.continue_on_fail,
    )
    return runner.run()


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "func", None) is None:
        parser.print_usage(sys.stderr)
        return 2
    report: RunReport = args.func(args)
    print(json.dumps(report.to_dict(), indent=2))
    return report.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
