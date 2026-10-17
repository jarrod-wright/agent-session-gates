# agent-session-gates

Deterministic pre-flight gates for agent and automation workflows.

[![ci](https://github.com/jarrod-wright/agent-session-gates/actions/workflows/ci.yml/badge.svg)](https://github.com/jarrod-wright/agent-session-gates/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Autonomous agents and CI pipelines make decisions and dispatch work. This
library gives that loop a small set of **deterministic gates** that run *before*
a decision is ratified or a job is dispatched — so a workflow fails closed,
loudly, and reproducibly instead of proceeding on an unstated assumption.

No dependencies. Python 3.12+ standard library only. Fully typed.

## The gates

| Gate | Question it answers | Blocks when |
|---|---|---|
| **GroundingGate** | Is this decision backed by evidence? | no evidence, a blank locator, or (with a resolver) a file that is missing or whose checksum doesn't match |
| **DispatchLock** | Is this unit of work fully specified? | the `open_questions` list is absent, non-empty, or contains an ambiguous placeholder (`TBD`, `TODO`, `?`, …) |
| **GateRunner** | Did every gate pass? | aggregates results into a single exit code (0 pass / 1 block / 2 error) |

Every gate returns a structured `GateResult` rather than raising — the outcome
is data you can log, serialise, and assert on. A gate that throws unexpectedly
is caught and recorded as `ERROR`, never silently skipped.

## Install

```bash
pip install "git+https://github.com/jarrod-wright/agent-session-gates"   # latest from GitHub
pip install -e ".[dev]"              # from a checkout, with test deps
```

## Quickstart (library)

```python
from agent_session_gates import (
    Decision, Evidence, EvidenceKind, JobSpec,
    GroundingGate, DispatchLock, GateRunner,
)

decision = Decision(
    id="ADR-017",
    statement="Adopt the queue-backed retry strategy.",
    evidence=(Evidence(EvidenceKind.ID, "TICKET-4821"),),
)
spec = JobSpec(id="JOB-retry", open_questions=())  # () == asserted complete

report = GateRunner([
    lambda: GroundingGate().check(decision),
    lambda: DispatchLock().check(spec),
]).run()

print(report.overall)     # GateStatus.PASS
raise SystemExit(report.exit_code)
```

## Quickstart (CLI)

Describe a session as JSON and let the standard suite gate it:

```bash
agent-session-gates check examples/session.json
agent-session-gates check --verify-files examples/session.json   # actually hash file evidence
```

The command prints a JSON report and exits `0` / `1` / `2`, so it drops
straight into a CI step or a pre-commit hook:

```yaml
- name: gate the session
  run: agent-session-gates check session.json
```

## Verified grounding

Structural grounding (evidence is present and well-formed) is the default.
Pass a resolver — or `--verify-files` on the CLI — to turn an *assertion* of
evidence into a *measurement*: file evidence is checked to exist, and any
supplied SHA-256 is recomputed and compared. A tampered or absent artefact
blocks.

```python
from agent_session_gates import GroundingGate, FileEvidenceResolver
GroundingGate(resolver=FileEvidenceResolver()).check(decision)
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | all gates passed |
| `1` | at least one gate blocked (policy violation) |
| `2` | at least one gate errored (fail-closed) |

## Design notes

- **Deterministic.** Same input, same result and exit code — no clocks, no network in the core.
- **Fail closed.** Absent evidence and absent specification are treated as failures, not neutral.
- **Composable.** `GateRunner` takes any `() -> GateResult` callable; write your own gates and drop them in.
- **Observable.** Results and reports serialise to plain dicts / JSON for logs and assertions.

## Development

```bash
pip install -e ".[dev]"
pytest -q --cov=agent_session_gates --cov-report=term-missing
```

## License

MIT — see [LICENSE](LICENSE).
