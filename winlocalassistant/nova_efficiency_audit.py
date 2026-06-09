from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AuditFinding:
    severity: str
    category: str
    title: str
    detail: str
    recommendation: str
    path: str = "."


@dataclass(slots=True)
class ResearchSignal:
    source: str
    relevance: str
    nova_action: str


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _python_files(root: Path) -> list[Path]:
    skip = {".venv", "__pycache__", ".pytest_cache", ".git", ".nova_runtime"}
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in skip for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def build_nova_efficiency_audit(root: Path | str) -> dict[str, Any]:
    """Build a deterministic, research-backed Nova improvement audit.

    This deliberately does not call an LLM. It is the cheap first pass Nova can run
    before deciding whether to spend qwen3-coder:30b context and time.
    """
    root = Path(root).resolve()
    py_files = _python_files(root)
    webui = root / "winlocalassistant" / "webui.py"
    ollama = root / "winlocalassistant" / "ollama.py"
    core = root / "winlocalassistant" / "core.py"
    launcher = root / "start_nova_best_models.ps1"

    findings: list[AuditFinding] = []
    large_files = []
    for path in py_files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > 180_000:
            large_files.append(str(path.relative_to(root)))
    if large_files:
        findings.append(AuditFinding(
            severity="medium",
            category="maintainability",
            title="Large modules need extraction seams",
            detail="Large Python modules are harder for local models to reason over and slower to test in focused slices: " + ", ".join(large_files[:8]),
            recommendation="Prefer additive extraction around stable seams: routing tables, GUI command metadata, media planning, and audits should live in smaller modules with focused tests.",
        ))

    silent_except = []
    for path in py_files:
        txt = _read(path)
        for idx, line in enumerate(txt.splitlines(), start=1):
            if re.search(r"except\s+Exception\s*:\s*(pass)?\s*$", line):
                # Ignore tests and intentionally tiny compatibility stubs.
                rel = str(path.relative_to(root))
                if not rel.startswith("tests_"):
                    silent_except.append(f"{rel}:{idx}")
    if silent_except:
        findings.append(AuditFinding(
            severity="medium",
            category="observability",
            title="Broad exceptions still hide repair evidence",
            detail=f"Found {len(silent_except)} broad exception handlers without structured logging. Examples: " + ", ".join(silent_except[:10]),
            recommendation="Replace bare `except Exception: pass` with structured warning records so mistake-learning and self-repair can learn the root cause.",
        ))

    webui_text = _read(webui)
    if len(webui_text) > 300_000:
        findings.append(AuditFinding(
            severity="medium",
            category="gui",
            title="Monolithic GUI file is a regression risk",
            detail=f"webui.py is {len(webui_text):,} characters. Small CSS/JS patches become fragile and hard to visually verify.",
            recommendation="Move command palette metadata, layout CSS, media widgets and voice/state panels toward separate templates/modules while preserving existing routes.",
            path="winlocalassistant/webui.py",
        ))
    for marker, title in [
        ("focus-workspace", "Focus workspace CSS not installed"),
        ("novaEfficiencyAudit", "Efficiency audit quick surface not installed"),
    ]:
        if marker not in webui_text:
            findings.append(AuditFinding("low", "gui", title, f"Missing marker `{marker}` in webui.py.", "Install the focus-mode GUI layer and command palette shortcut.", "winlocalassistant/webui.py"))

    ollama_text = _read(ollama)
    if "_acquire_ollama_lane" not in ollama_text or "queue_depth" not in ollama_text:
        findings.append(AuditFinding("high", "local-model", "Ollama prompt queue missing", "Overlapping prompts can still collide.", "Serialize same-model calls and expose queue depth in /llm-status.", "winlocalassistant/ollama.py"))
    if '"stream": False' not in ollama_text and '"stream": false' not in ollama_text.lower():
        findings.append(AuditFinding("low", "local-model", "Non-streaming JSON discipline not obvious", "Structured tool calls are easier to verify when stream=false and JSON mode/schema are explicit.", "Use non-streaming calls for tool/planning JSON and record token timings from final responses.", "winlocalassistant/ollama.py"))

    launcher_text = _read(launcher)
    if "Repair-VenvIfNeeded" not in launcher_text and "Remove-Item" not in launcher_text:
        findings.append(AuditFinding("medium", "startup", "Launcher lacks venv repair guard", "Damaged partial .venv folders can produce missing Activate.ps1 or invalid ~ip pip warnings.", "Detect missing .venv/Scripts/python.exe or Activate.ps1 and rebuild the venv before dependency install.", "start_nova_best_models.ps1"))

    core_text = _read(core)
    for cmd in ["/media-status", "/image-plan", "/video-storyboard", "/video-package", "/nova-efficiency-audit"]:
        if cmd not in core_text and cmd != "/nova-efficiency-audit":
            findings.append(AuditFinding("high", "routing", f"Missing route {cmd}", f"{cmd} is not present in core.py.", "Add route, help text and regression test.", "winlocalassistant/core.py"))

    research = [
        ResearchSignal(
            source="Ollama API",
            relevance="Ollama exposes keep_alive, stream=false, JSON/structured outputs and final timing fields such as eval_count/eval_duration.",
            nova_action="Keep queueing same-model calls, use stream=false for tool JSON, and record token/s for model benchmark history.",
        ),
        ResearchSignal(
            source="llama.cpp/local inference patterns",
            relevance="Quantization, partial GPU offload, KV-cache choices and speculative decoding are core local-inference efficiency levers.",
            nova_action="Keep high-spec and fallback model profiles separate; add future GGUF/llama.cpp profile export rather than hard-coding only Ollama.",
        ),
        ResearchSignal(
            source="Playwright visual comparisons",
            relevance="Screenshot baselines catch GUI regressions that unit tests miss.",
            nova_action="Keep optional Playwright visual tests and add a calm-layout screenshot smoke test for the chat/drawers/popups.",
        ),
        ResearchSignal(
            source="OpenTelemetry-style instrumentation",
            relevance="Spans and structured events make failures visible across agent, tool, model and GUI layers.",
            nova_action="Continue replacing silent exceptions with structured events that self-repair can consume.",
        ),
    ]

    priority = "pass" if not any(f.severity in {"critical", "high"} for f in findings) else "review"
    actions = [
        "Run python -m winlocalassistant.validate --all before release.",
        "Run a focused pytest slice for changed GUI/media/model files.",
        "Run /nova-efficiency-audit after major patches and attach the generated docs to release notes.",
        "Use /llm-status to ensure same-model prompts are queued, not overlapped.",
        "Use optional Playwright visual smoke tests before changing GUI layout again.",
    ]
    return {
        "ok": priority == "pass",
        "decision": priority,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "python_files": len(py_files),
        "findings": [asdict(f) for f in findings],
        "research_signals": [asdict(r) for r in research],
        "recommended_validation": actions,
    }


