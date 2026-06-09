from pathlib import Path
import json

from winlocalassistant.config import AssistantConfig
from winlocalassistant.planner import make_plan
from winlocalassistant.request_intent import analyze_request_intent
from winlocalassistant.tools import ToolRegistry


def test_failure_feedback_does_not_start_new_project_generation():
    goal = "you didntn actuall make anything or give me anything why? fix it?"
    plan = make_plan(goal, workspace=Path.cwd())
    tools = [step.tool for step in plan.steps]
    assert plan.mode == "diagnose"
    assert "ai_create_project" not in tools
    assert "ai_edit_project" not in tools
    assert "investigate_logs" in tools
    assert "development_strategy" in tools


def test_request_intent_classifies_failure_feedback_as_diagnostic():
    intent = analyze_request_intent("you didnt actually make anything why fix it")
    assert intent.category == "diagnostic_repair"
    assert not intent.wants_build
    assert not intent.wants_edit
    assert intent.safe_for_automatic_mutation


def test_meta_feedback_words_do_not_become_acceptance_terms():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    terms = registry._extract_requirement_terms("you didnt actually make anything or give me anything why? fix it?")
    assert terms == []


def test_local_model_context_serialisation_preserves_contracts_under_large_payload():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    payload = {
        "goal": "redesign GUI safely",
        "workspace_root": ".",
        "verification_conditions": ["condition"],
        "feature_preservation_contract": ["preserve project panel", "preserve tool refresh"],
        "action_receipt_contract": ["record changed files"],
        "strategy_rules_v2": ["patch before regenerate"],
        "mission_contract": {"success_conditions": ["real validation"]},
        "development_strategy": {"route": "surgical_recipe"},
        "project_type_contract": {"type": "wla_source"},
        "generation_template_manifest": {"templates": ["html_css_js_game"]},
        "recent_relevant_files": [{"path": f"file_{i}.py", "preview": "x" * 5000} for i in range(30)],
        "recent_runtime_context": "y" * 20000,
        "nova_operating_context": {"huge": "z" * 20000},
    }
    text = registry._serialise_local_model_context_payload(payload, max_chars=4000)
    assert len(text) <= 4000
    assert "feature_preservation_contract" in text
    assert "action_receipt_contract" in text
    assert "strategy_rules_v2" in text
    assert "preserve project panel" in text
    data = json.loads(text)
    assert "feature_preservation_contract" in data


def test_validate_model_project_no_longer_rejects_meta_feedback_for_missing_you():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    candidate = {
        "folder": "DiagnosticNote",
        "main_file": "README.md",
        "files": {
            "diagnose.py": "print('diagnose recent Nova failure and suggest next action')\n",
            "README.md": "# Diagnostic note\n\nThis project explains recent failure handling.\n" * 20,
        },
    }
    ok, reason = registry._validate_model_project(candidate, "you didnt actually make anything or give me anything why? fix it?")
    assert ok, reason
    assert "matched" not in reason.lower()
