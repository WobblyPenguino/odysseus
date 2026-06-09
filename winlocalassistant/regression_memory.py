from __future__ import annotations
import json, time, logging
from pathlib import Path
from typing import Any
from .safe_io import atomic_write_text
REG_PATH=Path.home()/'.winlocalassistant'/'regression_memory.json'

def load_regressions()->list[dict[str,Any]]:
    if REG_PATH.exists():
        try:
            data = json.loads(REG_PATH.read_text(encoding='utf-8'))
            return data if isinstance(data, list) else []
        except Exception as exc:
            logging.getLogger(__name__).debug('Could not load regression memory from %s', REG_PATH, exc_info=True)
    return []

def add_regression(description:str, repro:str='', expected:str='')->dict[str,Any]:
    items=load_regressions(); item={'id':f'reg-{int(time.time())}','description':description,'repro':repro,'expected':expected,'fixed_version':'','protection_status':'recorded','created_at':time.strftime('%Y-%m-%d %H:%M:%S')}; items.append(item); REG_PATH.parent.mkdir(parents=True,exist_ok=True); atomic_write_text(REG_PATH, json.dumps(items,indent=2)); return item

def export_regressions()->dict[str,Any]: return {'path':str(REG_PATH),'items':load_regressions()}

def render_regressions(payload:dict[str,Any]|list[dict[str,Any]])->str:
    items=payload if isinstance(payload,list) else payload.get('items',[])
    lines=['# Regression Memory Engine','',f"Count: **{len(items)}**"]
    for it in items[-20:]: lines += [f"## {it.get('id')}",f"- Description: {it.get('description')}",f"- Repro: `{it.get('repro','')}`",f"- Expected: {it.get('expected','')}",f"- Status: {it.get('protection_status','')}"]
    return '\n'.join(lines)
