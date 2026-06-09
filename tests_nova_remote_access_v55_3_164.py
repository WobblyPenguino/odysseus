from __future__ import annotations

from pathlib import Path

import pytest

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.remote_access import (
    build_remote_access_plan,
    build_remote_access_preflight,
    build_remote_access_status,
    build_wol_magic_packet,
    normalize_mac,
    parse_remote_wake_args,
    render_remote_access_preflight,
    send_wake_on_lan,
    write_remote_access_assets,
)
from winlocalassistant.nova_api import build_api_bridge_status, classify_api_command, create_fastapi_app, fastapi_available


def test_wol_mac_normalisation_and_magic_packet() -> None:
    assert normalize_mac("aa-bb-cc-dd-ee-ff") == "AA:BB:CC:DD:EE:FF"
    packet = build_wol_magic_packet("AA:BB:CC:DD:EE:FF")
    assert len(packet) == 102
    assert packet.startswith(b"\xff" * 6)
    assert packet[6:12] == bytes.fromhex("AABBCCDDEEFF")
    with pytest.raises(ValueError):
        normalize_mac("not-a-mac")


def test_remote_wake_parser_and_dry_run_result() -> None:
    args = parse_remote_wake_args("AA:BB:CC:DD:EE:FF 192.168.1.255 9 --dry-run")
    assert args["mac"] == "AA:BB:CC:DD:EE:FF"
    assert args["broadcast"] == "192.168.1.255"
    assert args["port"] == 9
    assert args["dry_run"] is True
    result = send_wake_on_lan(args["mac"], broadcast=args["broadcast"], port=args["port"], dry_run=True)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["packet_bytes"] == 102


def test_remote_access_plan_and_assets_are_safety_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "app.py").write_text("print('nova')\n", encoding="utf-8")

    plan = build_remote_access_plan(tmp_path)
    assert plan["architecture"].startswith("phone/laptop")
    assert any("Do not expose RDP" in step for phase in plan["phases"] for step in phase["steps"])

    assets = write_remote_access_assets(tmp_path)
    written = assets["written"]
    for path in written.values():
        assert Path(path).exists()
    guide = Path(written["setup_guide"]).read_text(encoding="utf-8")
    ps1 = Path(written["remote_api_ps1"]).read_text(encoding="utf-8")
    assert "Do **not** expose Windows Remote Desktop" in guide
    assert "NOVA_API_TOKEN" in guide
    assert "Refusing to expose Nova API beyond localhost" in ps1

    status = build_remote_access_status(tmp_path)
    assert status["default_api"]["host"] == "127.0.0.1"
    assert any("Do not port-forward" in item for item in status["security_warnings"])


def test_core_routes_remote_access_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "app.py").write_text("print('nova')\n", encoding="utf-8")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))

    plan = core.handle_command("/remote-access-plan")
    assert "Nova Remote PC Access Plan" in plan
    assert "Tailscale" in plan

    status = core.handle_command("/remote-access-status")
    assert "Nova Remote Access Status" in status
    assert "Do not port-forward" in status

    blocked = core.handle_command("/remote-wake AA:BB:CC:DD:EE:FF")
    assert "dry-run by default" in blocked

    dry = core.handle_command("/remote-wake AA:BB:CC:DD:EE:FF --dry-run")
    assert "Nova Remote Wake Result" in dry
    assert "Dry run: **True**" in dry

    scripts = core.handle_command("/remote-access-scripts")
    assert "Nova Remote Access Assets" in scripts
    assert (tmp_path / "start_nova_remote_api.ps1").exists()
    assert (tmp_path / "docs" / "NOVA_REMOTE_ACCESS_SETUP.md").exists()



def test_remote_access_preflight_reports_readiness_without_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "app.py").write_text("print('nova')\n", encoding="utf-8")

    before = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")}
    payload = build_remote_access_preflight(tmp_path)
    rendered = render_remote_access_preflight(payload)
    after = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")}

    assert payload["ok"] is True
    assert payload["counts"]["fail"] == 0
    assert any(check["name"] == "remote_assets" and check["status"] == "warn" for check in payload["checks"])
    assert "run /remote-access-scripts" in "\n".join(payload["next_steps"]).lower()
    assert "Nova Remote Access Preflight" in rendered
    assert before == after


