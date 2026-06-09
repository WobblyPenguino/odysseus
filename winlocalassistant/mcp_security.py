from __future__ import annotations
import time
from typing import Any
from .mcp_export import build_mcp_manifest

_DEFAULT_POLICY = {
    'default': 'deny_execute_allow_readonly',
    'read_only_tools': True,
    'command_execution': 'disabled_until_allowlisted',
    'raw_model_parameters': 'never_forward_without_schema_validation',
    'sandbox_risky_tools': True,
    'log_all_connector_calls': True,
}


def inspect_mcp_security(app: Any=None, root: Any=None) -> dict[str, Any]:
    manifest = build_mcp_manifest(app=app, root=root) if app is not None else {'tools': []}
    tools = manifest.get('tools', []) if isinstance(manifest, dict) else []
    risky=[]
    for t in tools:
        name=str(t.get('name',''))
        desc=str(t.get('description','')).lower()
        if any(k in name.lower()+desc for k in ['write','delete','exec','shell','install','promote','sandbox','docker']): risky.append(name)
    return {'generated_at':time.strftime('%Y-%m-%d %H:%M:%S'),'policy':_DEFAULT_POLICY,'tool_count':len(tools),'risky_tools':risky,'recommendations':['keep connectors read-only by default','sandbox risky tool execution','deny external tool descriptions that request secrets or command execution','require explicit user approval for install/promote/delete actions']}

def render_mcp_security(payload:dict[str,Any])->str:
    lines=['# Safe MCP / Connector Security Report','',f"Generated: {payload.get('generated_at','')}",f"Tools inspected: **{payload.get('tool_count',0)}**",'','## Policy']
    for k,v in payload.get('policy',{}).items(): lines.append(f"- {k}: `{v}`")
    lines += ['','## Risky tools needing sandbox/approval'] + ([f"- {x}" for x in payload.get('risky_tools',[])[:30]] or ['- none detected'])
    lines += ['','## Recommendations'] + [f"- {x}" for x in payload.get('recommendations',[])]
    return '\n'.join(lines)


def explain_mcp_tool(name:str, app:Any=None, root:Any=None)->str:
    manifest = build_mcp_manifest(app=app, root=root) if app is not None else {'tools': []}
    for t in manifest.get('tools',[]):
        if str(t.get('name','')).lower()==name.lower():
            risky = any(k in name.lower()+str(t.get('description','')).lower() for k in ['write','delete','exec','shell','install','promote'])
            return f"# MCP Tool Explanation\n\nTool: `{name}`\n\nRisk: **{'medium/high' if risky else 'low/read-only'}**\n\nDescription: {t.get('description','')}\n\nPolicy: {'Run only with explicit approval and sandboxing.' if risky else 'Read-only tool can be inspected safely.'}"
    return f"No MCP-style tool named `{name}` was found. Run `/mcp-tools` first."
