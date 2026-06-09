from __future__ import annotations

from winlocalassistant.config import AssistantConfig


def test_config_env_overrides_better_pc_models(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVA_APP_DIR", str(tmp_path / "profile"))
    monkeypatch.setenv("NOVA_MODEL", "qwen3-coder:30b")
    monkeypatch.setenv("NOVA_CHAT_MODEL", "qwen3-coder:30b")
    monkeypatch.setenv("NOVA_PLANNER_MODEL", "qwen3-coder:30b")
    monkeypatch.setenv("NOVA_VISION_MODEL", "llama3.2-vision:11b")
    monkeypatch.setenv("NOVA_LOCAL_MODEL_TIMEOUT_SEC", "420")

    cfg = AssistantConfig.load()

    assert cfg.model == "qwen3-coder:30b"
    assert cfg.chat_model == "qwen3-coder:30b"
    assert cfg.planner_model == "qwen3-coder:30b"
    assert cfg.vision_model == "llama3.2-vision:11b"
    assert cfg.local_model_timeout_sec == 420