def test_core_routes_remote_access_preflight_and_api_treats_as_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "app.py").write_text("print('nova')\n", encoding="utf-8")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))

    output = core.handle_command("/remote-access-test")
    assert "Nova Remote Access Preflight" in output
    assert "wake_on_lan_hardware" in output
    assert not (tmp_path / "start_nova_remote_api.ps1").exists()

    classification = classify_api_command("/remote-access-test")
    assert classification["mutating"] is False
    assert classification["risk"] == "low"

def test_api_status_mentions_optional_token_policy() -> None:
    payload = build_api_bridge_status(Path.cwd())
    assert "auth_token_required" in payload
    assert "NOVA_API_TOKEN" in payload["mutation_policy"]


def test_remote_setup_script_command_is_api_mutation_guarded() -> None:
    scripts = classify_api_command("/remote-access-scripts")
    alias = classify_api_command("/remote-scripts")
    status = classify_api_command("/remote-access-status")

    assert scripts["mutating"] is True
    assert scripts["risk"] == "medium"
    assert "writes Nova setup files" in scripts["reason"]
    assert alias["mutating"] is True
    assert status["mutating"] is False
    assert status["risk"] == "low"


@pytest.mark.skipif(not fastapi_available(), reason="FastAPI optional dependency is not installed")
def test_fastapi_remote_token_guard_when_configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.setenv("NOVA_API_TOKEN", "test-token-1234567890")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    app = create_fastapi_app(core)
    client = TestClient(app)

    health = client.get("/api/v1/health")
    assert health.status_code == 200

    blocked = client.get("/api/v1/status")
    assert blocked.status_code == 401

    allowed = client.get("/api/v1/status", headers={"Authorization": "Bearer test-token-1234567890"})
    assert allowed.status_code == 200
    assert allowed.json()["auth_token_required"] is True

    command = client.post(
        "/api/v1/command",
        headers={"X-Nova-Token": "test-token-1234567890"},
        json={"command": "/version"},
    )
    assert command.status_code == 200
    assert "Nova" in command.json()["output"]


@pytest.mark.skipif(not fastapi_available(), reason="FastAPI optional dependency is not installed")
def test_fastapi_blocks_remote_script_generation_without_mutation_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.delenv("NOVA_API_TOKEN", raising=False)
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    app = create_fastapi_app(core)
    client = TestClient(app)

    blocked = client.post("/api/v1/command", json={"command": "/remote-access-scripts"})
    assert blocked.status_code == 403
    assert not (tmp_path / "start_nova_remote_api.ps1").exists()

    allowed = client.post("/api/v1/command", json={"command": "/remote-access-scripts", "allow_mutation": True})
    assert allowed.status_code == 200
    assert "Nova Remote Access Assets" in allowed.json()["output"]
    assert (tmp_path / "start_nova_remote_api.ps1").exists()


def test_remote_api_health_parser_private_guard_and_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.remote_access import parse_remote_api_health_args, probe_remote_api_health, render_remote_api_health

    args = parse_remote_api_health_args("http://127.0.0.1:8767 --dry-run --token secret-token")
    assert args["host"] == "127.0.0.1"
    assert args["port"] == 8767
    assert args["token"] == "secret-token"
    assert args["dry_run"] is True

    calls: list[str] = []

    def fake_probe(url: str, **kwargs: object) -> dict[str, object]:
        calls.append(url)
        return {"ok": True, "status": 200, "body_preview": "{}"}

    monkeypatch.setattr("winlocalassistant.remote_access._http_probe", fake_probe)
    dry = probe_remote_api_health(**args)
    assert dry["ok"] is True
    assert dry["dry_run"] is True
    assert calls == []
    assert "Dry run only" in render_remote_api_health(dry)

    blocked = probe_remote_api_health("8.8.8.8", dry_run=True)
    assert blocked["ok"] is False
    assert "public host" in blocked["message"]


