from __future__ import annotations

import json
from pathlib import Path

from winlocalassistant.browser_worker import build_browser_task_plan
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.document_ingestion import ingest_document, search_ingested_document
from winlocalassistant.integration_review import build_integration_review, render_integration_review
from winlocalassistant.model_registry import build_model_registry
from winlocalassistant.repo_intelligence import build_patch_plan, build_repo_map, render_repo_map
from winlocalassistant.tools import ToolRegistry


def test_repo_map_finds_entrypoints_and_tests():
    payload = build_repo_map(Path('.').resolve(), max_files=260)
    assert payload['files']
    assert 'app.py' in payload['entrypoints']
    assert any(str(x).startswith('tests') for x in payload['tests'])
    text = render_repo_map(payload)
    assert 'Recommended validation' in text


def test_patch_plan_has_validation_and_policy():
    repo_map = build_repo_map(Path('.').resolve(), max_files=120)
    plan = build_patch_plan('improve Nova video and browser planning', repo_map)
    assert plan['validation_commands']
    assert 'patch-first' in plan['apply_policy']


def test_browser_worker_plan_is_read_only_by_default_and_gates_writes():
    read_plan = build_browser_task_plan('research this page and summarize it')
    assert read_plan['classification']['read_only'] is True
    assert all(not step.get('requires_approval') for step in read_plan['steps'])
    write_plan = build_browser_task_plan('login and submit the form')
    assert write_plan['classification']['requires_approval'] is True
    assert any(step.get('requires_approval') for step in write_plan['steps'])


def test_document_ingestion_chunks_and_searches(tmp_path):
    doc = tmp_path / 'note.md'
    doc.write_text('# Nova\n\nNova should cite document chunks and preserve freshness.\n', encoding='utf-8')
    payload = ingest_document(doc)
    assert payload['ok'] is True
    assert payload['chunks']
    result = search_ingested_document(payload, 'freshness')
    assert result['results']
    assert result['results'][0]['source'] == 'note.md'


def test_model_registry_never_routes_embedding_as_chat():
    payload = build_model_registry(['nomic-embed-text:latest', 'qwen3-coder:30b', 'gemma2:2b', 'llama3.2-vision:11b'])
    assert payload['ok'] is True
    roles = {item['role']: item['preferred'] for item in payload['roles']}
    assert roles['code'] == 'qwen3-coder:30b'
    assert roles['embedding'] == 'nomic-embed-text:latest'
    assert roles['chat'] != roles['embedding']


def test_integration_review_exercises_foundation_boundaries():
    payload = build_integration_review(Path('.').resolve())
    assert payload['ok'] is True, payload
    names = {c['name'] for c in payload['checks']}
    assert {'state_machine_blocks_busy_listening', 'durable_job_queue', 'video_manifest_valid'}.issubset(names)
    assert 'Research alignment' in render_integration_review(payload)


def test_tool_registry_exposes_v55_3_153_tools(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(Path('.').resolve())))
    for name, kwargs in {
        'repo_map_deep': {'path': '.', 'max_files': 40},
        'patch_plan': {'goal': 'improve Nova safely'},
        'browser_task_plan': {'goal': 'research a local page'},
        'local_model_registry': {},
        'integration_review': {},
    }.items():
        result = registry.call(name, **kwargs)
        assert result.ok is True or name == 'local_model_registry'
        assert 'message' in result.data


def test_core_routes_v55_3_153_commands(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(Path('.').resolve())))
    for command in ['/repo-map .', '/patch-plan improve Nova', '/browser-plan read docs', '/model-registry', '/integration-review']:
        text = core.handle_command(command)
        assert 'Unknown command' not in text
        assert len(text) > 20