def render_nova_efficiency_audit(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Efficiency and UX Audit",
        "",
        f"Decision: **{payload.get('decision', 'review').upper()}**",
        f"Generated: {payload.get('generated_at')}",
        f"Python files scanned: {payload.get('python_files')}",
        "",
        "## Research-backed signals",
    ]
    for item in payload.get("research_signals", []):
        lines.append(f"- **{item['source']}**: {item['relevance']} Action: {item['nova_action']}")
    lines += ["", "## Findings"]
    findings = payload.get("findings", [])
    if not findings:
        lines.append("- No deterministic findings.")
    for f in findings:
        lines.append(f"- **{f['severity'].upper()} / {f['category']}** — {f['title']} ({f.get('path','.')})")
        lines.append(f"  - {f['detail']}")
        lines.append(f"  - Fix: {f['recommendation']}")
    lines += ["", "## Validation ladder"]
    for cmd in payload.get("recommended_validation", []):
        lines.append(f"- {cmd}")
    return "\n".join(lines) + "\n"


def write_nova_efficiency_audit(root: Path | str) -> tuple[dict[str, Any], Path, Path]:
    root = Path(root).resolve()
    payload = build_nova_efficiency_audit(root)
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    json_path = docs / "NOVA_EFFICIENCY_AUDIT_LATEST.json"
    md_path = docs / "NOVA_EFFICIENCY_AUDIT_LATEST.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_nova_efficiency_audit(payload), encoding="utf-8")
    return payload, md_path, json_path
