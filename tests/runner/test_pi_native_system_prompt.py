"""Pi-native startup identity prompt (``--append-system-prompt``).

A composed bundle agent (e.g. agile_pm) running on pi-native must boot with
its authored instructions — otherwise Pi answers with its default model
identity and even denies being the agent. These tests pin the arg vector,
the support probe, and the capability declaration.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def _args(**kwargs):
    from omnigent.runner.native.orchestration import _build_pi_native_args

    base = {
        "terminal_launch_args": None,
        "extension_path": Path("/tmp/ext.js"),
        "session_dir": Path("/tmp/sess"),
        "external_session_id": None,
    }
    base.update(kwargs)
    return _build_pi_native_args(**base)


def test_no_prompt_by_default() -> None:
    """Without instructions the argv is unchanged (no empty flag)."""
    args = _args()
    assert "--append-system-prompt" not in args
    assert _args(append_system_prompt="") == args
    assert _args(append_system_prompt=None) == args


def test_prompt_appended_as_flag_pair() -> None:
    """Instructions ride one ``--append-system-prompt <text>`` pair."""
    args = _args(append_system_prompt="You are agile_pm.")
    idx = args.index("--append-system-prompt")
    assert args[idx + 1] == "You are agile_pm."


def test_user_passed_flag_coexists() -> None:
    """Pi accepts the flag multiple times — a user occurrence never conflicts."""
    args = _args(
        terminal_launch_args=["--append-system-prompt", "user-text"],
        append_system_prompt="agent-text",
    )
    assert args.count("--append-system-prompt") == 2
    assert "user-text" in args and "agent-text" in args


def test_probe_detects_flag_from_help() -> None:
    """Support is probed from ``pi --help``, not a version floor."""
    import subprocess

    from omnigent import pi_native

    fake = subprocess.CompletedProcess(
        args=["pi", "--help"], returncode=0, stdout="--append-system-prompt <text>", stderr=""
    )
    with patch.object(subprocess, "run", return_value=fake) as run:
        assert pi_native.pi_supports_append_system_prompt("pi") is True
        run.assert_called_once()
        assert run.call_args.args[0] == ["pi", "--help"]


def test_probe_fails_open() -> None:
    """Any probe error means 'no flag' — an old Pi must still launch."""
    import subprocess

    from omnigent import pi_native

    with patch.object(subprocess, "run", side_effect=OSError("no pi")):
        assert pi_native.pi_supports_append_system_prompt("pi") is False
    fake = subprocess.CompletedProcess(args=["pi", "--help"], returncode=0, stdout="", stderr="")
    with patch.object(subprocess, "run", return_value=fake):
        assert pi_native.pi_supports_append_system_prompt("pi") is False


def test_pi_native_declares_startup_additive_delivery() -> None:
    """Capability must match the launch path (was NOT_DELIVERED)."""
    from omnigent.harness_capabilities import InstructionDelivery
    from omnigent.harness_plugins import harness_capabilities

    assert (
        harness_capabilities()["pi-native"].instruction_delivery
        is InstructionDelivery.AGENT_STARTUP_ADDITIVE
    )
