from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from .blueprint_engine import build_project_blueprint, score_candidate


def build_prompt_contract(goal: str) -> dict[str, Any]:
    bp = build_project_blueprint(goal)
    low = (goal or '').lower()
    must = list(bp.get('must_have', []))
    must_not = list(bp.get('must_not_have', []))
    static = list(bp.get('validation_rules', []))
    if 'note' in low:
        for x in ['add notes', 'delete notes', 'display notes']:
            if x not in must: must.append(x)
    if 'localstorage' in low or 'save' in low:
        if 'persist notes in localStorage' not in must: must.append('persist notes in localStorage')
        static.append('app.js contains localStorage and safe JSON parse fallback')
    if 'export' in low or 'json' in low:
        if 'export notes as JSON' not in must: must.append('export notes as JSON')
        static.append('app.js contains Blob or JSON.stringify download export')
    if 'game' not in low:
        must_not += ['Dodge Game', 'score/player/enemy/canvas game defaults']
    return {
        'goal': goal or 'general Nova task',
        'artifact_type': bp.get('artifact_type','generic_project'),
        'must_have': sorted(set(must)),
        'must_not_have': sorted(set(must_not)),
        'static_checks': sorted(set(static)),
        'runtime_checks': ['open/run main entrypoint', 'exercise key buttons/handlers', 'verify output matches prompt'],
        'repair_hints': bp.get('repair_hints', []),
    }


def validate_contract(goal: str, root: str | Path = '.') -> dict[str, Any]:
    root = Path(root)
    contract = build_prompt_contract(goal)
    files: dict[str,str] = {}
    for name in ['index.html','style.css','app.js','README.md']:
        p = root / name
        if p.exists():
            try: files[name] = p.read_text(encoding='utf-8', errors='replace')
            except Exception: files[name] = ''
    score = score_candidate(goal, files=files)
    corpus = '\n'.join(files.values()).lower()
    checks=[]
    for rule in contract['static_checks']:
        low = rule.lower()
        ok = True
        if 'localstorage' in low: ok = 'localstorage' in corpus
        elif 'blob' in low or 'json.stringify' in low: ok = 'blob' in corpus or 'json.stringify' in corpus
        elif 'html references' in low: ok = ('app.js' in files and 'index.html' in files and 'app.js' in files.get('index.html',''))
        elif 'handlers' in low: ok = _handlers_exist(files.get('index.html',''), files.get('app.js',''))
        checks.append({'rule': rule, 'ok': ok})
    forbidden_hits = [x for x in contract['must_not_have'] if x.lower() in corpus]
    ok = score.get('passed', False) and not forbidden_hits and all(c['ok'] for c in checks)
    return {'ok': ok, 'contract': contract, 'score': score, 'checks': checks, 'forbidden_hits': forbidden_hits, 'root': str(root)}


def _handlers_exist(html: str, js: str) -> bool:
    handlers = re.findall(r'on\w+\s*=\s*["\']([A-Za-z_$][\w$]*)\s*\(', html or '')
    return all(re.search(r'function\s+'+re.escape(h)+r'\s*\(|(?:window\.)?'+re.escape(h)+r'\s*=|const\s+'+re.escape(h)+r'\s*=|let\s+'+re.escape(h)+r'\s*=', js or '') for h in handlers)


def render_prompt_contract(contract: dict[str, Any]) -> str:
    lines=['# Prompt Contract','',f"Goal: {contract.get('goal','')}",f"Artifact type: `{contract.get('artifact_type','')}`",'','## Must have']
    lines += [f"- {x}" for x in contract.get('must_have',[])] or ['- none']
    lines += ['','## Must not have'] + ([f"- {x}" for x in contract.get('must_not_have',[])] or ['- none'])
    lines += ['','## Static checks'] + ([f"- {x}" for x in contract.get('static_checks',[])] or ['- none'])
    lines += ['','## Runtime checks'] + ([f"- {x}" for x in contract.get('runtime_checks',[])] or ['- none'])
    return '\n'.join(lines)


def render_contract_validation(payload: dict[str, Any]) -> str:
    lines=['# Prompt Contract Validation','',f"Root: `{payload.get('root','')}`",f"OK: **{payload.get('ok')}**",f"Score: **{payload.get('score',{}).get('overall_percent','?')}%**",'','## Checks']
    for c in payload.get('checks',[]): lines.append(f"- {'✅' if c.get('ok') else '❌'} {c.get('rule')}")
    lines += ['','## Forbidden hits'] + ([f"- {x}" for x in payload.get('forbidden_hits',[])] or ['- none'])
    lines += ['','## Missing requirements'] + ([f"- {x}" for x in payload.get('score',{}).get('missing_requirements',[])] or ['- none'])
    return '\n'.join(lines)
