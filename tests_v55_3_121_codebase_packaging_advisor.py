from pathlib import Path
import zipfile

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.codebase_advisor import build_codebase_advisor, render_codebase_advisor
from winlocalassistant.config import AssistantConfig
from winlocalassistant.release_packager import build_release_package, collect_release_files, render_release_package
from winlocalassistant.tools import ToolRegistry


def test_version_121_label_preserves_previous_feature_markers():
    assert tuple(map(int, __version__.split('.'))) >= (55, 3, 121)
    assert f"v{__version__}" in VERSION_LABEL
    assert "codebase advisor" in VERSION_LABEL
    assert "clean release packaging" in VERSION_LABEL
    assert "completion audit" in VERSION_LABEL
    assert "Hey Nova" in VERSION_LABEL
    assert "voice reliability" in VERSION_LABEL
    assert "autonomous cockpit" in VERSION_LABEL
    assert "self-validation" in VERSION_LABEL


def test_release_packager_collects_files_and_excludes_runtime_noise(tmp_path):
    root = tmp_path / "repo"
    (root / "winlocalassistant").mkdir(parents=True)
    (root / "winlocalassistant" / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding='utf-8')
    for rel in ["app.py", "README.md", "CHANGELOG.md", "start_windows_assistant.bat", "winlocalassistant/core.py", "winlocalassistant/tools.py", "winlocalassistant/webui.py"]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding='utf-8')
    (root / ".pytest_cache").mkdir()
    (root / ".pytest_cache" / "noise.txt").write_text("skip", encoding='utf-8')
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "noise.pyc").write_bytes(b"skip")
    (root / "codebase_integrity_reports").mkdir()
    (root / "codebase_integrity_reports" / "old.json").write_text("{}", encoding='utf-8')

    collected = collect_release_files(root)
    assert collected["ok"] is True
    included = {item["path"] for item in collected["files"]}
    skipped = {item["path"] for item in collected["skipped"]}
    assert "app.py" in included
    assert ".pytest_cache/noise.txt" in skipped
    assert "__pycache__/noise.pyc" in skipped
    assert "codebase_integrity_reports/old.json" in skipped

    payload = build_release_package(root, out_dir=tmp_path / "out")
    assert payload["ok"] is True
    md = render_release_package(payload)
    assert "Clean Release Package" in md
    with zipfile.ZipFile(payload["package_path"], "r") as zf:
        names = set(zf.namelist())
    assert "RELEASE_MANIFEST.json" in names
    assert "app.py" in names
    assert ".pytest_cache/noise.txt" not in names


def test_codebase_advisor_reports_implemented_and_future_items():
    payload = build_codebase_advisor(Path.cwd())
    assert payload["ok"] is True
    ids = {item["id"] for item in payload["findings"]}
    assert "clean_release_packaging" in ids
    assert "codebase_advisor" in ids
    assert payload["implemented_now"]
    md = render_codebase_advisor(payload)
    assert "Implemented in this pass" in md
    assert "Recommended next improvements" in md


def test_tools_and_core_route_new_advisor_packager_commands():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    assert "release_package" in registry.tools
    assert "clean_release_package" in registry.tools
    assert "codebase_advisor" in registry.tools
    assert "next_codebase_improvements" in registry.tools
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "/release-package" in src
    assert "/codebase-advisor" in src
    assert "release_package" in src
    assert "codebase_advisor" in src


def test_gui_and_validation_contracts_expose_new_commands():
    webui = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert f"v{__version__}" in webui
    assert "/release-package" in webui
    assert "/codebase-advisor" in webui
    assert "Release package" in webui
    assert "Codebase advisor" in webui
    continuity = Path("winlocalassistant/feature_continuity.py").read_text(encoding="utf-8")
    assert "codebase_packaging_advisor" in continuity
    matrix = Path("winlocalassistant/validation_matrix.py").read_text(encoding="utf-8")
    assert "release-package" in matrix
    assert "codebase-advisor" in matrix
