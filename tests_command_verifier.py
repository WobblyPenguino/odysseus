from __future__ import annotations

from pathlib import Path
import tempfile

from winlocalassistant.command_verifier import (
    CommandContract,
    default_command_contracts,
    render_command_verification_markdown,
    verify_command_contracts,
)
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_command_verifier_detects_success_and_missing_markers() -> None:
    contracts = [
        CommandContract('/ok', 'ok command', ('hello',)),
        CommandContract('/bad', 'bad command', ('expected',)),
    ]
    report = verify_command_contracts(lambda command: 'hello world' if command == '/ok' else 'wrong output', contracts)
    assert report['passed'] == 1
    assert report['failed'] == 1
    assert not report['ok']
    md = render_command_verification_markdown(report)
    assert '/bad' in md
    assert 'Missing expected markers' in md


def test_command_verifier_flags_command_error_and_unknown_command() -> None:
    contracts = [
        CommandContract('/err', 'error command', ('anything',)),
        CommandContract('/unknown', 'unknown command', ('anything',)),
    ]
    outputs = {'/err': 'Command error: exploded', '/unknown': 'Unknown command. Use /help.'}
    report = verify_command_contracts(lambda command: outputs[command], contracts)
    assert report['failed'] == 2
    assert any('Command error:' in item['forbidden_hits'] for item in report['results'])
    assert any('Unknown command' in item['forbidden_hits'] for item in report['results'])


def test_default_contracts_are_safe_and_do_not_include_mutating_commands() -> None:
    commands = [contract.command for contract in default_command_contracts()]
    joined = '\n'.join(commands)
    assert '/self-improve' not in joined
    assert '/shell' not in joined
    assert '/write' not in joined
    assert '/delete' not in joined
    assert '/command-verify' not in joined
    assert '/version' in commands
    assert '/help' in commands


def test_core_command_verify_runs_existing_safe_commands() -> None:
    with tempfile.TemporaryDirectory(prefix='wla_command_verify_') as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=False, allow_internet=False)
        core = AssistantCore(cfg)
        out = core.chat('/command-verify')
        assert '# Nova Command Verification' in out
        assert 'Passed:' in out
        assert 'Unknown command' not in out
        assert 'Command error:' not in out
