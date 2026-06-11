from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.model_context import CONTEXT_HEADER, build_model_context_pack, enrich_messages_with_context
from winlocalassistant.model_router import model_chat, ollama_chat
from winlocalassistant.tools import ToolRegistry


def test_context_pack_includes_workspace_project_brief_and_prompt_file() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_pack_") as tmp:
        root = Path(tmp)
        (root / "PROJECT_BUILD_BRIEF.md").write_text("# Brief\nBuild a study planner with local saving.", encoding="utf-8")
        (root / "app.js").write_text("function save(){ localStorage.setItem('x','y') }", encoding="utf-8")
        cfg = AssistantConfig(workspace=tmp)
        pack = build_model_context_pack(cfg, [{"role": "user", "content": "review app.js for local saving bugs"}], desc="quality review")
        assert CONTEXT_HEADER in pack.text
        assert "PROJECT_BUILD_BRIEF.md" in pack.text
        assert "app.js" in pack.text
        assert "localStorage" in pack.text
        assert "code_debug" in pack.metadata["tags"]


def test_model_router_enriches_messages_once() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_enrich_") as tmp:
        cfg = AssistantConfig(workspace=tmp)
        messages = [{"role": "user", "content": "build a calculator app"}]
        enriched = enrich_messages_with_context(cfg, messages, desc="local LLM prompt")
        assert enriched[0]["role"] == "system"
        assert CONTEXT_HEADER in enriched[0]["content"]
        assert enriched[-1]["content"] == "build a calculator app"
        enriched_again = enrich_messages_with_context(cfg, enriched, desc="local LLM prompt")
        assert len(enriched_again) == len(enriched)


def test_model_context_command_preview_and_toggle() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_cmd_") as tmp:
        bot = AssistantCore(AssistantConfig(workspace=tmp))
        preview = bot.handle_command("/model-context build a snake game")
        assert "Local Model Context Pack Preview" in preview
        assert "Nova" in preview
        off = bot.handle_command("/model-context off")
        assert "disabled" in off.lower()
        assert bot.config.local_model_context_enabled is False
        on = bot.handle_command("/model-context on")
        assert "enabled" in on.lower()
        limit = bot.handle_command("/model-context max=5000")
        assert "5000" in limit
        assert bot.config.local_model_context_max_chars == 5000


def test_model_context_pack_reuses_cached_pack_for_same_config() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_cache_") as tmp:
        cfg = AssistantConfig(workspace=tmp)
        messages = [{"role": "user", "content": "review app.js for local saving bugs"}]
        first = build_model_context_pack(cfg, messages, desc="cache test")
        second = build_model_context_pack(cfg, messages, desc="cache test")
        assert first.text == second.text
        assert first.metadata == second.metadata


def test_model_context_pack_includes_response_quality_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_quality_") as tmp:
        cfg = AssistantConfig(workspace=tmp)
        pack = build_model_context_pack(cfg, [{"role": "user", "content": "fix a failing pytest and explain the result"}], desc="code repair")
        assert "response_quality_contract" in pack.text
        assert "Do not claim success" in pack.text
        assert "verification command" in pack.text


def test_response_quality_plan_tool_and_command_write_reports() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_resp_quality_") as tmp:
        cfg = AssistantConfig(workspace=tmp)
        registry = ToolRegistry(cfg)
        result = registry.call("response_quality_plan", goal="improve AI communication for coding fixes")
        assert result.ok is True
        assert "Nova Response Quality Plan" in result.data.get("message", "")
        assert "structured" in result.data.get("message", "").lower()

        bot = AssistantCore(cfg)
        out = bot.handle_command("/response-quality-plan improve Nova replies --write")
        assert "Reports written" in out
        assert Path(tmp, "docs", "NOVA_RESPONSE_QUALITY_PLAN_LATEST.md").exists()
        assert Path(tmp, "docs", "NOVA_RESPONSE_QUALITY_PLAN_LATEST.json").exists()


