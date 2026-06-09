from __future__ import annotations

import tempfile
from pathlib import Path

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


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
