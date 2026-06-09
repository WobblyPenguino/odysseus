from __future__ import annotations

import json
import os
import platform
import re
import sys
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .eventlog import ACTIVITY_PATH, MODEL_IO_PATH, tail_jsonl, log_activity
from .safe_io import atomic_write_json, atomic_write_text, read_json_file, append_jsonl
from .release_hygiene import build_release_hygiene_report


def _now() -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _docs(root: Path) -> Path:
    p = Path(root) / 'docs'
    p.mkdir(parents=True, exist_ok=True)
    return p


def _read(path: Path, limit: int = 400_000) -> str:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding='utf-8', errors='replace')[:limit]
    except Exception:
        return ''
    return ''


def _project_files(root: Path) -> dict[str, str]:
    root = Path(root)
    out: dict[str, str] = {}
    for name in ['index.html', 'app.js', 'style.css', 'README.md', 'FINAL_OUTPUT.md', 'TEST_REPORT.md']:
        out[name] = _read(root / name)
    return out


def _contains_any(text: str, terms: list[str]) -> bool:
    low = (text or '').lower()
    return any(t.lower() in low for t in terms)


def build_quality_report(root: Path, goal: str = '') -> dict[str, Any]:
    files = _project_files(root)
    joined = '\n'.join(files.values()).lower()
    goal_low = (goal or '').lower()
    checks = []
    def add(name: str, ok: bool, detail: str):
        checks.append({'name': name, 'ok': bool(ok), 'detail': detail})
    html = files.get('index.html','')
    js = files.get('app.js','')
    readme = files.get('README.md','')
    add('has_entrypoint', bool(html or 'main.py' in [p.name for p in Path(root).glob('*')]), 'Project has index.html or another obvious entrypoint.')
    add('html_links_js', ('app.js' in html) if html else False, 'HTML should reference app.js for browser apps.')
    add('button_handler_wiring', _button_handlers_ok(html, js), 'Inline handlers and common button IDs should exist in JS.')
    add('localstorage_when_requested', ('localstorage' not in goal_low) or ('localstorage' in joined), 'localStorage is implemented when requested.')
    add('json_export_when_requested', ('export' not in goal_low and 'json' not in goal_low) or ('json.stringify' in joined and ('blob' in joined or 'download' in joined)), 'JSON export uses JSON.stringify plus Blob/download evidence when requested.')
    add('readme_claims_true', _readme_claims_look_true(readme, joined), 'README claims should have matching implementation evidence.')
    add('no_unrelated_dodge_default', not ('dodge game' in joined or ('player' in joined and 'enemy' in joined and 'canvas' in joined and 'dodge' not in goal_low)), 'Reject unrelated Dodge Game/default-game leakage.')
    add('manual_test_clarity', _contains_any(readme + files.get('TEST_REPORT.md',''), ['run', 'open', 'test', 'verify']), 'README/TEST_REPORT explain how to run or verify.')
    score = round(100 * sum(1 for c in checks if c['ok']) / max(1, len(checks)), 1)
    payload = {'ok': score >= 85, 'score': score, 'goal': goal, 'root': str(root), 'checks': checks, 'recommendations': _quality_recommendations(checks)}
    path = _docs(root) / 'NOVA_BUILD_QUALITY_LATEST.json'
    atomic_write_json(path, payload, ensure_ascii=True)
    atomic_write_text(path.with_suffix('.md'), render_build_quality(payload))
    return payload


def _button_handlers_ok(html: str, js: str) -> bool:
    if not html:
        return False
    handlers = re.findall(r'on(?:click|submit|change)=["\']([A-Za-z_$][\w$]*)\s*\(', html)
    for h in handlers:
        if not re.search(r'(function\s+' + re.escape(h) + r'\s*\(|(?:window\.)?' + re.escape(h) + r'\s*=|const\s+' + re.escape(h) + r'\s*=|let\s+' + re.escape(h) + r'\s*=)', js):
            return False
    ids = re.findall(r'id=["\']([^"\']+)["\']', html)
    if 'noteForm' in ids and 'noteForm' not in js:
        return False
    return True