def test_remote_api_health_probe_reports_auth_and_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.remote_access import probe_remote_api_health, render_remote_api_health

    seen: list[tuple[str, str]] = []

    def fake_probe(url: str, **kwargs: object) -> dict[str, object]:
        seen.append((url, str(kwargs.get("token") or "")))
        if url.endswith("/api/v1/health"):
            return {"ok": True, "status": 200, "body_preview": '{"ok":true}'}
        return {"ok": False, "status": 401, "body_preview": "token required"}

    monkeypatch.setattr("winlocalassistant.remote_access._http_probe", fake_probe)
    payload = probe_remote_api_health("127.0.0.1", port=8767, token="", timeout=1)
    output = render_remote_api_health(payload)

    assert payload["ok"] is True
    assert payload["health"]["status"] == 200
    assert payload["status"]["status"] == 401
    assert "requires NOVA_API_TOKEN" in payload["message"]
    assert "Token supplied: **False**" in output
    assert seen[0][0].endswith("/api/v1/health")
    assert seen[1][0].endswith("/api/v1/status")


def test_core_routes_remote_api_health_and_api_classifies_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.nova_api import classify_api_command

    (tmp_path / "app.py").write_text("print('nova')\n", encoding="utf-8")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))

    def fake_probe(**kwargs: object) -> dict[str, object]:
        return {
            "ok": True,
            "dry_run": False,
            "base_url": "http://127.0.0.1:8767",
            "health_url": "http://127.0.0.1:8767/api/v1/health",
            "status_url": "http://127.0.0.1:8767/api/v1/status",
            "host_check": {"ok": True, "resolved_ip": "127.0.0.1", "category": "loopback", "safe_default": True},
            "token_supplied": False,
            "message": "Nova API health is reachable.",
            "health": {"ok": True, "status": 200},
            "status": {"ok": True, "status": 200},
        }

    monkeypatch.setattr("winlocalassistant.core.probe_remote_api_health", fake_probe)
    output = core.handle_command("/remote-api-health 127.0.0.1 8767")
    assert "Nova Remote API Health" in output
    assert "Overall OK: **True**" in output

    classification = classify_api_command("/remote-api-health 127.0.0.1 8767")
    assert classification["mutating"] is False
    assert classification["risk"] == "low"

    public_probe = classify_api_command("/remote-api-health 8.8.8.8 8767 --allow-public")
    assert public_probe["mutating"] is True
    assert public_probe["risk"] == "medium"
    assert "Public remote API probes" in public_probe["reason"]


def test_api_status_command_uses_configured_workspace_not_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = tmp_path / "workspace"
    other = tmp_path / "other"
    workspace.mkdir()
    other.mkdir()
    monkeypatch.chdir(other)

    core = AssistantCore(AssistantConfig(workspace=str(workspace)))
    output = core.handle_command("/nova-api-status")

    assert "Nova FastAPI Bridge Status" in output
    assert f"Workspace: `{workspace.resolve()}`" in output
    assert str(other.resolve()) not in output


def test_remote_profile_add_list_show_and_no_raw_token_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.remote_access import load_remote_profiles, remote_profile_action, render_remote_profiles

    monkeypatch.chdir(tmp_path)
    payload = remote_profile_action(
        tmp_path,
        "add newpc --host 127.0.0.1 --port 8767 --mac AA:BB:CC:DD:EE:FF --broadcast 192.168.1.255 --token-env NOVA_API_TOKEN --set-default",
    )
    assert payload["ok"] is True
    assert payload["changed"] is True
    assert payload["default"] == "newpc"
    assert (tmp_path / "config" / "remote_profiles.json").exists()

    saved_text = (tmp_path / "config" / "remote_profiles.json").read_text(encoding="utf-8")
    assert "NOVA_API_TOKEN" in saved_text
    assert "test-token" not in saved_text

    loaded = load_remote_profiles(tmp_path)
    assert loaded["profiles"]["newpc"]["mac"] == "AA:BB:CC:DD:EE:FF"
    listed = render_remote_profiles(remote_profile_action(tmp_path, "list"))
    shown = render_remote_profiles(remote_profile_action(tmp_path, "show newpc"))
    assert "newpc" in listed
    assert "Selected profile" in shown
    assert "Raw tokens are never stored" in shown


def test_remote_profile_blocks_public_hosts_and_requires_confirm_for_remove(tmp_path: Path) -> None:
    from winlocalassistant.remote_access import remote_profile_action

    blocked = remote_profile_action(tmp_path, "add public --host 8.8.8.8 --port 8767")
    assert blocked["ok"] is False
    assert "public remote host" in blocked["message"]

    added = remote_profile_action(tmp_path, "add newpc --host 127.0.0.1 --mac AA:BB:CC:DD:EE:FF")
    assert added["ok"] is True
    no_confirm = remote_profile_action(tmp_path, "remove newpc")
    assert no_confirm["ok"] is False
    assert "requires --confirm" in no_confirm["message"]
    removed = remote_profile_action(tmp_path, "remove newpc --confirm")
    assert removed["ok"] is True
    assert removed["changed"] is True
    assert "newpc" not in removed["profiles"]


