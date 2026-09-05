"""Structural test for the Agile PM orchestrator bundle (examples/agile_pm).

Agile PM manages agile development sprints across specialized sub-agents:
- ``ba`` (Business Analyst - claude-native/opus-5): story & Gherkin AC generation, UAT sign-off
- ``architect`` (System Architect - claude-native/opus-5): technical design, API/DB schemas, dev task breakdown
- ``dev`` (Developer - antigravity-native/gemini-3.8-flash): code & unit tests in worktree, PR creation
- ``sit`` (SIT / Peer Reviewer - codex-native/gpt-5.6-luna): cross-vendor review & integration tests, defect reporting

Pure spec-load — no LLM, no credentials — modeled on ``test_example_polly.py``
and ``test_example_debby.py``.

What breaks if this fails:
- the orchestrator executor/harness drifts (model / harness / context window),
- an agile sub-agent is dropped or harness changes,
- a spine skill is dropped or renamed (sprint-planning, sprint-execution, uat-signoff),
- guardrails are dropped (blast_radius, spawn_bounds, headless_subagent_purpose_guard),
- key orchestration contracts regress (zero code writing, PO approval gate, defect loop, co-signed commits).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from omnigent.spec import load
from omnigent.spec.types import AgentSpec

# tests/e2e/omnigent/test_example_agile_pm.py -> repo root is 3 parents up.
_AGILE_PM_BUNDLE = Path(__file__).resolve().parents[3] / "examples" / "agile_pm"


@pytest.fixture(scope="module")
def agile_pm_spec() -> AgentSpec:
    """Load and validate the agile_pm bundle once for the module."""
    return load(_AGILE_PM_BUNDLE)


def test_orchestrator_executor(agile_pm_spec: AgentSpec) -> None:
    """The orchestrator runs on pi-native with a pinned model/effort and 1M window."""
    assert agile_pm_spec.name == "agile_pm"
    ex = agile_pm_spec.executor
    assert ex.config.get("harness") == "pi-native"
    assert ex.config.get("smart_routing_harness") == "auto"
    assert ex.model == "muse-spark-1.3-contributor-free"
    assert ex.reasoning_effort == "xhigh"
    assert ex.profile is None
    assert ex.context_window == 1000000


def test_agile_subagents(agile_pm_spec: AgentSpec) -> None:
    """The bundle has four specialized sub-agents with expected harnesses and configurations."""
    fam = {a.name: a.executor.config.get("harness") for a in agile_pm_spec.sub_agents}
    assert sorted(agile_pm_spec.tools.agents) == ["architect", "ba", "dev", "sit"]
    assert fam["ba"] == "claude-native"
    assert fam["architect"] == "claude-native"
    assert fam["dev"] == "antigravity-native"
    assert fam["sit"] == "codex-native"

    by_name = {a.name: a for a in agile_pm_spec.sub_agents}

    # Sub-agents pin model + effort; no auth profiles
    assert by_name["ba"].executor.model == "opus-5"
    assert by_name["ba"].executor.reasoning_effort == "xhigh"
    assert by_name["architect"].executor.model == "opus-5"
    assert by_name["architect"].executor.reasoning_effort == "xhigh"
    assert by_name["dev"].executor.model == "gemini-3.8-flash"
    assert by_name["dev"].executor.reasoning_effort == "high"
    assert by_name["sit"].executor.model == "gpt-5.6-luna"
    assert by_name["sit"].executor.reasoning_effort == "max"
    for name in ("ba", "architect", "dev", "sit"):
        assert by_name[name].executor.profile is None, name

    # Headless / native permissions
    assert by_name["ba"].executor.config.get("permission_mode") == "auto"
    assert by_name["architect"].executor.config.get("permission_mode") == "auto"
    assert by_name["dev"].executor.config.get("permission_mode") == "bypassPermissions"
    assert by_name["sit"].executor.config.get("yolo") in (True, "True", "true")

    # Prompt role validation
    ba_prompt = (_AGILE_PM_BUNDLE / "agents" / "ba" / "config.yaml").read_text(encoding="utf-8")
    assert "STORY" in ba_prompt
    assert "UAT" in ba_prompt
    assert "Gherkin" in ba_prompt
    assert "Given" in ba_prompt and "When" in ba_prompt and "Then" in ba_prompt
    assert "ACCEPTED" in ba_prompt and "REJECTED" in ba_prompt

    arch_prompt = (_AGILE_PM_BUNDLE / "agents" / "architect" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "DESIGN" in arch_prompt
    assert "EXPLORE" in arch_prompt
    assert "Developer Task Packets" in arch_prompt or "task breakdown" in arch_prompt

    dev_prompt = (_AGILE_PM_BUNDLE / "agents" / "dev" / "config.yaml").read_text(encoding="utf-8")
    assert "IMPLEMENT" in dev_prompt
    assert ".worktrees/<task_id>" in dev_prompt
    assert "Co-authored-by: omnigent <noreply@omnigent.ai>" in dev_prompt
    assert "gh pr create" in dev_prompt

    sit_prompt = (_AGILE_PM_BUNDLE / "agents" / "sit" / "config.yaml").read_text(encoding="utf-8")
    assert "REVIEW" in sit_prompt
    assert "SIT" in sit_prompt
    assert "blocking" in sit_prompt and "non-blocking" in sit_prompt
    assert "test_failures" in sit_prompt


def test_spine_skills_present(agile_pm_spec: AgentSpec) -> None:
    """All sprint skills are discovered from skills/<dir>/SKILL.md."""
    assert sorted(s.name for s in agile_pm_spec.skills) == [
        "sprint-execution",
        "sprint-planning",
        "uat-signoff",
    ]


def test_guardrails_present(agile_pm_spec: AgentSpec) -> None:
    """The orchestrator and sub-agents carry required guardrail policies."""
    assert agile_pm_spec.guardrails is not None
    names = sorted(p.name for p in agile_pm_spec.guardrails.policies)
    assert names == [
        "blast_radius",
        "headless_subagent_purpose_guard",
        "spawn_bounds",
    ]

    spawn = next(p for p in agile_pm_spec.guardrails.policies if p.name == "spawn_bounds")
    assert spawn.function.arguments.get("max_dispatches_per_turn") == 6
    assert "sys_session_send" in spawn.function.arguments.get("dispatch_tools", [])
    assert "sys_session_create" in spawn.function.arguments.get("dispatch_tools", [])

    purpose_guard = next(
        p for p in agile_pm_spec.guardrails.policies if p.name == "headless_subagent_purpose_guard"
    )
    allowed = purpose_guard.function.arguments.get("allowed_purposes", [])
    for p in ["story", "design", "implement", "review", "sit", "uat", "explore", "search", "plan"]:
        assert p in allowed

    # Check all subagent guardrails
    for sub in agile_pm_spec.sub_agents:
        assert sub.guardrails is not None, sub.name
        sub_names = [p.name for p in sub.guardrails.policies]
        assert "blast_radius" in sub_names, sub.name

    # Non-empty arguments across all function policies
    specs = [agile_pm_spec, *agile_pm_spec.sub_agents]
    for spec in specs:
        if spec.guardrails is None:
            continue
        for policy in spec.guardrails.policies:
            func_ref = getattr(policy, "function", None)
            if func_ref is not None:
                assert func_ref.arguments, f"{spec.name}/{policy.name} has empty arguments"


def test_orchestrator_prompts_and_contracts(agile_pm_spec: AgentSpec) -> None:
    """The orchestrator prompt and skills enforce key sprint governance contracts."""
    config_text = (_AGILE_PM_BUNDLE / "config.yaml").read_text(encoding="utf-8")
    planning_text = (_AGILE_PM_BUNDLE / "skills" / "sprint-planning" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    execution_text = (_AGILE_PM_BUNDLE / "skills" / "sprint-execution" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    uat_text = (_AGILE_PM_BUNDLE / "skills" / "uat-signoff" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    config_compact = " ".join(config_text.split())

    # Zero code writing & zero direct test running
    assert "you do NOT write code" in config_compact
    assert "zero direct test running" in config_compact
    assert "ALL coding, design, and testing work gets delegated" in config_compact

    # Sprint state machine tracking
    assert ".agile-pm/sprint.json" in config_compact
    assert ".agile-pm/sprint.json" in planning_text
    assert ".agile-pm/sprint.json" in execution_text
    assert ".agile-pm/sprint.json" in uat_text

    # PO approval gate
    assert "PO Plan Approval" in config_compact
    assert "explicit approval before creating any git worktree" in config_compact
    assert "PO Plan Approval Gate" in planning_text
    assert "Wait for explicit PO approval before proceeding to Step 5" in planning_text

    # Defect loop
    assert "Defect Loop" in config_compact
    assert "Defect Loop" in execution_text
    assert "re-dispatch `sit`" in execution_text.lower() or "re-dispatch sit" in execution_text.lower()

    # Co-signed trailer
    assert "Co-authored-by: omnigent <noreply@omnigent.ai>" in config_compact
    assert "Co-authored-by: omnigent <noreply@omnigent.ai>" in execution_text

    # Roster preflight
    assert "command -v pi claude agy codex gh git || true" in config_compact

    # Turn discipline & inbox supervision
    assert "Act in the SAME turn you announce" in config_compact
    assert "NEVER end a turn after only saying what you are about to do" in config_compact
    assert "sys_read_inbox" in config_compact
    assert "sys_cancel_task" in config_compact


def test_agile_pm_has_os_env(agile_pm_spec: AgentSpec) -> None:
    """agile_pm has caller_process os_env with sandbox type none."""
    assert agile_pm_spec.os_env is not None
    assert agile_pm_spec.os_env.type == "caller_process"
    assert agile_pm_spec.os_env.sandbox is not None
    assert agile_pm_spec.os_env.sandbox.type == "none"


def test_agile_pm_terminals(agile_pm_spec: AgentSpec) -> None:
    """agile_pm specifies bash and zsh terminals."""
    assert agile_pm_spec.terminals is not None
    assert "shell" in agile_pm_spec.terminals
    assert agile_pm_spec.terminals["shell"].command == "bash"
    assert "zsh" in agile_pm_spec.terminals
    assert agile_pm_spec.terminals["zsh"].command == "zsh"
