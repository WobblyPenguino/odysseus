from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any

_FAILURES = ['syntax_error','missing_file','missing_handler','wrong_domain','readme_claim_false','validation_contract_failed','local_model_json_invalid','project_path_wrong','dependency_missing','browser_runtime_error']

def diagnose_repair(root: str | Path='.', evidence: str='') -> dict[str, Any]:
    root=Path(root); low=(evidence or '').lower(); files=list(root.glob('*')) if root.exists() else []
    kind='validation_contract_failed'
    if 'syntax' in low: kind='syntax_error'
    elif 'missing' in low and 'file' in low: kind='missing_file'
    elif 'handler' in low or 'onclick' in low: kind='missing_handler'
    elif 'dodge game' in low or 'wrong domain' in low: kind='wrong_domain'
    elif 'readme' in low and 'claim' in low: kind='readme_claim_false'
    elif 'json' in low and 'invalid' in low: kind='local_model_json_invalid'
    elif not any(p.suffix=='.py' for p in files) and not any((root/n).exists() for n in ['index.html','app.js','README.md']): kind='project_path_wrong'
    return {'root':str(root),'failure_type':kind,'evidence':evidence[:1000],'available_failure_types':_FAILURES,'risk':'low' if kind in {'missing_handler','readme_claim_false','syntax_error'} else 'medium','generated_at':time.strftime('%Y-%m-%d %H:%M:%S')}

def build_repair_plan(root: str | Path='.', evidence: str='') -> dict[str, Any]:
    d=diagnose_repair(root,evidence); kind=d['failure_type']
    ladder={
      'syntax_error':['patch the smallest syntax error','run parser/compile check','run targeted tests'],
      'missing_file':['create only the missing expected file','verify references','run final project check'],
      'missing_handler':['add the missing handler or change HTML to match existing function','run JS syntax and DOM wiring check'],
      'wrong_domain':['remove unrelated template artifacts','restore prompt-specific behaviours','rerun prompt contract validation'],
      'readme_claim_false':['either implement the claim or remove the README claim','rerun claim verifier'],
      'validation_contract_failed':['repair one missing contract item at a time','rerun contract validation'],
      'local_model_json_invalid':['strip fences/repair JSON','ask model with stricter schema only if repair fails'],
      'project_path_wrong':['resolve Nova/project root before mutation','rerun codebase audit'],
      'dependency_missing':['produce install plan; do not install without confirmation','rerun dependency check'],
      'browser_runtime_error':['capture console error','patch the smallest JS/UI issue','rerun Playwright or static JS check']}

    return {**d,'minimal_diff_policy':['prefer one file','prefer smallest diff','no broad rewrite unless two repairs fail','snapshot before apply','rollback available'], 'steps':ladder.get(kind,ladder['validation_contract_failed']), 'validation':['syntax/parse check','prompt contract validation','targeted regression test','release gate when Nova code changed']}

def render_repair(payload:dict[str,Any])->str:
    lines=['# Surgical Repair Engine v2','',f"Root: `{payload.get('root','')}`",f"Failure type: **{payload.get('failure_type','')}**",f"Risk: **{payload.get('risk','')}**",'','## Minimal-diff policy']
    lines += [f"- {x}" for x in payload.get('minimal_diff_policy',[])]
    lines += ['','## Plan'] + [f"{i+1}. {x}" for i,x in enumerate(payload.get('steps',[]))]
    lines += ['','## Validation'] + [f"- {x}" for x in payload.get('validation',[])]
    return '\n'.join(lines)