def test_remote_profile_health_uses_env_token_without_storing_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.remote_access import remote_profile_action

    remote_profile_action(tmp_path, "add newpc --host 127.0.0.1 --port 8767 --token-env NOVA_API_TOKEN")
    monkeypatch.setenv("NOVA_API_TOKEN", "secret-token-value")
    seen: dict[str, object] = {}

    def fake_probe(host: str, **kwargs: object) -> dict[str, object]:
        seen["host"] = host
        seen.update(kwargs)
        return {
            "ok": True,
            "dry_run": bool(kwargs.get("dry_run")),
            "base_url": "http://127.0.0.1:8767",
            "host_check": {"ok": True, "resolved_ip": "127.0.0.1", "category": "loopback"},
            "token_supplied": bool(kwargs.get("token")),
            "message": "fake ok",
        }

    monkeypatch.setattr("winlocalassistant.remote_access.probe_remote_api_health", fake_probe)
    payload = remote_profile_action(tmp_path, "health newpc --dry-run")
    assert payload["ok"] is True
    assert payload["health"]["ok"] is True
    assert seen["host"] == "127.0.0.1"
    assert seen["token"] == "secret-token-value"
    assert "secret-token-value" not in (tmp_path / "config" / "remote_profiles.json").read_text(encoding="utf-8")


def test_remote_profile_wake_requires_mac_and_confirm_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.remote_access import remote_profile_action

    remote_profile_action(tmp_path, "add nomac --host 127.0.0.1")
    no_mac = remote_profile_action(tmp_path, "wake nomac --dry-run")
    assert no_mac["ok"] is False
    assert "has no MAC" in no_mac["message"]

    remote_profile_action(tmp_path, "add newpc --host 127.0.0.1 --mac AA:BB:CC:DD:EE:FF")
    guarded = remote_profile_action(tmp_path, "wake newpc")
    assert guarded["ok"] is False
    assert "dry-run by default" in guarded["message"]

    calls: list[dict[str, object]] = []

    def fake_wol(mac: str, **kwargs: object) -> dict[str, object]:
        calls.append({"mac": mac, **kwargs})
        return {"ok": True, "dry_run": kwargs.get("dry_run"), "mac": mac, "packet_bytes": 102}

    monkeypatch.setattr("winlocalassistant.remote_access.send_wake_on_lan", fake_wol)
    dry = remote_profile_action(tmp_path, "wake newpc --dry-run")
    confirmed = remote_profile_action(tmp_path, "wake newpc --confirm")
    assert dry["wake"]["dry_run"] is True
    assert confirmed["wake"]["dry_run"] is False
    assert calls[0]["mac"] == "AA:BB:CC:DD:EE:FF"


def test_core_routes_remote_profile_and_api_classification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("print('nova')\n", encoding="utf-8")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))

    added = core.handle_command("/remote-profile add newpc --host 127.0.0.1 --port 8767 --mac AA:BB:CC:DD:EE:FF --set-default")
    assert "Nova Remote Profiles" in added
    assert "Saved remote profile" in added

    listed = core.handle_command("/remote-profile list")
    assert "newpc" in listed
    assert "Raw tokens are never stored" in listed

    assert classify_api_command("/remote-profile list")["mutating"] is False
    assert classify_api_command("/remote-profile health newpc --dry-run")["mutating"] is False
    assert classify_api_command("/remote-profile add newpc --host 127.0.0.1")["mutating"] is True
    assert classify_api_command("/remote-profile remove newpc --confirm")["mutating"] is True
    assert classify_api_command("/remote-profile wake newpc --confirm")["mutating"] is True
    assert classify_api_command("/remote-profile health newpc --allow-public")["mutating"] is True