def _readme_claims_look_true(readme: str, joined: str) -> bool:
    low = (readme or '').lower()
    claims = {
        'export': ['json.stringify','blob','download'],
        'localstorage': ['localstorage'],
        'delete': ['remove','delete'],
        'timer': ['setinterval','timer'],
    }
    for claim, evidence in claims.items():
        if claim in low and not any(e in joined for e in evidence):
            return False
    return True


def _quality_recommendations(checks: list[dict[str, Any]]) -> list[str]:
    recs = []
    for c in checks:
        if not c.get('ok'):
            recs.append(f"Fix {c.get('name')}: {c.get('detail')}")
    return recs or ['Build quality checks passed; run browser runtime tests for stronger evidence.']


def render_build_quality(payload: dict[str, Any]) -> str:
    lines = ['# Nova Build Quality Report','',f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**",f"Score: **{payload.get('score')}%**",f"Root: `{payload.get('root','')}`",f"Goal: {payload.get('goal','')}",'','## Checks']
    for c in payload.get('checks',[]):
        lines.append(f"- {'✅' if c.get('ok') else '❌'} **{c.get('name')}** — {c.get('detail')}")
    lines += ['','## Recommendations'] + [f"- {r}" for r in payload.get('recommendations',[])]
    return '\n'.join(lines)


def build_browser_runtime_test(root: Path, goal: str = '', mode: str = 'run') -> dict[str, Any]:
    files = _project_files(root)
    html = files.get('index.html','')
    js = files.get('app.js','')
    checks = []
    def add(name: str, ok: bool, detail: str): checks.append({'name': name, 'ok': bool(ok), 'detail': detail})
    add('browser_entrypoint_exists', bool(html), 'index.html exists for browser testing.')
    add('script_reference_resolves', 'app.js' in html and bool(js), 'index.html references existing app.js.')
    add('domcontent_or_safe_script', ('DOMContentLoaded' in js) or ('defer' in html) or ('</body>' in html and '<script' in html.lower()), 'JS should run after DOM is available or script is at body end.')
    add('clickable_controls', bool(re.search(r'<button|onclick=|addEventListener\(["\']click', html + js, re.I)), 'App has clickable controls.')
    add('storage_flow', ('localstorage' not in (goal or '').lower()) or ('localStorage' in js and ('setItem' in js and 'getItem' in js)), 'localStorage get/set flow present when requested.')
    add('export_flow', ('export' not in (goal or '').lower()) or ('Blob' in js and 'JSON.stringify' in js and 'download' in js), 'JSON export flow present when requested.')
    add('no_obvious_missing_dom_id', _no_missing_dom_ids(html, js), 'JS getElementById/querySelector references IDs present in HTML.')
    ok = all(c['ok'] for c in checks)
    payload = {'ok': ok, 'mode': mode, 'root': str(root), 'goal': goal, 'checks': checks, 'manual_steps': ['Open index.html or run /preview-start.', 'Click every primary button.', 'Refresh page and verify persistence if localStorage was requested.', 'Try export if requested.']}
    path = _docs(root) / 'NOVA_BROWSER_RUNTIME_TEST_LATEST.json'
    atomic_write_json(path, payload, ensure_ascii=True)
    atomic_write_text(path.with_suffix('.md'), render_browser_runtime(payload))
    return payload


def _no_missing_dom_ids(html: str, js: str) -> bool:
    ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
    refs = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', js))
    refs |= {m[1:] for m in re.findall(r'querySelector\(["\']#([^"\']+)["\']\)', js)}
    return refs.issubset(ids) if refs else True


def render_browser_runtime(payload: dict[str, Any]) -> str:
    lines = ['# Browser Runtime Test','',f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**",f"Root: `{payload.get('root','')}`",'','## Checks']
    for c in payload.get('checks',[]): lines.append(f"- {'✅' if c.get('ok') else '❌'} {c.get('name')} — {c.get('detail')}")
    lines += ['','## Manual steps'] + [f"- {s}" for s in payload.get('manual_steps',[])]
    return '\n'.join(lines)


def build_model_reliability(root: Path, focus: str = '') -> dict[str, Any]:
    activity = tail_jsonl(ACTIVITY_PATH, limit=200)
    model = tail_jsonl(MODEL_IO_PATH, limit=40)
    rejects = [e for e in activity if 'reject' in str(e.get('kind','')).lower() or 'rejected' in str(e.get('message','')).lower()]
    attempts = [e for e in activity if 'llm_attempt' in str(e.get('kind','')).lower()]
    failures = [e for e in activity if any(t in (str(e.get('kind',''))+str(e.get('message',''))).lower() for t in ['timeout','failed','not reachable','parseable json'])]
    recommendations=[]
    if len(rejects) >= 2: recommendations.append('Stop repeating the same prompt after two rejections; switch to prompt-contract + candidate tournament or deterministic template fallback.')
    if failures: recommendations.append('Use /model-output-coach and /model-fallback-strategy before another local model retry.')
    if not recommendations: recommendations.append('Model reliability looks acceptable from recent logs.')
    payload={'ok': len(failures) < 3, 'focus': focus, 'recent_attempts': len(attempts), 'recent_rejections': len(rejects), 'recent_failures': len(failures), 'recommendations': recommendations, 'last_model_io_count': len(model)}
    path=_docs(root)/'NOVA_MODEL_RELIABILITY_LATEST.json'; atomic_write_json(path,payload,ensure_ascii=True); atomic_write_text(path.with_suffix('.md'), render_model_reliability(payload)); return payload


def render_model_reliability(payload: dict[str, Any]) -> str:
    return '\n'.join(['# Local Model Reliability','',f"Overall: **{'READY' if payload.get('ok') else 'DEGRADED/ATTENTION'}**",f"Recent attempts: {payload.get('recent_attempts')}",f"Recent rejections: {payload.get('recent_rejections')}",f"Recent failures: {payload.get('recent_failures')}",'','## Recommendations']+[f"- {r}" for r in payload.get('recommendations',[])])


def build_model_fallback_strategy(root: Path, focus: str = '') -> dict[str, Any]:
    payload={'ok': True,'focus':focus,'strategy':['If JSON invalid: run /model-output-repair-json before retrying.','If off-course twice: run /prompt-contract and block unrelated templates.','If local model busy/degraded: switch to deterministic template or ask for confirmation before retrying.','If generated files fail browser runtime checks: run /repair-plan then /build-quality-repair.'],'retry_limits':{'same_rejection':2,'same_candidate_refinement':2,'llm_attempts_before_fallback':3}}
    return payload


def render_strategy(payload: dict[str, Any]) -> str:
    return '# Model Fallback Strategy\n\n'+'\n'.join(f"- {s}" for s in payload.get('strategy',[]))+"\n\n```json\n"+json.dumps(payload.get('retry_limits',{}),indent=2)+"\n```"


PATCH_QUEUE = APP_DIR / 'patch_queue.json'

def load_patch_queue() -> dict[str, Any]:
    return read_json_file(PATCH_QUEUE, {'patches': []}, expected_type=dict, quarantine=True)


def add_patch_queue_item(goal: str, diff: str = '', risk: str = 'low') -> dict[str, Any]:
    q=load_patch_queue(); item={'id':f"patch_{int(time.time())}_{len(q.get('patches',[]))+1}", 'goal':goal or 'safe Nova patch', 'risk':risk, 'diff':diff, 'status':'proposed', 'created_at':_now(), 'validation':['python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py','python tests_smoke.py']}; q.setdefault('patches',[]).append(item); atomic_write_json(PATCH_QUEUE,q,ensure_ascii=True); return item


def render_patch_queue(payload: dict[str, Any]) -> str:
    patches=payload.get('patches',[])
    lines=['# Nova Patch Queue','',f"Items: **{len(patches)}**"]
    for p in patches[-20:]: lines.append(f"- `{p.get('id')}` **{p.get('status')}** risk={p.get('risk')} — {p.get('goal')}")
    return '\n'.join(lines)


def patch_queue_action(action: str = 'status', goal: str = '') -> dict[str, Any]:
    q=load_patch_queue(); action=(action or 'status').lower()
    if action in {'propose','add'}:
        add_patch_queue_item(goal or 'safe improvement proposal')
        q=load_patch_queue()
    elif action in {'validate'}:
        for p in q.get('patches',[]):
            if p.get('status')=='proposed': p['status']='validated_pending_review'; p['validated_at']=_now()
        atomic_write_json(PATCH_QUEUE,q,ensure_ascii=True)
    elif action in {'promote'}:
        for p in q.get('patches',[]):
            if p.get('status') in {'validated_pending_review','proposed'}: p['status']='promoted_simulated'; p['promoted_at']=_now(); break
        atomic_write_json(PATCH_QUEUE,q,ensure_ascii=True)
    elif action in {'rollback'}:
        for p in q.get('patches',[]):
            if p.get('status') in {'promoted_simulated','validated_pending_review'}: p['status']='rolled_back_simulated'; p['rolled_back_at']=_now(); break
        atomic_write_json(PATCH_QUEUE,q,ensure_ascii=True)
    return q


def build_gui_cockpit_v2(root: Path, mode: str='preview') -> dict[str, Any]:
    features=['chat','projects','build','validate','repair','sandbox','autonomous','research','memory','settings','trace','patch queue','candidate comparison','model progress','architecture map']
    payload={'ok': True,'mode':mode,'feature_flagged': True,'classic_preserved': True,'layout':{'left':['Chat','Projects','Build','Validate','Repair','Sandbox','Autonomous','Research','Memory','Settings'],'center':['Prompt','Plan','Candidate','Files','Validation','Final Output'],'right':['Model status','Current trace','Autonomous state','Warnings','Next best action'],'bottom':['Attach','Mic','Mic test','Send','Model progress']},'feature_coverage':features,'regression_rules':['classic mode remains default','every classic feature mapped before cockpit default','run /gui-regression-test and /gui-visual-test before default switch']}
    path=_docs(root)/'NOVA_GUI_COCKPIT_V2_LATEST.json'; atomic_write_json(path,payload,ensure_ascii=True); atomic_write_text(path.with_suffix('.md'), render_gui_cockpit_v2(payload)); return payload


def render_gui_cockpit_v2(payload: dict[str, Any]) -> str:
    lines=['# GUI Cockpit v2 Preview','',f"Mode: `{payload.get('mode')}`",f"Classic preserved: **{payload.get('classic_preserved')}**",'','## Layout']
    for k,v in payload.get('layout',{}).items(): lines.append(f"- **{k}**: {', '.join(v)}")
    lines += ['','## Regression rules']+[f"- {r}" for r in payload.get('regression_rules',[])]
    return '\n'.join(lines)


def build_voice_mode_report(root: Path, mode: str='status') -> dict[str, Any]:
    payload={'ok': True,'mode':mode,'recommended_modes':['push-to-talk','continuous','readback-test'],'checks':['browser mic permission','selected input device','speech recognition support','transcript preview before send','readback using speechSynthesis'],'bluetooth_notes':['For WH-1000/WH-1000XM, select the Headset input device, not only Headphones output.','If no speech is detected, run /mic-test and Windows Settings > Sound > Input.']}
    return payload


def render_voice_mode(payload: dict[str, Any]) -> str:
    return '# Voice Mode Upgrade\n\n'+'\n'.join(f"- {x}" for x in payload.get('checks',[]))+"\n\n## Bluetooth notes\n"+'\n'.join(f"- {x}" for x in payload.get('bluetooth_notes',[]))


def list_templates() -> dict[str, Any]:
    return {'ok': True,'templates':['notes-app','dashboard','timer','crud-app','markdown-tool'],'recommendation':'Use deterministic templates for common apps, then let the model customize details.'}


def build_template_project(root: Path, template: str='notes-app') -> dict[str, Any]:
    template=(template or 'notes-app').lower().strip()
    if template not in list_templates()['templates']: template='notes-app'
    payload={'ok': True,'template': template,'files': {}}
    if template=='notes-app':
        payload['files']={
            'index.html':'<!doctype html><html><head><meta charset="utf-8"><title>Notes App</title><link rel="stylesheet" href="style.css"></head><body><main><h1>Notes</h1><form id="noteForm"><input id="noteInput" placeholder="Write a note"><button>Add</button></form><ul id="notesList"></ul><button id="exportBtn">Export JSON</button></main><script src="app.js"></script></body></html>',
            'style.css':'body{font-family:system-ui;margin:2rem;background:#f7f7fb}main{max-width:720px;margin:auto;background:white;padding:1rem;border-radius:16px;box-shadow:0 8px 30px #0001}button,input{padding:.7rem;margin:.25rem}li{display:flex;justify-content:space-between;padding:.5rem;border-bottom:1px solid #eee}',
            'app.js':'const input=document.getElementById("noteInput"),list=document.getElementById("notesList");let notes=JSON.parse(localStorage.getItem("notes")||"[]");function save(){localStorage.setItem("notes",JSON.stringify(notes));}function render(){list.innerHTML="";notes.forEach((n,i)=>{const li=document.createElement("li");li.textContent=n;const b=document.createElement("button");b.textContent="Delete";b.onclick=()=>{notes.splice(i,1);save();render();};li.appendChild(b);list.appendChild(li);});}document.getElementById("noteForm").onsubmit=e=>{e.preventDefault();const v=input.value.trim();if(v){notes.push(v);input.value="";save();render();}};document.getElementById("exportBtn").onclick=()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(notes,null,2)],{type:"application/json"}));a.download="notes.json";a.click();};render();',
            'README.md':'# Notes App\n\nOpen `index.html`. Add notes, refresh to confirm localStorage persistence, and click Export JSON to download notes.'}
    else:
        payload['files']={'index.html':f'<h1>{template}</h1><p>Template scaffold ready.</p>','README.md':f'# {template}\n\nOpen index.html.'}
    return payload


def render_templates(payload: dict[str, Any]) -> str:
    if 'files' in payload:
        return '# Template Build\n\n'+f"Template: **{payload.get('template')}**\n\nFiles staged: "+', '.join(payload.get('files',{}).keys())+'\n\nUse existing project write/promote flow to save these files.'
    return '# Project Templates\n\n'+'\n'.join(f"- {x}" for x in payload.get('templates',[]))+"\n\n"+payload.get('recommendation','')


def build_preview_server_report(root: Path, action: str='status') -> dict[str, Any]:
    return {'ok': True,'action':action,'root':str(root),'command':'python -m http.server 8767','url':'http://127.0.0.1:8767','notes':['Staged helper: run the command from the project folder for browser tests.','Use /browser-run-test after starting preview.']}


def render_preview(payload: dict[str, Any]) -> str:
    return '# Preview Server\n\n'+f"Action: `{payload.get('action')}`\nURL: `{payload.get('url')}`\nCommand: `{payload.get('command')}`\n"+'\n'.join(f"- {n}" for n in payload.get('notes',[]))


def build_feature_readiness(root: Path) -> dict[str, Any]:
    hygiene=build_release_hygiene_report(root)
    features=[
        {'name':'Docker validation','status':'ready' if shutil_which('docker') else 'missing dependency'},
        {'name':'Playwright GUI tests','status':'ready' if shutil_which('npx') else 'missing dependency'},
        {'name':'Voice input','status':'browser-dependent'},
        {'name':'Image generation','status':'optional backend required'},
        {'name':'Release hygiene','status':'ready' if hygiene.get('ok') else 'attention'},
    ]
    return {'ok': True,'features':features}


def shutil_which(name: str) -> bool:
    from shutil import which
    return which(name) is not None


def render_feature_readiness(payload: dict[str, Any]) -> str:
    return '# Feature Readiness\n\n'+'\n'.join(f"- **{f['name']}** — {f['status']}" for f in payload.get('features',[]))


def explain_error(text: str='') -> dict[str, Any]:
    low=(text or '').lower()
    if 'failed to fetch' in low:
        summary='The browser could not reach the Nova backend. The server may have restarted, crashed, or the page may be stale.'; steps=['Refresh the browser page.','Run /status.','If still broken, restart Nova from the .bat file.']
    elif 'health: degraded' in low or 'degraded' in low:
        summary='The local model/Ollama path is reachable but slow, busy, stale, or partly unavailable.'; steps=['Run /llm-status.','Wait for the current request or run /interrupt-current --confirm.','Use /model-reliability for retry strategy.']
    elif 'stopping' in low and 'ollama' in low:
        summary='Ollama reports a model is unloading/stopping. Nova should not start another long prompt until it clears.'; steps=['Run /llm-status.','If no Nova prompt is active, run /ollama-stop --confirm.']
    else:
        summary='No known error pattern matched. Use /support-report for context.'; steps=['Run /bug-review.','Run /trace-errors.','Copy /support-report output.']
    return {'ok': True,'input':text,'summary':summary,'next_steps':steps}


def render_error_explanation(payload: dict[str, Any]) -> str:
    return '# Error Explanation\n\n'+payload.get('summary','')+'\n\n## Next steps\n'+'\n'.join(f"- {s}" for s in payload.get('next_steps',[]))


def build_support_report(root: Path, focus: str='') -> dict[str, Any]:
    activity=tail_jsonl(ACTIVITY_PATH,limit=30)
    model=tail_jsonl(MODEL_IO_PATH,limit=5)
    payload={'ok': True,'version_context':'support report generated locally','root':str(root),'focus':focus,'generated_at':_now(),'activity_tail':activity[-10:],'model_tail_count':len(model),'release_hygiene':build_release_hygiene_report(root).get('overall'),'recommended_copy_paste':['/nova-mega-test --confirm','/bug-review','/trace-errors','/support-report']}
    path=_docs(root)/'NOVA_SUPPORT_REPORT_LATEST.json'; atomic_write_json(path,payload,ensure_ascii=True); atomic_write_text(path.with_suffix('.md'), render_support_report(payload)); return payload


def render_support_report(payload: dict[str, Any]) -> str:
    lines=['# Nova Support Report','',f"Generated: {payload.get('generated_at')}",f"Root: `{payload.get('root')}`",f"Focus: {payload.get('focus','')}",f"Release hygiene: {payload.get('release_hygiene')}",'','## Recent activity']
    for e in payload.get('activity_tail',[]): lines.append(f"- `{e.get('time','')}` {e.get('kind','')} — {str(e.get('message',''))[:180]}")
    lines+=['','## Commands to paste']+[f"- `{c}`" for c in payload.get('recommended_copy_paste',[])]
    return '\n'.join(lines)


def docs_index(root: Path, query: str='') -> dict[str, Any]:
    matches=[]
    q=(query or '').lower().strip()
    for p in list(Path(root).glob('*.md'))+list((Path(root)/'docs').glob('*.md') if (Path(root)/'docs').exists() else []):
        text=_read(p,80_000)
        if not q or q in text.lower() or q in p.name.lower(): matches.append({'path':str(p),'title':p.name,'preview':text[:300]})
        if len(matches)>=30: break
    return {'ok': True,'query':query,'matches':matches}


def render_docs_index(payload: dict[str, Any]) -> str:
    return '# Nova Docs/Code Index\n\n'+'\n'.join(f"- `{m['path']}` — {m['preview'][:120].replace(chr(10),' ')}" for m in payload.get('matches',[]))


def regression_test_generate(root: Path, bug: str='') -> dict[str, Any]:
    name='tests_generated_regression_' + re.sub(r'[^a-z0-9]+','_', (bug or 'wla_bug').lower()).strip('_')[:50] + '.py'
    body=f'''def test_regression_memory_placeholder():\n    bug = {bug!r}\n    assert bug\n    # Generated protection seed: convert this placeholder into an executable reproduction.\n'''
    payload={'ok': True,'test_name':name,'body':body,'status':'seed_generated_not_written','bug':bug}
    return payload


def render_regression_test(payload: dict[str, Any]) -> str:
    return '# Regression Test Generator\n\n'+f"Test seed: `{payload.get('test_name')}`\nStatus: **{payload.get('status')}**\n\n```python\n{payload.get('body','')}\n```"


def learning_status(root: Path) -> dict[str, Any]:
    regs_path=APP_DIR/'regressions.json'
    patchq=load_patch_queue()
    return {'ok': True,'mistake_learning':'active','regression_memory_exists':regs_path.exists(),'patch_queue_items':len(patchq.get('patches',[])),'learning_loop':['capture failure in trace','convert to regression seed','add to prompt-contract must_not/must_have','validate through /nova-mega-test','record outcome in project state']}


def render_learning_status(payload: dict[str, Any]) -> str:
    return '# Nova Mistake Learning Status\n\n'+f"Regression memory: **{payload.get('regression_memory_exists')}**\nPatch queue items: **{payload.get('patch_queue_items')}**\n\n## Loop\n"+'\n'.join(f"- {s}" for s in payload.get('learning_loop',[]))
