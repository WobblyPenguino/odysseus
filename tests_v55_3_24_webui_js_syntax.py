import re
from pathlib import Path


def test_pending_sandbox_permission_buttons_use_dataset_not_nested_quotes():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "quick('/sandbox-approve yes')" not in html
    assert 'data-command="/sandbox-approve yes" onclick="runDatasetCommand(this)"' in html
    assert 'data-command="/sandbox-cancel" onclick="runDatasetCommand(this)"' in html


def test_dynamic_tool_buttons_use_dataset_commands():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "data-tool=\"'+escAttr(name)+'\"" in html
    assert "data-command=\"'+escAttr('/tool-help '+name)+'\"" in html
    assert "quick(\\'/tool-help '+nm+'\\')" not in html


def test_webui_embedded_script_does_not_contain_known_broken_approval_call():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    m = re.search(r'HTML = r"""([\s\S]*?)"""', src)
    assert m, "webui HTML raw string should be present"
    scripts = re.findall(r"<script>([\s\S]*?)</script>", m.group(1))
    script = "\n".join(scripts)
    assert 'button onclick="quick(\'/sandbox-approve yes\')"' not in script
    assert "function send()" in script