def test_remote_profile_loader_tolerates_corrupt_profile_fields(tmp_path: Path) -> None:
    from winlocalassistant.remote_access import DEFAULT_API_PORT, load_remote_profiles

    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "remote_profiles.json").write_text(
        '{"default":"bad","profiles":{"bad":{"name":"bad","host":"127.0.0.1","port":"not-int","mac":"bad-mac"}}}',
        encoding="utf-8",
    )
    data = load_remote_profiles(tmp_path)
    assert data["profiles"]["bad"]["port"] == DEFAULT_API_PORT
    assert data["profiles"]["bad"]["mac"] == ""
    assert data["default"] == "bad"


@pytest.mark.skipif(not fastapi_available(), reason="FastAPI optional dependency is not installed")
def test_fastapi_blocks_remote_profile_mutation_without_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.delenv("NOVA_API_TOKEN", raising=False)
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    client = TestClient(create_fastapi_app(core))

    blocked = client.post("/api/v1/command", json={"command": "/remote-profile add newpc --host 127.0.0.1"})
    assert blocked.status_code == 403
    assert not (tmp_path / "config" / "remote_profiles.json").exists()

    allowed = client.post(
        "/api/v1/command",
        json={"command": "/remote-profile add newpc --host 127.0.0.1 --port 8767", "allow_mutation": True},
    )
    assert allowed.status_code == 200
    assert "Saved remote profile" in allowed.json()["output"]
    assert (tmp_path / "config" / "remote_profiles.json").exists()

    readonly = client.post("/api/v1/command", json={"command": "/remote-profile list"})
    assert readonly.status_code == 200
    assert "newpc" in readonly.json()["output"]


def test_remote_profile_wizard_is_read_only_and_builds_safe_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.remote_access import build_remote_profile_wizard, render_remote_profile_wizard

    monkeypatch.chdir(tmp_path)
    before = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")}
    payload = build_remote_profile_wizard(
        tmp_path,
        "--host 127.0.0.1 --port 8767 --mac aa-bb-cc-dd-ee-ff --broadcast 192.168.1.255 --token-env NOVA_API_TOKEN --set-default",
    )
    rendered = render_remote_profile_wizard(payload)
    after = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")}

    assert payload["ok"] is True
    assert payload["mac_supplied"] is True
    assert "remote-profile add newpc" in payload["commands"]["add_profile"]
    assert "AA:BB:CC:DD:EE:FF" in payload["commands"]["add_profile"]
    assert "paste-a-long-random-token" in payload["commands"]["set_token_powershell"]
    assert "Safety: this wizard is read-only" in rendered
    assert before == after
    assert not (tmp_path / "config" / "remote_profiles.json").exists()


def test_core_routes_remote_profile_wizard_and_api_treats_as_read_only(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('nova')\n", encoding="utf-8")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))

    output = core.handle_command("/remote-profile-wizard --host 127.0.0.1 --mac AA:BB:CC:DD:EE:FF")
    assert "Nova Remote Profile Wizard" in output
    assert "remote-profile add newpc" in output
    assert not (tmp_path / "config" / "remote_profiles.json").exists()

    classification = classify_api_command("/remote-profile-wizard --host 127.0.0.1 --mac AA:BB:CC:DD:EE:FF")
    assert classification["mutating"] is False
    assert classification["risk"] == "low"


def test_remote_profile_validate_reports_token_and_mac_readiness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from winlocalassistant.remote_access import remote_profile_action, render_remote_profiles

    remote_profile_action(tmp_path, "add newpc --host 127.0.0.1 --port 8767 --mac AA:BB:CC:DD:EE:FF --token-env NOVA_API_TOKEN")
    monkeypatch.delenv("NOVA_API_TOKEN", raising=False)
    missing_token = remote_profile_action(tmp_path, "validate newpc")
    rendered_missing = render_remote_profiles(missing_token)

    assert missing_token["ok"] is True
    assert "Profile validation" in rendered_missing
    assert "is not configured" in rendered_missing

    monkeypatch.setenv("NOVA_API_TOKEN", "secret-token-value")
    ready = remote_profile_action(tmp_path, "validate newpc")
    rendered_ready = render_remote_profiles(ready)
    assert ready["ok"] is True
    assert "is configured" in rendered_ready
    assert "secret-token-value" not in rendered_ready


def test_remote_profile_validate_aliases_are_read_only_for_api() -> None:
    assert classify_api_command("/remote-profile validate newpc")["mutating"] is False
    assert classify_api_command("/remote-profile check newpc")["mutating"] is False
    assert classify_api_command("/remote-profile verify newpc")["mutating"] is False
