from pathlib import Path


def test_best_model_launcher_loads_required_environment() -> None:
    ps1 = Path("start_nova_best_models.ps1").read_text(encoding="utf-8")
    assert "qwen3-coder:30b" in ps1
    assert "gemma2:2b" in ps1
    assert "llama3.2-vision:11b" in ps1
    assert "nomic-embed-text:latest" in ps1
    assert "winlocalassistant.validate --all" in ps1
    assert "C:\\Program Files\\nodejs" in ps1


def test_bat_launchers_delegate_to_best_model_launcher() -> None:
    main = Path("start_nova_best_models.bat").read_text(encoding="utf-8")
    legacy = Path("start_windows_assistant.bat").read_text(encoding="utf-8")
    api = Path("start_nova_fastapi_api.bat").read_text(encoding="utf-8")
    assert "start_nova_best_models.ps1" in main
    assert "start_nova_best_models.bat" in legacy
    assert "-Mode api" in api
