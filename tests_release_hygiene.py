from __future__ import annotations

import json
import tempfile
from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.project_iteration import ProjectIterationEvent, append_project_iteration_event


CURRENT_RELEASE_TEST_VERSION = "55.3.168"


def test_version_metadata_is_current() -> None:
    assert __version__ == CURRENT_RELEASE_TEST_VERSION
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 140)
    assert f"v{__version__}" in VERSION_LABEL


def test_readme_install_instructions_reference_current_zip() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert f"Nova v{__version__}" in readme
    assert f"Nova_v{__version__.replace('.', '_')}" in readme
    assert "Nova_v51_2_coding_engine_autonomous_hardening.zip" not in readme


def test_changelog_and_manifest_reference_current_version() -> None:
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads(Path("RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    assert f"v{__version__}" in changelog
    assert manifest.get("version") == __version__


def test_gitignore_excludes_runtime_and_cache_artifacts() -> None:
    text = Path(".gitignore").read_text(encoding="utf-8")
    assert "__pycache__/" in text
    assert "*.pyc" in text
    assert ".pytest_cache/" in text
    assert ".nova_runtime/" in text


def test_project_iteration_event_append_preserves_existing_jsonl_lines() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_iteration_append_") as tmp:
        root = Path(tmp)
        first = ProjectIterationEvent(round_no=1, stage="initial", ok=False, summary="first")
        second = ProjectIterationEvent(round_no=2, stage="repair", ok=True, summary="second")
        path = append_project_iteration_event(root, first)
        append_project_iteration_event(root, second)
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    assert lines[0]["summary"] == "first"
    assert lines[1]["summary"] == "second"


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


def test_launcher_scripts_reference_current_release_and_better_model_startup() -> None:
    ps1 = Path("start_nova_best_models.ps1").read_text(encoding="utf-8")
    bat = Path("start_nova_best_models.bat").read_text(encoding="utf-8")
    legacy = Path("start_windows_assistant.bat").read_text(encoding="utf-8")
    api = Path("start_nova_fastapi_api.bat").read_text(encoding="utf-8")
    assert "qwen3-coder:30b" in ps1
    assert "C:\\Program Files\\nodejs" in ps1
    assert "start_nova_best_models.ps1" in bat
    assert "start_nova_best_models" in legacy
    assert "start_nova_best_models.ps1" in api
    assert Path("START_NOVA_HERE.bat").exists()
    assert Path("SETUP_NOVA_FIRST.bat").exists()
    assert "START_NOVA_HERE.bat" in Path("README_START_HERE.txt").read_text(encoding="utf-8")
