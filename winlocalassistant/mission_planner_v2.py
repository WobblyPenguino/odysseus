from __future__ import annotations
import json, time, logging
from pathlib import Path
from typing import Any
from .safe_io import atomic_write_text

_MISSION_PATH = Path.home()/'.winlocalassistant'/'mission_state.json'

def create_mission(goal:str)->dict[str,Any]:
    low=(goal or '').lower()
    allowed=['blueprint','prompt-tests','candidate-tournament','contract-validate','sandbox-dev-run','trace-last']
    if any(k in low for k in ['repair','fix','bug','broken']): allowed += ['repair-diagnose','repair-plan','repair-verify']
    if any(k in low for k in ['gui','ui','layout']): allowed += ['gui-feature-map','gui-regression-test','gui-visual-test']
    mission={'goal':goal or 'improve Nova safely','created_at':time.strftime('%Y-%m-%d %H:%M:%S'),'status':'planned','success_conditions':['prompt contract created','candidate or repair plan scored','validation evidence collected','no repeated no-op cycle','release/test gate passes when Nova code changes'],'tools_allowed':allowed,'stop_conditions':['no improvement after 2 cycles','same failure repeated','model unavailable','user foreground task starts','risk exceeds approval threshold'],'queue':[{'step':'contract','command':'/prompt-contract '+(goal or '')},{'step':'candidate','command':'/candidate-tournament '+(goal or '')},{'step':'validate','command':'/contract-validate '+(goal or '')},{'step':'trace','command':'/trace-last'}],'history':[]}
    _MISSION_PATH.parent.mkdir(parents=True,exist_ok=True); atomic_write_text(_MISSION_PATH, json.dumps(mission,indent=2))
    return mission

def load_mission()->dict[str,Any]:
    if _MISSION_PATH.exists():
        try:
            data = json.loads(_MISSION_PATH.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {'status':'corrupt','goal':'','queue':[],'history':[], 'warning':'mission state was not a JSON object'}
        except Exception as exc:
            logging.getLogger(__name__).debug('Could not load mission state from %s', _MISSION_PATH, exc_info=True)
            return {'status':'corrupt','goal':'','queue':[],'history':[], 'warning': str(exc)}
    return {'status':'none','goal':'','queue':[],'history':[]}

def mission_step()->dict[str,Any]:
    m=load_mission(); q=m.get('queue',[])
    if not q: return {**m,'next':None,'status':'complete' if m.get('status')!='none' else 'none'}
    nxt=q.pop(0); m['queue']=q; m.setdefault('history',[]).append({'time':time.strftime('%Y-%m-%d %H:%M:%S'),'suggested':nxt}); m['status']='in_progress' if q else 'ready_to_verify'; atomic_write_text(_MISSION_PATH, json.dumps(m,indent=2)); return {**m,'next':nxt}

def render_mission(m:dict[str,Any])->str:
    lines=['# Autonomous Mission Planner v2','',f"Goal: {m.get('goal','')}",f"Status: **{m.get('status','')}**",'','## Success conditions']
    lines += [f"- {x}" for x in m.get('success_conditions',[])] or ['- none']
    lines += ['','## Allowed tools'] + [f"- `{x}`" for x in m.get('tools_allowed',[])]
    lines += ['','## Stop conditions'] + [f"- {x}" for x in m.get('stop_conditions',[])]
    if m.get('next'): lines += ['','## Next recommended step',f"- {m['next'].get('step')}: `{m['next'].get('command')}`"]
    lines += ['','## Queue'] + ([f"- {x.get('step')}: `{x.get('command')}`" for x in m.get('queue',[])] or ['- empty'])
    return '\n'.join(lines)
