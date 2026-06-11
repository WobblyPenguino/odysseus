from winlocalassistant.agent_browser_safety import (
    build_agent_browser_localhost_plan,
    default_agent_browser_safety_policy,
    is_agent_browser_url_allowed,
    normalise_agent_browser_host,
    safe_agent_browser_readonly_commands,
    unsafe_agent_browser_action_commands,
)


def test_agent_browser_policy_defaults_to_localhost_only() -> None:
    policy = default_agent_browser_safety_policy()

    assert policy.allowed_hosts == ("localhost", "127.0.0.1", "::1")
    assert policy.read_only_first is True
    assert policy.allow_existing_profile is False
    assert policy.allow_saved_state is False
    assert policy.allow_external_domains is False
    assert policy.require_manual_install is True


def test_agent_browser_url_policy_allows_localhost_only() -> None:
    assert is_agent_browser_url_allowed("http://localhost:8000")
    assert is_agent_browser_url_allowed("127.0.0.1:3000")
    assert not is_agent_browser_url_allowed("https://example.com")


def test_agent_browser_host_normalisation_handles_urlish_values() -> None:
    assert normalise_agent_browser_host("localhost:5173") == "localhost"
    assert normalise_agent_browser_host("http://127.0.0.1:8000/path") == "127.0.0.1"
    assert normalise_agent_browser_host("") == ""


def test_agent_browser_command_groups_separate_readonly_from_actions() -> None:
    readonly = safe_agent_browser_readonly_commands()
    actions = unsafe_agent_browser_action_commands()

    assert "snapshot" in readonly
    assert "screenshot" in readonly
    assert "click" in actions
    assert "fill" in actions
    assert not set(readonly).intersection(actions)


def test_agent_browser_localhost_plan_blocks_external_urls() -> None:
    plan = build_agent_browser_localhost_plan("https://example.com")

    assert plan["allowed"] is False
    assert plan["commands"] == []
    assert "localhost-only" in plan["blocked_reason"]


def test_agent_browser_localhost_plan_builds_readonly_evidence_commands() -> None:
    plan = build_agent_browser_localhost_plan("http://localhost:8000")

    assert plan["allowed"] is True
    assert ["agent-browser", "open", "http://localhost:8000"] in plan["commands"]
    assert ["agent-browser", "snapshot"] in plan["commands"]
    assert ["agent-browser", "screenshot", "--annotate"] in plan["commands"]
