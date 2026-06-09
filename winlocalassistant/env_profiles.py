from __future__ import annotations
import shutil, sys, subprocess, json, time, logging
from typing import Any

PROFILES = {
 'minimal': {'required':['python','pytest','ollama'], 'optional':[]},
 'dev': {'required':['python','pytest','git','node','npm','docker','ollama'], 'optional':['ruff','pre-commit']},
 'gui-test': {'required':['node','npm'], 'optional':['playwright','chromium']},
 'ai-heavy': {'required':['python','ollama'], 'optional':['torch','diffusers','accelerate']},
}

def _check(name:str)->dict[str,Any]:
    if name=='python': return {'name':'python','ok':True,'detail':sys.version.split()[0]}
    if name in {'pytest','torch','diffusers','accelerate'}:
        try: __import__(name.replace('-','_')); return {'name':name,'ok':True,'detail':'import ok'}
        except Exception as e:
            logging.getLogger(__name__).debug('Python package check failed for %s', name, exc_info=True)
            return {'name':name,'ok':False,'detail':str(e)}
    exe=shutil.which(name)
    detail=exe or 'not found'
    if exe:
        try:
            cp=subprocess.run([exe,'--version'],capture_output=True,text=True,timeout=5)
            detail=(cp.stdout or cp.stderr or exe).strip().splitlines()[0]
        except Exception as exc:
            logging.getLogger(__name__).debug('Version check failed for external tool %s', name, exc_info=True)
    return {'name':name,'ok':bool(exe),'detail':detail}

def build_env_profile(name:str='minimal')->dict[str,Any]:
    key=(name or 'minimal').strip().lower()
    prof=PROFILES.get(key, PROFILES['minimal'])
    req=[_check(x) for x in prof['required']]
    opt=[_check(x) for x in prof['optional']]
    return {'profile':key,'generated_at':time.strftime('%Y-%m-%d %H:%M:%S'),'ok':all(x['ok'] for x in req),'required':req,'optional':opt,'install_plan':build_install_plan(key)}

def build_install_plan(key:str)->list[str]:
    if key=='dev': return ['py -m pip install ruff pre-commit']
    if key=='gui-test': return ['npm install -D @playwright/test','npx playwright install chromium']
    if key=='ai-heavy': return ['Review GPU/VRAM first; then install torch/diffusers only if needed']
    return []

def render_env_profile(p:dict[str,Any])->str:
    lines=['# Nova Environment Profile Doctor','',f"Profile: `{p.get('profile')}`",f"OK: **{p.get('ok')}**",'','## Required']
    for c in p.get('required',[]): lines.append(f"- {'✅' if c['ok'] else '❌'} {c['name']} — {c['detail']}")
    lines += ['','## Optional']
    for c in p.get('optional',[]): lines.append(f"- {'✅' if c['ok'] else '⚪'} {c['name']} — {c['detail']}")
    lines += ['','## Install/fix plan'] + ([f"- `{x}`" for x in p.get('install_plan',[])] or ['- none'])
    return '\n'.join(lines)
