from __future__ import annotations
import difflib, json, time
from pathlib import Path
from typing import Any
from .blueprint_engine import build_project_blueprint, build_candidate_set, score_candidate


def build_candidate_tournament(goal: str, root: str | Path='.') -> dict[str, Any]:
    bp = build_project_blueprint(goal)
    base = build_candidate_set(goal)['candidates']
    root=Path(root)
    files={}
    for n in ['index.html','style.css','app.js','README.md']:
        p=root/n
        if p.exists(): files[n]=p.read_text(encoding='utf-8', errors='replace')
    candidates=[]
    for c in base:
        txt = '\n'.join(files.values()) + '\n' + c['strategy']
        s=score_candidate(goal, files=files if files else None, text=txt)
        boost={'minimal':0,'polished':4,'robust':8}.get(c['name'],0)
        s['overall_percent']=min(100, s.get('overall_percent',0)+boost)
        candidates.append({**c,'score':s,'rank_reason':_rank_reason(s,c)})
    candidates=sorted(candidates,key=lambda x:x['score']['overall_percent'],reverse=True)
    return {'goal':goal,'generated_at':time.strftime('%Y-%m-%d %H:%M:%S'),'blueprint':bp,'candidates':candidates,'winner':candidates[0]['name'] if candidates else ''}


def _rank_reason(s:dict[str,Any],c:dict[str,Any])->str:
    if s.get('passed'): return 'passes prompt-derived score and has the lowest repair concern for its tier'
    if s.get('missing_requirements'): return 'needs repair: '+', '.join(s.get('missing_requirements',[])[:3])
    if s.get('forbidden_hits'): return 'blocked by forbidden/default-template hit'
    return 'candidate needs additional validation evidence'


def candidate_diff(a: str, b: str) -> str:
    return '\n'.join(difflib.unified_diff((a or '').splitlines(), (b or '').splitlines(), fromfile='candidate_a', tofile='candidate_b', lineterm=''))


def render_tournament(payload: dict[str,Any]) -> str:
    lines=['# Candidate Tournament','',f"Goal: {payload.get('goal','')}",f"Winner: **{payload.get('winner','')}**",'','## Candidates']
    for c in payload.get('candidates',[]):
        s=c.get('score',{})
        lines += [f"### {c.get('name')}",f"- Score: **{s.get('overall_percent')}%**",f"- Strategy: {c.get('strategy')}",f"- Rank reason: {c.get('rank_reason')}",f"- Missing: {', '.join(s.get('missing_requirements',[]) or ['none'])}",f"- Forbidden: {', '.join(s.get('forbidden_hits',[]) or ['none'])}"]
    lines += ['','## Promotion rule','Promote only the winner after contract validation, sandbox/Docker validation, and diff review pass.']
    return '\n'.join(lines)


def render_candidate_failure_report(payload: dict[str,Any]) -> str:
    lines=['# Candidate Failure Report','']
    for c in payload.get('candidates',[]):
        s=c.get('score',{})
        if s.get('passed'): continue
        lines.append(f"## {c.get('name')}")
        lines += [f"- Score: {s.get('overall_percent')}%", f"- Missing: {', '.join(s.get('missing_requirements',[]) or ['none'])}", f"- Forbidden: {', '.join(s.get('forbidden_hits',[]) or ['none'])}", f"- Repair cost: {'medium' if s.get('missing_requirements') else 'low'}"]
    return '\n'.join(lines)
