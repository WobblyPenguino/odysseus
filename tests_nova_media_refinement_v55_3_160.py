
from __future__ import annotations

import json
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.image_generation import build_image_prompt_plan, render_image_prompt_plan_markdown
from winlocalassistant.nova_video import (
    build_video_image_prompt_plan,
    plan_video_manifest,
    write_storyboard_svg,
    write_shotlist_csv,
    write_video_render_package,
)
from winlocalassistant.tools import ToolRegistry


def test_image_prompt_plan_creates_variants_without_backend():
    plan = build_image_prompt_plan("friendly robot dog mascot", style="concept", variations=3)
    assert plan["ok"] is True
    assert len(plan["variants"]) == 3
    assert all("negative_prompt" in item for item in plan["variants"])
    assert "Nova Image Prompt Plan" in render_image_prompt_plan_markdown(plan)


def test_video_storyboard_and_package_files_are_written(tmp_path: Path):
    manifest = plan_video_manifest("A 10 second trailer about Nova building a polished app")
    storyboard = write_storyboard_svg(manifest, tmp_path)
    shotlist = write_shotlist_csv(manifest, tmp_path)
    prompts = build_video_image_prompt_plan(manifest)
    package = write_video_render_package("A 10 second trailer about Nova building a polished app", tmp_path / "pkg")
    assert storyboard.exists() and storyboard.read_text(encoding="utf-8").startswith("<svg")
    assert shotlist.exists() and "prompt" in shotlist.read_text(encoding="utf-8")
    assert prompts["shot_count"] >= 1
    assert Path(package["manifest_path"]).exists()
    assert Path(package["storyboard_path"]).exists()
    assert Path(package["preview_html_path"]).exists()
    assert Path(package["image_prompts_path"]).exists()


def test_core_exposes_media_commands(tmp_path: Path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    assert "Nova Media Status" in core.handle_command("/media-status")
    assert "Nova Image Prompt Plan" in core.handle_command("/image-plan robot dog mascot")
    assert "Storyboard written" in core.handle_command("/video-storyboard Nova trailer")
    assert "Nova Video Render Package" in core.handle_command("/video-package Nova trailer")


def test_tool_registry_exposes_media_tools(tmp_path: Path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    for name, kwargs in {
        "media_status": {},
        "image_plan": {"prompt": "robot dog mascot"},
        "video_storyboard": {"prompt": "Nova trailer"},
        "video_package": {"prompt": "Nova trailer"},
    }.items():
        result = registry.call(name, **kwargs)
        assert result.ok, (name, result.summary, result.data)
        assert "message" in result.data
