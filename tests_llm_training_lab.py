from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.llm_training_lab import (
    build_lab_report,
    estimate_training_budget,
    inspect_dataset,
    render_command,
    render_lab_markdown,
)
from winlocalassistant.command_help import command_help_payload


def test_llm_training_lab_inspects_dataset_and_writes_report(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "sample.txt").write_text("attention connects tokens\nattention connects tokens\nloss goes down\n", encoding="utf-8")
    stats = inspect_dataset(data)
    assert stats.exists is True
    assert stats.text_files == 1
    assert stats.approx_tokens > 0
    assert stats.unique_line_ratio < 1.0
    payload = build_lab_report(tmp_path, goal="tiny GPT smoke", dataset="data", params="13m", tokens="5m")
    assert payload["ok"] is True
    assert (tmp_path / "docs" / "NOVA_LLM_TRAINING_LAB_LATEST.json").exists()
    rendered = render_lab_markdown(payload)
    assert "Nova LLM Training Lab" in rendered
    assert "Dataset inspection" in rendered


def test_llm_training_lab_estimate_is_conservative_and_useful():
    estimate = estimate_training_budget("13m", "5m", seq_len=512, batch_size=2)
    assert estimate["params"] == 13_000_000
    assert estimate["tokens"] == 5_000_000
    assert estimate["estimated_steps"] > 0
    assert "recommendation" in estimate


def test_llm_lab_command_and_help_are_routable(tmp_path: Path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False, local_model_timeout_sec=0, chat_model_timeout_sec=0))
    help_text = core.handle_command("/llm-lab help")
    assert "/llm-lab dataset PATH" in help_text
    estimate = core.handle_command("/llm-lab estimate 13m 5m")
    assert "Rough budget estimate" in estimate
    direct = render_command("plan learn tokenizer", root=tmp_path)
    assert "Training plan" in direct
    payload = command_help_payload("llm-lab")
    assert payload["count"] >= 1
