import os
import tempfile
from pathlib import Path

from winlocalassistant.command_verifier import default_command_contracts
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_default_contracts_include_autonomous_journal() -> None:
    commands = {contract.command for contract in default_command_contracts()}
    assert "/autonomous-journal" in commands


def test_download_command_normalizes_windows_path() -> None:
    old = os.environ.get("NOVA_APP_DIR")
    with tempfile.TemporaryDirectory(prefix="wla_download_contract_") as tmp:
        os.environ["NOVA_APP_DIR"] = str(Path(tmp) / "profile")
        try:
            cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=False, allow_internet=False)
            core = AssistantCore(cfg)
            output = core.chat("/download folder\\nested\\file.txt")
        finally:
            if old is None:
                os.environ.pop("NOVA_APP_DIR", None)
            else:
                os.environ["NOVA_APP_DIR"] = old
    assert output == "Download link: /download?path=folder/nested/file.txt"


def run_all(verbose: bool = False) -> None:
    test_default_contracts_include_autonomous_journal()
    if verbose:
        print("PASS test_default_contracts_include_autonomous_journal")
    test_download_command_normalizes_windows_path()
    if verbose:
        print("PASS test_download_command_normalizes_windows_path")