def test_model_chat_defaults_to_config_model_when_no_model_passed() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_model_chat_") as tmp:
        cfg = AssistantConfig(workspace=tmp)
        called = {}
        def fake_ollama_chat(base_url, model, messages, timeout=None, desc="local model call", **kwargs):
            called["model"] = model
            return "ok"
        import winlocalassistant.model_router as router
        old_ollama_chat = router.ollama_chat
        router.ollama_chat = fake_ollama_chat
        try:
            result = model_chat(cfg, "", [{"role": "user", "content": "hello"}], timeout=1)
            assert result == "ok"
            assert called["model"] == cfg.model
        finally:
            router.ollama_chat = old_ollama_chat


def test_model_context_pack_includes_prompt_named_python_file_preview() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_py_") as tmp:
        root = Path(tmp)
        (root / "script.py").write_text("print('hello')", encoding='utf-8')
        cfg = AssistantConfig(workspace=tmp)
        pack = build_model_context_pack(cfg, [{"role": "user", "content": "review script.py"}], desc="quality review")
        assert "script.py" in pack.text
        assert "print('hello')" in pack.text


def test_model_context_pack_refreshes_prompt_named_file_preview_after_file_change() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_py_change_") as tmp:
        root = Path(tmp)
        file_path = root / "script.py"
        file_path.write_text("print('hello')", encoding='utf-8')
        cfg = AssistantConfig(workspace=tmp)
        pack1 = build_model_context_pack(cfg, [{"role": "user", "content": "review script.py"}], desc="quality review")
        assert "print('hello')" in pack1.text
        # Change file content
        file_path.write_text("print('world')", encoding='utf-8')
        pack2 = build_model_context_pack(cfg, [{"role": "user", "content": "review script.py"}], desc="quality review")
        assert "print('world')" in pack2.text
        # Ensure the old content is no longer present
        assert "print('hello')" not in pack2.text


def test_model_context_pack_rejects_prompt_named_file_outside_workspace() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_outside_") as tmp:
        root = Path(tmp)
        # Create a file inside the workspace
        (root / "inside.txt").write_text("inside", encoding='utf-8')
        # Create a file outside the workspace in its parent directory
        outside_path = Path(root.parent) / "outside.txt"
        outside_path.write_text("outside", encoding='utf-8')
        cfg = AssistantConfig(workspace=tmp)
        # Prompt referencing the outside file by relative name (should be rejected)
        pack = build_model_context_pack(cfg, [{"role": "user", "content": f"review {outside_path.name}"}], desc="quality review")
        assert "outside.txt" not in pack.text
        # Prompt referencing the inside file should include its preview
        pack_inside = build_model_context_pack(cfg, [{"role": "user", "content": "review inside.txt"}], desc="quality review")
        assert "inside.txt" in pack_inside.text


def test_model_context_prompt_named_file_signature_survives_read_error(monkeypatch) -> None:
    with tempfile.TemporaryDirectory(prefix="wla_ctx_sig_err_") as tmp:
        root = Path(tmp)
        file_path = root / "error.txt"
        file_path.write_text("content", encoding='utf-8')
        cfg = AssistantConfig(workspace=tmp)

        # Monkeypatch Path.read_text to raise an exception for the specific file
        original_read_text = Path.read_text

        def fake_read_text(self, *args, **kwargs):
            if self.resolve() == file_path.resolve():
                raise IOError("simulated read error")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", fake_read_text)

        pack = build_model_context_pack(cfg, [{"role": "user", "content": f"review {file_path.name}"}], desc="quality review")
        assert CONTEXT_HEADER in pack.text


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)


def test_model_context_static_defaults_keep_valid_loopback_url() -> None:
    source = Path("winlocalassistant/model_context.py").read_text(encoding="utf-8")
    assert 'ollama_url="http://127.0.0.1:11434"' in source
    assert "127.0.0-1" not in source
    assert '".[truncated]"' not in source
    assert '"...[truncated]"' in source
