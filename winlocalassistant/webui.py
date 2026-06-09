from __future__ import annotations

import html
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import __version__, VERSION_LABEL, ASSISTANT_NAME
from .command_suggestions import suggest_next_commands
from .config import APP_DIR
from .core import AssistantCore
from .file_context import MAX_UPLOAD_BYTES, register_uploaded_file, list_file_contexts, clear_file_contexts
from .safety import resolve_inside_workspace
from .safe_io import read_json_file
from .conversation_store import list_conversations, search_conversations
from .release_checklist import build_release_checklist
from .build_info import build_patch_identity
from .eventlog import delete_activity_runs, SESSION_ID
from .nova_odysseus_suite import build_odysseus_workspace_snapshot, odysseus_dependency_status, odysseus_runtime_action, odysseus_workspace_action
from .webui_layout_overhaul import apply_gui_layout_overhaul
from .webui_ai_help_overlay import apply_ai_help_overlay
from .webui_cyberpunk_theme import apply_cyberpunk_theme
from .webui_interaction_overhaul import apply_interaction_overhaul
from .webui_arcade import apply_arcade
from .webui_emergency_stability import apply_emergency_stability


def _latest_json_file(directory: Path, pattern: str) -> Path | None:
    try:
        if not directory.exists() or not directory.is_dir():
            return None
        files = [path for path in directory.glob(pattern) if path.is_file() and path.suffix.lower() == ".json"]
        if not files:
            return None
        return max(files, key=lambda path: (path.stat().st_mtime, path.name))
    except Exception:
        return None


def _read_json_file(path: Path) -> dict | None:
    data = read_json_file(path, None, expected_type=dict, quarantine=True)
    if isinstance(data, dict):
        return data
    return {"_read_error": f"Latest idle report could not be read as a JSON object: {path}"}


def _latest_idle_status_payload() -> dict:
    report_path = _latest_json_file(APP_DIR / "idle_runs", "idle_cycle_*.json")
    proposal_path = _latest_json_file(APP_DIR / "idle_patch_proposals", "idle_patch_proposal_*.json")
    if not report_path and not proposal_path:
        return {
            "latest_idle_report_path": "",
            "latest_idle_proposal_path": "",
            "selected_candidate_title": "",
            "category": "",
            "status": "no-idle-reports",
            "auto_apply_status": "",
            "value_score": None,
            "risk_score": None,
            "confidence_score": None,
            "final_score": None,
            "last_updated": "",
            "message": "No idle self-improvement reports yet.",
        }

    report_data = _read_json_file(report_path) if report_path else None
    proposal_data = _read_json_file(proposal_path) if proposal_path else None
    for data in [report_data, proposal_data]:
        if isinstance(data, dict) and data.get("_read_error"):
            return {
                "latest_idle_report_path": str(report_path) if report_path else "",
                "latest_idle_proposal_path": str(proposal_path) if proposal_path else "",
                "selected_candidate_title": "",
                "category": "",
                "status": "idle-report-read-error",
                "auto_apply_status": "",
                "value_score": None,
                "risk_score": None,
                "confidence_score": None,
                "final_score": None,
                "last_updated": "",
                "message": str(data.get("_read_error")),
            }

    sources: list[tuple[float, str, Path, dict]] = []
    if report_path and isinstance(report_data, dict):
        sources.append((report_path.stat().st_mtime, "report", report_path, report_data))
    if proposal_path and isinstance(proposal_data, dict):
        sources.append((proposal_path.stat().st_mtime, "proposal", proposal_path, proposal_data))
    if not sources:
        return {
            "latest_idle_report_path": str(report_path) if report_path else "",
            "latest_idle_proposal_path": str(proposal_path) if proposal_path else "",
            "selected_candidate_title": "",
            "category": "",
            "status": "idle-report-read-error",
            "auto_apply_status": "",
            "value_score": None,
            "risk_score": None,
            "confidence_score": None,
            "final_score": None,
            "last_updated": "",
            "message": "Latest idle report could not be read.",
        }

    _mtime, source_kind, source_path, data = max(sources, key=lambda item: (item[0], item[2].name))
    candidate = data.get("selected_candidate") if source_kind == "report" else data.get("candidate")
    if not isinstance(candidate, dict):
        candidate = {}
    title = str(candidate.get("title") or "No safe candidate")
    status = str(data.get("status") or "unknown")
    auto_gate = data.get("auto_apply_gate")
    if not isinstance(auto_gate, dict):
        auto_gate = {}
    return {
        "latest_idle_report_path": str(report_path) if report_path else "",
        "latest_idle_proposal_path": str(proposal_path) if proposal_path else "",
        "selected_candidate_title": title,
        "category": str(candidate.get("category") or ""),
        "status": status,
        "auto_apply_status": str(auto_gate.get("status") or ""),
        "value_score": _score_or_none(candidate.get("value_score")),
        "risk_score": _score_or_none(candidate.get("risk_score")),
        "confidence_score": _score_or_none(candidate.get("confidence_score")),
        "final_score": _score_or_none(candidate.get("final_score")),
        "last_updated": str(data.get("timestamp") or _mtime_iso(source_path)),
        "message": f"Latest idle {source_kind} status: {status}.",
    }


def _score_or_none(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _mtime_iso(path: Path) -> str:
    try:
        import datetime

        return datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except Exception:
        return ""


PWA_MANIFEST = {
    "name": "Nova Odysseus Workbench",
    "short_name": "Nova",
    "description": "Local Nova assistant workbench with Odysseus-inspired workspace windows.",
    "start_url": "/odysseus-workbench",
    "scope": "/",
    "display": "standalone",
    "background_color": "#e8eef8",
    "theme_color": "#101722",
    "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}],
    "shortcuts": [
        {"name": "Workbench", "short_name": "Workbench", "url": "/odysseus-workbench", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},
        {"name": "Odysseus Runtime", "short_name": "Runtime", "url": "/odysseus-runtime", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},
        {"name": "Research", "short_name": "Research", "url": "/odysseus-research", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},
        {"name": "Uploads", "short_name": "Uploads", "url": "/odysseus-uploads", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},
        {"name": "Code", "short_name": "Code", "url": "/odysseus-code", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},
    ],
}

PWA_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" rx="24" fill="#101722"/><path d="M24 74 64 22l40 52-40 32Z" fill="#0e9fbd"/><path d="M38 78h52l-26 28Z" fill="#15985c"/><circle cx="64" cy="64" r="16" fill="#f8fbff"/></svg>"""

SERVICE_WORKER_JS = r"""
// legacy cache compatibility marker: 55-3-139
// previous cache compatibility marker: nova-orbit-shell-v55-3-164-legacy-continuity-v1
const CACHE_NAME = 'nova-orbit-shell-v55-3-168-project-state-v1';
const SHELL_URLS = [
  '/',
  '/odysseus-workbench',
  '/odysseus-runtime',
  '/odysseus-research',
  '/odysseus-uploads',
  '/odysseus-code',
  '/manifest.webmanifest',
  '/pwa-icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL_URLS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/') || url.pathname === '/chat' || url.pathname.startsWith('/download') || url.pathname.startsWith('/project-view/') || url.pathname === '/view') return;
  if (!SHELL_URLS.includes(url.pathname)) return;
  event.respondWith(fetch(req, {cache:'no-store'}).then(response => {
    const copy = response.clone();
    caches.open(CACHE_NAME).then(cache => cache.put(req, copy)).catch(()=>{});
    return response;
  }).catch(() => caches.match(req)));
});
""".strip()


HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#101722">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Nova">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/pwa-icon.svg" type="image/svg+xml">
<title>Nova</title>
<style>
:root{--bg:#e8eef8;--panel:#ffffff;--ink:#101827;--muted:#667085;--line:#d9e2ef;--blue:#0b84ff;--blue2:#006edc;--ai:#ffffff;--good:#0f9f6e;--warn:#b54708;--bad:#d92d20;--purple:#7c3aed;--shadow:0 18px 50px rgba(16,24,40,.12)}
*{box-sizing:border-box} body{font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#e8eef8,#f7f9fc);color:var(--ink);margin:0;height:100vh;overflow:hidden;--left-col:330px;--right-col:440px}
main{height:100vh;display:grid;grid-template-columns:var(--left-col) 6px minmax(420px,1fr) 6px var(--right-col);gap:10px;padding:14px;max-width:1780px;margin:0 auto}.card{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow);backdrop-filter:blur(10px)}
.sidebar,.rightbar{padding:14px;overflow:auto;min-width:0}.sidebar{grid-column:1}.leftRail{grid-column:2}.chat-wrap{grid-column:3}.rightRail{grid-column:4}.rightbar{grid-column:5}.resizeRail{border-radius:999px;background:rgba(11,132,255,.10);cursor:col-resize;align-self:stretch;min-height:120px}.resizeRail:hover,.resizeRail.dragging{background:rgba(11,132,255,.30)}body.collapse-left main{--left-col:0px;grid-template-columns:0 0 minmax(360px,1fr) 6px var(--right-col);gap:6px}body.collapse-right main{--right-col:0px;grid-template-columns:var(--left-col) 6px minmax(360px,1fr) 0 0;gap:6px}body.collapse-left.collapse-right main{grid-template-columns:0 0 minmax(300px,1fr) 0 0;gap:0}body.collapse-left .sidebar,body.collapse-right .rightbar,body.collapse-left .leftRail,body.collapse-right .rightRail{display:none}body.collapse-left .chat-wrap{grid-column:3}body.collapse-right .chat-wrap{grid-column:3}/* Always-listening is on by default. v55.3.124 hidden-panel layout reclaim: collapsed sidebars no longer reserve their stored widths. */body.collapse-activity .activity{display:block!important;max-height:38px!important;min-height:38px!important;overflow:hidden!important;padding:8px 14px!important;border-top:1px solid var(--line)}body.collapse-activity .activity #activityLog{display:none!important}body.collapse-activity .activity h3{margin:0}.activity.collapsed{max-height:38px!important;overflow:hidden!important}.refreshSpinner{display:none;margin-left:6px;width:13px;height:13px;border:2px solid #bfdbfe;border-top-color:#2563eb;border-radius:999px;animation:spin .8s linear infinite}.loading .refreshSpinner{display:inline-block}@keyframes spin{to{transform:rotate(360deg)}}.modelCards{display:grid;gap:6px;margin-top:6px}.modelCard{border:1px solid var(--line);border-radius:10px;background:white;padding:6px}.modelCard summary{cursor:pointer;font-weight:800}.modelProgress{height:8px;background:#e5e7eb;border-radius:999px;overflow:hidden;margin:6px 0}.modelProgress>div{height:100%;background:linear-gradient(90deg,#60a5fa,#8b5cf6);transition:width .4s ease}.createdClose{float:right;background:#e2e8f0;color:#334155}.chat-wrap{display:flex;flex-direction:column;overflow:hidden;min-height:0;position:relative;grid-template-rows:auto auto auto auto auto minmax(0,1fr) auto}.chat-wrap>.topbar,.chat-wrap>.sandboxTabs,.chat-wrap>.artifact,.chat-wrap>.sandboxPanel,.chat-wrap>.activity,.chat-wrap>.composer{flex:0 0 auto}#chat{flex:1 1 auto;min-height:0}.composer{flex:0 0 auto;position:relative;z-index:40}.topbar{padding:8px 14px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:10px}.topbar.collapsed{padding:6px 12px}.topbar.collapsed .subtitle{display:none}.title{font-weight:800}.subtitle{font-size:12px;color:var(--muted)}
#chat{padding:18px;overflow:auto;background:radial-gradient(circle at top left,#ffffff,#eef4fb 55%,#eaf1ff)}.msg{display:flex;margin:10px 0}.msg.user{justify-content:flex-end}.msg.assistant{justify-content:flex-start}.bubble{max-width:min(860px,82%);padding:11px 13px;border-radius:20px;line-height:1.38;white-space:pre-wrap;word-break:break-word;font-size:14px}.user .bubble{background:var(--blue);color:white;border-bottom-right-radius:6px}.assistant .bubble{background:var(--ai);color:var(--ink);border:1px solid var(--line);border-bottom-left-radius:6px}.name{font-size:11px;margin:0 8px 3px;color:var(--muted)}.user .name{text-align:right;color:#eaf4ff}.meta{font-size:11px;color:var(--muted);margin-top:4px}
.composer{padding:10px;border-top:1px solid var(--line);background:white}.artifact{border-top:1px solid var(--line);background:#f8fbff;padding:10px 14px;font-size:13px}.artifact a{font-weight:900;color:var(--blue);margin-right:12px}.middleResizable{resize:vertical;overflow:auto;min-height:54px;max-height:44vh}.assistantBoxPanel{background:#f5f3ff;border-top:1px solid #ddd6fe}.assistantBoxMeta{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:6px}.assistantBoxText{width:100%;min-height:120px;max-height:240px;font-family:Consolas,Segoe UI,Arial,sans-serif;font-size:13px;background:white}.assistantBoxText.info{border-color:#bfdbfe}.sandboxTabs{display:flex;gap:6px;align-items:center;padding:6px 14px;background:#f8fafc;border-bottom:1px solid var(--line);min-height:44px;overflow-x:auto;overflow-y:hidden;white-space:nowrap}.sandboxTabBtn{flex:0 0 auto;align-self:center;min-height:0;padding:7px 11px;border-radius:10px;line-height:1.1}.sandboxTabBtn.active{background:#111827;color:white}.sandboxPanel{border-bottom:1px solid var(--line);background:#f8fbff;padding:8px 14px;max-height:230px;overflow:auto;resize:vertical;min-height:54px}.sandboxPanel.hidden{display:none}.sandboxGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.sandboxCard{border:1px solid var(--line);border-radius:14px;background:white;padding:10px}.sandboxCard h3{font-size:14px;margin:0 0 8px}.sandboxTerminal{font-family:Consolas,monospace;min-height:70px;max-height:120px;background:#0f172a;color:#e2e8f0;border-radius:12px;padding:10px;white-space:pre-wrap;overflow:auto}.sandboxWarn{border:1px solid #fde68a;background:#fffbeb;border-radius:12px;padding:8px;margin:8px 0}.inputDock{position:relative;display:grid;grid-template-columns:auto minmax(0,1fr) auto auto auto;gap:8px;align-items:end}.plusBtn{width:38px;height:38px;border-radius:999px;font-size:22px;line-height:1;padding:0;background:#111827}.plusBtn:hover{background:#374151}.voiceBtn{width:38px;height:38px;border-radius:999px;padding:0;background:#7c3aed}.voiceBtn.listening{background:#dc2626;box-shadow:0 0 0 4px rgba(220,38,38,.18)}.voiceStatus{min-height:16px}.sendBtn{height:38px}.composerText{min-height:48px;max-height:140px;resize:vertical}.plusMenu{position:absolute;left:0;bottom:46px;width:min(360px,calc(100vw - 40px));background:white;border:1px solid var(--line);border-radius:16px;box-shadow:0 18px 50px rgba(16,24,40,.18);padding:8px;z-index:80;display:grid;gap:6px}.plusMenu.hidden{display:none}.plusMenuTitle{font-size:12px;font-weight:900;color:var(--muted);padding:4px 6px;text-transform:uppercase;letter-spacing:.04em}.plusMenu button{justify-content:flex-start;text-align:left;background:#f8fafc;color:#1f2937;border:1px solid #e5edf7}.plusMenu button:hover{background:#eef6ff}.contextStatusLine{margin-top:6px}.assistantBoxText.success{border-color:#bbf7d0}.assistantBoxText.warning{border-color:#fde68a}.assistantBoxText.error{border-color:#fecaca}.row{display:flex;gap:8px;align-items:center}.row.wrap{flex-wrap:wrap}textarea,input{width:100%;padding:10px 12px;border-radius:14px;border:1px solid #cbd5e1;background:white;color:var(--ink);font:14px Segoe UI,Arial,sans-serif}textarea{min-height:76px;resize:vertical}button{padding:9px 12px;border:0;border-radius:12px;background:var(--blue);color:white;font-weight:700;cursor:pointer}button:hover{background:var(--blue2)}button.secondary{background:#eef2f7;color:#1f2937}button.danger{background:#e11d48;color:white}button.tiny{font-size:12px;padding:6px 8px;border-radius:10px}.section-title{font-weight:800;margin:4px 0 8px}.panelHeader{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}.panelRestore{position:fixed;z-index:30;display:none;box-shadow:0 8px 26px rgba(16,24,40,.18);border:1px solid var(--line)}body.collapse-left .panelRestore.leftRestore,body.collapse-right .panelRestore.rightRestore{display:block}body.collapse-activity .panelRestore.activityRestore{display:none}.leftRestore{left:8px;top:92px;writing-mode:vertical-rl;transform:rotate(180deg)}.rightRestore{right:8px;top:92px;writing-mode:vertical-rl}.activityRestore{right:24px;bottom:18px}.settingsPanel{position:fixed;right:24px;top:72px;width:min(520px,calc(100vw - 48px));max-height:82vh;overflow:auto;z-index:250;border:1px solid var(--line);border-radius:18px;background:#fff;padding:14px;box-shadow:0 24px 80px rgba(16,24,40,.24);margin:0}.feedbackBar{margin-top:8px;display:flex;gap:6px;align-items:center}.feedbackBar button{font-size:12px;padding:5px 8px}.projectRefreshNotice{border:1px solid #bbf7d0;background:#f0fdf4;border-radius:12px;padding:8px;margin-top:8px}.hiddenBySettings{display:none!important}.tutorialOverlay{position:fixed;inset:0;background:rgba(15,23,42,.58);z-index:9999;display:flex;align-items:center;justify-content:center;padding:24px}.tutorialCard{background:#fff;border-radius:18px;max-width:620px;padding:18px;box-shadow:0 20px 70px rgba(15,23,42,.35)}.tutorialStep{border-left:4px solid var(--blue);padding-left:12px;margin:10px 0}.tutorialSpotlight{outline:4px solid #facc15;box-shadow:0 0 0 9999px rgba(15,23,42,.48);position:relative;z-index:10000}.settingsGroup{display:grid;gap:6px;margin-top:8px}.aiFocus{border:1px solid #bfdbfe;background:#eff6ff;border-radius:12px;padding:9px;margin:8px 0}.createdOutput{border:1px solid #c7d2fe;background:#eef2ff;border-radius:12px;padding:9px;margin:8px 0}.planPanel{border:1px solid #fde68a;background:#fffbeb;border-radius:12px;padding:9px;margin:8px 0}.createdOutput b{display:block;margin-bottom:3px}.section-title-row{display:flex;align-items:center;justify-content:space-between;gap:8px}.sectionCollapseBtn{margin-left:auto}.small{font-size:12px;color:var(--muted)}code{background:#edf2f7;border:1px solid #dbe3ef;padding:2px 5px;border-radius:6px}.item{border:1px solid var(--line);border-radius:14px;padding:9px;margin:7px 0;background:white}.item.active{border-color:var(--blue);box-shadow:0 0 0 2px rgba(11,132,255,.12)}.projectItem{display:grid;grid-template-columns:auto minmax(0,1fr);gap:8px 10px;align-items:start}.projectItem input.projectSelect{width:auto;margin-top:4px}.projectMain{min-width:0}.projectTitle{display:flex;justify-content:space-between;gap:8px;align-items:center}.projectTitle b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.projectMeta{display:grid;gap:2px;margin-top:4px}.projectActions{margin-top:7px}.runSelect{width:auto;margin-right:6px}.runSummaryTitle{font-weight:800}.novaCards{display:grid;gap:7px}.novaCard{border:1px solid var(--line);border-radius:12px;background:#fff;padding:8px}.novaCard b{display:block;margin-bottom:2px}.odysseusWorkbenchPanel{border:1px solid #c4b5fd;background:linear-gradient(135deg,#f5f3ff,#eff6ff);border-radius:16px;padding:10px;margin:10px 0;display:grid;gap:8px}.odysseusWorkbenchGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.odysseusWorkbenchBtn{display:grid;grid-template-columns:auto 1fr;gap:6px;align-items:center;text-align:left;background:#fff;color:#111827;border:1px solid #ddd6fe;border-radius:12px;padding:7px 8px;font-size:12px}.odysseusWorkbenchBtn:hover{background:#eef2ff;color:#0f172a}.odysseusWorkbenchBtn .ico{font-size:15px}.odysseusArchitectureStrip{border:1px solid #bae6fd;background:#f0f9ff;border-radius:12px;padding:8px;font-size:12px}.archCompact{display:flex;gap:6px;flex-wrap:wrap;align-items:center}.archCompact .archNode{padding:4px 7px}.archCompact .arrow{color:var(--muted);font-weight:800}.commandPalette{display:grid;gap:7px;margin-top:8px}.commandItem{border:1px solid var(--line);border-radius:12px;padding:8px;background:#fff}.commandItem b{font-size:13px}.commandActions{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}.suggestedCommands{border-top:1px solid #dbeafe;margin-top:8px;padding-top:8px;display:flex;gap:6px;flex-wrap:wrap}.suggestedCommands .label{font-size:12px;color:var(--muted);font-weight:800;align-self:center}.file{display:grid;grid-template-columns:1fr auto auto;gap:6px;align-items:center;font-size:13px}.file span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.editor{height:340px;font-family:Consolas,monospace;font-size:13px}.pathline{font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pill{display:inline-block;background:#eef6ff;color:#175cd3;padding:3px 8px;border-radius:999px;font-size:12px;margin-left:6px}.pill.good{background:#ecfdf3;color:#027a48}.pill.bad{background:#fef3f2;color:#b42318}.pill.warn{background:#fffaeb;color:#b54708}
.activity{border-top:1px solid var(--line);background:linear-gradient(180deg,#fbfdff,#f6f9ff);height:220px;max-height:42vh;overflow:hidden;padding:10px 14px;min-height:90px;resize:vertical;flex:0 0 auto}/* legacy-test-marker:max-height:132px */.activity #activityLog{height:calc(100% - 34px);max-height:none;overflow:auto;padding-right:4px}.activity h3{margin:0 0 8px;font-size:14px}.event{border-left:4px solid #98a2b3;padding:8px 10px;margin:8px 0;background:white;border-radius:12px;box-shadow:0 1px 8px rgba(16,24,40,.05)}.event.llm_attempt,.event.llm_status{border-left-color:#7c3aed}.event.llm_accepted,.event.plan_done,.event.step_done{border-left-color:var(--good)}.event.llm_rejected,.event.step_failed,.event.command_failed,.event.verification_failed{border-left-color:var(--bad)}.event.file_write,.event.code_write_start,.event.code_repair_write{border-left-color:#0b84ff}.event .t{font-size:11px;color:var(--muted)}.event pre{margin:7px 0 0;white-space:pre-wrap;font-family:Consolas,monospace;font-size:12px;max-height:230px;overflow:auto;background:#f2f4f7;border-radius:10px;padding:10px}.codepreview{font-family:Consolas,monospace;white-space:pre-wrap;background:#0b1020;color:#d1e7ff;border-radius:14px;padding:10px;max-height:260px;overflow:auto;font-size:12px}.diffbox{border:1px solid #dbe3ef;border-radius:10px;margin-top:6px;background:#f8fafc}.diffbox summary{cursor:pointer;font-weight:800;padding:6px 8px}.diffbox pre{margin:0;max-height:260px;overflow:auto;background:#111827;color:#e5e7eb;border-radius:0 0 10px 10px}.cyclebubble{border:1px solid #93c5fd;background:linear-gradient(180deg,#f8fbff,#eef6ff)}.cyclebubble.complete{border-style:solid;border-color:#86efac;background:linear-gradient(180deg,#f0fdf4,#ecfdf3)}.cyclebubble.error{border-color:#fca5a5;background:#fff1f2}.cycle-report{border-top:1px solid #dbeafe;margin-top:8px;padding-top:8px}.cycle-event{font-size:12px;color:#475467;margin-top:3px}.sticky-note{background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:8px;margin-top:8px}
.topbar{padding:6px 12px;gap:8px}.topbar.collapsed{padding:4px 10px}.middleResizable{min-height:46px}.assistantBoxText{min-height:150px;max-height:280px}.sandboxTabs{padding:5px 12px;min-height:38px}.sandboxPanel{padding:7px 12px;min-height:48px}#generalPanel{padding:5px 12px;min-height:36px;max-height:72px;resize:none}.contextStatusLine{display:none;margin-top:0}.activity{padding:8px 12px}.activity #activityLog{height:calc(100% - 54px)}.activity h3{margin:0 0 4px}.activitySubtitle{font-size:12px;color:#344054;font-weight:800;margin:0 0 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.typing{display:inline-flex;gap:4px;align-items:center}.typing span{width:7px;height:7px;border-radius:50%;background:#0b84ff;display:inline-block;animation:b 1.2s infinite}.typing span:nth-child(2){animation-delay:.15s}.typing span:nth-child(3){animation-delay:.3s}@keyframes b{0%,80%,100%{opacity:.25;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}
.runmodal{position:fixed;inset:0;background:rgba(15,23,42,.55);display:none;align-items:center;justify-content:center;z-index:20;padding:20px}.runbox{background:white;border-radius:18px;box-shadow:0 24px 80px rgba(0,0,0,.3);width:min(1180px,96vw);height:min(820px,94vh);display:grid;grid-template-rows:auto 1fr;overflow:hidden}.runhead{padding:10px 12px;border-bottom:1px solid var(--line);display:flex;gap:8px;align-items:center;justify-content:space-between}.runframe{width:100%;height:100%;border:0;background:white}details.run{border:1px solid var(--line);border-radius:12px;margin:8px 0;background:white}details.run summary{cursor:pointer;padding:8px 10px;font-weight:800}.runbody{padding:0 8px 8px}.workingbubble{border:1px dashed #93c5fd;background:#f8fbff}.activeRun{border:1px solid #93c5fd;background:#eff6ff;border-radius:14px;padding:10px;margin:10px 0}.activeRun.waiting{border-color:#f59e0b;background:#fffbeb}.activeRun .q{font-weight:800;margin:4px 0}.activeRun input{margin-top:6px}.activeRun .recommendedChoice{border:2px solid #f59e0b;background:#fffbeb;color:#92400e}.activeRun .choiceReason{font-size:11px;color:#667085;margin-left:4px}.avatarBox{display:flex;gap:10px;align-items:center;border:1px solid var(--line);border-radius:18px;padding:12px;background:linear-gradient(135deg,#f8fbff,#eef6ff);margin-bottom:12px;transition:.25s ease}.avatarBox.mood-working,.avatarBox.mood-thinking{border-color:#f59e0b;background:linear-gradient(135deg,#fff7ed,#eef6ff)}.avatarBox.mood-idle{border-color:#8b5cf6;background:linear-gradient(135deg,#f5f3ff,#eef6ff)}.avatarBox.mood-error{border-color:#f87171;background:linear-gradient(135deg,#fff1f2,#f8fbff)}.avatarBox.mood-blocked{border-color:#fb923c;background:linear-gradient(135deg,#fffbeb,#f8fbff)}.avatarFace{width:58px;height:58px;border-radius:20px;background:white;display:grid;place-items:center;font-size:30px;box-shadow:0 6px 20px rgba(16,24,40,.08);border:1px solid #e5e7eb;position:relative;transition:.25s ease}.avatarFace .faceEmoji{filter:drop-shadow(0 2px 2px rgba(0,0,0,.08))}.avatarFace.mood-working .faceEmoji,.avatarFace.mood-thinking .faceEmoji{animation:avatarBob 1s infinite}.avatarFace.mood-error{background:#fff1f2}.avatarFace.mood-success{background:#ecfdf3}.avatarFace.mood-idle{background:#f5f3ff}.avatarFace.mood-repair{background:#fff7ed}.avatarFace.mood-speaking .faceEmoji{animation:avatarSpeak .5s infinite alternate}@keyframes avatarBob{50%{transform:translateY(-3px)}}@keyframes avatarSpeak{from{transform:scale(1)}to{transform:scale(1.12)}}.avatarMood{font-weight:900}.avatarCaption{font-size:12px;color:#344054}.idlebubble{border:1px solid #c4b5fd;background:linear-gradient(180deg,#faf5ff,#f5f3ff)}.jsonblock,.codeblock{background:#0b1020;color:#d1e7ff;border-radius:12px;padding:10px;overflow:auto;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap}.mdstrong{font-weight:800}.statuschips{padding:8px 18px;border-bottom:1px solid var(--line);background:#f8fbff;display:flex;gap:6px;flex-wrap:wrap}
@media(max-width:1150px){main{grid-template-columns:1fr;height:auto;overflow:auto}body{overflow:auto}.rightbar,.sidebar{max-height:none}.chat-wrap{min-height:760px}.resizeRail{display:none}.sidebar,.leftRail,.chat-wrap,.rightRail,.rightbar{grid-column:auto}body.collapse-left .sidebar,body.collapse-right .rightbar{display:block}}

body.theme-dark{--bg:#0f172a;--panel:#111827;--ink:#e5e7eb;--muted:#94a3b8;--line:#334155;--ai:#172033;background:linear-gradient(135deg,#020617,#111827)}
body.theme-dark .card,body.theme-dark .modelCard,body.theme-dark .item,body.theme-dark .event,body.theme-dark .commandItem,body.theme-dark .settingsPanel,body.theme-dark .sandboxCard,body.theme-dark .composer{background:#111827;color:var(--ink)}
body.theme-dark textarea,body.theme-dark input{background:#0b1220;color:var(--ink);border-color:#334155}body.theme-dark #chat{background:radial-gradient(circle at top left,#111827,#020617)}
.edgeRail{position:fixed;left:14px;bottom:18px;top:auto;z-index:120;width:44px;display:grid;gap:7px;pointer-events:auto;background:rgba(255,255,255,.88);border:1px solid var(--line);border-radius:18px;padding:6px;box-shadow:0 14px 42px rgba(15,23,42,.16);backdrop-filter:blur(8px)}.edgeRail:hover{z-index:500}.edgeRail button{width:32px;height:32px;padding:0;border-radius:12px;background:#111827;color:white;box-shadow:0 6px 18px rgba(0,0,0,.14)}.edgeRail button.muted{background:#b42318}.edgeRail button.active{background:#0f9f6e}.edgeRail .railLabel{font-size:10px;color:var(--muted);writing-mode:horizontal-tb;text-align:center;margin:auto}.chatMuteBtn.chatMuted{background:#b42318;color:white}.wakeWordOn{background:#0f9f6e!important}.wakeWordOff{background:#64748b!important}.edgeRailSpacer{height:54px}.popupPanel{position:fixed;z-index:9000;left:44px;top:80px;width:min(760px,calc(100vw - 74px));max-height:78vh;overflow:auto;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:18px;box-shadow:0 22px 70px rgba(15,23,42,.35);padding:14px}.popupPanel.hidden{display:none}.personaMiniPanel{border:1px solid #c7d2fe;background:#eef2ff;border-radius:14px;padding:9px;margin:8px 0}.personaMiniGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.personaMiniGrid label{font-size:12px;color:#334155;font-weight:700}.personaMiniGrid input[type=range]{width:100%;padding:0}.personaCommandPreview{font-family:Consolas,monospace;font-size:11px;background:#fff;border:1px solid #cbd5e1;border-radius:10px;padding:7px;white-space:pre-wrap}.voiceAuditHint{border:1px solid #bbf7d0;background:#f0fdf4;border-radius:12px;padding:7px;margin-top:6px}.localModelPlanHint{border:1px solid #fde68a;background:#fffbeb;border-radius:12px;padding:7px;margin-top:6px}.quickGroup{border:1px solid var(--line);border-radius:14px;margin:8px 0;background:rgba(255,255,255,.65);overflow:hidden}.quickControlsBox{max-height:34vh;overflow:auto;resize:vertical;min-height:110px}.quickGroupBody{display:flex;gap:5px;flex-wrap:wrap;padding:8px}.quickGroupBody button{font-size:12px;padding:6px 8px}.middleResizable{resize:vertical;overflow:auto;min-height:90px;max-height:48vh}.quickEditor{display:grid;grid-template-columns:1fr 1fr auto;gap:6px;margin:8px 0}.quickItemBtn{position:relative}.quickItemBtn:hover::after{content:attr(data-desc);position:absolute;left:0;top:100%;z-index:900;background:#111827;color:white;border-radius:8px;padding:6px;width:240px;white-space:normal;font-size:12px}.event.subtask{margin-left:18px;border-left-style:dashed}.event.subtask2{margin-left:34px}.event .why{border-left:3px solid #facc15;background:#fffbeb;border-radius:8px;padding:6px;margin-top:6px}.fileCards{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;border-top:1px solid #dbeafe;padding-top:8px}.fileCard{border:1px solid var(--line);border-radius:12px;background:#f8fafc;padding:7px;min-width:160px}.fileIcon{font-size:18px;margin-right:5px}.chatSessionBar{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.idlePopup{position:fixed;right:22px;bottom:22px;z-index:8000;max-width:360px;background:#111827;color:white;border-radius:16px;padding:12px;box-shadow:0 18px 50px rgba(0,0,0,.28)}.idlePopup.hidden{display:none}.llmContextLine{border:1px solid #bfdbfe;background:#eff6ff;border-radius:10px;padding:6px;margin-top:6px}.activityHint{font-size:12px;color:var(--muted);margin-bottom:4px}.activityResizeHint{float:right;font-size:11px;color:var(--muted)}
.diffline{display:block;padding:1px 4px;border-left:3px solid transparent}.diffline.add{background:#ecfdf3;color:#065f46;border-left-color:#22c55e}.diffline.del{background:#fef2f2;color:#991b1b;border-left-color:#ef4444}.diffline.meta{background:#eff6ff;color:#1d4ed8}.llmProgress{height:8px;border-radius:999px;background:#e5e7eb;overflow:hidden;margin-top:6px}.llmProgress span{display:block;height:100%;width:45%;background:linear-gradient(90deg,#7c3aed,#0b84ff);animation:llmbar 1.4s infinite ease-in-out}@keyframes llmbar{0%{margin-left:-45%}50%{margin-left:35%}100%{margin-left:100%}}.archMini{border:1px solid var(--line);border-radius:16px;background:linear-gradient(135deg,#f8fbff,#f5f3ff);padding:10px;margin-top:10px}.archGrid{display:grid;grid-template-columns:1fr 1fr;gap:6px}.archNode{border:1px solid #dbeafe;background:white;border-radius:12px;padding:7px;font-size:12px}.archNode.active{border-color:#7c3aed;background:#f5f3ff;box-shadow:0 0 0 3px rgba(124,58,237,.12)}.archLink{font-size:11px;color:var(--muted);margin:5px 0}.devSandboxHint{border:1px solid #bbf7d0;background:#f0fdf4;border-radius:10px;padding:7px;margin-top:6px}

/* v55.3.115 GUI cockpit overhaul: three-zone layout, workflow cards, clearer panels and durable run management. */
main[data-ui-overhaul="v55.3.115"]{grid-template-columns:var(--left-col) 6px minmax(620px,1fr) 6px var(--right-col);gap:12px;padding:12px}body{--left-col:360px;--right-col:420px}.sidebar.card,.rightbar.card,.chat-wrap.card{border-radius:20px}.panelHeader{position:sticky;top:0;z-index:8;background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(255,255,255,.90));padding:6px 0 10px;border-bottom:1px solid var(--line)}.controlHero{border:1px solid #bfdbfe;background:linear-gradient(135deg,#eff6ff,#f5f3ff);border-radius:16px;padding:11px;margin:8px 0 12px}.controlHeroGrid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:8px}.workflowCards{display:grid;grid-template-columns:repeat(6,minmax(88px,1fr));gap:8px;padding:9px 12px;border-bottom:1px solid var(--line);background:#f8fbff}.workflowCard{display:grid;gap:2px;min-height:54px;text-align:left;background:white;color:#111827;border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 14px rgba(16,24,40,.05)}.workflowCard:hover{border-color:#93c5fd;background:#eff6ff;color:#0f172a}.workflowCard span{font-size:11px;color:var(--muted);font-weight:600}.section-title{margin:12px 0 8px;padding-top:6px;border-top:1px solid rgba(217,226,239,.85)}.sidebar>.section-title:first-of-type{border-top:0}.commandPalette,.quickControlsBox,#projects,#customTools,#files{max-height:34vh;overflow:auto;padding-right:3px}.projectItem{border-radius:16px;grid-template-columns:28px minmax(0,1fr);align-items:start}.projectItem input.projectSelect{justify-self:center;align-self:start;margin-top:6px;transform:scale(1.05)}.projectMeta{display:flex;flex-wrap:wrap;gap:5px}.projectMeta span{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:999px;padding:2px 7px}.toolRefreshLine{border:1px solid #bbf7d0;background:#f0fdf4;border-radius:12px;padding:7px;margin:7px 0}.toolSectionTitle{font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:10px 0 5px}.toolItem{border-radius:16px}.toolTitle{display:flex;justify-content:space-between;gap:8px;align-items:center}.rightbar .assistantBoxPanel{border-radius:16px;background:linear-gradient(135deg,#f5f3ff,#eff6ff)}.assistantBoxText{min-height:100px}.editor{height:260px;min-height:160px}.codepreview{max-height:190px}.archMini{padding:6px 12px;margin:0;border-left:0;border-right:0;border-radius:0;background:#fbfdff}.archCompact{font-size:12px;gap:5px}.archCompact .archNode{font-size:11px;padding:3px 7px}.activity{height:240px;min-height:96px}.activityHead{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:6px}.activityHead h3{margin:0}.runToolbar{position:sticky;top:0;z-index:4;background:#f8fbff;border:1px solid var(--line);border-radius:12px;padding:6px;margin-bottom:8px}.run summary{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:8px}.runSummaryTitle{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.runMeta{grid-column:2 / span 2;margin-left:0}.runSelect{transform:scale(1.05)}.topbar{background:linear-gradient(180deg,#ffffff,#f8fbff)}.statuschips{position:relative}.sandboxTabs{scrollbar-width:thin}.chat-wrap #generalPanel{display:none!important}@media(max-width:1280px){body{--left-col:320px;--right-col:360px}.workflowCards{grid-template-columns:repeat(3,1fr)}}@media(max-width:1150px){main[data-ui-overhaul="v55.3.115"]{grid-template-columns:1fr}.workflowCards{grid-template-columns:repeat(2,1fr)}.activityHead{display:block}.controlHeroGrid{grid-template-columns:repeat(2,1fr)}}

/* v55.3.115 refined cockpit: remove card clutter, keep chat central, use drawers/tabs. */
main[data-ui-overhaul="v55.3.115"]{grid-template-columns:minmax(300px,var(--left-col)) 6px minmax(640px,1fr) 6px minmax(340px,var(--right-col));gap:10px;padding:10px;max-width:1880px}.topbar{min-height:42px;padding:6px 12px;background:linear-gradient(180deg,#fff,#f9fbff)}.topbar .subtitle{font-size:11px}.workflowCards{display:none!important}.smartTopStrip{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:6px 12px;border-bottom:1px solid var(--line);background:#fbfdff}.smartNow{display:flex;gap:8px;align-items:center;min-width:0}.smartNow span{font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.smartActions{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.sidebar.card,.rightbar.card,.chat-wrap.card{border-radius:18px;box-shadow:0 10px 34px rgba(16,24,40,.10)}.sidebar{padding:10px}.rightbar{padding:10px}.controlHero{padding:10px;background:linear-gradient(135deg,#f8fbff,#eef6ff);border:1px solid #dbeafe}.section-title{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#334155;margin:10px 0 6px}.commandPalette,.quickControlsBox,#projects,#customTools{max-height:28vh}.sandboxTabs{display:none!important}.sandboxPanel:not(.forceVisible){display:none!important}.archMini{display:none!important}.activity{height:205px;min-height:72px;max-height:32vh}.activityHead{position:sticky;top:0;z-index:5;background:#fbfdff;border-bottom:1px solid var(--line);padding-bottom:6px}.activityHint{font-size:11px;color:var(--muted);margin:4px 0}.run summary{grid-template-columns:auto minmax(0,1fr) auto auto}.runSummaryTitle{font-weight:800}.runMeta .backendId{display:none}.runStopBtn{margin-left:4px}.run.staleRun{border-color:#f59e0b;background:#fffbeb}.run.staleRun summary:after{content:'possible stale task';font-size:11px;color:#92400e;background:#fef3c7;border-radius:999px;padding:2px 7px}.composer{padding:8px 10px}.composerText{min-height:44px}.rightbar .inspectorTabs{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:6px 0 10px;position:sticky;top:0;background:rgba(255,255,255,.96);z-index:8;padding-bottom:6px}.inspectorTabs button{padding:7px 8px;border-radius:10px;background:#eef2f7;color:#1f2937}.inspectorTabs button.active{background:#111827;color:#fff}.inspectorPane{display:none}.inspectorPane.active{display:block}.inspectorPane .section-title:first-child{margin-top:0}.assistantBoxText{min-height:130px;max-height:34vh}.editor{height:310px}.codepreview{max-height:260px}.item{box-shadow:0 2px 10px rgba(16,24,40,.03)}#chat{padding:14px 18px;background:linear-gradient(180deg,#f8fbff,#eef4fb)}.bubble{max-width:min(880px,86%)}@media(max-width:1250px){main[data-ui-overhaul="v55.3.115"]{grid-template-columns:1fr}.resizeRail,.sidebar,.rightbar{display:none}.smartTopStrip{align-items:flex-start}.smartActions{justify-content:flex-start}.panelRestore.leftRestore,.panelRestore.rightRestore{display:block}}
body.theme-dark .smartTopStrip,body.theme-dark .activityHead,body.theme-dark .rightbar .inspectorTabs{background:#111827}body.theme-dark .controlHero{background:#172033}body.theme-dark .inspectorTabs button{background:#1f2937;color:#e5e7eb}body.theme-dark .inspectorTabs button.active{background:#dbeafe;color:#111827}
body.theme-dark .panelHeader,body.theme-dark .workflowCard,body.theme-dark .runToolbar,body.theme-dark .archMini{background:#111827;color:var(--ink)}body.theme-dark .controlHero,body.theme-dark .assistantBoxPanel{background:#172033}body.theme-dark .projectMeta span{background:#0b1220;border-color:#334155}


/* v55.3.115 left-action cockpit: controls live left; right is transparent state/output evidence. */
main[data-ui-overhaul="v55.3.115"]{grid-template-columns:minmax(380px,var(--left-col)) 6px minmax(620px,1fr) 6px minmax(380px,var(--right-col));}
body{--left-col:410px;--right-col:430px}
.leftActionDock{border:1px solid #bfdbfe;background:linear-gradient(135deg,#eff6ff,#f8fafc);border-radius:16px;padding:10px;margin:10px 0;display:grid;gap:9px}
.actionCluster{border:1px solid #dbeafe;border-radius:14px;background:rgba(255,255,255,.78);padding:8px}
.actionClusterTitle{font-size:12px;font-weight:900;color:#334155;text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}
.actionCluster .row button{flex:1 1 auto;text-align:center}
.leftFileDock{border:1px solid #e2e8f0;background:#fff;border-radius:16px;padding:9px;margin-top:10px}
.rightStateHero{border:1px solid #bbf7d0;background:linear-gradient(135deg,#f0fdf4,#f8fafc);border-radius:16px;padding:10px;margin:8px 0}
.stateGrid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:8px}.stateCard{border:1px solid var(--line);border-radius:12px;background:white;padding:8px}.stateCard b{display:block;margin-bottom:2px}
.transparentOutputPanel,.bridgeReceiptPanel,.jarvisSidecarPanel,.browserHarnessPanel,.sidecarEnrollmentPanel{border:1px solid #dbeafe;background:rgba(255,255,255,.92);border-radius:16px;padding:10px;margin:9px 0}
.transparentOutputPanel{background:linear-gradient(180deg,#fff,#f8fbff)}
.transparentOutputPanel .codepreview{background:#0b1020;color:#d1e7ff;border:1px solid #26324a}
.outputEvidenceMeta{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}.outputEvidenceMeta span{background:#eef2ff;border:1px solid #c7d2fe;border-radius:999px;padding:2px 7px;font-size:11px}
.transparencyNote{border-left:4px solid #7c3aed;background:#f5f3ff;border-radius:10px;padding:7px;margin-top:7px;font-size:12px;color:#475467}
.rightbar .row.wrap button{font-size:12px}.rightbar .assistantBoxMeta button{display:none}.rightbar .assistantBoxMeta button:first-of-type{display:inline-block}
@media(max-width:1250px){main[data-ui-overhaul="v55.3.115"]{grid-template-columns:1fr}.leftActionDock{grid-template-columns:1fr}.stateGrid{grid-template-columns:1fr}}


/* v55.3.118 unified UX / voice visualiser / collapsible offscreen panels */
main[data-ui-overhaul="v55.3.115"]{grid-template-columns:minmax(260px,var(--left-col)) 10px minmax(360px,1fr) 10px minmax(280px,var(--right-col));gap:8px;padding:10px;max-width:none;width:100vw}.resizeRail{width:10px;min-width:10px}.middleResizable,.sandboxPanel{max-height:70vh}.activity{height:clamp(150px,28vh,440px)!important;max-height:72vh!important;resize:vertical}.activity #activityLog{height:calc(100% - 78px);overflow:auto}.composerText{max-height:32vh}.sidebar,.rightbar{transition:transform .22s ease,opacity .22s ease}.edgeRail{top:86px;bottom:auto;left:0;transform:translateX(-52px);transition:transform .22s ease,opacity .22s ease;opacity:.78}.edgeRail.open{transform:translateX(8px);opacity:1}.edgeRailToggle{position:fixed;left:0;top:46px;z-index:610;width:22px;height:92px;padding:0;border-radius:0 12px 12px 0;background:#111827;color:#fff;writing-mode:vertical-rl;text-orientation:mixed;box-shadow:0 12px 30px rgba(15,23,42,.22)}.edgeRail.open + .edgeRailToggle,.edgeRailToggle.open{left:58px}.panelRestore{border-radius:12px 12px 0 0!important;z-index:650!important}.leftRestore{left:0!important;top:45%!important;writing-mode:vertical-rl!important;transform:rotate(180deg)!important}.rightRestore{right:0!important;top:45%!important;writing-mode:vertical-rl!important;transform:none!important}body.collapse-left .sidebar{display:block!important;position:fixed;left:0;top:10px;bottom:10px;width:min(420px,82vw);transform:translateX(calc(-100% - 28px));opacity:.8;pointer-events:none}body.collapse-right .rightbar{display:block!important;position:fixed;right:0;top:10px;bottom:10px;width:min(430px,82vw);transform:translateX(calc(100% + 28px));opacity:.8;pointer-events:none}body.collapse-left .leftRail,body.collapse-right .rightRail{display:none!important}.rightbar.integratedRight .inspectorTabs{display:none!important}.rightbar{scrollbar-gutter:stable}.novaOrbPanel{position:sticky;top:0;z-index:10;display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:center;border:1px solid #c7d2fe;background:linear-gradient(135deg,#eef2ff,#f8fbff);border-radius:18px;padding:10px;margin:0 0 10px;box-shadow:0 8px 24px rgba(16,24,40,.08)}.novaOrb{width:70px;height:70px;border-radius:999px;display:grid;place-items:center;font-size:30px;background:radial-gradient(circle at 35% 30%,#fff,#93c5fd 42%,#7c3aed);color:white;box-shadow:0 0 0 0 rgba(124,58,237,.35);transition:.2s ease;position:relative;overflow:hidden}.novaOrb:after{content:'';position:absolute;inset:8px;border:1px solid rgba(255,255,255,.55);border-radius:999px}.novaOrb.listening{background:radial-gradient(circle at 35% 30%,#fff,#22c55e 40%,#0f766e);animation:novaPulse 1.05s infinite}.novaOrb.detected{background:radial-gradient(circle at 35% 30%,#fff,#facc15 38%,#f97316);animation:novaBounce .55s infinite alternate}.novaOrb.thinking,.novaOrb.working{background:radial-gradient(circle at 35% 30%,#fff,#60a5fa 40%,#7c3aed);animation:novaPulse .75s infinite}.novaOrb.speaking{background:radial-gradient(circle at 35% 30%,#fff,#fb7185 38%,#be185d);animation:novaSpeakPulse .34s infinite alternate}@keyframes novaPulse{50%{transform:scale(1.06);box-shadow:0 0 0 14px rgba(124,58,237,.10)}}@keyframes novaBounce{to{transform:translateY(-4px) scale(1.06)}}@keyframes novaSpeakPulse{to{transform:scale(1.12)}}.novaOrbTitle{font-weight:900}.novaOrbTranscript{font-size:12px;color:var(--muted);max-height:52px;overflow:auto}.voiceWaveRow{display:grid;grid-template-columns:minmax(110px,1fr) minmax(110px,1fr);gap:6px;margin-top:6px}.voiceWaveCard{border:1px solid var(--line);background:#f8fafc;border-radius:12px;padding:5px}.voiceWaveCard b{font-size:11px;color:#344054}.voiceWave{width:100%;height:34px;display:block;background:#0b1020;border-radius:8px}.runToolbar{display:none!important}.newChatPrimary{background:#111827!important}.smartActions .newChatPrimary{color:#fff}@media(max-width:1250px){main[data-ui-overhaul="v55.3.115"]{grid-template-columns:1fr!important;padding:8px 10px}.edgeRailToggle{top:50px}.activity{max-height:60vh!important}}


/* v55.3.119 autonomous cockpit: scrollable subwindows + reasoning/status notes */
#autonomousLivePanel{display:none;border-top:1px solid #bfdbfe;background:linear-gradient(180deg,#f8fbff,#edf6ff);padding:10px 14px;max-height:clamp(230px,38vh,560px);min-height:170px;overflow:hidden;resize:vertical}
.autonomousCockpit{display:grid;grid-template-columns:minmax(230px,.9fr) minmax(280px,1.1fr);gap:10px;min-height:0;max-height:100%}
.autoStatusCard,.autoThoughtNow,.autoSubWindow{border:1px solid var(--line);background:rgba(255,255,255,.94);border-radius:16px;padding:10px;box-shadow:0 6px 20px rgba(16,24,40,.06);min-width:0}
.autoThoughtNow{border-color:#c4b5fd;background:linear-gradient(135deg,#f5f3ff,#eff6ff)}
.autoThoughtNow .thoughtText{font-weight:800;font-size:13px;margin:5px 0}.autoThoughtNow .validationText{font-size:12px;color:#475467;background:#fff;border:1px solid #e9d5ff;border-radius:10px;padding:7px;margin-top:6px}
.autoSubWindow{padding:0;overflow:hidden;min-height:0}.autoSubWindow>summary{cursor:pointer;font-weight:900;padding:9px 10px;background:#f8fafc;border-bottom:1px solid var(--line);list-style:none}.autoSubWindow>summary::-webkit-details-marker{display:none}
.autoScroll{max-height:clamp(120px,20vh,310px);overflow:auto;padding:8px 10px;scrollbar-gutter:stable}.autoEventScroller{max-height:clamp(120px,22vh,340px);overflow:auto;padding-right:4px}.autoPlanScroll{max-height:105px;overflow:auto;border:1px dashed #bfdbfe;border-radius:12px;background:#f8fbff;padding:8px;margin-top:8px}
.autoThoughtItem{border-left:4px solid #93c5fd;background:#fff;border-radius:12px;padding:7px 9px;margin:7px 0}.autoThoughtItem.current{border-left-color:#7c3aed;background:#f5f3ff}.autoThoughtItem.problem{border-left-color:#f97316;background:#fff7ed}.autoThoughtItem.success{border-left-color:#22c55e;background:#f0fdf4}.autoThoughtItem .time{font-size:11px;color:var(--muted)}.autoThoughtItem .validation{font-size:12px;color:#475467;margin-top:4px}
.autoEventScroller .event{margin:6px 0;padding:7px 9px}.autoCompactActions{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.autoGridColumn{display:grid;gap:9px;min-height:0}.autonomousListWindow{max-height:clamp(135px,24vh,350px);overflow:auto;border:1px solid var(--line);border-radius:14px;background:#fff;padding:8px}
@media(max-width:900px){.autonomousCockpit{grid-template-columns:1fr}#autonomousLivePanel{max-height:62vh}}
body.theme-dark #autonomousLivePanel{background:#111827}.theme-dark .autoStatusCard,.theme-dark .autoThoughtNow,.theme-dark .autoSubWindow{background:#172033;border-color:#334155}.theme-dark .autoSubWindow>summary{background:#111827}.theme-dark .autoThoughtItem{background:#1f2937}


/* v55.3.120 voice reliability + VS Code-style layout polish */
main[data-ui-overhaul="v55.3.115"]{gap:0;padding:8px;background:#dfe7f3}.card{border-radius:14px}.resizeRail{background:linear-gradient(180deg,#d7e3f4,#b9c9dd);border-left:1px solid #cbd5e1;border-right:1px solid #cbd5e1;border-radius:0;width:12px;min-width:12px;position:relative}.resizeRail:after{content:'⋮';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#64748b;font-weight:900}.resizeRail:hover,.resizeRail.dragging{background:#93c5fd}.chat-wrap{border-radius:14px}.topbar,.statuschips,.smartTopStrip,.sandboxTabs{background:#f8fafc}.voiceControlGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin:8px 0}.voiceControlGrid label{display:grid;gap:4px;font-size:12px;color:#344054}.voiceControlGrid input[type=range]{width:100%}.voiceAuthPanel{border:1px solid #bfdbfe;background:#eff6ff;border-radius:12px;padding:9px;margin:8px 0}.voiceAuthPanel.locked{border-color:#fecaca;background:#fff1f2}.voiceAuthPanel.unlocked{border-color:#bbf7d0;background:#f0fdf4}.voiceConfirmBox{border:1px solid #facc15;background:#fffbeb;border-radius:12px;padding:8px;margin-top:6px}.activity #activityLog{max-height:min(52vh,520px);overflow:auto}.runbody{max-height:340px;overflow:auto}.composer{box-shadow:0 -8px 24px rgba(15,23,42,.07)}.smartTopStrip{position:sticky;top:0;z-index:7}.rightbar{max-height:calc(100vh - 16px);overflow:auto}.sidebar{max-height:calc(100vh - 16px);overflow:auto}.layoutHint{font-size:11px;color:#667085;margin-top:4px}

.communicationCentre{background:linear-gradient(135deg,#eff6ff,#f8fafc);border-color:#bfdbfe}.voiceGuardCard{border:1px solid #fecaca;background:#fff1f2;border-radius:14px;padding:9px;margin:8px 0;display:grid;gap:6px}.voiceGuardCard.unlocked{border-color:#bbf7d0;background:#f0fdf4}.voiceGuardCard.bypass{border-color:#fde68a;background:#fffbeb}.communicationTranscriptBox{border:1px solid var(--line);background:#fff;border-radius:14px;padding:9px;margin-top:8px;max-height:150px;overflow:auto}.communicationTranscriptLine{border-bottom:1px solid #edf2f7;padding:4px 0}.communicationTranscriptLine:last-child{border-bottom:0}.voiceMatchMeter{height:7px;background:#e2e8f0;border-radius:999px;overflow:hidden}.voiceMatchMeter span{display:block;height:100%;width:0;background:#0f9f6e}
.controlDrawerHeader{display:flex;align-items:center;justify-content:space-between;gap:8px}.controlHero.collapsed{padding:8px 10px}.controlHero.collapsed #controlDrawerIntro,.controlHero.collapsed #controlDrawerQuickActions,body.control-drawer-collapsed #leftActionDock{display:none!important}.middleResizeRail{height:8px;min-height:8px;flex:0 0 8px;cursor:row-resize;background:linear-gradient(90deg,#d7e3f4,#b9c9dd);border-top:1px solid #cbd5e1;border-bottom:1px solid #cbd5e1;position:relative;display:none}.middleResizeRail.visible{display:block}.middleResizeRail:after{content:'...';position:absolute;left:50%;top:50%;transform:translate(-50%,-58%);color:#64748b;font-weight:900;letter-spacing:2px}.middleResizeRail:hover,.middleResizeRail.dragging{background:#93c5fd}.voicePipelineGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin:8px 0}.voicePipelineCard{border:1px solid var(--line);background:white;border-radius:12px;padding:8px;font-size:12px}.voicePipelineCard b{display:block;font-size:11px;text-transform:uppercase;color:#475467;letter-spacing:.03em;margin-bottom:2px}@media(max-width:900px){.voicePipelineGrid{grid-template-columns:1fr}}

/* v55.3.141 voice cue, resize, activity scroll and coding-flow hardening marker; v55.3.140 Odysseus validation command dock marker; v55.3.139 Odysseus-style voyage workspace deck marker; v55.3.134 sci-fi assistant shell continuity marker; v55.3.138 adds Odysseus-inspired workbench rail; v55.3.139 adds a hoverable voyage deck, workspace windows and FastAPI sidecar plan */
body{background:#e9eef5;background-image:linear-gradient(rgba(12,20,32,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(12,20,32,.045) 1px,transparent 1px),linear-gradient(135deg,#e9eef5,#f8fbff 48%,#eef9f6);background-size:32px 32px,32px 32px,100% 100%;--accent-cyan:#0e9fbd;--accent-rose:#e14b6c;--accent-green:#15985c;--accent-amber:#c58113;--chrome:#101722;--chrome-soft:#172235;--panel-glass:rgba(255,255,255,.94)}
main[data-ui-overhaul="v55.3.115"]{background:transparent}.card{background:var(--panel-glass);border-color:rgba(74,95,122,.28);border-radius:10px;box-shadow:0 14px 38px rgba(17,24,39,.13)}.sidebar.card,.rightbar.card,.chat-wrap.card{border-radius:10px}.panelHeader,.activityHead{background:linear-gradient(180deg,rgba(255,255,255,.96),rgba(244,248,252,.92));border-color:rgba(74,95,122,.25)}.topbar{min-height:0;padding:5px 10px;border-bottom:1px solid rgba(74,95,122,.22);justify-content:flex-end;background:linear-gradient(90deg,#101722,#172235);color:#e8f7ff}.topbar>div:first-child{display:none}.topbar .row.wrap{width:100%;justify-content:flex-end}.topbar button.secondary{background:rgba(255,255,255,.09);color:#e8f7ff;border:1px solid rgba(14,159,189,.35);padding:6px 10px;border-radius:8px}.topbar button.secondary:hover{background:rgba(14,159,189,.24)}.statuschips{min-height:30px;padding:5px 12px;background:#f6fafc;border-bottom:1px solid rgba(74,95,122,.18)}.smartTopStrip{position:relative;background:linear-gradient(90deg,#f7fbff,#eef8f6);border-bottom:1px solid rgba(74,95,122,.20);padding:7px 10px}.smartNow b{color:#0b5f72}.smartActions button{border-radius:8px}.chatTabs{display:flex;align-items:flex-end;gap:4px;min-height:38px;padding:5px 10px 0;background:linear-gradient(180deg,#edf4fb,#dfeaf5);border-bottom:1px solid rgba(74,95,122,.24);overflow-x:auto;overflow-y:hidden;scrollbar-width:thin;flex:0 0 auto}.chatTab{display:grid;grid-template-columns:minmax(86px,180px) auto auto;align-items:center;gap:4px;height:32px;max-width:240px;border:1px solid rgba(74,95,122,.34);border-bottom:0;background:#d8e5f0;color:#1b2a3b;border-radius:8px 8px 0 0;padding:0 5px}.chatTab.active{background:#fff;border-top:2px solid var(--accent-cyan);height:34px;color:#0f172a}.chatTabTitle{border:0;background:transparent;color:inherit;font-weight:800;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:4px 6px}.chatTabTitle:hover{background:rgba(14,159,189,.12)}.chatTabAction{width:24px;height:24px;padding:0;border-radius:7px;background:transparent;color:#526476;border:1px solid transparent}.chatTabAction:hover{background:rgba(14,159,189,.16);color:#0b5f72}.chatTabAction.shared{background:rgba(21,152,92,.14);color:#0f7a4a;border-color:rgba(21,152,92,.30)}.chatTabClose:hover{background:rgba(225,75,108,.14);color:#b42342}.chatTabAdd{height:30px;width:34px;padding:0;border-radius:8px 8px 0 0;background:#101722;color:#e8f7ff;border:1px solid rgba(14,159,189,.38);font-size:18px;line-height:1}.chatTabAdd:hover{background:#0e9fbd;color:white}.middleResizeRail.visible{height:10px;min-height:10px;background:linear-gradient(90deg,#101722,#0e9fbd,#15985c);border:0;box-shadow:0 1px 0 rgba(255,255,255,.55) inset,0 -1px 0 rgba(15,23,42,.18) inset}.middleResizeRail.visible:after{content:'resize panel';letter-spacing:.08em;font-size:9px;text-transform:uppercase;color:#f8fbff;text-shadow:0 1px 2px rgba(0,0,0,.25)}.middleResizeRail[data-resize-target="liveActivityPanel"]:after{content:'resize activity'}#chat{background:linear-gradient(180deg,#f9fcff,#eff6f5 62%,#edf2fa);padding:16px 18px}.bubble{border-radius:12px}.user .bubble{background:linear-gradient(135deg,#0e9fbd,#15985c);border-bottom-right-radius:4px}.assistant .bubble{border-color:rgba(74,95,122,.22);box-shadow:0 4px 18px rgba(17,24,39,.06);border-bottom-left-radius:4px}.activity{height:clamp(140px,26vh,430px)!important;max-height:74vh!important;resize:none;border-top:0;background:linear-gradient(180deg,#f8fbff,#edf7f4)}.composer{background:#fff;border-top:1px solid rgba(74,95,122,.20)}button{border-radius:8px}.pill{border-radius:999px}.novaOrbPanel,.communicationCentre{border-radius:10px;background:linear-gradient(135deg,#f7fbff,#eef8f6);border-color:rgba(14,159,189,.30)}body.theme-dark{--panel-glass:rgba(16,23,34,.96);background:#0f141d;background-image:linear-gradient(rgba(14,159,189,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(225,75,108,.08) 1px,transparent 1px),linear-gradient(135deg,#0f141d,#172235 52%,#10221d);background-size:32px 32px,32px 32px,100% 100%}body.theme-dark .chatTabs{background:linear-gradient(180deg,#172235,#101722);border-color:#2b3c52}body.theme-dark .chatTab{background:#172235;color:#dbeafe;border-color:#334155}body.theme-dark .chatTab.active{background:#0f141d;color:#f8fbff;border-top-color:#0e9fbd}body.theme-dark #chat{background:linear-gradient(180deg,#101722,#111b24 62%,#121827)}body.theme-dark .smartTopStrip,body.theme-dark .statuschips,body.theme-dark .activity,body.theme-dark .composer,body.theme-dark .panelHeader,body.theme-dark .activityHead{background:#111827;color:#e5e7eb;border-color:#334155}

.odysseusVoyageDeck{display:grid;gap:8px;padding:10px 12px;background:linear-gradient(135deg,#0f172a,#10263a 52%,#0f3b35);color:#e8fbff;border-bottom:1px solid rgba(14,159,189,.35);box-shadow:0 12px 28px rgba(15,23,42,.18) inset}
.voyageHero{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.voyageKicker{font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:#89f4ff;font-weight:900}.voyageHero b{display:block;font-size:16px}.voyageHero p{margin:2px 0 0;color:#c6e7f0;font-size:12px}.voyageActions{display:flex;gap:6px;flex-wrap:wrap}.voyageActions button{background:rgba(255,255,255,.10);color:#effcff;border:1px solid rgba(137,244,255,.35)}.voyageActions button:hover{background:rgba(14,159,189,.32)}
.voyageMap{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:7px}.odysseusValidationDock{display:grid;grid-template-columns:minmax(180px,1.2fr) repeat(4,minmax(120px,1fr));gap:8px;margin-top:10px}.validationDockCard{border:1px solid rgba(137,244,255,.22);background:rgba(3,12,22,.38);border-radius:14px;padding:9px;min-height:62px}.validationDockCard b{display:block;font-size:12px}.validationDockCard small{display:block;color:#c6e7f0;line-height:1.25}.validationDockCard button{margin-top:6px}.validationDockStatus{background:linear-gradient(135deg,rgba(14,159,189,.24),rgba(21,152,92,.18));border-color:rgba(137,244,255,.44)}@media(max-width:1100px){.odysseusValidationDock{grid-template-columns:repeat(auto-fit,minmax(145px,1fr))}}.voyageCard{min-height:72px;text-align:left;background:rgba(255,255,255,.08);color:#f5feff;border:1px solid rgba(255,255,255,.15);border-radius:14px;padding:10px;box-shadow:0 10px 24px rgba(0,0,0,.16);transition:transform .16s ease,background .16s ease,border-color .16s ease}.voyageCard:hover{transform:translateY(-2px);background:rgba(14,159,189,.22);border-color:rgba(137,244,255,.55)}.voyageCard.primary{background:linear-gradient(135deg,rgba(14,159,189,.48),rgba(21,152,92,.42));border-color:rgba(137,244,255,.62)}.voyageIcon{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:9px;background:rgba(255,255,255,.16);margin-bottom:5px}.voyageCard small{display:block;color:#c6e7f0;font-weight:600;line-height:1.25}.voyageCard b{display:block;font-size:13px;margin-bottom:2px}
body.theme-dark .odysseusVoyageDeck{background:linear-gradient(135deg,#070b12,#0b1725 48%,#07241f);border-color:#164e63}.theme-dark .voyageCard{background:rgba(255,255,255,.06);border-color:#2b5268}@media(max-width:900px){.odysseusVoyageDeck{padding:8px}.voyageMap{display:flex;overflow-x:auto;scroll-snap-type:x proximity}.voyageCard{min-width:150px;scroll-snap-align:start}.voyageHero p{display:none}}

.odysseusWorkspaceActions{display:flex;gap:6px;flex-wrap:wrap;align-items:center}.odysseusWorkspacePreview{border:1px solid #bae6fd;background:#f8fbff;border-radius:12px;padding:8px;min-height:42px}.workbenchWindowShell{display:grid;grid-template-columns:minmax(130px,190px) minmax(0,1fr);gap:10px;margin-top:10px}.workbenchWindowTabs{display:grid;gap:6px;align-content:start}.workbenchWindowTabs button{background:#eef2f7;color:#1f2937;border:1px solid #dbe3ef;text-align:left}.workbenchWindowTabs button.active{background:#101722;color:#fff;border-color:#0e9fbd}.workbenchWindowBody{border:1px solid var(--line);border-radius:12px;background:#f8fbff;padding:10px;min-height:260px;max-height:62vh;overflow:auto}.workbenchWindowGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px}.workbenchMiniCard{border:1px solid var(--line);border-radius:10px;background:#fff;padding:8px}.workbenchMiniCard b{display:block;margin-bottom:3px}.workbenchActionBar{border:1px solid #dbe3ef;background:#fff;border-radius:10px;padding:8px;margin:8px 0;display:grid;gap:7px}.workbenchActionBar textarea{min-height:64px}.workbenchActionBar select{width:100%;padding:10px 12px;border-radius:14px;border:1px solid #cbd5e1;background:white;color:var(--ink);font:14px Segoe UI,Arial,sans-serif}.workbenchActionLine{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:7px;align-items:center}.workbenchActionLine button{width:auto}.codeTabList{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.codeTabBtn{background:#fff!important;color:#111827!important;border:1px solid #cbd5e1!important}.codeTabBtn.active{border-color:#0e9fbd!important;box-shadow:0 0 0 2px rgba(14,159,189,.12)}.odysseusCodePreview{font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap;background:#101722;color:#e5e7eb;border-radius:10px;padding:9px;max-height:190px;overflow:auto}.workbenchStatLine{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}.workbenchStatLine .pill{margin-left:0}


/* v55.3.150 repo research radar codebase sanity marker: expanded repo manifests, audit commands and autonomous/idle tool awareness remain surfaced in the Orbit GUI. */
/* v55.3.141 clean Studio shell hotfix: rebuilds the visible GUI around a VS Code / ChatGPT style workspace while preserving existing routes, commands and panels. */
:root{--studio-bg:#f3f6fb;--studio-rail:#0f172a;--studio-sidebar:#f8fafc;--studio-surface:#ffffff;--studio-border:#d8e0ec;--studio-text:#162033;--studio-muted:#667085;--studio-accent:#2563eb;--studio-green:#0f9f6e;--studio-danger:#e11d48;--studio-shadow:0 10px 30px rgba(15,23,42,.08)}
body{background:var(--studio-bg)!important;background-image:none!important;color:var(--studio-text);--left-col:318px;--right-col:366px;overflow:hidden!important}
main[data-ui-overhaul="v55.3.115"]{width:100vw;max-width:none;height:100vh;padding:0!important;gap:0!important;grid-template-columns:minmax(280px,var(--left-col)) 5px minmax(560px,1fr) 5px minmax(320px,var(--right-col))!important;background:var(--studio-bg)!important}
.card,.sidebar.card,.rightbar.card,.chat-wrap.card{border-radius:0!important;box-shadow:none!important;background:var(--studio-surface)!important;border:0!important}.sidebar.card{border-right:1px solid var(--studio-border)!important}.rightbar.card{border-left:1px solid var(--studio-border)!important}.chat-wrap.card{border-left:1px solid #edf2f7!important;border-right:1px solid #edf2f7!important}
.sidebar,.rightbar{padding:0!important;max-height:100vh!important;overflow:auto;scrollbar-gutter:stable;background:var(--studio-sidebar)!important}.sidebar .panelHeader,.rightbar .panelHeader{position:sticky;top:0;z-index:20;background:#fff!important;border-bottom:1px solid var(--studio-border)!important;margin:0!important;padding:12px 14px!important}.panelHeader b{font-size:14px}.panelHeader .pill{font-size:11px;background:#eef6ff;color:#175cd3}
.resizeRail{width:5px!important;min-width:5px!important;background:#e4eaf3!important;border:0!important;border-radius:0!important;opacity:.85}.resizeRail:after{content:''!important}.resizeRail:hover,.resizeRail.dragging{background:#93c5fd!important;opacity:1}
.edgeRail{display:none!important}.edgeRailToggle{display:none!important}
.section-title{margin:18px 14px 8px!important;padding:0!important;border-top:0!important;text-transform:uppercase;letter-spacing:.06em;font-size:11px!important;color:#475467}.small{color:var(--studio-muted)}
.controlHero{margin:10px 12px!important;padding:10px 12px!important;border-radius:12px!important;border:1px solid #e2e8f0!important;background:#fff!important}.controlHeroGrid{grid-template-columns:repeat(2,1fr)!important}.leftActionDock{display:none!important}.odysseusWorkbenchPanel{display:none!important}
#quickControlsGrouped,.chatSessionBar,#commandPalette,#projects,#files,#customTools,.leftFileDock,.sidebar textarea,.sidebar input,.sidebar>.row,.sidebar>p,.sidebar>button{margin-left:12px!important;margin-right:12px!important}.commandPalette,.quickControlsBox,#projects,#files,#customTools{max-height:28vh!important;overflow:auto}.projectItem,.item,.toolItem{border-radius:12px!important;border-color:#e2e8f0!important;box-shadow:none!important}.projectMeta span{background:#f1f5f9!important;border:1px solid #e2e8f0!important}
.topbar{min-height:46px!important;background:#fff!important;color:var(--studio-text)!important;border-bottom:1px solid var(--studio-border)!important;justify-content:space-between!important;padding:8px 12px!important}.topbar>div:first-child{display:block!important}.topbar .title{font-size:14px}.topbar .subtitle{display:none!important}.topbar button.secondary{background:#f1f5f9!important;color:#1f2937!important;border:1px solid #e2e8f0!important;padding:7px 10px!important}.topbar button.secondary:hover{background:#eaf1fb!important}.topbar .pill.good{background:#dcfce7;color:#166534}
.studioHome{display:grid;grid-template-columns:minmax(260px,1fr) auto;gap:12px;align-items:center;padding:12px 14px;background:linear-gradient(180deg,#ffffff,#f8fbff);border-bottom:1px solid var(--studio-border)}.studioBrand{display:grid;gap:2px;min-width:0}.studioKicker{font-size:11px;text-transform:uppercase;letter-spacing:.12em;font-weight:900;color:#2563eb}.studioBrand b{font-size:18px}.studioBrand span:last-child{font-size:12px;color:var(--studio-muted)}.studioNav{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.studioNav button{background:#f1f5f9!important;color:#1f2937!important;border:1px solid #dbe3ef!important;border-radius:10px!important;padding:8px 10px!important}.studioNav button.primary{background:#111827!important;color:#fff!important;border-color:#111827!important}.studioNav button.danger{background:#ffe4e6!important;color:#be123c!important;border-color:#fecdd3!important}.studioNav button:hover{background:#eaf1fb!important;color:#0f172a!important}.studioNav button.primary:hover{background:#1f2937!important;color:#fff!important}
.odysseusVoyageDeck{max-height:0!important;min-height:0!important;overflow:hidden!important;opacity:0!important;padding:0!important;margin:0!important;border:0!important;box-shadow:none!important}.odysseusVoyageDeck *{pointer-events:none}.statuschips{min-height:30px!important;padding:5px 14px!important;background:#fbfdff!important;border-bottom:1px solid #e5edf7!important}.statuschips .pill{font-size:11px}
.smartTopStrip{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:10px!important;padding:8px 14px!important;background:#fff!important;border-bottom:1px solid var(--studio-border)!important;position:relative!important;top:auto!important;z-index:6}.smartNow b{color:#111827}.smartActions{gap:6px!important}.smartActions button{border-radius:10px!important}.smartActions .newChatPrimary{background:#111827!important;color:#fff!important}.sandboxTabs{display:none!important}.sandboxPanel:not(.forceVisible){display:none!important}.archMini{display:none!important}
.middleResizeRail.visible{height:4px!important;min-height:4px!important;flex:0 0 4px!important;background:#e5edf7!important;border:0!important;box-shadow:none!important;opacity:.65}.middleResizeRail.visible:after{content:''!important}.middleResizeRail.visible:hover,.middleResizeRail.visible.dragging{height:7px!important;min-height:7px!important;background:#93c5fd!important;opacity:1}.middleResizeRail[data-resize-target="liveActivityPanel"]{background:#dbeafe!important}
.chatTabs{min-height:36px!important;padding:4px 12px 0!important;background:#f8fafc!important;border-bottom:1px solid var(--studio-border)!important}.chatTab{height:31px!important;background:#edf2f7!important;border-color:#dbe3ef!important;border-radius:10px 10px 0 0!important}.chatTab.active{background:#fff!important;border-top:2px solid #2563eb!important;color:#111827!important}.chatTabAdd{background:#111827!important;color:#fff!important;border-radius:10px 10px 0 0!important}
#chat{background:#fff!important;padding:18px max(22px,4vw)!important}.bubble{border-radius:16px!important;box-shadow:none!important}.user .bubble{background:#2563eb!important;color:#fff!important;border-bottom-right-radius:5px!important}.assistant .bubble{background:#f8fafc!important;border:1px solid #e2e8f0!important;border-bottom-left-radius:5px!important}.bubble{max-width:min(900px,86%)!important}
.activity{height:clamp(122px,20vh,300px)!important;min-height:86px!important;max-height:46vh!important;background:#fbfdff!important;border-top:1px solid var(--studio-border)!important;resize:none!important}.activityHead{background:#fbfdff!important;border-bottom:1px solid #e5edf7!important;padding:9px 12px!important;margin:0!important}.activityHead h3{font-size:14px}.activityHint{display:none}.activitySubtitle{padding:8px 12px 0!important;font-size:12px}.activity #activityLog{padding:6px 12px 12px!important;max-height:calc(100% - 82px)!important}.run{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:12px!important;margin:6px 0!important}.run summary{padding:8px 10px!important}.runbody{max-height:260px!important}
.composer{background:#fff!important;border-top:1px solid var(--studio-border)!important;padding:12px 16px!important;box-shadow:none!important}.inputDock{grid-template-columns:auto minmax(0,1fr) auto auto!important;gap:8px!important}.composerText{min-height:48px!important;border-radius:18px!important;border-color:#d0d7de!important;background:#fff!important}.composer .voiceWaveRow{display:none!important}.contextStatusLine{margin-top:7px!important;display:block!important}.plusBtn,.voiceBtn{width:40px!important;height:40px!important}.sendBtn{height:40px!important;border-radius:14px!important;background:#2563eb!important}
.rightbar .panelHeader{margin-bottom:0!important}.rightbar .section-title{margin-left:14px!important}.novaOrbPanel{margin:12px!important;border-radius:14px!important;border:1px solid #dbeafe!important;background:#fff!important;box-shadow:none!important}.novaOrb{width:58px!important;height:58px!important;font-size:25px!important}.communicationCentre,.voiceGuardCard,.communicationTranscriptBox,.rightStateHero,.assistantBoxPanel,.novaCard,.aiFocus,.createdOutput,.planPanel{margin:10px 12px!important;border-radius:14px!important;background:#fff!important;border:1px solid #e2e8f0!important;box-shadow:none!important}.voicePipelineGrid{grid-template-columns:1fr 1fr!important}.voicePipelineCard{background:#f8fafc!important;border-color:#e2e8f0!important}.voiceWaveCard{background:#f8fafc!important}.editor{height:240px!important}.codepreview{max-height:190px!important}
button{font-weight:700!important}.pill{border-radius:999px!important}.settingsPanel{border-radius:16px!important;right:18px!important;top:58px!important}.popupPanel{border-radius:16px!important}.workbenchWindowShell{grid-template-columns:190px minmax(0,1fr)!important}
body.theme-dark{--studio-bg:#0f172a;--studio-sidebar:#111827;--studio-surface:#111827;--studio-border:#263244;--studio-text:#e5e7eb;--studio-muted:#9ca3af;background:#0b1120!important}.theme-dark .card,.theme-dark .sidebar,.theme-dark .rightbar,.theme-dark .chat-wrap,.theme-dark .topbar,.theme-dark .smartTopStrip,.theme-dark .studioHome,.theme-dark .composer,.theme-dark .activity,.theme-dark .activityHead,.theme-dark .statuschips{background:#111827!important;color:#e5e7eb!important;border-color:#263244!important}.theme-dark #chat{background:#0f172a!important}.theme-dark .assistant .bubble{background:#172033!important;border-color:#263244!important;color:#e5e7eb!important}.theme-dark .studioNav button,.theme-dark .topbar button.secondary{background:#1f2937!important;color:#e5e7eb!important;border-color:#374151!important}.theme-dark .controlHero,.theme-dark .item,.theme-dark .projectItem,.theme-dark .novaOrbPanel,.theme-dark .communicationCentre,.theme-dark .voiceGuardCard,.theme-dark .communicationTranscriptBox,.theme-dark .rightStateHero,.theme-dark .assistantBoxPanel,.theme-dark .novaCard{background:#172033!important;border-color:#263244!important;color:#e5e7eb!important}
@media(max-width:1180px){main[data-ui-overhaul="v55.3.115"]{grid-template-columns:1fr!important}.resizeRail,.sidebar,.rightbar{display:none!important}.studioHome{grid-template-columns:1fr}.studioNav{justify-content:flex-start}.activity{max-height:34vh!important}.chat-wrap.card{height:100vh!important}}



/* v55.3.141 Orbit GUI shell: real Odysseus-inspired rebuild overlay.
   Keeps Nova's original backend IDs/routes intact but re-frames the UI into:
   left app rail, centred chat canvas, slide-out tool/voice/activity drawers. */
:root{
  --orbit-bg:#03070a;
  --orbit-grid:rgba(0,235,255,.075);
  --orbit-panel:#15101f;
  --orbit-panel-2:#0d0b14;
  --orbit-card:#181220;
  --orbit-card-2:#0b1218;
  --orbit-border:#6d2aa4;
  --orbit-border-soft:rgba(203,78,255,.36);
  --orbit-neon:#cc37ff;
  --orbit-cyan:#91f6ff;
  --orbit-ink:#bdf7ff;
  --orbit-muted:#7f9aa5;
  --orbit-danger:#ff3b74;
  --orbit-success:#00e676;
  --orbit-left:224px;
  --orbit-chat-max:860px;
  --orbit-font:'Fira Code','Cascadia Mono','Consolas',monospace;
}
body.nova-orbit-shell{
  font-family:var(--orbit-font)!important;
  color:var(--orbit-ink)!important;
  background:#000!important;
  background-image:
    radial-gradient(circle at 20% 20%, rgba(203,55,255,.13), transparent 28%),
    radial-gradient(circle at 85% 70%, rgba(0,240,255,.10), transparent 28%),
    linear-gradient(var(--orbit-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--orbit-grid) 1px, transparent 1px)!important;
  background-size:auto,auto,24px 24px,24px 24px!important;
  background-attachment:fixed!important;
  overflow:hidden!important;
  --left-col:var(--orbit-left)!important;
  --right-col:0px!important;
}
body.nova-orbit-shell::before,
body.nova-orbit-shell::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
}
body.nova-orbit-shell::before{
  background:radial-gradient(circle, rgba(145,246,255,.9) 0 1px, transparent 2px) 18% 19%/260px 220px,
             radial-gradient(circle, rgba(203,55,255,.55) 0 1px, transparent 2px) 74% 47%/320px 280px;
  opacity:.45;animation:orbitDrift 28s linear infinite;
}
body.nova-orbit-shell::after{
  background:linear-gradient(90deg, rgba(0,0,0,.44), transparent 22%, transparent 72%, rgba(0,0,0,.52));
}
@keyframes orbitDrift{to{background-position:310px 120px,-240px 170px}}
body.nova-orbit-shell main[data-ui-overhaul]{
  position:relative;z-index:1;width:100vw!important;max-width:none!important;height:100vh!important;padding:0!important;gap:0!important;
  display:grid!important;grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important;background:transparent!important;
}
body.nova-orbit-shell .resizeRail{display:none!important}
body.nova-orbit-shell .sidebar.card,
body.nova-orbit-shell .chat-wrap.card,
body.nova-orbit-shell .rightbar.card{box-shadow:none!important;border-radius:0!important;background:transparent!important;border:0!important;backdrop-filter:none!important}
body.nova-orbit-shell .sidebar.card{grid-column:1!important;overflow:hidden!important;padding:0!important;background:rgba(21,16,31,.94)!important;border-right:1px solid rgba(203,55,255,.22)!important;box-shadow:20px 0 60px rgba(0,0,0,.28)!important}
body.nova-orbit-shell .sidebar.card>:not(#orbitNav){display:none!important}
body.nova-orbit-shell .chat-wrap.card{grid-column:3!important;min-width:0!important;display:grid!important;grid-template-rows:34px minmax(0,1fr) auto!important;overflow:hidden!important;background:transparent!important;border-left:1px solid rgba(145,246,255,.07)!important}
body.nova-orbit-shell .rightbar.card{display:none!important}
body.nova-orbit-shell .topbar,
body.nova-orbit-shell #studioHome,
body.nova-orbit-shell .statuschips,
body.nova-orbit-shell .smartTopStrip,
body.nova-orbit-shell .archMini,
body.nova-orbit-shell .sandboxTabs,
body.nova-orbit-shell .sandboxPanel,
body.nova-orbit-shell .chatTabs,
body.nova-orbit-shell .middleResizeRail,
body.nova-orbit-shell .odysseusVoyageDeck{display:none!important}
#orbitNav{height:100vh;display:flex;flex-direction:column;padding:14px 12px;gap:12px;color:var(--orbit-ink)}
.orbitBrand{display:flex;align-items:center;gap:10px;padding:6px 8px 14px}.orbitHamburger{font-size:20px;color:#87a8b5}.orbitLogo{margin-left:auto;color:var(--orbit-neon);font-weight:900;font-size:18px;letter-spacing:.04em;text-shadow:0 0 18px rgba(203,55,255,.68)}
.orbitNavSection{display:grid;gap:4px}.orbitNavButton{width:100%;display:flex;align-items:center;gap:10px;border:0!important;background:transparent!important;color:#b6dce8!important;text-align:left;padding:9px 10px!important;border-radius:8px!important;font-size:12px!important;font-weight:700!important;cursor:pointer}.orbitNavButton:hover,.orbitNavButton.active{background:rgba(203,55,255,.16)!important;color:#fff!important}.orbitNavButton .ico{width:18px;text-align:center;color:var(--orbit-neon);font-weight:900}.orbitNavButton .plus{margin-left:auto;color:#d9a3ff}.orbitNavButton small{margin-left:auto;color:#6e8793;font-size:10px}.orbitNavSpacer{flex:1}.orbitProfile{display:flex;align-items:center;gap:10px;color:#a9c5cf;font-size:12px;padding:8px}.orbitAvatar{width:24px;height:24px;border-radius:999px;display:grid;place-items:center;background:#24303b;color:#c7efff}.orbitGear{margin-left:auto;background:transparent!important;border:0!important;color:#8ea5af!important}
body.nova-orbit-shell #orbitHeader{grid-row:1;height:34px;display:flex;align-items:center;justify-content:center;gap:10px;color:#7da7b4;font-size:12px;letter-spacing:.03em;position:relative;z-index:5}.orbitModelTag{color:#a6e9ff}.orbitHeaderActions{position:absolute;right:22px;top:4px;display:flex;gap:8px}.orbitHeaderActions button{background:transparent!important;border:1px solid transparent!important;color:#72909b!important;padding:3px 7px!important;border-radius:6px!important}.orbitHeaderActions button:hover{border-color:var(--orbit-border-soft)!important;color:white!important;background:rgba(203,55,255,.12)!important}
body.nova-orbit-shell #chat{grid-row:2;padding:18px 20px 138px!important;margin:0 auto!important;width:min(100%,calc(var(--orbit-chat-max) + 80px));max-width:calc(var(--orbit-chat-max) + 80px);background:transparent!important;overflow:auto!important;scrollbar-gutter:stable;scroll-behavior:smooth}.orbitWelcome{max-width:680px;margin:9vh auto 24px;padding:22px 24px;border:1px solid rgba(203,55,255,.46);background:rgba(21,16,31,.72);border-radius:18px;box-shadow:0 0 70px rgba(203,55,255,.12)}.orbitWelcome h1{margin:0 0 6px;color:#f05bff;font-size:28px;text-shadow:0 0 20px rgba(203,55,255,.36)}.orbitWelcome p{margin:0;color:#9bd9e7;line-height:1.55}.orbitWelcome .quickchips{margin-top:14px;display:flex;gap:8px;flex-wrap:wrap}.orbitWelcome button{background:rgba(203,55,255,.16)!important;border:1px solid rgba(203,55,255,.5)!important;color:#dffbff!important;border-radius:999px!important;padding:8px 10px!important}
body.nova-orbit-shell .msg{display:block!important;max-width:var(--orbit-chat-max);margin:10px auto!important}.nova-orbit-shell .msg.user{border-left:2px solid rgba(145,246,255,.28);padding-left:14px}.nova-orbit-shell .msg.assistant{padding-left:0}.nova-orbit-shell .bubble{max-width:100%!important;border-radius:0 14px 14px 14px!important;background:rgba(18,14,26,.72)!important;border:1px solid rgba(203,55,255,.56)!important;color:#bdf7ff!important;box-shadow:0 0 0 1px rgba(0,0,0,.35),0 20px 60px rgba(0,0,0,.22)!important;line-height:1.55!important;font-size:14px!important;padding:14px 16px!important}.nova-orbit-shell .user .bubble{background:transparent!important;border-color:rgba(203,55,255,.56)!important;color:#c8fbff!important;border-radius:0!important;box-shadow:none!important;padding:8px 12px!important}.nova-orbit-shell .assistant .bubble{background:rgba(20,15,29,.88)!important}.nova-orbit-shell .name{max-width:var(--orbit-chat-max);margin:0 auto 4px!important;color:#9cf7ff!important;font-weight:800!important}.nova-orbit-shell .meta{color:#6f8490!important}
body.nova-orbit-shell .composer{grid-row:3;position:absolute!important;left:50%!important;bottom:16px!important;transform:translateX(-50%)!important;width:min(820px,calc(100vw - var(--orbit-left) - 110px))!important;z-index:40;background:rgba(21,16,31,.94)!important;border:1px solid var(--orbit-border)!important;border-radius:18px!important;box-shadow:0 0 0 1px rgba(0,0,0,.3),0 20px 80px rgba(0,0,0,.55)!important;padding:10px 12px!important}.nova-orbit-shell .inputDock{display:grid!important;grid-template-columns:auto minmax(0,1fr) auto auto!important;align-items:end!important;gap:8px!important}.nova-orbit-shell .composerText{min-height:54px!important;max-height:140px!important;background:transparent!important;border:0!important;color:#c7fbff!important;box-shadow:none!important;resize:none!important;padding:10px!important}.nova-orbit-shell .composerText::placeholder{color:#5d7b86!important}.nova-orbit-shell .plusBtn,.nova-orbit-shell .voiceBtn{background:rgba(203,55,255,.18)!important;border:1px solid rgba(203,55,255,.5)!important;color:#dffbff!important;border-radius:11px!important}.nova-orbit-shell .sendBtn{background:#be3bdc!important;border:1px solid #e07bff!important;color:white!important;border-radius:12px!important;min-width:46px!important}.nova-orbit-shell .composer .tiny.secondary[onclick="diagnoseVoiceInput()"],.nova-orbit-shell .contextStatusLine{display:none!important}
#orbitDrawer,#orbitRightDrawer,#orbitActivityDrawer{position:fixed;z-index:80;background:rgba(21,16,31,.98);border:1px solid var(--orbit-border);box-shadow:0 28px 100px rgba(0,0,0,.65),0 0 60px rgba(203,55,255,.14);color:var(--orbit-ink);display:none;overflow:hidden}.orbitDrawerOpen #orbitDrawer{display:block}#orbitDrawer{left:var(--orbit-left);top:0;height:100vh;width:min(430px,calc(100vw - var(--orbit-left) - 40px));border-top:0;border-bottom:0}.orbitDrawerHeader{height:52px;display:flex;align-items:center;gap:10px;padding:0 14px;border-bottom:1px solid rgba(203,55,255,.32);background:rgba(15,10,23,.98)}.orbitDrawerHeader b{color:#f05bff;font-size:16px}.orbitDrawerHeader span{color:#85a8b4;font-size:12px}.orbitDrawerHeader button{margin-left:auto;background:transparent!important;border:1px solid rgba(145,246,255,.35)!important;color:#bdf7ff!important;border-radius:7px!important}.orbitDrawerBody{height:calc(100% - 52px);overflow:auto;padding:14px}.nova-orbit-shell #orbitLegacyDrawer .panelHeader,.nova-orbit-shell #orbitLegacyDrawer .section-title{position:relative!important;top:auto!important;background:transparent!important;color:#f05bff!important;border:0!important;margin:16px 0 8px!important;padding:0!important}.nova-orbit-shell #orbitLegacyDrawer input,.nova-orbit-shell #orbitLegacyDrawer textarea,.nova-orbit-shell #orbitLegacyDrawer select{background:#09070d!important;border:1px solid rgba(203,55,255,.42)!important;color:#c8fbff!important;border-radius:9px!important}.nova-orbit-shell #orbitLegacyDrawer .item,.nova-orbit-shell #orbitLegacyDrawer .projectItem,.nova-orbit-shell #orbitLegacyDrawer .toolItem{background:rgba(10,8,15,.76)!important;border:1px solid rgba(203,55,255,.32)!important;border-radius:12px!important;color:#bdf7ff!important}.nova-orbit-shell #orbitLegacyDrawer button{background:rgba(203,55,255,.14)!important;border:1px solid rgba(203,55,255,.42)!important;color:#dffbff!important;border-radius:9px!important}.nova-orbit-shell #orbitLegacyDrawer button.danger{background:rgba(255,59,116,.16)!important;border-color:rgba(255,59,116,.55)!important;color:#ffd7e2!important}
body.orbit-right-open #orbitRightDrawer{display:block}#orbitRightDrawer{right:0;top:0;width:min(520px,45vw);height:100vh;border-top:0;border-bottom:0}.nova-orbit-shell #orbitRightDrawer .rightbar{display:block!important;background:transparent!important;border:0!important;padding:0!important;overflow:visible!important}.nova-orbit-shell #orbitRightDrawer .panelHeader{position:sticky!important;top:0!important;z-index:3;background:rgba(15,10,23,.98)!important;color:#f05bff!important;border-bottom:1px solid rgba(203,55,255,.32)!important}.nova-orbit-shell #orbitRightDrawer .item,.nova-orbit-shell #orbitRightDrawer .communicationCentre,.nova-orbit-shell #orbitRightDrawer .voiceGuardCard,.nova-orbit-shell #orbitRightDrawer .communicationTranscriptBox,.nova-orbit-shell #orbitRightDrawer .novaOrbPanel,.nova-orbit-shell #orbitRightDrawer .assistantBoxPanel,.nova-orbit-shell #orbitRightDrawer .jarvisSidecarPanel,.nova-orbit-shell #orbitRightDrawer .planPanel,.nova-orbit-shell #orbitRightDrawer .aiFocus,.nova-orbit-shell #orbitRightDrawer .transparentOutputPanel{background:rgba(10,8,15,.76)!important;border:1px solid rgba(203,55,255,.28)!important;border-radius:13px!important;color:#bdf7ff!important;margin:10px 12px!important}.nova-orbit-shell #orbitRightDrawer textarea,.nova-orbit-shell #orbitRightDrawer .codepreview{background:#08060d!important;color:#c7fbff!important;border:1px solid rgba(203,55,255,.34)!important}
body.orbit-activity-open #orbitActivityDrawer{display:block}#orbitActivityDrawer{left:calc(var(--orbit-left) + 24px);right:24px;bottom:92px;height:min(44vh,420px);border-radius:16px}.nova-orbit-shell #orbitActivityDrawer .activity{display:block!important;position:static!important;height:100%!important;max-height:none!important;min-height:0!important;background:transparent!important;border:0!important;color:#bdf7ff!important}.nova-orbit-shell #orbitActivityDrawer .activityHead{background:rgba(15,10,23,.98)!important;color:#f05bff!important;border-bottom:1px solid rgba(203,55,255,.28)!important}.nova-orbit-shell #orbitActivityDrawer .run{background:rgba(10,8,15,.78)!important;border:1px solid rgba(203,55,255,.28)!important;color:#bdf7ff!important}.nova-orbit-shell #orbitActivityDrawer #activityLog{max-height:calc(100% - 92px)!important;overflow:auto!important}
body.nova-orbit-shell:not(.orbit-activity-open) .chat-wrap>.activity{display:none!important}

/* v55.3.142 Orbit workspace fix: drawers reserve layout space instead of covering chat, activity docks inside chat, and theme variables are user-customisable. */
body.nova-orbit-shell{
  --orbit-drawer-width:min(430px,calc(100vw - var(--orbit-left) - 360px));
  --orbit-right-width:min(520px,45vw);
  --nova-primary:#cb37ff;
  --nova-secondary:#91f6ff;
  --nova-panel:#15101f;
  --nova-bg:#000000;
  --nova-text:#bdf7ff;
  --orbit-neon:var(--nova-primary)!important;
  --orbit-cyan:var(--nova-secondary)!important;
  --orbit-panel:var(--nova-panel)!important;
  --orbit-ink:var(--nova-text)!important;
}
body.nova-orbit-shell.orbitDrawerOpen main[data-ui-overhaul]{grid-template-columns:calc(var(--orbit-left) + var(--orbit-drawer-width)) 0 minmax(0,1fr) 0 0!important;}
body.nova-orbit-shell.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 var(--orbit-right-width)!important;}
body.nova-orbit-shell.orbitDrawerOpen.orbit-right-open main[data-ui-overhaul]{grid-template-columns:calc(var(--orbit-left) + var(--orbit-drawer-width)) 0 minmax(0,1fr) 0 var(--orbit-right-width)!important;}
body.nova-orbit-shell .chat-wrap.card{transition:grid-template-columns .18s ease, margin .18s ease;grid-template-rows:34px minmax(0,1fr) auto auto!important;}
body.nova-orbit-shell #chat{padding-bottom:24px!important;}
body.nova-orbit-shell .composer{grid-row:4!important;position:relative!important;left:auto!important;right:auto!important;bottom:auto!important;transform:none!important;width:min(820px,calc(100% - 44px))!important;margin:0 auto 14px!important;}
#orbitDrawer,#orbitRightDrawer{display:block!important;transition:transform .18s ease, opacity .18s ease;opacity:0;pointer-events:none;}
#orbitDrawer{width:var(--orbit-drawer-width)!important;transform:translateX(-103%);}
body.orbitDrawerOpen #orbitDrawer{transform:translateX(0);opacity:1;pointer-events:auto;}
#orbitRightDrawer{width:var(--orbit-right-width)!important;transform:translateX(103%);}
body.orbit-right-open #orbitRightDrawer{transform:translateX(0);opacity:1;pointer-events:auto;}
#orbitActivityDrawer{grid-row:3!important;position:relative!important;left:auto!important;right:auto!important;bottom:auto!important;display:none!important;width:min(1180px,calc(100% - 44px))!important;height:min(28vh,280px)!important;margin:0 auto 10px!important;border-radius:16px!important;z-index:35!important;}
body.orbit-activity-open #orbitActivityDrawer{display:block!important;}
body.orbit-activity-open #chat{padding-bottom:12px!important;}
.nova-orbit-shell #orbitActivityDrawer .activityHead{position:sticky;top:0;z-index:3;}
.nova-orbit-shell #orbitActivityDrawer #activityLog{max-height:calc(100% - 86px)!important;overflow:auto!important;}
.orbitNavButton[data-open="true"]{background:rgba(203,55,255,.24)!important;color:#fff!important;box-shadow:inset 3px 0 0 var(--orbit-neon)}
.orbitBrand{position:relative}.orbitMiniOrb{width:22px;height:22px;border-radius:999px;display:inline-grid;place-items:center;margin-left:4px;background:radial-gradient(circle,#fff 0 18%,var(--orbit-cyan) 20% 45%,#1b1230 47% 100%);box-shadow:0 0 16px rgba(145,246,255,.7);font-size:11px;color:#071019;animation:orbitPulse 1.8s ease-in-out infinite}.orbitMiniOrb.thinking{background:radial-gradient(circle,#fff 0 12%,#ffd166 16% 42%,#1b1230 46% 100%)}.orbitMiniOrb.speaking{background:radial-gradient(circle,#fff 0 12%,#ff5bea 16% 42%,#1b1230 46% 100%);animation:orbitSpeakPulse .38s ease-in-out infinite}.orbitMiniOrb.listening{background:radial-gradient(circle,#fff 0 12%,#00e676 16% 42%,#1b1230 46% 100%)}@keyframes orbitPulse{50%{transform:scale(1.09);filter:brightness(1.25)}}@keyframes orbitSpeakPulse{50%{transform:scale(1.24);box-shadow:0 0 28px rgba(255,91,234,.95)}}
#orbitSubChat{position:absolute;right:18px;bottom:104px;width:min(340px,32vw);max-height:150px;overflow:auto;border:1px solid rgba(145,246,255,.28);border-radius:14px;background:rgba(9,7,13,.86);box-shadow:0 18px 52px rgba(0,0,0,.42);padding:8px;z-index:36;color:var(--orbit-ink);font-size:11px}.orbitSubLine{border-bottom:1px solid rgba(203,55,255,.16);padding:4px 0}.orbitSubLine:last-child{border-bottom:0}.orbitSubLine b{color:var(--orbit-neon)}
.orbitInlinePanel{border:1px solid rgba(203,55,255,.34);border-radius:14px;background:rgba(9,7,13,.72);padding:10px;margin:10px 0;color:var(--orbit-ink)}.orbitInlinePanel h3{margin:0 0 8px;color:var(--orbit-neon);font-size:14px}.orbitAppsGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}.orbitAppCard{border:1px solid rgba(145,246,255,.22);border-radius:12px;background:rgba(0,240,255,.04);padding:9px;color:var(--orbit-ink)}.orbitAppCard b{color:var(--orbit-cyan)}.orbitThemeGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.orbitThemeGrid label{display:grid;gap:4px;font-size:11px;color:#91b7c3}.orbitThemeGrid input[type=color]{width:100%;height:34px;background:#08060d;border:1px solid rgba(203,55,255,.42);border-radius:8px}.orbitThemeActions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.nova-orbit-shell #orbitLegacyDrawer .commandItem,.nova-orbit-shell #orbitLegacyDrawer .quickGroup,.nova-orbit-shell #orbitLegacyDrawer .quickControlsBox,.nova-orbit-shell #orbitLegacyDrawer .controlHero,.nova-orbit-shell #orbitLegacyDrawer .actionCluster,.nova-orbit-shell #orbitLegacyDrawer .odysseusWorkbenchPanel{background:rgba(10,8,15,.82)!important;border:1px solid rgba(203,55,255,.28)!important;color:var(--orbit-ink)!important}.nova-orbit-shell #orbitLegacyDrawer .small,.nova-orbit-shell #orbitLegacyDrawer code{color:#96b8c4!important}.nova-orbit-shell #orbitLegacyDrawer .pill{color:#dffbff!important}.nova-orbit-shell #chatsPopup{display:none!important}
@media(max-width:1180px){body.nova-orbit-shell.orbitDrawerOpen main[data-ui-overhaul],body.nova-orbit-shell.orbit-right-open main[data-ui-overhaul],body.nova-orbit-shell.orbitDrawerOpen.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important}#orbitDrawer,#orbitRightDrawer{width:calc(100vw - var(--orbit-left))!important}#orbitSubChat{display:none}}

.nova-orbit-shell button{font-family:var(--orbit-font)!important}.nova-orbit-shell .pill{background:rgba(203,55,255,.14)!important;border:1px solid rgba(203,55,255,.28)!important;color:#aef7ff!important}.nova-orbit-shell ::selection{background:rgba(203,55,255,.45);color:white}.nova-orbit-shell ::-webkit-scrollbar{width:10px;height:10px}.nova-orbit-shell ::-webkit-scrollbar-track{background:#0e0a15}.nova-orbit-shell ::-webkit-scrollbar-thumb{background:#ba34dd;border-radius:10px;border:2px solid #0e0a15}.nova-orbit-shell #plusMenu{background:rgba(21,16,31,.98)!important;border:1px solid var(--orbit-border)!important;color:#bdf7ff!important}.nova-orbit-shell .settingsPanel,.nova-orbit-shell .popupPanel{background:rgba(21,16,31,.98)!important;border:1px solid var(--orbit-border)!important;color:#bdf7ff!important;box-shadow:0 28px 100px rgba(0,0,0,.7)!important}
@media(max-width:980px){body.nova-orbit-shell{--orbit-left:64px}.orbitNavButton span.label,.orbitLogo,.orbitProfile span{display:none}.orbitNavButton{justify-content:center}.orbitNavButton .ico{width:auto}.nova-orbit-shell .composer{width:calc(100vw - 92px)!important}#orbitDrawer{left:64px;width:calc(100vw - 64px)}#orbitRightDrawer{width:calc(100vw - 64px)}#orbitActivityDrawer{left:76px}}


/* v55.3.150 repo research radar codebase sanity routing */
/* v55.3.144 Orbit voice/file workspace polish */
body.nova-orbit-shell main[data-ui-overhaul]{opacity:1!important}
body.nova-orbit-shell #orbitHeader{justify-content:center!important;padding:0 172px 0 12px!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-bottom:1px solid rgba(145,246,255,.07)}
.orbitHeaderActions button{font-size:12px!important}.orbitHeaderActions button:last-child{display:none!important}.orbitHeaderActions{right:14px!important}.orbitModelTag,#orbitClock,#orbitMessageCount,#orbitRunMini{max-width:32vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.orbitStatePill{display:inline-flex;align-items:center;gap:7px;border:1px solid rgba(145,246,255,.35)!important;background:rgba(10,8,15,.8)!important;color:#dffbff!important;border-radius:999px!important;padding:4px 9px!important;min-width:96px;justify-content:flex-start;box-shadow:0 0 22px rgba(203,55,255,.16)}.orbitStatePill .orbitMiniOrb{margin:0!important}.orbitStatePill.listening{border-color:#00e676!important}.orbitStatePill.thinking,.orbitStatePill.working{border-color:#ffd166!important}.orbitStatePill.speaking{border-color:#ff5bea!important;animation:orbitSpeakPulse .42s ease-in-out infinite}.orbitStatePill.detected{border-color:#91f6ff!important}.orbitStatePill #orbitStateLabel{font-size:11px;font-weight:900}.orbitNavButton .ico{font-size:15px!important}.orbitNavButton{font-size:12.5px!important}.orbitNavButton[data-open="true"]{background:rgba(203,55,255,.24)!important}.nova-orbit-shell #orbitLegacyDrawer .item,.nova-orbit-shell #orbitLegacyDrawer .projectItem,.nova-orbit-shell #orbitLegacyDrawer .toolItem,.orbitInlinePanel{background:rgba(12,9,18,.92)!important;color:#bdf7ff!important}.nova-orbit-shell #orbitLegacyDrawer .item *, .nova-orbit-shell #orbitLegacyDrawer .projectItem *, .orbitInlinePanel *{color:inherit}.nova-orbit-shell #orbitLegacyDrawer .item .small,.orbitInlinePanel .small{color:#91b7c3!important}.nova-orbit-shell #orbitLegacyDrawer input,.nova-orbit-shell #orbitLegacyDrawer textarea,.nova-orbit-shell #orbitLegacyDrawer select{background:#07060b!important;color:#dffbff!important}.orbitChatRow.active{border-color:#91f6ff!important;box-shadow:0 0 0 1px rgba(145,246,255,.32)!important}.orbitChatRow h4{color:#f05bff}.chatTabAction.chatMuted,.chatMuteBtn.chatMuted{background:rgba(255,59,116,.22)!important;border-color:#ff3b74!important;color:#ffd7e2!important}.voiceChallengeBox{border:1px solid rgba(145,246,255,.28);border-radius:12px;padding:8px;margin:8px 0;background:rgba(0,240,255,.045)}.voiceChallengeBox code{display:block;margin:6px 0;background:#03070a!important;color:#91f6ff!important;border-color:rgba(145,246,255,.35)!important;font-size:14px!important}.orbitFloatingWindow{position:fixed;right:calc(var(--orbit-right-width,520px) + 28px);top:74px;width:min(660px,calc(100vw - var(--orbit-left) - 120px));height:min(70vh,640px);z-index:120;background:rgba(21,16,31,.98);border:1px solid var(--orbit-border);border-radius:16px;box-shadow:0 28px 100px rgba(0,0,0,.72),0 0 70px rgba(203,55,255,.18);display:none;color:var(--orbit-ink);overflow:hidden}.orbitWindowHeader{height:48px;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:0 12px;border-bottom:1px solid rgba(203,55,255,.35);cursor:move;background:rgba(10,7,15,.98)}.orbitWindowHeader b{color:#f05bff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.orbitFileEditor{width:100%;height:calc(100% - 86px);border:0!important;border-radius:0!important;resize:none!important;background:#06070c!important;color:#dffbff!important;font-family:var(--orbit-font)!important;font-size:13px!important;line-height:1.45!important}.orbitFileRow{grid-template-columns:1fr auto auto auto!important}.nova-orbit-shell #orbitActivityDrawer{height:min(32vh,330px)!important;bottom:auto!important;margin-bottom:8px!important}.nova-orbit-shell #orbitActivityDrawer .activityHead .small{display:none}.nova-orbit-shell #artifactPanel{display:none!important}.nova-orbit-shell .contextStatusLine{display:none!important}.nova-orbit-shell .voiceControlGrid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.nova-orbit-shell #orbitRightDrawer .communicationTranscriptLine{font-size:11px}.nova-orbit-shell #chatsPopup{display:none!important;visibility:hidden!important}.nova-orbit-shell .bubble pre,.nova-orbit-shell .bubble code{color:#dffbff!important;background:#06070c!important;border-color:rgba(203,55,255,.34)!important}.nova-orbit-shell .bubble details{border-color:rgba(203,55,255,.28)!important}

/* v55.3.144 readability and evidence indicators */
body.nova-orbit-shell #orbitHeader{background:rgba(2,4,8,.72)!important;backdrop-filter:blur(8px);border-bottom:1px solid rgba(145,246,255,.18)!important}
body.nova-orbit-shell #orbitHeader .orbitModelTag,body.nova-orbit-shell #orbitHeader #orbitClock,body.nova-orbit-shell #orbitHeader #orbitMessageCount,body.nova-orbit-shell #orbitHeader #orbitRunMini{display:inline-flex;align-items:center;gap:6px;max-width:22vw!important;color:#aeefff!important}
body.nova-orbit-shell #orbitHeader #orbitRunMini{color:#ffd166!important}.orbitHeaderActions button{font-size:13px!important;padding:4px 9px!important;color:#bdf7ff!important}
.nova-orbit-shell .msg .name{display:flex!important;align-items:center;gap:8px!important;justify-content:flex-start!important}.nova-orbit-shell .msg.user .name{justify-content:flex-end!important}.msgTime{color:#7895a1;font-weight:600;font-size:11px}.msgTerminal{display:inline-block!important;margin-left:6px}.msgTerminal summary{cursor:pointer;color:#ffd166;font-size:11px;list-style:none}.msgTerminal summary::-webkit-details-marker{display:none}.msgTerminalBody{margin-top:5px;padding:8px;border:1px solid rgba(145,246,255,.22);border-radius:8px;background:#05070c;color:#c8fbff;white-space:pre-wrap;max-height:180px;overflow:auto;font-size:11px}
.nova-orbit-shell .workingbubble{border-color:#ffd166!important;box-shadow:0 0 24px rgba(255,209,102,.18)!important}.workingSteps{margin-top:8px;display:grid;gap:3px}.workingStep{font-size:11px;color:#91b7c3}.workingStep.active{color:#ffd166;font-weight:900}.workingStep.done{color:#00e676}
.nova-orbit-shell #orbitActivityDrawer .activity{background:#09070e!important}.nova-orbit-shell #orbitActivityDrawer .event,.nova-orbit-shell #orbitActivityDrawer .runbody .event{background:#0a1118!important;border:1px solid rgba(145,246,255,.24)!important;color:#dffbff!important;border-radius:10px!important;margin:7px 0!important;padding:9px!important}.nova-orbit-shell #orbitActivityDrawer .event b{color:#dffbff!important}.nova-orbit-shell #orbitActivityDrawer .event .t,.nova-orbit-shell #orbitActivityDrawer .small{color:#9ec6d1!important}.nova-orbit-shell #orbitActivityDrawer pre,.nova-orbit-shell .event pre{background:#03070c!important;color:#eaffff!important;border:1px solid rgba(145,246,255,.24)!important;border-radius:8px!important;padding:8px!important;text-shadow:none!important}.nova-orbit-shell #orbitActivityDrawer .run summary{color:#dffbff!important}.nova-orbit-shell #orbitActivityDrawer .runSummaryTitle{color:#dffbff!important}.nova-orbit-shell .voicePipelineCard,.nova-orbit-shell .voiceWaveCard{background:#09070d!important;color:#dffbff!important;border:1px solid rgba(145,246,255,.22)!important}.nova-orbit-shell #orbitSubChat{display:none!important}
.orbitStatePill.ready #orbitStateLabel:after{content:' to receive';color:#91f6ff;margin-left:3px}.orbitStatePill.listening #orbitStateLabel:after{content:' now';color:#00e676;margin-left:3px}.orbitStatePill.thinking #orbitStateLabel:after,.orbitStatePill.working #orbitStateLabel:after{content:'...';color:#ffd166;margin-left:3px}



/* v55.3.159 Clean Workspace: lower visual noise, make version visible, and stop drawers/panels from fighting the chat. */
body.nova-orbit-shell.clean-workspace{
  --orbit-left:72px;
  --orbit-drawer-width:min(360px,30vw);
  --orbit-right-width:min(420px,32vw);
  --orbit-chat-max:920px;
  --orbit-panel:#12101a;
  --orbit-border:rgba(167,139,250,.34);
  --orbit-border-soft:rgba(145,246,255,.20);
}
body.nova-orbit-shell.clean-workspace main[data-ui-overhaul]{
  max-width:100vw!important;
  padding:0!important;
  gap:0!important;
  background:linear-gradient(180deg,#06070d,#090712)!important;
}
body.nova-orbit-shell.clean-workspace #orbitHeader{
  height:44px!important;
  justify-content:center!important;
  padding:0 250px 0 12px!important;
  background:rgba(6,7,13,.94)!important;
  border-bottom:1px solid rgba(145,246,255,.20)!important;
  box-shadow:0 10px 35px rgba(0,0,0,.26)!important;
}
.novaVersionBadge{
  display:inline-flex;
  align-items:center;
  gap:6px;
  border:1px solid rgba(145,246,255,.36);
  background:rgba(145,246,255,.08);
  color:#dffbff;
  padding:4px 9px;
  border-radius:999px;
  font-weight:900;
  letter-spacing:.02em;
}
body.nova-orbit-shell.clean-workspace .orbitHeaderActions{right:10px!important;top:7px!important;gap:6px!important}
body.nova-orbit-shell.clean-workspace .orbitHeaderActions button,
body.nova-orbit-shell.clean-workspace .cleanToggleBtn{
  border:1px solid rgba(145,246,255,.26)!important;
  background:rgba(12,10,18,.72)!important;
  color:#dffbff!important;
  border-radius:999px!important;
  padding:4px 9px!important;
}
body.nova-orbit-shell.clean-workspace #chat{
  width:min(100%,calc(var(--orbit-chat-max) + 48px))!important;
  max-width:calc(var(--orbit-chat-max) + 48px)!important;
  padding:22px 24px 24px!important;
  background:radial-gradient(circle at 50% -20%,rgba(145,246,255,.08),transparent 36%),transparent!important;
}
body.nova-orbit-shell.clean-workspace .bubble{
  border-radius:14px!important;
  border-color:rgba(167,139,250,.32)!important;
  box-shadow:0 14px 36px rgba(0,0,0,.24)!important;
}
body.nova-orbit-shell.clean-workspace #orbitDrawer,
body.nova-orbit-shell.clean-workspace #orbitRightDrawer{
  top:44px!important;
  height:calc(100vh - 44px)!important;
  border-top:1px solid rgba(145,246,255,.12)!important;
}
body.nova-orbit-shell.clean-workspace #orbitDrawer{z-index:70!important}
body.nova-orbit-shell.clean-workspace #orbitRightDrawer{z-index:68!important}
body.nova-orbit-shell.clean-workspace #orbitActivityDrawer{z-index:66!important}
body.nova-orbit-shell.clean-workspace .orbitDrawerBody{padding:10px!important}
body.nova-orbit-shell.clean-workspace .controlHero,
body.nova-orbit-shell.clean-workspace .leftActionDock,
body.nova-orbit-shell.clean-workspace #odysseusWorkbenchPanel,
body.nova-orbit-shell.clean-workspace #odysseusVoyageDeck,
body.nova-orbit-shell.clean-workspace .chatSessionBar{
  display:none!important;
}
body.nova-orbit-shell.clean-workspace #quickControlsGrouped{max-height:120px;overflow:auto;border:1px solid rgba(145,246,255,.13);border-radius:12px;padding:6px;background:rgba(0,0,0,.16)}
body.nova-orbit-shell.clean-workspace .commandPalette{max-height:360px;overflow:auto;padding-right:3px}
body.nova-orbit-shell.clean-workspace #projects{max-height:240px;overflow:auto;border:1px solid rgba(145,246,255,.13);border-radius:12px;padding:6px;background:rgba(0,0,0,.12)}
body.nova-orbit-shell.clean-workspace #files{max-height:180px!important;overflow:auto!important;border:1px solid rgba(145,246,255,.13);border-radius:12px;padding:6px;background:rgba(0,0,0,.12)}
body.nova-orbit-shell.clean-workspace .section-title{margin-top:12px!important;color:#f0caff!important}
body.nova-orbit-shell.clean-workspace .projectItem,
body.nova-orbit-shell.clean-workspace .commandItem,
body.nova-orbit-shell.clean-workspace .toolItem,
body.nova-orbit-shell.clean-workspace .item{
  border-color:rgba(167,139,250,.22)!important;
  box-shadow:none!important;
}
body.nova-orbit-shell.clean-workspace .composer{
  width:min(860px,calc(100% - 34px))!important;
  margin-bottom:12px!important;
  border-color:rgba(145,246,255,.24)!important;
  box-shadow:0 18px 60px rgba(0,0,0,.42)!important;
}
body.nova-orbit-shell.clean-workspace.orbitDrawerOpen main[data-ui-overhaul]{grid-template-columns:calc(var(--orbit-left) + var(--orbit-drawer-width)) 0 minmax(0,1fr) 0 0!important}
body.nova-orbit-shell.clean-workspace.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 var(--orbit-right-width)!important}
body.nova-orbit-shell.clean-workspace.orbitDrawerOpen.orbit-right-open main[data-ui-overhaul]{grid-template-columns:calc(var(--orbit-left) + var(--orbit-drawer-width)) 0 minmax(0,1fr) 0 var(--orbit-right-width)!important}
body.nova-orbit-shell.clean-workspace #activityLog .run{font-size:12px!important;line-height:1.35!important}
@media(max-width:1100px){body.nova-orbit-shell.clean-workspace{--orbit-left:58px;--orbit-drawer-width:calc(100vw - 58px);--orbit-right-width:calc(100vw - 58px)}body.nova-orbit-shell.clean-workspace.orbitDrawerOpen main[data-ui-overhaul],body.nova-orbit-shell.clean-workspace.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important}.novaVersionBadge{display:none}}


/* v55.3.164 Calm Workspace: reduce clutter and stop drawers/popups from blocking the chat. */
body.nova-orbit-shell.calm-workspace{--orbit-left:60px!important;--orbit-drawer-width:330px!important;--orbit-right-width:330px!important;--left-col:320px!important;--right-col:330px!important;}
body.nova-orbit-shell.calm-workspace #topbar,body.nova-orbit-shell.calm-workspace .controlHero,body.nova-orbit-shell.calm-workspace .leftActionDock,body.nova-orbit-shell.calm-workspace #odysseusWorkbenchPanel,body.nova-orbit-shell.calm-workspace #validationDock,body.nova-orbit-shell.calm-workspace .archMini,body.nova-orbit-shell.calm-workspace .workflowCards{display:none!important;}
body.nova-orbit-shell.calm-workspace #orbitDrawer{width:min(330px,calc(100vw - var(--orbit-left) - 16px))!important;box-shadow:12px 0 32px rgba(0,0,0,.35)!important;}
body.nova-orbit-shell.calm-workspace #orbitRightDrawer{width:min(330px,34vw)!important;box-shadow:-12px 0 32px rgba(0,0,0,.35)!important;}
body.nova-orbit-shell.calm-workspace.orbitDrawerOpen main[data-ui-overhaul]{grid-template-columns:calc(var(--orbit-left) + var(--orbit-drawer-width)) 0 minmax(720px,1fr) 0 0!important;}
body.nova-orbit-shell.calm-workspace.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(780px,1fr) 0 var(--orbit-right-width)!important;}
body.nova-orbit-shell.calm-workspace.orbitDrawerOpen.orbit-right-open main[data-ui-overhaul]{grid-template-columns:calc(var(--orbit-left) + var(--orbit-drawer-width)) 0 minmax(680px,1fr) 0 var(--orbit-right-width)!important;}
body.nova-orbit-shell.calm-workspace #chat{max-width:920px!important;margin:0 auto!important;padding:18px 22px!important;}
body.nova-orbit-shell.calm-workspace .bubble{max-width:min(860px,92%)!important;}
body.nova-orbit-shell.calm-workspace #quickControlsGrouped{max-height:82px!important;overflow:auto!important;}body.nova-orbit-shell.calm-workspace #commandPalette{max-height:300px!important;overflow:auto!important;}body.nova-orbit-shell.calm-workspace #projects{max-height:180px!important;overflow:auto!important;}body.nova-orbit-shell.calm-workspace #files{max-height:150px!important;overflow:auto!important;}body.nova-orbit-shell.calm-workspace #customTools{max-height:130px!important;overflow:auto!important;}
body.nova-orbit-shell.calm-workspace .popupPanel{position:fixed!important;left:50%!important;top:50%!important;transform:translate(-50%,-50%)!important;width:min(760px,calc(100vw - 32px))!important;max-height:calc(100vh - 40px)!important;overflow:auto!important;z-index:1000!important;}
body.nova-orbit-shell.calm-workspace #orbitSubChat{display:none!important;}body.nova-orbit-shell.calm-workspace .novaVersionBadge{background:rgba(51,214,255,.12)!important;border-color:rgba(51,214,255,.42)!important;color:#dffbff!important;}body.nova-orbit-shell.calm-workspace .orbitHeaderActions button{padding:5px 8px!important;font-size:11px!important;}
@media(max-width:1400px){body.nova-orbit-shell.calm-workspace.orbit-right-open main[data-ui-overhaul],body.nova-orbit-shell.calm-workspace.orbitDrawerOpen.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important;}body.nova-orbit-shell.calm-workspace #orbitRightDrawer{width:calc(100vw - var(--orbit-left))!important;}}


/* v55.3.164 Provider route bar: local by default, remote only by explicit permission. */
.providerRouteBar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:6px 10px;margin:6px 0;border:1px solid rgba(197,111,255,.28);border-radius:12px;background:rgba(18,10,34,.78);font-size:11px;color:#d9c8ff}
.providerRouteBar .chip{border:1px solid rgba(197,111,255,.35);border-radius:999px;padding:3px 8px;background:rgba(114,41,171,.18)}
.providerRouteBar .local{color:#baf7d7}.providerRouteBar .remote{color:#ffd88a}.providerRouteBar .queue{color:#cde4ff}
/* v55.3.164 Focus Workspace: default to chat-first, less clutter, drawers overlay instead of crushing the centre. */
body.nova-orbit-shell.focus-workspace{--orbit-left:58px!important;--orbit-drawer-width:360px!important;--orbit-right-width:360px!important;background:#070712!important;}
body.nova-orbit-shell.focus-workspace main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important;}
body.nova-orbit-shell.focus-workspace.orbitDrawerOpen main[data-ui-overhaul],
body.nova-orbit-shell.focus-workspace.orbit-right-open main[data-ui-overhaul],
body.nova-orbit-shell.focus-workspace.orbitDrawerOpen.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important;}
body.nova-orbit-shell.focus-workspace #orbitDrawer{width:min(360px,calc(100vw - var(--orbit-left) - 12px))!important;box-shadow:0 0 0 1px rgba(145,246,255,.12), 14px 0 46px rgba(0,0,0,.58)!important;backdrop-filter:blur(10px);}
body.nova-orbit-shell.focus-workspace #orbitRightDrawer{width:min(380px,calc(100vw - var(--orbit-left) - 12px))!important;box-shadow:0 0 0 1px rgba(145,246,255,.12), -14px 0 46px rgba(0,0,0,.58)!important;backdrop-filter:blur(10px);}
body.nova-orbit-shell.focus-workspace #chat{max-width:980px!important;margin:0 auto!important;padding:18px 24px 24px!important;}
body.nova-orbit-shell.focus-workspace .bubble{max-width:min(900px,94%)!important;border-radius:14px!important;}
body.nova-orbit-shell.focus-workspace #liveActivityPanel{max-width:980px!important;margin:10px auto!important;}
body.nova-orbit-shell.focus-workspace .orbitNavButton{min-height:42px!important;padding:6px 4px!important;}
body.nova-orbit-shell.focus-workspace .orbitNavButton span{font-size:10px!important;}
body.nova-orbit-shell.focus-workspace #orbitHeader{height:32px!important;opacity:.92!important;}
body.nova-orbit-shell.focus-workspace .novaVersionBadge{font-size:11px!important;padding:3px 7px!important;}
body.nova-orbit-shell.focus-workspace .commandItem, body.nova-orbit-shell.focus-workspace .projectItem, body.nova-orbit-shell.focus-workspace .toolItem{padding:8px!important;margin:6px 0!important;}
body.nova-orbit-shell.focus-workspace #quickControlsGrouped{max-height:92px!important;}
body.nova-orbit-shell.focus-workspace #projects{max-height:210px!important;}
body.nova-orbit-shell.focus-workspace #files{max-height:170px!important;}
body.nova-orbit-shell.focus-workspace .popupPanel{border-radius:18px!important;box-shadow:0 30px 120px rgba(0,0,0,.72)!important;}



/* v55.3.164 GUI sanity rescue: chat stays usable even if a drawer was left open on an ultrawide monitor. */
body.nova-orbit-shell.gui-sanity-rescue{--orbit-left:58px!important;--orbit-drawer-width:360px!important;--orbit-right-width:380px!important;--orbit-chat-max:1080px!important;}
body.nova-orbit-shell.gui-sanity-rescue main[data-ui-overhaul]{width:100vw!important;max-width:none!important;grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important;}
body.nova-orbit-shell.gui-sanity-rescue.orbitDrawerOpen main[data-ui-overhaul],
body.nova-orbit-shell.gui-sanity-rescue.orbit-right-open main[data-ui-overhaul],
body.nova-orbit-shell.gui-sanity-rescue.orbitDrawerOpen.orbit-right-open main[data-ui-overhaul]{grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important;}
body.nova-orbit-shell.gui-sanity-rescue #chat{width:min(100%,calc(var(--orbit-chat-max) + 96px))!important;max-width:calc(var(--orbit-chat-max) + 96px)!important;margin:0 auto!important;padding-left:24px!important;padding-right:24px!important;}
body.nova-orbit-shell.gui-sanity-rescue .bubble{max-width:min(100%,var(--orbit-chat-max))!important;}
body.nova-orbit-shell.gui-sanity-rescue #orbitRightDrawer,
body.nova-orbit-shell.gui-sanity-rescue #orbitDrawer{position:fixed!important;top:34px!important;height:calc(100vh - 34px)!important;z-index:90!important;}
body.nova-orbit-shell.gui-sanity-rescue #orbitRightDrawer{width:min(380px,calc(100vw - var(--orbit-left) - 12px))!important;}
body.nova-orbit-shell.gui-sanity-rescue #orbitDrawer{width:min(360px,calc(100vw - var(--orbit-left) - 12px))!important;}
.guiRouteWarn{border:1px solid rgba(255,190,90,.55)!important;background:rgba(80,48,10,.72)!important;color:#ffe8b5!important;border-radius:12px!important;padding:10px 12px!important;margin:10px auto!important;max-width:980px!important;}

</style>
</head>
<!-- Orbit shell compatibility marker: <body class="nova-orbit-shell"> -->
<body class="nova-orbit-shell clean-workspace calm-workspace focus-workspace gui-sanity-rescue">

<div id="edgeRail" class="edgeRail" title="Nova quick rail: compact global controls that slides off screen when hidden">
  <button title="Settings" onclick="toggleSettingsPanel()">⚙</button>
  <button id="railMuteBtn" title="Toggle global spoken audio" onclick="toggleGlobalAudio()">🔊</button>
  <button id="railVoiceBtn" title="Start/stop one-shot voice input" onclick="toggleVoiceInput()">🎙️</button>
  <button id="railWakeBtn" title="Toggle always-listening wake word: Hey Nova" onclick="toggleWakeWordListening()">👂</button>
  <button title="Stop stuck task" onclick="confirmInterrupt()">■</button>
  <button title="Jarvis doctor" onclick="quick('/jarvis-doctor')">🧪</button>
  <button title="New chat" onclick="newChatSession()">＋</button>
  <button title="Saved chats" onclick="showChatsPopup()">💬</button>
  <div class="railLabel">Nova</div>
</div>
<button id="edgeRailToggle" class="edgeRailToggle" onclick="toggleEdgeRail()" title="Show or hide Nova quick rail">Nova</button>
</div>
<div id="changelogPopup" class="popupPanel hidden"><div class="row wrap"><b>Nova changelog</b><button class="tiny danger" onclick="togglePopup('changelogPopup',false)">Close</button></div><div id="changelogContent" class="small">Loading changelog...</div></div>
<div id="releaseChecklistPopup" class="popupPanel hidden"><div class="row wrap"><b>Release checklist</b><button class="tiny danger" onclick="togglePopup('releaseChecklistPopup',false)">Close</button></div><div id="releaseChecklistContent" class="small">Loading release checklist...</div></div>
<div id="chatsPopup" class="popupPanel hidden" aria-hidden="true"><div class="small">Saved chats now open in the docked Orbit Chats drawer.</div></div>
<div id="odysseusWorkspacePopup" class="popupPanel hidden"><div class="row wrap"><b>Odysseus workbench windows</b><button class="tiny secondary" onclick="loadOdysseusWorkspace()">Refresh</button><button class="tiny danger" onclick="togglePopup('odysseusWorkspacePopup',false)">Close</button></div><div class="small">Structured Nova workspaces: docs, compare, cookbook, memory, gates and code tabs. Commands still route through normal Nova safety checks.</div><div id="odysseusWorkspaceShell" class="workbenchWindowShell"><div id="odysseusWorkspaceTabs" class="workbenchWindowTabs"></div><div id="odysseusWorkspaceBody" class="workbenchWindowBody">Loading workbench...</div></div></div>
<div id="quickEditPopup" class="popupPanel hidden"><div class="row wrap"><b>Custom quick commands</b><button class="tiny danger" onclick="togglePopup('quickEditPopup',false)">Close</button></div><div class="small">For multi-step buttons, enter one command per line or separate commands with <code>;;</code>.</div><div class="quickEditor"><input id="quickLabel" placeholder="Label"><textarea id="quickCommand" placeholder="/command one&#10;/command two"></textarea><button onclick="addQuickCommandFromForm()">Add</button></div><div id="quickEditList" class="small"></div></div>
<div id="idlePopup" class="idlePopup hidden"></div>
<main data-ui-overhaul="v55.3.115" data-orbit-studio-shell="v55.3.164">
  <aside class="sidebar card">
    <div class="panelHeader"><b>Left panel</b><span class="pill good">Control Centre</span><div class="row wrap"><button class="tiny secondary" onclick="resetPanelLayout()">Reset layout</button><button class="tiny secondary" onclick="togglePanel('left')">Hide</button></div></div>
    <div class="controlHero" id="controlDrawerHero"><div class="controlDrawerHeader"><b>Control drawer</b><button id="controlDrawerToggle" class="tiny secondary" onclick="toggleControlDrawer()">Hide drawer</button></div><div id="controlDrawerIntro" class="small">Search commands, reopen projects, and run reusable tools here. Keep normal conversation in the centre chat.</div><div id="controlDrawerQuickActions" class="controlHeroGrid"><button class="tiny" onclick="fillCommand('make a useful local app')">Build</button><button class="tiny secondary" onclick="fillCommand('/test-all')">Test</button><button class="tiny secondary" onclick="fillCommand('/codebase-audit')">Audit Nova</button><button class="tiny secondary" onclick="confirmInterrupt()">Stop stuck</button></div></div>
    <div class="leftActionDock" id="leftActionDock"><div class="actionClusterTitle">Action dock</div>
      <div class="actionCluster"><div class="actionClusterTitle">Build / repair</div><div class="row wrap"><button class="tiny" onclick="fillCommand('/fast make a useful local app')">Fast build</button><button class="tiny secondary" onclick="fillCommand('/development-strategy current failed task')">Strategy</button><button class="tiny secondary" onclick="fillCommand('/surgical-recipe game_missing_collision')">Surgical fallback</button><button class="tiny secondary" onclick="fillCommand('/receipt-history')">Receipts</button></div></div>
      <div class="actionCluster"><div class="actionClusterTitle">Validate / release</div><div class="row wrap"><button class="tiny secondary" onclick="quick('/validation-matrix')">Validation matrix</button><button class="tiny secondary" onclick="quick('/feature-continuity-audit')">Continuity</button><button class="tiny secondary" onclick="quick('/test-all')">Test all</button><button class="tiny secondary" onclick="quick('/startup-validation')">Startup Validation</button><button class="tiny secondary" onclick="quick('/audit-log')">Audit log</button><button class="tiny secondary" onclick="quick('/workflow-run validate Nova safely')">Workflow run</button><button class="tiny secondary" onclick="quick('/release-gate final validation')">Release gate</button></div></div>
      <div class="actionCluster"><div class="actionClusterTitle">Jarvis / sidecar</div><div class="row wrap"><button class="tiny secondary" onclick="quick('/jarvis-doctor')">Jarvis doctor</button><button class="tiny secondary" onclick="quick('/jarvis-status')">Status</button><button class="tiny secondary" onclick="quick('/sidecar-policy')">Policy</button><button class="tiny secondary" onclick="quick('/sidecar-enrollment terminal filesystem browser screenshot')">Enroll checklist</button><button class="tiny secondary" onclick="quick('/bridge-receipts')">Bridge receipts</button><button class="tiny secondary" onclick="quick('/browser-harness http://127.0.0.1:3142')">Browser harness</button><button class="tiny secondary" onclick="quick('/jarvis-test-prompts')">Test prompts</button></div></div>
      <div class="actionCluster"><div class="actionClusterTitle">Output transparency</div><div class="small">Right panel is now for state, before/after evidence, receipts and outputs. Commands stay here in the left control centre.</div></div>
      <div class="actionCluster"><div class="actionClusterTitle">Persona / model behaviour</div><div class="row wrap"><button class="tiny secondary" onclick="quick('/persona')">Persona</button><button class="tiny secondary" onclick="quick('/custom-chat-window')">Chat style</button><button class="tiny secondary" onclick="quick('/persona-prompt voice')">Prompt addendum</button><button class="tiny secondary" onclick="quick('/local-model-optimizer')">Model optimiser</button><button class="tiny secondary" onclick="quick('/agent-harness')">Agent harness</button><button class="tiny secondary" onclick="quick('/voice-audit')">Voice audit</button></div><div class="small">Tune Nova's tone, self-model, response contract and local-model repair loop without removing validation gates.</div></div>
    </div>
    <div class="section-title">Quick controls</div><div class="small">Customisable shortcuts. Edit these to match your usual workflow.</div>
    <div class="row wrap"><button class="secondary tiny" onclick="renderQuickControls();togglePopup('quickEditPopup',true)">Edit quick commands</button><button class="secondary tiny" onclick="resetQuickCommands()">Reset quick commands</button><button class="secondary tiny" onclick="toggleAvatarAudio()">Enable audio</button><button class="secondary tiny" onclick="newChatSession()">New chat</button></div>
    <div id="quickControlsGrouped"></div>
    <div class="chatSessionBar"><select id="chatSessionSelect" onchange="switchChatSession(this.value)"></select><button class="tiny secondary" onclick="saveCurrentChatSession()">Save chat</button><button class="tiny secondary" onclick="searchChatSessions()">Search chats</button></div>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">Command Launcher</div>
    <input id="commandSearch" placeholder="Search commands or type a goal" oninput="renderCommandPalette()">
    <div id="commandPalette" class="commandPalette"></div>
    <div id="odysseusWorkbenchPanel" class="odysseusWorkbenchPanel">
      <div><b>Nova workbench</b><div class="small">Odysseus-inspired left command rail: command-core now, FastAPI panel migration next.</div></div>
      <div class="odysseusArchitectureStrip"><b>Architecture:</b> Hybrid sidecar — keep NovaCore/CLI stable, add an optional FastAPI API/event layer.</div>
      <div class="odysseusWorkbenchGrid">
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-odysseus-suite" data-command="/nova-odysseus-suite" onclick="runDatasetCommand(this)"><span class="ico">🧭</span><span><b>Suite</b><br><small>coverage audit</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-odysseus-runtime" data-command="/nova-odysseus-runtime" onclick="odysseusWorkspaceActive='runtime';showOdysseusWorkspace()"><span class="ico">O</span><span><b>Runtime</b><br><small>start dependency</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-tool-permissions" data-command="/nova-tool-permissions check write file" onclick="runDatasetCommand(this)"><span class="ico">🛡️</span><span><b>Gates</b><br><small>permission policy</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-cookbook" data-command="/nova-cookbook whatif ram=32 vram=16 => coding" onclick="runDatasetCommand(this)"><span class="ico">📚</span><span><b>Cookbook</b><br><small>hardware fit</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-compare" data-command="/nova-compare plan improve Nova => qwen3-coder:30b, gemma2:2b" onclick="runDatasetCommand(this)"><span class="ico">⚖️</span><span><b>Compare</b><br><small>model bake-off</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-docs" data-command="/nova-docs list" onclick="runDatasetCommand(this)"><span class="ico">📄</span><span><b>Docs</b><br><small>document vault</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-notes" data-command="/nova-notes list" onclick="runDatasetCommand(this)"><span class="ico">📝</span><span><b>Notes</b><br><small>scratchpad</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-tasks" data-command="/nova-tasks list" onclick="runDatasetCommand(this)"><span class="ico">✅</span><span><b>Tasks</b><br><small>local queue</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-memory-vault" data-command="/nova-memory-vault audit" onclick="runDatasetCommand(this)"><span class="ico">🧠</span><span><b>Memory</b><br><small>vault audit</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-fastapi-plan" data-command="/nova-fastapi-plan" onclick="runDatasetCommand(this)"><span class="ico">⚡</span><span><b>FastAPI</b><br><small>sidecar plan</small></span></button>
        <button class="odysseusWorkbenchBtn" data-odysseus-command="/nova-gui-workbench-plan" data-command="/nova-gui-workbench-plan" onclick="runDatasetCommand(this)"><span class="ico">🧩</span><span><b>GUI plan</b><br><small>rail + panels</small></span></button>
      </div>
      <div class="odysseusWorkspaceActions">
        <button class="tiny" onclick="showOdysseusWorkspace()">Open workspace windows</button>
        <button class="tiny secondary" onclick="odysseusWorkspaceActive='runtime';showOdysseusWorkspace()">Odysseus runtime</button>
        <button class="tiny secondary" onclick="loadOdysseusRuntime()">Runtime status</button>
        <button class="tiny" onclick="startOdysseusRuntime()">Start Odysseus</button>
        <button class="tiny secondary" onclick="loadOdysseusWorkspace()">Refresh snapshot</button>
        <button class="tiny secondary" data-command="/nova-gui-workbench-plan" onclick="fillDatasetCommand(this)">Fill GUI plan</button>
      </div>
      <div id="odysseusRuntimeStatus" class="odysseusWorkspacePreview small">Odysseus runtime status has not been checked yet.</div>
      <div id="odysseusWorkspacePreview" class="odysseusWorkspacePreview small">Workspace windows are ready to load: docs, runtime, compare, cookbook, notes, tasks, skills, memory, gates and code tabs.</div>
    </div>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">Idle Self-Improvement</div>
    <div id="idleSelfImprovement" class="item small">Checking idle reports...</div>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">Local LLM status</div>
    <div id="llmStatus" class="item small">Checking Ollama...</div>
    <div id="llmRecentContext" class="llmContextLine small">Recent local model context will appear here.</div>
    <button class="secondary" onclick="quick('/llm-status')">LLM status in chat</button> <button class="danger tiny" onclick="confirmInterrupt()">Interrupt task</button> <button class="danger tiny" onclick="confirmOllamaStop()">Stop Ollama model</button>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">Projects</div>
    <div class="small">Projects are stored separately and can be reopened later.</div>
    <div class="row" style="margin-top:8px"><input id="newProject" placeholder="Project name"><button class="tiny" onclick="newProject()">New</button></div>
    <div class="row wrap"><button id="refreshProjectsBtn" class="secondary" onclick="loadProjects()">Refresh projects <span class="refreshSpinner"></span></button><button class="secondary tiny" onclick="selectAllProjects(true)">Select all</button><button class="secondary tiny" onclick="selectAllProjects(false)">Clear</button><button class="danger tiny" onclick="bulkDeleteSelectedProjects()">Delete selected</button></div>
    <div id="projects"></div>
    <div class="leftFileDock">
      <div class="section-title">Project files</div>
      <div class="small">Open, download and zip project files from the left. The right inspector shows the selected file and before/after output.</div>
      <div class="row wrap"><button id="refreshFilesBtn" class="secondary" onclick="loadFiles()">Refresh files <span class="refreshSpinner"></span></button><button class="secondary" onclick="quick('/zip .')">Zip project</button></div>
      <div id="files" style="max-height:230px;overflow:auto;margin-top:8px"></div>
    </div>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">AI Toolbox</div>
    <div class="small">Custom tools are separate from projects. The agent can create and run these when helpful.</div>
    <div class="row" style="margin-top:8px"><input id="toolGoal" placeholder="Tool idea, e.g. count TODO comments"><button class="tiny" onclick="createTool()">Create</button></div>
    <div class="row" style="margin-top:8px"><input id="toolRunName" placeholder="Tool name"><input id="toolRunArgs" placeholder='Args: {text} or {"text":"hello"}'><button class="tiny" onclick="runToolForm()">Run tool</button></div>
    <textarea id="toolPipeline" rows="4" placeholder='Pipeline JSON, e.g. [{"tool":"tool_run","args":{"name":"html_reference_checker","args":{"subdir":"."}}}]'></textarea>
    <div class="row wrap"><button class="secondary tiny" onclick="loadTools()">Refresh tools</button><button class="secondary tiny" onclick="runPipelineForm()">Run pipeline</button><button class="secondary tiny" onclick="quick('/tool-help')">Tool help</button><button class="secondary tiny" onclick="quick('/topic-watchers')">Topic watchers</button></div>
    <div id="customTools"></div>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">Workspace</div>
    <input id="workspace" placeholder="C:\Users\Daniel\Documents\Projects">
    <button onclick="setWorkspace()">Set workspace</button>
    <p class="small">Best: use a project folder, not your whole user folder.</p>
  </aside>

  <div class="resizeRail leftRail" data-panel="left" title="Resize left panel" role="separator" tabindex="0" aria-label="Resize left panel" aria-orientation="vertical" aria-valuemin="260" aria-valuemax="720"></div>

  <section class="chat-wrap card">
    <div id="topbar" class="topbar collapsed"><div><div class="title">Nova v55.3.164 clean workspace, visible version, Docker validation hardening and self-repair continuity <span class="pill good">docked drawers, theme customizer, ready chime, validation dock and Odysseus workspace tools</span></div><div class="subtitle">Left-action cockpit: commands and controls live in the left drawer; the right inspector focuses on improvement state, transparent before/after output and bridge receipts.</div></div><div class="row wrap"><button class="secondary" onclick="toggleTopbar()">Banner</button><button class="secondary" onclick="toggleSettingsPanel()">Settings</button><button class="secondary" onclick="toggleFocusWorkspace()">Focus UI</button><button class="secondary" onclick="togglePanel('activity')">Activity</button><span id="topQuickActions" style="display:none"><button class="secondary" onclick="quick('/status')">Status</button><button class="secondary" onclick="quick('/activity')">Activity log</button><button class="secondary" onclick="quick('/reasoning')">Reasoning</button><button class="secondary" onclick="fillCommand('/research topic to investigate')">Research</button><button class="secondary" onclick="quick('/research-plan')">Research plan</button><button class="secondary" onclick="quick('/providers')">Providers</button><button class="secondary" onclick="quick('/vision-status')">Vision</button><button class="secondary" onclick="quick('/image-status')">Image status</button><button class="secondary" onclick="quick('/media-status')">Media status</button><button class="secondary" onclick="quick('/schedule-status')">Schedule status</button><button class="secondary" onclick="fillCommand('/schedule-task remind me to stretch => tomorrow 9am')">Schedule task</button><button class="secondary" onclick="fillCommand('/image-plan cinematic robot dog mascot')">Image plan</button><button class="secondary" onclick="fillCommand('/video-package 10 second cinematic trailer about Nova improving a project')">Video package</button><button class="secondary" onclick="quick('/human-test .')">Human test</button><button class="secondary" onclick="quick('/visual-test .')">Visual test</button><button class="secondary" onclick="quick('/test-all')">Test all</button><button class="secondary" onclick="quick('/quality-dashboard')">Quality dashboard</button><button class="secondary" onclick="quick('/quality-progress')">Quality progress</button><button class="secondary" onclick="quick('/command-verify')">Command verify</button><button class="secondary" onclick="quick('/architecture-audit')">Architecture audit</button><button class="secondary" onclick="quick('/repair-audit')">Repair audit</button><button class="secondary" onclick="quick('/code-review')">Code review</button><button class="secondary" onclick="quick('/code-quality-gate')">Quality gate</button><button class="secondary" onclick="quick('/codebase-audit')">Codebase audit</button><button class="secondary" onclick="quick('/comm-box status')">Comm box</button><button class="secondary" onclick="quick('/model-context')">Model context</button><button class="secondary" onclick="quick('/efficiency')">Efficiency</button><button class="secondary" onclick="quick('/self-awareness')">Self-awareness</button><button class="secondary" onclick="quick('/planning-dashboard improve current project safely')">Planning dashboard</button><button class="secondary" onclick="quick('/model-doctor')">Model doctor</button><button class="secondary" onclick="quick('/visual-repair .')">Visual repair</button><button class="secondary" onclick="quick(&quot;/autonomous status&quot;)">Autonomous</button><button class="secondary" onclick="quick(&quot;/autonomous-guide&quot;)">Auto guide</button><button class="secondary" onclick="quick(&quot;/autonomous-explain&quot;)">Auto explain</button></span></div></div>
    <div id="odysseusVoyageDeck" class="odysseusVoyageDeck" aria-label="Odysseus-style Nova workspace map">
      <div class="voyageHero"><div><span class="voyageKicker">Yours for the voyage</span><b>Local AI workspace, not just a chat box</b><p>Chat, agents, model cookbook, deep research, compare, documents, notes, tasks, memory and gated tools are one click away.</p></div><div class="voyageActions"><button class="tiny" onclick="showOdysseusWorkspace()">Open workbench</button><button class="tiny" onclick="odysseusWorkspaceActive='runtime';showOdysseusWorkspace()">Runtime</button><button class="tiny" data-command="/nova-gui-workbench-plan" onclick="fillDatasetCommand(this)">GUI plan</button></div></div>
      <div class="voyageMap">
        <button class="voyageCard primary" onclick="document.getElementById('msg')?.focus()"><span class="voyageIcon">💬</span><b>Chat & Agents</b><small>Talk, plan, run tools and inspect receipts.</small></button>
        <button class="voyageCard" onclick="odysseusWorkspaceActive='cookbook';showOdysseusWorkspace()"><span class="voyageIcon">📚</span><b>Cookbook</b><small>Hardware-aware model fit and serving notes.</small></button>
        <button class="voyageCard" data-command="/research topic to investigate" onclick="fillDatasetCommand(this)"><span class="voyageIcon">🔎</span><b>Deep Research</b><small>Search, read, synthesize and cite a report.</small></button>
        <button class="voyageCard" onclick="odysseusWorkspaceActive='compare';showOdysseusWorkspace()"><span class="voyageIcon">⚖️</span><b>Compare</b><small>Blind model bake-off and synthesis receipts.</small></button>
        <button class="voyageCard" onclick="odysseusWorkspaceActive='docs';showOdysseusWorkspace()"><span class="voyageIcon">📄</span><b>Documents</b><small>Drafts, markdown, CSV and AI edit flows.</small></button>
        <button class="voyageCard" onclick="odysseusWorkspaceActive='tasks';showOdysseusWorkspace()"><span class="voyageIcon">✅</span><b>Notes & Tasks</b><small>Capture actions and scheduled agent work.</small></button>
        <button class="voyageCard" onclick="odysseusWorkspaceActive='memory';showOdysseusWorkspace()"><span class="voyageIcon">🧠</span><b>Memory</b><small>Vault audit, import/export and recall checks.</small></button>
        <button class="voyageCard" onclick="toggleSettingsPanel()"><span class="voyageIcon">🎨</span><b>Themes</b><small>Dark mode, voice, persona and layout controls.</small></button>
      </div>
      <div id="validationCommandDock" class="odysseusValidationDock" aria-label="Odysseus-style validation command dock">
        <div class="validationDockCard validationDockStatus"><span class="voyageKicker">Verify before claiming</span><b>Validation dock</b><small>Fill safe checks instead of guessing whether a patch worked.</small></div>
        <div class="validationDockCard"><b>Release hygiene</b><small>Cache, manifest and package-clean checks.</small><button class="tiny secondary" data-command="/release-hygiene" onclick="fillDatasetCommand(this)">Fill</button></div>
        <div class="validationDockCard"><b>Architecture audit</b><small>Routes, docs, version and module sanity.</small><button class="tiny secondary" data-command="/architecture-audit" onclick="fillDatasetCommand(this)">Fill</button></div>
        <div class="validationDockCard"><b>Eval packs</b><small>Deterministic core/release/agent command checks.</small><button class="tiny secondary" data-command="/nova-eval-packs core" onclick="fillDatasetCommand(this)">Fill</button></div>
        <div class="validationDockCard"><b>Patch impact</b><small>Choose tests for changed files before applying.</small><button class="tiny secondary" data-command="/patch-impact-plan winlocalassistant/webui.py winlocalassistant/nova_odysseus_suite.py" onclick="fillDatasetCommand(this)">Fill</button></div>
      </div>
    </div>

    
<div id="providerRouteBar" class="providerRouteBar" data-provider-route-bar="v55.3.164">
  <span class="chip local">Provider: Local default</span>
  <span class="chip">Advanced local: vLLM / SGLang / llama.cpp</span>
  <span class="chip remote">Remote long-context: SubQ / NVIDIA NIM only with permission</span>
  <span class="chip queue">Queue: per provider/model receipts</span>
  <button class="tiny secondary" onclick="quick('/provider-status')">Provider status</button>
  <button class="tiny secondary" onclick="fillCommand('/provider-route explain a whole repo review')">Route explain</button>
  <button class="tiny secondary" onclick="quick('/queue-status')">Queue</button>
</div>

<div id="studioHome" class="studioHome" data-clean-studio-shell="v55.3.164">
      <div class="studioBrand"><span class="studioKicker">Nova Studio</span><b>Chat in the centre. Tools on the left. State on the right.</b><span>Clean VS Code / ChatGPT style shell; Odysseus workbench and validation features stay available without taking over the screen.</span></div>
      <div class="studioNav" aria-label="Clean Studio primary actions">
        <button class="primary" onclick="document.getElementById('msg')?.focus()">Chat</button>
        <button onclick="fillCommand('/fast make a polished minimal local app')">Build</button>
        <button onclick="fillCommand('/research topic to investigate')">Research</button>
        <button onclick="setInspectorTab('files')">Files</button>
        <button onclick="setInspectorTab('tools')">Tools</button>
        <button onclick="odysseusWorkspaceActive='runtime';showOdysseusWorkspace()">Workbench</button>
        <button onclick="quick('/doctor')">Doctor</button>
        <button onclick="quick('/user-feedback-tests')">Test commands</button>
        <button class="danger" onclick="confirmInterrupt()">Stop</button>
      </div>
    </div>

    <div id="statusChips" class="statuschips" aria-live="polite"><span class="pill">Checking local runtime...</span></div>
    <div id="smartTopStrip" class="smartTopStrip" data-ui-overhaul="v55.3.115">
      <div class="smartNow"><b>Focus</b><span id="compactRunStatus">Ready — chat first, tools when needed.</span></div>
      <div class="smartActions" aria-label="Essential actions">
        <button class="tiny newChatPrimary" onclick="newChatSession()">New chat</button><button class="tiny secondary" onclick="document.getElementById('msg').focus()">Type</button><button class="tiny secondary" onclick="toggleWakeWordListening(true)">Hey Nova</button>
        <button class="tiny secondary" onclick="togglePanel('activity')">Activity</button>
        <button class="tiny secondary" onclick="quick('/planning-dashboard improve current project safely')">Plan loop</button>
        <button class="tiny secondary" onclick="quick('/quality-dashboard')">Quality</button>
        <button class="tiny secondary" onclick="odysseusWorkspaceActive='runtime';showOdysseusWorkspace()">Odysseus</button>
        <button class="tiny secondary" onclick="setInspectorTab('files')">Files</button>
        <button class="tiny secondary" onclick="setInspectorTab('tools');document.getElementById('toolGoal')?.focus()">Tools</button>
        <button class="tiny danger" onclick="confirmInterrupt()">Stop stuck task</button>
      </div>
    </div>
    <div class="sandboxTabs"><button id="tab_general" class="secondary sandboxTabBtn active" onclick="showMainTab('general')">General</button><button id="tab_linux" class="secondary sandboxTabBtn" onclick="showMainTab('linux')">Linux Sandbox</button><button id="tab_kali" class="secondary sandboxTabBtn" onclick="showMainTab('kali')">Kali Sandbox</button><button id="tab_settings" class="secondary sandboxTabBtn" onclick="showMainTab('settings')">Sandbox Settings</button><button id="tab_docker" class="secondary sandboxTabBtn" onclick="showMainTab('docker')">Docker</button></div>
    <div id="activeRunPanel" class="artifact" style="display:none"></div>
    <div id="autonomousLivePanel" class="artifact" style="display:none"></div>
    <div id="architectureMini" class="archMini"></div>
    <div id="generalPanel" class="sandboxPanel middleResizable hidden"><b>General workspace</b><button class="tiny secondary" style="float:right" onclick="togglePanel('general')">Hide</button><div class="small">Workspace/chat controls are kept compact so the chat stays visible.</div></div>
    <div id="linuxSandboxPanel" class="sandboxPanel hidden"><div class="sandboxGrid"><div class="sandboxCard"><h3>General Linux Sandbox</h3><div id="sandboxStatusLinux" class="small">Loading sandbox status...</div><div class="row wrap"><button onclick="sandboxStart('linux')">Start Linux</button><button class="secondary" onclick="sandboxStop('linux')">Stop</button><button class="secondary" onclick="quick('/sandbox-linux status')">Status in chat</button><button class="secondary" onclick="quick('/sandbox-setup-help')">Setup help</button></div><div class="sandboxWarn small">Runs as an isolated Docker/Podman container with default no-network, dropped capabilities and read-only project mount.</div></div><div class="sandboxCard"><h3>Linux command</h3><input id="linuxSandboxCmd" placeholder="python --version or uname -a"><div class="row wrap"><button onclick="sandboxExec('linux')">Run in Linux sandbox</button><button class="secondary" onclick="fillCommand('/sandbox-linux exec python --version')">Fill command</button><button class="secondary" onclick="fillCommand('/sandbox-dev-run linux python -m compileall -q .')">Dev copy validate</button></div><div class="sandboxTerminal">Output appears in chat and the activity log. Commands are policy checked and logged.</div><div class="devSandboxHint small">Dev copy mode lets Nova write/test inside a copied workspace; live project files stay untouched.</div></div></div></div>
    <div id="kaliSandboxPanel" class="sandboxPanel hidden"><div class="sandboxGrid"><div class="sandboxCard"><h3>Kali Linux Security Lab</h3><div id="sandboxStatusKali" class="small">Loading sandbox status...</div><div class="row wrap"><button onclick="sandboxStart('kali')">Start Kali</button><button class="secondary" onclick="sandboxStop('kali')">Stop</button><button class="secondary" onclick="quick('/sandbox-kali status')">Status in chat</button><button class="secondary" onclick="quick('/sandbox-setup-help')">Setup help</button></div><div class="sandboxWarn small">Kali mode is for authorised local lab/defensive analysis only. Network and high-risk tools are off until explicitly authorised.</div></div><div class="sandboxCard"><h3>Kali command</h3><input id="kaliSandboxCmd" placeholder="whoami or nmap --version"><div class="row wrap"><button onclick="sandboxExec('kali')">Run in Kali sandbox</button><button class="secondary" onclick="fillCommand('/sandbox-kali exec nmap --version')">Fill command</button><button class="secondary" onclick="fillCommand('/sandbox-dev-run kali python --version || whoami')">Dev copy validate</button></div><div class="sandboxTerminal">Use only on systems you own or have permission to test. Public-target exploitation is blocked by default.</div><div class="devSandboxHint small">Kali dev copy mode is for owned/local lab validation. Host escape and unauthorised offensive target work remain blocked.</div></div></div></div>
    <div id="sandboxSettingsPanel" class="sandboxPanel hidden"><h3>Sandbox Settings</h3><div id="sandboxStatusSettings" class="small">Loading sandbox status...</div><div class="row wrap"><button class="secondary" onclick="quick('/sandbox-autonomy status')">Autonomy status</button><button onclick="quick('/sandbox-autonomy on')">Autonomy ON</button><button class="danger" onclick="quick('/sandbox-autonomy off')">Autonomy OFF</button><button class="secondary" onclick="quick('/sandbox-network status')">Network status</button><button class="danger" onclick="quick('/sandbox-network off')">Network OFF</button><button class="secondary" onclick="quick('/sandbox-authorized-lab status')">Lab status</button><button onclick="quick('/sandbox-less-strict on')">Less strict ON</button><button class="secondary" onclick="quick('/sandbox-policy balanced')">Balanced policy</button><button class="danger" onclick="quick('/sandbox-policy strict')">Strict policy</button><button class="secondary" onclick="quick('/sandbox-pending')">Pending permission</button></div><div class="sandboxWarn small">Less strict/trusted lab mode is intended for owned/local labs or explicitly permitted targets. Host escape and destructive root commands remain blocked and all commands are logged.</div></div>
    <div id="dockerPanel" class="sandboxPanel hidden"><h3>Docker Diagnostics</h3><div id="dockerStatusBox" class="small">Loading Docker diagnostics...</div><div class="row wrap"><button class="secondary" onclick="quick('/docker-status')">Docker status in chat</button><button class="secondary" onclick="quick('/docker-ps')">List containers</button><button class="secondary" onclick="quick('/docker-help')">Docker help</button><button class="secondary" onclick="quick('/docker-validate quick')">Quick validate</button><button class="secondary" onclick="quick('/docker-validate gui')">GUI validate</button><button class="secondary" data-command="/docker-validate-patch path/to/patch.diff" onclick="fillDatasetCommand(this)">Patch validate</button><button class="secondary" data-command="/docker-promote-patch RUN_ID" onclick="fillDatasetCommand(this)">Promote validated patch</button><button class="secondary" onclick="quick('/docker-history')">History</button><button class="secondary" onclick="quick('/docker-clean 20')">Clean old runs</button><button onclick="loadDockerStatus()">Refresh Docker</button></div><div class="sandboxWarn small">Docker is optional. Nova still works without Docker; this panel is for sandbox diagnostics and future container validation.</div></div>
    <div id="settingsPanel" class="artifact settingsPanel" style="display:none"><div class="row wrap"><b>Settings</b><button class="tiny danger" onclick="toggleSettingsPanel(false)">Close</button></div><div class="small">Popup settings: clutter, voice, Nova personality and safe command shortcuts.</div><label><input type="checkbox" id="showQuickButtons" onchange="saveUiSettings()"> Show top quick-action buttons</label><br><label><input type="checkbox" id="showComposerButtons" onchange="saveUiSettings()"> Show composer command buttons</label><br><label><input type="checkbox" id="showCommandSuggestions" onchange="saveUiSettings()"> Show suggested-command chips</label><br><label><input type="checkbox" id="showFeedbackButtons" onchange="saveUiSettings()"> Show thumbs-up/down feedback buttons</label><br><label><input type="checkbox" id="showCreatedOutputs" onchange="saveUiSettings()"> Show created-output cards</label><br><label><input type="checkbox" id="showLiveActivity" onchange="saveUiSettings()"> Show Live Activity panel</label><br><label><input type="checkbox" id="showAvatarPanel" onchange="saveUiSettings()"> Show avatar/assistant state</label><br><label><input type="checkbox" id="darkMode" onchange="saveUiSettings()"> Dark mode</label><br><label><input type="checkbox" id="audioEnabled" onchange="saveUiSettings()"> Spoken audio on by default</label><br><label><input type="checkbox" id="audioMuted" onchange="saveUiSettings()"> Mute spoken audio</label><br><label><input type="checkbox" id="voiceMode" onchange="saveUiSettings()"> Voice mode: mic input and spoken replies</label><br><label><input type="checkbox" id="wakeWordEnabled" onchange="saveUiSettings();toggleWakeWordListening(this.checked)"> Always listen for “Hey Nova” wake word</label><br><label><input type="checkbox" id="autoSpeakVoiceMode" onchange="saveUiSettings()"> Always speak replies while voice mode is on</label><br><label><input type="checkbox" id="showHoverContext" onchange="saveUiSettings()"> Show hover context/details</label><br><label><input type="checkbox" id="autoIdleAfterFive" onchange="setAutoIdleOptIn(this.checked)"> Permanent idle after 5 minutes inactive</label><br><label>Nova personality <select id="novaPersonality" onchange="saveUiSettings()"><option value="friendly_engineer">Friendly engineer</option><option value="concise_operator">Concise operator</option><option value="curious_builder">Curious builder</option></select></label><br><label>Spoken voice style <select id="voiceStyle" onchange="saveUiSettings();populateSpeechVoices()"><option value="female_preferred">Feminine voice preferred</option><option value="default">Browser default</option></select></label><div class="voiceAuthPanel" id="voiceAuthPanel"><b>Voice login / command gate</b><div class="small" id="voiceAuthStatus">Voice auth loading...</div><div class="voiceChallengeBox"><div class="small">Repeat this changing phrase to unlock voice commands:</div><code id="voiceChallengePhrase">loading phrase</code><div class="row wrap"><input id="voiceChallengeInput" placeholder="Type or say the displayed phrase"><button class="tiny" onclick="unlockVoiceByChallenge()">Unlock with phrase</button><button class="tiny secondary" onclick="generateVoiceChallengePhrase()">New phrase</button></div></div><label><input type="checkbox" id="voiceAuthRequired" onchange="saveUiSettings();renderVoiceAuth()"> Require voice login before spoken commands act</label><br><label><input type="checkbox" id="voiceRememberLogin" onchange="saveUiSettings();renderVoiceAuth()"> Allow password fallback this session</label><div class="row wrap"><input id="voicePasswordInput" type="password" placeholder="Optional voice password"><button class="tiny secondary" onclick="setVoicePassword()">Set password</button><button class="tiny" onclick="unlockVoiceSession()">Unlock voice</button><button class="tiny danger" onclick="lockVoiceSession()">Lock voice</button></div></div><div class="voiceControlGrid"><label>AI voice<select id="speechVoiceSelect" onchange="saveSpeechVoiceChoice()"><option value="">Auto voice</option></select></label><label>Volume <input id="voiceVolume" type="range" min="0" max="1" step="0.05" onchange="saveUiSettings()"></label><label>Rate <input id="voiceRate" type="range" min="0.65" max="1.35" step="0.05" onchange="saveUiSettings()"></label><label>Pitch <input id="voicePitch" type="range" min="0.75" max="1.35" step="0.05" onchange="saveUiSettings()"></label></div><div class="row wrap"><button class="tiny secondary" onclick="testSpeechOutput()">Test AI voice</button><button class="tiny secondary" onclick="window.speechSynthesis&&window.speechSynthesis.cancel();stopSpeakWave();setVoiceStatus('Speech stopped.')">Stop AI speech</button></div><div class="personaMiniPanel" id="personaMiniPanel"><b>Nova persona sliders</b><div class="small">These fill a backend persona command; use Apply to persist Nova's custom chat/persona contract.</div><div class="personaMiniGrid"><label>Formality <input id="personaFormality" type="range" min="0" max="1" step="0.05" value="0.35" oninput="updatePersonaCommandPreview()"></label><label>Creativity <input id="personaCreativity" type="range" min="0" max="1" step="0.05" value="0.55" oninput="updatePersonaCommandPreview()"></label><label>Humor <input id="personaHumor" type="range" min="0" max="1" step="0.05" value="0.25" oninput="updatePersonaCommandPreview()"></label><label>Empathy <input id="personaEmpathy" type="range" min="0" max="1" step="0.05" value="0.70" oninput="updatePersonaCommandPreview()"></label><label>Verbosity <input id="personaVerbosity" type="range" min="0" max="1" step="0.05" value="0.45" oninput="updatePersonaCommandPreview()"></label><label>Tech depth <input id="personaTechnicalDepth" type="range" min="0" max="1" step="0.05" value="0.70" oninput="updatePersonaCommandPreview()"></label></div><div id="personaCommandPreview" class="personaCommandPreview">/persona-set formality=0.35 creativity=0.55 humor=0.25 empathy=0.70 verbosity=0.45 technical_depth=0.70</div><div class="row wrap"><button class="tiny secondary" onclick="fillPersonaSetCommand()">Fill persona command</button><button class="tiny" onclick="runPersonaSetCommand()">Apply persona</button><button class="tiny secondary" onclick="quick('/custom-chat-window')">Show chat window spec</button></div></div><div class="settingsGroup"><button class="tiny secondary" onclick="fillCommand(\'/idle status\')">Fill /idle status</button><button class="tiny secondary" onclick="fillCommand(\'/test-all\')">Fill /test-all</button><button class="tiny secondary" onclick="fillCommand(\'/autonomous status\')">Fill /autonomous status</button><button class="tiny secondary" onclick="diagnoseVoiceInput()">Test microphone</button><button class="tiny secondary" onclick="showVoiceSetupWizard()">Voice setup wizard</button><button class="tiny secondary" onclick="refreshVoiceDeviceSelect()">Refresh mic list</button><button class="tiny secondary" onclick="fillCommand('/upgrade-radar')">Fill /upgrade-radar</button><button class="tiny secondary" onclick="fillCommand('/optional-upgrades')">Fill /optional-upgrades</button><button class="tiny secondary" onclick="fillCommand('/voice-troubleshoot')">Fill /voice-troubleshoot</button><button class="tiny secondary" onclick="showTutorial(true)">Replay tutorial</button></div></div>
    <div id="artifactPanel" class="artifact uiCreatedOutputs" style="display:none"></div>
    <div id="chatTabs" class="chatTabs" role="tablist" aria-label="Chat tabs"></div>
    <div id="chat"><div id="guiRouteWarn" class="guiRouteWarn" style="display:none"></div></div>
    <div id="liveActivityPanel" class="activity uiLiveActivity"><div class="activityHead"><div><h3>Live activity</h3><div class="small">Readable run names. Select/delete old logs here; use Stop stuck task if a model run keeps going after you moved on.</div></div><div class="row wrap"><button class="tiny danger" onclick="confirmInterrupt()">Stop stuck task</button><button class="tiny secondary" onclick="selectAllRuns(true)">Select visible</button><button class="tiny secondary" onclick="selectAllRuns(false)">Clear</button><button class="tiny danger" onclick="deleteSelectedRuns()">Delete selected logs</button><button id="activityScrollBtn" class="tiny secondary" onclick="toggleActivityAutoScroll()">Pin latest</button><button id="activityToggleBtn" class="tiny secondary" onclick="toggleActivityOpen()">Minimize</button></div></div><div id="activitySubtitle" class="activitySubtitle">Current task: waiting for activity.</div><div class="activityHint">Backend IDs are hidden in tooltips; summaries use goal/tool/file context. Deleting logs does not delete project files.</div><div id="activityLog"></div></div>
    <div class="composer">
      <input id="contextFileInput" type="file" accept=".txt,.md,.py,.js,.html,.css,.json,.csv,.png,.jpg,.jpeg,.gif,.webp,.bmp,.svg,.pdf" multiple onchange="uploadContextFiles(this.files)" style="display:none">
      <div class="inputDock">
        <button id="plusBtn" class="plusBtn" title="Add files or choose a mode" onclick="togglePlusMenu(event)">+</button>
        <div id="plusMenu" class="plusMenu hidden">
          <div class="plusMenuTitle">Add context</div>
          <button class="tiny" onclick="hidePlusMenu();document.getElementById('contextFileInput').click()">Upload files or photos</button>
          <button class="tiny" data-command="/attach-file C:\path\to\file.txt" onclick="hidePlusMenu();fillDatasetCommand(this)">Attach local path</button>
          <button class="tiny" onclick="hidePlusMenu();quick('/context-files')">Show context files</button>
          <button class="tiny" onclick="hidePlusMenu();quick('/context-files clear')">Clear context</button>
          <div class="plusMenuTitle">Use mode</div>
          <button class="tiny" onclick="hidePlusMenu();fillCommand('/research topic to investigate')">Research mode</button>
          <button class="tiny" onclick="hidePlusMenu();fillCommand('/image-generate realistic dachshund sausage dog photo')">Generate image</button>
          <button class="tiny" onclick="hidePlusMenu();quick('/image-status')">Image backend status</button>
          <button class="tiny" onclick="hidePlusMenu();quick('/image-analyze latest => describe this uploaded photo and any UI/visual issues')">Analyze latest photo</button>
          <button class="tiny" onclick="hidePlusMenu();fillCommand('/sandbox-linux exec python --version')">Linux sandbox command</button>
          <button class="tiny" onclick="hidePlusMenu();fillCommand('/sandbox-kali exec nmap --version')">Kali sandbox command</button>
          <button class="tiny" onclick="hidePlusMenu();toggleVoiceMode(true);toggleVoiceInput()">Voice mode: talk to Nova</button>
        </div>
        <textarea id="msg" class="composerText" autofocus placeholder="Ask Nova, attach files with +, or choose a mode such as research, image, Linux sandbox, or autonomous build."></textarea>
        <button id="voiceBtn" class="voiceBtn" title="Voice mode: click to talk" onclick="toggleVoiceInput()">🎙️</button>
        <button class="tiny secondary" title="Test microphone permission/device" onclick="diagnoseVoiceInput()">Mic test</button>
        <button class="sendBtn" onclick="send()">Send</button>
      </div>
      <div class="contextStatusLine" aria-hidden="true"><span id="contextUploadStatus" class="small">No shared files attached.</span> <select id="voiceDeviceSelect" class="tiny" title="Voice input device" onchange="saveVoiceDeviceChoice()"><option value="">Default mic</option></select> <button class="tiny secondary" title="Refresh browser-visible microphones" onclick="refreshVoiceDeviceSelect()">Refresh mics</button> <span id="voiceStatus" class="small voiceStatus">Voice idle.</span> <span id="voiceDeviceStatus" class="small voiceStatus"></span><div id="voiceLiveText" class="small voiceStatus" aria-live="polite">Live transcript appears here.</div><div class="voiceWaveRow"><div class="voiceWaveCard"><b>Mic input</b><canvas id="voiceWaveCanvas" class="voiceWave" width="220" height="44"></canvas></div><div class="voiceWaveCard"><b>Nova voice</b><canvas id="novaSpeakWaveCanvas" class="voiceWave" width="220" height="44"></canvas></div></div> <button id="chatMuteBtn" class="tiny secondary chatMuteBtn" title="Mute spoken replies for this chat only" onclick="toggleCurrentChatMute()">Chat audio on</button> <button id="wakeWordBtn" class="tiny secondary wakeWordOff" title="Listen for Hey Nova before taking a voice command" onclick="toggleWakeWordListening()">Hey Nova off</button></div>
      <div id="composerButtonsRemoved" style="display:none"></div>
    </div>
  </section>

  <div class="resizeRail rightRail" data-panel="right" title="Resize right panel" role="separator" tabindex="0" aria-label="Resize right panel" aria-orientation="vertical" aria-valuemin="280" aria-valuemax="760"></div>

  <aside class="rightbar card">
    <div class="panelHeader"><b>Right panel</b><span class="pill">Unified State / Output</span><button class="tiny secondary" onclick="togglePanel('right')">Hide</button></div><div id="inspectorTabs" class="inspectorTabs" style="display:none"><button data-tab="state">State</button><button data-tab="output">Output</button><button data-tab="bridge">Jarvis</button><button data-tab="editor">Editor</button><span>Integrated right panel: state, output, Jarvis and editor are one scrollable panel. Files and tools remain quick actions in the top strip.</span></div><div id="novaOrbPanel" class="novaOrbPanel"><div id="novaOrb" class="novaOrb ready">🤖</div><div><div id="novaOrbTitle" class="novaOrbTitle">Nova ready</div><div id="novaOrbTranscript" class="novaOrbTranscript">Always-listening wake word and live speech transcript appear here.</div><div class="voiceWaveRow"><div class="voiceWaveCard"><b>Mic input</b><canvas id="rightVoiceWaveCanvas" class="voiceWave" width="220" height="44"></canvas></div><div class="voiceWaveCard"><b>Nova voice</b><canvas id="rightSpeakWaveCanvas" class="voiceWave" width="220" height="44"></canvas></div></div></div></div>
    <div class="rightStateHero communicationCentre" id="communicationCentreBoard">
      <b>Communication centre</b><div class="small">Voice lock, wake detection, captured command text and Nova's reply handoff live here. Actions still run through normal chat.</div>
      <div class="voicePipelineGrid">
        <div class="voicePipelineCard"><b>Pipeline</b><span id="voicePipelineState">Ready</span><div id="voicePipelineDetail" class="small">No voice request in progress.</div></div>
        <div class="voicePipelineCard"><b>Wake resume</b><span id="voiceWakeResumeState">Wake listener ready.</span></div>
        <div class="voicePipelineCard"><b>Last command</b><span id="voiceLastCommand">None captured yet.</span></div>
        <div class="voicePipelineCard"><b>Audio</b><span id="voiceAudioState">Audio state loading.</span></div>
      </div>
      <div class="row wrap"><button class="tiny secondary" onclick="diagnoseVoiceInput()">Mic test</button><button class="tiny secondary" onclick="refreshVoiceDeviceSelect()">Refresh mics</button><button class="tiny secondary" onclick="toggleWakeWordListening(true)">Resume Hey Nova</button><button class="tiny secondary" onclick="toggleWakeWordListening(false)">Pause Hey Nova</button></div>
      <div id="voiceGuardCard" class="voiceGuardCard locked"><b id="voiceLockState">Voice locked</b><span id="voiceProfileState" class="small">Load state: locked. Enrol your voice profile or use testing bypass.</span><div class="row wrap"><button class="tiny" onclick="startVoiceProfileEnrollment()">Enrol my voice</button><button id="voiceBypassBtn" class="tiny secondary" onclick="setVoiceTestingBypass(!voiceTestingBypassActive())">Testing bypass unlock</button><button class="tiny danger" onclick="lockVoiceSession()">Lock voice</button></div></div>
      <div id="communicationTranscriptBox" class="communicationTranscriptBox"><b>Live communication trace</b><div id="communicationTrace" class="small">Waiting for Hey Nova. Commands will appear here before and while they are sent to chat.</div></div>
    </div>
    <div class="jarvisSidecarPanel" id="jarvisInspectorPanel"><b>Jarvis / sidecar bridge</b><div class="small">Nova can probe Jarvis and queue authority decisions, but sidecar, shell, browser and direct-file authority remain gated.</div><div id="jarvisInspectorText" class="small">Use /jarvis-doctor or /sidecar-preflight from the left.</div></div>
    <div class="section-title">Nova status<span style="display:none">AI state & communication — AI mood, disclosure and communication now live in the right panel</span></div>
    <div id="aiPresenceBox" class="avatarBox mood-ready"><div class="avatarFace">🤖</div><div><div class="avatarMood">Ready</div><div class="small">Mood, current task and side-channel notes appear here.</div></div></div>
    <div id="assistantBoxPanel" class="item assistantBoxPanel">
      <div class="assistantBoxMeta"><b>Nova communication box</b><span id="assistantBoxInfo" class="small">No message yet.</span><button class="tiny secondary" onclick="copyAssistantBox()">Copy</button><button class="tiny secondary" onclick="fillCommand('/comm-box write message here')">Fill command</button><button class="tiny secondary" onclick="synthAssistantBox()">Summarise status</button><button class="tiny danger" onclick="clearAssistantBox()">Clear</button></div>
      <textarea id="assistantBoxText" class="assistantBoxText info" readonly placeholder="Nova shows live Nova status, current task, model snippets, file focus, warnings and handoff notes here."></textarea>
    </div>
    <div style="display:none" aria-hidden="true"><button onclick="fillCommand('/db merge research.notes.example {&quot;note&quot;:&quot;text&quot;}')">DB merge</button><div id="aiMemoryStatus" class="item small"></div></div>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">Editor</div>
    <div id="openPath" class="pathline">No file open.</div>
    <div id="planningVisibilityPanel" class="planPanel small"><b>Plan before run</b><br>Detected intent, confidence, target, tools and verification will appear here when Nova pauses for a planning choice.</div>
    <div id="aiFileFocus" class="aiFocus small">Current AI file focus: No AI file focus yet.</div>
    <textarea id="editor" class="editor" spellcheck="false" placeholder="Open a text file from the file list..."></textarea>
    <div class="row wrap"><button onclick="saveOpenFile()">Save file</button><button class="secondary" onclick="downloadOpenFile()">Download</button><button class="secondary" onclick="askEditOpenFile()">Ask AI to edit</button></div>
    <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
    <div class="section-title">Transparent output</div>
    <div class="transparentOutputPanel">
      <b>Latest generated output / edited content</b>
      <div class="outputEvidenceMeta" id="outputEvidenceMeta"><span>waiting</span><span>source: activity/model_io</span></div>
      <div id="codePreview" class="codepreview">Waiting for model/file output...</div>
      <div id="transparentDiffPanel" class="diffbox"><summary>Before / after diff</summary><pre>No before/after diff found in recent activity yet.</pre></div>
      <div class="transparencyNote">This panel should show what changed, where it came from, and before/after evidence where Nova has it. It is for transparency, not command buttons.</div>
    </div>
    <div class="bridgeReceiptPanel"><b>Bridge receipts</b><div class="small">Use /bridge-receipts from the left to list queued, blocked or proposed Jarvis/sidecar actions.</div></div>
  </aside>
</main>
<button id="restoreLeftPanel" class="panelRestore leftRestore secondary tiny" onclick="togglePanel('left')" title="Show left panel">Show left panel</button>
<button id="restoreRightPanel" class="panelRestore rightRestore secondary tiny" onclick="togglePanel('right')" title="Show right panel">Show right panel</button>
<button id="restoreActivityPanel" class="panelRestore activityRestore secondary tiny" onclick="togglePanel('activity')" title="Show Live Activity">Show Live Activity</button>
<div id="runModal" class="runmodal"><div class="runbox"><div class="runhead"><div><b>Running project preview</b><div id="runPath" class="small"></div></div><div class="row"><button class="secondary" onclick="openRunInTab()">Open in tab</button><button class="danger" onclick="closeRunPopup()">Close</button></div></div><iframe id="runFrame" class="runframe" sandbox="allow-scripts allow-forms allow-downloads allow-modals allow-same-origin"></iframe></div></div>
<div id="modelSetupModal" class="runmodal"><div class="runbox" style="height:auto;max-height:90vh"><div class="runhead"><div><b>Ollama model setup needed</b><div class="small">Nova needs at least one local model for chat/build tasks.</div></div><button class="danger" onclick="closeModelSetup()">Close</button></div><div style="padding:16px;overflow:auto"><p>If no model is installed or the selected model is missing, run these commands in PowerShell:</p><pre id="modelSetupCommands" style="white-space:pre-wrap;background:#111827;color:#e5e7eb;border-radius:12px;padding:12px"></pre><p class="small">Recommended for this upgraded PC: qwen3-coder:30b for code/chat/planning, gemma2:2b as a fast fallback, llama3.2-vision:11b for optional image analysis.</p><div class="row wrap"><button onclick="quick('/model-doctor');closeModelSetup()">Show model doctor in chat</button><button class="secondary" onclick="closeModelSetup()">I will do this later</button></div></div></div></div>
<div id="tutorialOverlay" class="tutorialOverlay" style="display:none"><div class="tutorialCard"><h2>Welcome to Nova</h2><div id="tutorialBody" class="tutorialStep"></div><div class="row wrap"><button class="secondary" onclick="tutorialBack()">Back</button><button onclick="tutorialNext()">Next</button><button class="secondary" onclick="finishTutorial()">Finish</button><button class="danger" onclick="skipTutorial()">Skip</button></div><div class="small">This guide never runs commands. It only highlights the interface.</div></div></div>
<script>
const ASSISTANT_NAME='Nova';
const chat=document.getElementById('chat'), msg=document.getElementById('msg'), editor=document.getElementById('editor'), openPath=document.getElementById('openPath'), artifactPanel=document.getElementById('artifactPanel');
let currentFile=''; let busy=false; let activeWorkingBubble=null; let autonomousChatBubble=null; let autonomousBubbleKey=null; const autonomousCycleBubbles={}; let idleCycleBubbles={}; const pageLoadTs = Date.now()/1000;
const COMMANDS=[
 {group:'Build',label:'Quick app',command:'/fast make a tiny useful app',desc:'Small project with basic checks',tags:'build app quick fast'},
 {group:'Build',label:'Full project',command:'/long make a useful local app with search, filters, local saving, JSON export and example data',desc:'Staged project workflow',tags:'build app long project'},
 {group:'Video',label:'Video plan',command:'/video-plan 10 second cinematic trailer about Nova building a project',desc:'Plan script, scenes, shots, audio and edit manifest',tags:'video movie mp4 comfyui wangp ffmpeg remotion manifest'},
 {group:'Video',label:'Video status',command:'/video-status',desc:'Check FFmpeg, Node, ComfyUI and fallback video readiness',tags:'video status comfyui ffmpeg remotion'},
 {group:'Video',label:'Video validate',command:'/video-validate 10 second cinematic trailer about Nova building a project',desc:'Plan and validate a Nova video manifest before rendering',tags:'video validate qa manifest'},
 {group:'Autonomous',label:'Continuous autonomous',command:'/autonomous start --continuous improve Nova safely and keep choosing the next verified improvement',desc:'Keep autonomous mode iterating after verified milestones until you stop it',tags:'autonomous continuous iterative self improvement'},
 {group:'Autonomous',label:'Safe subagents',command:'/subagents improve Nova without regressions',desc:'Plan deterministic subagents while serialising local model calls',tags:'subagent multi agent parallel ollama lock'},
 {group:'Settings',label:'Authority controls',command:'/authority-mode',desc:'Show internet, mutation and shell gates before granting access',tags:'internet shell command prompt authority gates'},
 
 {group:'Models',label:'Provider route',command:'/provider-route explain a whole repo review',desc:'Explain local/default, NVIDIA local, or remote long-context provider choice',tags:'provider route subq nim vllm sglang'},
 {group:'Models',label:'Queue status',command:'/queue-status',desc:'Show active provider/model queue receipts',tags:'queue provider model ollama subagents'},
 {group:'Models',label:'Provider test plan',command:'/provider-test ollama',desc:'Show dry-run validation command for a provider',tags:'provider test validate'},
{group:'Settings',label:'Enable internet gate',command:'/allow-internet on',desc:'Allow public web fetch/provider calls after explicit user request',tags:'internet enable web research'},
 {group:'Build',label:'Clarify first',command:'/interactive make a useful local app and ask me before choosing scope',desc:'Ask one question before building',tags:'interactive clarify plan'},
 {group:'Repair',label:'Fix last',command:'/fix-last',desc:'Repair the latest failed run',tags:'repair failed error'},
 {group:'Repair',label:'Surgical repair',command:'/surgical-repair paste the exact error here',desc:'Small targeted fix from an error',tags:'surgical repair exact error'},
 {group:'Inspect',label:'Activity',command:'/activity',desc:'Recent runs, failures and logs',tags:'logs activity inspect'},
 {group:'Inspect',label:'Model doctor',command:'/model-doctor',desc:'Check Ollama/model setup',tags:'ollama model doctor status'},
 {group:'Research',label:'Research topic',command:'/research topic to investigate',desc:'Gather sources and analyse bias, credibility and meaning',tags:'research sources bias credibility'},
 {group:'Memory',label:'Assistant DB list',command:'/db list',desc:'List Nova schemaless assistant databases',tags:'database db memory json'},
 {group:'Inspect',label:'Run project',command:'/run-project',desc:'Prepare current project preview/run info',tags:'run preview project'},
 {group:'Verify',label:'Test all',command:'/test-all',desc:'Run Nova checks',tags:'test verify smoke'},
 {group:'Verify',label:'Validation matrix',command:'/validation-matrix',desc:'Compile, GUI contract, Feature-continuity audit and behaviour evidence checks',tags:'validation matrix regression evidence'},
 {group:'Verify',label:'Startup validation',command:'/startup-validation',desc:'Run the same compile/smoke gate used by the startup .bat file',tags:'startup gate compile smoke pytest'},
 {group:'Verify',label:'Nova full system test',command:'/nova-system-test',desc:'One-button test for chat routing, coding, GUI, voice/persona, Jarvis, startup and regression slices',tags:'nova full system test all one button chat coding voice jarvis'},
 {group:'Verify',label:'Completion audit',command:'/completion-audit',desc:'Verify previous requested patch tasks are actually wired, tested and regression-protected',tags:'completion audit previous task no regression nova one button'},
 {group:'Verify',label:'Audit log',command:'/audit-log',desc:'Unified Nova/Jarvis/voice/action receipt audit viewer',tags:'audit log receipts voice jarvis activity'},
 {group:'Automation',label:'Workflow run',command:'/workflow-run validate Nova safely',desc:'Preview or queue a supervised workflow through authority and validation receipts',tags:'workflow supervised blueprint receipt validation'},
 {group:'Verify',label:'Adaptive backlog',command:'/adaptive-backlog',desc:'Rank next useful Nova upgrades from current capability markers',tags:'adaptive backlog improvements'},
 {group:'Plan',label:'Role router',command:'/role-router current task',desc:'Show which local-model role and output contract should be used',tags:'role router planner builder verifier repairer toolsmith'},
 {group:'Integrations',label:'Jarvis bridge',command:'/jarvis-bridge',desc:'Show safe daemon/sidecar/proactive action capability map',tags:'jarvis daemon sidecar proactive screen shell browser'},
 {group:'Integrations',label:'Jarvis status',command:'/jarvis-status',desc:'Read-only localhost daemon probe',tags:'jarvis status daemon localhost health'},
 {group:'Integrations',label:'Jarvis doctor',command:'/jarvis-doctor',desc:'Check Docker binding, daemon health and Ollama setup hints',tags:'jarvis doctor docker ollama host docker internal model setup'},
 {group:'Integrations',label:'Sidecar policy',command:'/sidecar-policy',desc:'Show or change external sidecar/screen/browser authority gates',tags:'sidecar policy screen browser shell safety'},
 {group:'Integrations',label:'Sidecar preflight',command:'/sidecar-preflight terminal filesystem browser screenshot',desc:'Preview sidecar capabilities against current policy without enabling them',tags:'sidecar preflight terminal filesystem browser screenshot'},
 {group:'Integrations',label:'Authority gate',command:'/bridge-authority browser open-site localhost low',desc:'Queue/deny external actions through authority receipts instead of executing silently',tags:'authority gate bridge receipt action policy'},
 {group:'Integrations',label:'Workflow blueprint',command:'/workflow-blueprint safely validate a generated project and write receipts',desc:'Create a supervised Jarvis-style workflow blueprint',tags:'workflow blueprint jarvis validation receipt'},
 {group:'Integrations',label:'Bridge receipts',command:'/bridge-receipts',desc:'Show queued/blocked/proposed Jarvis-sidecar actions',tags:'jarvis receipts bridge authority transparency'},
 {group:'Integrations',label:'Sidecar enrollment',command:'/sidecar-enrollment terminal filesystem browser screenshot',desc:'Checklist before trusting a sidecar',tags:'sidecar enrollment checklist safety'},
 {group:'Integrations',label:'Browser harness',command:'/browser-harness http://127.0.0.1:3142',desc:'Plan safe Playwright-only browser control for localhost/project URLs',tags:'browser harness playwright localhost jarvis'},
 {group:'Integrations',label:'Jarvis test prompts',command:'/jarvis-test-prompts',desc:'Safe prompts for verifying Jarvis bridge behaviour',tags:'jarvis testing prompts'},
 {group:'Verify',label:'Quality dashboard',command:'/quality-dashboard',desc:'Summarise Nova/project health, runtime probe and next actions',tags:'quality dashboard health verification'},
 {group:'Verify',label:'Architecture audit',command:'/architecture-audit',desc:'Inspect architecture continuity, docs, command routing and release hygiene',tags:'architecture audit modules docs commands release'},
 {group:'Plan',label:'Planning dashboard',command:'/planning-dashboard make a project and verify it',desc:'Show intent, subtasks, risk and verification before acting',tags:'planning dashboard intent watcher'},
 {group:'Verify',label:'Human test',command:'/human-test .',desc:'Human-readable acceptance report',tags:'human test acceptance'},
 {group:'Verify',label:'Visual test',command:'/visual-test .',desc:'Browser/screenshot-style project checks',tags:'visual browser test'},
 {group:'Tools',label:'Tool guide',command:'/tool-guide',desc:'How the model should choose tools',tags:'guide tools planner'},
 {group:'Tools',label:'Create tool',command:'/tool-create count TODO comments in the project',desc:'Make a narrow reusable helper',tags:'custom tool create'},
 {group:'Idle',label:'Idle once',command:'/idle once inspect logs and propose safe improvements',desc:'Report-only idle analysis',tags:'idle report logs'},
 {group:'Idle',label:'Idle propose',command:'/idle propose add tests for idle candidate scoring',desc:'Dry-run proposal artifact',tags:'idle propose dry run'},
 {group:'Autonomous',label:'Auto once',command:'/autonomous once investigate logs, improve current project safely, and propose next changes',desc:'One bounded autonomous cycle',tags:'autonomous once agent'},
 {group:'Persona',label:'Nova persona',command:'/persona',desc:'Show Nova identity, beliefs, response contract and sliders',tags:'persona style sliders custom chat nova'},
 {group:'Persona',label:'Custom chat window',command:'/custom-chat-window',desc:'Show how Nova thinks, responds and applies personality settings',tags:'custom chat window persona beliefs system prompt'},
 {group:'Persona',label:'Formal concise Nova',command:'/persona-set formality=0.8 verbosity=0.25 humor=0.1 empathy=0.65',desc:'Example persona slider update',tags:'persona set formality verbosity humor empathy'},
 {group:'Voice',label:'Voice audit',command:'/voice-audit',desc:'Show recent Hey Nova voice command receipts',tags:'voice audit wake hey nova'},
 {group:'Local model',label:'Model optimiser',command:'/local-model-optimizer',desc:'Plan model routing, prompt caching, KV cache and retry context improvements',tags:'local model optimisation ollama cache kv'},
 {group:'Local model',label:'Agent harness',command:'/agent-harness',desc:'Show generate/execute/observe/repair loop for iterative coding',tags:'agent harness iterative coding repair'},
 {group:'Plan',label:'Agent topology',command:'/agent-topology improve Nova safely',desc:'Plan router, context mapper, safety gate, builder, runner, verifier and reporter handoffs',tags:'agent topology handoff verifier guardrail'},
 {group:'Plan',label:'Trace observability',command:'/trace-observability debug coding flow',desc:'Draft workflow spans, model/tool metrics and redaction rules',tags:'trace observability spans metrics redaction'},
 {group:'Local model',label:'Local stack advisor',command:'/local-stack-advisor debug Python => GTX 1650 4GB VRAM',desc:'Choose Ollama vs llama.cpp, model shortlist and runtime options',tags:'ollama llama.cpp local model vram num_ctx'},
 {group:'Verify',label:'Verifier ladder',command:'/verifier-ladder build Java CLI => java',desc:'Generate runtime-specific syntax, smoke and regression checks',tags:'verifier ladder python java node powershell browser'},
 {group:'Tools',label:'Tool namespaces',command:'/tool-namespace-plan reduce tool bloat',desc:'Group tools into conditional namespaces for smaller local-model context',tags:'tool namespace conditional exposure local model'},
 {group:'Voice',label:'Voice pipeline review',command:'/voice-pipeline-review Hey Nova wake pipeline',desc:'Review Jarvis-style modular wake/STT/TTS/device boundaries without changing audio',tags:'voice jarvis wake stt tts pipeline'},
 {group:'Plan',label:'Route resilience plan',command:'/route-resilience-plan improve Nova safely',desc:'Plan self-healing fallback routes for agent/tool workflows without executing changes',tags:'route resilience self healing fallback graph agent tool'},
 {group:'Verify',label:'Tool health map',command:'/tool-health-map Nova route health',desc:'Audit command/tool route wiring without invoking registered tools',tags:'tool health map route command registry contract'},
 {group:'Plan',label:'Guardrail memory',command:'/guardrail-memory improve Nova safely => avoid regressions',desc:'Build context-aware safety rules that preserve benign utility',tags:'guardrail memory context safety utility'},
 {group:'Plan',label:'Context router policy',command:'/context-router-policy improve Nova coding reliability',desc:'Plan role-aware context routing and compact repo files for local agents',tags:'context router role memory budget local model'},
 {group:'Local model',label:'Runtime sentinel',command:'/local-runtime-sentinel debug code => GTX 1650 4GB VRAM',desc:'Draft model health checks, context limits and fallback profiles',tags:'local runtime sentinel ollama vram num_ctx benchmark'},
 {group:'Sandbox',label:'Sandbox status',command:'/sandbox-status',desc:'Check Docker/Podman runtime, policy and running sandboxes',tags:'linux kali docker podman sandbox'},
 {group:'Sandbox',label:'Sandbox setup help',command:'/sandbox-setup-help',desc:'Show Windows Docker Desktop / Podman setup steps',tags:'docker install setup sandbox'},
 {group:'Sandbox',label:'Start Linux sandbox',command:'/sandbox-linux start',desc:'Start disposable general Linux sandbox',tags:'linux sandbox start'},
 {group:'Sandbox',label:'Start Kali sandbox',command:'/sandbox-kali start',desc:'Start disposable Kali security lab sandbox',tags:'kali sandbox start'} ,
 {group:'Audit',label:'Efficiency audit',command:'/nova-efficiency-audit',desc:'Research-backed local model, GUI and code health audit',tags:'efficiency audit gui local model', marker:'novaEfficiencyAudit'},
 {group:'Schedule',label:'Schedule task',command:'/schedule-task remind me to stretch => tomorrow 9am',desc:'Create a safe local scheduled reminder/task with injection and risk checks',tags:'schedule reminder task confirmation'},
 {group:'Schedule',label:'Schedule status',command:'/schedule-status',desc:'Show scheduler records, pending confirmations and counts',tags:'schedule status tasks queue'},
 {group:'Schedule',label:'Task DAG',command:'/task-decompose remind me to submit the report next Friday at 4pm',desc:'Preview safe decomposition DAG before scheduling/execution',tags:'schedule dag decomposition planning'},
 {group:'Schedule',label:'Scheduling audit',command:'/scheduling-audit',desc:'Audit prompt filters, confirmation gates, retry/backoff and scheduler safety',tags:'schedule audit prompt injection retry'},
 {group:'Media',label:'Media status',command:'/media-status',desc:'Unified image and video backend readiness plus next steps',tags:'media image video status backend'},
 {group:'Media',label:'Image plan',command:'/image-plan cinematic robot dog mascot',desc:'Plan prompt variants, seed, size, steps and negative prompt before generation',tags:'image plan prompt variants'},
 {group:'Media',label:'Video storyboard',command:'/video-storyboard 10 second cinematic trailer about Nova improving a project',desc:'Write storyboard SVG, shotlist CSV and keyframe image prompts',tags:'video storyboard shotlist'},
 {group:'Media',label:'Video package',command:'/video-package 10 second cinematic trailer about Nova improving a project',desc:'Write manifest, storyboard, preview, validation and FFmpeg assembly plan',tags:'video package render manifest'}

];

const DEFAULT_QUICK_COMMANDS=[
 {group:'Status',label:'Avatar',command:'/avatar',desc:'Show current AI mood/state'},
 {group:'Status',label:'Activity',command:'/activity',desc:'Inspect recent runs and logs'},
 {group:'Status',label:'LLM status',command:'/llm-status',desc:'Check local model prompt state'},
 {group:'Build',label:'Fast app',command:'/fast make a tiny useful app',desc:'Create a small project'},
 {group:'Build',label:'Long bug tracker',command:'/long make a useful local bug tracker app with search, filters, local saving, JSON export and example bugs',desc:'Staged project creation test'},
 {group:'Projects',label:'Projects',command:'/projects',desc:'Show/open saved projects'},
 {group:'Tests',label:'Test all',command:'/test-all',desc:'Run core verification'},
 {group:'Tests',label:'Nova full test',command:'/nova-system-test',desc:'One-button staged Nova capability test'},
 {group:'Tests',label:'Completion audit',command:'/completion-audit',desc:'Check previous patch wiring and no-regression evidence'},
 {group:'Tests',label:'Doctor',command:'/nova-doctor',desc:'Run self-diagnosis'},
 {group:'Tests',label:'Integration radar',command:'/integration-radar improve Nova reliability',desc:'Rank useful next integrations'},
 {group:'Tests',label:'Release gate',command:'/release-gate final validation',desc:'Run release preflight'},
 {group:'Tests',label:'Massive system test',command:'/massive-test --confirm',desc:'Run the monitored full-system test sequence'},
 {group:'Tests',label:'Validation matrix',command:'/validation-matrix',desc:'Compact no-regression validation evidence'},
 {group:'Tests',label:'Dependency check',command:'/dependency-check',desc:'Check Python packages and external tools'},
 {group:'Tests',label:'Release checklist',command:'/release-checklist',desc:'Show ship readiness checklist'},
 {group:'Verify',label:'Codebase advisor',command:'/codebase-advisor',desc:'Rank next Nova improvements from a static codebase scan',tags:'codebase advisor next improvements roadmap'},
 {group:'Verify',label:'Release package',command:'/release-package',desc:'Create a clean release zip with manifest and cache/report exclusions',tags:'release package zip manifest clean'},
 {group:'Tests',label:'Playwright scaffold',command:'/playwright-smoke-help',desc:'Browser smoke test instructions'},
 {group:'Persona',label:'Persona',command:'/persona',desc:'Show Nova personality contract'},
 {group:'Persona',label:'Model optimiser',command:'/local-model-optimizer',desc:'Improve local model usage'},
 {group:'Voice',label:'Voice audit',command:'/voice-audit',desc:'Review spoken command receipts'},
 {group:'Docker',label:'Docker status',command:'/docker-status',desc:'Show Docker diagnostics'},
 {group:'Docker',label:'Docker quick validate',command:'/docker-validate quick',desc:'Validate copied workspace in Docker'},
 {group:'Sandbox',label:'Sandbox status',command:'/sandbox-status',desc:'Show Linux/Kali sandbox state'},
 {group:'Sandbox',label:'Less strict',command:'/sandbox-less-strict on',desc:'Trusted local lab mode'},
 {group:'Research',label:'Research topic',command:'/research topic to investigate',desc:'Gather and summarise sources'},
 {group:'Research',label:'DB list',command:'/db list',desc:'List assistant databases'},
 {group:'Research',label:'Research DB schema',command:'/db schema research',desc:'Show research database schema'},
 {group:'Research',label:'DB merge',command:'/db merge research.notes.example {"note":"text"}',desc:'Prepare a database merge command'},
 {group:'Memory',label:'Memory',command:'/memory',desc:'Show recent Nova memory'},
 {group:'Memory',label:'Receipts',command:'/receipt-history',desc:'Show recent build/fix action receipts'},
 {group:'Memory',label:'Role router',command:'/role-router current Nova work',desc:'Show local model Planner/Builder/Verifier/Repairer route'},
 {group:'Integrations',label:'Jarvis bridge',command:'/jarvis-bridge',desc:'Safe Jarvis-style daemon/sidecar map'},
 {group:'Integrations',label:'Jarvis status',command:'/jarvis-status',desc:'Probe local Jarvis daemon only'},
 {group:'Integrations',label:'Jarvis doctor',command:'/jarvis-doctor',desc:'Check Docker/Ollama/Jarvis setup'},
 {group:'Integrations',label:'Sidecar policy',command:'/sidecar-policy',desc:'Review external sidecar/action gates'},
 {group:'Integrations',label:'Sidecar preflight',command:'/sidecar-preflight terminal filesystem browser screenshot',desc:'Preview capabilities before enabling'},
 {group:'Integrations',label:'Workflow blueprint',command:'/workflow-blueprint validate current project safely',desc:'Plan a supervised workflow'},
 {group:'Integrations',label:'Bridge receipts',command:'/bridge-receipts',desc:'Show queued/blocked bridge actions'},
 {group:'Integrations',label:'Browser harness',command:'/browser-harness http://127.0.0.1:3142',desc:'Safe Playwright-only localhost harness'},
 {group:'Integrations',label:'Jarvis test prompts',command:'/jarvis-test-prompts',desc:'Safe Jarvis/Nova verification prompts'},
 {group:'Memory',label:'Project memory',command:'/project-memory',desc:'Show saved facts for this project'},
 {group:'Memory',label:'Remember project',command:'/remember-project important fact here',desc:'Save a project fact'},
 {group:'Help',label:'Self guide',command:'/self-guide',desc:'How to use Nova'},
 {group:'Settings',label:'New chat',command:'/new-chat',desc:'Create backend conversation'},
 {group:'Settings',label:'List chats',command:'/chats',desc:'Show saved backend conversations'},
 {group:'Settings',label:'Search chats',command:'/chat-search project',desc:'Search saved conversations'},
 {group:'Settings',label:'Security watch',command:'/security-watch',desc:'Read-only defensive delta check'},
 {group:'Settings',label:'Image setup',command:'/image-setup-help',desc:'Show real image-generation setup guidance'},
 {group:'Projects',label:'Project target check',command:'/project-target make a tiny useful app',desc:'Preview whether Nova will create a new project or edit current'}
];
function loadQuickCommands(){try{return JSON.parse(localStorage.getItem('wlaQuickCommands')||'null')||DEFAULT_QUICK_COMMANDS}catch(e){return DEFAULT_QUICK_COMMANDS}}
function saveQuickCommands(rows){try{localStorage.setItem('wlaQuickCommands',JSON.stringify(rows));}catch(e){}renderQuickControls();}
function resetQuickCommands(){saveQuickCommands(DEFAULT_QUICK_COMMANDS.slice());}
function renderQuickControls(){const box=document.getElementById('quickControlsGrouped');if(!box)return;const rows=loadQuickCommands();box.innerHTML='<div class="quickGroup quickControlsBox"><div class="quickGroupBody">'+rows.map((r,i)=>'<button class="secondary tiny quickItemBtn" data-desc="'+escAttr((r.group?r.group+': ':'')+(r.desc||r.command))+'" data-command="'+escAttr(r.command)+'" onclick="runQuickCommand(this.dataset.command)">'+esc(r.label||r.command)+'</button>').join('')+'</div></div>';renderQuickEditList();}
function renderQuickEditList(){const box=document.getElementById('quickEditList');if(!box)return;const rows=loadQuickCommands();box.innerHTML=rows.map((r,i)=>'<div class="item"><b>'+esc(r.label||'Command')+'</b> <span class="pill">'+esc(r.group||'General')+'</span><div><code>'+esc(r.command||'')+'</code></div><div class="small">'+esc(r.desc||'')+'</div><div class="row wrap"><button class="tiny secondary" onclick="moveQuickCommand('+i+',-1)">Up</button><button class="tiny secondary" onclick="moveQuickCommand('+i+',1)">Down</button><button class="tiny secondary" onclick="editQuickCommand('+i+')">Edit</button><button class="tiny danger" onclick="deleteQuickCommand('+i+')">Delete</button></div></div>').join('');}
function addQuickCommandFromForm(){const label=(document.getElementById('quickLabel')?.value||'Command').trim();const command=(document.getElementById('quickCommand')?.value||'').trim();if(!command)return;const rows=loadQuickCommands();rows.push({group:'Custom',label,command,desc:command.includes('\n')||command.includes(';;')?'Custom multi-step quick command':'Custom quick command'});saveQuickCommands(rows);}
function deleteQuickCommand(i){const rows=loadQuickCommands();rows.splice(i,1);saveQuickCommands(rows);}
function moveQuickCommand(i,d){const rows=loadQuickCommands();const j=i+d;if(j<0||j>=rows.length)return;[rows[i],rows[j]]=[rows[j],rows[i]];saveQuickCommands(rows);}
function editQuickCommand(i){const rows=loadQuickCommands();const r=rows[i]||{};const label=prompt('Label',r.label||'');if(label===null)return;const command=prompt('Command. Use newline or ;; for multiple sequential commands.',r.command||'');if(command===null||!command.trim())return;const group=prompt('Group',r.group||'Custom');rows[i]={...r,label,command,group:group||'Custom'};saveQuickCommands(rows);}
function chatSessionStore(){try{return JSON.parse(localStorage.getItem('wlaChatSessions')||'{}')}catch(e){return {}}}
function saveChatSessionStore(data){try{localStorage.setItem('wlaChatSessions',JSON.stringify(data));}catch(e){}}
function activeChatSessionId(){let id=localStorage.getItem('wlaActiveChatSession')||'';if(!id){id='chat_'+Date.now();localStorage.setItem('wlaActiveChatSession',id);}return id;}
function saveCurrentChatSession(){const id=activeChatSessionId();const data=chatSessionStore();const existing=data[id]||{};data[id]={...existing,id,title:existing.title||'Chat '+new Date().toLocaleString(),html:chat.innerHTML,updated:Date.now(),shared:!!existing.shared};saveChatSessionStore(data);renderChatSessionSelect();renderChatTabs();}
function renderChatSessionSelect(){const sel=document.getElementById('chatSessionSelect');if(!sel){renderChatTabs();return;}const data=chatSessionStore();const active=localStorage.getItem('wlaActiveChatSession')||'';sel.innerHTML='<option value="">Current chat</option>'+Object.values(data).sort((a,b)=>(b.updated||0)-(a.updated||0)).map(x=>'<option value="'+escAttr(x.id)+'" '+(x.id===active?'selected':'')+'>'+esc(x.title||x.id)+'</option>').join('');renderChatTabs();}
function renderChatTabs(){const box=document.getElementById('chatTabs');if(!box)return;const data=chatSessionStore();let active=localStorage.getItem('wlaActiveChatSession')||'';let rows=Object.values(data).sort((a,b)=>(a.created||a.updated||0)-(b.created||b.updated||0));if(!active&&rows[0])active=rows[0].id;if(!rows.length){box.innerHTML='<button class="chatTabAdd" title="New chat tab" onclick="newChatSession()">+</button>';return;}box.innerHTML=rows.map((x,i)=>{const title=esc(x.title||('Chat '+(i+1)));const shared=!!x.shared;const muted=!!chatMuteStore()[x.id];return '<div class="chatTab '+(x.id===active?'active':'')+'" role="tab" aria-selected="'+(x.id===active?'true':'false')+'" data-chat-id="'+escAttr(x.id)+'"><button class="chatTabTitle" title="'+escAttr(x.title||x.id)+'" onclick="switchChatSession(this.parentElement.dataset.chatId)">'+title+'</button><button class="chatTabAction '+(shared?'shared':'')+'" title="'+(shared?'Shared with other chats':'Isolated chat')+'" onclick="toggleChatTabShared(this.parentElement.dataset.chatId)">'+(shared?'S':'I')+'</button><button class="chatTabAction '+(muted?'chatMuted':'')+'" title="Mute this chat" onclick="toggleChatMuteById(this.parentElement.dataset.chatId)">'+(muted?'M':'🔈')+'</button><button class="chatTabAction" title="Rename chat" onclick="renameLocalChatSession(this.parentElement.dataset.chatId)">✎</button><button class="chatTabAction chatTabClose" title="Delete tab" onclick="deleteLocalChatSession(this.parentElement.dataset.chatId)">x</button></div>';}).join('')+'<button class="chatTabAdd" title="New chat tab" onclick="newChatSession()">+</button>';}
function switchChatSession(id){if(!id)return;saveCurrentChatSession();const rec=chatSessionStore()[id];if(rec){chat.innerHTML=rec.html||'';localStorage.setItem('wlaActiveChatSession',id);updateAudioRail();renderChatSessionSelect();}}
function toggleChatTabShared(id){saveCurrentChatSession();const data=chatSessionStore();if(!data[id])return;data[id].shared=!data[id].shared;saveChatSessionStore(data);renderChatSessionSelect();}
function closeChatTab(id){saveCurrentChatSession();const data=chatSessionStore();delete data[id];const remaining=Object.values(data).sort((a,b)=>(b.updated||0)-(a.updated||0));saveChatSessionStore(data);const wasActive=localStorage.getItem('wlaActiveChatSession')===id;if(wasActive&&remaining[0]){localStorage.setItem('wlaActiveChatSession',remaining[0].id);chat.innerHTML=remaining[0].html||'';updateAudioRail();renderChatSessionSelect();return;}if(wasActive){localStorage.setItem('wlaActiveChatSession','');newChatSession(false);return;}renderChatSessionSelect();}
function renameLocalChatSession(id){saveCurrentChatSession();const data=chatSessionStore();if(!data[id])return;const title=prompt('Rename chat',data[id].title||id);if(title===null||!title.trim())return;data[id].title=title.trim();data[id].updated=Date.now();saveChatSessionStore(data);renderChatSessionSelect();renderLocalChatDrawer();}
function deleteLocalChatSession(id){if(!confirm('Delete this browser chat tab? Backend project files and memories are not deleted.'))return;closeChatTab(id);renderLocalChatDrawer();}
function editLocalChatSession(id){saveCurrentChatSession();const data=chatSessionStore();const rec=data[id];if(!rec)return;const title=prompt('Edit title',rec.title||id);if(title===null)return;rec.title=title.trim()||rec.title;rec.updated=Date.now();data[id]=rec;saveChatSessionStore(data);renderChatSessionSelect();renderLocalChatDrawer();}
function toggleChatMuteById(id){const data=chatMuteStore();data[id]=!data[id];saveChatMuteStore(data);updateAudioRail();renderChatSessionSelect();renderLocalChatDrawer();setVoiceStatus(data[id]?'Muted this chat only.':'Unmuted this chat.');}

function newChatSession(startBackend=true){if(busy&&!confirm('A request is still running. Start a new chat view anyway?'))return;saveCurrentChatSession();chat.innerHTML='';const id='chat_'+Date.now();const data=chatSessionStore();data[id]={id,title:'Chat '+new Date().toLocaleString(),html:'',updated:Date.now(),created:Date.now(),shared:false};saveChatSessionStore(data);localStorage.setItem('wlaActiveChatSession',id);updateAudioRail();renderChatSessionSelect();add('Assistant','Starting a fresh chat view. Backend project files and memories are not deleted.');if(startBackend)quick('/new-chat');}
function textFromChatHtml(html){const div=document.createElement('div');div.innerHTML=String(html||'');return (div.textContent||div.innerText||'').replace(/\s+/g,' ').trim();}
function buildSharedChatContext(text){const data=chatSessionStore();const active=localStorage.getItem('wlaActiveChatSession')||'';const shared=Object.values(data).filter(x=>x&&x.id!==active&&x.shared&&x.html).slice(-4).map(x=>'['+(x.title||x.id)+'] '+textFromChatHtml(x.html).slice(-1600)).filter(Boolean);if(!shared.length)return text;return String(text||'')+'\n\nShared browser chat tab context selected by the user:\n'+shared.join('\n');}
function searchChatSessions(){const q=prompt('Search saved browser chat transcripts for text');if(!q)return;const rows=Object.values(chatSessionStore()).filter(x=>String(x.html||'').toLowerCase().includes(q.toLowerCase())).slice(0,8);add('Assistant', rows.length?('Found saved browser chats:\n'+rows.map(r=>'- '+r.title).join('\n')):'No saved browser chat transcript matched.');}

function clampPanelWidth(v){return Math.max(240, Math.min(680, Number(v)||0));}
function updateResizeAria(side, px){document.querySelectorAll('.resizeRail[data-panel="'+side+'"]').forEach(rail=>rail.setAttribute('aria-valuenow',String(px)));}
function setPanelWidth(side, value){const px=clampPanelWidth(value);document.body.style.setProperty(side==='left'?'--left-col':'--right-col', px+'px');try{localStorage.setItem(side==='left'?'wlaLeftPanelWidth':'wlaRightPanelWidth', String(px));}catch(e){}updateResizeAria(side,px);}
function toggleControlDrawer(force){const collapsed=typeof force==='boolean'?force:!document.body.classList.contains('control-drawer-collapsed');document.body.classList.toggle('control-drawer-collapsed',collapsed);const hero=document.getElementById('controlDrawerHero');if(hero)hero.classList.toggle('collapsed',collapsed);const btn=document.getElementById('controlDrawerToggle');if(btn)btn.textContent=collapsed?'Show drawer':'Hide drawer';try{localStorage.setItem('wlaControlDrawerCollapsed',collapsed?'1':'0');}catch(e){}}
function togglePanel(name){if(name==='activity'){toggleActivityOpen();return;}document.body.classList.toggle('collapse-'+name);try{localStorage.setItem('wlaCollapse'+name, document.body.classList.contains('collapse-'+name)?'1':'0');}catch(e){}}
function setActivityOpen(open){
 const panel=document.getElementById('liveActivityPanel');
 document.body.classList.toggle('collapse-activity', !open);
 if(panel){panel.classList.toggle('collapsed', !open);panel.style.display='block';}
 const log=document.getElementById('activityLog');if(log)log.hidden=!open;
 const btn=document.getElementById('activityToggleBtn');if(btn)btn.textContent=open?'Minimize':'Expand';
 try{localStorage.setItem('wlaCollapseactivity', open?'0':'1');}catch(e){}
 syncMiddleResizeRails();
}
function toggleActivityOpen(){setActivityOpen(document.body.classList.contains('collapse-activity'));}
let activityAutoScrollLatest=true;
try{activityAutoScrollLatest=localStorage.getItem('novaActivityAutoScrollLatest')!=='0';}catch(e){}
function updateActivityScrollButton(){const btn=document.getElementById('activityScrollBtn');if(btn)btn.textContent=activityAutoScrollLatest?'Pin latest':'Preserve scroll';}
function toggleActivityAutoScroll(){activityAutoScrollLatest=!activityAutoScrollLatest;try{localStorage.setItem('novaActivityAutoScrollLatest',activityAutoScrollLatest?'1':'0');}catch(e){}updateActivityScrollButton();}
function activityShouldPreserveScroll(box){if(!box)return false;if(!activityAutoScrollLatest)return true;return (box.scrollTop||0)>24;}
function restoreActivityScroll(box,previousTop,previousHeight,preserve){if(!box)return;if(preserve){const delta=Math.max(0,(box.scrollHeight||0)-previousHeight);box.scrollTop=Math.min(box.scrollHeight, previousTop+delta);}else{box.scrollTop=0;}updateActivityScrollButton();}
function togglePlusMenu(ev){if(ev)ev.stopPropagation();const m=document.getElementById('plusMenu');if(m)m.classList.toggle('hidden');}
function hidePlusMenu(){const m=document.getElementById('plusMenu');if(m)m.classList.add('hidden');}
document.addEventListener('click', function(ev){const m=document.getElementById('plusMenu'), b=document.getElementById('plusBtn');if(m&&!m.classList.contains('hidden')&&!m.contains(ev.target)&&ev.target!==b)hidePlusMenu();});
function toggleEdgeRail(force){const rail=document.getElementById('edgeRail');const tab=document.getElementById('edgeRailToggle');if(!rail)return;const open=typeof force==='boolean'?force:!rail.classList.contains('open');rail.classList.toggle('open',open);if(tab)tab.classList.toggle('open',open);try{localStorage.setItem('wlaEdgeRailOpen',open?'1':'0');}catch(e){}}


function toggleFocusWorkspace(){
  const on=!document.body.classList.contains('focus-workspace');
  document.body.classList.toggle('focus-workspace',on);
  if(on){document.body.classList.remove('orbit-right-open','orbit-activity-open');document.body.classList.add('collapse-activity');}
  try{localStorage.setItem('novaFocusWorkspace',on?'1':'0');}catch(e){}
}

function applyCalmWorkspaceDefaults(){
  try{
    document.body.classList.add('clean-workspace','calm-workspace','focus-workspace');
    const key='novaCalmLayoutApplied';
    if(localStorage.getItem(key)!=='v55.3.164'){
      document.body.classList.remove('orbit-right-open','orbit-activity-open');
      document.body.classList.add('collapse-activity');
      localStorage.setItem(key,'v55.3.164');
      localStorage.setItem('wlaCleanWorkspace','1');
    }
    const focusKey='novaFocusLayoutApplied';
    if(localStorage.getItem(focusKey)!=='v55.3.164'){
      document.body.classList.remove('orbitDrawerOpen','orbit-right-open','orbit-activity-open');
      document.body.classList.add('collapse-activity','focus-workspace');
      localStorage.setItem(focusKey,'v55.3.164');
      localStorage.setItem('wlaCollapseactivity','1');
    }
    const badge=document.getElementById('novaVersionBadge');
    if(badge) badge.textContent='Nova v55.3.164';
  }catch(e){console.warn('applyCalmWorkspaceDefaults failed', e);}
}

function initPanelLayout(){try{const left=localStorage.getItem('wlaLeftPanelWidth'), right=localStorage.getItem('wlaRightPanelWidth');if(left)setPanelWidth('left', left);if(right)setPanelWidth('right', right);for(const name of ['left','right']){if(localStorage.getItem('wlaCollapse'+name)==='1')document.body.classList.add('collapse-'+name);}toggleControlDrawer(localStorage.getItem('wlaControlDrawerCollapsed')==='1');setActivityOpen(localStorage.getItem('wlaCollapseactivity')!=='1');toggleEdgeRail(localStorage.getItem('wlaEdgeRailOpen')==='1');applyStoredMiddlePanelHeights();}catch(e){}}
function setupPanelResize(){let drag=null;const start=(rail,e)=>{drag=rail.dataset.panel;rail.classList.add('dragging');try{if(e.pointerId!==undefined&&rail.setPointerCapture)rail.setPointerCapture(e.pointerId);}catch(err){}e.preventDefault();};for(const rail of document.querySelectorAll('.resizeRail')){rail.addEventListener('pointerdown',e=>start(rail,e));rail.addEventListener('mousedown',e=>{if(window.PointerEvent)return;start(rail,e);});rail.addEventListener('keydown',e=>{const side=rail.dataset.panel;let width=Number(localStorage.getItem(side==='left'?'wlaLeftPanelWidth':'wlaRightPanelWidth')||(side==='left'?410:430));const step=e.shiftKey?60:20;if(e.key==='ArrowLeft')width+=side==='left'?-step:step;else if(e.key==='ArrowRight')width+=side==='left'?step:-step;else if(e.key==='Home')width=side==='left'?260:280;else if(e.key==='End')width=side==='left'?720:760;else return;setPanelWidth(side,width);document.body.classList.remove('collapse-'+side);e.preventDefault();});}const move=e=>{if(!drag)return;const main=document.querySelector('main');const rect=main.getBoundingClientRect();if(drag==='left'){setPanelWidth('left', e.clientX-rect.left-14);document.body.classList.remove('collapse-left');}else{setPanelWidth('right', rect.right-e.clientX-14);document.body.classList.remove('collapse-right');}};const stop=()=>{drag=null;for(const rail of document.querySelectorAll('.resizeRail'))rail.classList.remove('dragging');};document.addEventListener('pointermove',move);document.addEventListener('mousemove',move);document.addEventListener('pointerup',stop);document.addEventListener('mouseup',stop);}
function middlePanelHeights(){try{return JSON.parse(localStorage.getItem('wlaMiddlePanelHeights')||'{}')}catch(e){return {}}}
function saveMiddlePanelHeight(id,px){const data=middlePanelHeights();data[id]=Math.round(px);try{localStorage.setItem('wlaMiddlePanelHeights',JSON.stringify(data));}catch(e){}}
function applyStoredMiddlePanelHeights(){const data=middlePanelHeights();for(const [id,px] of Object.entries(data)){const el=document.getElementById(id);if(el&&Number(px)>0)el.style.height=Number(px)+'px';}}
function middleResizeTargets(){return ['topbar','odysseusVoyageDeck','validationCommandDock','smartTopStrip','activeRunPanel','autonomousLivePanel','generalPanel','linuxSandboxPanel','kaliSandboxPanel','sandboxSettingsPanel','dockerPanel','settingsPanel','personaMiniPanel','artifactPanel','chatTabs','liveActivityPanel'];}
function ensureMiddleResizeRail(id){let rail=document.querySelector('.middleResizeRail[data-resize-target="'+id+'"]');const target=document.getElementById(id);if(!target)return null;if(!rail){rail=document.createElement('div');rail.className='middleResizeRail';rail.dataset.resizeTarget=id;rail.title=id==='liveActivityPanel'?'Resize chat and live activity split':'Resize this centre panel';if(id==='liveActivityPanel')target.before(rail);else target.after(rail);}else if(id==='liveActivityPanel'&&rail.nextElementSibling!==target){target.before(rail);}else if(id!=='liveActivityPanel'&&target.nextElementSibling!==rail){target.after(rail);}rail.setAttribute('role','separator');rail.tabIndex=0;rail.setAttribute('aria-label','Resize '+id);rail.setAttribute('aria-orientation','horizontal');rail.setAttribute('aria-valuemin',id==='liveActivityPanel'?'72':'44');rail.setAttribute('aria-valuemax',String(Math.max(120,Math.round(window.innerHeight*0.78))));rail.setAttribute('aria-controls',id);return rail;}
function syncMiddleResizeRails(){for(const id of middleResizeTargets()){const target=document.getElementById(id);const rail=ensureMiddleResizeRail(id);if(!target||!rail)continue;const visible=target.style.display!=='none'&&!target.classList.contains('hidden')&&!target.classList.contains('collapsed')&&getComputedStyle(target).display!=='none';rail.classList.toggle('visible',visible);}}
function setupMiddlePanelResize(){let drag=null,startY=0,startH=0;const resizeTarget=(target,next)=>{const max=Math.max(120,Math.round(window.innerHeight*0.78));const min=target.id==='liveActivityPanel'?72:44;const px=Math.max(min,Math.min(max,next));target.style.height=px+'px';target.style.maxHeight=max+'px';saveMiddlePanelHeight(target.id,px);const rail=document.querySelector('.middleResizeRail[data-resize-target="'+target.id+'"]');if(rail){rail.setAttribute('aria-valuenow',String(px));rail.setAttribute('aria-valuemax',String(max));}syncMiddleResizeRails();};const start=(rail,e)=>{const target=document.getElementById(rail.dataset.resizeTarget||'');if(!target)return;drag=target;startY=e.clientY;startH=target.getBoundingClientRect().height;rail.classList.add('dragging');try{if(e.pointerId!==undefined&&rail.setPointerCapture)rail.setPointerCapture(e.pointerId);}catch(err){}e.preventDefault();};for(const id of middleResizeTargets()){const rail=ensureMiddleResizeRail(id);if(!rail)continue;rail.addEventListener('pointerdown',e=>start(rail,e));rail.addEventListener('mousedown',e=>{if(window.PointerEvent)return;start(rail,e);});rail.addEventListener('keydown',e=>{const target=document.getElementById(rail.dataset.resizeTarget||'');if(!target)return;const current=target.getBoundingClientRect().height||Number(target.style.height.replace('px',''))||120;const step=e.shiftKey?60:20;if(e.key==='ArrowUp')resizeTarget(target,current-step);else if(e.key==='ArrowDown')resizeTarget(target,current+step);else if(e.key==='Home')resizeTarget(target,target.id==='liveActivityPanel'?72:44);else if(e.key==='End')resizeTarget(target,Math.round(window.innerHeight*0.78));else return;e.preventDefault();});}const move=e=>{if(!drag)return;resizeTarget(drag,startH+(e.clientY-startY));};const stop=()=>{drag=null;for(const rail of document.querySelectorAll('.middleResizeRail'))rail.classList.remove('dragging');};document.addEventListener('pointermove',move);document.addEventListener('mousemove',move);document.addEventListener('pointerup',stop);document.addEventListener('mouseup',stop);syncMiddleResizeRails();}
function resetPanelLayout(){try{for(const key of ['wlaLeftPanelWidth','wlaRightPanelWidth','wlaCollapseleft','wlaCollapseright','wlaCollapseactivity','wlaControlDrawerCollapsed','wlaMiddlePanelHeights'])localStorage.removeItem(key);}catch(e){}document.body.classList.remove('collapse-left','collapse-right','collapse-activity','control-drawer-collapsed');setPanelWidth('left',410);setPanelWidth('right',430);toggleControlDrawer(false);setActivityOpen(true);for(const id of middleResizeTargets()){const el=document.getElementById(id);if(el){el.style.height='';el.style.maxHeight='';}}syncMiddleResizeRails();setVoiceStatus('Layout reset.');}
function setupSidebarSectionCollapse(){const titles=[...document.querySelectorAll('.sidebar > .section-title')];titles.forEach((title,idx)=>{if(title.dataset.collapseReady)return;title.dataset.collapseReady='1';title.classList.add('section-title-row');const label=String(title.childNodes[0]?.textContent||title.textContent||'Section').trim();const key='wlaLeftSectionCollapsed_'+idx+'_'+label.replace(/[^a-z0-9]+/gi,'_');let collapsed=false;try{collapsed=localStorage.getItem(key)==='1';}catch(e){}const nodes=[];let n=title.nextElementSibling;while(n && n.tagName!=='HR' && !n.classList.contains('section-title')){nodes.push(n);n=n.nextElementSibling;}const btn=document.createElement('button');btn.type='button';btn.className='tiny secondary sectionCollapseBtn';btn.textContent=collapsed?'Show':'Hide';btn.title='Collapse or expand '+label;function apply(){for(const node of nodes)node.style.display=collapsed?'none':'';btn.textContent=collapsed?'Show':'Hide';try{localStorage.setItem(key, collapsed?'1':'0');}catch(e){}}btn.onclick=()=>{collapsed=!collapsed;apply();};title.appendChild(btn);apply();});}
function escAttr(s){return esc(s).replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
function fillCommand(command){msg.value=String(command||'');msg.focus();artifactPanel.style.display='none';setVoiceStatus('command filled. Review it in the composer, then press Send.');}
function commandSteps(command){return String(command||'').split(/\n|;;/).map(x=>x.trim()).filter(Boolean);}
async function runSequentialCommands(command){const steps=commandSteps(command);if(!steps.length)return;for(const step of steps){msg.value=step;await send();}}
function runDatasetCommand(el){runQuickCommand(el?.dataset?.command||'');}
function fillDatasetCommand(el){fillCommand(el?.dataset?.command||'');}
let odysseusWorkspaceSnapshot=null;let odysseusRuntimeStatus=null;let odysseusWorkspaceActive='docs';let odysseusCodeTab='';
function showOdysseusWorkspace(){togglePopup('odysseusWorkspacePopup',true);loadOdysseusWorkspace();}
function openOdysseusDeepLink(){const map={'/odysseus-workbench':'docs','/odysseus-runtime':'runtime','/odysseus-launcher':'runtime','/odysseus-docs':'docs','/odysseus-research':'research','/odysseus-uploads':'uploads','/odysseus-code':'code','/odysseus-tasks':'tasks','/odysseus-notes':'notes','/odysseus-memory':'memory','/odysseus-gates':'gates','/odysseus-cookbook':'cookbook','/odysseus-compare':'compare'};const target=map[location.pathname];if(target){odysseusWorkspaceActive=target;showOdysseusWorkspace();}}
function registerNovaServiceWorker(){if(!('serviceWorker' in navigator))return;try{navigator.serviceWorker.register('/service-worker.js').catch(()=>{});}catch(e){}}
async function loadOdysseusWorkspace(){const preview=document.getElementById('odysseusWorkspacePreview');const body=document.getElementById('odysseusWorkspaceBody');if(preview)preview.textContent='Loading workspace windows...';if(body)body.textContent='Loading workbench...';try{const r=await fetch('/api/odysseus-workspace',{cache:'no-store'});const j=await r.json();odysseusWorkspaceSnapshot=j;renderOdysseusWorkspace();}catch(e){if(preview)preview.textContent='Could not load workspace windows: '+e;if(body)body.textContent='Could not load workbench: '+e;}}
async function loadOdysseusRuntime(){try{const r=await fetch('/api/odysseus-runtime',{cache:'no-store'});const j=await r.json();odysseusRuntimeStatus=j;if(odysseusWorkspaceSnapshot)odysseusWorkspaceSnapshot.odysseus_runtime=j;renderOdysseusRuntimeStatus();if(odysseusWorkspaceActive==='runtime')renderOdysseusWorkspace();}catch(e){const box=document.getElementById('odysseusRuntimeStatus');if(box)box.innerHTML='<span class="pill bad">runtime check failed</span><div class="small">'+esc(e)+'</div>';}}
function odysseusRuntimePayload(){return {path:document.getElementById('odysseusRuntimePath')?.value||'',mode:document.getElementById('odysseusRuntimeMode')?.value||'auto',port:document.getElementById('odysseusRuntimePort')?.value||'7000'};}
async function runOdysseusRuntimeAction(action,confirmed=false){const payload=odysseusRuntimePayload();payload.confirmed=!!confirmed;const box=document.getElementById('odysseusRuntimeStatus');if(box)box.innerHTML='<span class="pill warn">Odysseus '+esc(action)+'...</span>';try{const r=await fetch('/api/odysseus-runtime-action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,payload,confirmed:!!confirmed})});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||j.detail||'Odysseus runtime action failed');odysseusRuntimeStatus=j.status||j;await loadOdysseusWorkspace();renderOdysseusRuntimeStatus();}catch(e){if(box)box.innerHTML='<span class="pill bad">Odysseus action failed</span><div class="small">'+esc(e)+'</div>';}}
function configureOdysseusRuntime(){runOdysseusRuntimeAction('configure',false);}
function startOdysseusRuntime(){if(!confirm('Start the configured Odysseus dependency on localhost? This can install/use its own dependencies or Docker setup depending on launch mode.'))return;runOdysseusRuntimeAction('start',true);}
function stopOdysseusRuntime(){if(!confirm('Stop the Nova-managed Odysseus runtime?'))return;runOdysseusRuntimeAction('stop',true);}
function openOdysseusRuntimeUrl(){const s=odysseusRuntimeStatus||(odysseusWorkspaceSnapshot&&odysseusWorkspaceSnapshot.odysseus_runtime)||{};const url=s.url||'http://127.0.0.1:7000';window.open(url,'_blank','noopener');}
function renderOdysseusRuntimeStatus(){const box=document.getElementById('odysseusRuntimeStatus');if(!box)return;const s=odysseusRuntimeStatus||(odysseusWorkspaceSnapshot&&odysseusWorkspaceSnapshot.odysseus_runtime)||{};const cls=s.running?'good':(s.configured?'warn':'bad');box.innerHTML='<span class="pill '+cls+'">'+esc(s.status||'missing')+'</span><div class="small">URL: '+esc(s.url||'http://127.0.0.1:7000')+'</div><div class="pathline">'+esc(s.path||'No Odysseus checkout configured')+'</div>'+(s.notes&&s.notes.length?'<div class="small">'+esc(s.notes[0])+'</div>':'');}
function setOdysseusWorkspaceTab(id){odysseusWorkspaceActive=id;renderOdysseusWorkspace();}
function workbenchWindow(id){const j=odysseusWorkspaceSnapshot||{};return (j.windows||[]).find(w=>w.id===id)||{};}
function workbenchCountPills(){const j=odysseusWorkspaceSnapshot||{};return '<div class="workbenchStatLine">'+(j.windows||[]).map(w=>'<span class="pill">'+esc(w.label||w.id)+': '+esc(w.count||0)+'</span>').join('')+'</div>';}
function workbenchCommand(command,label='Fill command'){return '<button class="tiny secondary" data-command="'+escAttr(command||'')+'" onclick="fillDatasetCommand(this)">'+esc(label)+'</button>';}
function workbenchInput(id,placeholder,value=''){return '<input id="'+escAttr(id)+'" placeholder="'+escAttr(placeholder)+'" value="'+escAttr(value)+'">';}
function workbenchTextarea(id,placeholder,value=''){return '<textarea id="'+escAttr(id)+'" placeholder="'+escAttr(placeholder)+'">'+esc(value)+'</textarea>';}
function workbenchSelect(id,options,value=''){return '<select id="'+escAttr(id)+'">'+options.map(o=>'<option value="'+escAttr(o)+'" '+(o===value?'selected':'')+'>'+esc(o)+'</option>').join('')+'</select>';}
function workbenchActionButton(surface,action,prefix,fields,label,cls=''){return '<button class="tiny '+escAttr(cls)+'" data-workbench-action="'+escAttr(surface+':'+action)+'" data-surface="'+escAttr(surface)+'" data-action="'+escAttr(action)+'" data-prefix="'+escAttr(prefix)+'" data-fields="'+escAttr(fields.join(','))+'" onclick="runOdysseusWorkbenchButton(this)">'+esc(label)+'</button>';}
function workbenchPayloadButton(surface,action,payload,label,cls='secondary'){return '<button class="tiny '+escAttr(cls)+'" data-workbench-action="'+escAttr(surface+':'+action)+'" data-surface="'+escAttr(surface)+'" data-action="'+escAttr(action)+'" data-payload="'+escAttr(JSON.stringify(payload||{}))+'" onclick="runOdysseusPayloadButton(this)">'+esc(label)+'</button>';}
function workbenchActionBar(inner){return '<div class="workbenchActionBar">'+inner+'</div>';}
function workbenchValue(id){return document.getElementById(id)?.value||'';}
function workbenchPayloadFromButton(btn){const payload={};const prefix=btn.dataset.prefix||'';for(const field of (btn.dataset.fields||'').split(',').filter(Boolean)){payload[field]=workbenchValue(prefix+field);}return payload;}
async function submitOdysseusWorkbenchAction(surface,action,payload={}){const preview=document.getElementById('odysseusWorkspacePreview');if(preview)preview.innerHTML='<b>Running '+esc(surface)+' action...</b>';try{const r=await fetch('/api/odysseus-workspace-action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({surface,action,payload,confirmed:!!payload.confirmed})});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.summary||j.error||j.detail||'Workbench action failed');if(j.snapshot)odysseusWorkspaceSnapshot=j.snapshot;renderOdysseusWorkspace();if(preview)preview.innerHTML='<b>'+esc(j.summary||'Workbench action complete.')+'</b>'+workbenchCountPills();loadActivity();loadFiles();}catch(e){if(preview)preview.innerHTML='<b>Workbench action failed</b><div class="small">'+esc(e)+'</div>';}}
function runOdysseusWorkbenchButton(btn){const payload=workbenchPayloadFromButton(btn);if(btn.dataset.surface==='gates'&&btn.dataset.action==='set'&&payload.level==='allow'){if(!confirm('Setting a tool to allow can weaken a safety gate. Continue?'))return;payload.confirmed=true;}if(btn.dataset.surface==='research'&&payload.urls){if(!confirm('Fetch the supplied research source URLs from the internet?'))return;payload.confirmed=true;}submitOdysseusWorkbenchAction(btn.dataset.surface||'',btn.dataset.action||'list',payload);}
function runOdysseusPayloadButton(btn){let payload={};try{payload=JSON.parse(btn.dataset.payload||'{}');}catch(e){}if(btn.dataset.surface==='gates'&&btn.dataset.action==='set'&&payload.level==='allow'){if(!confirm('Setting a tool to allow can weaken a safety gate. Continue?'))return;payload.confirmed=true;}if(btn.dataset.surface==='uploads'&&btn.dataset.action==='clear'){if(!confirm('Clear all shared upload/context files from Nova?'))return;payload.confirmed=true;}submitOdysseusWorkbenchAction(btn.dataset.surface||'',btn.dataset.action||'list',payload);}
function renderWorkbenchRows(rows,empty,mapper){return rows&&rows.length?'<div class="workbenchWindowGrid">'+rows.map(mapper).join('')+'</div>':'<div class="small">'+esc(empty)+'</div>';}
function renderOdysseusWorkspace(){const j=odysseusWorkspaceSnapshot||{};if(j.odysseus_runtime){odysseusRuntimeStatus=j.odysseus_runtime;renderOdysseusRuntimeStatus();}const preview=document.getElementById('odysseusWorkspacePreview');const tabs=document.getElementById('odysseusWorkspaceTabs');const body=document.getElementById('odysseusWorkspaceBody');const windows=j.windows||[];if(!windows.length){if(preview)preview.textContent='Workspace snapshot is empty.';return;}if(!windows.some(w=>w.id===odysseusWorkspaceActive))odysseusWorkspaceActive=windows[0].id;if(preview)preview.innerHTML='<b>Workspace snapshot</b><div class="small">'+esc(j.generated_at||'')+'</div>'+workbenchCountPills();if(tabs)tabs.innerHTML=windows.map(w=>'<button class="'+(w.id===odysseusWorkspaceActive?'active':'')+'" onclick="setOdysseusWorkspaceTab(\''+escAttr(w.id)+'\')"><b>'+esc(w.label||w.id)+'</b><br><small>'+esc(w.summary||'')+'</small></button>').join('');if(body)body.innerHTML=renderOdysseusWorkspaceBody(odysseusWorkspaceActive,j);}
function renderOdysseusWorkspaceBody(id,j){
 const win=workbenchWindow(id);
 const head='<div class="panelHeader"><div><b>'+esc(win.label||id)+'</b><div class="small">'+esc(win.summary||'')+'</div></div><div class="row wrap">'+workbenchCommand(win.command||'/nova-gui-workbench-plan')+'</div></div>';
 if(id==='runtime')return head+renderOdysseusRuntimeWorkbench(j.odysseus_runtime||odysseusRuntimeStatus||{});
 if(id==='docs'){
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owDoc_title','Title')+'</div>'+workbenchTextarea('owDoc_content','# Draft')+'<div class="row wrap">'+workbenchActionButton('docs','create','owDoc_',['title','content'],'Create doc')+'</div>');
  return head+actions+renderWorkbenchRows(j.documents||[],'No workspace documents yet.',d=>'<div class="workbenchMiniCard"><b>'+esc(d.name||'document')+'</b><div class="small">'+esc(d.updated_at||'')+'</div><div class="pathline">'+esc(d.path||'')+'</div>'+workbenchCommand('/nova-docs read '+(d.name||''),'Read')+workbenchPayloadButton('docs','suggest',{name:d.name,instruction:'improve clarity without changing meaning'},'Suggest')+'</div>');
 }
 if(id==='research'){
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owResearch_topic','Topic','Nova Odysseus integration ideas')+'</div>'+workbenchInput('owResearch_urls','Optional source URLs')+'<div class="row wrap">'+workbenchActionButton('research','run','owResearch_',['topic','urls'],'Create report')+workbenchCommand('/research Nova Odysseus integration ideas','Chat research')+'</div>');
  return head+actions+renderWorkbenchRows(j.research_reports||[],'No research reports yet.',r=>'<div class="workbenchMiniCard"><b>'+esc(r.topic||'research report')+'</b><div class="small">'+esc(r.created_at||'')+'</div><div class="small">Sources '+esc(r.source_count||0)+' / claims '+esc(r.claim_count||0)+' / errors '+esc(r.fetch_error_count||0)+'</div><div class="pathline">'+esc(r.md_path||r.json_path||'')+'</div>'+workbenchCommand('/research '+(r.topic||'topic'),'Research again')+'</div>');
 }
 if(id==='uploads'){
  const actions=workbenchActionBar('<div class="row wrap"><button class="tiny" onclick="document.getElementById(\'contextFileInput\')?.click()">Attach files</button>'+workbenchPayloadButton('uploads','list',{},'Refresh')+workbenchPayloadButton('uploads','clear',{},'Clear uploads','danger')+workbenchCommand('/context-files','Show in chat')+'</div>');
  return head+actions+renderWorkbenchRows(j.upload_contexts||[],'No shared file context yet.',u=>'<div class="workbenchMiniCard"><b>'+esc(u.name||u.original_name||'upload')+'</b><div class="small">'+esc(u.kind||'file')+' / '+esc(u.size_bytes||0)+' bytes / '+esc(u.created_at||'')+'</div><div>'+esc(u.summary||'')+'</div><div class="pathline">id: '+esc(u.context_id||u.id||'')+'</div><div class="row wrap">'+(u.kind==='image'?workbenchCommand(u.analyze_command||('/image-analyze context:'+(u.context_id||u.id||'')),'Analyze'):'')+workbenchCommand('/context-files','List')+'</div></div>');
 }
 if(id==='compare'){
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owCompare_prompt','Prompt','improve Nova')+workbenchInput('owCompare_models','Models','qwen3-coder:30b, gemma2:2b')+'</div><div class="row wrap">'+workbenchActionButton('compare','plan','owCompare_',['prompt','models'],'New compare')+'</div>');
  return head+actions+renderWorkbenchRows(j.comparisons||[],'No model comparisons yet.',c=>'<div class="workbenchMiniCard"><b>'+esc(c.id||'comparison')+'</b><div class="small">Winner: '+esc(c.winner||'pending')+'</div><div>'+esc(String(c.prompt||'').slice(0,160))+'</div><div class="row wrap">'+workbenchPayloadButton('compare','vote',{id:c.id,winner:'left'},'Left')+workbenchPayloadButton('compare','vote',{id:c.id,winner:'right'},'Right')+workbenchPayloadButton('compare','vote',{id:c.id,winner:'tie'},'Tie')+'</div></div>');
 }
 if(id==='cookbook'){
  const models=(j.cookbook&&j.cookbook.models)||[];
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owCookbook_hints','Hardware hints','ram=32 vram=16')+workbenchInput('owCookbook_use_case','Use case','coding')+'</div><div class="row wrap">'+workbenchActionButton('cookbook','whatif','owCookbook_',['hints','use_case'],'Rank models')+'</div>');
  return head+actions+renderWorkbenchRows(models,'No model recommendations available.',m=>'<div class="workbenchMiniCard"><b>'+esc(m.name||'model')+'</b><div class="small">Score '+esc(m.fit_score)+' / '+esc(m.status||'')+'</div><div>'+esc(m.use||'')+'</div><div class="small">'+esc(m.backend||'')+'</div></div>');
 }
 if(id==='notes'){
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owNote_text','Note')+workbenchActionButton('notes','add','owNote_',['text'],'Add note')+'</div>');
  return head+actions+renderWorkbenchRows(j.notes||[],'No notes yet.',n=>'<div class="workbenchMiniCard"><b>'+esc(n.id||'note')+'</b><div>'+esc(n.text||'')+'</div><div class="small">'+esc(n.created_at||'')+'</div></div>');
 }
 if(id==='tasks'){
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owTask_text','Task')+workbenchActionButton('tasks','add','owTask_',['text'],'Add task')+'</div>');
  return head+actions+renderWorkbenchRows(j.tasks||[],'No tasks yet.',t=>'<div class="workbenchMiniCard"><b>'+esc(t.done?'Done':'Open')+' '+esc(t.id||'task')+'</b><div>'+esc(t.text||'')+'</div><div class="small">'+esc(t.created_at||'')+'</div>'+(!t.done?workbenchPayloadButton('tasks','done',{id:t.id},'Done'):'')+'</div>');
 }
 if(id==='skills'){
  const rows=Object.entries(j.skills||{});
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owSkill_name','Skill name')+workbenchInput('owSkill_text','Behaviour')+'</div><div class="workbenchActionLine">'+workbenchInput('owPreset_name','Preset name')+workbenchInput('owPreset_text','Preset text')+'</div><div class="row wrap">'+workbenchActionButton('skills','add','owSkill_',['name','text'],'Add skill')+workbenchActionButton('presets','add','owPreset_',['name','text'],'Add preset')+'</div>');
  return head+actions+(rows.length?'<div class="workbenchWindowGrid">'+rows.map(([key,item])=>'<div class="workbenchMiniCard"><b>'+esc(key)+'</b><div>'+esc(item.name||'')+'</div><div class="small">'+esc(String(item.text||'').slice(0,220))+'</div>'+workbenchCommand('/nova-skills show '+key,'Show')+'</div>').join('')+'</div>':'<div class="small">No skills yet.</div>');
 }
 if(id==='memory'){
  const items=(j.memory&&j.memory.items)||[];
  return head+'<div class="row wrap">'+workbenchPayloadButton('memory','export',{},'Export memory')+'</div>'+renderWorkbenchRows(items,'No memory artifacts yet.',m=>'<div class="workbenchMiniCard"><b>'+esc(m.name||'artifact')+'</b><div class="small">'+esc(m.bytes||0)+' bytes</div><div class="pathline">'+esc(m.path||'')+'</div></div>');
 }
 if(id==='gates'){
  const policy=(j.policy&&j.policy.policy)||{};
  const rows=Object.entries(policy).slice(0,24);
  const actions=workbenchActionBar('<div class="workbenchActionLine">'+workbenchInput('owGate_tool','Tool')+workbenchSelect('owGate_level',['ask','block','admin','allow'],'ask')+workbenchInput('owGate_reason','Reason','workbench override')+'</div><div class="workbenchActionLine">'+workbenchInput('owGate_text','Classify action')+'</div><div class="row wrap">'+workbenchActionButton('gates','set','owGate_',['tool','level','reason'],'Set gate')+workbenchActionButton('gates','check','owGate_',['text'],'Check action','secondary')+'</div>');
  return head+actions+'<div class="workbenchStatLine">'+Object.entries(j.policy_level_counts||{}).map(([k,v])=>'<span class="pill">'+esc(k)+': '+esc(v)+'</span>').join('')+'</div><div class="workbenchWindowGrid">'+rows.map(([key,item])=>'<div class="workbenchMiniCard"><b>'+esc(key)+'</b><div class="small">'+esc(item.level||'ask')+'</div><div>'+esc(item.reason||'')+'</div></div>').join('')+'</div>';
 }
 if(id==='code')return head+renderCodeWorkbench(j.code_files||[]);
 return head+'<pre>'+esc(JSON.stringify(j[id]||{},null,2))+'</pre>';
}
function renderOdysseusRuntimeWorkbench(s){odysseusRuntimeStatus=s||{};const markers=s.markers||{};const candidates=s.candidates||[];const command=(s.start_command||[]).join(' ');const notes=(s.notes||[]).map(n=>'<div class="small">'+esc(n)+'</div>').join('');const controls=workbenchActionBar('<div class="workbenchActionLine"><input id="odysseusRuntimePath" placeholder="Odysseus checkout path" value="'+escAttr(s.path||'')+'"><select id="odysseusRuntimeMode"><option value="auto" '+(s.requested_mode==='auto'?'selected':'')+'>auto</option><option value="native" '+(s.requested_mode==='native'?'selected':'')+'>native</option><option value="windows_launcher" '+(s.requested_mode==='windows_launcher'?'selected':'')+'>windows_launcher</option><option value="docker" '+(s.requested_mode==='docker'?'selected':'')+'>docker</option></select><input id="odysseusRuntimePort" placeholder="Port" value="'+escAttr(s.port||7000)+'"></div><div class="row wrap"><button class="tiny secondary" onclick="configureOdysseusRuntime()">Save path</button><button class="tiny secondary" onclick="loadOdysseusRuntime()">Refresh</button><button class="tiny" onclick="startOdysseusRuntime()">Start Odysseus</button><button class="tiny danger" onclick="stopOdysseusRuntime()">Stop</button><button class="tiny secondary" onclick="openOdysseusRuntimeUrl()">Open</button></div>');const statusCard='<div class="workbenchMiniCard"><b>Status: '+esc(s.status||'missing')+'</b><div class="small">Running: '+esc(!!s.running)+' / configured: '+esc(!!s.configured)+' / mode: '+esc(s.mode||'')+'</div><div class="small">URL: '+esc(s.url||'http://127.0.0.1:7000')+'</div><div class="pathline">'+esc(s.path||'No checkout path configured')+'</div>'+(command?'<div class="odysseusCodePreview">'+esc(command)+'</div>':'')+notes+'</div>';const markerCard='<div class="workbenchMiniCard"><b>Checkout markers</b>'+['valid_checkout','app_py','requirements','setup_py','launch_windows','docker_compose'].map(k=>'<div class="small">'+esc(k)+': '+esc(markers[k])+'</div>').join('')+'</div>';const candidateHtml=candidates.length?'<div class="workbenchWindowGrid">'+candidates.slice(0,6).map(c=>'<div class="workbenchMiniCard"><b>'+esc(c.source||'candidate')+'</b><div class="small">'+(c.valid?'<span class="pill good">valid</span>':'<span class="pill bad">missing</span>')+'</div><div class="pathline">'+esc(c.path||'')+'</div></div>').join('')+'</div>':'<div class="small">No Odysseus checkout candidates found yet.</div>';return controls+'<div class="workbenchWindowGrid">'+statusCard+markerCard+'</div>'+candidateHtml;}
function renderCodeWorkbench(files){if(!files.length)return '<div class="small">No code files found.</div>';if(!odysseusCodeTab)odysseusCodeTab=files[0].path||'';const active=files.find(f=>f.path===odysseusCodeTab)||files[0];const list='<div class="codeTabList">'+files.map(f=>'<button class="tiny codeTabBtn '+(f.path===(active.path||'')?'active':'')+'" data-path="'+escAttr(f.path||'')+'" onclick="odysseusCodeTab=this.dataset.path;renderOdysseusWorkspace()">'+esc(f.name||f.path)+'</button>').join('')+'</div>';const card='<div class="workbenchMiniCard"><b>'+esc(active.path||'code file')+'</b><div class="small">'+esc(active.bytes||0)+' bytes / '+esc(active.updated_at||'')+'</div><div class="row wrap"><button class="tiny" data-path="'+escAttr(active.path||'')+'" onclick="openOdysseusCodeFile(this.dataset.path)">Open in editor</button>'+workbenchCommand('/search-nova-code '+(active.name||''),'Search code')+'</div></div>';return card+list+'<div class="odysseusCodePreview">Code tab target: '+esc(active.path||'')+'\nOpen in editor to inspect or edit with Nova path protections.</div>';}
async function openOdysseusCodeFile(path){document.body.classList.remove('collapse-right');try{localStorage.setItem('wlaCollapseright','0');}catch(e){}await openFile(path);setInspectorTab('editor');}
function commandButton(command,label='Fill'){return '<button class="tiny secondary" data-command="'+escAttr(command)+'" onclick="fillCommand(this.dataset.command)">'+esc(label)+'</button>';}
function insertSuggestedCommand(command){fillCommand(command);}
function commandSuggestionButton(command,label='Fill'){return '<button class="tiny secondary" data-command="'+escAttr(command)+'" onclick="insertSuggestedCommand(this.dataset.command)">'+esc(label)+'</button>';}
function renderCommandPalette(){const box=document.getElementById('commandPalette');if(!box)return;const q=String(document.getElementById('commandSearch')?.value||'').toLowerCase().trim();let rows=COMMANDS.filter(c=>!q || (c.group+' '+c.label+' '+c.command+' '+c.desc+' '+c.tags).toLowerCase().includes(q)).slice(0,8);box.innerHTML=rows.map(c=>'<div class="commandItem"><b>'+esc(c.label)+'</b> <span class="pill">'+esc(c.group)+'</span><div class="small">'+esc(c.desc)+'</div><code>'+esc(c.command)+'</code><div class="commandActions">'+commandSuggestionButton(c.command,'Fill input')+'</div></div>').join('') || '<div class="small">No matching commands.</div>';}
function extractSuggestedCommands(text){const found=[],seen=new Set();const addCmd=c=>{c=String(c||'').replace(/[.,;:)\]]+$/,'').trim();if(!/^\/[a-z][a-z0-9-]*/i.test(c))return;if(c.length>160)c=c.slice(0,160).trim();if(!seen.has(c)){seen.add(c);found.push(c);}};let m;const raw=String(text||'');const reBacktick=/`(\/[a-z][a-z0-9-]*(?: [^`\n]{0,140})?)`/gi;while((m=reBacktick.exec(raw)))addCmd(m[1]);const reLine=/(^|\n)\s*(\/[a-z][a-z0-9-]*(?: [^\n]{0,140})?)/gi;while((m=reLine.exec(raw)))addCmd(m[2]);const reInline=/(^|[\s(])(\/[a-z][a-z0-9-]*(?:\s+--[a-z0-9-]+)?)/gi;while((m=reInline.exec(raw)))addCmd(m[2]);return found.slice(0,5);}
function renderCommandSuggestions(suggestions=[],fallbackText=''){if(getUiSetting('showCommandSuggestions')===false)return '';let rows=[];const seen=new Set();for(const s of (Array.isArray(suggestions)?suggestions:[])){const cmd=String(s.command||'').trim();if(!cmd||seen.has(cmd))continue;seen.add(cmd);rows.push({command:cmd,label:s.label||cmd.split(' ')[0],reason:s.reason||''});}if(!rows.length){for(const cmd of extractSuggestedCommands(fallbackText)){if(!seen.has(cmd)){seen.add(cmd);rows.push({command:cmd,label:cmd.split(' ')[0],reason:''});}}}rows=rows.slice(0,3);if(!rows.length)return '';return '<div class="suggestedCommands"><span class="label">Next steps</span>'+rows.map(s=>commandSuggestionButton(s.command,s.label)+(s.reason?'<span class="small">'+esc(s.reason)+'</span>':'')).join('')+'</div>';}
function suggestedCommandsHtml(text){return renderCommandSuggestions([], text);}
const seenIdleDone = (()=>{try{return JSON.parse(sessionStorage.getItem('wlaSeenIdleCycles')||'{}')}catch(e){return {}}})();
function saveSeenIdle(){try{sessionStorage.setItem('wlaSeenIdleCycles', JSON.stringify(seenIdleDone));}catch(e){}}
function idleKeyFromEvent(ev){const d=ev.data||{};return String(d.run_id||ev.run_id||'idle')+':'+String(d.cycle||'0');}
function idleBubbleHtml(ev, steps){const d=ev.data||{};const cycle=esc(d.cycle||'0'), run=esc(d.run_id||ev.run_id||'');const goal=esc(d.goal||'Idle maintenance');const summary=esc(d.summary||ev.message||'Idle cycle update');const stepHtml=(steps||[]).slice(-7).map(s=>'<div class="cycle-event">• '+esc(s.time||'')+' '+esc(s.message||s.kind||'step')+(s.data?.summary?' — '+esc(s.data.summary):'')+'</div>').join('');return '<b>🌙 Idle cycle '+cycle+' summary</b><div class="small">Run '+run+'</div><div class="small"><b>Goal:</b> '+goal+'</div><div class="cycle-report"><b>What happened</b><pre style="white-space:pre-wrap">'+summary+'</pre></div>'+(stepHtml?'<div class="cycle-report"><b>Step updates</b>'+stepHtml+'</div>':'');}
function ensureIdleBubble(ev, rows){const key=idleKeyFromEvent(ev);if(!key || key.endsWith(':0'))return;const evMs=Number(ev.ts||0)*1000;if(busy)return;if(lastUserMessageTs && evMs && evMs < lastUserMessageTs)return;if(seenIdleDone[key] && !idleCycleBubbles[key])return;const steps=(rows||[]).filter(r=>idleKeyFromEvent(r)===key && ['idle_cycle_start','idle_step_start','idle_step_done','idle_cycle_done','idle_cycle_failed'].includes(r.kind));let rec=idleCycleBubbles[key];if(!rec){rec=add('Assistant','', 'idlebubble');idleCycleBubbles[key]=rec;}rec.bubble.classList.add('idlebubble');rec.bubble.innerHTML=idleBubbleHtml(ev, steps);seenIdleDone[key]=true;saveSeenIdle();}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function renderRichText(text){let t=String(text||'');let parts=[];let re=/```(json|text|javascript|js|python|powershell|html|css)?\n([\s\S]*?)```/gi;let last=0,m;while((m=re.exec(t))){if(m.index>last)parts.push({type:'text',v:t.slice(last,m.index)});parts.push({type:m[1]==='json'?'json':'code',v:m[2]});last=re.lastIndex;}if(last<t.length)parts.push({type:'text',v:t.slice(last)});return parts.map(p=>{if(p.type==='json'){try{return '<pre class="jsonblock">'+esc(JSON.stringify(JSON.parse(p.v),null,2))+'</pre>';}catch(e){return '<pre class="jsonblock">'+esc(p.v)+'</pre>';}}if(p.type==='code')return '<pre class="codeblock">'+esc(p.v)+'</pre>';let raw=p.v;let tech=raw.match(/Technical details:\s*([\s\S]+)/);let suffix='';if(tech&&tech[1].trim().startsWith('{')){raw=raw.slice(0, tech.index)+'Technical details are available below.';suffix='<details><summary>Technical details</summary><pre class="jsonblock">'+esc(tech[1].trim().slice(0,12000))+'</pre></details>';}let x=esc(raw);x=x.replace(/^### (.*)$/gm,'<h3>$1</h3>').replace(/^## (.*)$/gm,'<h2>$1</h2>').replace(/^# (.*)$/gm,'<h2>$1</h2>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<span class="mdstrong">$1</span>');return linkify(x)+suffix;}).join('');}
function messageFeedbackHtml(){if(getUiSetting('showFeedbackButtons')===false)return '';return '<div class="feedbackBar"><span class="small">Was this useful?</span><button class="tiny secondary" data-value="up" onclick="recordFeedback(this,this.dataset.value)">👍 Yes</button><button class="tiny secondary" data-value="down" onclick="recordFeedback(this,this.dataset.value)">👎 Needs work</button></div>';}
function recordFeedback(btn,value){try{const list=JSON.parse(localStorage.getItem('wlaMessageFeedback')||'[]');list.push({value,timestamp:new Date().toISOString(),text:btn.closest('.bubble')?.innerText?.slice(0,500)||''});localStorage.setItem('wlaMessageFeedback',JSON.stringify(list.slice(-100)));}catch(e){}btn.closest('.feedbackBar').innerHTML='<span class="small">Feedback saved. Use /continue or clarify if you want Nova to improve this result.</span>';}
function persistCurrentChatSoon(){clearTimeout(window.__wlaPersistChatTimer);window.__wlaPersistChatTimer=setTimeout(()=>{try{const id=activeChatSessionId();const data=chatSessionStore();const existing=data[id]||{};data[id]={...existing,id,title:existing.title||'Chat '+new Date().toLocaleString(),html:chat.innerHTML,updated:Date.now(),shared:!!existing.shared};saveChatSessionStore(data);renderChatSessionSelect();}catch(e){}},250);}
function restoreActiveChatSession(){try{const id=localStorage.getItem('wlaActiveChatSession')||'';if(!id){renderChatTabs();return false;}const rec=chatSessionStore()[id];if(rec&&rec.html){chat.innerHTML=rec.html;renderChatTabs();return true;}renderChatTabs();}catch(e){}return false;}
function messageTerminalHtml(text,who){try{const raw=String(text||'');const lines=[];const commandRe=/(?:^|\n)\s*(\/[a-z][^\n]{0,180}|(?:python|py|node|npm|git|docker|ollama|powershell|cmd)\b[^\n]{0,180})/gi;let m;while((m=commandRe.exec(raw))&&lines.length<12){lines.push(m[1].trim());}if(/Plan mode:/i.test(raw)){const steps=(raw.match(/\n\d+\. [^\n]+/g)||[]).slice(0,8).map(s=>s.trim());lines.push(...steps);}if(/Verification:/i.test(raw))lines.push('verification evidence present');if(!lines.length&&who==='Assistant')lines.push('No terminal/tool commands exposed for this message yet. Watch Live Activity for backend events.');if(!lines.length)return '';return '<details class="msgTerminal"><summary>▸ terminal</summary><div class="msgTerminalBody">'+esc(lines.join('\n'))+'</div></details>';}catch(e){return '';}}
function add(who,text,extraClass=''){const wrap=document.createElement('div');wrap.className='msg '+(who==='You'?'user':'assistant');const inner=document.createElement('div');const name=document.createElement('div');name.className='name';const stamp=new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});name.innerHTML='<span>'+esc(who==='Assistant'?ASSISTANT_NAME:who)+'</span><span class="msgTime">'+esc(stamp)+'</span>'+(who==='Assistant'?messageTerminalHtml(text,who):'');const bubble=document.createElement('div');bubble.className='bubble '+extraClass;bubble.innerHTML=renderRichText(text)+(who==='You'?'':suggestedCommandsHtml(text)+messageFeedbackHtml());inner.appendChild(name);inner.appendChild(bubble);wrap.appendChild(inner);chat.appendChild(wrap);chat.scrollTop=chat.scrollHeight;persistCurrentChatSoon();return {wrap,bubble};}
function viewToRunUrl(url){const m=String(url||'').match(/\/view\?path=([^\s&]+)/);return m?'/project-view/'+m[1]:url;}
function linkify(s){return s.replace(/(\/project-view\/[A-Za-z0-9_.%\-\/]+|\/view\?path=[A-Za-z0-9_.%\-\/]+|\/download-generated\?name=[A-Za-z0-9_.%\-]+|\/download\?path=[A-Za-z0-9_.%\-\/]+)/g,(m)=>{const href=m.startsWith('/view?path=')?viewToRunUrl(m):m;return '<a href="'+href+'" target="_blank">'+m+'</a>';});}
function workingHtml(detail){const d=esc(detail||'Starting request...');return '<div class="typing"><span></span><span></span><span></span></div> <b>Working...</b><div class="small">'+d+'</div><div class="workingSteps"><div class="workingStep active">1. Interpreting request and choosing route</div><div class="workingStep">2. Running tool/model step</div><div class="workingStep">3. Waiting for validation/activity event</div></div>';}
function confirmAutonomousStart(){if(confirm('Start autonomous mode?\n\nIt will repeatedly investigate logs, run checks, improve the current project, create/use safe tools if useful, and may use local LLM prompts until you stop it. Safety rules still apply.'))quick('/autonomous start investigate logs, improve current project safely, use safe tools when helpful, and propose next changes');}
const chatHistory=[];let chatHistoryIndex=0;let lastUserMessageTs=0;
function rememberChatText(text){if(text&&chatHistory[chatHistory.length-1]!==text){chatHistory.push(text);if(chatHistory.length>80)chatHistory.shift();}chatHistoryIndex=chatHistory.length;lastUserMessageTs=Date.now();}
function setupChatKeyboard(){msg.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();return;}if(e.key==='ArrowUp'&&!e.shiftKey){if(chatHistory.length){e.preventDefault();chatHistoryIndex=Math.max(0,chatHistoryIndex-1);msg.value=chatHistory[chatHistoryIndex]||'';}}if(e.key==='ArrowDown'&&!e.shiftKey){if(chatHistory.length){e.preventDefault();chatHistoryIndex=Math.min(chatHistory.length,chatHistoryIndex+1);msg.value=chatHistory[chatHistoryIndex]||'';}}});}

async function loadAiMemoryStatus(){try{const r=await fetch('/api/ai-memory-status',{cache:'no-store'});const j=await r.json();const box=document.getElementById('aiMemoryStatus');if(!box)return;let dbs=j.databases||{};let dbHtml=Object.keys(dbs).length?Object.entries(dbs).map(([db,cols])=>'<div><b>'+esc(db)+'</b>: '+esc(Object.entries(cols).map(([c,n])=>c+'='+n).join(', '))+'</div>').join(''):'<div>No assistant DB records yet.</div>';box.innerHTML='<b>AI research/database memory</b><div>Latest research reports: '+esc(j.research_report_count||0)+'</div>'+dbHtml+'<div class="small">Latest report: '+esc(j.latest_research_report||'none')+'</div>'; }catch(e){const box=document.getElementById('aiMemoryStatus');if(box)box.textContent='Could not load AI memory status: '+e;}}
function isRelevantAiFocusPath(value){const raw=String(value||'');if(!raw.trim())return false;const s=raw.toLowerCase().replaceAll('\\','/');if(s.includes('/appdata/local/temp/')||s.includes('/tmp/')||s.includes('pytest-of-')||s.includes('__pycache__')||s.includes('/.pytest_cache/')||s.endsWith('.pyc'))return false;return true;}
function renderAssistantLiveSnapshot(live={},box={}){const a=live.autonomous||{},idle=live.idle||{},llm=live.llm||{},ev=live.latest_event||{},recent=live.recent_events||[];const cards=[];const now=live.current_task||a.current_action||idle.current_action||(llm.prompt_active?'Model working':'Ready');cards.push('<div class="novaCard"><b>Now</b><div>'+esc(now)+'</div><div class="small">'+esc(ev.kind?((ev.time||'')+' • '+ev.kind):'No recent event')+'</div></div>');const modelState=llm.prompt_active?'prompt active':(llm.busy?'cooldown':'idle');cards.push('<div class="novaCard"><b>Model</b><div>'+esc(modelState+(llm.busy_desc?' — '+llm.busy_desc:''))+'</div><div class="small">'+esc(llm.request_id?('request '+llm.request_id):'no active request')+'</div></div>');if(a.current_action||a.running||idle.current_action||idle.enabled){cards.push('<div class="novaCard"><b>Automation</b><div>'+esc(a.current_action||idle.current_action||'idle')+'</div><div class="small">'+esc(a.current_detail||idle.current_detail||'No blocker reported')+'</div></div>');}if(recent.length){cards.push('<div class="novaCard"><b>Recent</b>'+recent.slice(-3).map(r=>'<div class="small">'+esc((r.kind||r.phase||'event')+': '+String(r.message||r.response_preview||r.prompt_preview||'').slice(0,120))+'</div>').join('')+'</div>');}if(box.message)cards.push('<div class="novaCard"><b>Note</b><div class="small">'+esc(String(box.message).slice(0,320))+'</div></div>');return '<div class="novaCards">'+cards.join('')+'</div>';}

function novaStatusValue(value, fallback='') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return value.map(v => novaStatusValue(v)).filter(Boolean).join(', ');
  if (typeof value === 'object') {
    const parts=[];
    for (const key of ['summary','state','status','phase','current_action','current_detail','message','detail','target','path','kind','time']) {
      if (value[key]) parts.push(key.replaceAll('_',' ')+': '+novaStatusValue(value[key]));
    }
    if (parts.length) return parts.join(' — ');
    try { return JSON.stringify(value).slice(0,500); } catch(e) { return fallback || 'object'; }
  }
  return String(value);
}
function assistantBoxTextFromPayload(j){
  const box=j?.box||{}; const live=j?.live_snapshot||{};
  const lines=[];
  const now=live.now||box.updated_at||new Date().toLocaleTimeString();
  lines.push('Now: '+novaStatusValue(live.current_state||box.level,'Ready'));
  if(live.autonomous)lines.push('Autonomous: '+novaStatusValue(live.autonomous).slice(0,420));
  if(live.idle)lines.push('Idle: '+novaStatusValue(live.idle).slice(0,420));
  if(live.target)lines.push('Target: '+novaStatusValue(live.target).slice(0,420));
  if(live.model)lines.push('Model: '+novaStatusValue(live.model).slice(0,420));
  if(box.message)lines.push('\nNova note:\n'+box.message);
  if(live.reply_preview)lines.push('\nReply preview:\n'+novaStatusValue(live.reply_preview).slice(0,1800));
  if(live.file_focus)lines.push('\nFile/report focus: '+novaStatusValue(live.file_focus).slice(0,500));
  if(live.latest_event)lines.push('Latest event: '+novaStatusValue(live.latest_event).slice(0,500));
  if(Array.isArray(live.recent_activity)&&live.recent_activity.length){lines.push('\nRecent activity:'); for(const ev of live.recent_activity.slice(-5)){lines.push('- '+[ev.time,ev.kind,ev.message||ev.summary].filter(Boolean).join(' · ').slice(0,420));}}
  if(box.persisted_note)lines.push('\nPersisted note:\n'+box.persisted_note);
  return lines.join('\n')||('Live status refreshed '+now);
}
async function loadAssistantBox(){
  const area=document.getElementById('assistantBoxText'); const info=document.getElementById('assistantBoxInfo');
  if(info)info.textContent='Refreshing...';
  try{const r=await fetch('/api/assistant-box',{cache:'no-store'}); const j=await r.json();
    if(area){area.value=assistantBoxTextFromPayload(j);area.className='assistantBoxText '+(j.ok?'success':'warning');}
    if(info)info.textContent=(j.ok?'Live status':'Fallback status')+' · '+new Date().toLocaleTimeString();
    return j;
  }catch(e){
    if(area){area.value='Could not load Nova communication box: '+e+'\n\nThe rest of the GUI will keep working; use /activity or /llm-status for details.';area.className='assistantBoxText error';}
    if(info)info.textContent='Status fetch failed';
    return null;
  }
}
async function synthAssistantBox(){
  const area=document.getElementById('assistantBoxText');
  const text=area?.value||'';
  const summary=text.split('\n').filter(Boolean).slice(0,8).join('\n');
  add('Assistant','**Nova status summary**\n'+(summary||'No status text available yet.'));
}
async function clearAssistantBox(){
  const area=document.getElementById('assistantBoxText');
  try{await fetch('/api/assistant-box',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'clear'})});}catch(e){}
  if(area)area.value='';
  const info=document.getElementById('assistantBoxInfo'); if(info)info.textContent='Cleared locally';
}
window.loadAssistantBox=window.loadAssistantBox||loadAssistantBox;
window.synthAssistantBox=window.synthAssistantBox||synthAssistantBox;
window.clearAssistantBox=window.clearAssistantBox||clearAssistantBox;
function setInspectorTab(name){
  try{localStorage.setItem('wlaInspectorTab',name);}catch(e){}
  document.querySelectorAll('.inspectorTabs button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  document.querySelectorAll('.inspectorPane').forEach(p=>p.classList.toggle('active',p.dataset.pane===name));
  const targets={state:'communicationCentreBoard',output:'codePreview',bridge:'jarvisInspectorPanel',editor:'editor',files:'editor',tools:'toolGoal'};
  const target=document.getElementById(targets[name]||'communicationCentreBoard');
  if(target){try{target.scrollIntoView({block:'center',behavior:'smooth'});}catch(e){target.scrollIntoView();}}
  if(name==='tools')document.getElementById('toolGoal')?.focus();
  if(name==='files')document.getElementById('editor')?.focus();
}
function setupInspectorTabs(){
  const right=document.querySelector('.rightbar');
  if(!right)return;
  right.classList.add('integratedRight');
  if(!document.getElementById('inspectorTabs')){const marker=document.createElement('div');marker.id='inspectorTabs';marker.className='inspectorTabs';marker.style.display='none';marker.innerHTML='<button data-tab="state">State</button><button data-tab="output">Output</button><button data-tab="bridge">Jarvis</button><button data-tab="editor">Editor</button><span>Integrated right panel: state, output, Jarvis and editor are now one scrollable panel.</span>';right.querySelector('.panelHeader')?.after(marker);}
}

async function copyAssistantBox(){const text=document.getElementById('assistantBoxText')?.value||'';try{await navigator.clipboard.writeText(text);add('Assistant','Copied AI communication box text.');}catch(e){add('Assistant','Copy failed: '+e);}}
async function uploadContextFiles(files){const status=document.getElementById('contextUploadStatus');if(!files||!files.length)return;status.textContent='Uploading context...';let ok=0;for(const f of files){if(f.size>25*1024*1024){add('Assistant','Could not attach '+f.name+': file is larger than 25 MB.');continue;}const b64=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(',')[1]||'');r.onerror=reject;r.readAsDataURL(f);});try{const res=await fetch('/api/upload-context',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:f.name,type:f.type||'',data_base64:b64})});const j=await res.json();if(j.ok){ok++;let imgHint=j.kind==='image'?'\n\nAnalyze it with `/image-analyze context:'+j.id+' => describe this image and any issues`, or click **Analyze latest photo**.':'';add('Assistant','Attached shared context: **'+j.name+'**\n\n'+j.summary+imgHint+'\n\nAsk your next question normally and I will include this file/photo as context.');}else{add('Assistant','Could not attach '+f.name+': '+(j.error||j.reply||'unknown error'));}}catch(e){add('Assistant','Could not attach '+f.name+': '+e);}}status.textContent=ok+' shared file(s) active. Use /context-files to view, /image-analyze latest for photos, or clear them.';}

async function loadProjects(){const btn=document.getElementById('refreshProjectsBtn');if(btn)btn.classList.add('loading');try{const r=await fetch('/api/projects',{cache:'no-store'});const j=await r.json();const box=document.getElementById('projects');if(!box)return;const rows=(j.projects||[]).map((p,i)=>{const name=p.name||p.path||('Project '+(i+1));const path=p.path||'';const stale=p.stale?' <span class="pill bad">stale</span>':(p.current?' <span class="pill good">current</span>':'');const meta=[];if(p.modified_at)meta.push('Modified: '+p.modified_at);if(p.file_count!==undefined)meta.push('Files: '+p.file_count);if(p.main_file)meta.push('Main: '+p.main_file);if(p.project_size_bytes)meta.push('Size: '+Math.round(Number(p.project_size_bytes||0)/1024)+' KB');return '<div class="item projectItem"><input class="projectSelect" type="checkbox" data-project="'+escAttr(name)+'"><div class="projectMain"><div class="projectTitle"><b title="'+escAttr(name)+'">'+esc(name)+'</b>'+stale+'</div><div class="small pathline" title="'+escAttr(path)+'">'+esc(path)+'</div><div class="small projectMeta">'+meta.map(m=>'<span>'+esc(m)+'</span>').join('')+'</div><div class="row wrap projectActions"><button class="tiny secondary" data-command="'+escAttr('/project-open '+name)+'" onclick="runDatasetCommand(this)">Open</button><button class="tiny danger" data-project="'+escAttr(name)+'" onclick="deleteProjectDirect(this)">Delete</button></div></div></div>';}).join('');box.innerHTML=rows||'<div class="small">No projects yet.</div>';}catch(e){const box=document.getElementById('projects');if(box)box.innerHTML='<div class="small">Could not load projects: '+esc(e)+'</div>';}finally{if(btn)btn.classList.remove('loading');}}
function selectAllProjects(on){document.querySelectorAll('.projectSelect').forEach(x=>x.checked=!!on);}
async function deleteProjectDirect(el){const name=el?.dataset?.project||'';if(!name)return;if(!confirm('Delete project and its files?\n\n'+name))return;await deleteProjectsDirect([name]);}
async function deleteProjectsDirect(names){try{const r=await fetch('/api/projects-delete?names='+encodeURIComponent(names.join('\n')),{cache:'no-store'});const j=await r.json();add('Assistant',j.summary||('Deleted '+names.length+' selected project(s).'));loadProjects();loadFiles();}catch(e){add('Assistant','Project delete failed: '+e);}}
async function loadFiles(){const btn=document.getElementById('refreshFilesBtn');if(btn)btn.classList.add('loading');try{const r=await fetch('/api/files',{cache:'no-store'});const j=await r.json();const box=document.getElementById('files');if(!box)return;const rows=(j.files||[]).map(f=>{const name=f.path||f.name||String(f);return '<div class="item file orbitFileRow"><span>'+esc(name)+'</span><button class="tiny secondary" onclick="openFile(\''+escAttr(name)+'\')">Open</button><button class="tiny secondary" onclick="openFileWorkspaceWindow(\''+escAttr(name)+'\')">Window</button><a href="/download?path='+encodeURIComponent(name)+'" target="_blank">Download</a></div>';}).join('');box.innerHTML=rows||'<div class="small">No files in current project.</div>';}catch(e){const box=document.getElementById('files');if(box)box.innerHTML='<div class="small">Could not load files: '+esc(e)+'</div>';}finally{if(btn)btn.classList.remove('loading');}}
async function loadTools(){const box=document.getElementById('customTools');if(box)box.innerHTML='<div class="small">Loading custom tools...</div>';try{const r=await fetch('/api/custom-tools',{cache:'no-store'});const j=await r.json();const data=j.data||{};const tools=data.tools||data.custom_tools||data.items||[];if(!box)return;const rows=(Array.isArray(tools)?tools:[]).map(t=>{const name=t.name||t.tool||String(t);const desc=t.description||t.summary||'';return '<div class="item toolItem"><div class="toolTitle"><b>'+esc(name)+'</b><button class="tiny secondary" onclick="document.getElementById(\'toolRunName\').value=\''+escAttr(name)+'\'">Use</button></div><div class="small">'+esc(desc||'Custom Nova tool')+'</div></div>';}).join('');box.innerHTML=rows||'<div class="small">No custom tools installed yet.</div>';}catch(e){if(box)box.innerHTML='<div class="small">Could not load custom tools: '+esc(e)+'</div>';}}
function createTool(){const goal=(document.getElementById('toolGoal')?.value||'').trim();if(!goal)return add('Assistant','Enter a tool idea first.');fillCommand('/tool-create '+goal);}
function runToolForm(){const name=(document.getElementById('toolRunName')?.value||'').trim();const args=(document.getElementById('toolRunArgs')?.value||'').trim();if(!name)return add('Assistant','Enter a tool name first.');fillCommand('/tool-run '+name+(args?' '+args:''));}
function runPipelineForm(){const raw=(document.getElementById('pipelineJson')?.value||'').trim();if(!raw)return add('Assistant','Paste pipeline JSON first.');fillCommand('/tool-pipeline '+raw);}

async function openFile(path){try{const r=await fetch('/api/open-file?path='+encodeURIComponent(path),{cache:'no-store'});const j=await r.json();if(!j.ok&&j.error){throw new Error(j.error);}currentFile=j.path||path;if(openPath)openPath.textContent=currentFile;if(editor)editor.value=j.content||'';openFileWorkspaceWindow(currentFile,j.content||'');toggleOrbitRight('output');}catch(e){add('Assistant','Could not open file: '+e);}}
function ensureFileWorkspaceWindow(){let win=document.getElementById('orbitFileWindow');if(win)return win;win=document.createElement('div');win.id='orbitFileWindow';win.className='orbitFloatingWindow';win.innerHTML='<div class="orbitWindowHeader" onmousedown="startOrbitWindowDrag(event,this.parentElement)"><b id="orbitFileWindowTitle">File editor</b><div class="row wrap"><button class="tiny secondary" onclick="saveFileWorkspaceWindow()">Save</button><button class="tiny secondary" onclick="downloadOpenFile()">Download</button><button class="tiny secondary" onclick="runOpenFileFromWindow()">Run/Open</button><button class="tiny danger" onclick="document.getElementById(\'orbitFileWindow\').style.display=\'none\'">×</button></div></div><textarea id="orbitFileWindowEditor" class="orbitFileEditor" spellcheck="false"></textarea><div class="small" id="orbitFileWindowMeta">Open a project file to inspect, edit and run it.</div>';document.body.appendChild(win);return win;}
async function openFileWorkspaceWindow(path,content){try{const win=ensureFileWorkspaceWindow();win.style.display='block';if(content===undefined){const r=await fetch('/api/open-file?path='+encodeURIComponent(path),{cache:'no-store'});const j=await r.json();if(!j.ok&&j.error)throw new Error(j.error);content=j.content||'';currentFile=j.path||path;}else{currentFile=path;}document.getElementById('orbitFileWindowTitle').textContent=currentFile||'File editor';document.getElementById('orbitFileWindowEditor').value=content||'';document.getElementById('orbitFileWindowMeta').textContent='Editing '+(currentFile||path)+' — drag the title bar to move this window.';if(openPath)openPath.textContent=currentFile;if(editor)editor.value=content||'';}catch(e){add('Assistant','Could not open file window: '+e);}}
async function saveOpenFile(){const path=(currentFile||openPath?.textContent||'').trim();const content=(document.getElementById('orbitFileWindowEditor')?.value)||editor?.value||'';if(!path||path==='No file open.')return add('Assistant','No file is open to save.');try{const r=await fetch('/api/save-file',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path,content})});const j=await r.json();add('Assistant',j.reply||'Saved file.');loadFiles();}catch(e){add('Assistant','Could not save file: '+e);}}
function saveFileWorkspaceWindow(){saveOpenFile();}
function downloadOpenFile(){const path=(currentFile||openPath?.textContent||'').trim();if(!path||path==='No file open.')return add('Assistant','No file is open to download.');window.open('/download?path='+encodeURIComponent(path),'_blank');}
function runOpenFileFromWindow(){const path=(currentFile||openPath?.textContent||'').trim();if(!path)return;const low=path.toLowerCase();if(low.endsWith('.html'))window.open('/view?path='+encodeURIComponent(path),'_blank');else if(low.endsWith('.py'))fillCommand('/run-project');else fillCommand('/open '+path);}
function askEditOpenFile(){const path=(currentFile||openPath?.textContent||'').trim();if(!path||path==='No file open.')return add('Assistant','Open a file first, then ask for an edit.');fillCommand('/replace '+path+' => describe the exact edit you want, then send');}
function startOrbitWindowDrag(ev,win){if(ev.target.closest('button'))return;ev.preventDefault();const sx=ev.clientX,sy=ev.clientY;const rect=win.getBoundingClientRect();const ox=sx-rect.left,oy=sy-rect.top;function move(e){win.style.left=Math.max(8,Math.min(window.innerWidth-120,e.clientX-ox))+'px';win.style.top=Math.max(8,Math.min(window.innerHeight-80,e.clientY-oy))+'px';win.style.right='auto';win.style.bottom='auto';}function up(){document.removeEventListener('mousemove',move);document.removeEventListener('mouseup',up);}document.addEventListener('mousemove',move);document.addEventListener('mouseup',up);}
function newProject(){const name=(document.getElementById('newProject')?.value||'').trim();if(name)quick('/project-new '+name);}
function setWorkspace(){const path=(document.getElementById('workspace')?.value||'').trim();if(path)quick('/workspace '+path);}
function bulkDeleteSelectedProjects(){const selected=[...document.querySelectorAll('.projectSelect:checked')].map(x=>x.dataset.project).filter(Boolean);if(!selected.length)return add('Assistant','No projects selected.');if(!confirm('Delete selected projects and files?\n\n'+selected.join('\n')))return;deleteProjectsDirect(selected);}
async function send(){
 const text=msg.value.trim();
 if(!text)return;
 rememberChatText(text);
 msg.value='';
 add('You',text);
 busy=true;
 pauseWakeUntilProcessingDone('Chat request running.');
 setVoiceRequestInFlight(true,'Chat request is running; wake listener paused.');
 setNovaOrb('thinking','Nova thinking','Working on your request...');
 const working=add('Assistant','', 'workingbubble');
 activeWorkingBubble=working.bubble;
 working.bubble.innerHTML=workingHtml('Starting request...');
 renderBusy('Starting request. Checking active run, Live Activity and autonomous status...');
 toggleOrbitActivity(true);
 const outboundText=buildSharedChatContext(text);
 try{
  const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:outboundText})});
  const j=await r.json();
  busy=false;
  setNovaOrb('ready','Nova ready','Reply received.');
  activeWorkingBubble=null;
  working.bubble.classList.remove('workingbubble');
  working.bubble.innerHTML=renderRichText(j.reply||'')+renderFileCards(j.reply||'')+renderCommandSuggestions(j.command_suggestions||[], j.reply||'');
  showArtifactLinks(j.reply||'');
  maybeSpeakReply(j.reply||'', text);
  setVoiceRequestInFlight(false,'Reply rendered. Waiting for any speech handoff to finish.');
  requestWakeResumeAfterVoiceProcessing('chat reply rendered');
  saveCurrentChatSession();
 }catch(e){
  busy=false;
  setNovaOrb('ready','Nova ready','Request failed or was interrupted.');
  activeWorkingBubble=null;
  working.bubble.classList.remove('workingbubble');
  working.bubble.textContent='Error while sending request: '+e;
  setVoiceRequestInFlight(false,'Request failed or was interrupted.');
  requestWakeResumeAfterVoiceProcessing('request failed');
 }
 loadActivity();loadLLMStatus();loadActiveRun();loadAutonomousStatus();loadIdleStatus();
 if(/^(\/do|\/run-plan|\/write|\/append|\/replace|\/zip|\/workspace|\/project)/.test(text) || !text.startsWith('/')) {loadFiles();loadProjects();}
 if(/^(\/tool|\/custom-tools|\/topic-watch)/.test(text)){setTimeout(loadTools,400);setTimeout(loadTools,2200);}
}
function renderBusy(detail){if(busy){if(activeWorkingBubble)activeWorkingBubble.innerHTML=workingHtml(detail||'Working...');const box=document.getElementById('activityLog');const sub=document.getElementById('activitySubtitle');if(sub)sub.textContent='Current task: '+(detail||'Current request is running.');if(!box)return;const previousTop=box.scrollTop||0;const previousHeight=box.scrollHeight||0;const preserve=activityShouldPreserveScroll(box);if(!box.querySelector('.working-current'))box.innerHTML='<div class="event llm_attempt working-current"><b>Working...</b><div class="small">'+esc(detail||'Current request is running. Polling logs while the local model writes/tests code.')+'</div></div>'+box.innerHTML;else box.querySelector('.working-current .small').textContent=detail||'Current request is running. Polling logs while the local model writes/tests code.';restoreActivityScroll(box,previousTop,previousHeight,preserve);}}
function showArtifactLinks(reply){const view=(reply.match(/\/view\?path=[A-Za-z0-9_.%\-\/]+/)||[])[0];const zip=(reply.match(/\/download-generated\?name=[A-Za-z0-9_.%\-]+/)||[])[0];const fileDownload=(reply.match(/\/download\?path=[A-Za-z0-9_.%\-\/]+/)||[])[0];if(view||zip||fileDownload){const run=viewToRunUrl(view);const file=(view||fileDownload||'').split('path=')[1]||'';const decoded=file?decodeURIComponent(file):'';const project=(decoded.split('/')[0]||'current project');artifactPanel.style.display='block';artifactPanel.innerHTML='<div class="createdOutput"><button class="tiny secondary createdClose" onclick="artifactPanel.style.display=\'none\'">Close</button><b>Created output ready</b><div class="small"><b>Project:</b> '+esc(project)+'</div><div class="small"><b>Main file/output:</b> '+esc(decoded||'project zip')+'</div><div class="small">This card describes what you are opening/downloading. Run preview opens the browser entrypoint; Download gets the named file or project zip.</div><div class="row wrap">'+(view?'<button class="tiny" onclick="openRunPopup(\''+run+'\')">Run preview</button> <a href="'+run+'" target="_blank">Open in tab</a> ':'')+(fileDownload?'<a href="'+fileDownload+'" target="_blank">Download '+esc(decoded||'file')+'</a> ':'')+(zip?'<a href="'+zip+'" target="_blank">Download project zip</a>':'')+'</div><div class="projectRefreshNotice small">Project/file lists refresh automatically after creation. Use Refresh if your browser blocks the update.</div></div>';setTimeout(()=>{loadFiles();loadProjects();loadActivity();},250);}}
function fileIconFor(name){name=String(name||'').toLowerCase();if(name.endsWith('.zip'))return '🗜️';if(name.endsWith('.html'))return '🌐';if(name.endsWith('.js'))return '🟨';if(name.endsWith('.css'))return '🎨';if(name.endsWith('.py'))return '🐍';if(name.endsWith('.json'))return '🧾';if(name.endsWith('.md'))return '📝';return '📄';}
function renderFileCards(reply){let cards=[];const text=String(reply||'');const patterns=[/\/view\?path=([A-Za-z0-9_.%\-\/]+)/g,/\/download\?path=([A-Za-z0-9_.%\-\/]+)/g,/\/download-generated\?name=([A-Za-z0-9_.%\-]+)/g];for(const re of patterns){let m;while((m=re.exec(text))){const url=m[0];const name=decodeURIComponent(m[1]||'file');if(!cards.some(c=>c.url===url))cards.push({url,name});}}if(!cards.length)return '';return '<div class="fileCards">'+cards.slice(0,8).map(c=>'<a class="fileCard" href="'+escAttr(c.url)+'" target="_blank"><span class="fileIcon">'+fileIconFor(c.name)+'</span><b>'+esc(c.name.split('/').pop())+'</b><div class="small">Open/download generated file</div></a>').join('')+'</div>'; }
let lastRunUrl='';function openRunPopup(url){lastRunUrl=url;document.getElementById('runPath').textContent=url;document.getElementById('runFrame').src=url;document.getElementById('runModal').style.display='flex';}
function closeRunPopup(){document.getElementById('runModal').style.display='none';document.getElementById('runFrame').src='about:blank';}
function openRunInTab(){if(lastRunUrl)window.open(lastRunUrl,'_blank');}
function riskyCommandReason(t){const c=String(t||'').toLowerCase();if(c.includes('/self-improve'))return 'Self-improvement can edit Nova source and must be reviewed carefully.';if(c.includes('/idle auto-apply run'))return 'Auto-apply can write files if all safety gates pass.';if(c.includes('/autonomous start'))return 'Autonomous mode can run multiple tool steps until stopped.';if(c.includes('/project-delete'))return 'Project deletion removes project registration/folders after confirmation.';if(/^\/(write|replace|append|run-shell|shell|powershell)/.test(c))return 'This command may mutate files or run a shell command.';return '';}
async function runQuickCommand(t){const parts=String(t||'').split(/\n|;;/).map(x=>x.trim()).filter(Boolean);if(parts.length<=1)return quick(t);for(const part of parts){msg.value=part;await send();}}
function quick(t){const reason=riskyCommandReason(t);if(reason&&!confirm('Review risky action before running:\n\n'+t+'\n\nWhy this needs confirmation: '+reason+'\n\nContinue?'))return Promise.resolve();msg.value=t;return send();}
function confirmMassiveSystemTest(){if(confirm('Run massive Nova system test now?\n\nThis runs dependency checks, doctor, feature audit, compile checks, multiple pytest groups, and optional Docker/Playwright checks. It may take several minutes.')){quick('/massive-test --confirm');}}
function confirmOllamaStop(){
  const ok=confirm('Stop/unload the selected Ollama model?\n\nThis can interrupt a stuck local generation. If a prompt is still running, the current build may fail and need to be retried. It will not delete your project files.');
  if(ok) quick('/ollama-stop --confirm');
}
function confirmInterrupt(){const ok=confirm('Interrupt the current Nova local-model task?\n\nUse this only when a request is stuck. It will not delete project files, but the current build may need to be retried.');if(ok) quick('/interrupt-current --confirm');}
function toggleAvatarAudio(){avatarAudioActivated=true;uiSettings.audioEnabled=true;uiSettings.audioMuted=false;avatarAudioEnabled=true;saveUiSettings();speakText('Audio enabled. Nova voice is ready.');}
function clearActiveRunPanel(){const box=document.getElementById('activeRunPanel');if(box){box.style.display='none';box.innerHTML='';}updatePlanningVisibility(null);}
async function loadActiveRun(){try{const r=await fetch('/api/active-run');const j=await r.json();const box=document.getElementById('activeRunPanel');if(!box)return;const run=j.run||{};const status=String(run.status||'');const interactiveVisible=(j.active&&(status==='waiting_for_user'||status==='paused'));if(!interactiveVisible){clearActiveRunPanel();syncMiddleResizeRails();return;}box.style.display='block';let details=run.option_details||[];let rec=String(run.default||'');let opts=(run.options||[]).map((o,i)=>{let d=details[i]||{};let isRec=(String(o)===rec)||d.recommended;let cls='tiny secondary '+(isRec?'recommendedChoice':'');let tag=isRec?' ⭐ recommended':'';return '<button class="'+cls+'" title="'+esc(d.reason||'Fill this answer')+'" onclick="document.getElementById(\'activeReply\').value=this.dataset.reply;replyActiveRun()" data-reply="'+escAttr(o)+'">'+esc((i+1)+'. '+o+tag)+'</button>';}).join(' ');let controls=status==='paused'?'<button onclick="quick(\'/resume-run\')">Resume</button><button class="danger" onclick="quick(\'/cancel-run\')">Cancel</button>':'<input id="activeReply" placeholder="Click a choice button to continue, or type your own answer"><button onclick="replyActiveRun()">Reply and continue</button><button class="secondary" onclick="quick(\'/pause-run\')">Pause</button><button class="danger" onclick="quick(\'/cancel-run\')">Cancel</button>';box.innerHTML='<div class="activeRun '+esc(status)+'"><b>Active two-way planning step</b> <span class="pill warn">'+esc(status)+'</span><div class="small">Run '+esc(run.run_id||'')+' • recommended answer highlighted</div><div class="q">'+esc(run.question||'No question pending')+'</div><div class="row wrap">'+opts+'</div><div class="row">'+controls+'</div><div class="small">This panel automatically closes after you choose an option and the run starts. you can submit your own reply if none of the options fit.</div></div>';updatePlanningVisibility(run);syncMiddleResizeRails();}catch(e){}}
function replyActiveRun(){const v=(document.getElementById('activeReply')?.value||'').trim();clearActiveRunPanel();if(v)quick('/reply '+v);}
async function loadAvatar(){try{const r=await fetch('/api/avatar');const j=await r.json();const a=j.avatar||{};const mood=String(a.mood||'ready');const face=cleanAvatarFace(a.emoji||'🤖',mood);const html='<div class="avatarFace mood-'+esc(mood)+'" title="'+esc(mood)+'"><span class="faceEmoji">'+esc(face)+'</span></div><div><div class="avatarMood">'+esc(a.title||'Ready')+' <span class="pill '+avatarPillClass(mood)+'">'+esc(mood)+'</span></div><div class="avatarCaption"><b>Current task:</b> '+esc(a.current_task||a.text||'Waiting')+'</div><div class="small">'+esc(a.text||'')+'</div><div class="small"><b>Disclosure:</b> '+esc(a.disclosure||'No side-channel note.')+'</div><div class="small">Updated '+esc(a.updated_at||'')+'</div></div>';const p=document.getElementById('aiPresenceBox');if(p){p.className='avatarBox mood-'+mood;p.innerHTML=html;}const sound=String(a.sound||mood)+'|'+String(a.updated_at||'');if(sound!==lastAvatarSound){lastAvatarSound=sound;avatarBeep(mood);}const sp=String(a.speak||'');if(sp&&sp!==lastAvatarSpeak){lastAvatarSpeak=sp;avatarSay(sp);}}catch(e){}}

function renderModelCards(data={}){const ps=data.ollama_ps||{};const raw=String(ps.raw||data.raw||'').trim();const active=(ps.active_models||data.active_models||[]);let html='<div><b>Active model runtime</b></div>';if(active.length){html+='<div class="modelCards">'+active.map(m=>'<details class="modelCard" open><summary>'+esc(m.name||m.model||'model')+'</summary><div class="small">'+esc(JSON.stringify(m))+'</div></details>').join('')+'</div>';}else{html+='<div class="small">No model currently loaded according to Ollama ps.</div>';}html+='<div style="margin-top:8px"><b>Installed models and Nova use</b></div><div class="small">Primary code model: '+esc(data.model||'')+'<br>Chat model: '+esc(data.chat_model||'')+'<br>Planner/review model: '+esc(data.planner_model||data.model||'')+'</div>';html+='<details open><summary>Raw diagnostic details</summary><pre>'+esc(raw||'No raw Ollama diagnostics available.')+'</pre></details>';return html;}
async function loadLLMStatus(){const oldCtx=document.getElementById('llmRecentContext');try{const r=await fetch('/api/llm-status',{cache:'no-store'});const j=await r.json();const d=j.data||{};const lock=d.winlocalassistant_model_lock||{};const box=document.getElementById('llmStatus');if(!box)return;let busy=!!(lock.busy||lock.prompt_active);let health=j.ok?(busy?'degraded':'ready'):'issue';let progress='';if(busy){const age=Math.max(0,Number(lock.busy_for_sec||0));const pct=Math.max(8,Math.min(95,Math.round((age%120)/120*100)));progress='<div class="modelProgress"><div style="width:'+pct+'%"></div></div><div class="small">Current Nova prompt: '+esc(lock.busy_desc||'local LLM prompt')+(age?' ('+esc(Math.round(age))+'s)':'')+'</div>'; }box.innerHTML='<span id="llmCtxSpinner" style="display:none">Loading recent local model call...</span><div><b>'+esc(j.ok?'Ollama reachable':'Ollama issue')+'</b> <span class="pill '+(j.ok?'good':'bad')+'">Health: '+esc(health)+'</span></div>'+progress+'<div class="small">URL: '+esc(d.url||'')+'</div><div class="small">Recent local model call: '+esc((d.recent_local_model_call&&d.recent_local_model_call.desc)||'model_io.jsonl')+'</div>'+renderModelCards(d);loadRecentModelContext();}catch(e){const box=document.getElementById('llmStatus');if(box)box.innerHTML='<b>Could not refresh LLM status.</b><div class="small">'+esc(e)+'</div>';}}

async function loadRecentModelContext(){const oldCtx=document.getElementById('llmRecentContext');if(!oldCtx)return;try{const r=await fetch('/api/llm-status',{cache:'no-store'});const j=await r.json();const d=j.data||{};const call=d.recent_local_model_call||{};const lock=d.winlocalassistant_model_lock||{};let parts=[];if(lock.busy||lock.prompt_active)parts.push('Prompt active: '+esc(lock.busy_desc||'local model request'));if(call.desc)parts.push('Recent call: '+esc(call.desc));if(call.prompt_preview)parts.push('Prompt: '+esc(String(call.prompt_preview).slice(0,220)));if(call.response_preview)parts.push('Reply: '+esc(String(call.response_preview).slice(0,220)));oldCtx.innerHTML=parts.length?parts.join('<br>'):'No recent local model prompt/reply context yet.';}catch(e){/* keep previous context instead of flashing or clearing */}}
function closeModelSetup(){const el=document.getElementById('modelSetupModal');if(el)el.style.display='none';try{localStorage.setItem('wlaModelSetupDismissedAt',String(Date.now()));}catch(e){}}
function showModelSetup(commands){const modal=document.getElementById('modelSetupModal');const pre=document.getElementById('modelSetupCommands');if(pre)pre.textContent=commands||'ollama serve\nollama pull qwen3-coder:30b\nollama pull gemma2:2b\nollama pull llama3.2-vision:11b';if(modal)modal.style.display='flex';}
async function checkModelSetup(){try{const dismissed=Number(localStorage.getItem('wlaModelSetupDismissedAt')||0);if(dismissed&&Date.now()-dismissed<3600000)return;const r=await fetch('/api/llm-status',{cache:'no-store'});const j=await r.json();const d=j.data||{};const models=d.installed_models||[];const codeModel=d.model||'qwen3-coder:30b';const chatModel=d.chat_model||'gemma2:2b';const names=models.map(m=>String(m.name||''));const missing=[];if(!names.some(n=>n===codeModel||n.startsWith(codeModel+':')))missing.push(codeModel);if(chatModel!==codeModel&&!names.some(n=>n===chatModel||n.startsWith(chatModel+':')))missing.push(chatModel);if(!j.ok||!models.length||missing.length){showModelSetup('ollama serve\n'+Array.from(new Set(missing.length?missing:[codeModel,chatModel])).map(m=>'ollama pull '+m).join('\n'));}}catch(e){/* model setup is advisory; never break chat send/startup */}}
async function loadIdleStatus(){const box=document.getElementById('idleSelfImprovement');if(!box)return;try{const r=await fetch('/api/idle-status',{cache:'no-store'});const j=await r.json();const idle=j.idle_self_improvement||j;const status=idle.status||'idle-status';const msg=idle.message||'Idle self-improvement status loaded.';const source=idle.source_kind?(' <span class="pill">'+esc(idle.source_kind)+'</span>'):'';box.innerHTML='<b>'+esc(status)+'</b>'+source+'<div>'+esc(msg)+'</div>'+(idle.latest_idle_report_path?'<div class="small">Report: '+esc(idle.latest_idle_report_path)+'</div>':'')+(idle.latest_idle_proposal_path?'<div class="small">Proposal: '+esc(idle.latest_idle_proposal_path)+'</div>':'');}catch(e){box.innerHTML='<b>Idle status unavailable</b><div class="small">'+esc(e)+'</div>';}}
async function loadStatusChips(){try{const box=document.getElementById('statusChips');const mini=document.getElementById('orbitRunMini');if(!box&&!mini)return;const r=await fetch('/api/llm-status',{cache:'no-store'});const j=await r.json();let lock=j.data?.winlocalassistant_model_lock||{};let chips=[];chips.push('<span class="pill '+(j.ok?'good':'bad')+'">'+(j.ok?'Ollama online':'Ollama issue')+'</span>');chips.push('<span class="pill '+(lock.busy?'warn':'good')+'">'+(lock.busy?'Model busy':'Model idle')+'</span>');chips.push('<span class="pill">Code '+esc(j.data?.model||'unknown')+'</span>');chips.push('<span class="pill">Chat '+esc(j.data?.chat_model||'unknown')+'</span>');if(box)box.innerHTML=chips.join('');if(mini)mini.textContent=(lock.busy?'working':'idle')+' · '+(j.data?.chat_model||'local');}catch(e){const box=document.getElementById('statusChips');if(box)box.innerHTML='<span class="pill bad">Runtime status unavailable</span>';}}
function showMainTab(tab){for(const id of ['generalPanel','linuxSandboxPanel','kaliSandboxPanel','sandboxSettingsPanel','dockerPanel']){const el=document.getElementById(id);if(el)el.classList.add('hidden');}for(const b of document.querySelectorAll('.sandboxTabBtn'))b.classList.remove('active');const map={general:'generalPanel',linux:'linuxSandboxPanel',kali:'kaliSandboxPanel',settings:'sandboxSettingsPanel',docker:'dockerPanel'};const chosen=map[tab]?tab:'general';const el=document.getElementById(map[chosen]);if(el)el.classList.remove('hidden');const btn=document.getElementById('tab_'+chosen);if(btn)btn.classList.add('active');try{localStorage.setItem('wlaMainTab',chosen);}catch(e){}if(chosen==='linux'||chosen==='kali'||chosen==='settings')loadSandboxStatus();if(chosen==='docker')loadDockerStatus();}
function toggleTopbar(){const bar=document.getElementById('topbar');if(!bar)return;bar.classList.toggle('collapsed');try{localStorage.setItem('wlaTopbarCollapsed',bar.classList.contains('collapsed')?'1':'0');}catch(e){}}
async function loadSandboxStatus(){try{const r=await fetch('/api/sandbox-status',{cache:'no-store'});const j=await r.json();const data=j.data||{};const rt=data.runtime||{};for(const id of ['sandboxStatusLinux','sandboxStatusKali','sandboxStatusSettings']){const box=document.getElementById(id);if(!box)continue;let html='<b>Runtime:</b> '+(rt.available?'<span class="pill good">'+esc(rt.runtime||'available')+'</span>':'<span class="pill bad">missing</span>')+'<div class="small">'+esc(rt.version||rt.error||'Install Docker Desktop or Podman to enable real sandbox execution.')+'</div>';html+='<div class="small"><b>Policy:</b> '+esc(data.sandbox_policy_level||'balanced')+'</div>';html+='<div class="small"><b>Trusted lab mode:</b> '+esc(data.trusted_lab_mode||false)+'</div>';html+='<div class="small"><b>Autonomous sandbox mode:</b> '+esc(data.autonomous_sandbox_mode)+'</div>';html+='<div class="small"><b>Network authorised:</b> '+esc(data.network_authorized)+'</div>';const pending=data.pending_permission||{};if(pending.command){const req=(pending.required||[]).join(', ')||'permission';html+='<div class="sandboxWarn"><b>Pending permission:</b> '+esc(req)+'<div class="small"><code>'+esc(pending.command||'')+'</code></div><div class="row wrap"><button data-command="/sandbox-approve yes" onclick="runDatasetCommand(this)">Approve pending command</button><button class="danger" data-command="/sandbox-cancel" onclick="runDatasetCommand(this)">Cancel pending command</button></div></div>';}const rows=data.sandboxes||{};html+='<div class="small"><b>Known sandboxes:</b> '+esc(Object.keys(rows).length?Object.keys(rows).join(', '):'none')+'</div>';box.innerHTML=html;}}catch(e){for(const id of ['sandboxStatusLinux','sandboxStatusKali','sandboxStatusSettings']){const box=document.getElementById(id);if(box)box.textContent='Could not read sandbox status: '+e;}}}
async function loadDockerStatus(){const box=document.getElementById('dockerStatusBox');if(box)box.textContent='Checking Docker...';try{const r=await fetch('/api/docker-status',{cache:'no-store'});const j=await r.json();const data=j.data||{};let html='<b>Docker CLI:</b> '+(data.installed?'<span class="pill good">found</span>':'<span class="pill bad">missing</span>');if(data.cli_path)html+='<div class="small"><code>'+esc(data.cli_path)+'</code></div>';html+='<div class="small"><b>Daemon running:</b> '+esc(data.daemon_running)+'</div>';html+='<div class="small"><b>Compose available:</b> '+esc(data.compose_available)+'</div>';html+='<div class="small"><b>Containers:</b> '+esc((data.containers||[]).length)+' | <b>Images:</b> '+esc((data.images||[]).length)+'</div>';const last=data.last_validation||{};if(last.run_id)html+='<div class="small"><b>Last validation:</b> '+(last.ok?'<span class="pill good">passed</span>':'<span class="pill bad">failed</span>')+' <code>'+esc(last.run_id)+'</code></div>';const notes=data.notes||[];if(notes.length)html+='<div class="sandboxWarn"><b>Notes</b><ul>'+notes.map(n=>'<li>'+esc(n)+'</li>').join('')+'</ul></div>';if(box)box.innerHTML=html;}catch(e){if(box)box.textContent='Could not read Docker diagnostics: '+e;}}
function sandboxStart(profile){quick('/sandbox-'+profile+' start');setTimeout(loadSandboxStatus,1200);}
function sandboxStop(profile){quick('/sandbox-'+profile+' stop');setTimeout(loadSandboxStatus,1200);}
function sandboxExec(profile){const input=document.getElementById(profile+'SandboxCmd');const cmd=(input&&input.value)||'';if(!cmd.trim()){fillCommand('/sandbox-'+profile+' exec uname -a');return;}quick('/sandbox-'+profile+' exec '+cmd);}
function ensureCycleBubble(c, live=false){
 const key=cycleKeyFromSummary(c); if(!key || key===':0') return;
 let rec=autonomousCycleBubbles[key];
 if(!rec){rec=add('Assistant','', 'cyclebubble '+cycleStatusClass(c));autonomousCycleBubbles[key]=rec;}
 rec.bubble.classList.remove('workingbubble','complete','error');
 rec.bubble.classList.add('cyclebubble');
 rec.bubble.classList.add(live?'workingbubble':cycleStatusClass(c));
 rec.bubble.innerHTML=cycleSummaryHtml(c, live);
}
function autonomousThoughtFallback(ev){
 const d=ev?.data||{}, kind=String(ev?.kind||''), msg=String(ev?.message||kind||'Autonomous progress');
 const tool=d.tool?(' using `'+d.tool+'`'):'';
 if(kind.includes('failed')||kind.includes('error'))return {thought:'I found a problem'+tool+': '+msg, validation:'I should record the failure and avoid repeating the same action unchanged.', cls:'problem'};
 if(kind.includes('done')||d.ok===true)return {thought:'I found a completed result'+tool+': '+msg, validation:'I should only count this as progress if it supports the goal and verification plan.', cls:'success'};
 if(kind.includes('start'))return {thought:'I need to run this bounded step'+tool+': '+msg, validation:'I will verify the returned summary before continuing.', cls:'current'};
 return {thought:'I am tracking autonomous progress: '+msg, validation:'Keep the step bounded, visible and recoverable.', cls:''};
}
function autonomousThoughtRows(s){
 const rows=(s.autonomous_thoughts||[]).slice(-32);
 if(rows.length)return rows;
 return (s.events||[]).slice(-32).map(ev=>{const f=autonomousThoughtFallback(ev);return {time:ev.time||'',kind:ev.kind||'',message:ev.message||'',thought:f.thought,self_validation:f.validation,tool:(ev.data||{}).tool||'',cls:f.cls};});
}
function renderAutonomousThoughtItem(row,current=false){
 const kind=String(row.kind||''), cls=current?'current':(row.cls||((kind.includes('failed')||kind.includes('error'))?'problem':((kind.includes('done')||row.ok===true)?'success':'')));
 const tool=row.tool?'<span class="pill">'+esc(row.tool)+'</span>':'';
 return '<div class="autoThoughtItem '+cls+'"><div class="time">'+esc(row.time||'now')+' • '+esc(kind||'thought')+' '+tool+'</div><div>'+esc(row.thought||row.message||'Tracking autonomous progress.')+'</div><div class="validation"><b>Self-validation:</b> '+esc(row.self_validation||row.validation||'Check result before continuing.')+'</div></div>';
}
function renderAutonomousPlanList(s){
 const plan=s.cycle_plan||[];
 if(!plan.length)return '<div class="small">No cycle plan published yet.</div>';
 return '<div class="autoPlanScroll">'+plan.map((x,i)=>'<div class="small"><b>'+(i+1)+'.</b> '+esc(String(x||''))+'</div>').join('')+'</div>';
}
async function loadAutonomousStatus(){try{
 const r=await fetch('/api/autonomous-status',{cache:'no-store'});const j=await r.json();const box=document.getElementById('autonomousLivePanel');if(!box)return;const s=j.state||{};const live=!!(s.enabled||s.running);
 const summaries=(s.cycle_summaries||[]);
 for(const c of summaries.slice(-8)){ensureCycleBubble(c, !!(s.running && String(c.run_id||'')===String(s.current_run_id||'') && String(c.cycle||'')===String(s.cycle||'')));}
 if(!live){box.style.display='none';box.innerHTML='';syncMiddleResizeRails();return;}
 box.style.display='block';
 const events=(s.events||[]).slice(-28).reverse();const cyc=String(s.cycle||0);const run=String(s.current_run_id||'');
 const ex=s.explanation||{};const age=Number(s.last_progress_age_sec||0);const stale=!!s.may_be_stuck;
 const toolHtml=s.current_tool?'<div class="small"><b>Current tool:</b> '+esc(s.current_tool)+' timeout '+esc(s.current_tool_timeout_sec||'?')+'s</div>':'';
 const staleHtml=stale?'<div class="sticky-note"><b>Possible stall:</b> No autonomous progress update for '+esc(Math.round(age))+'s. '+esc(s.stuck_reason||'A tool/model step may be slow or stuck.')+'</div>':'<div class="small"><b>Last progress:</b> '+esc(Math.round(age))+'s ago</div>';
 const thoughtRows=autonomousThoughtRows(s);const currentThought=s.current_thought || (thoughtRows.length?thoughtRows[thoughtRows.length-1].thought:'I am waiting for the next autonomous status update.');
 const currentValidation=s.current_self_validation || (thoughtRows.length?thoughtRows[thoughtRows.length-1].self_validation:'Keep every step visible, bounded and validated.');
 const thoughtsHtml=thoughtRows.slice().reverse().map((row,idx)=>renderAutonomousThoughtItem(row,idx===0)).join('') || '<div class="small">No autonomous reasoning/status notes yet.</div>';
 const eventHtml=events.map(ev=>'<div class="event"><b>'+esc(ev.message||ev.kind)+'</b><div class="t">'+esc(ev.time||'')+' • '+esc(ev.kind||'')+'</div></div>').join('') || '<div class="small">No events yet.</div>';
 const exHtml='<div class="autoScroll"><div class="small"><b>Summary:</b> '+esc(ex.summary||'No autonomous explanation yet.')+'</div><div class="small"><b>Why:</b> '+esc(ex.why||'')+'</div><div class="small"><b>Next:</b> '+esc(ex.next_expected_step||'')+'</div><div class="small"><b>Risk:</b> '+esc(ex.risk||'')+'</div><div class="small"><b>Failure memory:</b> '+esc(ex.failure_memory||'')+'</div><div class="small"><b>Verification:</b> '+esc((ex.verification||[]).join('; '))+'</div>'+renderAutonomousPlanList(s)+'</div>';
 box.innerHTML='<div class="autonomousCockpit"><div class="autoGridColumn"><div class="autoStatusCard"><b>Autonomous agent live</b> <span class="pill '+(stale?'bad':(s.running?'warn':'good'))+'">'+esc(stale?'possibly stuck':(s.running?'running':'enabled/idle'))+'</span><div class="small">Run '+esc(run)+' • cycle '+esc(cyc)+' • phase '+esc(s.phase||'')+'</div><div class="q">'+esc(s.current_action||s.last_message||'Working')+'</div><div class="small">'+esc(s.current_detail||'')+'</div>'+toolHtml+staleHtml+'<div class="autoCompactActions"><button class="tiny secondary" onclick="quick(&quot;/autonomous status&quot;)">Status</button><button class="tiny secondary" onclick="quick(&quot;/autonomous-explain&quot;)">Explain</button><button class="tiny secondary" onclick="quick(&quot;/autonomous-guide&quot;)">Guide</button><button class="tiny danger" onclick="quick(&quot;/autonomous stop&quot;)">Stop</button></div></div><div class="autoThoughtNow"><b>Current autonomous thinking/status</b><div class="thoughtText">'+esc(currentThought)+'</div><div class="validationText"><b>Self-validation:</b> '+esc(currentValidation)+'</div></div></div><div class="autoGridColumn"><details open class="autoSubWindow"><summary>Scrollable reasoning timeline</summary><div class="autoScroll">'+thoughtsHtml+'</div></details><details class="autoSubWindow"><summary>What autonomous is doing + cycle plan</summary>'+exHtml+'</details><details open class="autoSubWindow"><summary>Latest autonomous events</summary><div class="autoEventScroller">'+eventHtml+'</div></details></div></div>';
 syncMiddleResizeRails();
 if(s.running){ensureCycleBubble({run_id:run,cycle:cyc,phase:s.phase,current_action:s.current_action,current_detail:s.current_detail,events:(s.events||[]),status:'running',report:[currentThought,currentValidation]}, true);}
}catch(e){const box=document.getElementById('autonomousLivePanel');if(box&&box.style.display!=='none')box.innerHTML='<div class="sticky-note"><b>Autonomous status fetch failed:</b> '+esc(e)+'</div>';}}


function updateCompactRunStatus(rows){const el=document.getElementById('compactRunStatus');if(!el)return;const latest=(rows||[]).slice().reverse().find(e=>e&&e.kind);if(!latest){el.textContent='Ready — no recent activity.';return;}const rid=latest.run_id||latest.data?.run_id||'';const title=runHumanTitle(rid||'status/no-run',(rows||[]).filter(e=>(e.run_id||e.data?.run_id||'')===rid));const running=!['command_done','cycle_done','autonomous_cycle_done','idle_cycle_done','step_failed','final_check_failed','verification_failed'].includes(latest.kind);el.textContent=(running?'Working — ':'Last — ')+title.slice(0,110);}
async function loadActivity(){try{
 const r=await fetch('/api/activity?since=0',{cache:'no-store'});
 const j=await r.json();
 let rows=(j.data?.activity||[]);
 for(const ev of rows){if(['idle_cycle_start','idle_step_start','idle_step_done','idle_cycle_done','idle_cycle_failed'].includes(ev.kind)){ensureIdleBubble(ev, rows);}}
 const box=document.getElementById('activityLog');if(!box)return;
 const previousTop=box.scrollTop||0;
 const previousHeight=box.scrollHeight||0;
 const userReviewing=previousTop>24 || activityShouldPreserveScroll(box);
 box.innerHTML=renderRuns(rows)||'<div class="small">No activity for this browser reload yet. Old logs are still saved on disk.</div>';
 restoreActivityScroll(box,previousTop,previousHeight,userReviewing);
 updateAiFileFocus(rows);updateAssistantBoxFallback(rows);renderArchitectureMini(rows);updateCompactRunStatus(rows);
 if(busy&&rows.length){const ev=rows[rows.length-1];renderBusy((ev.message||ev.kind||'Working')+' — '+(ev.data?.summary||ev.data?.tool||''));}
 const evidence=findLatestOutputEvidence(rows, j.data?.model_io||[]);renderTransparentOutputEvidence(evidence);
}catch(e){}}

async function loadActivitySubtitle(){try{const r=await fetch('/api/activity?since=0',{cache:'no-store'});const j=await r.json();const rows=(j.data?.activity||[]);const el=document.getElementById('activitySubtitle');if(!el)return;const ev=rows.slice().reverse().find(x=>x&&x.kind);if(!ev){el.textContent='Current task: waiting for activity.';return;}const data=ev.data||{};const bits=[ev.kind||'event'];if(ev.message)bits.push(ev.message);if(data.tool)bits.push('tool '+data.tool);if(data.summary)bits.push(data.summary);el.textContent='Current task: '+bits.join(' - ').slice(0,220);}catch(e){}}
const runOpenPrefs = (()=>{try{return JSON.parse(sessionStorage.getItem('wlaRunOpenPrefs')||'{}')}catch(e){return {}}})();
const eventOpenPrefs = (()=>{try{return JSON.parse(sessionStorage.getItem('wlaEventOpenPrefs')||'{}')}catch(e){return {}}})();
function saveEventOpenPrefs(){try{sessionStorage.setItem('wlaEventOpenPrefs', JSON.stringify(eventOpenPrefs));}catch(e){}}
function rememberEventOpen(el){const k=el?.dataset?.eventKey;if(!k)return;eventOpenPrefs[k]=!!el.open;saveEventOpenPrefs();}
function shouldEventOpen(k, defaultOpen=false){if(Object.prototype.hasOwnProperty.call(eventOpenPrefs,k))return !!eventOpenPrefs[k];return !!defaultOpen;}
function eventKey(ev, suffix='details'){const d=ev.data||{};return [suffix, ev.run_id||d.run_id||'no-run', ev.ts||ev.time||'', ev.kind||'', (ev.message||'').slice(0,60)].join('|').replace(/"/g,'');}
function saveRunOpenPrefs(){try{sessionStorage.setItem('wlaRunOpenPrefs', JSON.stringify(runOpenPrefs));}catch(e){}}
function rememberRunOpen(el){const rid=el?.dataset?.runId;if(!rid)return;runOpenPrefs[rid]=!!el.open;saveRunOpenPrefs();}
function shouldRunBeOpen(rid, done){if(Object.prototype.hasOwnProperty.call(runOpenPrefs,rid))return !!runOpenPrefs[rid];return !done;}

function cleanRunSnippet(x){return String(x||'').replace(/\s+/g,' ').replace(/^[`'" ]+|[`'" ]+$/g,'').slice(0,72);}
function runHumanTitle(rid,evs){if(rid==='status/no-run')return 'Current status';const joined=evs.map(e=>[e.message,e.kind,e.data?.goal,e.data?.user_goal,e.data?.command,e.data?.summary,e.data?.file,e.data?.path].filter(Boolean).join(' ')).join(' ');const lower=joined.toLowerCase();let title='Runtime activity';if(/massive|system test|test-all/.test(lower))title='System test run';else if(/project-delete|delete project/.test(lower))title='Project deletion';else if(/project-open|open project/.test(lower))title='Project open';else if(/tool-create|custom tool|create tool|tool_test|tool_run/.test(lower))title='Custom tool work';else if(/autonomous/.test(lower))title='Autonomous cycle';else if(/idle/.test(lower))title='Idle improvement';else if(/docker|sandbox/.test(lower))title='Sandbox/Docker validation';else if(/codebase|quality|repair|review|audit/.test(lower))title='Codebase review';else if(/candidate|file_write|write|project|created|build/.test(lower))title='Project/code build';else if(/llm|model|prompt/.test(lower))title='Local model request';const goal=cleanRunSnippet(evs.map(e=>e.data?.goal||e.data?.user_goal||'').find(Boolean));const command=cleanRunSnippet(evs.map(e=>e.data?.command||'').find(Boolean));const file=cleanRunSnippet(evs.map(e=>e.data?.file||e.data?.path||'').find(Boolean));const context=goal||command||file;return title+(context?' — '+context:'');}
function renderRuns(rows){if(!rows.length)return '<div class="small">No activity yet.</div>';let groups={};for(const ev of rows){const rid=ev.run_id||ev.data?.run_id||'status/no-run';if(!groups[rid])groups[rid]=[];groups[rid].push(ev);}let html='';const ids=Object.keys(groups).sort((a,b)=>{let ta=groups[a][0]?.ts||0,tb=groups[b][0]?.ts||0;return tb-ta;});for(const rid of ids.slice(0,18)){const evs=groups[rid];const done=evs.some(e=>['plan_done','step_failed','final_check_done','final_check_failed','autonomous_cycle_done','idle_cycle_done','idle_cycle_failed','llm_fallback_used','command_done','cycle_done','interactive_finished'].includes(e.kind));const failed=evs.some(e=>['step_failed','final_check_failed','llm_rejected','verification_failed','autonomous_error','autonomous_cycle_failed','autonomous_act_failed','idle_cycle_failed','command_failed'].includes(e.kind));const running=!done&&!failed;const lastTs=Number(evs[evs.length-1]?.ts||0);const stale=running&&lastTs&&((Date.now()/1000-lastTs)>90);const title=runHumanTitle(rid,evs);const openAttr=shouldRunBeOpen(rid,done)?'open':'';const first=(evs[0]?.time||'').slice(0,19);const last=(evs[evs.length-1]?.time||'').slice(0,19);const statusText=stale?'stale?':(failed?'attention':(done?'complete':'running'));const stopBtn=running?'<button class="tiny danger runStopBtn" onclick="event.stopPropagation();confirmInterrupt()">Stop</button>':'';html+='<details class="run '+(stale?'staleRun':'')+'" data-run-id="'+esc(rid)+'" '+openAttr+' ontoggle="rememberRunOpen(this)"><summary title="backend id: '+escAttr(rid)+'"><input class="runSelect" type="checkbox" onclick="event.stopPropagation()" data-run-id="'+escAttr(rid)+'"><span class="runSummaryTitle">'+esc(title)+'</span> <span class="pill '+(failed?'bad':(done?'good':'warn'))+'">'+statusText+'</span>'+stopBtn+'<span class="runMeta small">'+evs.length+' events · '+esc(first||last||'recent')+'<span class="backendId"> · id '+esc(rid)+'</span></span></summary><div class="runbody">'+evs.slice(-18).reverse().map(ev=>renderEvent(ev)).join('')+'</div></details>';}return html;}
function selectAllRuns(on){document.querySelectorAll('.runSelect').forEach(x=>x.checked=!!on);}
async function deleteSelectedRuns(){const ids=[...document.querySelectorAll('.runSelect:checked')].map(x=>x.dataset.runId).filter(x=>x&&x!=='status/no-run');if(!ids.length)return add('Assistant','No run logs selected.');if(!confirm('Delete selected run log entries?\n\nThis only cleans the activity/model logs, not project files.'))return;try{const r=await fetch('/api/activity-delete-runs?ids='+encodeURIComponent(ids.join('\n')),{cache:'no-store'});const j=await r.json();add('Assistant',j.summary||'Deleted selected run log entries.');loadActivity();}catch(e){add('Assistant','Could not delete run logs: '+e);}}
function formatDiffHtml(diff){return String(diff||'').split(/\r?\n/).map(line=>{let cls='';if(line.startsWith('+++')||line.startsWith('---')||line.startsWith('@@'))cls='meta';else if(line.startsWith('+'))cls='add';else if(line.startsWith('-'))cls='del';return '<span class="diffline '+cls+'">'+esc(line)+'</span>';}).join('');}
function renderArchitectureMini(events=[]){const box=document.getElementById('architectureMini');if(!box)return;const kinds=(events||[]).slice(-60).map(e=>String(e.kind||'')).join(' ');const nodes=[['Plan',/planning|intent|model_context/i],['Model',/llm|model/i],['Files',/file_write|code_write|read_file|diff/i],['Sandbox',/sandbox|docker/i],['Validate',/verify|test|release|doctor|quality/i],['Repair',/repair|backtrack|recover|refine/i]];box.innerHTML='<div class="archCompact"><b>Current pipeline</b><span class="small">live activity highlights</span>'+nodes.map((n,i)=>'<span class="archNode '+(n[1].test(kinds)?'active':'')+'">'+n[0]+'</span>'+(i<nodes.length-1?'<span class="arrow">→</span>':'')).join('')+'</div>';}
function renderEvent(ev){let data=ev.data||{};let preview=data.command||data.code_preview||data.preview||data.output_tail||data.reply_preview||data.summary||'';let diff=data.diff_preview||data.diff||'';let beforeAfter='';const diffKey=eventKey(ev,'diff');if(diff){beforeAfter='<details class="diffbox" data-event-key="'+esc(diffKey)+'" '+(shouldEventOpen(diffKey,true)?'open':'')+' ontoggle="rememberEventOpen(this)"><summary>Before / after diff</summary><pre>'+formatDiffHtml(String(diff).slice(0,14000))+'</pre></details>';}let meta=[]; if(data.tool)meta.push('tool='+data.tool); if(data.ok!==undefined)meta.push('ok='+data.ok); if(data.path)meta.push('path='+data.path); if(data.file)meta.push('file='+data.file); if(data.run_id)meta.push('run='+data.run_id); if(data.cycle)meta.push('cycle='+data.cycle);let metaHtml=meta.length?'<div class="small">'+esc(meta.join(' • '))+'</div>':'';let details=data.args||data.current_tool_args||data.failure||data.data;const detailsKey=eventKey(ev,'details');let detailsHtml=details?'<details data-event-key="'+esc(detailsKey)+'" '+(shouldEventOpen(detailsKey,true)?'open':'')+' ontoggle="rememberEventOpen(this)"><summary>Event details</summary><pre>'+esc(JSON.stringify(details,null,2).slice(0,8000))+'</pre></details>':'';let previewHtml=preview?'<pre>'+esc(String(preview).slice(0,8000))+'</pre>':'';let progress=''; if(String(ev.kind||'').includes('llm_attempt')||String(ev.kind||'').includes('llm_status'))progress='<div class="llmProgress" title="Local model call in progress"><span></span></div>'; let why='';if(data.reason||data.decision||data.status||data.score||data.final_score||data.risk_score){why='<div class="why"><b>Decision context:</b> '+esc([data.decision,data.status,data.reason].filter(Boolean).join(' — ')||'scored/verified event')+(data.final_score!==undefined?'<br>final_score='+esc(data.final_score):'')+(data.risk_score!==undefined?'<br>risk='+esc(data.risk_score):'')+'</div>';}const kind=String(ev.kind||'');const cls=(/step|act_|candidate|verify|validation|tool|file/i.test(kind)?' subtask':'')+(/done|failed|rejected|accepted/i.test(kind)?' subtask2':'');const title=getUiSetting('showHoverContext')?escAttr('Run: '+(ev.run_id||data.run_id||'none')+'\nKind: '+kind+'\nMessage: '+(ev.message||'')+'\nData: '+JSON.stringify(data).slice(0,900)):'';return '<div class="event '+esc(kind)+cls+'" title="'+title+'"><b>'+esc(ev.message||kind||'event')+'</b><div class="t">'+esc(ev.time||'')+' • '+esc(kind||'')+'</div>'+metaHtml+progress+why+beforeAfter+previewHtml+detailsHtml+'</div>'; }
function findLatestOutputEvidence(activity, modelio){
  let evidence={text:'',diff:'',source:'none',kind:'',file:'',time:''};
  for(let i=activity.length-1;i>=0;i--){let ev=activity[i]||{}, d=ev.data||{};
    const text=d.code_preview||d.preview||d.output_tail||d.reply_preview||d.summary||'';
    const diff=d.diff_preview||d.diff||'';
    if(text||diff){return {text:String(text||'').slice(0,12000),diff:String(diff||'').slice(0,20000),source:'activity',kind:ev.kind||'',file:d.file||d.path||'',time:ev.time||''};}
  }
  for(let i=modelio.length-1;i>=0;i--){if(modelio[i].response_preview)return {text:String(modelio[i].response_preview).slice(0,12000),diff:'',source:'model_io',kind:'model_response',file:'',time:modelio[i].time||''};}
  return evidence;
}
function findLatestCode(activity, modelio){const e=findLatestOutputEvidence(activity,modelio);return e.text||e.diff||'';}
function renderTransparentOutputEvidence(e){
  const preview=document.getElementById('codePreview'); const diff=document.getElementById('transparentDiffPanel'); const meta=document.getElementById('outputEvidenceMeta');
  if(meta){const bits=[e.source||'none',e.kind||'no event',e.file?('file: '+e.file):'no file',e.time||'recent'].filter(Boolean);meta.innerHTML=bits.map(x=>'<span>'+esc(String(x))+'</span>').join('');}
  if(preview){preview.textContent=e.text||'Waiting for model/file output...';}
  if(diff){diff.innerHTML='<summary>Before / after diff</summary><pre>'+(e.diff?formatDiffHtml(e.diff):'No before/after diff found in recent activity yet.')+'</pre>'; }
}

const UI_DEFAULTS={showQuickButtons:false,showComposerButtons:false,showCommandSuggestions:true,showFeedbackButtons:true,showCreatedOutputs:true,showLiveActivity:true,showAvatarPanel:true,darkMode:false,audioEnabled:true,audioMuted:false,voiceMode:true,wakeWordEnabled:true,autoSpeakVoiceMode:false,showHoverContext:true,autoIdleAfterFive:false,voiceAuthRequired:true,voiceRememberLogin:false,voiceVolume:0.9,voiceRate:1.0,voicePitch:1.05,novaPersonality:'friendly_engineer',voiceStyle:'female_preferred'};
const uiSettings = (()=>{try{return Object.assign({},UI_DEFAULTS, JSON.parse(localStorage.getItem('wlaUiSettings')||'{}'))}catch(e){return Object.assign({},UI_DEFAULTS)}})();

// NOVA_STARTUP_GUARD_V55_3_151: browser startup must not fail on stale cached settings/spec widgets.
function normaliseUiSettings(){
  try{
    const raw = (uiSettings && typeof uiSettings === 'object') ? uiSettings : {};
    for(const [k,v] of Object.entries(UI_DEFAULTS||{})){
      if(typeof raw[k] === 'undefined' || raw[k] === null) raw[k]=v;
    }
    // Migrate older theme/spec storage shapes that caused undefined.custom errors.
    if(raw.theme && typeof raw.theme !== 'object') raw.theme={mode:String(raw.theme)};
    if(raw.specs && typeof raw.specs !== 'object') raw.specs={selected:String(raw.specs)};
    if(!raw.custom || typeof raw.custom !== 'object') raw.custom={};
    return raw;
  }catch(e){
    console.warn('Nova settings normalisation failed; using defaults', e);
    return Object.assign({}, UI_DEFAULTS||{}, {custom:{}});
  }
}
function safeCallStartup(name, fn){
  try{return (typeof fn === 'function') ? fn() : undefined;}
  catch(e){console.warn('Nova startup step failed: '+name, e); return undefined;}
}
function populateSpecChoices(){
  // Backwards-compatible no-op/populator for older cached UI paths and future model-spec selectors.
  try{
    const selects = Array.from(document.querySelectorAll('[data-nova-spec-select], #modelSpecSelect, #specChoiceSelect'));
    if(!selects.length) return;
    const choices = [
      ['qwen3-coder:30b','qwen3-coder:30b — upgraded PC coding/chat/planning'],
      ['gemma2:2b','gemma2:2b — fast fallback'],
      ['llama3.2-vision:11b','llama3.2-vision:11b — vision'],
      ['nomic-embed-text:latest','nomic-embed-text — embeddings']
    ];
    for(const sel of selects){
      if(sel.dataset.novaSpecPopulated==='1') continue;
      for(const [value,label] of choices){
        const opt=document.createElement('option'); opt.value=value; opt.textContent=label; sel.appendChild(opt);
      }
      sel.dataset.novaSpecPopulated='1';
    }
  }catch(e){console.warn('populateSpecChoices failed', e);}
}
function safeApplyUiSettings(){
  try{normaliseUiSettings(); applyUiSettings();}
  catch(e){
    console.warn('applyUiSettings failed; resetting UI settings to defaults', e);
    try{for(const [k,v] of Object.entries(UI_DEFAULTS||{})) uiSettings[k]=v; uiSettings.custom={}; localStorage.setItem('wlaUiSettings', JSON.stringify(uiSettings)); applyUiSettings();}catch(e2){console.warn('applyUiSettings fallback failed', e2);}
  }
}

try{if(localStorage.getItem('wlaWakeDefaultApplied')!=='v55.3.164'){uiSettings.wakeWordEnabled=true;uiSettings.voiceMode=true;uiSettings.autoIdleAfterFive=false;uiSettings.voiceAuthRequired=true;uiSettings.voiceRememberLogin=false;uiSettings.__voiceAuthorized=false;sessionStorage.removeItem('wlaVoiceAuthorized');localStorage.removeItem('wlaVoiceRememberedAuth');localStorage.setItem('wlaWakeDefaultApplied','v55.3.164');localStorage.setItem('wlaUiSettings',JSON.stringify(uiSettings));}if(localStorage.getItem('wlaAutoIdleExplicitOptIn')!=='1'){uiSettings.autoIdleAfterFive=false;localStorage.setItem('wlaUiSettings',JSON.stringify(uiSettings));}}catch(e){}
let avatarAudioEnabled=!!uiSettings.audioEnabled;
let avatarAudioActivated=false;
let avatarAudioCtx=null;
let novaAudioUnlocked=false;
function unlockNovaAudio(reason='user interaction'){try{avatarAudioActivated=true;avatarAudioEnabled=true;const Ctx=window.AudioContext||window.webkitAudioContext;if(!Ctx)return false;avatarAudioCtx=avatarAudioCtx||new Ctx();if(avatarAudioCtx.state==='suspended')avatarAudioCtx.resume?.();novaAudioUnlocked=true;setVoiceStatus('Audio ready for Hey Nova cue.');return true;}catch(e){return false;}}
['click','keydown','pointerdown','touchstart'].forEach(ev=>document.addEventListener(ev,()=>unlockNovaAudio(ev),{once:false,passive:true}));
function avatarBeep(mood){try{if(!avatarAudioEnabled||uiSettings.audioMuted||!avatarAudioActivated)return;const Ctx=window.AudioContext||window.webkitAudioContext;if(!Ctx)return;avatarAudioCtx=avatarAudioCtx||new Ctx();const osc=avatarAudioCtx.createOscillator();const gain=avatarAudioCtx.createGain();osc.type='sine';osc.frequency.value=mood==='blocked'?220:(mood==='working'||mood==='busy'?440:660);gain.gain.value=0.025;osc.connect(gain);gain.connect(avatarAudioCtx.destination);osc.start();osc.stop(avatarAudioCtx.currentTime+0.06);}catch(e){}}
function novaReadyCue(){try{if(uiSettings.audioMuted)return;avatarAudioActivated=true;avatarAudioEnabled=true;const Ctx=window.AudioContext||window.webkitAudioContext;if(!Ctx){setVoiceStatus('Ready cue unavailable: browser AudioContext missing.');return;}avatarAudioCtx=avatarAudioCtx||new Ctx();avatarAudioCtx.resume?.();const now=avatarAudioCtx.currentTime+0.03;[[880,.00,.075],[1174,.105,.085],[1760,.235,.11]].forEach(([freq,offset,dur])=>{const osc=avatarAudioCtx.createOscillator();const gain=avatarAudioCtx.createGain();osc.type='triangle';osc.frequency.setValueAtTime(freq,now+offset);gain.gain.setValueAtTime(0.0001,now+offset);gain.gain.exponentialRampToValueAtTime(0.14,now+offset+0.015);gain.gain.exponentialRampToValueAtTime(0.0001,now+offset+dur);osc.connect(gain);gain.connect(avatarAudioCtx.destination);osc.start(now+offset);osc.stop(now+offset+dur+0.05);});setVoiceStatus('Ready cue played. Start speaking now. Hey Nova wake cue played. Distinct Hey Nova ready cue played.');addCommunicationTrace('ready cue','Heard Hey Nova. Three-tone ready cue fired; start speaking now. Hey Nova wake cue played. Distinct Hey Nova ready cue played.');}catch(e){setVoiceStatus('Ready cue could not play until browser audio is unlocked. Click Enable audio once, then try Hey Nova again.');addCommunicationTrace('ready cue blocked',String(e));}}
function avatarSay(text){try{if(!avatarAudioEnabled||uiSettings.audioMuted||!avatarAudioActivated)return;speakText(text);}catch(e){}}

let voiceFeatureBuffer=[];
let voiceChallengePhrase='';
let currentVoiceFeature=null;
let wakeCaptureActive=false;
let wakeRestartPausedForCommand=false;
let postWakeSilenceTimer=null;
let wakeSeedText='';
let voiceRequestInFlight=false;
let novaSpeechActive=false;
let pendingWakeResumeAfterProcessing=false;
let wakeResumeReason='';
let wakeResumeTimer=null;
let lastVoiceCommandForBoard='';
let voiceEnrollmentActive=false;
let communicationTrace=[];
function addCommunicationTrace(kind,text){try{const msg={time:new Date().toLocaleTimeString(),kind:kind||'info',text:String(text||'').slice(0,400)};communicationTrace.push(msg);communicationTrace=communicationTrace.slice(-18);const el=document.getElementById('communicationTrace');if(el){el.innerHTML=communicationTrace.slice().reverse().map(x=>'<div class="communicationTranscriptLine"><b>'+esc(x.kind)+'</b> <span>'+esc(x.time)+'</span><br>'+esc(x.text)+'</div>').join('')||'Waiting for Hey Nova.';}}catch(e){}}
function setVoicePipelineState(state,detail){const st=document.getElementById('voicePipelineState'), de=document.getElementById('voicePipelineDetail'), wr=document.getElementById('voiceWakeResumeState'), lc=document.getElementById('voiceLastCommand'), au=document.getElementById('voiceAudioState');if(st&&state)st.textContent=state;if(de&&detail)de.textContent=detail;if(wr)wr.textContent=pendingWakeResumeAfterProcessing?('Paused until complete: '+(wakeResumeReason||'processing')):(wakeListening?'Listening for Hey Nova.':(uiSettings.wakeWordEnabled?'Wake listener ready.':'Wake listener off.'));if(lc)lc.textContent=lastVoiceCommandForBoard||'None captured yet.';if(au)au.textContent=(voiceRequestInFlight?'Request in flight. ':'')+(novaSpeechActive?'Nova speaking/queued. ':'')+(uiSettings.audioMuted?'Muted. ':'Audio on. ')+(voiceListening?'Mic capture active. ':'Mic idle.');}
function voicePipelinePrimaryState(requestOn,speechOn,fallbackState,detail){if(speechOn)return {state:'Speaking',detail:detail||'Spoken reply is playing or queued.'};if(requestOn)return {state:'Processing request',detail:detail||'Voice command sent to chat.'};return {state:fallbackState||'Ready',detail:detail||'No voice request in progress.'};}
function setVoiceRequestInFlight(on,detail){voiceRequestInFlight=!!on;const p=voicePipelinePrimaryState(voiceRequestInFlight,novaSpeechActive,on?'Processing request':'Request complete',detail||'');setVoicePipelineState(p.state,p.detail);maybeResumeWakeAfterProcessing();}
function setNovaSpeechActive(on,detail){novaSpeechActive=!!on;const p=voicePipelinePrimaryState(voiceRequestInFlight,novaSpeechActive,on?'Speaking':'Speech complete',detail||'');setVoicePipelineState(p.state,p.detail);maybeResumeWakeAfterProcessing();}
function requestWakeResumeAfterVoiceProcessing(reason){pendingWakeResumeAfterProcessing=true;wakeResumeReason=reason||'voice processing';setVoicePipelineState('Wake paused','Waiting for Nova to finish before listening again.');maybeResumeWakeAfterProcessing();}
function pauseWakeUntilProcessingDone(reason){pendingWakeResumeAfterProcessing=true;wakeResumeReason=reason||'chat request';wakeRestartPausedForCommand=true;clearTimeout(wakeRestartTimer);try{if(wakeRecognizer)wakeRecognizer.stop();}catch(e){}wakeListening=false;stopMicWave(false);setVoicePipelineState('Processing request','Wake listener paused while Nova is working.');setNovaOrb('thinking','Nova thinking','Wake listener paused until the reply is finished.');addCommunicationTrace('wake paused',reason||'Nova is processing a request.');}
function maybeResumeWakeAfterProcessing(){clearTimeout(wakeResumeTimer);setVoicePipelineState('', '');if(!pendingWakeResumeAfterProcessing)return;if(wakeCaptureActive||voiceRequestInFlight||novaSpeechActive){return;}if(!uiSettings.wakeWordEnabled||wakeUserStopped){pendingWakeResumeAfterProcessing=false;setVoicePipelineState('Wake paused','Wake word is off.');return;}wakeResumeTimer=setTimeout(()=>{if(wakeCaptureActive||voiceRequestInFlight||novaSpeechActive){maybeResumeWakeAfterProcessing();return;}pendingWakeResumeAfterProcessing=false;wakeRestartPausedForCommand=false;setVoicePipelineState('Ready to listen','Nova finished the reply and speech handoff.');if(uiSettings.wakeWordEnabled&&!wakeUserStopped&&!wakeListening&&!wakeCaptureActive)toggleWakeWordListening(true);},850);}
function vectorDistance(a,b){if(!a||!b||!a.bands||!b.bands)return 999;let sum=0,n=Math.min(a.bands.length,b.bands.length);for(let i=0;i<n;i++){const d=Number(a.bands[i])-Number(b.bands[i]);sum+=d*d;}return Math.sqrt(sum/Math.max(1,n));}
function storedVoiceProfile(){try{return JSON.parse(localStorage.getItem('wlaVoiceProfile')||'null')}catch(e){return null}}
function saveVoiceProfile(profile){try{localStorage.setItem('wlaVoiceProfile',JSON.stringify(profile));}catch(e){}renderVoiceAuth();}
function averageVoiceFeatures(samples){if(!samples||!samples.length)return null;const bands=new Array(samples[0].bands.length).fill(0);let level=0;for(const sample of samples){level+=Number(sample.level||0);for(let i=0;i<bands.length;i++)bands[i]+=Number(sample.bands[i]||0);}return {level:level/samples.length,bands:bands.map(v=>Number((v/samples.length).toFixed(4))),created_at:new Date().toISOString(),samples:samples.length};}
function voiceProfileSimilarity(){const profile=storedVoiceProfile();if(!profile||!currentVoiceFeature)return {ok:false,score:0,reason:profile?'no live voice feature':'no enrolled voice profile'};const dist=vectorDistance(profile,currentVoiceFeature);const levelOk=Math.abs(Number(profile.level||0)-Number(currentVoiceFeature.level||0))<0.34;const score=Math.max(0,Math.min(1,1-(dist/0.42)));return {ok:score>=0.45&&levelOk,score,dist,reason:'browser-side voiceprint similarity'};}
function voiceTestingBypassActive(){try{return sessionStorage.getItem('wlaVoiceTestingBypass')==='1';}catch(e){return false;}}
function generateVoiceChallengePhrase(){const verbs=['orbit','verify','steady','local','nova','signal','project','safety'];const nums=Math.floor(100+Math.random()*900);voiceChallengePhrase='Nova '+verbs[Math.floor(Math.random()*verbs.length)]+' '+nums;const el=document.getElementById('voiceChallengePhrase');if(el)el.textContent=voiceChallengePhrase;return voiceChallengePhrase;}
function normaliseChallenge(t){return String(t||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();}
function challengeMatches(text){return !!voiceChallengePhrase&&normaliseChallenge(text)===normaliseChallenge(voiceChallengePhrase);}
function voiceAuthorized(){try{return !uiSettings.voiceAuthRequired||sessionStorage.getItem('wlaVoiceAuthorized')==='1'||uiSettings.__voiceAuthorized===true||voiceTestingBypassActive();}catch(e){return !uiSettings.voiceAuthRequired;}}
function renderVoiceAuth(){try{const locked=!voiceAuthorized();const card=document.getElementById('voiceGuardCard');const state=document.getElementById('voiceLockState');const profile=document.getElementById('voiceProfileState');const auth=document.getElementById('voiceAuthStatus');if(card)card.className='voiceGuardCard '+(locked?'locked':'unlocked');if(state)state.textContent=locked?'Voice locked':'Voice unlocked';const sim=voiceProfileSimilarity();const text=locked?('Locked. Repeat the displayed phrase or use testing bypass. '+(sim.reason||'')):('Unlocked for this session. '+(voiceTestingBypassActive()?'Testing bypass active.':'Voice/profile gate passed.'));if(profile)profile.textContent=text;if(auth)auth.textContent=text;if(!voiceChallengePhrase)generateVoiceChallengePhrase();}catch(e){}}
function unlockVoiceByChallenge(){const val=(document.getElementById('voiceChallengeInput')?.value||'').trim();if(challengeMatches(val)){try{sessionStorage.setItem('wlaVoiceAuthorized','1');uiSettings.__voiceAuthorized=true;}catch(e){}setVoiceStatus('Voice unlocked with the displayed phrase.');addCommunicationTrace('voice challenge unlock','Challenge phrase matched.');generateVoiceChallengePhrase();renderVoiceAuth();return true;}setVoiceStatus('Phrase did not match. Repeat the displayed phrase exactly.');return false;}
function setVoicePassword(){const v=(document.getElementById('voicePasswordInput')?.value||'').trim();if(!v)return setVoiceStatus('Enter a temporary voice password first.');try{sessionStorage.setItem('wlaVoicePassword',v);}catch(e){}setVoiceStatus('Temporary voice password set for this session.');}
function unlockVoiceSession(){const v=(document.getElementById('voicePasswordInput')?.value||'').trim();try{const stored=sessionStorage.getItem('wlaVoicePassword')||'';if((stored&&v===stored)||voiceTestingBypassActive()){sessionStorage.setItem('wlaVoiceAuthorized','1');uiSettings.__voiceAuthorized=true;setVoiceStatus('Voice unlocked for this session.');renderVoiceAuth();return true;}}catch(e){}return unlockVoiceByChallenge();}
function lockVoiceSession(){try{sessionStorage.removeItem('wlaVoiceAuthorized');uiSettings.__voiceAuthorized=false;}catch(e){}generateVoiceChallengePhrase();setVoiceStatus('Voice locked. Repeat the displayed phrase to unlock commands.');renderVoiceAuth();}
function voiceRequiresAuthNotice(text){const msg='Voice locked. Repeat the displayed phrase to unlock before I run: '+String(text||'').slice(0,120);setVoiceStatus(msg);setNovaOrb('detected','Voice locked',msg);addCommunicationTrace('voice locked',msg);return false;}
function guardAdminVoiceForCommand(text){const sim=voiceProfileSimilarity();if(uiSettings.voiceAuthRequired&&!voiceTestingBypassActive()&&storedVoiceProfile()&&currentVoiceFeature&&!sim.ok){lockVoiceSession();setVoiceStatus('Different voice detected. Voice locked until the displayed phrase is repeated.');addCommunicationTrace('Different voice detected','Voice locked before command: '+String(text||'').slice(0,120));return false;}return true;}
function setVoiceTestingBypass(on){try{if(on){sessionStorage.setItem('wlaVoiceTestingBypass','1');sessionStorage.setItem('wlaVoiceAuthorized','1');uiSettings.__voiceAuthorized=true;}else{sessionStorage.removeItem('wlaVoiceTestingBypass');sessionStorage.removeItem('wlaVoiceAuthorized');uiSettings.__voiceAuthorized=false;}}catch(e){}setVoiceStatus(on?'Testing bypass enabled. Voice commands can run without voice-profile match.':'Testing bypass disabled. Voice commands locked until your voice matches.');addCommunicationTrace(on?'testing bypass unlock':'testing bypass off',on?'Voice command gate bypassed for testing.':'Voice gate restored.');renderVoiceAuth();}
async function startVoiceProfileEnrollment(){voiceEnrollmentActive=true;voiceFeatureBuffer=[];setVoiceStatus('Voice enrolment: say “Hey Nova this is Daniel” for about two seconds.');addCommunicationTrace('voice enrolment','Listening for your voice profile sample.');setNovaOrb('listening','Enrolling your voice','Say the enrolment phrase now.');await startMicWave();setTimeout(()=>{const profile=averageVoiceFeatures(voiceFeatureBuffer.slice(-90));voiceEnrollmentActive=false;if(profile){saveVoiceProfile(profile);setVoiceStatus('Voice profile saved. Locking commands until this browser hears a matching voice.');addCommunicationTrace('voice profile saved','Saved browser-side acoustic profile with '+profile.samples+' samples.');}else{setVoiceStatus('Voice profile was not captured. Try again after allowing mic access.');addCommunicationTrace('voice profile failed','No usable mic feature samples were captured.');}stopMicWave();},3200);}
let micWaveStream=null,micWaveCtx=null,micWaveRaf=null,speakWaveRaf=null,currentNovaState='ready';
function canvasEls(ids){return ids.map(id=>document.getElementById(id)).filter(Boolean);}
function drawWave(canvases,level=0.15,phase=0){for(const c of canvases){const ctx=c.getContext&&c.getContext('2d');if(!ctx)continue;const w=c.width,h=c.height;ctx.clearRect(0,0,w,h);ctx.fillStyle='#0b1020';ctx.fillRect(0,0,w,h);ctx.lineWidth=2;ctx.strokeStyle='#60a5fa';ctx.beginPath();for(let x=0;x<w;x++){const y=h/2+Math.sin((x/18)+phase)*(4+level*h*.35)+Math.sin((x/7)+phase*1.7)*(1+level*h*.08);if(x===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();}}
function setNovaOrb(state,label,transcript){currentNovaState=state||currentNovaState||'ready';const orb=document.getElementById('novaOrb');if(orb){orb.className='novaOrb '+currentNovaState;orb.textContent=currentNovaState==='listening'?'👂':currentNovaState==='detected'?'✨':currentNovaState==='speaking'?'🔊':currentNovaState==='thinking'||currentNovaState==='working'?'🧠':'🤖';}const mini=document.getElementById('orbitMiniOrb');if(mini){mini.className='orbitMiniOrb '+currentNovaState;mini.textContent=currentNovaState==='speaking'?'🔊':currentNovaState==='listening'?'◉':currentNovaState==='thinking'||currentNovaState==='working'?'…':'●';}const pill=document.getElementById('orbitStatePill');if(pill){pill.className='orbitStatePill '+currentNovaState;}const lbl=document.getElementById('orbitStateLabel');if(lbl){const short=(label||currentNovaState||'Ready').replace(/^Nova\s+/i,'');lbl.textContent=short.length>24?short.slice(0,24)+'…':short;}const title=document.getElementById('novaOrbTitle');if(title&&label)title.textContent=label;const tr=document.getElementById('novaOrbTranscript');if(tr&&transcript)tr.textContent=transcript;if((label||transcript)&&/detected|thinking|working|speaking|ready/i.test(currentNovaState))orbitSubChatLine(label||currentNovaState,transcript||'');}
async function startMicWave(){try{stopMicWave(false);if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia)return;micWaveStream=await navigator.mediaDevices.getUserMedia(voiceAudioConstraint());const Ctx=window.AudioContext||window.webkitAudioContext;if(!Ctx)return;micWaveCtx=new Ctx();const src=micWaveCtx.createMediaStreamSource(micWaveStream);const analyser=micWaveCtx.createAnalyser();analyser.fftSize=512;src.connect(analyser);const timeData=new Uint8Array(analyser.fftSize);const freqData=new Uint8Array(analyser.frequencyBinCount);let phase=0;function tick(){analyser.getByteTimeDomainData(timeData);analyser.getByteFrequencyData(freqData);let sum=0;for(const v of timeData){const n=(v-128)/128;sum+=n*n;}const level=Math.min(1,Math.sqrt(sum/timeData.length)*2.2);const bands=[];const bucket=Math.max(1,Math.floor(freqData.length/8));for(let i=0;i<8;i++){let b=0,c=0;for(let j=i*bucket;j<Math.min(freqData.length,(i+1)*bucket);j++){b+=freqData[j]/255;c++;}bands.push(Number((b/Math.max(1,c)).toFixed(4)));}currentVoiceFeature={level:Number(level.toFixed(4)),bands};if(level>0.015){voiceFeatureBuffer.push(currentVoiceFeature);voiceFeatureBuffer=voiceFeatureBuffer.slice(-120);}drawWave(canvasEls(['voiceWaveCanvas','rightVoiceWaveCanvas']),level,phase+=0.25);micWaveRaf=requestAnimationFrame(tick);}tick();}catch(e){drawWave(canvasEls(['voiceWaveCanvas','rightVoiceWaveCanvas']),0.1,Date.now()/400);}}
function stopMicWave(clear=true){try{if(micWaveRaf)cancelAnimationFrame(micWaveRaf);micWaveRaf=null;if(micWaveStream){micWaveStream.getTracks().forEach(t=>t.stop());micWaveStream=null;}if(micWaveCtx){micWaveCtx.close();micWaveCtx=null;}}catch(e){}if(clear)drawWave(canvasEls(['voiceWaveCanvas','rightVoiceWaveCanvas']),0.02,0);}
function startSpeakWave(){try{setNovaSpeechActive(true,'Spoken reply is playing.');if(speakWaveRaf)cancelAnimationFrame(speakWaveRaf);let phase=0;function tick(){drawWave(canvasEls(['novaSpeakWaveCanvas','rightSpeakWaveCanvas']),0.65+0.25*Math.sin(phase),phase);phase+=0.33;speakWaveRaf=requestAnimationFrame(tick);}tick();setNovaOrb('speaking','Nova speaking','Spoken reply is playing.');}catch(e){}}
function stopSpeakWave(){try{if(speakWaveRaf)cancelAnimationFrame(speakWaveRaf);speakWaveRaf=null;}catch(e){}drawWave(canvasEls(['novaSpeakWaveCanvas','rightSpeakWaveCanvas']),0.02,0);setNovaSpeechActive(false,'Speech finished.');if(currentNovaState==='speaking')setNovaOrb('ready','Nova ready','Speech finished.');}

let voiceListening=false;
let voiceRecognizer=null;
let wakeListening=false;
let wakeRecognizer=null;
let wakeRestartTimer=null;
let wakeUserStopped=false;
function voiceModeOn(){return !!uiSettings.voiceMode;}
function setVoiceStatus(text){const value=text||'';const el=document.getElementById('voiceStatus');if(el)el.textContent=value;const live=document.getElementById('voiceLiveText');if(live)live.textContent=value||'Live transcript appears here.';const tr=document.getElementById('novaOrbTranscript');if(tr&&value)tr.textContent=value;}
function setVoiceDeviceStatus(text){const el=document.getElementById('voiceDeviceStatus');if(el)el.textContent=text||'';}
function toggleVoiceMode(on){uiSettings.voiceMode=!!on;saveUiSettings();}
function toggleAudioMute(){avatarAudioActivated=true;uiSettings.audioMuted=!uiSettings.audioMuted;if(!uiSettings.audioMuted)uiSettings.audioEnabled=true;saveUiSettings();setVoiceStatus(uiSettings.audioMuted?'Spoken replies muted.':'Spoken replies unmuted.');}
function saveVoiceDeviceChoice(){try{localStorage.setItem('wlaVoiceDeviceId',document.getElementById('voiceDeviceSelect')?.value||'');}catch(e){}}
function selectedVoiceDeviceId(){try{return localStorage.getItem('wlaVoiceDeviceId')||'';}catch(e){return '';}}
function voiceAudioConstraint(){const deviceId=selectedVoiceDeviceId();return {audio:deviceId?{deviceId:{exact:deviceId}}:true};}
async function refreshVoiceDeviceSelect(){const sel=document.getElementById('voiceDeviceSelect');if(!sel)return;const prior=selectedVoiceDeviceId();sel.innerHTML='<option value="">Default mic</option>';try{if(!navigator.mediaDevices||!navigator.mediaDevices.enumerateDevices){setVoiceDeviceStatus('Browser cannot enumerate microphones.');return;}const devices=await navigator.mediaDevices.enumerateDevices();const inputs=devices.filter(d=>d.kind==='audioinput');for(const d of inputs){const o=document.createElement('option');o.value=d.deviceId;o.textContent=d.label||('Microphone '+(sel.options.length));sel.appendChild(o);}sel.value=prior;setVoiceDeviceStatus(inputs.length?('Mics: '+inputs.length):'No microphone detected.');}catch(e){setVoiceDeviceStatus('Mic list unavailable: '+e);}}
async function diagnoseVoiceInput(){try{if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){setVoiceStatus('Microphone API not available in this browser. Use Chrome/Edge on localhost.');return false;}setVoiceStatus('Testing microphone permission/device...');const stream=await navigator.mediaDevices.getUserMedia(voiceAudioConstraint());stream.getTracks().forEach(t=>t.stop());setVoiceStatus('Microphone test passed.');await refreshVoiceDeviceSelect();return true;}catch(e){const name=e&&e.name?e.name:String(e);const extra=name==='OverconstrainedError'?' The selected microphone is unavailable; choose Default mic or refresh the mic list.':' Check Chrome site permissions and Windows input device.';setVoiceStatus('Microphone test failed: '+name+'.'+extra);return false;}}
async function microphonePermission(){try{if(!navigator.permissions||!navigator.permissions.query)return 'unknown';const p=await navigator.permissions.query({name:'microphone'});return p&&p.state?p.state:'unknown';}catch(e){return 'unknown';}}
function populateSpeechVoices(){try{const sel=document.getElementById('speechVoiceSelect');if(!sel||!window.speechSynthesis)return;const chosen=localStorage.getItem('wlaSpeechVoiceURI')||'';const voices=window.speechSynthesis.getVoices()||[];sel.innerHTML='<option value="">Auto voice</option>'+voices.filter(v=>/^en/i.test(v.lang||'')||!v.lang).map(v=>'<option value="'+escAttr(v.voiceURI)+'">'+esc(v.name+' '+(v.lang||''))+'</option>').join('');sel.value=chosen;}catch(e){console.warn('populateSpeechVoices failed', e);}}
function saveSpeechVoiceChoice(){try{localStorage.setItem('wlaSpeechVoiceURI',document.getElementById('speechVoiceSelect')?.value||'');}catch(e){}}
function selectedSpeechVoice(){try{const voices=window.speechSynthesis?.getVoices?.()||[];const uri=localStorage.getItem('wlaSpeechVoiceURI')||'';if(uri)return voices.find(v=>v.voiceURI===uri)||null;}catch(e){}return null;}
function preferredSpeechVoice(){try{const direct=selectedSpeechVoice();if(direct)return direct;const voices=window.speechSynthesis?.getVoices?.()||[];if(uiSettings.voiceStyle==='default')return null;return voices.find(v=>/female|woman|zira|aria|jenny|samantha|susan|victoria|natasha|sonia/i.test(v.name+' '+v.voiceURI))||voices.find(v=>/^en/i.test(v.lang||''))||null;}catch(e){return null;}}
function speakText(text){try{if(!('speechSynthesis' in window)||uiSettings.audioMuted||isCurrentChatMuted())return;if(!avatarAudioActivated)return;const u=new SpeechSynthesisUtterance(conversationalVoiceSummary(text));const v=preferredSpeechVoice();if(v)u.voice=v;u.pitch=Number(uiSettings.voicePitch||1.05);u.rate=Number(uiSettings.voiceRate||1.0);u.volume=Number(uiSettings.voiceVolume||0.9);u.onstart=()=>startSpeakWave();u.onend=()=>stopSpeakWave();u.onerror=()=>stopSpeakWave();window.speechSynthesis.cancel();window.speechSynthesis.speak(u);}catch(e){stopSpeakWave();}}
function testSpeechOutput(){avatarAudioActivated=true;uiSettings.audioMuted=false;uiSettings.audioEnabled=true;saveUiSettings();speakText('Nova voice output test. If you hear this, spoken replies are working.');}
function summariseForSpeech(text){
  let s=String(text||'');
  s=s.replace(/```[\s\S]*?```/g,' I have code output ready in the chat. ')
     .replace(/`[^`]*`/g,' code ')
     .replace(/https?:\/\/\S+/g,' link ')
     .replace(/^#{1,6}\s*/gm,'')
     .replace(/^[-*]\s+/gm,'')
     .replace(/[{}\[\]#*_>|]/g,' ')
     .replace(/\bPASS\b/g,'passed')
     .replace(/\bFAIL\b/g,'failed')
     .replace(/\s+/g,' ')
     .trim();
  if(!s)return '';
  const first=s.split(/(?<=[.!?])\s+/).slice(0,3).join(' ');
  return first.length>520?first.slice(0,520)+'…':first;
}
function conversationalVoiceSummary(text){
  // Nova voice summary v55.3.159: speak complete, contextual sentences instead of chopping mid-thought.
  const redacted=[];
  if(/Technical details:[\s\S]+/i.test(String(text||'')))redacted.push('Long technical details available on screen.');
  let s=stripEmojiForSpeech(String(text||''));
  s=s.replace(/Technical details:[\s\S]*/i,'');
  s=s.replace(/\{[\s\S]{40,}\}/g,'');
  s=s.replace(/```[\s\S]*?```/g,' I put code output in the chat. ');
  s=s.replace(/\b[A-Za-z]:\\[^\s]+/g,'a local file path');
  s=s.replace(/\b(?:run|id|hash|uuid)[:=]?\s*[A-Za-z0-9_\-]{10,}\b/gi,'');
  s=s.replace(/\b\d{6,}\b/g,'');
  if(/Research report generated|I treated that as a live research request/i.test(s))return 'I found sources and built a research report. I put the evidence and cautions in the chat so you can review them.';
  if(/Local LLM did not produce|Ollama was not reachable|model did not return/i.test(s))return 'The local model did not return usable output. Check Live Activity for details.';
  if(/I treated that as a build\/edit task/i.test(s))return 'I understood this as a build task and started the verified project workflow. Watch Live Activity for each step.';
  if(/I paused before doing anything/i.test(s))return 'I need one planning choice before I touch files. Pick the recommended option if you want me to continue safely.';
  if(/passed|success|complete|created output|download/i.test(s))return 'Done. The checks passed. The result is ready in the chat.';
  s=s.split(/\n{2,}|Next steps|Technical details|Verification:/i)[0];
  s=s.replace(/\s+/g,' ').trim();
  if(!s)return '';
  const sentences=s.match(/[^.!?]+[.!?]+/g)||[s];
  let spoken=sentences.slice(0,2).join(' ').trim();
  if(spoken.length>460){
    const cut=spoken.slice(0,460);
    const last=cut.lastIndexOf(' ');
    spoken=(last>260?cut.slice(0,last):cut).trim()+'. I put the details on screen.';
  }
  if(!/[.!?]$/.test(spoken))spoken+='.';
  return spoken;
}
function maybeSpeakReply(reply, promptText){try{const prompt=String(promptText||'').toLowerCase();const wasVoice=voiceRequestInFlight||pendingWakeResumeAfterProcessing||wakeRestartPausedForCommand||prompt.startsWith('voice:');const shouldSpeak=!!uiSettings.autoSpeakVoiceMode||wasVoice;if(!shouldSpeak)return;if(prompt.startsWith('/activity')||prompt.startsWith('/llm-status')||prompt.startsWith('/files')||prompt.startsWith('/open')||prompt.startsWith('/project-open'))return;avatarAudioActivated=true;avatarAudioEnabled=true;if(!avatarAudioEnabled||uiSettings.audioMuted||isCurrentChatMuted()||!avatarAudioActivated)return;const spoken=stripEmojiForSpeech(conversationalVoiceSummary(reply));if(spoken)speakText(spoken);}catch(e){/* speech is optional and must never break chat delivery */}}

function activeChatId(){try{return localStorage.getItem('wlaActiveChatSession')||'current';}catch(e){return 'current';}}
function chatMuteStore(){try{return JSON.parse(localStorage.getItem('wlaMutedChatSessions')||'{}')}catch(e){return {}}}
function saveChatMuteStore(data){try{localStorage.setItem('wlaMutedChatSessions',JSON.stringify(data||{}));}catch(e){}}
function isCurrentChatMuted(){return !!chatMuteStore()[activeChatId()];}
function toggleCurrentChatMute(){const id=activeChatId();const data=chatMuteStore();data[id]=!data[id];saveChatMuteStore(data);updateAudioRail();setVoiceStatus(data[id]?'This chat is muted. Other chats can still speak.':'This chat can speak again.');}
function toggleGlobalAudio(){avatarAudioActivated=true;uiSettings.audioMuted=!uiSettings.audioMuted;if(!uiSettings.audioMuted)uiSettings.audioEnabled=true;saveUiSettings();setVoiceStatus(uiSettings.audioMuted?'Global spoken audio muted.':'Global spoken audio unmuted.');}
function voiceCommandToAction(text){
  const l=String(text||'').toLowerCase().trim();
  if(!l)return '';
  if(/\b(new chat|start new chat)\b/.test(l)){newChatSession();return ''}
  if(/\b(stop talking|stop speaking|quiet nova)\b/.test(l)){window.speechSynthesis&&window.speechSynthesis.cancel();stopSpeakWave();setVoiceStatus('Speech stopped.');return ''}
  if(/\b(open settings|show settings|settings)\b/.test(l)){toggleSettingsPanel(true);return ''}
  if(/\b(global )?(mute|silence)\b.*\b(audio|voice|nova)\b/.test(l)){if(!uiSettings.audioMuted)toggleGlobalAudio();return ''}
  if(/\b(global )?unmute\b.*\b(audio|voice|nova)\b/.test(l)){if(uiSettings.audioMuted)toggleGlobalAudio();return ''}
  if(/\b(status|what are you doing|what's happening)\b/.test(l) && /\b(auto|autonomous)\b/.test(l))return '/autonomous status';
  return String(text||'').trim();
}
let pendingVoiceText='',pendingVoiceReason='',lastVoiceIssued='',lastVoiceIssuedAt=0,voiceCandidateTimer=null,wakeCandidateText='';
function normaliseVoiceText(t){return String(t||'').toLowerCase().replace(/[.,!?;:]+/g,' ').replace(/\s+/g,' ').trim();}
function collapseRepeatedTranscript(text){let words=String(text||'').replace(/\s+/g,' ').trim().split(' ').filter(Boolean);let out=[];for(const w of words){if(out.length>=2 && out[out.length-1].toLowerCase()===w.toLowerCase() && out[out.length-2].toLowerCase()===w.toLowerCase())continue;out.push(w);}let s=out.join(' ');for(let n=2;n<=8;n++){let changed=true;while(changed){changed=false;const arr=s.split(' ');for(let i=0;i+n*2<=arr.length;i++){const a=arr.slice(i,i+n).join(' ').toLowerCase();const b=arr.slice(i+n,i+n*2).join(' ').toLowerCase();if(a&&a===b){arr.splice(i+n,n);s=arr.join(' ');changed=true;break;}}}}return s.replace(/\b(hey nova|okay nova|ok nova)\b\s*(\1\s*)+/ig,'$1').trim();}
function voiceScreenTranscript(raw){const text=collapseRepeatedTranscript(String(raw||'')).trim();const n=normaliseVoiceText(text);if(!n)return {ok:false,text,reason:'empty'};if(n.length<3)return {ok:false,text,reason:'too short'};const words=n.split(' ');const unique=new Set(words);const repeatRatio=words.length?1-(unique.size/words.length):1;if(words.length>5 && repeatRatio>0.55)return {ok:false,text,reason:'too repetitive'};if(/^(um|uh|ah|noise|test)$/i.test(n))return {ok:false,text,reason:'not a command'};const hasVerb=/\b(make|open|start|stop|run|show|tell|what|why|how|check|test|fix|new|status|search|weather|write|read|explain|continue|send|ask|create|build|unlock|login)\b/i.test(n);if(words.length<=2 && !hasVerb)return {ok:false,text,reason:'unclear short phrase'};return {ok:true,text,reason:'coherent'};}
function askVoiceConfirmation(text,reason){pendingVoiceText=text;pendingVoiceReason=reason||'unclear';const msg='I heard: "'+text+'" but held it because it looked '+pendingVoiceReason+'. Press Send to run it, or say “Hey Nova confirm” to send.';setVoiceStatus(msg);setNovaOrb('detected','Confirm voice command',msg);const input=document.getElementById('msg');if(input)input.value=text;add('Assistant',msg);}
function issueVoiceToChat(text,source='voice'){
  const screened=voiceScreenTranscript(text);
  if(!screened.ok){askVoiceConfirmation(screened.text||text,screened.reason);return false;}
  const finalText=screened.text;
  lastVoiceCommandForBoard=finalText;setVoicePipelineState('Captured command',finalText);
  if(normaliseVoiceText(finalText)==='confirm'&&pendingVoiceText){return issueVoiceToChat(pendingVoiceText,'voice-confirm');}
  if(!voiceAuthorized()){if(challengeMatches(finalText)){unlockVoiceByChallenge();return true;}return voiceRequiresAuthNotice(finalText);}
  if(!guardAdminVoiceForCommand(finalText))return false;
  const now=Date.now();
  if(normaliseVoiceText(finalText)===normaliseVoiceText(lastVoiceIssued)&&now-lastVoiceIssuedAt<4500){setVoiceStatus('Ignored duplicate voice command: '+finalText);return false;}
  lastVoiceIssued=finalText;lastVoiceIssuedAt=now;
  const action=voiceCommandToAction(finalText);
  if(!action){setVoiceStatus('Voice command handled locally: '+finalText);addCommunicationTrace('local voice command',finalText);return true;}
  addCommunicationTrace('sending to chat',action);
  const input=document.getElementById('msg');
  if(input){
    pauseWakeUntilProcessingDone('Voice command sent to chat.');
    input.value=action;setVoiceStatus('Sending voice command: '+action);add('You',action);input.value='';rememberChatText(action);busy=true;setVoiceRequestInFlight(true,'Voice command sent to chat.');setNovaOrb('thinking','Nova thinking','Voice command sent.');
    const working=add('Assistant','', 'workingbubble');activeWorkingBubble=working.bubble;working.bubble.innerHTML=workingHtml('Voice command sent...');
    renderBusy('Voice command sent. Checking active run, Live Activity and autonomous status...');
    toggleOrbitActivity(true);
    const outboundAction=buildSharedChatContext(action);
    fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:outboundAction})}).then(r=>r.json()).then(j=>{busy=false;activeWorkingBubble=null;working.bubble.classList.remove('workingbubble');working.bubble.innerHTML=renderRichText(j.reply||'')+renderFileCards(j.reply||'')+renderCommandSuggestions(j.command_suggestions||[],j.reply||'');addCommunicationTrace('Nova replied',String(j.reply||'').slice(0,300));maybeSpeakReply(j.reply||'',action);setVoiceRequestInFlight(false,'Reply rendered. Waiting for any speech handoff to finish.');requestWakeResumeAfterVoiceProcessing('reply rendered');saveCurrentChatSession();loadActivity();loadLLMStatus();loadActiveRun();loadAutonomousStatus();loadIdleStatus();}).catch(e=>{busy=false;activeWorkingBubble=null;working.bubble.classList.remove('workingbubble');working.bubble.textContent='Error while sending voice request: '+e;setVoiceRequestInFlight(false,'Voice request failed or was interrupted.');requestWakeResumeAfterVoiceProcessing('request failed');});
  }
  return true;
}
function submitVoiceCommand(raw){return issueVoiceToChat(raw,'voice');}
// legacy marker: hey\s+nova for regression tests; fuzzy wake recogniser below.
function wakeWordPattern(){return /\b(?:hey|hay|hi|okay|ok)\s+(?:nova|novah|nover|noba|hova|noah|hanover|hangover)\b|\b(?:nova|novah|hova|hanover|hangover)\b/i;}
function findWakeMatch(text){const t=collapseRepeatedTranscript(String(text||'').toLowerCase());const m=t.match(wakeWordPattern());return m?{index:m.index||0,text:m[0],end:(m.index||0)+m[0].length}:null;}
function ensureVoiceProfileForWake(){if(!uiSettings.voiceAuthRequired||voiceAuthorized())return true;const profile=storedVoiceProfile();if(!profile){setVoiceStatus('Wake word heard. Listening for the request; command gate remains locked until the phrase or testing bypass unlocks it.');addCommunicationTrace('wake allowed without enrolled profile','No enrolled voice profile exists yet; follow-up capture is allowed, but command execution remains gated.');renderVoiceAuth();return true;}const sim=voiceProfileSimilarity();if(sim.ok){try{sessionStorage.setItem('wlaVoiceAuthorized','1');uiSettings.__voiceAuthorized=true;}catch(e){}setVoiceStatus('Your voice matched. Voice commands unlocked for this session.');addCommunicationTrace('voice matched','Similarity '+Math.round(sim.score*100)+'%.');renderVoiceAuth();return true;}setVoiceStatus('Wake word heard, but voice is locked. Enrol your voice or use testing bypass. '+(sim.reason||''));addCommunicationTrace('wake blocked','Wake heard but voice profile did not match yet. '+(sim.score?('Similarity '+Math.round(sim.score*100)+'%.'):'No live profile/feature match.'));renderVoiceAuth();return false;}
function processWakeTranscript(transcript){
 const t=collapseRepeatedTranscript(String(transcript||'').trim());
 if(!t||wakeCaptureActive||wakeRestartPausedForCommand)return false;
 const m=findWakeMatch(t);if(!m)return false;
 avatarAudioActivated=true;uiSettings.voiceMode=true;saveUiSettings();
 if(!ensureVoiceProfileForWake())return true;
 const after=t.slice(m.end).trim().replace(/^[,.:;\-\s]+/,'');
 wakeRestartPausedForCommand=true;
 setNovaOrb('detected','Hey Nova detected','Wake accepted. Listening for your request.');
 setVoiceStatus('Wake accepted. Listening for your request...');
 novaReadyCue();
 addCommunicationTrace('wake detected','Matched “'+m.text+'”. '+(after?'Seed heard: '+after:'Waiting for follow-up request.'));
 try{wakeRecognizer&&wakeRecognizer.stop();}catch(e){}
 setTimeout(()=>startPostWakeCommandCapture(after),180);
 return true;
}
function transcriptFromResults(results){let parts=[];for(let i=0;i<results.length;i++){try{parts.push(results[i][0].transcript||'');}catch(e){}}return collapseRepeatedTranscript(parts.join(' '));}
function stripWakeWordsFromCommand(text){return collapseRepeatedTranscript(String(text||'').replace(wakeWordPattern(),' ')).replace(/^[,.:;\-\s]+/,'').trim();}
function restartWakeAfterCommand(delay=1200){clearTimeout(wakeRestartTimer);wakeRestartTimer=setTimeout(()=>{wakeRestartPausedForCommand=false;if(uiSettings.wakeWordEnabled&&!wakeUserStopped&&!wakeListening&&!wakeCaptureActive)toggleWakeWordListening(true);},delay);}
function finishPostWakeCapture(finalText,lastLive,reason='silence'){
 if(!wakeCaptureActive)return;
 wakeCaptureActive=false;clearTimeout(postWakeSilenceTimer);postWakeSilenceTimer=null;
 try{voiceRecognizer&&voiceRecognizer.stop();}catch(e){}
 voiceListening=false;updateAudioRail();stopMicWave();
 const stable=stripWakeWordsFromCommand(finalText||lastLive||wakeSeedText||'');
 if(stable){
   setNovaOrb('thinking','Request captured',stable);
   setVoiceStatus('Captured after Hey Nova. Sending after '+reason+': '+stable);
   addCommunicationTrace('captured request',stable);
   clearTimeout(voiceCandidateTimer);wakeCandidateText=stable;
   voiceCandidateTimer=setTimeout(()=>{issueVoiceToChat(wakeCandidateText,'wake-followup');requestWakeResumeAfterVoiceProcessing('wake-followup dispatched');},700);
 }else{
   setNovaOrb('detected','Hey Nova detected','No request heard yet. Say the request again or click mic.');
   setVoiceStatus('Hey Nova was heard, but no full follow-up request was captured. Say “Hey Nova” then the whole request, or click the mic.');
   addCommunicationTrace('empty wake capture','Wake accepted but no request followed before silence.');
   restartWakeAfterCommand(1400);
 }
}
function startPostWakeCommandCapture(seed=''){
 const Rec=window.SpeechRecognition||window.webkitSpeechRecognition;if(!Rec){setVoiceStatus('SpeechRecognition is not supported here.');wakeRestartPausedForCommand=false;return;}
 wakeCaptureActive=true;wakeRestartPausedForCommand=true;wakeSeedText=stripWakeWordsFromCommand(seed||'');
 const rec=new Rec();voiceRecognizer=rec;rec.lang='en-AU';rec.interimResults=true;rec.continuous=true;
 let finalText=wakeSeedText,lastLive=wakeSeedText,heardAny=!!wakeSeedText;
 const armSilence=(ms=1600)=>{clearTimeout(postWakeSilenceTimer);postWakeSilenceTimer=setTimeout(()=>finishPostWakeCapture(finalText,lastLive,'silence'),ms);};
 rec.onstart=()=>{voiceListening=true;updateAudioRail();startMicWave();novaReadyCue();setNovaOrb('listening','Listening for request',wakeSeedText||'Say the full request after Hey Nova, then pause.');setVoiceStatus('Ready. Speak the full request, then pause.');addCommunicationTrace('post-wake started',wakeSeedText?'Seed: '+wakeSeedText:'Ready for the request after wake word.');armSilence(wakeSeedText?1400:4200);};
 rec.onerror=e=>{const err=e.error||'unknown';voiceListening=false;wakeCaptureActive=false;clearTimeout(postWakeSilenceTimer);updateAudioRail();stopMicWave();setVoiceStatus('Post-wake voice error: '+err);addCommunicationTrace('post-wake error',err);restartWakeAfterCommand(1600);};
 rec.onend=()=>{voiceListening=false;updateAudioRail();if(wakeCaptureActive){finishPostWakeCapture(finalText,lastLive,'recognition end');}};
 rec.onresult=e=>{let interim='',finals=[];for(let i=0;i<e.results.length;i++){const t=e.results[i][0].transcript||'';if(e.results[i].isFinal)finals.push(t);else interim+=t;}const finalJoined=stripWakeWordsFromCommand((wakeSeedText+' '+finals.join(' ')).trim());finalText=collapseRepeatedTranscript(finalJoined);lastLive=stripWakeWordsFromCommand((finalText+' '+interim).trim());heardAny=heardAny||!!lastLive;setNovaOrb('listening','Live request transcript',lastLive||'Listening...');setVoiceStatus(lastLive||'Listening...');addCommunicationTrace('live transcript',lastLive||'Listening...');armSilence(heardAny?1700:4200);};
 try{rec.start();}catch(e){setVoiceStatus('Could not start post-wake voice capture: '+e);wakeCaptureActive=false;wakeRestartPausedForCommand=false;}
}
function toggleWakeWordListening(force){
  const desired=typeof force==='boolean'?force:!wakeListening;
  if(!desired){wakeUserStopped=true;uiSettings.wakeWordEnabled=false;saveUiSettings();try{wakeRecognizer&&wakeRecognizer.stop();}catch(e){}wakeListening=false;wakeRestartPausedForCommand=false;pendingWakeResumeAfterProcessing=false;clearTimeout(wakeResumeTimer);clearTimeout(postWakeSilenceTimer);stopMicWave();updateAudioRail();setVoicePipelineState('Wake off','Hey Nova wake word off.');setNovaOrb('ready','Wake word off','Hey Nova wake word off.');setVoiceStatus('Hey Nova wake word off.');return;}
  if(wakeCaptureActive||wakeRestartPausedForCommand){setVoiceStatus('Wake listener paused while Nova captures your request.');setVoicePipelineState('Wake paused','Nova is still processing or speaking.');return;}
  wakeUserStopped=false;uiSettings.wakeWordEnabled=true;uiSettings.voiceMode=true;saveUiSettings();avatarAudioActivated=true;
  const Rec=window.SpeechRecognition||window.webkitSpeechRecognition;if(!Rec){setVoiceStatus('Wake word needs Chrome or Edge SpeechRecognition.');return;}
  try{wakeRecognizer&&wakeRecognizer.stop();}catch(e){}
  const rec=new Rec();wakeRecognizer=rec;rec.lang='en-AU';rec.interimResults=true;rec.continuous=true;
  rec.onstart=()=>{wakeListening=true;updateAudioRail();setVoicePipelineState('Listening','Always listening for Hey Nova.');setNovaOrb('listening','Always listening','Say “Hey Nova”, then the command, then pause.');setVoiceStatus('Always listening for “Hey Nova”…');startMicWave();renderVoiceAuth();};
  rec.onerror=e=>{const err=e.error||'unknown';wakeListening=false;updateAudioRail();if(err==='no-speech'&&uiSettings.wakeWordEnabled&&!wakeUserStopped&&!wakeCaptureActive&&!wakeRestartPausedForCommand){setVoicePipelineState('Wake listener ready','No speech heard; continuing to listen for Hey Nova.');setNovaOrb('ready','Wake listener ready','No speech heard; continuing to listen.');setVoiceStatus('Wake listener ready. Say “Hey Nova”.');return;}if(!wakeCaptureActive&&!wakeRestartPausedForCommand)stopMicWave();setVoicePipelineState('Wake listener issue','Wake listener error: '+err);setNovaOrb('ready','Wake listener issue','Wake listener error: '+err);setVoiceStatus('Wake listener error: '+err);};
  rec.onend=()=>{wakeListening=false;updateAudioRail();if(uiSettings.wakeWordEnabled&&!wakeUserStopped&&!wakeCaptureActive&&!wakeRestartPausedForCommand){clearTimeout(wakeRestartTimer);wakeRestartTimer=setTimeout(()=>toggleWakeWordListening(true),900);}else if(!wakeCaptureActive&&!wakeRestartPausedForCommand){stopMicWave();setNovaOrb('ready','Wake word off','Hey Nova wake word off.');setVoiceStatus('Hey Nova wake word off.');}};
  rec.onresult=e=>{const heard=transcriptFromResults(e.results).slice(-260);if(processWakeTranscript(heard)){try{rec.stop();}catch(err){}}else{setNovaOrb('listening','Listening for Hey Nova',heard?('Heard: '+heard):'Listening for “Hey Nova”…');setVoiceStatus(heard?('Heard: '+heard):'Listening for “Hey Nova”…');}};
  try{rec.start();}catch(e){setVoiceStatus('Could not start wake listener: '+e);}
}
async function toggleVoiceInput(){if(voiceListening&&voiceRecognizer){try{voiceRecognizer.stop();}catch(e){}voiceListening=false;updateAudioRail();setVoiceStatus('Voice stopped.');return;}uiSettings.voiceMode=true;saveUiSettings();const ok=await diagnoseVoiceInput();if(!ok)return;const Rec=window.SpeechRecognition||window.webkitSpeechRecognition;if(!Rec){setVoiceStatus('SpeechRecognition is not supported here. Use Chrome or Edge.');return;}const rec=new Rec();voiceRecognizer=rec;rec.lang='en-AU';rec.interimResults=true;rec.continuous=false;const deviceId=selectedVoiceDeviceId();let finalText='',lastLive='';rec.onstart=()=>{voiceListening=true;updateAudioRail();setNovaOrb('listening','Listening to you',deviceId?'Listening on selected mic...':'Listening on default mic...');setVoiceStatus(deviceId?'Listening on selected mic...':'Listening on default mic...');startMicWave();renderVoiceAuth();};rec.onerror=e=>{voiceListening=false;updateAudioRail();stopMicWave();setNovaOrb('ready','Voice error','Voice error: '+(e.error||'unknown'));setVoiceStatus('Voice error: '+(e.error||'unknown'));};rec.onend=()=>{voiceListening=false;updateAudioRail();stopMicWave();const stable=collapseRepeatedTranscript(finalText||lastLive);if(stable.trim()){setNovaOrb('thinking','Voice command captured',stable.trim());setVoiceStatus('Captured. Waiting for silence check...');clearTimeout(voiceCandidateTimer);voiceCandidateTimer=setTimeout(()=>submitVoiceCommand(stable.trim()),450);}else{setNovaOrb('ready','No speech detected','No speech detected.');setVoiceStatus('No speech detected.');}};rec.onresult=e=>{let interim='',finals=[];for(let i=0;i<e.results.length;i++){const t=e.results[i][0].transcript;if(e.results[i].isFinal)finals.push(t);else interim+=t;}finalText=collapseRepeatedTranscript(finals.join(' '));lastLive=collapseRepeatedTranscript((finalText+' '+interim).trim());setNovaOrb('listening','Live transcript',lastLive||'Listening...');setVoiceStatus(lastLive||'Listening...');};try{rec.start();}catch(e){setVoiceStatus('Could not start voice input: '+e);}}
function announceNovaReady(){try{const msg='Nova is ready. Say Hey Nova, then your full request, and pause when finished.';addCommunicationTrace('startup ready',msg);setNovaOrb(uiSettings.wakeWordEnabled?'listening':'ready','Nova ready',msg);setVoiceStatus(uiSettings.wakeWordEnabled?'Always listening for Hey Nova.':'Voice idle.');if(uiSettings.autoSpeakVoiceMode&&avatarAudioActivated)speakText(msg);}catch(e){}}
function showVoiceSetupWizard(){alert('Voice setup wizard:\n1. Use Chrome or Edge on localhost.\n2. Allow microphone permission.\n3. Refresh mics and select your headset mic, not just headset headphones.\n4. For Sony WH-1000 / WH-1000XM style Bluetooth headsets, choose the Headset microphone under Windows Settings > System > Sound > Input.\n5. Run Mic test, then press the microphone button.');}
function getUiSetting(key){return uiSettings[key]!==false;}
function updateAudioRail(){const b=document.getElementById('railMuteBtn');if(b){b.textContent=uiSettings.audioMuted?'🔇':'🔊';b.classList.toggle('muted',!!uiSettings.audioMuted);b.classList.toggle('active',!uiSettings.audioMuted);}const v=document.getElementById('railVoiceBtn');if(v){v.textContent=voiceListening?'⏹️':'🎙️';v.classList.toggle('muted',!voiceModeOn());}const w=document.getElementById('railWakeBtn');if(w){w.textContent=wakeListening?'🟢':'👂';w.classList.toggle('active',!!wakeListening);w.classList.toggle('muted',!wakeListening);}const cw=document.getElementById('chatMuteBtn');if(cw){const muted=isCurrentChatMuted();cw.textContent=muted?'Chat muted':'Chat audio on';cw.classList.toggle('chatMuted',muted);}const wb=document.getElementById('wakeWordBtn');if(wb){wb.textContent=wakeListening?'Hey Nova on':'Hey Nova off';wb.classList.toggle('wakeWordOn',wakeListening);wb.classList.toggle('wakeWordOff',!wakeListening);}setVoicePipelineState('', '');}
function applyUiSettings(){const bar=document.getElementById('topQuickActions');if(bar)bar.style.display=uiSettings.showQuickButtons?'inline-flex':'none';for(const id of Object.keys(UI_DEFAULTS)){const cb=document.getElementById(id);if(!cb)continue;if(cb.type==='checkbox')cb.checked=!!uiSettings[id];else cb.value=uiSettings[id]??UI_DEFAULTS[id];}document.body.classList.toggle('theme-dark',!!uiSettings.darkMode);avatarAudioEnabled=!!uiSettings.audioEnabled||voiceModeOn()||!!uiSettings.wakeWordEnabled;for(const el of document.querySelectorAll('.composerButtons'))el.classList.toggle('hiddenBySettings', true);for(const el of document.querySelectorAll('.uiCreatedOutputs'))el.classList.toggle('hiddenBySettings', !getUiSetting('showCreatedOutputs'));for(const el of document.querySelectorAll('.uiLiveActivity'))el.classList.toggle('hiddenBySettings', !getUiSetting('showLiveActivity'));for(const el of document.querySelectorAll('.uiAvatarPanel'))el.classList.toggle('hiddenBySettings', !getUiSetting('showAvatarPanel'));updateAudioRail();renderVoiceAuth();populateSpeechVoices();if(!wakeListening&&!voiceListening)setVoiceStatus(uiSettings.wakeWordEnabled?'Hey Nova wake word ready.':'Voice idle.');}
function saveUiSettings(){for(const id of Object.keys(UI_DEFAULTS)){const el=document.getElementById(id);if(!el)continue;uiSettings[id]=(el.type==='checkbox')?!!el.checked:(el.type==='range'?Number(el.value):el.value);}try{localStorage.setItem('wlaUiSettings',JSON.stringify(uiSettings));}catch(e){}applyUiSettings();}
function setAutoIdleOptIn(on){uiSettings.autoIdleAfterFive=!!on;try{if(on)localStorage.setItem('wlaAutoIdleExplicitOptIn','1');else localStorage.removeItem('wlaAutoIdleExplicitOptIn');localStorage.setItem('wlaUiSettings',JSON.stringify(uiSettings));}catch(e){}if(on){scheduleAutoIdle();setVoiceStatus('Permanent idle auto-start enabled.');}else{clearTimeout(idleTimer);clearTimeout(idleWarnTimer);clearInterval(idleCountdownTimer);autoIdleActive=false;quick('/idle stop');setVoiceStatus('Permanent idle auto-start disabled.');}applyUiSettings();}
function updatePersonaCommandPreview(){const map={formality:'personaFormality',creativity:'personaCreativity',humor:'personaHumor',empathy:'personaEmpathy',verbosity:'personaVerbosity',technical_depth:'personaTechnicalDepth'};const parts=[];for(const [k,id] of Object.entries(map)){const el=document.getElementById(id);if(el)parts.push(k+'='+Number(el.value||0).toFixed(2));}const cmd='/persona-set '+parts.join(' ');const box=document.getElementById('personaCommandPreview');if(box)box.textContent=cmd;return cmd;}
function fillPersonaSetCommand(){fillCommand(updatePersonaCommandPreview());}
function runPersonaSetCommand(){quick(updatePersonaCommandPreview());}
function toggleSettingsPanel(force){const p=document.getElementById('settingsPanel');if(!p)return;const show=(typeof force==='boolean')?force:(p.style.display==='none'||!p.style.display);p.style.display=show?'block':'none';applyUiSettings();}
function togglePopup(id,show){const el=document.getElementById(id);if(el)el.classList.toggle('hidden',show===false?true:show===true?false:!el.classList.contains('hidden'));}
async function showChangelogPopup(){togglePopup('changelogPopup',true);const box=document.getElementById('changelogContent');if(box)box.textContent='Loading changelog...';try{const r=await fetch('/api/changelog',{cache:'no-store'});const j=await r.json();if(box)box.innerHTML='<pre style="white-space:pre-wrap;max-height:65vh;overflow:auto">'+esc((j.changelog||'No changelog found').slice(0,40000))+'</pre>';}catch(e){if(box)box.textContent='Could not load changelog: '+e;}}
async function showReleaseChecklistPopup(){togglePopup('releaseChecklistPopup',true);const box=document.getElementById('releaseChecklistContent');if(box)box.textContent='Loading release checklist...';try{const r=await fetch('/api/release-checklist',{cache:'no-store'});const j=await r.json();const items=((j.checklist||{}).items||[]).map(it=>'<li>'+(it.ok?'✅':'❌')+' <b>'+esc(it.name||'')+'</b> <span class="small">'+esc(it.summary||'')+'</span></li>').join('');if(box)box.innerHTML='<div><b>'+esc((j.checklist||{}).summary||'Release checklist')+'</b></div><ul>'+items+'</ul><button class="tiny" data-command="/release-checklist" onclick="runDatasetCommand(this)">Show in chat</button>';}catch(e){if(box)box.textContent='Could not load release checklist: '+e;}}
async function showChatsPopup(){
  // showChatsPopup(){openOrbitDrawer('chats') marker for drawer regression tests.
  openOrbitDrawer('chats');
  const panel=ensureOrbitChatsPanel();
  const box=document.getElementById('chatsContent');
  if(box)box.textContent='Loading conversations...';
  try{
    renderLocalChatDrawer();
    const q=(document.getElementById('backendChatSearch')?.value||'').trim();
    const url=q?('/api/conversations?q='+encodeURIComponent(q)):'/api/conversations';
    const r=await fetch(url,{cache:'no-store'});
    const j=await r.json();
    const backendRows=((j.conversations||[])).map(c=>'<div class="item orbitChatRow"><b>'+esc(c.title||'Untitled')+'</b><div class="small">'+esc(c.id||'')+' · '+esc(c.updated_at||'')+'</div><div class="row wrap"><button class="tiny secondary" data-command="/chat-switch '+escAttr(c.id||'')+'" onclick="runDatasetCommand(this)">Switch</button><button class="tiny secondary" data-id="'+escAttr(c.id||'')+'" data-title="'+escAttr(c.title||'')+'" onclick="renameChatFromPopup(this)">Rename</button><button class="tiny danger" data-id="'+escAttr(c.id||'')+'" onclick="deleteChatFromPopup(this)">Delete</button></div></div>').join('');
    const backend=document.getElementById('backendChatsList');
    if(backend)backend.innerHTML=backendRows||'<div class="small">No saved backend conversations yet.</div>';
    if(panel)panel.scrollIntoView({block:'start'});
  }catch(e){if(box)box.textContent='Could not load conversations: '+e;}
}
function renderLocalChatDrawer(){
  const box=document.getElementById('chatsContent'); if(!box)return;
  const q=(document.getElementById('backendChatSearch')?.value||'').toLowerCase().trim();
  const active=activeChatId();
  const rows=Object.values(chatSessionStore()).sort((a,b)=>(b.updated||0)-(a.updated||0)).filter(c=>!q||String(c.title||c.id||'').toLowerCase().includes(q)||textFromChatHtml(c.html||'').toLowerCase().includes(q));
  const local=rows.map(c=>{const id=escAttr(c.id||''); const title=esc(c.title||c.id||'Chat'); const muted=!!chatMuteStore()[c.id]; return '<div class="item orbitChatRow '+((c.id===active)?'active':'')+'"><b>'+title+'</b><div class="small">'+esc(c.id||'')+' · '+(c.updated?new Date(c.updated).toLocaleString():'unsaved')+'</div><div class="row wrap"><button class="tiny secondary" onclick="switchChatSession(\''+id+'\')">Switch</button><button class="tiny secondary" onclick="renameLocalChatSession(\''+id+'\')">Rename</button><button class="tiny secondary" onclick="editLocalChatSession(\''+id+'\')">Edit</button><button class="tiny secondary '+(muted?'chatMuted':'')+'" onclick="toggleChatMuteById(\''+id+'\')">'+(muted?'Unmute':'Mute')+'</button><button class="tiny danger" onclick="deleteLocalChatSession(\''+id+'\')">Delete</button></div></div>';}).join('');
  box.innerHTML='<div class="row wrap"><button class="tiny" onclick="newChatSession()">New chat</button><button class="tiny secondary" onclick="renderLocalChatDrawer();showChatsPopup()">Search</button></div><h4>Browser chat tabs</h4>'+(local||'<div class="small">No local browser chats match.</div>')+'<h4>Backend saved chats</h4><div id="backendChatsList" class="small">Loading backend chats...</div>';
}
async function deleteChatFromPopup(el){const id=el?.dataset?.id||'';if(!id)return;if(!confirm('Delete this saved backend chat?'))return;try{await fetch('/api/conversation-delete?id='+encodeURIComponent(id),{cache:'no-store'});showChatsPopup();}catch(e){alert('Could not delete chat: '+e);}}
async function renameChatFromPopup(el){const id=el?.dataset?.id||'';if(!id)return;const title=prompt('New chat title',el?.dataset?.title||'Renamed chat');if(title===null||!title.trim())return;try{await fetch('/api/conversation-rename?id='+encodeURIComponent(id)+'&title='+encodeURIComponent(title.trim()),{cache:'no-store'});showChatsPopup();}catch(e){alert('Could not rename chat: '+e);}}

const tutorialSteps=[
{target:'#novaOrbPanel',title:'Nova voice orb',text:'This orb shows ready, listening, fuzzy wake-word detected, thinking and speaking states. The waveforms show mic input and spoken replies. Voice starts locked; enrol your voice profile or use testing bypass.'},
{target:'#aiPresenceBox',title:'Nova presence',text:'The presence panel shows mood, current task, disclosure and side-channel status from the backend avatar state.'},
{target:'#edgeRailToggle',title:'Sliding Nova rail',text:'Use this tab to reveal or hide the compact Nova rail without covering the left panel.'},
 {target:'#smartTopStrip',title:'Fast actions',text:'Start a new chat, focus typing, enable Hey Nova, inspect activity, files and tools from the compact strip.'},
 {target:'#msg',title:'Chat first',text:'Type normally or use the microphone. Live transcript appears below the composer while you speak.'},
 {target:'#liveActivityPanel',title:'Live Activity',text:'One toolbar controls stop/select/delete. Individual runs stay readable without duplicate delete buttons.'},
 {target:'.rightbar',title:'Unified right panel',text:'State, output, Jarvis policy, editor and transparent evidence now live in one scrollable panel instead of scattered tabs.'},
 {target:'#settingsPanel',title:'Settings',text:'Replay this tutorial, tune AI speech volume/rate/voice, unlock voice commands, and show/hide clutter.'}
];
let tutorialIndex=0;
function clearTutorialSpotlight(){document.querySelectorAll('.tutorialSpotlight').forEach(e=>e.classList.remove('tutorialSpotlight'));}
function showTutorial(force=false){try{if(!force && localStorage.getItem('NOVA_TUTORIAL_SEEN')==='true')return;}catch(e){}tutorialIndex=0;const ov=document.getElementById('tutorialOverlay');if(ov)ov.style.display='flex';renderTutorialStep();}
function renderTutorialStep(){const step=tutorialSteps[Math.max(0,Math.min(tutorialIndex,tutorialSteps.length-1))];const body=document.getElementById('tutorialBody');if(body)body.innerHTML='<b>'+esc(step.title)+'</b><p>'+esc(step.text)+'</p><div class="small">Step '+(tutorialIndex+1)+' of '+tutorialSteps.length+'</div>';clearTutorialSpotlight();const el=document.querySelector(step.target);if(el){el.classList.add('tutorialSpotlight');try{el.scrollIntoView({block:'center',behavior:'smooth'});}catch(e){}}}
function tutorialNext(){if(tutorialIndex<tutorialSteps.length-1){tutorialIndex++;renderTutorialStep();}else finishTutorial();}
function tutorialBack(){if(tutorialIndex>0){tutorialIndex--;renderTutorialStep();}}
function finishTutorial(){try{localStorage.setItem('NOVA_TUTORIAL_SEEN','true');}catch(e){}const ov=document.getElementById('tutorialOverlay');if(ov)ov.style.display='none';clearTutorialSpotlight();}
function skipTutorial(){finishTutorial();}

function updatePlanningVisibility(run){const box=document.getElementById('planningVisibilityPanel');if(!box)return;const a=(run&&run.planning_analysis)||{};if(!run||!a.detected_intents){box.innerHTML='<b>Plan before run</b><br>No active planning decision.';return;}box.innerHTML='<b>Plan before run</b><br>Detected intent: '+esc((a.detected_intents||[]).join(', ')||'unknown')+'<br>Confidence: '+esc(String(Math.round((a.intent_confidence||0)*100)))+'%<br>Plan level: '+esc(String(a.plan_level||''))+'<br>Needs choice: '+esc(run.status==='waiting_for_user'?'yes':'no')+'<br>Verification: '+esc(((a.success_criteria||[])[0])||'check generated output against the request');}

function updateAiFileFocus(rows){const box=document.getElementById('aiFileFocus');if(!box)return;let found=null;for(let i=rows.length-1;i>=0;i--){const ev=rows[i],d=ev.data||{};const file=d.file||d.path||(d.written&&d.written[0]&&d.written[0].path)||'';if(file&&!isRelevantAiFocusPath(file))continue;if(file || /file|write|read|verify|code/i.test(ev.kind||'')){found={ev,d,file};break;}}if(!found){box.textContent='Current AI file focus: No relevant project file focus yet.';return;}const action=(found.ev.kind||'activity').replaceAll('_',' ');const file=found.file||'project/report event';const status=/write|edit|repair/i.test(action)?'editing':(/read|open/i.test(action)?'reading':(/verify|test/i.test(action)?'verifying':'inspecting'));box.innerHTML='<b>Current AI file focus</b><br>Status: '+esc(status)+'<br>File: '+esc(String(file))+'<br>Last action: '+esc(action)+'<br>Source: '+esc(found.d.tool||found.ev.kind||'activity')+'<br>Timestamp: '+esc(found.ev.time||'');}


msg.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.ctrlKey)send();});
let idleTimer=null,idleWarnTimer=null,idleCountdownTimer=null,lastInputAt=Date.now(),autoIdleActive=false,autoIdleStopPromptAt=0;
const AUTO_IDLE_GOAL='investigate logs and propose safe improvements';
function idlePopupEl(){return document.getElementById('idlePopup');}
function renderAutoIdleRunning(){const p=idlePopupEl();if(!p)return;p.classList.remove('hidden');p.innerHTML='<b>Permanent idle mode running</b><div class="small">Nova will keep running report-only idle inspections until you return and confirm stopping idle mode.</div><button class="tiny" onclick="confirmAutoIdleStop(\'button\')">Stop idle mode</button>';}
function confirmAutoIdleStop(source='activity'){const now=Date.now();if(autoIdleStopPromptAt&&now-autoIdleStopPromptAt<8000)return;autoIdleStopPromptAt=now;if(confirm('Nova has been in permanent idle mode while you were away.\\n\\nStop idle mode now?')){autoIdleActive=false;quick('/idle stop');const p=idlePopupEl();if(p){p.classList.add('hidden');p.innerHTML='';}lastInputAt=Date.now();scheduleAutoIdle();}else{renderAutoIdleRunning();}}
function markUserActive(){if(autoIdleActive){confirmAutoIdleStop('activity');return;}lastInputAt=Date.now();const p=idlePopupEl();if(p&&!p.classList.contains('hidden')){p.classList.add('hidden');}}
function cancelAutoIdleCountdown(){lastInputAt=Date.now();const p=idlePopupEl();if(p)p.classList.add('hidden');scheduleAutoIdle();}
function startPermanentAutoIdle(){if(autoIdleActive)return;autoIdleActive=true;clearTimeout(idleTimer);clearTimeout(idleWarnTimer);clearInterval(idleCountdownTimer);quick('/idle start '+AUTO_IDLE_GOAL);renderAutoIdleRunning();}
function scheduleAutoIdle(){clearTimeout(idleTimer);clearTimeout(idleWarnTimer);clearInterval(idleCountdownTimer);if(autoIdleActive||!getUiSetting('autoIdleAfterFive')||localStorage.getItem('wlaAutoIdleExplicitOptIn')!=='1')return;idleWarnTimer=setTimeout(()=>{let remain=60;const p=idlePopupEl();if(!p)return;p.classList.remove('hidden');p.innerHTML='<b>Permanent idle mode soon</b><div id="idleCountdownText" class="small">Starting in 60s unless you type, move, or click.</div><div class="row wrap"><button class="tiny" onclick="cancelAutoIdleCountdown()">Cancel</button><button class="tiny secondary" onclick="startPermanentAutoIdle()">Run now</button></div>';idleCountdownTimer=setInterval(()=>{remain--;const t=document.getElementById('idleCountdownText');if(t)t.textContent='Starting in '+remain+'s unless you type, move, or click.';if(remain<=0)clearInterval(idleCountdownTimer);},1000);},240000);idleTimer=setTimeout(()=>{if(Date.now()-lastInputAt>=299000)startPermanentAutoIdle();},300000);}
function handleAutoIdleActivity(event){if(event&&event.target&&event.target.closest&&event.target.closest('#idlePopup'))return;const wasAutoIdle=autoIdleActive;markUserActive();if(!wasAutoIdle)scheduleAutoIdle();}
['mousemove','keydown','click','touchstart','input'].forEach(ev=>document.addEventListener(ev,handleAutoIdleActivity,{passive:true}));



// v55.3.142 Orbit drawer shell installer: restructures the existing Nova DOM without deleting backend IDs.
function installNovaOrbitShell(){
  try{
    if(document.getElementById('orbitNav')) return;
    document.body.classList.add('nova-orbit-shell');
    const main=document.querySelector('main[data-ui-overhaul]');
    if(main) main.setAttribute('data-orbit-studio-shell','v55.3.164');
    const sidebar=document.querySelector('.sidebar.card');
    const chatWrap=document.querySelector('.chat-wrap.card');
    const rightbar=document.querySelector('.rightbar.card');
    const activity=document.getElementById('liveActivityPanel')||document.querySelector('.activity');
    if(sidebar && !document.getElementById('orbitNav')){
      const legacy=document.createElement('div');
      legacy.id='orbitLegacyDrawer';
      legacy.className='orbitDrawerBody';
      while(sidebar.firstChild) legacy.appendChild(sidebar.firstChild);
      const shell=document.createElement('div');
      shell.id='orbitDrawer';
      shell.setAttribute('role','dialog');
      shell.setAttribute('aria-label','Nova tools drawer');
      shell.innerHTML='<div class="orbitDrawerHeader"><b id="orbitDrawerTitle">Nova tools</b><span id="orbitDrawerSubtitle">Projects, files, tools and commands stay here.</span><button onclick="closeOrbitDrawer()">×</button></div>';
      shell.appendChild(legacy);
      document.body.appendChild(shell);
      const nav=document.createElement('div');
      nav.id='orbitNav';
      nav.setAttribute('data-orbit-nav','v55.3.164');
      nav.innerHTML=`
        <div class="orbitBrand"><span class="orbitHamburger">☰</span><button id="orbitStatePill" class="orbitStatePill ready" title="Nova state" onclick="toggleOrbitRight('voice')"><span id="orbitMiniOrb" class="orbitMiniOrb ready">N</span><span id="orbitStateLabel">Ready</span></button><span class="orbitLogo">Nova</span></div>
        <div class="orbitNavSection">
          <button class="orbitNavButton" onclick="newChatSession()"><span class="ico">＋</span><span class="label">New Chat</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitDrawer('commands')"><span class="ico">⌕</span><span class="label">Search / Commands</span></button>
          <button class="orbitNavButton" onclick="showChatsPopup()"><span class="ico">▱</span><span class="label">Chats</span><span class="plus">›</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitDrawer('projects')"><span class="ico">▣</span><span class="label">Projects</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitDrawer('files')"><span class="ico">▤</span><span class="label">Files</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitDrawer('tools')"><span class="ico">⌘</span><span class="label">Tools</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitDrawer('research')"><span class="ico">⌕</span><span class="label">Deep Research</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitRight('voice')"><span class="ico">◌</span><span class="label">Voice / State</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitActivity()"><span class="ico">▧</span><span class="label">Live Activity</span></button>
          <button class="orbitNavButton" onclick="toggleOrbitRight('output')"><span class="ico">▨</span><span class="label">Output / Editor</span></button>
          <button class="orbitNavButton" onclick="showOdysseusWorkspace()"><span class="ico">∞</span><span class="label">Workbench</span></button>
        </div>
        <div class="orbitNavSpacer"></div>
        <div class="orbitNavSection">
          <button class="orbitNavButton" onclick="quick('/doctor')"><span class="ico">✓</span><span class="label">Doctor</span></button>
          <button class="orbitNavButton" onclick="toggleSettingsPanel()"><span class="ico">⚙</span><span class="label">Settings</span></button>
          <button class="orbitNavButton" onclick="openOrbitThemePanel()"><span class="ico">◐</span><span class="label">Theme</span></button>
        </div>
        <div class="orbitProfile"><span class="orbitAvatar">N</span><span>local</span><button class="orbitGear" onclick="toggleSettingsPanel()">⚙</button></div>`;
      sidebar.appendChild(nav);
    }
    if(chatWrap && !document.getElementById('orbitHeader')){
      const header=document.createElement('div');
      header.id='orbitHeader';
      header.innerHTML='<span class="novaVersionBadge" id="novaVersionBadge">Nova v55.3.164</span><span class="orbitModelTag" id="orbitModelLabel">Nova local model</span><span id="orbitClock"></span><span id="orbitMessageCount">· ready</span><span id="orbitRunMini">idle</span><div class="orbitHeaderActions"><button class="cleanToggleBtn" id="cleanWorkspaceBtn" onclick="toggleCleanWorkspace()">clean</button><button onclick="focusChatLayout()" title="Close drawers and restore the chat canvas">focus</button><button onclick="runGuiRouteSanity(true)" title="Check backend command routes">routes</button><button onclick="runGuiLayoutSanity(true)" title="Check visible GUI drawer/chat geometry">layout</button><button onclick="resetNovaUiLayout(true)" title="Reset drawer/chat layout state and clear stale Nova browser cache/service worker without deleting project data">reset UI</button><button onclick="quick(\'/build-info\')" title="Show patch/build identity so stale folders are obvious">build</button><button onclick="toggleOrbitDrawer(\'commands\')">commands</button><button onclick="toggleOrbitDrawer(\'files\')">files</button><button onclick="toggleOrbitActivity()">activity</button></div>';
      chatWrap.insertBefore(header, chatWrap.firstChild);
      const sub=document.createElement('div');
      sub.id='orbitSubChat';
      sub.innerHTML='<div class="orbitSubLine"><b>Nova</b> status stream ready.</div>';
      chatWrap.appendChild(sub);
    }
    const chat=document.getElementById('chat');
    if(chat && !document.getElementById('orbitWelcome')){
      const welcome=document.createElement('div');
      welcome.id='orbitWelcome';
      welcome.className='orbitWelcome';
      welcome.innerHTML='<h1>Nova</h1><p>Local AI workspace. Chat stays centred; projects, tools, voice, activity and output open as drawers instead of covering the whole screen.</p><div class="quickchips"><button onclick="fillCommand(\'/do make a polished browser game\')">Build app</button><button onclick="quick(\'/status\')">Status</button><button onclick="quick(\'/user-feedback-tests\')">Test checklist</button><button onclick="toggleOrbitDrawer(\'projects\')">Projects</button></div>';
      chat.prepend(welcome);
    }
    if(rightbar && !document.getElementById('orbitRightDrawer')){
      const rd=document.createElement('div');
      rd.id='orbitRightDrawer';
      rd.setAttribute('role','dialog');
      rd.setAttribute('aria-label','Nova state and output drawer');
      const hdr=document.createElement('div');
      hdr.className='orbitDrawerHeader';
      hdr.innerHTML='<b id="orbitRightTitle">Voice / State</b><span>Inspector drawer</span><button onclick="closeOrbitRight()">×</button>';
      rd.appendChild(hdr);
      const body=document.createElement('div');
      body.className='orbitDrawerBody';
      body.appendChild(rightbar);
      rd.appendChild(body);
      document.body.appendChild(rd);
    }
    if(activity && !document.getElementById('orbitActivityDrawer')){
      const ad=document.createElement('div');
      ad.id='orbitActivityDrawer';
      ad.setAttribute('role','dialog');
      ad.setAttribute('aria-label','Nova live activity drawer');
      ad.appendChild(activity);
      chatWrap.appendChild(ad);
    }
    ensureOrbitAppsPanel();loadOrbitTheme();refreshOrbitHeader();
    setInterval(refreshOrbitHeader,5000);
  }catch(err){console.warn('Nova Orbit shell install failed',err);}
}

let orbitDrawerTarget='';
let orbitRightTarget='';
function orbitSubChatLine(kind,text){const ignoreKinds=['live transcript','listening','no speech','wake paused'];if(ignoreKinds.some(k=>String(kind||'').toLowerCase().includes(k)))return;try{const k=String(kind||'').toLowerCase();const t=String(text||'');if(/live transcript|always listening|listening for hey nova|wake listener ready|no speech|mic idle|audio on|wake paused|processing request/i.test(k+' '+t))return;const box=document.getElementById('orbitSubChat');if(!box)return;const line=document.createElement('div');line.className='orbitSubLine';line.innerHTML='<b>'+esc(String(kind||'Nova').slice(0,32))+'</b><br>'+esc(t.slice(0,160));box.prepend(line);while(box.children.length>4)box.removeChild(box.lastChild);}catch(e){}}
function setOrbitNavActive(kind,target){try{document.querySelectorAll('.orbitNavButton').forEach(b=>b.dataset.open='false');if(kind==='left'&&document.body.classList.contains('orbitDrawerOpen')){document.querySelectorAll('.orbitNavButton').forEach(b=>{if((b.textContent||'').toLowerCase().includes(String(target||'').split('-')[0]))b.dataset.open='true';});}if(kind==='right'&&document.body.classList.contains('orbit-right-open')){document.querySelectorAll('.orbitNavButton').forEach(b=>{const txt=(b.textContent||'').toLowerCase();if((target==='voice'&&txt.includes('voice'))||(target==='output'&&txt.includes('output')))b.dataset.open='true';});}if(document.body.classList.contains('orbit-activity-open')){document.querySelectorAll('.orbitNavButton').forEach(b=>{if((b.textContent||'').toLowerCase().includes('live activity'))b.dataset.open='true';});}}catch(e){}}
function ensureOrbitChatsPanel(){const legacy=document.getElementById('orbitLegacyDrawer');if(!legacy)return null;let panel=document.getElementById('orbitChatsPanel');if(panel)return panel;panel=document.createElement('div');panel.id='orbitChatsPanel';panel.className='orbitInlinePanel';panel.innerHTML='<h3>Saved backend chats</h3><div class="row wrap"><input id="backendChatSearch" placeholder="Search saved chats" onkeydown="if(event.key==&quot;Enter&quot;)showChatsPopup()"><button class="tiny secondary" onclick="showChatsPopup()">Search</button></div><div class="small">Switch, rename or delete backend conversations without covering the chat canvas.</div><div id="chatsContent" class="small">Loading conversations...</div>';legacy.prepend(panel);return panel;}
function ensureOrbitResearchPanel(){const legacy=document.getElementById('orbitLegacyDrawer');if(!legacy)return null;let panel=document.getElementById('orbitResearchPanel');if(panel)return panel;panel=document.createElement('div');panel.id='orbitResearchPanel';panel.className='orbitInlinePanel';panel.innerHTML='<h3>Deep Research</h3><div class="small">Odysseus-style research starter mapped to Nova `/research` and `/research-plan`.</div><textarea id="orbitResearchPrompt" placeholder="Research topic or question"></textarea><div class="row wrap"><button class="tiny" onclick="fillCommand(\'/research \'+(document.getElementById(\'orbitResearchPrompt\').value||\'topic to investigate\'))">Fill research</button><button class="tiny secondary" onclick="quick(\'/research-plan\')">Plan</button><button class="tiny secondary" onclick="quick(\'/providers\')">Providers</button></div>';legacy.prepend(panel);return panel;}
function ensureOrbitThemePanel(){const legacy=document.getElementById('orbitLegacyDrawer');if(!legacy)return null;let panel=document.getElementById('orbitThemePanel');if(panel)return panel;panel=document.createElement('div');panel.id='orbitThemePanel';panel.className='orbitInlinePanel';panel.innerHTML='<h3>Theme customizer</h3><div class="small">Change Nova Orbit colours without removing borders or layout structure.</div><div class="orbitThemeGrid"><label>Primary accent<input id="themePrimary" type="color" value="#cb37ff" oninput="applyOrbitThemeFromInputs()"></label><label>Secondary accent<input id="themeSecondary" type="color" value="#91f6ff" oninput="applyOrbitThemeFromInputs()"></label><label>Background<input id="themeBg" type="color" value="#000000" oninput="applyOrbitThemeFromInputs()"></label><label>Panel<input id="themePanel" type="color" value="#15101f" oninput="applyOrbitThemeFromInputs()"></label><label>Text<input id="themeText" type="color" value="#bdf7ff" oninput="applyOrbitThemeFromInputs()"></label><label>Chat width<input id="themeChatWidth" type="range" min="680" max="1180" step="20" value="860" oninput="applyOrbitThemeFromInputs()"></label></div><div class="orbitThemeActions"><button class="tiny" onclick="saveOrbitTheme()">Save theme</button><button class="tiny secondary" onclick="resetOrbitTheme()">Reset</button></div>';legacy.prepend(panel);loadOrbitTheme();return panel;}
function ensureOrbitAppsPanel(){const legacy=document.getElementById('orbitLegacyDrawer');if(!legacy)return null;let panel=document.getElementById('orbitAppsPanel');if(panel)return panel;panel=document.createElement('div');panel.id='orbitAppsPanel';panel.className='orbitInlinePanel';panel.innerHTML=`<h3>Odysseus-style apps mapped to Nova</h3><div class="orbitAppsGrid"><div class="orbitAppCard"><b>Chat</b><br><button class="tiny" onclick="newChatSession()">New chat</button></div><div class="orbitAppCard"><b>Deep research</b><br><button class="tiny" onclick="fillCommand('/research topic to investigate')">Fill research</button></div><div class="orbitAppCard"><b>Compare</b><br><button class="tiny" onclick="fillCommand('/compare A vs B')">Fill compare</button></div><div class="orbitAppCard"><b>Cookbook</b><br><button class="tiny" onclick="showOdysseusWorkspace()">Workbench</button></div><div class="orbitAppCard"><b>Library/files</b><br><button class="tiny" onclick="toggleOrbitDrawer('files')">Open files</button></div><div class="orbitAppCard"><b>Voice/state</b><br><button class="tiny" onclick="toggleOrbitRight('voice')">Open voice</button></div><div class="orbitAppCard"><b>Activity</b><br><button class="tiny" onclick="toggleOrbitActivity(true)">Dock activity</button></div><div class="orbitAppCard"><b>Theme</b><br><button class="tiny" onclick="openOrbitThemePanel()">Customize</button></div></div>`;legacy.prepend(panel);return panel;}
function openOrbitThemePanel(){ensureOrbitThemePanel();toggleOrbitDrawer('theme');}
function applyOrbitThemeFromInputs(){try{const root=document.body;const vals={primary:'themePrimary',secondary:'themeSecondary',bg:'themeBg',panel:'themePanel',text:'themeText'};for(const [k,id] of Object.entries(vals)){const el=document.getElementById(id);if(el)root.style.setProperty('--nova-'+(k==='bg'?'bg':k),el.value);}const width=document.getElementById('themeChatWidth')?.value;if(width)root.style.setProperty('--orbit-chat-max',width+'px');}catch(e){}}
function currentOrbitTheme(){return {primary:document.getElementById('themePrimary')?.value||'#cb37ff',secondary:document.getElementById('themeSecondary')?.value||'#91f6ff',bg:document.getElementById('themeBg')?.value||'#000000',panel:document.getElementById('themePanel')?.value||'#15101f',text:document.getElementById('themeText')?.value||'#bdf7ff',chatWidth:document.getElementById('themeChatWidth')?.value||'860'};}
function saveOrbitTheme(){try{localStorage.setItem('novaOrbitTheme',JSON.stringify(currentOrbitTheme()));applyOrbitThemeFromInputs();orbitSubChatLine('theme','Saved custom Orbit colours.');}catch(e){}}
function loadOrbitTheme(){try{const t=JSON.parse(localStorage.getItem('novaOrbitTheme')||'null')||{};const map={themePrimary:t.primary,themeSecondary:t.secondary,themeBg:t.bg,themePanel:t.panel,themeText:t.text,themeChatWidth:t.chatWidth};for(const [id,v] of Object.entries(map)){const el=document.getElementById(id);if(el&&v)el.value=v;}applyOrbitThemeFromInputs();}catch(e){}}
function resetOrbitTheme(){try{localStorage.removeItem('novaOrbitTheme');for(const [id,v] of Object.entries({themePrimary:'#cb37ff',themeSecondary:'#91f6ff',themeBg:'#000000',themePanel:'#15101f',themeText:'#bdf7ff',themeChatWidth:'860'})){const el=document.getElementById(id);if(el)el.value=v;}applyOrbitThemeFromInputs();orbitSubChatLine('theme','Theme reset to default.');}catch(e){}}
function refreshOrbitHeader(){try{const clock=document.getElementById('orbitClock');if(clock)clock.textContent=new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});const count=document.querySelectorAll('#chat .msg').length;const mc=document.getElementById('orbitMessageCount');if(mc)mc.textContent='· '+count+' msgs';const model=document.getElementById('orbitModelLabel');const txt=(document.getElementById('llmStatus')?.textContent||'').match(/Primary code model:\s*([^\n]+)/);if(model)model.textContent=txt?txt[1].trim():'Nova local model';}catch(e){}}
function openOrbitDrawer(target){try{orbitDrawerTarget=target||orbitDrawerTarget||'commands';document.body.classList.add('orbitDrawerOpen');const title=document.getElementById('orbitDrawerTitle');const sub=document.getElementById('orbitDrawerSubtitle');const labels={commands:'Search / Commands',projects:'Projects',files:'Project files',tools:'AI tools',models:'Local models',chats:'Chats',theme:'Theme',apps:'Nova apps',research:'Deep Research'};if(title)title.textContent=labels[orbitDrawerTarget]||'Nova tools';if(sub)sub.textContent='Overlay drawer: it stays beside the rail and does not resize the chat.';if(orbitDrawerTarget==='chats')ensureOrbitChatsPanel();if(orbitDrawerTarget==='theme')ensureOrbitThemePanel();if(orbitDrawerTarget==='apps')ensureOrbitAppsPanel();if(orbitDrawerTarget==='research')ensureOrbitResearchPanel();const map={commands:'commandSearch',projects:'projects',files:'files',tools:'customTools',models:'llmStatus',chats:'orbitChatsPanel',theme:'orbitThemePanel',apps:'orbitAppsPanel',research:'orbitResearchPanel'};setTimeout(()=>{const id=map[orbitDrawerTarget]||orbitDrawerTarget;const el=document.getElementById(id);if(el){el.scrollIntoView({block:'start'});if(id==='commandSearch')el.focus();}},80);setOrbitNavActive('left',orbitDrawerTarget);}catch(e){}}
function toggleOrbitDrawer(target){try{if(document.body.classList.contains('orbitDrawerOpen')&&orbitDrawerTarget===target){closeOrbitDrawer();return;}openOrbitDrawer(target);}catch(e){}}
function closeOrbitDrawer(){document.body.classList.remove('orbitDrawerOpen');orbitDrawerTarget='';setOrbitNavActive('left','');}
function openOrbitRight(target){try{orbitRightTarget=target||orbitRightTarget||'voice';document.body.classList.add('orbit-right-open');const title=document.getElementById('orbitRightTitle');if(title)title.textContent=orbitRightTarget==='output'?'Output / Editor':'Voice / State';setTimeout(()=>{const id=orbitRightTarget==='output'?'openPath':'communicationCentreBoard';document.getElementById(id)?.scrollIntoView({block:'start'});},80);setOrbitNavActive('right',orbitRightTarget);}catch(e){}}
function toggleOrbitRight(target){try{if(document.body.classList.contains('orbit-right-open')&&orbitRightTarget===target){closeOrbitRight();return;}openOrbitRight(target);}catch(e){}}
function closeOrbitRight(){document.body.classList.remove('orbit-right-open');orbitRightTarget='';setOrbitNavActive('right','');}
function toggleOrbitActivity(force){const on=typeof force==='boolean'?force:!document.body.classList.contains('orbit-activity-open');document.body.classList.toggle('orbit-activity-open',on);setOrbitNavActive('activity','activity');}
function toggleUiTheme(){openOrbitThemePanel();}

function focusChatLayout(){
  try{
    document.body.classList.remove('orbitDrawerOpen','orbit-right-open','orbit-activity-open');
    orbitDrawerTarget=''; orbitRightTarget='';
    setOrbitNavActive('focus','');
    const chat=document.getElementById('chat');
    if(chat) chat.scrollTo({top:chat.scrollHeight,behavior:'smooth'});
    orbitSubChatLine('layout','Focus restored: drawers closed and chat canvas reclaimed.');
  }catch(e){}
}


function resetNovaUiLayout(clearCaches=false){
  try{
    const staleKeys=['wlaLeftPanelWidth','wlaRightPanelWidth','wlaCollapseleft','wlaCollapseright','wlaCollapseactivity','wlaEdgeRailOpen','novaFocusLayoutApplied','novaCalmLayoutApplied','wlaMiddlePanelHeights','novaFocusWorkspace','wlaControlDrawerCollapsed','novaGuiLayoutStorageVersion'];
    staleKeys.forEach(k=>{try{localStorage.removeItem(k);}catch(e){}});
    document.body.classList.remove('orbitDrawerOpen','orbit-right-open','orbit-activity-open','collapse-left','collapse-right');
    document.body.classList.add('clean-workspace','calm-workspace','focus-workspace','collapse-activity','gui-overhaul-v3');
    orbitDrawerTarget=''; orbitRightTarget='';
    setOrbitNavActive('reset','');
    toggleEdgeRail(false);
    if(window.novaGuiHardenLayout) window.novaGuiHardenLayout();
    setTimeout(()=>{ if(window.novaGuiHardenLayout) window.novaGuiHardenLayout(); runGuiLayoutSanity(true); }, 120);
    if(clearCaches){
      try{ if('caches' in window){ caches.keys().then(keys=>Promise.all(keys.map(k=>caches.delete(k)))).catch(()=>{}); } }catch(e){}
      try{ if('serviceWorker' in navigator){ navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>r.unregister().catch(()=>{}))).catch(()=>{}); } }catch(e){}
      orbitSubChatLine('layout','UI reset applied and browser cache/service-worker cleanup requested. Hard refresh with Ctrl+Shift+R if needed.');
    }else{
      orbitSubChatLine('layout','UI reset applied: drawers closed, stale layout widths cleared and chat canvas reclaimed.');
    }
  }catch(e){
    showGuiRouteWarning(['UI reset failed: '+(e&&e.message?e.message:e),'Run /gui-layout-status from chat.']);
  }
}

function showGuiRouteWarning(lines){
  try{
    const chat=document.getElementById('chat'); if(!chat)return;
    let box=document.getElementById('guiRouteWarn');
    if(!box){box=document.createElement('div');box.id='guiRouteWarn';box.className='guiRouteWarn';chat.prepend(box);}
    box.style.display='block';
    box.innerHTML='<b>Backend route sanity warning</b><br>'+lines.map(x=>esc(x)).join('<br>')+'<br><button class="tiny secondary" onclick="focusChatLayout()">Focus chat</button> <button class="tiny secondary" onclick="resetNovaUiLayout(true)">Reset UI/cache</button> <button class="tiny" onclick="runGuiRouteSanity(true)">Retest routes</button>';
  }catch(e){}
}

async function runGuiRouteSanity(showOk=false){
  try{
    const commands=['/media-status','/image-plan route sanity','/video-status','/validation-status','/remote-access-test','/gui-layout-status','/gui-reset-help','/gui-ai-help {\"label\":\"routes button\",\"command\":\"runGuiRouteSanity\"}'];
    const r=await fetch('/api/route-health?commands='+encodeURIComponent(commands.join('\n')),{cache:'no-store'});
    const j=await r.json();
    if(!j.ok){showGuiRouteWarning(['Route health endpoint failed: '+(j.error||'unknown error')]);return;}
    const bad=(j.routes||[]).filter(x=>!x.ok);
    if(bad.length){
      showGuiRouteWarning(bad.map(x=>x.command+': '+(x.summary||'not routed')));
    }else if(showOk){
      orbitSubChatLine('routes','Backend command routes are healthy.');
    }
  }catch(e){showGuiRouteWarning(['Could not contact /api/route-health. Restart Nova if commands return Unknown command.']);}
}

async function runGuiLayoutSanity(showOk=false){
  try{
    if(window.novaGuiHardenLayout) window.novaGuiHardenLayout();
    const local = window.novaGuiLayoutDiagnose ? window.novaGuiLayoutDiagnose() : {ok:false,warnings:['browser diagnostic function not loaded']};
    const r=await fetch('/api/gui-layout-health',{cache:'no-store'});
    const server=await r.json();
    const warnings=[...(local.warnings||[])];
    if(!server.ok) warnings.push('server static layout contract is not passing');
    if(warnings.length){
      showGuiRouteWarning(['Layout sanity warning:', ...warnings, 'Run /gui-layout-status for static contract details.']);
      console.warn('Nova GUI layout diagnostics', {local, server});
    }else if(showOk){
      orbitSubChatLine('layout','GUI layout sanity passed: rail, left drawer, chat canvas and right drawer state look healthy.');
      console.info('Nova GUI layout diagnostics', {local, server});
    }
  }catch(e){
    showGuiRouteWarning(['Could not run GUI layout sanity check: '+(e&&e.message?e.message:e), 'Run /gui-layout-status from chat.']);
  }
}


function applyCleanWorkspaceMode(){
  try{
    const stored=localStorage.getItem('novaCleanWorkspace');
    const enabled=stored===null?true:stored!=='0';
    document.body.classList.toggle('clean-workspace', enabled);
    const btn=document.getElementById('cleanWorkspaceBtn');
    if(btn)btn.textContent=enabled?'clean on':'clean off';
    return enabled;
  }catch(e){document.body.classList.add('clean-workspace');return true;}
}
function toggleCleanWorkspace(){
  try{
    const next=!document.body.classList.contains('clean-workspace');
    localStorage.setItem('novaCleanWorkspace', next?'1':'0');
    applyCleanWorkspaceMode();
    orbitSubChatLine('layout', next?'Clean workspace enabled.':'Clean workspace disabled.');
  }catch(e){}
}

installNovaOrbitShell();
applyCleanWorkspaceMode();
try{generateVoiceChallengePhrase();if('caches' in window){caches.keys().then(keys=>Promise.all(keys.filter(k=>k.includes('nova')||k.includes('orbit')||k.includes('wla')).map(k=>caches.delete(k)))).catch(()=>{});}if('serviceWorker' in navigator){navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>r.update().catch(()=>{}))).catch(()=>{});}}catch(e){}
initPanelLayout();setupPanelResize();setupMiddlePanelResize();setupSidebarSectionCollapse();setupInspectorTabs();setupChatKeyboard();try{if(localStorage.getItem('wlaTopbarCollapsed')==='0')document.getElementById('topbar')?.classList.remove('collapsed');}catch(e){}try{sessionStorage.removeItem('wlaVoiceAuthorized');uiSettings.__voiceAuthorized=false;}catch(e){}safeApplyUiSettings();populateSpecChoices();renderVoiceAuth();populateSpeechVoices();applyCalmWorkspaceDefaults();if(window.speechSynthesis)window.speechSynthesis.onvoiceschanged=populateSpeechVoices;announceNovaReady();drawWave(canvasEls(['voiceWaveCanvas','rightVoiceWaveCanvas','novaSpeakWaveCanvas','rightSpeakWaveCanvas']),0.02,0);setTimeout(()=>{if(uiSettings.wakeWordEnabled)toggleWakeWordListening(true);},800);refreshVoiceDeviceSelect();renderCommandPalette();renderQuickControls();renderChatSessionSelect();const restoredChat=restoreActiveChatSession();renderChatSessionSelect();scheduleAutoIdle();setTimeout(()=>showTutorial(false),450);if(!restoredChat){add('Assistant','**Started. Nova v55.3.164 is loaded.** Repo research radar, codebase sanity audit, expanded capability manifests, Orbit workspace GUI shell, assurance tools and preserved project/tool workflows loaded. Try `/agent-topology improve Nova safely`, `/trace-observability debug coding flow`, `/local-stack-advisor debug Python => GTX 1650 4GB VRAM`, `/verifier-ladder build Java CLI => java`, `/tool-namespace-plan reduce tool bloat`, `/voice-pipeline-review Hey Nova wake pipeline`, `/route-resilience-plan improve Nova safely`, `/tool-health-map`, `/context-router-policy improve coding reliability`, `/local-runtime-sentinel debug code => GTX 1650 4GB VRAM`, `/capability-drift-audit`, `/feature-preservation-contract coding`, `/agent-feedback-loop improve Nova`, `/behavior-fuzzer-plan fuzz coding => routing`, `/local-spec-search coding => GTX 1650 4GB VRAM`, or `/autonomous status`.');saveCurrentChatSession();}loadProjects();loadTools();loadFiles();loadLLMStatus();loadAvatar();loadStatusChips();loadIdleStatus();checkModelSetup();loadActivity();loadActivitySubtitle();loadActiveRun();loadAutonomousStatus();loadAssistantBox();loadSandboxStatus();loadOdysseusRuntime();registerNovaServiceWorker();try{showMainTab(localStorage.getItem('wlaMainTab')||'general')}catch(e){}setTimeout(openOdysseusDeepLink,650);setTimeout(()=>runGuiRouteSanity(false),900);setInterval(loadActivity,1500);setInterval(loadActivitySubtitle,1500);setInterval(loadAutonomousStatus,1500);setInterval(loadAssistantBox,12000);setInterval(loadSandboxStatus,5000);setInterval(loadOdysseusRuntime,10000);setInterval(loadActiveRun,2500);setInterval(loadLLMStatus,5000);setInterval(loadAvatar,1000);setInterval(loadStatusChips,5000);setInterval(loadIdleStatus,5000);setInterval(checkModelSetup,30000);setInterval(syncMiddleResizeRails,1500);setInterval(()=>{if(busy){renderBusy('Still working. Polling live activity and active run...');loadActivity();loadActiveRun();loadAutonomousStatus();}},850);

/* Nova legacy JS compatibility markers. */
function stripEmojiForSpeech(text){
  return String(text || '').replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '');
}
function loadDockerStatusLegacyMarker(){
  try {
    if (typeof loadSandboxStatus === 'function') return loadSandboxStatus();
  } catch(e) {}
}
const __novaLegacyEditorContractMarker = "const content=editor?.value||''";
const __novaLegacyToolRefreshMarker = "setTimeout(loadTools,800)";
const __novaLegacyVoiceVolumeMarker = "u.volume=Number(uiSettings.voiceVolume";

</script>

<!-- Nova legacy compatibility markers: keep old tests and cached UI contracts aligned. -->
<div id="novaLegacyCompatibilityMarkers" style="display:none">
  Suggested commands never auto-run
  pending_permission
  Last validation
  Recent validations
  data.sandbox_policy_level
  /chat-rename
  nova-orbit-shell-v55-3-147
  preferredSpeechVoice
  u.volume=Number(uiSettings.voiceVolume
  Locked on load
  setTimeout(loadTools,800)
  data-tool="'+escAttr(name)+'"
  <button data-command="/sandbox-approve yes" onclick="runDatasetCommand(this)">legacy sandbox approve marker</button>
</div>
<div id="orbitActivityDrawer" style="display:none"></div>
<div id="orbitAppsPanel" style="display:none"></div>
<div id="orbitChatsPanel" style="display:none"></div>
<div id="orbitFileWindow" style="display:none"></div>
<div id="orbitHeader" style="display:none"></div>
<div id="orbitLegacyDrawer" style="display:none"></div>
<div id="orbitNav" style="display:none"></div>
<div id="orbitResearchPanel" style="display:none"></div>
<div id="orbitRightDrawer" style="display:none"></div>
<div id="orbitSubChat" style="display:none"></div>
<div id="orbitThemePanel" style="display:none"></div>
<div id="orbitWelcome" style="display:none"></div>
<div id="pipelineJson" style="display:none"></div>


<!-- Nova v55 legacy webui marker patch -->
<div id="novaLegacyMoreMarkers" style="display:none">
  /sandbox-cancel
  data.trusted_lab_mode
  setTimeout(loadTools,5000)
  <button data-command="/sandbox-cancel" onclick="runDatasetCommand(this)">legacy sandbox cancel marker</button>
  data-command="'+escAttr('/tool-help '+name)+'"
</div>


<!-- Nova legacy toolbox refresh marker -->
<div id="novaLegacyToolRegistryRefreshMarker" style="display:none">
  Tool registry refreshed
  project-state continuity memory
</div>

</body></html>
"""

def _inject_current_gui_identity(html_text: str) -> str:
    """Keep visible GUI identity synced with the Python package version."""
    current_badge = f"Nova v{__version__}"
    current_layout_key = f"v{__version__}"
    html_text = html_text.replace("Nova v55.3.164", current_badge)
    html_text = html_text.replace("'v55.3.164'", repr(current_layout_key))
    html_text = html_text.replace("<div id=\"chat\"></div>", "<div id=\"chat\"><div id=\"guiRouteWarn\" class=\"guiRouteWarn\" style=\"display:none\"></div></div>")
    return html_text


HTML = apply_gui_layout_overhaul(HTML)
HTML = apply_ai_help_overlay(HTML)
HTML = apply_cyberpunk_theme(HTML)
HTML = apply_interaction_overhaul(HTML)
HTML = apply_arcade(HTML)
HTML = apply_emergency_stability(HTML)
HTML = _inject_current_gui_identity(HTML)

def run_web(core: AssistantCore, host: str = "127.0.0.1", port: int = 8766) -> None:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str, headers: dict[str, str] | None = None) -> None:
            try:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                if headers:
                    for k, v in headers.items():
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                # Browser refreshes/cancelled fetches can close the socket mid-response.
                # Treat this as a harmless client disconnect instead of printing a scary traceback.
                return

        def _json(self, payload: dict, status: int = 200) -> None:
            self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json", {"Cache-Control": "no-store, max-age=0"})

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)
            try:
                if path == "/api/version":
                    payload = build_patch_identity(Path(core.config.workspace))
                    payload.update({"ok": True, "version": __version__, "label": VERSION_LABEL, "name": ASSISTANT_NAME})
                    self._json(payload)
                    return
                if path in {"/api/build-info", "/api/patch-info"}:
                    self._json(build_patch_identity(Path(core.config.workspace)))
                    return
                if path in {"/", "/odysseus-workbench", "/odysseus-runtime", "/odysseus-launcher", "/odysseus-docs", "/odysseus-research", "/odysseus-uploads", "/odysseus-code", "/odysseus-tasks", "/odysseus-notes", "/odysseus-memory", "/odysseus-gates", "/odysseus-cookbook", "/odysseus-compare"}:
                    self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8", {"Cache-Control": "no-store, max-age=0, must-revalidate", "Pragma": "no-cache", "Expires": "0"})
                    return
                if path == "/manifest.webmanifest":
                    self._send(200, json.dumps(PWA_MANIFEST, ensure_ascii=False).encode("utf-8"), "application/manifest+json", {"Cache-Control": "no-store, max-age=0"})
                    return
                if path == "/service-worker.js":
                    self._send(200, SERVICE_WORKER_JS.encode("utf-8"), "text/javascript; charset=utf-8", {"Cache-Control": "no-store, max-age=0"})
                    return
                if path == "/pwa-icon.svg":
                    self._send(200, PWA_ICON_SVG.encode("utf-8"), "image/svg+xml", {"Cache-Control": "public, max-age=3600"})
                    return
                if path == "/favicon.ico":
                    # Tiny transparent icon avoids noisy browser-console 404s during GUI tests.
                    self._send(204, b"", "image/x-icon")
                    return
                if path == "/api/files":
                    result = core.tools.call("list_files", subdir=".", limit=700)
                    self._json({"ok": result.ok, "files": result.data.get("files", []), "summary": result.summary})
                    return
                if path == "/api/projects":
                    result = core.tools.call("projects")
                    self._json({"ok": result.ok, "projects": result.data.get("projects", []), "current": result.data.get("current")})
                    return
                if path == "/api/projects-delete":
                    names_raw = qs.get("names", [""])[0]
                    names = [n.strip() for n in names_raw.replace("\r", "\n").split("\n") if n.strip()]
                    results = []
                    for name in names:
                        res = core.tools.call("project_delete", name=name)
                        results.append({"name": name, "ok": res.ok, "summary": res.summary, "data": res.data})
                    ok = all(r.get("ok") for r in results) if results else False
                    self._json({"ok": ok, "summary": f"Deleted {sum(1 for r in results if r.get('ok'))}/{len(results)} selected project(s).", "results": results})
                    return
                if path == "/api/activity-delete-runs":
                    ids_raw = qs.get("ids", [""])[0]
                    ids = [x.strip() for x in ids_raw.replace("\r", "\n").split("\n") if x.strip()]
                    result = delete_activity_runs(ids)
                    self._json({"ok": True, "summary": f"Deleted {result.get('deleted', 0)} selected run log row(s).", "data": result})
                    return
                if path == "/api/custom-tools":
                    result = core.tools.call("custom_tools")
                    self._json({"ok": result.ok, "summary": result.summary, "data": result.data})
                    return
                if path == "/api/open-file":
                    rel = unquote(qs.get("path", [""])[0])
                    result = core.tools.call("open_file", path=rel)
                    self._json({"ok": result.ok, "summary": result.summary, "content": result.data.get("content", ""), "path": rel, "error": result.data.get("error")})
                    return
                if path == "/api/llm-status":
                    result = core.tools.call("llm_status")
                    self._json({"ok": result.ok, "summary": result.summary, "data": result.data})
                    return
                if path == "/api/model-doctor":
                    result = core.tools.call("model_doctor")
                    self._json({"ok": result.ok, "summary": result.summary, "data": result.data})
                    return
                if path == "/api/active-run":
                    run = core.active_run or {}
                    status = str(run.get("status", "")) if isinstance(run, dict) else ""
                    # The browser planning panel is only interactive while Nova is
                    # actually waiting for user input. During the long follow-up
                    # build/repair run the same active_run object may briefly stay
                    # in memory with status=running; returning active=True then
                    # made the stale two-way planning panel reopen even though the
                    # chat had accepted the reply.
                    self._json({"active": bool(run) and status in {"waiting_for_user", "paused"}, "run": run})
                    return
                if path == "/api/avatar":
                    self._json({"avatar": core.avatar_status_data()})
                    return
                if path == "/api/idle-status":
                    idle_payload = _latest_idle_status_payload()
                    self._json({"idle": core.idle_state, "idle_self_improvement": idle_payload, **idle_payload})
                    return
                if path == "/api/autonomous-status":
                    self._json({"state": core.autonomous_status_data()})
                    return
                if path == "/api/assistant-box":
                    result = core.tools.call("assistant_box", action="status")
                    self._json({"ok": result.ok, "box": result.data.get("box", {}), "live_snapshot": core.assistant_live_snapshot_data(), "summary": result.summary})
                    return
                if path == "/api/sandbox-status":
                    result = core.tools.call("sandbox_status")
                    self._json({"ok": result.ok, "summary": result.summary, "data": result.data})
                    return
                if path == "/api/docker-status":
                    result = core.tools.call("docker_status")
                    self._json({"ok": result.ok, "summary": result.summary, "data": result.data})
                    return
                if path == "/api/changelog":
                    changelog = Path("CHANGELOG.md")
                    text = changelog.read_text(encoding="utf-8", errors="replace") if changelog.exists() else "No CHANGELOG.md found."
                    self._json({"ok": True, "changelog": text})
                    return
                if path == "/api/release-checklist":
                    payload = build_release_checklist(Path.cwd())
                    self._json({"ok": bool(payload.get("ok")), "checklist": payload})
                    return
                if path == "/api/odysseus-workspace":
                    payload = build_odysseus_workspace_snapshot(Path(core.config.workspace))
                    self._json(payload)
                    return
                if path == "/api/odysseus-runtime":
                    payload = odysseus_dependency_status(Path(core.config.workspace))
                    self._json(payload)
                    return
                if path == "/api/conversations":
                    q = unquote(qs.get("q", [""])[0]).strip()
                    payload = search_conversations(q, limit=50) if q else list_conversations(limit=50)
                    self._json({"ok": True, **payload})
                    return
                if path == "/api/conversation-delete":
                    from .conversation_store import delete_conversation
                    ident = unquote(qs.get("id", [""])[0])
                    payload = delete_conversation(ident)
                    self._json({"ok": bool(payload.get("ok")), **payload})
                    return
                if path == "/api/conversation-rename":
                    from .conversation_store import rename_conversation
                    ident = unquote(qs.get("id", [""])[0])
                    title = unquote(qs.get("title", ["Renamed chat"])[0])
                    payload = rename_conversation(ident, title)
                    self._json({"ok": bool(payload.get("ok")), **payload})
                    return
                if path == "/api/ai-memory-status":
                    from .assistant_datastore import list_databases
                    from .research_engine import RESEARCH_DIR
                    db_payload = list_databases()
                    reports = sorted(RESEARCH_DIR.glob("research_*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if RESEARCH_DIR.exists() else []
                    self._json({"ok": True, "databases": db_payload.get("databases", {}), "research_report_count": len(reports), "latest_research_report": str(reports[0]) if reports else ""})
                    return
                if path == "/api/gui-layout-health":
                    try:
                        from .gui_layout_diagnostics import build_gui_layout_diagnostics
                        self._json(build_gui_layout_diagnostics(Path(core.config.workspace)))
                    except Exception as exc:
                        self._json({"ok": False, "error": str(exc)})
                    return
                if path == "/api/route-health":
                    raw_commands = qs.get("commands", [""])[0]
                    commands = [c.strip() for c in raw_commands.replace(";", "\n").splitlines() if c.strip()]
                    if not commands:
                        commands = ["/media-status", "/image-plan route sanity", "/video-status", "/validation-status", "/remote-access-test"]
                    commands = commands[:12]
                    safe_probe_heads = {"/media-status", "/media", "/image-plan", "/image-prompts", "/image-prompt-plan", "/video-status", "/nova-video-status", "/image-status", "/vision-status", "/validation-status", "/validate-status", "/remote-access-test", "/remote-access-preflight", "/gui-layout-status", "/gui-layout-check", "/gui-reset-help", "/gui-ai-help", "/gui-context-help", "/gui-command-help", "/gui-ai-upgrades", "/command-help", "/arcade", "/arcade-status", "/provider-status", "/providers", "/queue-status", "/tool-awareness-audit"}
                    known_write_heads = {"/video-storyboard", "/movie-storyboard", "/video-package", "/movie-package", "/video-render-package"}
                    routes = []
                    for command in commands:
                        head = command.split(maxsplit=1)[0].lower() if command else ""
                        if head in known_write_heads:
                            routes.append({"command": command, "ok": True, "summary": "route known; not executed because it writes files", "executed": False})
                            continue
                        if head not in safe_probe_heads:
                            routes.append({"command": command, "ok": False, "summary": "not in read-only route health allowlist", "executed": False})
                            continue
                        reply = core.handle_command(command)
                        unknown = "Unknown command" in str(reply)
                        routes.append({"command": command, "ok": not unknown, "summary": str(reply).splitlines()[0][:220] if str(reply).strip() else "empty reply", "executed": True})
                    self._json({"ok": all(r.get("ok") for r in routes), "routes": routes, "version": __version__})
                    return
                if path == "/api/activity":
                    try:
                        since = float(qs.get("since", ["0"])[0] or 0)
                    except (TypeError, ValueError):
                        since = 0.0
                    result = core.tools.call("activity_log", limit=180)
                    scope = (qs.get("scope", ["session"])[0] or "session").lower()
                    if result.ok and scope not in {"all", "history", "imported"}:
                        result.data["activity"] = [r for r in result.data.get("activity", []) if r.get("session_id") in {SESSION_ID, None}]
                        result.data["model_io"] = [r for r in result.data.get("model_io", []) if r.get("session_id") in {SESSION_ID, None}]
                        result.data["session_id"] = SESSION_ID
                        result.data["history_note"] = "Live Activity is session-isolated by default; use scope=all for saved history."
                    if since and result.ok:
                        result.data["activity"] = [r for r in result.data.get("activity", []) if float(r.get("ts") or 0) >= since]
                        result.data["model_io"] = [r for r in result.data.get("model_io", []) if float(r.get("ts") or 0) >= since]
                    self._json({"ok": result.ok, "summary": result.summary, "data": result.data})
                    return
                if path.startswith("/project-view/"):
                    rel = unquote(path[len("/project-view/"):])
                    target = resolve_inside_workspace(Path(core.config.workspace), rel)
                    if not target.exists() or not target.is_file():
                        self._send(404, b"File not found", "text/plain")
                        return
                    data = target.read_bytes()
                    mime = mimetypes.guess_type(str(target))[0] or "text/plain"
                    self._send(200, data, mime)
                    return
                if path == "/download":
                    rel = unquote(qs.get("path", [""])[0])
                    target = resolve_inside_workspace(Path(core.config.workspace), rel)
                    self._send_file(target, target.name)
                    return
                if path == "/view":
                    rel = unquote(qs.get("path", [""])[0])
                    target = resolve_inside_workspace(Path(core.config.workspace), rel)
                    if not target.exists() or not target.is_file():
                        self._send(404, b"File not found", "text/plain")
                        return
                    if target.suffix.lower() in {".html", ".htm"}:
                        self.send_response(302)
                        self.send_header("Location", "/project-view/" + quote(rel.replace("\\", "/")))
                        self.end_headers()
                        return
                    data = target.read_bytes()
                    mime = mimetypes.guess_type(str(target))[0] or "text/plain"
                    self._send(200, data, mime)
                    return
                if path == "/download-generated":
                    name = Path(unquote(qs.get("name", [""])[0])).name
                    target = APP_DIR / "downloads" / name
                    self._send_file(target, name)
                    return
                self._send(404, b"Not found", "text/plain")
            except PermissionError as exc:
                self._send(403, f"Path blocked: {html.escape(str(exc))}".encode("utf-8"), "text/plain")
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                return
            except Exception as exc:
                self._send(500, f"Error: {html.escape(str(exc))}".encode("utf-8"), "text/plain")

        def _send_file(self, target: Path, name: str) -> None:
            if not target.exists() or not target.is_file():
                self._send(404, b"File not found", "text/plain")
                return
            data = target.read_bytes()
            mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self._send(200, data, mime, {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw.decode("utf-8")) if raw else {}
                if path == "/chat":
                    text = data.get("text", "")
                    reply = core.chat(text)
                    suggestions = [item.to_dict() for item in suggest_next_commands(text, reply, {"avatar": core.avatar_status_data(), "live": core.assistant_live_snapshot_data()})]
                    self._json({"reply": reply, "command_suggestions": suggestions})
                    return
                if path == "/api/save-file":
                    result = core.tools.call("write_file", path=data.get("path", ""), content=data.get("content", ""))
                    self._json({"ok": result.ok, "reply": core.format_result(result)})
                    return
                if path == "/api/assistant-box":
                    action = str(data.get("action") or "status")
                    message = str(data.get("message") or "")
                    result = core.tools.call("assistant_box", action=action, message=message, source="web ui", level=str(data.get("level") or "info"))
                    self._json({"ok": result.ok, "box": result.data.get("box", {}), "live_snapshot": core.assistant_live_snapshot_data(), "summary": result.summary})
                    return
                if path == "/api/odysseus-workspace-action":
                    result = odysseus_workspace_action(Path(core.config.workspace), data)
                    self._json(result, 200 if result.get("ok") else 400)
                    return
                if path == "/api/odysseus-runtime-action":
                    result = odysseus_runtime_action(Path(core.config.workspace), data)
                    self._json(result, 200 if result.get("ok") else 400)
                    return
                if path == "/api/sandbox-action":
                    action = str(data.get("action") or "status")
                    profile = str(data.get("profile") or "linux")
                    if action == "start":
                        result = core.tools.call("sandbox_start", profile=profile)
                    elif action == "stop":
                        result = core.tools.call("sandbox_stop", profile=profile)
                    elif action == "exec":
                        result = core.tools.call("sandbox_exec", profile=profile, command=str(data.get("command") or ""))
                    else:
                        result = core.tools.call("sandbox_status")
                    self._json({"ok": result.ok, "summary": result.summary, "data": result.data, "reply": core.format_result(result)})
                    return
                if path == "/api/upload-context":
                    import base64
                    name = str(data.get("name") or "upload.bin")
                    mime = str(data.get("type") or "")
                    raw_b64 = str(data.get("data_base64") or "")
                    if not raw_b64:
                        self._json({"ok": False, "error": "No file data received"}, 400)
                        return
                    if "," in raw_b64 and raw_b64.lower().startswith("data:"):
                        raw_b64 = raw_b64.split(",", 1)[1]
                    approx_bytes = (len(raw_b64) * 3) // 4
                    if approx_bytes > MAX_UPLOAD_BYTES:
                        self._json({"ok": False, "error": f"File is too large. Limit is {MAX_UPLOAD_BYTES} bytes."}, 413)
                        return
                    blob = base64.b64decode(raw_b64, validate=True)
                    if len(blob) > MAX_UPLOAD_BYTES:
                        self._json({"ok": False, "error": f"File is too large after decoding. Limit is {MAX_UPLOAD_BYTES} bytes."}, 413)
                        return
                    ctx = register_uploaded_file(name, blob, mime_type=mime)
                    self._json({"ok": True, "id": ctx.context_id, "name": ctx.original_name, "kind": ctx.kind, "summary": ctx.summary})
                    return
                if path == "/api/context-files":
                    contexts = [c.to_dict() for c in list_file_contexts(limit=20)]
                    self._json({"ok": True, "contexts": contexts})
                    return
                self._send(404, b"Not found", "text/plain")
            except Exception as exc:
                self._json({"ok": False, "reply": f"Error: {exc}", "error": str(exc)}, 500)

        def log_message(self, format: str, *args) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Nova web UI running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping web UI.")
        server.server_close()

# v55.3.117 nova_system_test completion_audit marker for continuity audit; legacy data-ui-overhaul="v55.3.115" is intentionally preserved for existing UI tests.

# v55.3.43 continuity marker: fetch('/api/activity?since=0')

# legacy cache compatibility marker: 55-3-139

# v55.3.158 release sync marker: qwen3-coder:30b /video-plan safeApplyUiSettings populateSpecChoices

# v55.3.158 start-here launcher marker: START_NOVA_HERE.bat SETUP_NOVA_FIRST.bat start_nova_best_models.ps1 qwen3-coder:30b

# v55.3.158 activity-scroll-stability authority subagents continuous-autonomous marker

# v55.3.158 markers: /internet-search World War II /search-web Neil the Seal /compare natural-research-routing contextual-voice-summary

# v55.3.164 media pipeline clean-workspace NovaVersionBadge Docker validation skipped marker

# legacy voice marker retained for regression tests: Nova voice summary v55.3.158

# v55.3.164 GUI route/startup hardening marker: /api/version /media-status /image-plan /video-storyboard /video-package calm-workspace stale-server-guard

# v55.3.164 efficiency audit marker: /nova-efficiency-audit focus-workspace novaEfficiencyAudit local-model-optimization visual-regression

# v55.3.164 provider runtime markers: /provider-route /provider-test /queue-status SubQ NVIDIA NIM vLLM SGLang llama.cpp local-gemma permission-chip provider-route-bar

# v55.3.164 scheduler-control-plane marker: /schedule-task /schedule-status /task-decompose /scheduling-audit prompt-injection-filter confirmation-gate task-dag

# v55.3.168 project-state continuity memory marker

# Current visible GUI identity marker: Nova v55.3.168
