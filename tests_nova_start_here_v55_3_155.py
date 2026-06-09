from __future__ import annotations

from pathlib import Path


def test_start_here_batch_is_the_obvious_entrypoint() -> None:
    start = Path("START_NOVA_HERE.bat").read_text(encoding="utf-8")
    setup = Path("SETUP_NOVA_FIRST.bat").read_text(encoding="utf-8")
    readme = Path("README_START_HERE.txt").read_text(encoding="utf-8")

    assert "START HERE" in start
    assert "start_nova_best_models.ps1" in start
    assert "-Setup" in start
    assert "-Mode web" in start
    assert "-Mode setup" in setup
    assert "START_NOVA_HERE.bat" in readme
    assert "qwen3-coder:30b" in readme


def test_best_model_launcher_can_create_and_validate_environment() -> None:
    ps1 = Path("start_nova_best_models.ps1").read_text(encoding="utf-8")
    assert "[switch]$Setup" in ps1
    assert "python -ErrorAction" in ps1 or "Get-Command python" in ps1
    assert "-m venv .venv" in ps1
    assert "requirements-dev.txt" in ps1
    assert "winlocalassistant.validate --all" in ps1
    assert "qwen3-coder:30b" in ps1
    assert "NOVA_SKIP_STARTUP_TESTS" in ps1


def test_validation_checks_startup_obviousness() -> None:
    text = Path("winlocalassistant/validate.py").read_text(encoding="utf-8")
    assert "startup_bat_obviousness" in text
    assert "START_NOVA_HERE.bat" in text
    assert "README_START_HERE.txt" in text
