from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.skill_profiles import choose_skill_mode, detect_skill_mode, try_quick_arithmetic


def _assistant() -> AssistantCore:
    tmp = tempfile.TemporaryDirectory(prefix="wla_skill_test_")
    cfg = AssistantConfig(workspace=tmp.name, local_model_timeout_sec=1)
    bot = AssistantCore(cfg)
    bot._tmp = tmp  # type: ignore[attr-defined]
    return bot


def test_skill_detection_routes_common_domains() -> None:
    assert detect_skill_mode("debug this Python traceback") == "coding"
    assert detect_skill_mode("solve this equation and calculate the percentage") == "math"
    assert detect_skill_mode("explain the chemistry reaction with units") == "science"
    assert detect_skill_mode("rewrite this cover letter paragraph naturally") == "communication"


def test_configured_skill_mode_overrides_auto_detection() -> None:
    assert choose_skill_mode("communication", "debug this Python function") == "communication"
    assert choose_skill_mode("auto", "debug this Python function") == "coding"


def test_quick_arithmetic_handles_simple_expression() -> None:
    answer = try_quick_arithmetic("calculate 2 + 3 * 4")
    assert answer is not None
    assert "14" in answer


def test_skill_mode_command_persists_mode() -> None:
    bot = _assistant()
    response = bot.handle_command("/skill-mode math")
    assert "math" in response.lower()
    assert bot.config.skill_mode == "math"


def test_direct_math_command_uses_local_quick_check_without_model() -> None:
    bot = _assistant()
    response = bot.handle_command("/math 10 / 2 + 7")
    assert "12" in response
    assert "quick arithmetic" in response.lower()


def test_plain_chat_injects_detected_skill_prompt() -> None:
    import winlocalassistant.core as core_module

    bot = _assistant()
    seen = {}
    old_model_chat = core_module.model_chat
    try:
        def fake_model_chat(config, model, messages, **kwargs):
            seen["system"] = messages[0]["content"]
            return "ok"
        core_module.model_chat = fake_model_chat
        assert bot._answer_plain_chat("debug this Python traceback") == "ok"
    finally:
        core_module.model_chat = old_model_chat
    assert "Coding and debugging specialist" in seen.get("system", "")


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
