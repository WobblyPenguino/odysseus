from __future__ import annotations
import json, re
from typing import Any
from .blueprint_engine import score_candidate

def analyze_model_output(goal:str, output:str)->dict[str,Any]:
    raw=output or ''
    fenced=bool(re.search(r'```', raw))
    parsed=None; json_ok=False; repair=''
    text=raw.strip()
    if fenced:
        m=re.search(r'```(?:json)?\s*(.*?)```', raw, re.S|re.I)
        if m: text=m.group(1).strip()
    try:
        parsed=json.loads(text); json_ok=True
    except Exception as e:
        repair=str(e)
    files = parsed.get('files',{}) if isinstance(parsed,dict) and isinstance(parsed.get('files'),dict) else {}
    score=score_candidate(goal, files=files, text=raw)
    off=[]
    if fenced: off.append('markdown fences present when raw JSON/code may be required')
    if not json_ok: off.append('invalid JSON')
    if score.get('forbidden_hits'): off.append('forbidden/default-template contamination: '+', '.join(score.get('forbidden_hits',[])))
    if score.get('missing_requirements'): off.append('missing requirements: '+', '.join(score.get('missing_requirements',[])[:5]))
    return {'goal':goal,'json_ok':json_ok,'fenced':fenced,'files_detected':sorted(files.keys()),'score':score,'off_course':off,'json_error':repair,'coaching_prompt':build_coaching_prompt(goal,score,off)}

def build_coaching_prompt(goal:str, score:dict[str,Any], off:list[str])->str:
    forbidden=', '.join(score.get('forbidden_hits',[]) or ['unrelated defaults'])
    missing=', '.join(score.get('missing_requirements',[]) or ['prompt-specific behaviours'])
    return f"Your previous output was rejected for: {'; '.join(off) if off else 'insufficient evidence'}. User goal: {goal}. Return only the required format. Add missing: {missing}. Do not include: {forbidden}. Split code into the correct files and keep README claims truthful."

def render_model_output_coach(payload:dict[str,Any])->str:
    lines=['# Local Model Output Coach','',f"Goal: {payload.get('goal','')}",f"JSON ok: **{payload.get('json_ok')}**",f"Markdown fenced: **{payload.get('fenced')}**",f"Files detected: {', '.join(payload.get('files_detected',[]) or ['none'])}",f"Score: **{payload.get('score',{}).get('overall_percent','?')}%**",'','## Off-course signals']
    lines += [f"- {x}" for x in payload.get('off_course',[])] or ['- none']
    lines += ['','## Coaching prompt',payload.get('coaching_prompt','')]
    return '\n'.join(lines)
