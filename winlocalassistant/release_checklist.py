from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text, read_json_file


def _latest_json(directory: Path, pattern: str) -> Path | None:
    try:
        files = [p for p in directory.glob(pattern) if p.is_file()]
        return max(files, key=lambda p: (p.stat().st_mtime, p.name)) if files else None
    except Exception:
        return None


def build_release_checklist(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    doctor = root / "docs" / "NOVA_DOCTOR_LATEST.json"
    gate = root / "docs" / "NOVA_RELEASE_GATE_LATEST.json"
    integration = root / "docs" / "INTEGRATION_RADAR_LATEST.json"
    docker_report = _latest_json(APP_DIR / "docker_runs", "*/validation_report.json")
    security_report = APP_DIR / "security_reports" / "security_status_latest.json"
    items = []
    def add(name: str, path: Path | None, ok_key: str = "ok", required: bool = True):
        data = read_json_file(path, {}, expected_type=dict, quarantine=True) if path and path.exists() else {}
        ok = bool(data.get(ok_key)) if data else False
        items.append({"name": name, "ok": ok, "required": required, "path": str(path or ""), "summary": str(data.get("summary") or data.get("recommendation") or ("missing" if required else "optional"))[:500]})
    add("Nova Doctor", doctor)
    add("Release gate", gate)
    add("Integration radar", integration, ok_key="ok", required=False)
    add("Latest Docker validation", docker_report, ok_key="ok", required=False)
    add("Defensive security status", security_report, ok_key="ok", required=False)
    changelog = root / "CHANGELOG.md"
    readme = root / "README.md"
    items.append({"name": "CHANGELOG present", "ok": changelog.exists() and changelog.stat().st_size > 100, "required": True, "path": str(changelog), "summary": "Version notes available" if changelog.exists() else "missing"})
    items.append({"name": "README present", "ok": readme.exists() and readme.stat().st_size > 100, "required": True, "path": str(readme), "summary": "README available" if readme.exists() else "missing"})
    required = [i for i in items if i.get("required")]
    ok = all(bool(i.get("ok")) for i in required)
    payload = {"ok": ok, "summary": "Release checklist passed" if ok else "Release checklist has missing required items", "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "root": str(root), "items": items}
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    atomic_write_json(docs / "NOVA_RELEASE_CHECKLIST_LATEST.json", payload, ensure_ascii=False)
    atomic_write_text(docs / "NOVA_RELEASE_CHECKLIST_LATEST.md", render_release_checklist_markdown(payload))
    return payload


def render_release_checklist_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Nova Release Checklist", "", f"Generated: {payload.get('generated_at','')}", f"Root: `{payload.get('root','')}`", "", f"Overall: {'PASS' if payload.get('ok') else 'CHECK'}", "", "## Items"]
    for item in payload.get("items") or []:
        mark = "✅" if item.get("ok") else ("❌" if item.get("required") else "⚪")
        req = "required" if item.get("required") else "optional"
        lines.append(f"- {mark} **{item.get('name')}** ({req}) — {item.get('summary','')}")
        if item.get("path"):
            lines.append(f"  - `{item.get('path')}`")
    lines += [
        "",
        "## Next actions",
        "- Run `/nova-doctor` then `/release-gate final validation` before packaging.",
        "- Run `/docker-validate quick` when Docker is available.",
        "- Run `/security-status` before lab/security work to record a defensive inventory.",
        "- Use `/integration-radar` to choose the next external tool integration.",
    ]
    return "\n".join(lines)
