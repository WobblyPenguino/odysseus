from __future__ import annotations
import os, platform, shutil, subprocess, sys, time
from typing import Any

def benchmark_system()->dict[str,Any]:
    def cmd(args):
        try:
            cp=subprocess.run(args,capture_output=True,text=True,timeout=8)
            return (cp.stdout or cp.stderr).strip()[:2000]
        except Exception as e: return str(e)
    return {'generated_at':time.strftime('%Y-%m-%d %H:%M:%S'),'python':sys.version.split()[0],'platform':platform.platform(),'processor':platform.processor(),'cpu_count':os.cpu_count(),'docker':cmd(['docker','--version']) if shutil.which('docker') else 'missing','ollama':cmd(['ollama','--version']) if shutil.which('ollama') else 'missing','node':cmd(['node','--version']) if shutil.which('node') else 'missing','recommendations':['benchmark /fast build before and after new PC','increase local model timeout only if model quality improves','try larger coder model when VRAM >= 12GB','raise Docker memory/CPU after confirming stability']}

def render_benchmark(p:dict[str,Any])->str:
    lines=['# Nova New-PC Benchmark / Migration Report','',f"Generated: {p.get('generated_at')}",f"Platform: `{p.get('platform')}`",f"Python: `{p.get('python')}`",f"CPU count: **{p.get('cpu_count')}**",f"Processor: `{p.get('processor')}`",'','## Tool versions',f"- Docker: {p.get('docker')}",f"- Ollama: {p.get('ollama')}",f"- Node: {p.get('node')}", '','## Recommendations']
    lines += [f"- {x}" for x in p.get('recommendations',[])]
    return '\n'.join(lines)
