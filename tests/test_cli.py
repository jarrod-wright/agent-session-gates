from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from agent_session_gates.cli import main


def _write(path: Path, obj: object) -> str:
    path.write_text(json.dumps(obj))
    return str(path)


def test_clean_manifest_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = _write(
        tmp_path / "m.json",
        {
            "decision": {
                "id": "D",
                "statement": "ship",
                "evidence": [{"kind": "url", "locator": "https://example.test/r"}],
            },
            "spec": {"id": "S", "open_questions": []},
        },
    )
    code = main(["check", manifest])
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["overall"] == "PASS"


def test_ungrounded_decision_blocks(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = _write(
        tmp_path / "m.json",
        {
            "decision": {"id": "D", "statement": "ship", "evidence": []},
            "spec": {"id": "S", "open_questions": []},
        },
    )
    code = main(["check", manifest])
    assert code == 1
    assert json.loads(capsys.readouterr().out)["overall"] == "BLOCK"


def test_underspecified_spec_blocks(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = _write(
        tmp_path / "m.json",
        {
            "decision": {
                "id": "D",
                "statement": "ship",
                "evidence": [{"kind": "id", "locator": "TICKET-1"}],
            },
            "spec": {"id": "S", "open_questions": ["which db?"]},
        },
    )
    code = main(["check", manifest])
    assert code == 1


def test_verify_flag_resolves_file_checksums(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("grounded")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = _write(
        tmp_path / "m.json",
        {
            "decision": {
                "id": "D",
                "statement": "ship",
                "evidence": [
                    {"kind": "file", "locator": str(artifact), "checksum": digest}
                ],
            },
            "spec": {"id": "S", "open_questions": []},
        },
    )
    assert main(["check", "--verify-files", manifest]) == 0


def test_verify_flag_blocks_on_tampered_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("grounded")
    manifest = _write(
        tmp_path / "m.json",
        {
            "decision": {
                "id": "D",
                "statement": "ship",
                "evidence": [
                    {"kind": "file", "locator": str(artifact), "checksum": "0" * 64}
                ],
            },
            "spec": {"id": "S", "open_questions": []},
        },
    )
    assert main(["check", "--verify-files", manifest]) == 1


def test_missing_manifest_file_errors(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["check", "/no/such/manifest.json"])
    assert code == 2
    assert json.loads(capsys.readouterr().out)["overall"] == "ERROR"


def test_malformed_json_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json ")
    code = main(["check", str(bad)])
    assert code == 2
    assert json.loads(capsys.readouterr().out)["overall"] == "ERROR"


def test_no_command_returns_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2


def test_invalid_manifest_evidence_type_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "m.json"
    bad.write_text(json.dumps({"decision": {"id": "D", "evidence": "oops"}, "spec": {}}))
    code = main(["check", str(bad)])
    assert code == 2
    assert json.loads(capsys.readouterr().out)["overall"] == "ERROR"


def test_continue_on_fail_runs_all_gates(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = _write(
        tmp_path / "m.json",
        {
            "decision": {"id": "D", "statement": "s", "evidence": []},
            "spec": {"id": "S", "open_questions": ["q?"]},
        },
    )
    code = main(["check", "--continue-on-fail", manifest])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert len(out["results"]) == 2  # both gates ran, not just the first
